#!/usr/bin/env python3
"""Generate properties/middle-earth.json.

    python tools/make_middle_earth.py

Three sections. Books: The Hobbit, The Lord of the Rings as three volume
rows, The Silmarillion, then the four posthumous narrative volumes as
optional rows — years and Christopher Tolkien credits from the Middle-earth
section of Wikipedia's J. R. R. Tolkien bibliography. Films: Peter
Jackson's six, weighted by theatrical runtime, each row noting its extended
edition factually — both figures from the film-series articles' own length
tables, theatrical cuts cross-checked against Wikidata P2047.

The animated films (CLU-200, raised in Discord): the three adaptations that
predate Jackson — Rankin/Bass's The Hobbit (1977), Ralph Bakshi's The Lord of
the Rings (1978) and Rankin/Bass's The Return of the King (1980). They are
OPTIONAL rows and a section of their own, for two reasons. They are a different
adaptation lineage from Jackson, made by two studios who were not making one
series; and this list is live with ticks on it, so the spine that "finishing the
list" means has to stay the books plus Jackson's six. Each row's runtime is that
film's own infobox figure, cross-checked against Wikidata P2047 to ±1 minute —
see parse_middle_earth.py for why the tolerance is not exact there.

⚠ Their ids are new and nothing else moved. They sit in a section appended after
Jackson's, not interleaved by year, because every existing row keeps its position
that way and the optional material stays at the bottom of the page where the
optional books already are.

Book rows are unweighted (pages aren't hours). The Rings of Power is not a
row; the notes say so. Data: tools/data/middle-earth.json, built and
asserted by scratch/agent-books/parse_middle_earth.py.

WHY 9 OF THE 15 ROWS CARRY NO NUMBER, written down rather than rediscovered.
All 9 are books — The Hobbit, the three Lord of the Rings volumes, The
Silmarillion and the four posthumous volumes. No source gives a book an
honest hour figure: page counts differ by edition and reading speeds differ
by reader, so every book list in this repo refuses the same way. The six
films ARE weighted, from theatrical runtimes cross-checked against Wikidata
P2047, and the third property note says the two scales are deliberate. An
unweighted row counts as one entry downstream, which is a floor rather than
a claim that The Silmarillion takes an hour. Dropping the film runtimes so
the whole list counts one-per-row — the raimi and x-files shape — would
also be defensible, and is the owner's call, not this file's.
"""
import json
import pathlib

SLUG = "middle-earth"

OPT_BOOKS = {"Unfinished Tales", "The Children of Húrin",
             "Beren and Lúthien", "The Fall of Gondolin"}
LOTR_VOLS = {"The Fellowship of the Ring": 1, "The Two Towers": 2,
             "The Return of the King": 3}


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
    d = json.loads((here / "data" / "middle-earth.json")
                   .read_text(encoding="utf-8"))
    books, films, animated = d["books"], d["films"], d["animated"]
    assert len(books) == 9 and len(films) == 6 and len(animated) == 3

    book_items = []
    for b in books:
        it = {"id": "me-%d-%s" % (b["year"], slugify(b["title"])),
              "t": b["title"], "n": str(b["year"])}
        bits = []
        if b["title"] in LOTR_VOLS:
            bits.append("The Lord of the Rings, volume %d"
                        % LOTR_VOLS[b["title"]])
        if b["christopher"]:
            bits.append("edited by Christopher Tolkien")
        if b["title"] in OPT_BOOKS:
            it["opt"] = 1
        if bits:
            it["note"] = " · ".join(bits)
        book_items.append(it)

    film_items = []
    for f in films:
        film_items.append({
            "id": "me-f-%d-%s" % (f["year"], slugify(f["title"])),
            "t": f["title"], "n": str(f["year"]),
            "w": round(f["theatrical"] / 60.0, 2),
            "note": "%d min · extended edition %d min"
                    % (f["theatrical"], f["extended"])})

    # Same `me-f-` prefix as Jackson's rows, because these are film rows on this
    # list and a second convention is one more thing to get wrong later. The
    # year is what separates them, and it always will: 1977/1978/1980 against
    # 2001-2014, asserted disjoint in parse_middle_earth.py.
    animated_items = []
    for a in animated:
        bits = ["%d min" % a["runtime"], a["studio"]]
        if a["tv"]:
            bits.append("made for television")
        animated_items.append({
            "id": "me-f-%d-%s" % (a["year"], slugify(a["title"])),
            "t": a["title"], "n": str(a["year"]),
            "w": round(a["runtime"] / 60.0, 2),
            "opt": 1,
            "note": " · ".join(bits)})

    hours = sum(x["w"] for x in film_items)
    ahours = sum(x["w"] for x in animated_items)
    sections = [
        {"id": "books", "title": "The books",
         "sub": "1937–2018 · Tolkien on the page", "open": True,
         "intro": "The Hobbit, then The Lord of the Rings volume by "
                  "volume, then The Silmarillion. The four later volumes "
                  "Christopher Tolkien assembled from his father's papers "
                  "are optional rows — deep water, entered knowingly.",
         "items": book_items},
        {"id": "films", "title": "Jackson's six",
         "sub": "2001–2014 · about %.0f hours theatrical" % hours,
         "intro": "Weighted by theatrical runtime; every row notes its "
                  "extended edition. Watch either cut — the tick doesn't "
                  "ask which.",
         "items": film_items},
        {"id": "animated", "title": "The animated films",
         "sub": "1977–1980 · about %.0f hours" % ahours,
         "intro": "Three adaptations from before Jackson, by two studios "
                  "working separately: Rankin/Bass made The Hobbit for "
                  "television and The Return of the King as its sequel, and "
                  "Ralph Bakshi's film came between them. Optional rows — "
                  "finishing the list does not ask for these.",
         "items": animated_items},
    ]

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == 18 and len(set(ids)) == 18
    assert all(i == slugify(i) and i.isascii() for i in ids)
    opts = [x["t"] for x in book_items if x.get("opt")]
    assert set(opts) == OPT_BOOKS, opts
    # books carry no hours, films all do — see the docstring
    assert not any("w" in x for x in book_items), \
        "a book row grew an hour figure; there is no source for one"
    assert all("w" in x for x in film_items), "a film row lost its runtime"
    assert 17.0 < hours < 17.4, hours  # 557 + 474 = 1031 min
    # the animated three are weighted like the other film rows and optional
    # like the posthumous books; both halves are load-bearing, so both assert
    assert all("w" in x for x in animated_items), \
        "an animated row lost its runtime"
    assert all(x.get("opt") for x in animated_items), \
        "an animated row stopped being optional; that changes what finishing " \
        "this list means for everyone who already has progress on it"
    assert 5.1 < ahours < 5.2, ahours  # 78 + 133 + 98 = 309 min
    # Jackson's rows must not have moved: the six ids and their order are the
    # ticks people already have, and appending a section is the only change here
    assert [x["id"] for x in film_items] == [
        "me-f-2001-the-fellowship-of-the-ring",
        "me-f-2002-the-two-towers",
        "me-f-2003-the-return-of-the-king",
        "me-f-2012-the-hobbit-an-unexpected-journey",
        "me-f-2013-the-hobbit-the-desolation-of-smaug",
        "me-f-2014-the-hobbit-the-battle-of-the-five-armies",
    ], [x["id"] for x in film_items]

    prop = {
        "slug": SLUG,
        "title": "Middle-earth",
        "subtitle": "Tolkien's books and the films made from them",
        "kind": "books & films",
        "popularity": 85,
        "year": "1937–2014",
        "blurb": "The Hobbit to The Silmarillion with the posthumous "
                 "volumes optional, Peter Jackson's six films weighted by "
                 "runtime, and the three animated adaptations that came "
                 "before him as optional rows.",
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "read", "past": "done", "ing": "working through"},
        "accent": "#4A6B2A",
        "accentDark": "#E3C060",
        "tiers": False,
        "notes": [
            ["The Lord of the Rings is three rows.",
             "One per volume, 1954–55, so a winter spent inside The Two "
             "Towers still moves the bar. The Hobbit and The Silmarillion "
             "are one row each."],
            ["The posthumous four are optional.",
             "Unfinished Tales, The Children of Húrin, Beren and Lúthien "
             "and The Fall of Gondolin — all edited by Christopher Tolkien "
             "from his father's papers, all opt rows. The History of "
             "Middle-earth series is scholarship beyond even that, and is "
             "not here."],
            ["Films are weighted, books are not.",
             "Jackson's rows use theatrical runtimes from Wikipedia's own "
             "length tables — about 9 hours for The Lord of the Rings "
             "plus 8 for The Hobbit — and each row notes its extended "
             "edition. The animated rows carry the runtime on their own "
             "articles; none of the three has a second cut. Book rows count "
             "one each; pages aren't hours."],
            ["The animated films are their own lineage.",
             "Rankin/Bass made The Hobbit for American television in 1977 "
             "and The Return of the King in 1980 as its sequel. Ralph "
             "Bakshi's The Lord of the Rings came between them in 1978 and "
             "adapts the first two volumes, not the third. Two studios who "
             "were not making one series, then — but in that order the three "
             "of them reach the end of the story, twenty years before "
             "Jackson did. They are optional rows, so what finishing this "
             "list means is unchanged for anyone already part-way through."],
            ["No Rings of Power.",
             "Every screen row here adapts one of the books above. The "
             "Amazon series does not, and is left out on purpose."],
            "Books and years from Wikipedia's J. R. R. Tolkien "
            "bibliography; Jackson's film lengths from The Lord of the Rings "
            "and The Hobbit film-series articles, the animated films' from "
            "their own articles, all cross-checked against Wikidata.",
        ],
        "sections": sections,
    }

    out = here.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json — %d rows (%d books, %d Jackson films at %.1fh "
          "theatrical, %d animated at %.1fh)"
          % (SLUG, len(ids), len(book_items), len(film_items), hours,
             len(animated_items), ahours))
    for s in sections:
        print("   %-14s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
