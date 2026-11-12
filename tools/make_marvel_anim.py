#!/usr/bin/env python3
"""Generate properties/marvel-animation.json.

    python3 tools/make_marvel_anim.py

Every animated Marvel television series, season by season, plus the animated
feature films, in release order.

Sources, machine-read rather than typed (see scratch/marvel-anim/):
  - series: Wikipedia, List of television series based on Marvel Comics
    publications — the Animated table plus the animated Malibu and Icon
    imprint tables, which carry seasons, episodes and airing years
  - films: Wikipedia, List of films based on Marvel Comics publications — the
    animated Theatrical and Direct-to-video and television tables
  - film runtimes and release dates: Wikidata P2047 and P577

The three Spider-Verse films are deliberately absent: they already live in the
MCU Anthology property, and a film should not be tickable in two places.

Television is tracked season by season. A season's weight is the series'
episode count divided evenly across its seasons at 22 minutes each — the
source gives totals, not per-season breakdowns — and seasons are spread evenly
across the years the series aired, exactly as the DC Anthology does at 43
minutes. SEASON_YEAR corrects the spread where a series' own article dates a
season, and ANNOUNCED adds the dated seasons the table does not count yet.
"""
import json
import pathlib

SLUG = "marvel-animation"

EP_MINUTES = 22

# Seasons the even spread puts in the wrong year, keyed like FLAVOR, from the
# series' own Wikipedia article. A still-running series has no end year, so
# the spread assumes one season a year from the premiere.
#   X-Men '97: "The second season premiered on July 1, 2026 ... weekly until
#   August 12" (article, revision of 2026-11-08).
#   Spidey and His Amazing Friends: the series overview of List of Spidey and
#   His Amazing Friends episodes (revision of 2026-11-11) starts season 3 on
#   2024-01-08, season 4 on 2025-06-16 and season 5 on 2026-07-13; the series
#   article agrees for 4 ("Season Four Premieres June 16", press release of
#   29 May 2025) and 5 ("Premiering July 13", press release of 8 June 2026).
SEASON_YEAR = {
    ("X-Men '97", 2024): {2: 2026},
    ("Spidey and His Amazing Friends", 2021): {3: 2024, 4: 2025, 5: 2026},
}

# Seasons announced with a date but not yet counted by the source table. They
# weigh nothing until they are out. Each must sit past the table's own season
# count: once the table counts one, delete it here and the table's row takes
# over under the same id. From the series' articles, fetched 2026-11-11:
#   X-Men '97: "the third season planned for release in 2027 and the fourth
#   in 2028" (Collider, 6 August 2026)
#   Your Friendly Neighborhood Spider-Man: "The second season is scheduled to
#   premiere on January 13, 2027"
# Values are (when the list says it is due, sort date).
ANNOUNCED = {
    ("X-Men '97", 2024): {3: ("2027", "2027-06-15"),
                          4: ("2028", "2028-06-15")},
    ("Your Friendly Neighborhood Spider-Man", 2025):
        {2: ("13 January 2027", "2027-01-13")},
}

# What a series is, where the title alone does not say. Keyed by title and
# start year because Marvel reuses titles: Spider-Man is a 1967 series and a
# 1981 one, The Incredible Hulk is 1982 and 1996.
FLAVOR = {
    ("The Marvel Super Heroes", 1966): "An anthology with rotating segments",
    ("Fred and Barney Meet the Thing", 1979):
        "A crossover block with The Flintstones",
    ("Iron Man", 1994): "Half of The Marvel Action Hour",
    ("Fantastic Four", 1994): "The other half of The Marvel Action Hour",
    ("Marvel Disk Wars: The Avengers", 2014): "Anime",
    ("Marvel Future Avengers", 2017): "Anime",
    ("Super Crooks", 2021): "Anime",
    ("Big Hero 6: The Series", 2017): "Continuation of the 2014 film",
    ("M.O.D.O.K.", 2021): "The first adult-oriented Marvel cartoon",
    ("What If...?", 2021): "MCU",
    ("Eyes of Wakanda", 2025): "MCU",
    ("Marvel Zombies", 2025): "MCU · spun out of What If...?",
    ("Your Friendly Neighborhood Spider-Man", 2025): "MCU",
    ("X-Men '97", 2024): "Revival of X-Men: The Animated Series",
    ("Iron Man and His Awesome Friends", 2025):
        "A Spidey and His Amazing Friends spin-off",
    ("Avengers: Mightiest Friends", 2027):
        "A Spidey and His Amazing Friends spin-off",
}

MAF = {"Ultimate Avengers", "Ultimate Avengers 2", "The Invincible Iron Man",
       "Doctor Strange: The Sorcerer Supreme",
       "Next Avengers: Heroes of Tomorrow", "Hulk Versus", "Planet Hulk",
       "Thor: Tales of Asgard"}

FILM_NOTE = {
    ("Dracula: Sovereign of the Damned", 1980):
        "A Toei anime TV movie, loosely from The Tomb of Dracula",
    ("Kyoufu Densetsu Kaiki! Frankenstein", 1981):
        "A Toei anime TV movie, loosely from The Monster of Frankenstein",
    ("Iron Man: Rise of Technovore", 2013):
        "A Marvel Anime film, direct to video",
    ("Avengers Confidential: Black Widow & Punisher", 2014):
        "A Marvel Anime film, direct to video",
    ("Marvel Super Hero Adventures: Frost Fight!", 2015):
        "A direct-to-video Christmas special",
    ("Marvel Rising: Secret Warriors", 2018):
        "A television movie, first of the Marvel Rising line",
    ("Big Hero 6", 2014):
        "Disney's theatrical feature — won the Oscar for Best Animated Feature",
}

ERAS = [
    ("sat", "Saturday mornings", "1966–1983",
     "Grantray-Lawrence's barely animated Marvel Super Heroes through the "
     "Spider-Friends, plus two Toei TV movies — everything up to the long "
     "gap of the late eighties."),
    ("boom", "The nineties boom", "1992–1999",
     "X-Men on Fox Kids proved a cartoon could carry a continuity; "
     "Spider-Man, Iron Man, Fantastic Four and the Hulk followed until the "
     "bubble burst at the decade's end."),
    ("aughts", "The 2000s", "2000–2011",
     "From X-Men: Evolution to the Marvel Anime quartet, with the Marvel "
     "Animated Features line carrying the films direct to video."),
    ("disney", "The Disney era", "2012–2020",
     "Marvel Animation under Disney: Ultimate Spider-Man, Avengers Assemble "
     "and their Disney XD siblings, drawn to a house style."),
    ("streaming", "What If...? and X-Men '97", "2021–",
     "Marvel Studios Animation joins the MCU proper on Disney+, Hulu goes "
     "adult-oriented, and Disney Jr. gets a preschool Spidey."),
]
BOUNDS = {"sat": (0, 1991), "boom": (1992, 1999), "aughts": (2000, 2011),
          "disney": (2012, 2020), "streaming": (2021, 9999)}


def slug(t):
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def era_of(year):
    for k, (lo, hi) in BOUNDS.items():
        if lo <= year <= hi:
            return k
    return "streaming"


def main():
    data = pathlib.Path(__file__).resolve().parent / "data"
    src = json.loads((data / "marvel_anim.json").read_text(encoding="utf-8"))
    films, shows = src["films"], src["shows"]

    entries = []
    for f in films:
        mins = f["runtime"] or 0
        bits = []
        note = FILM_NOTE.get((f["title"], f["year"]))
        if note:
            bits.append(note)
        elif f["title"] in MAF:
            bits.append("A Marvel Animated Features film, direct to video")
        elif f["cat"] == "dtv":
            bits.append("Direct to video")
        entries.append({
            "id": "mva-f-%d-%s" % (f["year"], slug(f["title"])),
            "t": f["title"], "n": str(f["year"]), "w": round(mins / 60.0, 2),
            "note": " · ".join(bits), "date": f["released"],
            "year": f["year"], "kind": "film",
        })

    for s in shows:
        seasons = s["seasons"] or 1
        eps = s["episodes"] or 0
        per = round(eps / seasons * EP_MINUTES / 60.0, 2) if eps else 0
        year = int(s["start"])
        last = int(s["end"]) if s["end"] else year + seasons - 1
        for k in range(1, seasons + 1):
            # spread seasons evenly across the years the series aired, so a
            # five-year run does not sort entirely at its premiere
            sy = year if seasons == 1 else \
                year + round((k - 1) * (last - year) / (seasons - 1))
            sy = SEASON_YEAR.get((s["title"], year), {}).get(k, sy)
            bits = []
            if k == 1:
                span = s["start"] + ("–" + s["end"] if s["end"] else
                                     ("–" if s["ongoing"] else ""))
                if s["episodes"]:
                    bits.append("%s · %d season%s, %d episodes"
                                % (span, seasons,
                                   "" if seasons == 1 else "s", eps))
                else:
                    bits.append("%s · not out yet" % span)
                flavor = FLAVOR.get((s["title"], year))
                if flavor:
                    bits.append(flavor)
                if s["imprint"]:
                    bits.append("A Marvel imprint, not the main line")
            entries.append({
                "id": "mva-t-%d-%s-s%d" % (year, slug(s["title"]), k),
                "t": "%s season %d" % (s["title"], k),
                "n": str(sy), "w": per, "note": " · ".join(bits),
                "date": "%d-06-15" % sy, "year": sy, "kind": "show",
                "sortkey": (s["title"], k),
            })
        for k, (due, date) in sorted(
                ANNOUNCED.get((s["title"], year), {}).items()):
            assert k > seasons, ("the table now counts %s season %d: drop it "
                                 "from ANNOUNCED" % (s["title"], k))
            sy = int(date[:4])
            entries.append({
                "id": "mva-t-%d-%s-s%d" % (year, slug(s["title"]), k),
                "t": "%s season %d" % (s["title"], k),
                "n": str(sy), "w": 0, "note": "%s · not out yet" % due,
                "date": date, "year": sy, "kind": "show",
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
        bits = []
        if nf:
            bits.append("%d film%s" % (nf, "" if nf == 1 else "s"))
        if ns:
            bits.append("%d season%s" % (ns, "" if ns == 1 else "s"))
        sec = {"id": key, "title": title,
               "sub": "%s · %s · %d hours"
                      % (years, " and ".join(bits), round(hours)),
               "intro": intro,
               "items": [{k: v for k, v in e.items()
                          if k in ("id", "t", "n", "w") or (k == "note" and v)}
                         for e in got]}
        assert all(a["n"] <= b["n"] for a, b in zip(sec["items"], sec["items"][1:])), \
            "%s is out of year order" % title
        if key == "sat":
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(entries), (len(ids), len(entries))
    assert sum(1 for e in entries if e["kind"] == "film") == len(films)
    assert sum(1 for e in entries if e["kind"] == "show") == \
        sum(s["seasons"] or 1 for s in shows) + \
        sum(len(v) for v in ANNOUNCED.values())
    assert all(key in {(s["title"], int(s["start"])) for s in shows}
               for key in list(SEASON_YEAR) + list(ANNOUNCED)), \
        "a SEASON_YEAR or ANNOUNCED key matches no series in the table"
    hours = sum(e["w"] for e in entries)

    prop = {
        "slug": SLUG,
        # CLU-508 declared this list a mega list, and build.py reads the flag
        # off the property file (`p["_mega"] = bool(p.get("mega"))`) to put it
        # in the home page's mega row instead of the card wall. The flag was
        # committed straight onto properties/marvel-animation.json and never added
        # here, so every run of this script silently deleted it and dropped the
        # list out of that row. CLU-552 swept the whole catalogue for the class:
        # these two were the last of the five mega lists still exposed to it.
        "mega": True,
        "title": "Marvel Animation",
        "subtitle": "every animated Marvel series and film, in release order",
        "kind": "shows & films",
        "popularity": 60,
        "year": "1966–",
        "blurb": "%d films and %d seasons of television, about %d hours, in "
                 "the order they came out."
                 % (sum(1 for e in entries if e["kind"] == "film"),
                    sum(1 for e in entries if e["kind"] == "show"),
                    round(hours)),
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#A03035",
        "accentDark": "#EF7A80",
        "tiers": False,
        "notes": [
            ["Animation only.", "The live-action series and the MCU films "
             "live in other lists; this is the cartoons — every animated "
             "Marvel series, season by season, plus the animated features."],
            ["No Spider-Verse.", "Into, Across and Beyond the Spider-Verse "
             "already live in the MCU Anthology property, so they are not "
             "repeated here."],
            ["Television is tracked season by season.", "A season's length is "
             "the series' episode count split evenly across its seasons at "
             "%d minutes each — the source gives a total rather than a "
             "per-season breakdown. Seasons are spread evenly between the "
             "years the series started and ended, which is exact for "
             "anything that ran annually and close for anything that did "
             "not." % EP_MINUTES],
            ["Bar widths are runtimes.", "Films use their real runtime from "
             "Wikidata. Avengers: Mightiest Friends and the next seasons of "
             "X-Men '97 and Your Friendly Neighborhood Spider-Man are not out "
             "yet, so they weigh nothing and cannot drag a group's pace."],
            ["Series only, features only.", "Pilots, television specials, "
             "motion comics, web shorts and the Lego specials are promos and "
             "curios rather than series, and recut episodes sold as films "
             "are not films; none of them are here."],
            "Series and film lists from Wikipedia's Marvel Comics "
            "publications tables, including the Malibu and Icon imprint "
            "tables — so Ultraforce, Men in Black and Super Crooks are "
            "here. Film runtimes and release dates from Wikidata.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / \
        ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d entries, %d hours"
          % (len(sections), len(ids), round(hours)))
    for s in sections:
        print("   %-28s %3d  %s" % (s["title"], len(s["items"]), s["sub"][:60]))


if __name__ == "__main__":
    main()
