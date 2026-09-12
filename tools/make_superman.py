#!/usr/bin/env python3
"""Generate properties/superman.json — a Superman character reading list.

    python tools/make_superman.py            # build from the cached data
    python tools/make_superman.py --fetch    # re-read the sources first

WHAT THIS LIST IS, AND WHAT IT REFUSES TO BE
--------------------------------------------
It is not a publication history. Superman has the longest continuous one in
either universe and nobody finishes it; a list that tried would be unreadable
and unfinishable, which is worse than a list that admits it is a route.

So this is the house's route through him: the runs worth reading, one section
per run, in publication order, rows as issues. Veto any of it freely — the
picking is the only part that is not machine-read.

THE FRONT EDGE IS 1986, AND IT IS A HARD EDGE
---------------------------------------------
John Byrne's `The Man of Steel` restarted the character after Crisis on
Infinite Earths. Everything before it is a continuity this one replaced, so
nothing before it is here — not the Silver Age, and not Alan Moore's
`Whatever Happened to the Man of Tomorrow?`, which is that continuity's last
story rather than this one's first.

WHERE EVERY NUMBER COMES FROM
-----------------------------
Nothing in this file is typed from memory. Every row is read out of
`tools/data/superman-issues.json`, which is machine-read from the DC Database
(dc.fandom.com) and checked in so the build reproduces without a network:

  * WHICH ISSUES MAKE UP A RUN — the `IssueList` of the collected edition (or
    omnibus) that collects it. A row exists only because a collection names
    it. That is the same gate the Black Panther list uses, and it is what
    makes an invented issue number impossible to ship.
  * THAT EVERY ISSUE IS REAL — each issue's own page is fetched. A page that
    does not exist fails the fetch rather than shipping a guess.
  * THE COVER MONTH AND YEAR of every issue, read from that issue's page.
    Section spans and the publication order both come from those, so the order
    is a property of the data rather than of the order I typed the runs in.
  * THE CREDITS in each section subtitle — the `Writer`/`Penciler` fields of
    the attesting collection, never typed here.
  * THE SECTION LINKS — each volume page is fetched too, so a link cannot
    point at a page that is not there.

THE FOUR THINGS THAT NEEDED DECIDING, AND HOW
---------------------------------------------
1. `The Death and Return of Superman` is not here. It already ships as its own
   list in this catalogue with its own 48 rows and its own ids; duplicating it
   would give one issue two ids and two sets of ticks. The note says where it
   went. That is the Black Panther / Fantastic Four precedent.
2. Numbering restarts four times over this stretch — Action Comics at vol. 2,
   Superman at vols. 4, 5 and 6 — so a row id is never derived from an issue
   number alone. It is derived from the DC Database page title, which carries
   the volume and is globally unique.
3. An issue collected in two of the runs below belongs to the earlier one.
   Only `Action Comics` #1000 is affected: it closes Tomasi and Gleason's run
   and its Bendis story opens the next, and both collections print it.
   `rows_for()` keeps the first and prints what it dropped.
4. Order inside a section is cover date, with the collection's own order
   breaking ties. Ties are common — two monthly titles alternating in the same
   month — and the collection is the only thing that knows which came first.
   One collection (`Action Comics: Superman and the Men of Steel`) says on its
   own page that it prints its issues out of release order, which is exactly
   why cover date leads and the collection only breaks ties.

NOTES
-----
Unweighted, like every comics list here: no per-issue reading time is
published, so inventing one would be worse than leaving it out.

Row notes say what an entry is, never what happens in it. No story titles are
carried anywhere — the wiki prints one beside every issue and plenty of them
give away an ending.
"""
import argparse
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop  # noqa: E402

SLUG = "superman"
HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "data" / "superman-issues.json"
CACHE = HERE.parent / "scratch" / "agent-superman" / "cache"

DCDB = "dc.fandom.com"
WIKI = "https://dc.fandom.com/wiki/"
UA = "GroupWatch/1.0 (reading-list builder)"

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

# ---------------------------------------------------------------- the runs
# (section id, tier, title, the collected editions that attest it, intro)
#
# The collections are listed in the order they were published, and their issue
# lists are concatenated in that order. Nothing else about a section is typed:
# the subtitle's span, count and credits are all read back out of the data.
RUNS = [
    ("reboot", 1, "The Man of Steel",
     ["The Man of Steel 1986 (Collected)"],
     "The reboot itself: Byrne restarted the character and the whole cast "
     "from scratch, in six issues, and every run below assumes you have read "
     "it.\n\n"
     "This is the front edge of the list. Everything published before it "
     "belongs to the continuity this one replaced."),

    ("seasons", 1, "Superman for All Seasons",
     ["Superman for All Seasons (Collected)"],
     "Loeb and Sale's miniseries continues nothing and leads to nothing, and "
     "it is the one thing here you could hand to somebody who has never read "
     "a comic. It is second on the list for that reason rather than for any "
     "reason to do with order."),

    ("birthright", 2, "Superman: Birthright",
     ["Superman: Birthright (Collected)"],
     "A twelve-issue origin, told again a generation after the last one. "
     "Nothing above it leads here and nothing below it needs it — it is on "
     "the list as a second door in, for a reader who would rather start with "
     "a long origin than a short one."),

    ("fortomorrow", 3, "Superman: For Tomorrow",
     ["Superman: For Tomorrow Vol. 1 (Collected)",
      "Superman: For Tomorrow Vol. 2 (Collected)"],
     "A year on the main title, collected in two halves. It is the most "
     "argued-over thing on this list and it is here for the art; if the first "
     "half does not land, stopping costs you nothing later."),

    ("upupaway", 2, "Up, Up and Away!",
     ["Superman: Up, Up and Away! (Collected)"],
     "The first Superman story after Infinite Crisis, and the point where the "
     "main title went back to its original numbering — Superman #650 rather "
     "than a new #1. It runs as one serial alternating between the two "
     "monthly books, so the rows alternate with it."),

    ("lastson", 2, "Last Son",
     ["Superman: Last Son (Collected)"],
     "Geoff Johns wrote this one with Richard Donner, who directed the 1978 "
     "film. It shipped badly late: three issues, then a gap, then the last "
     "chapter, and then an annual a long way behind it. The cover dates in "
     "the subtitle show the delay; the collection's order is the reading "
     "order."),

    ("brainiac", 1, "Brainiac",
     ["Superman: Brainiac (Collected)"],
     "Johns and Gary Frank on Action Comics, and the shortest way to see what "
     "the pair are good at. The collection carries the special that follows "
     "straight on from it, so this list does too."),

    ("secretorigin", 2, "Secret Origin",
     ["Superman: Secret Origin (Collected)"],
     "Johns and Frank again: the origin a third time, and the last telling "
     "before the line restarted its numbering. A third door in, and the one "
     "that reads most like the films."),

    ("morrison", 1, "Action Comics, relaunched",
     ["Superman by Grant Morrison Omnibus (Collected)"],
     "The New 52 restarted every DC title at #1, and Morrison used the reset "
     "to write him young, broke and in a t-shirt before winding the run "
     "forward to where the rest of the line was.\n\n"
     "This is where the numbering breaks. Action Comics starts again at #1, "
     "which is why the rows from here on say which volume they are — the "
     "#1-18 below are not the same issues as any other #1-18 on this list. "
     "The #0 and the annual are placed by cover date, which is where the "
     "omnibus puts them."),

    ("unchained", 2, "Superman Unchained",
     ["Superman Unchained (Collected)"],
     "Snyder and Jim Lee, nine issues, published beside the New 52 monthlies "
     "rather than inside them — so it needs nothing from the run above and "
     "nothing below needs it."),

    ("loisclark", 3, "Lois and Clark",
     ["Superman: Lois and Clark (Collected)"],
     "Eight issues that bridge the New 52 out and Rebirth in. Optional as a "
     "story; it is here because without it the change between the two "
     "sections either side of it arrives from nowhere."),

    ("rebirth", 1, "Tomasi and Gleason's Superman",
     ["Superman by Peter J. Tomasi and Patrick Gleason Omnibus (Collected)"],
     "The longest run on this list and the house pick for the best modern "
     "one. Married, a father, and written as though neither of those needed "
     "defending.\n\n"
     "The omnibus order is followed exactly, so the chapters from other "
     "books — a crossover with Action Comics, and a detour through Super Sons "
     "and Teen Titans — sit where they are read rather than in a heap at the "
     "end. The gaps in the numbering are the omnibus's rather than this "
     "list's: what it leaves out, it leaves out."),

    ("bendis", 2, "Bendis takes over",
     ["The Man of Steel 2018 (Collected)",
      "Superman: The Unity Saga: Phantom Earth (Collected)",
      "Superman: The Unity Saga: The House of El (Collected)"],
     "A free preview, a six-issue miniseries that reuses the title The Man of "
     "Steel, and then a new Superman #1 for the Unity Saga — one run across "
     "three collected editions.\n\n"
     "The main title starts over at #1 here. It does that three times inside "
     "this list, which is why the rows carry a volume."),

    ("warworld", 1, "The Warworld Saga",
     ["Superman: The Warworld Saga (Collected)"],
     "The strongest recent run, and the one worth catching up for. The "
     "collection folds in the three Future State issues that set it up — "
     "they were published first, so they come first here."),

    ("supercorp", 2, "Williamson's Superman",
     ["Superman: Supercorp (Collected)"],
     "Where the list stops, because it is where a collected edition stops. "
     "The run carries on past this volume; nothing here is guessed ahead of "
     "a collection that names the issues."),
]

# Every `<series> Vol <n>` this list is allowed to contain. The display title
# is derived rather than typed — the wiki's own name, plus `(vol. n)` for any
# volume past the first, because the numbering restarts and a bare "Superman
# #1" would be four different comics. The allowlist is here so a collection
# that quietly grows a new series fails the build instead of shipping a row
# nobody chose.
SERIES_OK = {
    "Action Comics Vol 1", "Action Comics Vol 2",
    "Action Comics Annual Vol 1", "Action Comics Annual Vol 2",
    "Action Comics 2021 Annual Vol 1", "Action Comics 2022 Annual Vol 1",
    "Batman/Superman Authority Special Vol 1",
    "DC Nation Vol 2",
    "Future State: Superman: House of El Vol 1",
    "Future State: Superman: Worlds of War Vol 1",
    "Super Sons Vol 1",
    "Superman Vol 1", "Superman Vol 2", "Superman Vol 4", "Superman Vol 5",
    "Superman Vol 6",
    "Superman 2023 Annual Vol 6",
    "Superman Annual Vol 4",
    "Superman Special Vol 3",
    "Superman Unchained Vol 1",
    "Superman: Birthright Vol 1",
    "Superman: Lois and Clark Vol 1",
    "Superman: New Krypton Special Vol 1",
    "Superman: Rebirth Vol 1",
    "Superman: Secret Origin Vol 1",
    "Superman: Warworld Apocalypse Vol 1",
    "Superman for All Seasons Vol 1",
    "Teen Titans Vol 6",
    "The Man of Steel Vol 1", "The Man of Steel Vol 2",
}

# Row annotations, keyed by DC Database page title. Every one is a fact about
# publication — what kind of book it is, or why a collection carries it.
# Nothing here is a plot point, and no story titles are used.
NOTE = {
    "Superman: New Krypton Special Vol 1 1":
        "A one-shot, collected with the run it follows from.",
    "Action Comics Vol 2 0":
        "A zero issue, published between #12 and #13.",
    "Superman: Rebirth Vol 1 1":
        "A one-shot, ahead of the run's own #1.",
    "Action Comics Vol 1 1000":
        "The 1000th issue · an anthology · both this run's omnibus and the "
        "next run's collection print it.",
    "DC Nation Vol 2 0":
        "A free preview anthology.",
    "Superman Special Vol 3 1": "A one-shot.",
    "Superman: Warworld Apocalypse Vol 1 1": "A one-shot finale.",
    "Batman/Superman Authority Special Vol 1 1":
        "A one-shot from outside the Superman books.",
    "Future State: Superman: House of El Vol 1 1":
        "A one-shot, from the two-month Future State break in the line.",
    "Super Sons Vol 1 11": "A chapter from another book.",
    "Super Sons Vol 1 12": "A chapter from another book.",
    "Teen Titans Vol 6 15": "A chapter from another book.",
}
ANNUAL_NOTE = "An annual."

NOTES = [
    ["The house's picks — veto freely.",
     "This is a route through Superman, not his publication history: nobody "
     "finishes that, and a list that pretended otherwise would be "
     "unfinishable by design. So these are the "
     "runs the house would actually hand someone, one section each, in the "
     "order they were published. If one is not for you, skip the section "
     "whole; if something is missing, that is what the group chat is for. "
     "Everything except the picking is machine-read."],
    ["It starts in 1986, and that edge is hard.",
     "Byrne's The Man of Steel restarted the character from scratch after "
     "Crisis on Infinite Earths, and this list starts there because "
     "everything earlier belongs to a continuity that one replaced. That "
     "includes the story usually called the best Superman comic ever "
     "published, \"Whatever Happened to the Man of Tomorrow?\" — it is the "
     "last story of the old continuity rather than the first of this one, and "
     "it belongs on a list of its own."],
    ["Tiers.",
     "1 is the spine — the reboot, For All Seasons, Brainiac, Morrison's "
     "Action Comics, Tomasi and Gleason, and the Warworld Saga. 2 is "
     "strongly recommended, and includes the two origin retellings that are "
     "alternative ways in. 3 is genuinely optional: the most argued-over run "
     "here, and a bridge between two eras. Tier 1 alone is a complete read."],
    ["\"The Death and Return of Superman\" is its own list here.",
     "It sits inside this stretch chronologically — 1992 to 1993, between the "
     "reboot and For All Seasons — and it already ships in this catalogue as "
     "its own 48 issues with its own ids. Carrying it twice would give one "
     "issue two sets of ticks, so it is not repeated here. Read it between "
     "the first two sections below."],
    ["What is deliberately absent.",
     "Everything outside this continuity, however good: \"All-Star "
     "Superman\", \"Red Son\", \"Kingdom Come\", \"Secret Identity\", "
     "\"Superman Smashes the Klan\". "
     "Also the 1986–91 monthlies, which are years of two parallel titles "
     "with no agreed essential slice; New Krypton, which is longer than "
     "anything here and divides people; and Jon Kent's own solo book, which "
     "is a different character's list. None of those is "
     "a judgement on the comics — they are judgements about what belongs "
     "under this title."],
    ["Volume numbers, because the numbering keeps restarting.",
     "Action Comics starts again at #1 in 2011, and the main Superman title "
     "does it in 2016, 2018 and 2023. So a row says which volume it is — "
     "\"Superman (vol. 5) #1\" is not \"Superman (vol. 4) #1\" — and the "
     "tick ids behind them are built from the volume too, so no two issues "
     "can ever share one."],
    ["Order inside a section.",
     "Cover date, with the collection's own order breaking ties. Ties are "
     "constant in the stretches where two monthly books alternate, and the "
     "collection is the only thing that knows which of the two came first."],
    ["No hours, on any row.",
     "Comics have no runtimes and an issue count is not an hour, so nothing "
     "here is weighted. The bar counts issues."],
    ["Links.",
     "Sections link to the DC Database page for each series they contain, "
     "not to individual issues. Every one of those pages was fetched before "
     "the link was written."],
    "Issue lists, cover dates and credits machine-read from the DC Database "
    "(dc.fandom.com): the IssueList of the collected edition or omnibus that "
    "collects each run, each issue's own page for its cover month and year, "
    "and each series page for the section links. A row exists only because a "
    "collection names it; the generator refuses to emit one that is not "
    "attested.",
]


# ---------------------------------------------------------------- fetching
def wikitext(page):
    """The wikitext of a DC Database page, cached on disk. Returns None for a
    page that does not exist."""
    f = CACHE / (re.sub(r"[^A-Za-z0-9]+", "-", page)[:150] + ".wiki")
    if f.exists():
        t = f.read_text(encoding="utf-8")
        return None if t.startswith("\x00MISSING") else t
    f.parent.mkdir(parents=True, exist_ok=True)
    q = urllib.parse.urlencode({"action": "parse", "page": page,
                                "prop": "wikitext", "format": "json",
                                "formatversion": "2", "redirects": "1"})
    req = urllib.request.Request("https://%s/api.php?%s" % (DCDB, q),
                                 headers={"User-Agent": UA})
    d = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8"))
    time.sleep(0.4)
    if "error" in d:
        f.write_text("\x00MISSING", encoding="utf-8")
        return None
    t = d["parse"]["wikitext"]
    f.write_text(t, encoding="utf-8")
    return t


def url_of(page):
    return WIKI + urllib.parse.quote(page.replace(" ", "_"),
                                     safe="/:_,!()&'-.")


def field(t, name):
    m = re.search(r"\n\|\s*%s\s*=([^\n|]*)" % re.escape(name), t)
    return (m.group(1).strip() if m else "")


def fields(t, base):
    """`Writer1`, `Writer2`, ... in order, blanks dropped."""
    out = []
    for i in range(1, 12):
        v = field(t, "%s%d" % (base, i))
        v = re.sub(r"\[\[|\]\]", "", v).strip()
        if v and v not in out:
            out.append(v)
    return out


def issue_list(t, page):
    """The `{{C|...}}` entries of a collected edition's IssueList, in order."""
    m = re.search(r"\|\s*IssueList\s*=(.*?)(?=\n\|\s*\w+\s*=|\n\}\})", t, re.S)
    assert m, "%s has no IssueList" % page
    out = []
    for raw in re.findall(r"\{\{[Cc]\|([^}|]+)", m.group(1)):
        # `Superman Vol 2 #204` and `Superman Vol 2 204` both occur.
        out.append(re.sub(r"\bVol (\d+) #", r"Vol \1 ", raw.strip()))
    assert out, "%s has an empty IssueList" % page
    return out


def cover_date(t, page):
    """(month, year) from an issue page's infobox."""
    mon, yr = field(t, "Month"), field(t, "Year")
    assert re.match(r"^\d{4}$", yr), "%s has no cover year (%r)" % (page, yr)
    if re.match(r"^\d{1,2}$", mon):
        m = int(mon)
    else:
        names = [x for x in MONTHS if mon and x.lower().startswith(mon.lower()[:3])]
        assert len(names) == 1, "%s has no cover month (%r)" % (page, mon)
        m = MONTHS.index(names[0]) + 1
    assert 1 <= m <= 12, "%s has cover month %r" % (page, m)
    return m, int(yr)


def fetch():
    collections, issues, volumes = {}, {}, {}
    for _, _, _, cols, _ in RUNS:
        for col in cols:
            t = wikitext(col)
            assert t, "no DC Database page for the collection %r" % col
            pages = issue_list(t, col)
            collections[col] = {
                "url": url_of(col),
                "writers": fields(t, "Writer"),
                "pencilers": fields(t, "Penciler"),
                "issues": pages,
            }
            for page in pages:
                if page in issues:
                    continue
                it = wikitext(page)
                assert it, "no DC Database page for the issue %r (named by %s)" \
                    % (page, col)
                m, y = cover_date(it, page)
                issues[page] = {"month": m, "year": y, "url": url_of(page)}
    for page in issues:
        vol = page.rsplit(" ", 1)[0]
        if vol in volumes:
            continue
        # A one-shot has an issue page and no series page. Recorded as absent
        # rather than assumed away, so build() links the issue instead and
        # fails if a multi-issue series ever loses its page.
        volumes[vol] = url_of(vol) if wikitext(vol) else None
    data = {
        "_source": {
            "site": "https://dc.fandom.com/",
            "issue_lists": "the IssueList of each collected edition below",
            "cover_dates": "each issue's own page on the same wiki",
            "series_links": "each series page on the same wiki",
        },
        "fetched": time.strftime("%Y-%m-%d"),
        "collections": collections,
        "issues": issues,
        "volumes": volumes,
    }
    DATA.parent.mkdir(parents=True, exist_ok=True)
    with DATA.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, indent=1, ensure_ascii=False, sort_keys=True)
                + "\n")
    print("wrote %s" % DATA.relative_to(HERE.parent))
    print("  %d collections, %d issues, %d series"
          % (len(collections), len(issues), len(volumes)))


# ---------------------------------------------------------------- building
def parse(page):
    """`Action Comics Vol 2 13` -> (series key, display title, `#13`)."""
    m = re.match(r"^(.+?) Vol (\d+) (\d+)$", page)
    assert m, "unparseable issue page title %r" % page
    name, vol, num = m.group(1), int(m.group(2)), m.group(3)
    key = "%s Vol %d" % (name, vol)
    assert key in SERIES_OK, \
        "%r is not an allowed series - add it to SERIES_OK on purpose" % key
    title = name if vol == 1 else "%s (vol. %d)" % (name, vol)
    return key, title, "#%s" % num


def rows_for(run, data, used):
    """The issues of one run: the attesting collections concatenated, dropping
    anything an earlier run already took, ordered by cover date with the
    collections' own order breaking ties."""
    _, _, _, cols, _ = run
    seq, dropped = [], []
    for col in cols:
        for page in data["collections"][col]["issues"]:
            if page in used:
                if page not in dropped:
                    dropped.append(page)
                continue
            if page in [p for p, _ in seq]:
                continue
            seq.append((page, len(seq)))
    order = sorted(seq, key=lambda pi: (data["issues"][pi[0]]["year"],
                                        data["issues"][pi[0]]["month"], pi[1]))
    return [p for p, _ in order], dropped


def credits_of(run, data):
    """Writers then pencilers, as the attesting collections credit them."""
    names = []
    for base in ("writers", "pencilers"):
        for col in run[3]:
            for n in data["collections"][col][base]:
                if n not in names:
                    names.append(n)
    assert names, "no credits on the collections for %r" % run[0]
    if len(names) > 4:
        return ", ".join(names[:4]) + " and others"
    return ", ".join(names)


def span(pages, data):
    a = data["issues"][pages[0]]
    b = data["issues"][pages[-1]]
    first = "%s %d" % (MONTHS[a["month"] - 1], a["year"])
    last = "%s %d" % (MONTHS[b["month"] - 1], b["year"])
    return first if first == last else "%s – %s" % (first, last)


def build(data):
    sections, used, first_dates, drops = [], set(), [], []
    for run in RUNS:
        sid, tier, title, cols, intro = run
        pages, dropped = rows_for(run, data, used)
        assert pages, "section %s has no rows left" % sid
        drops += [(sid, p) for p in dropped]
        used |= set(pages)
        d = data["issues"][pages[0]]
        first_dates.append((sid, (d["year"], d["month"])))

        items, links = [], []
        for page in pages:
            key, t, n = parse(page)
            note = NOTE.get(page, "")
            if not note and re.search(r"\bAnnual\b", key):
                note = ANNUAL_NOTE
            items.append({"id": "sup-%s-v%s-%s"
                          % (prop.slug(key.rsplit(" Vol ", 1)[0]),
                             key.rsplit(" Vol ", 1)[1], n[1:]),
                          "t": t, "n": n, "note": note, "star": 0, "opt": 0,
                          "url": ""})
            if key not in [l["key"] for l in links]:
                # The series page, or for a one-shot that has none, the issue
                # page. A series with more than one issue here and no page of
                # its own would leave the header unable to name it, so it
                # fails instead.
                url = data["volumes"][key]
                if not url:
                    same = [q for q in pages if parse(q)[0] == key]
                    assert len(same) == 1, \
                        "%s has no series page but %d issues in %s" \
                        % (key, len(same), sid)
                    url = data["issues"][page]["url"]
                links.append({"key": key, "label": t, "url": url})
        sub = prop.join_bits(span(pages, data),
                             "%d issue%s" % (len(items),
                                             "" if len(items) == 1 else "s"),
                             credits_of(run, data))
        sections.append({"id": sid, "title": title, "sub": sub, "tier": tier,
                         "intro": intro,
                         "links": [{"label": l["label"], "url": l["url"]}
                                   for l in links],
                         "items": items})

    # Publication order is a property of the data, not of the order the runs
    # are typed in above. If a run is ever inserted in the wrong place this
    # fails rather than shipping a list that claims an order it does not have.
    for (a, da), (b, db) in zip(first_dates, first_dates[1:]):
        assert da <= db, "%s starts before %s - the runs are out of order" % (b, a)

    total = sum(len(s["items"]) for s in sections)
    assert total == len(used), "an issue is in two sections"
    years = [data["issues"][p]["year"] for p in used]

    p = {
        "slug": SLUG,
        "title": "Superman",
        "subtitle": "a character reading list · post-Crisis onward",
        "kind": "comics",
        "popularity": 74,
        "year": "%d–%d" % (min(years), max(years)),
        "blurb": "%d issues across %d runs, from the 1986 reboot onward — "
                 "the route the house would actually hand someone, rather "
                 "than the publication history." % (total, len(sections)),
        "unit": {"one": "issue", "many": "issues"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": "#C8102E",
        "accentDark": "#FF7D8A",
        "tiers": True,
        "notes": NOTES,
        "sections": sections,
    }
    return p, drops


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true",
                    help="re-read the DC Database into tools/data/superman-issues.json")
    args = ap.parse_args()
    if args.fetch:
        fetch()

    data = json.loads(DATA.read_text(encoding="utf-8"))
    p, drops = build(data)
    assert not any("w" in x for s in p["sections"] for x in s["items"]), \
        "a row carries a weight"
    out = prop.write(p)

    total = sum(len(s["items"]) for s in p["sections"])
    print("wrote %s" % out.name)
    print("  %d issues in %d sections, %s" % (total, len(p["sections"]),
                                              p["year"]))
    for s in p["sections"]:
        print("  T%d %-14s %3d  %s" % (s["tier"], s["id"], len(s["items"]),
                                       s["sub"]))
    counts = {}
    for s in p["sections"]:
        counts[s["tier"]] = counts.get(s["tier"], 0) + len(s["items"])
    print("  tiers: " + "   ".join("T%d %d" % (k, counts[k])
                                   for k in sorted(counts)))
    for sid, page in drops:
        print("  dropped from %s (an earlier run already has it): %s"
              % (sid, page))


if __name__ == "__main__":
    main()
