#!/usr/bin/env python3
"""Generate properties/grand-theft-auto.json.

    python tools/make_grand-theft-auto.py

Every Grand Theft Auto game in release order, cut into the eras the article's
own release timeline declares: the three Rockstar names — the 2D universe, the
3D universe and the HD universe — and the fourth one, opening in 2026, that
the source has not named. Expansions and handhelds ride in release order
alongside the numbered games rather than being hidden in a section of their own — the shape
properties/gears-of-war.json uses for its two DLC campaigns — and carry
`opt: 1`.

Where the roster came from
--------------------------
Wikipedia's "Grand Theft Auto" article, cached at
scratch/grand-theft-auto/wiki/ and parsed by
scratch/grand-theft-auto/parse_wiki.py into scratch/grand-theft-auto/
roster.json. That script reads TWO independent structures in the same
article and checks them against each other:

  * the {{Timeline of release years}} in "Series history", which supplies
    the release order, the mainline flag (it bolds the main series and
    leaves everything else plain) and the era boundaries its own legend
    names — 1997-2000 the 2D universe, 2001-2007 the 3D universe, 2008-2025
    the HD universe;
  * the "List of games" table, whose Universe column states 2D, 3D or HD per
    game, sourced to Rockstar's own newswire, and whose section headers name
    the group each game sits in.

Every game on both is asserted to get the same universe from each. The
ordering matters here more than usual: four years hold more than one release
and sorting by year alone would leave three sections' order to luck. The
timeline disambiguates them itself (1999a London 1969, 1999b London 1961,
1999c Grand Theft Auto 2; 2004a San Andreas, 2004b Advance; 2009a The Lost
and Damned, 2009b Chinatown Wars, 2009c The Ballad of Gay Tony), and this
file sorts and asserts on those slots.

Nothing on this page is typed from memory. Titles, years, release order,
eras and the mainline split are read from that article; hours are read from
HowLongToBeat; and this file re-states each fact independently and fails if
the data disagrees with it.

Hours
-----
HowLongToBeat main-story figures through tools/gwlib/hltb.py's verify-by-name
gate, collected by scratch/grand-theft-auto/fetch_hltb.py into
tools/data/grand-theft-auto.json. Collection ran with `year_slack=0` and this
file re-asserts the exact year on every row: a same-title-different-year match
is how two shipped lists picked up wrong runtimes (CLU-178), and this series
is a minefield for it — Vice City has shipped on PS2, Xbox, Windows, OS X,
Android, iOS and again in 2021 under the same name. The `howlongtobeatpy`
package is dead and must not be reintroduced; gwlib speaks the live protocol
(CLU-130).

One row is asked for under a name Wikipedia does not use. Wikipedia titles
the second Grand Theft Auto IV expansion *Grand Theft Auto: The Ballad of Gay
Tony*; HowLongToBeat files it as *Grand Theft Auto IV: The Ballad of Gay
Tony*. The row displays Wikipedia's title and the gate was asked for the
site's, and the substitution is declared and asserted below rather than
tolerated by loosening the name test for everybody. (*London, 1969* and
*London, 1961* carry a comma on the site that Wikipedia omits; punctuation
folds out in normalization, so those need no exception.)

Every row on this list carries a real `w`. That is not decoration: the page
computes `WEIGHT = x.w >= 0 ? x.w : 1`, so one missing weight on a weighted
list silently books a 30-hour game as an hour, and the home page's bars fill
by hours. There is no unweighted row here and no mechanism below to produce
one — a row whose figure fails the gate fails the build instead.

The five editorial calls, made deliberately
-------------------------------------------
**The mainline is what the timeline bolds — seven games, and nothing else.**
Grand Theft Auto, 2, III, Vice City, San Andreas, IV and V are the only rows
without `opt`, and this file asserts that correspondence against the parsed
timeline row by row rather than trusting whoever edited the roster last. The
reason is the headline total: someone who has played those seven has played
Grand Theft Auto in the sense that matters, and an optional row stays out of
the pace maths, so eight expansions and handhelds do not quietly rewrite what
"finishing" means.

**The Grand Theft Auto IV expansions are rows, and the split is measured.**
*The Lost and Damned* and *The Ballad of Gay Tony* are separate campaigns
with their own protagonists, sold apart from the game they attach to. The
test is the one halo.json, gears-of-war.json and persona.json fold their
remasters and editions on: does HowLongToBeat time it within three hours of
what it expands? Neither does — they miss by twenty-one hours and nineteen — so each takes its own optional row, and the assertion is written as
a floor, so if the site's figures ever converge the call gets made again
instead of quietly staying wrong.

**The London expansions are rows by the same test, not by analogy.**
*London, 1969* and *London, 1961* expand the 1997 original and miss its
figure by roughly nine and twelve hours. Same three-hour rule, same
direction, same optional marking — and *1961* is marked in its note as
needing *1969* installed, which is a fact about buying it, not about the
runtime.

**The handhelds and top-down games are rows, in the era Rockstar puts them
in.** *Advance*, *Liberty City Stories*, *Vice City Stories* and *Chinatown
Wars* are full games with their own campaigns and their own HowLongToBeat
records, and the timeline leaves all four unbolded, so all four are optional
rows. They sit in the universe the article's own Universe column gives them,
not the one their hardware suggests: *Advance* is a top-down Game Boy Advance
game and sits in the 3D universe as a *Grand Theft Auto III* prequel;
*Chinatown Wars* is a Nintendo DS game and sits in the HD universe because
it is set in *Grand Theft Auto IV*'s Liberty City.

**One row per game, whichever edition you play — and the usual fold test
could not be run.** *Grand Theft Auto: The Trilogy - The Definitive Edition*
(2021) remasters III, Vice City and San Andreas. The three-hour test wants a
per-game figure to compare against a per-game original, and HowLongToBeat has
none: it files the remaster as a single 44-hour bundle record. So the test is
not run and is not pretended to have been run. What IS asserted is (a) that
the per-game Definitive Edition records still do not exist — the day the site
splits them, this build fails and somebody runs the real test — and (b) that
the bundle times more than the longest of the three originals and less than
all three together, which is what "the same three campaigns" looks like and
not what a fourth campaign would. The remaster is named in a note instead of
being given rows.

**Grand Theft Auto VI is a row that weighs nothing, and Online is excluded
because it does not end.** The owner's rule, CLU-315: announced work the
source dates — even to a bare year — earns a row, and undated work does not.
The article dates VI to 19 November 2026, parsed out of its own prose by
scratch/grand-theft-auto/parse_wiki.py, so VI is a row.

It carries an explicit `w` of 0, never a missing one: the page resolves
`WEIGHT = x.w >= 0 ? x.w : 1`, so a row without a weight on a weighted list
silently books itself as an hour (CLU-131) — an invented hour for a game
nobody can have played. Both directions are asserted against the clock every
run. While the date is in the future the row weighs 0, its note says when the
game is due, and HowLongToBeat is asserted to still have no figure for it —
the day the site starts timing it this build fails, because a game people
have finished has shipped. The day that date passes, the build fails unless
tools/data/grand-theft-auto.json carries a name-and-year-gated figure; re-run
scratch/grand-theft-auto/fetch_hltb.py and the row weights itself.

VI also sits in a section of its own, and that is the source's doing rather
than a flourish. The release timeline declares a fourth era at `range4 = 2026
–`, and the List of games table's Universe cell for VI reads {{n/a|TBA}} —
a stated absence, not a parse miss. So Rockstar has not placed the game in a
universe, and this list does not place it in one either: the section carries
the era the timeline gives and says the universe is unnamed. The build
asserts that TBA is still what the table says, so the day the column fills
in, VI moves into the universe the source puts it in rather than staying in
a holding pen nobody revisits. *Grand Theft Auto Online* is on the
timeline, unbolded, and is a persistent multiplayer world with no ending; the
site times it at longer than any single-player game here, which is exactly
why folding it in would rewrite the total. The compilations — Director's Cut,
The Classics Collection, both Double Packs, The Trilogy, Episodes from
Liberty City and IV: Complete Edition — are repackagings of games that
already have rows.
"""
import datetime
import glob
import json
import math
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop as P  # noqa: E402

SLUG = "grand-theft-auto"
DATA = P.ROOT / "tools" / "data" / "grand-theft-auto.json"

# How far an expansion's main-story figure may sit from the game it expands
# before "it is the same sitting" stops being a claim the data supports. The
# number halo.json, gears-of-war.json and persona.json fold on.
EXPANSION_SLACK_H = 3.0

# Floor for the CIE76 distance between this list's accents and every other
# list's, per role. The catalogue's median nearest-neighbour distance is about
# 6.8 in each pool, so a floor of 8 asks this pair to be more distinct than a
# typical neighbour rather than merely not identical.
MIN_ACCENT_DE = 8.0

# The one place HowLongToBeat's name for a game does not normalize to
# Wikipedia's. Declared, not tolerated: every other row must match exactly.
HLTB_NAME_EXCEPTIONS = {
    "tbogt": "Grand Theft Auto IV: The Ballad of Gay Tony",
}

# Universe (from the article's own column) -> section id. A row the article
# dates and leaves without a universe — its Universe cell reads {{n/a|TBA}} —
# goes to the section for the era the release timeline opens at 2026.
SECTION_OF = {"2D": "twod", "3D": "threed", "HD": "hd"}
UNPLACED_SECTION = "next"

# Rows the source dates and nobody can have played yet. Each carries an
# explicit w of 0 and says so in its note; main() asserts the date against the
# clock in both directions and asserts the HowLongToBeat figure is still
# missing while that date is in the future.
UNRELEASED = {"gta6"}

# Grand Theft Auto VI's release date, as the article states it. Not recalled:
# scratch/grand-theft-auto/parse_wiki.py reads "later delayed to 19 November
# 2026" out of the article's own prose and writes it to roster.json, and that
# assertion fails if the sentence ever goes. Stated here because this
# generator's input carries years rather than dates, exactly as the roster
# above does for every other row.
UNRELEASED_DATE = {"gta6": datetime.date(2026, 11, 19)}

# Prefixed to an unreleased row's own note, so the row still reads correctly
# the day it ships and the note needs no second edit.
NOT_OUT = ("Not out yet — due %s, and the bar stays empty until "
           "HowLongToBeat has hours for it.")

# key -> note. Titles, years, order, era and the mainline flag all come from
# tools/data/grand-theft-auto.json; only the prose lives here.
NOTES = {
    "gta1": "The one that started it — a camera straight overhead, three "
            "fictional cities, and chapters you unlock by hitting a points "
            "target rather than by finishing a plot",
    "london69": "The first expansion, and the only one that also reached the "
                "PlayStation: a fictionalised 1960s London, new missions, new "
                "syndicates to work for. Needs the 1997 game.",
    "london61": "A freeware follow-on to 1969, PC only, three months later — "
                "and the shortest thing on this list. It expands the "
                "expansion, so it wants 1969 as well as the original.",
    "gta2": "Anywhere City, a retrofuturistic nowhere, and rival crime "
            "syndicates whose work you take in whatever order you like — the "
            "last of the 2D universe and the strangest of it",
    "gta3": "The one that changed everything: Liberty City in three "
            "dimensions, Claude saying not a word for the whole game, and an "
            "open world people stayed in",
    "vc": "1986, neon and pastel, and Tommy Vercetti with Ray Liotta's voice "
          "— the first Grand Theft Auto whose protagonist speaks",
    "sa": "Three cities and the countryside between them, plus the arrival of "
          "character customisation — the biggest of the 3D-era games by a "
          "wide margin",
    "advance": "A top-down Game Boy Advance prequel to Grand Theft Auto III, "
               "set in the same Liberty City a year earlier. Digital Eclipse "
               "built it rather than a Rockstar studio.",
    "lcs": "A PlayStation Portable exclusive and another Liberty City "
           "prequel to Grand Theft Auto III — ported to the PS2 the following "
           "year and to phones a decade later",
    "vcs": "The second PSP game, and Vice City two years earlier: 1984, and "
           "Vic Vance, a minor character from the 2002 game. A PS2 port "
           "followed five months on.",
    "gta4": "Niko Bellic in a Liberty City rebuilt from scratch, and a series "
            "that trades its customisation features away for realism and "
            "detail",
    "tlad": "A separate campaign running concurrently with Grand Theft Auto "
            "IV: Johnny Klebitz, vice-president of a biker club coming apart. "
            "Needs the 2008 game — or the Episodes from Liberty City disc, "
            "which needs nothing.",
    "cw": "On the Nintendo DS, under a camera you can spin, and set in a "
          "scaled-down Grand Theft Auto IV Liberty City it shares nothing "
          "else with — Huang Lee, and a stolen sword. Later on PSP and "
          "phones.",
    "tbogt": "The other Grand Theft Auto IV campaign, the same weeks seen "
             "from the penthouse rather than the gutter: Luis Lopez, "
             "bodyguard to a nightclub owner. HowLongToBeat files it under "
             "the Grand Theft Auto IV name; the title above is Wikipedia's.",
    "gta5": "A retired bank robber, a street gangster and a drug dealer, one "
            "Los Santos, and a story that cuts between the three of them from "
            "heist to heist — the longest campaign here",
    # The gap is computed in main() and spliced in, so it cannot rot.
    "gta6": "The sixth numbered game, and the first in %d years. Rockstar has "
            "not said which universe it belongs to and the article's table "
            "says TBA, so neither does this list.",
}

# Shipped rows. Order is asserted against the timeline's slots, not trusted.
ROWS = ("gta1", "london69", "london61", "gta2",
        "gta3", "vc", "sa", "advance", "lcs", "vcs",
        "gta4", "tlad", "cw", "tbogt", "gta5", "gta6")

# On the timeline, deliberately not shipped. Each is asserted about below.
EXCLUDED = ("online",)

# Off the timeline entirely, collected only so the calls above can be tested.
ASSERT_ONLY = ("de_trilogy", "eflc", "de3", "devc", "desa")

# Each expansion and the game it expands. Every one of these is expected to
# MISS the fold test — the assertion is a floor, so a future convergence
# fails the build instead of leaving four rows standing on nothing.
EXPANSIONS = {"london69": "gta1", "london61": "gta1",
              "tlad": "gta4", "tbogt": "gta4"}

SECTIONS = [
    ("twod", "The 2D universe",
     "DMA Design's top-down years — one city on screen at a time, a camera "
     "straight overhead, and two expansions that moved the whole thing to "
     "London."),
    ("threed", "The 3D universe",
     "Liberty City, Vice City and San Andreas rebuilt in three dimensions, "
     "plus the three prequels Rockstar's handheld studios filled the gaps "
     "with."),
    ("hd", "The HD universe",
     "A heavier Liberty City and a bigger Los Santos, with two standalone "
     "expansions and one top-down handheld sharing their streets."),
    (UNPLACED_SECTION, "What comes next",
     "Wikipedia's release timeline opens a fourth era in 2026 and its legend "
     "does not name one, and the List of games table gives Grand Theft Auto "
     "VI's universe as TBA. So this section is the era the source declares, "
     "with the universe left unnamed until Rockstar names it."),
]


# --------------------------------------------------------------------------
# accent distance
# --------------------------------------------------------------------------

def longdate(d):
    return "%d %s %d" % (d.day, d.strftime("%B"), d.year)


def _lab(hexstr):
    """CIE L*a*b* for an #rrggbb string, D65."""
    h = hexstr.lstrip("#")
    rgb = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
           for c in rgb]
    r, g, b = lin
    xyz = (r * 0.4124 + g * 0.3576 + b * 0.1805,
           r * 0.2126 + g * 0.7152 + b * 0.0722,
           r * 0.0193 + g * 0.1192 + b * 0.9505)
    white = (0.95047, 1.0, 1.08883)
    f = [(t / w) ** (1 / 3.0) if t / w > 0.008856 else 7.787 * (t / w) + 16 / 116.0
         for t, w in zip(xyz, white)]
    return (116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2]))


def _de(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(_lab(a), _lab(b))))


def check_accents(accent, accent_dark):
    """Assert this pair is unused and unusually distinct; return the neighbours.

    qa_lint.py only refuses an exactly duplicated PAIR, which lets two lists
    end up a delta-E apart and indistinguishable on a phone. This is the
    stricter check the brief asked for, run against every shipped property.
    """
    lights, darks = [], []
    for f in sorted(glob.glob(str(P.ROOT / "properties" / "*.json"))):
        name = os.path.basename(f)
        if name in ("index.json", "search.json", "%s.json" % SLUG):
            continue
        d = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        lights.append((d["slug"], d["accent"]))
        darks.append((d["slug"], d["accentDark"]))
    assert lights, "no other properties found — the uniqueness check is empty"
    out = []
    for role, mine, pool in (("accent", accent, lights),
                             ("accentDark", accent_dark, darks)):
        assert not any(h.lower() == mine.lower() for _, h in pool), \
            "%s %s is already in use" % (role, mine)
        dist, slug, hexs = min((_de(mine, h), s, h) for s, h in pool)
        assert dist >= MIN_ACCENT_DE, \
            ("%s %s sits %.1f CIE76 from %s's %s, under the %.1f floor — "
             "pick another" % (role, mine, dist, slug, hexs, MIN_ACCENT_DE))
        out.append((role, mine, slug, hexs, dist))
    return out


# --------------------------------------------------------------------------

def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    today = datetime.date.today()
    assert set(ROWS) | set(EXCLUDED) | set(ASSERT_ONLY) == set(data), \
        "tools/data/%s.json and this roster disagree: %r" \
        % (SLUG, sorted(set(ROWS) | set(EXCLUDED) | set(ASSERT_ONLY)
                        ^ set(data)))

    # --- the roster, verified row by row -----------------------------------
    entries = []
    for key in ROWS:
        rec = data[key]
        title, year = rec["wiki_title"], rec["wiki_year"]
        assert title and year, "%s carries no Wikipedia title or year" % key
        # Name. The one row whose site name is not Wikipedia's is allowed to
        # differ only because it is the declared exception, spelled out.
        want = HLTB_NAME_EXCEPTIONS.get(key, title)
        assert P.normt(rec["name"] or "") == P.normt(want), \
            "record mismatch for %s: asked %r, got %r" % (key, want, rec["name"])
        if key in HLTB_NAME_EXCEPTIONS:
            assert P.normt(rec["query"]) == P.normt(want), \
                "%s: the fetcher did not ask for the declared name" % key
        else:
            assert P.normt(rec["query"]) == P.normt(title), \
                "%s: the fetcher asked for %r, not Wikipedia's title" \
                % (key, rec["query"])
        # Year, exact and both ways. No window anywhere: Vice City alone has
        # shipped under this name on seven platforms across nineteen years.
        assert rec["year"] == year, \
            "year mismatch for %s: wiki %s, hltb %s" % (key, year, rec["year"])
        due = UNRELEASED_DATE.get(key)
        if key in UNRELEASED and due > today:
            # Dated, not out. The row exists because the source dates it and
            # it weighs nothing because nobody has played it. HowLongToBeat
            # only carries a main-story figure for a game people have
            # finished, so a figure appearing here means it has shipped.
            assert not rec["main_h"], \
                ("HowLongToBeat now times %s (%s h) — it has landed ahead of "
                 "the %s the article gives. Give the row its hours."
                 % (title, rec["main_h"], due))
            w = 0
        else:
            # All-or-nothing: the page reads a missing w as one hour, so a row
            # without a real figure must break the build, never ship. That
            # includes a row whose stated release date has passed — it must
            # not stay at zero either.
            assert isinstance(rec["main_h"], (int, float)) and rec["main_h"] > 0, \
                ("no main-story figure for %s (%s) — this list is weighted "
                 "and a row without one would silently count as an hour. If "
                 "its stated release date has passed, re-run "
                 "scratch/grand-theft-auto/fetch_hltb.py."
                 % (key, rec["why"]))
            w = rec["main_h"]
        # Era, from the article's own Universe column rather than from taste.
        # The one row the table leaves at TBA goes to the era the timeline
        # opens in 2026 — and the day the column fills in, this list moves it.
        if key in UNRELEASED and rec["universe"] is None:
            sec = UNPLACED_SECTION
        else:
            sec = SECTION_OF.get(rec["universe"])
        assert sec, "%s has no universe on Wikipedia's table" % key
        assert (sec == UNPLACED_SECTION) == (key in UNRELEASED
                                             and rec["universe"] is None), \
            ("%s: the table now gives a universe (%r) for a game this list "
             "holds unplaced, or the reverse — move the row into the section "
             "the source puts it in" % (key, rec["universe"]))
        # Mainline versus optional, taken from the timeline's own bolding.
        opt = 0 if rec["main_series"] else 1
        assert NOTES.get(key), "%s reached the emitter without a note" % key
        note = NOTES[key]
        if key == "gta6":
            note = note % (year - data["gta5"]["wiki_year"])
        if not w:
            note = "%s %s" % (NOT_OUT % longdate(due), note)
        entries.append({"id": "gta-%s" % key, "t": title, "n": str(year),
                        "w": w, "note": note, "sec": sec,
                        "opt": opt, "key": key, "slot": rec["slot"]})

    slots = [e["slot"] for e in entries]
    assert slots == sorted(slots), \
        "the roster is out of the release order Wikipedia's timeline gives"
    assert len(slots) == len(set(slots)), "two rows share a timeline slot"

    by_key = {e["key"]: e for e in entries}
    mainline = [e for e in entries if not e["opt"]]
    optional = [e for e in entries if e["opt"]]
    # The rows for games that exist to play. Every total and every superlative
    # below is taken over these, so a dated row with an empty bar cannot move
    # a number or win a comparison.
    played = [e for e in entries if e["w"]]
    assert {e["key"] for e in mainline} == \
        {k for k in ROWS if data[k]["main_series"]}, \
        "the mainline is no longer exactly the games Wikipedia's timeline bolds"
    assert all(data[e["key"]]["group"] == "Main series" for e in mainline), \
        "a mainline row is not in the table's Main series group"

    # --- the calls this file makes, asserted against the data --------------
    # The expansions. Every one is expected to miss the fold test, so each
    # assertion is a floor: converge and the build fails instead of leaving a
    # row standing on a claim the numbers stopped supporting.
    gaps = {}
    for exp, base in EXPANSIONS.items():
        rec, orig = data[exp], data[base]
        assert rec["main_h"] and orig["main_h"], \
            "no figure to test %s against %s" % (exp, base)
        gaps[exp] = abs(rec["main_h"] - orig["main_h"])
        assert gaps[exp] > EXPANSION_SLACK_H, \
            ("%s now times within %.2f h of %s — the reason it has its own "
             "row instead of a note has gone, and it should be folded"
             % (exp, gaps[exp], base))
        # Direction: every expansion is shorter than the game it expands, and
        # the notes read as though that is true.
        assert rec["main_h"] < orig["main_h"], \
            "%s no longer times shorter than %s" % (exp, base)

    # The Definitive Edition. The per-game fold test is not runnable because
    # the site has no per-game record, and this asserts that is still why —
    # if the remaster is ever split into three, run the real test.
    for key in ("de3", "devc", "desa"):
        assert data[key]["name"] is None, \
            ("HowLongToBeat now has a per-game Definitive Edition record "
             "(%s: %r) — the three-hour fold test is runnable, so run it "
             "instead of citing the bundle" % (key, data[key]["name"]))
    de = data["de_trilogy"]
    assert de["main_h"] and de["year"] == 2021, \
        "the Definitive Edition record moved: %r" % de
    remastered = [by_key[k]["w"] for k in ("gta3", "vc", "sa")]
    assert max(remastered) < de["main_h"] < sum(remastered), \
        ("the Definitive Edition times %s h against %s h for the three games "
         "it remasters — it is no longer 'those three campaigns', and the "
         "note that says so needs revisiting"
         % (de["main_h"], round(sum(remastered), 2)))
    # Episodes from Liberty City is named in a note as the standalone disc.
    assert data["eflc"]["main_h"], \
        "no figure for Episodes from Liberty City, which a note names"

    # Grand Theft Auto VI is a dated row that weighs nothing until it opens;
    # its date, its missing figure and the clock are asserted in the row loop
    # above, along with the TBA its section stands on.
    # Grand Theft Auto Online is excluded for not ending. The note says it
    # would outweigh anything here, so that has to keep being true.
    online = data["online"]["main_h"]
    assert online and online > max(e["w"] for e in played), \
        ("Grand Theft Auto Online times %s h, no longer more than every "
         "campaign on this list — the note that justifies cutting it needs "
         "rewriting" % online)

    # --- sections ----------------------------------------------------------
    sections = []
    for sec_id, sec_title, intro in SECTIONS:
        got = [e for e in entries if e["sec"] == sec_id]
        assert got, "empty section %s" % sec_id
        assert [e["slot"] for e in got] == sorted(e["slot"] for e in got), \
            "%s is out of the timeline's release order" % sec_id
        years = [int(e["n"]) for e in got]
        hours = sum(e["w"] for e in got)
        pending = [e for e in got if not e["w"]]
        span = ("%d" % years[0] if years[0] == years[-1]
                else "%d–%d" % (years[0], years[-1]))
        if len(pending) == len(got):
            # Nothing here has come out, so there are no hours to state.
            sub = "%s · %d %s · not out yet" \
                  % (span, len(got), "game" if len(got) == 1 else "games")
        else:
            sub = "%s · %d games · %d hours story" \
                  % (span, len(got), round(hours))
            if pending:
                sub += " · %d not out yet" % len(pending)
        sections.append({
            "id": sec_id, "title": sec_title,
            "sub": sub,
            "intro": intro,
            "items": [{k: v for k, v in e.items()
                       if k in ("id", "t", "n", "w", "note")}
                      | ({"opt": 1} if e["opt"] else {})
                      for e in got],
        })
    sections[0]["open"] = True

    every = [x for s in sections for x in s["items"]]
    ids = [x["id"] for x in every]
    assert len(ids) == len(set(ids)) == len(ROWS), (len(ids), len(ROWS))
    # Weighting is all or nothing: every row declares a w, and the only zeros
    # are the rows this file knows are dated and not out. A row with no w at
    # all would book itself as an hour (CLU-131).
    assert all("w" in x for x in every), \
        "a row reached the emitter without a weight"
    assert all(x["w"] >= 0 for x in every), "a negative weight"
    zeros = {x["id"] for x in every if not x["w"]}
    assert zeros == {"gta-%s" % k for k in UNRELEASED
                     if not data[k]["main_h"]}, sorted(zeros)

    # --- the numbers the blurb and the notes stand on -----------------------
    hours = sum(e["w"] for e in played)
    main_h = sum(e["w"] for e in mainline if e["w"])
    rest_h = sum(e["w"] for e in optional if e["w"])
    longest = max(played, key=lambda e: e["w"])
    shortest = min(played, key=lambda e: e["w"])
    assert longest["key"] == "gta5", \
        "the Grand Theft Auto V note claims it is the longest campaign here; " \
        "%r is" % longest["t"]
    assert shortest["key"] == "london61", \
        "the London 1961 note claims it is the shortest thing here; %r is" \
        % shortest["t"]
    threed = [e for e in played if e["sec"] == "threed"]
    assert max(threed, key=lambda e: e["w"])["key"] == "sa", \
        "the San Andreas note claims it is the biggest of the 3D-era games"
    years_all = [int(e["n"]) for e in entries]

    # ⚠ Moved off #A3195B on 2026-09-12 (CLU-540). Sailor Moon shipped a light
    # accent 1.6 CIE76 away — visually the same pink — and check_accents() below
    # refused to build at all, so this list was frozen: not for CLU-322's Grand
    # Theft Auto VI row, not for anything. Nathan's call on which of the two
    # moved: "yeah let gta have a different color."
    #
    # #A80DA8 was not picked by eye. Every accent shipping in properties/ was
    # converted to CIELAB and a hue/saturation/value grid walked across the band
    # the catalogue actually occupies (L* 30-60); this is the most isolated
    # point found, at 17.7 delta-E from its nearest neighbour — more than double
    # the 8.0 floor, against a catalogue median of about 6.8. It is still a
    # Vice City sign; it is a different hour of the night.
    accent, accent_dark = "#A80DA8", "#FF5FA2"
    neighbours = check_accents(accent, accent_dark)

    prop = {
        "slug": SLUG,
        "title": "Grand Theft Auto",
        "subtitle": "every released game in order, expansions and handhelds "
                    "marked",
        "kind": "games",
        # POPULARITY.md's 80-89 band: a household name outside its medium.
        # Below Mario (94) and Zelda (92), which are children's-television
        # famous; above Final Fantasy (82) and Resident Evil (80), which are
        # famous to people who play games and to nobody else. Grand Theft Auto
        # is the series that gets debated in parliaments and on the evening
        # news, and V is one of the best-selling products in any medium.
        "popularity": 86,
        "year": "%d–%d" % (min(years_all), max(years_all)),
        # Every number here is summed from the weights above. Five lists in
        # this catalogue shipped a blurb contradicting the card printed above
        # it (CLU-190), and the count is left to the card, which generates one.
        "blurb": "Top-down Liberty City to widescreen Los Santos — about %d "
                 "hours of story, %d of it the mainline."
                 % (round(hours), round(main_h)),
        "unit": {"one": "game", "many": "games"},
        "verb": {"base": "play", "past": "played", "ing": "playing"},
        "itemOrder": "number-first",
        # Light: the violet of a Vice City sign after sundown. Dark: the neon
        # pink it burns at. check_accents() above measures both against every
        # accent shipping in properties/ on every build and prints the nearest
        # neighbour — 17.7 CIE76 delta-E for the light one now, against a
        # catalogue median of about 6.8.
        "accent": accent,
        "accentDark": accent_dark,
        "tiers": False,
        "notes": [
            ["The mainline is what Rockstar's own timeline bolds.",
             "Grand Theft Auto, 2, III, Vice City, San Andreas, IV and V — "
             "the entries Wikipedia's release timeline sets in bold. They are "
             "the only rows here that are not optional, because someone who "
             "has played those has played Grand Theft Auto in the sense that "
             "matters. Everything else is marked optional and stays out of "
             "the finish date, so the expansions and the handhelds do not "
             "quietly rewrite what finishing this list means."],
            ["The Grand Theft Auto IV expansions get their own rows.",
             "The Lost and Damned and The Ballad of Gay Tony run alongside "
             "the 2008 game rather than after it — same fortnight, same city, "
             "different protagonist — and each is a full campaign with its "
             "own ending. The test for whether an expansion is a row or a "
             "line in a note is the one the Halo, Gears and Persona lists "
             "use: does HowLongToBeat time it within %d hours of what it "
             "expands? These miss by %d hours and %d, so they are rows. Both "
             "are marked optional because both need Grand Theft Auto IV — or "
             "the Episodes from Liberty City disc, which holds the two of "
             "them and needs no base game of its own."
             % (EXPANSION_SLACK_H, round(gaps["tlad"]), round(gaps["tbogt"]))],
            ["The London expansions pass the same test.",
             "London 1969 moved the 1997 game to a fictionalised 1960s "
             "London, and London 1961 is a freeware follow-on to that. They "
             "miss the original's figure by %d hours and %d, so they are rows "
             "rather than a note, and both are optional: 1969 needs the "
             "original installed and 1961 expands 1969."
             % (round(gaps["london69"]), round(gaps["london61"]))],
            ["The handhelds sit in the era Rockstar puts them in, not the one "
             "their hardware suggests.",
             "Advance, Liberty City Stories, Vice City Stories and Chinatown "
             "Wars are full games with their own campaigns, and the timeline "
             "leaves all four unbolded, so all four are optional. Where they "
             "sit is the article's own Universe column, not a guess: Advance "
             "is a top-down Game Boy Advance game filed in the 3D universe "
             "because it is a Grand Theft Auto III prequel, and Chinatown "
             "Wars is a Nintendo DS game filed in the HD universe because it "
             "is set in Grand Theft Auto IV's Liberty City."],
            ["One row per game, whichever edition you play.",
             "The Trilogy – The Definitive Edition (2021) remasters III, Vice "
             "City and San Andreas, and ticking those three rows is what "
             "playing it means. It is a note rather than three rows for a "
             "blunt reason: HowLongToBeat files the remaster as one %d-hour "
             "bundle and has no per-game record for it, so the three-hour "
             "test that decides these things cannot be run against the "
             "individual games — and this list does not pretend to have run "
             "it. The build checks that those per-game records still do not "
             "exist, so if the site ever adds them the question gets asked "
             "again properly."
             % round(de["main_h"])],
            ["Grand Theft Auto VI is here, with an empty bar.",
             "It is announced for %s and it is not out. It gets a row because "
             "the article dates it, and the row weighs nothing because nobody "
             "has played it: HowLongToBeat has a record for it and no figure, "
             "and this list refuses to guess one, so it counts as a game and "
             "adds no hours to any total. It sits in a section of its own "
             "because Rockstar has not said which universe it belongs to — "
             "the release timeline opens a fourth era in 2026 and the List of "
             "games table gives its universe as TBA. The date and the TBA are "
             "both re-read on every build: if the site starts timing the game, "
             "if that date passes with no figure behind it, or if the table "
             "places the game at last, the build stops rather than leave a "
             "stale row standing." % longdate(UNRELEASED_DATE["gta6"])],
            ["What is not here.",
             "Grand Theft Auto Online is on the timeline and is not on this "
             "list: it is a persistent multiplayer world with no ending, and "
             "HowLongToBeat times it longer than any campaign here, so "
             "folding it in would rewrite the total for something you cannot "
             "finish. The compilations are gone for a duller reason: "
             "Director's Cut, The Classics Collection, both Double Packs, "
             "The Trilogy, Episodes from Liberty City and IV: Complete "
             "Edition are boxes holding games that already have rows."],
            ["Hours are story only.",
             "HowLongToBeat main-story figures — the missions, not the "
             "hidden packages, not the stunt jumps, not a hundred per cent, "
             "and none of it online. Every row for a game you can play "
             "carries a real one; nothing on this list was estimated, a row "
             "whose figure fails the name-and-year check fails this build "
             "instead of shipping unweighted, and the only row without a "
             "figure is the one whose game is not out."],
            "Game list, release order, years, eras and the mainline split "
            "from Wikipedia's Grand Theft Auto article — its release timeline "
            "and its List of games table, read separately and checked against "
            "each other; hours from HowLongToBeat main-story figures, "
            "verified by name and exact release year.",
        ],
        "sections": sections,
    }

    P.write(prop)

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d games (%d playable), %d hours (%d mainline, "
          "%d optional)"
          % (len(sections), len(every), len(played), round(hours),
             round(main_h), round(rest_h)))
    for s in sections:
        print("   %-20s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))
    print("  expansion gaps against the %.1f h fold test:" % EXPANSION_SLACK_H)
    for k in ("london69", "london61", "tlad", "tbogt"):
        print("   %-9s %-44s %6.2f h  vs %-5s %6.2f h  gap %6.2f  %s"
              % (k, data[k]["name"], data[k]["main_h"], EXPANSIONS[k],
                 data[EXPANSIONS[k]]["main_h"], gaps[k],
                 "fold" if gaps[k] <= EXPANSION_SLACK_H else "split"))
    print("  Definitive Edition bundle %.2f h vs %.2f h for III+VC+SA "
          "(no per-game records)"
          % (de["main_h"], sum(remastered)))
    print("  excluded: Online %.2f h (no ending)" % online)
    print("  not out: %s, due %s, w=0"
          % (data["gta6"]["wiki_title"], UNRELEASED_DATE["gta6"]))
    for role, mine, slug, hexs, dist in neighbours:
        print("  %-10s %s  nearest %s %s at %.1f dE" % (role, mine, slug,
                                                        hexs, dist))
    for e in entries:
        print("   %-6s %-44s %s  w=%-7s%s%s"
              % (e["slot"], e["t"], e["n"], e["w"],
                 "  (optional)" if e["opt"] else "",
                 "  (not out)" if not e["w"] else ""))


if __name__ == "__main__":
    main()
