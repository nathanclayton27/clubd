#!/usr/bin/env python3
"""Generate properties/wolverine.json — the solo spine, Hulk #181 to now.

    PYTHONIOENCODING=utf-8 python tools/make_wolverine.py

This is a CHARACTER READING LIST, not a publication history. Wolverine has
appeared in something over five thousand comics and nobody reads that; what
follows is the sequence somebody should actually read, in publication order,
one section per run, rows as issues. It is a house pick. Veto freely.

WHAT IT IS NOT: an X-Men list. His X-Men appearances are the bulk of his page
count and they belong to properties/x-men.json, which already carries both
flagship lineages complete. This list is the SOLO spine — the books with his
name on the cover, plus the two Marvel Comics Presents serials where he was
the lead strip, plus the two Hulk issues he walks in through. The eight years
between his debut and his first solo series are X-Men issues and are not here.

THE TWO PLACES THE TWO LISTS TOUCH, and both are deliberate:

  * Wolverine (1982) #1-4. x-men carries it as ONE bundled row, `xm-wolv82`,
    weighted four, spliced into its Uncanny #171/#172 gap. This list carries
    the same four issues as four rows, because the Claremont/Miller miniseries
    is the front door to the solo spine and a Wolverine list without it is
    broken. The ids differ, so nothing collides; what a reader sees is one
    bundled row there and four issue rows here.
  * Wolverine (2020) #6-7 are X of Swords chapters 3 and 16, and x-men counts
    them inside its single bundled `xm-xos` row. They stay here because they
    are issues of the solo book and a reader of Percy's run cannot skip two of
    it.

Both ids are asserted against properties/x-men.json at build time, so if that
list ever stops bundling them this generator fails instead of quietly shipping
a note that has become false.

NOTHING IS TYPED FROM MEMORY. Every issue number, cover date, on-sale date and
creator credit is read out of tools/data/wolverine.json, which
scratch/agent-wolverine/fetch.py + parse.py harvested from the Marvel Database
(marvel.fandom.com) — `list=allpages` for the issue pages that exist in each
volume, then `prop=revisions` for each page's Comic Template infobox, and
`prop=revisions|info` for the volume pages whose canonical URLs the section
headers link to. Run boundaries are not transcribed from a reading order:
`writer_run()` reads the printed writer credit on every issue in a range and
fails the build if the range is not exactly that writer's, and
`not_written_by()` proves the run really does stop where the section says.

WHAT THE SOURCE CORRECTED. "Enemy of the State" is Wolverine (2003) #20-25,
six issues, not the thirteen Millar wrote: #26-31 are "Agent of S.H.I.E.L.D."
and #32 is a coda. The section is named for the run, not for the arc, and the
arc boundaries inside it are read off the printed story titles.

UNWEIGHTED, like every comics list here: nobody publishes a per-issue reading
time and this list does not invent one (CLU-131).

NOTES SAY WHAT AN ISSUE IS — a creator's first or last, a fill-in, a
renumbering, which arc opens, whose debut it is — and never what happens in
it. Stars carry the "this one matters" signal so a note never has to.
"""
import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop  # noqa: E402

SLUG = "wolverine"
HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "data" / (SLUG + ".json")
XMEN = HERE.parent / "properties" / "x-men.json"

TODAY = datetime.datetime(2026, 9, 11)

# series key -> (Marvel Database page, row title, id prefix, header label).
# The header URL is NOT here: it comes from the harvest, which read each volume
# page's own canonical url, so a section link cannot be a typo.
SER = {
    "hulk": ("Incredible Hulk Vol 1", "Incredible Hulk", "hulk",
             "Incredible Hulk (1962)"),
    "ls": ("Wolverine Vol 1", "Wolverine (1982)", "ls", "Wolverine (1982)"),
    "mcp": ("Marvel Comics Presents Vol 1", "Marvel Comics Presents", "mcp",
            "Marvel Comics Presents"),
    "v2": ("Wolverine Vol 2", "Wolverine (1988)", "v2", "Wolverine (1988)"),
    "origin": ("Wolverine: The Origin Vol 1", "Wolverine: The Origin", "or",
               "The Origin"),
    "v3": ("Wolverine Vol 3", "Wolverine (2003)", "v3", "Wolverine (2003)"),
    "logan": ("Logan Vol 1", "Logan", "lg", "Logan (2008)"),
    "gsoml": ("Wolverine: Old Man Logan Giant-Size Vol 1",
              "Giant-Size Old Man Logan", "gsoml", "Giant-Size Old Man Logan"),
    "awx": ("Wolverine Weapon X Vol 1", "Wolverine: Weapon X", "awx",
            "Wolverine: Weapon X (2009)"),
    "v4": ("Wolverine Vol 4", "Wolverine (2010)", "v4", "Wolverine (2010)"),
    "dow": ("Death of Wolverine Vol 1", "Death of Wolverine", "dow",
            "Death of Wolverine"),
    "row": ("Return of Wolverine Vol 1", "Return of Wolverine", "row",
            "Return of Wolverine"),
    "v7": ("Wolverine Vol 7", "Wolverine (2020)", "v7", "Wolverine (2020)"),
    "v8": ("Wolverine Vol 8", "Wolverine (2024)", "v8", "Wolverine (2024)"),
}

# The two rows properties/x-men.json bundles rather than itemises. Checked
# against that file so the overlap note cannot rot into a lie.
XMEN_BUNDLED = ("xm-wolv82", "xm-xos")

# The last issue of the current run that has shipped. A dated constant rather
# than `datetime.now()` so two runs of this generator are byte-identical
# forever, and asserted against the harvested on-sale dates either side of it.
AHMED_THROUGH = 27

# Row notes and stars, keyed by (series key, issue number as printed).
# Everything else ships with an empty note on purpose — an unannotated issue is
# an ordinary chapter of the run it sits in, and saying so 300 times is noise.
NOTES = {
    ("hulk", "180"): ("His first appearance, on the last page.", 0),
    ("hulk", "181"): ("His first full appearance. Len Wein and Herb Trimpe.",
                      1),
    ("ls", "1"): ("The first Wolverine story with his name on the cover — "
                  "Chris Claremont and Frank Miller.", 2),
    ("ls", "4"): ("The last of the four.", 0),
    ("mcp", "1"): ("“Save the Tiger” begins, a ten-part serial in the front "
                   "of an anthology.", 0),
    ("mcp", "10"): ("The serial's conclusion.", 0),
    ("mcp", "72"): ("“Weapon X” begins. Barry Windsor-Smith writes, pencils, "
                    "inks, colours and letters it.", 2),
    ("mcp", "84"): ("The twelfth and last chapter.", 1),
    ("v2", "1"): ("The ongoing series starts, by the same team as “Save the "
                  "Tiger”.", 2),
    ("v2", "9"): ("A fill-in: Peter David and Gene Colan.", 0),
    ("v2", "10"): ("Claremont's last issue of the ongoing.", 1),
    ("v2", "11"): ("Peter David takes over as writer.", 0),
    ("v2", "17"): ("Archie Goodwin and John Byrne begin.", 0),
    ("v2", "24"): ("A one-off by Peter David and Gene Colan.", 0),
    ("v2", "25"): ("Jo Duffy writes the next six.", 0),
    ("v2", "31"): ("Larry Hama's first issue, with Marc Silvestri on "
                   "pencils.", 2),
    ("v2", "35"): ("“Blood and Claws” begins.", 0),
    ("v2", "44"): ("A fill-in written by Peter David.", 0),
    ("v2", "48"): ("“The Shiva Scenario” begins.", 0),
    ("v2", "51"): ("“The Crunch Conundrum” begins, drawn by Andy Kubert.", 0),
    ("v2", "54"): ("A fill-in written by Fabian Nicieza.", 0),
    ("v2", "57"): ("Silvestri's last issue of the run.", 1),
    ("v2", "58"): ("Two issues by D.G. Chichester, sitting inside Hama's "
                   "run.", 0),
    ("v2", "60"): ("Hama back, and a new regular artist every few months from "
                   "here.", 0),
    ("v2", "75"): ("Adam Kubert's first, and the regular artist for most of "
                   "the next thirty.", 1),
    ("v2", "85"): ("A Phalanx Covenant chapter, read inside the run.", 0),
    ("v2", "110"): ("A fill-in written by Tom DeFalco.", 0),
    ("v2", "118"): ("Hama's last issue, after eighty-three of them.", 1),
    ("v2", "119"): ("“Not Dead Yet” begins — Warren Ellis and Leinil Francis "
                    "Yu.", 2),
    ("v2", "122"): ("Part four, and this list's last issue of the 1988 "
                    "series.", 1),
    ("origin", "1"): ("The origin, told twenty-seven years in. Paul Jenkins "
                      "and Andy Kubert.", 1),
    ("v3", "1"): ("Greg Rucka and Darick Robertson relaunch at #1 — "
                  "“Brotherhood”.", 1),
    ("v3", "7"): ("“Coyote Crossing” begins.", 0),
    ("v3", "13"): ("“Return of the Native” begins.", 0),
    ("v3", "19"): ("Rucka's last issue.", 1),
    ("v3", "20"): ("“Enemy of the State” begins — Mark Millar and John Romita "
                   "Jr.", 2),
    ("v3", "25"): ("The sixth and last part of “Enemy of the State”.", 1),
    ("v3", "26"): ("“Agent of S.H.I.E.L.D.”, the run's second half, begins "
                   "here.", 0),
    ("v3", "32"): ("Millar's last issue, drawn by Kaare Andrews.", 1),
    ("v3", "66"): ("“Old Man Logan” begins — Millar and Steve McNiven.", 2),
    ("v3", "72"): ("The seventh part. The conclusion is the Giant-Size "
                   "below.", 0),
    ("gsoml", "1"): ("“Old Man Logan: Conclusion”, four months after part "
                     "seven.", 1),
    ("logan", "1"): ("A three-issue story by Brian K. Vaughan and Eduardo "
                     "Risso.", 0),
    ("awx", "1"): ("Jason Aaron and Ron Garney start the run — “The "
                   "Adamantium Men”.", 2),
    ("awx", "6"): ("“Insane in the Brain” begins.", 0),
    ("awx", "11"): ("“Tomorrow Dies Today” begins.", 0),
    ("awx", "16"): ("The last issue under this title; the run carries "
                    "straight on below.", 1),
    ("v4", "1"): ("Same writer, new numbering.", 1),
    ("v4", "5.1"): ("A standalone .1 issue, drawn by Jefte Palo.", 0),
    ("v4", "6"): ("“Wolverine vs. the X-Men” begins, inside the solo book.",
                  0),
    ("v4", "10"): ("“Wolverine's Revenge!” begins.", 0),
    ("v4", "17"): ("“Goodbye Chinatown” begins.", 0),
    ("v4", "300"): ("The original numbering comes back, and “Back in Japan” "
                    "begins.", 1),
    ("v4", "304"): ("Aaron's last issue.", 1),
    ("dow", "1"): ("Charles Soule and Steve McNiven, a weekly miniseries.",
                   1),
    ("row", "1"): ("Soule again, four years later, with McNiven back on "
                   "the first and last.", 1),
    ("v7", "1"): ("Benjamin Percy and Adam Kubert open the Krakoa-era solo "
                  "book.", 1),
    ("v7", "6"): ("X of Swords chapter 3.", 0),
    ("v7", "7"): ("X of Swords chapter 16, co-written with Gerry Duggan.", 0),
    ("v7", "26"): ("“The Beast Agenda” begins.", 0),
    ("v7", "31"): ("“Weapons of X” begins.", 0),
    ("v7", "37"): ("“Last Mutant Standing” begins.", 0),
    ("v7", "41"): ("“Sabretooth War” begins, co-written with Victor "
                   "LaValle.", 0),
    ("v7", "50"): ("The last issue of the run.", 1),
    ("v8", "1"): ("Saladin Ahmed and Martin Coccolo begin the current "
                  "series.", 1),
}

# Fill-ins by other hands sitting inside a run, and the one .1 issue.
OPTIONAL = {("v2", "9"), ("v2", "24"), ("v2", "44"), ("v2", "54"),
            ("v2", "58"), ("v2", "59"), ("v2", "110"), ("v4", "5.1")}


def load():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    idx = {}
    for r in d["issues"]:
        idx[(r["vol"], r["numtext"])] = r
    assert len(idx) == len(d["issues"]), "duplicate issue in the harvest"
    return d, idx


D, IDX = load()


def fetch(key, num):
    """The harvested row for one issue, or a hard failure."""
    page = SER[key][0]
    r = IDX.get((page, str(num)))
    assert r, "%s #%s is not in tools/data/%s.json" % (page, num, SLUG)
    return r


def item(key, num):
    """One row, built entirely from the harvest plus the notes table above."""
    r = fetch(key, num)
    _, title, pre, _ = SER[key]
    note, star = NOTES.get((key, str(num)), ("", 0))
    return {
        "id": "%s-%s-%s" % (SLUG[:4], pre, str(num).replace(".", "-")),
        "t": title,
        "n": "#%s" % r["numtext"],
        "note": note,
        "star": star,
        "opt": 1 if (key, str(num)) in OPTIONAL else 0,
    }


def nums(key, lo, hi):
    """Every issue the wiki lists for this series between lo and hi, in order,
    point-ones included — so a .1 issue can never be silently skipped."""
    page = SER[key][0]
    out = [r for r in D["issues"] if r["vol"] == page and lo <= r["num"] <= hi]
    out.sort(key=lambda r: r["num"])
    assert out, "no issues of %s between %s and %s" % (page, lo, hi)
    return [r["numtext"] for r in out]


def rng(key, lo, hi):
    return [item(key, n) for n in nums(key, lo, hi)]


def writer_run(key, lo, hi, who, whole=True):
    """Assert the printed credits over a range, and hand back the rows.

    `whole` means every issue in the range is credited to `who`; without it,
    `who` merely has to appear somewhere in the issue's credits. This is the
    assertion the file rests on — the run boundaries are read off the wiki's
    own credits rather than typed in from a reading order.
    """
    got = nums(key, lo, hi)
    for n in got:
        r = fetch(key, n)
        names = r["lead"] if whole else r["writers"]
        assert who in names, \
            "%s #%s is credited to %s, not %s" % (SER[key][0], n,
                                                  names or "nobody", who)
    return [item(key, n) for n in got]


def mostly_written_by(key, lo, hi, who, holes):
    """A long run with named fill-ins inside it: every issue in the range is
    `who` except exactly the ones listed, and each of those is somebody else.
    Both halves are checked, so a fill-in that stops being one — or a new one
    the wiki has since credited — fails the build."""
    got = nums(key, lo, hi)
    for n in got:
        led_by_who = who in fetch(key, n)["lead"]
        if n in holes:
            assert not led_by_who, \
                "%s #%s is credited to %s after all" % (SER[key][0], n, who)
        else:
            assert led_by_who, \
                "%s #%s is credited to %s, not %s" \
                % (SER[key][0], n, fetch(key, n)["lead"] or "nobody", who)
    assert set(holes) <= set(got), \
        "fill-in outside the range: %s" % sorted(set(holes) - set(got))
    return [item(key, n) for n in got]


def not_written_by(key, lo, hi, who):
    """The other half of a boundary: prove the run really does stop here."""
    for n in nums(key, lo, hi):
        assert who not in fetch(key, n)["writers"], \
            "%s #%s is credited to %s after all" % (SER[key][0], n, who)


def penciler(key, num, who):
    """Assert a drawing credit a note or an intro leans on."""
    got = fetch(key, num)["penciler"]
    # the wiki spells a few names both with and without diacritics
    ok = got == who or got.encode("ascii", "ignore").decode() == who
    assert ok, "%s #%s is pencilled by %s, not %s" \
        % (SER[key][0], num, got, who)


def serial(key, lo, hi, who, prefix):
    """A serial in the front of an anthology. Marvel Comics Presents ran three
    strips an issue; the Wolverine one is story 1 in every issue this list
    touches, and that — not just the issue's credits — is what is checked, so
    a row can never point at somebody else's strip."""
    got = nums(key, lo, hi)
    for n in got:
        r = fetch(key, n)
        s1 = r["stories"][0]
        assert s1["n"] == 1, "%s #%s has no first story" % (SER[key][0], n)
        assert who in s1["writers"], \
            "%s #%s story 1 is written by %s, not %s" \
            % (SER[key][0], n, s1["writers"] or "nobody", who)
        assert prefix.lower() in s1["title"].lower(), \
            "%s #%s story 1 is %r, not a %s chapter" \
            % (SER[key][0], n, s1["title"], prefix)
    return [item(key, n) for n in got]


def links(*keys):
    """Header links, with every URL taken from the harvested volume page."""
    out = []
    for k in keys:
        page, _, _, label = SER[k]
        v = D["volumes"].get(page)
        assert v and v["url"].startswith("https://marvel.fandom.com/wiki/"), \
            "no harvested url for %s" % page
        out.append({"label": label, "url": v["url"]})
    return out


PRE_OF = {v[2]: k for k, v in SER.items()}


def onsale(x):
    """The on-sale date behind a built row, as a datetime."""
    key = PRE_OF[x["id"].split("-")[1]]
    return datetime.datetime.strptime(
        fetch(key, x["n"][1:])["released"], "%B %d, %Y")


def build():
    # ---- the two Hulk issues -------------------------------------------
    # A debut is a claim about a source, so it is read off the source: the
    # Marvel Database tags Wolverine's bullet {{1st}}{{Cameo}} in #180 and
    # {{1stFull}} in #181, and does not mention him in #179 at all.
    assert not fetch("hulk", 179)["wolverine"]["present"], \
        "#179 already has Wolverine in it"
    a = fetch("hulk", 180)["wolverine"]
    assert a["first"] and a["cameo"] and not a["firstfull"], \
        "#180 is no longer the first-appearance cameo"
    assert fetch("hulk", 181)["wolverine"]["firstfull"], \
        "#181 is no longer the first full appearance"
    for n in (180, 181):
        assert fetch("hulk", n)["lead"] == ["Len Wein"]
        penciler("hulk", n, "Herb Trimpe")
    debut = [item("hulk", 180), item("hulk", 181)]

    # ---- Claremont and Miller ------------------------------------------
    mini = writer_run("ls", 1, 4, "Chris Claremont")
    assert len(mini) == 4, "the 1982 series is no longer four issues"
    for n in nums("ls", 1, 4):
        penciler("ls", n, "Frank Miller")

    # ---- Save the Tiger, in the front of Marvel Comics Presents ---------
    tiger = serial("mcp", 1, 10, "Chris Claremont", "Save the Tiger")
    assert len(tiger) == 10, "Save the Tiger is no longer ten parts"
    for n in nums("mcp", 1, 10):
        assert fetch("mcp", n)["stories"][0]["penciler"] == "John Buscema"
    # and the strip is a Wolverine one only up to #10 — #11 is somebody else's
    assert "Save the Tiger" not in fetch("mcp", 11)["stories"][0]["title"]

    # ---- the ongoing: Claremont's ten ----------------------------------
    # #9 is a Peter David fill-in sitting inside the stretch, which is why
    # this is mostly_written_by rather than writer_run.
    madripoor = mostly_written_by("v2", 1, 10, "Chris Claremont", {"9"})
    for n in nums("v2", 1, 10):
        if n != "9":
            assert fetch("v2", n)["penciler"] == "John Buscema", \
                "#%s is not pencilled by Buscema" % n
    not_written_by("v2", 11, 24, "Chris Claremont")

    # ---- the stretch between the two long runs -------------------------
    between = rng("v2", 11, 30)
    for n, who in (("11", "Peter David"), ("17", "Archie Goodwin"),
                   ("24", "Peter David"), ("25", "Jo Duffy")):
        assert who in fetch("v2", n)["lead"], \
            "#%s is no longer led by %s" % (n, who)
    penciler("v2", 17, "John Byrne")
    for n in nums("v2", 11, 30):
        assert "Larry Hama" not in fetch("v2", n)["writers"], \
            "#%s already credits Hama" % n

    # ---- Hama, in three sections because Weapon X interrupts it ---------
    # Hama writes #31-118 with five fill-ins by other hands inside it. The
    # split points are not editorial: MCP #72 went on sale between #37 and
    # #38, so the run is cut exactly where a 1991 reader's month was cut.
    hama1 = writer_run("v2", 31, 37, "Larry Hama")
    for n in nums("v2", 31, 37):
        penciler("v2", n, "Marc Silvestri")

    weaponx = serial("mcp", 72, 84, "Barry Windsor-Smith", "Weapon X")
    assert len(weaponx) == 13, "Weapon X is no longer thirteen chapters"
    for n in nums("mcp", 72, 84):
        s1 = fetch("mcp", n)["stories"][0]
        assert s1["penciler"] == "Barry Windsor-Smith", \
            "MCP #%s story 1 is not pencilled by Windsor-Smith" % n
    assert fetch("mcp", 72)["stories"][0]["title"] == "Weapon X: Prologue"
    assert fetch("mcp", 84)["stories"][0]["title"] == "Weapon X: Chapter Twelve"
    # it really is a Wolverine serial that starts and stops there
    for n in (71, 85):
        assert "Weapon X" not in fetch("mcp", n)["stories"][0]["title"], \
            "MCP #%s is a Weapon X chapter after all" % n
    assert onsale(hama1[-1]) < onsale(weaponx[0]) < onsale(item("v2", 38)), \
        "Weapon X no longer goes on sale between Wolverine #37 and #38"

    hama2 = mostly_written_by("v2", 38, 57, "Larry Hama", {"44", "54"})
    sil = [n for n in nums("v2", 38, 57)
           if fetch("v2", n)["penciler"] == "Marc Silvestri"]
    assert len(sil) > len(hama2) / 2, \
        "Silvestri is no longer the regular artist of #38-57"
    penciler("v2", 51, "Andy Kubert")
    penciler("v2", 57, "Marc Silvestri")
    assert fetch("v2", 58)["penciler"] != "Marc Silvestri", \
        "#57 is no longer Silvestri's last"

    hama3 = mostly_written_by("v2", 58, 118, "Larry Hama",
                              {"58", "59", "110"})
    assert "D.G. Chichester" in fetch("v2", 58)["lead"]
    assert "D.G. Chichester" in fetch("v2", 59)["lead"]
    assert "Tom DeFalco" in fetch("v2", 110)["lead"]
    # "the regular artist for most of the next thirty" on the #75 note
    ak = [n for n in nums("v2", 75, 102)
          if fetch("v2", n)["penciler"] == "Adam Kubert"]
    assert len(ak) > len(nums("v2", 75, 102)) / 2, \
        "Adam Kubert is no longer the regular artist from #75"
    for n in nums("v2", 60, 74):
        assert fetch("v2", n)["penciler"] != "Adam Kubert", \
            "#%s already has Adam Kubert on pencils" % n
    hama_total = len([x for x in hama1 + hama2 + hama3 if not x["opt"]])
    assert hama_total == 83, "Hama's tally is %d, not 83" % hama_total
    not_written_by("v2", 119, 122, "Larry Hama")

    # ---- Ellis and Yu -------------------------------------------------
    ellis = writer_run("v2", 119, 122, "Warren Ellis")
    for n in nums("v2", 119, 122):
        penciler("v2", n, "Leinil Francis Yu")
        assert "Not Dead Yet" in fetch("v2", n)["arcs"], \
            "#%s is not filed under Not Dead Yet" % n

    # ---- the origin miniseries ----------------------------------------
    origin = writer_run("origin", 1, 6, "Paul Jenkins", whole=False)
    for n in nums("origin", 1, 6):
        penciler("origin", n, "Andy Kubert")

    # ---- the 2003 relaunch --------------------------------------------
    rucka = writer_run("v3", 1, 19, "Greg Rucka")
    penciler("v3", 1, "Darick Robertson")
    not_written_by("v3", 20, 32, "Greg Rucka")
    millar = writer_run("v3", 20, 32, "Mark Millar")
    for n in nums("v3", 20, 25):
        assert "Enemy of the State" in fetch("v3", n)["arcs"], \
            "#%s is not an Enemy of the State chapter" % n
    for n in nums("v3", 26, 31):
        assert "Agent of S.H.I.E.L.D." in fetch("v3", n)["arcs"], \
            "#%s is not an Agent of S.H.I.E.L.D. chapter" % n
    # the correction this file exists to record: the famous arc is six issues
    assert "Enemy of the State" not in fetch("v3", 26)["arcs"], \
        "Enemy of the State now runs past #25"
    for n in nums("v3", 20, 31):
        penciler("v3", n, "John Romita Jr.")
    penciler("v3", 32, "Kaare Andrews")

    # ---- Vaughan and Risso --------------------------------------------
    logan = writer_run("logan", 1, 3, "Brian K. Vaughan")
    for n in nums("logan", 1, 3):
        penciler("logan", n, "Eduardo Risso")

    # ---- Old Man Logan ------------------------------------------------
    # Seven parts in the parent title and a Giant-Size conclusion four months
    # later, which is why the section is dated rather than numbered.
    oml = writer_run("v3", 66, 72, "Mark Millar")
    for n in nums("v3", 66, 72):
        penciler("v3", n, "Steve McNiven")
        assert "Old Man Logan" in fetch("v3", n)["arcs"], \
            "#%s is not an Old Man Logan chapter" % n
    gs = writer_run("gsoml", 1, 1, "Mark Millar")
    penciler("gsoml", 1, "Steve McNiven")
    assert fetch("gsoml", 1)["titles"] == ["Old Man Logan: Conclusion"], \
        "the Giant-Size is no longer the conclusion"
    gap = (onsale(gs[0]) - onsale(oml[-1])).days
    assert 100 < gap < 140, "the Giant-Size gap is now %d days" % gap
    # #73-74 are other people's issues and this list does not carry them
    assert "Mark Millar" not in fetch("v3", 73)["writers"]

    # ---- Aaron, across two titles and one renumbering -------------------
    awx = writer_run("awx", 1, 16, "Jason Aaron")
    penciler("awx", 1, "Ron Garney")
    aaron = writer_run("v4", 1, 304, "Jason Aaron")
    assert [x["n"] for x in aaron][:6] == \
        ["#1", "#2", "#3", "#4", "#5", "#5.1"], \
        "the .1 issue is no longer the sixth row of Aaron's vol 4"
    for n in ("300", "301", "302", "303"):
        assert "Back In Japan" in fetch("v4", n)["arcs"], \
            "#%s is not a Back in Japan chapter" % n
    assert fetch("v4", 1)["legacy"] == "Wolverine Vol 2 280", \
        "vol 4 #1 no longer maps onto the old numbering at #280"
    not_written_by("v4", 305, 317, "Jason Aaron")
    assert onsale(aaron[0]) > onsale(awx[-1]), \
        "vol 4 #1 no longer ships after Weapon X #16"

    # ---- the two Soule and McNiven miniseries --------------------------
    death = writer_run("dow", 1, 4, "Charles Soule")
    for n in nums("dow", 1, 4):
        penciler("dow", n, "Steve McNiven")
    weekly = [onsale(x) for x in death]
    assert (weekly[-1] - weekly[0]).days < 50, \
        "Death of Wolverine no longer ships inside two months"
    ret = writer_run("row", 1, 5, "Charles Soule")
    # McNiven draws the bookends only — Declan Shalvey has the middle three,
    # which is why the section says "Soule again" rather than "the same pair".
    for n in ("1", "5"):
        penciler("row", n, "Steve McNiven")
    for n in ("2", "3", "4"):
        penciler("row", n, "Declan Shalvey")

    # ---- Percy -------------------------------------------------------
    percy = writer_run("v7", 1, 50, "Benjamin Percy", whole=False)
    penciler("v7", 1, "Adam Kubert")
    assert fetch("v7", 6)["titles"] == ["X of Swords: Chapter 03"]
    assert fetch("v7", 7)["titles"] == ["X of Swords: Chapter 16"]
    assert "Gerry Duggan" in fetch("v7", 7)["writers"]
    assert "Victor LaValle" in fetch("v7", 41)["writers"]
    assert len(percy) == 50, "Percy's run is no longer fifty issues"

    # ---- the book right now -------------------------------------------
    ahmed = writer_run("v8", 1, AHMED_THROUGH, "Saladin Ahmed")
    penciler("v8", 1, "Martin Coccolo")
    assert onsale(ahmed[-1]) <= TODAY, \
        "#%d has not shipped yet" % AHMED_THROUGH
    nxt = item("v8", AHMED_THROUGH + 1)
    assert onsale(nxt) > TODAY, \
        "#%d has shipped — raise AHMED_THROUGH" % (AHMED_THROUGH + 1)

    return [
        {"id": "debut", "tier": 3, "title": "Where he comes in",
         "sub": "1974 · two issues of somebody else's book",
         "links": links("hulk"),
         "intro": "Wolverine turns up on the last page of Incredible Hulk "
                  "#180 and fights for a whole issue in #181, eight years "
                  "before he gets a book of his own. What happens in between "
                  "is X-Men, and it is on the X-Men list here rather than on "
                  "this one — this list is the solo spine.",
         "items": debut},
        {"id": "claremiller", "tier": 1, "title": "Claremont & Miller",
         "sub": "#1–4 · 1982 · the miniseries",
         "open": True,
         "links": links("ls"),
         "intro": "Four issues that decided what a Wolverine story is: a "
                  "crime comic in Japan, written by the man who had been "
                  "writing him for seven years and drawn by the one who had "
                  "just finished reinventing Daredevil. Everything below is "
                  "downstream of it.\n\n"
                  "The X-Men list carries these four as a single bundled row "
                  "spliced into its 1982 run. They are four rows here, "
                  "because this is the front door.",
         "items": mini},
        {"id": "savethetiger", "tier": 2, "title": "Save the Tiger",
         "sub": "Marvel Comics Presents #1–10 · 1988",
         "links": links("mcp"),
         "intro": "Claremont and John Buscema serialise a Madripoor story "
                  "across the front strip of Marvel's new anthology, two "
                  "months before they launch the ongoing with it. The other "
                  "strips in each issue are other characters'; only the "
                  "Wolverine one is what this row points at.",
         "items": tiger},
        {"id": "madripoor", "tier": 1, "title": "Claremont & Buscema",
         "sub": "#1–10 · 1988–1989 · the ongoing starts",
         "links": links("v2"),
         "intro": "The first Wolverine monthly, by the team that had just "
                  "finished the serial above, and still in Madripoor. One "
                  "fill-in sits inside it and is marked as one.",
         "items": madripoor},
        {"id": "between", "tier": 3, "title": "Between the two long runs",
         "sub": "#11–30 · 1989–1990",
         "links": links("v2"),
         "intro": "Twenty issues by three writers in turn — Peter David, then "
                  "Archie Goodwin with John Byrne on pencils, then Jo Duffy. "
                  "Goodwin and Byrne's seven are the reason this section is "
                  "here at all. Skippable: the run below opens cleanly "
                  "without any of it.",
         "items": between},
        {"id": "hama1", "tier": 1, "title": "Hama takes the book",
         "sub": "#31–37 · 1990–1991 · with Marc Silvestri",
         "links": links("v2"),
         "intro": "Larry Hama's eighty-three issues start here and run for "
                  "seven years, which makes this the longest single "
                  "commitment on the list. It is cut into three sections at "
                  "the two points where something else went on sale in the "
                  "middle of it — the section below is the first of those.",
         "items": hama1},
        {"id": "weaponx", "tier": 1, "title": "Weapon X",
         "sub": "Marvel Comics Presents #72–84 · 1991",
         "links": links("mcp"),
         "intro": "Barry Windsor-Smith writes, draws, inks, colours and "
                  "letters thirteen chapters in the front of the anthology, "
                  "while Hama's monthly carries on around it. It is the one "
                  "story on this list that a reader who is reading nothing "
                  "else should still read, and it went on sale between "
                  "Wolverine #37 and #38, which is why it sits here.",
         "items": weaponx},
        {"id": "hama2", "tier": 1, "title": "Hama & Silvestri",
         "sub": "#38–57 · 1991–1992",
         "links": links("v2"),
         "intro": "Silvestri draws most of these, and #57 is his last on the "
                  "book. Two fill-ins by other writers are marked where they "
                  "fall.",
         "items": hama2},
        {"id": "hama3", "tier": 1, "title": "Hama through the nineties",
         "sub": "#58–118 · 1992–1997",
         "links": links("v2"),
         "intro": "The long middle: sixty-one issues, a new regular artist "
                  "every year or so, and Adam Kubert for most of the "
                  "stretch after #75. Three issues inside it are by other "
                  "writers and are marked.",
         "items": hama3},
        {"id": "notdeadyet", "tier": 2, "title": "Not Dead Yet",
         "sub": "#119–122 · 1997–1998 · Ellis and Yu",
         "links": links("v2"),
         "intro": "Warren Ellis and Leinil Francis Yu, straight after Hama "
                  "signs off. It stands alone, it is four issues, and it is "
                  "where this list leaves the 1988 series — the sixty-seven "
                  "issues after it are the stretch nobody recommends.",
         "items": ellis},
        {"id": "origin", "tier": 3, "title": "The Origin",
         "sub": "2001–2002 · written twenty-seven years in",
         "links": links("origin"),
         "intro": "Paul Jenkins and Andy Kubert fill in the backstory the "
                  "character had spent three decades not having. It is here "
                  "in publication order and reads fine anywhere, including "
                  "not at all — the rest of the list never depends on it.",
         "items": origin},
        {"id": "rucka", "tier": 3, "title": "Rucka & Robertson",
         "sub": "#1–19 · 2003–2004 · the relaunch",
         "links": links("v3"),
         "intro": "Greg Rucka restarts the book at #1 and writes it as small, "
                  "grim crime fiction — three arcs and a one-off. Optional in "
                  "the same way the section above is: the run below opens "
                  "without it and reads a shade better with it.",
         "items": rucka},
        {"id": "millar", "tier": 1, "title": "Millar & Romita Jr.",
         "sub": "#20–32 · 2004–2005",
         "links": links("v3"),
         "intro": "Two arcs and a coda. “Enemy of the State” is the first "
                  "six; “Agent of S.H.I.E.L.D.” is the six after it and is "
                  "the other half of the same story, which is why they are "
                  "one section rather than two.",
         "items": millar},
        {"id": "logan", "tier": 3, "title": "Logan",
         "sub": "#1–3 · 2008 · Vaughan and Risso",
         "links": links("logan"),
         "intro": "Three issues, one story, no connection to anything either "
                  "side of it. Here because it is very good and it is short.",
         "items": logan},
        {"id": "oldman", "tier": 1, "title": "Old Man Logan",
         "sub": "2008–2009 · Millar and McNiven",
         "links": links("v3", "gsoml"),
         "intro": "Millar's second stint on the book: a story set in a future "
                  "that is not this list's continuity, serialised in the "
                  "parent title and finished four months late in a Giant-Size "
                  "one-shot. Both are here, and the one-shot is part eight.\n\n"
                  "Everything Marvel published afterwards using the same "
                  "character is a different thing and is not on this list.",
         "items": oml + gs},
        {"id": "aaronwx", "tier": 1, "title": "Aaron & Garney",
         "sub": "Wolverine: Weapon X #1–16 · 2009–2010",
         "links": links("awx"),
         "intro": "Jason Aaron's run begins under its own title — three arcs, "
                  "sixteen issues — and carries straight on into the section "
                  "below without a break in the story. Read the two as one "
                  "run.",
         "items": awx},
        {"id": "aaron", "tier": 1, "title": "Aaron, renumbered",
         "sub": "2010–2012 · #1–20, then #300–304",
         "links": links("v4"),
         "intro": "The same run under the old title, restarted at #1 and then "
                  "reverting to the original numbering partway through, which "
                  "is why #20 is followed by #300. One standalone .1 issue is "
                  "marked optional where it went on sale.",
         "items": aaron},
        {"id": "death", "tier": 1, "title": "Death of Wolverine",
         "sub": "#1–4 · 2014 · Soule and McNiven",
         "links": links("dow"),
         "intro": "A four-issue miniseries published weekly. Charles Soule "
                  "wrote the book it grew out of; nothing on this list is "
                  "that book, and this reads cold.",
         "items": death},
        {"id": "return", "tier": 2, "title": "Return of Wolverine",
         "sub": "#1–5 · 2018–2019 · Soule again",
         "links": links("row"),
         "intro": "Charles Soule writes it again four years later, closing the "
                  "bracket he opened, with Steve McNiven on the first and last "
                  "issues and Declan Shalvey on the three between. Tier 2 "
                  "because it only means anything next to the section above "
                  "it.",
         "items": ret},
        {"id": "percy", "tier": 2, "title": "Percy's Wolverine",
         "sub": "#1–50 · 2020–2024",
         "links": links("v7"),
         "intro": "Fifty issues of the solo book through the Krakoa era, the "
                  "last ten of them a story co-written with Victor LaValle. "
                  "Two of them are X of Swords chapters, which the "
                  "X-Men list counts inside one bundled row of its own; they "
                  "are issues of this book, so they are rows here.",
         "items": percy},
        {"id": "ahmed", "tier": 3, "title": "The book right now",
         "sub": "2024– · Saladin Ahmed and Martin Coccolo",
         "links": links("v8"),
         "intro": "The current series, still being published. Rows run to the "
                  "last issue that has actually shipped and more arrive as it "
                  "does, so the list never carries an issue nobody can buy "
                  "yet.",
         "items": ahmed},
    ]


NOTESET = [
    ["Solo, and not his whole publication history.",
     "Wolverine has appeared in something over five thousand comics. Nobody "
     "reads that, and a list that tried would be unfinishable, so this is a "
     "house pick: the runs worth reading, in the order they were published, "
     "one section per run. Veto anything on it freely — the tiers are there "
     "so you can."],
    ["Where this list stops and the X-Men list starts.",
     "His X-Men appearances are the bulk of his page count and they belong to "
     "the X-Men list here, which carries both flagship lineages complete. "
     "This one carries the books with his name on the cover, the two Marvel "
     "Comics Presents serials where he was the lead strip, and the two Hulk "
     "issues he arrives in. Two things sit on both lists on purpose: the 1982 "
     "miniseries, which the X-Men list bundles into one row and this one "
     "itemises, and Wolverine (2020) #6–7, which are X of Swords chapters "
     "counted inside a single bundled row there. Ticks are separate either "
     "way — the ids are different — and nothing else is on both."],
    ["Rows are issues.",
     "Not collected volumes. A row is one comic, and a section is one run, so "
     "the page count you are looking at is the real one rather than a "
     "shelf's worth of spines."],
    ["Six series have been called Wolverine, so ids ignore the numbers.",
     "The solo book has restarted at #1 in 1982, 1988, 2003, 2010, 2013, "
     "2014, 2020 and 2024, and two of those reverted to the earlier "
     "numbering partway through — which is why #20 is followed by #300 in one "
     "section. Every row names its series by launch year, and no row id is "
     "derived from an issue number alone."],
    ["Tiers.",
     "Tier 1 is the spine: the miniseries, the Claremont ongoing, Weapon X, "
     "Hama's seven years, Millar, Old Man Logan, Aaron and the 2014 "
     "miniseries. Tier 2 "
     "is the shorter things that explain how a Tier 1 run opens or closes. "
     "Tier 3 is good comics that this list would not miss — the debut, the "
     "1989–90 stretch, the origin miniseries, Rucka, the Vaughan one-off and "
     "the current series. Tier 1 alone is a complete read."],
    ["What is deliberately missing.",
     "The 1988 series after #122; the 1998–2002 stretch and Frank Tieri's "
     "Weapon X; Daniel Way's fifty issues of Wolverine: Origins; the 2013–14 "
     "volumes; the later Old Man Logan series; and the out-of-continuity "
     "one-shots. Also the team books — Wolverine and the X-Men, X-Force, "
     "Uncanny — which are on the X-Men list where they belong. Say the word "
     "and any of them gets a section."],
    ["No spoilers.",
     "A note says what an issue is — whose first or last it is, a fill-in, a "
     "renumbering, which arc opens there, whose debut it is — and never what "
     "happens in it. Stars mark the issues that matter more than their note "
     "suggests."],
    ["Links sit on the section headers.",
     "Each section links the Marvel Database page for every series it draws "
     "from, and those pages list each issue with its credits and cover date. "
     "Rows carry no links of their own."],
    "Every issue number, cover date, on-sale date and creator credit read "
    "from the Marvel Database (marvel.fandom.com) through its API and cached "
    "in tools/data/wolverine.json, header links included. The run boundaries "
    "are derived from those printed credits by the generator, which refuses "
    "to build if a range is not exactly the writer it claims, if a Marvel "
    "Comics Presents row points at a strip that is not the Wolverine one, or "
    "if any section falls out of publication order.",
]


def main():
    sections = build()
    rows = sum(len(s["items"]) for s in sections)
    ids = {x["id"] for s in sections for x in s["items"]}
    assert rows == len(ids), "duplicate row id"

    for s in sections:
        for x in s["items"]:
            assert not x.get("w") and "w" not in x, \
                "comics lists are unweighted (CLU-131): %s" % x["id"]
            assert "url" not in x, \
                "comic rows carry no links: %s" % x["id"]

    # No id may be derivable from an issue number alone: every one carries its
    # series prefix, so the eight #1s on this list cannot collide.
    for i in sorted(ids):
        assert i.startswith("wolv-") and i.count("-") >= 2, "thin id %r" % i

    # The overlap note names two x-men rows. If that list stops bundling them,
    # the note has become false and this build should stop rather than ship it.
    xm = json.loads(XMEN.read_text(encoding="utf-8"))
    xm_ids = {x["id"] for s in xm["sections"] for x in s["items"]}
    for bid in XMEN_BUNDLED:
        assert bid in xm_ids, \
            "properties/x-men.json no longer carries %s — the overlap note " \
            "in this generator needs rewriting" % bid
    # and nothing this list ships may share an id with that one
    assert not (ids & xm_ids), "id shared with x-men: %s" % sorted(ids & xm_ids)

    # A sub whose first field is an issue range has to name the rows it holds.
    for s in sections:
        head = s["sub"].split(" ")[0]
        if head.startswith("#"):
            lo, hi = head[1:].split("–")
            assert (s["items"][0]["n"], s["items"][-1]["n"]) == \
                ("#" + lo, "#" + hi), \
                "%s runs %s-%s, not %s" % (s["id"], s["items"][0]["n"],
                                           s["items"][-1]["n"], head)

    # The list claims publication order, so prove it. Two books running in the
    # same months is the normal case here rather than an exception — Weapon X
    # ran alongside the monthly, and Aaron's two titles overlap the Old Man
    # Logan tail — so the rule is: every section's own rows run forwards, and
    # section STARTS never go backwards. Every row is checked.
    last = None
    for s in sections:
        dates = [onsale(x) for x in s["items"]]
        assert dates == sorted(dates), \
            "%s is out of publication order" % s["id"]
        assert last is None or dates[0] >= last, \
            "%s starts before the section above it does" % s["id"]
        last = dates[0]

    p = {
        "slug": SLUG,
        "title": "Wolverine",
        "subtitle": "the solo spine · a character reading list",
        "kind": "comics",
        "popularity": 74,
        "year": "1974–2026",
        "blurb": "The runs that made the character, as %d issues in "
                 "publication order — the Claremont/Miller miniseries, Weapon "
                 "X, Larry Hama's seven years on the ongoing, Old Man Logan, "
                 "Aaron, and the solo book since. His X-Men issues are on the "
                 "X-Men list." % rows,
        "unit": {"one": "issue", "many": "issues"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": "#7B5230",
        "accentDark": "#D9A468",
        "tiers": True,
        "notes": NOTESET,
        "sections": sections,
    }

    # CLU-545: every comics row on this site weighs ONE ISSUE, which is
    # Nathan's "issues, not collected volumes" ruling applied to the weight
    # as well as to the row. It makes the strip measure issues rather than
    # rows, and it is what lets a hub door into this list carry a real
    # weight instead of none. Stamped in one place rather than on every row
    # constructor: `w` is presentation and is not part of an id, so no tick
    # moves.
    for _sec in p["sections"]:
        for _row in _sec["items"]:
            _row["w"] = 1

    out = prop.write(p)
    print("wrote %s" % out.name)
    print("  %d sections, %d issues" % (len(sections), rows))
    for tier in (1, 2, 3):
        n = sum(len(s["items"]) for s in sections if s["tier"] == tier)
        print("  tier %d: %d issues" % (tier, n))
    print()
    for s in sections:
        d = [onsale(x) for x in s["items"]]
        print("   T%d %-26s %4d  %s–%s"
              % (s["tier"], s["title"][:26], len(s["items"]),
                 d[0].strftime("%Y-%m"), d[-1].strftime("%Y-%m")))


if __name__ == "__main__":
    main()
