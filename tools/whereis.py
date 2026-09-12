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
    # migrate-add-friend-privacy.sql USED TO SIT HERE. It never ran, and
    # DATABASE.md §5 proves that rather than assuming it: the 2026-08-25
    # read-only pre-flight found `friend_may_read` absent (CLU-195), and this is
    # the file that would have created it. It is in NEVER_RUN below. (CLU-446)
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
    # Ran 2026-09-10 with a 19/19 readback (CLU-389), recorded in the ledger as
    # it happened. It lives in the gitignored scratch/security/ rather than at
    # the repo root — see DATABASE.md §3 for why it has not moved — and being
    # in that folder no longer implies unrun.
    #
    # ⚠ It was missing from this list for the rest of that day, and the CLU-153
    # audit caught it: without it this tool reports save_progress,
    # club_progress, arr_union, club_session_visible and the groups_fold_sessions
    # trigger as objects that do not exist, and DATABASE.md §2 tells you to run
    # this tool before every paste. A safety tool that names ten live objects as
    # missing is worse than no safety tool, because the reader trusts it.
    "migrate-club-progress.sql",
]

# Written, never executed. Keeping these OUT of the applied list matters: while
# they sat in it, this tool labelled `find_profile_by_code` "LATEST APPLIED"
# from FINAL-3, a file that has never run — so an object that does not exist in
# the database was reported as its live definition.
NEVER_RUN = {
    "FINAL-3-profiles.sql":            "superseded by the clu153 pair below; never ran",
    "rls-fix-PART2-after-frontend.sql": "same fence, superseded by FINAL-3, no transaction",
    "clu153-A-find_profile_by_code.sql": "queued (CLU-153): the lookup function, safe any time",
    "clu153-B-narrow-profiles.sql":     "queued (CLU-153): fenced until the front end is live",
    "migrate-fix-rls-column-locks.sql": "PART1 and PART2 concatenated; never ran as itself",
    "migrate-perf-shares.sql":          "MUST NEVER RUN — silently replaces a live function",
    # Was in APPLIED until CLU-446. All five objects it defines are also defined
    # by files that really did run, and none of them ranked to it, so it misled
    # nobody — but a never-run file sitting in the applied list is the exact
    # shape of CLU-374, and next time the object could be one only it defines.
    "migrate-add-friend-privacy.sql":   "never ran — the 2026-08-25 pre-flight found friend_may_read absent (CLU-195)",
    # Written and queued, then failed its own hostile audit on 2026-09-12: the
    # ledger row it writes would be false, and `save_progress` breaks the
    # invariant its column comment asserts. Not to be pasted in this form.
    "clu504-tombstones.sql":            "queued then held (CLU-504): the audit said DO NOT RUN in this form",
}

# Read-only harnesses. They define nothing and they may be run against
# production freely, so they belong in neither list above — but they have to be
# named somewhere, or the unclassified-file check below cries wolf every run.
READ_ONLY = {
    "verify-groups.sql":            "read-only harness for migrate-groups",
    "preflight-club-progress.sql":  "read-only pre-flight; ran twice, wrote nothing",
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


def scanned():
    """Every .sql this tool looks at, in one place, so the census and the
    unclassified-file check cannot disagree with the scan about what exists."""
    out = []
    for f in sorted(ROOT.rglob("*.sql")):
        rel = f.relative_to(ROOT).as_posix()
        if ".claude/worktrees" in rel or "moved-to-repo" in rel:
            continue
        out.append(rel)
    return out


def scan():
    """Everything, including superseded/ — deliberately.

    An earlier comment here claimed superseded/ was skipped and the code never
    skipped it. Scanning it is the right behaviour: a retired file that still
    defines a live object is exactly the multiplicity this tool exists to show.
    Only the agent worktrees are excluded, because they are stale copies of
    these same files and would triple every count.
    """
    found = {}
    # worktrees are stale copies and would triple every count; moved-to-repo
    # holds the pre-move originals of files that now live at the root, so
    # counting both would invent a multiplicity that is not real. Both
    # exclusions live in scanned(), which is the only traversal here.
    for rel in scanned():
        f = ROOT / rel
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
        files = sorted({p for v in found.values() for p in v})
        print("\n" + "=" * 68)
        print("CENSUS — read what this counts before quoting it (CLU-446).")
        print("%d object NAMES, defined across %d of this repo's %d .sql files:"
              % (len(found), len(files), len(scanned())))
        print("  %3d defined by at least one file recorded as applied" % (len(found) - len(ghost)))
        print("  %3d defined only by files that never ran — not in the database" % len(ghost))
        print("  %3d defined in more than one file" % len(multi))
        print("That is a count of DEFINITIONS IN FILES, and it is not comparable")
        print("to a count of live database objects: it includes superseded/ and")
        print("never-run files, counts a name once however many files carry it,")
        print("and sees no column, index, view or grant at all. DATABASE.md §4")
        print("catalogues what is live; this catalogues where definitions are.")
        print("A repeated object is a trap: whichever file runs LAST wins, no")
        print("error is raised, and whatever the loser carried disappears.")
        if ghost:
            print("\n%d object(s) are defined ONLY by files that never ran, so they"
                  % len(ghost))
            print("do not exist in the database:")
            for kind, name in sorted(ghost):
                print("    %-8s %s" % (kind, name))
        unclassified = [f for f in scanned()
                        if pathlib.Path(f).name not in APPLIED
                        and pathlib.Path(f).name not in NEVER_RUN
                        and pathlib.Path(f).name not in READ_ONLY]
        if unclassified:
            print("\n⚠ %d .sql file(s) are in none of this tool's three lists, so"
                  % len(unclassified))
            print("it does not know whether they ran. Any object they define is")
            print("labelled \"unknown order\". Classify them here and in DATABASE.md")
            print("§5 before leaning on anything above:")
            for f in unclassified:
                print("    %s" % f)

        # DATABASE.md quotes this census in prose, twice: §2's pre-flight step 2
        # and §7. That transcription is what went stale — it read "23 of 74" for
        # a fortnight after migrate-club-progress.sql added ten names, and the
        # memorable half of the sentence still matched, so nobody re-derived it.
        # Checked here rather than maintained by hand (CLU-446).
        doc = ROOT / "DATABASE.md"
        if doc.exists():
            quoted = re.findall(r"(\d+) of (\d+) objects", doc.read_text(encoding="utf-8"))
            want = (str(len(multi)), str(len(found)))
            stale = [q for q in quoted if q != want]
            print("")
            if not quoted:
                print("DATABASE.md quotes no census, so there is nothing to keep in step.")
            elif stale:
                print("⚠ DATABASE.md says %s where this scan says %s of %s."
                      % (", ".join("%s of %s" % q for q in stale), want[0], want[1]))
                print("  One of them is stale. This tool is the weakest record of what")
                print("  RAN — but of this count it is the only record there is, so the")
                print("  document is the side to correct. (CLU-446)")
            else:
                print("DATABASE.md quotes %s of %s in %d place(s), and agrees."
                      % (want[0], want[1], len(quoted)))

        print("\nThis reads FILES, not the database. For what actually RAN, ask")
        print("the database: python tools/migrations.py --verify")
