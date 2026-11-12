#!/usr/bin/env python3
"""Generate properties/star-trek.json — all twelve series and all thirteen films.

    PYTHONIOENCODING=utf-8 python tools/make_star_trek.py

ONE list, not a hub. The alternative was eleven per-series lists behind an
index page, and it was rejected: a club that sets out to watch Star Trek is
watching one thing, the strip is built to hold it (Criterion carries 1,418
rows), and splitting it would put the thirteen films either in a twelfth list
of their own or in none.

Sections are one per SEASON, running series by series in production order,
each titled with the series it belongs to. A section per series would have
meant 176-row and 172-row accordions with no season markers anywhere, and the
season is the unit people navigate a 60-year television franchise by; Doctor
Who ships the same shape, 355 rows across 46 season sections.

Series follow the date their first episode aired, which is why Lower Decks
and Prodigy sit ahead of Strange New Worlds. Each block of films follows the
series whose cast it continues, at the point those films begin: the six
original-cast films after The Animated Series, the four Next Generation films
immediately after that show's finale, and the three Kelvin films in the gap
after Enterprise when nothing was being made for television. The section
headings say plainly where a block overlaps a series that was already on the
air, rather than implying the run is a single line.

Nothing is weighted. See the "Nothing is weighted" note below and the
WEIGHTING assert in main(): the films have real runtimes, the episodes have
none that can be read, and a weighted list where some rows have no weight
counts those rows as one hour each.

Data: scratch/startrek/collect.py -> tools/data/star-trek-episodes.json, which
enumerates every {{Episode list}} row in Wikipedia's per-series episode tables
and is asserted here against each article's own {{Series overview}} counts.
The collector is no longer in scratch/. The 2026-11-11 refresh (Starfleet
Academy added, one Strange New Worlds season 4 title corrected) re-read those
tables and Wikidata's P2047 by hand and wrote the rows into the same shape.
"""
import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop
from gwlib.prop import join_bits

SLUG = "star-trek"
DATA = pathlib.Path(__file__).resolve().parent / "data" / "star-trek-episodes.json"

# The day this list's contents were read. "Has this aired yet" needs a fixed
# date rather than today's whenever a season is mid-run, or the generator would
# stop being reproducible the morning after it shipped.
AS_OF = "2026-11-11"

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

# key -> the name the sections carry. The full titles all begin "Star Trek:",
# which on a page called Star Trek would be 53 rows of the same two words.
NAMES = {
    "tos": "The Original Series", "tas": "The Animated Series",
    "tng": "The Next Generation", "ds9": "Deep Space Nine",
    "voy": "Voyager", "ent": "Enterprise", "dis": "Discovery",
    "pic": "Picard", "snw": "Strange New Worlds", "ld": "Lower Decks",
    "pro": "Prodigy", "sfa": "Starfleet Academy",
}

INTROS = {
    "tos": "Gene Roddenberry's original, on NBC for three seasons and 79 "
           "episodes. Everything else on this page descends from it.",
    "tas": "The animated continuation, made with most of the original cast "
           "voicing their own parts. Twenty-two half-hour episodes.",
    "tng": "A new ship, a new crew and a new cast, in first-run syndication. "
           "Seven seasons and 178 episodes.",
    "ds9": "A space station rather than a starship. Seven seasons and 176 "
           "episodes, overlapping the last season of The Next Generation and "
           "most of Voyager.",
    "voy": "A ship stranded on the far side of the galaxy and trying to get "
           "home. Seven seasons and 172 episodes.",
    "ent": "A prequel, set a century before the original series. Four "
           "seasons and 98 episodes, and then no new Star Trek on television "
           "for twelve years.",
    "dis": "The return to television after that gap, and the first Star Trek "
           "made for streaming. Five seasons and 65 episodes.",
    "pic": "Patrick Stewart back in the part, eighteen years after Nemesis. "
           "Three seasons of ten.",
    "ld": "An animated half-hour comedy about the crew members who are not "
          "on the bridge. Five seasons of ten.",
    "pro": "An animated series made for younger viewers. Two seasons of "
           "twenty episodes.",
    "snw": "The Enterprise before Kirk, with the crew from the 1964 pilot. "
           "Ten-episode seasons.",
    "sfa": "Cadets at Starfleet Academy, coming of age and training to be "
           "officers, with Holly Hunter as their chancellor. Ten-episode "
           "seasons.",
}

# tag in the source's film tables -> section id, heading, intro
FILM_BLOCKS = {
    "OriginalSeries": (
        "films-tos", "The Original Series films",
        "Six films with the original cast. The first four arrived in the gap "
        "after the animated series; The Final Frontier and The Undiscovered "
        "Country came out while The Next Generation was already on the air."),
    "NextGeneration": (
        "films-tng", "The Next Generation films",
        "Four films with the Next Generation cast. Generations arrived six "
        "months after the series finale; the other three came out while Deep "
        "Space Nine, Voyager and Enterprise were on television."),
    "Kelvin": (
        "films-kelvin", "The Kelvin films",
        "Three films with a recast original crew, released across the twelve "
        "years when no Star Trek was being made for television."),
}

# The spine, in production order: ("s", series key) or ("f", film-table tag).
SPINE = [("s", "tos"), ("s", "tas"), ("f", "OriginalSeries"),
         ("s", "tng"), ("f", "NextGeneration"),
         ("s", "ds9"), ("s", "voy"), ("s", "ent"), ("f", "Kelvin"),
         ("s", "dis"), ("s", "pic"), ("s", "ld"), ("s", "pro"), ("s", "snw"),
         ("s", "sfa")]

# Seasons the source dates but has not titled yet. Announced work with a date
# belongs on the list (Nathan, 2026-08-26), and this list is unweighted, so the
# row carries no w. Until the titles come it is one row, its premiere, pinned
# to the id that episode's own row will carry, so a tick on it stays put when
# the table fills in. Source: "Star Trek: Starfleet Academy" (rev 1383416694,
# 2 November 2026): "The ten-episode second season is expected to premiere in
# March 2027", and its season 2 table has one untitled row dated
# {{Start date|2027|3}}; CBS and Paramount have said it is the last.
# Strange New Worlds' fifth season is not here: its table says TBA.
PENDING = {
    ("sfa", 2): {"id": "st-sfa-s2e01", "due": "2027-03", "episodes": 10,
                 "final": True},
}


WORDS = ("zero one two three four five six seven eight nine ten eleven twelve "
         "thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty "
         "twenty-one twenty-two twenty-three twenty-four twenty-five "
         "twenty-six twenty-seven twenty-eight twenty-nine thirty").split()


def words(n):
    """A counted number, spelled — so a computed value can open a sentence."""
    assert 0 <= n < len(WORDS), n
    return WORDS[n]


def human(iso):
    """2026-08-27 -> 27 August 2026."""
    y, m, d = (int(x) for x in iso.split("-"))
    return "%d %s %d" % (d, MONTHS[m - 1], y)


def days_between(a, b):
    fmt = "%Y-%m-%d"
    return (datetime.datetime.strptime(b, fmt)
            - datetime.datetime.strptime(a, fmt)).days


def span(a, b):
    """1987, 1988 -> 1987–88; 1999, 2000 -> 1999–2000; 1974, 1974 -> 1974."""
    if a == b:
        return str(a)
    return "%d–%s" % (a, str(b)[2:] if str(a)[:2] == str(b)[:2] else b)


def dates_of(ep):
    return [a for a in ep["airs"] if a]


def season_rows(key, sea):
    """(items, episode count) for one season, one row per source table row."""
    items, eps = [], 0
    # A season that arrived all at once — Prodigy's second, every episode
    # dated the same day — is a batch release, so a two-part row in it is two
    # episodes published together, not one double-length broadcast. Told
    # apart by the season's own dates rather than by which service it was on.
    batch = len({d for e in sea["episodes"] for d in dates_of(e)}) == 1
    for e in sea["episodes"]:
        sn = e["seasonnums"]
        assert all(isinstance(x, int) for x in sn), (key, sea["n"], e)
        assert all(b == a + 1 for a, b in zip(sn, sn[1:])), (key, sea["n"], sn)
        eps += len(sn)
        row = {"id": "st-%s-s%de%02d" % (key, sea["n"], sn[0]),
               "t": e["t"],
               "n": str(sn[0]) if len(sn) == 1 else "%d–%d" % (sn[0], sn[-1])}
        bits = []
        if len(sn) > 1:
            nights = sorted(set(dates_of(e)))
            assert len(sn) == 2, (key, sea["n"], sn)
            if len(nights) > 1:
                gap = days_between(nights[0], nights[-1])
                assert len(nights) == 2 and gap == 7, (key, sea["n"], nights)
                bits.append("Two parts, a week apart")
            else:
                bits.append("Two parts, released together" if batch
                            else "Two parts, aired as one double-length episode")
        first = min(dates_of(e), default=None)
        if first and first > AS_OF:
            bits.append("airs %s" % human(first))
        note = join_bits(*bits)
        if note:
            row["note"] = note
        items.append(row)
    return items, eps


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    series = {s["key"]: s for s in data["series"]}
    assert set(series) == set(NAMES), sorted(set(series) ^ set(NAMES))

    # ---- what the source says, checked before anything is built ------------
    # Every season's enumerated {{Episode list}} rows are counted against the
    # episode count that article's own {{Series overview}} box declares. The
    # tables win if they ever disagree; this assert is what turns a
    # disagreement into a failed build instead of a quietly short list.
    shipped, pending = {}, set()
    for key, s in series.items():
        keep = []
        for sea in s["seasons"]:
            if not all(e["t"] for e in sea["episodes"]):
                # A season that has been ordered but has no announced titles
                # or dates yet — Strange New Worlds' fifth, six untitled rows.
                # One the source dates is in PENDING and gets its one row
                # below.
                assert not any(dates_of(e) for e in sea["episodes"]), \
                    "%s season %s is half-announced" % (key, sea["n"])
                if (key, sea["n"]) in PENDING:
                    pending.add((key, sea["n"]))
                    assert s["overview"].get(str(sea["n"])) == \
                        PENDING[key, sea["n"]]["episodes"], (key, sea["n"])
                continue
            n_eps = sum(len(e["seasonnums"]) for e in sea["episodes"])
            declared = s["overview"].get(str(sea["n"]))
            assert declared == n_eps, \
                "%s season %d: the overview box says %s, the episode table " \
                "enumerates %d — the table wins, so fix the count here" \
                % (key, sea["n"], declared, n_eps)
            nums = [n for e in sea["episodes"] for n in e["seasonnums"]]
            assert nums == list(range(1, n_eps + 1)), \
                "%s season %d numbering is not 1..%d: %s" % (key, sea["n"], n_eps, nums)
            keep.append(sea)
        assert keep, key
        shipped[key] = keep
    # A PENDING season that now has titles fails here: take it out of PENDING
    # and let its real rows ship — the first of them gets the pinned id anyway.
    assert pending == set(PENDING), sorted(set(PENDING) - pending)

    # ---- sections ----------------------------------------------------------
    sections = []

    # The unaired original pilot. Not one of the 79 episodes — the episode
    # list files it above season one and says so — and not broadcast until
    # 1988, so it rides along as an optional row of its own.
    cage = next(p for p in data["tos_pilots"] if p["t"] == "The Cage")
    assert dates_of(cage) == ["1988-10-04"], cage
    sections.append({
        "id": "tos-cage", "title": "The Original Series · The Cage",
        "sub": "1964 · the original pilot, not broadcast until 1988",
        "items": [{"id": "st-tos-cage", "t": "The Cage", "n": "1964",
                   "opt": True,
                   "note": "The original pilot, made in 1964 and not "
                           "broadcast until 1988"}],
    })

    films_by_tag = {}
    for f in data["films"]:
        films_by_tag.setdefault(f["era"], []).append(f)

    for kind, key in SPINE:
        if kind == "f":
            secid, title, intro = FILM_BLOCKS[key]
            got = films_by_tag[key]
            assert all(f["runtime"] and f["runtime_src"] == "wikidata"
                       for f in got), [f["t"] for f in got if not f["runtime"]]
            items = [{"id": "st-film-%d" % f["year"], "t": f["t"],
                      "n": str(f["year"]),
                      "note": join_bits("Directed by %s" % f["director"],
                                        "%d minutes" % f["runtime"])}
                     for f in got]
            mins = sum(f["runtime"] for f in got)
            sections.append({
                "id": secid, "title": title,
                "sub": "%s · %d films · about %d hours"
                       % (span(got[0]["year"], got[-1]["year"]), len(got),
                          round(mins / 60.0)),
                "intro": intro, "items": items})
            continue

        for i, sea in enumerate(shipped[key]):
            items, n_eps = season_rows(key, sea)
            days = sorted(d for e in sea["episodes"] for d in dates_of(e))
            sub = "%s · %d episodes" % (span(int(days[0][:4]), int(days[-1][:4])),
                                        n_eps)
            if len(items) != n_eps:
                sub += " in %d entries" % len(items)
            aired = sum(1 for e in sea["episodes"]
                        if min(dates_of(e), default="9999") <= AS_OF)
            if aired < len(items):
                sub += " · %d of %d aired by %s" % (aired, len(items), human(AS_OF))
            sec = {"id": "%s-s%d" % (key, sea["n"]),
                   "title": "%s · Season %d" % (NAMES[key], sea["n"]),
                   "sub": sub, "items": items}
            if i == 0:
                sec["intro"] = INTROS[key]
            sections.append(sec)

        for (pk, pn), pend in sorted(PENDING.items()):
            if pk != key:
                continue
            # The pin is the id season_rows() gives that season's episode 1,
            # and the due date is checked against AS_OF, so moving AS_OF past
            # it fails the build until the season is re-read.
            assert pend["id"] == "st-%s-s%de%02d" % (pk, pn, 1), pend
            assert pn == shipped[pk][-1]["n"] + 1, (pk, pn)
            assert AS_OF < pend["due"], "%s season %d was due %s — re-read " \
                "the table" % (pk, pn, pend["due"])
            y, m = (int(x) for x in pend["due"].split("-"))
            sections.append({
                "id": "%s-s%d" % (pk, pn),
                "title": "%s · Season %d" % (NAMES[pk], pn),
                "sub": "%d · %s%d episodes · not out yet"
                       % (y, "the final season, " if pend["final"] else "",
                          pend["episodes"]),
                "items": [{"id": pend["id"], "t": "Untitled", "n": "1",
                           "note": "Not out yet — due %s %d"
                                   % (MONTHS[m - 1], y)}]})

    sections[1]["open"] = True          # The Original Series, season one

    # ---- the claims this page makes, checked against the data --------------
    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"

    film_rows = [x for s in sections if s["id"].startswith("films-")
                 for x in s["items"]]
    # A PENDING season's one row is not an episode anyone can count yet.
    pinned = {p["id"] for p in PENDING.values()}
    assert pinned <= set(ids), pinned - set(ids)
    ep_rows = [x for s in sections if not s["id"].startswith("films-")
               for x in s["items"] if x["id"] not in pinned]
    assert len(film_rows) == 13, len(film_rows)

    per_series = {k: sum(len(e["seasonnums"]) for sea in shipped[k]
                         for e in sea["episodes"]) for k in shipped}
    assert per_series == {"tos": 79, "tas": 22, "tng": 178, "ds9": 176,
                          "voy": 172, "ent": 98, "dis": 65, "pic": 30,
                          "snw": 40, "ld": 50, "pro": 40, "sfa": 10}, per_series
    episodes = sum(per_series.values()) + 1          # + The Cage
    assert episodes == 961, episodes
    assert len(ep_rows) == 938, len(ep_rows)
    assert len(ids) == 952, len(ids)

    doubles = [e for k in shipped for sea in shipped[k]
               for e in sea["episodes"] if len(e["seasonnums"]) > 1]
    one_night = [e for e in doubles if len(set(dates_of(e))) < 2]
    assert len(doubles) == 23 and len(one_night) == 17, \
        (len(doubles), len(one_night))
    assert episodes - len(ep_rows) == len(doubles), "double bookkeeping"

    # Series run in premiere order, and the film blocks sit where the docstring
    # says they do.
    order = [k for kind, k in SPINE if kind == "s"]
    premieres = {k: min(d for sea in shipped[k] for e in sea["episodes"]
                        for d in dates_of(e)) for k in order}
    assert order == sorted(order, key=lambda k: premieres[k]), \
        [(k, premieres[k]) for k in order]
    spine = [k for _, k in SPINE]
    assert spine.index("tas") < spine.index("OriginalSeries") < spine.index("tng")
    assert spine.index("tng") < spine.index("NextGeneration") < spine.index("ds9")
    assert spine.index("ent") < spine.index("Kelvin") < spine.index("dis")

    # How tangled the run actually is, counted rather than claimed: how many
    # series were on the air at the same time as another one, and how many
    # films came out during some series' run.
    runs = {k: (min(d for sea in shipped[k] for e in sea["episodes"]
                    for d in dates_of(e)),
                max(d for sea in shipped[k] for e in sea["episodes"]
                    for d in dates_of(e))) for k in order}
    overlapping = sum(1 for k, (a, b) in runs.items()
                      if any(j != k and c <= b and a <= d
                             for j, (c, d) in runs.items()))
    during = sum(1 for f in data["films"]
                 if any(a <= f["date"] <= b for a, b in runs.values()))
    assert overlapping == 9, overlapping
    assert during == 6, during

    mins = sum(f["runtime"] for f in data["films"])
    hours = round(mins / 60.0)

    # WEIGHTING, and why there is none. All thirteen films carry a Wikidata
    # runtime. The episodes do not: the collector asked Wikidata for a P2047
    # on every episode row it could resolve to an item, and the answer is
    # measured here rather than assumed. A weighted list treats a row with no
    # weight as one hour, so weighting the films and the runtime-bearing
    # episodes while the rest stayed bare would put a guessed hour into every
    # schedule this list feeds — which is the shape of a bug this project has
    # already shipped once. Either everything is weighted honestly or nothing
    # is, and it cannot be everything, so it is nothing. If the gap ever
    # closes, this assert is where to find out.
    rows_with_rt = sum(1 for k in shipped for sea in shipped[k]
                       for e in sea["episodes"] if e.get("wd_runtime"))
    ep_row_count = len(ep_rows)
    assert rows_with_rt < ep_row_count, \
        "every episode row now carries a runtime — revisit the weighting " \
        "decision instead of shipping %d verified hours as ones" % rows_with_rt
    assert not any("w" in x for s in sections for x in s["items"])

    sfa2 = PENDING["sfa", 2]
    assert sfa2["final"], sfa2
    sfa_due = "%s %s" % (MONTHS[int(sfa2["due"][5:]) - 1], sfa2["due"][:4])

    p = {
        "slug": SLUG,
        "title": "Star Trek",
        "subtitle": "every episode and all thirteen films, in production order",
        "kind": "tv & films",
        "popularity": 92,
        "year": "1966–2026",
        "blurb": "Sixty years of it in the order it was made — %d episodes "
                 "across %s series, with the thirteen films sitting beside "
                 "the crews they belong to." % (episodes, words(len(order))),
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#392B63",
        "accentDark": "#FFC08A",
        "tiers": False,
        "notes": [
            ["The films sit with the crew they belong to.", "Each block of "
             "films follows the series whose cast it continues, at the point "
             "those films begin: the six original-cast films after the "
             "animated series, the four Next Generation films immediately "
             "after that show's finale, and the three Kelvin films in the "
             "gap after Enterprise when nothing was being made for "
             "television. %s of the thirteen came out while some series was "
             "in its run, and the section headings say so."
             % words(during).capitalize()],
            ["Series run in the order they premiered.", "Which is why Lower "
             "Decks and Prodigy sit ahead of Strange New Worlds — they "
             "started first. %s of the %s series were on the air at the "
             "same time as another one, so no arrangement of whole series is "
             "strictly chronological; premiere date is the rule this page "
             "keeps to." % (words(overlapping).capitalize(), words(len(order)))],
            ["Sections are seasons, not series.", "One section per season, "
             "running series by series, each headed with the series it "
             "belongs to. The alternative was a single 178-row accordion for "
             "The Next Generation with no season markers in it."],
            ["%s rows cover two episodes each." % words(len(doubles)).capitalize(),
             "Wikipedia's episode tables file some two-part stories as one "
             "row and this list follows them, carrying both numbers. %s of "
             "those went out as a single installment and %s a week apart; "
             "every one of the rows says which. That is %d rows covering %d "
             "episodes."
             % (words(len(one_night)).capitalize(),
                words(len(doubles) - len(one_night)), len(ep_rows), episodes)],
            ["Nothing is weighted.", "The thirteen films' runtimes are known "
             "— Wikidata carries all thirteen, about %d hours, and the film "
             "headings add them up. The episodes are not so lucky: of %d "
             "episode rows, %d carry a runtime on Wikidata and %d carry "
             "nothing, and the gap is not random — the classic shows are "
             "nearly covered while Picard, Lower Decks and Prodigy have not "
             "one runtime between them. A weighted list counts a row with no "
             "weight as one hour, so weighting what is known would push a "
             "guessed hour into every finish date %d times over. An episode "
             "and a film each count one."
             % (hours, ep_row_count, rows_with_rt,
                ep_row_count - rows_with_rt, ep_row_count - rows_with_rt)],
            ["The Cage rides along, marked optional.", "The 1964 pilot is not "
             "one of the 79 original-series episodes and was not broadcast "
             "until 1988, so it sits in a section of its own above season "
             "one."],
            ["What is not on this page.", "Star Trek: Section 31 is a "
             "television film rather than one of the thirteen theatrical "
             "features, and the Short Treks are not episodes of any of these "
             "series. Strange New Worlds' fifth season has been ordered but "
             "has no announced titles or dates, so it has no rows yet. "
             "Starfleet Academy's second and final season is due in %s with "
             "no titles announced, so for now it is one row, its premiere."
             % sfa_due],
            "Titles, numbering and broadcast dates machine-read from "
            "Wikipedia's per-series episode tables; every season's enumerated "
            "rows are asserted against that article's own Series overview "
            "count before this builds. Film runtimes and release dates from "
            "Wikidata, gated on a matching release year.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d rows (%d episode rows covering %d episodes, %d films)"
          % (out.name, len(ids), len(ep_rows), episodes, len(film_rows)))
    for key in [k for kind, k in SPINE if kind == "s"]:
        rows = sum(1 for x in sections if x["id"].startswith(key + "-s")
                   for y in x["items"] if y["id"] not in pinned)
        print("   %-22s %3d seasons %4d rows %4d episodes"
              % (NAMES[key], len(shipped[key]), rows, per_series[key]))
    print("   %-22s %3s          %4d rows" % ("films", "", len(film_rows)))


if __name__ == "__main__":
    main()
