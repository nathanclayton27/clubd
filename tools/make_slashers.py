#!/usr/bin/env python3
"""Generate properties/slashers.json.

    PYTHONIOENCODING=utf-8 python tools/make_slashers.py

The three founding masked-killer franchises in one list: Halloween, Friday
the 13th and A Nightmare on Elm Street, plus the one film that belongs to two
of them. Every row is a released theatrical feature taken from its
franchise's own Films table on Wikipedia, weighted by the runtime that film's
own article infobox states.

WHY RELEASE ORDER, AND WHY THIS LIST HAS TO SAY SO
--------------------------------------------------
These franchises do not share one timeline, and Halloween does not even share
one with itself. Wikipedia's Halloween article carries a story-chronology box
listing FIVE mutually exclusive continuities; this generator reads that box
rather than trusting anyone's memory of it, and asserts the three facts the
list's intro claims:

  * the 1978 film opens three of the five;
  * Halloween 4 (1988) and Halloween H20 (1998) are each written as the
    sequel to Halloween II (1981), in different continuities;
  * Halloween II (1981) and Halloween (2018) are each written as the sequel
    to Halloween (1978).

So no chronological order exists that can hold all thirteen films, and any
list that silently picked one would be picking a side. This one picks U.S.
release order — the single order nobody disputes, and the order audiences
actually met the films in, each sequel having been made in answer to the one
before. The continuities are explained in the section intros and flagged
factually on the rows that start or end one; they are never imposed as
sequence. Sections are ordered the same way, by the year each franchise
began: Halloween (1978), Friday the 13th (1980), Elm Street (1984).

WHICH FRANCHISES, AND WHY NOT SCREAM OR CHILD'S PLAY
----------------------------------------------------
The brief was "long franchise with a tangled continuity", and both candidates
were collected so the call could rest on data rather than impression:

  * Scream — seven released films across thirty years, so long enough, but
    its article carries no chronology box and its Films table carries no
    continuity blocks, because there is nothing to divide: one unbroken
    timeline, no remake, no reboot. The problem this list exists to rule on
    never arises, and a section whose intro said "watch them in order" would
    be dead weight next to Halloween's five timelines.
  * Child's Play — eight released films, and its own Films table splits them
    into exactly two labelled blocks, "Original series" and "Reboot", which
    never intersect. That is a clean fork, not a tangle; and the original
    line's story continues in the Chucky television series, which a films
    list cannot hold without misrepresenting where the story goes.

FREDDY VS. JASON
----------------
It appears in the Films table of BOTH the Nightmare and the Friday articles —
the eighth film of one and the eleventh of the other — and the generator
asserts the two tables agree on its title, date and runtime. It gets ONE row,
in a section of its own, so a single viewing ticks a single row. Filing it
inside either franchise would have made it look missing from the other.

WEIGHTS
-------
Every row carries `w`, hours from the runtime in that film's own Wikipedia
infobox. This is all-or-nothing on purpose: downstream, a row with no `w`
counts as one hour, so a single missing runtime would quietly invent time.
The build asserts all 33 runtimes were parsed rather than defaulted, and a
film whose infobox stated none would fail here instead of shipping a guess.

Data: scratch/slashers/collect.py -> scratch/slashers/slashers_data.json
(prefetch.py warms the wikitext cache in batches first).
"""
import json
import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop
from gwlib.prop import slug, normt

SLUG = "slashers"
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "scratch" / "slashers" / "slashers_data.json"

ACCENT, ACCENT_DARK = "#5A0F1E", "#FF8C86"

WIKI = "https://en.wikipedia.org/wiki/"

# The one film in two franchises. Named once, here, and matched on the label
# both tables print.
CROSSOVER = "Freddy vs. Jason"

# Row notes. Terse, factual, spoiler-free, and only where a row carries
# information about where it sits in the tangle — the rest stay bare rather
# than padded. Keyed by (franchise, label).
NOTES = {
    ("halloween", "Halloween", 1978):
        "The original. Three of the five continuities start here.",
    ("halloween", "Halloween II", 1981):
        "Carries straight on from the first film. Two later films are each "
        "written as its sequel.",
    ("halloween", "Halloween III: Season of the Witch", 1982):
        "No Michael Myers — the one attempt to turn the series into an "
        "anthology.",
    ("halloween", "Halloween 4: The Return of Michael Myers", 1988):
        "Picks up from Halloween II, setting the anthology film aside.",
    ("halloween", "Halloween 5: The Revenge of Michael Myers", 1989):
        "Follows on from Halloween 4.",
    ("halloween", "Halloween: The Curse of Michael Myers", 1995):
        "Six years after Halloween 5, and the end of the original continuity.",
    ("halloween", "Halloween H20: 20 Years Later", 1998):
        "The second film written to follow Halloween II — this one sets 4, 5 "
        "and 6 aside instead.",
    ("halloween", "Halloween: Resurrection", 2002):
        "Three years after H20, and the end of that continuity.",
    ("halloween", "Halloween", 2007):
        "Rob Zombie's remake, and a continuity of its own.",
    ("halloween", "Halloween II", 2009):
        "Sequel to the 2007 remake.",
    ("halloween", "Halloween", 2018):
        "The other film written as the sequel to 1978, setting every film in "
        "between aside.",
    ("halloween", "Halloween Kills", 2021):
        "Carries straight on from the 2018 film.",
    ("halloween", "Halloween Ends", 2022):
        "Four years later, and the end of the Blumhouse continuity.",
    ("friday", "Friday the 13th", 1980):
        "The original, at Camp Crystal Lake.",
    ("friday", "Jason Goes to Hell: The Final Friday", 1993):
        "Jason is back, resurrected without explanation.",
    ("friday", "Jason X", 2002):
        "Set in the far future, largely aboard a spacecraft. Widely released "
        "in 2002, after a single Spanish showing in November 2001.",
    ("friday", "Friday the 13th", 2009):
        "A reboot: restarts the series' continuity, and connects to none of "
        "the films above.",
    ("elm", "A Nightmare on Elm Street", 1984):
        "Wes Craven's original.",
    ("elm", "Freddy's Dead: The Final Nightmare", 1991):
        "The end of the original Freddy continuity.",
    ("elm", "Wes Craven's New Nightmare", 1994):
        "Steps outside the series' own fiction: Craven, Heather Langenkamp "
        "and Robert Englund appear as themselves.",
    ("elm", "A Nightmare on Elm Street", 2010):
        "A remake of the 1984 film, with a new Freddy and a continuity of its "
        "own.",
}


def load_json(path, tries=4):
    """Read a JSON file that another builder may be mid-write on."""
    for n in range(tries):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            if n == tries - 1:
                raise
            time.sleep(0.4)


def released(films):
    """The rows of a Films table that name a film somebody has released."""
    return [f for f in films if f["released"]]


def check_source(d):
    """Everything the list asserts about its own sources, before it builds."""
    # --- the three franchises are the shape the intros describe -----------
    counts = {k: len(released(d[k]["films"])) for k in d}
    assert counts["halloween"] == 13, counts
    assert counts["friday"] == 12, counts
    assert counts["elm"] == 8 + 1, counts        # eight, plus the crossover
    # everything a table names but this list leaves out is genuinely unreleased
    for k, v in d.items():
        for f in v["films"]:
            assert f["released"] or not f["date"], (k, f["label"])
            assert f["released"] or re.search(r"untitled|\bTBA\b", f["label"],
                                              re.I), (k, f["label"])
        for a in v["announced"]:
            assert "TBA" in a["date_cell"], (k, a)
    # the Nightmare table's one bare "Untitled film" row, with no date at all
    assert [a["label"] for a in d["elm"]["announced"]] == ["Untitled film"], \
        d["elm"]["announced"]

    # --- every row is machine-read, and its year checks out ---------------
    for k in ("halloween", "friday", "elm"):
        for f in released(d[k]["films"]):
            assert f["runtime"], "no runtime parsed: %s" % f["label"]
            assert 60 <= f["runtime"] <= 200, (f["label"], f["runtime"])
            # one clean "N minutes", not a list of cuts to choose between
            assert re.fullmatch(r"\d+ minutes", f["runtime_field"]), \
                (f["label"], f["runtime_field"])
            # the franchise table's release year is one the film's own
            # infobox states — the guard against a near-identical title
            # (Halloween 1978 / 2007 / 2018) pulling the wrong runtime
            assert f["date"][0] in f["infobox_years"], \
                (f["label"], f["date"], f["infobox_years"])
        got = [f["date"] for f in released(d[k]["films"])]
        assert got == sorted(got), "%s table is not in release order" % k

    # --- the counts the section intros state, checked not remembered ------
    def upto(key, year):
        return sum(1 for f in released(d[key]["films"])
                   if f["label"] != CROSSOVER and f["date"][0] <= year)
    # Friday: ten films from Camp Crystal Lake to Jason X, then the reboot
    assert upto("friday", 2002) == 10, upto("friday", 2002)
    assert counts["friday"] - 1 - upto("friday", 2002) == 1
    # Elm Street: six in the original Freddy continuity, then New Nightmare
    # and the remake
    assert upto("elm", 1991) == 6, upto("elm", 1991)
    assert counts["elm"] - 1 - upto("elm", 1991) == 2

    # --- the crossover is one film, agreed on by two articles -------------
    pair = [f for k in ("friday", "elm") for f in d[k]["films"]
            if f["label"] == CROSSOVER]
    assert len(pair) == 2, pair
    assert pair[0]["date"] == pair[1]["date"] == [2003, 8, 15], pair
    assert pair[0]["runtime"] == pair[1]["runtime"], pair
    fr = [f["label"] for f in released(d["friday"]["films"])]
    el = [f["label"] for f in released(d["elm"]["films"])]
    assert fr.index(CROSSOVER) == 10 and el.index(CROSSOVER) == 7, \
        "the crossover moved in one of the tables"

    # --- the Halloween continuity claims, read from the article's own box --
    ch = d["halloween"]["chronology"]
    assert len(ch) == 5, sorted(ch)
    first = [(t, y) for v in ch.values() for t, y in [v[0]]]
    assert sum(1 for t, y in first if (t, y) == ("Halloween", 1978)) == 3, first
    def follows(title, year):
        """Films written as the next instalment after a given one."""
        out = []
        for v in ch.values():
            for i, (t, y) in enumerate(v[:-1]):
                if (t, y) == (title, year):
                    out.append(tuple(v[i + 1]))
        return sorted(set(out))
    after81 = follows("Halloween II", 1981)
    assert after81 == [("Halloween 4: The Return of Michael Myers", 1988),
                       ("Halloween H20: 20 Years Later", 1998)], after81
    after78 = follows("Halloween", 1978)
    assert after78 == [("Halloween", 2018), ("Halloween II", 1981)], after78

    # --- and the reasons the other two franchises are not here ------------
    scream = released(d["scream"]["films"])
    assert len(scream) == 7 and not d["scream"]["chronology"] \
        and not d["scream"]["groups"], (len(scream), d["scream"]["groups"])
    assert scream[0]["date"][0] == 1996 and scream[-1]["date"][0] == 2026
    chucky = released(d["chucky"]["films"])
    assert len(chucky) == 8, len(chucky)
    assert d["chucky"]["groups"] == ["Original series", "Reboot"], \
        d["chucky"]["groups"]
    assert not d["chucky"]["chronology"], d["chucky"]["chronology"]
    return counts


def accent_is_free():
    """No other property may share this list's accent pair (qa_lint rule)."""
    for f in sorted((ROOT / "properties").glob("*.json")):
        if f.name in ("index.json", "search.json", "%s.json" % SLUG):
            continue
        p = load_json(f)
        assert (p.get("accent"), p.get("accentDark")) != (ACCENT, ACCENT_DARK), \
            "accent pair already used by %s" % f.stem


def sync_partners(rows):
    """Rows on other lists that will tick together with rows on this one.

    build.py groups film rows across lists on normalized title + year — with
    a fallback to a single year found in the note, which is how Criterion's
    spine-numbered rows join in — so this reproduces that key rather than
    guessing at it. Every overlap is found and returned, keyed by this list's
    row id, each mapping to sorted (slug, id, title) triples; the notes are
    built from exactly this, so they name every shared film and every list it
    sits on as the catalogue stands today. Other lists are added all the
    time, so a later run can find more than the committed notes say — that
    is drift, and a fresh run is the fix. The one fixed expectation is that
    the John Carpenter list carries Halloween (1978).
    """
    want = {"%s|%s" % (normt(x["t"]), x["n"]): x["id"] for x in rows}
    out = {}
    for f in sorted((ROOT / "properties").glob("*.json")):
        if f.name in ("index.json", "search.json", "%s.json" % SLUG):
            continue
        p = load_json(f)
        if "film" not in (p.get("kind") or "") or p.get("secret"):
            continue
        for s in p.get("sections", []):
            for x in s.get("items", []):
                n = str(x.get("n", ""))
                if re.fullmatch(r"(18|19|20)\d{2}", n):
                    year = n
                else:
                    found = set(re.findall(r"\b((?:18|19|20)\d{2})\b",
                                           x.get("note") or ""))
                    year = found.pop() if len(found) == 1 else None
                key = "%s|%s" % (normt(x.get("t", "")), year)
                if year and key in want:
                    out.setdefault(want[key], []).append(
                        (p["slug"], x["id"], p["title"]))
    got = out.get("sl-1978-halloween", [])
    assert any(s == "carpenter" for s, _, _ in got), \
        "the John Carpenter list no longer carries Halloween (1978): %s" % got
    return {k: sorted(v) for k, v in out.items()}


def main():
    d = load_json(DATA)
    counts = check_source(d)
    accent_is_free()

    def row(key, f):
        year = f["date"][0]
        it = {"id": "sl-%d-%s" % (year, slug(f["label"])),
              "t": f["label"], "n": str(year),
              "w": round(f["runtime"] / 60.0, 2)}
        note = NOTES.get((key, f["label"], year))
        if note:
            it["note"] = note
        return it

    def section(key, sid, title, intro, page, extra=""):
        got = [f for f in released(d[key]["films"])
               if f["label"] != CROSSOVER]
        items = [row(key, f) for f in got]
        mins = sum(f["runtime"] for f in got)
        sub = "%d–%d · %d films · %d hours" % (
            got[0]["date"][0], got[-1]["date"][0], len(got), round(mins / 60.0))
        return {"id": sid, "title": title, "sub": sub + extra, "intro": intro,
                "links": [{"label": "The filmography", "url": WIKI + page}],
                "items": items}, mins

    ch = d["halloween"]["chronology"]
    names = [n.replace(" continuity", "") for n in ch]
    halloween, h_min = section(
        "halloween", "halloween", "Halloween",
        "Thirteen films and five continuities. The article's own story "
        "chronology divides them into %s and %s — and they overlap: the 1978 "
        "film opens three of the five, Halloween II (1981) is followed by "
        "Halloween 4 in one continuity and by H20 in another, and 1978 itself "
        "is followed by both Halloween II and the 2018 film. Nothing "
        "reconciles them, so the rows run in release order and each one says "
        "where it picks up." % (", ".join(names[:-1]), names[-1]),
        "Halloween_(franchise)")

    friday, f_min = section(
        "friday", "friday", "Friday the 13th",
        "Eleven films here, and a twelfth in the crossover section below. Ten "
        "of them run as one line from Camp Crystal Lake in 1980 out to a "
        "spacecraft in Jason X, a line the films patch as they go — their "
        "killer comes back twice without the films explaining how — and then "
        "the 2009 film restarts the continuity from scratch.",
        "Friday_the_13th_(franchise)", " · plus the crossover below")

    elm, e_min = section(
        "elm", "elm", "A Nightmare on Elm Street",
        "Eight films here, and a ninth in the crossover section below. Six "
        "are a single Freddy continuity, 1984 to 1991. New Nightmare then "
        "steps outside the series' own fiction rather than continuing it, and "
        "the 2010 film is a remake that starts the story over.",
        "A_Nightmare_on_Elm_Street_(franchise)", " · plus the crossover below")

    fvj = next(f for f in d["friday"]["films"] if f["label"] == CROSSOVER)
    cross = {
        "id": "crossover", "title": "Freddy vs. Jason",
        "sub": "2003 · one film · %d hours · counted once, ticks for both"
               % round(fvj["runtime"] / 60.0),
        "intro": "One film belonging to two series: it is the eighth Nightmare "
                 "on Elm Street film and the eleventh Friday the 13th film, "
                 "and both franchise articles list it in their own "
                 "filmographies. It sits here rather than inside either "
                 "section, with one row rather than two, so a single viewing "
                 "ticks once — and so it never looks missing from the other "
                 "franchise.",
        "items": [row("cross", fvj)],
    }

    sections = [halloween, friday, elm, cross]
    halloween["open"] = True

    # ---- the checks the shipped file has to pass -------------------------
    rows = [x for s in sections for x in s["items"]]
    assert len(rows) == 33, len(rows)
    assert len(rows) == counts["halloween"] + counts["friday"] \
        + counts["elm"] - 1, len(rows)
    ids = [x["id"] for x in rows]
    assert len(ids) == len(set(ids)), \
        sorted({i for i in ids if ids.count(i) > 1})
    assert sum(1 for x in rows if x["t"] == CROSSOVER) == 1
    for s in sections:
        years = [int(x["n"]) for x in s["items"]]
        assert years == sorted(years), "%s is out of release order" % s["title"]
    # all-or-nothing weighting: one bare row would silently cost an hour
    assert all(isinstance(x.get("w"), float) and x["w"] > 0 for x in rows), \
        [x["id"] for x in rows if not x.get("w")]
    # sections are ordered by the year each franchise began
    starts = [int(s["items"][0]["n"]) for s in sections[:3]]
    assert starts == [1978, 1980, 1984] == sorted(starts), starts

    mins = h_min + f_min + e_min + fvj["runtime"]
    assert mins == sum(f["runtime"] for k in ("halloween", "friday", "elm")
                       for f in released(d[k]["films"])) - fvj["runtime"], mins
    hours = round(sum(x["w"] for x in rows), 2)
    assert abs(hours - mins / 60.0) < 0.2, (hours, mins / 60.0)
    partners = sync_partners(rows)

    def span(key):
        got = released(d[key]["films"])
        return "from %d to %d" % (got[0]["date"][0], got[-1]["date"][0])

    def joined(names):
        return (" and ".join(names) if len(names) < 3
                else ", ".join(names[:-1]) + " and " + names[-1])

    # one entry per shared film, in row order: the film as the notes name it,
    # and every list it also sits on (a list carrying it twice is named once)
    shared = []
    for x in rows:
        if x["id"] in partners:
            titles = []
            for _, _, t in partners[x["id"]]:
                if t not in titles:
                    titles.append(t)
            shared.append(("%s (%s)" % (x["t"], x["n"]), titles))
    assert shared, "no shared film, so the overlap notes have nothing to say"
    overlap_notes = [
        ["%s is shared with %s."
         % (film, "another list" if len(titles) == 1 else "other lists"),
         "It also sits on %s, and ticking it in any one of those places "
         "ticks it in all of them." % joined(titles)]
        for film, titles in shared]
    # every overlap was computed above, so this is checked, not assumed
    overlap_notes[-1][1] += " Nothing else on this list overlaps the catalogue."
    p = {
        "slug": SLUG,
        "title": "Slashers",
        "subtitle": "Halloween, Friday the 13th and Elm Street, in release order",
        "kind": "films",
        "popularity": 60,
        "year": "1978–2022",
        "blurb": "Michael, Jason and Freddy — three franchises whose timelines "
                 "contradict each other, in the one order nobody disputes. "
                 "About %d hours." % round(hours),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ["Release order, and why it had to be.",
             "Halloween alone carries five mutually exclusive continuities in "
             "its own article's story chronology: the 1978 film opens three "
             "of them, Halloween 4 and Halloween H20 are each written as the "
             "sequel to Halloween II (1981), and Halloween II and the 2018 "
             "film are each written as the sequel to 1978. No single timeline "
             "holds all thirteen, so this list does not pretend one does. "
             "Every section runs in U.S. release order — the one order nobody "
             "disputes, and the order audiences met these films in, each "
             "sequel made in answer to the one before. The continuities are "
             "explained in the section intros and flagged on the rows that "
             "start or end one; they are never imposed as sequence."],
            ["Why these three franchises.",
             "The long masked-killer series that built the slasher decade and "
             "outlasted it — Michael %s, Jason %s, Freddy %s — each carrying "
             "more than one continuity, and two of them sharing a crossover. "
             "Scream is not here: seven films across thirty years, "
             % (span("halloween"), span("friday"), span("elm")) +
             "but one unbroken timeline with no remake and no reboot, so the "
             "ordering problem this list exists to settle never comes up. "
             "Child's Play is not here either: its own filmography splits "
             "cleanly into an original run and a 2019 remake that never "
             "touch, and the original story then continues in a television "
             "series that a films list cannot hold."],
            ["Freddy vs. Jason gets its own section.",
             "It is the eighth Nightmare on Elm Street film and the eleventh "
             "Friday the 13th film, and it appears once, so one viewing ticks "
             "one row. Filing it inside either franchise would have left it "
             "looking missing from the other."],
            ["Bar widths are runtimes.",
             "Every row carries the runtime stated in that film's own "
             "Wikipedia infobox, checked against the release year the "
             "franchise table gives — %d hours in all. These franchises reuse "
             "their titles across decades, so a year is what tells Halloween "
             "1978 from 2007 and 2018, and a row whose runtime could not be "
             "read would fail the build rather than ship as a guess."
             % round(hours)],
            *overlap_notes,
            ["Not included.",
             "The untitled Nightmare on Elm Street film in that franchise's "
             "table has no release date and no runtime, so it is not a row "
             "yet; every other film the three tables name is here. Neither "
             "the television series, the video games, the novels nor the "
             "comics are in scope."],
            "Titles, U.S. release dates and film order from the Films tables "
            "of Wikipedia's Halloween, Friday the 13th and A Nightmare on Elm "
            "Street franchise articles; the five Halloween continuities from "
            "that article's own story-chronology box; runtimes from each "
            "film's own article infobox.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d rows, %.2f hours (%d minutes)"
          % (out.name, len(rows), hours, mins))
    for s in sections:
        print("   %-26s %2d  %s" % (s["title"][:26], len(s["items"]), s["sub"]))
    for film, titles in shared:
        print("   %s sync partners: %s" % (film, joined(titles)))


if __name__ == "__main__":
    main()
