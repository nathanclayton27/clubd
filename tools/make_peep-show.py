#!/usr/bin/env python3
"""Generate properties/peep-show.json — all 54 episodes, nine series.

    python3 tools/make_peep-show.py

Channel 4, September 2003 to December 2015, in the order it went out. Nine
series of six episodes each, which is the whole show: the run is closed, the
series infobox carries an end date rather than "present", and there is nothing
to add later.

WHAT IS IN. The 54 numbered episodes of "List of Peep Show episodes", read from
that article's own {{Episode list}} blocks. Nothing is re-ordered, nothing is
merged, and nothing is invented — every title, number and airdate on a row came
out of that table.

WHAT IS OUT. Nothing, which is the pleasant part of a finite show: the article
carries no specials, no webisodes, no film and no unnumbered entries, and
main() asserts that by requiring exactly 54 blocks across exactly nine series
headings and refusing any block without a number.

WEIGHTS. None. Wikipedia documents running time once, for the series, as a
range — "23–27 minutes" in the television infobox — and not one {{Episode
list}} block on the list article carries a RunTime or Length field. main()
checks both before writing. There is therefore no verifiable per-row figure to
weight with, and a part-weighted list is worse than an unweighted one: the
reader resolves `WEIGHT = x.w >= 0 ? x.w : 1`, so a row with no `w` on an
otherwise weighted list silently counts as a full hour. It is all rows or none,
and here it is none.

Everything is machine-read from the cached Wikipedia wikitext in
scratch/britcoms/ — "List of Peep Show episodes" and the series article. Before
anything is written: each series' count is asserted against that series'
episodesN in the list article's own {{Series overview}}; in-series numbering is
asserted to run 1..6 in every series; the overall numbering is asserted
contiguous 1..54; airdates are asserted non-decreasing within each series and
across the run; the series infobox's num_episodes, num_series and closed end
date are asserted to agree with what was parsed; and the accent pair is
asserted unused by any other property.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki  # noqa: E402

SLUG = "peep-show"
CACHE = prop.ROOT / "scratch" / "britcoms"
LIST_PAGE = "List of Peep Show episodes"
SERIES_PAGE = "Peep Show (British TV series)"
SERIES = list(range(1, 10))

TOTAL = 54          # asserted three ways below
PER_SERIES = 6

ACCENT = "#0C662D"      # the list article's own series 1 colour
ACCENT_DARK = "#7FD79B"

# A sentence only where the source supports one and a reader gains something.
# Everything else is a series of the show and says so by existing.
INTRO = {
    1: "Six episodes from 2003, filmed almost entirely from the characters' "
       "own eyes with their thoughts on the soundtrack — the device the show "
       "never drops.",
    9: "The final series, as the source calls it. The last episode went out "
       "in December 2015 and nothing has followed it.",
}


def text(page):
    t = wiki.wikitext(page, cache_dir=CACHE)
    assert t, "no wikitext for %r" % page
    return t


def template(t, name):
    """The full source of the first {{name ...}} in t, brace-balanced."""
    start = t.index("{{" + name)
    depth, i = 0, start
    while i < len(t) - 1:
        if t[i:i + 2] == "{{":
            depth, i = depth + 1, i + 2
        elif t[i:i + 2] == "}}":
            depth, i = depth - 1, i + 2
            if depth == 0:
                return t[start:i]
        else:
            i += 1
    raise AssertionError("{{%s}} is never closed" % name)


def series_overview(list_text):
    """{series number: episode count} from the list article's own table."""
    seg = template(list_text, "Series overview")
    counts = {int(m.group(1)): int(m.group(2)) for m in
              re.finditer(r"\|\s*episodes(\d+)\s*=\s*(\d+)", seg)}
    assert counts, "series overview carries no episode counts"
    assert sorted(counts) == SERIES, \
        "series overview lists %s, expected %s" % (sorted(counts), SERIES)
    return counts


def field(block, name):
    m = re.search(r"\|\s*%s\s*=\s*(.*?)(?=\n\s*\||\Z)" % name, block, re.S)
    return m.group(1).strip() if m else ""


def _date(kind, v):
    """(y, m, d) from a {{Start date}} / {{End date}}, whose df= flag may come
    first or last. Always applied to a NAMED field: Blackadder's tables carry a
    filming date above the airdate, and "the first date in the block" dated a
    whole series three months early there."""
    m = re.search(r"\{\{%s\s*\|([^}]*)\}\}" % kind, v or "", re.I)
    if not m:
        return None
    nums = [int(a.strip()) for a in m.group(1).split("|") if a.strip().isdigit()]
    assert len(nums) >= 3, "incomplete %s date %r" % (kind, v[:60])
    return tuple(nums[:3])


def airdate(block):
    d = _date("Start date", field(block, "OriginalAirDate"))
    assert d, "no OriginalAirDate in %r" % block[:80]
    return d


def end_date(field_value):
    return _date("End date", field_value)


def year_span(years):
    a, b = min(years), max(years)
    if a == b:
        return str(a)
    return "%d–%02d" % (a, b % 100) if a // 100 == b // 100 else "%d–%d" % (a, b)


def accent_is_unused(pair):
    """No other property may already use either half of this accent pair —
    qa_lint fails the sweep on a duplicate, so find out here instead."""
    for f in sorted((prop.ROOT / "properties").glob("*.json")):
        if f.stem in (SLUG, "index", "search"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(d, dict):
            continue
        assert d.get("accent") != pair[0] and d.get("accentDark") != pair[1], \
            "%s already uses half of %s" % (f.stem, pair)


def read_series(list_text):
    """{series number: [(overall, in_series, title, (y, m, d))]} from the
    list article's own episode tables, split on its series headings."""
    body = list_text[list_text.index("==Episodes=="):]
    body = body[:body.index("\n==References==")]
    parts = re.split(r"\n===\s*Series (\d+) \((\d{4})\)\s*===", body)
    heads = [(int(parts[i]), int(parts[i + 1])) for i in range(1, len(parts), 3)]
    assert [n for n, _ in heads] == SERIES, \
        "series headings are %s, expected %s" % (heads, SERIES)

    out = {}
    for idx, (n, _year) in enumerate(heads):
        seg = parts[3 + idx * 3]
        rows = []
        for overall, in_series, title, _y, block in wiki.episodes(seg):
            assert title, "series %d has an episode block with no title" % n
            assert overall and in_series, \
                "series %d row %r is unnumbered" % (n, title)
            assert not re.search(r"\|\s*(?:RunTime|Runtime|Length)\s*=", block), \
                "series %d row %r now carries a runtime — the no-weights " \
                "reasoning needs revisiting" % (n, title)
            rows.append((overall, in_series, title, airdate(block)))
        assert [r[1] for r in rows] == list(range(1, len(rows) + 1)), \
            "series %d in-series numbering is not 1..%d" % (n, len(rows))
        dates = [r[3] for r in rows]
        assert dates == sorted(dates), \
            "series %d airdates are not in broadcast order" % n
        out[n] = rows
    return out


def main():
    accent_is_unused((ACCENT, ACCENT_DARK))

    list_text = text(LIST_PAGE)
    overview = series_overview(list_text)
    series = read_series(list_text)

    # 1. every series' count against the article's own overview table
    for n in SERIES:
        assert len(series[n]) == overview[n] == PER_SERIES, \
            "series %d: parsed %d rows, overview says %d" \
            % (n, len(series[n]), overview[n])

    # 2. the overall numbering must run 1..54 unbroken or a series is missing
    everything = [r[0] for n in SERIES for r in series[n]]
    assert everything == list(range(1, TOTAL + 1)), \
        "overall episode numbering is not contiguous 1..%d" % TOTAL

    # 3. broadcast order across the whole run, not just inside a series
    dates = [r[3] for n in SERIES for r in series[n]]
    assert dates == sorted(dates), "the run is not in broadcast order"

    # 4. the series article counts the show independently of the list article,
    #    and its closed end date is what makes "finite" a fact rather than a
    #    claim — a show still running would need a different note
    series_text = text(SERIES_PAGE)
    ib = wiki.infobox(series_text, kind="television")
    assert ib, "no television infobox on the series article"
    # the one claim in the notes that is not arithmetic, checked against the
    # sentence it came from rather than trusted
    assert "longest-running comedy in Channel 4 history" in series_text, \
        "the series article no longer makes the Channel 4 longevity claim"
    assert "final series" in series_text, \
        "the series article no longer calls series 9 the final series"
    assert ib("num_episodes").strip() == str(TOTAL), \
        "series infobox says %r episodes, parsed %d" % (ib("num_episodes"), TOTAL)
    assert ib("num_series").strip() == str(len(SERIES)), \
        "series infobox says %r series, parsed %d" % (ib("num_series"),
                                                      len(SERIES))
    end = end_date(ib("last_aired"))
    assert end, "the series infobox has no closed end date: %r" % ib("last_aired")
    assert dates[-1] == end, \
        "the infobox ends the show on %s but the last episode aired %s" \
        % (end, dates[-1])
    # one runtime for the whole show, given as a range — half the reason no
    # row carries a weight; the other half is checked per block above
    assert re.fullmatch(r"\d+–\d+ minutes", ib("runtime").strip()), \
        "series runtime is no longer a single series-level range: %r" \
        % ib("runtime")

    sections = []
    for n in SERIES:
        rows = series[n]
        sections.append({
            "id": "s%d" % n,
            "title": "Series %d" % n,
            "sub": prop.join_bits(year_span([r[3][0] for r in rows]),
                                  "%d episodes" % len(rows)),
            "items": [{"id": "ps-s%de%d" % (n, r[1]), "t": r[2],
                       "n": str(r[1])} for r in rows],
        })
        if n in INTRO:
            sections[-1]["intro"] = INTRO[n]
    sections[0]["open"] = True

    total = sum(len(s["items"]) for s in sections)
    assert total == TOTAL, total
    assert sum(1 for s in sections for x in s["items"] if "w" in x) == 0, \
        "a weight crept in — this list is unweighted end to end"

    p = {
        "slug": SLUG,
        "title": "Peep Show",
        "subtitle": "all nine series, in broadcast order",
        "kind": "tv",
        "popularity": 58,
        "year": "2003–15",
        "blurb": "All 54 episodes in broadcast order — nine series of Mark "
                 "and Jeremy, filmed from behind their eyes, finished and not "
                 "coming back.",
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ["Nine series, and that is the whole show.", "Channel 4 ran it "
             "from September 2003 to December 2015 and it ended on its own "
             "terms. Six episodes a series, no specials, no film, nothing "
             "unaired — the source article carries 54 numbered episodes and "
             "nothing else, and this list is those 54."],
            ["Nothing is weighted.", "Wikipedia documents one running time for "
             "the series — 23 to 27 minutes — and no episode carries its own, "
             "so there is no verifiable per-row figure and every episode "
             "counts one. A part-weighted list is worse than an unweighted "
             "one: a row with no weight would silently count as a full hour."],
            ["Channel 4's longest-running comedy, by years on air.", "The "
             "source records it taking that title in 2010 — nine series spread "
             "across twelve years, with long gaps between them rather than a "
             "heavy episode count."],
            ["No episode notes.", "The titles are the source's titles and "
             "nothing here describes what happens in an episode. This is a "
             "show of running jokes and slow disasters and a one-line summary "
             "gives them away."],
            "Titles, numbering and airdates machine-read from Wikipedia's "
            "List of Peep Show episodes; every series' count is asserted "
            "against the article's own series overview, the overall numbering "
            "asserted contiguous, the airdates asserted in broadcast order, "
            "and the total cross-checked against the series infobox before "
            "this builds.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d episodes in %d series" % (out.name, total, len(sections)))
    for s in sections:
        print("   %-10s %3d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
