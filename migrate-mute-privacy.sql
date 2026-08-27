-- ===========================================================================
-- THE PER-GROUP MUTE MUST NOT BE PUBLIC TO THE GROUP.          CLU-114 follow-up
-- ===========================================================================
-- Idempotent. Adds no column, drops no policy, rewrites no rows.
--
-- WHAT IS WRONG TODAY
-- migrate-groups.sql added `group_members.share_with_group` — the per-group
-- mute, one person's private choice about one roster. It did not narrow who
-- can READ that column, and `group_members` carries
--
--     create policy "members read roster" on group_members
--       for select using (is_group_member(group_id));
--
-- which is ROW-level and therefore covers EVERY COLUMN. Supabase's default
-- privileges give `authenticated` table-wide SELECT on top. So any co-member
-- can ask PostgREST for the roster and read the flag directly:
--
--     GET /rest/v1/group_members?select=*&group_id=eq.<theirs>
--
-- and learn EXACTLY WHO HAS MUTED THEM. The mute hides your progress and
-- then announces that you hid it, which is worse than not offering it — the
-- social fact it leaks is the whole thing a person mutes to avoid.
--
-- This is the same class as the hidden_slugs leak FINAL-2 was written to
-- close: "a privacy feature that publishes the privacy settings is not one."
--
-- HOW REACHABLE IS IT TODAY
-- AUDIT I-6 corrected an earlier draft of this comment, which claimed nothing
-- could set the flag yet. That is only true of the UI. `set_group_share()` is
-- live and granted to authenticated, so /rest/v1/rpc/set_group_share is
-- callable and discoverable right now — and `authenticated` also still holds
-- table UPDATE, so a direct PATCH works too. So a mute CAN be set today by
-- anyone willing to call the API, and it would be readable by their group.
--
-- No control exists on the site, so in practice every row sits at the `true`
-- default. But "no UI" is not "not reachable", and that argues for running
-- this SOONER rather than treating it as pre-emptive. It must certainly land
-- before the mute control ships — the ordering is the point.
--
-- WHY THIS IS SAFE FOR THE FRONT END
-- Column-level SELECT cannot be revoked from a role that holds table-wide
-- SELECT; the table grant has to come off and the wanted columns go back
-- individually. That breaks any caller doing `select('*')` on this table.
-- Checked before writing this: the site never does. Every read names its
-- columns —
--
-- AUDIT L-2 sharpened this. There are NINE call sites, not three, and the
-- WRITES matter as much as the reads: Postgres requires SELECT privilege on
-- any column named in an UPDATE or DELETE WHERE clause. All nine, verified in
-- src/template.html AND the deployed index.html:
--
--   reads   .select('group_id')                                     x3
--           .select('group_id, user_id')                            x1
--           .select('group_id, user_id, display_name, color_index') x1
--   writes  .update({display_name})  filtered on group_id + user_id x1
--           .delete()                filtered on group_id + user_id x3
--
-- No bare .select(), no PostgREST embed pulling group_members(...) from
-- another table, no .order(), no realtime channel. Every column any of the
-- nine touches is in the grant below.
--
-- And the failure mode is LOUD, not silent: Postgres expands `*` at parse
-- time and denies, so PostgREST returns 42501 / HTTP 403 rather than quietly
-- omitting the column. Which is exactly why this had to be verified.
-- — so no deployed query loses a column it was reading.
-- ===========================================================================

begin;

-- §0 ---------------------------------------------------------------- guard --
do $$
begin
  if not exists (select 1 from information_schema.columns
                  where table_schema = 'public' and table_name = 'group_members'
                    and column_name = 'share_with_group') then
    raise exception
      'group_members.share_with_group does not exist — run migrate-groups.sql '
      'first. There is nothing to protect yet.';
  end if;
end $$;

-- §1 ------------------------------------------------- narrow the read grant --
-- Table-wide SELECT off, then back column by column. Everything a client
-- legitimately reads is listed; share_with_group is the one deliberately
-- absent. RLS still applies on top of these — a non-member reads nothing at
-- all, exactly as before.
revoke select on public.group_members from public, anon, authenticated;

grant select (group_id, user_id, display_name, color_index, joined_at)
  on public.group_members to authenticated;

-- AUDIT M-1: anon gets the SAME narrowed columns, and withholding them would
-- have been a silent reversal of a decision an earlier migration made in
-- writing about this exact table. migrate-fix-rls-column-locks.sql says:
--
--   "SELECT is left in place on purpose: RLS already returns zero rows to
--    anon (verified against the live project), and revoking it would turn a
--    query that races the session into a hard error instead of an empty
--    result."
--
-- That is the difference between an empty roster and a red banner reading
-- "permission denied for table group_members". loadGroups() and loadMembers()
-- both `if(error) throw error`, so the sign-out-mid-flight window — session
-- cleared, module-level `user` not yet — would surface it to a real person.
--
-- It leaks nothing: "members read roster" is is_group_member(group_id), which
-- resolves through auth.uid(), which is null for anon. Zero rows either way.
-- FINAL-2 set the same precedent, re-granting its narrowed profiles columns to
-- anon AND authenticated rather than authenticated alone.
grant select (group_id, user_id, display_name, color_index, joined_at)
  on public.group_members to anon;

-- §2 ------------------------------------------------ your own answer, back --
-- Narrowing the grant hides the flag from everyone INCLUDING its owner, so
-- the person has to be able to read their own choice back or the checkbox
-- cannot draw itself. A definer function scoped to auth.uid() gives exactly
-- that and nothing else: it can only ever answer about you.
create or replace function public.my_group_shares()
returns table (group_id uuid, share_with_group boolean)
language sql security definer stable
set search_path = public, pg_temp as $$
  select m.group_id, m.share_with_group
    from group_members m
   where m.user_id = auth.uid();
$$;

revoke all on function public.my_group_shares()
  from public, anon, authenticated;
grant execute on function public.my_group_shares() to authenticated;

-- set_group_share() already writes only the caller's own row
-- (`where group_id = p_group and user_id = auth.uid()`), and is SECURITY
-- DEFINER so it is unaffected by the grant change above. Not touched here.

commit;

notify pgrst, 'reload schema';

-- ===========================================================================
-- READBACK — paste this whole block, one result table.
-- ===========================================================================
-- select '1 mute column NOT readable' as check,
--        has_column_privilege('authenticated','public.group_members',
--                             'share_with_group','select')::text as actual,
--        'false' as expect
-- union all select '2 roster columns still readable',
--        (has_column_privilege('authenticated','public.group_members','display_name','select')
--     and has_column_privilege('authenticated','public.group_members','user_id','select')
--     and has_column_privilege('authenticated','public.group_members','color_index','select'))::text,
--        'true'
-- union all select '3 anon cannot read the mute either',
--        has_column_privilege('anon','public.group_members','share_with_group','select')::text,
--        'false'
-- union all select '4 you can read your own mutes',
--        has_function_privilege('authenticated','public.my_group_shares()','execute')::text,
--        'true'
-- union all select '5 the roster policy is untouched',
--        (select count(*)::text from pg_policies
--          where schemaname='public' and tablename='group_members'
--            and policyname='members read roster'), '1'
-- union all select '6 anon reads the roster too (empty, not an error)',
--        has_column_privilege('anon','public.group_members','display_name','select')::text,
--        'true'
-- union all select '7 joined_at still readable',
--        has_column_privilege('authenticated','public.group_members','joined_at','select')::text,
--        'true'
-- order by 1;
-- ===========================================================================
