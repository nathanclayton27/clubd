-- ===========================================================================
-- THUMBS GET A GROUP READ POLICY.                       CLU-390 / audit F10
-- ===========================================================================
-- Idempotent. Adds no column, drops no existing policy, rewrites no rows.
-- One new permissive SELECT policy, and nothing else.
--
-- WHAT IS MISSING TODAY
-- The CLU-387 audit found this while checking something else (finding F10):
--
--   "shares_group_with() is referenced by exactly one policy in the entire
--    project: 'read group progress' on public.progress. There is no group
--    branch on thumbs (whose only non-owner policy is 'mutual friends read
--    thumbs') and none on tick_events."
--
-- So co-members can read each other's TICKS and not their THUMBS. For a
-- watch club that has always been true and nobody noticed, because club
-- members are usually friends too and the friends policy covered it. For a
-- GROUP it is the motivating case that breaks: a coworkers group exists
-- precisely because those people are NOT your friends, so the friends policy
-- covers none of them and the thumbs half of the feature silently does
-- nothing — with no error to explain why.
--
-- Nathan asked for the feature this unblocks on CLU-389:
--   "have thumbs be shown matching whatever graph/club tile has selected. so
--    if you're solo dont show thumbs for other people, if you're in group mode
--    show thumbs for everyone in the group, if you're in a club mode show
--    thumbs for all members of the club"
--
-- WHY THIS IS ADDITIVE AND NOT THE CLOBBER FINAL-1 WARNS ABOUT
-- FINAL-1 §6 says its two merged policies are the single definition and must
-- never be pasted into another migration, because "every copy is a future
-- silent clobber". This file does not touch them. It adds a NEW, separately
-- named policy beside them — exactly as "read group progress" already sits
-- beside "mutual friends read progress" on the other table. Permissive
-- policies OR together, so the friends rule keeps working untouched and this
-- one only ever widens.
--
-- WHY THE PREDICATE NEEDS NO PRIVACY LOGIC OF ITS OWN
-- shares_group_with() already carries all of it, as of migrate-groups.sql:
-- the club branch is unconditional for that club's own property (CLU-388:
-- "being in a club implies you want to share progress with club members"),
-- and the group branch ANDs the gated-list check, both global switches, both
-- per-list arrays and the per-group mute. Duplicating any of that here would
-- create a second place to keep in sync, which is the mistake FINAL-1 spent
-- a whole section warning about.
--
-- ORDER: run AFTER migrate-groups.sql. §0 refuses otherwise.
-- ===========================================================================

begin;

-- §0 ---------------------------------------------------------------- guard --
do $$
declare src text;
begin
  if to_regprocedure('public.shares_group_with(uuid, text)') is null then
    raise exception
      'shares_group_with(uuid, text) is missing — run migrate-groups.sql first.';
  end if;

  -- and that it is the POST-groups body. The pre-groups version has no
  -- group_may_read call, so a policy built on it would expose thumbs to group
  -- co-members with none of the privacy switches applied — the exact thing
  -- CLU-388 ruled must not happen.
  select prosrc into src from pg_proc
   where oid = 'public.shares_group_with(uuid, text)'::regprocedure;
  -- AUDIT F2: coalesce, because `NULL not like ...` is NULL and `if NULL then`
  -- is false — the guard would pass silently on a function whose body is not
  -- in prosrc (a PG14+ `begin atomic` body). Theoretical today; a guard that
  -- fails open is worth one word to close.
  if coalesce(src, '') not like '%group_may_read%' then
    raise exception
      'shares_group_with is the PRE-GROUPS body (no group_may_read) — re-run '
      'migrate-groups.sql first. Building a thumbs policy on it would ignore '
      'every privacy switch.';
  end if;

  if to_regprocedure('public.is_private_property(text)') is null then
    raise exception
      'is_private_property(text) is missing — run FINAL-1 first.';
  end if;
end $$;

-- §1 ------------------------------------------------------- the new policy --
-- IT MIRRORS "read group progress" EXACTLY. Nothing else.
--
-- The live definition, in migrate-to-multiproperty.sql:
--     create policy "read group progress" on progress
--       for select using (shares_group_with(user_id, property_id));
--
-- AUDIT F1 REJECTED AN EARLIER VERSION OF THIS FILE, and the mistake is worth
-- keeping written down because it looked more correct than the fix does.
--
-- That version added `not is_private_property(...)` at the policy level,
-- copied from FINAL-1's "mutual friends read thumbs". Wrong template. That
-- term encodes a FRIENDS-only decision which FINAL-1 deliberately did NOT
-- extend to clubs — its own comment says so: the gated list stops reaching
-- friends, and "Club members are untouched — read group progress is a
-- separate PERMISSIVE policy."
--
-- All the gating that belongs here already lives INSIDE shares_group_with,
-- and only on the group branch. The club branch is unconditional by design
-- (CLU-388). So a policy-level gate has exactly one reachable effect: it
-- blocks CLUB co-members from each other's thumbs on the gated list, while
-- their progress on that same list stays visible.
--
--   reader                        progress    thumbs, as first written
--   club co-member, normal list   visible     visible
--   club co-member, GATED list    visible     BLOCKED   <- the defect
--
-- The gated list has a club. So that version would have shipped CLU-389's
-- "in a club mode show thumbs for all members of the club" as a silent no-op
-- for the one club it matters most for — reproducing verbatim the failure
-- this file's own header was written to eliminate.
--
-- One line, no privacy logic of its own, and identical to the policy it
-- mirrors. If gated-list thumbs should ever be withheld from clubs, that is a
-- product decision to state out loud, not something to leave sitting in a
-- conjunct.
drop policy if exists "read group thumbs" on public.thumbs;
create policy "read group thumbs" on public.thumbs
  for select using (
    public.shares_group_with(thumbs.user_id, thumbs.property_id)
  );

commit;

notify pgrst, 'reload schema';

-- ===========================================================================
-- DELIBERATELY NOT DONE HERE
-- ===========================================================================
-- tick_events has no group branch either, and this file does not add one.
-- The activity feed it belongs to has not shipped, so there is nothing to
-- widen yet and adding a policy for an unbuilt surface would be widening
-- read access with no feature asking for it. Its own card when it lands.
--
-- ===========================================================================
-- READBACK — paste whole, one result table.
-- ===========================================================================
-- select '1 the group thumbs policy exists' as check,
--        (select count(*)::text from pg_policies
--          where schemaname='public' and tablename='thumbs'
--            and policyname='read group thumbs') as actual,
--        '1' as expect
-- union all select '2 the friends thumbs policy still has BOTH its halves',
--        (select (qual like '%is_private_property%'
--             and qual like '%friend_may_read%')::text from pg_policies
--          where schemaname='public' and tablename='thumbs'
--            and policyname='mutual friends read thumbs'), 'true'
-- union all select '3 it is a permissive SELECT policy',
--        (select (permissive || ' ' || cmd) from pg_policies
--          where schemaname='public' and tablename='thumbs'
--            and policyname='read group thumbs'), 'PERMISSIVE SELECT'
-- union all select '4 it carries NO gate of its own (audit F1)',
--        (select (qual like '%is_private_property%')::text from pg_policies
--          where schemaname='public' and tablename='thumbs'
--            and policyname='read group thumbs'), 'false'
-- union all select '5 it routes through the group predicate',
--        (select (qual like '%shares_group_with%')::text from pg_policies
--          where schemaname='public' and tablename='thumbs'
--            and policyname='read group thumbs'), 'true'
-- order by 1;
-- ===========================================================================
