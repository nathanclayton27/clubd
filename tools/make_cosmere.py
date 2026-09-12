#!/usr/bin/env python3
"""Generate properties/cosmere.json.

    python tools/make_cosmere.py

Brandon Sanderson's Cosmere, sections per world/series, publication order
within each: Elantris, the two Mistborn eras, The Stormlight Archive (its
novellas in their publication slots), and a standalones section holding
Warbreaker, the free-floating novellas, the Cosmere Secret Projects and the
White Sand omnibus as an optional row. Arcanum Unbounded is one row; the
three short stories only ever collected there ride inside it.

Cosmere membership is exactly the ==Cosmere== section of Wikipedia's
Brandon Sanderson bibliography (tools/data/cosmere.json, built and asserted
by scratch/agent-books/parse_cosmere.py) — which keeps The Frugal Wizard
(Secret Project 2) and everything non-Cosmere out, and the notes say so.
"""
import json
import pathlib

SLUG = "cosmere"

# separately rowed novellas from the Short works table
ROWED_SHORTS = {"The Emperor's Soul", "Shadows for Silence in the Forests "
                "of Hell", "Sixth of the Dusk", "Secret History",
                "Edgedancer", "Dawnshard"}
CARD_STORIES = {"Elsecaller", "King Lopen the First of Alethkar"}


def slugify(t):
    # CLU-430. This fold DELETES a straight apostrophe (`The Emperor's Soul`
    # gives the-emperors-soul) and left U+2019 alone, so a curly one reached
    # the isalnum test below and became a dash instead. Two spellings of one
    # title would reach two ids, and an id is the `item_id` every tick and
    # thumb is stored against — moving one unticks the row for everyone
    # holding it. Drop both forms: that is the correction THIS direction
    # needs, and the opposite of what the folds that dash a straight
    # apostrophe need.
    t = t.replace("'", "").replace("’", "").replace("‘", "")
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    keep = keep.encode("ascii", "ignore").decode("ascii")
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def row(title, year, note="", opt=0):
    it = {"id": "cos-%d-%s" % (year, slugify(title)), "t": title,
          "n": str(year)}
    if note:
        it["note"] = note
    if opt:
        it["opt"] = 1
    return it


def main():
    here = pathlib.Path(__file__).resolve().parent
    d = json.loads((here / "data" / "cosmere.json").read_text(encoding="utf-8"))
    shorts = {s["title"]: s for s in d["shorts"]}

    # every separately rowed novella must be in the shorts table, collected
    # in Arcanum Unbounded where the table says so
    for t in ROWED_SHORTS:
        assert t in shorts, t
    inside_arcanum_only = [s["title"] for s in d["shorts"]
                           if s["arcanum"] and s["title"] not in ROWED_SHORTS]
    assert len(inside_arcanum_only) == 3, inside_arcanum_only

    AU = "collected in Arcanum Unbounded"
    era1 = [x for x in d["mistborn"] if x["era"] == "First Era"]
    era2 = [x for x in d["mistborn"] if x["era"] == "Second Era"]
    storm = {x["title"]: x for x in d["stormlight"]}
    stand = {x["title"]: x for x in d["standalones"]}
    hoid = {x["title"]: x for x in d["hoid"]}

    sections = [
        {"id": "elantris", "title": "Elantris",
         "sub": "2005 · the first Cosmere novel", "open": True,
         "items": [row("Elantris", stand["Elantris"]["year"])]},
        {"id": "mb-era1", "title": "Mistborn: the First Era",
         "sub": "2006–2016 · the trilogy, plus its 2016 novella",
         "items": [row(x["title"], x["year"]) for x in era1]
                  + [row("Mistborn: Secret History",
                         shorts["Secret History"]["year"],
                         "Novella · " + AU)]},
        {"id": "mb-era2", "title": "Mistborn: the Second Era",
         "sub": "2011–2022 · four novels",
         "items": [row(x["title"], x["year"]) for x in era2]},
        {"id": "stormlight", "title": "The Stormlight Archive",
         "sub": "2010–2024 · five novels, two novellas",
         "intro": "The novellas sit in their publication slots between the "
                  "novels.",
         "items": [
             row("The Way of Kings", storm["The Way of Kings"]["year"]),
             row("Words of Radiance", storm["Words of Radiance"]["year"]),
             row("Edgedancer", shorts["Edgedancer"]["year"],
                 "Novella · " + AU + ", standalone in 2017"),
             row("Oathbringer", storm["Oathbringer"]["year"]),
             row("Dawnshard", shorts["Dawnshard"]["year"], "Novella"),
             row("Rhythm of War", storm["Rhythm of War"]["year"]),
             row("Wind and Truth", storm["Wind and Truth"]["year"]),
         ]},
        {"id": "wider", "title": "Standalones & Secret Projects",
         "sub": "2009– · the rest of the Cosmere, publication order",
         "items": [
             row("Warbreaker", stand["Warbreaker"]["year"]),
             row("The Emperor's Soul", shorts["The Emperor's Soul"]["year"],
                 "Novella · the Elantris setting · " + AU),
             row("Shadows for Silence in the Forests of Hell",
                 shorts["Shadows for Silence in the Forests of Hell"]["year"],
                 "Novella · Threnody · " + AU),
             row("Sixth of the Dusk", shorts["Sixth of the Dusk"]["year"],
                 "Novella · First of the Sun · " + AU),
             row("Arcanum Unbounded",
                 shorts["Arcanum Unbounded: The Cosmere Collection"]["year"],
                 "The collection — the Cosmere short fiction through 2016; "
                 "one tick covers the three stories rowed nowhere else"),
             row("White Sand (omnibus)", 2022,
                 "Graphic novel with Rik Hoskin — the three Taldain "
                 "volumes, 2016–19, in one", opt=1),
             row("Tress of the Emerald Sea",
                 hoid["Tress of the Emerald Sea"]["year"],
                 "Secret Project 1 · Hoid's Travails"),
             row("Yumi and the Nightmare Painter",
                 hoid["Yumi and the Nightmare Painter"]["year"],
                 "Secret Project 3 · Hoid's Travails"),
             row("The Sunlit Man", stand["The Sunlit Man"]["year"],
                 "Secret Project 4"),
             row("Isles of the Emberdark",
                 stand["Isles of the Emberdark"]["year"],
                 "Secret Project 5"),
             row("The Fires of December",
                 hoid["The Fires of December"]["year"],
                 "Secret Project 6 · Hoid's Travails — carries the "
                 "bibliography's 2026 date"),
         ]},
    ]

    # the graphic-novel row's years must match the parsed table
    assert [(g["title"], g["year"]) for g in d["graphic"]][:3] == [
        ("White Sand I", 2016), ("White Sand II", 2018),
        ("White Sand III", 2019)]
    assert d["graphic"][3]["year"] == 2022

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == 27 and len(set(ids)) == 27, len(ids)
    assert all(i == slugify(i) and i.isascii() for i in ids)
    # publication order inside every section
    for s in sections:
        ys = [int(x["n"]) for x in s["items"]]
        assert ys == sorted(ys), (s["id"], ys)
    # nothing from the card pair leaked in
    assert not any(x["t"] in CARD_STORIES for s in sections for x in s["items"])

    prop = {
        "slug": SLUG,
        "title": "Cosmere",
        "subtitle": "Brandon Sanderson's connected universe",
        "kind": "books",
        "popularity": 55,
        "year": "2005–",
        "blurb": "The Cosmere in publication order, one section per world — "
                 "Elantris, both Mistborn eras, the Stormlight Archive with "
                 "its novellas in place, and every standalone and Secret "
                 "Project that belongs to the universe.",
        "unit": {"one": "book", "many": "books"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": "#3E4A5C",
        "accentDark": "#9CCDE8",
        "tiers": False,
        "notes": [
            ["Cosmere only, as the bibliography draws the line.",
             "Membership is Wikipedia's own Cosmere section of the Brandon "
             "Sanderson bibliography. Alcatraz, the Cytoverse, the "
             "Reckoners, Legion, his Wheel of Time volumes and The Frugal "
             "Wizard's Handbook (Secret Project 2) are all outside it, so "
             "they are not here."],
            ["Arcanum Unbounded is one row.",
             "The 2016 collection gathers the Cosmere short fiction. The "
             "novellas big enough to read on their own have their own rows "
             "and say so; The Hope of Elantris, The Eleventh Metal and "
             "Allomancer Jak exist only inside the collection, so its one "
             "tick is theirs. The 2024 Story Deck card stories are out."],
            ["Worlds, not a timeline.",
             "Sections group by world or series and run in publication "
             "order inside each; there is no one true Cosmere order and "
             "this page doesn't invent one."],
            ["Nothing is weighted.",
             "A Stormlight brick and a novella each count as one — page "
             "counts differ by edition and faking hours would be worse."],
            "Titles, years and groupings from the Cosmere tables of "
            "Wikipedia's Brandon Sanderson bibliography.",
        ],
        "sections": sections,
    }

    out = here.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json — %d rows" % (SLUG, len(ids)))
    for s in sections:
        print("   %-32s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
