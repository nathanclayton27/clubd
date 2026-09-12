#!/usr/bin/env python3
"""Generate properties/futurama.json — every episode, plus the four films.

    python3 tools/make_futurama.py

Four eras in the order they went out: the Fox run (production seasons 1-4),
the four direct-to-video films, the Comedy Central revival (6-7) and the Hulu
revival (8-11). 163 rows.

THE FILMS COUNT ONCE. The four 2007-09 films were re-cut into sixteen
half-hour episodes and broadcast as Comedy Central's "season 5"; the two are
the same footage, so listing both would count the same watch twice. This list
carries FOUR film rows, not sixteen episode rows, because:

  * the films are the form the work was written, animated and released in —
    the sixteen parts are a later broadcast re-cut of them;
  * Wikipedia's season 5 article gives those sixteen parts no titles of their
    own (one {{Episode list/sublist}} block per film, NumParts = 4), so
    shipping sixteen rows would mean inventing sixteen titles; and
  * a row is a thing you sit down and finish, and you finish a film.

Each film row names its runtime and the season 5 episodes it was broadcast
as, so nothing about the other representation is hidden. Choosing the films
puts the list at 163 rows; the sixteen-part reading would have made it 175,
which is the number Wikipedia's series infobox carries.

ORDER. Fox aired the first 72 episodes out of the order they were made, so a
strict broadcast sort matches no box set, no streaming season and not the
source article either. This list follows the production seasons — what
Wikipedia's list, the DVD volumes and the streaming seasons all use — with
the eras themselves in the order they reached an audience.

WEIGHTS. None. Wikipedia documents one running time for the series (22
minutes) and none per episode, so there is no verifiable per-row number to
weight with; every row counts one and no row carries `w`. Mixing a weighted
film row into unweighted episodes would make each unweighted row silently
count as an hour, which is the bug this avoids outright.

Everything is machine-read from the cached Wikipedia wikitext in
scratch/futurama/ — "List of Futurama episodes", the eleven season articles
and the four film articles. Each season's row count is asserted against the
list article's own {{Series overview}} before anything is written, and the
overall episode numbers are asserted contiguous.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki  # noqa: E402

SLUG = "futurama"
CACHE = prop.ROOT / "scratch" / "futurama"
LIST_PAGE = "List of Futurama episodes"

# Season 11 was mid-run when this was built. Only episodes that had actually
# aired by this date are listed; the constant is hard-coded rather than read
# from the clock so re-running this produces the same file. It is the date the
# source article itself carries in its {{Aired episodes}} stamp.
AIRED_THROUGH = (2026, 8, 24)

# The Fox run's four seasons, then Comedy Central's two, then Hulu's four.
# Season 5 is the films and is built separately.
EPISODE_SEASONS = [1, 2, 3, 4, 6, 7, 8, 9, 10, 11]

ERA = {
    1: ("Fox", "The original run, cancelled in 2003. Fox aired these 72 "
                "episodes out of the order they were made; the list follows "
                "the production seasons, the way the box sets and the "
                "streaming seasons do."),
    6: ("Comedy Central", "Comedy Central ordered 26 more episodes after the "
                          "films did well. Each of its two seasons was split "
                          "in half and aired a year apart."),
    8: ("Hulu", "The second revival, ordered in 2022 and still running."),
}
ERA_OF = {1: "Fox", 2: "Fox", 3: "Fox", 4: "Fox",
          6: "Comedy Central", 7: "Comedy Central",
          8: "Hulu", 9: "Hulu", 10: "Hulu", 11: "Hulu"}

FILM_PAGES = ["Futurama: Bender's Big Score",
              "Futurama: The Beast with a Billion Backs",
              "Futurama: Bender's Game",
              "Futurama: Into the Wild Green Yonder"]


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


def series_overview(list_text):
    """{'season number': 'episode count'} from the list article's own table."""
    seg = re.search(r"\{\{Series overview(.*?)\n\}\}", list_text, re.S)
    assert seg, "no series overview"
    counts = {int(m.group(1)): int(m.group(2)) for m in
              re.finditer(r"\|\s*episodes(\d+)\s*=\s*(\d+)", seg.group(1))}
    assert counts, "series overview carries no episode counts"
    return counts


def read_episodes(list_text):
    """{season: [(overall, in_season, title, (y, m, d))]} for every season but
    the films. Seasons 1-10 come from their own articles; season 11 has no
    article yet and is listed inline in the list article."""
    out = {}
    for n in EPISODE_SEASONS:
        if n == 11:
            parts = list_text.split("=== Season 11 (2026) ===")
            assert len(parts) == 2, "season 11 heading moved"
            raw = wiki.episodes(parts[1])
        else:
            raw = wiki.episodes(text("Futurama season %d" % n))
        rows = [(o, s, t, airdate(b)) for o, s, t, _, b in raw]
        assert rows, "season %d parsed empty" % n
        for o, s, t, _ in rows:
            assert o and s and t, "season %d row incomplete: %r" % (n, (o, s, t))
        assert [s for _, s, _, _ in rows] == list(range(1, len(rows) + 1)), \
            "season %d numbering is not 1..%d" % (n, len(rows))
        out[n] = rows
    return out


def read_films():
    """The four films: title, DVD year, runtime, and the season 5 episode
    numbers they were broadcast as. One {{Episode list/sublist}} block each."""
    season5 = text("Futurama season 5")
    blocks = season5.split("{{Episode list/sublist|Futurama season 5")[1:]
    assert len(blocks) == 4, "expected 4 film blocks, got %d" % len(blocks)

    films = []
    for i, block in enumerate(blocks):
        block = block[:block.index("| LineColor")]

        def field(name):
            m = re.search(r"\|\s*%s\s*=\s*(.*?)(?=\n\s*\||\Z)" % name, block, re.S)
            return m.group(1).strip() if m else ""

        assert field("NumParts") == "4", "film %d is not four parts" % (i + 1)
        title = wiki.clean(field("RTitle"))
        assert title, "film %d has no title" % (i + 1)

        parts = [int(field("EpisodeNumber2_%d" % p)) for p in range(1, 5)]
        overall = [int(field("EpisodeNumber_%d" % p)) for p in range(1, 5)]
        assert parts == list(range(i * 4 + 1, i * 4 + 5)), parts
        assert overall == list(range(72 + i * 4 + 1, 72 + i * 4 + 5)), overall
        codes = [field("ProdCode_%d" % p) for p in range(1, 5)]
        assert codes == ["5ACV%02d" % p for p in
                         range(i * 4 + 1, i * 4 + 5)], codes

        # two dates on the row: the DVD release, then the Comedy Central
        # broadcast. The DVD one comes first and is the film's own release.
        dvd_year = airdate(field("OriginalAirDate"))[0]

        infobox = wiki.infobox(text(FILM_PAGES[i]), kind="film")
        assert infobox, "no film infobox for %s" % FILM_PAGES[i]
        rt = re.search(r"(\d+)\s*minutes", infobox("runtime"))
        assert rt, "no runtime for %s" % FILM_PAGES[i]
        mins = int(rt.group(1))
        assert 70 <= mins <= 120, "%s runtime %d looks wrong" % (title, mins)

        films.append({"t": title, "year": dvd_year, "mins": mins,
                      "parts": parts})
    return films


def main():
    list_text = text(LIST_PAGE)
    overview = series_overview(list_text)
    episodes = read_episodes(list_text)
    films = read_films()

    # the source article's own table is the check on every count we parsed
    for n, rows in episodes.items():
        assert len(rows) == overview[n], \
            "season %d: parsed %d rows, overview says %d" \
            % (n, len(rows), overview[n])
    assert overview[5] == 16, "season 5 is not the sixteen film parts"
    assert len(films) * 4 == overview[5], "films do not cover season 5"

    # overall numbering must run 1..170 unbroken across the Fox run, the film
    # parts (73-88) and both revivals, or a season is silently missing
    numbered = sorted(o for n in EPISODE_SEASONS for o, _, _, _ in episodes[n])
    film_parts = list(range(73, 89))
    assert sorted(numbered + film_parts) == list(range(1, 181)), \
        "overall episode numbering is not contiguous"

    sections = []

    def episode_section(n):
        rows = episodes[n]
        aired = [r for r in rows if r[3] <= AIRED_THROUGH]
        assert aired, "season %d has nothing aired" % n
        # only the tail of a season may be unaired; a hole would mean the
        # production order and the airdates have drifted apart
        assert aired == rows[:len(aired)], "season %d has an unaired gap" % n
        items = [{"id": "fut-s%de%d" % (n, s), "t": t, "n": str(s)}
                 for _, s, t, _ in aired]
        bits = [year_span([d[0] for _, _, _, d in aired])]
        if len(aired) == len(rows):
            bits.append("%d episodes" % len(rows))
        else:
            bits.append("%d of %d episodes aired" % (len(aired), len(rows)))
        bits.append(ERA_OF[n])
        sec = {"id": "s%d" % n, "title": "Season %d" % n,
               "sub": prop.join_bits(*bits), "items": items}
        if n in ERA:
            sec["intro"] = ERA[n][1]
        return sec

    for n in (1, 2, 3, 4):
        sections.append(episode_section(n))

    sections.append({
        "id": "films", "title": "The Films",
        "sub": prop.join_bits(year_span([f["year"] for f in films]),
                              "four direct-to-video features",
                              "Comedy Central's season 5"),
        "intro": "Written and released as four feature-length films, then "
                 "re-cut into the sixteen episodes Comedy Central aired as "
                 "season 5. They are counted here once, as films.",
        "items": [{
            # CLU-430. The apostrophe is dropped BEFORE prop.slug rather than
            # by it — prop.slug would dash it — so `Bender's Big Score` gives
            # fut-film-benders-big-score. Both spellings have to be dropped or
            # the two forms of one title reach two ids, and an id is the
            # `item_id` every tick is stored against: `Bender’s Big Score`
            # folded to fut-film-bender-s-big-score and unticked the film.
            # idsafe.py cannot see this fold, because it is written at the call
            # site and not inside a function, which is why this list reads
            # UNPROVEN there rather than SAFE.
            "id": "fut-film-%s" % prop.slug(
                f["t"].replace("'", "").replace("’", "")),
            "t": f["t"],
            "n": str(f["year"]),
            "note": prop.join_bits(
                "%d direct-to-video feature" % f["year"],
                "%d minutes" % f["mins"],
                "broadcast as season 5 episodes %d–%d"
                % (f["parts"][0], f["parts"][-1])),
        } for f in films],
    })

    for n in (6, 7, 8, 9, 10, 11):
        sections.append(episode_section(n))

    sections[0]["open"] = True

    assert [s["id"] for s in sections] == [
        "s1", "s2", "s3", "s4", "films", "s6", "s7", "s8", "s9", "s10", "s11"]
    total = sum(len(s["items"]) for s in sections)
    assert total == 163, total
    assert sum(1 for s in sections for x in s["items"] if "w" in x) == 0, \
        "a weight crept in — this list is unweighted end to end"

    aired_11 = len(sections[-1]["items"])
    assert 0 < aired_11 < overview[11], "season 11 is no longer part-aired"

    p = {
        "slug": SLUG,
        "title": "Futurama",
        "subtitle": "every episode, and the four films once each",
        "kind": "tv & films",
        "popularity": 80,
        "year": "1999–",
        "blurb": "163 rows across four eras — the Fox run, the four "
                 "direct-to-video films, the Comedy Central revival and the "
                 "Hulu revival, in the order they were made.",
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#472F8C",
        "accentDark": "#5FEFB8",
        "tiers": False,
        "notes": [
            ["The four films count once each.", "Comedy Central re-cut the "
             "2007–09 films into sixteen half-hour episodes and aired them as "
             "season 5. It is the same footage either way, so listing both "
             "would count the same watch twice. The films are the form the "
             "work was written and released in, and the source article gives "
             "the sixteen parts no titles of their own — so this list carries "
             "four film rows, each naming its runtime and the season 5 "
             "episodes it was broadcast as. That is 163 rows; the sixteen-part "
             "reading would be 175."],
            ["Production order, not the order Fox aired it.", "Fox broadcast "
             "the first 72 episodes out of the order they were made, so no "
             "box set, streaming season or episode list matches a strict "
             "airdate sort. This follows the production seasons, like the "
             "source article does, with the four eras in the order they "
             "reached an audience."],
            ["Nothing is weighted.", "Wikipedia documents one running time "
             "for the series and none per episode, so there is no verifiable "
             "per-row number to weight with; every row counts one. The four "
             "film rows are feature length and their notes say so rather than "
             "carrying a weight the rest of the list could not match."],
            ["Season 11 is still going out.", "Five of its ten episodes had "
             "aired when this was built, on August 24, 2026. The rest join "
             "the list as they air, and so will the specials ordered for a "
             "twelfth season."],
            "Titles and airdates machine-read from Wikipedia's List of "
            "Futurama episodes, the season articles and the four film "
            "articles; every season's count is asserted against the list "
            "article's own series overview, and the overall episode numbering "
            "asserted contiguous, before this builds.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d entries in %d sections"
          % (out.name, total, len(sections)))
    for s in sections:
        print("   %-12s %3d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
