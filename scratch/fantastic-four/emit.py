#!/usr/bin/env python3
"""Write tools/data/fantastic-four.json — the committed extract.

scratch/ is gitignored, so the cached Marvel Database pages cannot travel with
the generator. What travels is this: one record per issue carrying only fields
the Comic Template states outright, plus, for each first appearance the page
marks with {{1st}}, how many Fantastic Four issues in the whole corpus link
that character at all. The generator applies its thresholds to that number, so
the cut-off is visible in the generator rather than baked in here.

    python emit.py
"""
import html
import json
import pathlib
import re
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PAGES = json.loads((HERE / "mdb" / "pages.json").read_text(encoding="utf-8"))
rows = json.loads((HERE / "issues.json").read_text(encoding="utf-8"))

appears = Counter()
for title, text in PAGES.items():
    for page in set(re.findall(r"\[\[([^\]|]+\(Earth-616\))\|", text)):
        appears[page] += 1

# Marvel Database marks a first appearance two ways and both are live on the
# same page: the marker can wrap the link, {{1st|[[Page|Label]]}}, or trail it,
# [[Page|Label]] {{1st}}. Reading only the trailing form missed the debut of
# the Fantastic Four themselves in Fantastic Four #1.
# {{1st Unnamed}} is a third thing and deliberately matches neither.
LINK = r"\[\[([^\]|]+\(Earth-616\))\|([^\]]+)\]\]"
DEBUT = re.compile(r"\{\{1st(?:m)?\s*\|\s*%s" % LINK + r"|" +
                   r"%s[^\n*]*?\{\{1st(?:m)?\}\}" % LINK)


def unesc(s):
    """Entity-fold and drop editor comments — FF #231 credits Roger Stern
    inside an HTML comment, and the raw field truncates mid-tag."""
    s = re.sub(r"<!--.*?(?:-->|$)", "", s or "", flags=re.S)
    s = re.sub(r"<[^>]*>?", "", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip(" ,;")


out = []
for r in rows:
    text = PAGES[r["page"]]
    debuts, seen = [], set()
    for a_page, a_label, b_page, b_label in DEBUT.findall(text):
        page, labelx = (a_page or b_page), unesc(a_label or b_label)
        # the wiki's label disambiguates with a real name in brackets —
        # "Red Ghost (Ivan Kragoff)", "Thing (Benjamin "Ben" Grimm)". A row
        # wants the name on the cover, not the parenthesis.
        labelx = re.sub(r"\s*\([^()]*\)\s*$", "", labelx).strip()
        if not labelx or labelx in seen:
            continue
        seen.add(labelx)
        debuts.append([labelx, appears[page]])
    out.append({
        "vol": r["vol"], "num": r["num"], "legacy": r["legacy"],
        "annual": r["annual"], "unlimited": r["unlimited"],
        "title": unesc(r["title"]),
        "month": r["month"], "year": int(r["year"]),
        "writers": [unesc(w) for w in r["writers"][:3]],
        "pencilers": [unesc(p) for p in r["pencilers"][:2]],
        # source order, not count order: the wiki lists a debut under Featured,
        # then Supporting, then Antagonists, which is the order a row wants to
        # name them in. The count is for the star threshold, nothing else.
        "debuts": debuts,
    })

dest = ROOT / "tools" / "data" / "fantastic-four.json"
# newline="\n": the default on Windows writes CRLF and git rewrites the whole
# file on the next checkout, which makes the diff useless.
with dest.open("w", encoding="utf-8", newline="\n") as fh:
    fh.write(json.dumps({
    "source": "Marvel Database (marvel.fandom.com), Comic Template fields, "
              "read 2026-09-11 via the MediaWiki API",
    "categories": ["Fantastic Four Vol 1", "Fantastic Four Vol 2",
                   "Fantastic Four Vol 3", "Fantastic Four Annual Vol 1",
                   "Fantastic Four Unlimited Vol 1"],
    "note": "`legacy` is the continuous issue number: Vol 1 ran to #416 and "
            "Vol 2 added 13, so Vol 3 #1 is #430 and Vol 3 #70 is #499, which "
            "is why the book could resume at #500. `debuts` pairs a character "
            "Marvel Database marks {{1st}} in that issue with the number of "
            "issues in these five volumes that link the character at all.",
        "issues": out,
    }, indent=1, ensure_ascii=False) + "\n")
print("wrote %s — %d issues, %d bytes" % (dest, len(out), dest.stat().st_size))
