#!/usr/bin/env python3
"""Generate properties/a24.json.

    python3 tools/make_a24.py

Every film on Wikipedia's "List of A24 films" that carries a release date, in
release order: both released-films tables (2010s and 2020s) plus the dated
upcoming films, which are noted "Not out yet". Undated films and films in
development are excluded by scratch/a24/build_data.py, which builds
tools/data/a24.json and records how many it left out.

The source list does not split distributed films from produced ones into
separate tables; its Notes column marks the difference ("U.S. distribution
only", "Also produced by A24", ...) and each row here keeps that annotation
verbatim after the director. Weights are Wikidata runtimes (P2047) in hours;
a film with no runtime there weighs 0 and is counted in the notes.
"""
import json
import pathlib
import unicodedata

SLUG = "a24"

# era boundaries chosen so the sections stay near an even row count
# (27 / 33 / 36 / 36 / 43 / 36) while still breaking on real turns
ERAS = [
    ("acquisitions", "The acquisition years", 2013, 2015,
     "A24 launched in August 2012 and spent its first three years buying "
     "finished films — every entry here is a distribution pickup. Amy won "
     "the company its first Academy Award."),
    ("moonlight", "Moonlight and after", 2016, 2017,
     "Moonlight — financed with Plan B, the first film A24 produced itself — "
     "won Best Picture. From here the list mixes its own productions with "
     "the pickups."),
    ("peak-indie", "The A24 horror years", 2018, 2019,
     "Hereditary, Midsommar and The Lighthouse sit in the same stretch as "
     "Eighth Grade and Uncut Gems. 2019's twenty-one releases made it the "
     "busiest year of the company's first decade."),
    ("pandemic", "The pandemic dip and the sweep", 2020, 2022,
     "Three releases in all of 2020, then the climb back out — capped by "
     "Everything Everywhere All at Once sweeping the major categories at "
     "the Oscars."),
    ("scale", "Scaling up", 2023, 2024,
     "Forty-three releases in two years, the widest slate yet."),
    ("now", "Now and next", 2025, 9999,
     "The current slate, through everything A24 has put a date on. "
     "Backrooms became the company's highest-grossing film; the rows "
     "marked below are not out yet."),
]


def fold(t):
    """ASCII-fold a title into an id fragment."""
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("&", " and ")
    keep = "".join(c.lower() if (c.isascii() and c.isalnum()) else "-"
                   for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    keep = keep.strip("-")
    assert keep and keep.isascii(), "id fragment collapsed for %r" % t
    return keep


def main():
    here = pathlib.Path(__file__).resolve().parent
    data = json.loads((here / "data" / "a24.json").read_text(encoding="utf-8"))
    meta, films = data["meta"], data["films"]

    assert all(a["date"] <= b["date"] for a, b in zip(films, films[1:])), \
        "data file is out of release order"

    released = [f for f in films if f["status"] == "released"]
    coming = [f for f in films if f["status"] == "scheduled"]
    assert len(released) + len(coming) == len(films)

    sections = []
    for key, title, lo, hi, intro in ERAS:
        got = [f for f in films if lo <= f["year"] <= hi]
        assert got, "era %r is empty" % key
        items = []
        for f in got:
            bits = [f["director"]]
            if f["note"]:
                bits.append(f["note"])
            if f["status"] == "scheduled":
                bits.append("Not out yet")
            items.append({
                "id": "a24-%d-%s" % (f["year"], fold(f["title"])),
                "t": f["title"], "n": str(f["year"]),
                "w": round(f["runtime"] / 60.0, 2) if f["runtime"] else 0.0,
                "note": " · ".join(bits),
            })
        hours = sum(f["runtime"] or 0 for f in got) / 60.0
        last = "2028" if hi == 9999 else str(hi)
        sections.append({
            "id": key, "title": title,
            "sub": "%d–%s · %d films · %d hours"
                   % (lo, last, len(got), round(hours)),
            "intro": intro,
            "items": items,
        })

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids: %s" % sorted(
        i for i in set(ids) if ids.count(i) > 1)
    assert len(ids) == len(films), (len(ids), len(films))

    have = [f for f in films if f["runtime"]]
    hours = sum(f["runtime"] for f in have) / 60.0
    no_rt_released = [f for f in released if not f["runtime"]]
    no_rt_coming = [f for f in coming if not f["runtime"]]

    prop = {
        "slug": SLUG,
        "title": "A24",
        "subtitle": "every film with a release date, in order",
        "kind": "films",
        "popularity": 66,
        # A distributor's catalogue, not a story: the order A24 released
        # these in says nothing about the order to watch them in
        # (Nathan, CLU-372, approved 2026-08-27). Prerequisites, where any
        # exist, live in tools/data/sequences.json and are enforced separately.
        "random": True,
        "year": "2013–",
        "blurb": "Everything A24 has released or dated, A Glimpse Inside the "
                 "Mind of Charles Swan III through Elden Ring — %d films, "
                 "about %d hours." % (len(films), round(hours)),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#111111",
        "accentDark": "#E8E8E8",
        "tiers": False,
        "notes": [
            ["Every film with a release date.",
             "%d released and %d upcoming films, in release order, from "
             "Wikipedia's List of A24 films. The %d films that have started "
             "shooting but carry no date, and the %d in development, are not "
             "listed — they join once A24 dates them. Upcoming rows are "
             "marked \"Not out yet\"."
             % (len(released), len(coming), meta["excluded_undated"],
                meta["excluded_in_development"])],
            ["A24 distributes some films and produces others.",
             "The source list does not separate them into tables; its Notes "
             "column does. The early years are almost all acquisitions — "
             "rows marked \"U.S. distribution only\" and the like — while "
             "\"Also produced by A24\" marks the films it made itself, "
             "starting with Moonlight. Each row here keeps the list's "
             "annotation, after the director; a row with neither carries no "
             "annotation on the list."],
            ["Bar widths are runtimes.",
             "From Wikidata, in hours — about %d in all. %d films have no "
             "runtime there — all %d upcoming films plus %d already released "
             "— and weigh nothing, so they cannot drag a group's pace."
             % (round(hours), len(no_rt_released) + len(no_rt_coming),
                len(no_rt_coming), len(no_rt_released))],
            "Catalogue, dates and distribution notes from Wikipedia's List "
            "of A24 films; runtimes from Wikidata.",
        ],
        "sections": sections,
    }

    out = here.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d films (%d released, %d upcoming), %.1f hours weighted"
          % (len(films), len(released), len(coming), hours))
    print("  no runtime on Wikidata: %d (%d released, %d upcoming)"
          % (len(no_rt_released) + len(no_rt_coming),
             len(no_rt_released), len(no_rt_coming)))
    for s in sections:
        print("   %-28s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
