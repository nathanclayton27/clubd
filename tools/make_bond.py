#!/usr/bin/env python3
"""Generate properties/bond.json.

    python3 tools/make_bond.py

Every James Bond film in release order — the 25 Eon productions in sections
per Bond actor, plus the two films made outside Eon (the 1967 Casino Royale
spoof and Never Say Never Again) slotted into the era their year falls in and
marked "Not Eon".

Tier 1 is the continuity: the five Craig films are genuinely serialized, and
On Her Majesty's Secret Service joins them because its ending echoes forward.
Every other Eon film stands alone as tier 2; the two non-Eon films are tier 3
and sit outside the pace line.

Titles, years and Bond actors come from Wikipedia's List of James Bond films;
runtimes and release dates come from Wikidata (P2047, P577), harvested by
scratch/bond/build.py into tools/data/bond.json.
"""
import json
import pathlib
import unicodedata

SLUG = "bond"

# Eon film count per actor is a fact of the list; pin it so a bad harvest
# fails here instead of shipping a wrong section.
ACTORS = [
    ("connery", "Sean Connery", 6),
    ("lazenby", "George Lazenby", 1),
    ("moore", "Roger Moore", 7),
    ("dalton", "Timothy Dalton", 2),
    ("brosnan", "Pierce Brosnan", 4),
    ("craig", "Daniel Craig", 5),
]

# Tier 1 = the films with real continuity weight: the Craig arc, and the one
# Lazenby film, whose ending the arc eventually answers.
TIER1_ACTORS = {"Daniel Craig", "George Lazenby"}

INTRO = {
    "connery": "Where it starts. Six Connery films — and, in the middle of "
               "them, the 1967 spoof made outside Eon.",
    "lazenby": "One film. It carries more continuity weight than any other "
               "pre-Craig entry — the only one of them in tier 1.",
    "craig": "The serialized era: five films telling one continuous story. "
             "The only stretch where the order is not optional.",
}

NOTE = {
    "bond-1967-casino-royale":
        "Not Eon — the 1967 spoof, with David Niven as Bond",
    "bond-1983-never-say-never-again":
        "Not Eon — Connery's return, in a rival remake of Thunderball",
    "bond-1969-on-her-majesty-s-secret-service":
        "Lazenby's only outing — its ending echoes forward",
}


# Curly punctuation, straightened to the ASCII this fold already handles.
# CLU-430: `encode("ascii", "ignore")` DROPS a curly apostrophe and keeps a
# straight one as a dash, so `Child’s Play` folds to `childs-play` while
# `Child's Play` folds to `child-s-play`. An id is somebody’s tick, so two
# spellings of one title must never reach two ids. Straightening is the
# correction THIS direction needs — the opposite of the folds that drop the
# straight form — and it leaves every id this list has shipped where it is.
STRAIGHTEN = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'})


def slug(t):
    t = unicodedata.normalize("NFKD", t.translate(STRAIGHTEN))
    t = t.encode("ascii", "ignore").decode()
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def main():
    data = pathlib.Path(__file__).resolve().parent / "data"
    films = json.loads((data / "bond.json").read_text(encoding="utf-8"))
    films.sort(key=lambda f: (f["released"], f["title"]))
    assert all(f["runtime"] for f in films), \
        [f["title"] for f in films if not f["runtime"]]

    # An actor's era spans his first to last Eon film; the two non-Eon films
    # slot into whichever era their year falls in, never by their own lead —
    # Never Say Never Again stars Connery but 1983 is the Moore era.
    span = {}
    for key, name, n in ACTORS:
        ys = [f["year"] for f in films if f["eon"] and f["actor"] == name]
        assert len(ys) == n, (name, len(ys), n)
        span[key] = (min(ys), max(ys))

    def era(f):
        if f["eon"]:
            return next(k for k, name, _ in ACTORS if name == f["actor"])
        got = [k for k, _, _ in ACTORS
               if span[k][0] <= f["year"] <= span[k][1]]
        assert len(got) == 1, (f["title"], got)
        return got[0]

    sections = []
    for key, name, _ in ACTORS:
        got = [f for f in films if era(f) == key]
        items = []
        for f in got:
            it = {
                "id": "bond-%d-%s" % (f["year"], slug(f["title"])),
                "t": f["title"], "n": str(f["year"]),
                "w": round(f["runtime"] / 60.0, 2),
                "tier": (3 if not f["eon"]
                         else 1 if f["actor"] in TIER1_ACTORS else 2),
            }
            if it["id"] in NOTE:
                it["note"] = NOTE[it["id"]]
            items.append(it)
        eon = [f for f in got if f["eon"]]
        lo, hi = got[0]["year"], got[-1]["year"]
        years = "%d" % lo if lo == hi else "%d–%d" % (lo, hi)
        extra = "" if len(eon) == len(got) \
            else " + %d not Eon" % (len(got) - len(eon))
        sec = {"id": key, "title": name,
               "sub": "%s · %d film%s%s · %d hours"
                      % (years, len(eon), "" if len(eon) == 1 else "s", extra,
                         round(sum(f["runtime"] for f in got) / 60.0)),
               "items": items}
        if key in INTRO:
            sec["intro"] = INTRO[key]
        if key == "connery":
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(films) == 27, (len(ids), len(films))
    tiers = [x["tier"] for s in sections for x in s["items"]]
    assert (tiers.count(1), tiers.count(2), tiers.count(3)) == (6, 19, 2), tiers
    order = {f2["id"]: i for i, f2 in enumerate(
        {"id": "bond-%d-%s" % (f["year"], slug(f["title"]))} for f in films)}
    for s in sections:
        ii = [order[x["id"]] for x in s["items"]]
        assert ii == sorted(ii), "%s is out of release order" % s["title"]

    eonf = [f for f in films if f["eon"]]
    hours = sum(f["runtime"] for f in films) / 60.0
    ehours = sum(f["runtime"] for f in eonf) / 60.0

    prop = {
        "slug": SLUG,
        "title": "James Bond",
        "subtitle": "every Bond film in release order, in sections per actor",
        "kind": "films",
        "popularity": 88,
        # Not a story, so not a sequence: the order these came out in
        # is a fact about the maker, not an instruction to the viewer
        # (Nathan, CLU-372). Prerequisites, where any exist, live in
        # tools/data/sequences.json and are enforced separately.
        "random": True,
        "year": "%d–%d" % (films[0]["year"], films[-1]["year"]),
        "blurb": "All %d Eon films in release order, grouped by Bond actor, "
                 "plus the two oddities made outside Eon. The Craig arc is "
                 "the serialized spine." % len(eonf),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#1F1F2E",
        "accentDark": "#C9B458",
        "tiers": True,
        "itemTiers": True,
        "paceTiers": [1, 2],
        "paceLabel": "the non-Eon oddities",
        "notes": [
            ["Tier 1 is the continuity.", "The five Craig films are genuinely "
             "serialized — one continuous story — and On Her Majesty's Secret "
             "Service is tier 1 with them because its ending echoes forward. "
             "Every other Eon film stands alone as tier 2, watchable in any "
             "gaps you like. The two films made outside Eon are tier 3."],
            ["Two of the %d are not Eon films." % len(films), "A rights "
             "tangle kept Casino Royale out of Eon's hands for decades — the "
             "1967 film is a spoof with David Niven, and Never Say Never "
             "Again is a rival remake of Thunderball with Connery back in "
             "the role. Both are marked, sit in the era their year falls in, "
             "and stay outside the timeline unless you tick the box under "
             "the bar."],
            ["Bar widths are runtimes.", "Every one of the %d has a real "
             "runtime from Wikidata — the generator refuses to build without "
             "them." % len(films)],
            "Titles, years and Bond actors from Wikipedia's List of James "
            "Bond films; runtimes and release dates from Wikidata.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d films (%d Eon), %.1f hours (%.1f Eon)"
          % (len(films), len(eonf), hours, ehours))
    print("  tiers: %d / %d / %d" % (tiers.count(1), tiers.count(2), tiers.count(3)))
    for s in sections:
        print("   %-16s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
