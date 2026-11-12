#!/usr/bin/env python3
"""Generate properties/the-big-o.json — all 26 episodes, both seasons.

    python3 tools/make_the-big-o.py

Sunrise's film-noir mecha series: thirteen episodes on Wowow in 1999–2000,
thirteen more on Sun Television in 2003. 26 rows, one per episode, in the
broadcast order and the numbering the source itself uses.

THE SLUG IS `the-big-o`, NOT `big-o`. The house is split on leading articles —
x-files, twilight-zone and sandman drop theirs; the-office, the-wire,
the-simpsons and the-sopranos keep theirs — and the split is not arbitrary.
The ones that drop it are already unique without it. The ones that keep it
would otherwise be a generic phrase standing for something else, which is
exactly this title's problem: `?p=big-o` reads as the complexity notation
before it reads as an anime. The source keeps the article too — the article's
own DISPLAYTITLE and bold lead are both ''The Big O''.

THE TWO SEASONS WERE MADE UNDER DIFFERENT CIRCUMSTANCES, AND THAT IS A FACT
ABOUT THE PRODUCTION, so it rides in the section subs the way vinland-saga's
two studios do. Both articles say it, and main() asserts both sentences
before this builds:

  * the series article's lead: "Originally planned as a 26-episode series,
    low viewership in Japan reduced production to the first 13. Positive
    international reception resulted in a second season consisting of the
    remaining 13 episodes, co-produced by Cartoon Network, Sunrise, and
    Bandai Visual."; and
  * the episode-list article: "Originally a 26-episode series, it was reduced
    to 13 episodes due to low ratings in Japan. However, positive
    international reception resulted in a second season co-produced by
    Cartoon Network, Sunrise, and Bandai Visual."

So season 1's sub names Sunrise alone and season 2's names Sunrise with
Cartoon Network and Bandai Visual. The studio never changed; the money did.

IT ENDS WHERE IT ENDS, AND THE SOURCE DOCUMENTS WHY WITHOUT ANYONE HAVING TO
DESCRIBE THE ENDING. The production section: "Along with the 13 episodes of
season two, Cartoon Network had an option for 26 additional episodes to be
written by Konaka, but according to Jason DeMarco, executive producer for
season two, the middling ratings and DVD sales in the United States and Japan
made any further episodes impossible to be produced." A continuation was
optioned and it was not made — that is a production fact and it is the whole
of what this list says about the end. What the last episode IS (a finale) is
allowed; what happens in it is not, and nothing here says.

NUMBERING IS THE SOURCE'S. The episode-list article numbers season 2 as
episodes 14 to 26 rather than restarting at 1, and there is no
EpisodeNumber2 anywhere in it, so there is no in-season numbering to prefer.
Rows therefore run 1 to 26 straight through, asserted contiguous.

WEIGHTS: NONE, AND THE HUNT IS THE FINDING. Four places a per-episode running
time could live were checked and all four came up empty; scratch/agent-bigo/
holds the probes, and main() re-asserts what it can from the cached wikitext:

  1. Each episode's own Wikipedia article. There are none. All 26 titles were
     probed bare, as "<title> (The Big O)" and as "<title> (The Big O
     episode)" — 78 candidates. Seven of the bare forms exist, because six of
     the titles are common nouns (Leviathan, Hydra, Stripes, Eyewitness,
     Electric City) and one is a Queen lyric; every one of them is a
     disambiguation page or an unrelated subject, none carries P31 =
     television series episode, and none carries P179 = The Big O. Not one
     Title field in the episode table is a wikilink either, which main()
     asserts.
  2. Per-episode Wikidata P2047. There are no per-episode Wikidata items at
     all: the series is Q974411, and a haswbstatement search for items
     declaring P179, P361 or P4908 pointing at it returns zero. The series
     item itself carries no P2047 and no P527 has-part statements, so there
     is nothing to read a runtime off.
  3. Season articles. There are none. "The Big O season 1" and "The Big O
     season 2" both redirect to the episode-list article and "The Big O II"
     redirects to the series article, so the list article's two section
     headings are the only season-level source that exists.
  4. The episode table's own RunTime fields, and the infoboxes. Not one of
     the 26 {{Episode list}} blocks carries a RunTime. The series uses
     {{Infobox animanga/Video}}, which carries no runtime parameter in either
     of its two instances, and the string "minutes" does not occur anywhere
     in the series article, the episode-list article or the music article.

All 26 rows or none, because a row with no `w` on a weighted list silently
counts as one hour (CLU-131) — 26 half-hours would read as 26 hours. It is
none, main() asserts none, and the notes name every source that was checked.

CROSS-LIST SYNC: THERE IS NONE, AND IT IS CONFIRMED RATHER THAN ASSUMED.
build.py's gate is `syncable = "film" in kind or "game" in kind`; this list's
kind is "anime", so no row ever reaches the pairing code. main() re-states
that gate literally so a future kind change trips it. Belt and braces, it
also asserts no row carries an explicit `y`, no `n` is a bare year, and no
note contains one — the note fallback in build.py reads a single year out of
a note when `n` is not a year, and an episode called "Leviathan" pairing with
a same-titled film is exactly the accident that would cause. Airdates are
therefore kept out of row notes entirely and live in the section intros.

ONE AIRDATE DISAGREES WITH ITSELF, AND THE EPISODE TABLE WINS. The series
article's second infobox closes season 2 on March 23, 2003. The episode table
dates the last episode March 27, 2003, and the episode-list article's prose
says the season "concluded with 'The Show Must Go On' on March 27, 2003".
Two sources to one, and the table is internally consistent — season 2 ran
weekly from Thursday January 2, and thirteen weekly slots land on March 27.
main() asserts the table and the prose agree, and asserts the infobox is
still carrying its known discrepancy so that a third value would fail the
build rather than pass unnoticed.

EXCLUSIONS. Everything else in the franchise is another medium: the six-volume
manga (1999–2001) and the two-volume Lost Memory (2002–2003), the Paradigm
Noise novel, the "Walking Together On The Yellow Brick Road" drama CD, and
the Super Robot Wars appearances. The 2001 Toonami broadcast, the uncut Adult
Swim reruns and the 2007 Animax reruns are the same 26 episodes, not more of
them. There is no film and no OVA; main() asserts the series article still
files exactly two {{Infobox animanga/Video}} blocks, so a third one appearing
fails the build.

Everything is machine-read from the cached Wikipedia wikitext in
scratch/agent-bigo/. Nothing is typed in from memory. Before anything is
written: each season's parsed row count is asserted against that season's own
{{Infobox animanga/Video}} episodes field AND against the two prose sentences
that give the split; the overall numbering is asserted contiguous 1..26;
airdates are asserted non-decreasing and matched against each infobox's first
and last dates; each section's year span is asserted against the year span in
the list article's own section heading; and the accent pair is asserted
unused by every other property on disk.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki  # noqa: E402

SLUG = "the-big-o"

# The wikitext cache. Nothing here is required — gwlib re-fetches and
# repopulates whichever of these exists — but a warmed cache keeps this
# generator offline and keeps it off Wikipedia's rate limiter.
CACHE = next((d for d in (prop.ROOT / "scratch" / "agent-bigo",
                          prop.ROOT / "scratch" / SLUG)
              if d.exists()), prop.ROOT / "scratch" / "agent-bigo")

LIST_PAGE = "List of The Big O episodes"
SERIES_PAGE = "The Big O"

SEASONS = [1, 2]
TOTAL_EPISODES = 26          # asserted five ways, never assumed
PER_SEASON = 13              # ditto

# The series article's second infobox closes season 2 four days before the
# episode table does. Held here as a named constant so the discrepancy is
# visible rather than silently tolerated — see the docstring.
INFOBOX_S2_LAST_DISCREPANCY = (2003, 3, 23)

ACCENT = "#2C2F3A"       # the noir charcoal of the Big O's armour
ACCENT_DARK = "#F2C14E"  # ...and the yellow of its trim, for dark mode

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

# Rows that get a note. Nothing here says what happens in an episode — only
# what the episode IS, which is the copy rule. Episode 13's second bit is
# appended in main() from the source rather than typed here: the episode
# table titles it with a katakana middle dot and the article's lead writes it
# with full stops, and a reader searching for one form should find the other.
ROW_NOTES = {
    1: "series premiere",
    13: "first-season finale",
    14: "second-season premiere",
    # no "series finale" on 26: the last row already says it (CLU-123,
    # CLU-557). 13 keeps its note, which carries the alternate spelling.
}


def text(page):
    t = wiki.wikitext(page, cache_dir=CACHE)
    assert t, "no wikitext for %r" % page
    return t


def strip_refs(t):
    """Prose with the footnotes gone, for the sentences main() reads as fact."""
    t = re.sub(r"<ref[^>]*/>", "", t)
    return re.sub(r"<ref.*?</ref>", "", t, flags=re.S)


def flat(t):
    """Footnote-free prose on one line, for sentence matching."""
    return re.sub(r"\s+", " ", strip_refs(t))


def date_in(field, kind="Start"):
    """The first {{Start date}} in a chunk, as (y, m, d)."""
    m = re.search(r"\{\{%s date\s*\|\s*(\d{4})\s*\|\s*(\d{1,2})\s*\|"
                  r"\s*(\d{1,2})" % kind, field or "", re.I)
    assert m, "no %s date in %r" % (kind.lower(), (field or "")[:80])
    return tuple(int(g) for g in m.groups())


def plain_date(s):
    """`October 13, 1999` -> (1999, 10, 13). The animanga infoboxes write
    their dates as prose rather than as a date template."""
    m = re.search(r"(%s)\s+(\d{1,2}),\s*(\d{4})" % "|".join(MONTHS), s or "")
    assert m, "no plain date in %r" % (s or "")[:60]
    return (int(m.group(3)), MONTHS.index(m.group(1)) + 1, int(m.group(2)))


def fmt_date(d):
    return "%s %d, %d" % (MONTHS[d[1] - 1], d[2], d[0])


def year_span(years):
    a, b = min(years), max(years)
    return str(a) if a == b else "%d–%d" % (a, b)


def season_segments(list_text):
    """{season: (segment, heading year span)} cut at the article's own
    `===Season N (years)===` headings — the source's division, not a guess."""
    heads = [(int(m.group(1)), m.group(2), m.start(), m.end())
             for m in re.finditer(r"^===\s*Season (\d+) \((\d{4}(?:–\d{4})?)\)"
                                  r"\s*===\s*$", list_text, re.M)]
    assert [h[0] for h in heads] == SEASONS, \
        "the list article's season headings are %s, expected %s" \
        % ([h[0] for h in heads], SEASONS)
    out = {}
    for i, (n, span, _s, e) in enumerate(heads):
        end = heads[i + 1][2] if i + 1 < len(heads) else len(list_text)
        out[n] = (list_text[e:end], span)
    return out


def rows_from(segment, label):
    """[(number, title, (y,m,d), block)] for one season's episode table."""
    raw = wiki.episodes(segment)
    assert raw, "%s parsed empty" % label
    rows = []
    for n1, n2, title, _year, block in raw:
        assert n1, "%s row with no episode number: %r" % (label, title)
        assert n2 is None, \
            "%s episode %s now carries a second number — the source has " \
            "grown in-season numbering and the rows should use it" % (label, n1)
        assert title, "%s episode %s has no title" % (label, n1)
        assert not re.search(r"\|\s*RunTime\s*=\s*\S", block, re.I), \
            "%s episode %s now documents a running time — revisit weights, " \
            "because the only reason this list is unweighted is that no " \
            "episode had one" % (label, n1)
        rows.append((n1, title, date_in(block), block))
    dates = [d for _n, _t, d, _b in rows]
    assert dates == sorted(dates), "%s airdates are not in broadcast order" % label
    return rows


def balanced(text_, opening):
    """Every template body starting with `opening`, brace-balanced.

    A non-greedy match to the next `\\n}}` is not good enough here: these
    infoboxes nest {{English anime licensee}} and {{ubl}} inside themselves,
    and their closing braces sit on their own lines, so a lazy match stops
    inside the box and every field after it reads as empty. Counting braces
    is the only way to get the whole block."""
    out = []
    for m in re.finditer(re.escape(opening), text_):
        i, depth = m.start(), 0
        while i < len(text_):
            if text_.startswith("{{", i):
                depth += 1
                i += 2
            elif text_.startswith("}}", i):
                depth -= 1
                i += 2
                if depth == 0:
                    break
            else:
                i += 1
        assert depth == 0, "unbalanced %s block" % opening
        out.append(text_[m.start() + len(opening):i - 2])
    return out


def series_infoboxes(series_text):
    """The two {{Infobox animanga/Video}} blocks, as field readers.

    A third one appearing would mean a film, an OVA or a third season, and
    this list would be short — so the count is asserted, not assumed."""
    blocks = balanced(series_text, "{{Infobox animanga/Video")
    assert len(blocks) == len(SEASONS), \
        "the series article carries %d animanga/Video infoboxes, expected " \
        "%d — a new one means another anime installment exists" \
        % (len(blocks), len(SEASONS))
    out = []
    for b in blocks:
        assert not re.search(r"^\s*\|\s*runtime\s*=", b, re.M | re.I), \
            "an animanga/Video infobox now has a runtime — revisit weights"

        def field(name, b=b):
            m = re.search(r"^\s*\|\s*%s\s*=\s*(.*?)(?=\n\s*\|\s*[a-z_]+\s*=|\Z)"
                          % name, b, re.M | re.S | re.I)
            return m.group(1).strip() if m else ""
        out.append(field)
    return out


def first_network(field):
    """The first network's article name, taken from the wikilink target so a
    piped display label (`[[Sun Television|SUN]]`) still reads in full."""
    m = re.search(r"\[\[([^\]|]+)", field or "")
    assert m, "no network wikilink in %r" % (field or "")[:60]
    return m.group(1).strip()


def production_sentences(series_text, list_text):
    """The three sentences this list's framing rests on, read as data.

    Returned so the notes quote what the source says rather than a paraphrase
    of it, and asserted so a rewrite upstream fails the build instead of
    leaving this list asserting something the source no longer supports."""
    lead = re.search(
        r"Originally planned as a 26-episode series, low viewership in Japan "
        r"reduced production to the first (\d+)\. Positive international "
        r"reception resulted in a second season consisting of the remaining "
        r"(\d+) episodes, co-produced by Cartoon Network, Sunrise, and "
        r"\[\[Bandai Visual\]\]\.", flat(series_text))
    assert lead, \
        "the series article's lead no longer explains the 13/13 split and " \
        "the co-production — the section subs and the notes both quote it"

    listed = re.search(
        r"Originally a 26-episode series, it was reduced to (\d+) episodes "
        r"due to low ratings in Japan\. However, positive international "
        r"reception resulted in a second season co-produced by Cartoon "
        r"Network, \[\[Sunrise \(company\)\|Sunrise\]\], and "
        r"\[\[Bandai Visual\]\]\.", flat(list_text))
    assert listed, \
        "the episode-list article no longer states the same production " \
        "history as the series article"

    ended = re.search(
        r"Along with the 13 episodes of season two, Cartoon Network had an "
        r"\[\[Option \(films\)\|option\]\] for (\d+) additional episodes to "
        r"be written by Konaka, but according to Jason DeMarco, executive "
        r"producer for season two, the middling ratings and DVD sales in the "
        r"United States and Japan made any further episodes impossible to be "
        r"produced\.", flat(series_text))
    assert ended, \
        "the series article no longer documents the optioned-but-unmade " \
        "continuation — the note saying this is all of it quotes it"

    asked = re.search(
        r"When Cartoon Network later offered funding for the second season, "
        r"its representatives requested that the story be satisfactorily "
        r"finished at the end of this season", flat(series_text))
    assert asked, \
        "the series article no longer says Cartoon Network asked for the " \
        "story to be finished within the second season"

    counts = (int(lead.group(1)), int(lead.group(2)), int(listed.group(1)))
    assert set(counts) == {PER_SEASON}, \
        "the prose now splits the run as %s, not %d and %d" \
        % (counts, PER_SEASON, PER_SEASON)
    return int(ended.group(1))


def check_not_syncable(p):
    """build.py's own gate, restated. An anime-kind list never reaches the
    pairing code; if that ever changes, this is where it fails loudly."""
    kind = p.get("kind") or ""
    assert "film" not in kind and "game" not in kind, \
        "kind %r is syncable — every row would try to pair by title+year" % kind
    for s in p["sections"]:
        for x in s["items"]:
            assert "y" not in x, "%s carries an explicit year" % x["id"]
            assert not re.fullmatch(r"(18|19|20)\d{2}", str(x.get("n", ""))), \
                "%s numbers itself with a bare year" % x["id"]
            leak = re.findall(r"\b(?:18|19|20)\d{2}\b", x.get("note") or "")
            assert not leak, \
                "%s leaks the year %s into its note — build.py reads a single " \
                "year out of a note when `n` is not one, which would pair " \
                "this episode with a same-titled film" % (x["id"], leak)


def check_accent():
    """The pair, and each half of it, must be unused by every other list."""
    for f in sorted((prop.ROOT / "properties").glob("*.json")):
        if f.stem in (SLUG, "index", "search"):
            continue
        other = json.loads(f.read_text(encoding="utf-8"))
        pair = (other.get("accent"), other.get("accentDark"))
        assert pair != (ACCENT, ACCENT_DARK), \
            "accent pair already belongs to %s" % f.stem
        for hexv in (ACCENT, ACCENT_DARK):
            assert hexv not in pair, "%s already uses %s" % (f.stem, hexv)


def main():
    list_text = text(LIST_PAGE)
    series_text = text(SERIES_PAGE)

    optioned = production_sentences(series_text, list_text)
    boxes = series_infoboxes(series_text)
    segs = season_segments(list_text)
    check_accent()

    rows = {n: rows_from(segs[n][0], "season %d" % n) for n in SEASONS}

    # 1. every Title field is plain text — a wikilinked title would mean an
    # episode has its own article, and the runtime hunt would have to run again
    for n in SEASONS:
        for num, _t, _d, block in rows[n]:
            raw = re.search(r"\|\s*Title\s*=\s*(.*)", block)
            assert raw and "[[" not in raw.group(1), \
                "episode %d's title is now a wikilink — an episode article " \
                "exists and may document a running time" % num

    # 2. two independent counts per season: the parsed table and the season's
    # own infobox, with the prose already asserted at PER_SEASON above
    for n in SEASONS:
        ib = boxes[n - 1]
        assert len(rows[n]) == PER_SEASON, \
            "season %d parsed %d rows, expected %d" \
            % (n, len(rows[n]), PER_SEASON)
        assert ib("episodes").strip() == str(PER_SEASON), \
            "season %d's infobox says %r episodes, parsed %d" \
            % (n, ib("episodes"), len(rows[n]))
        assert ib("studio").strip().startswith("[[Sunrise") or \
            wiki.clean(ib("studio")) == "Sunrise", \
            "season %d is no longer a Sunrise production: %r" \
            % (n, ib("studio"))

    # 3. overall numbering runs 1..26 unbroken across the two seasons
    numbered = [num for n in SEASONS for num, _t, _d, _b in rows[n]]
    assert numbered == list(range(1, TOTAL_EPISODES + 1)), \
        "episode numbering is not contiguous 1..%d: %s" \
        % (TOTAL_EPISODES, numbered)

    # 4. airdates against each infobox's own first/last, and the one known
    # discrepancy held where it can be seen
    first = {n: rows[n][0][2] for n in SEASONS}
    last = {n: rows[n][-1][2] for n in SEASONS}
    for n in SEASONS:
        ib = boxes[n - 1]
        assert plain_date(ib("first")) == first[n], \
            "season %d: infobox opens %s, first episode aired %s" \
            % (n, ib("first"), first[n])
    assert plain_date(boxes[0]("last")) == last[1], \
        "season 1: infobox closes %s, last episode aired %s" \
        % (boxes[0]("last"), last[1])
    ib_s2_last = plain_date(boxes[1]("last"))
    assert ib_s2_last in (last[2], INFOBOX_S2_LAST_DISCREPANCY), \
        "the series infobox now closes season 2 on %s, which is neither the " \
        "episode table's %s nor the known %s discrepancy — re-read the source" \
        % (ib_s2_last, last[2], INFOBOX_S2_LAST_DISCREPANCY)
    corrected = ib_s2_last != last[2]
    # ...and the episode table is backed by the list article's own prose
    assert re.search(r"concluded with \"The Show Must Go On\" on %s"
                     % fmt_date(last[2]), flat(list_text)), \
        "the list article's prose no longer dates the finale %s" \
        % fmt_date(last[2])

    # 4b. the first-season finale is titled two ways by the one article: the
    # episode table uses a katakana middle dot, the lead uses full stops
    lead_form = re.search(r"concluded with \"(R\.D\.)\" on %s"
                          % fmt_date(last[1]), flat(list_text))
    assert lead_form, \
        "the list article's lead no longer names the season 1 finale — the " \
        "row note quotes the alternate spelling it gives"
    table_form = rows[1][-1][1]
    assert table_form != lead_form.group(1), \
        "the two spellings of the season 1 finale have converged on %r; the " \
        "row note pointing at the other one should go" % table_form
    ROW_NOTES[13] = prop.join_bits(
        ROW_NOTES[13],
        "the article's lead writes this title \"%s\"" % lead_form.group(1))

    # 5. the weights finding, re-asserted from the cached source every build
    for name, t in (("series", series_text), ("episode list", list_text),
                    ("music", text("Music of The Big O"))):
        assert not re.search(r"\d+\s*minutes", t, re.I), \
            "the %s article now gives a duration in minutes — revisit " \
            "weights, because the only reason this list is unweighted is " \
            "that no source documented one" % name

    sections = []
    for n in SEASONS:
        ib = boxes[n - 1]
        span = year_span([d[0] for _n, _t, d, _b in rows[n]])
        assert span == segs[n][1], \
            "season %d spans %s, the list article's heading says %s" \
            % (n, span, segs[n][1])
        studio = ("Sunrise" if n == 1 else
                  "Sunrise with Cartoon Network and Bandai Visual")
        sections.append({
            "id": "s%d" % n,
            "title": "Season %d" % n,
            "sub": prop.join_bits(span, "%d episodes" % len(rows[n]), studio,
                                  first_network(ib("network"))),
            "intro": (
                "Thirteen episodes on Wowow, %s to %s. The source says the "
                "run was outlined at 26 and cut to 13 after low viewership "
                "in Japan." % (fmt_date(first[1]), fmt_date(last[1]))
                if n == 1 else
                "The other thirteen, three years later, and they exist "
                "because of how the show did abroad: positive international "
                "reception brought Cartoon Network in to co-produce alongside "
                "Sunrise and Bandai Visual, and its representatives asked "
                "that the story be finished within the season. %s to %s, "
                "numbered 14 to 26 because that is how the source numbers "
                "them." % (fmt_date(first[2]), fmt_date(last[2]))),
            "items": [
                {k: v for k, v in (
                    ("id", "bigo-%d" % num),
                    ("t", title),
                    ("n", str(num)),
                    ("note", ROW_NOTES.get(num)),
                ) if v is not None}
                for num, title, _d, _b in rows[n]
            ],
        })
    sections[0]["open"] = True

    total = sum(len(s["items"]) for s in sections)
    assert total == TOTAL_EPISODES, "%d rows, expected %d" % (total, TOTAL_EPISODES)
    assert sum(1 for s in sections for x in s["items"] if "w" in x) == 0, \
        "a weight crept in — this list is unweighted end to end"

    p = {
        "slug": SLUG,
        "title": "The Big O",
        "subtitle": "both seasons, all 26 episodes",
        "kind": "anime",
        "popularity": 48,
        "year": "1999–2003",
        "blurb": "Sunrise's film-noir mecha series in broadcast order — "
                 "thirteen episodes in 1999, thirteen more in 2003, and none "
                 "after that.",
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ["The second season exists because of how the first one did "
             "abroad.",
             "That is a fact about the production rather than the story, so "
             "each section's header names it. The series article's lead: "
             "\"Originally planned as a 26-episode series, low viewership in "
             "Japan reduced production to the first 13. Positive "
             "international reception resulted in a second season consisting "
             "of the remaining 13 episodes, co-produced by Cartoon Network, "
             "Sunrise, and Bandai Visual.\" The episode-list article says the "
             "same thing in its own words: \"Originally a 26-episode series, "
             "it was reduced to 13 episodes due to low ratings in Japan. "
             "However, positive international reception resulted in a second "
             "season co-produced by Cartoon Network, Sunrise, and Bandai "
             "Visual.\" Sunrise animated both; only the second had American "
             "money and an American broadcaster behind it."],
            ["Twenty-six between them, taken from the source rather than "
             "assumed.",
             "Thirteen and thirteen, counted three ways before this builds: "
             "the rows parsed out of each of the episode-list article's two "
             "season tables, the episodes field in each of the series "
             "article's two infoboxes, and the two prose sentences above. "
             "The overall numbering is asserted contiguous 1 to 26, and each "
             "season's first and last airdates are checked against its own "
             "infobox."],
            ["Rows are numbered 1 to 26 straight through.",
             "That is the source's numbering: the episode-list article files "
             "season 2 as episodes 14 to 26 rather than restarting at 1, and "
             "carries no in-season numbers at all. So the second section "
             "opens at 14."],
            ["One airdate disagrees with itself, and the episode table wins.",
             "The series article's second infobox closes season 2 on March "
             "23, 2003. The episode table dates the last episode March 27, "
             "2003, and the episode-list article's prose says the season "
             "\"concluded with 'The Show Must Go On' on March 27, 2003\". Two "
             "sources to one, and the table is the internally consistent one "
             "— the season ran weekly from Thursday January 2, and thirteen "
             "weekly slots land on March 27. This list follows the table, and "
             "fails the build if a third date ever appears."],
            ["This is all of it.",
             "There is no third season, and the source says why without "
             "anyone having to describe how the story ends: \"Along with the "
             "13 episodes of season two, Cartoon Network had an option for 26 "
             "additional episodes to be written by Konaka, but according to "
             "Jason DeMarco, executive producer for season two, the middling "
             "ratings and DVD sales in the United States and Japan made any "
             "further episodes impossible to be produced.\" The same section "
             "notes that Cartoon Network's representatives had asked for the "
             "story to be satisfactorily finished within the second season. "
             "So a continuation was optioned and never made, and 26 is the "
             "whole of it."],
            ["Nothing is weighted, and hours are not tracked on this list.",
             "Not for want of looking. Four sources were checked and all four "
             "came up empty. (1) Per-episode articles: none exist — all 26 "
             "titles were probed bare and in both disambiguated forms, and "
             "the handful of pages that answer are disambiguation pages and "
             "unrelated subjects, because six of the titles are common nouns. "
             "(2) Per-episode Wikidata: no episode items exist at all, so "
             "there is no P2047 to read; the series item carries neither a "
             "runtime nor any has-part statements. (3) Season articles: none "
             "exist — both season titles redirect to the episode-list "
             "article. (4) The episode table's own RunTime fields: not one of "
             "the 26 blocks has one, the series article's two infoboxes carry "
             "no runtime parameter, and the word \"minutes\" appears nowhere "
             "in the series, episode-list or music articles. It has to be "
             "every row or none, because a row with no weight silently counts "
             "as a full hour — weighting nothing keeps 26 half-hours from "
             "reading as 26 hours."],
            ["Everything else in the franchise is another medium.",
             "The six-volume manga, the two-volume Lost Memory, the Paradigm "
             "Noise novel, the drama CD and the Super Robot Wars appearances "
             "are not episodes and are not here. Neither are the Toonami, "
             "Adult Swim and Animax rebroadcasts, which are these same 26 "
             "episodes rather than more of them. There is no film and no OVA, "
             "and this list fails the build if the series article ever files "
             "a third anime installment."],
            "Titles, numbering and airdates machine-read from Wikipedia's "
            "\"List of The Big O episodes\"; production history, episode "
            "counts and broadcast dates cross-checked against \"The Big O\" "
            "and \"Music of The Big O\"; the runtime hunt run against "
            "Wikidata item Q974411 and the English Wikipedia article index.",
        ],
        "sections": sections,
    }

    check_not_syncable(p)
    out = prop.write(p)

    print("wrote %s — %d rows in %d sections, unweighted"
          % (out.name, total, len(sections)))
    if corrected:
        print("   correction: season 2's infobox closes %s; the episode table "
              "and the list article's prose both say %s, and the table wins"
              % (fmt_date(ib_s2_last), fmt_date(last[2])))
    print("   Cartoon Network optioned %d more episodes; none were made"
          % optioned)
    for n, s in zip(SEASONS, sections):
        print("   %-10s %2d rows  %s..%s  #%d–%d  %s"
              % (s["title"], len(s["items"]), fmt_date(first[n]),
                 fmt_date(last[n]), rows[n][0][0], rows[n][-1][0], s["sub"]))


if __name__ == "__main__":
    main()
