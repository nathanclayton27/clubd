#!/usr/bin/env python3
"""Reduce the cached Marvel Database wikitext to one row per issue.

Writes two files:

  scratch/daredevil/parsed.json  every issue of every volume fetched
  tools/data/daredevil.json      the trimmed, committed table the generator
                                 reads — the volumes the reading list touches

Each row carries the volume, the issue number, the cover month and year, the
on-sale date, the writers credited on every story in the issue ("lead" is the
credit on the issue's first story, which is what a run boundary actually
means), the lead penciler, the story titles and the story arcs.

Every field pattern is line-bounded on purpose: a lazy `(.*?)\\s*$` under
re.MULTILINE happily swallows newlines to reach a later line's end, and the
first draft of this file credited Daredevil #164 to "| Penciler2_1 = Frank
Miller" because of it.
"""
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
LINE = r"^\|\s*%s\s*=([^\n]*)$"

# The volumes the reading list draws on. Daredevil Vol 1 is trimmed to the
# stretch around Miller's two stints; the rest ship whole.
KEEP = {
    "Daredevil Vol 1": (150, 240),
    "Daredevil Vol 2": None,
    "Daredevil Vol 3": None,
    "Daredevil Vol 4": None,
    "Daredevil Vol 5": None,
    "Daredevil Vol 6": None,
    "Daredevil Vol 7": None,
    "Daredevil: The Man Without Fear Vol 1": None,
    "Daredevil: Woman Without Fear Vol 1": None,
    "Devil's Reign Vol 1": None,
    "Shadowland Vol 1": None,
    "Daredevil: Reborn Vol 1": None,
}


def field(t, name):
    m = re.search(LINE % re.escape(name), t, re.M)
    return m.group(1) if m else ""


def clean(v):
    v = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", v)
    v = re.sub(r"\[\[([^\]]+)\]\]", r"\1", v)
    v = re.sub(r"\{\{[^{}]*\}\}", "", v)
    v = re.sub(r"<[^>]+>", " ", v)
    v = re.sub(r"\s+", " ", v).replace("'''", "").replace("''", "").strip()
    # the wiki editorialises inside a few credit fields ("Denny O'Neil (his
    # debut on the book)"); a credit is a name, so drop the aside
    return re.sub(r"\s*\([^()]*\)\s*$", "", v).strip()


def rows_from(data):
    rows = []
    for vol, pages in data.items():
        pat = re.compile(r"^%s (\d+(?:\.\d+)?)$" % re.escape(vol))
        for title, t in pages.items():
            m = pat.match(title)
            if not m:
                continue
            num = m.group(1)
            writers, lead = [], []
            for mm in re.finditer(r"^\|\s*Writer(\d+)_(\d+)\s*=([^\n]*)$", t, re.M):
                w = clean(mm.group(3))
                if not w:
                    continue
                if w not in writers:
                    writers.append(w)
                if mm.group(1) == "1" and w not in lead:
                    lead.append(w)
            titles = [clean(x) for x in re.findall(LINE % r"StoryTitle\d+", t, re.M)]
            arcs = [clean(x) for x in re.findall(LINE % r"StoryArc\d+", t, re.M)]
            reprints = [clean(x) for x in re.findall(LINE % r"ReprintOf\d+", t, re.M)]
            rows.append({
                "vol": vol,
                "num": float(num) if "." in num else int(num),
                "numtext": num,
                "month": clean(field(t, "Month")),
                "year": clean(field(t, "Year")),
                "released": clean(field(t, "ReleaseDate")),
                "legacy": clean(field(t, "LegacyNumber")),
                "writers": writers,
                "lead": lead,
                "penciler": clean(field(t, "Penciler1_1")),
                "titles": [x for x in titles if x],
                "arcs": [x for x in arcs if x],
                "reprints": [x for x in reprints if x],
            })
    rows.sort(key=lambda r: (r["vol"], r["num"]))
    return rows


def main():
    data = json.loads((HERE / "issues.json").read_text(encoding="utf-8"))
    rows = rows_from(data)
    with (HERE / "parsed.json").open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rows, ensure_ascii=False, indent=1))
    print("%d issues parsed" % len(rows))

    keep = []
    for r in rows:
        if r["vol"] not in KEEP:
            continue
        span = KEEP[r["vol"]]
        if span and not (span[0] <= r["num"] <= span[1]):
            continue
        if not r["writers"]and not r["reprints"]:
            continue  # redirect stubs for legacy numbering carry no credits
        keep.append(r)
    vols = {}
    for title, v in json.loads(
            (HERE / "volumes.json").read_text(encoding="utf-8")).items():
        if title not in KEEP:
            continue
        vols[title] = {
            "url": v["url"],
            "publisher": clean(field(v["wikitext"], "publisher")),
            "years": clean(field(v["wikitext"], "years_published")),
        }
    assert set(vols) == set(KEEP), \
        "volume pages missing: %s" % sorted(set(KEEP) - set(vols))

    out = {
        "source": "Marvel Database (marvel.fandom.com), read through api.php: "
                  "list=allpages for each volume's issue pages, then "
                  "prop=revisions for each page's Comic Template infobox, and "
                  "prop=revisions|info for the volume pages themselves.",
        "fetched": "2026-09-11",
        "harvester": "scratch/daredevil/fetch.py + scratch/daredevil/parse.py",
        "volumes": vols,
        "issues": keep,
    }
    dst = ROOT / "tools" / "data" / "daredevil.json"
    with dst.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print("wrote %s (%d issues)" % (dst, len(keep)))


if __name__ == "__main__":
    main()
