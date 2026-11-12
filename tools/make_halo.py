#!/usr/bin/env python3
"""Generate properties/halo.json.

    python3 tools/make_halo.py

The Halo campaigns in release order — Combat Evolved through Infinite,
with the two Halo Wars strategy campaigns as optional rows.

Which games exist and their release years come from Wikipedia's Halo
(franchise) article and its game timeline
(scratch/agent-games1/wiki/halo.wiki). Hours are HowLongToBeat main-story
figures — story only, the house standard — read from
tools/data/halo.json, collected by scratch/agent-games1/fetch_hltb.py and
verified by name (this generator refuses a record whose name is not what
it expects, and cross-checks HLTB's release year against Wikipedia's).

The Master Chief Collection note is stated as fact: it is the practical
way into everything up to Halo 4. Anniversary remasters, Spartan Assault/
Strike and the arcade releases are not campaigns in their own right and
are not rows. Halo: Campaign Evolved (2026) remakes Combat Evolved's ten
missions and adds three prequel ones; it is a note on the CE row, not a
row, so the same story is not counted twice (CLU-608, 2026-11-12).
"""
import json
import pathlib

SLUG = "halo"

# key in the data file, display title, Wikipedia year, note, opt
BUNGIE = [
    ("ce", "Halo: Combat Evolved", 2001,
     "The ring, the Flood, and the warthog run. The 2026 remake, Halo: "
     "Campaign Evolved, ticks this row too — it adds three prequel "
     "missions", 0),
    ("halo2", "Halo 2", 2004,
     "The Arbiter's half is the surprise; ends on the series' famous "
     "cliffhanger", 0),
    ("halo3", "Halo 3", 2007,
     "The trilogy's close — finish the fight", 0),
    ("wars", "Halo Wars", 2009,
     "Real-time strategy spin-off campaign, set twenty years before the "
     "ring", 1),
    ("odst", "Halo 3: ODST", 2009,
     "A night in New Mombasa without the armor — the moody side story",
     0),
    ("reach", "Halo: Reach", 2010,
     "The prequel tragedy, and Bungie's farewell. You know how it ends.",
     0),
]

FOURTREE = [
    ("halo4", "Halo 4", 2012,
     "343 takes over; the Didact, and the Chief-and-Cortana story", 0),
    ("halo5", "Halo 5: Guardians", 2015,
     "The one that is not in the Master Chief Collection — Xbox only",
     0),
    ("wars2", "Halo Wars 2", 2017,
     "Strategy again — the Banished arrive, and Infinite leans on them",
     1),
    ("infinite", "Halo Infinite", 2021,
     "The open-ring campaign; the Banished war continues", 0),
]

SECTIONS = [
    ("bungie", "The Bungie years",
     "The original trilogy and its two side stories, 2001–2010.", BUNGIE),
    ("threefortythree", "343 Industries",
     "The Reclaimer era, 2012 on.", FOURTREE),
]


def norm(s):
    s = (s or "").replace("’", "'").replace("–", "-")
    return " ".join(s.casefold().split())


def main():
    data = json.loads((pathlib.Path(__file__).resolve().parent / "data"
                       / "halo.json").read_text(encoding="utf-8"))

    sections = []
    for sec_id, sec_title, intro, roster in SECTIONS:
        years = [y for _, _, y, _, _ in roster]
        assert years == sorted(years), "%s roster out of release order" % sec_id
        items = []
        for key, title, year, note, opt in roster:
            rec = data.get(key)
            assert rec, "no HLTB record for %s" % key
            assert norm(rec["name"]) == norm(title), \
                "record mismatch for %s: %r" % (key, rec["name"])
            assert abs(int(rec["year"]) - year) <= 1, \
                "year mismatch for %s: wiki %d, hltb %s" % (key, year, rec["year"])
            x = {"id": "halo-%s" % key, "t": title, "n": str(year),
                 "w": rec["main_h"]}
            if note:
                x["note"] = note
            if opt:
                x["opt"] = 1
            items.append(x)
        hours = sum(x["w"] for x in items)
        sections.append({
            "id": sec_id, "title": sec_title,
            "sub": "%d–%d · %d campaigns · %d hours story"
                   % (years[0], years[-1], len(items), round(hours)),
            "intro": intro,
            "items": items,
        })
    sections[0]["open"] = True

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(BUNGIE) + len(FOURTREE) == 10, (len(ids),)

    hours = sum(x["w"] for s in sections for x in s["items"])
    fps = sum(x["w"] for s in sections for x in s["items"] if not x.get("opt"))

    prop = {
        "slug": SLUG,
        "title": "Halo",
        "subtitle": "the campaigns in release order, Wars included",
        "kind": "games",
        "popularity": 76,
        "year": "2001–",
        "blurb": "%d campaigns — about %d hours of story, %d of it the "
                 "shooter line." % (len(ids), round(hours), round(fps)),
        "unit": {"one": "game", "many": "games"},
        "verb": {"base": "play", "past": "played", "ing": "playing"},
        "itemOrder": "number-first",
        "accent": "#4A7040",
        "accentDark": "#7AC8F5",
        "tiers": False,
        "notes": [
            ["Campaigns, in release order.", "This list is the stories; "
             "multiplayer is its own hobby and keeps its own hours. ODST "
             "and Reach are side and prequel stories, but release order "
             "is how the series was meant to unfold and the recaps "
             "assume it."],
            ["The Master Chief Collection is the way in.", "As a matter "
             "of fact it bundles Combat Evolved, 2, 3, ODST, Reach and 4 "
             "— remastered, on PC and Xbox. Halo 5 is the exception: "
             "never added, Xbox only. Infinite stands alone."],
            ["The Wars games are optional.", "Both are real-time strategy "
             "— a different genre wearing the same story. Wars 2 sets up "
             "the Banished that Infinite fights; a recap covers it if "
             "strategy isn't your thing."],
            ["Hours are story only.", "HowLongToBeat main-story figures — "
             "normal difficulty, no Legendary runs, no multiplayer."],
            "Game list and years from Wikipedia's Halo (franchise) "
            "article; hours from HowLongToBeat main-story figures, "
            "verified by name.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d campaigns, %d hours (%d shooter line)"
          % (len(sections), len(ids), round(hours), round(fps)))
    for s in sections:
        print("   %-18s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
