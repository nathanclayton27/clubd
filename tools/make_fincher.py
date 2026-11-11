#!/usr/bin/env python3
"""Generate properties/fincher.json.

    python3 tools/make_fincher.py

David Fincher's directed features in list order: twelve released, plus The
Further Mis-Adventures of Cliff Booth, which its own article dates to IMAX on
November 25, 2026 and Netflix on December 23. A dated film ships as a w: 0 row
marked not out yet (house rule), so it carries runtime null and a note in
tools/data/fincher.json until it is out; then it gets its Wikidata runtime
and loses the note. Its "released" date (the US date on its infobox's Film
date) is asserted to be in the future, so on release day this generator
fails and the row gets revisited instead of staying "not out yet".

Also out: the producing and executive-producing credits, the music videos,
and the television work — this is the directed-features list.
"""
import datetime
import json
import pathlib

SLUG = "fincher"

ERAS = [
    ("videos", "Out of music videos", 1992, 1999,
     "An Alien sequel he has disowned in all but name, then the three "
     "films that fixed the reputation: Seven, The Game, Fight Club."),
    ("procedural", "The procedural decade", 2002, 2011,
     "Panic Room through the Dragon Tattoo remake — Zodiac's decades of "
     "unsolved paperwork sit in the middle, and The Social Network won "
     "him his widest acclaim."),
    ("streaming", "Late, mostly Netflix", 2014, 2026,
     "Gone Girl, then three films made for Netflix — his father's Citizen "
     "Kane script, a killer whose routine goes wrong, and a Quentin "
     "Tarantino script."),
]


def slug(t):
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def main():
    data = pathlib.Path(__file__).resolve().parent / "data"
    films = json.loads((data / "fincher.json").read_text(encoding="utf-8"))
    assert len(films) == 13, [f["t"] for f in films]
    films.sort(key=lambda f: (f["year"], f["t"]))
    # every film has a runtime or says why not: only a film that is not out
    # yet may go without one, and it must carry the note that says so
    assert all(bool(f["runtime"]) != bool(f.get("note")) for f in films), \
        [f["t"] for f in films]
    assert sum(1 for f in films if f["runtime"]) == 12, \
        [f["t"] for f in films if not f["runtime"]]
    # a not-out-yet film carries its release date, and the build fails the
    # day it comes out, so the row cannot quietly stay "not out yet"
    today = datetime.date.today()
    for f in films:
        if f["runtime"]:
            continue
        released = datetime.date.fromisoformat(f["released"])
        assert today < released, (
            "%s came out on %s: give it its Wikidata runtime (P2047 was "
            "140 min on 2026-11-11; the infobox said 141), drop its "
            "not-out-yet note and its released date in "
            "tools/data/fincher.json, and update the counts and notes "
            "that say twelve are out" % (f["t"], released))

    def row(f):
        r = {"id": "df-%d-%s" % (f["year"], slug(f["t"])),
             "t": f["t"], "n": str(f["year"]),
             "w": round(f["runtime"] / 60.0, 2) if f["runtime"] else 0}
        if f.get("note"):
            r["note"] = f["note"]
        return r

    sections = []
    for key, title, lo, hi, intro in ERAS:
        got = [f for f in films if lo <= f["year"] <= hi]
        assert got, title
        sec = {"id": key, "title": title,
               "sub": "%d–%d · %d films · %d hours"
                      % (got[0]["year"], got[-1]["year"], len(got),
                         round(sum(f["runtime"] or 0 for f in got) / 60.0)),
               "intro": intro,
               "items": [row(f) for f in got]}
        if key == "videos":
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == 13, len(ids)
    for s in sections:
        assert all(a["n"] <= b["n"] for a, b in zip(s["items"], s["items"][1:])), \
            "%s is out of year order" % s["title"]

    hours = sum(x["w"] for s in sections for x in s["items"])

    prop = {
        "slug": SLUG,
        "title": "David Fincher",
        "subtitle": "the directed features",
        "kind": "films",
        "popularity": 69,
        # Not a story, so not a sequence: the order these came out in
        # is a fact about the maker, not an instruction to the viewer
        # (Nathan, CLU-372). Prerequisites, where any exist, live in
        # tools/data/sequences.json and are enforced separately.
        "random": True,
        "year": "1992–2026",
        "blurb": "Thirteen features, Alien 3 to The Further Mis-Adventures "
                 "of Cliff Booth — about %d hours of controlled dread."
                 % round(hours),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": "#33484A",
        "accentDark": "#93B8BA",
        "tiers": False,
        "notes": [
            ["Features only.", "The music videos, the producing credits "
             "and the television work (Mindhunter, House of Cards) are "
             "other lists."],
            ["Bar widths are runtimes.", "From Wikidata, in hours, for "
             "the twelve that are out. Cliff Booth weighs nothing until "
             "it is."],
            "Filmography from Wikipedia's David Fincher filmography, and "
            "Cliff Booth's dates from its own article; runtimes from "
            "Wikidata.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")
    print("wrote %s.json — %d rows, %.1f hours" % (SLUG, len(ids), hours))
    for s in sections:
        print("   %-24s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
