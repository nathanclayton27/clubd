#!/usr/bin/env python3
"""Generate properties/gears-of-war.json.

    python tools/make_gears-of-war.py

The Gears of War campaigns in release order — the 2006 original through
Gears 5 and its Hivebusters expansion — cut into the two eras the franchise
actually has: Epic Games on the Xbox 360, then The Coalition under Microsoft.
Spin-offs and expansions ride in release order alongside the numbered games
rather than being hidden in a section of their own, and carry `opt: 1`, which
is the shape properties/halo.json already uses for the two Halo Wars games.

Where the roster came from
--------------------------
Wikipedia's "Gears of War" article, cached at
scratch/gears-of-war/wiki/Gears-of-War.wiki, and specifically its {{VG
timeline}} — the franchise's own release list, which bolds the main series
and leaves the spin-offs plain:

    2006 Gears of War · 2008 Gears of War 2 · 2011 Gears of War 3 ·
    2013 Judgment · 2015 Ultimate Edition · 2016 Gears of War 4 ·
    2019 Gears Pop! · 2019 Gears 5 · 2020 Gears Tactics ·
    2025 Reloaded · 2026 E-Day

Release dates below are each game's own Wikipedia article, cached in the same
directory; they are in the roster because "release order" is a claim this file
asserts rather than an ordering it assumes. Two years hold two entries each
(2011, 2020) and sorting by year alone would leave the order to luck.

Hours
-----
HowLongToBeat main-story figures through tools/gwlib/hltb.py's verify-by-name
gate, collected by scratch/gears-of-war/fetch_hltb.py into
tools/data/gears-of-war.json. Collection ran with `year_slack=0` and this file
re-asserts the exact year on every row: a same-title-different-year match is
how two shipped lists picked up wrong runtimes (CLU-178), and this franchise
is a minefield for it — the 2006 campaign exists three times over under three
titles and three years. The `howlongtobeatpy` package is dead and must not be
reintroduced; gwlib speaks the live protocol (CLU-130).

Every row on this list carries a real `w`. That is not decoration: the page
computes `WEIGHT = x.w >= 0 ? x.w : 1`, so one missing weight on a weighted
list silently books a game as an hour. There is no unweighted row here and no
mechanism below to produce one — a row whose figure fails the gate fails the
build instead.

The three editorial calls, made deliberately
--------------------------------------------
**Judgment ships, marked optional.** Wikipedia files it under "Spin-offs" and
its timeline leaves it unbolded, so the source does not call it mainline. It
is nevertheless the same genre played the same way, made by Epic with People
Can Fly, and it is a real finishable campaign — so excluding it would hide a
game a Gears club would obviously play. It ships in release order with
`opt: 1`: Baird's court-martial, a squad the numbered line never returns to,
and nothing after it depends on it.

**One row for the first game, not three.** *Ultimate Edition* (2015) and
*Reloaded* (2025) are remasters of the 2006 campaign, not new campaigns, so
they are folded into the 2006 row exactly as properties/halo.json folds
*Anniversary* into *Combat Evolved*. This is asserted rather than asserted-by
-vibes: the generator checks HowLongToBeat times both remasters within three
hours of the original, which is what "same campaign, better lighting" looks
like in the data. Their existence is stated in a note, because Ultimate
Edition is the version that restores the five chapters that were PC-only in
2006.

**Tactics ships optional; Pop! is excluded.** *Gears Tactics* is turn-based
tactics rather than a shooter — a different genre wearing the same war, which
is the identical call halo.json makes for Halo Wars, and it lands in the
Coalition-era section for the same reason Halo Wars 2 sits in the 343 section
despite Creative Assembly building it. It is also, at roughly 25 hours, the
longest campaign here, which is precisely why it must not be silently mixed
into the mainline total. *Gears Pop!* is excluded outright: a Funko-branded
mobile real-time strategy game with no campaign, whose servers Microsoft shut
off on 26 April 2021. There is no version of it left to play, which is the
same rule fps-canon uses to cut live-service shooters.

**The two DLC campaigns ship, marked optional.** *RAAM's Shadow* (2011) and
*Hivebusters* (2020) are separate single-player campaigns with their own
squads, sold apart from the games they attach to, and HowLongToBeat times
both. They are optional because each needs its parent game.

**E-Day is a row, and it weighs nothing until it is out.** The owner's rule,
CLU-315: announced work the source dates — even to a bare year — earns a row;
undated work does not. Its own article's infobox gives `released = October 6,
2026` and its short description reads "Upcoming video game", so it is dated
and it is a row.

An unreleased row carries an explicit `w` of 0, never a missing one. The page
resolves `WEIGHT = x.w >= 0 ? x.w : 1`, so a row without a weight on a
weighted list silently books itself as an hour (CLU-131) — an invented hour
for a game nobody can have played. Zero is the honest figure and it leaves the
other nine rows' verified HowLongToBeat hours alone.

Both directions are asserted against the clock every run:

  * while the date is in the future the row weighs 0, its note says when the
    game is due, and HowLongToBeat is asserted to still have no figure for it
    — the day the site starts timing it this build fails, because a game
    people have finished has shipped;
  * the day the date passes, the build fails unless
    tools/data/gears-of-war.json carries a name-and-year-gated figure. Re-run
    scratch/gears-of-war/fetch_hltb.py and the row weights itself. It cannot
    quietly stay at zero and it cannot quietly become a phantom hour.
"""
import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop as P  # noqa: E402

SLUG = "gears-of-war"
DATA = P.ROOT / "tools" / "data" / "gears-of-war.json"

# How far a remaster's main-story figure may sit from the original's before
# "it is the same campaign" stops being a claim the data supports.
REMASTER_SLACK_H = 3.0

# key, display title, Wikipedia release date, section, opt, note
ROSTER = [
    # ------------------------------------------------------------------ Epic
    ("gow1", "Gears of War", "2006-11-07", "epic", 0,
     "Delta Squad, the Lightmass offensive, and the chest-high wall the "
     "whole decade copied"),
    ("gow2", "Gears of War 2", "2008-11-07", "epic", 0,
     "Six months on, and the COG sink their own city to drown the Hollow"),
    ("gow3", "Gears of War 3", "2011-09-20", "epic", 0,
     "The trilogy's close — the Lambent, Adam Fenix, and the end of the war"),
    ("raam", "Gears of War 3: RAAM's Shadow", "2011-12-13", "epic", 1,
     "Downloadable side campaign for the third game: Zeta-Six at Ilima, and "
     "stretches played as General RAAM himself. The shortest sitting here."),
    ("judgment", "Gears of War: Judgment", "2013-03-19", "epic", 1,
     "Spin-off prequel — Baird's court-martial, told as testimony, with a "
     "squad the numbered games never come back to"),
    # -------------------------------------------------------------- Coalition
    ("gow4", "Gears of War 4", "2016-10-11", "coalition", 0,
     "Twenty-five years after the third game, and a new generation: JD "
     "Fenix, Kait, Del, and the Swarm risen from the Locust's remains"),
    ("gears5", "Gears 5", "2019-09-10", "coalition", 0,
     "Kait's story, and where the Locust actually came from. The longest of "
     "the numbered campaigns."),
    ("tactics", "Gears Tactics", "2020-04-28", "coalition", 1,
     "Turn-based tactics spin-off and a prequel — it opens as the Hammer of "
     "Dawn strikes fall, and follows the man who becomes Kait's father. By "
     "some distance the longest campaign here."),
    ("hivebusters", "Gears 5: Hivebusters", "2020-12-15", "coalition", 1,
     "Downloadable expansion for Gears 5: Scorpio Squad, six chapters in "
     "Sera's South Islands, and the series at its most colourful"),
    ("eday", "Gears of War: E-Day", "2026-10-06", "coalition", 0,
     "Emergence Day itself, fourteen years before the first game — Marcus "
     "and Dom pulled back into a war that starts under their feet, in the "
     "industrial city of Kalona"),
]

# Rows the source dates and nobody can have played yet. Each carries an
# explicit w of 0 and says so in its note; main() asserts the date against the
# clock in both directions, and asserts the HowLongToBeat figure is still
# missing while that date is in the future.
UNRELEASED = {"eday"}

# Prefixed to an unreleased row's own note, so the row still reads correctly
# the day it ships and the note needs no second edit.
NOT_OUT = ("Not out yet — due %s, and the bar stays empty until "
           "HowLongToBeat has hours for it.")

SECTIONS = [
    ("epic", "The Epic years",
     "Epic Games on the Xbox 360, 2006–2013: the Locust war start to "
     "finish, plus the two the numbered trilogy spun off."),
    ("coalition", "The Coalition",
     "Microsoft's own studio picks it up, 2016 on — a new Fenix, a new "
     "enemy, and the series' first turn-based detour."),
]


def longdate(d):
    return "%d %s %d" % (d.day, d.strftime("%B"), d.year)


def named_ok(got, want):
    """The gate's own name test: HowLongToBeat suffixes DLC entries " DLC"."""
    g, w = P.normt(got or ""), P.normt(want)
    return g == w or g == w + " dlc"


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    today = datetime.date.today()

    # --- the roster, verified row by row -----------------------------------
    entries = []
    for key, title, date, sec, opt, note in ROSTER:
        year = int(date[:4])
        rec = data.get(key)
        assert rec, "no HowLongToBeat record for %s — re-run fetch_hltb.py" % key
        assert named_ok(rec["name"], title), \
            "record mismatch for %s: asked %r, got %r" % (key, title, rec["name"])
        # Exact, not a window. Three releases of the 2006 campaign exist under
        # three years; a slack year is how the wrong one gets shipped.
        assert rec["year"] == year, \
            "year mismatch for %s: wiki %d, hltb %s" % (key, year, rec["year"])
        assert rec["wiki_year"] == year, \
            "%s: the fetcher was told %s, this roster says %d" \
            % (key, rec["wiki_year"], year)
        due = datetime.date.fromisoformat(date)
        if key in UNRELEASED and due > today:
            # Dated, not out. The row exists because the source dates it and
            # it weighs nothing because nobody has played it. HowLongToBeat
            # only carries a main-story figure for a game people have
            # finished, so a figure appearing here means it has shipped.
            assert not rec["main_h"], \
                ("HowLongToBeat now times %s (%s h) — it has landed ahead of "
                 "the %s its own article gives. Give the row its hours."
                 % (title, rec["main_h"], due))
            w = 0
            note = "%s %s" % (NOT_OUT % longdate(due), note)
        else:
            # All-or-nothing: the page reads a missing w as one hour, so a row
            # without a real figure must break the build, never ship. That
            # includes a row whose stated release date has passed — it must
            # not stay at zero either.
            assert isinstance(rec["main_h"], (int, float)) and rec["main_h"] > 0, \
                ("no main-story figure for %s (%s) — this list is weighted "
                 "and a row without one would silently count as an hour. If "
                 "the %s date has passed, re-run "
                 "scratch/gears-of-war/fetch_hltb.py."
                 % (key, rec["why"], due))
            w = rec["main_h"]
        x = {"id": "gow-%s" % key, "t": title, "n": str(year),
             "w": w, "note": note, "date": date, "sec": sec}
        if opt:
            x["opt"] = 1
        entries.append(x)

    dates = [e["date"] for e in entries]
    assert dates == sorted(dates), "the roster is out of release order"
    assert len(dates) == len(set(dates)), "two entries share a release date"

    # --- the calls this file makes, asserted against the data --------------
    # One row for the 2006 campaign, not three: both remasters time the same
    # campaign. If either ever drifts, the fold-into-one-row note is no longer
    # true and this build says so.
    original = data["gow1"]["main_h"]
    for key, label in (("ultimate", "Ultimate Edition"), ("reloaded", "Reloaded")):
        rec = data[key]
        assert rec["main_h"], "no figure for the %s remaster" % label
        assert abs(rec["main_h"] - original) <= REMASTER_SLACK_H, \
            ("%s times %s h against the 2006 original's %s h — that is no "
             "longer 'the same campaign, better lighting', so the one-row "
             "decision needs revisiting" % (label, rec["main_h"], original))
    # E-Day is a dated row that weighs nothing until it opens; its date, its
    # missing figure and the clock are asserted in the roster loop above.

    # --- sections ----------------------------------------------------------
    sections = []
    for sec_id, sec_title, intro in SECTIONS:
        got = [e for e in entries if e["sec"] == sec_id]
        assert got, "empty section %s" % sec_id
        years = [int(e["n"]) for e in got]
        hours = sum(e["w"] for e in got)
        pending = [e for e in got if not e["w"]]
        sub = "%d–%d · %d campaigns · %d hours story" \
              % (years[0], years[-1], len(got), round(hours))
        if pending:
            sub += " · %d not out yet" % len(pending)
        sections.append({
            "id": sec_id, "title": sec_title,
            "sub": sub,
            "intro": intro,
            "items": [{k: v for k, v in e.items()
                       if k in ("id", "t", "n", "w", "note", "opt")}
                      for e in got],
        })
    sections[0]["open"] = True

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)) == len(ROSTER), (len(ids), len(ROSTER))
    every = [x for s in sections for x in s["items"]]
    # Weighting is all or nothing: every row declares a w, and the only zeros
    # are the rows this file knows the source dates and nobody can have
    # played. A row with no w at all would book itself as an hour (CLU-131).
    assert all("w" in x for x in every), \
        "a row reached the emitter without a weight"
    assert all(x["w"] >= 0 for x in every), "a negative weight"
    zeros = {x["id"] for x in every if not x["w"]}
    assert zeros == {"gow-%s" % k for k in UNRELEASED
                     if not data[k]["main_h"]}, zeros

    # Every figure below is summed over the campaigns that exist to play, so a
    # dated row with an empty bar cannot move a total or a superlative.
    played = [x for x in every if x["w"]]
    hours = sum(x["w"] for x in played)
    main = sum(x["w"] for x in played if not x.get("opt"))
    longest = max(played, key=lambda x: x["w"])
    shortest = min(played, key=lambda x: x["w"])
    assert longest["id"] == "gow-tactics", \
        "the Tactics note claims it is the longest campaign here; %r is" \
        % longest["t"]
    assert shortest["id"] == "gow-raam", \
        "the RAAM's Shadow note claims it is the shortest sitting here; %r is" \
        % shortest["t"]
    numbered = [x for x in played if not x.get("opt")]
    assert max(numbered, key=lambda x: x["w"])["id"] == "gow-gears5", \
        "the Gears 5 note claims it is the longest of the numbered campaigns"
    # The one date a note prints, taken from the roster rather than retyped.
    eday_due = longdate(datetime.date.fromisoformat(
        next(d for k, _t, d, _s, _o, _n in ROSTER if k == "eday")))

    prop = {
        "slug": SLUG,
        "title": "Gears of War",
        "subtitle": "the campaigns in release order, spin-offs marked",
        "kind": "games",
        # POPULARITY.md's 60-69 band: well known inside its medium, thin
        # outside it. Sits just under Halo (76) and Metal Gear (74), which
        # both sell to people who do not play games, and a shade under
        # Metroid (70) and Silent Hill (69) on name recognition outside the
        # console audience — Gears never had a film, a soundtrack or a
        # Nintendo mascot carrying it past the Xbox.
        "popularity": 68,
        "year": "2006–",
        "blurb": "The Locust war end to end — about %d hours of campaign, "
                 "%d of it the numbered line."
                 % (round(hours), round(main)),
        "unit": {"one": "game", "many": "games"},
        "verb": {"base": "play", "past": "played", "ing": "playing"},
        "itemOrder": "number-first",
        # Light: the caked oxblood of the Crimson Omen. Dark: Imulsion, the
        # glow that lights the back half of the third game. Both checked
        # against every accent shipping in properties/index.json — nearest
        # neighbours are 7.2 and 12.2 CIE76 delta-E, against a catalogue
        # median of 6.8.
        "accent": "#7A2E24",
        "accentDark": "#C9D46A",
        "tiers": False,
        "notes": [
            ["Campaigns, in release order.",
             "This list is the stories. Horde and multiplayer are their own "
             "hobby and keep their own hours. The two downloadable campaigns "
             "sit where they came out rather than being tucked under the "
             "games they attach to, because release order is how the series "
             "actually arrived."],
            ["Judgment is a spin-off, so it is optional.",
             "Wikipedia files it under spin-offs and its release timeline "
             "leaves it unbolded, so the source does not call it mainline — "
             "but it is the same shooter with the same guns, made by Epic "
             "with People Can Fly, and it finishes. It is here because it is "
             "a real campaign; it is marked optional because it is Baird's "
             "court-martial with a squad the numbered games never mention "
             "again, and nothing after it depends on it."],
            ["One row for the first game, not three.",
             "Ultimate Edition (2015) and Reloaded (2025) are remasters of "
             "the 2006 campaign, and HowLongToBeat times all three within "
             "about an hour or two of each other — the same game with better "
             "lighting. The Halo list folds Anniversary into Combat Evolved "
             "for the same reason. Worth knowing anyway: Ultimate Edition is "
             "the version that restores the five chapters which were "
             "PC-only in 2006, and Reloaded is the one that put the first "
             "game on PlayStation."],
            ["Tactics is optional the way Halo Wars is.",
             "Turn-based tactics rather than a shooter — a different genre "
             "wearing the same war. It is a prequel that opens as the Hammer "
             "of Dawn strikes fall, and it follows the man who becomes "
             "Kait's father. It is also the longest campaign here by a wide "
             "margin, which is exactly why it is not folded into the shooter "
             "total. A recap covers it if strategy is not your thing."],
            ["The two expansions need their parent game.",
             "RAAM's Shadow is bought against Gears of War 3 and Hivebusters "
             "against Gears 5, which is why both are marked optional. Each "
             "is a separate campaign with its own squad rather than a "
             "mission pack, and each is a single evening."],
            ["E-Day is here, with an empty bar.",
             "The prequel set fourteen years before the first game is "
             "announced for %s and is not out. It gets a row because its own "
             "article dates it, and the row weighs nothing because nobody has "
             "played it: HowLongToBeat has a record for it and no figure, and "
             "this list refuses to guess one. The date is checked against the "
             "clock on every build — if the site starts timing the game, or "
             "if that date passes with no figure behind it, the build stops "
             "rather than leaving the bar empty or inventing an hour."
             % eday_due],
            ["What is not here.",
             "Gears Pop! was a Funko-branded mobile strategy game with no "
             "campaign, and Microsoft shut its servers off in April 2021 — "
             "there is nothing left to play. The remasters are folded into "
             "the row for the campaign they hold."],
            ["Hours are story only.",
             "HowLongToBeat main-story figures — normal difficulty, no "
             "Insane runs, no Horde, no multiplayer. Every row for a game you "
             "can play carries a real one; nothing on this list was "
             "estimated, and the only row without a figure is the one whose "
             "game is not out."],
            "Game list, release order and dates from Wikipedia's Gears of "
            "War article and the individual game articles; hours from "
            "HowLongToBeat main-story figures, verified by name and exact "
            "release year.",
        ],
        "sections": sections,
    }

    P.write(prop)

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d campaigns (%d playable), %d hours (%d the "
          "numbered line)"
          % (len(sections), len(ids), len(played), round(hours), round(main)))
    for s in sections:
        print("   %-18s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))
    for x in every:
        print("   %-34s %s  w=%-6s%s%s"
              % (x["t"], x["n"], x["w"],
                 "  (optional)" if x.get("opt") else "",
                 "  (not out)" if not x["w"] else ""))


if __name__ == "__main__":
    main()
