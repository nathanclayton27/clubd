#!/usr/bin/env python3
"""Generate properties/stephen-king.json.

    python3 tools/make_king.py

Every Stephen King novel in publication order, sectioned by decade —
including the seven published as Richard Bachman, which are marked. Story
collections, standalone novellas shelved elsewhere, nonfiction, children's
books and graphic novels are excluded; the list is exactly the Novels table
of Wikipedia's "Stephen King bibliography", via tools/data/king.json
(fetched and verified by scratch/king/fetch_wiki.py + parse_wiki.py).

The list is unweighted: page counts vary by edition and pretending to know
the hours would be worse, so each novel counts as one.

The Dark Tower books are the connected spine and carry "Dark Tower N of 8".
Row notes otherwise say only what the bibliography table says — pen names,
co-writers, declared sequels and twins. No connections from memory.

The generator asserts the table's row count against the article's own
infobox count and refuses to build if any note transform below fails to
match; a Wikipedia edit therefore breaks the build loudly instead of
drifting silently. (The article's lead says "67 novels/novellas" while its
infobox and table say 69. Since November 2026 the table folds the Uncut
Stand into The Stand's row, lists The End Times by its 2027 collected
edition, and adds Anything for Holly, dated 2027; see PIN, UNCUT and
NOT_OUT below for how each keeps the list's ids.)
"""
import json
import pathlib
import re

SLUG = "stephen-king"

# An id is where every reader's tick is stored, so a row the table now
# presents differently keeps the id it shipped with. Keyed by table title;
# main() asserts every key was found. Anything not given here is the
# table's own.
PIN = {
    # The table now dates it by the one-volume edition (1997) and notes the
    # 1996 serial; the row shipped under its serial year.
    "The Green Mile": {"id": "king-1996-the-green-mile"},
    # The table now lists only the collected edition, due 9 March 2027 (The
    # End Times article, fetched 2026-11-11). The serial it collects ran from
    # 19 November 2025 to late 2026 (same article) and is what this row has
    # always been, so it keeps its title, its label and its place.
    "The End Times: Volume One": {"id": "king-2025-the-end-times",
                                  "t": "The End Times", "n": "2025–26",
                                  "year": 2025},
}

# The table used to give the 1990 Complete & Uncut Edition a row of its own;
# it now carries it as a note on The Stand. The row stays, dated by The Stand
# article (Doubleday, May 1990; fetched 2026-11-11).
UNCUT = {"from": "The Stand", "frag": "The Complete and Uncut Edition",
         "title": "The Stand: The Complete and Uncut Edition", "year": 1990}

# Announced and dated, not out. The table gives publisher, ISBN, pages and
# notes all as "TBA"; main() asserts that, so the day the book is out the
# build stops and the row is reviewed. Not weighted, like every row here.
NOT_OUT = {"Anything for Holly": 2027}

# "First novel in The Dark Tower series" and so on: the marker
# "Dark Tower N of 8" already says it, and main() checks the ordinal agrees.
DT_ORDINAL = {"First": 1, "Second": 2, "Third": 3, "Fourth": 4, "Fifth": 5,
              "Sixth": 6, "Seventh": 7}

# Single-fragment rewrites, applied verbatim. Keys must match the cleaned
# table fragments in king.json exactly; main() asserts every one was used.
TRANSFORM = {
    "First novel published under pseudonym Richard Bachman, now out of "
    "print at the author's request":
        "as Richard Bachman · out of print at the author's request",
    "Published under pseudonym Richard Bachman": "as Richard Bachman",
    "First novel in the Bill Hodges Trilogy": "Bill Hodges 1 of 3",
    "Second novel in the Bill Hodges Trilogy": "Bill Hodges 2 of 3",
    "Third novel in the Bill Hodges Trilogy": "Bill Hodges 3 of 3",
    "The eighth Dark Tower novel, but chronologically set between the "
    "fourth and fifth volumes": "set between books 4 and 5",
    "First published as a limited edition in 1984, then for the mass "
    "market in 1987, by Viking Press":
        "First published as a limited edition in 1984, then for the mass "
        "market in 1987",
}

# Fragments allowed through untouched. Anything not listed anywhere raises,
# so a changed table cannot slip an unreviewed note into the page.
KEEP = {
    "Written with Peter Straub",
    "Written with Owen King",
    "Written with Richard Chizmar",
    "Sequel to The Shining",
    "Twin novel of The Regulators",
    "Illustrated by Bernie Wrightson",
    "First published as a six-part serial novel in 1996",
}

# Whole-note overrides for rows whose table fragments read poorly verbatim.
# Keyed by table title; main() asserts every key was found.
OVERRIDE = {
    "The Stand: The Complete and Uncut Edition":
        "The 1978 novel complete and uncut — optional here",
    "The Regulators":
        "as Richard Bachman · twin novel of Desperation",
    "Black House":
        "Written with Peter Straub · sequel to The Talisman",
    "Gwendy's Final Task":
        "Written with Richard Chizmar · the third Gwendy book",
    "The End Times: Volume One":
        "Serialized, written with Benjamin Percy as Claudia Inez Bachman · "
        "collected edition due 2027",
    "Other Worlds Than These":
        "Written with Peter Straub · the third Talisman book",
}

OPTIONAL = {"The Stand: The Complete and Uncut Edition"}


def slug(t):
    """ASCII-fold a title into an id fragment."""
    t = t.replace("'", "").replace("’", "")
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    keep = keep.encode("ascii", "ignore").decode("ascii")
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def main():
    here = pathlib.Path(__file__).resolve().parent
    data = json.loads((here / "data" / "king.json").read_text(encoding="utf-8"))
    table = data["novels"]

    # The list's rows: the table's, pinned where PIN says, the uncut Stand
    # carried over from The Stand's notes, then back into year order (a
    # stable sort, so the table's own order holds within a year).
    novels, used_p, uncut, soon = [], set(), [], set()
    for nv in table:
        nv = dict(nv, notes=list(nv["notes"]))
        if nv["title"] in PIN:
            used_p.add(nv["title"])
            nv["year"] = PIN[nv["title"]].get("year", nv["year"])
        if nv["title"] == UNCUT["from"] and UNCUT["frag"] in nv["notes"]:
            nv["notes"].remove(UNCUT["frag"])
            uncut.append({"year": UNCUT["year"], "n": str(UNCUT["year"]),
                          "title": UNCUT["title"], "bachman": False,
                          "dark_tower": None, "notes": []})
        if nv["title"] in NOT_OUT:
            assert nv["year"] == NOT_OUT[nv["title"]], nv
            assert nv["notes"] == ["TBA"], "out now? review %r" % nv
            nv["notes"] = []
            soon.add(nv["title"])
        novels.append(nv)
    assert used_p == set(PIN), set(PIN) - used_p
    assert soon == set(NOT_OUT), set(NOT_OUT) - soon
    assert len(uncut) == 1, "The Stand's row no longer notes the uncut edition"
    novels = sorted(novels + uncut, key=lambda nv: nv["year"])
    out_ = [nv for nv in novels if nv["title"] not in NOT_OUT]

    used_t, used_o, used_dt = set(), set(), set()

    def item(nv):
        frags = []
        if nv["dark_tower"]:
            frags.append("Dark Tower %d of 8" % nv["dark_tower"])
        if nv["title"] in NOT_OUT:
            frags.append("Not out yet — dated %d" % nv["year"])
        if nv["title"] in OVERRIDE:
            used_o.add(nv["title"])
            frags.append(OVERRIDE[nv["title"]])
        else:
            for f in nv["notes"]:
                dm = re.match(r"^(\w+) novel in The Dark Tower series$", f)
                if dm and DT_ORDINAL.get(dm.group(1)) == nv["dark_tower"]:
                    used_dt.add(nv["dark_tower"])  # the marker says it
                elif f in TRANSFORM:
                    used_t.add(f)
                    frags.append(TRANSFORM[f])
                elif f in KEEP:
                    frags.append(f)
                else:
                    raise SystemExit("unreviewed table note on %r: %r"
                                     % (nv["title"], f))
        pin = PIN.get(nv["title"], {})
        it = {"id": pin.get("id",
                            "king-%d-%s" % (nv["year"], slug(nv["title"]))),
              "t": pin.get("t", nv["title"]), "n": pin.get("n", nv["n"])}
        if nv["title"] in OPTIONAL:
            it["opt"] = 1
        if frags:
            it["note"] = " · ".join(frags)
        return it

    assert used_o | set(OPTIONAL) <= {nv["title"] for nv in novels}
    nb = sum(1 for nv in novels if nv["bachman"])

    sections = []
    for decade in range(1970, 2030, 10):
        got = [nv for nv in novels if decade <= nv["year"] < decade + 10]
        assert got, decade
        # a dated row counts in the range and the number, as on every list
        # with one; the tail says how many are not out
        sub = "%d–%d · %d novels" % (got[0]["year"],
                                     max(nv["year"] for nv in got), len(got))
        db = sum(1 for nv in got if nv["bachman"])
        if db:
            sub += " · %d as Bachman" % db
        ns = sum(1 for nv in got if nv["title"] in NOT_OUT)
        if ns:
            sub += " · %d not out yet" % ns
        sec = {"id": "d%02d" % (decade % 100), "title": "The %ds" % decade,
               "sub": sub, "items": [item(nv) for nv in got]}
        if decade == 1970:
            sec["open"] = True
        sections.append(sec)

    # every transform and override matched something — a silent no-op here
    # has caused real outages elsewhere in this repo
    assert used_t == set(TRANSFORM), set(TRANSFORM) - used_t
    assert used_o == set(OVERRIDE), set(OVERRIDE) - used_o
    assert used_dt == set(range(1, 8)), used_dt

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert all(i == slug(i) and i.isascii() for i in ids), "non-folded id"

    # the table's total, against the article's own count; the list is the
    # table plus the uncut Stand
    assert len(table) == data["infobox_novels"], \
        (len(table), data["infobox_novels"])
    assert len(ids) == len(novels) == len(table) + 1, (len(ids), len(table))
    assert nb == data["lead_bachman"] == 7, nb
    spine = [x for s in sections for x in s["items"]
             if x.get("note", "").startswith("Dark Tower ")]
    assert len(spine) == 8 and "Dark Tower 8 of 8" in spine[-1]["note"]

    # The headline counts every row, dated ones too, as every list with one
    # does: the table's novels plus the uncut Stand, which together are the
    # page counter's total. The blurb runs to the last book out and names
    # what is still to come.
    first, last = out_[0], out_[-1]
    soon_t = [nv["title"] for nv in novels if nv["title"] in NOT_OUT]
    assert len(table) + len(uncut) == len(ids)
    prop = {
        "slug": SLUG,
        "title": "Stephen King",
        "subtitle": "every novel, Bachman included",
        "kind": "books",
        "popularity": 80,
        "year": "%d–%d" % (first["year"], max(nv["year"] for nv in novels)),
        "blurb": "Every novel in publication order, %s to %s — %d novels and "
                 "the uncut Stand, the seven Richard Bachman books included, "
                 "each counting as one, with %s still to come."
                 % (first["title"], last["title"], len(table),
                    " and ".join(soon_t)),
        "unit": {"one": "novel", "many": "novels"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": "#4A1F1F",
        "accentDark": "#C97070",
        "tiers": False,
        "notes": [
            ["Novels only, as Wikipedia draws the line.",
             "This is the bibliography's novels table, whole — its %d "
             "rows, plus the uncut Stand (see below). "
             "Story collections, standalone novellas shelved elsewhere, "
             "nonfiction, children's books and graphic novels are out. A "
             "few short books the table counts as novels — Cycle of the "
             "Werewolf, Elevation, the Gwendy books — stay in because the "
             "table says so." % len(table)],
            ["The Bachman books are here.",
             "Seven novels came out under the pen name Richard Bachman; "
             "they sit in publication order with everything else, marked "
             "“as Richard Bachman”."],
            ["The Dark Tower is the spine.",
             "Eight books, marked “Dark Tower N of 8”, read here "
             "in publication order. The eighth, The Wind Through the "
             "Keyhole, arrived last but sits between books 4 and 5 in the "
             "story."],
            ["The Stand appears twice.",
             "The 1990 Complete & Uncut Edition has its own row — marked "
             "optional, since it is the 1978 novel restored rather than a "
             "new one."],
            ["Nothing is weighted.",
             "An eleven-hundred-page novel and a slim one each count as "
             "one. Page counts differ by edition, and pretending to know "
             "the hours would be worse."],
            "Titles, years and notes from Wikipedia's Stephen King "
            "bibliography — the novels table, verified against the "
            "article's own count of %d. Two rows lean on other Wikipedia "
            "articles: the uncut Stand is dated from The Stand, and The End "
            "Times serial is titled and dated from The End Times."
            % data["infobox_novels"],
        ],
        "sections": sections,
    }

    out = here.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d novels (%d as Bachman, 8 Dark Tower), %s"
          % (len(ids), nb, prop["year"]))
    for s in sections:
        print("   %-9s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
