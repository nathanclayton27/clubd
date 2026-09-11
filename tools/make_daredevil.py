#!/usr/bin/env python3
"""Generate properties/daredevil.json — five runs, Miller to Zdarsky.

    python tools/make_daredevil.py

Daredevil is the cleanest spine at Marvel: five long runs, each finite, each
starting where the last one stopped, in one unbroken main-line continuity. So
the list is one section per run, in publication order, and the tier legend is
barely working: Tier 1 is the five runs, Tier 2 is the three lead-ins that
explain how a run starts, and Tier 3 is the two stretches by other hands that
sit between runs.

**Nothing here is typed from memory.** Every issue number, cover date and
creator credit is read out of tools/data/daredevil.json, which
scratch/daredevil/fetch.py harvested from the Marvel Database
(marvel.fandom.com) — `list=allpages` for the issue pages that exist in each
volume, then `prop=revisions` for each page's Comic Template infobox. The run
boundaries below are not asserted from a reading order somebody wrote down;
`writer_run()` reads the printed writer credit on every issue in a range and
fails the build if the range is not exactly that writer's. That is the whole
reason the file is shaped this way: a reading list for comics is a claim about
who wrote what, and a wrong issue number is worse than a missing list.

Unweighted, like every comics list here: comics publish no per-issue reading
time, and inventing one is the defect CLU-131 exists for.

**Notes say what an issue is, never what happens in it.** A creator's first or
last issue, a renumbering, a fill-in, an arc's opening chapter — all fine.
Stars carry the "this one matters" signal so a note never has to.
"""
import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop  # noqa: E402

SLUG = "daredevil"
DATA = pathlib.Path(__file__).resolve().parent / "data" / (SLUG + ".json")

# volume key -> (Marvel Database page, row title, id prefix, header label).
# The header URL is NOT here: it comes from the harvest, which read each
# volume page's own canonical url, so a section link cannot be a typo.
VOLS = {
    "v1": ("Daredevil Vol 1", "Daredevil (1964)", "dd1", "Daredevil (1964)"),
    "v2": ("Daredevil Vol 2", "Daredevil (1998)", "dd2", "Daredevil (1998)"),
    "v3": ("Daredevil Vol 3", "Daredevil (2011)", "dd3", "Daredevil (2011)"),
    "v4": ("Daredevil Vol 4", "Daredevil (2014)", "dd4", "Daredevil (2014)"),
    "v5": ("Daredevil Vol 5", "Daredevil (2016)", "dd5", "Daredevil (2016)"),
    "v6": ("Daredevil Vol 6", "Daredevil (2019)", "dd6", "Daredevil (2019)"),
    "v7": ("Daredevil Vol 7", "Daredevil (2022)", "dd7", "Daredevil (2022)"),
    "mwf": ("Daredevil: The Man Without Fear Vol 1",
            "Daredevil: The Man Without Fear", "mwf", "The Man Without Fear"),
    "wwf": ("Daredevil: Woman Without Fear Vol 1",
            "Daredevil: Woman Without Fear", "wwf", "Woman Without Fear"),
    "dr": ("Devil's Reign Vol 1", "Devil's Reign", "dr", "Devil's Reign"),
    "sl": ("Shadowland Vol 1", "Shadowland", "sl", "Shadowland"),
    "rb": ("Daredevil: Reborn Vol 1", "Daredevil: Reborn", "rb", "Reborn"),
}

# Row notes, keyed by (volume key, issue number as printed). Everything else
# ships with an empty note on purpose — an unannotated issue is an ordinary
# chapter of the run it sits in, and saying so 300 times would be noise.
NOTES = {
    ("v1", "158"): ("Miller's first issue on the book, as artist only.", 1),
    ("v1", "162"): ("A fill-in: Michael Fleisher and Steve Ditko.", 0),
    ("v1", "165"): ("His first co-writing credit.", 0),
    ("v1", "167"): ("David Michelinie writes it, with Miller sharing the "
                    "credit.", 0),
    ("v1", "168"): ("He takes the writing too, and brings Elektra with him.", 2),
    ("v1", "181"): ("", 2),
    ("v1", "185"): ("Klaus Janson pencils as well as inks, through #190.",
                    0),
    ("v1", "191"): ("Miller back on pencils, and the last issue of the "
                    "first stint.", 1),
    ("v1", "219"): ("A one-off drawn by John Buscema, written two years "
                    "after he left.", 0),
    ("v1", "226"): ("Co-plotted with Denny O'Neil — the handover issue.", 0),
    ("v1", "227"): ("Born Again begins, with David Mazzucchelli.", 2),
    ("v1", "233"): ("His last issue of the 1964 series.", 1),
    ("mwf", "1"): ("Miller and John Romita Jr. on the origin.", 1),
    ("v2", "1"): ("Kevin Smith and Joe Quesada relaunch the book under "
                  "Marvel Knights.", 1),
    ("v2", "9"): ("David Mack takes over as writer.", 0),
    ("v2", "12"): ("A fill-in by Jimmy Palmiotti and Joe Quesada.", 0),
    ("v2", "16"): ("Bendis's first Daredevil, drawn by David Mack.", 1),
    ("v2", "20"): ("Six issues by Bob Gale before Bendis returns.", 0),
    ("v2", "26"): ("Bendis and Alex Maleev begin the run proper.", 2),
    ("v2", "51"): ("Five issues by David Mack, between Bendis's two halves.", 0),
    ("v2", "56"): ("Bendis and Maleev resume.", 0),
    ("v2", "81"): ("Bendis's last issue.", 1),
    ("v2", "82"): ("Brubaker and Michael Lark start on the next page.", 2),
    ("v2", "500"): ("Legacy numbering returns, and Brubaker signs off.", 1),
    ("v2", "501"): ("Andy Diggle takes over.", 0),
    ("sl", "1"): ("The crossover Waid's run is written against.", 0),
    ("rb", "1"): ("A four-issue bridge before the relaunch.", 0),
    ("v3", "1"): ("Waid, Paolo Rivera and Marcos Martin restart at #1.", 2),
    ("v3", "10.1"): ("A standalone .1 issue.", 0),
    ("v3", "12"): ("Chris Samnee's first issue.", 1),
    ("v3", "36"): ("The series restarts at a new #1 next month.", 0),
    ("v4", "0.1"): ("Reprints the four-part Road Warrior digital prelude.", 0),
    ("v4", "1"): ("Same creators, new numbering, new city.", 1),
    ("v4", "1.50"): ("An anniversary special: a Waid lead story and two "
                     "shorts.", 0),
    ("v4", "15.1"): ("A standalone .1 issue.", 0),
    ("v4", "18"): ("Waid's last issue.", 1),
    ("v5", "1"): ("Charles Soule and Ron Garney.", 0),
    ("v5", "595"): ("Legacy numbering returns again.", 0),
    ("v6", "1"): ("Zdarsky and Marco Checchetto begin.", 2),
    ("v6", "36"): ("The run pauses here for the event below.", 0),
    ("dr", "1"): ("A line-wide event written out of this run.", 1),
    ("wwf", "1"): ("A companion miniseries, read between the event's "
                   "chapters.", 0),
    ("v7", "1"): ("The run picks straight back up at a new #1.", 1),
    ("v7", "14"): ("The end of Zdarsky's Daredevil.", 1),
}

OPTIONAL = {("v1", "219"), ("v3", "10.1"), ("v4", "0.1"), ("v4", "1.50"),
            ("v4", "15.1")}
OPTIONAL |= {("v2", str(n)) for n in range(20, 26)}
OPTIONAL |= {("v2", str(n)) for n in range(51, 56)}


def load():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    idx = {}
    for r in d["issues"]:
        idx[(r["vol"], r["numtext"])] = r
    assert len(idx) == len(d["issues"]), "duplicate issue in the harvest"
    return d, idx


D, IDX = load()


def fetch(vk, num):
    """The harvested row for one issue, or a hard failure."""
    page = VOLS[vk][0]
    r = IDX.get((page, str(num)))
    assert r, "%s #%s is not in tools/data/%s.json" % (page, num, SLUG)
    return r


def item(vk, num):
    """One row, built entirely from the harvest plus the notes table above."""
    r = fetch(vk, num)
    _, title, pre, _ = VOLS[vk]
    note, star = NOTES.get((vk, str(num)), ("", 0))
    return {
        "id": "%s-%s" % (pre, str(num).replace(".", "-")),
        "t": title,
        "n": "#%s" % r["numtext"],
        "note": note,
        "star": star,
        "opt": 1 if (vk, str(num)) in OPTIONAL else 0,
        "url": "",
    }


def nums(vk, lo, hi):
    """Every issue the wiki lists for this volume between lo and hi, in order,
    point-ones included — so a .1 issue can never be silently skipped."""
    page = VOLS[vk][0]
    out = [r for r in D["issues"] if r["vol"] == page and lo <= r["num"] <= hi]
    out.sort(key=lambda r: r["num"])
    assert out, "no issues of %s between %s and %s" % (page, lo, hi)
    return [r["numtext"] for r in out]


def rng(vk, lo, hi):
    return [item(vk, n) for n in nums(vk, lo, hi)]


def writer_run(vk, lo, hi, who, whole=True):
    """Assert the printed credits over a range, and hand back the rows.

    `whole` means every issue in the range is credited to `who`; without it,
    `who` merely has to appear somewhere in the issue's credits. This is the
    assertion the whole file rests on — the run boundaries are read off the
    wiki's own credits rather than typed in from a reading order.
    """
    got = nums(vk, lo, hi)
    for n in got:
        r = fetch(vk, n)
        names = r["lead"] if whole else r["writers"]
        assert who in names, \
            "%s #%s is credited to %s, not %s" % (VOLS[vk][0], n,
                                                  names or "nobody", who)
    return [item(vk, n) for n in got]


def not_written_by(vk, lo, hi, who):
    """The other half of a boundary: prove the run really does stop here."""
    for n in nums(vk, lo, hi):
        r = fetch(vk, n)
        assert who not in r["writers"], \
            "%s #%s is credited to %s after all" % (VOLS[vk][0], n, who)


def links(*keys):
    """Header links, with every URL taken from the harvested volume page."""
    out = []
    for k in keys:
        page, _, _, label = VOLS[k]
        v = D["volumes"].get(page)
        assert v and v["url"].startswith("https://marvel.fandom.com/wiki/"), \
            "no harvested url for %s" % page
        out.append({"label": label, "url": v["url"]})
    return out


VK_OF = {v[2]: k for k, v in VOLS.items()}


def onsale(x):
    """The on-sale date behind a built row, as a datetime."""
    vk = VK_OF[x["id"].split("-")[0]]
    return datetime.datetime.strptime(
        fetch(vk, x["n"][1:])["released"], "%B %d, %Y")


def penciler(vk, num, who):
    """Assert a drawing credit a note or an intro leans on."""
    got = fetch(vk, num)["penciler"]
    # the wiki spells Marcos Martin both with and without the accent
    ok = got == who or got.replace("í", "i") == who
    assert ok, "%s #%s is pencilled by %s, not %s" % (VOLS[vk][0], num, got, who)


def build():
    # ---- Miller, first stint -------------------------------------------
    # He pencils from #158 and writes from #168; #165-167 carry a shared
    # credit, which is why the lead-in is its own tier 2 section.
    arrival = [item("v1", n) for n in nums("v1", 158, 167)]
    for n in ("158", "159", "160", "161", "163", "164"):
        assert "Frank Miller" not in fetch("v1", n)["lead"], \
            "#%s already credits Miller as writer" % n
        assert fetch("v1", n)["penciler"] == "Frank Miller", \
            "#%s is not pencilled by Miller" % n
    # #162 is a one-issue fill-in by other hands sitting inside the stretch
    assert fetch("v1", "162")["penciler"] == "Steve Ditko"
    assert "Frank Miller" in fetch("v1", "165")["lead"]
    assert "Frank Miller" in fetch("v1", "166")["lead"]
    # #167 is David Michelinie's script with Miller sharing the credit, so
    # "over Roger McKenzie's scripts" is true of most of the stretch, not all.
    assert fetch("v1", "167")["lead"] == ["David Michelinie"],         "#167 is no longer led by Michelinie"
    assert "Frank Miller" in fetch("v1", "167")["writers"]
    miller = writer_run("v1", 168, 191, "Frank Miller")
    not_written_by("v1", 192, 218, "Frank Miller")
    assert "Elektra" in fetch("v1", "168")["titles"], \
        "#168 is no longer the issue titled Elektra"
    for n in nums("v1", 168, 184):
        penciler("v1", n, "Frank Miller")
    janson = nums("v1", 185, 190)
    for n in janson:
        penciler("v1", n, "Klaus Janson")
    assert len(janson) == 6, "the Janson pencils are no longer six issues"
    # and Miller takes the pencils back for the last one, which is why the
    # note on #185 stops at #190 instead of saying "from here".
    penciler("v1", 191, "Frank Miller")

    # ---- Miller, second stint ------------------------------------------
    badlands = [item("v1", "219")]
    assert "Frank Miller" in fetch("v1", "219")["lead"]
    penciler("v1", 219, "John Buscema")
    handover = writer_run("v1", 226, 226, "Frank Miller")
    born = writer_run("v1", 227, 233, "Frank Miller")
    for n in nums("v1", 227, 233):
        assert any(a.startswith("Born Again") for a in fetch("v1", n)["arcs"]), \
            "#%s is not filed under Born Again" % n
    assert len(born) == 7, "Born Again is no longer seven issues"
    not_written_by("v1", 234, 240, "Frank Miller")
    for n in nums("v1", 226, 233):
        penciler("v1", n, "David Mazzucchelli")

    mwf = writer_run("mwf", 1, 5, "Frank Miller")
    for n in nums("mwf", 1, 5):
        penciler("mwf", n, "John Romita Jr.")
    # Miller writes five more Daredevil issues seven years after #233, which
    # is why that row says "of the 1964 series" rather than "on Daredevil".
    assert onsale(mwf[0]) > onsale(item("v1", "233")),         "The Man Without Fear no longer ships after #233"

    # ---- the 1998 relaunch Bendis walks into ---------------------------
    # The wiki files the whole of vol 2 #1-81 under the Marvel Knights
    # imprint, which is why the section is named for it.
    assert D["volumes"]["Daredevil Vol 2"]["publisher"] == "Marvel Knights"
    knights = rng("v2", 1, 15)
    assert [x for x in knights if x["id"] == "dd2-1"], "vol 2 #1 missing"
    for n in range(1, 9):
        assert "Kevin Smith" in fetch("v2", n)["lead"]
    for n in (9, 10, 11, 13, 14, 15):
        assert "David Mack" in fetch("v2", n)["lead"]
    penciler("v2", 1, "Joe Quesada")
    assert fetch("v2", 12)["lead"] == ["Jimmy Palmiotti", "Joe Quesada"]

    # ---- Bendis --------------------------------------------------------
    # Bendis has written no earlier Daredevil in the harvest, so "his first"
    # is a fact about the data rather than a recollection.
    for n in nums("v2", 0, 15):
        assert "Brian Michael Bendis" not in fetch("v2", n)["writers"]
    wakeup = writer_run("v2", 16, 19, "Brian Michael Bendis")
    penciler("v2", 16, "David Mack")
    gale = writer_run("v2", 20, 25, "Bob Gale")
    assert len(gale) == 6, "the Gale fill-in is no longer six issues"
    bendis_a = writer_run("v2", 26, 50, "Brian Michael Bendis")
    penciler("v2", 26, "Alex Maleev")
    mack = writer_run("v2", 51, 55, "David Mack")
    assert len(mack) == 5, "the Mack interlude is no longer five issues"
    bendis_b = writer_run("v2", 56, 81, "Brian Michael Bendis")

    # ---- Brubaker ------------------------------------------------------
    bru = writer_run("v2", 82, 119, "Ed Brubaker")
    bru += writer_run("v2", 500, 500, "Ed Brubaker")
    penciler("v2", 82, "Michael Lark")
    assert not [r for r in D["issues"] if r["vol"] == "Daredevil Vol 2"
                and 119 < r["num"] < 500], \
        "#119 is no longer followed straight by #500"

    # ---- Diggle, and the crossover between the runs ---------------------
    # Shadowland ran alongside the last months of the parent title rather than
    # after them, so this section interleaves on on-sale dates too.
    diggle = sorted(writer_run("v2", 501, 512, "Andy Diggle", whole=False)
                    + writer_run("sl", 1, 5, "Andy Diggle")
                    + writer_run("rb", 1, 4, "Andy Diggle"), key=onsale)

    # ---- Waid ----------------------------------------------------------
    # Vol 3 #1 leads with a Fred Van Lente short; Waid writes the two stories
    # after it, so the check is "credited", not "credited first".
    waid3 = writer_run("v3", 1, 36, "Mark Waid", whole=False)
    assert {fetch("v3", 1)["penciler"],
            fetch("v3", 2)["penciler"]} == {"Marcos Martin", "Paolo Rivera"}
    penciler("v3", 12, "Chris Samnee")
    pencils3 = [fetch("v3", n)["penciler"] for n in nums("v3", 12, 36)]
    assert pencils3.count("Chris Samnee") > len(pencils3) / 2,         "Samnee is no longer the regular artist from #12 on"
    for n in nums("v3", 1, 11):
        assert fetch("v3", n)["penciler"] != "Chris Samnee", \
            "#%s already has Samnee on pencils" % n
    # Vol 4 #0.1 is a reprint of the Road Warrior digital prelude and carries
    # no original credit of its own, so it is checked as a reprint instead.
    assert fetch("v4", "0.1")["reprints"] and not fetch("v4", "0.1")["writers"]
    assert len(fetch("v4", "0.1")["reprints"]) == 4, \
        "the Road Warrior prelude is no longer four parts"
    assert len(fetch("v4", "1.50")["writers"]) == 3, \
        "the anniversary special is no longer three stories"
    # #0.1 shipped in July 2014, months after the #1 it preludes, so it sits
    # on its own on-sale date like every other row rather than at the head of
    # the section. The list is publication order and now has no exceptions.
    waid4 = sorted([item("v4", "0.1")]
                   + writer_run("v4", 1, 18, "Mark Waid", whole=False),
                   key=onsale)
    penciler("v4", 1, "Chris Samnee")

    # ---- Soule, between Waid and Zdarsky --------------------------------
    soule = writer_run("v5", 1, 612, "Charles Soule")
    penciler("v5", 1, "Ron Garney")
    assert not [r for r in D["issues"] if r["vol"] == "Daredevil Vol 5"
                and 28 < r["num"] < 595], "#28 no longer runs into #595"

    # ---- Zdarsky -------------------------------------------------------
    zd6 = writer_run("v6", 1, 36, "Chip Zdarsky")
    penciler("v6", 1, "Marco Checchetto")
    reign = writer_run("dr", 1, 6, "Chip Zdarsky")
    wwf = writer_run("wwf", 1, 3, "Chip Zdarsky")
    zd7 = writer_run("v7", 1, 14, "Chip Zdarsky")

    # Devil's Reign and Woman Without Fear shipped alternately; interleave
    # them on the on-sale dates the harvest carries rather than by guess.
    event = sorted(reign + wwf, key=onsale)

    # "restarts at a new #1 next month" has to stay true of the dates
    assert 0 < (onsale(item("v4", 1)) - onsale(item("v3", 36))).days <= 40

    return [
        {"id": "arrival", "tier": 2, "title": "Miller arrives",
         "sub": "1979–1980 · he draws it before he writes it",
         "open": True,
         "links": links("v1"),
         "intro": "Frank Miller's first stretch on Daredevil is as the artist "
                  "only, mostly over Roger McKenzie's scripts — two of the ten "
                  "are written by other hands, and both rows say so. He picks "
                  "up a shared writing credit near the end of it and the book "
                  "outright straight after. Skippable, but this is where the "
                  "look starts.",
         "items": arrival},
        {"id": "miller", "tier": 1, "title": "Miller & Janson",
         "sub": "#168–191 · 1981–1983",
         "links": links("v1"),
         "intro": "The run everything after it is measured against. Miller "
                  "writes all of it and draws most of it, handing the pencils "
                  "to Klaus Janson for six issues near the end, and "
                  "the book turns from a superhero comic into a crime one.",
         "items": miller},
        {"id": "bornagain", "tier": 1, "title": "Badlands and Born Again",
         "sub": "1985–1986 · the second stint, with Mazzucchelli",
         "links": links("v1"),
         "intro": "Miller comes back twice: once for a single issue drawn by "
                  "John Buscema, then for the seven-issue story that most "
                  "people mean when they say his Daredevil. David "
                  "Mazzucchelli draws that one, from the handover issue on.",
         "items": badlands + handover + born},
        {"id": "mwf", "tier": 2, "title": "The Man Without Fear",
         "sub": "1993–1994 · the origin, written last",
         "links": links("mwf"),
         "intro": "Miller and John Romita Jr. go back to the beginning, seven "
                  "years after Born Again. It sits here in publication order "
                  "and reads fine anywhere.",
         "items": mwf},
        {"id": "knights", "tier": 2, "title": "Marvel Knights",
         "sub": "1998–2001 · the relaunch Bendis inherits",
         "links": links("v2"),
         "intro": "Kevin Smith and Joe Quesada restart the book at #1 for "
                  "Marvel Knights, then David Mack takes the writing. This is "
                  "the setup the next run opens on, which is the only reason "
                  "it is here.",
         "items": knights},
        {"id": "wakeup", "tier": 1, "title": "Wake Up",
         "sub": "2001 · Bendis's first Daredevil story",
         "links": links("v2"),
         "intro": "Four issues drawn by David Mack, told from outside the "
                  "costume. It stands alone and it is the on-ramp.",
         "items": wakeup},
        {"id": "bendis", "tier": 1, "title": "Bendis & Maleev",
         "sub": "#20–81 · 2001–2006",
         "links": links("v2"),
         "intro": "The longest single Daredevil run there is, and the one that "
                  "set the tone for everything since: procedural, claustrophobic "
                  "and shot in Alex Maleev's photographic murk. Two fill-in "
                  "stretches by other writers are marked optional where they "
                  "fall.",
         "items": gale + bendis_a + mack + bendis_b},
        {"id": "brubaker", "tier": 1, "title": "Brubaker & Lark",
         "sub": "#82–500 · 2006–2009",
         "links": links("v2"),
         "intro": "Ed Brubaker and Michael Lark start on the page after Bendis "
                  "stops, keep the crime-comic register, and hand the title "
                  "back to its original numbering at the end.",
         "items": bru},
        {"id": "shadowland", "tier": 3, "title": "Diggle and Shadowland",
         "sub": "2009–2011 · the stretch the next run is a reaction to",
         "links": links("v2", "sl", "rb"),
         "intro": "Andy Diggle's run, the crossover it builds to and the "
                  "bridge out of it, interleaved in the order they went on "
                  "sale. Genuinely optional — Waid's first issue explains "
                  "where things stand without it — but it is the reason his "
                  "run looks the way it does.",
         "items": diggle},
        {"id": "waid3", "tier": 1, "title": "Waid, Rivera & Martin",
         "sub": "2011–2014 · a deliberate hard turn",
         "links": links("v3"),
         "intro": "Mark Waid restarts at #1 and takes the book back into "
                  "daylight: bright, buoyant, and drawn by Paolo Rivera and "
                  "Marcos Martin before Chris Samnee settles in as the "
                  "regular artist.",
         "items": waid3},
        {"id": "waid4", "tier": 1, "title": "Waid & Samnee in San Francisco",
         "sub": "2014–2015 · same creators, new coast",
         "links": links("v4"),
         "intro": "The same run, renumbered and relocated. Read it straight on "
                  "from the section above.",
         "items": waid4},
        {"id": "soule", "tier": 3, "title": "Soule & Garney",
         "sub": "2016–2019 · between Waid and Zdarsky",
         "links": links("v5"),
         "intro": "Charles Soule's run, drawn first by Ron Garney. Optional in "
                  "the same way Diggle's is: the next run opens cleanly "
                  "without it, and reads a little sharper with it.",
         "items": soule},
        {"id": "zdarsky", "tier": 1, "title": "Zdarsky & Checchetto",
         "sub": "2019–2021 · the longest run since Bendis",
         "links": links("v6"),
         "intro": "Chip Zdarsky and Marco Checchetto take the crime-comic "
                  "version of the book and push it as far as it goes. Reads as "
                  "one continuous story from here to the end of the list.",
         "items": zd6},
        {"id": "devilsreign", "tier": 1, "title": "Devil's Reign",
         "sub": "2022 · the run goes line-wide",
         "links": links("dr", "wwf"),
         "intro": "Zdarsky's run continues as a Marvel event and a companion "
                  "miniseries, interleaved here in the order they went on "
                  "sale.",
         "items": event},
        {"id": "redfist", "tier": 1, "title": "The Red Fist Saga",
         "sub": "2022–2023 · the finish",
         "links": links("v7"),
         "intro": "One more renumbering, one continuous story, and the end of "
                  "the run.",
         "items": zd7},
    ]


def main():
    sections = build()
    rows = sum(len(s["items"]) for s in sections)
    tier1 = sum(len(s["items"]) for s in sections if s["tier"] == 1)
    assert rows == len({x["id"] for s in sections for x in s["items"]}), \
        "duplicate row id"
    for s in sections:
        for x in s["items"]:
            assert not x.get("w") and "w" not in x, \
                "comics lists are unweighted (CLU-131): %s" % x["id"]

    # A section whose sub names an issue range has to name the rows it holds:
    # the Bendis sub read "#26-81" over rows that start at #20.
    for sec in sections:
        head = sec["sub"].split(" ")[0]
        if head.startswith("#"):
            lo, hi = head[1:].split("–")
            assert (sec["items"][0]["n"], sec["items"][-1]["n"]) ==                 ("#" + lo, "#" + hi),                 "%s runs %s-%s, not %s" % (sec["id"], sec["items"][0]["n"],
                                           sec["items"][-1]["n"], head)

    # The list claims publication order, so prove it: every section's rows run
    # forwards on their on-sale dates, and each section starts no earlier than
    # the one above it ends. Every row is checked — there is no exemption.
    last = None
    for s in sections:
        dates = [onsale(x) for x in s["items"]]
        assert dates == sorted(dates), "%s is out of publication order" % s["id"]
        assert last is None or dates[0] >= last, \
            "%s starts before the section above it ends" % s["id"]
        last = dates[-1]

    p = {
        "slug": SLUG,
        "title": "Daredevil",
        "subtitle": "Miller to Zdarsky · main-line Marvel continuity",
        "kind": "comics",
        "popularity": 68,
        "year": "1979–2023",
        "blurb": "The five runs that make up the modern character — Miller, "
                 "Bendis, Brubaker, Waid, Zdarsky — in the order they were "
                 "published, with the lead-ins that explain how each one "
                 "starts.",
        "unit": {"one": "issue", "many": "issues"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": "#A81C23",
        "accentDark": "#F2606A",
        "tiers": True,
        "notes": [
            ["One continuity, one man, no reboots.",
             "This is main-line Marvel — Earth-616 — from end to end. Matt "
             "Murdock's book has run more or less continuously since 1964 and "
             "nothing on this list is an alternate universe, a retelling or a "
             "restart of the character. The series itself restarts its "
             "numbering constantly; the story does not."],
            ["Tiers, barely.",
             "Tier 1 is the five runs, and it is most of the list, which is "
             "the point: they hand over to each other with nothing missing in "
             "between. Tier 2 is three shorter stretches around them — the "
             "two lead-ins that explain how a run opens, and Miller's origin "
             "miniseries. Tier 3 is the two stretches by other writers that "
             "sit between runs — good comics, skippable here. The minimum "
             "viable path is Tier 1 alone."],
            ["Which Daredevil is this.",
             "The book has relaunched at #1 six times, so every row names its "
             "series by launch year — Daredevil (1964), (1998), (2011), "
             "(2014), (2016), (2019), (2022). Two of those relaunches also "
             "reverted to the original numbering partway through, which is why "
             "#119 is followed by #500 and #28 by #595."],
            ["No spoilers.",
             "A note says what an issue is — a creator's first or last, a "
             "fill-in, a renumbering, where an arc opens — and never what "
             "happens in it. Stars mark the issues that matter more than their "
             "note suggests."],
            ["Links sit on the section headers.",
             "Each section links the Marvel Database page for every series it "
             "draws from; those pages list each issue with its credits and "
             "cover date. Rows carry no links of their own."],
            "Every issue number, on-sale date, cover date and creator credit "
            "read from the Marvel Database (marvel.fandom.com) through its API "
            "and cached in tools/data/daredevil.json, header links included. "
            "The run boundaries are derived from those printed credits by the "
            "generator, which refuses to build if a range is not exactly the "
            "writer it claims, or if any section falls out of publication "
            "order.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s" % out.name)
    print("  %d sections, %d issues (%d tier 1)"
          % (len(sections), rows, tier1))
    for s in sections:
        print("   T%d %-34s %4d" % (s["tier"], s["title"][:34], len(s["items"])))


if __name__ == "__main__":
    main()
