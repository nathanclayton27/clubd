-- GroupWatch — let a group's owner remove members
--
-- Run ONCE in the Supabase SQL editor, after migrate-to-multiproperty.sql.
-- Additive and safe to re-run.
--
-- Until now the only delete policy on group_members was "leave group", which
-- matches auth.uid() = user_id — you could remove yourself and nobody else.
-- This adds the group's creator as the one other person who may remove a row.

-- Ownership is checked by a definer function for the same reason the membership
-- tests are: a policy on group_members that reads `groups` would otherwise be
-- filtered by that table's own RLS, and the check would silently fail closed.
create or replace function is_group_owner(gid uuid)
returns boolean language sql security definer stable set search_path = public as $$
  select exists (
    select 1 from groups
    where id = gid and created_by = auth.uid()
  );
$$;

do $$ begin
  create policy "owner removes member" on group_members
    for delete using (is_group_owner(group_id));
exception when duplicate_object then null; end $$;

-- Note the owner can also remove themselves through this policy. That is the
-- same outcome as leaving, and it leaves the group ownerless rather than
-- deleting it — the UI offers "Leave group" for that instead and does not show
-- a remove control against your own row.
