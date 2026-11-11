#!/usr/bin/env python3
"""Generate properties/code-geass.json.

    PYTHONIOENCODING=utf-8 python tools/make_code-geass.py

Sixty-three entries: the two television seasons, the optional side story, and
the three works of the film continuity — in release order, with every fork
named on the section that forks.

THE FORK, AND WHY THIS LIST REFUSES TO PICK A SIDE
--------------------------------------------------
Code Geass is two stories wearing one name, and a list that hides that lies
to whoever reads it. The 2017–18 trilogy is a compilation of the television
series, but not a faithful one — the trilogy article quotes its own director
saying "while the films are recap of the television series, there are few
changes to the storylines". Those changes are load-bearing. The 2019 film
''Lelouch of the Re;surrection'' is written as a sequel to the FILMS:

    "Lelouch of the Re;surrection takes place in the continuation of the
     series that was first depicted in the three-part compilation film:
     Initiation, Transgression, and Glorification, which was released
     between 2017 and 2018, and serves as a direct sequel to the events of
     the three-part film."

and the 2024 four-part ''Rozé of the Recapture'' article says so even more
bluntly, calling Re;surrection a film "which itself takes place in an
alternate continuity established in the three-part compilation film".

So somebody who watches the fifty television episodes and then reaches for
Re;surrection has changed continuity mid-story without being told. That is
the exact reader this list exists for. Following make_slashers.py, which had
to hold five mutually exclusive Halloween timelines in one list, the answer
is: order by RELEASE — the one order nobody disputes — explain the split in
the section intros, flag it factually on the rows that start or end a
continuity, and never render one route as the correct one. There is no tier
column here for the same reason: a tier would rank the two routes.

Release order happens to keep each continuity contiguous, which is luck
worth stating rather than engineering: television 2006–2016, films 2017–2024.

AKITO THE EXILED IS IN, AND OPTIONAL
------------------------------------
The brief was to include it only if the source treats it as part of the same
work. It does, three times over: the franchise article gives it its own
subsection under Media → Anime, states that "Along with the two seasons of
the television series, the OVAs are licensed by Funimation", and places it
inside the television story's own timeline — "set in Europe during the
Britannian invasion of the continent between Lelouch of the Rebellion's two
seasons". Its own article calls it a spin-off. So it is a section, marked
optional on every row, sitting at its release position with the intro saying
where the source puts it in the story.

WEIGHTS: NONE, AND THAT IS THE WHOLE POINT
------------------------------------------
An unweighted row on a weighted list silently counts as one hour (CLU-131),
so weighting is all-or-nothing. The eight films publish runtimes; the fifty
television episodes and the five OVA episodes do not — the collector records
every RunTime/Length/Duration field it can find in either season article and
finds none, and this build asserts that. Weighting the films and leaving the
episodes bare would have invented fifty hours; applying a series-level
average per episode would have invented a source. So nothing carries `w`,
every mark is one entry, and the film runtimes live in the row notes where
they inform without pretending to measure.

Data: scratch/agent-geass/fetch.py (batched wikitext cache) then
scratch/agent-geass/collect.py -> tools/data/code-geass.json.
"""
import json
import pathlib
import re
import sys
import time
import unicodedata
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop                                          # noqa: E402
from gwlib.prop import join_bits, normt                         # noqa: E402

SLUG = "code-geass"
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "tools" / "data" / "code-geass.json"

ACCENT, ACCENT_DARK = "#4B1D6E", "#B98BE8"

WIKI = "https://en.wikipedia.org/wiki/"

# What each compilation film covers, in the franchise's own numbering. Read
# out of the trilogy article's Plot section by check_source() below rather
# than trusted here; this table only turns it into readable copy.
COVERS = {
    "Initiation": ("Season 1, Episodes 1-17", "season one, episodes 1–17"),
    "Transgression": ("Season 1, Episodes 18-25 and Season 2, Episodes 1-16",
                      "season one from episode 18, then season two through "
                      "episode 16"),
    "Glorification": ("Season 2, Episodes 17-25", "season two, episodes 17–25"),
}


def wiki_url(page):
    """A section link built from the article title the fetch actually
    resolved, so no link is a guess. Rozé needs the accent percent-encoded and
    Re;surrection's semicolon has to survive, which quote() with a safe set
    of ";:" handles."""
    return WIKI + urllib.parse.quote(page.replace(" ", "_"), safe="_;:,()")


def load_json(path, tries=4):
    """Read a JSON file another builder may be mid-write on."""
    for n in range(tries):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            if n == tries - 1:
                raise
            time.sleep(0.4)


def check_source(d):
    """Everything this list asserts about its sources, before it builds."""
    # --- the two seasons are 25 and 25, said twice and counted once --------
    for k in ("1", "2"):
        s = d["seasons"][k]
        assert s["declared_episodes"] == 25, (k, s["declared_episodes"])
        assert len(s["episodes"]) == 25, (k, len(s["episodes"]))
        got = [e["n"] for e in s["episodes"]]
        assert got == list(range(1, 26)), (k, got)
        assert all(e["t"] for e in s["episodes"]), k
    overall = [e["overall"] for k in ("1", "2") for e in d["seasons"][k]["episodes"]]
    assert overall == list(range(1, 51)), overall
    assert d["seasons"]["1"]["first_aired"] == [2006, 10, 6], \
        d["seasons"]["1"]["first_aired"]

    # --- the reason nothing is weighted -----------------------------------
    # If Wikipedia ever starts publishing per-episode runtimes this assert
    # fires, and the right response is to weight the WHOLE list, films
    # included — not to weight the half that already has numbers.
    for k in ("1", "2"):
        assert not d["seasons"][k]["runtime_fields"], \
            "season %s now states runtimes (%s) — reconsider weighting the " \
            "whole list, not half of it" % (k, d["seasons"][k]["runtime_fields"])
    assert not d["akito"]["runtime_field"], d["akito"]["runtime_field"]

    # --- the trilogy: three films, three dates, three runtimes ------------
    t = d["trilogy"]
    labels = [r["label"] for r in t["releases"]]
    assert labels == ["Initiation", "Transgression", "Glorification"], labels
    assert [r["label"] for r in t["runtimes"]] == labels, t["runtimes"]
    assert [r["date"] for r in t["releases"]] == \
        [[2017, 10, 21], [2018, 2, 10], [2018, 5, 26]], t["releases"]
    assert [r["minutes"] for r in t["runtimes"]] == [135, 133, 140], t["runtimes"]
    assert len(t["full_titles"]) == 3, t["full_titles"]
    for short, full in zip(labels, t["full_titles"]):
        assert full.endswith(short), (full, short)

    # --- the trilogy is a compilation, and it changes things --------------
    q = d["quotes"]
    assert "is a compilation of the television series" in q["trilogy_is_compilation"]
    assert "there are few changes to the storylines" in q["trilogy_has_changes"]
    # the article writes its episode ranges with en dashes since 2026, and
    # not consistently ("1-16" kept its hyphen), so compare dash-blind
    coverage = q["trilogy_coverage"].replace("–", "-")
    for short, (stated, _readable) in COVERS.items():
        assert stated in coverage, (short, q["trilogy_coverage"])

    # --- and the sequel follows the FILMS, which is the whole list --------
    assert "serves as a direct sequel to the events of the three-part film" \
        in q["resurrection_follows_films"], q["resurrection_follows_films"]
    assert "takes place in the continuation of the series that was first " \
        "depicted in the three-part compilation film" \
        in q["resurrection_follows_films"], q["resurrection_follows_films"]
    assert "alternate continuity established in the three-part compilation " \
        "film" in q["roze_alternate_continuity"], q["roze_alternate_continuity"]
    assert d["resurrection"]["releases"] == [{"label": "", "date": [2019, 2, 9]}], \
        d["resurrection"]["releases"]
    assert [r["minutes"] for r in d["resurrection"]["runtimes"]] == [114], \
        d["resurrection"]["runtimes"]

    # --- Rozé: four acts, twelve streamed episodes, three per act ---------
    z = d["roze"]
    assert z["acts"] == ["Act 1", "Act 2", "Act 3", "Final Act"], z["acts"]
    assert len(z["releases"]) == 4 and len(z["runtimes"]) == 4, z
    assert [r["date"][0] for r in z["releases"]] == [2024] * 4, z["releases"]
    # every runtime is paired to its act by the label the source prints, not
    # by position in the list — two of the four acts are the same length, so a
    # positional slip would have been invisible
    assert [r["label"] for r in z["releases"]] == z["acts"], z["releases"]
    assert [r["label"] for r in z["runtimes"]] == z["acts"], z["runtimes"]
    assert [r["minutes"] for r in z["runtimes"]] == [74, 76, 76, 74], z["runtimes"]
    assert [r["date"][1] for r in z["releases"]] == [5, 6, 7, 8], z["releases"]
    assert z["ona_episodes"] == 12, z["ona_episodes"]
    assert [z["act_episodes"][a] for a in z["acts"]] == \
        [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]], z["act_episodes"]
    assert "Each film act is divided into three parts" in q["roze_acts_are_episodes"]

    # --- Akito is part of the same work, and the source says where --------
    assert d["akito"]["declared_episodes"] == 5, d["akito"]
    assert len(d["akito"]["episodes"]) == 5, d["akito"]
    assert "spin-off to the main Code Geass series" in q["akito_is_spin_off"]
    assert "between Lelouch of the Rebellion's two seasons" in q["akito_is_side_story"]
    assert "Along with the two seasons of the television series, the OVAs are " \
        "licensed" in q["akito_licensed_with_series"]

    # --- the excluded things exist, so the note naming them is not fiction -
    assert len(d["seasons"]["1"]["recap_specials"]) == 2, \
        d["seasons"]["1"]["recap_specials"]
    picture = sum(len(d["seasons"][k]["picture_dramas"]) for k in ("1", "2"))
    assert picture == 20, picture
    assert d["excluded_named_by_source"]["nunnally_in_wonderland"]
    assert d["excluded_named_by_source"]["miraculous_birthday"]

    # --- the final two episodes of season one shared one broadcast --------
    s1 = d["seasons"]["1"]["episodes"]
    assert s1[23]["date"] == s1[24]["date"] == [2007, 7, 29], (s1[23], s1[24])
    assert "contiguous one-hour broadcast of episodes 24 and 25" \
        in q["s1_double_broadcast"]
    assert "never officially translated into English" in q["recaps_untranslated"], \
        q["recaps_untranslated"]
    return picture


def accent_is_free():
    """No other property may share this list's accent pair (qa_lint rule)."""
    for f in sorted((ROOT / "properties").glob("*.json")):
        if f.name in ("index.json", "search.json", "%s.json" % SLUG):
            continue
        p = load_json(f)
        assert (p.get("accent"), p.get("accentDark")) != (ACCENT, ACCENT_DARK), \
            "accent pair already used by %s" % f.stem


def sync_partners(rows, kind):
    """Rows on other lists that would tick together with rows on this one.

    Reproduces build.py's group key exactly — normalized title, a plain
    four-digit year (falling back to a lone year in the note), and a medium
    letter — rather than approximating it, because an approximation would
    report a reassuring answer that the build does not agree with. Only
    film-kind and game-kind lists take part, so this list has to declare a
    film kind for its eight film rows to pair at all.
    """
    assert "film" in kind or "game" in kind, \
        "kind %r is not syncable — the film rows would never pair" % kind

    def year_of(x, n):
        if re.fullmatch(r"(18|19|20)\d{2}", n):
            return n
        explicit = str(x.get("y", ""))
        if re.fullmatch(r"(18|19|20)\d{2}", explicit):
            return explicit
        found = set(re.findall(r"\b((?:18|19|20)\d{2})\b", x.get("note") or ""))
        return found.pop() if len(found) == 1 else None

    want = {}
    for x in rows:
        y = year_of(x, str(x.get("n", "")))
        if y:
            want.setdefault(normt(x["t"]) + "|" + y + "|f", []).append(x["id"])
    out = {}
    for f in sorted((ROOT / "properties").glob("*.json")):
        if f.name in ("index.json", "search.json", "%s.json" % SLUG):
            continue
        p = load_json(f)
        k = p.get("kind") or ""
        if p.get("secret") or not ("film" in k or "game" in k):
            continue
        medium = "g" if "game" in k else "f"
        for s in p.get("sections", []):
            for x in s.get("items", []):
                y = year_of(x, str(x.get("n", "")))
                if not y:
                    continue
                key = normt(x["t"]) + "|" + y + "|" + medium
                if key in want:
                    out.setdefault(key, []).append((p["slug"], x["id"], p["title"]))
    return want, out


def main():
    d = load_json(DATA)
    picture_dramas = check_source(d)
    accent_is_free()
    kind = "anime & films"

    # ---- the television continuity ---------------------------------------
    def ep_rows(k, prefix):
        out = []
        for e in d["seasons"][k]["episodes"]:
            row = {"id": "%s%d" % (prefix, e["n"]), "t": e["t"], "n": str(e["n"])}
            out.append(row)
        return out

    s1_items = ep_rows("1", "cg-s1e")
    s1_items[23]["note"] = "Broadcast back to back with episode 25 as one hour"
    s1_items[24]["note"] = "Broadcast back to back with episode 24 as one hour"

    r2_items = ep_rows("2", "cg-r2e")
    r2_items[0]["note"] = "Picks up a year after the first season"
    r2_items[24]["note"] = "The end of the television continuity"

    s1 = {
        "id": "s1", "title": "Lelouch of the Rebellion",
        "sub": "2006–07 · 25 episodes · the television continuity starts here",
        "intro": "The television version, and the first of this list's two "
                 "routes through the same events. Twenty-five episodes, "
                 "October 2006 to July 2007. Everything down to Akito the "
                 "Exiled belongs to this continuity; everything from the 2017 "
                 "films down belongs to the other one.",
        "links": [{"label": "Season 1",
                   "url": wiki_url(d["seasons"]["1"]["page"])}],
        "open": True,
        "items": s1_items,
    }
    r2 = {
        "id": "r2", "title": "Lelouch of the Rebellion R2",
        "sub": "2008 · 25 episodes · the television continuity ends here",
        "intro": "Twenty-five more episodes, and the end of the television "
                 "story. No released work continues from this ending: the 2019 "
                 "sequel further down is written as a sequel to the compilation "
                 "films instead, so finishing here and starting there means "
                 "switching versions partway through rather than carrying on.",
        "links": [{"label": "Season 2",
                   "url": wiki_url(d["seasons"]["2"]["page"])}],
        "items": r2_items,
    }

    akito_items = [
        {"id": "cg-akito-%d" % e["n"], "t": e["t"], "n": str(e["n"]), "opt": 1}
        for e in d["akito"]["episodes"]
    ]
    akito_years = [e["date"][0] for e in d["akito"]["episodes"]]
    akito = {
        "id": "akito", "title": "Akito the Exiled",
        "sub": "%d–%d · 5 OVA episodes · optional side story"
               % (akito_years[0], akito_years[-1]),
        "intro": "A spin-off with its own cast, set in Europe — the franchise "
                 "article places it between the two television seasons, and it "
                 "belongs to the television continuity rather than the films'. "
                 "It is here rather than back there because it came out years "
                 "later, in five instalments spread over %d–%d, and because "
                 "nothing in the two seasons depends on it. Optional, and it "
                 "works whether you take it between the seasons or after "
                 "them."
                 % (akito_years[0], akito_years[-1]),
        "links": [{"label": "The OVA series",
                   "url": wiki_url(d["akito"]["page"])}],
        "items": akito_items,
    }

    # ---- the film continuity ---------------------------------------------
    tri = d["trilogy"]
    film_items = []
    for rel, run, full in zip(tri["releases"], tri["runtimes"],
                              tri["full_titles"]):
        short = rel["label"]
        film_items.append({
            "id": "cg-film-%s" % prop.slug(short),
            "t": full, "n": str(rel["date"][0]),
            "note": join_bits(
                "Compilation film",
                "covers %s" % COVERS[short][1],
                "%d minutes" % run["minutes"],
                "The trilogy's version of events is the one the 2019 film "
                "follows" if short == "Glorification" else ""),
        })

    films = {
        "id": "films", "title": "The compilation films",
        "sub": "2017–18 · 3 films · the second continuity starts here",
        "intro": "The trilogy retells both seasons as three theatrical films, "
                 "and it is not a straight recap: the source calls it a "
                 "compilation of the television series, and quotes its "
                 "director saying that while the films are a recap, there are "
                 "changes to the storylines. Those changes are what the 2019 "
                 "sequel below is built on, so this is a second route through "
                 "the same events rather than a quicker version of the first — "
                 "and the two routes do not stay identical. Each row says which "
                 "episodes it covers.",
        "links": [{"label": "The film trilogy",
                   "url": wiki_url(tri["page"])}],
        "items": film_items,
    }

    res = d["resurrection"]
    resurrection = {
        "id": "resurrection", "title": "Lelouch of the Re;surrection",
        "sub": "2019 · 1 film · follows the films, not the series",
        "intro": "New story rather than recap, and the reason the split above "
                 "matters. The source is unambiguous: it takes place in the "
                 "continuation of the series first depicted in the three-part "
                 "compilation film, and serves as a direct sequel to the events "
                 "of that trilogy. Reaching it straight from the television "
                 "finale means changing versions of the story on the way in. "
                 "Watching the trilogy first is what the film is written for.",
        "links": [{"label": "The film", "url": wiki_url(res["page"])}],
        "items": [{
            "id": "cg-film-resurrection", "t": res["title"],
            "n": str(res["releases"][0]["date"][0]),
            "note": join_bits("Sequel to the compilation films",
                              "not to the television seasons",
                              "%d minutes" % res["runtimes"][0]["minutes"]),
        }],
    }

    z = d["roze"]
    roze_items = []
    for i, (rel, run) in enumerate(zip(z["releases"], z["runtimes"])):
        act = rel["label"]
        eps = z["act_episodes"][act]
        roze_items.append({
            "id": "cg-roze-%s" % prop.slug(act),
            "t": "%s – %s" % (z["title"], act),
            "n": str(rel["date"][0]),
            "note": join_bits(
                "Part %d of 4" % (i + 1),
                "streaming episodes %d–%d" % (eps[0], eps[-1]),
                "%d minutes" % run["minutes"],
                "New cast, same continuity as the films above"
                if i == 0 else ""),
        })
    roze = {
        "id": "roze", "title": "Rozé of the Recapture",
        "sub": "2024 · 4 films · continues the film continuity",
        "intro": "Four films with a new cast, and the film continuity's "
                 "current end: the source calls this a sequel to "
                 "Re;surrection, which itself takes place in an alternate "
                 "continuity established by the compilation trilogy. It also "
                 "streamed internationally as twelve episodes, three to an "
                 "act, so one row here is three episodes there — the rows say "
                 "which.",
        "links": [{"label": "The film series", "url": wiki_url(z["page"])}],
        "items": roze_items,
    }

    sections = [s1, r2, akito, films, resurrection, roze]

    # ---- the checks the shipped file has to pass -------------------------
    rows = [x for s in sections for x in s["items"]]
    assert len(rows) == 63, len(rows)
    assert sum(len(s["items"]) for s in (s1, r2)) == 50
    assert len(akito["items"]) == 5 and len(films["items"]) == 3
    assert len(resurrection["items"]) == 1 and len(roze["items"]) == 4
    ids = [x["id"] for x in rows]
    assert len(ids) == len(set(ids)), sorted({i for i in ids if ids.count(i) > 1})
    # all-or-nothing weighting: one `w` anywhere would make every bare row
    # silently weigh an hour (CLU-131)
    assert not any("w" in x for x in rows), [x["id"] for x in rows if "w" in x]
    # only the side story is flagged optional; flagging a whole continuity
    # optional would be this list picking a side
    assert [x["id"] for x in rows if x.get("opt")] == \
        [x["id"] for x in akito["items"]]
    assert not any(x.get("star") for x in rows)
    # sections run in release order, and each is internally ordered
    firsts = [2006, 2008, d["akito"]["episodes"][0]["date"][0], 2017, 2019, 2024]
    assert firsts == sorted(firsts), firsts
    for s in (s1, r2, akito):
        got = [int(x["n"]) for x in s["items"]]
        assert got == sorted(got) == list(range(1, len(got) + 1)), (s["id"], got)
    for s in (films, resurrection, roze):
        years = [int(x["n"]) for x in s["items"]]
        assert years == sorted(years), (s["id"], years)
    # no episode row may carry a lone year in its note: build.py would read it
    # as a film year and try to sync a television episode with a film
    for s in (s1, r2, akito):
        for x in s["items"]:
            found = re.findall(r"\b((?:18|19|20)\d{2})\b", x.get("note") or "")
            assert len(set(found)) != 1, (x["id"], x.get("note"))
    # every row's text is plain display text
    for x in rows:
        for f in ("t", "n", "note"):
            v = x.get(f)
            assert v is None or unicodedata.normalize("NFC", v) == v, (x["id"], f)

    want, partners = sync_partners(rows, kind)
    assert len(want) == 8, sorted(want)          # the eight film rows, no more
    assert not partners, \
        "the catalogue overlap changed — the notes say nothing here is " \
        "shared, but found %s" % {k: v for k, v in partners.items()}

    film_minutes = (sum(r["minutes"] for r in tri["runtimes"])
                    + res["runtimes"][0]["minutes"]
                    + sum(r["minutes"] for r in z["runtimes"]))

    # Excluded things are named, not summarised away. The two recap specials
    # are few enough to list by title; the picture dramas are twenty short
    # bonus tracks and go by count.
    recaps = " and ".join(r["t"] for r in d["seasons"]["1"]["recap_specials"])

    p = {
        "slug": SLUG,
        "title": "Code Geass",
        "subtitle": "the television story, and the film continuity that forks "
                    "away from it",
        "kind": kind,
        "popularity": 72,
        "year": "2006–2024",
        "blurb": "Fifty episodes, eight films and one fork: the film trilogy "
                 "retells the series with changes, and the sequels follow the "
                 "films. Every row says which version it belongs to.",
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ["Two continuities, and this list will not pick one.",
             "The 2017–18 trilogy is described by its own article as a "
             "compilation of the television series, and quotes its director "
             "saying that while the films are a recap, there are changes to "
             "the storylines. Those changes stick: Lelouch of the "
             "Re;surrection is written as a direct sequel to the trilogy, not "
             "to the two seasons, and the Rozé article calls the trilogy's "
             "version an alternate continuity outright. So watching the fifty "
             "episodes and then the 2019 film is not one continuous story, "
             "however much it looks like one — you would be crossing from one "
             "version into another partway through. Both routes are complete "
             "and neither is marked as the right one; the section intros say "
             "what each is, and the rows that start or end a continuity say "
             "so."],
            ["Release order, because no other order is honest.",
             "Two versions of the same events cannot both sit in one "
             "chronology, so this list runs by release date — the one order "
             "nobody argues about, and the order these came out in, each made "
             "in answer to the one before. It falls out neatly: television "
             "2006 to 2016, films 2017 to 2024. There is no tier column here "
             "on purpose, because a tier would rank one route above the "
             "other."],
            ["Akito the Exiled is here, and optional.",
             "A five-part spin-off with its own cast. The franchise article "
             "keeps it with the two seasons — same media section, licensed "
             "together — and places it in the television timeline, between "
             "the two seasons. It sits at its release position rather than at "
             "its story position because it arrived years afterwards and "
             "nothing in the seasons depends on it. Every row is flagged "
             "optional."],
            ["Nothing is weighted.",
             "Every mark is one entry, and an episode and a film count one "
             "each. The eight films publish runtimes and the fifty television "
             "episodes do not — no per-episode length appears anywhere in "
             "either season article — so weighting the films alone would have "
             "quietly counted every unweighted episode as an hour, and "
             "spreading a series-level figure across fifty rows would have "
             "invented a source. The runtimes are in the film rows' notes "
             "instead, where they inform without pretending to measure: %d "
             "minutes of film in all." % film_minutes],
            ["Not included.",
             "The two season-one recap specials, %s, which retell episodes "
             "already on this list and were never officially translated; the "
             "%d picture dramas bundled with the home video releases; the "
             "Nunnally in Wonderland bonus OVA; and The Miraculous Birthday, "
             "a drama film based on a live event. The manga, light novels, "
             "audio dramas and games are out of scope for a watch list. "
             "Nothing on this list is shared with another list in the "
             "catalogue." % (recaps, picture_dramas)],
            "Episode titles, numbering and air dates machine-read from "
            "Wikipedia's two Code Geass season articles and the Akito the "
            "Exiled article; film titles, release dates and runtimes from the "
            "Code Geass, Lelouch of the Rebellion film-trilogy, "
            "Re;surrection and Rozé of the Recapture articles; the continuity "
            "statements quoted above are asserted against those articles "
            "every time this list is rebuilt.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d rows, unweighted (%d minutes of film in the notes)"
          % (out.name, len(rows), film_minutes))
    for s in sections:
        ns = [x["n"] for x in s["items"]]
        print("   %-26s %2d  %s" % (s["title"][:26], len(s["items"]), s["sub"]))
    print("   sync keys offered: %d film rows, %d catalogue partners"
          % (len(want), len(partners)))


if __name__ == "__main__":
    main()
