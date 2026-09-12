#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate properties/villeneuve.json.

    PYTHONIOENCODING=utf-8 python tools/make_villeneuve.py

Every feature Denis Villeneuve has directed, in release order — the rows of
the Film table in Wikipedia's "Denis Villeneuve" article whose Director cell is
a bare {{yes}} and whose film the source dates. There is no separate "Denis
Villeneuve filmography" article; the roster lives in the ==Filmography==
section of the biography, and that is what is read here.

Everything below is machine-read from wikitext cached in scratch/villeneuve/
by scratch/villeneuve/fetch.py — the biography for the roster and the career
divisions, and each film's own article for its runtime, release dates, source
material and screenwriter. Nothing is typed in from memory, and every number
this file prints is asserted against the source that produced it before
anything is written.

THE ROSTER RULE: HE DIRECTED IT, AND THE SOURCE DATES IT
-------------------------------------------------------
Only a bare {{yes}} in the Director column puts a film here. The Writer and
Producer columns gate nothing: he wrote all four Quebec films and none of the
four that followed, and the Producer column is {{no}} on everything before
Dune. All three facts are asserted below and all three are section-intro copy,
not roster criteria.

Coming out is NOT a roster criterion, as of the owner's ruling on CLU-315:
announced work the source dates — even to a bare year — earns a row, and
undated work does not. So the Film table's thirteen rows come out as twelve
rows here and one exclusion:

  * Dune: Part Three (2026) is a row. Its own article's infobox reads
    `released = {{Film date|2026|12|18}}` and its short description is
    "Upcoming film by Denis Villeneuve". The row weighs 0, because the same
    infobox publishes no runtime and nobody has watched the film — an
    unreleased row carries an explicit `w` of 0, never a missing one, since
    `WEIGHT = x.w >= 0 ? x.w : 1` turns a missing weight into a silent
    invented hour (CLU-131). main() asserts the date is still in the future
    and that the runtime field is still empty, so the film's opening, or a
    published runtime, stops the build and brings the row back for review
    instead of leaving an empty bar standing.
  * Bond 26 (Year cell "TBA") is not a row — no article, no wikilink, no date
    anywhere, and the biography's own prose says only that Amazon MGM expects
    it in 2028. The TBA, the missing article and the future year are all
    asserted, so the day Wikipedia dates it the build fails and it comes back
    for review.

The Film table is cross-checked against the article's own lead, which is the
lesson built into tools/make_matt-johnson.py: a filmography table that lags
its own lead produces a list one film short. main() extracts every italicised
wikilink from the lead and asserts each is either a shipped row or a title
this file excludes on purpose.

The 2013 Year cell rowspans two films, Prisoners and Enemy — the other
make_matt-johnson.py lesson. Positional cell-picking without a rowspan carry
hands the second film the wrong year or none at all, so table_rows() carries
it and the carry is re-checked by name. The two 2013 films are additionally
asserted to be in release-date order rather than merely table order.

WEIGHTS: ALL OF THEM, FROM THE FILMS' OWN INFOBOXES
---------------------------------------------------
Every row that has opened carries `w`, the film's runtime in hours, read from
the `runtime` field of its own {{Infobox film}}. The page resolves
`WEIGHT = x.w >= 0 ? x.w : 1`, so a single row without a weight would silently
book itself as one hour and the total would be confidently wrong. minutes()
has no fallback and no estimate in it: a runtime that will not parse as one
plain figure stops the build. main() then asserts every released row got a
real infobox number, that the one unreleased row carries an explicit zero, and
that the eleven bar widths reconstitute the exact minute total.

One runtime here disagrees with the catalogue's other copy of the same film.
properties/dune.json takes its screen runtimes from Wikidata and gives Dune:
Part Two 166 minutes; the film's own Wikipedia infobox says 165, and 165 is
what this list uses, because this list's rule is the infobox and a total half
from one source and half from another belongs to neither. The two lists still
sync, because sync pairs on title and year and never on runtime.

THE DELIBERATE OVERLAP WITH THE DUNE LIST
-----------------------------------------
properties/dune.json already carries Dune (2021) and Dune: Part Two (2024),
and that is intended: a connected run and a director's filmography answer
different questions, and both may hold the same rows. Cross-list tick sync
groups rows on normalised-title|year|medium, so a tick on either list
propagates to the other — but only if the two files agree on the title string
and the year to the character. That agreement is not assumed here: main()
recomputes build.py's own sync keys for both films, checks that dune.json
produces the same two keys, and refuses to write if it does not. Getting this
wrong is what left Casablanca out of sync between the Criterion and Best
Picture lists (CLU-191).

Row ids carry a `dv-` prefix, so nothing here can collide with dune.json's
`dune-s-` ids, and main() asserts the two id sets are disjoint. Ids are
permanent — a collision would make two different rows tick together.

THE BLURB CARRIES NO FILM COUNT (CLU-190). The hours figure in it is computed
from the weights, so it cannot drift from them.

Data:   scratch/villeneuve/fetch.py -> scratch/villeneuve/*.wiki
Accent: scratch/villeneuve/accent.py
"""
import datetime
import json
import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki  # noqa: E402
from gwlib.prop import join_bits, slug  # noqa: E402

SLUG = "villeneuve"
CACHE = prop.ROOT / "scratch" / SLUG
ARTICLE = "Denis Villeneuve"
DUNE = "dune.json"

# The three career headings the biography divides itself with. The sections
# below take their boundaries from these rather than from years chosen by
# hand, so the shape of this list is the source's shape.
ERA_HEADINGS = ("1991–2012: Canadian films",
                "2013–2016: Transition to Hollywood",
                "2017–present: Critical and commercial acclaim")

# The kind of work each adaptation adapts. The work and its author are read
# out of the film's own {{Based on}} template; only this one word per film is
# editorial, and every note built from it is asserted to still name the work
# and the author the template gives.
ADAPTED_KIND = {
    "Incendies": "play",
    "Enemy": "novel",
    "Arrival": "short story",
}

# The four English-language films he directed from someone else's script get
# that writer named on the row. Which field carries the name differs by
# article, so both are read and the value is asserted to be one plain name.
CREDIT_WRITER = ("Prisoners", "Sicario")

WORDS = ("no", "one", "two", "three", "four", "five", "six", "seven", "eight",
         "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen")


def word(n):
    """Small counts read as words in this house's copy."""
    assert n < len(WORDS), "no word for %d; spell it or widen WORDS" % n
    return WORDS[n]


# --------------------------------------------------------------------------
# wikitext helpers
# --------------------------------------------------------------------------
_CELL = re.compile(r"^\|\s*(?:([^|\[{]*=[^|\[{]*)\|)?\s*(.*)$", re.S)


def table_after(text, marker):
    """The first wikitable following a bolded label such as '''Film'''."""
    m = re.search(r"^'''%s'''\s*$" % re.escape(marker), text, re.M)
    assert m, "no %r table label on the article" % marker
    a = text.index('{| class="wikitable"', m.end())
    return text[a:text.index("\n|}", a)]


def table_rows(seg, ncols):
    """Cells per row, with rowspan carried down to the rows it covers.

    The Film table's 2013 Year cell rowspans Prisoners and Enemy, and the
    Short film table's 2011 cell rowspans two more; positional picking without
    this hands the second film the wrong year or none at all. Chunks with no
    data lines — the trailing `|-` before `|}` — are skipped rather than
    emitted as a row of empty strings.
    """
    out, pending = [], {}
    for chunk in seg.split("\n|-")[1:]:
        lines = [l.strip() for l in chunk.split("\n")
                 if l.strip().startswith("|")]
        if not lines:
            continue
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
            sp = re.search(r'rowspan\s*=\s*"?(\d+)', attrs)
            if sp and int(sp.group(1)) > 1:
                pending[c] = [int(sp.group(1)) - 1, content]
        out.append(cols)
    return out


def yes(cell):
    """True only for a bare {{yes}}; anything qualified is not a credit."""
    return bool(re.fullmatch(r"\{\{\s*[Yy]es\s*\}\}", cell.strip()))


def no(cell):
    return bool(re.fullmatch(r"\{\{\s*[Nn]o\s*\}\}", cell.strip()))


def link(cell):
    """The wikilink target inside an italicised title cell, or None."""
    m = re.search(r"\[\[([^\]|]+)", cell)
    return m.group(1).strip() if m else None


def minutes(field, what):
    """A single whole-minute runtime out of an infobox field.

    A range, a blank, or anything that is not one plain figure fails, and
    that is the point: `WEIGHT = x.w >= 0 ? x.w : 1` means a row that quietly
    lost its runtime books itself as an hour. There is no fallback here and no
    estimate anywhere in this file — an unsourceable runtime is a blocker, not
    a number to invent.
    """
    v = wiki.clean(field or "")
    m = re.match(r"(\d{1,3})\s*minutes?\b", v.strip())
    assert m, "%s does not publish a single runtime: %r" % (what, v)
    n = int(m.group(1))
    assert 60 <= n <= 240, "%s: implausible runtime %d" % (what, n)
    return n


def film_dates(field, what):
    """Every release date on an infobox `released` field, earliest first.

    Footnotes come out first: two of these films carry <ref>...</ref> inside
    the {{Film date}} call, and a cite template full of numbers sitting beside
    a date pipe is how a wrong date gets read.
    """
    txt = re.sub(r"<ref[^>]*/>", "", field or "")
    txt = re.sub(r"<ref.*?</ref>", "", txt, flags=re.S)
    got = []
    for m in re.finditer(r"\|\s*(\d{4})\s*\|\s*(\d{1,2})\s*\|\s*(\d{1,2})\b",
                         txt):
        try:
            got.append(datetime.date(*(int(g) for g in m.groups())))
        except ValueError:
            pass
    assert got, "%s: no release date on the infobox" % what
    return sorted(set(got))


def based_on(field, what):
    """(work, author) out of a {{Based on|work|author}} infobox field.

    The wikilinks inside the arguments are collapsed to their labels BEFORE
    the arguments are split, because every one of these three templates wraps
    a piped link — [[Incendies (play)|Incendies]] — and splitting first hands
    back half a link as the author.
    """
    m = re.search(r"\{\{\s*[Bb]ased on\s*\|", field or "")
    assert m, "%s: no {{Based on}} template to read" % what
    body = field[m.end():field.index("}}", m.end())]
    body = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", body)
    body = re.sub(r"\[\[([^\]]+)\]\]", r"\1", body)
    parts = [wiki.clean(x).strip('"') for x in body.split("|")]
    assert len(parts) == 2, "%s: {{Based on}} has %d arguments: %s" \
        % (what, len(parts), parts)
    work, who = parts
    assert work and who, (what, work, who)
    return work, who


def one_writer(ib, what):
    """The single screenwriter named on a film's infobox.

    `screenplay` where the article uses it, `writer` where it does not; a
    field holding a list fails rather than printing half of it.
    """
    v = wiki.clean(ib("screenplay") or "") or wiki.clean(ib("writer") or "")
    assert v, "%s: no screenplay or writer field" % what
    assert "," not in v and " and " not in v, \
        "%s credits more than one writer (%r) — the row note says one" \
        % (what, v)
    return v


# --------------------------------------------------------------------------
# the cross-list sync keys, computed the way build.py computes them
# --------------------------------------------------------------------------
def normt(t):
    """build.py's sync-key normalizer, copied so this generator can predict
    the groups the build will actually form."""
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    t = re.sub(r"[^a-z0-9]+", " ", t).strip()
    return re.sub(r"^(the|a|an) ", "", t)


def year_of(x, n):
    """build.py's year-for-sync rule: the row number when it is a plain year,
    else an explicit y, else the single year named in the note."""
    if re.fullmatch(r"(18|19|20)\d{2}", n):
        return n
    explicit = str(x.get("y", ""))
    if re.fullmatch(r"(18|19|20)\d{2}", explicit):
        return explicit
    found = set(re.findall(r"\b((?:18|19|20)\d{2})\b", x.get("note") or ""))
    return found.pop() if len(found) == 1 else None


def sync_keys(path):
    """{build.py sync key -> [row id]} for one shipped property file.

    Films and games sync and nothing else does; the medium rides in the key so
    a film and a game of the same name and year never pair.
    """
    p = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    kind = p.get("kind") or ""
    if p.get("secret") or not ("film" in kind or "game" in kind):
        return {}
    medium = "g" if "game" in kind else "f"
    out = {}
    for s in p.get("sections", []):
        for x in s.get("items", []):
            y = year_of(x, str(x.get("n", "")))
            if y:
                out.setdefault(normt(x["t"]) + "|" + y + "|" + medium,
                               []).append(x["id"])
    return out


def hrs(m):
    return round(m / 60.0, 2)


def longdate(d):
    return "%d %s %d" % (d.day, d.strftime("%B"), d.year)


# Prefixed to an unreleased row's own note, so the row still reads correctly
# the day the film opens and the note needs no second edit.
NOT_OUT = "Not out yet — due %s, and the bar stays empty until it opens"


def main():
    today = datetime.date.today()
    art = wiki.wikitext(ARTICLE, cache_dir=CACHE)
    assert art, ("no cached wikitext for %r — run "
                 "scratch/villeneuve/fetch.py first" % ARTICLE)
    lead = art[:art.index("\n==")]

    # ---- the article divides its own career; borrow the boundaries --------
    for h in ERA_HEADINGS:
        assert re.search(r"^=+\s*%s\s*=+\s*$" % re.escape(h), art, re.M), \
            ("the career heading %r is gone — the sections take their "
             "boundaries from it and must be re-derived" % h)

    # ---- the Film table ---------------------------------------------------
    rows = table_rows(table_after(art, "Film"), 5)
    assert len(rows) == 13, \
        ("the Film table has %d rows, not the 13 this list was built against "
         "— a film was added or removed: %s"
         % (len(rows), [wiki.clean(r[1]) for r in rows]))

    table, not_directed = [], []
    for year, title, d, w, p in rows:
        rec = {"t": wiki.clean(title), "page": link(title),
               "yearcell": wiki.clean(year),
               "wrote": yes(w), "wrote_no": no(w),
               "produced": yes(p), "produced_no": no(p)}
        (table if yes(d) else not_directed).append(rec)
    assert not not_directed, \
        "a Film-table row is no longer a bare directing credit: %s" \
        % [x["t"] for x in not_directed]

    # The rowspan carry, re-checked by name rather than trusted. Prisoners and
    # Enemy share one 2013 Year cell; without the carry Enemy reads blank.
    dated = [x for x in table if re.fullmatch(r"\d{4}", x["yearcell"])]
    for x in dated:
        x["year"] = int(x["yearcell"])
    y2013 = [x["t"] for x in dated if x["year"] == 2013]
    assert y2013 == ["Prisoners", "Enemy"], \
        "the 2013 rowspan carry is broken: %s" % y2013

    # ---- what is held back, and what is here with an empty bar -----------
    excluded = {}

    # Bond 26: no year, no article, and the biography's prose says 2028.
    bond = [x for x in table if x["yearcell"] == "TBA"]
    assert [x["t"] for x in bond] == ["Bond 26"], [x["t"] for x in bond]
    assert bond[0]["page"] is None, \
        "Bond 26 now has an article — read it for a date and a runtime"
    bondyear = re.search(r"26th James Bond film\]\], with an expected release "
                         r"date in (\d{4})", art)
    assert bondyear, "the biography no longer states when Bond 26 is expected"
    assert int(bondyear.group(1)) > today.year, \
        "Bond 26 was expected in %s — check whether it has opened" \
        % bondyear.group(1)
    excluded["Bond 26"] = "not released; expected %s" % bondyear.group(1)

    # Dune: Part Three: a row, because its own article dates it — and a row
    # that weighs nothing, because that same article publishes no runtime and
    # nobody has watched it. Both halves are asserted, so the film opening or
    # a runtime appearing stops the build instead of leaving an empty bar.
    p3 = next(x for x in dated if x["t"] == "Dune: Part Three")
    p3page = wiki.wikitext(p3["page"], cache_dir=CACHE)
    assert p3page, "no cached article for %s" % p3["page"]
    p3ib = wiki.infobox(p3page, kind="film")
    assert p3ib, "no film infobox on %s" % p3["page"]
    p3_date = film_dates(p3ib("released"), p3["t"])[0]
    assert p3_date.year == p3["year"], (p3_date, p3["year"])
    assert p3_date > today, \
        ("Dune: Part Three opened on %s — move it in with the released films "
         "so it takes its runtime from its own infobox, and drop the not-out "
         "note from its row" % p3_date)
    assert not wiki.clean(p3ib("runtime") or ""), \
        ("Dune: Part Three now publishes a runtime (%r) while its stated "
         "release date %s is still in the future — decide whether the row "
         "weighs it or keeps the zero, rather than shipping both claims"
         % (wiki.clean(p3ib("runtime") or ""), p3_date))
    p3["runtime"] = 0
    p3["work"], p3["author"] = based_on(p3ib("based_on"), p3["t"])
    upcoming = [p3]

    films = [x for x in dated if x is not p3]
    assert len(films) == 11, [x["t"] for x in films]
    assert films[0]["t"] == "August 32nd on Earth" and films[0]["year"] == 1998
    assert films[-1]["t"] == "Dune: Part Two" and films[-1]["year"] == 2024
    assert all(a["year"] <= b["year"] for a, b in zip(films, films[1:])), \
        "the filmography table is not in release order"

    # ---- each film's own article -----------------------------------------
    for f in films:
        page = wiki.wikitext(f["page"], cache_dir=CACHE)
        assert page, "no cached article for %s" % f["page"]
        ib = wiki.infobox(page, kind="film")
        assert ib, "no film infobox on %s" % f["page"]
        f["runtime"] = minutes(ib("runtime"), f["t"])
        f["runtime_src"] = "infobox"
        f["released"] = film_dates(ib("released"), f["t"])[0]
        f["language"] = wiki.clean(ib("language"))
        f["country"] = wiki.clean(ib("country"))
        f["based_on_raw"] = ib("based_on")
        f["writer_name"] = one_writer(ib, f["t"]) if f["t"] in CREDIT_WRITER \
            else None
        f["lead"] = page[:page.index("\n==")] if "\n==" in page else page
        # the table's Year checked against the film's own article, not the
        # other way round
        assert f["released"].year == f["year"], \
            "%s: the filmography says %d, its article's first release is %s" \
            % (f["t"], f["year"], f["released"])
        assert f["released"] <= today, \
            "%s is dated %s and has not opened; it does not belong yet" \
            % (f["t"], f["released"])

    # Two films share 2013 and this list is in RELEASE order, so the order has
    # to be the dates' and it has to agree with the table's.
    assert [f["t"] for f in films if f["year"] == 2013] == \
        [f["t"] for f in sorted((g for g in films if g["year"] == 2013),
                                key=lambda g: g["released"])], \
        "Prisoners and Enemy are not in release-date order"

    # ---- runtimes: every one of them, from one kind of source -------------
    assert all(f["runtime"] for f in films), \
        [f["t"] for f in films if not f["runtime"]]
    assert {f["runtime_src"] for f in films} == {"infobox"}, \
        sorted({f["runtime_src"] for f in films})
    mins = sum(f["runtime"] for f in films)
    hours = mins / 60.0
    longest = max(films, key=lambda f: f["runtime"])
    shortest = min(films, key=lambda f: f["runtime"])

    # ---- the shorts, counted rather than remembered -----------------------
    shorts = table_rows(table_after(art, "Short film"), 7)
    assert all(yes(r[2]) for r in shorts), \
        "a Short film row is no longer a bare directing credit"
    short_titles = [wiki.clean(r[1]) for r in shorts]
    for t in ("Next Floor", "Le Technétium"):
        assert t in short_titles, "%s is no longer in the Short film table" % t
    cosmos = next(wiki.clean(r[5]) for r in shorts
                  if wiki.clean(r[1]) == "Le Technétium")
    assert cosmos == "Segment from the film Cosmos", cosmos
    videos = [t for t, r in zip(short_titles, shorts)
              if "Music video" in wiki.clean(r[5])]
    assert len(videos) == 3, videos

    # ---- the claims the intros and notes make, each checked ---------------
    assert "four French-language dramas" in lead, \
        "the lead no longer frames the Quebec films that way"
    assert "Academy Award for Best International Feature Film" in lead, \
        "the lead no longer records the Incendies nomination"
    quebec = [f for f in films if f["year"] <= 2012]
    english = [f for f in films if 2013 <= f["year"] <= 2016]
    scifi = [f for f in films if f["year"] >= 2017]
    assert (len(quebec), len(english), len(scifi)) == (4, 4, 3), \
        (len(quebec), len(english), len(scifi))
    assert all(f["wrote"] for f in quebec), \
        [f["t"] for f in quebec if not f["wrote"]]
    assert all(f["wrote_no"] for f in english), \
        "he now has a writing credit in 2013–2016: %s" \
        % [f["t"] for f in english if not f["wrote_no"]]
    assert all(f["produced_no"] for f in films if f["year"] < 2021), \
        [f["t"] for f in films if f["year"] < 2021 and not f["produced_no"]]
    assert [f["t"] for f in films if f["produced"]] == \
        ["Dune", "Dune: Part Two"], \
        [f["t"] for f in films if f["produced"]]
    assert all("French" in f["language"] for f in quebec), \
        [(f["t"], f["language"]) for f in quebec]
    assert all(f["country"] == "Canada" for f in quebec), \
        [(f["t"], f["country"]) for f in quebec]
    assert not any("French" in f["language"] for f in films
                   if f["year"] > 2012), \
        "he has made another French-language feature; the Quebec intro says "\
        "Incendies was the last"
    first_us = next(f for f in films if "United States" in f["country"])
    assert first_us["t"] == "Prisoners", first_us["t"]
    # the three sentences the row notes are built out of
    assert "feature film directorial debut" in quebec[0]["lead"], \
        "the debut claim is gone from August 32nd on Earth's article"
    frtitle = re.search(r"\{\{langx\|fr\|'''([^']+)'''\}\}", quebec[0]["lead"])
    assert frtitle, "August 32nd on Earth no longer gives its French title"
    maelstrom = next(f for f in films if f["t"] == "Maelström")
    assert "narrated by a talking fish" in maelstrom["lead"], \
        "Maelström's article no longer describes its narrator"
    poly = next(f for f in films if f["t"] == "Polytechnique")
    massacre = re.search(r"based on the (\d{4}) \[\[École Polytechnique "
                         r"massacre\]\]", poly["lead"])
    assert massacre, \
        "Polytechnique's article no longer states what it is based on"
    br = next(f for f in films if f["t"] == "Blade Runner 2049")
    seq = re.search(r"A sequel to ''\[\[Blade Runner\]\]'' \((\d{4})\)",
                    br["lead"])
    assert seq, "Blade Runner 2049's article no longer calls itself a sequel"
    gap = br["year"] - int(seq.group(1))
    assert gap > 0, gap

    # ---- the lead cross-check: nothing the lead names may go missing ------
    named = {m.group(1).split("|")[0].strip()
             for m in re.finditer(r"''\[\[([^\]]+)\]\]''", lead)}
    named = {n for n in named if n}
    shipped = {f["page"] for f in films + upcoming}
    unaccounted = named - shipped
    assert not unaccounted, \
        ("the lead names %s and this list neither ships nor excludes it — a "
         "filmography table lagging its own lead is how a list ends up one "
         "film short" % sorted(unaccounted))
    for f in films:
        assert f["page"] in named, \
            "%s is in the table but not the lead — check it is really his" \
            % f["t"]

    # ---- the sync groups this list is meant to join -----------------------
    # Not assumed: recomputed with build.py's own rules, on both files. A year
    # or a colon out of step is the whole failure, and it is a silent one —
    # the two lists simply stop ticking together (CLU-191).
    mine = {}
    for f in films:
        mine.setdefault(normt(f["t"]) + "|" + str(f["year"]) + "|f",
                        []).append(f["t"])
    theirs = sync_keys(prop.ROOT / "properties" / DUNE)
    assert theirs, "properties/%s contributed no syncable rows" % DUNE
    want = {"dune|2021|f", "dune part two|2024|f"}
    shared = set(mine) & set(theirs)
    assert shared == want, \
        ("this list and the Dune list do not group both Dune films: got %s, "
         "wanted %s. The usual cause is the two files disagreeing on a year "
         "or on title punctuation — match dune.json's strings."
         % (sorted(shared), sorted(want)))
    assert all(len(mine[k]) == 1 for k in want), mine

    # ---- row notes, every fact in them read from the sources above --------
    def adapted(f):
        work, who = based_on(f["based_on_raw"], f["t"])
        return "Adapted from %s, a %s by %s" % (work, ADAPTED_KIND[f["t"]],
                                                who)

    NOTE = {
        "August 32nd on Earth":
            "%s — his first feature, and his own screenplay"
            % frtitle.group(1),
        "Maelström": "An absurdist drama narrated by a talking fish",
        "Polytechnique": "A re-enactment of the %s École Polytechnique "
                         "massacre in Montreal" % massacre.group(1),
        "Blade Runner 2049": "A sequel to Blade Runner, made %d years after it"
                             % gap,
        "Dune": "Part one of a two-part adaptation of Frank Herbert's novel — "
                "also a row on the Dune list here, and the two tick together",
        "Dune: Part Two": "Part two, and the last feature he has released — "
                          "also a row on the Dune list here, and the two tick "
                          "together",
    }
    for t in ADAPTED_KIND:
        NOTE[t] = adapted(next(f for f in films if f["t"] == t))
    for f in films:
        if f["writer_name"]:
            NOTE[f["t"]] = join_bits(NOTE.get(f["t"]),
                                     "Written by %s" % f["writer_name"])
    NOTE["Prisoners"] = join_bits(NOTE["Prisoners"],
                                  "His first American production")
    # The one row nobody can have watched. Its note says when it is due and
    # what it adapts; both are read from its own article above.
    NOTE["Dune: Part Three"] = join_bits(
        NOT_OUT % longdate(p3_date),
        "Part three, adapted from %s, a novel by %s" % (p3["work"],
                                                       p3["author"]))
    assert "Wajdi Mouawad" in NOTE["Incendies"], NOTE["Incendies"]
    assert "José Saramago" in NOTE["Enemy"], NOTE["Enemy"]
    assert "Ted Chiang" in NOTE["Arrival"] and \
        "Story of Your Life" in NOTE["Arrival"], NOTE["Arrival"]
    assert "Taylor Sheridan" in NOTE["Sicario"], NOTE["Sicario"]
    assert "Un 32 août sur terre" in NOTE["August 32nd on Earth"], \
        NOTE["August 32nd on Earth"]
    # Nothing on this list says how a film turns out. Arrival and Prisoners
    # both hang on a reveal, so the two words that would give either away are
    # checked for across every note rather than trusted to care.
    for t, n in NOTE.items():
        assert not re.search(r"\btwist\b|\brevea|\bturns out\b", n, re.I), \
            "spoiler-shaped note on %s: %r" % (t, n)

    # ---- sections ---------------------------------------------------------
    ERAS = [
        ("quebec", "The Quebec films", quebec, [],
         "Twelve years and four features made in Quebec, a long way from any "
         "studio — the biography's own lead calls them four French-language "
         "dramas. He wrote or co-wrote every one, produced none, and all four "
         "are Canadian productions. Incendies closes the run and is the film "
         "that carried him out of it: an Academy Award nomination for Best "
         "International Feature, and the last feature he has made in French."),
        ("english", "Into English", english, [],
         "Four English-language films in four years, and the only stretch of "
         "his career where the Writer column is a bare no on every row — he "
         "directed all four from other people's scripts. Prisoners is the "
         "first American production here, and Arrival is where the science "
         "fiction starts."),
        ("scifi", "Science fiction at scale", scifi, upcoming,
         "The Blade Runner sequel, and then Dune. The three he has released "
         "are the three longest features he has made — %d minutes between "
         "them, more than a third of everything on this list — and Dune is "
         "the first film he produced as well as directed. Part Three is dated "
         "%s and sits here with an empty bar until it opens."
         % (sum(f["runtime"] for f in scifi), longdate(p3_date))),
    ]

    sections, placed = [], []
    for key, title, got, coming, intro in ERAS:
        assert got, key
        placed += got
        secrows = got + coming
        items = []
        for f in secrows:
            it = {"id": "dv-%d-%s" % (f["year"], slug(f["t"])),
                  "t": f["t"], "n": str(f["year"]), "w": hrs(f["runtime"])}
            if f["t"] in NOTE:
                it["note"] = NOTE[f["t"]]
            items.append(it)
        # The hours are the released films' hours. A dated row with an empty
        # bar is counted as a row and named, never folded into a total.
        sub = "%d–%d · %d films · %d hours" \
              % (secrows[0]["year"], secrows[-1]["year"], len(secrows),
                 round(sum(f["runtime"] for f in got) / 60.0))
        if coming:
            sub += " · %d not out yet" % len(coming)
        sections.append({
            "id": key, "title": title,
            "sub": sub,
            "intro": intro,
            "items": items,
        })
    sections[0]["open"] = True

    # the intro claim about the third section, checked against the runtimes
    assert sorted(f["runtime"] for f in films)[-3:] == \
        sorted(f["runtime"] for f in scifi), \
        "the three longest features are no longer the last three"
    assert sum(f["runtime"] for f in scifi) * 3 > mins, \
        "the science fiction is no longer more than a third of the hours"

    # ---- the arithmetic, checked -----------------------------------------
    assert placed == films, "a film was dropped or placed twice"
    items = [x for s in sections for x in s["items"]]
    assert len(items) == len(films) + len(upcoming), \
        (len(items), len(films), len(upcoming))
    for s in sections:
        assert all(a["n"] <= b["n"]
                   for a, b in zip(s["items"], s["items"][1:])), \
            "%s is out of year order" % s["title"]
    # Every row weighted and none of them defaulted: an absent `w` on a
    # weighted list is worth a silent invented hour. The only zeros are the
    # dated films nobody can have watched yet, named row by row.
    assert all(isinstance(x["w"], float) and x["w"] >= 0 for x in items), \
        [x["id"] for x in items if not isinstance(x.get("w"), float)]
    zeros = {x["id"] for x in items if not x["w"]}
    assert zeros == {"dv-%d-%s" % (f["year"], slug(f["t"]))
                     for f in upcoming}, sorted(zeros)
    assert not any("opt" in x for x in items), \
        "nothing here is optional; he directed all of it"
    barsum = round(sum(x["w"] for x in items), 2)
    assert abs(barsum - hours) < 0.05, (barsum, hours)
    # The section headings print rounded hours; rounding three numbers and
    # adding them is how a list advertises an hour it does not have.
    printed = sum(round(sum(f["runtime"] for f in got) / 60.0)
                  for _, _, got, _, _ in ERAS)
    assert printed == round(hours), \
        "section headings add to %d hours, the real total rounds to %d" \
        % (printed, round(hours))

    # Ids are permanent, and dune.json's rows must never be among them.
    ids = [x["id"] for x in items]
    assert len(ids) == len(set(ids)), ids
    dune_ids = {i for v in theirs.values() for i in v}
    assert not (set(ids) & dune_ids), sorted(set(ids) & dune_ids)

    # ---- where the two copies of a shared film disagree -------------------
    # The Dune list weights its screen rows from Wikidata; this one weights
    # from the films' own infoboxes, and for one of the two shared films those
    # sources differ. Read theirs off their bar width rather than typing it,
    # and only say anything when there is something to say — if the two ever
    # agree, the sentence disappears instead of going stale.
    dunep = json.loads((prop.ROOT / "properties" / DUNE)
                       .read_text(encoding="utf-8"))
    dune_rows = {x["id"]: x for s in dunep["sections"] for x in s["items"]}
    disagree = []
    for key in sorted(want):
        ours = next(f for f in films
                    if normt(f["t"]) + "|" + str(f["year"]) + "|f" == key)
        for rid in theirs[key]:
            w = dune_rows[rid].get("w")
            assert isinstance(w, (int, float)) and w > 0, (rid, w)
            if round(w * 60) != ours["runtime"]:
                disagree.append((ours["t"], round(w * 60), ours["runtime"]))
    runtime_note = ("Every row for a film that has opened carries one, read "
                    "from the runtime field of that film's own Wikipedia "
                    "infobox — %d hours %d minutes across the %s of them, "
                    "from %s at %d minutes to %s at %d. There are no "
                    "unweighted rows and no estimates anywhere: a row missing "
                    "its runtime would quietly count as one hour and make the "
                    "total confidently wrong, so the generator stops rather "
                    "than guess, and the one film that is not out carries an "
                    "explicit zero instead."
                    % (mins // 60, mins % 60, word(len(films)), shortest["t"],
                       shortest["runtime"], longest["t"], longest["runtime"]))
    if disagree:
        runtime_note += (
            " %s differs from the catalogue's other copy of the same film: "
            "the Dune list takes its screen runtimes from Wikidata and has "
            "%s at %d minutes, where the film's own infobox says %d. This "
            "list keeps to the infobox for all %s, because a total half from "
            "one source and half from another belongs to neither. The two "
            "rows still tick together — films are paired by title and year, "
            "never by runtime."
            % ("One number" if len(disagree) == 1 else "Two numbers",
               disagree[0][0], disagree[0][1], disagree[0][2],
               word(len(films))))

    # ---- the accent pair is nobody else's --------------------------------
    accent, accent_dark = "#704F5C", "#C28AA0"
    for f in sorted((prop.ROOT / "properties").glob("*.json")):
        if f.stem in (SLUG, "index", "search"):
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

    p = {
        "slug": SLUG,
        "title": "Denis Villeneuve",
        "subtitle": "the directed features, in release order",
        "kind": "films",
        # Under Kubrick's 76 and well under the Nolan and Scorsese end of the
        # director range: a working career most people can name two or three
        # films from rather than eight, and a shorter one than the
        # filmographies above it. Comfortably above Raimi's 58. See
        # POPULARITY.md.
        "popularity": 62,
        # Not a story, so not a sequence: the order these came out in
        # is a fact about the maker, not an instruction to the viewer
        # (Nathan, CLU-372). Prerequisites, where any exist, live in
        # tools/data/sequences.json and are enforced separately.
        "random": True,
        "year": "%d–%d" % (films[0]["year"],
                           max(f["year"] for f in films + upcoming)),
        "blurb": "Quebec dramas in French, thrillers made from other people's "
                 "scripts, and the science fiction that made his name — every "
                 "feature he has directed, in release order and weighted by "
                 "runtime, about %d hours of it." % round(hours),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        # A drained plum, and the dusty rose of an Arrakeen sunset for dark
        # mode. Measured in CIELAB against every accent shipping in
        # properties/ (scratch/villeneuve/accent.py): the colours anyone would
        # reach for first are all spoken for — the Dune ochre IS the Dune
        # list's accent, the Blade Runner 2049 sodium orange lands 2.0 from
        # Mission: Impossible's, and the cold Arrival grey-green IS Fincher's.
        # This pair sits 17.4 and 12.0 from its nearest shipped neighbours.
        "accent": accent,
        "accentDark": accent_dark,
        "tiers": False,
        "notes": [
            ["Directed features only.",
             "A film is here if the filmography's Director column says yes "
             "and the source gives it a release date. Coming out is not the "
             "test; being dated is. Nothing else gates it: he wrote all "
             "four Quebec films and none of the four that followed, and he is "
             "credited producer on only the two Dune films. Out: the %s "
             "shorts, music videos and commercials the article keeps in its "
             "own separate table, Next Floor and the Le Technétium segment of "
             "the anthology Cosmos among them. There is no Denis Villeneuve "
             "filmography article — this is the Film table inside the "
             "biography, cross-checked against the biography's own lead so "
             "that a table lagging its lead cannot leave a film off."
             % word(len(shorts))],
            ["One film is here with an empty bar, and one is not here at all.",
             "Dune: Part Three is a row: its own article dates it %s, and "
             "dated work belongs on a list even before it opens. Its bar is "
             "empty because the same article publishes no runtime and nobody "
             "has watched it, and a weight this list cannot source is one it "
             "refuses to invent — so it counts as a film and adds no hours. "
             "Bond 26 is the one row of the Film table that is not here: no "
             "article, no wikilink and no date, only the biography saying "
             "Amazon MGM expects it in %s. Both are re-read every time this "
             "list is generated — the build stops if Part Three opens, if it "
             "publishes a runtime, or if Bond 26 acquires a date — so the "
             "rows change on the sources rather than whenever somebody "
             "remembers. That is %s rows on the table and %s here."
             % (longdate(p3_date), bondyear.group(1),
                word(len(rows)), word(len(films) + len(upcoming)))],
            ["Both Dune films are on the Dune list too, on purpose.",
             "Dune (2021) and Dune: Part Two (2024) are rows here and rows on "
             "the Dune list, and that is deliberate rather than a duplicate "
             "to clean up. The Dune list is a connected run through Frank "
             "Herbert's novels and every screen version of them; this one is "
             "a director's filmography. They answer different questions, so "
             "both keep the films. Nothing is watched twice and no hours are "
             "counted twice, because each list totals only its own rows — and "
             "film rows are paired across lists by title and year, so ticking "
             "either Dune here ticks the same film there, and the other way "
             "round."],
            ["Bar widths are runtimes.", runtime_note],
            "Roster, career divisions and the writing and producing credits "
            "from the Filmography and Career sections of Wikipedia's Denis "
            "Villeneuve, read from the tables and headings themselves; "
            "runtimes, release dates, screenwriters and source material from "
            "each film's own article.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %s rows (%s released), %d min = %.2f hours "
          "(prints as %d)"
          % (out.name, len(items), len(films), mins, hours, round(hours)))
    print("   bar widths sum to %.2f hours; section headings print %d"
          % (barsum, printed))
    for s in sections:
        print("   %-22s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))
    for f in films + upcoming:
        print("   %-4d %-22s %3d min  w=%.2f  %-32s%s"
              % (f["year"], f["t"], f["runtime"], hrs(f["runtime"]),
                 "dv-%d-%s" % (f["year"], slug(f["t"])),
                 "  (not out)" if not f["runtime"] else ""))
    print("   sync groups shared with %s: %s"
          % (DUNE, ", ".join(sorted(shared))))
    print("   held back: %s"
          % "; ".join("%s (%s)" % (t, w) for t, w in sorted(excluded.items())))


if __name__ == "__main__":
    main()
