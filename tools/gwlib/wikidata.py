"""Wikidata batch lookups with the year gates that keep wrong items out.

The year gate exists because a title search once matched the 2018 slasher
Night Shift to Stephen King's 1978 story collection; P577 within a year of
the claimed release is the price of believing a runtime.
"""
import time
import urllib.parse

from . import wiki

WD = "https://www.wikidata.org/w/api.php"


def qids_for(pages, sleep=2.5):
    """{page title -> QID} via the enwiki pageprops API, redirects resolved,
    batched 40 per request."""
    out = {}
    pages = [p for p in pages if p]
    for i in range(0, len(pages), 40):
        q = urllib.parse.urlencode({
            "action": "query", "format": "json", "formatversion": "2",
            "prop": "pageprops", "ppprop": "wikibase_item", "redirects": "1",
            "titles": "|".join(pages[i:i + 40])})
        d = wiki.get_json(wiki.API + "?" + q)
        time.sleep(sleep)
        norm = {}
        for k in ("normalized", "redirects"):
            for m in d.get("query", {}).get(k, []):
                norm[m["from"]] = m["to"]
        by = {p["title"]: p.get("pageprops", {}).get("wikibase_item")
              for p in d["query"]["pages"]}
        for c in pages[i:i + 40]:
            x = c
            while x in norm:
                x = norm[x]
            if by.get(x):
                out[c] = by[x]
    return out


def claims_for(qids, sleep=2.5):
    """{QID -> claims dict}, batched 40 per request."""
    out = {}
    ids = sorted(set(q for q in qids if q))
    for i in range(0, len(ids), 40):
        q = urllib.parse.urlencode({
            "action": "wbgetentities", "format": "json", "formatversion": "2",
            "ids": "|".join(ids[i:i + 40]), "props": "claims"})
        for k, v in wiki.get_json(WD + "?" + q)["entities"].items():
            out[k] = v.get("claims", {})
        time.sleep(sleep)
    return out


# P2047 is a quantity, and its unit is part of the value. Anything outside this
# map is refused rather than assumed to be minutes: the old reader read the
# `amount` alone, so an item stating its runtime in seconds or hours would have
# been believed as minutes without a word.
_UNITS = {"Q7727": 1.0,          # minute
          "Q25235": 60.0,        # hour
          "Q11574": 1.0 / 60}    # second


def runtime_values(claims):
    """[(minutes, rank, applies_to)] for every P2047 statement, unit applied.

    `rank` is "preferred", "normal" or "deprecated" as Wikidata states it, and
    `applies_to` is the QID on the statement's `applies to part` qualifier
    (P518) or None — which is where an item says "this length is the director's
    cut" rather than the film. Order is the item's own.

    Statements whose unit is not in _UNITS are dropped, because a number whose
    unit we cannot read is not a runtime.

    This exists so a caller can see the AMBIGUITY rather than a scalar that
    hides it. Q184843 (Blade Runner) returns [(112.0, 'normal', None),
    (116.0, 'normal', None)] — two equally ranked bare numbers, neither of them
    the 117 minutes the film's own article cites to the BBFC. No rank rule can
    choose between those, which is the finding of CLU-178 and the reason weights
    in this catalogue come from infoboxes now; see gwlib/runtime.py.
    """
    out = []
    for st in (claims or {}).get("P2047", []):
        try:
            v = st["mainsnak"]["datavalue"]["value"]
            per = _UNITS.get(str(v.get("unit", "")).rsplit("/", 1)[-1])
            if per is None:
                continue
            amount = float(str(v["amount"]).lstrip("+")) * per
        except (KeyError, TypeError, ValueError):
            continue
        part = None
        for q in (st.get("qualifiers") or {}).get("P518", []):
            try:
                part = q["datavalue"]["value"]["id"]
            except (KeyError, TypeError):
                pass
        out.append((amount, st.get("rank") or "normal", part))
    return out


def runtime(claims, lo=15, hi=250, parts=False):
    """Best P2047 in minutes within [lo, hi], else None.

    Reads rank, qualifier and unit, none of which the first version of this
    function looked at (CLU-178):

      * a **deprecated** statement is dropped — Wikidata's own word for a value
        that should not be used;
      * where any statement is ranked **preferred**, only those are considered;
      * a statement qualified `applies to part` (P518) is dropped unless
        `parts=True`, because it describes a version and not the work. Q509913
        (Legend) carries 114 minutes qualified "director's cut" and an
        unqualified 125, so this is what stops the director's cut being read as
        the film;
      * a statement whose unit is not minutes, hours or seconds is dropped
        rather than believed as minutes.

    Among what survives it still takes the **longest** in range, unchanged, so
    no existing caller's answer moves for a reason other than the four rules
    above.

    **Do not use this for a weight.** CLU-178 asked for exactly the fix above
    and the fix does not rescue either row that found the bug: after it, Blade
    Runner returns 116 where its article says 117, and Legend returns 125 — a
    length nothing was ever released at — because both items carry the wrong
    figure as an ordinary unqualified statement. P2047 records lengths and
    discards the provenance that would let you choose between them. A film's own
    {{Infobox film}} keeps it, which is why every list in this catalogue weighs
    from the infobox and gwlib/runtime.py holds that rule. What P2047 is still
    good for is a sanity check, a gap-filler with a stated caveat, and the
    question "does this item look like a film at all".
    """
    vals = [(m, rank, part) for m, rank, part in runtime_values(claims)
            if rank != "deprecated" and (parts or part is None)]
    pref = [v for v in vals if v[1] == "preferred"]
    best = None
    for m, _rank, _part in (pref or vals):
        if lo <= m <= hi and (best is None or m > best):
            best = m
    return int(round(best)) if best else None


def pub_years(claims):
    """Every P577 publication year on the item."""
    out = []
    for st in (claims or {}).get("P577", []):
        try:
            out.append(int(st["mainsnak"]["datavalue"]["value"]["time"][1:5]))
        except (KeyError, TypeError, ValueError):
            pass
    return out


def year_gate(claims, year, slack=1):
    """True when the item's publication dates are compatible with `year`.
    An item with no P577 passes (absence is not contradiction)."""
    ys = pub_years(claims)
    return not ys or min(abs(y - year) for y in ys) <= slack
