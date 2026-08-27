# Superseded migrations — do not run

These files were once live migrations. They are kept because a superseded file
is often the only record that a change was ever made, and **they must not be
pasted into the SQL editor**. Most raise no error when re-run, and several leave
their own verification blocks passing while undoing protection that later work
installed.

They sit here rather than in the `migrate-*.sql` namespace deliberately: they
used to have names shaped exactly like the migrations that ARE meant to be run,
which is the whole hazard.

**The bootstrap is in [`DATABASE.md`](../DATABASE.md). Nothing in this folder is
part of it.**

## Files that would revert live protection

### `migrate-add-friend-privacy.sql`

Recreates `"mutual friends read progress"` **without the gated-list term**. Run
it after FINAL-1 and the password-gated list is readable by every mutual friend
again. Superseded by `FINAL-1-rls-locks.sql` and `FINAL-2-privacy.sql`.

### `migrate-add-thumbs-friends-policy.sql`

The `mutual friends read thumbs` policy as it originally shipped, carrying
**neither** the gated-list term nor the privacy term — so one statement undoes
both `rls-fix-PART1` §5b and `FINAL-1` §6. Superseded by `FINAL-1` §6.

*This was split out of `migrate-add-thumbs.sql` on 2026-08-27. The rest of that
file — the `thumbs` table, its two indexes and its four own-row policies — is
the **only** copy in the repo and was never superseded, so it now lives at
[`../migrate-add-thumbs.sql`](../migrate-add-thumbs.sql) and is part of the
bootstrap. While it sat here, a fresh install obeying this README would have
finished with no `thumbs` table and no error, because every thumbs call in the
front end swallows a missing-relation error by design.*

### `migrate-add-join-or-create.sql`

Defines an older `join_or_create_group` with **no rate-limit calls**.
Superseded by `migrate-add-rate-limits.sql`. Running it disarms the join cap on
one door while leaving `join_group()`'s intact — and a half-disarmed limiter
reads exactly like a working one.

### `migrate-add-friend-shelves.sql`

The weakest of the five copies of `"mutual friends read progress"` — neither the
gated-list term nor the privacy term. Superseded by `FINAL-1-rls-locks.sql`.

### `migrate-to-multiproperty.sql`

Carries the pre-groups, property-only body of `shares_group_with(uuid, text)`
against the live club/group version. Same signature, so it replaces silently.
Everything it adds is already in `schema.sql` in final form.

## Redundant rather than dangerous

### `migrate-add-owner-removal.sql`

`is_group_owner` and `"owner removes member"`, both already in `schema.sql` in
identical form. Its `is_group_owner` is the *older* copy, so a re-run would
revert the `search_path` hardening `rls-fix-PART1` applied.

### `migrate-add-schedule-start.sql`

One `alter table groups add column if not exists schedule_start date`, and
`schema.sql`'s `create table groups` already carries the column. The only
genuinely inert file here.

---

**Why these were retired rather than deleted.** Several are the only surviving
record of a change that really was made to the production database, and the
history in `DATABASE.md` cites them. A file nobody may run is still evidence.
