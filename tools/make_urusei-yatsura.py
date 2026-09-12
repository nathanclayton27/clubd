#!/usr/bin/env python3
"""Generate properties/urusei-yatsura.json.

    python tools/make_urusei-yatsura.py

Four eras: the 1981–86 series (194 numbered episodes across the four
season tables Wikipedia uses), the six theatrical films, the ten OVAs, and
the 2022 remake's two seasons. Everything comes from
tools/data/urusei-yatsura.json, built by scratch/agent-anime/harvest_uy.py
from the Wikipedia episode lists and the film-series article; a film's own
article beats the franchise page on runtime (Beautiful Dreamer: 98 min,
not 96).

Films and episodes share the page, so everything is weighted — episodes
and OVAs at 0.4h, films at runtime/60. Beautiful Dreamer's row notes its
Time Loops cross-listing; it is on that page too. The three specials the
1981 tables carry outside the numbering are not rows, and the notes say so.

Why the six films carry "m", and two of them "q" (CLU-551)
----------------------------------------------------------
This list's kind is "anime", which is the copy printed on the card wall. It
was also the tick-sync gate, and that gate only recognised the words "film"
and "game" — so no row here minted a sync key at all, and Beautiful Dreamer
could not pair with the SAME FILM on time-loops, which has carried it since
that list shipped. The failure was silent: a list that cannot pair simply
never appears in a group.

CLU-369 made the gate a per-row declaration, and this is that declaration.
The six theatrical films say `m: "f"`; the 194 episodes, the ten OVAs and the
46 remake broadcasts say nothing, because they are television and video and
must never pair with a film row. What counts as a film here is not a reading
of the copy: the film-series article states `type = film` on each of the six
and `type = ova` on the making-of featurette and the OVA block, and those
declarations are collected into the data file and asserted below.

Two of the six also carry "q", a Wikidata work id, which is what pairs a row
when the titles or the years disagree. Only Only You and Beautiful Dreamer
have an article of their own for the film-series page to link to, so only
those two have an id that came from a wikilink rather than from a title
search — and a title search is how a row ends up pointing at a soundtrack
album or at a different film of the same name. The other four ship no id and
pair on title and year alone, which is what every row here did until now.
Each id is re-checked against the entity itself before it ships; see gate().

Adding a medium letter and a work id changes no row id, so no tick moves.
"""
import json
import pathlib

SLUG = "urusei-yatsura"

DATA = pathlib.Path(__file__).resolve().parent / "data" / (SLUG + ".json")
OUT = pathlib.Path(__file__).resolve().parent.parent / "properties" / (SLUG + ".json")

EP_W = 0.4
WIKI = "https://en.wikipedia.org/wiki/"

FILM_NOTES = {1984: "Also on the Time Loops list"}

# The printed title of every row that is a film, mapped to the title the
# film-series article's own {{Infobox animanga/Video}} box gives it. That box
# is the evidence for `m: "f"`: four of these films have no article of their
# own, so it IS their article, and its `type = film` is the only
# machine-readable statement that they are films rather than OVAs.
FILM_SOURCE_TITLE = {
    "Urusei Yatsura: Only You": "Urusei Yatsura: Only You",
    "Urusei Yatsura 2: Beautiful Dreamer":
        "Urusei Yatsura 2: Beautiful Dreamer",
    "Urusei Yatsura 3: Remember My Love": "Remember My Love",
    "Urusei Yatsura 4: Lum the Forever": "Lum the Forever",
    "Urusei Yatsura: The Final Chapter": "The Final Chapter",
    "Urusei Yatsura: Always My Darling": "Always, My Darling",
}

# The classes a work id is allowed to be an instance of. Both ids state
# exactly Q20650540 (anime film) today. Asserted rather than assumed: an id
# that has drifted to a franchise, to the manga or to a soundtrack would
# otherwise pair this row with everything else carrying that entity.
FILM_CLASS = {"Q20650540"}

# Who the film-series article credits as director, which the gate checks
# Wikidata agrees with. A year alone reaches a remake and a title alone
# reaches a different film of the same name; the director is the third
# independent fact, and all three have to hold.
DIRECTOR = {
    "Urusei Yatsura: Only You": "Mamoru Oshii",
    "Urusei Yatsura 2: Beautiful Dreamer": "Mamoru Oshii",
}

# A film whose work id may NOT ship, keyed by printed title, with the reason.
# The four films with no English article of their own are here: the
# film-series page has no wikilink to resolve, and this catalogue does not
# search for a title and believe what comes back. They still declare `m`, so
# they pair on title and year — shipping no id is what every row on this list
# did until now, while a WRONG id would tick a film nobody watched on every
# other list carrying the real work.
NO_Q = {
    "Urusei Yatsura 3: Remember My Love":
        "no English article of its own, so no wikilink to resolve",
    "Urusei Yatsura 4: Lum the Forever":
        "no English article of its own, so no wikilink to resolve",
    "Urusei Yatsura: The Final Chapter":
        "no English article of its own, so no wikilink to resolve",
    "Urusei Yatsura: Always My Darling":
        "no English article of its own, so no wikilink to resolve",
}


def gate(title, year, wd):
    """Why this film's work id may NOT ship, or None if it may.

    The evidence is collected by scratch/agent-rows/verify.py into
    tools/data/urusei-yatsura.json and asserted here, so a re-collection
    landing on a different entity stops this script instead of quietly pairing
    the wrong film. Three independent facts have to agree, because each one
    alone can be satisfied by the wrong work.
    """
    if not wd:
        return "no Wikidata evidence collected"
    names = {n for n in [wd.get("label")] + list(wd.get("aliases") or []) if n}
    if title not in names:
        return "no en label or alias reads %r — got %s" % (title,
                                                            sorted(names))
    want = DIRECTOR.get(title)
    if want not in (wd.get("directors") or []):
        return "P57 does not credit %s — %s" % (want, wd.get("directors"))
    if year not in (wd.get("years") or []):
        return "P577 %s does not include the row's %d" % (wd.get("years"),
                                                          year)
    cls = set(wd.get("instance_of") or [])
    if not cls & FILM_CLASS:
        return "P31 %s is not a film class" % sorted(cls)
    return None


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))

    sections = []
    for s in d["series"]:
        sec = {
            "id": "s%d" % s["season"],
            "title": "Season %d" % s["season"],
            "sub": "%s · %d episodes" % (s["years"], len(s["eps"])),
            "links": [{"label": "The episode list",
                       "url": WIKI + "List_of_Urusei_Yatsura_episodes"}],
            "items": [{"id": "uy-e%d" % e["n"], "t": e["t"],
                       "n": str(e["n"]), "w": EP_W} for e in s["eps"]],
        }
        if s["season"] == 1:
            sec["open"] = True
            sec["intro"] = ("Rumiko Takahashi's alien-girl farce, adapted "
                            "while the manga ran. Most early episodes aired "
                            "as two shorter segments — those rows join both "
                            "titles.")
        sections.append(sec)

    # `m: "f"` is a claim that a row is a film, so it is checked against the
    # source rather than against the shape of the row: the film-series
    # article's own video boxes say which of its entries are films and which
    # are OVAs, and this asserts that the six rows about to declare `m` are
    # exactly the six that article calls films.
    boxes = {v["title"]: v for v in d["series_article_videos"]}
    said_film = {t for t, v in boxes.items() if v["type"] == "film"}
    want = set(FILM_SOURCE_TITLE.values())
    assert want == said_film, \
        "the film-series article no longer calls exactly these entries " \
        "films: missing %s, unexpected %s" % (sorted(want - said_film),
                                              sorted(said_film - want))
    assert {f["t"] for f in d["films"]} == set(FILM_SOURCE_TITLE), \
        "FILM_SOURCE_TITLE no longer names this list's films: %s" \
        % sorted({f["t"] for f in d["films"]} ^ set(FILM_SOURCE_TITLE))
    stray = sorted(set(NO_Q) - {f["t"] for f in d["films"]})
    assert not stray, "NO_Q names films this list does not have: %s" % stray

    wd = d.get("wd") or {}
    film_items, refused = [], []
    for f in d["films"]:
        note = "%d min" % f["runtime"]
        if f["year"] in FILM_NOTES:
            note = FILM_NOTES[f["year"]] + " · " + note
        # "f" says this row is a film, which is the whole reason it can pair:
        # the list's kind is "anime", and the gate reads the row, not the copy.
        it = {"id": "uy-film-%d" % f["year"], "t": f["t"],
              "n": str(f["year"]), "w": round(f["runtime"] / 60.0, 2),
              "m": "f", "note": note}
        why = gate(f["t"], f["year"], wd.get(f["t"]))
        if f["t"] in NO_Q:
            refused.append((f["t"], NO_Q[f["t"]]))
            assert f["t"] not in wd, \
                "%s is in NO_Q but evidence WAS collected for it — either " \
                "ship the id or say here why not" % f["t"]
        else:
            assert not why, ("%s: work id %s fails the gate — %s"
                             % (f["t"], (wd.get(f["t"]) or {}).get("qid"),
                                why))
            it["q"] = wd[f["t"]]["qid"]
        film_items.append(it)
    qs = [x["q"] for x in film_items if x.get("q")]
    assert len(qs) == len(set(qs)), "two rows share a work id: %s" % qs
    assert len(qs) == len(d["films"]) - len(NO_Q), (len(qs), len(NO_Q))
    sections.append({
        "id": "films",
        "title": "The films",
        "sub": "1983–91 · six theatrical films",
        "intro": "Four made during the TV run, two after it. Beautiful "
                 "Dreamer is Mamoru Oshii's — and sits on the Time Loops "
                 "list as well.",
        "links": [{"label": "The film series",
                   "url": WIKI + "Urusei_Yatsura_(film_series)"}],
        "items": film_items,
    })

    sections.append({
        "id": "ovas",
        "title": "The OVAs",
        "sub": "1987–2008 · ten releases",
        "intro": "Released 1987–91, plus one 2008 special made for the "
                 "It's a Rumic World exhibition. All ran in cinemas before "
                 "video.",
        "items": [{"id": "uy-ova-%d" % o["n"], "t": o["t"], "n": str(o["n"]),
                   "w": EP_W, "note": str(o["year"])} for o in d["ovas"]],
    })

    for r in d["remake"]:
        items = []
        for e in r["eps"]:
            slug_n = e["n"].replace("–", "-").lower()
            items.append({"id": "uy22-%s" % slug_n, "t": e["t"],
                          "n": e["n"], "w": EP_W})
        sec = {
            "id": "r%d" % r["season"],
            "title": "The remake, season %d" % r["season"],
            "sub": "%s · 23 broadcasts" % r["years"],
            "links": [{"label": "The 2022 series",
                       "url": WIKI + "Urusei_Yatsura_(2022_TV_series)"}],
            "items": items,
        }
        if r["season"] == 1:
            sec["intro"] = ("The 2022 remake by David Production, adapting "
                            "selected chapters afresh.")
        else:
            sec["intro"] = ("The numbering keeps the tables' own quirk: two "
                            "broadcasts each span parts of two episodes, so "
                            "their rows carry both numbers.")
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == 194 + 6 + 10 + 46, len(ids)
    hours = sum(x["w"] for s in sections for x in s["items"])

    prop = {
        "slug": SLUG,
        "title": "Urusei Yatsura",
        "subtitle": "the 1981 series, the films, the OVAs, the remake",
        "kind": "anime",
        "popularity": 38,
        "year": "1981–2024",
        "blurb": "All 194 episodes of the original run, six films, ten "
                 "OVAs and the 2022 remake — about %d hours of Lum."
                 % round(hours),
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#4C7A1D",
        "accentDark": "#FFD447",
        "tiers": False,
        "notes": [
            ["Eras in order.", "The 1981–86 series (the four season tables "
             "Wikipedia uses are kept), the six theatrical films, the OVAs "
             "as one block, then the 2022 remake's two seasons."],
            ["Weights.", "Episodes and OVAs weigh 0.4 hours; films weigh "
             "their runtimes. Beautiful Dreamer's runtime comes from its "
             "own article (98 min), which beats the franchise page's 96."],
            ["What is out.", "The three specials the 1981 tables carry "
             "outside the episode numbering — All-Star Bash, Ryoko's "
             "September Tea Party and Memorial Album, the latter two "
             "mixing new footage with clips — and the Lum the Forever "
             "making-of featurette."],
            "Episode tables, film years and runtimes machine-read from the "
            "Wikipedia episode lists, the film-series article and the "
            "films' own articles; season counts and the 1–194 numbering "
            "asserted before this builds.",
        ],
        "sections": sections,
    }

    with OUT.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json — %d rows, %.2f hours" % (SLUG, len(ids), hours))
    for s in sections:
        print("   %-24s %3d  %s" % (s["title"], len(s["items"]),
                                    s.get("sub", "")[:40]))
    print("   %d film rows declare m:f; %d of them carry a work id"
          % (len(film_items), len(qs)))
    for t_, why_ in refused:
        print("   no work id: %-38s %s" % (t_[:38], why_))


if __name__ == "__main__":
    main()
