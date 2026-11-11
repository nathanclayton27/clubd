#!/usr/bin/env python3
"""Generate properties/lego-games.json.

    python3 tools/make_lego.py

Every Lego video game, from Wikipedia's "List of Lego video games", fetched
and parsed by scratch/lego/ into tools/data/lego.json. The article merged its
original and licensed tables into one in 2026; the parser keeps each title on
the side the two-table article gave it and stops on a title it has not seen.
The brief, verbatim: lump all the non tie-in Lego games into a first section,
then after Lego Star Wars go nuts.

So the first section is the whole unlicensed catalogue — Lego Island, Racers,
Rock Raiders, Creator, on through Worlds and 2K Drive — and from Lego Star
Wars: The Video Game (2005) the licensed tie-ins are grouped by franchise
family rather than by era, because the data leans that way hard: Star Wars,
the supers, and Harry Potter each have a run long enough to be its own story,
and eras would shuffle those three decks together for no gain.

Choices, stated rather than buried:
- Lego Fortnite is excluded. It is a mode inside Epic's Fortnite, not a
  standalone Lego game — the same line the Star Wars games list draws for
  crossovers into other studios' games.
- Mobile-only rows from the unlicensed table (30 of them, J2ME and app-store
  spinoffs) sit in a compact last section instead of burying Lego Island
  under Lego Duplo Zoo. A licensed mobile spinoff stays with its franchise,
  marked, because a franchise section is a timeline and holes in it lie.
  Mobile-only is mechanical: the article lists no PC, console or handheld
  release. (So Lego Legacy: Heroes Unboxed, which has a Windows port, stays
  in the first section.)
- The two Creator: Harry Potter expansions (2001, 2002) are licensed and
  predate Lego Star Wars; they open the Wizarding World section rather than
  polluting the unlicensed one.
- The Lego Batman Movie Game sits with the film tie-ins, not the supers —
  it adapts the film, alongside the other Lego-movie games.
- The article lists nothing cancelled or unreleased (Lego Batman: Legacy of
  the Dark Knight, once announced, came out on 22 May 2026), so nothing
  needed a shipped/never-shipped call.

No weights. Playtimes for a hundred-odd games are not available at a scale
worth trusting, and a made-up number would go straight into everyone's pace,
so every game counts as one.
"""
import json
import pathlib

SLUG = "lego-games"

STAR_WARS = {
    "Lego Star Wars: The Video Game",
    "Lego Star Wars II: The Original Trilogy",
    "Lego Star Wars: The Complete Saga",
    "Lego Star Wars III: The Clone Wars",
    "Lego Star Wars: Microfighters",
    "Lego Star Wars: The Force Awakens",
    "Lego Star Wars Battles",
    "Lego Star Wars: Castaways",
    "Lego Star Wars: The Skywalker Saga",
}
SUPERS = {
    "Lego Batman: The Videogame",
    "Lego Batman 2: DC Super Heroes",
    "Lego Marvel Super Heroes",
    "Lego Marvel Super Heroes: Universe in Peril",
    "Lego Batman 3: Beyond Gotham",
    "Lego Marvel's Avengers",
    "Lego Marvel Super Heroes 2",
    "Lego DC Super-Villains",
    "Lego Marvel Collection",
    "Lego Batman: Legacy of the Dark Knight",
}
WIZARDING = {
    "Lego Creator: Harry Potter",
    "Creator: Harry Potter and the Chamber of Secrets",
    "Lego Harry Potter: Years 1–4",
    "Lego Harry Potter: Years 5–7",
    "Lego Harry Potter Collection",
}
FILMS = {
    "Lego Indiana Jones: The Original Adventures",
    "Lego Indiana Jones 2: The Adventure Continues",
    "Lego Pirates of the Caribbean: The Video Game",
    "Lego The Lord of the Rings",
    "The Lego Movie Videogame",
    "Lego The Hobbit",
    "Lego Jurassic World",
    "The Lego Batman Movie Game",
    "The Lego Ninjago Movie Video Game",
    "Lego The Incredibles",
    "The Lego Movie 2 Videogame",
}
ONE_OFFS = {
    "Lego Rock Band",
    "Lego Dimensions",
    "Lego Hill Climb Adventures",
    "Lego Horizon Adventures",
}
EXCLUDED = {
    "Lego Fortnite",  # a mode inside Epic's Fortnite, not a standalone game
}

# What an entry is, where the title alone does not say.
NOTES = {
    ("Lego Fun to Build", 1995): "Sega Pico only — the first Lego video game",
    ("Lego Racers", 2007): "Phone game — no relation to the 1999 Lego Racers",
    ("Lego Creator: Harry Potter", 2001):
        "A Lego Creator expansion, four years before Lego Star Wars",
    ("Creator: Harry Potter and the Chamber of Secrets", 2002):
        "A Lego Creator expansion",
    ("Lego Star Wars: The Complete Saga", 2007):
        "Compilation of the first two",
    ("Lego Star Wars: Microfighters", 2014): "Mobile spin-off",
    ("Lego Star Wars Battles", 2019): "Mobile — Apple Arcade",
    ("Lego Star Wars: Castaways", 2021): "Mobile — Apple Arcade",
    ("Lego Marvel Super Heroes: Universe in Peril", 2014):
        "The handheld and mobile version of Lego Marvel Super Heroes",
    ("Lego Harry Potter Collection", 2016):
        "Compilation of the two Years games",
    ("Lego Marvel Collection", 2019): "Compilation",
    ("The Lego Batman Movie Game", 2017): "Mobile tie-in to the film",
    ("Lego Hill Climb Adventures", 2024):
        "Mobile — Lego does Hill Climb Racing",
    ("Lego Horizon Adventures", 2024): "Lego does Horizon Zero Dawn",
    ("Lego Dimensions", 2015): "Toys-to-life, every licence at once",
    ("Lego Rock Band", 2009): "Rock Band with bricks",
}

SECTIONS = [
    ("original", "Original Lego", None,
     "Everything The Lego Group made without borrowing a licence — Lego "
     "Island, Racers, Rock Raiders and Creator through Universe, Worlds, "
     "Bricktales and 2K Drive. Phone-only spinoffs are the last section."),
    ("starwars", "Lego Star Wars", STAR_WARS,
     "The one that invented the formula, and the licence TT has never put "
     "down since."),
    ("supers", "Super heroes", SUPERS,
     "Batman carried DC in, Marvel followed — the capes share one timeline "
     "here."),
    ("wizarding", "Wizarding World", WIZARDING,
     "The two Creator expansions predate Lego Star Wars by four years; the "
     "proper TT games arrive in 2010."),
    ("films", "Film tie-ins", FILMS,
     "One film, one game — Indiana Jones to The Incredibles, plus the games "
     "of Lego's own movies."),
    ("oneoffs", "One-offs", ONE_OFFS,
     "A music game, a toys-to-life platform, and two licensed collaborations "
     "that got a release of their own."),
    ("mobile", "Mobile spinoffs", None,
     "The phone-only end of the unlicensed catalogue — J2ME curios, then a "
     "decade of app-store tie-ins to the toy lines."),
]


def slug(t):
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def item(g):
    it = {"id": "lego-%d-%s" % (g["year"], slug(g["t"])),
          "t": g["t"], "n": str(g["year"])}
    note = NOTES.get((g["t"], g["year"]))
    if note:
        it["note"] = note
    return it


def sub_line(rows):
    lo, hi = rows[0]["year"], rows[-1]["year"]
    span = "%d" % lo if lo == hi else "%d–%d" % (lo, hi)
    return "%s · %d game%s" % (span, len(rows), "" if len(rows) == 1 else "s")


def main():
    data = pathlib.Path(__file__).resolve().parent / "data" / "lego.json"
    d = json.loads(data.read_text(encoding="utf-8"))
    original, licensed = d["original"], d["licensed"]

    # every licensed title is claimed exactly once, or named as excluded —
    # a new row on Wikipedia fails here instead of vanishing
    families = [STAR_WARS, SUPERS, WIZARDING, FILMS, ONE_OFFS, EXCLUDED]
    claimed = set().union(*families)
    got = {g["t"] for g in licensed}
    assert sum(len(f) for f in families) == len(claimed), "a title is in two families"
    assert got == claimed, ("unmapped: %s / unused: %s"
                            % (sorted(got - claimed), sorted(claimed - got)))

    # the two tables stay in the article's row order, which is year order —
    # within a year the source's own order stands, release order being
    # unstated at day level
    buckets = {"original": [g for g in original if not g["mobileOnly"]],
               "mobile": [g for g in original if g["mobileOnly"]]}
    for key, _, fam, _ in SECTIONS:
        if fam is not None:
            buckets[key] = [g for g in licensed if g["t"] in fam]

    sections = []
    for key, title, _, intro in SECTIONS:
        rows = buckets[key]
        assert rows, "empty section %s" % key
        years = [g["year"] for g in rows]
        assert years == sorted(years), "%s out of year order" % key
        sections.append({"id": key, "title": title, "sub": sub_line(rows),
                         "intro": intro, "items": [item(g) for g in rows]})
    sections[0]["open"] = True

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), \
        "duplicate ids: %s" % sorted({i for i in ids if ids.count(i) > 1})[:5]
    assert len(ids) == len(original) + len(licensed) - len(EXCLUDED), \
        (len(ids), len(original), len(licensed))
    sw = next(s for s in sections if s["id"] == "starwars")
    assert sw["items"][0]["t"] == "Lego Star Wars: The Video Game"

    prop = {
        "slug": SLUG,
        "title": "Lego Games",
        "subtitle": "the bricks first, then every licence",
        "kind": "games",
        "popularity": 62,
        "year": "1995–",
        "blurb": "%d games — the unlicensed catalogue in one run, then the "
                 "tie-ins by franchise from Lego Star Wars on." % len(ids),
        "unit": {"one": "game", "many": "games"},
        "verb": {"base": "play", "past": "played", "ing": "playing"},
        "itemOrder": "number-first",
        "accent": "#C4372A",
        "accentDark": "#F0837A",
        "tiers": False,
        "random": True,
        "notes": [
            ["The bricks, then the licences.", "The first section is every "
             "Lego game made without a licence, in release order. From Lego "
             "Star Wars: The Video Game the tie-ins take over, grouped by "
             "franchise family — Star Wars, the supers, the Wizarding World, "
             "the film tie-ins — rather than by era, because those runs are "
             "each long enough to be their own story. The two Creator: Harry "
             "Potter expansions are licensed and predate Lego Star Wars, so "
             "they open the Wizarding World section."],
            ["Mobile spinoffs.", "Phone-only games from the unlicensed "
             "catalogue — no PC, console or handheld release listed — sit in "
             "the last section rather than burying Lego Island under Lego "
             "Duplo Zoo. A licensed mobile spinoff stays with its franchise "
             "and is marked, so no franchise timeline has holes."],
            ["No weights.", "No source for how long a Lego game takes was "
             "confirmed at this scale, so every game counts as one entry "
             "rather than wearing a made-up number. A finish date paces you "
             "by count."],
            ["What is not here.", "Lego Fortnite — a mode inside Epic's "
             "Fortnite rather than a standalone Lego game. Nothing else was "
             "cut: the source lists nothing cancelled."],
            "Titles and years from Wikipedia's list of Lego video games. "
            "The Star Wars games also appear on their own list; ticking one "
            "there does not tick it here.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json — %d sections, %d games" % (SLUG, len(sections), len(ids)))
    for s in sections:
        print("   %-16s %3d  %s" % (s["id"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
