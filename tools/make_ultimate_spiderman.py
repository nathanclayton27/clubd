#!/usr/bin/env python3
"""Generate properties/ultimate-spider-man.json.

    python3 tools/make_ultimate_spiderman.py

PARKED - THIS SCRIPT REFUSES TO RUN (CLU-559). It is the only working draft of
the 2024 Ultimate Spider-Man list, which Nathan put on hold on 2026-08-21: that
list is not to be built until he gives instructions for it. properties/ has no
ultimate-spider-man.json, and src/build.py ships whatever is in properties/, so
one run would publish a 184-row list nobody reviewed. main() therefore exits
non-zero before writing anything; take that guard out only when he gives the
instructions. The ult2000 section below is superseded: the 2000 run lives in
the `ultimate-marvel` list, under its ids (u-ultimate-spider-man-N), and must
not come back here as ult00-N. The ult2024 section (Hickman, #1-24) is on no
list and exists only in this file. tools/gendrift.py records the script in
CANNOT_RUN.

Both Ultimate Spider-Man runs, which used to sit at the bottom of the
post-Civil War list. They are their own continuity twice over — the 2000 run
restarts the character from scratch outside the main line, and the 2024 run
restarts him again in a second, unrelated Ultimate universe — so neither
belongs under a heading about what happened after Civil War, and neither needs
a single issue of the main title to make sense.

Tracked issue by issue. Both runs are tier 1 because both are complete works
you either read or don't; there is no spine-and-optional split to make here.

Deliberately not included yet: Ultimate Comics Spider-Man (2009–2012), which
carries the line on with a different lead. Nathan said he would elaborate on
what he wants in this list, so this holds exactly what was moved out of the
other one rather than guessing at more.

Notes say what an entry is, never what happens in it.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from spiderman_data import S_ULT00, S_ULT24

SLUG = "ultimate-spider-man"


def run(prefix, title, nums, notes=None, stars=None):
    notes, stars, out = notes or {}, stars or {}, []
    for n in nums:
        x = {"id": "%s-%d" % (prefix, n), "t": title, "n": "#%d" % n}
        if n in notes:
            x["note"] = notes[n]
        if n in stars:
            x["star"] = stars[n]
        out.append(x)
    return out


SECTIONS = [
    {
        "id": "ult2000", "tier": 1, "title": "Ultimate Spider-Man (2000–09)",
        "sub": "#1–160 · Bendis and Bagley",
        "open": True,
        "links": [{"label": "The series", "url": S_ULT00}],
        "intro": "The original Ultimate line. Separate continuity, retells the "
                 "origin from the beginning, and then runs for eleven years "
                 "without a reboot — one of the great long runs in Marvel "
                 "history, and the longest single stretch of Spider-Man by one "
                 "creative team anywhere.\n\n"
                 "You need nothing else to read it.",
        "items": run("ult00", "Ultimate Spider-Man (2000)", range(1, 161),
                     notes={1: "The origin, from scratch"}, stars={1: 1}),
    },
    {
        "id": "ult2024", "tier": 1, "title": "Ultimate Spider-Man (2024–26)",
        "sub": "#1–24 · Hickman and Checchetto · finished",
        "links": [{"label": "The series", "url": S_ULT24}],
        "intro": "A second, unrelated Ultimate universe, twenty-odd years later. "
                 "Peter becomes Spider-Man in his mid-thirties, already married "
                 "with two kids. A complete, finished run — and it needs nothing "
                 "from the 2000 series above.",
        "items": run("ult24", "Ultimate Spider-Man (2024)", range(1, 25),
                     stars={1: 1}),
    },
]


def main():
    sys.exit("make_ultimate_spiderman.py is the parked draft of the 2024 "
             "Ultimate Spider-Man list and must not write properties/ until "
             "Nathan gives instructions for it (CLU-559). Nothing written.")
    ids = [x["id"] for s in SECTIONS for x in s["items"]]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate item ids")
    total = len(ids)
    assert total == 184, total
    unlinked = [s["title"] for s in SECTIONS if not s.get("links")]
    assert not unlinked, unlinked

    prop = {
        "slug": SLUG,
        "title": "Ultimate Spider-Man",
        "subtitle": "both runs, outside continuity",
        "kind": "comics",
        "popularity": 55,
        "year": "2000–2026",
        "blurb": "Two complete runs that restart the character from scratch — "
                 "%d issues, and no homework." % total,
        "unit": {"one": "issue", "many": "issues"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": "#1F6FA8",
        "accentDark": "#6BB8E8",
        "tiers": False,
        "notes": [
            ["No homework.", "Neither run needs anything from the main "
             "Spider-Man line, and the two do not need each other. They are "
             "separate continuities that happen to share a name — you can start "
             "with either."],
            ["Which to start with.", "The 2000 run if you want the long version: "
             "160 issues, one creative team, the origin told properly. The 2024 "
             "run if you want something finished in an afternoon or two."],
            ["No spoilers.", "The notes say what an entry is, never what happens "
             "in it."],
        ],
        "sections": SECTIONS,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    for s in SECTIONS:
        print("   %-34s %4d issues" % (s["title"][:34], len(s["items"])))
    print("  %d issues total" % total)


if __name__ == "__main__":
    main()
