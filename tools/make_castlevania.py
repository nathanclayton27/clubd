#!/usr/bin/env python3
"""Generate properties/castlevania.json.

    python3 tools/make_castlevania.py

The Castlevania canon in three styles: the classic whip-and-stairs games,
Symphony of the Night, the six handheld Metroidvanias that followed it and
Belmont's Curse (2026), and the Lords of Shadow reboot as its own optional
wing.

Which games exist and their release years come from Wikipedia's Castlevania
article — its main-series release timeline is the authority
(scratch/agent-games1/wiki/castlevania.wiki). Hours are HowLongToBeat
main-story figures — story only, the house standard — read from
tools/data/castlevania.json, collected by
scratch/agent-games1/fetch_hltb.py (Belmont's Curse, added 2026-11-11, by
tools/gwlib/hltb.py — that script's package is dead) and verified by name
(this generator refuses a record whose name is not what it expects, and
cross-checks HLTB's release year against Wikipedia's).

Every row carries a style tag — Classic, Metroidvania, Reboot — and the
page grows filter chips from them.

Scope cut, stated: the Game Boy trilogy (The Adventure, Belmont's Revenge,
Legends), the Nintendo 64 pair, the PS2 3D pair (Lament of Innocence, Curse
of Darkness), Dracula X on SNES, Haunted Castle (and its 2024 remake,
Haunted Castle Revisited) and the spin-offs are on Wikipedia's timeline but
not here — this list keeps to the canon the series is remembered for. The
notes say so.
"""
import json
import pathlib

SLUG = "castlevania"

# key in the data file, display title, Wikipedia year, note
CLASSIC = [
    ("cv1", "Castlevania", 1986,
     "NES. Simon Belmont, the whip, the clock tower — the blueprint."),
    ("cv2", "Castlevania II: Simon's Quest", 1987,
     "The odd open one — day-night cycles and famously cryptic clues"),
    ("cv3", "Castlevania III: Dracula's Curse", 1989,
     "Branching paths and three partners; the NES peak"),
    ("cv4", "Super Castlevania IV", 1991,
     "SNES. The original retold with an eight-way whip."),
    ("rondo", "Castlevania: Rondo of Blood", 1993,
     "PC Engine, Japan only for years — play it via the Dracula X "
     "Chronicles PSP disc or the Requiem pair on PS4. The SNES "
     "“Dracula X” is a different, lesser retelling."),
    ("bloodlines", "Castlevania: Bloodlines", 1994,
     "Genesis. The 1917 one — Eric Lecarde's spear and a different "
     "bloodline."),
    ("chronicles", "Castlevania Chronicles", 2001,
     "The PS1 release of the Sharp X68000 rebuild of the original"),
]

METROIDVANIA = [
    ("sotn", "Castlevania: Symphony of the Night", 1997,
     "PS1. Alucard, the inverted castle, and the genre's other namesake."),
    ("cotm", "Castlevania: Circle of the Moon", 2001,
     "GBA launch — the card-combining one"),
    ("hod", "Castlevania: Harmony of Dissonance", 2002,
     "GBA. The Symphony-styled one, brighter and easier."),
    ("aos", "Castlevania: Aria of Sorrow", 2003,
     "GBA. Soma Cruz and the soul system — the handheld peak."),
    ("dos", "Castlevania: Dawn of Sorrow", 2005,
     "DS. Aria's direct sequel."),
    ("por", "Castlevania: Portrait of Ruin", 2006,
     "DS. Two characters, paintings as worlds — the Bloodlines "
     "follow-up."),
    ("ooe", "Castlevania: Order of Ecclesia", 2008,
     "DS. Shanoa and the glyphs; the hardest of the six."),
    ("bc", "Castlevania: Belmont's Curse", 2026,
     "Switch, PS5, PC and Xbox. Rose Belmont and Dracula's castle in the "
     "heart of 1499 Paris — the 40th-anniversary entry."),
]

REBOOT = [
    ("los", "Castlevania: Lords of Shadow", 2010,
     "The continuity reboot — a God of War-shaped epic with Patrick "
     "Stewart narrating"),
    ("mirror", "Castlevania: Lords of Shadow – Mirror of Fate", 2013,
     "The 3DS side chapter between the two console games"),
    ("los2", "Castlevania: Lords of Shadow 2", 2014,
     "Dracula in the modern day; the reboot's divisive close"),
]

SECTIONS = [
    ("classic", "The classic line", "Classic",
     "Stage-by-stage vampire hunting, 1986 to the PS1 Chronicles — "
     "Rondo and Bloodlines included.", 0, CLASSIC),
    ("metroidvania", "Symphony and its heirs", "Metroidvania",
     "The castle becomes a map: Symphony of the Night, then the GBA and "
     "DS six that carried it, and Belmont's Curse in 2026.", 0,
     METROIDVANIA),
    ("reboot", "Lords of Shadow", "Reboot",
     "The 2010 continuity reboot — a separate story, optional by "
     "design.", 1, REBOOT),
]


# where HLTB's release year is allowed to differ from Wikipedia's by more
# than one: HLTB dates Chronicles to the 1993 X68000 original, the row to
# its 2001 PS1 release — both sit on Wikipedia's timeline
YEAR_EXCUSED = {"chronicles"}


def norm(s):
    s = (s or "").replace("’", "'").replace("–", "-")
    return " ".join(s.casefold().split())


def main():
    data = json.loads((pathlib.Path(__file__).resolve().parent / "data"
                       / "castlevania.json").read_text(encoding="utf-8"))

    sections = []
    for sec_id, sec_title, style, intro, opt, roster in SECTIONS:
        years = [y for _, _, y, _ in roster]
        assert years == sorted(years), "%s roster out of release order" % sec_id
        items = []
        for key, title, year, note in roster:
            rec = data.get(key)
            assert rec, "no HLTB record for %s" % key
            assert norm(rec["name"]) == norm(title), \
                "record mismatch for %s: %r" % (key, rec["name"])
            assert key in YEAR_EXCUSED or abs(int(rec["year"]) - year) <= 1, \
                "year mismatch for %s: wiki %d, hltb %s" % (key, year, rec["year"])
            x = {"id": "cv-%s" % key, "t": title, "n": str(year),
                 "w": rec["main_h"], "tags": [style]}
            if note:
                x["note"] = note
            if opt:
                x["opt"] = 1
            items.append(x)
        hours = sum(x["w"] for x in items)
        sections.append({
            "id": sec_id, "title": sec_title,
            "sub": "%d–%d · %d games · %d hours story"
                   % (years[0], years[-1], len(items), round(hours)),
            "intro": intro,
            "items": items,
        })
    sections[0]["open"] = True

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(CLASSIC) + len(METROIDVANIA) + len(REBOOT) == 18, \
        (len(ids),)
    styles = {t for s in sections for x in s["items"] for t in x["tags"]}
    assert styles == {"Classic", "Metroidvania", "Reboot"}, styles

    hours = sum(x["w"] for s in sections for x in s["items"])
    core = sum(x["w"] for s in sections for x in s["items"] if not x.get("opt"))

    prop = {
        "slug": SLUG,
        "title": "Castlevania",
        "subtitle": "the whip canon: classic, Metroidvania, and the reboot",
        "kind": "games",
        "popularity": 61,
        "year": "1986–",
        "blurb": "%d games — the classics, Symphony and the handheld six, "
                 "Lords of Shadow, and Belmont's Curse; about %d hours of "
                 "story."
                 % (len(ids), round(hours)),
        "unit": {"one": "game", "many": "games"},
        "verb": {"base": "play", "past": "played", "ing": "playing"},
        "itemOrder": "number-first",
        "accent": "#4E3220",
        "accentDark": "#F2A83B",
        "tiers": False,
        "filter": {"key": "style", "label": "Style", "mode": "include",
                   "values": ["Classic", "Metroidvania", "Reboot"]},
        "notes": [
            ["Three styles, chips to match.", "Classic is stage-by-stage "
             "action; Metroidvania is the explorable castle Symphony "
             "invented for the series; Reboot is the Lords of Shadow "
             "continuity, a separate story marked optional. The chips "
             "filter the list by style."],
            ["Release order within each section.", "Almost every game is "
             "its own century and its own Belmont — order barely binds. "
             "The one real pairing: Dawn of Sorrow directly continues "
             "Aria of Sorrow."],
            ["What was cut.", "Wikipedia's timeline also carries the Game "
             "Boy trilogy, the Nintendo 64 pair, the PS2 3D pair, Dracula "
             "X on SNES, Haunted Castle and assorted spin-offs. This list "
             "keeps to the canon the series is remembered for; nothing "
             "cut is required by anything here."],
            ["Hours are story only.", "HowLongToBeat main-story figures — "
             "Symphony's number is one castle, not both, and the "
             "handhelds' soul and item hunts aren't counted."],
            "Game list and years from Wikipedia's Castlevania series "
            "timeline; hours from HowLongToBeat main-story figures, "
            "verified by name.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d games, %d hours (%d outside the reboot)"
          % (len(sections), len(ids), round(hours), round(core)))
    for s in sections:
        print("   %-26s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
