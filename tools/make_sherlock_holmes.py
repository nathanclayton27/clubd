#!/usr/bin/env python3
"""Generate properties/sherlock-holmes.json.

    python tools/make_sherlock_holmes.py

The complete canon — 4 novels and 56 short stories, one row each, exactly
as Wikipedia's "Canon of Sherlock Holmes" article lists them. Nine sections
in publication order: each novel is its own section, each collection holds
its stories in collection order with first-publication years as n. The
Cardboard Box sits in The Memoirs here because that is where the article
puts it; its row and the His Last Bow intro note the other arrangement,
which the article itself documents.

Section headers link to each book's Wikipedia article (links live on
headers, never rows — house rule). Data: tools/data/sherlock-holmes.json,
built and asserted by scratch/agent-books/parse_sherlock.py against the
canon's own "56 short stories and four novels".
"""
import json
import pathlib

SLUG = "sherlock-holmes"
WP = "https://en.wikipedia.org/wiki/"

# (data index or collection title, section id, sub, intro)
NOVEL_META = {
    "A Study in Scarlet": ("study", "the first novel",
                           "Holmes and Watson meet."),
    "The Sign of the Four": ("sign", "the second novel", ""),
    "The Hound of the Baskervilles":
        ("hound", "the third novel, serialized across two years", ""),
    "The Valley of Fear":
        ("valley", "the fourth novel, serialized across two years", ""),
}
COLL_META = {
    "The Adventures of Sherlock Holmes":
        ("adventures", "12 stories · The Strand, July 1891 – June 1892",
         "The first dozen, with the Paget illustrations that fixed how "
         "Holmes looks."),
    "The Memoirs of Sherlock Holmes":
        ("memoirs", "12 stories · The Strand, December 1892 – December 1893",
         ""),
    "The Return of Sherlock Holmes":
        ("return", "13 stories · The Strand, October 1903 – December 1904",
         ""),
    "His Last Bow":
        ("lastbow", "7 stories · 1908–1917",
         "Many editions carry eight stories here, adding The Cardboard Box "
         "from The Memoirs."),
    "The Case-Book of Sherlock Holmes":
        ("casebook", "12 stories · 1921–1927", "The final collection."),
}

STORY_NOTES = {
    "The Adventure of the Cardboard Box":
        "Doyle later collected it in His Last Bow instead — many editions "
        "follow him",
    "The Adventure of the Final Problem": "The Reichenbach story",
    "The Adventure of the Empty House": "Holmes returns",
    "His Last Bow. The War Service of Sherlock Holmes":
        "The title story",
}


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


def short_years(y):
    """'1901–1902' -> '1901–02'; plain years pass through."""
    if "–" in y:
        a, b = y.split("–")
        return "%s–%s" % (a, b[2:])
    return y


def main():
    here = pathlib.Path(__file__).resolve().parent
    d = json.loads((here / "data" / "sherlock-holmes.json")
                   .read_text(encoding="utf-8"))
    novels = {n["title"]: n for n in d["novels"]}
    colls = {c["title"]: c for c in d["collections"]}

    def novel_section(title, opened=False):
        sid, sub, intro = NOVEL_META[title]
        nv = novels[title]
        sec = {"id": sid, "title": title,
               "sub": "%s · %s" % (short_years(nv["years"]), sub),
               "links": [{"label": "The novel",
                          "url": WP + nv["page"].replace(" ", "_")}],
               "items": [{"id": "sh-%s-%s" % (nv["years"][:4], slugify(title)),
                          "t": title, "n": short_years(nv["years"])}]}
        if intro:
            sec["intro"] = intro
        if opened:
            sec["open"] = True
        return sec

    def coll_section(title):
        sid, sub, intro = COLL_META[title]
        c = colls[title]
        items = []
        for s in c["stories"]:
            disp = ("His Last Bow" if s["title"].startswith("His Last Bow.")
                    else s["title"])
            it = {"id": "sh-%d-%s" % (s["year"], slugify(disp)),
                  "t": disp, "n": str(s["year"])}
            if s["title"] in STORY_NOTES:
                it["note"] = STORY_NOTES[s["title"]]
            items.append(it)
        sec = {"id": sid, "title": "%s (%d)" % (title, c["year"]),
               "sub": sub,
               "links": [{"label": "The collection",
                          "url": WP + title.replace(" ", "_")}],
               "items": items}
        if intro:
            sec["intro"] = intro
        return sec

    sections = [
        novel_section("A Study in Scarlet", opened=True),
        novel_section("The Sign of the Four"),
        coll_section("The Adventures of Sherlock Holmes"),
        coll_section("The Memoirs of Sherlock Holmes"),
        novel_section("The Hound of the Baskervilles"),
        coll_section("The Return of Sherlock Holmes"),
        novel_section("The Valley of Fear"),
        coll_section("His Last Bow"),
        coll_section("The Case-Book of Sherlock Holmes"),
    ]

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == 60 and len(set(ids)) == 60, len(ids)
    assert all(i == slugify(i) and i.isascii() for i in ids)
    noted = {x["t"] for s in sections for x in s["items"] if "note" in x}
    assert len(noted) == len(STORY_NOTES), noted
    # no row carries a url — links live on the section headers only
    assert not any("url" in x for s in sections for x in s["items"])
    assert all(s.get("links") for s in sections)

    prop = {
        "slug": SLUG,
        "title": "Sherlock Holmes",
        "subtitle": "the complete canon — 60 adventures",
        "kind": "books",
        "popularity": 76,
        "year": "1887–1927",
        "blurb": "All four novels and all 56 short stories in publication "
                 "order, sectioned by collection — A Study in Scarlet to "
                 "the Case-Book, forty years of Baker Street.",
        "unit": {"one": "story", "many": "stories"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": "#7A5220",
        "accentDark": "#DFA75E",
        "tiers": False,
        "notes": [
            ["One row per story, one per novel.",
             "Sixty rows — what Sherlockians call the 60 adventures. The "
             "number on each story is its first magazine publication year; "
             "sections are the books, in the order the books appeared."],
            ["The Cardboard Box moves around.",
             "It ran in The Strand in 1893 with the Memoirs stories, and "
             "Doyle later collected it only in His Last Bow — so many "
             "editions have an 11-story Memoirs and an 8-story His Last "
             "Bow. It sits in The Memoirs here, where Wikipedia's canon "
             "list puts it; tick it wherever your edition keeps it."],
            ["Canon only.",
             "The extracanonical Doyle pieces — The Field Bazaar, How "
             "Watson Learned the Trick, the stage plays and essays — are "
             "outside the 60 and not rowed."],
            ["Nothing is weighted.",
             "A novel and a twelve-page story each count as one; the "
             "counter tracks adventures, not hours."],
            "Titles, years and collection boundaries from Wikipedia's "
            "Canon of Sherlock Holmes article, verified against its own "
            "count of 56 stories and four novels.",
        ],
        "sections": sections,
    }

    out = here.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json — %d rows in %d sections" % (SLUG, len(ids),
                                                      len(sections)))
    for s in sections:
        print("   %-44s %2d  %s" % (s["title"][:44], len(s["items"]),
                                    s["sub"][:40]))


if __name__ == "__main__":
    main()
