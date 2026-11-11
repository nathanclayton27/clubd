#!/usr/bin/env python3
"""Generate properties/resident-evil.json.

    python tools/make_re.py

Mainline Resident Evil in release order — the numbered games, Code:
Veronica, the remakes (marked), and the two Chronicles recaps as the only
spin-offs kept.

Hours are HowLongToBeat main-story figures — story only — read from
tools/data/residentevil.json, which was collected by scratch/re/fetch_hltb.py
and verified there by name AND release year; the original/remake name
collisions (RE 1996/2002, RE2 1998/2019, RE3 1999/2020, RE4 2005/2023) make
the year part of the identity, and the generator re-checks both.

Tiers:
  1  the mainline story spine — the numbered games, 0 through Requiem
  2  the canon between the numbers — Code: Veronica and the Revelations pair
  3  the remakes (marked) and the two kept spin-offs

Requiem (February 2026) is the ninth mainline game and is included with
real HLTB data.

Unreleased work is listed when the source dates it, and weighs zero (the
house rule: a source date, even a bare year, earns a row; undated work does
not).  Resident Evil Veronica, the Code: Veronica remake, is a row: its own
Wikipedia article's infobox reads `released = 2027` and its lead "scheduled
for release in 2027", and the franchise article's timeline slots it under
2027 (both fetched 2026-11-11, kept as scratch/re/veronica.wiki and
scratch/re/franchise.wiki).  It carries an explicit w of 0 — the page books
a row with no w as one hour — and says why in its note.  HowLongToBeat only
carries a main-story figure for a game people have finished, so when 2027
has passed without one in the data file the build fails here and the row
comes back for review.
"""
import datetime
import json
import pathlib

SLUG = "resident-evil"

# Rows with no HowLongToBeat record because the game is not out yet. Each
# ships with an explicit w of 0 and NOT_OUT in front of its note; main()
# asserts the stated year has not passed.
UNRELEASED = {"veronica"}

# Prefixed to an unreleased row's own note, so the row still reads correctly
# the day it ships and the note needs no second edit.
NOT_OUT = ("Not out yet — dated %d, and the bar stays empty until "
           "HowLongToBeat has hours for it.")

# key in the data file, expected HLTB name, display title, display year,
# tier, note, opt
ROSTER = [
    ("re1", "Resident Evil", "Resident Evil", 1996, 1,
     "The mansion — the series' whole grammar in one house.", 0),
    ("re2", "Resident Evil 2", "Resident Evil 2", 1998, 1, "", 0),
    ("re3", "Resident Evil 3: Nemesis", "Resident Evil 3: Nemesis", 1999, 1,
     "Runs alongside 2 rather than after it.", 0),
    ("cv", "Resident Evil Code: Veronica",
     "Resident Evil – Code: Veronica", 2000, 2,
     "The mainline sequel in everything but a number. Code: Veronica X is "
     "the definitive cut; a full remake is due in 2027.", 0),
    ("re1r", "Resident Evil", "Resident Evil (2002)", 2002, 3,
     "The GameCube remake of the first game — widely treated as the "
     "definitive way to play it. On modern platforms as the HD Remaster.",
     1),
    ("re0", "Resident Evil 0", "Resident Evil 0", 2002, 1,
     "The prequel — mainline by number, and the one numbered game later "
     "entries never lean on.", 0),
    ("re4", "Resident Evil 4", "Resident Evil 4", 2005, 1,
     "The reinvention — over-the-shoulder, action-forward, and half the "
     "industry followed.", 0),
    ("uc", "Resident Evil: The Umbrella Chronicles",
     "Resident Evil: The Umbrella Chronicles", 2007, 3,
     "Wii rail shooter retelling the early arc — a recap machine more than "
     "a chapter.", 1),
    ("re5", "Resident Evil 5", "Resident Evil 5", 2009, 1,
     "Built for co-op, and the close of the storyline the classics "
     "opened.", 0),
    ("dc", "Resident Evil: The Darkside Chronicles",
     "Resident Evil: The Darkside Chronicles", 2009, 3,
     "The second rail shooter — retells 2 and Code: Veronica.", 1),
    ("rev", "Resident Evil: Revelations", "Resident Evil: Revelations",
     2012, 2, "Between 4 and 5, born on 3DS — episodic horror on a ship.",
     0),
    ("re6", "Resident Evil 6", "Resident Evil 6", 2012, 1,
     "Four campaigns, every tone at once — the bloated one, and the pivot "
     "point.", 0),
    ("rev2", "Resident Evil: Revelations 2",
     "Resident Evil: Revelations 2", 2015, 2,
     "Between 5 and 6, episodic — Claire's return.", 0),
    ("re7", "Resident Evil 7: Biohazard", "Resident Evil 7: Biohazard",
     2017, 1,
     "First person and back to horror — a fresh start that still counts.",
     0),
    ("re2r", "Resident Evil 2", "Resident Evil 2 (2019)", 2019, 3,
     "The remake that started the modern wave — a full rebuild of 1998, "
     "not a reissue.", 1),
    ("re3r", "Resident Evil 3", "Resident Evil 3 (2020)", 2020, 3,
     "Remake of Nemesis — brisk, and trims as much as it rebuilds.", 1),
    ("village", "Resident Evil Village", "Resident Evil Village", 2021, 1,
     "Direct sequel to 7 — the Winters story's second half.", 0),
    ("re4r", "Resident Evil 4", "Resident Evil 4 (2023)", 2023, 3,
     "Remake of the 2005 game, and the rare remake that stands fully "
     "beside its original.", 1),
    ("requiem", "Resident Evil Requiem", "Resident Evil Requiem", 2026, 1,
     "The ninth mainline game — a new lead, and a return to Raccoon City.",
     0),
    ("veronica", None, "Resident Evil Veronica", 2027, 3,
     "Remake of Code: Veronica — third-person, built along the lines of "
     "the 2019 Resident Evil 2.", 1),
]

ERAS = [
    ("classic", "The classic era", 1996, 2001,
     "Fixed cameras, ink ribbons, Raccoon City — the four games that "
     "define survival horror."),
    ("gamecube", "The GameCube years", 2002, 2004,
     "Capcom remade the first game and prequeled it in the same year."),
    ("action", "The action era", 2005, 2014,
     "4 turns the camera over the shoulder and the series chases action "
     "for a decade."),
    ("return", "The return to horror", 2015, 2018,
     "First person, family estates, found footage — the correction."),
    ("twotracks", "Two tracks at once", 2019, 9999,
     "Since 2019 the series runs remakes of the classics alongside new "
     "mainline entries, one lane feeding the other."),
]


def main():
    data = json.loads((pathlib.Path(__file__).resolve().parent / "data"
                       / "residentevil.json").read_text(encoding="utf-8"))

    entries = []
    used = set()
    today = datetime.date.today()
    for key, expect, title, year, tier, note, opt in ROSTER:
        rec = data.get(key)
        if key in UNRELEASED and not rec:
            # Dated to a year and not out: a row because the source dates
            # it, weightless because nobody has finished it yet.
            assert today.year <= year, (
                "%s was dated %d and that year has passed with no "
                "HowLongToBeat record. Collect its hours into "
                "tools/data/residentevil.json and drop it from UNRELEASED."
                % (title, year))
            x = {"id": "re-%s" % key, "t": title, "n": str(year),
                 "w": 0, "tier": tier, "year": year,
                 "note": " ".join([NOT_OUT % year, note]).strip()}
            if opt:
                x["opt"] = 1
            entries.append(x)
            continue
        assert rec, "no HLTB record for %s" % key
        assert expect, "no expected HLTB name for %s" % key
        assert rec["name"].lower() == expect.lower(), (
            "record mismatch for %s: %r" % (key, rec["name"]))
        assert rec["year"] == year, (
            "year mismatch for %s: %r vs %r" % (key, rec["year"], year))
        used.add(key)
        x = {"id": "re-%s" % key, "t": title, "n": str(year),
             "w": rec["main_h"], "tier": tier, "year": year}
        if note:
            x["note"] = note
        if opt:
            x["opt"] = 1
        entries.append(x)

    assert used == set(data), "cache keys unused: %r" % (set(data) - used)

    sections = []
    for key, title, lo, hi, intro in ERAS:
        got = [e for e in entries if lo <= e["year"] <= hi]
        assert got, "empty era %s" % key
        hours = sum(e["w"] for e in got)
        span = ("%d" % got[0]["year"] if got[0]["year"] == got[-1]["year"]
                else "%d–%d" % (got[0]["year"], got[-1]["year"]))
        sec = {"id": key, "title": title,
               "sub": "%s · %d %s · %d hours story"
                      % (span, len(got),
                         "game" if len(got) == 1 else "games", round(hours)),
               "items": [{k: v for k, v in e.items()
                          if k in ("id", "t", "n", "w", "tier", "opt", "note")}
                         for e in got]}
        if intro:
            sec["intro"] = intro
        if key == "classic":
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(ROSTER) == 20, (len(ids),)
    tiers = {t: [x for s in sections for x in s["items"] if x["tier"] == t]
             for t in (1, 2, 3)}
    assert len(tiers[1]) == 10, "spine should be 10 games, got %d" % len(tiers[1])
    assert len(tiers[2]) == 3, "tier 2 should be 3 games, got %d" % len(tiers[2])
    assert len(tiers[3]) == 7, "tier 3 should be 7 games, got %d" % len(tiers[3])
    # The only weightless rows are the ones this file knows are unreleased.
    zeros = {x["id"] for s in sections for x in s["items"] if x["w"] == 0}
    assert zeros == {"re-%s" % k for k in UNRELEASED if k not in data}, zeros

    hours = sum(x["w"] for s in sections for x in s["items"])
    spine = sum(x["w"] for x in tiers[1])

    prop = {
        "slug": SLUG,
        "title": "Resident Evil",
        "subtitle": "mainline in release order, Code: Veronica and the "
                    "remakes included",
        "kind": "games",
        "popularity": 80,
        "year": "1996–",
        "blurb": "%d games in release order — about %d hours of story, %d "
                 "of it the mainline spine." % (len(ids), round(hours),
                                                round(spine)),
        "unit": {"one": "game", "many": "games"},
        "verb": {"base": "play", "past": "played", "ing": "playing"},
        "itemOrder": "number-first",
        "accent": "#5F1F1F",
        "accentDark": "#D97A7A",
        "tiers": True,
        "itemTiers": True,
        "paceTiers": [1, 2],
        "paceLabel": "the remakes and spin-offs",
        "notes": [
            ["Remake or original.", "The 2019–2023 remakes are rebuilds, "
             "not reissues — same events, different shape, with scenes "
             "moved, cut or invented. The spine lists the originals and "
             "the remakes sit in tier 3, marked; either version counts for "
             "following the story, so tick one per game. The exception is "
             "1996: the 2002 remake is widely treated as the definitive "
             "first game."],
            ["Zero, the odd number.", "Resident Evil 0 is mainline by its "
             "number and a prequel by its content — nothing later depends "
             "on it. It keeps the spine tier for completeness; "
             "skip-and-return is a fine way to play it."],
            ["The tier-2 canon.", "Code: Veronica continues the classic "
             "story — a mainline sequel in everything but the digit — and "
             "the Revelations pair bridges 4–5 and 5–6. A finish date "
             "covers tiers 1 and 2, and the checkbox adds the rest. A "
             "Code: Veronica remake, Resident Evil Veronica, is due in "
             "2027."],
            ["Spin-offs, kept to two.", "The Chronicles rail shooters stay "
             "because they retell the classic era and work as recaps. "
             "Survivor, Outbreak, Dead Aim, Operation Raccoon City and the "
             "multiplayer experiments are left off on purpose."],
            ["Hours are story only.", "HowLongToBeat main-story figures — "
             "no extra modes, no completionist padding. The classics "
             "assume second scenarios and replays; those are not counted."],
            "Hours from HowLongToBeat, matched by name and release year.",
        ],
        "sections": sections,
    }

    out = (pathlib.Path(__file__).resolve().parent.parent / "properties"
           / ("%s.json" % SLUG))
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d games, %d hours (%d spine, %d with tier 2)"
          % (len(sections), len(ids), round(hours), round(spine),
             round(spine + sum(x["w"] for x in tiers[2]))))
    for s in sections:
        print("   %-24s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
