#!/usr/bin/env python3
"""Generate properties/gossip-girl.json — the original CW series, 2007-2012.

    python3 tools/make_gossip-girl.py

One row per episode, 121 rows covering all 121 episodes. No entry in the six
season tables spans two episode numbers, so rows and episodes are the same
number here — unlike The Golden Girls, where they are not.

Deliberately excluded: the 2021 HBO Max series of the same name (a separate
show with its own episode list), the two clip specials the list page files
under "Specials" — Gossip Girl: Revealed and Gossip Girl: XOXO — and the six
Chasing Dorota webisodes. None of the three sit inside the run's 121
broadcast episodes.

Episode titles and airdates are machine-read from the six "Gossip Girl
season N" articles by scratch/agent-tv3/extract_tv3.py, which asserts every
season's numbering contiguous and equal to the list page's own Series
overview counts (121 in the lede); the committed result is
tools/data/gossip-girl-episodes.json. This script re-asserts the totals
before it writes anything.

Nothing is weighted: an episode counts one, which keeps 121 marks even.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop

SLUG = "gossip-girl"
SEASONS = 6
TOTAL = 121


def main():
    data = json.loads((pathlib.Path(__file__).resolve().parent / "data"
                       / ("%s-episodes.json" % SLUG)).read_text(encoding="utf-8"))
    assert data["stated"]["lede"] == TOTAL, data["stated"]["lede"]
    assert len(data["seasons"]) == SEASONS, len(data["seasons"])

    sections = []
    for n in range(1, SEASONS + 1):
        rows = data["seasons"][str(n)]
        items = []
        for r in rows:
            assert r["e"] == r["e2"], (n, r)      # no hour-long merges here
            item = {"id": "%s-s%de%d" % (SLUG, n, r["e"]), "t": r["t"],
                    "n": str(r["e"])}
            bits = []
            if n == 1 and r["e"] == 1:
                bits.append("Series premiere")
            if r.get("bdpilot"):
                bits.append("A backdoor pilot for a spin-off "
                            "that was not picked up")
            # no "Series finale": the last row of the last season already
            # says it (CLU-123, CLU-557)
            note = prop.join_bits(*bits)
            if note:
                item["note"] = note
            items.append(item)
        count = sum(r["e2"] - r["e"] + 1 for r in rows)
        assert count == data["stated"]["per_season"][str(n)], (n, count)
        sec = {"id": "s%d" % n, "title": "Season %d" % n,
               "sub": "%s · %d episodes" % (data["years"][str(n)], count),
               "items": items}
        if n == 1:
            sec["open"] = True
            sec["intro"] = ("Eighteen episodes: the 2007–2008 writers' strike "
                            "interrupted the season, and its last five aired "
                            "after the strike ended.")
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == TOTAL, len(ids)
    covered = sum(r["e2"] - r["e"] + 1 for v in data["seasons"].values()
                  for r in v)
    assert covered == TOTAL, covered
    assert data["strike"] is True
    assert sections[0]["items"][0]["t"] == "Pilot"
    assert sections[-1]["items"][-1]["t"] == "New York, I Love You XOXO"
    assert {s["t"] for s in data["skipped"]} == {
        "Gossip Girl: Revealed", "Gossip Girl: XOXO",
        "Chasing Dorota, 6 webisodes"}

    p = {
        "slug": SLUG,
        "title": "Gossip Girl",
        "subtitle": "the original series — six seasons on The CW",
        "kind": "tv",
        "popularity": 57,
        "year": "2007–2012",
        "blurb": "All 121 episodes of the original CW series in broadcast "
                 "order, from the pilot to the finale.",
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#243B72",
        "accentDark": "#E9A8C6",
        "tiers": False,
        "notes": [
            ["The original series only.", "This is the 2007–2012 run on The "
             "CW. The 2021 series of the same name is a separate show with "
             "its own episode list and is deliberately not listed here."],
            ["Specials and webisodes are not listed.", "Two clip specials — "
             "Gossip Girl: Revealed and Gossip Girl: XOXO — and the six "
             "Chasing Dorota webisodes sit outside the run's 121 broadcast "
             "episodes."],
            ["Season one is the short one.", "The 2007–2008 Writers Guild of "
             "America strike interrupted it; the last five of its eighteen "
             "episodes aired after the strike ended."],
            ["Nothing is weighted.", "Every episode counts one, so the strip "
             "divides evenly across 121 marks."],
            "Episode titles and airdates machine-read from the six Wikipedia "
            "season articles; every season's numbering is asserted contiguous "
            "and equal to the episode list's own counts before this builds.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d rows covering %d episodes" % (out.name, len(ids), covered))
    for s in sections:
        print("   %-10s %3d  %s" % (s["title"], len(s["items"]), s["sub"]))
    for s in sections:
        for x in s["items"]:
            if x.get("note"):
                print("   note  %-34s %s" % (x["t"][:34], x["note"]))


if __name__ == "__main__":
    main()
