-- GroupWatch — migrate the single-property database to multi-property
--
-- Run this ONCE, in the Supabase SQL editor, against the project that already
-- runs the Secret Wars tracker. Run it before deploying the new front end.
--
-- Existing progress and groups are preserved: every current row is backfilled
-- to the 'hickman-secret-wars' property, which is the slug the exported
-- properties/hickman-secret-wars.json declares. Nobody loses a tick.
--
-- Safe to re-run; every step is guarded.

begin;

-- ------------------------------------------------------- progress per property

alter table progress add column if not exists property_id text not null
  default 'hickman-secret-wars';

do $$ begin
  alter table progress drop constraint progress_pkey;
  alter table progress add primary key (user_id, property_id);
exception
  when invalid_table_definition then null;  -- already recomposed
  when others then
    if sqlstate = '42P16' then null; else raise; end if;
end $$;

-- new rows must say which property they belong to
alter table progress alter column property_id drop default;

-- ---------------------------------------------------------- groups per property

alter table groups add column if not exists property_id text not null
  default 'hickman-secret-wars';
alter table groups alter column property_id drop default;

create index if not exists groups_property_idx on groups (property_id);

-- A property's schedule is a default, not a decree. A group can slide the whole
-- thing forward or back by a number of days — every arc window moves together,
-- so the pace is unchanged and only the dates differ. The existing
-- "creator updates group" policy already restricts who may set this.
alter table groups add column if not exists schedule_shift_days integer not null default 0;

-- ------------------------------------------- close the cross-property leak

-- The single-property version asked only "are we in a group together?". With
-- several properties that lets someone in your Fullmetal Alchemist group read
-- your Secret Wars progress. Scope the test to one property.

create or replace function shares_group_with(other uuid, prop text)
returns boolean language sql security definer stable set search_path = public as $$
  select exists (
    select 1
    from group_members a
    join group_members b using (group_id)
    join groups g on g.id = a.group_id
    where a.user_id = auth.uid()
      and b.user_id = other
      and g.property_id = prop
  );
$$;

drop policy if exists "read group progress" on progress;
create policy "read group progress" on progress
  for select using (shares_group_with(user_id, property_id));

-- the one-argument version is now unreferenced and would be a way around the
-- property scoping if anything called it
drop function if exists shares_group_with(uuid);

-- ------------------------------------------------ create_group takes a property

drop function if exists create_group(text, date, text);

create or replace function create_group(
  p_name text, p_target date, p_display_name text, p_property_id text
) returns groups language plpgsql security definer set search_path = public as $$
declare g groups;
begin
  if auth.uid() is null then
    raise exception 'must be signed in to create a group';
  end if;
  if coalesce(btrim(p_property_id), '') = '' then
    raise exception 'a group needs a property';
  end if;

  insert into groups (code, name, target_date, created_by, property_id)
  values (
    new_group_code(),
    coalesce(nullif(btrim(p_name), ''), 'Reading group'),
    p_target,
    auth.uid(),
    p_property_id
  )
  returning * into g;

  insert into group_members (group_id, user_id, display_name, color_index)
  values (g.id, auth.uid(),
          coalesce(nullif(btrim(p_display_name), ''), 'Reader'), 0);

  return g;
end $$;

revoke all on function create_group(text, date, text, text) from anon;
grant execute on function create_group(text, date, text, text) to authenticated;

commit;

-- Check it worked:
--   select property_id, count(*) from progress group by 1;
--   select property_id, count(*) from groups   group by 1;
