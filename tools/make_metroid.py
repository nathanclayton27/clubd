#!/usr/bin/env python3
"""Generate properties/metroid.json.

    python3 tools/make_metroid.py

Every mainline Metroid in release order, remakes included, split the way the
series actually splits: the 2D saga and the Prime line.

Which games exist and their release years come from Wikipedia's List of
Metroid media (scratch/agent-games1/wiki/metroid.wiki). Hours are
HowLongToBeat main-story figures — story only, the house standard — read
from tools/data/metroid.json, collected by
scratch/agent-games1/fetch_hltb.py and verified by name (this generator
refuses a record whose name is not what it expects, and cross-checks HLTB's
release year against Wikipedia's).

Tiers are kept simple, on each row: 1 is the mainline saga, 2 is the
opt-flavored rows — Hunters and Federation Force. Other M sits in the saga
section because that is where its story sits; the row says it is the 3D
outlier.

Metroid Prime Remastered (2023) is a note on the Prime row, not a row:
HowLongToBeat folds the remaster into its 2002 Metroid Prime entry —
searching the remaster's name returns that record — so a separate row
would either duplicate the tick or carry an invented number. Pinball and
the Trilogy compilation are not rows either — noted below.

UNRELEASED WORK IS LISTED WHEN THE SOURCE DATES IT, AND WEIGHS ZERO
-------------------------------------------------------------------
Metroid Ravenous is a row in the 2D saga. The List of Metroid media dates
it `{{vgrelease|WW|January 28, 2027}}`, and its own article (rev
2026-11-07) calls it "the sequel to Metroid Dread" and says it "is
scheduled for release on January 28, 2027". An unreleased row carries an
explicit `w: 0`, never a missing one — the page resolves a missing w as one
hour (CLU-131). The date is asserted against the clock every run: while it
is in the future the row weighs 0, its note says when it is due, and
tools/data/metroid.json must still have no record for it; the day it passes
the build fails until a name-gated HowLongToBeat record is added (give
scratch/agent-games1/fetch_hltb.py a "ravenous" spec and re-run it).
"""
import datetime
import json
import pathlib

SLUG = "metroid"

# key in the data file, display title, Wikipedia year, tier, note, opt
SAGA = [
    ("metroid", "Metroid", 1986, 1,
     "NES. Zebes the first time; Zero Mission below rebuilds it.", 0),
    ("metroid2", "Metroid II: Return of Samus", 1991, 1,
     "Game Boy. The Metroid hunt; Samus Returns rebuilds it.", 0),
    ("super", "Super Metroid", 1994, 1,
     "SNES. The map, the sequence breaks, the template half a genre is "
     "named for.", 0),
    ("fusion", "Metroid Fusion", 2002, 1,
     "GBA. The X parasite and the SA-X — the saga's tightest, tensest "
     "chapter.", 0),
    ("zero-mission", "Metroid: Zero Mission", 2004, 1,
     "Remake — the GBA rebuild of the 1986 original, and the friendly way "
     "into it. Ticking either version counts.", 0),
    ("other-m", "Metroid: Other M", 2010, 1,
     "The 3D outlier in the saga line, set between Super and Fusion — "
     "divisive, and canon", 0),
    ("samus-returns", "Metroid: Samus Returns", 2017, 1,
     "Remake — the 3DS rebuild of Metroid II. Ticking either version "
     "counts.", 0),
    ("dread", "Metroid Dread", 2021, 1,
     "Switch. The long-promised close of the Metroid arc — the E.M.M.I. and "
     "the end of the Fusion thread.", 0),
    ("ravenous", "Metroid Ravenous", 2027, 1,
     "Switch 2. The sequel to Dread.", 0),
]

PRIME = [
    ("prime", "Metroid Prime", 2002, 1,
     "GameCube. First person, same loneliness. The 2023 Switch Remastered "
     "is the modern door — ticking either version counts.", 0),
    ("prime2", "Metroid Prime 2: Echoes", 2004, 1,
     "The dark-world one — harder and stranger", 0),
    ("hunters", "Metroid Prime Hunters", 2006, 2,
     "DS side story built around multiplayer; thin as a campaign", 1),
    ("prime3", "Metroid Prime 3: Corruption", 2007, 1,
     "Wii. The trilogy's close.", 0),
    ("fed-force", "Metroid Prime: Federation Force", 2016, 2,
     "3DS co-op spin-off — the one without Samus", 1),
    ("prime4", "Metroid Prime 4: Beyond", 2025, 1,
     "Eighteen years after Corruption — the Prime line resumes", 0),
]

# Dated, not out: key -> release date the source gives (List of Metroid
# media and the game's own article, both read 2026-11-11).
UNRELEASED = {"ravenous": datetime.date(2027, 1, 28)}

# Prefixed to an unreleased row's own note, so the row still says what it is
# the day it ships and the note needs no second edit.
NOT_OUT = ("Not out yet — due %s, and the bar stays empty until "
           "HowLongToBeat has hours for it.")

SECTIONS = [
    ("saga", "The 2D saga",
     "Samus's own story, told mostly side-on — the 1986 original to "
     "Ravenous, remakes beside their originals.", SAGA),
    ("prime", "Prime",
     "The first-person line, a story of its own set between the original "
     "and Metroid II.", PRIME),
]


def norm(s):
    s = (s or "").replace("’", "'").replace("–", "-")
    return " ".join(s.casefold().split())


def _today():
    """The clock, isolated so a check can stub it."""
    return datetime.date.today()


def longdate(d):
    return "%d %s %d" % (d.day, d.strftime("%B"), d.year)


def main():
    data = json.loads((pathlib.Path(__file__).resolve().parent / "data"
                       / "metroid.json").read_text(encoding="utf-8"))
    today = _today()

    sections = []
    for sec_id, sec_title, intro, roster in SECTIONS:
        years = [y for _, _, y, _, _, _ in roster]
        assert years == sorted(years), "%s roster out of release order" % sec_id
        items = []
        for key, title, year, tier, note, opt in roster:
            due = UNRELEASED.get(key)
            if due and due > today:
                # Dated, not out. HowLongToBeat only carries a main-story
                # figure for a game people have finished, so a record here
                # means it has shipped ahead of the source's date.
                assert key not in data, \
                    ("%s has a HowLongToBeat record (%r) before its stated %s "
                     "release — give the row its hours" % (title, data[key], due))
                assert year == due.year, (key, year, due)
                w = 0
                note = " ".join([NOT_OUT % longdate(due), note]).strip()
            else:
                rec = data.get(key)
                assert rec, ("no HLTB record for %s%s" % (key, (
                    " — its %s release date has passed; add a name-gated "
                    "HowLongToBeat record" % due) if due else ""))
                assert norm(rec["name"]) == norm(title), \
                    "record mismatch for %s: %r" % (key, rec["name"])
                assert abs(int(rec["year"]) - year) <= 1, \
                    "year mismatch for %s: wiki %d, hltb %s" % (key, year,
                                                                rec["year"])
                w = rec["main_h"]
            x = {"id": "met-%s" % key, "t": title, "n": str(year),
                 "w": w, "tier": tier}
            if note:
                x["note"] = note
            if opt:
                x["opt"] = 1
            items.append(x)
        hours = sum(x["w"] for x in items)
        sub = "%d–%d · %d games · %d hours story" % (
            years[0], years[-1], len(items), round(hours))
        pending = [x for x in items if x["w"] == 0]
        if pending:
            sub += " · %d not out yet" % len(pending)
        sections.append({
            "id": sec_id, "title": sec_title,
            "sub": sub,
            "intro": intro,
            "items": items,
        })
    sections[0]["open"] = True

    rows = [x for s in sections for x in s["items"]]
    ids = [x["id"] for x in rows]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(SAGA) + len(PRIME) == 15, (len(ids),)
    t2 = [x for x in rows if x["tier"] == 2]
    assert len(t2) == 2 and all(x.get("opt") for x in t2), \
        "tier 2 is the two opt rows"
    # The only zero weights are the dated rows that are not out yet.
    zeros = {x["id"] for x in rows if x["w"] == 0}
    assert zeros == {"met-%s" % k for k, d in UNRELEASED.items()
                     if d > today}, zeros

    hours = sum(x["w"] for x in rows)
    spine = sum(x["w"] for x in rows if x["tier"] == 1)
    coming = [x["t"] for x in rows if x["w"] == 0]
    blurb = ("%d games across two lines — about %d hours of story, %d of it "
             "mainline" % (len(ids), round(hours), round(spine)))
    blurb += (", with %s still to come." % coming[0].replace("Metroid ", "")
              if len(coming) == 1 else ".")

    prop = {
        "slug": SLUG,
        "title": "Metroid",
        "subtitle": "the 2D saga and the Prime line, remakes included",
        "kind": "games",
        "popularity": 70,
        "year": "1986–",
        "blurb": blurb,
        "unit": {"one": "game", "many": "games"},
        "verb": {"base": "play", "past": "played", "ing": "playing"},
        "itemOrder": "number-first",
        "accent": "#B34A0C",
        "accentDark": "#45D6E8",
        "tiers": True,
        "itemTiers": True,
        "paceTiers": [1],
        "paceLabel": "the side games",
        "notes": [
            ["Release order, two lines.", "The 2D saga and Prime run as "
             "their own sections because they are different games telling "
             "different stretches of the same story. Release order within "
             "each; nothing requires jumping between them."],
            ["Remakes are rows.", "Zero Mission rebuilds the 1986 original "
             "and Samus Returns rebuilds Metroid II — each remake is the "
             "friendlier door, and ticking either version counts."],
            ["Tiers, kept simple.", "1 is the mainline saga, both lines. "
             "2 is the opt rows — Hunters and Federation Force; a finish "
             "date covers tier 1 and the checkbox adds the rest."],
            ["Hours are story only.", "HowLongToBeat main-story figures — "
             "no 100% item hunts."],
            ["Not rows.", "Prime Remastered (2023) rides as a note on the "
             "Prime row — HowLongToBeat counts remaster and original as "
             "one game, and so does this list. Metroid Prime Pinball and "
             "the Prime Trilogy compilation are on Wikipedia's list but "
             "aren't campaigns — Pinball is a spin-off, Trilogy a box of "
             "three games already here."],
            "Game list and years from Wikipedia's List of Metroid media; "
            "hours from HowLongToBeat main-story figures, verified by "
            "name.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d games, %d hours (%d mainline)"
          % (len(sections), len(ids), round(hours), round(spine)))
    for s in sections:
        print("   %-14s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
