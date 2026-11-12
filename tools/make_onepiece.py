#!/usr/bin/env python3
"""Generate properties/one-piece.json.

    python3 tools/make_onepiece.py

Arc boundaries from animefillerguide, cross-checked against the two arc lengths
everyone quotes: Wano is 196 episodes and Dressrosa is 118. Both come out right.

Two things to know about the shape of this one:

Arcs are made contiguous. Several have small filler arcs cut into the middle of
them — Buggy's side story inside Loguetown, Little East Blue inside Impel Down,
Cidre Guild and Uta's Past inside Wano — and a strip cannot show a gap. Those
are folded into the surrounding arc, which is how every watch order presents
them anyway. Filler arcs that stand alone keep their own section and every
episode in them is flagged optional.

Episode titles are deliberately absent. There are over eleven hundred, no single
source lists them all in one fetch, and a wrong title is worse than none. The arc
is what you navigate by here.

LAST is the newest aired episode. Bump it and rerun as the show continues.
NEXT holds episodes announced with a date but not yet aired (a bare year is
enough); they follow LAST as ordinary rows marked "Not out yet". When one airs,
raise LAST past it and take it out of NEXT.
"""
import json
import pathlib

SLUG = "one-piece"
LAST = 1180          # newest aired episode as of 11 November 2026
LAST_AIRED = "27 September 2026"   # its air date, from One Piece season 22

# Announced, not aired: episode -> due date as the source gives it. After 1180
# aired, the official X account said the next episode airs in 2027, "detailed
# broadcast timing to follow" (Oricon News 2482880, 27 Sep 2026), still the
# latest as of 12 Nov 2026. It continues the open Elbaph season (One Piece
# season 22 on Wikipedia: last_aired = present), so it ends that arc's run.
# No `w`: nothing on this list is weighted, and a lone w: 0 would switch the
# page into hours. The id is op-<number>, so a title or date arriving later
# cannot move it.
NEXT = {1181: "2027"}

# saga, arc, first episode, filler?
# each arc runs to the episode before the next one starts
ARCS = [
    ("East Blue",      "Romance Dawn",           1, False),
    ("East Blue",      "Orange Town",            4, False),
    ("East Blue",      "Syrup Village",          9, False),
    ("East Blue",      "Baratie",               19, False),
    ("East Blue",      "Arlong Park",           31, False),
    ("East Blue",      "Loguetown",             45, False),
    ("East Blue",      "Warship Island",        54, True),

    ("Alabasta",       "Reverse Mountain",      62, False),
    ("Alabasta",       "Whisky Peak",           64, False),
    ("Alabasta",       "Koby and Helmeppo",     68, True),
    ("Alabasta",       "Little Garden",         70, False),
    ("Alabasta",       "Drum Island",           78, False),
    ("Alabasta",       "Alabasta",              92, False),
    ("Alabasta",       "Post-Alabasta",        131, True),

    ("Sky Island",     "Goat Island",          136, True),
    ("Sky Island",     "Ruluka Island",        139, True),
    ("Sky Island",     "Jaya",                 144, False),
    ("Sky Island",     "Skypiea",              153, False),
    ("Sky Island",     "G-8",                  196, True),

    ("Water 7",        "Long Ring Long Land",  207, False),
    ("Water 7",        "Ocean's Dream",        220, True),
    ("Water 7",        "Foxy's Return",        225, True),
    ("Water 7",        "Water 7",              229, False),
    ("Water 7",        "Enies Lobby",          264, False),
    ("Water 7",        "Post-Enies Lobby",     313, False),

    ("Thriller Bark",  "Ice Hunter",           326, True),
    ("Thriller Bark",  "Thriller Bark",        337, False),
    ("Thriller Bark",  "Spa Island",           382, True),

    ("Summit War",     "Sabaody Archipelago",  385, False),
    ("Summit War",     "Amazon Lily",          408, False),
    ("Summit War",     "Impel Down",           422, False),
    ("Summit War",     "Marineford",           457, False),
    ("Summit War",     "Post-War",             490, False),

    ("Fish-Man Island","Return to Sabaody",    517, False),
    ("Fish-Man Island","Fish-Man Island",      523, False),

    ("Dressrosa",      "Z's Ambition",         575, True),
    ("Dressrosa",      "Punk Hazard",          579, False),
    ("Dressrosa",      "Caesar Retrieval",     626, True),
    ("Dressrosa",      "Dressrosa",            629, False),

    ("Whole Cake",     "Silver Mine",          747, True),
    ("Whole Cake",     "Zou",                  751, False),
    ("Whole Cake",     "Marine Rookie",        780, True),
    ("Whole Cake",     "Whole Cake Island",    783, False),
    ("Whole Cake",     "Levely",               878, False),

    # 196 episodes is too long to be one section, and the anime is already cut
    # into three acts, so it is split on those.
    ("Wano Country",   "Wano: Act 1",          890, False),
    ("Wano Country",   "Wano: Act 2",          918, False),
    ("Wano Country",   "Wano: Act 3",          959, False),

    ("Final",          "Egghead",             1086, False),
    ("Final",          "Elbaph",              1156, False),
]


def slugify(name):
    out = []
    for ch in name.lower():
        if ch.isalnum():
            out.append(ch)
        elif out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-")


def main():
    # announced episodes come straight after the aired ones, with no gap
    if sorted(NEXT) != list(range(LAST + 1, LAST + 1 + len(NEXT))):
        raise SystemExit("NEXT must run on from LAST: %r" % sorted(NEXT))
    final = LAST + len(NEXT)

    sections = []
    for i, (saga, arc, first, filler) in enumerate(ARCS):
        last = ARCS[i + 1][2] - 1 if i + 1 < len(ARCS) else final
        n = last - first + 1
        if n < 1:
            raise SystemExit("arc %r has no episodes" % arc)
        sections.append({
            "id": "a-" + slugify(arc),
            "title": arc,
            "sub": "%s · episode%s %d–%d%s"
                   % (saga, "" if n == 1 else "s", first, last,
                      " · filler" if filler else ""),
            "items": [
                dict({"id": "op-%d" % e, "t": "Episode", "n": str(e)},
                     **({"opt": 1} if filler else {}),
                     **({"note": "Not out yet — due %s" % NEXT[e]}
                        if e in NEXT else {}))
                for e in range(first, last + 1)
            ],
        })

    ids = [x["id"] for s in sections for x in s["items"]]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate item ids")
    if len(ids) != final:
        raise SystemExit("expected %d rows, built %d" % (final, len(ids)))
    # counts below are of aired episodes; the announced ones are rows, not
    # episodes yet
    total = LAST

    # the two lengths every source agrees on, as a check on the boundaries
    by = {s["title"]: len(s["items"]) for s in sections}
    by["Wano Country"] = sum(v for k, v in by.items() if k.startswith("Wano: "))
    for arc, want in (("Wano Country", 196), ("Dressrosa", 118)):
        if by[arc] != want:
            raise SystemExit("%s is %d episodes, expected %d" % (arc, by[arc], want))

    filler_eps = sum(len(s["items"]) for s, a in zip(sections, ARCS) if a[3])

    # the "Between runs." note speaks of one announced episode due in a bare
    # year; anything else needs that note rewritten, not filled in
    if len(NEXT) != 1 or not NEXT[LAST + 1].isdigit():
        raise SystemExit("NEXT changed shape: rewrite the 'Between runs.' note")

    prop = {
        "slug": SLUG,
        "title": "One Piece",
        "kind": "anime",
        "popularity": 91,
        "year": "1999–",
        # "aired": the card prints the row count, which includes NEXT, beside it
        "blurb": "%d episodes aired, %d arcs, the filler is optional." % (total, len(sections)),
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": "#B8531F",
        "accentDark": "#E8904A",
        "tiers": False,
        "notes": [
            ["Filler.", "Whole filler arcs get their own section and every episode "
                        "in them is flagged optional — %d of %d. Skipping all of it "
                        "costs you nothing." % (filler_eps, total)],
            ["Arc boundaries.", "A few filler arcs sit inside a canon one rather "
                                "than between two, so they are folded into the arc "
                                "around them. A strip cannot show a gap, and every "
                                "watch order presents them that way regardless."],
            # Since April 2026 the show airs in runs, at most 26 episodes a
            # year (One Piece (1999 TV series), Broadcast). Nothing aired after
            # 1180. After it aired, the official X account said the next
            # episode airs in 2027, no exact date yet (Oricon News 2482880,
            # 27 Sep 2026; ja.wikipedia "ONE PIECE (アニメ)"), as of 11 Nov 2026.
            # The year and the one listed episode come from NEXT, checked
            # above the prop.
            ["Between runs.", "The newest out is episode %d, aired %s. The "
                              "show now airs at most 26 episodes a year; the "
                              "next are due in %s, with no exact date yet, so "
                              "%d is listed as not out yet; rerun the "
                              "generator to extend it."
                              % (LAST, LAST_AIRED, NEXT[LAST + 1], LAST + 1)],
            # Unheaded, last: the colophon (CLU-275 rule 6). The two arc
            # lengths named here are the assertions run above.
            "Arc names, boundaries and the filler marks from Anime Filler "
            "Guide's One Piece list; the boundaries are held to the two arc "
            "lengths every source quotes, Wano at 196 episodes and Dressrosa "
            "at 118, and the generator fails rather than ship a list that "
            "disagrees with either.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d arcs, %d episodes, %d filler" % (len(sections), total, filler_eps))
    saga = None
    for (s, a) in zip(sections, ARCS):
        if a[0] != saga:
            saga = a[0]
            print("  %s" % saga)
        print("     %-22s %4d  %s" % (s["title"], len(s["items"]),
                                      "filler" if a[3] else ""))


if __name__ == "__main__":
    main()
