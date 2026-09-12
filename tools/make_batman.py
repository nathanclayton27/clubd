#!/usr/bin/env python3
"""Generate properties/batman.json — Batman as a character reading list.

    PYTHONIOENCODING=utf-8 python tools/make_batman.py

WHAT THIS IS, AND WHAT IT REPLACED. This file used to emit a list of collected
*stories* — Year One as one row, Knightfall as one row — gated on whether
Wikipedia's publication history of Batman stopped to name each one. The
umbrella ruling of 2026-09-11 settled the shape of every comics list in this
catalogue: **rows are issues, not collected volumes.** So the list is rebuilt
here as twelve runs in publication order, one section per run, one row per
issue, and the old story ids are gone with the story rows. Two ids survive
because their rows survive unchanged — a one-shot and a graphic novel are one
comic either way — and they are passed as `legacy_ids` so the build refuses to
lose them.

A CHARACTER READING LIST IS NOT A PUBLICATION HISTORY. Batman has been
published monthly since 1940 in at least two titles at once; the complete
thing is thousands of issues and unfinishable. This is the other thing: the
sequence somebody should actually read, picked here, in the voice
properties/indie-essentials.json uses — a house pick, veto freely. Where a
famous run is left out, the notes say so by name.

THE NINETIES ARE DELIBERATELY ABSENT. Knightfall, Prodigal, Contagion,
Legacy, Cataclysm and No Man's Land are one long contiguous crossover read
across every Bat-book, and they are a list of their own rather than six
sections here. This list therefore steps from Arkham Asylum (1989) to The
Long Halloween (1996) — a self-contained miniseries that happens to sit in
that decade — and then to Hush (2002). Nothing in this file overlaps that
read.

WHERE EVERY NUMBER COMES FROM, AND WHY NONE IS TYPED FROM MEMORY.
Two Wikipedia articles, cached, and one article per run:

  * `List of Batman comics` — its collected-editions tables cite exact issue
    ranges (`''Batman'' (vol. 2) #35-40`). Those are parsed into a set of
    (series, volume, issue) triples and NO ROW IS EMITTED THAT IS NOT IN THAT
    SET. The volume is taken from the citation where it says one, and
    otherwise from which continuity block the table sits in — which is what
    keeps Batman vol. 1 #1, vol. 2 #1 and vol. 3 #1 apart. Its one-shots and
    graphic novels table attests the two rows that have no issue number.
  * `Batman (comic book)` — its publication history is asserted verbatim for
    every boundary claim this file makes: where Morrison started and stopped,
    that Snyder and Capullo ended at #51 and not #52, that King ended at #85,
    that #64-65 are somebody else's Flash crossover, when #0 was published.
    The creator names in the first-issue notes of those two runs are read out
    of that prose with a regex rather than written down.
  * one article per run — `Batman: Hush`, `Batman: The Black Mirror` and the
    rest. Their infoboxes carry the run's months and years and its writer and
    artist, and where the infobox also carries a `titles` field its issue
    range is cross-checked against the collected editions. Both sources have
    to agree or the build stops.

The parsed result is written to tools/data/batman-issues.json so the numbers
this file shipped are readable without re-running it.

FIVE THINGS ARE LEFT OUT RATHER THAN GUESSED AT.
  * Batman (vol. 3) #64-65 — the article says they are a Flash crossover
    written by Joshua Williamson, and the run's own collected volumes skip
    them.
  * Batman #659-662 and #670-671 — not Morrison's; #670-671 are collected
    with The Resurrection of Ra's al Ghul.
  * Batman (vol. 2) #23.1-23.4 — four Villains Month one-shots, each about a
    villain, not chapters of the run.
  * Batman (vol. 2) #52 — Snyder and Capullo's run ends at #51; #52 closes
    the volume under other hands.
  * The Killing Joke's month. Its own article says March 1988 and the
    bibliography's sort key says December 1988, so the row carries the year
    both agree on and no month.

UNWEIGHTED, like every comics list here: comics publish no per-issue reading
time, so no row carries `w` and there is no `weightUnit`.
"""
import json
import pathlib
import re
import sys
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop as P  # noqa: E402
from gwlib import wiki as W  # noqa: E402

SLUG = "batman"
CACHE = P.ROOT / "scratch" / "agent-batman"
DATA = pathlib.Path(__file__).resolve().parent / "data" / "batman-issues.json"

LIST = "List of Batman comics"
BOOK = "Batman (comic book)"

# The ids of rows that existed on the story-shaped version of this list and
# still exist here, unchanged, because a one-shot and a graphic novel are one
# comic under either shape. prop.write refuses the file if either is lost.
LEGACY = ("bat-killing-joke", "bat-arkham")


# ------------------------------------------------------------- the plumbing --

DASHES = {"–": "-", "—": "-", "‒": "-", "−": "-"}


def flat(t):
    for a, b in DASHES.items():
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t)


def page(name):
    t = W.wikitext(name, cache_dir=str(CACHE))
    assert t, "no Wikipedia article: %r" % name
    assert not re.match(r"\s*#REDIRECT", t, re.I), "%r is a redirect" % name
    return t


def url(name):
    return "https://en.wikipedia.org/wiki/" + urllib.parse.quote(
        name.replace(" ", "_"), safe="_(),:!'-")


def unlink(t):
    """[[a|b]] -> b, [[a]] -> a. Every title in these tables is linked."""
    t = re.sub(r"\[\[[^\]|]*\|([^\]]+)\]\]", r"\1", t)
    return re.sub(r"\[\[([^\]]+)\]\]", r"\1", t)


def normkey(t):
    t = t.lower().replace("&", "and").replace("'", "").replace("’", "")
    return re.sub(r"\s+", " ", t.replace(".", "").strip())


# Only these two books restarted their numbering, so only these two need the
# volume disambiguated. Anything else cited without a volume is itself.
VOLUMED = {"batman", "detective comics"}

_CITE = re.compile(r"''(.+?)''\s*(?:\(?\bvol\.?\s*(\d+)\)?)?\s*#\s*", re.I)
_TOKEN = re.compile(r"(\d+(?:\.\d+)?)(?:\s*[-‐-―]\s*(\d+))?")
_SEP = re.compile(r"\s*(?:,|and)\s*")

REJECTED = []


def citations(text, default_vol=None):
    """(series, vol) -> {issue} for every `''Title'' (vol. N) #range` in text.

    The token loop stops at the first thing that is not an issue number, which
    is what keeps a trailing publication year, an ISBN and a following
    `Annual #25` out of the series' own set. A range wider than 200 is a typo
    in the source rather than a run — the bibliography really does carry
    `Detective Comics #568-5789` — and is recorded and dropped.
    """
    out = {}
    text = unlink(text)
    for m in _CITE.finditer(text):
        name = normkey(m.group(1))
        vol = int(m.group(2)) if m.group(2) else (
            default_vol if name in VOLUMED else None)
        got = out.setdefault((name, vol), set())
        pos = m.end()
        while True:
            tm = _TOKEN.match(text, pos)
            if not tm:
                break
            a, b = tm.group(1), tm.group(2)
            if b is not None and "." not in a:
                lo, hi = int(a), int(b)
                if hi < lo:            # Zero Hour counts down: #4-0
                    lo, hi = hi, lo
                if hi > lo + 200:
                    REJECTED.append("%s #%s-%s" % (name, a, b))
                    break
                got.update(str(n) for n in range(lo, hi + 1))
            else:
                got.add(a)
            pos = tm.end()
            sm = _SEP.match(text, pos)
            if not sm:
                break
            pos = sm.end()
    return out


def block(text, heading_rx):
    """One `== heading ==` section, up to the next heading of the same level."""
    m = re.search(heading_rx, text, re.M)
    assert m, "heading not found: %s" % heading_rx
    lvl = len(re.match(r"=+", m.group(0).strip()).group(0))
    nxt = re.compile(r"^={1,%d}[^=].*?={1,%d}\s*$" % (lvl, lvl), re.M)
    n = nxt.search(text, m.end())
    return text[m.end():n.start() if n else len(text)]


def rows_of(seg):
    """(title cell, material cell) for every data row of every table in seg."""
    out = []
    for row in seg.split("\n|-"):
        lines = [l.strip() for l in row.strip().split("\n") if l.strip()]
        cells = [l for l in lines
                 if l.startswith("|") and not l.startswith("|}")
                 and "-align" not in l.split("|")[1][:40]]
        if len(cells) < 2:
            continue
        def cell(s):
            s = s[1:]
            if re.match(r"\s*[^|\[{]*=[^|\[{]*\|", s):
                s = s.split("|", 1)[1]
            return s.strip()
        out.append((cell(cells[0]), cell(cells[1])))
    return out


# ------------------------------------------------------------- the attesting --
# Which collected-editions block carries which continuity, and therefore which
# volume an unqualified `''Batman'' #N` means inside it.

BLOCKS = [
    (r"^===\s*Modern Batman\s*===\s*$", 1),
    (r"^===\s*''\[\[The New 52\]\]'' Batman\s*===\s*$", 2),
    (r"^===\s*''\[\[DC Rebirth\]\]'' Batman\s*===\s*$", 3),
    (r"^===\s*''\[\[Infinite Frontier\]\] Batman''\s*===\s*$", 3),
    (r"^===\s*''\[\[DC Omnibus\]\]''es.*$", None),
    (r"^===\s*Writer/artist collections\s*===\s*$", None),
]

ATTEST = {}
COLLECTIONS = []        # (collection title, {(series, vol): {issues}})
ONESHOT_BLOCK = ""


def read_sources():
    global ONESHOT_BLOCK
    listing = page(LIST)
    for rx, vol in BLOCKS:
        seg = block(listing, rx)
        for k, v in citations(seg, default_vol=vol).items():
            ATTEST.setdefault(k, set()).update(v)
        for title, material in rows_of(seg):
            COLLECTIONS.append((W.clean(title), citations(material, vol)))
    assert len(ATTEST) > 200, "the collected-editions tables did not parse"
    ONESHOT_BLOCK = block(listing, r"^==\s*One-shots and graphic novels\s*==\s*$")
    return listing


# display title, citation name, volume, id token
SERIES = {
    "b1":  ("Batman", "batman", 1, "b1"),
    "b2":  ("Batman (vol. 2)", "batman", 2, "b2"),
    "b3":  ("Batman (vol. 3)", "batman", 3, "b3"),
    "dc":  ("Detective Comics", "detective comics", 1, "dc"),
    "ann": ("Batman Annual", "annual", None, "ann1"),
    "dkr": ("The Dark Knight Returns", "batman: the dark knight returns", None, "dkr"),
    "lh":  ("The Long Halloween", "batman: the long halloween", None, "lh"),
}

MISSING = []


def rows(skey, nums, notes=None):
    """One row per issue, each checked against the parsed collected editions."""
    disp, cite, vol, tok = SERIES[skey]
    notes = notes or {}
    out = []
    for n in nums:
        n = str(n)
        if n not in ATTEST.get((cite, vol), ()):
            MISSING.append("%s%s #%s" % (cite, " vol %s" % vol if vol else "", n))
        row = {"id": "bat-%s-%s" % (tok, n.replace(".", "-")),
               "t": disp, "n": "#%s" % n}
        if notes.get(n):
            row["note"] = notes[n]
        out.append(row)
    return out


def oneshot_row(article):
    """The bibliography's one-shots-and-graphic-novels row for one article."""
    for row in ONESHOT_BLOCK.split("\n|-"):
        if ("[[%s]]" % article) in row or ("[[%s|" % article) in row:
            return row
    raise AssertionError("%r is not in the one-shots table" % article)


def oneshot(article, display, row_id, note, year):
    """A single comic with no issue number. Attested twice: the bibliography
    lists it among the one-shots and graphic novels, and its cover date there
    carries the same year the article's own infobox does."""
    row = oneshot_row(article)
    assert year in row, "%r is not dated %s in the bibliography" % (article, year)
    return [{"id": row_id, "t": display, "n": "", "note": note}]


def rng(a, b):
    return [str(n) for n in range(a, b + 1)]


# ------------------------------------------------------------------ the runs --

ARTICLE = {
    "dkr":        "The Dark Knight Returns",
    "yearone":    "Batman: Year One",
    "killingjoke": "Batman: The Killing Joke",
    "family":     "A Death in the Family (comics)",
    "arkham":     "Arkham Asylum: A Serious House on Serious Earth",
    "halloween":  "Batman: The Long Halloween",
    "hush":       "Batman: Hush",
    "underhood":  "Batman: Under the Hood",
    "morrison":   "Batman and Son",
    "rip":        "Batman R.I.P.",
    "blackmirror": "Batman: The Black Mirror",
}

FACTS = {}          # section key -> {span, years, writers, artists, titles}

YEAR = re.compile(r"\b(?:1[89]|20)\d\d\b")


def dash(s):
    """One en dash between date parts, whatever the source used."""
    return re.sub(r"\s*[-‐-―]\s*", "–", s).strip()


def datespan(get):
    """The run's months and years, out of whichever infobox fields carry them."""
    d = get("date")
    if d:
        return dash(d)
    smo, syr = get("startmo"), get("startyr")
    emo, eyr = get("endmo"), get("endyr")
    assert syr, "no start year"
    if not eyr or eyr == syr:
        if smo and emo and smo != emo:
            return "%s–%s %s" % (smo, emo, syr)
        return ("%s %s" % (smo, syr)).strip()
    return "%s–%s" % (("%s %s" % (smo, syr)).strip(),
                      ("%s %s" % (emo, eyr)).strip())


def read_runs():
    for key, name in ARTICLE.items():
        ib = W.infobox(page(name),
                       kind=r"comic book title|comics story arc|graphic novel")
        assert ib, "no comics infobox on %r" % name
        get = lambda f: W.clean(ib(f))
        span = datespan(get)
        assert span, "no date on %r" % name
        years = YEAR.findall(span)
        assert years, "no year in %r for %r" % (span, name)
        FACTS[key] = {
            "span": span,
            "years": years,
            "writers": get("writers"),
            "artists": get("artists") or get("pencillers"),
            "titles": flat(unlink(ib("titles") or "")),
            "issues": get("issues"),
            # raw, not cleaned: clean() renders [[Dick Grayson|Batman]] as its
            # label and the name behind the cowl is the half that matters here
            "cast": ib("main_char_team") or "",
        }


def cross_check(key, skey, nums):
    """The run's own article and the bibliography have to name the same issues."""
    disp, cite, vol, _ = SERIES[skey]
    said = FACTS[key]["titles"]
    if not said:
        return
    got = citations(said, default_vol=vol).get((cite, vol))
    if not got:
        return
    want = set(str(n) for n in nums)
    assert got == want, (
        "%r says %s for %s but this file carries %s"
        % (ARTICLE[key], sorted(got, key=int), disp, sorted(want, key=int)))


def by(key):
    """`Writer with Artist`, straight out of the run's infobox. One name where
    the writer drew it too — Miller on The Dark Knight Returns."""
    f = FACTS[key]
    first = lambda s: re.split(r",| and ", s)[0].strip()
    w, a = first(f["writers"]), first(f["artists"])
    assert w, "no writer on %r" % ARTICLE[key]
    return w if not a or a == w else "%s with %s" % (w, a)


# Arc boundaries inside the two long runs are not typed either: each collected
# volume's own contents cell says which issue it opens on, and the note goes
# there. The label is what the volume is called after its `Vol. N:` prefix.
def collection(needle, skey):
    """The issues of one series that one named collected edition contains."""
    disp, cite, vol, _ = SERIES[skey]
    hit = ([c for c in COLLECTIONS if c[0] == needle]
           or [c for c in COLLECTIONS if needle in c[0]])
    assert len(hit) == 1, "%r matches %d collected volumes" % (needle, len(hit))
    issues = hit[0][1].get((cite, vol))
    assert issues, "%r cites no %s issues" % (needle, disp)
    return issues


def arc_notes(skey, labels):
    out = {}
    for needle, label in labels:
        first = str(min(int(i) for i in collection(needle, skey)))
        assert first not in out, "two arcs both open at #%s" % first
        out[first] = "“%s” begins" % label
    return out


SNYDER_ARCS = [("Batman Vol. 1: The Court of Owls", "The Court of Owls"),
               ("Batman Vol. 2: The City of Owls", "The City of Owls"),
               ("Batman Vol. 3: Death of the Family", "Death of the Family"),
               ("Batman Vol. 4: Zero Year", "Zero Year"),
               ("Batman Vol. 7: Endgame", "Endgame"),
               ("Batman Vol. 8: Superheavy", "Superheavy"),
               ("Batman Vol. 9: Bloom", "Bloom")]

KING_ARCS = [("Batman Vol. 1: I Am Gotham", "I Am Gotham"),
             ("Batman: Night of the Monster Men", "Night of the Monster Men"),
             ("Batman Vol. 2: I Am Suicide", "I Am Suicide"),
             ("Batman Vol. 3: I Am Bane", "I Am Bane"),
             ("Batman/The Flash: The Button", "The Button"),
             ("Batman Vol. 4: The War of Jokes and Riddles",
              "The War of Jokes and Riddles"),
             ("Batman Vol. 5: The Rules of Engagement", "The Rules of Engagement"),
             ("Batman Vol. 6: Bride or Burglar?", "Bride or Burglar?"),
             ("Batman Vol. 7: The Wedding", "The Wedding"),
             ("Batman Vol. 8: Cold Days", "Cold Days"),
             ("Batman Vol. 9: The Tyrant Wing", "The Tyrant Wing"),
             ("Batman Vol. 10: Knightmares", "Knightmares"),
             ("Batman Vol. 11: The Fall and the Fallen", "The Fall and the Fallen"),
             ("Batman Vol. 12: City of Bane Part 1", "City of Bane")]


# Everything this file claims about the two runs with no arc article of their
# own, asserted against `Batman (comic book)` before any of it is used.
PROSE = [
    "Grant Morrison began their long-form Batman narrative in issue #655.",
    "Morrison's final two issues were tie-ins to the event miniseries Final Crisis",
    "Grant Morrison temporarily returned to the Batman title for issues #700-702",
    "the second volume of Batman began publication on September 21, 2011",
    "The second volume of Batman was almost in its entirety written by "
    "Scott Snyder and pencilled by Greg Capullo",
    'Issue #0 was published in September 2012 as part of DC\'s line-wide '
    '"Zero Month" event',
    "four issues numbered #23.1-23.4 were published weekly",
    "issue #28 was thus illustrated by Dustin Nguyen",
    "Snyder and Capullo's run on the series concluded with issue #51",
    "The second volume of Batman concluded with issue #52",
    "the third volume of Batman began publication two weeks later on June 15, 2016",
    "initially written by Tom King and illustrated by David Finch",
    "The series crossed over with The Flash again in issues #64-65, both "
    "written by Joshua Williamson",
    "Tom King's run ended with issue #85 at the end of 2019",
    "beginning with a backup feature in issue #85",
    "The milestone issue #700",
    'titled "R.I.P.: The Missing Chapter"',
    "initially planned as a long-form story lasting 100 issues",
]

# Claims the section intros make about one run, asserted against that run's own
# article. The Long Halloween one is here because "set in the year after Year
# One" was written first and the article does not say it — it says the story
# sits in Year One's continuity, which is a weaker and true thing.
RUN_PROSE = [
    ("halloween", "a story set in the Year One continuity"),
]

# The continuity note says Rebirth is a relaunch and not a reboot, which is the
# opposite of what "three continuities" would have said. The bibliography is
# where that comes from, so it is asserted rather than remembered.
LIST_PROSE = [
    "In 2011, DC Comics rebooted their entire continuity",
    "DC Rebirth intended to restore the DC Universe to a form much like that "
    "prior to the Flashpoint story arc, while still incorporating numerous "
    "elements of The New 52, including its continuity",
]

# A personal name, and the full stop matters: `[\w.]` let "pencilled by Greg
# Capullo. The first story arc" capture "Greg Capullo. The", which shipped into
# a row note. An initial is allowed only mid-name, never as the last token.
NAME = r"(?:[A-Z][\w'’-]+ |[A-Z]\. )*[A-Z][\w'’-]+"
PAIR = re.compile(r"written by (%s) and pencilled by (%s)" % (NAME, NAME))
KING_PAIR = re.compile(r"written by (Tom King) and illustrated by (%s)" % NAME)

# Every year in a section dateline that no infobox carries is lifted out of
# the publication history by one of these, so none of them is typed.
YEARS = {
    "vol2start": r"the second volume of Batman began publication on "
                 r"September 21, (\d{4})",
    "vol2end":   r"The second volume of Batman concluded with issue #52, "
                 r"\"The List\", published on May 11, (\d{4})",
    "vol3start": r"the third volume of Batman began publication two weeks "
                 r"later on June 15, (\d{4})",
    "kingend":   r"Tom King's run ended with issue #85 at the end of (\d{4})",
    "morrend":   r"Issues #701-702 \(September - October (\d{4})\)",
}


def yr(prose, key):
    m = re.search(YEARS[key], prose)
    assert m, "the publication history no longer carries %s" % key
    return m.group(1)


def sections(prose):
    out = []

    out.append({
        "id": "dkr", "title": "The Dark Knight Returns",
        "sub": "A %s-issue miniseries · %s" % (FACTS["dkr"]["issues"],
                                               FACTS["dkr"]["span"]),
        "intro": (
            "Frank Miller writing and drawing an old Batman in a future that is "
            "nobody's continuity but its own — and the book that made every "
            "list like this one possible. It depends on nothing before it and "
            "nothing after it depends on it, which is exactly why it is the "
            "door: four issues, no homework.\n\n"
            "Read it first or read it last. The only wrong answer is skipping it "
            "because it is old."),
        "links": [{"label": ARTICLE["dkr"], "url": url(ARTICLE["dkr"])}],
        "items": rows("dkr", rng(1, 4), {"1": by("dkr")}),
        "open": True,
    })

    out.append({
        "id": "yearone", "title": "Year One",
        "sub": "Batman #404–407 · %s" % FACTS["yearone"]["span"],
        "intro": (
            "The origin, retold a year later by the same writer and this time "
            "in the main title. Everything after this in DC's post-Crisis "
            "continuity is built on it, and it is still four issues long.\n\n"
            "If you read one Batman comic, read this one."),
        "links": [{"label": ARTICLE["yearone"], "url": url(ARTICLE["yearone"])}],
        "items": rows("b1", rng(404, 407), {"404": by("yearone")}),
    })

    # The month is left off deliberately: its own article says March 1988 and
    # the bibliography's sort key says December 1988, so the row carries the
    # year both of them agree on.
    kj_year = FACTS["killingjoke"]["years"][0]
    out.append({
        "id": "killingjoke", "title": "The Killing Joke",
        "sub": "A one-shot · %s" % kj_year,
        "links": [{"label": ARTICLE["killingjoke"],
                   "url": url(ARTICLE["killingjoke"])}],
        "items": oneshot(ARTICLE["killingjoke"], "Batman: The Killing Joke",
                         "bat-killing-joke", by("killingjoke"), kj_year),
    })

    out.append({
        "id": "family", "title": "A Death in the Family",
        "sub": "Batman #426–429 · %s" % FACTS["family"]["span"],
        "links": [{"label": ARTICLE["family"], "url": url(ARTICLE["family"])}],
        "items": rows("b1", rng(426, 429), {"426": by("family")}),
    })

    out.append({
        "id": "arkham", "title": "Arkham Asylum",
        "sub": "A graphic novel · %s" % FACTS["arkham"]["span"],
        "links": [{"label": "Arkham Asylum", "url": url(ARTICLE["arkham"])}],
        "items": oneshot(ARTICLE["arkham"],
                         "Arkham Asylum: A Serious House on Serious Earth",
                         "bat-arkham", by("arkham"),
                         FACTS["arkham"]["years"][0]),
    })

    out.append({
        "id": "halloween", "title": "The Long Halloween",
        "sub": "A %s-issue miniseries · %s" % (FACTS["halloween"]["issues"],
                                               FACTS["halloween"]["span"]),
        "intro": (
            "Thirteen issues, one per holiday, written into Year One's own "
            "continuity — so it reads straight off the back of it.\n\n"
            "It is also the only nineties entry here. The rest of that decade "
            "in the Bat-books is one continuous crossover — Knightfall "
            "through No Man's Land — which is a long contiguous read of its "
            "own rather than six sections of this one, so this list steps over "
            "it. The Long Halloween is self-contained and does not need any of "
            "it."),
        "links": [{"label": ARTICLE["halloween"], "url": url(ARTICLE["halloween"])}],
        "items": rows("lh", rng(1, 13), {"1": by("halloween")}),
    })

    out.append({
        "id": "hush", "title": "Hush",
        "sub": "Batman #608–619 · %s" % FACTS["hush"]["span"],
        "intro": (
            "Twelve issues in the main title, one writer, one artist, and a tour "
            "of the entire supporting cast — which makes it the easiest "
            "place to start if you want to know who everybody is. It assumes you "
            "have heard of the nineties without asking you to have read them."),
        "links": [{"label": ARTICLE["hush"], "url": url(ARTICLE["hush"])}],
        "items": rows("b1", rng(608, 619), {"608": by("hush")}),
    })

    out.append({
        "id": "underhood", "title": "Under the Hood",
        "sub": "Batman #635–641, 645–650 and Annual #25 · %s"
               % FACTS["underhood"]["span"],
        "intro": (
            "#642–644 are collected with War Games, a line-wide crossover, "
            "rather than with this story, so the numbering jumps. The Annual is "
            "last because that is where the story's own collected edition puts "
            "it."),
        "links": [{"label": ARTICLE["underhood"], "url": url(ARTICLE["underhood"])}],
        "items": (rows("b1", rng(635, 641) + rng(645, 650),
                       {"635": by("underhood")})
                  + rows("ann", ["25"], {"25": "Collected last, with the arc"})),
    })

    # #676 and the two Final Crisis tie-ins are placed from the R.I.P.
    # collection's own contents rather than from anybody's memory: it opens the
    # arc, and Morrison's last two issues close it.
    ripissues = sorted(int(i) for i in collection("Batman R.I.P.", "b1"))
    morrison_notes = {
        "655": by("morrison"),
        str(ripissues[0]): P.join_bits("“Batman R.I.P.” begins", by("rip")),
        str(ripissues[-2]): "A Final Crisis tie-in",
        str(ripissues[-1]): "A Final Crisis tie-in",
        "700": "The milestone issue",
        "701": "“R.I.P.: The Missing Chapter”",
    }
    morrison_items = rows("b1", rng(655, 658) + rng(663, 669) + rng(672, 683)
                          + rng(700, 702), morrison_notes)
    out.append({
        "id": "morrison", "title": "Grant Morrison",
        "sub": "Batman #655–683 and #700–702 · %s–%s · %d issues"
               % (FACTS["morrison"]["years"][0], yr(prose, "morrend"),
                  len(morrison_items)),
        "intro": (
            "Morrison spent seven years on Batman and used every comic ever "
            "published about him as raw material, on purpose — the fifties, "
            "the Silver Age, the bits everyone else quietly dropped. It is the "
            "most argued-about run here and the one that rewards knowing the "
            "history.\n\n"
            "This is the main-title half of it. The run also carries on through "
            "Batman and Robin, The Return of Bruce Wayne and Batman "
            "Incorporated — three more books, and a rabbit hole this list "
            "does not carry. #659–662 and #670–671 sit between its chapters "
            "without being part of it; #670–671 are collected with The "
            "Resurrection of Ra's al Ghul instead."),
        "links": [{"label": ARTICLE["morrison"], "url": url(ARTICLE["morrison"])},
                  {"label": ARTICLE["rip"], "url": url(ARTICLE["rip"])}],
        "items": morrison_items,
    })

    out.append({
        "id": "blackmirror", "title": "The Black Mirror",
        "sub": "Detective Comics #871–881 · %s" % FACTS["blackmirror"]["span"],
        "intro": (
            "Scott Snyder in Detective Comics rather than the main title — "
            "the section after this one is his main-title run. Dick Grayson is "
            "under the cowl for it, which the book explains as it goes.\n\n"
            "Eleven issues, self-contained, and closer to a crime comic than to "
            "a superhero one."),
        "links": [{"label": ARTICLE["blackmirror"], "url": url(ARTICLE["blackmirror"])}],
        "items": rows("dc", rng(871, 881), {"871": by("blackmirror")}),
    })

    pair = PAIR.search(prose)
    assert pair, "the prose no longer names the vol. 2 creative team"
    snyder = arc_notes("b2", SNYDER_ARCS)
    snyder["1"] = P.join_bits("%s with %s" % pair.groups(), snyder.get("1"))
    snyder["0"] = ("“Zero Month”, September 2012 — a standalone origin, "
                   "sitting where it was published")
    snyder["28"] = "A fill-in, illustrated by Dustin Nguyen"
    snyder["51"] = "Snyder and Capullo's last issue"
    snyder_items = (rows("b2", rng(1, 12), snyder) + rows("b2", ["0"], snyder)
                    + rows("b2", rng(13, 51), snyder))
    out.append({
        "id": "snyder", "title": "Scott Snyder and Greg Capullo",
        "sub": "Batman (vol. 2) #0–51 · %s–%s · %d issues"
               % (yr(prose, "vol2start"), yr(prose, "vol2end"),
                  len(snyder_items)),
        "intro": (
            "DC restarted its entire line in 2011 and this was the flagship: one "
            "writer and one artist on Batman #1 through #51, which is the last "
            "time the character had a single definitive book. If you want the "
            "modern answer to “where do I start”, it is here — the "
            "reboot means it assumes nothing at all.\n\n"
            "#0 sits where it was published rather than where it is collected. "
            "The four Villains Month issues numbered #23.1–23.4 are one-shots "
            "about villains and are not here, and neither is #52, which closes the "
            "volume after the run ends."),
        "links": [{"label": "Batman (comic book)", "url": url(BOOK)}],
        "items": snyder_items,
    })

    kp = KING_PAIR.search(prose)
    assert kp, "the prose no longer names the vol. 3 creative team"
    king = arc_notes("b3", KING_ARCS)
    king["1"] = P.join_bits("%s with %s" % kp.groups(), king.get("1"))
    king["85"] = "King's last issue"
    king_items = rows("b3", rng(1, 63) + rng(66, 85), king)
    out.append({
        "id": "king", "title": "Tom King",
        "sub": "Batman (vol. 3) #1–85 · %s–%s · %d issues"
               % (yr(prose, "vol3start"), yr(prose, "kingend"),
                  len(king_items)),
        "intro": (
            "Eighty-five issues planned as one hundred, written as a single "
            "long-form book about whether the character can be well. It is the "
            "most divisive run on this list by a distance — people who love "
            "it call it the best Batman comic ever made and people who do not "
            "bounce off it in six issues. Both reactions are normal; this is the "
            "one to veto if you are going to veto something.\n\n"
            "#64–65 are a Flash crossover written by somebody else and are "
            "not here, so the numbering jumps."),
        "links": [{"label": "Batman (comic book)", "url": url(BOOK)}],
        "items": king_items,
    })

    return out


# ------------------------------------------------------------------- the file --

def main():
    listing = read_sources()
    read_runs()
    prose = flat(W.clean(page(BOOK)))
    for needle in PROSE:
        assert flat(needle) in prose, \
            "source changed — %r no longer says %r" % (BOOK, needle)
    bib = flat(W.clean(listing))
    for needle in LIST_PROSE:
        assert flat(needle) in bib, \
            "source changed — %r no longer says %r" % (LIST, needle)
    for key, needle in RUN_PROSE:
        art = flat(W.clean(page(ARTICLE[key])))
        assert flat(needle) in art, \
            "source changed — %r no longer says %r" % (ARTICLE[key], needle)

    cross_check("family", "b1", rng(426, 429))
    cross_check("hush", "b1", rng(608, 619))
    cross_check("underhood", "b1", rng(635, 641) + rng(645, 650))
    cross_check("blackmirror", "dc", rng(871, 881))
    cross_check("morrison", "b1", rng(655, 658))
    assert "Annual #25" in FACTS["underhood"]["titles"], \
        "the arc article no longer carries the Annual"
    assert FACTS["dkr"]["issues"] == "4", "The Dark Knight Returns is not 4 issues"
    assert FACTS["halloween"]["issues"] == "13", "The Long Halloween is not 13 issues"
    assert "Dick Grayson" in FACTS["blackmirror"]["cast"], \
        "The Black Mirror's article no longer says who is under the cowl"

    # The two gaps this file explains to the reader, checked rather than recited.
    assert {"642", "643", "644"} <= collection("Batman: War Games Book Two", "b1"), \
        "#642-644 are no longer collected with War Games"
    assert collection("Batman: The Resurrection of Ra's al Ghul", "b1") \
        == {"670", "671"}, "#670-671 are no longer the Ra's al Ghul crossover"

    SECTIONS = sections(prose)
    assert not MISSING, (
        "%d issue(s) are not attested by any collected edition, so they are not "
        "going in the file: %s" % (len(MISSING), MISSING[:8]))
    for s in SECTIONS:
        for x in s["items"]:
            # CLU-555. A MARK'S WIDTH IS ISSUES, and since the CLU-465
            # rework every row here IS one issue, so every row weighs one.
            # That is what CLU-131 was actually about: the bug was a
            # PARTLY weighted list, where the template's
            # WEIGHT = x.w >= 0 ? x.w : 1 silently redefines every
            # unweighted row as one. Weighting all of them is the fix, not
            # the bug -- and it is what lets the DC Comics shelf draw this
            # door as 225 issues wide instead of as one mark among eight.
            # The two one-shot rows (The Killing Joke, Arkham Asylum) are
            # one comic each, so they weigh one like everything else.
            assert "w" not in x, "a row was weighted before the stamp"
            x["w"] = 1
            assert not x.get("url"), "links live on section headers, not rows"
    total = sum(len(s["items"]) for s in SECTIONS)

    p = {
        "slug": SLUG,
        "title": "Batman",
        "subtitle": "the essential runs, issue by issue",
        "kind": "comics",
        "popularity": 72,
        "year": "1986–2019",
        "blurb": "%d issues in twelve runs, from The Dark Knight Returns to the "
                 "end of Tom King's — a route through the character rather "
                 "than everything ever printed." % total,
        "unit": {"one": "issue", "many": "issues"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": "#1B2436",
        "accentDark": "#D8B740",
        "tiers": False,
        "notes": [
            ["The house's picks — veto freely.",
             "Batman has been published every month since 1940 in at least two "
             "titles at once, so there is no complete version of this list that "
             "anybody could finish. This is the other kind: twelve runs, chosen "
             "here, in the order they came out. If one is not for you, skip it "
             "loudly — the sections are independent enough that nothing "
             "later breaks. If something you love is missing, the notes below "
             "probably name it."],
            ["Rows are issues.",
             "One row per comic, not per collected volume, which is how every "
             "comics list in this catalogue works. Where a story ran through "
             "other books, only the issues of the title in the section heading "
             "are here — except Batman Annual #25 and Batman (vol. 2) #0, "
             "which sit at the point you read them. This list used to count "
             "collected stories instead, so anyone who ticked those rows starts "
             "again."],
            ["Which continuity, and where the numbers restart.",
             "Everything from Year One to The Black Mirror is post-Crisis DC "
             "continuity. The New 52 rebooted the line outright in 2011, which "
             "is where the Snyder run starts. DC Rebirth in 2016 is the other "
             "thing — a relaunch that kept the New 52's continuity while "
             "restoring much of what came before it — and it renumbered the "
             "book again, which is why the rows say which volume they are and "
             "why #1 happens three times. The Dark Knight Returns sits outside "
             "all of it."],
            ["The nineties are somewhere else.",
             "Knightfall, Prodigal, Contagion, Legacy, Cataclysm and No Man's "
             "Land are one contiguous crossover across every Bat-book for most "
             "of a decade. That is a long ordered read in its own right rather "
             "than six sections here, and none of it is duplicated on this list. "
             "The Long Halloween is the one nineties entry, because it is a "
             "self-contained miniseries that happens to land in the decade."],
            ["Also not here, on purpose.",
             "Broken City, Bruce Wayne: Fugitive, War Games, Dark Victory, the "
             "Gaiman two-parter, Morrison's three other Bat-titles, and "
             "everything after 2019. Some of that is good and none of it is "
             "load-bearing for the rest of the list; a reading list that carries "
             "everything is a publication history, which nobody finishes."],
            ["No hours, on any row.",
             "Comics publish no reading time and an issue count is not an hour, "
             "so nothing here is weighted. The strip divides evenly and every "
             "figure on the page is a plain issue count."],
            "Issue ranges machine-read from the collected-editions tables of "
            "Wikipedia's “List of Batman comics”, which cite each "
            "volume's contents issue by issue; no row is emitted that those "
            "tables do not name. Run boundaries, the creative teams and the "
            "gaps are asserted against the publication history in "
            "“Batman (comic book)”, and each run's months, writer and "
            "artist come from its own article's infobox — cross-checked "
            "against the collected editions wherever both name the issues.",
        ],
        "sections": SECTIONS,
    }

    assert all(x.get("w") == 1 for s in SECTIONS for x in s["items"]), \
        "a row escaped the weight stamp"
    out = P.write(p, legacy_ids=LEGACY)

    DATA.write_text(json.dumps(
        {"source": [LIST, BOOK] + sorted(ARTICLE.values()),
         "rejected_ranges": sorted(set(REJECTED)),
         "runs": {s["id"]: [x["t"] + " " + x["n"] for x in s["items"]]
                  for s in SECTIONS},
         "attested": {"%s|%s" % k: sorted(v, key=float)
                      for k, v in sorted(ATTEST.items(), key=lambda kv: kv[0][0])
                      if k[0] in {c[1] for c in SERIES.values()}}},
        indent=1, ensure_ascii=False, sort_keys=True) + "\n",
        # LF on Windows too: without it every run rewrites the whole
        # body as CRLF and a real change cannot be seen in the diff.
        encoding="utf-8", newline="\n")

    print("wrote %s and %s" % (out.name, DATA.name))
    print("  %d sections, %d issues" % (len(SECTIONS), total))
    for s in SECTIONS:
        print("   %-14s %-46s %3d" % (s["id"], s["sub"][:46], len(s["items"])))
    if REJECTED:
        print("  source ranges rejected as typos: %s" % sorted(set(REJECTED)))
    assert len(listing) > 100000, "the bibliography came back short"


if __name__ == "__main__":
    main()
