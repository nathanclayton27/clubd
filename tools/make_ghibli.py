#!/usr/bin/env python3
"""Generate properties/ghibli.json.

    python3 tools/make_ghibli.py

Every Studio Ghibli feature plus the two Hayao Miyazaki features made outside
it, in release order. Miyazaki's films are the focus: they are tier 1, they are
what a finish date paces you through, and everything else is marked with who
directed it instead.

Titles and years come from Wikipedia's List of Studio Ghibli works. Directors
and release dates come from Wikidata (P57, P577) rather than from that table,
whose director column is a thicket of rowspans and colspans spanning four
columns at once.

Weights: each film's own infobox, not Wikidata (CLU-425, CLU-178)
-----------------------------------------------------------------
Every bar is the runtime printed in that film's own {{Infobox film}}, chosen by
gwlib.runtime.weigh() — see that module for the rule and for why P2047 is the
wrong place to read a length from. This list used to weigh from P2047, and that
shipped **The Castle of Cagliostro at 110 minutes** while the film's own article
prints 100 and nothing was ever released at 110. Nine of the 26 rows moved when
the rule was applied; eight moved by one to five minutes, which is source noise,
and Cagliostro moved by ten, which was the defect CLU-425 sent us here to find.

What the box printed, labels and all, is recorded beside every row in
tools/data/ghibli.json as `cuts` — so the question "which version is this list
measuring" is answered by re-running this script rather than by reading 26
articles. The generator prints the chosen label on every run.

A row the rule cannot settle keeps the figure it already had and is named in
the run output, never silently re-weighted. Ocean Waves is the one: it is a
television film and its article carries {{Infobox animanga}} rather than
{{Infobox film}}, so there is no box to read and its 72 minutes stay Wikidata's.

Ocean Waves and Earwig and the Witch were made for television rather than
cinemas, but they are feature-length Ghibli films and are counted here, marked
as such. The Castle of Cagliostro and Nausicaa predate the studio.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import runtime as RT  # noqa: E402

SLUG = "ghibli"

ERAS = [
    ("before", "Before Ghibli", 0, 1985,
     "Two features Miyazaki directed before the studio existed. Nausicaa is why "
     "it exists at all — Ghibli was founded to make what came next."),
    ("eighties", "The first films", 1986, 1989,
     "Four years that establish everything: Miyazaki and Takahata alternating, "
     "and a studio with no house style beyond doing it properly."),
    ("nineties", "The nineties", 1990, 1999, ""),
    ("golden", "Spirited Away and after", 2000, 2013,
     "The Oscar, the international audience, and the run up to what Miyazaki "
     "announced as his last film."),
    ("after", "After the retirement", 2014, 9999,
     "The studio without Miyazaki directing — and then Miyazaki directing "
     "again, a decade later."),
]

NOTE = {
    "Nausicaä of the Valley of the Wind":
        "Not a Ghibli film — the studio was founded on the back of it",
    "The Castle of Cagliostro": "Not a Ghibli film — Miyazaki's first feature",
    "Grave of the Fireflies": "Released on a double bill with My Neighbor Totoro",
    "The Boy and the Heron": "Miyazaki's return, ten years after The Wind Rises",
    "The Red Turtle": "A co-production — the only Ghibli feature by a director "
                      "from outside Japan",
}


def slug(t):
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def main():
    data = pathlib.Path(__file__).resolve().parent / "data"
    films = json.loads((data / "ghibli.json").read_text(encoding="utf-8"))
    films.sort(key=lambda f: (f["released"], f["title"]))

    # ---- weights: the film's own infobox, by gwlib.runtime's rule ---------
    # A row the rule cannot settle keeps the figure it already carried — never
    # a guess, and never quietly. `cuts` is what the box printed, labels kept,
    # collected by scratch/agent-rows/measure_lists.py.
    kept, moved = [], []
    for f in films:
        cuts = [tuple(c) for c in (f.get("cuts") or [])]
        n, why = RT.weigh(cuts, f.get("cuts_range", False))
        if n is None:
            kept.append((f["title"], f["runtime"], why))
            f["runtime_why"] = "kept Wikidata's figure: " + why
            continue
        if n != f["runtime"]:
            moved.append((n - f["runtime"], f["title"], f["runtime"], n, why))
        f["runtime"], f["runtime_why"] = n, why

    sections = []
    for key, title, lo, hi, intro in ERAS:
        got = [f for f in films if lo <= f["year"] <= hi]
        if not got:
            continue
        items = []
        for f in got:
            bits = []
            if f["title"] in NOTE:
                bits.append(NOTE[f["title"]])
            if not f["miyazaki"]:
                bits.append("Directed by " + ", ".join(f["directors"]))
            if f.get("tv"):
                bits.append("Made for television")
            items.append({
                "id": "gh-%d-%s" % (f["year"], slug(f["title"])),
                "t": f["title"], "n": str(f["year"]),
                "w": round((f["runtime"] or 0) / 60.0, 2),
                "tier": 1 if f["miyazaki"] else 2,
                **({"note": " · ".join(bits)} if bits else {}),
            })
        nm = sum(1 for f in got if f["miyazaki"])
        sec = {"id": key, "title": title,
               "sub": "%d–%d · %d film%s, %d by Miyazaki · %d hours"
                      % (got[0]["year"], got[-1]["year"], len(got),
                         "" if len(got) == 1 else "s", nm,
                         round(sum((f["runtime"] or 0) for f in got) / 60.0)),
               "items": items}
        if intro:
            sec["intro"] = intro
        if key == "before":
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(films), (len(ids), len(films))
    assert all(f["runtime"] for f in films), \
        [f["title"] for f in films if not f["runtime"]]
    for s in sections:
        assert all(a["n"] <= b["n"] for a, b in zip(s["items"], s["items"][1:])), \
            "%s is out of year order" % s["title"]

    miy = [f for f in films if f["miyazaki"]]
    hours = sum(f["runtime"] for f in films) / 60.0
    mhours = sum(f["runtime"] for f in miy) / 60.0

    prop = {
        "slug": SLUG,
        "title": "Studio Ghibli",
        "subtitle": "every Ghibli film in release order, built around Miyazaki's",
        "kind": "films",
        "popularity": 79,
        "year": "1979–",
        "blurb": "%d films in release order. The %d Miyazaki directed are the "
                 "spine; the rest are marked with who made them."
                 % (len(films), len(miy)),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#3F7A55",
        "accentDark": "#7FC79A",
        "tiers": True,
        "itemTiers": True,
        "paceTiers": [1],
        "paceLabel": "the films Miyazaki did not direct",
        "notes": [
            ["Miyazaki is the spine.", "The %d films he directed are tier 1 and "
             "are what a finish date paces you through — about %d hours. The "
             "other %d are tier 2, each marked with its director, and sit "
             "outside the timeline unless you tick the box under the bar."
             % (len(miy), round(mhours), len(films) - len(miy))],
            ["Two of them are not Ghibli films.", "The Castle of Cagliostro was "
             "Miyazaki's first feature, made at Tokyo Movie Shinsha in 1979. "
             "Nausicaa came in 1984, before the studio existed — and did well "
             "enough that the studio was founded to make what came next."],
            ["Two more were made for television.", "Ocean Waves and Earwig and "
             "the Witch were produced for broadcast rather than for cinemas, "
             "and both only reached Japanese screens afterwards. They are "
             "feature-length Ghibli films all the same, and are marked."],
            ["Bar widths are runtimes, read from each film's own article.",
             "Every bar is the runtime printed in that film's own Wikipedia "
             "infobox, which is where a length keeps the name of the version "
             "it belongs to. %d of the %d have one; Ocean Waves was made for "
             "television and its article carries no film infobox, so its "
             "figure stays Wikidata's. The generator refuses to build without "
             "a runtime for every row."
             % (len(films) - len(kept), len(films))],
            "Titles and years from Wikipedia's List of Studio Ghibli works; "
            "directors and release dates from Wikidata; runtimes from each "
            "film's own Wikipedia article.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d films (%d Miyazaki), %.0f hours (%.0f Miyazaki)"
          % (len(films), len(miy), hours, mhours))
    for s in sections:
        print("   %-26s %2d  %s" % (s["title"], len(s["items"]), s["sub"][:48]))
    print("  runtimes: %d rows read the film's own infobox, %d kept Wikidata's"
          % (len(films) - len(kept), len(kept)))
    for title, cur, why in kept:
        print("     keeps %-4s %-34s %s" % (cur, title[:34], why[:54]))
    for d_, title, was, now, why in sorted(moved, key=lambda m: -abs(m[0])):
        print("     %+5d %-34s %s -> %s  (%s)"
              % (d_, title[:34], was, now, why[:44]))


if __name__ == "__main__":
    main()
