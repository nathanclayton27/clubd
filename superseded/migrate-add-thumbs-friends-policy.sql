-- RETIRED — DO NOT RUN. Kept only as the record of what used to be here.
--
-- This is the `mutual friends read thumbs` policy as it shipped with CLU-43.
-- It carries NEITHER the gated-list term NOR the privacy term, so running it
-- today undoes rls-fix-PART1 §5b and FINAL-1 §6 in a single statement — every
-- mutual friend regains read access to the password-gated list and to lists
-- people have hidden, with no error and with the verification blocks in both
-- of those files still passing.
--
-- Superseded by scratch/security/FINAL-1-rls-locks.sql §6.
-- Flagged by the independent SQL re-check on 2026-08-25 (CLU-201).
--
-- The rest of the original file — the thumbs table, its indexes and its four
-- own-row policies — was NOT superseded and is the only copy in the repo. It
-- lives at migrate-add-thumbs.sql in the root and is part of the bootstrap.

-- Mutual friends may READ, and only read — the same shape as the friend
-- shelves policy (CLU-72), deliberately copied rather than reinvented: both
-- directions of the friendship must exist, so nobody one-sided sees anything.
-- There is no matching write policy and there never should be.
drop policy if exists "mutual friends read thumbs" on public.thumbs;
create policy "mutual friends read thumbs" on public.thumbs
  for select using (
    exists (select 1 from public.friendships f1
            where f1.a = auth.uid() and f1.b = thumbs.user_id)
    and
    exists (select 1 from public.friendships f2
            where f2.a = thumbs.user_id and f2.b = auth.uid())
  );
