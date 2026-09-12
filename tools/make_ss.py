#!/usr/bin/env python3
"""Generate properties/sight-and-sound.json — the 2022 critics' top 100.

    python tools/make_ss.py

The Sight and Sound Greatest Films of All Time, 2022 critics' poll, exactly
as the poll ranks it — 100 films, ties sharing a number and wearing the
poll's own "=" mark. Rank bands for sections, rank for n, runtimes for
weights. Random button on: it's a lifetime list, not a syllabus.

Weights: each film's own infobox, not Wikidata (CLU-178)
-------------------------------------------------------
Every bar is the runtime printed in that film's own {{Infobox film}}, selected
by gwlib.runtime.weigh() — see that module for why, and for the rule. This list
used to weigh from P2047, and that shipped *Blade Runner* at 112 minutes, which
is the film run at 25fps for a PAL transfer and a length nobody has ever sat
through; the article says 117, cited to the BBFC. 45 of the 100 rows moved.

The card that found it (CLU-178) blamed a rank-blind reader, and the raw
statements do not bear that out: Q184843 carries 112 and 116 as two `normal`
statements with no qualifier between them, so respecting rank cannot choose. It
is provenance that P2047 lacks and an infobox has, which is why the rule reads
labels — "(first cut)", "(Cannes cut)", "(20 fps)" — rather than ranks.

Where a box prints several lengths the row's own note says which one the bar is,
and VERSION_NOTE below must cover every such row or this script stops. Where the
box declines to give a figure at all — Pather Panchali, whose article says
outright that sources disagree — the row keeps the figure it already had and is
reported rather than being quietly re-weighted.

Data: tools/data/sight-and-sound.json via scratch/agent-canons/collect_ss.py
(BFI's own results page, top ten cross-checked against Wikipedia's article,
every film verified on Wikidata by year and director) and
scratch/agent-runtimes/measure.py (each film's own infobox, read from the
article the film's own Wikidata sitelink names).

One row’s collected data is another film’s, and it is corrected here rather than
in the collected file: the collector mis-resolved Histoire(s) du Cinéma to
Godard’s King Lear (1987) and then read its runtime off King Lear’s article, which
is why WRONG_INFOBOX exists (CLU-541). Its printed year is wrong for the same
reason and is NOT corrected, because the year is inside the row id and the id is
where the ticks are — PINNED_IDS refuses the rename rather than trusting nobody
tries it.

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
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import runtime as RT  # noqa: E402

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
    # year to pass its year gate. The row's printed year and its runtime bar were
    # read off that same wrong entity, which is a defect of its own (CLU-541).
    # The runtime half is fixed below; the year half cannot be, because the year
    # is in the id. This entry keeps the wrong id out of the sync map.
    #
    # The right item is Q2533567, and it stays out of the map deliberately rather
    # than for want of proof: Wikidata models the work as a *television series*
    # (P31 Q5398426), eight parts across 1989–1999, while every other row on this
    # poll is a film, so what it should pair with elsewhere is a question for a
    # card rather than a line here. No other list in this repo carries Q2533567
    # today, so attaching it would pair nothing and unpair nothing (CLU-541).
    "Histoire(s) du Cinéma": "Q2707428 is King Lear (1987), another film",
}

# A row whose collected runtime was read off the WRONG ARTICLE, because the
# collector resolved the film to the wrong Wikidata item and then followed that
# item’s sitelink to an infobox (CLU-541). This is not RUNTIME_EXCEPTION’s
# problem: the rule chose correctly from the box it was handed, and the box
# belonged to another film.
#
# Histoire(s) du Cinéma resolved to Q2707428, which is Godard’s *King Lear*
# (1987) — same director, and 1987 sits inside the ±1 year the collector’s gate
# allowed against the BFI’s 1988, so the gate passed it. Both entities were read
# on 2026-09-11 and they are not close:
#
#   Q2707428  label "King Lear", description "1987 film by Jean-Luc Godard",
#             P31 film, P577 1987, P2047 90 min, enwiki "King Lear (1987 film)".
#             That article’s box prints `runtime = 90 minutes`, `released` 17 May
#             1987 (Cannes), `country = United States`.
#   Q2533567  label "Histoire(s) du cinéma", P57 Godard, P577 1998, P2047 267
#             min, P580 1989-05-07, P582 1999, enwiki "Histoire(s) du cinéma".
#             That article’s box prints `runtime = 266 minutes (total)`, no
#             `released` field at all, and `country = France<br>Switzerland` —
#             which is the country the BFI page gives for this row, while King
#             Lear’s "United States" is not. The prose agrees: "an eight-part
#             video project begun … in the late 1980s and completed in 1998",
#             "at a total of 266 minutes".
#
# The bar is 266 and not P2047’s 267 because this list weighs from the film’s own
# infobox rather than from Wikidata (CLU-178), and that box says 266 — the same
# figure its own prose gives. The row was weighing 90 minutes, so this list was
# under-counting a four-and-a-half-hour work by nearly three hours.
#
# The PRINTED YEAR is wrong for exactly the same reason and is deliberately NOT
# corrected here: the year is inside `ss-1987-histoire-s-du-cinema`, which is
# where every tick on this row is stored, and the two candidate right answers
# (the BFI’s 1988, Wikidata’s 1998) both move it. That is a decision, on CLU-541,
# not an edit — and PINNED_IDS below makes the rename impossible to do by
# accident in the meantime.
WRONG_INFOBOX = {
    # title: (the right box’s figure, the box it was read from,
    #         the box it should have been read from, what the rule says today)
    "Histoire(s) du Cinéma": (266, "King Lear (1987 film)",
                                "Histoire(s) du cinéma", 90),
}

# Row ids that must not move. A tick is stored against an id, so a renamed row
# does not migrate anybody’s progress — it silently unticks everyone who had it.
# This one is pinned because its printed year is known to be wrong (CLU-541), so
# the obvious fix is a rename waiting to happen; the assertion fails instead.
PINNED_IDS = [
    "ss-1987-histoire-s-du-cinema",
]

# The one row where the infobox rule needs overruling, with its reason and the
# answer the rule gives, asserted — an exception that has silently stopped
# matching its article is worse than no exception at all.
#
# L'Atalante's box prints "65 minutes (original French release)" and "85 minutes
# (restored version)". The 65-minute version is not a shorter release of this
# film: the article says Gaumont cut it and reissued it retitled *Le Chaland qui
# passe*, after a popular song of the day which they also cut into the score.
# The film Vigo made is the 1990 restoration, re-edited in 2001, and that is the
# version in circulation — it is what Criterion carries. So the restoration is
# the weight, and the rule's own answer is pinned so a rewritten box is noticed.
RUNTIME_EXCEPTION = {
    "L'Atalante": (85, "the restoration", 65),
}

# Every row whose box prints more than one length, or gives none, says on the
# row which length the bar is. Asserted to cover exactly that set: a new
# multi-cut box stops this script instead of shipping an unexplained bar.
VERSION_NOTE = {
    "Apocalypse Now": "the 70mm cut",
    "The Passion of Joan of Arc": "at 24fps",
    "L'Atalante": "the restoration",
    "Pather Panchali": "sources give 112–126 min",
    "The Battle of Algiers": "the original cut",
    "Andrei Rublev": "the final cut",
    "Journey to Italy": "the Italian release",
    "The Shining": "the US release",
    "The Leopard": "the Italian cut",
    "Once upon a Time in the West": "the Italian release",
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

    # Weights: the film's own infobox, by gwlib.runtime's rule. A row the rule
    # cannot settle keeps the figure it already carried — never a guess.
    exc, needs_note, kept, moved = dict(RUNTIME_EXCEPTION), set(), [], []
    bad_box = dict(WRONG_INFOBOX)
    for f in films:
        cuts = [tuple(c) for c in (f.get("infobox_cuts") or [])]
        n, why = RT.weigh(cuts, f.get("infobox_range", False))
        if f["t"] in WRONG_INFOBOX:
            want, from_page, right_page, rule_said = bad_box.pop(f["t"])
            assert f.get("infobox_page") == from_page, \
                "WRONG_INFOBOX says %s's figure came from %r; the data says " \
                "%r. If the collector has been fixed, delete this entry \u2014 do " \
                "not leave it overriding a figure it no longer describes" \
                % (f["t"], from_page, f.get("infobox_page"))
            assert n == rule_said, \
                "WRONG_INFOBOX for %s expects the wrong box to give %s, it " \
                "gives %s \u2014 re-read both articles before trusting either figure" \
                % (f["t"], rule_said, n)
            n, why = want, "%s's box, not %s's" % (right_page, from_page)
        if f["t"] in RUNTIME_EXCEPTION:
            want, reason, rule_said = exc.pop(f["t"])
            assert n == rule_said,                 "RUNTIME_EXCEPTION for %s expects the rule to say %s, it says "                 "%s — the article's box has changed" % (f["t"], rule_said, n)
            n, why = want, reason
        if n is None:
            kept.append((f["t"], f["min"], why))
            n = f["min"]
        elif n != f["min"]:
            moved.append((f["t"], f["min"], n, why))
        if len(cuts) > 1 or f.get("infobox_range"):
            needs_note.add(f["t"])
        f["min"], f["min_src"] = n, "infobox"
    assert not exc, "RUNTIME_EXCEPTION names no film on this poll: %s" % sorted(exc)
    assert not bad_box, \
        "WRONG_INFOBOX names no film on this poll: %s" % sorted(bad_box)
    assert needs_note == set(VERSION_NOTE),         "VERSION_NOTE must name exactly the rows whose box prints more than one "         "length: missing %s, stale %s" % (sorted(needs_note - set(VERSION_NOTE)),
                                          sorted(set(VERSION_NOTE) - needs_note))

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
            if f["t"] in VERSION_NOTE:
                it["note"] += " · %d min, %s" % (f["min"], VERSION_NOTE[f["t"]])
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
    for pid in PINNED_IDS:
        assert pid in ids, \
            "pinned id lost: %s. Every tick on that row is stored against it, " \
            "so shipping this build would untick them all. If the rename is " \
            "wanted, it needs a backfill first \u2014 see CLU-541" % pid
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
            ["Bar widths are runtimes, read from each film's own article.",
             "Every bar is the runtime printed in that film's own Wikipedia "
             "infobox, which is where a length keeps the name of the version "
             "it belongs to. Where a box prints several cuts the bar is the "
             "release and the row says which; where the article says sources "
             "disagree, the row says that too. Nothing is estimated, and the "
             "longest here keeps its full %d minutes rather than being capped."
             % max(f["min"] or 0 for f in films)],
            ["Where the list comes from.",
             "The ranked list is read from the BFI's own results page — the "
             "reference Wikipedia's record of the poll points to, since the "
             "encyclopedia's article keeps only the top ten. That top ten "
             "is cross-checked against the article, and every film on the "
             "hundred is verified against Wikidata by year and director "
             "before it gets a row."],
            "The 2022 Sight and Sound critics' poll, via bfi.org.uk; "
            "runtimes from each film's own Wikipedia article.",
        ],
        "sections": sections,
    }

    with OUT.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")
    print("wrote %s.json — 100 films, %d hours, %d work ids"
          % (SLUG, round(hours), len(qs)))
    print("  runtimes: %d rows moved to the film's own infobox, %d kept what "
          "they had" % (len(moved), len(kept)))
    for t, was, now, why in sorted(moved, key=lambda m: -abs(m[2] - (m[1] or 0))):
        print("   %+5d  %-38s %-4s -> %-4s  %s"
              % (now - (was or 0), t[:38], was, now, why[:52]))
    for t, was, why in kept:
        print("   kept   %-38s %-4s       %s" % (t[:38], was, why[:52]))
    for s in sections:
        print("   %-10s %3d  %s" % (s["title"], len(s["items"]), s["sub"][:44]))


if __name__ == "__main__":
    main()
