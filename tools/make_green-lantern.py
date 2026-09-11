#!/usr/bin/env python3
"""Generate properties/green-lantern.json.

    python3 tools/make_green-lantern.py

Geoff Johns' Green Lantern, from Green Lantern: Rebirth #1 to Blackest Night #8
— one continuous arc that runs across a miniseries, two monthlies and two
line-wide crossovers, which is exactly the shape that is hard to hold in your
head and the reason a reading order is worth having.

WHERE THE ISSUE NUMBERS COME FROM

Nothing here is typed from memory. Every range is asserted against a string in
a cached Wikipedia source before a row is written, so a mistyped number fails
the generator instead of shipping:

  * Green Lantern (comic book)  — the collected-editions table for vol. 4.
    Each trade names the issues it collects, which also supplies the section
    names: No Fear, Revenge of the Green Lanterns, Wanted: Hal Jordan, Secret
    Origin, Rage of the Red Lanterns, Agent Orange.
  * Green Lantern Corps         — the collected-editions list for vol. 2.
  * Green Lantern: Rebirth      — the infobox issue count.
  * Sinestro Corps War          — the Format section, which states the crossover
    in parts: a one-shot, then Green Lantern #21–25 alternating with Green
    Lantern Corps #14–18, then an epilogue. The alternation below is ZIPPED from
    those two ranges rather than typed, so it cannot drift from the source.
  * Blackest Night              — the "Titles involved" table, parsed whole. It
    is the only enumeration of the event's tie-ins that names issue numbers, and
    it carries the writer of each, which is what the tie-in rows use as a note.

THE ONE THING THE SOURCES DO NOT GIVE

An issue-by-issue interleave for Blackest Night. The three books ran in
parallel and no source in this repo orders them against each other, so this list
keeps each title whole and says so in the section intro rather than inventing a
sequence. The Sinestro Corps War alternation is different — the article states
it outright, so that one is interleaved.

BRIGHTEST DAY

In, but only the ten Green Lantern issues banded with it, and only at tier 3.
They finish what Blackest Night starts. The wider Brightest Day event is a
different book about Aquaman, Firestorm and the Martian Manhunter, and dragging
it in would double the list with comics that are not about Green Lantern.

No weights. Comics publish no per-issue reading time and a mix of weighted and
unweighted rows is the defect CLU-131 exists for.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki  # noqa: E402

SLUG = "green-lantern"
CACHE = pathlib.Path(__file__).resolve().parent.parent / "scratch" / SLUG

PAGES = {
    "gl": "Green Lantern (comic book)",
    "glc": "Green Lantern Corps",
    "rebirth": "Green Lantern: Rebirth",
    "scw": "Sinestro Corps War",
    "bn": "Blackest Night",
    "brightest": "Brightest Day",
}

W_GL = "https://en.wikipedia.org/wiki/Green_Lantern_(comic_book)"
W_GLC = "https://en.wikipedia.org/wiki/Green_Lantern_Corps"
W_REBIRTH = "https://en.wikipedia.org/wiki/Green_Lantern:_Rebirth"
W_SCW = "https://en.wikipedia.org/wiki/Sinestro_Corps_War"
W_BN = "https://en.wikipedia.org/wiki/Blackest_Night"
W_BRIGHTEST = "https://en.wikipedia.org/wiki/Brightest_Day"


# --------------------------------------------------------------------- sources
def load():
    """Cached wikitext for every page this generator reads."""
    out = {}
    for key, page in PAGES.items():
        t = wiki.wikitext(page, cache_dir=str(CACHE))
        assert t, "no wikitext for %s" % page
        out[key] = t
    return out


SRC = load()

# One flattened haystack per page. Wikipedia's dashes are inconsistent between
# the two tables this reads — the vol. 4 table uses en dashes, the omnibus rows
# and the Corps bullets use hyphens — so every comparison folds dashes and
# collapses whitespace rather than pretending the source is tidy.
DASH = re.compile(r"[‐-―−-]")


def flat(t):
    # Apostrophes go too. wiki.clean strips italic and bold markup by removing
    # PAIRS of apostrophes, so a five-apostrophe bold-italic title leaves one
    # behind on each side and "Green Lantern Corps (vol. 2) #47-57" reads back
    # as "'Green Lantern Corps' (vol. 2) #47-57". Dropping them from both the
    # haystack and the needle is the only comparison that survives that.
    t = re.sub(r"['’]", "", wiki.clean(t))
    return re.sub(r"\s+", " ", DASH.sub("-", t))


HAY = {k: flat(v) for k, v in SRC.items()}


def cite(fragment, *pages):
    """Assert a literal issue range appears in one of the named sources.

    This is the whole safety net. A row is only written after the string that
    justifies it has been found in a file on disk, so a transposed digit is a
    crash and never a shipped lie.
    """
    needle = flat(fragment)
    for p in pages:
        if needle in HAY[p]:
            return fragment
    raise AssertionError("not in %s: %r" % ("/".join(pages), fragment))


def spec(fragment, *pages):
    """cite(), returning just the issue part: 'GL vol. 4 #26-28, 36-38' -> the
    '#26-28, 36-38'. Keeps the range and the sentence that justifies it in one
    place, so the two cannot drift apart."""
    cite(fragment, *pages)
    return fragment[fragment.index("#"):]


def covered(target, *sources):
    """Assert every issue in `target` is accounted for by the cited fragments.

    Sections here are named for the trades that define them, and a trade is the
    only place Wikipedia states an issue range. Where a section spans two or
    more trades, this checks the union really does cover the span rather than
    trusting arithmetic done in my head.
    """
    have = set()
    for fragment, page in sources:
        have.update(expand(spec(fragment, page)))
    missing = sorted(set(expand(target)) - have)
    assert not missing, "%s: no source covers %s" % (target, missing)
    return target


def inside(target, fragment, *pages):
    """Assert `target` is a subset of one cited range, and return it.

    Rage of the Red Lanterns and the two issues after the Sinestro Corps War
    are collected out of issue order, so the trade that names them covers more
    ground than the section does. This reads the part it needs.
    """
    extra = sorted(set(expand(target)) - set(expand(spec(fragment, *pages))))
    assert not extra, "%s: %s are not in %r" % (target, extra, fragment)
    return target


def agrees(target, fragment, *pages):
    """Assert two independent sources state the same range, and return it.

    Blackest Night's titles table and the Green Lantern collected editions both
    say which issues of the monthly are part of the event. If they ever stop
    agreeing, the list should stop building rather than pick one.
    """
    assert set(expand(target)) == set(expand(spec(fragment, *pages))), \
        "%r and %r disagree" % (target, fragment)
    return target


# The Rebirth miniseries states its length in the infobox rather than a
# collected-editions line, so it is read from there.
_ISSUES = re.search(r"\|issues\s*=\s*(\d+)", SRC["rebirth"])
assert _ISSUES, "Green Lantern: Rebirth infobox has no issue count"
REBIRTH_N = int(_ISSUES.group(1))
assert REBIRTH_N == 6, "Rebirth issue count moved: %d" % REBIRTH_N


# ------------------------------------------------------------- the back edge
# Brightest Day is the soft edge of this list and the decision to take only part
# of it needs the facts it rests on checked, not asserted in prose. The event's
# own titles list says which book is about whom; these are the two lines the
# coda's section intro and the "Where it stops" note are built on.
BRIGHTEST_GL = spec("Green Lantern (vol. 4) #53-62", "brightest")
for _who in ("Aquaman", "Firestorm", "Martian Manhunter"):
    assert _who in HAY["brightest"], \
        "Brightest Day no longer names %s among its leads" % _who
for _after in ("Green Lantern Corps (vol. 2) #47-57",
               "Green Lantern: Emerald Warriors"):
    cite(_after, "brightest")


# ----------------------------------------------------------------- range maths
def expand(issues):
    """'#4-5, 7' -> [4, 5, 7]. '#0-8' -> [0..8]. '#46' -> [46]."""
    nums = []
    for part in DASH.sub("-", issues).replace("#", "").split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(\d+)-(\d+)$", part)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            assert a <= b, "backwards range %r" % part
            nums.extend(range(a, b + 1))
        else:
            assert re.match(r"^\d+$", part), "unparsable issue spec %r" % part
            nums.append(int(part))
    assert nums, "empty issue spec %r" % issues
    return nums


# ------------------------------------------------------------- the Blackest
# Night titles table, parsed whole. It is the only place that enumerates the
# event's tie-ins by issue number, and it also names each one's writer, which is
# what the tie-in rows carry as a note — a reader following a writer rather than
# a banner is the only sane way through thirty optional issues.
#
# Three shapes in that table have to be handled or the rows come out wrong:
#   * titles are wrapped in five apostrophes, and wiki.clean leaves one behind
#   * cells carry `rowspan="2" |` and `colspan="2" |` attribute prefixes, which
#     prop.validate rejects outright as wikitext junk
#   * the rowspan cells are real: seven miniseries share one Notes cell and
#     Secret Six shares Suicide Squad's writer, so they carry down or vanish
CELL = re.compile(r"^\|\s*(?:[^|\[{]*=[^|\[{]*\|)?\s*(.*)$", re.S)
ISSUE_CELL = re.compile(r"^#[\d,\s‐-―-]+$")


def cell(line):
    m = CELL.match(line)
    return wiki.clean(m.group(1) if m else line).strip("'\u2019 ")


def rowspan(line):
    m = re.search(r'rowspan="?(\d+)', line)
    return int(m.group(1)) if m else 1


def blackest_titles():
    m = re.search(r"== Titles involved ==(.*?)\n==", SRC["bn"], re.S)
    assert m, "Blackest Night: no titles table"
    groups, heading, pending = {}, None, {}
    for chunk in m.group(1).split("\n|-"):
        lines = [l.strip() for l in chunk.strip().split("\n") if l.strip()]
        head = next((l for l in lines if l.startswith("!") and "colspan" in l), None)
        if head:
            heading = wiki.clean(head.split("|")[-1])
            groups.setdefault(heading, [])
            pending = {}
            continue
        cells = [l for l in lines if l.startswith("|")]
        if len(cells) < 2 or heading is None:
            continue
        title, issues = cell(cells[0]), cell(cells[1])
        if not title or not ISSUE_CELL.match(issues):
            continue
        # Columns are title, issues, writer, artist, notes. The artist column
        # has to be walked even though nothing reads it, or the notes cell is
        # read out of the artist's slot; and a rowspan in any of them covers
        # the rows below, which is how Secret Six gets Suicide Squad's writer
        # and the seven miniseries get their shared Notes cell.
        got, raw = {}, list(cells[2:])
        for col in (2, 3, 4):
            if col in pending:
                got[col], pending[col][0] = pending[col][1], pending[col][0] - 1
                if pending[col][0] == 0:
                    del pending[col]
                continue
            line = raw.pop(0) if raw else "|"
            got[col] = cell(line)
            if rowspan(line) > 1:
                pending[col] = [rowspan(line) - 1, got[col]]
        groups[heading].append((title, issues, got[2], got[4]))
    for want in ("Preludes", "Main series", "Other tie-ins"):
        assert groups.get(want), "Blackest Night table lost its %s" % want
    return groups


BN = blackest_titles()


def bn(title, heading):
    """An (issues, writer, note) triple from the Blackest Night table.

    The heading is required rather than convenient: Green Lantern appears twice
    in that table, once as a prelude and once as the crossover proper, and a
    lookup by title alone silently picks whichever came last.
    """
    rows = [r for r in BN[heading] if r[0] == title]
    assert len(rows) == 1, "%r under %r: %d rows" % (title, heading, len(rows))
    return rows[0][1:]


PRELUDE, MAIN, WAR, TIEIN = ("Preludes", "Main series", '"War of Light" tie-in',
                             "Other tie-ins")
assert BN.get(WAR), "Blackest Night table lost its War of Light group"


# --------------------------------------------------- the Sinestro Corps War
# This crossover cannot be ordered by zipping the two issue ranges, and the
# article says so three separate ways. It calls the main story 11 parts. It
# then gives "Parts Two through Ten" to an alternation between Green Lantern
# #21-25 and Green Lantern Corps #14-18 - nine part numbers for ten issues, so
# one of those ten is not in the alternation. And its citation for the finale
# names which one: "''The Sinestro Corps War'' part 11. ''Green Lantern''
# (vol. 4) #25." Green Lantern #25 was delayed two weeks and shipped last, so
# Corps #18 is part 10 and the alternation covers the nine issues left over.
#
# So the part numbers are read out of the article at both ends and the middle
# is derived between them. Nothing here is counted off a list index.
WORD = {"Two": 2, "Three": 3, "Four": 4, "Five": 5, "Six": 6, "Seven": 7,
        "Eight": 8, "Nine": 9, "Ten": 10, "Eleven": 11}


def sinestro_order():
    m = re.search(r"alternating between ''\[?\[?Green Lantern.*?''\s*#([\d‐-―-]+)"
                  r"\s*and\s*''\[?\[?Green Lantern Corps[^']*''\s*#([\d‐-―-]+)",
                  SRC["scw"])
    assert m, "Sinestro Corps War: the alternation sentence changed shape"
    gl, glc = expand(m.group(1)), expand(m.group(2))
    assert len(gl) == len(glc) == 5, "unexpected alternation: %r %r" % (gl, glc)

    # The last part, from the article's own citation for it.
    f = re.search(r"''The Sinestro Corps War'' part (\d+)\.\s*''Green Lantern''"
                  r"\s*\(vol\. \d\) #(\d+)", SRC["scw"])
    assert f, "Sinestro Corps War: the citation numbering the finale is gone"
    finale, last = ("gl", int(f.group(2))), int(f.group(1))
    assert finale[1] in gl, \
        "finale #%d is outside the alternation range %r" % (finale[1], gl)

    # The span the alternation covers, from the sentence that states it.
    sp = re.search(r"Parts (\w+) through (\w+) were released", SRC["scw"])
    assert sp, "Sinestro Corps War: the parts-two-through-ten sentence moved"
    lo, hi = WORD[sp.group(1)], WORD[sp.group(2)]
    assert lo == 2 and hi == last - 1, \
        "parts %d-%d do not sit between part one and part %d" % (lo, hi, last)

    # Nine parts for nine issues once the finale is set aside, which is the
    # arithmetic that proves a straight zip of the two ranges wrong.
    rest = [("gl", n) for n in gl if n != finale[1]] + [("glc", n) for n in glc]
    assert len(rest) == hi - lo + 1, \
        "%d issues for parts %d-%d" % (len(rest), lo, hi)

    # Alternate, main title first. The Corps book runs on by one at the end,
    # because the finale it would otherwise alternate with comes after it.
    heads = [x for x in rest if x[0] == "gl"]
    tails = [x for x in rest if x[0] == "glc"]
    out = []
    while heads or tails:
        if heads:
            out.append(heads.pop(0))
        if tails:
            out.append(tails.pop(0))
    out.append(finale)

    numbered = list(zip(range(lo, last + 1), out))
    assert numbered[-1] == (last, finale), "the finale lost its part number"
    assert (hi, ("glc", glc[-1])) in numbered, \
        "Corps #%d should be part %d" % (glc[-1], hi)
    return numbered


SCW_ORDER = sinestro_order()

_PARTS = re.search(r"main story consisted of (\w+) parts", SRC["scw"])
assert _PARTS and _PARTS.group(1) == "11", "Sinestro Corps War part count moved"
assert SCW_ORDER[-1][0] == int(_PARTS.group(1)), \
    "the last part numbered is not the last part the article counts"

# The delay is the reason the finale falls after the Corps book's last chapter,
# so the sentence that states it is checked rather than remembered.
assert "The conclusion of ''Green Lantern'' #25 was delayed by two weeks." \
    in SRC["scw"], "Sinestro Corps War: the delay sentence moved"


# ----------------------------------------------------------------------- rows
SEEN = set()


def row(series, num, note="", star=None, opt=0, key=None):
    num = int(str(num).lstrip("#"))
    ident = "gl-%s-%d" % (key or prop.slug(series), num)
    assert ident not in SEEN, "duplicate row %s" % ident
    SEEN.add(ident)
    if star is None:
        star = STARS.get((series, num), 0)
    return {"id": ident, "t": series, "n": "#%d" % num,
            "note": note, "star": star, "opt": opt, "url": ""}


GL = "Green Lantern (vol. 4)"
GLC = "Green Lantern Corps (vol. 2)"
# The bare series names, as the Blackest Night table writes them.
GL_TITLE, GLC_TITLE = "Green Lantern", "Green Lantern Corps"


# Row notes are prose, so a counted thing in one is spelled out.
NUMBER = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
          7: "seven", 8: "eight", 9: "nine"}


def tidy(note):
    """A table's Notes cell as a row note: quotes off, sentence case kept."""
    return note.replace('"', "").strip()


# Standouts. Two is "this is the issue people mean when they recommend the
# run"; one is a landmark worth knowing you have reached. Kept to six rows in
# 192, because a star on everything is a star on nothing.
STARS = {("Green Lantern: Rebirth", 1): 1, (GL, 25): 2, (GL, 29): 1,
         ("Green Lantern: Sinestro Corps Special", 1): 2,
         ("Blackest Night", 1): 1, ("Blackest Night", 8): 2}


def gl_rows(issues, notes=None, key="v4"):
    notes = notes or {}
    return [row(GL, n, notes.get(n, ""), key=key) for n in expand(issues)]


def glc_rows(spec, notes=None, key="glc"):
    notes = notes or {}
    return [row(GLC, n, notes.get(n, ""), key=key) for n in expand(spec)]


def mini_rows(title, spec, note="", key=None):
    """A limited series, one row per issue, note on the first only."""
    nums = expand(spec)
    return [row(title, n, note if i == 0 else "", key=key)
            for i, n in enumerate(nums)]


def one_shot(fragment, note, key, opt=0, page="gl", title=None, num=None):
    """A single-issue row whose 'Title #n' is cited whole from a source.

    `num` is for the handful of one-shots a source names without an issue
    number — they are all #1, but typing that here rather than reading it keeps
    the citation honest about what it did and did not find.
    """
    cite(fragment, page)
    name = fragment
    if num is None:
        name, num = fragment.rsplit(" #", 1)
    return row(title or name, num, note, opt=opt, key=key)


def links(*pairs):
    return [{"label": a, "url": b} for a, b in pairs]


# ------------------------------------------------------------------- sections
SECTIONS = []


def section(**kw):
    SECTIONS.append(kw)


section(
    id="rebirth", tier=1, title="Green Lantern: Rebirth",
    sub="2004–2005 · start here",
    intro="Six issues that put Hal Jordan back in the ring and, more usefully, "
          "set out the rules everything after this runs on. You do not need to "
          "have read a Green Lantern comic before it; it is written for someone "
          "who has not.",
    items=(mini_rows("Green Lantern: Rebirth",
                     spec("Green Lantern: Rebirth #1–6", "gl"), key="rebirth")
           + [one_shot("Green Lantern Secret Files and Origins 2005 #1",
                       "profiles and a short story; collected with Rebirth",
                       "secretfiles", opt=1)]),
    links=links(("The miniseries", W_REBIRTH)),
)
assert len(SECTIONS[-1]["items"]) == REBIRTH_N + 1

section(
    id="nofear", tier=1, title="No Fear · Revenge of the Green Lanterns",
    sub="2005–2006 · the monthly begins",
    intro="Johns spends the first stretch of the monthly rebuilding the job — "
          "Hal back in a cockpit, the Corps back on Oa, a villain list worth "
          "having. The two trades split at #6, and the run gets noticeably "
          "better across the second one.",
    items=gl_rows(covered("#1-13", ("Green Lantern vol. 4 #1–6", "gl"),
                          ("Green Lantern vol. 4 #7–13", "gl"))),
    links=links(("Green Lantern vol. 4", W_GL)),
)

section(
    id="recharge", tier=2, title="Green Lantern Corps: Recharge",
    sub="2005–2006 · the Corps book starts here",
    intro="A five-issue miniseries that reopens the Corps as a going concern and "
          "hands Guy Gardner and Kyle Rayner the book they spend the rest of "
          "this list in. Tier 2 because the main title carries the plot without it — "
          "but half of both wars is fought over here, and reading only the "
          "Hal issues leaves the Corps as scenery.",
    items=mini_rows("Green Lantern Corps: Recharge",
                    spec("Green Lantern Corps:Recharge #1-5", "gl"),
                    key="recharge"),
    links=links(("Green Lantern Corps vol. 2", W_GLC)),
)

section(
    id="corpsbook", tier=2, title="To Be a Lantern · The Dark Side of Green",
    sub="2006–2007 · Guy, Kyle, Soranik, Vath and Isamot",
    intro="The ongoing Corps book, running alongside the Green Lantern monthly "
          "from here to the end of the list. It is a police procedural set in "
          "space and it is very good at being one.",
    items=glc_rows(covered("#1-13",
                           ("Green Lantern Corps (vol. 2) #1–6", "glc"),
                           ("Green Lantern Corps (vol. 2) #7–13", "glc"))),
    links=links(("Green Lantern Corps vol. 2", W_GLC)),
)

section(
    id="wanted", tier=1, title="Wanted: Hal Jordan",
    sub="2007 · the last stretch before the war",
    intro="Back on the main title. The final issues here are the ones the "
          "Sinestro Corps War is built on top of, and the Tales of the Sinestro "
          "Corps hardcover collects parts of them for that reason.",
    items=gl_rows(spec("Green Lantern vol. 4 #14–20", "gl")),
    links=links(("Green Lantern vol. 4", W_GL)),
)

_scw_items = [row("Green Lantern: Sinestro Corps Special", 1, "part 1",
                  key="scwspecial")]
for _n, (_book, _num) in SCW_ORDER:
    _title = GL if _book == "gl" else GLC
    _key = "v4" if _book == "gl" else "glc"
    _note = "part %d" % _n
    if _n == SCW_ORDER[-1][0]:
        _note = "part %d · its release was delayed two weeks" % _n
    _scw_items.append(row(_title, _num, _note, key=_key))
cite("Green Lantern Corps (vol. 2) #16–19", "glc")
_scw_items.append(row(GLC, 19,
                      "rewritten late, after the reaction to the story",
                      key="glc"))
_scw_items.append(row(GL, 26, "epilogue", key="v4"))

section(
    id="sinestro", tier=1, title="The Sinestro Corps War",
    sub="2007 · the crossover, chapter by chapter across both titles",
    intro="The crossover that made the run. It alternates between the two "
          "monthlies chapter by chapter, which is the only genuinely difficult "
          "thing about reading it. The article's own numbering runs: the "
          "one-shot is part one, parts two to ten alternate between the two "
          "books, and part eleven is Green Lantern #25, whose release was "
          "delayed two weeks — so the Corps book's last chapter comes before "
          "it. The epilogue is back in the main title.\n\nGreen Lantern Corps "
          "#19 is not a numbered part. It was rewritten after the fact, in "
          "response to the reaction to the story, and the hardcover of the "
          "war's second half collects it, so it sits here.",
    items=_scw_items,
    links=links(("The crossover", W_SCW), ("Green Lantern vol. 4", W_GL),
                ("Green Lantern Corps vol. 2", W_GLC)),
)

section(
    id="talessinestro", tier=3, title="Tales of the Sinestro Corps",
    sub="2007 · the one-shots, and the one tie-in outside the Lantern books",
    intro="Late additions DC commissioned once the war started selling, each "
          "one a single issue about one character: Parallax, the Cyborg "
          "Superman, Superman-Prime and Ion. None of them is load-bearing. The "
          "Secret Files issue is a reference book — rosters and back story — "
          "rather than a story.",
    items=[one_shot("Tales of the Sinestro Corps: Parallax #1", "Ron Marz",
                    "talesparallax"),
           one_shot("Tales of the Sinestro Corps: Cyborg-Superman #1",
                    "Alan Burnett", "talescyborg"),
           one_shot("Tales of the Sinestro Corps: Superman-Prime #1",
                    "Geoff Johns", "talesprime"),
           one_shot("Tales of the Sinestro Corps: Ion #1", "Ron Marz",
                    "talesion"),
           one_shot("Green Lantern/Sinestro Corps Secret Files #1",
                    "rosters and back story, not a story", "scwfiles"),
           one_shot("Blue Beetle #20",
                    "the only tie-in outside the two Lantern books",
                    "bluebeetle", page="scw")],
    links=links(("The crossover", W_SCW)),
)

section(
    id="prelude", tier=1, title="After the war",
    sub="2008 · the quiet stretch that plants everything",
    intro="Two issues of fallout and a one-shot that trails what comes next. "
          "Short, and the groundwork for the next two years is all in here.",
    items=gl_rows(inside("#27-28", "Green Lantern vol. 4 #26–28, 36–38", "gl"))
          + [one_shot("DC Universe #0",
                      "not a Green Lantern book; more of Blackest Night was "
                      "first revealed here, and the Johns omnibus collects it "
                      "with these issues", "dcu", opt=1)],
    links=links(("Green Lantern vol. 4", W_GL)),
)

section(
    id="secretorigin", tier=2, title="Secret Origin",
    sub="2008 · a flashback, and the one part you can skip without losing the thread",
    intro="Seven issues retelling how Hal Jordan got the ring, rebuilt around "
          "everything the run has introduced since Rebirth. It stops the "
          "forward story dead, which is why it is tier 2 — but it is also the "
          "single best jumping-on point in the whole list, and if you are "
          "handing this to someone who has never read a Green Lantern comic, "
          "hand them this.",
    items=gl_rows(spec("Green Lantern vol. 4 #29–35", "gl")),
    links=links(("Green Lantern vol. 4", W_GL)),
)

section(
    id="rage", tier=1, title="Rage of the Red Lanterns",
    sub="2008–2009 · the spectrum opens out",
    intro="The one-shot has a Final Crisis banner on the cover and no Final "
          "Crisis in it; it is chapter one of this story and the trade collects "
          "it as such.",
    items=[one_shot("Final Crisis Rage of the Red Lanterns #1",
                    "a Final Crisis cover banner on a Green Lantern chapter",
                    "fcrage", title="Final Crisis: Rage of the Red Lanterns")]
          + gl_rows(inside("#36-38", "Green Lantern vol. 4 #26–28, 36–38", "gl")),
    links=links(("Green Lantern vol. 4", W_GL)),
)

section(
    id="orange", tier=1, title="Agent Orange",
    sub="2009 · the last arc before the event",
    intro="Four issues, and the last of the colours to get an introduction. "
          "Everything from here is Blackest Night.",
    items=gl_rows(spec("Green Lantern vol. 4 #39–42", "gl")),
    links=links(("Green Lantern vol. 4", W_GL)),
)

section(
    id="corpswar", tier=2, title="Ring Quest · Sins of the Star Sapphire · Emerald Eclipse",
    sub="2008–2009 · the Corps book runs to meet the event",
    intro="Everything the Corps book does between the two wars, in issue order. "
          "The Alpha Lantern two-parter at #21–22 is collected years later with "
          "a story it leads into rather than with the issues either side of it, "
          "which is a shelving decision and not a reading one — it is in its "
          "place here.",
    items=glc_rows(covered("#20-38",
                           ("Green Lantern Corps (vol. 2) #19–20, 23–26", "glc"),
                           ("Green Lantern Corps (vol. 2) #21–22, 48–52", "glc"),
                           ("Green Lantern Corps (vol. 2) #27–32", "glc"),
                           ("Green Lantern Corps (vol. 2) #33–38", "glc"))),
    links=links(("Green Lantern Corps vol. 2", W_GLC)),
)

_bn_main = bn("Blackest Night", MAIN)
section(
    id="blackest", tier=1, title="Blackest Night",
    sub="2009–2010 · the main series",
    intro="The spine of the event. It opens with a Free Comic Book Day issue "
          "numbered #0, which is a real chapter and not a preview.\n\nThis "
          "section and the two after it ran in parallel, month for month, and "
          "no source this list reads puts them in a single issue-by-issue "
          "order. So each title is kept whole rather than interleaved on a "
          "guess: read the main series, then the Green Lantern issues, then "
          "the Corps ones.",
    items=[row("Blackest Night", n,
               "Free Comic Book Day" if n == 0 else "", key="bn")
           for n in expand(_bn_main[0])],
    links=links(("The event", W_BN)),
)

section(
    id="blackestgl", tier=1, title="Blackest Night · Green Lantern",
    sub="2009–2010 · the main title through the event",
    intro="The War of Light half of the crossover, told in the monthly. These "
          "are the issues that do the work the main series does not have room "
          "for, and they are not optional.",
    items=gl_rows(agrees(bn("Green Lantern", WAR)[0],
                         "Green Lantern vol. 4 #43–52", "gl")),
    links=links(("The event", W_BN), ("Green Lantern vol. 4", W_GL)),
)

# The Corps book has two end points for this event in the sources, and the
# section below says on the page which one the list follows. All three
# statements are checked here so that sentence cannot quietly go stale: the
# event's titles table stops at #46, the collection runs one further to #47,
# and Brightest Day's own titles list opens the NEXT event at #47 — which is
# what settles it.
_GLC_BN = expand(bn("Green Lantern Corps", WAR)[0])
assert _GLC_BN[-1] == 46, \
    "the Blackest Night titles table no longer ends the Corps book at #46"
cite("Green Lantern Corps'' (vol. 2) #39-47", "bn", "glc")
cite("Green Lantern Corps (vol. 2) #47-57", "brightest")

section(
    id="blackestglc", tier=2, title="Blackest Night · Green Lantern Corps",
    sub="2009–2010 · the Corps book through the event",
    intro="The same war from Oa. Tier 2 for the same reason the Corps book "
          "has been tier 2 all along — the plot survives without it and the "
          "run does not.\n\nIt stops at #46, which is where the event's own "
          "titles table stops. The collection runs one further, to #47, but "
          "Brightest Day's titles list hands Green Lantern Corps #47–57 to the "
          "event after this one — so #47 is the next book's first issue rather "
          "than this one's last.",
    items=glc_rows(bn("Green Lantern Corps", WAR)[0]),
    links=links(("The event", W_BN), ("Green Lantern Corps vol. 2", W_GLC)),
)

_minis = ["Blackest Night: Tales of the Corps", "Blackest Night: Batman",
          "Blackest Night: The Flash", "Blackest Night: JSA",
          "Blackest Night: Superman", "Blackest Night: Titans",
          "Blackest Night: Wonder Woman"]
_mini_items = []
for _t in _minis:
    _issues, _writer, _ = bn(_t, TIEIN)
    _mini_items += mini_rows(_t, _issues, _writer, key=prop.slug(_t))
_untold_writers = bn("Untold Tales of Blackest Night", TIEIN)[1].split(", ")
_mini_items += [row("Untold Tales of Blackest Night", 1,
                    "an anthology one-shot: %s and %s others"
                    % (_untold_writers[0], NUMBER[len(_untold_writers) - 1]),
                    key="untold")]

section(
    id="blackestminis", tier=3, title="The Blackest Night miniseries",
    sub="2009–2010 · the tie-in miniseries, and one anthology · optional",
    intro="Each one takes a corner of the DC line and runs the event through it. "
          "Tales of the Corps is the odd one out and the one worth reading "
          "first: it is a set of short back stories for the characters the main "
          "series assumes you know.",
    items=_mini_items,
    links=links(("The event", W_BN)),
)

_other = []
for _t, _issues, _writer, _note in BN[PRELUDE]:
    if _t in (GL_TITLE, GLC_TITLE):
        continue
    _other += mini_rows(_t, _issues, prop.join_bits("prelude", _writer),
                        key=prop.slug(_t))
for _t, _issues, _writer, _note in BN[TIEIN]:
    if _t in _minis or _t == "Untold Tales of Blackest Night":
        continue
    _other += mini_rows(_t, _issues, prop.join_bits(_writer, tidy(_note)),
                        key=prop.slug(_t))

section(
    id="blackesttieins", tier=3, title="Blackest Night across the line",
    sub="2009–2010 · every other book that carried the banner · genuinely optional",
    intro="The event reached most of the DC line, and this is the rest of it — "
          "single issues and two-parters of other people's books. None of it is "
          "needed to follow the story and some of it is very good; the notes say "
          "who wrote each one so you can follow a writer rather than a banner.",
    items=_other,
    links=links(("The event", W_BN)),
)

section(
    id="brightest", tier=3, title="Brightest Day",
    sub="2010–2011 · the coda · optional",
    intro="Ten issues of the monthly that finish what Blackest Night starts, "
          "banded with a DC-wide event they are largely independent of. Tier 3 "
          "because the arc this list is about ends at Blackest Night #8 — but "
          "these are the issues that clear up after it, and they run to the "
          "edge of War of the Green Lanterns, which is where this list "
          "stops.\n\nTwo things deliberately left out. The Brightest Day event "
          "itself is a different book, about Aquaman, Firestorm and the Martian "
          "Manhunter. And the Corps book keeps going past this point, as does "
          "Emerald Warriors — both of them straight into the next war, which "
          "wants a list of its own.",
    items=gl_rows(agrees(BRIGHTEST_GL, "Green Lantern vol. 4 #53–62", "gl"))
          + [one_shot("Green Lantern: Larfleeze Christmas Special",
                      "never bannered with the event; the only volume that "
                      "collects it runs well past where this list stops",
                      "larfleeze", opt=1, page="brightest",
                      title="Green Lantern: Larfleeze Christmas Special",
                      num=1)],
    links=links(("Green Lantern vol. 4", W_GL), ("The event", W_BRIGHTEST)),
)

# ------------------------------------------------------------------ the object
TOTAL = sum(len(s["items"]) for s in SECTIONS)
assert TOTAL > 150, "the list came out short: %d rows" % TOTAL

PROP = {
    "slug": SLUG,
    "title": "Green Lantern",
    # The continuity goes in the subtitle because "Rebirth" is also the name
    # of a LATER DC continuity, and because Lanterns sits a few rows away in
    # the catalogue and is a television show.
    "subtitle": "Geoff Johns, Rebirth to Blackest Night · post-Crisis continuity",
    "kind": "comics",
    "popularity": 50,
    "year": "2004–2011",
    "blurb": "%d issues, Green Lantern: Rebirth #1 to Blackest Night #8 and "
             "the coda after it, in the order they're meant to be read." % TOTAL,
    "unit": {"one": "issue", "many": "issues"},
    "verb": {"base": "read", "past": "read", "ing": "reading"},
    "accent": "#117A3E",
    "accentDark": "#3BB273",
    "tiers": True,
    "notes": [
        ["The mantle, not the man.",
         "Hal Jordan is the lead and this is his comeback, but the ring has had "
         "four holders from Earth and all four are in here: John Stewart and "
         "Guy Gardner throughout, Kyle Rayner carrying the Corps book. This is "
         "post-Crisis continuity, before Flashpoint rebooted it — and the "
         "Rebirth in the title is the 2004 miniseries, not the 2016 relaunch "
         "that borrowed the word."],
        ["Tiers.",
         "1 is the readable path — Rebirth, the Green Lantern monthly, "
         "Blackest Night itself, and the Corps chapters of the Sinestro Corps "
         "War, which is a crossover you cannot read half of. 2 is the rest of "
         "the Corps book, where Guy, Kyle and John live and where half of "
         "Blackest Night is fought. 3 is genuinely optional. The minimum "
         "viable path is Tier 1 alone."],
        ["Where it stops.",
         "The arc ends at Blackest Night #8. The ten Green Lantern issues "
         "banded Brightest Day are here as a tier 3 coda because they clear up "
         "after it — the wider Brightest Day event is a different book about "
         "other characters and is deliberately not in this list."],
        ["Not the television show.",
         "Lanterns, elsewhere in the catalogue, is the 2026 series. This is the "
         "comics, and the two share almost nothing but a ring."],
        "Issue ranges machine-read from Wikipedia: the collected-editions "
        "tables for Green Lantern vol. 4 and Green Lantern Corps vol. 2, the "
        "Sinestro Corps War article's part numbering — including the "
        "citation that names its last part — and the Blackest Night article's "
        "titles-involved table, which is where the tie-in rows and their "
        "writers come from.",
    ],
    "sections": SECTIONS,
}

if __name__ == "__main__":
    out = prop.write(PROP)
    print("%s: %d rows across %d sections" % (out, TOTAL, len(SECTIONS)))
