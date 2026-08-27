"""Where does the LIVE definition of a database object live? (CLU-374)

WHY THIS EXISTS

`schema.sql` is what anything reasoning about this database reads, and its
functions and policies are behind reality. That is not cosmetic — it caused the
two worst near-misses in the project:

  * A migration replaced `join_group()` with a body copied out of `schema.sql`,
    silently deleting `guard_group_join_rate()` and the whole brute-force cap on
    club codes. An auditor caught it; nothing in the file did.
  * A decision document quoted `schema.sql` to argue the database "has never
    known that list is special", and recommended building a table that already
    existed.

Both are the same mistake: reading a RECORDED state instead of the live one,
from a file that did not say it was stale.

WHAT THIS DOES

Scans every .sql in the repo and reports, for each object, EVERY file that
defines it — ordered by when those files were applied. The point is not to pick
a winner automatically; it is to make MULTIPLICITY VISIBLE. An object defined in
five files is a trap, and the trap is otherwise invisible.

    python tools/whereis.py                 # the whole map
    python tools/whereis.py join_group      # one object

It cannot see the live database and it does not pretend to. It tells you which
files to read. For what actually RAN, ask the database itself —
`python tools/migrations.py --verify` — or read DATABASE.md §5.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

# What actually ran against production, oldest first.
#
# This list is now the WEAKEST of the three records, and should be treated that
# way. Since 2026-08-27 the database keeps its own — `public.schema_migrations`
# (CLU-404) — and `python tools/migrations.py --verify` reads it back. The order
# of authority is: the ledger, then DATABASE.md §5, then this. It survives
# because this tool must work without a database connection.
APPLIED = [
    "schema.sql",
    "migrate-to-multiproperty.sql",
    "migrate-add-friends.sql",
    "migrate-add-friend-privacy.sql",
    "migrate-add-friend-decline.sql",
    "migrate-add-friend-shelves.sql",
    "migrate-add-join-or-create.sql",
    "migrate-add-owner-removal.sql",
    "migrate-add-schedule-start.sql",
    "migrate-add-thumbs.sql",
    "migrate-add-thumbs-friends-policy.sql",   # split out of the above, 2026-08-27
    "migrate-add-tick-events.sql",
    "migrate-add-rate-limits.sql",
    "rls-fix-PART1-safe-now.sql",
    "FINAL-1-rls-locks.sql",
    "FINAL-2-privacy.sql",
    "migrate-groups.sql",
    "migrate-mute-privacy.sql",
    "migrate-group-thumbs.sql",
    "migrate-add-schema-ledger.sql",
]

# Written, never executed. Keeping these OUT of the applied list matters: while
# they sat in it, this tool labelled `find_profile_by_code` "LATEST APPLIED"
# from FINAL-3, a file that has never run — so an object that does not exist in
# the database was reported as its live definition.
NEVER_RUN = {
    "FINAL-3-profiles.sql":            "fenced on a front-end change that has not shipped",
    "rls-fix-PART2-after-frontend.sql": "same fence, superseded by FINAL-3, no transaction",
    "migrate-fix-rls-column-locks.sql": "PART1 and PART2 concatenated; never ran as itself",
    "migrate-perf-shares.sql":          "MUST NEVER RUN — silently replaces a live function",
}

DEFS = [
    (re.compile(r"create\s+(?:or\s+replace\s+)?function\s+(?:public\.)?(\w+)", re.I), "function"),
    (re.compile(r"create\s+policy\s+\"([^\"]+)\"", re.I), "policy"),
    (re.compile(r"create\s+table\s+(?:if\s+not\s+exists\s+)?(?:public\.)?(\w+)", re.I), "table"),
    (re.compile(r"create\s+trigger\s+(\w+)", re.I), "trigger"),
]


def rank(name):
    """Applied position. Never-run and unknown files sort BELOW everything
    applied, so they can never be reported as the live definition."""
    if name in NEVER_RUN:
        return -2
    return APPLIED.index(name) if name in APPLIED else -1


def label(path, i):
    base = pathlib.Path(path).name
    if base in NEVER_RUN:
        return "NEVER RUN"
    if base not in APPLIED:
        return "unknown order"
    return "LATEST APPLIED" if i == 0 else "superseded"


def scan():
    """Everything, including superseded/ — deliberately.

    An earlier comment here claimed superseded/ was skipped and the code never
    skipped it. Scanning it is the right behaviour: a retired file that still
    defines a live object is exactly the multiplicity this tool exists to show.
    Only the agent worktrees are excluded, because they are stale copies of
    these same files and would triple every count.
    """
    found = {}
    for f in sorted(ROOT.rglob("*.sql")):
        rel = f.relative_to(ROOT).as_posix()
        # worktrees are stale copies and would triple every count;
        # moved-to-repo holds the pre-move originals of files that now live at
        # the root, so counting both would invent a multiplicity that is not real
        if ".claude/worktrees" in rel or "moved-to-repo" in rel:
            continue
        try:
            body = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        # comments describe objects constantly; only real statements count
        code = "\n".join(l for l in body.split("\n")
                         if not l.strip().startswith("--"))
        for pat, kind in DEFS:
            for m in pat.finditer(code):
                found.setdefault((kind, m.group(1)), set()).add(rel)
    return found


def show(found, only=None):
    rows = sorted(found.items(), key=lambda kv: (kv[0][0], kv[0][1]))
    hits = 0
    for (kind, name), files in rows:
        if only and only.lower() not in name.lower():
            continue
        hits += 1
        ordered = sorted(files, key=lambda p: -rank(pathlib.Path(p).name))
        live = [p for p in ordered if pathlib.Path(p).name in APPLIED]
        flag = "  <-- %d COPIES" % len(files) if len(files) > 1 else ""
        print("\n%-8s %s%s" % (kind, name, flag))
        for i, p in enumerate(ordered):
            print("    %-14s %s" % (label(p, i), p))
        if not live:
            print("    ** no applied file defines this — it is not in the database **")
    if only and not hits:
        print("nothing named %r defines an object in any .sql here" % only)
    return rows


if __name__ == "__main__":
    found = scan()
    only = sys.argv[1] if len(sys.argv) > 1 else None
    rows = show(found, only)
    if not only:
        multi = [k for k, v in found.items() if len(v) > 1]
        ghost = [k for k, v in found.items()
                 if not any(pathlib.Path(p).name in APPLIED for p in v)]
        print("\n" + "=" * 68)
        print("%d objects, %d defined in more than one file." % (len(found), len(multi)))
        print("A repeated object is a trap: whichever file runs LAST wins, no")
        print("error is raised, and whatever the loser carried disappears.")
        if ghost:
            print("\n%d object(s) are defined ONLY by files that never ran, so they"
                  % len(ghost))
            print("do not exist in the database:")
            for kind, name in sorted(ghost):
                print("    %-8s %s" % (kind, name))
        print("\nThis reads FILES, not the database. DATABASE.md is the record of")
        print("what actually ran.")
