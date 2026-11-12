#!/usr/bin/env python3
"""Generate properties/yuyu-hakusho.json — all 112 episodes, both films, the
2018 OVA.

    python3 tools/make_yuyu-hakusho.py

Broadcast order, one row per episode, with each film at the point it went
out. THAT IS THE WHOLE DECISION HERE, and the answer is not where the
instinct puts it. Both films opened *inside* the television run, not around
it: the 1993 short went out on July 10, 1993, four and a half months into the
Dark Tournament Saga, and Poltergeist Report opened on April 9, 1994, seven
weeks into the Chapter Black Saga. Appending them after the finale — the
default a list comprehension gives you — would move them past 74 and 37
episodes respectively.

Nothing is placed by hand. Each film is filed by comparing its release date
against every season's first and last airdate, exactly as make_babylon-5.py
does, and both land inside a season rather than between two.

The tie-break is worth naming, because both films hit it. Yu Yu Hakusho aired
weekly on Saturdays and both films opened ON a broadcast Saturday — July 10,
1993 is also the airdate of episode 38, and April 9, 1994 is also the airdate
of episode 75. The source records no order within a day, so a film is placed
before the first episode that aired strictly LATER than it, which puts it
after the episode it shared a day with. main() asserts that both films
actually collide with an episode's airdate, so if a date is ever corrected
the tie-break stops being invisible.

THE ARC NAMES ARE THE SOURCE'S AND SO ARE THEIR BOUNDARIES. The list article
divides the run into four sections and names each one — Spirit Detective,
Dark Tournament, Chapter Black, Three Kings — and this list carries those
names and those boundaries unchanged. The same article is candid about what
they are: the divisions follow Funimation's North American box sets, which
"only correspond to story arcs, and not to the pattern in which the show
actually aired", because in Japan the series ran year-round with no seasons
at all. That is a caveat to print, not a reason to invent a different
division, so the page says it.

NUMBERING RUNS 1 TO 112 STRAIGHT THROUGH. The source's episode tables carry
one number per episode and it is the overall one — there is no in-season
numbering to fall back on — so season 4 opens at 95 rather than at 1.

WEIGHTS: NONE, and the hunt behind that is unusually complete because the
films make it tempting. Both films publish a runtime (30 and 95 minutes,
agreed by their infoboxes and by Wikidata P2047) and the OVA infoboxes
publish one too. The 112 episodes publish nothing, anywhere:

  * no episode has an article of its own — not one of the 112 Title fields
    is a wikilink;
  * therefore no episode has a Wikidata item to carry P2047, and asking
    Wikidata directly for everything filed as part of the series (P179, P361
    and P4908 against Q286950) returns only the four season items, none of
    which carries a runtime;
  * none of the four season articles has a runtime field, and the word does
    not appear on any of them;
  * the series article's {{Infobox television}} has no runtime field of its
    own — the two `runtime =` lines on that page belong to the two OVA
    infoboxes nested inside `related`, which is exactly the trap a naive
    field read falls into and is asserted against here;
  * and no {{Episode list}} block carries a RunTime.

A weighted list resolves a row with no weight to one hour, so weighting the
two films alone would push a guessed hour into all 112 episodes — a 112-hour
lie standing next to two honest ones. It is all rows or none. It is none, the
runtimes ride in the film and OVA row notes as text, and main() asserts not
one row carries `w`.

EIZOU HAKUSHO IS NOT HERE. See the notes on the page.

Titles, numbering, airdates, arc names, film dates and runtimes, the OVA
facts and the runtime census are machine-read from Wikipedia by
scratch/agent-yuyu/build_data.py; the committed result is
tools/data/yuyu-hakusho.json.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop  # noqa: E402

SLUG = "yuyu-hakusho"
DATA = pathlib.Path(__file__).resolve().parent / "data" / "yuyu-hakusho.json"

TOTAL_EPISODES = 112
ROWS = 116               # 112 episodes + 2 films + 2 OVA episodes

ACCENT = "#1C5B4A"       # the green of Yusuke's school uniform
ACCENT_DARK = "#6FE3C4"  # ...against the aqua of a spirit gun

MONTHS = ["", "January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

# Per film: what kind of thing it is. Dates, runtimes, alternate titles and
# the festival clause are never typed here — they come from the data file.
FILMS = {"1993": "Theatrical film", "1994": "Theatrical film"}
FESTIVAL = "Shown at a seasonal Toei Anime Fair"

# What each 2018 OVA episode adapts, in the franchise article's own words.
OVA_IS = {
    "Two Shot": "Adapts a bonus chapter from the manga's seventh volume",
    "All or Nothing": "Adapts the manga's penultimate chapter",
}

INTRO = {
    1: "Where it starts. Twenty-five episodes adapting the manga's first six "
       "volumes.",
}


def datestr(d):
    return "%s %d, %d" % (MONTHS[d[1]], d[2], d[0])


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
    seasons, heads, films = d["seasons"], d["headings"], d["films"]
    nums = ["1", "2", "3", "4"]
    check_accent()

    # ---- where each film goes. Dates decide; nothing is placed by hand.
    first = {n: seasons[n][0]["d"] for n in nums}
    last = {n: seasons[n][-1]["d"] for n in nums}
    inside, alone = {}, []
    for f in films:
        home = next((n for n in nums if first[n] < f["d"] < last[n]), None)
        (inside.setdefault(home, []).append(f) if home else alone.append(f))
    assert sorted(inside) == ["2", "3"], \
        "the films land in seasons %s, expected 2 and 3" % sorted(inside)
    assert not alone, \
        "%d film(s) fell outside every season — they would need sections of " \
        "their own" % len(alone)
    assert all(len(v) == 1 for v in inside.values()), \
        "two films landed in one season: %s" % {k: len(v) for k, v in inside.items()}

    # ---- both films opened on a broadcast day, so the tie-break is load-
    # bearing rather than incidental. Say so out loud.
    shared = {}
    for n, fs in inside.items():
        for f in fs:
            same = [e for e in seasons[n] if e["d"] == f["d"]]
            assert len(same) == 1, \
                "%s no longer shares its release date with exactly one " \
                "episode — the same-day tie-break needs re-reading" % f["t"]
            shared[f["key"]] = same[0]

    def film_row(f):
        e = shared[f["key"]]
        note = prop.join_bits(
            FILMS[f["key"]], "%d minutes" % f["runtime"],
            "Opened %s, the day episode %d aired" % (datestr(f["d"]), e["o"]),
            "Also known as %s" % f["alt"] if f["alt"] else "",
            FESTIVAL if f["festival"] else "")
        return {"id": "yyh-film-%s" % f["key"], "t": f["t"], "n": "film",
                "note": note}

    # ---- sections, in broadcast order
    sections = []
    for n in nums:
        items, here = [], sorted(inside.get(n, []), key=lambda f: f["d"])
        for e in seasons[n]:
            while here and here[0]["d"] < e["d"]:
                items.append(film_row(here.pop(0)))
            row = {"id": "yyh-e%d" % e["o"], "t": e["t"], "n": str(e["o"])}
            # no "Series finale" on the last episode: its position already
            # says it (CLU-123, CLU-557)
            items.append(row)
        assert not here, "a film outran its season"
        name, span = heads[n]
        sub = prop.join_bits(span, "%d episodes" % len(seasons[n])
                             + (", with the film where it opened"
                                if inside.get(n) else ""),
                             d["season_meta"][n]["network"])
        sec = {"id": "s%s" % n, "title": "Season %s: %s" % (n, name),
               "sub": sub, "items": items}
        if int(n) in INTRO:
            sec["intro"] = INTRO[int(n)]
        sections.append(sec)

    # ---- the sequel OVA, twenty-three years after the finale
    ova = d["ova_2018"]
    assert ova["episodes"] == len(ova["titles"]) == 2, ova
    sections.append({
        "id": "ova2018",
        "title": "Two Shot & All or Nothing",
        "sub": prop.join_bits(str(ova["released"][0]),
                              "two OVA episodes", ova["runtime"]),
        "intro": "Made for the anime's 25th anniversary and released with a "
                 "Blu-ray box set, twenty-three years after the finale. Two "
                 "short episodes, both adapting manga chapters the television "
                 "run never reached.",
        "items": [{"id": "yyh-ova-%s" % prop.slug(t), "t": t,
                   "n": str(ova["released"][0]),
                   "note": prop.join_bits("OVA", ova["runtime"],
                                          "Released %s" % datestr(ova["released"]),
                                          OVA_IS[t])}
                  for t in ova["titles"]],
    })
    sections[0]["open"] = True

    # ---- counts
    ids = [x["id"] for s in sections for x in s["items"]]
    eps = [i for i in ids if re.fullmatch(r"yyh-e\d+", i)]
    assert len(eps) == TOTAL_EPISODES == d["series"]["num_episodes"], \
        "%d episode rows, the source counts %d" % (len(eps),
                                                   d["series"]["num_episodes"])
    assert len(ids) == ROWS, "%d rows, expected %d" % (len(ids), ROWS)
    assert len(set(ids)) == len(ids), "duplicate ids"
    assert [int(i[5:]) for i in eps] == list(range(1, TOTAL_EPISODES + 1)), \
        "episode ids are not contiguous 1..%d" % TOTAL_EPISODES
    assert sum(1 for s in sections for x in s["items"] if "w" in x) == 0, \
        "a weight crept in — this list is unweighted end to end"

    # ---- the sync trap. This list's kind contains "film", so build.py reads
    # a year out of any row's note when the number column is not a year — an
    # episode note naming a single year would quietly pair that episode with
    # a same-titled film on another list. The film and OVA rows are supposed
    # to publish exactly one year each; the episode rows, none.
    for s in sections:
        for x in s["items"]:
            years = set(re.findall(r"\b((?:18|19|20)\d{2})\b", x.get("note") or ""))
            if re.fullmatch(r"yyh-e\d+", x["id"]):
                assert not years, \
                    "year in an episode note would fake a film sync: %s" % x["id"]
            else:
                assert len(years) == 1, \
                    "%s publishes %d years, so its sync key is ambiguous" \
                    % (x["id"], len(years))

    cens = d["census"]
    assert cens["episodes_with_article"] == 0 and \
        cens["episode_wikidata_items"] == 0 and \
        cens["series_parts_with_runtime"] == 0, \
        "the runtime census changed — revisit weights: %s" % cens

    ez = d["eizou"]
    prop.write({
        "slug": SLUG,
        "title": "Yu Yu Hakusho",
        "subtitle": "every episode, with both films where they opened",
        "kind": "tv & films",
        "popularity": 68,
        "year": "1992–2018",
        "blurb": "All 112 episodes of Togashi's Spirit Detective run in "
                 "broadcast order, with both films at the point they opened "
                 "and the anniversary OVA at the end.",
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ["Both films opened inside the run, so both sit inside it.",
             "Neither film came after the series and neither came between two "
             "arcs. The 1993 short opened on July 10, 1993, four and a half "
             "months into the Dark Tournament Saga; Poltergeist Report opened "
             "on April 9, 1994, seven weeks into the Chapter Black Saga. Each "
             "one is filed by comparing its release date against every "
             "season's first and last airdate, so they sit in those lists "
             "rather than in sections of their own."],
            ["Each film opened on a broadcast Saturday.",
             "The series went out weekly on Saturdays, and both films opened "
             "on a day that also carried an episode — July 10, 1993 is also "
             "episode 38's airdate, and April 9, 1994 is also episode 75's. "
             "Nothing in the source orders a film against an episode within "
             "the same day, so each film is placed after the episode it "
             "shared a day with. Both row notes name that day."],
            ["The four sections are the source's arcs, and the source says "
             "what they are not.",
             "%s are the divisions and the names the episode list uses, and "
             "they are carried here unchanged. That article is also plain "
             "that its seasons \"only correspond to story arcs, and not to "
             "the pattern in which the show actually aired\": in Japan the "
             "series ran year-round with no seasons at all, and the American "
             "broadcast seasons were cut somewhere else again — %s. The arcs "
             "are the division worth watching by. They are not a broadcast "
             "fact, and this page does not pretend otherwise."
             % (", ".join(heads[n][0].replace(" Saga", "") for n in nums[:-1])
                + " and " + heads[nums[-1]][0].replace(" Saga", ""),
                ", ".join("%d–%d" % tuple(r) for r in d["us_broadcast_seasons"]))],
            ["The numbers run 1 to 112 straight through.",
             "The source's tables carry one number per episode and it is the "
             "overall one — there is no in-season numbering to fall back on. "
             "That is why the Three Kings Saga opens at 95 rather than at 1."],
            ["Eizou Hakusho is not here.",
             "Six OVA volumes went out on VHS in Japan between September 21, "
             "1994 and February 7, 1996. The source describes what is on them "
             "— video montages from the anime, image songs, voice actor "
             "interviews and satirical shorts, alongside very short original "
             "clips — and the series article files the set as a compilation "
             "series. Most of it is the episodes already on this list, cut "
             "differently, and the source gives no title and no date for any "
             "individual volume, so no row here could say which one it was. "
             "Named here instead, so its absence is a statement rather than "
             "an oversight."],
            ["The 2023 live-action series is not here either.",
             "Netflix's adaptation is a different production with its own "
             "cast, its own article and its own run. This list is the anime."],
            ["Nothing is weighted, and hours are not tracked on this list.",
             "Both films publish a runtime — 30 and 95 minutes, agreed by "
             "their infoboxes and by Wikidata — and both film rows carry "
             "theirs, as does each OVA row. The 112 episodes publish none, "
             "anywhere: not one episode has an article of its own, so not one "
             "has a Wikidata item to carry a runtime; asking Wikidata "
             "directly for everything filed as part of the series returns "
             "only the four season items and none of them carries one "
             "either; no season article has a runtime field, or the word; the "
             "series infobox has no runtime field of its own; and no episode "
             "table row has a runtime column. A weighted list counts a row "
             "with no weight as a full hour, so weighting the two films alone "
             "would invent an hour 112 times over. An episode, a film and an "
             "OVA each count one."],
            "Titles, numbering, airdates, arc names, film dates and runtimes "
            "and the OVA facts machine-read from Wikipedia's List of Yu Yu "
            "Hakusho episodes, the four season articles, the YuYu Hakusho "
            "(1992 TV series) and Yu Yu Hakusho articles and both film "
            "articles, with the runtime census taken from Wikidata; every "
            "season's count is asserted against its own infobox, the total "
            "against the series infobox, the numbering asserted contiguous "
            "1–112, and each film's placement recomputed from its release "
            "date before this builds.",
        ],
        "sections": sections,
    })

    print("wrote %s.json — %d rows (%d episodes + 2 films + 2 OVA)"
          % (SLUG, len(ids), len(eps)))
    for s in sections:
        print("   %-34s %3d  %s" % (s["title"], len(s["items"]), s["sub"]))
    print("   excluded: %s (%d volumes, %s, %s–%s)"
          % (ez["title"], ez["episodes"], ez["runtime"], ez["first"], ez["last"]))


if __name__ == "__main__":
    main()
