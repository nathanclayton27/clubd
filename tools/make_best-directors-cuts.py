#!/usr/bin/env python3
"""Generate properties/best-directors-cuts.json.

    python tools/make_best-directors-cuts.py

Films whose later cut is the one to watch — nineteen of them, oldest first,
each weighed at the length of the cut rather than the length of the release.

The gate
--------
"Better" is an opinion, and this catalogue does not ship opinions typed from
memory, so the list is gated the way the FPS canon is gated on published
best-of lists. A film gets a row only if **English Wikipedia says, in a
sentence you can point at, that the later cut was better received than the
release it replaced** — better/warmer reviews, "superior", "an improvement",
"the definitive version", or a documented reappraisal the article attributes
to the cut. The sentence may come from the film's own article, from the
article about the cut, or from Wikipedia's "Director's cut" article; nowhere
else counts.

That sentence is not a footnote here, it is the data. Every row in
tools/data/directors-cuts.json carries `quote` (the verdict) and `evidence`
(the whole paragraph it was lifted out of), plus `mins` and `mins_evidence`
for the runtime; this generator re-asserts, on every run, that the quote is
still inside its evidence and that the runtime is still inside its own. A row
whose source stops saying what it said fails the build instead of quietly
shipping a claim nobody can check. scratch/agent-cuts/ holds the collector.

What the gate threw out
-----------------------
Famous cuts that everyone "knows" are better, whose articles do not say so:

  * Aliens (1986) — Cameron calls the 157-minute extended edition his
    preferred version and the article stops there. A director preferring his
    own cut is not a reception claim, and Cameron elsewhere says the
    theatrical release IS his director's cut.
  * Dark City (1998) — the article documents New Line demanding the opening
    narration and the 2008 cut removing it, and never rules on either.
  * Das Boot (1981), Little Shop of Horrors (1986), Legend (1985),
    Nightbreed (1990), The New World (2005), Troy (2004) — a cut exists, the
    article describes it, no comparison is made.
  * Close Encounters of the Third Kind (1977) — Ebert called the 1980 recut
    "quite simply, a better film", but that is a version Spielberg himself
    replaced in 1998 and whose ending the article says the studio demanded.
    The 1998 cut he calls definitive carries no comparative reception.
  * Superman II (1980) — the Donner Cut splits the article down the middle:
    Screen Rant calls it superior, one book calls it "neither a better nor a
    worse film", The A.V. Club calls it "a curio, not a corrective".
  * Highlander II (1991) — one reviewer calls the Special Edition "infinitely
    superior", IGN gives it 2/10, and Mulcahy says he was not involved.
  * Until the End of the World (1991) — the one favourable-to-the-cut
    sentence carries a citation-needed tag, which is Wikipedia saying it is
    unsourced.
  * American History X, Event Horizon, Gangs of New York, The 13th Warrior,
    Fantastic Four (2015), Suicide Squad (2016), The Golden Compass,
    Dune (1984), The Keep — the director's cut was never released, or the
    footage is gone, so there is nothing to watch.

And one that passed the verdict and lost on arithmetic: **Daredevil (2003)**,
whose article says plainly that "reviews were more positive than for the
theatrical version" — but nobody publishes how long its director's cut runs.
This list is weighted on the cut, weighting is all-or-nothing, and the house
rule is never to guess a runtime, so the row is not here. It is named in the
property notes rather than dropped silently.

Weights
-------
Hours are the runtime of the CUT, following the standing ruling on Kingdom of
Heaven: the 190-minute director's cut is the film, wherever it appears in this
catalogue. Sixteen runtimes come from a figure in the film's own article
(usually the infobox, which carries both lengths); three — Kingdom of Heaven,
Watchmen, Batman v Superman — come from Wikidata's P2047 qualified
P518=Q240862 ("director's cut") or its Ultimate Edition equivalent, which is
where the 190 in ridley-scott came from too.

Titles, and why they are stated rather than derived
---------------------------------------------------
A row here displays the CUT's title, never the film's. That is not cosmetic:
cross-list sync keys on normalised title + year + medium, so a row on a cuts
list titled with the bare film name is the same work as the theatrical copy on
every other list. That is the bug that produced the rule — unticking the E.T.
director's cut unticked E.T., and somebody lost a true record of something they
had watched. Naming the cut is the whole fix.

The names cannot be computed from the data. Three cuts were released under
their own title (Rocky vs. Drago, The Godfather Coda, Zack Snyder's Justice
League), several are the film plus a real released subtitle (Blade Runner: The
Final Cut, Alexander: The Ultimate Cut), and the rest are the film plus a
parenthetical. So CUT_TITLES states all nineteen, and the build asserts on
every run that each one is either the cut's own title or the film's title
extended. That assert is the point of it: the titles were once added to the
shipped JSON by hand and this generator went on emitting bare film names, so a
rebuild would have stripped all nineteen back and the diff would have read as a
tidy-up (CLU-448).

The YEAR on a row is still the film's ORIGINAL release year, and the weight is
still the length of the cut. Kingdom of Heaven is the one row that keeps its
pair on purpose: ridley-scott carries the same "Kingdom of Heaven (Director's
Cut)" title, so those two rows are the same work and go on syncing.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop as P  # noqa: E402

SLUG = "best-directors-cuts"
SIBLING = "worst-directors-cuts"
DATA = pathlib.Path(__file__).resolve().parent / "data" / "directors-cuts.json"

# The coded half of the gate. A verdict has to actually say better, in one of
# the ways English says it; a sentence that merely describes a cut does not
# get a film onto a list called "the ones that improve the film".
VERDICT = re.compile(
    r"better|superior|improve|warmer|definitive|acclaim|elevat|reevaluat|"
    r"re-evaluat|reapprais|more coherent|positive|prais", re.I)

# The displayed title of each row: the title of the CUT, which is what makes a
# row on this list a different film from the theatrical copy elsewhere in the
# catalogue. Stated, not derived — see the docstring — and checked below. It
# lives here rather than in tools/data/directors-cuts.json because that file is
# collector output (scratch/agent-cuts/build_data.py rewrites it wholesale) and
# an editorial title put there would be lost the next time the cuts are
# re-collected.
CUT_TITLES = {
    "Touch of Evil": "Touch of Evil (Walter Murch's Re-edit)",
    "Major Dundee": "Major Dundee (The Restored Extended Cut)",
    "The Wild Bunch": "The Wild Bunch (The Original Director's Cut)",
    "Pat Garrett and Billy the Kid":
        "Pat Garrett and Billy the Kid (Peckinpah's Preview Version)",
    "Star Trek: The Motion Picture":
        "Star Trek: The Motion Picture (The Director's Edition)",
    "The Big Red One": "The Big Red One: The Reconstruction",
    "Heaven's Gate": "Heaven's Gate (The Restored Director's Cut)",
    "Blade Runner": "Blade Runner: The Final Cut",
    "Once Upon a Time in America":
        "Once Upon a Time in America (Leone's Full Length)",
    "Rocky IV": "Rocky vs. Drago: The Ultimate Director's Cut",
    "The Abyss": "The Abyss (Special Edition)",
    "The Godfather Part III":
        "The Godfather Coda: The Death of Michael Corleone",
    "Alien 3": "Alien 3 (The Assembly Cut)",
    "Payback": "Payback: Straight Up - The Director's Cut",
    "Alexander": "Alexander: The Ultimate Cut",
    "Kingdom of Heaven": "Kingdom of Heaven (Director's Cut)",
    "Watchmen": "Watchmen (Director's Cut)",
    "Batman v Superman: Dawn of Justice":
        "Batman v Superman: Dawn of Justice (Ultimate Edition)",
    "Justice League": "Zack Snyder's Justice League",
}

ERAS = [
    ("vault", "Rescued from the vault", None, 1980,
     "Films a studio took off its director and shortened, put back together a "
     "long time afterwards. Nothing here was rescued inside a decade and most "
     "of it took twenty years or more, by which point the long version is the "
     "one the write-ups mean."),
    ("video", "The home-video era", 1981, 1999,
     "Laserdisc and then DVD made a second version something you could sell, "
     "and these are the ones where the second version is the film. The range "
     "of what that means is the point: a restored epic just short of four "
     "hours, a sequel re-cut and re-titled thirty years later, and a boxing "
     "film reassembled by its own star."),
    ("modern", "The modern recut", 2000, None,
     "The cut as part of the release plan rather than an apology for it. "
     "Length and ratings do most of the work here, and one of these was "
     "finished four years late by a director the studio had already replaced."),
]


def main():
    doc = json.loads(DATA.read_text(encoding="utf-8"))
    films = doc["films"]
    mine = [f for f in films if f["list"] == "best"]
    theirs = [f for f in films if f["list"] == "worst"]
    assert mine and theirs, "the data file lost one of the two lists"

    # ---- disjointness, twice: once against the shared data file, once
    # against whatever the sibling property actually shipped. A film belongs
    # to exactly one of these lists or the pair is incoherent.
    keys = {(f["t"], f["n"]) for f in mine}
    clash = keys & {(f["t"], f["n"]) for f in theirs}
    assert not clash, "on both lists in the data file: %s" % sorted(clash)
    sib = P.ROOT / "properties" / ("%s.json" % SIBLING)
    if sib.exists():
        # keyed on the ROW ID, not the displayed title: both lists now title a
        # row with the cut rather than the film, so comparing film names
        # against what shipped would compare two different things and never
        # fire. The id is "<prefix>-<year>-<slug of the film>" on both lists.
        other = json.loads(sib.read_text(encoding="utf-8"))
        shipped = {tuple(x["id"].split("-", 2)[1:]) for s in other["sections"]
                   for x in s["items"]}
        clash = {(str(n), P.slug(t)) for t, n in keys} & shipped
        assert not clash, "%s already ships: %s" % (SIBLING, sorted(clash))

    # ---- the gate, re-asserted on every run
    for f in mine:
        assert f["quote"] in f["evidence"], \
            "%s: the verdict is no longer in its own evidence" % f["t"]
        assert VERDICT.search(f["quote"]), \
            "%s: %r is not a verdict, it is a description" % (f["t"], f["quote"])
        assert f["mins"], "%s: a weighted list cannot carry a row with no " \
                          "runtime (see the module docstring)" % f["t"]
        assert str(f["mins"]) in f["mins_evidence"], \
            "%s: %d min is not in the text it came from" % (f["t"], f["mins"])

    # ---- the naming rule, re-asserted on every run. A row on a list ABOUT
    # cuts must display the cut, and a cut's title is either its own release
    # title or the film's title extended. Anything else — the bare film name
    # above all — fails the build rather than shipping a row that shares an
    # identity with the theatrical copy on some other list.
    stray = set(CUT_TITLES) - {f["t"] for f in mine}
    assert not stray, \
        "CUT_TITLES names a film this list does not carry: %s" % sorted(stray)
    for f in mine:
        disp = CUT_TITLES.get(f["t"])
        assert disp, \
            "%s: no cut title. A cuts list must name the cut on the row; " \
            "the bare film name makes it the same work as the theatrical " \
            "copy elsewhere in the catalogue" % f["t"]
        own_title = P.normt(disp) == P.normt(f["cut"])
        extended = (disp.startswith(f["t"] + " (") and disp.endswith(")")) \
            or disp.startswith(f["t"] + ": ")
        assert own_title or extended, \
            "%s: %r names neither the cut (%r) nor the film extended" \
            % (f["t"], disp, f["cut"])

    mine.sort(key=lambda f: (f["n"], P.normt(f["t"])))

    sections = []
    for key, title, lo, hi, intro in ERAS:
        got = [f for f in mine
               if (lo is None or f["n"] >= lo) and (hi is None or f["n"] <= hi)]
        assert got, "empty era %s" % key
        items = []
        for f in got:
            cut = f["cut"][0].upper() + f["cut"][1:]
            if f["cut_year"]:
                cut = "%s, %d" % (cut, f["cut_year"])
            items.append({
                # the id stays keyed on the FILM, because ids are where ticks
                # are stored; only the displayed title carries the cut
                "id": "bdc-%d-%s" % (f["n"], P.slug(f["t"])),
                "t": CUT_TITLES[f["t"]], "n": str(f["n"]),
                "w": round(f["mins"] / 60.0, 2),
                "note": P.join_bits(cut, f["changes"], "%d min" % f["mins"]),
            })
        hours = sum(x["w"] for x in items)
        sections.append({
            "id": key, "title": title,
            "sub": "%d–%d · %d films · %d hours"
                   % (got[0]["n"], got[-1]["n"], len(got), round(hours)),
            "intro": intro, "items": items})
    sections[0]["open"] = True

    rows = [x for s in sections for x in s["items"]]
    assert len(rows) == len(mine) == 19, len(rows)
    # the notes quote 144 as the theatrical length; it rides on the same
    # Wikidata statement the 190 came from, so assert it rather than trust it
    koh = next(f for f in mine if f["t"] == "Kingdom of Heaven")
    assert "144 minutes (P518=Q26225765, theatrical release)" in koh["mins_evidence"]
    # the vault section's intro claims nothing there was rescued inside a
    # decade and that most of it took twenty years or more
    gaps = sorted(f["cut_year"] - f["n"] for f in mine
                  if f["n"] <= 1980 and f["cut_year"])
    assert len(gaps) == 7 and min(gaps) >= 10 and \
        sum(1 for g in gaps if g >= 20) > len(gaps) / 2, gaps
    total = sum(x["w"] for x in rows)
    # the prose below names films, not cuts, so these read from the data rows
    # rather than from the items, whose titles are now the cuts'
    hrs = {f["t"]: round(f["mins"] / 60.0, 2) for f in mine}
    longest = max(mine, key=lambda f: f["mins"])
    shortest = min(mine, key=lambda f: f["mins"])
    wikidata = sum(1 for f in mine if f["mins_src"] == "wikidata")

    prop = {
        "slug": SLUG,
        "title": "Best Director's Cuts",
        "subtitle": "the version that is the film, and the receipts",
        "kind": "films",
        # A thematic survey of films most people already know, for people who
        # care which version they are watching — the 25–39 band. A shade above
        # Time Loops (36) is too high: "director's cut" is a familiar phrase
        # but a list OF them is a film-buff object. It sits beside Body Swap
        # (34) and above its own sibling, which carries five rows to these
        # nineteen.
        "popularity": 35,
        "year": "1958–2017",
        "blurb": "%d films where a later cut is the one to watch — about %d "
                 "hours, every bar measuring the cut and not the release. A "
                 "row exists only where Wikipedia says the cut landed better."
                 % (len(rows), round(total)),
        "unit": {"one": "cut", "many": "cuts"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": "#8F5A00",
        "accentDark": "#F0B84A",
        "tiers": False,
        "random": True,
        "notes": [
            ["What earns a row.",
             "Wikipedia has to say, in a sentence you can point at, that the "
             "later cut was better received than the release it replaced — "
             "better or warmer reviews, “superior”, “an improvement”, “the "
             "definitive version”, or a reappraisal it credits to the cut. "
             "The sentence can come from the film's article, from the article "
             "about the cut, or from Wikipedia's “Director's cut” page. "
             "Nothing here is on the list because everyone knows it belongs; "
             "the verdict and the paragraph around it are stored with the row "
             "and re-checked every time this list is rebuilt."],
            ["The bar is the cut, not the film.",
             "Every runtime here is the length of the version being "
             "recommended, which is why Kingdom of Heaven weighs %s hours "
             "rather than the 144 minutes cinemas got. That follows the house "
             "ruling on that film, and it applies to all %d rows. %d of the "
             "runtimes come from a figure in the film's own article — the "
             "infobox usually carries both lengths — and %d from Wikidata's "
             "runtime statements tagged as the director's cut."
             % (("%.2f" % hrs["Kingdom of Heaven"]).rstrip("0"),
                len(rows), len(rows) - wikidata, wikidata)],
            ["Same film, one row.",
             "A film that exists in several versions still gets a single row, "
             "because you do not watch it twice and because rows pair across "
             "the catalogue by title and release year. The year on the row is "
             "the film's original year; the cut's own year and length are in "
             "the note. Tick Kingdom of Heaven here and it ticks in the "
             "Ridley Scott list too."],
            ["Longest, shortest, and the odd one out.",
             "%s runs %s hours, the longest thing on the list by some "
             "distance. %s is the shortest at %s hours — and it is the rare "
             "director's cut that runs shorter than the release rather than "
             "longer, which is the whole reason it is interesting."
             % (longest["t"],
                ("%.2f" % hrs[longest["t"]]).rstrip("0").rstrip("."),
                shortest["t"],
                ("%.2f" % hrs[shortest["t"]]).rstrip("0").rstrip("."))],
            ["One film passed and is still not here.",
             "Daredevil (2003). Its article says outright that “reviews were "
             "more positive than for the theatrical version” for the 2004 "
             "R-rated cut, so it passes the gate cleanly — but no source "
             "publishes how long that cut runs, and this list is weighted on "
             "the cut. Weights are all-or-nothing: one row without a number "
             "would silently count as an hour and skew every figure above. "
             "Guessing the runtime was the other option and it is not one we "
             "take. Same reason a few obvious names are missing: Aliens, Dark "
             "City, Das Boot and Legend all have a later cut their director "
             "made or supervised, and no published verdict on how it landed."],
            "Verdicts and runtimes read from English Wikipedia — the film "
             "articles, the articles about individual cuts, and the "
             "“Director's cut” and “List of films cut over the director's "
             "opposition” pages — with three runtimes from Wikidata's P2047 "
             "statements qualified as the director's cut.",
        ],
        "sections": sections,
    }

    P.write(prop)

    print("wrote %s.json" % SLUG)
    print("  %d films · %d hours · %d sections"
          % (len(rows), round(total), len(sections)))
    print("  gate: a Wikipedia sentence saying the cut landed better; "
          "%d/%d runtimes from Wikidata" % (wikidata, len(rows)))
    for s in sections:
        print("   %-24s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
