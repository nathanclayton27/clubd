#!/usr/bin/env python3
"""Generate properties/kurosawa.json.

    python3 tools/make_kurosawa.py

The thirty features Akira Kurosawa directed, in release order, weighted by
runtime. The inclusion rule is decided in scratch/kurosawa/fetch_data.py,
which builds tools/data/kurosawa.json from Wikipedia's "List of works by
Akira Kurosawa" (there is no page titled "Akira Kurosawa filmography") and
Wikidata: the director table's one co-direction, Those Who Make Tomorrow
(1946, shared with Hideo Sekigawa and Kajiro Yamamoto), is flagged in the
cache and left out here — the same rule that keeps Spielberg's Twilight Zone
segment off his list.

Weights are Wikidata runtimes (P2047) in hours; release dates are P577. Eras
are a judgment call, stated in each intro: the wartime start ends when the
Mifune partnership begins with Drunken Angel (1948), the Mifune years end
with Red Beard (1965), and everything after the five-year silence that
followed is the colour late period.
"""
import json
import pathlib
import unicodedata

SLUG = "kurosawa"

ERAS = [
    ("wartime", "The wartime start", 0, 1947,
     "Six films made inside the war and just after it: two judo pictures, a "
     "home-front film shot for the war effort, and — once the censors "
     "changed from Japanese to American — the first films about the country "
     "rebuilding."),
    ("mifune", "The Mifune years", 1948, 1965,
     "Seventeen films in eighteen years, sixteen of them with Toshiro Mifune "
     "— from Drunken Angel, where the partnership starts, to Red Beard, "
     "where it ends."),
    ("colour", "The colour late period", 1966, 9999,
     "Seven films in twenty-three years, all in colour, made the hard way — "
     "a Soviet co-production, epics financed from abroad, and three quiet "
     "last films."),
]

NOTE = {
    "Sanshiro Sugata":
        "His first feature — what survives is the reissue cut, trimmed by "
        "the wartime censors",
    "The Men Who Tread on the Tiger's Tail":
        "Held from release by the occupation until 1952",
    "Dodes'ka-den": "His first film in colour",
    "Dersu Uzala":
        "A Soviet co-production in Russian — the only film he made in a "
        "language other than Japanese",
    "Dreams": "Also released as Akira Kurosawa's Dreams",
    "Madadayo": "His thirtieth and last film",
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
    films = json.loads((data / "kurosawa.json").read_text(encoding="utf-8"))
    films = [f for f in films if not f.get("co_directed")]

    # the data file keeps the table's order — release order within each year
    assert all(a["year"] <= b["year"] for a, b in zip(films, films[1:])), \
        "data file is out of year order"
    missing = [f["title"] for f in films if not f["runtime"]]
    assert not missing, "films with no Wikidata runtime: %s" % missing

    sections = []
    for key, title, lo, hi, intro in ERAS:
        got = [f for f in films if lo <= f["year"] <= hi]
        assert got, title
        items = []
        for f in got:
            items.append({
                "id": "kur-%d-%s" % (f["year"], slug(f["title"])),
                "t": f["title"], "n": str(f["year"]),
                "w": round(f["runtime"] / 60.0, 2),
                **({"note": NOTE[f["title"]]} if f["title"] in NOTE else {}),
            })
        sec = {"id": key, "title": title,
               "sub": "%d–%d · %d films · %d hours"
                      % (got[0]["year"], got[-1]["year"], len(got),
                         round(sum(f["runtime"] for f in got) / 60.0)),
               "intro": intro, "items": items}
        if key == "wartime":
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(films) == 30, (len(ids), len(films))
    assert all(i.replace("-", "").replace("_", "").isalnum()
               and i[0].isalpha() and i.isascii() for i in ids), ids
    for s in sections:
        assert all(a["n"] <= b["n"] for a, b in zip(s["items"], s["items"][1:])), \
            "%s is out of year order" % s["title"]

    hours = sum(f["runtime"] for f in films) / 60.0

    prop = {
        "slug": SLUG,
        "title": "Akira Kurosawa",
        "subtitle": "the thirty features, in release order",
        "kind": "films",
        "popularity": 62,
        # Not a story, so not a sequence: the order these came out in
        # is a fact about the maker, not an instruction to the viewer
        # (Nathan, CLU-372). Prerequisites, where any exist, live in
        # tools/data/sequences.json and are enforced separately.
        "random": True,
        "year": "1943–1993",
        "blurb": "Every feature he directed, Sanshiro Sugata through "
                 "Madadayo — %d films, about %d hours."
                 % (len(films), round(hours)),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": "#5A2E28",
        "accentDark": "#D08A80",
        "tiers": False,
        "notes": [
            ["Directed features only.", "The filmography's one co-direction "
             "— Those Who Make Tomorrow, a 1946 studio project shared with "
             "Hideo Sekigawa and Kajiro Yamamoto — is not here: it is not "
             "his film the way the other thirty are. Everything from "
             "Sanshiro Sugata to Madadayo is."],
            ["Many sit on the Criterion list too.", "Rashomon, Ikiru, Seven "
             "Samurai, Yojimbo and a dozen more are also on the Criterion "
             "Collection list in this tracker; each list keeps its own "
             "ticks."],
            ["Bar widths are runtimes.", "From Wikidata, in hours — about "
             "%d in all. Every one of the %d films has a real runtime; the "
             "generator refuses to build without them."
             % (round(hours), len(films))],
            "Filmography from Wikipedia's List of works by Akira Kurosawa; "
            "runtimes and release dates from Wikidata.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d films, %.1f hours" % (len(films), hours))
    for s in sections:
        print("   %-22s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
