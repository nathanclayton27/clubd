#!/usr/bin/env python3
"""Generate properties/one-location-films.json — films that never leave.

    python tools/make_olf.py

House-curated: films set (almost) entirely in one place, Lifeboat to Oxygen.
Every row's title, year, runtime and director are machine-read from the
film's own Wikipedia article infobox (scratch/agent-canons/collect_olf.py);
the note names the location conceit. Unweighted grab bag, Random intended.
"""
import json
import pathlib
import unicodedata

SLUG = "one-location-films"
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = pathlib.Path(__file__).resolve().parent / "data" / ("%s.json" % SLUG)
OUT = ROOT / "properties" / ("%s.json" % SLUG)

ERAS = [
    ("classics", "The classics", None, 1975,
     "Hitchcock keeps proving a single set is enough; Lumet and Buñuel "
     "agree."),
    ("slow", "Word of mouth", 1976, 2009,
     "A quarter century where the one-room film survives on dares and "
     "dinner conversation."),
    ("boom", "The boom", 2010, None,
     "Cheap cameras and festival slots make the single location a genre of "
     "its own."),
]


def slug(t):
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    films = d["films"]
    assert all(f["runtime"] and f["year"] and f["conceit"] for f in films)

    sections = []
    for key, title, lo, hi, intro in ERAS:
        got = [f for f in films
               if (lo is None or f["year"] >= lo)
               and (hi is None or f["year"] <= hi)]
        assert got, key
        got.sort(key=lambda f: (f["year"], f["t"]))
        items = [{
            "id": "olf-%d-%s" % (f["year"], slug(f["t"])),
            "t": f["t"], "n": str(f["year"]),
            "note": "%s · %d min" % (f["conceit"], f["runtime"]),
        } for f in got]
        sec = {"id": key, "title": title,
               "sub": "%d–%d · %d films" % (got[0]["year"], got[-1]["year"],
                                            len(got)),
               "intro": intro, "items": items}
        if key == "classics":
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), \
        "duplicate ids: %s" % sorted({i for i in ids if ids.count(i) > 1})[:6]
    assert len(ids) == len(films)

    prop = {
        "slug": SLUG,
        "title": "One Location",
        "subtitle": "films that never leave the room",
        "kind": "films",
        "popularity": 28,
        "year": "%d–%d" % (min(f["year"] for f in films),
                           max(f["year"] for f in films)),
        "blurb": "%d films set (almost) entirely in one place — a jury room, "
                 "a lifeboat, a coffin, a car. Any order; every note names "
                 "the room." % len(films),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        # CLU-544: this was #46586B, identical to Frasier's. Frasier keeps the
        # Seattle slate — a real show with a real palette outranks a genre list
        # on a colour neither chose deliberately — and this list takes the
        # leather and wood of the room it is about, which also puts it in the
        # same warm family as its own dark tone. dE00 9.90 from its nearest
        # neighbour (wolverine), 4.47:1 against the page.
        "accent": "#846054",
        "accentDark": "#D9A94E",
        "tiers": False,
        "random": True,
        "notes": [
            ["Added here — shout if it doesn't belong.",
             "\"One location\" is a judgment call (Devil has a lobby, Dogville "
             "paints its town on the floor), so the picks are the house's "
             "own — veto freely, nominate more. The facts are not judgment "
             "calls: every title, year and runtime is read from the film's "
             "own Wikipedia article."],
            ["No order, no weights.",
             "A grab bag — hit Random. Runtimes ride on the notes; most of "
             "these are lean by design."],
            "Facts from each film's Wikipedia article infobox; the conceit "
            "lines are ours.",
        ],
        "sections": sections,
    }

    with OUT.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")
    print("wrote %s.json — %d films" % (SLUG, len(films)))
    for s in sections:
        print("   %-16s %2d  %s" % (s["title"], len(s["items"]), s["sub"][:44]))


if __name__ == "__main__":
    main()
