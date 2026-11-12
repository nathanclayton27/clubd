#!/usr/bin/env python3
"""Generate properties/inuyasha.json — all 193 episodes and all four films.

    python3 tools/make_inuyasha.py

Broadcast order, one row per episode, numbered 1 to 193 straight through,
with each film at the point it opened.

THE FINAL ACT IS NOT OPTIONAL, AND THE STRUCTURE SAYS SO. The 2000–04 run
stops with the manga unfinished; the 2009–10 run was made to adapt the rest.
It therefore gets a section of its own with the same standing as a season,
season four's subhead says the story does not end there, and both sections
carry an intro saying it in words. The source is unusually explicit about
its status and says two things at once, so this list quotes both rather than
picking one:

  * its own article calls it "the direct sequel to the Inuyasha anime
    series, and is based on the last 21 volumes of the manga series", and
    the episode list calls it "a sequel anime television series" that
    "adapted the final volumes of the manga" — a separate series;
  * and the same episode list carries it as the fifth block of one
    {{Series overview}}, its episode table numbers its episodes 168 to 193
    of the same run, and its infobox is an {{Infobox television season}}
    whose prev_season is Season 4 — a continuation.

Both are true and neither is optional to a viewer, which is the only thing
the page needs to get across.

THE FILMS ARE THE OTHER DECISION, and the answer is not where instinct puts
it. Three of the four opened INSIDE the television run rather than after it.
All four opened in the week before Christmas, and the series took a four- or
five-week break over each new year, so each of the first three opened in the
gap between the last episode of one December and the first of the following
January: Affections Touching Across Time eleven episodes into season two,
The Castle Beyond the Looking Glass eight into season three, Swords of an
Honorable Ruler nine into season four. Appending them after the finale — the
default a list comprehension gives you — would move the first of them past
138 episodes. Only Fire on the Mystic Island fell outside a season, three
months after the original run ended, and only it gets a section of its own.

Nothing is placed by hand. Each film is filed by comparing its release date
against every run's first and last airdate, exactly as make_babylon-5.py and
make_yuyu-hakusho.py do.

WEIGHTS: NONE, ALL OR NOTHING, and the hunt behind that is long because the
films make it tempting. All four films publish a runtime. No episode does,
and the near-misses are the interesting part:

  * no episode of either run has an article of its own — not one of the 193
    Title fields on the five episode-list articles is a wikilink;
  * no {{Episode list}} block on any of them carries a RunTime;
  * none of the four season articles has a runtime field, and the word does
    not appear on any of them, nor on The Final Act's article, nor on the
    episode list;
  * the Inuyasha (TV series) infobox has no runtime field either — the one
    match for the word on that page is a wikilink to Binary Runtime
    Environment for Wireless, a handset platform, which is exactly the trap
    a naive field read falls into and is asserted against here;
  * Wikidata does publish two figures, and they are the wrong shape. Each
    run's own item carries one blanket number for the whole run — 25 minutes
    for the original, 24 for The Final Act — which is a fact about a
    broadcast slot and not about any episode in it;
  * and Wikidata has episode items for 30 of the 193 episodes, all of them
    in the original run's first 30, with nothing at all for The Final Act.
    Every one of those 30 repeats the same 25 minutes the run's item
    carries. That is the series blanket copied down, not 30 measurements.

A weighted list resolves a row with no weight to one hour, so weighting the
four films alone would push a guessed hour into all 193 episodes. It is all
rows or none. It is none, the runtimes ride in the film row notes as text,
and main() asserts not one row carries `w`.

BLACK TESSAIGA AND YASHAHIME ARE NOT HERE. See the notes on the page.

Titles, numbering, airdates, season arc names, the one-hour specials, film
dates and runtimes, The Final Act's status sentences and the runtime census
are machine-read from Wikipedia and Wikidata by
scratch/agent-inuyasha/build_data.py; the committed result is
tools/data/inuyasha.json.
"""
import json
import pathlib
import re
import sys
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop  # noqa: E402

SLUG = "inuyasha"
DATA = pathlib.Path(__file__).resolve().parent / "data" / "inuyasha.json"

ORIGINAL = 167           # episodes in the 2000–04 run
TOTAL_EPISODES = 193     # ...and with The Final Act
ROWS = TOTAL_EPISODES + 4

ACCENT = "#A62639"       # the red of the fire-rat robe
ACCENT_DARK = "#FF8A93"  # ...lifted for dark mode

MONTHS = ["", "January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

# Per film: what kind of thing it is, and — for the one that falls outside
# every season — the heading and subhead it gets when it stands alone. Dates,
# runtimes and alternate titles are never typed here; they come from the data
# file.
KIND = "Theatrical film"
ALONE = {"island": ("Fire on the Mystic Island",
                    "the fourth film, between the two runs")}

INTRO = {
    "1": "Where it starts.",
    "4": "The last season of the original run, and not the end of the "
         "story. The anime stops here with the manga still going, and did "
         "not come back to it for five years. The Final Act, below, is the "
         "rest of it.",
}


def datestr(d):
    return "%s %d, %d" % (MONTHS[d[1]], d[2], d[0])


def span(a, b):
    return str(a[0]) if a[0] == b[0] else "%d–%02d" % (a[0], b[0] % 100)


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
    d = json.loads(DATA.read_text(encoding="utf-8"))
    seasons, tfa, films, cens = d["seasons"], d["tfa"], d["films"], d["census"]
    st, ex, ov = tfa["status"], d["exclusions"], d["overview"]
    nums = ["1", "2", "3", "4"]
    runs = [(n, seasons[n]) for n in nums] + [("tfa", tfa)]
    by_key = dict(runs)
    check_accent()

    # ---- where each film goes. Dates decide; nothing is placed by hand.
    first = {k: r["first"] for k, r in runs}
    last = {k: r["last"] for k, r in runs}
    inside, alone = {}, []
    for f in films:
        home = next((k for k, _r in runs if first[k] < f["d"] < last[k]), None)
        (inside.setdefault(home, []).append(f) if home else alone.append(f))
    assert sorted(inside) == ["2", "3", "4"], \
        "the films land in %s, expected seasons 2, 3 and 4" % sorted(inside)
    assert all(len(v) == 1 for v in inside.values()), \
        "two films landed in one run: %s" % {k: len(v) for k, v in inside.items()}
    assert [f["key"] for f in alone] == ["island"], \
        "%s fell outside every run" % [f["key"] for f in alone]
    assert last["4"] < alone[0]["d"] < first["tfa"], \
        "the fourth film no longer sits between the two runs"

    # ---- no film shares a broadcast day with an episode, so no tie-break is
    # doing invisible work. Yu Yu Hakusho's did, twice; this one does not, and
    # that is worth asserting rather than assuming.
    for k, fs in inside.items():
        for f in fs:
            same = [e for e in by_key[k]["rows"] if e["d"] == f["d"]]
            assert not same, \
                "%s now shares its release date with episode %d — the " \
                "same-day order needs reading off the source" \
                % (f["t"], same[0]["o"])

    def film_row(f, where):
        note = prop.join_bits(
            KIND, "%d minutes" % f["runtime"], where,
            "Also known as %s" % f["alt"] if f["alt"] else "")
        return {"id": "iy-film-%s" % f["key"], "t": f["t"], "n": "film",
                "note": note}

    def episode_rows(key, run):
        """One run's rows, with any film spliced in where it opened."""
        items, here = [], sorted(inside.get(key, []), key=lambda f: f["d"])
        specials = run["specials"]
        for e in run["rows"]:
            while here and here[0]["d"] < e["d"]:
                f = here.pop(0)
                prev = next(x["_o"] for x in reversed(items) if "_o" in x)
                # each of these three opened in the series' own new-year
                # break, not between two ordinary weekly episodes. That is
                # WHY they are inside a season at all, so it is asserted
                # rather than left as a coincidence nobody rechecks.
                before = next(x["d"] for x in reversed(run["rows"])
                              if x["o"] == prev)
                gap = (date(*e["d"]) - date(*before)).days
                assert gap >= 21, \
                    "%s opened in a %d-day gap, not a broadcast break" \
                    % (f["t"], gap)
                items.append(film_row(f, "Opened %s, between episodes %d and %d"
                                      % (datestr(f["d"]), prev, prev + 1)))
            bits = []
            if e["o"] == 1:
                bits.append("Series premiere")
            if str(e["o"]) in specials:
                bits.append("Aired as a one-hour special with episode %d"
                            % specials[str(e["o"])])
            if e["o"] == ORIGINAL:
                bits.append("Where the original run stops; The Final Act "
                            "carries on from here")
            # no "Series finale" on the last episode: its position already
            # says it (CLU-123, CLU-557)
            row = {"id": "iy-e%d" % e["o"], "t": e["t"], "n": str(e["o"]),
                   "_o": e["o"]}
            if bits:
                row["note"] = prop.join_bits(*bits)
            items.append(row)
        assert not here, "a film outran its run"
        return items

    # ---- sections, in broadcast order
    sections = []
    for n in nums:
        s = seasons[n]
        sub = prop.join_bits(
            span(s["first"], s["last"]),
            "%d episodes" % s["num_episodes"]
            + (", with the film where it opened" if inside.get(n) else ""),
            "not where the story ends" if n == "4" else "")
        sec = {"id": "s%s" % n, "title": "Season %s: %s" % (n, s["arc"]),
               "sub": sub, "items": episode_rows(n, s)}
        if n in INTRO:
            sec["intro"] = INTRO[n]
        sections.append(sec)

    for f in alone:
        title, subbit = ALONE[f["key"]]
        sections.append({
            "id": "film-%s" % f["key"], "title": title,
            "sub": prop.join_bits(str(f["d"][0]), subbit),
            "intro": "An original story by the series writer, like the other "
                     "three. It opened three months after the original run "
                     "ended and is not where the story finishes.",
            "items": [film_row(f, "Opened %s, between the two runs"
                               % datestr(f["d"]))]})

    sections.append({
        "id": "tfa", "title": "The Final Act",
        "sub": prop.join_bits(span(tfa["first"], tfa["last"]),
                              "%d episodes" % tfa["num_episodes"],
                              "the ending"),
        "intro": "Not optional. The original run adapts the manga's first %d "
                 "volumes and stops; this one adapts volumes %d to %d and "
                 "finishes it, five years later, with the original staff and "
                 "cast brought back. The source files it both ways and this "
                 "list keeps both: its own article calls it the direct sequel "
                 "to the Inuyasha anime series, while the same episode list "
                 "carries it as the fifth block of one series overview, "
                 "numbers its episodes %d to %d of the same run, and names "
                 "Season 4 as the season before it."
                 % (st["original_run_volumes"], st["greenlit_volumes"][0],
                    st["greenlit_volumes"][1], ORIGINAL + 1, TOTAL_EPISODES),
        "items": episode_rows("tfa", tfa)})

    sections[0]["open"] = True
    for s in sections:
        for x in s["items"]:
            x.pop("_o", None)

    # ---- counts
    ids = [x["id"] for s in sections for x in s["items"]]
    eps = [i for i in ids if re.fullmatch(r"iy-e\d+", i)]
    assert len(eps) == TOTAL_EPISODES, "%d episode rows" % len(eps)
    assert [int(i[4:]) for i in eps] == list(range(1, TOTAL_EPISODES + 1)), \
        "episode ids are not contiguous 1..%d" % TOTAL_EPISODES
    assert len(ids) == ROWS, "%d rows, expected %d" % (len(ids), ROWS)
    assert len(set(ids)) == len(ids), "duplicate ids"
    assert sum(1 for s in sections for x in s["items"] if "w" in x) == 0, \
        "a weight crept in — this list is unweighted end to end"
    assert d["series"]["num_episodes"] == ORIGINAL and \
        tfa["num_episodes"] == TOTAL_EPISODES - ORIGINAL, "run counts moved"

    # ---- the sync trap. This list's kind contains "film", so build.py reads
    # a year out of any row's note when the number column is not a year — an
    # episode note naming a single year would quietly pair that episode with
    # a same-titled film on another list. The four film rows are supposed to
    # publish exactly one year each; the 193 episode rows, none.
    for s in sections:
        for x in s["items"]:
            years = set(re.findall(r"\b((?:18|19|20)\d{2})\b", x.get("note") or ""))
            if re.fullmatch(r"iy-e\d+", x["id"]):
                assert not years, \
                    "year in an episode note would fake a film sync: %s" % x["id"]
            else:
                assert len(years) == 1, \
                    "%s publishes %d years, so its sync key is ambiguous" \
                    % (x["id"], len(years))

    # ---- the runtime census the weights decision rests on
    assert cens["episodes_with_article"] == 0 and \
        cens["episode_table_runtime_fields"] == 0 and \
        cens["season_articles_with_runtime"] == 0 and \
        cens["episode_wikidata_items"] == 30 and \
        cens["episodes_without_a_wikidata_item"] == 163, \
        "the runtime census changed — revisit weights: %s" \
        % {k: v for k, v in cens.items() if not isinstance(v, dict)}

    # ---- the claim season four's intro and the first note both make: the
    # original run stopped while the manga was still being serialised
    assert ex["manga"]["serialisation_ended_year"] > seasons["4"]["last"][0], \
        "the manga finished in %s, before the run stopped in %s" \
        % (ex["manga"]["serialisation_ended_year"], seasons["4"]["last"][0])

    # ---- the North American DVD division, and one worked example of how far
    # it diverges. Computed, because "a DVD season 5 sits inside season 3" is
    # exactly the kind of sentence that rots when a boundary moves.
    dvd = ov["dvd_seasons"]
    page = {n: (int(seasons[n]["rows"][0]["o"]), int(seasons[n]["rows"][-1]["o"]))
            for n in nums}
    example = next((dn, a, b, n) for dn, a, b in dvd for n in nums
                   if page[n][0] <= a and b <= page[n][1] and dn != int(n))
    assert example, "no DVD season falls inside a single page season any more"
    stopped = "%s %d" % (MONTHS[seasons["4"]["last"][1]], seasons["4"]["last"][0])

    prop.write({
        "slug": SLUG,
        "title": "Inuyasha",
        "subtitle": "every episode, the films where they opened, and the "
                    "ending",
        "kind": "anime & films",
        "popularity": 71,
        "year": "2000–2010",
        "blurb": "All 193 episodes in broadcast order — the 2000 run, all "
                 "four films at the point each one opened, and The Final "
                 "Act, which is where the story actually ends.",
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ["The Final Act is not optional.",
             "The original run adapts the manga's first %d volumes and stops "
             "there in %s, with the manga itself still running. The Final "
             "Act was made five years later, with the original staff and "
             "cast, to adapt volumes %d to %d, and it is the ending. It has "
             "a section of its own here "
             "with the same standing as a season because that is what it is "
             "to a viewer — not a bonus, not a spin-off, and not something "
             "you can leave off the end."
             % (st["original_run_volumes"], stopped, st["greenlit_volumes"][0],
                st["greenlit_volumes"][1])],
            ["What the source calls it, in its own words.",
             "Two things at once, and this list keeps both. Its own article "
             "says it \"is the direct sequel to the Inuyasha anime series, "
             "and is based on the last 21 volumes of the manga series\", and "
             "the episode list calls it \"a sequel anime television series\" "
             "that \"adapted the final volumes of the manga\" — a separate "
             "series. But that same episode list carries it as the fifth "
             "block of one series overview, its episode table numbers its "
             "episodes 168 to 193 of the same run, and its infobox is a "
             "television-season box whose previous season is Season 4 — a "
             "continuation. The numbering here follows the source and runs "
             "1 to 193 straight through, which is why The Final Act opens at "
             "168 rather than at 1."],
            ["Three of the four films opened inside the run.",
             "Not one of them came after the series. All four opened in the "
             "week before Christmas, and the series took a month off over "
             "each new year, so Affections Touching Across Time, The Castle "
             "Beyond the Looking Glass and Swords of an Honorable Ruler each "
             "opened in the gap between a December episode and a January one "
             "and sit inside those seasons rather than in sections of their "
             "own. Each film is filed by comparing its release date against "
             "every run's first and last airdate, and each row note names "
             "the two episodes it fell between. Only Fire on the Mystic "
             "Island fell outside a season — three months after the original "
             "run ended — so only it gets a section. All four are original "
             "stories by the series writer, so none of them is load-bearing; "
             "they are here because they are part of the run, at the point "
             "they were part of it."],
            ["The four seasons are a retroactive sorting, and the source "
             "says so.",
             "The episode list notes that its seasons \"correspond to a "
             "retroactive sorting established by Yomiuri TV as far back as "
             "2019\", recertified by four Blu-ray box sets released in Japan "
             "in 2021 and 2022 that called them phases. The season names "
             "here are the Japanese collected titles those sets use. North "
             "America cut the same 167 episodes seven ways instead — %s — "
             "so a DVD box labelled season %d, episodes %d to %d, sits "
             "wholly inside season %s on this page. The four are the "
             "division the source uses; they are not a broadcast fact, and "
             "this page does not pretend otherwise."
             % (", ".join("%d–%d" % (a, b) for _n, a, b in dvd),
                example[0], example[1], example[2], example[3])],
            ["Four pairs aired as one hour.",
             "Episodes 21 and 22, 133 and 134, 147 and 148, and 166 and 167 "
             "each went out as a single one-hour broadcast. They are eight "
             "rows here, as the source numbers them, and all eight say so."],
            ["Nothing is weighted, and hours are not tracked on this list.",
             "All four films publish a runtime and all four film rows carry "
             "theirs. The 193 episodes publish none. No episode of either "
             "run has an article of its own, so none has a Wikidata item to "
             "reach that way; no episode table row carries a runtime field; "
             "no season article has one, or the word; and the series "
             "infobox has no runtime field either — its only match for the "
             "word is a link to a handset platform. Wikidata does publish "
             "two numbers and both are the wrong shape: one blanket figure "
             "per run, 25 minutes for the original and 24 for The Final Act, "
             "which describes a broadcast slot rather than an episode; and "
             "episode items for 30 of the 193, all in the first 30 and all "
             "repeating that same 25. A weighted list counts a row with no "
             "weight as a full hour, so weighting the four films alone would "
             "invent an hour 193 times over. An episode and a film each "
             "count one."],
            ["Black Tessaiga is not here.",
             "A 30-minute short with the original voice cast, first shown at "
             "an It's a Rumic World exhibition in Tokyo in July 2008 and put "
             "out on disc in October 2010. It is not an episode of either "
             "run — the episode list does not carry it, and the numbering "
             "runs straight from 167 to 168 with no gap for it. Named here "
             "so its absence is a statement rather than an oversight."],
            ["Yashahime is not here either.",
             "The 2020–22 sequel spin-off is an anime-original story with "
             "its own cast and its own article. This list is Inuyasha, and "
             "it ends where Inuyasha ends."],
            "Titles, numbering, airdates, the retroactive season names, the "
            "one-hour specials, film dates and runtimes and The Final Act's "
            "status machine-read from Wikipedia's List of Inuyasha episodes, "
            "the four Inuyasha season articles, Inuyasha, Inuyasha (TV "
            "series), Inuyasha: The Final Act and all four film articles, "
            "with the runtime census taken from Wikidata; every run's count "
            "is asserted against its own infobox and against the episode "
            "list's series overview, the numbering asserted contiguous "
            "1–193, and each film's placement recomputed from its release "
            "date before this builds.",
        ],
        "sections": sections,
    })

    print("wrote %s.json — %d rows (%d episodes + 4 films)"
          % (SLUG, len(ids), len(eps)))
    for s in sections:
        nn = [int(x["n"]) for x in s["items"] if x["n"].isdigit()]
        print("   %-30s %3d  %-52s %s"
              % (s["title"], len(s["items"]), s["sub"],
                 "%d–%d" % (nn[0], nn[-1]) if nn else "film"))
    print("   excluded: %s (%d minutes, %s), Yashahime (%s – %s)"
          % (ex["ova"]["title"], ex["ova"]["minutes"], ex["ova"]["presented"],
             ex["yashahime"]["first"], ex["yashahime"]["last"]))


if __name__ == "__main__":
    main()
