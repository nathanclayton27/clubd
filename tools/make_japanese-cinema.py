#!/usr/bin/env python3
"""Generate properties/japanese-cinema.json.

    python tools/make_japanese-cinema.py

"The best of Japanese cinema" is a verdict, and this catalogue does not ship
verdicts. So this list never decides that a Japanese film is one of the best:
it takes the ranking Japan's own film magazine published, and, for the years
that ranking could not reach, counts how many of Japan's eight film juries
have since named a film. Both figures ride on every row, so a reader can argue
with either one.

The gate
--------
**A film is here if Kinema Junpo's 2009 all-time poll of Japanese cinema
ranked it, or — released after that poll closed — if at least two of Japan's
eight film juries have since named it Best Film.**

Clause one is the spine. Kinema Junpo is Japan's oldest film magazine, founded
in 1919, and for its ninetieth anniversary it asked 114 critics, film-makers
and writers for the ten Japanese films that stayed with them, then published
the whole tally — «オールタイム・ベスト 映画遺産200», All-Time Best: Film
Heritage 200. That is one considered survey of the entire history rather than
a prize for one year, and it is the closest thing Japanese cinema has to a
native canon. It ran 198 Japanese entries deep, from Tokyo Story at the top to
the 89-film tie at 106th place, and — this is what makes it usable here — 187
of those entries link to the film's record in the magazine's OWN database,
whose numbers Wikidata carries as KINENOTE film ids.

Clause two exists because the poll was taken in 2009 and its newest entry is
from 2008. Drive My Car could not have been on it. Neither could Shoplifters.
Films released since are admitted only where at least two of these eight
agree, each a record of what a Japanese institution chose rather than an
opinion this file formed:

    Kinema Junpo's own Best One · the Mainichi Film Award · the Blue Ribbon ·
    the Japan Academy Film Prize · the Hochi Film Award · the Nikkan Sports
    Film Award · the Yokohama Film Festival — Best Film in each — and the
    committee that picks Japan's Academy Award entry.

The magazine that made the poll is the first of the eight, deliberately: its
annual Best Ten has run since 1924 and is the same voice that made the spine.

Why the juries do not govern the years the poll covers
------------------------------------------------------
Letting them would nearly have worked — and the data says loudly why not.
Forty-four films from before 2009 took at least two of these prizes and were
NOT ranked by the poll, and the single loudest of them is Sumo Do, Sumo Don't
(1992), which took SEVEN of the eight juries in its year and did not place in
the magazine's all-time ranking at all. So did Poppoya, The Silk Road and
Crest of Betrayal. A jury names one film a year whatever the year was like; a
survey of the whole history does not, and the two are not the same kind of
evidence. Clause two is the coarser instrument, so it only governs the
seventeen years the finer one could not reach.

Why two juries and not one or three
-----------------------------------
At one, the modern section grows from 30 rows to 64 and takes in Fly Me to the
Saitama, Samurai Hustle and All of a Sudden, which has not been released. At
three it falls to 16 and drops Godzilla Minus One and In This Corner of the
World, which is the check that says a gate has gone wrong. Two is where a
modern row stops being one jury's pick of one year.

The four sanity checks, and what the gate refuses
-------------------------------------------------
All four obvious ones clear on their own merits, and the generator asserts
each with the reason it clears, so a future edit cannot quietly lose one:

  * **Tokyo Story** (1953) — the poll's number one.
  * **Seven Samurai** (1954) — its number two.
  * **Rashomon** (1950) — seventh.
  * **Godzilla** (1954) — 106th, in the poll's long final tie. Japan's critics
    did not rate it in 1954 and the tally shows it, but it is on the list and
    no clause was written to put it there.

What it refuses is worth naming, because it is the honest cost:

  * **Spirited Away** (2001). Four of the eight juries named it and the poll's
    114 voters did not rank it, and because it predates the poll clause two
    cannot reach it. It is the clearest thing this gate throws out. **Princess
    Mononoke** (1997) and **Hana-bi** (1997) go the same way at three juries
    each, as does **A Taxing Woman** (1987) at five.
  * **Kwaidan**, **Fires on the Plain**, **The Burmese Harp** and **Gate of
    Hell** — one jury apiece and no place in the ranking.
  * Everything from 2009 on that only one jury liked — thirty-four films,
    listed by the generator when it runs.
  * Two of the poll's own entries, for a different reason: 現代性犯罪絶叫篇
    理由なき暴行 and 襲(や）られた女 are printed without a link, are absent from
    the magazine's own database, and are documented by no Wikipedia in any
    language, so nothing gives a running time for them. Weights are all or
    nothing, so a row that cannot be weighed cannot ship, and the page names
    both rather than dropping them quietly.

Animation, settled by the source rather than by us
--------------------------------------------------
Kinema Junpo polled animation SEPARATELY in the same survey, which might have
been read as putting it outside the Japanese-film ranking. It did not: four
animated features are ranked inside that ranking — Nausicaä of the Valley of
the Wind at 17, My Neighbor Totoro at 36, and The Castle of Cagliostro and
Castle in the Sky at 59 — so animation is in scope on the source's own
authority, and all four pair with the Studio Ghibli list here. Spirited Away
is absent for the reason above and not to avoid an overlap.

Traps this file hit, and what it did about them
------------------------------------------------
  * **Reading the two columns in order put Vertigo on the Japanese list.**
    The poll prints Japanese films left and foreign films right, and a rank
    shared by three Japanese films leaves the left column empty on two of its
    rows. The columns are told apart by the gutter cell between them, never by
    which link comes first.
  * **The second table's header row has no closing tag**, which glued it to
    the first data row: Ikiru, ranked 13th, went unread and the four rows
    under it inherited rank 10. Rows are split on the OPENING tag.
  * **A wikitext table closes at `|}` and so does an {{ill}} template with an
    empty last argument.** Scanning for a bare `|}` ended the Kinema Junpo
    award table on its first row and cost 95 of its 96 winners.
  * **Hochi's Best Picture cell prints `''film'' (director)`**, and taking the
    first link in the cell filed 2024's Best Picture under Michihito Fujii.
    Only an italic link counts, and where the cell links nothing the film is
    taken from another cell of the SAME row by exact title.
  * **AN ENTRY IS A CELL, NOT A LINK.** Eleven of the poll's Japanese entries
    are printed as plain text with no link at all, because the magazine's
    database had no record for them. Reading only the linked ones dropped I
    Was Born, But…, Sisters of the Gion, The Story of the Last Chrysanthemums
    and The Life of Matsu the Untamed, and — because the last rank cell before
    the unlinked run was 36th — reported the ranking as ending at 36th place
    when it in fact runs to 106th. This was the worst bug in the build and it
    was invisible: every link on the page had been read, and the totals
    reconciled.
  * **A title search finds a person, reliably.** Searching Japanese Wikipedia
    for the poll's unresolved rows returned five human beings for one of them
    and a railway station for another, so a candidate must be a film, must be
    dated within a year of the year the poll printed, must not already carry
    somebody else's KINENOTE number, and must be the only survivor.
  * **A release date is not an identity either.** Two Japanese films opened on
    22 January 1977, and asking Wikidata for the one that did put アラスカ物語
    on the row belonging to レイプ25時 暴姦. A candidate has to be NAMED like
    the row as well, and that check caught three wrong films.
  * **`film character` contains the word `film`.** A substring test for the
    class kept Tange Sazen the character standing beside The Million Ryo Pot,
    and two survivors is a refusal, so the poll's seventh-placed film lost its
    id. The class name has to END in the word.
  * **The poll ranks three SERIES as if they were films** — the 48-film
    Tora-san series, Toho's Jirocho Sangokushi and the Chuji Travel Diary
    trilogy. None can be a row or carry a running time, so all three are
    dropped and said so. The first Tora-san film is separately ranked and
    stays.

Wikidata ids
------------
210 of the 223 rows carry `q`, which build.py groups on ahead of title and
year. 155 came from an identifier the source printed itself — the magazine's
own database number, which Wikidata stores as P2508. The rest of the spine's
ids were recovered a row at a time, in descending order of confidence: the
exact Japanese page title, the exact release date the magazine's database
prints, a Japanese Wikipedia search, a Wikidata label search. Every one of
those four routes goes through the same gate — the candidate must be a film,
must be dated within a year of the year the poll printed, must not carry a
different KINENOTE number, must be named like the row, and must be the only
survivor — and a row that fails ships with no id rather than a guess. Modern
ids come from the award articles' own wikilinks.

Titles
------
The poll prints Japanese titles and nothing else, so the English name on a row
is the film's English Wikipedia title, reached through the id and never by
looking a title up; where there is no article, the Wikidata item's English
name; and where there is neither, the Japanese title, because nothing here was
romanised by us. Kinema Junpo's own database carries an English field and it
is not usable: it gives Nausicaä of the Valley of the Wind as "Warriors of the
Wind", the butchered American cut, and Castle in the Sky as "Laputa". The
Japanese title rides in every note.

Weights
-------
Every row is weighted and no figure was invented, from three sources in this
order: the film's own English Wikipedia infobox; Kinema Junpo's own database
record, the 上映時間 field of the film's KINENOTE page; and, for the two rows
with neither, the same field on the Japanese Wikipedia article. Wikidata's
P2047 is carried only as a cross-check. Three rows measure something a figure
had to be chosen for, and OVERRIDES below names each with its reason.

Data: scratch/agent-japan/{parse_kinejun,ids,resolve2,kinerecs,awards,facts,
      runtimes,collect}.py -> tools/data/japanese-cinema.json
"""
import collections
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop as P  # noqa: E402

SLUG = "japanese-cinema"
DATA = pathlib.Path(__file__).resolve().parent / "data" / ("%s.json" % SLUG)

# Kana and kanji. Testing for any non-ASCII character instead reported
# Nausicaä of the Valley of the Wind as having no English title at all.
CJK = re.compile(r"[　-ヿ㐀-䶿一-鿿＀-￯]")

# clause two: how many of Japan's juries must agree on a film the poll was
# taken too early to consider. See the docstring for why 2.
MIN_JURIES = 2

# The eight, in the order the notes name them. Each is a Best Film prize
# except the last, which is the committee that picks Japan's Academy entry.
JURIES = [
    ("kinejun", "Kinema Junpo's own Best One"),
    ("mainichi", "the Mainichi Film Award"),
    ("blueribbon", "the Blue Ribbon"),
    ("japanacademy", "the Japan Academy Film Prize"),
    ("hochi", "the Hochi Film Award"),
    ("nikkan", "the Nikkan Sports Film Award"),
    ("yokohama", "the Yokohama Film Festival"),
    ("oscar", "Japan's Academy Award entry"),
]

ACCENT, ACCENT_DARK = "#7C3A2D", "#EFB6A2"

# Eras. The poll is a flat ranking and divides nothing, so the divisions come
# from Wikipedia's "Cinema of Japan", "Japanese New Wave", "Nikkatsu" and
# "Pink film", and every boundary is a sentence one of them states — see
# FRAMING, which the build checks against the fetched articles.
ERAS = [
    ("prewar", "Before the Golden Age", None, 1949),
    ("golden", "The Golden Age", 1950, 1959),
    ("newwave", "The New Wave", 1960, 1971),
    ("afterstudios", "After the studios", 1972, 1988),
    ("heisei", "Heisei", 1989, 2008),
    ("since", "Since the poll", 2009, 9999),
]

# Era prose. Every countable claim is filled from the roster at build time
# rather than typed, and every historical one has to still be present in the
# fetched wikitext.
INTROS = {
    "prewar": "Silent film, the benshi who narrated it, and a war. Only "
              "%(count)d of the poll's %(spine)d entries predate 1950 at all, "
              "and that is mostly a fact about survival rather than about the "
              "films: pre-war and wartime films were reviewed after the "
              "surrender, over five hundred were condemned and half of those "
              "were burned, with Toho and Daiei destroying prints of their "
              "own before anyone asked.",
    "golden": "The Golden Age — the decade Wikipedia's history of Japanese "
              "cinema calls that outright, and the one that put Rashomon, "
              "Tokyo Story and Seven Samurai in front of the rest of the "
              "world. %(count)d films, and %(topten)d of the poll's top ten "
              "are among them.",
    "newwave": "The New Wave, which unlike the French one started inside the "
               "studios: Shochiku put out Cruel Story of Youth and Night and "
               "Fog in Japan in 1960 and Nikkatsu answered with Pigs and "
               "Battleships. This section ends in 1971, the year television "
               "had done enough damage that Nikkatsu stopped making anything "
               "else and switched to Roman Porno.",
    "afterstudios": "The studio system stops making the films it used to. "
                    "The biggest section here, and the strangest: Japanese "
                    "critics kept ranking one or two Roman Pornos among the "
                    "ten best films of the year from 1971 on, and the poll's "
                    "long final tie carries several of them beside Ozu and "
                    "Kurosawa. Nothing has been quietly dropped.",
    "heisei": "The Heisei era, which Wikipedia's history of Japanese cinema "
              "heads together with Reiwa — the Reiwa years are in the last "
              "section here, because the poll could not reach them. Cinema "
              "numbers had been falling since the 1960s, under 2,000 screens "
              "in 1993 against more than 7,000 in 1960, and the 1990s reverse "
              "it with the multiplex while the mini-theatres carry the rest. "
              "%(count)d films, and the poll stops in 2008.",
    "since": "Everything after the poll closed. These rows are not Kinema "
             "Junpo's ranking — there has been no new one — so each is here "
             "because at least %(min)d of Japan's eight juries named it Best "
             "Film, and the note says how many. It is a coarser instrument "
             "than a considered survey and this section should be read as "
             "provisional.",
}

# The historical claims above, in the words the sources use. If an article is
# rewritten these stop matching and the build fails rather than shipping prose
# that has quietly outrun what anybody said.
FRAMING = {
    "Cinema-of-Japan.wiki": [
        "Pre-war and wartime films were also subject to review, and over 500 "
        "were condemned, with half of them being burned.",
        "[[Toho]] and [[Daiei Film|Daiei]] pre-emptively destroyed films they "
        "thought to be incriminating",
        "The 1950s are widely considered the [[Golden age (metaphor)|Golden "
        "Age]] of Japanese cinema",
        "theaters in Japan hired [[benshi]], storytellers who sat next to the "
        "screen and narrated silent movies",
        "the number of movie theaters in Japan had been steadily decreasing "
        "since the 1960s",
        "The number of cinemas was under 2,000 in 1993 compared to more than "
        "7,000 in 1960.",
        "The 1990s saw the reversal of this trend and the introduction of the "
        "[[Multiplex (movie theater)|multiplex]] in Japan",
    ],
    "Japanese-New-Wave.wiki": [
        "the Japanese New Wave originated within the film studio "
        "establishment",
        "Important early examples of the Shochiku New Wave were ''[[Cruel "
        "Story of Youth]]'' and ''[[Night and Fog in Japan]]'' (both 1960",
        "''[[Pigs  and Battleships]]'', released by [[Nikkatsu]] the "
        "following year",
    ],
    "Nikkatsu.wiki": [
        "By 1971 the increased popularity of television had taken a heavy "
        "toll on the film industry and in order to remain profitable Nikkatsu "
        "turned to the production of [[Roman Porno]]",
    ],
    "Pink-film.wiki": [
        "another major studio, [[Nikkatsu]], switched to producing only "
        "''[[Roman Porno]]'' films later that year",
        "at least one or two ''Roman Pornos'' have been chosen every year "
        "since 1971 as among the ten best films of the year by Japanese "
        "critics",
    ],
}

# Asserted rather than hoped for: the four films any credible gate has to
# admit, each with the reason it clears. If an edit ever breaks one of these
# the gate is wrong and the build should stop, NOT be patched around.
CANARIES = {
    "Tokyo Story": (1953, 1),
    "Seven Samurai": (1954, 2),
    "Rashomon": (1950, 7),
    "Godzilla": (1954, 106),
}

# Named on the page, with the jury count the page quotes for each. Checked
# against the data so neither the exclusion nor the number can go stale.
REFUSED = {
    "Spirited Away": (2001, 4),
    "Princess Mononoke": (1997, 3),
    "Hana-bi": (1997, 3),
    "A Taxing Woman": (1987, 5),
    "Kwaidan": (1965, 1),
    "Fires on the Plain": (1959, 1),
    "The Burmese Harp": (1956, 1),
    "Gate of Hell": (1953, 1),
    # the argument for clause two not reaching back, in one row
    "Sumo Do, Sumo Don't": (1992, 7),
}

# The three rows where a figure had to be decided rather than read, each with
# the reason, as HOW-IT-WORKS.md asks: the override lives in one visible place
# in the generator and the row note says which version the bar measures.
# Keyed by the KINENOTE number for a poll row, by title for a modern one.
OVERRIDES = {
    # The one row the poll ranks as a SPAN rather than a year: 人間の條件
    # （59～61） is Kobayashi's three-part film, and the database record it
    # links is only the first two parts, 201 minutes. English Wikipedia covers
    # the work as one article and gives 579 minutes for all of it, which is
    # what the poll ranked. Keeping the id would point the row at Part I
    # alone, so it ships without one.
    "26064": {"page": "The Human Condition (film series)", "drop_q": True,
              "note": "the three-part film, 1959–61"},
    # Two modern rows are films released in two halves, and their juries named
    # the whole thing. The infobox prints both figures and the bar adds them.
    "Wilderness": {"minutes": 157 + 147, "note": "both parts"},
    "Solomon's Perjury": {"minutes": 121 + 146, "note": "both parts"},
    # The one row where the figure the box leads with cannot be watched
    # (CLU-425). Sanshiro Sugata's article prints three lengths — 97 minutes
    # (original cut), 79 (1943 cut), 91 (2026 cut) — and the collector takes
    # the first, which is the release Kurosawa made. That version does not
    # survive: the article's Censorship and alternate versions section says the
    # censors trimmed it after release, and quotes Toho's own on-screen card,
    # "1,845 feet of footage was cut in 1944 ... we were not able to locate the
    # cut footage". So the bar was measuring a sitting nobody can have, which is
    # the whole argument of gwlib/runtime.py, and kurosawa's row for the same
    # film has said so in its note all along.
    #
    # 79 and not 91: the 4K restoration the same article dates to 2026 recovered
    # twelve of the missing minutes, but it has played Cannes Classics and
    # cinemas in two countries, while 79 minutes is the cut on every disc and
    # every stream. The bar measures the version a reader can actually sit down
    # with, and the note names the other two so nobody has to guess which.
    #
    # This is a decided figure, not a read one, so `was` pins what the collector
    # says today: if the article's box changes, this stops the build rather than
    # overriding a figure it no longer describes.
    "Sanshiro Sugata": {
        "minutes": 79, "was": 97,
        "note": "the surviving cut — the 1943 release ran 97 minutes and its "
                "trimmed footage was never found; a 2026 restoration runs 91",
    },
}

# The animated features the poll ranked inside its Japanese-film list, which
# is how the animation question was settled. All four are on `ghibli` too, and
# the build checks that they still pair.
ANIMATED = ["Castle in the Sky", "My Neighbor Totoro",
            "Nausicaä of the Valley of the Wind", "The Castle of Cagliostro"]


def straight(t):
    """Curly apostrophes to straight ones, so a title reads and sorts like
    every other title in the catalogue.

    Also un-shouts a title typed entirely in capitals: fourteen rows have no
    English Wikipedia article and take their name from the item's English
    label instead, and one of those labels is set in caps. Nothing else about
    the string changes, and a title with any lower-case letter in it is left
    exactly as it is.
    """
    t = (t or "").replace("’", "'").replace("‘", "'")
    letters = [c for c in t if c.isalpha()]
    if len(letters) > 3 and all(c.isupper() for c in letters):
        t = re.sub(r"[A-Za-z]+", lambda m: m.group(0).capitalize(), t)
    return t


def undab(t):
    """Drop English Wikipedia's disambiguator: `Godzilla (1954 film)` is a
    page name, not a title."""
    return re.sub(r"\s*\((?:[^()]*\b(?:film|anime|movie)\b[^()]*)\)\s*$", "",
                  t or "").strip()


def era_of(year):
    for key, _label, lo, hi in ERAS:
        if (lo is None or year >= lo) and year <= hi:
            return key
    raise AssertionError("no era for %r" % year)


def is_film(kinds):
    """A film work, not merely something with `film` in its class name.

    Wikidata's classes for these items include `film character` and `film
    director`, which a substring test keeps: it left Tange Sazen the character
    standing beside The Million Ryo Pot and cost the poll's seventh-placed
    film its id. Every real class ends in the word — film, anime film,
    animated film, documentary film, silent film.
    """
    return any(re.search(r"\bfilms?$", str(k or "").lower())
               for k in kinds or ())


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
    poll, juries = d["poll"], d["juries"]
    facts, kine, wiki_rt = d["facts"], d["kine"], d["runtime_wiki"]
    ja_rt = d["runtime_jawiki"]
    rows = poll["rows"]

    # ---- the poll is the shape this file claims ---------------------------
    assert len(rows) == 198, "the poll ranked %d Japanese entries" % len(rows)
    ranks = [r["rank"] for r in rows]
    assert ranks == sorted(ranks), "the ranking is out of order"
    assert ranks[0] == 1 and ranks[-1] == 106, \
        "the ranking now runs 1..%d" % ranks[-1]
    # eleven entries are printed as plain text with no link to the magazine's
    # database, and reading only the linked ones stopped the ranking at 36th
    assert sum(1 for r in rows if not r["kid"]) == 11, \
        "%d entries now have no database link" % sum(1 for r in rows
                                                     if not r["kid"])
    # a tie block of size n is followed by rank + n, which is what proves the
    # ranks are a ranking and not a decoration
    sizes = collections.Counter(ranks)
    nxt = 1
    for rank in sorted(sizes):
        assert rank == nxt, "rank %d does not follow the tie above it" % rank
        nxt = rank + sizes[rank]
    assert poll["closed"] == 2008 and poll["published"] == 2009
    series = [r for r in rows if r["series"]]
    assert len(series) == 3, \
        "the poll ranks %d series entries, not 3" % len(series)
    assert {k for k, _n in JURIES} == set(juries), \
        "the jury panel and the data disagree: %s" % sorted(
            set(juries) ^ {k for k, _n in JURIES})

    # ---- clause one: the poll's ranking -----------------------------------
    films, dropped_series = {}, []
    for r in rows:
        if r["series"]:
            dropped_series.append(r)
            continue
        key = r["q"] or "kj:%s" % r["rid"]
        assert key not in films, "two poll rows resolve to %s" % key
        fa = facts.get(r["q"]) or {}
        films[key] = {
            "key": key, "q": r["q"], "via": r["via"], "kid": r["kid"],
            "rid": r["rid"], "ja": r["ja"], "year": r["year"],
            "rank": r["rank"], "poll": True, "src": {}, "titles": [],
            "enwiki": fa.get("enwiki")}
    # The poll page prints a two-digit year per row and gets one of them
    # wrong. A year is corrected only where the magazine's OWN database record
    # for the film that row links AND the film's Wikidata item both contradict
    # the page — two independent sources against one printed digit. It fires
    # once, for お嬢さん乾杯！, which the page dates 46 and the record dates
    # 1949/03/13. It does NOT fire for 飢餓海峡, where the record's 1964/12/27
    # release is a late-December one the magazine itself counts as 1965.
    fixed_year = []
    for f in films.values():
        rec = kine.get(f["kid"]) or {}
        m = re.match(r"(\d{4})", rec.get("released") or "")
        if not m or int(m.group(1)) == f["year"]:
            continue
        said = int(m.group(1))
        ys = (facts.get(f["q"]) or {}).get("pub_years") or []
        if said in ys:
            fixed_year.append((f["ja"], f["year"], said))
            f["year"] = said
    assert len(fixed_year) == 1, \
        "the poll's printed years are now wrong on %d rows, not 1: %s" \
        % (len(fixed_year), fixed_year)

    # the overrides, applied where they are keyed by KINENOTE number
    for kid, ov in OVERRIDES.items():
        f = next((x for x in films.values() if x["kid"] == kid), None)
        if f is None:
            continue
        if ov.get("drop_q"):
            f["q"] = None
        if ov.get("page"):
            f["forced_page"] = ov["page"]
        f["extra"] = ov.get("note")

    by_q = {f["q"]: f for f in films.values() if f["q"]}
    by_page = {f["enwiki"]: f for f in films.values() if f.get("enwiki")}

    # ---- the juries -------------------------------------------------------
    # An award row with no wikilink at all cannot be identified and does not
    # vote; the generator prints those rather than guessing at a title.
    orphans = []
    for jkey, _name in JURIES:
        for r in juries[jkey]:
            q, page = r.get("q"), r.get("page")
            if q and q in by_q:
                f = by_q[q]
            elif q:
                fa = facts.get(q) or {}
                ys = fa.get("pub_years") or []
                films[q] = {"key": q, "q": q, "via": "award link",
                            "kid": None, "ja": fa.get("ja"),
                            "year": min(ys) if ys else None,
                            "rank": None, "poll": False, "src": {},
                            "titles": [], "enwiki": fa.get("enwiki")}
                f = by_q[q] = films[q]
            elif page and page in by_page:
                # the film is already here from the poll; the jury just linked
                # its article rather than an item this file could use
                f = by_page[page]
            elif page:
                # No usable Wikidata item, but a real English article: All the
                # Long Nights carries an {{Infobox film}} and a running time
                # while its item is typed as a literary work with no date, and
                # keying on the item alone threw away all three of its votes.
                # The article is the identity and the award years are the year.
                key = "en:%s" % page
                if key not in films:
                    films[key] = {"key": key, "q": None, "via": "award article",
                                  "kid": None, "ja": None, "year": None,
                                  "rank": None, "poll": False, "src": {},
                                  "titles": [], "enwiki": page}
                    by_page[page] = films[key]
                f = films[key]
                f["year"] = min([x for x in (f["year"], r["year"]) if x])
            else:
                orphans.append((jkey, r["year"], r["t"]))
                continue
            f["src"].setdefault(jkey, r["year"])
            if r["t"] and r["t"] not in f["titles"]:
                f["titles"].append(r["t"])

    # ---- the gate ---------------------------------------------------------
    closed = poll["closed"]
    gated, near = [], []
    for f in films.values():
        if f["poll"]:
            gated.append(f)
        elif f["year"] and f["year"] > closed and len(f["src"]) >= MIN_JURIES:
            gated.append(f)
        elif f["year"] and f["year"] > closed:
            near.append(f)
    modern = [f for f in gated if not f["poll"]]
    assert len(gated) - len(modern) == 195, \
        "the poll contributes %d rows" % (len(gated) - len(modern))
    assert len(modern) == 30, (
        "the gate now admits %d modern films" % len(modern))

    # ---- ids: only where they hold up -------------------------------------
    refused_id = []
    for f in gated:
        if not f["q"]:
            continue
        fa = facts.get(f["q"]) or {}
        ys = fa.get("pub_years") or []
        why = None
        if not is_film(fa.get("kinds")):
            why = "not a film: %s" % ", ".join(str(k) for k in
                                               (fa.get("kinds") or ["unknown"]))
        elif ys and min(abs(y - f["year"]) for y in ys) > 1:
            why = min(ys, key=lambda y: abs(y - f["year"]))
        if why is not None:
            refused_id.append((f["ja"] or f["q"], f["year"], why))
            f["q"] = None
    qs = [f["q"] for f in gated if f["q"]]
    assert len(qs) == len(set(qs)), \
        "two rows share an id: %s" % [q for q in qs if qs.count(q) > 1][:3]

    # ---- names: the English article, reached through the source's id ------
    for f in list(films.values()):
        fa = facts.get(f["q"]) or {}
        page = f.get("forced_page") or fa.get("enwiki") or f.get("enwiki")
        en = undab(page or "") or fa.get("en")
        if en and CJK.search(en) and not page:
            en = None            # a Japanese label is not an English title
        f["t"] = straight(en or f["ja"] or (f["titles"] or [""])[0])
        f["english"] = bool(en)
        f["name_src"] = ("article" if page else
                         "label" if en else "japanese")
        f["director"] = fa.get("director")
        f["enwiki"] = page
        assert f["t"], "a row with no title at all: %s" % f["key"]

    # ---- the sanity checks, on their own merits ---------------------------
    for name, (year, rank) in CANARIES.items():
        hit = [f for f in gated
               if P.normt(f["t"]) == P.normt(name) and f["year"] == year]
        assert len(hit) == 1, "%s (%d) is not on this list" % (name, year)
        f = hit[0]
        assert f["poll"] and f["rank"] == rank, \
            "%s clears as rank %r, not %d" % (name, f["rank"], rank)
    # everything the notes name as a casualty, with the count they quote
    named = {}
    for f in films.values():
        fa = facts.get(f["q"]) or {}
        nm = undab(fa.get("enwiki") or "") or fa.get("en") or ""
        named.setdefault(P.normt(nm), []).append(f)
    for name, (year, n) in REFUSED.items():
        assert not [f for f in gated if P.normt(f["t"]) == P.normt(name)], \
            "the notes say %s (%d) is excluded and it is not" % (name, year)
        hit = [f for f in named.get(P.normt(name), [])
               if f["year"] and abs(f["year"] - year) <= 1]
        assert len(hit) == 1, \
            "%s (%d) is not in the data at all, so the note about it is " \
            "unchecked" % (name, year)
        assert len(hit[0]["src"]) == n, \
            "the notes say %s took %d juries; it took %d" \
            % (name, n, len(hit[0]["src"]))

    # ---- weights are all-or-nothing (CLU-131) -----------------------------
    used_overrides, multi, unweighable = set(), [], []
    for f in list(gated):
        page = f.get("enwiki")
        raw = (wiki_rt.get(page) or {}).get("raw") or ""
        w = (wiki_rt.get(page) or {}).get("min") if page else None
        src = "infobox"
        if not w:
            w, src = (kine.get(f["kid"]) or {}).get("min"), "kinenote"
        if not w:
            # Eleven entries are printed without a link, so the magazine's own
            # database has no record to fall back on. Japanese Wikipedia
            # documents two of those films and its infobox carries 上映時間.
            ja_page = (facts.get(f["q"]) or {}).get("jawiki")
            w, src = (ja_rt.get(ja_page) or {}).get("min"), "jawiki"
        ov = OVERRIDES.get(f["kid"]) or OVERRIDES.get(f["t"]) or {}
        if ov.get("minutes"):
            # An override that pins `was` is correcting a figure rather than
            # supplying a missing one, so it has to still be correcting the
            # same figure — otherwise it silently overrides a box that has
            # since been rewritten.
            assert "was" not in ov or w == ov["was"], \
                "the override for %s expects the source to give %s, it gives " \
                "%s — re-read the article before trusting either figure" \
                % (f["t"], ov["was"], w)
            w, src = ov["minutes"], "infobox"
            used_overrides.add(f["t"])
            f["extra"] = ov.get("note")
        if not w:
            # Weights are all or nothing, so a row nothing gives a running
            # time for cannot ship. Two of the poll's entries are in that
            # position — 現代性犯罪絶叫篇 理由なき暴行 and 襲(や）られた女, both
            # printed without a link, both absent from the magazine's own
            # database and from every Wikipedia. They are named on the page
            # rather than dropped silently.
            unweighable.append(f)
            gated.remove(f)
            continue
        assert 30 <= w <= 600, "%s runtime %r is not credible" % (f["t"], w)
        f["runtime"], f["rt_src"] = w, src
        # A field with several figures in it decided something; these are the
        # rows to read by hand, and the generator prints them every run.
        # Citations are stripped first — a {{sfn}} page number is not a
        # running time and put twenty false rows on the list.
        bare = re.sub(r"<ref.*|\{\{\s*(?:sfn|efn|refn|cite)[^{}]*\}\}", "",
                      raw, flags=re.I)
        if len(re.findall(r"\d{2,3}", bare)) > 1:
            multi.append((f["t"], f["year"], w, re.sub(r"\s+", " ", raw)[:96]))
    assert used_overrides == {t for t in OVERRIDES if not t.isdigit()
                              and OVERRIDES[t].get("minutes")}, \
        "a running-time override stopped matching a row: %s" % used_overrides
    assert len(unweighable) == 2, \
        "%d rows now have no running time anywhere: %s" \
        % (len(unweighable), [(f["ja"], f["year"]) for f in unweighable])
    modern = [f for f in gated if not f["poll"]]
    from_infobox = [f for f in gated if f["rt_src"] == "infobox"]
    from_kine = [f for f in gated if f["rt_src"] == "kinenote"]
    from_ja = [f for f in gated if f["rt_src"] == "jawiki"]
    assert len(from_infobox) + len(from_kine) + len(from_ja) == len(gated)
    disagree = [f for f in from_infobox
                if (facts.get(f["q"]) or {}).get("p2047")
                and abs(facts[f["q"]]["p2047"] - f["runtime"]) > 4]

    # ---- rows -------------------------------------------------------------
    gated.sort(key=lambda f: (f["year"], P.normt(f["t"])))
    entries, seen = [], set()
    for f in gated:
        n_juries = len(f["src"])
        if f["poll"]:
            gate_bit = "Kinema Junpo all-time, no. %d" % f["rank"]
            jury_bit = ("%d of %d juries" % (n_juries, len(JURIES))
                        if n_juries else None)
        else:
            gate_bit = "%d of %d juries" % (n_juries, len(JURIES))
            jury_bit = None
        ja = f["ja"] if f["ja"] and f["ja"] != f["t"] else None
        # An item id must be ASCII. Fourteen rows have no English name at all
        # and slugging a Japanese one leaves kanji in the id — which the
        # export code cannot survive, because btoa() throws on any character
        # above U+00FF and the export is btoa(JSON.stringify(ticked ids)).
        # Those rows take the poll's own database number instead.
        stem = P.slug(f["t"])
        if not stem or not stem.isascii():
            stem = "kj%s" % f["kid"] if f["kid"] else P.slug(f["key"])
        base = "jc-%d-%s" % (f["year"], stem)
        iid, k = base, 2
        while iid in seen:
            iid, k = "%s-%d" % (base, k), k + 1
        seen.add(iid)
        x = {"id": iid, "t": f["t"], "n": str(f["year"]),
             "w": round(f["runtime"] / 60.0, 2),
             "note": P.join_bits(gate_bit, jury_bit, f["director"], ja,
                                 "%d min" % f["runtime"], f.get("extra"))}
        if f["q"]:
            x["q"] = f["q"]
        entries.append(dict(x, era=era_of(f["year"]), year=f["year"],
                            runtime=f["runtime"], poll=f["poll"],
                            rank=f["rank"], juries=n_juries,
                            english=f["english"]))

    years = [e["year"] for e in entries]
    assert years == sorted(years), "the roster is out of release order"
    for e in entries:
        assert re.fullmatch(r"(19|20)\d{2}", e["n"]), e["id"]
    total_min = sum(e["runtime"] for e in entries)

    # ---- sections ---------------------------------------------------------
    sections = []
    for key, label, lo, hi in ERAS:
        got = [e for e in entries if e["era"] == key]
        assert got, "empty section %s" % key
        assert all((lo is None or e["year"] >= lo) and e["year"] <= hi
                   for e in got), key
        sections.append({
            "id": key, "title": label,
            "sub": " · ".join([
                "%d–%d" % (got[0]["year"], got[-1]["year"]),
                "%d films" % len(got),
                "%d hours" % round(sum(e["runtime"] for e in got) / 60.0)]),
            "intro": INTROS[key] % {
                "count": len(got), "min": MIN_JURIES,
                "spine": len(entries) - len(modern),
                "topten": sum(1 for e in got if e["rank"] and e["rank"] <= 10)},
            "items": [{k: v for k, v in e.items()
                       if k in ("id", "t", "n", "w", "note", "q")}
                      for e in got]})
    sections[1]["open"] = True

    # ---- the era prose must not outrun the articles it came from ----------
    ctx = P.ROOT / "scratch" / "agent-japan"
    for fname, claims in FRAMING.items():
        f = ctx / fname
        if not f.exists():
            continue
        src = f.read_text(encoding="utf-8")
        for claim in claims:
            assert claim in src, \
                "the era framing outran %s: %r" % (fname, claim)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)) == len(entries)
    for i in ids:
        assert i.isascii(), "non-ASCII item id %r breaks the export code" % i

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
    # A row carrying both an id and a plain year offers build.py two keys and
    # build.py merges them into ONE group, so groups are counted per row of
    # OURS, which is what merging does.
    mine_year = {(P.normt(e["t"]), e["year"]): e["id"] for e in entries}
    mine_keys = {k for k, _y in mine_year}
    mine_q = {e["q"]: e["id"] for e in entries if e.get("q")}
    by_key = {(P.normt(e["t"]), e["year"]): e["t"] for e in entries}
    groups, missed, near_title = collections.defaultdict(set), [], []
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
        elif year:
            # the other half of a near miss: the SAME year and a title one of
            # ours contains or is contained by. Japanese films are the worst
            # case for this — Sight & Sound prints Ugetsu Monogatari where
            # every other list prints Ugetsu — and a title-equality test can
            # never see it.
            for k, y in mine_year:
                if y == year and k != key and len(key) > 4 and len(k) > 4 \
                        and (key in k or k in key):
                    near_title.append((raw, slug, year, by_key[(k, y)]))
    for slug in ("criterion", "kurosawa", "ghibli", "godzilla",
                 "sight-and-sound", "cult-classics", "palme-dor"):
        assert any(slug in v for v in groups.values()), \
            "no sync group forms with %s" % slug
    lists_met = {s for v in groups.values() for s in v}
    by_id = {e["id"]: e["t"] for e in entries}
    top_share = max(groups.items(), key=lambda kv: len(kv[1]))
    most_shared = (by_id[top_share[0]], top_share[1])
    ghibli = sorted(by_id[i] for i, v in groups.items() if "ghibli" in v)
    assert ghibli == ANIMATED, \
        "the notes name these animated rows and the data has %s" % ghibli
    # the sentence naming them, with each one's place, built from the data
    ranked = sorted(((e["rank"], e["t"]) for e in entries if e["t"] in ANIMATED),
                    key=lambda kv: kv[0])
    bits = ["%s at %d%s" % (t, r, "th" if 4 <= r % 100 <= 20 else
                            {1: "st", 2: "nd", 3: "rd"}.get(r % 10, "th"))
            for r, t in ranked]
    animated_bit = ", ".join(bits[:-1]) + " and " + bits[-1]

    # ---- figures the notes quote, computed rather than typed --------------
    oldest, newest = entries[0], entries[-1]
    # the sentence this feeds is about the SECOND rule, so the leader has to
    # be one of the rows that rule admitted — taking it from every row named
    # The Twilight Samurai, which is on the poll and clears on the first rule
    top_juries = max((e for e in entries if not e["poll"]),
                     key=lambda e: e["juries"])
    # the whole roster's leader, printed rather than quoted on the page: it is
    # a poll row, so it says nothing about the second rule
    top_overall = max(entries, key=lambda e: e["juries"])
    at_gate = sum(1 for e in entries
                  if not e["poll"] and e["juries"] == MIN_JURIES)
    shortest = min(entries, key=lambda e: e["runtime"])
    longest = max(entries, key=lambda e: e["runtime"])
    biggest = max(sections, key=lambda s: len(s["items"]))
    with_id = sum(1 for e in entries if e.get("q"))
    no_english = [e for e in entries if not e["english"]]
    names = collections.Counter(f["name_src"] for f in gated)
    assert names["japanese"] == len(no_english)
    best_film = [n for _k, n in JURIES[:-1]]
    jury_names = ", ".join(best_film[:-1]) + " and " + best_film[-1]
    assert JURIES[-1][0] == "oscar", "the last jury is the odd one out"
    from_source = sum(1 for f in gated if f["q"] and f["via"] == "kinenote")
    from_jawiki = sum(1 for f in gated
                      if f["q"] and f["via"] in ("title", "search",
                                                 "release date"))
    n_spine = len(entries) - len(modern)
    top_of_poll = next(e["t"] for e in entries if e["rank"] == 1)
    tail_rank = max(e["rank"] for e in entries if e["poll"])
    tail_size = sum(1 for e in entries if e["rank"] == tail_rank)
    # films the poll passed over that two of the juries did name, which is the
    # argument for the second clause not reaching back
    pre_jury = sum(1 for f in films.values()
                   if not f["poll"] and f["year"] and f["year"] <= closed
                   and len(f["src"]) >= MIN_JURIES)

    prop = {
        "slug": SLUG,
        "title": "Japanese Cinema",
        "subtitle": "Kinema Junpo's all-time ranking, and what came after",
        "kind": "films",
        # A national-cinema survey, so the 40-59 band in POPULARITY.md — it
        # needs a sentence of explanation to a general audience. Placed just
        # above Korean Cinema (56) because the names inside it travel further
        # on their own (Kurosawa, Godzilla, Studio Ghibli), and below the
        # Criterion Collection (63) and Kurosawa (62), whose name carries a
        # list by itself.
        "popularity": 58,
        "year": "%d–%d" % (oldest["year"], newest["year"]),
        "blurb": "%d films Japan's own film magazine and its film juries "
                 "picked out, %d to %d — about %d hours. No order; let "
                 "the picker choose."
                 % (len(entries), oldest["year"], newest["year"],
                    round(total_min / 60.0)),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "random": True,
        "notes": [
            ["“The best of Japanese cinema” is a verdict, so this list does "
             "not pass one.",
             "The spine is somebody else's: %d of the Japanese films Kinema "
             "Junpo ranked in its ninetieth-anniversary poll. Japan's oldest "
             "film magazine, founded in 1919, asked %d critics, film-makers "
             "and writers for the ten Japanese films that stayed with them, "
             "then printed the whole tally top to bottom — %s heads it, and "
             "%d of these rows share the %dth place it ends on. Every row "
             "says where it placed. Nothing was added because it felt right."
             % (n_spine, poll["voters"], top_of_poll, tail_size, tail_rank)],
            ["That poll was taken in 2009, and stops at 2008.",
             "So Drive My Car could not have been on it, and neither could "
             "Shoplifters. The %d films released since are here on a second "
             "rule, stated so you can argue with it: at least %d of Japan's "
             "eight juries must have named the film Best Film. Seven of the "
             "eight are prizes — %s — and the eighth is the committee that "
             "picks Japan's Academy Award entry. The magazine that made the "
             "poll is the first of them, because its annual Best Ten has run "
             "since 1924. %s leads with %d; %d of these rows clear on exactly "
             "%d. This is a coarser instrument than a survey and the last "
             "section should be read as provisional."
             % (len(modern), MIN_JURIES, jury_names, top_juries["t"],
                top_juries["juries"], at_gate, MIN_JURIES)],
            ["Why the juries do not govern the years the poll covers.",
             "Because the data says not to. %d films from before %d took at "
             "least %d of these prizes and the poll did not rank them, and "
             "the loudest is Sumo Do, Sumo Don't, which took seven of the "
             "eight juries in 1992 and does not appear in the magazine's "
             "all-time ranking at all. A jury names one film a year whatever "
             "the year was like. A survey of the whole history does not, and "
             "the two are not the same kind of evidence."
             % (pre_jury, closed + 1, MIN_JURIES)],
            ["What that costs, said plainly.",
             "Spirited Away is not here. Four of the eight juries named it, "
             "the poll's %d voters did not rank it, and it came out in 2001, "
             "so the second rule cannot reach it either. Princess Mononoke "
             "and Hana-bi go the same way at three juries each, and A Taxing "
             "Woman at five; Kwaidan, Fires on the Plain, The Burmese Harp "
             "and Gate of Hell have one apiece and no place in the ranking. "
             "That is the honest cost of letting somebody else choose, and it "
             "is worth arguing with."
             % poll["voters"]],
            ["Animation is in, and the source is what decided it.",
             "Kinema Junpo polled animation separately in the same survey, "
             "which could have been read as putting it outside the "
             "Japanese-film ranking. It did not — %s are all ranked inside "
             "that ranking. All four are on the Studio Ghibli list here as "
             "well, and ticking one ticks the other. Spirited Away is not, "
             "and the reason is above rather than a wish to avoid the "
             "overlap." % animated_bit],
            ["The eras come from a history, not from us.",
             "The poll is a flat ranking and divides nothing, so the six "
             "sections take their boundaries from Wikipedia's “Cinema of "
             "Japan” and the articles it leads to, and each boundary is a "
             "sentence one of them states: the 1950s as the Golden Age; "
             "Shochiku launching the New Wave from inside the studio system "
             "in 1960; 1971, the year television had done enough damage that "
             "Nikkatsu stopped making anything but Roman Porno; and the "
             "Heisei era beginning in 1989. The build checks each of those "
             "sentences is still in the articles before it will run."],
            ["Bar widths are running times, and none was invented.",
             "All %d rows are weighted, %d hours in total. %d figures are the "
             "film's own English Wikipedia infobox; %d have no English article "
             "at all and take the running time from Kinema Junpo's own "
             "database record for the film; %d have neither and take it from "
             "the Japanese Wikipedia article. Wikidata's runtime is carried "
             "only as a cross-check and disagrees with the infobox on %d rows, "
             "which is why it is not the source. The range runs from %s at %d "
             "minutes to %s at %d. Two of the poll's entries are not here at "
             "all because no source we could reach gives a running time for "
             "them, and a list with weights cannot carry a row without one."
             % (len(entries), round(total_min / 60.0), len(from_infobox),
                len(from_kine), len(from_ja), len(disagree), shortest["t"],
                shortest["runtime"], longest["t"], longest["runtime"])],
            ["Titles are English Wikipedia's, and no id came from a title "
             "this file trusted on its own.",
             "The poll prints Japanese titles and nothing else, so the "
             "English name on a row is the film's English Wikipedia title, "
             "reached through the KINENOTE database number the poll linked "
             "and never by looking a title up — %d rows that way, and %d more "
             "from the Wikidata item's English name where there is no article "
             "to take one from. The magazine's own English field exists and "
             "is not usable: it calls Nausicaä of the Valley of the Wind "
             "“Warriors of the Wind”, after the butchered American cut, and "
             "Castle in the Sky “Laputa”. The remaining %d rows have no "
             "English name anywhere and keep their Japanese one, because "
             "nothing here was romanised by us. %d of the %d rows carry a "
             "Wikidata id: %d from the poll's own numbering, %d recovered a "
             "row at a time — by exact Japanese page title, by the exact "
             "release date the magazine's database prints, then by search — "
             "under a gate that refuses anything that is not a film, dated to "
             "the right year, carrying no other database number and named "
             "like the row, and that refuses outright when two candidates "
             "survive; the rest come from the award articles' own wikilinks."
             % (names["article"], names["label"], names["japanese"],
                with_id, len(entries), from_source, from_jawiki)],
            ["The same film on two lists here is the point.",
             "%d of these films are already somewhere else in the catalogue — "
             "across %s — and ticking one ticks the other. %s is on %d other "
             "lists, more than anything else here."
             % (len(groups), ", ".join(sorted(lists_met)), most_shared[0],
                len(most_shared[1]))],
            "Ranking from Kinema Junpo's “オールタイム・ベスト 映画遺産200” "
            "(2009), read from the magazine's own site via the Internet "
            "Archive; for films released after it, the Kinema Junpo, "
            "Mainichi, Blue Ribbon, Japan Academy, Hochi, Nikkan Sports and "
            "Yokohama Best Film records on Wikipedia plus Japan's Academy "
            "Award submissions; era framing from Wikipedia's “Cinema of "
            "Japan”, “Japanese New Wave”, “Nikkatsu” and “Pink film”; running "
            "times from each film's English Wikipedia infobox, its archived "
            "KINENOTE record or its Japanese Wikipedia infobox; ids from "
            "KINENOTE via Wikidata.",
        ],
        "sections": sections,
    }

    P.write(prop)
    print("wrote %s.json" % SLUG)
    print("  %d sections, %d films — all weighted, %d min (%.1f hours)"
          % (len(sections), len(ids), total_min, total_min / 60.0))
    print("  gate: the poll's %d, plus %d films since %d with >=%d of %d juries"
          % (len(entries) - len(modern), len(modern), closed, MIN_JURIES,
             len(JURIES)))
    print("  ids: %d of %d rows (%d from the poll's own KINENOTE numbers, "
          "%d recovered from ja.wikipedia, the rest from award wikilinks)"
          % (with_id, len(entries), from_source, from_jawiki))
    for t, y, why in refused_id:
        print("    id refused %-30s row %s vs item %s" % (t, y, why))
    print("  runtimes: %d from English infoboxes, %d from KINENOTE, %d from "
          "Japanese infoboxes, %d where Wikidata disagrees"
          % (len(from_infobox), len(from_kine), len(from_ja), len(disagree)))
    print("  rows the poll ranks that cannot be weighed, so are not here (%d):"
          % len(unweighable))
    for f in unweighable:
        print("     rank %-4s %d %s" % (f["rank"], f["year"], f["ja"]))
    print("  rows with no English title (%d):" % len(no_english))
    for e in no_english:
        print("     %s %s" % (e["n"], e["t"]))
    for s in sections:
        print("   %-22s %3d  %s" % (s["title"], len(s["items"]), s["sub"]))
    print("  %d sync groups across %d other lists:"
          % (len(groups), len(lists_met)))
    for s, n in collections.Counter(
            s for v in groups.values() for s in v).most_common(15):
        print("   %-24s %3d" % (s, n))
    print("  near misses — same title, a different year (%d):"
          % len(set(missed)))
    for raw, slug, year, ours in sorted(set(missed)):
        print("   %-34s %-18s theirs=%s ours=%s" % (raw, slug, year, ours))
    print("  near misses — same year, a title that nearly matches (%d):"
          % len(set(near_title)))
    for raw, slug, year, ours in sorted(set(near_title)):
        print("   %-34s %-18s %s  vs our %r" % (raw, slug, year, ours))
    print("  running-time fields with more than one figure (%d), the rows to "
          "read by hand:" % len(multi))
    for t, y, w, raw in sorted(multi):
        print("   %-34s %s -> %3d  %s" % (t[:34], y, w, raw))
    print("  post-%d films the juries named only once (%d), all excluded:"
          % (closed, len(near)))
    for f in sorted(near, key=lambda f: (f["year"], f["t"])):
        print("   %s %-40s %s" % (f["year"], f["t"][:40], sorted(f["src"])))
    print("  series rows dropped (%d):" % len(dropped_series))
    for r in dropped_series:
        print("   rank %d %s (%s-%s)" % (r["rank"], r["ja"], r["year"],
                                         r["end_year"]))
    print("  award rows with no wikilink, not counted (%d)" % len(orphans))
    print("  ghibli rows: %s" % ghibli)
    print("  biggest section: %s;  most juries on any row: %s (%d)"
          % (biggest["id"], top_overall["t"], top_overall["juries"]))


if __name__ == "__main__":
    main()
