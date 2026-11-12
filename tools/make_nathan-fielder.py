#!/usr/bin/env python3
"""Generate properties/nathan-fielder.json.

    PYTHONIOENCODING=utf-8 python tools/make_nathan-fielder.py

Everything Nathan Fielder created, in the order it came out: four seasons and
a special of *Nathan for You*, two seasons of *The Rehearsal*, one season of
*The Curse*, and his first feature, the documentary *You Can See Everything*.
Fifty-four episodes and one film, four sections, nothing else.

Every title, number, airdate and count below is machine-read from Wikipedia
wikitext cached in scratch/nathan-fielder/ — the "Nathan Fielder" article for
the roster, "List of Nathan for You episodes" plus "Nathan for You" for the
cable show, "The Rehearsal (TV series)" and "The Curse (American TV series)"
for the other two, and "You Can See Everything" for the film. Nothing is typed
in from memory, and every number this file prints is asserted against the
source that produced it before anything is written.

THE RULE FOR WHAT IS ON THE LIST: HE CREATED IT
------------------------------------------------
Matt Johnson's list settled on Director = Yes, because his filmography carries
a Director column with {{Yes}} in it. Fielder's does not: his filmography is
two tables with a free-text Notes column, and he is variously creator, writer,
director, executive producer, consulting producer and actor, frequently four
of those on the same row. So a credit has to be chosen rather than read off a
column, and this list chooses **creator**.

That is the credit that makes these his. A bare directing filter would sweep in
two episodes of Sacha Baron Cohen's *Who Is America?* and five short films with
no article, no runtime and no way to watch them; a producing filter would sweep
in *How To with John Wilson*, which is John Wilson's show. Creator admits
exactly three works and they are exactly the three the show-off sentence about
Fielder always names:

  * ''Nathan for You'' — "Creator, writer, director, and executive producer",
    with Michael Koman;
  * ''The Rehearsal''  — "Creator, executive producer, writer, director";
  * ''The Curse''      — "Main role; also co-creator, writer and director",
    with Benny Safdie.

AND A FEATURE FILM HE DIRECTED (CLU-623). Nathan, 2026-11-11, on *You Can See
Everything*, the 2026 documentary he co-directed with Lance Oppenheim: "it
definitely gets added to the list". A film has no creator credit to read, so on
the Film table the credit that makes a work his is director: a row that is not
a short film, has its own article, and carries a director or co-director
credit. That admits exactly one today, and main() pins it by name. The shorts
stay off for the reasons below; the acting rows carry no directing credit.

The test is a bare \\bcreator\\b against the Role and Notes cells of both
filmography tables, case-insensitive so it catches "Creator" and "co-creator"
alike. Both cells, not just Notes: the Role column normally holds a character
name, but where he does not appear in a work it holds his crew credit instead —
the short film *Kelly 5-9* keeps its entire directing credit there and has
nothing in Notes but "Short film". Reading one column is how a credit filter
goes silently short by a row, and this generator did exactly that for one
draft before the short-film count came out at four.

main() asserts the roster the test produces is those four and no others. It also
pins the three near-misses by name — *How To with John Wilson* (executive
producer only), *Who Is America?* (consulting producer and co-director) and
*Jon Benjamin Has a Van* (creative consultant, the one row whose Notes cell
contains the letters "creat" without a creator credit) — so that a Wikipedia
editor rewording any of them into a creator credit breaks the build rather
than silently changing what this list means.

THE LEAD IS CROSS-CHECKED AGAINST THE FILMOGRAPHY
--------------------------------------------------
A rowspan in a wikitable silently loses rows, and a recent work reaches an
article's lead paragraph before its filmography table catches up — which is
exactly how the Matt Johnson list nearly shipped one film short. So main()
pulls every italicised wikilink out of the lead and asserts each one is either
a shipped section or a page this file excludes on purpose, by name, with a
reason. It also asserts the reverse: every shipped work is named in the lead.
A fourth Fielder show or a second film appearing in the lead fails the build.

The table reader carries rowspans down anyway, though neither of these two
tables uses one today. It costs four lines and it is the bug that has bitten
this repo three times.

WEIGHTS: NONE, AND THE CHECK IS IN THE CODE
--------------------------------------------
All-or-nothing, and it is nothing. The page resolves
`WEIGHT = x.w >= 0 ? x.w : 1`, so one unweighted row on an otherwise weighted
list silently books itself as a full hour; since the home page fills its bars
by hours on fully weighted lists, that distortion is visible to readers.

Not one of the three articles publishes a per-episode runtime. main() asserts
all three legs of that:

  * *The Rehearsal* infobox: "27–58 minutes" — a range for the series;
  * *The Curse* infobox: "38–69 minutes" — a range for the series;
  * *Nathan for You* infobox: a flat "21 minutes", which looks usable and is
    not. Its own episode list calls the finale, "Finding Frances", a
    "90-minute series finale" in the same article. A series-level figure
    applied to every episode would be an invention with a citation stapled to
    it, and it would be wrong by 69 minutes on that row alone.
  * and no {{Episode list}} block on any of the three pages carries a RunTime
    field at all.

Every one of those is an assertion, not a comment. If The Rehearsal's infobox
ever states a single figure, or the episode blocks grow RunTime fields, or the
Nathan for You finale stops being described as 90 minutes, this build fails and
whoever is standing there weights the list instead of the omission quietly
outliving its reason. These shows have wildly uneven episodes — 27 to 69
minutes across the two prestige runs — so an invented uniform figure would be
worse here than on most lists.

SEASONS ARE ASSERTED THREE WAYS, AND A NEW ONE BREAKS THE BUILD
----------------------------------------------------------------
None of the three shows has a per-season Wikipedia article — no {{Main}} link
to one exists on any of them — so "each season's own infobox" resolves to the
strongest per-season sources that do exist, and every season is checked against
all of them:

  1. the {{Series overview}} `episodesN` count, and its `startN`/`endN` dates
     against the first and last episode this file actually parsed for that
     season;
  2. the series {{Infobox television}} `num_seasons` and `num_episodes`;
  3. the article's own `=== Season N (year) ===` headings, which is how the
     episodes are grouped in the first place — the Nathan for You special sits
     between the third and fourth seasons and is filed under its own heading,
     which is why it lands between S3E8 and S4E1 here rather than at the end.

Numbering is asserted contiguous overall and within each season, airdates are
asserted non-decreasing, and every episode is asserted to have aired on or
before the day this runs. As of this writing the counts are 4+special / 2 / 1
seasons and 32 / 12 / 10 episodes; a fifth Nathan for You, a third Rehearsal or
a second Curse changes those numbers and fails this build, which is the point.

SPOILERS
--------
*The Curse* and *The Rehearsal* both turn on things a row note would ruin, so
neither section carries a single row note and the intros describe premises
only. The two notes on the whole list are on Nathan for You's special (what it
is) and its finale (that it is feature-length), and neither gives anything away.

THE BLURB CARRIES NO EPISODE COUNT (CLU-190), and no hours, because this list
does not track them.
"""
import datetime
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki  # noqa: E402

SLUG = "nathan-fielder"
CACHE = prop.ROOT / "scratch" / SLUG
ARTICLE = "Nathan Fielder"

NFY = "Nathan for You"
NFY_EPS = "List of Nathan for You episodes"
REHEARSAL = "The Rehearsal (TV series)"
CURSE = "The Curse (American TV series)"
FILM = "You Can See Everything"

# The roster rule, as a regex against the filmography Notes cell. \bcreator\b
# matches "Creator" and the hyphenated "co-creator" alike, and does not match
# "Creative consultant".
CREATOR = re.compile(r"\bcreator\b", re.I)
# The film half of the rule (CLU-623): a Film-table row that is not a short,
# has an article, and credits him as director — "co-directed" included.
DIRECTOR = re.compile(r"\bdirect(?:or|ed)\b", re.I)

# Pages the lead names that this list deliberately does not ship. The lead
# cross-check refuses to pass a title that is neither a section nor in here,
# so a fourth Fielder show cannot go quietly missing.
EXCLUDED = {
    "This Hour Has 22 Minutes":
        ("This Hour Has 22 Minutes",
         "he was a correspondent on it, not its creator"),
    "Important Things with Demetri Martin":
        ("Important Things with Demetri Martin",
         "he wrote for it and appeared on it; Demetri Martin created it"),
    "How To with John Wilson":
        ("How To with John Wilson",
         "he executive produced it; John Wilson created it"),
    "Time (magazine)":
        ("Time", "a magazine that put him on a list, not a work of his"),
}

# Near-misses pinned by name: the Notes cell each one must keep failing on. If
# an editor rewords any of these into a creator credit the build stops.
NEAR_MISSES = {
    "How To with John Wilson": "Executive producer",
    "Who Is America?": "Consulting producer",
    "Jon Benjamin Has a Van": "Creative consultant",
}

# Small counts read better spelled out in prose, and every count in the notes
# is derived rather than typed, so the spelling has to be derived too.
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
         7: "seven", 8: "eight", 9: "nine", 10: "ten"}

_CELL = re.compile(r"^\|\s*(?:([^|\[{]*=[^|\[{]*)\|)?\s*(.*)$", re.S)
_RANGE = re.compile(r"(\d{1,3})\s*[–—-]\s*(\d{1,3})\s*minutes")
_FLAT = re.compile(r"^(\d{1,3})\s*minutes$")


def table_after(text, heading):
    """The first wikitable following a `===heading===` line."""
    m = re.search(r"^=+\s*%s\s*=+\s*$" % re.escape(heading), text, re.M)
    assert m, "no %r section on the article" % heading
    a = text.index('{| class="wikitable', m.end())
    return text[a:text.index("\n|}", a)]


def table_rows(seg, ncols):
    """Cells per row, with rowspan carried down, header chunks skipped.

    Neither filmography table rowspans anything today. The carry stays because
    positional cell-picking without it has silently shifted a Year column in
    this repo three times; the day someone merges two rows on a shared year,
    this reader is already right."""
    out, pending = [], {}
    for chunk in seg.split("\n|-")[1:]:
        lines = [l.strip() for l in chunk.split("\n") if l.strip().startswith("|")]
        if not lines:
            continue                       # the `! Year / ! Title` header chunk
        raw = iter(lines)
        cols = []
        for c in range(ncols):
            if c in pending:
                cols.append(pending[c][1])
                pending[c][0] -= 1
                if pending[c][0] == 0:
                    del pending[c]
                continue
            m = _CELL.match(next(raw, "|"))
            attrs, content = m.group(1) or "", m.group(2)
            cols.append(content)
            sp = re.search(r'rowspan="?(\d+)', attrs)
            if sp and int(sp.group(1)) > 1:
                pending[c] = [int(sp.group(1)) - 1, content]
        out.append(cols)
    return out


def link(cell):
    """The wikilink target inside a cell, or None."""
    m = re.search(r"\[\[([^\]|]+)", cell or "")
    return m.group(1).strip() if m else None


def date_in(field, what):
    """The first {{Start date|y|m|d}} / {{End date|y|m|d}} in a field."""
    m = re.search(r"\{\{\s*(?:start|end) date\s*\|\s*(\d{4})\s*\|\s*(\d{1,2})"
                  r"\s*\|\s*(\d{1,2})", field or "", re.I)
    assert m, "%s: no full date in %r" % (what, (field or "")[:60])
    return datetime.date(*(int(g) for g in m.groups()))


def section_slices(text, headings):
    """(heading text, wikitext) for each `=== ... ===` heading given, in the
    order they appear in the article. The Nathan for You special has its own
    heading between Season 3 and Season 4, which is the only reason its row
    lands in the middle of that section instead of after it."""
    found = []
    for m in re.finditer(r"^=+\s*(.+?)\s*=+\s*$", text, re.M):
        if m.group(1) in headings:
            found.append((m.group(1), m.end()))
    assert [h for h, _ in found] == list(headings), \
        "the season headings changed: %s" % [h for h, _ in found]
    out = []
    for i, (head, at) in enumerate(found):
        end = found[i + 1][1] if i + 1 < len(found) else len(text)
        out.append((head, text[at:end]))
    return out


def parse_season(text, label):
    """(overall, in-season, title, airdate) per episode of one season block."""
    got = []
    for overall, inseason, title, _year, block in wiki.episodes(text):
        assert overall, "%s: an episode block has no EpisodeNumber" % label
        assert title, "%s: episode %s has no title" % (label, overall)
        got.append((overall, inseason, title,
                    date_in(re.search(r"\|\s*OriginalAirDate\s*=\s*(.*)",
                                      block).group(1),
                            "%s E%s" % (label, overall))))
    assert got, "%s: no episode blocks" % label
    return got


def main():
    today = datetime.date.today()

    # ---- the roster: two filmography tables, one credit test ---------------
    art = wiki.wikitext(ARTICLE, cache_dir=CACHE)
    assert art, "no cached wikitext for %r" % ARTICLE
    lead = art[:art.index("\n==")]

    roster, rejected = [], {}
    for table in ("Film", "Television"):
        for year, title, role, notes in table_rows(table_after(art, table), 4):
            rec = {"t": wiki.clean(title), "page": link(title),
                   "year": wiki.clean(year), "notes": wiki.clean(notes),
                   "role": wiki.clean(role), "table": table}
            # Both columns, not just Notes: the Role column is normally a
            # character name but is used for a crew credit where he does not
            # appear — "Kelly 5-9" carries its whole directing credit there.
            # Reading one column only is how a credit filter goes silently
            # short by a row.
            rec["credits"] = prop.join_bits(rec["role"], rec["notes"])
            feature = (table == "Film" and rec["page"]
                       and "Short film" not in rec["notes"]
                       and DIRECTOR.search(rec["credits"]))
            if CREATOR.search(rec["credits"]) or feature:
                roster.append(rec)
            else:
                rejected[rec["t"]] = rec
    assert len(rejected) + len(roster) >= 30, (len(rejected), len(roster))

    shows = [r for r in roster if r["table"] == "Television"]
    films = [r for r in roster if r["table"] == "Film"]
    got = [r["t"] for r in shows + films]
    assert [r["t"] for r in shows] == [NFY, "The Rehearsal", "The Curse"], got
    assert [r["page"] for r in shows] == [NFY, REHEARSAL, CURSE], shows
    assert all(CREATOR.search(r["credits"]) for r in shows), shows
    # The one feature, pinned by name: a second directed feature arriving in
    # the filmography fails here rather than shipping unread.
    assert [r["page"] for r in films] == [FILM], films
    film_row = films[0]
    assert not CREATOR.search(film_row["credits"]), film_row
    assert "Feature directorial debut" in film_row["notes"], film_row
    assert "Lance Oppenheim" in film_row["notes"], film_row

    # The three near-misses, pinned so a reworded Notes cell fails loudly
    # rather than silently changing what "everything he created" means.
    for title, must_say in NEAR_MISSES.items():
        row = rejected.get(title)
        assert row, "%s has fallen out of the filmography" % title
        assert must_say.lower() in row["credits"].lower(), \
            "%s's credits no longer say %r: %r" % (title, must_say,
                                                   row["credits"])
        assert not CREATOR.search(row["credits"]), \
            "%s now carries a creator credit — it belongs on this list" % title

    # The short films the notes point at, counted rather than remembered: film
    # rows with a directing credit and no article to link to. They are real
    # directing work and they are off this list because it is not a directing
    # list — and because Wikipedia gives them no runtime and no way to watch.
    shorts = [r for r in rejected.values()
              if r["table"] == "Film" and "Short film" in r["notes"]]
    assert shorts, "the short films have left the filmography"
    short_years = sorted(int(r["year"]) for r in shorts)
    # every one of them is a directing credit — the reason the notes mention
    # them at all — and none of them has an article to read a runtime out of
    assert all(re.search(r"\bdirector\b", r["credits"], re.I) for r in shorts), \
        [(r["t"], r["credits"]) for r in shorts]
    assert all(r["page"] is None for r in shorts), \
        ("a short film gained a Wikipedia article: %s — it may now publish a "
         "runtime" % [r["t"] for r in shorts if r["page"]])
    # the acting the notes name, so the sentence cannot outlive the credits
    for acting in ("The Disaster Artist", "The Simpsons", "Rick and Morty",
                   "Bob's Burgers"):
        assert acting in rejected, \
            "%s is no longer on the filmography; the notes name it" % acting

    # ---- the film's own article --------------------------------------------
    film = wiki.wikitext(FILM, cache_dir=CACHE)
    assert film, "no cached wikitext for %r" % FILM
    film_ib = wiki.infobox(film, kind="film")
    assert film_ib, "no film infobox on %s" % FILM
    assert wiki.clean(film_ib("name")) == FILM, film_ib("name")
    film_dirs = wiki.clean(film_ib("director"))
    assert "Nathan Fielder" in film_dirs and "Lance Oppenheim" in film_dirs, \
        film_dirs
    assert wiki.clean(film_ib("distributor")) == "A24", film_ib("distributor")
    film_dates = [datetime.date(*(int(g) for g in m)) for m in re.findall(
        r"\|\s*(\d{4})\s*\|\s*(\d{1,2})\s*\|\s*(\d{1,2})\b",
        film_ib("released"))]
    assert film_dates and film_dates == sorted(film_dates), film_ib("released")
    # the last date in {{Film date}} is the general release; the first is the
    # festival premiere
    film_out = film_dates[-1]
    assert film_out <= today, \
        ("%s is dated %s, which is not out yet; this catalogue lists only "
         "what is out" % (FILM, film_out))
    assert str(film_out.year) == film_row["year"], (film_out, film_row["year"])
    film_lead = wiki.clean(film[film.index("\n" + "'" * 3):film.index("\n==")])
    # the intro below says these things, so the article has to keep saying them
    for phrase in ("documentary film", "Elizabeth Holmes", "Theranos",
                   "Billy Evans", "invited a film crew", "defrauding investors",
                   "theatrically released by A24"):
        assert phrase in film_lead, "%s's lead no longer says %r" % (FILM, phrase)

    # ---- the lead cross-check: nothing the lead names may go missing -------
    named = {n for n in (link(m.group(0))
                         for m in re.finditer(r"''\[\[[^\]]+\]\]''", lead)) if n}
    shipped = {r["page"] for r in roster}
    unaccounted = named - shipped - set(EXCLUDED)
    assert not unaccounted, \
        ("the lead names %s and this list neither ships nor excludes it — a "
         "filmography table lagging its own lead is how a list ships short"
         % sorted(unaccounted))
    for r in roster:
        assert r["page"] in named, \
            "%s is in the filmography but not the lead — check it is his" % r["t"]

    # ---- Nathan for You ----------------------------------------------------
    nfy = wiki.wikitext(NFY, cache_dir=CACHE)
    nfy_eps_page = wiki.wikitext(NFY_EPS, cache_dir=CACHE)
    nfy_ib = wiki.infobox(nfy, kind="television")
    assert nfy_ib, "no infobox on %s" % NFY
    assert nfy_ib("num_seasons").strip() == "4", nfy_ib("num_seasons")
    assert nfy_ib("num_episodes").strip() == "32", nfy_ib("num_episodes")
    assert "Comedy Central" in nfy_ib("channel"), nfy_ib("channel")
    nfy_creators = wiki.clean(nfy_ib("creator"))
    assert "Nathan Fielder" in nfy_creators and "Michael Koman" in nfy_creators, \
        nfy_creators
    # ended, and asserted so a fifth season cannot arrive unnoticed
    assert "would not return for a fifth season" in wiki.clean(nfy_eps_page), \
        "the episode list no longer says Nathan for You ended at four seasons"

    nfy_heads = ["Season 1 (2013)", "Season 2 (2014)", "Season 3 (2015)",
                 "Special (2017)", "Season 4 (2017)"]
    nfy_blocks = [(h, parse_season(seg, h))
                  for h, seg in section_slices(nfy_eps_page, nfy_heads)]

    # ---- The Rehearsal -----------------------------------------------------
    reh = wiki.wikitext(REHEARSAL, cache_dir=CACHE)
    reh_ib = wiki.infobox(reh, kind="television")
    assert reh_ib, "no infobox on %s" % REHEARSAL
    assert reh_ib("num_seasons").strip().split("<")[0] == "2", \
        ("The Rehearsal is no longer a two-season show — a third season needs "
         "a section, and the notes say there is not one: %r"
         % reh_ib("num_seasons"))
    assert reh_ib("num_episodes").strip().split("<")[0] == "12", \
        reh_ib("num_episodes")
    assert "HBO" in reh_ib("network"), reh_ib("network")
    assert wiki.clean(reh_ib("creator")) == "Nathan Fielder", reh_ib("creator")
    assert ("In January and September 2026, Fielder was still said to be "
            "developing ideas for a third season") in reh, \
        ("the article no longer says a third Rehearsal is only an idea as of "
         "September 2026 — the note 'Where the three shows stand' says so")
    # the order argument, in the source's own words
    assert "premise for ''The Rehearsal'' developed from Fielder's series" in reh, \
        "the article no longer derives The Rehearsal from Nathan for You"
    reh_heads = ["Season 1 (2022)", "Season 2 (2025)"]
    reh_blocks = [(h, parse_season(seg, h))
                  for h, seg in section_slices(reh, reh_heads)]

    # ---- The Curse ---------------------------------------------------------
    curse = wiki.wikitext(CURSE, cache_dir=CACHE)
    curse_ib = wiki.infobox(curse, kind="television")
    assert curse_ib, "no infobox on %s" % CURSE
    assert curse_ib("num_seasons").strip() == "1", \
        ("The Curse now has more than one season — it needs season numbering "
         "and a second block: %r" % curse_ib("num_seasons"))
    assert curse_ib("num_episodes").strip().split("<")[0] == "10", \
        curse_ib("num_episodes")
    assert "Showtime" in curse_ib("network"), curse_ib("network")
    creators = wiki.clean(curse_ib("creator"))
    assert "Nathan Fielder" in creators and "Benny Safdie" in creators, creators
    assert "{{Series overview" not in curse, \
        "The Curse grew a Series overview — re-derive its season structure"
    curse_eps = parse_season(curse[curse.index("== Episodes =="):], "The Curse")
    assert all(e[1] is None for e in curse_eps), \
        "The Curse's episode blocks grew in-season numbers; the row labels " \
        "are bare E1..E10 because the source numbers them that way"

    # ---- per-season counts, three sources, plus dates ----------------------
    def overview(text, page):
        i = text.index("{{Series overview")
        seg = text[i:text.index("\n}}", i)]
        eps = {int(k): int(v)
               for k, v in re.findall(r"\|\s*episodes(\d+)\s*=\s*(\d+)", seg)}
        starts = {int(k): date_in(v, page)
                  for k, v in re.findall(r"\|\s*start(\d+)\s*=\s*(.*)", seg)}
        ends = {int(k): date_in(v, page)
                for k, v in re.findall(r"\|\s*end(\d+)\s*=\s*(.*)", seg)}
        specials = {k: date_in(v, page) for k, v
                    in re.findall(r"\|\s*released(\d+S)\s*=\s*(.*)", seg)}
        return eps, starts, ends, specials

    nfy_ov, nfy_start, nfy_end, nfy_special = overview(nfy_eps_page, NFY_EPS)
    assert nfy_ov == {1: 8, 2: 8, 3: 8, 4: 7}, nfy_ov
    assert set(nfy_special) == {"3S"}, nfy_special
    reh_ov, reh_start, reh_end, reh_special = overview(reh, REHEARSAL)
    assert reh_ov == {1: 6, 2: 6}, reh_ov
    assert not reh_special, reh_special

    for blocks, ov, starts, ends, page in (
            (nfy_blocks, nfy_ov, nfy_start, nfy_end, NFY),
            (reh_blocks, reh_ov, reh_start, reh_end, REHEARSAL)):
        for head, eps in blocks:
            m = re.match(r"Season (\d+) \(", head)
            if not m:                                   # the 2017 special
                assert len(eps) == 1, (head, len(eps))
                assert eps[0][3] == nfy_special["3S"], (eps[0], nfy_special)
                continue
            n = int(m.group(1))
            assert len(eps) == ov[n], \
                ("%s %s: %d episode blocks against %d in the Series overview"
                 % (page, head, len(eps), ov[n]))
            assert [e[1] for e in eps] == list(range(1, len(eps) + 1)), \
                "%s %s: in-season numbering is not contiguous" % (page, head)
            assert eps[0][3] == starts[n] and eps[-1][3] == ends[n], \
                ("%s %s: the Series overview runs %s–%s, the episodes run %s–%s"
                 % (page, head, starts[n], ends[n], eps[0][3], eps[-1][3]))

    # totals against each series infobox, and the airdate spine
    all_nfy = [e for _h, eps in nfy_blocks for e in eps]
    all_reh = [e for _h, eps in reh_blocks for e in eps]
    for eps, want, page in ((all_nfy, 32, NFY), (all_reh, 12, REHEARSAL),
                            (curse_eps, 10, CURSE)):
        assert len(eps) == want, (page, len(eps), want)
        assert [e[0] for e in eps] == list(range(1, want + 1)), \
            "%s: overall numbering is not contiguous 1..%d" % (page, want)
        dates = [e[3] for e in eps]
        assert dates == sorted(dates), "%s: airdates go backwards" % page
        assert dates[-1] <= today, \
            ("%s carries an episode dated %s, which has not aired; this "
             "catalogue lists only what is out" % (page, dates[-1]))
    assert date_in(nfy_ib("first_aired"), NFY) == all_nfy[0][3], nfy_ib("first_aired")
    assert date_in(nfy_ib("last_aired"), NFY) == all_nfy[-1][3], nfy_ib("last_aired")
    assert date_in(reh_ib("first_aired"), REHEARSAL) == all_reh[0][3], \
        reh_ib("first_aired")
    assert reh_ib("last_aired").strip() == "present", reh_ib("last_aired")
    assert date_in(curse_ib("first_aired"), CURSE) == curse_eps[0][3], \
        curse_ib("first_aired")
    assert date_in(curse_ib("last_aired"), CURSE) == curse_eps[-1][3], \
        curse_ib("last_aired")

    # ---- the shows are in the order they started --------------------------
    firsts = [all_nfy[0][3], all_reh[0][3], curse_eps[0][3], film_out]
    assert firsts == sorted(firsts), \
        "the sections are no longer in premiere order: %s" % firsts

    # ---- WEIGHTS: the check that decides all-or-nothing, and decides none --
    reh_run, curse_run = reh_ib("runtime").strip(), curse_ib("runtime").strip()
    nfy_run = nfy_ib("runtime").strip()
    reh_range = _RANGE.fullmatch(reh_run)
    curse_range = _RANGE.fullmatch(curse_run)
    assert reh_range, \
        ("The Rehearsal's runtime is no longer a range (%r) — if it now "
         "publishes one figure per episode, re-check whether this list can "
         "carry hours" % reh_run)
    assert curse_range, \
        ("The Curse's runtime is no longer a range (%r) — see above" % curse_run)
    nfy_flat = _FLAT.fullmatch(nfy_run)
    assert nfy_flat, \
        "Nathan for You's runtime is no longer a flat figure: %r" % nfy_run
    # ...and the flat figure is not the truth about any given episode. The
    # article's own episode list says so, in the finale's summary.
    finale = re.search(r"\((\d{2,3})-minute series finale\)", nfy_eps_page)
    assert finale, \
        ("the Nathan for You episode list no longer describes a "
         "feature-length finale — re-check whether the flat %s applies to "
         "every episode after all" % nfy_run)
    finale_min = int(finale.group(1))
    assert finale_min != int(nfy_flat.group(1)), (finale_min, nfy_run)
    # and no episode anywhere publishes its own runtime
    for text, page in ((nfy_eps_page, NFY_EPS), (reh, REHEARSAL),
                       (curse, CURSE)):
        assert not re.search(r"\|\s*RunTime\s*=", text), \
            ("%s's episode blocks grew RunTime fields — this list can "
             "probably carry hours now" % page)

    # ---- who actually directed, counted rather than claimed ----------------
    def directed(text, n):
        d = re.findall(r"\|\s*DirectedBy\s*=\s*(.*)", text)
        assert len(d) == n, (len(d), n)
        return sum(1 for x in d if "Nathan Fielder" in wiki.clean(x))

    nfy_dir = directed(nfy_eps_page, 32)
    reh_dir = directed(reh, 12)
    curse_dir = directed(curse, 10)
    assert reh_dir == 12, reh_dir
    assert 0 < curse_dir < 10 and 0 < nfy_dir < 32, (curse_dir, nfy_dir)

    # ---- sections, in the order the shows arrived -------------------------
    def nfy_section():
        items = []
        for head, eps in nfy_blocks:
            m = re.match(r"Season (\d+) \(", head)
            for overall, inseason, title, _d in eps:
                if m:
                    n = "S%sE%d" % (m.group(1), inseason)
                    note = None
                else:
                    n = "Special"
                    note = ("A special between the third and fourth seasons — "
                            "Nathan checks in with businesses and people from "
                            "earlier episodes")
                if title == "Finding Frances":
                    note = ("The series finale, and feature-length — its own "
                            "episode list calls it %d minutes against the "
                            "show's usual %s" % (finale_min, nfy_flat.group(1)))
                it = {"id": "nf-nfy-e%02d" % overall, "t": title, "n": n}
                if note:
                    it["note"] = note
                items.append(it)
        return {
            "id": "nathanforyou", "title": NFY,
            "sub": "2013–2017 · four seasons and a special on Comedy Central · "
                   "%d episodes" % len(items),
            "intro": "Fielder has a business degree from a real university, "
                     "and on Comedy Central he spent four seasons offering it "
                     "to struggling businesses around Los Angeles — a frozen "
                     "yoghurt shop, a petting zoo, a gas station, a taxi "
                     "firm. The strategies are legal, exhaustively researched "
                     "and completely insane, and the people receiving them "
                     "are not actors and have not been told it is a comedy. "
                     "He created it with Michael Koman and is the credited "
                     "director on %d of the %d episodes. Start here: nothing "
                     "further down this list reads the same way without it."
                     % (nfy_dir, len(items)),
            "items": items,
            "open": True,
        }

    def rehearsal_section():
        items = [{"id": "nf-reh-e%02d" % overall, "t": title,
                  "n": "S%sE%d" % (re.match(r"Season (\d+) \(", head).group(1),
                                   inseason)}
                 for head, eps in reh_blocks
                 for overall, inseason, title, _d in eps]
        return {
            "id": "rehearsal", "title": "The Rehearsal",
            "sub": "2022–2025 · two seasons on HBO · %d episodes" % len(items),
            "intro": "The same man with an HBO budget. Fielder offers to walk "
                     "ordinary people through conversations they are dreading "
                     "by rehearsing them first — inside full-scale replicas "
                     "of the rooms the conversations will happen in, with "
                     "actors trained to play the other person, rehearsed "
                     "until the real thing is a formality. Two seasons: the "
                     "first on the people who agreed to this, the second on "
                     "communication between airline pilots. Wikipedia traces "
                     "the premise straight back to the rehearsals Fielder's "
                     "team ran while making Nathan for You, which is the best "
                     "argument for watching that first. He created it alone "
                     "and directed all %d episodes." % len(items),
            "items": items,
        }

    def curse_section():
        items = [{"id": "nf-curse-e%02d" % overall, "t": title,
                  "n": "E%d" % overall}
                 for overall, _in, title, _d in curse_eps]
        return {
            "id": "curse", "title": "The Curse",
            "sub": "2023–2024 · one season on Showtime · %d episodes"
                   % len(items),
            "intro": "His first scripted series, created and written with "
                     "Benny Safdie, who acts in it alongside Fielder and Emma "
                     "Stone. A married couple are shooting a home-renovation "
                     "show in Española, New Mexico, about the eco-friendly "
                     "houses they are building and the good they are doing "
                     "for the town. Nobody is improvising and nobody is being "
                     "pranked, and it is somehow the least comfortable thing "
                     "on this list. Fielder directed %d of the %d episodes; "
                     "David and Nathan Zellner took the rest."
                     % (curse_dir, len(items)),
            "items": items,
        }

    def film_section():
        fid = "nf-%d-%s" % (film_out.year, prop.slug(FILM))
        assert fid == "nf-2026-you-can-see-everything", fid
        return {
            "id": "film", "title": FILM,
            "sub": "%d · his first feature, a documentary from A24"
                   % film_out.year,
            "intro": "His first feature film, co-directed with Lance "
                     "Oppenheim and released in cinemas by A24. A "
                     "documentary: it follows Elizabeth Holmes, the founder "
                     "of the defunct health technology company Theranos, and "
                     "her partner Billy Evans, who invited a film crew to "
                     "document them in the weeks before Holmes began serving "
                     "a federal prison sentence for defrauding investors.",
            "items": [{"id": fid, "t": FILM, "n": str(film_out.year)}],
        }

    sections = [nfy_section(), rehearsal_section(), curse_section(),
                film_section()]
    assert [s["id"] for s in sections] == ["nathanforyou", "rehearsal",
                                           "curse", "film"], sections

    rows = [x for s in sections for x in s["items"]]
    assert len(rows) == len(all_nfy) + len(all_reh) + len(curse_eps) + 1 \
        == 55, len(rows)
    # All-or-nothing, and it is nothing. A single `w` here would make the total
    # confidently wrong, because 53 rows have no runtime to carry.
    assert not any("w" in x for x in rows), [x["id"] for x in rows if "w" in x]
    assert not any("opt" in x for x in rows), \
        "nothing here is optional; he created all of it"
    # spoiler discipline: only Nathan for You carries row notes, and only two
    assert not any("note" in x for s in sections[1:] for x in s["items"]), \
        "The Rehearsal and The Curse rows must stay bare — both shows turn " \
        "on things a row note would give away"
    assert sum(1 for x in sections[0]["items"] if "note" in x) == 2, \
        [x["id"] for x in sections[0]["items"] if "note" in x]

    # ---- the accent pair is nobody else's ---------------------------------
    accent, accent_dark = "#3F6B62", "#9EDCC9"
    for f in sorted((prop.ROOT / "properties").glob("*.json")):
        if f.stem == SLUG:
            continue
        try:
            other = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if not isinstance(other, dict):
            continue
        assert (other.get("accent") or "").lower() != accent.lower(), \
            "%s already uses accent %s" % (f.name, accent)
        assert (other.get("accentDark") or "").lower() != accent_dark.lower(), \
            "%s already uses accentDark %s" % (f.name, accent_dark)

    notes = [
        ["The rule for this list: he created it.",
         "Fielder writes, directs, produces and stars, often all four on the "
         "same show, so a list of him has to pick the credit that makes a "
         "thing his rather than one he worked on: creator for television, "
         "director for a feature film. Every row comes from a work his "
         "Wikipedia filmography marks him creator or co-creator of, or a "
         "feature it marks him director or co-director of, and that admits "
         "exactly four: Nathan for You, made with Michael Koman; The "
         "Rehearsal, his alone; The Curse, made with Benny Safdie; and the "
         "documentary You Can See Everything, co-directed with Lance "
         "Oppenheim. What "
         "it leaves out is real work, left out on purpose. How To with John "
         "Wilson he only executive produced — it is John Wilson's show. On "
         "Who Is America? he was a consulting producer and co-directed two "
         "episodes for Sacha Baron Cohen. He directed %s short films between "
         "%d and %d that Wikipedia gives no article, no runtime and no way to "
         "watch. And the acting — The Disaster Artist, The Simpsons, Rick and "
         "Morty, Bob's Burgers — is somebody else's show every time."
         % (WORDS[len(shorts)], short_years[0], short_years[-1])],
        ["The order is the argument.",
         "Chronological, one section per work, and Nathan for You first. The "
         "Rehearsal is the same man with a premium-cable budget doing the "
         "same thing long past the point where it is a bit — Wikipedia traces "
         "its premise directly back to the rehearsals his team ran while "
         "making the cable show — and it reads as an escalation only if you "
         "have seen what it escalates from. The Curse comes next because it "
         "is what happens when he stops filming real people and writes the "
         "whole thing instead, and You Can See Everything, his first feature, "
         "comes last because it came out last. In any other order the "
         "punchline turns up before its setup."],
        ["Hours are not tracked on this list.",
         "No row carries a runtime, and that is a decision rather than an "
         "unfinished job. The Rehearsal's infobox publishes %s and The "
         "Curse's %s — ranges for a series, not figures for an episode — and "
         "not one episode block on any of the three articles carries a "
         "runtime field at all. Nathan for You does state a flat %s, which "
         "looks usable and is not: the same article calls the finale a "
         "%d-minute one. Weighting the rows that could be weighted and "
         "leaving the rest bare would be worse than weighting nothing, "
         "because a row with no weight silently counts as a full hour and "
         "the total would come out confidently wrong. So this list counts "
         "entries, not time, and the home page's hour bar leaves it alone. "
         "The generator re-checks all three runtime fields every run, so the "
         "day real per-episode figures are published the build fails and "
         "somebody weights the list."
         % (reh_run, curse_run, nfy_run, finale_min)],
        ["Where the three shows stand.",
         "Nathan for You ran four seasons and a special, and Comedy Central "
         "confirmed in 2018 that it would not return for a fifth. The "
         "Rehearsal has two seasons; HBO has ordered no third, and as of "
         "September 2026 Fielder was still developing ideas for one. The Curse "
         "has one season, and while neither Fielder nor Safdie has ruled a "
         "second out, none has been ordered. The generator asserts all three "
         "counts against Wikipedia every time it runs, so a new season "
         "breaks the build rather than quietly going missing from this list."],
        ["Nothing here is spoiled.",
         "The Curse and The Rehearsal both turn on things that would be "
         "ruined by a one-line row note, so neither section has any. The "
         "section intros describe premises and nothing past them, and the "
         "only two row notes on the whole list are on Nathan for You: what "
         "its 2017 special is, and that its finale runs feature-length."],
        "Roster and credits from Wikipedia's Nathan Fielder article, filtered "
        "on its filmography's own Notes column; episode titles, numbering and "
        "airdates read from the episode tables on List of Nathan for You "
        "episodes, The Rehearsal and The Curse, and cross-checked against "
        "each series' infobox and its Series overview; the film's director "
        "credit and release date from its own article.",
    ]

    p = {
        "slug": SLUG,
        "title": "Nathan Fielder",
        "subtitle": "everything he created, in order",
        "kind": "tv & film",
        "popularity": 44,
        "year": "%d–%d" % (all_nfy[0][3].year, max(all_reh[-1][3],
                                                   curse_eps[-1][3],
                                                   film_out).year),
        "blurb": "Deadpan business advice on basic cable, life-size "
                 "rehearsals of conversations nobody wants to have, a "
                 "marriage inside a home-renovation show and a documentary "
                 "about Elizabeth Holmes — everything Nathan Fielder created, "
                 "in the order it came out.",
        # a film among the episodes, so the count is of entries (the same
        # kind and unit Breaking Bad and Deadwood use for their films)
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        # Light: the flat institutional green of a rehearsal-set wall built to
        # be photographed and thrown away. Dark: the mint glass of the passive
        # houses in The Curse. Checked above against every accent in
        # properties/.
        "accent": accent,
        "accentDark": accent_dark,
        "tiers": False,
        "notes": notes,
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d rows, no weights (nothing publishes a per-episode "
          "runtime)" % (out.name, len(rows)))
    for s in sections:
        print("   %-18s %2d  %s" % (s["title"][:18], len(s["items"]), s["sub"]))
    print("   seasons parsed vs source:")
    for head, eps in nfy_blocks:
        n = re.match(r"Season (\d+) \(", head)
        src = nfy_ov[int(n.group(1))] if n else 1
        print("      %-22s %2d parsed / %2d source" % (NFY + " " + head,
                                                       len(eps), src))
    for head, eps in reh_blocks:
        n = int(re.match(r"Season (\d+) \(", head).group(1))
        print("      %-22s %2d parsed / %2d source"
              % ("The Rehearsal " + head, len(eps), reh_ov[n]))
    print("      %-22s %2d parsed / %2s source"
          % ("The Curse (2023–24)", len(curse_eps),
             curse_ib("num_episodes").strip().split("<")[0]))
    print("   credit filter: creator (TV) or feature director (film) — %s"
          % ", ".join(got))
    print("   %s: released %s · directed by %s · %s"
          % (FILM, " / ".join(str(d) for d in film_dates), film_dirs,
             wiki.clean(film_ib("distributor"))))
    print("   runtimes: %s %r · The Rehearsal %r · The Curse %r · finale %d min"
          % (NFY, nfy_run, reh_run, curse_run, finale_min))
    print("   directed by Fielder: %d/32 · %d/12 · %d/10"
          % (nfy_dir, reh_dir, curse_dir))
    print("   excluded: %s"
          % "; ".join("%s (%s)" % v for v in EXCLUDED.values()))


if __name__ == "__main__":
    main()
