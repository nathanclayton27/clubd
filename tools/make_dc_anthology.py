#!/usr/bin/env python3
"""Generate properties/dc-anthology.json.

    python3 tools/make_dc_anthology.py

Every live-action DC film and television series, in release order. No animation:
that is a separate and much larger body of work.

Sources, machine-read rather than typed:
  - films: Wikipedia, List of films based on DC Comics publications, the
    live-action feature table plus the DC imprints tables
  - series: Wikipedia, List of television series based on DC Comics
    publications, the live-action table plus the DC Imprints table, which
    already carry seasons, episodes and airing years
  - film release dates: Wikidata P577
  - film runtimes: each film's own {{Infobox film}} — see below

Weights: each film's own infobox, not Wikidata (CLU-425, CLU-178)
-----------------------------------------------------------------
Every film bar is the runtime printed in that film's own Wikipedia infobox,
chosen by gwlib.runtime.weigh(). This list used to weigh from Wikidata's P2047,
which collects every length an item has ever been given with the provenance
stripped off — so "the runtime" quietly became "one of the cuts", and three
rows on this list ended up measuring a version their own title does not name:

  * **Watchmen** carried 216 minutes. The theatrical release is 162; 186 is the
    director's cut and 215 the Ultimate Cut, and best-directors-cuts already
    carries that director's cut as a row of its own at 186. A plainly-titled
    row cannot be half an hour longer than the row that IS the director's cut.
  * **Batman v Superman** carried 182 minutes, which is byte-identical to
    best-directors-cuts' *Ultimate Edition* row. The theatrical is 151.
  * **Supergirl** (1984) carried 125 minutes, which is no released length at
    all — the box prints 105 (US theatrical cut), 124 (international cut) and
    138 (director's cut), and 125 is the international cut rounded up from
    124:28. Nobody found this by hand; it fell out of the re-run.

On clubd a cut is its own film: rows pair across lists on normalised title plus
year, so a row measuring a cut while displaying the plain title is a row that
will one day tick somebody's theatrical viewing, or be ticked by it. That is the
whole reason these three mattered and the 16 rows that moved by one to ten
minutes did not.

What each box printed, labels kept, is recorded beside every film in
tools/data/dc_films.json as `cuts`, and the generator prints the label it chose
on every run — so "which version is this list measuring" is answered by
re-running this script rather than by reading 55 articles.

Two rows the rule gets wrong are overridden, each with its citation, and each
pinning what the rule says today so a rewritten box stops the build instead of
silently outvoting the decision. See RUNTIME_EXCEPTION.

Television is tracked season by season, not episode by episode. A season's
weight is the series' episode count divided evenly across its seasons at 43
minutes each — an even split, because the source gives a total rather than a
per-season breakdown, and 44 series is too many to look up individually.

Seasons sit together at the year their series began rather than being spread
across the years they aired, because the source has no per-season dates and
inventing them would be worse than grouping them.

Unlike Marvel there is no single continuity to rank against, so there are no
tiers. Where an entry belongs to a recognisable run — the Nolan films, the
DCEU, the Arrowverse, the new DCU — its note says so.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import runtime as RT  # noqa: E402

SLUG = "dc-anthology"

EP_MINUTES = 43

# A film where the rule in gwlib/runtime.py returns the wrong figure, keyed by
# (title, year) because DC reuses titles. The value is (minutes, why,
# rule_says) — and `rule_says` is pinned so that a rewritten infobox stops the
# build rather than leaving an override describing a figure that has changed
# under it. This is make_ss.py's RUNTIME_EXCEPTION, same shape and same reason.
RUNTIME_EXCEPTION = {
    # The rule takes the first figure a box prints, and its docstring says why:
    # where a box lists several national cuts, the first has been the original
    # release every time so far, and where it is not, the generator says so
    # with a citation. This is that case. The box leads with 105 minutes
    # (US theatrical cut), but the article's own release section says the film
    # "was edited from 135 minutes to 105 minutes for its North American
    # release" and that it "originally ran at 124 minutes in its European
    # version" — so the original release is the second figure, not the first,
    # and the 124-minute international cut is also what Warner has sold on
    # every disc since 2006. The 138-minute director's cut is a later re-edit
    # and is not a candidate under the rule.
    ("Supergirl", 1984): (
        124, "the international cut — the original release; Tri-Star cut it to "
             "105 for North America", 105),
    # The box prints one figure, 123 minutes, with no label — so the rule has
    # nothing to reject and returns it. The article's own home-media section
    # says what it is: the Blu-ray "includes an extended cut, which adds an
    # extra nine minutes of footage to the running time, totaling 123 minutes".
    # The theatrical release is 114, which is the figure this row already
    # carried, so the rule would have moved a correct bar onto an extended cut.
    # A label the box does not print is exactly what the rule cannot see, and
    # the honest answer is a named exception rather than a widened rule.
    ("Green Lantern", 2011): (
        114, "the theatrical cut — the box's 123 is the extended cut its own "
             "home-media section describes", 123),
}

# The rows whose bar has to SAY which version it is, keyed by (title, year).
# The clause here follows the minutes, which the generator supplies, so the
# note can never disagree with the bar.
#
# Every row whose box prints more than one figure must appear here, and the
# build asserts it: a box that starts listing cuts is a row that has stopped
# being self-explanatory. The two rows that are here anyway print ONE figure
# each, and are here because this catalogue carries their longer cut as a row
# of its own on best-directors-cuts — which is what proved both of them were
# measuring the wrong version in the first place.
VERSION_NOTE = {
    ("Watchmen", 2009):
        "the theatrical cut; a director's cut runs 186 and an Ultimate Cut 215",
    ("Batman v Superman: Dawn of Justice", 2016):
        "the theatrical cut; the Ultimate Edition runs 31 minutes longer",
    ("Supergirl", 1984):
        "the international cut; the US theatrical cut runs 105 and a "
        "director's cut 138",
    ("Green Lantern", 2011):
        "the theatrical cut; an extended cut runs 123",
}

# Which run something belongs to, where it belongs to one at all.
# Which run a FILM belongs to, where it belongs to one at all.
#
# Keyed by title AND year, for the same reason SHOW_RUN below is: DC reuses
# titles. Keyed by title alone, this map labelled Donner's 1978 "Superman"
# and the 1984 "Supergirl" as DCU — Gunn's continuity, which began in 2025
# and which neither film could possibly belong to.
#
# The 1978-87 Superman films and the 1984 Supergirl ARE one continuity, and
# they still carry no label, because nothing on this list before 1989 does:
# the label exists to tell apart continuities that run ALONGSIDE each other,
# and there was only ever one of these at a time until Burton.
#
# Television series are not in here at all. RUN is consumed only for film
# rows, so the Arrowverse entries that used to sit here were dead — and worse
# than dead, since a Batwoman film would have inherited "Arrowverse".
RUN = {
    ("Batman Begins", 2005): "The Dark Knight trilogy",
    ("The Dark Knight", 2008): "The Dark Knight trilogy",
    ("The Dark Knight Rises", 2012): "The Dark Knight trilogy",
    ("Man of Steel", 2013): "DCEU",
    ("Batman v Superman: Dawn of Justice", 2016): "DCEU",
    ("Suicide Squad", 2016): "DCEU",
    ("Wonder Woman", 2017): "DCEU",
    ("Justice League", 2017): "DCEU",
    ("Aquaman", 2018): "DCEU",
    ("Shazam!", 2019): "DCEU",
    ("Birds of Prey", 2020): "DCEU",
    ("Wonder Woman 1984", 2020): "DCEU",
    ("The Suicide Squad", 2021): "DCEU",
    ("Black Adam", 2022): "DCEU",
    ("Shazam! Fury of the Gods", 2023): "DCEU",
    ("The Flash", 2023): "DCEU",
    ("Blue Beetle", 2023): "DCEU",
    ("Aquaman and the Lost Kingdom", 2023): "DCEU",
    ("Superman", 2025): "DCU",
    ("Supergirl", 2026): "DCU",
    ("Clayface", 2026): "DCU",
    ("Man of Tomorrow", 2027): "DCU",
    ("The Batman", 2022): "Matt Reeves' continuity",
    ("The Batman: Part II", 2028): "Matt Reeves' continuity",
    ("Joker", 2019): "Standalone",
    ("Joker: Folie à Deux", 2024): "Standalone",
}# Keyed by title *and* start year: DC reuses titles, so "The Flash" is both a
# 1990 series and a 2014 Arrowverse one, and "Birds of Prey" is both a 2002
# series and a 2020 DCEU film. Shows never fall back to the film table.
SHOW_RUN = {
    ("Arrow", 2012): "Arrowverse",
    ("The Flash", 2014): "Arrowverse",
    ("Supergirl", 2015): "Arrowverse",
    ("Legends of Tomorrow", 2016): "Arrowverse",
    ("Black Lightning", 2018): "Arrowverse",
    ("Batwoman", 2019): "Arrowverse",
    ("Peacemaker", 2022): "DCU",
    ("The Penguin", 2024): "Matt Reeves' continuity",
}

# Wikipedia's Batwoman row is missing its Original airing cell entirely, so
# the parser leaves its years blank. Wikidata has the premiere: 6 Oct 2019.
SHOW_YEAR_FIX = {"Batwoman": (2019, "2019", "2022")}

# A verified Wikidata work id for a season row, keyed by (title, start year,
# season number) — same reason SHOW_RUN is keyed by title and year, and the
# season number too because a series item would be wrong on every season but
# one.
#
# This exists because of CLU-550. Two different DC series are called Swamp
# Thing and both begin in 1990: this one, the live-action USA Network series,
# and the five-episode animated series on dc-animation. The sync map pairs
# rows across lists on title+year+medium, so those two rows were ONE work to
# the site — ticking the live-action season marked the cartoon watched on a
# list the person had never opened, and unticking either took the other with
# it.
#
# The id does NOT fix that on its own, and it is important not to believe it
# does: build.py mints the title+year key ALONGSIDE the id key and merges any
# two keys a single row carries, so the two rows still met through the title
# they share. Parting them took the title, and dc-animation's row carries the
# disambiguation. The ids are here because they are the right identity for
# these rows regardless, and because they are what pairs the seasons correctly
# the day another list carries this series.
#
# Read from Wikidata 2026-09-11: each is P31 Q3464665 (television series
# season), P179 Q2024136 (the 1990 series) with the P1545 ordinal below, and
# their P1113 episode counts of 22, 11 and 39 add to the 72 the series claims.
SHOW_Q = {
    ("Swamp Thing", 1990, 1): "Q114448629",
    ("Swamp Thing", 1990, 2): "Q114448710",
    ("Swamp Thing", 1990, 3): "Q114447920",
}

ERAS = [
    ("early", "Before Burton", "1951–1988",
     "Serial-era Superman, the 1966 Batman, and the Donner films that showed a "
     "comic-book movie could be played straight."),
    ("burton", "Burton to Schumacher", "1989–2001",
     "Four Batman films that get progressively louder, and the first modern "
     "run of DC television."),
    ("nolan", "Nolan and the wilderness", "2002–2012",
     "One trilogy that reset what the genre could be, surrounded by films that "
     "did not connect to anything."),
    ("dceu", "The DCEU and the Arrowverse", "2013–2023",
     "The shared universe on film and a separate, larger one on television, "
     "running alongside each other for a decade."),
    ("dcu", "Elseworlds and the DCU", "2024–",
     "The reboot, plus the standalone films that were never part of any "
     "continuity to begin with."),
]
BOUNDS = {"early": (0, 1988), "burton": (1989, 2001), "nolan": (2002, 2012),
          "dceu": (2013, 2023), "dcu": (2024, 9999)}


def slug(t):
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def era_of(year):
    for k, (lo, hi) in BOUNDS.items():
        if lo <= year <= hi:
            return k
    return "dcu"


def main():
    data = pathlib.Path(__file__).resolve().parent / "data"
    films = json.loads((data / "dc_films.json").read_text(encoding="utf-8"))
    shows = json.loads((data / "dc_shows.json").read_text(encoding="utf-8"))

    # ---- weights: the film's own infobox, by gwlib.runtime's rule ---------
    # A row the rule cannot settle keeps the figure it already carried — never
    # a guess, and never quietly. `cuts` is what the box printed, labels kept,
    # collected by scratch/agent-rows/measure_lists.py.
    exc = dict(RUNTIME_EXCEPTION)
    kept, moved, needs_note = [], [], set()
    for f in films:
        key = (f["title"], f["year"])
        cuts = [tuple(c) for c in (f.get("cuts") or [])]
        n, why = RT.weigh(cuts, f.get("cuts_range", False))
        if len(cuts) > 1 or f.get("cuts_range"):
            needs_note.add(key)
        if key in RUNTIME_EXCEPTION:
            want, reason, rule_says = exc.pop(key)
            assert n == rule_says, \
                "RUNTIME_EXCEPTION for %s %s expects the rule to say %s, it " \
                "says %s — the article's box has changed, so re-read it before " \
                "trusting either figure" % (f["title"], f["year"], rule_says, n)
            n, why = want, reason
        if n is None:
            kept.append((f["title"], f["year"], f["runtime"], why))
            continue
        if n != f["runtime"]:
            moved.append((n - (f["runtime"] or 0), f["title"], f["year"],
                          f["runtime"], n, why))
        f["runtime"], f["runtime_why"] = n, why
    assert not exc, \
        "RUNTIME_EXCEPTION names films this list does not have: %s" \
        % sorted(exc)
    missing = sorted(k for k in needs_note | set(RUNTIME_EXCEPTION)
                     if k not in VERSION_NOTE)
    assert not missing, \
        "these rows measure one version among several and must say which: %s" \
        % missing
    stray = sorted(set(VERSION_NOTE) - {(f["title"], f["year"]) for f in films})
    assert not stray, \
        "VERSION_NOTE names films this list does not have: %s" % stray

    entries = []
    for f in films:
        mins = f["runtime"] or 0
        bits = []
        if f["imprint"]:
            bits.append("A DC imprint, not the main line")
        if (f["title"], f["year"]) in RUN:
            bits.append(RUN[(f["title"], f["year"])])
        if not mins and f["year"] >= 2025:
            bits.append("Not out yet")
        if f["title"] == "Batgirl":
            bits.append("Shelved before release")
        if (f["title"], f["year"]) in VERSION_NOTE:
            bits.append("%d min, %s"
                        % (mins, VERSION_NOTE[(f["title"], f["year"])]))
        entries.append({
            "id": "dc-f-%d-%s" % (f["year"], slug(f["title"])),
            "t": f["title"], "n": str(f["year"]), "w": round(mins / 60.0, 2),
            "note": " · ".join(bits), "date": f["released"],
            "year": f["year"], "kind": "film",
        })

    for s in shows:
        seasons = s["seasons"] or 1
        eps = s["episodes"] or 0
        per = round(eps / seasons * EP_MINUTES / 60.0, 2) if eps else 0
        year = int(s["start"]) if s["start"] else None
        if year is None and s["title"] in SHOW_YEAR_FIX:
            year, s["start"], s["end"] = SHOW_YEAR_FIX[s["title"]]
        if year is None:
            continue
        run = SHOW_RUN.get((s["title"], year))
        last = int(s["end"]) if s["end"] else year + seasons - 1
        for k in range(1, seasons + 1):
            # Each season gets its own year, spread evenly across the run. A
            # ten-season show parked entirely at its first year sorts ahead of
            # everything that came out while it was still airing, and lands in
            # whichever era it started in — Smallville ran 2001 to 2011 and was
            # sitting in a section that ends in 2001.
            sy = year if seasons == 1 else                 year + round((k - 1) * (last - year) / (seasons - 1))
            bits = []
            if k == 1:
                span = s["start"] + ("–" + s["end"] if s["end"] else "–")
                bits.append("%s · %d season%s, %d episodes"
                            % (span, seasons, "" if seasons == 1 else "s", eps))
                if s["imprint"]:
                    bits.append("A DC imprint, not the main line")
                if run:
                    bits.append(run)
            entries.append({
                # DC reuses titles freely — The Flash, Swamp Thing and
                # Human Target are each two different series — so the id
                # needs the first year to stay unique
                "id": "dc-t-%d-%s-s%d" % (year, slug(s["title"]), k),
                "t": "%s season %d" % (s["title"], k),
                "q": SHOW_Q.get((s["title"], year, k)),
                "n": str(sy), "w": per, "note": " · ".join(bits),
                "date": "%d-06-15" % sy, "year": sy, "kind": "show",
                "sortkey": (s["title"], k),
            })

    # sort seasons by number, not by title: "season 10" sorts before
    # "season 2" alphabetically
    entries.sort(key=lambda e: (e["date"], e["kind"] == "show",
                                e.get("sortkey", (e["t"], 0))))

    sections = []
    for key, title, years, intro in ERAS:
        got = [e for e in entries if era_of(e["year"]) == key]
        if not got:
            continue
        nf = sum(1 for e in got if e["kind"] == "film")
        ns = len(got) - nf
        hours = sum(e["w"] for e in got)
        sec = {"id": key, "title": title,
               "sub": "%s · %d film%s and %d season%s · %d hours"
                      % (years, nf, "" if nf == 1 else "s", ns,
                         "" if ns == 1 else "s", round(hours)),
               "intro": intro,
               "items": [{k: v for k, v in e.items()
                          if k in ("id", "t", "n", "w")
                          or (k in ("note", "q") and v)}
                         for e in got]}
        assert all(a["n"] <= b["n"] for a, b in zip(sec["items"], sec["items"][1:])),             "%s is out of year order" % title
        if key == "early":
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(entries), (len(ids), len(entries))
    hours = sum(e["w"] for e in entries)

    prop = {
        "slug": SLUG,
        # CLU-508 declared this list a mega list, and build.py reads the flag
        # off the property file (`p["_mega"] = bool(p.get("mega"))`) to put it
        # in the home page's mega row instead of the card wall. The flag was
        # committed straight onto properties/dc-anthology.json and never added
        # here, so every run of this script silently deleted it and dropped the
        # list out of that row — the hand-edit-undone-by-rebuild trap, caught
        # for the third time on CLU-550. Declared here so the generator
        # reproduces its own file. (make_starwars.py carries the same note;
        # marvel-animation and mcu-anthology are still exposed to it.)
        "mega": True,
        "title": "DC Anthology",
        "subtitle": "every live-action DC film and series, in release order",
        "kind": "films & shows",
        "popularity": 82,
        "year": "1951–",
        "blurb": "%d films and %d seasons of television, about %d hours, in the "
                 "order they came out." % (sum(1 for e in entries if e["kind"] == "film"),
                                           sum(1 for e in entries if e["kind"] == "show"),
                                           round(hours)),
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#1F5FA8",
        "accentDark": "#6FA8E8",
        "tiers": False,
        "notes": [
            ["Live action only.", "DC's animated output is enormous and largely "
             "separate — a different list, not a section of this one."],
            ["No tiers, because there is no single continuity.", "Marvel has one "
             "through-line to rank against; DC has the Donner films, the Burton "
             "films, the Nolan trilogy, the DCEU, the Arrowverse, Matt Reeves' "
             "Gotham, the new DCU and a pile of standalones. Where an entry "
             "belongs to a recognisable run, its note says which."],
            ["Television is tracked season by season.", "A season's length is the "
             "series' episode count split evenly across its seasons at %d minutes "
             "each — the source gives a total rather than a per-season breakdown. "
             "Each season is placed by spreading them evenly between the years the series started and ended, which is exact for anything that ran annually and close for anything that did not." % EP_MINUTES],
            ["Bar widths are runtimes, read from each film's own article.",
             "Every film bar is the runtime printed in that film's own "
             "Wikipedia infobox, which is where a length keeps the name of the "
             "version it belongs to — Wikidata collects every cut a film has "
             "and says which is which about none of them, which is how three "
             "rows here came to measure a director's cut under a plain title. "
             "Where a film has more than one version, the row says which one "
             "the bar is. Batgirl was shelved before release and the 2026–28 "
             "films are not out, so those weigh nothing and cannot drag a "
             "group's pace."],
            "Film and series lists from Wikipedia's DC publications tables, "
            "including the DC imprint tables — Vertigo and the rest — so "
            "Sandman, Lucifer, Preacher, V for Vendetta and Road to Perdition "
            "are all here. Release dates from Wikidata; film runtimes from "
            "each film's own Wikipedia article.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d entries, %d hours" % (len(sections), len(ids), round(hours)))
    for s in sections:
        print("   %-30s %3d  %s" % (s["title"], len(s["items"]), s["sub"][:50]))
    print("  runtimes: %d films read their own infobox, %d kept what they had"
          % (len(films) - len(kept), len(kept)))
    for title, year, cur, why in kept:
        print("     keeps %-5s %-34s %s" % (cur, "%s (%d)" % (title[:26], year),
                                            why[:50]))
    for d_, title, year, was, now, why in sorted(moved,
                                                 key=lambda m: -abs(m[0])):
        print("     %+5d %-34s %s -> %s  (%s)"
              % (d_, "%s (%d)" % (title[:26], year), was, now, why[:46]))


if __name__ == "__main__":
    main()
