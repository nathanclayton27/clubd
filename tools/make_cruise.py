#!/usr/bin/env python3
"""Generate properties/tom-cruise.json.

    python3 tools/make_cruise.py

Tom Cruise's acting filmography — every feature film he acted in, in release
order, from Wikipedia's "Tom Cruise filmography" Film table, with release dates
(P577) from Wikidata via scratch/cruise/fetch_data.py and runtimes from each
film's own article via scratch/agent-runtimes/measure.py.

The rule for what is in: a row survives only if the table itself gives it no
disqualifying note. Rows marked "Documentary" (narration jobs), "Cameo" or
"Uncredited cameo" (a walk-on in Young Guns, himself-as-Austin-Powers in
Goldmember), "Archive footage", or still unreleased ({{pending film}} /
"Post-production") are skipped, and
tools/data/cruise.json records each with its reason so this script can assert
nothing else was dropped. The table's own year and row order are authoritative
for ordering and IDs — the table is already in release order — and P577 is
carried for verification only (it disagrees once, dating Losin' It 1983
against the table's 1982).

Weights: the film's own infobox, not Wikidata (CLU-178)
-------------------------------------------------------
Every bar is the runtime printed in that film's own {{Infobox film}}, chosen by
gwlib.runtime.weigh() — see that module for the rule and for why P2047 could not
be made to work. This list used to weigh from P2047's longest in-range value,
and that shipped *Legend* at **125 minutes**: Scott's first assembly, a length
the film was never released at anywhere. Its article lists the three that were —
89 minutes (US), 93 (European), 114 (director's cut) — and a filmography in
release order wants the release, so the bar is 89. That is a 40% correction on
one row, and 20 of the 45 rows moved in total, most of them by a minute.

The rule picks the release rather than the longest cut, which matters on three
rows here: Legend, *The Outsiders* (91-minute theatrical, not the 114-minute
"Complete Novel" re-edit) and *Far and Away* (140, not the 170-minute extended
cut). Each of those says on the row which length its bar is, and VERSION_NOTE
must cover exactly that set or this script stops.

A film whose infobox gives no figure would keep its Wikidata runtime and be
reported, not invented; as read, all 45 have one.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import runtime as RT  # noqa: E402

SLUG = "tom-cruise"

KNOWN_SKIPS = {"Documentary", "Cameo", "Uncredited cameo", "Archive footage",
               "Post-production"}

# Every row whose article prints more than one length says on the row which one
# the bar is. Asserted to cover exactly that set, so a film that gains a second
# cut in its infobox stops this script rather than shipping an unexplained bar.
VERSION_NOTE = {
    "Legend": "89 min, the US theatrical cut",
    "The Outsiders": "91 min, the theatrical cut",
    "Far and Away": "140 min, the theatrical cut",
}

ERAS = [
    ("rise", "The eighties", 1981, 1989,
     "Nine years from a minor debut to an Oscar-nominated lead in Born on the "
     "Fourth of July — Risky Business, Top Gun and Rain Man all sit inside "
     "this stretch."),
    ("nineties", "The nineties", 1990, 1999,
     "The leading-man decade: the Sorkin courtroom, the Grisham thriller, the "
     "first Mission: Impossible, and a 1999 spent with Kubrick and Paul "
     "Thomas Anderson."),
    ("blockbuster", "The blockbuster years", 2000, 2014,
     "Mission sequels every few years with directors between them — Crowe, "
     "Spielberg twice, Michael Mann — and a run of science fiction to close "
     "it out."),
    ("mission", "The Mission years", 2015, 9999,
     "From Rogue Nation on the output narrows: mostly Ethan Hunt, plus the "
     "Top Gun sequel that became his biggest film."),
]

NOTE = {
    "Endless Love": "The debut — a minor role",
    "Risky Business": "The breakthrough",
    "Top Gun": "1986's highest-grossing film",
    "Born on the Fourth of July": "As Ron Kovic",
    "Mission: Impossible": "First Mission: Impossible",
    "Eyes Wide Shut": "The Kubrick one",
    "Magnolia": "Oscar-nominated supporting turn",
    "Minority Report": "The first of two with Spielberg",
    "War of the Worlds": "Spielberg again",
    "Tropic Thunder": "As Les Grossman",
    "Valkyrie": "As Claus von Stauffenberg",
    "Top Gun: Maverick": "His highest-grossing film",
    "Mission: Impossible – The Final Reckoning": "The eighth Mission: Impossible",
}


def slug(t):
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def main():
    data = pathlib.Path(__file__).resolve().parent / "data"
    rows = json.loads((data / "cruise.json").read_text(encoding="utf-8"))

    years = [r["year"] for r in rows]
    assert years == sorted(years), "table rows are not in year order"
    skipped = [r for r in rows if r["skip"]]
    assert all(r["skip"] in KNOWN_SKIPS for r in skipped), \
        "unknown skip reason: " + repr(sorted({r["skip"] for r in skipped} - KNOWN_SKIPS))
    films = [r for r in rows if not r["skip"]]

    # Weights: the film's own infobox, by gwlib.runtime's rule. A row the rule
    # cannot settle keeps its Wikidata figure — never a guess.
    needs_note, moved, kept = set(), [], []
    for f in films:
        cuts = [tuple(c) for c in (f.get("infobox_cuts") or [])]
        n, why = RT.weigh(cuts, f.get("infobox_range", False))
        if n is None:
            kept.append((f["title"], f["runtime"], why))
            n = f["runtime"]
        elif n != f["runtime"]:
            moved.append((f["title"], f["runtime"], n, why))
        if len(cuts) > 1 or f.get("infobox_range"):
            needs_note.add(f["title"])
        f["runtime"] = n
    assert needs_note == set(VERSION_NOTE),         "VERSION_NOTE must name exactly the rows whose article prints more than "         "one length: missing %s, stale %s"         % (sorted(needs_note - set(VERSION_NOTE)),
           sorted(set(VERSION_NOTE) - needs_note))

    no_rt = [f for f in films if not f["runtime"]]

    sections = []
    for key, title, lo, hi, intro in ERAS:
        got = [f for f in films if lo <= f["year"] <= hi]
        assert got, "era %r is empty" % key
        items = []
        for f in got:
            bits = [NOTE[f["title"]]] if f["title"] in NOTE else []
            if f["title"] in VERSION_NOTE:
                bits.append(VERSION_NOTE[f["title"]])
            items.append({
                "id": "tc-%d-%s" % (f["year"], slug(f["title"])),
                "t": f["title"], "n": str(f["year"]),
                "w": round((f["runtime"] or 0) / 60.0, 2),
                **({"note": " · ".join(bits)} if bits else {}),
            })
        sec = {"id": key, "title": title,
               "sub": "%d–%d · %d films · %d hours"
                      % (got[0]["year"], got[-1]["year"], len(got),
                         round(sum((f["runtime"] or 0) for f in got) / 60.0)),
               "intro": intro, "items": items}
        if key == "rise":
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(films), (len(ids), len(films))
    assert len(films) + len(skipped) == len(rows), "a row fell through the eras"
    assert all(NOTE_TITLE in {f["title"] for f in films} for NOTE_TITLE in NOTE), \
        "NOTE keys that match no film: " + repr(sorted(set(NOTE) - {f["title"] for f in films}))

    hours = sum(f["runtime"] or 0 for f in films) / 60.0
    hunt = [f for f in films if f["title"].startswith("Mission: Impossible")]

    prop = {
        "slug": SLUG,
        "title": "Tom Cruise",
        "subtitle": "the acting filmography, in release order",
        "kind": "films",
        "popularity": 79,
        "year": "%d–%d" % (films[0]["year"], films[-1]["year"]),
        "blurb": "%d films in release order, %d to %d — about %d hours, %d of "
                 "them as Ethan Hunt."
                 % (len(films), films[0]["year"], films[-1]["year"],
                    round(hours), len(hunt)),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": "#1F6F63",
        "accentDark": "#6FD0B8",
        "tiers": False,
        "notes": [
            ["What is skipped.", "Six rows of Wikipedia's table are not here: "
             "two cameos — an uncredited walk-on in Young Guns and a turn as "
             "himself in Austin Powers in Goldmember — narration on two "
             "documentaries, an archive-footage appearance in The Queen, and "
             "Digger, still in post-production. This is the acted feature "
             "films, released."],
            ["Bar widths are runtimes, read from each film's own article.",
             "Every one of the %d has a runtime printed in its own Wikipedia "
             "infobox, and where an article lists more than one length the bar "
             "is the theatrical release and the row says so — Legend went out "
             "at 89 minutes, not the 125 of an assembly cut that was never "
             "released. About %d hours end to end, %d of them as Ethan Hunt."
             % (len(films), round(hours),
                round(sum(f["runtime"] for f in hunt) / 60.0))],
            "Filmography from Wikipedia's Tom Cruise filmography; runtimes "
            "from each film's own Wikipedia article, release dates from "
            "Wikidata.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d films, %.1f hours" % (len(films), hours))
    print("  runtimes: %d rows moved to the film's own infobox, %d kept what "
          "they had" % (len(moved), len(kept)))
    for t, was, now, why in sorted(moved, key=lambda m: -abs(m[2] - (m[1] or 0))):
        print("   %+5d  %-38s %-4s -> %-4s  %s"
              % (now - (was or 0), t[:38], was, now, why[:52]))
    for t, was, why in kept:
        print("   kept   %-38s %-4s       %s" % (t[:38], was, why[:52]))
    for s in sections:
        print("   %-22s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))
    print("  skipped %d rows:" % len(skipped))
    for r in skipped:
        print("   %d %-38s %s" % (r["year"], r["title"], r["skip"]))
    print("  missing runtimes: %s"
          % (", ".join("%s (%d)" % (f["title"], f["year"]) for f in no_rt) or "none"))


if __name__ == "__main__":
    main()
