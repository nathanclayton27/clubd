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
  - film runtimes and release dates: Wikidata P2047 and P577

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

SLUG = "dc-anthology"

EP_MINUTES = 43

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
            ["Bar widths are runtimes.", "Films use their real runtime from "
             "Wikidata. Batgirl was shelved before release and the 2026–28 films "
             "are not out, so those weigh nothing and cannot drag a group's pace."],
            "Film and series lists from Wikipedia's DC publications tables, "
            "including the DC imprint tables — Vertigo and the rest — so "
            "Sandman, Lucifer, Preacher, V for Vendetta and Road to Perdition "
            "are all here. Runtimes and release dates from Wikidata.",
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


if __name__ == "__main__":
    main()
