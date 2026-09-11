#!/usr/bin/env python3
"""Fetch every Captain America issue page from the Marvel Database wiki.

    PYTHONIOENCODING=utf-8 python scratch/captain-america/fetch.py

Two API calls per series, then the issue pages themselves in batches of 40:

  list=allpages&apprefix="<series> "   enumerates the issues that exist
  prop=revisions&rvprop=content        gives each issue's infobox

The infobox carries the fields this list is built out of — Month, Year,
StoryTitle, StoryArc and every Writer credit — so no issue number, no date
and no creative-run boundary in properties/captain-america.json is typed by
hand. Raw responses cache here as JSON; delete a file to refetch it.

marvel.fandom.com is the same class of source as bleach.fandom.com, which
scratch/bleach/ already reads for the Bleach chapter list.

The cache itself is NOT tracked, unlike the .wiki files some other properties
keep here: it is 3.4 MB of API envelopes, and everything the generator reads
out of it already lives in tools/data/captain-america.json, which is. A clone
rebuilds the list from that file alone; this script exists to rebuild the file.
"""
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
API = "https://marvel.fandom.com/api.php"
UA = "GroupWatch/1.0 (reading-list builder)"

# Every series the list touches, by its Marvel Database volume name.
SERIES = [
    "Captain America Comics Vol 1",
    "Tales of Suspense Vol 1",
    "Avengers Vol 1",
    "Captain America Vol 1",
    "Captain America Vol 2",
    "Captain America Vol 3",
    "Captain America Vol 4",
    "Captain America Vol 5",
    "Captain America Vol 6",
    "Captain America and Bucky Vol 1",
    "Captain America: Reborn Vol 1",
    "Winter Soldier Vol 1",
]

# Issues wanted from each series. Avengers and Tales of Suspense are huge
# books that the list only borrows from, so they are clipped here rather than
# fetched whole.
WANT = {
    "Captain America Comics Vol 1": lambda n: n == 1,
    "Tales of Suspense Vol 1": lambda n: 59 <= n <= 99,
    "Avengers Vol 1": lambda n: n == 4,
}


def get(**kw):
    kw.update(format="json", formatversion="2", action="query")
    url = API + "?" + urllib.parse.urlencode(kw)
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 5:
                raise
            time.sleep(10 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError):
            if attempt == 5:
                raise
            time.sleep(5)


def cached(name, build):
    f = HERE / (re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-") + ".json")
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    d = build()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    time.sleep(0.4)
    return d


def issue_numbers(series):
    """Every mainline issue page of a series, as integers."""
    def build():
        out, cont = [], {}
        while True:
            d = get(list="allpages", apprefix=series + " ", aplimit="500",
                    apnamespace="0", **cont)
            out += [p["title"] for p in d["query"]["allpages"]]
            if "continue" not in d:
                break
            cont = d["continue"]
            time.sleep(0.4)
        return out
    titles = cached("pages-" + series, build)
    pat = re.compile(r"^" + re.escape(series) + r" (\d+)$")
    nums = sorted(int(m.group(1)) for m in map(pat.match, titles) if m)
    keep = WANT.get(series)
    return [n for n in nums if not keep or keep(n)]


def issue_pages(series, nums):
    """Wikitext for a list of issues, batched 40 at a time."""
    out = {}
    for i in range(0, len(nums), 40):
        chunk = nums[i:i + 40]
        name = "text-%s-%d" % (series, chunk[0])

        def build(chunk=chunk):
            d = get(prop="revisions", rvslots="main", rvprop="content",
                    titles="|".join("%s %d" % (series, n) for n in chunk))
            got = {}
            for p in d["query"]["pages"]:
                if p.get("missing"):
                    continue
                got[p["title"]] = p["revisions"][0]["slots"]["main"]["content"]
            return got
        got = cached(name, build)
        assert got, "no wikitext came back for %s %s" % (series, chunk[:3])
        out.update(got)
    return out


def main():
    total = 0
    for series in SERIES:
        nums = issue_numbers(series)
        assert nums, "no issues enumerated for %s" % series
        pages = issue_pages(series, nums)
        missing = [n for n in nums if "%s %d" % (series, n) not in pages]
        assert not missing, "no page text for %s %s" % (series, missing[:5])
        total += len(pages)
        print("%-34s %4d issues  #%s-#%s"
              % (series, len(nums), nums[0], nums[-1]))
    print("%d issue pages cached in %s" % (total, HERE))


if __name__ == "__main__":
    sys.exit(main())
