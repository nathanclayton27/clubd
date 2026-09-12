#!/usr/bin/env python3
"""Prove, per generator, that curling a title cannot move a row id. (CLU-430)

WHY THIS EXISTS

Rule 4 of the copy register wants curly apostrophes everywhere. The template
was converted; `properties/*.json` was not, and the reason is not taste. A row
id is `item_id` in the ticks and thumbs tables and in every browser's
localStorage, ids fold from titles, and the folds disagree about what an
apostrophe is:

  * `make_criterion.py`'s `slug()` maps every non-alphanumeric to "-", so
    `'` and `’` both give "-". Ids do not move. That is why criterion already
    prints `Monty Python’s Life of Brian` beside
    `crit-61-monty-python-s-life-of-brian`.
  * `make_alien.py`'s `fold()` ASCII-folds, which DROPS `’` entirely:
    `Child's Play` gives `child-s-play` and `Child’s Play` gives `childs-play`.
    Converting there rewrites the id and orphans every tick on that row.

So the conversion is safe or unsafe per GENERATOR, and nothing in the repo
could say which. A per-string review cannot answer it either: the question is
not what a string looks like, it is what the function that folded it does.

WHAT THIS DOES

For each generator it finds the function that actually produced its row ids —
by folding the row's own title and checking the result appears in the row's own
id — and then folds the curled title and compares. A generator is SAFE only
when every fold that demonstrably built an id is blind to the character being
converted, and MOVES the moment one is not, naming the rows.

    python tools/idsafe.py                  # every generator
    python tools/idsafe.py criterion alien  # only these slugs
    python tools/idsafe.py --safe           # print the safe slugs, one per line
    python tools/idsafe.py --rows           # name every row that would move

Exit 0 means every generator carrying a convertible title is proven id-safe.
Exit 1 means at least one is not, or could not be read at all — which is the
same answer for this purpose: an unreadable fold is an unproven fold.

WHAT IT DELIBERATELY DOES NOT DO

It does not convert anything. It is the gate the conversion runs behind, and it
is per generator so the conversion can proceed one list at a time while the
generators that fail wait for their fold to be fixed.

It also checks item ids only, because those are the ids people's ticks are
stored against. Section ids are derived from hand-written section keys, not
from prose, and no tick is stored against one.

READING THE VERDICTS

  SAFE     every id-building fold in this generator treats the straight and
           curly forms alike, on the real rows and on a probe battery.
  MOVES    at least one row's id changes. Do not convert this list until the
           fold is fixed; run with --rows to see which rows and to what.
  NOT-FOLDED no id on the list owes anything to a title — checked twice, once
           against the generator's own functions and once against canonical
           folds of the title and of its usual id-building parts. Episode and
           spine numbering lands here, and it is safe to convert.
  UNPROVEN a row carries an apostrophe AND has an id that looks folded from
           its title, but no fold this check can find reproduces it. The
           generator has to be read by hand. This is the verdict that must
           never be rounded down to SAFE.
  NO-GEN   the property has no generator declaring its slug, so there is no
           fold to check. Unproven.
  UNREAD   the module could not be imported. Unproven.

A generator with nothing to convert is reported as SAFE with a count of 0 and
costs nothing; the fold battery still classifies it, so a title that grows an
apostrophe later is covered by the same run.

WHAT THE FIRST FULL RUN FOUND, AND ONE THING WORTH KEEPING

The unsafe folds do not all fail the same way, so there is no single fix:

  * bond, hitchcock and kurosawa keep a straight apostrophe as a dash
    (on-her-majesty-s-secret-service) and drop a curly one. Their fold must
    learn to dash the curly one.
  * cosmere, discworld, dune, sherlock-holmes and wheel-of-time DROP a
    straight apostrophe (the-emperors-soul, winters-heart) and would dash a
    curly one. Their fold must learn to drop the curly one.

Same conversion, opposite corrections, and each one is right only because it
preserves the ids that list already shipped.

The ellipsis conversion is safe everywhere, and for a reason worth keeping:
NFKD decomposes "…" into three full stops, so every fold here that normalizes
first sees an ellipsis and an ASCII "..." as the same characters. Curly quotes
and apostrophes have no such decomposition, which is exactly why they are the
dangerous ones. The probe battery tests characters placed BETWEEN letters,
because a curly character beside a space is harmless either way — the space
already dashes and a doubled dash collapses — and spaced probes passed folds
that demonstrably lose the character.
"""
import argparse
import contextlib
import importlib.util
import inspect
import io
import json
import pathlib
import re
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROPS = ROOT / "properties"
TOOLS = ROOT / "tools"

# The three conversions the copy register asks for, each as the character the
# data has now and the one it would gain. Apostrophes are the big one — 1,097
# of the straight-apostrophe strings in properties/ are item titles — but an
# ellipsis and a double quote fold exactly as riskily, and a generator is only
# clear for the conversion it was actually checked for.
CLASSES = [
    ("apostrophe", "'", "’"),
    ("ellipsis", "...", "…"),
    ("quote-open", '"', "“"),
    ("quote-close", '"', "”"),
]

# Titles for the data-free half of the check, so a generator whose rows carry
# no apostrophe today is still classified for the day one does. Real shapes:
# a possessive, a plural possessive, a contraction, a trailing ellipsis and a
# quoted phrase.
PROBES = [
    "Child's Play",
    "Monty Python's Life of Brian",
    "The Emperor's New Groove",
    "Don't Look Now",
    # The risk is a character BETWEEN two alphanumerics, because that is where
    # dropping it and dashing it give different ids. A character beside a space
    # is harmless either way — the space already dashes, and a doubled dash
    # collapses — which is why these two probes are deliberately unspaced and
    # look nothing like a real title. Spaced versions passed every generator,
    # including the folds that demonstrably drop the character.
    "Wait...What",
    'He said"no"to that',
]


def load_props():
    out = {}
    for f in sorted(PROPS.glob("*.json")):
        if f.name in ("index.json", "search.json"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if isinstance(d, dict) and d.get("sections") and not d.get("secret"):
            out[f.stem] = d
    return out


def generators():
    """{slug -> (path, module or None, import error or None)}.

    A generator claims a property by declaring its slug, which 225 of the 231
    do. The handful that do not are matched on the property paths written in
    their own source, which is weaker and only used where SLUG is absent.
    """
    claims = {}
    sys.path.insert(0, str(TOOLS))
    for f in sorted(TOOLS.glob("make_*.py")):
        spec = importlib.util.spec_from_file_location("idsafe_gen_" + f.stem, f)
        mod = importlib.util.module_from_spec(spec)
        err = None
        try:
            # A generator prints as it loads constants; none of them should,
            # but swallow it rather than interleave it with the report.
            with contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
                spec.loader.exec_module(mod)
        except BaseException as e:              # noqa: BLE001 - report, never die
            mod, err = None, "%s: %s" % (type(e).__name__, e)
        slugs = set()
        if mod is not None and isinstance(getattr(mod, "SLUG", None), str):
            slugs.add(mod.SLUG)
        if not slugs:
            src = f.read_text(encoding="utf-8")
            slugs |= set(re.findall(r"properties/([a-z0-9][a-z0-9-]*)\.json",
                                    src))
        for s in slugs:
            claims.setdefault(s, []).append((f, mod, err))
    return claims


SLUGGY = re.compile(r"[a-z0-9][a-z0-9._-]{3,}")

# A fold is a pure string function. Anything whose source reaches the network,
# the disk or the clock is not one, and must not be CALLED to find that out —
# several generators carry a one-argument fetcher, and calling one would put a
# Wikipedia request behind a check that exists to be run casually before a
# conversion. Read the source, refuse the call.
IMPURE = ("urlopen", "get_json", "wikitext", "requests", "urllib", "socket",
          "subprocess", "time.sleep", "read_text", "read_bytes", "open(",
          "Path(", "glob(", "qids_for", "claims_for", "input(", "system(",
          "wiki.", "RT.", "hltb", "json.load")


def fold_candidates(mod):
    """The module-level one-argument functions that behave like a fold.

    "Behave like" means: handed a title, they answer with something shaped
    like the inside of an id — lowercase, no spaces. The shape test is here
    rather than a name test because the folds are called slug(), fold(), sl()
    and _slug() across the catalogue, and because a generator's other
    one-argument helpers can be expensive to call. Filtering on two probes
    keeps the row-by-row work below to the few functions that could matter.
    """
    # A generator reaches the shared fold three ways, and all three have to be
    # followed or the check calls the list unproven for the wrong reason: it
    # imports the function by name, or the module (`from gwlib import prop`,
    # then prop.slug), or the module under an alias (`as P`, then P.slug).
    seen = [("", mod)]
    for nm, val in vars(mod).items():
        if inspect.ismodule(val) and str(getattr(val, "__file__", "") or "") \
                .startswith(str(TOOLS)):
            seen.append((nm + ".", val))
    out = []
    for prefix, holder in seen:
        out += _from(holder, prefix)
    return out


def _from(holder, prefix):
    out = []
    for name, fn in inspect.getmembers(holder, inspect.isfunction):
        # Anything defined under tools/, not just in this file: 126 generators
        # fold with the shared gwlib.prop.slug(), imported by name, and a check
        # that only looked at the module's own defs would call more than half
        # the catalogue unproven.
        try:
            where = inspect.getfile(fn)
        except TypeError:
            continue
        if not str(pathlib.Path(where).resolve()).startswith(str(TOOLS)):
            continue
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            continue
        need = [p for p in sig.parameters.values()
                if p.default is inspect.Parameter.empty
                and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
        if len(need) != 1:
            continue
        try:
            src = inspect.getsource(fn)
        except (OSError, TypeError):
            continue
        if any(bad in src for bad in IMPURE):
            continue
        if any(SLUGGY.fullmatch(call(fn, p) or "") for p in PROBES[:2]):
            out.append((prefix + name, fn))
    return out


def call(fn, s):
    try:
        with contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            v = fn(s)
    except BaseException:                       # noqa: BLE001
        return None
    return v if isinstance(v, str) else None


# The three ways every fold in this repo turns a title into an id fragment,
# written out canonically. They are not used to judge safety — only to answer
# a different question: does this id LOOK folded from this title? That matters
# because "the checker found no fold" and "this id owes nothing to this title"
# are opposite conclusions, and only the second one makes a conversion safe.
def _g_sep(t):
    """Every non-alphanumeric becomes a dash: Child's Play -> child-s-play."""
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def _g_drop(t):
    """Apostrophes vanish, the rest dashes: Child's Play -> childs-play."""
    return _g_sep(re.sub(r"['’ʼ`]", "", t))


def _g_ascii(t):
    """NFKD then drop what is not ASCII, then dash. The fold that loses a
    curly apostrophe without losing a straight one."""
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return _g_sep(t)


GENERIC = (("sep", _g_sep), ("drop", _g_drop), ("ascii", _g_ascii))


def derived_by(rid, t):
    """The name of a generic fold whose output sits inside this id, or None.

    None is the strong statement: no canonical folding of this title, or of
    the parts of it an id is usually built from, appears anywhere in the id.
    An id like bobs-s3e7 or cp-s1e4 answers None, and a title conversion
    cannot reach it.
    """
    for f in forms(t):
        for nm, g in GENERIC:
            v = g(f)
            if v and len(v) >= 5 and v in rid:
                return nm
    return None


def forms(t):
    """The parts of a printed title an id might have been folded from.

    An id is often built from a shorter string than the row prints. The
    directors' cuts list is the clear case: it prints "Touch of Evil (Walter
    Murch’s Re-edit)" and its id is bdc-1958-touch-of-evil, folded from the
    film title alone. Checking the whole printed string only would have called
    that list "not folded from titles", which is the wrong answer in the one
    direction that matters — Heaven’s Gate on the same list DOES carry its
    apostrophe into its id.
    """
    out = [t, re.sub(r"\s*\([^)]*\)\s*$", "", t), t.split(" (")[0],
           t.split(":")[0], t.split(" — ")[0]]
    seen, keep = set(), []
    for f in out:
        f = f.strip()
        if f and f not in seen:
            seen.add(f)
            keep.append(f)
    return keep


def reach(fn, rid, t):
    """The form of this title whose fold appears in this id, or None.

    None means this fold did not build this id, so converting the title cannot
    move it THROUGH THIS FUNCTION. The longest matching form is returned, so a
    fold is judged on as much of the title as actually reached the id.
    """
    for f in forms(t):
        v = call(fn, f)
        if v and len(v) >= 4 and v in rid:
            return f
    return None


def id_folds(cands, rows):
    """The folds that demonstrably built an id: fold(title) lands inside id.

    This is the whole reason the check can be trusted. It does not guess from
    a function's name which one makes ids — it asks the data, and a fold that
    never reproduces a shipped id is not treated as one.
    """
    proven = {}
    for name, fn in cands:
        for rid, t in rows[:500]:
            if reach(fn, rid, t):
                proven[name] = fn
                break
    return proven


def analyse(slug, prop, folds):
    rows = [(x["id"], x["t"]) for s in prop["sections"]
            for x in s.get("items", []) if x.get("id") and x.get("t")]
    report = {}
    for cls, have, want in CLASSES:
        affected = [(i, t) for i, t in rows if have in t]
        moves, probe_moves = [], []
        for name, fn in sorted(folds.items()):
            for p in PROBES:
                if have in p and call(fn, p) != call(fn, p.replace(have, want)):
                    probe_moves.append(name)
                    break
            for rid, t in affected:
                # Judge the fold on the part of the title that reached the id,
                # and only when the character being converted is in that part:
                # a cut name in brackets that no id was folded from is not a
                # risk to anybody's ticks.
                form = reach(fn, rid, t)
                if not form or have not in form:
                    continue
                a, b = call(fn, form), call(fn, form.replace(have, want))
                if a != b:
                    moves.append((rid, t, name, a, b))
        # A title that ALREADY carries the curly form while the fold drops it
        # is the same defect arrived at from the other side: this row's shipped
        # id has already lost the character, so nobody may "tidy" it back.
        already, curly = [], [(i, t) for i, t in rows if want in t]
        for name, fn in sorted(folds.items()):
            for rid, t in curly:
                form = reach(fn, rid, t)
                if not form or want not in form:
                    continue
                if call(fn, form) != call(fn, form.replace(want, have)):
                    already.append((rid, t, name))
        report[cls] = {"n": len(affected), "moves": moves,
                       "probe": sorted(set(probe_moves)), "already": already}
    return rows, report


def main():
    ap = argparse.ArgumentParser(add_help=True, description=__doc__)
    ap.add_argument("slugs", nargs="*", help="only these properties")
    ap.add_argument("--safe", action="store_true",
                    help="print the slugs proven safe for apostrophes")
    ap.add_argument("--rows", action="store_true",
                    help="name every row whose id would move")
    a = ap.parse_args()

    props = load_props()
    claims = generators()
    if a.slugs:
        props = {k: v for k, v in props.items() if k in set(a.slugs)}
        missing = sorted(set(a.slugs) - set(props))
        if missing:
            print("no such property: %s" % ", ".join(missing))
            return 2

    verdicts, safe_slugs, bad = [], [], 0
    for slug in sorted(props):
        got = claims.get(slug) or []
        if not got:
            verdicts.append(("NO-GEN", slug, "-", "no generator declares this "
                             "slug", None))
            bad += 1
            continue
        path, mod, err = got[0]
        if mod is None:
            verdicts.append(("UNREAD", slug, path.name, err, None))
            bad += 1
            continue
        cands = fold_candidates(mod)
        rows = [(x["id"], x["t"]) for s in props[slug]["sections"]
                for x in s.get("items", []) if x.get("id") and x.get("t")]
        folds = id_folds(cands, rows)
        # Which rows carrying an apostrophe have an id that LOOKS folded from
        # the title? Those are the rows a conversion could reach, and every
        # one of them has to be covered by a fold this check actually found,
        # or the verdict is "unproven" rather than "safe".
        risky = [(rid, t, derived_by(rid, t)) for rid, t in rows if "'" in t]
        risky = [(rid, t, g) for rid, t, g in risky if g]
        uncovered = [(rid, t, g) for rid, t, g in risky
                     if not any(reach(fn, rid, t) for fn in folds.values())]
        if not folds:
            if uncovered:
                verdicts.append(("UNPROVEN", slug, path.name,
                                 "%d of %d apostrophe rows have a "
                                 "title-shaped id and no fold this check can "
                                 "find — read the generator by hand"
                                 % (len(uncovered), len(risky)), None))
                bad += 1
            else:
                n = sum(1 for _, t in rows if "'" in t)
                verdicts.append(("NOT-FOLDED", slug, path.name,
                                 "no id owes anything to a title (%d rows "
                                 "carry an apostrophe, none reach an id)" % n,
                                 None))
                safe_slugs.append(slug)
            continue
        if uncovered:
            verdicts.append(("UNPROVEN", slug, "/".join(sorted(folds)) + "()",
                             "%d apostrophe rows have a title-shaped id that "
                             "no fold found here reproduces, e.g. %s"
                             % (len(uncovered), uncovered[0][0]), None))
            bad += 1
            continue
        _, rep = analyse(slug, props[slug], folds)
        moved = {c: r for c, r in rep.items() if r["moves"] or r["probe"]}
        names = "/".join(sorted(folds)) + "()"
        if moved:
            why = ", ".join("%s: %d of %d rows move"
                            % (c, len({m[0] for m in r["moves"]}), r["n"])
                            if r["moves"] else "%s: fold drops it" % c
                            for c, r in sorted(moved.items()))
            verdicts.append(("MOVES", slug, names, why, rep))
            bad += 1
        else:
            n = rep["apostrophe"]["n"]
            verdicts.append(("SAFE", slug, names,
                             "%d rows carry an apostrophe, none move" % n,
                             rep))
            safe_slugs.append(slug)

    if a.safe:
        for s in safe_slugs:
            print(s)
        return 0 if not bad else 1

    order = {"MOVES": 0, "UNPROVEN": 1, "UNREAD": 2, "NO-GEN": 3,
             "NOT-FOLDED": 4, "SAFE": 5}
    for v, slug, who, why, rep in sorted(verdicts,
                                         key=lambda r: (order[r[0]], r[1])):
        print("%-10s %-26s %-22s %s" % (v, slug, who[:22], why))
        if a.rows and rep:
            for cls, r in sorted(rep.items()):
                for rid, t, name, was, now in r["moves"]:
                    print("         %-10s %-34s %s -> %s"
                          % (cls, rid[:34], was, now))
                for rid, t, name in r["already"]:
                    print("         %-10s %-34s already curly: %s()"
                          % ("ALREADY", rid[:34], name))

    tally = {}
    for v, *_ in verdicts:
        tally[v] = tally.get(v, 0) + 1
    print("\n%s" % "  ".join("%s %d" % (k, tally[k]) for k in sorted(tally)))
    conv = sum(1 for s in props.values() for sec in s["sections"]
               for x in sec.get("items", []) if "'" in (x.get("t") or ""))
    print("%d item titles carry a straight apostrophe across %d properties"
          % (conv, len(props)))
    if bad:
        print("\nDO NOT convert the lists above until each is SAFE. An "
              "unproven fold is not a small risk: a moved id is a silent "
              "untick of every tick on that row.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
