#!/usr/bin/env python3
"""What gwlib.wiki actually reads out of a corpus of cached wikitext, counted.

    python tools/measure_wiki_parser.py <dir-of-.wiki-files> [<other-parser.py>]

Prints today's numbers for today's parser. With a second argument — a copy of
some older gwlib/wiki.py — it prints both and diffs them row by row.

WHY THIS IS A SCRIPT AND NOT A PARAGRAPH. gwlib/wiki.py used to carry its sweep
as prose: pages changed, rows changed, titles changed, blocks byte-identical. A
reviewer re-derived those counts over the same articles and four of them came
back different, and nobody who cloned this repo could have caught it, because
every input to the sweep lives under the gitignored scratch/. A precise number
that is both wrong and unverifiable is worse than no number — it is the one part
of a file like that which a later reader trusts instead of re-deriving.

So the corpus stays local (it is a cache of Wikipedia, not repo content, and it
is large), and the METHOD is in the repo. Anyone with a directory of cached
articles can re-run this and get numbers for their corpus; a number quoted in a
commit message is then a dated record of one run rather than a standing claim
about the file.

What a bare clone can still check without any corpus at all is
tools/test_wiki_parser.py, which asserts against tracked fixtures.
"""
import collections
import importlib.util
import pathlib
import sys


def load(path, name):
    """Import a standalone copy of gwlib/wiki.py under its own module name."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read(mod, text):
    """(rows, notes) for one page, where a row is the comparable part of it."""
    notes = []
    try:
        eps = mod.episodes(text, notes=notes)
    except TypeError:          # an older parser with no notes= argument
        eps = mod.episodes(text)
    except ValueError as e:     # an older parser that refused the page
        return None, ["refused: %s" % str(e)[:70]]
    return [(e[0], e[1], e[2], e[3], e[4]) for e in eps], notes


def sweep(mod, files, label):
    n = collections.Counter()
    pages = {}
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        if "Episode list" not in text:
            continue
        n["pages with an {{Episode list}}"] += 1
        rows, notes = read(mod, text)
        n["pages refused"] += rows is None
        n["notes reported"] += len(notes)
        if rows is not None:
            n["rows"] += len(rows)
            n["rows with a title"] += sum(1 for r in rows if r[2])
            n["rows with no number"] += sum(1 for r in rows if r[0] is None)
            n["rows numbered with a fraction"] += sum(
                1 for r in rows if isinstance(r[0], float))
        pages[f] = rows
    print("\n== %s ==" % label)
    for k in ("pages with an {{Episode list}}", "pages refused", "rows",
              "rows with a title", "rows with no number",
              "rows numbered with a fraction", "notes reported"):
        print("   %-34s %6d" % (k, n[k]))
    return pages


def compare(a, b, files):
    rowcount = titles = blocks = numbers = refused = 0
    examples = collections.defaultdict(list)
    for f in files:
        x, y = a.get(f), b.get(f)
        if x is None or y is None:
            if x != y:
                refused += 1
            continue
        if len(x) != len(y):
            rowcount += 1
            examples["row count"].append((f.name, len(x), len(y)))
            continue
        for p, q in zip(x, y):
            if p[2] != q[2]:
                titles += 1
                examples["title"].append((f.name, p[2], q[2]))
            if (p[0], p[1]) != (q[0], q[1]):
                numbers += 1
                examples["number"].append((f.name, p[0:2], q[0:2]))
            if p[4] != q[4]:
                blocks += 1
    print("\n== old vs new, over the same pages ==")
    print("   pages one parser refused and the other did not %6d" % refused)
    print("   pages whose ROW COUNT differs                  %6d" % rowcount)
    print("   rows whose TITLE differs                       %6d" % titles)
    print("   rows whose NUMBERS differ                      %6d" % numbers)
    print("   rows whose BLOCK text differs                  %6d" % blocks)
    for k, v in examples.items():
        print("   -- %s, first 8 of %d:" % (k, len(v)))
        for x in v[:8]:
            print("      %s" % (x,))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    corpus = pathlib.Path(sys.argv[1])
    files = sorted(corpus.rglob("*.wiki"))
    print("corpus: %s  (%d .wiki files)" % (corpus, len(files)))
    if not files:
        print("nothing to measure")
        return 2

    here = pathlib.Path(__file__).resolve().parent
    new = sweep(load(here / "gwlib" / "wiki.py", "wiki_new"), files,
                "tools/gwlib/wiki.py, as it stands")
    if len(sys.argv) > 2:
        other = pathlib.Path(sys.argv[2])
        old = sweep(load(other, "wiki_other"), files, str(other))
        compare(old, new, files)
    return 0


if __name__ == "__main__":
    sys.exit(main())
