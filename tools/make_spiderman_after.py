#!/usr/bin/env python3
"""Generate properties/spider-man-after-civil-war.json.

    python3 tools/make_spiderman_after.py

Picks up at ASM #539, where the Civil War list leaves off, and runs to now.
Tracked issue by issue: an earlier version collapsed each run into a single
entry ("Superior Spider-Man #1–33") which made it impossible to tick off where
you actually got to.

One section per run rather than per era, so each carries its own Marvel series
link — these are eleven different series and a single link would have been
wrong for ten of them.

Back in Black and One More Day finish the story the pre-Civil War list was
telling, so they are tier 1. Superior Spider-Man is tier 2, the one run every
guide singles out. The rest is tier 3: still per issue, but a set of
recommendations rather than a list to complete, and outside the finish date.
Brand New Day and Big Time list the arcs worth reading rather than every issue
of those runs, which is how the source frames them. The two Ultimate Spider-Man
runs used to live here and are now their own list — different continuity, and
neither one needs anything on this page.

CLU-546: selective is not the same as absent, and both named sections were
getting that wrong at the one arc that gives them their name.

  * The Big Time section held #666-673, #682-687 and #698-700 — Spider-Island,
    Ends of the Earth and Dying Wish — and not one issue of Big Time itself.
    Wikipedia's "Big Time (comics)" infobox puts the arc at ASM #648-656,
    November 2010 to March 2011, and names its three parts in the prose: "Kill
    to be You" #648-651, "Revenge of the Spider-Slayer" #652-654 and "No One
    Dies" #655-656. All nine are added at the head of the section. The `sub`
    already said 2010-13 while the earliest issue in it was from 2011.
  * Brand New Day shipped #546, #547 and #548. Wikipedia's "Brand New Day
    (comics)" infobox puts the storyline at ASM #546-564 and the prose is
    explicit that "the banner only runs across the front covers of #546-564" —
    nineteen issues, of which three were here. Every other arc in that section
    ships complete, so the one the section is named after now does too.

Neither fix renames anything: #549-564 and #648-656 had no rows in this file at
all, so the id set only grew. The other arcs the source names and this list
still does not carry are recorded on the card rather than guessed at here.

Notes say what an entry is, never what happens in it.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from spiderman_data import (S_V2, S_SUP, S_2014, S_2015, S_2018, S_2022,
                            S_2025, S_LIFE, S_BLUE, asm, item)

SLUG = "spider-man-after-civil-war"

# arc markers for the ASM issues after One More Day; everything else is
# deliberately unannotated
ARC = {
    546: "“Brand New Day” begins — Slott and McNiven, and the banner runs "
         "to #564",
    564: "The last issue to carry the Brand New Day banner",
    568: "“New Ways to Die” begins — Slott and John Romita Jr.",
    595: "“American Son” begins",
    600: "Anniversary issue",
    612: "“The Gauntlet” begins — a systematic reintroduction of the rogues",
    630: "“Shed” begins — Zeb Wells and Chris Bachalo on the Lizard",
    634: "“Grim Hunt” begins — the sequel to Kraven's Last Hunt, 23 years on",
    642: "“Origin of the Species” begins",
    648: "“Big Time” begins — “Kill to be You”, Slott now writing alone, with "
         "Humberto Ramos",
    652: "“Revenge of the Spider-Slayer” begins",
    655: "“No One Dies” begins",
    666: "“Spider-Island” begins — all of Manhattan gets spider-powers",
    682: "“Ends of the Earth” begins — Doc Ock",
    698: "“Dying Wish” begins — the end of Slott's first era",
}
ARC_STAR = {568: 1, 630: 1, 634: 1, 666: 1, 698: 2}


def later(n):
    """An ASM issue after One More Day, carrying an arc marker if it starts one."""
    x = asm(n)
    if n in ARC:
        x["note"] = ARC[n]
    if n in ARC_STAR:
        x["star"] = ARC_STAR[n]
    x.pop("w", None)
    return x


def run(prefix, title, nums, notes=None, stars=None):
    """One issue per number, for a series tracked on its own numbering."""
    notes, stars, out = notes or {}, stars or {}, []
    for n in nums:
        x = {"id": "%s-%d" % (prefix, n), "t": title, "n": "#%d" % n}
        if n in notes:
            x["note"] = notes[n]
        if n in stars:
            x["star"] = stars[n]
        out.append(x)
    return out


def plain(n):
    x = asm(n)
    x.pop("w", None)
    return x


def cross(key, title, num, note=""):
    """A chapter published outside ASM. No weight — everything here is one issue."""
    x = item(key, title, num, note)
    x.pop("w", None)
    return x


BND = (list(range(546, 565)) + list(range(568, 574))
       + list(range(595, 600)) + [600]
       + list(range(612, 624)) + list(range(630, 634)) + list(range(634, 638))
       + list(range(642, 648)))
BIGTIME = (list(range(648, 657)) + list(range(666, 674))
           + list(range(682, 688)) + [698, 699, 700])

SECTIONS = [
    {
        "id": "backinblack", "tier": 1, "title": "Back in Black",
        "sub": "#539–543 · 2007 · straight out of Civil War",
        "open": True,
        "links": [{"label": "The series", "url": S_V2}],
        "intro": "Reads directly on from the last Civil War issue. If you have "
                 "not read that list, start there — this arc is a reaction to it "
                 "from the first page.",
        "items": [plain(n) for n in range(539, 544)],
    },
    {
        "id": "omd", "tier": 1, "title": "One More Day",
        "sub": "2007 · four issues, in exactly this order",
        "links": [{"label": "The series", "url": S_V2}],
        "intro": "The most argued-about editorial decision in the character's "
                 "history, and the line the classic run ends on. Best read in one "
                 "sitting — and plenty of readers stop here on purpose.",
        "items": [
            plain(544),
            cross("omd-2", "Friendly Neighborhood Spider-Man", "#24",
                  "One More Day, part 2"),
            cross("omd-3", "Sensational Spider-Man", "#41",
                  "One More Day, part 3"),
            plain(545),
        ],
    },
    {
        "id": "bnd", "tier": 3, "title": "Brand New Day",
        "sub": "2008–10 · the arcs worth reading, issue by issue",
        "links": [{"label": "The series", "url": S_V2}],
        "intro": "From here on this is a set of recommendations rather than a "
                 "list to finish, so these are the arcs the source picks out of a "
                 "hundred-issue stretch — not every issue of it. Three issues a "
                 "month, rotating writers, Peter single and broke and back in "
                 "Queens. Better than its reputation.",
        "items": [later(n) for n in BND],
    },
    {
        "id": "bigtime", "tier": 3, "title": "Dan Slott solo: Big Time",
        "sub": "2010–13 · the arcs worth reading, issue by issue",
        "links": [{"label": "The series", "url": S_V2}],
        "intro": "Peter takes a job at Horizon Labs. Brighter, gadget-heavy, "
                 "more optimistic.",
        "items": [later(n) for n in BIGTIME],
    },
    {
        "id": "superior", "tier": 2, "title": "Superior Spider-Man",
        "sub": "#1–33 · 2013–14 · if you read one thing after One More Day",
        "links": [{"label": "The series", "url": S_SUP}],
        "intro": "The most contentious relaunch in the character's history — "
                 "greeted with fury on announcement, and now widely considered "
                 "the best Spider-Man run of the century. Thirty-three issues, "
                 "finished, and it goes somewhere the main title never could.",
        "items": run("sup", "Superior Spider-Man", range(1, 34), stars={1: 2}),
    },
    {
        "id": "asm2014", "tier": 3, "title": "Amazing Spider-Man (2014)",
        "sub": "#1–18 · Peter returns",
        "links": [{"label": "The series", "url": S_2014}],
        "items": run("asm14", "Amazing Spider-Man (2014)", range(1, 19),
                     notes={9: "“Spider-Verse” begins — the crossover the animated "
                               "films drew from"}, stars={9: 1}),
    },
    {
        "id": "asm2015", "tier": 3, "title": "Amazing Spider-Man (2015–18)",
        "sub": "#1–32, then #789–801 · Parker Industries",
        "links": [{"label": "The series", "url": S_2015}],
        "intro": "Peter as globe-trotting CEO. Divisive, and the numbering "
                 "changes partway when the title returns to its legacy count.",
        "items": (run("asm15", "Amazing Spider-Man (2015)", range(1, 33))
                  + run("asm15", "Amazing Spider-Man", range(789, 802),
                        notes={789: "Legacy numbering resumes",
                               801: "Slott's finale, and genuinely lovely"},
                        stars={801: 1})),
    },
    {
        "id": "asm2018", "tier": 3, "title": "Amazing Spider-Man (2018–22)",
        "sub": "#1–74 · Nick Spencer",
        "links": [{"label": "The series", "url": S_2018}],
        "intro": "The best-regarded modern run on the main title, and it spends "
                 "its full length building toward something.",
        "items": run("asm18", "Amazing Spider-Man (2018)", range(1, 75),
                     notes={16: "“Hunted” begins", 50: "“Last Remains” begins"},
                     stars={1: 1, 16: 1, 50: 1}),
    },
    {
        "id": "asm2022", "tier": 3, "title": "Amazing Spider-Man (2022–25)",
        "sub": "#1–70 · Zeb Wells",
        "links": [{"label": "The series", "url": S_2022}],
        "intro": "The run that broke a lot of people's patience.",
        "items": run("asm22", "Amazing Spider-Man (2022)", range(1, 71)),
    },
    {
        "id": "asm2025", "tier": 3, "title": "Amazing Spider-Man (2025– )",
        "sub": "#1–34 · Joe Kelly and Pepe Larraz · still running",
        "links": [{"label": "The series", "url": S_2025}],
        "intro": "Twice monthly and well received, building to ASM #1000 in "
                 "September 2026. Marvel Unlimited adds issues about three months "
                 "after print, so the last few are not readable there yet.",
        "items": run("asm25", "Amazing Spider-Man (2025)", range(1, 35),
                     stars={1: 1}),
    },
    {
        "id": "lifestory", "tier": 3, "title": "Spider-Man: Life Story",
        "sub": "#1–6 · 2019 · outside continuity",
        "links": [{"label": "The series", "url": S_LIFE}],
        "intro": "Zdarsky and Bagley. One issue per decade, Peter ageing in real "
                 "time from 1962. Self-contained, and arguably the finest "
                 "Spider-Man comic of the last twenty years.",
        "items": run("ls", "Spider-Man: Life Story", range(1, 7), stars={1: 2}),
    },
    {
        "id": "blue", "tier": 3, "title": "Spider-Man: Blue",
        "sub": "#1–6 · 2002 · outside continuity",
        "links": [{"label": "The series", "url": S_BLUE}],
        "intro": "Loeb and Sale. A good decompression read after the classic run.",
        "items": run("blue", "Spider-Man: Blue", range(1, 7)),
    },
]


def main():
    ids = [x["id"] for s in SECTIONS for x in s["items"]]
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        raise SystemExit("duplicate item ids: %s" % dupes[:10])
    total = len(ids)

    # everything is a single issue now, so nothing should carry a weight
    assert not any("w" in x for s in SECTIONS for x in s["items"]), "stray weight"
    # nothing here may overlap the Civil War list, which ends at ASM #538
    nums = [int(i[4:]) for i in ids if i.startswith("asm-") and i[4:].isdigit()]
    assert min(nums) == 539, min(nums)
    # every section must carry a series link
    unlinked = [s["title"] for s in SECTIONS if not s.get("links")]
    assert not unlinked, unlinked

    tiers = {1: 0, 2: 0, 3: 0}
    for s in SECTIONS:
        tiers[s["tier"]] += len(s["items"])
    assert tiers[1] == 9, tiers[1]
    assert tiers[2] == 33, tiers[2]

    prop = {
        "slug": SLUG,
        "title": "Spider-Man After Civil War",
        "subtitle": "Back in Black to now",
        "kind": "comics",
        "popularity": 37,
        "year": "2007–",
        "blurb": "The end of the classic run, then eighteen years of "
                 "recommendations — %d issues, tracked one by one." % total,
        "unit": {"one": "issue", "many": "issues"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": "#7A3B5E",
        "accentDark": "#D98BB4",
        "tiers": True,
        "paceTiers": [1, 2],
        "paceLabel": "the modern recommendations",
        "notes": [
            ["Start with the Civil War list.", "Back in Black reads directly on "
             "from the last issue of Civil War. Before that, the whole run from "
             "1962 is in Amazing Spider-Man."],
            ["Tiers.", "1 is Back in Black and One More Day, finishing the story "
             "the earlier lists were telling. 2 is Superior Spider-Man, the one "
             "run every guide singles out. 3 is the rest — recommendations, not a "
             "list to complete, and outside the finish date."],
            ["Brand New Day and Big Time are selective.", "Those two sections "
             "list the arcs worth reading rather than every issue of a "
             "hundred-issue stretch, which is how the source frames them. Every "
             "other section is complete."],
            ["No spoilers.", "The notes say what an entry is, never what happens "
             "in it. The eighteen years covered here are the most contested "
             "period in the character's history and the arguments are easy to "
             "find; none of them are here."],
            "Selections from the checklist written for the group; the annotations "
            "are rewritten from it rather than copied, because that document "
            "spoils freely.",
        ],
        "sections": SECTIONS,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d issues, every section linked" % (len(SECTIONS), total))
    for s in SECTIONS:
        print("   T%d  %-34s %4d issues" % (s["tier"], s["title"][:34], len(s["items"])))


if __name__ == "__main__":
    main()
