#!/usr/bin/env python3
"""Generate properties/best-picture.json — every Best Picture nominee, by year.

    python tools/make_bestpicture.py

One section per ceremony year, 1st (1927/28) through 98th (2025), each section
titled the way the source styles it — "1927/28 (1st)" — with the winner named
in the sub. The winner's own row carries "Won Best Picture" and two stars; the
winner is public record, not a spoiler.

Source: scratch/oscars/bp.wiki, the full wikitext of Wikipedia's "Academy
Award for Best Picture", fetched earlier. Only the "Winners and nominees"
section is read — eleven decade tables of identical shape.

How winners are detected: each ceremony group in those tables opens with a row
whose separator is `|- style="background:#FAEB86"` — the gold row the article's
own {{legend}} declares "indicates the winner". That same row carries the year
header cell (`! rowspan="N"| [[YYYY in film|label]] … [(Nth)]`) and the winning
film, whose title the table also sets in bold ('''''…'''''). Nominees follow on
plain or #eee zebra rows. Detection is the gold row style, cross-checked
against the bold title — the two must agree on every row — and each group is
asserted to hold exactly one winner, sitting first, with exactly `rowspan`
films in total.

Weights are runtimes, resolved through each film's wikilink target: the
targets go to the Wikipedia API (prop=pageprops) for their Wikidata ids, then
to wbgetentities for P2047 (duration), both batched 40 per request with a 2s
sleep and UA "GroupWatch/1.0 (reading-list builder)". Results are cached in
tools/data/bestpicture.json so re-runs touch no network. A film whose runtime
cannot be resolved weighs 0 rather than a guess.

`n` is the table's own "Year of film release" value — a plain year from 1934
on, a split season like "1927/28" before that. Section ids and item ids use
the year of the `[[YYYY in film]]` link target, which is how "1927/28" becomes
`y1928`.
"""
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

SLUG = "best-picture"

ROOT = pathlib.Path(__file__).resolve().parent.parent
WIKI = ROOT / "scratch" / "oscars" / "bp.wiki"
CACHE = pathlib.Path(__file__).resolve().parent / "data" / "bestpicture.json"
OUT = ROOT / "properties" / ("%s.json" % SLUG)

UA = "GroupWatch/1.0 (reading-list builder)"
BATCH = 40
SLEEP = 3.0  # >=2s per request; 2.0 still drew a 429 once, so a little more

YEARCELL = re.compile(r"\[\[(\d{4}) in film\|([^\]]+)\]\]")
ORDCELL = re.compile(r"\[\[\d+(?:st|nd|rd|th) Academy Awards\|\((\d+(?:st|nd|rd|th))\)\]\]")
LINK = re.compile(r"\[\[([^|\]]+)(?:\|([^\]]+))?\]\]")
ROWSPAN = re.compile(r'^!\s*rowspan="(\d+)"')

# duration units Wikidata actually uses on P2047, as minutes-per-unit
UNIT_MIN = {
    "http://www.wikidata.org/entity/Q7727": 1.0,       # minute
    "http://www.wikidata.org/entity/Q25235": 60.0,     # hour
    "http://www.wikidata.org/entity/Q11574": 1.0 / 60,  # second
}


def slug(t):
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


# ---------------------------------------------------------------- parsing

def region(text):
    """The 'Winners and nominees' section, and nothing else."""
    m = re.search(r"^==Winners and nominees==$", text, re.M)
    assert m, "no Winners and nominees heading"
    rest = text[m.end():]
    n = re.search(r"^==[^=]", rest, re.M)
    return rest[:n.start()] if n else rest


def film_cell(line, winner):
    """Title and wikilink target from a film cell; assert bold agrees."""
    cell = line.lstrip("|").strip()
    bold = "'''" in cell
    assert bold == winner, "bold/gold disagree on %r" % line
    m = LINK.search(cell)
    assert m, "film cell with no wikilink: %r" % line
    target = m.group(1).strip()
    title = (m.group(2) or m.group(1)).strip().strip("'").strip()
    assert title and target, "empty title in %r" % line
    return title, target


def parse(text):
    """[{year, label, ord, films: [{t, target, winner}]}, …] per ceremony."""
    groups = []
    cur = None          # the ceremony group being filled
    row_style = ""      # style of the current table row
    cell_no = 0         # pipe-cells seen in the current row

    def close(g):
        if g is None:
            return
        assert len(g["films"]) == g["rowspan"], \
            "%s: %d films, rowspan %d" % (g["label"], len(g["films"]), g["rowspan"])
        wins = [f for f in g["films"] if f["winner"]]
        assert len(wins) == 1, "%s has %d winners" % (g["label"], len(wins))
        assert g["films"][0]["winner"], "%s: winner is not first" % g["label"]
        groups.append(g)

    for line in region(text).splitlines():
        line = line.rstrip()
        if line.startswith("|-"):
            row_style = line
            cell_no = 0
        elif line.startswith("!"):
            m = ROWSPAN.match(line)
            if not m:
                continue                       # a plain column-header cell
            y = YEARCELL.search(line)
            o = ORDCELL.search(line)
            assert y and o, "unparseable year cell: %r" % line[:80]
            assert "#FAEB86" in row_style, "year row is not gold: %r" % line[:80]
            close(cur)
            cur = {"year": int(y.group(1)), "label": y.group(2).strip(),
                   "ord": o.group(1), "rowspan": int(m.group(1)), "films": []}
        elif line.startswith("|") and not line.startswith(("|}", "|+")):
            cell_no += 1
            if cell_no != 1:
                continue                       # studio / producer cell
            assert cur is not None, "film cell outside a ceremony: %r" % line[:80]
            t, target = film_cell(line, "#FAEB86" in row_style)
            cur["films"].append({"t": t, "target": target,
                                 "winner": "#FAEB86" in row_style})
    close(cur)

    assert len(groups) == 98, "expected 98 ceremonies, got %d" % len(groups)
    years = [g["year"] for g in groups]
    assert len(years) == len(set(years)), "two ceremonies share a year id"
    for i, g in enumerate(groups):
        assert g["ord"] == "%d%s" % (i + 1, ordsuf(i + 1)), \
            "ceremony %d styled %s" % (i + 1, g["ord"])
    return groups


def ordsuf(n):
    if 10 <= n % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


# ---------------------------------------------------------------- fetching

def api(url, params):
    """One POST, rate-limit aware: waits out a 429/503 rather than dying."""
    req = urllib.request.Request(
        url, data=urllib.parse.urlencode(params).encode("utf-8"),
        headers={"User-Agent": UA})
    for attempt in range(6):
        time.sleep(SLEEP)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or attempt == 5:
                raise
            try:
                wait = int(e.headers.get("Retry-After", "0"))
            except ValueError:
                wait = 0
            wait = max(wait, 30 * (attempt + 1))
            print("  %d from %s — waiting %ds" %
                  (e.code, urllib.parse.urlsplit(url).hostname, wait), flush=True)
            time.sleep(wait)


def qids_for(chunk):
    """{wikilink target: Q-id or None} for one batch, via prop=pageprops."""
    d = api("https://en.wikipedia.org/w/api.php", {
        "action": "query", "format": "json", "formatversion": "2",
        "prop": "pageprops", "ppprop": "wikibase_item",
        "redirects": "1", "titles": "|".join(chunk)})
    q = d.get("query", {})
    fwd = {}
    for r in q.get("normalized", []) + q.get("redirects", []):
        fwd[r["from"]] = r["to"]
    byname = {p["title"]: p.get("pageprops", {}).get("wikibase_item")
              for p in q.get("pages", [])}
    out = {}
    for t in chunk:
        name = t
        hops = 0
        while name in fwd and hops < 5:
            name = fwd[name]
            hops += 1
        out[t] = byname.get(name)
    return out


def p2047(claims):
    """Runtime in minutes from a P2047 claim list, or None."""
    stmts = [s for s in claims.get("P2047", []) if s.get("rank") != "deprecated"]
    pref = [s for s in stmts if s.get("rank") == "preferred"]
    for s in pref or stmts:
        try:
            v = s["mainsnak"]["datavalue"]["value"]
            per = UNIT_MIN[v["unit"]]
        except KeyError:
            continue
        return float(v["amount"]) * per
    return None


def runtimes_for(qids):
    """{Q-id: minutes or None} for one batch, via wbgetentities."""
    out = {}
    d = api("https://www.wikidata.org/w/api.php", {
        "action": "wbgetentities", "format": "json",
        "props": "claims", "ids": "|".join(qids)})
    for q in qids:
        ent = d.get("entities", {}).get(q, {})
        out[q] = p2047(ent.get("claims", {}))
    return out


def save_cache(cache):
    # CLU-560: a non-map written here is self-sustaining (see load_cache), so
    # refuse it before the file is even opened.
    assert isinstance(cache, dict) and cache, \
        "refusing to write %s: films must be a non-empty {target: {qid, min}} " \
        "map, got %s %r" % (CACHE, type(cache).__name__, str(cache)[:80])
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    with CACHE.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(
            {"source": "en.wikipedia.org pageprops + wikidata P2047",
             "films": cache}, indent=2, ensure_ascii=False) + "\n")


def load_cache():
    """The cached {target: {qid, min}} map, or {} when there is no file yet.

    A file whose "films" is not a map is an error, never an empty cache
    (CLU-560). It was once found holding one film title as a string: `t not in
    cache` then became a substring test, every film read as uncached, and the
    first write raised. Falling back to {} would send all of them to the
    network, which offline reads as a harmless "needs the network" skip.
    """
    if not CACHE.exists():
        return {}
    raw = json.loads(CACHE.read_text(encoding="utf-8"))
    films = raw.get("films") if isinstance(raw, dict) else raw
    if not isinstance(films, dict):
        raise ValueError(
            "%s is corrupt: \"films\" should be a {target: {qid, min}} map but "
            "holds %s %r. Restore it with: git checkout HEAD -- "
            "tools/data/bestpicture.json"
            % (CACHE, type(films).__name__, str(films)[:80]))
    return films


def resolve(targets, cache):
    """{target: {qid, min}} for every wikilink target, cached on disk.

    Works batch by batch and writes the cache after every batch, so a
    rate-limit kill part-way costs nothing but the retry.
    """
    missing = [t for t in targets if t not in cache]
    if not missing:
        return cache
    print("resolving %d of %d films (rest cached)" % (len(missing), len(targets)),
          flush=True)
    for i in range(0, len(missing), BATCH):
        chunk = missing[i:i + BATCH]
        qmap = qids_for(chunk)
        qs = sorted({q for q in qmap.values() if q})
        rmap = runtimes_for(qs) if qs else {}
        for t in chunk:
            q = qmap.get(t)
            cache[t] = {"qid": q, "min": rmap.get(q) if q else None}
        save_cache(cache)
        print("  resolved %d/%d" % (min(i + BATCH, len(missing)), len(missing)),
              flush=True)
    return cache


# ---------------------------------------------------------------- property

def main():
    # The cache is checked before the scratch/ wikitext is read: without
    # scratch/ (as in CI) a read of the wikitext fails first and gendrift files
    # it as unchecked, which would hide a corrupt committed cache.
    cache = load_cache()
    groups = parse(WIKI.read_text(encoding="utf-8"))
    films = [f for g in groups for f in g["films"]]
    runt = resolve(sorted({f["target"] for f in films}), cache)

    sections = []
    for g in groups:
        items = []
        for f in g["films"]:
            r = runt[f["target"]]["min"]
            it = {"id": "bp-%d-%s" % (g["year"], slug(f["t"])),
                  "t": f["t"], "n": g["label"],
                  "w": round(r / 60.0, 2) if r else 0}
            # The canonical work id, CLU-191. This list dates rows by the
            # Academy's award year, which for most films IS the release year
            # but diverges when a film premieres in one year and opens in the
            # next — Casablanca is 1943 here and 1942 on Criterion, and both
            # are citing a real release. An id pairs them without either list
            # having to change the year it prints.
            #
            # It is safe to emit here for one reason only: it was resolved
            # from the wikilink THIS article gives, not guessed from a title.
            # A guess lands on the wrong film — resolving "Friendly Persuasion
            # (film)" by name reaches a different entity entirely.
            if runt[f["target"]].get("qid"):
                it["q"] = runt[f["target"]]["qid"]
            # tags feed the Winners/Nominees toggle; the strip follows the
            # filter, so "just the winners" narrows the bar to 98 marks too
            # only winners carry a tag: the single Winners chip is the whole
            # control, so a nominee needs nothing to be filtered out by it
            if f["winner"]:
                it["note"] = "Won Best Picture"
                it["star"] = 2
                it["tags"] = ["Winners"]
            items.append(it)
        sec = {"id": "y%d" % g["year"],
               "title": "%s (%s)" % (g["label"], g["ord"]),
               "sub": "%d film%s · winner: %s"
                      % (len(items), "" if len(items) == 1 else "s",
                         g["films"][0]["t"]),
               "items": items}
        if g is groups[0]:
            sec["open"] = True
        sections.append(sec)

    # The winners-only view. When the filter selection is exactly {Winners}
    # the page swaps to this grouping: the same 98 winner rows (identical ids,
    # so ticks carry over), one section per decade instead of 98 sections of
    # one film each. The n stays the ceremony label, which is what dates it.
    decades = {}
    for g in groups:
        w = g["films"][0]
        r = runt[w["target"]]["min"]
        row = {"id": "bp-%d-%s" % (g["year"], slug(w["t"])),
               "t": w["t"], "n": g["label"],
               "w": round(r / 60.0, 2) if r else 0,
               "note": "Won Best Picture", "star": 2, "tags": ["Winners"]}
        if runt[w["target"]].get("qid"):
            row["q"] = runt[w["target"]]["qid"]
        dec = (g["year"] // 10) * 10
        decades.setdefault(dec, []).append(row)
    alt = []
    for dec in sorted(decades):
        rows = decades[dec]
        alt.append({
            "id": "d%d" % dec, "title": "The %ds" % dec,
            "sub": "%d winner%s · %d hours"
                   % (len(rows), "" if len(rows) == 1 else "s",
                      round(sum(x["w"] for x in rows))),
            "items": rows,
        })
    alt_ids = [x["id"] for s in alt for x in s["items"]]
    base_ids = {x["id"] for s in sections for x in s["items"]}
    assert len(alt_ids) == 98 and len(set(alt_ids)) == 98
    assert set(alt_ids) <= base_ids, "alt view invented an id"

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), \
        "duplicate ids: %s" % sorted({i for i in ids if ids.count(i) > 1})[:6]
    assert len(ids) == len(films)
    for s in sections:
        stars = [x for x in s["items"] if x.get("star")]
        assert len(stars) == 1, "%s has %d starred rows" % (s["id"], len(stars))

    nowin = sum(1 for f in films if not runt[f["target"]]["min"])
    hours = sum(runt[f["target"]]["min"] or 0 for f in films) / 60.0

    prop = {
        "slug": SLUG,
        "title": "Best Picture",
        "subtitle": "every nominee, winners marked",
        "kind": "films",
        "popularity": 86,
        "year": "1927–2025",
        "blurb": "All %d Best Picture nominees across %d ceremonies, about %d "
                 "hours, each year's winner marked."
                 % (len(films), len(groups), round(hours)),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": "#9A7B1C",
        "accentDark": "#E0C25A",
        "tiers": False,
        "random": True,
        "filter": {
            "key": "result", "label": "Show", "mode": "include",
            "values": ["Winners"]
        },
        "altSections": {"when": ["Winners"], "sections": alt},
        "notes": [
            ["Each year's winner sits first, starred.",
             "The tables on Wikipedia open every ceremony with the winner on a "
             "gold row, title in bold; this list keeps that order and marks the "
             "winner with ★★ and “Won Best Picture”. Everything under "
             "it is that year's other nominees. The winner is public record, "
             "not a spoiler — it is in the section header too."],
            ["Bar widths are runtimes.",
             "Read from each film's Wikidata entry (duration, P2047). "
             "%s" % ("Every film resolved to a real runtime."
                     if not nowin else
                     "%d of the %d films have no runtime there and weigh "
                     "nothing, so they cannot drag a group's pace."
                     % (nowin, len(films)))],
            ["Years follow the Academy's own styling.",
             "Through 1932/33 the eligibility season straddled two calendar "
             "years, so the early sections are labelled the way the Academy "
             "labels them — “1927/28 (1st)” — and single years from "
             "1934 on. The 2nd ceremony had no official nominees; its list is "
             "AMPAS's own reconstruction of the films the judges considered."],
            "Nominees and winners from Wikipedia's “Academy Award for Best "
            "Picture”; runtimes from Wikidata.",
        ],
        "sections": sections,
    }

    with OUT.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d ceremonies, %d films, %d winners, about %d hours"
          % (len(groups), len(films), len(sections), round(hours)))
    print("  %d film%s without a runtime" % (nowin, "" if nowin == 1 else "s"))


if __name__ == "__main__":
    main()
