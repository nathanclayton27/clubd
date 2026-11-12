#!/usr/bin/env python3
"""Collect the Ridley Scott list's source data.

    PYTHONIOENCODING=utf-8 python scratch/ridley/collect.py

One Wikipedia article is the spine — "Ridley Scott filmography" — cached as
raw wikitext under scratch/ridley/cache/ so a re-run is offline and reviewable.

  * "Film > Feature film" is the list. Thirty rows, every one of them a bare
    {{yes}} in the Director column.
  * "Film > Short film" is collected too, five rows, even though the shipped
    list has no shorts section: collecting them turns "no shorts" into a
    checked fact (how many of the five can be weighted at all) rather than a
    preference.
  * "Ridley Scott" itself is cached too, for one table only: its
    directed-features table can run past the filmography's to dated
    announced films, and tools/make_ridley_scott.py asserts its COMING rows
    against it.
  * The As producer / As executive producer bullet lists and the Television
    and Commercials sections are collected only so the shipped "directing
    only" note can name what it leaves out from the article rather than from
    anyone's memory.

RUNTIMES, AND WHY THIS FILM-MAKER MAKES IT HARD

Runtimes come from Wikidata P2047 and from nothing else, gated on a P577
publication year within a year of the table's year. But Ridley Scott is the
alternate-cut director: Blade Runner has five released versions, Kingdom of
Heaven's director's cut runs three quarters of an hour longer than the
theatrical, Legend went out at three different lengths on two continents. So
several of these items carry more than one legitimate P2047, and picking one
takes a rule rather than a max().

gwlib.wikidata.runtime() is rank-blind and returns the longest in-range value.
Here that is wrong three separate ways, all of them present in the live data:

  * Kingdom of Heaven carries 144 qualified "applies to part: theatrical
    version" and 190 qualified "applies to part: director's cut". The longest
    is the director's cut — a different film from the one the 2005 row is
    dated by.
  * Blade Runner carries an unqualified 112 imported from de.wikipedia beside
    an unqualified 116 sourced to a film database. 112 is the PAL-speedup
    number; nothing on the statement says so.
  * Legend carries 114 qualified "director's cut" and an unqualified 125,
    which is neither of the two lengths it was released at. Its own article
    says why: "Scott's first cut of Legend ran 125 minutes long" — a cut
    nobody outside the edit suite ever saw. The longest wins there too.

So `p2047()` below reads statement rank AND the P518 "applies to part"
qualifier, and `pick_runtime()` decides between what is left:

  1. minutes only (Q7727), inside a sane band, deprecated rank dropped;
  2. preferred rank wins outright over normal, as Wikidata intends;
  3. if one distinct value survives, that is the runtime and nothing else is
     consulted. Twenty-six of the twenty-nine released features land here.
     Where such a value disagrees with the film's own article by a few
     minutes it still ships: one source, kept to, is the house rule, and
     mixing in article numbers wherever they were larger would make the total
     a blend of two different kinds of measurement;
  4. only when two or more distinct values survive is there a choice to make,
     and only then do the tie-breaks run:
       a. a value qualified "applies to part: theatrical version" wins
          outright — the row is dated by the theatrical release, so that is
          the release it is measured at (Kingdom of Heaven);
       b. otherwise CORROBORATION. The film's own article states, in its
          infobox runtime field, the length of every version it was released
          at; a value is eligible only if it lands within a minute of one of
          them. This is the article selecting among numbers Wikidata already
          carries — no number is ever typed in from the article. It is what
          drops Blade Runner's PAL-speedup 112 and Legend's never-released
          125-minute first cut;
       c. whatever is left is preferred unqualified over named-alternate-cut,
          and longest inside a bucket — the gwlib rule, correct once ranks
          and cuts have been separated out.

Every value seen, its rank, its qualifier and whether it corroborated is
recorded on the row, so the generator can assert the situation still exists
instead of trusting this docstring.

WHAT IS NOT ON THE LIST, AND HOW THE COLLECTOR PROVES IT

The Dog Stars sits in the table at 2026 and is not a shipped row: its own
article calls it upcoming and states a release date this collection ran
before, and its Wikidata item carries no P2047 at all. Both facts are
recorded (`upcoming`, `release_date`, `collected`) so the generator can
assert them rather than take anyone's word, and so the day it releases the
build fails until the row is added.

Writes scratch/ridley/ridley_data.json.
"""
import datetime
import json
import pathlib
import re
import sys
import urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from gwlib import wiki, wikidata
from gwlib.prop import normt

CACHE = HERE / "cache"
WD_API = "https://www.wikidata.org/w/api.php"

MINUTE = "Q7727"                       # the only unit P2047 is read in here
THEATRICAL = "Q26225765"               # P518 value: theatrical version
FEATURE_COLS = ["year", "title", "director", "producer", "notes"]
SHORT_COLS = ["year", "title", "notes"]


# --------------------------------------------------------------------------
# Wikidata
# --------------------------------------------------------------------------
def p2047(claims, lo=15, hi=300):
    """Every P2047 statement on the item, read at rank and with its P518 cut.

    Returns a list of {amount, unit, rank, parts} — the choosing happens in
    pick_runtime(), which also needs the article, so it is kept separate.
    """
    seen = []
    for st in (claims or {}).get("P2047", []):
        v = st.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        try:
            amt = float(str(v["amount"]).lstrip("+"))
        except (KeyError, TypeError, ValueError):
            continue
        parts = [q.get("datavalue", {}).get("value", {}).get("id")
                 for q in (st.get("qualifiers") or {}).get("P518", [])]
        seen.append({"amount": amt,
                     "unit": str(v.get("unit", "")).rsplit("/", 1)[-1],
                     "rank": st.get("rank", "normal"),
                     "parts": [p for p in parts if p],
                     "in_band": lo <= amt <= hi})
    return seen


def pick_runtime(seen, article_minutes):
    """Choose one runtime from the item's P2047 statements. See the module
    docstring for the steps; returns (minutes|None, why, pool)."""
    live = [s for s in seen
            if s["rank"] != "deprecated" and s["unit"] == MINUTE and s["in_band"]]
    if not live:
        return None, "no live in-band P2047 in minutes", []
    pool = [s for s in live if s["rank"] == "preferred"] or \
           [s for s in live if s["rank"] == "normal"]
    rank_used = "preferred" if pool[0]["rank"] == "preferred" else "normal"
    for s in pool:
        s["corroborated"] = any(abs(s["amount"] - m) <= 1 for m in article_minutes)

    # One value, one answer. No tie-break runs, and in particular the article
    # is not consulted: where the two sources differ by a few minutes on a
    # film with a single released cut, that is two sources rounding, not a
    # choice between cuts, and this list keeps to one source.
    if len({s["amount"] for s in pool}) == 1:
        return int(round(pool[0]["amount"])), \
            "single live value, %s rank" % rank_used, pool

    # Two or more. Now there is genuinely a cut to choose.
    theatrical = [s for s in pool if THEATRICAL in s["parts"]]
    if theatrical:
        return int(round(max(s["amount"] for s in theatrical))), \
            "theatrical-version-qualified, %s rank" % rank_used, pool
    ok = [s for s in pool if s["corroborated"]]
    if not ok:
        return None, ("%d P2047 values and none matches a length the article "
                      "states (%s vs %s)"
                      % (len(pool), sorted(s["amount"] for s in pool),
                         sorted(article_minutes))), pool
    plain = [s for s in ok if not s["parts"]]
    named = [s for s in ok if s["parts"]]
    for bucket, why in ((plain, "unqualified, corroborated by the article's "
                                "stated lengths"),
                        (named, "the only value the article's stated lengths "
                                "corroborate, and it names its cut")):
        if bucket:
            return int(round(max(s["amount"] for s in bucket))), \
                "%s, %s rank" % (why, rank_used), pool
    return None, "nothing survived the buckets", pool


def sweep_directed(qid):
    """Every Wikidata item claiming P57 = Ridley Scott. CirrusSearch rather
    than SPARQL — the query service rate-limits hard. Used only to prove the
    filmography table is not missing a feature."""
    qids, offset = [], 0
    while True:
        q = urllib.parse.urlencode({
            "action": "query", "list": "search", "format": "json",
            "formatversion": "2", "srlimit": "50", "sroffset": str(offset),
            "srsearch": "haswbstatement:P57=%s" % qid})
        d = wiki.get_json(WD_API + "?" + q)
        qids += [x["title"] for x in d["query"]["search"]]
        offset = d.get("continue", {}).get("sroffset")
        if not offset:
            break
    out = {}
    for i in range(0, len(qids), 40):
        q = urllib.parse.urlencode({
            "action": "wbgetentities", "format": "json", "formatversion": "2",
            "ids": "|".join(qids[i:i + 40]),
            "props": "claims|labels|descriptions", "languages": "en"})
        for q2, ent in wiki.get_json(WD_API + "?" + q)["entities"].items():
            c = ent.get("claims", {})
            out[q2] = {
                "label": (ent.get("labels", {}).get("en") or {}).get("value", ""),
                "desc": (ent.get("descriptions", {}).get("en") or {}).get("value", ""),
                "years": sorted(set(wikidata.pub_years(c))),
                "p31": [s["mainsnak"].get("datavalue", {}).get("value", {}).get("id")
                        for s in c.get("P31", [])],
                # P527 "has part": the franchise item declares which films
                # belong to it, which is how the Alien-strand claim in a
                # section intro gets checked instead of assumed
                "parts": [s["mainsnak"].get("datavalue", {}).get("value", {}).get("id")
                          for s in c.get("P527", [])],
                "runtimes": sorted({s["amount"] for s in p2047(c, 1, 400)}),
            }
    return out


def labels_for(qids):
    out = {}
    ids = sorted({q for q in qids if q})
    for i in range(0, len(ids), 40):
        q = urllib.parse.urlencode({
            "action": "wbgetentities", "format": "json", "formatversion": "2",
            "ids": "|".join(ids[i:i + 40]), "props": "labels",
            "languages": "en"})
        for qid, ent in wiki.get_json(WD_API + "?" + q)["entities"].items():
            out[qid] = (ent.get("labels", {}).get("en") or {}).get("value", "")
    return out


# --------------------------------------------------------------------------
# Wikipedia
# --------------------------------------------------------------------------
def section_of(text, head, nexthead):
    i = text.index(head)
    return text[i:text.index(nexthead, i)]


def first_table(seg):
    seg = seg[seg.index("{|"):]
    return seg[:seg.index("\n|}")]


def cells(chunk):
    """A row's raw cells; both one-per-line and inline `||` are honoured."""
    out = []
    for line in chunk.split("\n"):
        line = line.strip()
        if not line.startswith("|") or line.startswith("|}") or line.startswith("|-"):
            continue
        out += [c.strip() for c in line[1:].split("||")]
    return out


def rows(seg, cols):
    """Table rows as dicts, rowspan cells carried down. The Feature film
    table rowspans its Year cell twice (2017 and 2021, the two years with two
    releases each); without the carry every column after it shifts."""
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
        d = dict(zip(cols, row))
        if not re.fullmatch(r"(19|20)\d{2}", d["year"].strip()):
            continue
        d["year"] = int(d["year"])
        out.append(d)
    return out


def wikilink(cell):
    m = re.search(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", cell)
    if m:
        return m.group(1).strip(), wiki.clean(m.group(2) or m.group(1))
    return None, wiki.clean(cell)


RUNTIME_BIT = re.compile(r"(\d{2,3})\s*minutes?\s*(?:\(([^)]*)\))?", re.I)
FILM_DATE = re.compile(r"\{\{\s*Film date\s*\|\s*(\d{4})\s*\|\s*(\d{1,2})\s*\|"
                       r"\s*(\d{1,2})", re.I)
UPCOMING = re.compile(r"is an? upcoming|is scheduled to be released|"
                      r"scheduled for release", re.I)
# run over the CLEANED article, not the wikitext: the sentence that counts
# the versions of Blade Runner puts the phrase inside a piped wikilink
# ("Seven different [[versions of Blade Runner|versions of ...]] exist"), so
# a wikitext-level pattern finds a vaguer sentence further down the page
# instead. Preferring the "different versions" phrasing picks the counted
# claim over the "Several versions have been shown" one.
VERSIONS_CLAIM = [re.compile(r"\b([A-Z][a-z]+|\d+) different versions of\b"),
                  re.compile(r"\b([A-Z][a-z]+|\d+) versions of\b")]
VERSION_HEAD = re.compile(r"^=+\s*(.*(?:version|cut|edition)[^=]*?)\s*=+\s*$",
                          re.I | re.M)


def article_facts(page):
    """The film's own infobox and the handful of article facts the runtime
    picker and the row notes lean on.

    `runtimes` is the pairs the infobox runtime field states: [(minutes,
    label)], where the label is the parenthetical the field itself carries —
    "(director's cut)", "(European version)" — or "" when the field states a
    single bare number. This is what lets the picker say which of Wikidata's
    numbers belongs to a version that was actually released, and it is what
    the row notes name a cut from. It is never a runtime source: the shipped
    number is always the P2047 value it selected.

    `version_heads` and `versions_claim` are the article's own account of how
    many versions of itself exist — the section headings that say "version",
    "cut" or "edition", and any "Seven different versions of ''Blade Runner''
    exist" sentence. The alternate-cuts note is written off these rather than
    off anybody's memory of which Ridley Scott films were recut.
    """
    t = wiki.wikitext(page, cache_dir=CACHE)
    fb = wiki.infobox(t) if t else None
    if not fb:
        return {}
    out = {}
    for f in ("runtime", "country", "language", "distributor", "studio",
              "based_on", "screenplay", "writer", "story", "starring",
              "released", "budget"):
        v = wiki.clean(fb(f))
        if v:
            out[f] = v
    out["runtimes"] = [[int(m.group(1)), (m.group(2) or "").strip()]
                       for m in RUNTIME_BIT.finditer(out.get("runtime", ""))]
    raw_released = fb("released")
    d = FILM_DATE.search(raw_released)
    out["release_date"] = "%04d-%02d-%02d" % tuple(int(x) for x in d.groups()) \
        if d else None
    # comments stripped before cleaning: Blade Runner's lead opens with an
    # editors' note about genre that would otherwise land in the text, and
    # kept long enough to reach the end of the lead section, where the
    # sentence about which cut Scott controlled lives
    lead = wiki.clean(re.sub(r"<!--.*?-->", "", lead_of(t)[:6000],
                             flags=re.S))[:3000]
    out["lead"] = lead
    out["upcoming"] = bool(UPCOMING.search(lead))
    cleaned = wiki.clean(t)
    out["versions_claim"] = None
    for pat in VERSIONS_CLAIM:
        m = pat.search(cleaned)
        if m:
            out["versions_claim"] = cleaned[m.start():m.start() + 140]
            break
    out["version_heads"] = sorted({wiki.clean(h) for h in VERSION_HEAD.findall(t)})
    return out


def lead_of(text):
    """The article's prose, with the infobox counted past brace by brace
    (anchoring on ^''' misses a title wrapped in a template)."""
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


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    art = wiki.wikitext("Ridley Scott filmography", cache_dir=CACHE)
    # Not parsed here: the generator reads its directed-features table for
    # the COMING rows. Fetched here so a re-run refreshes that snapshot too.
    wiki.wikitext("Ridley Scott", cache_dir=CACHE)

    film_chunk = section_of(art, "==Film==", "==Television==")
    short_rows = rows(first_table(section_of(film_chunk, "'''Short film'''",
                                             "'''Feature film'''")), SHORT_COLS)
    feat_seg = film_chunk[film_chunk.index("'''Feature film'''"):]
    feat_rows = rows(first_table(feat_seg), FEATURE_COLS)

    assert all(r["director"].strip().lower() == "{{yes}}" for r in feat_rows), \
        [r["title"] for r in feat_rows
         if r["director"].strip().lower() != "{{yes}}"]

    films = []
    for r in feat_rows:
        page, label = wikilink(r["title"])
        films.append({
            "t": label,
            "page": page or label,
            "year": r["year"],
            "producer_cell": r["producer"].strip(),
            "produced": r["producer"].strip().lower() == "{{yes}}",
            "exec_produced": "partial" in r["producer"].strip().lower(),
            "tablenote": wiki.clean(r["notes"]),
        })
    films.sort(key=lambda f: (f["year"], f["t"]))

    shorts = [{"t": wikilink(r["title"])[1], "page": wikilink(r["title"])[0],
               "year": r["year"], "tablenote": wiki.clean(r["notes"])}
              for r in short_rows]

    # the bullet lists and the television section, for the "directing only" note
    def bullets(seg):
        out = []
        for line in seg.split("\n"):
            if line.startswith("*"):
                out.append(wiki.clean(line[1:]))
            elif out:
                break
        return out

    other = {}
    for head in ("As producer", "As executive producer"):
        i = feat_seg.index("'''%s'''" % head)
        other[head] = bullets(feat_seg[i + len(head) + 6:])
    tv_seg = section_of(art, "==Television==", "==Commercials==")
    tv = {}
    for head in ("Designer", "Director", "Developer", "Producer",
                 "Executive producer"):
        i = tv_seg.index("'''%s'''" % head)
        tv[head] = bullets(tv_seg[i + len(head) + 6:])
    ads = bullets(section_of(art, "==Commercials==", "==See also==")
                  [len("==Commercials==\n{{ref improve|date=November 2017}}\n"):])

    # ---- Wikidata --------------------------------------------------------
    # cached to disk beside the wikitext, so a re-run to fix a parse bug does
    # not re-hammer the API and a reviewer can read exactly what was answered
    def cached(name, fn):
        f = CACHE / ("%s.json" % name)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8"))
        v = fn()
        with f.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(v, indent=1, ensure_ascii=False) + "\n")
        return v

    def trimmed_claims():
        """The four properties anything here reads, and no more. The full
        wbgetentities answer for these thirty-odd items is six megabytes of
        claims nobody looks at; cached this way it is a few dozen kilobytes a
        reviewer can actually open."""
        got = wikidata.claims_for(qids.values())
        keep = ("P2047", "P577", "P31", "P527")
        return {q: {k: v for k, v in c.items() if k in keep}
                for q, c in got.items()}

    pages = [f["page"] for f in films] + [s["page"] for s in shorts if s["page"]]
    him = cached("wd-him", lambda: wikidata.qids_for(["Ridley Scott"]))["Ridley Scott"]
    qids = cached("wd-qids", lambda: wikidata.qids_for(pages))
    claims = cached("wd-claims", trimmed_claims)
    sweep = cached("wd-sweep", lambda: sweep_directed(him))

    part_qids = set()
    for f in films:
        f["article"] = article_facts(f["page"])
        f["qid"] = qids.get(f["page"])
        c = claims.get(f["qid"]) if f["qid"] else None
        f["pubyears"] = sorted(set(wikidata.pub_years(c))) if c else []
        f["year_gate"] = bool(c) and wikidata.year_gate(c, f["year"])
        seen = p2047(c) if c else []
        for s in seen:
            part_qids.update(s["parts"])
        article_minutes = [m for m, _ in f["article"].get("runtimes", [])]
        rt, why, pool = pick_runtime(seen, article_minutes)
        if not f["year_gate"]:
            rt, why = None, "release year does not match the table's year"
        f["p2047_seen"] = seen
        f["runtime"] = rt
        f["runtime_src"] = "P2047" if rt else None
        f["runtime_why"] = why
        f["cuts"] = f["article"].get("runtimes", [])
        f["upcoming"] = f["article"].get("upcoming")
        f["release_date"] = f["article"].get("release_date")

    lab = cached("wd-partlabels", lambda: labels_for(part_qids))
    for f in films:
        for s in f["p2047_seen"]:
            s["part_labels"] = [lab.get(p, p) for p in s["parts"]]

    for s in shorts:
        q = qids.get(s["page"]) if s["page"] else None
        c = claims.get(q) if q else None
        seen = p2047(c, 1, 400) if c else []
        live = [x for x in seen if x["rank"] != "deprecated" and x["unit"] == MINUTE]
        s["qid"] = q
        s["runtime"] = int(round(max(x["amount"] for x in live))) if live else None
        s["p2047_seen"] = seen

    known = {f["qid"] for f in films} | {s["qid"] for s in shorts}
    extras = {q: e for q, e in sweep.items() if q not in known}

    data = {
        "collected": datetime.date.today().isoformat(),
        "films": films,
        "shorts": shorts,
        "producer_only": other["As producer"],
        "exec_producer_only": other["As executive producer"],
        "television": tv,
        "commercials": ads,
        "him": him,
        "sweep_size": len(sweep),
        "sweep_extras": [{"qid": q, "label": e["label"], "desc": e["desc"],
                          "years": e["years"], "runtimes": e["runtimes"],
                          "p31": e["p31"], "parts": e["parts"]}
                         for q, e in sorted(extras.items(),
                                            key=lambda kv: kv[1]["label"])],
    }
    out = HERE / "ridley_data.json"
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(data, indent=1, ensure_ascii=False) + "\n")

    print("collected %s — feature film rows in the table: %d"
          % (data["collected"], len(films)))
    for f in films:
        alt = [(s["amount"], s["rank"], "/".join(s["part_labels"]) or "-")
               for s in f["p2047_seen"]]
        print("  %s %-38s %4s min  %-52s  P2047 %s%s"
              % (f["year"], f["t"][:38], f["runtime"], f["runtime_why"][:52],
                 alt, "   UPCOMING (%s)" % f["release_date"]
                 if f["upcoming"] else ""))
    multi = [f for f in films if len({s["amount"] for s in f["p2047_seen"]}) > 1]
    print("\nitems carrying more than one P2047 value: %d — %s"
          % (len(multi), [f["t"] for f in multi]))
    cuts = [f for f in films if len(f["cuts"]) > 1]
    print("articles stating more than one released length: %d — %s"
          % (len(cuts), [(f["t"], f["cuts"]) for f in cuts]))
    vh = [f for f in films if f["article"].get("version_heads")]
    print("articles with a version/cut/edition section: %d" % len(vh))
    for f in vh:
        print("   %-30s %s  %s" % (f["t"][:30], f["article"]["version_heads"],
                                   f["article"].get("versions_claim") or ""))
    print("upcoming: %s" % [(f["t"], f["release_date"]) for f in films
                            if f["upcoming"]])
    print("disagreements between the shipped P2047 and the article's field:")
    for f in films:
        mins = [m for m, _ in f["cuts"]]
        if f["runtime"] and mins and not any(abs(f["runtime"] - m) <= 1
                                             for m in mins):
            print("   %-30s wikidata %s   article %s"
                  % (f["t"][:30], f["runtime"], mins))
    print("\nshorts: %d" % len(shorts))
    for s in shorts:
        print("   %s  %-24s %-12s %s min"
              % (s["year"], s["t"], s["qid"] or "NO ITEM", s["runtime"] or "-"))
    print("\nP57 sweep: %d items; not matched to a table row: %d"
          % (len(sweep), len(extras)))
    for e in data["sweep_extras"]:
        print("   %-12s %-44s %s  %s"
              % (e["qid"], e["label"][:44], e["years"], e["runtimes"]))
    print("\nwrote %s" % out)


if __name__ == "__main__":
    main()
