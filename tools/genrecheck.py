#!/usr/bin/env python3
"""Genre table checker (CLU-510).

Two jobs, and the second one is why the table exists at all.

1. IT REFUSES. `tools/data/genres.json` has to stay complete and honest, so
   this exits non-zero on: a list with no line in the table (the important
   one - a new list must not be able to arrive untagged), a line for a list
   that no longer exists, a genre outside the closed vocabulary, more than two
   tags, an untagged list that does not name the clause exempting it, a clause
   outside the six, an orphan note, and a contradiction (tags plus an EXEMPT
   note).

2. IT HINTS. For every genre shelf named in the table, it prints which lists
   carry that genre and are NOT a door on the shelf - the same line build.py
   prints under Directors and Marvel Comics for the filmographies and Marvel
   reading orders nobody added. The shelf is curated, so these are hints and
   never failures: the answer to one of them can legitimately be "no".

   The whole point of the tagging pass is this net. CLU-79: "a rule only obeyed
   by a person who remembers it is a rule that lapses."

Run it:  python tools/genrecheck.py
It reads the repo and writes nothing.
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROPS = ROOT / "properties"
TABLE = ROOT / "tools" / "data" / "genres.json"

# Files in properties/ that are build output, not lists.
GENERATED = {"index.json", "search.json"}

problems = []


def bad(msg):
    problems.append(msg)


def media_of(kind, unit_one):
    """The medium tags for a list.

    A deliberate copy of build.py's rule. It is not imported because build.py
    defines it inside build(), and it is not read off properties/index.json
    because that manifest is build output and can be a commit behind - which it
    was while this file was being written, by four lists. A checker that reads
    stale output reports phantom failures, so it reads the property files.
    """
    k = (kind or "").lower()
    u = unit_one or ""
    m = set()
    if "film" in k or "movie" in k:
        m.add("movies")
    if re.search(r"\btv\b|show|series|episode", k):
        m.add("tv")
    if "anime" in k:
        m.add("anime")
    if "manga" in k or u == "chapter":
        m.add("manga")
    if "comic" in k or u == "issue":
        m.add("comics")
    if "book" in k or u in ("book", "novel"):
        m.add("books")
    if "game" in k:
        m.add("games")
    return m or {"other"}


def load_properties():
    out = {}
    for f in sorted(PROPS.glob("*.json")):
        if f.name in GENERATED:
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except ValueError as e:
            bad("%s is not valid JSON: %s" % (f.name, e))
            continue
        if not isinstance(d, dict) or "slug" not in d:
            bad("%s has no slug" % f.name)
            continue
        items = [x for s in (d.get("sections") or [])
                 for x in (s.get("items") or [])]
        out[d["slug"]] = {
            "title": d.get("title") or d["slug"],
            "secret": bool(d.get("secret")),
            "media": media_of(d.get("kind"), (d.get("unit") or {}).get("one")),
            # a door is a row that opens another list, which is how a box set
            # is built and how the build derives a hub
            "doors": {x.get("into") or x.get("beside") for x in items
                      if x.get("into") or x.get("beside")},
        }
    return out


def main():
    if not TABLE.exists():
        print("tools/data/genres.json is missing", file=sys.stderr)
        return 1
    table = json.loads(TABLE.read_text(encoding="utf-8"))
    vocab = table.get("vocabulary") or []
    clauses = set(table.get("clauses") or ())
    raw = table.get("lists") or {}

    # the table is written as one line per list with an optional sibling note
    # keyed slug + "?" on the line under it
    tags = {k: v for k, v in raw.items() if not k.endswith("?")}
    notes = {k[:-1]: v for k, v in raw.items() if k.endswith("?")}

    props = load_properties()

    for slug, note in sorted(notes.items()):
        if not isinstance(note, str):
            bad("note %r is not a string" % (slug + "?"))
        if slug not in tags:
            bad("note %r has no line for %r above it" % (slug + "?", slug))

    for slug, g in sorted(tags.items()):
        note = notes.get(slug, "")
        if not isinstance(g, list) or not all(isinstance(x, str) for x in g):
            bad("%s: tags must be a list of strings, got %r" % (slug, g))
            continue
        unknown = [x for x in g if x not in vocab]
        if unknown:
            bad("%s: %s is not in the vocabulary (%s)"
                % (slug, ", ".join(repr(u) for u in unknown),
                   ", ".join(vocab)))
        if len(g) > 2:
            bad("%s: %d tags, and the cap is two" % (slug, len(g)))
        if len(set(g)) != len(g):
            bad("%s: the same genre twice (%s)" % (slug, ", ".join(g)))
        if g and note.startswith("EXEMPT"):
            bad("%s: tagged %s and its note claims an exemption - one of the "
                "two is wrong" % (slug, ", ".join(g)))
        if not g and not note.startswith("PENDING"):
            # An untagged list must say WHICH clause exempts it. 54 blank lines
            # with no reason read exactly like 54 lines nobody got to, which is
            # the failure this file exists to prevent.
            m = re.match(r"EXEMPT (\w+)", note)
            if not m:
                bad("%s: no genre and no clause. Give it tags, or a note "
                    "\"%s?\": \"EXEMPT <%s> - why\"."
                    % (slug, slug, "|".join(sorted(clauses))))
            elif m.group(1) not in clauses:
                bad("%s: EXEMPT %s is not one of the clauses (%s)"
                    % (slug, m.group(1), ", ".join(sorted(clauses))))
        if slug not in props and not note.startswith("PENDING"):
            bad("%s is in genres.json and there is no properties/%s.json. "
                "Delete the line, or mark the note PENDING if the list is "
                "being built." % (slug, slug))

    shelves = {k: v for k, v in (table.get("shelves") or {}).items()
               if not k.startswith("_")}
    for shelf, spec in sorted(shelves.items()):
        # a shelf pointing at a genre that does not exist would silently check
        # nothing, which is the one shelf-side mistake worth failing over
        if (spec or {}).get("genre") not in vocab:
            bad("shelf %r names genre %r, which is not in the vocabulary (%s)"
                % (shelf, (spec or {}).get("genre"), ", ".join(vocab)))

    for slug in sorted(props):
        if slug not in tags:
            bad("properties/%s.json carries no genre. Add a line to "
                "tools/data/genres.json: \"%s\": [\"<genre>\"] - or \"%s\": [] "
                "with a note \"%s?\": \"EXEMPT <clause> - why\"."
                % (slug, slug, slug, slug))

    if problems:
        print("genrecheck: %d problem(s)\n" % len(problems), file=sys.stderr)
        for p in problems:
            print("  FAIL  " + p, file=sys.stderr)
        print("\ntools/data/genres.json documents every rule above in its "
              "_doc block.", file=sys.stderr)
        return 1

    # ---- the numbers, so a review can start from the shape of the shelves --
    live = {s: g for s, g in tags.items() if s in props}
    counts = {v: sum(1 for g in live.values() if v in g) for v in vocab}
    print("genrecheck: %d list(s) tagged, %d exempt, %d total"
          % (sum(1 for g in live.values() if g),
             sum(1 for g in live.values() if not g), len(live)))
    print("  %s" % "  ".join("%s %d" % (v, counts[v]) for v in vocab))
    print("  %d take one tag, %d take two"
          % (sum(1 for g in live.values() if len(g) == 1),
             sum(1 for g in live.values() if len(g) == 2)))
    byclause = {}
    for s, g in sorted(live.items()):
        if not g:
            c = re.match(r"EXEMPT (\w+)", notes.get(s, ""))
            byclause.setdefault(c.group(1) if c else "?", []).append(s)
    print("  exempt by clause: %s"
          % (", ".join("%s %d" % (c, len(v))
                       for c, v in sorted(byclause.items())) or "none"))
    amb = sorted(s for s, n in notes.items()
                 if isinstance(n, str) and n.startswith("AMBIGUOUS")
                 and s in live)
    print("  %d call(s) marked AMBIGUOUS for review%s"
          % (len(amb), ": " + ", ".join(amb) if amb else ""))

    # ---- the hints: which lists a shelf is missing ------------------------
    if not shelves:
        print("  no genre shelves declared yet, so nothing to keep complete")
    for shelf, spec in sorted(shelves.items()):
        genre = spec.get("genre")
        want = spec.get("media")
        if shelf not in props:
            print("  shelf %s: not built yet (%s%s), nothing to check"
                  % (shelf, genre, " + " + want if want else ""))
            continue
        doors = props[shelf]["doors"]
        absent = sorted(s for s, g in live.items()
                        if genre in g and s != shelf and s not in doors
                        and not props[s]["secret"]
                        and (want is None or want in props[s]["media"]))
        print("  shelf %s: %d door(s), for %s%s"
              % (shelf, len(doors), genre,
                 " lists whose media includes %s" % want if want else " lists"))
        if absent:
            print("      %d list(s) carry %s%s and have no row here: %s"
                  % (len(absent), genre,
                     " + " + want if want else "", ", ".join(absent)))
            print("      hints, not failures - a shelf is curated, and \"no\" "
                  "is a legitimate answer to any of them")
        else:
            print("      complete: every %s%s list is a door here"
                  % (genre, " + " + want if want else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
