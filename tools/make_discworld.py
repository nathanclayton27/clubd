#!/usr/bin/env python3
"""Generate properties/discworld.json.

    python tools/make_discworld.py

All 41 Discworld novels in publication order — the novels table of
Wikipedia's Discworld article, parsed into tools/data/discworld.json by
scratch/agent-books/parse_discworld.py and asserted against the lead's own
"forty-one books".

The point of the property is the Storyline filter: chips recreate the famous
reading-order diagram from the sub-series assignments Wikipedia records —
the Discworld Emporium's published reading-order guide (its Unseen
University strand is the Rincewind books; its Industrial revolution strand
is the chip of that name) and Transworld's five cover sub-series (the
Tiffany Aching chip). The Moist chip is the article's own Moist von Lipwig
storyline section, which names his three novels. Rows left unassigned by
all of that are Standalone. Every mapping is asserted by count, so a
Wikipedia edit breaks the build rather than silently reshuffling the chips.

The Science of Discworld books, short stories, mapps, diaries and other
side matter are not novels in the table and are excluded; the notes say so.
"""
import json
import pathlib

SLUG = "discworld"

ARC_RINCEWIND = "Rincewind"
ARC_WITCHES = "Witches"
ARC_DEATH = "Death"
ARC_WATCH = "Watch"
ARC_MOIST = "Moist"
ARC_INDUSTRIAL = "Industrial Revolution"
ARC_STANDALONE = "Standalone"
ARC_TIFFANY = "Tiffany Aching"
ARCS = [ARC_RINCEWIND, ARC_WITCHES, ARC_DEATH, ARC_WATCH, ARC_MOIST,
        ARC_INDUSTRIAL, ARC_STANDALONE, ARC_TIFFANY]

# how many novels each chip must catch — from the parsed table, hand-checked
EXPECT = {ARC_RINCEWIND: 8, ARC_WITCHES: 6, ARC_DEATH: 5, ARC_WATCH: 8,
          ARC_MOIST: 3, ARC_INDUSTRIAL: 5, ARC_STANDALONE: 4, ARC_TIFFANY: 5}

# terse factual row notes, each grounded in the parsed data or the article
NOTES = {
    "Pyramids": "The Emporium's Gods strand",
    "Small Gods": "The Emporium's Gods strand",
    "The Last Hero": "The one novel the Emporium's reading-order guide "
                     "leaves unassigned",
    "The Amazing Maurice and His Educated Rodents":
        "The Emporium files it with the younger-readers books",
    "The Shepherd's Crown": "Published posthumously",
}

DECADES = [
    ("d80s", "The '80s", 1983, 1989,
     "Eight novels in seven years — the wizards, the witches, Death and "
     "the Watch all get their opening books."),
    ("d90s", "The '90s", 1990, 1999,
     "The peak run: sixteen novels, every strand advancing at once."),
    ("d00s", "The 2000s", 2000, 2009,
     "The Industrial Revolution books arrive, and Tiffany Aching begins."),
    ("d10s", "The 2010s", 2010, 2015, ""),
]


def slugify(t):
    # CLU-430. This fold DELETES a straight apostrophe (`The Emperor's Soul`
    # gives the-emperors-soul) and left U+2019 alone, so a curly one reached
    # the isalnum test below and became a dash instead. Two spellings of one
    # title would reach two ids, and an id is the `item_id` every tick and
    # thumb is stored against — moving one unticks the row for everyone
    # holding it. Drop both forms: that is the correction THIS direction
    # needs, and the opposite of what the folds that dash a straight
    # apostrophe need.
    t = t.replace("'", "").replace("’", "").replace("‘", "")
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    keep = keep.encode("ascii", "ignore").decode("ascii")
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def arcs_for(nv, moist):
    tags = []
    if nv["emporium"] == "Unseen University":
        tags.append(ARC_RINCEWIND)
    if nv["emporium"] == "Witches":
        tags.append(ARC_WITCHES)
    if nv["emporium"] == "Death":
        tags.append(ARC_DEATH)
    if nv["emporium"] == "City Watch":
        tags.append(ARC_WATCH)
    if nv["title"] in moist:
        tags.append(ARC_MOIST)
    if nv["emporium"] == "Industrial revolution":
        tags.append(ARC_INDUSTRIAL)
    if nv["transworld"] == "Tiffany Aching":
        tags.append(ARC_TIFFANY)
    if not tags:
        tags.append(ARC_STANDALONE)
    return tags


def main():
    here = pathlib.Path(__file__).resolve().parent
    data = json.loads((here / "data" / "discworld.json").read_text(encoding="utf-8"))
    novels, moist = data["novels"], set(data["moist"])
    assert len(novels) == 41, len(novels)
    assert [n["num"] for n in novels] == list(range(1, 42))

    used_notes = set()
    sections = []
    for sid, title, lo, hi, intro in DECADES:
        got = [nv for nv in novels if lo <= nv["year"] <= hi]
        assert got, sid
        items = []
        for nv in got:
            it = {"id": "dw-%d-%s" % (nv["num"], slugify(nv["title"])),
                  "t": nv["title"], "n": str(nv["year"]),
                  "tags": arcs_for(nv, moist)}
            if nv["title"] in NOTES:
                used_notes.add(nv["title"])
                it["note"] = NOTES[nv["title"]]
            items.append(it)
        sec = {"id": sid, "title": title,
               "sub": "%d–%d · novels %d–%d" % (got[0]["year"], got[-1]["year"],
                                                got[0]["num"], got[-1]["num"]),
               "items": items}
        if intro:
            sec["intro"] = intro
        if sid == "d80s":
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == 41 and len(set(ids)) == 41, "bad ids"
    assert all(i == slugify(i) and i.isascii() for i in ids)
    assert used_notes == set(NOTES), set(NOTES) - used_notes

    # every chip catches exactly the count hand-checked against the table
    from collections import Counter
    counts = Counter(t for s in sections for x in s["items"] for t in x["tags"])
    assert dict(counts) == EXPECT, (dict(counts), EXPECT)
    assert all(x["tags"] for s in sections for x in s["items"])
    # Moist rides inside Industrial Revolution, never alone
    for s in sections:
        for x in s["items"]:
            if ARC_MOIST in x["tags"]:
                assert ARC_INDUSTRIAL in x["tags"], x["id"]

    prop = {
        "slug": SLUG,
        "title": "Discworld",
        "subtitle": "Terry Pratchett — all 41 novels",
        "kind": "books",
        "popularity": 62,
        "year": "1983–2015",
        "blurb": "Every Discworld novel in publication order, The Colour of "
                 "Magic to The Shepherd's Crown, with the reading-order "
                 "diagram rebuilt as storyline chips — follow one strand or "
                 "read the whole Disc.",
        "unit": {"one": "book", "many": "books"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": "#356B58",
        "accentDark": "#B37DF0",
        "tiers": False,
        "filter": {"key": "arc", "label": "Storyline", "mode": "include",
                   "values": ARCS},
        "notes": [
            ["Publication order, one strand at a time if you like.",
             "The rows run 1–41 as published. The chips recreate the famous "
             "reading-order diagram: pick a storyline and the list shrinks "
             "to that strand."],
            ["Where the chips come from.",
             "The sub-series assignments Wikipedia records: the Discworld "
             "Emporium's reading-order guide supplies Witches, Death, the "
             "Watch and Industrial Revolution, and its Unseen University "
             "strand is the Rincewind chip; Tiffany Aching is Transworld's "
             "cover sub-series; Moist marks the three novels the article "
             "names as Moist von Lipwig's, inside Industrial Revolution. "
             "The four books none of that touches are Standalone."],
            ["Novels only.",
             "The Science of Discworld books, the short stories, the mapps, "
             "diaries and the rest of the side matter are not in the "
             "article's novels table and are not here."],
            ["Nothing is weighted.",
             "Every novel counts as one; Pratchett kept them close enough "
             "in size that pretending to know the hours would be worse."],
            "Titles, years and sub-series from Wikipedia's Discworld "
            "article — the novels table, verified against the lead's own "
            "count of forty-one.",
        ],
        "sections": sections,
    }

    out = here.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json — 41 novels" % SLUG)
    for s in sections:
        print("   %-10s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))
    print("   chips:", dict(counts))


if __name__ == "__main__":
    main()
