#!/usr/bin/env python3
"""Generate properties/mst3k.json — every experiment, KTMA to RiffTrax.

    python3 tools/make_mst3k.py

One row per experiment, titled by the film riffed, numbered by episode code
(512 = season 5, episode 12; KTMA episodes are K01-K21): the KTMA-TV season
(optional — it aired only in Minneapolis before the national run, and its
unaired pilot K00 rides along), seasons 1-7 on The Comedy Channel / Comedy
Central, the 1996 theatrical movie in its place, seasons 8-10 on the Sci-Fi
Channel, and the revival seasons — 11-12 on Netflix, 13 on the Gizmoplex,
14 (The RiffTrax Experiments) from RiffTrax. 236 rows.

Season 14 is still coming out. Its last episode, 1404, is dated 20 November
2026 and ships now under the dated-announcement rule, its note saying it is
not out yet. The list is unweighted, so the row carries no `w`: a lone
`w: 0` would switch the page into hours with every other episode an invented
hour (CLU-131). The aired/upcoming split is frozen at the extractor's TODAY
(2026-11-11), not read from the clock, so nothing fails by itself when 1404
comes out. After 20 November 2026, bump TODAY in
scratch/agent-tv1/extract_mst3k.py and rerun it; the UPCOMING assert then fails
until this file and 1404's note are updated.

Everything is machine-read from "List of Mystery Science Theater 3000
episodes" by scratch/agent-tv1/extract_mst3k.py, which asserts each season's
row count against the article's own series overview; the committed result is
tools/data/mst3k-episodes.json. K03's note follows the article: long lost,
it resurfaced in March 2026. The extractor pins the episode codes of seasons
1 and 6 as first shipped: the article renumbered season 6 on 2026-09-10
(rev 1374243670) and season 1 on 2026-10-23 (rev 1381592816), and a code is
a row id (CLU-621). Season 6 shipped with its real codes (Satellite News:
604 is Zombie Nightmare, 615 Kitten with a Whip), so it stays as pinned.
Season 1 shipped with ten wrong ones: Women of the Prehistoric Planet is 104
(Satellite News, and the article since that edit), not 113. Here those rows
show their real codes, in code order, under the ids they shipped with
(S1_SHOWN below).
"""
import json
import pathlib

SLUG = "mst3k"

ERA = {1: "the national run begins, on The Comedy Channel",
       8: "the Sci-Fi Channel years begin",
       11: "the Netflix revival begins",
       13: "the Gizmoplex season",
       14: "The RiffTrax Experiments"}

MONTHS = ("January February March April May June July August September "
          "October November December").split()

# Dated and not out yet, as of the extractor's TODAY. Checked against the
# committed data, not the clock: after 20 November 2026 bump TODAY in the
# extractor and rerun it, and this assert fails until 1404 is updated.
UPCOMING = {"1404": "2026-11-20"}

# Season 1's ids are its codes as first shipped, when the article filed Women
# of the Prehistoric Planet last, as 113, so 104-112 each sat one slot early.
# Its real code is 104, and each of the others is one higher. An id never
# moves (it is where readers' ticks live), so each row keeps its id, shows its
# real code, and sorts by it (CLU-621, decided 2026-11-12).
S1_SHOWN = {"mst-113": "104"}
S1_SHOWN.update({"mst-%d" % c: "%d" % (c + 1) for c in range(104, 113)})
S1_TITLES = {"mst-104": "The Corpse Vanishes",
             "mst-112": "The Black Scorpion",
             "mst-113": "Women of the Prehistoric Planet"}


def due(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return "%d %s %d" % (d, MONTHS[m - 1], y)


def main():
    data = json.loads((pathlib.Path(__file__).resolve().parent / "data"
                       / "mst3k-episodes.json").read_text(encoding="utf-8"))

    sections = []
    for s in data["sections"]:
        if s["kind"] == "movie":
            r = s["rows"][0]
            sections.append({
                "id": "movie", "title": "The Movie",
                "sub": "1996 · the theatrical feature, between seasons 7 and 8",
                "items": [{"id": "mst-movie", "t": r["t"], "n": "1996",
                           "note": "%d film · riffed in theatres" % r["film_year"]}],
            })
            continue
        items = []
        for r in s["rows"]:
            row = {"id": "mst-%s" % r["code"].lower(), "t": r["t"],
                   "n": r["code"],
                   "note": "%d film" % r["film_year"]}
            if r["note_unaired"]:
                row["note"] += " · the unaired pilot"
            if r["code"] == "K03":
                row["note"] += " · long lost, resurfaced in 2026"
            if "upcoming" in r:
                row["note"] += " · not out yet, due %s" % due(r["upcoming"])
            if s["kind"] == "ktma":
                row["opt"] = True
            items.append(row)
        if s.get("season") == 1:
            got = {x["id"]: x["t"] for x in items if x["id"] in S1_TITLES}
            assert got == S1_TITLES, got
            for x in items:
                x["n"] = S1_SHOWN.get(x["id"], x["n"])
            items.sort(key=lambda x: int(x["n"]))
            assert [x["n"] for x in items] == [
                "%d" % c for c in range(101, 114)], items
        if s["kind"] == "ktma":
            sec = {"id": "k", "title": "KTMA (Season 0)",
                   "sub": "%s · 21 episodes + the unaired pilot · optional"
                          % s["years"],
                   "intro": "The year on Minneapolis's KTMA-TV, before the "
                            "national run. One episode was lost for decades. "
                            "Start at season 1 unless you want all of it.",
                   "items": items}
        else:
            n = s["season"]
            sub = "%s · %d episodes" % (s["years"], len(items))
            if n in ERA:
                sub += " · " + ERA[n]
            sec = {"id": "s%d" % n, "title": "Season %d" % n,
                   "sub": sub, "items": items}
            if n == 1:
                sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == 236, len(ids)
    assert sum(1 for s in sections for x in s["items"] if x.get("opt")) == 22
    assert [s["id"] for s in sections] == (
        ["k"] + ["s%d" % i for i in range(1, 8)] + ["movie"]
        + ["s%d" % i for i in range(8, 15)])
    assert data["excluded"] == [], data["excluded"]
    assert {r["code"]: r["upcoming"] for s in data["sections"]
            for r in s["rows"] if "upcoming" in r} == UPCOMING

    prop = {
        "slug": SLUG,
        "title": "Mystery Science Theater 3000",
        "subtitle": "every experiment, KTMA to RiffTrax",
        "kind": "tv",
        "popularity": 46,
        # Not a story, so not a sequence: the order these came out in
        # is a fact about the maker, not an instruction to the viewer
        # (Nathan, CLU-372). Prerequisites, where any exist, live in
        # tools/data/sequences.json and are enforced separately.
        "random": True,
        "year": "1988–2026",
        "blurb": "All 236 experiments in episode order — the KTMA year, the "
                 "cable runs, the movie, and the revivals, each row the film "
                 "it riffs.",
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": "#7A6200",
        "accentDark": "#F2C230",
        "tiers": False,
        "notes": [
            ["One row per experiment.", "The number is the episode code — 512 "
             "is season 5, episode 12; KTMA episodes are K01–K21 — and the "
             "title is the film riffed. Each row's note carries that film's "
             "release year, as the episode list files it."],
            ["KTMA is optional.", "The 1988–89 season aired only on "
             "Minneapolis's KTMA-TV, before the national run; one of its "
             "episodes, long lost, resurfaced only in 2026. Its 21 episodes "
             "and the unaired pilot K00 are marked optional."],
            "Machine-read from Wikipedia's List of Mystery Science Theater "
            "3000 episodes; every season's row count is asserted against the "
            "article's own series overview before this builds.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json — %d rows" % (SLUG, len(ids)))
    for s in sections:
        print("   %-18s %3d  %s" % (s["title"], len(s["items"]), s.get("sub", "")[:52]))


if __name__ == "__main__":
    main()
