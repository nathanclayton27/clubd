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
out of the wikitext cached under scratch/culture/, and the page is read in
THREE places so the years are corroborated rather than trusted:

  the infobox `books` plainlist    the ten titles, with years, in order
  the `number_of_books` field     the series' stated size
  the Books in the series table   the same ten as {{Book list}} blocks, with
                                  their own publish_date and a summary that
                                  classifies each row
  the Primary sources bibliography  a third year per title

Those three places agree on nine of the ten rows and disagree on one: THE
STATE OF THE ART is 1991 in the infobox and the bibliography and 1989 in the
table. The generator detects that mechanically rather than papering over it —
it asserts that there is exactly one disagreement and that the table is the
one dissenting, and it ships the year the other two carry, with a note saying
the page contradicts itself. They are three places in one article, not three
independent sources, so the note says "two places to one" and claims no more
than that. Both of the source's own lists put the row fourth regardless, so
only the printed year is in question, never the position.

The State of the Art is also the one row that is not a novel: the article says
"nine novels and one short story collection" and the row's own summary opens
"A short story collection." It is a full row, not an optional one, because the
source counts it among the ten — and it carries a note saying what it is. The
classification is read from the summary, not assumed.

That row is also why the page is called THE CULTURE SERIES and not "the
Culture novels": ten rows, one of which is not a novel, so the plural would be
false for a tenth of the page. "Culture series" is the article's own name for
the thing — its first sentence is "The Culture series is a science fiction
series" — and the subtitle still spells out the nine-and-one split. Do not
rename this back.

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


def spell(n):
    """Numbers are spelled out in prose on this page; digits are for years."""
    return SPELLED.get(n, str(n))


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


def lead_selfcontained(text):
    """The lead's standalone clause, which note 1 and two intros lean on.

    Note the scope: the article says each NOVEL is self-contained. One row here
    is not a novel, so nothing on the page may widen this to all ten.
    """
    a = "Each novel is a self-contained story with new characters"
    b = "reference is occasionally made to the events of previous novels"
    assert a in text and b in text, \
        "the lead's self-contained sentence was rewritten"
    return a, b


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


def draft_years(text, titles):
    """Years the Genesis section attaches to the early drafts, per title.

    It dates four of them — "In Banks's first draft of ''Use of Weapons'' in
    1974", then "the first draft of ''The Player of Games'' from 1980 and that
    of ''Consider Phlebas'' from 1982". The opening section's intro quotes two
    of these, so they are parsed rather than typed: if the sentence is
    rewritten this raises instead of shipping a stale claim.

    Only series titles count, which drops ''The Wasp Factory'' (a 1983 date,
    and an acceptance rather than a draft). ''The State of the Art''`s 1979 is
    dated to the title NOVELLA, not to the collection the row is — which is
    why the intro quotes the two unambiguous ones and not that.
    """
    seg = text.split("==Genesis of the series==")[1].split("==Reception==")[0]
    out = {}
    for m in re.finditer(
            r"''\[\[([^\]|]+)(?:\|([^\]]+))?\]\]''[^.]{0,60}?"
            r"(?:in|from)\s+(\d{4})", seg):
        t = linked(m)
        if t in titles:
            out.setdefault(t, int(m.group(3)))
    return out


def reception_picks(text):
    """The two rows the Reception section singles out of the middle run.

    The middle section's intro reports these, so they are matched here and the
    years come out of the match: if either sentence is rewritten this raises.
    """
    seg = text.split("==Reception==")[1].split("==Notes==")[0]
    a = re.search(r"''\[\[Inversions[^\]]*\]\]'' won the (\d{4}) Italia "
                  r"Science Fiction Award for the Best International Novel",
                  seg)
    b = re.search(r"The American edition of ''\[\[Look to Windward\]\]'' was "
                  r"listed by the editors of ''SF Site'' as one of the "
                  r"\"Best SF and Fantasy Books of (\d{4})\" after the UK "
                  r"edition had missed out by just one place the previous "
                  r"year", seg)
    assert a and b, \
        "the Reception lines for Inversions / Look to Windward moved"
    assert "''[[Excession]]''" not in seg, \
        "Excession is in Reception now; the middle intro says it is not"
    return int(a.group(1)), int(b.group(1))


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
    lead_selfcontained(text)
    tb = table_books(text)
    bib = bibliography_years(text)
    drafts = draft_years(text, {t for t, _ in ib})
    award_year, listed_year = reception_picks(text)

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

    # --- three places in the article, reconciled. They are not independent
    # sources and the page does not claim they are; where the table dissents we
    # go with the other two on the count and say so. Exactly one such row is
    # tolerated: a second one means the article has been rewritten and a human
    # should look.
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
        d_title: prop.join_bits(
            "Short story collection, not a novel",
            "two of its works explicitly set in the Culture universe"),
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

    # Intros carry something the `sub` does not already say — the sub has the
    # span, the count and the ordering, so repeating any of those is filler.
    # Each of these earns its place off a named line of the article: the
    # Genesis section's draft dates, the lead's "occasionally", and the
    # article's silence about the gaps. Every number in them is computed.
    early, late = "Use of Weapons", "Consider Phlebas"
    assert {early, late} <= set(drafts), \
        "the Genesis draft dates moved: %s" % sorted(drafts)
    assert drafts[early] < drafts[late], \
        "draft dates no longer run %s before %s: %s" % (early, late, drafts)
    assert groups[0][0]["t"] == late, \
        "%s no longer opens the first run" % late
    assert early in [x["t"] for x in groups[0]], \
        "%s is no longer in the first run" % early
    gap3 = int(groups[2][0]["n"]) - int(groups[1][-1]["n"])
    assert groups[1][-1]["t"] == "Look to Windward", \
        "the middle run no longer ends on Look to Windward"
    assert hedged[0] in [x["t"] for x in groups[1]], \
        "%s left the middle run" % hedged[0]

    TITLES = ["The opening run", "The middle three", "The last three"]
    INTROS = [
        "Publication order is not writing order: the source dates the first "
        "draft of %s to %d and %s's to %d, %s years later — and %s is the one "
        "that came out first. This page follows the shelf, not the desk."
        % (early, drafts[early], late, drafts[late],
           spell(drafts[late] - drafts[early]), late),
        "The article's reception section singles out two of these three: %s "
        "took the %d Italia Science Fiction Award for best international "
        "novel, and the American edition of %s made SF Site's best-of-%d list "
        "after the UK edition missed by one place the year before."
        % (hedged[0], award_year, groups[1][-1]["t"], listed_year),
        "The last Culture book he published is the bottom row here, and the "
        "%s years in front of %s are the reason the page splits at all. The "
        "article says nothing about what that gap was for, so neither does "
        "this." % (spell(gap3), groups[2][0]["t"]),
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
        # Not "the Culture novels": one of the ten rows is a collection, so the
        # plural would be false for it. This is the article's own name.
        "title": "The Culture series",
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
            # "Each NOVEL" is the article's scope and it stays the scope: one
            # of the ten rows is not a novel, so "every one of these" would be
            # the article's sentence stretched over a row it excludes.
            ["Publication order, and for once it barely matters.",
             "The source lists the series by publication date and so does "
             "this page. Each novel is a self-contained story with new "
             "characters — the article says so in its first paragraph — so "
             "there is no chronology to get wrong. It also says reference is "
             "occasionally made to the events of previous novels, which is "
             "the only reason an order is worth having at all."],
            ["One of the ten is not a novel.",
             "Wikipedia counts the series as %s novels and %s short story "
             "collection, and %s is the collection. It is a full row rather "
             "than an optional one because the source counts it among the "
             "ten, and because two of the works in it are explicitly set in "
             "the Culture universe. Like every other row it counts as one."
             % (SPELLED[novels], SPELLED[collections], d_title)],
            ["The source contradicts itself about one year, and this is the "
             "one it is.",
             "%s is dated %d by the article's infobox and by the bibliography "
             "it cites, and %d by the table of books on the same page. This "
             "page carries %d on the count — two places to one, all three of "
             "them the same article. The row's position is not in doubt "
             "either way: both of the source's own lists put it fourth."
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

    # The title names ten rows, one of which is not a novel, so it may not say
    # "novels" — and the name it does use has to be the article's own.
    assert "The Culture series comprises" in text, \
        "the article no longer calls the thing 'the Culture series'"
    assert "novel" not in p["title"].lower(), \
        "the title must not say 'novels': %s is a collection" % d_title
    assert "%s novels and %s collection" % (SPELLED[novels],
                                            SPELLED[collections]) \
        in p["subtitle"], "the subtitle has to keep carrying the split"

    out = prop.write(p)
    print("wrote %s — %d rows (%d novels, %d collection)"
          % (out.name, len(all_items), novels, collections))
    for s in sections:
        print("   %-18s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))
    print("   disputed year: %s %d (infobox, bibliography) vs %d (table)"
          % (d_title, d_keep, d_other))


if __name__ == "__main__":
    main()
