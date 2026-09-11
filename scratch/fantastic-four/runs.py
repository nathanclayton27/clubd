#!/usr/bin/env python3
"""Print the writer runs the cached data actually shows, so the sections are
drawn from the credits rather than from memory.

    python runs.py            coarse runs by lead writer
    python runs.py debuts     recurring-character debuts, by issue
"""
import json
import pathlib
import sys
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent
rows = json.loads((HERE / "issues.json").read_text(encoding="utf-8"))
main = [r for r in rows if not r["annual"] and not r["unlimited"] and r["legacy"]]


def label(r):
    return "v%d#%s" % (r["vol"], r["num"])


def runs():
    blocks, prev = [], object()
    for r in main:
        key = r["writers"][0] if r["writers"] else "?"
        if key != prev:
            blocks.append([key, []])
            prev = key
        blocks[-1][1].append(r)
    # merge one-issue interruptions into the surrounding run
    for who, b in blocks:
        if len(b) < 3:
            continue
        print("%-22s %-9s -> %-9s  %3d iss  %s %s - %s %s  | pencils: %s" % (
            who, label(b[0]), label(b[-1]), len(b),
            b[0]["month"], b[0]["year"], b[-1]["month"], b[-1]["year"],
            ", ".join(w for w, _ in Counter(
                p for x in b for p in x["pencilers"][:1]).most_common(3))))
    print("\n--- short blocks (fill-ins) ---")
    for who, b in blocks:
        if len(b) >= 3:
            continue
        print("  %-22s %s%s" % (who, label(b[0]),
                                "" if len(b) == 1 else " -> " + label(b[-1])))


def debuts():
    counts = Counter()
    for r in rows:
        for d in r["debuts"]:
            counts[d] += 1
    # how often does a debuting character come back in this corpus?
    appear = Counter()
    for r in rows:
        seen = set()
        for d in r["debuts"]:
            seen.add(d)
        for d in seen:
            appear[d] += 1
    for r in main:
        if r["debuts"]:
            print("%-9s %-5s %-30s  %s" % (label(r), r["year"], r["title"][:30],
                                           "; ".join(r["debuts"][:5])))


if __name__ == "__main__":
    {"": runs, "debuts": debuts}[sys.argv[1] if len(sys.argv) > 1 else ""]()
