#!/usr/bin/env python3
"""Generate properties/hitchcock.json.

    python3 tools/make_hitchcock.py

The fifty-four features Alfred Hitchcock directed, in release order, weighted
by runtime. The inclusion rule is decided in scratch/hitchcock/fetch_data.py,
which builds tools/data/hitchcock.json from the Wikipedia filmography's
"As director" table and Wikidata: features only, so the unfinished Number 13
and the four shorts (An Elastic Affair, The Fighting Generation, Bon Voyage,
Aventure Malgache) never reach this script.

Two rows are special. The Mountain Eagle (1926) is lost — it stays on the
list, marked as such, and weighs zero no matter what runtime the records
claim, because there is nothing to watch. Mary (1931) is the German-language
version of Murder! shot in parallel with a German cast, so it rides along as
an optional row rather than counting among the films proper.

Weights are Wikidata runtimes (P2047) in hours; release dates are P577. Eras
are a judgment call, stated in each intro, and split on first films rather
than years because 1929 holds both the last silent and the first sound
picture: British silents run to The Manxman, British sound starts with
Blackmail, Hollywood with Rebecca, and the late run with Torn Curtain.
"""
import json
import pathlib
import unicodedata

SLUG = "hitchcock"

# each era begins at a named film; 1929 splits mid-year at Blackmail
ERAS = [
    ("silents", "British silents", "The Pleasure Garden",
     "Nine silent features from the British studios, an art director's "
     "apprenticeship turning into a director's career. One of them, The "
     "Mountain Eagle, no longer exists."),
    ("sound", "British sound", "Blackmail",
     "Blackmail arrives in silent and sound versions at once, and the run "
     "that follows — The 39 Steps, Sabotage, The Lady Vanishes — is what "
     "gets him invited to Hollywood."),
    ("hollywood", "Hollywood", "Rebecca",
     "Twenty-six films in twenty-five years, Rebecca to Marnie — the "
     "Selznick pictures first, then the fifties run where most of the "
     "famous ones live."),
    ("late", "The late run", "Torn Curtain",
     "Four films to finish: two Cold War thrillers, a return to London, and "
     "a last one back in California."),
]

NOTE = {
    "The Pleasure Garden": "His directorial debut",
    "The Mountain Eagle":
        "Lost — no print is known to survive, so it weighs nothing here",
    "The Lodger: A Story of the London Fog":
        "His first hit, and the first of the cameo appearances",
    "Blackmail":
        "Released in both silent and sound versions — his first sound film",
    "Mary":
        "The German-language Murder!, shot in parallel with a German cast — "
        "an alternate version, so it is optional here",
    "Rebecca": "His first Hollywood picture, and a Best Picture winner",
    "Rope": "His first film in Technicolor",
    "Dial M for Murder": "Filmed in 3D",
    "The Man Who Knew Too Much (1956)":
        "A remake of his own 1934 film",
    "Family Plot": "His last film",
}


# Curly punctuation, straightened to the ASCII this fold already handles.
# CLU-430: `encode("ascii", "ignore")` DROPS a curly apostrophe and keeps a
# straight one as a dash, so `Child’s Play` folds to `childs-play` while
# `Child's Play` folds to `child-s-play`. An id is somebody’s tick, so two
# spellings of one title must never reach two ids. Straightening is the
# correction THIS direction needs — the opposite of the folds that drop the
# straight form — and it leaves every id this list has shipped where it is.
STRAIGHTEN = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'})


def slug(t):
    t = unicodedata.normalize("NFKD", t.translate(STRAIGHTEN))
    t = t.encode("ascii", "ignore").decode()
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def main():
    data = pathlib.Path(__file__).resolve().parent / "data"
    cached = json.loads((data / "hitchcock.json").read_text(encoding="utf-8"))
    films = [f for f in cached if f["kind"] == "feature"]

    # the data file keeps the table's order — release order within each year
    assert all(a["year"] <= b["year"] for a, b in zip(films, films[1:])), \
        "data file is out of year order"
    assert films[0]["title"] == "The Pleasure Garden"
    assert films[-1]["title"] == "Family Plot"

    no_runtime = [f["title"] for f in films
                  if not f["runtime"] and not f.get("lost")]

    # split the release-order list at each era's named first film
    idx = []
    for key, title, first, intro in ERAS:
        matches = [i for i, f in enumerate(films) if f["title"] == first]
        assert len(matches) == 1, (first, matches)
        idx.append(matches[0])
    assert idx[0] == 0 and idx == sorted(idx), idx
    idx.append(len(films))

    def item(f):
        # a 1956 remake shares its title with the 1934 original
        key = f["title"]
        if sum(1 for x in films if x["title"] == key) > 1:
            key = "%s (%d)" % (f["title"], f["year"])
        it = {"id": "hit-%d-%s" % (f["year"], slug(f["title"])),
              "t": f["title"], "n": str(f["year"])}
        if f.get("lost"):
            it["w"] = 0  # nothing survives to watch, whatever the records say
        elif not f["runtime"]:
            it["w"] = 0
            it["note"] = "No runtime on record — it weighs nothing here"
        else:
            it["w"] = round(f["runtime"] / 60.0, 2)
        if f.get("alt_of"):
            it["opt"] = 1
        if key in NOTE:
            it["note"] = NOTE[key]
        return it

    sections = []
    for (key, title, first, intro), lo, hi in zip(ERAS, idx, idx[1:]):
        got = films[lo:hi]
        assert got, title
        items = [item(f) for f in got]
        hours = sum(x["w"] for x in items)
        sec = {"id": key, "title": title,
               "sub": "%d–%d · %d films · %d hours"
                      % (got[0]["year"], got[-1]["year"], len(got),
                         round(hours)),
               "intro": intro, "items": items}
        if key == "silents":
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(films) == 54, (len(ids), len(films))
    assert all(i.replace("-", "").replace("_", "").isalnum()
               and i[0].isalpha() and i.isascii() for i in ids), ids
    for s in sections:
        assert all(a["n"] <= b["n"] for a, b in zip(s["items"], s["items"][1:])), \
            "%s is out of year order" % s["title"]
    lost = [x for s in sections for x in s["items"] if x["w"] == 0]
    assert [x["t"] for x in lost] == ["The Mountain Eagle"], lost

    hours = sum(x["w"] for s in sections for x in s["items"])

    prop = {
        "slug": SLUG,
        "title": "Alfred Hitchcock",
        "subtitle": "the features he directed, silents through Family Plot",
        "kind": "films",
        "popularity": 77,
        # Not a story, so not a sequence: the order these came out in
        # is a fact about the maker, not an instruction to the viewer
        # (Nathan, CLU-372). Prerequisites, where any exist, live in
        # tools/data/sequences.json and are enforced separately.
        "random": True,
        "year": "1925–1976",
        "blurb": "Every feature he directed, The Pleasure Garden through "
                 "Family Plot — %d films, about %d hours."
                 % (len(films), round(hours)),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": "#3A3A45",
        "accentDark": "#B8B8D0",
        "tiers": False,
        "notes": [
            ["Directed features only.", "The filmography's director table "
             "also holds an unfinished first attempt and four shorts, and "
             "none of them are here: Number 13 was abandoned mid-shoot and "
             "is lost, and An Elastic Affair, The Fighting Generation, Bon "
             "Voyage and Aventure Malgache are shorts, not features. "
             "Everything from The Pleasure Garden through Family Plot is."],
            ["The Mountain Eagle is lost.", "No print is known to survive. "
             "It stays on the list as the one film you cannot watch, and it "
             "weighs nothing in the totals."],
            ["Mary is an alternate version.", "The German-language Murder!, "
             "shot in parallel with a German cast — kept as an optional row "
             "rather than counted among the films proper."],
            ["Bar widths are runtimes.", "From Wikidata, in hours — about "
             "%d in all. The lost film is zeroed no matter what the records "
             "say; every other film carries its real Wikidata runtime, and "
             "a film without one would weigh nothing and say so on its row."
             % round(hours)],
            "Filmography from Wikipedia's Alfred Hitchcock filmography; "
            "runtimes and release dates from Wikidata.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d films (1 lost at weight 0, Mary optional), %.1f hours"
          % (len(films), hours))
    if no_runtime:
        print("  MISSING RUNTIMES (weighted 0, noted): %s"
              % ", ".join(no_runtime))
    else:
        print("  no missing runtimes beyond the lost film")
    for s in sections:
        print("   %-16s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
