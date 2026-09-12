#!/usr/bin/env python3
"""Generate properties/pokemon.json.

    python tools/make_pokemon.py

The Pokemon mainline, one section per generation in release order: the pair
that defines each generation, plus the remakes and third versions that are
different enough from what they retell to be a second sitting, plus the two
Legends games. Ten sections, first generation to tenth.

Where the roster came from
--------------------------
Wikipedia's "Pokemon (video game series)" article, and specifically the
{{tree chart}} in its Games section — the franchise's own "Summary of main
series titles" family tree. It is the only place on Wikipedia that states, in
one machine-readable block, which generation each title belongs to AND which
kind of title it is, under its own column headers:

    System | Generation | Main titles | Derivative titles |
    Upper versions/DLCs | Remake titles | Legends titles | Legends DLC

That column is the editorial spine of this list, and it is the source's
answer rather than this file's. "Is Emerald a main title or an upper
version?" and "is Legends: Arceus one of the numbered games?" are questions
the chart answers; every row below re-asserts the answer it was given.
scratch/pokemon/parse_wiki.py reads the chart, follows every box to the
game's own article, and takes the release dates off its infobox; the tree's
year and the article's own earliest release year agree on all 23 entries,
which is what makes the year safe to assert rather than approximate. The
parsed roster is baked into tools/data/pokemon.json by
scratch/pokemon/fetch_hltb.py — `gen`, `column`, `system`, `wiki_year`,
`wiki_years`, `first_date` and `article` are Wikipedia's, not
HowLongToBeat's, and every one of them is re-asserted below.

Nothing on this page is typed from memory. Every display title IS the title
of the game's own Wikipedia article, asserted string-for-string; years,
release order, generation and the main/remake/upper-version split are read
from the family tree; hours are read from HowLongToBeat.

Hours
-----
HowLongToBeat main-story figures through tools/gwlib/hltb.py's verify-by-name
gate. Collection ran with `year_slack=0` and this file re-asserts the exact
year on every row. Pokemon is the worst franchise in this catalogue for a
loose window, for two compounding reasons: every generation ships twice, once
in Japan and once in the West a year later, and then ships again a decade on
as a remake under a near-identical name. One year of tolerance on "Pokemon
Diamond and Pearl" crosses a regional split; two years on "Pokemon Gold and
Silver" reaches HeartGold. That is precisely the mechanism that put wrong
runtimes on two shipped lists (CLU-178). The site also crawls with fan ROM
hacks — a bare search for "Pokemon Emerald" returns Emerald Seaglass, Emerald
Rogue, Blazing Emerald, Inclement Emerald and Emerald Kaizo — so the
verify-by-name gate is load-bearing here rather than ceremonial.

No row needed a declared year exception. Every one of the 23 records matched
its Wikipedia year exactly at zero slack, and this file additionally asserts
each gated year is one the game's own article lists. Worth knowing anyway:
the years on this page are FIRST release, which for the first five
generations means Japan. Red and Blue is dated 1996 because Pocket Monsters
Red and Green shipped in February 1996; the West did not see Red and Blue
until 1998. HowLongToBeat dates it 1996 too, which is why the two agree.

Every row that has come out carries a real `w`. That is not decoration: the
page computes `WEIGHT = x.w >= 0 ? x.w : 1`, so one missing weight on a
weighted list silently books a forty-hour RPG as an hour — and the home page's
bars now fill by hours on fully weighted lists, so the distortion is visible
to readers rather than buried. There is no unweighted row here and no
mechanism below to produce one: a row whose figure fails the gate fails the
build, and the one row for a game nobody can have played carries an explicit
`w` of 0 rather than no `w` at all.

The calls, made deliberately
----------------------------
**Paired versions are one row.** Red and Blue, Gold and Silver, Sword and
Shield, Scarlet and Violet — every generation ships as two cartridges, and
they are the same game with a different creature list and a different
box legendary. Nobody plays both; you pick one and trade for the rest.
Wikipedia gives each pair a single article, and this list gives each pair a
single row, titled the way that article is titled.

**Third versions and remakes are decided by the runtime test, not by
opinion.** Ten titles retell a game already on this list: the third versions
Yellow, Crystal, Emerald, Platinum and Ultra Sun and Ultra Moon, and the
remakes FireRed and LeafGreen, HeartGold and SoulSilver, Omega Ruby and Alpha
Sapphire, Let's Go and Brilliant Diamond and Shining Pearl. The question each
time is whether it is genuinely a second sitting, and the test is the one
properties/halo.json folds Anniversary on, properties/gears-of-war.json folds
Ultimate Edition on and tools/make_persona.py folds FES on: does
HowLongToBeat time it within three hours of the game it retells?

Four pass and become notes on the row they retell — Yellow and Let's Go on
Red and Blue, Crystal on Gold and Silver, Ultra Sun and Ultra Moon on Sun and
Moon. Six miss and become their own optional rows. The test runs in BOTH
directions and every one of the ten is asserted, because two of them sit
within an hour of the line — FireRed and LeafGreen, and Emerald — and if
either ever drifts inward this build fails and the call gets made again
rather than a row quietly standing on a claim the data stopped supporting.
Each margin is printed in the row's own note by the generator, so the notes
cannot drift away from the figures either. Let's Go is the interesting pass
— a 2018 Switch game folding
into a 1996 row — and it folds because it is Kanto with the same 151
creatures and the site times it within an hour of the original. Its note says
what it actually is.

**Legends games ship, marked optional.** The family tree gives Legends:
Arceus and Legends: Z-A their own column, separate from "Main titles", so the
source does not call them the generation's flagship. They are nevertheless
full Game Freak RPGs that finish, so excluding them would hide two games a
Pokemon club would obviously play. They ship in release order inside the
generation whose chart row they sit on, marked optional, exactly as
properties/gears-of-war.json ships Judgment.

**Black 2 and White 2 is a main row, not an upper version.** It is the only
direct sequel the numbered line has ever made, and the tree files it in the
"Main titles" column alongside Black and White rather than in "Upper
versions". This file asserts that column rather than taking the decision
itself.

**Winds and Waves is a row, and it weighs nothing until it is out.** The
owner's rule, CLU-315: announced work the source dates — even to a bare year —
earns a row, and undated work does not. The family tree dates the tenth
generation 2027 and the games' own article says "They are set to release in
2027", so the pair is dated and it is a row, in a tenth section of its own.

It carries an explicit `w` of 0. A missing `w` would book a full-size Pokemon
RPG as one hour (CLU-131); zero is the honest figure and it leaves the other
eighteen rows' verified HowLongToBeat hours alone. Both directions are
asserted against the clock every run: while 2027 has not passed the row weighs
0 and HowLongToBeat is asserted to still have no figure for it — the day the
site starts timing it, the build fails, because a game people have finished
has shipped — and once that year is behind us the build fails unless there is
a real figure to put beside the row. It cannot quietly stay at zero and it
cannot quietly become a phantom hour. Its section heading and its row note
both say it is not out; no total counts it.

Wikipedia does not name the tenth generation's region yet, so neither does its
section heading. It describes "a tropical archipelago region resembling
Southeast Asia" and gives no in-game name, and this list does not invent one.

**Expansion passes and spin-offs are excluded.** The Isle of Armor and The
Crown Tundra, The Hidden Treasure of Area Zero and Mega Dimension are add-ons
to a game already on this list, played from the same save file rather than
started fresh, which is what separates them from the standalone DLC campaigns
gears-of-war.json ships as rows. Everything under Wikipedia's "Spin-off
games" heading — Mystery Dungeon, Snap, Ranger, GO, Unite, Stadium,
Colosseum, Pinball, Conquest and the rest — is out by the same rule every
franchise list here uses: this list is the mainline.

No tiers
--------
`tiers` is false and the non-spine rows carry `opt` instead, which is the
shape gears-of-war.json uses. The blurb states the mainline hours and the
optional hours as two separate computed numbers so that adding eight
optional rows never quietly rewrites what finishing this list means.
"""
import datetime
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop as P  # noqa: E402

SLUG = "pokemon"
DATA = P.ROOT / "tools" / "data" / "pokemon.json"

# How far a third version's or a remake's main-story figure may sit from the
# figure of the game it retells before "it is the same journey with more in
# it" stops being a claim the data supports and starts being a second
# sitting. The number halo.json, gears-of-war.json and make_persona.py fold
# their remasters and editions on.
EDITION_SLACK_H = 3.0

# key, display title, generation, opt, note. The title is asserted to be the
# name of the game's own Wikipedia article, so nothing here is a title
# somebody typed; the generation is asserted against the family tree.
ROSTER = [
    # ------------------------------------------------------- first, Kanto
    ("rb", "Pokémon Red and Blue", 1, 0, None),        # note computed below
    # ------------------------------------------------------ second, Johto
    ("gs", "Pokémon Gold and Silver", 2, 0, None),     # note computed below
    # ------------------------------------------------------- third, Hoenn
    ("rs", "Pokémon Ruby and Sapphire", 3, 0,
     "Hoenn, 135 new creatures, abilities and natures, and double battles — "
     "two Pokémon out per side at once. Emerald has a row below; the Omega "
     "Ruby remake sits in the sixth generation, where it was made."),
    ("frlg", "Pokémon FireRed and LeafGreen", 3, 1, None),
    ("emerald", "Pokémon Emerald", 3, 1, None),
    # ----------------------------------------------------- fourth, Sinnoh
    ("dp", "Pokémon Diamond and Pearl", 4, 0, None),   # note computed below
    ("platinum", "Pokémon Platinum", 4, 1, None),
    ("hgss", "Pokémon HeartGold and SoulSilver", 4, 1, None),
    # ------------------------------------------------------ fifth, Unova
    ("bw", "Pokémon Black and White", 5, 0, None),     # note computed below
    ("bw2", "Pokémon Black 2 and White 2", 5, 0,
     "The only direct sequel the numbered line has ever made — Unova two "
     "years on, a changed map and a new story rather than a third version. "
     "Wikipedia's family tree files it as a main title, beside Black and "
     "White rather than under them, and this list follows it."),
    # ------------------------------------------------------ sixth, Kalos
    ("xy", "Pokémon X and Y", 6, 0,
     "Kalos, and the jump to the full 3D models the series still uses. "
     "72 new creatures, the Fairy type, and Mega Evolution."),
    ("oras", "Pokémon Omega Ruby and Alpha Sapphire", 6, 1, None),
    # ----------------------------------------------------- seventh, Alola
    ("sm", "Pokémon Sun and Moon", 7, 0, None),        # note computed below
    # ------------------------------------------------------ eighth, Galar
    ("swsh", "Pokémon Sword and Shield", 8, 0, None),  # note computed below
    ("bdsp", "Pokémon Brilliant Diamond and Shining Pearl", 8, 1, None),
    ("la", "Pokémon Legends: Arceus", 8, 1,
     "An action RPG set in Hisui — Sinnoh, centuries before Diamond and "
     "Pearl — where you throw the ball yourself in the open field instead of "
     "opening a battle screen. The tree files the Legends games in their own "
     "column rather than under main titles, which is why this is optional."),
    # ------------------------------------------------------ ninth, Paldea
    ("sv", "Pokémon Scarlet and Violet", 9, 0, None),  # note computed below
    ("lza", "Pokémon Legends: Z-A", 9, 1,
     "The second Legends game, set entirely inside Kalos's Lumiose City five "
     "years after X and Y, with Mega Evolution brought back. Optional for "
     "the same reason Arceus is."),
    # ------------------------------------------------------------ tenth
    ("ww", "Pokémon Winds and Waves", 10, 0, None),   # note computed below
]

# Collected by the fetcher, asserted against, never shipped as a row: the
# four editions the runtime test folds.
ASSERT_ONLY = ("yellow", "crystal", "usum", "lgpe")

# Rows the source dates and nobody can have played yet. Each carries an
# explicit w of 0 and says so in its note; main() asserts the year against the
# clock and asserts the HowLongToBeat figure is still missing while it holds.
UNRELEASED = {"ww"}

# Prefixed to an unreleased row's own note, so the row still reads correctly
# the day it ships and the note needs no second edit.
NOT_OUT = ("Not out yet — dated %s, and the bar stays empty until "
           "HowLongToBeat has hours for it.")

# What each third version or remake retells. Membership of FOLDED versus
# SPLIT is this file's editorial call and the assertion below is what holds
# it to the data — every FOLDED key must time within EDITION_SLACK_H of its
# base and every SPLIT key must miss by more.
FOLDED = {"yellow": "rb", "crystal": "gs", "usum": "sm", "lgpe": "rb"}
SPLIT = {"frlg": "rb", "emerald": "rs", "platinum": "dp", "hgss": "gs",
         "oras": "rs", "bdsp": "dp"}

# generation -> section title and intro. The console is not written here; it
# is read from the family tree and spliced in, so a section cannot claim
# hardware the source does not give it.
SECTIONS = [
    (1, "First generation: Kanto",
     "%s. Where it starts — one town, eight badges, and a Pokédex nobody "
     "can fill on their own."),
    (2, "Second generation: Johto",
     "%s. A clock that keeps running while the cartridge sleeps, and a "
     "second half of the map nobody was told about."),
    (3, "Third generation: Hoenn",
     "%s. A clean break: new hardware, a roster that would not trade "
     "backwards, and the first time the series went back to remake itself."),
    (4, "Fourth generation: Sinnoh",
     "%s. Two screens, the first mainline games you could battle over the "
     "internet, and the generation that went back for Johto."),
    (5, "Fifth generation: Unova",
     "%s. The boldest reset the series has attempted, and the only place "
     "the numbered line ever wrote a direct sequel."),
    (6, "Sixth generation: Kalos",
     "%s. Everything becomes a 3D model, and a new type arrives to "
     "rebalance seventeen years of matchups."),
    (7, "Seventh generation: Alola",
     "%s. Four islands instead of a mainland, and trials instead of gyms."),
    (8, "Eighth generation: Galar",
     "%s. The mainline moves to a console that plugs into a television, "
     "opens up its first genuinely explorable ground, and spins off into a "
     "Sinnoh remake and an open-world prequel inside a single winter."),
    (9, "Ninth generation: Paldea",
     "%s. The series lets go of the corridor at last, and stops minding "
     "much where you go first."),
    # No region name: Wikipedia describes a tropical archipelago resembling
    # Southeast Asia and names no region, so this heading names none either.
    # The second %s is the section's own year span, spliced in below.
    (10, "Tenth generation",
     "%s, and the first generation to leave the original Switch behind. "
     "Dated %s and not out, so it sits here with an empty bar: the tree gives "
     "the year, HowLongToBeat has no hours, and this list will not invent "
     "any."),
]


_WORDS = ("zero one two three four five six seven eight nine ten eleven "
          "twelve thirteen fourteen fifteen sixteen seventeen eighteen "
          "nineteen twenty").split()


def spell(n):
    """A generated count that still reads like prose. "2 Legends games" is
    what a template writes; "two" is what a person writes, and the number
    stays computed either way."""
    return _WORDS[n] if n < len(_WORDS) else str(n)


def span(years):
    """A year range for a section subtitle, without the 1996–1996 tic."""
    return ("%d" % years[0] if years[0] == years[-1]
            else "%d–%d" % (years[0], years[-1]))


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    today = datetime.date.today()

    # --- the roster, verified row by row ------------------------------------
    entries = []
    for key, title, gen, opt, note in ROSTER:
        rec = data.get(key)
        assert rec, "no HowLongToBeat record for %s — re-run fetch_hltb.py" % key
        # The display title IS the name of the game's own Wikipedia article.
        # Nothing on this page is a title somebody remembered.
        assert rec["article"] == title, \
            "%s: Wikipedia titles the article %r, this roster says %r" \
            % (key, rec["article"], title)
        # The HowLongToBeat record the gate landed on, stated here
        # independently of the fetcher's query list.
        assert rec["name"], "%s carries no HowLongToBeat record" % key
        assert P.normt(rec["name"]) == P.normt(rec["query"]), \
            "record mismatch for %s: asked %r, got %r" \
            % (key, rec["query"], rec["name"])
        # Year, exact and three ways: what the site says, what the gate was
        # held to, and what Wikipedia says. No window anywhere. A one-year
        # window here reaches across a Japanese/Western split; a two-year one
        # reaches a remake.
        assert rec["year"] == rec["hltb_year"] == rec["wiki_year"], \
            ("%s: the site says %s, the gate ran against %s, Wikipedia says %s"
             % (key, rec["year"], rec["hltb_year"], rec["wiki_year"]))
        assert rec["hltb_year"] in rec["wiki_years"], \
            ("%s: gated on %s, which is not a year Wikipedia lists for it (%s)"
             % (key, rec["hltb_year"], rec["wiki_years"]))
        # Generation and kind-of-title, taken from the family tree's own
        # columns rather than from whoever edited this list last.
        assert rec["gen"] == gen, \
            "%s: the family tree puts it in generation %s, this roster says %d" \
            % (key, rec["gen"], gen)
        if key in UNRELEASED and not rec["main_h"]:
            # Dated to a year and not out. The row exists because the source
            # dates it and it weighs nothing because nobody has played it.
            # HowLongToBeat only carries a main-story figure for a game people
            # have finished, so a figure here means it has shipped.
            assert today.year <= rec["wiki_year"], \
                ("%s was dated %s and that year has passed with no "
                 "HowLongToBeat figure. Re-run scratch/pokemon/fetch_hltb.py "
                 "— a released row must not stay at w 0, and it must not lose "
                 "its w either (a missing w books itself as one hour)."
                 % (key, rec["wiki_year"]))
            assert not rec["first_date"], \
                ("%s now has a dated release (%s) — read its article again "
                 "and give the row a real date and a figure"
                 % (key, rec["first_date"]))
            w = 0
        else:
            assert rec["first_date"], \
                "%s has no dated release — release order would be a guess" % key
            # All-or-nothing: the page reads a missing w as one hour, so a row
            # without a real figure must break the build, never ship.
            assert isinstance(rec["main_h"], (int, float)) and rec["main_h"] > 0, \
                ("no main-story figure for %s (%s) — this list is weighted and "
                 "a row without one would silently count as an hour"
                 % (key, rec["why"]))
            w = rec["main_h"]
        entries.append({"id": "pkm-%s" % key, "t": title,
                        "n": str(rec["wiki_year"]), "w": w,
                        "note": note, "gen": gen,
                        "opt": opt, "key": key, "date": rec["first_date"],
                        "column": rec["column"], "system": rec["system"]})

    used = {e["key"] for e in entries} | set(ASSERT_ONLY)
    assert used == set(data), \
        "tools/data/pokemon.json and this roster disagree: %r" \
        % sorted(used ^ set(data))
    dates = [e["date"] for e in entries]
    assert len(dates) == len(set(dates)), "two rows share a release date"

    by_key = {e["key"]: e for e in entries}

    # --- the spine, taken from the tree's own column ------------------------
    # A row is in the spine when the family tree calls it a main title. That
    # correspondence is asserted rather than trusted, so the list cannot drift
    # into marking a flagship optional or a Legends game mainline.
    for e in entries:
        assert (e["column"] == "Main") == (not e["opt"]), \
            ("%s sits in the tree's %r column but this list marks it %s"
             % (e["key"], e["column"], "optional" if e["opt"] else "mainline"))
    spine = [e for e in entries if not e["opt"]]
    optional = [e for e in entries if e["opt"]]
    # The rows for games that exist to play. Every total and every superlative
    # below is taken over these, so a dated row with an empty bar can never
    # move a number or win a comparison.
    played = [e for e in entries if e["w"]]
    played_spine = [e for e in spine if e["w"]]
    assert len(spine) == len({e["gen"] for e in spine}) + 1, \
        ("every generation should contribute exactly one flagship row, plus "
         "Black 2 and White 2 — got %d rows across %d generations"
         % (len(spine), len({e["gen"] for e in spine})))

    # --- fold or split, tested the same way in both directions --------------
    # A third version or remake that times within EDITION_SLACK_H of the game
    # it retells is the same journey and belongs in a note; one that does not
    # is a row. Both halves are asserted: if a folded one ever drifts out the
    # note is no longer true, and if a split one ever drifts in the row is no
    # longer earned. Two of the six splits sit within an hour of the line.
    gaps = {}
    for edition, base in list(FOLDED.items()) + list(SPLIT.items()):
        rec, orig = data[edition], data[base]
        assert rec["main_h"], "no figure for %s" % edition
        gaps[edition] = abs(rec["main_h"] - orig["main_h"])
    for edition, base in FOLDED.items():
        assert gaps[edition] <= EDITION_SLACK_H, \
            ("%s times %s h against %s's %s h — that is no longer the same "
             "journey with more in it, so folding it into a note is a claim "
             "the data stopped supporting and it needs its own row"
             % (edition, data[edition]["main_h"], base, data[base]["main_h"]))
    for edition, base in SPLIT.items():
        assert gaps[edition] > EDITION_SLACK_H, \
            ("%s now times within %.2f h of %s — the reason it has its own "
             "row instead of a note has gone, and it should be folded"
             % (edition, gaps[edition], base))
    assert set(FOLDED) | set(SPLIT) == \
        {k for k, v in data.items() if v["column"] in ("UDLC", "Remk")}, \
        ("every upper version and remake the tree draws must be tested: %r"
         % sorted((set(FOLDED) | set(SPLIT)) ^
                  {k for k, v in data.items()
                   if v["column"] in ("UDLC", "Remk")}))
    assert set(SPLIT) == {e["key"] for e in optional
                          if e["column"] in ("UDLC", "Remk")}, \
        "a split edition is missing its row, or a folded one grew one"

    # Which edition sits closest to the game it retells, and which furthest.
    # Two notes say so out loud, and a superlative is exactly the sort of
    # claim that quietly stops being true.
    closest = min(gaps, key=gaps.get)
    widest = max(gaps, key=gaps.get)
    narrowest_split = min(SPLIT, key=gaps.get)
    assert closest == "usum", \
        "the Sun and Moon note calls Ultra Sun the closest pair here; %r is" \
        % closest
    assert widest == "bdsp", \
        "the Brilliant Diamond note calls it the widest gap here; %r is" % widest
    assert narrowest_split == "frlg", \
        "the FireRed note calls it the narrowest split here; %r is" \
        % narrowest_split
    assert data["dp"]["main_h"] == max(e["w"] for e in played), \
        "the Diamond and Pearl note calls it the longest thing here"
    assert data["swsh"]["main_h"] == min(e["w"] for e in played_spine), \
        "the Sword and Shield note calls it the shortest of the mainline rows"
    assert data["hgss"]["main_h"] == max(
        data[k]["main_h"] for k in SPLIT if data[k]["column"] == "Remk"), \
        "the HeartGold note calls it the longest of the remakes here"
    assert data["hgss"]["main_h"] > data["gs"]["main_h"], \
        "the HeartGold note has it running over the 1999 original"
    assert data["frlg"]["main_h"] > data["rb"]["main_h"], \
        "the FireRed note has it running over the 1996 original"
    for key in ("emerald", "platinum", "oras", "bdsp"):
        assert data[key]["main_h"] < data[SPLIT[key]]["main_h"], \
            "%s no longer times under the game it retells" % key

    # Two section intros carry a claim about the calendar rather than about
    # a runtime, so both are checked against the release dates too.
    assert int(by_key["xy"]["n"]) - int(by_key["rb"]["n"]) == 17, \
        "the Kalos intro has the Fairy type rebalancing seventeen years"
    winter = (datetime.date.fromisoformat(by_key["la"]["date"])
              - datetime.date.fromisoformat(by_key["bdsp"]["date"])).days
    assert 0 < winter <= 120, \
        ("the Galar intro puts the Sinnoh remake and the open-world prequel "
         "inside a single winter; they are %d days apart" % winter)

    # The tenth generation is a row of its own, dated and unweighted; the
    # clock and the missing figure are asserted in the roster loop above.
    assert data["ww"]["gen"] == max(v["gen"] for v in data.values()), \
        "the unreleased generation is no longer the newest generation"

    # --- the notes that carry numbers, generated so they cannot rot ---------
    def hrs(gap):
        """A gap in whole hours, rounded up, so 'within N hours' is true."""
        return spell(max(1, math.ceil(gap - 1e-9)))

    by_key["rb"]["note"] = (
        "Kanto, 151 creatures, and a link cable that turned filling the "
        "Pokédex into a two-player problem. Japan got Red and Green in "
        "February 1996; the West got Red and Blue in 1998, which is why the "
        "year beside this row is the earlier one. Yellow (1998) and Let's Go "
        "(2018) both retell it and tick this row — HowLongToBeat times all "
        "three within %s hours of each other." % hrs(max(gaps["yellow"],
                                                         gaps["lgpe"])))
    by_key["gs"]["note"] = (
        "Johto, west of Kanto and three years on, with an internal clock that "
        "gave the world a day and a night — and then the whole of Kanto again "
        "once the credits roll. Crystal (2000) is the third version and ticks "
        "this row, within %s hours of it on HowLongToBeat; it adds a Battle "
        "Tower, animated battle sprites and the option to play as a girl. "
        "The HeartGold remake has its own row, in the fourth generation."
        % hrs(gaps["crystal"]))
    by_key["frlg"]["note"] = (
        "Remake — Kanto rebuilt on Game Boy Advance, with a help menu and the "
        "Sevii Islands opening up after the Elite Four. HowLongToBeat times "
        "it %.1f hours over the 1996 original, which clears the three-hour "
        "fold by little more than half an hour — the narrowest split on this "
        "page, and the reason the test is asserted in both directions. "
        "Nintendo put it back on the Switch in February 2026." % gaps["frlg"])
    by_key["emerald"]["note"] = (
        "Third version — Ruby and Sapphire folded together and extended, with "
        "the Battle Frontier waiting past the credits. HowLongToBeat times it "
        "%.1f hours under the pair it expands, clearing the three-hour fold "
        "by under an hour." % gaps["emerald"])
    by_key["dp"]["note"] = (
        "Sinnoh, 107 new creatures for 493, online play over Nintendo's Wi-Fi "
        "Connection, and the physical/special split, which stopped a move's "
        "type deciding which of your stats it used and quietly rewired every "
        "battle in the series. At %d hours it is the longest thing here."
        % round(data["dp"]["main_h"]))
    by_key["platinum"]["note"] = (
        "Third version — Diamond and Pearl reworked, faster, with the "
        "Distortion World and its altered physics dropped into the middle of "
        "the story. HowLongToBeat times it %.1f hours under the pair it "
        "expands." % gaps["platinum"])
    by_key["hgss"]["note"] = (
        "Remake — Gold and Silver rebuilt on DS, with your lead Pokémon "
        "walking behind you. At %d hours it runs %.1f hours over the 1999 "
        "original and is the longest of the remakes here."
        % (round(data["hgss"]["main_h"]), gaps["hgss"]))
    by_key["bw"]["note"] = (
        "Unova, and 156 new creatures — more than any other generation added, "
        "and for the length of the story the only ones you meet: Game Freak "
        "held every older Pokémon back until the credits so it would feel "
        "like starting over.")
    by_key["oras"]["note"] = (
        "Remake — Hoenn rebuilt in the X and Y engine, eight years after "
        "Ruby and Sapphire. HowLongToBeat times it %.1f hours under the 2002 "
        "original: a different sitting rather than a longer one."
        % gaps["oras"])
    by_key["sm"]["note"] = (
        "Alola, four islands, 88 new creatures, Alolan forms of old ones, and "
        "island trials where the gyms used to be. Ultra Sun and Ultra Moon "
        "(2017) is the enhanced version and ticks this row — HowLongToBeat "
        "times the two %d minutes apart, the closest any pair on this page "
        "comes." % round(gaps["usum"] * 60))
    by_key["swsh"]["note"] = (
        "Galar, 96 new creatures, and the Wild Area — one open stretch with a "
        "free camera and wild Pokémon you can see coming, which is the step "
        "everything since has built on. The shortest of the mainline rows, "
        "narrowly.")
    by_key["bdsp"]["note"] = (
        "Remake — Diamond and Pearl rebuilt by ILCA rather than Game Freak, "
        "and promoted as a faithful one. HowLongToBeat times it %.1f hours "
        "under the DS originals, the widest gap on this page between a remake "
        "and the game it remakes." % gaps["bdsp"])
    by_key["sv"]["note"] = (
        "Paldea, and the series' first true open world: three separate "
        "stories laid over one map, taken in whatever order you like. The "
        "newest generation that has actually shipped — the tenth has a "
        "section of its own below, dated %s and weighing nothing until it "
        "opens."
        % data["ww"]["wiki_year"])
    by_key["ww"]["note"] = (
        "%s Game Freak's tenth generation, and the first for the %s — a "
        "tropical archipelago the source describes and does not name. "
        "Announced, dated, and nobody has played it."
        % (NOT_OUT % data["ww"]["wiki_year"], data["ww"]["system"]))
    assert all(e["note"] for e in entries), \
        "a row reached the emitter without a note"

    # --- sections -----------------------------------------------------------
    sections = []
    for gen, sec_title, intro in SECTIONS:
        # An undated row sorts last inside its generation: the only rows
        # without a first_date are the ones that are not out.
        got = sorted([e for e in entries if e["gen"] == gen],
                     key=lambda e: e["date"] or "9999-99-99")
        assert got, "empty section for generation %d" % gen
        assert [e["date"] for e in got] == \
            [e["date"] for e in entries if e["gen"] == gen], \
            "generation %d is out of the release order Wikipedia gives" % gen
        consoles = {e["system"] for e in got}
        assert len(consoles) == 1, \
            "generation %d spans consoles %s" % (gen, sorted(consoles))
        years = [int(e["n"]) for e in got]
        hours = sum(e["w"] for e in got)
        pending = [e for e in got if not e["w"]]
        if len(pending) == len(got):
            # Nothing here has come out, so there are no hours to state. A
            # section that printed "0 hours story" would be stating a figure
            # it does not have.
            sub_ = "%s · %d %s · not out yet" \
                   % (span(years), len(got),
                      "game" if len(got) == 1 else "games")
        else:
            sub_ = "%s · %d %s · %d hours story" \
                   % (span(years), len(got),
                      "game" if len(got) == 1 else "games", round(hours))
            if pending:
                sub_ += " · %d not out yet" % len(pending)
        sections.append({
            "id": "gen%d" % gen, "title": sec_title,
            "sub": sub_,
            # A section intro takes the console the tree gives it, and may
            # take its own year span as a second argument.
            "intro": intro % (consoles.pop(), span(years))[:intro.count("%s")],
            "items": [{k: v for k, v in e.items()
                       if k in ("id", "t", "n", "w", "note")}
                      | ({"opt": 1} if e["opt"] else {})
                      for e in got],
        })
    sections[0]["open"] = True
    assert [s["id"] for s in sections] == \
        ["gen%d" % g for g in sorted({e["gen"] for e in entries})], \
        "the sections are not the generations the tree gives, in order"

    every = [x for s in sections for x in s["items"]]
    assert len(every) == len(ROSTER), (len(every), len(ROSTER))
    ids = [x["id"] for x in every]
    assert len(ids) == len(set(ids)), "duplicate row ids"
    # Weighting is all or nothing: every row declares a w, and the only zeros
    # are the rows this file knows are dated and not out. A row with no w at
    # all would book itself as an hour (CLU-131).
    assert all("w" in x for x in every), \
        "a row reached the emitter without a weight"
    assert all(x["w"] >= 0 for x in every), "a negative weight"
    zeros = {x["id"] for x in every if not x["w"]}
    assert zeros == {"pkm-%s" % k for k in UNRELEASED
                     if not data[k]["main_h"]}, sorted(zeros)

    hours = sum(x["w"] for x in every)
    spine_h = sum(e["w"] for e in spine)
    opt_h = sum(e["w"] for e in optional)
    legends = [e for e in optional if e["column"] == "Lgnd"]
    assert played_spine[0]["t"].endswith("Red and Blue"), \
        "the blurb opens the mainline on Red and Blue; it opens on %r" \
        % played_spine[0]["t"]
    assert played_spine[-1]["t"].endswith("Scarlet and Violet"), \
        "the blurb closes the mainline on Scarlet and Violet; it closes on %r" \
        % played_spine[-1]["t"]
    coming = [e for e in entries if not e["w"]]
    assert len(coming) == 1 and coming[0]["key"] == "ww", \
        "the blurb names one generation still to come: %r" % coming

    prop = {
        "slug": SLUG,
        "title": "Pokémon",
        "subtitle": "the mainline generations in release order, remakes marked",
        "kind": "games",
        # POPULARITY.md's 80s band, calibrated against the Nintendo lists
        # already shipping: Super Mario 94, Zelda 92, Final Fantasy 82.
        # Pokémon is the larger media franchise but the smaller *game* series
        # in the way this field measures — it sits under Zelda, which carries
        # more weight as a name people invoke without playing games, and well
        # over Final Fantasy.
        "popularity": 88,
        "year": "1996–",
        # Every number here is summed from the weights above. Five lists in
        # this catalogue shipped a blurb contradicting the card printed above
        # it (CLU-190), so there is no row count in this sentence: the card
        # generates one, and what this states is hours.
        "blurb": "The mainline start to finish, Red and Blue through Scarlet "
                 "and Violet — about %d hours of story. The remakes, the "
                 "third versions that diverge and the %s Legends games add "
                 "%d more, and the tenth generation is dated %s with no "
                 "hours behind it yet."
                 % (round(spine_h), spell(len(legends)), round(opt_h),
                    data["ww"]["wiki_year"]),
        "unit": {"one": "game", "many": "games"},
        "verb": {"base": "play", "past": "played", "ing": "playing"},
        "itemOrder": "number-first",
        # Light: the blue of the Pokémon wordmark. Dark: the yellow it is
        # filled with. Checked against every accent shipping in
        # properties/*.json — nearest neighbours are 8.6 and 11.6 CIE76
        # delta-E, against a catalogue median nearest-neighbour of 6.8.
        "accent": "#3B4CCA",
        "accentDark": "#FFCB05",
        "tiers": False,
        "notes": [
            ["One row per pair, not two.",
             "Red and Blue, Gold and Silver, Sword and Shield, Scarlet and "
             "Violet — every generation ships as two cartridges, and they "
             "are the same game with a different creature list and a "
             "different legendary on the box. You pick one and trade for the "
             "rest; nobody plays both. Wikipedia gives each pair one article "
             "and this list gives each pair one row, titled the way that "
             "article is titled."],
            ["Third versions and remakes: notes where the data says fold, "
             "rows where it says split.",
             "Ten titles here retell a game already on the list — Yellow, "
             "Crystal, Emerald, Platinum and Ultra Sun and Ultra Moon on one "
             "side, FireRed and LeafGreen, HeartGold and SoulSilver, Omega "
             "Ruby and Alpha Sapphire, Let's Go and Brilliant Diamond and "
             "Shining Pearl on the other. The question each time is whether "
             "it is really a second sitting, and the test is the one the "
             "Halo, Gears and Persona lists fold their remasters on: does "
             "HowLongToBeat time it within %s hours of the game it retells? "
             "Four pass and became notes on that game's row. Six miss and "
             "became rows of their own. The margins are printed in each "
             "note, and the build checks the test in both directions, so a "
             "fold that drifts apart or a split that drifts together fails "
             "instead of quietly staying wrong."
             % spell(int(EDITION_SLACK_H))],
            ["Let's Go folds into the very first row, and that is not a typo.",
             "It is a 2018 Switch game and it ticks a 1996 one, because it "
             "is Kanto with the same 151 creatures and HowLongToBeat times "
             "the two within an hour. It plays nothing like the original — "
             "wild Pokémon are caught with a flick rather than fought, and a "
             "second player can join in — so it is a genuinely different "
             "evening. It is the same journey, which is what this list "
             "measures."],
            ["The Legends games are optional.",
             "Arceus and Z-A are full Game Freak RPGs and they finish, so "
             "leaving them out would hide two games a Pokémon club would "
             "obviously play. They are marked optional because Wikipedia's "
             "own family tree gives them a column apart from the main "
             "titles: they are not the generation's flagship, they are what "
             "the studio built alongside it. Each sits in the generation "
             "whose chart row it occupies."],
            ["Years are first release, which usually means Japan.",
             "Red and Blue is dated 1996 because Pocket Monsters Red and "
             "Green shipped in February of that year; the West did not get "
             "Red and Blue until 1998. The same gap runs through the first "
             "five generations. HowLongToBeat dates these games the same "
             "way, which is what lets every runtime here be matched on an "
             "exact year rather than a tolerant window — and an exact year "
             "matters in a series where Gold and Silver, HeartGold and "
             "SoulSilver, and a fan hack called Sacred Gold all answer to a "
             "search for the same words."],
            ["The tenth generation is here, with an empty bar.",
             "Winds and Waves is dated %s by the family tree and by its own "
             "article, and dated work belongs on a list even before it comes "
             "out. Its bar is empty because nobody has played it: "
             "HowLongToBeat has a record for it and no figure, and this list "
             "refuses to guess one, so the row counts as a game and adds no "
             "hours to any total. The year is checked against the clock on "
             "every build — if the site starts timing the games, or if %s "
             "passes with no figure behind them, the build stops rather than "
             "leave the bar empty or invent an hour. Wikipedia describes a "
             "tropical archipelago and names no region, so the section "
             "heading names none either."
             % (data["ww"]["wiki_year"], data["ww"]["wiki_year"])],
            ["What is not here.",
             "Spin-offs, first: Mystery Dungeon, Snap, Ranger, GO, Unite, "
             "Stadium, Colosseum, Pinball, Conquest and everything else "
             "under Wikipedia's spin-off heading. This list is the mainline. "
             "Expansion passes are out too — The Isle of Armor and The Crown "
             "Tundra, The Hidden Treasure of Area Zero, Mega Dimension — "
             "because they are add-ons you load into a save file for a game "
             "already on this page rather than something you start."],
            ["Hours are story only.",
             "HowLongToBeat main-story figures — the run to the credits, not "
             "a completed Pokédex, not shiny hunting, not competitive "
             "breeding, and none of the hundreds of hours the endgame will "
             "take if you let it. Every row for a game you can play carries a "
             "real figure; nothing on this list was estimated, a row whose "
             "figure fails the name-and-year check fails this build instead "
             "of shipping unweighted, and the one row with no figure is the "
             "one whose games are not out."],
            "Game list, generations, release order, years and the "
            "main/remake/upper-version split from the family tree in "
            "Wikipedia's Pokémon (video game series) article and each game's "
            "own article; hours from HowLongToBeat main-story figures, "
            "verified by name and exact release year.",
        ],
        "sections": sections,
    }

    P.write(prop)

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d games (%d playable), %d hours (%d mainline, "
          "%d optional)"
          % (len(sections), len(every), len(played), round(hours),
             round(spine_h), round(opt_h)))
    for s in sections:
        print("   %-30s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))
    print("  the %.1f h fold test:" % EDITION_SLACK_H)
    for k in list(FOLDED) + list(SPLIT):
        base = FOLDED.get(k) or SPLIT[k]
        print("   %-9s %-46s %6.2f h  vs %-9s %6.2f h  gap %5.2f  %s"
              % (k, data[k]["name"][:46], data[k]["main_h"], base,
                 data[base]["main_h"], gaps[k],
                 "FOLD" if gaps[k] <= EDITION_SLACK_H else "split"))
    for e in entries:
        print("   %-46s %s  w=%-7s%s%s"
              % (e["t"], e["n"], e["w"],
                 "  (optional)" if e["opt"] else "",
                 "  (not out)" if not e["w"] else ""))


if __name__ == "__main__":
    main()
