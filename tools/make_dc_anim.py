#!/usr/bin/env python3
"""Generate properties/dc-animation.json.

    python3 tools/make_dc_anim.py

Every animated DC film and television series, in release order — the drawn
counterpart to the live-action DC Anthology, and built the same way.

Sources, machine-read rather than typed (see scratch/dc-anim/):
  - series: Wikipedia, List of television series based on DC Comics
    publications, the Animated table plus its From DC imprints table
  - films: Wikipedia, List of films based on DC Comics publications, the
    animated Theatrical and Direct-to-video and streaming tables
  - which films are DC Animated Movie Universe and which are its
    Tomorrowverse arc: the Continuity column of the DC Universe Animated
    Original Movies article
  - film runtimes and release dates: Wikidata P2047 and P577, with the film
    articles' infoboxes filling the runtimes Wikidata lacks for much of the
    direct-to-video line

Television is tracked season by season at 22 minutes an episode, the count
split evenly across the seasons, each season placed by spreading them evenly
between the years the series started and ended — the same approximations as
the anthology, at cartoon length. Broadcast wheels that only repackaged
series already on the list, TV specials, shorts, motion comics, web series
and episode compilations are left out.

Like the anthology there are no tiers: there is no single continuity to rank
against. The ones people care about are named in row notes instead — DCAU,
DC Animated Movie Universe, Tomorrowverse, DCU — read from the source tables
rather than asserted from memory.
"""
import json
import pathlib
import re

PROP_SLUG = "dc-animation"
EP_MINUTES = 22

# The year "–present" airing ranges run through: the revision of the list
# these tables were read from was fetched in 2026.
PRESENT = 2026

# One row known bad upstream: the television list gives Static Shock 13
# episodes, which is its episodes-per-season. Wikidata (Q1470464) has
# P1113 = 52 episodes over P2437 = 4 seasons; verified by
# scratch/dc-anim/runtimes.py.
SHOW_EPISODE_FIX = {"Static Shock": 52}

# CLU-550. Two different DC series are called Swamp Thing and both begin in
# 1990: this animated one, five episodes on Fox Kids, and the live-action USA
# Network series on dc-anthology. clubd pairs ticks across lists on
# title+year+medium, so to the site those two rows were ONE work — ticking the
# live-action season marked this cartoon watched on a list the person had never
# opened, and unticking either took the other with it.
#
# THE WORK ID DOES NOT PART THEM. build.py mints the title+year key alongside
# the id key and unions any two keys one row carries, so giving each row its
# own correct id left them meeting through the title they still share — and
# named the merged group after the live-action series, which is worse than
# where it started. What parts them is the title, so this row says which Swamp
# Thing it is. Parenthetical disambiguation is how the rest of the catalogue
# already tells two same-named works apart (1,448 rows do it, black-panther
# most of all), and the row id is untouched: the id is where the ticks are.
#
# Keyed by (title, start year) like the anthology's tables, because DC reuses
# titles — Super Friends is two different series, Aquaman and Krypto recur.
SHOW_TITLE = {("Swamp Thing", 1990): "Swamp Thing (animated)"}

# The work id for a season row. Q3051963 is the animated series itself, read
# from Wikidata 2026-09-11: "1991 American animated television series",
# P31 Q117467246, P580 1990-10-31 to P582 1991-05-11, P1113 five episodes,
# P144 based on Swamp Thing the character (Q1427625) — which is all it shares
# with the live-action Q2024136.
#
# It is the SERIES item on a row that says "season 1", and that is right here
# rather than sloppy: the series ran one season of five episodes, so the row is
# the whole series. Wikidata has no season item to prefer — nothing carries
# P179 = Q3051963, unlike the live-action series, which has one per season and
# whose rows use those.
SHOW_Q = {("Swamp Thing", 1990, 1): "Q3051963"}

ERAS = [
    ("superfriends", "The Super Friends era", "1966–1990",
     "Filmation's Superman through Hanna-Barbera's Super Friends: "
     "Saturday-morning cartoons, made fast and sold by the hour. The "
     "broadcast blocks that only repackaged shows already here are left "
     "out."),
    ("dcau", "The DCAU", "1992–2006",
     "Batman: The Animated Series through Justice League Unlimited — one "
     "continuity across fourteen years, and the reason DC animation has the "
     "reputation it does. Rows marked DCAU are part of it; Teen Titans and "
     "The Batman ran alongside and are not."),
    ("dtv", "The direct-to-video era", "2007–2019",
     "Superman: Doomsday opens the DC Universe Animated Original Movies "
     "line and the films start arriving several a year, straight to disc — "
     "including the connected DC Animated Movie Universe from 2013. "
     "Television keeps going beside them: The Brave and the Bold, Young "
     "Justice, Teen Titans Go!."),
    ("tomorrowverse", "The Tomorrowverse and after", "2020–",
     "The Tomorrowverse arc runs Man of Tomorrow through Crisis on Infinite "
     "Earths, and television turns adult — Harley Quinn and its spin-offs, "
     "Caped Crusader, My Adventures with Superman, and Creature Commandos "
     "opening the new DCU."),
]
BOUNDS = {"superfriends": (0, 1991), "dcau": (1992, 2006),
          "dtv": (2007, 2019), "tomorrowverse": (2020, 9999)}

PART = {"one": 1, "two": 2, "three": 3, "i": 1, "ii": 2, "iii": 3}


def slug(t):
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def era_of(year):
    for k, (lo, hi) in BOUNDS.items():
        if lo <= year <= hi:
            return k
    return "tomorrowverse"


def part_key(title):
    """Multi-part films share a release date, and 'Part Three' sorts before
    'Part Two' alphabetically — order them by the part number instead."""
    m = re.search(r"(?:part|chapter)\s+(\w+)$", title, re.I)
    if not m:
        return title, 0
    w = m.group(1).lower()
    n = PART.get(w, int(w) if w.isdigit() else 0)
    return title[:m.start()], n


def main():
    data = pathlib.Path(__file__).resolve().parent / "data" / "dc_anim.json"
    blob = json.loads(data.read_text(encoding="utf-8"))

    entries = []
    for f in blob["films"]:
        mins = f["runtime"] or 0
        bits = list(f["runs"])
        if not mins and f["year"] >= 2026:
            bits.append("Not out yet")
        entries.append({
            "id": "dca-f-%d-%s" % (f["year"], slug(f["title"])),
            "t": f["title"], "n": str(f["year"]), "w": round(mins / 60.0, 2),
            "note": " · ".join(bits), "date": f["released"],
            "year": f["year"], "kind": "film",
            "sortkey": part_key(f["title"]),
        })

    for s in blob["shows"]:
        year = int(s["start"]) if s["start"] else None
        if year is None:
            continue  # announced, no airdate — nothing to watch yet
        seasons = s["seasons"] or 1
        eps = SHOW_EPISODE_FIX.get(s["title"], s["episodes"]) or 0
        per = round(eps / seasons * EP_MINUTES / 60.0, 2) if eps else 0
        if s["end"]:
            last = int(s["end"])
        elif s["present"]:
            last = PRESENT
        else:
            last = year + seasons - 1
        run = "DCAU" if s["dcau"] else ("DCU" if s["dcu"] else None)
        for k in range(1, seasons + 1):
            # each season gets its own year, spread evenly across the run,
            # so a long series doesn't sort entirely at its premiere
            sy = year if seasons == 1 else \
                year + round((k - 1) * (last - year) / (seasons - 1))
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
                # DC reuses titles — Super Friends is two different series,
                # Aquaman and Krypto recur — so the id keeps the first year
                "id": "dca-t-%d-%s-s%d" % (year, slug(s["title"]), k),
                "t": "%s season %d" % (
                    SHOW_TITLE.get((s["title"], year), s["title"]), k),
                "q": SHOW_Q.get((s["title"], year, k)),
                "n": str(sy), "w": per, "note": " · ".join(bits),
                "date": "%d-06-15" % sy, "year": sy, "kind": "show",
                "sortkey": (s["title"], k),
            })

    # sort seasons by number, not title ("season 10" precedes "season 2"
    # alphabetically), and film parts by part number
    entries.sort(key=lambda e: (e["date"], e["kind"] == "show", e["sortkey"]))

    sections = []
    for key, title, years, intro in ERAS:
        got = [e for e in entries if era_of(e["year"]) == key]
        if not got:
            continue
        nf = sum(1 for e in got if e["kind"] == "film")
        ns = len(got) - nf
        hours = sum(e["w"] for e in got)
        counts = " and ".join(
            "%d %s%s" % (n, w, "" if n == 1 else "s")
            for n, w in ((nf, "film"), (ns, "season")) if n)
        sec = {"id": key, "title": title,
               "sub": "%s · %s · %d hours" % (years, counts, round(hours)),
               "intro": intro,
               "items": [{k: v for k, v in e.items()
                          if k in ("id", "t", "n", "w")
                          or (k in ("note", "q") and v)}
                         for e in got]}
        assert all(a["n"] <= b["n"] for a, b in zip(sec["items"], sec["items"][1:])), \
            "%s is out of year order" % title
        if key == "superfriends":
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(entries), (len(ids), len(entries))
    nf = sum(1 for e in entries if e["kind"] == "film")
    ns = len(entries) - nf
    hours = sum(e["w"] for e in entries)

    prop = {
        "slug": PROP_SLUG,
        # CLU-508 declared this list a mega list, and build.py reads the flag
        # off the property file (`p["_mega"] = bool(p.get("mega"))`) to put it
        # in the home page's mega row instead of the card wall. The flag was
        # committed straight onto properties/dc-animation.json and never added
        # here, so every run of this script silently deleted it and dropped the
        # list out of that row — the hand-edit-undone-by-rebuild trap, caught
        # for the third time on CLU-550. Declared here so the generator
        # reproduces its own file. (make_starwars.py carries the same note;
        # marvel-animation and mcu-anthology are still exposed to it.)
        "mega": True,
        "title": "DC Animation",
        "subtitle": "every animated DC film and series, in release order",
        "kind": "shows & films",
        "popularity": 62,
        "year": "1966–",
        "blurb": "%d films and %d seasons of television, about %d hours, in "
                 "the order they came out." % (nf, ns, round(hours)),
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#2A5F9E",
        "accentDark": "#7FB0E8",
        "tiers": False,
        "notes": [
            ["Animation only.", "The live-action films and series are the DC "
             "Anthology, a separate list. This is the drawn side: theatrical "
             "features, the direct-to-video line, and television from "
             "Filmation to the streaming era."],
            ["No tiers, because there is no single continuity.", "Where an "
             "entry belongs to one that matters, its note says which — DCAU "
             "for the 1992–2006 animated universe, DC Animated Movie "
             "Universe for the 2013–2020 film line, Tomorrowverse for the "
             "2020–2024 arc that followed it, DCU for the new franchise."],
            ["Television is tracked season by season.", "A season's length "
             "is the series' episode count split evenly across its seasons "
             "at %d minutes an episode — the source gives totals, not "
             "per-season breakdowns. Seasons are spread evenly between the "
             "years the series started and ended." % EP_MINUTES],
            ["Bar widths are runtimes.", "Films use their real runtime from "
             "Wikidata, with the film articles filling the gaps Wikidata "
             "has across the direct-to-video line. The unreleased ones "
             "weigh nothing and cannot drag a group's pace."],
            "Series and film lists from Wikipedia's DC publications tables, "
            "including the animated imprint table; continuity labels from "
            "the tables' own notes. Broadcast blocks that only repackaged "
            "series already on the list, TV specials, shorts, motion "
            "comics, web series and episode compilations are left out.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % PROP_SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % PROP_SLUG)
    print("  %d sections, %d entries (%d films, %d seasons), %d hours"
          % (len(sections), len(ids), nf, ns, round(hours)))
    for s in sections:
        print("   %-28s %3d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
