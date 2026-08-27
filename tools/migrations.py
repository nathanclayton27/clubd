"""The applied-migrations ledger, from the repo side (CLU-404).

The database records what has been run in `public.schema_migrations`. This is
the other half: it checksums the `.sql` files here, writes the footer a new
migration needs so it records itself, and prints a read-only query that
reconciles the two.

    python tools/migrations.py                 # every .sql, with its checksum
    python tools/migrations.py --footer F.sql  # the block to paste at F's end
    python tools/migrations.py --verify        # read-only SQL to run and paste back

It never connects to a database. Nothing here executes SQL; it prints text.

CHECKSUMS ARE NEWLINE-NORMALISED, and that is not fussiness. Two files in this
repo are stored CRLF while a third is their LF concatenation, and a byte-count
offered as proof that they matched did not reproduce — in a record whose whole
value is being trusted over guesswork, a checksum that changes when a file is
opened in a different editor is worse than none.
"""
import hashlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKIP_DIRS = (".claude/worktrees", "moved-to-repo")


# The footer a migration ends with is excluded from its own checksum. It has to
# be: the footer CONTAINS the checksum, so digesting the whole file gives a value
# that is wrong the instant it is pasted in — a self-reference with no fixpoint.
# Everything above this marker is "the migration body", which is the thing worth
# identifying anyway: it is what actually ran against the database.
FOOTER_MARK = "-- ------------------------------------------------------- record this run"


def digest(path):
    """sha256 of the migration BODY: newlines normalised, footer excluded."""
    raw = pathlib.Path(path).read_bytes()
    text = raw.decode("utf-8", "replace").replace("\r\n", "\n").replace("\r", "\n")
    cut = text.find(FOOTER_MARK)
    if cut != -1:
        text = text[:cut]
    return hashlib.sha256(text.rstrip().encode("utf-8")).hexdigest()


def sqls():
    out = []
    for f in sorted(ROOT.rglob("*.sql")):
        rel = f.relative_to(ROOT).as_posix()
        if any(d in rel for d in SKIP_DIRS):
            continue
        out.append((rel, f))
    return out


FOOTER = FOOTER_MARK + """
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
--     python tools/migrations.py --footer %s %s

insert into public.schema_migrations
  (filename, applied_at, checksum, source, outcome, evidence, note)
values ('%s', now(), '%s', 'recorded', 'applied', '%s', null);
"""


def footer(target, clu="CLU-???"):
    p = ROOT / target
    if not p.exists():
        p = pathlib.Path(target)
    if not p.exists():
        print("no such file: %s" % target)
        return 1
    rel = p.resolve().relative_to(ROOT).as_posix() if ROOT in p.resolve().parents else p.name
    print(FOOTER % (p.name, clu, rel, digest(p), clu))
    print("-- Paste that INSIDE the file's begin/commit, as its last statement.")
    print("--")
    print("-- The filename recorded is PATH-QUALIFIED (%r) so it joins against" % rel)
    print("-- `python tools/migrations.py`, which lists files by path. Bare")
    print("-- basenames do not: several .sql files live outside the repo root,")
    print("-- and a basename cannot tell two of them apart.")
    return 0


VERIFY = """-- Read-only. Run in the Supabase SQL editor and paste the output back.
-- Nothing here writes.

-- 1. what the database says has run, most recent first.
--    `how_sure` is the column to read second. Three backfilled rows have no
--    run record at all and are marked outcome='unknown'; two more rest on a
--    commit hash rather than a confirmation. Without this column the outcome
--    reads as fact for all eighteen.
select filename, applied_at, outcome, source,
       case
         when source = 'recorded'     then 'observed at run time'
         when evidence is null        then 'NO EVIDENCE — inferred only'
         when evidence like 'commit%' then 'commit only, no run record'
         else 'board-confirmed: ' || evidence
       end as how_sure,
       coalesce(left(checksum, 12), '(none)') as checksum
from public.schema_migrations
order by applied_at desc, id desc;

-- 2. anything recorded more than once — a re-run, which is worth seeing
select filename, count(*) as runs,
       count(*) filter (where outcome = 'failed') as failures
from public.schema_migrations
group by filename having count(*) > 1
order by filename;

-- 3. the repo's current checksums, for comparison with column `checksum` above.
--    A row whose checksum differs from the value here means the FILE has been
--    edited since it ran. That is not automatically wrong — several headers
--    have been corrected deliberately — but it does mean the file in front of
--    you is not the one that was executed.
--
--    Backfilled rows carry no checksum at all: nobody knows the bytes that ran.
__REPO_CHECKSUMS__
"""


def verify():
    rows = ["--    %-42s %s" % (rel, digest(f)) for rel, f in sqls()]
    # .replace, not %-formatting: the SQL above legitimately contains
    # `like 'commit%'`, and % -formatting chokes on it.
    print(VERIFY.replace("__REPO_CHECKSUMS__", "\n".join(rows)))
    return 0


def listing():
    print("%-44s %s" % ("file", "sha256 (newline-normalised)"))
    print("-" * 78)
    for rel, f in sqls():
        print("%-44s %s" % (rel, digest(f)[:32]))
    print("\n%d files. The database's own record is public.schema_migrations;" % len(sqls()))
    print("`--verify` prints the read-only query that compares the two.")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(listing())
    if a[0] == "--verify":
        sys.exit(verify())
    if a[0] == "--footer" and len(a) > 1:
        sys.exit(footer(a[1], a[2] if len(a) > 2 else "CLU-???"))
    print(__doc__)
    sys.exit(2)
