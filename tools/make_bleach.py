#!/usr/bin/env python3
"""Generate properties/bleach.json.

    python tools/make_bleach.py

One list of 416: the original *Bleach* run (366 episodes, 2004–2012) and its
sequel *Bleach: Thousand-Year Blood War* (50 episodes, 2022–2026), in
broadcast order, sectioned by arc. Wikipedia's sixteen seasons ARE the arcs — each season
article opens by naming the arc it covers — and the sequel's four Parts are
the arc divisions its own article marks.

The thing this list exists to show is the filler. Bleach's filler burden is
second only to Naruto's, and whole seasons of it are anime-original. Every row
is classified from two independent sources that have to agree:

  * animefillerlist.com's published per-episode classification, and
  * the manga chapters the Bleach wiki records each episode as adapting.

An episode both call anime-original is marked and flagged optional. An episode
they disagree about is left UNMARKED on purpose — a wrong filler label sends
someone skipping real story, and an unmarked filler episode only costs them
twenty minutes. Nothing is guessed either way, in either direction.

Both are cached, by scratch/bleach/parse.py and scratch/bleach/
fetch_chapters.py, so this generator is offline and byte-reproducible. The
counts come from the enumerated episode tables on the Wikipedia season
articles, never an infobox summary; parse.py asserts the two agree per season,
and TOTAL below asserts the whole thing, so a future desync fails the build
loudly instead of shipping a short list.

Both series are finished. The sequel's fourth and final Part ended on 27
October 2026 at its 50th episode (416 overall); the Wikipedia lead says the
run totals 50 episodes, and LAST in scratch/bleach/parse.py is 416 to match.

No runtimes. Nobody publishes a verified length for 416 individual episodes, so
this ships unweighted rather than repeating an invented 24 minutes 416 times
into everyone's finish date.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from gwlib import prop as gwprop            # noqa: E402

DATA = ROOT / "scratch" / "bleach" / "bleach.json"
CHAPTERS = ROOT / "scratch" / "bleach" / "chapters.json"

SLUG = "bleach"
ORIGINAL = 366
TOTAL = 416          # through Thousand-Year Blood War #50, the finale, 27 Oct 2026

SEASON_URL = "https://en.wikipedia.org/wiki/Bleach_season_%d"
TYBW_URL = "https://en.wikipedia.org/wiki/Bleach:_Thousand-Year_Blood_War"

# The Bleach wiki writes an episode's `|chapters=` field as one of these when
# the episode adapts nothing — an empty field and the literal word both occur,
# on the same template, so both have to count as "no manga behind this".
NO_CHAPTERS = ("", "none", "n/a", "-", "none.", "tbd", "unknown")


def dash(first, last):
    return str(first) if first == last else "%d–%d" % (first, last)


def spans(numbers):
    """[3, 4, 5, 9] -> '3–5, 9'."""
    out, run = [], []
    for n in sorted(numbers):
        if run and n == run[-1] + 1:
            run.append(n)
        else:
            if run:
                out.append(run)
            run = [n]
    if run:
        out.append(run)
    return ", ".join(dash(r[0], r[-1]) for r in out)


def classify(afl, chapters):
    """filler / canon / unconfirmed / unclassified, from the two sources.

    `afl` is None where the published list has not reached the episode yet;
    that is one source, not two, so it cannot produce a filler mark."""
    if afl is None:
        return "unclassified"
    if afl != "filler":
        return "canon"
    # the filler list says anime-original; the chapter mapping decides whether
    # that is confirmed or contradicted
    return "unconfirmed" if chapters else "filler"


def main():
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    chap = json.loads(CHAPTERS.read_text(encoding="utf-8"))

    assert raw["original"] == ORIGINAL, \
        "the season tables come to %d episodes, expected %d" % (
            raw["original"], ORIGINAL)
    assert raw["last"] == TOTAL, \
        "scratch/bleach/parse.py stops at %d, this generator expects %d" % (
            raw["last"], TOTAL)

    afl = {int(n): v for n, v in raw["filler"].items()}
    adapts = {}
    for e in range(1, TOTAL + 1):
        row = chap.get(str(e))
        assert row, "the Bleach wiki has no page for episode %d" % e
        adapts[e] = row["chapters"].strip().lower() not in NO_CHAPTERS

    state, counts = {}, {"filler": 0, "canon": 0,
                         "unconfirmed": 0, "unclassified": 0}
    for e in range(1, TOTAL + 1):
        s = classify(afl.get(e), adapts[e])
        state[e] = s
        counts[s] += 1
    assert sum(counts.values()) == TOTAL, counts

    conflict = [e for e in state if state[e] == "unconfirmed"]
    unclassified = [e for e in state if state[e] == "unclassified"]
    filler = counts["filler"]

    assert unclassified == list(range(TOTAL - len(unclassified) + 1, TOTAL + 1)), \
        "the published filler list has a hole in the middle, not just a tail: " \
        "%s" % spans(unclassified)
    assert not any(state[e] == "filler" for e in unclassified), unclassified

    runs = [dict(s, kind="season") for s in raw["seasons"]]
    for p in raw["parts"]:
        if p["first"] > TOTAL:
            continue
        runs.append(dict(p, kind="part", last=min(p["last"], TOTAL)))

    assert runs[0]["first"] == 1, "the list does not start at episode 1"
    for a, b in zip(runs, runs[1:]):
        assert b["first"] == a["last"] + 1, \
            "gap or overlap between sections at episode %d" % b["first"]
    assert runs[-1]["last"] == TOTAL, \
        "sections run to %d, expected %d" % (runs[-1]["last"], TOTAL)

    titles = [r["title"] for r in runs]
    assert len(titles) == len(set(titles)), \
        "two sections would share a title: %s" % sorted(
            t for t in titles if titles.count(t) > 1)[:2]

    sections = [build_section(r, state) for r in runs]
    rows = sum(len(s["items"]) for s in sections)
    assert rows == TOTAL, \
        "built %d rows, expected %d — the source tables moved" % (rows, TOTAL)
    assert sum(1 for s in sections for x in s["items"] if x.get("opt")) == filler

    prop = {
        "slug": SLUG,
        "title": "Bleach",
        "subtitle": "The original run and Thousand-Year Blood War",
        "kind": "anime",
        "popularity": 85,
        "year": "2004–2026",
        "blurb": "%d episodes in broadcast order, both series, with the "
                 "filler marked." % TOTAL,
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": "#E85A0C",
        "accentDark": "#FF9B5E",
        "tiers": False,
        "notes": [
            ["Filler.",
             "%d of %d episodes are marked anime-original and flagged "
             "optional: “Filler arc” for a run of three or more, "
             "“Anime-original” for a one-off or a pair. A row has to be "
             "called filler by animefillerlist.com's published list AND "
             "adapt no manga chapter in the Bleach wiki's episode data "
             "before it gets marked. An unmarked row adapts the manga."
             % (filler, TOTAL)],
            ["Unmarked on purpose.",
             "%d episodes are left unmarked because the two sources disagree "
             "about them — the filler list calls them filler, the chapter "
             "mapping ties them to a chapter, an omake or a side story: %s. "
             "A wrong filler label costs you real story; leaving one unmarked "
             "costs you an episode. Nothing here is guessed."
             % (len(conflict), spans(conflict))],
        ] + ([
            # only while the published filler list trails the broadcast; it
            # has covered all 416 since the finale
            ["Not classified yet.",
             "The published filler list stops at episode %d, so the %d "
             "episodes of Part 4 that have aired so far — %s — have only one "
             "source behind them and carry no filler mark either way. The "
             "chapter mapping ties every one of them to the manga."
             % (unclassified[0] - 1, len(unclassified), spans(unclassified))],
        ] if unclassified else []) + [
            ["No runtimes.",
             "There is no verified per-episode length for %d episodes, so "
             "every row weighs the same and the pace counts episodes rather "
             "than minutes. A blanket 24 minutes would read as measured and "
             "would be invented." % TOTAL],
            ["Arcs.",
             "Sections are the arcs: Wikipedia's sixteen seasons of the "
             "original run, each of which is one named arc, then the four "
             "Parts of Thousand-Year Blood War. Rows are numbers, not titles "
             "— Bleach's episode titles routinely name the outcome of the "
             "episode."],
            ["Both series are finished.",
             "The original run finished at 366 episodes in 2012. Thousand-"
             "Year Blood War finished at 50 episodes in October 2026, when "
             "Part 4 ended."],
        ],
        "sections": sections,
    }

    out = gwprop.write(prop)
    print("wrote %s" % out.name)
    print("  %d sections, %d rows (%d + %d)"
          % (len(sections), rows, ORIGINAL, TOTAL - ORIGINAL))
    print("  %d filler, %d unmarked on a conflict, %d not classified, "
          "%d adapt the manga"
          % (filler, len(conflict), len(unclassified), counts["canon"]))
    for s in sections:
        marked = sum(1 for x in s["items"] if x.get("opt"))
        print("   %-56s %3d  %s" % (s["sub"], len(s["items"]),
                                    "%d filler" % marked if marked else ""))


def build_section(run, state):
    first, last = run["first"], run["last"]
    n = last - first + 1
    episodes = list(range(first, last + 1))
    filler = [e for e in episodes if state[e] == "filler"]
    conflict = [e for e in episodes if state[e] == "unconfirmed"]

    # "filler arc" for a run of three or more consecutive anime-original
    # episodes, or for any row in a section that is anime-original end to end;
    # "anime-original" for a one-off or a pair sitting inside a canon arc
    whole_arc = bool(filler) and len(filler) == n
    run_len, i = {}, 0
    while i < len(episodes):
        if state[episodes[i]] != "filler":
            i += 1
            continue
        j = i
        while j < len(episodes) and state[episodes[j]] == "filler":
            j += 1
        for e in episodes[i:j]:
            run_len[e] = j - i
        i = j
    note = {e: ("Filler arc" if whole_arc or run_len[e] >= 3
                else "Anime-original") for e in filler}

    items = []
    for e in episodes:
        row = {"id": "ble-%d" % e, "t": "Episode", "n": str(e)}
        if e in note:
            row["note"] = note[e]
            row["opt"] = 1
        items.append(row)

    if run["kind"] == "season":
        sub = "Season %d · episode%s %s" % (run["season"], "" if n == 1 else "s",
                                            dash(first, last))
        link = {"label": "Episode list", "url": SEASON_URL % run["season"]}
        sid = "ble-s%d-%s" % (run["season"], gwprop.slug(run["title"]))
    else:
        sub = "Thousand-Year Blood War part %d · episode%s %s" % (
            run["part"], "" if n == 1 else "s", dash(first, last))
        link = {"label": "Episode list", "url": TYBW_URL}
        sid = "ble-tybw%d-%s" % (run["part"], gwprop.slug(run["title"]))

    if filler and len(filler) == n:
        sub += " · filler arc"
    elif filler:
        sub += " · %d of %d filler" % (len(filler), n)

    intro = []
    if conflict:
        intro.append("Unmarked here: %s — the filler list and the chapter "
                     "mapping disagree." % spans(conflict))
    unclassified = [e for e in episodes if state[e] == "unclassified"]
    if unclassified:
        intro.append("Not classified: %s — these aired after the published "
                     "filler list's last update, so only the chapter mapping "
                     "covers them." % spans(unclassified))

    section = {"id": sid, "title": run["title"], "sub": sub,
               "links": [link], "items": items}
    if intro:
        section["intro"] = " ".join(intro)
    return section


if __name__ == "__main__":
    main()
