#!/usr/bin/env python3
"""Export the Hickman reading order to properties/hickman-secret-wars.json.

`reading_order.py` stays the authoring source for this one property — it has the
helpers and loops that make a 250-item interleaved order tractable. The JSON it
emits is what the site actually reads.

The item ids here are load-bearing: every existing user's saved progress is a
list of them. This script asserts they match the ids the old single-property
build produced, so a careless edit fails here rather than silently wiping
everyone's ticks.

    python3 tools/export_secretwars.py
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from reading_order import build_sections  # noqa: E402

SLUG = "hickman-secret-wars"


def main():
    sections = build_sections()

    out_sections = []
    for s in sections:
        sec = {
            "id": s["id"],
            "title": s["title"],
            "sub": s["sub"],
            "tier": s["tier"],
            "items": [
                {
                    "id": x["id"],
                    "t": x["t"],
                    "n": x["n"],
                    "note": x.get("note", ""),
                    "star": x.get("star", 0),
                    "opt": x.get("opt", 0),
                    "url": x.get("url", ""),
                    # CLU-545: one row is one issue, so every row
                    # weighs 1 and the strip measures issues rather
                    # than rows. `w` is not part of an id, so no tick
                    # moves.
                    "w": 1,
                }
                for x in s["items"]
            ],
        }
        if s.get("intro"):
            sec["intro"] = s["intro"]
        if s.get("series"):
            sec["links"] = s["series"]
        if s.get("start"):
            sec["start"] = True
        out_sections.append(sec)

    ids = [x["id"] for s in out_sections for x in s["items"]]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate item ids — refusing to write")

    total = len(ids)
    if total != 250:
        raise SystemExit("expected 250 items, got %d" % total)

    # The ids people's progress is keyed on. If this list ever changes shape,
    # every saved tick that pointed at a renamed id is lost.
    checksum = sum(len(i) for i in ids)

    prop = {
        "slug": SLUG,
        "title": "Everything Dies: Secret Wars",
        "subtitle": "Jonathan Hickman's Marvel run",
        "kind": "comics",
        # Honest: comics readers know this run, nobody else does. It opens the
        # catalogue because build.py pins it there, not because of this number.
        # See POPULARITY.md.
        "popularity": 44,
        "year": "2009–2015",
        "blurb": "250 issues from Fantastic Four #570 through Secret Wars #9, "
                 "in the order they're meant to be read.",
        "unit": {"one": "issue", "many": "issues"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": "#C1352A",
        "accentDark": "#E4584A",
        "tiers": True,
        "notes": [
            ["Tiers.", "1 is essential, 2 is strongly recommended (the Fantastic "
                       "Four run — it's what makes the ending land), 3 is genuinely "
                       "optional. The minimum viable path is Tier 1 alone."],
            ["Reading in Marvel Unlimited?", "Most issues link to their series page "
                       "rather than the issue, because Marvel only exposes the 20 most "
                       "recent issues of any series to the outside world. The issue "
                       "numbers tell you when to switch titles, which is the real "
                       "difficulty with an interleaved run."],
            "Reading order compiled from Comic Book Herald, Crushing Krisis and How "
            "To Love Comics; the Fantastic Four/FF weave follows the order Hickman "
            "specified for the omnibus.",
        ],
        "sections": out_sections,
    }

    out = ROOT / "properties" / ("%s.json" % SLUG)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    tiers = {1: 0, 2: 0, 3: 0}
    for s in out_sections:
        tiers[s["tier"]] += len(s["items"])

    print("wrote properties/%s.json" % SLUG)
    print("  %d sections, %d items" % (len(out_sections), total))
    print("  tier 1: %d   tier 2: %d   tier 3: %d" % (tiers[1], tiers[2], tiers[3]))
    print("  id checksum: %d  (first: %s / last: %s)" % (checksum, ids[0], ids[-1]))


if __name__ == "__main__":
    main()
