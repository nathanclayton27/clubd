-- GroupWatch — anchor a property's schedule to a date the group picks
--
-- Run ONCE in the Supabase SQL editor. Additive and safe to re-run.
--
-- A property with a relative schedule describes a shape — "20 episodes in the
-- first week, 10 in the second" — and nothing more. It has no dates of its own,
-- so nobody sees a pace line until a group says when it started. This column is
-- that date. Null means the schedule is not running yet.
--
-- Distinct from start_date, which defaults to the day the group was created and
-- therefore cannot tell you whether anyone actually chose it.

alter table groups add column if not exists schedule_start date;
