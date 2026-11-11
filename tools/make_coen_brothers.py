#!/usr/bin/env python3
"""Generate properties/coen-brothers.json.

    python3 tools/make_coen_brothers.py

The eighteen features Joel and Ethan Coen made together, in release order,
plus the solo films in their own section with a note saying whose each one
is. Joel's Macbeth, Ethan's Jerry Lee Lewis documentary, Drive-Away Dolls
and Honey Don't!, and Joel's Jack of Spades.

Jack of Spades is not out. Both Wikipedia pages date it 2027 (the Jack of
Spades article: Netflix opens it in theatres in fall 2027), so it is a row
under the house rule for dated announced work, with "due" in the data file,
no runtime, w: 0, and a note on the row saying so. Joel directs it alone;
Ethan is one of its four writers, which the row also says. When it opens,
add its Wikidata runtime and drop "due".

Left out, with reasons: their segments of Paris, je t'aime and Chacun son
cinéma (segments, not features), The Naked Man (Ethan co-wrote, didn't
direct), and everything they only wrote or produced for other directors.
"""
import json
import pathlib

SLUG = "coen-brothers"

ERAS = [
    ("indie", "The independents", 1984, 1998,
     "Blood Simple through The Big Lebowski: seven films of murders "
     "misfiring and kidnappings going wrong, with Fargo the point where "
     "the Academy caught up. Ethan went uncredited as co-director until "
     "2004 — they were always both directing."),
    ("studio", "The studio decade", 2000, 2009,
     "O Brother through A Serious Man — three George Clooney pictures, a "
     "black-and-white noir, a Ladykillers remake, and No Country for Old "
     "Men, which won them Best Picture, Best Director and Best Adapted "
     "Screenplay at once."),
    ("late", "Late together", 2010, 2018,
     "A western from the Portis novel, a folk singer going nowhere, old "
     "Hollywood, and an anthology western — the last film they made as a "
     "pair."),
]

WHO_NOTE = {
    "The Tragedy of Macbeth": "Joel, alone",
    "Jerry Lee Lewis: Trouble in Mind": "Ethan, alone · documentary",
    "Drive-Away Dolls": "Ethan, alone · co-written with Tricia Cooke",
    "Honey Don't!": "Ethan, alone · co-written with Tricia Cooke",
    "Jack of Spades": "Joel, alone · co-written with Ethan, Eleanor Catton "
                      "and Conor McPherson",
}

# Appended to an unreleased row's note; "due" comes from the data file.
NOT_OUT = "Not out yet — due %s, and the bar stays empty until it opens"

WORDS = {4: "four", 5: "five", 6: "six", 7: "seven", 18: "eighteen"}


def slug(t):
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def mins(f):
    return f["runtime"] or 0


def item(f, prefix_note=None):
    it = {"id": "cb-%d-%s" % (f["year"], slug(f["t"])),
          "t": f["t"], "n": str(f["year"]),
          "w": round(f["runtime"] / 60.0, 2) if f["runtime"] else 0}
    bits = [b for b in (prefix_note,
                        NOT_OUT % f["due"] if f.get("due") else None) if b]
    if bits:
        it["note"] = " · ".join(bits)
    return it


def main():
    data = pathlib.Path(__file__).resolve().parent / "data"
    films = json.loads((data / "coen-brothers.json").read_text(encoding="utf-8"))
    joint = sorted((f for f in films if f["who"] == "joint"),
                   key=lambda f: (f["year"], f["t"]))
    solo = sorted((f for f in films if f["who"] != "joint"),
                  key=lambda f: (f["year"], f["t"]))
    assert len(joint) == 18, len(joint)
    assert len(solo) == 5, [f["t"] for f in solo]
    # Every film has a runtime, except one that is not out: that one has a
    # source-given "due" and no runtime, never both and never neither.
    assert all(bool(f["runtime"]) != bool(f.get("due")) for f in films), \
        [f["t"] for f in films if bool(f["runtime"]) == bool(f.get("due"))]
    assert not any(f.get("due") for f in joint)
    coming = [f for f in solo if f.get("due")]
    assert set(WHO_NOTE) == {f["t"] for f in solo}, [f["t"] for f in solo]
    for f in solo:
        assert WHO_NOTE[f["t"]].startswith(f["who"]), (f["t"], f["who"])

    sections = []
    for key, title, lo, hi, intro in ERAS:
        got = [f for f in joint if lo <= f["year"] <= hi]
        assert got, title
        sec = {"id": key, "title": title,
               "sub": "%d–%d · %d films · %d hours"
                      % (got[0]["year"], got[-1]["year"], len(got),
                         round(sum(f["runtime"] for f in got) / 60.0)),
               "intro": intro, "items": [item(f) for f in got]}
        if key == "indie":
            sec["open"] = True
        sections.append(sec)
    assert sum(len(s["items"]) for s in sections) == 18

    solo_sub = ("%d–%d · %d films · %d hours"
                % (solo[0]["year"], solo[-1]["year"], len(solo),
                   round(sum(mins(f) for f in solo) / 60.0)))
    if coming:
        solo_sub += " · %d not out yet" % len(coming)
    sections.append({
        "id": "solo", "title": "Solo",
        "sub": solo_sub,
        "intro": "After Buster Scruggs they worked apart for a stretch — "
                 "Joel toward Shakespeare, Ethan toward a Jerry Lee Lewis "
                 "documentary and two lesbian B-movie capers. Each row says "
                 "whose film it is.",
        "items": [item(f, WHO_NOTE[f["t"]]) for f in solo],
    })

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(films) == 23, (len(ids), len(films))
    for s in sections:
        assert all(a["n"] <= b["n"] for a, b in zip(s["items"], s["items"][1:])), \
            "%s is out of year order" % s["title"]

    hours = sum(x["w"] for s in sections for x in s["items"])

    prop = {
        "slug": SLUG,
        "title": "The Coen Brothers",
        "subtitle": "%s together, %s apart" % (WORDS[len(joint)],
                                              WORDS[len(solo)]),
        "kind": "films",
        "popularity": 67,
        # Not a story, so not a sequence: the order these came out in
        # is a fact about the maker, not an instruction to the viewer
        # (Nathan, CLU-372). Prerequisites, where any exist, live in
        # tools/data/sequences.json and are enforced separately.
        "random": True,
        "year": "%d–%d" % (min(f["year"] for f in films),
                           max(f["year"] for f in films)),
        "blurb": "The %s features Joel and Ethan made together, plus "
                 "the %s solo films with a note saying whose — about %d "
                 "hours." % (WORDS[len(joint)], WORDS[len(solo)],
                             round(hours)),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": "#6E5533",
        "accentDark": "#C9A87E",
        "tiers": False,
        "notes": [
            ["Credits were odd for twenty years.", "Until The Ladykillers, "
             "Joel alone took the directing credit and Ethan the producing "
             "credit, and they edited under the shared pseudonym Roderick "
             "Jaynes. The filmography credits them jointly on all eighteen; "
             "so does this list."],
            ["What isn't here.", "Their segments of the anthology films "
             "Paris, je t'aime and Chacun son cinéma, The Naked Man (Ethan "
             "co-wrote it, nobody named Coen directed it), and the scripts "
             "and producing jobs for other directors."],
            ["Bar widths are runtimes.", "From Wikidata, in hours, for the "
             "%d films that are out." % (len(films) - len(coming))],
            "Filmography from Wikipedia's Coen brothers filmography; "
            "runtimes from Wikidata.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")
    print("wrote %s.json — %d rows, %.1f hours" % (SLUG, len(ids), hours))
    for s in sections:
        print("   %-18s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
