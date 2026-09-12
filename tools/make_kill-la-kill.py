#!/usr/bin/env python3
"""Generate properties/kill-la-kill.json — the 2013-14 run, plus the OVA.

    PYTHONIOENCODING=utf-8 python tools/make_kill-la-kill.py
    PYTHONIOENCODING=utf-8 python tools/make_kill-la-kill.py --harvest

Trigger's twenty-four-episode run, October 4, 2013 to March 28, 2014, in
broadcast order, plus the one original video animation episode the source's own
table carries. 25 rows.

Without `--harvest` this reads only the two committed data files beside it and
touches no network, so it is byte-reproducible:

    tools/data/kill-la-kill-episodes.json       the table, the infoboxes, the
                                                sentences this list rests on,
                                                and the runtime-absence evidence
    tools/data/kill-la-kill-runtime-hunt.json   the weights hunt: every page
                                                name asked for, every Wikidata
                                                item, and what each answered

With `--harvest` it refetches both English articles from Wikipedia, re-runs the
whole weights hunt against Wikipedia and Wikidata, rewrites both data files,
and then builds — so every assertion below is checked against the live source
rather than against last week's copy of it. The wikitext cache lives in
scratch/agent-klk/cache (gitignored); the data files are the committed record.

THE OVA IS A ROW, AND IT IS OPTIONAL. THAT IS THE SCOPE DECISION.
Both infoboxes count the run as "24 + OVA" rather than 24 or 25, and the
episode table's twenty-fifth {{Episode list}} block is numbered literally
"OVA" — not 25. It is new animation rather than a re-cut of anything: the
series article says the nine home-media volumes ran from January 8, 2014 to
September 3, 2014 "with an [[original video animation]] episode included on
the final volume", and the Japanese home-media table's last row reads
"24 + OVA (25)". So it is a thing to watch that nothing else on this list
covers, and leaving it off would make the list incomplete in the one direction
the source is explicit about.

It is marked `opt` because it never went out on television, is not one of the
twenty-four, and reached shops five months after the run closed. Twenty-four
rows are required; the twenty-fifth is an extra.

The decision is one constant. Set INCLUDE_OVA = False and the OVA section
disappears, the count claims fall back to twenty-four, and the notes say the
OVA is deliberately absent instead of saying it is optional. Nothing else moves
and no id is reused, so flipping it back restores every tick.

THE OVA'S ID IS `klk-ova`, NEVER A NUMBER. The source numbers it "OVA"; the
home-media table calls it 25 in passing and the Japanese article calls it 最終25話.
Either of those would collide with a future episode 25 and, worse, `int()` on
the field gives nothing at all — gwlib's parsed `num_overall` is None here. The
number is read from the raw wikitext as written and the id is built from the
word, so a row can never silently land on top of another one.

THE OVA'S TITLE CARRIES AN ANCHOR AND THE PARSER EATS IT. The field reads
`Title = Goodbye Again{{anchor|ep25|epOVA}}`, and clean()'s keep-the-last-
argument rule turns that into "Goodbye AgainepOVA" — a title no source has
ever printed, on the one row of this list a reader has to look for. The anchor
is stripped before cleaning, and main() asserts the anchor is still there: if
Wikipedia drops it the strip is dead code and someone should know.

WEIGHTS: NONE, AND IT IS ALL-OR-NOTHING (CLU-131). The full hunt was run and
every source came up empty. This list is emptier than Gurren Lagann's, which
at least had a series-level average to refuse:

  1. no episode has its own English Wikipedia article. All 25 titles were
     asked for directly, in three forms each — bare, "(Kill la Kill)" and
     "(Kill la Kill episode)", 75 page names — and the eleven that resolve are
     all the unrelated songs and films the titles are borrowed from. That trap
     is specific to this series: every episode is named after a Japanese pop
     song, so "Trigger", "Incomplete" and "Don't Stop Me Now" all hit real
     articles. Each of the eleven was opened: none is in a Kill la Kill
     category and none mentions the series in its intro. A hunt that counted a
     resolved page name as a find would have weighed episode 5 at the length of
     a Christopher Cross single.
  2. no episode has a Wikidata item at all — nothing that is a
     television-series episode points at the series — and the series item
     Q13637192 carries NO P2047 statement of any kind, not even the unqualified
     series-level average Q4277 has. Nothing else Wikidata files under the
     series carries a duration either.
  3. neither article has a runtime field anywhere: not the series article's
     {{Infobox animanga/Video}}, not the episode list's {{Infobox television
     season}}, and no `runtime =` line on either page.
  4. not one of the 25 {{Episode list}} blocks carries a RunTime.

The Japanese article was read as well, since a Japanese anime article often
states a broadcast slot, and it states no length either. So there is no figure
to weigh from — not a measured one, not an average, not a slot. It has to be
every row or no row, because a row with no `w` on a weighted list resolves to
a full hour and twenty-five of those would claim twenty-five hours for about
ten hours of television. It is no row, every episode counts one, and the notes
say all of this rather than implying it.

If the catalogue ever rules that a house constant may stand in for a source —
cowboy-bebop, ghost-in-the-shell and urusei-yatsura all weigh an episode at a
flat 0.4 hours with no citation for it — set EPISODE_HOURS to that figure and
the weights note rewrites itself to say the number is a house estimate and not
a measurement. Nothing here will invent one on its own.

THE SECTION SPLIT IS THE SOURCE'S, NOT A READING OF THE STORY. The episode
list article says the opening and ending themes change: "For the first fifteen
episodes" one pair, "From episode sixteen onwards" another. Both numbers are
read out of that prose and asserted adjacent, so the two television sections
are a production fact about the broadcast rather than anything about what
happens in it.

Everything is machine-read. Nothing on this list is typed from memory, and
where a claim in the brief disagreed with the source the source won: the brief
called this "a later OVA episode", and the source dates it inside the same
home-media release schedule as the broadcast run rather than later than it.
"""
import hashlib
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki  # noqa: E402

SLUG = "kill-la-kill"
HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "data" / "kill-la-kill-episodes.json"
HUNT = HERE / "data" / "kill-la-kill-runtime-hunt.json"
CACHE = prop.ROOT / "scratch" / "agent-klk" / "cache"

LIST_PAGE = "List of Kill la Kill episodes"
SERIES_PAGE = "Kill la Kill"
JA_PAGE = "キルラキル"
JA_API = "https://ja.wikipedia.org/w/api.php"
WD_SPARQL = "https://query.wikidata.org/sparql"

# ---- the two switches this list is steered by ----------------------------
INCLUDE_OVA = True      # the scope decision; see the docstring
EPISODE_HOURS = None    # None = unweighted. Nothing here will guess a figure.

BROADCAST = 24          # asserted three ways: both infoboxes and Wikidata
OVA_NUMBER = "OVA"      # the source's literal EpisodeNumber, never 25
OVA_ID = "klk-ova"
FIRST_AIRED = (2013, 10, 4)
LAST_AIRED = (2014, 3, 28)
OVA_RELEASED = (2014, 9, 3)
# The run took a three-week new-year break. Asserted as exactly one gap so a
# re-harvest that loses or gains a week fails instead of shipping quietly.
BREAK_AFTER = 12
BREAK_DAYS = 21
HOME_MEDIA_VOLUMES = 9
SERIES_QID = "Q13637192"

# The episode list's own {{Infobox television season}} bg_colour, read from the
# source rather than chosen, and the dark half a lightened tone of it. Both
# halves asserted unused by every other list.
ACCENT = "#880808"
ACCENT_DARK = "#F4756B"

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
MONTHNUM = {m: i for i, m in enumerate(MONTHS, 1)}

_ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven",
         "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
         "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50}


def word2num(w):
    """"twenty-four" -> 24. The source writes two of its counts as words."""
    w = (w or "").strip().lower().replace("–", "-")
    if w in _ONES:
        return _ONES.index(w)
    head, _, tail = w.partition("-")
    assert head in _TENS, "cannot read %r as a number" % w
    return _TENS[head] + (_ONES.index(tail) if tail else 0)


def num2word(n):
    """24 -> "twenty-four". Prose counts in the notes are written from the
    asserted number rather than typed beside it, so they cannot drift apart."""
    if n < len(_ONES):
        return _ONES[n]
    tens = {v: k for k, v in _TENS.items()}
    assert n // 10 * 10 in tens, "cannot spell %d" % n
    head = tens[n // 10 * 10]
    return head if n % 10 == 0 else "%s-%s" % (head, _ONES[n % 10])


def fmt_date(d):
    return "%s %d, %d" % (MONTHS[d[1] - 1], d[2], d[0])


def ordinal_word(n):
    words = {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth",
             6: "sixth", 7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth"}
    assert n in words, "no ordinal word for %d" % n
    return words[n]


def days_between(a, b):
    """Whole days from date tuple a to b. datetime would do, but the dates in
    this file are read as tuples everywhere else and one representation is
    fewer places to get it wrong."""
    import datetime
    return (datetime.date(*b) - datetime.date(*a)).days


def strip_refs(t):
    """Prose with the footnotes gone, for the sentences main() reads as fact."""
    t = re.sub(r"<ref[^>]*/>", "", t or "")
    t = re.sub(r"<ref.*?</ref>", "", t, flags=re.S)
    return re.sub(r"\{\{efn.*?\}\}", "", t, flags=re.S)


def raw_field(block, name):
    """One {{Episode list}} field exactly as written.

    The numbering is always read from here and never through gwlib's parsed
    EpisodeNumber: this table's last row states "OVA", which int() cannot read
    at all, so the parsed number is None and a row keyed on it would be keyed
    on nothing."""
    m = re.search(r"\|\s*%s\s*=\s*(.*?)(?=\n\s*\||\Z)" % name, block, re.S)
    return m.group(1).strip() if m else ""


def date_in(chunk, kind="Start"):
    """The first {{Start date}} / {{End date}} in a chunk, as (y, m, d)."""
    m = re.search(r"\{\{%s date\s*\|\s*(\d{4})\s*\|\s*(\d{1,2})\s*\|"
                  r"\s*(\d{1,2})" % kind, chunk or "", re.I)
    assert m, "no %s date in %r" % (kind.lower(), (chunk or "")[:80])
    return tuple(int(g) for g in m.groups())


def plain_date(s):
    """"October 4, 2013" -> (2013, 10, 4)."""
    m = re.search(r"([A-Z][a-z]+)\s+(\d{1,2}),\s*(\d{4})", s or "")
    assert m, "no plain date in %r" % (s or "")[:60]
    return (int(m.group(3)), MONTHNUM[m.group(1)], int(m.group(2)))


def brace_block(t, start):
    """The balanced {{...}} beginning at `start`.

    A split on a line-leading `}}` is wrong on the series article: the animanga
    infobox nests {{English anime licensee}} and {{English anime network}}
    blocks whose closing braces sit at column zero, and a split-based reader
    truncates every field after them — which is where the episode count lives.
    """
    depth, i = 0, start
    while i < len(t):
        if t.startswith("{{", i):
            depth, i = depth + 1, i + 2
        elif t.startswith("}}", i):
            depth, i = depth - 1, i + 2
            if depth == 0:
                return t[start:i]
        else:
            i += 1
    raise AssertionError("unbalanced braces from offset %d" % start)


def infobox_fields(block):
    """{field: value} for one template, split only on top-level pipes.

    Nested templates close two at a time and wikilinks carry pipes at template
    depth zero (`network = [[MBS TV|MBS]]`), so `{{`/`}}` and `[[`/`]]` are both
    counted, two characters at a step."""
    body = block[2:-2]
    fields, depth, buf, i, n = {}, 0, "", 0, len(body)

    def flush(chunk):
        if "=" in chunk:
            k, v = chunk.split("=", 1)
            fields[k.strip().lower()] = v.strip()

    while i < n:
        two = body[i:i + 2]
        if two in ("{{", "[["):
            depth, buf, i = depth + 1, buf + two, i + 2
        elif two in ("}}", "]]"):
            depth, buf, i = depth - 1, buf + two, i + 2
        elif body[i] == "|" and depth == 0:
            flush(buf)
            buf, i = "", i + 1
        else:
            buf, i = buf + body[i], i + 1
    flush(buf)
    return fields


# ==========================================================================
# the harvest: everything this list rests on, read out of the live source
# ==========================================================================

def harvest():
    """Refetch both articles, re-run the weights hunt, rewrite both data
    files. Raises rather than recording anything it cannot read."""
    import time
    import urllib.parse
    from gwlib import wikidata

    texts = {}
    for page in (SERIES_PAGE, LIST_PAGE):
        t = wiki.wikitext(page, cache_dir=CACHE)
        assert t, "no wikitext for %r" % page
        texts[page] = t

    series_text, list_text = texts[SERIES_PAGE], texts[LIST_PAGE]

    # ---- the episode table ----------------------------------------------
    a, b = list_text.find("==Episode list=="), list_text.find("==Notes==")
    assert 0 <= a < b, \
        "the list article's Episode list / Notes headings have moved — the " \
        "slice this list reads its rows out of is no longer valid"
    seg = list_text[a:b]

    rows = []
    for e in wiki.episodes(seg):
        n = raw_field(e.block, "EpisodeNumber")
        raw_title = raw_field(e.block, "Title")
        anchor = re.search(r"\{\{\s*anchor\s*\|([^}]*)\}\}", raw_title, re.I)
        title = wiki.clean(re.sub(r"\{\{\s*anchor\s*\|[^}]*\}\}", "",
                                 raw_title, flags=re.I)).strip().strip('"')
        assert n and title, "incomplete episode row: %r" % (n or title)[:60]
        assert not raw_field(e.block, "RunTime"), \
            "episode %s documents a runtime now — revisit weights, because " \
            "the only reason this list is unweighted is that no episode had " \
            "one" % n
        rows.append({
            "n": n,
            "t": title,
            "anchor": anchor.group(1) if anchor else None,
            "translit": wiki.clean(raw_field(e.block, "TranslitTitle")),
            "aired": list(date_in(raw_field(e.block, "OriginalAirDate"))),
            "airdate_raw": raw_field(e.block, "OriginalAirDate"),
            "directed": wiki.clean(raw_field(e.block, "DirectedBy")),
            "storyboard": wiki.clean(raw_field(e.block, "Aux2")),
        })

    # ---- the infoboxes ---------------------------------------------------
    season = wiki.infobox(list_text, kind=r"television season")
    assert season, "the list article has no {{Infobox television season}}"
    season_box = {
        "num_episodes": season("num_episodes"),
        "first_aired": list(date_in(season("first_aired"))),
        "last_aired": list(date_in(season("last_aired"), "End")),
        "bg_colour": season("bg_colour"),
    }

    videos = [infobox_fields(brace_block(series_text, m.start()))
              for m in re.finditer(r"\{\{Infobox animanga/Video", series_text)]
    assert len(videos) == 1, \
        "the series article carries %d animanga video infoboxes, not the one " \
        "television series this list knows — something has been announced or " \
        "released and the shape of this list needs deciding on before it " \
        "builds" % len(videos)
    tv = videos[0]
    assert not tv.get("runtime"), \
        "the television infobox documents a running time now — revisit " \
        "weights, because the only reason this list is unweighted is that " \
        "nothing anywhere had one"
    series_box = {
        "episodes": tv.get("episodes", ""),
        "first": tv.get("first", ""),
        "last": tv.get("last", ""),
        "studio": tv.get("studio", ""),
        "episode_list": tv.get("episode_list", ""),
    }

    prints = [infobox_fields(brace_block(series_text, m.start())).get("type", "")
              for m in re.finditer(r"\{\{Infobox animanga/Print", series_text)]

    # ---- the sentences this list rests on --------------------------------
    clean_list = strip_refs(list_text)
    themes = {}
    m = re.search(r"For the first ([a-z]+) episodes, the opening theme is "
                  r"\{\{nihongo\|\"([^\"]+)\"", clean_list, re.I)
    assert m, "the list article no longer says where the first opening theme " \
              "runs to — the two television sections are that sentence"
    themes["first_block"] = word2num(m.group(1))
    themes["first_opening"] = m.group(2)
    m = re.search(r"From episode ([a-z]+) onwards, the opening theme is "
                  r"\"([^\"]+)\"", clean_list, re.I)
    assert m, "the list article no longer says where the second opening " \
              "theme starts"
    themes["from_episode"] = word2num(m.group(1))
    themes["second_opening"] = m.group(2)

    m = re.search(r"The title of each episode is named after a Japanese "
                  r"classical pop song selected from within the iTunes "
                  r"collection of ''Kill la Kill'' head writer "
                  r"\[\[([^\]|]+)", clean_list)
    assert m, "the list article no longer says the episode titles are song " \
              "titles — that sentence is a note on this list and is also why " \
              "eleven of the titles collide with unrelated articles"
    songs_writer = m.group(1)

    m = re.search(r"The series was released on ([a-z]+) home media volumes "
                  r"between ([A-Z][a-z]+ \d{1,2}, \d{4}), and "
                  r"([A-Z][a-z]+ \d{1,2}, \d{4}), with an "
                  r"\[\[original video animation\]\] episode included on the "
                  r"final volume\.", clean_list)
    assert m, "the list article no longer ties the OVA to the last home " \
              "media volume — that sentence is why the OVA is a row at all"
    ova_evidence = {"volumes": word2num(m.group(1)),
                    "first_volume": list(plain_date(m.group(2))),
                    "last_volume": list(plain_date(m.group(3)))}

    clean_series = strip_refs(series_text)
    m = re.search(r"An \[\[original video animation\]\] episode was released "
                  r"as part of the ([a-z]+) volume on "
                  r"([A-Z][a-z]+ \d{1,2}, \d{4})\.", clean_series)
    assert m, "the series article no longer dates the OVA's release"
    ova_evidence["volume_ordinal"] = m.group(1)
    ova_evidence["released"] = list(plain_date(m.group(2)))

    # the Japanese home-media table, whose last row counts the OVA as 25
    # Bounded at the table's own close, not at a character count: the English
    # section holds a second volume table directly under this one, and a fixed
    # window swallowed it and counted seventeen volumes.
    i = clean_series.find("Aniplex (Region A/2)")
    assert i > 0, "the series article's Japanese home media table has moved"
    j = clean_series.find("\n|}", i)
    assert j > i, "the Japanese home media table is not closed"
    vol_rows = re.findall(r"\|Volume (\d+)\s*\n\|([^\n]+)\s*\n\|([^\n]+)",
                          clean_series[i:j])
    assert len(vol_rows) == HOME_MEDIA_VOLUMES, \
        "the Japanese home media table holds %d volumes, expected %d" \
        % (len(vol_rows), HOME_MEDIA_VOLUMES)

    # ---- what is deliberately absent ------------------------------------
    m = re.search(r"A \[\[manga\]\] adaptation by .*? started in .*? on "
                  r"([A-Z][a-z]+ \d{1,2}, \d{4}), and concluded with "
                  r"(\d+) chapters on ([A-Z][a-z]+ \d{1,2}, \d{4})\.",
                  clean_series, re.S)
    assert m, "the series article no longer describes the manga the notes " \
              "name as deliberately absent"
    manga = {"first": list(plain_date(m.group(1))), "chapters": int(m.group(2)),
             "last": list(plain_date(m.group(3)))}
    m = re.search(r"Its chapters were collected in ([a-z]+) "
                  r"\{\{Transliteration\|ja\|\[\[tank", clean_series)
    assert m, "the series article no longer counts the manga's volumes"
    manga["volumes"] = word2num(m.group(1))

    m = re.search(r"It was released on .*? in Japan on "
                  r"([A-Z][a-z]+ \d{1,2}, \d{4}), and in North America and "
                  r"Europe the next day\.", clean_series, re.S)
    assert m, "the series article no longer dates the video game the notes " \
              "name as deliberately absent"
    m2 = re.search(r"A video game adaptation titled \{\{Nihongo\|''([^']+)''",
                   clean_series)
    assert m2, "the series article no longer names the video game"
    game = {"title": m2.group(1), "released": list(plain_date(m.group(1)))}

    # ---- (3) and (4): every runtime field on either page -----------------
    absence = {
        "runtime_lines_series": re.findall(
            r"^\s*\|\s*runtime\s*=\s*(.*)$", series_text, re.M | re.I),
        "runtime_lines_list": re.findall(
            r"^\s*\|\s*runtime\s*=\s*(.*)$", list_text, re.M | re.I),
        "episode_runtime_fields": re.findall(
            r"\|\s*RunTime\s*=\s*([^\n|]*)", list_text, re.I),
        "minutes_on_series_article": re.findall(
            r"\b(\d{1,3})\s+minutes?\b", clean_series),
        "minutes_on_list_article": re.findall(
            r"\b(\d{1,3})\s+minutes?\b", clean_list),
    }
    assert absence["runtime_lines_series"] == [], \
        "the series article carries runtime fields now: %r" \
        % absence["runtime_lines_series"]
    assert absence["runtime_lines_list"] == [], \
        "the list article carries runtime fields now: %r" \
        % absence["runtime_lines_list"]
    assert absence["episode_runtime_fields"] == [], \
        "an {{Episode list}} block carries a RunTime now — revisit weights"
    assert absence["minutes_on_series_article"] == [], \
        "the series article states a length in minutes now (%r) — revisit " \
        "weights" % absence["minutes_on_series_article"]
    # The list article's plot summaries say "fifteen minutes" and "five
    # minutes" in words; a FIGURE in minutes would be new and would be a
    # running time or something close enough to read before this ships.
    assert absence["minutes_on_list_article"] == [], \
        "the episode list states a figure in minutes now (%r) — revisit " \
        "weights" % absence["minutes_on_list_article"]

    data = {
        "pages": {p: {"chars": len(t),
                      "sha256": hashlib.sha256(t.encode("utf-8")).hexdigest()}
                  for p, t in sorted(texts.items())},
        "fetched_via": "en.wikipedia.org/w/api.php action=parse prop=wikitext",
        "episodes": rows,
        "season_infobox": season_box,
        "series_infobox": series_box,
        "print_infobox_types": prints,
        "themes": themes,
        "songs_head_writer": songs_writer,
        "ova_evidence": ova_evidence,
        "home_media_jp": [list(r) for r in vol_rows],
        "manga": manga,
        "game": game,
        "runtime_absence": absence,
    }
    DATA.write_text(json.dumps(data, indent=1, ensure_ascii=False,
                               sort_keys=True) + "\n", encoding="utf-8")
    print("harvested %s — %d episode rows" % (DATA.name, len(rows)))

    # ======================================================================
    # (1) and (2): the weights hunt
    # ======================================================================
    names = []
    for r in rows:
        names += [r["t"], "%s (Kill la Kill)" % r["t"],
                  "%s (Kill la Kill episode)" % r["t"]]

    resolved = {}
    for i in range(0, len(names), 40):
        chunk = names[i:i + 40]
        q = urllib.parse.urlencode({
            "action": "query", "format": "json", "formatversion": "2",
            "redirects": "1", "titles": "|".join(chunk)})
        d = wiki.get_json(wiki.API + "?" + q)
        time.sleep(1.5)
        norm = {}
        for k in ("normalized", "redirects"):
            for mm in d.get("query", {}).get(k, []):
                norm[mm["from"]] = mm["to"]
        missing = {p["title"] for p in d["query"]["pages"] if p.get("missing")}
        for c in chunk:
            x = c
            while x in norm:
                x = norm[x]
            if x not in missing:
                resolved[c] = x

    # Every resolved name is opened. On this series a resolved name is the
    # DEFAULT rather than the exception, because the episode titles are pop
    # song titles, so "it resolves" proves nothing on its own.
    checked = {}
    targets = sorted(set(resolved.values()))
    if targets:
        q = urllib.parse.urlencode({
            "action": "query", "format": "json", "formatversion": "2",
            "redirects": "1", "prop": "categories|extracts", "cllimit": "max",
            "exintro": "1", "explaintext": "1", "exlimit": "20",
            "titles": "|".join(targets)})
        d = wiki.get_json(wiki.API + "?" + q)
        time.sleep(1.5)
        by = {p["title"]: p for p in d["query"]["pages"]}
        for name in targets:
            p = by.get(name, {})
            cats = [c["title"] for c in p.get("categories", [])]
            intro = (p.get("extract") or "").strip()
            checked[name] = {
                "kill_la_kill_categories": [c for c in cats
                                            if "Kill la Kill" in c],
                "intro_mentions_series": "Kill la Kill" in intro,
                "intro_opens": intro.split(". ")[0][:200],
            }

    qids = wikidata.qids_for([SERIES_PAGE, LIST_PAGE])
    claims = wikidata.claims_for(list(qids.values()))
    wd = {}
    for page, qid in sorted(qids.items()):
        c = claims.get(qid, {})
        wd[page] = {
            "qid": qid,
            "runtime_statements": wikidata.runtime_values(c),
            "num_episodes": [
                int(str(s["mainsnak"]["datavalue"]["value"]["amount"])
                    .lstrip("+"))
                for s in c.get("P1113", [])
                if s.get("mainsnak", {}).get("datavalue")],
        }

    def sparql(query):
        q = urllib.parse.urlencode({"query": query, "format": "json"})
        return wiki.get_json(WD_SPARQL + "?" + q)["results"]["bindings"]

    qid = qids[SERIES_PAGE]
    orbit = [{"item": r["item"]["value"].rsplit("/", 1)[-1],
              "label": r.get("itemLabel", {}).get("value"),
              "class": r.get("clsLabel", {}).get("value"),
              "runtime": r.get("rt", {}).get("value")}
             for r in sparql("""
SELECT ?item ?itemLabel ?cls ?clsLabel ?rt WHERE {
  { ?item wdt:P179 wd:%s } UNION { ?item wdt:P361 wd:%s }
  UNION { ?item wdt:P1441 wd:%s } UNION { ?item wdt:P4908 wd:%s }
  UNION { ?item wdt:P155|wdt:P156 wd:%s }
  OPTIONAL { ?item wdt:P31 ?cls }
  OPTIONAL { ?item wdt:P2047 ?rt }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}""" % (qid, qid, qid, qid, qid))]

    episode_items = [{"item": r["item"]["value"].rsplit("/", 1)[-1],
                      "label": r.get("itemLabel", {}).get("value"),
                      "runtime": r.get("rt", {}).get("value")}
                     for r in sparql("""
SELECT ?item ?itemLabel ?rt WHERE {
  ?item wdt:P31/wdt:P279* wd:Q21191270 .
  { ?item wdt:P179 wd:%s } UNION { ?item wdt:P1441 wd:%s }
  UNION { ?item wdt:P361 wd:%s }
  OPTIONAL { ?item wdt:P2047 ?rt }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}""" % (qid, qid, qid))]

    jq = urllib.parse.urlencode({"action": "parse", "page": JA_PAGE,
                                "prop": "wikitext", "format": "json",
                                "formatversion": "2", "redirects": "1"})
    jd = wiki.get_json(JA_API + "?" + jq)
    ja = "" if "error" in jd else jd["parse"]["wikitext"]
    assert len(ja) > 10000, "the Japanese article came back empty"
    (CACHE).mkdir(parents=True, exist_ok=True)
    (CACHE / "ja-kill-la-kill.wiki").write_text(ja, encoding="utf-8")
    ja_box = re.search(r"\{\{Infobox animanga/TVAnime.*?\n\}\}", ja, re.S)
    assert ja_box, "the Japanese article's television infobox has moved"
    ja_slot = re.findall(r"^\|\s*放送時間\s*=\s*(.*)$", ja_box.group(0), re.M)

    hunt = {
        "series_qid": qid,
        "article_names_checked": sorted(names),
        "article_names_resolved": resolved,
        "resolved_names_are_not_episodes": checked,
        "wikidata": wd,
        "orbit": orbit,
        "episode_items": episode_items,
        "with_runtime": [o for o in orbit if o["runtime"]]
                        + [e for e in episode_items if e["runtime"]],
        "ja_article_chars": len(ja),
        "ja_broadcast_slot_field": ja_slot,
        "ja_minute_figures_in_infobox": re.findall(r"(\d{1,3})分",
                                                   ja_box.group(0)),
    }
    HUNT.write_text(json.dumps(hunt, indent=1, ensure_ascii=False,
                               sort_keys=True) + "\n", encoding="utf-8")
    print("hunted %s — %d page names asked, %d resolved, %d episode items"
          % (HUNT.name, len(names), len(resolved), len(episode_items)))


# ==========================================================================
# the build: assertions over the committed data, then the property
# ==========================================================================

def load(path, what):
    assert path.exists(), \
        "%s is missing — run `python tools/make_kill-la-kill.py --harvest`; " \
        "%s" % (path, what)
    return json.loads(path.read_text(encoding="utf-8"))


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


def check_rows(data):
    """Numbering, titles, dates — contiguous, in order, and the OVA apart."""
    rows = data["episodes"]
    listed = BROADCAST + 1
    assert len(rows) == listed, \
        "the episode table holds %d rows, expected %d (%d broadcast plus the " \
        "OVA)" % (len(rows), listed, BROADCAST)

    numbers = [r["n"] for r in rows]
    assert numbers.count(OVA_NUMBER) == 1, \
        "the table holds %d rows numbered %r, expected exactly one" \
        % (numbers.count(OVA_NUMBER), OVA_NUMBER)
    assert numbers[-1] == OVA_NUMBER, \
        "the OVA is no longer the last row of the table (%r)" % numbers[-1]
    assert numbers[:-1] == [str(i) for i in range(1, BROADCAST + 1)], \
        "broadcast numbering is not a plain contiguous 1..%d: %r" \
        % (BROADCAST, numbers[:-1])
    assert all(r["t"] for r in rows), "a row parsed with no title"
    assert len({r["t"] for r in rows}) == listed, \
        "two rows share a title: %r" % sorted(
            t for t in (r["t"] for r in rows)
            if [x["t"] for x in rows].count(t) > 1)

    # The OVA's title is the one this table cannot be read naively: its Title
    # field carries an {{anchor}} whose last argument clean() would keep.
    ova = rows[-1]
    assert ova["anchor"], \
        "the OVA row no longer carries the {{anchor}} this generator strips " \
        "— the strip is now dead code and the title should be re-read"
    assert "ep" in ova["anchor"], \
        "the OVA's anchor is %r, not the ep25/epOVA pair this knows" \
        % ova["anchor"]
    assert not re.search(r"ep(25|OVA)$", ova["t"]), \
        "the OVA's title is %r — the anchor leaked into it" % ova["t"]

    # dates: broadcast weekly and in order, with exactly one longer gap
    dates = [tuple(r["aired"]) for r in rows[:-1]]
    assert dates == sorted(dates), "broadcast air dates are out of order"
    assert dates[0] == FIRST_AIRED and dates[-1] == LAST_AIRED, \
        "the run reads %s to %s, expected %s to %s" \
        % (dates[0], dates[-1], FIRST_AIRED, LAST_AIRED)
    gaps = [(i + 1, days_between(dates[i], dates[i + 1]))
            for i in range(len(dates) - 1)]
    long_gaps = [g for g in gaps if g[1] != 7]
    assert long_gaps == [(BREAK_AFTER, BREAK_DAYS)], \
        "the broadcast run's non-weekly gaps are %r, expected exactly one " \
        "%d-day break after episode %d" % (long_gaps, BREAK_DAYS, BREAK_AFTER)

    ova_date = tuple(ova["aired"])
    assert ova_date == OVA_RELEASED, \
        "the OVA is dated %r, expected %r" % (ova_date, OVA_RELEASED)
    assert ova_date > dates[-1], \
        "the OVA is dated inside the broadcast run — it is listed as a home " \
        "media release after the run closed"
    # The row's own air-date field says where it went out, and the whole reason
    # it is optional is that the answer is "nowhere".
    assert "Home media only" in ova["airdate_raw"], \
        "the OVA's air-date field reads %r and no longer says it is home " \
        "media only — if it aired somewhere it is not optional any more" \
        % ova["airdate_raw"]
    for r in rows[:-1]:
        assert "Home media" not in r["airdate_raw"], \
            "episode %s is marked home media only now — the broadcast run " \
            "is what the required rows are" % r["n"]
    return rows


def check_count(data, hunt):
    """The episode count, twice from the articles and once from Wikidata."""
    stated = "%d + %s" % (BROADCAST, OVA_NUMBER)
    assert data["season_infobox"]["num_episodes"] == stated, \
        "the season infobox counts %r episodes, expected %r" \
        % (data["season_infobox"]["num_episodes"], stated)
    assert data["series_infobox"]["episodes"] == stated, \
        "the series infobox counts %r episodes, expected %r" \
        % (data["series_infobox"]["episodes"], stated)
    wd = hunt["wikidata"][SERIES_PAGE]
    assert wd["qid"] == SERIES_QID, \
        "the series' Wikidata item is %r, not %r" % (wd["qid"], SERIES_QID)
    assert wd["num_episodes"] == [BROADCAST], \
        "Wikidata %s records %r episodes, expected [%d]" \
        % (SERIES_QID, wd["num_episodes"], BROADCAST)
    return stated


def check_dates_agree(data):
    """Both infoboxes' first and last aired, against the table."""
    assert tuple(data["season_infobox"]["first_aired"]) == FIRST_AIRED
    assert tuple(data["season_infobox"]["last_aired"]) == LAST_AIRED
    assert plain_date(data["series_infobox"]["first"]) == FIRST_AIRED, \
        "the series infobox first aired %r" % data["series_infobox"]["first"]
    assert plain_date(data["series_infobox"]["last"]) == LAST_AIRED, \
        "the series infobox last aired %r" % data["series_infobox"]["last"]
    assert data["season_infobox"]["bg_colour"].upper() == ACCENT.upper(), \
        "the season infobox's colour is %r, and this list's accent is read " \
        "from it" % data["season_infobox"]["bg_colour"]


def check_themes(data):
    """The two television sections are the source's own theme-music split."""
    t = data["themes"]
    assert t["from_episode"] == t["first_block"] + 1, \
        "the source's theme change reads %r then %r — the two sections are " \
        "no longer adjacent" % (t["first_block"], t["from_episode"])
    assert 1 < t["first_block"] < BROADCAST, \
        "the theme change sits at episode %r, outside the run" \
        % t["first_block"]
    return t["first_block"]


def check_ova_evidence(data):
    """Why the OVA is a row: a home-media release of new animation."""
    ev = data["ova_evidence"]
    assert ev["volumes"] == HOME_MEDIA_VOLUMES, \
        "the source counts %r home media volumes, expected %d" \
        % (ev["volumes"], HOME_MEDIA_VOLUMES)
    assert tuple(ev["released"]) == OVA_RELEASED, \
        "the series article dates the OVA %r" % (ev["released"],)
    assert tuple(ev["last_volume"]) == OVA_RELEASED, \
        "the last home media volume and the OVA no longer share a date " \
        "(%r vs %r)" % (ev["last_volume"], OVA_RELEASED)
    assert ev["volume_ordinal"] == ordinal_word(HOME_MEDIA_VOLUMES), \
        "the source calls it the %r volume, expected the %s" \
        % (ev["volume_ordinal"], ordinal_word(HOME_MEDIA_VOLUMES))
    last = data["home_media_jp"][-1]
    assert last[0] == str(HOME_MEDIA_VOLUMES), \
        "the home media table's last volume is %r" % last[0]
    assert OVA_NUMBER in last[1] and str(BROADCAST) in last[1], \
        "the last home media volume's episode list is %r, and the OVA being " \
        "a row rests on it holding both the finale and the OVA" % last[1]
    return last[1]


def check_no_runtimes(data, hunt):
    """Every one of the four places a running time could live, asserted empty.

    This is the whole weights decision, and it is asserted rather than
    remembered because a note that claims a source is empty is a claim, and an
    unchecked claim ages into a lie."""
    ab = data["runtime_absence"]
    for key in ("runtime_lines_series", "runtime_lines_list",
                "episode_runtime_fields", "minutes_on_series_article",
                "minutes_on_list_article"):
        assert ab[key] == [], \
            "%s is no longer empty (%r) — revisit weights" % (key, ab[key])

    checked = hunt["article_names_checked"]
    assert len(checked) == 3 * (BROADCAST + 1), \
        "the hunt asked for %d page names, expected %d (3 forms for each of " \
        "%d rows)" % (len(checked), 3 * (BROADCAST + 1), BROADCAST + 1)
    resolved = hunt["article_names_resolved"]
    detail = hunt["resolved_names_are_not_episodes"]
    assert set(resolved.values()) == set(detail), \
        "the hunt resolved %d names but opened %d of them" \
        % (len(set(resolved.values())), len(detail))
    for name, d in sorted(detail.items()):
        assert not d["kill_la_kill_categories"], \
            "%r is filed under %r — it may be an episode article after all, " \
            "so revisit weights" % (name, d["kill_la_kill_categories"])
        assert not d["intro_mentions_series"], \
            "%r mentions the series in its intro — it may be an episode " \
            "article, so revisit weights" % name
    for _page, wd in sorted(hunt["wikidata"].items()):
        assert wd["runtime_statements"] == [], \
            "%s carries a duration now (%r) — revisit weights" \
            % (wd["qid"], wd["runtime_statements"])
    assert hunt["episode_items"] == [], \
        "Wikidata has %d per-episode items now — they may carry P2047, so " \
        "revisit weights" % len(hunt["episode_items"])
    assert hunt["with_runtime"] == [], \
        "something in the series' Wikidata orbit carries a duration now " \
        "(%r) — revisit weights" % hunt["with_runtime"]
    assert hunt["ja_broadcast_slot_field"] == [], \
        "the Japanese infobox states a broadcast slot now (%r); a slot is " \
        "still not a running time, but it is the nearest thing to one this " \
        "hunt looks for and it should be read before this ships unweighted" \
        % hunt["ja_broadcast_slot_field"]
    assert hunt["ja_minute_figures_in_infobox"] == [], \
        "the Japanese infobox states a figure in minutes now (%r) — revisit " \
        "weights" % hunt["ja_minute_figures_in_infobox"]
    return len(checked), len(resolved)


# --------------------------------------------------------------------------

def main():
    if "--harvest" in sys.argv:
        harvest()

    data = load(DATA, "it holds the episode table this list is built from")
    hunt = load(HUNT, "it holds the receipts for this list being unweighted")

    check_accent()
    rows = check_rows(data)
    stated = check_count(data, hunt)
    check_dates_agree(data)
    split = check_themes(data)
    last_volume = check_ova_evidence(data)
    names_asked, names_resolved = check_no_runtimes(data, hunt)

    ova = rows[-1]
    broadcast = rows[:-1]

    def row(r, note=None, opt=False):
        out = {"id": "klk-e%s" % r["n"], "t": r["t"], "n": r["n"]}
        if r["n"] == OVA_NUMBER:
            out["id"] = OVA_ID
        if EPISODE_HOURS is not None:
            out["w"] = EPISODE_HOURS
        if note:
            out["note"] = note
        if opt:
            out["opt"] = True
        return out

    notes_by_number = {
        "1": "Series premiere",
        str(BROADCAST): "Series finale",
    }

    def block(lo, hi):
        return [row(r, notes_by_number.get(r["n"]))
                for r in broadcast if lo <= int(r["n"]) <= hi]

    first, second = block(1, split), block(split + 1, BROADCAST)

    def dateline(items):
        """"October 2013 – January 2014" from the rows themselves."""
        a = tuple(next(r for r in broadcast if r["n"] == items[0]["n"])["aired"])
        b = tuple(next(r for r in broadcast if r["n"] == items[-1]["n"])["aired"])
        if a[0] == b[0]:
            return "%s–%s %d" % (MONTHS[a[1] - 1], MONTHS[b[1] - 1], a[0])
        return "%s %d – %s %d" % (MONTHS[a[1] - 1], a[0],
                                       MONTHS[b[1] - 1], b[0])

    sections = [
        {
            "id": "themeone",
            "title": "Episodes 1–%d" % split,
            "sub": prop.join_bits(dateline(first), "%d episodes" % len(first),
                                  "the first opening and ending themes"),
            "intro": "Start at the top: this is the broadcast order, which is "
                     "the only order there is. The two television sections "
                     "split where the source splits them — the opening "
                     "and ending themes change at episode %d — and not "
                     "at anything that happens."
                     % (split + 1),
            "open": True,
            "items": first,
        },
        {
            "id": "themetwo",
            "title": "Episodes %d–%d" % (split + 1, BROADCAST),
            "sub": prop.join_bits(dateline(second),
                                  "%d episodes" % len(second),
                                  "the second opening and ending themes"),
            "items": second,
        },
    ]

    if INCLUDE_OVA:
        sections.append({
            "id": "ova",
            "title": "The OVA",
            "sub": prop.join_bits(
                "%s %d" % (MONTHS[OVA_RELEASED[1] - 1], OVA_RELEASED[0]),
                "one episode, home media only",
                "optional — skip it and you have still watched the "
                "series"),
            "items": [row(ova, "Never broadcast — bundled with the %s "
                               "home media volume"
                          % ordinal_word(HOME_MEDIA_VOLUMES), opt=True)],
        })

    total = sum(len(s["items"]) for s in sections)
    expected = BROADCAST + (1 if INCLUDE_OVA else 0)
    assert total == expected, "%d rows, expected %d" % (total, expected)
    assert len(first) == split and len(second) == BROADCAST - split, \
        "sections split %d/%d" % (len(first), len(second))
    required = [x for s in sections for x in s["items"] if not x.get("opt")]
    assert len(required) == BROADCAST, \
        "%d required rows, expected the %d broadcast episodes" \
        % (len(required), BROADCAST)
    weighted = [x for s in sections for x in s["items"] if "w" in x]
    assert len(weighted) in (0, total), \
        "%d of %d rows carry a weight — CLU-131: a row with no `w` on a " \
        "weighted list silently counts as one hour, so it is every row or " \
        "none" % (len(weighted), total)

    # Every row here is an episode. A bare year in a row note would make it a
    # cross-list sync candidate keyed on title and year, and this list's titles
    # are pop song titles — "Trigger", "Incomplete", "Into the Night" — so a
    # year in a note is a genuine collision risk rather than a theoretical one.
    for s in sections:
        for x in s["items"]:
            assert not re.search(r"\b(18|19|20)\d{2}\b", x.get("note") or ""), \
                "episode row %s names a year in its note" % x["id"]
            assert "url" not in x, "episode row %s carries a url" % x["id"]

    hours_claim = ("about %d hours" % round(total * EPISODE_HOURS)
                   if EPISODE_HOURS is not None else None)

    # How long after the finale the OVA reached shops, in whole months, taken
    # off the two dates rather than typed beside them.
    gap_months = int(round(days_between(LAST_AIRED, OVA_RELEASED) / 30.44))
    assert 1 <= gap_months <= 24, "the OVA gap reads %d months" % gap_months

    if EPISODE_HOURS is None:
        weights_note = [
            "Nothing is weighted, and hours are not tracked here.",
            "Every place a per-episode running time could live was checked "
            "and every one is empty. No episode has its own Wikipedia "
            "article: all %d titles were asked for directly, in three forms "
            "each, and of those %d page names the %d that resolve are the "
            "unrelated songs, films and disambiguation pages the titles "
            "collide with — every one of them was opened, and not one is "
            "filed under this series or mentions it. "
            "Wikidata has no per-episode items at all, and "
            "the series item %s carries no duration statement of any kind, "
            "so there is not even a series-level average to spread across "
            "the rows; nothing else Wikidata files under the series carries "
            "one either. Neither the series infobox nor the episode list's "
            "season infobox has a runtime field, neither article states a "
            "figure in minutes anywhere, and not one of the %d episode-table "
            "entries carries a "
            "running-time field. The Japanese article was read too and gives "
            "no length and no broadcast slot. So there is no figure to weigh "
            "from. It has to be every row or no row, because a row with no "
            "weight silently counts as a full hour — so it is no row, "
            "every episode counts one, and the strip and the pace line count "
            "episodes rather than hours."
            % (BROADCAST + 1, names_asked, names_resolved, SERIES_QID,
               BROADCAST + 1)]
    else:
        weights_note = [
            "The hours here are an estimate, not a measurement.",
            "No per-episode running time is published anywhere that was "
            "checked — no episode article, no Wikidata item, no runtime "
            "field on either article, no RunTime on any of the %d table "
            "entries, and no length on the Japanese article. Every row "
            "therefore carries the same %.2f hours, which is the figure this "
            "catalogue's other half-hour anime lists use rather than anything "
            "this series publishes. Treat the total as a rough %s and the "
            "per-row width as meaningless."
            % (BROADCAST + 1, EPISODE_HOURS, hours_claim)]

    if INCLUDE_OVA:
        ova_note = [
            "The OVA is a row, and it is optional.",
            "The source's own episode table carries %s entries, not %s: the "
            "last one is numbered “%s” rather than 25, and both "
            "infoboxes count the run as “%s”. It is new animation "
            "rather than a re-cut of anything — it was released as part "
            "of the %s home media volume on %s, whose own row in the source's "
            "table reads “%s” — so it is a thing to watch that "
            "nothing else here covers, and it sits at the end where the "
            "source puts it. It is marked optional because it never aired, it "
            "is not one of the %s, and it reached shops %s months after the "
            "run closed. Skip it and you have still watched the series."
            % (num2word(BROADCAST + 1), num2word(BROADCAST), OVA_NUMBER,
               stated, ordinal_word(HOME_MEDIA_VOLUMES),
               fmt_date(OVA_RELEASED), last_volume, num2word(BROADCAST),
               num2word(gap_months))]
    else:
        ova_note = [
            "The OVA is deliberately absent.",
            "The source's episode table carries one entry more than the "
            "broadcast run, numbered “%s” rather than 25 and "
            "released with the %s home media volume on %s. This list is the "
            "%s broadcast episodes only, so it is not here."
            % (OVA_NUMBER, ordinal_word(HOME_MEDIA_VOLUMES),
               fmt_date(OVA_RELEASED), num2word(BROADCAST))]

    p = {
        "slug": SLUG,
        "title": "Kill la Kill",
        "subtitle": "the whole broadcast run, and the OVA that never aired"
                    if INCLUDE_OVA else "the broadcast run only",
        "kind": "anime",
        "popularity": 65,
        "year": "%d–%d" % (FIRST_AIRED[0], LAST_AIRED[0]),
        "blurb": ("Trigger's %s-episode run in broadcast order, plus the "
                  "OVA episode that only ever shipped on the last home media "
                  "volume."
                  % num2word(BROADCAST)) if INCLUDE_OVA else
                 ("Trigger's %s-episode run in broadcast order."
                  % num2word(BROADCAST)),
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ova_note,
            weights_note,
            ["Every episode is named after a pop song.",
             "“Trigger”, “Don't Stop Me Now”, "
             "“Into the Night” — the source says each title is "
             "a Japanese classical pop song, picked out of head writer %s's "
             "own iTunes collection as he wrote the scripts. So a title here "
             "is not a description of the episode, and %s of the %s have a "
             "Wikipedia article of their own about something else entirely. "
             "Worth knowing before you go looking one up."
             % (data["songs_head_writer"], num2word(names_resolved),
                num2word(BROADCAST + 1))],
            ["What is deliberately absent.",
             "The manga adaptation — %d chapters serialised between %s "
             "and %s and collected in %s volumes — and the video game, "
             "%s, released %s. Neither is the television run, and this list "
             "is the television run and the episode the source files "
             "alongside it."
             % (data["manga"]["chapters"],
                fmt_date(tuple(data["manga"]["first"])),
                fmt_date(tuple(data["manga"]["last"])),
                num2word(data["manga"]["volumes"]),
                data["game"]["title"], fmt_date(tuple(data["game"]["released"]))
                )],
            "Episode numbering, titles and air dates machine-read from "
            "Wikipedia's “List of Kill la Kill episodes”; the OVA's "
            "release, the home media volumes, the manga and the game from the "
            "“Kill la Kill” article; the episode count corroborated "
            "against Wikidata %s. Both infoboxes are asserted to say "
            "“%s”, the broadcast numbering asserted contiguous 1 to "
            "%d with the OVA apart from it, and the runtime hunt behind the "
            "weights note recorded in "
            "tools/data/kill-la-kill-runtime-hunt.json, before this builds."
            % (SERIES_QID, stated, BROADCAST),
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d rows in %d sections (%d broadcast%s)"
          % (out.name, total, len(sections), BROADCAST,
             " + 1 OVA, optional" if INCLUDE_OVA else ", OVA excluded"))
    for s in sections:
        print("   %-16s %3d  %s" % (s["title"], len(s["items"]), s["sub"]))
    print("   count asserted 3 ways: season infobox %r, series infobox %r, "
          "Wikidata %s P1113=%d" % (stated, stated, SERIES_QID, BROADCAST))
    print("   section split read from the source's theme change at episode %d"
          % (split + 1))
    print("   weighted: %s"
          % ("no — %d page names asked (%d resolved, every one opened and "
             "none of them an episode), no "
             "per-episode Wikidata item, no runtime field on either article, "
             "no RunTime on any of the %d table rows, nothing on the Japanese "
             "article" % (names_asked, names_resolved, BROADCAST + 1)
             if EPISODE_HOURS is None
             else "yes — %.2f h per row, a house estimate" % EPISODE_HOURS))


if __name__ == "__main__":
    main()
