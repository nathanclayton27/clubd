#!/usr/bin/env python3
"""Generate properties/persona.json.

    python tools/make_persona.py

The whole Persona franchise in release order: the six mainline RPGs, the
expanded editions that are different enough from their originals to be a
second sitting, the Persona 3 remake and the dated Persona 4 one, and every
spin-off — the fighting games, the two Persona Q crawlers, the three rhythm
games, Strikers, Tactica and the mobile Phantom X.

Where the roster came from
--------------------------
Wikipedia's "Persona (franchise)" article (formerly "Persona (series)", a
title that now redirects to a disambiguation page), and specifically its {{Video game
timeline}} — the franchise's own release list, which bolds the main series and
leaves everything else plain. scratch/persona/parse_wiki.py reads that
timeline, follows every link to the game's own article, and takes the release
year off its infobox; on all 22 released-or-dated entries the timeline's slot
and the article's own earliest release year agree exactly, which is what makes
the year safe to assert rather than approximate. The parsed roster is baked
into tools/data/persona.json by scratch/persona/fetch_hltb.py — `slot`,
`main_series`, `wiki_year` and `wiki_years` are Wikipedia's, not
HowLongToBeat's, and every one of them is re-asserted below.

Nothing on this page is typed from memory. Titles, years, release order and
the mainline/spin-off split are all read from that timeline; hours are read
from HowLongToBeat; and this file re-states each fact independently and fails
if the data disagrees with it.

Hours
-----
HowLongToBeat main-story figures through tools/gwlib/hltb.py's verify-by-name
gate. Collection ran with `year_slack=0` and this file re-asserts the exact
year on every row: a same-title-different-year match is how two shipped lists
picked up wrong runtimes (CLU-178), and this franchise is a minefield for it —
a bare search for "Persona 3" returns Reload, Portable, FES, Episode Aigis and
a rhythm game before it returns Persona 3. The `howlongtobeatpy` package is
dead and must not be reintroduced; gwlib speaks the live protocol (CLU-130).

One row's HowLongToBeat year is not its first-release year, and it is declared
rather than tolerated: Persona 4 Arena Ultimax reached Japanese arcades in
2013 and consoles worldwide in 2014, and the site times the console release.
The gate still ran at zero slack — against 2014 — and this file asserts that
2014 is a year Wikipedia actually lists for that game. That is the difference
between naming an exception and widening a window.

Every released row carries a real `w`. That is not decoration: the page
computes `WEIGHT = x.w >= 0 ? x.w : 1`, so one missing weight on a weighted
list silently books a 60-hour dungeon crawler as an hour, on a list whose
entire point is that the hours are honest. There is no unweighted row here and
no mechanism below to produce one — a row whose figure fails the gate fails
the build instead. The one exception is declared, not tolerated: a row in
`UNRELEASED` carries an explicit `w: 0`, and only while HowLongToBeat has no
figure for it.

The seven rows this list shipped with keep their ids AND their figures.
Ids are permanent: renaming one silently orphans everybody's ticks. The
figures are frozen for a softer reason — people have a pace schedule against
this list, and moving Persona 3 by a tenth of an hour to no purpose is churn.
scratch/persona/fetch_hltb.py records what today's fetch said beside each
frozen figure, so the freeze is visible rather than invisible.

The four calls, made deliberately
---------------------------------
**Expanded editions: folded where the data says fold, split where it says
split.** FES, Portable, Golden and Royal are not sequels; they are the same
game with more in it, and properties/halo.json folds Anniversary into Combat
Evolved while properties/gears-of-war.json folds Ultimate Edition into the
2006 original. Both of those assert the fold rather than assuming it — the
remaster has to time within three hours of the original — and the same test
runs here, on all four, in both directions. Exactly one passes. *FES* comes in
within two hours of Persona 3, because HowLongToBeat files *The Answer*, the
28-hour epilogue FES added, as a separate record; so FES ticks the Persona 3
row and is named in its note. *Portable*, *Golden* and *Royal* all miss by
more than three hours — Portable by eighteen — so each gets its own optional
row rather than a claim the data will not support. Royal misses by under an
hour of slack and the split rests on that margin, which is precisely why the
assertion is written both ways: if the site's figures ever converge, this
build fails and the call gets made again instead of quietly staying wrong.

**Everything that is not mainline is optional.** Wikipedia's timeline bolds
six released games; those six are the only rows here without `opt`, and this
file asserts that correspondence row by row rather than trusting itself to
have marked them by hand. The reason is the headline total: someone who plays
the six has played Persona in the sense that matters, and an optional row
stays out of the pace maths, so adding thirteen spin-offs and editions does
not silently rewrite what "finishing" means for people already ticking this
list. Persona 3 Reload was already optional for the same reason and stays
where it was.

**The blurb computes its own numbers.** Five lists in this catalogue shipped a
blurb that contradicted the card printed directly above it (CLU-190), and the
one this list had — "7 games and about 431 hours" — was about to become the
sixth. Every number in the new one is summed from the weights at build time,
so an added row moves the sentence with it. The row count is left to the card,
which generates one; what the blurb states is the mainline count, which is a
different and explicitly labelled number.

**Live and dead spin-offs are treated differently.** *Persona 5: The Phantom
X* is a free-to-play mobile game still adding story, and it ships, marked
optional, with its note saying so — HowLongToBeat times it and it can be
played today. The Japan-only mobile and browser games Wikipedia describes in
prose but leaves off its timeline — *The Night Before*, *Ain Soph*, *Persona
Mobile Online*, the *Persona 3* phone side-stories, *Persona 4 The Card
Battle* — are cut: their servers are off and there is nothing left to play,
which is the rule properties/fps-canon.json uses for dead live-service
shooters and the one gears-of-war.json uses to cut Gears Pop!.

**Dated unreleased work is a row at zero; undated work is not.** The owner's
rule, the one silent-hill.json and gears-of-war.json already follow: a game
announced with a release date, even a bare year, gets a row with an explicit
`w: 0` and a note saying when it is due; one without a date stays off.
Persona 4 Revival is the first kind — the timeline slots it at 2027 and its
own infobox dates it 18 February 2027, Switch 2 on 20 May — so it ships as an
optional row beside Reload, the other remake. Persona 6 is the second: the
timeline puts it under TBA and its article gives no date, and this file
asserts both. Both have HowLongToBeat records with no main-story figure, and
this file asserts that stays true: the day the site times either, this build
fails and someone gives Revival its real weight or Persona 6 its row, rather
than the list quietly staying wrong.

Tiers
-----
  1  the modern trilogy — 3, 4, 5, what everyone means by "Persona"
  2  the PS1 classics — the original and the Persona 2 duology
  3  everything optional — the editions, the two remakes, the spin-offs

Three is the ceiling, not a choice: the page's stats bar is built for tiers 1
to 3 (`TIERTOT = {1:0,2:0,3:0}` in src/template.html) and a fourth would count
into an undefined slot.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop as P  # noqa: E402

SLUG = "persona"
DATA = P.ROOT / "tools" / "data" / "persona.json"

# How far an expanded edition's main-story figure may sit from its original's
# before "it is the same game with more in it" stops being a claim the data
# supports and starts being a second sitting. The number halo.json and
# gears-of-war.json fold their remasters on.
EDITION_SLACK_H = 3.0

# Ids that were live before this expansion. Renaming one orphans every tick
# recorded against it, so P.write refuses to emit a file that has lost any.
LEGACY_IDS = ("per-1", "per-2is", "per-2ep", "per-3", "per-4", "per-5",
              "per-3r")

# key, id, HowLongToBeat name, display title, display year, section, tier,
# opt, note
ROSTER = [
    # ------------------------------------------------------------- mainline
    ("p1", "per-1", "Revelations: Persona", "Revelations: Persona", 1996,
     "ps1", 2, 0,
     "The PS1 original. The 2009 PSP remake is the usual way to play it "
     "now — either edition ticks this row."),
    ("p2is", "per-2is", "Persona 2: Innocent Sin", "Persona 2: Innocent Sin",
     1999, "ps1", 2, 0,
     "First half of the duology — Japan-only until the 2011 PSP release"),
    ("p2ep", "per-2ep", "Persona 2: Eternal Punishment",
     "Persona 2: Eternal Punishment", 2000, "ps1", 2, 0,
     "The direct conclusion — the duology is one story in two games"),
    ("p3", "per-3", "Shin Megami Tensei: Persona 3", "Persona 3", 2006,
     "calendar", 1, 0, None),                       # note computed below
    ("p4", "per-4", "Shin Megami Tensei: Persona 4", "Persona 4", 2008,
     "calendar", 1, 0,
     "A year in Inaba, a rural town, where a group of students investigate a "
     "run of killings tied to a realm behind the television called the "
     "Midnight Channel. Golden, the expanded version and the usual pick, has "
     "its own row below."),
    ("p5", "per-5", "Persona 5", "Persona 5", 2016, "phantom", 1, 0,
     "The biggest one — Tokyo, and a group of students who put on thieves' "
     "disguises to steal the city's corruption out from under it. Royal, the "
     "expanded version, has its own row below."),
    ("p3r", "per-3r", "Persona 3 Reload", "Persona 3 Reload", 2024,
     "phantom", 3, 1,
     "The ground-up remake of Persona 3 — same story, modern build. Play "
     "this or the original, not both."),
    # ------------------------------------------------------------- editions
    ("p3p", "per-3p", "Shin Megami Tensei: Persona 3 Portable",
     "Persona 3 Portable", 2009, "editions", 3, 1, None),
    ("p4g", "per-4g", "Persona 4 Golden", "Persona 4 Golden", 2012,
     "editions", 3, 1,
     "The Vita version, and the one most people mean by Persona 4: two new "
     "social links, a new character in Marie, extra Personas and more voiced "
     "scenes. Play this or the PS2 original, not both."),
    ("p5r", "per-5r", "Persona 5 Royal", "Persona 5 Royal", 2019,
     "editions", 3, 1,
     "The rework: a new Palace, a new party member, a new district of Tokyo "
     "and a playable third semester on top of everything the 2016 game had. "
     "The longest thing on this list. Play this or the original, not both."),
    # ------------------------------------------------------------ spin-offs
    ("p4a", "per-4a", "Persona 4 Arena", "Persona 4 Arena", 2012,
     "spinoffs", 3, 1,
     "A fighting game co-developed with Arc System Works, and a real sequel: "
     "a visual-novel story mode set two months after the Inaba murders close"),
    ("p4au", "per-4au", "Persona 4 Arena Ultimax", "Persona 4 Arena Ultimax",
     2013, "spinoffs", 3, 1,
     "The follow-up: Japanese arcades in 2013, consoles worldwide in 2014, "
     "which is the release HowLongToBeat times. Eight more fighters, and a "
     "story mode split into one campaign per game's cast."),
    ("pq", "per-q", "Persona Q: Shadow of the Labyrinth",
     "Persona Q: Shadow of the Labyrinth", 2014, "spinoffs", 3, 1, None),
    ("p4d", "per-4d", "Persona 4: Dancing All Night",
     "Persona 4: Dancing All Night", 2015, "spinoffs", 3, 1,
     "The rhythm game, set after Arena Ultimax, and the one of the three "
     "built around a full story mode — the 2018 pair dropped it for "
     "character interactions instead"),
    ("p3d", "per-3d", "Persona 3: Dancing in Moonlight",
     "Persona 3: Dancing in Moonlight", 2018, "spinoffs", 3, 1,
     "One half of a pair released together on purpose — the Persona 3 "
     "soundtrack, original and remixed, with S.E.E.S. dancing to it"),
    ("p5d", "per-5d", "Persona 5: Dancing in Starlight",
     "Persona 5: Dancing in Starlight", 2018, "spinoffs", 3, 1,
     "The other half, released the same day, Phantom Thieves instead of "
     "S.E.E.S."),
    ("pq2", "per-q2", "Persona Q2: New Cinema Labyrinth",
     "Persona Q2: New Cinema Labyrinth", 2018, "spinoffs", 3, 1,
     "The crawler sequel, adding the Persona 5 cast to the crossover. "
     "Japan in 2018, worldwide the year after."),
    ("p5s", "per-5s", "Persona 5 Strikers", "Persona 5 Strikers", 2020,
     "spinoffs", 3, 1,
     "A Dynasty Warriors-style action sequel: four months after Persona 5, "
     "the Phantom Thieves reunite for a summer camping trip. The closest "
     "thing the series has to a numbered follow-up."),
    ("p5t", "per-5t", "Persona 5 Tactica", "Persona 5 Tactica", 2023,
     "spinoffs", 3, 1,
     "Turn-based tactics with the Phantom Thieves — a different genre "
     "wearing the same cast"),
    ("p5x", "per-5x", "Persona 5: The Phantom X", "Persona 5: The Phantom X",
     2025, "spinoffs", 3, 1,
     "A free-to-play mobile spin-off with its own cast and its own Tokyo, "
     "built by Black Wings Game Studio rather than Atlus. Personas are "
     "pulled from a gacha, so the figure beside it is what HowLongToBeat "
     "times today rather than a fixed length."),
    # ---------------------------------------------------------- not out yet
    ("p4rev", "per-4rev", "Persona 4 Revival", "Persona 4 Revival", 2027,
     "phantom", 3, 1,
     "The remake of Persona 4 Golden — the same story, rebuilt to the "
     "standard of Royal and Reload."),
]

# Dated but not out. Each row weighs an explicit 0 and its note opens with
# NOT_OUT, filled from here: (first release date, later platform's date).
# Both dates are Persona 4 Revival's own infobox; main() asserts the year
# against the data's Wikipedia year and that HowLongToBeat has no figure yet.
UNRELEASED = {"p4rev": ("18 February 2027", "20 May 2027 on Switch 2")}

# Prefixed to an unreleased row's note — the wording silent-hill.json and
# gears-of-war.json use for theirs.
NOT_OUT = ("Not out yet — due %s (%s), and the bar stays empty until "
           "HowLongToBeat has hours for it.")

# Collected by the fetcher, asserted against, never shipped as a row.
ASSERT_ONLY = ("p3fes", "p3answer", "p3r_aigis", "p6")

SECTIONS = [
    ("ps1", "The PS1 years",
     "Before the social links — the original and the two-part sequel, "
     "darker and stranger than what followed."),
    ("calendar", "The calendar reinvention",
     "A school year, a dungeon, and a deadline — the structure the series "
     "is famous for arrives."),
    ("phantom", "Phantom Thieves and after",
     "The biggest one, the remake that brought Persona 3 up to its "
     "standard, and the one doing the same for Persona 4."),
    ("editions", "The expanded editions",
     "Not sequels — the same games with more in them. FES folds into "
     "Persona 3 because HowLongToBeat times the two within hours of each "
     "other; these three miss that mark by too far to call them the same "
     "sitting, so they are rows."),
    ("spinoffs", "The spin-offs",
     "Fighting games, dungeon crawlers, rhythm games, a Warriors game, a "
     "tactics game and a phone game. All optional, and every one of them "
     "assumes you have finished the game it spins off."),
]


_WORDS = ("zero one two three four five six seven eight nine ten eleven "
          "twelve thirteen fourteen fifteen sixteen seventeen eighteen "
          "nineteen twenty").split()


_TENS = "twenty thirty forty fifty sixty seventy eighty ninety".split()


def spell(n):
    """A generated count that still reads like prose. "The mainline is 6
    games" is what a template writes; "six" is what a person writes, and the
    number stays computed either way."""
    if n < len(_WORDS):
        return _WORDS[n]
    if n < 100:
        tens = _TENS[n // 10 - 2]
        return tens if n % 10 == 0 else "%s-%s" % (tens, _WORDS[n % 10])
    return str(n)


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))

    # --- the roster, verified row by row ------------------------------------
    entries = []
    for key, iid, hname, title, year, sec, tier, opt, note in ROSTER:
        rec = data.get(key)
        assert rec, "no HowLongToBeat record for %s — re-run fetch_hltb.py" % key
        # Name, stated here independently of the fetcher's query list.
        assert P.normt(rec["name"] or "") == P.normt(hname), \
            "record mismatch for %s: asked %r, got %r" % (key, hname, rec["name"])
        # Year, exact and three ways: what the site says, what the gate was
        # held to, and what this roster claims. No window anywhere.
        assert rec["year"] == rec["hltb_year"], \
            "%s: the gate ran against %s but the record says %s" \
            % (key, rec["hltb_year"], rec["year"])
        assert rec["wiki_year"] == year, \
            "%s: Wikipedia's release year is %s, this roster says %d" \
            % (key, rec["wiki_year"], year)
        # The one row whose site year is not its first-release year is allowed
        # to differ only because Wikipedia lists that year for it too.
        assert rec["hltb_year"] in rec["wiki_years"], \
            ("%s: gated on %s, which is not a year Wikipedia lists for it "
             "(%s)" % (key, rec["hltb_year"], rec["wiki_years"]))
        # Mainline versus optional, taken from the timeline's own bolding
        # rather than from whoever edited this list last.
        assert rec["main_series"] == (not opt), \
            ("%s: Wikipedia's timeline %s it as main series, this roster "
             "marks it %s" % (key, "bolds" if rec["main_series"] else
                              "does not bold",
                              "optional" if opt else "mainline"))
        if key in UNRELEASED:
            # Dated but not out: an explicit zero, and only while the site
            # has nothing to say. The day it times the game, this fails and
            # the row gets its real weight and loses its "not out yet".
            assert not rec["main_h"], \
                ("HowLongToBeat now times %s (%s h) — it is out; give the "
                 "row its real weight and take it out of UNRELEASED"
                 % (title, rec["main_h"]))
            due = UNRELEASED[key]
            assert due[0].endswith(str(rec["wiki_year"])), \
                ("%s: due %s, but Wikipedia's release year is %s"
                 % (key, due[0], rec["wiki_year"]))
            assert rec["slot"] == str(rec["wiki_year"]), \
                ("%s: the timeline slots it at %s, not under its year %s"
                 % (key, rec["slot"], rec["wiki_year"]))
            w, note = 0, NOT_OUT % due + " " + note
        else:
            # All-or-nothing: the page reads a missing w as one hour, so a
            # row without a real figure must break the build, never ship.
            assert (isinstance(rec["main_h"], (int, float))
                    and rec["main_h"] > 0), \
                ("no main-story figure for %s (%s) — this list is weighted "
                 "and a row without one would silently count as an hour"
                 % (key, rec["why"]))
            w = rec["main_h"]
        assert tier in (1, 2, 3), \
            "%s: the stats bar only counts tiers 1-3, not %r" % (key, tier)
        entries.append({"id": iid, "t": title, "n": str(year),
                        "w": w, "note": note, "sec": sec,
                        "tier": tier, "opt": opt, "key": key,
                        "slot": rec["slot"]})

    used = {e["key"] for e in entries} | set(ASSERT_ONLY)
    assert used == set(data), \
        "tools/data/persona.json and this roster disagree: %r" \
        % sorted(used ^ set(data))
    slots = [e["slot"] for e in entries]
    assert len(slots) == len(set(slots)), "two rows share a timeline slot"

    by_key = {e["key"]: e for e in entries}

    # --- the calls this file makes, asserted against the data ---------------
    # Fold or split, tested the same way in both directions. An edition that
    # times within EDITION_SLACK_H of its original is the same sitting and
    # belongs in a note; one that does not is a row. Exactly one of the four
    # passes, and if that ever changes this build says so rather than leaving
    # a note or a row standing on a claim the numbers stopped supporting.
    FOLDED = {"p3fes": "p3"}
    SPLIT = {"p3p": "p3", "p4g": "p4", "p5r": "p5"}
    gaps = {}
    for edition, base in list(FOLDED.items()) + list(SPLIT.items()):
        rec, orig = data[edition], data[base]
        assert rec["main_h"], "no figure for the %s edition" % edition
        gaps[edition] = abs(rec["main_h"] - orig["main_h"])
    for edition, base in FOLDED.items():
        assert gaps[edition] <= EDITION_SLACK_H, \
            ("%s times %s h against %s's %s h — that is no longer 'the same "
             "game with more in it', so folding it into a note is a claim "
             "the data stopped supporting and it needs its own row"
             % (edition, data[edition]["main_h"], base, data[base]["main_h"]))
    for edition, base in SPLIT.items():
        assert gaps[edition] > EDITION_SLACK_H, \
            ("%s now times within %.2f h of %s — the reason it has its own "
             "row instead of a note has gone, and it should be folded"
             % (edition, gaps[edition], base))
    # Which side of its original each split edition falls on. Two notes say
    # so out loud — "Royal comes in over the game it expands and Golden and
    # Portable come in under theirs" — and a direction is exactly the sort of
    # claim that quietly stops being true.
    assert data["p5r"]["main_h"] > data["p5"]["main_h"], \
        "Royal no longer times longer than Persona 5"
    for edition, base in (("p4g", "p4"), ("p3p", "p3")):
        assert data[edition]["main_h"] < data[base]["main_h"], \
            "%s no longer times shorter than %s" % (edition, base)

    # Why FES times like the base game: HowLongToBeat files The Answer, the
    # epilogue FES added, as its own record — twice over, once for FES and
    # once for Reload's DLC. The Persona 3 note says so, so both must exist.
    for key in ("p3answer", "p3r_aigis"):
        assert data[key]["main_h"], \
            ("%s carries no figure — the Persona 3 note claims HowLongToBeat "
             "tracks The Answer separately, and that claim needs the record"
             % key)

    # Persona 6: announced, undated, so not a row. The day Wikipedia dates
    # it or HowLongToBeat times it, this fails and it gets one.
    assert not data["p6"]["main_h"], \
        ("HowLongToBeat now times Persona 6 (%s h) — it has shipped, and it "
         "belongs on this list" % data["p6"]["main_h"])
    assert data["p6"]["wiki_year"] is None and \
        data["p6"]["slot"].startswith("TBA"), \
        ("Wikipedia now dates Persona 6 (%s, slot %s) — a dated game gets a "
         "w: 0 row; add it to ROSTER and UNRELEASED"
         % (data["p6"]["wiki_year"], data["p6"]["slot"]))

    # --- the notes that carry numbers, generated so they cannot rot ---------
    by_key["p3"]["note"] = (
        "The calendar reinvention. FES (2007) is its director's cut and ticks "
        "this row — HowLongToBeat times the two within %d hours of each "
        "other, because it files The Answer, the epilogue FES added, as a "
        "separate %d-hour game. Portable and Reload have rows of their own."
        % (max(1, round(gaps["p3fes"])), round(data["p3answer"]["main_h"])))
    by_key["p3p"]["note"] = (
        "The PSP version of FES's main story: a female protagonist to play "
        "as instead, the whole party under your control in battle, and "
        "content adjusted or cut to fit a handheld. HowLongToBeat times it "
        "%d hours under the PS2 original, which is a different sitting, not "
        "a different edition." % round(gaps["p3p"]))
    by_key["pq"]["note"] = (
        "A 3DS dungeon crawler dropping the Persona 3 and 4 casts into one "
        "labyrinth. Atlus counts it inside the canon, and at %d hours it runs "
        "longer than any of the PS1 games."
        % round(data["pq"]["main_h"]))
    assert all(e["note"] for e in entries), \
        "a row reached the emitter without a note"

    # --- sections -----------------------------------------------------------
    sections = []
    for sec_id, sec_title, intro in SECTIONS:
        got = [e for e in entries if e["sec"] == sec_id]
        assert got, "empty section %s" % sec_id
        assert [e["slot"] for e in got] == sorted(e["slot"] for e in got), \
            ("%s is out of the release order Wikipedia's timeline gives"
             % sec_id)
        years = [int(e["n"]) for e in got]
        hours = sum(e["w"] for e in got)
        sub = ("%d–%d · %d games · %d hours story"
               % (years[0], years[-1], len(got), round(hours)))
        pending = [e for e in got if e["key"] in UNRELEASED]
        if pending:
            sub += " · %d not out yet" % len(pending)
        sections.append({
            "id": sec_id, "title": sec_title,
            "sub": sub,
            "intro": intro,
            "items": [{k: v for k, v in e.items()
                       if k in ("id", "t", "n", "w", "tier", "note")}
                      | ({"opt": 1} if e["opt"] else {})
                      for e in got],
        })
    sections[0]["open"] = True

    every = [x for s in sections for x in s["items"]]
    assert len(every) == len(ROSTER), (len(every), len(ROSTER))
    assert all("w" in x for x in every), \
        "a row reached the emitter without a weight"
    # The only zeros are the rows this file declares unreleased.
    assert {x["id"] for x in every if x["w"] <= 0} == \
        {e["id"] for e in entries if e["key"] in UNRELEASED}, \
        "a released row reached the emitter without a real weight"

    # --- the numbers the blurb and the notes stand on -----------------------
    mainline = [e for e in entries if not e["opt"]]
    optional = [e for e in entries if e["opt"]]
    tiers = {t: [e for e in entries if e["tier"] == t] for t in (1, 2, 3)}
    assert len(tiers[1]) == 3, "the modern trilogy should be 3 rows"
    assert len(tiers[2]) == 3, "the PS1 classics should be 3 rows"
    assert not any(e["opt"] for e in tiers[1] + tiers[2]), \
        "a paced tier holds an optional row — it would count toward the "\
        "finish date the checkbox is supposed to add"
    assert all(e["opt"] for e in tiers[3]), \
        "tier 3 holds a row that is not optional"
    assert len(mainline) == 6 and {e["key"] for e in mainline} == \
        {k for k, v in data.items() if v["main_series"] and v["main_h"]}, \
        "the mainline is no longer exactly the released games Wikipedia bolds"

    hours = sum(e["w"] for e in entries)
    main_h = sum(e["w"] for e in mainline)
    rest_h = sum(e["w"] for e in optional)
    trilogy_avg = sum(e["w"] for e in tiers[1]) / len(tiers[1])
    longest = max(entries, key=lambda e: e["w"])
    assert longest["key"] == "p5r", \
        "the Royal note claims it is the longest thing on this list; %r is" \
        % longest["t"]
    assert data["pq"]["main_h"] > max(e["w"] for e in tiers[2]), \
        "the Persona Q note claims it runs longer than any of the PS1 games"
    assert min(e["w"] for e in tiers[1]) >= 60, \
        "the blurb frames the modern trilogy as 60-plus hours each"

    prop = {
        "slug": SLUG,
        "title": "Persona",
        "subtitle": "the whole series in release order, spin-offs marked",
        "kind": "games",
        "popularity": 66,
        "year": "1996–",
        # Every number here is summed from the weights above. Five lists in
        # this catalogue shipped a blurb contradicting the card printed above
        # it (CLU-190); the row count is left to the card, which generates
        # one, and what this states is the mainline count, which is a
        # different and labelled number.
        "blurb": "%s mainline RPGs, about %d hours of story — the modern "
                 "trilogy alone averages %d hours each, and that is not a "
                 "typo. The editions, the remakes and the spin-offs add %d "
                 "more."
                 % (spell(len(mainline)).capitalize(), round(main_h),
                    round(trilogy_avg), round(rest_h)),
        "unit": {"one": "game", "many": "games"},
        "verb": {"base": "play", "past": "played", "ing": "playing"},
        "itemOrder": "number-first",
        "accent": "#2D3C93",
        "accentDark": "#EF4B5E",
        "tiers": True,
        "itemTiers": True,
        "paceTiers": [1, 2],
        "paceLabel": "the editions, the remakes and the spin-offs",
        "notes": [
            ["The mainline is %s games." % spell(len(mainline)),
             "Revelations, the Persona 2 duology, and 3, 4 and 5 — the "
             "entries Wikipedia's own release timeline sets in bold. They are "
             "the only rows here that are not optional, because someone who "
             "has played those %s has played Persona in the sense that "
             "matters. Everything else is marked optional and stays out of "
             "the finish date unless you tick the box that widens it, so a "
             "page that grew to %s rows did not quietly rewrite what "
             "finishing this list means."
             % (spell(len(mainline)), spell(len(entries)))],
            ["Editions are notes where the data says fold, rows where it "
             "says split.",
             "FES, Portable, Golden and Royal are not sequels — they are the "
             "same game with more in it, and the question each time is "
             "whether it is really a second sitting. The test is the one the "
             "Halo and Gears lists fold their remasters on: does "
             "HowLongToBeat time it within %d hours of the original? FES "
             "does, because the site files The Answer, the epilogue FES "
             "added, as a separate game — so FES ticks the Persona 3 row and "
             "is named in its note. The other three miss, Portable by %d "
             "hours, Golden by %d and Royal by %d the other way, so each is "
             "its own optional row. None of them asks you to play both: the "
             "notes say which to pick."
             % (EDITION_SLACK_H, round(gaps["p3p"]), round(gaps["p4g"]),
                round(gaps["p5r"]))],
            ["Every spin-off is optional.",
             "The two fighting games, the two Persona Q crawlers, the three "
             "rhythm games, Strikers, Tactica and the mobile Phantom X are "
             "real games, and several are canon — Atlus counts Persona Q "
             "inside it. They are optional to a one, and every one of them "
             "assumes you have played the game it spins off. Persona Q is a "
             "%d-hour dungeon crawler and Q2 another %d, which is exactly "
             "why they are not folded into the mainline total."
             % (round(data["pq"]["main_h"]), round(data["pq2"]["main_h"]))],
            ["What is not here.",
             "Wikipedia's release timeline is the roster, and everything on "
             "it that has shipped is on this page. The Japan-only mobile and "
             "browser games it describes in prose but leaves off the timeline "
             "are not: Persona 3: The Night Before, Persona Ain Soph, Persona "
             "Mobile Online, the Persona 3 phone side-stories and Persona 4 "
             "The Card Battle all closed years ago, and there is nothing left "
             "to play. Persona 4 Revival, due %s, has a row at zero hours: "
             "HowLongToBeat has a record for it and no figure yet, and this "
             "list refuses to guess one. Persona 6 is announced without a "
             "date, and goes on the day it has one."
             % UNRELEASED["p4rev"][0]],
            ["Hours are story only.",
             "HowLongToBeat main-story figures — no side content, no maxed "
             "social links, no New Game Plus. They are what people report, "
             "not what a box claims, which is why Royal comes in over the "
             "game it expands and Golden and Portable come in under theirs. "
             "Every released row carries a real one, and Persona 4 Revival "
             "carries zero until it is out; nothing here was estimated, and "
             "a row whose figure fails the name-and-year check fails this "
             "build instead of shipping unweighted."],
            "Game list, release order, years and the mainline split from "
            "Wikipedia's Persona (franchise) article and each game's own "
            "article; hours from HowLongToBeat main-story figures, verified "
            "by name and exact release year.",
        ],
        "sections": sections,
    }

    P.write(prop, legacy_ids=LEGACY_IDS)

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d games, %d hours (%d mainline, %d optional)"
          % (len(sections), len(every), round(hours), round(main_h),
             round(rest_h)))
    for s in sections:
        print("   %-24s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))
    print("  edition gaps against the %.1f h fold test:" % EDITION_SLACK_H)
    for k in ("p3fes", "p3p", "p4g", "p5r"):
        print("   %-6s %-46s %6.2f h  vs base  %6.2f h   gap %5.2f  %s"
              % (k, data[k]["name"], data[k]["main_h"],
                 data[{"p3fes": "p3", "p3p": "p3", "p4g": "p4",
                       "p5r": "p5"}[k]]["main_h"], gaps[k],
                 "fold" if gaps[k] <= EDITION_SLACK_H else "split"))
    for e in entries:
        print("   %-38s %s  w=%-7s%s"
              % (e["t"], e["n"], e["w"], "  (optional)" if e["opt"] else ""))


if __name__ == "__main__":
    main()
