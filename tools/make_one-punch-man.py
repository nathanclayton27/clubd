#!/usr/bin/env python3
"""Generate properties/one-punch-man.json — the whole television run.

    PYTHONIOENCODING=utf-8 python tools/make_one-punch-man.py

Thirty-six broadcast episodes in three seasons, in air order, plus the thirteen
episodes that only ever shipped on home video, which are optional. Every title,
number, airdate, count and absence below is machine-read by
scratch/agent-opm/harvest.py out of five Wikipedia articles — "List of
One-Punch Man episodes", "One-Punch Man", and the three "One-Punch Man season N"
articles — frozen into tools/data/one-punch-man.json, and asserted here before
anything is written.

THE THIRD SEASON IS HALF A SEASON, AND THAT IS THE SOURCE'S OWN SHAPE. Its
first cours ran from October 12 to December 29, 2025 and is listed in full. A
second cours was announced the day the first ended, for 2027, and the source
carries that year and nothing else — no episode count, no titles, no table, and
the season infobox still reads `last_aired = present`. There is therefore
nothing of it to list: an unreleased row would have to invent its own title.
main() asserts each of those absences, so the day Wikipedia starts filling
the second cours in, this build fails instead of quietly staying short.

THE TWO RECAP SPECIALS ARE NOT ROWS. Numbered 12.5 and 24.5, filed under their
own heading outside both episode tables, and described by the source as
commemorative specials recapping the previous season. They are the episodes
above told again, so listing them would count the same viewing twice. Named in
the notes rather than dropped silently, and main() asserts there are exactly two
and that both still describe themselves as recaps.

THE OVAs AND THE OAD ARE ROWS, AND EVERY ONE IS OPTIONAL. Twelve OVAs came with
the two seasons' Blu-ray and DVD volumes, six per season; "Road to Hero" came
with the special edition of the tenth manga volume, which is why the main
article's infobox counts the run as "36 + 12 OVAs" and files that one
separately as an OAD. They are new animation rather than compilations, so
unlike the recaps they are worth a row — and they never aired, so `opt` keeps
them out of the way of anyone watching the broadcast run. Set OVA_ROWS to False
to take the section and its note out together; nothing else has to change.

NOTHING IS WEIGHTED, AND THAT IS A FINDING WITH RECEIPTS. Weighting is
all-or-nothing — a row with no `w` silently counts as one hour, CLU-131 — so a
partial set of runtimes would be worse than none. harvest.py looked in every
place a duration could live and every one is empty:

  * not one of the 51 {{Episode list}} rows on the four articles that carry
    them (36 episodes, 13 home-video episodes, 2 recap specials) has a
    running-time field of any kind;
  * no episode title is even a wikilink, and none of the 49 titles has an
    article of its own: five of them resolve to unrelated works and not one of
    the 49 "<title> (One-Punch Man)" spellings exists;
  * the 25 per-episode Wikidata items that DO exist — twelve declared by the
    season 1 item, thirteen by the season 2 item — carry no P2047 between them,
    and season 3's item declares no parts at all;
  * neither the three season items, nor the anime series item all three hang
    off (Q22341674), nor the franchise item, nor the episode-list item carries
    a P2047;
  * none of the three season infoboxes has a runtime field, and neither does
    the main article's television infobox.

The only lengths published anywhere in the five articles are 24 minutes for
Road to Hero, on its own OAD infobox, and "ten-minute" in prose for the second
season's OVAs. Spreading one bundled extra's length across 36 broadcast
episodes would invent precision the source refuses to give, so every row counts
one and the page counts episodes. main() asserts each of those zeroes, and the
day a runtime appears this generator stops rather than shipping a stale claim.

CROSS-LIST TICK SYNC DOES NOT APPLY. src/build.py syncs film-kind and game-kind
rows only, and this kind is "anime". Belt and braces, main() also asserts no row
note carries a bare four-digit year, because build.py's `_year_of` falls back to
reading one out of a note when `n` is not a year.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop  # noqa: E402

SLUG = "one-punch-man"
DATA = pathlib.Path(__file__).resolve().parent / "data" / (SLUG + ".json")

KIND = "anime"
SEASONS = 3
PER_SEASON = 12
EPISODES = SEASONS * PER_SEASON          # 36 broadcast episodes
OVA_ROWS = True                          # the 13 home-video rows, all optional

ACCENT = "#B02A1E"       # the red of Saitama's gloves and boots
ACCENT_DARK = "#F5C93B"  # ...and the yellow of the jumpsuit

GROUPS = ("Bundled with the manga",
          "One-Punch Man Season 1 OVAs",
          "One-Punch Man Season 2 OVAs")


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


def check_shape(d):
    """Everything the copy below states, checked against the harvest."""
    ov, series, seasons = d["overview"], d["series"], d["seasons"]
    assert len(seasons) == SEASONS, "%d seasons in the data" % len(seasons)

    # --- counts, three ways per season: rows, season infobox, series overview
    claimed = [ov["s1_episodes"], ov["s2_episodes"], ov["s3_part1_episodes"]]
    for s, want in zip(seasons, claimed):
        assert len(s["episodes"]) == PER_SEASON, \
            "season %d parsed %d rows" % (s["n"], len(s["episodes"]))
        assert s["num_episodes"] == PER_SEASON, \
            "season %d's infobox says %d" % (s["n"], s["num_episodes"])
        assert want == PER_SEASON, \
            "the series overview gives season %d %r episodes" % (s["n"], want)
        assert s["network"] == "TV Tokyo", s["network"]
        assert [e["in_season"] for e in s["episodes"]] == \
            list(range(1, PER_SEASON + 1)), \
            "season %d's in-season numbering is not 1..%d" % (s["n"], PER_SEASON)

    # --- one contiguous run of 36 across the three seasons ------------------
    overall = [e["overall"] for s in seasons for e in s["episodes"]]
    assert overall == list(range(1, EPISODES + 1)), \
        "the overall numbering is not contiguous 1..%d" % EPISODES
    assert series["infobox_episodes"].startswith(str(EPISODES)), \
        "the series infobox now says %r" % series["infobox_episodes"]

    # --- dates: the infobox, the overview and the rows must agree ----------
    firsts = [ov["s1_start"], ov["s2_start"], ov["s3_part1_start"]]
    lasts = [ov["s1_end"], ov["s2_end"], ov["s3_part1_end"]]
    for s, f, l in zip(seasons, firsts, lasts):
        assert s["episodes"][0]["airdate"] == f == s["first_aired"], \
            "season %d starts %r / %r / %r" % (s["n"],
                                               s["episodes"][0]["airdate"], f,
                                               s["first_aired"])
        assert s["episodes"][-1]["airdate"] == l, \
            "season %d ends %r, the overview says %r" \
            % (s["n"], s["episodes"][-1]["airdate"], l)
        assert all(e["airdate"] for e in s["episodes"]), \
            "season %d has an episode with no airdate" % s["n"]

    # --- the second cours of season 3: announced, dated, and empty ---------
    assert seasons[2]["last_aired_raw"] == "present", \
        "season 3's infobox now closes with %r — it may be finished" \
        % seasons[2]["last_aired_raw"]
    assert ov["s3_part2_start_year"] == "2027", \
        "the second cours is now dated %r" % ov["s3_part2_start_year"]
    assert ov["s3_part2_episodes"] == "" and ov["s3_part2_end"] == "", \
        "the series overview has started filling the second cours in: %r / %r" \
        % (ov["s3_part2_episodes"], ov["s3_part2_end"])

    # --- who made what ------------------------------------------------------
    assert series["studio_by_season"] == {"1": "Madhouse", "2": "J.C.Staff",
                                          "3": "J.C.Staff"}, \
        "the studios have changed: %r" % series["studio_by_season"]

    # --- the recap specials -------------------------------------------------
    recaps = d["recap_specials"]
    assert [r["numbered"] for r in recaps] == [12.5, 24.5], \
        "the recap specials are numbered %r" % [r["numbered"] for r in recaps]
    for r in recaps:
        assert "recap" in r["summary"].lower(), \
            "%r no longer calls itself a recap: %r" % (r["t"], r["summary"])
        assert r["airdate"], "%r has no airdate" % r["t"]

    # --- the home-video episodes -------------------------------------------
    ovas = d["ovas"]
    assert len(ovas) == 13, "%d home-video rows" % len(ovas)
    assert [o["group"] for o in ovas] == \
        [GROUPS[0]] + [GROUPS[1]] * 6 + [GROUPS[2]] * 6, \
        "the OVA table's grouping has changed: %r" % [o["group"] for o in ovas]
    assert ovas[0]["n"] == 0 and ovas[0]["t"] == "Road to Hero", \
        "the OAD row is now %r" % (ovas[0],)
    assert series["oad_runtime"] == "24 minutes", series["oad_runtime"]
    assert [o["n"] for o in ovas[1:7]] == list(range(1, 7)) and \
        [o["n"] for o in ovas[7:]] == list(range(1, 7)), \
        "the OVAs are no longer numbered 1..6 twice"
    assert all(o["released"] for o in ovas), "an OVA has no release date"
    assert "12 OVAs" in series["infobox_episodes"], \
        "the series infobox no longer counts 12 OVAs: %r" \
        % series["infobox_episodes"]

    # --- the runtime hunt: every zero, asserted before anything is built ---
    h = d["runtime_hunt"]
    assert h["episode_table_runtime_fields"] == [], \
        "an episode row has grown a running-time field: %r" \
        % h["episode_table_runtime_fields"]
    assert h["title_wikilinks"] == 0, \
        "%d episode titles are now wikilinks" % h["title_wikilinks"]
    assert h["episode_titles_asked"] == EPISODES + 13, \
        "%d titles were checked for articles" % h["episode_titles_asked"]
    assert h["qualified_pages_that_exist"] == {}, \
        "an episode now has its own article: %r" % h["qualified_pages_that_exist"]
    assert h["opm_named_in_any_resolved_page_title"] == [], \
        "an episode title now resolves to a One-Punch Man page: %r" \
        % h["opm_named_in_any_resolved_page_title"]
    assert len(h["episode_title_pages_that_exist"]) == 5, \
        "%d episode titles resolve to some article" \
        % len(h["episode_title_pages_that_exist"])
    assert h["wikidata_items_below_with_P2047"] == [], \
        "a Wikidata item below the series now states a duration: %r" \
        % h["wikidata_items_below_with_P2047"]
    assert len(h["wikidata_items_below"]) == 28, \
        "%d items hang below the series" % len(h["wikidata_items_below"])
    for page, wd in h["wikidata"].items():
        assert wd["P2047"] == [], "%s (%s) now states a duration: %r" \
            % (page, wd["qid"], wd["P2047"])
    per_ep = h["wikidata_part_of_hits"]
    assert len(per_ep["P4908=Q105081756 (One-Punch Man season 1)"]) == 12, \
        "season 1 no longer has 12 per-episode Wikidata items"
    assert len(per_ep["P4908=Q105081766 (One-Punch Man season 2)"]) == 13, \
        "season 2 no longer has 13 per-episode Wikidata items"
    assert per_ep["P4908=Q135945901 (One-Punch Man season 3)"] == [], \
        "season 3 has grown per-episode Wikidata items — re-run the hunt"
    assert h["season_infobox_runtime_fields"] == [], \
        "a season infobox now carries a runtime: %r" \
        % h["season_infobox_runtime_fields"]
    assert h["series_infobox_runtime"] is None, \
        "the series infobox now states a runtime: %r" % h["series_infobox_runtime"]
    assert sorted(h["prose_minute_claims"]) == ["10-minute", "24 minutes",
                                                "ten-minute"], \
        "the prose now publishes other lengths: %r" % h["prose_minute_claims"]

    # --- the one verdict on this list, quoted rather than invented ---------
    assert "largely negative" in d["reception"]["s3_sentence"], \
        "the season 3 reception sentence has changed: %r" \
        % d["reception"]["s3_sentence"]
    assert d["reception"]["s1_s2_reception_sections"] == [], \
        "seasons 1 and 2 now have reception sections of their own"


def season_sections(d):
    studios = d["series"]["studio_by_season"]
    urls = d["source"]["season_urls"]
    list_url = d["source"]["list_url"]
    out = []
    for s in d["seasons"]:
        n = s["n"]
        notes = {}
        if n == 1:
            notes[1] = "Series premiere"
        if n == 2:
            notes[s["episodes"][0]["overall"]] = \
                "First episode animated by %s rather than %s" \
                % (studios["2"], studios["1"])
        if n == SEASONS:
            notes[EPISODES] = ("Last episode of the first cours — the second "
                               "has not aired")
        items = []
        for e in s["episodes"]:
            row = {"id": "opm-e%d" % e["overall"], "t": e["t"],
                   "n": str(e["overall"])}
            if e["overall"] in notes:
                row["note"] = notes[e["overall"]]
            items.append(row)

        if n == 1:
            sub = prop.join_bits("2015", "%d episodes" % PER_SEASON,
                                 "%s on %s" % (studios["1"], s["network"]))
            intro = ("Twelve episodes, the whole of Madhouse's season, in the "
                     "order TV Tokyo ran them — %s to %s. The numbers are the "
                     "source's own overall numbering, which keeps counting "
                     "through the seasons below."
                     % (s["first_aired"], s["last_aired"]))
        elif n == 2:
            sub = prop.join_bits("2019", "%d episodes" % PER_SEASON,
                                 "%s takes over" % studios["2"])
            intro = None
        else:
            sub = prop.join_bits("2025", "%d episodes" % PER_SEASON,
                                 "the first cours of two")
            intro = ("Half a season: twelve episodes from %s to %s, with a "
                     "second cours announced for 2027 that the source dates "
                     "and describes no further. It is also the worst-received "
                     "stretch of the show — the article records that the "
                     "premiere \"received largely negative reviews from "
                     "critics\" and that later episodes drew backlash over "
                     "the animation. Worth knowing before you start it; it is "
                     "still the only animated version there is."
                     % (s["first_aired"], d["overview"]["s3_part1_end"]))
        sec = {"id": "s%d" % n, "title": "Season %d" % n, "sub": sub}
        if intro:
            sec["intro"] = intro
        if n == 1:
            sec["open"] = True
            sec["links"] = [{"label": "Season 1", "url": urls["1"]},
                            {"label": "The episode list", "url": list_url}]
        else:
            sec["links"] = [{"label": "Season %d" % n, "url": urls[str(n)]}]
        sec["items"] = items
        out.append(sec)
    return out


def ova_section(d):
    """The thirteen home-video episodes, in release order, all optional."""
    ovas = d["ovas"]
    items = []
    for o in ovas:
        if o["group"] == GROUPS[0]:
            xid, num = "opm-oad-0", "OAD"
            note = "Bundled with the special edition of the tenth manga volume"
        else:
            season = 1 if o["group"] == GROUPS[1] else 2
            xid = "opm-s%dova-%d" % (season, o["n"])
            num = "S%d OVA %d" % (season, o["n"])
            note = None
        row = {"id": xid, "t": o["t"], "n": num, "opt": True}
        if note:
            row["note"] = note
        items.append(row)
    years = sorted({int(o["released"].rsplit(" ", 1)[-1]) for o in ovas})
    return {
        "id": "extras",
        "title": "Only on home video",
        "sub": prop.join_bits("%d–%d" % (years[0], years[-1]),
                              "%d episodes" % len(items),
                              "none of them broadcast"),
        "intro": ("Optional, and safely skipped: six OVAs on each season's "
                  "Blu-ray and DVD volumes, and the OAD that shipped with a "
                  "manga volume before any of them. New animation rather than "
                  "recaps, which is why these are rows and the two recap "
                  "specials are not."),
        "links": [{"label": "The episode list", "url": d["source"]["list_url"]}],
        "items": items,
    }


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    check_shape(d)
    ov, series = d["overview"], d["series"]
    recaps = d["recap_specials"]

    sections = season_sections(d)
    if OVA_ROWS:
        sections.append(ova_section(d))

    notes = [
        ["Three seasons, thirty-six episodes, and the show is not finished.",
         "Season 1 ran on TV Tokyo from %s to %s, animated by %s; season 2 "
         "from %s to %s, with %s taking over; season 3's first cours from %s "
         "to %s. A second cours was announced the day the first one ended and "
         "is set to premiere in 2027 — and that year is all the source has: no "
         "episode count, no titles, no table, and the season's infobox still "
         "reads \"present\" where its last airdate would go. So this list "
         "stops at episode %d, and the generator asserts those absences one by "
         "one: the day Wikipedia starts filling the second cours in, the "
         "build fails instead of quietly staying short."
         % (ov["s1_start"], ov["s1_end"], series["studio_by_season"]["1"],
            ov["s2_start"], ov["s2_end"], series["studio_by_season"]["2"],
            ov["s3_part1_start"], ov["s3_part1_end"], EPISODES)],
        ["The two recap specials are not rows.",
         "A week before season 2, and again a week before season 3, TV Tokyo "
         "ran a commemorative special recapping the previous season: \"%s\" on "
         "%s and \"%s\" on %s. The source numbers them 12.5 and 24.5 and files "
         "them under their own heading, outside both episode tables. They are "
         "the episodes above told again, so listing them would count the same "
         "viewing twice — and leaving them out costs you nothing."
         % (recaps[0]["t"], recaps[0]["airdate"],
            recaps[1]["t"], recaps[1]["airdate"])],
        ["Nothing is weighted, and the hunt for a runtime came up empty "
         "everywhere.",
         "Weighting is all or nothing — a row with no weight silently counts "
         "as a full hour — so a handful of sourced lengths would be worse than "
         "none. Every place a duration could live was checked and every one is "
         "empty: not one of the 51 episode-table rows across the four articles "
         "that carry them has a running-time field; no episode title is even a "
         "link, and none of the %d titles has an article of its own — five of "
         "them resolve to unrelated works, and not one of the %d \"(One-Punch "
         "Man)\" spellings exists; the 25 per-episode Wikidata items that do "
         "exist — twelve under season 1, thirteen under season 2 — state no "
         "duration between them, and season 3's item lists no episodes at all; "
         "neither the three season items, nor the anime series item all three "
         "hang off, nor the franchise item, nor the episode-list item states "
         "one either; and no season infobox or series infobox carries a "
         "runtime field. The only lengths published anywhere in the five "
         "articles are %s for Road to Hero, on its own infobox, and "
         "\"ten-minute\" in prose for the second season's OVAs. Spreading one "
         "bundled extra's length across %d broadcast episodes would invent "
         "precision the source refuses to give, so every row counts one and "
         "this page counts episodes."
         % (EPISODES + 13, EPISODES + 13, series["oad_runtime"], EPISODES)],
    ]
    if OVA_ROWS:
        notes.append(
            ["The thirteen home-video episodes are here, and every one is "
             "optional.",
             "Twelve OVAs came bundled with the two seasons' Blu-ray and DVD "
             "volumes, six per season, and \"%s\" came bundled with the "
             "special edition of the tenth manga volume — which is why the "
             "main article counts the run as \"%s\" and files that one apart "
             "as an OAD. They are new animation rather than compilations, so "
             "they are worth a row; they never aired, so they are marked "
             "optional and cannot hold up the broadcast run. The second "
             "season's six are short — the source calls them ten-minute — and "
             "no length is published for the first season's. The manga, the "
             "original webcomic and the games are out of scope for a watch "
             "list."
             % (d["ovas"][0]["t"], series["infobox_episodes"])])
    else:
        notes.append(
            ["The OVAs and the bundled OAD are not listed.",
             "Twelve OVAs shipped with the two seasons' home video volumes, "
             "and \"%s\" with the special edition of the tenth manga volume. "
             "They are new animation rather than recaps, so their absence is a "
             "choice rather than an oversight, and it is named here so it "
             "reads as one." % d["ovas"][0]["t"]])
    notes.append(
        "Titles, numbering, airdates and the OVA table machine-read from "
        "Wikipedia's List of One-Punch Man episodes and the three One-Punch "
        "Man season articles; each season's count and its first and last "
        "airdates cross-checked against both its own infobox and the list "
        "article's series overview, the 1–%d numbering asserted contiguous, "
        "and the absence of any published runtime confirmed against Wikidata's "
        "franchise, series, season and per-episode items before this builds."
        % EPISODES)

    p = {
        "slug": SLUG,
        "title": "One-Punch Man",
        "subtitle": "every broadcast episode, and the extras after them",
        "kind": KIND,
        "popularity": 77,
        "year": "2015–",
        "blurb": "Saitama's whole television run in broadcast order — %d "
                 "episodes over three seasons, the third of them half-aired, "
                 "with the home-video episodes optional at the end."
                 % EPISODES,
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": notes,
        "sections": sections,
    }

    # --- house rules this list has to hold ---------------------------------
    check_accent()
    assert "film" not in KIND and "game" not in KIND, \
        "build.py syncs film and game kinds; %r would start syncing" % KIND
    required = 0
    for s in sections:
        for x in s["items"]:
            assert "w" not in x, "a weight crept in — this list is unweighted"
            assert not re.search(r"\b(?:18|19|20)\d{2}\b", x.get("note") or ""), \
                "row %s leaks a bare year into its note: %r" \
                % (x["id"], x["note"])
            assert not re.fullmatch(r"(18|19|20)\d{2}", x["n"]), \
                "row %s numbers itself with a year" % x["id"]
            required += 0 if x.get("opt") else 1
    assert required == EPISODES, \
        "%d non-optional rows, expected %d" % (required, EPISODES)

    out = prop.write(p)
    total = sum(len(s["items"]) for s in sections)
    print("wrote %s — %d rows in %d sections, unweighted (%d required)"
          % (out.name, total, len(sections), required))
    for s in sections:
        opt = sum(1 for x in s["items"] if x.get("opt"))
        print("   %-18s %3d rows%s  %s"
              % (s["title"], len(s["items"]),
                 " (%d optional)" % opt if opt else "", s["sub"]))
    print("   excluded: recap specials %s; season 3's second cours, due %s "
          "with no episodes published"
          % ([r["t"] for r in recaps], d["overview"]["s3_part2_start_year"]))


if __name__ == "__main__":
    main()
