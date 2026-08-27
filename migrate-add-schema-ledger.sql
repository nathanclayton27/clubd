-- clubd — an applied-migrations ledger (CLU-404)
--
-- Run ONCE in the Supabase SQL editor. Genuinely safe to run twice — see
-- "HOW RE-RUNNING WORKS" below, which is enforced by a unique constraint
-- rather than promised by a comment.
--
-- ===========================================================================
-- WHY
-- ===========================================================================
--
-- The database has never recorded what has been run against it. DATABASE.md's
-- history is reconstructed from run confirmations pasted onto Linear threads,
-- which means five early files have no run record at all, a body edited by
-- hand in the SQL editor would leave no trace anywhere, and nothing can answer
-- "has this already run?" except a person reading comment threads.
--
-- That is not a theoretical cost. tools/whereis.py needed a hand-kept list of
-- what had run, and the list was WRONG: while a never-run file sat in it, the
-- tool reported a live definition for `find_profile_by_code`, an object that
-- has never existed in this database.
--
-- ===========================================================================
-- ONE ROW PER RUN, NOT PER FILE
-- ===========================================================================
--
-- Re-running the wrong file is the main hazard in this repo — rls-fix-PART1
-- reverts four things silently, superseded/migrate-add-friend-shelves.sql
-- reverts the privacy switches, migrate-perf-shares.sql replaces a live
-- function with a same-signature body. A ledger keyed on filename would let a
-- second run quietly overwrite the record of the first, which is precisely the
-- event most worth seeing.
--
-- So: one row per RUN. A file that ran twice has two rows. `outcome` also
-- records failures, so migrate-groups.sql aborting on 2026-08-26 22:44 is
-- history rather than a hole in the record.
--
-- **This file obeys that rule about ITSELF.** An earlier draft recorded itself
-- with `where not exists (... where filename = ...)`, i.e. keyed on filename,
-- one row per file — the exact design these paragraphs argue against. An audit
-- caught it. Run this file three times and there are three rows for it.
--
-- ===========================================================================
-- HOW RE-RUNNING WORKS
-- ===========================================================================
--
-- `schema_migrations_run_uk` is unique on (filename, applied_at). The backfill
-- below carries FIXED timestamps, so a second run conflicts row-for-row and
-- does nothing. The self-record uses now(), which differs every run, so every
-- run is recorded.
--
-- That one constraint replaces a hand-written guard, and is strictly better
-- than the `if exists (... where source = 'backfilled')` an earlier draft used:
-- that guard tripped on a SINGLE surviving backfilled row, so deleting one row
-- and re-running would not restore it. This form restores it.
--
-- It heals a DELETED row, not a CORRECTED one. `do nothing` means a later edit
-- to any evidence, note or outcome value below will NOT take effect on a
-- re-run — the existing row wins. Changing a backfilled value is a deliberate
-- UPDATE, not a re-run of this file.
--
-- ===========================================================================
-- WHAT THIS TABLE IS NOT
-- ===========================================================================
--
-- It records what it was TOLD. It is much better evidence than a comment
-- thread and it is still not the database's own account of its own functions.
-- A body edited by hand in the SQL editor remains invisible; the only honest
-- check for that is to run each migration's readback block, which is
-- read-only. DATABASE.md §6 says so and should go on saying so.
--
-- Backfilled rows carry NO CHECKSUM on purpose. We do not know the bytes of
-- what ran, and several of those files have been edited since — PART1 gained
-- a do-not-re-run banner, schema.sql gained one, migrate-add-thumbs.sql was
-- split in two. Recording today's checksum as though it were the one that ran
-- would manufacture exactly the false confidence this file exists to remove.

begin;

-- ---------------------------------------------------------------- the table

create table if not exists public.schema_migrations (
  id          bigint generated always as identity primary key,
  filename    text        not null,
  applied_at  timestamptz not null default now(),
  checksum    text,
  source      text        not null default 'recorded',
  outcome     text        not null default 'applied',
  evidence    text,
  note        text
);

-- `create table if not exists` is silent about SHAPE, which is the table-level
-- version of DATABASE.md trap 4 — and the name is not far-fetched, since the
-- Supabase CLI keeps its own `schema_migrations` (in the supabase_migrations
-- schema, not public, but close enough to be worth refusing rather than
-- assuming). If a table of this name already exists without these COLUMN
-- NAMES, stop loudly instead of half-applying against it.
--
-- Names only: types, nullability, defaults and the identity property are NOT
-- checked. A pre-existing table with the right names and wrong types passes
-- here and fails later on the first insert — inside this transaction, so it
-- still cannot half-apply.
do $$
declare
  missing text;
begin
  select string_agg(c, ', ') into missing
  from unnest(array['id','filename','applied_at','checksum',
                    'source','outcome','evidence','note']) as c
  where not exists (
    select 1 from information_schema.columns
    where table_schema = 'public' and table_name = 'schema_migrations'
      and column_name = c);
  if missing is not null then
    raise exception
      'public.schema_migrations exists with a different shape; missing: %',
      missing;
  end if;
end $$;

-- Both constraints are qualified by `conrelid`. `pg_constraint.conname` is
-- unique per RELATION, not per schema, so an unqualified name lookup can match
-- a constraint of the same name on a different table and silently skip.
do $$
begin
  if not exists (select 1 from pg_constraint
                 where conrelid = 'public.schema_migrations'::regclass
                   and conname = 'schema_migrations_source_ck') then
    alter table public.schema_migrations
      add constraint schema_migrations_source_ck
      check (source in ('recorded', 'backfilled'));
  end if;
  -- 'partial' exists because several files in this repo have no transaction
  -- (DATABASE.md names them), so a run really can end half-applied.
  --
  -- 'unknown' exists so that "we believe this ran but cannot show it" is
  -- representable rather than being rounded up to 'applied'. THREE rows below
  -- use it — the three whose note says "no run record". The site working proves
  -- the schema exists; it does not prove THIS FILE is what put it there, and a
  -- ledger that cannot tell those apart manufactures the certainty this file
  -- exists to refuse.
  if not exists (select 1 from pg_constraint
                 where conrelid = 'public.schema_migrations'::regclass
                   and conname = 'schema_migrations_outcome_ck') then
    alter table public.schema_migrations
      add constraint schema_migrations_outcome_ck
      check (outcome in ('applied', 'failed', 'partial', 'unknown'));
  end if;
  -- The constraint that makes every insert below idempotent.
  if not exists (select 1 from pg_constraint
                 where conrelid = 'public.schema_migrations'::regclass
                   and conname = 'schema_migrations_run_uk') then
    alter table public.schema_migrations
      add constraint schema_migrations_run_uk unique (filename, applied_at);
  end if;
end $$;

create index if not exists schema_migrations_file_idx
  on public.schema_migrations (filename, applied_at desc);

-- ------------------------------------------------------------ who may read it
--
-- Nobody, through the API. This is operational metadata, not user data: the
-- site never reads it and should not be able to enumerate which migrations
-- exist.
--
-- **RLS ON with NO POLICIES is the part that actually holds.** The revoke is
-- defence in depth, not the guarantee: an earlier draft of this comment claimed
-- the revoke would stop a later `grant all on all tables` sweep reopening the
-- table, and it would not — such a sweep re-grants regardless. RLS with no
-- policies is what survives it.
--
-- `from public` is included, matching every other lock-down in this repo
-- (migrate-add-rate-limits.sql, migrate-groups.sql, migrate-mute-privacy.sql).
-- Omitting it leaves a grant to PUBLIC in place, which anon and authenticated
-- both inherit — and which `information_schema.role_table_grants` does not
-- even show, so the omission would have been invisible to the readback too.
--
-- `service_role` is deliberately NOT revoked: it is the admin identity behind
-- the service key and revoking it would break legitimate maintenance. It never
-- reaches this table from the site.

alter table public.schema_migrations enable row level security;
revoke all on public.schema_migrations from public, anon, authenticated;

-- The identity column implicitly creates public.schema_migrations_id_seq, and
-- Supabase's default privileges grant sequences to anon and authenticated. A
-- revoke on the TABLE does not touch it, and a sequence's `last_value` is the
-- row count — which is precisely the enumeration the paragraph above says this
-- is preventing. No API path reaches it today (PostgREST does not expose
-- sequences), so this closes a gap rather than a hole.
revoke all on sequence public.schema_migrations_id_seq
  from public, anon, authenticated;

-- --------------------------------------------------------------- the backfill
--
-- Everything DATABASE.md records, marked `backfilled` so a reconstructed
-- history is never mistaken for an observed one. Fixed timestamps + the unique
-- constraint make this idempotent AND self-healing: a deleted row comes back
-- on the next run, and nothing duplicates.
--
-- Filenames are PATH-QUALIFIED, so they join against `python tools/migrations.py`,
-- which lists by path. Bare basenames cannot: five of these files now live
-- under superseded/ and a basename cannot tell them apart.

insert into public.schema_migrations
  (filename, applied_at, source, outcome, evidence, note)
values
  -- Before the Linear board existed. Dates are the COMMIT dates; no run was
  -- ever confirmed, so these are the weakest rows in the table and say so.
  ('schema.sql',                                  '2026-08-19T00:00:00Z', 'backfilled', 'unknown', 'commit 936e52b', 'no run record; inferred from the site working'),
  ('superseded/migrate-to-multiproperty.sql',     '2026-08-19T00:00:00Z', 'backfilled', 'applied', 'CLU-34',         'strong: a 2026-08-25 pg_policies dump shows the 2-arg shares_group_with this file introduced'),
  ('superseded/migrate-add-owner-removal.sql',    '2026-08-19T00:00:00Z', 'backfilled', 'applied', 'CLU-34',         'circumstantial: CLU-34 reasons about "owner removes member" as live'),
  ('superseded/migrate-add-schedule-start.sql',   '2026-08-19T00:00:00Z', 'backfilled', 'unknown', 'commit af59c94', 'no run record. Adds groups.schedule_start — the date a GROUP picks. (An earlier draft cited CLU-47 here; that card is solo schedules, it is still in Todo, and it was created four days after this date.)'),
  ('superseded/migrate-add-join-or-create.sql',   '2026-08-21T00:00:00Z', 'backfilled', 'unknown', null,             'no run record, and moot: migrate-add-rate-limits.sql replaced its function on 2026-08-24'),

  -- Board-confirmed from here down.
  ('migrate-add-tick-events.sql',                 '2026-08-23T00:00:00Z', 'backfilled', 'applied', 'CLU-25',  'tick_events, two indexes, three policies, the update guard'),
  ('migrate-add-friends.sql',                     '2026-08-24T17:12:00Z', 'backfilled', 'applied', 'CLU-69',  'SQL pasted inline and byte-identical to the repo file'),
  ('migrate-add-friend-decline.sql',              '2026-08-24T17:26:00Z', 'backfilled', 'applied', 'CLU-102', 'one policy'),
  ('superseded/migrate-add-friend-shelves.sql',   '2026-08-24T18:04:00Z', 'backfilled', 'applied', 'CLU-72',  'the first "mutual friends read progress"; since superseded twice — do not re-run'),
  ('migrate-add-rate-limits.sql',                 '2026-08-24T22:27:00Z', 'backfilled', 'applied', 'CLU-35',  'rate_events, four functions, rate-limited join_group and join_or_create_group'),
  ('migrate-add-thumbs.sql',                      '2026-08-24T23:43:00Z', 'backfilled', 'applied', 'CLU-43',  'ran while filed under superseded/; split 2026-08-27, DDL half now at the root'),
  ('rls-fix-PART1-safe-now.sql',                  '2026-08-25T00:06:00Z', 'backfilled', 'applied', 'CLU-34',  'confirmed by a pasted pg_policies dump. DO NOT RE-RUN — see its banner'),
  ('FINAL-1-rls-locks.sql',                       '2026-08-25T18:32:00Z', 'backfilled', 'applied', 'CLU-195', 'readback at 18:37 returned both friends-read policies in the merged form'),
  ('FINAL-2-privacy.sql',                         '2026-08-25T18:39:00Z', 'backfilled', 'applied', 'CLU-195', 'profiles 4-column grant; privacy_settings, set_privacy, set_list_hidden'),
  ('migrate-groups.sql',                          '2026-08-26T22:44:00Z', 'backfilled', 'failed',  'CLU-387', 'ERROR 42703 at line 371: a language sql body bound a column added later. Transaction aborted, database untouched'),
  ('migrate-groups.sql',                          '2026-08-26T23:00:00Z', 'backfilled', 'applied', 'CLU-387', 're-run after reordering; 19/19 readback at 23:04'),
  ('migrate-mute-privacy.sql',                    '2026-08-26T23:47:00Z', 'backfilled', 'applied', 'CLU-392', '7/7 readback'),
  ('migrate-group-thumbs.sql',                    '2026-08-27T00:27:00Z', 'backfilled', 'applied', 'CLU-390', '5/5 readback')
on conflict on constraint schema_migrations_run_uk do nothing;

-- ------------------------------------------------------- record this run
-- The ledger is append-only: one row per RUN, not per file, so a second run
-- of this file is visible rather than overwriting the record of the first.
-- Inside the transaction above, so a rollback un-records it too.
--
-- The checksum covers everything ABOVE this marker, not the whole file. It has
-- to: this block contains the checksum, so a whole-file digest would be wrong
-- the moment it was pasted here. What it identifies is the migration body —
-- the part that actually runs — which is the thing worth identifying.
--
-- Re-generate it after ANY edit above:
--     python tools/migrations.py --footer migrate-add-schema-ledger.sql CLU-404

insert into public.schema_migrations
  (filename, applied_at, checksum, source, outcome, evidence, note)
values ('migrate-add-schema-ledger.sql', now(), 'bf69b0fad254dcca851fbe1985ac0577c441792844d6aed8f9c2d0acd87dacb5', 'recorded', 'applied', 'CLU-404', null);

commit;

-- ===========================================================================
-- READBACK — read-only. Paste the output back onto CLU-404.
-- ===========================================================================

select '01 table exists'          as check,
       to_regclass('public.schema_migrations') is not null as ok
union all
select '02 RLS is on',
       (select relrowsecurity from pg_class
        where oid = 'public.schema_migrations'::regclass)
union all
select '03 no policies on it (deny-all)',
       (select count(*) = 0 from pg_policies
        where schemaname = 'public' and tablename = 'schema_migrations')
union all
-- has_table_privilege, not information_schema. That view omits privileges held
-- via a grant to PUBLIC and lists grants by literal grantee, so privileges
-- reaching these roles by inheritance are invisible to it — both of which are
-- exactly the exposure this line is written against.
select '04 anon cannot select',
       not has_table_privilege('anon', 'public.schema_migrations', 'select')
union all
select '05 authenticated cannot select',
       not has_table_privilege('authenticated', 'public.schema_migrations', 'select')
union all
select '06 backfill is 18 rows',
       (select count(*) = 18 from public.schema_migrations
        where source = 'backfilled')
union all
select '07 the failed migrate-groups run is recorded',
       (select count(*) = 1 from public.schema_migrations
        where filename = 'migrate-groups.sql' and outcome = 'failed')
union all
select '08 migrate-groups has two rows, one each way',
       (select count(*) = 2 from public.schema_migrations
        where filename = 'migrate-groups.sql')
union all
select '09 no backfilled row claims a checksum',
       (select count(*) = 0 from public.schema_migrations
        where source = 'backfilled' and checksum is not null)
union all
-- >= 1, not = 1. Running this file twice SHOULD produce two rows here; an
-- equality would go red exactly when the append-only design worked.
select '10 this file recorded its own run',
       (select count(*) >= 1 from public.schema_migrations
        where filename = 'migrate-add-schema-ledger.sql'
          and source = 'recorded')
union all
select '11 the identity sequence is locked down for anon',
       not has_sequence_privilege('anon', 'public.schema_migrations_id_seq', 'select')
union all
select '12 ...and for authenticated',
       not has_sequence_privilege('authenticated', 'public.schema_migrations_id_seq', 'select')
union all
select '13 all three constraints exist on this table',
       (select count(*) = 3 from pg_constraint
        where conrelid = 'public.schema_migrations'::regclass
          and conname in ('schema_migrations_source_ck',
                          'schema_migrations_outcome_ck',
                          'schema_migrations_run_uk'))
union all
-- The vocabulary is only worth having if it is used. An earlier draft added
-- 'unknown' to the constraint and then recorded every uncertain row as
-- 'applied' anyway, which is the rounding-up it was added to prevent.
select '14 the three rows with no run record say so',
       (select count(*) = 3 from public.schema_migrations
        where outcome = 'unknown');

-- What has run, most recent first — the query this whole file exists to make
-- possible. `python tools/migrations.py --verify` prints a longer version that
-- also compares checksums against the files in the repo.
--
--   select filename, applied_at, outcome, source, evidence
--   from public.schema_migrations order by applied_at desc, id desc;
