#!/usr/bin/env python3
"""Generate properties/spawn.json.

    python3 tools/make_spawn.py

Spawn and its spin-offs in reading order, transcribed from the reading order
Nathan supplied — Blake Whitlow's "Spawn Reading Order / Chronology", kept
updated since 2012:

    https://docs.google.com/document/d/11i91JQNlfxKwxr4yV1S35444mO0wIsTHgXxm7lMGUCc/mobilebasic

That document is the scope. It is emphatically *not* a chronological order —
its own preamble says so twice — it is the order that introduces the cast and
the terminology without spoiling the series' turns, which is exactly the order
a tracker wants. So the rows here are in document order, and nothing is
resequenced to match publication dates.

WHAT IS TAKEN. The document has five tables. The first two are the reading
order proper: "SPAWN READING ORDER" (1992 to the Spawn's Universe relaunch)
and "SPAWN'S UNIVERSE READING ORDER" (the four concurrent ongoings that follow
it). Those two are the list. Deliberately left out:

  * the ANNOUNCED PROJECTS table — series with no issues published yet, listed
    as ranges rather than issues, so they cannot be rows in an issue tracker;
  * the RELEASE ORDER calendar — the same issues again, by cover month; it is
    an index, not a second order. It was tried as a source of cover years for
    the section headers and abandoned: it covers 197 of the 375 Spawn issues
    with gaps, and from 2021 it abbreviates the four ongoings to "King #36",
    "Scorched #31" in cells that run several titles together, which does not
    reconcile cleanly. A year on two headers in five is worse than none, so
    headers carry issue ranges instead;
  * the MISCELLANY appendix — toy comics, the parody books, the cancelled
    projects, and a trade-paperback buying guide. The document files these
    outside the order on purpose and marks nearly all of them non-canon.

The two reading-order tables also each carry the Spawn's Universe one-shot, as
the hinge between them; it is one comic and gets one row, at the head of the
Spawn's Universe order where that order begins.

SECTIONS are the document's own arc column, which uses rowspan to bracket the
issues belonging to each arc. Nothing is merged or re-cut: if the document
calls one issue an arc, it is a section with one row.

NOTES are rewritten rather than copied. The source's annotations are one
reader's prose and occasionally give away a turn; what survives here is the
placement fact underneath — what an issue is, where it sits, what it crosses
over with — in the house style, screened for spoilers. NOTE_REWRITES below is
keyed by issue and asserted exhaustive, so a future edit to the document that
adds an annotation fails the build instead of silently dropping it.
"""
import html
import json
import pathlib
import re
import sys
import collections

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop  # noqa: E402

SLUG = "spawn"
ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "scratch" / "spawn" / "doc_mobilebasic.html"
# The distilled source: the two reading-order tables as flat rows, which is
# the whole of what this generator consumes. Committed, where the 2.5MB page it
# came from is not — a fresh clone regenerates the property from this alone.
EXTRACT = ROOT / "scratch" / "spawn" / "reading_order.json"

# The document's colour legend, keyed by the cell background it uses. The reds
# are shaded differently only to keep the four concurrent Spawn's Universe
# ongoings apart on screen; they all mean the same thing.
LEGEND = {
    "#000000": "Main series",
    "#cc0000": "Spin-off",
    "#e06666": "Spin-off",
    "#990000": "Spin-off",
    "#660000": "Spin-off",
    "#38761d": "One-shot",
    "#666666": "Optional",
    "#434343": "Optional",
}

# Two unrelated Violator minis, 1994 and 2024, both titled "Violator" and both
# numbered from #1. The document keeps them apart only by position; the years
# are the ones it uses itself in its collections list.
VIOLATOR_1994 = "The World"      # the arc the 1994 mini is filed under
VIOLATOR_2024 = "Violator"

# The document marks the publication frontier with "(Most Recent Issue)" and
# then keeps listing solicited issues past it. Both facts are worth keeping:
# the marker becomes a note, the later issues stay in the order.
FRONTIER = re.compile(r"\s*\(Most Recent Issue\)\s*$")

# Arc titles the document leaves as a placeholder. "One-Shot" is the label it
# gives every standalone, so four different sections would otherwise share that
# header; those are titled after the comic itself instead.
ARC_TITLE = {
    "???": "Untitled arc",
    "???(Spawn Vol. 9)": "Spawn, Vol. 9",
}

# Trailing parentheticals on a one-shot's title: the format is already carried
# by its tag, and the publisher and alternate title read better as a note.
ONESHOT_TAIL = re.compile(r"\s*\((One-Shot|Image|DC/Image)\)", re.I)
AKA = re.compile(r"\s*\(A\.K\.A\.\s*(.+?)\)")

# ---------------------------------------------------------------------------
# Notes: {issue string as the document writes it: house-style note, or None to
# drop}. Every annotated row in the two reading-order tables must appear here.
NOTE_REWRITES = {
    "Spawn #001, Questions, Part 1": "In-story year 1992.",
    "Spawn #010, Crossing Over": "Meta commentary on the comic industry.",
    "Spawn #012, Flashback, Part 1": "Semi-crossover with Youngblood.",
    "Spawn/Batman (Image) (A.K.A. The Red Scare) (One-Shot)":
        "Leads straight into Spawn #21.",
    "Curse of the Spawn #23, Overt-Resurrection":
        "Placement uncertain — could also sit between Curse #22 and #25.",
    "Violator #1, The World, Part 1": "Runs concurrently with The Hunt.",
    "Spawn, Fan Edition #1, The Sword of Hell, Blood of the Innocent":
        "Placed after Violator, which introduces its cast.",
    "Youngblood #08, The Death of Chapel, Part 1":
        "Leads straight into Spawn #27. Possibly non-canon.",
    "Angela #1": "Leads straight into Spawn #29.",
    "Spawn #032, Appearances / Blood Feud: Preludes and Nocturnes":
        "Some editions carried a mini-comic prelude to Blood Feud.",
    "Spawn: Blood Feud #1": "Leads straight into Spawn #33.",
    "Spawn #039, Noel": "A Christmas issue.",
    "Medieval Spawn/Witchblade #1":
        "Crosses over with Top Cow's Witchblade and Arcanum.",
    "Medieval Spawn and Witchblade #1":
        "Kept here so Medieval Spawn's story runs unbroken.",
    "Spawn/WildC.A.T.s #1, Devil Day, Part 1":
        "Placement uncertain — this is the best fit. In-story year given as "
        "1996, unconfirmed.",
    "Spawn #050, Choices": "Months have passed since Violator.",
    "Spawn #052, Messiah":
        "Crosses over with Savage Dragon, and continues in Savage Dragon #30, "
        "which the source calls non-essential.",
    "Spawn #060, Dwarfed":
        "Cyan is two. Retcons the Youngblood Death of Chapel arc.",
    "Spawn #061, Sanctuary":
        "A soft reboot — some Spawniverse details are altered here.",
    "Curse of the Spawn #12, Codename: Priest":
        "Placed here for what Spawn #61 establishes.",
    "Cy-Gor #5, Then One Foggy Christmas Eve":
        "A Christmas issue, about a year on from Spawn #39.",
    "Curse of the Spawn #09, Limbo":
        "Leads into and crosses over with Spawn #62.",
    "Spawn #065, The Past": "A clean jumping-on point.",
    "Curse of the Spawn #01, Dark Future":
        "Placed here for its ties to Curse #9–11 and #17–19.",
    "Spawn: Blood & Salvation (One-Shot)": "Closes out the Dark Future arc.",
    "Spawn #067, Homeland": "A few weeks from winter.",
    "Spawn #068, Intersection": "Only months since Spawn took to the alleys.",
    "Spawn #070, Darkness": "Cyan is just under three.",
    "Curse of the Spawn #22, Deadland": "Possibly non-canon.",
    "Curse of the Spawn #25, Heart of Hell": "Possibly non-canon.",
    "Curse of the Spawn #29, Last Rites": "Possibly non-canon.",
    "Spawn #087, Folklore":
        "From here the series overlap; they are split into arcs for pacing.",
    "Curse of the Spawn #26, Brother's Keeper": "Leads into Sam and Twitch.",
    "Sam and Twitch #01, Udaku, Part 1": "Shortly after Spawn #87.",
    "Spawn, The Undead #1, A Face in the Crowd":
        "The Undead sits between Spawn #87 and #88.",
    "Spawn, The Undead #9, Waiting for Sparky":
        "Cover art exists for an unmade #10.",
    "Spawn: Blood & Shadows (One-Shot)":
        "Possibly non-canon. Placed from context in the main series.",
    "Curse of the Spawn #20, Dark Myth":
        "Possibly non-canon. Placed as a prelude to The Dark Ages.",
    "Spawn, The Dark Ages #01, Devil's Knight":
        "Placed here for what Spawn #75 establishes, and for pacing.",
    "Spawn #094, The Children's Hour":
        "In-story year 1998 or later, dated from a background reference.",
    "Spawn: Simony (One-Shot)": "Placed from context in the story.",
    "Hellspawn #01, The Clown, Part 1":
        "After Spawn #106. Contradicts the main series in places, but is "
        "largely treated as canon.",
    "Spawn: Architects of Fear (One-Shot)": "Placed from context in the story.",
    "Case Files, Sam and Twitch #01, Have You Seen Me, Part 1":
        "The whole Case Files run sits in the gap between Spawn #144 and #145.",
    "Spawn #145, Destination: Anywhere, Part 1":
        "A large timeskip sits between Spawn #144 and #145 — at least a "
        "couple of years.",
    "Spawn #156, Armageddon, Part 3": "Eight years on from Spawn #60.",
    "Spawn #164, Home Coming": "In-story year 2002 or later.",
    "Spawn #165, Mandarin Spawn": "A standalone set in the 1270s.",
    "Spawn #174, Gunslinger Spawn, Part 1": "Set in 1881.",
    "Spawn #175, Gunslinger Spawn, Part 2": "Set in 1881.",
    "Spawn #176, The Monster in the Bubble, Part 1":
        "In-story year 2007 or later, dated from a background reference.",
    "Spawn #179, War Spawn": "Set in 1896 and 1916.",
    "Spawn #185, Endgame, Part 1": "A clean jumping-on point.",
    "Sam and Twitch, The Writer #1, Incipit In Medias Res":
        "Placed from context.",
    "Haunt #01, Shillinger's Notes, Part 1":
        "Placed here because it eventually crosses into Spawn; the arcs "
        "alternate for pacing.",
    "Spawn #214, The Gathering Storm, Part 2":
        "Dated December 12th in the issue.",
    "Spawn #225, De-Programmed, Part 1":
        "November, 2008 or 2012 — 17 days after Spawn #219.",
    "Haunt #28, Lady Haunt, Part 4, While You Were Beaten!":
        "Cover art exists for an unmade #29–31.",
    "Spawn #233, Celebrity Savior, Part 5 / Spawn Costume Origin, Part 1":
        "Crosses over with Haunt, Sam and Twitch and Case Files.",
    "Spawn #239, The Dead Zone, Part 2": "Crosses over with Haunt.",
    "Spawn #243, Disappearance, Part 2": None,   # the compiler's own aside
    "Spawn #248, Coma, Part 3": "Crosses over with Haunt.",
    "Spawn: Resurrection (One-Shot)": "A clean jumping-on point.",
    "Spawn #255, Resurrection, Part 6":
        "Spawn #185–250 covers an undefined stretch of months, under a year.",
    "Spawn #263, Return to Earth, Part 1":
        "A one-year timeskip sits between Spawn #262 and #263.",
    "Ant #01": "A crossover arc with Savage Dragon and Ant.",
    "Ant #3": "Retells Spawn #265 from Ant's side.",
    "Ant #04": "Retells Savage Dragon #216 from Ant's side.",
    "Ant #05": "Retells Spawn #266 from Ant's side.",
    "Ant #06": "Retells Savage Dragon #217 from Ant's side.",
    "Spawn #296, The History of Al Simmons, Part 1": "A clean jumping-on point.",
    "Gunslinger Spawn #01, Lost in the Future, Part 1":
        "Straight after Spawn's Universe.",
    "King Spawn #03, King of Swords, Part 3": "After Spawn #321.",
    "Gunslinger Spawn #10, The Two Faces of Revenge, Part 4":
        "Leads straight into The Scorched #1.",
    "Spawn #328, Bad Business, Part 5": "Two weeks after King Spawn #2.",
    "Spawn #337, Sinn’s War, Part 7": "After Batman Spawn.",
    "King Spawn #15": "After Gunslinger Spawn #7–9.",
    "Spawn #343, Battle for the Throne I, Part 6":
        "Before Gunslinger Spawn #21–23.",
    "The Scorched #14": "After Spawn #337.",
    "Spawn #344, Battle for the Throne II, Part 1":
        "After Gunslinger Spawn #21–23.",
    "Spawn #347, Battle for the Throne II, Part 4": "Leads into King Spawn #27.",
    "King Spawn #25": "After Spawn #343.",
    "Spawn #348, Battle for the Throne II, Part 5": "During King Spawn #30.",
    "Spawn #349, Battle for the Throne II, Part 6": "After King Spawn #30.",
    "King Spawn #31": "Nearly a month after Spawn #350.",
    "Gunslinger Spawn #29": "Weeks after Spawn #350, and after King Spawn #31.",
    "Spawn #351": "Two months after Spawn #350.",
    "The Scorched #27": "A few months after Spawn #350.",
    "Misery #1": "After King Spawn #34 and #35.",
    "Misery #2": "After King Spawn #34 and #35.",
    "Rat City #1": "Opens in 2107, set in 2111. Crosses over after Spawn #301.",
}

# The frontier the document marks with "(Most Recent Issue)". Asserted, because
# it is the one thing in the document that three different passages disagree
# about: the collections list still says Spawn is at #364, King Spawn at #45,
# Gunslinger at #42 and The Scorched at #40, while the reading order enumerates
# well past all four. The enumeration wins; this assert makes a desync loud.
EXPECTED_FRONTIER = {
    "Spawn": 365,
    "King Spawn": 46,
    "Gunslinger Spawn": 43,
    "The Scorched": 42,
}

# Enumerated totals, so a re-parse that silently loses rows fails here. 835
# issue rows across the two tables, less the duplicated hinge and the five
# announced-project ranges.
EXPECTED_ROWS = 829
# 195 arc groups across the two tables, less the hinge's own group, the five
# announced-project groups, and the two runs of blank spacer rows.
EXPECTED_SECTIONS = 187
EXPECTED_SERIES_MAX = {
    "Spawn": 375, "King Spawn": 54, "Gunslinger Spawn": 54,
    "The Scorched": 56, "Curse of the Spawn": 29, "Haunt": 28,
    "Spawn, The Dark Ages": 28, "Sam and Twitch": 26,
    "Case Files, Sam and Twitch": 25, "Rat City": 18, "Hellspawn": 16,
}


# ---------------------------------------------------------------------------
def cells(tr):
    """One table row, as [{text, background, rowspan, colspan}]."""
    out = []
    for m in re.finditer(r"<td([^>]*)>(.*?)</td>", tr, re.S):
        attrs, inner = m.group(1), m.group(2)
        txt = re.sub(r"<[^>]+>", "", inner)
        txt = html.unescape(txt).replace("\xa0", " ")
        bg = re.search(r"background-color:(#[0-9a-fA-F]{6})", attrs)
        rs = re.search(r'rowspan="(\d+)"', attrs)
        cs = re.search(r'colspan="(\d+)"', attrs)
        out.append({"t": re.sub(r"\s+", " ", txt).strip(),
                    "bg": (bg.group(1) if bg else "").lower(),
                    "rowspan": int(rs.group(1)) if rs else 1,
                    "colspan": int(cs.group(1)) if cs else 1})
    return out


def read_doc():
    """The two reading-order tables, as flat rows in document order.

    Prefers the distilled extract, so a fresh clone can regenerate the property
    without refetching. When the full page is cached alongside it the page wins
    and the extract is refreshed from it, which is also how a desync between
    the two gets noticed.
    """
    if CACHE.exists():
        order = parse_doc()
        EXTRACT.parent.mkdir(parents=True, exist_ok=True)
        with EXTRACT.open("w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(order, indent=1, ensure_ascii=False) + "\n")
        return order
    assert EXTRACT.exists(), (
        "neither %s nor %s is present. The Google Doc is the whole source; "
        "refetch it with a browser User-Agent rather than substituting any "
        "other reading order." % (EXTRACT.name, CACHE.name))
    return json.loads(EXTRACT.read_text(encoding="utf-8"))


def parse_doc():
    """Walk the cached page's tables into flat rows."""
    body = CACHE.read_text(encoding="utf-8")
    body = body[body.find("<body"):]
    body = re.sub(r"<script.*?</script>", "", body, flags=re.S)
    tables = re.findall(r"<table.*?</table>", body, re.S)
    assert len(tables) == 5, "expected 5 tables in the document, saw %d" % len(tables)

    rows, order = [], []
    for ti, t in enumerate(tables):
        for tr in re.findall(r"<tr.*?</tr>", t, re.S):
            rows.append((ti, cells(tr)))

    # Rebuild the grid. The arc cell is held over by rowspan, so a row inside an
    # arc has two cells (issue, note) and the row that opens one has three.
    carry, arc = 0, None
    for ti, c in rows:
        if ti not in (0, 1) or not c:
            if ti not in (0, 1):
                continue
            carry = 0
            continue
        if len(c) == 1 and c[0]["colspan"] == 3:       # banner spanning the table
            carry = 0
            continue
        if carry:
            carry -= 1
            issue, note = c[0], (c + [{"t": ""}])[1]
        else:
            if len(c) < 2:
                continue
            arc, carry = c[0]["t"], c[0]["rowspan"] - 1
            issue, note = c[1], (c + [{"t": ""}] * 2)[2]
        if issue["t"] in ("", "ISSUE"):                 # header and spacer rows
            continue
        # Only whether a row is annotated is kept, not what the annotation
        # said: NOTE_REWRITES is keyed by issue and supplies the house wording,
        # so the flag is all the exhaustiveness check needs.
        order.append({"table": ti, "arc": arc, "issue": issue["t"],
                      "note": bool(note["t"]),
                      "bg": issue["bg"] or c[0]["bg"]})
    return order


ISSUE = re.compile(r"^(?P<series>.+?) #(?P<num>\d+(?:\.\d+)?)(?:, (?P<title>.*))?$")


def parse_issue(text, arc):
    """(series, issue label, story title, aside). One-shots have no number."""
    core = FRONTIER.sub("", text)
    m = ISSUE.match(core)
    if not m:
        aka = AKA.search(core)
        return (ONESHOT_TAIL.sub("", AKA.sub("", core)).strip(), "", "",
                "Also published as %s" % aka.group(1) if aka else "")
    series, num, title = m.group("series"), m.group("num"), m.group("title") or ""
    if series == "Violator":
        series = "Violator (1994)" if arc == VIOLATOR_1994 else "Violator (2024)"
    return series, "#" + num.lstrip("0").rjust(1, "0"), title, ""


def strip_arc(title, arc):
    """Drop a story title that only repeats the section header it sits under."""
    if not title:
        return ""
    bare = re.sub(r",? Part \d+$", "", title).strip()
    if prop.normt(bare) == prop.normt(re.sub(r",? Part \d+$", "", arc).strip()):
        return ""
    return title


def rng(nums):
    """"#1–#6" for a contiguous block, "#1, #4, #9" otherwise."""
    vals = [n for n in nums if n]
    if not vals:
        return ""
    if len(vals) == 1:
        return vals[0]
    try:
        ints = [int(v.lstrip("#")) for v in vals]
    except ValueError:
        return "%s–%s" % (vals[0], vals[-1].lstrip("#"))
    if ints == list(range(ints[0], ints[0] + len(ints))):
        return "%s–%s" % (vals[0], ints[-1])
    return ", ".join(vals)


def main():
    order = read_doc()

    # The Spawn's Universe one-shot closes the first table and opens the second.
    # One comic, one row: keep the copy that opens the Spawn's Universe order.
    seen_hinge = False
    trimmed = []
    for row in order:
        if row["issue"] == "Spawn's Universe (One-Shot)":
            if row["table"] == 0:
                seen_hinge = True
                continue
        trimmed.append(row)
    assert seen_hinge, "the Spawn's Universe hinge row is no longer duplicated"

    # The Spawn's Universe table ends with announced series given as ranges
    # rather than issues — the same block the ANNOUNCED PROJECTS table repeats.
    # Nothing in it has been published, and a range is not an issue.
    announced = re.compile(r"#\d+\s*-\s*(\d+|ongoing)", re.I)
    dropped_ranges = [r["issue"] for r in trimmed if announced.search(r["issue"])]
    assert len(dropped_ranges) == 5, \
        "expected 5 announced-project ranges, saw %s" % dropped_ranges
    rows = [r for r in trimmed if not announced.search(r["issue"])]

    assert len(rows) == EXPECTED_ROWS, \
        "the document now enumerates %d issues, not %d" % (len(rows), EXPECTED_ROWS)

    # Every annotation in the source must have been looked at by a human.
    annotated = {r["issue"] for r in rows if r["note"]}
    unknown = annotated - set(NOTE_REWRITES)
    assert not unknown, \
        "the document has new annotations with no house rewrite: %s" % sorted(unknown)[:4]
    stale = set(NOTE_REWRITES) - annotated
    assert not stale, "NOTE_REWRITES has entries the document dropped: %s" % sorted(stale)[:4]

    # The publication frontier, as the document marks it.
    frontier = {}
    for r in rows:
        if FRONTIER.search(r["issue"]):
            series, num = parse_issue(r["issue"], r["arc"])[:2]
            frontier[series] = int(num.lstrip("#"))
    assert frontier == EXPECTED_FRONTIER, \
        "the '(Most Recent Issue)' markers moved: %s" % frontier

    sections, ids, series_max = [], {}, collections.defaultdict(int)
    tags_seen = set()
    for row in rows:
        arc = row["arc"]
        if not sections or sections[-1]["_arc"] != arc or \
                sections[-1]["_table"] != row["table"]:
            sections.append({"_arc": arc, "_table": row["table"], "items": [],
                             "_series": []})
        sec = sections[-1]

        series, num, title, aside = parse_issue(row["issue"], arc)
        tag = LEGEND.get(row["bg"])
        assert tag, "unmapped legend colour %r on %r" % (row["bg"], row["issue"])
        tags_seen.add(tag)
        if num:
            series_max[series] = max(series_max[series], int(float(num.lstrip("#"))))

        note = NOTE_REWRITES.get(row["issue"]) if row["note"] else None
        if FRONTIER.search(row["issue"]):
            note = prop.join_bits(note, "The latest issue published.")
        item = {"id": "spawn-" + prop.slug("%s %s" % (series, num or title)),
                "t": series, "n": num}
        body = prop.join_bits(strip_arc(title, arc), aside, note)
        if body:
            item["note"] = body
        item["tags"] = [tag]
        if tag == "Optional":
            item["opt"] = 1
        assert item["id"] not in ids, \
            "%r and %r collide on id %s" % (row["issue"], ids.get(item["id"]), item["id"])
        ids[item["id"]] = row["issue"]
        sec["items"].append(item)
        if not sec["_series"] or sec["_series"][-1][0] != series:
            sec["_series"].append((series, []))
        sec["_series"][-1][1].append(num)

    assert len(sections) == EXPECTED_SECTIONS, \
        "the document now divides into %d arcs, not %d" % (len(sections), EXPECTED_SECTIONS)
    for name, top in EXPECTED_SERIES_MAX.items():
        assert series_max[name] == top, \
            "%s now runs to #%s, not #%s" % (name, series_max[name], top)

    out = []
    for i, sec in enumerate(sections, 1):
        arc = sec["_arc"]
        title = ARC_TITLE.get(arc, arc)
        if title == "One-Shot" and len(sec["items"]) == 1:
            title = sec["items"][0]["t"]
        bits = " · ".join("%s %s" % (s, rng(ns)) if ns[0] else s
                          for s, ns in sec["_series"])
        optional = all(x.get("opt") for x in sec["items"])
        out.append({"id": "arc%03d-%s" % (i, prop.slug(title)),
                    "tier": 2 if optional else 1,
                    "title": title,
                    "sub": bits,
                    "items": sec["items"]})

    p = {
        "slug": SLUG,
        "title": "Spawn",
        "subtitle": "Blake Whitlow's reading order",
        "kind": "comics",
        "popularity": 61,
        # The source dates its first row itself: "Year is 1992."
        "year": "1992–",
        "blurb": "%d issues of Spawn and its spin-offs, in the order they are "
                 "meant to be read rather than the order they came out."
                 % len(ids),
        "unit": {"one": "issue", "many": "issues"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": "#4412A6",
        "accentDark": "#9B7BEE",
        "tiers": True,
        "paceTiers": [1],
        "paceLabel": "the arcs the source marks non-essential",
        "filter": {"key": "line", "label": "Show", "mode": "exclude",
                   "values": sorted(tags_seen)},
        "notes": [
            ["This is not chronological order.",
             "The source says so twice in its own preamble, and it matters: the "
             "issues that come first chronologically give away the series' "
             "biggest turns, and much of the terminology only lands once the "
             "main book has introduced it. This is the order that reads best "
             "cold, which is a different thing and a much more useful one."],
            ["Four kinds of row.",
             "The source colour-codes every issue and the filter carries that "
             "over: the main Spawn book, the spin-off series it treats as "
             "essential, the one-shots, and the spin-offs it marks "
             "non-essential. Hiding the last of those leaves a spine you can "
             "read straight through."],
            ["Sections are its arcs, not ours.",
             "The arc column of the source is reproduced exactly, down to the "
             "arcs that are one issue long. Where it interleaves a mini-series "
             "into the middle of a main-book arc, so does this."],
            ["No spoilers.",
             "A note says what an issue is and where it sits — which series it "
             "crosses over with, how much time has passed, whether the source "
             "doubts its placement. Never what happens in it. The source's own "
             "annotations are rewritten to that rule rather than copied."],
            ["It runs past what is published.",
             "The source keeps its grid filled in ahead of the solicitations, "
             "so the last stretch of each ongoing is issues that do not exist "
             "yet. The last published issue of each is marked."],
            ["What is left out.",
             "The source's appendices: the announced series with no issues out "
             "yet, the cover-date calendar, and the miscellany of toy comics, "
             "parodies and cancelled projects it files outside the order and "
             "marks non-canon. The reading order itself is here whole."],
            "Order, arc divisions and placement notes from Blake Whitlow's "
            "Spawn Reading Order / Chronology, kept updated since 2012; the "
            "annotations are rewritten from it rather than copied.",
        ],
        "sections": out,
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

    path = prop.write(p)
    print("%s: %d issues in %d arcs" % (path.name, len(ids), len(out)))
    print("   lines: %s" % ", ".join(
        "%s %d" % (t, sum(1 for s in out for x in s["items"] if x["tags"] == [t]))
        for t in sorted(tags_seen)))
    for name in sorted(EXPECTED_FRONTIER):
        print("   %-18s enumerated to #%-4s published to #%s"
              % (name, series_max[name], EXPECTED_FRONTIER[name]))


if __name__ == "__main__":
    main()
