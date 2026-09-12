#!/usr/bin/env python3
"""Generate properties/the-simpsons.json — seasons 1-10.

    python3 tools/make_the-simpsons.py

One row per episode, 226 rows. Where the list stops is deliberate and the
property note says why: nothing past "Thirty Minutes over Tokyo" is listed.
Treehouse of Horror episodes carry a small factual note.

CLU-186 moved the cutoff. It used to fall after season 8, on the conventional
golden-age line; Nathan asked for seasons 9 and 10 as well, on the grounds that
they are still good and the drop comes after them. Every per-season count below
is read off that season's own Wikipedia infobox rather than taken from the
ticket — 25 and 23 is what the articles say, and they are the authority.

Episode titles and airdates are machine-read from the ten Wikipedia
"The Simpsons season N" articles' {{Episode list}} rows by
scratch/agent-tv2/fetch_simpsons.py, which asserts each season's numbering
against the article's own infobox episode count; the committed result is
tools/data/the-simpsons.json. This script re-asserts the numbering before it
writes anything.

Nothing is weighted: an episode counts as one.
"""
import json
import pathlib
import re

SLUG = "the-simpsons"
EXPECT = {1: 13, 2: 22, 3: 24, 4: 22, 5: 22, 6: 25, 7: 25, 8: 25,
          9: 25, 10: 23}
TOTAL = 226
TREEHOUSES = 9  # one per season 2-10


def year_span(rows):
    ys = sorted({int(r["air"][:4]) for r in rows if r.get("air")})
    assert ys, "no airdates"
    if ys[0] == ys[-1]:
        return str(ys[0])
    a, b = ys[0], ys[-1]
    return "%d–%02d" % (a, b % 100) if a // 100 == b // 100 else "%d–%d" % (a, b)


def main():
    data = json.loads((pathlib.Path(__file__).resolve().parent / "data"
                       / "the-simpsons.json").read_text(encoding="utf-8"))

    for n, want in EXPECT.items():
        rows = data[str(n)]
        assert [r["e"] for r in rows] == list(range(1, want + 1)), \
            "season %d numbering incomplete" % n

    treehouses = 0

    def section(n):
        nonlocal treehouses
        items = []
        for r in data[str(n)]:
            row = {"id": "simp-s%d-%d" % (n, r["e"]), "t": r["t"],
                   "n": str(r["e"])}
            if r["t"].startswith("Treehouse of Horror"):
                row["note"] = "The annual Halloween anthology — three " \
                              "stand-alone segments"
                treehouses += 1
            items.append(row)
        rows = data[str(n)]
        return {"id": "s%d" % n, "title": "Season %d" % n,
                "sub": "%s · %d episodes" % (year_span(rows), len(rows)),
                "items": items}

    sections = [section(n) for n in range(1, len(EXPECT) + 1)]
    sections[0]["open"] = True
    assert treehouses == TREEHOUSES, treehouses

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert all(re.fullmatch(r"[a-z0-9-]+", i) for i in ids)
    assert len(ids) == TOTAL, len(ids)
    # A title carrying markup or an HTML entity is a shipped defect, and it
    # happened: season 10's "Marge Simpson in: 'Screaming Yellow Honkers'" has
    # a trailing `&hairsp;` in the article's Title field, which the fetcher's
    # wikitext cleaner passed straight through. Caught here as well as there,
    # because the data file is the thing this reads and it can be hand-edited.
    for s in sections:
        for x in s["items"]:
            assert not re.search(r"&[A-Za-z]+;|&#\d+;|\{\{|\}\}|\[\[|\]\]|<",
                                 x["t"]), "markup in title: %r" % x["t"]

    prop = {
        "slug": SLUG,
        "title": "The Simpsons",
        "subtitle": "the golden age, and the two seasons after it",
        "kind": "tv",
        "popularity": 93,
        # generated rather than typed: this string was "1989–97" for as long as
        # the list stopped at season 8, and a hand-typed span is the same rot
        # source as a hand-typed episode count
        "year": year_span([r for n in EXPECT for r in data[str(n)]]),
        # No episode count in the blurb on purpose. The card prints a generated
        # total directly above it, and a typed one here disagreed with the rows
        # the moment the cutoff moved.
        "blurb": "Seasons 1 through 10, one row per episode. The golden age "
                 "runs to season 8; 9 and 10 are still good, and the list "
                 "stops after them.",
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#C2477E",
        "accentDark": "#F2C744",
        "tiers": False,
        "notes": [
            ["The cutoff is deliberate.", "The conventional golden-age line "
             "is drawn after season 8 — \"Homer's Enemy\" territory. Seasons "
             "9 and 10 sit past it and are here anyway: still pretty good, "
             "just not as good as what came before them. After season 10 is "
             "where the show really falls off, and that is where this list "
             "ends."],
            ["Treehouse of Horror counts one each.", "The Halloween "
             "anthologies are regular episodes of their seasons and sit in "
             "broadcast position, noted on the row."],
            "Episode titles and airdates machine-read from the ten "
            "Wikipedia season articles (The Simpsons season 1–10); each "
            "season's numbering is asserted against the article's own "
            "episode count before this builds.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json — %d episodes in %d sections (%d Treehouses noted)"
          % (SLUG, len(ids), len(sections), treehouses))
    for s in sections:
        print("   %-10s %3d  %s" % (s["title"], len(s["items"]),
                                    s.get("sub", "")))


if __name__ == "__main__":
    main()
