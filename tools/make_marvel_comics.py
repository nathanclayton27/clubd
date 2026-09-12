"""Build properties/marvel-comics.json — the Marvel shelf, one row per order.

CLU-480 / CLU-508. A MEGA LIST: every row carries `into: "<slug>"` pointing at
a Marvel reading order that already exists as its own property, which is what
makes the build flag the page `_hub`, and a hub gets `mega: true` in the
manifest for free. Nothing declares `mega` here — two sources for one fact is
how the two come to disagree.

NOTHING IS TYPED BY HAND except the section prose and which slugs belong. The
titles, the year ranges and the counts are read back out of the target files,
because a hand-written count rots the day a list gains an issue.

WHY THE STRIP IS UNWEIGHTED, and why three Marvel lists are missing from it.
Nathan, CLU-508: "drawing the line based on hours where we can and defaulting
to items per otherwise is fine. like for comics the amount of items checked
works." Comics publish no per-issue reading time, so every door here counts
one and the marks are equal width.

That is also a constraint rather than only a choice. `amazing-spider-man`,
`x-men` and `civil-war` are the three older Marvel lists that weight every row
with an ISSUE COUNT (`w: 6` on a `#1-6` row), so build.py derives a real weight
for a door into them — and it then refuses, correctly, to draw a measured mark
beside an unmeasured one:

    "A weighted strip cannot carry an unweighted row - it would draw as a
     default-sized mark beside a real one."

So they cannot sit on this shelf until the twelve lists agree on one unit.
Leaving them off is the smaller lie: the shelf says nine and holds nine.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop as P  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROPS = ROOT / "properties"

# Grouped by what KIND of reading order it is, which is the only grouping that
# helps a reader choose: a character spine, an event, a single run and a
# separate universe are four different commitments, not four sizes of one.
SECTIONS = [
    ("characters", "The character spines",
     "One character or team from the first appearance forward, across every "
     "title they carried. The longest reads on the shelf.",
     ["fantastic-four", "thor", "captain-america", "black-panther",
      "daredevil"]),
    ("runs", "Runs and events",
     "One author, one stretch of a single title, or one crossover with its "
     "tie-ins in order rather than assumed.",
     ["hickman-secret-wars", "cates-venom", "spider-man-after-civil-war"]),
    ("elsewhere", "A universe of its own",
     "Marvel outside main continuity, complete.",
     ["ultimate-marvel"]),
]


WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
         7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven",
         12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen",
         16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen",
         20: "twenty"}


def read(slug):
    f = PROPS / (slug + ".json")
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def facts(slug):
    """Everything the row says, read out of the target itself."""
    d = read(slug)
    if d is None:
        return None
    items = [x for sec in d["sections"] for x in sec["items"]]
    core = [x for x in items if not x.get("opt")]
    nopt = len(items) - len(core)
    unit = (d.get("unit") or {}).get("many", "entries")
    note = ("%d %s" % (len(core), unit) if not nopt
            else "%d + %d optional" % (len(core), nopt))
    span = (d.get("year") or "").strip()
    m = re.search(r"\b(?:18|19|20)\d{2}\b", span)
    return {"title": d["title"], "n": span, "note": note,
            "first": int(m.group(0)) if m else 9999}


def main():
    rows_by_sec, missing, total = [], [], 0
    for sid, stitle, sub, slugs in SECTIONS:
        items = []
        for slug in slugs:
            f = facts(slug)
            if f is None:
                missing.append(slug)
                continue
            total += 1
            items.append({
                # permanent, and deliberately the target's own slug: an id
                # derived from a title would move the day a list is retitled,
                # and a moved id destroys everyone's ticks
                "id": "mvc-" + slug,
                "t": f["title"],
                "n": f["n"],
                "note": f["note"],
                "into": slug,
            })
        items.sort(key=lambda x: facts(x["into"])["first"])
        rows_by_sec.append((sid, stitle, sub, items))

    if missing:
        raise SystemExit("no property file for: %s" % ", ".join(missing))

    prop = {
        "slug": "marvel-comics",
        "title": "Marvel Comics",
        "subtitle": "%d reading orders" % total,
        "kind": "comics",
        "year": "1941–",
        # POPULARITY.md, the 90-100 band: "household name well outside its own
        # audience". Marvel Comics is, and a hub should sit above the lists it
        # opens rather than below them — Amazing Spider-Man is 87, X-Men 86.
        # Below the MCU at 95, because the films are the better-known door in.
        "popularity": 90,
        "unit": {"one": "reading order", "many": "reading orders"},
        # without this the stats bar falls back to the literal "Done"; every
        # row is a body of comics, so the honest past tense is "read"
        "verb": {"base": "read", "ing": "reading", "past": "read"},
        "accent": "#B32024",
        "accentDark": "#F0565A",
        # spelled rather than printed as a digit: a blurb is prose and
        # "9 Marvel reading orders" reads as a table cell. Derived either way,
        # so the sentence still cannot disagree with the shelf.
        "blurb": "%s Marvel reading orders as one list. Each row opens that "
                 "order's own page, and finishing that page ticks the row "
                 "here." % WORDS.get(total, str(total)).capitalize(),
        "notes": [
            ["Every row is a door.",
             "Hover a row and a loupe appears with a fraction beside it — how "
             "far into that reading order you already are. Opening it takes "
             "you to its own page, an ordinary list with its own strip, its "
             "own schedule and its own clubs. Nothing about it changes "
             "because it is reachable from here."],
            ["Ticking works in both directions.",
             "Marking a row here ticks that whole order, and finishing that "
             "order marks the row here. Unticking a row only takes back the "
             "ticks this page put there — anything you had already marked "
             "yourself stays marked."],
            ["Every mark is the same width, and that is deliberate.",
             "Comics publish no per-issue reading time, so there are no hours "
             "to size a mark with. Each door counts one, which makes this "
             "page read as a shelf of reading orders rather than as several "
             "thousand issues. The issue count sits on each row instead, "
             "where it is a fact rather than a guess at how long you will be."],
            ["Three Marvel lists on the site are not here yet.",
             "Amazing Spider-Man, X-Men and Civil War each weight every row "
             "with an issue count, and the nine here do not. A strip cannot "
             "honestly mix a measured mark with an unmeasured one — the "
             "unmeasured one would draw at a default size beside a real one — "
             "so the build refuses the mix, and they stay off until the "
             "twelve lists agree on one unit. Spider-Man is on the shelf as "
             "the list that continues him, not the one that starts him."],
            ["Where these overlap, and where they do not.",
             "Fantastic Four stops one issue short of Hickman, so it and "
             "Everything Dies meet without repeating a row. Spider-Man After "
             "Civil War starts where Amazing Spider-Man stops. An event list "
             "does cross several of these spines by design — that is what an "
             "event is — which is why ticking one list here never reaches "
             "into another."],
        ],
        "sections": [
            {"id": sid, "title": stitle, "sub": sub, "items": items}
            for sid, stitle, sub, items in rows_by_sec
        ],
    }

    out = P.write(prop)
    print("wrote %s — %d rows across %d sections"
          % (out.name, total, len(rows_by_sec)))
    for sid, stitle, sub, items in rows_by_sec:
        print("  %-28s %d" % (stitle[:28], len(items)))


if __name__ == "__main__":
    main()
