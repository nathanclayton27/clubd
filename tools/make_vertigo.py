#!/usr/bin/env python3
"""Generate properties/vertigo.json — the Vertigo shelf.

    python tools/make_vertigo.py

One list, one section per series, one row per COLLECTED VOLUME. The three
runs are Preacher, Transmetropolitan and Y: The Last Man; each section is a
complete run in the trades it was collected into, so the whole shelf is
twenty-nine ticks instead of a hundred and eighty-six issues.

Nothing here is typed from memory. Every title, volume number, issue range
and release date is machine-read from wikitext cached under scratch/vertigo/
(fetched on first run via gwlib.wiki, disk-cached after), and the editorial
claims in the section intros — the Eisner wins, the Hugo nomination, the
Helix-to-Vertigo move — are each asserted present in the source article
before the file is written. So are the two exclusions:

  * The Sandman is excluded because it already has its own list in this
    catalogue (properties/sandman.json, one row per issue). A silent gap on
    a page called "the Vertigo shelf" would read as an oversight, so the
    notes name it and point at it.
  * Saga is excluded because it is not a Vertigo book — the generator reads
    Image Comics out of its infobox and refuses to proceed if that ever
    changes — and because it is still running, which a completion tracker
    cannot honestly close.

The parsers, and why each is shaped the way it is:

  Y            the Collected editions table has no `scope="row"` headers and
               a rowspan on the Format column, so the release date is found
               by {{dts}} anywhere in the row rather than by cell position.
               Titles are cross-checked against the infobox's own TPB list,
               which spells the small words properly ("Ring of Truth", not
               the table's "Ring Of Truth").
  Preacher     `! scope="row"` rows, some cells carrying a style attribute
               ahead of the content; cells are read in order after the attr
               is stripped.
  Transmet     cells contain multi-line {{plainlist}} ISBN blocks, so a cell
               is "a line starting with | plus every line after it that does
               not" — line-per-cell splitting would have lost the extras.
               Column 2 is the CURRENT printing; the first printing cut the
               same 60 issues differently and Vol. 0 was folded into Vols 3
               and 10, so Vol. 0 is dropped (asserted, not assumed).

EVERY ROW IS WEIGHTED, AND THE WEIGHT IS COMICS (CLU-555). A row here is a
BOOK while a row on every other comics list in the catalogue is an ISSUE, and
that difference used to mean this page could carry no weight at all. It is the
wrong conclusion. The unit of a tick and the unit of a mark are two different
questions: a tick is a volume, because a volume is what you finish, and a mark
is issues, because issues are the one quantity every comics list on the site
can state. So each row's `w` is the number of comics that volume collects,
read off its own "Material collected" cell.

Why it has to be that and not one-per-volume. This list is a door on the DC
Comics shelf, and build.py gives a door a weight equal to the sum of its
target's rows. Weighing a volume one would draw the Vertigo door as 29 beside
Sandman's 88 — a third of Sandman's width for a shelf that is more than twice
its size. A mark must mean one thing across a hub, and the only thing all
eight DC doors can mean is issues.

WEIGHT = x.w >= 0 ? x.w : 1 downstream, so this is all-or-nothing: a single
unweighted row here would silently draw as one comic. Hence the stamp is
asserted over every row rather than applied per constructor.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from gwlib import prop, wiki  # noqa: E402

SLUG = "vertigo"
CACHE = prop.ROOT / "scratch" / SLUG
WP = "https://en.wikipedia.org/wiki/"

# Ink and a bruise. Asserted unique against every other property below, not
# eyeballed — the sweep linter only catches a shared pair after it ships.
ACCENT, ACCENT_DARK = "#2E2039", "#B08CD9"

PAGES = {
    "y": "Y: The Last Man",
    "preacher": "Preacher (comics)",
    "transmet": "Transmetropolitan",
    "saga": "Saga (comics)",
    "imprint": "Vertigo Comics",
}

ANCHOR = {
    "y": WP + "Y:_The_Last_Man#Collected_editions",
    "preacher": WP + "Preacher_(comics)#Collected_editions",
    "transmet": WP + "Transmetropolitan#Collected_editions",
}

WORDS = {2: "two", 3: "three", 4: "four", 5: "five"}

MONTHS = {"Jan": "January", "Feb": "February", "Mar": "March",
          "Apr": "April", "May": "May", "Jun": "June", "Jul": "July",
          "Aug": "August", "Sep": "September", "Oct": "October",
          "Nov": "November", "Dec": "December"}

# Claims made in the section intros. Each must be findable in its article or
# the build fails — the alternative is an intro that drifts away from the
# source and nobody notices.
CLAIMS = {
    "y": ["published in sixty issues",
          "won the [[Eisner Award]] for [[Eisner Award for Best Continuing "
          "Series|Best Continuing Series]]",
          "[[Hugo Award for Best Graphic Story]]"],
    "preacher": ["66 regular, monthly issues",
                 "won the [[Eisner Award for Best Continuing Series]] in 1999"],
    "transmet": ["was switched to the [[Vertigo Comics|Vertigo]] imprint "
                 "starting with issue #13",
                 "[[Helix (comics)|Helix]]"],
}

# Runs the shelf deliberately does not chase. Named in the notes, so each one
# is asserted to be a real Vertigo title per the imprint's own article rather
# than a name recalled from somewhere.
LEFT_OFF = ["Hellblazer", "Swamp Thing", "Doom Patrol", "The Invisibles",
            "Sandman Mystery Theatre", "100 Bullets", "Fables", "DMZ",
            "Scalped"]


def text(key):
    """Cached wikitext for one of PAGES; fetched on first run."""
    t = wiki.wikitext(PAGES[key], cache_dir=str(CACHE))
    assert t and len(t) > 5000, "no wikitext for %s" % PAGES[key]
    return t


def field(box, name):
    """One field out of a wikitext infobox blob."""
    m = re.search(r"^\s*\|\s*%s[ \t]*=[ \t]*(.*?)(?=\n\s*\|\s*[A-Za-z]"
                  r"[A-Za-z0-9_ ]*[ \t]*=|\n\}\})" % name, box, re.M | re.S)
    return wiki.clean(m.group(1)) if m else ""


def box_of(t):
    """The page's opening infobox, however it is named."""
    m = re.search(r"\{\{(?:Infobox comic book title|Comicsbooktitlebox)", t, re.I)
    assert m, "no comic infobox"
    return re.sub(r"<!--.*?-->", "", t[m.start():m.start() + 4000], flags=re.S)


def span(t):
    """(first year, last year) out of an infobox `date` field."""
    ys = [int(y) for y in re.findall(r"(?:19|20)\d{2}", field(box_of(t), "date"))]
    assert len(ys) >= 2 and ys[0] < ys[-1], ys
    return ys[0], ys[-1]


def rng(s, series=""):
    """'#18-23' -> (18, 23). A bare '#2' is not a range.

    `series` anchors the match to one title, which is what keeps Preacher's
    Ancient History volume honest: its contents cell reads "Saint of Killers
    #1-4", and an unanchored regex read that as main-run issues 1-4.
    """
    m = re.search(r"%s#\s*(\d+)\s*[-–—]\s*(\d+)"
                  % (re.escape("''%s'' " % series) if series else ""), s)
    return (int(m.group(1)), int(m.group(2))) if m else None


def contiguous(ranges, last):
    """Ranges must tile #1..last with no gap and no overlap."""
    assert ranges[0][0] == 1, ranges[0]
    for a, b in zip(ranges, ranges[1:]):
        assert b[0] == a[1] + 1, (a, b)
    assert ranges[-1][1] == last, ranges[-1]


def nondecreasing(years, where):
    """Release years must never run backwards inside a section."""
    for a, b in zip(years, years[1:]):
        assert a <= b, "%s: release years go backwards %d -> %d" % (where, a, b)


def month_year(raw):
    """'{{dts|23 Nov 2005}}' / 'March 1, 1996' -> ('November 2005', 2005)."""
    raw = wiki.clean(raw)
    y = re.search(r"(?:19|20)\d{2}", raw)
    assert y, raw
    m = re.search(r"[A-Z][a-z]{2,}", raw)
    assert m, raw
    name = MONTHS.get(m.group(0)[:3], m.group(0))
    return "%s %s" % (name, y.group(0)), int(y.group(0))


# ---------------------------------------------------------------- Y


def parse_y(t):
    """The ten original trade paperbacks, #1-60."""
    seg = t.split("==Collected editions==", 1)[1]
    tpb = seg.split("|Trade Paperbacks", 1)[1].split("!colspan", 1)[0]
    infobox_titles = [field(box_of(t), "TPB")] + \
                     [field(box_of(t), "TPB%d" % i) for i in range(1, 10)]
    assert all(infobox_titles), infobox_titles

    rows = []
    for chunk in tpb.split("\n|-"):
        vol = re.search(r"^\|(\d+)\s*$", chunk, re.M)
        title = re.search(r"'''''(.+?)'''''", chunk)
        pages = re.search(r'text-align: center;"\|(\d+)', chunk)
        date = re.search(r"\{\{dts\|(.+?)\}\}", chunk)
        if not (vol and title and date):
            continue
        got = rng(chunk, "Y: The Last Man")
        assert got, chunk[:80]
        when, year = month_year(date.group(1))
        rows.append({"vol": int(vol.group(1)), "t": title.group(1).strip(),
                     "range": got, "pages": int(pages.group(1)) if pages else 0,
                     "when": when, "year": year})

    assert len(rows) == 10, "Y: expected 10 trade paperbacks, got %d" % len(rows)
    assert [r["vol"] for r in rows] == list(range(1, 11))
    for r, want in zip(rows, infobox_titles):
        assert r["t"].lower() == want.lower(), (r["t"], want)
        r["t"] = want          # the infobox spells the small words properly
    contiguous([r["range"] for r in rows], 60)
    nondecreasing([r["year"] for r in rows], "Y")
    return rows


# --------------------------------------------------------- Preacher


def cells(chunk):
    """Wikitable cells of one row: a line starting with | opens a cell and
    swallows every following line that does not (the {{plainlist}} case)."""
    out = []
    for line in chunk.split("\n"):
        if line.lstrip().startswith("|") and not line.lstrip().startswith("|-"):
            body = line.lstrip()[1:]
            m = re.match(r"\s*([^|\[{]*=[^|\[{]*)\|(.*)$", body)
            out.append((m.group(2) if m else body).strip())
        elif out and line.strip():
            out[-1] += "\n" + line.strip()
    return out


def parse_preacher(t):
    """The nine original trade paperbacks: #1-66 plus the specials volume."""
    seg = t.split("== Collected editions ==", 1)[1]
    table = seg.split("|+''Preacher'' trade paperbacks", 1)[1].split("\n|}", 1)[0]

    rows = []
    for chunk in table.split("\n|-"):
        head = re.search(r"!\s*scope=\"row\"[^|]*\|(.+)", chunk)
        if not head:
            continue
        c = cells(chunk)
        assert len(c) >= 3, c
        when, year = month_year(c[1])
        title = wiki.clean(head.group(1))
        assert title.startswith("Preacher: "), title
        rows.append({"t": title[len("Preacher: "):], "raw": c[2],
                     "collects": wiki.clean(c[2]),
                     "range": rng(c[2], "Preacher"), "when": when,
                     "year": year})

    assert len(rows) == 9, "Preacher: expected 9 trade paperbacks, got %d" % len(rows)
    main = [r["range"] for r in rows if r["range"]]
    assert len(main) == 8, main            # Ancient History collects specials only
    specials = [r for r in rows if not r["range"]]
    assert len(specials) == 1 and specials[0]["t"] == "Ancient History", specials
    contiguous(main, 66)
    nondecreasing([r["year"] for r in rows], "Preacher")
    return rows


# --------------------------------------------------- Transmetropolitan


def parse_transmet(t):
    """The ten volumes of the current printing, #1-60. Vol. 0 is superseded."""
    seg = t.split("== Collected editions ==", 1)[1]
    table = seg.split("|+''Transmetropolitan'' collected editions", 1)[1] \
               .split("\n|}", 1)[0]

    rows, dropped = [], []
    for chunk in table.split("\n|-"):
        head = re.search(r"!\s*scope=\"row\"[^|]*\|(.+)", chunk)
        if not head:
            continue
        title = wiki.clean(head.group(1)).replace('"', "")
        c = cells(chunk)
        assert len(c) >= 3, (title, c)
        current = c[2]                     # old printing, ISBNs, NEW printing
        got = rng(current)
        if not got:
            dropped.append(title)
            continue
        old = rng(c[0])
        rows.append({"t": title, "range": got, "old": old, "current": current})

    assert dropped == ['Vol. 0: Tales of Human Waste'], dropped
    assert len(rows) == 10, "Transmet: expected 10 volumes, got %d" % len(rows)
    assert [r["t"][:7] for r in rows] == ["Vol. %d:" % n for n in range(1, 10)] \
                                         + ["Vol. 10"], [r["t"] for r in rows]
    contiguous([r["range"] for r in rows], 60)
    # The other two sections get nondecreasing() over their release years. This
    # table carries no dates at all, and that has to be a checked fact rather
    # than a forgotten call — if Wikipedia ever adds them, this fails and the
    # year assert gets wired up here too.
    bare = re.sub(r"\{\{ISBN[Tt]?\|[^{}]*\}\}", "", table)   # ISBNs look like years
    assert not re.search(r"|".join(MONTHS) + r"|\b(?:19|20)\d{2}\b", bare), \
        "Transmet's collected-editions table now has dates — assert them"
    return rows


# ------------------------------------------------------------ assembly


def dash(a, b):
    return "#%d–%d" % (a, b)


def and_join(names):
    """'a, b and c' — one Oxford-free list, no stray double 'and'."""
    names = list(names)
    return names[0] if len(names) == 1 else \
        "%s and %s" % (", ".join(names[:-1]), names[-1])


def spanof(r):
    """How many issues an inclusive (first, last) range covers."""
    assert r and r[1] >= r[0], r
    return r[1] - r[0] + 1


# The title is delimited by wiki italics, NOT by a quote: "One Man's War"
# contains an apostrophe, and a [^'] title class silently skipped that
# special, undercounting the run by one and tripping the prose cross-check.
PREACHER_SPECIAL = re.compile(
    r"''Preacher Special: (.+?)''(?:\s*#\s*(\d+)\s*[-\u2013\u2014]\s*(\d+))?")


def preacher_comics(r):
    """Comics in one Preacher volume, counted off its own contents cell.

    The main run's issues, plus every Preacher Special the cell names: one
    with an issue range is that many comics (Saint of Killers is a four-issue
    miniseries), one without is a single one-shot. Ancient History has no main
    run at all and is six specials' worth on its own.
    """
    n = spanof(r["range"]) if r["range"] else 0
    for m in PREACHER_SPECIAL.finditer(r["raw"]):
        n += (int(m.group(3)) - int(m.group(2)) + 1) if m.group(2) else 1
    assert n, "no comics counted for Preacher %r" % r["t"]
    return n


def transmet_comics(r):
    """The volume's own issues, plus any STANDALONE one-shot it collects.

    Two volumes also reprint a short story out of ''Vertigo: Winter's Edge'',
    an anthology of everybody's characters. The cell lists those as story
    titles under that anthology issue's heading, and a short printed inside
    somebody else's comic is not a comic: counting it would invent an issue
    for Transmetropolitan and simultaneously count one that belongs to Winter's
    Edge. So it is worth nothing here, while the two Transmetropolitan
    specials — whole books with their own covers — are worth one each. If the
    table ever grows a bullet of a third shape this stops rather than guesses.
    """
    n, body = spanof(r["range"]), r["current"]
    head, specials = body, 0
    if "The specials:" in body:
        head, tail = body.split("The specials:", 1)
        specials = len(re.findall(r"^\*", tail, re.M))
        assert specials, body
    loose = [ln for ln in head.split("\n") if ln.lstrip().startswith("*")]
    if loose:
        assert re.search(r"\"Vertigo: Winter's Edge\" #\d+:", head), body
    return n + specials


def row(rid, title, n, note, w):
    """A row. An empty note is left OUT rather than shipped as "", and `w` is
    the number of comics the volume collects — see the module docstring."""
    it = {"id": rid, "t": title, "n": n}
    if note:
        it["note"] = note
    it["w"] = w
    return it


def unique_accent(accent, dark):
    """No other property may already own this pair — the sweep linter flags a
    shared pair after the fact, and a generator should fail before that."""
    for f in sorted((prop.ROOT / "properties").glob("*.json")):
        if f.stem in (SLUG, "index", "search"):
            continue
        try:
            other = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:                 # a sibling generator mid-write
            continue
        assert (other.get("accent"), other.get("accentDark")) != (accent, dark), \
            "accent pair %s/%s is already %s's" % (accent, dark, f.stem)


def main():
    src = {k: text(k) for k in PAGES}

    # Saga: excluded on two counts, both read out of its own article rather
    # than asserted from memory. If either ever stops being true the build
    # fails and somebody re-argues the decision.
    saga_box = box_of(src["saga"])
    saga_pub = field(saga_box, "publisher")
    saga_date = field(saga_box, "date")
    assert saga_pub == "Image Comics", saga_pub
    assert "present" in saga_date, saga_date
    assert "hiatus from July 2018 to January 2022" in saga_date, saga_date
    saga_issues = re.search(r"\d+", field(saga_box, "issues")).group(0)

    # The Sandman's list has to actually be there, and be what the notes say
    # it is, before this page sends anybody to it.
    sand = prop.ROOT / "properties" / "sandman.json"
    assert sand.exists(), "notes point at properties/sandman.json and it is missing"
    sand = json.loads(sand.read_text(encoding="utf-8"))
    assert sand["title"] == "The Sandman" and sand["unit"]["one"] == "issue", sand["title"]
    assert len(sand["sections"]) == 13, len(sand["sections"])

    unique_accent(ACCENT, ACCENT_DARK)

    for key, claims in CLAIMS.items():
        for c in claims:
            assert c in src[key], "unsourced claim for %s: %r" % (key, c[:48])
    for name in LEFT_OFF:
        assert name in src["imprint"], "not a Vertigo title per the imprint: %s" % name
    born = re.search(r"Vertigo was launched in January (\d{4})", src["imprint"])
    died = re.search(r"DC discontinued Vertigo in January (\d{4})", src["imprint"])
    assert born and died, "the imprint's own dates moved"
    born, died = int(born.group(1)), int(died.group(1))

    y, preacher, transmet = (parse_y(src["y"]), parse_preacher(src["preacher"]),
                             parse_transmet(src["transmet"]))
    y_from, y_to = span(src["y"])
    p_from, p_to = span(src["preacher"])
    t_from, t_to = span(src["transmet"])
    p_issues = int(re.match(r"\d+", field(box_of(src["preacher"]), "issues")).group(0))
    t_issues = int(field(box_of(src["transmet"]), "issues"))
    assert (p_issues, t_issues) == (66, 60), (p_issues, t_issues)
    # The Y intro says the Deluxe line covers the same ground; that is five
    # books over #1-60 in the same table the rows came from.
    deluxe = src["y"].split("|Deluxe Editions", 1)[1].split("!colspan", 1)[0]
    assert len(re.findall(r"'''''Book \w+'''''", deluxe)) == 5, deluxe[:200]
    assert rng(deluxe, "Y: The Last Man")[0] == 1 and "#49-60" in deluxe

    sections = []

    sections.append({
        "id": "preacher",
        "title": "Preacher",
        "sub": "%d issues plus specials · %d–%d · %d volumes"
               % (p_issues, p_from, p_to, len(preacher)),
        "intro": "Garth Ennis and Steve Dillon, %d issues and a handful of "
                 "one-shots, and the Eisner for Best Continuing Series in "
                 "1999. These are the nine original trades. The later Book "
                 "One through Book Six hardcovers hold the same issues cut "
                 "along different lines, so go by the ranges, not the titles, "
                 "if that is the edition on your shelf." % p_issues,
        "links": [{"label": "The volumes", "url": ANCHOR["preacher"]}],
        "open": True,
        "items": [row("vert-preacher-%02d" % (i + 1), r["t"],
                      dash(*r["range"]) if r["range"] else "The specials",
                      prop.join_bits(r["when"], preacher_note(r)),
                      preacher_comics(r))
                  for i, r in enumerate(preacher)],
    })

    sections.append({
        "id": "transmet",
        "title": "Transmetropolitan",
        "sub": "%d issues · %d–%d · %d volumes"
               % (t_issues, t_from, t_to, len(transmet)),
        "intro": "Warren Ellis and Darick Robertson's gonzo journalist and "
                 "his City. It started on DC's short-lived Helix imprint and "
                 "moved to Vertigo with issue #13, which is what puts it on "
                 "this shelf. Six issues a volume in the current printing.",
        "links": [{"label": "The volumes", "url": ANCHOR["transmet"]}],
        "items": [row("vert-transmet-%02d" % (i + 1), r["t"],
                      dash(*r["range"]), transmet_note(r),
                      transmet_comics(r))
                  for i, r in enumerate(transmet)],
    })

    sections.append({
        "id": "y",
        "title": "Y: The Last Man",
        "sub": "60 issues · %d–%d · %d volumes" % (y_from, y_to, len(y)),
        "intro": "Brian K. Vaughan and Pia Guerra. Sixty issues, the Eisner "
                 "for Best Continuing Series in 2008, and a nomination for "
                 "the first Hugo for Best Graphic Story. Ten trades, and the "
                 "five Deluxe hardcovers cover exactly the same ground.",
        "links": [{"label": "The volumes", "url": ANCHOR["y"]}],
        "items": [row("vert-y-%02d" % r["vol"],
                      "Vol. %d: %s" % (r["vol"], r["t"]), dash(*r["range"]),
                      prop.join_bits(r["when"], "%d pages" % r["pages"]
                                     if r["pages"] else ""),
                      spanof(r["range"]))
                  for r in y],
    })

    # All or nothing: build.py totals a weight only when EVERY row has one,
    # and downstream an unweighted row would quietly draw as a single comic.
    for s in sections:
        for x in s["items"]:
            assert isinstance(x.get("w"), int) and x["w"] > 0, \
                "row %s has no comic count" % x["id"]

    rows = sum(len(s["items"]) for s in sections)
    assert rows == 29, rows
    issues = p_issues + t_issues + 60

    # The weights came out of the collected-editions TABLES. Check them against
    # what each article says in PROSE, which is a different sentence written by
    # different people: the main-run issues must tile exactly the run length the
    # infobox and the intro both claim, and what is left over must be the
    # specials, counted and not assumed.
    by = {s["id"]: [x["w"] for x in s["items"]] for s in sections}
    p_main = sum(spanof(r["range"]) for r in preacher if r["range"])
    t_main = sum(spanof(r["range"]) for r in transmet)
    assert (p_main, t_main, sum(by["y"])) == (p_issues, t_issues, 60), \
        (p_main, t_main, sum(by["y"]))
    p_extra, t_extra = sum(by["preacher"]) - p_main, sum(by["transmet"]) - t_main
    extras = p_extra + t_extra
    # Nine Preacher specials (Saint of Killers is four of them) and the two
    # Transmetropolitan one-shots. Typed so that a change to either article's
    # tables stops the generator instead of quietly moving every mark.
    assert (p_extra, t_extra) == (9, 2), \
        "specials count moved: %d Preacher, %d Transmetropolitan; rows %r" \
        % (p_extra, t_extra, by)
    comics = sum(sum(v) for v in by.values())
    assert comics == issues + extras, (comics, issues, extras)
    # Read off the rows rather than typed: the note names the extremes,
    # and a retitled or recut volume must move the sentence with it.
    allw = [w for v in by.values() for w in v]
    thin, thick = min(allw), max(allw)

    p = {
        "slug": SLUG,
        "title": "The Vertigo Shelf",
        "subtitle": "three complete runs, in the volumes they were collected in",
        "kind": "comics",
        "popularity": 48,
        "year": "%d–%d" % (min(y_from, p_from, t_from), max(y_to, p_to, t_to)),
        "blurb": "Preacher, Transmetropolitan and Y: The Last Man — the "
                 "imprint's great creator-owned runs, tracked by collected "
                 "volume rather than by issue. The Sandman has its own list.",
        "unit": {"one": "volume", "many": "volumes"},
        # A tick is a volume; a mark is issues. Declaring both is what keeps
        # the page honest about the difference instead of hiding it — the same
        # shape x-men and amazing-spider-man already ship.
        "weightUnit": {"one": "issue", "many": "issues"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ["One list, not one per series.",
             "Nobody reads only one of these. Split up, they would be %s thin "
             "switcher entries cluttering the catalogue, and there would be "
             "no way to see the shelf as a shelf — so each run is a section "
             "here instead. Open the one you are on and the others fold away."
             % WORDS[len(sections)]],
            ["A row is a collected volume, not an issue.",
             "The three runs are %d issues between them, and that many rows "
             "of checkbox would be unusable. So a row is a trade paperback as "
             "each series' own collected-editions table defines it, with the "
             "issues it holds printed beside it. Tick it when you finish the "
             "book." % issues],
            ["The Sandman is not here because it is already somewhere.",
             "It has its own list in this catalogue, issue by issue across "
             "the ten trades plus Death and Overture — too big to be one "
             "section of somebody else's page. Its absence from a Vertigo "
             "shelf would otherwise look like an oversight, so: two doors, "
             "both open."],
            ["Saga is not here at all.",
             "Brian K. Vaughan's other great run is an Image book, not a "
             "Vertigo one, so a shelf named for the imprint has no honest "
             "room for it — and it is still going (%s issues and counting, "
             "after a three-and-a-half-year hiatus), which a list you are "
             "meant to be able to finish cannot really hold. If it lands "
             "here one day it will be as its own list." % saga_issues],
            ["A mark's width is issues. A tick is still a volume.",
             "Comics publish no reading time, so there are no hours to size a "
             "mark with — but there are issues, and the rest of the "
             "catalogue's comics count in them. So the two units are kept "
             "apart on purpose: you tick a book, because a book is what you "
             "finish, and the bar draws that book as wide as the comics "
             "inside it. The thinnest book on the shelf holds %d comics and "
             "the thickest %d, and the marks are drawn in that proportion. The "
             "three runs are %d issues plus %d specials and one-shots — %d "
             "comics in %d volumes."
             % (thin, thick, issues, extras, comics, rows)],
            ["Left off.",
             "The imprint ran from %d to %d and this is three books out of "
             "it. Not chased here: %s, and the rest of the line. "
             "Nor the Absolute, Compendium, Deluxe and Book re-collections, "
             "which cut the same issues a different way — one row per story, "
             "not per printing." % (born, died, and_join(LEFT_OFF))],
            "Volume titles, issue ranges and release dates machine-read from "
            "each series' own Wikipedia article; a volume whose range could "
            "not be verified would fail the build rather than ship a guess. "
            "Each mark's width is counted off that volume's own Material "
            "collected cell — its issues, plus any special the cell names as "
            "a book of its own — and the three totals are checked against the "
            "issue counts the articles state in prose before the file is "
            "written.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d volumes in %d sections (%d comics = %d issues "
          "+ %d specials)"
          % (out.name, rows, len(sections), comics, issues, extras))
    for s in sections:
        print("   %-20s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))


def preacher_note(r):
    """Publication context only — what else is in the book, never the plot.

    Both halves come off the Collected material cell. The specials are matched
    on the RAW wikitext because their titles contain the word "and" ("Cassidy
    – Blood and Whiskey"), which a comma-and-and split truncated."""
    bits = []
    fw = re.search(r"foreword by ([^,]+)", r["collects"])
    if fw:
        bits.append("foreword by " + fw.group(1).strip())
    extras = [e.strip() for e in
              re.findall(r"''Preacher Special: ((?:(?!'').)+)''", r["raw"])]
    if r["range"] is None:                 # the specials-only volume
        assert len(extras) == 3, extras
        bits.insert(0, "the %s miniseries, plus %s"
                    % (extras[0], and_join(extras[1:])))
    elif extras:
        assert len(extras) == 1, extras
        bits.insert(0, "with the %s special" % extras[0])
    return " · ".join(bits)


def transmet_note(r):
    """Only what the collected-editions table actually says about the book."""
    bits = []
    if r["old"] and r["old"] != r["range"]:
        bits.append("the first printing cut this one as %s" % dash(*r["old"]))
    if "Winter's Edge" in r["current"]:
        n = re.search(r"Winter's Edge\"? #(\d+)", r["current"])
        bits.append("also carries the short from Vertigo: Winter's Edge #%s"
                    % n.group(1))
    if "I Hate It Here" in r["current"]:
        bits.append("also carries the two specials, I Hate It Here and "
                    "Filth of the City")
    return " · ".join(bits)


if __name__ == "__main__":
    main()
