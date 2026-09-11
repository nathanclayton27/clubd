# The clubd database

What it holds, what has actually been run against it, and how to tell whether a
command is safe before you paste it.

This file is the record. `schema.sql` is not — its functions and policies are
behind production and it says so in its own banner. Where the two disagree,
this file is right.

**Maintenance**: see [§7](#7-the-maintenance-rule). A stale entry here is more
dangerous than no entry, because this file is trusted on sight.

---

## 1. The mental model

Read this section alone and you should be able to predict where a new feature's
data goes.

### What it stores

| What | Where |
|---|---|
| What you have watched or read | `progress` — one row per user per list, holding an array of item ids |
| What you watched *with a club* | `club_progress` — one row per club membership, a session of its own; every write to it also unions up into `progress` |
| When you ticked it | `tick_events` — an append-only log, one row per tick |
| What you thought of it | `thumbs` — up or down, per item, or one for a whole list |
| Who you watch it with | `groups` + `group_members`, plus `group_join_tokens` for invite links |
| Who you know | `profiles` (friend code, username) + `friendships` (one row per direction) |
| Guardrails | `private_properties` (lists treated as private), `rate_events` (join-attempt counting) |

Everything else is a function or a policy mediating access to those.

### The three rules that explain most of it

**1. Every row belongs to one user, and `auth.uid()` is the key to everything.**
RLS is on for every table. Almost every policy starts life as
`user_id = auth.uid()`. If you are writing a new table, that is the first policy
you write and often the only one.

**2. Rows are scoped by `property_id`, which is a list slug.** `progress` is
keyed `(user_id, property_id)`. A slug may carry a `#`-suffixed variant for a
rewatch; server-side checks `split_part` on `#` before comparing, so a suffix
cannot be used to sidestep a rule that applies to the base list.

**3. Sharing is additive, and that is deliberate.** Permissive policies **OR**
together. On `progress` there are separate branches for your own row, for mutual
friends, and for club and group co-members. Narrowing the friends branch cannot
narrow the club branch. Anyone who "tidies" several policies into one changes
the privacy model. Do not.

### The two mechanisms that carry the weight

**`security definer` functions.** Anything the client must not be trusted to
compute lives in one: `shares_group_with`, `friend_may_read`, `group_may_read`,
`is_private_property`, plus every RPC that writes a table the client cannot
write directly. A definer function resolves `EXECUTE` against its **owner**, not
the caller — which is why some are granted to nobody and must stay that way.
`group_may_read` is called only from inside `shares_group_with`; granting it to
`authenticated` would make it callable on its own.

**Column-level grants.** Two tables have table-wide `select` revoked and a
named-column grant in its place:

- `profiles` → `user_id, fcode, username, updated_at`
- `group_members` → `group_id, user_id, display_name, color_index, joined_at`

Add a column to either and forget the grant and it is unreadable — and the error
is `permission denied`, not "column does not exist". `groups` has **no** column
grant and the front end does `select('*')` on it, so adding one to `groups`
breaks every group and club screen at once. That is why the invite token went
into its own table rather than a `groups` column.

### So where does a new feature's data go?

If it is *a thing one user records about one item on one list*, it is shaped
like `thumbs`: a table keyed `(user_id, property_id, item_id)`, own-row policies
for select/insert/update/delete, and — if other people should see it — one extra
permissive select policy whose predicate is `shares_group_with(user_id,
property_id)` or `friend_may_read(user_id, property_id)`. **Put the gating
inside the predicate function, not in the policy.** That is the pattern the
whole database follows.

---

## 2. Is this safe to run?

### The pre-flight, every time

1. **Read the whole file**, top to bottom, including the header.
2. **`python tools/whereis.py <object>`** for every object the file creates or
   replaces. **23 of 74 objects here are defined in more than one file.**
   Whichever runs last wins, silently.
3. **`python tools/ordercheck.py <file.sql>`** for create-time resolution
   (trap 1). Know its limit before you lean on it — see below.
4. **Confirm one `begin` / `commit` wraps the whole file.** Several older files
   have none, and a file without a transaction can leave half its work applied.
5. **Confirm every `drop` has its `create` immediately underneath**, inside that
   transaction.
6. **Confirm it ends with a readback** — a `select` block asserting what should
   now be true. If it has none, write one before running anything.
7. **Paste the whole file. Never half.** Stopping between a drop and its create
   is how a correct file causes an outage.

Both scripts are read-only and read `.sql` files. They connect to nothing.

### The Supabase SQL editor sends a pasted file as ONE statement — measured, not assumed

**`begin;` at the top of a file genuinely governs everything below it**, so
"if anything raises, the whole file rolls back" is true here. Step 4 above is
worth doing precisely because it works.

Established 2026-08-28 (CLU-424) by Nathan running this in the real editor and
pasting back the result — `ONE TRANSACTION - begin; governs the whole file`:

```sql
begin;
create temp table _txn_probe as select txid_current() as xid;
select case when (select xid from _txn_probe) = txid_current()
         then 'ONE TRANSACTION - begin; governs the whole file'
         else 'SPLIT - each statement got its own transaction' end as verdict;
commit;
```

This mattered enough to measure because **every file in this project that claims
"one transaction" was resting on it and none had checked.** Had the editor split
on semicolons, `begin;` would have been its own statement and a failure partway
down would have left earlier statements committed — which for
`migrate-club-progress.sql` would have meant an irreversible delete of 36 clubs
escaping the transaction meant to be able to undo it. That file has since been
pasted whole and committed as one unit (2026-09-10, §5), which is this
measurement being cashed in rather than trusted.

The probe is safe to re-run on production if anyone ever wants to confirm it
again: `create temp table` lives in a per-session schema that PostgREST cannot
see, it disappears with the connection, and no real table is read or written.

⚠ **This licenses the transaction, not carelessness.** Rule 7 above still
stands — paste the whole file, never half. A rollback can only undo what was
inside the transaction it was told about.

> **What `ordercheck.py` does not do.** It builds its symbol table from *the one
> file it is scanning*. It has no cross-file knowledge, so it cannot see a single
> edge between two migrations — `FINAL-2-privacy.sql` reports "0 create-time
> edges" even though its `language sql` `privacy_settings()` reads three columns
> that `FINAL-1` creates. "All files pass ordercheck" is therefore a statement
> about each file internally, and says almost nothing about the order they run
> in. The order below was derived by hand and is argued, not tool-verified.

### What makes a command safe here

- It is additive: `create table if not exists`, `add column if not exists`,
  `create index if not exists`, `create or replace function`, a `create policy`
  for a name no other file uses.
- It re-runs to the same state — genuinely, not because its header says so.
- It is one transaction.
- Every object it touches is defined in exactly one file, and this is that file.
- Its `language sql` bodies reference only things created earlier in the same
  file.

### What makes one dangerous

- `create or replace function` on a name that appears in more than one file.
- A `drop policy` whose `create policy` is anywhere other than directly below.
- Replacing a trigger *function* where the *trigger* may not exist.
- A new `not null` or `check` that live rows could fail.
- **Any body copied out of `schema.sql` or out of `superseded/`.**

### The five traps this project has actually been bitten by

#### Trap 1 — `language sql` resolves at CREATE time; `plpgsql` does not

A function reading a column, placed above the section that adds it. In
`plpgsql` the body is text until it runs, so it is fine. In `language sql`
Postgres parses and binds at creation, so it fails immediately. **The two look
identical in a diff.**

It bit us on `migrate-groups.sql`, 2026-08-26 22:44 UTC: `ERROR 42703: column
p.share_with_groups does not exist`. `group_may_read()` and `shares_group_with()`
are `language sql` and sat above the section adding the columns they read. The
transaction aborted and the database was untouched. **Three adversarial audits
had missed it.** Reordered, it succeeded (CLU-387).

`tools/ordercheck.py` was written after that failure and validated against the
broken layout before it was trusted. It found thirteen create-time edges in that
file — within it. See its limit above.

#### Trap 2 — replacing a trigger function without recreating the trigger

`create or replace function foo_guard()` with no `create trigger` under it, on
the reasoning that the trigger is already attached. That holds only where it
already is. Anywhere else you get a function nobody calls: the migration commits
clean, every check against `pg_proc` passes, and `pg_policies` does not show
triggers so a policy dump misses it too. The guard is inert and nothing says so.

**Check `pg_trigger` by `tgname`, not `pg_proc` by `proname`.**
`migrate-groups.sql` §1b drops and recreates `groups_update_guard` for exactly
this reason, and readback check 14 confirms attachment (CLU-387, 19/19).
`migrate-club-progress.sql` went one better for `groups_fold_sessions`: it
asserts attachment **inside its own transaction** (§5 of that file), so a fold
function defined but not attached rolls the whole migration back rather than
committing an inert guard, and asserts it again as readback 12 (CLU-389, 19/19,
2026-09-10).

#### Trap 3 — dropping a policy without recreating it

Two ways to lose. Permissive policies OR together, so dropping one branch
removes a whole class of rows for everyone until the create lands — and if the
file has no transaction, a failure between the two leaves RLS on with that
branch gone.

The slower version: **two files creating the same policy name.** Whichever runs
last wins, no error, both files' verification blocks still passing.
`"mutual friends read progress"` is defined in **five** files, the most
redefined object in the project. `FINAL-1-rls-locks.sql` is its single
definition; `FINAL-2` *verifies* it rather than recreating it, and aborts if it
is not the expected one.

#### Trap 4 — a constraint existing rows would fail

`add constraint ... check (...)` and `set not null` both validate against
existing rows immediately — a full scan that either passes or rolls the whole
migration back.

A matched pair worth knowing: `add column if not exists c boolean not null
default true` **skips entirely** if `c` already exists as nullable, and the
following `set not null` then fails on the nulls already there.

Before adding a constraint, run its negation and expect zero:

```sql
select count(*) from public.t where not (<the check predicate>);
```

`groups_scope_ck` was safe because every existing row was a watch club carrying
both a code and a property (CLU-387, readback 04 and 05). For the nullable case,
put an explicit `update ... where c is null` between the add and the
`set not null` — `migrate-groups.sql` does this for `profiles.hidden_from_groups`.

#### Trap 5 — copying a definition out of a stale file

You need `join_group()`, so you copy it from `schema.sql`, which is where it is
defined. But `schema.sql` describes a fresh project and has never been
reconciled against production: its `join_group()` predates the rate limiter. A
migration whose stated purpose was adding a boolean copied that body and **would
have deleted `guard_group_join_rate()` and the entire join-attempt cap.** An
auditor caught it (CLU-374).

**`schema.sql` is not uniformly stale, which is what makes it convincing.** Its
**tables are current** — `progress` already carries `property_id` and the
two-column key, `groups` already carries `schedule_start` and
`schedule_shift_days`, `create_group` is already the four-argument form. Its
**functions and policies are not.** Its banner says exactly this and is right.

Run `python tools/whereis.py join_group` before copying anything, then take the
body from the newest file **the [history table](#5-history-what-has-actually-been-run)
says was run**.

---

## 3. Bootstrap: standing up an empty project

Fourteen files, in this order. The first thirteen are at the repo root; the
fourteenth is not, and that is called out below.

```
 1. schema.sql
 2. migrate-add-friends.sql
 3. migrate-add-friend-decline.sql
 4. migrate-add-tick-events.sql
 5. migrate-add-rate-limits.sql
 6. migrate-add-thumbs.sql
 7. rls-fix-PART1-safe-now.sql
 8. FINAL-1-rls-locks.sql
 9. FINAL-2-privacy.sql
10. migrate-groups.sql
11. migrate-mute-privacy.sql
12. migrate-group-thumbs.sql
13. migrate-add-schema-ledger.sql
14. scratch/security/migrate-club-progress.sql
```

All fourteen are live. Step 13 ran on 2026-08-27 with a 14/14 readback
(CLU-404), so from there on the database keeps its own record of what has been
run and this section stops being the only one. **Step 14 ran on 2026-09-10 with
a 19/19 readback (CLU-389) and is the first run the ledger recorded as it
happened** rather than by backfill.

⚠ **Step 14 is still in `scratch/security/`, and this file does not move it.**
It is a live migration now, so the convention in
`scratch/security/moved-to-repo/README.md` — a live migration the repo cannot
reproduce the database without belongs at the root, tracked — points at moving
it. Two things have to be settled first, and neither is mechanical. Whether it
may be published at all is Nathan's, and has its own card (CLU-414): its comment
header names 36 deleted clubs and 10 surviving ones **by the names their creators
typed**, which is other people's content, not ours. And the ledger row it wrote records the
**path-qualified** filename `scratch/security/migrate-club-progress.sql` —
`tools/migrations.py` prints that path deliberately, because basenames collide —
so a move without a plan for that row leaves `--verify` joining a path that no
longer exists. Until both are answered, a bootstrap runs step 14 from
`scratch/security/`, which is gitignored and therefore absent from a fresh
clone: **a clone alone cannot complete this path.**

### The order is not a preference

Every edge below is forced. Permuting the early files was tested: of the 24
orderings of steps 2–5, **12 fail**, all on the same edge.

- **2 before 3.** `migrate-add-friend-decline.sql` creates a policy on
  `public.friendships`, which step 2 creates. Out of order it is `42P01`.
  *(Steps 4 and 5 are genuinely independent of the others; 2 and 3 are not.)*
- **6 before 7, 8 and 12.** The thumbs blocks in steps 7, 8 and 9 are guarded on
  `to_regclass('public.thumbs')` and pass **vacuously** if the table is absent —
  so omitting step 6 buys you a database with no thumbs table and two green
  verification blocks. It does eventually fail loudly, at step 12, which touches
  `thumbs` unguarded. The sound reason for step 6 is simpler: **the thumbs DDL
  exists nowhere else in the repo.**
- **7 before 8.** `private_properties` is created **only** by step 7, and
  FINAL-1 inserts into it.
- **5 before 10.** `migrate-groups.sql` §0 refuses without
  `guard_group_join_rate()`.
- **8 → 9 → 10 → {11, 12}.** Enforced by §0 blocks that check function *bodies*,
  not merely existence.
- **10 before 14.** `migrate-club-progress.sql` §0 checks four things and none
  of them is mere existence: `groups.universal` present, `groups_scope_ck`
  carrying both `NOT universal` and `property_id IS NOT NULL`,
  `groups_update_guard` **attached** to `public.groups` (`pg_trigger`, not
  `pg_proc`), and a `shares_group_with(uuid,text)` whose `prosrc` mentions
  `universal`. Any one missing and it raises before it touches a row.
- **13 before 14.** Step 14's last statement before `commit` inserts its own
  ledger row into `schema_migrations`, which step 13 creates. Out of order the
  whole migration rolls back on `42P01` — after doing all its work, which is the
  cheapest possible way to discover it.
- **1 before 14**, for `progress` itself: step 14 writes to
  `progress (user_id, property_id)` and its readback check 15 asserts that
  two-column primary key is still the one in place. It adds no column to
  `progress` and drops nothing from it — the sidecar shape exists so that
  sentence can be true.

### This is Supabase-only, and it fails at step 1 elsewhere

**No file in this repo creates the `anon`, `authenticated` or `service_role`
roles.** `schema.sql` revokes and grants on them, and the path references them
61 / 67 / 39 times. On stock Postgres it dies at step 1 with `42704`.

A second, later divergence: `schema.sql` runs `create extension if not exists
pgcrypto` **unqualified**, while `migrate-groups.sql` §0 demands
`extensions.gen_random_bytes`. On Supabase that resolves; on stock Postgres
pgcrypto lands in `public` and step 10 refuses.

### What this path does not give you, and what step 14 changed

1. **Data.** Obviously. It builds the shape, not the contents. *(Step 14 is the
   one exception worth knowing: its snapshot writes one `club_progress` row per
   surviving watch-club membership, so on an empty database it writes nothing,
   and on production it wrote state that no other file contains. How many rows
   is not recorded anywhere — readback 11 asserts only that the count equals
   the surviving memberships, and 66 is the number *deleted*, not snapshotted.)*
2. **`club_progress` and `save_progress` are no longer missing.** They exist
   live — created by step 14 on 2026-09-10 21:38 UTC, confirmed by readback
   checks 06–14 (CLU-389) — so **the caveat that used to sit here has inverted.**
   It used to read "this path reproduces the live database only if those two do
   not exist live, which no file can tell you". Now: a bootstrap that stops at
   step 13 **does not** reproduce the live database, and the difference is
   visible from the outside. The front end calls both; without them
   `missingThing()` catches `42P01`, `PGRST205`, `42883` and `PGRST202`, the
   `CPGONE` / `SAVEGONE` latches trip once per load, and session ticks fold back
   into the all-time row. That degradation is still in the bundle and still
   correct, but on production it is now **dead code** — reachable only if
   somebody drops the table.

### Nothing in `superseded/` is in this list

That folder is history. Until 2026-08-27 it also held `migrate-add-thumbs.sql`,
which was the **only** definition of the `thumbs` table, its two indexes and its
four own-row policies — so a fresh install obeying that folder's own README
would have finished with no thumbs table and no error. The file has been split:
the DDL is now step 6 at the root, and only the genuinely superseded
`mutual friends read thumbs` policy stayed behind.

---

## 4. The object map

Per table: what it holds, who may read it, who may write it.

**`progress`** — one row per user per list, `read_ids` as an array. Keyed
`(user_id, property_id)`. Read by you, by mutual friends (`friend_may_read`,
which consults the privacy switches and excludes gated lists), and by club and
group co-members (`shares_group_with`). Written only by you.

**`club_progress`** — a club's own tracking session: one row per **membership**,
keyed `(group_id, user_id)`, with `read_ids text[] not null default '{}'` and
`updated_at`. Plus an index on `user_id`. It is not a lens onto `progress`; it is
a separate set of ticks, and `progress` was not altered to make room for it — no
new column, no dropped constraint, no re-key (readback 15 and 16 assert that).
There is **no `property_id` column on purpose**: `groups_scope_ck` guarantees a
watch club has one and `groups_update_guard` refuses to let it change, so
`group_id` *is* the scope, and a second copy of a scoping fact is a thing that
can drift.

*Who reads it:* two policies, both `select`. `"read own club session"` —
`auth.uid() = user_id`. `"club members read the club's sessions"` —
`club_session_visible(group_id, user_id)`. *Who writes it:* **nobody, directly.**
There is no insert, update or delete policy at all, and `revoke all` takes DML
from `public, anon, authenticated` with only `select` granted back — to `anon` as
well, deliberately, because RLS returns a signed-out caller zero rows whereas
revoking `select` would turn a query that races the session into a hard error.
Every write goes through `save_progress()`, which is what makes "furthest wins"
structural rather than a promise.

*The foreign key is a ruling, not a detail.* `(group_id, user_id)` references
`group_members (group_id, user_id) on delete cascade` — so leaving a club
deletes **your** session and nobody else's (Nathan, CLU-420), and rejoining
restores nothing. Deleting the club still reaches sessions, the long way round:
`groups` → `group_members` → `club_progress`. Readback 17 tests the referenced
table *and* `confdeltype = 'c'`, because pointing at `group_members` with
`no action` would satisfy everything else and make "leave a club" raise a
foreign-key violation. `user_id` also carries a second, independent
`references auth.users(id) on delete cascade`, so deleting the account takes its
sessions with it.

**`save_progress(p_property text, p_club uuid, p_ids text[])
→ timestamptz`** — the **only** write path into `club_progress`.
`security definer`, `search_path = public, pg_temp`, `execute` granted to
`authenticated` only and revoked from `public` and `anon` (readback 13). One call
makes two writes in one statement pair, and the asymmetry between them *is* the
ruling: the **session** row is upserted to the exact set passed in, so unticking
works inside a club; your **universal** `progress` row is upserted with
`arr_union`, so a club untick can never lower your all-time record. Both in one
transaction, so a JWT lapsing between two round trips cannot leave a session
holding ticks the universal row does not.

It refuses four ways: not signed in (`auth.uid() is null`); an id set larger than
**5000** (*"that is not a plausible progress set"* — a sanity bound, not a
security control; the largest real `progress` row was 1174 ids on 2026-09-10);
`p_club` that is not a non-universal group **you are a member of**; and a
`p_property` that disagrees with the property it derives from the club (a null
`p_property` is accepted — the check is `is not null and is distinct from`, so
omitting it is not a way round anything, only a way of not asking). The
property is **derived, never trusted** — `p_property` is checked against it
rather than used, because a caller who could name their own property could write
their club's ticks onto any list.

**`arr_union(a text[], b text[]) → text[]`** — sorted, de-duplicated union of two
id arrays; `immutable`, `parallel safe`. Callable by **neither** browser role
(`revoke all`, nothing granted back — readback 14): it is an internal of
`save_progress` and the fold trigger. A union rather than anything shaped like
`greatest(count)`, because `read_ids` is a set and people tick out of order, so
comparing sizes would discard one array's ticks wholesale. Its monotonicity is
what licenses every "furthest wins" claim in the schema.

**`club_session_visible(p_group uuid, p_owner uuid) → boolean`** — the predicate
behind the co-member read policy, `language sql security definer stable`. Three
tests, and the third is the interesting one: the group is a watch club, **you**
are in it, **and the row's owner** is in it. That last clause is why leaving a
club stops the people still in it reading your old sessions, with no delete
policy anywhere. `security definer` because a policy reading `group_members`
directly would be filtered by that table's own RLS; granted to **`anon` as well
as `authenticated`** (readback 18) because it is named directly *in a policy*,
and policy expressions resolve `EXECUTE` against the querying role.

**`club_fold_on_delete()`, attached as trigger `groups_fold_sessions`** —
`before delete on public.groups, for each row`. Deleting a watch club cascades
its sessions away, and the superset invariant only survives *forward*: a Just-me
untick is a replace, so the universal row can briefly sit **below** a session
that still holds those ids. Delete the club in that window and the ticks exist
nowhere. So on each deleted row it returns early for a universal group or a null
property, and otherwise folds every session on that club into its owner's
`progress` row for the club's property — `insert ... on conflict do update set
read_ids = arr_union(...)`, never a replace — skipping empty sessions. `before
delete` on the parent is load-bearing: it fires before the RI cascade reaches
`club_progress`. ⚠ **It does not cover leaving or being removed**, which hit the
same window with no fold — the open exposure in [§5](#the-largest-thing-in-the-repo-and-it-has-now-run).

**`deleted_groups_20260827`** and **`deleted_group_members_20260827`** — the
archive of what the 2026-09-10 run deleted: 36 clubs and 66 memberships
(readback 03 and 04). `create table ... (like <source> including all)` copies,
written **child-then-parent inside the same transaction as the delete**, before
it. After that commit they are the only route back. **Nobody can read either one
through the API**: RLS on, **no policies at all**, and `revoke all` from
`public, anon, authenticated` (readback 05 and 19). Same posture as
`schema_migrations`: operational, and the site never touches them.

**`tick_events`** — append-only log of when you ticked and whether it was
`live` or `backfill`. Read and written by you only. Nobody else ever sees it;
the distinction exists so a batch import cannot look like tonight's viewing.
**It still has no `group_id`.** That column was cut from the 2026-09-10 run
deliberately (§6 of that file): every user has an UPDATE policy on their own
`tick_events` rows and the update guard pins `user_id`, `property_id`, `item_id`,
`action` and `at` — but would not have pinned `group_id`, so anyone could have
set their own ticks' provenance to any club. Nothing in the bundle reads or
writes it, so a club tick is **not** attributable from this table. It comes back
on its own card, with the guard extended in the same commit.

**`thumbs`** — up or down per item; `item_id NULL` is the whole-list thumb.
Read by you, by mutual friends, and — since `migrate-group-thumbs.sql` — by club
and group co-members. Written only by you. There is no neutral value: removing
an opinion deletes the row.

**`groups`** — clubs and groups both. `universal = true` means a group (no
code, no property); `false` means a watch club. `groups_scope_ck` enforces the
pairing, and `groups_update_guard` stops `universal` being flipped after
creation. Readable by members; writable by the creator. **No column grant** —
the front end does `select('*')`.

**`group_members`** — the roster, with `display_name` and `color_index`.
Five-column grant. Members read; you rename yourself; the owner removes others;
you may leave.

**`group_join_tokens`** — invite links. Its own table rather than a `groups`
column precisely because `groups` has no column grant and adding one would break
every club screen.

**`profiles`** — friend code and username. Four-column grant. **Readable by any
signed-in user today** — every row, one request for the whole directory —
because "add a friend by code" reads it directly. That stays true until
`clu153-B-narrow-profiles.sql` runs (§5, *Queued and ready*), which narrows it
to your own row plus anyone a `friendships` edge connects you to; a stranger is
then reachable through `find_profile_by_code()`, the definer function `clu153-A`
creates, **or by asserting an edge to them** — `migrate-add-friends.sql`'s
insert policy constrains only column `a`, uncapped, so a held `user_id` is as
good as a held code (CLU-445). Neither file has run. *(This line used to say
`FINAL-3` would narrow it; FINAL-3 is superseded by that pair. It also used to
say strangers would be reachable "only" through the function, which the CLU-153
audit refuted — see §5.)*

**`friendships`** — one row per direction. Mutual means both rows exist. You may
add your own direction, remove your own, and decline an incoming one.

**`private_properties`** — lists treated as private by policy. One row today.
Empty, the gated-list term in every policy is a no-op, which is why step 7
without step 8's insert protects nothing.

**`rate_events`** — join-attempt counting behind `guard_group_join_rate()`.
Once `clu153-A` runs it also counts friend-code misses, under kind `'fcode'`.

**`schema_migrations`** — one row per migration **run**, not per file, so a second run of the same file is visible rather than
overwriting the first. Records outcome too, so a failure is history rather than
a hole. **Nobody can read it through the API**: RLS on with no policies, plus a
revoke from `public, anon, authenticated`. It is operational metadata and the
site never touches it.

---

## 5. History: what has actually been run

Timestamps are UTC. Nathan is UTC−7, so several fall on the previous local day.

### Before the board existed — committed, no run record

The board's first issue is 2026-08-23; nothing earlier could be recorded.

| Committed | File | Evidence it ran |
|---|---|---|
| 2026-08-19 `936e52b` | `schema.sql` | None. Inferred from the site working. |
| 2026-08-19 `63b931c` | `migrate-to-multiproperty.sql` | Strong — a 2026-08-25 `pg_policies` dump shows `"read group progress"` using the two-argument `shares_group_with` this file introduced (CLU-34). |
| 2026-08-19 `cacea45` | `migrate-add-owner-removal.sql` | Circumstantial — CLU-34 reasons about `"owner removes member"` as live. |
| 2026-08-19 `af59c94` | `migrate-add-schedule-start.sql` | **None.** It adds `groups.schedule_start` — the date a *group* picks. *(This line used to cite CLU-47 as evidence. That card is solo schedules, it is still in Todo, and it was created four days after this date, so it cannot be evidence for anything here.)* |
| 2026-08-21 `70c5504` | `migrate-add-join-or-create.sql` | None, and moot: `migrate-add-rate-limits.sql` replaced its function on 2026-08-24 and that run is confirmed. |

None of these five was pasted into a comment, so we cannot confirm they ran in
exactly the committed form.

### Board-confirmed

| When (UTC) | What ran | What it changed | CLU |
|---|---|---|---|
| 2026-08-23 | `migrate-add-tick-events.sql` | `tick_events`, two indexes, three policies, the update guard | CLU-25 |
| 2026-08-23 20:28 | Supabase upgraded to Pro, daily backups on | Dashboard action, not SQL | CLU-9 |
| 2026-08-24 17:12 | `migrate-add-friends.sql` | `profiles`, `friendships`, six policies. Pasted inline, byte-identical to the repo file | CLU-69 |
| 2026-08-24 17:26 | `migrate-add-friend-decline.sql` | One policy | CLU-102 |
| 2026-08-24 18:04 | `migrate-add-friend-shelves.sql` | The first `"mutual friends read progress"` | CLU-72 |
| 2026-08-24 22:27 | `migrate-add-rate-limits.sql` + GoTrue settings | `rate_events`, four functions, rate-limited `join_group` and `join_or_create_group` | CLU-35 |
| 2026-08-24 23:43 | `migrate-add-thumbs.sql` *(then in `superseded/`)* | `thumbs`, two indexes, five policies | CLU-43 |
| 2026-08-25 00:06 | `rls-fix-PART1-safe-now.sql` | Two update-guard triggers, `private_properties` (empty), `is_private_property()`, `search_path` hardening, `anon` write revokes on six tables. Confirmed by a pasted `pg_policies` dump | CLU-34 |
| 2026-08-25 18:31 | **Read-only** pre-flight: ownership and RLS flags across five tables | All owned by `postgres`, RLS on, force-RLS off — as it must be, or the definer functions would not work | CLU-195 |
| 2026-08-25 ~18:32 | `FINAL-1-rls-locks.sql` | Three `profiles` columns, `friend_may_read()`, the merged single definition of both friends-read policies, one row into `private_properties` | CLU-195 |
| 2026-08-25 18:37 | **Read-only** `pg_policy` readback | Both policies came back merged. The strongest evidence in this table: the enforcement read out of the database itself | CLU-195, CLU-187 |
| 2026-08-25 18:39 | `FINAL-2-privacy.sql` | `profiles` four-column grant; `privacy_settings`, `set_privacy`, `set_list_hidden` | CLU-195 |
| 2026-08-26 22:44 | `migrate-groups.sql` — **FAILED** | `ERROR 42703` at line 371. Transaction aborted, **database untouched.** The origin of `ordercheck.py` | CLU-387 |
| 2026-08-26 23:00 | `migrate-groups.sql` — re-run reordered, succeeded | `groups.universal`, nullable `code`/`property_id`, `groups_scope_ck`, `group_join_tokens`, three privacy columns, the rewritten `shares_group_with`, eight RPCs | CLU-387 |
| 2026-08-26 23:04 | **Read-only** 19-check readback | 19/19. Confirmed `join_group` still carries its rate-limit calls, `group_may_read` is callable by neither `anon` nor `authenticated`, and `groups_update_guard` is attached rather than orphaned | CLU-387 |
| 2026-08-26 23:47 | `migrate-mute-privacy.sql` + 7-check readback | 7/7. `group_members` five-column grant, `my_group_shares()` | CLU-392 |
| 2026-08-27 00:27 | `migrate-group-thumbs.sql` + 5-check readback | 5/5. One policy, `"read group thumbs"` | CLU-390 |
| 2026-08-27 18:43 | `migrate-add-schema-ledger.sql` + 14-check readback | 14/14. `schema_migrations`, three constraints, an index, RLS deny-all, and the eighteen rows above backfilled into it | CLU-404 |
| 2026-08-28 | **Read-only** `preflight-club-progress.sql`, five-statement version | Returned one row, `must_be_zero = 0` — the editor showed only the last statement (see §2). Rewritten as one statement the same day. Nothing changed | CLU-389 |
| 2026-09-10 21:04 | **Read-only** `preflight-club-progress.sql`, one-statement version | Seven rows: 5 PASS, 1 INFO (largest `progress` row is 1174 ids; the write cap is 5000), and **1 false STOP**: check 4 named the nine clubs that carried a date *at survey time* as if they had gained one. Nothing changed; the check was wrong, not the data. Fixed the same hour, below | CLU-389 |
| 2026-09-10 ~21:37 | **Read-only** `preflight-club-progress.sql` re-run, check 4 fixed (152 lines, md5 `47cf964c…`) | Seven rows: **6 PASS, 1 INFO** — the INFO is the same 1174-id `progress` row against the 5000 cap. Check 4 now compares live dates against the surveyed ones and read PASS, so the nine dated clubs stopped being a standing STOP. Nothing changed. **This clean read was the go signal** | CLU-389 |
| 2026-09-10 21:38 | `migrate-club-progress.sql` (777 lines, md5 `76e61d1e…`, byte-identical to the audited file) + 19-check readback | **19/19 true.** 36 watch clubs and 66 memberships archived then deleted; `club_progress` with RLS, two read policies and **no** write policy; `save_progress`, `arr_union`, `club_session_visible`; the `groups_fold_sessions` trigger **attached**; a snapshot row for every surviving watch-club membership; `progress` confirmed un-re-keyed with its policies intact. **The only irreversible statement in the repo has now run.** First run recorded in the ledger as it happened | CLU-389 |

**`migrate-club-progress.sql` is the most recent change to production, and the
first one the database wrote down itself.** Its footer (lines 646–648) inserts a
single `schema_migrations` row *inside* the transaction — `filename`
`scratch/security/migrate-club-progress.sql`, `checksum`
`493ae4fb3285a9d933d40af89da145c2975215dd1e0cb68e8b26de669665d89d`,
`source = 'recorded'`, `outcome = 'applied'`, `evidence = 'CLU-389'`, with a note
naming the 36 clubs, the 66 memberships and the three objects created — so a
rollback would have un-recorded it, and the row exists only because the file
committed. **Yes: this run recorded itself.** `python tools/migrations.py`
computes that same `493ae4fb…` for the file on disk today, so the ledger and the
repo agree on the bytes that ran — the first time in this project that has been
true of anything.

**Queued behind it, written and not run: the CLU-153 pair**, under *Queued and
ready* below. Nothing else in the repo is waiting on a paste.

**From the ledger row (2026-08-27) the database records its own history.**
Everything above that row was reconstructed from the board. The three rows after
it split two ways: the two read-only pre-flights wrote nothing and so left no
ledger row — they are board-only, like everything before — and the migration
itself is the first row recorded at run time by the file that ran. `python
tools/migrations.py --verify` prints the read-only query that reads the ledger
back and compares checksums against the repo.

### Written and deliberately not run

These stay in `scratch/security/`, which is gitignored, because they describe
work that has not happened rather than the state that has.

⚠ **Gitignored is not the same as unpublishable.** `.gitignore` stops a file
becoming tracked and does nothing at all once one already is, and GitHub Pages
serves every tracked file — which is how two QA harnesses under `scratch/qa2/`
came to answer 200 on the live site (2026-09-10, CLU-414). `python
tools/notracked.py` now fails if anything is tracked under `scratch/security/`,
so this folder's guarantee is a command rather than a habit.

⚠ **Do not read that the other way round.** Since 2026-09-10 the folder also
holds `migrate-club-progress.sql`, which **has** run and is bootstrap step 14;
being in `scratch/security/` no longer implies unrun. It is the only such file,
and §3 says why it has not moved.

| File | Why |
|---|---|
| `FINAL-3-profiles.sql` | **Superseded by the CLU-153 pair** (`clu153-A` / `clu153-B`, *Queued and ready* below), which is FINAL-3 split in two so the function half can run ahead of the front end. Do not run it: it would do both halves in one paste, which is exactly what its fence exists to stop. The fence is **enforced in the file**, not merely commented, and still holds. *(This line used to say `find_profile_by_code` appears 0 times in the template; since CLU-153 it appears once, in `friendByCode()`.)* |
| `rls-fix-PART2-after-frontend.sql` | Same fence, comment-only, and **no transaction** — a mid-file failure leaves `profiles` with RLS on and its SELECT policy dropped. Superseded by FINAL-3, which is in turn superseded by the pair. |
| `migrate-fix-rls-column-locks.sql` | `rls-fix-PART1` + `rls-fix-PART2` concatenated, verified: after normalising line endings, 16,007 + 7,048 = 23,055 characters and the concatenation is identical. *(Raw byte counts do **not** add up — the PART files are CRLF and the combined file is LF. An earlier note here cited the raw numbers as proof, which anyone re-checking with `wc -c` would have found false.)* Never ran as itself. |
| `migrate-perf-shares.sql` | **Must never run.** It buys under 1%: CLU-397 established the slowdown was request *count*, not per-row cost — a ~926 ms fixed per-request floor against ~10 ms of per-row work. It would also create a sixth `shares_group_with`, with an **identical signature** to the live one, so `create or replace` replaces it silently rather than erroring. It stays unrun with the measurement in its header, so the next person looking at RLS performance finds the answer "not here". |
| `verify-groups.sql` | Read-only harness. Defines nothing. |
| `superseded/migrate-add-friend-privacy.sql` | Never ran. Proven, not assumed: the 2026-08-25 pre-flight showed `friend_may_read` did not exist yet (CLU-195). |

### Files that advertise themselves as safe and are not

- **`rls-fix-PART1-safe-now.sql`** is bootstrap step 7 and correct on an empty
  database. On a live one a re-run silently reverts four things — the
  pre-groups `shares_group_with`, the pre-`universal` `groups_guard_update`, and
  both friends-read policies back to their no-`friend_may_read` shape, which
  undoes the CLU-118 privacy switches for every user. It also has no
  transaction. **It now carries a banner naming all four**; its original header
  claimed "every step is guarded and safe to re-run".
- **`superseded/migrate-add-join-or-create.sql`** and
  **`superseded/migrate-add-owner-removal.sql`** both said "safe to re-run" and
  both would replace a live function body with an older one. Archived
  2026-08-27. The first is the serious one: its `join_or_create_group()` has no
  rate-limit calls, so running it removes the cap from one door while leaving
  `join_group()`'s intact — and a half-disarmed limiter reads as a working one.

### The largest thing in the repo, and it has now run

**`scratch/security/migrate-club-progress.sql`** (777 lines, CLU-389) **ran on
2026-09-10 at 21:38 UTC and returned 19/19**, minutes after
**`preflight-club-progress.sql`** read 6 PASS + 1 INFO. This section used to
exist because a migration written and not run is the state in which somebody
reasons about a database that does not match the file in front of them. It stays
for three reasons that outlive the paste: the audit history below is *why* the
run was uneventful, one exposure it names is still open, and the rules it
established about this file still bind anyone who touches it.

**It carried the only irreversible statement in the repo**: a delete of 36 watch
clubs and 66 memberships, by an explicit id list Nathan approved by eye on
2026-08-27 (keep-list on CLU-389; the four dated clubs confirmed separately on
CLU-404). The archive was written child-then-parent inside the same transaction,
before the delete, and the readback counted it: 36 rows in
`deleted_groups_20260827`, 66 in `deleted_group_members_20260827`, neither
readable through the API. **The delete has happened and cannot be re-asked.**
Those two tables are now the only record of the 36, so nothing in this project
may drop them.

⚠ **Do not hand-edit the `.sql`, and now there is a second reason.** It is
generated wholesale by `scratch/security/gen_club_progress.py`, which does an
unconditional `write_text`, so a hand edit is overwritten by the next
regeneration. And the file is no longer just a file: `schema_migrations` holds
`493ae4fb…` as the bytes that ran, and `tools/migrations.py` computes that from
the file on disk. **Any change to it breaks that match** — a hand edit silently
(the ledger now describes bytes nobody has), a regeneration openly (the checksum
moves and the row stops describing the file). If it must change, it changes for a
*second run*, and the ledger is append-only precisely so a second run is visible
rather than overwriting the first.

**Six defects found by audit on 2026-08-27 are fixed** (2026-08-28): the
orphaned id list before `begin;`, a drift guard that tested for the presence of
a date rather than for drift, `club_sync` not matching the deployed bundle's
`save_progress(p_property, p_club, p_ids)`, a cascade from the club rather than
the membership, an unguarded `tick_events.group_id`, and a missing existence
probe.

**A second, independent audit then found eight more**, all now closed. The one
that mattered: **it had no ledger footer and would have run unrecorded**, five
days after the ledger was built for exactly this. That fix is the one the run
cashed in — the row is in `schema_migrations`, checksummed, and this history
table is no longer the only evidence that the biggest migration in the project
happened. Also fixed — `revoke all`
rather than three named verbs (Supabase grants ALL by default, so TRUNCATE,
REFERENCES and TRIGGER survived a partial revoke), `to_regclass` rather than
privilege-filtered `information_schema`, three new readback checks including
one asserting the membership cascade that sixteen green checks had not covered,
and a separately runnable pre-flight, because commenting the id list to fix the
syntax error had made the advertised "run this first" step require hand-
stripping 36 uuids.

⚠ **One exposure shipped recorded rather than fixed, it is live as of
2026-09-10, and it is Nathan's call.** This is the one paragraph in this section
that is not history. The fold trigger exists because a Just-me untick is a
replace and can lower the universal row below a session that still holds those
ids. Under the membership cascade that is now in production, **leaving or being
removed hits that same window with no fold** — the trigger is `before delete on
groups`, and neither path deletes a group. `DECISIONS.md` §4 rules out a
fold-on-leave trigger on the premise that no id can exist in `club_progress` and
nowhere else — which is false for those few seconds. It is narrow (untick in
Just-me, then leave) and he has already ruled against a second definer trigger
writing other users' rows, so it stays open with its name written down. The file
says so too, at its `club_fold_on_delete` definition, so the next reader of
either finds it rather than discovering it.

**Order, and it is what happened:** the pre-flight ran first and was read
(~21:37, 6 PASS + 1 INFO), then the migration whole in one paste (21:38), then
the 19-row readback went onto CLU-389. The same order governs any re-run, and the
re-run question is not hypothetical — the file now **refuses**, because
`club_progress` exists and the delete-first safety argument no longer holds.
The guard is in its §1, inside the delete block and ahead of the archive insert
(not in §0, which only checks that `migrate-groups.sql` ran and would still
pass). A second run of this file as written raises *"club_progress already
exists — the delete-first argument does not hold, stop"* and rolls back — the
date-drift check ahead of it matches zero rows now that the 36 are gone, so
this is the first thing that fires. That is correct behaviour, not a defect.

⚠ **The pre-flight is ONE statement, and it has to stay that way.** It was five
separate `select`s, and on 2026-08-28 Nathan pasted it and got back a single
`must_be_zero = 0` — the last statement's result. The Supabase editor returns
only that when a file is sent whole, which is the same behaviour recorded on
CLU-424 and the reason the migration is written as one transaction. Four of the
five checks were invisible, and a pre-flight nobody can read is worse than none:
it looks like it passed.

It now folds every check into one `union all` returning a row each — `n`, `what`,
`verdict`, `detail` — so one paste answers everything, and each row reads `PASS`,
`STOP` or `INFO`. The per-club listing that used to be check 2 is kept at the
bottom **commented out**, with a note not to paste it with the rest, because
appending it would make it the last statement and hide the verdicts again.

Anything added to this file later must go inside that single select.

⚠ **Check 4 carried the migration's first audited defect, and it was only
caught when Nathan ran it.** The migration's drift guard was fixed on
2026-08-28 to compare live dates against the *surveyed* dates, because nine of
the 36 clubs carried a date when the list was approved. The pre-flight, written
in the second audit round, re-asked the older question — "does any listed club
carry a date at all" — under the label "gained a date since the survey". So it
was guaranteed to read STOP on every clean run, naming the same nine clubs each
time, and on 2026-09-10 it did. Two replies on CLU-389 then told Nathan those
nine had "since put a date on", which was false; the survey file had those dates
all along.

Fixed 2026-09-10: the `del` CTE now carries `(id, target, sched)` from the
frozen file and check 4 uses `is distinct from` on both columns — the same test
the migration runs, so the two cannot disagree. The generator parses the CTE's
36 triples back out and asserts them equal to the frozen file *by id* (a bag of
dates would pass with two rows swapped). The audit of that fix added three
small honesty changes to the same check: the PASS text counts the rows that
joined rather than hard-coding 36, and a STOP names each club with the first
eight characters of its id, because two of the dated nine are both called
`#greenringgang`. **The migration file did not change** (`76e61d1e…`); the
pre-flight is now 152 lines, md5 `47cf964c…`, and a second independent audit of
the finished file (2026-09-10, ten checks, five mutants) returned SAFE. A STOP
on check 4 now means a date really moved.

**It cleared the same evening.** The re-run at ~21:37 returned 6 PASS and the
single 1174-id INFO — check 4 among the PASSes — and the migration went in the
same sitting. **That defect was the whole delay**: the file had been finished
since 2026-08-28 and was held for two weeks by a check that could never go
green, which is what a pre-flight costs when its label and its test ask
different questions.

Check 1 was widened in the same edit, ahead of a change that is *coming*: CLU-408
gives every fresh watch its own progress row, `<slug>#fw<start>`, where today
the only rewatch row is `<slug>#fw`. The check used to STOP on any suffix other
than exactly `fw`; it now STOPs on any suffix that does not *begin* with `fw`
(`!~ '^fw'`), so the first fresh watch started after CLU-408 ships cannot turn a
clean pre-flight red. The audit notes this makes it a weaker canary — `#fwx`
would pass — and that it does not matter to this migration: the snapshot joins
`progress` to `groups` on exact `property_id` equality, and a group's
`property_id` never carries a `#`, so no suffixed row of any shape can reach
`club_progress`. Check 1 only decides whether Nathan is told to stop, never what
is written. **Settled by the event:** the snapshot ran on 2026-09-10 and covers
every watch-club membership (readback 11), so no suffixed row reached
`club_progress` — check 1 now matters only if the pre-flight is re-used for
something else.

### Queued and ready: the friend-code lookup, in two files (CLU-153)

`profiles` is readable by every signed-in user, and the only reason it has to
be is that "add a friend by code" reads it directly (`?fcode=eq.<code>`). The
fix is a definer function for the lookup and a narrower read policy — which is
what `FINAL-3-profiles.sql` did in one paste, and why it could never run: the
policy half breaks "add by code" for everyone until a front end that calls the
function is live, so the whole file was fenced on that. Split, the function
can go in today and the policy waits on its own.

| Order | File | What it does | Must be true before it runs |
|---|---|---|---|
| 1 | `scratch/security/clu153-A-find_profile_by_code.sql` | Creates `find_profile_by_code(text)` — definer, `search_path = public, pg_temp`, refuses anonymous callers, `upper(btrim())`s the code, exact match, one row `(user_id, username, fcode)` or none; misses charged through `rate_limit_guard`/`rate_limit_note` under kind `'fcode'` (20/hour, 60/day, per user). Revoked from `public, anon, authenticated`, granted to `authenticated`. Touches no policy, no table grant and no row of user data; inserts its own ledger row. | Nothing beyond the rate-limit helpers (CLU-35, live) and the ledger (CLU-404, live). **Safe now and safe to re-run — but not inert.** The RPC-calling front end is already deployed, so the moment A commits, live lookups move onto it: they become rate limited, and two sentences that live in this file can reach users. |
| 2 | `scratch/security/clu153-B-narrow-profiles.sql` | Drops `"profiles readable when signed in"` and creates `"read own profile"` (`auth.uid() = user_id`) and `"read connected profiles"` (an edge in either direction in `friendships`). One transaction, so the drop cannot land without both replacements. Asserts exactly two SELECT policies afterwards. Records itself. | **File A has run, the `index.html` live on clubd.watch calls `find_profile_by_code`, and a deliberate MISS on the live site has been seen to add a `kind = 'fcode'` row to `rate_events`** — which is the only evidence that distinguishes the function from the fallback. Enforced: the file raises unless its `set_config` line is live, *and* it checks the function exists and `authenticated` can execute it. Arm it with `python scratch/security/arm-clu153-B.py` immediately before pasting — that spends the fence and re-stamps the checksum together. |

**The front end is ahead of both.** Since CLU-153 `friendByCode()` calls
`rpc('find_profile_by_code', {p_code})` first and does the direct read only
when PostgREST answers `PGRST202` or `42883` (no such function). A `42501` or a
rate-limit `PT429` surfaces as an error and does not widen into a table read.
So the order of events is: front end live (already) → **A** → prove on the live
site that the function is actually serving the lookup → **arm B** → **B**.

That third step is not "confirm add-by-code works". It is a `rate_events` count
either side of a **deliberate miss**, because the fallback succeeds too and a
working add-by-code cannot tell the two paths apart. B's own header carries the
exact steps, and the audit note below says why. Before A runs, the site behaves
exactly as it does today, at the cost of one 404 per lookup.

#### A six-lens hostile audit rewrote what these files say about themselves

Run 2026-09-10 after Nathan asked whether the SQL auditor had been run at all
(*"i dont see a mention of it"*). Six independent auditors, every serious finding
then put to two skeptics told to refute it. **No executable statement changed.**
Four things they say about themselves did, and all four mattered:

- **A's banner said "SAFE TO RUN NOW, BEFORE THE FRONT END CHANGES" and "the
  site behaves exactly as it does today".** Both were written before commit
  `7e48b60` shipped the RPC-calling front end. A is not a dormant function: the
  moment it commits, live lookups move onto it, which means they **become rate
  limited** and **two sentences that live in the SQL file can reach users**.
  Nothing breaks — but the old banner removed the reason to test the live site
  afterwards, and that test is the entire content of B's fence.
- **B asked for the wrong evidence.** Its precondition was "you have added a
  friend by code there". The deployed `friendByCode()` falls back to the direct
  read on `PGRST202` — precisely the error a stale PostgREST schema cache
  returns — and then **succeeds**, so a working add-by-code is the same
  observable event whether the function served it or the old read did. The
  replacement is a before/after count of `select count(*) from rate_events
  where kind = 'fcode';` around a **deliberate miss**, because only a miss
  writes that row.
- **B claimed the narrowed policy leaves everyone else "reachable only by
  holding their code".** It does not. `migrate-add-friends.sql`'s
  `"add own direction"` insert policy constrains only column `a`, uncapped, so
  **a held `user_id` is as good as a held code**: insert one `friendships` row
  and you may read that person's username and code. B is still a strict
  narrowing and worth running; it is not the whole answer.
- **B's footer checksum covers its own fence line**, so arming by hand breaks
  the ledger: the row the file writes about itself would carry the digest of the
  *fenced* bytes while the bytes that executed were the *armed* ones. `--verify`
  compares the recorded digest against the file on disk, so from then on the
  strongest record this project has would disagree with the repo about a file
  that ran perfectly — and nobody could tell that apart from tampering. So
  arming is one command, `python scratch/security/arm-clu153-B.py`, which spends
  the fence and re-stamps the checksum together, validates the footer *before*
  it touches the fence so a failure leaves the file unrunnable, and is
  idempotent. **Run it immediately before pasting B.** It does not re-fence
  afterwards: an armed B stays armed, and the remaining backstop is its check
  that the function exists and `authenticated` may execute it.

  ⚠ *An earlier version of this section claimed that leaving the fence commented
  would make `--verify` falsely confirm the unrunnable file had run. That was
  wrong and the verification pass caught it: a fenced paste raises, the
  transaction rolls back, and **no ledger row is written at all** — so there is
  nothing for `--verify` to compare. The reason to use the script is the
  hand-arming case above, not that one.*

Four smaller corrections came out of the same pass: A's readback comment claimed
a wrong-shape lookup "charges one miss" when the block is `begin; … rollback;`
and charges nothing; A said its prefix was deliberately unpinned when
`length(want) <> 8` pins it; A's expected `proacl` did not predict the
`service_role` entry Supabase grants by default, which is not a failed revoke;
and B's ONE TRANSACTION paragraph lacked A's **"never half"** warning, which
belongs there far more — a paste that stops after the drop leaves `profiles`
with no read policy inside an uncommitted transaction still holding
`ACCESS EXCLUSIVE` on it.

**Do not read either file's checksum out of this document.** Ask the tool —
`python tools/migrations.py --footer <file>` — because a digest quoted in prose
goes stale the moment anyone edits a comment, and A's has already been
regenerated three times (`c062c104…`, then `f601420c…`, then the value it now
carries). A's footer matches its own body. **B's deliberately does not**:
`arm-clu153-B.py` re-stamps it at arming time, so B is the one file here whose
recorded checksum is written minutes before it runs, and the value sitting in it
now describes no version of the file.

⚠ **The audit could not and did not check the database.** Every statement it
makes about live state comes from this document and the migration files. Whether
`profiles` still has RLS enabled, what its policies are right now, and whether
every stored `fcode` is the eight-character shape A's check requires are all
things only a read can answer.

Both are FINAL-3 lifted verbatim — the function, the three policy statements
and the readback — with the fence moved to B and rewritten to name the pair,
and B's post-run note corrected: FINAL-3 warned of a PostgREST schema-cache
window after the paste, which existed only because it created the function and
closed the directory together. `tools/ordercheck.py` is clean on both;
`tools/whereis.py` lists both as never run.

⚠ **`whereis.py` was itself a migration stale until the audit caught it**, and
it is the tool §2 tells you to run before every paste. Its `APPLIED` list ended
at `migrate-add-schema-ledger.sql` and omitted `migrate-club-progress.sql`,
which ran on 2026-09-10 — so it reported `save_progress`, `club_progress`,
`arr_union`, `club_session_visible` and the `groups_fold_sessions` trigger as
objects that **do not exist in the database**. A safety tool that names ten live
objects as missing is worse than no safety tool, because it is read and
believed. Fixed; it now flags exactly the three CLU-153 objects, which really
are absent.

⚠ **After these two run, the repo will hold three live migrations that a fresh
clone does not contain** — this pair plus `migrate-club-progress.sql` — because
all three live in the gitignored `scratch/security/`. Both record themselves
with path-qualified filenames under `scratch/`, so `--verify` joins against
paths that a clone cannot produce. §3 already carries this warning for
`migrate-club-progress.sql`; it applies to all three now, and the question of
what should be published is CLU-414.

**Until B runs, `profiles` is still the open directory §4 describes.** A copy
already taken is not undone by B; that is the reason not to let it wait.

### And three that fail safely — leave them alone

`migrate-add-friends.sql`, `migrate-add-friend-decline.sql` and the archived
`migrate-add-friend-shelves.sql` use bare `create policy`, no drop, no guard. A
second run raises `42710` and changes nothing. That is *luck*, but it is
load-bearing luck: `create policy` has no `or replace` form, so they cannot
clobber. **Adding `drop policy if exists` to make them "idempotent" would turn
`migrate-add-friend-shelves.sql` into the most destructive file in the repo**,
because the policy it defines has since been replaced twice. Do not tidy them.

`schema.sql` is only partly idempotent: its policies sit in two
`do $$ ... exception when duplicate_object then null` blocks, each wrapping
several statements under one handler. If the first policy in a block already
exists, the exception aborts the block and the rest are never created — and it
reports success either way. **A half-applied `schema.sql` cannot heal itself by
being re-run.**

---

## 6. What is genuinely unknown

An honest gap is safe. A confident guess is not.

1. **Everything before 2026-08-27 rests on reconstruction, and always will.**
   The ledger (CLU-404) now records every run from here on, but its eighteen
   backfilled rows are the old history copied in, not observed: where a readback
   was pasted (CLU-387 19/19, CLU-392 7/7, CLU-390 5/5, and the policy dumps on
   CLU-195 and CLU-34) the claim rests on the database's own answer; everywhere
   else it rests on inference. **Three of the eighteen carry
   `outcome = 'unknown'`** because no run record exists for them at all, and
   none of the eighteen carries a checksum — nobody knows the bytes that ran,
   and several of those files have been edited since.

   **The first row the ledger wrote at run time is different in kind**, and there
   is now exactly one: `migrate-club-progress.sql`, 2026-09-10, `source =
   'recorded'`, with a checksum that still matches the file. Everything before it
   is testimony; that row is a receipt.

   **The ledger does not close item 2 either.** It records what it is *told*,
   which is far better evidence than a comment thread and still not the
   database's own account of its own functions.
2. **No function body in production has been compared against a file.** If
   something were edited by hand in the SQL editor, nothing here would show it.
   The only honest check is to run each file's readback block, which is
   read-only.
3. **Anything done outside the SQL editor is invisible here.** Supabase's Table
   Editor can change grants; a dashboard action leaves no trace in the repo or
   on the board.
4. **Which schema `pgcrypto` landed in.** `migrate-groups.sql` §0 is the only
   thing that would ever find out.
5. ~~**Whether `club_progress` and `save_progress` exist live.**~~ **Known since
   2026-09-10 21:38 UTC: they exist.** The migration ran and its 19-check
   readback is the database's own answer — `club_progress` with RLS on, exactly
   two policies and both `SELECT`, no write policy, `insert`/`update`/`delete`/
   `truncate` denied to `authenticated` and `select` allowed,
   `save_progress(text,uuid,text[])` executable by `authenticated` and not by
   `anon`, `arr_union` by neither, `club_session_visible` by both,
   `groups_fold_sessions` attached, and the snapshot covering every watch-club
   membership (CLU-389). The front end's degradation path is now unreachable on
   production, which also means **nothing live would tell you if the table were
   dropped tomorrow** — it would simply look like the old behaviour coming back.

   **What that readback did not settle is item 2.** It tested privileges, policy
   counts, constraint shapes and trigger attachment — not a single function
   *body* against its file. The ledger row does pin the bytes that were pasted
   (`493ae4fb…`, still what `tools/migrations.py` computes for the file), which
   is the strongest evidence any run in this project carries; it is evidence
   about the paste, not about what the database holds now.

---

## 7. The maintenance rule

**Update this file in the same change as the migration — including a migration
that is only planned.**

Not after it runs. The dangerous window is exactly the one where a file has been
written and not yet executed, because that is when somebody reasons about a
database that no longer matches the file in front of them.

This project has already paid for the alternative. `schema.sql` went behind,
nothing said so, and **two separate pieces of work were built on it confidently
and wrongly** (CLU-374) — one of which would have deleted a live rate limiter.
`tools/whereis.py` exists because of it, and reports that **23 of 74 objects are
defined in more than one file**, whichever runs last winning silently.

A document like this is trusted on sight, which is what makes a stale one worse
than none: nobody re-derives what it claims, so a wrong line is believed and
acted on.

**When something is superseded, say what replaced it rather than deleting the
line.** A reversal is itself a decision, and the next reader needs to know the
question was asked twice.

### Standing safety rules

- **SQL is never executed by an agent.** It is written here and run by hand in
  the Supabase SQL editor against a database with real users.
- **Every migration is audited by someone other than its author** before it is
  queued for running.
- **A card carrying unrun SQL sits in `run SQL`**, never in Live or Done. Code
  shipping ahead of its migration is the most common way a feature half-works in
  production.
- **Archiving means moving a file into `superseded/`. It never means dropping a
  database object**, and it never means deleting the file — a superseded file is
  often the only surviving record that a change was made.
