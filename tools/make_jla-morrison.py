#!/usr/bin/env python3
"""Generate properties/jla-morrison.json — Grant Morrison's JLA.

    PYTHONIOENCODING=utf-8 python tools/make_jla-morrison.py

Three Wikipedia pages, fetched through gwlib.wiki and cached under
scratch/jla-morrison/:

  * "JLA (comic book)" — the infobox creative-team field carries Morrison's
    issue ranges; the publication-history prose names every fill-in writer
    and the issues they took; the collected-editions list gives both the arc
    titles (the six trades) and the run's own boundary (the four Deluxe
    Edition hardcovers).
  * "Grant Morrison bibliography" — the two one-shots, JLA: Earth 2,
    JLA: Classified and DC One Million, each with its credits and year.
  * "Prometheus (DC Comics)" — the one-shot's date against JLA #16, which is
    the only reason this list can say where it goes.

Nothing here is typed from memory. Morrison's issues are stated twice in the
source, independently — infobox-minus-fill-ins, and the contents of the four
Deluxe hardcovers — and the two are asserted to agree before a row is written.
Every one-shot row asserts the sentence that credits it.

THE DECISION the run forces, made once and stated on the list: **if the run's
own Deluxe Editions collect it, it is on this list.** That takes in the Secret
Files short, the Prometheus and WildC.A.T.s one-shots, JLA #1,000,000,
JLA: Earth 2 and JLA: Classified #1-3. It leaves out Aztek, the other
thirty-odd #1,000,000 tie-ins, and JLA Secret Files & Origins #2 — which the
Strength in Numbers trade collects, but which Morrison's bibliography does not
claim. The one deliberate addition is DC One Million #1-4, marked optional,
because the JLA chapter is a chapter OF it.

Fill-in issues by other writers are left out rather than marked optional. They
are not this run, and a list that carried them would be lying about its subject.

Unweighted, like every comics list here: comics publish no per-issue reading
time, and a half-weighted list is worse than an unweighted one.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki  # noqa: E402

SLUG = "jla-morrison"
ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "scratch" / SLUG


def page(title):
    t = wiki.wikitext(title, cache_dir=str(CACHE))
    assert t, "wikipedia page did not come back: %s" % title
    return t


RANGE = re.compile(r"(\d+)\s*(?:[-–—]\s*(\d+))?")


def issues_in(fragment):
    """Issue numbers in a fragment like "1-17, 22-31, 34-41, 1,000,000"."""
    out = []
    if "1,000,000" in fragment:
        out.append(1000000)
        fragment = fragment.replace("1,000,000", " ")
    for a, b in RANGE.findall(fragment):
        a, b = int(a), int(b or a)
        assert 1 <= a <= b <= 125, \
            "implausible JLA issue range %r in %r" % ((a, b), fragment[:60])
        out.extend(range(a, b + 1))
    assert out, "no issue numbers in %r" % fragment[:60]
    return out


# ---------------------------------------------------------------- the run ---

JLA = page("JLA (comic book)")
BIB = page("Grant Morrison bibliography")
PROM = page("Prometheus (DC Comics)")

# 1. What the infobox credits Morrison with.
m = re.search(r"\[\[Grant Morrison\]\]\s*\(([^)]*)\)", JLA)
assert m, "the JLA infobox no longer credits Grant Morrison with a range"
CREDITED = set(issues_in(m.group(1)))

# 2. The fill-ins, from the publication-history prose. The infobox ranges
#    include them; this sentence is the only place the page says whose they
#    are, and the list's own copy quotes it, so it must keep parsing.
m = re.search(r"''JLA'' #(\d+)-#(\d+) and #(\d+) were written by \[\[Mark Waid\]\]",
              JLA)
assert m, "the Mark Waid fill-in sentence changed shape"
WAID = set(range(int(m.group(1)), int(m.group(2)) + 1)) | {int(m.group(3))}
m = re.search(r"\[\[Mark Millar\]\], \[\[Devin Grayson\]\] and Mark Waid, and "
              r"\[\[J\.M\. DeMatteis\]\] wrote issues #(\d+), (\d+) and (\d+), "
              r"respectively", JLA)
assert m, "the Millar/Grayson/DeMatteis fill-in sentence changed shape"
MILLAR, GRAYSON, DEMATTEIS = (int(g) for g in m.groups())
FILLINS = WAID | {MILLAR, GRAYSON, DEMATTEIS}

MORRISON = CREDITED - FILLINS
assert 1000000 in MORRISON, "JLA #1,000,000 fell out of the credited set"

# 3. The independent statement of the same thing: what the run's own Deluxe
#    hardcovers collect. If these two ever disagree, a person should look.
hc = JLA.split("'''Hardcovers'''")[1].split("'''Softcovers'''")[0]
DELUXE, vols = set(), 0
for line in hc.splitlines():
    # Only the numbered volumes. The fifth hardcover in this block is a Tower
    # of Babel collection of the fill-in issues and #43-46, which is exactly
    # the material this list excludes.
    if not re.search(r"''Vol\. \d''\s*\(collects ''JLA'' #", line):
        continue
    seg = line.split("(collects ''JLA'' #", 1)[1]
    seg = re.split(r"''|,\s*\d+\s*pages", seg)[0]
    DELUXE.update(issues_in(seg))
    vols += 1
assert vols == 4, "expected four Deluxe hardcovers, parsed %d" % vols
assert DELUXE == MORRISON, \
    "the two statements of Morrison's issues disagree: %s" % sorted(DELUXE ^ MORRISON)
assert len(MORRISON) == 34, "expected 34 Morrison issues, got %d" % len(MORRISON)

# 4. The arcs and their titles, from the trade paperback list. Asserting the
#    six tile #1-41 without a gap is what stops a renamed or dropped line from
#    quietly shortening the list.
ARCS = []
for line in JLA.splitlines():
    m = re.match(r"\*\s*''(.+?)''\s*\(collects ''JLA'' #(\d+)[-–](\d+)", line)
    if m:
        ARCS.append((re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]+)\]\]", r"\1", m.group(1)),
                     int(m.group(2)), int(m.group(3))))
ARCS = [a for a in ARCS if a[1] <= 41]
assert len(ARCS) == 6, "expected six Morrison-era trades, parsed %d" % len(ARCS)
assert ARCS[0][1] == 1 and ARCS[-1][2] == 41, "the trades no longer span #1-41"
for (_, _, end), (_, start, _) in zip(ARCS, ARCS[1:]):
    assert start == end + 1, "a gap between trades at #%d" % end
ARC = {t: (a, b) for t, a, b in ARCS}
for want in ("New World Order", "American Dreams", "Rock of Ages",
             "Strength in Numbers", "Justice for All", "World War III"):
    assert want in ARC, "trade %r is no longer in the collected-editions list" % want


# 5. The one-shots and the books either side of the run, each asserted against
#    the sentence in the bibliography that credits it.
def credited(fragment, what):
    assert fragment in BIB, "the bibliography no longer credits %s" % what


credited('"Star-Seed" short story (co-written by Morrison and Mark Millar',
         "the Star-Seed short")
credited("JLA Secret Files & Origins]]'' #1 (1997)", "JLA Secret Files & Origins #1")
credited("JLA/WildC.A.T.s]]'' one-shot (written by Morrison", "JLA/WildC.A.T.s")
credited("New Year's Evil: Prometheus]]'' one-shot (written by Morrison",
         "New Year's Evil: Prometheus")
credited("''[[JLA: Earth 2]]'' (with Frank Quitely, graphic novel", "JLA: Earth 2")
credited("''[[JLA: Classified]]'' #1–3 (with [[Ed McGuinness]], 2005)",
         "JLA: Classified #1-3")
credited("''[[DC One Million]]'' #1–4 (with Val Semeiks, 1998)",
         "DC One Million #1-4")

# Where the Prometheus one-shot goes. This sentence is the whole reason it is
# read before #16 rather than filed at the back with the other extras.
assert ("A new version of Prometheus debuted in ''New Year's Evil: Prometheus'' "
        "(February 1998) and returned in ''[[JLA (comic book)|JLA]]'' "
        "#16–17 (March–April 1998)") in PROM, \
    "the Prometheus debut sentence changed — the placement note is unsourced now"

# The two lead-in pages, which is why JLA #1,000,000 sits after #23.
assert ("the paperback version omits both this issue and the two lead-in pages "
        "from ''JLA'' #23") in BIB, "the #23 lead-in sentence changed"


# ------------------------------------------------------------------ rows ---

def row(rid, title, num, note="", star=0, opt=0):
    return {"id": rid, "t": title, "n": num, "note": note,
            "star": star, "opt": opt, "url": ""}


def jla_rows(lo, hi, notes=None, stars=None):
    """Every Morrison issue in #lo-#hi, in order, with the gaps simply absent."""
    notes, stars = notes or {}, stars or {}
    out = [row("jla-%d" % n, "JLA", "#%d" % n, notes.get(n, ""), stars.get(n, 0))
           for n in range(lo, hi + 1) if n in MORRISON]
    assert out, "no Morrison issues in #%d-#%d" % (lo, hi)
    return out


SECTIONS = [
    {
        "id": "nwo", "tier": 1, "title": "New World Order",
        "sub": "JLA #%d–%d · 1997 · the relaunch" % ARC["New World Order"],
        "intro":
            "Seven characters and a base on the Moon. DC had spent a decade "
            "rotating the League through spin-offs and second-stringers; the "
            "pitch here was to put the biggest names back on one team and size "
            "the threats against them. It became DC's best-selling book on the "
            "strength of it.\n\n"
            "Two of the seven seats are held by successors rather than the "
            "originals — Wally West is the Flash, Kyle Rayner is the Green "
            "Lantern. Beyond that there is nothing to catch up on. The team was "
            "reassembled a few months earlier in Justice League: A Midsummer's "
            "Nightmare, which is not Morrison's and is not on this list.",
        "items": jla_rows(*ARC["New World Order"],
                          notes={1: "the pitch, in four issues"}, stars={1: 2}),
    },
    {
        "id": "dreams", "tier": 1, "title": "American Dreams",
        "sub": "#%d–%d · mostly one-and-dones" % ARC["American Dreams"],
        "intro":
            "Shorter stories, and the stretch where the roster starts moving. "
            "The Secret Files short at the end is collected with #1–9 in the "
            "Deluxe Edition, which is why it sits here.",
        "items": jla_rows(*ARC["American Dreams"]) + [
            row("jla-secret-files-1", "JLA Secret Files & Origins", "#1",
                "the Star-Seed short, co-written with Mark Millar"),
        ],
    },
    {
        "id": "rock", "tier": 1, "title": "Rock of Ages",
        "sub": "#%d–%d · the arc people name" % ARC["Rock of Ages"],
        "intro":
            "Six issues, and the one most often pointed at when someone says "
            "this run is the good one. Judge the whole thing by it — if this "
            "does not land, the rest will not either.",
        "items": jla_rows(*ARC["Rock of Ages"], stars={ARC["Rock of Ages"][0]: 2}),
    },
    {
        "id": "oneshots", "tier": 2, "title": "Two one-shots",
        "sub": "1997–98 · collected with #10–17",
        "intro":
            "Both are Morrison's, and both are collected inside the run's own "
            "Deluxe Edition rather than alongside it. Prometheus came out in "
            "February 1998 and its villain turns up in JLA the month after, so "
            "it is read here rather than filed at the back.",
        "items": [
            row("new-years-evil-prometheus-1", "New Year's Evil: Prometheus", "#1",
                "Morrison with Arnie Jorgensen · the villain's first issue, "
                "a month before #16"),
            row("jla-wildcats-1", "JLA/WildC.A.T.s", "#1",
                "Morrison with Val Semeiks · a crossover with the WildStorm team"),
        ],
    },
    {
        "id": "strength", "tier": 1, "title": "Strength in Numbers",
        "sub": "#16–17 and #22–23 · the rest of the trade is other writers",
        "intro":
            "Morrison wrote #16–17 and #22–23. The four issues between "
            "them are Mark Waid's and are not on this list — the trade that "
            "collects this range carries all eight, so its contents and this "
            "section will not agree.",
        "items": jla_rows(*ARC["Strength in Numbers"]),
    },
    {
        "id": "million", "tier": 2, "title": "DC One Million",
        "sub": "November 1998 · #23 ends two pages into it",
        "intro":
            "For one month every DC title shipped an issue numbered #1,000,000, "
            "set in the 853rd century. Morrison wrote the four-issue core "
            "miniseries as well as the JLA chapter, and the last two pages of "
            "#23 lead into it.\n\n"
            "The JLA issue is the one the run's own collection keeps, so it is "
            "first here. The core four are marked optional: they are the "
            "crossover rather than the run, and the order they interleave with "
            "thirty-odd other tie-ins is not something this list tries to settle.",
        "items": [
            row("jla-1000000", "JLA", "#1,000,000", "the run's chapter of it"),
        ] + [
            row("dc-one-million-%d" % n, "DC One Million", "#%d" % n,
                "Morrison with Val Semeiks · the core miniseries" if n == 1 else "",
                0, 1)
            for n in range(1, 5)
        ],
    },
    {
        "id": "justice", "tier": 1, "title": "Justice for All",
        "sub": "#24–26 and #28–31 · #27 is Mark Millar's",
        "intro":
            "Seven of the ten issues the trade carries: #27 is Mark Millar's, "
            "#32 is Devin Grayson with Mark Waid, #33 is Waid alone, and none of "
            "the three is here.",
        "items": jla_rows(*ARC["Justice for All"]),
    },
    {
        "id": "ww3", "tier": 1, "title": "World War III",
        "sub": "#34 and #36–41 · the finish",
        "intro":
            "The last arc, and the one the whole run has been feeding. #35 is "
            "J. M. DeMatteis's and sits inside the trade but outside this list. "
            "#41 is Morrison's last issue of the book.",
        "items": jla_rows(*ARC["World War III"],
                          notes={41: "Morrison's last issue"}, stars={41: 1}),
    },
    {
        "id": "coda", "tier": 2, "title": "After the run",
        "sub": "2000 and 2005 · collected with it, not part of it",
        "intro":
            "Two Morrison JLA books that are not the monthly title but are "
            "collected inside the run's Deluxe Edition. Earth 2 is a graphic "
            "novel, published in 2000 as the run was ending. Classified is his "
            "return to the characters five years later.",
        "items": [
            row("jla-earth-2", "JLA: Earth 2", "2000",
                "a graphic novel with Frank Quitely", 2),
            row("jla-classified-1", "JLA: Classified", "#1",
                "Morrison with Ed McGuinness · collected as Ultramarine Corps"),
            row("jla-classified-2", "JLA: Classified", "#2"),
            row("jla-classified-3", "JLA: Classified", "#3"),
        ],
    },
]

ISSUES = sum(1 for s in SECTIONS for x in s["items"] if x["t"] == "JLA")
assert ISSUES == len(MORRISON), \
    "emitted %d JLA issues; the sources credit Morrison with %d" % (ISSUES, len(MORRISON))

GAPS = ", ".join("#%d" % n for n in sorted(FILLINS))

PROPERTY = {
    "slug": SLUG,
    "title": "JLA",
    "subtitle": "Grant Morrison's run · post-Crisis DC",
    "kind": "comics",
    "popularity": 45,
    "year": "1997–2000",
    "blurb": "The %d issues Morrison actually wrote, from JLA #1 to #41, with "
             "the one-shots and the two books collected alongside them."
             % len(MORRISON),
    "unit": {"one": "issue", "many": "issues"},
    "verb": {"base": "read", "past": "read", "ing": "reading"},
    "accent": "#1D4FA3",
    "accentDark": "#5D93E8",
    "tiers": True,
    "notes": [
        ["Tiers.",
         "1 is the run itself — the %d issues Morrison wrote on the monthly "
         "book. 2 is what is collected alongside it: the two one-shots, the "
         "crossover chapter, and the two books either side of the end. The "
         "minimum viable path is Tier 1 alone." % len(MORRISON)],
        ["Which continuity.",
         "Post-Crisis DC, a decade before Flashpoint rebooted it. The Flash is "
         "Wally West and the Green Lantern is Kyle Rayner — the mantles, not "
         "Barry Allen and Hal Jordan, and the book treats them as the League's "
         "own. Nothing outside it is required reading: the stories are "
         "deliberately self-contained, which was half the pitch."],
        ["The fill-ins are not here.",
         "Morrison wrote #1–17, #22–26, #28–31, #34 and "
         "#36–41. The gaps — %s — are Mark Waid, Mark Millar, "
         "Devin Grayson and J. M. DeMatteis, and they are left out rather than "
         "marked optional, because they are not this run. The trades collect "
         "them, so a trade's contents and a section here will not always "
         "agree." % GAPS],
        ["Where the run ends.",
         "One rule, applied throughout: if the run's own Deluxe Editions "
         "collect it, it is on this list. That takes in the Secret Files short, "
         "both one-shots, JLA #1,000,000, Earth 2 and Classified. It leaves out "
         "Aztek and the other thirty-odd #1,000,000 tie-ins. It also leaves out "
         "JLA Secret Files & Origins #2, which the Strength in Numbers trade "
         "collects but Morrison's bibliography does not claim. The single "
         "addition is DC One Million #1–4, marked optional, because the JLA "
         "chapter is a chapter of it."],
        "Issues and credits from Wikipedia's JLA article — the "
        "creative-team field, the publication history, and the collected "
        "editions, which are also where the section titles come from. The "
        "one-shots, Earth 2, Classified and DC One Million from Grant "
        "Morrison's Wikipedia bibliography; the Prometheus one-shot is placed "
        "from the dates in that character's article.",
    ],
    "sections": SECTIONS,
}


def main():
    out = prop.write(PROPERTY)
    rows = sum(len(s["items"]) for s in SECTIONS)
    print("wrote %s" % out.name)
    print("  %d sections, %d rows, %d of them JLA issues"
          % (len(SECTIONS), rows, ISSUES))
    print("  two statements of Morrison's issues agree: "
          "infobox minus fill-ins == the four Deluxe hardcovers")
    print("  left out: %s (other writers)" % GAPS)
    for s in SECTIONS:
        opt = sum(1 for x in s["items"] if x["opt"])
        print("   T%d  %-22s %3d rows%s"
              % (s["tier"], s["title"][:22], len(s["items"]),
                 "  (%d optional)" % opt if opt else ""))


if __name__ == "__main__":
    main()
