#!/usr/bin/env python3
"""Generate properties/silent-hill.json.

    python3 tools/make_silent-hill.py

Silent Hill in release order: the four Team Silent games, the wandering years
after them, and the revival that starts in 2023.

WHY THIS LIST STOPPED SAYING "MAINLINE ONLY"
--------------------------------------------
It shipped with a scope note reading "Mainline only", which excluded
*Silent Hill f* on the grounds that Wikipedia's Silent Hill article files it
under `=== Spin-offs ===`. The list did not follow its own rule: the same
`=== Spin-offs ===` heading also holds *The Short Message*, which was already
a row. One game admitted and another refused from the same section of the same
article is not a rule, it is a coin toss, and the note described a list that
did not exist.

The article argues with itself about *f* in four places, all of them read by
scratch/agent-sh/read_source.py:

  * structurally it is `==== ''Silent Hill f'' (2025) ====` inside Spin-offs;
  * the prose opens "A spin-off entitled ''Silent Hill f'' was announced in
    October 2022", cited to producer Motoi Okamoto, and f's own article's lead
    calls it "a standalone spin-off of the ''Silent Hill'' franchise";
  * the franchise infobox names it `latest release version` with
    `latest release date = 2025-09-25` — the newest thing the series has;
  * and the citation immediately after that prose is Polygon's, headlined
    "Silent Hill f, Konami's first main-series game in a decade, brings the
    franchise to Japan".

A source that cannot decide cannot sort this list, so the list sorts itself:
the test is whether a thing is a Silent Hill you sit down and play — a
standalone release with its own story — whatever heading it sits under. That
admits the arcade cabinet's neighbours (The Short Message, f, Townfall) and
refuses the arcade cabinet, the four mobile games, the Play Novel visual
novel, Book of Memories, P.T. and the two compilations. main() asserts the
Spin-offs section still holds all three of the entries this rule takes from
it, so a reorganised article sends the scope note back for review.

THE ONE DELIBERATE EXCEPTION: ASCENSION
---------------------------------------
*Silent Hill: Ascension* is on the list on the owner's instruction and does
not pass the rule above. Wikipedia does not file it with the games at all —
it is `=== Television ===` under Other media, "a CGI interactive television
series" broadcast nightly from October 31, 2023 to April 24, 2024, whose
audience voted on the story. Its row says so in as many words, and main()
asserts the article still files it under Television so the exception cannot
quietly become untrue. It is weighted because HowLongToBeat does carry a
main-story figure for it.

UNRELEASED WORK IS LISTED WHEN THE SOURCE DATES IT, AND WEIGHS ZERO
-------------------------------------------------------------------
The owner's rule: announced with a release date — even a bare year — is
enough to earn a row; undated work is not. So:

  * *Silent Hill: Townfall* went in that way (dated September 24, 2026,
    while its article still called it upcoming) and shipped on the day: its
    article's lead now reads "''Townfall'' was released for PlayStation 5
    and Windows on 24 September 2026". It weighs its HowLongToBeat hours
    like every other released row, and main() asserts the lead still says
    so.
  * The remake of the first game is NOT a row. It is announced (June 2025,
    Bloober Team) with no date anywhere: the release timeline slots it under
    `TBA`, its heading reads `''Silent Hill'' (TBA)`, its paragraph gives no
    date, and it has no article of its own. main() asserts all three, so the
    day Wikipedia dates it the build fails and it comes back for review.

An unreleased row carries an explicit `w: 0`, never a missing `w`. The page
resolves `WEIGHT = x.w >= 0 ? x.w : 1`, so a row without one on a weighted
list silently books itself as one hour (CLU-131) — an invented hour for a
game nobody can have played. Zero is the honest figure and it keeps every other
row's verified HowLongToBeat hours intact.

The release date is asserted every run, against the clock:

  * while it is in the future, the row weighs 0, its note says when the game
    is due, and the source is asserted to still call it upcoming — if the
    article starts describing it as released, the build fails;
  * the day it passes, the build fails unless tools/data/silent-hill.json has
    a name-gated HowLongToBeat record for it. Re-run
    scratch/agent-sh/fetch_hltb.py and the row weights itself. It cannot
    quietly stay at zero, and it cannot quietly become a phantom hour.

SOURCES
-------
Every fact on the card is machine-read. Game list, years and how the article
files each entry: Wikipedia's Silent Hill, Silent Hill f and Silent Hill:
Townfall articles, parsed by scratch/agent-sh/read_source.py into the
"_source" block of tools/data/silent-hill.json. Hours: HowLongToBeat
main-story figures collected by scratch/agent-sh/fetch_hltb.py through
gwlib.hltb.story_hours(), which refuses a record whose name is not what was
asked for; this generator re-checks each record's name and year before
believing it (the 2024 remake shares the 2001 game's name on HowLongToBeat
and is told apart by year).

TIERS: 1 is the essential path — Silent Hill 1 through 4, the 2024 remake and
Silent Hill f, which is a full-size current entry rather than a side trip
however the article files it. 2 is everything else.
"""
import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop  # noqa: E402

SLUG = "silent-hill"

# Every id currently shipped. Progress is stored as a list of these, so a
# renamed one destroys everyone's ticks silently; prop.write refuses to write
# a file that has lost any of them.
LEGACY_IDS = [
    "sh-sh1", "sh-sh2", "sh-sh3", "sh-sh4",
    "sh-origins", "sh-homecoming", "sh-shattered", "sh-downpour",
    "sh-short-message", "sh-sh2-remake",
]

# key in the data file, display title, Wikipedia year, tier, note, opt
TEAM_SILENT = [
    ("sh1", "Silent Hill", 1999, 1,
     "PS1. Harry Mason, the fog, the school — where the town starts.", 0),
    ("sh2", "Silent Hill 2", 2001, 1,
     "James Sunderland and the letter. The series' peak, and its own "
     "story — the 2024 row rebuilds it.", 0),
    ("sh3", "Silent Hill 3", 2003, 1,
     "Heather's story — the one direct sequel, continuing the first "
     "game", 0),
    ("sh4", "Silent Hill 4: The Room", 2004, 1,
     "Room 302 and the hole in the bathroom wall; Team Silent's last", 0),
]

AFTER = [
    ("origins", "Silent Hill: Origins", 2007, 2,
     "PSP prequel to the first game", 0),
    ("homecoming", "Silent Hill: Homecoming", 2008, 2,
     "The first western-built entry", 0),
    ("shattered", "Silent Hill: Shattered Memories", 2009, 2,
     "A reimagining of the first game — the therapy-session one, and the "
     "best of this stretch", 0),
    ("downpour", "Silent Hill: Downpour", 2012, 2,
     "Murphy Pendleton, rain, and the last of the old line", 0),
]

REVIVAL = [
    ("ascension", "Silent Hill: Ascension", 2023, 2,
     "Not a game — a CGI series broadcast nightly from October 2023 to "
     "April 2024, with the audience voting on where the story went. "
     "Wikipedia files it under television; it is here because it is part "
     "of the revival.", 1),
    ("short-message", "Silent Hill: The Short Message", 2024, 2,
     "Free on PS5 — a short standalone story, and the series waking back "
     "up", 1),
    ("sh2-remake", "Silent Hill 2 (2024)", 2024, 1,
     "Bloober Team's remake — the modern door into the story; ticking "
     "either version counts", 0),
    ("f", "Silent Hill f", 2025, 1,
     "1960s rural Japan rather than the town — the first all-new full-size "
     "entry since Downpour, and its own story. Wikipedia files it as a "
     "spin-off; it plays like the main event.", 0),
    ("townfall", "Silent Hill: Townfall", 2026, 2,
     "First-person, and set in 1996 in the Scottish town of St. Amelia.", 0),
]

# Prefixed to an unreleased row's own note, so the row still says what it is
# the day it ships and the note needs no second edit.
NOT_OUT = ("Not out yet — due %s, and the bar stays empty until "
           "HowLongToBeat has hours for it.")

# Rows with no HowLongToBeat figure because the game is not out. Each must
# carry an explicit w of 0 and say so in its note; main() asserts both, and
# asserts the release date the source gives against today's clock. Empty
# since Townfall shipped on 24 September 2026.
UNRELEASED = set()

# expected HLTB names where they differ from the display title
EXPECT = {"sh2-remake": ["Silent Hill 2", "Silent Hill 2 Remake",
                         "Silent Hill 2 (2024)"]}

SECTIONS = [
    ("team-silent", "Team Silent",
     "Four games in six years from the studio the series is measured "
     "against.", TEAM_SILENT),
    ("after", "After Team Silent",
     "Outside studios carry the town, 2007–2012 — worthwhile side trips, "
     "none required.", AFTER),
    ("revival", "The revival",
     "Konami restarts the series from 2023: an interactive series, a free "
     "short story, a remake, and the first all-new games in over a decade.",
     REVIVAL),
]


def norm(s):
    s = (s or "").replace("’", "'").replace("–", "-")
    return " ".join(s.casefold().split())


def _today():
    """The clock, isolated so a check can stub it (scratch/agent-sh/)."""
    return datetime.date.today()


def longdate(d):
    return "%d %s %d" % (d.day, d.strftime("%B"), d.year)


def main():
    data = json.loads((pathlib.Path(__file__).resolve().parent / "data"
                       / ("%s.json" % SLUG)).read_text(encoding="utf-8"))
    src = data["_source"]
    today = _today()

    # ---- the diagnosis this list was repaired for -------------------------
    # All three of these sit under the article's ===Spin-offs=== heading, and
    # all three are rows. The moment that stops being true the scope note is
    # describing a different article and must be rewritten.
    spin = " · ".join(src["spinoff_sections"])
    for name in ("Silent Hill: The Short Message", "Silent Hill f",
                 "Silent Hill: Townfall"):
        assert any(s.startswith(name) for s in src["spinoff_sections"]), \
            ("%s is no longer filed under Spin-offs — the scope note argues "
             "with that heading and needs rechecking (found: %s)"
             % (name, spin))

    # ---- Silent Hill f: out, and dated by its own article -----------------
    f_out = datetime.date.fromisoformat(src["f"]["released"])
    assert f_out.year == 2025 and f_out <= today, \
        "Silent Hill f's release date moved: %s" % f_out
    assert src["f"]["short_description"] == "2025 video game", \
        src["f"]["short_description"]

    # ---- Townfall: dated, not out, weighs nothing until it is -------------
    due = datetime.date.fromisoformat(src["townfall"]["released"])
    townfall_out = due <= today
    if not townfall_out:
        assert src["townfall"]["short_description"].startswith("Upcoming") \
            and src["townfall"]["lead_upcoming"], \
            ("Wikipedia no longer describes Townfall as upcoming (%r) while "
             "its stated release date %s is still in the future — re-read the "
             "article: it may have shipped early"
             % (src["townfall"]["short_description"], due))
        assert "townfall" not in data, \
            ("Townfall now has a HowLongToBeat record (%r) — HowLongToBeat "
             "only carries a main-story figure for a game people have "
             "finished, so it has landed ahead of its stated %s date. Give "
             "the row its hours." % (data.get("townfall"), due))
    else:
        assert src["townfall"].get("lead_released"), \
            ("Townfall's stated release date (%s) has passed but its article "
             "no longer says it was released on that date — re-read it" % due)
        assert data.get("townfall", {}).get("main_h"), \
            ("Townfall's release date (%s) has passed and there is still no "
             "HowLongToBeat record for it. Run "
             "scratch/agent-sh/fetch_hltb.py — a released row must not stay "
             "at w 0, and it must not lose its w either (a missing w books "
             "itself as one hour)." % due)

    # ---- the remake of the first game: announced, undated, not a row ------
    r = src["sh1_remake"]
    assert r["timeline_slot"] == "TBA" and r["heading_date"] == "TBA" \
        and r["prose_date"] is None, \
        ("Wikipedia now dates the remake of the first game (%r) — dated work "
         "earns a row on this list. Add it, at w 0 until HowLongToBeat has "
         "hours for it." % r)

    # ---- Ascension is the deliberate exception, and stays labelled --------
    assert src["ascension"]["filed_under"] == "Television", \
        "Ascension is no longer filed under Television — recheck its row note"
    assert src["ascension"]["first"] == "2023-10-31" \
        and src["ascension"]["last"] == "2024-04-24", src["ascension"]

    sections = []
    for sec_id, sec_title, intro, roster in SECTIONS:
        years = [y for _, _, y, _, _, _ in roster]
        assert years == sorted(years), "%s roster out of release order" % sec_id
        items = []
        for key, title, year, tier, note, opt in roster:
            if key in UNRELEASED and key not in data:
                w = 0
                note = " ".join([NOT_OUT % longdate(due), note]).strip()
            else:
                rec = data.get(key)
                assert rec, "no HLTB record for %s" % key
                want = {norm(n) for n in EXPECT.get(key, [title])}
                assert norm(rec["name"]) in want, \
                    "record mismatch for %s: %r" % (key, rec["name"])
                assert abs(int(rec["year"]) - year) <= 1, \
                    "year mismatch for %s: wiki %d, hltb %s" % (key, year,
                                                                rec["year"])
                w = rec["main_h"]
                assert w > 0, "%s has a zero HLTB figure" % key
            x = {"id": "sh-%s" % key, "t": title, "n": str(year),
                 "w": w, "tier": tier}
            if note:
                x["note"] = note
            if opt:
                x["opt"] = 1
            items.append(x)
        hours = sum(x["w"] for x in items)
        span = ("%d" % years[0] if years[0] == years[-1]
                else "%d–%d" % (years[0], years[-1]))
        sub = "%s · %d games · %d hours story" % (span, len(items),
                                                  round(hours))
        pending = [x for x in items if x["w"] == 0]
        if pending:
            sub += " · %d not out yet" % len(pending)
        sections.append({
            "id": sec_id, "title": sec_title, "sub": sub,
            "intro": intro, "items": items,
        })
    sections[0]["open"] = True

    rows = [x for s in sections for x in s["items"]]
    ids = [x["id"] for x in rows]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(TEAM_SILENT) + len(AFTER) + len(REVIVAL) == 13, \
        (len(ids),)
    # Weighting is all or nothing: every row declares a w, and the only zeros
    # are the rows this file knows are unreleased.
    assert all("w" in x for x in rows), "a row without w books itself as 1h"
    zeros = {x["id"] for x in rows if x["w"] == 0}
    assert zeros == {"sh-%s" % k for k in UNRELEASED if k not in data}, zeros
    t1 = [x for x in rows if x["tier"] == 1]
    assert len(t1) == 6, "the essential path is 1-4, the remake and f"

    hours = sum(x["w"] for x in rows)
    spine = sum(x["w"] for x in t1)
    coming = [x["t"] for x in rows if x["w"] == 0]

    blurb = ("%d games — about %d hours of story, %d of it the essential path"
             % (len(ids), round(hours), round(spine)))
    blurb += (", with %s still to come." % coming[0].split(": ")[-1]
              if len(coming) == 1 else ".")

    prop_ = {
        "slug": SLUG,
        "title": "Silent Hill",
        "subtitle": "the games you sit down and play, in release order",
        "kind": "games",
        "popularity": 69,
        "year": "1999–",
        "blurb": blurb,
        "unit": {"one": "game", "many": "games"},
        "verb": {"base": "play", "past": "played", "ing": "playing"},
        "itemOrder": "number-first",
        "accent": "#6B655E",
        "accentDark": "#C97455",
        "tiers": True,
        "itemTiers": True,
        "paceTiers": [1],
        "paceLabel": "the later games and the side entries",
        "notes": [
            ["Tiers.", "1 is the essential path — Silent Hill 1 through 4, "
             "the 2024 remake and Silent Hill f, about %d hours; 2 is the "
             "post-Team Silent years and the side entries. A finish date "
             "covers tier 1 and the checkbox adds the rest." % round(spine)],
            ["Scope.", "The test is whether a thing is a Silent Hill you sit "
             "down and play — a standalone release with its own story — not "
             "which heading Wikipedia files it under. Its spin-offs section "
             "holds The Short Message, Silent Hill f and Townfall next to an "
             "arcade cabinet and four phone games, so that heading sorts "
             "nothing here. Left out on the rule: Silent Hill: The Arcade, "
             "the phone games (Orphan 1–3, The Escape, and the 2006 mobile "
             "Silent Hill), the Play Novel visual novel, Book of Memories (a "
             "co-op dungeon crawler), P.T. (a delisted teaser for a "
             "cancelled game) and the two compilations, which re-release "
             "games already here. Ascension is the one deliberate "
             "exception — it is not a game at all, and its row says so."],
            ["Mostly standalone.", "Only Silent Hill 3 is a direct sequel "
             "(to the first game); everything else is its own story, most "
             "of them in the same town. The Short Message, Silent Hill f and "
             "Townfall leave it for Germany, 1960s Japan and Scotland. "
             "Release order is the natural order all the same."],
            ["Not out yet.", "Bloober Team's remake of the first game is "
             "announced with no date at all, so it is not a row yet."],
            ["Getting the old games, honestly.", "Konami has delisted or "
             "never re-released most of the pre-2024 catalogue — the "
             "Team Silent games have no modern storefront release apart "
             "from Silent Hill 4 on GOG, and Origins, Shattered Memories "
             "and Downpour remain on their original platforms. Budget "
             "for original hardware or the remake."],
            ["Hours are story only.", "HowLongToBeat main-story figures — "
             "one ending, no UFO runs. A row with no figure yet weighs "
             "nothing rather than guessing."],
            "Game list, years and release dates from Wikipedia's Silent "
            "Hill, Silent Hill f and Silent Hill: Townfall articles; hours "
            "from HowLongToBeat main-story figures, verified by name.",
        ],
        "sections": sections,
    }

    out = prop.write(prop_, legacy_ids=LEGACY_IDS)

    print("wrote %s" % out.name)
    print("  %d sections, %d games, %d hours (%d essential), %d unreleased"
          % (len(sections), len(ids), round(hours), round(spine), len(coming)))
    for s in sections:
        print("   %-18s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))
    return prop_


if __name__ == "__main__":
    main()
