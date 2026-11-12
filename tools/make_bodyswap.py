#!/usr/bin/env python3
"""Generate properties/body-swap.json — the body-swap films.

    python tools/make_bodyswap.py

Every film row of Wikipedia's "Body swap appearances in media" that links an
English Wikipedia article, by decade: who swaps and how ride on the note, the
way the source table gives them. Unweighted grab bag — runtimes sit in the
notes (Wikidata P2047) — pick anything, any order.

Data: tools/data/body-swap.json via scratch/agent-canons/collect_bodyswap.py.
"""
import json
import pathlib
import re
import unicodedata

SLUG = "body-swap"
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = pathlib.Path(__file__).resolve().parent / "data" / ("%s.json" % SLUG)
OUT = ROOT / "properties" / ("%s.json" % SLUG)

ERAS = [
    ("early", "Before Freaky Friday", None, 1975,
     "The premise is older than the name for it — a mad-science brain swap "
     "from 1936, wishes and statues after that."),
    ("seventies", "The '70s and '80s", 1976, 1989,
     "Freaky Friday lands in 1976 and the late-'80s wave — Vice Versa, 18 "
     "Again!, Dream a Little Dream — chases it."),
    ("nineties", "The '90s", 1990, 1999, ""),
    ("aughts", "The 2000s", 2000, 2009, ""),
    ("tens", "The 2010s", 2010, 2019, ""),
    ("twenties", "The 2020s", 2020, None, ""),
]


def slug(t):
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def scrub(t):
    """Source cells can carry <br /> separators and '' italics."""
    t = re.sub(r"<br\s*/?>", ", ", t or "")
    t = t.replace("''", "")
    return re.sub(r"\s+", " ", t).strip()


# Who swaps, overridden where the source's cell gives too much away. Keyed on
# (title, year), with the cell the ruling was made against: if the source stops
# saying that, the assert stops the run so somebody re-reads it.
#   The Substance (2024): "Elisabeth Sparkle and Sue" gives away that a second
#   self exists, and for a film whose turn IS the premise that is a spoiler -
#   Nathan, CLU-123: "just make sure to do your best to make it so a premise
#   note is obviously not a crazy spoiler for something recommended to go in
#   blind". Commit 4ef1b1d cut it on the property file; CLU-557 moved the
#   ruling here so a rebuild cannot undo it.
CHARACTERS = {
    ("The Substance", 2024): ("Elisabeth Sparkle and Sue", "Elisabeth Sparkle"),
}


def note_for(f):
    bits = []
    country = scrub(f["country"])
    if country and country != "United States":
        bits.append(country)
    ch = scrub(f["characters"]).rstrip(".")
    if (f["t"], f["year"]) in CHARACTERS:
        was, now = CHARACTERS[(f["t"], f["year"])]
        assert ch == was, \
            "%s (%d): the source's characters cell now reads %r, not the " \
            "%r the override was ruled on - re-read it" \
            % (f["t"], f["year"], ch, was)
        ch = now
    if ch and len(ch) <= 55:
        bits.append(ch)
    me = scrub(f["method"]).split(". ")[0].rstrip(".")
    if me and len(me) <= 55:
        bits.append(me[0].lower() + me[1:] if ch else me)
    if f.get("runtime"):
        bits.append("%d min" % f["runtime"])
    return " · ".join(bits)


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    films = d["films"]
    assert all("runtime" in f for f in films), \
        "run collect_bodyswap.py --runtimes first"
    missing = set(CHARACTERS) - {(f["t"], f["year"]) for f in films}
    assert not missing, \
        "CHARACTERS overrides a film the source no longer lists: %s" \
        % sorted(missing)

    sections = []
    for key, title, lo, hi, intro in ERAS:
        got = [f for f in films
               if (lo is None or f["year"] >= lo)
               and (hi is None or f["year"] <= hi)]
        assert got, key
        got.sort(key=lambda f: (f["year"], f["t"]))
        items = []
        seen = set()
        for f in got:
            i = "bsw-%d-%s" % (f["year"], slug(f["t"]))
            assert i not in seen, i
            seen.add(i)
            note = note_for(f)
            items.append({"id": i, "t": f["t"], "n": str(f["year"]),
                          **({"note": note} if note else {})})
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
    assert len(ids) == len(set(ids)), \
        "duplicate ids: %s" % sorted({i for i in ids if ids.count(i) > 1})[:6]
    assert len(ids) == len(films)
    norun = sum(1 for f in films if not f.get("runtime"))

    prop = {
        "slug": SLUG,
        "title": "Body Swap",
        "subtitle": "who's in whose body, by decade",
        "kind": "films",
        "popularity": 34,
        "year": "1936–2026",
        "blurb": "%d body-swap films from Wikipedia's own list — four Freaky "
                 "Fridays included — with who swaps and how on every note. "
                 "Watch in any order." % len(films),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": "#0F7A78",
        "accentDark": "#F2913D",
        "tiers": False,
        "random": True,
        "notes": [
            ["No order, no weights.",
             "A grab bag, not a schedule — the Random button is the intended "
             "interface. Runtimes ride on the notes where Wikidata has one"
             + ("; %d rows have none on record." % norun if norun else "."),
             ],
            ["Every row has an article.",
             "The source list carries dozens more films that only exist on "
             "other-language Wikipedias; rows here are the ones an English "
             "article verifies — title, year, who swaps, and how. Big and "
             "Face/Off aren't on Wikipedia's list (an age-up and a face "
             "transplant are not swaps), so they aren't here either."],
            "From the Films table of Wikipedia's \"Body swap appearances in "
            "media\"; runtimes from Wikidata.",
        ],
        "sections": sections,
    }

    with OUT.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")
    print("wrote %s.json — %d films" % (SLUG, len(films)))
    for s in sections:
        print("   %-24s %2d  %s" % (s["title"], len(s["items"]), s["sub"][:44]))


if __name__ == "__main__":
    main()
