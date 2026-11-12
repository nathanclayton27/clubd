#!/usr/bin/env python3
"""Generate properties/korean-cinema.json.

    python tools/make_korean-cinema.py

"The best of Korean cinema" is a verdict, and this catalogue does not ship
verdicts. So this list never decides that a Korean film is one of the best: it
takes the selection Korea's own national film archive made, and, for the years
that selection could not reach, counts how many of Korea's film juries have
since named a film. Both figures ride on every row, so a reader can argue with
either one.

The gate
--------
**A film is here if the Korean Film Archive's 2014 selection of 100 Korean
films named it, or — released after that selection closed — if at least two of
Korea's eight film juries have since named it.**

Clause one is the spine. KOFA is the country's sole national film archive, a
government body founded in 1974, and its "100 Korean Films" is the closest
thing Korean cinema has to a native canon: one considered survey of the whole
history rather than a prize for one year. The archive publishes it itself, at
eng.koreafilm.or.kr, with a director, a release year and — this is what makes
it usable here — a KMDb identifier per row, KMDb being the archive's own
database. Nothing on this list was matched by title.

Clause two exists because that selection was made in 2014 and its newest entry
is Pietà (2012). Parasite could not have been on it. Neither could Burning.
The films released since are admitted only where at least two of these eight
agree, each of which is a record of what a Korean institution chose rather
than an opinion this file formed:

    Blue Dragon · Grand Bell · Baeksang · Buil · Chunsa · the Korean Film
    Awards · the Korean Association of Film Critics — Best Film in each — and
    the committee that picks the country's Academy Award entry.

Why not a flat count across all nine
------------------------------------
It was tried first, because a single countable number per row is what
cult-classics ships and it is the better shape. The distribution killed it:
at "two of nine", THE HOUSEMAID falls out. The archive's own number one — the
film Wikipedia's article on Korean cinema names as one of the two best the
country has made — would have been cut for winning no year-prize in 1960.
So would 3-Iron, Chunhyang and sixty-eight other archive selections. A flat
count only works when the sources are the same kind of thing, as
cult-classics' twenty-three books are. One considered canon and seven annual
prizes are not, and averaging them lies about both.

Why two and not one, in clause two
----------------------------------
At one jury the modern section grows from 20 rows to 37 and takes in Revolver,
Smugglers, Harbin and Next Sohee. Every one of those is a real prize honestly
won; none of them is what somebody means by the best of Korean cinema. Two
is where a modern row stops being one jury's pick of one year. It is not tuned for scale: three
would give 8 rows and would drop Burning, which is the check that says a gate
is wrong.

The sanity checks, and what the gate refuses
--------------------------------------------
All four obvious ones clear it without being special-cased, and the generator
asserts each with its reason so a future edit cannot quietly lose one:

  * **Oldboy** (2003) — the archive selected it, as "Old Boy". It also won the
    Korean Film Awards' Best Film and the critics' association's.
  * **Memories of Murder** (2003) — the archive ranked it eighth, the highest
    of any film made this century.
  * **Parasite** (2019) — six of the eight juries, more than any other film
    here.
  * **Burning** (2018) — two: the Grand Bell's Best Film, and Korea's Academy
    Award entry that year.

What it refuses is worth naming, because it is the honest cost:

  * **The Handmaiden** (2016) and **Train to Busan** (2016) are on none of
    these lists at all. Korea's juries gave The Handmaiden its Best Director
    nominations and its Best Film prizes went elsewhere, and it was not the
    country's Academy entry — The Age of Shadows was. This is the clearest
    thing the gate throws out and it should be argued with.
  * **The Wailing** (2016), **House of Hummingbird** (2018) and **Hill of
    Freedom** (2014) each have exactly one jury and stop there.
  * Everything between 2013 and today that only one jury liked — seventeen
    films, listed by the generator when it runs.

Traps this file hit, and what it did about them
------------------------------------------------
  * **A KMDb id carries a collection letter and it is load-bearing.**
    Ninety-nine of the archive's hundred are `K/#####`; Repatriation is
    `A/03370`, a documentary. Wikidata files those under a different property
    and KMDb serves them from a different path, so dropping the letter fetched
    a 1979 melodrama and would have shipped its Wikidata id on a 2003
    documentary's row.
  * **Reading a table cell by offset crosses row boundaries.** The archive's
    page gives some rows an extra YouTube button; searching forward from the
    title for a KMDb link picked up the NEXT row's id. The row is the unit
    now, and nothing is read across it.
  * **A title search finds the wrong film, reliably.** Looking up the fourteen
    archive rows Wikidata has no KMDb id for by name returned a 1960 film for
    The Wedding Day (1956) and a 1928 one for Rainy Days (1979). Those rows
    ship with no `q` rather than a guessed one.
  * **The archive's earlier selection is not readable.** KOFA published a
    100 Korean Films in 1996 too and still links it, but all five tabs of
    that page serve the same first twenty rows, so eighty of its hundred
    cannot be read at all. It would have been a second, older archive voice
    to count with; it is left out rather than shipped as a fifth of itself.
  * **Blue Dragon and Baeksang list nominees beside winners.** Oldboy is a
    2003 Blue Dragon Best Film NOMINEE — Spring, Summer, Fall, Winter... and
    Spring won — so only the row carrying {{double dagger}} counts, and the
    generator asserts the totals that fact produces.

Wikidata ids
------------
105 of the 120 rows carry `q`, which build.py groups on ahead of title and
year. Every one was resolved from an identifier the source itself printed —
the archive's KMDb number for its own selections, the award article's own
wikilink for the juries' — and then checked against the item's P31 and P577:
an item that is not a film, or whose publication dates miss the row's year by
more than a year, loses its id rather than risk ticking a film nobody watched.

Weights
-------
Every row is weighted and no figure was invented. 84 come from the film's own
English Wikipedia infobox; the other 36 have no English article at all and
take the running time from the archive's own database, the 상영시간 field of
the film's KMDb record, matched to the release the archive dated. Wikidata's
P2047 is carried only as a cross-check and disagrees with the infobox on six
rows, which is why it is not the source.

Data: scratch/agent-korea/{kofa,collect,gate,runtimes}.py
      -> tools/data/korean-cinema.json
"""
import collections
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop as P  # noqa: E402

SLUG = "korean-cinema"
DATA = pathlib.Path(__file__).resolve().parent / "data" / ("%s.json" % SLUG)

# clause two: how many of Korea's juries must agree on a film the archive's
# selection was made too early to consider. See the docstring for why 2.
MIN_JURIES = 2

# The eight, in the order the notes name them. Each is a Best Film jury except
# the last, which is the committee that picks the country's Academy entry.
JURIES = [
    ("bluedragon", "the Blue Dragon"),
    ("grandbell", "the Grand Bell"),
    ("baeksang", "the Baeksang"),
    ("buil", "the Buil"),
    ("chunsa", "the Chunsa"),
    ("koreanfilm", "the Korean Film Awards"),
    ("kafca", "the Korean Association of Film Critics"),
    ("oscar", "Korea's Academy Award entry"),
]

ACCENT, ACCENT_DARK = "#1D5C7A", "#79C2DD"

# The archive prints its hundred under four era tabs and its top twelve
# separately; the tabs are decade-aligned and the generator proves it before
# using them. `hi` is the last year the tab covers — the last tab is labelled
# "2000s" but runs to Pietà, which is where the whole selection stops.
ARCHIVE_ERAS = [
    ("early", "1930s ~ 1950s", None, 1959),
    ("goldenage", "1960s ~ 1970s", 1960, 1979),
    ("recovery", "1980s ~ 1990s", 1980, 1999),
    ("newwave", "2000s", 2000, 2012),
]

# Era prose. Every countable claim in here is filled in from the roster at
# build time rather than typed, and every historical one is a sentence that
# has to still be present in the fetched "Cinema of South Korea" wikitext —
# see FRAMING and the check that uses it.
INTROS = {
    "early": "Colonial rule, liberation, and a war. The oldest thing the "
             "archive selected is from 1934 and only %(prewar)d of its "
             "hundred predate 1950 at all; the run at the end of this "
             "section is the industry restarting, from fifteen features made "
             "in 1954 to a hundred and eleven in 1959.",
    "goldenage": "The golden age, and then the clampdown. The Motion Picture "
                 "Law of 1962 capped imports under a quota and cut the "
                 "number of production companies from seventy-one to sixteen "
                 "inside a year, and censorship targeted obscenity, "
                 "communism and unpatriotic themes. A third of the archive's "
                 "hundred comes from these twenty years anyway — "
                 "%(count)d films.",
    "recovery": "Censorship relaxes. The Motion Picture Law of 1984 lets "
                "independent film-makers produce at all, and in 1992 the "
                "film this list carries as The Marriage Life becomes the "
                "first Korean release from a chaebol, which is how Samsung "
                "and the rest end up financing an industry. The biggest "
                "section here, and the stretch the archive drew most heavily "
                "from.",
    "newwave": "The industry's revival with the Korean New Wave, and the "
               "point at which the rest of the world starts paying. The "
               "archive's selection stops at Pietà in 2012, so this section "
               "thins after 2010 for a reason that is about the list rather "
               "than about the films.",
    "since": "Everything after the archive's selection closed. These rows "
             "are not the archive's picks — it has not made a new selection "
             "— so each one is here because at least %(min)d of Korea's "
             "eight juries named it, and the note says how many. It is a "
             "coarser instrument than a considered canon and this section "
             "should be read as provisional.",
}

# The historical claims above, in the words the source uses. If the article
# is rewritten these stop matching and the build fails rather than shipping
# prose that has quietly outrun what anybody said.
FRAMING = [
    "The number of films made in South Korea increased from only 15 in 1954 "
    "to 111 in 1959.",
    "Under the Motion Picture Law of 1962, a series of increasingly "
    "restrictive measures was enacted that limited imported films under a "
    "[[Screen quotas|quota]] system",
    "reduced the number of domestic film-production companies from 71 to 16 "
    "within a year",
    "Government censorship targeted obscenity, [[communism]], and "
    "unpatriotic themes in films",
    "The Motion Picture Law of 1984 allowed independent filmmakers to begin "
    "producing films",
    "the first South Korean movie to be released by business conglomerate "
    "known as a ''[[chaebol]]''",
    "the industry's revival with the Korean New Wave from the late 1990s to "
    "the present",
]

# Asserted rather than hoped for: the four films any credible gate has to
# admit, each with the reason it clears. If an edit ever breaks one of these
# the gate is wrong and the build should stop, NOT be patched around.
CANARIES = {
    "Old Boy": ("archive", 2003),
    "Memories of Murder": ("archive", 2003),
    "Parasite": ("juries", 2019),
    "Burning": ("juries", 2018),
}

# Named on the page. Checked against the data so the claim cannot go stale.
REFUSED = {
    "The Handmaiden": 2016,
    "Train to Busan": 2016,
}


# One typo, twice, in the archive's own director column: a capital I where an
# l belongs. English Wikipedia's article on the director of The Wedding Day is
# "Lee Byung-il", which is what settles it. Kept as an explicit map rather than
# a clever rule, and asserted below so it can never quietly stop matching.
SOURCE_TYPOS = {"Lee Byung-iI": "Lee Byung-il"}


def person(name):
    """A director's name as display text, with the sources' defects removed.

    All of them are the sources' own, not a parse: the archive types some
    surnames in capitals (KIM Ho-sun) and left a full-width question mark on
    one row, and Wikipedia's award tables carry article disambiguators
    (Kim Sung-su (director)). None of that is a fact about the person, so
    none of it ships; nothing here changes a name beyond its case and its
    punctuation, and the one actual misspelling is listed above by hand.
    """
    name = SOURCE_TYPOS.get((name or "").strip(), name)
    name = re.sub(r"\s*\((?:film )?director\)", "", name or "").strip()
    name = re.sub(r"[^\w .,'’-]", "", name, flags=re.UNICODE).strip()
    out = []
    for tok in name.split():
        if tok.strip(",").isupper() and len(tok.strip(",")) > 1:
            tok = tok.capitalize()
        out.append(tok)
    return " ".join(out)


def straight(t):
    """Curly apostrophes to straight ones, so A Good Lawyer's Wife reads and
    sorts like every other title in the catalogue."""
    return (t or "").replace("’", "'").replace("‘", "'")


def era_of(year):
    for key, _label, lo, hi in ARCHIVE_ERAS:
        if (lo is None or year >= lo) and year <= hi:
            return key
    return "since"


def is_film(kinds):
    return any("film" in k.lower() for k in kinds or ())


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
                n = str(x.get("n", ""))
                y = n if re.fullmatch(r"(18|19|20)\d{2}", n) else None
                if not y:
                    found = set(re.findall(r"\b((?:18|19|20)\d{2})\b",
                                           x.get("note") or ""))
                    y = found.pop() if len(found) == 1 else None
                q = x.get("q")
                out.append((d["slug"], x["id"], P.normt(x["t"]),
                            int(y) if y else None,
                            q if isinstance(q, str) else None, x["t"]))
    return out


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    archive, juries = d["archive"], d["juries"]
    facts, runtimes = d["facts"], d["runtime"]
    rows = archive["rows"]

    # ---- the archive's selection is the shape this file claims ------------
    assert len(rows) == 100, "the archive selected %d films" % len(rows)
    assert sorted(r["rank"] for r in rows) == list(range(1, 101))
    assert archive["closed"] == max(r["year"] for r in rows) == 2012, \
        "the archive's newest selection is not 2012"
    typo_hits = sum(1 for r in rows if r["director"] in SOURCE_TYPOS)
    assert typo_hits == 2, \
        "the archive's director typo no longer appears twice (%d) — check " \
        "SOURCE_TYPOS before removing it" % typo_hits
    assert set(k for k, _n in JURIES) == set(juries), \
        "the jury panel and the data disagree: %s" % sorted(
            set(juries) ^ {k for k, _n in JURIES})

    # Ranks 1-12 are the archive's own order — the films its critics voted for
    # most, printed on a tab of their own. Ranks 13-100 are a chronological
    # index across four era tabs and are NOT a ranking, which is why no row
    # below twelve prints a number. Proven, not assumed.
    tail = sorted((r for r in rows if r["rank"] > 12), key=lambda r: r["rank"])
    years = [r["year"] for r in tail]
    assert years == sorted(years), \
        "ranks 13-100 are not in date order, so they may be a ranking"
    top = [r for r in rows if r["rank"] <= 12]
    assert [r["year"] for r in top] != sorted(r["year"] for r in top), \
        "the top twelve are in date order too, so they may not be a ranking"

    # ...and the era tabs are decade-aligned, so the twelve the archive pulled
    # out of them can be filed back by year without inventing a boundary.
    for r in tail:
        label = r["era"]
        got = next(k for k, lb, _lo, _hi in ARCHIVE_ERAS if lb == label)
        assert got == era_of(r["year"]), \
            "%s (%d) sits under the archive's %r tab but this file's " \
            "boundaries put it in %r" % (r["t"], r["year"], label, got)

    # ---- clause one: the archive's hundred --------------------------------
    films = {}
    for r in rows:
        key = r["q"] or "kofa:%d" % r["rank"]
        assert key not in films, "two archive rows resolve to %s" % key
        films[key] = {
            "key": key, "q": r["q"], "t": straight(r["t"]),
            "year": r["year"], "director": person(r["director"]),
            "rank": r["rank"], "archive": True,
            "korean": r.get("korean"), "src": {},
            "titles": [straight(r["t"])]}
    by_q = {f["q"]: f for f in films.values() if f["q"]}
    by_title = collections.defaultdict(list)
    for f in films.values():
        by_title[P.normt(f["t"])].append(f)

    # ---- the juries -------------------------------------------------------
    # An award row with no wikilink cannot carry an id. It still counts as a
    # vote where its title is unique among the films already on the roster and
    # the film's own release year sits within two years of the ceremony —
    # Whale Hunting and Deep Blue Night reach the archive's rows that way.
    # Anything ambiguous is dropped and printed.
    attached, orphans = [], []
    for jkey, _name in JURIES:
        for r in juries[jkey]:
            q = r.get("q")
            if q and q in by_q:
                f = by_q[q]
            elif q:
                fa = facts.get(q) or {}
                ys = fa.get("pub_years") or []
                if q not in films:
                    films[q] = {"key": q, "q": q, "t": straight(r["t"]),
                                "year": min(ys) if ys else None,
                                "director": person(r.get("director")),
                                "rank": None,
                                "archive": False, "korean": r.get("korean"),
                                "src": {}, "titles": []}
                    by_q[q] = films[q]
                f = films[q]
            else:
                cand = [x for x in by_title.get(P.normt(r["t"]), [])
                        if x["year"]
                        and 0 <= r["award_year"] - x["year"] <= 2]
                if len(cand) != 1:
                    orphans.append((jkey, r["award_year"], r["t"]))
                    continue
                f = cand[0]
                attached.append((jkey, r["award_year"], r["t"], f["key"]))
            f["src"].setdefault(jkey, r["award_year"])
            if straight(r["t"]) not in f["titles"]:
                f["titles"].append(straight(r["t"]))
            if r.get("korean") and not f["korean"]:
                f["korean"] = r["korean"]

    # ---- the gate ---------------------------------------------------------
    closed = archive["closed"]
    gated, near = [], []
    for f in films.values():
        if f["archive"]:
            gated.append(f)
        elif f["year"] and f["year"] > closed and len(f["src"]) >= MIN_JURIES:
            gated.append(f)
        elif f["year"] and f["year"] > closed:
            near.append(f)
    assert len(gated) == 120, "the gate now admits %d films" % len(gated)
    assert sum(1 for f in gated if f["archive"]) == 100
    modern = [f for f in gated if not f["archive"]]

    # ---- ids: the source's own identifier, and only where it holds up -----
    refused_id = []
    for f in gated:
        if not f["q"]:
            continue
        fa = facts.get(f["q"]) or {}
        ys = fa.get("pub_years") or []
        why = None
        if not is_film(fa.get("kinds")):
            why = "not a film: %s" % ", ".join(fa.get("kinds") or ["unknown"])
        elif ys and min(abs(y - f["year"]) for y in ys) > 1:
            why = min(ys, key=lambda y: abs(y - f["year"]))
        if why is not None:
            refused_id.append((f["t"], f["year"], why))
            f["q"] = None
    assert len(refused_id) == 1 and isinstance(refused_id[0][2], int), \
        "the notes describe exactly one refused id: %s" % refused_id
    qs = [f["q"] for f in gated if f["q"]]
    assert len(qs) == len(set(qs)), \
        "two rows share an id: %s" % [q for q in qs if qs.count(q) > 1][:3]

    # ---- the sanity checks, on their own merits ---------------------------
    for name, (how, year) in CANARIES.items():
        hit = [f for f in gated
               if any(P.normt(t) == P.normt(name) for t in f["titles"])
               and f["year"] == year]
        assert len(hit) == 1, "%s (%d) is not on this list" % (name, year)
        f = hit[0]
        if how == "archive":
            assert f["archive"], "%s no longer clears via the archive" % name
        else:
            assert not f["archive"] and len(f["src"]) >= MIN_JURIES, \
                "%s clears on %d juries, below the gate" % (name,
                                                            len(f["src"]))
    for name, year in REFUSED.items():
        assert not [f for f in gated
                    if any(P.normt(t) == P.normt(name) for t in f["titles"])], \
            "the notes say %s (%d) is excluded and it is not" % (name, year)

    # ---- weights are all-or-nothing (CLU-131) -----------------------------
    for f in gated:
        rt = runtimes.get(f["key"]) or {}
        f["runtime"], f["rt_src"] = rt.get("min"), rt.get("src", "")
        assert f["runtime"], "no sourced runtime for %s (%s)" % (f["t"],
                                                                 f["year"])
        assert 30 <= f["runtime"] <= 250, \
            "%s runtime %r is not credible" % (f["t"], f["runtime"])
    from_infobox = [f for f in gated if f["rt_src"].startswith("infobox")]
    from_kmdb = [f for f in gated if f["rt_src"].startswith("kmdb")]
    assert len(from_infobox) + len(from_kmdb) == len(gated)
    disagree = [f for f in from_infobox
                if (facts.get(f["q"]) or {}).get("p2047")
                and abs(facts[f["q"]]["p2047"] - f["runtime"]) > 4]

    # ---- rows -------------------------------------------------------------
    gated.sort(key=lambda f: (f["year"], P.normt(f["t"])))
    entries, seen = [], set()
    for f in gated:
        fa = facts.get(f["q"]) or {}
        # the archive translates some titles its own way — "Good Windy Day",
        # "Declaration of Idiot" — and the source's title is the one that
        # ships. The English Wikipedia name rides in the note where it
        # differs, so a reader can find the film.
        alt = fa.get("enwiki")
        alt = re.sub(r"\s*\([^()]*\)$", "", alt).strip() if alt else None
        korean = f["korean"] or fa.get("ko")
        if korean:
            korean = re.sub(r"\s*\([^()]*\)$", "", korean).strip()
        n_juries = len(f["src"])
        if f["archive"]:
            gate_bit = ("Korean Film Archive 100, no. %d" % f["rank"]
                        if f["rank"] <= 12 else "Korean Film Archive 100")
            jury_bit = ("%d of %d juries" % (n_juries, len(JURIES))
                        if n_juries else None)
        else:
            gate_bit = "%d of %d juries" % (n_juries, len(JURIES))
            jury_bit = None
        base = "kc-%d-%s" % (f["year"], P.slug(f["t"]))
        iid, k = base, 2
        while iid in seen:
            iid, k = "%s-%d" % (base, k), k + 1
        seen.add(iid)
        x = {"id": iid, "t": f["t"], "n": str(f["year"]),
             "w": round(f["runtime"] / 60.0, 2),
             "note": P.join_bits(
                 gate_bit, jury_bit, f["director"] or None, korean,
                 "%d min" % f["runtime"],
                 "also %s" % alt if alt and P.normt(alt) != P.normt(f["t"])
                 else None)}
        if f["q"]:
            x["q"] = f["q"]
        entries.append(dict(x, era=era_of(f["year"]), year=f["year"],
                            runtime=f["runtime"], archive=f["archive"],
                            juries=n_juries))

    years = [e["year"] for e in entries]
    assert years == sorted(years), "the roster is out of release order"
    # a plain-year `n` is what build.py syncs on, so a Korean title that IS a
    # year — 1987 — can never be mistaken for one
    for e in entries:
        assert re.fullmatch(r"(19|20)\d{2}", e["n"]), e["id"]
    total_min = sum(e["runtime"] for e in entries)

    # ---- sections ---------------------------------------------------------
    sections = []
    for key, label, lo, hi in ARCHIVE_ERAS + [("since", "After the archive's "
                                               "list", 2013, 9999)]:
        got = [e for e in entries if e["era"] == key]
        assert got, "empty section %s" % key
        assert all((lo is None or e["year"] >= lo) and e["year"] <= hi
                   for e in got), key
        title = label if key != "since" else "After the archive's list"
        sections.append({
            "id": key, "title": title.replace(" ~ ", " – "),
            "sub": " · ".join([
                "%d–%d" % (got[0]["year"], got[-1]["year"]),
                "%d films" % len(got),
                "%d hours" % round(sum(e["runtime"] for e in got) / 60.0)]),
            "intro": INTROS[key] % {
                "count": len(got), "min": MIN_JURIES,
                "prewar": sum(1 for e in entries if e["year"] < 1950)},
            "items": [{k: v for k, v in e.items()
                       if k in ("id", "t", "n", "w", "note", "q")}
                      for e in got]})
    sections[0]["open"] = True

    # ---- the era prose must not outrun the article it came from -----------
    ctx = P.ROOT / "scratch" / "agent-korea" / "Cinema-of-South-Korea.wiki"
    if ctx.exists():
        src = ctx.read_text(encoding="utf-8")
        for claim in FRAMING:
            assert claim in src, "the era framing outran its source: %r" % claim
    # the two intros that count something, checked against the roster
    assert 0.30 <= len([e for e in entries
                        if 1960 <= e["year"] <= 1979]) / 100.0 <= 0.36, \
        "the golden-age intro's 'a third' no longer holds"
    assert any(e["t"] == "The Marriage Life" and e["year"] == 1992
               for e in entries), "the chaebol intro names a row that is gone"

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)) == len(entries)

    # ---- the accent pair is ours alone ------------------------------------
    for f in sorted((P.ROOT / "properties").glob("*.json")):
        if f.name in ("index.json", "search.json", "%s.json" % SLUG):
            continue
        o = json.loads(f.read_text(encoding="utf-8"))
        assert o.get("accent") != ACCENT, \
            "%s already uses accent %s" % (o.get("slug"), ACCENT)
        assert o.get("accentDark") != ACCENT_DARK, \
            "%s already uses accentDark %s" % (o.get("slug"), ACCENT_DARK)

    # ---- the overlaps have to actually group ------------------------------
    # A row of ours carrying both an id and a plain year offers build.py two
    # keys, and build.py merges them into ONE group — Parasite pairs with
    # Criterion and Best Picture by id and with the Palme d'Or and Sight &
    # Sound by title+year, and that is a single group of four, not two of
    # two. So groups are counted per row of OURS, which is what merging does.
    mine_year = {(P.normt(e["t"]), e["year"]): e["id"] for e in entries}
    mine_keys = {k for k, _y in mine_year}
    mine_q = {e["q"]: e["id"] for e in entries if e.get("q")}
    groups, missed = collections.defaultdict(set), []
    elsewhere = catalogue()
    for slug, _iid, key, year, q, raw in elsewhere:
        if q and q in mine_q:
            groups[mine_q[q]].add(slug)
        elif (key, year) in mine_year:
            groups[mine_year[(key, year)]].add(slug)
        elif key in mine_keys and year:
            missed.append((raw, slug, year,
                           tuple(sorted(y for k, y in mine_year
                                        if k == key))))
    for slug in ("criterion", "cult-classics", "best-picture", "palme-dor",
                 "sight-and-sound"):
        assert any(slug in v for v in groups.values()), \
            "no sync group forms with %s" % slug
    lists_met = {s for v in groups.values() for s in v}
    by_id = {e["id"]: e["t"] for e in entries}
    top_share = max(groups.items(), key=lambda kv: len(kv[1]))
    most_shared = (by_id[top_share[0]], top_share[1])
    # the note below names two films the catalogue already carries and this
    # gate refuses, and three the juries named exactly once. Both claims are
    # checked against the data rather than trusted.
    for slug, _iid, _key, year, _q, raw in elsewhere:
        if slug == "zombie-films" and raw in REFUSED:
            assert (P.normt(raw), year) not in mine_year, raw
    one_jury = {f["t"] for f in near if len(f["src"]) == 1}
    for t in ("The Wailing", "House of Hummingbird", "Hill of Freedom"):
        assert t in one_jury, \
            "the notes say %s stops at one jury and it does not" % t

    # ---- figures the notes quote, computed rather than typed --------------
    oldest, newest = entries[0], entries[-1]
    top_juries = max(entries, key=lambda e: e["juries"])
    at_gate = sum(1 for e in entries
                  if not e["archive"] and e["juries"] == MIN_JURIES)
    shortest = min(entries, key=lambda e: e["runtime"])
    longest = max(entries, key=lambda e: e["runtime"])
    biggest = max(sections, key=lambda s: len(s["items"]))
    with_id = sum(1 for e in entries if e.get("q"))
    best_film = [n for _k, n in JURIES[:-1]]
    jury_names = ", ".join(best_film[:-1]) + " and " + best_film[-1]
    assert JURIES[-1][0] == "oscar", "the last jury is the odd one out"

    prop = {
        "slug": SLUG,
        "title": "Korean Cinema",
        "subtitle": "the national archive's hundred, and what came after",
        "kind": "films",
        # A national-cinema survey. Parasite's Best Picture win put the
        # category in front of a general audience in a way "cult classics"
        # took decades to manage, so this sits just above Cult Classics (55)
        # and Zombie Films (52) — but it is still a thematic survey that needs
        # a sentence of explanation, which is the 40-59 band in POPULARITY.md,
        # and it stays below the Criterion Collection (63) and Kurosawa (62),
        # a named auteur whose name travels on its own.
        "popularity": 56,
        "year": "%d–%d" % (oldest["year"], newest["year"]),
        "blurb": "%d films Korea's own national film archive and its film "
                 "juries picked out, %d to %d — about %d hours. No order; "
                 "let the picker choose."
                 % (len(entries), oldest["year"], newest["year"],
                    round(total_min / 60.0)),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "random": True,
        "notes": [
            ["“The best of Korean cinema” is a verdict, so this list does not "
             "pass one.",
             "The spine is somebody else's: the %d films the Korean Film "
             "Archive — the country's national archive, a government body — "
             "selected as its 100 Korean Films. That is the closest thing "
             "Korean cinema has to a native canon, and it is one considered "
             "survey of the whole history rather than a prize for one year. "
             "The archive prints twelve of them separately and in order, "
             "headed by The Housemaid, and lists the other eighty-eight by "
             "date; every row here says which of the two it is. Nothing was "
             "added because it felt right."
             % sum(1 for e in entries if e["archive"])],
            ["That selection was made in 2014, and stops at Pietà.",
             "So Parasite could not have been on it, and neither could "
             "Burning. The %d films released since are here on a second "
             "rule, stated so you can argue with it: at least %d of Korea's "
             "eight juries must have named the film. Seven of the eight "
             "award a Best Film — %s — and the eighth is the committee that "
             "picks the country's Academy Award entry. %s leads with %d of "
             "them; %d of these rows clear on exactly %d. This is a coarser "
             "instrument than a canon and the last section should be read as "
             "provisional."
             % (len(modern), MIN_JURIES, jury_names, top_juries["t"],
                top_juries["juries"], at_gate, MIN_JURIES)],
            ["What that costs, said plainly.",
             "The Handmaiden and Train to Busan are not here. Neither took a "
             "Best Film prize from any of the eight and neither was Korea's "
             "Academy entry, so no honest count reaches them; The Wailing, "
             "House of Hummingbird and Hill of Freedom stop at one jury "
             "apiece. A prize is a poor proxy for a canon and this is where "
             "it shows. The other direction costs too: a jury names one film "
             "a year whatever the year was like, so the last section carries "
             "some very large commercial pictures beside the rest."],
            ["The eras are the archive's own, not ours.",
             "It publishes its hundred under four tabs — 1930s–1950s, "
             "1960s–1970s, 1980s–1990s and 2000s — and those are the first "
             "four sections here, boundaries and all. The generator proves "
             "they are decade-aligned before filing the twelve top-ranked "
             "films back into them by date. The fifth section is not the "
             "archive's and does not pretend to be. Era descriptions come "
             "from Wikipedia's “Cinema of South Korea”, which splits the "
             "same history into a golden age, censorship, recovery and "
             "renaissance."],
            ["Bar widths are runtimes, and none was invented.",
             "All %d rows are weighted, %d hours in total. %d figures are "
             "the film's own English Wikipedia infobox; the other %d have no "
             "English article at all and take the running time from the "
             "archive's own database, KMDb, matched to the release the "
             "archive dated. Wikidata's runtime is carried only as a "
             "cross-check and disagrees with the infobox on %d rows, which is "
             "why it is not the source. The range runs from %s at %d minutes "
             "to %s at %d."
             % (len(entries), round(total_min / 60.0), len(from_infobox),
                len(from_kmdb), len(disagree), shortest["t"],
                shortest["runtime"], longest["t"], longest["runtime"])],
            ["Titles are the source's, and so is every id.",
             "The archive translates some of its own selections its own way — "
             "Good Windy Day, Declaration of Idiot, A Peppermint Candy — and "
             "that is the title that ships, with the more familiar English "
             "name in the note where they differ. Korean titles come from the "
             "archive's database or from the award tables' own original-title "
             "column; nothing here was romanised by us. %d of the %d rows "
             "carry a Wikidata id, each resolved from an identifier the "
             "source printed itself — the archive's KMDb number, or the award "
             "article's wikilink — and never from a title. %d of the "
             "remaining %d are archive selections Wikidata holds no KMDb "
             "number for, and looking those up by name returned a 1960 film "
             "for The Wedding Day and a 1928 one for Rainy Days, so they ship "
             "without an id instead. %s had one and lost it: the archive "
             "dates it %d and its own Wikidata item dates it %d, and a gap "
             "that wide is not something to tick a film on."
             % (with_id, len(entries),
                len(entries) - with_id - len(refused_id),
                len(entries) - with_id, refused_id[0][0], refused_id[0][1],
                refused_id[0][2])],
            ["The same film on two lists here is the point.",
             "%d of these films are already somewhere else in the catalogue — "
             "across %s — and ticking one ticks the other. %s is on %d other "
             "lists, more than anything else here. The overlap is small "
             "because the rest of the catalogue is thin on Korean cinema, "
             "which is most of the reason this list exists; two that ought to "
             "pair, Train to Busan and The Wailing on Zombie Films, do not, "
             "because the gate does not admit them."
             % (len(groups), ", ".join(sorted(lists_met)), most_shared[0],
                len(most_shared[1]))],
            "Selection from the Korean Film Archive's “100 Korean Films” "
            "(2014) and, for films released after it, the Blue Dragon, Grand "
            "Bell, Baeksang, Buil, Chunsa, Korean Film Awards and Korean "
            "Association of Film Critics Best Film records on Wikipedia plus "
            "Korea's Academy Award submissions; era framing from Wikipedia's "
            "“Cinema of South Korea”; running times from each film's "
            "Wikipedia infobox or its KMDb record; ids from KMDb via Wikidata.",
        ],
        "sections": sections,
    }

    P.write(prop)

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d films — all weighted, %d min (%.1f hours)"
          % (len(sections), len(ids), total_min, total_min / 60.0))
    print("  gate: the archive's %d, plus %d films since %d with >=%d of %d "
          "juries" % (len(entries) - len(modern), len(modern), closed,
                      MIN_JURIES, len(JURIES)))
    print("  ids: %d of %d rows carry one" % (with_id, len(entries)))
    for t, y, why in refused_id:
        print("    id refused %-34s row %s vs item %s" % (t, y, why))
    print("  runtimes: %d from infoboxes, %d from KMDb, %d where Wikidata "
          "disagrees" % (len(from_infobox), len(from_kmdb), len(disagree)))
    for s in sections:
        print("   %-26s %3d  %s" % (s["title"], len(s["items"]), s["sub"]))
    print("  %d sync groups across %d other lists:"
          % (len(groups), len(lists_met)))
    for s, n in collections.Counter(
            s for v in groups.values() for s in v).most_common(12):
        print("   %-24s %3d" % (s, n))
    print("  near misses — same title, a different year (%d):" % len(missed))
    for raw, slug, year, ours in sorted(set(missed)):
        print("   %-34s %-18s theirs=%s ours=%s" % (raw, slug, year, ours))
    print("  post-%d films the juries named only once (%d), all excluded:"
          % (closed, len(near)))
    for f in sorted(near, key=lambda f: (f["year"], f["t"])):
        print("   %s %-34s %s" % (f["year"], f["t"], sorted(f["src"])))
    print("  award rows with no wikilink, attached by title+year (%d):"
          % len(attached))
    for a in attached:
        print("   %-11s %s %-32s -> %s" % a)
    print("  award rows with no wikilink and no home (%d)" % len(orphans))
    assert biggest["id"] == "recovery", biggest["id"]


if __name__ == "__main__":
    main()
