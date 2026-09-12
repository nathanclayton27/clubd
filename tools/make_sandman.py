#!/usr/bin/env python3
"""Generate properties/sandman.json.

    python tools/make_sandman.py

One row per issue: The Sandman #1–75 plus The Sandman Special #1, sectioned
by collected volume — Preludes & Nocturnes through The Wake, boundaries
from the trade list of Wikipedia's The Sandman article, story titles from
each volume article's own issues table. Fables & Reflections keeps its
book's deliberately shuffled order. Then the two Death miniseries and
Overture, each its own section.

Links live on section headers only (each header links its volume's
Wikipedia article); no row carries a url. Data: tools/data/sandman.json,
built and asserted by scratch/agent-books/parse_sandman.py.
"""
import json
import pathlib
import re

SLUG = "sandman"
WP = "https://en.wikipedia.org/wiki/"

SECTION_IDS = {
    "Preludes and Nocturnes": "preludes",
    "The Doll's House": "dolls-house",
    "Dream Country": "dream-country",
    "Season of Mists": "season-of-mists",
    "A Game of You": "game-of-you",
    "Fables and Reflections": "fables",
    "Brief Lives": "brief-lives",
    "Worlds' End": "worlds-end",
    "The Kindly Ones": "kindly-ones",
    "The Wake": "wake",
}

INTROS = {
    "Preludes and Nocturnes": "Dream is captured, escapes, and reclaims his "
                              "tools. #8 is where most people fall in love "
                              "with the series.",
    "Fables and Reflections": "Short stories gathered from across the run — "
                              "the book shuffles publication order on "
                              "purpose, and the rows here follow the book. "
                              "Also collects Fear of Falling, a brief piece "
                              "from Vertigo Preview #1.",
    "The Kindly Ones": "The longest Sandman story. The collection also "
                       "carries The Castle, a short from Vertigo Jam #1.",
    "The Wake": "The series ends; Gaiman stopped it on purpose at #75.",
}

EXTRA_NOTES = {
    8: "Death's debut",
    19: "won the World Fantasy Award",
}


def link(page):
    return [{"label": "The volume", "url": WP + page.replace(" ", "_")}]


def main():
    here = pathlib.Path(__file__).resolve().parent
    d = json.loads((here / "data" / "sandman.json").read_text(encoding="utf-8"))

    kindly_fixed = 0
    sections = []
    for v in d["volumes"]:
        items = []
        for iss in v["issues"]:
            title = iss["title"]
            m = re.match(r"The Kindly Ones - (\d+)$", title)
            if m:
                title = "The Kindly Ones, part %s" % m.group(1)
                kindly_fixed += 1
            if iss["n"] == "special":
                it = {"id": "sand-special", "t": "The Sandman Special",
                      "n": "#1", "note": title}
            else:
                note = title
                if iss["n"] in EXTRA_NOTES:
                    note += " · " + EXTRA_NOTES[iss["n"]]
                it = {"id": "sand-%d" % iss["n"], "t": "The Sandman",
                      "n": "#%d" % iss["n"], "note": note}
                if iss["n"] == 19:
                    it["star"] = 1
            items.append(it)
        short = v["label"].replace("Fables and Reflections",
                                   "Fables & Reflections")
        spec = ", ".join(
            ("#%d" % i["n"]) if isinstance(i["n"], int) else "Special #1"
            for i in v["issues"])
        sec = {"id": SECTION_IDS[v["label"]], "title": short,
               "sub": "The Sandman %s · %s"
                      % (compress(spec), v["years"]),
               "links": link(v["page"]),
               "items": items}
        if v["label"] in INTROS:
            sec["intro"] = INTROS[v["label"]]
        if v["label"] == "Preludes and Nocturnes":
            sec["open"] = True
        sections.append(sec)
    assert kindly_fixed == 13, kindly_fixed

    for m_, key, years, months in [
            (d["death"][0], "hcol", "1993", "March–May 1993"),
            (d["death"][1], "toyl", "1996", "April–July 1996")]:
        assert m_["issues"] == 3 and m_["years"] == years
        sections.append({
            "id": "death-" + key, "title": m_["title"],
            "sub": "3 issues · %s" % months,
            "links": link(m_["page"]),
            "items": [{"id": "sand-%s-%d" % (key, n), "t": m_["title"],
                       "n": "#%d" % n} for n in (1, 2, 3)]})
    sections[-2]["intro"] = ("The first Sandman spin-off miniseries — "
                             "Death takes human form for a day.")

    ov = d["overture"]
    assert ov["issues"] == 6
    sections.append({
        "id": "overture", "title": "The Sandman: Overture",
        "sub": "6 issues · 2013–15",
        "intro": "The prequel, twenty-five years on — it recounts the "
                 "events leading into #1, and won the 2016 Hugo for Best "
                 "Graphic Story. Publication order puts it here; reading "
                 "it first works too.",
        "links": link(ov["page"]),
        "items": [{"id": "sand-ov-%d" % n, "t": "The Sandman: Overture",
                   "n": "#%d" % n} for n in range(1, 7)]})

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == 88 and len(set(ids)) == 88, len(ids)
    nums = sorted(int(i[5:]) for i in ids
                  if re.match(r"sand-\d+$", i))
    assert nums == list(range(1, 76)), "main run has gaps"
    assert not any("url" in x for s in sections for x in s["items"])
    assert all(s.get("links") for s in sections)

    prop = {
        "slug": SLUG,
        "title": "The Sandman",
        "subtitle": "Neil Gaiman — every issue, plus Death and Overture",
        "kind": "comics",
        "popularity": 70,
        "year": "1988–2015",
        "blurb": "All 75 issues and the Special, one row each, sectioned by "
                 "collected volume — then the two Death miniseries and the "
                 "Overture prequel. 88 issues of the Dreaming.",
        "unit": {"one": "issue", "many": "issues"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": "#1F1D2B",
        "accentDark": "#C9C9D9",
        "tiers": False,
        "notes": [
            ["Sections are the ten trades.",
             "Issue ranges come from Wikipedia's own collected-editions "
             "list, and every row carries its story title from the "
             "volume's issue table. Read volume by volume and the strip "
             "matches your shelf."],
            ["Fables & Reflections is out of sequence on purpose.",
             "It gathers #29–31, #38–40, #50 and the Sandman Special from "
             "across the run, shuffled into the book's own order — the "
             "rows follow the book, not the numbering. The tiny Vertigo "
             "Preview and Vertigo Jam pieces ride inside their volumes' "
             "ticks rather than getting rows."],
            ["After The Wake.",
             "The two Death miniseries are the closest spin-offs and sit "
             "here in publication order; Overture is the 2013–15 prequel "
             "and closes the list. Reading Overture first is a defensible "
             "heresy the checkboxes won't fight you over."],
            ["Not here.",
             "Endless Nights, The Dream Hunters, the other spin-offs and "
             "the Netflix series are beyond this list's scope."],
            "Volume boundaries and years from Wikipedia's The Sandman "
            "article; story titles from each volume's own article.",
        ],
        "sections": sections,
    }

    # CLU-555. A MARK'S WIDTH IS ISSUES. Every row on this list is exactly
    # one issue, so every row weighs one. That asserts nothing the page did
    # not already claim -- its row count and its issue count are the same
    # number -- it only makes the claim machine-readable, which is what lets
    # the DC Comics shelf draw this door as wide as the run behind it instead
    # of as one equal mark among eight.
    #
    # Stamped in one place rather than on every row constructor: one loop, one
    # reason. All or nothing, because build.py totals a weight only when EVERY
    # row carries one, and a hub cannot mix measured doors with unmeasured
    # ones. `opt` rows are weighted too: optional is about what completion
    # requires, not about how wide a mark is drawn.
    for _s in sections:
        for _x in _s["items"]:
            _x["w"] = 1
    assert all(_x.get("w") == 1 for _s in sections for _x in _s["items"]), \
        "a row escaped the weight stamp"

    out = here.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json — %d issues in %d sections" % (SLUG, len(ids),
                                                        len(sections)))
    for s in sections:
        print("   %-28s %2d  %s" % (s["title"][:28], len(s["items"]),
                                    s["sub"][:44]))


def compress(spec):
    """'#1, #2, #3' -> '#1–3'; keeps non-contiguous lists readable."""
    nums, tail = [], []
    for part in spec.split(", "):
        if part.startswith("#") and part[1:].isdigit():
            nums.append(int(part[1:]))
        else:
            tail.append(part)
    runs, start, prev = [], None, None
    for n in sorted(nums):
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            runs.append((start, prev))
            start = prev = n
    if start is not None:
        runs.append((start, prev))
    bits = ["#%d–%d" % r if r[0] != r[1] else "#%d" % r[0] for r in runs]
    return ", ".join(bits + tail)


if __name__ == "__main__":
    main()
