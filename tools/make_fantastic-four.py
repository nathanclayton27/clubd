#!/usr/bin/env python3
"""Generate properties/fantastic-four.json — #1 to #569.

    python tools/make_fantastic-four.py

Every issue of the Fantastic Four from November 1961 up to, but not including,
Fantastic Four #570. That last part is the whole point of where this stops:
#570 is the first issue of Jonathan Hickman's run, and Hickman's run is
already a list here — `hickman-secret-wars`, 250 issues of it. Duplicating
those rows would give a reader two half-ticked copies of the same comics, so
this list ends one issue short and hands over. The check at the bottom asserts
the handover really is clean: not one (series, issue) pair appears on both.

WHERE THE SECTIONS COME FROM. Not from memory. tools/data/fantastic-four.json
is the credits block of every issue page on Marvel Database, read through its
API, and the section boundaries below are asserted against it — Kirby pencils
#1 to #102 and then stops, Byrne writes #232 to #294, Millar writes the
sixteen issues that end at #569, Hickman writes #570. If the source ever
disagrees with one of those, this refuses to build rather than shipping a
section whose title is a lie.

WHY THERE ARE NO WEIGHTS. Comics publish no per-issue reading time and this
catalogue does not invent one. Every row here is unweighted, like every other
comics list.

WHAT THE STARS MEAN. They are derived, not chosen. Marvel Database records
first appearances issue by issue with a {{1st}} marker; the extract pairs each
one with the number of issues across these volumes that link that character at
all. A debut of someone the book kept using earns a star. It is a mechanical
rule and it has mechanical results — it stars the issue that introduced the
Baxter Building's receptionist and gives the Black Panther's debut the same
one star as Blastaar's — but it is honest about what it measures, which a
hand-picked list of "great issues" would not be.

NOTES SAY WHAT AN ISSUE IS. A debut, a creator arriving or leaving, a
numbering change. Never what happens in it.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "tools" / "data" / "fantastic-four.json")
                  .read_text(encoding="utf-8"))
ISSUES = DATA["issues"]

SLUG = "fantastic-four"
HANDOFF = "hickman-secret-wars"
LAST = 569              # the last issue before Hickman
V3_RESUME = 500         # where legacy numbering comes back

MARVEL_V1 = "https://www.marvel.com/comics/series/2121/fantastic_four_1961_-_1998"
MARVEL_V3 = "https://www.marvel.com/comics/series/421/fantastic_four_(1998_-_2012)"
MDB = "https://marvel.fandom.com/wiki/Fantastic_Four_%s"

# ------------------------------------------------------------------ debut rules
STAR_1 = 20     # the character turns up in at least this many issues of the book
STAR_2 = 70
# Suppressed debuts, each for a stated reason rather than taste:
#   * placeholders — the wiki names a character it has no name for.
#   * a later {{1st}} on a name already used earlier in the list. Marvel
#     Database marks FF #265 as a first appearance of "Alicia Masters"; Alicia
#     debuts at #8, and printing both would read as an error.
#   * "Valeria von Doom" at Vol 3 #15, where the surname is the reveal and the
#     character is introduced under a different name entirely.
#   * "House of Agon" at #45 — the Inhuman royal family's name, listed in the
#     same issue as five of the people in it, which the row already names.
SKIP_DEBUT = ("Unnamed", "Impostor", "Valeria von Doom", "House of Agon")


def debuts_for(rec, used):
    """Kept debut labels for an issue, newest names only."""
    out = []
    for labelx, count in rec["debuts"]:
        if count < STAR_1 or any(s in labelx for s in SKIP_DEBUT):
            continue
        if any(labelx.startswith(u + " ") or u.startswith(labelx + " ")
               or labelx == u for u in used):
            continue
        used.add(labelx)
        out.append((labelx, count))
    return out


# The wiki stores an epithet as a bare noun phrase. On a row it wants its
# article back; these are the only labels in the whole list that need one.
ARTICLE = {"Fantastic Four", "Frightful Four", "Watcher", "Puppet Master",
           "Mad Thinker", "Super-Skrull", "Impossible Man", "Silver Surfer",
           "Black Panther", "Dragon Man", "Thing", "Invisible Girl",
           "Human Torch"}


def debut_note(kept):
    names = [("the " + k[0]) if k[0] in ARTICLE else k[0] for k in kept][:5]
    if len(names) == 1:
        who = names[0]
    else:
        who = ", ".join(names[:-1]) + " and " + names[-1]
    return "first appearance of " + who


# ------------------------------------------------------------------- selection
def main_series(rec):
    return not rec["annual"] and not rec["unlimited"]


def legacy(rec):
    """The continuous number. Vol 1 ran to #416 and Heroes Reborn added 13, so
    Vol 3 #1 is #430 — which is why Vol 3 #70 could be followed by #500."""
    if not main_series(rec):
        return None
    if rec["vol"] == 2:
        return 416 + int(rec["num"])
    return rec["legacy"]


RUN = [r for r in ISSUES if main_series(r)
       and legacy(r) is not None and legacy(r) <= LAST]
RUN.sort(key=lambda r: legacy(r))
HALF = [r for r in ISSUES if r["vol"] == 3 and r["num"] == "½"]
ANNUALS = {int(r["num"]): r for r in ISSUES
           if r["annual"] and r["num"].isdigit() and int(r["num"]) < 100}

assert len(HALF) == 1, "expected exactly one ½ issue, found %d" % len(HALF)
assert [legacy(r) for r in RUN] == list(range(1, LAST + 1)), \
    "the run is not contiguous 1..%d — %d rows" % (LAST, len(RUN))


def band(lo, hi):
    return [r for r in RUN if lo <= legacy(r) <= hi]


def cover(rec):
    return rec["year"]


def yrs(recs):
    a, b = cover(recs[0]), cover(recs[-1])
    return str(a) if a == b else "%d–%d" % (a, b)


def printed(rec):
    """The issue number as it appears on the cover."""
    return "#%s" % rec["num"]


def series_of(rec):
    """What goes in the title column.

    Three volumes have an issue #1 and two of them have an issue #12, so the
    two relaunches carry their year the way the S.H.I.E.L.D. volumes do on the
    Secret Wars list. From #500 on there is nothing to disambiguate — the 1998
    volume went back to the legacy count — so those rows are plain, which is
    also what makes the overlap check against that list mean anything.
    """
    if rec["annual"]:
        return "Fantastic Four Annual"
    if rec["vol"] == 2:
        return "Fantastic Four (1996)"
    if rec["vol"] == 3 and (not rec["num"].isdigit()
                            or int(rec["num"]) < V3_RESUME):
        return "Fantastic Four (1998)"
    return "Fantastic Four"


WORDS = {n: w for n, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve "
    "thirteen fourteen fifteen sixteen seventeen eighteen nineteen "
    "twenty".split())}


def writers_in(recs):
    """Distinct lead writers across a stretch, in order of first credit."""
    out = []
    for r in recs:
        w = r["writers"][0] if r["writers"] else ""
        if w and w not in out:
            out.append(w)
    return out


# ------------------------------------------------------- boundary assertions
def lead(n, field):
    r = next(x for x in ISSUES if main_series(x) and legacy(x) == n)
    return (r[field] or [""])[0]


HICKMAN_FIRST = next(x for x in ISSUES if x["vol"] == 3 and x["num"] == "570")
assert lead(1, "pencilers") == "Jack Kirby" and lead(102, "pencilers") == "Jack Kirby", \
    "Kirby is meant to pencil #1 and #102"
assert lead(103, "pencilers") != "Jack Kirby", "Kirby is meant to be gone by #103"
assert lead(232, "writers") == "John Byrne" and lead(294, "writers") == "John Byrne", \
    "Byrne is meant to write #232 and #294"
assert lead(295, "writers") != "John Byrne", "Byrne is meant to be gone by #295"
assert lead(554, "writers") == "Mark Millar" and lead(LAST, "writers") == "Mark Millar", \
    "Millar is meant to write #554 and #%d" % LAST
assert HICKMAN_FIRST["writers"][0] == "Jonathan Hickman", \
    "#570 is meant to be Hickman's first — the handover is the shape of this list"
assert lead(430, "writers") and legacy(
    next(x for x in ISSUES if x["vol"] == 3 and x["num"] == "70")) == 499, \
    "Vol 3 #70 is meant to be legacy #499, one short of the resumed #500"

KIRBY_ENCORE = [legacy(r) for r in band(103, 231)
                if (r["pencilers"] or [""])[0] == "Jack Kirby"]
assert KIRBY_ENCORE == [108], \
    "expected Kirby's one post-run issue to be #108, got %s" % KIRBY_ENCORE
BYRNE_ART = [legacy(r) for r in band(103, 231)
             if (r["pencilers"] or [""])[0] == "John Byrne"]
assert BYRNE_ART == list(range(209, 219)) + [220, 221], \
    "expected Byrne to draw #209-218 and #220-221 before the run, got %s" % BYRNE_ART

# ------------------------------------------------------------------- row notes
MILESTONE = {
    102: "Kirby's last issue",
    108: "Kirby pencils one more, six issues after he left",
    209: "John Byrne starts drawing it",
    416: "the last issue of the original numbering",
    429: "the last of the Heroes Reborn year",
    499: "printed as #70 — the next issue is #500",
    500: "legacy numbering resumes",
    LAST: "the last issue before Hickman",
}


def row(rec, used, opt=0):
    n = legacy(rec)
    kept = debuts_for(rec, used)
    bits = []
    if kept:
        bits.append(debut_note(kept))
    if n in MILESTONE:
        bits.append(MILESTONE[n])
    star = 0
    if kept:
        star = 2 if max(k[1] for k in kept) >= STAR_2 else 1
    # ids are the continuous number, never the printed one: three volumes have
    # an issue #1 and a tick is stored against the id forever.
    if rec["annual"]:
        ident = "ffa-%s" % rec["num"]
    elif n is None:
        ident = "ff-half"
    else:
        ident = "ff-%d" % n
    return {"id": prop.slug(ident), "t": series_of(rec), "n": printed(rec),
            "note": prop.join_bits(*bits), "star": star, "opt": opt, "url": ""}


def links(*pairs):
    return [{"label": a, "url": b} for a, b in pairs]


V1_LINKS = links(("The series", MARVEL_V1), ("Issue list", MDB % "Vol_1"))
V2_LINKS = links(("Issue list", MDB % "Vol_2"))
V3_LINKS = links(("The series", MARVEL_V3), ("Issue list", MDB % "Vol_3"))
ANN_LINKS = links(("Issue list", MDB % "Annual_Vol_1"))

# ------------------------------------------------------------------- sections
USED = set()
SECTIONS = []


def section(sid, title, tier, recs, sub_tail, intro, sect_links, opt=0, rng=None):
    items = [row(r, USED, opt) for r in recs]
    if rng is None:
        # the ½ issue has no place in a range, and neither does a section whose
        # covers change numbering partway through — those pass `rng` instead.
        numbered = [r for r in recs if legacy(r) is not None or r["annual"]]
        first, last = printed(numbered[0]), printed(numbered[-1])
        rng = first if first == last else "%s–%s" % (first, last.lstrip("#"))
    sub = prop.join_bits(rng, yrs(recs), sub_tail)
    SECTIONS.append({"id": sid, "title": title, "sub": sub, "tier": tier,
                     "intro": intro, "items": items, "links": sect_links})


section(
    "founding", "Lee & Kirby, the first three years", 1, band(1, 43),
    "where the Marvel Universe starts",
    "Almost everything Marvel would go on to be gets invented inside these "
    "forty-three issues, and you can watch it happen: a monster comic that "
    "keeps discovering it is something else. The Skrulls, Doctor Doom, the "
    "Watcher, the Sub-Mariner's return, the first supervillain team — all of "
    "it is here, and most of it arrives by accident.\n\n"
    "It is also 1961. The pacing is loud and the dialogue explains itself. "
    "That settles down.",
    V1_LINKS)

section(
    "imperial", "Lee & Kirby, the imperial run", 1, band(44, 102),
    "the reason people talk about this book",
    "The stretch everything else in superhero comics is measured against. "
    "Kirby is drawing at full power, the scale gets absurd and stays coherent, "
    "and the book introduces more durable ideas in three years than most "
    "titles manage in forty.\n\n"
    "If you only ever read one run of Fantastic Four, read this one. "
    "Starting here rather than at #1 also works — the team is established by "
    "now and nothing earlier is required.",
    V1_LINKS)

section(
    "annuals", "The annuals Kirby drew", 2,
    [ANNUALS[i] for i in range(1, 7)],
    "double-length, and inside the run above",
    "Six annuals, all of them Lee and Kirby, published alongside the run "
    "above and set among it. Longer than a monthly issue and not filler: two "
    "of the six are among the most consequential things this book ever "
    "printed.\n\n"
    "The annuals after these are other people's, and they are not here.",
    ANN_LINKS)

section(
    "afterkirby", "After Kirby", 3, band(103, 190),
    "%s writers, no run" % WORDS[len(writers_in(band(103, 190)))],
    "Kirby leaves and the book spends most of a decade looking for a "
    "replacement. There are good issues in here and there is no run. Nothing "
    "later depends on any of it, so dip in or skip it outright — the tier "
    "means what it says.",
    V1_LINKS)

section(
    "wolfman", "Wolfman, Moench, and Byrne arriving", 3, band(191, 231),
    "the approach to the run below",
    "Two things worth knowing about this stretch. Marv Wolfman writes it for "
    "three years, and John Byrne turns up as a penciller long before he takes "
    "the book over: he draws #209–218, then writes and draws #220–221, a year "
    "ahead of #232.",
    V1_LINKS)

section(
    "byrne", "John Byrne", 1, band(232, 294),
    "one voice, writing and drawing",
    "The other essential run, and the one that proved the book could be "
    "revived rather than continued. Byrne wrote and drew almost all of it. He "
    "went back into what Lee and Kirby had built instead of around it, gave "
    "every member of the team something to do, and changed the roster while "
    "he was at it — this book has never been four fixed people, and Byrne is "
    "where that becomes a feature.\n\n"
    "Sixty-three issues. It is the cleanest single-creator run Marvel has.",
    V1_LINKS)

section(
    "byrneannuals", "Byrne's annuals", 3,
    [ANNUALS[i] for i in (17, 18, 19)],
    "alongside the run above",
    "Three annuals from the Byrne years. Optional, and they read fine after "
    "the run rather than inside it.",
    ANN_LINKS, opt=1)

section(
    "eighties", "Stern, Englehart, and the drop", 3, band(295, 333),
    "three years without a direction",
    "Byrne leaves and the book does not recover for three years. Roger Stern "
    "has a short go, then Steve Englehart gets twenty-five issues — and signs "
    "his last five 'John Harkness' rather than with his own name, which is "
    "how the credits read to this day.",
    V1_LINKS)

section(
    "simonson", "Walt Simonson", 2, band(334, 354),
    "short, strange, very good",
    "Twenty-one issues written by Walt Simonson and mostly drawn by him too, "
    "and unlike anything on either side of it. It is the run nobody brings "
    "up, and it is the best thing in this list between Byrne and Waid.",
    V1_LINKS)

section(
    "defalco", "DeFalco & Ryan", 3, band(355, 416),
    "to the end of the original numbering",
    "Tom DeFalco and Paul Ryan take the book from 1991 to the end of Vol 1. "
    "Sixty-two issues, nineties to the bone.",
    V1_LINKS)

section(
    "reborn", "Heroes Reborn", 3, band(417, 429),
    "the year the book was handed out",
    "Marvel gave the title to Jim Lee's studio for a year and relaunched it "
    "at #1, then took it back. Thirteen issues, and the legacy count keeps "
    "them — which is the arithmetic that lets the 1998 relaunch reach #500 "
    "two issues after its own #70.",
    V2_LINKS)

section(
    "relaunch", "Lobdell, Claremont & Larroca", 3,
    band(430, 432) + HALF + band(433, 463),
    "a new #1 in 1998",
    "The second relaunch, and the second new #1. Scott Lobdell opens it, "
    "Chris Claremont writes most of it with Salvador Larroca, and it is "
    "perfectly fine.\n\n"
    "The fourth row is an issue numbered ½, sitting at the cover date it was "
    "published under and outside the numbering entirely.",
    V3_LINKS)

section(
    "pacheco", "Pacheco & Marín", 3, band(464, 488),
    "co-written by the artist",
    "Carlos Pacheco draws it and co-writes it with Rafael Marín. It looks "
    "superb and it is the first stretch since Simonson with a plan.",
    V3_LINKS)

section(
    "waid", "Waid & Wieringo", 2, band(489, 524),
    "one run, two numberings",
    "The best Fantastic Four anyone wrote between Byrne and Hickman, and the "
    "shortest way into the modern book if you would rather not start in 1961.\n\n"
    "The numbering jumps in the middle of it: the run starts at a fresh #60 "
    "and the covers go back to the legacy count partway through, so #70 is "
    "followed by #500 with no gap in the story at all.",
    V3_LINKS, rng="#60–70, then #500–524")

section(
    "mcduffie", "Straczynski, Kesel & McDuffie", 3, band(525, 553),
    "three writers, no handover",
    "J. Michael Straczynski, then Karl Kesel for two, then Dwayne McDuffie. "
    "Twenty-nine issues that lead nowhere in particular, which is unlucky, "
    "because what comes next leads everywhere.",
    V3_LINKS)

section(
    "millar", "Millar & Hitch, the handover", 2, band(554, LAST),
    "the sixteen issues before #570",
    "Mark Millar and Bryan Hitch get sixteen issues, and then the book "
    "changes hands for the last time this list covers.\n\n"
    "#569 is where this stops. The next issue, Fantastic Four #570, is the "
    "first page of Jonathan Hickman's run — and that is a list of its own "
    "here, Everything Dies: Secret Wars, 250 issues from #570 to the end of "
    "everything. You do not need these sixteen to start it; that list opens "
    "cold on purpose. They are simply what the book was doing the month "
    "before.",
    V3_LINKS)

# ------------------------------------------------------------------ the property
ALL = [x for s in SECTIONS for x in s["items"]]
PROPERTY = {
    "slug": SLUG,
    "title": "Fantastic Four",
    "subtitle": "Marvel's main continuity, #1 to #569 — the team, not the four people",
    "kind": "comics",
    "popularity": 68,
    "year": "1961–2009",
    "blurb": "Every issue from Fantastic Four #1 to #569, where Jonathan "
             "Hickman's run — and the Secret Wars list — begins.",
    "unit": {"one": "issue", "many": "issues"},
    "verb": {"base": "read", "past": "read", "ing": "reading"},
    "accent": "#1B4FA3",
    "accentDark": "#8FBEFF",
    "tiers": True,
    "notes": [
        ["Tiers.",
         "1 is essential — Lee & Kirby, and Byrne, which between them are the "
         "character. 2 is strongly recommended: the six annuals Kirby drew, "
         "Simonson, Waid & Wieringo, and the sixteen issues that hand the book "
         "over. 3 is everything else, and there is a great deal of it, because "
         "this book has been published continuously since 1961. The minimum "
         "viable path is Tier 1 alone."],
        ["Where this stops, and why.",
         "At #569. Fantastic Four #570 is Jonathan Hickman's first issue, and "
         "Hickman's run is already a list here — Everything Dies: Secret Wars, "
         "250 issues running from #570 to the end of the Marvel universe. Not "
         "one issue appears on both lists, so ticking your way through this one "
         "leaves you standing exactly where that one starts."],
        ["Marvel's main continuity, and one continuous count.",
         "One book, three volumes, one numbering. Vol 1 ran to #416, the "
         "Heroes Reborn year added thirteen, and the 1998 relaunch started "
         "again at #1 — which is why its #70 is followed by #500 rather than "
         "#71. The numbers on the rows are the ones printed on the covers; the "
         "count they belong to never restarts."],
        ["The team, not the four people.",
         "Members leave and are replaced, sometimes for years at a time, and "
         "the book follows whoever is in the Baxter Building rather than a "
         "fixed roster. Byrne is where that stops being an emergency and "
         "becomes how the title works."],
        ["Stars are derived, not chosen.",
         "Marvel Database records first appearances issue by issue. A star "
         "here means an issue introduced someone the book then kept using — at "
         "least twenty issues across these volumes, and two stars at seventy. "
         "It is a mechanical rule with mechanical results: it stars the debut "
         "of the Baxter Building's receptionist, and gives the Black Panther "
         "the same single star as Blastaar. It measures what it says it "
         "measures, which a list of somebody's favourite issues would not."],
        ["No reading times.",
         "Comics publish no per-issue reading time, so no row here carries "
         "one. Every comics list in this catalogue is unweighted for the same "
         "reason."],
        "Issue numbers, cover dates, credits and first appearances read from "
        "Marvel Database (marvel.fandom.com) through its API; the sections are "
        "drawn where the writer and penciller credits change, and the "
        "generator refuses to build if they have moved.",
    ],
    "sections": SECTIONS,
}

# ------------------------------------------------------------------- the checks
assert len(ALL) == len(RUN) + 1 + 9, \
    "expected %d rows, built %d" % (len(RUN) + 10, len(ALL))
assert all(not x.get("w") and "w" not in x for x in ALL), \
    "a weight got onto a comics row — CLU-131"

# The handover has to be real. Two lists offering the same issue would give a
# reader two half-ticked copies of it.
other = json.loads((ROOT / "properties" / ("%s.json" % HANDOFF))
                   .read_text(encoding="utf-8"))
theirs = {(x["t"], x["n"]) for s in other["sections"] for x in s["items"]}
mine = {(x["t"], x["n"]) for x in ALL}
overlap = sorted(mine & theirs)
assert not overlap, "these issues are on %s too: %s" % (HANDOFF, overlap[:6])
assert ("Fantastic Four", "#570") in theirs, \
    "%s no longer starts the Fantastic Four at #570 — recheck where this ends" % HANDOFF

tiers = {s["tier"] for s in SECTIONS}
assert tiers == {1, 2, 3}, "tiers used: %s" % sorted(tiers)

out = prop.write(PROPERTY)
t1 = sum(len(s["items"]) for s in SECTIONS if s["tier"] == 1)
print("wrote %s" % out)
print("  %d issues in %d sections — %d in Tier 1, %d starred"
      % (len(ALL), len(SECTIONS), t1, sum(1 for x in ALL if x["star"])))
print("  ends at #%d; %s starts at #570 with no overlap" % (LAST, HANDOFF))
