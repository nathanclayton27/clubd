#!/usr/bin/env python3
"""Parse the cached Marvel Database issue pages into tools/data/captain-america.json.

    PYTHONIOENCODING=utf-8 python scratch/captain-america/parse.py

One record per issue: cover month and year, the first story's title, the
story-arc name the wiki files it under, the page count the infobox gives,
and every writer credited on any story in the issue. Nothing here is
interpreted — the generator does the interpreting and asserts against
these fields.
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

# [ \t] and not \s on either side of the "=": \s matches a newline, so an
# empty field (Writer1_2 = , which Marvel Database leaves in place) swallowed
# the line below it and issue #250 came out credited to "| Penciler1_1 =
# John Byrne".
FIELD = re.compile(r"^\|[ \t]*([A-Za-z0-9_:-]+)[ \t]*=[ \t]*(.*)$", re.M)
LINK = re.compile(r"\[\[([^\]|]+)\|([^\]]+)\]\]")

# The Appearing blocks are the only multi-line fields in the template, and
# their bullet lists are what the one-line FIELD scan has to be kept away
# from. Cutting the page at the first "| Appearing1" did that and threw away
# everything after it, which on this wiki is where the credits usually are:
# Captain America Vol 4 #8, #9, #15 and #16 came out with no writer at all,
# and every second-feature credit in Tales of Suspense was lost — the Cap
# strip is story 2 there, so the list had Stan Lee down as NOT credited on
# #68 and #99 when the wiki credits him on the Captain America story in both.
# So drop each Appearing block's body instead, up to the next field line, and
# scan the rest of the page.
APPEARING = re.compile(
    r"^\|[ \t]*Appearing\d+[ \t]*=.*?(?=^\|[ \t]*[A-Za-z0-9_:-]+[ \t]*=)",
    re.M | re.S)


def clean(v):
    v = re.sub(r"<!--.*?-->", "", v or "", flags=re.S)
    v = LINK.sub(r"\2", v)
    v = re.sub(r"\[\[([^\]]+)\]\]", r"\1", v)
    v = re.sub(r"<ref.*?</ref>", "", v, flags=re.S)
    v = re.sub(r"<[^>]+>", " ", v)
    v = re.sub(r"'''?", "", v)
    return re.sub(r"\s+", " ", v).strip()


def fields(text):
    """Flat {name: value} of the comic template's one-line fields."""
    body = APPEARING.sub("", text)
    return {m.group(1): clean(m.group(2)) for m in FIELD.finditer(body)}


def main():
    files = sorted(HERE.glob("text-*.json"))
    assert files, "run fetch.py first"
    raw = {}
    for f in files:
        raw.update(json.loads(f.read_text(encoding="utf-8")))
    assert len(raw) > 600, "only %d issue pages cached" % len(raw)

    out, redirects = {}, {}
    for title, text in raw.items():
        series, num = title.rsplit(" ", 1)
        m = re.match(r"\s*#REDIRECT\s*\[\[([^\]]+)\]\]", text, re.I)
        if m:
            # A volume's page can be a pointer at another volume's issue —
            # Captain America Vol 1 600 redirects to Vol 5 600. Those are not
            # issues of the volume whose prefix found them.
            redirects.setdefault(series, {})[num] = m.group(1).strip()
            continue
        fl = fields(text)
        writers = sorted({v for k, v in fl.items()
                          if re.match(r"^Writer\d+_\d+$", k)
                          and v and v.upper() != "N/A"})
        rec = {
            "n": int(num),
            "year": int(fl["Year"]) if re.match(r"^\d{4}$", fl.get("Year", "")) else None,
            "month": fl.get("Month", ""),
            "story": fl.get("StoryTitle1", ""),
            "arc": re.sub(r"\s*\(\d{4}\)$", "", fl.get("StoryArc1", "")),
            "pages": int(fl["Pages"]) if re.match(r"^\d+$", fl.get("Pages", "")) else None,
            "writers": writers,
        }
        out.setdefault(series, {})[num] = rec

    for series, issues in out.items():
        blank = [n for n, r in issues.items() if r["year"] is None]
        assert not blank, "no cover year on %s %s" % (series, blank[:5])

    # An issue with no writer at all is nearly always a parse failure rather
    # than a fact about the wiki, and the last one hid behind a `writers: []`
    # that nothing looked at. One page on this run genuinely carries no Writer
    # field; anything else joining it means the scan has lost credits again.
    nocredit = sorted("%s %s" % (s, n) for s, iss in out.items()
                      for n, r in iss.items() if not r["writers"])
    assert nocredit == ["Captain America Vol 1 216"], \
        "issues parsed with no writer credit at all: %s" % nocredit

    out = {"issues": out, "redirects": redirects}
    dest = ROOT / "tools" / "data" / "captain-america.json"
    with dest.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=1,
                           sort_keys=True) + "\n")
    print("%d issues across %d series -> %s"
          % (sum(len(v) for v in out["issues"].values()),
             len(out["issues"]), dest.relative_to(ROOT)))
    for series in sorted(out["issues"]):
        ns = sorted(int(n) for n in out["issues"][series])
        print("  %-34s %4d  #%d-#%d" % (series, len(ns), ns[0], ns[-1]))


if __name__ == "__main__":
    sys.exit(main())
