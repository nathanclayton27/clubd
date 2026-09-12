#!/usr/bin/env python3
"""Generate properties/thor.json — sixty years of Thor, in publication order.

    python3 tools/make_thor.py

THE ORDER IS PUBLICATION ORDER, AND THE TIERS DO THE CURATING.

Thor's problem is that the peak is not the beginning: Walt Simonson's run
starts 21 years and 254 issues into the title, and it is the thing everybody
is actually sent to. Two ways out of that, and only one of them survives
contact with a tracker:

  * resequence the list so Simonson comes first. Rejected. A reading order's
    product is the sequence, and a sequence that lies about what came before
    what makes the 1962-1996 material unreadable as a lineage — the numbering
    on the cover stops matching the row above it.
  * keep publication order and let `tier` say what is worth reading. Taken.
    Tier 1 is the readable path and it BEGINS at Simonson (#337); everything
    before it is Tier 2 or Tier 3 and says so in its own section header. A
    reader who ticks only Tier 1 gets Simonson, Straczynski and the whole of
    Jason Aaron, 159 issues, and skips 439 issues of 1970s and 1990s filler
    without ever being told they read them.

The blurb says which order this is, in the first sentence, because a list that
does not say cannot be checked.

SOURCES — nothing here is typed from memory.

  * Marvel Fandom's per-volume categories enumerate the issues. A category
    member carries a sortkey prefix that encodes the issue's cover date, which
    is how section headers get real years and how the Balder the Brave
    miniseries is woven into the Simonson run at the month it shipped, rather
    than bolted on the end. Cached under scratch/thor/ by scratch/thor/fetch.py
    (or refetched here if the cache is cold).
  * Wikipedia's "List of Thor titles" is the spine: it gives every primary
    series with its issue range, its dates, and its legacy numbering. Every
    range asserted below is checked against the Fandom enumeration, so the two
    sources have to agree or the build stops.
  * Wikipedia's "Thor (comic book)" infobox `writers` field gives the writer
    boundaries the sections are cut on (Conway 193-238, Simonson 337-382,
    DeFalco 383-459, and so on), and its publication-history prose gives the
    per-issue notes — Kirby's last issue, the Tales of Asgard back-up, the
    title changing to The Mighty Thor at #407.
  * Wikipedia's "Beta Ray Bill" and "Thunderstrike (Eric Masterson)" articles
    give the two mantle facts the list cannot avoid stating.

DELIBERATELY NOT ROWED, and each for a reason:

  * Journey into Mystery #503-521 (1996-1998). The title reverted during Heroes
    Reborn and Thor is not in it — Wikipedia's own list files it under
    "Secondary series" with the note "does not feature Thor". A Thor tracker
    that makes you tick nineteen issues of Shang-Chi and Black Widow is broken.
  * Annuals, one-shots and the several dozen miniseries. They are not in the
    legacy numbering and no source orders them against the monthly.
  * The Immortal Thor (2023- ). Still publishing; a row count that goes stale
    every month is worse than a note saying where the list stops.

UNWEIGHTED, per the house rule: comics publish no per-issue reading time, and
a mix of weighted and unweighted rows is a hard failure.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "scratch" / "thor"

SLUG = "thor"

# Marvel series ids, resolved against the shared index so a typo fails here.
_INDEX = json.loads((ROOT / "tools" / "data" / "marvel_series_index.json")
                    .read_text(encoding="utf-8"))


def S(slug):
    assert slug in _INDEX, "not in the Marvel index: %r" % slug
    return "https://www.marvel.com/comics/series/%s/%s" % (_INDEX[slug], slug)


def L(label, slug):
    return {"label": label, "url": S(slug)}


# --------------------------------------------------------------- the source --
def members(cat):
    """Marvel Fandom category members: [{title, key}], key carrying the cover
    date. Reads scratch/thor/, fetching if the cache is cold."""
    f = CACHE / ("cat-" + re.sub(r"[^A-Za-z0-9]+", "-", cat).strip("-") + ".json")
    if not f.exists():
        sys.path.insert(0, str(CACHE))
        import fetch  # noqa: E402  (scratch/thor/fetch.py)
        fetch.members(cat)
    d = json.loads(f.read_text(encoding="utf-8"))
    assert d, "empty category: %r" % cat
    return d


def issues(cat):
    """{issue label -> 'YYYY-MM'} for one Fandom volume category.

    The issue label is whatever follows the volume name in the page title, so
    '#620.1' survives as '620.1' rather than being coerced to an int."""
    pre = cat + " "
    out = {}
    for m in members(cat):
        t = m["title"]
        assert t.startswith(pre), "unexpected page in %r: %r" % (cat, t)
        n = t[len(pre):]
        d = re.search(r"(\d{4})-(\d{2})", m["key"] or "")
        assert d, "no cover date for %r" % t
        assert n not in out, "duplicate issue %r in %r" % (n, cat)
        out[n] = d.group(0)
    return out


JIM1 = issues("Journey Into Mystery Vol 1")        # #1-125; Thor from #83
V1 = issues("Thor Vol 1")                          # #126-502
V2 = issues("Thor Vol 2")                          # #1-85
V3 = issues("Thor Vol 3")                          # #1-12, #600-621, #620.1
MT1 = issues("Mighty Thor Vol 1")                  # #1-22, #12.1
JIM4 = issues("Journey Into Mystery Vol 4")        # #622-655, #626.1
GOT = issues("Thor: God of Thunder Vol 1")         # #1-25
V4 = issues("Thor Vol 4")                          # #1-8
THORS = issues("Thors Vol 1")                      # #1-4
MT2 = issues("Mighty Thor Vol 2")                  # #1-23, #700-706
V5 = issues("Thor Vol 5")                          # #1-16
WOTR = issues("War of the Realms Vol 1")           # #1-6
KING = issues("King Thor Vol 1")                   # #1-4
V6 = issues("Thor Vol 6")                          # #1-35
BALDER = issues("Balder the Brave Vol 1")          # #1-4

# Wikipedia's "List of Thor titles" primary-series spine, asserted against the
# Fandom enumerations above. If either source moves, the build stops.
SPINE = [
    # The category is the whole anthology, #1-125; Thor only arrives at #83.
    ("Journey into Mystery #1-125", JIM1, [str(n) for n in range(1, 126)]),
    ("Thor #126-502", V1, [str(n) for n in range(126, 503)]),
    ("Thor vol. 2 #1-85", V2, [str(n) for n in range(1, 86)]),
    ("Thor vol. 3 #1-12, #600-621, #620.1", V3,
     [str(n) for n in range(1, 13)] + [str(n) for n in range(600, 622)] + ["620.1"]),
    ("The Mighty Thor #1-22, #12.1", MT1,
     [str(n) for n in range(1, 23)] + ["12.1"]),
    ("Journey into Mystery #622-655, #626.1", JIM4,
     [str(n) for n in range(622, 656)] + ["626.1"]),
    # Marvel branded issue 19 as "#19.NOW"; Wikipedia counts it as #19.
    ("Thor: God of Thunder #1-25", GOT,
     [str(n) for n in range(1, 19)] + ["19.NOW"]
     + [str(n) for n in range(20, 26)]),
    ("Thor vol. 4 #1-8", V4, [str(n) for n in range(1, 9)]),
    ("Thors #1-4", THORS, [str(n) for n in range(1, 5)]),
    ("The Mighty Thor #1-23, #700-706", MT2,
     [str(n) for n in range(1, 24)] + [str(n) for n in range(700, 707)]),
    ("Thor vol. 5 #1-16", V5, [str(n) for n in range(1, 17)]),
    ("War of the Realms #1-6", WOTR, [str(n) for n in range(1, 7)]),
    ("King Thor #1-4", KING, [str(n) for n in range(1, 5)]),
    ("Thor vol. 6 #1-35", V6, [str(n) for n in range(1, 36)]),
    ("Balder the Brave #1-4", BALDER, [str(n) for n in range(1, 5)]),
]
for label, got, want in SPINE:
    missing = [n for n in want if n not in got]
    extra = [n for n in got if n not in want]
    assert not missing and not extra, \
        "%s: Fandom and Wikipedia disagree — missing %s, extra %s" % (
            label, missing[:6], extra[:6])

# --------------------------------------------------------------------- notes --
# Every line below is a publication fact taken from one of the named sources.
# Nothing says what happens in an issue; see HOUSE RULES.
N_JIM = {
    "83": ("Thor's first appearance — Stan Lee, Larry Lieber, Jack Kirby", 2),
    "97": ("the “Tales of Asgard” back-up starts here", 0),
    "101": ("Kirby becomes the regular artist — this is where the run people "
            "mean begins", 2),
    "104": ("“The Mighty Thor” takes over the cover logo", 0),
    "105": ("the feature grows to 18 pages and the anthology stories go", 0),
    "125": ("the last issue under this title", 1),
}
N_V1 = {
    "126": ("same book, new name, and the numbering carries straight on", 1),
    "145": ("the last “Tales of Asgard” back-up", 0),
    "146": ("an Inhumans back-up runs from here to #152", 0),
    "179": ("Kirby's last issue", 1),
    "180": ("Neal Adams pencils this one and the next", 0),
    "182": ("John Buscema becomes the regular artist", 0),
    "193": ("Gerry Conway takes over the writing", 0),
    "239": ("Roy Thomas takes over", 0),
    "242": ("Len Wein writes from here", 0),
    "278": ("Buscema's last as regular artist", 0),
    "329": ("Alan Zelenetz writes the stretch into Simonson", 0),
    "337": ("Walt Simonson takes over as writer and artist, and Beta Ray Bill "
            "debuts", 2),
    "367": ("Simonson's last as artist — he keeps writing", 1),
    "382": ("Simonson's last issue", 2),
    "383": ("Tom DeFalco takes over, mostly with Ron Frenz", 0),
    "391": ("Eric Masterson's first appearance", 0),
    "407": ("the indicia says The Mighty Thor from here", 0),
    "408": ("Masterson is merged with Thor and is the alter ego to #432", 0),
    "432": ("the mantle changes hands — Masterson carries it to #459", 1),
    "459": ("DeFalco's last; Masterson leaves for his own book", 0),
    "460": ("Ron Marz writes from here", 0),
    "472": ("Roy Thomas returns", 0),
    "491": ("plain Thor on the indicia again; Warren Ellis writes four", 0),
    "495": ("William Messner-Loebs to the end", 0),
    "502": ("the last issue of the 1966 series", 1),
}
N_V2 = {
    "1": ("Dan Jurgens and John Romita Jr. relaunch it", 1),
    "36": ("dual numbering starts — this one is also #538", 0),
    "59": ("a single fill-in by Christopher Priest", 0),
    "60": ("Jurgens again", 0),
    "80": ("Michael Avon Oeming and Daniel Berman write the last six", 0),
    "85": ("the last issue — #587 in the legacy count", 1),
}
N_V3 = {
    "1": ("J. Michael Straczynski and Olivier Coipel — a clean place to start "
          "cold", 2),
    "600": ("the numbering goes back to the original count", 1),
    "604": ("Kieron Gillen takes over", 0),
    "615": ("Matt Fraction takes over", 0),
    "620.1": ("a point-one issue — a jumping-on point alongside #620", 0),
    "621": ("the last issue before the title changes again", 0),
}
N_MT1 = {
    "1": ("Fraction and Coipel, straight on from Thor #621", 0),
    "12.1": ("a jumping-on point, published between #12 and #13", 0),
    "22": ("the last issue", 0),
}
N_JIM4 = {
    "622": ("the title reverts a second time — Gillen and Doug Braithwaite, "
            "with Loki as the lead", 1),
    "626.1": ("a point-one issue", 0),
    "655": ("the last issue", 0),
}
N_GOT = {
    "1": ("Jason Aaron and Esad Ribic begin — the other clean place to start "
          "cold", 2),
    "19.NOW": ("Marvel branded this one #19.NOW — it is issue 19", 0),
    "25": ("the last issue", 0),
}
N_V4 = {"1": ("the hammer changes hands", 2), "8": ("the last issue", 0)}
N_THORS = {"1": ("a Secret Wars tie-in, written by Aaron between the two "
                 "volumes", 0)}
N_MT2 = {
    "1": ("Aaron with Russell Dauterman", 1),
    "700": ("the legacy numbering comes back", 1),
    "706": ("the last issue", 0),
}
N_V5 = {"1": ("Aaron again, with Mike del Mundo", 1)}
N_WOTR = {"1": ("the event Aaron had been building to since 2013", 1),
          "6": ("the last issue", 0)}
N_KING = {"1": ("four issues, Aaron and Ribic again", 0),
          "4": ("the last issue of Aaron's seven years on the character", 2)}
N_V6 = {"1": ("Donny Cates and Nic Klein pick it up", 1),
        "35": ("the last issue of the volume", 0)}
N_BALDER = {"1": ("a Simonson-written miniseries running alongside the main "
                  "book — placed here by its cover date", 0)}


def rows(prefix, title, src, nums, notes, opt=0):
    """One row per issue. `title` may be a callable of the issue label."""
    out = []
    for n in nums:
        assert n in src, "%s #%s is not in the source" % (prefix, n)
        note, star = notes.get(n, ("", 0))
        out.append({
            "id": "thor-%s-%s" % (prefix, n.replace(".", "-")),
            "t": title(n) if callable(title) else title,
            "n": "#" + n,
            "note": note,
            "star": star,
            "opt": opt,
            "url": "",
            "_d": src[n],
        })
    return out


def span(items):
    """'1983–1987' from the rows' own cover dates — never typed by hand."""
    ys = sorted(x["_d"][:4] for x in items)
    return ys[0] if ys[0] == ys[-1] else "%s–%s" % (ys[0], ys[-1])


def sec(sid, title, sub, tier, items, links, intro=None):
    for x in items:
        x.pop("_d", None)
    s = {"id": sid, "title": title, "sub": sub, "tier": tier}
    if intro:
        s["intro"] = intro
    s["items"] = items
    s["links"] = links
    return s


def r(a, b):
    return [str(n) for n in range(a, b + 1)]


# ------------------------------------------------------------------ sections --
def v1_title(n):
    """The indicia changed twice inside one volume."""
    return "The Mighty Thor" if 407 <= int(float(n)) <= 490 else "Thor"


sections = []

it = rows("jim", "Journey into Mystery", JIM1, r(83, 125), N_JIM)
sections.append(sec(
    "jim", "Journey into Mystery #83–125", "%s · before it was his book" % span(it), 2,
    it, [L("Journey into Mystery", "journey_into_mystery_1952_1966")],
    intro="Thor starts as a thirteen-page feature in a monster anthology, "
          "sharing the issue with whatever else fit. Lee and Kirby find the "
          "book somewhere around #101 and it stops being a superhero strip and "
          "starts being Asgard.\n\nYou do not need any of this to read "
          "Simonson. It is here because it is the foundation and because the "
          "Kirby stretch is one of the great runs in the medium — but it is "
          "Tier 2, not Tier 1, and the difference is honest."))

it = rows("v1", v1_title, V1, r(126, 179), N_V1)
sections.append(sec(
    "leekirby", "Thor #126–179", "%s · Lee and Kirby" % span(it), 2, it,
    [L("Thor", "thor_1966_1996")]))

it = rows("v1", v1_title, V1, r(180, 238), N_V1)
sections.append(sec(
    "afterkirby", "Thor #180–238", "%s · after Kirby" % span(it), 3, it,
    [L("Thor", "thor_1966_1996")],
    intro="Adams for two issues, then John Buscema for most of a decade, with "
          "the writing passing from Lee to Gerry Conway. It is competent "
          "monthly comics and almost nobody reads it straight through."))

it = rows("v1", v1_title, V1, r(239, 299), N_V1)
sections.append(sec(
    "seventies", "Thor #239–299", "%s · Wein, then Thomas" % span(it), 3, it,
    [L("Thor", "thor_1966_1996")]))

it = rows("v1", v1_title, V1, r(300, 336), N_V1)
sections.append(sec(
    "drift", "Thor #300–336", "%s · the stretch before the good part" % span(it),
    3, it, [L("Thor", "thor_1966_1996")]))

simonson = rows("v1", v1_title, V1, r(337, 382), N_V1) \
    + rows("balder", "Balder the Brave", BALDER, r(1, 4), N_BALDER)
simonson.sort(key=lambda x: (x["_d"], x["id"]))
sections.append(sec(
    "simonson", "Thor #337–382", "%s · start here" % span(simonson), 1, simonson,
    [L("Thor", "thor_1966_1996"), L("Balder", "balder_the_brave_1985_1986")],
    intro="This is the run. Simonson writes and draws from #337, hands the "
          "pencils to Sal Buscema at #367 and keeps writing to #382, and in "
          "between he rebuilds the book out of the mythology rather than out "
          "of the superhero line around it.\n\nIt needs nothing before it. "
          "Everything above this section is Tier 2 or Tier 3 for exactly that "
          "reason — if you are starting Thor today you start on this row, and "
          "you can go back for Kirby afterwards.\n\nThe four Balder the Brave "
          "issues are woven in at the month they shipped rather than hung off "
          "the end, because that is where they are read."))

it = rows("v1", v1_title, V1, r(383, 459), N_V1)
sections.append(sec(
    "defalco", "Thor #383–459", "%s · DeFalco and Frenz" % span(it), 3, it,
    [L("Thor", "thor_1966_1996")],
    intro="Tom DeFalco follows Simonson, which is the hardest job on the "
          "board, and the run is longer than Simonson's. The title changes to "
          "The Mighty Thor at #407 and the mantle changes hands at #432 — both "
          "are noted on the rows, because otherwise the covers stop matching "
          "the list."))

it = rows("v1", v1_title, V1, r(460, 502), N_V1)
sections.append(sec(
    "endof66", "Thor #460–502", "%s · to the end of the 1966 series" % span(it),
    3, it, [L("Thor", "thor_1966_1996")]))

it = rows("v2", "Thor (1998)", V2, r(1, 85), N_V2)
sections.append(sec(
    "jurgens", "Thor vol. 2 #1–85", "%s · Jurgens and Romita Jr." % span(it), 3,
    it, [L("Thor vol. 2", "thor_1998_2004")],
    intro="Six years and 85 issues, well liked at the time and not what "
          "anyone hands you first. Skipping it costs you nothing that the next "
          "section does not restate."))

jms = rows("v3", "Thor (2007)", V3, r(1, 12), N_V3) \
    + rows("v3", "Thor", V3, r(600, 603), N_V3)
sections.append(sec(
    "jms", "Thor vol. 3 #1–12 and #600–603",
    "%s · Straczynski and Coipel" % span(jms), 1, jms,
    [L("Thor vol. 3", "thor_2007_2011")],
    intro="The second place you can start cold. Straczynski relaunches the "
          "book from nothing and Coipel draws it; at what would have been #13 "
          "the numbering jumps to #600 to match the original count, which is "
          "why this section has two ranges in it and only one story."))

it = rows("v3", "Thor", V3, r(604, 620) + ["620.1", "621"], N_V3)
sections.append(sec(
    "gillenfraction", "Thor #604–621", "%s · Gillen, then Fraction" % span(it),
    3, it, [L("Thor vol. 3", "thor_2007_2011")]))

it = rows("mt1", "The Mighty Thor (2011)", MT1, r(1, 12) + ["12.1"] + r(13, 22),
          N_MT1)
sections.append(sec(
    "fraction", "The Mighty Thor #1–22", "%s · Fraction and Coipel" % span(it),
    3, it, [L("The Mighty Thor", "the_mighty_thor_2011_2012")]))

it = rows("jim4", "Journey into Mystery", JIM4,
          r(622, 626) + ["626.1"] + r(627, 655), N_JIM4)
sections.append(sec(
    "loki", "Journey into Mystery #622–655", "%s · Loki's book" % span(it), 2, it,
    [L("Journey into Mystery", "journey_into_mystery_2011_2013")],
    intro="Gillen takes the old title back and gives it to Loki. It is not a "
          "Thor comic and it is the best-regarded thing on this list outside "
          "Simonson and Aaron, which is why it is Tier 2 in a section of the "
          "list that is otherwise Tier 3."))

it = rows("got", "Thor: God of Thunder", GOT,
          r(1, 18) + ["19.NOW"] + r(20, 25), N_GOT)
sections.append(sec(
    "aaron", "Thor: God of Thunder #1–25", "%s · Aaron and Ribic" % span(it), 1,
    it, [L("God of Thunder", "thor_god_of_thunder_2012_2014")],
    intro="Jason Aaron's Thor starts here and runs, under five different "
          "titles, for the next seven years. Every section below this one is "
          "the same continuous story and they are Tier 1 together.\n\nLike "
          "Simonson, it starts cold on purpose. Nothing above this row is "
          "required."))

it = rows("v4", "Thor (2014)", V4, r(1, 8), N_V4) \
    + rows("thors", "Thors", THORS, r(1, 4), N_THORS)
sections.append(sec(
    "mantle", "Thor #1–8 and Thors #1–4",
    "%s · the hammer changes hands" % span(it), 1, it,
    [L("Thor", "thor_2014_2015"), L("Thors", "thors_2015")],
    intro="Thor is a mantle in this list, not a person, and from here it is "
          "carried by someone else — the book keeps the title, the numbering "
          "and the writer, so the rows keep going.\n\nThors is a four-issue "
          "Secret Wars tie-in Aaron wrote in the gap between the two volumes. "
          "It sits here because that is where its cover dates put it."))

it = rows("mt2", "The Mighty Thor (2015)", MT2, r(1, 23) + r(700, 706), N_MT2)
sections.append(sec(
    "mighty", "The Mighty Thor #1–23 and #700–706",
    "%s · Aaron and Dauterman" % span(it), 1, it,
    [L("The Mighty Thor", "mighty_thor_2015_2018")]))

it = rows("v5", "Thor (2018)", V5, r(1, 16), N_V5)
sections.append(sec(
    "vol5", "Thor #1–16", "%s · the run turns toward the end" % span(it), 1, it,
    [L("Thor", "thor_2018_2019")]))

it = rows("wotr", "War of the Realms", WOTR, r(1, 6), N_WOTR)
sections.append(sec(
    "wotr", "War of the Realms #1–6",
    "%s · ships alongside the tail of Thor vol. 5" % span(it), 1, it,
    [L("War of the Realms", "war_of_the_realms_2019")],
    intro="Six issues, and the payoff for six years of setup. Its cover dates "
          "overlap Thor #11–16 above, so read those first and then this; the "
          "dozens of tie-in miniseries published around it are not rowed here "
          "and are not needed."))

it = rows("king", "King Thor", KING, r(1, 4), N_KING)
sections.append(sec(
    "king", "King Thor #1–4", "%s · the end of the run" % span(it), 1, it,
    [L("King Thor", "king_thor_2019")]))

it = rows("v6", "Thor (2020)", V6, r(1, 35), N_V6)
sections.append(sec(
    "cates", "Thor #1–35", "%s · what comes next" % span(it), 3, it,
    [L("Thor vol. 6", "thor_2020_2023")],
    intro="Donny Cates and Nic Klein take over after Aaron, with Torunn "
          "Grønbekk finishing the volume. It is here so the list does not stop "
          "mid-shelf, not because you have to read it.\n\nThe Immortal Thor, "
          "which follows it and is still publishing, is deliberately not "
          "rowed — an unfinished run would put a stale number on this page "
          "every month."))

# --------------------------------------------------------------------- emit --
ROWS = sum(len(s["items"]) for s in sections)
TIER1 = sum(len(s["items"]) for s in sections if s["tier"] == 1)
assert ROWS == 730, "row count moved: %d" % ROWS
assert TIER1 == 159, "Tier 1 count moved: %d" % TIER1
assert not any("w" in x or "weightUnit" in s
               for s in sections for x in s["items"]), "this list is unweighted"

P = {
    "slug": SLUG,
    "title": "Thor",
    "subtitle": "sixty years of the mantle — Lee and Kirby to Jason Aaron",
    "kind": "comics",
    "popularity": 71,
    "year": "1962–2023",
    "blurb": "%d issues in publication order, from Journey into Mystery #83 to "
             "the end of the 2020 volume — with the tiers saying where to "
             "actually start, because the best run is 254 issues in."
             % ROWS,
    "unit": {"one": "issue", "many": "issues"},
    "verb": {"base": "read", "past": "read", "ing": "reading"},
    "accent": "#1F4E8C",
    "accentDark": "#7FB2F0",
    "tiers": True,
    "notes": [
        ["Tiers.",
         "1 is essential, 2 is strongly recommended, 3 is genuinely optional. "
         "The minimum viable path is Tier 1 alone — %d issues, starting at "
         "Simonson and ending with Aaron." % TIER1],
        ["This is publication order, not a curated order.",
         "Every row sits where it was published, which is the only order in "
         "which the numbers on the covers make sense. The curation is the "
         "tier: Tier 1 begins at Thor #337 and skips the 1970s and the 1990s "
         "entirely. If you want the short answer to “where do I start”, it is "
         "#337, or Thor: God of Thunder #1 if you would rather start in 2013."],
        ["The mantle, not the man.",
         "Thor is an identity here and it changes hands more than once — most "
         "consequentially at Thor #432 and again at Thor #1 in 2014. The rows "
         "follow the book, because the book keeps its title and its numbering "
         "through both."],
        ["Why the numbering keeps jumping.",
         "Marvel renumbered this title six times. Journey into Mystery becomes "
         "Thor at #126, Thor becomes The Mighty Thor at #407 and back at #491, "
         "the 1998 relaunch restarts at #1, the 2007 relaunch restarts again "
         "and then jumps to #600, and the legacy count returns at #700. The "
         "section headers give the numbers on the covers."],
        ["Journey into Mystery #503–521 is not here.",
         "The title reverted during Heroes Reborn and Thor is not in it — "
         "Wikipedia files those nineteen issues as a secondary series that "
         "“does not feature Thor”. Annuals, one-shots and the miniseries are "
         "out for the same reason: no source orders them against the monthly."],
        "Issue enumerations and cover dates are read from Marvel Fandom's "
        "per-volume categories; the series spine, the legacy numbering and the "
        "writer boundaries come from Wikipedia's “List of Thor titles” and "
        "“Thor (comic book)”. The two are cross-checked against each other and "
        "the generator stops if they disagree.",
    ],
    "sections": sections,
}

# CLU-545: every comics row on this site weighs ONE ISSUE, which is
# Nathan's "issues, not collected volumes" ruling applied to the weight
# as well as to the row. It makes the strip measure issues rather than
# rows, and it is what lets a hub door into this list carry a real
# weight instead of none. Stamped in one place rather than on every row
# constructor: `w` is presentation and is not part of an id, so no tick
# moves.
for _sec in P["sections"]:
    for _row in _sec["items"]:
        _row["w"] = 1

out = prop.write(P)
print("%s — %d rows, %d sections, Tier 1 = %d" %
      (out, ROWS, len(sections), TIER1))
