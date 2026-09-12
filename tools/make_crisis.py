#!/usr/bin/env python3
"""Generate properties/crisis-on-infinite-earths.json.

    python3 tools/make_crisis.py            # build from tools/data/crisis.json
    python3 tools/make_crisis.py --fetch     # re-read the four sources first

The 1985 maxiseries and its crossover, interleaved. Crisis is the clearest case
in comics for why a reading order exists at all: the twelve issues are a
complete story, and the crossover around them is forty more issues published in
other people's books, in an order nobody can reconstruct from the covers.

WHERE THE ORDER COMES FROM
The spine is Comic Book Herald's issue-by-issue reading order, cross-checked
against comicbookreadingorders.com. The two agree on every issue they both
list; they differ only on where Wonder Woman #328-329 and Vigilante #22 fall,
and comicbookreadingorders.com omits five issues Comic Book Herald carries
(Losers Special #1, Legends of the DCU: Crisis #1, Wonder Woman #327, Legion of
Super-Heroes #17, New Teen Titans #14). This follows Comic Book Herald, which
is the superset, and both orders are parsed and asserted against on every fetch.

WHOSE TIE-IN LIST IT IS — the part that is contested
There is no single agreed tie-in list for Crisis, so this list uses the one
fact nobody disputes: DC printed a "Special Crisis Cross-Over" banner on the
covers of a specific set of issues. Wikipedia's Crisis article and the DC
Database both enumerate that set, independently, and this generator asserts
that the two enumerations are identical before it will write anything. That
banner set is tier 2. Everything the guides place in the order that never
carried the banner — the Batman/Detective six-parter, Vigilante #22, Swamp
Thing #44-45, Legion of Super-Heroes #16-17, Green Lantern #196-197 — is
tier 3, and says so.

THE TIERS
  1  the maxiseries, plus the three DC Comics Presents issues, which are the
     only tie-ins either guide singles out as worth reading for themselves.
  2  the rest of the banner crossover, in reading position.
  3  the unbannered issues the guides carry anyway, and the run of
     pre-Crisis Monitor cameos that comicbookreadingorders.com enumerates and
     then tells you to skip.

NO WEIGHTS. A row is an issue and comics publish no per-issue reading time.

NOTES ARE SPOILER-FREE. This event is famous for what happens in it, and a
reading order is a thing you read BEFORE. So a note says what an issue is, who
made it or how a guide rates it, and never what occurs. The maxiseries' own
chapter titles are not used as section headings for exactly that reason — half
of them give the issue away.

One row is placed by neither guide: Blue Devil #17 carries the banner in both
enumerations of it but appears in neither reading order, so it sits beside #18
and the note says so. Wikipedia's banner list also carries JLA: Incarnations #5
(2001), which neither guide places anywhere; it is not on this list.
"""
import argparse
import html
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop as gwprop  # noqa: E402
from gwlib import wiki  # noqa: E402

SLUG = "crisis-on-infinite-earths"
HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "data" / "crisis.json"
CACHE = HERE.parent / "scratch" / "coie"

CBH_URL = "https://www.comicbookherald.com/crisis-on-infinite-earths-reading-order/"
CBRO_URL = ("https://comicbookreadingorders.com/dc/events/"
            "crisis-on-infinite-earths-reading-order/")
DCDB = "dc.fandom.com"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# ---------------------------------------------------------------- the series
# key -> (display title, DC Database page prefix). The display title carries a
# volume only where 1985 had two live books of the same name and a reader would
# otherwise pull the wrong one off the shelf.
#
# Two mappings are not the identity and are the reason this table exists:
#   * "Tales of the Legion of Super-Heroes" was the retitled continuation of
#     Legion of Super-Heroes vol. 2, and the DC Database files it under the old
#     name. The cover title is what a reader sees, so that is what is shown.
#   * The DC Database drops the comma from "Infinity, Inc." in page titles.
SERIES = {
    "coie":    ("Crisis on Infinite Earths", "Crisis on Infinite Earths Vol 1"),
    "asq":     ("All-Star Squadron", "All-Star Squadron Vol 1"),
    "fof":     ("The Fury of Firestorm", "The Fury of Firestorm Vol 1"),
    "ii":      ("Infinity, Inc.", "Infinity Inc. Vol 1"),
    "iiann":   ("Infinity, Inc. Annual", "Infinity Inc. Annual Vol 1"),
    "bat":     ("Batman", "Batman Vol 1"),
    "det":     ("Detective Comics", "Detective Comics Vol 1"),
    "gl":      ("Green Lantern (vol. 2)", "Green Lantern Vol 2"),
    "jla":     ("Justice League of America", "Justice League of America Vol 1"),
    "jlaann":  ("Justice League of America Annual",
                "Justice League of America Annual Vol 1"),
    "vig":     ("Vigilante", "Vigilante Vol 1"),
    "losers":  ("The Losers Special", "Losers Special Vol 1"),
    "dcp":     ("DC Comics Presents", "DC Comics Presents Vol 1"),
    "st":      ("Swamp Thing (vol. 2)", "Swamp Thing Vol 2"),
    "legends": ("Legends of the DC Universe: Crisis on Infinite Earths",
                "Legends of the DC Universe: Crisis on Infinite Earths Vol 1"),
    "ww":      ("Wonder Woman", "Wonder Woman Vol 1"),
    "lsh":     ("Legion of Super-Heroes (vol. 3)", "Legion of Super-Heroes Vol 3"),
    "sup":     ("Superman", "Superman Vol 1"),
    "om":      ("The Omega Men", "Omega Men Vol 1"),
    "bd":      ("Blue Devil", "Blue Devil Vol 1"),
    "ntt2":    ("The New Teen Titans (vol. 2)", "New Teen Titans Vol 2"),
    "am":      ("Amethyst (vol. 2)", "Amethyst Vol 2"),
    # pre-Crisis cameos only
    "ntt1":    ("The New Teen Titans", "New Teen Titans Vol 1"),
    "nttann":  ("The New Teen Titans Annual", "New Teen Titans Annual Vol 1"),
    "flash":   ("The Flash", "The Flash Vol 1"),
    "tott":    ("Tales of the Teen Titans", "Tales of the Teen Titans Vol 1"),
    "bo":      ("Batman and the Outsiders", "Batman and the Outsiders Vol 1"),
    "ac":      ("Action Comics", "Action Comics Vol 1"),
    "tlsh":    ("Tales of the Legion of Super-Heroes", "Legion of Super-Heroes Vol 2"),
    "wf":      ("World's Finest Comics", "World's Finest Vol 1"),
    "gic":     ("G.I. Combat", "G.I. Combat Vol 1"),
    "warlord": ("Warlord", "Warlord Vol 1"),
    "jhex":    ("Jonah Hex", "Jonah Hex Vol 1"),
}

# How each source spells a series. Volume suffixes are stripped before lookup,
# so "Swamp Thing" and "Swamp Thing Vol. 2" both land on `st`.
ALIAS = {
    "crisis on infinite earths": "coie",
    "all-star squadron": "asq",
    "fury of firestorm": "fof",
    "the fury of firestorm": "fof",
    "infinity, inc.": "ii",
    "infinity inc.": "ii",
    "infinity, inc. annual": "iiann",
    "infinity inc. annual": "iiann",
    "batman": "bat",
    "detective comics": "det",
    "green lantern": "gl",
    "justice league of america": "jla",
    "justice league of america annual": "jlaann",
    "vigilante": "vig",
    "losers special": "losers",
    "the losers special": "losers",
    "dc comics presents": "dcp",
    "swamp thing": "st",
    "legends of the dcu: crisis on infinite earths": "legends",
    "legends of the dc universe: crisis on infinite earths": "legends",
    "wonder woman": "ww",
    "legion of super-heroes": "lsh",
    "superman": "sup",
    "omega men": "om",
    "the omega men": "om",
    "blue devil": "bd",
    "new teen titans": "ntt2",
    "the new teen titans": "ntt2",
    "new teen titans annual": "nttann",
    "amethyst": "am",
    "amethyst, princess of gem world": "am",
    "the flash": "flash",
    "flash": "flash",
    "tales of the teen titans": "tott",
    "batman and the outsiders": "bo",
    "action comics": "ac",
    "tales of the legion of super-heroes": "tlsh",
    "world's finest": "wf",
    "world's finest comics": "wf",
    "g.i. combat": "gic",
    "warlord": "warlord",
    "jonah hex": "jhex",
    "jla: incarnations": "incarnations",
}

# In the pre-Crisis block the unqualified names mean the older books: the
# Titans were still New Teen Titans vol. 1 in 1984, and Legion of Super-Heroes
# vol. 3 did not exist yet.
PRE_ALIAS = {"new teen titans": "ntt1", "the new teen titans": "ntt1"}

ISSUE = re.compile(r"^(?P<s>.+?)(?:\s+Vol\.?\s*(?P<v>\d+))?\s+#(?P<n>\d+)"
                   r"(?:\s+\((?P<y>\d{4})\))?$")


def key_of(name, pre=False):
    """Source spelling -> series key, or None if this source names something
    the table has never seen (which fails the fetch rather than shipping)."""
    n = re.sub(r"\s+\(?vol\.?\s*\d+\)?$", "", name.strip().lower())
    n = n.replace("’", "'").strip()
    if pre and n in PRE_ALIAS:
        return PRE_ALIAS[n]
    return ALIAS.get(n)


# ---------------------------------------------------------------- the order
# (key, issue). This is the list; everything below it is the checking.
#
# The event, from Comic Book Herald's issue-by-issue order, in five sections
# cut at the maxiseries issues. Section titles name the Crisis issues they
# cover rather than the chapter titles DC printed, which are spoilers.
ACT1 = [
    ("coie", 1), ("fof", 41), ("asq", 50), ("asq", 51), ("asq", 52), ("ii", 18),
    ("coie", 2), ("bat", 389), ("det", 556), ("bat", 390), ("det", 557),
    ("bat", 391), ("det", 558), ("gl", 194), ("ii", 19), ("jla", 244),
    ("ii", 20), ("vig", 22),
]
ACT2 = [
    ("coie", 3), ("losers", 1), ("dcp", 86), ("st", 44), ("st", 45),
    ("iiann", 1), ("ii", 21), ("coie", 4), ("coie", 5), ("legends", 1),
    ("st", 46), ("asq", 53), ("asq", 54), ("asq", 55), ("asq", 56), ("ii", 22),
]
ACT3 = [
    ("coie", 6), ("ii", 23), ("ww", 327), ("ww", 328), ("ww", 329),
    ("coie", 7), ("gl", 195), ("ii", 24), ("lsh", 16), ("lsh", 17), ("lsh", 18),
    ("dcp", 87), ("sup", 414), ("om", 31),
]
ACT4 = [
    ("coie", 8), ("bd", 17), ("bd", 18), ("dcp", 88), ("jlaann", 3),
    ("coie", 9), ("jla", 245), ("fof", 42), ("ntt2", 13), ("ntt2", 14),
]
ACT5 = [
    ("coie", 10), ("coie", 11), ("am", 13), ("gl", 196), ("gl", 197),
    ("coie", 12), ("gl", 198), ("sup", 415),
]

# The run of Monitor cameos, from comicbookreadingorders.com, which
# enumerates them and says in the same breath that they are unnecessary.
PRE = [
    ("ntt1", 21), ("nttann", 2), ("gl", 173), ("gl", 176), ("gl", 178),
    ("flash", 338), ("flash", 339), ("tott", 47), ("bd", 5), ("fof", 28),
    ("bo", 14), ("bo", 15), ("ac", 560), ("jla", 232), ("tlsh", 317),
    ("st", 30), ("ww", 321), ("ii", 8), ("asq", 40), ("dcp", 76), ("sup", 402),
    ("st", 31), ("jla", 234), ("vig", 14), ("sup", 403), ("wf", 311),
    ("tlsh", 319), ("tlsh", 320), ("am", 2), ("ww", 323), ("gic", 274),
    ("gic", 275), ("ac", 564), ("warlord", 91), ("jhex", 90), ("bat", 384),
    ("det", 551), ("flash", 350), ("tott", 58), ("dcp", 78),
]

# The only row on the list that no reading order places.
UNPLACED = {("bd", 17)}

# The three issues the two guides file under different maxiseries chapters.
# Anything else moving means a source has been rewritten and the notes that
# describe the disagreement have gone stale, so the build stops.
CROSSCHECK_MOVES = [("gl", 195), ("ww", 328), ("ww", 329)]

# Tier 1 tie-ins. Comic Book Herald calls the DC Comics Presents issues "easily
# some of the most interesting and relevant connected stories within Crisis"
# and #87 "the single most compelling tie-in comic". Nothing else in either
# guide gets a recommendation of its own, so nothing else is tier 1.
RECOMMENDED = {("dcp", 86), ("dcp", 87), ("dcp", 88)}

# Wikipedia lists two issues published long after the crossover alongside the
# banner issues. Only one of them is placed by a reading order; the other is
# named in the notes and left off.
LATER = {("legends", 1)}
NOT_CARRIED = {("incarnations", 5)}

STAR = {("coie", n): 2 for n in range(1, 13)}
STAR[("dcp", 87)] = 2
STAR[("dcp", 86)] = 1
STAR[("dcp", 88)] = 1

NOTE = {
    ("asq", 50): "Roy Thomas's 1940s team book. Comic Book Herald rates these "
                 "the most skippable issues of the crossover.",
    ("ii", 18): "Roy Thomas again, with early Todd McFarlane art.",
    ("bat", 389): "Six issues of Batman and Detective with no banner on the "
                  "covers — they reference the red skies and little else.",
    ("vig", 22): "comicbookreadingorders.com puts this five rows earlier, "
                 "straight after Detective #558.",
    ("losers", 1): "A one-shot that runs alongside issue #3.",
    ("dcp", 86): "Comic Book Herald rates the three DC Comics Presents issues "
                 "the most worthwhile tie-ins on the list.",
    ("st", 44): "Alan Moore, Bissette and Totleben, mid-run. Worth reading "
                "whether or not you came for the Crisis.",
    ("legends", 1): "Written by Wolfman and published in 1998, filling in a "
                    "gap. One guide warns it gives part of issue #5 away; "
                    "both put it after.",
    ("ww", 327): "comicbookreadingorders.com places #328–329 much earlier, "
                 "between issues #3 and #4, and leaves #327 out.",
    ("gl", 195): "comicbookreadingorders.com reads this one chapter earlier, "
                 "after #6.",
    ("lsh", 16): "No banner on #16 or #17; the guides carry them so the "
                 "three-parter reads whole.",
    ("dcp", 87): "Comic Book Herald's pick for the single best tie-in here.",
    ("bd", 17): "Carries the banner, but neither reading order places it, so "
                "it sits with #18.",
    ("gl", 196): "No banner on #196 or #197 — the run reaches the banner "
                 "issue at #198.",
}

PRE_NOTE = {
    ("ntt1", 21): "The first of them.",
    ("flash", 350): "Issue #2 of the maxiseries refers back to this one.",
    ("dcp", 78): "The last of the cameos, and the one DC picked up when it "
                 "collected the crossover.",
}


# ---------------------------------------------------------------- fetching
def get(url):
    f = CACHE / "web" / (re.sub(r"[^A-Za-z0-9]+", "-", url)[:120] + ".html")
    if f.exists():
        return f.read_text(encoding="utf-8", errors="replace")
    f.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-GB,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read().decode("utf-8", "replace")
    f.write_text(body, encoding="utf-8")
    time.sleep(1.0)
    return body


def text(s):
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s).replace("’", "'")
    return re.sub(r"\s+", " ", s).strip()


def pairs(lines, pre=False, where=""):
    out = []
    for v in lines:
        m = ISSUE.match(v)
        if not m:
            continue
        k = key_of(m.group("s"), pre)
        assert k, "%s names a series this generator does not know: %r" % (where, v)
        out.append([k, int(m.group("n"))])
    return out


def fetch_cbh():
    t = get(CBH_URL)
    i = t.find("Issue by Issue Reading Order")
    j = t.find("Heroically Support", i)
    assert i > 0 and j > i, "Comic Book Herald's reading-order heading moved"
    rows = [text(m.group(2))
            for m in re.finditer(r"(?is)<p([^>]*)>(.*?)</p>", t[i:j])
            if "padding-left" not in m.group(1)]
    return pairs(rows, where="Comic Book Herald")


def fetch_cbro():
    t = get(CBRO_URL)
    i = t.find("Pre-Crisis Monitor Appearances")
    j = t.find("x-accordion-inner", i)
    k = t.find("</div>", j)
    assert 0 < i < j < k, "comicbookreadingorders.com's cameo accordion moved"
    chunks = re.split(r"(?i)<p[^>]*>|<br\s*/?>", t[j:k])
    pre = pairs([text(c).split(">")[-1] for c in chunks], pre=True,
                where="comicbookreadingorders.com (cameos)")

    a = t.find("Unless you have been reading", k)
    b = t.find("</p>", t.find("Superman #415", a))
    assert 0 < a < b, "comicbookreadingorders.com's reading order moved"
    rows = [text(c) for c in re.split(r"(?i)<p[^>]*>|<br\s*/?>", t[a:b])
            if "#0000ff" not in c]
    return pre, pairs(rows, where="comicbookreadingorders.com")


def fetch_banner_wikipedia():
    """The `Special Crisis Cross-Over` bullet list in the Tie-ins section."""
    t = wiki.wikitext("Crisis on Infinite Earths", cache_dir=str(CACHE))
    m = re.search(r"\{\{Div col\}\}(.*?)\{\{div col end\}\}", t, re.S | re.I)
    assert m, "Wikipedia's tie-in bullet list moved"
    out = []
    for line in m.group(1).splitlines():
        if not line.strip().startswith("*"):
            continue
        v = wiki.clean(line.lstrip("* ").strip())
        v = re.sub(r"\s*\(released in \d{4}\)", "", v)
        # `Series (vol. 2) #194–195; #198` and `Series #18–24; Annual #1`
        head = re.split(r"#", v)[0]
        base = key_of(head)
        assert base, "Wikipedia's list names an unknown series: %r" % v
        cur = base
        for part in v.split(";"):
            part = part.strip()
            if re.match(r"(?i)^annual\b", part):
                cur = base + "ann"
                assert cur in SERIES, "no annual series for %r" % v
            for a, b in re.findall(r"#(\d+)(?:\s*[-–]\s*(\d+))?", part):
                for n in range(int(a), int(b or a) + 1):
                    out.append([cur, n])
    return out


def fetch_banner_dcdb():
    """The `Crossovers` bullet list on the DC Database's event page."""
    q = urllib.parse.urlencode({"action": "parse", "page": "Crisis on Infinite Earths",
                                "prop": "wikitext", "format": "json",
                                "formatversion": "2", "redirects": "1"})
    req = urllib.request.Request("https://%s/api.php?%s" % (DCDB, q),
                                 headers={"User-Agent": UA})
    t = json.loads(urllib.request.urlopen(req, timeout=60).read()
                   .decode("utf-8"))["parse"]["wikitext"]
    (CACHE / "wiki").mkdir(parents=True, exist_ok=True)
    (CACHE / "wiki" / "dc-Crisis-on-Infinite-Earths.wiki").write_text(
        t, encoding="utf-8")
    m = re.search(r"'''Crossovers''':(.*?)(?:\n\s*\n|\| Wikipedia)", t, re.S)
    assert m, "the DC Database's Crossovers list moved"
    out = []
    for raw in re.findall(r"\{\{c\|([^}]+)\}\}", m.group(1)):
        raw = raw.strip()
        mm = re.match(r"^(?P<s>.+?)(?:\s+Vol\s+(?P<v>\d+))?\s+#?(?P<n>\d+)$", raw)
        assert mm, "cannot read a DC Database crossover entry: %r" % raw
        k = key_of(mm.group("s"))
        assert k, "the DC Database names an unknown series: %r" % raw
        out.append([k, int(mm.group("n"))])
    return out


def verify_pages(rows):
    """Every row must resolve to a real issue page on the DC Database. This is
    the check that makes an invented issue number impossible to ship."""
    titles = ["%s %d" % (SERIES[k][1], n) for k, n in rows]
    live = {}
    for i in range(0, len(titles), 40):
        chunk = titles[i:i + 40]
        q = urllib.parse.urlencode({"action": "query", "titles": "|".join(chunk),
                                    "format": "json", "formatversion": "2",
                                    "redirects": "1"})
        req = urllib.request.Request("https://%s/api.php?%s" % (DCDB, q),
                                     headers={"User-Agent": UA})
        d = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8"))
        norm = {r["from"]: r["to"] for r in
                d["query"].get("normalized", []) + d["query"].get("redirects", [])}
        real = {p["title"]: ("missing" not in p) for p in d["query"]["pages"]}
        for t in chunk:
            seen, cur = 0, t
            while cur in norm and seen < 4:
                cur, seen = norm[cur], seen + 1
            live[t] = real.get(cur, False)
        time.sleep(0.4)
    missing = sorted(t for t, ok in live.items() if not ok)
    assert not missing, "no DC Database page for: %s" % missing[:6]
    return live


def fetch():
    order_cbh = fetch_cbh()
    pre_cbro, order_cbro = fetch_cbro()
    data = {
        "fetched": time.strftime("%Y-%m-%d"),
        "sources": {
            "order": CBH_URL,
            "order_crosscheck": CBRO_URL,
            "banner_wikipedia": "https://en.wikipedia.org/wiki/Crisis_on_Infinite_Earths",
            "banner_dc_database": "https://dc.fandom.com/wiki/Crisis_on_Infinite_Earths",
        },
        "order_cbh": order_cbh,
        "order_cbro": order_cbro,
        "pre_cbro": pre_cbro,
        "banner_wikipedia": fetch_banner_wikipedia(),
        "banner_dcdb": fetch_banner_dcdb(),
    }
    rows = [tuple(x) for x in ACT1 + ACT2 + ACT3 + ACT4 + ACT5 + PRE]
    data["dc_pages"] = verify_pages(sorted(set(rows)))
    with DATA.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print("wrote %s" % DATA.relative_to(HERE.parent))
    for k in ("order_cbh", "order_cbro", "pre_cbro", "banner_wikipedia",
              "banner_dcdb", "dc_pages"):
        print("  %-18s %d" % (k, len(data[k])))


# ---------------------------------------------------------------- checking
def check(src):
    """Everything this list claims about its sources, asserted."""
    event = [tuple(x) for x in ACT1 + ACT2 + ACT3 + ACT4 + ACT5]
    pre = [tuple(x) for x in PRE]
    tup = lambda rows: [tuple(x) for x in rows]

    # 1. the spine is Comic Book Herald's order, in order, complete.
    assert [r for r in event if r not in UNPLACED] == tup(src["order_cbh"]), \
        "the event order no longer matches Comic Book Herald"

    # 2. the cross-check agrees on every issue it lists, and adds none. It
    #    disagrees on where three of them sit, and the rows say which.
    cbro = tup(src["order_cbro"])
    extra = [r for r in cbro if r not in event]
    assert not extra, \
        "comicbookreadingorders.com lists issues this order omits: %s" % extra
    #    Comparing them row by row would report every reshuffle inside a
    #    chapter as a disagreement, which is noise: what a reader needs is
    #    which maxiseries issue a tie-in reads after. So compare that.
    def chapters(rows):
        out, cur = {}, 0
        for k, n in rows:
            if k == "coie":
                cur = n
            else:
                out[(k, n)] = cur
        return out

    a, b = chapters(tup(src["order_cbh"])), chapters(cbro)
    moved = sorted(r for r in set(a) & set(b) if a[r] != b[r])
    assert moved == sorted(CROSSCHECK_MOVES), \
        "the two orders now disagree about different issues: %s" % moved

    # 3. the cameo block is comicbookreadingorders.com's, unedited.
    assert pre == tup(src["pre_cbro"]), \
        "the pre-Crisis block no longer matches comicbookreadingorders.com"

    # 4. the two banner enumerations are the same set. If they ever diverge,
    #    "whose list is it" stops having an answer and this build stops.
    wp, dc = set(tup(src["banner_wikipedia"])), set(tup(src["banner_dcdb"]))
    assert wp - dc == LATER | NOT_CARRIED, \
        "Wikipedia and the DC Database disagree about the banner: %s" % sorted(wp - dc)
    assert not dc - wp, \
        "the DC Database banners issues Wikipedia does not: %s" % sorted(dc - wp)
    banner = dc

    # 5. the maxiseries is complete and in order.
    spine = [n for k, n in event if k == "coie"]
    assert spine == list(range(1, 13)), spine

    # 6. every row resolves to a real issue page on the DC Database.
    for k, n in event + pre:
        t = "%s %d" % (SERIES[k][1], n)
        assert src["dc_pages"].get(t), "unverified issue: %s" % t

    # 7. nothing is on the list twice.
    assert len(set(event + pre)) == len(event + pre), "a row is repeated"

    # 8. every banner issue a reading order places is on the list.
    placed = set(tup(src["order_cbh"])) | set(cbro)
    for r in sorted(banner & placed):
        assert r in set(event), "banner issue dropped: %s" % (r,)
    return banner


def tier_of(row, banner):
    if row[0] == "coie":
        return 1
    if row in RECOMMENDED:
        return 1
    if row in banner or row in LATER:
        return 2
    return 3


# ---------------------------------------------------------------- the build
def item(row, banner, pre=False):
    k, n = row
    t, _ = SERIES[k]
    x = {
        "id": "coie-%s%s-%d" % ("pre-" if pre else "", k, n),
        "t": t,
        "n": "#%d" % n,
        "note": NOTE.get(row, "") if not pre else PRE_NOTE.get(row, ""),
        "star": STAR.get(row, 0) if not pre else 0,
        "tier": 3 if pre else tier_of(row, banner),
    }
    return x


SECTIONS = [
    ("pre", 3, "Before the Crisis",
     "the Monitor cameos · skip these and start at #1",
     "In January 1983 DC told its editors and writers to put a character "
     "called the Monitor in their books twice in the coming year, and not to "
     "show him. These are those appearances — usually a panel, a man at a "
     "screen, no explanation. comicbookreadingorders.com lists all forty and "
     "says plainly that they are unnecessary; they are here so a completist "
     "does not have to go looking, and they are tier 3 for the same reason.",
     PRE),
    ("act1", 1, "Crisis #1–2",
     "the crossover starts thin",
     "The twelve issues of the maxiseries are a complete story on their own, "
     "and tier 1 is that story. Everything between the numbered issues is a "
     "tie-in. Comic Book Herald's warning about this early stretch is worth "
     "repeating: most of these amount to a red sky and a stranger turning up "
     "to recruit somebody.",
     ACT1),
    ("act2", 1, "Crisis #3–5",
     "the tie-ins stop being weather",
     "", ACT2),
    ("act3", 1, "Crisis #6–7",
     "Legion, Superman and the Omega Men join in",
     "", ACT3),
    ("act4", 1, "Crisis #8–9",
     "Blue Devil through to the Titans",
     "", ACT4),
    ("act5", 1, "Crisis #10–12",
     "the end, and the two issues that follow it",
     "Two banner issues come after the last chapter, and both guides "
     "put them there.", ACT5),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true",
                    help="re-read the sources into tools/data/crisis.json")
    args = ap.parse_args()
    if args.fetch:
        fetch()

    src = json.loads(DATA.read_text(encoding="utf-8"))
    banner = check(src)

    sections = []
    for sid, tier, title, sub, intro, rows in SECTIONS:
        sec = {"id": sid, "title": title, "sub": sub, "tier": tier,
               "intro": intro,
               "items": [item(tuple(r), banner, pre=(sid == "pre"))
                         for r in rows]}
        sections.append(sec)

    counts = {1: 0, 2: 0, 3: 0}
    for s in sections:
        for x in s["items"]:
            counts[x["tier"]] += 1
    total = sum(counts.values())
    assert counts[1] == 15, counts
    series = len({x["t"] for s in sections for x in s["items"]})

    p = {
        "slug": SLUG,
        "title": "Crisis on Infinite Earths",
        "subtitle": "the 1985 maxiseries and its crossover — the end of "
                    "pre-Crisis DC",
        "kind": "comics",
        "popularity": 55,
        "year": "1985–86",
        "blurb": "%d issues across %d series, interleaved in the order they're "
                 "meant to be read — %d of them if you only want the story."
                 % (total, series, counts[1]),
        "unit": {"one": "issue", "many": "issues"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": "#4B3FA6",
        "accentDark": "#9B8CF0",
        "tiers": True,
        "itemTiers": True,
        "paceTiers": [1, 2],
        "paceLabel": "the pre-Crisis cameos",
        "notes": [
            ["Tiers are on each row, not each section.",
             "1 is the twelve-issue maxiseries plus the three DC Comics "
             "Presents issues, and it is a complete story — the minimum viable "
             "path is Tier 1 alone. 2 is the rest of the crossover DC put a "
             "banner on. 3 is the issues the guides carry that never had the "
             "banner, and the cameos that came before any of it."],
            ["Whose tie-in list this is.",
             "There is no agreed one, so this uses the only undisputed fact: "
             "DC printed a \"Special Crisis Cross-Over\" banner on a specific "
             "set of covers. Wikipedia and the DC Database enumerate that set "
             "separately, and the generator refuses to build if the two ever "
             "stop agreeing. Two issues published much later — Legends of the "
             "DC Universe: Crisis on Infinite Earths #1 (1998) and JLA: "
             "Incarnations #5 (2001) — get put on the same list; the first is "
             "placed by both reading orders and is here, the second is placed "
             "by neither and is not."],
            ["This is the boundary.",
             "Everything before it is pre-Crisis DC — a multiverse with a "
             "separate Earth for the 1940s heroes, another for the Marvel "
             "Family, another for the Charlton ones. Everything after it is "
             "one continuity, and the reboots that followed (Man of Steel, "
             "Year One, Pérez's Wonder Woman) start from here. Infinite Crisis "
             "and Final Crisis are different events twenty and twenty-three "
             "years later, and are not on this list."],
            ["No reading times.",
             "Comics do not publish a per-issue reading time and this list "
             "does not invent one. A row is one issue; the bar counts issues."],
            ["What is referenced but not here.",
             "Comic Book Herald notes that issue #2 leans on Flash #350 (which "
             "is in the cameo block), issue #4 on Omega Men #26 and issue #6 "
             "on Superman #413. Neither guide puts those last two in the "
             "order, so neither does this."],
            "Order from Comic Book Herald's issue-by-issue reading order, "
            "cross-checked against comicbookreadingorders.com, which supplies "
            "the pre-Crisis Monitor cameos. The crossover banner list is "
            "Wikipedia's and the DC Database's, which agree; every issue on "
            "the list is checked against its DC Database page before the file "
            "is written.",
        ],
        "sections": sections,
    }

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

    out = gwprop.write(p)
    print("wrote %s" % out.name)
    print("  %d rows, %d sections, %d series" % (total, len(sections), series))
    print("  T1 %d (the readable path)   T2 %d (the banner crossover)   "
          "T3 %d (completist)" % (counts[1], counts[2], counts[3]))


if __name__ == "__main__":
    main()
