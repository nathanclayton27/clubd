#!/usr/bin/env python3
"""Generate properties/time-loops.json — the group's Groundhog Day collection.

    python3 tools/make_timeloops.py

Three layers, merged:
  - the group's own Discord thread (the original 27 rows — their ids are
    load-bearing and asserted unchanged, ticks live on them)
  - Wikipedia's "List of films featuring time loops"
  - two Reddit threads the Discord recommended: r/movies' "I watched 135 time
    loop movies" (1flvzco) and r/television's loop-episode compilation
    (1ilm56j)

scratch/loops2/ holds the pipeline: collect_films.py merged and deduped the
film lists and resolved Wikidata runtimes; verify_eps.py checked every claimed
episode against Wikipedia's own episode tables before it got a row (which is
how "S15E24 Yuletide Repeat" became American Dad's S17E24 "Yule. Tide.
Repeat." and Quantum Leap's "Live, Die, Repeat" became "Leap. Die. Repeat.");
enrich_runtimes.py added runtimes for reddit-only films with a verify-by-name
gate. Provenance rides on every row as tags, so the original house list is
one chip away.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib.prop import slug, normt

SLUG = "time-loops"
DATA = pathlib.Path(__file__).resolve().parent / "data"

T_HOUSE = "Group picks"
T_WIKI = "Wikipedia list"
T_R135 = "135-movie thread"
T_EPTH = "Episode thread"

# The original rows. Titles/years exactly as first shipped — the ids derive
# from them. (title, year, runtime min, note, house_addition)
FILMS = [
    ("Groundhog Day", 1993, 101, "Where the name comes from", 0),
    ("12:01", 1993, 92, "The TV movie that aired the same year — its short-film "
     "ancestor predates Groundhog Day", 1),
    ("Run Lola Run", 1998, 81, "Three runs at twenty minutes", 0),
    ("Triangle", 2009, 99, "The horror one people argue about", 1),
    ("Source Code", 2011, 93, "Eight minutes at a time", 0),
    ("Edge of Tomorrow", 2014, 113, "", 0),
    ("ARQ", 2016, 98, "", 0),
    ("Before I Fall", 2017, 99, "", 1),
    ("Happy Death Day", 2017, 96, "The loop as a slasher", 0),
    ("The Endless", 2017, 111, "Loops inside loops, on a cult compound", 1),
    ("Happy Death Day 2U", 2019, 100, "", 0),
    ("Palm Springs", 2020, 90, "", 0),
    ("Boss Level", 2020, 104, "", 0),
    ("Two Distant Strangers", 2020, 32, "The Oscar-winning short", 0),
    ("A Map of Tiny Perfect Things", 2021, 99, "", 0),
]

# Display-title corrections that must NOT touch the id (ticks key on ids)
TITLE_FIX = {"A Map of Tiny Perfect Things": "The Map of Tiny Perfect Things"}

# (show, episode title, S, E, year, note, house_addition, also_in_thread)
EPISODES = [
    ("Star Trek: The Next Generation", "Cause and Effect", 5, 18, 1992, "", 0, 1),
    ("Xena: Warrior Princess", "Been There, Done That", 3, 2, 1997, "", 1, 1),
    ("The X-Files", "Monday", 6, 14, 1999, "", 0, 1),
    ("Stargate SG-1", "Window of Opportunity", 4, 6, 2000, "", 0, 1),
    ("Buffy the Vampire Slayer", "Life Serial", 6, 5, 2001, "", 1, 1),
    ("Supernatural", "Mystery Spot", 3, 11, 2008, "", 0, 1),
    ("Fringe", "White Tulip", 2, 18, 2010, "", 1, 0),
    ("Doctor Who", "Heaven Sent", 9, 11, 2015, "", 0, 0),
    ("Legends of Tomorrow", "Here I Go Again", 3, 11, 2018, "", 0, 1),
    ("Agents of S.H.I.E.L.D.", "As I Have Always Been", 7, 9, 2020, "", 0, 1),
    ("Tales of the Walking Dead", "Blair / Gina", 1, 2, 2022,
     "The series' time-loop episode", 0, 1),
]

# terse factual notes for a few of the sourced episode rows
EP_NOTES = {
    ("American Dad!", "Yule. Tide. Repeat."): "The show's 300th episode",
    ("Animaniacs", "Groundmouse Day"):
        "The Pinky and the Brain segment of a three-part episode",
    ("The Simpsons", "Treehouse of Horror V"):
        "For the “Time and Punishment” segment",
    ("Quantum Leap", "Leap. Die. Repeat."): "The 2022 revival",
    ("Fringe", "And Those We've Left Behind"):
        "The thread's pick; White Tulip is the house one",
}

SERIES_NOTES = {
    "Day Break": "Taye Diggs relives the day he is framed for murder",
    "Hounded": "CBBC, and prime nonsense",
    "The Lazarus Project": "The loop as a doomsday-prevention job",
    "Looped": "Animated — two boys loop the same Saturday",
    "No Through Road": "A web series before that was normal",
    "Reset": "The Chinese one — a bus that keeps exploding",
    "Worst Year of My Life, Again!": "Australian teen sitcom, a full year loop",
    "Russian Doll": "Two seasons; the first is the loop",
}

# language notes for wiki-listed films the reddit thread didn't mark
COUNTRY_LANG = {"France": "French", "Japan": "Japanese", "Russia": "Russian",
                "Germany": "German", "Sweden": "Swedish", "Italy": "Italian",
                "Spain": "Spanish", "South Korea": "Korean", "China": "Chinese",
                "India": "Indian", "Egypt": "Arabic", "Philippines": "Filipino",
                "Indonesia": "Indonesian", "Kazakhstan": "Kazakh",
                "Thailand": "Thai"}

SHORTS = {"12:01 PM", "Groundhog Day for a Black Man", "Two Distant Strangers"}

DECADES = [
    ("pre", "Before Groundhog Day", None, 1992,
     "The loop predates the name — a French experiment, two Japanese "
     "classics, a Soviet drama and the Oscar-nominated short."),
    ("nineties", "The '90s", 1993, 1999,
     "Groundhog Day lands, and the first wave of echoes follows it."),
    ("aughts", "The 2000s", 2000, 2009, ""),
    ("tens", "The 2010s", 2010, 2019, ""),
    ("twenties", "The 2020s", 2020, None, ""),
]


HOUSE = "Added here — shout if it doesn't belong"
LEGACY_IDS = [
    "loop-f-1993-12-01", "loop-f-1993-groundhog-day", "loop-f-1998-run-lola-run",
    "loop-f-2009-triangle", "loop-f-2011-source-code",
    "loop-f-2014-edge-of-tomorrow", "loop-f-2016-arq", "loop-f-2017-before-i-fall",
    "loop-f-2017-happy-death-day", "loop-f-2017-the-endless",
    "loop-f-2019-happy-death-day-2u", "loop-f-2020-boss-level",
    "loop-f-2020-palm-springs", "loop-f-2020-two-distant-strangers",
    "loop-f-2021-a-map-of-tiny-perfect-things",
    "loop-e-1992-star-trek-the-next-generation-cause-and-effect",
    "loop-e-1997-xena-warrior-princess-been-there-done-that",
    "loop-e-1999-the-x-files-monday",
    "loop-e-2000-stargate-sg-1-window-of-opportunity",
    "loop-e-2001-buffy-the-vampire-slayer-life-serial",
    "loop-e-2008-supernatural-mystery-spot", "loop-e-2010-fringe-white-tulip",
    "loop-e-2015-doctor-who-heaven-sent",
    "loop-e-2018-legends-of-tomorrow-here-i-go-again",
    "loop-e-2020-agents-of-s-h-i-e-l-d-as-i-have-always-been",
    "loop-e-2022-tales-of-the-walking-dead-blair-gina",
    "loop-s-2019-russian-doll",
]


def main():
    merged = json.loads((DATA / "timeloop-films.json").read_text(encoding="utf-8"))
    new_eps = json.loads((DATA / "timeloop-eps.json").read_text(encoding="utf-8"))
    series = json.loads((DATA / "timeloop-series.json").read_text(encoding="utf-8"))

    # ---- films: house rows first, sourced rows joined onto them ----
    house_by_key = {}
    for t, year, mins, note, house in FILMS:
        for dy in (0, 1, -1):
            house_by_key[(normt(t), year + dy)] = (t, year, mins, note, house)

    rows = []
    matched_house = set()
    for f in merged:
        key = next(((normt(f["t"]), f["year"] + dy) for dy in (0, 1, -1)
                    if (normt(f["t"]), f["year"] + dy) in house_by_key), None)
        tags = ([T_WIKI] if f["wiki"] else []) + ([T_R135] if f["reddit"] else [])
        if key:
            t, year, mins, note, house = house_by_key[key]
            matched_house.add(t)
            bits = [b for b in (note, "%d min" % mins, HOUSE if house else "") if b]
            rows.append({"id": "loop-f-%d-%s" % (year, slug(t)),
                         "t": TITLE_FIX.get(t, t), "year": year,
                         "note": " · ".join(bits), "tags": [T_HOUSE] + tags})
        else:
            bits = []
            lang = f.get("lang") or COUNTRY_LANG.get(
                f.get("country", "").split("<br/>")[0], "")
            if lang:
                bits.append(lang)
            if f["t"] in SHORTS:
                bits.append("A short")
            if f.get("runtime"):
                bits.append("%d min" % f["runtime"])
            rows.append({"id": "loop-f-%d-%s" % (f["year"], slug(f["t"])),
                         "t": f["t"], "year": f["year"],
                         "note": " · ".join(bits), "tags": tags})
    assert matched_house == {t for t, *_ in FILMS}, \
        "house films missing from the merge: %s" % ({t for t, *_ in FILMS} - matched_house)

    film_sections = []
    for key, title, lo, hi, intro in DECADES:
        got = sorted((r for r in rows
                      if (lo is None or r["year"] >= lo)
                      and (hi is None or r["year"] <= hi)),
                     key=lambda r: (r["year"], normt(r["t"])))
        assert got, key
        items = [{"id": r["id"], "t": r["t"], "n": str(r["year"]),
                  **({"note": r["note"]} if r["note"] else {}),
                  "tags": r["tags"]} for r in got]
        sec = {"id": key, "title": title,
               "sub": "%d–%d · %d films" % (got[0]["year"], got[-1]["year"],
                                            len(got)),
               "items": items}
        if intro:
            sec["intro"] = intro
        if key == "pre":
            sec["open"] = True
        film_sections.append(sec)

    # ---- episodes ----
    ep_rows = []
    for show, t, s, e, year, note, house, in_thread in EPISODES:
        bits = [b for b in (note, HOUSE if house else "") if b]
        ep_rows.append({
            "id": "loop-e-%d-%s" % (year, slug(show + "-" + t)),
            "t": "%s — “%s”" % (show, t), "n": "S%dE%d" % (s, e), "year": year,
            **({"note": " · ".join(bits)} if bits else {}),
            "tags": [T_HOUSE] + ([T_EPTH] if in_thread else [])})
    for v in new_eps:
        note = EP_NOTES.get((v["show"], v["t"]), "")
        ep_rows.append({
            "id": "loop-e-%d-%s" % (v["year"], slug(v["show"] + "-" + v["t"])),
            "t": "%s — “%s”" % (v["show"], v["t"]),
            "n": "S%dE%d" % (v["s"], v["e"]), "year": v["year"],
            **({"note": note} if note else {}), "tags": [T_EPTH]})
    ep_rows.sort(key=lambda x: (x["year"], x["t"]))
    ep_items = [{k: v for k, v in r.items() if k != "year"} for r in ep_rows]

    # ---- series ----
    ser_rows = [{"id": "loop-s-2019-russian-doll", "t": "Russian Doll",
                 "year": 2019, "n": "2019–22",
                 "note": SERIES_NOTES["Russian Doll"],
                 "tags": [T_HOUSE, T_EPTH, T_R135]}]
    for sr in series:
        note = SERIES_NOTES[sr["t"]]
        ser_rows.append({"id": "loop-s-%d-%s" % (sr["year"], slug(sr["t"])),
                         "t": sr["t"], "year": sr["year"], "n": str(sr["year"]),
                         "note": note, "tags": [T_R135]})
    ser_rows.sort(key=lambda x: (x["year"], x["t"]))
    ser_items = [{k: v for k, v in r.items() if k != "year"} for r in ser_rows]

    sections = film_sections + [
        {"id": "episodes", "title": "Single episodes",
         "sub": "%d–%d · %d rows, one loop each"
                % (ep_rows[0]["year"], ep_rows[-1]["year"], len(ep_items)),
         "intro": "Each row names its show, season and number — the loop "
                  "episodes were built to work cold, so nobody has to watch "
                  "anything else to get there.",
         "items": ep_items},
        {"id": "series", "title": "Whole series about it",
         "sub": "when one episode was never going to be enough",
         "items": ser_items},
    ]

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), \
        [i for i in ids if ids.count(i) > 1][:4]
    for lid in LEGACY_IDS:
        assert lid in ids, "legacy id lost: %s" % lid
    n_films = sum(len(s["items"]) for s in film_sections)
    assert n_films == len(merged), (n_films, len(merged))
    assert len(ep_items) == len(EPISODES) + len(new_eps)
    used = {t for s in sections for x in s["items"] for t in x["tags"]}
    values = [T_HOUSE, T_WIKI, T_R135, T_EPTH]
    assert used == set(values), used ^ set(values)
    assert all(x.get("tags") for s in sections for x in s["items"])
    house = sum(1 for s in sections for x in s["items"]
                if HOUSE in (x.get("note") or ""))

    prop = {
        "slug": SLUG,
        "title": "Time Loops",
        "subtitle": "the same day, again — films, episodes, whole shows",
        "kind": "films & episodes",
        "popularity": 36,
        "year": "1963–",
        "blurb": "%d films, %d single episodes and %d whole series where the "
                 "day repeats — the group's picks plus every list the Discord "
                 "brought in. Watch in any order."
                 % (n_films, len(ep_items), len(ser_items)),
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": "#6B2E7A",
        "accentDark": "#C08FE0",
        "tiers": False,
        "random": True,
        "filter": {"key": "src", "label": "From", "mode": "include",
                   "values": values},
        "notes": [
            ["No order.", "Pick whatever tonight feels like — nothing leads "
             "to anything else and nothing is weighted, because this is a "
             "grab bag, not a schedule. Runtimes ride on the rows where a "
             "source had one."],
            ["The chips are provenance.", "Group picks is the original house "
             "list from the Discord thread; the rest mark Wikipedia's "
             "time-loop film list, r/movies' 135-film watch-through and "
             "r/television's episode compilation. Rows can carry several."],
            ["Everything is verified.", "Every episode's season and number "
             "were read out of Wikipedia's own tables before it got a row — "
             "which renamed a few: the thread's \"S15E24 Yuletide Repeat\" "
             "is really American Dad's S17E24 \"Yule. Tide. Repeat.\", and "
             "Quantum Leap's loop is \"Leap. Die. Repeat.\""],
            ["House additions are marked.", "%d entries were added here "
             "beyond any list and say so on the row — veto freely." % house],
            "Assembled by the group in Discord, then grown from Wikipedia's "
            "List of films featuring time loops and two Reddit compilations "
            "the thread recommended.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json — %d entries (%d films, %d episodes, %d series)"
          % (SLUG, len(ids), n_films, len(ep_items), len(ser_items)))
    for s in sections:
        print("   %-24s %3d  %s" % (s["title"], len(s["items"]), s["sub"][:44]))


if __name__ == "__main__":
    main()
