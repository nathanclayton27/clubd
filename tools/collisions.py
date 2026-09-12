"""Cross-list sync collisions: two DIFFERENT works the sync map thinks are one.

clubd pairs ticks across lists on a normalised `title|year|medium` key, plus a
`Q-id|medium` key wherever a generator could prove the work id. Two rows that
mint the same key on different lists become one sync group, and ticking either
ticks both. That is the feature -- Dr. Strangelove on Kubrick, Criterion and
Best Picture is one film -- and it is a silent data corruption the day two rows
share a key and are NOT the same work: a tick lands on a list the person never
opened, and an untick takes the stranger with it.

CLU-550 was that. `Swamp Thing season 1 (1990)` is the live-action USA Network
series on dc-anthology and the five-episode animated series on dc-animation.
Same title, same year, same lane, different works.

This sweep exists so the class is CHECKABLE rather than found by a user. It
  - rebuilds the sync map from properties/*.json,
  - counts every key spanning more than one list (the candidate pairs),
  - flags the ones carrying evidence of being different works, and
  - exits non-zero on any flagged pair that is not judged below, or that is
    judged a collision and is still sharing a sync group.

That last clause is what makes it a regression test rather than a note: a fix
has to actually separate the rows, not merely be described.

WHY THE MAPPING IS REPLICATED HERE. build.py builds the sync map inline in
main(), which also writes index.html and the generated property files, so it
cannot be imported without running the build. The three functions below are a
faithful copy of src/build.py's _normt, _year_of and key minting. IF THAT BLOCK
CHANGES, CHANGE THIS ONE -- and selftest() is the alarm: it asserts the replica
still agrees with the build's own committed output in properties/search.json.

Usage:
    python tools/collisions.py            # sweep; non-zero on unresolved
    python tools/collisions.py --all      # also list every cross-list pair
    python tools/collisions.py --groups   # just the group count, for diffing
"""
import collections
import json
import pathlib
import re
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROPS = ROOT / "properties"
GENERATED = {"index.json", "search.json"}

# ---- judged pairs -------------------------------------------------------
# key -> (verdict, why). "same" = one work on two lists, the feature working,
# nothing to do. "split" = genuinely different works; the sweep then PROVES
# they no longer share a sync group and fails if they do.
JUDGED = {
    "swamp thing season 1|1990|f": ("split", """
        CLU-550. Two different series. dc-anthology carries the live-action USA
        Network series (Wikidata Q2024136, 1990-07-27 to 1993-05-01, 72 episodes
        over 3 seasons, 17.2h); dc-animation carries the animated one (Q3051963,
        1990-10-31 to 1991-05-11, 5 episodes, 1.83h). All they share is the
        character they are both based on, Swamp Thing (Q1427625)."""),
    "what if season 1|2021|f": ("same", """
        One work. The MCU animated anthology's first season, carried by both
        marvel-animation and mcu-anthology. The 3.18h/4.8h spread is two lists
        estimating the same nine episodes, not two works."""),
    "what if season 2|2023|f": ("same", """
        One work, as season 1 above: marvel-animation and mcu-anthology both
        carry the 2023 season."""),
    "x men 97 season 1|2024|f": ("same", """
        One work. X-Men '97 season 1 on both marvel-animation and
        mcu-anthology; 3.48h against 5.33h is the same ten episodes counted
        twice."""),
}

# A runtime ratio at or above this between two rows on one key is evidence they
# are not the same work. 1.5 is deliberately low: it catches the three Marvel
# pairs above, all of which are honestly one work with sloppy hour estimates, so
# the threshold costs three judged entries and leaves the 9.4x Swamp Thing pair
# a long way clear of the noise.
W_RATIO = 1.5


def _normt(t):
    """src/build.py: strip accents, fold to a-z0-9, drop a leading article."""
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    t = re.sub(r"[^a-z0-9]+", " ", t).strip()
    return re.sub(r"^(the|a|an) ", "", t)


def _year_of(x, n):
    """src/build.py: the printed number, else `y`, else the note's ONE year."""
    if re.fullmatch(r"(18|19|20)\d{2}", n):
        return n
    explicit = str(x.get("y", ""))
    if re.fullmatch(r"(18|19|20)\d{2}", explicit):
        return explicit
    found = set(re.findall(r"\b((?:18|19|20)\d{2})\b", x.get("note") or ""))
    return found.pop() if len(found) == 1 else None


def load_props():
    out = []
    for f in sorted(PROPS.glob("*.json")):
        if f.name in GENERATED:
            continue
        out.append(json.loads(f.read_text(encoding="utf-8")))
    return out


def mint(props):
    """src/build.py's key minting.

    Returns (groups, alias, meta):
      groups  key -> [[slug, id], ...]
      alias   [[k1, k2], ...] -- key pairs one row proves name one work
      meta    (slug, id) -> the row, plus _slug/_kind/_sec, for reporting
    """
    groups, alias, meta = collections.defaultdict(list), [], {}
    for p in props:
        if p.get("secret"):
            continue
        kind = p.get("kind") or ""
        prop_medium = "g" if "game" in kind else "f"
        syncable = "film" in kind or "game" in kind
        for s in p.get("sections", []):
            for x in s.get("items", []):
                n = str(x.get("n", ""))
                meta[(p["slug"], x["id"])] = dict(
                    x, _slug=p["slug"], _kind=kind, _sec=s.get("id"))
                rm = x.get("m")
                assert rm is None or rm in ("f", "g"), (
                    "%s item %s: medium %r must be 'f' or 'g'"
                    % (p["slug"], x["id"], rm))
                medium = rm or (prop_medium if syncable else None)
                if not medium:
                    continue
                keys = []
                y = _year_of(x, n)
                if y:
                    keys.append(_normt(x["t"]) + "|" + y + "|" + medium)
                q = x.get("q")
                if isinstance(q, str) and re.fullmatch(r"Q[1-9]\d*", q):
                    keys.append(q + "|" + medium)
                for k in keys:
                    groups[k].append([p["slug"], x["id"]])
                if len(keys) > 1:
                    alias.append(keys)
    return groups, alias, meta


def sync_map(props):
    """src/build.py's merged sync map: group name -> [[slug, id], ...]."""
    groups, alias, _ = mint(props)
    parent = {}

    def find(k):
        parent.setdefault(k, k)
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    for ks in alias:
        for k in ks[1:]:
            a, b = find(ks[0]), find(k)
            if a != b:
                parent[a] = b

    merged = {}
    for k, v in groups.items():
        m = merged.setdefault(find(k), {"keys": [], "rows": []})
        m["keys"].append(k)
        m["rows"] += v

    sync = {}
    for m in merged.values():
        seen, rws = set(), []
        for s, i in m["rows"]:
            if (s, i) not in seen:
                seen.add((s, i))
                rws.append([s, i])
        if len({s for s, _ in rws}) > 1:
            ks = sorted(m["keys"])
            sync[next((k for k in ks if k[0] == "Q"), ks[0])] = rws
    return sync


def row_group(sync, slug, rid):
    """The name of the sync group holding this row, or None."""
    for name, rws in sync.items():
        if [slug, rid] in rws:
            return name
    return None


def suspects(groups, meta):
    """(all cross-list title keys, the flagged subset -> why flagged)."""
    cands, flagged = {}, {}
    for k, v in groups.items():
        if k[0] == "Q" or len({s for s, _ in v}) < 2:
            continue
        cands[k] = v
        rows = [meta[(s, i)] for s, i in v]
        why = []
        qs = {r["q"] for r in rows if r.get("q")}
        if len(qs) > 1:
            why.append("rows carry different work ids: %s" % ", ".join(sorted(qs)))
        ws = [r["w"] for r in rows
              if isinstance(r.get("w"), (int, float)) and r["w"] > 0]
        if len(ws) > 1 and max(ws) / min(ws) >= W_RATIO:
            why.append("runtimes disagree %.2fx (%s)" % (
                max(ws) / min(ws),
                ", ".join("%s %gh" % (r["_slug"], r["w"])
                          for r in rows if r.get("w"))))
        seas = {bool(re.search(r"\bseasons?\b", r["t"], re.I)) for r in rows}
        if len(seas) > 1:
            why.append("one row is a season and one is not")
        if why:
            flagged[k] = why
    return cands, flagged


def selftest(props):
    """The replica has to agree with the build's own committed sync map."""
    f = PROPS / "search.json"
    if not f.exists():
        return "search.json absent, replica unchecked"
    shipped = json.loads(f.read_text(encoding="utf-8")).get("sync") or {}
    if not shipped:
        return "search.json carries no sync map, replica unchecked"

    def norm(d):
        return {k: sorted(tuple(r) for r in v) for k, v in d.items()}

    a, b = norm(shipped), norm(sync_map(props))
    if a == b:
        return "replica agrees with properties/search.json (%d groups)" % len(a)
    only_s, only_m = sorted(set(a) - set(b)), sorted(set(b) - set(a))
    diff = sorted(k for k in set(a) & set(b) if a[k] != b[k])
    return ("DIFFERS from properties/search.json: %d only there, %d only here, "
            "%d changed -- expected between a properties edit and the next "
            "build, a replica drift otherwise (%s)"
            % (len(only_s), len(only_m), len(diff),
               ", ".join((only_s + only_m + diff)[:4]) or "-"))


def main(argv):
    props = load_props()
    sync = sync_map(props)
    if "--groups" in argv:
        print(len(sync))
        return 0
    groups, _, meta = mint(props)
    cands, flagged = suspects(groups, meta)
    nrows = sum(len(s.get("items", [])) for p in props
                for s in p.get("sections", []))

    print("catalogue   %d property files, %d rows" % (len(props), nrows))
    print("sync map    %d groups" % len(sync))
    print("title keys  %d span more than one list (candidate pairs)"
          % len(cands))
    print("selftest    %s" % selftest(props))
    print()

    bad = 0
    print("flagged pairs (%d of %d candidates):" % (len(flagged), len(cands)))
    for k in sorted(flagged):
        rows = [meta[(s, i)] for s, i in groups[k]]
        verdict, why = JUDGED.get(k, (None, ""))
        mark = {"same": "ok   same work",
                "split": "ok   split"}.get(verdict, "FAIL unjudged")
        holding = {row_group(sync, r["_slug"], r["id"]) for r in rows}
        if verdict == "split" and len(holding) < 2:
            mark = "FAIL still one group (%s)" % holding.pop()
        if mark.startswith("FAIL"):
            bad += 1
        print("  [%s] %s" % (mark, k))
        for r in rows:
            print("      %-17s %-34s %-14s %s" % (
                r["_slug"], r["id"],
                ("q=%s" % r["q"]) if r.get("q") else "",
                ("%gh" % r["w"]) if r.get("w") else ""))
        for w in flagged[k]:
            print("      ! %s" % w)
        if verdict:
            print("      judged %s: %s" % (verdict, " ".join(why.split())))
        else:
            print("      NOT JUDGED -- decide whether these are one work, then "
                  "add the key to JUDGED in this file")

    if "--all" in argv:
        print("\nall %d cross-list candidate pairs:" % len(cands))
        for k in sorted(cands):
            print("  %-58s %s" % (k, " ".join(s for s, _ in groups[k])))

    print()
    if bad:
        print("%d flagged pair(s) unresolved" % bad)
        return 1
    print("all flagged pairs resolved")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
