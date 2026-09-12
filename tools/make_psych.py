#!/usr/bin/env python3
"""Generate properties/psych.json — every Psych broadcast, season by season.

    PYTHONIOENCODING=utf-8 python tools/make_psych.py

123 rows: one per broadcast of the 2006-2014 run, in air order, eight
season sections, then the three films in a dated section of their own.

120 of those rows are the run. The season tables number 121 episodes, because
the musical is one double-length broadcast carrying two numbers — overall
110-111, season seven's 15 and 16 — so it is one row spanning both, exactly
as the season overview and its own article file it. It sits at the end of
season seven, which is both where the numbering puts it and where it aired:
after "No Trout About It" (May 2013) and before season eight opened (January
2014).

The three films are NOT episodes. They premiered three to seven years after
the run, so they get the last section and nothing else changes; a reader who
only wants the show stops at season eight.

WEIGHTED, and every row carries a weight, because an unweighted row in a
weighted list silently counts as an hour (CLU-131). Psych is not a show with
a published runtime per episode: no Psych episode has a runtime in Wikidata,
and only six of them have an article of their own that publishes a length. So
the weights are the two published figures there are — an episode's own
article where it has one, and the series article's stated 42 minutes
otherwise — which is the rule ghost-in-the-shell and urusei-yatsura already
ship. Nothing is estimated and nothing is averaged.

Everything numeric and every title comes from tools/data/psych-episodes.json,
written by scratch/agent-psych/harvest.py from the eight "Psych season N"
articles, "List of Psych episodes", and the series, episode and film
infoboxes. That script asserts the per-season counts against the page's own
{{Series overview}}, the in-season numbering contiguous, each season's first
and last air date against the overview, and the overall numbering to be
1-121 exactly once with the musical filling 110-111. This script re-asserts
the counts and the numbering before it writes anything.

The pilot is the one row with two lengths on record: 66 minutes as broadcast
and a 78-minute extended version. The bar measures the broadcast version, as
the house rule on alternate cuts has it, and the row note names the other.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from gwlib import prop  # noqa: E402

SLUG = "psych"
DATA = pathlib.Path(__file__).resolve().parent / "data" / "psych-episodes.json"
WIKI = "https://en.wikipedia.org/wiki/"

EXPECT = {1: 15, 2: 16, 3: 16, 4: 16, 5: 16, 6: 16, 7: 14, 8: 10}
ROWS = 120          # broadcasts of the run: 119 tabled rows + the musical
EPISODES = 121      # numbers those rows cover
FILMS = 3

S1_INTRO = ("A fake psychic detective agency in Santa Barbara, a case an "
            "episode, and a childhood flashback to open most of them.")
FILMS_INTRO = ("Feature-length and years later: not episodes, and not part "
               "of any season.")


def hours(minutes):
    return round(minutes / 60.0, 2)


def year_span(dates):
    ys = sorted({int(d[:4]) for d in dates})
    assert ys, "no air dates"
    if ys[0] == ys[-1]:
        return str(ys[0])
    a, b = ys[0], ys[-1]
    if a // 100 == b // 100:
        return "%d–%02d" % (a, b % 100)
    return "%d–%d" % (a, b)


def runtime_note(row, default_min):
    """A row says its length only where that length is not the series' own."""
    bits = []
    if row["min"] != default_min:
        bits.append("%d min" % row["min"])
    for alt in row.get("alt") or []:
        bits.append("a %d-minute %s exists" % (alt["min"], alt["of"]))
    return prop.join_bits(*bits)


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    default_min = d["series"]["runtime_min"]
    assert d["series"]["seasons_stated"] == 8, "the series is not eight seasons"
    assert d["series"]["episodes_stated"] == EPISODES, \
        "the series article states %d episodes" % d["series"]["episodes_stated"]

    mus = d["musical"]
    assert mus["season"] == 7 and mus["e"] == [15, 16] and mus["o"] == [110, 111]

    sections, covered = [], 0
    for n in range(1, 9):
        rows = d["seasons"][str(n)]
        assert len(rows) == EXPECT[n] == d["overview"][str(n)]["episodes"], \
            "season %d holds %d rows" % (n, len(rows))
        assert [r["e"] for r in rows] == list(range(1, len(rows) + 1)), \
            "season %d in-season numbering is not contiguous" % n

        items, dates = [], [r["air"] for r in rows]
        for r in rows:
            item = {"id": "psych-s%de%d" % (n, r["e"]), "t": r["t"],
                    "n": str(r["e"]), "w": hours(r["min"])}
            note = runtime_note(r, default_min)
            if note:
                item["note"] = note
            items.append(item)

        if n == mus["season"]:
            assert rows[-1]["e"] + 1 == mus["e"][0], \
                "the musical does not follow season %d's last episode" % n
            assert rows[-1]["air"] < mus["air"], \
                "the musical aired before season %d finished" % n
            items.append({
                "id": "psych-s%de%d" % (n, mus["e"][0]), "t": mus["t"],
                "n": "%d–%d" % (mus["e"][0], mus["e"][-1]),
                "w": hours(mus["min"]),
                "note": prop.join_bits("One double-length broadcast, December "
                                       "2013", "%d min" % mus["min"])})
            dates.append(mus["air"])

        eps = sum(len(x["n"].split("–")) for x in items)
        covered += eps
        h = sum(x["w"] for x in items)
        sec = {"id": "s%d" % n, "title": "Season %d" % n,
               "sub": "%s · %s · %d hours"
                      % (year_span(dates),
                         "%d episodes in %d rows" % (eps, len(items))
                         if eps != len(items) else "%d episodes" % eps,
                         round(h)),
               "links": [{"label": "The season",
                          "url": WIKI + "Psych_season_%d" % n}],
               "items": items}
        if n == 1:
            sec["open"] = True
            sec["intro"] = S1_INTRO
        sections.append(sec)

    films = d["films"]
    assert len(films) == FILMS, "expected %d films" % FILMS
    sections.append({
        "id": "films", "title": "The films",
        "sub": "%s · three films, after the run"
               % year_span([f["released"] for f in films]),
        "intro": FILMS_INTRO,
        "links": [{"label": "The film series",
                   "url": WIKI + "Psych_(film_series)"}],
        "items": [{"id": "psych-film-%s" % f["released"][:4], "t": f["t"],
                   "n": f["released"][:4], "w": hours(f["min"]),
                   "note": "%d min" % f["min"]} for f in films]})

    run = [x for s in sections[:8] for x in s["items"]]
    assert len(run) == ROWS, "%d rows in the run" % len(run)
    assert covered == EPISODES, "rows cover %d episodes" % covered
    allit = [x for s in sections for x in s["items"]]
    assert len(allit) == ROWS + FILMS, len(allit)
    assert all(isinstance(x["w"], float) and x["w"] > 0 for x in allit), \
        "a row carries no weight"
    total = sum(x["w"] for x in allit)

    p = {
        "slug": SLUG,
        "title": "Psych",
        "subtitle": "eight seasons in air order, with the films after",
        "kind": "tv & films",
        "popularity": 62,
        "year": "2006–2021",
        "blurb": "All %d episodes of the eight-season run in %d broadcasts, "
                 "then the three films — about %d hours in Santa Barbara."
                 % (EPISODES, ROWS, round(total)),
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#2F7D32",
        "accentDark": "#F2C14E",
        "tiers": False,
        "notes": [
            ["120 rows, 121 episodes.", "The musical is one double-length "
             "broadcast carrying two numbers — season seven's 15 and 16 "
             "— so it is one row spanning both, and it sits at the end of "
             "season seven, where both the numbering and the December 2013 "
             "air date put it."],
            ["Weighted by published runtime.", "Psych has no runtime per "
             "episode in Wikidata and only six episodes have an article of "
             "their own that publishes a length, so a row weighs its own "
             "article's figure where there is one — the pilot at 66 "
             "minutes, Dual Spires at 50, four season-one episodes at 42 or "
             "43 — and the series article's stated 42 minutes otherwise. "
             "The musical weighs its article's 88. A row notes its length "
             "only where that length is not 42 minutes."],
            ["The pilot has two lengths on record.", "The bar measures the "
             "66-minute broadcast version; its article also records a "
             "78-minute extended version, and the row says so."],
            ["The films are not episodes.", "Three films followed the run "
             "between 2017 and 2021. They are feature-length and years "
             "later, so they sit in a dated section of their own at the end "
             "rather than inside a season, and a reader who only wants the "
             "show stops at season eight."],
            "Titles, numbering and air dates machine-read from the eight "
            "Wikipedia season articles and the episode list; runtimes from "
            "the series, episode and film infoboxes.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d rows (%d of the run + %d films), %.2f hours"
          % (out.name, len(allit), len(run), FILMS, total))
    for s in sections:
        print("   %-10s %3d rows  %-34s %6.2f h"
              % (s["title"], len(s["items"]), s["sub"],
                 sum(x["w"] for x in s["items"])))


if __name__ == "__main__":
    main()
