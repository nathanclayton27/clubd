#!/usr/bin/env python3
"""Build scratch/bleach/bleach.json from the cached Wikipedia articles and the
cached animefillerlist.com classification tables.

    python scratch/bleach/parse.py            # uses the cache, no network
    python scratch/bleach/parse.py --fetch    # refresh the cache first

The enumerated episode tables are the source of truth for the count, never an
infobox summary: every season asserts its table and its `num_episodes` agree,
and the run asserts contiguity from 1, so a future edit to Wikipedia fails
loudly instead of quietly shipping a short list.

WHY THIS DOES NOT USE gwlib.wiki.episodes()
-------------------------------------------
That reader drops rows on three shapes (CLU-167) and *Bleach*'s articles have
the shape that matters most here: the Thousand-Year Blood War table keeps its
not-yet-aired episodes inside an HTML comment. A regex reader that does not
strip comments first invents four episodes that do not exist, complete with
blank titles. It also closes a block at the first line-initial `}}`, and these
episodes' `ShortSummary` fields carry nested templates. So the reader below
strips comments, then finds each template's real end by counting braces.
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
WIKI = HERE / "wiki"
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

SEASONS = ["Bleach season %d" % n for n in range(1, 17)]
TYBW = "Bleach: Thousand-Year Blood War"
LIST = "List of Bleach episodes"

# the original run, asserted against the tables
ORIGINAL = 366
# the newest AIRED episode overall. The sequel finished on 27 October 2026 at
# 50 episodes (its Wikipedia lead: "totaling 50 episodes"), so this is final.
LAST = 416          # Thousand-Year Blood War #50, aired 27 October 2026

AFL = {"bleach": "bleach", "tybw": "bleach-thousand-year-blood-war"}


def cache_name(page):
    return re.sub(r"[^A-Za-z0-9]+", "-", page) + ".wiki"


def fetch():
    from gwlib import wiki
    for page in [LIST, TYBW] + SEASONS:
        wiki.wikitext(page, cache_dir=str(WIKI), sleep=0.6)
    import urllib.request
    ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
    for slug in AFL.values():
        out = HERE / ("afl-%s.html" % slug)
        if out.exists():
            continue
        req = urllib.request.Request(
            "https://www.animefillerlist.com/shows/" + slug,
            headers={"User-Agent": ua, "Accept": "text/html"})
        with urllib.request.urlopen(req, timeout=60) as r:
            out.write_bytes(r.read())


# --- the brace-counting episode reader ------------------------------------

COMMENT = re.compile(r"<!--.*?-->", re.S)
EPSTART = re.compile(r"\{\{(?:#invoke:)?Episode list\s*[|/]", re.I)


def template_bodies(text, start_re):
    """[(offset, body)] for every template whose opening `start_re` matches,
    each body running to its OWN closing braces rather than to the first
    line-initial `}}`."""
    out = []
    for m in start_re.finditer(text):
        depth, i, n = 0, m.start(), len(text)
        while i < n:
            if text.startswith("{{", i):
                depth += 1
                i += 2
            elif text.startswith("}}", i):
                depth -= 1
                i += 2
                if depth == 0:
                    break
            else:
                i += 1
        assert depth == 0, "unclosed Episode list at offset %d" % m.start()
        out.append((m.start(), text[m.start():i]))
    return out


def field(body, name):
    """One template field, value ending at the next top-level `|` or the close.

    `[ \\t]` and not `\\s` after the `=`: with `\\s*` an empty field eats its own
    newline and captures the next line."""
    m = re.search(r"\n[ \t]*\|[ \t]*%s[ \t]*=[ \t]*(.*?)(?=\n[ \t]*\||\Z)"
                  % name, body, re.S | re.I)
    return m.group(1).strip() if m else ""


def episode_rows(text):
    """[(overall, in_series, title, body)], comments stripped first."""
    text = COMMENT.sub("", text)
    rows = []
    for off, body in template_bodies(text, EPSTART):
        n1, n2 = field(body, "EpisodeNumber"), field(body, "EpisodeNumber2")
        assert re.fullmatch(r"\d+", n1), \
            "EpisodeNumber %r is not a plain number at offset %d" % (n1, off)
        rows.append((int(n1), int(n2) if re.fullmatch(r"\d+", n2) else None,
                     field(body, "Title"), body))
    return rows


INFOBOX_N = re.compile(r"\|\s*num_episodes\s*=\s*(\d+)")


def season_rows(page):
    text = (WIKI / cache_name(page)).read_text(encoding="utf-8")
    box = INFOBOX_N.search(text)
    assert box, "no num_episodes in %s" % page
    body = text[text.index("== Episodes =="):]
    rows = episode_rows(body)
    assert rows, "no episodes parsed from %s" % page
    assert len(rows) == int(box.group(1)), \
        "%s: table has %d episodes, infobox says %d (the table wins, but a " \
        "mismatch means the article changed)" % (page, len(rows),
                                                 int(box.group(1)))
    return rows


# `=== Part 4: ''The Calamity'' (2026) ===`: since Nov 2026 the headings carry
# a year, which is not part of the title (the section id is built from it)
PART_HEAD = re.compile(r"^=={1,3}[ ']*Part (\d+):[ ']*(.*?)[' ]*"
                       r"(?:\(\d{4}[^)]*\)[ ]*)?=={1,3}\s*$", re.M)
# `=== Season 4: ''The Bount'' (2006) ===` on the list article. These are the
# arc names the English release uses, and they are what the seasons ARE: each
# season article opens by naming its arc.
# Since Nov 2026 the list article nests these one level deeper (====) under a
# per-series heading, so either depth is accepted.
SEASON_HEAD = re.compile(r"^={3,4}[ ]*Season (\d+):[ ']*(.*?)[' ]*\((\d{4}[^)]*)\)"
                         r"[ ]*={3,4}\s*$", re.M)


def season_titles():
    text = (WIKI / cache_name(LIST)).read_text(encoding="utf-8")
    out = {int(n): (t.strip(), y.strip())
           for n, t, y in SEASON_HEAD.findall(text)}
    assert sorted(out) == list(range(1, 17)), \
        "the list article's season headings changed: %s" % sorted(out)
    return out


def tybw_parts():
    """[(part number, part title, [(overall, in_series)])] for the sequel.

    The page's own `=== Part n ===` headings carry the split; the recap
    special after them is a separate section and is not an episode."""
    text = (WIKI / cache_name(TYBW)).read_text(encoding="utf-8")
    text = COMMENT.sub("", text)
    body = text[text.index("== Episodes =="):text.index("== Recap special ==")]
    heads = [(m.start(), int(m.group(1)),
              re.sub(r"''", "", m.group(2)).strip())
             for m in PART_HEAD.finditer(body)]
    assert heads, "no Part headings on %s" % TYBW
    # each template keeps its own offset, so a row lands in the Part whose
    # heading it sits under rather than being counted off a running total
    stamped = []
    for off, tbody in template_bodies(body, EPSTART):
        n1 = field(tbody, "EpisodeNumber")
        n2 = field(tbody, "EpisodeNumber2")
        assert re.fullmatch(r"\d+", n1) and re.fullmatch(r"\d+", n2), \
            "Part episode with a non-numeric number: %r / %r" % (n1, n2)
        stamped.append((off, int(n1), int(n2)))
    parts = []
    for i, (pos, num, title) in enumerate(heads):
        end = heads[i + 1][0] if i + 1 < len(heads) else len(body)
        eps = [(a, b) for off, a, b in stamped if pos < off < end]
        assert eps, "Part %d has no episodes" % num
        parts.append({"part": num, "title": title, "episodes": eps})
    assert len(stamped) == sum(len(p["episodes"]) for p in parts), \
        "an episode sits outside every Part heading"
    return parts


# --- animefillerlist: the published filler classification ------------------

AFL_ROW = re.compile(r'<tr class="[^"]*" id="eps-(\d+)">.*?'
                     r'<td class="Type"><span>([^<]+)</span>', re.S)

CLASS = {"Manga Canon": "canon", "Filler": "filler",
         "Mixed Canon/Filler": "mixed", "Anime Canon": "anime-canon"}


def filler_map(key):
    html = (HERE / ("afl-%s.html" % AFL[key])).read_text(
        encoding="utf-8", errors="replace")
    out = {}
    for num, kind in AFL_ROW.findall(html):
        assert kind in CLASS, "unknown animefillerlist type %r" % kind
        out[int(num)] = CLASS[kind]
    nums = sorted(out)
    assert nums == list(range(1, len(nums) + 1)), \
        "%s: animefillerlist rows are not 1..n" % key
    return out


def main():
    if "--fetch" in sys.argv:
        fetch()

    titles = season_titles()
    seasons, seen = [], 0
    for n, page in enumerate(SEASONS, 1):
        rows = season_rows(page)
        nums = [a for a, _b, _t, _x in rows]
        assert nums == list(range(nums[0], nums[-1] + 1)), \
            "%s: episode numbers are not contiguous" % page
        assert nums[0] == seen + 1, \
            "%s: starts at %d, previous season ended at %d" % (
                page, nums[0], seen)
        seen = nums[-1]
        seasons.append({"season": n, "page": page,
                        "title": titles[n][0], "years": titles[n][1],
                        "first": nums[0], "last": nums[-1],
                        "episodes": len(nums)})
    assert seen == ORIGINAL, \
        "the season tables come to %d episodes, expected %d" % (seen, ORIGINAL)

    parts = tybw_parts()
    flat = [a for p in parts for a, _b in p["episodes"]]
    assert flat == list(range(ORIGINAL + 1, ORIGINAL + 1 + len(flat))), \
        "Thousand-Year Blood War does not continue the overall numbering"
    for p in parts:
        p["first"], p["last"] = p["episodes"][0][0], p["episodes"][-1][0]
        p["series_first"] = p["episodes"][0][1]
        p["series_last"] = p["episodes"][-1][1]
        del p["episodes"]

    afl = {}
    for n, cls in filler_map("bleach").items():
        afl[n] = cls
    tybw_afl = filler_map("tybw")
    for n, cls in tybw_afl.items():
        afl[ORIGINAL + n] = cls
    assert len(afl) >= ORIGINAL, "animefillerlist is short of the original run"

    data = {"original": ORIGINAL, "last": LAST,
            "seasons": seasons, "parts": parts,
            "filler": {str(k): v for k, v in sorted(afl.items())}}
    out = HERE / "bleach.json"
    with out.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    print("wrote %s" % out)
    print("  %d seasons, %d episodes 1-%d" % (len(seasons), ORIGINAL, ORIGINAL))
    for p in parts:
        print("  TYBW Part %d %-18s %d-%d" % (p["part"], p["title"],
                                              p["first"], p["last"]))
    print("  animefillerlist covers %d episodes (1-%d, then %d-%d)"
          % (len(afl), ORIGINAL, ORIGINAL + 1, ORIGINAL + len(tybw_afl)))


if __name__ == "__main__":
    main()
