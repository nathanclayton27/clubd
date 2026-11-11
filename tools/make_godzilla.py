#!/usr/bin/env python3
"""Generate properties/godzilla.json.

    python3 tools/make_godzilla.py

Every Godzilla film from 1954 on, era by era, plus the Godzilla Fest shorts
the group asked for by name and the Monarch series, one row per season. An
announced film whose article dates it is a row that weighs nothing and says
when it is due.

Reads tools/data/godzilla.json, which scratch/godzilla/build.py collected
from the filmography tables of Wikipedia's Godzilla (franchise) article
("List of Godzilla films" redirects there) and from Wikidata (P2047 runtimes,
P577 release dates), with runtimes cross-checked against each film's
Wikipedia infobox. The Fest shorts have no Wikidata items and no confirmed
runtimes anywhere on Wikipedia or Wikidata, so they weigh 0 and say so.

Structure calls, stated: the Fest shorts get their own section rather than
rows inside Reiwa — minute-long web shorts interleaved between features
muddy an era list, and the group asked for them specifically. TriStar's 1998
film fits none of Toho's eras and the MonsterVerse is a different branch, so
it stands alone as a one-film section between Heisei and Millennium, which
is where it falls in release order.
"""
import json
import pathlib

SLUG = "godzilla"

DATA = pathlib.Path(__file__).resolve().parent / "data" / "godzilla.json"

SECTIONS = [
    ("showa", "Shōwa era", None),
    ("heisei", "Heisei era", None),
    ("tristar", "TriStar (1998)", None),
    ("millennium", "Millennium era", None),
    ("reiwa", "Reiwa era", None),
    ("fest", "Godzilla Fest shorts",
     "Toho premieres official shorts free online for Godzilla Fest, its "
     "annual fan event held around Godzilla Day, November 3 — suitmation "
     "Fest Godzilla episodes alongside the 3DCG line that began with "
     "G vs. G. None of the eight has a published runtime, so they carry no "
     "width on the bar."),
    ("monsterverse", "MonsterVerse", None),
]

NOTE = {
    "gz-1998-godzilla":
        "Roland Emmerich's American reimagining for TriStar — its monster "
        "returns in Godzilla: Final Wars as Zilla",
    "gz-2017-godzilla-planet-of-the-monsters":
        "Animated — first of the anime trilogy",
    "gz-2018-godzilla-city-on-the-edge-of-battle":
        "Animated — second of the anime trilogy",
    "gz-2018-godzilla-the-planet-eater":
        "Animated — third of the anime trilogy",
    "gz-2023-monarch-legacy-of-monsters":
        "Apple TV+ series — season one, ten episodes as one row · "
        "runtime unconfirmed",
    "gz-2026-monarch-legacy-of-monsters-season-2":
        "Apple TV series — season two, ten episodes as one row · "
        "runtime unconfirmed",
}

MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")


def due(iso):
    y, m, d = (int(v) for v in iso.split("-"))
    return "Not out yet — due %d %s %d, and the bar stays empty until it " \
           "opens" % (d, MONTHS[m - 1], y)


def slug(t):
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def main():
    films = json.loads(DATA.read_text(encoding="utf-8"))

    by_era = {}
    for f in films:
        by_era.setdefault(f["era"], []).append(f)

    sections = []
    for key, title, intro in SECTIONS:
        got = by_era.pop(key)
        items = []
        for f in got:
            iid = "gz-%d-%s" % (f["year"], slug(f["title"]))
            note = f.get("note") or NOTE.get(iid, "")
            w = round((f["runtime"] or 0) / 60.0, 2)
            if f.get("upcoming"):
                assert f["runtime"] is None and not note, iid
                note = due(f["due"])
            elif f["runtime"] is None and "runtime unconfirmed" not in note:
                note += " · runtime unconfirmed"
            x = {"id": iid, "t": f["title"], "n": str(f["year"]), "w": w}
            if note:
                x["note"] = note
            items.append(x)
        hours = round(sum(f["runtime"] or 0 for f in got) / 60.0)
        years = "%d–%d" % (got[0]["year"], got[-1]["year"])
        if key == "tristar":
            sub = "1998 · one film · %d hours" % hours
        elif key == "fest":
            sub = "%s · %d shorts · premiered free online" % (years, len(got))
        elif key == "monsterverse":
            sub = "%s– · %d films and one series · %d hours" % (
                got[0]["year"], sum(1 for f in got if f["kind"] == "film"),
                hours)
        else:
            sub = "%s · %d films · %d hours" % (years, len(got), hours)
        soon = sum(1 for f in got if f.get("upcoming"))
        if soon:
            sub += " · %d not out yet" % soon
        sec = {"id": key, "title": title, "sub": sub, "items": items}
        if intro:
            sec["intro"] = intro
        sections.append(sec)

    assert not by_era, "unplaced eras: %s" % sorted(by_era)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(films) == 50, (len(ids), len(films))
    for sec, want in zip(sections, [15, 7, 1, 6, 6, 8, 7]):
        assert len(sec["items"]) == want, (sec["id"], want, len(sec["items"]))
    for s in sections:
        assert all(int(a["n"]) <= int(b["n"])
                   for a, b in zip(s["items"], s["items"][1:])), \
            "%s is out of year order" % s["title"]
    for s in sections:
        for x in s["items"]:
            assert x["w"] > 0 or "runtime unconfirmed" in x.get("note", "") \
                or x.get("note", "").startswith("Not out yet"), x["id"]

    out_films = [f for f in films
                 if f["kind"] == "film" and not f.get("upcoming")]
    nfilm = len(out_films)
    last = max(f["year"] for f in out_films)
    nshort = sum(1 for f in films if f["kind"] == "short")
    hours = round(sum(f["runtime"] or 0 for f in films) / 60.0)

    prop = {
        "slug": SLUG,
        "title": "Godzilla",
        "subtitle": "every film era by era, Godzilla Fest shorts included",
        "kind": "films",
        "popularity": 80,
        "year": "1954–",
        "blurb": "%d films from 1954 to %d, the Monarch series, and all "
                 "%d Godzilla Fest shorts." % (nfilm, last, nshort),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#2E6B3F",
        "accentDark": "#7FD096",
        "tiers": False,
        "notes": [
            ["Eras.", "Toho counts its films in four eras — Shōwa, Heisei, "
             "Millennium and Reiwa — split by the years the series went "
             "dark. The American branches sit apart: TriStar's 1998 one-off "
             "and Legendary's MonsterVerse, which includes the Monarch "
             "series, one row per season."],
            ["The Godzilla Fest shorts.", "Free online premieres for Toho's "
             "annual fan festival: the suitmation Fest Godzilla series — "
             "Godzilla Appears at Godzilla Fest, G vs. Hedorah, Gigan "
             "Attacks, Operation Jet Jaguar, All Monsters Showdown — and "
             "the 3DCG shorts G vs. G, Godzilla vs. Gigan Rex and Godzilla "
             "vs. Megalon. The two vs. shorts share their titles with the "
             "1971 and 1973 films; the year tells them apart."],
            ["Bar widths are runtimes.", "Weights are hours from Wikidata, "
             "cross-checked against each film's Wikipedia infobox — where "
             "the two disagreed by more than five minutes the infobox won. "
             "The shorts and Monarch have no runtime confirmed on "
             "Wikipedia or Wikidata, so they weigh nothing."],
            ["Not included.", "Kong: Skull Island belongs to the "
             "MonsterVerse but is a Kong film, and Wikipedia's Godzilla "
             "filmography does not count it."],
            "Titles, years and release order from the filmography of "
            "Wikipedia's Godzilla (franchise) article; the Fest shorts from "
            "the Wikipedia pages that document them; runtimes and release "
            "dates from Wikidata (P2047, P577).",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d rows (%d films out, %d shorts, 2 series rows), about %d hours"
          % (len(ids), nfilm, nshort, hours))
    for s in sections:
        print("   %-22s %2d  %s" % (s["id"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
