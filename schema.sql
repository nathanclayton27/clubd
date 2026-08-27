-- ###########################################################################
-- ##  THIS FILE IS A MIGRATION BEHIND THE LIVE DATABASE.  READ THIS FIRST.  ##
-- ###########################################################################
--
-- Last reconciled against production: NEVER. It describes a FRESH project.
--
-- The tables below are still broadly accurate. THE FUNCTIONS AND POLICIES ARE
-- NOT. Many have been replaced by later migrations, and this file does not
-- mention `private_properties`, `is_private_property()`, `club_progress`, the
-- rate limiter, or the five privacy settings at all.
--
-- ---------------------------------------------------------------------------
-- ##  DATABASE.md IS THE RECORD. THIS FILE IS STEP 1 OF ITS BOOTSTRAP.      ##
-- ---------------------------------------------------------------------------
--
-- Running this file ALONE does not produce the live database. It is the first
-- of twelve, and the other eleven are listed in order in DATABASE.md, which
-- also holds what has actually been run, when, and what is safe to run now.
--
-- Before copying ANY definition out of this file, run:
--     python tools/whereis.py <object>
-- 23 of 73 objects here are defined in more than one file, and whichever runs
-- last wins with no error raised.
--
-- One more thing this file gets wrong about itself: it is only PARTLY
-- idempotent. Its policies sit in two `do $$ ... exception when
-- duplicate_object then null` blocks, each wrapping several statements under
-- ONE handler — so if the first policy in a block already exists, the
-- exception aborts the block and the rest are never created, and it reports
-- success either way. A half-applied schema.sql cannot heal itself by being
-- re-run.
--
-- WHAT THIS HAS ALREADY COST, so nobody treats it as pedantry:
--
--   * A migration replaced `join_group()` with the body FROM THIS FILE. The
--     live one is the rate-limited version in migrate-add-rate-limits.sql, so
--     that replace would have silently deleted the entire brute-force
--     protection on club codes — from a migration whose stated purpose was
--     adding a boolean. An auditor caught it; the file did not warn anyone.
--   * A decision document quoted this file to argue the database "has never
--     known that list is special", and recommended building a table that
--     already existed.
--
-- Both are the same mistake: reading a RECORDED state as if it were the live
-- one, from a file that never said it was stale. It says so now.
--
-- BEFORE YOU COPY ANY FUNCTION OR POLICY OUT OF HERE:
--
--     python scratch/security/whereis.py <name>
--
-- It reports every .sql file that defines that object, newest applied first.
-- 23 of 73 objects in this repo are defined in more than one file. Whichever
-- file runs last wins, no error is raised, and whatever the loser carried
-- disappears without a trace.
--
-- It reads files, not the database — it tells you what to read, not what ran.
-- ###########################################################################

-- GroupWatch — database schema, for a FRESH project
--
-- If this project already runs the single-property Secret Wars tracker, do NOT
-- start here — run migrate-to-multiproperty.sql instead. It preserves existing
-- progress and groups; this file assumes empty tables.
--
-- Progress is one row per (person, property). Groups let several people track
-- the same property and see each other's progress stacked on one strip, which
-- means a group member can read your `progress` row for that property — and
-- only that property. Nobody outside your groups can, and joining is opt-in.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------- progress --

create table if not exists progress (
  user_id     uuid not null references auth.users on delete cascade,
  property_id text not null,
  read_ids    text[] not null default '{}',
  updated_at  timestamptz default now(),
  primary key (user_id, property_id)
);

alter table progress enable row level security;

do $$ begin
  create policy "read own"   on progress for select using (auth.uid() = user_id);
  create policy "write own"  on progress for insert with check (auth.uid() = user_id);
  create policy "update own" on progress for update using (auth.uid() = user_id)
                                                with check (auth.uid() = user_id);
exception when duplicate_object then null; end $$;

-- ------------------------------------------------------------------ groups --

create table if not exists groups (
  id                  uuid primary key default gen_random_uuid(),
  code                text unique not null,
  name                text not null,
  property_id         text not null,
  start_date          date not null default current_date,
  target_date         date,
  -- slide a property's whole schedule by N days; every window moves together
  schedule_shift_days integer not null default 0,
  -- a relative schedule has no dates of its own; this is when the group started
  -- it. Null means it is not running yet and nobody is behind.
  schedule_start      date,
  created_by          uuid references auth.users on delete set null,
  created_at          timestamptz default now()
);

create index if not exists groups_property_idx on groups (property_id);

create table if not exists group_members (
  group_id     uuid not null references groups on delete cascade,
  user_id      uuid not null references auth.users on delete cascade,
  display_name text not null,
  color_index  int not null default 0,
  joined_at    timestamptz default now(),
  primary key (group_id, user_id)
);

create index if not exists group_members_user_idx on group_members (user_id);

alter table groups        enable row level security;
alter table group_members enable row level security;

-- Membership tests run as the definer so the policies below can ask "is this
-- person in the group?" without the policy on group_members re-triggering
-- itself. A policy that selects from its own table recurses and errors out.

create or replace function is_group_member(gid uuid)
returns boolean language sql security definer stable set search_path = public as $$
  select exists (
    select 1 from group_members
    where group_id = gid and user_id = auth.uid()
  );
$$;

create or replace function is_group_owner(gid uuid)
returns boolean language sql security definer stable set search_path = public as $$
  select exists (
    select 1 from groups
    where id = gid and created_by = auth.uid()
  );
$$;

-- Scoped to one property on purpose. Without the join to groups, someone in
-- your Fullmetal Alchemist group could read your Secret Wars progress.
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

-- Policies. Note there is deliberately no plain select policy on `groups` by
-- code: a code you have not joined with is not readable, so the table cannot be
-- enumerated by guessing codes. Joining goes through join_group() below.

do $$ begin
  create policy "members read group" on groups
    for select using (is_group_member(id));

  create policy "creator updates group" on groups
    for update using (auth.uid() = created_by)
                with check (auth.uid() = created_by);

  create policy "creator deletes group" on groups
    for delete using (auth.uid() = created_by);

  create policy "members read roster" on group_members
    for select using (is_group_member(group_id));

  create policy "rename self" on group_members
    for update using (auth.uid() = user_id)
                with check (auth.uid() = user_id);

  create policy "leave group" on group_members
    for delete using (auth.uid() = user_id);

  create policy "owner removes member" on group_members
    for delete using (is_group_owner(group_id));

  -- the one privacy change: co-members can read each other's ticks, and only
  -- for the property that group is about
  create policy "read group progress" on progress
    for select using (shares_group_with(user_id, property_id));
exception when duplicate_object then null; end $$;

-- ------------------------------------------------------------------- rpcs --

-- Codes skip 0/O/1/I so they survive being read aloud or typed from a photo.
create or replace function new_group_code()
returns text language plpgsql security definer set search_path = public as $$
declare
  alphabet text := 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  c text;
  i int;
begin
  loop
    c := '';
    for i in 1..6 loop
      c := c || substr(alphabet, 1 + floor(random() * length(alphabet))::int, 1);
    end loop;
    exit when not exists (select 1 from groups where code = c);
  end loop;
  return c;
end $$;

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
  values (g.id, auth.uid(), coalesce(nullif(btrim(p_display_name), ''), 'Reader'), 0);

  return g;
end $$;

create or replace function join_group(
  p_code text, p_display_name text
) returns groups language plpgsql security definer set search_path = public as $$
declare
  g groups;
  taken int;
begin
  if auth.uid() is null then
    raise exception 'must be signed in to join a group';
  end if;

  select * into g from groups where code = upper(btrim(p_code));
  if not found then
    raise exception 'no group with that code';
  end if;

  select count(*) into taken from group_members where group_id = g.id;

  insert into group_members (group_id, user_id, display_name, color_index)
  values (g.id, auth.uid(),
          coalesce(nullif(btrim(p_display_name), ''), 'Reader'),
          taken)
  on conflict (group_id, user_id)
    do update set display_name = excluded.display_name;

  return g;
end $$;

revoke all on function create_group(text, date, text, text) from anon;
revoke all on function join_group(text, text)         from anon;
grant execute on function create_group(text, date, text, text) to authenticated;
grant execute on function join_group(text, text)         to authenticated;
