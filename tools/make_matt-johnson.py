#!/usr/bin/env python3
"""Generate properties/matt-johnson.json.

    PYTHONIOENCODING=utf-8 python tools/make_matt-johnson.py

Matt Johnson, the Canadian director: everything his own filmography marks him
as having directed. Five features, the eleven episodes of the web series he
and Jay McCarrol put online themselves, the sixteen of the Viceland series
that adapted it, and the three of the cartoon they made after.

Everything below is machine-read from Wikipedia wikitext cached in
scratch/matt-johnson/ — the "Matt Johnson (director)" article for the roster,
each film's own article for its release date and runtime, and the two series
articles for the shows. Nothing here is typed in from memory, and every number
this file prints is asserted against the source that produced it before
anything is written.

THE RULE FOR WHAT IS ON THE LIST: HE DIRECTED IT
------------------------------------------------
The list owner set the roster rule — anything he directs appears. So the only
creative test applied anywhere below is a bare {{Yes}} in a Director column,
and it is the same test in all three of the article's credit tables.

That admits five features — The Dirties (2013), Operation Avalanche (2016),
BlackBerry (2023), Nirvanna the Band the Show the Movie (2025) and Tony (2026)
— and all three shows. It excludes exactly one work on role grounds:
*Crash Land* (2026). Executive producing is not directing.

The article used to carry *Crash Land* as a Film row with Director {{No}} and
Producer {{partial|Executive}}, and this file checked those two cells by name.
As of the read of 11 September 2026 it is out of the director filmography
altogether, in a second table under a bold "Executive producer" line whose
only columns are Year, Title and Ref. So the exclusion is now checked from the
other side, which is stronger: the Film table is asserted to mark every row it
carries as directed and to contain no mention of *Crash Land* at all, and the
executive-producer table is asserted to be where *Crash Land* sits. A
non-directed row reappearing in the director table fails the build rather than
being admitted to the list.

The filmography table is checked against the article's own lead paragraph
rather than believed on its own. The brief that commissioned this list had
four films in it and missed *Tony*, which the lead names in its first
sentence; a filmography table that lags its own lead is exactly the failure
that produces a list one film short. So main() extracts every italicised
wikilink from the lead and asserts each one is either a shipped row or a title
this file excludes on purpose, by name, with a reason. A new work reaching the
lead breaks the build instead of going quietly missing.

UNRELEASED WORK IS NOT LISTED, AND UNCLE STAV LETS ITSELF IN
------------------------------------------------------------
Release dates are read from each film's own {{Infobox film}} `released` field,
asserted against the filmography table's Year column, and asserted to be on or
before the day this runs. *Tony* released on 7 August 2026 and is on the list.

*Uncle Stav* — Stavros Halkias' stand-up special, Director {{Yes}} — is the
one work kept off for timing alone. The article says it premieres on Netflix
on 8 September 2026, main() parses that date out of the prose, and the section
is built only when the date has passed. **It admits itself.** Nobody has to
remember on the day: run the generator on or after 8 September and the row and
its section appear, the roster count moves from 35 to 36, and the note that
explains its absence is replaced by the row itself. The premise that it has
not aired is asserted either way, so the build cannot disagree with its own
notes about which state it is in.

WEIGHTS: NONE, DELIBERATELY, AND THIS IS THE THING TO FIX
---------------------------------------------------------
Not one row carries `w`, and main() asserts that rather than leaving it to
care. The page resolves `WEIGHT = x.w >= 0 ? x.w : 1`, so a row without a
weight on an otherwise weighted list silently books itself as one hour. Half a
list weighted is worse than none of it, because the total then looks
authoritative and is wrong.

Twenty-one of the thirty-five rows could be weighted today:

  * the five features, from each film's own {{Infobox film}} `runtime` — 83
    minutes for The Dirties up to 121 for BlackBerry, all five read and
    asserted below even though nothing is emitted from them, so the figures
    are already verified for whoever adds the weights;
  * the sixteen Viceland episodes, at the flat 22 minutes the series infobox
    states.

The other fourteen cannot, and that is what keeps hours off the whole list:

  * *Nirvana the Band the Show* (2007–2009, 11 episodes) — its television
    infobox documents "10–20 minutes", a range for the series, and not one of
    its eleven {{Episode list}} blocks carries a runtime field. Its Wikidata
    item (Q133503895) has no P2047 either. Picking a number inside that range
    would be an estimate wearing a citation.
  * *Matt & Bird Break Loose* (2021, 3 episodes) — no Wikipedia article at
    all, absent from both Amazon Prime Video programming lists, and no runtime
    published anywhere the encyclopedia can be asked. Wikipedia does not even
    document the three episodes' titles, which is why they are numbered.

Both reasons are asserted, not just described: main() checks that the web
series' runtime is *still* a range and that *Matt & Bird* *still* has no
article. If either ever gains a real per-episode figure this build fails, and
whoever is standing there weights the list instead of the exclusion quietly
outliving the reason for it. The card says the same thing in the notes, so a
reader knows the hours are missing rather than assuming this list has none.

TWO SHOWS, NOT ONE SHOW TWICE
-----------------------------
*Nirvana the Band the Show* (2007–2009) and *Nirvanna the Band the Show*
(2017–2018) are separate works, and the list owner ruled that they must never
be presented as two runs of one programme. They get two sections, far apart in
the chronology, and the source backs the separation: two tables on the
filmography (===Web=== against ===Television===), two Wikipedia articles, two
Wikidata items, two episode counts.

One correction to the brief that commissioned this list, which reasoned from
the differing spelling: the source does *not* treat *Nirvana* against
*Nirvanna* as evidence of two unrelated works. The series article says in
plain terms that the television show "is adapted from the web series", that it
was "created as a web series between 2007 and 2009 ... later expanded into a
full television series", and that "the spelling was changed from ''Nirvana''
to ''Nirvanna'' at the recommendation of a lawyer". So the honest description
— and the one the notes give — is that the 2017 series is a television
*adaptation* of the web series: the same two men and the same premise, remade
for a network. That is still not a continuation, a revival or a second run,
which is what the ruling actually forbids, and nothing in the output says
otherwise.

SHAPE
-----
Five sections in chronology, and films and episodes never share one: the web
series, the two found-footage features, the Viceland show, the cartoon, the
three features since BlackBerry. The film sections take their boundary from
the article's own career headings, "2007–2021: Early work" and "2022–present:
Career expansion", which main() reads out of the wikitext rather than choosing.

*Nirvanna the Band the Show the Movie* (2025) sits with the films, because it
is a theatrical feature and the filmography files it in the Film table. Its
row says it continues the show, because it is the one entry here that does not
work cold.

THE BLURB CARRIES NO ITEM COUNT AND NO HOURS. Five cards in this catalogue
already contradict their own generated count, and this list does not track
hours at all.
"""
import datetime
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki  # noqa: E402

SLUG = "matt-johnson"
CACHE = prop.ROOT / "scratch" / SLUG
ARTICLE = "Matt Johnson (director)"
SHOW = "Nirvanna the Band the Show"
WEB = "Nirvana the Band the Show"
CARTOON = "Matt & Bird Break Loose"
SPECIAL = "Uncle Stav"

# The two career headings the article divides itself with. The film sections
# take their boundary from these rather than from a year picked by hand.
ERA_HEADINGS = ("2007–2021: Early work", "2022–present: Career expansion")
ERA_SPLIT = 2022                      # first year of the second heading

# Titles this list deliberately does not ship, each with the reason. The lead
# cross-check refuses to pass a title that is neither a row nor in here, so a
# new work cannot go quietly missing. Uncle Stav is added at runtime, and only
# while it is still unreleased.
EXCLUDED = {"Crash Land": "executive produced, not directed"}

# Per-film row notes. Nothing factual lives in these — every year and title on
# the card is read from the wikitext — they are the editorial line.
NOTES = {
    "The Dirties": "His directorial debut: two high-school students shoot a "
                   "film about taking revenge on their bullies, and one of "
                   "them stops pretending",
    "Operation Avalanche": "Two CIA agents infiltrate NASA hunting a KGB "
                           "mole, and end up inside a plan to fake the "
                           "Apollo 11 landing",
    "BlackBerry": "The dramatised rise and spectacular fall of the Canadian "
                  "phone — he plays co-founder Doug Fregin, opposite Jay "
                  "Baruchel and Glenn Howerton",
    "Nirvanna the Band the Show the Movie": "Continues the show and does not "
                                            "work cold — watch the sixteen "
                                            "episodes first",
    "Tony": "Anthony Bourdain's first years cooking in Provincetown, out of "
            "Kitchen Confidential — his first American film, with Dominic "
            "Sessa as Bourdain",
}

FILM_SECTIONS = [
    ("early", "The found-footage features",
     "Two cheap films shot as though a documentary crew were really in the "
     "room and losing control of it. He wrote, directed and starred in both. "
     "Zapruder Films, the company he set up with Matthew Miller after the "
     "first, made the second."),
    ("expansion", "After BlackBerry",
     "The phone picture turned him into a director other people fund. What he "
     "did with that was finally make the Nirvanna film he and Jay McCarrol "
     "had been workshopping since 2009, and then a Bourdain biopic in the "
     "United States."),
]

_CELL = re.compile(r"^\|\s*(?:([^|\[{]*=[^|\[{]*)\|)?\s*(.*)$", re.S)


def table_after(text, heading):
    """The first wikitable following a `===heading===` line."""
    m = re.search(r"^=+\s*%s\s*=+\s*$" % re.escape(heading), text, re.M)
    assert m, "no %r section on the article" % heading
    a = text.index('{| class="wikitable"', m.end())
    return text[a:text.index("\n|}", a)]


def table_after_bold(text, label):
    """The first wikitable following a bold `'''label'''` line. The article
    files its executive-producer credits under one of those rather than under a
    heading, so table_after() cannot reach them."""
    m = re.search(r"^'''%s'''\s*$" % re.escape(label), text, re.M)
    assert m, "no bold %r line on the article" % label
    a = text.index('{| class="wikitable"', m.end())
    return text[a:text.index("\n|}", a)]


def table_rows(seg, ncols):
    """Cells per row, with rowspan carried down. The Film table's 2026 row
    used to rowspan its Year cell over two films — Tony and Crash Land — and
    positional picking without this handed Tony the wrong year, or no year at
    all. Crash Land has since moved to its own table and the cell now reads
    rowspan="1", which is the kind of change that must not be allowed to
    quietly start mattering again: the carry stays."""
    out, pending = [], {}
    for chunk in seg.split("\n|-")[1:]:
        raw = iter(l for l in chunk.split("\n") if l.strip().startswith("|"))
        cols = []
        for c in range(ncols):
            if c in pending:
                cols.append(pending[c][1])
                pending[c][0] -= 1
                if pending[c][0] == 0:
                    del pending[c]
                continue
            m = _CELL.match(next(raw, "|").strip())
            attrs, content = m.group(1) or "", m.group(2)
            cols.append(content)
            sp = re.search(r'rowspan="?(\d+)', attrs)
            if sp and int(sp.group(1)) > 1:
                pending[c] = [int(sp.group(1)) - 1, content]
        out.append(cols)
    return out


def yes(cell):
    """True only for a bare {{Yes}} — {{partial|Executive}} is not a credit."""
    return bool(re.fullmatch(r"\{\{\s*[Yy]es\s*\}\}", cell.strip()))


def no(cell):
    return bool(re.fullmatch(r"\{\{\s*[Nn]o\s*\}\}", cell.strip()))


def link(cell):
    """The wikilink target inside an italicised title cell."""
    m = re.search(r"\[\[([^\]|]+)", cell)
    return m.group(1).strip() if m else None


def minutes(field, what):
    """A single whole-minute runtime out of an infobox field. A range — which
    is what the web series carries — fails, which is the whole point."""
    v = wiki.clean(field or "")
    m = re.fullmatch(r"(\d{1,3})\s*minutes?", v.strip())
    assert m, "%s does not publish a single runtime: %r" % (what, v)
    n = int(m.group(1))
    assert 5 <= n <= 240, "%s: implausible runtime %d" % (what, n)
    return n


def film_dates(field, what):
    """Every release date on an infobox `released` field, in order."""
    got = []
    for m in re.finditer(r"\{\{\s*[Ff]ilm date\s*\|\s*(\d{4})\s*\|\s*(\d{1,2})"
                         r"\s*\|\s*(\d{1,2})", field or ""):
        got.append(datetime.date(*(int(g) for g in m.groups())))
    for m in re.finditer(r"\|\s*(\d{4})\s*\|\s*(\d{1,2})\s*\|\s*(\d{1,2})\s*\|",
                         field or ""):
        try:
            got.append(datetime.date(*(int(g) for g in m.groups())))
        except ValueError:
            pass
    assert got, "%s: no release date on the infobox" % what
    return sorted(set(got))


def main():
    today = datetime.date.today()
    art = wiki.wikitext(ARTICLE, cache_dir=CACHE)
    assert art, "no cached wikitext for %r" % ARTICLE
    lead = art[:art.index("\n==")]

    # ---- the article divides its own career; borrow the boundary ----------
    for h in ERA_HEADINGS:
        assert re.search(r"^=+\s*%s\s*=+\s*$" % re.escape(h), art, re.M), \
            ("the career heading %r is gone — the film sections take their "
             "boundary from it and must be re-derived" % h)

    # ---- films -----------------------------------------------------------
    frows = table_rows(table_after(art, "Film"), 7)
    assert len(frows) >= 5, len(frows)
    films, not_directed = [], []
    for year, title, d, w, p, note, _ref in frows:
        rec = {"t": wiki.clean(title), "page": link(title),
               "year": int(wiki.clean(year)), "wrote": yes(w)}
        (films if yes(d) else not_directed).append(rec)
    # The one work kept out on role grounds. Checked from both sides, because
    # the article has moved it: it is no longer a Film row with Director {{No}}
    # for the old by-name cell checks to read, but a row in a separate
    # bold-labelled executive-producer table. So the Film table must mark
    # everything it carries as directed and must not mention Crash Land at all,
    # and Crash Land must be where the source now files it.
    assert not not_directed, \
        ("the Film table carries rows it does not mark directed: %s — this "
         "list ships Director={{Yes}} and nothing else, so a row like that "
         "needs a decision rather than a default"
         % [x["t"] for x in not_directed])
    assert "Crash Land" not in table_after(art, "Film"), \
        ("Crash Land is back in the director filmography — re-read its credits "
         "before this list ships it")
    ep_titles = [wiki.clean(r[1]) for r in
                 table_rows(table_after_bold(art, "Executive producer"), 3)]
    assert "Crash Land" in ep_titles, \
        ("Crash Land is no longer filed under Executive producer (%s), and the "
         "notes tell readers that is why it is missing" % ep_titles)
    assert len(films) == 5, [x["t"] for x in films]
    assert [x["year"] for x in films] == sorted(x["year"] for x in films), \
        "the filmography table is out of release order"
    assert all(x["wrote"] for x in films), \
        "he is credited as writer on every feature he directed; that changed"

    for f in films:
        page = wiki.wikitext(f["page"], cache_dir=CACHE)
        assert page, "no cached article for %s" % f["page"]
        ib = wiki.infobox(page, kind="film")
        assert ib, "no film infobox on %s" % f["page"]
        # Read and asserted although nothing is emitted from it: these are the
        # five figures already verified for whoever weights this list, and the
        # notes quote the shortest and the longest.
        f["runtime"] = minutes(ib("runtime"), f["t"])
        dates = film_dates(ib("released"), f["t"])
        f["released"] = dates[0]
        # the table's Year against the film's own article, not the other way
        assert f["released"].year == f["year"], \
            "%s: filmography says %d, its article's first release is %s" \
            % (f["t"], f["year"], f["released"])
        assert f["released"] <= today, \
            "%s is dated %s and has not come out; it does not belong yet" \
            % (f["t"], f["released"])

    # Tony is the row the commissioning brief did not have. Pinned by name so
    # that if it ever falls out of the table this build fails loudly.
    tony = next(f for f in films if f["t"] == "Tony")
    assert tony["year"] == 2026 and tony["released"] <= today, tony

    # ---- television and web: two tables, and they stay two ----------------
    trows = table_rows(table_after(art, "Television"), 8)
    wrows = table_rows(table_after(art, "Web"), 8)
    tv = {wiki.clean(r[1]): r for r in trows}
    web = {wiki.clean(r[1]): r for r in wrows}
    assert set(tv) == {SHOW, CARTOON, SPECIAL}, sorted(tv)
    assert set(web) == {WEB}, sorted(web)
    # the ruling, checked against the source: different tables, different names
    assert SHOW != WEB and SHOW not in web and WEB not in tv, (SHOW, WEB)
    # The notes tell readers the titles differ by one n, and that the change
    # was a lawyer's. If either stops being true that sentence must change.
    assert SHOW.count("n") == WEB.count("n") + 1, (SHOW, WEB)
    for t in (SHOW, WEB, CARTOON, SPECIAL):
        assert yes(tv.get(t, web.get(t))[3]), \
            "%s is no longer marked directed — the roster rule is Director=Yes" % t

    # ---- the web series ---------------------------------------------------
    wpage = wiki.wikitext(WEB, cache_dir=CACHE)
    wib = wiki.infobox(wpage, kind="television")
    assert wib, "no infobox on the web series article"
    assert wib("num_episodes").strip() == "11", wib("num_episodes")
    assert wiki.clean(web[WEB][6]).startswith(
        "Directed and co-wrote all 11 episodes"), web[WEB][6]
    weps = wiki.episodes(wpage)
    assert len(weps) == 11, len(weps)
    assert [e[0] for e in weps] == list(range(1, 12)), [e[0] for e in weps]
    assert all(e[2] for e in weps), "a web episode has no title"
    # ten in the run, plus the 2010 bonus the article files separately — which
    # is how the infobox reaches eleven while its last-aired date says 2009
    assert re.search(r"^=+\s*Series \(2007–09\)\s*=+\s*$", wpage, re.M), \
        "the web article no longer files its run under Series (2007–09)"
    assert re.search(r"^=+\s*Bonus Episode \(2010\)\s*=+\s*$", wpage, re.M), \
        "the web article no longer files a 2010 bonus episode"
    assert [e[3] for e in weps[:10]] == sorted(e[3] for e in weps[:10]), weps
    assert weps[10][3] == 2010 and weps[9][3] == 2009, (weps[9], weps[10])
    wdirs = re.findall(r"\|\s*DirectedBy\s*=\s*(.*)", wpage)
    assert len(wdirs) == 11 and all("Matt Johnson" in wiki.clean(d)
                                    for d in wdirs), wdirs
    # THE REASON THE WHOLE LIST IS UNWEIGHTED, part one. Still a range, still
    # nothing per episode. If that changes, this build fails and someone
    # weights the list instead of the omission outliving its reason.
    web_runtime = wib("runtime").strip()
    assert re.fullmatch(r"\d+–\d+ minutes", web_runtime), \
        ("the web series runtime is no longer a range (%r) — if it now "
         "publishes one figure per episode, this list can carry hours"
         % web_runtime)
    assert not re.search(r"\|\s*RunTime\s*=", wpage), \
        "the web series episode list grew runtime fields — weight this list"

    # ---- the Viceland series ----------------------------------------------
    spage = wiki.wikitext(SHOW, cache_dir=CACHE)
    sib = wiki.infobox(spage, kind="television")
    assert sib, "no infobox on the series article"
    ep_min = minutes(sib("runtime"), SHOW)     # a real figure; see the notes
    assert sib("num_episodes").strip() == "16", sib("num_episodes")
    assert sib("num_seasons").strip() == "2", sib("num_seasons")
    assert "Viceland" in sib("network"), sib("network")
    assert wiki.clean(tv[SHOW][6]) == "Directed and co-wrote all 16 episodes", \
        tv[SHOW][6]
    assert re.search(r"spelling was changed from ''Nirvana'' to ''Nirvanna''",
                     spage), \
        "the lawyer's spelling change is no longer stated; the note says it is"

    seps = wiki.episodes(spage)
    assert len(seps) == 16, len(seps)
    assert [e[0] for e in seps] == list(range(1, 17)), [e[0] for e in seps]
    heads = re.findall(r"^=+\s*Season (\d) \((\d{4})(?:–\d{2,4})?\)\s*=+\s*$",
                       spage, re.M)
    assert [h[0] for h in heads] == ["1", "2"], heads
    ov = dict(re.findall(r"\|\s*episodes(\d)\s*=\s*(\d+)", spage))
    assert ov == {"1": "8", "2": "8"}, ov
    seasons, n = [], 0
    for num, count in (("1", 8), ("2", 8)):
        block = seps[n:n + count]
        assert [e[1] for e in block] == list(range(1, count + 1)), block
        seasons.append((int(num), block))
        n += count
    assert n == len(seps)
    sdirs = re.findall(r"\|\s*DirectedBy\s*=\s*(.*)", spage)
    assert len(sdirs) == 16 and all("Matt Johnson" in wiki.clean(d)
                                    for d in sdirs), sdirs
    aired = [e[3] for e in seps]
    assert min(aired) == 2017 and max(aired) == 2018, (min(aired), max(aired))
    assert "third season" in art and "not released" in art, \
        "the unreleased third season is no longer described in the article"

    # ---- the works people ask for that the record does not have -----------
    # Eight titles are named around this list by viewers who have seen them.
    # Seven leave no machine-readable trace at all — not in the filmography,
    # not in a full-text insource: search of every article, not on his Wikidata
    # item — and a row with an invented year would be worse than no row. The
    # 64X pair is the single exception, and what the source actually says about
    # it is "appeared in", which is the ground the Alvvays video is excluded
    # on. The notes tell readers exactly that, so the sentence they describe is
    # asserted here: if it ever credits him as director, this build fails and
    # whoever is standing there ships two rows instead of the note outliving
    # its own reason.
    assert re.search(r"^=+\s*Online video collaborations\s*=+\s*$", spage, re.M), \
        ("the Viceland article no longer has an Online video collaborations "
         "section — it is the only source for the 64X shorts the notes name")
    assert re.search(r"In September 2023, and again in September 2024, Matt "
                     r"and Jay appeared in special shorts for 64X", spage), \
        ("the 64X sentence has changed — re-read it; a director credit there "
         "makes those two shorts rows and the notes wrong")
    assert re.search(r"collaborated with YouTuber \[\[Joel Haver\]\]", spage), \
        ("the Joel Haver sentence has changed — the notes say that short is "
         "his rather than Johnson's")
    for absent in ("Honolulu Blue", "My Mother's Pearls", "Fantastic Corpse",
                   "Live at Comic-Con", "64expo"):
        assert absent not in art and absent not in spage and absent not in wpage, \
            ("%r is now documented in the source the notes say is silent about "
             "it — read the credit and ship the row if he directed it" % absent)

    # ---- the cartoon ------------------------------------------------------
    cart = tv[CARTOON]
    assert wiki.clean(cart[6]) == "Co-directed and co-wrote all 3 episodes", \
        cart[6]
    assert wiki.clean(cart[0]) == "2021", cart[0]
    assert "Amazon Kids+" in art and "spiritual successor" in art, \
        "the cartoon's platform or lineage is no longer described"
    # THE REASON THE WHOLE LIST IS UNWEIGHTED, part two — and the reason its
    # three rows are numbered rather than titled. No article means no runtime
    # and no episode titles.
    assert link(cart[1]) is None, \
        ("%s now has a Wikipedia article — check it for a runtime and for "
         "episode titles; this list can probably carry hours" % CARTOON)
    n_cartoon = int(re.search(r"all (\d+) episodes", wiki.clean(cart[6])).group(1))
    assert n_cartoon == 3, n_cartoon

    # ---- Uncle Stav: it admits itself the day it airs ---------------------
    stav = tv[SPECIAL]
    assert "comedy special" in wiki.clean(stav[6]), stav[6]
    prem = re.search(r"''Uncle Stav''.{0,400}?premiere on \[\[Netflix\]\] on "
                     r"(\w+) (\d{1,2})", art, re.S)
    assert prem, "the Uncle Stav premiere date is no longer stated in prose"
    stav_date = datetime.datetime.strptime(
        "%s %s %s" % (prem.group(1), prem.group(2), wiki.clean(stav[0])),
        "%B %d %Y").date()
    stav_out = stav_date > today
    if stav_out:
        EXCLUDED[SPECIAL] = "not released until %s" % stav_date

    # ---- the lead cross-check: nothing the lead names may go missing ------
    named = {link(m.group(0)) for m in re.finditer(r"''\[\[[^\]]+\]\]''", lead)}
    named = {n for n in named if n}
    shipped = {f["page"] for f in films} | {SHOW, WEB, CARTOON}
    if not stav_out:
        shipped.add(SPECIAL)
    unaccounted = named - shipped - set(EXCLUDED)
    assert not unaccounted, \
        ("the lead names %s and this list neither ships nor excludes it — the "
         "filmography table lagged the lead once already (Tony)"
         % sorted(unaccounted))
    for f in films:
        assert f["page"] in named, \
            "%s is in the filmography but not the lead — check it is his" % f["t"]

    # ---- sections, in chronology ------------------------------------------
    def web_section():
        items = []
        for overall, _inseason, title, year, _b in weps:
            it = {"id": "mj-ntbs-e%02d" % overall, "t": title,
                  "n": "Bonus" if year == 2010 else "E%d" % overall}
            if year == 2010:
                it["note"] = ("Bonus episode, posted in 2010 after the run "
                              "ended — Matt goes to Cuba")
            items.append(it)
        return {
            "id": "web", "title": WEB,
            "sub": "2007–2010 · %d episodes online · one n" % len(items),
            "intro": "Where all of it starts. He and Jay McCarrol filmed "
                     "themselves in Toronto as a band trying to get booked at "
                     "the Rivoli, put it online themselves, and directed and "
                     "co-wrote all %d episodes. Ten in the run to 2009, plus "
                     "one bonus in 2010. This is the web series with one n — "
                     "the Viceland show further down is the adaptation of it, "
                     "made a decade later, and a separate work."
                     % len(items),
            "items": items,
            "open": True,
        }

    def film_section(key, title, intro):
        got = [f for f in films
               if (f["year"] < ERA_SPLIT) == (key == "early")]
        assert got, key
        return {
            "id": key, "title": title,
            "sub": "%d–%d · %d features" % (got[0]["year"], got[-1]["year"],
                                            len(got)),
            "intro": intro,
            "items": [{"id": "mj-%d-%s" % (f["year"], prop.slug(f["t"])),
                       "t": f["t"], "n": str(f["year"]),
                       "note": NOTES[f["t"]]} for f in got],
        }

    def show_section():
        items = [{"id": "mj-ntbts-s%de%02d" % (snum, inseason),
                  "t": t, "n": "S%dE%d" % (snum, inseason)}
                 for snum, block in seasons
                 for _o, inseason, t, _y, _b in block]
        return {
            "id": "nirvanna", "title": SHOW,
            "sub": "2017–2018 · %d episodes on Viceland · two n's" % len(items),
            "intro": "Two Toronto men spend two seasons on elaborate plans to "
                     "get their band booked at the Rivoli, a band that has "
                     "never written a song. Scripted scenes, improvisation "
                     "and candid footage of bystanders who never agreed to be "
                     "in it. He created it with Jay McCarrol and directed and "
                     "co-wrote all %d episodes. A third season was partly "
                     "produced and remains unaired. This is the television "
                     "adaptation of the web series at the top of the list, "
                     "not a later run of it — the spelling gained an n on a "
                     "lawyer's advice." % len(items),
            "items": items,
        }

    def cartoon_section():
        return {
            "id": "mattbird", "title": CARTOON,
            "sub": "2021 · %d episodes on Amazon Kids+" % n_cartoon,
            "intro": "An animated children's show he and Jay McCarrol "
                     "co-created and starred in, described by his own article "
                     "as a spiritual successor to Nirvanna the Band the Show. "
                     "He co-directed and co-wrote all %d episodes. Wikipedia "
                     "has no article on it and does not publish the episode "
                     "titles, so the rows are numbered rather than named."
                     % n_cartoon,
            "items": [{"id": "mj-mbbl-e%d" % i, "t": "Episode %d" % i,
                       "n": "E%d" % i} for i in range(1, n_cartoon + 1)],
        }

    def stav_section():
        return {
            "id": "unclestav", "title": SPECIAL,
            "sub": "%d · one stand-up special on Netflix" % stav_date.year,
            "intro": "Stavros Halkias' stand-up special, filmed over four "
                     "shows in Baltimore. Johnson directed it and did not "
                     "write or create it, which is no bar: anything he "
                     "directs is on this list. Halkias is also in Tony.",
            "items": [{"id": "mj-%d-uncle-stav" % stav_date.year, "t": SPECIAL,
                       "n": str(stav_date.year),
                       "note": "Stand-up special — he directed it for "
                               "Stavros Halkias, who acts in Tony"}],
        }

    sections = [web_section(),
                film_section(*FILM_SECTIONS[0]),
                show_section(),
                cartoon_section(),
                film_section(*FILM_SECTIONS[1])]
    if not stav_out:
        sections.append(stav_section())

    order = [s["id"] for s in sections]
    assert order[:5] == ["web", "early", "nirvanna", "mattbird",
                         "expansion"], order
    for s in sections:
        if s["id"] not in ("early", "expansion"):
            continue
        ys = [x["n"] for x in s["items"]]
        assert ys == sorted(ys), "%s is out of year order" % s["title"]

    # ---- the weighting: none, and nothing may sneak one in ----------------
    rows = [x for s in sections for x in s["items"]]
    want = len(films) + len(weps) + len(seps) + n_cartoon + (0 if stav_out else 1)
    assert want == (35 if stav_out else 36), want
    assert len(rows) == want, (len(rows), want)
    # A row with `w` on a list where fourteen rows cannot have one would make
    # the total confidently wrong. Either all of them or none, and it is none.
    assert not any("w" in x for x in rows), \
        [x["id"] for x in rows if "w" in x]
    assert not any("opt" in x for x in rows), \
        "nothing here is optional; he directed all of it"

    weightable = len(films) + len(seps)
    unweightable = len(weps) + n_cartoon

    # ---- the accent pair is nobody else's ---------------------------------
    accent, accent_dark = "#5C4B8C", "#B9A6F0"
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
        ["Everything he has directed.",
         "The rule for this list is simple: if his filmography marks him "
         "director, it is here — features, television, the web series and the "
         "cartoon alike, whether or not he created or wrote them. The one "
         "thing kept out on those grounds is Crash Land (2026), which his "
         "filmography files under executive producer rather than in the "
         "director table. Executive producing is not directing. His acting "
         "roles in other people's films and the Alvvays video are not here "
         "either, and neither is the third season of the Viceland show, which "
         "was partly produced and never aired."],
        ["Eight more works get asked for, and they are not here.",
         "Honolulu Blue, a second and earlier Operation Avalanche, a Live @ "
         "the Rivoli recording, My Mother's Pearls, Fantastic Corpse and a "
         "Matt Johnson Live at Comic-Con are named by people who have seen "
         "them, and no encyclopedia documents any of them — not the "
         "filmography, not a full-text search of every article, not his "
         "Wikidata item. The Mega64 specials are the one exception and they "
         "are one thing rather than two: the Viceland show's article records "
         "that he and Jay McCarrol appeared in shorts for 64X, Mega64's "
         "online event, in September 2023 and again in September 2024. It "
         "credits them as appearing, gives the shorts no title of their own "
         "and no runtime, so they fail the same test the Alvvays video fails. "
         "The same article records a 2026 short in which the two reprise "
         "their roles, which is Joel Haver's film and not his. Every one of "
         "them is left off rather than given a year this list cannot stand "
         "behind."],
        ["Hours are not tracked on this list.",
         "No row carries a runtime, and that is deliberate rather than "
         "unfinished. Fourteen of the %d rows have no published per-episode "
         "runtime anywhere: the web series' infobox gives a range for the "
         "whole series, 10 to 20 minutes, and nothing per episode, and Matt & "
         "Bird Break Loose has no Wikipedia article at all — no runtime, not "
         "even episode titles. Weighting only the rows that can be weighted "
         "would be worse than weighting none, because an unweighted row "
         "silently counts as a full hour and the total would come out "
         "confidently wrong. So the list counts entries, not time. The "
         "figures that do exist are ready for the day the rest turn up: all "
         "five features publish runtimes, %d minutes for %s up to %d for %s, "
         "and the Viceland episodes run a flat %d."
         % (len(rows), min(f["runtime"] for f in films),
            min(films, key=lambda f: f["runtime"])["t"],
            max(f["runtime"] for f in films),
            max(films, key=lambda f: f["runtime"])["t"], ep_min)],
        ["Two shows, not one show twice.",
         "Nirvana the Band the Show, one n, is the independent web series he "
         "and Jay McCarrol produced and put online themselves — eleven "
         "episodes, and the top section here. Nirvanna the Band the Show, two "
         "n's, is the sixteen-episode Viceland series a decade later. The "
         "second is a television adaptation of the first: same two men, same "
         "Rivoli, remade for a network, with the spelling changed on a "
         "lawyer's advice. It is not a later run of the web series, not a "
         "revival and not a second season of it. They sit apart on this list "
         "because they are separate works, and each is watchable without the "
         "other."],
        ["The movie does not work cold.",
         "Nirvanna the Band the Show the Movie is a feature and sits with the "
         "features, which is where his filmography files it. It is also a "
         "direct continuation of the Viceland show, with the same two men and "
         "the same joke running underneath it, so those sixteen episodes come "
         "first."],
    ]
    if stav_out:
        notes.append(
            ["Uncle Stav is not out yet.",
             "He directed Stavros Halkias' stand-up special, and directing it "
             "is enough to earn it a place here. It is missing only because "
             "it has not been released: it premieres on Netflix on %d %s "
             "%d, and this catalogue does not list work nobody can watch "
             "yet. The generator adds it by itself on the day."
             % (stav_date.day, stav_date.strftime("%B"), stav_date.year)])
    notes.append(
        "Filmography, credits and episode lists from Wikipedia's Matt Johnson "
        "(director), Nirvana the Band the Show and Nirvanna the Band the Show "
        "articles, read from the tables themselves; release dates from each "
        "film's own article.")

    p = {
        "slug": SLUG,
        "title": "Matt Johnson",
        "subtitle": "everything he has directed",
        "kind": "films & tv",
        "popularity": 34,
        "year": "%d–%d" % (weps[0][3], films[-1]["year"]),
        "blurb": "Docufiction pranks, the phone that ate the world and a "
                 "young Anthony Bourdain — the features he directed, and "
                 "every episode of the shows he made around them.",
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        # Light: the bruised purple the show's title cards live in. Dark: the
        # washed-out lilac of a camcorder tape played once too often. Checked
        # above against every accent shipping in properties/.
        "accent": accent,
        "accentDark": accent_dark,
        "tiers": False,
        "notes": notes,
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d rows, no weights (%d weightable today, %d not)"
          % (out.name, len(rows), weightable, unweightable))
    for s in sections:
        print("   %-30s %2d  %s" % (s["title"][:30], len(s["items"]), s["sub"]))
    print("   films publish runtimes: %s"
          % ", ".join("%s %d" % (f["t"], f["runtime"]) for f in films))
    print("   %s: %d min flat · %s: %s (range) · %s: no article"
          % (SHOW, ep_min, WEB, web_runtime, CARTOON))
    print("   excluded: Crash Land (executive produced, not directed)%s"
          % ("; %s (premieres %s — it joins by itself on the day)"
             % (SPECIAL, stav_date) if stav_out else ""))


if __name__ == "__main__":
    main()
