#!/usr/bin/env python3
"""Generate properties/wheel-of-time.json.

    python tools/make_wheel_of_time.py

The 14 Wheel of Time novels plus New Spring, in publication order — which is
the order Wikipedia's own novels table lists them, New Spring sitting in its
publication slot between Crossroads of Twilight and Knife of Dreams. Its row
notes the placement factually; the final three carry the Jordan-and-Sanderson
credit the table gives them. Data: tools/data/wheel-of-time.json, built and
asserted by scratch/agent-books/parse_wot.py.

Unweighted: the books famously vary in length, but page counts differ by
edition and pretending to know the hours would be worse.
"""
import json
import pathlib

SLUG = "wheel-of-time"

SECTIONS = [
    ("opening", "The opening run", 1990, 1994,
     "Six novels in five years — Jordan at full speed."),
    ("middle", "The long middle", 1996, 2005,
     "The pace slows and the story widens. New Spring, the prequel, "
     "arrives in the middle of it."),
    ("ending", "The ending", 2009, 2013,
     "Jordan died in 2007 leaving extensive notes; Brandon Sanderson "
     "completed the final volume as three books."),
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


def main():
    here = pathlib.Path(__file__).resolve().parent
    data = json.loads((here / "data" / "wheel-of-time.json")
                      .read_text(encoding="utf-8"))
    books = data["books"]
    assert len(books) == 15
    assert [b["date"] for b in books] == sorted(b["date"] for b in books)

    sections = []
    for sid, title, lo, hi, intro in SECTIONS:
        got = [b for b in books if lo <= b["year"] <= hi]
        assert got, sid
        items = []
        for b in got:
            it = {"id": "wot-%d-%s" % (b["year"], slugify(b["title"])),
                  "t": b["title"],
                  "n": str(b["year"])}
            if b["num"] == 0:
                it["note"] = ("The prequel novel — published here, between "
                              "books 10 and 11; some read it first instead")
            elif b["num"] >= 12:
                it["note"] = ("Book %d — Jordan and Sanderson" % b["num"])
            else:
                it["note"] = "Book %d" % b["num"]
            items.append(it)
        sec = {"id": sid, "title": title,
               "sub": "%d–%d · %d books" % (got[0]["year"], got[-1]["year"],
                                            len(got)),
               "intro": intro, "items": items}
        if sid == "opening":
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == 15 and len(set(ids)) == 15
    assert all(i == slugify(i) and i.isascii() for i in ids)
    ns = [x for s in sections for x in s["items"] if x["t"] == "New Spring"]
    assert len(ns) == 1 and "prequel" in ns[0]["note"]
    sand = [x for s in sections for x in s["items"]
            if "Sanderson" in x.get("note", "")]
    assert len(sand) == 3

    prop = {
        "slug": SLUG,
        "title": "The Wheel of Time",
        "subtitle": "Robert Jordan — 15 books, prequel included",
        "kind": "books",
        "popularity": 59,
        "year": "1990–2013",
        "blurb": "All fourteen novels plus New Spring in publication order, "
                 "The Eye of the World to A Memory of Light — the last "
                 "three completed by Brandon Sanderson from Jordan's notes.",
        "unit": {"one": "book", "many": "books"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": "#8C6A2F",
        "accentDark": "#E8D9A0",
        "tiers": False,
        "notes": [
            ["Publication order, New Spring where it landed.",
             "The prequel came out in January 2004, between Crossroads of "
             "Twilight and Knife of Dreams, and sits there — its row says "
             "so. Reading it first instead is a fine and common choice; "
             "the checkbox doesn't care when you tick it."],
            ["The last three are Jordan and Sanderson.",
             "Jordan died in 2007 while writing what was planned as the "
             "final volume, leaving extensive notes. Brandon Sanderson "
             "completed it as The Gathering Storm, Towers of Midnight and "
             "A Memory of Light; those rows carry the shared credit."],
            ["Novels only, nothing weighted.",
             "The companion books, the short fiction and the Amazon series "
             "are out of scope, and every book counts as one — the books "
             "vary hugely in length, but page counts differ by edition "
             "and faking hours would be worse."],
            "Titles, numbering, authors and dates from the novels table of "
            "Wikipedia's The Wheel of Time article.",
        ],
        "sections": sections,
    }

    out = here.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json — %d books" % (SLUG, len(ids)))
    for s in sections:
        print("   %-16s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
