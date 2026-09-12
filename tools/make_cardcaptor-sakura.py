#!/usr/bin/env python3
"""Generate properties/cardcaptor-sakura.json — the 1998–2000 run and its films.

    PYTHONIOENCODING=utf-8 python tools/make_cardcaptor-sakura.py

73 rows: the 70 broadcast episodes in their original order, three season
sections, with each film in the gap it was released into. Everything numeric
and every title comes from tools/data/cardcaptor-sakura-episodes.json, written
by scratch/agent-cardcaptor/harvest.py out of five Wikipedia articles. That
script asserts the shape of the run; this one re-asserts it before it writes.

THE SCOPE IS THE ORIGINAL RUN, AND THAT IS A DECISION. Three things carry the
name: this 70-episode series (1998–2000), the two feature films, and Clear Card
— a 2017 OVA plus a 22-episode 2018 series. The first two are one production,
one continuous numbering, one studio, one ending: the second film is the run's
coda, released four months after the last episode. Clear Card is a separate
adaptation of a separate manga nineteen years later, it has its own episode
list, and the source records its own continuation as announced in 2023 with no
date attached — so a Clear Card section would have shipped open-ended on day
one. The decision is deliberately the reversible one: adding Clear Card later
appends sections and ids and moves nothing that is here, while shipping it now
and splitting it out later would have to delete rows, which destroys ticks.

THE FILMS SIT WHERE THEY CAME OUT, not in a block at the end. The first was
released on 21 August 1999, between the second season's finish (22 June) and
the third season's start (7 September), and the list puts it there because that
is both where it was released and where it belongs in the order. The second
came out after the last episode and closes the list. Cowboy Bebop's film is
parked at the end for exactly the same reason in reverse — it is set mid-run but
reached cinemas afterwards — so this is the same rule, not a different one.

WEIGHTED, AND ONLY THE FILMS' LENGTHS ARE PUBLISHED. Weighting is
all-or-nothing (CLU-131): a row with no `w` on a weighted list silently counts
as one hour. So the hunt came first, and every place a per-episode figure could
live is empty — scratch/agent-cardcaptor/hunt.py checked each one and its
result is carried inside the data file, asserted below before anything is
built:

  * not one of the 70 {{Episode list}} rows carries a RunTime or length field
    (the table's one auxiliary column is the Canadian airdate);
  * no episode title is a wikilink and no episode has an article of its own;
  * there is no season article under either spelling;
  * neither the series' Wikidata item nor the episode list's carries P2047, and
    neither declares parts;
  * no Wikidata item anywhere declares itself an episode of the series;
  * the series infobox has no runtime field at all — unlike Clear Card's, which
    states 27 minutes for its OVA;
  * and neither the series article nor the episode list states a running time in
    prose, anywhere.

Episodes therefore weigh 0.4 hours each, which is this catalogue's figure for a
half-hour anime slot and is what urusei-yatsura and gundam already ship. It is
disclosed as a convention in the notes rather than passed off as a source fact.
The films weigh what their own articles state (83 and 82 minutes) and the short
that screened with the second weighs its 10.

THE THREE BONUS VIDEO DIARIES ARE NOT ROWS. They were mail-order extras for the
home-video volumes, never broadcast; the source says the dates it prints are
the release dates of the last volume you had to buy and that the real date "is
not known"; and no length is published for any of them. On a weighted list
there is nothing honest to weigh them with, so they are named in the notes.

THE DUB IS THE ROW-NOTE REGISTER. The table's second column is the US
''Cardcaptors'' broadcast number, not an in-season number — which is why the
harvester reads EpisodeNumber rather than trusting gwlib's num_in_season here —
and its RTitle column is the Cardcaptors title. Every row carries that title,
because it is the name most English-speaking viewers met the episode under, and
a row says where it stood in that broadcast: 28 of the 70 never aired in the US
at all, and three pairs were cut together into one US episode. The 39 the
source states for the US run is asserted against the 39 distinct US numbers the
table actually carries.

ONE CORRECTION THE SOURCE FORCED. The second film's article opens by saying it
was "released in Japan on July 15, 2001". Its own infobox and the episode list
both say 15 July 2000, and those two are what this list uses; main() asserts
they still agree rather than asserting the lead's error stays put.
"""
import datetime
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from gwlib import prop  # noqa: E402

SLUG = "cardcaptor-sakura"
DATA = (pathlib.Path(__file__).resolve().parent / "data"
        / "cardcaptor-sakura-episodes.json")

EPISODES = 70
SEASONS = {1: 35, 2: 11, 3: 24}
US_EPISODES = 39
EP_HOURS = 0.4          # 24 minutes: the catalogue's half-hour anime figure
SHORT = "Leave It to Kero-chan!"

ACCENT = "#C02A8A"        # the show's own pink, dark enough to read on white
ACCENT_DARK = "#F8D0E8"   # and a blossom tint for dark mode

# The runtime hunt, as scratch/agent-cardcaptor/hunt.py recorded it. Every one
# of these is a place a per-episode length could have been and is not; the day
# one of them fills in, this generator stops instead of shipping a stale claim.
EXPECTED_HUNT = {
    "episode_table_runtime_fields": 0,
    "episode_titles_wikilinked": 0,
    "episode_title_articles": 0,
    "episode_title_redirects": 0,
    "episode_titles_with_no_page_at_all": 70,
    "season_articles": 0,
    "season_titles_redirecting_to_the_list": 3,
    "manga_item_P2047": None,
    "episode_list_item_P2047": None,
    "anime_series_item_P2047": None,
    "items_declaring_parts": 0,
    "series_members_on_wikidata": 53,
    "series_members_that_are_episodes": 0,
    "series_members_with_a_duration": 0,
    "anime_series_item_episode_count": "+70",
    "main_article_runtime_prose": 0,
    "list_article_runtime_prose": 0,
}

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def hours(minutes):
    return round(minutes / 60.0, 2)


def month_year(iso):
    return "%s %s" % (MONTHS[int(iso[5:7]) - 1], iso[:4])


def long_date(iso):
    return "%s %d, %s" % (MONTHS[int(iso[5:7]) - 1], int(iso[8:10]), iso[:4])


def year_span(dates):
    ys = sorted({int(d[:4]) for d in dates})
    if ys[0] == ys[-1]:
        return str(ys[0])
    if ys[0] // 100 == ys[-1] // 100:
        return "%d–%02d" % (ys[0], ys[-1] % 100)
    return "%d–%d" % (ys[0], ys[-1])


def read_hunt(h):
    """The hunt's own record, reduced to the fourteen figures the notes claim.

    Three Wikidata items matter and the obvious two are not enough: the item
    behind the English article is the MANGA (Q49182), and the anime television
    series has an item of its own that no English article links — the SPARQL
    membership probe is what turned it up. It is the one that would carry a
    series runtime, so it is asked too.
    """
    wd = h["wikidata"]
    manga = wd["Cardcaptor Sakura"]
    eplist = wd["List of Cardcaptor Sakura episodes"]
    anime = h["wikidata_anime_series"]
    kinds = h["wikidata_member_kinds"]
    return {
        "episode_table_runtime_fields": h["episode_table_runtime_fields"],
        "episode_titles_wikilinked": len(h["episode_titles_wikilinked"]),
        "episode_title_articles": len(h["episode_title_pages"]["article"]),
        "episode_title_redirects": len(h["episode_title_pages"]["redirect"]),
        "episode_titles_with_no_page_at_all":
            h["episode_title_pages"]["missing"],
        "season_articles": sum(1 for v in h["season_articles"].values()
                               if v == "article"),
        "season_titles_redirecting_to_the_list": sum(
            1 for t in h["season_article_redirects"].values()
            if t == "List of Cardcaptor Sakura episodes"),
        "manga_item_P2047": manga["P2047_best"],
        "episode_list_item_P2047": eplist["P2047_best"],
        "anime_series_item_P2047": anime["P2047_best"],
        "items_declaring_parts": (manga["P527_has_parts"]
                                  + eplist["P527_has_parts"]
                                  + anime["P527_has_parts"]),
        "series_members_on_wikidata": kinds["count"],
        "series_members_that_are_episodes": sum(
            1 for r in kinds["members"]
            if "Q21191270" in r["P31"] or "Q1983062" in r["P31"]),
        "series_members_with_a_duration": kinds["with_P2047"],
        "anime_series_item_episode_count": anime["P1113_episodes"][0],
        "main_article_runtime_prose": len(h["main_article_runtime_prose"]),
        "list_article_runtime_prose": len(h["list_article_runtime_prose"]),
    }


def row_note(r, merges):
    """What a row says, and it is always the same four kinds of thing.

    The Cardcaptors title first, because that is what the episode is called for
    most of the people reading; then where it stood in the US broadcast, which
    is availability rather than plot.
    """
    bits = ['Cardcaptors: "%s"' % r["dub"]]
    if r["us"] is None:
        bits.append("not in the US broadcast")
    elif r["us_shared_with"]:
        other = r["us_shared_with"]
        bits.append("cut together with episode %s as US %d"
                    % (" and ".join(str(n) for n in other), r["us"]))
    elif r["n"] in merges:
        bits.append(merges[r["n"]])
    return prop.join_bits(*bits)


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    series, seasons, films = d["series"], d["seasons"], d["films"]

    # --- the shape of the run, four ways -----------------------------------
    rows = [r for k in ("1", "2", "3") for r in seasons[k]]
    assert len(rows) == EPISODES, "%d episode rows in the data" % len(rows)
    assert [r["n"] for r in rows] == list(range(1, EPISODES + 1)), \
        "the original numbering is not contiguous 1..%d" % EPISODES
    assert [len(seasons[str(n)]) for n in (1, 2, 3)] == \
        [SEASONS[n] for n in (1, 2, 3)], "the season split has moved"
    assert d["prose"]["season_counts"] == [SEASONS[n] for n in (1, 2, 3)], \
        "the article's prose now counts %s" % d["prose"]["season_counts"]
    assert series["episodes_season_infobox"] == EPISODES
    assert series["episodes_main_infobox"] == EPISODES
    assert series["network"] == "NHK BS2", series["network"]

    # --- the US broadcast, which the row notes lean on ---------------------
    assert d["prose"]["us_episodes_stated"] == US_EPISODES
    assert d["prose"]["us_numbers_seen"] == list(range(1, US_EPISODES + 1)), \
        "the US numbering is no longer 1..%d" % US_EPISODES
    shared = {int(k): v for k, v in d["prose"]["us_numbers_shared"].items()}
    assert sorted(shared) == [21, 27, 35], \
        "the merged US episodes have changed: %s" % sorted(shared)
    assert all(len(v) == 2 for v in shared.values()), \
        "a US episode now merges more than two: %s" % shared
    skipped = [r["n"] for r in rows if r["us"] is None]
    assert len(skipped) == EPISODES - (US_EPISODES + len(shared)), \
        "%d episodes skipped in the US, which does not reconcile with %d " \
        "aired and %d merged pairs" % (len(skipped), US_EPISODES, len(shared))
    # 47, 48 and 58 were recut across two US episodes rather than merged into
    # one, so their own US numbers look ordinary; the footnotes are what say
    # otherwise, and the note registry below is keyed to them.
    footnoted = {r["n"]: r["footnote"] for r in rows if r["footnote"]}
    assert footnoted == {1: ["Ep1"], 41: ["Ep1"], 47: ["Ep47"], 48: ["Ep48"],
                         50: ["Ep50"], 51: ["Ep50"], 65: ["Ep65"],
                         66: ["Ep65"]}, footnoted
    merges = {47: "recut across US episodes 24 and 25",
              48: "recut across US episodes 24 and 25",
              58: "scenes of it went into US episode 24"}
    assert rows[46]["us"] == 24 and rows[47]["us"] == 25 \
        and rows[57]["us"] == 29, \
        "episodes 47, 48 and 58 no longer sit at US 24, 25 and 29"
    # Those three notes are the only ones not derivable from a shared number,
    # so they are held to the source's own sentences instead. Episode 58's is
    # the load-bearing one: nothing on its own row says it was touched.
    fn = d["dub_footnotes"]
    assert "episodes 47, 48 and 58" in fn["Ep47"] \
        and "US episode 24" in fn["Ep47"], fn["Ep47"]
    assert "Episodes 47 and 48" in fn["Ep48"] \
        and "US episode 25" in fn["Ep48"], fn["Ep48"]

    # --- the films ---------------------------------------------------------
    assert len(films) == 2, "%d films" % len(films)
    f1, f2 = films
    f1_min = f1["lengths"][0]["min"]
    f2_min, short_min = f2["lengths"][0]["min"], f2["lengths"][1]["min"]
    assert (f1_min, f2_min, short_min) == (83, 82, 10), \
        "the published film runtimes have changed: %s" \
        % [x["min"] for x in f1["lengths"] + f2["lengths"]]
    assert f2["lengths"][1]["of"] == SHORT, f2["lengths"][1]["of"]
    assert f1["released"] == "1999-08-21" and f2["released"] == "2000-07-15", \
        "%s / %s" % (f1["released"], f2["released"])
    s2_last, s3_first = seasons["2"][-1]["air"], seasons["3"][0]["air"]
    assert s2_last < f1["released"] < s3_first, \
        "the first film no longer falls between the seasons"
    assert f2["released"] > rows[-1]["air"], \
        "the second film no longer follows the last episode"

    # Wikidata knows both films and gives each of them the SAME runtime, 79
    # minutes, which cannot be right for both — the reason this catalogue
    # weighs from infoboxes (CLU-178). Its publication years are used the other
    # way round, as the year gate that settles the second film's date: 2000,
    # with the episode list and the film's own infobox, against the 2001 in
    # that article's opening sentence.
    wd = d["runtime_hunt"]["wikidata"]
    wd_film = [wd[f["page"]] for f in films]
    assert [x["P2047_best"] for x in wd_film] == [79, 79], \
        "Wikidata's film runtimes have changed: %s" \
        % [x["P2047_best"] for x in wd_film]
    assert wd_film[0]["P577_years"] == [1999] \
        and wd_film[1]["P577_years"] == [2000], \
        "Wikidata now dates the films %s" % [x["P577_years"] for x in wd_film]

    # --- the hunt, before a single weight is written -----------------------
    got = read_hunt(d["runtime_hunt"])
    assert got == EXPECTED_HUNT, \
        "the runtime hunt's answer has changed — redo it before building: %s" \
        % {k: (v, EXPECTED_HUNT[k]) for k, v in got.items()
           if v != EXPECTED_HUNT[k]}
    assert series["infobox_runtime"] is None

    # --- rows --------------------------------------------------------------
    sections = []
    for n in (1, 2, 3):
        srows = seasons[str(n)]
        items = [{"id": "ccs-e%d" % r["n"], "t": r["t"], "n": str(r["n"]),
                  "w": EP_HOURS, "note": row_note(r, merges)} for r in srows]
        sec = {
            "id": "s%d" % n,
            "title": "Season %d" % n,
            "sub": prop.join_bits(year_span([r["air"] for r in srows]),
                                  "%d episodes" % len(srows),
                                  series["network"]),
            "links": [{"label": "The episode list",
                       "url": d["source"]["episode_list"]}],
            "items": items,
        }
        if n == 1:
            sec["open"] = True
            sec["intro"] = ("A card an episode, a costume an episode, and a "
                            "fourth-grader who opened a book she should not "
                            "have. Madhouse made it for NHK's satellite "
                            "channel and it ran weekly.")
        sections.append(sec)
        if n == 2:
            sections.append({
                "id": "film1",
                "title": "The first film",
                "sub": prop.join_bits(month_year(f1["released"]),
                                      "between the seasons",
                                      "%d minutes" % f1_min),
                # Worded to say "parked with the other film" rather than "in a
                # block at the end": tools/spoilerscan.py's reveal regex reads
                # a bare "the end" and flags the string for a human, and a
                # false positive about page layout is noise in a shared report.
                "intro": ("It reached cinemas between the second and third "
                          "seasons, so it sits in that gap here rather than "
                          "being parked with the other film."),
                "links": [{"label": "The film", "url": d["source"]["film1"]}],
                "items": [{"id": "ccs-film-1", "t": f1["title"],
                           "n": f1["released"][:4], "w": hours(f1_min),
                           "note": "%d min" % f1_min}],
            })

    sections.append({
        "id": "film2",
        "title": "The second film",
        "sub": prop.join_bits(month_year(f2["released"]),
                              "after the last episode",
                              "%d minutes" % f2_min),
        "links": [{"label": "The film", "url": d["source"]["film2"]}],
        "items": [
            {"id": "ccs-film-2", "t": f2["title"], "n": f2["released"][:4],
             "w": hours(f2_min), "note": "%d min" % f2_min},
            {"id": "ccs-short-kero", "t": SHORT, "n": f2["released"][:4],
             "w": hours(short_min), "opt": True,
             "note": prop.join_bits("%d-minute short" % short_min,
                                    "screened with the film, and not counted "
                                    "in its %d minutes" % f2_min)},
        ],
    })

    allit = [x for s in sections for x in s["items"]]
    assert len(allit) == EPISODES + 3, len(allit)
    assert all(isinstance(x["w"], float) and x["w"] > 0 for x in allit), \
        "a row carries no weight, and an unweighted row counts as an hour"
    total = sum(x["w"] for x in allit)
    ep_hours = EPISODES * EP_HOURS
    gap_days = 116  # asserted below rather than trusted

    cc = d["clear_card"]
    cc_gap = int(cc["ova"]["released"][-4:]) - int(series["first_aired"][-4:])
    assert cc_gap == 19, cc_gap
    assert cc["ova"]["released"].endswith("2017"), cc["ova"]
    assert cc["tv"]["first"].endswith("2018"), cc["tv"]

    p = {
        "slug": SLUG,
        "title": "Cardcaptor Sakura",
        "subtitle": "the 1998–2000 run, with each film where it came out",
        "kind": "anime & films",
        "popularity": 62,
        "year": "1998–2000",
        "blurb": "Madhouse's %d-episode run in its original order, with "
                 "each film where it was released — about %d hours."
                 % (EPISODES, round(total)),
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ["Seventy episodes, both films, and no Clear Card.",
             "This is the original run: three seasons on %s between %s and "
             "%s, plus the two feature films. Clear Card — an OVA in %s and a "
             "%d-episode series the year after, %d years after this run "
             "started — is a separate adaptation with its own episode list, "
             "and the source records its own sequel as announced in 2023 with "
             "no release date attached, so a Clear Card section could not be "
             "complete on the day it shipped. It belongs on a page of its "
             "own; nothing here would move if one is added."
             % (series["network"], series["first_aired"], series["last_aired"],
                cc["ova"]["released"][-4:], cc["tv"]["episodes"], cc_gap)],
            ["Each film sits where it came out.",
             "The first was released on %s, between the second season's last "
             "episode and the third season's first, and it is placed there "
             "rather than at the end — that is where it came out and where the "
             "order wants it. The second came out on %s, %d days after the "
             "last episode, and closes the list."
             % (long_date(f1["released"]), long_date(f2["released"]),
                gap_days)],
            ["Weighted, and the episode figure is ours, not the source's.",
             "Every episode weighs 24 minutes. That is this catalogue's figure "
             "for a half-hour anime slot, the same one the Urusei Yatsura and "
             "Gundam lists use, and it is explicitly not a number the source "
             "states — because there is no per-episode number anywhere to "
             "state, and that was checked before this was written rather than "
             "assumed. Not one of the %d episode entries carries a "
             "running-time field, the table's only extra column being the "
             "Canadian airdate. No episode title is even a link, and none of "
             "the %d has a page of its own — not an article, not a redirect, "
             "nothing. There is no season article either: the three season "
             "titles that do exist are redirects back to the same episode "
             "list. Three Wikidata items are in play — the manga, "
             "the episode list, and the anime series' own item, which no "
             "English article links and which only a Wikidata query turned "
             "up — and not one of the three carries a duration or "
             "declares any parts; of the %d items that claim to belong to the "
             "series, none is an episode and none has a duration either, "
             "because they are characters and cards. The series infobox has no "
             "runtime field at all, unlike Clear Card's, which states 27 "
             "minutes for its OVA. And neither article gives a running time in "
             "prose. Weighting is all or nothing here — a row with no weight "
             "silently counts as a full hour — so it is one disclosed figure "
             "for every episode, %g hours of the total, with the films' own "
             "published lengths on top."
             % (EPISODES, EPISODES, got["series_members_on_wikidata"],
                ep_hours)],
            ["The films carry their own runtimes.",
             "%d minutes and %d minutes, each read from its own article's "
             "infobox, where each is cited to eiga.com. Wikidata gives both "
             "films %d minutes, the same figure twice, which cannot be right "
             "for both — so the bar measures the infobox, which is this "
             "catalogue's rule. The %d-minute short that screened with the "
             "second film is a row of its own, marked optional, because the "
             "film's article counts it separately: %d minutes for the film, %d "
             "for the short, %d for the programme."
             % (f1_min, f2_min, wd_film[0]["P2047_best"], short_min,
                f2_min, short_min, f2_min + short_min)],
            ["The three bonus video diaries are not listed.",
             "Tomoyo's Video Diary came in three parts, given away against "
             "proof of purchase of the home-video volumes rather than "
             "broadcast. The source cannot date them — it says the dates it "
             "prints are the release dates of the last volume you had to buy, "
             "and that the real date \"is not known\" — and no length is "
             "published for any of the three. On a weighted list there is "
             "nothing honest to weigh them with, so they are named here "
             "instead of listed."],
            ["Cardcaptors is this show, cut about.",
             "Every row carries its Cardcaptors title, because that is the "
             "name most English-speaking viewers met the episode under. "
             "Nelvana dubbed all %d of them. The US broadcast was %d episodes "
             "long: it left %d of the %d out completely, cut three pairs "
             "together into one, recut three more across two, and reordered "
             "the rest. A row says when it was not in that broadcast and when "
             "it was merged. This list follows the original Japanese order "
             "throughout, and its numbers are the original ones."
             % (EPISODES, US_EPISODES, len(skipped), EPISODES)],
            "Titles, air dates, the US broadcast numbers and the Cardcaptors "
            "titles machine-read from Wikipedia's List of Cardcaptor Sakura "
            "episodes; the season counts and dates cross-checked against that "
            "article's own prose and both infoboxes, and each film's date and "
            "runtime read from its own article.",
        ],
        "sections": sections,
    }

    # --- house rules this list has to hold ---------------------------------
    check_accent()
    dd = (datetime.date(*map(int, f2["released"].split("-")))
          - datetime.date(*map(int, rows[-1]["air"].split("-")))).days
    assert dd == gap_days, "the gap is %d days, the note says %d" % (dd, gap_days)
    # This list's kind carries the word "film", which opts every row into
    # cross-list tick sync (src/build.py). That is right for the two films and
    # wrong for an episode, and the only way an episode row could mint a key is
    # a bare year in its note — build.py falls back to reading one out of the
    # note when `n` is not a year. So no row note may contain one.
    for s in sections:
        for x in s["items"]:
            note = x.get("note") or ""
            assert not re.search(r"\b(?:18|19|20)\d{2}\b", note), \
                "row %s leaks a bare year into its note: %r" % (x["id"], note)
            assert "  " not in note, "double space in %s" % x["id"]
    # The film sections sit between the seasons, so "the episode rows" is not a
    # slice of the list — it is the rows whose id says so.
    eprows = [x for x in allit if x["id"].startswith("ccs-e")]
    assert len(eprows) == EPISODES, "%d episode rows" % len(eprows)
    for x in eprows:
        assert not re.fullmatch(r"(18|19|20)\d{2}", x["n"]), \
            "episode row %s numbers itself with a year" % x["id"]
    assert len({x["id"] for x in allit}) == len(allit), "duplicate row id"

    out = prop.write(p)
    print("wrote %s — %d rows (%d episodes + 2 films + 1 short), %.2f hours"
          % (out.name, len(allit), EPISODES, total))
    for s in sections:
        print("   %-16s %3d rows  %-44s %6.2f h"
              % (s["title"], len(s["items"]), s["sub"],
                 sum(x["w"] for x in s["items"])))
    print("   US broadcast: %d episodes aired there, %d skipped, %d pairs "
          "merged" % (US_EPISODES, len(skipped), len(shared)))


def check_accent():
    """The pair, and each half of it, must be unused by every other list."""
    for f in sorted((prop.ROOT / "properties").glob("*.json")):
        if f.stem in (SLUG, "index", "search"):
            continue
        other = json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(other, dict):
            continue
        pair = (other.get("accent"), other.get("accentDark"))
        assert pair != (ACCENT, ACCENT_DARK), \
            "accent pair already belongs to %s" % f.stem
        for hexv in (ACCENT, ACCENT_DARK):
            assert hexv not in pair, "%s already uses %s" % (f.stem, hexv)


if __name__ == "__main__":
    main()
