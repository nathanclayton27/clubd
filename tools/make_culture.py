#!/usr/bin/env python3
"""Generate properties/culture.json — Iain M. Banks's Culture books.

    python tools/make_culture.py

Ten books, 1987 to 2012, in publication order. The order is the source's own:
Wikipedia's Culture series article lists the books "ordered by publication
date" and this page keeps that, because there is nothing else to keep — the
article's opening paragraph says each novel is a self-contained story with new
characters, so there is no chronology to get wrong and no reading order to
argue about. What publication order buys you is the backward references
landing the right way round.

Nothing is typed from memory. Every title, year and the count itself are read
out of the wikitext cached under scratch/culture/, and the page is read THREE
times over so the years are corroborated rather than trusted:

  the infobox `books` plainlist    the ten titles, with years, in order
  the `number_of_books` field     the series' stated size
  the Books in the series table   the same ten as {{Book list}} blocks, with
                                  their own publish_date and a summary that
                                  classifies each row
  the Primary sources bibliography  a third, independent year per title

Those three year sources agree on nine of the ten rows and disagree on one:
THE STATE OF THE ART is 1991 in the infobox and the bibliography and 1989 in
the table. The generator detects that mechanically rather than papering over
it — it asserts that there is exactly one disagreement, that the two
independent sources are the ones that agree, and it ships their year with a
note saying the page contradicts itself. Both of the source's own lists put
the row fourth regardless, so only the printed year is in question, never the
position.

The State of the Art is also the one row that is not a novel: the article says
"nine novels and one short story collection" and the row's own summary opens
"A short story collection." It is a full row, not an optional one, because the
source counts it among the ten — and it carries a note saying what it is. The
classification is read from the summary, not assumed.

Sections are the two long gaps in Banks's publication run, found by splitting
wherever consecutive years are five or more apart: 1987-1991, 1996-2000,
2008-2012. Nothing editorial decides the boundaries.

NO WEIGHTS. Not one row carries `w`, on purpose: the reader-side weight rule
is `WEIGHT = x.w >= 0 ? x.w : 1`, so a single weighted row would silently
redefine every unweighted row as one hour. Page counts differ by edition and a
page is not an hour, so this page counts books and says so in the notes.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki  # noqa: E402

SLUG = "culture"
ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "scratch" / "culture"
PAGE = "Culture series"

WORDNUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
           "seven": 7, "eight": 8, "nine": 9, "ten": 10}
SPELLED = {v: k for k, v in WORDNUM.items()}

# `''[[Page|Label]]'' (1987)` — italic wikilink plus year. Short stories in
# these lists are quoted rather than italicised, so this never picks one up.
BOOK_YEAR = re.compile(r"''\[\[([^\]|]+)(?:\|([^\]]+))?\]\]''\s*\((\d{4})\)")
BOOK = re.compile(r"''\[\[([^\]|]+)(?:\|([^\]]+))?\]\]''")

# The two long silences in the run. Five years is the smaller of them; the
# next-largest ordinary interval is two, so the threshold is not a close call.
GAP = 5

ACCENT, ACCENT_DARK = "#3A2E6B", "#8FD9E8"


def linked(m):
    """Display title of a match: the pipe label when there is one."""
    return (m.group(2) or m.group(1)).strip()


# ---------------------------------------------------------------- sources

def infobox_books(text):
    """(title, year) for each book in the infobox plainlist, in its order."""
    m = re.search(r"\|\s*books\s*=\s*\{\{plainlist\|(.*?)\n\}\}", text,
                  re.S | re.I)
    assert m, "Culture infobox book list not found"
    out = []
    for line in m.group(1).strip().split("\n"):
        line = line.strip()
        if not line.startswith("*"):
            continue
        b = BOOK_YEAR.search(line)
        assert b, "infobox book line did not parse: %r" % line[:70]
        out.append((linked(b), int(b.group(3))))
    return out


def infobox_facts(text):
    """The series' stated size and its stated publication span."""
    n = re.search(r"\|\s*number_of_books\s*=\s*(\d+)", text)
    span = re.search(r"\|\s*pub_date\s*=\s*(\d{4})\s*[-–—]\s*(\d{4})",
                     text)
    assert n and span, "infobox number_of_books / pub_date did not parse"
    return int(n.group(1)), (int(span.group(1)), int(span.group(2)))


def stated_split(text):
    """The article's own count of what the series is made of."""
    m = re.search(r"comprises (\w+) novels and (\w+) short story collection",
                  text)
    assert m, "the 'nine novels and one short story collection' line moved"
    return WORDNUM[m.group(1).lower()], WORDNUM[m.group(2).lower()]


def table_books(text):
    """The Books in the series table as (title, publish_date, summary), in the
    table's order. One {{Book list}} block per row."""
    out = []
    for m in re.finditer(r"\{\{Book list\|List of Culture series\s*(.*?)\n\}\}",
                         text, re.S):
        block = "\n" + m.group(1)

        def field(name):
            fm = re.search(r"\|\s*%s\s*=\s*(.*?)(?=\n\s*\|\s*\w+\s*=|\Z)"
                           % name, block, re.S)
            return fm.group(1).strip() if fm else ""

        t = BOOK.search(field("title"))
        y = re.match(r"(\d{4})", field("publish_date"))
        assert t and y, "table row did not parse: %r" % block[:80]
        out.append((linked(t), int(y.group(1)), field("short_summary")))
    return out


def bibliography_years(text):
    """A third year per title: the Primary sources cite-book bullets."""
    seg = text.split("===Primary sources===")[1].split("===Secondary")[0]
    out = {}
    for line in seg.strip().split("\n"):
        if "cite book" not in line:
            continue
        t = re.search(r"\|\s*title\s*=\s*(.*?)\s*\|", line)
        y = re.search(r"\|\s*year\s*=\s*(\d{4})", line)
        assert t and y, "bibliography bullet did not parse: %r" % line[:70]
        out[t.group(1).strip()] = int(y.group(1))
    return out


# ---------------------------------------------------------------- assembly

def row(title, year, note=""):
    it = {"id": "cul-%d-%s" % (year, prop.slug(title)), "t": title,
          "n": str(year)}
    if note:
        it["note"] = note
    return it


def gap_groups(rows):
    """Split a year-ordered list wherever the run pauses for GAP years."""
    groups = [[rows[0]]]
    for prev, cur in zip(rows, rows[1:]):
        if int(cur["n"]) - int(prev["n"]) >= GAP:
            groups.append([])
        groups[-1].append(cur)
    return groups


def accent_is_free():
    """No other property may already own this accent pair (qa_lint rejects
    duplicates, and a shared pair makes two lists look like one)."""
    for f in sorted((ROOT / "properties").glob("*.json")):
        if f.stem in (SLUG, "index", "search"):
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        assert (d.get("accent"), d.get("accentDark")) != (ACCENT, ACCENT_DARK), \
            "accent pair already used by %s" % f.stem
    return True


def main():
    text = wiki.wikitext(PAGE, cache_dir=CACHE)
    assert text, "could not read %s" % PAGE

    ib = infobox_books(text)
    stated_books, (span_from, span_to) = infobox_facts(text)
    novels, collections = stated_split(text)
    tb = table_books(text)
    bib = bibliography_years(text)

    # --- the page's own totals have to agree with each other and with us
    assert len(ib) == len(tb) == stated_books == novels + collections == 10, \
        (len(ib), len(tb), stated_books, novels, collections)
    assert [t for t, _ in ib] == [t for t, _, _ in tb], \
        "infobox and table disagree on the order: %s vs %s" % (
            [t for t, _ in ib], [t for t, _, _ in tb])
    assert len(set(t for t, _ in ib)) == 10, "a title repeats"
    assert set(bib) == set(t for t, _ in ib), \
        "bibliography titles differ: %s" % sorted(set(bib) ^
                                                  {t for t, _ in ib})

    # --- three year sources, reconciled. The infobox and the bibliography are
    # independent of each other; where the table dissents we go with the two
    # and say so on the page. Exactly one such row is tolerated: a second one
    # means the article has been rewritten and a human should look.
    disputed = []
    for (t, y_ib), (_, y_tb, _) in zip(ib, tb):
        assert bib[t] == y_ib, \
            "infobox and bibliography disagree on %s: %d vs %d" % (t, y_ib,
                                                                   bib[t])
        if y_tb != y_ib:
            disputed.append((t, y_ib, y_tb))
    assert len(disputed) == 1 and disputed[0][0] == "The State of the Art", \
        "year disagreements changed: %s" % disputed
    d_title, d_keep, d_other = disputed[0]

    # --- which row is the collection, read off its own summary
    not_novel = [t for t, _, s in tb
                 if re.search(r"\bshort story collection\b", s, re.I)]
    assert not_novel == [d_title], \
        "the collection rows changed: %s" % not_novel

    # --- and which row the source itself hedges about
    hedged = [t for t, _, s in tb
              if re.search(r"not explicitly a Culture novel", s, re.I)]
    assert hedged == ["Inversions"], "the hedged rows changed: %s" % hedged

    notes = {
        d_title: prop.join_bits("Short story collection, not a novel",
                                "two of its stories are set in the Culture"),
        hedged[0]: "Not explicitly a Culture novel, says the source — which "
                   "files it here among the ten anyway",
    }

    rows = [row(t, y, notes.get(t, "")) for t, y in ib]
    years = [int(x["n"]) for x in rows]
    assert years == sorted(years), "publication order is not year-ordered: %s" \
        % years
    assert (years[0], years[-1]) == (span_from, span_to), \
        "rows span %s-%s, infobox says %s-%s" % (years[0], years[-1],
                                                 span_from, span_to)

    groups = gap_groups(rows)
    assert [len(g) for g in groups] == [4, 3, 3], \
        "the publication gaps moved: %s" % [[x["n"] for x in g]
                                            for g in groups]

    TITLES = ["The opening run", "The middle three", "The last three"]
    INTROS = [
        "Four books in five years, then Banks went quiet for five more. Each "
        "one is a self-contained story with its own cast, so nothing in here "
        "depends on having read the book above it.",
        "He came back to the Culture in 1996 and stayed for three. Still "
        "standalone, still no plot to fall behind on — the only thing "
        "publication order buys you is the backward references landing the "
        "right way round.",
        "Three more after eight years away, and the last Culture book he "
        "published. The gap in front of them is a gap, not a change of "
        "direction.",
    ]
    sections = []
    for n, (g, title, intro) in enumerate(zip(groups, TITLES, INTROS)):
        s = {
            "id": "run%d" % (n + 1),
            "title": title,
            "sub": "%s–%s · %s books · publication order"
                   % (g[0]["n"], g[-1]["n"], SPELLED[len(g)]),
        }
        if n == 0:
            s["open"] = True
        s["intro"] = intro
        s["items"] = g
        sections.append(s)

    all_items = [x for s in sections for x in s["items"]]
    assert len(all_items) == 10, len(all_items)
    assert not any("w" in x for x in all_items), "a weight got in"
    assert not any("opt" in x for x in all_items), \
        "nothing here is optional; the source counts all ten"
    assert len({x["id"] for x in all_items}) == 10, "duplicate row id"
    accent_is_free()

    blurb = ("Iain M. Banks's Culture books in the order he published them "
             "— standalone space opera in a post-scarcity galaxy, plus "
             "the short-story collection the source counts with them.")
    assert not re.search(r"\d", blurb), "no counts in the blurb (CLU-190)"

    p = {
        "slug": SLUG,
        "title": "The Culture novels",
        "subtitle": "Iain M. Banks — %s novels and %s collection"
                    % (SPELLED[novels], SPELLED[collections]),
        "kind": "books",
        "popularity": 49,
        "year": "%d–%d" % (span_from, span_to),
        "blurb": blurb,
        "unit": {"one": "book", "many": "books"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ["Publication order, and for once it barely matters.",
             "The source lists the series by publication date and so does "
             "this page. Banks wrote every one of these as a self-contained "
             "story with new characters — the article says so in its "
             "first paragraph — so there is no chronology to get wrong "
             "and no book that gives another away. Later books do refer back "
             "to earlier ones, which is the only reason an order is worth "
             "having at all."],
            ["One of the ten is not a novel.",
             "Wikipedia counts the series as %s novels and %s short story "
             "collection, and %s is the collection. It is a full row rather "
             "than an optional one because the source counts it among the "
             "ten, and because two of its stories are set in the Culture "
             "outright. Like every other row it counts as one."
             % (SPELLED[novels], SPELLED[collections], d_title)],
            ["The source contradicts itself about one year, and this is the "
             "one it is.",
             "%s is dated %d by the article's infobox and by the bibliography "
             "it cites, and %d by the table of books on the same page. This "
             "page carries %d, the year the two independent sources agree on. "
             "The row's position is not in doubt either way: both of the "
             "source's own lists put it fourth."
             % (d_title, d_keep, d_other, d_keep)],
            ["Inversions is here because the source puts it here.",
             "The article's own entry for it says it is not explicitly a "
             "Culture novel, and then files it with the other nine. Tick it "
             "or skip it; nothing else on this page leans on it."],
            ["Hours are not tracked.",
             "Every book counts as one and nothing on this page is weighted. "
             "Page counts differ by edition, a page is not an hour, and one "
             "weighted row would quietly turn every other row into an hour "
             "— so there are none at all."],
            "Titles, years, publication order and the count read from "
            "Wikipedia's Culture series article — its infobox, its "
            "table of books and its bibliography.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d rows (%d novels, %d collection)"
          % (out.name, len(all_items), novels, collections))
    for s in sections:
        print("   %-18s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))
    print("   disputed year: %s %d (infobox, bibliography) vs %d (table)"
          % (d_title, d_keep, d_other))


if __name__ == "__main__":
    main()
