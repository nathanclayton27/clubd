#!/usr/bin/env python3
"""Generate properties/nicolas-cage.json.

    python3 tools/make_nicolas_cage.py

Nicolas Cage's film roles in release order, one row per film, from
Wikipedia's Nicolas Cage filmography film table, runtimes from Wikidata with
the film articles' own infoboxes filling the gaps. Same shape as the Robin
Williams list: era sections, the table's factual notes riding along, weights
in hours.

Out, with reasons: the five producer-only rows (Bel Air, Shadow of the
Vampire, The Life of David Gale, A Thousand Words, Can't Stand Losing You —
no acting role), everything the article still dates TBA (The Prince, Parish,
C.L.A.Y.), and the television and video-game work.

In, though not out yet: a film the source gives a release date — even a bare
year — is a row under the house rule for dated unreleased work. Its data
entry carries `due` (an ISO date or a year), `runtime: null` and a pinned
`id`, so a slipped date can never move the row; it weighs nothing and says
so on the row. As of the 2026-11-11 refresh: Best Pancakes in the County
(20 Nov 2026), Fortitude (2026), Lords of War (22 Jan 2027) and Spider-Man:
Beyond the Spider-Verse (18 Jun 2027), each date from the film's own
article. The filmography still tags all of them, and Madden, {{pending
film}}; Madden opened in select US theatres on 11 Nov 2026, so it is a
normal row, its 110 minutes from its infobox (Wikidata has no runtime yet).
When one opens, drop `due` and `id` and give it a runtime. The table's notes
cell for Beyond the Spider-Verse holds only its production status, so the
voice-role flag comes from the film's article (`articlenote`).
"""
import datetime
import json
import pathlib

SLUG = "nicolas-cage"

ERAS = [
    ("coppola", "Nicolas Coppola", 1982, 1989,
     "Billed as Nicolas Coppola in Fast Times, then renamed to escape the "
     "uncle — the decade runs from bit parts through Birdy, Raising "
     "Arizona and Moonstruck to eating a cockroach in Vampire's Kiss."),
    ("leading", "Leading man", 1990, 1996,
     "Wild at Heart to The Rock: the Elvis fixation, the screwball years, "
     "and Leaving Las Vegas — the shoestring drama that won him the "
     "Oscar."),
    ("action", "The action star", 1997, 2004,
     "Con Air, Face/Off, the Bruckheimer money years — with 8MM, Bringing "
     "Out the Dead and Adaptation folded between explosions, and National "
     "Treasure to close."),
    ("excess", "Ghost riders", 2005, 2012,
     "Lord of War through the second Ghost Rider: the era of the burning "
     "skull, the bees, the bad lieutenant, and Kick-Ass — committed to "
     "all of it equally."),
    ("vod", "The video-on-demand years", 2013, 2018,
     "The tax-debt stretch: a dozen thrillers that went straight to "
     "video, with Joe, The Trust and finally Mandy scattered through them "
     "like signal in the noise."),
    ("renaissance", "The renaissance", 2019, 2027,
     "Color Out of Space, Pig, playing himself in The Unbearable Weight "
     "of Massive Talent, Dream Scenario, Longlegs — the comeback that "
     "turned out to be the whole point."),
]

# The table's display text says "Colour"; the film's own article - which
# the same cell links to - is titled Color Out of Space. The article wins.
TITLE = {"Colour Out of Space": "Color Out of Space"}

# Which table notes ride along - factual flags only, same test as the
# Robin Williams list plus this filmography's own recurring markers.
KEYS = ("credited as", "voice", "cameo", "uncredited", "documentary",
        "short film", "television", "direct-to-video", "video on demand",
        "also director")


MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")
WORDS = ("zero", "one", "two", "three", "four", "five", "six", "seven",
         "eight", "nine", "ten", "eleven", "twelve")


def word(n):
    return WORDS[n] if n < len(WORDS) else str(n)


def due_text(due):
    """'2026' -> 'dated 2026'; '2026-11-20' -> 'due 20 November 2026'."""
    if len(due) == 4:
        return "dated %s" % due
    d = datetime.date.fromisoformat(due)
    return "due %d %s %d" % (d.day, MONTHS[d.month - 1], d.year)


def slug(t):
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def main():
    data = pathlib.Path(__file__).resolve().parent / "data"
    films = json.loads((data / "nicolas-cage.json").read_text(encoding="utf-8"))
    assert len(films) == 118, len(films)
    for f in films:
        f["t"] = TITLE.get(f["t"], f["t"])
    films.sort(key=lambda f: (f["year"], f["t"]))
    out_now = [f for f in films if not f.get("due")]
    ahead = [f for f in films if f.get("due")]
    assert all(f.get("runtime") for f in out_now), \
        [f["t"] for f in out_now if not f.get("runtime")]
    assert all(f.get("runtime") is None and f.get("id") for f in ahead), \
        [f["t"] for f in ahead]
    assert len(out_now) == 114 and len(ahead) == 4, (len(out_now), len(ahead))
    from_wd = [f for f in out_now if not f.get("runtime_from")]

    sections = []
    for key, title, lo, hi, intro in ERAS:
        got = [f for f in films if lo <= f["year"] <= hi]
        assert got, title
        items = []
        for f in got:
            bits = []
            for raw in (f.get("tablenote"), f.get("articlenote")):
                note = (raw or "").strip()
                if note and any(k in note.lower() for k in KEYS):
                    bits.append(note.rstrip("."))
            if f.get("due"):
                bits.append("Not out yet — %s, and the bar stays empty "
                            "until it opens" % due_text(f["due"]))
            it = {"id": f.get("id") or "nc-%d-%s" % (f["year"], slug(f["t"])),
                  "t": f["t"], "n": str(f["year"]),
                  "w": round(f["runtime"] / 60.0, 2) if f.get("runtime") else 0}
            if bits:
                it["note"] = " · ".join(bits)
            items.append(it)
        sec = {"id": key, "title": title,
               "sub": "%d–%d · %d films · %d hours"
                      % (got[0]["year"], got[-1]["year"], len(got),
                         round(sum(f["runtime"] or 0 for f in got) / 60.0)),
               "intro": intro, "items": items}
        if key == "coppola":
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(films) == 118, (len(ids), len(films))
    for s in sections:
        assert all(a["n"] <= b["n"] for a, b in zip(s["items"], s["items"][1:])), \
            "%s is out of year order" % s["title"]

    hours = sum(x["w"] for s in sections for x in s["items"])

    prop = {
        "slug": SLUG,
        "title": "Nicolas Cage",
        "subtitle": "the film roles, in release order",
        "kind": "films",
        "popularity": 65,
        "year": "%d–%d" % (films[0]["year"], films[-1]["year"]),
        "blurb": "%d films across five decades — about %d hours, from "
                 "Nicolas Coppola's bit parts to the renaissance."
                 % (len(films), round(hours)),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": "#B8860B",
        "accentDark": "#F2B845",
        "tiers": False,
        "notes": [
            ["Acting roles only.", "The five films he only produced, "
             "everything still marked TBA, and the television "
             "and video-game work are not here. The table's own factual "
             "notes — a name change, a voice role, a video-on-demand "
             "release — ride along where they help."],
            ["Bar widths are runtimes.", "From Wikidata for %d of the "
             "%d films out so far; the film articles' own infoboxes fill "
             "the other %s. The %s with a release date still ahead weigh "
             "nothing until they open."
             % (len(from_wd), len(out_now), word(len(out_now) - len(from_wd)),
                word(len(ahead)))],
            "Filmography from Wikipedia's Nicolas Cage filmography; "
            "runtimes from Wikidata and the film articles' infoboxes.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")
    print("wrote %s.json — %d films, %.1f hours" % (SLUG, len(ids), hours))
    for s in sections:
        print("   %-28s %3d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
