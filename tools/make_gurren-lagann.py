#!/usr/bin/env python3
"""Generate properties/gurren-lagann.json — the whole 2007 run, no films.

    python3 tools/make_gurren-lagann.py

Gainax's twenty-seven-episode mecha series, April 1 to September 30, 2007, in
broadcast order, plus the one bonus episode the source's own table carries.
28 rows.

TWO FILMS EXIST AND NEITHER OF THEM IS A ROW. THIS IS THE WHOLE JOB.
Both were checked against the source rather than assumed, and the source is
unusually clear about the first and clear enough about the second:

  * ''Gurren Lagann the Movie: Childhood's End'' (September 6, 2008, 112
    minutes) — "The film is a compilation of the events of the first arc of
    the series (episodes one through fifteen) with around 20 minutes of newly
    animated scenes." That is an exact range, so main() asserts it BY RANGE
    rather than by name: the range must start at episode 1 and must stop
    short of the finale, which is what makes it a re-cut of part of this list
    rather than a thing to watch alongside it.

  * ''Gurren Lagann The Movie: The Lights in the Sky are Stars'' (April 25,
    2009, 126 minutes) — "It focuses on the second half of the series,
    contributing more new animation than the first film." More new animation
    than a compilation is still a compilation; the source never calls it a
    sequel, never says it carries story the series does not, and gives it no
    material of its own to point at.

Three further statements in the cached source say the same thing about the
pair, and all three are asserted:

  * the series article's lead: "Two [[animated film]] versions were
    produced" — versions, not sequels;
  * the production section: "Once the series ended, Yamaga had the idea of
    releasing a film that retells the events of the series to expand the
    audience"; and
  * the word "sequel" appears nowhere in the Anime films section, which
    main() asserts as a negative — if either film is ever described as one,
    this build fails rather than quietly keeping it off the list.

So both films are the same viewing as the episodes below, re-cut for cinemas.
Rowing either would count the series twice, in the row count and in the hours
if this list were weighted. They are named in the notes as an alternative way
to watch it, with their dates and lengths, which is all they are. Note also
that the second film takes its title from episode 27 — the row on this list
with that title is the episode.

THE BONUS EPISODE IS A ROW, AND IT IS OPTIONAL. The article's episode table
carries twenty-eight {{Episode list}} blocks, not twenty-seven: one is
numbered "5.5" and its own note says "This is a bonus episode bundled with
the [[Nintendo DS]] game based on the series." It is new animation rather
than a re-cut, it sits between episodes 5 and 6 where the source puts it, and
it is marked optional because it was never broadcast and is not one of the
twenty-seven. Its number is read from the raw wikitext, never through
gwlib's parsed EpisodeNumber — int() folds "5.5" into 5, which would collide
with episode 5 and silently drop a row.

THE COUNT IS ASSERTED FOUR WAYS: the list article's {{Infobox television
season}} num_episodes, the list article's own prose ("containing twenty-seven
episodes"), the series article's {{Infobox animanga/Video}} episodes field,
and the series article's lead ("It ran for 27 episodes"). Wikidata's Q4277
agrees independently with P1113 = 27, recorded by scratch/agent-gurren/hunt2.py
and asserted here from its cached result.

WEIGHTS: NONE, AND IT IS ALL-OR-NOTHING (CLU-131). The full hunt was run and
every source came up empty:

  1. no episode has its own English Wikipedia article — all 28 titles were
     asked for directly, in three forms each (bare, "(Gurren Lagann)",
     "(Gurren Lagann episode)"), and none of the 84 names resolves;
     scratch/agent-gurren/hunt.py records the answer and main() asserts it;
  2. no episode has a Wikidata item at all — nothing that is a
     television-series episode points at Q4277, and nothing anywhere in the
     series' orbit carries P2047; scratch/agent-gurren/hunt2.py records that
     and main() asserts it;
  3. neither the series article's television infobox nor the list article's
     season infobox carries a runtime field — the only `runtime =` lines on
     either page are the two films', asserted here; and
  4. not one of the twenty-eight {{Episode list}} blocks carries a RunTime.

The single duration that exists for the television run is one unqualified,
series-level P2047 of 25 minutes on Q4277 — an average, not twenty-seven
measurements. Spreading it across every row would invent precision the source
refuses to give. And it has to be every row or no row, because a row with no
`w` on a weighted list resolves to a full hour: weighting the films (112 and
126 minutes, the only lengths published anywhere) while twenty-eight episodes
had none would read as twenty-eight hours of television. Nothing carries a
weight, the films are not rows anyway, and main() asserts both.

Everything is machine-read from the cached Wikipedia wikitext in
scratch/agent-gurren/gurren-lagann/ — the episode-list article and the series
article — plus the two hunt result files beside them. Nothing is typed from
memory. Before anything is written: the parsed row count and numbering are
asserted contiguous 1..27 with exactly one 5.5; air dates are asserted
weekly-ordered and matched against both infoboxes' first/last aired; the film
table is asserted to hold exactly the two films this generator knows, in that
order, with those dates; the compilation range is asserted to start at the
first episode and stop short of the last; every exclusion the notes name —
the two Parallel Works batches, the Yoko music video, the manga, the light
novels, the spin-off manga, the DS game and the mobile game — is matched in
the source rather than remembered; and the accent pair is asserted unused by
every other property on disk.

scratch/agent-gurren/tamper.py checks the guards actually fire: it copies the
cache, rewrites one sentence at a time (the second film described as a sequel,
the compilation range widened to the whole run, an episode gaining a RunTime,
the bonus episode losing its 5.5, a third film appearing) and confirms this
generator refuses each one.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki  # noqa: E402

SLUG = "gurren-lagann"
SCRATCH = prop.ROOT / "scratch" / "agent-gurren"
CACHE = SCRATCH / SLUG
LIST_PAGE = "List of Gurren Lagann episodes"
SERIES_PAGE = "Gurren Lagann"

BROADCAST = 27          # asserted four ways plus Wikidata
BONUS_NUMBER = "5.5"    # read from raw wikitext; int() would fold it into 5
BONUS_AFTER = 5
LISTED = 28             # 27 broadcast + the bonus
FIRST_AIRED = (2007, 4, 1)
LAST_AIRED = (2007, 9, 30)

FILMS = ["Gurren Lagann the Movie: Childhood's End",
         "Gurren Lagann the Movie: The Lights in the Sky Are Stars"]
FILM_DATES = [(2008, 9, 6), (2009, 4, 25)]

# the article's own table colours: A62020 for the series, FF7A7A for the film
# table under it. Both asserted unused by every other list.
ACCENT = "#A62020"
ACCENT_DARK = "#FF7A7A"

SERIES_QID = "Q4277"
SERIES_LEVEL_RUNTIME = 25   # one unqualified P2047 on Q4277: an average

MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}

_ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven",
         "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
         "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50}


def word2num(w):
    """"twenty-seven" -> 27. Small on purpose: the source writes counts as
    words in two places and both are read rather than remembered."""
    w = w.strip().lower().replace("–", "-")
    if w in _ONES:
        return _ONES.index(w)
    head, _, tail = w.partition("-")
    assert head in _TENS, "cannot read %r as a number" % w
    return _TENS[head] + (_ONES.index(tail) if tail else 0)


def text(page):
    t = wiki.wikitext(page, cache_dir=CACHE)
    assert t, "no wikitext for %r (run scratch/agent-gurren/fetch.py)" % page
    return t


def hunt(name):
    f = SCRATCH / name
    assert f.exists(), \
        "%s is missing — run scratch/agent-gurren/hunt.py and hunt2.py; the " \
        "weights decision on this list rests on what they found" % f
    return json.loads(f.read_text(encoding="utf-8"))


def strip_refs(t):
    """Prose with the footnotes gone, for the sentences main() reads as fact."""
    t = re.sub(r"<ref[^>]*/>", "", t)
    return re.sub(r"<ref.*?</ref>", "", t, flags=re.S)


def raw_field(block, name):
    """One {{Episode list}} field exactly as written.

    gwlib's episodes() reads EpisodeNumber through int(), which folds "5.5"
    into 5 — on this article that silently collides the bonus episode with
    episode 5 and loses a row. Numbering is always read from the raw text."""
    m = re.search(r"\|\s*%s\s*=\s*(.*?)(?=\n\s*\||\Z)" % name, block, re.S)
    return m.group(1).strip() if m else ""


def date_in(chunk, kind="Start"):
    """The first {{Start date}} / {{End date}} in a chunk, as (y, m, d)."""
    m = re.search(r"\{\{%s date\s*\|\s*(\d{4})\s*\|\s*(\d{1,2})\s*\|"
                  r"\s*(\d{1,2})" % kind, chunk or "", re.I)
    assert m, "no %s date in %r" % (kind.lower(), (chunk or "")[:80])
    return tuple(int(g) for g in m.groups())


def plain_date(s):
    """"April 1, 2007" -> (2007, 4, 1). The series infobox writes its dates
    as prose where the season infobox uses templates."""
    m = re.search(r"([A-Z][a-z]+)\s+(\d{1,2}),\s*(\d{4})", s or "")
    assert m, "no plain date in %r" % (s or "")[:60]
    return (int(m.group(3)), MONTHS[m.group(1)], int(m.group(2)))


def fmt_date(d):
    names = {v: k for k, v in MONTHS.items()}
    return "%s %d, %d" % (names[d[1]], d[2], d[0])


def brace_block(t, start):
    """The balanced {{...}} beginning at `start`.

    A split on a line-leading `}}` is wrong on this page: the animanga
    infoboxes nest {{English anime licensee}} blocks whose closing braces also
    sit at column zero, and a split-based reader truncates every field after
    the licensee — which is exactly where `runtime` lives."""
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

    Nested templates close two at a time (`…}}}}`) and wikilinks carry pipes
    at template depth zero (`network = [[AT-X (TV network)|AT-X]]`), so both
    `{{`/`}}` and `[[`/`]]` are counted, two characters at a step."""
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


def animanga_videos(t):
    """Every {{Infobox animanga/Video}} on a page, as [(type, {field: value})].

    Counted rather than searched, so a newly announced installment fails this
    build instead of going quietly missing from the list."""
    out = []
    for m in re.finditer(r"\{\{Infobox animanga/Video", t):
        fields = infobox_fields(brace_block(t, m.start()))
        out.append((fields.get("type", "").lower(), fields))
    return out


# --------------------------------------------------------------------------
# the episode table
# --------------------------------------------------------------------------

def episode_segment(list_text):
    """The article's ==Episodes== section, sliced at its own headings."""
    a = list_text.find("==Episodes==")
    b = list_text.find("==''Gurren Lagann Parallel Works''==")
    assert 0 <= a < b, \
        "the list article's Episodes / Parallel Works headings have moved — " \
        "the slice this generator reads episodes out of is no longer valid"
    return list_text[a:b]


def episode_rows(list_text):
    """[(number_as_written, title, (y,m,d), block)] for the whole table."""
    seg = episode_segment(list_text)
    raw = wiki.episodes(seg)
    rows = []
    for _o, _s, title, _y, block in raw:
        n = raw_field(block, "EpisodeNumber")
        assert n and title, "incomplete episode row: %r" % (n or title)[:60]
        assert not raw_field(block, "RunTime"), \
            "episode %s documents a runtime now — revisit weights, because " \
            "the only reason this list is unweighted is that no episode " \
            "had one" % n
        rows.append((n, title, date_in(raw_field(block, "OriginalAirDate")),
                     block))
    assert len(rows) == LISTED, \
        "the episode table parsed %d rows, expected %d (%d broadcast plus " \
        "the bonus episode)" % (len(rows), LISTED, BROADCAST)

    numbers = [n for n, _, _, _ in rows]
    assert numbers.count(BONUS_NUMBER) == 1, \
        "the table holds %d rows numbered %r, expected exactly one" \
        % (numbers.count(BONUS_NUMBER), BONUS_NUMBER)
    broadcast = [n for n in numbers if n != BONUS_NUMBER]
    assert broadcast == [str(i) for i in range(1, BROADCAST + 1)], \
        "broadcast numbering is not a plain contiguous 1..%d: %r" \
        % (BROADCAST, broadcast)
    assert numbers.index(BONUS_NUMBER) == BONUS_AFTER, \
        "the bonus episode sits at table position %d, not directly after " \
        "episode %d where the source puts it" \
        % (numbers.index(BONUS_NUMBER), BONUS_AFTER)
    return rows


def check_broadcast_dates(rows, season_box, series_box):
    """Weekly, in order, and matching both infoboxes' first and last aired."""
    dates = [d for n, _, d, _ in rows if n != BONUS_NUMBER]
    assert dates == sorted(dates), "broadcast air dates are out of order"
    assert dates[0] == FIRST_AIRED and dates[-1] == LAST_AIRED, \
        "the run reads %s to %s, expected %s to %s" \
        % (dates[0], dates[-1], FIRST_AIRED, LAST_AIRED)
    assert date_in(season_box("first_aired")) == FIRST_AIRED, \
        "the season infobox first aired %r" % season_box("first_aired")
    assert date_in(season_box("last_aired"), "End") == LAST_AIRED, \
        "the season infobox last aired %r" % season_box("last_aired")
    assert plain_date(series_box["first"]) == FIRST_AIRED, \
        "the series infobox first aired %r" % series_box["first"]
    assert plain_date(series_box["last"]) == LAST_AIRED, \
        "the series infobox last aired %r" % series_box["last"]

    bonus = [d for n, _, d, _ in rows if n == BONUS_NUMBER][0]
    assert bonus > dates[-1], \
        "the bonus episode is dated %s, inside the broadcast run — it is " \
        "listed as a game bundle released after the finale" % (bonus,)
    return bonus


def check_count(list_text, series_text, season_box, series_box, wd):
    """The episode count, four ways from the articles and once from Wikidata."""
    assert int(season_box("num_episodes")) == BROADCAST, \
        "the season infobox counts %r episodes" % season_box("num_episodes")
    assert int(series_box["episodes"]) == BROADCAST, \
        "the series infobox counts %r episodes" % series_box["episodes"]

    prose = re.search(r"containing ([a-z-]+) episodes",
                      strip_refs(list_text))
    assert prose, "the list article no longer states its own episode count"
    assert word2num(prose.group(1)) == BROADCAST, \
        "the list article's prose says %r episodes" % prose.group(1)

    lead = re.search(r"It ran for (\d+) episodes on TV Tokyo",
                     strip_refs(series_text))
    assert lead, "the series article's lead no longer states the run length"
    assert int(lead.group(1)) == BROADCAST, \
        "the series lead says %s episodes" % lead.group(1)

    assert wd.get("series_episodes") == [BROADCAST], \
        "Wikidata %s records %r episodes, expected [%d]" \
        % (SERIES_QID, wd.get("series_episodes"), BROADCAST)
    return prose.group(1)


# --------------------------------------------------------------------------
# the two films, and the evidence that neither is a row
# --------------------------------------------------------------------------

def films_section(series_text):
    a = series_text.find("===Anime films===")
    b = series_text.find("==Reception==")
    assert 0 <= a < b, "the series article's Anime films section has moved"
    return strip_refs(series_text[a:b])


def film_table(list_text):
    """[(title, (y,m,d))] for the list article's own film table.

    Those rows use RTitle rather than Title, so gwlib's episodes() reads them
    with an empty title; they are parsed here instead."""
    a = list_text.find("===Film===")
    b = list_text.find("==Music videos==")
    assert 0 <= a < b, "the list article's Film section has moved"
    seg = list_text[a:b]
    out = []
    for m in re.finditer(r"\{\{Episode list\s*(\|.*?)\n\s*\}\}", seg, re.S):
        block = "\n" + m.group(1)
        out.append((wiki.clean(raw_field(block, "RTitle")),
                    date_in(raw_field(block, "OriginalAirDate"))))
    assert [t for t, _ in out] == FILMS, \
        "the film table lists %r, not the two films this generator knows — " \
        "a third film would need deciding on before it can be listed" \
        % [t for t, _ in out]
    assert [d for _, d in out] == FILM_DATES, \
        "the film table dates the films %r, expected %r" \
        % ([d for _, d in out], FILM_DATES)
    return out


def compilation_evidence(series_text):
    """The sentence that makes the first film a re-cut, read as a range.

    Returns (first_episode, last_episode, new_minutes). The range is the whole
    point: main() asserts it starts at the first episode and stops short of
    the last, which is what makes listing the film a double count rather than
    a matter of taste."""
    seg = films_section(series_text)
    m = re.search(r"The film is a compilation of the events of the first arc "
                  r"of the series \(episodes ([a-z-]+) through ([a-z-]+)\) "
                  r"with around (\d+) minutes of newly animated scenes\.", seg)
    assert m, "the series article no longer says the first film is a " \
              "compilation, or no longer says which episodes it covers — " \
              "the shape of this list rests on that sentence and it must be " \
              "re-read before building"
    return word2num(m.group(1)), word2num(m.group(2)), int(m.group(3))


def second_film_evidence(series_text):
    """The sentence that decides the second film, and the negative that
    matters more than it: the word "sequel" appears nowhere near either."""
    seg = films_section(series_text)
    m = re.search(r"It focuses on the (second half) of the series, "
                  r"contributing more new animation than the first film\.",
                  seg)
    assert m, "the series article no longer describes the second film as " \
              "covering the second half of the series — if it now carries " \
              "story the series does not, it becomes a row and this list " \
              "must be rebuilt around it"
    assert not re.search(r"\bsequels?\b", seg, re.I), \
        "the Anime films section now uses the word \"sequel\" — one of the " \
        "films may no longer be a re-cut, and this list refuses to guess"
    return m.group(1)


def pair_evidence(series_text):
    """Two more statements that call the films versions of the series."""
    lead = re.search(r"Two \[\[animated film\]\] versions were produced; the "
                     r"first premiered in Japanese theaters in (\w+) (\d{4}), "
                     r"and the second premiered in (\w+) (\d{4})\.",
                     strip_refs(series_text))
    assert lead, "the series article's lead no longer calls the films two " \
                 "versions of the series"
    assert (int(lead.group(2)), MONTHS[lead.group(1)]) == FILM_DATES[0][:2], \
        "the lead dates the first film %s %s" % (lead.group(1), lead.group(2))
    assert (int(lead.group(4)), MONTHS[lead.group(3)]) == FILM_DATES[1][:2], \
        "the lead dates the second film %s %s" % (lead.group(3), lead.group(4))

    origin = re.search(r"Yamaga had the idea of releasing a film that retells "
                       r"the events of the series", strip_refs(series_text))
    assert origin, "the production section no longer says the film project " \
                   "began as a retelling of the series"


def film_infoboxes(series_text):
    """The films' own infoboxes: titles, dates and the only runtimes on the
    page. Returns [(title, (y,m,d), minutes)]."""
    blocks = animanga_videos(series_text)
    types = [t for t, _ in blocks]
    assert types == ["tv series", "film", "film"], \
        "the series article's anime infoboxes are %r, not the three this " \
        "generator knows — something has been announced or released and the " \
        "list needs deciding on before it builds" % types

    tv = blocks[0][1]
    assert not tv.get("runtime"), \
        "the television infobox documents a running time now — revisit " \
        "weights, because the only reason this list is unweighted is that " \
        "nothing per-episode had one"

    out = []
    for _t, f in blocks[1:]:
        title = wiki.clean(f.get("title", ""))
        rt = re.search(r"(\d+) minutes", f.get("runtime", ""))
        assert rt, "no runtime on the infobox for %r" % title
        mins = int(rt.group(1))
        assert 80 <= mins <= 200, "film runtime %d looks wrong" % mins
        out.append((title, date_in(f.get("released", "")), mins))
    assert [t for t, _, _ in out] == FILMS, \
        "the film infoboxes are titled %r" % [t for t, _, _ in out]
    assert [d for _, d, _ in out] == FILM_DATES, \
        "the film infoboxes are dated %r" % [d for _, d, _ in out]
    return out, tv


# --------------------------------------------------------------------------
# the weights hunt, asserted rather than remembered
# --------------------------------------------------------------------------

def check_no_runtimes(list_text, series_text, rows):
    """Every place a per-episode running time could live, checked."""
    assert not re.search(r"\|\s*RunTime\s*=", list_text, re.I), \
        "an {{Episode list}} block on the list article carries a RunTime " \
        "now — revisit weights"
    for n, _t, _d, block in rows:
        assert not raw_field(block, "RunTime"), \
            "episode %s carries a RunTime now — revisit weights" % n
    season_rt = re.findall(r"^\s*\|\s*runtime\s*=\s*(.*)$", list_text,
                           re.M | re.I)
    assert season_rt == [], \
        "the list article carries runtime fields now: %r" % season_rt
    page_rt = re.findall(r"^\s*\|\s*runtime\s*=\s*(.*)$", series_text,
                         re.M | re.I)
    assert len(page_rt) == 2 and all("minutes" in v for v in page_rt), \
        "the series article's runtime fields are %r, expected exactly the " \
        "two films'" % page_rt


def check_hunts(rows):
    """What hunt.py and hunt2.py found, asserted from their cached results."""
    arts = hunt("hunt_articles.json")
    assert arts["episode_titles"] == [t for _n, t, _d, _b in rows], \
        "hunt_articles.json was built from different episode titles — rerun " \
        "scratch/agent-gurren/hunt.py"
    assert len(arts["checked"]) == 3 * LISTED, \
        "hunt_articles.json checked %d page names, expected %d" \
        % (len(arts["checked"]), 3 * LISTED)
    assert not arts["found"], \
        "an episode has its own article now (%r) — it may carry a runtime, " \
        "so revisit weights" % sorted(arts["found"])

    wd = hunt("wikidata_hunt.json")
    assert wd["episode_items"] == [], \
        "Wikidata now has per-episode items for this series (%d) — they may " \
        "carry P2047, so revisit weights" % len(wd["episode_items"])
    assert wd["with_runtime"] == [], \
        "something in the series' Wikidata orbit carries a duration now — " \
        "revisit weights"
    assert wd["series_runtime"] == SERIES_LEVEL_RUNTIME, \
        "%s's series-level runtime is %r, not the %d minutes this list " \
        "refuses to spread across every row" \
        % (SERIES_QID, wd["series_runtime"], SERIES_LEVEL_RUNTIME)
    assert len(wd["runtime_statements"]) == 1, \
        "%s carries %d P2047 statements now" \
        % (SERIES_QID, len(wd["runtime_statements"]))
    return arts, wd


# --------------------------------------------------------------------------
# what is deliberately absent
# --------------------------------------------------------------------------

def check_exclusions(list_text, series_text):
    """Everything the notes say is missing, matched in the source.

    A note that names what is absent is a claim, and an unchecked claim ages
    into a lie."""
    pw = re.search(r"The first series was released on (\w+ \d{1,2}, \d{4})\. "
                   r"A second series with ([a-z-]+) videos, ''Parallel "
                   r"Works 2'', was released on (\w+ \d{1,2}, \d{4})\.",
                   strip_refs(list_text))
    assert pw, "the list article no longer describes Parallel Works — the " \
               "notes name it as deliberately absent and must not name a " \
               "thing the source has dropped"
    a = list_text.find("==''Gurren Lagann Parallel Works''==")
    b = list_text.find("===Film===")
    assert 0 <= a < b, "the Parallel Works section has moved"
    pw_rows = len(re.findall(r"\|\s*EpisodeNumber\s*=", list_text[a:b]))
    assert pw_rows > word2num(pw.group(2)), \
        "the Parallel Works table holds %d rows but the second batch alone " \
        "is %d videos" % (pw_rows, word2num(pw.group(2)))

    c = list_text.find("==Music videos==")
    d = list_text.find("==References==")
    assert 0 <= c < d, "the Music videos section has moved"
    mv = wiki.episodes(list_text[c:d])
    mv_rows = len(mv)
    assert mv_rows >= 1, "the Music videos section parsed empty"
    assert any("Yoko" in t for _o, _s, t, _y, _b in mv), \
        "the music-video section no longer holds the Yoko video the notes " \
        "name: %r" % [t for _o, _s, t, _y, _b in mv]

    game = re.search(r"A \[\[Nintendo DS\]\] video game was released in "
                     r"(\w+ \d{4}), bundled with a special episode of the "
                     r"anime series\.", strip_refs(series_text))
    assert game, "the series article no longer ties the DS game to the bonus " \
                 "episode — that sentence is why the bonus row is on this list"

    # the print and game infoboxes the notes name as deliberately absent
    prints = [infobox_fields(brace_block(series_text, m.start())).get("type",
                                                                     "").lower()
              for m in re.finditer(r"\{\{Infobox animanga/Print", series_text)]
    assert prints == ["manga", "light novel", "manga"], \
        "the series article's print infoboxes are %r, not the manga, the " \
        "light novels and the spin-off manga the notes name" % prints
    games = [m for m in re.finditer(r"\{\{Infobox animanga/Game", series_text)]
    assert len(games) == 1, \
        "the series article carries %d game infoboxes" % len(games)
    ds = infobox_fields(brace_block(series_text, games[0].start()))
    assert plain_date(ds.get("released", "")) == (2007, 10, 25), \
        "the DS game is dated %r" % ds.get("released")

    mobile = re.search(r"An iOS and Android Gurren Lagann videogame was "
                       r"released in English on \w+ \d{1,2}, \d{4}, and was "
                       r"shut down on \w+ \d{1,2}, \d{4}\.",
                       strip_refs(series_text))
    assert mobile, "the series article no longer describes the mobile game " \
                   "the notes name as absent"
    return pw_rows, mv_rows, pw.group(1), pw.group(3), game.group(1)


def check_bonus_note(rows):
    """The bonus episode's own note, read rather than assumed."""
    block = [b for n, _t, _d, b in rows if n == BONUS_NUMBER][0]
    m = re.search(r"'''Note:'''\s*This is a bonus episode bundled with the "
                  r"\[\[Nintendo DS\]\] game based on the series\.", block)
    assert m, "the bonus episode no longer carries the note that says what " \
              "it is — if it has become a broadcast episode the count and " \
              "the optional flag are both wrong"


def check_uncut_note(rows):
    """Episode 6's note names an uncut home-video version; the row note says
    so, so the title is read out of the source rather than typed."""
    block = [b for n, _t, _d, b in rows if n == "6"][0]
    m = re.search(r"An uncut version of the episode, \{\{Nihongo\|"
                  r"\"([^\"]+)\"", block)
    assert m, "episode 6 no longer names an uncut home-video version"
    return m.group(1)


def check_clip_show(rows):
    """Episode 16 is the run's own recap; its row note says so."""
    n, title, _d, block = [r for r in rows if r[0] == "16"][0]
    assert title == "Compilation Episode", \
        "episode 16 is titled %r, not the recap this list labels" % title
    assert "[[clip show]] recapping" in block, \
        "episode 16 is no longer described as a clip show"
    return title


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


# --------------------------------------------------------------------------

def main():
    list_text = text(LIST_PAGE)
    series_text = text(SERIES_PAGE)
    check_accent()

    season_box = wiki.infobox(list_text, kind=r"television season")
    assert season_box, "the list article has no {{Infobox television season}}"
    films, tv_box = film_infoboxes(series_text)

    rows = episode_rows(list_text)
    _arts, wd = check_hunts(rows)
    count_word = check_count(list_text, series_text, season_box, tv_box, wd)
    bonus_date = check_broadcast_dates(rows, season_box, tv_box)
    check_no_runtimes(list_text, series_text, rows)
    check_bonus_note(rows)
    uncut = check_uncut_note(rows)
    check_clip_show(rows)

    # the two films, and why neither of them is a row
    table = film_table(list_text)
    first_a, first_b, new_mins = compilation_evidence(series_text)
    second_half = second_film_evidence(series_text)
    pair_evidence(series_text)
    assert first_a == 1, \
        "the first film's compilation starts at episode %d, not the first" \
        % first_a
    assert first_b < BROADCAST, \
        "the first film now covers episodes %d-%d, the whole run — the " \
        "section split this list uses is no longer the source's" \
        % (first_a, first_b)
    assert [d for _, d in table] == [d for _, d, _ in films], \
        "the film table and the film infoboxes disagree on the dates"
    assert films[0][2] < films[1][2], \
        "the films' runtimes are %r — the second is no longer the longer of " \
        "the pair" % [m for _, _, m in films]
    # the second film is named after the last episode; the notes say so, and a
    # reader who saw only the title could easily take one for the other
    assert rows[-1][0] == str(BROADCAST) and rows[-1][1] in FILMS[1], \
        "the second film no longer takes its title from episode %d (%r vs " \
        "%r) — the note that says so must be re-read" \
        % (BROADCAST, rows[-1][1], FILMS[1])

    pw_rows, mv_rows, pw1, pw2, game_when = check_exclusions(list_text,
                                                             series_text)

    # ---- rows ------------------------------------------------------------
    def row(n, title, note=None, opt=False):
        r = {"id": "gl-e%s" % n.replace(".", "-"), "t": title, "n": n}
        if note:
            r["note"] = note
        if opt:
            r["opt"] = True
        return r

    notes = {
        "1": "Series premiere",
        "6": "Broadcast with clip-show inserts standing in for cut footage; "
             "the uncut version, “%s”, is on the home video "
             "releases" % uncut,
        "16": "A clip show recapping the episodes before it",
        # no "Series finale" on the last broadcast episode: its position
        # already says it (CLU-123, CLU-557)
        BONUS_NUMBER: "Bonus episode bundled with the Nintendo DS game; not "
                      "one of the twenty-seven broadcast episodes, and "
                      "numbered 5.5 by the source",
    }

    def section_items(lo, hi):
        out = []
        for n, title, _d, _b in rows:
            key = float(n)
            if not (lo <= key <= hi):
                continue
            out.append(row(n, title, notes.get(n), opt=(n == BONUS_NUMBER)))
        return out

    first = section_items(1, first_b)
    rest = section_items(first_b + 1, BROADCAST)

    sections = [
        {
            "id": "arc1",
            "title": "Episodes 1–%d" % first_b,
            "sub": prop.join_bits("2007", "%d episodes" % first_b,
                                  "plus one bonus"),
            "intro": "What the source calls the first arc — and exactly "
                     "what the first film re-cuts, which is why that film is "
                     "not a row. The bonus episode sits after episode %d, "
                     "where the source puts it, and is marked optional: it "
                     "shipped with a game rather than on television."
                     % BONUS_AFTER,
            "open": True,
            "items": first,
        },
        {
            "id": "arc2",
            "title": "Episodes %d–%d" % (first_b + 1, BROADCAST),
            "sub": prop.join_bits("2007", "%d episodes" % len(rest)),
            "intro": "The rest of the run. The second film covers what the "
                     "source calls the %s of the series and is not a row "
                     "either; see the notes." % second_half,
            "items": rest,
        },
    ]

    total = sum(len(s["items"]) for s in sections)
    assert total == LISTED, "%d rows, expected %d" % (total, LISTED)
    assert len(first) == first_b + 1 and len(rest) == BROADCAST - first_b, \
        "sections split %d/%d" % (len(first), len(rest))
    assert sum(1 for s in sections for x in s["items"] if "w" in x) == 0, \
        "a weight crept in — this list is unweighted end to end"
    # every row here is an episode, and a year in an episode note would make
    # it a cross-list sync candidate keyed on title+year — episode 27 shares
    # its title with the second film, so this matters on this list in
    # particular
    for s in sections:
        for x in s["items"]:
            assert not re.search(r"\b(18|19|20)\d{2}\b", x.get("note") or ""), \
                "episode row %s names a year in its note" % x["id"]
            assert "url" not in x, "episode row %s carries a url" % x["id"]

    p = {
        "slug": SLUG,
        "title": "Gurren Lagann",
        "subtitle": "the whole 2007 run — and neither film",
        "kind": "anime",
        "popularity": 69,
        "year": "2007",
        "blurb": "Gainax's twenty-seven-episode mecha series in broadcast "
                 "order, plus the bonus episode that came with the game. "
                 "Both films re-cut the series, so neither is listed.",
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ["Two films exist. Neither of them is a row.",
             "%s (%s, %d minutes) is, in the source's own words, “a "
             "compilation of the events of the first arc of the series "
             "(episodes %s through %s) with around %d minutes of newly "
             "animated scenes”. %s (%s, %d minutes) “focuses on the "
             "%s of the series, contributing more new animation than the "
             "first film”. Neither is ever called a sequel, the article's "
             "lead calls the pair “two animated film versions”, and "
             "the production section says the project began as a film that "
             "retells the series. They are the same viewing as the episodes "
             "above, so listing them would count the run twice. If you would "
             "rather watch it as two sittings than as %s, they are how "
             "— and that is all they are."
             % (FILMS[0], fmt_date(FILM_DATES[0]), films[0][2],
                _ONES[first_a], _ONES[first_b], new_mins,
                FILMS[1], fmt_date(FILM_DATES[1]), films[1][2], second_half,
                count_word)],
            ["The second film borrows episode %d's title." % BROADCAST,
             "“%s” is both the last episode of the series and the "
             "name of the second film. The row on this list is the episode."
             % rows[-1][1]],
            ["One row is optional, and it is not a re-cut.",
             "The source's episode table carries twenty-eight entries, not "
             "twenty-seven: one is numbered 5.5 and its own note calls it a "
             "bonus episode bundled with the Nintendo DS game, which came "
             "out in %s. It is new animation rather than a compilation, so it "
             "is here, sitting after episode %d where the source puts it — "
             "but it never aired and is not one of the twenty-seven, so it is "
             "marked optional." % (game_when, BONUS_AFTER)],
            ["Nothing is weighted, and hours are not tracked here.",
             "Every place a per-episode running time could live was checked "
             "and every one is empty. No episode has its own Wikipedia "
             "article: all %d titles were asked for directly, in three forms "
             "each, and none of the %d names resolves. No episode has a "
             "Wikidata item at all — nothing that is a television-series "
             "episode points at %s, and nothing in the series' orbit carries "
             "a duration. Neither the series infobox nor the episode list's "
             "season infobox has a runtime field, and not one of the %d "
             "episode-table entries carries a running-time field. The only "
             "figure "
             "that exists for the television run is a single series-level %d "
             "minutes on %s, which is an average rather than %d "
             "measurements, and spreading it across every row would invent "
             "precision the source refuses to give. It has to be every row or "
             "no row, because a row with no weight silently counts as a full "
             "hour — so it is no row, and every episode counts one. The "
             "only lengths published anywhere are the two films' %d and %d "
             "minutes, and neither film is a row."
             % (LISTED, 3 * LISTED, SERIES_QID, LISTED,
                wd["series_runtime"], SERIES_QID, BROADCAST,
                films[0][2], films[1][2])],
            ["What else is deliberately absent.",
             "Gurren Lagann Parallel Works, the %d short music videos in two "
             "batches (%s and %s) that tell alternative stories — the "
             "source files them apart from the episodes, and they are not the "
             "series. The Yoko music video that shipped with a DVD pack. The "
             "manga, the light novels, the spin-off manga, the DS game the "
             "bonus episode came bundled with, and the mobile game. This "
             "list is the television run and nothing else."
             % (pw_rows, pw1, pw2)],
            "Episode titles, numbering and air dates machine-read from "
            "Wikipedia's “List of Gurren Lagann episodes”; the film "
            "descriptions, dates and runtimes from the “Gurren "
            "Lagann” article. The episode count is asserted four ways "
            "— both infoboxes, the list article's own prose and "
            "Wikidata's %s — the numbering asserted contiguous with "
            "exactly one 5.5, and the first film's episode range read out of "
            "the source's own sentence, before this builds." % SERIES_QID,
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d rows in %d sections (%d broadcast + 1 bonus)"
          % (out.name, total, len(sections), BROADCAST))
    print("   films refused: %s"
          % "; ".join("%s (%s, %d min)" % (t, fmt_date(d), m)
                      for t, d, m in films))
    print("   bonus episode dated %s, after the finale" % fmt_date(bonus_date))
    print("   excluded: %d Parallel Works videos, %d music video"
          % (pw_rows, mv_rows))
    for s in sections:
        print("   %-18s %3d  %s" % (s["title"], len(s["items"]), s["sub"]))
    print("   weighted: no (no per-episode runtime in any source; "
          "%s carries one series-level %d minutes)"
          % (SERIES_QID, wd["series_runtime"]))


if __name__ == "__main__":
    main()
