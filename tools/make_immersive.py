#!/usr/bin/env python3
"""Generate properties/immersive.json.

    python tools/make_immersive.py

A house canon of 23 immersive sims in release order, Ultima Underworld to
Skin Deep, cut into four eras: the Looking Glass years, the scattered years,
the big-money revival, and the indies.

Why this list needs a stated rule more than most
------------------------------------------------
Nobody agrees what an immersive sim is. Thief, System Shock, Deus Ex and Prey
are not in dispute; everything at the edge is, and a curated list that does
not say where its edge came from is just a person's shelf. So the edge is
mechanical here, and it is re-asserted on every run.

  MEMBERSHIP, and it is the hard gate. Wikipedia's Category:Immersive sims
  must hold the game's article. Read from the API into
  scratch/immersive/category.json by scratch/immersive/fetch_wiki.py.

  EVIDENCE, at least one of four, because that category is uncited and loose
  (it holds Thief Simulator, a burglary game, and Wolfenstein: Youngblood, a
  co-op shooter):
    1. the article's own infobox `genre` field names the genre;
    2. the article's prose names it, and not behind a hedge — "inspired by",
       "similar to", "elements of" and friends are recorded separately, since
       ''Pathologic 2'' mentions the genre nowhere but its category tag and
       ''Indiana Jones and the Great Circle'' only ever compares itself to
       one;
    3. Wikipedia's "Immersive sim" article names the game in its own History
       or Lineage section;
    4. PC Gamer's "History of the best immersive sims" lists it, either in
       the ten dated picks or among the indies (parsed by
       scratch/immersive/parse_pcgamer.py).

  VETO, and it is the only negative evidence in the build. That same PC Gamer
  feature keeps a section for "games outside the immersive sim genre" that use
  some of its traits, and files Alien: Isolation, Hitman: Blood Money and Far
  Cry 3 there. Anything in it is refused, which is what keeps Alien:
  Isolation — a category member — off the list on a citation rather than on
  taste.

  PLAYABLE TO AN END, asserted only by its consequences: no mods (The Dark
  Mod), no compilations (BioShock: The Collection), no expansions of a row
  already here (Dishonored: Death of the Outsider), nothing cancelled
  (Perfect Dark) or unfinished (Gloomwood, Peripeteia, Psycho Patrol R, Core
  Decay), and no remake of a game already on the list (System Shock 2023).
  Shadows of Doubt is here because it left early access in September 2024.

What the gate does not decide
-----------------------------
Which of the survivors ship. Twenty-eight games pass it and 23 are here, so
the last cut is the house's and the property note says so out loud. The five
eligible games left off — Deus Ex: Invisible War, Underworld Ascendant, Gone
Home, Consortium, Neon Struct — are listed in CUT_BUT_ELIGIBLE below and
re-checked against the gate every run, so that claim cannot go stale quietly.

Two rows are here on PC Gamer alone: Vampire: The Masquerade – Bloodlines and
Dark Messiah of Might and Magic. No Wikipedia text anywhere claims either for
the genre; the feature puts both in its canon. Asserted, because it is the
most interesting thing the sources do.

Hours
-----
HowLongToBeat main-story figures through tools/gwlib/hltb.py's verify-by-name
gate — a figure counts only when the record's name normalizes to the title
asked for and the release year matches. Collected by
scratch/immersive/fetch_hltb.py into scratch/immersive/hltb.json. All 23
verified, so this list ships WEIGHTED with no exceptions and no invented
numbers; if a future row cannot be verified, the honest move is to drop the
row or unweight the list, never to guess (CLU-131).
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop as P  # noqa: E402

SLUG = "immersive"
CACHE = P.ROOT / "scratch" / "immersive"

# key, Wikipedia article, display title, year, section, note
ROSTER = [
    # --------------------------------------------------- the Looking Glass years
    ("uu", "Ultima Underworld: The Stygian Abyss",
     "Ultima Underworld: The Stygian Abyss", 1992, "lg",
     "Blue Sky Productions, later Looking Glass — the first role-playing game "
     "with first-person action in a 3D world you can look up and down in, a "
     "few months ahead of Wolfenstein 3D."),
    ("ss1", "System Shock", "System Shock", 1994, "lg",
     "The same idea moved onto a space station, with the story left in logs "
     "to find rather than scenes to watch. The 1994 original, not the remake."),
    ("thief", "Thief: The Dark Project", "Thief: The Dark Project", 1998, "lg",
     "The first PC game to make light and sound the mechanics rather than the "
     "decoration; the team called it a first-person sneaker."),
    ("ss2", "System Shock 2", "System Shock 2", 1999, "lg",
     "Ken Levine with Irrational and Looking Glass together — a shooter's "
     "shape over an RPG's build choices, and the row most of these lists put "
     "at the top."),
    ("thief2", "Thief II", "Thief II: The Metal Age", 2000, "lg",
     "Bigger levels and cleaner systems, made by a studio near bankruptcy: it "
     "shipped in March 2000 and Looking Glass closed in May."),
    ("deusex", "Deus Ex (video game)", "Deus Ex", 2000, "lg",
     "Warren Spector at Ion Storm. Every door has a code, a vent and a "
     "conversation that skips it, and the genre spent the next decade "
     "answering to that."),
    # ----------------------------------------------------- the scattered years
    ("arx", "Arx Fatalis", "Arx Fatalis", 2002, "scatter",
     "Arkane's first game, made because EA would not licence Ultima "
     "Underworld — a dungeon, and spells drawn with the mouse."),
    ("thief3", "Thief: Deadly Shadows", "Thief: Deadly Shadows", 2004,
     "scatter",
     "Ion Storm take the series over and add a city to walk between the jobs."),
    ("bloodlines", "Vampire: The Masquerade – Bloodlines",
     "Vampire: The Masquerade – Bloodlines", 2004, "scatter",
     "Troika's vampire RPG, first-person and systemic — and one of the two "
     "rows here that only a published list claims for the genre."),
    ("darkmessiah", "Dark Messiah of Might and Magic",
     "Dark Messiah of Might and Magic", 2006, "scatter",
     "Arkane on Half-Life 2's engine, with physics as the whole of the "
     "combat. The other row PC Gamer carries and Wikipedia's prose does not."),
    # ------------------------------------------------ the big-money revival
    ("bioshock", "BioShock", "BioShock", 2007, "revival",
     "Irrational's spiritual successor to System Shock 2, systems simplified "
     "and the place doing the talking — the genre in front of everybody."),
    ("hr", "Deus Ex: Human Revolution", "Deus Ex: Human Revolution", 2011,
     "revival",
     "Eidos-Montréal's prequel and the series' first game in eight years; "
     "its boss fights were outsourced to another studio under time pressure."),
    ("dishonored", "Dishonored", "Dishonored", 2012, "revival",
     "Arkane at full strength: a plague city, a teleport that goes up as well "
     "as across, and a game that counts how you got through it."),
    ("mankind", "Deus Ex: Mankind Divided", "Deus Ex: Mankind Divided", 2016,
     "revival",
     "Eidos-Montréal again, built around one dense Prague hub rather than a "
     "world tour."),
    ("dishonored2", "Dishonored 2", "Dishonored 2", 2016, "revival",
     "Two playable characters with separate power sets, and the levels the "
     "series is remembered for."),
    ("prey", "Prey (2017 video game)", "Prey", 2017, "revival",
     "Arkane Austin's System Shock in everything but the name: a station, a "
     "toolkit, and enemies that hide as the furniture."),
    # ------------------------------------------------- small teams, same idea
    ("voidbastards", "Void Bastards", "Void Bastards", 2019, "indies",
     "Blue Manchu's raid-based one — a derelict ship at a time, and a new "
     "survivor when the last one runs out."),
    ("crueltysquad", "Cruelty Squad", "Cruelty Squad", 2021, "indies",
     "Consumer Softproducts in Finland: a serious assassination sim wearing "
     "visuals Rock Paper Shotgun called sensorally aggressive."),
    ("deathloop", "Deathloop", "Deathloop", 2021, "indies",
     "Arkane Lyon's time loop, where the progress is what you have learnt "
     "rather than what you are carrying."),
    ("weirdwest", "Weird West (video game)", "Weird West", 2022, "indies",
     "WolfEye Studios turn the whole thing top-down — the same simulation, "
     "seen from above instead of from behind the eyes."),
    ("mosalina", "Mosa Lina", "Mosa Lina", 2023, "indies",
     "A game that calls itself a hostile interpretation of the form: three "
     "random tools a level, and no promise they fit."),
    ("shadowsofdoubt", "Shadows of Doubt", "Shadows of Doubt", 2023, "indies",
     "A procedurally generated city with one murder in it at a time; out of "
     "early access in September 2024."),
    ("skindeep", "Skin Deep (video game)", "Skin Deep", 2025, "indies",
     "Blendo Games, and the newest here: a stowaway, a cargo ship and a great "
     "deal of improvising."),
]

SECTIONS = [
    ("lg", "The Looking Glass years", 1992, 2000,
     "One studio and the people who left it. In eight years the idea goes "
     "from a dungeon you can look up inside to a conspiracy thriller with a "
     "vent behind every wall."),
    ("scatter", "The scattered years", 2002, 2006,
     "Looking Glass closed two months after Thief II, and the form turns up "
     "in other people's games instead — a dungeon crawler, a vampire RPG, a "
     "Might and Magic spin-off — mostly made by the same handful of people."),
    ("revival", "The big-money revival", 2007, 2017,
     "Publishers try it at scale: three Deus Ex games, two Dishonoreds, and "
     "BioShock and Prey at either end of the decade. BioShock sold three "
     "million copies and most of the rest disappointed somebody, which is why "
     "the next section looks the way it does."),
    ("indies", "Small teams, same idea", 2019, 2025,
     "The budgets left and the genre did not: six games from small studios, "
     "plus Arkane's most recent, which lands here by its date rather than by "
     "who made it."),
]

# Eligible under the gate, and left off by the house. Re-checked every run so
# the property note that names them cannot rot.
CUT_BUT_ELIGIBLE = [
    ("Deus Ex: Invisible War", "the sequel nobody sends you to first"),
    ("Underworld Ascendant", "the lineage's own attempted return"),
    ("Gone Home", "nothing to sneak past or subvert"),
    ("Consortium (video game)", "PC Gamer's inspired indie, and rough"),
    ("Neon Struct", "a smaller Thief, and PC Gamer says as much"),
]

# In the category, and refused by the evidence test rather than by taste.
NOT_ELIGIBLE = ("Alien: Isolation", "Hitman 3",
                "Indiana Jones and the Great Circle", "Amnesia: The Bunker",
                "Pathologic 2", "Wolfenstein: Youngblood", "Thief Simulator")

# PC Gamer's canon picks that the category does not hold. The note about the
# open-world RPGs stands on these two.
CANON_NOT_IN_CATEGORY = ("The Elder Scrolls IV: Oblivion",
                         "Stalker: Call of Pripyat")

# Named in the genre article's History as the mentality's origin, top-down and
# outside the category, which is why this list starts in 1992 instead of 1990.
ULTIMA_VI = "Ultima VI"


def join_and(items):
    """"a, b and c" — the house reads notes aloud, so no serial comma."""
    items = list(items)
    return (" and ".join([", ".join(items[:-1]), items[-1]])
            if len(items) > 1 else items[0])


def evidence(article, display, facts, pcg):
    """Which sources say this game IS an immersive sim."""
    f = facts[article]
    out = []
    if f["genre_field"]:
        out.append("infobox")
    if f["prose_plain"]:
        out.append("prose")
    if f["in_genre_article"]:
        out.append("genre article")
    names = {P.normt(c["title"]) for c in pcg["canon"]} | {
        P.normt(t) for t in pcg["indies"]}
    if P.normt(display) in names or P.normt(article) in names:
        out.append("PC Gamer")
    return out


def main():
    hours = json.loads((CACHE / "hltb.json").read_text(encoding="utf-8"))
    cat = json.loads((CACHE / "category.json").read_text(encoding="utf-8"))
    facts = json.loads((CACHE / "pages.json").read_text(encoding="utf-8"))
    pcg = json.loads((CACHE / "pcgamer.json").read_text(encoding="utf-8"))
    genre_wiki = (CACHE / "Immersive-sim.wiki").read_text(encoding="utf-8")

    members = set(cat["pages"])
    assert cat["category"] == "Category:Immersive sims", cat["category"]
    assert len(members) >= 50, "the category shrank to %d" % len(members)
    assert set(facts) <= members, "a cached page is not in the category"
    assert len(pcg["canon"]) == 10, "PC Gamer's canon is not ten picks"
    vetoed = {P.normt(t) for t in pcg["outside"]}
    assert len(vetoed) == 3, "PC Gamer's outside-the-genre list moved"

    entries, from_genre_article, from_pcgamer, pcgamer_only = [], [], [], []
    for key, article, title, year, sec, note in ROSTER:
        assert article in members, \
            "%s is not in %s" % (article, cat["category"])
        assert article in facts, "no cached article for %s" % article
        src = evidence(article, title, facts, pcg)
        assert src, ("nothing says %s is an immersive sim: infobox no, prose "
                     "no, genre article no, PC Gamer no" % title)
        assert P.normt(title) not in vetoed and P.normt(article) not in vetoed, \
            "%s is on PC Gamer's outside-the-genre list" % title

        # the display title is the article's, optionally with its subtitle
        bare = article.split(" (")[0]
        assert P.normt(title).startswith(P.normt(bare)), \
            "display title %r does not match article %r" % (title, article)

        years = facts[article]["years"]
        assert years, "no release year in %s's infobox" % article
        assert years[0] == year, \
            "%s: roster says %d, the infobox says %s" % (article, year, years[0])

        rec = hours.get(key)
        assert rec, "no HowLongToBeat record for %s" % key
        assert P.normt(rec["name"] or "") == P.normt(title), \
            "record mismatch for %s: %r" % (key, rec["name"])
        assert int(rec["year"]) == year, \
            "year mismatch for %s: roster %d, HLTB %s" % (key, year, rec["year"])
        assert rec["main_h"] and rec["main_h"] > 0, \
            "no main-story figure for %s — this list ships weighted" % key

        if "genre article" in src:
            from_genre_article.append(title)
        if "PC Gamer" in src:
            from_pcgamer.append(title)
        if src == ["PC Gamer"]:
            pcgamer_only.append(title)
        entries.append({"id": "ims-%s" % key, "t": title, "n": str(year),
                        "w": rec["main_h"], "note": note,
                        "year": year, "sec": sec, "src": src})

    assert set(hours) == {r[0] for r in ROSTER}, \
        "hours cache and roster disagree: %s" % sorted(
            set(hours) ^ {r[0] for r in ROSTER})
    years = [e["year"] for e in entries]
    assert years == sorted(years), "the roster is out of release order"
    assert len(pcgamer_only) == 2, \
        "expected 2 rows carried by PC Gamer alone, got %s" % pcgamer_only
    assert set(pcgamer_only) == {"Vampire: The Masquerade – Bloodlines",
                                 "Dark Messiah of Might and Magic"}, pcgamer_only

    # the claims the property notes make about what was left out
    assert len(CUT_BUT_ELIGIBLE) == 5, \
        "the note says five eligible games were cut; there are %d" \
        % len(CUT_BUT_ELIGIBLE)
    for article, _why in CUT_BUT_ELIGIBLE:
        assert article in members, "%s is not in the category" % article
        assert evidence(article, article.split(" (")[0], facts, pcg), \
            "%s does not pass the gate, so it is not a house cut" % article
        assert article not in {r[1] for r in ROSTER}, \
            "%s is both cut and on the list" % article
    for article in NOT_ELIGIBLE:
        assert article in members, "%s is not in the category" % article
        assert not evidence(article, article.split(" (")[0], facts, pcg), \
            "%s now passes the gate and cannot be cited as failing it" % article
    for title in CANON_NOT_IN_CATEGORY:
        assert P.normt(title) in {P.normt(c["title"]) for c in pcg["canon"]}, \
            "PC Gamer no longer names %s" % title
        assert not [m for m in members if P.normt(m) == P.normt(title)], \
            "%s joined the category" % title
    assert "Alien: Isolation" in pcg["outside"], \
        "PC Gamer no longer files Alien: Isolation outside the genre"
    assert ULTIMA_VI in genre_wiki and "immersive sim mentality" in genre_wiki, \
        "the genre article no longer calls Ultima VI the mentality's origin"
    assert not [m for m in members if m.startswith(ULTIMA_VI)], \
        "Ultima VI joined the category"
    assert "not necessarily considered immersive sims" in genre_wiki, \
        "the genre article no longer hedges on the Hitman and Zelda games"
    for slug in ("fallout", "elder-scrolls"):
        assert (P.ROOT / "properties" / ("%s.json" % slug)).exists(), \
            "the note points at properties/%s.json and it is gone" % slug

    sections = []
    for key, title, lo, hi, intro in SECTIONS:
        got = [e for e in entries if e["sec"] == key]
        assert got, "empty section %s" % key
        assert all(lo <= e["year"] <= hi for e in got), \
            "%s holds a game outside %d-%d" % (key, lo, hi)
        sections.append({
            "id": key, "title": title,
            "sub": "%d–%d · %d games · %d hours story"
                   % (got[0]["year"], got[-1]["year"], len(got),
                      round(sum(e["w"] for e in got))),
            "intro": intro,
            "items": [{k: v for k, v in e.items()
                       if k in ("id", "t", "n", "w", "note")} for e in got]})
    sections[0]["open"] = True
    assert sum(len(s["items"]) for s in sections) == len(ROSTER), \
        "a row fell out of the sections"
    spans = [(lo, hi) for _k, _t, lo, hi, _i in SECTIONS]
    assert all(a[1] < b[0] for a, b in zip(spans, spans[1:])), \
        "the section year ranges overlap"

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)) == len(ROSTER) == 23, (len(ids),)
    total = sum(x["w"] for s in sections for x in s["items"])
    shortest = min(entries, key=lambda e: e["w"])
    longest = sorted(entries, key=lambda e: -e["w"])[:2]
    assert shortest["t"] == "Mosa Lina", shortest["t"]
    assert {e["t"] for e in longest} == {"Deus Ex",
                                         "Vampire: The Masquerade – Bloodlines"}, \
        [e["t"] for e in longest]

    prop = {
        "slug": SLUG,
        "title": "Immersive Sims",
        "subtitle": "a house canon of the genre nobody can define",
        "kind": "games",
        # Enthusiast band (POPULARITY.md 40-59): the genre's name needs a
        # sentence of explanation to a general audience, and half of these
        # games sold badly on purpose. Well below fps-canon (60), which
        # surveys the mainstream genre this one is the argumentative cousin
        # of, and a couple of points above indie-essentials (43) because
        # BioShock, Dishonored and the Deus Ex games are names a mainstream
        # player recognises. Neighbours at this value: suda51 46,
        # nasuverse 47, Everything Dies 44.
        "popularity": 45,
        # A survey, not a sequence: release order is history rather than an
        # instruction, so the random pick is free to open anywhere. The two
        # direct continuations here (System Shock -> System Shock 2,
        # Dishonored -> Dishonored 2) are prerequisites and live in
        # tools/data/sequences.json, which is enforced separately.
        "random": True,
        "year": "1992–2025",
        "blurb": "%d games in release order, Ultima Underworld to Skin Deep — "
                 "about %d hours of story between them, and a stated rule for "
                 "what counts as one." % (len(ROSTER), round(total)),
        "unit": {"one": "game", "many": "games"},
        "verb": {"base": "play", "past": "played", "ing": "playing"},
        "itemOrder": "number-first",
        "accent": "#71189E",
        "accentDark": "#D98CFF",
        "tiers": False,
        "notes": [
            ["The house's picks — veto freely.",
             "%d games, chosen here, in release order because the form "
             "develops rather than ranks. The rule below decides what is "
             "eligible; a person decided what is on it. If one is not for "
             "you, skip it loudly; if one is missing, that is what the group "
             "chat is for." % len(ROSTER)],
            ["Nobody agrees what an immersive sim is, so here is the rule.",
             "A game ships only if Wikipedia's Category:Immersive sims holds "
             "it — %d articles today — and at least one source says outright "
             "that it is one: the article's own infobox genre field, the "
             "article's prose, Wikipedia's “Immersive sim” article naming it, "
             "or PC Gamer's “History of the best immersive sims”. %d of the "
             "%d are named in the genre article itself and %d are among PC "
             "Gamer's picks. Being compared to the genre does not count: "
             "“inspired by” and “similar to” are all that Indiana Jones and "
             "the Great Circle, Amnesia: The Bunker and the Hitman games "
             "manage, and Pathologic 2 names the genre nowhere but its "
             "category tag."
             % (len(members), len(from_genre_article), len(ROSTER),
                len(from_pcgamer))],
            ["Two rows are here on one magazine's word.",
             "%s are in the category and no Wikipedia text anywhere calls "
             "either an immersive sim — PC Gamer's canon does, and that is "
             "the whole of their claim. Said out loud because it is the "
             "thinnest evidence on the list." % " and ".join(pcgamer_only)],
            ["Alien: Isolation is not here, and that is the sources talking.",
             "PC Gamer keeps a second list of “games outside the immersive "
             "sim genre” that borrow its traits, and files Alien: Isolation, "
             "Hitman: Blood Money and Far Cry 3 in it. Wikipedia's category "
             "holds Isolation and all three modern Hitman games anyway. Where "
             "a category and a sentence disagree, the sentence wins."],
            ["The big open-world RPGs are somewhere else.",
             "The genre article credits The Elder Scrolls IV: Oblivion, "
             "S.T.A.L.K.E.R. and Fallout 3 with reviving the form, and PC "
             "Gamer's canon carries Oblivion and Call of Pripyat outright — "
             "but the category holds none of them, and Fallout and The Elder "
             "Scrolls have their own lists here. The line this one draws is a "
             "building you can solve, not a country you can wander. Ultima VI "
             "(1990), which the genre article calls the first game with the "
             "mentality, is out for the same reason: it is played from above "
             "and the category does not hold it."],
            ["No remakes, no mods, nothing unfinished.",
             "A row has to be a finished game with an end, so System Shock's "
             "2023 remake is out and the 1994 original is the row; The Dark "
             "Mod and BioShock: The Collection are a mod and a compilation; "
             "Dishonored: Death of the Outsider is an expansion of the row "
             "above it; and Gloomwood, Peripeteia, Psycho Patrol R and Core "
             "Decay are still in development. Shadows of Doubt is here "
             "because it left early access in September 2024."],
            ["Eligible, and cut anyway.",
             "Five games pass the rule and the house passed on them: %s. That "
             "is a judgement rather than a finding, so argue it."
             % join_and([a.split(" (")[0] for a, _w in CUT_BUT_ELIGIBLE])],
            ["Hours are story only, and every row has one.",
             "HowLongToBeat main-story figures — credits, not completion. "
             "About %d hours across %d games, an average of %d: nothing here "
             "is a weekend. The longest are %s and %s at roughly %d hours "
             "each; the shortest is %s at under two, and it is built to be "
             "replayed rather than finished."
             % (round(total), len(ROSTER), round(total / len(ROSTER)),
                longest[0]["t"], longest[1]["t"], round(longest[0]["w"]),
                shortest["t"])],
            "Contents gated on Wikipedia's Category:Immersive sims and its "
            "“Immersive sim” article, with PC Gamer's “History of the best "
            "immersive sims” as the published canon; hours from "
            "HowLongToBeat main-story figures, verified by name and release "
            "year.",
        ],
        "sections": sections,
    }

    P.write(prop)

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d games, %d hours story (all weighted)"
          % (len(sections), len(ids), round(total)))
    print("  gate: in %s (%d articles) + at least one source saying so; "
          "%d via the genre article, %d via PC Gamer, %d via PC Gamer alone"
          % (cat["category"], len(members), len(from_genre_article),
             len(from_pcgamer), len(pcgamer_only)))
    for s in sections:
        print("   %-24s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
