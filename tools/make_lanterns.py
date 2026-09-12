#!/usr/bin/env python3
"""Generate properties/lanterns.json — Lanterns (2026).

    PYTHONIOENCODING=utf-8 python tools/make_lanterns.py
    PYTHONIOENCODING=utf-8 python tools/make_lanterns.py --refresh

The DC Green Lantern series: Hal Jordan and John Stewart investigating a murder
in the American heartland. Eight episodes, weekly on Sundays from 16 August to
4 October 2026, airing on HBO and streaming on HBO Max.

It is airing right now, which makes it one of the properties whose schedule
matters week to week — one window per episode, so the pace line tells you
whether you are current rather than whether you are on track for a distant
date.

WHERE THE TITLES AND DATES COME FROM
------------------------------------
Nothing in this file is typed in from memory. The first version of this list
was written before the show aired and carried no source at all: episodes 3 to 8
were the string "Episode 3" … "Episode 8", every row's note read "airs 30
August" in the future tense whatever the date, and the list's own note claimed
"only the first two have been announced" long after that stopped being true.
Up Next was offering "Episode 5" to readers as though it were a title.

So the roster is now machine-read from the {{Episode list}} rows of the
Wikipedia article "Lanterns (TV series)" into tools/data/lanterns-episodes.json,
which is committed and is what a normal run reads. `--refresh` is the step that
produces it: it fetches the article, parses the episode table and the television
infobox, and writes the data file with the revision it read. Run it, look at the
diff, then run the generator. The extractor lives in this file rather than in
scratch/ on purpose — a source step nobody can find is a source step nobody can
check.

A TITLE IS NEVER INVENTED, AND A PLACEHOLDER IS NEVER DRESSED UP
----------------------------------------------------------------
An episode gets the title the source publishes. An episode the source has not
titled gets "Episode N", and the notes say plainly how many rows are in that
state so a reader knows the difference between a title and a number. As of the
read below, HBO has published five of the eight: episodes 1 to 4 have aired,
and episode 5 is named in the show's own official podcast, which the article
cites. Episodes 6 to 8 have air dates and no titles. They stay numbered.

THE AIRED/UPCOMING WORDING IS FROZEN, NOT READ FROM THE CLOCK
------------------------------------------------------------
Row notes read "aired 16 August" once an episode is out and "airs 13 September"
before, and the boundary is AS_OF rather than today, so two runs of this file on
different days cannot silently disagree. AS_OF is cross-checked against the
source: the number of episodes dated on or before it must equal the episode
count the article's own infobox states. If HBO's schedule slips, that check
fails rather than the list quietly claiming an episode aired.

THE SCHEDULE IS THE SOURCE'S DATES, NOT A WEEKLY ASSUMPTION
-----------------------------------------------------------
Each window opens on an episode's published air date and runs six days, and
`through` is that episode's number, so "behind" means behind the broadcast. The
old version computed the dates by adding weeks to a hardcoded premiere, which
would have gone on being confident through any schedule change. The dates are
now read per episode and the weekly spacing is asserted instead of assumed.

NOTHING IS WEIGHTED
-------------------
The article publishes "52–57 minutes" for the series and no per-episode
runtime; the episode table declares no runtime column. A range is a range, and
eight identical invented figures would be a guess dressed as a measurement, so
every episode counts one — the same call make_president-curtis.py and
make_xfiles.py make. That the runtime is still a range is asserted, so if the
source ever publishes per-episode figures this build fails and whoever is
standing there weights the list.

ROW IDS ARE PEOPLE'S TICKS. The eight `lanterns-N` ids this list shipped with
are passed to prop.write() as legacy_ids, so a rename or a reorder fails the
build instead of silently clearing everyone's progress.
"""
import argparse
import json
import pathlib
import re
import sys
import urllib.parse
from datetime import date, timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki  # noqa: E402

SLUG = "lanterns"
ARTICLE = "Lanterns (TV series)"
DATA = pathlib.Path(__file__).resolve().parent / "data" / ("%s-episodes.json" % SLUG)

# Freezes the aired/upcoming wording in the row notes, and cross-checked below
# against the episode count the article's own infobox states. Bump it when you
# re-run --refresh; reading the clock instead would make this file's output
# differ by the day it happened to run.
AS_OF = date(2026, 9, 11)

# The ids this list shipped with. Every one of them must survive every future
# edit of this file: a tick is stored against the id, so renaming one throws
# away a reader's progress with no way to get it back.
LEGACY_IDS = tuple("lanterns-%d" % n for n in range(1, 9))


def daymonth(d):
    """'16 August' — %-d is not portable, so the day is formatted by hand."""
    return "%d %s" % (d.day, d.strftime("%B"))


def and_list(bits):
    """'6, 7 and 8' — for a note that names a varying set of episodes."""
    bits = list(bits)
    if len(bits) <= 1:
        return "".join(bits)
    return "%s and %s" % (", ".join(bits[:-1]), bits[-1])


# --------------------------------------------------------------------------
# --refresh: read the article, write tools/data/lanterns-episodes.json
# --------------------------------------------------------------------------

def refresh():
    q = {"action": "query", "prop": "revisions", "titles": ARTICLE,
         "rvprop": "ids|timestamp", "rvlimit": "1", "format": "json",
         "formatversion": "2", "redirects": "1"}
    meta = wiki.get_json(wiki.API + "?" + urllib.parse.urlencode(q))
    page = meta["query"]["pages"][0]
    rev = page["revisions"][0]

    text = wiki.wikitext(ARTICLE)
    assert text, "no wikitext for %r" % ARTICLE

    ib = wiki.infobox(text, kind="television")
    assert ib, "no television infobox on %r" % ARTICLE
    runtime = ib("runtime").strip()
    first = re.search(r"\{\{\s*Start date\s*\|\s*(\d{4})\s*\|\s*(\d{1,2})"
                      r"\s*\|\s*(\d{1,2})", ib("first_aired"))
    assert first, "no parseable first_aired on the infobox: %r" % ib("first_aired")

    eps = []
    for e in wiki.episodes(text):
        raw = wiki.field(e.fields, "OriginalAirDate") or ""
        m = re.search(r"\{\{\s*Start date\s*\|\s*(\d{4})\s*\|\s*(\d{1,2})"
                      r"\s*\|\s*(\d{1,2})", raw)
        assert m, "episode %s has no parseable air date: %r" % (e[0], raw)
        assert e[0], "an episode row has no number"
        title = (e[2] or "").strip()
        eps.append({"e": int(e[0]),
                    "t": title or None,
                    "d": date(*(int(g) for g in m.groups())).isoformat()})
    assert eps, "no episode rows found — the episode table has moved"

    out = {
        "source": {
            "article": page["title"],
            "revid": rev["revid"],
            "revision_timestamp": rev["timestamp"],
            "url": "https://en.wikipedia.org/w/index.php?oldid=%d" % rev["revid"],
            "read": date.today().isoformat(),
            "what": "the {{Episode list}} rows of the article's Episodes "
                    "section, and its {{Infobox television}}",
        },
        "infobox": {
            "num_episodes": int(ib("num_episodes").strip()),
            "num_seasons": int(ib("num_seasons").strip()),
            "runtime": runtime,
            "network": wiki.clean(ib("network")),
            "first_aired": date(*(int(g) for g in first.groups())).isoformat(),
        },
        "episodes": eps,
    }
    DATA.parent.mkdir(parents=True, exist_ok=True)
    with DATA.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print("wrote %s from %s (rev %d)"
          % (DATA.name, out["source"]["article"], rev["revid"]))
    for r in eps:
        print("   %2d  %-14s %s" % (r["e"], r["t"] or "(untitled)", r["d"]))
    print("   infobox: %d episodes aired · %s · %s"
          % (out["infobox"]["num_episodes"], out["infobox"]["runtime"],
             out["infobox"]["network"]))


# --------------------------------------------------------------------------
# the build
# --------------------------------------------------------------------------

def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    eps, ib, src = data["episodes"], data["infobox"], data["source"]

    # ---- the source, before anything is built from it ---------------------
    assert src["article"] == ARTICLE, src["article"]
    n = len(eps)
    assert [r["e"] for r in eps] == list(range(1, n + 1)), \
        "episode numbering is not 1..N: %s" % [r["e"] for r in eps]
    dates = [date.fromisoformat(r["d"]) for r in eps]
    assert dates == sorted(dates), "air dates are out of order"
    # Weekly is asserted, not assumed. The previous version of this file built
    # every date by adding weeks to a hardcoded premiere, so a schedule change
    # could not have been noticed here.
    for a, b in zip(dates, dates[1:]):
        assert b - a == timedelta(days=7), \
            ("the run is no longer weekly: %s then %s — the windows are one "
             "per week and need re-deriving" % (a, b))
    assert dates[0] == date.fromisoformat(ib["first_aired"]), \
        "episode 1's air date disagrees with the infobox's first_aired"
    assert ib["num_seasons"] == 1, ib["num_seasons"]

    # ---- AS_OF is checked against the source, not trusted -----------------
    aired = [r for r, d in zip(eps, dates) if d <= AS_OF]
    assert len(aired) == ib["num_episodes"], \
        ("AS_OF %s makes %d episodes aired but the article's infobox counts "
         "%d — bump AS_OF, or the schedule moved"
         % (AS_OF, len(aired), ib["num_episodes"]))

    # ---- titles: published, or numbered, and never anything in between ----
    titled = [r for r in eps if r["t"]]
    untitled = [r for r in eps if not r["t"]]
    for r in titled:
        assert r["t"].strip() == r["t"] and len(r["t"]) > 1, r
    # Every episode that has aired must have a title. An aired episode with no
    # title means the parser lost one, which is the defect that put "Episode 5"
    # in front of readers as though it were a name.
    for r in aired:
        assert r["t"], \
            ("episode %d aired on %s and has no title in the source — that is "
             "a parser failure, not a fact" % (r["e"], r["d"]))

    # ---- NOTHING IS WEIGHTED, and here is the reason ---------------------
    assert re.fullmatch(r"\d+–\d+ minutes", ib["runtime"]), \
        ("the runtime is no longer a range (%r) — if the source now publishes "
         "one figure per episode, this list can carry hours" % ib["runtime"])

    items, windows = [], []
    for r, airs in zip(eps, dates):
        role = ("series premiere" if r["e"] == 1 else
                "season finale" if r["e"] == n else "")
        items.append({
            "id": "%s-%d" % (SLUG, r["e"]),
            "t": r["t"] or "Episode %d" % r["e"],
            "n": str(r["e"]),
            "note": prop.join_bits(
                "%s %s" % ("aired" if airs <= AS_OF else "airs",
                           daymonth(airs)),
                role),
        })
        # a week to watch each one, so "behind" means behind the broadcast
        windows.append({
            "start": r["d"],
            "end": (airs + timedelta(days=6)).isoformat(),
            "through": r["e"],
            "label": "Episode %d" % r["e"],
        })

    sections = [{
        "id": "s1",
        "title": "Season 1",
        "sub": "%d episodes · weekly from %s %d" % (n, daymonth(dates[0]),
                                                    dates[0].year),
        "items": items,
    }]

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate item ids"
    assert len(ids) == n, "built %d rows for %d episodes" % (len(ids), n)
    thr = [w["through"] for w in windows]
    assert thr == sorted(thr), "window targets are not monotonic"
    assert thr[-1] == n, "the last window does not close the season"
    for a, b in zip(windows, windows[1:]):
        assert a["end"] < b["start"], "windows overlap: %s / %s" % (a, b)
    for w, r in zip(windows, eps):
        assert w["start"] == r["d"], \
            "window %d does not open on the episode's published air date" % r["e"]

    if untitled:
        # Phrased from the untitled side only. Saying "HBO has named 1 to N"
        # would assume the published titles stay contiguous, and a later
        # episode being announced before an earlier one is an ordinary thing
        # for a show mid-run to do.
        which = and_list([str(r["e"]) for r in untitled])
        titles_note = (
            "%d of the %d titles are published. %s %s carry air dates and no "
            "titles yet, so this list numbers them rather than inventing names "
            "for them; they get their titles here when the source publishes "
            "them."
            % (len(titled), n,
               "Episodes" if len(untitled) > 1 else "Episode", which))
    else:
        titles_note = ("All %d titles are published, so no row on this list is "
                       "a placeholder." % n)

    p = {
        "slug": SLUG,
        "title": "Lanterns",
        "subtitle": "Hal Jordan and John Stewart",
        "kind": "tv",
        "popularity": 29,
        "year": "2026",
        "blurb": "%d episodes, weekly, still airing." % n,
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#2E7A45",
        "accentDark": "#5FC47E",
        "tiers": False,
        "schedule": {"kind": "windows", "windows": windows},
        "notes": [
            ["Airing now.", "One window per episode, so the pace line tells "
             "you whether you are caught up with the broadcast rather than on "
             "track for some distant finish. The last episode lands on %s %d."
             % (daymonth(dates[-1]), dates[-1].year)],
            ["Where it airs.", "Sundays on HBO, streaming the same day on HBO "
             "Max. Eight episodes weekly, %s to %s."
             % (daymonth(dates[0]), daymonth(dates[-1]))],
            ["Titles.", titles_note],
            ["Nothing is weighted.", "The source publishes %s for the series "
             "and no figure per episode, so every episode counts one rather "
             "than carrying a runtime this list would have had to guess at."
             % ib["runtime"]],
            ["The whole season is listed.", "All %d episodes are dated in the "
             "source, so the %d that have not aired yet are listed too. The "
             "schedule needs them, and an announced row is what an airing "
             "show looks like." % (n, n - len(aired))],
            "Episode titles and air dates machine-read from the episode table "
            "of the Wikipedia article \"%s\", revision %d, read %s; how many "
            "episodes have aired is cross-checked against that article's own "
            "infobox count before this builds, and an episode the article has "
            "not titled is numbered rather than named."
            % (src["article"], src["revid"], src["read"]),
        ],
        "sections": sections,
    }

    out = prop.write(p, legacy_ids=LEGACY_IDS)

    print("wrote %s — %d rows (%d aired by %s), unweighted"
          % (out.name, n, len(aired), AS_OF))
    print("   source: %s rev %d, read %s" % (src["article"], src["revid"],
                                             src["read"]))
    print("   %d titles published, %d still numbered: %s"
          % (len(titled), len(untitled),
             ", ".join(str(r["e"]) for r in untitled) or "none"))
    for it, w in zip(items, windows):
        print("   %2s  %-14s %-28s %s .. %s"
              % (it["n"], it["t"], it["note"], w["start"], w["end"]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refresh", action="store_true",
                    help="re-read the Wikipedia article and rewrite "
                         "tools/data/lanterns-episodes.json")
    args = ap.parse_args()
    if args.refresh:
        refresh()
    else:
        main()
