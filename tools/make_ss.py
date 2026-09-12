#!/usr/bin/env python3
"""Generate properties/sight-and-sound.json — the 2022 critics' top 100.

    python tools/make_ss.py

The Sight and Sound Greatest Films of All Time, 2022 critics' poll, exactly
as the poll ranks it — 100 films, ties sharing a number and wearing the
poll's own "=" mark. Rank bands for sections, rank for n, runtimes for
weights. Random button on: it's a lifetime list, not a syllabus.

Data: tools/data/sight-and-sound.json via scratch/agent-canons/collect_ss.py
(BFI's own results page, top ten cross-checked against Wikipedia's article,
every film verified on Wikidata by year and director).

Rows also carry `q`, a Wikidata work id, wherever the id the collector resolved
could be PROVED to be this film (CLU-368). It is what lets a row pair across
lists that print the same work under a different title: this poll prints Ugetsu
Monogatari while both japanese-cinema and criterion print Ugetsu, so on
title+year — the only other key this list has — the film pairs with neither.
Renaming the row would fix that one film and move its id, which is what every
tick on it is stored against; an id fixes every title variant the list has and
moves nothing.
"""
import json
import pathlib
import re
import unicodedata

SLUG = "sight-and-sound"
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = pathlib.Path(__file__).resolve().parent / "data" / ("%s.json" % SLUG)
OUT = ROOT / "properties" / ("%s.json" % SLUG)

# BFI's own results page prints one title with a double space where the colon
# belongs, and the collector reads it faithfully, so the error arrives from the
# source rather than from the read (CLU-431). It is the only title affected:
# 2001: A Space Odyssey keeps its colon through the same pipeline, so nothing in
# the chain strips punctuation. Corrected here rather than in the collected data
# so that a re-collection from a page that still has the typo cannot quietly
# bring it back.
#
# A colon folds to the same "-" the double space folded to, so the row id does
# not move: ss-1927-sunrise-a-song-of-two-humans, which is where every tick on
# this row is stored.
TITLE_FIX = {
    "Sunrise  A Song of Two Humans": "Sunrise: A Song of Two Humans",
}

# A work id the gate refused. The row ships without one, exactly as every row
# here did before ids existed — a wrong id is worse than none, because it would
# tick a film nobody watched on every list that carries the real work.
NO_Q = {
    # The collector resolved this one by title search and landed on Godard's
    # King Lear (1987): a different film by the same director, close enough in
    # year to pass its year gate. The row's printed year and its runtime bar are
    # read off that same wrong entity, which is a defect of its own (CLU-541);
    # this only keeps the wrong id out of the sync map.
    "Histoire(s) du Cinéma": "Q2707428 is King Lear (1987), another film",
}

BANDS = [
    ("top", "1–10", 1, 10,
     "Jeanne Dielman unseated Vertigo in 2022 — the first film by a woman "
     "to top the poll in its seventy years."),
    ("b11", "11–25", 11, 25, ""),
    ("b26", "26–50", 26, 50, ""),
    ("b51", "51–100", 51, 100, ""),
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
    assert len(films) == 100, len(films)

    fix = dict(TITLE_FIX)
    for f in films:
        if f["t"] in fix:
            f["t"] = fix.pop(f["t"])
    assert not fix, "TITLE_FIX no longer matches the data: %s" % sorted(fix)
    refused = dict(NO_Q)

    sections = []
    for key, title, lo, hi, intro in BANDS:
        got = [f for f in films if lo <= f["rank"] <= hi]
        assert got, key
        got.sort(key=lambda f: (f["rank"], f["t"]))
        items = []
        for f in got:
            year = f.get("wd_year") or f["year"]
            note = "%s, %d" % (f["director"], year)
            it = {"id": "ss-%d-%s" % (year, slug(f["t"])),
                  "t": f["t"],
                  "n": ("=%d" % f["rank"]) if f["tie"] else "#%d" % f["rank"],
                  "w": round((f["min"] or 0) / 60.0, 2),
                  "note": note}
            if f.get("qid") and f["t"] not in NO_Q:
                it["q"] = f["qid"]
            refused.pop(f["t"], None)
            if not f["min"]:
                it["note"] += " · no runtime on record — weighs nothing"
            items.append(it)
        hours = sum(x["w"] for x in items)
        sec = {"id": key, "title": title,
               "sub": "%d films · %d hours" % (len(got), round(hours)),
               "items": items}
        if intro:
            sec["intro"] = intro
        if key == "top":
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), \
        "duplicate ids: %s" % sorted({i for i in ids if ids.count(i) > 1})[:6]
    assert len(ids) == 100
    assert not refused, \
        "NO_Q names rows this poll does not have: %s" % sorted(refused)
    # Two rows sharing a work id would tie two ranks of this same list together
    # in the sync map: tick one and the other ticks with it.
    qs = [x["q"] for s in sections for x in s["items"] if x.get("q")]
    assert len(qs) == len(set(qs)), \
        "two rows share a work id: %s" % sorted({q for q in qs
                                                 if qs.count(q) > 1})
    assert all(re.fullmatch(r"Q[1-9]\d*", q) for q in qs), \
        "malformed work id"
    assert len(qs) == 100 - len(NO_Q), (len(qs), len(NO_Q))
    hours = sum(x["w"] for s in sections for x in s["items"])
    ties = sorted({f["rank"] for f in films if f["tie"]})

    prop = {
        "slug": SLUG,
        "title": "Sight & Sound 100",
        "subtitle": "the 2022 critics' poll, as ranked",
        "kind": "films",
        "popularity": 50,
        "year": "%d–%d" % (min(f.get("wd_year") or f["year"] for f in films),
                           max(f.get("wd_year") or f["year"] for f in films)),
        "blurb": "The 100 greatest films of all time per Sight and Sound's "
                 "2022 critics' poll — about %d hours, ties and all. Watch "
                 "in any order; the ranks are the argument." % round(hours),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": "#33383D",
        "accentDark": "#E2554A",
        "tiers": False,
        "random": True,
        "notes": [
            ["Ties share a number, exactly as the poll prints them.",
             "An = on a rank means the poll's own tie — %d positions are "
             "shared, which is why some numbers never appear. Still 100 "
             "films." % len(ties)],
            ["Bar widths are runtimes.",
             "From Wikidata, with each film's own Wikipedia article filling "
             "the gaps — which is how the longest entry here keeps its full "
             "%d minutes instead of being capped."
             % max(f["min"] or 0 for f in films)],
            ["Where the list comes from.",
             "The ranked list is read from the BFI's own results page — the "
             "reference Wikipedia's record of the poll points to, since the "
             "encyclopedia's article keeps only the top ten. That top ten "
             "is cross-checked against the article, and every film on the "
             "hundred is verified against Wikidata by year and director "
             "before it gets a row."],
            "The 2022 Sight and Sound critics' poll, via bfi.org.uk; "
            "runtimes from Wikidata and Wikipedia.",
        ],
        "sections": sections,
    }

    with OUT.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")
    print("wrote %s.json — 100 films, %d hours, %d work ids"
          % (SLUG, round(hours), len(qs)))
    for s in sections:
        print("   %-10s %3d  %s" % (s["title"], len(s["items"]), s["sub"][:44]))


if __name__ == "__main__":
    main()
