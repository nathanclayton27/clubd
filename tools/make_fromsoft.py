#!/usr/bin/env python3
"""Generate properties/fromsoft.json.

    python3 tools/make_fromsoft.py

The Souls line and its adjacents, in release order: Demon's Souls through
Elden Ring, Shadow of the Erdtree as its own row (it is the size of a full
game), Nightreign, and Armored Core VI as a marked outlier. Not the whole
studio — no King's Field, no older Armored Core, no Déraciné, no Duskbloods.

The Duskbloods (Wikipedia: 2027, Switch 2) is left off on purpose, not by
staleness: it is a multiplayer PvP/PvE match game, not a story to finish, and
it neither belongs to the Souls line nor extends Elden Ring. AC6 stays the one
outlier. Ruled 2026-11-12 under Nathan's delegation (CLU-602); the Scope note
names it so the next freshness sweep reads the call instead of re-asking.

Which games exist and their release years come from Wikipedia's FromSoftware
article (scratch/fromsoft/games.wiki — its developed-games and DLC tables).
Hours are HowLongToBeat main-story figures — story only, the house rule —
read from tools/data/fromsoft.json, collected by
scratch/fromsoft/fetch_hltb.py and verified by name (this generator refuses a
record whose name is not what it expects, and cross-checks HLTB's release
year against Wikipedia's).

Tiers, and the rule behind them:
  1  the Souls line proper — the seven complete games, Demon's Souls to
     Elden Ring
  2  what extends Elden Ring: Shadow of the Erdtree and Nightreign
  3  the outlier — Armored Core VI, same studio, not Souls

Dark Souls: Remastered (2018) and the Demon's Souls remake (2020) are the
same stories in better clothes; they are notes on their rows, not rows.
"""
import json
import pathlib

SLUG = "fromsoft"

# key in the data file, display title, Wikipedia year, tier, note, opt
ROSTER = [
    ("demons", "Demon's Souls", 2009, 1,
     "Where the shape starts. The 2020 PS5 remake is the accessible way in "
     "— same story, same hours.", 0),
    ("ds1", "Dark Souls", 2011, 1,
     "The one the rest get measured against; the 2018 Remastered is the "
     "version to actually buy, and it counts as this row", 0),
    ("ds2", "Dark Souls II", 2014, 1,
     "The odd one out and better than its reputation; Scholar of the First "
     "Sin is its current edition", 0),
    ("bloodborne", "Bloodborne", 2015, 1,
     "PlayStation only. Faster, meaner, gothic; The Old Hunters expansion "
     "is worth the detour.", 0),
    ("ds3", "Dark Souls III", 2016, 1,
     "The send-off; Ashes of Ariandel and The Ringed City close it "
     "properly", 0),
    ("sekiro", "Sekiro: Shadows Die Twice", 2019, 1,
     "Same house, different verbs — no builds, no summons, just the "
     "sword", 0),
    ("eldenring", "Elden Ring", 2022, 1,
     "The open-world one, and the biggest single game here", 0),
    ("ac6", "Armored Core VI: Fires of Rubicon", 2023, 3,
     "The marked outlier — not Souls at all, here because it is what the "
     "studio built between Elden Ring and its expansion. Mechs and "
     "missions; skip it and nothing breaks.", 1),
    ("erdtree", "Elden Ring: Shadow of the Erdtree", 2024, 2,
     "Elden Ring's expansion, the size of a full game — a row so a group "
     "can track it. Entered from deep in Elden Ring, so it cannot come "
     "first.", 0),
    ("nightreign", "Elden Ring: Nightreign", 2025, 2,
     "The standalone co-op spin — runs rather than a quest, and the one "
     "row built for playing together", 0),
]

ERAS = [
    ("souls", "The Souls line", 2009, 2016,
     "Five games that invent and refine the shape: ruined kingdoms, "
     "bonfire logic, death as the teacher."),
    ("depart", "Sekiro to Elden Ring", 2017, 2022,
     "Two departures — one takes the build away, the other opens the map."),
    ("after", "After Elden Ring", 2023, 9999,
     "The outlier, the expansion, and the co-op spin."),
]


def main():
    data = json.loads((pathlib.Path(__file__).resolve().parent / "data"
                       / "fromsoft.json").read_text(encoding="utf-8"))

    entries = []
    for key, title, year, tier, note, opt in ROSTER:
        rec = data.get(key)
        assert rec, "no HLTB record for %s" % key
        got = rec["name"].replace("’", "'").lower()
        want = title.replace("’", "'").lower()
        assert got == want, "record mismatch for %s: %r" % (key, rec["name"])
        assert abs(int(rec["year"]) - year) <= 1, \
            "year mismatch for %s: wiki %d, hltb %s" % (key, year, rec["year"])
        x = {"id": "fs-%s" % key, "t": title, "n": str(year),
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
        if key == "souls":
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(ROSTER), (len(ids), len(ROSTER))
    t1 = [x for s in sections for x in s["items"] if x["tier"] == 1]
    assert len(t1) == 7, "the Souls line proper should be 7 games, got %d" % len(t1)

    hours = sum(x["w"] for s in sections for x in s["items"])
    spine = sum(x["w"] for x in t1)

    prop = {
        "slug": SLUG,
        "title": "FromSoftware",
        "subtitle": "the Souls line and its adjacents, in release order",
        "kind": "games",
        "popularity": 72,
        "year": "2009–",
        "blurb": "%d games — about %d hours of story, %d of it the Souls "
                 "line proper." % (len(ROSTER), round(hours), round(spine)),
        "unit": {"one": "game", "many": "games"},
        "verb": {"base": "play", "past": "played", "ing": "playing"},
        "itemOrder": "number-first",
        "accent": "#3A3530",
        "accentDark": "#C9B8A0",
        "tiers": True,
        "itemTiers": True,
        "paceTiers": [1, 2],
        "paceLabel": "the Armored Core outlier",
        "notes": [
            ["Scope.", "The Souls line and what sits beside it, not the "
             "whole studio — no King's Field, no older Armored Core, no "
             "Déraciné, no Duskbloods. Armored Core VI is the one marked "
             "outlier, included "
             "because it is what the studio built between Elden Ring and "
             "its expansion; skip it and nothing breaks."],
            ["Hours are story only.", "HowLongToBeat main-story figures, as "
             "asked — the credits, not completion. These are the games "
             "where skill moves the number more than anywhere else on this "
             "site, so treat every figure as a median, not a promise."],
            ["Tiers, and the rule behind them.", "1 is the Souls line "
             "proper: the seven complete games from Demon's Souls to Elden "
             "Ring, about %d hours. 2 is what extends Elden Ring — Shadow "
             "of the Erdtree and Nightreign. 3 is the outlier. A finish "
             "date covers 1 and 2; the checkbox adds Armored Core."
             % round(spine)],
            ["Erdtree is a row, on purpose.", "Shadow of the Erdtree is "
             "DLC, but it is the size of a full game and most of a "
             "playthrough long, so it gets its own tracked row rather than "
             "a footnote on Elden Ring."],
            ["Remaster and remake, noted rather than listed.", "Dark "
             "Souls: Remastered (2018) and the Demon's Souls remake (2020) "
             "are the same stories in better clothes. Play whichever "
             "edition you like and tick the one row — separate rows would "
             "double-count the same game."],
            "Game list and years from Wikipedia's FromSoftware article; "
            "hours from HowLongToBeat, collected from its own pages and "
            "verified by name.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d games, %d hours (%d the Souls line)"
          % (len(sections), len(ids), round(hours), round(spine)))
    for s in sections:
        print("   %-24s %2d  %s" % (s["title"], len(s["items"]), s["sub"][:44]))


if __name__ == "__main__":
    main()
