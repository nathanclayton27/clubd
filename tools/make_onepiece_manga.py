#!/usr/bin/env python3
"""Generate properties/one-piece-manga.json.

    python3 tools/make_onepiece_manga.py

Chapters rather than episodes, so this is the one to track if you are reading
ahead of the anime — or instead of it.

Arc chapter boundaries come from the One Pace timeline data, which lists the
manga chapters each arc covers and is the same source the One Pace property
here is built from. Made contiguous: One Pace has a few cover-story segments
that interleave with the main chapters, and every chapter belongs to exactly one
arc in a tracker.

Egghead ending at 1125 and Elbaf opening at 1126 are corroborated separately —
Egghead is widely reported as 68 chapters, and 1058-1125 is 68.

LAST is the newest released chapter. Bump it and rerun.
"""
import json
import pathlib

# Viz publishes it in English and its reader is the one place every chapter
# is legitimately available, so every volume points at the same series page —
# there is no stable per-volume URL to point at instead.
VIZ = "https://www.viz.com/shonenjump/chapters/one-piece"
SERIES_LINK = [{"label": "Read on Viz", "url": VIZ}]

SLUG = "one-piece-manga"
LAST = 1198          # released 9 November 2026

# The anime's newest episode, 1180 (27 September 2026), adapts chapters
# 1150-1151, so the "Ahead of the anime" note below says roughly fifty.
# Recheck it whenever LAST moves.

# Volumes are the sections; the arc table below only labels them, so you can see
# which story an unfamiliar volume number belongs to.
# saga, arc, first chapter — each arc runs to the chapter before the next starts
ARCS = [
    ("East Blue",       "Romance Dawn",           1),
    ("East Blue",       "Orange Town",            8),
    ("East Blue",       "Syrup Village",         23),
    ("East Blue",       "Baratie",               42),
    ("East Blue",       "Arlong Park",           69),
    ("East Blue",       "Loguetown",             96),

    ("Alabasta",        "Reverse Mountain",     101),
    ("Alabasta",        "Whisky Peak",          106),
    ("Alabasta",        "Little Garden",        115),
    ("Alabasta",        "Drum Island",          130),
    ("Alabasta",        "Alabasta",             155),

    ("Sky Island",      "Jaya",                 218),
    ("Sky Island",      "Skypiea",              237),

    ("Water 7",         "Long Ring Long Land",  304),
    ("Water 7",         "Water Seven",          322),
    ("Water 7",         "Enies Lobby",          375),
    ("Water 7",         "Post-Enies Lobby",     431),

    ("Thriller Bark",   "Thriller Bark",        442),

    ("Summit War",      "Sabaody Archipelago",  490),
    ("Summit War",      "Amazon Lily",          514),
    ("Summit War",      "Impel Down",           525),
    ("Summit War",      "Marineford",           549),
    ("Summit War",      "Post-War",             581),

    ("Fish-Man Island", "Return to Sabaody",    598),
    ("Fish-Man Island", "Fish-Man Island",      603),

    ("Dressrosa",       "Punk Hazard",          654),
    ("Dressrosa",       "Dressrosa",            700),

    ("Whole Cake",      "Zou",                  801),
    ("Whole Cake",      "Whole Cake Island",    823),
    ("Whole Cake",      "Reverie",              903),

    # 149 chapters is too long to be one section. The arc is published in three
    # acts, so it splits on those rather than on an invented boundary.
    ("Wano Country",    "Wano: Act 1",          909),
    ("Wano Country",    "Wano: Act 2",          925),
    ("Wano Country",    "Wano: Act 3",          958),

    ("Final",           "Egghead",             1058),
    ("Final",           "Elbaf",               1126),
]

VOLUMES = [
    (1, 1, 8),
    (2, 9, 17),
    (3, 18, 26),
    (4, 27, 35),
    (5, 36, 44),
    (6, 45, 53),
    (7, 54, 62),
    (8, 63, 71),
    (9, 72, 81),
    (10, 82, 90),
    (11, 91, 99),
    (12, 100, 108),
    (13, 109, 117),
    (14, 118, 126),
    (15, 127, 136),
    (16, 137, 145),
    (17, 146, 155),
    (18, 156, 166),
    (19, 167, 176),
    (20, 177, 186),
    (21, 187, 195),
    (22, 196, 205),
    (23, 206, 216),
    (24, 217, 226),
    (25, 227, 236),
    (26, 237, 246),
    (27, 247, 255),
    (28, 256, 264),
    (29, 265, 275),
    (30, 276, 285),
    (31, 286, 295),
    (32, 296, 305),
    (33, 306, 316),
    (34, 317, 327),
    (35, 328, 336),
    (36, 337, 346),
    (37, 347, 357),
    (38, 358, 367),
    (39, 368, 377),
    (40, 378, 388),
    (41, 389, 399),
    (42, 400, 409),
    (43, 410, 419),
    (44, 420, 430),
    (45, 431, 440),
    (46, 441, 449),
    (47, 450, 459),
    (48, 460, 470),
    (49, 471, 481),
    (50, 482, 491),
    (51, 492, 502),
    (52, 503, 512),
    (53, 513, 522),
    (54, 523, 532),
    (55, 533, 541),
    (56, 542, 551),
    (57, 552, 562),
    (58, 563, 573),
    (59, 574, 584),
    (60, 585, 594),
    (61, 595, 603),
    (62, 604, 614),
    (63, 615, 626),
    (64, 627, 636),
    (65, 637, 646),
    (66, 647, 656),
    (67, 657, 667),
    (68, 668, 678),
    (69, 679, 690),
    (70, 691, 700),
    (71, 701, 711),
    (72, 712, 721),
    (73, 722, 731),
    (74, 732, 742),
    (75, 743, 752),
    (76, 753, 763),
    (77, 764, 775),
    (78, 776, 785),
    (79, 786, 795),
    (80, 796, 806),
    (81, 807, 816),
    (82, 817, 827),
    (83, 828, 838),
    (84, 839, 848),
    (85, 849, 858),
    (86, 859, 869),
    (87, 870, 879),
    (88, 880, 889),
    (89, 890, 900),
    (90, 901, 910),
    (91, 911, 921),
    (92, 922, 931),
    (93, 932, 942),
    (94, 943, 953),
    (95, 954, 964),
    (96, 965, 974),
    (97, 975, 984),
    (98, 985, 994),
    (99, 995, 1004),
    (100, 1005, 1015),
    (101, 1016, 1025),
    (102, 1026, 1035),
    (103, 1036, 1046),
    (104, 1047, 1055),
    (105, 1056, 1065),
    (106, 1066, 1076),
    (107, 1077, 1088),
    (108, 1089, 1100),
    (109, 1101, 1110),
    (110, 1111, 1121),
    (111, 1122, 1133),
    (112, 1134, 1144),
    (113, 1145, 1155),
    (114, 1156, 1166),
    (115, 1167, 1179),
    # Volume 116 is due 4 December 2026. Add it once it is out and Wikipedia
    # lists its chapters outright (its list is still commented out there).
]

MOVING = {"Elbaf"}


def slugify(name):
    out = []
    for ch in name.lower():
        if ch.isalnum():
            out.append(ch)
        elif out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-")


def main():
    # chapter -> arc, for labelling
    arc_of = {}
    for i, (saga, arc, first) in enumerate(ARCS):
        last = ARCS[i + 1][2] - 1 if i + 1 < len(ARCS) else LAST
        for c in range(first, last + 1):
            arc_of[c] = arc

    def arcs_in(a, b):
        seen = []
        for c in range(a, b + 1):
            name = arc_of.get(c)
            if name and name not in seen:
                seen.append(name)
        return seen

    sections = []
    for num, first, last in VOLUMES:
        names = arcs_in(first, last)
        sections.append({
            "id": "v-%d" % num,
            "title": "Volume %d" % num,
            "sub": "chapters %d–%d · %s" % (first, last, ", ".join(names)),
            "links": SERIES_LINK,
            "items": [
                {"id": "opm-%d" % c, "t": "Chapter", "n": str(c)}
                for c in range(first, last + 1)
            ],
        })

    collected = VOLUMES[-1][2]
    if collected < LAST:
        names = arcs_in(collected + 1, LAST)
        sections.append({
            "id": "v-uncollected",
            "title": "Not yet collected",
            "sub": "chapters %d–%d · %s · no volume yet"
                   % (collected + 1, LAST, ", ".join(names)),
            "links": SERIES_LINK,
            "items": [
                {"id": "opm-%d" % c, "t": "Chapter", "n": str(c)}
                for c in range(collected + 1, LAST + 1)
            ],
        })

    ids = [x["id"] for s in sections for x in s["items"]]
    total = len(ids)
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate item ids")
    if total != LAST:
        raise SystemExit("expected %d chapters, built %d" % (LAST, total))
    # volumes must tile the chapters with no gap or overlap
    for i in range(1, len(VOLUMES)):
        if VOLUMES[i][1] != VOLUMES[i - 1][2] + 1:
            raise SystemExit("volume %d does not follow %d" % (VOLUMES[i][0], VOLUMES[i-1][0]))

    prop = {
        "slug": SLUG,
        "title": "One Piece (manga)",
        "subtitle": "Eiichiro Oda",
        "kind": "manga",
        "popularity": 80,
        "year": "1997–",
        "blurb": "%d chapters across %d volumes, still running." % (total, len(VOLUMES)),
        "unit": {"one": "chapter", "many": "chapters"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "tiers": False,
        "accent": "#A8721F",
        "accentDark": "#E0AE55",
        "notes": [
            ["Ahead of the anime.", "The manga is well past where the anime is. "
                                    "Chapter %d here is roughly fifty chapters "
                                    "beyond what has been animated." % LAST],
            ["Volumes.", "Sections are the collected volumes, with the arc each one "
                         "covers named alongside. Volume boundaries are parsed from the "
                         "Wikipedia chapter lists and checked to tile the chapters with "
                         "no gap or overlap."],
            "Still running. This goes up to chapter %d; rerun the generator to "
            "extend it." % LAST,
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d volumes, %d sections, %d chapters" % (len(VOLUMES), len(sections), total))
    print("  longest section: %d chapters" % max(len(s["items"]) for s in sections))


if __name__ == "__main__":
    main()
