#!/usr/bin/env python3
"""Generate properties/fps-canon.json.

    python tools/make_fps_canon.py

A curated canon of 27 genre-defining first-person shooters in release order,
Wolfenstein 3D to Half-Life: Alyx — the lineage rather than a ranking, cut
into four eras: the DOS pioneers, the arena era, the cinematic era, the
modern era.

Where the cut came from
-----------------------
A curated list has no authority except its sources, so this one names them and
then obeys them, including where that hurts.

  1. Wikipedia, "Video games listed among the best first-person shooters" —
     an aggregator that indexes 154 games against 20 published best-of-FPS
     features and footnotes which ones named each game: Paste (2016), Complex
     (2014, 2017), GameSpot (2004, 2026), IGN (2016), PC Gamer (2026), USgamer
     (2014), The A.V. Club (2014), Den of Geek (2023), Digital Trends (2025),
     GamesRadar (2026), Thrillist (2016), Shortlist (2016), TechRadar (2025),
     VG247 (2024), NME (2023), LaptopMag (2022), Maxim (2011) and City
     Magazine (2016). Cached and counted by scratch/fps/parse_wiki_canon.py
     into scratch/fps/wiki_canon.json.
  2. Den of Geek, "30 Best First-Person Shooter Games Ever Made" — a
     ranked all-time canon, read directly from the article rather than
     second-hand and parsed by scratch/fps/parse_denofgeek.py. It is one of
     the twenty above, which is stated rather than hidden: the aggregate
     carries nineteen others, and this one is here because a ranked canon
     read in full is a different check from a footnote count.
  3. Wikipedia, "First-person shooter" — the History section, for the
     question a best-of list does not answer: did the genre keep anything
     from this game. Cached at scratch/fps/First-person-shooter.wiki.

The gate, asserted below and re-run every time this file runs: **a game ships
only if at least 3 of those 20 published lists named it**, and only if it is
something a club can play through to an end. 18 of the 27 also appear in Den
of Geek's ranked 30, which is the cross-check rather than a second gate.

What the gate threw out
-----------------------
Three of the games this list started from failed it and were cut:

  * Unreal (1998) — zero of the twenty name it, and Den of Geek does not
    rank it. Unreal Tournament (eight of twenty, Den of Geek #10) carries the
    Epic line, and an engine's importance is not a game's.
  * Doom II (1994) — two of the twenty, and no editorial canon. It is the
    modding scene's platform and it has the better shotgun, but the canon
    step is Doom.
  * Medal of Honor: Allied Assault (2002) — one of the twenty. Its claim is
    genealogical: the team that made it left to found Infinity Ward. That
    team's first game, Call of Duty, is on the list; the ancestor is not.

Whole branches were cut on the "play through to an end" rule rather than on
counts, and the property notes say so: live-service shooters whose current
shape is not their historical one (Valorant, Counter-Strike 2, Destiny 2,
Apex Legends, Rainbow Six Siege, Escape from Tarkov, Overwatch 2, Battlefield
6), remakes and compilations of games already here (Black Mesa, Halo: The
Master Chief Collection), first-person games that are not shooters (Portal,
Dishonored, Metroid Prime), the immersive sims GameSpot's own 2004 list
disqualified by name as closer to RPGs (System Shock 2, Deus Ex, Prey — the
thread reaches this list through BioShock), and franchise duplicates where
the published lists split with no consensus pick (all four Far Cry entries
sit on three lists each; Left 4 Dead 2, Halo 3, Wolfenstein II and Metro
Exodus each repeat a design already represented).

Hours
-----
HowLongToBeat main-story figures through tools/gwlib/hltb.py's verify-by-name
gate — a figure counts only when the record's name normalizes to the title
asked for and its release year matches. Collected by scratch/fps/fetch_hltb.py
into scratch/fps/hltb.json; all 27 verified, and the two "Doom" records (1993
and 2016) were separated by the gate's nearest-year sort.

Two rows still ship UNWEIGHTED, and the reason is written on the row rather
than replaced with a guess: Counter-Strike and Team Fortress 2 have no
campaign and no ending, so HowLongToBeat's figure for them is time played
rather than time to finish — Team Fortress 2's is 298 hours, more on its own
than every other game on this list put together. Quake III Arena, Unreal
Tournament and Battlefield 1942 keep their figures because each shipped a
bot ladder or single-player campaign that finishes.

Several of these campaigns are famously short — Doom is five hours, Quake
five and a half, Titanfall 2 six — and that is the genre, not a data problem.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop as P  # noqa: E402

SLUG = "fps-canon"
CACHE = P.ROOT / "scratch" / "fps"

# the gate: how many of the 20 published lists must name a game
MIN_LISTS = 3

# Verified by name, but there is no story to time: neither game has a
# campaign or an ending, so HowLongToBeat's number for it is play time.
NOCLOCK = frozenset(("cs", "tf2"))

# key, display title, year, section, Den of Geek's title for it (or None), note
ROSTER = [
    # ------------------------------------------------------------------- DOS
    ("wolf3d", "Wolfenstein 3D", 1992, "dos", None,
     "id Software on DOS, published by Apogee — the genre's shape in one "
     "game: a maze, a gun held in the corner of the screen, and doors."),
    ("doom", "Doom", 1993, "dos", "Doom",
     "id again, a year later, with height, coloured light, level-editing "
     "tools and a multiplayer mode that named itself deathmatch."),
    ("duke3d", "Duke Nukem 3D", 1996, "dos", None,
     "3D Realms on the Build engine — the first shooter whose levels read as "
     "places rather than corridors, and the loudest game of the DOS era."),
    ("quake", "Quake", 1996, "dos", "Quake",
     "id's move to true 3D geometry and mouselook, and the game that turned "
     "online deathmatch and the LAN party into a scene."),
    # ----------------------------------------------------------------- arena
    ("goldeneye", "GoldenEye 007", 1997, "arena", "GoldenEye 007",
     "Rare on the Nintendo 64. The console shooter arrives: four-way split "
     "screen, and objectives that multiply with the difficulty setting."),
    ("halflife", "Half-Life", 1998, "arena", "Half-Life",
     "Valve's first game, and the one that moved the story out of the text "
     "screens between levels and into the level itself, without cutting "
     "away."),
    ("ut", "Unreal Tournament", 1999, "arena", "Unreal Tournament",
     "Epic's arena game — a ladder of bots to climb alone, and the "
     "multiplayer modes the next twenty years borrowed from."),
    ("quake3", "Quake III Arena", 1999, "arena", "Quake 3 Arena",
     "id's arena shooter with the campaign scraped off: movement, weapon "
     "balance and a bot ladder, and nothing else in the box."),
    ("perfectdark", "Perfect Dark", 2000, "arena", None,
     "Rare's follow-up to GoldenEye, pushed past what the Nintendo 64 could "
     "comfortably hold, with bots and a co-operative mode."),
    ("cs", "Counter-Strike", 2000, "arena", "Counter-Strike",
     "A Half-Life mod turned retail release, and the template for round-based "
     "competitive shooters: two teams, one life a round, guns you buy."),
    ("halo", "Halo: Combat Evolved", 2001, "arena", "Halo: Combat Evolved",
     "Bungie's Xbox launch game. Two weapons, recharging shields and a "
     "controller layout console shooters still use unchanged."),
    # ------------------------------------------------------------- cinematic
    ("bf1942", "Battlefield 1942", 2002, "cinematic", None,
     "DICE's combined-arms shooter: dozens of players, vehicles to crew and "
     "a front line that moves — the branch Battlefield has run ever since."),
    ("cod", "Call of Duty", 2003, "cinematic", "Call of Duty",
     "Infinity Ward's first game. The war campaign as a scripted set piece, "
     "built around a squad rather than one soldier."),
    ("halo2", "Halo 2", 2004, "cinematic", None,
     "The Xbox Live one: matchmaking, parties and playlists, which is how "
     "console shooters became something you play online by default."),
    ("halflife2", "Half-Life 2", 2004, "cinematic", "Half-Life 2",
     "Valve on the Source engine, with a physics system the design is built "
     "around. The game most of these lists open with."),
    ("fear", "F.E.A.R.", 2005, "cinematic", "F.E.A.R.",
     "Monolith's shooter, and the enemy AI the genre still measures itself "
     "against — squads that flank, suppress and call it out loud."),
    ("bioshock", "BioShock", 2007, "cinematic", "BioShock",
     "Irrational's shooter with a place to read as well as fight through — "
     "the immersive sim reaching a mainstream audience."),
    ("tf2", "Team Fortress 2", 2007, "cinematic", "Team Fortress 2",
     "Valve's class-based multiplayer game: nine roles, a cartoon art "
     "direction, and the free-to-play economy that followed it."),
    ("cod4", "Call of Duty 4: Modern Warfare", 2007, "cinematic",
     "Call of Duty 4: Modern Warfare",
     "Infinity Ward moves the series to the present day and adds the "
     "levelling, unlocks and killstreaks multiplayer copied for a decade."),
    ("l4d", "Left 4 Dead", 2008, "cinematic", None,
     "Valve's four-player co-op shooter, paced by an AI Director that "
     "rearranges the pressure on every run."),
    # ---------------------------------------------------------------- modern
    ("metro2033", "Metro 2033", 2010, "modern", "Metro 2033",
     "4A Games in the Moscow underground — scarce ammunition doubling as "
     "currency, and a gas mask on a timer."),
    ("borderlands2", "Borderlands 2", 2012, "modern", "Borderlands 2",
     "Gearbox's looter-shooter at full strength: procedurally generated "
     "guns, four classes and drop-in co-op."),
    ("wolftno", "Wolfenstein: The New Order", 2014, "modern", None,
     "MachineGames revives the big single-player campaign, on the series "
     "that started the genre twenty-two years earlier."),
    ("doom2016", "Doom", 2016, "modern", "Doom (2016)",
     "id's reboot, built for speed rather than cover — no regenerating "
     "health, and the head of the retro-shooter revival that followed."),
    ("titanfall2", "Titanfall 2", 2016, "modern", "Titanfall 2",
     "Respawn's wall-running shooter with a mech you call down, wrapped "
     "around the most inventive campaign of its decade."),
    ("doometernal", "Doom Eternal", 2020, "modern", None,
     "The follow-up as a resource puzzle: every weapon and every enemy has a "
     "job, and standing still is not one of them."),
    ("alyx", "Half-Life: Alyx", 2020, "modern", None,
     "Valve in virtual reality — the first full-length shooter designed for "
     "it rather than ported into it."),
]

SECTIONS = [
    ("dos", "The DOS pioneers", 1992, 1996,
     "Four games from id Software and Apogee that invented the genre on DOS. "
     "In four years it goes from a flat maze with a gun in it to fully 3D "
     "geometry, mouselook and online deathmatch."),
    ("arena", "The arena era", 1997, 2001,
     "Deathmatch becomes the point — first on a LAN, then on a console. "
     "Half-Life sits here by date while quietly starting something else, and "
     "Halo closes the era by moving the whole genre onto a controller."),
    ("cinematic", "The cinematic era", 2002, 2009,
     "The campaign becomes a set piece and multiplayer becomes a career: "
     "combined arms, matchmaking, unlock progression, and the first co-op "
     "shooter built around a director."),
    ("modern", "The modern era", 2010, 2999,
     "Survival economies, loot, virtual reality, and two returns to 1993 — "
     "the decade the genre spent facing both directions at once."),
]


def main():
    hours = json.loads((CACHE / "hltb.json").read_text(encoding="utf-8"))
    canon = json.loads((CACHE / "wiki_canon.json").read_text(encoding="utf-8"))
    dog = json.loads((CACHE / "denofgeek30.json").read_text(encoding="utf-8"))

    # the published-list count, keyed by (normalized title, year)
    counts = {(P.normt(g["title"]), g["year"]): g["n"] for g in canon}
    assert len(counts) == len(canon), "the aggregator repeats a game"
    assert len(dog) == 30, "Den of Geek should rank 30, got %d" % len(dog)

    entries, seen_dog = [], set()
    for key, title, year, sec, dogtitle, note in ROSTER:
        rec = hours.get(key)
        assert rec, "no HowLongToBeat record for %s" % key
        assert P.normt(rec["name"] or "") == P.normt(title), \
            "record mismatch for %s: %r" % (key, rec["name"])
        assert int(rec["year"]) == year, \
            "year mismatch for %s: roster %d, HLTB %s" % (key, year, rec["year"])

        n = counts.get((P.normt(title), year))
        assert n is not None, \
            "%s (%d) is not in the published-list aggregate at all" % (title, year)
        assert n >= MIN_LISTS, \
            ("%s (%d) is named by %d of the 20 published lists; the gate is %d"
             % (title, year, n, MIN_LISTS))

        if dogtitle is not None:
            assert dogtitle in dog, \
                "Den of Geek does not rank %r" % dogtitle
            seen_dog.add(dogtitle)

        x = {"id": "fps-%s" % key, "t": title, "n": str(year),
             "year": year, "sec": sec, "note": note, "lists": n}
        if key not in NOCLOCK:
            assert rec["main_h"], "missing hours for %s" % key
            x["w"] = rec["main_h"]
        entries.append(x)

    assert set(hours) == {r[0] for r in ROSTER}, \
        "hours cache and roster disagree: %s" % sorted(
            set(hours) ^ {r[0] for r in ROSTER})
    years = [e["year"] for e in entries]
    assert years == sorted(years), "the roster is out of release order"
    assert len(seen_dog) == 18, \
        "expected 18 of the 27 in Den of Geek's 30, matched %d" % len(seen_dog)

    sections = []
    for key, title, lo, hi, intro in SECTIONS:
        got = [e for e in entries if e["sec"] == key]
        assert got, "empty section %s" % key
        assert all(lo <= e["year"] <= hi for e in got), \
            "%s holds a game outside %d-%d" % (key, lo, hi)
        clocked = [e for e in got if "w" in e]
        bits = ["%d–%d" % (got[0]["year"], got[-1]["year"]),
                "%d games" % len(got)]
        if len(clocked) == len(got):
            bits.append("%d hours story" % round(sum(e["w"] for e in clocked)))
        else:
            bits.append("%d hours story across %d"
                        % (round(sum(e["w"] for e in clocked)), len(clocked)))
        sections.append({
            "id": key, "title": title, "sub": " · ".join(bits), "intro": intro,
            "items": [{k: v for k, v in e.items()
                       if k in ("id", "t", "n", "w", "note")} for e in got]})
    sections[0]["open"] = True

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)) == len(ROSTER) == 27, (len(ids),)
    weighted = [x for s in sections for x in s["items"] if "w" in x]
    assert len(weighted) == 25, "expected 25 weighted rows, got %d" % len(weighted)
    total = sum(x["w"] for x in weighted)
    shortest = min(weighted, key=lambda x: x["w"])
    by_key = {x["id"][4:]: x for s in sections for x in s["items"]}
    # the figure the site reports for a game with no ending, quoted in a note
    tf2_h = hours["tf2"]["main_h"]
    assert tf2_h > total, \
        ("the Team Fortress 2 note claims its play time beats the whole list; "
         "it is %s h against %s h" % (tf2_h, total))

    prop = {
        "slug": SLUG,
        "title": "The FPS Canon",
        "subtitle": "the genre-defining shooters, in release order",
        "kind": "games",
        # A survey of a genre rather than a franchise: everyone into games
        # knows this lineage cold and almost nobody outside games calls it a
        # canon, which is the 60-69 band in POPULARITY.md. Bottom of that
        # band because it is a curated cut rather than a flagship, and it
        # sits below the two franchise lists it overlaps — Halo (76) and
        # Half-Life & Portal (71) — per that file's second signal.
        "popularity": 60,
        # A genre canon. The same shape as the other canons here, and the
        # release order is history rather than an instruction
        # (Nathan, CLU-372, approved 2026-08-27). Prerequisites, where any
        # exist, live in tools/data/sequences.json and are enforced separately.
        "random": True,
        "year": "1992–2020",
        "blurb": "%d shooters in the order they came out, Wolfenstein 3D to "
                 "Half-Life: Alyx — about %d hours of story across the %d "
                 "that have one."
                 % (len(ROSTER), round(total), len(weighted)),
        "unit": {"one": "game", "many": "games"},
        "verb": {"base": "play", "past": "played", "ing": "playing"},
        "itemOrder": "number-first",
        "accent": "#10851E",
        "accentDark": "#4FE863",
        "tiers": False,
        "notes": [
            ["A canon is only as good as its sources, so here they are.",
             "Every game here is named by at least three of the twenty "
             "published best-of-FPS features that Wikipedia's “Video games "
             "listed among the best first-person shooters” indexes — Paste, "
             "Complex, GameSpot, IGN, PC Gamer, USgamer, The A.V. Club, Den "
             "of Geek, Digital Trends, GamesRadar, Thrillist, Shortlist, "
             "TechRadar, VG247, NME, LaptopMag and Maxim among them. "
             "%d of the %d also sit in Den of Geek's ranked thirty, "
             "read in full as a second check. Nothing was added because it "
             "felt right." % (len(seen_dog), len(ROSTER))],
            ["Release order, not a ranking.",
             "This is a lineage: each of these games left something the ones "
             "after it kept, and reading it top to bottom is watching the "
             "genre argue with itself. The four sections are eras, not "
             "tiers. One wrinkle worth naming — Half-Life lands in the arena "
             "era by its release date while being the game that starts the "
             "cinematic one, and the dates are left honest rather than "
             "tidied."],
            ["Two rows carry no hours, and no number was invented.",
             "Counter-Strike and Team Fortress 2 have no campaign and no "
             "ending, so HowLongToBeat's figure for them is time played "
             "rather than time to finish — Team Fortress 2's is %d hours, "
             "more than every other game on this list put together. They "
             "ship unweighted and count as an hour apiece to the bar, which "
             "is a floor rather than a claim. Quake III Arena, Unreal "
             "Tournament and Battlefield 1942 keep their figures: each "
             "shipped a ladder or campaign that ends." % round(tf2_h)],
            ["The campaigns are short, and that is the genre.",
             "The shortest here is %s at about %.0f hours, and it is the one "
             "everything after it answers to. Titanfall 2 is %.0f, Call of "
             "Duty 4 is %.0f. The %d weighted games come to roughly %d hours "
             "between them — about one long open-world game. Shooters were "
             "built to be finished over a weekend and replayed on a harder "
             "setting, and the numbers say so."
             % (shortest["t"], shortest["w"], by_key["titanfall2"]["w"],
                by_key["cod4"]["w"], len(weighted), round(total))],
            ["What is missing, and why.",
             "Four kinds of thing were cut on purpose. Live-service shooters "
             "whose current build is nothing like their historical one — "
             "Valorant, Counter-Strike 2, Destiny 2, Apex Legends, Rainbow "
             "Six Siege — because there is no version of them to play "
             "through. Remakes and compilations of games already here, like "
             "Black Mesa and the Master Chief Collection. First-person games "
             "that are not shooters: Portal, Dishonored, Metroid Prime. And "
             "the immersive sims GameSpot's own 2004 list disqualified by "
             "name as closer to role-playing games — System Shock 2, Deus Ex "
             "— whose thread reaches this list through BioShock instead."],
            ["Three obvious names failed the gate.",
             "Unreal (1998) is named by none of the twenty; Unreal "
             "Tournament carries the Epic line, and an engine's importance "
             "is not a game's. Doom II (1994) is named by two, and by "
             "neither editorial canon — it is the modding scene's platform "
             "and it has the better shotgun, but the canon step is Doom. "
             "Medal of Honor: Allied Assault (2002) is named by one; its "
             "claim is that the team behind it left to found Infinity Ward, "
             "and that team's first game, Call of Duty, is here instead. "
             "Following the sources when they are inconvenient is the whole "
             "point of naming them."],
            "Contents from Wikipedia's “Video games listed among the best "
            "first-person shooters” and Den of Geek's “30 Best "
            "First-Person Shooter Games Ever Made”, cross-read against "
            "Wikipedia's “First-person shooter” history; hours from "
            "HowLongToBeat main-story figures, verified by name and release "
            "year.",
        ],
        "sections": sections,
    }

    P.write(prop)

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d games — %d weighted (%d hours), %d unweighted"
          % (len(sections), len(ids), len(weighted), round(total),
             len(ids) - len(weighted)))
    print("  gate: >=%d of 20 published lists; %d/%d also in Den of Geek's 30"
          % (MIN_LISTS, len(seen_dog), len(ids)))
    for s in sections:
        print("   %-20s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
