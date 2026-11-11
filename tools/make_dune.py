#!/usr/bin/env python3
"""Generate properties/dune.json.

    python tools/make_dune.py

Three sections. Frank Herbert's six novels in publication order — the
numbered Dune list of Wikipedia's Frank Herbert bibliography. The Brian
Herbert / Kevin J. Anderson continuations as one optional row per book,
publication order, each noted with its series and nothing else — the lists
in Wikipedia's "Dune prequel series" article plus the two Dune 7 sequels
from the franchise article's own prose. Then every screen Dune, weighted by
runtime from Wikidata (P2047): Lynch 1984, the two Sci Fi Channel
miniseries, and Villeneuve's three parts.

Book rows are unweighted — page counts aren't hours. Dune: Part Three is a
row from the day the franchise article's film table dates it (18 December
2026): until it opens it carries an explicit w: 0 and a "not out yet" note,
because a dated announcement belongs on the list and an unwatched film has
no runtime to weigh (CLU-599). The Dune: Prophecy TV series is not a row;
the notes say so. Data: tools/data/dune.json, built and asserted by
scratch/agent-books/parse_dune.py, which gives Part Three its minutes only
once its date has passed.

WHY 23 OF THE 29 ROWS CARRY NO NUMBER, written down so a weight audit does
not have to re-derive it. All 23 are books: Frank Herbert's six and the
seventeen continuations. There is no source that gives a book an honest
hour figure — page counts differ by edition, reading speeds differ by
reader, and every other book list in this repo (middle-earth, cosmere,
discworld, stephen-king, wheel-of-time, sherlock-holmes) refuses the same
way. The six screen rows ARE weighted, from Wikidata P2047 (Part Three at
an explicit zero until it opens), so the strip
deliberately shows reading and watching at different scales; the third
property note says so out loud. An unweighted row counts as one entry
downstream, which is a floor, not a claim about how long Dune takes to
read. Whether the screen rows should give up their runtimes so the whole
list counts one-per-row instead — the way raimi and x-files do — is a
design call for the list's owner, not something to change quietly here.
"""
import datetime
import json
import pathlib

SLUG = "dune"

# Leads an unreleased screen row's note, worded as the villeneuve list words
# the same film, so the two copies of Part Three read alike.
NOT_OUT = "Not out yet — due %s, and the bar stays empty until it opens"

MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")


def longdate(iso):
    d = datetime.date.fromisoformat(iso)
    return "%d %s %d" % (d.day, MONTHS[d.month - 1], d.year)

SERIES_NOTE = {
    "Prelude to Dune": "Prelude to Dune — set before Dune",
    "Legends of Dune": "Legends of Dune",
    "Dune 7": "Completes the original series, from Frank Herbert's "
              "Dune 7 outline",
    "Heroes of Dune": "Heroes of Dune — set between the original novels",
    "Great Schools of Dune": "Great Schools of Dune",
    "The Caladan Trilogy": "The Caladan Trilogy",
}


def slugify(t):
    # CLU-430. This fold DELETES a straight apostrophe (`The Emperor's Soul`
    # gives the-emperors-soul) and left U+2019 alone, so a curly one reached
    # the isalnum test below and became a dash instead. Two spellings of one
    # title would reach two ids, and an id is the `item_id` every tick and
    # thumb is stored against — moving one unticks the row for everyone
    # holding it. Drop both forms: that is the correction THIS direction
    # needs, and the opposite of what the folds that dash a straight
    # apostrophe need.
    t = t.replace("'", "").replace("’", "").replace("‘", "")
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    keep = keep.encode("ascii", "ignore").decode("ascii")
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def main():
    here = pathlib.Path(__file__).resolve().parent
    data = json.loads((here / "data" / "dune.json").read_text(encoding="utf-8"))
    core, conts, screen = data["core"], data["continuations"], data["screen"]
    assert len(core) == 6 and len(conts) == 17 and len(screen) == 6

    core_items = [{"id": "dune-%d-%s" % (b["year"], slugify(b["title"])),
                   "t": b["title"], "n": str(b["year"])} for b in core]

    used = set()
    cont_items = []
    for b in conts:
        used.add(b["series"])
        disp = b["title"]
        if disp.startswith("Dune: "):
            disp = disp[len("Dune: "):]
        cont_items.append({"id": "dune-c-%d-%s" % (b["year"], slugify(disp)),
                           "t": disp, "n": str(b["year"]),
                           "note": SERIES_NOTE[b["series"]], "opt": 1})
    assert used == set(SERIES_NOTE), set(SERIES_NOTE) ^ used

    screen_items = []
    coming = []
    for s in screen:
        item = {"id": "dune-s-%d-%s" % (s["year"], slugify(s["title"])),
                "t": s["title"], "n": str(s["year"])}
        if s["minutes"] is None:
            # dated and not out (CLU-599): an explicit zero, and a note that
            # says why the bar is empty and when it fills
            item["w"] = 0
            item["note"] = "%s · %s" % (NOT_OUT % longdate(s["due"]),
                                        s["note"])
            coming.append(s)
        else:
            item["w"] = round(s["minutes"] / 60.0, 2)
            item["note"] = "%s · %d min" % (s["note"], s["minutes"])
        screen_items.append(item)
    assert [s["title"] for s in coming] in ([], ["Dune: Part Three"]), coming
    mins = {s["key"]: s["minutes"] for s in screen}
    dv = [mins[k] for k in ("dune-2021", "dune-part-two", "dune-part-three")
          if mins[k] is not None]
    dv_text = ", ".join(str(m) for m in dv[:-1]) + " and %d" % dv[-1]
    last = max(s["year"] for s in screen)

    hours = sum(x["w"] for x in screen_items)
    sections = [
        {"id": "herbert", "title": "Frank Herbert's six",
         "sub": "1965–1985 · the original novels", "open": True,
         "intro": "Publication order, Dune to Chapterhouse: Dune. Everything "
                  "else on the page hangs off these.",
         "items": core_items},
        {"id": "continuations", "title": "The continuations",
         "sub": "1999–2023 · 17 books · Brian Herbert & Kevin J. Anderson · "
                "optional",
         "intro": "One row per book, publication order, each marked with its "
                  "series. Read none, some, or all — they are optional rows "
                  "and count toward nothing unless ticked.",
         "items": cont_items},
        {"id": "screen", "title": "Dune on screen",
         "sub": "1984–%d · %d adaptations · about %.0f hours%s"
                % (last, len(screen_items), hours,
                   " · %d not out yet" % len(coming) if coming else ""),
         "intro": "Weighted by runtime."
                  + (" Villeneuve's Part Three is dated %s and sits here "
                     "with an empty bar until it opens."
                     % longdate(coming[0]["due"]) if coming else ""),
         "items": screen_items},
    ]

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == 29 and len(set(ids)) == 29, "bad ids"
    assert all(i == slugify(i) and i.isascii() for i in ids)
    assert 16 < hours < 17, hours  # 988 min of released screen Dune
    assert all(x.get("opt") for x in cont_items)
    # books carry no hours, screen rows all do — see the docstring
    assert not any("w" in x for x in core_items + cont_items), \
        "a book row grew an hour figure; there is no source for one"
    assert all("w" in x for x in screen_items), \
        "a screen row lost its runtime"

    prop = {
        "slug": SLUG,
        "title": "Dune",
        "subtitle": "the novels, the continuations, the screen versions",
        "kind": "books & films",
        "popularity": 73,
        "year": "1965–%d" % last,
        "blurb": "Frank Herbert's six novels in publication order, the "
                 "seventeen Brian Herbert & Kevin J. Anderson continuations "
                 "as optional rows, and every screen Dune from Lynch to "
                 "Villeneuve, weighted by runtime.",
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "read", "past": "done", "ing": "working through"},
        "accent": "#9C6414",
        "accentDark": "#7FB4E8",
        "tiers": False,
        "notes": [
            ["The six are the spine.",
             "Frank Herbert's novels, publication order, each counting as "
             "one — page counts differ by edition and pretending to know "
             "the hours would be worse."],
            ["The continuations are optional and unranked.",
             "Seventeen books by Brian Herbert and Kevin J. Anderson, one "
             "row each in publication order. Rows say which series a book "
             "belongs to and nothing more; whether to read them is your "
             "argument to have, not this page's."],
            ["Screen rows are weighted by runtime.",
             "From Wikidata: Lynch's %d-minute film, the two three-part "
             "Sci Fi Channel miniseries at %d and %d minutes, and "
             "Villeneuve's %s. Book rows stay unweighted, so the "
             "strip shows reading and watching at different scales on "
             "purpose." % (mins["dune-1984"], mins["dune-2000"],
                           mins["dune-cod-2003"], dv_text)],
            ["Not here.",
             "The Dune: Prophecy series, the short stories, the "
             "Dune Encyclopedia and the games are outside this list's "
             "scope."],
            "Novels and years from Wikipedia's Frank Herbert bibliography "
            "and Dune prequel series articles; screen list and dates from "
            "the Dune franchise article; runtimes from Wikidata.",
        ],
        "sections": sections,
    }

    out = here.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json — %d rows (%d core, %d continuations, %d screen, "
          "%.1f screen hours)" % (SLUG, len(ids), len(core_items),
                                  len(cont_items), len(screen_items), hours))
    for s in sections:
        print("   %-24s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
