#!/usr/bin/env python3
"""Generate properties/avatar.json.

    python tools/make_avatar.py

*Avatar: The Last Airbender* (61 chapters, three books), *The Legend of Korra*
(52 chapters, four books) and *Avatar: Seven Havens* (13 chapters so far, one
book) as one list of 126, in air order, one section per book. Korra is a sequel
rather than a spin-off — same world, same creators, the next Avatar — so it
belongs on the same page rather than on one of its own, and Seven Havens
(2026) is a sequel on exactly those terms: created by DiMartino and Konietzko,
set after Korra, about the next Avatar.

Seven Havens' later books are ordered but undated (TBA in the franchise
article's series overview), so they are not rows. The generator reads that
overview and fails the moment a later book gains a date, so the dated book
gets added as a not-out-yet row instead of being missed.

The live-action retellings, the 2010 film and the 2024 Netflix series, are not
here. They are separate works with their own reception and neither is an
episode of any of the three shows; the list's own notes say so, so the omission
reads as a decision rather than an oversight.

Everything numeric is enumerated from Wikipedia's episode tables — the seven
season articles the two "List of ... episodes" pages transclude, and Seven
Havens' own article, which has no list page or season article and carries its
one table itself — never from an infobox count. The infobox totals and the
series-overview per-book counts (the list pages' own, and the franchise
article's for Seven Havens) are read as well and asserted against the
enumerated rows, so an edit that desynchronises a table from its own summary
fails this generator loudly instead of shipping a list that is quietly one
episode short.

Parsing details that earned their code here:

  * Blocks are brace-balanced, not regex-terminated. "The Tales of Ba Sing Se"
    carries a multi-line {{efn}} whose closing braces sit on their own line; a
    non-greedy `.*?\\n}}` ends the block there and the episode silently loses
    its air date.
  * Fields are split at top-level pipes only, so a `|` inside a wikilink, a
    citation or a footnote cannot invent a field.
  * In November 2026 the list pages renamed their headings from "Book One:
    ''Water''" to "Season 1: ''Water''", and "Winter Solstice" lost its
    per-part |Title_1/|Title_2 ("The Spirit World (Winter Solstice, Part 1)")
    for one |Title, the part names surviving only as '''Part 1: "The Spirit
    World"''' in its summary. Both heading shapes are read, and a part name
    given that way in the summary keeps the row titled as it always was.

Nothing is weighted: see the note of the same name in the list.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki                                    # noqa: E402

SLUG = "avatar"
ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "scratch" / "avatar"
WIKI = "https://en.wikipedia.org/wiki/"

# The totals this list signed up for. Enumerated rows must equal them, and so
# must the infobox and the series-overview figures on the source pages.
SERIES = [
    {
        "key": "atla",
        "title": "Avatar: The Last Airbender",
        "short": "The Last Airbender",
        "idp": "atla",
        "article": "Avatar: The Last Airbender",
        "list": "List of Avatar: The Last Airbender episodes",
        "seasons": ["Avatar: The Last Airbender season %d" % n for n in (1, 2, 3)],
        "total": 61,
        "books": [20, 20, 21],
    },
    {
        "key": "korra",
        "title": "The Legend of Korra",
        "short": "The Legend of Korra",
        "idp": "korra",
        "article": "The Legend of Korra",
        "list": "List of The Legend of Korra episodes",
        "seasons": ["The Legend of Korra season %d" % n for n in (1, 2, 3, 4)],
        "total": 52,
        "books": [12, 14, 13, 13],
    },
    {
        # no "List of ... episodes" page and no season articles: the article
        # holds the only episode table, and the franchise article holds the
        # series overview, which is also where the book's name is given
        "key": "havens",
        "title": "Avatar: Seven Havens",
        "short": "Seven Havens",
        "idp": "havens",
        "article": "Avatar: Seven Havens",
        "list": None,
        "overview": "Avatar: The Last Airbender (franchise)",
        "seasons": ["Avatar: Seven Havens"],
        "links": ["Avatar: Seven Havens#Episodes"],
        "total": 13,
        "books": [13],
    },
]

# Table entries that cover more than one numbered chapter, keyed by the overall
# numbers they span. Asserted against what the tables actually say, so the note
# naming them cannot drift away from the data.
MULTIPART = {
    "atla": [((7, 8), "Winter Solstice"),
             ((19, 20), "The Siege of the North"),
             ((50, 51), "The Day of Black Sun"),
             ((54, 55), "The Boiling Rock"),
             ((58, 59, 60, 61), "Sozin's Comet")],
    "korra": [((15, 16), "Civil Wars"),
              ((19, 20), "Beginnings")],
    "havens": [((8, 9), "The Envoys")],
}

ORDINALS = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight",
            "Nine", "Ten"]
MONTHS = ["", "January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


# --------------------------------------------------------------- wikitext ---

def page(name):
    """Cached wikitext, comments stripped so they cannot unbalance braces."""
    text = wiki.wikitext(name, cache_dir=str(CACHE))
    assert text, "no wikitext for %s" % name
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def balanced_blocks(text, opener):
    """Every {{opener...}} in `text`, closed by brace counting.

    A non-greedy regex stops at the first `}}` on its own line, which is inside
    a multi-line footnote for at least one episode in this franchise.
    """
    out = []
    for m in re.finditer(r"\{\{(?:#invoke:)?%s" % opener, text, re.I):
        i, depth = m.start(), 0
        while i < len(text):
            if text.startswith("{{", i):
                depth += 1
                i += 2
            elif text.startswith("}}", i):
                depth -= 1
                i += 2
                if depth == 0:
                    break
            else:
                i += 1
        assert depth == 0, "unbalanced template at %d" % m.start()
        out.append(text[m.start():i])
    return out


def fields(block):
    """Named arguments of a template, split at top-level pipes only."""
    body, parts, buf, depth, i = block[2:-2], [], [], 0, 0
    while i < len(body):
        two = body[i:i + 2]
        if two in ("{{", "[["):
            depth += 1
            buf.append(two)
            i += 2
        elif two in ("}}", "]]"):
            depth -= 1
            buf.append(two)
            i += 2
        elif body[i] == "|" and depth == 0:
            parts.append("".join(buf))
            buf = []
            i += 1
        else:
            buf.append(body[i])
            i += 1
    parts.append("".join(buf))
    out = {}
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def title_of(raw):
    """A display title. <br /> is a line break inside a title, not a list
    separator, so it becomes a space before gwlib's cleaner turns it into a
    comma and leaves 'The Day of Black Sun,, Part 1'."""
    t = wiki.clean(re.sub(r"<br\s*/?>", " ", raw)).strip().strip('"')
    return re.sub(r"\s+", " ", t)


def date_of(raw):
    m = re.search(r"Start date\|(\d+)\|(\d+)\|(\d+)", raw)
    assert m, "no air date in %r" % raw[:80]
    return tuple(int(x) for x in m.groups())


def part_name(summary, i):
    """A part's own name where the summary gives one as '''Part 2: "Avatar
    Roku"''' (quotes optional). A bare '''Part 1''' or {{Itcol|Part 1}} names
    nothing, and None sends the row back to "<Title>, Part <i>"."""
    m = re.search(r"'''Part %d:\s*\"?([^'\"]+?)\"?'''" % i, summary or "")
    return m.group(1).strip() if m else None


def episodes_of(text):
    """(overall, in-book, title, air date) per numbered chapter, table order.

    In-book is None where the table has no EpisodeNumber2 column, which only a
    one-book series may do (collect() asserts it); there the two are equal."""
    rows = []
    for block in balanced_blocks(text, "Episode list"):
        f = fields(block)
        parts = int(f.get("NumParts", 1))
        named = [part_name(f.get("ShortSummary"), i)
                 for i in range(1, parts + 1)] if parts > 1 else [None]
        # all parts named or none: half a set of names is a summary edit in
        # progress, not a title
        if not all(named):
            named = [None] * parts
        for i in range(1, parts + 1):
            sfx = "_%d" % i if parts > 1 else ""
            title = f.get("Title" + sfx)
            if not title and named[i - 1]:
                # Winter Solstice: the parts' own names live in the summary
                title = "%s (%s, Part %d)" % (named[i - 1],
                                              title_of(f["Title"]), i)
            elif not title:
                # one title over several chapters: The Boiling Rock, Civil Wars
                title = "%s, Part %d" % (title_of(f["Title"]), i)
            else:
                title = title_of(title)
            in_book = f.get("EpisodeNumber2" + sfx)
            rows.append((int(f["EpisodeNumber" + sfx]),
                         int(in_book) if in_book else None,
                         title,
                         date_of(f.get("OriginalAirDate" + sfx)
                                 or f["OriginalAirDate"]),
                         parts))
    return rows


def books_of(list_page_text):
    """(ordinal word, book name, displayed year span) per book heading.

    The headings have read both "Book One: ''Water''" and "Season 1:
    ''Water''"; the section titles keep the franchise's own "Book One"."""
    out = re.findall(r"^===\s*(?:Book ([A-Za-z]+)|Season (\d+)):\s*''(.+?)''"
                     r"\s*\((.+?)\)\s*===\s*$", list_page_text, re.M)
    assert out, "no book headings"
    return [(word or ORDINALS[int(num) - 1], b.strip(), c.strip())
            for word, num, b, c in out]


def overview_counts(list_page_text):
    """The per-book episode counts the list page's own summary box claims."""
    m = re.search(r"\{\{Series overview(.*?)\n\}\}", list_page_text, re.S)
    assert m, "no series overview"
    got = re.findall(r"\|\s*episodes(\d+)\s*=\s*(\d+)", m.group(1))
    return [int(n) for _, n in sorted(got, key=lambda kv: int(kv[0]))]


def released_books(franchise_text, series):
    """(episode count, book name) per released book of `series`, from the
    franchise article's overview box for it.

    A book counts as released when its start is a dated {{Start date}}. One
    still TBA is undated and stays off the list; anything else, or a dated book
    after an undated one, fails here, because a later book that gains a date
    must be added as a not-out-yet row rather than slip past."""
    for block in balanced_blocks(franchise_text, "Series overview"):
        f = fields(block)
        if title_of(f.get("series", "")) != series:
            continue
        out, n, undated = [], 1, False
        while "start%d" % n in f:
            start = f["start%d" % n]
            if re.search(r"Start date\|\d{4}\|\d+\|\d+", start):
                assert not undated, \
                    "%s book %d is dated after an undated book" % (series, n)
                out.append((int(f["episodes%d" % n]),
                            title_of(f["auxA%d" % n])))
            else:
                assert re.fullmatch(r"\{\{N/A\|TBA\}\}", start), \
                    "%s book %d starts %r: dated now? add it as a w: 0 row" % (
                        series, n, start)
                undated = True
            n += 1
        assert out, "%s: no released books in the overview" % series
        return out
    raise AssertionError("no series overview for %s" % series)


def infobox_total(article_text):
    f = wiki.infobox(article_text, kind=r"television")
    assert f, "no television infobox"
    return int(re.search(r"\d+", f("num_episodes")).group(0))


# ----------------------------------------------------------------- sections --

def collect(s):
    """Every chapter of one series, checked against every count the source
    publishes about itself."""
    rows = []
    for season in s["seasons"]:
        rows += episodes_of(page(season))

    nums = [r[0] for r in rows]
    assert nums == list(range(1, s["total"] + 1)), \
        "%s: episode numbers are %r, not 1..%d" % (s["key"], nums[:5], s["total"])
    assert len(rows) == s["total"], "%s: %d rows, expected %d" % (
        s["key"], len(rows), s["total"])

    # a table with no in-book column is only readable for a one-book series,
    # where the in-book number is the overall one
    if any(r[1] is None for r in rows):
        assert all(r[1] is None for r in rows) and len(s["books"]) == 1, \
            "%s: in-book numbers missing from a multi-book table" % s["key"]
        rows = [(r[0], r[0]) + r[2:] for r in rows]

    # the tables are the authority; the infobox and the overview only get to
    # agree with them
    article = page(s["article"])
    box = infobox_total(article)
    assert box == s["total"], \
        "%s: infobox says %d episodes, the tables enumerate %d" % (
            s["key"], box, s["total"])
    if s["list"]:
        listing = page(s["list"])
        overview = overview_counts(listing)
        books = books_of(listing)
    else:
        released = released_books(page(s["overview"]), s["title"])
        overview = [n for n, _ in released]
        years = sorted({r[3][0] for r in rows})
        span = "%d" % years[0] if len(years) == 1 else "%d–%d" % (
            years[0], years[-1])
        assert len(released) == 1, "%s: books per year are not derived " \
            "for more than one book yet" % s["key"]
        books = [(ORDINALS[0], released[0][1], span)]
        # the article names the book too; the two must agree
        assert "''Book One: %s''" % released[0][1] in article, \
            "%s: the article does not call book one %r" % (
                s["key"], released[0][1])
    assert overview == s["books"], \
        "%s: series overview says %r, this list expects %r" % (
            s["key"], overview, s["books"])
    assert sum(overview) == s["total"], "%s: overview sums to %d" % (
        s["key"], sum(overview))

    assert len(books) == len(s["books"]), \
        "%s: %d book headings, %d book counts" % (
            s["key"], len(books), len(s["books"]))
    assert [b[0] for b in books] == ORDINALS[:len(books)], \
        "%s: unexpected book ordinals %r" % (s["key"], [b[0] for b in books])

    # air order, which is also the order the tables are written in
    dates = [r[3] for r in rows]
    assert dates == sorted(dates), "%s: rows are not in air order" % s["key"]

    # multi-part entries, named in the notes, verified here
    groups, i = [], 0
    while i < len(rows):
        n = rows[i][4]
        if n > 1:
            groups.append(tuple(r[0] for r in rows[i:i + n]))
        i += n
    assert groups == [g for g, _ in MULTIPART[s["key"]]], \
        "%s: multi-part entries are %r" % (s["key"], groups)

    return rows, books


def sections_for(s, rows, books):
    out, first = [], 1
    for i, ((word, name, years), count) in enumerate(zip(books, s["books"]), 1):
        last = first + count - 1
        chunk = rows[first - 1:last]
        assert [r[1] for r in chunk] == list(range(1, count + 1)), \
            "%s book %d: in-book numbering is not 1..%d" % (s["key"], i, count)
        sec = {
            "id": "%s-b%d" % (s["idp"], i),
            "title": "%s · Book %s: %s" % (s["short"], word, name),
            "sub": "%s · %d episodes · %d–%d of %d" % (
                years, count, first, last, s["total"]),
            "links": [{"label": "Episode list",
                       "url": WIKI + s.get("links", s["seasons"])[i - 1]
                       .replace(" ", "_")}],
            "items": [{"id": "%s-%d" % (s["idp"], r[0]),
                       "t": r[2],
                       "n": str(r[1])} for r in chunk],
        }
        if s["key"] == "atla" and i == 1:
            sec["open"] = True
        out.append(sec)
        first = last + 1
    assert first - 1 == s["total"]
    return out


def series_list(names):
    return ", ".join(names[:-1]) + " and " + names[-1]


def main():
    sections, spans, multi = [], [], []
    for s in SERIES:
        rows, books = collect(s)
        sections += sections_for(s, rows, books)
        spans.append((rows[0][3], rows[-1][3]))
        multi += [name for _, name in MULTIPART[s["key"]]]

    total = sum(s["total"] for s in SERIES)
    assert total == 126, total
    assert len(sections) == 8, len(sections)
    counted = sum(len(sec["items"]) for sec in sections)
    assert counted == total, (counted, total)

    first_year, last_year = spans[0][0][0], spans[-1][1][0]
    parts = sum(len(g) for s in SERIES for g, _ in MULTIPART[s["key"]])
    atla, korra, havens = SERIES
    nseries = ORDINALS[len(SERIES) - 1].lower()

    p = {
        "slug": SLUG,
        "title": "Avatar: The Last Airbender",
        "subtitle": "with The Legend of Korra and Seven Havens",
        "kind": "animated series",
        # Nickelodeon's flagship, a theatrical film, a live-action remake and a
        # streaming revival keep the name in general circulation: it sits under
        # X-Men (86) and over Breaking Bad (84), with the catalogue's other
        # acclaimed-animation flagship, Brotherhood (83), a notch below.
        "popularity": 85,
        "year": "%d–%d" % (first_year, last_year),
        "blurb": "All %d episodes of the %s series in air order — %d chapters "
                 "of The Last Airbender, then Korra's %d and Seven Havens' %d."
                 % (total, nseries, atla["total"], korra["total"],
                    havens["total"]),
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        # a deep spirit-blue with a luminous arrow-cyan: the elements' own
        # colours are all spoken for in this catalogue, and this pair sits
        # further from its nearest neighbour (Cosmere) than the median list
        "accent": "#2B3F73",
        "accentDark": "#5FD3D9",
        "tiers": False,
        "notes": [
            ["One list, %s series." % nseries,
             "The Legend of Korra and Seven Havens are sequels, not spin-offs: "
             "the same world, the same creators, the next Avatar. The Last "
             "Airbender's three books run first, then Korra's four, then Seven "
             "Havens', which is air order and story order at once."],
            ["Books, not seasons.",
             "The franchise calls a season a Book and an episode a chapter. One "
             "section per book; the number on a row is its place within that "
             "book, and every section header carries the series-wide range so "
             "%s stay countable."
             % series_list(["the %d" % s["total"] for s in SERIES])],
            ["The live-action versions are not here.",
             "The 2010 film and the 2024 Netflix series retell this story as "
             "separate works with their own reception, and neither is an "
             "episode of any of the %s shows. Left out deliberately, not "
             "forgotten." % nseries],
            ["Multi-part chapters get a row each.",
             "%s table entries across the %s series cover more than one "
             "numbered chapter — %s — %d chapters between them. Each part is "
             "numbered separately at the source, so each part is its own row "
             "here." % (ORDINALS[len(multi) - 1], nseries, series_list(multi),
                        parts)],
            ["Nothing is weighted.",
             "The episode tables carry no per-episode runtime and each series "
             "infobox gives at most one blanket figure for every chapter, which "
             "is plainly wrong for a four-part finale that also aired as a "
             "two-hour television film. Repeating a number the source does not "
             "have per row would be inventing data, so nothing is weighted at "
             "all and all %d rows count the same." % total],
            "Titles, numbering and air dates are read from the seven Wikipedia "
            "season articles the two episode lists transclude, and from Seven "
            "Havens' own article, which carries its only episode table. Every "
            "series total and every book's count is checked against a "
            "series-overview box (the two lists' own, and the franchise "
            "article's for Seven Havens) and the series infoboxes; the "
            "generator fails rather than ship a list that disagrees with its "
            "sources.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s" % out.name)
    print("  %d sections, %d episodes (%s)"
          % (len(sections), counted,
             " + ".join(str(s["total"]) for s in SERIES)))
    for sec in sections:
        print("   %-40s %-34s %3d" % (sec["title"], sec["sub"], len(sec["items"])))


if __name__ == "__main__":
    main()
