#!/usr/bin/env python3
"""Generate properties/jojo.json — the David Production anime, part by part.

    python3 tools/make_jojo.py

One row per episode, 202 rows across seven parts, one section per part.
Phantom Blood and Battle Tendency share the 2012 season, so their rows keep
that season's continuous numbering (1-9 and 10-26); every later part was
broadcast with its own count and numbers from 1. A note places all seven in
the overall numbering.

Episode titles are machine-read from the six Wikipedia season articles by
scratch/jojo/fetch_episodes.py, which asserts every part's numbering complete
and normalises it to the overall 1-202; the committed result is
tools/data/jojo.json. Dual-titled rows keep the original broadcast title, not
the localized rename that dodges the music trademarks.

Steel Ball Run (overall 191-) is still airing, weekly on Netflix. Its rows
carry their air date from the source, and the fetch step checks the titled
ones against the article's own infobox count. Every episode the source dates
is listed; one that has not aired by AS_OF says "airs <day>" and, until the
source titles it, is numbered "Episode N" rather than named. AS_OF is frozen
rather than read from the clock so two runs on different days agree; the
weekly bump is: refetch sbr, move AS_OF and the sbr range below, rerun.

Nothing is weighted: equal marks, and the part boundaries in the strip do the
rest. That includes the episodes still to come. A `w: 0` on those alone would
make the page treat the list as weighted and print "Time left 0m · 4 of 202
timed" over 198 invented hours, so they carry no `w`, like every other row and
like the other unweighted airing lists (lanterns, president-curtis).
"""
import json
import pathlib
from datetime import date

SLUG = "jojo"

# the day this list's aired/upcoming split was read; see the docstring
AS_OF = date(2026, 11, 11)

# key, title, years — key order is watch order
PARTS = [
    ("pb", "Phantom Blood", "2012"),
    ("bt", "Battle Tendency", "2012–13"),
    ("sc", "Stardust Crusaders", "2014–15"),
    ("diu", "Diamond Is Unbreakable", "2016"),
    ("gw", "Golden Wind", "2018–19"),
    ("so", "Stone Ocean", "2021–22"),
    ("sbr", "Steel Ball Run", "2026–"),
]

# where each part sits in the overall numbering; pb/bt display these numbers
# because they are one 2012 season, later parts display theirs from 1
OVERALL = {"pb": (1, 9), "bt": (10, 26), "sc": (27, 74),
           "diu": (75, 113), "gw": (114, 152), "so": (153, 190),
           "sbr": (191, 202)}

MONTHS = ("January February March April May June July August September "
          "October November December").split()


def daymonth(d):
    return "%d %s" % (d.day, MONTHS[d.month - 1])


def main():
    data = json.loads((pathlib.Path(__file__).resolve().parent / "data"
                       / "jojo.json").read_text(encoding="utf-8"))

    sections = []
    upcoming = []
    for key, title, years in PARTS:
        lo, hi = OVERALL[key]
        eps = data[key]
        assert [x["o"] for x in eps] == list(range(lo, hi + 1)), \
            "%s: expected overall %d-%d, got %d rows" % (key, lo, hi, len(eps))
        shown = (lambda o: o) if key in ("pb", "bt") else (lambda o: o - lo + 1)
        items = []
        for x in eps:
            row = {"id": "jojo-%s-%d" % (key, shown(x["o"])),
                   "t": x["t"], "n": str(shown(x["o"]))}
            if key == "sbr":
                airs = date.fromisoformat(x["d"])
                if airs <= AS_OF:
                    # an aired episode with no title is a parser failure
                    assert x["t"], "sbr %d aired %s untitled" % (x["o"], airs)
                else:
                    row["t"] = x["t"] or "Episode %s" % row["n"]
                    row["note"] = "airs %s" % daymonth(airs)
                    upcoming.append((row, bool(x["t"])))
            else:
                assert x["t"] and "d" not in x, x
            items.append(row)
        sec = {"id": key, "title": title,
               "sub": "%s · %d episodes" % (years, len(items)),
               "items": items}
        if key == "pb":
            sec["open"] = True
        if key == "bt":
            sec["intro"] = ("The back half of the 2012 season — the "
                            "numbering carries straight on from Phantom "
                            "Blood.")
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == 202, len(ids)
    counts = {s["id"]: len(s["items"]) for s in sections}
    assert counts == {"pb": 9, "bt": 17, "sc": 48, "diu": 39, "gw": 39,
                      "so": 38, "sbr": 12}, counts
    # the "still airing" copy below is only true while something is to come;
    # once every dated episode is out, this stops and the copy gets rewritten
    assert upcoming, "every Steel Ball Run episode has aired: rewrite the notes"
    untitled = sum(1 for _, titled in upcoming if not titled)

    prop = {
        "slug": SLUG,
        "title": "JoJo's Bizarre Adventure",
        "subtitle": "every episode of the David Production anime",
        "kind": "anime",
        "popularity": 71,
        "year": "2012–",
        "blurb": "All %d episodes of the David Production anime in order — "
                 "seven parts, seven JoJos, one bloodline, still airing."
                 % len(ids),
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#7A2E5F",
        "accentDark": "#E080BF",
        "tiers": False,
        "notes": [
            ["Each part stands on the last but tells its own story.",
             "A new JoJo, a new era and a mostly new cast every time; "
             "earlier parts pay off later, but every part opens fresh, and "
             "a part boundary is a clean place to pause."],
            ["Where each part sits in the overall numbering.",
             "Phantom Blood is episodes 1–9 and Battle Tendency 10–26 — one "
             "2012 season split between them, so their rows keep that "
             "numbering; Stardust Crusaders runs 27–74, Diamond Is "
             "Unbreakable 75–113, Golden Wind 114–152, Stone Ocean 153–190 "
             "and Steel Ball Run from 191, each numbered from 1 as "
             "broadcast."],
            ["Steel Ball Run is still airing.",
             "A new episode reaches Netflix each Friday. The %d dated ones "
             "still to come carry the day they air%s."
             % (len(upcoming),
                ", and are numbered rather than named until titles are "
                "published" if untitled == len(upcoming) else
                "; %d of them are numbered rather than named until a title "
                "is published" % untitled if untitled else "")],
            ["The manga continues past the anime.",
             "It carries on with JoJolion and The JoJoLands, and has a list "
             "of its own."],
            "Episode titles machine-read from the six Wikipedia season "
            "articles; every part's numbering is asserted complete, and "
            "Steel Ball Run's aired count checked against its article's "
            "own infobox, before this builds. Where a release renamed an "
            "episode to dodge a music trademark, the broadcast title stays.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json — %d episodes in %d parts"
          % (SLUG, len(ids), len(sections)))
    for s in sections:
        print("   %-24s %3d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
