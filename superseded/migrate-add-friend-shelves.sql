-- Friends page shelves (CLU-72): run once in the Supabase SQL editor.
-- Lets you read the progress rows of MUTUAL friends only — both
-- directions of the friendship must exist. Counts power the top-3/4
-- shelf preview on the Friends page; nobody one-sided sees anything.
create policy "mutual friends read progress" on public.progress
  for select using (
    exists (select 1 from public.friendships f1
            where f1.a = auth.uid() and f1.b = progress.user_id)
    and
    exists (select 1 from public.friendships f2
            where f2.a = progress.user_id and f2.b = auth.uid())
  );
