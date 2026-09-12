#!/usr/bin/env python3
"""Generate properties/mcu-anthology.json.

    python3 tools/make_mcu_anthology.py

Every live-action Marvel film from Blade (1998) to Avengers: Doomsday (2026) in
release order, with the Marvel Studios series slotted in by premiere date, and a
tier on each entry saying how much the through-line needs it.

Sources, all machine-read rather than typed:
  - film list and years: Wikipedia, List of films based on Marvel Comics
    publications, live-action feature table
  - film runtimes and exact release dates: Wikidata P2047 and P577
  - show premiere dates: the Marvel Cinematic Universe Phase Four/Five/Six
    articles
  - episode counts: Wikidata P1113, with three season articles read directly
    where the property was missing

Runtime is the weight, in hours, so the bars are as wide as the thing takes.
Films use their real runtime. A season uses episodes times episode length,
which is a measured number for five of them and a stated assumption for the
rest — 45 minutes live action, 32 animated. Two unreleased entries weigh
nothing so they cannot drag a group's pace line.

Tiers sit on the item, not the section: a single year holds a film the whole
saga turns on and a spin-off nobody needs, and they belong next to each other
because that is the order they came out in.
"""
import json
import pathlib

SLUG = "mcu-anthology"

# T1 — the through-line. Skip it and something later stops making sense.
T1 = {
    "Iron Man", "The Avengers", "Captain America: The Winter Soldier",
    "Guardians of the Galaxy", "Avengers: Age of Ultron",
    "Captain America: Civil War", "Thor: Ragnarok", "Black Panther",
    "Avengers: Infinity War", "Avengers: Endgame", "Spider-Man: No Way Home",
    "Doctor Strange in the Multiverse of Madness", "Thunderbolts*",
    "The Fantastic Four: First Steps", "Avengers: Doomsday",
}
# T2 — properly connected: introduces someone or something a T1 entry uses.
T2 = {
    "Iron Man 2", "Thor", "Captain America: The First Avenger", "Ant-Man",
    "Doctor Strange", "Guardians of the Galaxy Vol. 2", "Spider-Man: Homecoming",
    "Ant-Man and the Wasp", "Captain Marvel", "Spider-Man: Far From Home",
    "Shang-Chi and the Legend of the Ten Rings", "Black Panther: Wakanda Forever",
    "Ant-Man and the Wasp: Quantumania", "Guardians of the Galaxy Vol. 3",
    "Deadpool & Wolverine", "Captain America: Brave New World",
    "Spider-Man: Brand New Day",
}
SHOW_T1 = {("Loki", "2021-06-09"), ("Loki", "2023-10-05")}
SHOW_T2 = {
    ("WandaVision", "2021-01-15"),
    ("The Falcon and the Winter Soldier", "2021-03-19"),
    ("Hawkeye", "2021-11-24"), ("Ms. Marvel", "2022-06-08"),
    ("Daredevil: Born Again", "2025-03-04"),
    ("Daredevil: Born Again", "2026-03-24"),
}

# A handful of one-line notes. Same rule as the comic lists: say what an entry
# is, never what happens in it.
NOTE = {
    "Blade": "The one that proved Marvel films could work at all",
    "Iron Man": "Where the MCU starts",
    "The Incredible Hulk": "MCU canon, and almost never referred to again",
    "The Avengers": "The first crossover, and the reason the model exists",
    "Captain America: The Winter Soldier": "The one that changed what these could be",
    "Avengers: Endgame": "The end of the Infinity Saga",
    "Deadpool & Wolverine": "Marvel Studios' first R-rated film",
    "Logan": "Outside the MCU, and the best of the Fox films",
    "Avengers: Doomsday": "Not out yet — 18 December 2026",
}
SHOW_NOTE = {
    ("Loki", "2021-06-09"): "Sets up the premise the whole Multiverse Saga runs on",
    ("VisionQuest", "2026-10-14"): "Not out yet — October 2026",
}


# The films Marvel Studios made. Everything else on this list shares a release
# window with a phase without being in one, and says so — a section called
# "Phase Two" should not quietly imply that The Wolverine was part of it.
MCU = {
    "Iron Man", "The Incredible Hulk", "Iron Man 2", "Thor",
    "Captain America: The First Avenger", "The Avengers", "Iron Man 3",
    "Thor: The Dark World", "Captain America: The Winter Soldier",
    "Guardians of the Galaxy", "Avengers: Age of Ultron", "Ant-Man",
    "Captain America: Civil War", "Doctor Strange",
    "Guardians of the Galaxy Vol. 2", "Spider-Man: Homecoming",
    "Thor: Ragnarok", "Black Panther", "Avengers: Infinity War",
    "Ant-Man and the Wasp", "Captain Marvel", "Avengers: Endgame",
    "Spider-Man: Far From Home", "Black Widow",
    "Shang-Chi and the Legend of the Ten Rings", "Eternals",
    "Spider-Man: No Way Home", "Doctor Strange in the Multiverse of Madness",
    "Thor: Love and Thunder", "Black Panther: Wakanda Forever",
    "Ant-Man and the Wasp: Quantumania", "Guardians of the Galaxy Vol. 3",
    "The Marvels", "Deadpool & Wolverine", "Captain America: Brave New World",
    "Thunderbolts*", "The Fantastic Four: First Steps",
    "Spider-Man: Brand New Day", "Avengers: Doomsday",
}


# Which phase each Marvel Studios film belongs to. Placing them by release date
# does not work: Iron Man's earliest Wikidata date is two days before the US
# opening, which pushed it out of Phase One, and The Avengers — the film Phase
# One ends with — landed in Phase Two. Everything that is not a Marvel Studios
# release has no phase at all and is placed by date, inside whichever era window
# these assignments produce.
PHASE = {
    "p1": ["Iron Man", "The Incredible Hulk", "Iron Man 2", "Thor",
           "Captain America: The First Avenger", "The Avengers"],
    "p2": ["Iron Man 3", "Thor: The Dark World",
           "Captain America: The Winter Soldier", "Guardians of the Galaxy",
           "Avengers: Age of Ultron", "Ant-Man"],
    "p3": ["Captain America: Civil War", "Doctor Strange",
           "Guardians of the Galaxy Vol. 2", "Spider-Man: Homecoming",
           "Thor: Ragnarok", "Black Panther", "Avengers: Infinity War",
           "Ant-Man and the Wasp", "Captain Marvel", "Avengers: Endgame",
           "Spider-Man: Far From Home"],
    "p4": ["Black Widow", "Shang-Chi and the Legend of the Ten Rings",
           "Eternals", "Spider-Man: No Way Home",
           "Doctor Strange in the Multiverse of Madness",
           "Thor: Love and Thunder", "Black Panther: Wakanda Forever"],
    "p5": ["Ant-Man and the Wasp: Quantumania", "Guardians of the Galaxy Vol. 3",
           "The Marvels", "Deadpool & Wolverine",
           "Captain America: Brave New World", "Thunderbolts*"],
    "p6": ["The Fantastic Four: First Steps", "Spider-Man: Brand New Day",
           "Avengers: Doomsday"],
}
FILM_PHASE = {t: k for k, v in PHASE.items() for t in v}
assert set(FILM_PHASE) == MCU, sorted(set(FILM_PHASE) ^ MCU)
SHOW_PHASE = {"Four": "p4", "Five": "p5", "Six": "p6"}

ANIMATED = {"What If...?", "Eyes of Wakanda", "Marvel Zombies",
            "Your Friendly Neighborhood Spider-Man"}

# episode counts read from the season articles where Wikidata had no P1113
FILL_EPISODES = {("Loki", "2023-10-05"): 6, ("What If...?", "2023-12-22"): 9,
                 ("Your Friendly Neighborhood Spider-Man", "2025-01-29"): 10}

# release-date boundaries, taken from the MCU's own phase markers
ERAS = [
    ("premcu", "Before the MCU", "1998–2008", "0000-00-00", "2008-05-01",
     "Blade, the Fox X-Men films and Sam Raimi's Spider-Man. None of it connects "
     "to what follows, and none of it is required — but it is where Marvel films "
     "start working."),
    # Phase One ends *with* The Avengers, whose Wikidata date is a few days
    # past the US opening, so the boundary sits after it and before the next film
    ("p1", "Phase One", "2008–2012", "2008-05-02", "2012-06-01",
     "Six films building to one crossover, plus everything else Marvel released "
     "alongside them."),
    ("p2", "Phase Two", "2012–2015", "2012-06-02", "2015-07-17", ""),
    ("p3", "Phase Three", "2015–2019", "2015-07-18", "2019-07-02",
     "The stretch the whole thing was built for, and the densest run of tier-1 "
     "entries on the list."),
    ("p4", "Phase Four", "2019–2022", "2019-07-03", "2022-11-11",
     "Where the Disney+ series start, and where the films stop assuming you have "
     "seen everything."),
    ("p5", "Phase Five", "2022–2025", "2022-11-12", "2025-05-02", ""),
    ("p6", "Phase Six", "2025–", "2025-05-03", "9999-99-99",
     "Still going. Two entries here are not out yet and weigh nothing, so they "
     "cannot make anyone late."),
]



# Wikidata's P577 carries every publication date a film has, including festival
# screenings and, for the unreleased ones, dates that have since moved. Taking
# the earliest put The Avengers in July 2011. The Wikipedia table's year is the
# authority for which year a film belongs to, so the date is only used to order
# within that year.
DATE_FIX = {
    # announced for 18 December 2026; Wikidata still carries an older slot
    "Avengers: Doomsday": "2026-12-18",
}


def film_date(f):
    if f["title"] in DATE_FIX:
        return DATE_FIX[f["title"]]
    d = f.get("released") or ""
    # a bare January 1st is Wikidata recording year precision, not a release
    # date — it put Punisher: War Zone, a December film, ahead of Iron Man
    if d[:4] == str(f["year"]) and not d.endswith("-01-01"):
        return d
    return "%d-07-01" % f["year"]      # mid-year, so it sorts inside its own year


def main():
    root = pathlib.Path(__file__).resolve().parent.parent
    # committed alongside the generator: scratch/ is gitignored, and the
    # Wikipedia and Wikidata calls that produced these are slow and rate-limited
    data = pathlib.Path(__file__).resolve().parent / "data"
    films = json.loads((data / "films.json").read_text(encoding="utf-8"))
    shows = json.loads((data / "shows.json").read_text(encoding="utf-8"))
    netflix = json.loads((data / "netflix.json").read_text(encoding="utf-8"))
    othertv = json.loads((data / "marveltv.json").read_text(encoding="utf-8"))
    spiderverse = json.loads((data / "spiderverse.json").read_text(encoding="utf-8"))

    entries = []
    for f in films:
        title, key = f["title"], f["title"]
        mins = f["runtime"] or 0
        entries.append({
            "id": "mv-f-%d-%s" % (f["year"], slug(title)),
            "t": title, "n": str(f["year"]),
            "w": round(mins / 60.0, 2),
            "tier": 1 if key in T1 else (2 if key in T2 else 3),
            "note": NOTE.get(key, ""),
            "date": film_date(f),
            "kind": "film", "mins": mins, "mcu": title in MCU,
            "phase": FILM_PHASE.get(title),
        })

    for s in shows:
        key = (s["title"], s["released"])
        eps = s["episodes"] or FILL_EPISODES.get(key) or 0
        per = s["ep_minutes"] or (32 if s["title"] in ANIMATED else 45)
        mins = 0 if key == ("VisionQuest", "2026-10-14") else eps * per
        season = ""
        same = [x for x in shows if x["title"] == s["title"]]
        if len(same) > 1:
            season = " season %d" % (sorted(x["released"] for x in same).index(s["released"]) + 1)
        entries.append({
            "id": "mv-t-%s-%s" % (s["released"][:4], slug(s["title"] + season)),
            "t": s["title"] + season,
            "n": s["released"][:4],
            "w": round(mins / 60.0, 2),
            "tier": 1 if key in SHOW_T1 else (2 if key in SHOW_T2 else 3),
            "note": SHOW_NOTE.get(key, "%d episodes" % eps if eps else ""),
            "date": s["released"], "kind": "show", "mins": mins, "mcu": True,
            "phase": SHOW_PHASE.get(s["phase"]),
        })

    for r in netflix:
        eps = r["episodes"] or 0
        mins = eps * (r["ep_minutes"] or 50)   # Marvel's Netflix hours run long
        n = sum(1 for x in netflix if x["title"] == r["title"])
        season = ""
        if n > 1:
            season = " season %d" % (sorted(x["released"] for x in netflix
                                            if x["title"] == r["title"]).index(r["released"]) + 1)
        entries.append({
            "id": "mv-n-%s" % slug(r["page"]),
            "t": r["title"] + season, "n": r["released"][:4],
            "w": round(mins / 60.0, 2),
            # Daredevil is the one Born Again reads on from; the rest are optional
            "tier": 2 if r["title"] == "Daredevil" else 3,
            "note": "%d episodes" % eps,
            "date": r["released"], "kind": "show", "mins": mins, "mcu": False,
            "phase": None,
        })

    for r in othertv:
        eps = r["episodes"]
        mins = eps * (r["ep_minutes"] or 45)
        # the page name already carries the season where there is more than one
        tail = r["page"].rsplit(" season ", 1)
        name = r["title"] + (" season " + tail[1] if len(tail) == 2 else "")
        if eps == 1:
            note = "A %d-minute special" % (r["ep_minutes"] or 45)
        else:
            note = "%d episodes" % eps
        if r["title"] == "X-Men '97":
            note = "Continues the 1992 cartoon, not the MCU · " + note
        entries.append({
            "id": "mv-o-%s" % slug(r["page"]),
            "t": name, "n": r["released"][:4],
            "w": round(mins / 60.0, 2),
            "tier": 3,
            "note": note,
            "date": r["released"], "kind": "show", "mins": mins,
            "mcu": r["studios"],
            "phase": SHOW_PHASE.get(r["phase"]) if r["studios"] else None,
        })

    # The Spider-Verse films are Sony and animated, so they are not in the
    # live-action feature table the rest of the films came from, and they are
    # not MCU — they carry the same marker as the other non-MCU entries.
    for r in spiderverse:
        mins = r["runtime"] or 0
        entries.append({
            "id": "mv-f-%s-%s" % (r["released"][:4], slug(r["title"])),
            "t": r["title"], "n": r["released"][:4],
            "w": round(mins / 60.0, 2),
            "tier": 3,
            "note": "Animated, and the best-reviewed Spider-Man films there are"
                    if "Into" in r["title"] else
                    ("Not out yet — June 2027" if not mins else ""),
            "date": r["released"], "kind": "film", "mins": mins,
            "mcu": False, "phase": None,
        })

    entries.sort(key=lambda e: (e["date"], e["kind"] == "show", e["t"]))

    # An era's window is whatever its declared members span, so the unphased
    # entries fall between them without any hand-tuned cut-off dates.
    window = {}
    for sid, *_ in ERAS:
        dates = [e["date"] for e in entries if e["phase"] == sid]
        if dates:
            window[sid] = (min(dates), max(dates))
    order = [sid for sid, *_ in ERAS if sid in window]
    for e in entries:
        if e["phase"]:
            continue
        placed = "premcu"
        for sid in order:
            if e["date"] >= window[sid][0]:
                placed = sid
        e["phase"] = placed

    sections = []
    for sid, title, years, lo, hi, intro in ERAS:
        got = [e for e in entries if e["phase"] == sid]
        if not got:
            continue
        films_n = sum(1 for e in got if e["kind"] == "film")
        shows_n = len(got) - films_n
        if sid != "premcu":
            for e in got:
                if e["mcu"]:
                    continue
                if e["note"].startswith("Continues the 1992"):
                    continue
                mark = ("Marvel Television — not part of %s" % title
                        if e["kind"] == "show"
                        else "Not an MCU film — it just came out during %s" % title)
                e["note"] = mark + (" · " + e["note"] if e["note"] else "")
        # the display span comes from the rows, not the phase-boundary dates —
        # a season that started after a phase closed (Agent Carter S2) or a
        # non-MCU film in the gap (Deadpool) belongs to the bucket by release
        # order, and the hand-set spans drifted from what the rows say
        row_years = sorted(int(str(e["n"])[:4]) for e in got)
        years = ("%d–" % row_years[0] if years.endswith("–")
                 else "%d–%d" % (row_years[0], row_years[-1]))
        sec = {
            "id": sid, "tier": 1, "title": title,
            "sub": "%s · %d film%s%s · %.0f hours"
                   % (years, films_n, "" if films_n == 1 else "s",
                      "" if not shows_n else " and %d season%s" % (shows_n, "" if shows_n == 1 else "s"),
                      sum(e["mins"] for e in got) / 60.0),
            "items": [{k: v for k, v in e.items()
                       if k in ("id", "t", "n", "w", "tier") or (k == "note" and v)}
                      for e in got],
        }
        if intro:
            sec["intro"] = intro
        if sid == "premcu":
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(entries), (len(ids), len(entries))
    hours = sum(e["mins"] for e in entries) / 60.0
    per = {1: 0, 2: 0, 3: 0}
    hrs = {1: 0.0, 2: 0.0, 3: 0.0}
    for e in entries:
        per[e["tier"]] += 1
        hrs[e["tier"]] += e["mins"] / 60.0

    prop = {
        "slug": SLUG,
        # CLU-508 declared this list a mega list, and build.py reads the flag
        # off the property file (`p["_mega"] = bool(p.get("mega"))`) to put it
        # in the home page's mega row instead of the card wall. The flag was
        # committed straight onto properties/mcu-anthology.json and never added
        # here, so every run of this script silently deleted it and dropped the
        # list out of that row. CLU-552 swept the whole catalogue for the class:
        # these two were the last of the five mega lists still exposed to it.
        "mega": True,
        "title": "MCU Anthology",
        # the list is wider than the MCU — Blade, the Fox X-Men films and the
        # Sony ones are all in it — so the subtitle carries that rather than
        # letting the name imply the list is MCU-only
        "subtitle": "every Marvel film in release order, MCU or not",
        "kind": "films & shows",
        "popularity": 95,
        "year": "1998–2026",
        "blurb": "%d films and %d seasons in the order they came out — about %d "
                 "hours, tiered by how much the story needs each one."
                 % (sum(1 for e in entries if e["kind"] == "film"),
                    sum(1 for e in entries if e["kind"] == "show"), round(hours)),
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#B3282D",
        "accentDark": "#F0666B",
        "tiers": True,
        "itemTiers": True,
        "paceTiers": [1, 2],
        "paceLabel": "the tier 3 entries",
        "notes": [
            ["Release order, not chronological.", "This is the order the films "
             "came out, which is the order they were made to be watched in. "
             "Every in-universe timeline reorders things that were written to "
             "surprise you."],
            ["Tiers are on each row, not each section.", "1 is the through-line: "
             "skip it and something later stops making sense. 2 is properly "
             "connected — it introduces someone or something a tier 1 entry "
             "uses. 3 is self-contained, or outside the MCU altogether. A single "
             "year holds all three, which is why the badge sits on the row."],
            ["Tier 1 alone is %d hours." % round(hrs[1]),
             "Tiers 1 and 2 together are %d hours across %d entries. Everything "
             "on the page is %d hours. The finish date only counts tiers 1 and 2 "
             "— there is a checkbox under the bar if you want the rest included."
             % (round(hrs[1] + hrs[2]), per[1] + per[2], round(hours))],
            ["Bar widths are runtimes.", "Films use their real runtime from "
             "Wikidata. A season uses episodes times episode length, which is a "
             "measured figure for five of them and a stated assumption for the "
             "rest — 45 minutes live action, 32 animated. Avengers: Doomsday and "
             "VisionQuest are not out yet and weigh nothing."],
            ["Everything is here.", "The films, the Disney+ series, the Netflix "
             "run, the ABC and Hulu shows, the Special Presentations and "
             "X-Men '97 — which is on the page despite continuing the 1992 "
             "cartoon rather than the MCU, and says so on its row. Runaways is "
             "one entry rather than three: its article gives per-season episode "
             "counts but only season one's date."],
            "Film list from Wikipedia's live-action Marvel features table; "
            "runtimes and release dates from Wikidata; show premieres from the "
            "MCU phase articles and episode counts from Wikidata. The tier "
            "assignments are a judgement call, not a source.",
        ],
        "sections": sections,
    }

    out = root / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d entries, %.0f hours" % (len(sections), len(ids), hours))
    print("  T1 %3d (%3.0fh)   T2 %3d (%3.0fh)   T3 %3d (%3.0fh)"
          % (per[1], hrs[1], per[2], hrs[2], per[3], hrs[3]))
    for s in sections:
        print("   %-18s %3d entries" % (s["title"], len(s["items"])))


def slug(t):
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


if __name__ == "__main__":
    main()
