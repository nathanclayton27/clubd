#!/usr/bin/env python3
"""Generate properties/palme-dor.json — every top prize at Cannes since 1946.

    python tools/make_palme.py

One row per winning film from the decade tables of Wikipedia's Palme d'Or
article. The 1946–1954 winners open the list as their own section under the
award's original name, the Grand Prix du Festival International du Film; the
Palme proper runs from 1955 in decade sections, Best Picture style. Years
with several winners (1946 had eleven) get one row each, marked "joint
winner". Unanimous wins are noted where the article's own § legend marks
them.

Weighted by runtime (Wikidata P2047) — a Palme marathon is measured in hours,
and every single winner resolved to a real runtime, so nothing weighs a guess.

Rows carry `q`, a Wikidata work id, and on a festival list that is not a
nicety (CLU-347). This list dates a film by the year it won at Cannes and a
release list dates it by the year it came out, so the two disagree by a year as
a matter of course — All That Jazz is 1980 here and 1979 on Criterion and Best
Picture — and title+year, the only other key there is, can never bridge that.
Every award list is structurally unable to pair without an id.

The ids are the ones the source article's own wikilinks resolve to, which is the
Best Picture rule rather than a title guess: a title search reaches the wrong
film, a link cannot. Each was then checked against the entity itself — a label
or alias matching the title this list prints, P577 within three years of the
award year (the Cannes-to-release gap is routinely one and sometimes more), and
a credited person matching the winner column, which for the 2013 row is the two
lead actresses because that is who Cannes named alongside the director.

Data: tools/data/palme-dor.json, built by scratch/agent-canons/collect_palme.py;
work ids from tools/data/palme-dor-runtimes.json, resolved from the same
wikilinks the runtimes came from.
"""
import json
import pathlib
import re

SLUG = "palme-dor"
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = pathlib.Path(__file__).resolve().parent / "data" / "palme-dor.json"
QIDS = (pathlib.Path(__file__).resolve().parent / "data"
        / "palme-dor-runtimes.json")
OUT = ROOT / "properties" / ("%s.json" % SLUG)

# A work id the gate refused, and the row ships without one exactly as every row
# here did before. Empty today: all 102 winners passed. It stays as the place a
# refusal goes, because a wrong id would tick a film nobody watched on every
# other list that carries the real work.
NO_Q = {}

DECADES = [
    ("fifties", "The '50s, from Marty on", 1955, 1959,
     "1955 is where the trophy becomes the Palme d'Or."),
    ("sixties", "The '60s", 1960, 1969,
     "The 1968 festival was halted mid-run alongside the May 68 strikes and "
     "gave no prize."),
    ("seventies", "The '70s", 1970, 1979, ""),
    ("eighties", "The '80s", 1980, 1989, ""),
    ("nineties", "The '90s", 1990, 1999, ""),
    ("aughts", "The 2000s", 2000, 2009, ""),
    ("tens", "The 2010s", 2010, 2019, ""),
    ("twenties", "The 2020s", 2020, 2026,
     "No 2020 row: the festival was cancelled outright that year."),
]


def slug(t):
    import unicodedata
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    keep = "".join(c.lower() if (c.isalnum() and c.isascii()) else "-"
                   for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def items_for(years, qids):
    items = []
    for y in years:
        joint = len(y["films"]) > 1
        for f in y["films"]:
            bits = [f["by"]] if f["by"] else []
            if joint:
                bits.append("joint winner")
            if f["unanimous"]:
                bits.append("unanimous")
            q = (qids.get(f["target"]) or {}).get("qid")
            items.append({
                "id": "pd-%d-%s" % (y["year"], slug(f["t"])),
                "t": f["t"], "n": str(y["year"]),
                "w": round((f["runtime"] or 0) / 60.0, 2),
                **({"q": q} if q and f["target"] not in NO_Q else {}),
                **({"note": " · ".join(bits)} if bits else {}),
            })
    return items


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    qids = json.loads(QIDS.read_text(encoding="utf-8"))
    years = d["years"]
    gapyears = {g["year"] for g in d["gaps"] if g["year"]}
    assert {1968, 2020} <= gapyears
    assert all(f["runtime"] for y in years for f in y["films"])

    early = [y for y in years if y["year"] <= 1954]
    n_early = sum(len(y["films"]) for y in early)
    eh = sum(f["runtime"] for y in early for f in y["films"]) / 60.0
    sections = [{
        "id": "grand-prix", "title": "Grand Prix years",
        "sub": "1946–1954 · %d winners · %d hours" % (n_early, round(eh)),
        "intro": "Before 1955 the festival's top prize was the Grand Prix du "
                 "Festival International du Film — same award, earlier name. "
                 "The 1946 jury spread it across eleven films, 1947 across "
                 "five; no festival was held in 1948 or 1950.",
        "open": True,
        "items": items_for(early, qids),
    }]

    for key, title, lo, hi, intro in DECADES:
        got = [y for y in years if lo <= y["year"] <= hi]
        assert got, key
        items = items_for(got, qids)
        hours = sum(x["w"] for x in items)
        sec = {"id": key, "title": title,
               "sub": "%d winner%s · %d hours"
                      % (len(items), "" if len(items) == 1 else "s",
                         round(hours)),
               "items": items}
        if intro:
            sec["intro"] = intro
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), \
        "duplicate ids: %s" % sorted({i for i in ids if ids.count(i) > 1})[:6]
    total = sum(len(y["films"]) for y in years)
    assert len(ids) == total
    # Two rows sharing a work id would tie two winners of this same list to each
    # other in the sync map, and a film can win the Palme only once.
    qs = [x["q"] for s in sections for x in s["items"] if x.get("q")]
    assert len(qs) == len(set(qs)), \
        "two rows share a work id: %s" % sorted({q for q in qs
                                                 if qs.count(q) > 1})
    assert all(re.fullmatch(r"Q[1-9]\d*", q) for q in qs), \
        "malformed work id"
    assert len(qs) == total - len(NO_Q), (len(qs), total, len(NO_Q))
    stray = sorted(set(NO_Q) - {f["target"] for y in years for f in y["films"]})
    assert not stray, "NO_Q names winners this list does not have: %s" % stray
    hours = sum(x["w"] for s in sections for x in s["items"])

    prop = {
        "slug": SLUG,
        "title": "Palme d'Or",
        "subtitle": "every top prize at Cannes, 1946 on",
        "kind": "films",
        "popularity": 54,
        "year": "1946–2026",
        "blurb": "All %d films that took the top prize at Cannes — the Grand "
                 "Prix years included — about %d hours, one row per winner."
                 % (total, round(hours)),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": "#A6252D",
        "accentDark": "#E9BE4A",
        "tiers": False,
        "random": True,
        "notes": [
            ["Bar widths are runtimes.",
             "From Wikidata (duration, P2047), and every winner resolved to "
             "a real one — so the bar is honest about what a joint-winner "
             "year like 1946 actually costs you. Weighted because a Palme "
             "run is a time commitment, not a count."],
            ["Shared prizes are separate rows.",
             "Thirteen years split the award — each winner gets its own row "
             "and says so. Unanimous wins carry the article's own marker."],
            ["The 1939 festival that never was.",
             "Cannes was to debut in 1939 and was cancelled by the war; in "
             "2002 a jury watched the surviving competition entries and "
             "voted Union Pacific a retrospective Palme. It is a footnote, "
             "not a row."],
            "Winners from Wikipedia's Palme d'Or article; runtimes from "
            "Wikidata.",
        ],
        "sections": sections,
    }

    with OUT.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")
    print("wrote %s.json — %d winners, %d hours, %d work ids"
          % (SLUG, total, round(hours), len(qs)))
    for s in sections:
        print("   %-26s %3d  %s" % (s["title"], len(s["items"]), s["sub"][:44]))


if __name__ == "__main__":
    main()
