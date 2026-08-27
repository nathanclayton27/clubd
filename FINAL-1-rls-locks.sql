-- clubd — FINAL-1: finish the locks, and set the one friends-read rule
-- (CLU-34, CLU-43, CLU-118)
--
-- Run in the Supabase SQL editor. One transaction. Idempotent: re-running it
-- lands exactly the same rules and touches no row it has already written.
--
-- ===========================================================================
-- RUN ORDER — READ THIS FIRST
-- ===========================================================================
--
--   FINAL-1-rls-locks.sql   <- YOU ARE HERE. Run it FIRST. No front-end
--                              prerequisite. Nothing needs to deploy before
--                              or after it.
--   FINAL-2-privacy.sql        second. No front-end prerequisite either — the
--                              privacy UI is ALREADY deployed and hides its
--                              own controls until FINAL-2's RPCs answer.
--   FINAL-3-profiles.sql       LAST, and FENCED: it must not run until
--                              friendByCode() in src/template.html stops
--                              querying `profiles` directly. As of the
--                              deployed index.html it still does. See that
--                              file's header.
--
-- FRONT-END CHANGE REQUIRED BEFORE THIS FILE: none.
--
-- ===========================================================================
-- WHAT IS ALREADY IN FORCE — this file is a correction, not the main event
-- ===========================================================================
--
-- scratch/security/rls-fix-PART1-safe-now.sql HAS ALREADY BEEN RUN against
-- production. Confirmed from pg_policies, not inferred:
--
--   progress | mutual friends read progress | SELECT |
--     ((NOT is_private_property(property_id))
--      AND EXISTS (SELECT 1 FROM friendships f1
--                   WHERE f1.a = auth.uid() AND f1.b = progress.user_id)
--      AND EXISTS (SELECT 1 FROM friendships f2
--                   WHERE f2.a = progress.user_id AND f2.b = auth.uid()))
--
-- So the following are DONE and this file does not repeat them: the two
-- BEFORE UPDATE guard triggers on group_members and groups; the anon
-- INSERT/UPDATE/DELETE revokes on the six tables and on thumbs; the
-- private_properties table; the pg_temp search_path sweep over
-- is_group_member / is_group_owner / shares_group_with.
--
-- Three things PART 1 shipped WITHOUT, all of them live gaps right now:
--
--   A. private_properties is EMPTY, so `NOT is_private_property(...)` is
--      currently a no-op and a password-gated list's progress is still
--      readable by every mutual friend. §3 below fixes that.
--
--   B. The policy compares the RAW property_id. A fresh watch (CLU-46) stores
--      its parallel run under `<slug>#fw` — a real progress row with a real
--      property_id — so even once the slug is registered, the rewatch row
--      stays wide open. §6 fixes that with split_part.
--
--   C. is_private_property is executable only through the implicit PUBLIC
--      grant that PART 1's own §3 calls a hazard. A policy is evaluated with
--      the privileges of the querying role, so the day anyone runs
--      `alter default privileges ... revoke execute on functions from public`
--      every select on progress and thumbs starts failing for everybody.
--      §2 makes the grant explicit.
--
-- ===========================================================================
-- THE ONE MERGED POLICY — the point of this file
-- ===========================================================================
--
-- Two pending migrations both dropped and recreated
-- "mutual friends read progress", and neither carried the other's protection:
--
--   PART 1 (now live)          gated-list scoping, no privacy switch
--   migrate-add-friend-privacy gated-list scoping ABSENT, privacy switch
--
-- Whichever ran second would have silently deleted the first one's work. On
-- this database PART 1 is the one in force, so running the privacy migration
-- as written would re-open the gated-list leak on a database where it is
-- about to be closed — no error, no warning, and PART 1's own verification
-- query would still pass.
--
-- The resolution is one policy carrying both halves, defined ONCE, HERE:
--
--     not is_private_property(split_part(property_id, '#', 1))
--     and friend_may_read(user_id, property_id)
--
-- and, so that this file can define it, the privacy columns and
-- friend_may_read() move here too, out of migrate-add-friend-privacy.sql.
-- That is not tidiness. It is the only arrangement in which EVERY object has
-- exactly ONE definition in exactly ONE file, which is what makes these three
-- files re-runnable in any order without any of them weakening another. If
-- the policy were defined in two files, re-running the earlier one after the
-- later one would be a silent downgrade — the exact failure this file exists
-- to prevent, wearing a different hat.
--
-- DO NOT RUN migrate-add-friend-privacy.sql (repo root). Its columns, its
-- function and its policy are all superseded here and in FINAL-2. Running it
-- at any point after this file replaces the merged policy with its own
-- half-blind version.
--
-- ===========================================================================
-- WHAT CHANGES FOR A USER TODAY: nothing, except the gated list closing
-- ===========================================================================
--
-- The three new columns arrive carrying today's behaviour exactly —
-- share_progress true, share_activity true, hidden_slugs empty — so every
-- friend sees on the morning after precisely what they saw the night before.
-- The privacy CONTROLS stay invisible until FINAL-2 creates the RPCs they are
-- gated on, which is the correct shape: no switch is ever drawn before the
-- database honours it.
--
-- The one visible change is the intended one: progress and thumbs on the
-- password-gated list stop reaching mutual friends, including its `#fw`
-- rewatch rows. Club members are untouched — "read group progress" is a
-- separate PERMISSIVE policy, ORed with this one, and nothing here names it.
--
-- ===========================================================================
-- KNOWN CONSEQUENCE OF PART 1 §4, recorded because it is not written down
-- anywhere else
-- ===========================================================================
--
-- anon lost INSERT/UPDATE/DELETE on the six tables. A write issued while the
-- JS `user` object is set but the JWT has lapsed goes out on the anon key: it
-- used to hit RLS and return "0 rows, no error", and now returns 42501
-- permission denied. Three call sites in the deployed template latch a
-- permanent kill-switch on their FIRST error — THBROKEN, evBroken, FBROKEN —
-- so one such write silently disables thumbs sync, tick-event flushing or the
-- whole Friends section for the rest of that page's life. Narrow window,
-- self-healing on reload. Worth a front-end ticket: do not latch on 42501.

-- The explicit transaction is not decoration: every statement below is
-- transactional DDL, and unwrapped, the drop/create pairs in §6 each have a
-- window in which the drop has landed and the create has not — friends'
-- shelves go blank, fail-closed but a real outage. The Supabase SQL editor
-- usually sends a pasted script as one implicit transaction, but that is a
-- property of how the statements are transmitted, not a guarantee, and it
-- does not hold if this file is run in chunks. If the editor answers
-- "there is already a transaction in progress", that warning is harmless.
-- Run the file whole, top to bottom, in one paste.
begin;

-- ------------------------------------------- 1. revokes that actually revoke --

-- PART 1 §3 revoked `from public, anon` and granted back to authenticated,
-- which is right. This restates it with authenticated in the revoke list too,
-- so any stray non-EXECUTE privilege comes off as well and every function in
-- this project ends up described by the same three-way pattern. Idempotent,
-- and the grant immediately below each revoke restores what the site needs.
--
-- Not exhaustive by design: service_role holds these directly through
-- Supabase's default privileges and is not stripped here. It is already
-- omnipotent, so removing it would be theatre.

revoke all on function create_group(text, date, text, text)
  from public, anon, authenticated;
grant execute on function create_group(text, date, text, text) to authenticated;

revoke all on function join_group(text, text)
  from public, anon, authenticated;
grant execute on function join_group(text, text) to authenticated;

revoke all on function join_or_create_group(text, text, text, text)
  from public, anon, authenticated;
grant execute on function join_or_create_group(text, text, text, text) to authenticated;

-- called only from inside create_group(), which is definer-owned and runs as
-- the owner; no browser role needs it
revoke all on function new_group_code() from public, anon, authenticated;

-- ------------------------------ 2. the gate oracle, and the grant it needs --

-- Same signature and same volatility as the definition PART 1 installed, so
-- this is a genuine CREATE OR REPLACE — no drift, no new overload.
--
-- One change to the body: it now also matches on the base slug. The two
-- policies below already strip the suffix before calling, so this is belt and
-- braces — it exists so that a future call site which forgets split_part
-- fails closed instead of leaking. A gated slug registered in either form
-- covers both forms.
--
-- Answers a fact about a slug, not about a person, and the public property
-- manifest already says which lists are gated. Deliberately does not look at
-- auth.uid().
create or replace function is_private_property(prop text)
returns boolean language sql security definer stable
set search_path = public, pg_temp as $$
  select exists (
    select 1 from private_properties
     where property_id = prop
        or property_id = split_part(prop, '#', 1)
  );
$$;

-- RLS policy expressions run with the privileges of the role running the
-- query, so both browser roles need EXECUTE — anon included, because a
-- signed-out read must come back empty rather than error. PART 1 argued this
-- for the three group helpers and then left this one leaning on the implicit
-- PUBLIC grant it had just called a hazard.
grant execute on function is_private_property(text) to anon, authenticated;

-- ------------------------------- 3. the step without which §6 protects nothing --

-- private_properties starts empty, which makes the gated-list term a no-op.
-- One row per property carrying a `secret:` block in the manifest. There is
-- exactly ONE today — `secret`, served at ?p=secret, which is also its
-- filename in properties/ and its slug in the baked manifest, so naming it
-- here reveals nothing that clubd.watch does not already serve. The list's
-- real title, its password and its group code stay out of this repository,
-- as they must.
--
-- (The audit said two properties carry a `secret:` block. It is one: the
-- second hit was the same property's entry in properties/index.json.)
--
-- With split_part in §6 and in is_private_property above, the `#fw` form does
-- not need its own row. Adding one anyway would be harmless.
insert into private_properties (property_id) values ('secret')
  on conflict do nothing;

-- ------------------------------------------- 4. the privacy columns (CLU-118) --

-- Moved here from migrate-add-friend-privacy.sql. friend_may_read() cannot
-- compile without them, and the merged policy cannot exist without
-- friend_may_read() — so if the policy is to have exactly one definition, in
-- the first file to run, these have to be in the first file too.
--
-- On PG 11+ a non-volatile default is a catalog-only change: no table
-- rewrite, a brief ACCESS EXCLUSIVE lock held to commit, trivial at this
-- size. The defaults reproduce today's behaviour for every existing row, so
-- no live row can be rejected and nobody's experience changes.
--
--   share_progress  the master switch. Off, your shelves render nowhere on
--                   any friend's friends page. The friendship survives.
--   hidden_slugs    per list. Hidden here, that one list is gone from every
--                   friend's view and the rest stay.
--   share_activity  consent banked ahead of the feature. NOTHING READS THIS
--                   COLUMN YET — no policy or function below touches it.
--                   CLU-70 MUST GATE ON share_progress AND share_activity
--                   TOGETHER: a person who turned progress off has said no to
--                   the louder thing already.
--
--                   Its default is TRUE, and this is the one judgement call
--                   in these three files. TRUE means the activity feed has
--                   something in it the day it ships and that anyone who
--                   wanted out could have opted out weeks earlier. FALSE
--                   means it launches empty and fills as people find the
--                   switch. IF YOU WANT FALSE, CHANGE THE WORD BELOW BEFORE
--                   RUNNING THIS FILE — afterwards it is an UPDATE across
--                   every live row, and a different conversation. It is
--                   declared HERE and nowhere else, so there is one word to
--                   change and no second copy to drift from it.

alter table public.profiles
  add column if not exists share_progress boolean not null default true,
  add column if not exists share_activity boolean not null default true,
  add column if not exists hidden_slugs   text[]  not null default '{}';

-- --------------------------------------------- 5. the gatekeeper function --

-- The CLU-72 mutual-friendship condition with the owner's own answer bolted
-- onto the end. SECURITY DEFINER because the policy has to read
-- share_progress and hidden_slugs, and FINAL-2 takes column SELECT on
-- profiles away from the browser roles; the definer runs as the table owner,
-- which can.
--
-- The mutual-friendship test stays INSIDE the function rather than beside it
-- in the policy, so the function is safe to leave callable: asked about a
-- stranger it answers false, which is what the policy would have said.
--
-- split_part on '#' is not decoration. A fresh watch stores its parallel run
-- under `<slug>#fw`, and hiding a list has to hide its rewatch too —
-- otherwise the one list somebody most wanted covered is the one still being
-- served.
--
-- THE RESIDUAL, stated honestly rather than argued away. The root migration's
-- header claimed this function is "no kind of oracle" because it only tells
-- you what the policy would tell you anyway. That is not quite true. The
-- policy's answer is entangled with whether a row exists, so through the
-- policy a mutual friend cannot tell "never tracked that list" from "hid that
-- list". A direct call separates them cleanly and can be swept across all 126
-- slugs in one round trip. It CANNOT simply be revoked: policy expressions
-- run as the querying role, so authenticated needs EXECUTE. The exposure is
-- bounded — it answers false for anyone who is not already your mutual
-- friend, so what leaks is "which lists you hid" to people you have already
-- accepted, not to the world. Accepted deliberately; do not let a future
-- reader think it was overlooked.
--
-- MISSING PROFILE ROW: coalesce(..., TRUE), not false. A user can sit in a
-- live mutual friendship with no profiles row — addFriend() inserts an edge
-- without needing the target's row, and mirrorProfile() latches FBROKEN
-- permanently on its first error. Answering false there would blank those
-- users' shelves overnight, and worse, would disagree with
-- privacy_settings() in FINAL-2, which coalesces a missing row to
-- share_progress TRUE. A control that reads "on" while the database enforces
-- "off" is exactly the class of lie these files exist to prevent. Absent row
-- means "settings never touched", and untouched settings are the defaults.
create or replace function public.friend_may_read(p_owner uuid, p_prop text)
returns boolean language sql security definer stable
set search_path = public, pg_temp as $$
  select
    exists (select 1 from public.friendships f1
            where f1.a = auth.uid() and f1.b = p_owner)
    and
    exists (select 1 from public.friendships f2
            where f2.a = p_owner and f2.b = auth.uid())
    and
    coalesce((select p.share_progress
                     and not (split_part(p_prop, '#', 1) = any (p.hidden_slugs))
                from public.profiles p
               where p.user_id = p_owner), true);
$$;

-- Same reason as is_private_property: the policies below are evaluated as the
-- querying role.
grant execute on function public.friend_may_read(uuid, text) to anon, authenticated;

-- ===========================================================================
-- 6. THE MERGED POLICIES — THE SINGLE DEFINITION. DO NOT COPY THEM ANYWHERE.
-- ===========================================================================
--
-- These two statements are the ONLY place in this project where
-- "mutual friends read progress" and "mutual friends read thumbs" are
-- defined. FINAL-2 and FINAL-3 do not touch them; FINAL-2 verifies them and
-- refuses to commit if either has been replaced by a narrower or blinder
-- version.
--
-- IF YOU EVER NEED TO CHANGE ONE OF THESE RULES, CHANGE IT HERE AND RE-RUN
-- THIS FILE. Do not paste a policy into another migration. Every copy is a
-- future silent clobber: the last file to run wins, no error is raised, and
-- whichever protection the loser carried disappears without a trace. That has
-- already nearly happened once on this database.
--
-- Each drop is paired with its create inside this transaction, so there is no
-- window in which progress or thumbs is readable under no friends policy at
-- all — and if the create fails, the drop rolls back with it.
--
-- Both halves, and what each one is for:
--   not is_private_property(split_part(...))  a password-gated list's rows do
--                                             not reach friends, rewatch rows
--                                             included (CLU-34/CLU-43)
--   friend_may_read(...)                      mutual friendship AND the row
--                                             owner's own switches (CLU-118)

drop policy if exists "mutual friends read progress" on public.progress;
create policy "mutual friends read progress" on public.progress
  for select using (
    not public.is_private_property(split_part(progress.property_id, '#', 1))
    and public.friend_may_read(progress.user_id, progress.property_id)
  );

-- thumbs carries the same leak and the same fix. migrate-add-thumbs.sql
-- copied the CLU-72 shape deliberately and inherited its missing property
-- scope; PART 1 §5b added the gated-list term; this adds the owner's
-- switches, which the root privacy migration never did. Without it, hiding a
-- list still leaves your NAMED up/down pills on it visible to every mutual
-- friend, rendered on the list page by pullFriendThumbs() — somebody who
-- hides a list and then finds their own name on a friend's thumb pill for it
-- has been lied to by a control the site drew for them.
--
-- pushThumb() writes SLUG and never CKEY, so thumbs.property_id carries no
-- '#fw' suffix today. split_part is applied anyway, for the same reason it is
-- inside is_private_property: the cost is nothing and the assumption is not
-- enforced anywhere.
--
-- Guarded on the table existing so this file runs against a database where
-- migrate-add-thumbs.sql has not gone in. It has gone in here.
do $$ begin
  if to_regclass('public.thumbs') is null then
    raise warning 'thumbs does not exist — re-run this file after migrate-add-thumbs.sql';
    return;
  end if;

  drop policy if exists "mutual friends read thumbs" on public.thumbs;
  create policy "mutual friends read thumbs" on public.thumbs
    for select using (
      not public.is_private_property(split_part(thumbs.property_id, '#', 1))
      and public.friend_may_read(thumbs.user_id, thumbs.property_id)
    );
end $$;

-- ------------------------------------- 7. refuse to commit a half-landed rule --

-- The failure this guards against is the silent one: a policy that exists,
-- that no query errors on, and that is missing half of what it should be
-- checking. If either policy in force is not the merged version, this raises
-- and the whole transaction rolls back — nothing above is applied and the
-- database keeps the rules it had.
do $$
declare q text;
begin
  select pg_get_expr(pol.polqual, pol.polrelid) into q
    from pg_policy pol
    join pg_class c     on c.oid = pol.polrelid
    join pg_namespace n on n.oid = c.relnamespace
   where n.nspname = 'public' and c.relname = 'progress'
     and pol.polname = 'mutual friends read progress';

  if q is null then
    raise exception '"mutual friends read progress" is not on public.progress';
  end if;
  if q not like '%is_private_property%' or q not like '%friend_may_read%'
     or q not like '%split_part%' then
    raise exception 'progress policy is not the merged version: %', q;
  end if;

  if to_regclass('public.thumbs') is not null then
    select pg_get_expr(pol.polqual, pol.polrelid) into q
      from pg_policy pol
      join pg_class c     on c.oid = pol.polrelid
      join pg_namespace n on n.oid = c.relnamespace
     where n.nspname = 'public' and c.relname = 'thumbs'
       and pol.polname = 'mutual friends read thumbs';

    if q is null then
      raise exception '"mutual friends read thumbs" is not on public.thumbs';
    end if;
    if q not like '%is_private_property%' or q not like '%friend_may_read%' then
      raise exception 'thumbs policy is not the merged version: %', q;
    end if;
  end if;

  if not exists (select 1 from public.private_properties) then
    raise warning 'private_properties is EMPTY — the gated-list half of both policies is protecting nothing';
  end if;
end $$;

commit;

-- ===========================================================================
-- Check it worked — none of this changes anything
-- ===========================================================================
--
--   -- the merged rule, both tables. Each qual must contain BOTH
--   -- is_private_property and friend_may_read.
--   select tablename, policyname, qual from pg_policies
--    where policyname in ('mutual friends read progress',
--                         'mutual friends read thumbs');
--
--   -- exactly one definition of each, which is the whole point
--   select policyname, count(*) from pg_policies
--    where policyname like 'mutual friends read%'
--    group by 1;                                  -- one row each, count 1
--
--   select property_id from private_properties;   -- 'secret'
--
--   -- the browser roles can call what the policies call
--   select proname, proacl from pg_proc
--    where proname in ('is_private_property', 'friend_may_read');
--        -- both lists include anon=X and authenticated=X
--
--   select column_name, column_default, is_nullable
--     from information_schema.columns
--    where table_schema = 'public' and table_name = 'profiles'
--      and column_name in ('share_progress','share_activity','hidden_slugs');
--                                                  -- three rows, all NOT NULL
--
-- PROVING THE GATED LIST IS CLOSED. Impersonate a mutual friend and ask for
-- the row directly; if RLS is doing the work it comes back empty. This
-- changes nothing — it rolls back.
--
--   begin;
--     set local role authenticated;
--     set local request.jwt.claims = '{"sub":"<friend-uuid>","role":"authenticated"}';
--     select property_id from public.progress where user_id = '<owner-uuid>';
--   rollback;
--
-- The gated slug and its `#fw` twin must be absent from that result, and
-- every other list the two of them share must still be present. If a club
-- connects the same two people on the gated list, the row still comes back
-- through "read group progress" — that is correct, not a leak. Joining a club
-- with a shared code is its own act of consent; hiding from friends is not a
-- retraction of it. Leaving the club is.
-- ===========================================================================
