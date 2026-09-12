#!/usr/bin/env python3
"""Generate properties/my-hero-academia.json — the whole anime, season by season.

    PYTHONIOENCODING=utf-8 python tools/make_my-hero-academia.py

175 rows: the 170 episodes of the eight-season television run in air order,
eight season sections; the one bonus special that followed it, in a dated
section of its own; then the four films in a dated section at the end.

SCOPE, and every one of these is a decision rather than an accident:

  * THE BONUS SPECIAL IS IN. It aired on 2 May 2026, five months after the
    finale, in the series' own television slot, and the source counts it in
    the series total — the infobox reads "170 + Special + 11 OVAs" and numbers
    the broadcast "170+1" rather than 171. It gets its own section because
    the source gives it its own section, and because it is not part of any
    season.
  * THE FOUR FILMS ARE IN, at the end, in a dated section. They are not
    episodes: each is feature-length and released between two broadcast
    years. That makes the unit "entries" rather than "episodes", the same
    trade psych.json takes. A reader who only wants the television run stops
    at the bonus special.
  * THE FIVE RECAP SPECIALS ARE OUT. Wikipedia's season pages carry them in a
    table apart from the episodes and number them 13.5 (March 2017) and
    138.5.1-138.5.4 (April 2024) rather than into the 1-170 run. They re-air
    material that is already on this list.
  * THE ELEVEN OVAS ARE OUT. Not one has a published length, and the single
    figure that does exist — two minutes, for All Might: Rising — proves the
    set is nowhere near uniform, so weighing them at the television figure
    would invent a number eleven times over. They are bundled with manga
    volumes, film releases and event screenings rather than broadcast.

Both exclusions are one flag each: RECAPS and OVAS below. Flip either and the
generator builds the section, so neither decision is baked into the data.

WEIGHTED, and every row carries a weight, because an unweighted row on a
weighted list silently counts as a full hour (CLU-131). The runtime hunt is
written out in scratch/agent-mha/harvest.py and its result is short: nothing
publishes a per-episode length for this show. No {{Episode list}} row carries
a |RunTime; the string does not occur on the eight season pages or the episode
list at all (asserted, not assumed); and of the 178 items Wikidata files as
part of the series, NOT ONE carries P2047, while the only eight with an
article of their own are the season pages. What is published is the series
infobox's two labelled figures — 24 minutes (Season 1), 23 minutes (Seasons
2-8) — so an episode weighs its own season's figure, and each film weighs the
runtime its own article prints. Nothing is averaged and nothing is estimated.

The one weight that is a judgement call: the bonus special, for which the
source states no length at all. It takes the 23 minutes the box states for
seasons 2-8, because it aired as one broadcast in that slot, and the note on
the list says so in as many words.

Everything numeric and every title comes from
tools/data/my-hero-academia-episodes.json, written by
scratch/agent-mha/harvest.py from the eight "My Hero Academia season N"
articles, "List of My Hero Academia episodes", "My Hero Academia (TV series)"
and the four film articles. That script asserts the per-season counts against
the page's own {{Series overview}}, the in-season numbering contiguous, the
overall numbering contiguous across all eight seasons, each season's first and
last air date against the overview, and the special's date and number against
both. This script re-asserts the counts, the numbering and the weights before
it writes anything.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from gwlib import prop           # noqa: E402
from gwlib import runtime        # noqa: E402

SLUG = "my-hero-academia"
DATA = pathlib.Path(__file__).resolve().parent / "data" / \
    "my-hero-academia-episodes.json"
WIKI = "https://en.wikipedia.org/wiki/"

SEASONS = 8
EPISODES = 170
FILMS = 4
RECAPS = False          # the five recap specials — see the docstring
OVAS = False            # the eleven OVAs — see the docstring
SPECIAL_NUMBER = "170+1"

# The two proper nouns are the episode list's own lede — "an anime television
# series based on the manga series My Hero Academia by Kōhei Horikoshi …
# produced by Bones" — rather than anything typed from memory. The years are
# interpolated from the series infobox's first and last air dates.
S1_INTRO = ("Bones's adaptation of Kōhei Horikoshi's manga: a school for "
            "superheroes, one class of first-years, and a television run that "
            "follows them from %s to %s.")
SPECIAL_INTRO = ("One broadcast, months after the finale, in the slot the "
                 "series had. Wikipedia numbers it 170+1 rather than 171 and "
                 "keeps it out of season 8; so does this.")
FILMS_INTRO = ("Feature-length, and none of them part of a season: each one "
               "opened in cinemas between two broadcast years.")


def hours(minutes):
    return round(minutes / 60.0, 2)


def year_span(dates):
    ys = sorted({int(d[:4]) for d in dates})
    assert ys, "no dates"
    a, b = ys[0], ys[-1]
    if a == b:
        return str(a)
    if a // 100 == b // 100:
        return "%d–%02d" % (a, b % 100)
    return "%d–%d" % (a, b)


def film_minutes(f):
    """The length to weigh a film at, through the house rule on cuts."""
    cuts = [(m, label) for m, label in f["cuts"]]
    minutes, why = runtime.weigh(cuts)
    assert minutes, "%s: %s" % (f["t"], why)
    return minutes, why


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    series, ov = d["series"], d["overview"]

    assert series["seasons"] == SEASONS, \
        "the source now states %d seasons" % series["seasons"]
    assert series["episodes"] == EPISODES, \
        "the source now counts %d episodes" % series["episodes"]
    per_season = {int(k): v for k, v in series["runtime_by_season"].items()}
    assert sorted(per_season) == list(range(1, SEASONS + 1)), per_season
    # The spin-off is a different series with its own article, and nothing
    # here may quietly absorb it.
    assert not any("Vigilantes" in r["t"] for rows in d["seasons"].values()
                   for r in rows), "a Vigilantes episode reached the run"

    sections, covered = [], 0
    for n in range(1, SEASONS + 1):
        rows = d["seasons"][str(n)]
        stated = ov[str(n)]["episodes"]
        assert len(rows) == stated, \
            "season %d holds %d rows, the overview says %d" % (
                n, len(rows), stated)
        assert [r["e"] for r in rows] == list(range(1, len(rows) + 1)), \
            "season %d in-season numbering is not contiguous" % n
        assert [r["o"] for r in rows] == list(
            range(covered + 1, covered + len(rows) + 1)), \
            "season %d overall numbering does not follow episode %d" % (
                n, covered)

        w = hours(per_season[n])
        items = []
        for r in rows:
            item = {"id": "mha-s%de%d" % (n, r["e"]), "t": r["t"],
                    "n": str(r["e"]), "w": w}
            if r["o"] == 1:
                item["note"] = "series premiere"
            elif r["o"] == EPISODES:
                item["note"] = "series finale"
            items.append(item)
        covered += len(rows)

        sec = {"id": "s%d" % n, "title": "Season %d" % n,
               "sub": "%s · %d episodes · %d hours"
                      % (year_span([r["air"] for r in rows]), len(rows),
                         round(len(rows) * w)),
               "links": [{"label": "The season",
                          "url": WIKI + "My_Hero_Academia_season_%d" % n}],
               "items": items}
        if n == 1:
            sec["open"] = True
            sec["intro"] = S1_INTRO % (series["first_aired"][:4],
                                      series["last_aired"][:4])
        sections.append(sec)

    assert covered == EPISODES, "the seasons cover %d episodes" % covered

    sp = d["special"]
    assert sp["number"] == SPECIAL_NUMBER, \
        "the bonus special is numbered %r now" % sp["number"]
    assert sp["air"] == ov["special"]["released"], "the special's date moved"
    assert int(sp["number"].split("+")[0]) == EPISODES, sp["number"]
    special_w = hours(per_season[SEASONS])
    sections.append({
        "id": "special", "title": "Bonus special",
        "sub": "%s · one broadcast" % sp["air"][:4],
        "intro": SPECIAL_INTRO,
        "links": [{"label": "The episode list",
                   "url": WIKI + "List_of_My_Hero_Academia_episodes"}],
        "items": [{"id": "mha-special-1", "t": sp["t"],
                   "n": sp["number"], "w": special_w,
                   "note": prop.join_bits("after the run",
                                          "no published length of its own")}],
    })

    films, qids = d["films"], dict(d["wikidata"]["film_items"])
    assert len(films) == FILMS, "the source now carries %d films" % len(films)
    film_items, film_mins = [], []
    for f in films:
        minutes, _why = film_minutes(f)
        film_mins.append(minutes)
        year = f["released"][:4]
        item = {"id": "mha-film-%s" % year, "t": f["t"], "n": year,
                "w": hours(minutes), "note": "%d min" % minutes,
                # A film pairs with a film. `kind` is "anime", which mints no
                # sync key at all (build.py gates on the word), so the four
                # films declare their own medium the way satoshi-kon's do —
                # CLU-369 — and the episodes deliberately declare none.
                "m": "f"}
        q = qids.get(f["page"])
        assert q, "no Wikidata item resolved for %s" % f["page"]
        item["q"] = q
        film_items.append(item)
    assert len(set(x["id"] for x in film_items)) == FILMS, \
        "two films released in the same year would share an id"
    sections.append({
        "id": "films", "title": "The films",
        "sub": "%s · four films · %d hours"
               % (year_span([f["released"] for f in films]),
                  round(sum(hours(m) for m in film_mins))),
        "intro": FILMS_INTRO,
        "items": film_items,
    })

    if RECAPS:
        sections.append({
            "id": "recaps", "title": "The recap specials",
            "sub": "%s · five broadcasts"
                   % year_span([r["air"] for r in d["recaps"]]),
            "items": [{"id": "mha-recap-%s" % r["number"].replace(".", "-"),
                       "t": r["t"], "n": r["number"], "w": special_w,
                       "note": "recap special"} for r in d["recaps"]],
        })
    if OVAS:
        sections.append({
            "id": "ovas", "title": "The OVAs",
            "sub": "%s · eleven releases"
                   % year_span([o["first"] for o in d["ovas"]]),
            "items": [{"id": "mha-ova-%d" % o["n"], "t": o["t"],
                       "n": str(o["n"])} for o in d["ovas"]],
        })

    allit = [x for s in sections for x in s["items"]]
    rows = len(allit)
    assert rows == EPISODES + 1 + FILMS, "built %d rows" % rows
    assert all(isinstance(x["w"], float) and x["w"] > 0 for x in allit), \
        "a row carries no weight, and on a weighted list that reads as an hour"
    total = sum(x["w"] for x in allit)

    p = {
        "slug": SLUG,
        "title": "My Hero Academia",
        "subtitle": "all eight seasons in air order, then the special and the films",
        "kind": "anime",
        "popularity": 83,
        "year": "%s–%s" % (series["first_aired"][:4], sp["air"][:4]),
        "blurb": "All %d episodes of the eight-season run, the bonus special "
                 "and the four films — about %d hours at U.A."
                 % (EPISODES, round(total)),
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        # #38A969 is the colour Wikipedia's own season 1 episode table uses for
        # this show, and it is the most isolated green in the catalogue's light
        # accents at 17.6 delta-E from its nearest neighbour. The dark half is
        # 15.1 from its two nearest, and the pair is checked unique by
        # tools/qa_lint.py.
        "accent": "#38A969",
        "accentDark": "#D7F26A",
        "tiers": False,
        "notes": [
            ["The run is finished.",
             "Season 8 was the last, and it ended on 13 December 2025. One "
             "bonus special followed on 2 May 2026: the source numbers that "
             "broadcast 170+1 rather than 171, so it sits in a section of its "
             "own after season 8 rather than inside it. Rows carry the "
             "in-season number; the source's overall numbering runs 1 to %d "
             "across the eight seasons." % EPISODES],
            ["Weighted from the only length anyone publishes.",
             "There is no per-episode runtime for this show anywhere. Not one "
             "of the %d episode rows carries a length, the eight season "
             "articles do not state one, and of the %d items Wikidata files "
             "as part of the series not one carries a runtime — the only "
             "eight with an article of their own are the season pages. What "
             "the series' own infobox does publish is two figures, each "
             "labelled with the seasons it covers: 24 minutes for season 1 "
             "and 23 minutes for seasons 2 to 8. So every episode weighs its "
             "own season's figure, each film weighs the runtime printed on "
             "its own article, and nothing here is averaged or estimated."
             % (EPISODES, d["wikidata"]["items_in_series"])],
            ["One weight is a judgement call.",
             "The bonus special has no published length at all. It weighs the "
             "23 minutes the infobox states for seasons 2 to 8, because it "
             "aired as a single broadcast in that slot — the one figure on "
             "this list that was not labelled for the thing it measures, and "
             "the row says so."],
            ["The films are not episodes.",
             "Four of them, between 2018 and 2024, each opening in cinemas "
             "between two broadcast years. They sit in a dated section at the "
             "end rather than inside a season, which is why this list counts "
             "entries rather than episodes; a reader who only wants the "
             "television run stops at the bonus special."],
            ["The recap specials are not here.",
             "Wikipedia's season pages carry five of them in a table apart "
             "from the episodes, numbered 13.5 and 138.5.1 to 138.5.4 rather "
             "than into the 1 to %d run: one ahead of season 2 in March 2017, "
             "four ahead of season 7 in April 2024. They re-air material "
             "already on this list." % EPISODES],
            ["The OVAs are not here either.",
             "There are eleven, bundled with manga volumes and film releases "
             "or screened at events rather than broadcast, and not one has a "
             "published length. The single figure that does exist — two "
             "minutes, for All Might: Rising — shows how far from uniform the "
             "set is, so weighing them at the television figure would mean "
             "inventing a number eleven times. No idea whether they are worth "
             "it; the episode list documents them under its own heading."],
            ["Vigilantes is a different series.",
             "The spin-off has its own article and its own episodes, and none "
             "of them are here."],
            "Titles, numbering and air dates machine-read from the eight "
            "Wikipedia season articles and the episode list; the per-season "
            "runtime from the series article's infobox; film runtimes and "
            "release dates from the four films' own articles; the absence of "
            "any per-episode runtime checked against Wikidata as well.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d rows (%d episodes + 1 special + %d films), %.2f hours"
          % (out.name, rows, EPISODES, FILMS, total))
    for s in sections:
        print("   %-14s %3d rows  %-34s %6.2f h"
              % (s["title"], len(s["items"]), s["sub"],
                 sum(x["w"] for x in s["items"])))
    print("   films weigh %s minutes" % film_mins)


if __name__ == "__main__":
    main()
