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
    return re.sub(r"\s+", " ", DASH.sub("-", wiki.clean(t)))


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
        # columns 2 and 4 are writer and notes; a rowspan there covers the rows
        # below it, which is how Secret Six gets its writer and the seven
        # miniseries get theirs.
        got = {}
        raw = list(cells[2:])
        for col in (2, 4):
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
# The article states the crossover's shape in prose: one-shot, then the two
# monthlies alternating, then an epilogue. Both ranges are pulled out of that
# sentence and zipped, so the interleave is derived rather than asserted.
def sinestro_order():
    m = re.search(r"alternating between ''\[?\[?Green Lantern.*?''\s*#([\d‐-―-]+)"
                  r"\s*and\s*''\[?\[?Green Lantern Corps[^']*''\s*#([\d‐-―-]+)",
                  SRC["scw"])
    assert m, "Sinestro Corps War: the alternation sentence changed shape"
    gl, glc = expand(m.group(1)), expand(m.group(2))
    assert len(gl) == len(glc) == 5, "unexpected alternation: %r %r" % (gl, glc)
    out = []
    for a, b in zip(gl, glc):
        out.append(("gl", a))
        out.append(("glc", b))
    return out


SCW_ORDER = sinestro_order()

_PARTS = re.search(r"main story consisted of (\w+) parts", SRC["scw"])
assert _PARTS and _PARTS.group(1) == "11", "Sinestro Corps War part count moved"


# ----------------------------------------------------------------------- rows
SEEN = set()


def row(series, num, note="", star=0, opt=0, key=None):
    ident = "gl-%s-%s" % (key or prop.slug(series), str(num).lstrip("#"))
    assert ident not in SEEN, "duplicate row %s" % ident
    SEEN.add(ident)
    return {"id": ident, "t": series, "n": "#%s" % str(num).lstrip("#"),
            "note": note, "star": star, "opt": opt, "url": ""}


GL = "Green Lantern (vol. 4)"
GLC = "Green Lantern Corps (vol. 2)"
# The bare series names, as the Blackest Night table writes them.
GL_TITLE, GLC_TITLE = "Green Lantern", "Green Lantern Corps"


def tidy(note):
    """A table's Notes cell as a row note: quotes off, sentence case kept."""
    return note.replace('"', "").strip()


def gl_rows(spec, notes=None, stars=(), key="v4"):
    notes = notes or {}
    return [row(GL, n, notes.get(n, ""), 2 if n in stars else 0, key=key)
            for n in expand(spec)]


def glc_rows(spec, notes=None, key="glc"):
    notes = notes or {}
    return [row(GLC, n, notes.get(n, ""), key=key) for n in expand(spec)]


def mini_rows(title, spec, note="", key=None):
    """A limited series, one row per issue, note on the first only."""
    nums = expand(spec)
    return [row(title, n, note if i == 0 else "", key=key)
            for i, n in enumerate(nums)]


def one_shot(fragment, note, key, opt=0, page="gl", title=None):
    """A single-issue row whose 'Title #n' is cited whole from a source."""
    cite(fragment, page)
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
          "hands Guy Gardner and Kyle Rayner the book they spend the next six "
          "years in. Tier 2 because the main title carries the plot without it — "
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

_scw_items = [row("Green Lantern: Sinestro Corps Special",
                  1, "part one", star=2, key="scwspecial")]
for _n, (_book, _num) in enumerate(SCW_ORDER, start=2):
    _title = GL if _book == "gl" else GLC
    _key = "v4" if _book == "gl" else "glc"
    _note = "part %d" % _n
    if _book == "gl" and _num == 25:
        _note = "part %d · its release slipped two weeks" % _n
    _scw_items.append(row(_title, _num, _note,
                          star=2 if (_book == "gl" and _num == 25) else 0,
                          key=_key))
cite("Green Lantern Corps (vol. 2) #16–19", "glc")
_scw_items.append(row(GLC, 19,
                      "rewritten late, after the reaction to the story",
                      key="glc"))
_scw_items.append(row(GL, 26, "epilogue", key="v4"))

section(
    id="sinestro", tier=1, title="The Sinestro Corps War",
    sub="2007 · eleven parts across two books",
    intro="The crossover that made the run. It alternates between the two "
          "monthlies chapter by chapter, which is the only genuinely difficult "
          "thing about reading it — the order below is the one the article "
          "states: the one-shot, then the two books trading off, then an "
          "epilogue back in the main title.\n\nGreen Lantern Corps #19 is not a "
          "numbered part. It was reworked after the fact and sits with the war "
          "in every collection of it, so it sits here.",
    items=_scw_items,
    links=links(("The crossover", W_SCW), ("Green Lantern vol. 4", W_GL),
                ("Green Lantern Corps vol. 2", W_GLC)),
)

section(
    id="talessinestro", tier=3, title="Tales of the Sinestro Corps",
    sub="2007 · four one-shots and a Secret Files · skippable",
    intro="Late additions DC commissioned once the war started selling, each one "
          "a single issue about a single member of the other side. None of them "
          "is load-bearing. The Secret Files issue is a reference book — rosters "
          "and back story — rather than a story.",
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
    intro="Two issues of fallout and one eight-page teaser. Short, and the "
          "groundwork for the next two years is all in here.",
    items=gl_rows(inside("#27-28", "Green Lantern vol. 4 #26–28, 36–38", "gl"))
          + [one_shot("DC Universe #0",
                      "a line-wide teaser; collected with these issues in the "
                      "Johns omnibus", "dcu", opt=1)],
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
          "numbered #0, which is a real chapter and not a preview.\n\nThe three "
          "books below ran in parallel, month for month, and no source this list "
          "reads puts them in a single issue-by-issue order. So each title is "
          "kept whole rather than guessing an interleave: read the main series, "
          "then the Green Lantern issues, then the Corps ones.",
    items=[row("Blackest Night", n,
               "Free Comic Book Day" if n == 0 else "",
               star=2 if n == 8 else 0, key="bn")
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

section(
    id="blackestglc", tier=2, title="Blackest Night · Green Lantern Corps",
    sub="2009–2010 · the Corps book through the event",
    intro="The same war from Oa. Tier 2 for the same reason the Corps book has "
          "been tier 2 all along — the plot survives without it and the run does "
          "not.",
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
_mini_items += [row("Untold Tales of Blackest Night", 1,
                    prop.join_bits("an anthology one-shot",
                                   bn("Untold Tales of Blackest Night",
                                      TIEIN)[1].split(",")[0] + " and five others"),
                    key="untold")]

section(
    id="blackestminis", tier=3, title="The Blackest Night miniseries",
    sub="2009–2010 · six three-issue tie-ins and an anthology · optional",
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
          "these are the issues that clear up after it, and they lead straight "
          "into War of the Green Lanterns, which is where the run properly "
          "changes shape.\n\nThe Brightest Day event itself is a different book, "
          "about Aquaman, Firestorm and the Martian Manhunter. It is not here.",
    items=gl_rows(spec("Green Lantern vol. 4 #53–62", "gl"))
          + [one_shot("Green Lantern: Larfleeze Christmas Special #1",
                      "a one-shot, collected with these issues", "larfleeze",
                      opt=1)],
    links=links(("Green Lantern vol. 4", W_GL), ("The event", W_BRIGHTEST)),
)

# ------------------------------------------------------------------ the object
TOTAL = sum(len(s["items"]) for s in SECTIONS)
assert TOTAL > 150, "the list came out short: %d rows" % TOTAL

PROP = {
    "slug": SLUG,
    "title": "Green Lantern",
    "subtitle": "Geoff Johns, Rebirth to Blackest Night",
    "kind": "comics",
    "popularity": 50,
    "year": "2004–2011",
    "blurb": "%d issues from Green Lantern: Rebirth #1 to Blackest Night #8 and "
             "its coda, in the order they're meant to be read." % TOTAL,
    "unit": {"one": "issue", "many": "issues"},
    "verb": {"base": "read", "past": "read", "ing": "reading"},
    "accent": "#117A3E",
    "accentDark": "#3BB273",
    "tiers": True,
    "notes": [
        ["Tiers.",
         "1 is the readable path — Rebirth, the Green Lantern monthly, and "
         "Blackest Night itself. 2 is the Corps book, which is where Guy, Kyle "
         "and John live and where half of both wars is fought. 3 is genuinely "
         "optional. The minimum viable path is Tier 1 alone."],
        ["The mantle, not the man.",
         "Hal Jordan is the lead and this is his comeback, but the ring has had "
         "four holders from Earth and all four are in here: John Stewart and "
         "Guy Gardner throughout, Kyle Rayner carrying the Corps book. This is "
         "post-Crisis continuity, before Flashpoint rebooted it."],
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
        "Sinestro Corps War article's own part-by-part breakdown, and the "
        "Blackest Night article's titles-involved table, which is where the "
        "tie-in rows and their writers come from.",
    ],
    "sections": SECTIONS,
}

if __name__ == "__main__":
    out = prop.write(PROP)
    print("%s: %d rows across %d sections" % (out, TOTAL, len(SECTIONS)))
