#!/usr/bin/env python3
"""Generate properties/made-in-abyss.json — both seasons and the two films
that are not re-cuts of them.

    python3 tools/make_made-in-abyss.py

Kinema Citrus' adaptation of Akihito Tsukushi's manga, in the order the
source puts it: season 1, the sequel film, season 2 — then Awakening Mystery,
the first film of the series announced in 2025, which the franchise article
calls a sequel to the second season. 27 rows.

THE 2019–20 TRILOGY IS THREE FILMS AND ONLY ONE OF THEM IS A ROW. THIS IS
THE WHOLE JOB.
Wikipedia's episode-list article files all three under one heading,
"Theatrical film trilogy (2019–20)", sitting between season 1 and season 2 —
which is why a reader coming to this cold sees three films and assumes three
sittings. Two of them are not. The list article's own prose, asserted in
main() rather than believed:

    Two [[compilation film]]s, titled ... "Journey's Dawn" (encompassing
    episodes 1–8 with new scenes for introduction) and ... "Wandering
    Twilight" (encompassing episodes 9–13), were released on January 4,
    2019, and January 18, 2019, respectively.

Episodes 1–8 and 9–13 is the whole of season 1, and main() asserts exactly
that: the two ranges are contiguous, start at 1, and end at the season's last
episode. Carrying them as rows would count all thirteen episodes a second
time — in the row count, and in the hours if this list were weighted.

The third film is a different kind of thing, and three separate statements in
the cached source say so, all three asserted:

  * the franchise article's lead: "A sequel film, subtitled ''Dawn of the
    Deep Soul'', premiered in Japan in January 2020";
  * the list article: "Following the release of the first compilation films,
    the sequel was revealed to be a film titled ... Made in Abyss the Movie:
    Dawn of the Deep Soul", premiering January 17, 2020; and
  * the footnote on season 2's first episode, which places that season
    "Directly after the events of the film ... Dawn of the Deep Soul".

So it is a sequel, it cannot be skipped, and it goes between the seasons —
which is where the source's own running order puts it, as the last of the
three films in a section sitting between the two season sections. The two
compilations are named in the notes as an alternative way to watch season
one, which is all they are.

WEIGHTS: NONE, AND IT IS ALL-OR-NOTHING. Wikipedia documents no running time
for this series — no `runtime` on either television infobox, and no `Runtime`
field on any of the 25 episode blocks, both asserted in main(). The film
infobox does give 105 minutes, and that is precisely the trap: weighting the
film while 25 episodes have no verifiable number would leave every episode
row resolving `WEIGHT = x.w >= 0 ? x.w : 1` to a full hour, so 25 half-hour
episodes would read as 25 hours (CLU-131). The only per-episode lengths the
source gives are the two "One hour season finale special" footnotes, one on
each season's last episode — both read here, because they are worth telling a
reader, and two durations out of 25 cannot weight a list. So no row carries a
`w`, the film included, and its runtime rides in the row note as text.

Everything is machine-read from the cached Wikipedia wikitext in
scratch/agent-abyss/made-in-abyss/ — the episode-list article and the
franchise article. Before anything is written: each season's parsed row count
is asserted against the list article's {{Series overview}}; each season's
in-season numbering is asserted to run 1..N and the overall numbering to run
1..25 unbroken; air dates are asserted non-decreasing and matched against the
overview's start and end dates; the film table is asserted to hold exactly
the three films this generator knows, in that order, with those dates; the
franchise article is asserted to carry exactly four anime video infoboxes, so
a newly released installment breaks the build instead of going missing; and
the accent pair is asserted unused by every other property on disk.

AWAKENING MYSTERY (2026-11-11). The episode-list article does not carry it
yet, so it is read from the franchise article's Films prose instead: the
announcement sentence, the first film's title and premiere date, the lead's
"sequel film to the second season", and the sentence saying a second film is
in production with no date — all asserted, so a second film gaining a date,
or the first one gaining an infobox, breaks the build. It has no runtime in
the source, which changes nothing here: the list is unweighted end to end.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki  # noqa: E402

SLUG = "made-in-abyss"
CACHE = prop.ROOT / "scratch" / "agent-abyss" / SLUG
LIST_PAGE = "List of Made in Abyss episodes"
FRANCHISE_PAGE = "Made in Abyss"

SEASONS = [1, 2]
TOTAL_EPISODES = 25    # 13 + 12, asserted three ways
LISTED = 27            # 25 episodes + two films

# The heading the episode-list article files all three films under. It is one
# section, sitting between the two season sections, and reading it as three
# equal things to watch is the mistake this generator exists to prevent.
FILMS_HEADING = "=== Theatrical film trilogy (2019–20) ==="
SEASON_HEADINGS = {1: "=== Season 1 (2017) ===",
                   2: "=== Season 2: ''The Golden City of the Scorching Sun''"
                      " (2022) ==="}

# The two that retell season 1, and the one that does not. Both facts are
# asserted from the source before either is used.
COMPILATIONS = ["Journey's Dawn", "Wandering Twilight"]
SEQUEL_FILM = "Made in Abyss: Dawn of the Deep Soul"
# the first film of the series announced in 2025; a sequel to season 2
SERIES_FILM = "Made in Abyss: Awakening Mystery"

ACCENT = "#1F5E63"       # the blue-green dark of the pit
ACCENT_DARK = "#E8C36A"  # ...against the light coming up out of it

MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}


def text(page):
    t = wiki.wikitext(page, cache_dir=CACHE)
    assert t, "no wikitext for %r (run scratch/agent-abyss/fetch.py)" % page
    return t


def strip_refs(t):
    """Prose with the footnotes gone, for the sentences main() reads as fact."""
    t = re.sub(r"<ref[^>]*/>", "", t)
    return re.sub(r"<ref.*?</ref>", "", t, flags=re.S)


def raw_field(block, name):
    """One {{Episode list}} field exactly as written — gwlib's episodes()
    reads EpisodeNumber through int(), which would fold "23β" into 23 and
    "25 (OVA)" into 25. Nothing here needs that, but the same footgun is one
    typo away, so numbering is always read from the raw text."""
    m = re.search(r"\|\s*%s\s*=\s*(.*?)(?=\n\s*\||\Z)" % name, block, re.S)
    return m.group(1).strip() if m else ""


def date_in(chunk, kind="Start"):
    """The first {{Start date}} / {{End date}} in a chunk, as (y, m, d)."""
    m = re.search(r"\{\{%s date\s*\|\s*(\d{4})\s*\|\s*(\d{1,2})\s*\|"
                  r"\s*(\d{1,2})" % kind, chunk or "", re.I)
    assert m, "no %s date in %r" % (kind.lower(), (chunk or "")[:80])
    return tuple(int(g) for g in m.groups())


def fmt_date(d):
    names = {v: k for k, v in MONTHS.items()}
    return "%s %d, %d" % (names[d[1]], d[2], d[0])


def brace_block(t, start):
    """The balanced {{...}} beginning at `start`.

    A naive split on a line-leading `}}` is wrong on these pages: the
    animanga infoboxes nest {{English anime licensee}} blocks whose closing
    braces also sit at column zero, and a split-based reader silently
    truncates every field after the licensee."""
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

    Two things have to be tracked or the split is silently wrong, and both
    occur in these infoboxes:

      * nested templates — a field ending `…}}}}` closes two templates at
        once, so the scanner must step over `{{` and `}}` two characters at a
        time rather than testing every character (testing every character
        counts `}}}}` as three closes and throws the depth off, which shipped
        a reader that lost every field after the first nested one); and
      * wikilinks — `network = [[AT-X (TV network)|AT-X]], [[Tokyo MX]]`
        carries a pipe at template depth zero, so `[[`/`]]` count as well."""
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

    gwlib.wiki.infobox() reads {{Infobox film}} / {{Infobox television}};
    anime franchise articles use the animanga family instead and stack
    several of them, which is exactly what has to be counted here."""
    out = []
    for m in re.finditer(r"\{\{Infobox animanga/Video", t):
        fields = infobox_fields(brace_block(t, m.start()))
        out.append((fields.get("type", "").lower(), fields))
    return out


def segments(list_text):
    """The article's three episode sections, sliced at its own headings."""
    marks = [(SEASON_HEADINGS[1], "s1"), (FILMS_HEADING, "films"),
             (SEASON_HEADINGS[2], "s2")]
    at = []
    for heading, key in marks:
        i = list_text.find(heading)
        assert i >= 0, "the list article no longer has the heading %r — the " \
                       "sections this generator slices on have moved" % heading
        at.append((i, key))
    order = sorted(at)
    assert [k for _, k in order] == ["s1", "films", "s2"], \
        "the article's sections run %r, not season 1 then the films then " \
        "season 2 — the running order this list follows is the source's" \
        % [k for _, k in order]
    out = {}
    for n, (i, key) in enumerate(order):
        end = order[n + 1][0] if n + 1 < len(order) else len(list_text)
        out[key] = list_text[i:end]
    return out


def series_overview(list_text):
    """{season: (episodes, start, end)} from the article's own overview."""
    seg = re.search(r"\{\{Series overview(.*?)\n\}\}", list_text, re.S)
    assert seg, "no series overview on the list article"
    body = seg.group(1)
    counts = {int(m.group(1)): int(m.group(2)) for m in
              re.finditer(r"\|\s*episodes(\d+)\s*=\s*(\d+)", body)}
    assert sorted(counts) == SEASONS, \
        "the overview lists seasons %s, expected %s" % (sorted(counts), SEASONS)
    assert sum(counts.values()) == TOTAL_EPISODES, \
        "the overview counts %d episodes, expected %d" \
        % (sum(counts.values()), TOTAL_EPISODES)
    out = {}
    for n in SEASONS:
        s = re.search(r"\|\s*start%d\s*=\s*(.*)" % n, body)
        e = re.search(r"\|\s*end%d\s*=\s*(.*)" % n, body)
        assert s and e, "season %d has no start/end in the overview" % n
        out[n] = (counts[n], date_in(s.group(1)), date_in(e.group(1), "End"))
    # a mid-run show carries this stamp; this one does not, which is why the
    # list can treat season 2 as the last season aired
    assert "{{Aired episodes" not in list_text, \
        "the list article has an aired-episodes stamp — a season may be " \
        "running and this generator's counts are frozen"
    return out


def season_rows(seg, n, overview):
    """[(overall, in_season, title, (y,m,d), block)] for one season."""
    raw = wiki.episodes(seg)
    assert raw, "season %d parsed empty" % n
    rows = []
    for o, s, t, _y, block in raw:
        assert not raw_field(block, "Runtime"), \
            "season %d episode %s documents a runtime now — revisit " \
            "weights, because the only reason this list is unweighted is " \
            "that no episode had one" % (n, o)
        assert o and s and t, "season %d row incomplete: %r" % (n, (o, s, t))
        rows.append((o, s, t, date_in(raw_field(block, "OriginalAirDate")),
                     block))
    episodes, start, end = overview[n]
    assert len(rows) == episodes, \
        "season %d parsed %d rows, the overview says %d" \
        % (n, len(rows), episodes)
    assert [s for _, s, _, _, _ in rows] == list(range(1, episodes + 1)), \
        "season %d numbering is not 1..%d" % (n, episodes)
    dates = [d for _, _, _, d, _ in rows]
    assert dates == sorted(dates), "season %d air dates are out of order" % n
    assert dates[0] == start and dates[-1] == end, \
        "season %d ran %s to %s, the overview says %s to %s" \
        % (n, dates[0], dates[-1], start, end)
    return rows


def film_rows(seg):
    """[(n, title, (y,m,d))] for the article's theatrical-film section."""
    raw = wiki.episodes(seg)
    assert len(raw) == 3, \
        "the film section holds %d entries, not the three this list knows — " \
        "a fourth film would need deciding on before it can be listed" \
        % len(raw)
    out = []
    for o, s, t, _y, block in raw:
        assert s is None, "a film row carries a season number: %r" % t
        assert raw_field(block, "EpisodeNumber") == str(o), \
            "film numbering is not plain: %r" % raw_field(block,
                                                          "EpisodeNumber")
        out.append((o, t, date_in(raw_field(block, "OriginalAirDate"))))
    assert [o for o, _, _ in out] == [1, 2, 3], \
        "the film section is numbered %r" % [o for o, _, _ in out]
    return out


def compilation_evidence(list_text):
    """The sentence that decides which films are re-cuts, read as data.

    Returns [(name, first_episode, last_episode)] for the two compilations.
    The episode ranges are the whole point: main() asserts they tile season 1
    exactly, which is what makes listing them a double count rather than a
    matter of taste."""
    m = re.search(
        r"Two \[\[compilation film\]\]s, titled "
        r"\{\{Nihongo\|[^{}]*?\|\"([^\"]+)\"\}\}"
        r"\s*\(encompassing episodes (\d+)–(\d+)[^)]*\) and "
        r"\{\{Nihongo\|[^{}]*?\|\"([^\"]+)\"\}\}"
        r"\s*\(encompassing episodes (\d+)–(\d+)\)",
        strip_refs(list_text))
    assert m, "the list article no longer says which films are compilations " \
              "or which episodes they cover — the entire shape of this list " \
              "rests on that sentence and it must be re-read before building"
    a, a1, a2, b, b1, b2 = m.groups()
    got = [(a, int(a1), int(a2)), (b, int(b1), int(b2))]
    assert [n for n, _, _ in got] == COMPILATIONS, \
        "the compilation films are named %r, expected %r" \
        % ([n for n, _, _ in got], COMPILATIONS)
    return got


def sequel_evidence(list_text, franchise_text):
    """The three statements that make Dawn of the Deep Soul a sequel rather
    than a third re-cut, each read from the source rather than assumed."""
    lead = re.search(r"A sequel film, subtitled ''Dawn of the Deep Soul'', "
                     r"premiered in Japan in January (\d{4})\.",
                     strip_refs(franchise_text))
    assert lead, "the franchise article's lead no longer calls Dawn of the " \
                 "Deep Soul a sequel film — if it is now described as a " \
                 "compilation it must come off this list"

    reveal = re.search(r"Following the release of the first compilation "
                       r"films?, (?:the sequel was revealed to be|a new "
                       r"sequel was announced)", strip_refs(list_text))
    assert reveal, "the list article no longer distinguishes the sequel from " \
                   "the compilation films"

    premiere = re.search(r"The film premiered in Japan on (\w+) (\d{1,2}), "
                         r"(\d{4})\.", strip_refs(list_text))
    assert premiere, "the list article gives no premiere date for the sequel"
    dated = (int(premiere.group(3)), MONTHS[premiere.group(1)],
             int(premiere.group(2)))

    # and the source's own note on where season 2 starts from
    after = re.search(r"Directly after the events of the film ''Gekij[^']*"
                      r"Made in Abyss the Movie: Dawn of the Deep Soul\)''\.",
                      list_text)
    assert after, "season 2's first episode no longer carries the note " \
                  "placing it directly after the film — that note is why " \
                  "the film sits between the seasons on this list"
    assert int(lead.group(1)) == dated[0], \
        "the lead says the film premiered in %s, the body says %s" \
        % (lead.group(1), dated[0])
    return dated


def franchise_video_blocks(franchise_text):
    """The franchise article's anime infoboxes: types, titles, runtimes.

    Counted rather than searched, so an installment that gains an infobox —
    the film series announced for 2026, a third season — fails this build
    instead of quietly missing from the list. (Awakening Mystery, the film
    series' first, has no infobox yet; when it gains one this fails, and its
    row should then read from that infobox.)"""
    blocks = animanga_videos(franchise_text)
    types = [t for t, _ in blocks]
    assert types == ["tv series", "film series", "film", "tv series"], \
        "the franchise article's anime infoboxes are %r, not the four this " \
        "generator knows — something has been announced or released and the " \
        "list needs deciding on before it builds" % types

    tv1, comp, film, tv2 = (f for _, f in blocks)
    for label, fields in (("season 1", tv1), ("season 2", tv2)):
        assert not fields.get("runtime"), \
            "%s now documents a running time — revisit weights" % label

    comp_titles = [wiki.clean(x) for x in
                   re.findall(r"Made in Abyss: [^|}\n]+",
                              comp.get("title", ""))]
    assert comp_titles == ["Made in Abyss: %s" % c for c in COMPILATIONS], \
        "the compilation infobox names %r" % comp_titles
    comp_runtimes = [int(x) for x in
                     re.findall(r"(\d+) minutes", comp.get("runtime", ""))]
    assert len(comp_runtimes) == 2, \
        "the compilation infobox gives %r runtimes" % comp_runtimes

    assert wiki.clean(film.get("title", "")) == SEQUEL_FILM, \
        "the film infobox is titled %r, expected %r" \
        % (film.get("title"), SEQUEL_FILM)
    rt = re.search(r"(\d+) minutes", film.get("runtime", ""))
    assert rt, "no runtime on the sequel film's infobox"
    mins = int(rt.group(1))
    assert 80 <= mins <= 180, "film runtime %d looks wrong" % mins
    return dated_from(film), mins, comp_runtimes


def dated_from(fields):
    return date_in(fields.get("released", ""))


def check_exclusions(list_text, franchise_text):
    """Everything the notes say is deliberately absent, read from the source.

    A note that names what is missing is a claim, and an unchecked claim ages
    into a lie — so the shorts, the game and the film series' undated second
    film are all matched here rather than remembered."""
    shorts = re.search(r"A four-part series of short films, called "
                       r"\"Marulk's Daily Life\", was produced along the "
                       r"third movie ''Made in Abyss: Dawn of the Deep Soul''",
                       strip_refs(list_text))
    assert shorts, "the list article no longer describes the four shorts " \
                   "that screened with Dawn of the Deep Soul — the notes " \
                   "name them as deliberately absent and must not name a " \
                   "thing the source has dropped"

    game = re.search(r"\{\{Infobox animanga/Game", franchise_text)
    assert game, "the franchise article no longer carries a game infobox"
    fields = infobox_fields(brace_block(franchise_text, game.start()))
    assert wiki.clean(fields.get("title", "")) == \
        "Made in Abyss: Binary Star Falling into Darkness", \
        "the game is titled %r" % fields.get("title")
    years = re.findall(r"\b(20\d{2})\b", fields.get("released", ""))
    assert years and len(set(years)) == 1, \
        "the game's release dates are %r" % years

    # the series' second film: announced, in production, and undated — the
    # notes say so, and a date appearing must break the build so it is listed
    second = re.search(r"In October (\d{4}), it was announced that a second "
                       r"film of the series is in production\.",
                       strip_refs(franchise_text))
    assert second, "the franchise article no longer says the series' second " \
                   "film is in production with no date — re-read it: dated, " \
                   "it ships as a w: 0 row; out, as a row"
    return int(years[0])


def series_film_evidence(franchise_text):
    """Awakening Mystery, read from the franchise article's Films prose.

    The episode-list article does not carry it, so its title, premiere date
    and place after season 2 all come from here. Returns (announced year,
    first year, (y, m, d) premiere)."""
    body = strip_refs(franchise_text)
    ahead = re.search(r"In August (\d{4}), it was announced that a series of "
                      r"films would be released starting in (\d{4})\.", body)
    assert ahead, "the franchise article no longer describes the announced " \
                  "film series"
    first = re.search(r"The first film, \{\{Nihongo\|''([^'|]+)''\|[^{}]*\}\}, "
                      r"premiered on (\w+) (\d{1,2}), (\d{4})\.", body)
    assert first, "the franchise article no longer names and dates the film " \
                  "series' first film"
    assert first.group(1) == SERIES_FILM, \
        "the series' first film is titled %r, expected %r" \
        % (first.group(1), SERIES_FILM)
    dated = (int(first.group(4)), MONTHS[first.group(2)], int(first.group(3)))
    assert dated[0] == int(ahead.group(2)), \
        "the series was to start in %s, its first film premiered in %s" \
        % (ahead.group(2), dated[0])
    assert re.search(r"A sequel film to the second season has been "
                     r"(?:announced|released)", body), \
        "the franchise article's lead no longer calls the new film a sequel " \
        "to the second season — that is why it sits after season 2"
    return int(ahead.group(1)), dated


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
    franchise_text = text(FRANCHISE_PAGE)
    overview = series_overview(list_text)
    seg = segments(list_text)
    check_accent()

    s1 = season_rows(seg["s1"], 1, overview)
    s2 = season_rows(seg["s2"], 2, overview)
    films = film_rows(seg["films"])

    # 1. overall numbering runs 1..25 unbroken across the two seasons
    numbered = sorted(o for o, _, _, _, _ in s1 + s2)
    assert numbered == list(range(1, TOTAL_EPISODES + 1)), \
        "overall episode numbering is not contiguous 1..%d" % TOTAL_EPISODES

    # 2. which films are re-cuts, and of exactly what
    comps = compilation_evidence(list_text)
    (c1, c1a, c1b), (c2, c2a, c2b) = comps
    assert c1a == 1, "the first compilation starts at episode %d" % c1a
    assert c2a == c1b + 1, \
        "the compilations leave a gap: %d–%d then %d–%d" % (c1a, c1b, c2a, c2b)
    assert c2b == overview[1][0], \
        "the compilations cover episodes 1–%d, season 1 has %d — they no " \
        "longer tile the season and the double-count argument must be " \
        "re-made" % (c2b, overview[1][0])

    # 3. and which one is not
    sequel_dated = sequel_evidence(list_text, franchise_text)
    film_date, film_mins, comp_mins = franchise_video_blocks(franchise_text)
    game_year = check_exclusions(list_text, franchise_text)
    announced, series_date = series_film_evidence(franchise_text)
    assert film_date == sequel_dated, \
        "the infobox dates the film %s, the prose says %s" \
        % (film_date, sequel_dated)

    # 4. the film section holds the two compilations then the sequel, in that
    #    order — the source's running order, and the reason the sequel sits
    #    between the seasons rather than after them
    film_titles = [t for _, t, _ in films]
    assert film_titles == ["Made in Abyss: %s" % c for c in COMPILATIONS] \
        + [SEQUEL_FILM], "the film section lists %r" % film_titles
    assert films[-1][2] == film_date, \
        "the film table dates the sequel %s, the infobox says %s" \
        % (films[-1][2], film_date)
    assert all(d[0] == 2019 for _, _, d in films[:2]), \
        "the compilations are dated %r" % [d for _, _, d in films[:2]]
    assert s1[-1][3] < films[-1][2] < s2[0][3], \
        "the film no longer falls between the two seasons in time"
    assert s2[-1][3] < series_date, \
        "Awakening Mystery no longer falls after season 2 in time"

    # 5. the two footnoted episode lengths — the only ones in the source, and
    #    the reason the weights note can say exactly what is missing
    finale_note = re.search(r'\{\{efn\|name="1h"\|([^{}]+)\}\}', list_text)
    assert finale_note, "the one-hour-finale footnote has gone"
    assert finale_note.group(1).strip() == "One hour season finale special.", \
        "the finale footnote now reads %r" % finale_note.group(1)
    long_eps = {o for o, _, _, _, block in s1 + s2
                if 'efn|name="1h"' in block}
    assert long_eps == {s1[-1][0], s2[-1][0]}, \
        "the one-hour footnote is on episodes %r, expected the two season " \
        "finales" % sorted(long_eps)

    sections = []

    # --- Season 1 ----------------------------------------------------------
    sections.append({
        "id": "s1",
        "title": "Season 1",
        "sub": prop.join_bits("2017", "%d episodes" % len(s1)),
        "intro": "The whole first season, and the place to start. The two "
                 "2019 compilation films re-cut exactly these thirteen "
                 "episodes and are not listed; see the notes.",
        "open": True,
        "items": [
            {"id": "mia-s1e%d" % s, "t": t, "n": str(s),
             **({"note": "One-hour season finale"} if o == s1[-1][0] else {})}
            for o, s, t, _d, _b in s1
        ],
    })

    # --- the film that is not a re-cut -------------------------------------
    sections.append({
        "id": "film",
        "title": "Dawn of the Deep Soul",
        "sub": prop.join_bits(str(film_date[0]), "the sequel film",
                              "%d minutes" % film_mins),
        "intro": "A sequel, not a compilation. "
                 "The source's own note on season 2's first episode says that "
                 "season picks up directly after it, so it sits here — "
                 "between the seasons, where the episode-list article puts "
                 "it.",
        "items": [{
            "id": "mia-film-%s" % prop.slug("Dawn of the Deep Soul"),
            "t": SEQUEL_FILM,
            "n": str(film_date[0]),
            "note": prop.join_bits("Feature film", "%d minutes" % film_mins,
                                   "premiered %s" % fmt_date(film_date)),
        }],
    })

    # --- Season 2 ----------------------------------------------------------
    sections.append({
        "id": "s2",
        "title": "Season 2: The Golden City of the Scorching Sun",
        "sub": prop.join_bits("2022", "%d episodes" % len(s2)),
        "intro": "Five years after the first season and straight on from the "
                 "film.",
        "items": [
            {"id": "mia-s2e%d" % s, "t": t, "n": str(s),
             **({"note": "One-hour season finale"} if o == s2[-1][0] else {})}
            for o, s, t, _d, _b in s2
        ],
    })

    # --- the film series' first film ---------------------------------------
    sections.append({
        "id": "awakening",
        "title": "Awakening Mystery",
        "sub": prop.join_bits(str(series_date[0]), "the sequel to season 2"),
        "intro": "The first film of the series announced in %d. The franchise "
                 "article calls it a sequel to the second season, so it comes "
                 "last." % announced,
        "items": [{
            "id": "mia-film-%s" % prop.slug("Awakening Mystery"),
            "t": SERIES_FILM,
            "n": str(series_date[0]),
            "note": prop.join_bits("Feature film",
                                   "premiered %s" % fmt_date(series_date)),
        }],
    })

    assert [s["id"] for s in sections] == ["s1", "film", "s2", "awakening"], \
        [s["id"] for s in sections]
    total = sum(len(s["items"]) for s in sections)
    assert total == LISTED, "%d rows, expected %d" % (total, LISTED)
    assert sum(1 for s in sections for x in s["items"] if "w" in x) == 0, \
        "a weight crept in — this list is unweighted end to end"
    # a year in an episode note would make that row a cross-list sync
    # candidate keyed on title+year; only the film row may carry one
    for s in sections:
        for x in s["items"]:
            if x["id"].startswith("mia-film"):
                continue
            assert not re.search(r"\b(18|19|20)\d{2}\b", x.get("note") or ""), \
                "episode row %s names a year in its note" % x["id"]

    p = {
        "slug": SLUG,
        "title": "Made in Abyss",
        "subtitle": "both seasons, and the two films that are not re-cuts",
        "kind": "anime & films",
        "popularity": 55,
        "year": "2017–%d" % series_date[0],
        "blurb": "Kinema Citrus' descent, in the source's own order — twenty "
                 "five episodes, the sequel film between the seasons and the "
                 "%d film after them, with the two compilation films left off."
                 % series_date[0],
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ["Four films exist. Two of them are rows.",
             "%s (%s) and %s (%s) are compilation films: the source says they "
             "cover episodes %d–%d and %d–%d, which is the whole of season "
             "one, re-cut for cinemas with a new introduction. They are the "
             "same viewing as the episodes above, so listing them would count "
             "season one twice. If you would rather watch that season as two "
             "sittings than as thirteen, they are how — and that is all they "
             "are."
             % (c1, fmt_date(films[0][2]), c2, fmt_date(films[1][2]),
                c1a, c1b, c2a, c2b)],
            ["Dawn of the Deep Soul is not one of them.",
             "It is a sequel and it cannot be skipped. The franchise "
             "article's lead calls it \"a sequel film\", the episode-list "
             "article separates it from the compilations by name, and the "
             "footnote on season two's first episode says that season begins "
             "directly after it. So it sits between the seasons, which is "
             "also where the source's own running order puts it: all three "
             "films share one section there, and this list keeps the "
             "position while dropping the two re-cuts."],
            ["Nothing is weighted, and hours are not tracked here.",
             "Wikipedia documents no running time for this series: neither "
             "television infobox has one and not one of the twenty-five "
             "episode blocks carries one. The only lengths in the source are "
             "Dawn of the Deep Soul's %d minutes and a footnote calling each "
             "season's "
             "finale a one-hour special. Two durations out of twenty-five "
             "cannot weight a list, and weighting only the film would be "
             "worse than weighting nothing — an unweighted row silently "
             "counts as a full hour, so twenty-five half-hour episodes would "
             "read as twenty-five hours. Every row counts one, the films "
             "included, and Dawn of the Deep Soul's runtime is in its row "
             "note instead."
             % film_mins],
            ["What else is deliberately absent.",
             "The four \"Marulk's Daily Life\" shorts that screened with Dawn "
             "of the Deep Soul. The manga the series adapts, and the %d "
             "game. A second film in the series that began with "
             "Awakening Mystery is in production; the source gives it no release date, so it joins "
             "when it opens. This list is the anime television run and the "
             "films that are not re-cuts of it." % game_year],
            "Episode titles, air dates, film dates and runtimes machine-read "
            "from Wikipedia's \"List of Made in Abyss episodes\" and \"Made "
            "in Abyss\" articles; each season's count, first air date and "
            "last air date are asserted against the list article's series "
            "overview, and the compilation films' episode ranges are asserted "
            "to tile season one exactly, before this builds.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d rows in %d sections (%d episodes + 2 films)"
          % (out.name, total, len(sections), TOTAL_EPISODES))
    print("   compilations refused: %s"
          % ", ".join("%s (%d–%d, %d min)" % (n, a, b, m)
                      for (n, a, b), m in zip(comps, comp_mins)))
    for s in sections:
        span = s["sub"].split(" · ")[0]
        print("   %-46s %3d  %s" % (s["title"], len(s["items"]), span))
    print("   weighted: no (no episode runtime in the source)")


if __name__ == "__main__":
    main()
