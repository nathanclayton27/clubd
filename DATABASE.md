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

Thirteen files, in this order, all at the repo root.

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
```

All thirteen are live. Step 13 ran on 2026-08-27 with a 14/14 readback
(CLU-404), so from here on the database keeps its own record of what has been
run and this section stops being the only one.

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

### This is Supabase-only, and it fails at step 1 elsewhere

**No file in this repo creates the `anon`, `authenticated` or `service_role`
roles.** `schema.sql` revokes and grants on them, and the path references them
61 / 67 / 39 times. On stock Postgres it dies at step 1 with `42704`.

A second, later divergence: `schema.sql` runs `create extension if not exists
pgcrypto` **unqualified**, while `migrate-groups.sql` §0 demands
`extensions.gen_random_bytes`. On Supabase that resolves; on stock Postgres
pgcrypto lands in `public` and step 10 refuses.

### Two things this path does not give you

1. **`club_progress` and `save_progress`.** The front end calls both and **no
   file in this repo creates either.** That is not a gap in the path — the site
   discovers their absence and degrades: `missingThing()` catches `42P01`,
   `PGRST205`, `42883` and `PGRST202`, the `CPGONE` / `SAVEGONE` latches trip
   once per load, and session ticks fold back into the all-time row. So the path
   reproduces everything the repo describes, and "reproduces the live database"
   is only true if those two do not exist live, which no file can tell you.
2. **Data.** Obviously. It builds the shape, not the contents.

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

**`tick_events`** — append-only log of when you ticked and whether it was
`live` or `backfill`. Read and written by you only. Nobody else ever sees it;
the distinction exists so a batch import cannot look like tonight's viewing.

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

**`profiles`** — friend code and username. Four-column grant. Readable by any
signed-in user today; `FINAL-3` would narrow that and has not run.

**`friendships`** — one row per direction. Mutual means both rows exist. You may
add your own direction, remove your own, and decline an incoming one.

**`private_properties`** — lists treated as private by policy. One row today.
Empty, the gated-list term in every policy is a no-op, which is why step 7
without step 8's insert protects nothing.

**`rate_events`** — join-attempt counting behind `guard_group_join_rate()`.

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

**The last line is the most recent change to production. Nothing is queued
behind it.**

**From this point the database records its own history.** Everything above the
last row was reconstructed from the board; everything after it is recorded at
run time by the migration itself. `python tools/migrations.py --verify` prints
the read-only query that reads it back and compares checksums against the repo.

### Written and deliberately not run

These stay in `scratch/security/`, which is gitignored, because they describe
work that has not happened rather than the state that has.

| File | Why |
|---|---|
| `FINAL-3-profiles.sql` | Fenced on a front-end change that has not shipped (CLU-153). The fence is **enforced in the file**, not merely commented. Verified still valid: `find_profile_by_code` appears 0 times in `src/template.html` and 0 times in the built `index.html`. |
| `rls-fix-PART2-after-frontend.sql` | Same fence, comment-only, and **no transaction** — a mid-file failure leaves `profiles` with RLS on and its SELECT policy dropped. Superseded by FINAL-3. |
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
5. **Whether `club_progress` and `save_progress` exist live.** No file creates
   either, and the front end is built to survive their absence — so their
   absence is invisible from the outside.

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
