-- GroupWatch — join a group by a fixed code, creating it if nobody has yet.
--
-- Run once, on an existing database. Safe to run twice.
--
-- `join_group()` resolves a code that already exists, which is right for a code
-- someone read out to you. A secret list needs the other half: everybody who
-- types the password lands in the same group, and the first of them arrives
-- before that group exists. Rather than have one person create it by hand and
-- hope the code matches what the property file declares, this takes the code as
-- given and creates the group on first use.
--
-- Why this cannot be done with the existing functions: create_group() always
-- calls new_group_code(), so the code it produces is random and would never
-- match the one in the property. There is no way to ask for a specific code.
--
-- The code space is unchanged — six characters from an alphabet with 0, O, 1
-- and I removed — so a caller cannot squat on a code that a future
-- new_group_code() would have handed out, because that function already
-- re-rolls on collision.

create or replace function join_or_create_group(
  p_code text, p_name text, p_property_id text, p_display_name text
) returns groups language plpgsql security definer set search_path = public as $$
declare
  g groups;
  taken int;
  want text := upper(btrim(p_code));
begin
  if auth.uid() is null then
    raise exception 'must be signed in to join a group';
  end if;
  if want !~ '^[A-HJ-NP-Z2-9]{6}$' then
    raise exception 'a join code is six characters from the code alphabet';
  end if;
  if coalesce(btrim(p_property_id), '') = '' then
    raise exception 'a group needs a property';
  end if;

  select * into g from groups where code = want;

  if not found then
    insert into groups (code, name, property_id, created_by)
    values (want,
            coalesce(nullif(btrim(p_name), ''), 'Reading group'),
            p_property_id,
            auth.uid())
    returning * into g;
  elsif g.property_id is distinct from p_property_id then
    -- the same code cannot mean two different lists, or joining one would
    -- quietly hand out read access to progress on the other
    raise exception 'that code belongs to a different property';
  end if;

  select count(*) into taken from group_members where group_id = g.id;

  insert into group_members (group_id, user_id, display_name, color_index)
  values (g.id, auth.uid(),
          coalesce(nullif(btrim(p_display_name), ''), 'Reader'),
          taken)
  on conflict (group_id, user_id) do nothing;

  return g;
end $$;

revoke all on function join_or_create_group(text, text, text, text) from anon;
grant execute on function join_or_create_group(text, text, text, text) to authenticated;
