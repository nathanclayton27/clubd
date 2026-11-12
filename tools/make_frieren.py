#!/usr/bin/env python3
"""Generate properties/frieren.json — both aired seasons, every episode.

    PYTHONIOENCODING=utf-8 python tools/make_frieren.py

Madhouse's adaptation of Kanehito Yamada and Tsukasa Abe's manga. 38 rows:
28 episodes of season 1 (September 2023 to March 2024) and 10 of season 2
(January to March 2026), in broadcast order, read from Wikipedia's
"List of Frieren episodes" article.

THE SECOND SEASON HAS ALREADY AIRED, IN FULL. That is a fact taken from the
source, not assumed from the announcement: the article's own {{Series
overview}} gives season 2 `episodes2 = 10`, `start2 = 2026-01-16` and — the
part that settles it — `end2 = 2026-03-27`, an {{End date}} rather than an
open run. Every one of the ten episodes parses with an airdate on or before
TODAY, which main() asserts row by row. So the season is listed in full and
this list is not a broadcast tracker.

WHICH IS WHY THERE IS NO `schedule` BLOCK. The house treatment for a
currently-running season is one dated window per episode (president-curtis
and lanterns both do it, and both were mid-run when they shipped). It is the
right shape only while a season is actually airing: the pace line then reads
"are you caught up with the broadcast". Season 2 closed on 27 March 2026,
five months before this was built, and season 3 does not premiere until
October 2027 with no per-episode dates published. Windows here would pace a
club against a broadcast that finished, so there are none.

SEASON 3 IS ANNOUNCED AND IS NOT LISTED, WITH A TRIPWIRE. The source carries
it as `start3 = {{Start date|2027|10}}` with `episodes3` EMPTY, no episode
table, and no `=== Season 3 ===` heading; the series article says it covers
the "Golden Land" arc and was announced after season 2's finale. Nothing
about it can be listed, because the source publishes no episode. main()
therefore asserts all three of those absences and asserts the announced
premiere is still in the future — the day Wikipedia starts filling season 3
in, this generator fails loudly instead of quietly shipping a list that has
gone short.

THE SHORTS ARE A DIFFERENT SERIES. "Frieren: Beyond Journey's End – Spell
That Does OOO" is a run of short episodes with its own seasons and its own
numbering, filed under its own level-2 heading on the same article. It is
not part of the television series' 38 and is not listed; the section
boundary is where this generator stops reading, and main() asserts that
heading is still there so the cut cannot silently swallow real episodes.

WEIGHTS: NONE, AND THE SOURCE IS THE REASON. Wikipedia documents exactly one
running time for this show — `runtime = 24 minutes` on the series infobox,
a series-level figure — and none whatsoever per episode: no episode entry in
either season carries a Runtime field, which main() asserts for all 38.
Wikidata does not rescue it; the series item (Q115792176) holds TWO
unqualified, equal-rank P2047 durations, 24 minutes and 25 minutes, with
nothing to choose between them. Spreading a series average over 38 rows
would invent precision the source refuses to give, and the two-hour
four-episode premiere is proof that a flat per-episode number is not what
happened. It is all rows or none, because a row with no `w` on a weighted
list silently counts as one hour and a part-weighted list reads worse than
an unweighted one. It is none; main() asserts no row carries a weight.

Everything is machine-read from the cached Wikipedia wikitext — the episode
list article and the series article. Nothing is typed from memory. Before
anything is written: each season's parsed row count is asserted against the
list article's {{Series overview}}; each season's in-season numbering is
asserted to run 1..N and the overall numbering to run 1..38 unbroken; the
overall total is cross-checked against the series infobox's num_episodes and
num_seasons; airdates are asserted non-decreasing, asserted to match the
overview's start/end dates for each season, and asserted to be in the past;
and the accent pair is asserted unused by every other property on disk.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki  # noqa: E402

SLUG = "frieren"

# The wikitext cache. Nothing here is required — gwlib re-fetches and
# repopulates whichever of these exists — but a warmed cache keeps this
# generator offline and keeps it off Wikipedia's rate limiter.
CACHE = next((d for d in (prop.ROOT / "scratch" / SLUG,
                          prop.ROOT / "scratch" / "agent-frieren")
              if d.exists()), prop.ROOT / "scratch" / SLUG)

LIST_PAGE = "List of Frieren episodes"
SERIES_PAGE = "Frieren (TV series)"

SEASONS = [1, 2]
TOTAL_EPISODES = 38          # 28 + 10, asserted three ways
UNAIRED_SEASON = 3           # announced, undated per episode, not listed

# The shorts run, which is where this generator stops reading the article.
SHORTS_HEADING = "== ''Spell That Does OOO'' =="

# Hard-coded rather than read from the clock so re-running produces the same
# file. Anything dated after this has not aired.
TODAY = (2026, 8, 25)

ACCENT = "#8A6A2F"       # the warm gold of the first season's palette
ACCENT_DARK = "#9ECBEA"  # ...against the pale blue of the second's

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


NUMWORD = ["zero", "one", "two", "three", "four", "five", "six", "seven",
           "eight", "nine", "ten", "eleven", "twelve"]


def word(n):
    """Small counts read as words in prose; anything larger stays a numeral."""
    return NUMWORD[n] if 0 <= n < len(NUMWORD) else str(n)


def text(page):
    t = wiki.wikitext(page, cache_dir=CACHE)
    assert t, "no wikitext for %r" % page
    return t


def strip_refs(t):
    """Prose with the footnotes gone, for the sentences main() reads as fact."""
    t = re.sub(r"<ref[^>]*/>", "", t)
    return re.sub(r"<ref.*?</ref>", "", t, flags=re.S)


def date_in(field, kind="Start"):
    """The first {{Start date}} / {{End date}} in a chunk, as (y, m, d)."""
    m = re.search(r"\{\{%s date\s*\|\s*(\d{4})\s*\|\s*(\d{1,2})\s*\|"
                  r"\s*(\d{1,2})" % kind, field or "", re.I)
    assert m, "no %s date in %r" % (kind.lower(), (field or "")[:80])
    return tuple(int(g) for g in m.groups())


def fmt_date(d):
    return "%d %s %d" % (d[2], MONTHS[d[1] - 1], d[0])


def year_span(years):
    a, b = min(years), max(years)
    if a == b:
        return str(a)
    return "%d–%02d" % (a, b % 100) if a // 100 == b // 100 else "%d–%d" % (a, b)


def series_overview(list_text):
    """{season: (episodes, start, end)} from the article's own overview.

    Season 3 is read separately and deliberately: it is the row that must
    still be empty for this list to be complete."""
    seg = re.search(r"\{\{Series overview(.*?)\n\}\}", list_text, re.S)
    assert seg, "no series overview on the list article"
    body = seg.group(1)

    out = {}
    for n in SEASONS:
        m = re.search(r"\|\s*episodes%d\s*=\s*(\d+)" % n, body)
        assert m, "the overview no longer counts season %d" % n
        s = re.search(r"\|\s*start%d\s*=\s*([^\n]*)" % n, body)
        e = re.search(r"\|\s*end%d\s*=\s*([^\n]*)" % n, body)
        assert s and e, "season %d has no start/end in the overview" % n
        out[n] = (int(m.group(1)), date_in(s.group(1)),
                  date_in(e.group(1), "End"))
    assert sum(v[0] for v in out.values()) == TOTAL_EPISODES, \
        "the overview counts %d episodes across seasons %s, expected %d" \
        % (sum(v[0] for v in out.values()), SEASONS, TOTAL_EPISODES)

    # --- the tripwire on the unaired season ---------------------------------
    n = UNAIRED_SEASON
    assert re.search(r"\|\s*episodes%d\s*=\s*\n" % n, body), \
        "the series overview now gives season %d an episode count — it has " \
        "started airing and this list is short. Add it." % n
    assert not re.search(r"\|\s*episodes%d\s*=\s*\d" % n, body), \
        "season %d now has episodes in the overview" % n
    s3 = re.search(r"\|\s*start%d\s*=\s*([^\n]*)" % n, body)
    assert s3, "the overview no longer announces season %d at all — either " \
               "it was cancelled or the article was restructured" % n
    m = re.search(r"\{\{Start date\s*\|\s*(\d{4})\s*\|\s*(\d{1,2})",
                  s3.group(1))
    assert m, "season %d's announced start is no longer a {{Start date}}" % n
    announced = (int(m.group(1)), int(m.group(2)))
    assert announced > TODAY[:2], \
        "season %d was announced for %s, which is not in the future — check " \
        "whether it has begun airing" % (n, announced)
    assert "=== Season %d" % n not in list_text, \
        "the list article now has a season %d section — it is airing and " \
        "this list is short" % n
    return out, announced


def season_segments(list_text):
    """{season: (segment, (first year, last year))} cut at the article's own
    headings, stopping at the shorts run so its numbering cannot leak in."""
    assert SHORTS_HEADING in list_text, \
        "the shorts heading moved — this generator cuts the article there " \
        "and would otherwise parse the shorts as episodes"
    end = list_text.index(SHORTS_HEADING)
    heads = list(re.finditer(r"^=== Season (\d+) \((\d{4})(?:–(\d{4}))?\) ===",
                             list_text[:end], re.M))
    assert [int(h.group(1)) for h in heads] == SEASONS, \
        "the article's season headings are %s, expected %s" \
        % ([h.group(1) for h in heads], SEASONS)
    out = {}
    for i, h in enumerate(heads):
        stop = heads[i + 1].start() if i + 1 < len(heads) else end
        years = (int(h.group(2)), int(h.group(3) or h.group(2)))
        out[int(h.group(1))] = (list_text[h.end():stop], years)
    return out


def delay_note(block):
    """The source's own broadcast-delay footnote, as a row note.

    Season 2's sixth episode moved a week; the article says why in an
    {{efn}} on its airdate. Read rather than remembered, so the note
    disappears if the footnote does."""
    m = re.search(r"\{\{efn\|Episode \d+ was delayed by (\w+) weeks? due to "
                  r"coverage of the \[\[([^\]|]+)(?:\|[^\]]+)?\]\]\.\}\}",
                  block)
    if not m:
        return ""
    return "held %s week%s for %s coverage" \
        % (m.group(1), "" if m.group(1) == "one" else "s", m.group(2))


def rows_from(seg, label):
    """[(overall, in_season, title, (y,m,d), note)] for one season's segment."""
    raw = wiki.episodes(seg)
    assert raw, "%s parsed empty" % label
    rows = []
    for o, s, t, _, block in raw:
        assert not re.search(r"\|\s*Runtime\s*=", block, re.I), \
            "%s now carries a per-episode runtime — revisit weights, " \
            "because the only reason this list is unweighted is that it " \
            "did not" % label
        assert o and s and t, "%s row incomplete: %r" % (label, (o, s, t))
        assert not re.search(r"\d+\.\d", str(o)), "%s: fractional row %r" % (label, o)
        rows.append((o, s, t, date_in(block), delay_note(block)))
    dates = [d for _, _, _, d, _ in rows]
    assert dates == sorted(dates), "%s airdates are not in broadcast order" % label
    for _, s, t, d, _ in rows:
        assert d <= TODAY, \
            "%s episode %d (%r) is dated %s, which has not happened yet" \
            % (label, s, t, fmt_date(d))
    return rows


def premiere_evidence(list_text, seg1):
    """The source's own statement that season 1 opened with a two-hour
    special of the first four episodes, read rather than remembered."""
    m = re.search(r"premiered with a two-hour special on September 29, 2023, "
                  r"on .{0,40}Nippon TV.{0,120}?, which is normally reserved "
                  r"for feature films, becoming the first anime series to do "
                  r"so\.", re.sub(r"\s+", " ", strip_refs(list_text)))
    assert m, "the list article no longer describes the two-hour premiere — " \
              "the season 1 intro and the first four rows' notes say so"
    f = re.search(r"The episode rating counts as part of a 2-hour special "
                  r"premiere for the first (\w+) episodes\.", seg1)
    assert f, "the premiere footnote naming how many episodes the special " \
              "covered is gone"
    assert f.group(1) == "four", \
        "the special is now described as covering %r episodes" % f.group(1)
    return 4


def check_no_weights_available(list_text, series_text):
    """The runtime situation, asserted so a later source change reopens it."""
    ib = wiki.infobox(series_text, kind="television")
    assert ib, "no television infobox on the series article"
    rt = ib("runtime").strip()
    assert rt == "24 minutes", \
        "the series runtime is now %r rather than the single series-level " \
        "figure this list refuses to spread across every episode — if the " \
        "source has started publishing per-episode lengths, weight the list" % rt
    assert not re.search(r"\|\s*Runtime\s*=", list_text, re.I), \
        "the episode list article now carries Runtime fields — revisit weights"
    return ib


def season_three_arc(series_text):
    """The one sentence naming what season 3 adapts, for the notes."""
    t = re.sub(r"\s+", " ", strip_refs(series_text))
    m = re.search(r"A third season, covering the \"([^\"]+)\" arc, was "
                  r"announced after the airing of the final episode of the "
                  r"second season\. It is set to premiere in (\w+ \d{4})\.", t)
    assert m, "the series article no longer describes the third season the " \
              "way the notes quote it"
    return m.group(1), m.group(2)


def second_season_director(series_text):
    """The director handover, read from the source rather than asserted."""
    t = re.sub(r"\s+", " ", strip_refs(series_text))
    m = re.search(r"The staff and cast from the first season are reprising "
                  r"their roles, with ([^,]+) replacing ([^ ]+ [^ ]+) as the "
                  r"season's director\.", t)
    assert m, "the series article no longer names the second season's director"
    return m.group(1).strip()


def check_accent():
    """The pair, and each half of it, must be unused by every other list."""
    for f in sorted((prop.ROOT / "properties").glob("*.json")):
        if f.stem in (SLUG, "index", "search"):
            continue
        other = json.loads(f.read_text(encoding="utf-8"))
        pair = (other.get("accent"), other.get("accentDark"))
        assert pair != (ACCENT, ACCENT_DARK), \
            "accent pair already belongs to %s" % f.stem
        for hexv in (ACCENT, ACCENT_DARK):
            assert hexv not in pair, "%s already uses %s" % (f.stem, hexv)


def main():
    list_text = text(LIST_PAGE)
    series_text = text(SERIES_PAGE)

    overview, announced = series_overview(list_text)
    segs = season_segments(list_text)
    special = premiere_evidence(list_text, segs[1][0])
    ib = check_no_weights_available(list_text, series_text)
    arc, premiere = season_three_arc(series_text)
    s2_director = second_season_director(series_text)
    check_accent()

    seasons = {n: rows_from(segs[n][0], "season %d" % n) for n in SEASONS}

    # 1. each season's count, against the overview
    for n in SEASONS:
        rows = seasons[n]
        assert len(rows) == overview[n][0], \
            "season %d: parsed %d rows, the overview says %d" \
            % (n, len(rows), overview[n][0])
        assert [s for _, s, _, _, _ in rows] == list(range(1, len(rows) + 1)), \
            "season %d numbering is not 1..%d" % (n, len(rows))
        assert rows[0][3] == overview[n][1], \
            "season %d: the overview opens %s, the first episode aired %s" \
            % (n, overview[n][1], rows[0][3])
        assert rows[-1][3] == overview[n][2], \
            "season %d: the overview closes %s, the last episode aired %s" \
            % (n, overview[n][2], rows[-1][3])
        # the article's own heading years must agree with the airdates
        years = {d[0] for _, _, _, d, _ in rows}
        assert (min(years), max(years)) == segs[n][1], \
            "season %d spans %s, its heading says %s" \
            % (n, (min(years), max(years)), segs[n][1])

    # 2. overall numbering contiguous, or a season is missing
    numbered = sorted(o for n in SEASONS for o, _, _, _, _ in seasons[n])
    assert numbered == list(range(1, TOTAL_EPISODES + 1)), \
        "overall episode numbering is not contiguous 1..%d" % TOTAL_EPISODES

    # 3. and the series infobox counts the run independently
    assert ib("num_episodes").strip() == str(TOTAL_EPISODES), \
        "the series infobox says %r episodes, parsed %d" \
        % (ib("num_episodes"), TOTAL_EPISODES)
    assert ib("num_seasons").strip() == str(len(SEASONS)), \
        "the series infobox says %r seasons, parsed %d" \
        % (ib("num_seasons"), len(SEASONS))
    network = wiki.clean(ib("network")).split(",")[0].strip()
    assert network == "Nippon Television", \
        "the series now airs on %r" % network

    # 4. the first four episodes really did share one broadcast
    opening = {d for _, s, _, d, _ in seasons[1] if s <= special}
    assert len(opening) == 1, \
        "the first %d episodes carry %d different airdates, so they were not " \
        "one special" % (special, len(opening))
    assert seasons[1][special][3] != seasons[1][0][3], \
        "episode %d shares the premiere's airdate — the special covered more " \
        "than %d episodes" % (special + 1, special)

    sections = []
    for n in SEASONS:
        rows = seasons[n]
        span = year_span([d[0] for _, _, _, d, _ in rows])
        items = []
        for _, s, t, d, delay in rows:
            bits = []
            if n == 1 and s == 1:
                bits.append("series premiere")
                bits.append("episodes 1–%d aired together as a two-hour "
                            "special" % special)
            elif n == 1 and s <= special:
                bits.append("part of the two-hour premiere")
            # no "season finale": the last row of a section titled "Season N"
            # already says it (CLU-123, CLU-557)
            if delay:
                bits.append(delay)
            row = {"id": "frieren-s%de%d" % (n, s), "t": t, "n": str(s)}
            note = prop.join_bits(*bits)
            if note:
                row["note"] = note
            items.append(row)
        sections.append({
            "id": "s%d" % n,
            "title": "Season %d" % n,
            "sub": prop.join_bits(span, "%d episodes" % len(rows), "Nippon TV"),
            "items": items,
        })

    sections[0]["intro"] = (
        "Two straight cours, 28 episodes. It opened on %s with a two-hour "
        "special made of the first %s episodes, in a Nippon TV slot "
        "normally kept for feature films — the first anime series ever given "
        "it — and ran to %s."
        % (fmt_date(seasons[1][0][3]), word(special),
           fmt_date(seasons[1][-1][3])))
    sections[0]["open"] = True
    sections[1]["intro"] = (
        "Ten episodes, %s to %s, with %s taking over as director. The rest of "
        "the staff and the cast return."
        % (fmt_date(seasons[2][0][3]), fmt_date(seasons[2][-1][3]),
           s2_director))

    total = sum(len(s["items"]) for s in sections)
    assert total == TOTAL_EPISODES, "%d rows, expected %d" % (total, TOTAL_EPISODES)
    assert sum(1 for s in sections for x in s["items"] if "w" in x) == 0, \
        "a weight crept in — this list is unweighted end to end"
    # the reason this list carries no dated pace windows, asserted rather
    # than asserted-by-omission: nothing is between its first and last
    # broadcast right now
    last_aired = max(d for n in SEASONS for _, _, _, d, _ in seasons[n])
    assert last_aired < TODAY and announced > TODAY[:2], \
        "a season is currently airing (last episode %s, next season %s) — " \
        "this list should carry the house `schedule` windows, one per " \
        "episode, the way president-curtis and lanterns do" \
        % (fmt_date(last_aired), announced)

    p = {
        "slug": SLUG,
        "title": "Frieren: Beyond Journey's End",
        "subtitle": "both aired seasons, every episode",
        "kind": "anime",
        "popularity": 67,
        "year": "2023–",
        "blurb": "Madhouse's elf-mage road story — 28 episodes of the first "
                 "season and 10 of the second, in broadcast order.",
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ["Both seasons here have finished airing.",
             "Season 1 ran from September 2023 to March 2024; season 2 ran "
             "from 16 January to 27 March 2026. The source closes both with a "
             "final date rather than leaving them open, and every one of the "
             "38 episodes is asserted to have already aired before this list "
             "is written. There is no pace schedule on this list because "
             "there is no broadcast left to keep pace with."],
            ["A third season is coming, and nothing of it is listed.",
             "It was announced after the second season's finale, covers the "
             "\"%s\" arc, and is set to premiere in %s. The source carries "
             "that date and nothing else — no episode count, no episode "
             "table, no section. Rather than guess, this list stops at "
             "episode %d and the generator asserts all three of those "
             "absences: the day Wikipedia starts filling season 3 in, the "
             "build fails instead of quietly staying short."
             % (arc, premiere, TOTAL_EPISODES)],
            ["The premiere was %s episodes at once." % word(special),
             "Season 1 opened with a two-hour special made of episodes 1 to "
             "%d, in a Nippon TV slot normally reserved for feature films — "
             "the first anime series to get it. They are %s rows here "
             "because the source lists %s episodes, and each of the %s says "
             "so." % (special, word(special), word(special), word(special))],
            ["The shorts are a separate series.",
             "Frieren: Beyond Journey's End – Spell That Does OOO is a "
             "run of short episodes with its own seasons and its own "
             "numbering. The source files it under its own heading, apart "
             "from the television series, and it is not listed here."],
            ["Nothing is weighted, and hours are not tracked on this list.",
             "Wikipedia gives one running time for the whole show — 24 "
             "minutes, on the series infobox — and none at all per episode: "
             "not one of the 38 entries carries a length, which is asserted "
             "before this builds. Wikidata is no better; the series item "
             "holds two equal-ranked durations, 24 minutes and 25 minutes, "
             "with nothing to pick between them. Spreading a series-level "
             "average across every row would invent precision the source "
             "refuses to give, and the two-hour four-episode premiere shows "
             "why a flat number would be wrong. It has to be every row or no "
             "row, because a row with no weight silently counts as a full "
             "hour — so it is no row, and every episode counts one."],
            "Titles and airdates machine-read from Wikipedia's \"List of "
            "Frieren episodes\" and \"Frieren (TV series)\" articles; each "
            "season's count, first and last airdates are asserted against "
            "the article's own series overview, the overall numbering "
            "asserted contiguous, and the total cross-checked against the "
            "series infobox before this builds.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d rows in %d sections" % (out.name, total, len(sections)))
    for n, s in zip(SEASONS, sections):
        rows = seasons[n]
        print("   %-10s %3d  %-28s %s – %s"
              % (s["title"], len(s["items"]), s["sub"],
                 fmt_date(rows[0][3]), fmt_date(rows[-1][3])))
    print("   unweighted: no per-episode runtime published for any of %d rows"
          % total)
    print("   season %d announced for %s (%s arc) — not listed"
          % (UNAIRED_SEASON, premiere, arc))


if __name__ == "__main__":
    main()
