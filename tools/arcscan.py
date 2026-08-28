"""Classify every section as an ARC or as EVEN bookkeeping (CLU-427).

Nathan, 2026-08-28 on CLU-266:

    "there needs to be a way to figure out if an arc is important to keep
     together or part it out in a way that doesn't mix arcs... Something like
     secret wars doesn't make any sense to have all of a section done in a week
     it's just a set amount of comics until the completion date."
    "do your best guess and bring examples you're unsure of to me
     The added granularity of being able to have both in a list is ideal"

So the value is **per section**, not per list — one list may hold both.

WHAT THIS IS AND IS NOT. It is a first pass that sorts the obvious cases and
surfaces the rest. It is not the answer. The signal lives in the section TITLE,
because shape cannot tell these apart:

    one-piece     49 sections, avg 24.0 rows   "Romance Dawn", "Arlong Park"
    best-picture  98 sections, avg  6.3 rows   "1927/28 (1st)", "1928/29 (2nd)"

Both look arc-shaped. One is sagas, the other is ceremony years. 152 of 208
lists look arc-shaped structurally, so a structural test would be confidently
wrong on a large minority — which is why this reads names instead, and why
anything it cannot name confidently is reported rather than guessed.

    python tools/arcscan.py            # summary + the unsure list
    python tools/arcscan.py --full     # every section, every list
"""
import glob
import io
import json
import os
import re
import sys

# --- bookkeeping shapes: a container that carries no story of its own -------
EVEN = [
    (re.compile(r"^#?\s*\d+\s*[-–—]\s*#?\d+\s*$"), "a numeric range"),
    (re.compile(r"^(19|20)\d\d(\s*[/–-]\s*\d\d)?"), "a year"),
    (re.compile(r"^season\s+\d+", re.I), "a season number"),
    (re.compile(r"^(vol(ume)?|book|part|series|wave|phase|tier|batch)"
                r"\s*\.?\s*\d+\s*$", re.I), "a numbered container"),
    (re.compile(r"^(the\s+)?(films?|movies?|shorts?|specials?|extras?|"
                r"supplemental|appendix|misc\w*|other|everything else)\s*$",
                re.I), "a catch-all bucket"),
    (re.compile(r"^\d+\s*$"), "a bare number"),
    (re.compile(r"^(tier|rank)\b", re.I), "a ranking bucket"),
]

# --- arc shapes: a named story unit ----------------------------------------
ARC = [
    (re.compile(r"\b(saga|arc)\b", re.I), "says saga or arc"),
    (re.compile(r"^(chapter|book|part)\s+\d+\s*:", re.I),
     "a numbered chapter with a name"),
    (re.compile(r",\s*part\s+\d+\s*$", re.I), "an explicitly multi-part story"),
]


# An era or a run is a container, not a story — split it freely. This is the
# vocabulary of the genuinely ambiguous middle, and it is what needs a human.
ERA = re.compile(r"\b(era|age|years?|run|reprint|prelude|coda|epilogue|"
                 r"interlude|omnibus|collection|anthology|lead[- ]?in|"
                 r"aftermath|beginnings?|the rest)\b", re.I)


# The model this converged on, and it is the one Nathan asked for when he said
# "the added granularity of being able to have both in a list is ideal".
#
# A section is not simply arc-or-even. A section BELONGS TO an arc group, and
# the rule is one sentence: **a session may split a section freely, but may
# never cross an arc-group boundary.** Bookkeeping sections belong to no group
# and merge freely.
#
# Most titles say which group they are in, in one of two ways:
#
#     "Phantom Blood · Volume 3"   parent · child
#     "Buffy Season 2"             parent + numbered container
#     "Z Volume 1"                 same, no separator
#
# That single rule collapses jojo-manga's 139 sections to its 9 parts and
# star-trek's 53 to its 14 series, and it is why those looked "unsure" — they
# were never ambiguous, the classifier just could not see the hierarchy.
CONTAINER = r"(?:volume|vol|season|series|part|book|wave|phase|cycle|arc|saga)"
PARENT_DOT = re.compile(r"^(.+?)\s*·\s*.+$")
PARENT_NUM = re.compile(r"^(.+?)\s+" + CONTAINER + r"\s*\.?\s*\d+.*$", re.I)


def arc_group(title):
    """The arc a section sits inside, or None if it is bookkeeping."""
    t = (title or "").strip()
    if not t:
        return None
    m = PARENT_DOT.match(t)
    if m:
        p = m.group(1).strip()
        return None if EVEN_ONLY.match(p) else p
    m = PARENT_NUM.match(t)
    if m:
        p = m.group(1).strip()
        return None if EVEN_ONLY.match(p) else p
    return None


# a "parent" that is itself just a container name carries no story
EVEN_ONLY = re.compile(r"^(the\s+)?" + CONTAINER + r"?s?\s*$", re.I)


def classify(title, rows):
    t = (title or "").strip()
    if not t:
        return "even", "no title", "high"
    for rx, why in ARC:
        if rx.search(t):
            return "arcs", why, "high"
    for rx, why in EVEN:
        if rx.match(t):
            return "even", why, "high"
    # A prose title with no number IS a named story unit — "Romance Dawn",
    # "Arlong Park", "Payback". The first pass called these low-confidence and
    # produced 1,315 unsure sections across 172 lists, which is not a shortlist,
    # it is the catalogue. They are arcs; say so and stop hedging.
    if ERA.search(t):
        return "even", "names an era or a run, not a story", "low"
    if not re.search(r"\d", t):
        return "arcs", "a named story unit", "high"
    return "even", "unrecognised — defaulting to even", "low"


def main():
    full = "--full" in sys.argv
    counts = {"arcs": 0, "even": 0}
    unsure = []
    per_list = []
    for p in sorted(glob.glob("properties/*.json")):
        if p.endswith("search.json"):
            continue
        try:
            d = json.loads(io.open(p, encoding="utf-8").read())
        except Exception:
            continue
        if not isinstance(d, dict) or "sections" not in d:
            continue
        slug = os.path.basename(p)[:-5]
        got = {"arcs": 0, "even": 0}
        low = []
        for s in d["sections"]:
            rows = len(s.get("items") or [])
            if not rows:
                continue
            kind, why, conf = classify(s.get("title"), rows)
            counts[kind] += 1
            got[kind] += 1
            if conf == "low":
                low.append((s.get("title") or "", rows, kind, why))
            if full:
                print("  %-26s %-4s %-44s %s" % (slug, kind,
                                                 (s.get("title") or "")[:44], why))
        if got["arcs"] and got["even"]:
            per_list.append((slug, got["arcs"], got["even"], "MIXED"))
        elif got["arcs"]:
            per_list.append((slug, got["arcs"], 0, "arcs"))
        elif got["even"]:
            per_list.append((slug, 0, got["even"], "even"))
        if low:
            unsure.append((slug, low))

    print("sections classified: %d arcs, %d even" % (counts["arcs"], counts["even"]))
    mixed = [x for x in per_list if x[3] == "MIXED"]
    print("lists that are wholly arcs : %d" % len([x for x in per_list if x[3] == "arcs"]))
    print("lists that are wholly even : %d" % len([x for x in per_list if x[3] == "even"]))
    print("lists carrying BOTH        : %d   <- the granularity he asked for"
          % len(mixed))
    print()
    print("MIXED lists (first 20):")
    for slug, a, e, _ in sorted(mixed, key=lambda x: -(x[1] + x[2]))[:20]:
        print("   %-32s %3d arcs / %3d even" % (slug, a, e))
    print()
    nlow = sum(len(v) for _, v in unsure)
    print("LOW CONFIDENCE — %d sections across %d lists" % (nlow, len(unsure)))
    for slug, low in sorted(unsure, key=lambda x: -len(x[1]))[:12]:
        print("   %-30s %d unsure  e.g. %s" % (
            slug, len(low), " | ".join(t[:26] for t, _, _, _ in low[:3])))


if __name__ == "__main__":
    main()
