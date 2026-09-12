#!/usr/bin/env python3
"""Generate properties/fma-brotherhood.json.

One-off. Kept so the arc boundaries and dates can be corrected in one place and
regenerated, rather than hand-edited across 64 items.

    python3 tools/make_fmab.py
"""
import json
import pathlib

# (section id, title, first episode, last episode, week)
#
# The schedule has no dates of its own — it is a shape, one week per chapter,
# and a group anchors it to whatever day they start. The club's own run began on
# 15 July 2026; any group can reproduce that by starting there.
#
# The calendar gives chapters 1 and 2 a single fortnight, but the real split is
# 1–12 and 13–20, so they get a week each.
ARCS = [
    ("ch1", "Chapter 1: Hunt for the Stone",       1, 12, 0),
    ("ch2", "Chapter 2: Shadow of the Homunculi", 13, 20, 1),
    ("ch3", "Chapter 3: Sins of the Father",      21, 30, 2),
    ("ch4", "Chapter 4: The Wall of Briggs",      31, 43, 3),
    ("ch5", "Chapter 5: The Uprising",            44, 53, 4),
    ("ch6", "Chapter 6: The Promised Day",        54, 64, 5),
]


# English episode titles, 1-64. Cross-checked between the Wikipedia episode
# list (1-58) and epguides (55-64); the overlap agrees.
TITLES = [
    "Fullmetal Alchemist", "The First Day", "City of Heresy",
    "An Alchemist's Anguish", "Rain of Sorrows", "Road of Hope",
    "Hidden Truths", "The Fifth Laboratory", "Created Feelings",
    "Separate Destinations", "Miracle at Rush Valley", "One is All, All is One",
    "Beasts of Dublith", "Those Who Lurk Underground", "Envoy from the East",
    "Footsteps of a Comrade-in-Arms", "Cold Flame",
    "The Arrogant Palm of a Small Human", "Death of the Undying",
    "Father Before the Grave", "Advance of the Fool", "Backs in the Distance",
    "Girl on the Battlefield", "Inside the Belly", "Doorway of Darkness",
    "Reunion", "Interlude Party", "Father", "Struggle of the Fool",
    "The Ishvalan War of Extermination", "The 520 Cens Promise",
    "The Führer's Son", "The Northern Wall of Briggs", "Ice Queen",
    "The Shape of This Country", "Family Portrait", "The First Homunculus",
    "Conflict at Baschool", "Daydream", "Homunculus (The Dwarf in the Flask)",
    "The Abyss", "Signs of a Counteroffensive", "Bite of the Ant",
    "Revving at Full Throttle", "The Promised Day", "Looming Shadows",
    "Emissary of Darkness", "The Oath in the Tunnel", "Filial Affection",
    "Upheaval in Central", "The Immortal Legion", "Combined Strength",
    "Flame of Vengeance", "Beyond the Inferno", "The Adults' Way of Life",
    "The Return of the Führer", "Eternal Leave", "Sacrifices", "Lost Light",
    "Eye of Heaven, Gateway of Earth", "He Who Would Swallow God",
    "A Fierce Counterattack", "The Other Side of the Gateway", "Journey's End",
]
assert len(TITLES) == 64, "expected 64 titles, have %d" % len(TITLES)



def main():
    sections = []
    windows = []

    for sid, title, first, last, week in ARCS:
        sections.append({
            "id": sid,
            "title": title,
            "sub": "episodes %d–%d · week %d" % (first, last, week + 1),
            "items": [
                {"id": "fmab-%d" % n, "t": TITLES[n - 1], "n": str(n)}
                for n in range(first, last + 1)
            ],
        })
        windows.append({
            "offset": week * 7,       # days from whenever the group starts
            "days": 7,
            "through": last,          # cumulative episodes due by end of window
            "label": title,
        })

    total = sum(len(s["items"]) for s in sections)
    assert total == 64, "expected 64 episodes, built %d" % total
    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate item ids"

    prop = {
        "slug": "fma-brotherhood",
        "title": "Fullmetal Alchemist: Brotherhood",
        "kind": "anime",
        "popularity": 83,
        "year": "2009–2010",
        "blurb": "64 episodes across six arcs.",
        # Shown only to people in the matching group. This is presentation, not
        # secrecy — this file is served publicly, so anyone who opens it can
        # read what is below. Move it to the database if it ever needs hiding.
        "forGroup": {
            "75PSPM": {
                "blurb": "HD DVD Anime Club, Round 4. 64 episodes across six "
                         "arcs, on a fixed club schedule from 15 July to "
                         "25 August 2026.",
                "rulesTitle": "FMA Club bylaws",
            }
        },
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        # shows read better as "12  One is All, All is One" than the other way
        "itemOrder": "number-first",
        "accent": "#B0472E",
        "accentDark": "#E8874F",
        "tiers": False,
        "rules": [
            "Pace yourself — don't watch a whole arc in one day. The windows are "
            "for flexibility, not permission to binge.",
            "Remember to discuss.",
            "Finish an arc before its window is up and the remaining days are yours "
            "off until the next arc begins.",
            "Don't transmute your mom.",
        ],
        "schedule": {"kind": "windows", "windows": windows},
        # Unheaded, last: the colophon. Every list carries one (CLU-275 rule 6).
        # Both halves of the title check are in the comment on TITLES above.
        "notes": [
            "Episode titles cross-checked between Wikipedia's Brotherhood "
            "episode list, which carries 1–58, and epguides, which carries "
            "55–64; the overlap agrees. The six chapters and their episode "
            "spans come from the club calendar rather than from any published "
            "arc division, and the schedule is that calendar's shape — one "
            "week each, with no dates of its own until a group picks a start "
            "date. The calendar gives chapters 1 and 2 a single fortnight; "
            "they are two sections here, split at episode 12.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / "fma-brotherhood.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    # newline="\n" to match .gitattributes; otherwise every rebuild on Windows
    # rewrites all 800 lines as CRLF and the diff is useless
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s" % out.name)
    print("  %d episodes, %d arcs" % (total, len(sections)))
    for w in windows:
        print("  through E%-2d by day %-2d  %s" % (w["through"], w["offset"] + w["days"], w["label"]))


if __name__ == "__main__":
    main()
