#!/usr/bin/env python3
"""Generate properties/hellsing-ultimate.json.

    PYTHONIOENCODING=utf-8 python tools/make_hellsing-ultimate.py

Ten OVAs in release order, weighted from the per-episode Runtime column of
Wikipedia's "List of Hellsing episodes", plus the three Hellsing: The Dawn
shorts as an optional section. Everything this file prints is read out of
tools/data/hellsing-episodes.json, harvested by scratch/agent-hellsing/
harvest.py; nothing here is typed from memory.

THE SCOPE DECISION, and how to reverse it
-----------------------------------------
There are two Hellsing anime. This list is the OVA — ten volumes released
between 2006 and 2012, the ones Toonami ran in 2014 — and it deliberately does
NOT carry the thirteen-episode 2001 television series Gonzo made. Two
independent reasons, both from the source:

  1. They are two adaptations of one manga rather than two halves of a story.
     The source calls the OVA "more faithful to the original manga than the TV
     series" and says the two diverge; finishing this list therefore leaves
     nothing dangling.
  2. No per-episode runtime for the 2001 series is published anywhere. The
     hunt is recorded in the data file under `hunt` and summarised in the
     notes: no episode article, no episode Wikidata item, no season article,
     no runtime column in its table, no runtime field in its infobox, and no
     duration on the series item Q951078. Weights are all or nothing
     (CLU-131), so thirteen unweighted rows would silently add thirteen
     phantom hours to an eight-hour list.

To reverse it: set INCLUDE_TV = True. The TV rows are already harvested, their
ids are namespaced `hsu-tv-N` against the OVAs' `hsu-ova-N` so nothing
collides, and tv_section() refuses to build until TV_EPISODE_W is given a
figure together with the source that publishes it. That refusal is the point —
flipping the flag must not be able to invent hours.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop  # noqa: E402

SLUG = "hellsing-ultimate"
DATA = pathlib.Path(__file__).resolve().parent / "data" / "hellsing-episodes.json"
LIST_URL = "https://en.wikipedia.org/wiki/List_of_Hellsing_episodes"

# ---- the scope switch. See the docstring; do not flip it silently.
INCLUDE_TV = False
# A sourced per-episode runtime in minutes for the 2001 series, and the source
# that publishes it. Both stay None because nothing publishes one: see `hunt`
# in the data file. An average is not a figure and must never go here.
TV_EPISODE_W = None
TV_EPISODE_W_SOURCE = None

# The Dawn's three shorts have no per-episode figure anywhere. The source's
# infobox states one range for all three — "6-9 minutes" — so each row weighs
# the BOTTOM of that range, which understates the section by at most nine
# minutes and invents nothing. Read out of the data file rather than typed.
DAWN_FLOOR_FROM_RANGE = True


def load():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    assert d["source"]["episodes"] == LIST_URL, d["source"]
    return d


def studio_spans(field):
    """[(studio, first, last)] out of "Satelight (1-4)|Madhouse (5-7)|...".

    The section split is the source's own production split, not a shape chosen
    here, so it is parsed rather than typed — and asserted to tile 1..10 with
    no gap and no overlap.
    """
    out = []
    for part in field.split("|"):
        m = re.fullmatch(r"\s*(.+?)\s*\((\d+)\s*[‐-―-]\s*(\d+)\)\s*", part)
        assert m, "unparsed studio span %r" % part
        out.append((m.group(1), int(m.group(2)), int(m.group(3))))
    flat = [n for _s, a, b in out for n in range(a, b + 1)]
    assert flat == list(range(1, len(flat) + 1)), flat
    return out


def month_year(day_month_year):
    """"February 10, 2006" -> "February 2006"."""
    m = re.fullmatch(r"([A-Z][a-z]+) \d{1,2}, ((?:19|20)\d{2})", day_month_year)
    assert m, day_month_year
    return "%s %s" % (m.group(1), m.group(2))


def roman(title):
    """"Hellsing VIII" -> "VIII"."""
    m = re.fullmatch(r"Hellsing ([IVX]+)", title)
    assert m, title
    return m.group(1)


def ova_sections(d):
    rows = d["ova"]
    mins = [r["runtime_min"] for r in rows]
    assert len(set(mins)) == len(mins), \
        "two OVAs now share a runtime — the notes say no two are alike"
    out = []
    for studio, lo, hi in studio_spans(d["infobox"]["ova"]["studio"]):
        part = rows[lo - 1:hi]
        assert [r["n"] for r in part] == list(range(lo, hi + 1)), part
        minutes = sum(r["runtime_min"] for r in part)
        sec = {
            "id": prop.slug(studio),
            "title": "Hellsing %s–%s" % (roman(part[0]["t"]),
                                         roman(part[-1]["t"])),
            "sub": " · ".join([
                "%s to %s" % (month_year(part[0]["jp"]),
                              month_year(part[-1]["jp"])),
                studio,
                "%d episodes" % len(part),
                "%d minutes" % minutes]),
            "items": [{
                "id": "hsu-ova-%d" % r["n"],
                "t": r["t"],
                "n": str(r["n"]),
                "w": round(r["runtime_min"] / 60.0, 2),
                "note": prop.join_bits("%d min" % r["runtime_min"],
                                       "Japan, %s" % r["jp"]),
            } for r in part],
        }
        if lo == 1:
            sec["open"] = True
            sec["links"] = [{"label": "The episode list", "url": LIST_URL}]
            sec["intro"] = (
                "Ten OVAs, released one volume at a time between %s and %s by "
                "three studios in turn. This is the adaptation that follows "
                "the manga — the source calls it “more faithful to the "
                "original manga than the TV series” — and no two volumes "
                "run the same length, so each mark on the strip is drawn to "
                "the runtime the source publishes for that volume. %s "
                "animated these first four."
                % (rows[0]["jp"][-4:], rows[-1]["jp"][-4:], studio))
        out.append(sec)
    return out


def dawn_section(d):
    rows, ova = d["dawn"], d["ova"]
    lo, hi = dawn_range(d)
    assert DAWN_FLOOR_FROM_RANGE, "the floor is the only honest weight here"
    with_ova = {}
    for r in ova:
        if r["dawn_with"]:
            with_ova[r["dawn_with"]] = r["t"]
    assert sorted(with_ova) == [r["n"] for r in rows], with_ova
    return {
        "id": "dawn",
        "title": "Hellsing: The Dawn",
        "sub": " · ".join([
            "%s to %s" % (month_year(rows[0]["jp"]), month_year(rows[-1]["jp"])),
            "three shorts, one inside each of the last three limited editions",
            "optional"]),
        "intro": "A separate production from a separate prequel, bundled with "
                 "the last three volumes rather than released on its own. "
                 "Optional here, and the only rows on the list whose length "
                 "the source does not publish one by one — see the note "
                 "below the list.",
        "links": [{"label": "The Dawn on the episode list",
                   "url": dawn_url(d)}],
        "items": [{
            "id": "hsu-dawn-%d" % r["n"],
            "t": r["t"],
            "n": str(r["n"]),
            "w": round(lo / 60.0, 2),
            "opt": True,
            "note": "Shipped inside the limited edition of %s"
                    % with_ova[r["n"]],
        } for r in rows],
    }


def dawn_url(d):
    """The Dawn's section link, built from the anchor the SOURCE's own infobox
    points at rather than from an anchor typed here. (The OVA box's equivalent
    field is stale — it says "(2006-14)" where the heading says "(2006-12)" —
    so the OVA sections link to the article plainly.)"""
    page, _, anchor = d["infobox"]["dawn"]["episode_list"].partition("#")
    assert page == "List of Hellsing episodes" and anchor, \
        d["infobox"]["dawn"]["episode_list"]
    return LIST_URL + "#" + anchor.replace(" ", "_")


def dawn_range(d):
    """(6, 9) out of The Dawn infobox's "6-9 minutes", refusing anything else."""
    raw = d["infobox"]["dawn"]["runtime"]
    m = re.fullmatch(r"\s*(\d{1,3})\s*[‐-―-]\s*(\d{1,3})\s*minutes\s*",
                     raw)
    assert m, "The Dawn's runtime field is no longer a plain range: %r" % raw
    lo, hi = int(m.group(1)), int(m.group(2))
    assert 0 < lo <= hi, raw
    return lo, hi


def tv_section(d):
    """The 2001 series, if INCLUDE_TV is ever turned on. See the docstring."""
    rows = d["tv"]
    assert not any(r["runtime_min"] for r in rows), \
        "the TV table now publishes runtimes — weigh from them, not from " \
        "TV_EPISODE_W"
    if not TV_EPISODE_W:
        raise SystemExit(
            "INCLUDE_TV is on, but no per-episode runtime for the 2001 series "
            "exists in any source this repo has checked (see `hunt` in %s). "
            "Thirteen rows with no `w` would silently count as thirteen hours "
            "on a weighted list (CLU-131). Set TV_EPISODE_W and "
            "TV_EPISODE_W_SOURCE together, or leave INCLUDE_TV off." % DATA.name)
    assert TV_EPISODE_W_SOURCE, "a weight with no source is a guess"
    return {
        "id": "tv2001",
        "title": "Hellsing (2001)",
        "sub": " · ".join([
            "%s to %s" % (month_year(rows[0]["jp"]), month_year(rows[-1]["jp"])),
            d["infobox"]["tv"]["studio"].replace("|", " and "),
            "%d episodes" % len(rows)]),
        "items": [{
            "id": "hsu-tv-%d" % r["n"],
            "t": r["t"],
            "n": str(r["n"]),
            "w": round(TV_EPISODE_W / 60.0, 2),
            "note": prop.join_bits("%d min" % TV_EPISODE_W,
                                   "Japan, %s" % r["jp"]),
        } for r in rows],
    }


def hunt_receipts(d):
    """The sentence the notes make about the empty runtime hunt, checked
    against what the harvest actually recorded rather than asserted."""
    h = d["hunt"]
    found = h["episode_articles_found"]
    labels = " ".join(v[1] for v in found.values()).lower()
    assert h["episode_articles_asked"] == 45, h["episode_articles_asked"]
    assert len(found) == 8, found
    for word in ("band", "racehorse", "album", "disambiguation"):
        assert word in labels, (word, labels)
    assert all(not v for v in h["wikidata_durations"].values()), \
        "an episode-title item grew a duration — re-check the hunt"
    series = h["series_items"]
    assert series["Q951078"]["P2047"] == [], "the 2001 series item grew a runtime"
    assert series["Q951078"]["P1113"] == ["+13"], series["Q951078"]
    assert series["Q2750339"]["P2047"] == [[50.0, "normal", None]], \
        series["Q2750339"]
    assert series["Q2750339"]["P1113"] == ["+10"], series["Q2750339"]
    assert not [p for p in h["season_articles"]
                if re.search(r"hellsing.*season", p, re.I)], h["season_articles"]
    return len(found)


def quote(d, key, fragment):
    """A fragment of the source's own sentence, asserted to be in it."""
    whole = d["quotes"][key]
    assert fragment in whole, (fragment, whole)
    return fragment


def main():
    d = load()
    hunt_receipts(d)

    sections = ova_sections(d)
    if INCLUDE_TV:
        sections.append(tv_section(d))
    sections.append(dawn_section(d))

    ova_minutes = sum(r["runtime_min"] for r in d["ova"])
    dawn_lo, dawn_hi = dawn_range(d)
    dawn_minutes = dawn_lo * len(d["dawn"])
    lo, hi = d["ova_runtime_range"]
    hours = sum(x["w"] for s in sections for x in s["items"])
    required = sum(x["w"] for s in sections for x in s["items"]
                   if not x.get("opt"))

    notes = [
        ["Ten OVAs, and no two of them the same length.",
         "The shortest runs %d minutes and the longest %d, and the ten together "
         "run %d — so the marks on the strip are drawn to the length of "
         "each one rather than to an average. Every figure is the Runtime "
         "column of the source's own OVA table, which publishes one per "
         "episode. The series infobox states only the spread, “%s”, "
         "and a spread is never used as a weight here."
         % (lo, hi, ova_minutes, d["infobox"]["ova"]["runtime"])],
        ["The 2001 television series is not on this list, and that is a "
         "decision.",
         "Hellsing Ultimate and the thirteen-episode Hellsing that Gonzo made "
         "in 2001 are two adaptations of one manga, not two halves of one "
         "story. The source says the OVA episodes “%s”, and "
         "describes the OVA as “%s”. Finishing this list therefore "
         "leaves nothing half-watched. The second reason is arithmetic: not "
         "one per-episode runtime for the 2001 series is published anywhere "
         "(the next note is the hunt), and on a weighted list a row with no "
         "weight silently counts as a full hour — thirteen of them would "
         "add thirteen invented hours to an eight-hour list. The decision is "
         "one line in tools/make_hellsing-ultimate.py if it is ever reversed: "
         "the thirteen rows are already harvested, their ids are namespaced "
         "apart from these, and the generator refuses to ship them until "
         "somebody supplies a runtime with a source attached."
         % (quote(d, "divergence",
                  "more closely follow the source manga and differ from the "
                  "first series"),
            quote(d, "faithful",
                  "more faithful to the original manga than the TV series"))],
        ["What the hunt for the 2001 series' runtimes found, which was nothing.",
         "No episode of it has an article of its own: all thirteen titles were "
         "asked for in three forms each, %d names in all, and the eight that "
         "resolve to anything resolve to other subjects entirely — a punk "
         "band, a racehorse, an album, an article about duelling, one about "
         "training facilities and three disambiguation pages — and not "
         "one of them carries a duration. No episode has a Wikidata item, so "
         "there is no per-episode duration statement to read. The series item "
         "Q951078 states thirteen episodes and no duration at all. There is no "
         "season article to hold a runtime column, the episode table has no "
         "runtime field for those thirteen rows, and the series infobox has no "
         "runtime field either. The only duration anywhere in the franchise's "
         "Wikidata is 50 minutes on the OVA item Q2750339 — one "
         "series-level figure, which the per-episode table already beats ten "
         "times over." % d["hunt"]["episode_articles_asked"]],
        ["Hellsing: The Dawn is optional, and its three rows weigh a floor "
         "rather than a figure.",
         "Three shorts, one inside the limited edition of each of the last "
         "three volumes — the source: “%s” They are a separate "
         "production with their own studio and their own infobox, and of the "
         "prequel manga behind them the source says “%s”, so they sit here "
         "marked optional. Their length is the one number on this list the "
         "source will not give per episode: it publishes “%s” for all three "
         "together and nothing for any one of them, and there is no Wikidata "
         "item for the shorts at all. Each therefore weighs %d minutes, the "
         "bottom of that range, which understates the section by at most %d "
         "minutes rather than inventing three numbers. %d of the list's %d "
         "weighted minutes are these three rows."
         % (quote(d, "limited", "Each limited edition of the last three "
                                "episodes' home video release included an "
                                "episode of Hellsing: The Dawn."),
            quote(d, "dawn_manga", "the series remains incomplete"),
            d["infobox"]["dawn"]["runtime"], dawn_lo,
            (dawn_hi - dawn_lo) * len(d["dawn"]), dawn_minutes,
            ova_minutes + dawn_minutes)],
        ["Where it ran, if you saw it on television.",
         "The source: “%s” That block is where this list came from. "
         "The 2001 series had its own American airing years earlier, dubbed on "
         "Encore Action from October to December 2003, which is the other "
         "reason the two get confused."
         % quote(d, "toonami", "In 2014, Hellsing Ultimate aired on US "
                               "television via Adult Swim's Toonami "
                               "programming block, starting on September 13.")],
        ["What else is deliberately absent.",
         "The manga, ten volumes, and the six-chapter prequel manga — "
         "both print, and this is a watch list. The Crossfire drama CD that "
         "shipped with the sixth OVA, which is audio: the source's own line is "
         "“%s” And the 2001 television series, for the two reasons "
         "above."
         % quote(d, "crossfire", "OVA 6 features a drama CD of Crossfire.")],
        "Titles, numbering, release dates and every per-episode runtime "
        "machine-read from Wikipedia's List of Hellsing episodes; the episode "
        "counts, studios, release spans and both runtime ranges from the "
        "infoboxes on the Hellsing article; the runtime hunt also asked "
        "Wikidata, and every question it asked is recorded in "
        "tools/data/hellsing-episodes.json.",
    ]

    p = {
        "slug": SLUG,
        "title": "Hellsing Ultimate",
        "subtitle": "the ten OVAs, and not the 2001 series",
        "kind": "anime",
        "popularity": 62,
        "year": "2006–2012",
        "blurb": "Ten OVAs released one at a time over seven years, in release "
                 "order — %d hours of them, and no two the same length. "
                 "The 2001 television series is a different adaptation of the "
                 "same manga and is not here." % round(required),
        "unit": {"one": "OVA", "many": "OVAs"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#8E1B1B",
        "accentDark": "#FF7B7B",
        "tiers": False,
        "notes": notes,
        "sections": sections,
    }

    # Cross-list tick sync mints a key from title + year, and a row's year can
    # come from a lone year inside its note (src/build.py `_year_of`). These
    # rows carry release dates, so the list must stay off that path: "anime" is
    # not one of build.py's syncable kinds and no row declares a medium of its
    # own, which is the only other way in.
    assert "film" not in p["kind"] and "game" not in p["kind"], p["kind"]
    for s in p["sections"]:
        for x in s["items"]:
            assert not {"m", "q", "y"} & set(x), x

    ids = [x["id"] for s in p["sections"] for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(d["ova"]) + len(d["dawn"]) \
        + (len(d["tv"]) if INCLUDE_TV else 0), ids
    assert all(x.get("w") for s in p["sections"] for x in s["items"]), \
        "an unweighted row on a weighted list would count as an hour"

    out = prop.write(p)
    print("wrote %s — %d rows, %.2f hours (%.2f required)"
          % (out.name, len(ids), hours, required))
    for s in p["sections"]:
        w = sum(x["w"] for x in s["items"])
        print("   %-22s %2d rows  %5.2fh  %s"
              % (s["title"], len(s["items"]), w, s["sub"]))


if __name__ == "__main__":
    main()
