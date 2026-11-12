#!/usr/bin/env python3
"""Generate properties/zombie-films.json.

    python tools/make_zombies.py

Every feature Wikipedia's List of zombie films links, era sections from
White Zombie to the streaming wave. The bare-text entries on the source list
stay out — the same cut the body-swap list made. A link is not an article:
25 rows (24 red links on source rev 1384587879, plus I Summoned The Dead,
which has left it) have no page. CLU-649, decided under Nathan's delegation:
they keep their rows, since ids hold ticks, and the copy no longer promises
an article for every row. Shorts live on Wikipedia's separate shorts list
and are out of scope. Unweighted grab bag: director and runtime ride on the
notes, the random picker is the front door.

Data: scratch/zombies/collect.py -> tools/data/zombie-films.json
(title/page/year/director from the list's table, runtimes Wikidata P2047).
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib.prop import slug

SLUG = "zombie-films"

ERAS = [
    ("early", "Before Romero", None, 1967,
     "Voodoo pictures and haunted islands — the walking dead before anyone "
     "thought to make them hungry."),
    ("romero", "Romero and the ferals", 1968, 1984,
     "Night of the Living Dead rewrites the rules in 1968, and the Italians "
     "run with them."),
    ("video", "The video-store years", 1985, 2001,
     "Return of the Living Dead teaches zombies to talk, and the genre "
     "goes to tape."),
    ("revival", "The revival", 2002, 2012,
     "28 Days Later makes them fast, Shaun makes them funny, REC makes "
     "them found-footage — the boom years."),
    ("modern", "The modern wave", 2013, None, ""),
]

# Director spellings the source table gets wrong, keyed (title, year):
# (table's spelling, corrected spelling, citation). The id comes from the
# title, so no tick moves. Drop an entry once the table itself is fixed.
DIRECTOR_FIX = {
    ("Jombieland", 2025): (
        "Deepak Thaper", "Deepak Thapar",
        "Pind Peya Saara Jombieland Baneya rev 1368169578: infobox director, "
        "infobox writer and lead all say Thapar"),
}


def main():
    data = pathlib.Path(__file__).resolve().parent / "data" / "zombie-films.json"
    films = json.loads(data.read_text(encoding="utf-8"))

    for (t, year), (bad, good, _cite) in DIRECTOR_FIX.items():
        hit = [f for f in films if f["t"] == t and f["year"] == year]
        assert len(hit) == 1, (t, year, len(hit))
        assert hit[0].get("director") in (bad, good), (t, hit[0].get("director"))
        hit[0]["director"] = good

    sections = []
    for key, title, lo, hi, intro in ERAS:
        got = [f for f in films
               if (lo is None or f["year"] >= lo)
               and (hi is None or f["year"] <= hi)]
        assert got, key
        got.sort(key=lambda f: (f["year"], f["t"].lower()))
        items = []
        for f in got:
            bits = [b for b in (f.get("director"),
                                "%d min" % f["runtime"] if f.get("runtime")
                                else None) if b]
            base = "z-%d-%s" % (f["year"], slug(f["t"]))
            iid, n = base, 2
            while any(x["id"] == iid for x in items):
                iid = "%s-%d" % (base, n)
                n += 1
            items.append({"id": iid, "t": f["t"], "n": str(f["year"]),
                          **({"note": " · ".join(bits)} if bits else {})})
        sec = {"id": key, "title": title,
               "sub": "%d–%d · %d films" % (got[0]["year"], got[-1]["year"],
                                            len(got)),
               "items": items}
        if intro:
            sec["intro"] = intro
        if key == "early":
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(films), (len(ids), len(films))
    with_rt = sum(1 for s in sections for x in s["items"]
                  if "min" in (x.get("note") or ""))

    prop = {
        "slug": SLUG,
        "title": "Zombie Films",
        "subtitle": "the walking dead on film, era by era",
        "kind": "films",
        "popularity": 52,
        "year": "%d–" % films[0]["year"],
        "blurb": "%d zombie features, "
                 "from the voodoo pictures to the streaming wave. No order — "
                 "let the picker choose." % len(films),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": "#5A6B2E",
        "accentDark": "#A8C46A",
        "tiers": False,
        "random": True,
        "notes": [
            ["No order, no weights.", "A grab bag by design — nothing leads "
             "anywhere, a 60-minute cheapie counts the same as a two-hour "
             "epic, and the Pick-one button is the intended front door."],
            ["Linked features only.", "Wikipedia's list carries "
             "a few dozen entries it doesn't link; only the linked ones got "
             "rows, and some of those links have no article behind them. "
             "Shorts live on Wikipedia's separate shorts list and are not "
             "here."],
            "From Wikipedia's List of zombie films; runtimes from Wikidata "
            "where they exist.",
        ],
        "sections": sections,
    }

    out = (pathlib.Path(__file__).resolve().parent.parent / "properties"
           / ("%s.json" % SLUG))
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")
    print("wrote %s.json — %d films, runtimes on %d" % (SLUG, len(ids), with_rt))
    for s in sections:
        print("   %-26s %3d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
