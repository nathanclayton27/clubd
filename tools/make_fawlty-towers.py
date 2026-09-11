#!/usr/bin/env python3
"""Generate properties/fawlty-towers.json — all twelve, and there are only twelve.

    python3 tools/make_fawlty-towers.py

Two series on BBC Two, three and a half years apart: six episodes in the autumn
of 1975 and six in 1979. Twelve rows, which is the entire show — the series
infobox gives num_episodes = 12 with a closed end date, and main() asserts both.

THE GAP IS THREE AND A HALF YEARS, AND ONLY THAT NUMBER GOES IN THE COPY. The
article gives two intervals for two different things: "The second series was
transmitted three-and-a-half years later", and, in a parenthesis about Connie
Booth's reluctance, "the four-year gap between productions". These rows are
airdates, so the transmission figure is the one that matches what a reader is
looking at, and the blurb, the note and the series 2 intro all use it. Carrying
"four years" beside twelve broadcast dates was the earlier version of this file.

THE SOURCE IS THE SERIES ARTICLE. Fawlty Towers has no "List of ... episodes"
page; its twelve {{Episode list}} blocks sit in the "Episodes" section of the
"Fawlty Towers" article, under two series headings, numbered 1–12 straight
through with no in-series numbering at all. So the rows carry the overall
number, which is the only number the encyclopedia gives them.

THE SIGN GAG IS THE ROW NOTE. Every episode's title sequence shows the hotel
sign rearranged — WATERY FOWLS, FLOWERY TWATS — and the source table carries
them in an aux column headed "Sign reads". They are machine-read from that
column, tags stripped, and printed as the note. Exactly one episode has no sign:
the source gives "None" for "The Germans", with a footnote explaining its titles
were shot somewhere else. main() asserts that there is exactly one such row, so
a note going missing later is a failure rather than a silent gap.

WHAT IS OUT. Nothing exists to leave out, which is the whole appeal of this
list. The article discusses a rumoured thirteenth episode — long rumoured, no
concrete evidence, per the source — and a feature-length special Cleese thought
about in the 1990s and never wrote. Neither is a row; both are named in the
notes, because a reader who has heard the rumour deserves an answer rather than
a gap. main() asserts the source still describes the thirteenth as unevidenced.

WEIGHTS. None. The television infobox documents running time once, for the
series, as "30–40 minutes", and not one {{Episode list}} block carries a RunTime
or Length field — main() checks both. There is no verifiable per-row figure, and
a part-weighted list is worse than an unweighted one: the reader resolves
`WEIGHT = x.w >= 0 ? x.w : 1`, so a row with no `w` on an otherwise weighted
list silently counts as a full hour. Twelve rows, twelve equal marks.

Everything is machine-read from the cached Wikipedia wikitext in
scratch/britcoms/ — the "Fawlty Towers" article alone. Before anything is
written: each series' count is asserted against that series' episodesN in the
article's own {{Series overview}}; the numbering is asserted contiguous 1..12
across the two series; airdates are asserted non-decreasing inside each series
and across the run; the infobox's num_episodes, num_series and closed end date
are asserted to agree with what was parsed; and the accent pair is asserted
unused by any other property.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki  # noqa: E402

SLUG = "fawlty-towers"
CACHE = prop.ROOT / "scratch" / "britcoms"
PAGE = "Fawlty Towers"
SERIES = [1, 2]
TOTAL = 12
PER_SERIES = 6

ACCENT = "#8C6239"
ACCENT_DARK = "#DEAF77"      # the article's own series 1 colour

INTRO = {
    1: "Six episodes in the autumn of 1975, written by John Cleese and Connie "
       "Booth after the Pythons stayed at a Torquay hotel whose owner the "
       "source credits as the original Basil.",
    2: "Transmitted three and a half years later, the source says, and that is "
       "the last of it. Cleese and Booth stopped at twelve; the source notes "
       "other writers have cited that decision since.",
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


def field(block, name):
    m = re.search(r"\|\s*%s\s*=\s*(.*?)(?=\n\s*\||\Z)" % name, block, re.S)
    return m.group(1).strip() if m else ""


def _date(kind, v):
    """(y, m, d) from a {{Start date}} / {{End date}}, df= flag anywhere.

    Always applied to a NAMED field: episode tables elsewhere in this project
    carry a filming date above the airdate, and "the first date in the block"
    dated a whole series three months early there."""
    m = re.search(r"\{\{%s\s*\|([^}]*)\}\}" % kind, v or "", re.I)
    if not m:
        return None
    nums = [int(a.strip()) for a in m.group(1).split("|") if a.strip().isdigit()]
    assert len(nums) >= 3, "incomplete %s date %r" % (kind, v[:60])
    return tuple(nums[:3])


def sign(block):
    """The "Sign reads" column, as display text, or None where the source
    records no sign at all.

    wiki.clean leaves two things behind that matter here: bold markup is three
    apostrophes and it only strips pairs, and <small> is an HTML tag it never
    touches. Both are inside every value in this column."""
    raw = field(block, "Aux1")
    if not raw:
        return None
    txt = wiki.clean(re.sub(r"</?small>", "", raw.replace("'''", "")))
    txt = re.sub(r"\s+", " ", txt).strip()
    return None if txt.lower().startswith("none") else txt


def series_overview(t):
    seg = template(t, "Series overview")
    counts = {int(m.group(1)): int(m.group(2)) for m in
              re.finditer(r"\|\s*episodes(\d+)\s*=\s*(\d+)", seg)}
    assert sorted(counts) == SERIES, \
        "series overview lists %s, expected %s" % (sorted(counts), SERIES)
    return counts


def year_span(years):
    a, b = min(years), max(years)
    return str(a) if a == b else "%d–%02d" % (a, b % 100)


def accent_is_unused(pair):
    for f in sorted((prop.ROOT / "properties").glob("*.json")):
        if f.stem in (SLUG, "index", "search"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(d, dict):
            continue
        assert d.get("accent") != pair[0] and d.get("accentDark") != pair[1], \
            "%s already uses half of %s" % (f.stem, pair)


def read_series(t):
    """{series: [(number, title, (y, m, d), sign or None)]}."""
    body = t[t.index("==Episodes=="):t.index("==Reception==")]
    parts = re.split(r"\n===\s*Series (\d+) \((\d{4})\)\s*===", body)
    heads = [int(parts[i]) for i in range(1, len(parts), 3)]
    assert heads == SERIES, "series headings are %s, expected %s" % (heads, SERIES)

    out = {}
    for idx, n in enumerate(heads):
        seg = parts[3 + idx * 3]
        rows = []
        for number, in_series, title, _y, blk in wiki.episodes(seg):
            assert title, "series %d has an episode block with no title" % n
            assert number, "series %d row %r is unnumbered" % (n, title)
            # the table numbers 1..12 straight through and gives no in-series
            # number; if that ever changes, the `n` on every row is wrong
            assert in_series is None, \
                "the source now carries an in-series number for %r" % title
            assert not re.search(r"\|\s*(?:RunTime|Runtime|Length)\s*=", blk), \
                "row %r now carries a runtime — the no-weights reasoning " \
                "needs revisiting" % title
            d = _date("Start date", field(blk, "OriginalAirDate"))
            assert d, "row %r has no airdate" % title
            rows.append((number, title, d, sign(blk)))
        dates = [r[2] for r in rows]
        assert dates == sorted(dates), \
            "series %d is not in broadcast order" % n
        out[n] = rows
    return out


def main():
    accent_is_unused((ACCENT, ACCENT_DARK))

    t = text(PAGE)
    overview = series_overview(t)
    series = read_series(t)

    # 1. each series against the article's own overview table
    for n in SERIES:
        assert len(series[n]) == overview[n] == PER_SERIES, \
            "series %d: parsed %d rows, overview says %d" \
            % (n, len(series[n]), overview[n])

    # 2. one unbroken numbering across both series, which is what the source
    #    gives and therefore what the rows can show
    numbering = [r[0] for n in SERIES for r in series[n]]
    assert numbering == list(range(1, TOTAL + 1)), \
        "the numbering is not contiguous 1..%d" % TOTAL

    # 3. broadcast order across the whole run, not just inside a series
    dates = [r[2] for n in SERIES for r in series[n]]
    assert dates == sorted(dates), "the run is not in broadcast order"

    # 4. exactly one episode without a sign — the note promises that, and a
    #    quietly dropped aux column would otherwise look like eleven gags
    signless = [r[1] for n in SERIES for r in series[n] if not r[3]]
    assert signless == ["The Germans"], \
        "episodes with no sign in the source are now %s" % signless

    # 5. the infobox counts the show independently, and its closed end date is
    #    what makes "twelve and no more" a fact rather than a claim
    ib = wiki.infobox(t, kind="television")
    assert ib, "no television infobox on the article"
    assert ib("num_episodes").strip() == str(TOTAL), \
        "infobox says %r episodes, parsed %d" % (ib("num_episodes"), TOTAL)
    assert ib("num_series").strip() == str(len(SERIES)), \
        "infobox says %r series, parsed %d" % (ib("num_series"), len(SERIES))
    end = _date("End date", ib("last_aired"))
    assert end and dates[-1] == end, \
        "infobox ends the show on %s but the last episode aired %s" \
        % (end, dates[-1])
    # one runtime for the whole show, given as a range — half the reason no row
    # carries a weight; the other half is checked per block above
    assert re.fullmatch(r"\d+–\d+ minutes", ib("runtime").strip()), \
        "the runtime is no longer a single series-level range: %r" % ib("runtime")

    # 6. the claims the notes make that are not arithmetic, checked against the
    #    sentences they came from
    for phrase in ("It has long been rumoured that a 13th episode",
                   "no concrete evidence",
                   "the individual episodes had no on-screen titles",
                   "to quit before a third series",
                   "Gleneagles Hotel",
                   # the gap, in the source's own words. The article also says
                   # "four-year gap between productions" a few paragraphs on;
                   # these rows are airdates, so this is the sentence the copy
                   # uses, and it uses one number and not both
                   "The second series was transmitted three-and-a-half years "
                   "later"):
        assert phrase in t, "the article no longer says %r" % phrase

    sections = []
    for n in SERIES:
        rows = series[n]
        items = []
        for number, title, _d, sgn in rows:
            row = {"id": "ft-%d" % number, "t": title, "n": str(number)}
            if sgn:
                row["note"] = "Sign reads: %s" % sgn
            items.append(row)
        sections.append({
            "id": "s%d" % n,
            "title": "Series %d" % n,
            "sub": prop.join_bits(year_span([r[2][0] for r in rows]),
                                  "%d episodes" % len(rows)),
            "intro": INTRO[n],
            "items": items,
        })
    sections[0]["open"] = True

    total = sum(len(s["items"]) for s in sections)
    assert total == TOTAL, total
    assert sum(1 for s in sections for x in s["items"] if "w" in x) == 0, \
        "a weight crept in — this list is unweighted end to end"
    assert all(x.get("n") for s in sections for x in s["items"]), \
        "a row has no number — the card would print the word undefined"

    p = {
        "slug": SLUG,
        "title": "Fawlty Towers",
        "subtitle": "twelve episodes, two series, 1975 and 1979",
        "kind": "tv",
        "popularity": 64,
        "year": "1975–79",
        "blurb": "All twelve episodes in broadcast order — two series three "
                 "and a half years apart, and Cleese and Booth stopped there.",
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ["Twelve, and there is no thirteenth.", "Two series of six, the "
             "second transmitted three and a half years after the first, and "
             "that is the whole show. The source records a "
             "long-rumoured thirteenth episode with no concrete evidence "
             "behind it, and a feature-length special Cleese considered in the "
             "1990s and never wrote. Neither is a row here."],
            ["The sign gag is on every row that has one.", "The title sequence "
             "rearranges the hotel sign each week and the source table records "
             "what it reads. Those are the row notes, printed from that column. "
             "One episode has none: the source gives \"None\" for The Germans, "
             "whose titles were not shot at the hotel."],
            ["The titles came later than the episodes.", "The source notes the "
             "episodes had no on-screen titles when they went out — the names "
             "everyone uses were first printed on the 1980s VHS releases, and "
             "some early audio releases used different ones again. The titles "
             "here are the ones the encyclopedia files them under."],
            ["Numbered 1 to 12, because the source is.", "The article's "
             "episode table numbers the run straight through and gives no "
             "per-series number, so the rows carry the only number there is. "
             "The series headings still say which six are which."],
            ["Nothing is weighted.", "One running time is documented for the "
             "series — 30 to 40 minutes — and no episode carries its own, so "
             "there is no verifiable per-row figure and every episode counts "
             "one. A part-weighted list is worse: a row with no weight would "
             "silently count as a full hour."],
            "Titles, numbering, airdates and sign gags machine-read from the "
            "Wikipedia article's own episode tables; each series' count is "
            "asserted against the article's series overview, the numbering "
            "asserted contiguous 1–12, the airdates asserted in broadcast "
            "order, and the total cross-checked against the infobox before "
            "this builds.",
        ],
        "sections": sections,
    }

    # one number for the gap, and it is the transmission one. The article's
    # other figure — "the four-year gap between productions" — is about when
    # they were made, not when they went out, and this list is airdates.
    copy = json.dumps(p, ensure_ascii=False)
    assert "four years" not in copy and "four-year" not in copy, \
        "the copy has gone back to the four-year production gap; the rows are " \
        "airdates and the source's transmission figure is three and a half years"
    assert copy.count("three and a half years") == 3, \
        "expected the transmission gap in the blurb, note 1 and series 2's " \
        "intro, found %d mentions" % copy.count("three and a half years")

    out = prop.write(p)
    print("wrote %s — %d episodes in %d series" % (out.name, total, len(sections)))
    for s in sections:
        print("   %-10s %3d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
