"""Build properties/directors.json — the hub, one row per filmography.

CLU-79. Every row is a door: `into: "<slug>"` pointing at a director list that
already exists as a first-class property, which is what a close-up is (CLU-30).

NOTHING HERE IS TYPED BY HAND except the section prose and which slugs belong.
The counts, the year ranges and the hours are all read back out of the target
files, and the hours are not even written — `build.py` sums each target's own
runtimes into the row's weight, because a hand-written number rots the day a
filmography gains a film.

That is the whole argument for a weighted hub: fifteen marks standing for
hundreds of hours only mean something if the widths are proportional. On a
filmography every mark is a film and they are all about the same size, so the
widths carry nothing; here the widths are the entire message.
"""
import io
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROPS = ROOT / "properties"
THIS_YEAR = 2026

# Grouped by first feature, which is the only ordering that says something:
# it puts each filmography next to the industry it started inside.
SECTIONS = [
    ("before-the-studios-broke", "Before the studios broke",
     "The two who started inside the studio system and outlived it.",
     ["hitchcock", "kurosawa"]),
    ("new-hollywood", "New Hollywood and its neighbours",
     "First features from the fifties to the late seventies — the stretch "
     "that carries most of the hours on this page.",
     ["kubrick", "coppola", "scorsese", "spielberg", "carpenter",
      "david-lynch", "raimi"]),
    ("after-the-video-store", "After the video store",
     "First features from 1984 on.",
     ["coen-brothers", "tarantino", "fincher", "wes-anderson",
      "satoshi-kon", "nolan"]),
]


def read(slug):
    f = PROPS / (slug + ".json")
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8"))


def facts(slug):
    """Everything the hub row says, read out of the target itself."""
    d = read(slug)
    if d is None:
        return None
    items = [x for sec in d["sections"] for x in sec["items"]]
    core = [x for x in items if not x.get("opt")]
    nopt = len(items) - len(core)

    # the range is the filmography's, so optional shorts and codas do not
    # stretch it — that is what makes Kubrick read 1953 and not 1951
    years = []
    for x in core:
        m = re.search(r"\b(?:19|20)\d{2}\b", str(x.get("n", "") or ""))
        if m:
            years.append(int(m.group(0)))
    if years:
        lo, hi = min(years), max(years)
        span = "%d–" % lo if hi >= THIS_YEAR else "%d–%d" % (lo, hi)
    else:
        span = ""

    unit = (d.get("unit") or {}).get("many", "entries")
    note = ("%d %s" % (len(core), unit) if not nopt
            else "%d + %d optional" % (len(core), nopt))
    return {"title": d["title"], "n": span, "note": note,
            "first": min(years) if years else 9999}


def main():
    rows_by_sec, missing, total_core = [], [], 0
    for sid, stitle, sub, slugs in SECTIONS:
        items = []
        for slug in slugs:
            f = facts(slug)
            if f is None:
                missing.append(slug)
                continue
            total_core += 1
            items.append({
                "id": "dir-" + slug,
                "t": f["title"],
                "n": f["n"],
                "note": f["note"],
                # the door. build.py resolves it, derives the weight from the
                # target's own hours, and strips it if the file ever goes away
                "into": slug,
            })
        items.sort(key=lambda x: facts(x["into"])["first"])
        rows_by_sec.append((sid, stitle, sub, items))

    if missing:
        raise SystemExit("no property file for: %s" % ", ".join(missing))

    prop = {
        "slug": "directors",
        "title": "Directors",
        "subtitle": "%d filmographies" % total_core,
        "kind": "film, TV and anime filmographies",
        "year": "1925–",
        # A judgement call, not a derived one: above Sight & Sound (50) because
        # it is a front door to fifteen lists rather than one list, below
        # Criterion (63) because it is a way in rather than a destination.
        "popularity": 58,
        "unit": {"one": "filmography", "many": "filmographies"},
        # without this the stats bar falls back to the literal "Done"; every
        # row here is a body of films, so the honest past tense is "watched"
        "verb": {"base": "watch", "ing": "watching", "past": "watched"},
        "accent": "#5B4A9E",
        "accentDark": "#9C8AE0",
        "blurb": "Fifteen filmographies as one list. Each row opens the "
                 "director's own page, and finishing that page ticks the row "
                 "here.",
        "notes": [
            ["Every row is a door.",
             "Hover a row and a loupe appears with a fraction beside it — "
             "how far into that filmography you already are. Opening it takes "
             "you to the director's own page, which is an ordinary list with "
             "its own strip, its own schedule and its own clubs. Nothing about "
             "it changes because it is reachable from here."],
            ["Ticking works in both directions.",
             "Marking a row here ticks that director's whole page, and "
             "finishing that page marks the row here. Unticking a row only "
             "takes back the ticks this page put there — anything you had "
             "already marked yourself stays marked."],
            ["The widths are the point.",
             "Each mark is one filmography and its width is that "
             "filmography's real hours, summed from the films themselves and "
             "never typed here. Nicolas Cage against Quentin Tarantino is a "
             "sentence you can read off the strip before you read a number."],
            ["What the Sam Raimi row does not count.",
             "Its hours cover the films. The 29 Ash vs Evil Dead episodes on "
             "that list carry no published runtimes and are recorded as zero "
             "rather than guessed at, so the row understates him. A guessed "
             "half-hour would reach somebody's finish date, which is worse "
             "than a number that is honestly short."],
        ],
        "sections": [
            {"id": sid, "title": stitle, "sub": sub, "items": items}
            for sid, stitle, sub, items in rows_by_sec
        ],
    }

    out = PROPS / "directors.json"
    out.write_text(json.dumps(prop, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print("wrote %s — %d rows across %d sections"
          % (out.name, total_core, len(rows_by_sec)))
    for sid, stitle, sub, items in rows_by_sec:
        print("  %-24s %d" % (stitle[:24], len(items)))


if __name__ == "__main__":
    main()
