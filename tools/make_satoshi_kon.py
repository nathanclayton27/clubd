#!/usr/bin/env python3
"""Generate properties/satoshi-kon.json.

    python3 tools/make_satoshi_kon.py

Everything Satoshi Kon directed: the four features (runtimes from Wikidata),
Paranoia Agent's thirteen episodes at 24 minutes each, and the one-minute
Ani*Kuri15 short Good Morning (Ohayō) — the Satoshi Kon article's own
television table dates it 2008 and calls it a 1-minute short, which is also
its weight.

Not here: the films he only wrote or animated on (Roujin Z, Memories'
Magnetic Rose segment, Patlabor 2 layouts), and the three episodes of the
1993 JoJo's Bizarre Adventure OVA — episode direction on someone else's
series. Dreaming Machine, unfinished at his death in 2010, gets a note
instead of a row: there is nothing to watch.

Why the four features carry "m" and "q" (CLU-369)
-------------------------------------------------
This list's kind is "anime", which is the copy printed on the card wall. It
was also the sync gate, and the gate only recognised the words "film" and
"game" — so no row here minted a sync key at all, and Perfect Blue could
never pair with the same film on another list, in either lane, ever. The
failure was silent: a list that cannot pair simply never appears in a group.

The fix is a per-row declaration rather than a wider reading of the copy. The
four features declare "m": "f" — they are films, and they are the only rows
here that are. Paranoia Agent's thirteen episodes are television and declare
nothing; neither does the one-minute short, whose printed title is
"Ohayō (Good Morning)" and would not match another list's spelling of it
on title anyway.

They also carry "q", a Wikidata work id, which is what pairs a row when the
titles or the years disagree — and for Millennium Actress they do: Wikidata
publishes 2001, 2002 and 2003 for it, so a list dating it by a later release
would miss this row on title+year. Each id is the one the Satoshi Kon
article's own filmography wikilink resolved to, never a title search, and each
is checked against the entity itself before it ships — see gate() below.
Adding a medium letter and a work id changes no row id, so no tick moves.
"""
import json
import pathlib

SLUG = "satoshi-kon"

FILM_INTRO = ("Four features in nine years, every one of them about a "
              "boundary failing — performer and role, actress and century, "
              "dream and machine. All from Madhouse, all complete "
              "in themselves.")

FILM_NOTE = {
    "Perfect Blue": "His debut feature",
    "Paprika": "His last completed feature",
}


# The classes a work id is allowed to be an instance of. All four features
# state exactly Q20650540 today. Asserted rather than assumed: an id that has
# drifted to a soundtrack album, a franchise or the manga would otherwise pair
# this row with everything else carrying that entity.
FILM_CLASS = {"Q20650540"}

# A work id the gate refused, keyed by title, with the reason. Empty today —
# all four features pass. It stays as the place a refusal goes, because a row
# shipping no id is exactly what every row here did until now, while a WRONG id
# would tick a film nobody watched on every other list carrying the real work.
NO_Q = {}


def gate(f):
    """Why this film's work id may NOT ship, or None if it may.

    The evidence is collected by scratch/agent-kon-qid/verify.py into
    tools/data/satoshi-kon.json and asserted here, so a re-collection landing
    on a different entity stops this script instead of quietly pairing the
    wrong film. Three independent facts have to agree, because each one alone
    can be satisfied by the wrong work: a title reaches a different film of
    the same name, a year reaches a remake, and a director credit reaches
    everything else he made.
    """
    wd = f.get("wd") or {}
    names = {n for n in [wd.get("label")] + list(wd.get("aliases") or []) if n}
    if f["t"] not in names:
        return "no en label or alias reads %r — got %s" % (f["t"],
                                                            sorted(names))
    if "Satoshi Kon" not in (wd.get("directors") or []):
        return "P57 does not credit Satoshi Kon — %s" % (wd.get("directors"),)
    if f["year"] not in (wd.get("years") or []):
        return "P577 %s does not include the row's %d" % (wd.get("years"),
                                                          f["year"])
    cls = set(wd.get("instance_of") or [])
    if not cls & FILM_CLASS:
        return "P31 %s is not a film class" % sorted(cls)
    return None


def slug(t):
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def main():
    data = pathlib.Path(__file__).resolve().parent / "data"
    d = json.loads((data / "satoshi-kon.json").read_text(encoding="utf-8"))
    films, pa, short = d["films"], d["paranoia"], d["short"]
    assert len(films) == 4 and all(f["runtime"] for f in films), films
    assert len(pa["episodes"]) == 13, len(pa["episodes"])
    assert short["minutes"] == 1 and short["year"] == 2008, short

    stray = sorted(set(NO_Q) - {f["t"] for f in films})
    assert not stray, "NO_Q names films this list does not have: %s" % stray

    fitems, refused = [], []
    for f in films:
        why = gate(f)
        if f["t"] in NO_Q:
            refused.append((f["t"], NO_Q[f["t"]]))
        else:
            assert not why, ("%s: work id %s fails the gate — %s"
                             % (f["t"], f["qid"], why))
        # "f" says this row is a film, which is the whole reason it can pair:
        # the list's kind is "anime", and the gate reads the row, not the copy.
        it = {"id": "sk-%d-%s" % (f["year"], slug(f["t"])),
              "t": f["t"], "n": str(f["year"]),
              "w": round(f["runtime"] / 60.0, 2), "m": "f"}
        if f["t"] not in NO_Q:
            it["q"] = f["qid"]
        if f["t"] in FILM_NOTE:
            it["note"] = FILM_NOTE[f["t"]]
        fitems.append(it)
    qs = [x["q"] for x in fitems if x.get("q")]
    assert len(qs) == len(set(qs)), "two rows share a work id: %s" % qs
    assert len(qs) == len(films) - len(NO_Q), (len(qs), len(NO_Q))
    fh = sum(f["runtime"] for f in films) / 60.0

    epw = round(24 / 60.0, 2)
    eitems = [{"id": "sk-pa-%d" % e["n"], "t": e["t"], "n": str(e["n"]),
               "w": epw} for e in pa["episodes"]]

    sections = [
        {"id": "films", "title": "The four films",
         "sub": "1997–2006 · 4 films · %d hours" % round(fh),
         "intro": FILM_INTRO, "items": fitems, "open": True},
        {"id": "paranoia", "title": "Paranoia Agent",
         "sub": "2004 · 13 episodes · %d hours" % round(13 * 24 / 60.0),
         "intro": "The one television series — built from ideas that "
                  "wouldn't fit in the films, and aired between Tokyo "
                  "Godfathers and Paprika. Episodes weigh 24 minutes each.",
         "items": eitems},
        {"id": "ohayo", "title": "Ohayō",
         "sub": "2008 · one minute",
         "intro": "A one-minute short made for the Ani*Kuri15 television "
                  "anthology — the last thing he finished.",
         "items": [{"id": "sk-2008-ohayo", "t": "Ohayō (Good Morning)",
                    "n": "2008", "w": round(1 / 60.0, 2),
                    "note": "1-minute short for the Ani*Kuri15 television "
                            "anthology"}]},
    ]

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == 18, len(ids)
    for s in sections:
        ns = [x["n"] for x in s["items"]]
        key = [int(n) for n in ns]
        assert key == sorted(key), "%s out of order" % s["title"]

    hours = sum(x["w"] for s in sections for x in s["items"])

    prop = {
        "slug": SLUG,
        "title": "Satoshi Kon",
        "subtitle": "everything he directed",
        "kind": "anime",
        "popularity": 45,
        # Not a story, so not a sequence: the order these came out in
        # is a fact about the maker, not an instruction to the viewer
        # (Nathan, CLU-372). Prerequisites, where any exist, live in
        # tools/data/sequences.json and are enforced separately.
        "random": True,
        "year": "1997–2008",
        "blurb": "Four films, thirteen episodes of Paranoia Agent, and a "
                 "one-minute short — the complete directed work, about %d "
                 "hours." % round(hours),
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": "#8B3A85",
        "accentDark": "#E794DC",
        "tiers": False,
        "notes": [
            ["This is the whole thing.", "Kon died in 2010, at 46, with "
             "four features, one series and a short finished. It all fits "
             "in a week, and none of it is skippable."],
            ["Dreaming Machine has no row.", "His fifth feature was in "
             "production at Madhouse when he died and was never completed "
             "— by 2013 only 600 of 1,500 shots were animated, and the "
             "studio has declined to finish it with another director in "
             "his place. There is nothing to watch, so there is nothing "
             "to tick."],
            ["Bar widths are runtimes.", "Film runtimes from Wikidata; "
             "Paranoia Agent episodes weigh a flat 24 minutes; the short "
             "weighs its one minute."],
            "Filmography and the Good Morning short from Wikipedia's "
            "Satoshi Kon article; episode list from List of Paranoia "
            "Agent episodes; film runtimes from Wikidata.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")
    print("wrote %s.json — %d entries, %.2f hours" % (SLUG, len(ids), hours))
    for s in sections:
        print("   %-16s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))
    for t, why in refused:
        print("   no work id: %-22s %s" % (t, why))
    for line in pairs(fitems):
        print("   %s" % line)


def pairs(fitems):
    """What the four features pair with across the catalogue, right now.

    Reads the other property files with build.py's gate — a row syncs on its
    own "m", or on a kind containing "film" or "game" — and reports by work
    id and by title+year separately, because the id is the half that survives
    two lists dating a film differently. A line saying a film pairs with
    nothing is the truthful answer rather than a failure: no other list carried
    a Kon film on the day this shipped, which is why the defect was silent.
    """
    import re
    import unicodedata

    def normt(t):
        t = unicodedata.normalize("NFKD", t)
        t = "".join(c for c in t if not unicodedata.combining(c)).lower()
        t = re.sub(r"[^a-z0-9]+", " ", t).strip()
        return re.sub(r"^(the|a|an) ", "", t)

    props = pathlib.Path(__file__).resolve().parent.parent / "properties"
    byq, byty = {}, {}
    for pf in sorted(props.glob("*.json")):
        if pf.name in ("index.json", "search.json"):
            continue
        p = json.loads(pf.read_text(encoding="utf-8"))
        if p.get("secret") or p.get("slug") == SLUG or "sections" not in p:
            continue
        kind = p.get("kind") or ""
        fallback = ("g" if "game" in kind else "f") if (
            "film" in kind or "game" in kind) else None
        for s in p.get("sections", []):
            for x in s.get("items", []):
                if (x.get("m") or fallback) != "f":
                    continue
                n = str(x.get("n", ""))
                if x.get("q"):
                    byq.setdefault(x["q"], []).append(p["slug"])
                if re.fullmatch(r"(18|19|20)[0-9]{2}", n):
                    byty.setdefault(normt(x["t"]) + "|" + n,
                                    []).append(p["slug"])
    out = []
    for x in fitems:
        q = sorted(set(byq.get(x.get("q"), [])))
        ty = sorted(set(byty.get(normt(x["t"]) + "|" + x["n"], [])))
        out.append("pairs: %-20s id -> %-22s title+year -> %s"
                   % (x["t"][:20], ", ".join(q) or "nothing",
                      ", ".join(ty) or "nothing"))
    return out


if __name__ == "__main__":
    main()
