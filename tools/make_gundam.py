#!/usr/bin/env python3
"""Generate properties/gundam.json.

    python tools/make_gundam.py

One franchise, organised by continuity, the shape the group chose: the
Universal Century in release order, then every alternate universe, then the
major manga. One row per series, film or OVA — never per episode. Games are
out by request, and so are the live-action pieces, the SD comedy spinoffs,
the promotional shorts, compilation re-cuts of series already listed, and
anything announced without a date. Announced work the media table dates —
even to a bare year — ships as a row that says it is not out yet and weighs
zero. Its due date is kept to the precision the source gives (a day, a month
or a year), and main() asserts it against the clock, so the build fails once
it passes and the row gets its real numbers.

Everything numeric comes from tools/data/gundam.json, transcribed from
Wikipedia's franchise media table (episode counts, dates, in-universe
calendars), the individual film articles (runtimes), and the manga list plus
the individual manga articles (serialization dates, volume counts). Series
weigh episodes x 24 minutes in hours; films weigh their runtime; manga weigh
zero. The second Hathaway film has no runtime on English Wikipedia yet, so its
runtime is the one the Japanese Hathaway article's infobox gives.
"""
import datetime
import json
import unicodedata
import pathlib

SLUG = "gundam"

DATA = pathlib.Path(__file__).resolve().parent / "data" / "gundam.json"
OUT = pathlib.Path(__file__).resolve().parent.parent / "properties" / (SLUG + ".json")

EXPECTED = {"uc": 20, "au": 22, "manga": 6}

# Appended to the note of a row the source dates but nobody can have watched,
# in the wording gears-of-war, silent-hill and dune use.
NOT_OUT = "Not out yet — due %s"

MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")


def due_date(due):
    """Read a due date given as "2027-01-15", "2027-04" or "2027".

    Returns the words for the note and the first day the entry is surely
    out: the day itself, else the first of the next month, else 1 January
    of the next year.
    """
    parts = [int(p) for p in str(due).split("-")]
    if len(parts) == 3:
        d = datetime.date(*parts)
        return "%d %s %d" % (d.day, MONTHS[d.month - 1], d.year), d
    if len(parts) == 2:
        y, m = parts
        assert 1 <= m <= 12, "bad due month %r" % due
        return "%s %d" % (MONTHS[m - 1], y), datetime.date(y + m // 12, m % 12 + 1, 1)
    assert len(parts) == 1, "bad due date %r" % due
    return "%d" % parts[0], datetime.date(parts[0] + 1, 1, 1)


def slugify(t):
    # ids must satisfy build.py's [A-Za-z][A-Za-z0-9_-]* rule, so accented
    # titles are folded to ASCII first — École du Ciel was shipping an é
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    keep = "".join(c.lower() if ("a" <= c.lower() <= "z" or c.isdigit()) else "-"
                   for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def weight(e):
    if "eps" in e:
        return round(e["eps"] * 24 / 60.0, 2)
    if e.get("min"):
        return round(e["min"] / 60.0, 2)
    return 0


def note(e):
    if "eps" in e:
        head = "%s, %d episodes" % (e["media"], e["eps"])
    elif e.get("min"):
        head = "%s, %d min" % (e["media"], e["min"])
    else:
        head = e["media"]
    bits = [head]
    if e.get("cal"):
        bits.append(e["cal"])
    if e.get("extra"):
        bits.append(e["extra"])
    if e.get("due"):
        bits.append(NOT_OUT % due_date(e["due"])[0])
    return " · ".join(bits)


def row(e):
    # an unreleased row pins its id in the data, so a slipped year or a
    # retitle on release cannot move where everyone's tick is stored
    x = {
        "id": e.get("id") or "gdm-%d-%s" % (e["year"], slugify(e["title"])),
        "t": e["title"],
        "n": str(e["year"]),
        "w": weight(e),
        "note": note(e),
    }
    if e.get("opt"):
        x["opt"] = 1
    return x


def manga_row(e):
    head = "Manga"
    if e.get("vols"):
        head += ", %d volumes" % e["vols"]
    x = {
        "id": "gdm-%d-%s" % (e["year"], slugify(e["title"])),
        "t": e["title"],
        "n": str(e["year"]),
        "w": 0,
        "note": " · ".join([head + " (%s)" % e["span"], e["extra"]]),
    }
    return x


def hours(entries):
    return sum(weight(e) for e in entries)


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    uc, au, manga = data["uc"], data["au"], data["manga"]

    for key, want in EXPECTED.items():
        got = len(data[key])
        assert got == want, "%s: expected %d entries, got %d" % (key, want, got)
    for key in ("uc", "au", "manga"):
        years = [e["year"] for e in data[key]]
        assert years == sorted(years), "%s is out of release order" % key

    today = datetime.date.today()
    for e in uc + au:
        if not e.get("due"):
            continue
        words, out_by = due_date(e["due"])
        assert today < out_by, (
            "%s was due %s: refetch it and give it its real numbers"
            % (e["title"], words))
        assert int(str(e["due"])[:4]) == e["year"], (
            "%s is due %s but its row says %d" % (e["title"], words, e["year"]))
        assert weight(e) == 0 and not e.get("eps") and not e.get("min"), (
            "%s is not out yet but carries a weight" % e["title"])
        assert e.get("id"), "%s is not out yet and needs a pinned id" % e["title"]

    uc_h, au_h = hours(uc), hours(au)

    sections = [
        {
            "id": "uc",
            "title": "Universal Century",
            "sub": "1979– · %d entries · about %d hours" % (len(uc), round(uc_h)),
            "intro": "One timeline told out of order. Rows run in release "
                     "order; each note carries the in-universe year, so UC "
                     "0079 sits next to entries made forty years apart.",
            "links": [
                {"label": "The media list",
                 "url": "https://en.wikipedia.org/wiki/Gundam#Media"},
                {"label": "Gundam.info",
                 "url": "https://en.gundam.info/"},
            ],
            "items": [row(e) for e in uc],
        },
        {
            "id": "au",
            "title": "Alternate universes",
            "sub": "1994– · %d entries · about %d hours" % (len(au), round(au_h)),
            "intro": "Each universe stands alone and needs nothing from the "
                     "Universal Century. The notes say which entry starts "
                     "each line. Build entries are hobby spin-offs, marked "
                     "optional.",
            "links": [
                {"label": "The media list",
                 "url": "https://en.wikipedia.org/wiki/Gundam#Media"},
                {"label": "Gundam.info",
                 "url": "https://en.gundam.info/"},
            ],
            "items": [row(e) for e in au],
        },
        {
            "id": "manga",
            "title": "Manga",
            "sub": "1994– · %d series · unweighted" % len(manga),
            "intro": "The major ones only. They weigh nothing, so they sit "
                     "outside the hour counts.",
            "links": [
                {"label": "The manga list",
                 "url": "https://en.wikipedia.org/wiki/"
                        "List_of_Gundam_manga_and_novels"},
            ],
            "items": [manga_row(e) for e in manga],
        },
    ]

    ids = [x["id"] for s in sections for x in s["items"]]
    total = len(ids)
    assert len(ids) == len(set(ids)), "duplicate item ids"
    assert total == sum(EXPECTED.values()), (total, EXPECTED)
    assert all(x["w"] >= 0 for s in sections for x in s["items"])

    prop = {
        "slug": SLUG,
        "title": "Gundam",
        "subtitle": "the Universal Century and every alternate universe",
        "kind": "anime & manga",
        "popularity": 65,
        "year": "1979–",
        "blurb": "%d entries across every Gundam continuity: the Universal "
                 "Century in release order, the alternate universes, and the "
                 "major manga." % total,
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#3F4E9E",
        "accentDark": "#8E9BE8",
        "tiers": False,
        "notes": [
            ["One timeline, out of order.",
             "The Universal Century is a single continuity released out of "
             "sequence, so the section runs in release order and every row's "
             "note carries its in-universe year — UC 0079 and so on. Watch "
             "by release or by calendar; the notes support either."],
            ["Alternate universes stand alone.",
             "Every other calendar — Future Century, After Colony, After "
             "War, Correct Century, Cosmic Era, Anno Domini, Advanced "
             "Generation, Regild Century, Post Disaster, Ad Stella, After "
             "Apocalypse — starts "
             "fresh, and the notes say which entry opens each line. "
             "GQuuuuuuX is the exception: a branch of the Universal Century "
             "rather than a calendar of its own."],
            ["No games.", "Excluded by request."],
            ["Also left out.",
             "Live-action (G-Saviour, Gundam Build Real, the announced "
             "film), the SD comedy spinoffs, promotional shorts (Evolve, "
             "Twilight AXIS, the Battlogues and their like), Build "
             "Metaverse, compilation re-cuts of series already listed, and "
             "anything announced without a date."],
            ["Where the numbers come from.",
             "Episode counts, dates and calendars are from Wikipedia's "
             "franchise media list; film runtimes from each film's article. "
             "Series weigh episodes × 24 minutes, so Unicorn and The Origin "
             "— hour-long episodes — count light. The second Hathaway film's "
             "runtime is from Japanese Wikipedia; the English article has "
             "none yet. Entries not out yet weigh nothing. Manga weigh "
             "zero by design."],
        ],
        "sections": sections,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d entries, %.0f hours weighted"
          % (len(sections), total, uc_h + au_h))
    for s in sections:
        w = sum(x["w"] for x in s["items"])
        print("   %-22s %2d rows  %6.1f h" % (s["title"], len(s["items"]), w))


if __name__ == "__main__":
    main()
