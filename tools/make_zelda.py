#!/usr/bin/env python3
"""Generate properties/zelda.json.

    python3 tools/make_zelda.py

The Legend of Zelda in release order: the mainline 21 from the 1986 original
through Echoes of Wisdom, plus the remakes and spin-offs worth a row, marked
as such.

Which games exist and their release years come from Wikipedia's "List of The
Legend of Zelda media" (scratch/zelda/media.wiki). Hours are HowLongToBeat
main-story figures — story only, the house rule — read from
tools/data/zelda.json, collected by scratch/zelda/fetch_hltb.py (the 2026
Ocarina of Time remake, added 2026-11-11, by tools/gwlib/hltb.py: HLTB id
187305, Switch 2) and verified by name (this generator refuses a record
whose name is not what it expects, and cross-checks HLTB's release year
against Wikipedia's).

Tiers are necessity, stated judgment:
  1  the console 3D line (Ocarina through Tears) plus the 2D pillars that
     built it: the original, A Link to the Past, Link's Awakening
  2  the rest of mainline 2D — the DS pair included
  3  spin-offs and remakes, each marked for what it is

One honest fudge: Four Swords shipped in 2002 only as the second half of a
Game Boy Advance cart with A Link to the Past, and HLTB has no entry for that
release on its own. The row sits at 2002 where the game belongs, and its
hours are the name-verified Four Swords Anniversary Edition — the 2011 DSi
standalone of the same game. The row's note says so.
"""
import json
import pathlib

SLUG = "zelda"

Z = "The Legend of Zelda: "

# key in the data file, display title, Wikipedia year, tier, note, opt
ROSTER = [
    ("loz", "The Legend of Zelda", 1986, 1,
     "NES. Where it all starts — still the most open the series was until "
     "Breath of the Wild.", 0),
    ("zelda2", "Zelda II: The Adventure of Link", 1987, 2,
     "The side-scrolling RPG detour, and the hardest game on this list", 0),
    ("alttp", Z + "A Link to the Past", 1991, 1,
     "SNES. The top-down blueprint every 2D Zelda refines.", 0),
    ("la", Z + "Link's Awakening", 1993, 1,
     "Game Boy. Small, strange, and the series' heart; the 2019 row rebuilds "
     "it.", 0),
    ("oot", Z + "Ocarina of Time", 1998, 1,
     "N64. The 3D template — for the series and for everyone else.", 0),
    ("mm", Z + "Majora's Mask", 2000, 1,
     "Built from Ocarina's parts and nothing like it; the three-day loop", 0),
    ("oos", Z + "Oracle of Seasons", 2001, 2,
     "The Capcom-built Game Boy Color pair, action half", 0),
    ("ooa", Z + "Oracle of Ages", 2001, 2,
     "Puzzle half of the pair; the two link into one long game", 0),
    ("fsae", Z + "Four Swords", 2002, 2,
     "The four-player one, born on a 2002 GBA cart with A Link to the Past; "
     "hours are the DSi Anniversary Edition, its standalone release", 0),
    ("ww", Z + "The Wind Waker", 2002, 1,
     "GameCube. The toon reinvention — divisive then, beloved now.", 0),
    ("fsa", Z + "Four Swords Adventures", 2004, 2,
     "GameCube multiplayer sequel to Four Swords; playable solo", 0),
    ("mc", Z + "The Minish Cap", 2004, 2,
     "Capcom again, on GBA — the last of the old-style handhelds", 0),
    ("tp", Z + "Twilight Princess", 2006, 1,
     "The dark-horse epic; the HD row is the easier way to play it now", 0),
    ("ph", Z + "Phantom Hourglass", 2007, 2,
     "DS. The touch-controlled follow-up to Wind Waker.", 0),
    ("st", Z + "Spirit Tracks", 2009, 2,
     "DS again — the train one, better than that sounds", 0),
    ("oot3d", Z + "Ocarina of Time 3D", 2011, 3,
     "Remake — the 3DS rebuild of Ocarina of Time, and the friendliest way "
     "into it", 1),
    ("ss", Z + "Skyward Sword", 2011, 1,
     "Wii. The origin-story one; the HD row fixes the controls.", 0),
    ("wwhd", Z + "The Wind Waker HD", 2013, 3,
     "Remaster — Wind Waker on Wii U, with the slow parts sanded down", 1),
    ("albw", Z + "A Link Between Worlds", 2013, 2,
     "3DS. A Link to the Past's map, rethought — the best 2D entry in "
     "decades.", 0),
    ("hw", "Hyrule Warriors", 2014, 3,
     "Spin-off — the Warriors crossover, pure fanservice by the thousand", 1),
    ("mm3d", Z + "Majora's Mask 3D", 2015, 3,
     "Remake — Majora's Mask on 3DS", 1),
    ("tfh", Z + "Tri Force Heroes", 2015, 2,
     "The three-player dress-up dungeon crawler; thin solo", 0),
    ("tphd", Z + "Twilight Princess HD", 2016, 3,
     "Remaster — Twilight Princess on Wii U", 1),
    ("botw", Z + "Breath of the Wild", 2017, 1,
     "Switch. The open-air reinvention; everything after answers to it.", 0),
    ("cadence", "Cadence of Hyrule", 2019, 3,
     "Spin-off — the Crypt of the NecroDancer rhythm crossover, and a real "
     "Zelda in miniature", 1),
    ("la2019", Z + "Link's Awakening", 2019, 3,
     "Remake — the 2019 Switch rebuild of the Game Boy game", 1),
    ("aoc", "Hyrule Warriors: Age of Calamity", 2020, 3,
     "Spin-off — Warriors again, set around Breath of the Wild", 1),
    ("sshd", Z + "Skyward Sword HD", 2021, 3,
     "Remaster — Skyward Sword with the controls fixed", 1),
    ("totk", Z + "Tears of the Kingdom", 2023, 1,
     "Breath of the Wild's direct sequel — the one hard sequel-order rule "
     "here", 0),
    ("eow", Z + "Echoes of Wisdom", 2024, 2,
     "Top-down again, and Zelda herself plays the lead", 0),
    ("aoi", "Hyrule Warriors: Age of Imprisonment", 2025, 3,
     "Spin-off — the Switch 2 Warriors entry, grown from Tears of the "
     "Kingdom", 1),
    ("oot2026", Z + "Ocarina of Time", 2026, 3,
     "Remake — the Switch 2 rebuild of Ocarina of Time", 1),
]

# where the data file's verified name is not the display title
EXPECT = {"fsae": Z + "Four Swords Anniversary Edition"}
# where HLTB's release year is allowed to differ from Wikipedia's
YEAR_EXCUSED = {"fsae"}

ERAS = [
    ("founding", "The 2D foundations", 1986, 1997,
     "Four games that built the vocabulary: the original, its odd sequel, "
     "and the two that perfected top-down Zelda."),
    ("n64", "The Nintendo 64 turn and the Capcom handhelds", 1998, 2001,
     "The 3D leap, and the two Game Boy Color stories Capcom built in its "
     "shadow."),
    ("gcds", "GameCube to DS", 2002, 2010,
     "Toon and Twilight, the multiplayer experiments, and the two DS "
     "follow-ups."),
    ("revisits", "Skyward Sword and the revisits", 2011, 2016,
     "The pre-Switch line closes while 3DS and Wii U rebuild the classics."),
    ("switch", "The Switch era", 2017, 9999,
     "The open-air reinvention and everything since."),
]


def main():
    data = json.loads((pathlib.Path(__file__).resolve().parent / "data"
                       / "zelda.json").read_text(encoding="utf-8"))

    entries = []
    for key, title, year, tier, note, opt in ROSTER:
        rec = data.get(key)
        assert rec, "no HLTB record for %s" % key
        want = EXPECT.get(key, title).replace("’", "'").lower()
        got = rec["name"].replace("’", "'").lower()
        assert got == want, "record mismatch for %s: %r" % (key, rec["name"])
        assert key in YEAR_EXCUSED or abs(int(rec["year"]) - year) <= 1, \
            "year mismatch for %s: wiki %d, hltb %s" % (key, year, rec["year"])
        x = {"id": "zelda-%s" % key, "t": title, "n": str(year),
             "w": rec["main_h"], "tier": tier, "year": year}
        if note:
            x["note"] = note
        if opt:
            x["opt"] = 1
        entries.append(x)

    years = [e["year"] for e in entries]
    assert years == sorted(years), "roster is out of release order"

    sections = []
    for key, title, lo, hi, intro in ERAS:
        got = [e for e in entries if lo <= e["year"] <= hi]
        if not got:
            continue
        hours = sum(e["w"] for e in got)
        sec = {"id": key, "title": title,
               "sub": "%d–%d · %d games · %d hours story"
                      % (got[0]["year"], got[-1]["year"], len(got), round(hours)),
               "intro": intro,
               "items": [{k: v for k, v in e.items()
                          if k in ("id", "t", "n", "w", "tier", "opt", "note")}
                         for e in got]}
        if key == "founding":
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(ROSTER), (len(ids), len(ROSTER))
    t1 = [x for s in sections for x in s["items"] if x["tier"] == 1]
    t3 = [x for s in sections for x in s["items"] if x["tier"] == 3]
    assert len(t1) == 10, "the pillars and the 3D line should be 10, got %d" % len(t1)
    assert len(ROSTER) - len(t3) == 21, "mainline should be 21 games"
    assert all(x.get("opt") for x in t3), "tier-3 rows are all optional"

    hours = sum(x["w"] for s in sections for x in s["items"])
    mainline = sum(x["w"] for s in sections for x in s["items"] if x["tier"] < 3)
    spine = sum(x["w"] for x in t1)

    prop = {
        "slug": SLUG,
        "title": "The Legend of Zelda",
        "subtitle": "mainline in release order, remakes and spin-offs marked",
        "kind": "games",
        "popularity": 92,
        "year": "1986–",
        "blurb": "%d games — the mainline %d plus remakes and spin-offs, "
                 "about %d hours of story, %d of it mainline."
                 % (len(ROSTER), len(ROSTER) - len(t3), round(hours),
                    round(mainline)),
        "unit": {"one": "game", "many": "games"},
        "verb": {"base": "play", "past": "played", "ing": "playing"},
        "itemOrder": "number-first",
        "accent": "#2E6B4F",
        "accentDark": "#7FD0A8",
        "tiers": True,
        "itemTiers": True,
        "paceTiers": [1, 2],
        "paceLabel": "the remakes and spin-offs",
        "notes": [
            ["Release order, on purpose.", "Zelda's timeline is an "
             "after-the-fact curiosity — the games were made as riffs on a "
             "legend, not chapters of one story. Release order is how the "
             "ideas actually develop, and the only hard sequencing rule it "
             "has to respect comes free: Tears of the Kingdom after Breath "
             "of the Wild."],
            ["Hours are story only.", "HowLongToBeat main-story figures, as "
             "asked — no shrine-hunting, no completionist padding. For the "
             "two open-world games that undercounts how people actually "
             "play them, which is the point of a floor."],
            ["Tiers, and the judgment in them.", "1 is the console 3D line "
             "— Ocarina of Time through Tears of the Kingdom — plus the "
             "three 2D pillars it grew from: the 1986 original, A Link to "
             "the Past, Link's Awakening. About %d hours. 2 is the rest of "
             "the mainline, the DS pair included. 3 is spin-offs and "
             "remakes, marked as such; a finish date covers 1 and 2 and "
             "the checkbox adds the rest." % round(spine)],
            ["Four Swords, the honest version.", "In 2002 it existed only "
             "as the second half of A Link to the Past's GBA cart, and "
             "HowLongToBeat has no standalone entry for that release. The "
             "row sits at 2002 where the game belongs; its hours are the "
             "2011 DSi Anniversary Edition, the same game released on its "
             "own."],
            ["Remakes are marked.", "Every remake and remaster row names "
             "the game it rebuilds. None is required — but the 2019 Link's "
             "Awakening and the two 3DS rebuilds are the friendliest doors "
             "into their originals, and ticking either version counts."],
            "Game list and years from Wikipedia's List of The Legend of "
            "Zelda media; hours from HowLongToBeat, collected from its own "
            "pages and verified by name.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d games, %d hours (%d mainline, %d tier-1)"
          % (len(sections), len(ids), round(hours), round(mainline),
             round(spine)))
    for s in sections:
        print("   %-42s %2d  %s" % (s["title"], len(s["items"]), s["sub"][:44]))


if __name__ == "__main__":
    main()
