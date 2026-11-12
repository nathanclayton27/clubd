#!/usr/bin/env python3
"""Collect the Paul Thomas Anderson list's source data.

    PYTHONIOENCODING=utf-8 python scratch/pta/collect.py

One Wikipedia article is the authority — "Paul Thomas Anderson filmography" —
cached as raw wikitext under scratch/pta/cache/ so a re-run is offline and
reviewable. Each feature's own article is cached beside it, for the handful of
facts the section intros and row notes lean on.

WHAT THE ARTICLE'S "Film" SECTION ACTUALLY CONTAINS, AND WHY IT MATTERS

  * "Film > Feature films" is one wikitable. Ten rows, Hard Eight (1996) to
    One Battle After Another (2025), every one of them a bare {{Yes}} in the
    Director column. That table is the list.
  * Immediately below it, under a bolded '''Documentaries''' heading, sits a
    SECOND, differently-shaped table: Year / Title / Credit, two rows — Junun
    (2015) and the concert film Cameron Winter at Carnegie Hall (2026), which
    has no article of its own and links to a section of the Live at Carnegie
    Hall album article. The source files Junun outside the feature table on
    purpose, and
    that is the fact the shipped list's Junun decision rests on, so it is
    collected rather than remembered.
  * "Short films" (13 rows), "Miscellaneous", "Cameo and documentary
    appearances", "Television", "Stage" and "Music videos" (24 rows) are all
    collected too — not to ship them, but so the "what is not here" note can
    name them from the article instead of from anyone's memory.

RUNTIMES

From Wikidata P2047 and nothing else, each gated on a P577 publication year
within a year of the table's year so a same-titled item cannot slip a wrong
number in. Read at statement rank: see p2047() below for why gwlib's reader
is not used here.

Writes scratch/pta/pta_data.json.
"""
import json
import pathlib
import re
import sys
import urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from gwlib import wiki, wikidata

CACHE = HERE / "cache"
WD_API = "https://www.wikidata.org/w/api.php"
HIM = "Q25132"                        # Paul Thomas Anderson on Wikidata

FEATURE_COLS = ["year", "title", "director", "writer", "producer",
                "cinematographer", "notes", "ref"]
DOC_COLS = ["year", "title", "credit", "ref"]
SHORT_COLS = ["year", "title", "director", "writer", "producer", "notes", "ref"]
MISC_COLS = ["year", "title", "credit", "ref"]
TV_COLS = ["year", "title", "director", "writer", "actor", "thanks", "notes",
           "ref"]
MV_COLS = ["year", "title", "performer", "notes", "ref"]

MINUTE, SECOND = "Q7727", "Q11574"
# P2047 is a quantity with a unit, and both of these turn up on this
# filmography. Everything else is refused rather than assumed.
TO_MINUTES = {MINUTE: 1.0, SECOND: 1.0 / 60.0}

# The rank qualifiers this list actually leans on, so the shipped note can
# quote Wikidata's own stated reason instead of paraphrasing it.
RANK_QUALS = ("P2241", "P7452", "P1013")   # deprecation reason, preferred
                                           # reason, criterion used


def p2047(claims, lo=15.0, hi=250.0):
    """The item's runtime in minutes, honouring statement rank and unit.

    gwlib.wikidata.runtime takes the longest in-range P2047 and ignores rank
    entirely, which is right for the festival-cut case it was written for and
    wrong here. Rank is Wikidata's own verdict on its own numbers: deprecated
    means "this value is wrong", preferred means "this is the one to use". A
    rank-blind reader will cheerfully ship a figure the database itself has
    struck out, and this filmography carries exactly that conflict.

    One Battle After Another is the case in full. Its item holds three P2047
    statements: 161 minutes, deprecated, reason for deprecation
    "approximation", criterion used "truncation"; 162 minutes, deprecated,
    same reason, criterion used "rounding"; and 9,691 *seconds*, rank
    preferred, reason for preferred rank "most precise value". gwlib's reader
    returns 162 — the rounded approximation the database itself struck out.

    So: deprecated statements are dropped outright, every surviving value is
    converted to minutes through TO_MINUTES (an unrecognised unit is refused,
    never assumed to be minutes), preferred rank wins over normal if any
    preferred statement survives, and only then does the longest-in-range rule
    apply among equals.

    gwlib is deliberately left alone; every other list in the catalogue is
    built on its current behaviour.

    Returns (minutes as a float or None, [every value seen, with its unit,
    rank, minutes-equivalent and rank qualifiers]).
    """
    seen, best = [], {}
    for st in (claims or {}).get("P2047", []):
        v = st.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        try:
            amt = float(str(v["amount"]).lstrip("+"))
        except (KeyError, TypeError, ValueError):
            continue
        unit = str(v.get("unit", "")).rsplit("/", 1)[-1]
        rank = st.get("rank", "normal")
        mins = amt * TO_MINUTES[unit] if unit in TO_MINUTES else None
        quals = {}
        for p in RANK_QUALS:
            got = [q.get("datavalue", {}).get("value", {}).get("id")
                   for q in st.get("qualifiers", {}).get(p, [])]
            if any(got):
                quals[p] = [g for g in got if g]
        seen.append({"amount": amt, "unit": unit, "rank": rank,
                     "minutes": mins, "quals": quals})
        if rank == "deprecated" or mins is None or not (lo <= mins <= hi):
            continue
        best.setdefault(rank, []).append(mins)
    vals = best.get("preferred") or best.get("normal") or []
    return (max(vals) if vals else None), seen


def labels_for(qids):
    """{QID -> English label}, for the rank-qualifier items the notes quote."""
    ids = sorted({q for q in qids if q})
    out = {}
    for i in range(0, len(ids), 40):
        q = urllib.parse.urlencode({
            "action": "wbgetentities", "format": "json", "formatversion": "2",
            "ids": "|".join(ids[i:i + 40]), "props": "labels",
            "languages": "en"})
        for qid, ent in wiki.get_json(WD_API + "?" + q)["entities"].items():
            out[qid] = (ent.get("labels", {}).get("en") or {}).get("value", "")
    return out


def section(text, head, nexthead):
    """The wikitext between two headings."""
    i = text.index(head)
    return text[i:text.index(nexthead, i)]


def first_table(seg):
    """The first wikitable in a chunk, without its {| ... |} fence."""
    seg = seg[seg.index("{|"):]
    return seg[:seg.index("\n|}")]


def nth_table(seg, n):
    """The nth (0-based) wikitable in a chunk. The Film section holds two."""
    out, rest = None, seg
    for _ in range(n + 1):
        rest = rest[rest.index("{|"):]
        out = rest[:rest.index("\n|}")]
        rest = rest[rest.index("\n|}") + 3:]
    return out


def cells(chunk):
    """A row's raw cells. These tables mix one-cell-per-line with inline `||`
    separators, so both have to be honoured. Splitting on `||` is safe:
    wikilinks and templates use a single pipe."""
    out = []
    for line in chunk.split("\n"):
        line = line.strip()
        if not line.startswith("|") or line.startswith("|}") or line.startswith("|-"):
            continue
        out += [c.strip() for c in line[1:].split("||")]
    return out


def rows(seg, cols, keep_nonyear=False):
    """Table rows as dicts, with rowspan cells carried down to the rows they
    cover. Positional cell-picking without the carry silently shifts every
    column after a rowspan, and this article has rowspans in five of its
    tables — the Short films table alone has one spanning three rows.

    `keep_nonyear` keeps a row whose Year cell is not a year, such as "TBA",
    so an unreleased entry in a table is counted rather than silently hidden
    (the Documentary table's second row read TBA until its 2026 release)."""
    out, pending = [], {}
    for chunk in seg.split("\n|-")[1:]:
        raw = iter(cells(chunk))
        row = []
        for c in range(len(cols)):
            if c in pending:
                row.append(pending[c][1])
                pending[c][0] -= 1
                if pending[c][0] == 0:
                    del pending[c]
                continue
            v = next(raw, None)
            if v is None:
                row.append("")
                continue
            m = re.match(r'^rowspan\s*=\s*"?(\d+)"?\s*\|(.*)$', v, re.S)
            if m:
                span, v = int(m.group(1)), m.group(2).strip()
                if span > 1:
                    pending[c] = [span - 1, v]
            row.append(v)
        if not any(row):
            continue
        d = dict(zip(cols, row))
        y = d["year"].strip()
        if re.fullmatch(r"(19|20)\d{2}", y):
            d["year"] = int(y)
            out.append(d)
        elif keep_nonyear and y:
            d["year"] = y
            out.append(d)
    return out


def wikilink(cell):
    """([[Target|Label]] -> Target, Label); a bare [[X]] gives (X, X); a plain
    ''Title'' gives (None, Title)."""
    m = re.search(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", cell)
    if m:
        return m.group(1), wiki.clean(m.group(2) or m.group(1))
    return None, wiki.clean(cell)


def directed_items():
    """Every Wikidata item claiming P57 = Paul Thomas Anderson, with label,
    publication years and P2047. CirrusSearch rather than SPARQL: the query
    service rate-limits hard and this needs no joins. The sweep is what turns
    "Junun has a runtime" and "the music videos are not features" into
    measurements rather than assertions."""
    qids, offset = [], 0
    while True:
        q = urllib.parse.urlencode({
            "action": "query", "list": "search", "format": "json",
            "formatversion": "2", "srlimit": "50", "sroffset": str(offset),
            "srsearch": "haswbstatement:P57=%s" % HIM})
        d = wiki.get_json(WD_API + "?" + q)
        qids += [x["title"] for x in d["query"]["search"]]
        offset = d.get("continue", {}).get("sroffset")
        if not offset:
            break
    out = {}
    for i in range(0, len(qids), 40):
        q = urllib.parse.urlencode({
            "action": "wbgetentities", "format": "json", "formatversion": "2",
            "ids": "|".join(qids[i:i + 40]), "props": "claims|labels",
            "languages": "en"})
        for qid, ent in wiki.get_json(WD_API + "?" + q)["entities"].items():
            c = ent.get("claims", {})
            # a wide band: this sweep covers four-minute music videos as well
            # as features, and its only job is to say whether a runtime exists
            rt, seen = p2047(c, lo=1, hi=400)
            out[qid] = {
                "label": (ent.get("labels", {}).get("en") or {}).get("value", ""),
                "years": sorted(set(wikidata.pub_years(c))),
                "runtime": rt,
                "p2047_seen": seen,
                "p31": [s["mainsnak"].get("datavalue", {}).get("value", {}).get("id")
                        for s in c.get("P31", [])],
            }
    return out


def lead_of(text):
    """The article's prose, with the infobox counted past brace by brace."""
    i = text.find("{{Infobox film")
    if i < 0:
        return text
    depth, j = 0, i
    while j < len(text) - 1:
        if text[j:j + 2] == "{{":
            depth, j = depth + 1, j + 2
        elif text[j:j + 2] == "}}":
            depth, j = depth - 1, j + 2
            if depth == 0:
                return text[j:]
        else:
            j += 1
    return text[i:]


def article_facts(page):
    """The handful of article facts the copy leans on, read from the film's own
    page. Never a runtime source — those all come from P2047 — but the
    composer, the cinematographer, the distributor and "what is this adapted
    from" are things the section intros assert, and an intro asserting
    something nobody checked is a guess.

    `runtime` is captured only so the generator can print the infobox figure
    beside the Wikidata one; it never reaches a weight."""
    t = wiki.wikitext(page, cache_dir=CACHE)
    fb = wiki.infobox(t) if t else None
    if not fb:
        return {}
    out = {}
    for f in ("cinematography", "music", "distributor", "based_on", "story",
              "screenplay", "writer", "producer", "studio", "editing",
              "country", "runtime", "released", "language"):
        v = wiki.clean(fb(f))
        if v:
            out[f] = v
    # wiki.clean drops the title out of {{Based on|''Title''|Author}}, keeping
    # only the author, so the raw field is kept too (citations stripped): the
    # row notes name the novel, and the name has to be checkable
    raw = fb("based_on")
    if raw:
        raw = re.sub(r"<ref[^>]*/>", "", raw)
        out["based_on_raw"] = re.sub(r"<ref.*?</ref>", "", raw, flags=re.S).strip()
    out["lead"] = wiki.clean(lead_of(t)[:1800])[:1000]
    return out


ORDINALS = ("first second third fourth fifth sixth seventh eighth ninth "
            "tenth eleventh twelfth").split()


def biography():
    """The handful of sentences in the main "Paul Thomas Anderson" article that
    the shipped list's decisions rest on, pulled out whole so the generator can
    assert against the source's own words.

    The load-bearing one is the ordinal: the article calls Phantom Thread
    "Anderson's eighth film". Phantom Thread is the eighth row of the Feature
    films table, and it is the ninth thing he directed if Junun (2015) counts.
    That single phrase is the article stating, independently of how it lays its
    tables out, that Junun is not one of the features.
    """
    t = wiki.wikitext("Paul Thomas Anderson", cache_dir=CACHE)
    out = {"ordinals": [], "sentences": {}}
    # Citations are stripped from the whole article before the windows are cut,
    # not after: a window sliced through the middle of a <ref> keeps half a
    # citation's URLs, and the first attempt at this matched "eighth film"
    # against a blogs.indiewire.com link instead of against Phantom Thread.
    bare = re.sub(r"<ref[^>]*/>", "", t)
    bare = re.sub(r"<ref.*?</ref>", "", bare, flags=re.S)
    # The prose puts the title on either side of the phrase — "There Will Be
    # Blood, Anderson's fifth film" and "Anderson's eighth film, Phantom
    # Thread" both occur — so the window is kept whole and the generator does
    # the matching rather than a regex guessing which side the title is on.
    for m in re.finditer(r"Anderson's (%s) film" % "|".join(ORDINALS), bare):
        out["ordinals"].append({
            "n": ORDINALS.index(m.group(1)) + 1,
            "said": m.group(1),
            "window": wiki.clean(bare[max(0, m.start() - 170):m.end() + 170]),
        })
    # probes run against cleaned lines: the raw wikitext writes the titles as
    # wikilinks, so "Anderson directed Junun" only exists after cleaning
    lines = [wiki.clean(l) for l in t.split("\n")]
    for key, probe in (("collaborations", "noted for his collaborations"),
                       ("junun", "Anderson directed Junun"),
                       ("ghoulardi", "named his production company"),
                       ("hard_eight", "which was retitled")):
        hit = next((l for l in lines if probe in l), None)
        if hit:
            out["sentences"][key] = hit[:700]
    return out


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    art = wiki.wikitext("Paul Thomas Anderson filmography", cache_dir=CACHE)

    film_chunk = section(art, "==Film==", "===Short films===")
    feat_rows = rows(nth_table(film_chunk, 0), FEATURE_COLS)
    # the shipped intro names the camera column by the header the table shows
    assert "|[[Cinematographer|DoP]]" in nth_table(film_chunk, 0), \
        "the feature table's DoP header changed — recheck the After Elswit intro"
    # the second table in the Film section, under the bolded '''Documentaries'''
    assert "'''Documentaries'''" in film_chunk, \
        "the Documentary sub-heading moved — re-read the Film section"
    doc_rows = rows(nth_table(film_chunk, 1), DOC_COLS, keep_nonyear=True)

    short_rows = rows(first_table(section(art, "===Short films===",
                                          "===Miscellaneous===")), SHORT_COLS)
    misc_rows = rows(first_table(section(
        art, "===Miscellaneous===", "===Cameo and documentary appearances===")),
        MISC_COLS, keep_nonyear=True)
    tv_rows = rows(first_table(section(art, "==Television==", "==Stage==")),
                   TV_COLS)
    mv_rows = rows(first_table(section(art, "==Music videos==", "==See also==")),
                   MV_COLS)

    directed = [r for r in feat_rows if r["director"].strip().lower() == "{{yes}}"]
    assert len(directed) == len(feat_rows), \
        "a Feature films row is not a bare {{Yes}} director credit"

    features = []
    for r in directed:
        page, label = wikilink(r["title"])
        features.append({
            "t": label,
            "page": page or label,
            "year": r["year"],
            "wrote": r["writer"].strip().lower() == "{{yes}}",
            "produced": r["producer"].strip().lower() == "{{yes}}",
            "shot": r["cinematographer"].strip().lower() == "{{yes}}",
            # Phantom Thread's cell reads {{partial|Uncredited}}: he shot it,
            # and no cinematographer is listed in the film's credits
            "shot_uncredited": r["cinematographer"].strip().lower()
                               == "{{partial|uncredited}}",
            "tablenote": wiki.clean(r["notes"]),
            "runtime": None,
            "runtime_src": None,
        })
    features.sort(key=lambda f: (f["year"], f["t"]))

    docs = []
    for r in doc_rows:
        page, label = wikilink(r["title"])
        # A link into a section of another article (the Cameron Winter concert
        # film points at the album's "Concert film" section) is not the film's
        # own item, so it is never looked up: the album's runtime and dates
        # would be attributed to the film.
        section_of = None
        if page and "#" in page:
            section_of, page = page, None
        docs.append({"t": label, "page": page, "section_of": section_of,
                     "year": r["year"], "credit": wiki.clean(r["credit"])})

    shorts = [{"t": wikilink(r["title"])[1], "page": wikilink(r["title"])[0],
               "year": r["year"], "tablenote": wiki.clean(r["notes"])}
              for r in short_rows]
    shorts.sort(key=lambda s: (s["year"], s["t"]))

    misc = [{"t": wikilink(r["title"])[1], "year": r["year"],
             "credit": wiki.clean(r["credit"])} for r in misc_rows]
    tv = [{"t": wikilink(r["title"])[1], "year": r["year"],
           "directed": r["director"].strip().lower() == "{{yes}}",
           "notes": wiki.clean(r["notes"])} for r in tv_rows]
    mvs = [{"t": wiki.clean(r["title"]), "year": r["year"],
            "performer": wiki.clean(r["performer"]),
            "notes": wiki.clean(r["notes"])} for r in mv_rows]

    # ---- Wikidata ----------------------------------------------------------
    sweep = directed_items()
    pages = [f["page"] for f in features] + [d["page"] for d in docs if d["page"]]
    qids = wikidata.qids_for(pages)
    claims = wikidata.claims_for(qids.values())

    for f in features:
        q = qids.get(f["page"])
        f["qid"] = q
        c = claims.get(q) if q else None
        f["pubyears"] = sorted(set(wikidata.pub_years(c))) if c else []
        rt, seen = p2047(c) if c else (None, [])
        f["p2047_seen"] = seen
        f["year_gate"] = bool(c) and wikidata.year_gate(c, f["year"])
        if f["year_gate"] and rt:
            f["runtime"], f["runtime_src"] = rt, "P2047"
        f["p31"] = [s["mainsnak"].get("datavalue", {}).get("value", {}).get("id")
                    for s in (c or {}).get("P31", [])]
        f["article"] = article_facts(f["page"])

    for d in docs:
        q = qids.get(d["page"]) if d["page"] else None
        d["qid"] = q
        c = claims.get(q) if q else None
        rt, seen = p2047(c, lo=1, hi=400) if c else (None, [])
        d["runtime"], d["p2047_seen"] = rt, seen
        d["pubyears"] = sorted(set(wikidata.pub_years(c))) if c else []
        d["p31"] = [s["mainsnak"].get("datavalue", {}).get("value", {}).get("id")
                    for s in (c or {}).get("P31", [])]

    # Match the shorts and the music videos against the sweep by title and
    # year, so "this row cannot be weighted from P2047" is a fact about
    # Wikidata rather than about whether anybody wrote an en-wiki article for
    # it. Most of these have no article at all, which is exactly why the sweep
    # rather than pageprops is the instrument.
    from gwlib.prop import normt
    by_title = {}
    for qid, e in sweep.items():
        by_title.setdefault(normt(e["label"]), []).append((qid, e))

    def match(title, year):
        cand = by_title.get(normt(title), [])
        if not cand:
            cand = [(q, e) for q, e in sweep.items()
                    if normt(e["label"]).startswith(normt(title))]
        cand = [(q, e) for q, e in cand
                if not e["years"] or min(abs(y - year) for y in e["years"]) <= 1]
        return cand[0] if len(cand) == 1 else (None, {})

    for s in shorts:
        q, e = match(s["t"], s["year"])
        s["qid"], s["runtime"] = q, e.get("runtime")
        s["runtime_src"] = "P2047" if s["runtime"] else None
    for v in mvs:
        q, e = match(v["t"], v["year"])
        v["qid"], v["runtime"] = q, e.get("runtime")

    extras = {q: e for q, e in sweep.items()
              if q not in {f["qid"] for f in features}
              and q not in {d["qid"] for d in docs}}
    sweep_labels = sorted(e["label"] for e in sweep.values())

    # Resolve the rank-qualifier items so the shipped note can quote Wikidata's
    # own words for why a value is deprecated or preferred, rather than a
    # paraphrase of them.
    qq = {"Q7727": None, "Q11574": None}
    for f in features:
        for s in f["p2047_seen"]:
            qq[s["unit"]] = None
            for ids in s["quals"].values():
                qq.update({i: None for i in ids})
    ranklabels = labels_for(qq)

    data = {
        "rank_labels": ranklabels,
        "biography": biography(),
        "features": features,
        "documentaries": docs,
        "shorts": shorts,
        "misc": misc,
        "television": tv,
        "music_videos": mvs,
        "sweep_size": len(sweep),
        "sweep_labels": sweep_labels,
        "sweep_extras": [{"qid": q, "label": e["label"], "years": e["years"],
                          "runtime": e["runtime"]}
                         for q, e in sorted(extras.items(),
                                            key=lambda kv: (kv[1]["years"] or [0],
                                                            kv[1]["label"]))],
    }
    out = HERE / "pta_data.json"
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(data, indent=1, ensure_ascii=False) + "\n")

    print("feature films table: %d rows" % len(features))
    for f in features:
        a = f["article"]
        print("   %s  %-26s %8s min  gate=%s  wrote/prod/shot=%d%d%d"
              % (f["year"], f["t"],
                 "%.2f" % f["runtime"] if f["runtime"] else None,
                 f["year_gate"], f["wrote"], f["produced"], f["shot"]))
        print("        dp=%-28s music=%-22s infobox runtime=%s"
              % (a.get("cinematography", "-")[:28], a.get("music", "-")[:22],
                 a.get("runtime", "-")))
        if len(f["p2047_seen"]) > 1 or any(s["rank"] != "normal"
                                           for s in f["p2047_seen"]):
            for s in f["p2047_seen"]:
                why = " ".join("%s=%s" % (p, [ranklabels.get(i, i)
                                              for i in ids])
                               for p, ids in sorted(s["quals"].items()))
                print("        P2047 %8.2f %-8s %-10s -> %s min  %s"
                      % (s["amount"], ranklabels.get(s["unit"], s["unit"]),
                         s["rank"],
                         "%.2f" % s["minutes"] if s["minutes"] else "REFUSED",
                         why))
    print("documentary table: %d rows" % len(docs))
    for d in docs:
        print("   %-5s %-30s %-28s %s min  p31=%s"
              % (d["year"], d["t"], d["credit"],
                 "%.2f" % d["runtime"] if d["runtime"] else None, d["p31"]))
    print("short films: %d — weightable from P2047: %d"
          % (len(shorts), sum(1 for s in shorts if s["runtime"])))
    for s in shorts:
        print("   %s  %-28s %-12s %4s min  %s"
              % (s["year"], s["t"], s["qid"] or "NO ITEM",
                 s["runtime"] or "-", s["tablenote"][:34]))
    print("music videos: %d — with a P57 Wikidata item: %d"
          % (len(mvs), sum(1 for v in mvs if v["qid"])))
    print("misc: %d;  television: %d" % (len(misc), len(tv)))
    bio = data["biography"]
    print("main article ordinals: %s"
          % [(o["said"], o["window"][:60]) for o in bio["ordinals"]])
    for k, v in sorted(bio["sentences"].items()):
        print("   %-14s %s" % (k, v[:150]))
    print("P57 sweep: %d items; %d not on the feature or documentary tables"
          % (len(sweep), len(data["sweep_extras"])))
    print("wrote %s" % out)


if __name__ == "__main__":
    main()
