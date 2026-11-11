#!/usr/bin/env python3
"""Generate properties/bobs-burgers.json — every episode, one row each.

    python3 tools/make_bobs-burgers.py

Sixteen seasons on Fox, January 2011 to May 2026, in the order they went out.
312 rows covering the 313 episodes Wikipedia numbers; the single place those
two numbers part company is "The Bleakening", and it is explained below and
asserted in code rather than quietly absorbed.

WHAT IS IN. Episodes of the television series, and only those: the numbered
run Wikipedia's {{Series overview}} counts, 13 + 9 + 23 + 22 + 21 + 19 + 22 +
21 + 22 + 22 + 22 + 22 + 22 + 16 + 22 + 15. Nothing is re-ordered and nothing
is invented.

WHAT IS OUT, AND WHY.

  * "The Bob's Burgers Movie" (2022). The list article carries it, but under
    its own "Theatrical film" heading and with no episode number — it is not
    in the series overview and not in the infobox's 313. Futurama's four films
    are on this site as film rows because that list's unit is mixed by design
    and the films are the form that work was released in. Here the unit is the
    episode, no row carries a weight, and a cinema feature dropped among
    313 twenty-two-minute episodes would count exactly one, misrepresenting
    both it and them. It is named in the notes instead of being counted.
  * The two shorts, "My Butt Has a Fever" and "On the Fort Day of Christmas".
    Same section of the source, same absence of an episode number. The second
    is a Hulu holiday short dated December 7, 2026; main() asserts that date so
    the note naming it cannot drift.
  * The "Future episodes" table — nineteen titles known from WGA listings and
    writers' social media, with production codes or TBA and no airdate. A row
    on this list has an airdate the encyclopedia stands behind.

THE BLEAKENING IS ONE ROW. Season 8's Christmas special aired on December 10,
2017 as a single hour-long block. Wikipedia numbers it as episodes 6 and 7 of
the season (135 and 136 overall, production codes 7ASA16 and 7ASA17) and
counts it twice in the overview's 21, but gives it ONE title, ONE airdate and
one {{Episode list/sublist}} block with NumParts = 2 — the two halves have no
titles of their own. So the source's own episode table shows one row, and this
list shows one row too, labelled "6–7" and noting the hour. Shipping two rows
would mean inventing two titles, which is the one thing this generator is not
allowed to do. That is 312 rows for 313 numbered episodes; both numbers are
asserted, and the season 8 section says so in its own subtitle.

ORDER. Broadcast, which for this show is the only order there is. Fox has
aired Bob's Burgers out of production order in every single one of its sixteen
seasons — main() proves it rather than claiming it, by checking that no
season's production codes come out sorted — and the production cycles do not
line up with the broadcast seasons either (broadcast season 3 mixes 2ASA and
3ASA codes, season 14 is mostly the thirteenth production cycle). There is no
production ordering to follow that any box set, streaming season or source
article agrees with. Wikipedia's numbering and the airdates, meanwhile, agree
end to end: every season's dates are non-decreasing, and main() asserts it.

SEASON 16 IS FINISHED, AND THERE IS NO SEASON 17 YET. The list article carries
no {{Aired episodes}} stamp, so completeness is established from the articles
themselves: the season 16 infobox gives num_episodes = 15 and a closed
{{End date|2026|5|17}} rather than "present", all fifteen episodes carry a
sourced airdate, the last of them is that date, and the series infobox counts
16 seasons and 313 episodes. Season 17 has no article, no row in the series
overview and no heading on the list page — the show was renewed in April 2025
for four more seasons, through a nineteenth, but a renewal is not an airdate
and nothing unaired is listed here.

WEIGHTS. None, deliberately. Wikipedia documents running time once, for the
series, as a range — "20–23 minutes" in the television infobox — and not a
single {{Episode list}} block in any of the sixteen season articles carries a
RunTime or Length field. main() checks both of those before writing. There is
therefore no verifiable per-row number to weight with, and a half-weighted
list is worse than an unweighted one: the reader resolves
`WEIGHT = x.w >= 0 ? x.w : 1`, so a row with no `w` on an otherwise weighted
list silently counts as a full hour. It is all rows or none. It is none — even
for The Bleakening, whose own article gives 43:47, because one weighted row
among 311 unweighted ones is exactly the bug described.

THE BLURB CARRIES NO COUNT. The card prints the generated total three lines
above it; a hard-coded number in the blurb only survives until the next season
airs, and five other lists already contradict themselves that way. main()
asserts the blurb holds no digits at all.

Everything is machine-read from the cached Wikipedia wikitext in
scratch/bobs-burgers/ — "List of Bob's Burgers episodes", the sixteen season
articles and the series article. Nothing is typed in from memory. Before
anything is written: each season's numbered episode count is asserted against
that season's episodesN in the list article's own {{Series overview}} AND
against that season's own infobox num_episodes; each season's in-season
numbering is asserted to run 1..N; the overall numbering is asserted contiguous
1..313; airdates are asserted non-decreasing inside every season; the series
infobox's num_episodes and num_seasons are asserted to agree; the list page is
asserted to hold no numbered episode blocks of its own (so a generator that
read it instead of the season articles would ship the film and the shorts and
none of the show, which is precisely what it would have done); and the accent
pair is asserted unused by any other property.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki  # noqa: E402

SLUG = "bobs-burgers"
CACHE = prop.ROOT / "scratch" / SLUG
LIST_PAGE = "List of Bob's Burgers episodes"
SERIES_PAGE = "Bob's Burgers"
SEASONS = list(range(1, 17))

TOTAL_EPISODES = 313   # what Wikipedia numbers; asserted four ways below
TOTAL_ROWS = 312       # one fewer: The Bleakening is a single hour-long row

ACCENT = "#B4331C"      # the awning
ACCENT_DARK = "#F2A65A"

# Seasons that need a sentence. Everything else is a season of the show and
# says so by existing. Every claim here is on the cached season article.
INTRO = {
    8: "Its Christmas special, \"The Bleakening\", went out as one hour-long "
       "block on December 10, 2017. Wikipedia numbers it as episodes 6 and 7 "
       "and gives the two halves a single title between them, so it is one "
       "row here rather than two rows with an invented Part 1 and Part 2.",
    14: "Cut from a planned 22 episodes to 16 by the 2023 Writers Guild of "
        "America and SAG-AFTRA strikes, and stretched out until September "
        "2024. Most of it is the thirteenth production cycle.",
    16: "Fox renewed the show in April 2025 for four more seasons, taking it "
        "through a nineteenth. This is the season that carried the 300th "
        "episode.",
}


def text(page):
    t = wiki.wikitext(page, cache_dir=CACHE)
    assert t, "no wikitext for %r" % page
    return t


def airdate(block):
    """The first {{Start date}} in an episode block, as (y, m, d)."""
    m = re.search(r"\{\{Start date\|\s*(\d{4})\s*\|\s*(\d{1,2})\s*\|"
                  r"\s*(\d{1,2})", block)
    assert m, "no airdate in %r" % block[:80]
    return tuple(int(g) for g in m.groups())


def year_span(years):
    a, b = min(years), max(years)
    if a == b:
        return str(a)
    return "%d–%02d" % (a, b % 100) if a // 100 == b // 100 else "%d–%d" % (a, b)


def template(t, name):
    """The full source of the first {{name ...}} in t, brace-balanced.

    Rick and Morty's generator could stop at the first `\\n}}`; this article's
    {{Series overview}} closes on a line that begins with an HTML comment, and
    the naive pattern silently truncated it to season 1."""
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
    """{season number: episode count} from the list article's own table."""
    seg = template(list_text, "Series overview")
    assert seg, "no series overview"
    counts = {int(m.group(1)): int(m.group(2)) for m in
              re.finditer(r"\|\s*episodes(\d+)\s*=\s*(\d+)", seg)}
    assert counts, "series overview carries no episode counts"
    assert sorted(counts) == SEASONS, \
        "series overview lists seasons %s, expected %s" % (sorted(counts),
                                                           SEASONS)
    return counts


def field(block, name):
    m = re.search(r"\|\s*%s\s*=\s*(.*?)(?=\n\s*\||\Z)" % name, block, re.S)
    return m.group(1).strip() if m else ""


def read_season(n):
    """[(overall_nums, in_season_nums, title, (y, m, d), prodcodes)] for one
    season, read from the season's own article.

    A block is usually one episode. A {{Episode list/sublist}} with NumParts
    covers several numbered episodes under one title — season 8's "The
    Bleakening" is the only one in the run — and stays one entry here, with
    every number it covers recorded so the arithmetic still checks out."""
    body = text("Bob's Burgers season %d" % n)
    raw = wiki.episodes(body)
    assert raw, "season %d parsed empty" % n

    rows = []
    for overall, in_season, title, _year, block in raw:
        assert title, "season %d has an episode block with no title" % n
        assert not re.search(r"\|\s*(?:RunTime|Runtime|Length)\s*=", block), \
            "season %d row %r now carries a runtime — the no-weights " \
            "reasoning needs revisiting" % (n, title)
        parts = field(block, "NumParts")
        if parts:
            k = int(parts)
            assert k >= 2, "NumParts=%d on %r" % (k, title)
            overalls, in_seasons, codes = [], [], []
            for p in range(1, k + 1):
                o = field(block, "EpisodeNumber_%d" % p)
                s = field(block, "EpisodeNumber2_%d" % p)
                assert o.isdigit() and s.isdigit(), \
                    "season %d multi-part %r part %d is unnumbered" \
                    % (n, title, p)
                overalls.append(int(o))
                in_seasons.append(int(s))
                codes.append(field(block, "ProdCode_%d" % p))
            # a multi-part block must cover consecutive numbers or the
            # "one row, several numbers" label would be a lie
            assert in_seasons == list(range(in_seasons[0],
                                            in_seasons[0] + k)), in_seasons
            assert overalls == list(range(overalls[0],
                                          overalls[0] + k)), overalls
        else:
            assert overall and in_season, \
                "season %d row %r is unnumbered" % (n, title)
            overalls, in_seasons = [overall], [in_season]
            codes = [field(block, "ProdCode")]
        rows.append((overalls, in_seasons, title, airdate(block), codes))

    numbered = [x for r in rows for x in r[1]]
    assert numbered == list(range(1, len(numbered) + 1)), \
        "season %d in-season numbering is not 1..%d" % (n, len(numbered))
    dates = [r[3] for r in rows]
    assert dates == sorted(dates), \
        "season %d airdates are not in broadcast order" % n

    # the season's own infobox is a second, independent count
    ib = wiki.infobox(body, kind="television season")
    assert ib, "no season infobox on the season %d article" % n
    ep = re.search(r"\d+", ib("num_episodes"))
    assert ep and int(ep.group(0)) == len(numbered), \
        "season %d infobox says %r episodes, parsed %d" \
        % (n, ib("num_episodes"), len(numbered))
    return rows, ib


def accent_is_unused(pair):
    """No other property may already use this exact accent pair — qa_lint
    fails the sweep on a duplicate, so find out here instead."""
    for f in sorted((prop.ROOT / "properties").glob("*.json")):
        if f.stem in (SLUG, "index", "search"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(d, dict):
            continue
        assert (d.get("accent"), d.get("accentDark")) != pair, \
            "accent pair %s is already %s's" % (pair, f.stem)
        assert d.get("accent") != pair[0] and d.get("accentDark") != pair[1], \
            "%s already uses half of %s" % (f.stem, pair)


def main():
    accent_is_unused((ACCENT, ACCENT_DARK))

    list_text = text(LIST_PAGE)
    overview = series_overview(list_text)

    # The list article transcludes the season articles; its own {{Episode
    # list}} blocks are the film and the two shorts, none of them numbered.
    # Reading episodes from this page would ship exactly those three and none
    # of the show, so assert the shape that makes that obvious.
    own_blocks = wiki.episodes(list_text)
    assert own_blocks, "list article has no episode blocks at all"
    assert all(o is None and s is None for o, s, _, _, _ in own_blocks), \
        "the list article now carries numbered episodes of its own"
    assert re.search(r"==\s*Theatrical film\s*==", list_text), \
        "the film is no longer filed under its own heading"
    assert re.search(r"==\s*Shorts\s*==", list_text), \
        "the shorts are no longer filed under their own heading"
    # the film-and-shorts note dates the Hulu short; keep it honest
    fort = [b for _, _, t, _, b in own_blocks
            if t == "On the Fort Day of Christmas"]
    assert len(fort) == 1 and airdate(fort[0]) == (2026, 12, 7), \
        "On the Fort Day of Christmas is no longer dated December 7, 2026"

    for n in SEASONS:
        assert re.search(r"\{\{:Bob's Burgers season %d\}\}" % n, list_text), \
            "list article no longer transcludes the season %d article" % n
    headings = [int(m) for m in
                re.findall(r"\n=== Season (\d+)[^=]*===", list_text)]
    assert headings == SEASONS, \
        "list article's season headings are %s, expected %s" % (headings,
                                                                SEASONS)

    seasons, infoboxes = {}, {}
    for n in SEASONS:
        seasons[n], infoboxes[n] = read_season(n)

    # 1. the source article's own table is the check on every count parsed
    for n in SEASONS:
        numbered = sum(len(r[1]) for r in seasons[n])
        assert numbered == overview[n], \
            "season %d: parsed %d numbered episodes, overview says %d" \
            % (n, numbered, overview[n])

    # 2. overall numbering must run 1..313 unbroken or a season is missing
    everything = sorted(x for n in SEASONS for r in seasons[n] for x in r[0])
    assert everything == list(range(1, TOTAL_EPISODES + 1)), \
        "overall episode numbering is not contiguous 1..%d" % TOTAL_EPISODES

    # 3. rows are episodes minus the multi-part blocks' extra numbers
    rows_total = sum(len(seasons[n]) for n in SEASONS)
    assert rows_total == TOTAL_ROWS, \
        "parsed %d rows, expected %d" % (rows_total, TOTAL_ROWS)
    multi = [(n, r[2], r[1]) for n in SEASONS for r in seasons[n]
             if len(r[1]) > 1]
    assert len(multi) == 1 and multi[0][0] == 8, \
        "expected one multi-part episode in season 8, found %s" % (multi,)

    # 4. Fox aired every season out of production order — the claim the
    # broadcast-order note makes, checked rather than asserted in prose
    for n in SEASONS:
        codes = [r[4][0] for r in seasons[n]]
        assert all(codes), "season %d has an unlabelled production code" % n
        assert codes != sorted(codes), \
            "season %d aired in production order after all" % n

    # 5. the series infobox counts the run independently of the list article
    ib = wiki.infobox(text(SERIES_PAGE), kind="television")
    assert ib, "no television infobox on the series article"
    eps = re.search(r"\d+", ib("num_episodes"))
    assert eps and int(eps.group(0)) == TOTAL_EPISODES, \
        "series infobox says %r episodes, parsed %d" % (ib("num_episodes"),
                                                        TOTAL_EPISODES)
    assert ib("num_seasons").strip() == str(len(SEASONS)), \
        "series infobox says %r seasons, parsed %d" % (ib("num_seasons"),
                                                       len(SEASONS))
    # the series is still running, which is why the last season being over
    # has to be established from the season article rather than from here
    assert ib("last_aired").strip() == "present", \
        "the series has an end date now: %r" % ib("last_aired")
    # one running time for the whole show, given as a range, and no episode
    # block anywhere carries its own — together, the reason for no `w`
    assert re.fullmatch(r"\d+(–\d+)? minutes", ib("runtime").strip()), \
        "series runtime is no longer a single series-level value: %r" \
        % ib("runtime")

    # 6. nothing is mid-run: season 16's own infobox must carry a closed end
    # date, and it must be the last airdate parsed. There is no {{Aired
    # episodes}} stamp on this article to lean on.
    last_ib = infoboxes[SEASONS[-1]]
    end = re.search(r"\{\{End date\|\s*(\d{4})\s*\|\s*(\d{1,2})\s*\|"
                    r"\s*(\d{1,2})", last_ib("last_aired"))
    assert end, "season %d has no closed end date — it is still airing: %r" \
        % (SEASONS[-1], last_ib("last_aired"))
    end = tuple(int(g) for g in end.groups())
    assert seasons[SEASONS[-1]][-1][3] == end, \
        "season %d ends %s but its last episode aired %s" \
        % (SEASONS[-1], end, seasons[SEASONS[-1]][-1][3])

    # 7. the 300th-episode claim in the season 16 intro, checked
    assert any(300 in r[0] for r in seasons[16]), \
        "episode 300 is not in season 16"

    sections = []
    for n in SEASONS:
        rows = seasons[n]
        numbered = sum(len(r[1]) for r in rows)
        count = ("%d episodes" % numbered if numbered == len(rows)
                 else "%d episodes in %d rows" % (numbered, len(rows)))
        items = []
        for _overalls, in_seasons, title, _date, _codes in rows:
            label = "–".join(str(x) for x in
                             (in_seasons if len(in_seasons) < 3
                              else [in_seasons[0], in_seasons[-1]]))
            item = {"id": "bobs-s%de%s" % (n, "-".join(str(x)
                                                       for x in in_seasons)),
                    "t": title,
                    "n": label}
            if len(in_seasons) > 1:
                item["note"] = prop.join_bits(
                    "one hour-long episode",
                    "numbered %s in the season" % label.replace("–", " and "))
            items.append(item)
        sections.append({
            "id": "s%d" % n,
            "title": "Season %d" % n,
            "sub": prop.join_bits(year_span([r[3][0] for r in rows]), count),
            "items": items,
        })
        if n in INTRO:
            sections[-1]["intro"] = INTRO[n]

    sections[0]["open"] = True

    assert [s["id"] for s in sections] == ["s%d" % n for n in SEASONS]
    total = sum(len(s["items"]) for s in sections)
    assert total == TOTAL_ROWS, total
    assert sum(1 for s in sections for x in s["items"] if "w" in x) == 0, \
        "a weight crept in — this list is unweighted end to end"

    blurb = ("Fox's Belcher family sitcom, one row per episode, every season "
             "in the order it aired.")
    assert not re.search(r"\d", blurb), \
        "the blurb carries a number the card will contradict: %r" % blurb

    p = {
        "slug": SLUG,
        "title": "Bob's Burgers",
        "subtitle": "every episode, in broadcast order",
        "kind": "tv",
        "popularity": 70,
        "year": "2011–",
        "blurb": blurb,
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ["Episodes only — the film is not here.", "The Bob's Burgers "
             "Movie went out in cinemas in May 2022 and the source article "
             "files it under its own heading, with no episode number and no "
             "place in the count. A cinema feature dropped among "
             "twenty-two-minute episodes would count as one row exactly like "
             "them, which misrepresents both, so it is named here instead of "
             "listed. The two shorts, My Butt Has a Fever and On the Fort Day "
             "of Christmas, are out for the same reason; the second is a Hulu "
             "holiday short dated December 7, 2026."],
            ["The Bleakening is one row, not two.", "Season 8's Christmas "
             "special aired as a single hour-long block in December 2017. "
             "Wikipedia numbers it as episodes 6 and 7 but gives the two "
             "halves one title between them, so this list follows its episode "
             "table and shows one row labelled 6–7. That is why the total "
             "reads one lower than the 313 episodes the series infobox "
             "counts; every one of those 313 numbers is accounted for, and "
             "the season 8 heading says so."],
            ["Broadcast order, which is the only order there is.", "Fox has "
             "aired this show out of production order in all sixteen seasons, "
             "and the production cycles do not line up with the broadcast "
             "seasons either — broadcast season 3 mixes two cycles, and "
             "season 14 is mostly the thirteenth. There is no production "
             "order any box set or streaming season follows, and Wikipedia's "
             "numbering agrees with the airdates end to end, so the rows sit "
             "where the numbering puts them."],
            ["Nothing is weighted.", "Wikipedia documents one running time "
             "for the series — 20 to 23 minutes — and not a single episode in "
             "the sixteen season articles carries its own, so there is no "
             "verifiable per-row number to weight with and every row counts "
             "one. A half-weighted list is worse than an unweighted one: a "
             "row with no weight would silently count as a full hour. That "
             "holds for the hour-long Bleakening too."],
            ["The show is not finished.", "Season 16 ended on May 17, 2026. "
             "Fox renewed Bob's Burgers in April 2025 for four more seasons, "
             "through a nineteenth; season 17 had not begun airing when this "
             "was built, so nothing from it is listed. Its episodes join the "
             "list as they go out."],
            "Titles and airdates machine-read from Wikipedia's sixteen Bob's "
            "Burgers season articles; every season's count is asserted against "
            "both the list article's own series overview and that season's own "
            "infobox, the overall numbering asserted contiguous, the airdates "
            "asserted in order within every season, and the total "
            "cross-checked against the series infobox before this builds.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d rows covering %d episodes in %d sections"
          % (out.name, total, TOTAL_EPISODES, len(sections)))
    for s in sections:
        print("   %-12s %3d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
