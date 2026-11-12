#!/usr/bin/env python3
"""Generate properties/one-pace.json — the One Pace recut.

    python3 tools/make_onepace.py

One Pace is a fan project that re-edits the One Piece anime down to the manga's
pacing: filler cut, padding removed. Arc names, order, the manga chapters each covers and the anime episodes each
replaces come from the official watch page at https://onepace.net/en/watch —
read out of the timeline data the page itself ships, so this is what One Pace
says rather than someone's summary of it.

Per-arc episode COUNTS first came from a community mirror. Since the 2026-11-11
refresh they come from the same official page, which now lists every released
episode of every arc; the chapter and anime ranges were re-read from it then too.
Two differences were ruled on 2026-11-12 (CLU-625, Nathan delegated the call):
the page lists 8 Baratie episodes where this list had shipped 9, so Baratie
counts 8 and row 9 stays as a marked, uncounted row (KEPT below) because its id
holds ticks; and Long Ring Long Land's 2-minute untitled "00" piece ahead of its
episode 1 is not a row, which the Numbering note says.

Each arc numbers its episodes from 1, as the releases do, so there is no
continuous episode number to track.

Two "special" segments are left out — the One Piece Fan Letter tie-in and an
April Fools release — since neither is part of the run. Wano and Egghead are
both marked Work in Progress on the page (2026-11-11: Wano 63 and Egghead 23
onward not released yet), so their counts will grow.
"""
import json
import pathlib

SLUG = "one-pace"


ARCS = [
    ('Romance Dawn', '1-7', '1-3, 19, Episode of East Blue', 4),
    ('Orange Town', '8-21', '4-8', 3),
    ('Syrup Village', '23-41', '9-17', 7),
    ('Gaimon', '42, 22', '18', 1),
    # The page lists 8 Baratie episodes; row 9 shipped from an older count and
    # stays in KEPT (CLU-625).
    ('Baratie', '42-68', '19-30, 135', 8),
    ('Arlong Park', '69-95', '31-44', 10),
    ("The Adventures of Buggy's Crew", '35-75 cover stories', '46-47', 1),
    ('Loguetown', '96-100, Loguetown Arc (Novel)', '45, 48-53', 3),
    ('Reverse Mountain', '101-105', '54-55, 61-63', 2),
    ('Whisky Peak', '106-114', '64-67', 2),
    ('The Trials of Koby-Meppo', '83-119 cover stories', '68-69', 1),
    ('Little Garden', '115-129', '70-79', 5),
    ('Drum Island', '129-155', '78-91', 8),
    ('Alabasta', '155-218', '92-98, 100-101, 103-130', 21),
    ('Jaya', '218-236', '143-152', 8),
    ('Skypiea', '237-303', '153-195, 203, 207', 25),
    ('Long Ring Long Land', '303-321', '207-212, 215, 217-219, 225-228', 6),
    ('Water Seven', '322-374', '228-263, 320', 20),
    ('Enies Lobby', '375-430', '263-278, 284-302, 304-312', 25),
    ('Post-Enies Lobby', '431-441', '313-325', 6),
    ('Thriller Bark', '442-489', '326, 337-381', 22),
    ('Sabaody Archipelago', '490-513', '385-405', 11),
    ('Amazon Lily', '514-524', '408-421', 5),
    ('Impel Down', '525-548', '422-425, 430-451, 454', 10),
    ('If You Could Go Anywhere... The Adventures of the Straw Hats', '543-560 cover stories', '453-456', 1),
    ('Marineford', '549-580', '452, 459-465, 467-489', 17),
    ('Post-War', '581-597', '490-491, 493-498, 500-505, 507-516, Episode of Sabo', 8),
    ('Return to Sabaody', '598-602', '517-522', 3),
    ('Fishman Island', '603-653', '523-541, 543-573', 24),
    ('Punk Hazard', '654-699', '574, 579-589, 591-626, 628', 22),
    ('Dressrosa', '700-800', '628-745', 48),
    ('Zou', '801-822', '746-747, 751-774, 776', 10),
    ('Whole Cake Island', '823-902', '777-779, 783-877', 39),
    ('Reverie', '903-908', '878-889', 3),
    ('Wano', '909-1057', '890-894, 897-906, 908-1028, 1031-1083, 1085', 62),
    ('Egghead', '1058-1126', '1086-1155', 22),
]

MOVING = {"Wano", "Egghead"}

# Rows shipped from an older count that the official page no longer lists.
# Their ids are where users' ticks live, so they stay, with a note, after the
# arc's real episodes, and the arc's count and the blurb leave them out.
KEPT = {
    "Baratie": [(9, "One Pace now lists Baratie as 8 episodes; this row, from "
                    "an older count, stays for anyone who ticked it.")],
}

# Three arcs took their official names after ids had already shipped. Item ids
# are what progress is stored against, so those keep the slug they were first
# published with — the title on screen changes, the key underneath does not.
ID_ALIAS = {
    "Whisky Peak": "whiskey-peak",
    "Alabasta": "arabasta",
    "If You Could Go Anywhere... The Adventures of the Straw Hats":
        "the-adventures-of-the-straw-hat-pirates",
}


def slugify(name):
    out = []
    for ch in name.lower():
        if ch.isalnum():
            out.append(ch)
        elif out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-")


def main():
    sections = []
    episodes = 0
    for arc, chapters, anime, n in ARCS:
        episodes += n
        sid = ID_ALIAS.get(arc, slugify(arc))
        bits = []
        if chapters: bits.append("chapters " + chapters)
        if anime:    bits.append("anime " + anime)
        bits.append("%d episode%s" % (n, "" if n == 1 else "s"))
        if arc in MOVING: bits.append("still releasing")
        sections.append({
            "id": "a-" + sid,
            "title": arc,
            "sub": " · ".join(bits),
            "items": [
                {"id": "onepace-%s-%d" % (sid, i), "t": "Episode", "n": str(i)}
                for i in range(1, n + 1)
            ] + [
                {"id": "onepace-%s-%d" % (sid, i), "t": "Episode", "n": str(i),
                 "note": note}
                for i, note in KEPT.get(arc, [])
            ],
        })

    ids = [x["id"] for s in sections for x in s["items"]]
    total = len(ids)
    if total != episodes + sum(len(v) for v in KEPT.values()):
        raise SystemExit("KEPT names an arc that is not in ARCS")
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate item ids")
    if len(sections) != 36:
        raise SystemExit("expected 36 arcs, built %d" % len(sections))

    prop = {
        "slug": SLUG,
        "title": "One Pace",
        "subtitle": "One Piece at the manga's pacing",
        "kind": "anime",
        "popularity": 33,
        "year": "fan recut",
        "blurb": "%d episodes, %d arcs, no filler and no padding." % (episodes, len(ARCS)),
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#2E7A6B",
        "accentDark": "#5FBFA8",
        "tiers": False,
        "notes": [
            ["What this is.", "A fan re-edit of the One Piece anime cut down to the "
                              "manga's pacing — filler removed, padding trimmed. The "
                              "same story as the One Piece tracker here, in roughly a "
                              "third of the runtime."],
            ["Numbering.", "One Pace numbers each arc from 1 rather than running a "
                           "continuous count, so the episode numbers here restart in "
                           "every section, exactly as the releases do. The 2-minute "
                           "untitled 00 that opens Long Ring Long Land is not a row."],
            ["Source.", "Arc order, names, the manga chapters each covers and the "
                        "anime episodes each replaces are read from the official "
                        "watch page at onepace.net. Wano and Egghead are still being "
                        "released and their counts will grow."],
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d arcs, %d episodes, %d rows" % (len(sections), episodes, total))
    for s in sections[:3]:
        print("   %-20s %s" % (s["title"][:20], s["sub"]))


if __name__ == "__main__":
    main()
