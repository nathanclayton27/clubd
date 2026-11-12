#!/usr/bin/env python3
"""Generate properties/outlaw-star.json — the complete 26-episode run.

    python tools/make_outlaw-star.py

Sunrise's 1998 space western, every episode, in the order the show numbers
them. One season, 26 rows, finished: TV Tokyo ran it from January 8 to
June 25, 1998 and nothing continued it. Titles, airdates and Toonami dates are
machine-read from Wikipedia's "List of Outlaw Star episodes" by
scratch/agent-outlaw/harvest.py; the committed result is
tools/data/outlaw-star.json and everything below is asserted against it.

TWO EPISODES HAVE BROADCAST HISTORIES WORTH A ROW NOTE, IN OPPOSITE
DIRECTIONS, AND BOTH ARE READ FROM THE SOURCE RATHER THAN REMEMBERED.

  * Episode 16, "Demon of the Water Planet", has no Japanese airdate at all —
    its OriginalAirDate field is the literal string "Not aired". The other 25
    went out weekly with no gap, which is what makes the missing slot a
    missing EPISODE and not a missing week, and main() asserts exactly that:
    25 distinct dates, seven days apart, unbroken. Toonami ran it in its
    numbered position, so English-speaking viewers saw it first. It is a row
    because it is an episode of the show.
  * Episode 23, "Hot Springs Planet Tenrei", is the reverse: it aired in Japan
    and was pulled from the 2001 Toonami run, reaching the West only when the
    revived block ran it seventeen years later. The list follows the Japanese
    broadcast, so it sits in its numbered place.

ANGEL LINKS IS OUT, AND NAMED. The franchise's one spin-off is a separate
13-episode Sunrise series that ran on Wowow in 1999. The main article files it
under "Spin-off" in the infobox — main() asserts that block still names it and
nothing else — and settles the scope question in one sentence, quoted in the
notes: "Outlaw Star and Angel Links take place in the same universe;
characters from both series appeared in an episode of Outlaw Star, but the two
have little else in relation." A shared setting is not a shared story, so it
is not a continuation of this list. The crossover the sentence refers to is
episode 19, "Law and Lawlessness" — Angel Links' own article names that
episode as where Duuz and Valeria debuted, and main() asserts the title it
names is one of the 26 parsed here, so the row note pointing at the spin-off
cannot drift onto the wrong episode.

THERE IS NO OVA AND NO FILM. A single-episode sequel was drafted and never
animated; the source's words are "Preliminary plans were made to create a
direct sequel in the form of a single-episode (OVA) called Sword of Wind, but
production never began." An unmade episode cannot be watched, so it is named
in the notes rather than listed. The manga and the light novels are print and
out of scope for a watch list; the manga has no official English release at
all, which main() asserts along with its chapter count.

NOTHING IS WEIGHTED, AND THE HUNT WAS EXHAUSTIVE. Weighting is all-or-nothing
— a row with no `w` silently counts as one hour — so a partial set of runtimes
would be worse than none. Every place a per-episode duration could live was
checked by scratch/agent-outlaw/runtimes.py and every one came up empty:
none of the 26 {{Episode list}} blocks has a RunTime or Aux field; no episode
has a Wikipedia article of its own (all 20 episode-title pages are redirects
to the list, and not one Title field is a wikilink); no episode has a Wikidata
item (nothing carries P179/P361/P4908/P1811 = Q2470001, and the series item
declares no parts); neither the series item nor the episode-list item carries
P2047, and the series item has no P2047 statement at all; there is no season
article; and the main article states no running time in prose. main() asserts
all eight of those zeroes before it will build, so the day the source grows a
runtime this generator stops rather than shipping a stale claim.

CROSS-LIST TICK SYNC DOES NOT APPLY. src/build.py syncs film-kind and
game-kind rows only, and this list's kind is "anime" — main() asserts the kind
contains neither word. Belt and braces, it also asserts no row note contains a
bare four-digit year, because build.py's `_year_of` falls back to reading one
out of a note when `n` is not a year, and every `n` here is an episode number.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop  # noqa: E402

SLUG = "outlaw-star"
DATA = pathlib.Path(__file__).resolve().parent / "data" / (SLUG + ".json")

EPISODES = 26
KIND = "anime"

ACCENT = "#8C2340"       # the Outlaw Star's crimson hull
ACCENT_DARK = "#FFB35C"  # ...and the gold of its grappler arms

EPISODE_LIST_URL = ("https://en.wikipedia.org/wiki/"
                    "List_of_Outlaw_Star_episodes")


def check_accent():
    """The pair, and each half of it, must be unused by every other list."""
    for f in sorted((prop.ROOT / "properties").glob("*.json")):
        if f.stem in (SLUG, "index", "search"):
            continue
        other = json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(other, dict):
            continue
        pair = (other.get("accent"), other.get("accentDark"))
        assert pair != (ACCENT, ACCENT_DARK), \
            "accent pair already belongs to %s" % f.stem
        for hexv in (ACCENT, ACCENT_DARK):
            assert hexv not in pair, "%s already uses %s" % (f.stem, hexv)


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    eps, series, scope, hunt = (data["episodes"], data["series"],
                                data["scope"], data["runtime_hunt"])

    # --- the shape of the run, three ways ----------------------------------
    assert len(eps) == EPISODES, "%d episodes in the data" % len(eps)
    assert [e["n"] for e in eps] == list(range(1, EPISODES + 1)), \
        "episode numbering is not contiguous 1..%d" % EPISODES
    assert series["episode_count"] == EPISODES, \
        "the article's own count is %d" % series["episode_count"]
    assert series["wikidata_episode_count"] == EPISODES, \
        "Wikidata counts %d episodes" % series["wikidata_episode_count"]
    assert series["info"]["network"] == "TV Tokyo", series["info"]["network"]
    assert series["info"]["studio"] == "Sunrise", series["info"]["studio"]
    assert series["first_aired"].endswith("1998") \
        and series["last_aired"].endswith("1998"), \
        "the run is no longer contained in 1998"

    # --- the one episode Japan never saw, and the one Toonami skipped ------
    unaired = series["unaired_in_japan"]
    assert [e["n"] for e in eps if not e["aired"]] == [unaired], \
        "more than one episode now lacks a Japanese airdate"
    assert series["japanese_broadcasts"] == EPISODES - 1, \
        "%d Japanese broadcasts for %d episodes" \
        % (series["japanese_broadcasts"], EPISODES)
    # Toonami ran the unaired one in its numbered slot: its English date falls
    # between its neighbours', which is what lets the note say "in sequence"
    order = [e["toonami"] for e in eps]
    assert order[unaired - 2] == "February 2, 2001" \
        and order[unaired - 1] == "February 5, 2001" \
        and order[unaired] == "February 6, 2001", \
        "episode %d no longer sits between its neighbours on Toonami" % unaired

    skipped = series["skipped_episode"]
    assert skipped != unaired, \
        "the skipped and unaired episodes have collapsed into one"
    assert eps[skipped - 1]["toonami"] == series["skipped_aired"], \
        "episode %d's English date is %r, the prose says %r" \
        % (skipped, eps[skipped - 1]["toonami"], series["skipped_aired"])
    assert series["skipped_years_later"] == 17, series["skipped_years_later"]

    # --- scope -------------------------------------------------------------
    assert scope["spinoffs_listed"] == ["Angel Links"], \
        "the franchise now files %r as spin-offs — the notes name only one" \
        % scope["spinoffs_listed"]
    assert "little else in relation" in scope["angel_links_quote"], \
        "the sentence the Angel Links decision rests on has changed"
    assert "production never began" in scope["ova_quote"], \
        "Sword of Wind may have gone into production — re-read the source"
    cross = scope["crossover_episode"]
    assert eps[cross - 1]["t"] == scope["crossover_title"], \
        "episode %d is %r, not the crossover episode %r" \
        % (cross, eps[cross - 1]["t"], scope["crossover_title"])

    # --- weights: eight empty sources, asserted before anything is built ---
    assert hunt == {
        "episode_table_runtime_fields": 0,
        "per_episode_articles": 0,
        "episode_title_redirects": 20,
        "per_episode_wikidata_items": 0,
        "season_articles": 0,
        "series_wikidata_P2047": None,
        "list_wikidata_P2047": None,
        "main_article_runtime_prose": 0,
    }, "the runtime hunt's result has changed — redo it before building"

    # --- rows ---------------------------------------------------------------
    notes = {
        1: "Series premiere",
        unaired: "Never broadcast in Japan; Toonami ran it in sequence, so "
                 "English-speaking viewers saw it first",
        cross: "Introduces Duuz and Valeria, who go on to the spin-off "
               "Angel Links",
        skipped: "Held back from the original Toonami run for its content; "
                 "the West did not see it until the revived block ran it "
                 "%d years later" % series["skipped_years_later"],
        # no "Series finale" on the last episode: its position already says
        # it (CLU-123, CLU-557)
    }
    items = []
    for e in eps:
        row = {"id": "ols-%d" % e["n"], "t": e["t"], "n": str(e["n"])}
        if e["n"] in notes:
            row["note"] = notes[e["n"]]
        items.append(row)

    sections = [{
        "id": "series",
        "title": "The series",
        "sub": prop.join_bits("1998", "%d episodes" % EPISODES,
                              series["info"]["network"]),
        "intro": "Every episode, numbered the way the show numbers them. One "
                 "season, start to finish — the Japanese broadcast ran from %s "
                 "to %s — and nothing came after it."
                 % (series["first_aired"], series["last_aired"]),
        "links": [{"label": "The episode list", "url": EPISODE_LIST_URL}],
        "open": True,
        "items": items,
    }]

    p = {
        "slug": SLUG,
        "title": "Outlaw Star",
        "subtitle": "the complete 26-episode run",
        "kind": KIND,
        "popularity": 60,
        "year": "1998",
        "blurb": "Sunrise's 1998 space western in full — 26 episodes, one "
                 "season, in broadcast order, with nothing left over.",
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ["Twenty-six episodes, and that is the whole show.",
             "One season on %s, %s to %s, and no sequel series, film or "
             "special was ever made. This list is finished on the day it is "
             "built. The count is checked three ways before it ships: the "
             "episode table's own numbering, the article's anime infobox, and "
             "Wikidata's episode-count statement."
             % (series["info"]["network"], series["first_aired"],
                series["last_aired"])],
            ["One episode never aired in Japan.",
             "Episode %d, %s, carries no Japanese broadcast date at all. The "
             "other %d went out weekly with no break, so the missing slot is a "
             "missing episode rather than a missing week. Toonami ran it in "
             "its numbered position on %s, which means English-speaking "
             "viewers saw it before anyone in Japan did. It is a row here "
             "because it is an episode of the show."
             % (unaired, eps[unaired - 1]["t"], EPISODES - 1,
                series["unaired_toonami_date"])],
            ["And one episode never aired on Toonami.",
             "The reverse case. Episode %d, %s, aired in Japan and was pulled "
             "from the 2001 Toonami broadcast for \"%s\"; the West did not see "
             "it until the revived Toonami block ran it on %s, %d years later. "
             "This list follows the Japanese broadcast, so it sits in its "
             "numbered place like everything else."
             % (skipped, eps[skipped - 1]["t"], series["skipped_reason"],
                series["skipped_aired"], series["skipped_years_later"])],
            ["Angel Links is not on this list, and that is a decision.",
             "It is the franchise's one spin-off — %d episodes on %s in %s, "
             "made by the same studio — and the source is direct about what it "
             "shares: \"%s\" The crossover it means is episode %d, %s. A "
             "shared setting and two borrowed characters are not a "
             "continuation, so watching this list does not leave Angel Links "
             "unfinished. It is named here so its absence reads as a choice "
             "rather than an oversight."
             % (scope["angel_links_episodes"], scope["angel_links_network"],
                scope["angel_links_aired"].split(", ")[-1],
                scope["angel_links_quote"], cross, scope["crossover_title"])],
            ["There is no OVA, no film and no continuation.",
             "A single-episode sequel got as far as character designs and a "
             "plot outline and no further: \"%s\" No production date was ever "
             "set. An episode that was never animated cannot be watched, so it "
             "is named rather than listed. The manga (%d chapters, and no "
             "official English release) and the light novels are print, and "
             "out of scope for a watch list."
             % (scope["ova_quote"], scope["manga_chapters"])],
            ["Nothing is weighted, and hours are not tracked here.",
             "Weighting is all or nothing — a row without a weight silently "
             "counts as one hour — so a handful of sourced runtimes would be "
             "worse than none. Every place a per-episode duration could live "
             "was checked and every one is empty: not one of the 26 episode "
             "entries carries a running-time field; no episode has a Wikipedia "
             "article of its own, since the 20 episode titles that have a page "
             "at all are redirects to the list and no title in the table is "
             "even a link; no episode "
             "has a Wikidata item, so there is no per-episode duration "
             "statement to read; neither the series nor the episode-list "
             "Wikidata item carries a duration; there is no season article to "
             "hold one; and the main article gives no running time in prose. "
             "So every row counts one, and the page counts episodes."],
            "Titles, airdates and Toonami dates machine-read from Wikipedia's "
            "List of Outlaw Star episodes; the run, the spin-off and the "
            "unmade OVA from the Outlaw Star, Angel Links and Outlaw Star "
            "chapters articles; the episode count cross-checked against the "
            "anime infobox and Wikidata before this builds.",
        ],
        "sections": sections,
    }

    # --- house rules this list has to hold ---------------------------------
    check_accent()
    assert "film" not in KIND and "game" not in KIND, \
        "build.py syncs film and game kinds; %r would start syncing" % KIND
    for s in sections:
        for x in s["items"]:
            assert not re.search(r"\b(?:18|19|20)\d{2}\b", x.get("note") or ""), \
                "row %s leaks a bare year into its note: %r" \
                % (x["id"], x["note"])
            assert "w" not in x, "a weight crept in — this list is unweighted"
            assert not re.fullmatch(r"(18|19|20)\d{2}", x["n"]), \
                "row %s numbers itself with a year" % x["id"]

    out = prop.write(p)
    total = sum(len(s["items"]) for s in sections)
    print("wrote %s — %d rows in %d section, unweighted"
          % (out.name, total, len(sections)))
    for s in sections:
        print("   %-14s %3d  %s" % (s["title"], len(s["items"]), s["sub"]))
    print("   %d aired in Japan, %d aired on Toonami; episode %d never aired "
          "in Japan, episode %d was skipped on Toonami"
          % (series["japanese_broadcasts"], EPISODES - 1, unaired, skipped))


if __name__ == "__main__":
    main()
