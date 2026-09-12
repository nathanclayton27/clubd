#!/usr/bin/env python3
"""Generate properties/ghost-in-the-shell.json.

    python tools/make_ghost-in-the-shell.py

Everything animated, sectioned by continuity: Mamoru Oshii's two films; the
Stand Alone Complex television continuity (season 1, 2nd GIG, the Solid
State Society TV film, and — much later — SAC_2045 with its Sustainable War
compilation film between the seasons); and the Arise continuity (five
feature-length OVA "borders" closed by the 2015 New Movie).

Everything numeric comes from tools/data/ghost-in-the-shell.json, built by
scratch/agent-anime/harvest_gits.py from the Wikipedia episode lists and
film articles (infobox runtimes beat Wikidata). Because films and episodes
share the page, everything is weighted: episodes at 0.4h, films at
runtime/60, the borders at the Arise infobox's 50 minutes each. Sustainable
War has no runtime in any machine-readable source and weighs nothing rather
than a guess. Live action is out; the notes say so.

Why four rows carry "m", and three of them "q" (CLU-551)
--------------------------------------------------------
This list's kind is "anime", which is the copy printed on the card wall. It
was also the tick-sync gate, and that gate only recognised the words "film"
and "game" — so no row here minted a sync key at all, and the 1995 film could
not pair with the SAME FILM on cult-classics, which has carried it (and its
work id) since that list shipped. The failure was silent: a list that cannot
pair simply never appears in a group.

CLU-369 made the gate a per-row declaration, and this is that declaration.
The four rows that are single films say `m: "f"`. The 76 episodes say
nothing, and neither do the five Arise borders — they are feature-length OVAs,
they are numbered by border rather than by year, and a film list must never
tick one. Sustainable War says nothing either: it has no English article, so
nothing machine-readable calls it a film, and this list does not declare what
it cannot cite.

Three of the four also carry "q", a Wikidata work id, which is what pairs a
row when the titles or the years disagree. Each id is the one the Ghost in
the Shell franchise article's own wikilink resolves to — never a title search
— and each is re-checked against the entity itself before it ships: an en
label or alias equal to the printed title, the director the article credits,
the row's year among the entity's publication years, and a film class. See
gate() and NO_Q below, which is where the fourth row's refusal is recorded.

Adding a medium letter and a work id changes no row id, so no tick moves.
"""
import json
import pathlib

SLUG = "ghost-in-the-shell"

DATA = pathlib.Path(__file__).resolve().parent / "data" / (SLUG + ".json")
OUT = pathlib.Path(__file__).resolve().parent.parent / "properties" / (SLUG + ".json")

EP_W = 0.4

WIKI = "https://en.wikipedia.org/wiki/"

# The classes a work id is allowed to be an instance of. All four films state
# Q20650540 (anime film); Solid State Society adds Q506240 (television film),
# which is what it is. Asserted rather than assumed: an id that has drifted to
# the manga, the franchise, a video game or a soundtrack would otherwise pair
# this row with everything else carrying that entity.
FILM_CLASS = {"Q20650540"}

# Who the franchise article credits as director, which the gate checks
# Wikidata agrees with. A year alone reaches a remake and a title alone
# reaches a different film of the same name — and this franchise has a
# live-action film, two video games and a manga sharing its title — so the
# director is the third independent fact, and all three have to hold.
DIRECTOR = {
    "Ghost in the Shell": "Mamoru Oshii",
    "Ghost in the Shell 2: Innocence": "Mamoru Oshii",
    "Solid State Society": "Kenji Kamiyama",
    "Ghost in the Shell: The New Movie": "Kazuchika Kise",
}

# A film whose work id may NOT ship, keyed by printed title, with the reason.
# The row still declares `m`, so it pairs on title and year; shipping no id is
# what every row on this list did until now, while a WRONG id would tick a
# film nobody watched on every other list carrying the real work.
NO_Q = {
    "Solid State Society":
        "Q764897 is the right entity — Kamiyama, 2006, an anime television "
        "film — but its en label is the full 'Ghost in the Shell: Stand Alone "
        "Complex - Solid State Society' and it carries no alias reading the "
        "short title this list prints, so the label check refuses it. Widening "
        "that check is the wrong fix: it is the half of the gate that stops an "
        "id reaching a different work of the same name",
}


def gate(title, year, wd):
    """Why this film's work id may NOT ship, or None if it may.

    The evidence is collected by scratch/agent-rows/verify.py into
    tools/data/ghost-in-the-shell.json and asserted here, so a re-collection
    landing on a different entity stops this script instead of quietly pairing
    the wrong film. Four independent facts have to agree, because each one
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


def ep_rows(eps, prefix):
    return [{"id": "%s%d" % (prefix, e["n"]), "t": e["t"], "n": str(e["n"]),
             "w": EP_W} for e in eps]


def film_row(f, id_, note_extra="", wd=None, refused=None):
    """One film row, declaring its medium and — where the gate allows — its id.

    `wd` is the whole evidence block; a title absent from it gets neither `m`
    nor `q`, which is Sustainable War's case: no English article, so nothing
    machine-readable calls it a film.
    """
    w = round(f["runtime"] / 60.0, 2) if f.get("runtime") else 0
    note = ("%d min" % f["runtime"]) if f.get("runtime") else \
        "No runtime on record — weighs nothing"
    if note_extra:
        note = note_extra + " · " + note
    it = {"id": id_, "t": f["t"], "n": str(f["year"]), "w": w, "note": note}
    ev = (wd or {}).get(f["t"])
    if not ev:
        if refused is not None:
            refused.append((f["t"], "no English article, so nothing "
                                    "machine-readable calls it a film"))
        return it
    it["m"] = "f"
    why = gate(f["t"], f["year"], ev)
    if f["t"] in NO_Q:
        if refused is not None:
            refused.append((f["t"], NO_Q[f["t"]]))
        assert why, \
            "%s is in NO_Q but the gate now passes it — delete the entry and " \
            "ship the id rather than leaving a refusal that no longer holds" \
            % f["t"]
        return it
    assert not why, ("%s: work id %s fails the gate — %s"
                     % (f["t"], ev.get("qid"), why))
    it["q"] = ev["qid"]
    return it


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    films = d["films"]
    wd, refused = d.get("wd") or {}, []
    stray = sorted(set(NO_Q) - {f["t"] for f in films.values()})
    assert not stray, "NO_Q names films this list does not have: %s" % stray
    stray = sorted(set(DIRECTOR) - {f["t"] for f in films.values()})
    assert not stray, "DIRECTOR names films this list does not have: %s" % stray

    sections = [
        {
            "id": "oshii",
            "title": "The Oshii films",
            "sub": "1995 & 2004 · the film continuity",
            "intro": "Mamoru Oshii's continuity: the 1995 film and its "
                     "sequel Innocence. Separate from every series below.",
            "links": [{"label": "The 1995 film",
                       "url": WIKI + "Ghost_in_the_Shell_(1995_film)"}],
            "open": True,
            "items": [film_row(films["f1995"], "gits-film-1995",
                                wd=wd, refused=refused),
                      film_row(films["f2004"], "gits-film-2004",
                               wd=wd, refused=refused)],
        },
        {
            "id": "sac1",
            "title": "Stand Alone Complex",
            "sub": "2002–03 · 26 episodes",
            "intro": "A second continuity, restarted for television: "
                     "Section 9 from scratch, unconnected to the films.",
            "links": [{"label": "The episode list",
                       "url": WIKI + "List_of_Ghost_in_the_Shell:_"
                              "Stand_Alone_Complex_episodes"}],
            "items": ep_rows(d["sac1"], "gits-s1e"),
        },
        {
            "id": "sac2",
            "title": "S.A.C. 2nd GIG",
            "sub": "2004–05 · 26 episodes",
            "intro": "Season two of the Stand Alone Complex continuity.",
            "items": ep_rows(d["sac2"], "gits-s2e"),
        },
        {
            "id": "sss",
            "title": "Solid State Society",
            "sub": "2006 · the Stand Alone Complex TV film",
            "items": [film_row(films["f2006"], "gits-film-2006",
                               "TV film, two years after 2nd GIG",
                               wd=wd, refused=refused)],
        },
        {
            "id": "arise",
            "title": "Arise",
            "sub": "2013–15 · five borders",
            "intro": "A third continuity: a younger Section 9, told in five "
                     "feature-length OVAs called borders, released to "
                     "cinemas first.",
            "links": [{"label": "Arise",
                       "url": WIKI + "Ghost_in_the_Shell:_Arise"}],
            "items": [{"id": "gits-arise-b%d" % b["n"],
                       "t": "Border %d: %s" % (b["n"], b["t"]),
                       "n": str(b["n"]),
                       "w": round(d["arise_min"] / 60.0, 2),
                       "note": "%d min" % d["arise_min"]}
                      for b in d["arise"]],
        },
        {
            "id": "newmovie",
            "title": "The New Movie",
            "sub": "2015 · the film that closes Arise",
            "items": [film_row(films["f2015"], "gits-film-2015",
                               "Follows the Arise borders",
                               wd=wd, refused=refused)],
        },
        {
            "id": "s2045a",
            "title": "SAC_2045 season 1",
            "sub": "2020 · 12 episodes",
            "intro": "Back to the Stand Alone Complex continuity, set in "
                     "2045 — eleven years after Solid State Society. 3DCG, "
                     "on Netflix.",
            "links": [{"label": "The episode list",
                       "url": WIKI + "List_of_Ghost_in_the_Shell:_"
                              "SAC_2045_episodes"}],
            "items": ep_rows(d["s2045a"], "gits-2045-s1e"),
        },
        {
            "id": "suswar",
            "title": "Sustainable War",
            "sub": "2021 · the season-one compilation film",
            "items": [film_row(d["suswar"], "gits-film-2021",
                               "Recompiles season 1",
                               wd=wd, refused=refused)],
        },
        {
            "id": "s2045b",
            "title": "SAC_2045 season 2",
            "sub": "2022 · 12 episodes",
            "items": ep_rows(d["s2045b"], "gits-2045-s2e"),
        },
    ]

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == 86, len(ids)
    hours = sum(x["w"] for s in sections for x in s["items"])

    prop = {
        "slug": SLUG,
        "title": "Ghost in the Shell",
        "subtitle": "everything animated, by continuity",
        "kind": "anime",
        "popularity": 64,
        "year": "1995–2022",
        "blurb": "Three animated continuities — the Oshii films, Stand "
                 "Alone Complex through SAC_2045, and Arise — %d entries, "
                 "about %d hours." % (len(ids), round(hours)),
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#186A66",
        "accentDark": "#F5933E",
        "tiers": False,
        "notes": [
            ["Sections are continuities.", "Three separate animated tellings "
             "share these characters: Oshii's two films; the Stand Alone "
             "Complex television line (seasons 1 and 2, Solid State Society, "
             "and — set eleven years later — SAC_2045); and Arise, whose "
             "five borders the 2015 New Movie concludes. Watch a continuity "
             "together; nothing carries between them."],
            ["Weights.", "Episodes weigh 0.4 hours, films their runtimes, "
             "and the Arise borders the 50 minutes each their article "
             "gives. Sustainable War has no runtime on record anywhere "
             "machine-readable and weighs nothing rather than a guess."],
            ["Animation only.", "The 2017 live-action remake is out. So are "
             "the recuts and rebroadcasts — Arise: Alternative Architecture "
             "(the borders re-aired for TV) and The Last Human (the "
             "season-two compilation film). Sustainable War, the season-one "
             "compilation, keeps its row so the Netflix run is complete; "
             "its row says what it is."],
            ["The Tachikomatic Days shorts are not rows.",
             "Comedy omake attached to the Stand Alone Complex broadcasts; "
             "they are on the episode-list page and nothing here depends on "
             "them."],
            "Episode lists, film years and runtimes machine-read from the "
            "Wikipedia articles; every season's numbering asserted complete "
            "before this builds.",
        ],
        "sections": sections,
    }

    with OUT.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json — %d rows, %.2f hours" % (SLUG, len(ids), hours))
    for s in sections:
        print("   %-22s %2d  %s" % (s["title"], len(s["items"]),
                                    s.get("sub", "")[:40]))
    dec = [x for s in sections for x in s["items"] if x.get("m")]
    print("   %d rows declare m:f; %d of them carry a work id"
          % (len(dec), sum(1 for x in dec if x.get("q"))))
    for t_, why_ in refused:
        print("   no work id: %-24s %s" % (t_[:24], why_[:120]))


if __name__ == "__main__":
    main()
