#!/usr/bin/env python3
"""Generate properties/seinfeld.json — every episode, nine seasons.

    python3 tools/make_seinfeld.py

One row per entry in the nine season articles' episode tables: 171 rows
covering all 180 numbered episodes. Nine hour-long entries (The Boyfriend,
The Trip, The Pilot, The Raincoats, The Highlights of 100, The Cadillac,
The Bottle Deposit, The Chronicle, The Finale) are numbered as two episodes
each by the lists and sit here as one row spanning both numbers, exactly as
the season articles file them. All but The Trip aired in one sitting; its
two parts aired a week apart in August 1992.

Episode titles and airdates are machine-read from the nine "Seinfeld
(season N)" articles by scratch/agent-tv1/extract_sitcoms.py, which asserts
every season's numbering contiguous and equal to the list page's own counts
(180 in the lede); the committed result is tools/data/seinfeld-episodes.json.
"""
import json
import pathlib

SLUG = "seinfeld"


def main():
    data = json.loads((pathlib.Path(__file__).resolve().parent / "data"
                       / "seinfeld-episodes.json").read_text(encoding="utf-8"))

    sections = []
    for n in range(1, 10):
        rows = data["seasons"][str(n)]
        items = []
        for r in rows:
            span = ("%d" % r["e"]) if r["e"] == r["e2"] else "%d–%d" % (r["e"], r["e2"])
            row = {"id": "sein-s%d-%d" % (n, r["e"]), "t": r["t"],
                   "n": "S%dE%s" % (n, span)}
            if r["e"] != r["e2"]:
                row["note"] = ("Aired as one hour-long episode" if r["oneNight"]
                               else "Two parts, aired a week apart")
            items.append(row)
        count = sum(r["e2"] - r["e"] + 1 for r in rows)
        sec = {"id": "s%d" % n, "title": "Season %d" % n,
               "sub": "%s · %d episodes" % (data["years"][str(n)], count),
               "items": items}
        if n == 1:
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == 171, len(ids)
    covered = sum(r["e2"] - r["e"] + 1 for v in data["seasons"].values() for r in v)
    assert covered == 180, covered

    prop = {
        "slug": SLUG,
        "title": "Seinfeld",
        "subtitle": "every episode across nine seasons",
        "kind": "tv",
        "popularity": 82,
        "year": "1989–1998",
        "blurb": "All 180 episodes in broadcast order — nine seasons about "
                 "nothing, from The Seinfeld Chronicles to The Finale.",
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        # CLU-544: this was #B3282D, which is Marvel's red and was also, to the
        # digit, mcu-anthology's. Marvel red stays with Marvel; the show keeps
        # the deli ochre its own dark tone already used, so for the first time
        # both themes wear one hue instead of red-then-gold. dE00 6.40 from its
        # nearest neighbour (star-wars-games), 6.72:1 against the page.
        "accent": "#684800",
        "accentDark": "#E8B93F",
        "tiers": False,
        "notes": [
            ["171 rows, 180 episodes.", "Nine hour-long entries are numbered "
             "as two episodes each by the episode lists and sit here as one "
             "row spanning both numbers, exactly as the season articles file "
             "them. All but The Trip aired in one sitting."],
            "Episode titles and airdates machine-read from the nine Wikipedia "
            "season articles; every season's numbering is asserted contiguous "
            "and equal to the episode list's own counts before this builds.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json — %d rows covering %d episodes" % (SLUG, len(ids), covered))
    for s in sections:
        print("   %-10s %3d  %s" % (s["title"], len(s["items"]), s.get("sub", "")))


if __name__ == "__main__":
    main()
