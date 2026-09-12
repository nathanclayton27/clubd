#!/usr/bin/env python3
"""Generate properties/cult-classics.json.

    python tools/make_cult-classics.py

"Cult classic" is a verdict, and this catalogue does not ship verdicts. So
this list never decides that a film has a cult: it counts how many published
cult-film reference works say so, prints the count on every row, and lets a
reader argue with the count rather than with us.

The gate
--------
Wikipedia's "List of cult films" splits alphabetically across twenty-seven
pages — "0-9" and one per letter — and every entry is a table row of
Film | Year | Director | Source, where Source is a run of footnotes into a
bibliography of published cult-film books and collections. That per-entry
citation is the whole reason this list is built from that article rather than
from a panel assembled by hand the way Body Horror had to be: the aggregation
already exists, it is maintained, and it shows its working.

**A film ships only if at least three of the twenty-three published works
cited there name it as a cult film.** Nothing else qualifies a row, and
nothing that cleared three was dropped for taste.

Twenty-three, not the twenty-five footnotes the article defines: one of those
is Paul Simpson's Rough Guide typed out a second time by hand on the Police
Academy row, which would have let one book count as two, and one is a
magazine piece about a single film that is defined in a bibliography and then
cited by no row at all. Both are asserted below rather than assumed.

Why the raw list is not the deliverable
---------------------------------------
Scale was not the reason. Zombie Films ships 605 rows era by era and reads
well, and 2,821 would only have been more of the same problem if it were a
problem. The reason is that **2,074 of those 2,821 rows rest on a single
citation**, and one book — Paul Simpson's Rough Guide to Cult Movies — supplies
38% of every citation on the article. "One author called it a cult film once"
is exactly the loose entry a gate exists to keep out.

The threshold, honestly
-----------------------
Three is the number Body Horror and the FPS canon already use, so it was the
one to try first — but the whole distribution was on screen before it was
fixed, so this was not chosen blind and should not be presented as if it
were. What settled it was a measure other than the row count: **how much of
each band is only the three longest books agreeing with each other.** At two
or more, 33% of the surviving films cite nothing outside Simpson, Cult Cinema
and Eiss; at three, 9%; at four, none. Three is where a row stops being an
artefact of which books happen to be long.

If the number had been tuned for scale, two was the tempting one — 747 rows
sits nearer Zombie Films' 605 than 326 does — and it was not taken.

Where the gate is weak, said plainly
------------------------------------
  1. **Nothing after 2008 survives it.** The panel is books, and books have
     publication dates: most of these were printed between 2008 and 2011. A
     2015 film has had no time to be written up three times. The newest row
     is In Bruges (2008) and only 18 rows are from this century, which is a
     fact about the bibliography rather than about cinema.
  2. **Four of the twenty-three works have Ernest Mathijs on the cover** (both
     BFI volumes, Cult Cinema, the Routledge companion). Collapse him to one
     voice and 23 rows fall under three — Suspiria, Star Wars, Coffy, My
     Neighbor Totoro, American Psycho among them. So roughly 7% of this list
     needs his four books to count as four. They are four separate acts of
     selection, years apart, with different co-authors, and the FPS canon
     counts GameSpot's 2004 and 2026 lists separately for the same reason —
     but the figure is printed on the page rather than left to be found.
  3. **The panel leans Anglophone.** Two of the works are Everman's cult
     horror and cult science fiction surveys, one is a Japanese cult cinema
     guide, one a Bollywood study, one British. There is no equivalent for
     Hong Kong or Mexican cult cinema, and this list is thinner there than
     the world is.

What the source got wrong, and what this file did about it
-----------------------------------------------------------
Every one of these was forced by the data, not chosen:

  * **The same film is listed twice under two names, eighteen times over.**
    Reefer Madness and Tell Your Children carry the same year and the same
    eight citations; so do House and Hausu, Witchfinder General and The
    Conqueror Worm, Black Sunday and La maschera del demonio, Breathless and
    À bout de souffle, Life of Brian and Monty Python's Life of Brian, and
    twelve more. They are merged on the Wikidata id their own wikilinks
    resolve to, citations unioned, alternate title kept in the note.
  * **The Shining's year cell reads "|1980"** — a stray pipe the table
    renders away and a strict parse rejects. Repaired, not dropped.
  * **The Police Academy row types the Rough Guide out by hand** under a ref
    name of its own rather than reusing the shared one, which would have made
    the same book a twenty-sixth source. Collapsed.
  * **{{sortname|The|Thing|dab=1982 film}} links [[The Thing (1982 film)]]**,
    article and all. Reading the target without the article sent 412 pages to
    a red link and cost every one of them its Wikidata id, The Thing and The
    Wicker Man included. Fixed in scratch/agent-cult/parse.py.
  * **Two rows link the wrong article** — Ivan the Terrible, Part II points at
    the Part I article and Joan the Maid II at Joan the Maid I. Neither clears
    three citations, and the year-agreement rule on merging keeps them two
    rows rather than folding a 1958 film into a 1944 one.
  * **Three rows link something that is not a film.** Legend of the Overfiend
    and Urotsukidoji both link the MANGA article, and Grindhouse links an
    item Wikidata classes as a double feature. The first two matter: two
    citations each, sharing an id, they would have merged into a three-
    citation "film" with no Wikidata item and no runtime behind it. Every id
    is checked against its item's P31 before anything is merged on it, so
    all three lost their id and all three then failed the gate on two
    citations apiece.
  * **One row is a serial and one is a trilogy** — Fantomas (1913-14) and The
    Lord of the Rings (2001-3). Neither is one film with one year, so neither
    can be a row here or pair with anything; both are named in the notes
    rather than faked into a row.

Wikidata ids
------------
A row carries `q`, which build.py groups on ahead of title and year. Every id
was resolved from the wikilink the list article printed itself and then
checked against the item's own P577: a link disagreeing with the row's year by
more than a year loses its id rather than risk ticking a film nobody watched.
Nothing was searched for by title.

That is what collapses the eighteen double-listings, and it is what pairs this
list with the Criterion and Best Picture rows whose years disagree with this
article's by exactly one — Casablanca, Salò, If.…, Blood Simple, Slacker,
Crumb and the rest. Neither list is wrong; they cite different releases.

Where the source names a film twice, the article title behind that id also
breaks the tie: Black Sunday over La maschera del demonio, House over Hausu.
That rule applies ONLY to merges. Run over every row it would rename Q – The
Winged Serpent to "Q" and Dr. Strangelove to its short form, so the source's
own display title stands everywhere it is unambiguous.

Weights: the film's own infobox, not Wikidata (CLU-365)
-------------------------------------------------------
Every row is weighted, and every weight is the runtime printed in that film's
own {{Infobox film}}, read by scratch/agent-cult/infobox_runtimes.py from the
article the list's own wikilink points at. All 326.

It used to be Wikidata's P2047 for 325 of them, and that was wrong in a way
nothing on the page could show. gwlib.wikidata.runtime() takes the LONGEST
figure an item carries, and P2047 collects every cut a film has ever been
given, so the figure reaches unrated and extended versions: this list shipped
*Enter the Dragon* at 98 minutes while the film's own article says 102, cited
to the BBFC — and the bruce-lee list, weighted from infoboxes, said 102. Two
lists disagreeing about how long one film is will disagree about hours
forever, so one source had to win, and the infobox wins for three reasons:

  * it is the article's own claim about the film, cited on the page, and it is
    what every list built since reads;
  * it names the version — "(theatrical)", "(final cut)", "(1998 version)" —
    where P2047 is a bare number with the provenance stripped off;
  * it is already the source for the two rows this list had to read by hand
    (below), so following it everywhere removes an exception rather than
    adding one.

**Where a box prints more than one cut, the FIRST figure is taken** — the
version the article leads with, which is the original release in every case
but the handful the generator prints. Seventeen boxes list more than one, and
the generator prints each of them with the figure it took, so the choice is
visible rather than buried. The scrubbed field text is stored on every row in
tools/data/cult-classics.json (`infobox_raw`) so any figure can be checked
against the words beside it.

Moving to the infobox changed 153 of the 326 weights, 52 of them by a single
minute and the largest by more than an hour: *Martin* 165 to 95, *Das Boot*
209 to 149, *Donnie Darko* 134 to 113 — every one of them P2047 reporting a
longer cut than the film had in cinemas. Both of the old hand-read exceptions
now come out of the same pipeline as everything else and are unchanged by it:
Ganja & Hess still weighs the 113 minutes its box prints above a 78-minute
recut, and Invocation of My Demon Brother, a Kenneth Anger short the cult
books carry, still weighs 11.

P2047 is kept in the data beside each infobox figure rather than thrown away,
so the gap stays measurable — and it is the documented fallback if a box ever
stops publishing a runtime. No runtime was estimated anywhere; a row with
neither figure stops this generator.

Deliberate overlaps
-------------------
This list collides with Criterion hardest, then Sight & Sound, Best Picture,
Zombie Films, Bad Movie Night, Cronenberg, Body Horror and a couple of dozen
director lists. That is cross-list sync working — a survey of what got a cult
and a filmography answer different questions, and one tick should serve both.
The generator counts the groups that actually form, fails if the big ones do
not, and prints every near-miss it can see.

Data: scratch/agent-cult/{fetch,parse,collect,collect2,runtime_fix,titles}.py
-> tools/data/cult-classics.json
"""
import collections
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop as P, wiki  # noqa: E402

SLUG = "cult-classics"
DATA = pathlib.Path(__file__).resolve().parent / "data" / ("%s.json" % SLUG)

# The gate: how many of the published cult-film works must name a film.
# 23 is what the article's bibliographies actually cast citations with. It
# defines 25 footnotes: one is a duplicate of the Rough Guide typed out by
# hand (see SAME_SOURCE) and one, a magazine piece about a single film, is
# defined and then never cited by any row. Counting either would inflate the
# denominator without any film being able to reach it.
MIN_SOURCES = 3
PANEL = 23
UNCITED = frozenset(("publika",))

ACCENT, ACCENT_DARK = "#7D2483", "#DE86E8"

# The Police Academy row types the Rough Guide out by hand under its own ref
# name instead of reusing "simpson". Same book; it must not count twice.
SAME_SOURCE = {"Paul Simpson 2010": "simpson"}

# Clears the gate, but is not one film with one year — so it cannot be a row
# here and cannot pair with anything. Named in the notes rather than dropped
# in silence.
NOT_A_FILM = {
    "Fantômas": "a 1913-14 serial in five parts",
    "The Lord of the Rings": "the 2001-3 trilogy on one row",
}

# The four works with Ernest Mathijs on the cover. They count separately;
# this exists so the generator can print how much of the roster needs them to.
MATHIJS = frozenset(("bfi", "bfi2", "cultcinema", "routledge"))

ERAS = [
    ("silent", "Before the term existed", None, 1949,
     "Nothing in this section was called a cult film when it opened — the "
     "phrase does not reach print until the 1970s. These are the pictures "
     "the later books reached back for: silents, studio-era oddities and "
     "poverty-row horror, kept in circulation by repertory houses and "
     "late-night television long enough for somebody to write them down."),
    ("drivein", "The drive-in decade", 1950, 1959,
     "The second feature, the double bill and the monster picture built for "
     "a car park. Ten years that put almost as many films on this list as "
     "the thirty before them did."),
    ("underground", "Underground and exploitation", 1960, 1969,
     "Modern cult cinema starts here: 1960s counterculture, the underground "
     "film scene and the festivals it threw, running alongside a grindhouse "
     "trade making the films the studios would not."),
    ("midnight", "The midnight-movie years", 1970, 1979,
     "Those festivals turn into the midnight movie, and the midnight movie "
     "peaks with The Rocky Horror Picture Show in 1975 — a film that found "
     "its audience years after it opened. The largest section here, and the "
     "decade the term itself was coined in."),
    ("videostore", "The video store", 1980, 1989,
     "Home video ends the midnight movie and replaces it with something "
     "wider: a shelf that keeps a flop in circulation, and a cable schedule "
     "that replays it until an audience turns up."),
    ("after", "After the video store", 1990, None,
     "Independent film, the rental chains, then the internet. This section "
     "thins fast after 2000 and stops in 2008 — not because cinema stopped, "
     "but because the books did. A cult takes years to be written down three "
     "separate times."),
]


def era_of(year):
    for key, _t, lo, hi, _i in ERAS:
        if (lo is None or year >= lo) and (hi is None or year <= hi):
            return key
    raise AssertionError("no era holds %r" % year)


def bare(title):
    """An article title without its disambiguator: House (1977 film) -> House."""
    return re.sub(r"\s*\([^()]*\)$", "", title).strip()


def year_of(x, n):
    """build.py's rule for a film row's sync year: `n` when it is a plain
    year, else `y`, else the single year in the note, else nothing."""
    if re.fullmatch(r"(18|19|20)\d{2}", n):
        return n
    ex = str(x.get("y", ""))
    if re.fullmatch(r"(18|19|20)\d{2}", ex):
        return ex
    found = set(re.findall(r"\b((?:18|19|20)\d{2})\b", x.get("note") or ""))
    return found.pop() if len(found) == 1 else None


def catalogue():
    """Every syncable film row already in the catalogue, as build.py sees it:
    (slug, id, normalized title, year or None, q or None, raw title)."""
    out = []
    for f in sorted((P.ROOT / "properties").glob("*.json")):
        if f.name in ("index.json", "search.json", "%s.json" % SLUG):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("secret") or "film" not in (d.get("kind") or ""):
            continue
        for s in d.get("sections", []):
            for x in s.get("items", []):
                y = year_of(x, str(x.get("n", "")))
                q = x.get("q")
                out.append((d["slug"], x["id"], P.normt(x["t"]),
                            int(y) if y else None,
                            q if isinstance(q, str) else None, x["t"]))
    return out


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    panel, rows, facts, titles = d["panel"], d["rows"], d["facts"], d["titles"]
    kinds = d["kinds"]

    # ---- the panel is the one this file describes -------------------------
    defined = {SAME_SOURCE.get(k, k) for k in panel}
    for r in rows:
        r["refs"] = sorted({SAME_SOURCE.get(x, x) for x in r["refs"]})
        r["n"] = len(r["refs"])
        assert r["refs"] and set(r["refs"]) <= defined, r["t"]
    names = {x for r in rows for x in r["refs"]}
    assert defined - names == UNCITED, \
        "the uncited-source list is stale: %s" % sorted(defined - names)
    assert len(names) == PANEL, \
        "the article cites %d distinct works, this file says %d" % (
            len(names), PANEL)
    assert len(rows) == 2821, "the article carries %d rows" % len(rows)
    # The hand-typed Rough Guide duplicate sits on a row that cites nothing
    # else, so collapsing it changes the panel without changing this total.
    assert sum(r["n"] for r in rows) == 4252, "citation total moved"
    singles = sum(1 for r in rows if r["n"] == 1)
    assert singles == 2074, singles

    # ---- an id is only usable if the item behind it is a film -------------
    # The wikilink is the article's own, but an article is not always the
    # film. "Legend of the Overfiend" and "Urotsukidoji" both link the MANGA
    # article, and merging on that id would have added up two rows of two
    # citations into a film that does not exist as a Wikidata item at all.
    # An id whose P31 classes never say "film" is dropped here, BEFORE the
    # merge, so it can never be a merge key either.
    # `kinds` is carried only for the items a row could ever reach the gate
    # with, so an unclassified id belongs to a single-citation row: two of
    # those merging still comes to two, and the roster assert below refuses
    # any id that never got classified.
    notfilm = []
    for r in rows:
        ks = kinds.get(r["q"]) if r["q"] else None
        if ks is not None and not any("film" in k.lower() for k in ks):
            notfilm.append((r["t"], r["year"], ks))
            r["q"] = None

    # ---- merge the rows that are one film listed under two names ----------
    # Keyed on the Wikidata id the row's OWN wikilink resolved to, and only
    # where the two rows also agree on the year — so Ivan the Terrible Part I
    # and Part II, which share an article because the list links the wrong
    # one, stay two rows and then fail the gate on their own merits.
    by_work, merges = {}, []
    for r in rows:
        key = (r["q"] or "t:" + P.normt(r["t"] or ""), r["year"])
        if key in by_work:
            first = by_work[key]
            first["refs"] = sorted(set(first["refs"]) | set(r["refs"]))
            first["n"] = len(first["refs"])
            first["names"].append(r["t"])
            merges.append((first["names"][0], r["t"], r["year"], first["n"]))
        else:
            by_work[key] = dict(r, names=[r["t"]])
    works = list(by_work.values())
    assert len(works) + len(merges) == len(rows)

    # ---- the gate decides membership, and nothing else --------------------
    gated = [w for w in works if w["n"] >= MIN_SOURCES]
    cut = len(works) - len(gated)
    merged_in = [m for m in merges if m[3] >= MIN_SOURCES]

    # Everything with no single year must be named here, whether or not it
    # cleared the gate — the Fantomas serial is stopped by the citation count
    # first and the trilogy row only by this, and both are stated on the page.
    yearless = {w["t"] for w in works if not w["year"]}
    assert yearless == set(NOT_A_FILM), \
        "NOT_A_FILM and the source disagree: %s" % sorted(
            yearless ^ set(NOT_A_FILM))
    dropped = [w for w in gated if w["t"] in NOT_A_FILM]
    assert len(dropped) == 1 and dropped[0]["t"] == "The Lord of the Rings", \
        "the notes say only the trilogy row clears the gate: %s" % dropped
    gated = [w for w in gated if w["t"] not in NOT_A_FILM]
    assert all(w["year"] for w in gated), "a gated row with no year"

    # ---- ids: the source's own link, and only where the year agrees -------
    refused = []
    for w in gated:
        ys = (facts.get(w["q"]) or {}).get("pub_years") or []
        if w["q"] and ys and min(abs(y - w["year"]) for y in ys) > 1:
            refused.append((w["t"], w["year"], sorted(ys)))
            w["q"] = None
    qs = [w["q"] for w in gated if w["q"]]
    assert len(qs) == len(set(qs)), \
        "two rows share a Wikidata id: %s" % [q for q in qs
                                              if qs.count(q) > 1][:3]
    for q in qs:
        assert any("film" in k.lower() for k in kinds.get(q, [])), \
            "%s ships an id that was never classified as a film" % q

    # ---- titles: the source's, except where the source gives two ----------
    for w in gated:
        if len(w["names"]) > 1:
            art = bare(titles.get(w["q"], "")) or w["names"][0]
            w["t"] = next((c for c in w["names"]
                           if P.normt(c) == P.normt(art)), art)
        w["aka_all"] = [a for a in ([w["aka"]] if w["aka"] else []) + w["names"]
                        if P.normt(a) != P.normt(w["t"])]

    # ---- weights: the film's own infobox, all-or-nothing (CLU-131/365) ----
    # The film's own {{Infobox film}} decides how long the film is. Wikidata's
    # P2047 stays in the data beside it, unused unless a box publishes no
    # figure at all, because P2047 is the longest cut an item carries and that
    # is not the same question.
    fallbacks, drift, multi = [], [], []
    for w in gated:
        f = facts.get(w["q"]) or {}
        ib, wd = f.get("infobox_runtime"), f.get("runtime")
        if ib:
            w["runtime"], w["runtime_src"] = ib, "infobox"
            if wd and wd != ib:
                drift.append((abs(wd - ib), w["t"], wd, ib))
            if (f.get("infobox_figures") or 1) > 1:
                multi.append((w["t"], f["infobox_figures"], ib,
                              f.get("infobox_raw") or ""))
        else:
            w["runtime"], w["runtime_src"] = wd, "wikidata"
            fallbacks.append(w["t"])
        assert w["runtime"], "no sourced runtime for %s (%d)" % (w["t"],
                                                                 w["year"])
        assert 5 <= w["runtime"] <= 250, \
            "%s runtime %r is not credible" % (w["t"], w["runtime"])
    # Today every row comes from its own infobox, and the note says so without
    # hedging. If a box loses its runtime field this fails rather than quietly
    # reintroducing a Wikidata figure — re-run
    # scratch/agent-cult/infobox_runtimes.py first, in case the article simply
    # was not re-fetched.
    assert not fallbacks, \
        ("%d rows have no runtime in their own infobox and would fall back to "
         "Wikidata's longest cut: %s. Re-run "
         "scratch/agent-cult/infobox_runtimes.py; if the box really has no "
         "figure, say so in the runtime note before letting it through."
         % (len(fallbacks), fallbacks[:6]))
    assert {w["runtime_src"] for w in gated} == {"infobox"}, \
        sorted({w["runtime_src"] for w in gated})
    drift.sort(reverse=True)
    # Two claims the runtime note makes about the shape of that drift, held to
    # the data rather than to whoever wrote the sentence.
    assert all(ib < wd for _d, _t, wd, ib in drift[:3]), \
        ("the note says the three biggest moves are all Wikidata reporting a "
         "longer cut than the release; they are %s" % drift[:3])
    up = max(drift, key=lambda d: d[3] - d[2])
    assert up[1] == "Touch of Evil", \
        ("the note names Touch of Evil as the one large move the other way; "
         "the biggest is now %s" % (up,))

    # ---- rows -------------------------------------------------------------
    gated.sort(key=lambda w: (w["year"], P.normt(w["t"])))
    entries, seen = [], set()
    for w in gated:
        akas, seen_aka = [], set()
        for a in w["aka_all"]:
            if P.normt(a) not in seen_aka:
                seen_aka.add(P.normt(a))
                akas.append(a)
        base = "cult-%d-%s" % (w["year"], P.slug(w["t"]))
        iid, k = base, 2
        while iid in seen:
            iid, k = "%s-%d" % (base, k), k + 1
        seen.add(iid)
        x = {"id": iid, "t": w["t"], "n": str(w["year"]),
             "w": round(w["runtime"] / 60.0, 2),
             "note": P.join_bits(
                 "%d of %d sources" % (w["n"], PANEL),
                 # the Director cell is wikitext: [[Hugh Wilson (director)|
                 # Hugh Wilson]], {{sortname}}, footnotes. Never hand-stripped.
                 wiki.clean(w["director"]) or None,
                 "%d min" % w["runtime"],
                 "also known as %s" % ", ".join(akas) if akas else None)}
        if w["q"]:
            x["q"] = w["q"]
        entries.append(dict(x, era=era_of(w["year"]), year=w["year"],
                            sources=w["n"], runtime=w["runtime"]))

    years = [e["year"] for e in entries]
    assert years == sorted(years), "the roster is out of release order"
    # a note must never offer build.py a second year to sync on
    for e in entries:
        assert not re.search(r"\b(18|19|20)\d{2}\b", e["note"]), \
            "a year leaked into %s's note: %r" % (e["id"], e["note"])
    total_min = sum(e["runtime"] for e in entries)

    # ---- sections ---------------------------------------------------------
    sections = []
    for key, title, lo, hi, intro in ERAS:
        got = [e for e in entries if e["era"] == key]
        assert got, "empty era %s" % key
        assert all((lo is None or e["year"] >= lo)
                   and (hi is None or e["year"] <= hi) for e in got), key
        sections.append({
            "id": key, "title": title,
            "sub": " · ".join([
                "%d–%d" % (got[0]["year"], got[-1]["year"]),
                "%d films" % len(got),
                "%d hours" % round(sum(e["runtime"] for e in got) / 60.0)]),
            "intro": intro,
            "items": [{k: v for k, v in e.items()
                       if k in ("id", "t", "n", "w", "note", "q")}
                      for e in got]})
    sections[0]["open"] = True

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)) == len(entries)

    # ---- the accent pair is ours alone ------------------------------------
    for f in sorted((P.ROOT / "properties").glob("*.json")):
        if f.name in ("index.json", "search.json", "%s.json" % SLUG):
            continue
        o = json.loads(f.read_text(encoding="utf-8"))
        assert (o.get("accent"), o.get("accentDark")) != (ACCENT, ACCENT_DARK)
        assert o.get("accent") != ACCENT, \
            "%s already uses accent %s" % (o.get("slug"), ACCENT)

    # ---- the overlaps have to actually group ------------------------------
    mine_year = {(P.normt(e["t"]), e["year"]) for e in entries}
    mine_keys = {k for k, _y in mine_year}
    mine_q = {e["q"] for e in entries if e.get("q")}
    by_year = collections.defaultdict(list)
    for e in entries:
        by_year[e["year"]].append(P.normt(e["t"]))
    groups, near, variants = collections.defaultdict(set), [], []
    for slug, _iid, key, year, q, raw in catalogue():
        if q and q in mine_q:
            groups[q].add(slug)
        elif (key, year) in mine_year:
            groups["%s|%s" % (key, year)].add(slug)
        elif key in mine_keys and year:
            near.append((raw, slug, year,
                         sorted(y for k, y in mine_year if k == key)))
        elif year:
            # The other near miss, and the harder one to see: same film, same
            # year, one list spelling the title longer than the other —
            # Nosferatu against Nosferatu: A Symphony of Horror. A prefix
            # match on the same year finds them; an id on both lists is the
            # only thing that actually pairs them.
            for k in by_year.get(year, ()):
                if k != key and (k.startswith(key + " ")
                                 or key.startswith(k + " ")):
                    variants.append((raw, slug, year, k))
    for slug in ("criterion", "sight-and-sound", "best-picture",
                 "zombie-films", "bad-movie-night", "body-horror",
                 "cronenberg", "carpenter", "palme-dor", "david-lynch"):
        assert any(slug in v for v in groups.values()), \
            "no sync group forms with %s" % slug
    lists_met = {s for v in groups.values() for s in v}

    # ---- the era framing must not outrun the article it came from ---------
    ctx = P.ROOT / "scratch" / "agent-cult" / "Cult-film.wiki"
    if ctx.exists():
        t = ctx.read_text(encoding="utf-8")
        for claim in ("first used in the 1970s",
                      "led to the creation of [[midnight movie]]s",
                      "peaking with the release of ''[[The Rocky Horror "
                      "Picture Show]]'' (1975)",
                      "rise of home video marginalized midnight movies"):
            assert claim in t, "the era framing outran its source: %r" % claim

    top = max(entries, key=lambda e: e["sources"])
    at_gate = sum(1 for e in entries if e["sources"] == MIN_SOURCES)
    modern = [e for e in entries if e["year"] >= 2000]
    newest, oldest = entries[-1], entries[0]
    leaners = sum(1 for w in gated
                  if len({"M" if x in MATHIJS else x
                          for x in w["refs"]}) < MIN_SOURCES)
    sizes = collections.Counter()
    for r in rows:
        for s in r["refs"]:
            sizes[s] += 1
    top3 = set(s for s, _ in sizes.most_common(3))

    def only_big(g):
        band = [w for w in works if w["n"] >= g]
        return round(100 * sum(1 for w in band if set(w["refs"]) <= top3)
                     / len(band))

    shortest = min(entries, key=lambda e: e["runtime"])
    longest = max(entries, key=lambda e: e["runtime"])
    biggest = max(sections, key=lambda s: len(s["items"]))

    prop = {
        "slug": SLUG,
        "title": "Cult Classics",
        "subtitle": "the films the cult-film books agree on, era by era",
        "kind": "films",
        # "Cult classic" is a phrase a general audience uses without being
        # told what it means, and the roster holds Blade Runner, The Shining
        # and Rocky Horror — but it is a thematic survey rather than a
        # flagship, which is the 40-59 band in POPULARITY.md. Set just above
        # its neighbours Zombie Films (52) and Body Horror (50) because the
        # term travels further than either genre's does, and below the
        # Criterion Collection (63) it overlaps most heavily, per that file's
        # second signal.
        "popularity": 55,
        "year": "%d–%d" % (oldest["year"], newest["year"]),
        "blurb": "%d films that at least %d of %d published cult-film "
                 "reference works call a cult film, era by era from %d to "
                 "%d — about %d hours. No order; let the picker choose."
                 % (len(entries), MIN_SOURCES, PANEL, oldest["year"],
                    newest["year"], round(total_min / 60.0)),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "random": True,
        "notes": [
            ["“Cult classic” is a verdict, so this list does not pass one.",
             "A film is here only if at least %d of the %d published works "
             "Wikipedia's “List of cult films” cites name it as one: Danny "
             "Peary's three Cult Movies volumes, the BFI's two 100 Cult "
             "Films, Mathijs and Sexton's Cult Cinema and its Routledge "
             "companion, the Rough Guide to Cult Movies, 500 Essential Cult "
             "Movies, 100 Greatest Cult Films, 101 Cult Movies You Must See "
             "Before You Die, surveys of cult horror, cult science fiction, "
             "Japanese cult cinema and Bollywood, TCM Underground, a Rotten "
             "Tomatoes book, and the Criterion Collection's own Cult Movies "
             "shelf. Nothing was added because it felt right and nothing "
             "that cleared %d was dropped. The count rides on every row, so "
             "you can argue with it: %s leads with %d of the %d, and %d rows "
             "clear the gate with exactly %d."
             % (MIN_SOURCES, PANEL, MIN_SOURCES, top["t"], top["sources"],
                PANEL, at_gate, MIN_SOURCES)],
            ["Why the whole list is not here.",
             "That article carries %s entries — %s distinct films once the "
             "same-film double-listings fold together — and %s of those "
             "entries rest on a single citation, one author saying it once, "
             "while a single book supplies %d%% of every citation on the "
             "article. Scale was not the problem; %s rows would have read "
             "fine. The looseness was. So the threshold was set on a "
             "different measure than the row count: at two citations, %d%% "
             "of the surviving films cite nothing outside the three longest "
             "books; at three, %d%%; at four, none. Three is where a row "
             "stops being an artefact of which books happen to be long. It "
             "cut %s of the %s."
             % ("{:,}".format(len(rows)), "{:,}".format(len(works)),
                "{:,}".format(singles),
                round(100 * sizes.most_common(1)[0][1] / sum(sizes.values())),
                "{:,}".format(len(rows)), only_big(2), only_big(MIN_SOURCES),
                "{:,}".format(cut), "{:,}".format(len(works)))],
            ["Nothing after 2008 clears it, and that is about books.",
             "The sources are reference works, and reference works have "
             "publication dates — most of these were printed between 2008 "
             "and 2011. A film needs years and three separate authors before "
             "it can appear here, so the newest row is %s (%d) and only %d "
             "of the %d are from this century. Read that as a fact about the "
             "bibliography rather than a claim that cinema stopped making "
             "them." % (newest["t"], newest["year"], len(modern),
                        len(entries))],
            ["Where the gate is weakest.",
             "Four of the %d works have Ernest Mathijs on the cover — both "
             "BFI volumes, Cult Cinema and the Routledge companion. Collapse "
             "him to one voice and %d rows fall below three, Suspiria and "
             "Star Wars among them, so about %d%% of this list needs those "
             "four books to count as four. They are four separate acts of "
             "selection, years apart, with different co-authors, which is "
             "why they do count separately — but the number belongs in the "
             "open. The panel leans Anglophone too: there is a Japanese "
             "guide and a Bollywood study on it and no equivalent for "
             "anywhere else."
             % (PANEL, leaners, round(100 * leaners / len(entries)))],
            ["Bar widths are runtimes, and none was invented.",
             "All %d rows are weighted, %d hours in total, and every figure "
             "is the runtime printed in that film's own Wikipedia infobox — "
             "all %d of them, with no exceptions and nothing estimated. The "
             "range runs from %s at %d minutes, a short the cult books carry "
             "and a feature filter would have thrown out, to %s at %d. A "
             "missing runtime stops this list being built rather than being "
             "guessed at."
             % (len(entries), round(total_min / 60.0), len(entries),
                shortest["t"], shortest["runtime"], longest["t"],
                longest["runtime"])],
            ["Why the infobox and not Wikidata.",
             "This list used to weigh %d of its %d rows from Wikidata's "
             "runtime property, which is what a list of this size reaches for "
             "— one query, every film. The trouble is that the property "
             "collects every cut a film has ever had and the reader takes the "
             "longest, so the bars quietly measured unrated and extended "
             "versions: Enter the Dragon showed 98 minutes where its own "
             "article says 102, cited to the BBFC, and the Bruce Lee list "
             "here said 102 as well. Two lists cannot disagree about how long "
             "one film is, so the film's own infobox wins — it is the "
             "article's own cited claim and it says which version it means. "
             "Reading all %d that way moved %d of them — %d by a single "
             "minute, %d up and %d down, and the largest by more than an hour "
             "(Martin from %d to %d, Das Boot from %d to %d). The small "
             "moves go both ways; the three biggest are all the same thing, "
             "Wikidata reporting a cut longer than the film had in cinemas. "
             "The one large move the other way is Touch of Evil, whose own "
             "box leads with the 1998 re-edit rather than the 1958 release: "
             "the rule takes the article at its word there too. Where a box "
             "lists more than one cut — %d of them do — the first figure is "
             "taken, which is the version the article leads with."
             % (len(entries) - 1, len(entries), len(entries), len(drift),
                sum(1 for d, _t, _a, _b in drift if d == 1),
                sum(1 for _d, _t, a, b in drift if b > a),
                sum(1 for _d, _t, a, b in drift if b < a),
                next(a for _d, tt, a, _b in drift if tt == "Martin"),
                next(b for _d, tt, _a, b in drift if tt == "Martin"),
                next(a for _d, tt, a, _b in drift if tt == "Das Boot"),
                next(b for _d, tt, _a, b in drift if tt == "Das Boot"),
                len(multi))],
            ["The source lists some films twice, and the ids sort it out.",
             "Reefer Madness and Tell Your Children are one 1936 film with "
             "one set of eight citations; so are House and Hausu, "
             "Witchfinder General and The Conqueror Worm, Black Sunday and "
             "La maschera del demonio, Breathless and À bout de souffle. %d "
             "such pairs were merged on the Wikidata id their own wikilinks "
             "resolve to, with the other name kept in the note. Two entries "
             "are not single films at all — the Fantomas serial and the Lord "
             "of the Rings trilogy — and are left out rather than squeezed "
             "onto one row." % len(merged_in)],
            ["The same film on two lists here is the point.",
             "This list overlaps the Criterion Collection hardest, then "
             "Sight & Sound, Best Picture, Zombie Films, Bad Movie Night and "
             "a couple of dozen director lists — %d shared films across %d "
             "of them, and ticking one ticks the other. Where two lists date "
             "a film differently, as Criterion and Best Picture do for "
             "Casablanca, Salò and Blood Simple, a Wikidata id pairs them "
             "anyway — and every one of these %d rows carries one, each "
             "resolved from the link the source article printed itself."
             % (len(groups), len(lists_met), len(entries))],
            "Contents from Wikipedia's “List of cult films” and its 27 "
            "alphabetical pages, counted per entry against the %d published "
            "works cited there; era framing from Wikipedia's “Cult film”; "
            "ids and runtimes resolved from each entry's own wikilink via "
            "Wikidata." % PANEL,
        ],
        "sections": sections,
    }

    P.write(prop)

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d films — all weighted from their own infoboxes, "
          "%d min (%.1f hours)"
          % (len(sections), len(ids), total_min, total_min / 60.0))
    print("  runtimes: %d from the film's own infobox, %d fell back to "
          "Wikidata P2047" % (len(entries) - len(fallbacks), len(fallbacks)))
    print("  %d disagree with P2047 (infobox first, P2047 second):"
          % len(drift))
    for d, tt, wd, ib in drift:
        print("   %+5d  %-44s %4d -> %4d" % (ib - wd, tt[:44], wd, ib))
    print("  %d boxes print more than one cut; the first is taken:"
          % len(multi))
    for tt, cuts, ib, raw in sorted(multi):
        print("   %-40s %d figures, took %-4s %s" % (tt[:40], cuts, ib,
                                                     raw[:70]))
    print("  gate: >=%d of %d published works — %s entries fold into %s "
          "distinct films, %s cut (%d merged pairs)"
          % (MIN_SOURCES, PANEL, "{:,}".format(len(rows)),
             "{:,}".format(len(works)), "{:,}".format(cut), len(merged_in)))
    print("  ids: %d of %d rows carry one, %d refused by the year gate"
          % (len(qs), len(entries), len(refused)))
    for t, y, ys in refused:
        print("    refused %-34s row %s vs P577 %s" % (t, y, ys))
    for s in sections:
        print("   %-30s %3d  %s" % (s["title"], len(s["items"]), s["sub"]))
    print("  %d sync groups across %d other lists:"
          % (len(groups), len(lists_met)))
    for s, n in collections.Counter(
            s for v in groups.values() for s in v).most_common(14):
        print("   %-24s %3d" % (s, n))
    print("  near misses — same title, a different year (%d):" % len(near))
    for raw, slug, year, ours in sorted(near):
        print("   %-36s %-20s theirs=%s ours=%s" % (raw, slug, year, ours))
    print("  title variants — same year, a longer or shorter name (%d):"
          % len(variants))
    for raw, slug, year, k in sorted(set(variants)):
        print("   %-36s %-20s %s  ours=%r" % (raw, slug, year, k))
    if notfilm:
        print("  ids refused because the article is not a film (%d):"
              % len(notfilm))
        for t, y, ks in notfilm:
            print("   %-36s %s  %s" % (t, y, ks))
    assert biggest["id"] == "midnight", biggest["id"]
    # the drive-in intro's one countable claim
    n50 = len([e for e in entries if 1950 <= e["year"] <= 1959])
    n_before = len([e for e in entries if e["year"] < 1950])
    assert 0.8 * n_before <= n50 < n_before, (n50, n_before)


if __name__ == "__main__":
    main()
