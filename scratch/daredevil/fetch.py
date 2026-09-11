#!/usr/bin/env python3
"""Machine-read every Daredevil issue from the Marvel Database (marvel.fandom.com).

Two API calls do the work:
  list=allpages&apprefix=<Volume>   -> the issue pages that exist in a volume
  prop=revisions (50 titles a time) -> each issue's infobox: writer, title, date

Nothing here is typed from memory; the cache under this directory is the
evidence for every row the generator emits.
"""
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
API = "https://marvel.fandom.com/api.php"
UA = "GroupWatch/1.0 (reading-list builder)"

VOLUMES = [
    "Daredevil Vol 1", "Daredevil Vol 2", "Daredevil Vol 3", "Daredevil Vol 4",
    "Daredevil Vol 5", "Daredevil Vol 6", "Daredevil Vol 7", "Daredevil Vol 8",
    "Daredevil: The Man Without Fear Vol 1",
    "Daredevil: Love and War Vol 1",
    "Daredevil: Woman Without Fear Vol 1",
    "Devil's Reign Vol 1",
    "Daredevil: Born Again Vol 1",
    "Daredevil: End of Days Vol 1",
    "Daredevil: Reborn Vol 1",
    "Shadowland Vol 1",
    "Daredevil: Black Armor Vol 1",
    "Daredevil Annual Vol 1",
]


def get(params):
    params = dict(params, format="json", formatversion="2")
    url = API + "?" + urllib.parse.urlencode(params)
    for n in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001 - retry anything transient
            if n == 5:
                raise
            print("  retry %d (%s)" % (n + 1, e))
            time.sleep(4 * (n + 1))


def allpages(prefix):
    """Every page whose title starts with '<prefix> ' - the volume's issues."""
    out, cont = [], None
    while True:
        p = {"action": "query", "list": "allpages", "apprefix": prefix + " ",
             "aplimit": "500", "apnamespace": "0"}
        if cont:
            p["apcontinue"] = cont
        d = get(p)
        out += [x["title"] for x in d["query"]["allpages"]]
        cont = (d.get("continue") or {}).get("apcontinue")
        if not cont:
            return out
        time.sleep(0.5)


def contents(titles):
    """Wikitext for up to 50 pages in one call."""
    out = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        d = get({"action": "query", "prop": "revisions", "rvprop": "content",
                 "rvslots": "main", "titles": "|".join(chunk)})
        for pg in d["query"]["pages"]:
            if "revisions" in pg:
                out[pg["title"]] = pg["revisions"][0]["slots"]["main"]["content"]
        print("    %d/%d" % (min(i + 50, len(titles)), len(titles)))
        time.sleep(0.6)
    return out


def volume_pages():
    """The volume pages themselves: publisher/imprint, and the canonical URL
    the property's section headers link to. Fetched rather than typed, because
    a header link nobody checked is a 404 waiting to ship."""
    out = {}
    for i in range(0, len(VOLUMES), 20):
        chunk = VOLUMES[i:i + 20]
        d = get({"action": "query", "prop": "revisions|info",
                 "rvprop": "content", "rvslots": "main", "inprop": "url",
                 "titles": "|".join(chunk)})
        for pg in d["query"]["pages"]:
            if pg.get("missing"):
                continue
            out[pg["title"]] = {
                "url": pg["fullurl"],
                "wikitext": pg["revisions"][0]["slots"]["main"]["content"],
            }
        time.sleep(0.6)
    return out


def main():
    cache = HERE / "issues.json"
    data = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
    for vol in VOLUMES:
        if vol in data:
            print("cached  %s (%d)" % (vol, len(data[vol])))
            continue
        print("fetch   %s" % vol)
        pages = allpages(vol)
        pat = re.compile(r"^%s (\d+(?:\.\d+)?)$" % re.escape(vol))
        issues = [p for p in pages if pat.match(p)]
        print("  %d pages, %d issue pages" % (len(pages), len(issues)))
        data[vol] = contents(issues)
        cache.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print("done: %s" % {k: len(v) for k, v in data.items()})

    vf = HERE / "volumes.json"
    if not vf.exists():
        print("fetch   the volume pages")
        vf.write_text(json.dumps(volume_pages(), ensure_ascii=False),
                      encoding="utf-8")
    print("volumes: %d" % len(json.loads(vf.read_text(encoding="utf-8"))))


if __name__ == "__main__":
    main()
