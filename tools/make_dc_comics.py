"""Build properties/dc-comics.json — the DC shelf, one row per reading order.

CLU-449, and the companion to tools/make_marvel_comics.py (CLU-480). A MEGA
LIST: every row carries `into: "<slug>"` pointing at a DC reading order that
already exists as its own property, which is what makes the build flag the page
`_hub`, and a hub gets `mega: true` in the manifest for free. Nothing declares
`mega` here — two sources for one fact is how the two come to disagree.

NOTHING IS TYPED BY HAND except the section prose and which slugs belong. The
titles, the year ranges, the counts and this list's own year span are read back
out of the target files, because a hand-written count rots the day a list gains
an issue.

WHY THE STRIP IS WEIGHTED IN ISSUES (CLU-555, following CLU-545). Nathan's
umbrella ruling is that comics count in issues, "not collected volumes", and
CLU-545 applied that to the weight as well as to the row across the Marvel
side. This is the DC half, and it had to be one pass rather than five: a door's
weight is not typed here, it is the SUM of its target's row weights, computed
by build.py and only when every row of that target carries one. So weighting
some of these lists and not others produces exactly the mix build.py refuses -

    "A weighted strip cannot carry an unweighted row - it would draw as a
     default-sized mark beside a real one."

- and the shelf fails to build. All eight doors or none; there is no half.

THE ONE THAT MADE IT HARD. Seven of the eight tick issue by issue, so a row
weighs one and the weight restates a number the page already showed. `vertigo`
ticks by COLLECTED VOLUME, because a volume is what you finish there, and
weighing a volume one would have drawn that door as 29 beside Sandman's 88 for
a shelf more than twice Sandman's size. It is fixed at the source rather than
here: each Vertigo row now weighs the comics its volume collects, read off that
volume's own contents cell, and the page declares `weightUnit` so it can say a
tick is a book while a mark is issues. Nothing on this shelf reconciles units,
because by the time a door is read there is only one.

WHAT IS NOT HERE AND WHY. `hellboy` is Dark Horse and `spawn` is Image, so
neither is DC however comics-shaped it looks. `dc-anthology` and `dc-animation`
are screen lists, not comics, and they are flat release-order lists rather than
hubs of doors — so this is not a third copy of either.
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
# helps a reader choose: a route through a character with no single run, one
# author's stretch on one book, a crossover read interleaved, and the
# creator-owned imprint are four different commitments rather than four sizes
# of one.
SECTIONS = [
    ("route", "Where to start with a character",
     "Neither of these two has a run to read front to back — decades of it, "
     "several reboots, and two flagship titles running in parallel the whole "
     "time — so the way in is a house pick of the runs worth the time, in "
     "publication order, an issue to a row. Each page says on itself where it "
     "starts, where it stops and what it leaves out.",
     ["batman", "superman"]),
    ("runs", "One author, one long run",
     "A single writer's stretch on one book, from their first issue to their "
     "last, with what was collected alongside it. Both are post-Crisis "
     "continuity and both say so on their own page.",
     ["jla-morrison", "green-lantern"]),
    ("crossovers", "The line-wide crossovers",
     "An event running through a dozen titles at once, with the tie-ins "
     "interleaved in order rather than assumed. This is the shape a reading "
     "order exists for.",
     ["crisis-on-infinite-earths", "death-of-superman"]),
    ("imprint", "The creator-owned shelf",
     "DC away from the superhero line: one series taken issue by issue, and "
     "three more tracked by the volumes they were collected in.",
     ["sandman", "vertigo"]),
]

# Every comics list on the site is either a door above or named here with the
# publisher that makes it ineligible. Nothing is allowed to be neither, because
# the first draft of this file quietly omitted `jla-morrison` and the only thing
# that noticed was a row count read by eye. A new comics list now stops the
# generator until somebody decides which side of the line it is on.
NOT_DC = {
    "marvel-comics": "Marvel — and the shelf this one mirrors",
    "amazing-spider-man": "Marvel",
    "black-panther": "Marvel",
    "captain-america": "Marvel",
    "cates-venom": "Marvel",
    "civil-war": "Marvel",
    "daredevil": "Marvel",
    "fantastic-four": "Marvel",
    "hickman-secret-wars": "Marvel",
    "spider-man-after-civil-war": "Marvel",
    "thor": "Marvel",
    "ultimate-marvel": "Marvel",
    "x-men": "Marvel",
    "wolverine": "Marvel",
    "hellboy": "Dark Horse",
    "spawn": "Image",
}


WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
         7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven",
         12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen",
         16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen",
         20: "twenty"}

YEAR = re.compile(r"\b(?:18|19|20)\d{2}\b")


def read(slug):
    f = PROPS / (slug + ".json")
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def facts(slug):
    """Everything the row says, read out of the target itself."""
    d = read(slug)
    if d is None:
        return None
    items = [x for sec in d["sections"] for x in sec["items"]]
    # Assert the premise this whole list rests on rather than trusting it. It
    # is the exact inverse of what it used to be: an UNWEIGHTED DC list
    # appearing later turns the strip into the mix build.py refuses, and the
    # generator should be where that is discovered rather than the build.
    # `opt` rows count too — build.py totals a weight only when every row of
    # the target has one, optional included.
    bare = [x["id"] for x in items
            if not isinstance(x.get("w"), (int, float))
            or isinstance(x.get("w"), bool)]
    assert not bare, \
        "%s leaves %d row(s) unweighted (%s ...) — a door into it would " \
        "derive no weight and the strip could no longer carry the weighted " \
        "ones" % (slug, len(bare), ", ".join(bare[:3]))
    core = [x for x in items if not x.get("opt")]
    nopt = len(items) - len(core)
    unit = (d.get("unit") or {}).get("many", "entries")
    note = ("%d %s" % (len(core), unit) if not nopt
            else "%d + %d optional" % (len(core), nopt))
    # How wide this door will be drawn, which is not always the row count. A
    # list that ticks in one unit and measures in another says so with
    # `weightUnit`, and then the row has to print both or the mark looks wrong
    # beside the count. Derived from the same rows build.py will sum.
    wtotal = int(sum(x["w"] for x in items))
    wunit = (d.get("weightUnit") or {}).get("many")
    if wunit:
        note += " · %d %s" % (wtotal, wunit)
    span = (d.get("year") or "").strip()
    years = [int(y) for y in YEAR.findall(span)]
    return {"title": d["title"], "n": span, "note": note, "unit": unit,
            "w": wtotal,
            "first": years[0] if years else 9999,
            "last": years[-1] if years else 0,
            # "1985–" means still running, and the shelf's own span has to stay
            # open if any door behind it is
            "open": bool(re.search(r"[–-]\s*$", span))}


def audit_the_catalogue(mine):
    """Refuse to run while any comics list is neither a door nor excluded."""
    comics = set()
    for f in sorted(PROPS.glob("*.json")):
        if f.name in ("index.json", "search.json"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("kind") == "comics" and d.get("slug") != "dc-comics":
            comics.add(d["slug"])
    loose = sorted(comics - set(mine) - set(NOT_DC))
    if loose:
        raise SystemExit(
            "comics list(s) accounted for nowhere: %s — put each on the shelf "
            "or in NOT_DC with its publisher" % ", ".join(loose))
    stale = sorted((set(mine) | set(NOT_DC)) - comics)
    if stale:
        raise SystemExit("named here but not a comics list any more: %s"
                         % ", ".join(stale))


def main():
    rows_by_sec, missing, total = [], [], 0
    allf = []
    audit_the_catalogue([s for _, _, _, ss in SECTIONS for s in ss])
    for sid, stitle, sub, slugs in SECTIONS:
        items = []
        for slug in slugs:
            f = facts(slug)
            if f is None:
                missing.append(slug)
                continue
            total += 1
            allf.append(f)
            items.append({
                # permanent, and deliberately the target's own slug: an id
                # derived from a title would move the day a list is retitled,
                # and a moved id destroys everyone's ticks
                "id": "dcc-" + slug,
                "t": f["title"],
                "n": f["n"],
                "note": f["note"],
                "into": slug,
            })
        items.sort(key=lambda x: facts(x["into"])["first"])
        rows_by_sec.append((sid, stitle, sub, items))

    if missing:
        raise SystemExit("no property file for: %s" % ", ".join(missing))

    # The shelf's span is the union of the spans behind it, so it cannot
    # disagree with them the way a typed range would.
    span = "%d–%s" % (min(f["first"] for f in allf),
                      "" if any(f["open"] for f in allf)
                      else max(f["last"] for f in allf))

    # The mixed-unit note counts its own examples: CLU-449's first decision is
    # that these lists disagree about what a row is, and a hand-typed "five"
    # would be wrong the first time a volumes-counting list joins the shelf.
    nissues = sum(1 for f in allf if f["unit"] == "issues")

    # What the whole shelf weighs, summed from the doors rather than typed —
    # the same numbers build.py will put on the marks.
    wall = sum(f["w"] for f in allf)

    prop = {
        "slug": "dc-comics",
        "title": "DC Comics",
        "subtitle": "%d reading orders" % total,
        "kind": "comics",
        "year": span,
        # POPULARITY.md, the 80-89 band: "very widely known; a mainstream
        # audience recognises the title on sight". Two below Marvel Comics at
        # 90 on signal 1 — both names travel far outside comics, Marvel's
        # slightly further today — and above every list this opens, the highest
        # of which is Batman at 72. It also sits above DC Anthology at 82,
        # which is the reverse of the Marvel shelf sitting below the MCU: the
        # MCU is the better-known door into Marvel, while DC Anthology is a
        # complete live-action survey back to 1951 rather than one famous
        # series, and is scored as one.
        "popularity": 88,
        "unit": {"one": "reading order", "many": "reading orders"},
        # without this the stats bar falls back to the literal "Done"; every
        # row is a body of comics, so the honest past tense is "read"
        "verb": {"base": "read", "ing": "reading", "past": "read"},
        "accent": "#0A50C8",
        "accentDark": "#7AA9FF",
        # spelled rather than printed as a digit: a blurb is prose and
        # "7 DC reading orders" reads as a table cell. Derived either way,
        # so the sentence still cannot disagree with the shelf.
        "blurb": "%s DC reading orders as one list. Each row opens that "
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
            ["A mark's width is issues, not hours.",
             "Comics publish no per-issue reading time, so there are no hours "
             "to size a mark with — but there are issues, and every list "
             "behind this page counts in them. Each door is drawn as wide as "
             "the number of issues in the order it opens, so the longest of "
             "these and the shortest are not the same size on the bar. All "
             "eight together are %d issues, which is what finishing this "
             "page means." % wall],
            # Batman used to be the second exception here — it counted
            # collected stories — and the umbrella ruling of 2026-09-11 made
            # every comics list count issues, so the only page left out of step
            # is the Vertigo shelf. The count is derived, so the sentence
            # cannot disagree with the shelf when that changes again.
            ["The rows do not all count the same thing. The marks do.",
             "%s of these pages tick issue by issue; the Vertigo shelf ticks "
             "by collected volume, because a volume is what you actually "
             "finish there. That disagreement is real and it stays on each "
             "page, where each says which unit it uses and why. The bars are "
             "another matter — every door here is measured in issues, "
             "Vertigo's included, so nothing on this page has to reconcile "
             "anything."
             % WORDS.get(nissues, str(nissues)).capitalize()],
            ["DC on screen is a different shelf.",
             "The films and television are already covered by DC Anthology "
             "and DC Animation, which are release-order surveys of the screen "
             "rather than reading orders. This page is only the comics, and "
             "nothing here opens either of those."],
            ["Two comics lists on the site are deliberately absent.",
             "Hellboy is Dark Horse and Spawn is Image. Both are on clubd and "
             "neither is DC, so neither belongs on a DC shelf however much it "
             "looks like one from the outside."],
            ["DC is bigger than this.",
             "There is no Wonder Woman here, no Flash, no Swamp Thing, no "
             "Starman, no Kingdom Come. Every row on this page "
             "is a list that already exists; the rest are written down as work "
             "still to do, and each will get a row here once it is built "
             "rather than a promise of one now."],
            # Unheaded, last: the colophon (CLU-275 rule 6). A hub's provenance
            # is unusual — it has no sources of its own, only the lists
            # behind it — so the note says that rather than naming a wiki this
            # page never read.
            "Every row is read out of the list it opens. The title, the years "
            "and the count on each row are taken from that list's own file "
            "when the page is built, so nothing here can drift from the page "
            "behind it, and none of it was typed in. The sources are on those "
            "%s pages, each naming its own. What is a judgement, and mine, "
            "is which reading orders belong on a DC shelf and how they are "
            "grouped." % WORDS.get(total, str(total)),
        ],
        "sections": [
            {"id": sid, "title": stitle, "sub": sub, "items": items}
            for sid, stitle, sub, items in rows_by_sec
        ],
    }

    out = P.write(prop)
    print("wrote %s — %d rows across %d sections, span %s, %d issues"
          % (out.name, total, len(rows_by_sec), span, wall))
    for sid, stitle, sub, items in rows_by_sec:
        print("  %-30s %d  %s" % (stitle[:30], len(items),
                                  ", ".join(x["into"] for x in items)))


if __name__ == "__main__":
    main()
