#!/usr/bin/env python3
"""Generate properties/final-fantasy.json.

    python3 tools/make_ff.py

The sixteen numbered Final Fantasy games in release order, plus the branches
off them: the direct sequels (X-2, XIII-2, Lightning Returns) and the VII
remake line. Every numbered game stands alone — that is the property's first
note, because it is the franchise's whole deal.

Hours are HowLongToBeat main-story figures, read from
tools/data/finalfantasy.json, which scratch/ff/fetch_hltb.py collected one
search at a time and verified by name and year (the list itself was checked
against Wikipedia's series page first). This generator re-verifies every
record's name before using it.

Tiers:
  1  the sixteen numbered games — the spine a finish date paces
  2  the branches: direct sequels and the VII remake line

XIV is one row for the whole MMO. HLTB's figure is A Realm Reborn's base
story, and the note says what that leaves out — a decade of expansions.

A row in UNRELEASED is dated but not out: it ships with w 0 and a note
saying when it is due. HLTB lists it with no main-story figure, and the
generator refuses to run once its date passes, so the hours get fetched.
"""
import datetime
import json
import pathlib

SLUG = "final-fantasy"

# key in the data file, expected name there, tier, note
ROSTER = [
    ("ff1", "Final Fantasy", 1, ""),
    ("ff2", "Final Fantasy II", 1, ""),
    ("ff3", "Final Fantasy III", 1,
     "The one that stayed in Japan until the DS remake"),
    ("ff4", "Final Fantasy IV", 1,
     "Shipped in the US as “Final Fantasy II”"),
    ("ff5", "Final Fantasy V", 1, ""),
    ("ff6", "Final Fantasy VI", 1,
     "Shipped in the US as “Final Fantasy III”"),
    ("ff7", "Final Fantasy VII", 1, ""),
    ("ff8", "Final Fantasy VIII", 1, ""),
    ("ff9", "Final Fantasy IX", 1, ""),
    ("ff10", "Final Fantasy X", 1, "The first one with voice acting"),
    ("ff11", "Final Fantasy XI", 1,
     "The first of the two MMOs — still running, and soloable these days. "
     "The hours are its base story."),
    ("ff10-2", "Final Fantasy X-2", 2,
     "The franchise's first direct sequel, following X"),
    ("ff12", "Final Fantasy XII", 1, ""),
    ("ff13", "Final Fantasy XIII", 1, ""),
    ("ff14", "Final Fantasy XIV", 1,
     "The MMO. Launched 2010, remade as A Realm Reborn in 2013 — the hours "
     "are the base story alone, and a decade of expansions sits on top of "
     "them."),
    ("ff13-2", "Final Fantasy XIII-2", 2, "Direct sequel to XIII"),
    ("lightning-returns", "Lightning Returns: Final Fantasy XIII", 2,
     "The close of the XIII trilogy"),
    ("ff15", "Final Fantasy XV", 1, ""),
    ("ff7-remake", "Final Fantasy VII Remake", 2,
     "First of the remake trilogy — a retelling of VII, not a replacement "
     "for it"),
    ("ff16", "Final Fantasy XVI", 1, ""),
    ("ff7-rebirth", "Final Fantasy VII Rebirth", 2,
     "Second of the remake trilogy"),
    ("ff7-revelation", "Final Fantasy VII Revelation", 2,
     "Third and last of the remake trilogy"),
]

# Dated, not out: key -> release date, from the game's own Wikipedia article
# (checked 2026-11-11: "scheduled for release on April 8, 2027").
UNRELEASED = {"ff7-revelation": "2027-04-08"}

# Prefixed to an unreleased row's own note, so the row still reads correctly
# the day it ships and the note needs no second edit.
NOT_OUT = ("Not out yet — due %s, and the bar stays empty until "
           "HowLongToBeat has hours for it.")


def longdate(d):
    return "%d %s %d" % (d.day, d.strftime("%B"), d.year)

# XIV's cache record is A Realm Reborn (2013); the numbered entry premiered
# in 2010 and that is where release order puts the row. The note carries it.
YEAR_SHOWN = {"ff14": 2010}

ERAS = [
    ("bit", "The 8- and 16-bit years", 1987, 1996,
     "Six games in seven years, on the NES and Super NES. The Pixel "
     "Remasters are the modern way to play all of them."),
    ("ps1", "The PlayStation era", 1997, 2000,
     "Three games that took the series from Japanese institution to "
     "worldwide one."),
    ("ps2", "The PlayStation 2 era", 2001, 2008,
     "The first MMO, the first direct sequel, and two of the biggest "
     "single-player entries."),
    ("hd", "The HD era", 2009, 2017,
     "The XIII trilogy, the MMO reborn, and the decade XV spent arriving."),
    ("now", "The current era", 2018, 9999,
     "The remake line and the action turn."),
]


def main():
    data = json.loads((pathlib.Path(__file__).resolve().parent / "data"
                       / "finalfantasy.json").read_text(encoding="utf-8"))

    today = datetime.date.today()
    entries = []
    for key, expect, tier, note in ROSTER:
        rec = data.get(key)
        assert rec, "no HLTB record for %s" % key
        assert rec["name"].lower() == expect.lower(), \
            "record mismatch for %s: %r" % (key, rec["name"])
        if key in UNRELEASED:
            due = datetime.date.fromisoformat(UNRELEASED[key])
            assert due > today, \
                ("%s was due %s and the row still weighs nothing: drop it "
                 "from UNRELEASED and fetch its hours" % (expect, due))
            assert rec["year"] == due.year, (key, rec["year"], due)
            assert not rec["main_h"], \
                ("HLTB now times %s (%s h) ahead of its %s date: give the "
                 "row its hours" % (expect, rec["main_h"], due))
            w = 0
            note = " ".join([NOT_OUT % longdate(due), note]).strip()
        else:
            assert rec["main_h"] > 0, "no hours for %s" % key
            w = rec["main_h"]
        year = YEAR_SHOWN.get(key, rec["year"])
        x = {"id": "ff-%s" % (key[2:] if key.startswith("ff") else key),
             "t": expect, "n": str(year), "w": w, "tier": tier,
             "year": year}
        if note:
            x["note"] = note
        entries.append(x)

    entries.sort(key=lambda e: (e["year"], e["t"]))

    sections = []
    for key, title, lo, hi, intro in ERAS:
        got = [e for e in entries if lo <= e["year"] <= hi]
        assert got, "empty era %s" % key
        hours = sum(e["w"] for e in got)
        sub = "%d–%d · %d games · %d hours story" \
              % (got[0]["year"], got[-1]["year"], len(got), round(hours))
        pending = [e for e in got if not e["w"]]
        if pending:
            sub += " · %d not out yet" % len(pending)
        sec = {"id": key, "title": title,
               "sub": sub,
               "intro": intro,
               "items": [{k: v for k, v in e.items()
                          if k in ("id", "t", "n", "w", "tier", "note")}
                         for e in got]}
        sections.append(sec)
    sections[0]["open"] = True

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(ROSTER), (len(ids), len(ROSTER))
    assert all(i.isascii() for i in ids), "non-ascii id"
    t1 = [x for s in sections for x in s["items"] if x["tier"] == 1]
    t2 = [x for s in sections for x in s["items"] if x["tier"] == 2]
    assert len(t1) == 16, "the numbered spine should be 16, got %d" % len(t1)
    assert len(t2) == 6, "the branches should be 6, got %d" % len(t2)
    zeros = {x["t"] for s in sections for x in s["items"] if not x["w"]}
    assert zeros == {t for k, t, _, _ in ROSTER if k in UNRELEASED}, zeros
    for s in sections:
        yrs = [int(x["n"]) for x in s["items"]]
        assert yrs == sorted(yrs), "%s is out of year order" % s["title"]

    hours = sum(x["w"] for s in sections for x in s["items"])
    spine = sum(x["w"] for x in t1)
    coming = sorted(zeros)
    assert len(coming) <= 1, "the blurb names one game still to come"
    blurb = ("%d games — about %d hours of story, %d of it the sixteen "
             "numbered ones" % (len(ids), round(hours), round(spine)))
    blurb += (", with %s still to come." % coming[0].split()[-1]
              if coming else ".")
    # When Revelation ships, this lookup fails along with the date assert
    # above: the remake-line note then needs rewriting, not just the row.
    revelation_due = longdate(datetime.date.fromisoformat(
        UNRELEASED["ff7-revelation"]))

    prop = {
        "slug": SLUG,
        "title": "Final Fantasy",
        "subtitle": "the sixteen numbered games, their sequels, and the VII "
                    "remake line",
        "kind": "games",
        "popularity": 82,
        "year": "1987–",
        "blurb": blurb,
        "unit": {"one": "game", "many": "games"},
        "verb": {"base": "play", "past": "played", "ing": "playing"},
        "itemOrder": "number-first",
        "accent": "#2E3A8A",
        "accentDark": "#8A96E8",
        "tiers": True,
        "itemTiers": True,
        "paceTiers": [1],
        "paceLabel": "the sequels and the remake line",
        "notes": [
            ["Every number starts fresh.", "A new Final Fantasy number is a "
             "new world, a new cast, a new story — there is no continuity "
             "between the numbered games, which is the franchise's whole "
             "deal. Start anywhere. The tier-2 rows are the exceptions: "
             "direct sequels and the VII remakes, which do need their "
             "parent."],
            ["Hours are story only.", "HowLongToBeat main-story figures — no "
             "side content, no completionist padding. The two MMOs get the "
             "same treatment and it undersells them: XI's figure is its base "
             "story, and XIV's is A Realm Reborn alone, under a decade of "
             "expansions."],
            ["Tiers.", "1 is the sixteen numbered games, about %d hours. 2 "
             "is the branches off them — X-2, the XIII sequels, and the VII "
             "remake line. A finish date paces the numbered spine; the "
             "checkbox under the bar adds the branches." % round(spine)],
            ["The remake line.", "VII Remake and Rebirth are not the usual "
             "kind of remake — they retell VII across three games, and they "
             "land best with the original played first. The third part, "
             "Revelation, is due on %s, so the line is here unfinished."
             % revelation_due],
            "Hours and dates from HowLongToBeat, verified by name; the list "
            "itself checked against Wikipedia's series page, and "
            "Revelation's release date against its own article.",
        ],
        "sections": sections,
    }

    out = (pathlib.Path(__file__).resolve().parent.parent / "properties"
           / ("%s.json" % SLUG))
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d games, %d hours (%d spine)"
          % (len(sections), len(ids), round(hours), round(spine)))
    for s in sections:
        print("   %-26s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
