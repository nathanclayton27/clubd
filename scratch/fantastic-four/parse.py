#!/usr/bin/env python3
"""Turn the cached Marvel Database pages into one issue table.

Reads mdb/pages.json (fetch_mdb.py) and writes issues.json: one record per
issue, carrying only fields the Comic Template states outright —

    vol, num, legacy, title (StoryTitle1), month, year,
    writers, pencilers, arcs, debuts

`debuts` are the character links the page marks with {{1st}} or {{1stm}},
which is how Marvel Database records a first appearance. Nothing is inferred
and nothing is written by hand: if the template does not say it, it is not
here.
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
PAGES = json.loads((HERE / "mdb" / "pages.json").read_text(encoding="utf-8"))

# Vol 3 resumed Vol 1's numbering after its own #70: #70 is legacy #499.
V3_LEGACY_OFFSET = 429


def field(text, name):
    m = re.search(r"^\s*\|\s*%s\s*=[ \t]*(.*?)(?=\n\s*\|\s*[A-Za-z0-9_-]+\s*=|\n\}\})"
                  % re.escape(name), text, re.M | re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def multi(text, prefix):
    """Writer1_1, Writer1_2, ... in order, de-duplicated."""
    out = []
    for m in re.finditer(r"^\s*\|\s*%s\d+_\d+\s*=[ \t]*(.+)$" % prefix, text, re.M):
        v = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", m.group(1)).strip()
        v = v.replace("[[", "").replace("]]", "").strip()
        if v and v not in out and v.lower() not in ("n/a", "none"):
            out.append(v)
    return out


DEBUT = re.compile(r"\[\[([^\]|]+)\|([^\]]+)\]\][^\n*]*?\{\{1st(?:m)?\}\}")


def parse_one(title, text):
    num = title.rsplit(" ", 1)[-1]
    vol = int(re.search(r"Vol (\d+)", title).group(1))
    annual = "Annual" in title
    unlimited = "Unlimited" in title
    arcs = [field(text, "StoryArc%d" % i) for i in range(1, 4)]
    debuts = []
    for m in DEBUT.finditer(text):
        page, label = m.group(1), m.group(2)
        if "(Earth-616)" not in page:
            continue
        if label not in debuts:
            debuts.append(label)
    legacy = None
    if not annual and not unlimited:
        try:
            n = float(num)
            if vol == 1:
                legacy = n
            elif vol == 3:
                legacy = n if n >= 500 else n + V3_LEGACY_OFFSET
        except ValueError:
            legacy = None
    return {
        "page": title, "vol": vol, "num": num, "annual": annual,
        "unlimited": unlimited, "legacy": legacy,
        "title": re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2",
                        field(text, "StoryTitle1")).replace("[[", "").replace("]]", ""),
        "month": field(text, "Month"), "year": field(text, "Year"),
        "writers": multi(text, "Writer"), "pencilers": multi(text, "Penciler"),
        "arcs": [a for a in arcs if a], "debuts": debuts,
    }


def sortkey(r):
    try:
        n = float(r["num"])
    except ValueError:
        n = 0.5 if r["num"] == "½" else 9999
    return (r["vol"], r["annual"] or r["unlimited"], n)


def main():
    rows = [parse_one(t, x) for t, x in PAGES.items()]
    rows.sort(key=sortkey)
    out = HERE / "issues.json"
    out.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    print("parsed %d issues -> %s" % (len(rows), out.name))
    missing = [r["page"] for r in rows if not r["year"]]
    print("no cover year on %d: %s" % (len(missing), missing[:6]))


if __name__ == "__main__":
    main()
