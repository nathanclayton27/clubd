#!/usr/bin/env python3
"""Generate properties/blackadder.json — 24 episodes and the four specials.

    python3 tools/make_blackadder.py

Four series of six on BBC1, 1983 to 1989, plus the four things Wikipedia's own
infobox counts alongside them: "24 (plus 4 specials)". Those four are The
Cavalier Years (1988), Blackadder's Christmas Carol (1988), Back & Forth (1999)
and the 1982 pilot, which sat unseen for forty-one years. 28 rows.

ORDER IS BROADCAST ORDER, END TO END, AND THAT DECIDES WHERE THE ODD ONES SIT.
The two 1988 specials went out between series 3 (autumn 1987) and series 4
(autumn 1989), so they sit between them, in their own section, exactly as the
source's {{Series overview}} files them. Back & Forth follows series 4, ten
years later. The pilot goes LAST, not first: it was taped in 1982, shelved, and
first screened on Gold on 15 June 2023 — forty years to the day after series 1
began. main() asserts every section's first airdate is later than the one
before, so the ordering is checked rather than claimed.

WHAT IS OUT, AND WHY. The source's episode page carries two further tables and
neither is the show: "Additional appearances" (eleven charity sketches, cameos
and after-dinner turns, one of them a radio slot, several with no airdate beyond
a year) and "Retrospectives and documentaries" (four programmes about
Blackadder). Neither table is counted by the infobox's 24-plus-4, and main()
asserts both headings still exist so this exclusion stays a decision about a
known part of the source rather than an accident of parsing.

SERIES 1's BROADCAST ORDER IS DISPUTED BY THE SOURCE ITSELF. The episode
table's airdates run straight down — "Born to Be King" on 22 June 1983 as the
second episode — while a note on the same page says transmission switched the
second and fourth episodes because that episode was not ready. The rows follow
the table's own dates, because those are the machine-readable field and the note
is prose; the disagreement is stated in the notes rather than resolved silently.

WEIGHTS. None. Each series article documents one running time for its series
(33 minutes for the first, 30 for the rest), no {{Episode list}} block anywhere
carries a RunTime or Length field, and main() checks both. The four specials do
each publish a length on their own article — 15, 42, 37 and 32 minutes — and
those numbers appear in the row notes, but a weight on four rows out of 28 is
the exact bug CLU-131 is about: the reader resolves `WEIGHT = x.w >= 0 ? x.w :
1`, so the 24 unweighted episodes would silently count as an hour each. It is
all rows or none, and there is no per-episode figure to be had.

Everything is machine-read from the cached Wikipedia wikitext in
scratch/britcoms/ — "List of Blackadder episodes", the four series articles it
transcludes, the series article, and each special's own article for its length.
Before anything is written: the list article is asserted to transclude all four
series articles; each series is asserted to hold six numbered episodes running
1..6 in series and contiguous across the run 1..24; airdates are asserted
non-decreasing inside every section and between sections; the 24-plus-4 count is
asserted against the series infobox; series 4's last airdate is asserted to
equal that infobox's end date; and the accent pair is asserted unused by any
other property.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki  # noqa: E402

SLUG = "blackadder"
CACHE = prop.ROOT / "scratch" / "britcoms"
LIST_PAGE = "List of Blackadder episodes"
SERIES_PAGE = "Blackadder"

# (source article, section id, section title, sub year, intro key)
SERIES = [
    ("The Black Adder", "s1", "Series 1: The Black Adder"),
    ("Blackadder II", "s2", "Series 2: Blackadder II"),
    ("Blackadder the Third", "s3", "Series 3: Blackadder the Third"),
    ("Blackadder Goes Forth", "s4", "Series 4: Blackadder Goes Forth"),
]
EPISODES = 24       # the series infobox's own figure
SPECIALS = 4        # ditto, and the four are the pilot, two 1988s, Back & Forth
TOTAL = EPISODES + SPECIALS

ACCENT = "#4A2545"
ACCENT_DARK = "#D8B04A"

INTRO = {
    "s1": "Six episodes on BBC1 in 1983, written by Rowan Atkinson and Richard "
          "Curtis and shot on location with horses, extras and medieval "
          "costumes. The source records it costing a million pounds and the "
          "BBC not repeating the arrangement.",
    "s2": "The BBC asked for improvements and cut the budget. Ben Elton joined "
          "Richard Curtis as co-writer, the production moved into the studio, "
          "and the episode titles became single words.",
    "s3": "Regency London. The source notes the titles parody Jane Austen, one "
          "alliterative pair at a time.",
    "specials": "Two one-offs made between series 3 and series 4, and they sit "
                "here because that is when they aired.",
    "s4": "The trenches, 1989, and the last of the series proper. The source "
          "notes the titles are puns on military ranks, the final one aside.",
    "bf": "The millennium special, ten years on: shown at the Millennium Dome "
          "on New Year's Eve 1999, then Sky One in 2000 and BBC1 in 2002. The "
          "source's episode table dates it by the Dome screening, and so does "
          "this row.",
    "pilot": "Taped in 1982 and never broadcast. Gold screened it on 15 June "
             "2023, forty years to the day after series 1 began, which is why "
             "it is last on a list in broadcast order rather than first.",
}


def text(page):
    t = wiki.wikitext(page, cache_dir=CACHE)
    assert t, "no wikitext for %r" % page
    return t


def start_date(v):
    """(y, m, d) from a {{Start date}}, whose df= flag may come first.

    The series 3 and 4 tables carry a FILMING date in Aux2 above the airdate,
    so this is always applied to a named field rather than to a whole block:
    "the first Start date in the block" would have dated every episode of
    Blackadder the Third three months early."""
    m = re.search(r"\{\{Start date\s*\|([^}]*)\}\}", v or "", re.I)
    if not m:
        return None
    nums = [int(a.strip()) for a in m.group(1).split("|") if a.strip().isdigit()]
    assert len(nums) >= 3, "incomplete date %r" % v[:60]
    return tuple(nums[:3])


def airdate(block):
    """The block's OriginalAirDate, by name — never whatever date comes first."""
    return start_date(field(block, "OriginalAirDate"))


def end_date(v):
    m = re.search(r"\{\{End date\s*\|([^}]*)\}\}", v or "", re.I)
    if not m:
        return None
    nums = [int(a.strip()) for a in m.group(1).split("|") if a.strip().isdigit()]
    assert len(nums) >= 3, "incomplete end date %r" % v[:60]
    return tuple(nums[:3])


def field(block, name):
    m = re.search(r"\|\s*%s\s*=\s*(.*?)(?=\n\s*\||\Z)" % name, block, re.S)
    return m.group(1).strip() if m else ""


def link_target(raw):
    """The article a wikilinked Title field points at. The four specials'
    lengths come from their own pages, and this is how those pages are found
    without a hard-coded list of names."""
    m = re.match(r"\s*\[\[([^\]|]+)", raw)
    assert m, "title field %r is not a wikilink" % raw[:60]
    return m.group(1).strip()


def minutes(page):
    """The runtime a special's own article publishes, in whole minutes."""
    t = text(page)
    ib = wiki.infobox(t, kind="television")
    assert ib, "no television infobox on %r" % page
    raw = ib("runtime") or ib("length")
    m = re.search(r"(\d+)\s*minutes", raw)
    assert m, "%r publishes no runtime: %r" % (page, raw)
    return int(m.group(1))


MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def fmt_date(d):
    """(1988, 2, 5) -> "5 February 1988" — British order, as the source uses."""
    y, m, day = d
    return "%d %s %d" % (day, MONTHS[m - 1], y)


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


def read_series(page, sid):
    """[(overall, in_series, title, (y, m, d))] from a series' own article."""
    body = text(page)
    rows = []
    for overall, in_series, title, _y, blk in wiki.episodes(body):
        assert title, "%s has an episode block with no title" % page
        assert overall and in_series, "%s row %r is unnumbered" % (page, title)
        assert not re.search(r"\|\s*(?:RunTime|Runtime|Length)\s*=", blk), \
            "%s row %r now carries a runtime — the no-weights reasoning " \
            "needs revisiting" % (page, title)
        d = airdate(blk)
        assert d, "%s row %r has no airdate" % (page, title)
        rows.append((overall, in_series, title, d))
    assert len(rows) == 6, "%s parsed %d episodes, expected 6" % (page, len(rows))
    assert [r[1] for r in rows] == list(range(1, 7)), \
        "%s in-series numbering is not 1..6" % page
    dates = [r[3] for r in rows]
    assert dates == sorted(dates), "%s is not in broadcast order" % page
    # one runtime for the series, none per episode: half the no-weights reason
    ib = wiki.infobox(body, kind="television")
    assert ib and re.match(r"\d+ minutes", ib("runtime").strip()), \
        "%s no longer gives a single series-level runtime: %r" \
        % (page, ib("runtime") if ib else None)
    return rows


def section_of(list_text, heading):
    """One section of the list article, up to the NEXT heading of any level.

    The level matters: splitting on `===` alone runs the Back & Forth section
    straight into "==Additional appearances==" and swallows eleven charity
    sketches and four documentaries."""
    # the trailing newline is a lookahead, not consumed: eating it makes two
    # headings on consecutive lines invisible ("==Episodes==" then "===Pilot===")
    parts = re.split(r"\n(=+)\s*([^=\n]+?)\s*\1[ \t]*(?=\n)", list_text)
    heads = [parts[i + 1].strip() for i in range(1, len(parts), 3)]
    assert heading in heads, "no %r section on the list article (has %s)" \
        % (heading, heads)
    return parts[3 + heads.index(heading) * 3]


def main():
    accent_is_unused((ACCENT, ACCENT_DARK))

    list_text = text(LIST_PAGE)

    # the four series' tables live on their own articles and are transcluded
    # here; a generator that read this page for episodes would find the pilot,
    # the specials and eleven charity sketches, and none of the show
    for page, _sid, _title in SERIES:
        assert re.search(r"\{\{:%s\}\}" % re.escape(page), list_text), \
            "the list article no longer transcludes %r" % page
    # the two tables this list deliberately leaves out
    for heading in ("Additional appearances", "Retrospectives and documentaries"):
        assert re.search(r"==\s*%s\s*==" % re.escape(heading), list_text), \
            "%r is no longer its own section — recheck what is excluded" % heading
    # the prose that contradicts series 1's own airdates, quoted in the notes
    assert "not ready for transmission" in list_text, \
        "the list article no longer disputes series 1's broadcast order"
    # the section intros' non-arithmetic claims, checked against the sentences
    # they came from rather than trusted
    for phrase in ("single word references", "alliteration", "puns on"):
        assert phrase in list_text, \
            "the list article no longer says %r about a series' titles" % phrase

    series = {sid: read_series(page, sid) for page, sid, _t in SERIES}
    numbering = [r[0] for _p, sid, _t in SERIES for r in series[sid]]
    assert numbering == list(range(1, EPISODES + 1)), \
        "overall episode numbering is not contiguous 1..%d" % EPISODES

    # --- the four specials, each read from the source table that carries it
    specials = []
    for _overall, _in_s, _title, _y, blk in wiki.episodes(
            section_of(list_text, "Specials")):
        raw = field(blk, "Title")
        page = link_target(raw)
        d = airdate(blk)
        assert d, "special %r has no airdate" % page
        specials.append((wiki.clean(raw), page, d))
    assert len(specials) == 2, "expected two 1988 specials, got %d" % len(specials)

    bf_block = wiki.episodes(section_of(list_text, "''Back & Forth''"))
    assert len(bf_block) == 1, "expected one Back & Forth row"
    bf_raw = field(bf_block[0][4], "Title")
    back_forth = (wiki.clean(bf_raw), link_target(bf_raw),
                  airdate(bf_block[0][4]))
    assert back_forth[2], "Back & Forth has no airdate"

    pilot_block = wiki.episodes(section_of(list_text, "Pilot"))
    assert len(pilot_block) == 1, "expected one pilot row"
    pilot_raw = field(pilot_block[0][4], "Title")
    assert airdate(pilot_block[0][4]) is None, \
        "the pilot row now carries an airdate of its own — reread it"
    # the pilot's screening date lives in the series overview, not the table
    sm = re.search(r"\|\s*released0S\s*=\s*(\{\{Start date[^}]*\}\})", list_text)
    assert sm, "the series overview no longer dates the pilot's screening"
    screened = start_date(sm.group(1))
    assert screened, "the pilot's screening date is unparseable: %r" % sm.group(1)
    pilot = (wiki.clean(pilot_raw), link_target(pilot_raw), screened)
    assert "Born to Be King" in field(pilot_block[0][4], "ShortSummary"), \
        "the source no longer ties the pilot's story to Born to Be King"

    # --- the series article counts the whole thing independently: "24 (plus 4
    #     specials)", which is the only check that says all four odd ones are in
    series_text = text(SERIES_PAGE)
    ib = wiki.infobox(series_text, kind="television")
    assert ib, "no television infobox on the series article"
    for phrase in ("Millennium Dome", "It cost a million pounds"):
        assert phrase in series_text, \
            "the series article no longer supports the intro claim %r" % phrase
    counts = [int(x) for x in re.findall(r"\d+", ib("num_episodes"))]
    assert counts[:2] == [EPISODES, SPECIALS], \
        "series infobox says %r, expected %d episodes plus %d specials" \
        % (ib("num_episodes"), EPISODES, SPECIALS)
    assert ib("num_series").strip() == "4", \
        "series infobox says %r series, expected 4" % ib("num_series")
    end = end_date(ib("last_aired"))
    assert end and series["s4"][-1][3] == end, \
        "the infobox ends the series on %s but series 4 closed %s" \
        % (end, series["s4"][-1][3])

    # --- rows
    def series_section(page, sid, title):
        rows = series[sid]
        return {
            "id": sid,
            "title": title,
            "sub": prop.join_bits(year_span([r[3][0] for r in rows]),
                                  "%d episodes" % len(rows)),
            "items": [{"id": "ba-%s-%d" % (sid, r[1]), "t": r[2],
                       "n": str(r[1])} for r in rows],
            "_first": rows[0][3],
        }

    sections = [series_section(*SERIES[0]), series_section(*SERIES[1]),
                series_section(*SERIES[2])]

    sections.append({
        "id": "specials",
        "title": "The 1988 specials",
        "sub": prop.join_bits(year_span([d[0] for _t, _p, d in specials]),
                              "%d specials" % len(specials)),
        "items": [{"id": "ba-sp-%d" % (i + 1), "t": t,
                   "n": str(i + 1),
                   "note": prop.join_bits(fmt_date(d),
                                          "%d minutes" % minutes(page))}
                  for i, (t, page, d) in enumerate(specials)],
        "_first": specials[0][2],
    })

    sections.append(series_section(*SERIES[3]))

    sections.append({
        "id": "bf",
        "title": "Back & Forth",
        "sub": prop.join_bits(str(back_forth[2][0]), "1 special"),
        # a one-off row takes its year as its number, as deadwood's film does;
        # an absent `n` renders the string "undefined" on the card
        "items": [{"id": "ba-back-and-forth", "t": back_forth[0],
                   "n": str(back_forth[2][0]),
                   "note": prop.join_bits(fmt_date(back_forth[2]),
                                          "%d minutes"
                                          % minutes(back_forth[1]))}],
        "_first": back_forth[2],
    })

    sections.append({
        "id": "pilot",
        "title": "The pilot",
        "sub": "recorded 1982, screened %d · 1 episode" % pilot[2][0],
        "items": [{"id": "ba-pilot", "t": pilot[0], "n": str(pilot[2][0]),
                   "note": prop.join_bits("Taped 1982, first screened %s"
                                          % fmt_date(pilot[2]),
                                          "%d minutes" % minutes(pilot[1]),
                                          "its story was reused for Born to "
                                          "Be King")}],
        "_first": pilot[2],
    })

    for sid, intro in INTRO.items():
        sec = next(s for s in sections if s["id"] == sid)
        sec["intro"] = intro
    sections[0]["open"] = True

    # broadcast order across the whole list: every section starts later than
    # the one before it, which is what puts the specials mid-run and the pilot
    # at the end rather than either of them being bolted on by hand
    firsts = [s.pop("_first") for s in sections]
    assert firsts == sorted(firsts), \
        "the sections are not in broadcast order: %s" % (firsts,)

    total = sum(len(s["items"]) for s in sections)
    assert total == TOTAL, (total, TOTAL)
    assert sum(1 for s in sections for x in s["items"] if "w" in x) == 0, \
        "a weight crept in — this list is unweighted end to end"
    assert all(x.get("n") for s in sections for x in s["items"]), \
        "a row has no number — the card would print the word undefined"

    p = {
        "slug": SLUG,
        "title": "Blackadder",
        "subtitle": "four series, the two 1988 specials, Back & Forth and the pilot",
        "kind": "tv",
        "popularity": 63,
        "year": "1983–2023",
        "blurb": "Every Blackadder the source counts — 24 episodes across four "
                 "eras, plus the four specials, in the order they were shown.",
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ["Four series, four specials.", "Wikipedia's infobox counts \"24 "
             "(plus 4 specials)\" and this list is both halves of that: the "
             "four six-episode series, the two 1988 one-offs, Back & Forth, "
             "and the pilot. Nothing here is a documentary, a charity sketch "
             "or an after-dinner turn — the source keeps those in two separate "
             "tables and so does this."],
            ["The specials sit where they aired.", "The Cavalier Years went "
             "out in February 1988 and Blackadder's Christmas Carol that "
             "December, in the gap between series 3 and series 4. They are a "
             "section in that gap rather than an appendix at the end, which is "
             "also how the source's series overview files them."],
            ["The pilot is last, on purpose.", "It was taped in 1982, shelved, "
             "and first screened in June 2023 — forty years after the series "
             "began. This list is in broadcast order, so that is where it "
             "goes. Its story was reused for Born to Be King, so it is a "
             "curiosity rather than a missing first episode."],
            ["Series 1's own order is disputed by the source.", "The episode "
             "table dates Born to Be King as the second episode, 22 June "
             "1983; a note on the same page says transmission actually swapped "
             "the second and fourth episodes because it was not ready. The "
             "rows follow the table's dates, because those are the field the "
             "encyclopedia records per episode, and the disagreement is "
             "flagged here rather than quietly picked."],
            ["Nothing is weighted.", "Each series publishes one running time "
             "and no episode publishes its own, so there is no verifiable "
             "per-row figure and every row counts one. The four specials do "
             "each give a length on their own article and those minutes are in "
             "the row notes — but weighting four rows out of 28 would make the "
             "other 24 count as a full hour each, which is worse than counting "
             "nothing."],
            "Titles, numbering and airdates machine-read from Wikipedia's "
            "List of Blackadder episodes and the four series articles it "
            "transcludes, with each special's length from its own article; the "
            "numbering is asserted contiguous 1–24, every section asserted to "
            "start later than the one before, and the total cross-checked "
            "against the series infobox before this builds.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d rows in %d sections" % (out.name, total, len(sections)))
    for s in sections:
        print("   %-32s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
