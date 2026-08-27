-- ###########################################################################
-- ##  DO NOT RE-RUN THIS FILE AS IT STANDS.  APPLIED, THEN SUPERSEDED.     ##
-- ###########################################################################
--
-- This file ran and is in force. But §2 of it — privacy_settings() and
-- set_privacy() — was SUPERSEDED on 2026-08-26 by migrate-groups.sql (CLU-387,
-- verified 19/19 in production). Re-running this file now would do two silent
-- pieces of damage:
--
--   1. It recreates `set_privacy(boolean, boolean)`. migrate-groups.sql
--      dropped that signature and created a THREE-argument version. Both would
--      then exist, and PostgREST cannot choose between overloads for
--      rpc('set_privacy', …) — it returns PGRST203 and EVERY PRIVACY TOGGLE ON
--      THE SITE STOPS WORKING. Worse, if it ever did resolve to the 2-arg one,
--      the CLU-388 ratchet would be bypassed entirely.
--
--   2. It reverts privacy_settings() to the three-key body, dropping
--      share_with_groups and hidden_from_groups from the JSON the account page
--      reads — so two live privacy controls would silently report nothing.
--
-- This is the hazard FINAL-1 §6 warns about in general terms ("every copy is a
-- future silent clobber: the last file to run wins, no error is raised"), now
-- concrete for this file.
--
-- IF YOU NEED §2's BEHAVIOUR, EDIT AND RE-RUN migrate-groups.sql §6 INSTEAD.
-- Sections 1 and 3 of this file (the profiles column locks and the three-way
-- revokes) are NOT superseded and remain the definition for what they cover.
--
-- ###########################################################################

-- clubd — FINAL-2: the privacy switches (CLU-118)
--
-- Run in the Supabase SQL editor, AFTER FINAL-1-rls-locks.sql. One
-- transaction. Idempotent, additive, destroys nothing.
--
-- ===========================================================================
-- RUN ORDER — READ THIS FIRST
-- ===========================================================================
--
--   FINAL-1-rls-locks.sql   MUST have run. This file refuses to commit if it
--                           has not: it checks, before anything else, that
--                           the merged friends-read policies are in force and
--                           that the privacy columns exist.
--   FINAL-2-privacy.sql     <- YOU ARE HERE. Second.
--   FINAL-3-profiles.sql    LAST, and fenced on a front-end change that has
--                           NOT shipped. See its header.
--
-- FRONT-END CHANGE REQUIRED BEFORE THIS FILE: none. The privacy UI is
-- ALREADY DEPLOYED (HEAD a45784f, in index.html) and is sitting in the safe
-- half of its own ordering rule: the account page asks the database for its
-- settings through privacy_settings(), that function does not exist yet, the
-- call errors, PRIVOFF latches, and every privacy control stays HIDDEN — not
-- greyed out, not present-and-broken, absent. Nothing on the page can imply a
-- privacy the database is not enforcing.
--
-- The consequence, stated plainly: the feature is NOT shipped until this file
-- runs. The controls are invisible, so a user who has heard that clubd has
-- privacy settings cannot find them. That is the correct failure, but it is
-- still a promise outstanding.
--
-- ===========================================================================
-- DO NOT RUN migrate-add-friend-privacy.sql
-- ===========================================================================
--
-- The file at the repo ROOT named migrate-add-friend-privacy.sql is
-- SUPERSEDED by FINAL-1 and this file, and must not be run at any point, in
-- any order, ever. It drops and recreates "mutual friends read progress" with
-- a version that has no gated-list term. On this database that term is LIVE —
-- rls-fix-PART1-safe-now.sql has already been run against production — so
-- running the root migration would silently re-open a password-gated list's
-- progress to every mutual friend. No error. No warning. Its own verification
-- block would still pass.
--
-- Its three columns are declared in FINAL-1 instead; its friend_may_read() is
-- defined in FINAL-1 instead; its policy is merged into FINAL-1's. This file
-- carries only what it had left: the RPCs and the profiles column grant.
--
-- ===========================================================================
-- THIS FILE DEFINES NO POLICY, ON PURPOSE
-- ===========================================================================
--
-- "mutual friends read progress" and "mutual friends read thumbs" have
-- exactly one definition each, in FINAL-1-rls-locks.sql, and this file does
-- not drop, alter or recreate either of them. That is deliberate and it is
-- the fix for the single most dangerous thing in the audit. A policy defined
-- in two migrations is a silent clobber waiting for whichever file runs
-- second — the loser's protection vanishes with no error raised anywhere.
--
-- For reference, the rule this file is written against and depends on. DO NOT
-- PASTE IT INTO A MIGRATION; it lives in FINAL-1:
--
--     create policy "mutual friends read progress" on public.progress
--       for select using (
--         not public.is_private_property(split_part(progress.property_id, '#', 1))
--         and public.friend_may_read(progress.user_id, progress.property_id)
--       );
--
-- IF THE CHECK AT THE TOP OF THIS FILE FIRES, THE ANSWER IS TO RE-RUN
-- FINAL-1, not to paste a policy here. Every copy of a policy is a future
-- outage or a future leak.
--
-- ===========================================================================
-- WHAT THIS FILE ADDS
-- ===========================================================================
--
-- 1. The profiles table stops being readable column-by-column by everyone.
--    profiles has to stay broadly readable — a typed friend code has to find
--    its owner (CLU-69) — but left alone that would make hidden_slugs public:
--    any signed-in stranger could read the exact list of lists you were
--    embarrassed enough to hide. A privacy feature that publishes the privacy
--    settings is not one. SELECT is narrowed to the four columns the
--    handshake actually needs.
--
--    Note for whoever adds the NEXT column to profiles: it will not be
--    readable until you add it to the grant below. That is the point, but it
--    is the kind of point that costs an hour if nobody wrote it down.
--
--    Tables get no default PUBLIC grant in Postgres, so unlike the function
--    case, revoking from the two roles here really is sufficient.
--
-- 2. Three RPCs, because the table will no longer answer for the three new
--    columns: read your own settings, set the two switches, hide or unhide
--    one list. They are also how the front end knows whether this file has
--    run at all — no function, no controls.
--
-- ===========================================================================
-- WHAT IS DELIBERATELY NOT TOUCHED: CLUBS
-- ===========================================================================
--
-- Joining a club with a shared code is its own act of consent. You handed
-- somebody six characters; hiding a list from friends is not a retraction of
-- that. Multiple PERMISSIVE policies on the same table and command are
-- combined with OR, so narrowing the friends policy cannot narrow the club
-- path — "read group progress" is a different OR branch and nothing in these
-- three files names it. A friend who is ALSO in a club with you, on that same
-- list, still sees your progress there. Hiding a list from friends is not a
-- way to hide from a club. Leaving the club is.

-- One transaction, so a half-applied file cannot leave the table in a state
-- nobody designed: either the narrowed grant and all three RPCs land together
-- or none of them do. Run it whole, in one paste. If the SQL editor answers
-- "there is already a transaction in progress", that warning is harmless.
begin;

-- ===========================================================================
-- 0. REFUSE TO RUN ON A DATABASE FINAL-1 HAS NOT PREPARED
-- ===========================================================================
--
-- Everything below assumes FINAL-1's columns, FINAL-1's friend_may_read() and
-- FINAL-1's merged policies. Rather than fail halfway through with a column
-- error, or — far worse — succeed while the policy in force is a blinder
-- version somebody pasted in by hand, check first and roll the whole thing
-- back.

do $$
declare q text;
begin
  if to_regprocedure('public.friend_may_read(uuid, text)') is null then
    raise exception 'FINAL-1 has not run: public.friend_may_read(uuid, text) does not exist. Run FINAL-1-rls-locks.sql first.';
  end if;
  if to_regprocedure('public.is_private_property(text)') is null then
    raise exception 'public.is_private_property(text) does not exist. Run FINAL-1-rls-locks.sql first.';
  end if;

  if not exists (
    select 1 from information_schema.columns
     where table_schema = 'public' and table_name = 'profiles'
       and column_name in ('share_progress','share_activity','hidden_slugs')
     group by table_name having count(*) = 3
  ) then
    raise exception 'public.profiles is missing the privacy columns. Run FINAL-1-rls-locks.sql first.';
  end if;

  select pg_get_expr(pol.polqual, pol.polrelid) into q
    from pg_policy pol
    join pg_class c     on c.oid = pol.polrelid
    join pg_namespace n on n.oid = c.relnamespace
   where n.nspname = 'public' and c.relname = 'progress'
     and pol.polname = 'mutual friends read progress';

  if q is null then
    raise exception '"mutual friends read progress" is missing from public.progress. Re-run FINAL-1-rls-locks.sql.';
  end if;
  if q not like '%is_private_property%' or q not like '%friend_may_read%' then
    raise exception 'the policy in force is NOT the merged one — re-run FINAL-1-rls-locks.sql, do not patch it here. In force: %', q;
  end if;

  if to_regclass('public.thumbs') is not null then
    select pg_get_expr(pol.polqual, pol.polrelid) into q
      from pg_policy pol
      join pg_class c     on c.oid = pol.polrelid
      join pg_namespace n on n.oid = c.relnamespace
     where n.nspname = 'public' and c.relname = 'thumbs'
       and pol.polname = 'mutual friends read thumbs';

    if q is null or q not like '%is_private_property%' or q not like '%friend_may_read%' then
      raise exception 'the thumbs policy is missing or not the merged one — re-run FINAL-1-rls-locks.sql. In force: %', coalesce(q, '<none>');
    end if;
  end if;

  if not exists (select 1 from public.private_properties) then
    raise warning 'private_properties is EMPTY — the gated-list half of both policies is protecting nothing. See FINAL-1 §3.';
  end if;
end $$;

-- ------------------------------------------------ 1. narrow the profiles read --

-- The handshake needs a code, a name and an owner. It has never needed more,
-- and the three privacy columns are nobody's business but their owner's.
--
-- Verified against the DEPLOYED index.html, not only src/template.html: the
-- only three profiles accesses are
--   .upsert({user_id, fcode, username, updated_at}, {onConflict:'user_id'})
--   .select('user_id,username,fcode').eq('fcode', ...)
--   .select('user_id,username,fcode').in('user_id', ...)
-- Every column touched is in the grant below. The upsert has no .select()
-- chained, so supabase-js v2 sends Prefer: return=minimal and there is no
-- RETURNING needing SELECT privilege; the on conflict (user_id) arbiter needs
-- SELECT on user_id, which is granted.
--
-- The one-line undo, if a column grant ever gets in the way:
--
--     grant select on public.profiles to anon, authenticated;
--
-- It restores the old blanket read — and re-opens the hidden_slugs leak, so
-- do not leave it there.

revoke select on public.profiles from anon, authenticated;
grant select (user_id, fcode, username, updated_at)
  on public.profiles to anon, authenticated;

-- ---------------------------------------------------------------- 2. the rpcs --

-- All three are SECURITY DEFINER and all three name pg_temp explicitly. Left
-- off, Postgres searches the caller's temporary schema FIRST for relation
-- names, so anyone who could get a temp table called `profiles` onto a pooled
-- connection would choose what these read. Nothing in clubd creates temp
-- tables, so this is closing a door while it is already shut — the sweep
-- migrate-add-rate-limits.sql started and PART 1 §6 continued.
--
-- ONE KNOWN ROUGH EDGE, LEFT ALONE DELIBERATELY. set_privacy() and
-- set_list_hidden() both insert a profiles row if the user has none, and that
-- row can carry a NULL fcode and a NULL username — if somebody flips a switch
-- before ensureFcode() and mirrorProfile() have landed, they are briefly
-- nameless and codeless to everyone. It is self-healing: mirrorProfile()
-- fills both on the next pass and fetchFriendEdges() already falls back to
-- 'someone'. Minting an fcode here instead would mean duplicating the
-- browser's code alphabet in SQL and keeping the two in step forever, which
-- buys a few seconds of cosmetics for a permanent second source of truth.
-- Not worth it. Recorded so the next reader knows it was weighed.

-- Returns one json object rather than a row so the output names cannot
-- collide with the column names inside it. Null for a signed-out caller,
-- which is what makes "no settings, no controls" work in the browser.
--
-- A user with no profiles row gets the defaults, TRUE/TRUE/{} — the same
-- answer FINAL-1's friend_may_read() gives for that user, deliberately. The
-- switch on the page and the rule in the database must never disagree.
create or replace function public.privacy_settings()
returns json language sql security definer stable
set search_path = public, pg_temp as $$
  select json_build_object(
           'share_progress', coalesce(p.share_progress, true),
           'share_activity', coalesce(p.share_activity, true),
           'hidden_slugs',   coalesce(p.hidden_slugs, '{}'::text[]))
    from (select auth.uid() as uid) me
    left join public.profiles p on p.user_id = me.uid
   where me.uid is not null;
$$;

-- Null means "leave that one alone", so the two switches never overwrite each
-- other — someone toggling activity on a phone cannot silently undo a
-- progress switch thrown on a laptop a second earlier. One statement, so
-- there is no read-modify-write to lose.
create or replace function public.set_privacy(
  p_share boolean default null, p_activity boolean default null
) returns json language plpgsql security definer
set search_path = public, pg_temp as $$
begin
  if auth.uid() is null then
    raise exception 'must be signed in to change privacy settings';
  end if;
  insert into public.profiles (user_id, share_progress, share_activity, updated_at)
  values (auth.uid(), coalesce(p_share, true), coalesce(p_activity, true), now())
  on conflict (user_id) do update
    set share_progress = coalesce(p_share, profiles.share_progress),
        share_activity = coalesce(p_activity, profiles.share_activity),
        updated_at     = now();
  return public.privacy_settings();
end $$;

-- One slug at a time, added and removed server-side, so two devices editing
-- the set cannot write each other's copy of the whole array back.
--
-- THE `for update` IS THE FIX, and it is the whole difference from the root
-- migration. Without it this function reads hidden_slugs, thinks, and writes
-- the array back — and two devices hiding two different lists in the same
-- instant leave one of them UNHIDDEN: a privacy setting that silently did not
-- apply, which is the exact failure the comment above it claimed to prevent.
-- The row lock makes the second caller wait for the first to commit and then
-- read what it wrote. One word, no restructuring, and the 500 cap below is
-- now checked under the same lock that the write takes.
create or replace function public.set_list_hidden(p_slug text, p_hidden boolean)
returns json language plpgsql security definer
set search_path = public, pg_temp as $$
declare cur text[];
begin
  if auth.uid() is null then
    raise exception 'must be signed in to change privacy settings';
  end if;
  -- the same shape src/build.py demands of a slug, so the column cannot fill
  -- up with anything that was never a list. All 126 slugs in properties/
  -- pass it. The front end passes SLUG and never CKEY, so the `slug#fw` form
  -- never arrives here — and it does not need to, because FINAL-1's
  -- friend_may_read() splits on '#' when it reads.
  if p_slug is null or p_slug !~ '^[A-Za-z][A-Za-z0-9_-]*$' then
    raise exception 'that is not a list';
  end if;

  insert into public.profiles (user_id, updated_at) values (auth.uid(), now())
    on conflict (user_id) do nothing;

  select hidden_slugs into cur from public.profiles
   where user_id = auth.uid()
     for update;
  if not found then
    -- unreachable: the insert above guarantees the row. Here so that a future
    -- change which removes the insert fails loudly instead of writing zero
    -- rows and reporting success.
    raise exception 'no profile row to change';
  end if;

  if p_hidden then
    -- 500 is far past the whole catalogue and always will be at this rate; it
    -- is here so a scripted client cannot use somebody's profile row as free
    -- storage, not because anyone will ever hide a hundred lists.
    if coalesce(array_length(cur, 1), 0) >= 500 then
      raise exception 'too many hidden lists';
    end if;
    if not (p_slug = any (cur)) then cur := cur || p_slug; end if;
  else
    cur := array_remove(cur, p_slug);
  end if;

  update public.profiles set hidden_slugs = cur, updated_at = now()
   where user_id = auth.uid();
  return public.privacy_settings();
end $$;

-- ------------------------------------------- 3. revokes that actually revoke --

-- `revoke ... from public` ALONE IS NOT ENOUGH, and the root migration's
-- comment asserted the opposite. Functions in schema public are granted
-- EXECUTE to PUBLIC by Postgres, and Supabase's default privileges grant anon
-- and authenticated ON TOP, directly. Revoking PUBLIC does not remove a
-- role-specific grant, so anon would keep EXECUTE on all three. Not
-- exploitable today — privacy_settings() returns NULL for a null auth.uid()
-- and the other two raise — but it is precisely the mistake PART 1 §3 was
-- written to fix, and the next function written to that pattern may not
-- check. Three-way revoke, then grant back exactly what the browser needs.

revoke all on function public.privacy_settings()
  from public, anon, authenticated;
revoke all on function public.set_privacy(boolean, boolean)
  from public, anon, authenticated;
revoke all on function public.set_list_hidden(text, boolean)
  from public, anon, authenticated;

grant execute on function public.privacy_settings()             to authenticated;
grant execute on function public.set_privacy(boolean, boolean)  to authenticated;
grant execute on function public.set_list_hidden(text, boolean) to authenticated;

-- FINAL-1's friend_may_read() is NOT revoked here and must not be: RLS policy
-- expressions run with the privileges of the querying role, so both browser
-- roles need EXECUTE on it or every select on progress and thumbs fails with
-- "permission denied for function". FINAL-1 grants it explicitly.

-- --------------------------------- 4. the merged rules survived this file --

-- Nothing above touches a policy. This proves it, in the same transaction, so
-- that if some future edit to this file ever does touch one, the file stops
-- committing until somebody reads this comment.
do $$
declare q text;
begin
  select pg_get_expr(pol.polqual, pol.polrelid) into q
    from pg_policy pol
    join pg_class c     on c.oid = pol.polrelid
    join pg_namespace n on n.oid = c.relnamespace
   where n.nspname = 'public' and c.relname = 'progress'
     and pol.polname = 'mutual friends read progress';
  if q is null or q not like '%is_private_property%' or q not like '%friend_may_read%' then
    raise exception 'this file changed the progress policy. It must not. In force: %', coalesce(q, '<none>');
  end if;
end $$;

commit;

-- ===========================================================================
-- Check it worked
-- ===========================================================================
--
--   select proname, proacl from pg_proc
--    where proname in ('privacy_settings','set_privacy','set_list_hidden');
--        -- each acl: the owner, plus authenticated=X. No anon. No PUBLIC.
--
--   select grantee, privilege_type, column_name
--     from information_schema.column_privileges
--    where table_schema = 'public' and table_name = 'profiles'
--      and grantee in ('anon','authenticated') and privilege_type = 'SELECT';
--        -- user_id, fcode, username, updated_at — and nothing else.
--        -- share_progress, share_activity and hidden_slugs must NOT appear.
--
--   select policyname, qual from pg_policies
--    where policyname = 'mutual friends read progress';
--        -- still carries BOTH is_private_property and friend_may_read
--
-- POSTGREST'S SCHEMA CACHE. sb.rpc('privacy_settings') is not callable until
-- PostgREST reloads. Supabase installs an event trigger that does this
-- automatically, but there is a window — usually seconds, occasionally
-- longer — in which the deployed front end gets PGRST202 and keeps the
-- controls hidden. Reload the account page twice before concluding anything.
--
-- PROVING IT BLOCKS — impersonate the reader and ask for the row directly.
-- This changes nothing; it rolls back.
--
--   begin;
--     set local role authenticated;
--     set local request.jwt.claims = '{"sub":"<B-uuid>","role":"authenticated"}';
--     select property_id from public.progress where user_id = '<A-uuid>';
--     select property_id, item_id from public.thumbs where user_id = '<A-uuid>';
--   rollback;
--
-- Run it once before A hides anything: A's lists are listed. Then, as
-- postgres:
--   update public.profiles set hidden_slugs = array['<slug>'] where user_id = '<A-uuid>';
-- and run it again: that slug is gone from B's progress result, so is
-- `<slug>#fw` if a fresh watch existed, AND SO ARE A's THUMB ROWS FOR IT —
-- that last one is what the root migration missed, and it is why hiding a
-- list no longer leaves your name on a friend's thumb pill for it. Set
-- share_progress false and B's result is empty entirely. The rows are still
-- in the tables; select them as postgres and they are right there. B simply
-- cannot reach them, which is the whole point.
--
-- The club branch, checked in the same breath: put A and B in a club for the
-- hidden list and re-run as B. The progress row comes back, because
-- "read group progress" is a separate OR branch. If it does NOT come back,
-- something has leaked into the club path and must be undone before this
-- ships.
-- ===========================================================================
