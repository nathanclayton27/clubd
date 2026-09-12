#!/usr/bin/env python3
"""Generate properties/chuck.json — all 91 episodes, one section per season.

    PYTHONIOENCODING=utf-8 python tools/make_chuck.py
    PYTHONIOENCODING=utf-8 python tools/make_chuck.py --refetch

Two sources, each doing the one job it is authoritative for:

  * TITLES, NUMBERING AND AIR DATES come from Wikipedia's five "Chuck season
    N" articles, which are where the episode tables actually live — "List of
    Chuck episodes" only transcludes them ({{:Chuck season 1}}), so parsing
    the list page returns no rows at all. Read through
    gwlib.wiki.episodes(); every season's numbering is asserted contiguous,
    and the five counts are cross-checked against the list page's own
    {{Series overview}} and its {{Aired episodes|num=91}}.

  * RUNTIMES come from the Apple TV / iTunes Store listing for "Chuck: The
    Complete Series" (collection 700656050), which publishes a duration per
    episode — 91 of them, in season-and-episode order, keyed in each
    trackName as "Season N, Episode M: Title". This is the only machine-read
    per-episode runtime found for this show: the episodes have no P2047 on
    Wikidata (checked on the pilot, Q5115791, which carries 22 properties and
    no duration), and only a handful of them have their own Wikipedia article
    to read an {{Infobox television episode}} |length out of.

WHY NOT MULTIPLY 91 BY 43. Because that is inventing 91 numbers and calling
them data, and the real ones are not all 43: the published figures run from
41.3 minutes (season 1's "Chuck Versus the Sandworm") to 44.4 (the last
episode). The spread is small — this is a network hour, not an anthology —
but it is measured rather than assumed, and the total is asserted to sit
inside the runtime band Wikipedia's own series infobox states.

THE NAME GATE IS MANDATORY AND IT ALLOWS EXACTLY ONE MISMATCH. A runtime is
only believed when the storefront's title for that (season, episode) slot
normalises to Wikipedia's title for it — the same verify-by-name rule
gwlib.hltb applies to games, because a runtime attached to the wrong row is
worse than no runtime. 90 of the 91 match outright. The one that does not is
the pilot: the storefront files it as "Pilot" where the broadcast title is
"Chuck Versus the Intersect". That exception is declared below, asserted to
be the only one, and asserted to be that specific pair — a second mismatch
appearing, or this one changing shape, fails the build rather than shipping a
misaligned weight. Normalisation folds case, punctuation and the article
"the", which is what absorbs the four rows where the two sources disagree
only on "the" ("Chuck Versus Gravitron" / "Chuck Versus the Gravitron",
"Chuck Versus the Phase Three" / "Chuck Versus Phase Three", "Chuck Versus
Hack Off" / "Chuck Versus the Hack Off", and "Chuck Versus The Last
Details"). Wikipedia's spelling is the one that ships, in every case.

TITLES ARE VERBATIM. Every one of the 91 begins "Chuck Versus", the pilot
included, and the generator asserts that rather than trusting it. Trimming
the pattern to "the Intersect" would read as a different show.

SPOILERS. No row carries a note, and nothing anywhere describes what happens
in an episode. Section subtitles are year, count and hours. The four section
intros are production facts — strike-shortened orders, back-nine pickups, the
final renewal — of exactly the kind spoilerscan rules as "a production or
biographical fact, not a reveal".

THE DATA FILE IS THE CACHE. tools/data/chuck-episodes.json holds what the two
sources said, fetched once; the generator reads it and refetches only when it
is missing or --refetch is passed. So two consecutive runs are byte-identical
and no build depends on a network round trip.
"""
import json
import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki  # noqa: E402

SLUG = "chuck"
HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "data" / "chuck-episodes.json"
CACHE = HERE.parent / "scratch" / "agent-chuck"

LIST_PAGE = "List of Chuck episodes"
SERIES_PAGE = "Chuck (TV series)"
SEASON_PAGE = "Chuck season %d"
WIKI_URL = "https://en.wikipedia.org/wiki/Chuck_season_%d"

# The storefront collection that carries a runtime per episode, and the show
# it must belong to. Both are verified on every fetch; a collection that has
# moved, been re-cut, or belongs to another artist fails rather than being
# believed.
ITUNES_LOOKUP = ("https://itunes.apple.com/lookup?id=%d&entity=tvEpisode"
                 "&limit=200&country=US")
ITUNES_COLLECTION = 700656050
ITUNES_ARTIST = 262603760
ITUNES_ARTIST_NAME = "Chuck"

TOTAL = 91
EXPECT = {1: 13, 2: 22, 3: 19, 4: 24, 5: 13}

# The single tolerated title disagreement: (season, episode) -> the storefront's
# own name for it. Declared, not discovered, so a NEW mismatch is a failure.
NAME_EXCEPTIONS = {(1, 1): "Pilot"}

# Production facts only. Each is on the list page or the series article.
INTROS = {
    1: "Thirteen episodes: the 2007–08 writers' strike cut the first season "
       "short, and NBC renewed the show for a second season rather than "
       "extending it to a full twenty-two.",
    3: "Nineteen episodes: thirteen were ordered in May 2009, and NBC added "
       "six more that October, before the season began airing.",
    4: "Twenty-four episodes, the longest season — thirteen ordered, then "
       "eleven more rather than the usual back nine.",
    5: "Thirteen episodes: NBC renewed the show for a fifth and final season "
       "in May 2011.",
}

MONTHS = ("January February March April May June July August September "
          "October November December").split()


# --------------------------------------------------------------- normalisation
def norm(t):
    """Fold a title for matching: accents, case, punctuation and "the".

    Dropping the article is what lets the storefront's "Chuck Versus
    Gravitron" verify against Wikipedia's "Chuck Versus the Gravitron". It is
    narrow on purpose — every other word still has to be there, in order.
    """
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    t = re.sub(r"[^a-z0-9]+", " ", t).strip()
    return " ".join(w for w in t.split() if w != "the")


def hm(minutes):
    """"9h 25m" — never "N hours", which qa_lint reconciles against weights."""
    m = int(round(minutes))
    return "%dh %dm" % (m // 60, m % 60) if m >= 60 else "%dm" % m


WORDS = ("no one two three four five six seven eight nine ten eleven twelve "
         "thirteen").split()


def words(n):
    """Small counts read as words in prose; the figure is still derived."""
    return WORDS[n] if n < len(WORDS) else str(n)


def year_span(dates):
    """"2007–08" from ISO air dates, the shape Wikipedia's own headings use."""
    ys = sorted({int(d[:4]) for d in dates})
    assert ys, "no air dates"
    if ys[0] == ys[-1]:
        return str(ys[0])
    a, b = ys[0], ys[-1]
    return "%d–%02d" % (a, b % 100) if a // 100 == b // 100 else "%d–%d" % (a, b)


# ----------------------------------------------------------------- the sources
def wiki_rows():
    """The five season articles' episode tables, plus the list page's own
    counts as an independent cross-check of them."""
    listing = wiki.wikitext(LIST_PAGE, cache_dir=CACHE)
    assert listing, "could not read %r" % LIST_PAGE

    # {{Aired episodes|num=91|...}} — the page's own headline figure.
    m = re.search(r"\{\{\s*Aired episodes\s*\|[^}]*?\bnum\s*=\s*(\d+)",
                  listing, re.I)
    assert m, "the list page no longer carries {{Aired episodes|num=...}}"
    aired = int(m.group(1))

    # {{Series overview}} episodesN — the page's own per-season figures.
    so = re.search(r"\{\{Series overview(.*?)\n\}\}", listing, re.S)
    assert so, "no {{Series overview}} on the list page"
    overview = {int(k): int(v) for k, v in
                re.findall(r"\|\s*episodes(\d+)\s*=\s*(\d+)", so.group(1))}
    assert overview, "no episodesN fields in {{Series overview}}"

    # The series infobox's stated runtime band, used to sanity-gate the
    # storefront's figures rather than to produce any of them.
    series = wiki.wikitext(SERIES_PAGE, cache_dir=CACHE)
    assert series, "could not read %r" % SERIES_PAGE
    ib = wiki.infobox(series, kind=r"television")
    assert ib, "no {{Infobox television}} on %r" % SERIES_PAGE
    band = re.findall(r"\d+", ib("runtime"))
    assert len(band) == 2, "series runtime is not a two-ended band: %r" \
        % ib("runtime")[:60]
    lo_band, hi_band = int(band[0]), int(band[1])
    assert lo_band < hi_band, "series runtime band is inverted: %r" % band

    rows = []
    for season in sorted(EXPECT):
        text = wiki.wikitext(SEASON_PAGE % season, cache_dir=CACHE)
        assert text, "could not read %r" % (SEASON_PAGE % season)
        eps = wiki.episodes(text)
        assert eps, "no episode rows on %r" % (SEASON_PAGE % season)
        for e in eps:
            raw = wiki.field(e.fields, "OriginalAirDate") or ""
            d = re.search(r"\{\{\s*Start date\s*\|\s*(\d{4})\s*\|\s*(\d{1,2})"
                          r"\s*\|\s*(\d{1,2})", raw, re.I)
            assert d, "no {{Start date}} on s%de%s: %r" % (season, e[1], raw[:60])
            y, mo, dy = (int(x) for x in d.groups())
            assert e[0] and e[1], "unnumbered row on season %d: %r" % (season, e[2])
            assert e[2], "row with no title on season %d, episode %s" % (season, e[1])
            rows.append({"s": season, "e": e[1], "n": e[0], "t": e[2],
                         "air": "%04d-%02d-%02d" % (y, mo, dy)})
    return rows, {"aired": aired, "overview": overview,
                  "runtime_band": [lo_band, hi_band]}


def itunes_rows():
    """{(season, episode): (storefront title, milliseconds)} for all 91."""
    d = wiki.get_json(ITUNES_LOOKUP % ITUNES_COLLECTION)
    coll = [r for r in d.get("results", []) if r.get("wrapperType") == "collection"]
    assert len(coll) == 1, "expected one collection in the lookup, got %d" % len(coll)
    c = coll[0]
    assert c.get("artistId") == ITUNES_ARTIST and \
        c.get("artistName") == ITUNES_ARTIST_NAME, \
        "collection %d is not Chuck's any more: %r / %r" \
        % (ITUNES_COLLECTION, c.get("artistId"), c.get("artistName"))
    assert "Complete Series" in (c.get("collectionName") or ""), \
        "collection %d is no longer the complete series: %r" \
        % (ITUNES_COLLECTION, c.get("collectionName"))
    assert c.get("trackCount") == TOTAL, \
        "the complete-series collection now states %r tracks, not %d" \
        % (c.get("trackCount"), TOTAL)

    out = {}
    for r in d["results"]:
        if r.get("wrapperType") != "track":
            continue
        m = re.match(r"Season (\d+), Episode (\d+): (.+)$", r.get("trackName") or "")
        assert m, "a track name no longer carries its numbering: %r" \
            % (r.get("trackName") or "")[:70]
        ms = r.get("trackTimeMillis")
        assert isinstance(ms, int) and ms > 0, \
            "no duration on %r" % r.get("trackName")
        key = (int(m.group(1)), int(m.group(2)))
        assert key not in out, "two tracks for season %d episode %d" % key
        out[key] = (m.group(3), ms)
    assert len(out) == TOTAL, "read %d storefront tracks, expected %d" \
        % (len(out), TOTAL)
    return out


def fetch():
    """Read both sources, reconcile them, and write the committed data file."""
    rows, meta = wiki_rows()
    store = itunes_rows()

    exceptions = {}
    for r in rows:
        key = (r["s"], r["e"])
        assert key in store, "no storefront track for season %d episode %d" % key
        st_title, ms = store[key]
        if norm(st_title) != norm(r["t"]):
            exceptions[key] = st_title
        r["store_t"] = st_title
        r["ms"] = ms

    # The gate: the only tolerated mismatch is the declared one, and it has to
    # be the same mismatch it was when this was written.
    assert exceptions == NAME_EXCEPTIONS, \
        "the storefront titles no longer line up as expected — declared %r, " \
        "found %r. A runtime on the wrong row is worse than no runtime." \
        % (NAME_EXCEPTIONS, exceptions)

    payload = {
        "source": {
            "titles": "Wikipedia, the five 'Chuck season N' articles, read "
                      "through gwlib.wiki.episodes()",
            "counts": "Wikipedia, 'List of Chuck episodes' — {{Series "
                      "overview}} and {{Aired episodes}}",
            "runtimes": "Apple TV / iTunes Store, 'Chuck: The Complete "
                        "Series', collection %d, one duration per episode"
                        % ITUNES_COLLECTION,
            "name_gate": "a runtime is believed only where the storefront's "
                         "title for that slot normalises to Wikipedia's; the "
                         "one declared exception is the pilot, which the "
                         "storefront files as 'Pilot'",
        },
        "aired_total": meta["aired"],
        "overview": {str(k): v for k, v in sorted(meta["overview"].items())},
        "series_runtime_band": meta["runtime_band"],
        "name_exceptions": {"s%de%d" % k: v for k, v in sorted(exceptions.items())},
        "episodes": rows,
    }
    DATA.parent.mkdir(parents=True, exist_ok=True)
    with DATA.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print("fetched %d episodes -> %s" % (len(rows), DATA.name))
    return payload


# ------------------------------------------------------------------- the build
def main():
    if "--refetch" in sys.argv or not DATA.exists():
        data = fetch()
    else:
        data = json.loads(DATA.read_text(encoding="utf-8"))

    rows = data["episodes"]
    overview = {int(k): v for k, v in data["overview"].items()}
    lo_band, hi_band = data["series_runtime_band"]

    # ---- the count, three ways, before anything is built ------------------
    assert len(rows) == TOTAL, "the data file holds %d episodes, not %d" \
        % (len(rows), TOTAL)
    assert data["aired_total"] == TOTAL, \
        "the source's own headline figure is %d episodes, not %d — the source " \
        "wins and this expectation needs revisiting" % (data["aired_total"], TOTAL)
    assert overview == EXPECT, \
        "the source's {{Series overview}} now says %r, not %r" % (overview, EXPECT)
    assert [r["n"] for r in rows] == list(range(1, TOTAL + 1)), \
        "the overall numbering is not the contiguous run 1-%d" % TOTAL
    assert data["name_exceptions"] == \
        {"s%de%d" % k: v for k, v in sorted(NAME_EXCEPTIONS.items())}, \
        "the data file's title exceptions are not the declared ones"

    # ---- every title keeps the pattern -----------------------------------
    for r in rows:
        assert r["t"].startswith("Chuck Versus"), \
            "title %r does not begin 'Chuck Versus' — the pattern is the joke " \
            "and trimming it reads as a different show" % r["t"]

    # ---- sections --------------------------------------------------------
    sections, mins_total = [], 0.0
    for season in sorted(EXPECT):
        eps = [r for r in rows if r["s"] == season]
        assert [r["e"] for r in eps] == list(range(1, EXPECT[season] + 1)), \
            "season %d numbering is not 1-%d" % (season, EXPECT[season])
        items, mins = [], 0.0
        for r in eps:
            minutes = r["ms"] / 60000.0
            assert lo_band <= round(minutes) <= hi_band, \
                "s%de%d runs %.1f minutes, outside the %d-%d band the series " \
                "article states" % (season, r["e"], minutes, lo_band, hi_band)
            w = round(minutes / 60.0, 2)
            items.append({"id": "chuck-s%de%d" % (season, r["e"]), "t": r["t"],
                          "n": str(r["e"]), "w": w})
            # Accumulated from the STORED weight, not the raw minutes, so the
            # five section subtitles add up to the total the notes state and
            # to the figure the site's own pace maths will reach. Summing raw
            # minutes here put the parts five minutes under the whole.
            mins += w * 60.0
        mins_total += mins
        section = {
            "id": "s%d" % season,
            "title": "Season %d" % season,
            "sub": "%s · %d episodes · %s" % (
                year_span([r["air"] for r in eps]), len(eps), hm(mins)),
            "links": [{"label": "Episode list", "url": WIKI_URL % season}],
            "items": items,
        }
        if season in INTROS:
            section["intro"] = INTROS[season]
        sections.append(section)
    sections[0]["open"] = True

    items = [x for s in sections for x in s["items"]]
    assert len(items) == TOTAL, "built %d rows, expected %d" % (len(items), TOTAL)
    # An unweighted row in a weighted list silently counts as one hour
    # (CLU-131), which on a 43-minute show is wrong by a third.
    assert all(isinstance(x["w"], float) and x["w"] > 0 for x in items), \
        "a row has no weight"

    # Everything the prose states is derived from the weights the site will
    # actually add up, not from the raw minutes, so the two can never drift.
    hours = sum(x["w"] for x in items)
    shortest = min(r["ms"] for r in rows) / 60000.0
    longest = max(r["ms"] for r in rows) / 60000.0

    # How many titles the two sources spell differently once case and
    # punctuation are set aside, minus the declared pilot exception. Counted
    # rather than typed: the note said "four" while the data said three, which
    # is exactly the drift a hard-coded figure produces.
    def bare(t):
        t = unicodedata.normalize("NFKD", t)
        t = "".join(c for c in t if not unicodedata.combining(c)).lower()
        return re.sub(r"[^a-z0-9]+", " ", t).strip()
    article_only = sum(1 for r in rows
                       if bare(r["t"]) != bare(r["store_t"])
                       and (r["s"], r["e"]) not in NAME_EXCEPTIONS)
    assert article_only, "no title spellings differ any more — recheck the note"

    p = {
        "slug": SLUG,
        "title": "Chuck",
        "subtitle": "every episode, season by season",
        "kind": "tv",
        # 40-59, enthusiast territory: five seasons and 91 episodes on NBC is
        # real network reach, and the Subway campaign that kept it alive is a
        # story people outside the audience have heard — but the title now
        # needs a sentence of explanation, which 60+ does not. Placed just
        # above Gossip Girl 57 and Friday Night Lights 56, its own network-era
        # neighbours, and below Columbo 59 and Babylon 5 60.
        "popularity": 58,
        "year": "2007–2012",
        "blurb": "All 91 episodes across five seasons, in air order and "
                 "weighted by each episode's published runtime — about %d "
                 "hours." % round(hours),
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        # The Buy More's own signage: a yellow-green sitting on the olive side
        # of green, lifting to a pale Nerd Herd green in the dark theme. The
        # plain greens were all taken — measured in CIELAB against all 227
        # accents already shipped, #708A3E sits 13.1 from its nearest
        # light-mode neighbour (Gilliam #7A7A29, then President Curtis, then
        # Urusei Yatsura) and #C6E69A sits 14.6 from its nearest dark-mode one
        # (Zombie Films, then Metal Gear). A straight Buy More green landed
        # 2.8 from Green Lantern.
        "accent": "#708A3E",
        "accentDark": "#C6E69A",
        "tiers": False,
        "notes": [
            ["Weighted by real runtime, every row.",
             "Each weight is that episode's own published duration rather "
             "than a network hour assumed for all 91. They run from %d to %d "
             "minutes — a narrow spread, as a network drama's should be, but "
             "measured rather than guessed. %d episodes, %s in total, and the "
             "finish date is built on those figures." %
             (round(shortest), round(longest), TOTAL, hm(hours * 60))],
            ["The seasons are not the same length.",
             "Thirteen, twenty-two, nineteen, twenty-four, thirteen. The "
             "first season was cut short by the 2007–08 writers' strike, the "
             "third and fourth were each extended past their original "
             "thirteen-episode orders, and the fifth was commissioned as a "
             "final thirteen. The section subtitles carry "
             "the years and the counts so the shape is visible without "
             "counting rows."],
            ["Titles are printed as broadcast.",
             "All %d begin \"Chuck Versus\", the pilot included — it is "
             "\"Chuck Versus the Intersect\", which is easy to mistake for a "
             "later episode. The pattern is not trimmed anywhere here. One "
             "aside for anyone matching this list against a storefront: Apple "
             "files the pilot as \"Pilot\", and disagrees with Wikipedia about "
             "the word \"the\" on %s other titles. Wikipedia's spelling is "
             "what ships." % (TOTAL, words(article_only))],
            ["No episode notes.",
             "Nothing on this page says what happens in an episode. The "
             "subtitles are years, counts and hours; the four section intros "
             "are production facts about how many episodes were ordered and "
             "when."],
            "Titles, numbering and air dates machine-read from Wikipedia's "
            "five Chuck season articles, with the per-season counts "
            "cross-checked against the list page's own series overview; "
            "per-episode runtimes from the Apple TV listing for Chuck: The "
            "Complete Series, matched on season and episode number and "
            "verified by title before any weight is believed.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d episodes in %d sections, %s"
          % (out.name, len(items), len(sections), hm(hours * 60)))
    for s in sections:
        print("   %-10s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))
    print("   runtime range: %.2f-%.2f minutes" % (shortest, longest))


if __name__ == "__main__":
    main()
