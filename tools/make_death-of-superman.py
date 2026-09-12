#!/usr/bin/env python3
"""Generate properties/death-of-superman.json.

    python tools/make_death-of-superman.py

The 1992–93 Superman crossover, issue by issue, in the order it was
published to be read.

WHERE THE ORDER COMES FROM, AND WHY IT IS NOT AN OPINION
--------------------------------------------------------
Nothing in this file is typed from memory. Everything is read out of
`tools/data/death-of-superman.json`, which is itself machine-read from named
pages and checked in so the build reproduces without a network:

  * the reading order — the `Issues` block of DC Database's storyline page
    https://dc.fandom.com/wiki/Death_and_Return_of_Superman, which lists all 38
    issues of the three arcs in one sequence;
  * the tie-ins and the back edge — the contents of four collected editions on
    the same wiki (`The Death of Superman`, `Superman: Funeral for a Friend`,
    `Superman: Reign of the Supermen`, `The Return of Superman`), read only for
    their issue lists. Anything a collection prints that the storyline page
    does not list is slotted in **immediately after the last storyline issue
    that precedes it in that collection** — a mechanical rule, applied by
    `weave()` below, never a judgement about where a tie-in "feels" right;
  * a cover month and year for every one of the 48 issues, read from that
    issue's own page on the same wiki. `assert_sources()` re-checks every row
    against that file, so a wrong issue number fails here rather than shipping;
  * why there is an order at all — DC Database's "Triangle Era", which says
    that from 1991 to 2002 the four monthly Superman books were "published
    with a triangular marking on their covers indicating reading order";
  * the prologue — Wikipedia's "The Death of Superman", which says the story
    "was first alluded to in Simonson's Superman: The Man of Steel #17
    (November 1992)", one teaser panel after the issue's own story.

THE TWO EDGES, WHICH ARE THE WHOLE DIFFICULTY WITH THIS LIST
------------------------------------------------------------
The front edge is hard: Man of Steel #18 opens the story, and #17 carries only
a teaser panel. So #17 is here as an optional Tier 3 prologue rather than as
part of the arc.

The back edge is soft, and no two sources stop in the same place. DC Database's
storyline page ends at Adventures of Superman #505. The 2016 collection runs on
through Action Comics #692 and Superman #83 — and Wikipedia notes that #83,
published after the last Reign issue, is an epilogue to *Funeral for a Friend*
rather than to Reign. Those two issues are kept, in their own Tier 2 section,
labelled as running past the end. Nothing after them is included: the next
sourced stop would be Superman: The Wedding Album, a year and a half later, and
that is a different story.

Adventures of Superman #500 sits in both the Funeral collection and the Reign
collection, and DC Database's storyline page files it under Funeral. It heads
the Reign section here, because Wikipedia says the final arc "began with a
prologue in The Adventures of Superman #500" and because the three-month
hiatus falls in front of it — the cover dates say so, March 1993 to June 1993.
The sequence is identical either way; only the section boundary moves.

NOTES
-----
Unweighted, like every comics list here: no per-issue reading time is
published, so inventing one would be worse than leaving it out.

The row notes say what an entry is, never what happens in it. That is harder
here than anywhere else in the catalogue, because the wiki prints a story title
beside every issue and several of them say outright how it ends. So no story
title is carried anywhere: `tools/data/death-of-superman.json` holds a cover
month and year per issue and nothing else, and nothing below reads any other
field.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop

SLUG = "death-of-superman"
DATA = pathlib.Path(__file__).resolve().parent / "data" / ("%s.json" % SLUG)

WIKI = "https://en.wikipedia.org/wiki/The_Death_of_Superman"
DCDB = "https://dc.fandom.com/wiki/Death_and_Return_of_Superman"
LINKS = [{"label": "The Death of Superman", "url": WIKI},
         {"label": "Issue order", "url": DCDB}]

# DC Database page prefix -> (display title, id prefix). The wiki names every
# issue "<series> Vol <n> <issue>"; the volume is dropped from the display
# title except where two volumes of the same name exist, which is why Superman
# and Green Lantern carry theirs and nothing else does.
SERIES = {
    "Action Comics": ("Action Comics", "act"),
    "Action Comics Annual": ("Action Comics Annual", "act-ann"),
    "Adventures of Superman": ("Adventures of Superman", "aos"),
    "Adventures of Superman Annual": ("Adventures of Superman Annual", "aos-ann"),
    "Superman": ("Superman (vol. 2)", "sup"),
    "Superman Annual": ("Superman Annual (vol. 2)", "sup-ann"),
    "Superman: The Man of Steel": ("Superman: The Man of Steel", "mos"),
    "Superman: The Man of Steel Annual":
        ("Superman: The Man of Steel Annual", "mos-ann"),
    "Justice League America": ("Justice League America", "jla"),
    "Green Lantern": ("Green Lantern (vol. 3)", "gl"),
    "Superman: The Legacy of Superman":
        ("Superman: The Legacy of Superman", "legacy"),
    "Supergirl and Team Luthor": ("Supergirl and Team Luthor", "sgtl"),
    "Newstime: The Life and Death of the Man of Steel":
        ("Newstime: The Life and Death of the Man of Steel", "newstime"),
}

PROLOGUE = "Superman: The Man of Steel Vol 1 17"

# Row annotations, keyed by DC Database page title. Everything here is a fact
# about publication — panel counts, cover dates, which book a thing is, how a
# collection treats it. Nothing here is a plot point.
NOTE = {
    PROLOGUE:
        "One teaser panel after the issue's own story. That is the whole "
        "of it.",
    "Justice League America Vol 1 69": "The League's issue.",
    "Adventures of Superman Vol 1 497": "Four panels a page.",
    "Action Comics Vol 1 684": "Three panels a page.",
    "Superman: The Man of Steel Vol 1 19": "Two panels a page.",
    "Superman Vol 2 75": "One panel a page, twenty-two of them.",
    "Newstime: The Life and Death of the Man of Steel Vol 1 1":
        "A one-shot in the form of a news magazine · cover-dated May 1993, "
        "but the first collection prints it here.",
    "Justice League America Vol 1 70": "The second and last League issue.",
    "Superman: The Legacy of Superman Vol 1 1":
        "A one-shot of five short stories.",
    "Supergirl and Team Luthor Vol 1 1": "A one-shot of two short stories.",
    "Adventures of Superman Vol 1 500":
        "The books came back from a three-month hiatus with this one.",
    "Action Comics Vol 1 687": "One of the four debuts.",
    "Superman: The Man of Steel Vol 1 22": "One of the four debuts.",
    "Superman Vol 2 78": "One of the four debuts.",
    "Adventures of Superman Vol 1 501": "One of the four debuts.",
    "Green Lantern Vol 3 46": "A tie-in from outside the Superman books.",
    "Action Comics Vol 1 692": "An epilogue, after the last chapter.",
    "Superman Vol 2 83":
        "Published last, but it closes out Funeral for a Friend.",
}
ANNUAL_NOTE = ("A 1993 Bloodlines annual — a different crossover · "
               "the collection slots it here.")

STAR = {"Superman Vol 2 75", "Adventures of Superman Vol 1 500",
        "Adventures of Superman Vol 1 505"}

# weave() marks everything the storyline page does not list as optional, which
# is right for the tie-ins and wrong for these two: they are not tie-ins, they
# are the far side of the back edge, and they carry their own Tier 2 section
# saying so. Optional inside a tier-2 section would be a second hedge.
NOT_OPT = {"Action Comics Vol 1 692", "Superman Vol 2 83"}

# (id, title, sub, tier, first page title, last page title, intro)
SECTIONS = [
    ("prologue", "Prologue", "November 1992 · a teaser panel, and nothing else",
     3, PROLOGUE, PROLOGUE,
     "The story proper starts next issue. This is one panel at the back of "
     "the one before it, and it is here so the front edge of the list is "
     "honest rather than tidy — skipping it costs you nothing."),
    ("doomsday", "Doomsday!",
     "December 1992 – January 1993 · seven issues across five books, "
     "plus a one-shot", 1,
     "Superman: The Man of Steel Vol 1 18",
     "Newstime: The Life and Death of the Man of Steel Vol 1 1",
     "The four monthly Superman books ran as one serial, each cover "
     "carrying a numbered triangle telling you which issue came next — so "
     "the order across those titles is a published fact rather than a "
     "guide's opinion. One Justice League America issue falls inside it, "
     "where DC Database's storyline page puts it.\n\n"
     "The last four issues count themselves down in panels — four to a page, "
     "then three, then two, then one. You can see the ending coming in the "
     "layout before you get there."),
    ("funeral", "Funeral for a Friend",
     "January – April 1993 · the aftermath, and then a gap", 1,
     "Adventures of Superman Vol 1 498", "Supergirl and Team Luthor Vol 1 1",
     "Nine issues of consequence, and then every Superman book stopped for "
     "three months. The two one-shots are optional; they hand the city to "
     "the supporting cast for an issue each."),
    ("reign", "Reign of the Supermen!",
     "June – July 1993 · four claimants, one per title", 1,
     "Adventures of Superman Vol 1 500", "Adventures of Superman Vol 1 502",
     "The books came back with a new lead in each one, each of the four "
     "introduced in his own debut issue with a cardstock cover and a poster. "
     "The rotation is the same as before, so the four run in parallel and "
     "you switch titles from issue to issue.\n\n"
     "The two annuals belong to Bloodlines, a separate 1993 crossover. They "
     "are optional, and they are placed where the collection places them."),
    ("return", "The Return of Superman",
     "July – October 1993 · the back half", 1,
     "Action Comics Vol 1 689", "Adventures of Superman Vol 1 505",
     "Where the 2016 collections cut the arc in two. Same rotation across "
     "the four books, and one tie-in from outside them."),
    ("epilogue", "Past the end",
     "October – November 1993 · where the collections stop", 2,
     "Action Comics Vol 1 692", "Superman Vol 2 83",
     "DC Database's storyline page ends one issue before these two; the 2016 "
     "collection keeps them. Both are worth having, and neither is part of "
     "the arc, so they sit out here where you can stop without them."),
]

NOTES = [
    ["Post-Crisis.",
     "The John Byrne reboot's Superman — the one relaunched in 1986 after "
     "Crisis on Infinite Earths, who works at the Daily Planet and is engaged "
     "to Lois Lane. Nothing published before 1986 is needed to follow this."],
    ["Why the order is a matter of record.",
     "From 1991 to 2002 every Superman book carried a small numbered "
     "triangle on its cover saying where that issue fell in the reading "
     "order — DC Database calls the whole stretch the Triangle Era. So there "
     "is no competing order to argue about here: the sequence below is the "
     "one DC Database's storyline page lists and the collected editions "
     "reprint."],
    ["Tiers.",
     "1 is the story itself, all three arcs. 2 is the two issues that run "
     "past the end. 3 is the teaser panel that set it up. The minimum "
     "viable path is Tier 1 alone."],
    ["What's marked optional.",
     "Seven of them: four Bloodlines annuals, two one-shots and a fake news "
     "magazine. None is part of the serial the four books ran. They are "
     "left in place "
     "rather than dropped so the order stays intact, each sitting exactly "
     "where a collected edition puts it. The prologue is optional too, for "
     "the different reason that it is one panel."],
    ["Where it stops.",
     "Adventures of Superman #505 is where the storyline ends. Action Comics "
     "#692 and Superman #83 come after it and are kept because the 2016 "
     "collection keeps them — #83 is an epilogue to Funeral for a Friend "
     "despite shipping last of all. Anything past those is a later story."],
    ["No spoilers.",
     "The notes say what an entry is, never what happens in it — which on "
     "this one means leaving out the story titles, since several of them "
     "say outright how it ends."],
    "Reading order machine-read from DC Database's Death and Return of "
    "Superman storyline page and from the contents of four collected "
    "editions on the same wiki; cover dates read from each issue's own page; "
    "the cover numbering from that wiki's Triangle Era article; the prologue "
    "and the Superman #83 placement from Wikipedia's The Death of Superman.",
]


def parse(page):
    """`Action Comics Vol 1 684` -> (display title, id, issue label)."""
    m = re.match(r"^(.+?) Vol \d+ (\d+)$", page)
    assert m, "unparseable page title %r" % page
    series, num = m.group(1), m.group(2)
    assert series in SERIES, "unmapped series %r" % series
    title, pre = SERIES[series]
    return title, "%s-%s" % (pre, num), "#%s" % num


def weave(data):
    """The storyline order, with each collection-only issue slotted in after
    the last storyline issue that precedes it in that collection."""
    spine = (data["arcs"]["Doomsday!"]
             + data["arcs"]["Funeral for a Friend"]
             + data["arcs"]["Reign of the Supermen!"])
    assert len(spine) == len(set(spine)) == 38, len(spine)
    extra = {}
    for name, pages in data["collections"].items():
        anchor = None
        for page in pages:
            if page in spine:
                anchor = page
                continue
            assert anchor, "%s opens with a non-storyline issue" % name
            extra.setdefault(anchor, [])
            if page not in extra[anchor]:
                extra[anchor].append(page)
    out = []
    for page in spine:
        out.append((page, 0))
        out += [(p, 1) for p in extra.get(page, [])]
    return out


def assert_sources(rows, data):
    """Every row is an issue page that was verified to exist, and every issue
    that was verified is used exactly once. Both directions, so neither a
    typo nor a dropped issue can get through."""
    used = [p for p, _ in rows]
    known = set(data["issues"])
    assert not set(used) - known, "rows with no source page: %s" % \
        sorted(set(used) - known)
    assert not known - set(used), "verified issues left out: %s" % \
        sorted(known - set(used))
    assert len(used) == len(set(used)), "issue used twice"


def build():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    rows = [(PROLOGUE, 1)] + weave(data)
    assert_sources(rows, data)

    by_page = {p: i for i, (p, _) in enumerate(rows)}
    sections, seen = [], 0
    for sid, title, sub, tier, first, last, intro in SECTIONS:
        a, b = by_page[first], by_page[last]
        assert a <= b and a == seen, \
            "section %s does not start where the last one ended" % sid
        seen = b + 1
        items = []
        for page, opt in rows[a:b + 1]:
            opt = 0 if page in NOT_OPT else opt
            t, iid, n = parse(page)
            note = NOTE.get(page, "")
            if not note and "Annual" in page:
                note = ANNUAL_NOTE
            items.append({"id": iid, "t": t, "n": n, "note": note,
                          "star": 1 if page in STAR else 0, "opt": opt,
                          "url": ""})
        sections.append({"id": sid, "title": title, "sub": sub, "tier": tier,
                         "intro": intro, "items": items, "links": LINKS})
    assert seen == len(rows), "%d rows unplaced" % (len(rows) - seen)

    return {
        "slug": SLUG,
        "title": "The Death and Return of Superman",
        "subtitle": "the 1992–93 crossover · post-Crisis",
        "kind": "comics",
        "popularity": 63,
        "year": "1992–1993",
        "blurb": "48 issues across the four monthly Superman books and "
                 "their tie-ins, in the order they were published to be "
                 "read.",
        "unit": {"one": "issue", "many": "issues"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": "#0B3C91",
        "accentDark": "#6FA8F5",
        "tiers": True,
        "notes": NOTES,
        "sections": sections,
    }


def main():
    p = build()
    n = sum(len(s["items"]) for s in p["sections"])
    opt = sum(1 for s in p["sections"] for x in s["items"] if x["opt"])
    assert n == 48, n
    assert opt == 8, opt   # the prologue plus seven tie-ins
    assert not any("w" in x or "weightUnit" in p
                   for s in p["sections"] for x in s["items"]), "weights"
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
    for _s in p["sections"]:
        for _x in _s["items"]:
            _x["w"] = 1
    assert all(_x.get("w") == 1 for _s in p["sections"] for _x in _s["items"]), \
        "a row escaped the weight stamp"
    out = prop.write(p)
    print("%s — %d issues in %d sections (%d optional)"
          % (out, n, len(p["sections"]), opt))


if __name__ == "__main__":
    main()
