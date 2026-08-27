-- clubd — thumbs: the taste signal behind recommendations (CLU-43)
--
-- THIS FILE IS PART OF THE BOOTSTRAP. Run it on a fresh project.
--
-- It was in superseded/ until 2026-08-27, which was a real bug: it is the ONLY
-- definition anywhere in this repo of the `thumbs` table, its two indexes and
-- its four own-row policies. A fresh install that obeyed that folder's "do not
-- paste" README would have ended up with no thumbs table at all, and the site
-- would have degraded silently because every thumbs call swallows a 42P01.
--
-- What was actually superseded is one policy — `mutual friends read thumbs` —
-- which now lives in superseded/migrate-add-thumbs-friends-policy.sql and must
-- NOT be run. FINAL-1 replaced it with a version carrying the gated-list and
-- privacy terms.
--
-- Re-running this file IS safe, and for a reason worth stating rather than
-- trusting: the table and indexes are `if not exists`, and each of the four
-- policies is a `drop policy if exists` followed by a `create policy`.
--
-- Drop-then-create is normally the dangerous pattern here — it is exactly how
-- the retired file below silently reverted two later protections. It is safe
-- in THIS file only because these four policies have no later definition
-- anywhere: `auth.uid() = user_id` is the whole rule and nothing has ever
-- widened or narrowed it. If that stops being true, this file becomes a trap
-- and belongs in superseded/ with the other half.
--
-- ===========================================================================
-- RUN ORDER — THE FRONT END IS ALREADY OUT, AND THAT IS FINE.
-- ===========================================================================
--
-- The thumbs UI ships BEFORE this file runs, and it is built to survive that.
-- Every thumb is written to localStorage first and works immediately; the
-- cloud copy is a mirror whose failures are swallowed on the first error
-- (THBROKEN in src/template.html) and never reach the console, a flash line
-- or the layout. Until this migration runs:
--
--   * thumbs work, persist across reloads, and mark rows watched — locally;
--   * they do not follow you to another device;
--   * friends' counts are simply absent, not broken.
--
-- Running this file is therefore an upgrade, not a repair. Nothing on the
-- site is dead while it waits — which is the standing rule here after the
-- friend-code episode: never ship a door with nothing behind it.
--
-- After running it, the next page load folds any cloud rows into the local
-- set (local wins a clash: the device in your hand is the one that just heard
-- from you) and friends' pills start appearing.
--
-- ===========================================================================
-- WHAT A THUMB IS
-- ===========================================================================
--
-- Two states and silence. Up, down, or no row at all — there is no neutral
-- value and no scale, because a five-star field turns 600 rows into a voting
-- booth. Removing an opinion deletes the row; it does not store a zero.
--
-- item_id NULL is the WHOLE-LIST thumb — "I'm a zombie person" — which the
-- recommendations engine weighs heaviest before any row-level taste exists.
-- Both levels are independent: a list thumb and a row thumb say different
-- things and neither implies the other.
--
-- property_id and item_id are the slugs and item ids from properties/*.json,
-- not foreign keys — the catalogue is static files, not database rows.

create table if not exists public.thumbs (
  user_id     uuid not null references auth.users (id) on delete cascade,
  property_id text not null,
  item_id     text,                       -- NULL = the whole list
  direction   text not null check (direction in ('up', 'down')),
  updated_at  timestamptz not null default now()
);

-- One opinion per person per thing. A plain unique (user_id, property_id,
-- item_id) would NOT do it: Postgres treats NULLs as distinct, so the
-- whole-list thumb could be stored twice over. coalesce() collapses that
-- case into a real key.
--
-- The expression index is also why the front end deletes and re-inserts
-- instead of upserting: PostgREST can only aim ON CONFLICT at a plain column
-- list, and no plain column list describes this index.
create unique index if not exists thumbs_one_per_thing
  on public.thumbs (user_id, property_id, coalesce(item_id, ''));

-- "everyone's thumbs on this list", which is the friend-pill query
create index if not exists thumbs_property
  on public.thumbs (property_id);

alter table public.thumbs enable row level security;

-- Your own rows, all four verbs. RLS with these policies and no others is
-- deny-by-default for everybody else: auth.uid() is NULL for the anon key, so
-- a signed-out stranger matches nothing here and never sees a thumb.
drop policy if exists "read own thumbs" on public.thumbs;
create policy "read own thumbs" on public.thumbs
  for select using (auth.uid() = user_id);

drop policy if exists "insert own thumbs" on public.thumbs;
create policy "insert own thumbs" on public.thumbs
  for insert with check (auth.uid() = user_id);

drop policy if exists "update own thumbs" on public.thumbs;
create policy "update own thumbs" on public.thumbs
  for update using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists "delete own thumbs" on public.thumbs;
create policy "delete own thumbs" on public.thumbs
  for delete using (auth.uid() = user_id);
