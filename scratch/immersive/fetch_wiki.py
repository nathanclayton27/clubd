#!/usr/bin/env python3
"""Collect the two Wikipedia sources the immersive-sim canon is gated on.

    python scratch/immersive/fetch_wiki.py

Writes three caches into scratch/immersive/:

  * category.json  — every article in Wikipedia's Category:Immersive sims,
    read from the API (action=query&list=categorymembers). This is the
    membership gate: a game that Wikipedia's own genre category does not hold
    is not on the list, whatever anyone thinks of it.
  * Immersive-sim.wiki — the genre article's wikitext, whose History and
    Lineage sections are the editorial spine: who says which game belongs,
    and in what order the form developed.
  * pages/<Article>.wiki — one cached article per candidate game, used for
    three things the roster must never assert by hand: the release year, taken
    from the infobox; whether the infobox's own genre field says "immersive
    sim"; and whether the prose says it outright rather than merely comparing
    the game to the genre.

That last distinction is the whole second gate, and it needs care in both
directions:

  * The category tag at the bottom of an article contains the words
    "immersive sim", so a naive substring search over the wikitext says every
    member of the category describes itself as one. It does not:
    ''Pathologic 2'''s article mentions the genre nowhere but the tag. So the
    category tags and the reference blocks are stripped before the prose is
    read at all.
  * An article can name the genre to say the game is NOT one of them, or is
    merely like one. ''Indiana Jones and the Great Circle'' says its "level
    design was inspired by immersive sims"; the genre article says the
    ''Hitman'' games are "not necessarily considered immersive sims". Mentions
    with one of the HEDGES below in front of them are recorded as hedged, and
    a game whose every mention is hedged does not pass on prose alone.

Nothing here decides what ships. It records what the sources say; the gate
and the cut live in tools/make_immersive.py, which re-asserts both every run.
"""
import json
import pathlib
import re
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from gwlib import wiki  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
CATEGORY = "Category:Immersive sims"
GENRE_PAGE = "Immersive sim"

# Every ns-0 member of the category is fetched, so the generator can reason
# about what it cut as well as what it kept. Series/list pages carry no
# infobox and are skipped for year extraction.
SKIP_YEAR = {"Immersive sim", "System Shock (series)"}


def category_members(cat):
    out, cont = [], None
    while True:
        q = {"action": "query", "list": "categorymembers", "cmtitle": cat,
             "cmlimit": "500", "format": "json", "formatversion": "2"}
        if cont:
            q["cmcontinue"] = cont
        d = wiki.get_json(wiki.API + "?" + urllib.parse.urlencode(q))
        out.extend(d["query"]["categorymembers"])
        cont = (d.get("continue") or {}).get("cmcontinue")
        if not cont:
            break
    return out


GENRE = re.compile(r"immersive[ -]sim", re.I)

# A mention with one of these in front of it compares the game to the genre
# instead of placing it inside it.
HEDGES = re.compile(r"(inspired by|similar to|reminiscent of|elements of|"
                    r"influenced by|not necessarily|in the (?:vein|style) of|"
                    r"comparisons? (?:to|with)|akin to|like (?:an|other)?)"
                    r"[^.]{0,60}$", re.I)


def prose(text):
    """Article text with category tags, references and templates removed.

    Templates are stripped innermost-first and repeatedly, so the infobox
    goes too — otherwise an article whose infobox has no nested templates
    keeps its genre field in the "prose" and an article whose infobox does
    have one loses it, and the two signals stop being independent.
    """
    t = re.sub(r"<ref[^>]*/>", " ", text)
    t = re.sub(r"<ref.*?</ref>", " ", t, flags=re.S)
    t = re.sub(r"\[\[Category:[^\]]*\]\]", " ", t, flags=re.I)
    for _ in range(8):
        t, n = re.subn(r"\{\{[^{}]*\}\}", " ", t)
        if not n:
            break
    return t


def genre_field(text):
    """The infobox `genre` field, or ''."""
    box = wiki.infobox(text, kind=r"video game|VG")
    return (box("genre") if box else "") or ""


def mentions(text):
    """(plain, hedged) counts of 'immersive sim' in the article's prose."""
    t = prose(text)
    plain = hedged = 0
    for m in GENRE.finditer(t):
        if HEDGES.search(t[max(0, m.start() - 120):m.start()]):
            hedged += 1
        else:
            plain += 1
    return plain, hedged


def released_years(text):
    """Every 4-digit year in the infobox `released` field, in order."""
    box = wiki.infobox(text, kind=r"video game|VG")
    if not box:
        return []
    field = box("released") or box("release") or ""
    return [int(y) for y in re.findall(r"\b(19[7-9]\d|20[0-4]\d)\b", field)]


def main():
    members = category_members(CATEGORY)
    pages = sorted(m["title"] for m in members if m["ns"] == 0)
    (HERE / "category.json").write_text(
        json.dumps({"category": CATEGORY, "pages": pages}, indent=1,
                   ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")
    print("%s: %d article members" % (CATEGORY, len(pages)))

    genre = wiki.wikitext(GENRE_PAGE, cache_dir=str(HERE))
    assert genre and "immersive sim" in genre.lower(), "genre article missing"

    cache = HERE / "pages"
    facts = {}
    for title in pages:
        if title == GENRE_PAGE:
            continue
        text = wiki.wikitext(title, cache_dir=str(cache))
        assert text, "no wikitext for %s" % title
        plain, hedged = mentions(text)
        facts[title] = {
            "genre_field": bool(GENRE.search(genre_field(text))),
            "prose_plain": plain,
            "prose_hedged": hedged,
            "years": [] if title in SKIP_YEAR else released_years(text),
            # does the genre article itself link to this page
            "in_genre_article": bool(
                re.search(r"\[\[%s(\||\]\])" % re.escape(title), genre)),
        }
        f = facts[title]
        print("  %-52s box=%-5s prose=%d/%dh years=%-9s linked=%s"
              % (title[:52], f["genre_field"], plain, hedged,
                 ",".join(str(y) for y in f["years"][:2]),
                 f["in_genre_article"]))

    (HERE / "pages.json").write_text(
        json.dumps(facts, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")
    said = [t for t, f in facts.items()
            if f["genre_field"] or f["prose_plain"]]
    print("\n%d pages cached; %d name the genre in the infobox or in "
          "unhedged prose; %d only ever compare themselves to it; %d linked "
          "from the genre article"
          % (len(facts), len(said),
             sum(1 for f in facts.values()
                 if not f["genre_field"] and not f["prose_plain"]
                 and f["prose_hedged"]),
             sum(1 for f in facts.values() if f["in_genre_article"])))


if __name__ == "__main__":
    main()
