#!/usr/bin/env python3
"""Generate properties/alien-predator.json.

    python tools/make_alien.py

Every theatrical film of the Alien and Predator franchises in one
release-order run — Alien through Romulus, Predator through Badlands — plus
Prey, the two Alien vs. Predator crossovers, and the Alien: Earth television
series as a single season row.

Sources, machine-read rather than typed (see scratch/alien/fetch.py):
  - the title set from the wikitext of Wikipedia's "Alien (franchise)" and
    "Predator (franchise)" articles — every title is verified against them
  - film release dates and runtimes from Wikidata (P577, P2047)
  - the series' start date and episode count from Wikidata (P580, P1113); its
    per-episode runtime is not on Wikidata, so it comes from the series
    article's own infobox, as a range, and weighs in at the midpoint

Predator: Killer of Killers (2025, animated, streaming) was originally left
out as neither theatrical nor live-action; the group asked for it via the
Discord (2026-08), so it rides in the Disney era with its nature named on
the row.

Weights are runtime hours throughout. Sections are eras, not decades — the
shared twentieth century, the two crossovers, the 2010s returns, and the
Disney years — because the crossovers are the reason the two lines share a
page and deserve their own heading.
"""
import json
import pathlib
import unicodedata

SLUG = "alien-predator"

ERAS = [
    ("twentieth", "The twentieth century", 0, 1999,
     "Two monsters, four years apart — a haunted ship and a jungle that "
     "hunts back. Each line collects its sequels before the century turns."),
    ("crossovers", "The crossovers", 2000, 2009,
     "The two lines meet, twice. Neither film is anyone's favourite, but "
     "they are why these franchises share a page."),
    ("returns", "Returns and prequels", 2010, 2019,
     "Both lines reach back for what made them work — Predator with new "
     "hunts, Alien with prequels asking where it all began."),
    ("disney", "The Disney era", 2020, 9999,
     "A new studio and a lighter touch: stripped-back films that stand "
     "alone, and the franchise's first television series."),
]

# rows whose release was a stream rather than a cinema — kept, and said so
STREAMING_NOTE = "Streaming release"


# Curly punctuation, straightened to the ASCII this fold already handles.
# CLU-430: `encode("ascii", "ignore")` DROPS a curly apostrophe and keeps a
# straight one as a dash, so `Child’s Play` folds to `childs-play` while
# `Child's Play` folds to `child-s-play`. An id is somebody’s tick, so two
# spellings of one title must never reach two ids. Straightening is the
# correction THIS direction needs — the opposite of the folds that drop the
# straight form — and it leaves every id this list has shipped where it is.
STRAIGHTEN = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'})


def fold(t):
    """ASCII-fold a title into an id fragment."""
    t = unicodedata.normalize("NFKD", t.translate(STRAIGHTEN))
    t = t.encode("ascii", "ignore").decode()
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def era_of(year):
    for key, _, lo, hi, _ in ERAS:
        if lo <= year <= hi:
            return key
    raise AssertionError(year)


def main():
    data = pathlib.Path(__file__).resolve().parent / "data" / "alien.json"
    d = json.loads(data.read_text(encoding="utf-8"))

    entries = []

    for f in d["films"]:
        year = int(f["released"][:4])
        bits = []
        if f["line"] == "Crossover":
            bits.append("Crossover")
        if f.get("extra"):
            bits.append(f["extra"])
        if f["kind"] == "streaming":
            bits.append(STREAMING_NOTE)
        entries.append({
            "id": "ap-f-%d-%s" % (year, fold(f["t"])),
            "t": f["t"], "n": str(year),
            "w": round(f["runtime"] / 60.0, 2),
            "note": " · ".join(bits),
            "date": f["released"], "year": year, "kind": "film",
            "tags": [f["line"]],
        })

    ep_range = None
    for s in d["series"]:
        year = int(s["start"][:4])
        if s.get("ep_minutes"):
            ep_min = s["ep_minutes"]
            note_len = "%d minutes each" % ep_min
        else:
            lo, hi = s["ep_minutes_range"]
            ep_min = (lo + hi) / 2.0
            ep_range = (lo, hi)
            note_len = "%d–%d minutes each" % (lo, hi)
        entries.append({
            "id": "ap-t-%d-%s-s1" % (year, fold(s["t"])),
            "t": s["t"], "n": str(year),
            "w": round(s["episodes"] * ep_min / 60.0, 2),
            "note": "Television · 1 season, %d episodes · %s"
                    % (s["episodes"], note_len),
            "date": s["start"], "year": year, "kind": "season",
            "tags": [s["line"]],
        })

    entries.sort(key=lambda e: e["date"])

    sections = []
    for key, title, lo, hi, intro in ERAS:
        got = [e for e in entries if era_of(e["year"]) == key]
        assert got, "empty era: %s" % key
        nf = sum(1 for e in got if e["kind"] == "film")
        ns = sum(1 for e in got if e["kind"] == "season")
        parts = ["%d film%s" % (nf, "" if nf == 1 else "s") if nf else "",
                 "%d season%s" % (ns, "" if ns == 1 else "s") if ns else ""]
        span = ("%d–" % got[0]["year"] if hi == 9999
                else "%d–%d" % (got[0]["year"], got[-1]["year"]))
        sec = {"id": key, "title": title,
               "sub": "%s · %s · %d hours"
                      % (span, ", ".join(p for p in parts if p),
                         round(sum(e["w"] for e in got))),
               "intro": intro,
               "items": [{k: v for k, v in e.items()
                          if k in ("id", "t", "n", "w", "tags")
                          or (k == "note" and v)}
                         for e in got]}
        if key == "twentieth":
            sec["open"] = True
        assert all(a["date"] <= b["date"] for a, b in zip(got, got[1:])), \
            "%s is out of release order" % title
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), \
        "duplicate ids: %s" % sorted({i for i in ids if ids.count(i) > 1})[:5]
    assert len(ids) == len(entries) == len(d["films"]) + len(d["series"]), \
        (len(ids), len(entries))
    assert all(i == fold(i) for i in ids), "non-ASCII id"
    assert all(x["w"] > 0 for s in sections for x in s["items"]), "zero weight"
    lines = {t for e in entries for t in e["tags"]}
    assert lines == {"Alien", "Predator", "Crossover"}, lines

    hours = sum(e["w"] for e in entries)
    by = {ln: sum(1 for e in entries
                  if e["kind"] == "film" and e["tags"] == [ln])
          for ln in ("Alien", "Predator", "Crossover")}
    nf = sum(by.values())
    ns = sum(1 for e in entries if e["kind"] == "season")

    season_note = ("Alien: Earth is one row for the whole season, "
                   "%d episodes counted at the midpoint of the "
                   "%d–%d-minute range its own infobox gives."
                   % (d["series"][0]["episodes"], *ep_range) if ep_range else
                   "Alien: Earth is one row for the whole season.")

    prop = {
        "slug": SLUG,
        "title": "Alien & Predator",
        "subtitle": "both franchises in one release-order run",
        "kind": "films",
        "popularity": 76,
        "year": "1979–",
        "blurb": "%d films — %d Alien, %d Predator, %d crossovers — and one "
                 "television season, in the order they came out: about %d "
                 "hours." % (nf, by["Alien"], by["Predator"], by["Crossover"],
                             round(hours)),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#1E3A2E",
        "accentDark": "#7FBFA0",
        "tiers": False,
        "filter": {
            "key": "line", "label": "Show", "mode": "exclude",
            "values": ["Alien", "Predator", "Crossover"]
        },
        "notes": [
            ["One run, two franchises.",
             "The lines are interleaved exactly as they came out, because "
             "that is the order the rumour grew in. The chips at the top "
             "hide a whole line — Alien, Predator, or the crossovers — so "
             "either franchise can be watched on its own. Hiding a line "
             "redraws the bar; it never unticks anything."],
            ["Sections are eras, not decades.",
             "The shared twentieth century, the two crossovers, the 2010s "
             "returns, and the Disney years. The crossovers get their own "
             "heading because they are the reason these two series share a "
             "page."],
            ["Weights are runtimes.",
             "A film's width in the bar is its length in hours. "
             + season_note],
            ["The animated one is in.",
             "Predator: Killer of Killers, the animated anthology, joined "
             "at the group's request — it sits in the Disney era with its "
             "nature on the row. The two Alien vs. Predator films stay, "
             "marked Crossover, because they came out in the middle of "
             "everything."],
            "Film dates and runtimes from Wikidata; the title set and the "
            "season's shape from Wikipedia's franchise articles.",
        ],
        "sections": sections,
    }

    out = (pathlib.Path(__file__).resolve().parent.parent / "properties"
           / ("%s.json" % SLUG))
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d rows (%d films + %d season), %.1f hours"
          % (len(sections), len(ids), nf, ns, hours))
    print("  by line: %d Alien, %d Predator, %d crossovers (+1 Alien TV)"
          % (by["Alien"], by["Predator"], by["Crossover"]))
    for s in sections:
        print("   %-24s %2d  %s" % (s["title"][:24], len(s["items"]),
                                    s["sub"]))


if __name__ == "__main__":
    main()
