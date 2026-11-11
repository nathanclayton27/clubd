#!/usr/bin/env python3
"""Generate properties/jojo-manga.json.

    python tools/make_jojo-manga.py

The manga, in the Japanese tankobon volumization — one section per volume,
one row per chapter, nine parts end to end. The anime list is `jojo`; the
anime reached Steel Ball Run in 2026, and this carries on through it,
JoJolion and The JoJoLands.

**The numbering restarts, and the source is what says so.** Shueisha ran the
volumes 1-63 straight through Parts 1-5; the hub article's lead states it
plainly — "After volume 63, the beginning of each Part has reset the volume
number count back at one" — and from Part 6 the volume tables print the
part's own number with the cumulative one in brackets, "1 (64)". So both
numberings are published, and neither is invented here: sections lead with
the number on the spine and carry the overall number in the sub wherever the
two differ. The chapter numbering resets with it, 1-594 across Parts 1-5 and
then from 1 again in each later part, which is why the item ids carry a
per-part prefix — one id per chapter, never two chapters sharing one.

The JoJoLands is ongoing. It stops at the last released volume, and
EXPECTED asserts that count, so the build fails when the next one ships
rather than the list quietly staying short.

Everything numeric comes from tools/data/jojo-manga.json, which
scratch/agent-jojomanga/parse.py builds from the nine Wikipedia part
articles and asserts against the articles' own counts.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop as gwprop  # noqa: E402

SLUG = "jojo-manga"

DATA = pathlib.Path(__file__).resolve().parent / "data" / ("%s.json" % SLUG)

WIKI = "https://en.wikipedia.org/wiki/"

# The totals the group signed up for. Bump these deliberately, never to make
# a red build go green — a changed number means the source moved.
EXPECTED = {
    "chapters": 993,
    "volumes": 140,
    # part -> (volumes, first chapter, last chapter)
    "parts": {
        1: (5, 1, 47),
        2: (7, 48, 114),
        3: (16, 115, 265),
        4: (18, 266, 436),
        5: (17, 437, 594),
        6: (17, 1, 158),
        7: (24, 1, 95),
        8: (27, 1, 110),
        9: (9, 1, 36),
    },
    # the last part is still being serialized; this is its released-volume
    # count, asserted upstream against The JoJoLands' own infobox
    "ongoing_part": 9,
    "ongoing_volumes": 9,
}

# per-part: the Wikipedia article the volume table lives on, and the item-id
# prefix for the chapter run that part belongs to
PART_PAGE = {
    1: "Phantom_Blood",
    2: "Battle_Tendency",
    3: "Stardust_Crusaders",
    4: "Diamond_Is_Unbreakable",
    5: "Golden_Wind_(manga)",
    6: "Stone_Ocean",
    7: "Steel_Ball_Run",
    8: "JoJolion",
    9: "The_JoJoLands",
}

PREFIX = {"a": "jjm", "so": "jjm-so", "sbr": "jjm-sbr",
          "jjl": "jjm-jjl", "tjl": "jjm-tjl"}

# One line each, on the first volume of every part whose numbering restarts —
# which is the one place a reader meets a second "Volume 1" and needs telling.
RESTART_INTRO = (
    "The volume numbering starts over here: the spine reads %s 1, and it is "
    "volume %d overall."
)


def join_names(names):
    return ", ".join(names[:-1]) + " and " + names[-1]


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    parts = data["parts"]

    assert len(parts) == 9, len(parts)
    assert [p["part"] for p in parts] == list(range(1, 10))

    for p in parts:
        want = EXPECTED["parts"][p["part"]]
        got = (len(p["volumes"]), p["first"], p["last"])
        assert got == want, "part %d: %r, expected %r" % (p["part"], got, want)

    # volumes tile their part's chapters with no gap or overlap
    for p in parts:
        nxt = p["first"]
        for v in p["volumes"]:
            assert v["first"] == nxt, \
                "part %d volume %d does not follow chapter %d" \
                % (p["part"], v["vol"], nxt - 1)
            assert v["last"] >= v["first"], "part %d volume %d is empty" \
                % (p["part"], v["vol"])
            nxt = v["last"] + 1
        assert nxt - 1 == p["last"], "part %d stops at %d" % (p["part"], nxt - 1)

    # the cumulative volume numbers run 1..N unbroken across all nine parts
    cum = [v["cum"] for p in parts for v in p["volumes"]]
    assert cum == list(range(1, len(cum) + 1)), "cumulative volume numbers"
    assert len(cum) == EXPECTED["volumes"], len(cum)

    # and the numbering the source prints: continuous until the reset, then
    # 1..n within each later part
    for p in parts:
        own = [v["vol"] for v in p["volumes"]]
        if p["volumes"][0]["cum"] == p["volumes"][0]["vol"]:
            assert own == [v["cum"] for v in p["volumes"]], p["part"]
        else:
            assert own == list(range(1, len(own) + 1)), \
                "part %d does not restart at volume 1" % p["part"]

    # the ongoing part is held back at its last released volume
    ong = parts[EXPECTED["ongoing_part"] - 1]
    assert ong["part"] == EXPECTED["ongoing_part"]
    assert len(ong["volumes"]) == EXPECTED["ongoing_volumes"], \
        "%s is at %d volumes, expected %d — rerun the pipeline and bump " \
        "EXPECTED" % (ong["name"], len(ong["volumes"]),
                      EXPECTED["ongoing_volumes"])

    # the parts whose volume numbering starts over, named rather than counted
    # by hand — every one of them puts a second "Volume 1" on the page
    restart_names = [p["name"] for p in parts
                     if p["volumes"][0]["vol"] != p["volumes"][0]["cum"]]
    assert len(restart_names) == 4, restart_names
    last_continuous = max(v["cum"] for p in parts for v in p["volumes"]
                          if v["vol"] == v["cum"])

    sections = []
    for p in parts:
        page = PART_PAGE[p["part"]]
        links = [{"label": "The volume list", "url": WIKI + page}]
        prefix = PREFIX[p["run"]]
        restarts = p["volumes"][0]["vol"] != p["volumes"][0]["cum"]
        for v in p["volumes"]:
            sub = "chapters %d–%d" % (v["first"], v["last"])
            if v["vol"] != v["cum"]:
                sub += " · volume %d overall" % v["cum"]
            sec = {
                "id": "p%d-v%d" % (p["part"], v["vol"]),
                "title": "%s · Volume %d" % (p["name"], v["vol"]),
                "sub": sub,
                "links": links,
                "items": [{"id": "%s-%d" % (prefix, c), "t": "Chapter",
                           "n": str(c)}
                          for c in range(v["first"], v["last"] + 1)],
            }
            if restarts and v is p["volumes"][0]:
                sec["intro"] = RESTART_INTRO % (p["name"], v["cum"])
            sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate item ids"
    assert len(ids) == EXPECTED["chapters"], len(ids)
    assert len(sections) == EXPECTED["volumes"], len(sections)
    assert len({s["id"] for s in sections}) == len(sections), "duplicate section ids"

    # Unweighted, like every manga list here: chapter counts live in the
    # section subs and no row carries hours. A row is exactly id/t/n — which
    # also means no note exists to leak a bare year into, the one thing
    # build.py reads a year out of when a row's `n` is not one.
    for s in sections:
        for x in s["items"]:
            assert set(x) == {"id", "t", "n"}, "unexpected row fields: %r" % x
            assert "w" not in x, "a chapter row carries a weight"
    assert not any(re.search(r"\b(?:18|19|20)\d{2}\b", x.get("note") or "")
                   for s in sections for x in s["items"]), "a note names a year"

    prop = {
        "slug": SLUG,
        "title": "JoJo's Bizarre Adventure (manga)",
        "subtitle": "Hirohiko Araki",
        "kind": "manga",
        "popularity": 70,
        "year": "1987–",
        "blurb": "All %d chapters in %d volumes — nine parts, nine JoJos, "
                 "one bloodline, still running."
                 % (EXPECTED["chapters"], EXPECTED["volumes"]),
        "unit": {"one": "chapter", "many": "chapters"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "tiers": False,
        "accent": "#5B3A8C",
        "accentDark": "#B79BE8",
        "notes": [
            ["Nine parts, and the numbering restarts with them.",
             "Shueisha ran the volumes 1–%d straight through Parts 1–5, then "
             "began each later part again at volume 1 — so %s each start over "
             "at Volume 1. Sections lead with the number on the spine and "
             "name the part; where the source also prints a cumulative "
             "number, the sub carries it."
             % (last_continuous, join_names(restart_names))],
            ["Chapters restart too.",
             "Chapters run 1–%d across Parts 1–5, then start again at 1 for "
             "%s. Chapter %d sits at the end of volume %d here, where the "
             "Japanese volume prints it, rather than at the head of volume %d "
             "where the English edition moves it."
             % (parts[4]["last"], join_names(restart_names),
                parts[1]["last"], parts[1]["volumes"][-1]["vol"],
                parts[2]["volumes"][0]["vol"])],
            ["Still running.",
             "The JoJoLands is ongoing, and this stops at volume %d — the last "
             "one released. The generator asserts that count against the "
             "article, so the next volume fails the build rather than leaving "
             "the list quietly short. Rerun the pipeline to extend it."
             % EXPECTED["ongoing_volumes"]],
            ["The anime has reached Steel Ball Run.",
             "The jojo list here is the David Production anime, which began "
             "adapting Steel Ball Run in 2026. JoJolion and The JoJoLands "
             "exist only as manga."],
            "Volume boundaries and chapter numbers machine-read from the nine "
            "Wikipedia part articles that List of JoJo's Bizarre Adventure "
            "volumes transcludes, each volume checked to tile its part's "
            "chapters with no gap or overlap. Two unnumbered volume-exclusive "
            "Steel Ball Run extras carry no chapter number and are left out.",
        ],
        "sections": sections,
    }

    # manga is not a syncable kind — build.py pairs rows across lists only
    # for films and games, so nothing here can tick anything elsewhere
    kind = prop["kind"]
    assert "film" not in kind and "game" not in kind, \
        "kind %r would make these rows syncable" % kind

    out = gwprop.write(prop)

    print("wrote %s" % out.name)
    print("  %d sections, %d chapters, unweighted"
          % (len(sections), len(ids)))
    print("  longest section: %d chapters"
          % max(len(s["items"]) for s in sections))
    for p in parts:
        v = p["volumes"]
        print("   Part %d  %-22s %2d volumes (%d–%d)  chapters %d–%d"
              % (p["part"], p["name"], len(v), v[0]["vol"], v[-1]["vol"],
                 p["first"], p["last"]))


if __name__ == "__main__":
    main()
