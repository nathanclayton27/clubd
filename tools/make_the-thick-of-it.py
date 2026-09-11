#!/usr/bin/env python3
"""Generate properties/the-thick-of-it.json — all 23 episodes, specials included.

    python3 tools/make_the-thick-of-it.py

BBC Four then BBC Two, May 2005 to October 2012, in the order it went out: four
series and the two hour-long 2007 specials, which sit between series 2 and
series 3 because that is when they aired.

THE SPECIALS ARE EPISODES HERE, and the source decides that rather than me.
"List of The Thick of It episodes" numbers "The Rise of the Nutters" and
"Spinners and Losers" as 7 and 8 of the run, its {{Series overview}} gives them
their own two-episode block between series 2 and 3, and the series article's
infobox counts 23 episodes — 3 + 3 + 2 + 8 + 7. Dropping them would contradict
the count on the page they came from, so they are rows, in their own section,
where they went out.

WHAT IS OUT, AND WHY.

  * "Opposition Extra", the 15-minute Red Button mini-episode that followed
    "Spinners and Losers". The source's own table gives it "–" for both episode
    numbers, so it is outside the 23, and main() asserts that every row it
    writes carries a number rather than filtering by name.
  * The eight "Out of The Thick of It" webisodes. Different table, filed under
    "Other media", numbered 1-8 in their own sequence, ten minutes each of
    deleted scenes and interviews.
  * "In the Loop" (2009), a spin-off film with its own article, different roles
    for most of the cast, and no episode number.

EPISODE TITLES, OR THE LACK OF THEM. Nineteen of the 23 went out untitled. The
source labels them "Series N – Episode M" and those labels are printed exactly
as it gives them; inventing titles is the one thing this generator must not do.
The two specials have real titles and carry them.

WEIGHTS. None. The series article documents running time once, as "29 minutes",
and not one {{Episode list}} block carries a RunTime or Length field — main()
checks both. Two of the rows are hour-long specials and the list article says a
series 4 episode was hour-long too without saying which, so there is no
verifiable per-row figure to weight with and a part-weighted list is worse than
an unweighted one: a row with no `w` on an otherwise weighted list silently
counts as a full hour. Every row counts one, and the notes say so.

Everything is machine-read from the cached Wikipedia wikitext in
scratch/britcoms/ — "List of The Thick of It episodes" and "The Thick of It".
Before anything is written: each section's count is asserted against that
block's own episodesN in the list article's {{Series overview}}; in-series
numbering is asserted to run 1..N inside every section; the overall numbering is
asserted contiguous 1..23; airdates are asserted non-decreasing within every
section and across the run, which is what puts the specials between series 2 and
3 rather than at the end; the series infobox's num_episodes, num_series and
closed end date are asserted to agree; and the accent pair is asserted unused by
any other property.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki  # noqa: E402

SLUG = "the-thick-of-it"
CACHE = prop.ROOT / "scratch" / "britcoms"
LIST_PAGE = "List of The Thick of It episodes"
SERIES_PAGE = "The Thick of It"

TOTAL = 23      # asserted against the overview and the series infobox
# (heading in the source, overview key, section id, section title)
BLOCKS = [
    ("Series 1 (2005)", "1", "s1", "Series 1"),
    ("Series 2 (2005)", "2", "s2", "Series 2"),
    ("Specials (2007)", "2S", "specials", "The 2007 specials"),
    ("Series 3 (2009)", "3", "s3", "Series 3"),
    ("Series 4 (2012)", "4", "s4", "Series 4"),
]
ID_PREFIX = {"s1": "toi-s1e", "s2": "toi-s2e", "specials": "toi-sp",
             "s3": "toi-s3e", "s4": "toi-s4e"}

ACCENT = "#3C5A99"
ACCENT_DARK = "#9FB6E8"

INTRO = {
    "s1": "Three episodes on BBC Four in May 2005, with a further three that "
          "October; the DVD calls all six the first series and the source "
          "keeps them as two.",
    "specials": "Two hour-long specials in 2007, made around a change of "
                "prime minister. The source numbers them 7 and 8 of the run "
                "and they sit here where they aired, between series 2 and 3.",
    "s3": "The move to BBC Two, eight episodes in 2009, and the series that "
          "put the word omnishambles into circulation.",
    "s4": "Seven episodes in 2012, made after four years off. The source says "
          "one of them ran an hour without saying which.",
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
    """{overview key: episode count} — keys are "1", "2", "2S", "3", "4", the
    specials block included, which is the source counting them as episodes."""
    seg = template(list_text, "Series overview")
    counts = {m.group(1): int(m.group(2)) for m in
              re.finditer(r"\|\s*episodes(\d+S?)\s*=\s*(\d+)", seg)}
    assert counts, "series overview carries no episode counts"
    assert sorted(counts) == sorted(k for _, k, _, _ in BLOCKS), \
        "series overview lists %s, expected %s" \
        % (sorted(counts), sorted(k for _, k, _, _ in BLOCKS))
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


def end_date(v):
    return _date("End date", v)


def year_span(years):
    a, b = min(years), max(years)
    if a == b:
        return str(a)
    return "%d–%02d" % (a, b % 100) if a // 100 == b // 100 else "%d–%d" % (a, b)


def accent_is_unused(pair):
    for f in sorted((prop.ROOT / "properties").glob("*.json")):
        if f.stem in (SLUG, "index", "search"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(d, dict):
            continue
        assert d.get("accent") != pair[0] and d.get("accentDark") != pair[1], \
            "%s already uses half of %s" % (f.stem, pair)


def read_blocks(list_text):
    """{section id: [(overall, in_block, title, (y, m, d))]}, numbered rows
    only — the unnumbered mini-episode is dropped by the number test, not by
    its name."""
    body = list_text[list_text.index("==Episodes=="):
                     list_text.index("==Other media==")]
    parts = re.split(r"\n===\s*([^=\n]+?)\s*===", body)
    heads = [parts[i] for i in range(1, len(parts), 2)]
    assert heads == [h for h, _, _, _ in BLOCKS], \
        "the source's episode headings are %s, expected %s" \
        % (heads, [h for h, _, _, _ in BLOCKS])

    out, dropped = {}, []
    for idx, (_head, _key, sid, _title) in enumerate(BLOCKS):
        seg = parts[2 + idx * 2]
        rows = []
        for overall, in_block, title, _y, blk in wiki.episodes(seg):
            assert title, "%s has an episode block with no title" % sid
            assert not re.search(r"\|\s*(?:RunTime|Runtime|Length)\s*=", blk), \
                "%s row %r now carries a runtime — the no-weights reasoning " \
                "needs revisiting" % (sid, title)
            if overall is None or in_block is None:
                dropped.append(title)
                continue
            rows.append((overall, in_block, title, airdate(blk)))
        assert [r[1] for r in rows] == list(range(1, len(rows) + 1)), \
            "%s numbering is not 1..%d" % (sid, len(rows))
        dates = [r[3] for r in rows]
        assert dates == sorted(dates), "%s is not in broadcast order" % sid
        out[sid] = rows

    # exactly one unnumbered entry, and it is the Red Button mini-episode the
    # docstring says is excluded. A second one appearing means the source has
    # changed and the exclusion needs rereading rather than widening.
    assert dropped == ["Opposition Extra"], \
        "unnumbered entries in the source are now %s" % dropped
    return out


def main():
    accent_is_unused((ACCENT, ACCENT_DARK))

    list_text = text(LIST_PAGE)
    overview = series_overview(list_text)
    blocks = read_blocks(list_text)

    # 1. every section's count against the article's own overview table
    for _head, key, sid, _title in BLOCKS:
        assert len(blocks[sid]) == overview[key], \
            "%s: parsed %d rows, overview says %d" \
            % (sid, len(blocks[sid]), overview[key])

    # 2. the overall numbering must run 1..23 unbroken, which is also the check
    #    that the specials belong to the run rather than sitting beside it
    everything = [r[0] for _h, _k, sid, _t in BLOCKS for r in blocks[sid]]
    assert everything == list(range(1, TOTAL + 1)), \
        "overall episode numbering is not contiguous 1..%d" % TOTAL

    # 3. broadcast order across the whole list, sections included
    dates = [r[3] for _h, _k, sid, _t in BLOCKS for r in blocks[sid]]
    assert dates == sorted(dates), "the list is not in broadcast order"

    # 4. the series article counts the run independently, and its closed end
    #    date is what makes "finished" a fact rather than a claim
    ib = wiki.infobox(text(SERIES_PAGE), kind="television")
    assert ib, "no television infobox on the series article"
    assert ib("num_episodes").strip() == str(TOTAL), \
        "series infobox says %r episodes, parsed %d" % (ib("num_episodes"), TOTAL)
    assert ib("num_series").strip() == "4", \
        "series infobox says %r series, expected 4" % ib("num_series")
    end = end_date(ib("last_aired"))
    assert end and dates[-1] == end, \
        "infobox ends the show on %s, last row aired %s" % (end, dates[-1])
    # one runtime for the whole show and none per episode — the reason no row
    # carries a weight, checked rather than asserted in prose
    assert re.fullmatch(r"\d+ minutes", ib("runtime").strip()), \
        "series runtime is no longer a single series-level figure: %r" \
        % ib("runtime")
    # the three claims the section intros make that are not arithmetic,
    # checked against the sentences they came from rather than trusted
    assert "one of which was an hour long" in list_text, \
        "the list article no longer says a series 4 episode ran an hour"
    assert "The Complete First Series" in list_text, \
        "the list article no longer says the DVD calls all six the first series"
    assert "omnishambles" in list_text, \
        "the list article no longer records the omnishambles episode"

    sections = []
    for _head, _key, sid, title in BLOCKS:
        rows = blocks[sid]
        unit = ("hour-long specials" if sid == "specials" else "episodes")
        sections.append({
            "id": sid,
            "title": title,
            "sub": prop.join_bits(year_span([r[3][0] for r in rows]),
                                  "%d %s" % (len(rows), unit)),
            "items": [{"id": ID_PREFIX[sid] + str(r[1]), "t": r[2],
                       "n": str(r[1])} for r in rows],
        })
        if sid in INTRO:
            sections[-1]["intro"] = INTRO[sid]
    sections[0]["open"] = True

    total = sum(len(s["items"]) for s in sections)
    assert total == TOTAL, total
    assert sum(1 for s in sections for x in s["items"] if "w" in x) == 0, \
        "a weight crept in — this list is unweighted end to end"

    p = {
        "slug": SLUG,
        "title": "The Thick of It",
        "subtitle": "four series and the two 2007 specials",
        "kind": "tv",
        "popularity": 54,
        "year": "2005–12",
        "blurb": "Everything the source counts as an episode, in broadcast "
                 "order — four series of ministerial damage control, and the "
                 "two hour-long specials where they aired.",
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ["The specials are part of the run.", "Wikipedia numbers The Rise "
             "of the Nutters and Spinners and Losers as episodes 7 and 8, "
             "gives them their own block in the series overview between series "
             "2 and 3, and counts 23 episodes in total. They are rows here, in "
             "their own section, in the place they went out — not extras "
             "parked at the end."],
            ["The mini-episode and the webisodes are not.", "Opposition "
             "Extra, the 15-minute Red Button follow-on to Spinners and "
             "Losers, carries no episode number in the source's table, and the "
             "eight Out of The Thick of It webisodes are a separate table "
             "under Other media. In the Loop is a film with its own article "
             "and most of the cast in different roles. None of the three is in "
             "the 23."],
            ["Most of these episodes have no title.", "They went out "
             "untitled. The source labels them Series N – Episode M and those "
             "labels are printed exactly as it gives them, because the "
             "alternative is making titles up. The two specials have real "
             "titles and keep them."],
            ["Nothing is weighted.", "The source gives one running time for "
             "the series — 29 minutes — and no episode carries its own. Two "
             "rows are hour-long specials and the list article says a series 4 "
             "episode ran an hour too without saying which, so there is no "
             "verifiable per-row figure and every row counts one. A "
             "part-weighted list is worse: a row with no weight would silently "
             "count as a full hour."],
            "Titles, numbering and airdates machine-read from Wikipedia's "
            "List of The Thick of It episodes; every section's count is "
            "asserted against the article's own series overview, the overall "
            "numbering asserted contiguous 1–23, the airdates asserted in "
            "broadcast order across the whole list, and the total "
            "cross-checked against the series infobox before this builds.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d episodes in %d sections" % (out.name, total, len(sections)))
    for s in sections:
        print("   %-20s %3d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
