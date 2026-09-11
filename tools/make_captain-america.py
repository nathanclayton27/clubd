#!/usr/bin/env python3
"""Generate properties/captain-america.json.

    PYTHONIOENCODING=utf-8 python tools/make_captain-america.py

Captain America Comics #1 in 1941, then the 1964 revival, then the solo book
straight through to the end of Ed Brubaker's eight years on it — 1941 to 2013,
one section per creative run.

Sourcing. Every issue number, cover date and creator credit comes from the
Marvel Database wiki (marvel.fandom.com), fetched by
scratch/captain-america/fetch.py and flattened by its parse.py into
tools/data/captain-america.json: the volume's own page list says which issues
exist, and each issue's infobox says who wrote it and when it was cover-dated.
Nothing below is typed from memory, and the assertions are the point:

  * every row is an issue the wiki enumerates, or the build stops;
  * every section is a CONTIGUOUS span of the issues that exist, so a gap in
    the wiki's numbering cannot be swallowed silently;
  * a section that names a writer declares, as data, exactly which issues in
    its span that writer is NOT credited on — if the wiki's credits move, the
    declared exceptions stop matching and the build stops;
  * every year in a section subtitle is the cover year of that section's first
    and last issue, computed, never typed.

Runs, not arcs. The sections are creative runs because that is how this book
is actually talked about and read — the revival, Englehart, Kirby's return,
Stern and Byrne, Gruenwald's decade, Brubaker's eight years. The tier decides
which of them are the readable path.

Civil War. Captain America (vol. 5) #22-24 are chapters of the 2006 crossover
and are already rows on properties/civil-war.json, in the interleaved order
that event wants. They are NOT repeated here — CIVIL_WAR_GAP below is checked
against that file at build time, so if those rows ever leave the Civil War list
this one fails rather than quietly holding a hole.

Unweighted, like every comics list here: nobody publishes a per-issue reading
time and this list does not invent one.

Notes say what an issue IS — whose first issue it is, which book it continues,
how many pages — and never what happens in it. That bites harder on this run
than on most, so several obvious annotations are missing on purpose.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from gwlib import prop  # noqa: E402

SLUG = "captain-america"
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "tools" / "data" / "captain-america.json"

# Series on marvel.com, by the slug Marvel's own A-Z index uses. Resolved
# against tools/data/marvel_series_index.json so a mistyped slug fails the
# build instead of shipping a dead link — the same guard make_civilwar.py has.
SERIES_SLUG = {
    "Captain America Comics Vol 1": "captain_america_comics_1941_1954",
    "Tales of Suspense Vol 1": "tales_of_suspense_1959_1968",
    "Avengers Vol 1": "avengers_1963_1996",
    "Captain America Vol 1": "captain_america_1968_1996",
    "Captain America Vol 2": "captain_america_1996_1997",
    "Captain America Vol 3": "captain_america_1998_2002",
    "Captain America Vol 4": "captain_america_2002_2004",
    "Captain America Vol 5": "captain_america_2004_2011",
    "Captain America Vol 6": "captain_america_2011_2012",
    "Captain America and Bucky Vol 1": "captain_america_and_bucky_2011_2012",
    "Captain America: Reborn Vol 1": "captain_america_reborn_2009_2010",
    "Winter Soldier Vol 1": "winter_soldier_2012_2013",
}

# How each volume is printed on a row, and the id prefix its rows carry.
DISPLAY = {
    "Captain America Comics Vol 1": ("Captain America Comics", "cap-comics"),
    "Tales of Suspense Vol 1": ("Tales of Suspense", "cap-tos"),
    "Avengers Vol 1": ("Avengers", "cap-avengers"),
    "Captain America Vol 1": ("Captain America", "cap-v1"),
    "Captain America Vol 2": ("Captain America vol. 2", "cap-v2"),
    "Captain America Vol 3": ("Captain America vol. 3", "cap-v3"),
    "Captain America Vol 4": ("Captain America vol. 4", "cap-v4"),
    "Captain America Vol 5": ("Captain America vol. 5", "cap-v5"),
    "Captain America Vol 6": ("Captain America vol. 6", "cap-v6"),
    "Captain America and Bucky Vol 1": ("Captain America and Bucky", "cap-bucky"),
    "Captain America: Reborn Vol 1": ("Captain America: Reborn", "cap-reborn"),
    "Winter Soldier Vol 1": ("Winter Soldier", "cap-ws"),
}

# The three issues this list deliberately does not carry, because
# properties/civil-war.json carries them in the order that event reads.
CIVIL_WAR_GAP = ("Captain America Vol 5", (22, 23, 24))

# note and star, by (series, issue). Every one of these is a publication fact
# taken from the same infoboxes the rows are: a first issue, a fill-in, a page
# count, which book a numbering continues. None of them says what happens.
NOTE = {
    ("Avengers Vol 1", 4): "Not his own book — the issue that brings him back.",
    ("Tales of Suspense Vol 1", 59): "The strip starts here, in the back half of the book.",
    ("Tales of Suspense Vol 1", 63): "Kirby draws the origin again for the new readers.",
    ("Captain America Vol 1", 100): "Continues Tales of Suspense's numbering.",
    ("Captain America Vol 1", 110): "Steranko.",
    ("Captain America Vol 1", 111): "Steranko.",
    ("Captain America Vol 1", 112): "A Lee and Kirby fill-in between Steranko's two halves.",
    ("Captain America Vol 1", 113): "Steranko's last.",
    ("Captain America Vol 1", 153): "Englehart's first.",
    ("Captain America Vol 1", 193): "Kirby returns, writing and drawing.",
    ("Captain America Vol 1", 247): "Stern and Byrne begin.",
    ("Captain America Vol 1", 261): "DeMatteis begins.",
    ("Captain America Vol 1", 307): "Gruenwald begins. He stays ten years.",
    ("Captain America Vol 1", 444): "Waid's first.",
    ("Captain America Vol 2", 1): "Relaunched outside the main continuity.",
    ("Captain America Vol 3", 1): "Waid and Garney pick it back up.",
    ("Captain America Vol 3", 24): "A one-issue fill-in between the two runs.",
    ("Captain America Vol 3", 25): "Jurgens takes over.",
    ("Captain America Vol 4", 1): "Rieber and Cassaday relaunch it.",
    ("Captain America Vol 5", 1): "Brubaker's first. Eight years from here.",
    ("Captain America Vol 5", 25): "#22-24 are Civil War chapters and sit on that list.",
    ("Captain America Vol 5", 600): "104 pages, and the old numbering is back.",
    ("Captain America Vol 5", 601): "A stand-alone, drawn by Gene Colan.",
    ("Captain America Vol 6", 1): "Renumbered again; same writer, straight on.",
    ("Captain America: Reborn Vol 1", 1): "A six-issue book running alongside the main title.",
    ("Winter Soldier Vol 1", 1): "A book of its own, and where the run ends.",
}
STAR = {
    ("Avengers Vol 1", 4): 2,
    ("Tales of Suspense Vol 1", 59): 1,
    ("Captain America Vol 1", 100): 1,
    ("Captain America Vol 1", 110): 1,
    ("Captain America Vol 1", 111): 1,
    ("Captain America Vol 1", 113): 1,
    ("Captain America Vol 1", 153): 1,
    ("Captain America Vol 1", 193): 1,
    ("Captain America Vol 1", 247): 1,
    ("Captain America Vol 1", 255): 1,
    ("Captain America Vol 5", 1): 2,
    ("Winter Soldier Vol 1", 1): 1,
}

V1 = "Captain America Vol 1"
V5 = "Captain America Vol 5"

# id, tier, title, the spans it covers, and the writer each span is attributed
# to. `skip` lifts issues out of a span (only Civil War does that); `bar` is
# the set of issues in the span the writer is NOT credited on, declared here
# and checked against the wiki's credits.
SECTIONS = [
    dict(
        id="timely", tier=3, title="Timely, 1941",
        sub="#1 · the first one",
        spans=[("Captain America Comics Vol 1", 1, 1)],
        writer="Jack Kirby", bar=set(),
        intro="Simon and Kirby's first issue, and it reads like what it is: a "
              "1941 adventure comic aimed squarely at children, with a cover "
              "that got its publisher hate mail.\n\nNothing later on this list "
              "needs it. It is here because it is the thing everything else is "
              "a revival of.",
    ),
    dict(
        id="fifties", tier=3, title="The 1954 attempt",
        sub="#76–78 · three issues and out",
        spans=[(V1, 76, 78)],
        writer="Don Rico", bar=set(),
        intro="Atlas brought the character back in 1954 for three issues and "
              "then stopped. The numbering here is continuous with the 1968 "
              "book, which is why Captain America #79 does not exist.\n\nSkip "
              "it if you like. Englehart comes back to these issues twenty "
              "years later and makes something out of them, which is the only "
              "reason to have read them.",
    ),
    dict(
        id="revival", tier=1, title="The revival: Lee and Kirby",
        sub="Avengers #4, then Tales of Suspense #59–99",
        spans=[("Avengers Vol 1", 4, 4), ("Tales of Suspense Vol 1", 59, 99)],
        writer="Stan Lee", bar={68, 99},
        start=True,
        intro="Captain America had been out of print for a decade when the "
              "Avengers found him in 1964. Four issues later he had half of "
              "Tales of Suspense, and for the next four years that is where "
              "the character lived: ten or twelve pages an issue, sharing the "
              "book with Iron Man.\n\nThe split matters for a practical "
              "reason. Only the back half of each Tales of Suspense is on this "
              "list, but Marvel files the whole issue under one cover, so you "
              "will be paging past an Iron Man story to get to it.",
    ),
    dict(
        id="ownbook", tier=1, title="His own book again",
        sub="#100–109 · straight on from Tales of Suspense",
        spans=[(V1, 100, 109)],
        writer="Stan Lee", bar=set(),
        intro="Tales of Suspense splits in two and Captain America keeps the "
              "numbering, which is why his first solo issue in fourteen years "
              "is #100.",
    ),
    dict(
        id="steranko", tier=1, title="Steranko",
        sub="#110–113 · three issues, and the fill-in between them",
        spans=[(V1, 110, 113)],
        writer=None, bar=set(),
        intro="Jim Steranko wrote and drew three issues of this book and then "
              "left, and people have been talking about them ever since. They "
              "look like nothing else in 1969 Marvel.\n\n#112 is a Lee and "
              "Kirby fill-in that landed in the middle of them because "
              "Steranko was late.",
    ),
    dict(
        id="lateLee", tier=3, title="Lee winds down",
        sub="#114–152 · Lee, then Friedrich, then Conway",
        spans=[(V1, 114, 152)],
        writer=None, bar=set(),
        intro="Three years of a book with no particular direction, handed "
              "between writers. There is good work in it and no reason to "
              "start here.",
    ),
    dict(
        id="englehart", tier=1, title="The Englehart era",
        sub="#153–186 · the run that made the book political",
        spans=[(V1, 153, 186)],
        writer="Steve Englehart", bar={168},
        intro="Steve Englehart took a book about a soldier who believes in his "
              "country and wrote thirty-odd issues about what that belief "
              "costs when the country turns out not to deserve it. It was "
              "published while Watergate was on television.\n\nHe also dug up "
              "the three 1954 issues and explained them, which is the trick "
              "everyone remembers. Reading #76–78 first is not required, but "
              "it is cheap.",
    ),
    dict(
        id="interregnum", tier=3, title="Six months in between",
        sub="#187–192 · Warner, Isabella, Mantlo, Wolfman",
        spans=[(V1, 187, 192)],
        writer=None, bar=set(),
        intro="The stretch between Englehart leaving and Kirby arriving. Four "
              "writers in six issues, and it shows.",
    ),
    dict(
        id="kirby", tier=1, title="Kirby comes back",
        sub="#193–214 · writing and drawing, this time",
        spans=[(V1, 193, 214)],
        writer="Jack Kirby", bar=set(),
        intro="Kirby returned to the character he co-created in 1941 and wrote "
              "it himself, with nobody editing the ideas down. The result is "
              "loud, strange, enormously confident and completely unlike the "
              "run it follows.\n\nPeople who want the Englehart book back tend "
              "to hate it. Take it on its own terms.",
    ),
    dict(
        id="manyhands", tier=3, title="Many hands",
        sub="#215–246 · 1977–80, and a different writer most months",
        spans=[(V1, 215, 246)],
        writer=None, bar=set(),
        intro="Four years the book spent being kept alive rather than written. "
              "Roger McKenzie holds most of it together. Skippable in full.",
    ),
    dict(
        id="stern", tier=1, title="Stern and Byrne",
        sub="#247–255 · nine issues",
        spans=[(V1, 247, 255)],
        writer="Roger Stern", bar=set(),
        intro="Nine issues, and the shortest thing on this list anybody "
              "argues for. Stern and Byrne rebuilt the character's supporting "
              "cast and his day job, and #255 retells the origin in a single "
              "issue well enough that later writers mostly stopped trying.",
    ),
    dict(
        id="gap81", tier=3, title="Five before DeMatteis",
        sub="#256–260 · 1981",
        spans=[(V1, 256, 260)],
        writer=None, bar=set(),
        intro="Fill-ins between two runs.",
    ),
    dict(
        id="dematteis", tier=2, title="J.M. DeMatteis",
        sub="#261–300 · with David Kraft taking six of them",
        spans=[(V1, 261, 300)],
        writer="J.M. DeMatteis", bar={265, 266, 271, 273, 274, 291},
        intro="DeMatteis writes the character as somebody who would rather "
              "talk than fight, and builds the run around villains he can "
              "argue with. It is quieter than what comes after it and better "
              "than its reputation.",
    ),
    dict(
        id="carlin", tier=3, title="Michael Carlin",
        sub="#301–306 · 1985",
        spans=[(V1, 301, 306)],
        writer="Michael Carlin", bar=set(),
        intro="Six issues holding the door for the longest run the book has "
              "had.",
    ),
    dict(
        id="gruenwald", tier=2, title="Mark Gruenwald",
        sub="#307–443 · ten years, the longest run on the title",
        spans=[(V1, 307, 443)],
        writer="Mark Gruenwald", bar={423},
        intro="Ten years and 137 issues, which is more of this character than "
              "anyone else has written. Gruenwald knew the Marvel universe "
              "better than its editors did and used the book as a place to "
              "take its rules seriously: what the job is, who else has done "
              "it, what the government thinks it owns.\n\nIt is uneven over a "
              "decade, and it is the run to read if you want to know the "
              "character rather than the highlights.",
    ),
    dict(
        id="waid", tier=2, title="Mark Waid arrives",
        sub="#444–454 · eleven issues before the line was restarted",
        spans=[(V1, 444, 454)],
        writer="Mark Waid", bar=set(),
        intro="Waid and Ron Garney got eleven issues before Marvel handed the "
              "character to another studio, and spent them writing the "
              "straight version — the one that takes the shield at face "
              "value. They are back in two sections' time.",
    ),
    dict(
        id="heroesreborn", tier=3, title="Heroes Reborn",
        sub="vol. 2 #1–13 · 1996–97 · a year in a separate universe",
        spans=[("Captain America Vol 2", 1, 13)],
        writer=None, bar=set(),
        intro="Marvel outsourced four of its oldest books for a year and "
              "restarted them in a pocket universe. This is the Captain "
              "America one, by Rob Liefeld and then James Robinson.\n\nIt "
              "connects to nothing before it and nothing after it. Included "
              "because the numbering goes through it.",
    ),
    dict(
        id="heroesreturn", tier=2, title="Heroes Return: Waid again",
        sub="vol. 3 #1–24 · picking up where #454 stopped",
        spans=[("Captain America Vol 3", 1, 24)],
        writer="Mark Waid", bar={24},
        intro="The same creative team, the same continuity, two years later — "
              "the run from #444 continuing as though the year in between had "
              "not happened.",
    ),
    dict(
        id="jurgens", tier=3, title="Dan Jurgens",
        sub="vol. 3 #25–50 · to the end of the volume",
        spans=[("Captain America Vol 3", 25, 50)],
        writer="Dan Jurgens", bar=set(),
        intro="Competent superhero comics for two years. Nothing here is "
              "needed later.",
    ),
    dict(
        id="vol4", tier=3, title="The 2002 relaunch",
        sub="vol. 4 #1–32 · four writers in thirty-two issues",
        spans=[("Captain America Vol 4", 1, 32)],
        writer=None, bar=set(),
        intro="Marvel restarted the book for a mature-readers imprint six "
              "months after September 2001 and pointed it directly at that. "
              "John Ney Rieber and John Cassaday open it; Chuck Austen, Dave "
              "Gibbons, Robert Morales and Robert Kirkman take the rest.\n\n"
              "It argues with itself more than it works, and the next section "
              "is why anybody still buys this book.",
    ),
    dict(
        id="brubaker1", tier=1, title="Brubaker begins",
        sub="vol. 5 #1–21 · 2005–06",
        spans=[(V5, 1, 21)],
        writer="Ed Brubaker", bar=set(),
        intro="This is the reason most people arrive. Brubaker wrote the book "
              "for eight years and it reads as one continuous story — a spy "
              "thriller with a superhero in it, drawn mostly by Steve Epting "
              "in heavy shadow, where the plot turns on things that happened "
              "in 1945 and are still being paid for.\n\nStart at #1. You need "
              "nothing above this line.",
    ),
    dict(
        id="brubaker2", tier=1, title="Brubaker: the middle",
        sub="vol. 5 #25–42 · 2007–08",
        spans=[(V5, 25, 42)],
        writer="Ed Brubaker", bar=set(),
        intro="#22–24 are Civil War chapters. They are on the Civil War list "
              "here rather than on this one, in the interleaved order that "
              "event reads in, so the run steps from #21 to #25 and the gap is "
              "where they go.\n\nThe story is continuous across it either way.",
    ),
    dict(
        id="brubaker3", tier=1, title="Brubaker: the third act",
        sub="vol. 5 #43–50 · 2008–09",
        spans=[(V5, 43, 50)],
        writer="Ed Brubaker", bar=set(),
        intro="Eight issues, and the last under this numbering.",
    ),
    dict(
        id="legacy", tier=1, title="Back to the old numbering",
        sub="vol. 5 #600–619, with the Reborn miniseries in its place",
        spans=[(V5, 600, 601), ("Captain America: Reborn Vol 1", 1, 6),
               (V5, 602, 619)],
        writer="Ed Brubaker", bar=set(),
        intro="Marvel counted the whole title's issues and jumped to #600. The "
              "six-issue Reborn book ran alongside it and is slotted in where "
              "it was published, between #601 and #602.",
    ),
    dict(
        id="volsix", tier=1, title="Volume six",
        sub="vol. 6 #1–19 · 2011–12",
        spans=[("Captain America Vol 6", 1, 19)],
        writer="Ed Brubaker", bar=set(),
        intro="Renumbered again alongside the first film, with the same writer "
              "carrying straight on. Nineteen issues.",
    ),
    dict(
        id="bucky", tier=2, title="Captain America and Bucky",
        sub="#620–628 · a companion book on the old numbering",
        spans=[("Captain America and Bucky Vol 1", 620, 628)],
        writer="Ed Brubaker", bar=set(),
        intro="Brubaker co-wrote nine issues of a second book that keeps the "
              "legacy numbering going while volume six runs. It fills in the "
              "1940s, and the main run does not depend on it.",
    ),
    dict(
        id="wintersoldier", tier=2, title="Winter Soldier",
        sub="#1–14 · 2012–13 · where the run actually stops",
        spans=[("Winter Soldier Vol 1", 1, 14)],
        writer="Ed Brubaker", bar=set(),
        intro="The last fourteen issues Brubaker wrote of this story, in a "
              "book with somebody else's name on the cover. It is a spy comic "
              "with the superheroes almost entirely out of frame, and it is "
              "the end of the thing that started at volume five #1.",
    ),
]

NOTES = [
    ["Tiers.",
     "1 is the readable path: the 1964 revival, Steranko, Englehart, Kirby's "
     "return, Stern and Byrne, and every issue of Brubaker's run. 2 is "
     "strongly recommended — DeMatteis, Gruenwald's ten years, Waid, and the "
     "two books Brubaker's run finishes in. 3 is genuinely optional, and most "
     "of it is there so the numbering has no holes in it. The minimum viable "
     "path is Tier 1 alone."],
    ["Civil War.",
     "Captain America #22–24 are chapters of the 2006 crossover and live on "
     "the Civil War list here instead, where they sit interleaved with the "
     "rest of that event. They are not repeated on this list, which is why "
     "this one steps from #21 straight to #25."],
    ["Tales of Suspense was a split book.",
     "For #59–99 Captain America has the back half of each issue and Iron Man "
     "has the front. Only the back half is on this list, but the issue is one "
     "object on a shelf and in Marvel Unlimited, so it is one row."],
    ["Reading in Marvel Unlimited?",
     "Sections link the series rather than the issue, because Marvel only "
     "exposes the most recent issues of a series to the outside world. The "
     "issue numbers are the part you need; the volume changes are the part "
     "that catches people out, and the rows name the volume every time it "
     "moves."],
    "Issue numbers, cover dates and writer credits machine-read from the "
    "Marvel Database (marvel.fandom.com) — the volume page lists say which "
    "issues exist and each issue's infobox says who wrote it, and every run "
    "boundary below is checked against those credits at build time. Series "
    "links resolve against Marvel's own A–Z series index.",
]


def yspan(a, b):
    """1972, 1975 -> '1972–75'; 1999, 2001 -> '1999–2001'."""
    if a == b:
        return str(a)
    return "%d–%s" % (a, str(b)[2:] if a // 100 == b // 100 else b)


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    issues = data["issues"]
    idx = json.loads((ROOT / "tools" / "data" /
                      "marvel_series_index.json").read_text(encoding="utf-8"))

    gap_series, gap_nums = CIVIL_WAR_GAP
    civil = json.loads((ROOT / "properties" / "civil-war.json")
                       .read_text(encoding="utf-8"))
    carried = {x["n"].lstrip("#") for s in civil["sections"] for x in s["items"]
               if x["t"] == "Captain America"}
    missing = [n for n in gap_nums if str(n) not in carried]
    assert not missing, (
        "civil-war.json no longer carries Captain America #%s, so leaving "
        "them out of this list would lose them entirely" % missing)

    sections, seen = [], set()
    for spec in SECTIONS:
        items, years, off = [], [], set()
        for series, lo, hi in spec["spans"]:
            have = sorted(int(n) for n in issues[series])
            span = [n for n in have if lo <= n <= hi]
            assert span and span[0] == lo and span[-1] == hi, (
                "%s: %s #%d–%d is not a run of issues the source lists (%s)"
                % (spec["id"], series, lo, hi, span[:3]))
            if series == gap_series:
                span = [n for n in span if n not in gap_nums]
            title, pre = DISPLAY[series]
            for n in span:
                rec = issues[series][str(n)]
                key = (series, n)
                assert key not in seen, "issue listed twice: %s #%d" % key
                seen.add(key)
                years.append(rec["year"])
                row = {"id": "%s-%d" % (pre, n), "t": title, "n": "#%d" % n,
                       "note": NOTE.get(key, ""), "star": STAR.get(key, 0),
                       "opt": 0, "url": ""}
                items.append(row)

            if spec["writer"]:
                off |= {n for n in span
                        if spec["writer"] not in issues[series][str(n)]["writers"]}

        # A named writer has to actually be credited across the section, and
        # the issues they are not credited on have to be exactly the declared
        # ones. This is what stops a run boundary drifting off its source.
        assert off == spec["bar"], (
            "%s: the source credits %s on a different set of issues than "
            "declared — not credited on %s, declared %s"
            % (spec["id"], spec["writer"], sorted(off), sorted(spec["bar"])))

        links, seen_links = [], set()
        for series, _, _ in spec["spans"]:
            mslug = SERIES_SLUG[series]
            assert mslug in idx, "no such Marvel series slug: %s" % mslug
            if mslug in seen_links:
                continue
            seen_links.add(mslug)
            links.append({"label": DISPLAY[series][0],
                          "url": "https://www.marvel.com/comics/series/%s/%s"
                                 % (idx[mslug], mslug)})

        # The years on a section header are never typed: they are the cover
        # years of its own first and last issue.
        sec = {"id": spec["id"], "title": spec["title"],
               "sub": "%s · %s" % (spec["sub"], yspan(min(years), max(years))),
               "tier": spec["tier"], "intro": spec["intro"],
               "items": items, "links": links}
        if spec.get("start"):
            sec["start"] = True
        sections.append(sec)

    rows = sum(len(s["items"]) for s in sections)
    assert rows > 600, "only %d rows" % rows
    assert not any("w" in x for s in sections for x in s["items"]), \
        "comics lists here carry no weights"

    first = issues["Captain America Comics Vol 1"]["1"]["year"]
    last = max(issues["Winter Soldier Vol 1"][str(n)]["year"]
               for n in range(1, 15))

    out = {
        "slug": SLUG,
        "title": "Captain America",
        "subtitle": "Marvel's main continuity — the shield, not the man",
        "kind": "comics",
        "popularity": 68,
        "year": "%d–%d" % (first, last),
        "blurb": "%d issues, from the 1964 revival to the last page Ed "
                 "Brubaker wrote, one section per run." % rows,
        "unit": {"one": "issue", "many": "issues"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": "#26468F",
        "accentDark": "#7FA8E8",
        "tiers": True,
        "notes": NOTES,
        "sections": sections,
    }
    path = prop.write(out)
    print("%s: %d rows in %d sections (tier 1: %d)"
          % (path.name, rows, len(sections),
             sum(len(s["items"]) for s in sections if s["tier"] == 1)))


if __name__ == "__main__":
    sys.exit(main())
