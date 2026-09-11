#!/usr/bin/env python3
"""Cache Marvel Database (marvel.fandom.com) pages under scratch/fantastic-four/mdb.

Two jobs:

  python fetch_mdb.py cats     -> category members for each volume, one json per
                                  category (the definitive issue enumeration)
  python fetch_mdb.py pages    -> the wikitext of every issue page named by those
                                  categories, 50 at a time, into mdb/pages.json

Marvel Database is a MediaWiki, so both are plain API reads. Nothing here
interprets the data; parse.py does that.
"""
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://marvel.fandom.com/api.php"
UA = "GroupWatch/1.0 (reading-list builder)"
HERE = pathlib.Path(__file__).resolve().parent
CACHE = HERE / "mdb"

CATEGORIES = [
    "Fantastic Four Vol 1",
    "Fantastic Four Vol 2",
    "Fantastic Four Vol 3",
    "Fantastic Four Annual Vol 1",
    "Fantastic Four Unlimited Vol 1",
]


def api(params, tries=6):
    q = urllib.parse.urlencode(params)
    for n in range(tries):
        try:
            req = urllib.request.Request(API + "?" + q, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or n == tries - 1:
                raise
            time.sleep(8 * (n + 1))
        except (urllib.error.URLError, TimeoutError):
            if n == tries - 1:
                raise
            time.sleep(5)


def cats():
    CACHE.mkdir(parents=True, exist_ok=True)
    for cat in CATEGORIES:
        out, cont = [], None
        while True:
            p = {"action": "query", "list": "categorymembers",
                 "cmtitle": "Category:" + cat, "cmlimit": "500",
                 "cmtype": "page", "format": "json", "formatversion": "2"}
            if cont:
                p["cmcontinue"] = cont
            d = api(p)
            out += [m["title"] for m in d["query"]["categorymembers"]]
            cont = (d.get("continue") or {}).get("cmcontinue")
            if not cont:
                break
            time.sleep(0.5)
        f = CACHE / (re.sub(r"[^A-Za-z0-9]+", "-", cat) + ".json")
        f.write_text(json.dumps(out, indent=1), encoding="utf-8")
        print("%-34s %4d pages -> %s" % (cat, len(out), f.name), flush=True)
        time.sleep(0.5)


def pages():
    want = []
    for cat in CATEGORIES:
        f = CACHE / (re.sub(r"[^A-Za-z0-9]+", "-", cat) + ".json")
        want += json.loads(f.read_text(encoding="utf-8"))
    dest = CACHE / "pages.json"
    have = json.loads(dest.read_text(encoding="utf-8")) if dest.exists() else {}
    todo = [t for t in want if t not in have]
    print("%d pages wanted, %d already cached, %d to fetch"
          % (len(want), len(want) - len(todo), len(todo)), flush=True)
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        d = api({"action": "query", "prop": "revisions", "rvprop": "content",
                 "rvslots": "main", "titles": "|".join(batch),
                 "format": "json", "formatversion": "2"})
        for p in d["query"]["pages"]:
            if "revisions" not in p:
                continue
            have[p["title"]] = p["revisions"][0]["slots"]["main"]["content"]
        dest.write_text(json.dumps(have, ensure_ascii=False), encoding="utf-8")
        print("  %d/%d" % (min(i + 50, len(todo)), len(todo)), flush=True)
        time.sleep(0.4)
    print("cached %d pages in %s" % (len(have), dest), flush=True)


if __name__ == "__main__":
    {"cats": cats, "pages": pages}[sys.argv[1]]()
