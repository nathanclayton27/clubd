#!/usr/bin/env python3
"""Generate properties/president-curtis.json — President Curtis (2026).

    python3 tools/make_president-curtis.py

The Rick and Morty spin-off: Keith David's President Andre Curtis and his
staff handling the crises Rick leaves alone. Ten episodes, weekly on Sundays
on Adult Swim from 26 July 2026, reaching HBO Max the day after broadcast.
Adult Swim renewed it for a second season two days before the premiere.

Season one was written up mid-air, which made this the second property
after lanterns to carry a `schedule` — one dated window per episode, so the
pace line answers "am I caught up with the broadcast" rather than "will I
finish by some distant date". The window shape is lanterns' exactly: a window
opens on an episode's air date and runs six days, and `through` is that
episode's number. Season one finished on 27 September 2026.

All ten episodes are listed whether or not they have aired. An announced row
is what an airing show looks like and the schedule needs the whole season;
the aired/upcoming wording in the row notes, the blurb and the notes is frozen
by AS_OF below rather than read from the clock, so two runs of this file
always agree. AS_OF is cross-checked against the infobox's episode count.

Titles and air dates are machine-read from the {{Episode list}} rows of the
Wikipedia article "President Curtis (TV series)" by
scratch/agent-curtis/episodes.py, which asserts the numbering is 1..N
contiguous and that N matches the season length the article states in prose;
the committed result is tools/data/president-curtis-episodes.json. Last read
2026-11-11, revision 1379745232.

Nothing is weighted. The episode table declares no runtime column, no
episode has its own article or Wikidata item, and the series' Wikidata item
carries no P2047 — the infobox's blanket "24 minutes" is a series-level
figure, not per-episode data, and ten identical invented weights would be a
guess dressed as a measurement. Every episode counts one, as in
make_xfiles.py.
"""
import json
import pathlib
import sys
from datetime import date, timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop

SLUG = "president-curtis"

# Freezes the aired/upcoming wording in the row notes. Bump it when you
# re-run; reading the clock instead would make the file differ by the day.
AS_OF = date(2026, 11, 11)


def daymonth(d):
    """'26 July' — %-d is not portable, so the day is formatted by hand."""
    return "%d %s" % (d.day, d.strftime("%B"))


def main():
    data = json.loads((pathlib.Path(__file__).resolve().parent / "data"
                       / ("%s-episodes.json" % SLUG)).read_text(encoding="utf-8"))
    eps = data["episodes"]

    items, windows = [], []
    for r in eps:
        n = r["e"]
        airs = date.fromisoformat(r["d"])
        role = ("series premiere" if n == 1 else
                "season finale" if n == len(eps) else "")
        items.append({
            "id": "%s-%d" % (SLUG, n),
            "t": r["t"],
            "n": str(n),
            "note": prop.join_bits(
                "%s %s" % ("aired" if airs <= AS_OF else "airs", daymonth(airs)),
                role),
        })
        # a week to watch each one, so "behind" means behind the broadcast
        windows.append({
            "start": r["d"],
            "end": (airs + timedelta(days=6)).isoformat(),
            "through": n,
            "label": "Episode %d" % n,
        })

    first = date.fromisoformat(eps[0]["d"])
    last = date.fromisoformat(eps[-1]["d"])

    # AS_OF is checked against the source, not trusted: the infobox counts
    # the episodes that have aired, so a slipped date fails here rather than
    # the list claiming an episode is out.
    aired = sum(1 for r in eps if date.fromisoformat(r["d"]) <= AS_OF)
    assert str(aired) == data["meta"]["num_episodes_infobox"],         ("AS_OF %s makes %d episodes aired but the infobox counts %s — bump "
         "AS_OF, or the schedule moved"
         % (AS_OF, aired, data["meta"]["num_episodes_infobox"]))
    done = aired == len(eps)

    sections = [{
        "id": "s1",
        "title": "Season 1",
        "sub": "%d episodes · weekly from %d %s" % (len(eps), first.day,
                                                    first.strftime("%B %Y")),
        "items": items,
    }]

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate item ids"
    assert len(ids) == len(eps), "built %d rows for %d episodes" % (len(ids), len(eps))
    assert [x["n"] for x in items] == [str(i) for i in range(1, len(eps) + 1)], \
        "episode numbering is not 1..N"
    thr = [w["through"] for w in windows]
    assert thr == sorted(thr), "window targets are not monotonic"
    assert thr[-1] == len(eps), "last window does not close the season"
    for a, b in zip(windows, windows[1:]):
        assert a["end"] < b["start"], "windows overlap: %s / %s" % (a, b)

    p = {
        "slug": SLUG,
        "title": "President Curtis",
        "subtitle": "Keith David as President Andre Curtis",
        "kind": "tv",
        # appended after the current last property, the way every recent
        # addition has been. Sitting it beside lanterns at 8 — the other
        # currently-airing weekly show — would read better in the picker but
        # makes a fourth order tie, and qa_lint's known-tie list is not this
        # generator's to edit. One number to change if the lead wants it.
        "popularity": 26,
        "year": "2026",
        "blurb": "The Rick and Morty spin-off — %d episodes, weekly, %s."
                 % (len(eps), "all aired" if done else "still airing"),
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#4F6B14",
        "accentDark": "#A8D93F",
        "tiers": False,
        "schedule": {"kind": "windows", "windows": windows},
        "notes": [
            ["All aired." if done else "Airing now.",
             "One window per episode, so the pace line tells "
             "you whether you are caught up with the broadcast rather than on "
             "track for some distant finish. The last one %s on %s %d."
             % ("landed" if done else "lands", daymonth(last), last.year)],
            ["Where it airs.", "Sundays on Adult Swim — the premiere followed "
             "the Rick and Morty ninth-season finale — with episodes reaching "
             "HBO Max the day after broadcast."],
            ["Already renewed.", "Adult Swim ordered a second season in July "
             "2026, ahead of the premiere."],
        ] + ([] if done else [
            ["The whole season is listed.", "All %d episodes are dated in the "
             "source, so the ones that have not aired yet are listed too. The "
             "schedule needs them, and an announced row is what an airing "
             "show looks like." % len(eps)],
        ]) + [
            ["Nothing is weighted.", "The source carries no per-episode "
             "runtime, so every episode counts one."],
            "Titles and air dates machine-read from the Wikipedia article "
            "\"President Curtis (TV series)\"; the season length is checked "
            "against the article's own count before this builds.",
        ],
        "sections": sections,
    }

    out = prop.write(p)

    print("wrote %s — %d rows" % (out.name, len(ids)))
    print("   %-10s %2d rows  %s" % (sections[0]["title"], len(items),
                                     sections[0]["sub"]))
    print("   span %s .. %s · unweighted" % (eps[0]["d"], eps[-1]["d"]))
    for it, w in zip(items, windows):
        print("   %2s  %-10s %-33s %s .. %s"
              % (it["n"], it["t"], it["note"], w["start"], w["end"]))


if __name__ == "__main__":
    main()
