#!/usr/bin/env python3
"""Generator drift checker (CLU-552).

THE BUG THIS EXISTS TO STOP. Most of properties/ is generated: a `tools/make_*.py`
writes the file and the file is committed. So a field added to a property file BY
HAND survives exactly until the next run of its generator, which rewrites the file
from its own dict and drops anything it does not know about. Nothing fails. The
build is green, the JSON is valid, the ids are intact - a feature just quietly
stops working, and the loss only shows up as something missing on the live site.

It had already happened five times with one flag. CLU-508 put `"mega": true` on
five property files by hand (commit afd81ce) so the home page could lift them out
of the card wall into a row of their own. Not one of the five generators emitted
it, so each of those lists was one rebuild away from falling back onto the wall.
It goes the other way too: commit 4ef1b1d deleted ten pointless finale notes from
nine property files and left all nine generators emitting them, so a rebuild
restores notes Nathan had decided to remove.

WHAT IT REFUSES. For every property a generator produces, this regenerates the
file into a temp directory - never over the real one - and compares:

  * a field the committed file has that the generator would NOT produce, or one
    they disagree on. In the BUILD-READ set below that is always a failure and
    can never be excused, because that is the class that costs a live feature;
    anything else has to be fixed at the generator or named in KNOWN_DRIFT;
  * a fresh run that would ADD a field, or reformat the file - the committed file
    is then behind its generator, and the next rebuild changes the site;
  * the item id set, or its ORDER, moving - always a failure, never excusable.
    An id is somebody's tick: renaming one destroys it, moving one hands it to a
    different row;
  * a generator that writes a list properties/ does not have - one run would
    create a whole unreviewed list, and the build ships what is in properties/;
  * a property nothing generates, unless NO_GENERATOR says why.

AND IT SAYS WHAT IT COULD NOT CHECK. A checker reporting "clean" when it skipped
a third of the catalogue is worse than none - and a third is roughly what a clean
checkout of this repo skips, because about forty lists are built from data in
gitignored scratch/ or is fetched live rather than from a committed cache. So
anything not actually compared is printed under UNCHECKED with its reason, every
run, and the run reports itself as incomplete rather than clean. On this machine,
with those scratch caches present, only a handful go unchecked.

Every table below is debt, and the checker guards the tables too: an entry that no
longer matches reality is itself a failure, so the lists shrink instead of rotting.

Run it:
    python tools/gendrift.py                 # offline, every generator
    python tools/gendrift.py --net           # let generators fetch
    python tools/gendrift.py star-wars mcu-anthology     # a subset
    python tools/gendrift.py -j 4            # workers (default: cpu count)

Exit status:
    0   clean - every generated property file is exactly what its generator makes
    2   no NEW problem, but something was unchecked or is recorded debt
    1   a problem that is not recorded anywhere - read the REFUSED list

It writes nothing outside the system temp directory. READS of properties/ and
tools/data/ are left alone on purpose, because a generator that re-reads its own
file to keep ids stable has to see the real one; every WRITE to either is
redirected, so a check can never edit the tree or a source cache.
"""

import argparse
import collections
import concurrent.futures
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROPS = ROOT / "properties"
TOOLS = ROOT / "tools"

# properties/ holds two build outputs as well as the lists
NOT_A_LIST = {"index.json", "search.json"}

# Every top-level key src/build.py reads off a property file. Losing one is a
# live-site regression, so none of them is ever excusable:
#   slug/title/unit/popularity/sections   the build refuses the file without them
#   subtitle/kind/year/blurb/accent/accentDark/verb   travel into the manifest,
#       and the manifest is what home paints before it loads any list
#   mega/satellite/random/schedule        decide which SURFACE a list appears on
#   secret/generate                       decide whether it ships at all
BUILD_KEYS = frozenset({
    "slug", "title", "subtitle", "kind", "year", "popularity", "blurb",
    "accent", "accentDark", "unit", "verb", "mega", "satellite", "random",
    "schedule", "secret", "generate", "sections",
})
# and per row: `w` is the weight the home bars are summed from, `into`/`beside`
# are the doors the build validates and counts, `id` is the tick itself
ITEM_BUILD_KEYS = frozenset({"id", "w", "into", "beside"})

# ---------------------------------------------------------------------------
# Properties no generator produces. Hand-maintained is fine; hand-maintained
# without anyone knowing is not. The password-gated list is NOT named here: it
# is recognised by its `secret` flag, the way src/build.py does it, because
# nothing identifying it may enter the repo.
NO_GENERATOR = {
    "cyberpunk-edgerunners": "hand-written; a scheduled list of nine rows",
    "david-lynch": "hand-written filmography",
    "hickman-secret-wars": "hand-written; tools/export_secretwars.py reads this "
                           "file, it does not write it",
}

# Generators that cannot run, the list each one owns, and why. A generator
# failing for a reason NOT recorded here is a failure: it means the catalogue
# holds a list nobody can rebuild and nobody noticed.
CANNOT_RUN = {
    "make_secret.py": ((), "prompts for the password of the gated list"),
    "make_slashers.py": (
        ("slashers",),
        "asserts on its own catalogue-overlap note - it expects Halloween "
        "(1978) to be the only film shared with another list and now finds "
        "Friday the 13th (1980) as well. Found by the CLU-552 sweep; slashers "
        "stays UNCHECKED until the note and the assert agree again."),
}

# A generator whose list properties/ no longer has. Running one would create an
# unreviewed list from nothing, so each is recorded with what to do about it.
ORPHAN_GENERATOR = {
    "make_ultimate_spiderman.py":
        "writes properties/ultimate-spider-man.json, a list that no longer "
        "exists - its material moved into `ultimate-marvel` under different "
        "ids (u-ultimate-spider-man-N, not ult00-N). Running it would add a "
        "184-row list nobody reviewed, ticked against ids nothing else uses. "
        "Found by the CLU-552 sweep: delete the script or restore the list.",
}

# Fields a generator will not reproduce, with why. A BUILD_KEY may never appear
# here - the checker rejects the entry itself if one does. Every line is debt:
# fix it in the generator and delete the line.
KNOWN_DRIFT = {
    "body-swap": {"item:note":
                  "commit 4ef1b1d rewrote The Substance's premise note on the "
                  "property file and not in tools/make_bodyswap.py"},
    "dc-comics": {"notes": "top-level notes edited on the property file",
                  "item:note": "row notes edited on the property file",
                  "item:n": "row numbering edited on the property file"},
    "donnie-yen": {"notes": "top-level notes edited on the property file"},
    "jet-li": {"notes": "top-level notes edited on the property file"},
    "nathan-fielder": {"notes": "top-level notes edited on the property file"},
}

# Lists whose committed file is BEHIND its generator: a fresh run would add
# something, or reformat the file. Same trap seen from the other side.
_4EF1B1D = ("commit 4ef1b1d edited these property files and not their "
            "generators: it deleted the ten pointless finale notes (CLU-123, "
            "Nathan: 'delete those notes if they're actually pointless') and "
            "reindented each file from two spaces to one on the way past. "
            "A run of any of these generators puts its note back, so the fix "
            "is to stop the generator emitting it.")
KNOWN_STALE = {s: _4EF1B1D for s in (
    "body-swap", "frieren", "gossip-girl", "gurren-lagann", "inuyasha",
    "outlaw-star", "sailor-moon", "samurai-jack", "the-big-o",
    "yuyu-hakusho")}

# ---------------------------------------------------------------------------
# WHICH LIST A GENERATOR OWNS, WITHOUT RUNNING IT. Needed because a generator
# that cannot run writes nothing, and a list with no output looked exactly like
# a list with no generator - which had 41 of them reported as hand-maintained on
# a clean checkout. Deliberately narrow: the house docstring convention
# ("""Generate properties/<slug>.json), a literal "properties" / "x.json", and
# `"properties" / ("%s.json" % SLUG)` resolved through a module-level constant.
# A name that is not a file in properties/ is ignored, so a docstring mentioning
# another list cannot claim it.
_DECL = None


def declared_slugs(path):
    global _DECL
    if _DECL is None:
        _DECL = {p.stem for p in PROPS.glob("*.json")} - {"index", "search"}
    t = path.read_text(encoding="utf-8", errors="replace")
    consts = dict(re.findall(r'^([A-Z_][A-Z0-9_]*)\s*=\s*"([a-z0-9-]+)"\s*$', t, re.M))
    out = set()
    m = re.search(r'^\s*(?:"""|\x27\x27\x27)(?:Generate|Build) '
                  r'properties/([a-z0-9-]+)\.json', t, re.M)
    if m:
        out.add(m.group(1))
    # the prop dict's own slug, for the ones that hand it to gwlib.prop.write()
    out |= set(re.findall(r'^\s*"slug":\s*"([a-z0-9-]+)",', t, re.M))
    out |= set(re.findall(r'"properties"\s*/\s*\(?\s*"([a-z0-9-]+)\.json"', t))
    for name in re.findall(r'"properties"\s*/\s*\(?\s*"%s\.json"\s*%\s*([A-Za-z_]\w*)', t):
        if name in consts:
            out.add(consts[name])
    for name in re.findall(r'"properties"\s*/\s*f"\{([A-Za-z_]\w*)\}\.json"', t):
        if name in consts:
            out.add(consts[name])
    return {s for s in out if s in _DECL}


# What kept a generator from running, in the words the report should use. A
# reason this recognises is UNCHECKED; anything else is a failure, because an
# unexplained break means a list nobody can rebuild and nobody noticed.
def why_it_could_not_run(err):
    if "NETWORK BLOCKED" in err:
        return ("needs the network - its source is not in a committed cache; "
                "re-run with --net")
    if re.search(r"scratch[\\/]", err) or "No module named 'fetch'" in err:
        return ("its source data lives in gitignored scratch/, so it cannot run "
                "from a clean checkout of this repo")
    return None


problems = []        # unrecorded: exit 1
recorded = []        # (reason, subject) pairs of recorded debt, printed every run
unchecked = []       # not compared at all


def bad(msg):
    problems.append(msg)


def debt(reason, subject):
    recorded.append((reason, subject))


# ---------------------------------------------------------------------------
# the child: run one generator with every write into the tree redirected


def child(gen_path, out_dir, allow_net):
    import builtins
    import runpy
    import shutil
    import traceback

    gen = pathlib.Path(gen_path).resolve()
    out = pathlib.Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    repo = gen.parent.parent
    props = (repo / "properties").resolve()
    # tools/data holds the committed source caches every generator reads. A
    # CHECK must not write them: a half-written cache can leave a generator
    # unrunnable, which is how tools/data/bestpicture.json was found during the
    # CLU-552 sweep holding {"films": "<one film title>"} instead of 621 rows.
    data = (repo / "tools" / "data").resolve()

    def target(p):
        try:
            rp = pathlib.Path(p).resolve()
        except Exception:
            return None
        if rp.parent == props and rp.name.endswith(".json"):
            return out / rp.name
        if rp.parent == data or data in rp.parents:
            d = out / "_data" / rp.relative_to(data)
            d.parent.mkdir(parents=True, exist_ok=True)
            return d
        return None

    _open = builtins.open

    def open_(file, mode="r", *a, **k):
        if isinstance(file, (str, bytes, os.PathLike)) \
                and any(c in str(mode) for c in "wxa+"):
            t = target(file)
            if t is not None:
                return _open(str(t), mode, *a, **k)
        return _open(file, mode, *a, **k)
    builtins.open = open_

    _popen = pathlib.Path.open

    def popen(self, mode="r", *a, **k):
        if any(c in str(mode) for c in "wxa+"):
            t = target(self)
            if t is not None:
                return _open(str(t), mode, *a, **k)
        return _popen(self, mode, *a, **k)
    pathlib.Path.open = popen

    _wt, _wb = pathlib.Path.write_text, pathlib.Path.write_bytes
    pathlib.Path.write_text = lambda s, d, *a, **k: _wt(target(s) or s, d, *a, **k)
    pathlib.Path.write_bytes = lambda s, d: _wb(target(s) or s, d)

    for mod, name in ((os, "replace"), (os, "rename"), (shutil, "copyfile"),
                      (shutil, "copy"), (shutil, "copy2"), (shutil, "move")):
        real = getattr(mod, name)

        def wrap(real=real):
            def g(src, dst, *a, **k):
                t = target(dst)
                return real(src, str(t) if t is not None else dst, *a, **k)
            return g
        setattr(mod, name, wrap())

    if not allow_net:
        # DNS only. Replacing socket.socket breaks `import ssl`, which
        # subclasses it, and that reads back as the generator's own TypeError -
        # 50 generators looked broken that way before this was narrowed.
        import socket

        def blocked(*a, **k):
            raise OSError("NETWORK BLOCKED by tools/gendrift.py")
        socket.getaddrinfo = blocked
        socket.create_connection = blocked

    os.chdir(str(repo))
    sys.argv = [str(gen)]
    try:
        runpy.run_path(str(gen), run_name="__main__")
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    except BaseException:
        traceback.print_exc()
        return 97
    return 0


# ---------------------------------------------------------------------------
# comparison


def rows_of(p):
    return [x for s in p.get("sections", []) for x in s.get("items", [])]


def indent_of(txt):
    m = re.match(r"[\[{]\r?\n( *)", txt)
    return len(m.group(1)) if m else None


def compare(committed, made):
    """(lost, added, ids_moved, id_detail).

    lost  = {field: what} the committed file has and a fresh run would not.
    added = {field: what} a fresh run produces and the committed file lacks.
    Fields are bare for top level, `item:<k>` per row, `section:<k>` per section.
    """
    lost, added = {}, {}
    for k in sorted(set(committed) - set(made)):
        lost[k] = "the committed file has it; the generator does not emit it"
    for k in sorted(set(made) - set(committed)):
        added[k] = "which the committed file has not got"
    for k in sorted(set(committed) & set(made)):
        if k != "sections" and committed[k] != made[k]:
            lost[k] = "they disagree"

    ic = [x["id"] for x in rows_of(committed)]
    im = [x["id"] for x in rows_of(made)]
    if ic != im:
        gone, new = sorted(set(ic) - set(im)), sorted(set(im) - set(ic))
        if set(ic) == set(im):
            return lost, added, True, "REORDERS the rows"
        return lost, added, True, (
            "changes the ID SET - %d gone (%s), %d new (%s)"
            % (len(gone), ", ".join(gone[:6]) or "-",
               len(new), ", ".join(new[:6]) or "-"))

    fc = {x["id"]: x for x in rows_of(committed)}
    fm = {x["id"]: x for x in rows_of(made)}
    lost_f, add_f, diff_f = collections.Counter(), collections.Counter(), collections.Counter()
    for i in fc:
        a, b = fc[i], fm[i]
        for k in set(a) - set(b):
            lost_f[k] += 1
        for k in set(b) - set(a):
            add_f[k] += 1
        for k in set(a) & set(b):
            if a[k] != b[k]:
                diff_f[k] += 1
    for k, n in sorted(lost_f.items()):
        lost["item:" + k] = "%d row(s) carry it; the generator emits none" % n
    for k, n in sorted(diff_f.items()):
        lost.setdefault("item:" + k, "%d row(s) disagree" % n)
    for k, n in sorted(add_f.items()):
        added["item:" + k] = "to %d row(s)" % n

    sc = {s["id"]: s for s in committed.get("sections", [])}
    sm = {s["id"]: s for s in made.get("sections", [])}
    for i in sorted(set(sc) & set(sm)):
        for k in sorted(set(sc[i]) - set(sm[i])):
            lost.setdefault("section:" + k,
                            "section %r has it, the generator does not" % i)
        for k in sorted(set(sm[i]) - set(sc[i])):
            added.setdefault("section:" + k, "to a section")
        for k in sorted((set(sc[i]) & set(sm[i])) - {"items"}):
            if sc[i][k] != sm[i][k]:
                lost.setdefault("section:" + k, "section %r disagrees" % i)
    return lost, added, False, ""


def is_dangerous(field):
    if field.startswith("item:"):
        return field[5:] in ITEM_BUILD_KEYS
    if field.startswith("section:"):
        return False
    return field in BUILD_KEYS


# ---------------------------------------------------------------------------


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("only", nargs="*",
                    help="generator names or slugs to check, matched on "
                         "letters and digits only, so `mcu-anthology` "
                         "finds make_mcu_anthology.py. Loose by design: "
                         "a full run is the one that proves coverage.")
    ap.add_argument("--net", action="store_true",
                    help="let generators fetch; off by default so a run is "
                         "deterministic and costs nobody's rate limit")
    ap.add_argument("-j", type=int, default=min(8, (os.cpu_count() or 4)),
                    help="parallel generator runs")
    ap.add_argument("--keep", action="store_true",
                    help="keep the temp tree and say where it is")
    a = ap.parse_args(argv)
    subset = bool(a.only)

    gens = sorted(TOOLS.glob("make_*.py"))
    if subset:
        def key(s):
            return re.sub(r"[^a-z0-9]", "", s.lower())
        want = {key(x.replace(".py", "").replace("make_", "")) for x in a.only}
        gens = [g for g in gens
                if key(g.stem.replace("make_", "")) in want
                or any(w and w in key(g.stem) for w in want)]
        if not gens:
            print("nothing matches %s" % " ".join(a.only))
            return 1

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="gendrift-"))
    print("regenerating %d generator(s)%s into %s"
          % (len(gens), "" if a.net else ", network blocked", tmp))

    def run(g):
        if g.name in CANNOT_RUN:
            return g, -1, "", []
        p = subprocess.run(
            [sys.executable, str(pathlib.Path(__file__).resolve()),
             "--child", str(g), str(tmp / g.stem)] + (["--net"] if a.net else []),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=900)
        d = tmp / g.stem
        return g, p.returncode, (p.stderr or "")[-1200:], \
            sorted(f.stem for f in d.glob("*.json")) if d.exists() else []

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, a.j)) as ex:
        for r in ex.map(run, gens):
            results.append(r)

    owners = collections.defaultdict(list)
    # a list nothing produced, and the generator that was supposed to. Read
    # statically, because a generator that dies writes nothing and a list with
    # no output is otherwise indistinguishable from a list with no generator.
    orphaned = {}
    for g, rc, err, wrote in results:
        if rc == -1:
            slugs, why = CANNOT_RUN[g.name]
            debt(why, "%s cannot run" % g.name)
            for s in slugs:
                orphaned.setdefault(s, "%s cannot run - %s" % (g.name, why))
            continue
        if rc != 0 and not wrote:
            why = why_it_could_not_run(err)
            if why is None:
                last = [l for l in err.strip().splitlines() if l.strip()]
                bad("%s exits %d and CANNOT_RUN does not say why - the list it "
                    "owns cannot be rebuilt by anyone. Last line: %s"
                    % (g.name, rc, last[-1][:160] if last else "(no output)"))
                why = "failed, see REFUSED"
            mine = declared_slugs(g)
            for s in mine:
                orphaned.setdefault(s, "%s %s" % (g.name, why))
            if not mine:      # otherwise each list says it, which is the useful half
                unchecked.append("%s: %s" % (g.name, why))
            continue
        for s in wrote:
            owners[s].append((g, tmp / g.stem / (s + ".json")))

    # ---- compare every regenerated file against the committed one ---------
    checked, clean = [], []
    for slug in sorted(owners):
        live = PROPS / (slug + ".json")
        if not live.exists():
            for g, _ in owners[slug]:
                if g.name in ORPHAN_GENERATOR:
                    debt(ORPHAN_GENERATOR[g.name], g.name)
                else:
                    bad("%s writes properties/%s.json, which does not exist - "
                        "one run would create a whole unreviewed list, and the "
                        "build ships whatever is in properties/. Record it in "
                        "ORPHAN_GENERATOR or delete the script."
                        % (g.name, slug))
            continue
        live_txt = live.read_text(encoding="utf-8")
        committed = json.loads(live_txt)
        # two generators can write one slug; judge the one that agrees most
        g, path = min(owners[slug], key=lambda gp: len(
            compare(committed, json.loads(gp[1].read_text(encoding="utf-8")))[0]))
        made_txt = path.read_text(encoding="utf-8")
        checked.append(slug)
        if made_txt == live_txt:
            clean.append(slug)
            continue

        lost, added, ids_moved, how = compare(committed, json.loads(made_txt))
        if ids_moved:
            bad("%s: %s %s. An id is a tick - this is never acceptable, and no "
                "table may excuse it." % (slug, g.name, how))
            continue

        allowed = KNOWN_DRIFT.get(slug, {})
        for f in sorted(lost):
            if is_dangerous(f):
                bad("%s: `%s` %s -- the build reads it, so the next run of %s "
                    "DELETES a live feature. Declare it in the generator."
                    % (slug, f, lost[f], g.name))
            elif f in allowed:
                debt(allowed[f], "%s: `%s` %s" % (slug, f, lost[f]))
            else:
                bad("%s: `%s` %s. Either put it in %s or record it in "
                    "KNOWN_DRIFT with a reason." % (slug, f, lost[f], g.name))
        for f in sorted(set(allowed) - set(lost)):
            bad("%s: KNOWN_DRIFT claims `%s` drifts and it does not any more - "
                "delete the line" % (slug, f))

        reindent = indent_of(live_txt) != indent_of(made_txt)
        if added or reindent:
            what = ", ".join("adds `%s` %s" % (f, added[f]) for f in sorted(added))
            if reindent:
                what = (what + ", and " if what else "") + (
                    "reindents the file from %s to %s space(s)"
                    % (indent_of(live_txt), indent_of(made_txt)))
            if slug in KNOWN_STALE:
                debt(KNOWN_STALE[slug],
                     "%s is BEHIND %s: a fresh run %s" % (slug, g.name, what))
            else:
                bad("%s: the committed file is BEHIND %s - a fresh run %s. "
                    "Rebuild the list and commit it, change the generator, or "
                    "record it in KNOWN_STALE." % (slug, g.name, what))
        elif not lost:
            bad("%s: the committed bytes differ from a fresh run of %s but no "
                "field and no id does - the generator serialises differently "
                "(key order or line endings)." % (slug, g.name))
    for slug in sorted(KNOWN_STALE):
        # only a list that was actually regenerated can prove its line stale;
        # on a clean checkout a third of them cannot run at all
        if slug in checked or subset:
            continue
        if slug not in orphaned and (PROPS / (slug + ".json")).exists():
            bad("KNOWN_STALE names %s, which nothing regenerated and nothing "
                "claims - delete the line or find out why" % slug)

    # ---- coverage: everything in properties/ is checked or excused --------
    if not subset:
        covered = set(checked)
        for f in sorted(PROPS.glob("*.json")):
            if f.name in NOT_A_LIST or f.stem in covered:
                continue
            try:
                p = json.loads(f.read_text(encoding="utf-8"))
            except ValueError:
                bad("%s is not valid JSON" % f.name)
                continue
            if p.get("secret"):
                unchecked.append("%s: the password-gated list - its contents "
                                 "are ciphertext and its generator needs the "
                                 "password" % f.stem)
                continue
            if f.stem in NO_GENERATOR:
                unchecked.append("%s: no generator - %s"
                                 % (f.stem, NO_GENERATOR[f.stem]))
                continue
            if f.stem in orphaned:
                unchecked.append("%s: not compared - %s" % (f.stem, orphaned[f.stem]))
                continue
            bad("%s has no generator and NO_GENERATOR does not say why. Either "
                "it is hand-maintained - say so there - or its generator no "
                "longer declares its slug, and the list cannot be rebuilt."
                % f.stem)
        for slug, why in sorted(NO_GENERATOR.items()):
            if not (PROPS / (slug + ".json")).exists():
                bad("NO_GENERATOR names %s, which is not in properties/ any "
                    "more - delete the line" % slug)
            elif slug in covered:
                bad("NO_GENERATOR says %s has no generator, but one produced "
                    "it - delete the line (%s)" % (slug, why))
        for name in sorted(set(CANNOT_RUN) | set(ORPHAN_GENERATOR)):
            if not (TOOLS / name).exists():
                bad("CANNOT_RUN/ORPHAN_GENERATOR names %s, which is gone - "
                    "delete the line" % name)
        for slug, fields in sorted(KNOWN_DRIFT.items()):
            for f in sorted(fields):
                if is_dangerous(f):
                    bad("KNOWN_DRIFT excuses `%s` on %s, which the build reads "
                        "- that field can never be excused" % (f, slug))
            if not (PROPS / (slug + ".json")).exists():
                bad("KNOWN_DRIFT names %s, which is not in properties/ any "
                    "more - delete the entry" % slug)

    # ---- report ----------------------------------------------------------
    n_lists = len([f for f in PROPS.glob("*.json") if f.name not in NOT_A_LIST])
    print()
    print("  %d of %d list(s) regenerated and compared; %d byte-identical to "
          "what their generator makes" % (len(checked), n_lists, len(clean)))
    if orphaned and not subset:
        n_scratch = sum(1 for w in orphaned.values() if "scratch/" in w)
        print("  %d list(s) could not be regenerated from this checkout at all%s"
              % (len(orphaned),
                 " - %d of them because their source data lives in gitignored "
                 "scratch/ rather than in the repo" % n_scratch if n_scratch else ""))
    if recorded:
        by = collections.defaultdict(set)
        for reason, subject in recorded:
            by[reason].add(subject)
        print()
        print("RECORDED DEBT (%d) - known, named, and still wrong:"
              % len(set(recorded)))
        for reason in sorted(by):
            for s in sorted(by[reason]):
                print("   %s" % s)
            print("      ^ %s" % reason)
    if unchecked:
        print()
        print("UNCHECKED (%d) - this run did NOT verify these:" % len(unchecked))
        for u in sorted(set(unchecked)):
            print("   %s" % u)
    if problems:
        print()
        print("REFUSED (%d):" % len(problems))
        for p in sorted(problems):
            print("   %s" % p)
    if a.keep:
        print("\n  temp tree kept at %s" % tmp)
    print()
    if problems:
        print("gendrift: FAIL - %d unrecorded problem(s). A hand-edit to a "
              "generated property file does not survive its generator: fix it "
              "in the generator." % len(problems))
        return 1
    if unchecked or recorded:
        print("gendrift: no new problem, but this run is INCOMPLETE - %d "
              "unchecked, %d recorded as debt. Not the same as clean."
              % (len(set(unchecked)), len(set(recorded))))
        return 2
    print("gendrift: clean - every generated property file is exactly what its "
          "generator produces.")
    return 0


if __name__ == "__main__":
    if "--child" in sys.argv:
        i = sys.argv.index("--child")
        sys.exit(child(sys.argv[i + 1], sys.argv[i + 2], "--net" in sys.argv))
    sys.exit(main())
