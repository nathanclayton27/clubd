-- ===========================================================================
-- GROUPS: one roster, every list.       CLU-387 / CLU-114 / CLU-376 / CLU-388
-- ===========================================================================
-- Idempotent. Safe to run twice. Rewrites no rows and deletes no user data.
--
-- VERSION 3. Versions 1 and 2 were both audited and rejected. Read the audit
-- history before reviewing — the interesting parts of this file are the places
-- where an earlier version looked obviously right and was not.
--
-- ---------------------------------------------------------------------------
-- V1 -> V2: THE STALE-DEFINITION REGRESSION
-- ---------------------------------------------------------------------------
-- V1 did `create or replace function join_group(...)` with a body copied out
-- of schema.sql. schema.sql IS A MIGRATION BEHIND for functions: the live
-- join_group() is the rate-limited one in migrate-add-rate-limits.sql. That
-- replace would have silently deleted guard_group_join_rate(),
-- rate_limit_note('join'), the code shape check, the NULL-on-miss contract the
-- front end depends on, the `do update set display_name` clause, and pg_temp
-- — the entire brute-force protection on club codes, removed by a migration
-- whose stated purpose was adding a boolean.
--
-- V2 AND V3 DO NOT TOUCH join_group() AT ALL. The refusal it was there to add
-- is achieved structurally instead:
--
--        A GROUP HAS NO CODE. code IS NULL FOR EVERY UNIVERSAL ROW.
--
-- join_group() looks a group up BY code, so a row with no code cannot be found
-- by any code. Enforced by a CHECK constraint (§1) and by the trigger (§1b),
-- not by a line of plpgsql a future migration could overwrite the same way V1
-- nearly overwrote the rate limiter.
--
-- ---------------------------------------------------------------------------
-- V2 -> V3: TWO BLOCKING FINDINGS, BOTH ONE-LINERS, BOTH WORTH UNDERSTANDING
-- ---------------------------------------------------------------------------
-- F1. V2 granted EXECUTE on group_may_read() to anon and authenticated, with
--     a comment claiming policy expressions run as the querying role. THAT
--     COMMENT WAS FALSE HERE. group_may_read is named by no policy; its only
--     caller is shares_group_with(), which is SECURITY DEFINER, and inside a
--     definer function EXECUTE is checked against the function OWNER. The
--     grant bought nothing and cost a privacy oracle: any caller, including
--     anon with the key that ships inside index.html, could probe
--     group_may_read('<any uuid>', '<any slug>') across the catalogue and
--     read back that person's exact hidden-list set — the very leak FINAL-2
--     revoked column SELECT on profiles to close.
--
--     friend_may_read IS granted, and that is not a contradiction: it appears
--     DIRECTLY in the policy expressions in FINAL-1 §6, where the querying
--     role really is what matters. The difference is where the function is
--     named, not what it does.
--
-- F2. V2 called is_private_property(prop) with the raw prop. Every other call
--     site in this project strips the rewatch suffix first (FINAL-1 §6 passes
--     split_part(property_id,'#',1)). V2 worked only because FINAL-1's body
--     re-splits internally as belt-and-braces — so V2 made the belt
--     load-bearing. Two files still in this tree (migrate-fix-rls-column-locks
--     and rls-fix-PART1) contain the OLDER body with a bare `property_id =
--     prop`, and this project's documented remedy for a tripped guard is
--     "re-run the file". Re-running either one after FINAL-1 would silently
--     revert is_private_property, and from that instant every co-member of a
--     universal group could read every other member's rewatch progress on the
--     password-gated list. §0 now checks the BODY, not merely that it exists.
--
-- ---------------------------------------------------------------------------
-- THE READ SCOPE IS THE PART THAT MATTERS
-- ---------------------------------------------------------------------------
-- shares_group_with() is scoped to one property ON PURPOSE. schema.sql names
-- the failure it prevents: someone in your Fullmetal Alchemist group reading
-- your Secret Wars progress. Relaxing it is what makes a group possible, and
-- Nathan ruled on exactly how far.
--
-- CLU-185: yes for public lists, never for the gated one.
-- CLU-388: and the owner's privacy switches apply to the group half.
--
--   setting            | club co-member, that list | friend | group-only
--   -------------------+---------------------------+--------+-----------
--   nothing            | sees                      | sees   | sees
--   hide from groups   | sees                      | sees   | hidden
--   hide from friends  | sees                      | hidden | hidden
--
-- "being in a club implies you want to share progress with club members"
-- — so THE CLUB BRANCH IS UNCONDITIONAL and no switch may hide it, while the
-- group branch consults every switch below.
--
--   scope        | from friends                | from groups
--   -------------+-----------------------------+---------------------------
--   everything   | profiles.share_progress     | profiles.share_with_groups
--   one list     | profiles.hidden_slugs       | profiles.hidden_from_groups
--   one group    | —                           | group_members.share_with_group
--
-- And one rule ties them: ANYTHING HIDDEN FROM FRIENDS IS HIDDEN FROM GROUPS
-- at the same scope, one-way. Turning a friends hide back off does not
-- restore groups. Enforced in §6 server-side, not only in the checkbox,
-- because it is a safety property: without it, un-hiding from friends would
-- silently restore visibility to coworkers too, one click quietly widening
-- the audience past the one the person was thinking about.
--
-- ORDER: run AFTER FINAL-1, FINAL-2 and migrate-add-rate-limits. §0 refuses
-- otherwise. AND SEE "FRONT-END ORDERING" AT THE BOTTOM — one front-end change
-- must be deployed BEFORE the first universal group is created.
-- ===========================================================================

begin;

-- §0 ---------------------------------------------------------------- guard --
-- Five refusals. Each names something this file depends on and would silently
-- weaken if it were absent or stale. Note that three of these check a BODY
-- rather than mere existence: "the function exists" is the assumption that got
-- V1 rejected, and F2 showed it was still hiding in V2.
do $$
declare src text;
begin
  -- FINAL-1: the predicate that keeps the gated list out of the group branch.
  if to_regprocedure('public.is_private_property(text)') is null then
    raise exception
      'is_private_property(text) is missing — run FINAL-1 first. Refusing to '
      'widen group reads without the predicate that keeps the gated list out.';
  end if;

  -- ...and that it is FINAL-1's body, not the older one from
  -- migrate-fix-rls-column-locks / rls-fix-PART1. See F2 in the header.
  select prosrc into src from pg_proc
   where oid = 'public.is_private_property(text)'::regprocedure;
  if src not like '%split_part%' then
    raise exception
      'is_private_property is the PRE-FINAL-1 body (no split_part) — re-run '
      'FINAL-1 first. Proceeding would let group members read rewatch rows on '
      'the gated list.';
  end if;

  -- FINAL-2: the switches the group branch has to honour (CLU-388).
  if to_regprocedure('public.privacy_settings()') is null then
    raise exception
      'privacy_settings() is missing — run FINAL-2 first. Refusing to widen '
      'group reads before the privacy switches they must obey exist.';
  end if;

  -- Rate limits: not modified by this file, but its absence means the database
  -- is older than this migration was written against, and join_group() is then
  -- not the function the audit reasoned about.
  if to_regprocedure('public.guard_group_join_rate()') is null then
    raise exception
      'guard_group_join_rate() is missing — run migrate-add-rate-limits.sql '
      'first. This database is older than this migration was written against.';
  end if;

  -- AUDIT F4: new_join_token() is plpgsql, so `extensions.gen_random_bytes` is
  -- resolved at RUNTIME, not at CREATE. Without this check the migration
  -- COMMITS CLEAN, every readback passes, and the first person to click
  -- "create a group" gets "function extensions.gen_random_bytes does not
  -- exist". schema.sql installs pgcrypto unqualified, so nothing in this repo
  -- establishes where it landed. Fail now, loudly, instead of later, quietly.
  if to_regprocedure('extensions.gen_random_bytes(integer)') is null then
    raise exception
      'pgcrypto is not in the extensions schema — new_join_token() would fail '
      'at runtime, AFTER this file commits clean. Install it or change the '
      'schema qualification before running this.';
  end if;
end $$;

-- §1 ------------------------------------------------------------- the flag --
alter table public.groups
  add column if not exists universal boolean not null default false;

-- A group has no property and no code. Every existing row is a watch club with
-- both, so the constraint validates immediately without rewriting anything.
alter table public.groups alter column property_id drop not null;
alter table public.groups alter column code        drop not null;

-- THIS CONSTRAINT IS THE SECURITY BOUNDARY, not a tidiness rule.
--   universal  => code is null      the code door cannot reach a group
--   watch club => code is not null  every club keeps exactly what it had
--
-- AUDIT F7: V2 wrapped this in a bare duplicate_object handler, which would
-- silently accept a PRE-EXISTING constraint of the same name with a DIFFERENT
-- body — swallowing exactly the kind of drift this constraint exists to stop.
-- Now it verifies what it found and raises if it is not the rule we wanted.
do $$
begin
  alter table public.groups add constraint groups_scope_ck
    check ((universal     and property_id is null and code is null)
        or (not universal and property_id is not null and code is not null));
exception when duplicate_object then
  -- AUDIT G2: the first version of this check was `not like '%universal%code%'`,
  -- which cannot produce a false FAILURE but can produce a false PASS — it
  -- would happily accept a materially weaker rule of the same name, such as
  -- `check (not universal or code is null)`, which permits universal = true
  -- with a NON-NULL property_id and re-aims the whole group at one list.
  -- Assert the sub-predicates instead of two tokens in an order.
  declare def text;
  begin
    select pg_get_constraintdef(oid) into def from pg_constraint
     where conrelid = 'public.groups'::regclass and conname = 'groups_scope_ck';
    if def not like '%NOT universal%'
       or def not like '%property_id IS NULL%'
       or def not like '%code IS NULL%'
       or def not like '%property_id IS NOT NULL%'
       or def not like '%code IS NOT NULL%' then
      raise exception
        'groups_scope_ck already exists with a WEAKER definition (%) — inspect '
        'it before proceeding. This constraint is what keeps the code door '
        'away from universal groups.', def;
    end if;
  end;
end $$;

-- `unique` already permits many nulls (NULLS NOT DISTINCT must be asked for
-- explicitly), so many groups sharing "no code" is fine and clubs keep their
-- uniqueness exactly as it is.

-- §1b ------------------------------------------- a group cannot change kind --
-- AUDIT F7. groups_guard_update() pins property_id, code, created_by, id and
-- created_at, but knew nothing about `universal`, and authenticated retains
-- table-level UPDATE on groups. The CHECK does hold the line today — flipping
-- universal requires simultaneously changing code/property_id, which the
-- trigger rejects — but that leaves the whole defence resting on one
-- constraint. If a group could be converted into a watch club for the gated
-- list, every member would gain unconditional read on that list's progress
-- through the club branch: no password, no switch, no error.
--
-- Body below is COPIED VERBATIM from migrate-fix-rls-column-locks.sql:113-137,
-- the live definition, with exactly one clause added. Not reconstructed from
-- memory — that is the mistake this file's history is made of.
-- AUDIT G3: schema-qualified and given an explicit search_path, which the live
-- definition lacks. The body touches no relations, so this is hardening rather
-- than a fix — but an unqualified `create or replace` creates in the FIRST
-- schema of the search_path rather than "wherever the live one is", which is a
-- pattern this project has been bitten by before.
create or replace function public.groups_guard_update()
returns trigger language plpgsql security invoker
set search_path = public, pg_temp as $$
begin
  if current_user not in ('anon', 'authenticated') then
    return new;
  end if;
  -- the column shares_group_with() scopes on. Changing it re-aims every
  -- member's consent at a list they never agreed to share.
  if new.property_id is distinct from old.property_id then
    raise exception 'a group cannot change property — make a new group instead';
  end if;
  -- a code that has been handed out must keep meaning the same group
  if new.code is distinct from old.code then
    raise exception 'a join code cannot be changed';
  end if;
  -- ADDED (CLU-387): a universal group and a watch club are read under
  -- different rules — one consults the owner's privacy switches, one is
  -- unconditional. Converting between them would re-aim consent just as
  -- surely as changing the property, and in the more dangerous direction.
  if new.universal is distinct from old.universal then
    raise exception 'a group cannot change kind — make a new one instead';
  end if;
  -- with check already pins this to auth.uid(); saying so here means the rule
  -- does not depend on the policy staying the way it is
  if new.created_by is distinct from old.created_by then
    raise exception 'ownership is not transferable';
  end if;
  if new.id is distinct from old.id or new.created_at is distinct from old.created_at then
    raise exception 'identity columns are not editable';
  end if;
  return new;
end $$;

-- AUDIT G1 — THE GAP THAT NEARLY MADE §1b DECORATIVE.
--
-- `create or replace function` preserves a trigger's link to it ONLY IF THE
-- TRIGGER ALREADY EXISTS. V3 replaced the function and stopped there. If
-- rls-fix-PART1 / migrate-fix-rls-column-locks never ran on this database, the
-- replace would have created an ORPHAN function with no trigger attached: the
-- migration commits clean, every readback passes (none of them looked at
-- pg_trigger), and the entire §1b boundary is inert.
--
-- With the trigger absent, `authenticated` still holds UPDATE on groups under
-- "creator updates group", and one PATCH moving universal, property_id and
-- code together SATISFIES groups_scope_ck — converting a universal group into
-- a watch club for the gated list, and handing every member unconditional read
-- through the club branch.
--
-- FINAL-VERIFICATION.md calls PART 1 "in force (as confirmed from pg_policies)"
-- — and pg_policies does not show triggers. So the one document establishing
-- this dependency does not cover the object §1b depends on. Rather than add a
-- pre-flight query someone has to remember to run, the trigger is simply
-- (re)created here. Idempotent, and cheap.
drop trigger if exists groups_update_guard on public.groups;
create trigger groups_update_guard
  before update on public.groups
  for each row execute function public.groups_guard_update();

-- §2 ------------------------------------------------------- the join token --
-- AUDIT (v1 F3): v1 put this in groups.join_token. Every member can read the
-- whole groups row — the SELECT policy is row-level, there are no column
-- grants, and the front end does select('*'). For a group the token is the
-- ONLY door, so a member-readable token means any member can hand a stranger
-- permanent access to the roster.
--
-- Own table, own policy, owner only.
create table if not exists public.group_join_tokens (
  group_id   uuid primary key references public.groups(id) on delete cascade,
  token      text not null unique,
  created_at timestamptz not null default now()
);

alter table public.group_join_tokens enable row level security;

-- Only the group's creator may read it. Members get nothing: the token reaches
-- other people as a link the owner sends, never as a row they select.
drop policy if exists "owner reads join token" on public.group_join_tokens;
create policy "owner reads join token" on public.group_join_tokens
  for select using (
    exists (select 1 from public.groups g
             where g.id = group_join_tokens.group_id
               and g.created_by = auth.uid()
               and g.universal)
  );

-- No insert/update/delete policy at all: the table is written only by the
-- security-definer functions below, which bypass RLS. A client cannot mint,
-- change or clear a token directly.

-- AUDIT (v1 F4): v1 used random() — a 48-bit-state PRNG, shared across the
-- session and observable by anyone who can call a function that draws from it.
-- Tokens minted under it are guessable however many characters they have,
-- which made v1's "~110 bits" claim false. gen_random_bytes() is pgcrypto's
-- CSPRNG, named with its schema because §0 has just proved where it lives.
create or replace function public.new_join_token()
returns text language plpgsql security definer
set search_path = public, pg_temp as $$
declare
  alphabet text := 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  raw bytea; t text; i int;
begin
  loop
    raw := extensions.gen_random_bytes(22);
    t := '';
    for i in 1..22 loop
      -- & 31 maps a byte onto the 32-character alphabet with no modulo bias,
      -- because 256 is an exact multiple of 32. get_byte is 0-based.
      t := t || substr(alphabet, 1 + (get_byte(raw, i - 1) & 31), 1);
    end loop;
    exit when not exists (select 1 from group_join_tokens where token = t);
  end loop;
  return t;             -- 22 chars x 5 bits = 110 bits, and now genuinely 110
end $$;

-- §2b ------------------------------------------- the privacy columns, early --
-- THESE LIVE HERE, NOT IN §6, AND THE REASON IS A BUG THAT GOT PAST THREE
-- AUDITS AND ONE REAL RUN.
--
-- v4 had them in §6, after the functions. Running it failed at the first
-- attempt with:
--
--     ERROR: 42703: column p.share_with_groups does not exist
--     LINE 371:  and p.share_with_groups
--
-- because group_may_read() and shares_group_with() are `language sql`, and a
-- SQL function body is PARSED AND VALIDATED AT CREATE TIME — every column
-- reference in it is resolved right then. plpgsql is the one that defers to
-- runtime. The audit had reasoned about exactly this asymmetry in the other
-- direction (it is why a missing pgcrypto would NOT have failed at CREATE,
-- since new_join_token() is plpgsql) and nobody turned it around to ask what
-- the `language sql` functions therefore require.
--
-- So: columns first, predicates second. The transaction meant the failed run
-- rolled back whole and the database was untouched.
--
-- ---------------------------------------------------------------------------
-- THE FULL SET OF ORDERING CONSTRAINTS IN THIS FILE — DO NOT REORDER SECTIONS
-- WITHOUT RE-CHECKING THESE.
-- ---------------------------------------------------------------------------
-- §2b's constraint was the one that bit, but it is not the only one. Every
-- edge below is resolved at CREATE time and will hard-error if the left side
-- moves below the right:
--
--   groups.universal (§1)            -> the CHECK groups_scope_ck (§1)
--   groups.universal (§1)            -> the token RLS policy (§2)
--   groups.universal (§1)            -> shares_group_with() (§3)
--   groups.universal (§1)            -> group_join_link() (§5)
--   groups_guard_update() (§1b)      -> its trigger (§1b)
--   group_join_tokens (§2)           -> the token RLS policy (§2)
--   group_join_tokens (§2)           -> group_join_link() (§5)
--   profiles.share_with_groups (§2b) -> group_may_read() (§3)
--   profiles.share_with_groups (§2b) -> privacy_settings() (§6)
--   profiles.hidden_from_groups(§2b) -> group_may_read() (§3)
--   profiles.hidden_from_groups(§2b) -> privacy_settings() (§6)
--   group_members.share_with_group   -> shares_group_with() (§3)
--   group_may_read() (§3)            -> shares_group_with() (§3)
--
-- Note the token RLS policy is the second member of this class: it reads
-- g.universal and is safe only because §1 runs before §2. It would have failed
-- identically had those two sections been swapped.
--
-- `scratch/security/ordercheck.py` verifies all of this mechanically. Run it
-- after ANY edit to this file:
--
--     python scratch/security/ordercheck.py scratch/security/migrate-groups.sql
--
-- It is deliberately validated against the broken layout — it reports the
-- exact error Postgres gave — so a clean verdict from it means something.
alter table public.profiles
  add column if not exists share_with_groups boolean not null default true;
alter table public.profiles
  add column if not exists hidden_from_groups text[] not null default '{}';

-- On the MEMBERSHIP, not on the group: it is my choice about this roster, so
-- two people in one group can answer differently and neither sees the other's
-- answer. A column on `groups` would have been one shared setting for everyone.
alter table public.group_members
  add column if not exists share_with_group boolean not null default true;

-- AUDIT G10: `add column if not exists` SKIPS ENTIRELY if the column already
-- exists — including if a partial prior run or a hand-add left it NULLABLE.
-- That matters because group_may_read() fails OPEN on a null array
-- (`x = any(NULL)` is NULL, and the coalesce turns that into "visible"). The
-- shape is deliberately the same as FINAL-1's friend_may_read, so the fix is
-- to guarantee the precondition rather than to change the predicate.
update public.profiles set hidden_from_groups = '{}' where hidden_from_groups is null;
alter table public.profiles alter column hidden_from_groups set not null;
-- share_with_groups gets NO null-cleanup on purpose. If it somehow pre-existed
-- as nullable WITH nulls, this raises "contains null values" and rolls the
-- whole file back — which is the RIGHT outcome, not a bug to work around:
-- auto-filling true would preserve a fail-open state, and auto-filling false
-- would silently tighten somebody's privacy without their asking. If you ever
-- see that error, it means the column arrived from somewhere unexpected and a
-- human needs to decide which way those rows should go.
alter table public.profiles alter column share_with_groups  set not null;

-- §3 ------------------------------------------------------- the read scope --

-- CLU-388. Deliberately NOT friend_may_read(): that one requires MUTUAL
-- FRIENDSHIP, and group co-members frequently are not friends — a coworkers
-- group is the motivating case. Same switches, no friendship requirement.
--
-- All four global/per-list levels are required, so this stays correct even if
-- the UI ratchets that tie them together are bypassed or broken:
--   share_progress false      "hide from friends" — which per the table above
--                             hides from groups too
--   share_with_groups false   "hide from groups"
--   hidden_slugs              this list hidden from friends, so also from groups
--   hidden_from_groups        this list hidden from groups specifically
--
-- MISSING PROFILE ROW COALESCES TO TRUE, for the reason FINAL-1 gives: a user
-- can sit in a live membership with no profiles row, and answering false there
-- would blank people's tiles overnight while privacy_settings() reported the
-- opposite. Absent row means untouched settings, and untouched settings are
-- the defaults.
--
-- NOT GRANTED TO ANY BROWSER ROLE — see AUDIT F1 in the header. It is called
-- only from shares_group_with(), which is SECURITY DEFINER and therefore
-- resolves EXECUTE against the function owner.
create or replace function public.group_may_read(p_owner uuid, p_prop text)
returns boolean language sql security definer stable
set search_path = public, pg_temp as $$
  select coalesce((
    select p.share_progress
       and p.share_with_groups
       and not (split_part(p_prop, '#', 1) = any (p.hidden_slugs))
       and not (split_part(p_prop, '#', 1) = any (p.hidden_from_groups))
      from public.profiles p
     where p.user_id = p_owner), true);
$$;

-- Same signature, so every policy referring to it keeps working untouched.
create or replace function public.shares_group_with(other uuid, prop text)
returns boolean language sql security definer stable
set search_path = public, pg_temp as $$
  select exists (
    select 1
    from group_members a
    join group_members b using (group_id)
    join groups g on g.id = a.group_id
    where a.user_id = auth.uid()
      and b.user_id = other
      and (
        -- A WATCH CLUB, for its own property. Unconditional, and it must stay
        -- that way: "being in a club implies you want to share progress with
        -- club members" (CLU-388). No privacy switch may hide this. The
        -- `not g.universal` is redundant given §1's CHECK — universal rows
        -- have a null property_id, which never equals prop — but it is written
        -- out so the two branches read as mutually exclusive.
        (not g.universal and g.property_id = prop)

        -- A GROUP: every list except a gated one (CLU-185), only what the
        -- owner's own switches allow (CLU-388), and only if the owner has not
        -- muted this particular roster. `b` is the OWNER's membership row, so
        -- share_with_group is their choice about this group — two people in
        -- one group can answer differently and neither sees the other's answer.
        --
        -- AUDIT F2: split_part is applied HERE rather than relying on
        -- is_private_property to re-split internally. Correct under either
        -- installed body of that function; see the header.
        or (g.universal
            and not is_private_property(split_part(prop, '#', 1))
            and coalesce(b.share_with_group, true)
            and group_may_read(other, prop))
      )
  );
$$;

-- §4 ------------------------------------------------------------- the door --
-- ONE new door. join_group() IS NOT TOUCHED BY THIS FILE — see the header.
--
-- AUDIT (v1 F5): v1's token door had no rate limit. It reuses the existing
-- 'join' budget rather than inventing a kind, so one attacker cannot spend the
-- code budget and the token budget separately. Both doors lead to the same
-- place, so they share a cap.
create or replace function public.join_group_by_token(
  p_token text, p_display_name text
) returns groups language plpgsql security definer
set search_path = public, pg_temp as $$
declare
  g     groups;
  taken int;
  -- AUDIT F8: upper(), matching live join_group(). The alphabet excludes I and
  -- O so there is no case ambiguity, and a token lowercased by a mail client
  -- would otherwise fail the regex below and be charged a rate-limit miss.
  want  text := upper(btrim(coalesce(p_token, '')));
begin
  if auth.uid() is null then
    raise exception 'must be signed in to join a group';
  end if;

  -- before the lookup, so a blocked caller learns nothing about the token
  perform guard_group_join_rate();

  -- A token that cannot exist is still a guess; charge it.
  if want !~ '^[A-HJ-NP-Z2-9]{22}$' then
    perform rate_limit_note('join');
    return null;
  end if;

  select g2.* into g
    from groups g2
    join group_join_tokens t on t.group_id = g2.id
   where t.token = want and g2.universal;

  if not found then
    perform rate_limit_note('join');
    -- NOT `raise`, for the reason migrate-add-rate-limits.sql documents at
    -- length: raising rolls back the line above and the cap never fires.
    return null;
  end if;

  select count(*) into taken from group_members where group_id = g.id;

  insert into group_members (group_id, user_id, display_name, color_index)
  values (g.id, auth.uid(),
          coalesce(nullif(btrim(p_display_name), ''), 'Reader'), taken)
  on conflict (group_id, user_id)
    -- matches live join_group(): re-joining renames you, it does not no-op
    do update set display_name = excluded.display_name;

  return g;
end $$;

-- §5 ------------------------------------------------------------ creation --
-- A separate function rather than a branch inside create_group(), so the
-- watch-club creation path is not touched by this migration either.
create or replace function public.create_universal_group(
  p_name text, p_display_name text
) returns groups language plpgsql security definer
set search_path = public, pg_temp as $$
declare g groups;
begin
  if auth.uid() is null then
    raise exception 'must be signed in to create a group';
  end if;

  insert into groups (code, name, property_id, universal, created_by)
  values (
    null,                    -- no code: §1's CHECK requires it, and why
    coalesce(nullif(btrim(p_name), ''), 'My people'),
    null,
    true,
    auth.uid()
  )
  returning * into g;

  insert into group_join_tokens (group_id, token) values (g.id, new_join_token());

  insert into group_members (group_id, user_id, display_name, color_index)
  values (g.id, auth.uid(),
          coalesce(nullif(btrim(p_display_name), ''), 'Reader'), 0);

  return g;
end $$;

-- Rotating invalidates every link ever sent — the same promise the friend code
-- makes. Owner only, and it returns the new token because the owner is the one
-- person entitled to see it.
create or replace function public.rotate_join_token(p_group uuid)
returns text language plpgsql security definer
set search_path = public, pg_temp as $$
declare t text;
begin
  if auth.uid() is null then
    raise exception 'must be signed in';
  end if;
  if not exists (select 1 from groups
                 where id = p_group and created_by = auth.uid() and universal) then
    raise exception 'not your group';
  end if;
  t := new_join_token();
  insert into group_join_tokens (group_id, token) values (p_group, t)
    on conflict (group_id) do update set token = excluded.token,
                                         created_at = now();
  return t;
end $$;

-- The owner reads it back to draw the invite link. The RLS policy in §2 allows
-- exactly this, but going through a function keeps the front end from needing
-- a second table in its select.
create or replace function public.group_join_link(p_group uuid)
returns text language sql security definer stable
set search_path = public, pg_temp as $$
  select t.token from group_join_tokens t
    join groups g on g.id = t.group_id
   where t.group_id = p_group
     and g.created_by = auth.uid()
     and g.universal;
$$;

-- §6 ---------------------------------------------------- the group switches --
-- CLU-388. Three new controls, each narrower than the last, plus the ratchets.

-- The three columns themselves are added in §2b, ABOVE, not here. They have to
-- exist before §3 defines the predicates that read them — see the note there.
-- What remains in this section is everything that does NOT have to move: the
-- backfill and the setter functions.

-- BACKFILL — apply the ratchet retroactively.
--
-- Both columns above default to TRUE, which is right for a new account and
-- WRONG for someone who already chose to hide. A user who turned "hide from
-- friends" on last week never passed through the ratchet, because it did not
-- exist; they would sit at share_with_groups = true, and the day they turned
-- friends sharing back on they would be silently exposed to every group they
-- had joined. That is precisely the one-click widening the ratchet exists to
-- prevent, so the people who hid EARLIEST must not be the only ones it fails.
--
-- This is the one place this file writes existing rows. It only ever tightens
-- — no row becomes more visible — and it is idempotent: re-running finds
-- nothing left to change.
update public.profiles
   set share_with_groups = false, updated_at = now()
 where share_progress = false and share_with_groups;

update public.profiles
   set hidden_from_groups = (
         select array(select distinct unnest(hidden_from_groups || hidden_slugs))),
       updated_at = now()
 where coalesce(array_length(hidden_slugs, 1), 0) > 0
   and not (hidden_slugs <@ hidden_from_groups);

-- privacy_settings() gains two keys. Body otherwise IDENTICAL to FINAL-2's,
-- copied from the live file rather than reconstructed.
create or replace function public.privacy_settings()
returns json language sql security definer stable
set search_path = public, pg_temp as $$
  select json_build_object(
           'share_progress',     coalesce(p.share_progress, true),
           'share_activity',     coalesce(p.share_activity, true),
           'share_with_groups',  coalesce(p.share_with_groups, true),
           'hidden_slugs',       coalesce(p.hidden_slugs, '{}'::text[]),
           'hidden_from_groups', coalesce(p.hidden_from_groups, '{}'::text[]))
    from (select auth.uid() as uid) me
    left join public.profiles p on p.user_id = me.uid
   where me.uid is not null;
$$;

-- THE GLOBAL RATCHET (CLU-388): turning "hide from friends" ON also turns
-- "hide from groups" on. Turning it back OFF does NOT turn the other back on.
-- Enforced here and not only in the checkbox — see the header for why the
-- asymmetry is a safety property rather than a UI nicety.
--
-- The old two-argument set_privacy is DROPPED rather than left beside this
-- one: PostgREST resolves rpc() by name and would refuse an ambiguous
-- overload. Drop and create are in the same transaction and §7 re-grants.
drop function if exists public.set_privacy(boolean, boolean);

create or replace function public.set_privacy(
  p_share boolean default null,
  p_activity boolean default null,
  p_groups boolean default null
) returns json language plpgsql security definer
set search_path = public, pg_temp as $$
declare
  -- null means "leave alone", so the switches never overwrite each other. The
  -- ratchet is the one exception: an explicit false on p_share forces the
  -- group switch off regardless of what p_groups said.
  eff_groups boolean := case when p_share is false then false else p_groups end;
begin
  if auth.uid() is null then
    raise exception 'must be signed in to change privacy settings';
  end if;
  insert into public.profiles
         (user_id, share_progress, share_activity, share_with_groups, updated_at)
  values (auth.uid(), coalesce(p_share, true), coalesce(p_activity, true),
          coalesce(eff_groups, true), now())
  on conflict (user_id) do update
    set share_progress    = coalesce(p_share, profiles.share_progress),
        share_activity    = coalesce(p_activity, profiles.share_activity),
        share_with_groups = coalesce(eff_groups, profiles.share_with_groups),
        updated_at        = now();
  return public.privacy_settings();
end $$;

-- THE PER-LIST RATCHET. Same signature as FINAL-2's, so this is a genuine
-- create-or-replace and its grants survive. Body is FINAL-2's verbatim with
-- one addition: hiding a list from friends also hides it from groups, and
-- un-hiding does not reverse that.
--
-- THE `for update` IS LOAD-BEARING and is kept for the reason FINAL-2 gives:
-- without it, two devices hiding two different lists in the same instant leave
-- one of them UNHIDDEN — a privacy setting that silently did not apply.
create or replace function public.set_list_hidden(p_slug text, p_hidden boolean)
returns json language plpgsql security definer
set search_path = public, pg_temp as $$
declare cur text[]; curg text[];
begin
  if auth.uid() is null then
    raise exception 'must be signed in to change privacy settings';
  end if;
  if p_slug is null or p_slug !~ '^[A-Za-z][A-Za-z0-9_-]*$' then
    raise exception 'that is not a list';
  end if;

  insert into public.profiles (user_id, updated_at) values (auth.uid(), now())
    on conflict (user_id) do nothing;

  select hidden_slugs, hidden_from_groups into cur, curg from public.profiles
   where user_id = auth.uid()
     for update;
  if not found then
    raise exception 'no profile row to change';
  end if;

  if p_hidden then
    if coalesce(array_length(cur, 1), 0) >= 500 then
      raise exception 'too many hidden lists';
    end if;
    if not (p_slug = any (cur)) then cur := cur || p_slug; end if;
    -- the ratchet: hidden from friends implies hidden from groups
    if not (p_slug = any (curg)) then curg := curg || p_slug; end if;
  else
    cur := array_remove(cur, p_slug);
    -- and NOT reversed here. Coming out of hiding goes one step: the list
    -- becomes visible to friends again, and stays hidden from groups until
    -- the person says otherwise.
  end if;

  update public.profiles
     set hidden_slugs = cur, hidden_from_groups = curg, updated_at = now()
   where user_id = auth.uid();
  return public.privacy_settings();
end $$;

-- The group-only sibling. Never touches hidden_slugs, so hiding a list from
-- groups leaves friends exactly as they were.
create or replace function public.set_list_hidden_groups(p_slug text, p_hidden boolean)
returns json language plpgsql security definer
set search_path = public, pg_temp as $$
declare cur text[];
begin
  if auth.uid() is null then
    raise exception 'must be signed in to change privacy settings';
  end if;
  if p_slug is null or p_slug !~ '^[A-Za-z][A-Za-z0-9_-]*$' then
    raise exception 'that is not a list';
  end if;

  insert into public.profiles (user_id, updated_at) values (auth.uid(), now())
    on conflict (user_id) do nothing;

  select hidden_from_groups into cur from public.profiles
   where user_id = auth.uid()
     for update;
  if not found then
    raise exception 'no profile row to change';
  end if;

  if p_hidden then
    if coalesce(array_length(cur, 1), 0) >= 500 then
      raise exception 'too many hidden lists';
    end if;
    if not (p_slug = any (cur)) then cur := cur || p_slug; end if;
  else
    cur := array_remove(cur, p_slug);
  end if;

  update public.profiles set hidden_from_groups = cur, updated_at = now()
   where user_id = auth.uid();
  return public.privacy_settings();
end $$;

-- The per-group switch. Only ever writes the caller's OWN membership row.
create or replace function public.set_group_share(p_group uuid, p_share boolean)
returns boolean language plpgsql security definer
set search_path = public, pg_temp as $$
begin
  if auth.uid() is null then
    raise exception 'must be signed in';
  end if;
  update group_members set share_with_group = coalesce(p_share, true)
   where group_id = p_group and user_id = auth.uid();
  if not found then
    raise exception 'you are not in that group';
  end if;
  return coalesce(p_share, true);
end $$;

-- §7 --------------------------------------------------------------- grants --
-- Supabase's default privileges add anon AND authenticated on top of PUBLIC,
-- so all three come off explicitly before anything is granted back. This is
-- the pattern FINAL-2 §grants and migrate-add-rate-limits both use.

-- Plumbing. Not callable from a browser by anyone.
--
-- AUDIT F1: group_may_read is NOT granted to anon/authenticated. It is reached
-- only from shares_group_with(), a SECURITY DEFINER function, which resolves
-- EXECUTE against its owner. Granting it would publish a privacy oracle over
-- every user's hidden-list set. Do not "fix" this by adding a grant.
revoke all on function public.new_join_token()
  from public, anon, authenticated;
revoke all on function public.group_may_read(uuid, text)
  from public, anon, authenticated;

revoke all on function public.join_group_by_token(text, text)
  from public, anon, authenticated;
revoke all on function public.create_universal_group(text, text)
  from public, anon, authenticated;
revoke all on function public.rotate_join_token(uuid)
  from public, anon, authenticated;
revoke all on function public.group_join_link(uuid)
  from public, anon, authenticated;
revoke all on function public.privacy_settings()
  from public, anon, authenticated;
revoke all on function public.set_privacy(boolean, boolean, boolean)
  from public, anon, authenticated;
revoke all on function public.set_list_hidden(text, boolean)
  from public, anon, authenticated;
revoke all on function public.set_list_hidden_groups(text, boolean)
  from public, anon, authenticated;
revoke all on function public.set_group_share(uuid, boolean)
  from public, anon, authenticated;

grant execute on function public.join_group_by_token(text, text)       to authenticated;
grant execute on function public.create_universal_group(text, text)    to authenticated;
grant execute on function public.rotate_join_token(uuid)               to authenticated;
grant execute on function public.group_join_link(uuid)                 to authenticated;
grant execute on function public.privacy_settings()                    to authenticated;
grant execute on function public.set_privacy(boolean, boolean, boolean) to authenticated;
grant execute on function public.set_list_hidden(text, boolean)        to authenticated;
grant execute on function public.set_list_hidden_groups(text, boolean) to authenticated;
grant execute on function public.set_group_share(uuid, boolean)        to authenticated;

-- AUDIT F3: three-way on the TABLE too. Supabase's default privileges grant
-- authenticated full DML on new tables in public, and TRUNCATE IS NOT SUBJECT
-- TO RLS — it is gated on the privilege alone. Not reachable through PostgREST
-- today, but this is exactly the "a future 'disable RLS for a minute to debug'
-- cannot quietly expose it" hazard rate_events was written against.
revoke all on table public.group_join_tokens from public, anon, authenticated;
grant select on table public.group_join_tokens to authenticated;  -- RLS still applies

commit;

-- AUDIT G8: dropping and recreating set_privacy invalidates PostgREST's schema
-- cache. Supabase's pgrst_ddl_watch event trigger normally reloads within a
-- second, but there is a window in which the deployed savePrivacy() gets a
-- PGRST202 and the account page shows "write failed". Ask for the reload
-- explicitly rather than racing it.
notify pgrst, 'reload schema';

-- ===========================================================================
-- FRONT-END ORDERING — READ THIS BEFORE CREATING THE FIRST GROUP
-- ===========================================================================
-- AUDIT F6. renderMyClubs() in src/template.html selects every group the user
-- belongs to with NO property filter and unconditionally prints
-- titleOf(g.property_id) and g.code. Both are NULL on a universal row, and
-- esc() stringifies rather than throwing — so it renders a club row reading
-- "null … null … Copy … Open", with Open navigating to ?p=null.
--
-- This CANNOT fire when the SQL runs: no universal row can exist until
-- something calls create_universal_group(), and the deployed build never does.
-- It fires the instant anyone creates one, INCLUDING from the SQL editor.
--
-- So: deploy the renderMyClubs() guard that skips g.universal rows BEFORE
-- creating the first group. Running this migration on its own is safe.
--
-- ===========================================================================
-- ALSO RECORD (audit, non-blocking)
-- ===========================================================================
-- F5  FINAL-2-privacy.sql §2 is now SUPERSEDED and must NOT be re-run: it
--     would recreate set_privacy(boolean, boolean) as a second overload
--     (PostgREST then refuses every privacy toggle with PGRST203) and revert
--     privacy_settings() to the 3-key body. Banner that file and note it in
--     MIGRATION-AUDIT.md.
-- F9  If a universal group's owner ever uses the "leave group" policy on their
--     own group, the groups row becomes invisible to them and they lose table
--     access to their own token. group_join_link() still works, being definer.
--     Fails closed; recorded so it is not later diagnosed as a bug.
-- F10 shares_group_with() is referenced by ONE policy: "read group progress"
--     on public.progress. There is no group branch on thumbs or tick_events,
--     so group co-members will see each other's ticks but not their thumbs.
--     Product gap, not a leak — but "a roster you see on every list" reads
--     wider than what this ships.
-- F11 For anyone in a universal group, every candidate row in a select on
--     progress now costs an is_private_property() plus a group_may_read(),
--     neither inlinable. Watch it.
-- G4  set_list_hidden's 500 cap counts hidden_slugs only, while the ratchet
--     also appends to hidden_from_groups — so that array can reach ~1000 via
--     500 group-only hides plus 500 friend hides. Storage padding, no privacy
--     consequence.
-- G5  The backfill is idempotent EXCEPT if someone group-un-hides a list that
--     is still in hidden_slugs; a later re-run re-adds it. Tightening only,
--     and a no-op at read time because group_may_read consults both arrays.
-- G6  `hidden_slugs <@ hidden_from_groups` is false whenever a NULL element is
--     involved, so such a row would be rewritten every run — updated_at churn,
--     never a visibility change. Unreachable through the RPCs.
-- G7  The ratchet is enforced in the RPC path and at READ time, but not at the
--     table: authenticated keeps UPDATE on its OWN profiles row, so a client
--     can PATCH share_with_groups=true directly. Self-affecting only, and
--     anything hidden via share_progress/hidden_slugs still blocks at read.
--     Worth knowing that the header's "server-side" claim means "in the RPC
--     and at read", not "on the table".
-- G9  service_role is not revoked on group_may_read. Not browser-reachable —
--     only the anon key ships in index.html — and service_role can read
--     profiles directly anyway. Consistent with every other revoke here.
--
-- ===========================================================================
-- READBACK — run separately, and check each line rather than trusting a
-- "Success. No rows returned."
-- ===========================================================================
-- 1. select column_name, is_nullable from information_schema.columns
--     where table_name='groups' and column_name in ('universal','property_id','code');
--       -> universal NO | property_id YES | code YES
--
-- 2. select conname from pg_constraint
--     where conrelid='public.groups'::regclass and conname='groups_scope_ck';   -> 1 row
--
-- 3. select count(*) from groups where property_id is null or code is null;     -> 0
--    select count(*) from groups where universal;                               -> 0
--
-- 4. join_group() STILL HAS ITS RATE LIMITING — the v1 regression, checked:
--    select prosrc like '%guard_group_join_rate%' as limited,
--           prosrc like '%rate_limit_note%'       as counted
--      from pg_proc where proname='join_group';                       -> true, true
--
-- 5. the read scope obeys both rulings AND splits the rewatch suffix:
--    select prosrc like '%split_part%'       as splits,
--           prosrc like '%group_may_read%'   as switches_apply,
--           prosrc like '%share_with_group%' as per_group
--      from pg_proc where proname='shares_group_with';           -> true, true, true
--
-- 6. group_may_read is NOT executable by the browser roles (AUDIT F1):
--    select has_function_privilege('anon','public.group_may_read(uuid,text)','execute'),
--           has_function_privilege('authenticated','public.group_may_read(uuid,text)','execute');
--                                                                   -> false, false
--    ...and reads still work: select count(*) from progress;         -> no error
--
-- 6b. THE TRIGGER IS ACTUALLY ATTACHED (audit G1) — the check whose absence
--     would have let §1b be silently decorative:
--     select count(*) from pg_trigger
--      where tgrelid='public.groups'::regclass
--        and tgname='groups_update_guard' and not tgisinternal;          -> 1
--     select prosrc like '%cannot change kind%' as guards_universal
--       from pg_proc where proname='groups_guard_update';                -> true
--
-- 7. pg_temp on everything this file wrote:
--    select proname from pg_proc
--     where proname in ('new_join_token','group_may_read','shares_group_with',
--                       'join_group_by_token','create_universal_group',
--                       'rotate_join_token','group_join_link','privacy_settings',
--                       'set_privacy','set_list_hidden','set_list_hidden_groups',
--                       'set_group_share','groups_guard_update')
--       and not (proconfig::text like '%pg_temp%');                  -> 0 rows
--
-- 8. exactly one set_privacy:
--    select count(*) from pg_proc where proname='set_privacy';       -> 1
--
-- 9. the ratchets, on a throwaway account:
--    select set_privacy(p_share => false);  -> share_with_groups false
--    select set_privacy(p_share => true);   -> share_with_groups STAYS false
--    select set_list_hidden('dune', true);  -> slug in BOTH arrays
--    select set_list_hidden('dune', false); -> gone from hidden_slugs,
--                                              STILL in hidden_from_groups
-- ===========================================================================
