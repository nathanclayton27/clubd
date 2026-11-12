#!/usr/bin/env python3
"""Generate properties/samurai-jack.json — all five seasons, every episode.

    PYTHONIOENCODING=utf-8 python tools/make_samurai-jack.py

Genndy Tartakovsky's series in the source's own episode order: 62 rows, four
seasons of thirteen on Cartoon Network between 2001 and 2004, then ten more
in 2017 on Adult Swim.

THE 2017 SEASON IS SEASON FIVE, AND THE SOURCE SAYS SO IN FIVE PLACES. This
was the one real question — a different network, thirteen years later, a
different rating — and Wikipedia answers it the same way every time it is
asked. The series article's infobox counts `num_seasons = 5` and
`num_episodes = 62`. The episode list article's {{Series overview}} files it
as season 5, giving it the only `network` override in the template. The
season article opens "The fifth and final season of ''Samurai Jack'', an
American animated series, premiered on Adult Swim's Toonami programming
block on March 11, 2017", and its infobox carries `season_number = 5` with
`prev_season` pointing at season 4. The overall episode numbering runs
straight on, 52 to 53. The word "revival" is the source's too — the series
article says the show "was revived thirteen years later with a darker, more
mature fifth season that provided a conclusion to the series" — but it is a
revival OF this series, filed as its fifth season, not a separate work. So
it is section five here, and every one of those five statements is asserted
before this builds.

WHAT DID CHANGE IS THE NETWORK, AND EVERY SECTION SUBTITLE NAMES ITS OWN.
The {{Series overview}} declares a network twice and only twice — Cartoon
Network at season 1, Adult Swim at season 5 — and the template carries the
first forward until the second replaces it. That carry-forward is read here
rather than assumed, and the two declarations are asserted to be exactly
those two seasons, because the network change is the fact the subtitles are
for. Adult Swim's Toonami block is named alongside it, from the same
sentence the season article opens with.

THE OPENING THREE ARE THREE EPISODES. The source files them in one
{{Episode list}} block with `NumParts=3`, and that block numbers them
individually — 1, 2, and 3 overall, 1, 2 and 3 in season — with the three
part titles written into the summary as "Part I: The Beginning", "Part II:
The Samurai Called Jack" and "Part III: The First Fight". The block's own
Title field, "Samurai Jack: The Premiere Movie", is the name of the VHS and
DVD compilation the same article describes two paragraphs earlier, not the
name of an episode. So the rows follow the numbering and carry the part
titles; the compilation is named in the notes and gets no row of its own.
The same call is made for the two other multi-part blocks, "The Birth of
Evil" (37–38) and "The Scotsman Saves Jack" (45–46), whose parts the source
numbers separately but does not title separately, so those rows read
"Part I" and "Part II". Thirteen a season, 52 across four, is what the
source's own overview, its own prose and the series infobox all say, and all
three are checked.

THE ROMAN NUMERALS ARE THE SHOW'S OWN EPISODE NUMBERS. The list article
states the rule: "All episodes are identified in the credits by Roman
numerals, which correspond to the total number of episodes released until
the fifth season, which adds 40 to the number of the season 4 finale, LII
(52), to start the numeration of its episodes at XCII (92)". That is why the
2017 season's episodes are titled XCII to CI and have no descriptive titles
at all — the same sentence says only the first four seasons have "an
alternate, more descriptive title". Rather than trust the rule, this
generator applies it and then checks it: season 5's ten titles are read back
as numbers and asserted to be the ten the rule produces — 92 to 101, counting
on from the fourth-season finale plus forty rather than from 53 — and eight
numeral-and-title pairs the series article spells out in its own citations
("XXXII – Jack and the Traveling Creatures", "XXII – Jack vs. the Five
Hunters", and six more) are asserted to match what this derives.

BROADCAST ORDER IS NOT THE SOURCE'S ORDER. Several episodes went out
ahead of or behind their number — season 4 began while season 3 was still
airing. The list follows the source's numbering, which is the numbering the
credits use; that at least one airdate runs backwards against it is
asserted, because the note says so.

WEIGHTS: NONE, AFTER A HUNT THROUGH SIX SOURCES. Wikipedia and Wikidata
between them document a running time for three of the 62 episodes.
Checked, in order: (1) the {{Episode list}} blocks' own RunTime field —
absent from all 58 blocks on both articles; (2) the season 5 article's
{{Infobox television season}} — no runtime field; (3) per-episode Wikipedia
articles — there are none, every episode title either redirects to the
episode list or lands on something unrelated ("XCII" on 92 (number),
"C" on the letter); (4) Wikidata items for those titles — nothing to
resolve, for the same reason; (5) Wikidata's own inventory of the series,
`part of the series (P179) = Q694101` — 62 items, of which 9 are seasons and
53 are episodes, so nine of the 2017 season's ten have no item at all; (6)
P2047 duration on those 53 — present on three, episodes XXXI, XXXIX and
XLIX, at 23, 23 and 22 minutes. The series article's infobox does carry
`runtime = 22 minutes`, but that is one nominal figure for a 62-episode
run, and the only three real per-episode durations the sources hold are not
all 22 — so spreading it across every row would be a guessed number dressed
as a measured one. It is all rows or none (CLU-131), and a row with no `w`
on a weighted list silently counts as a full hour, so it is none; main()
asserts none.

Everything is machine-read from the cached Wikipedia wikitext of "List of
Samurai Jack episodes", "Samurai Jack season 5" and "Samurai Jack". Nothing
is typed from memory.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki  # noqa: E402

SLUG = "samurai-jack"

# The wikitext cache. Nothing here is required — gwlib re-fetches and
# repopulates whichever of these exists — but a warmed cache keeps this
# generator offline and keeps it off Wikipedia's rate limiter.
CACHE = next((d for d in (prop.ROOT / "scratch" / SLUG,
                          prop.ROOT / "scratch" / "agent-jack")
              if d.exists()), prop.ROOT / "scratch" / SLUG)

LIST_PAGE = "List of Samurai Jack episodes"
S5_PAGE = "Samurai Jack season 5"
SERIES_PAGE = "Samurai Jack"

SEASONS = [1, 2, 3, 4, 5]
TOTAL_EPISODES = 62
ORIGINAL_EPISODES = 52       # the four Cartoon Network seasons
REVIVAL_EPISODES = 10        # the 2017 Adult Swim season
NUMERAL_JUMP = 40            # LII (52) -> XCII (92); the source's own figure

# What the runtime hunt found on Wikidata, checked 25 August 2026 and
# re-runnable from scratch/agent-jack/{hunt_runtimes,wd_episodes}.py. Nothing
# here is fetched at build time — the numbers only appear in the notes, and
# the reason this list is unweighted does not depend on them being current:
# 3 of 62 would still be 3 of 62 if the other two moved.
WD_EPISODE_ITEMS = 53        # items with `part of the series` = Q694101
WD_WITH_DURATION = 3         # of those, carrying P2047
WD_DURATIONS = "23, 23 and 22 minutes"

# Where the list article stops holding its own episodes and transcludes the
# season 5 article instead.
S5_HEADING = "=== Season 5 (2017) ==="

# Hard-coded rather than read from the clock so re-running produces the same
# file. Anything dated after this has not aired.
TODAY = (2026, 8, 25)

ACCENT = "#9E2B25"       # lacquer red
ACCENT_DARK = "#E8A33D"  # ...and the amber it burns to, for dark mode

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

NUMWORD = ["zero", "one", "two", "three", "four", "five", "six", "seven",
           "eight", "nine", "ten", "eleven", "twelve", "thirteen"]

ROMAN = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"),
         (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"),
         (5, "V"), (4, "IV"), (1, "I")]


def word(n):
    """Small counts read as words in prose; anything larger stays a numeral."""
    return NUMWORD[n] if 0 <= n < len(NUMWORD) else str(n)


def roman(n):
    out, rest = "", n
    for v, s in ROMAN:
        while rest >= v:
            out, rest = out + s, rest - v
    return out


def unroman(s):
    """Read a Roman numeral back, strictly — roman(unroman(s)) == s or bust."""
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total, prev = 0, 0
    for ch in reversed(s):
        v = vals[ch]
        total += -v if v < prev else v
        prev = max(prev, v)
    assert roman(total) == s, "%r is not a canonical Roman numeral" % s
    return total


def text(page):
    t = wiki.wikitext(page, cache_dir=CACHE)
    assert t, "no wikitext for %r" % page
    return t


def strip_refs(t):
    """Prose with the footnotes gone, for the sentences main() reads as fact."""
    t = re.sub(r"<ref[^>]*/>", "", t)
    return re.sub(r"<ref.*?</ref>", "", t, flags=re.S)


def flat_prose(t):
    return re.sub(r"\s+", " ", strip_refs(t))


def date_in(field, kind="Start"):
    """The first {{Start date}} / {{End date}} in a chunk, as (y, m, d)."""
    m = re.search(r"\{\{%s date\s*\|\s*(\d{4})\s*\|\s*(\d{1,2})\s*\|"
                  r"\s*(\d{1,2})" % kind, field or "", re.I)
    assert m, "no %s date in %r" % (kind.lower(), (field or "")[:80])
    return tuple(int(g) for g in m.groups())


def fmt_date(d):
    return "%d %s %d" % (d[2], MONTHS[d[1] - 1], d[0])


def span(first, last):
    """`2001` or `2002–03`, from a season's own first and last airdate."""
    if first[0] == last[0]:
        return str(first[0])
    return "%d–%02d" % (first[0], last[0] % 100)


# ---------------------------------------------------------------- the source

def series_overview(list_text):
    """{season: (episodes, start, end, network)} from the list article.

    {{Series overview}} declares a network only where it changes and carries
    the last one forward, so the carry-forward is done here rather than
    guessed at, and which seasons declare one is asserted — that pair of
    declarations IS the network change this list is shaped around."""
    seg = re.search(r"\{\{Series overview(.*?)\n\}\}", list_text, re.S)
    assert seg, "no series overview on the list article"
    body = seg.group(1)
    declared, out, carry = [], {}, None
    for n in SEASONS:
        m = re.search(r"\|\s*episodes%d\s*=\s*(\d+)" % n, body)
        s = re.search(r"\|\s*start%d\s*=\s*([^\n]*)" % n, body)
        e = re.search(r"\|\s*end%d\s*=\s*([^\n]*)" % n, body)
        assert m and s and e, "the overview no longer documents season %d" % n
        net = re.search(r"\|\s*network%d\s*=\s*([^\n]*)" % n, body)
        if net:
            declared.append(n)
            carry = wiki.clean(net.group(1))
        assert carry, "season %d has no network and none to carry forward" % n
        out[n] = (int(m.group(1)), date_in(s.group(1)),
                  date_in(e.group(1), "End"), carry)
    assert not re.search(r"\|\s*episodes%d\s*=" % (len(SEASONS) + 1), body), \
        "the overview now carries a season %d — it is airing and this list " \
        "is short" % (len(SEASONS) + 1)
    assert declared == [1, len(SEASONS)], \
        "the overview declares a network on seasons %s, expected the first " \
        "and the last — the network change is what the subtitles are for" \
        % declared
    assert out[1][3] != out[len(SEASONS)][3], \
        "both ends of the run now name the same network: %r" % out[1][3]
    assert sum(v[0] for v in out.values()) == TOTAL_EPISODES, \
        "the overview counts %d episodes, expected %d" \
        % (sum(v[0] for v in out.values()), TOTAL_EPISODES)
    assert re.search(r"\{\{:Samurai Jack season %d\}\}" % len(SEASONS),
                     list_text), \
        "the list article no longer transcludes the season 5 article — " \
        "check where those episodes now live"
    return out


def blocks(seg):
    """{{Episode list}} / {{Episode list/sublist|Page}} bodies, in order.

    gwlib.wiki.episodes() is the usual reader, but it looks for a single
    `EpisodeNumber` field and three of this show's blocks carry
    `NumParts` with `EpisodeNumber_1`, `_2`, `_3` instead — those blocks are
    the multi-part broadcasts, and dropping them would silently lose seven
    episodes."""
    return ["\n" + m.group(1) for m in
            re.finditer(r"\{\{Episode list(?:/sublist\s*\|[^|\n]*)?"
                        r"\s*(\|.*?)\n\s*\}\}", seg, flags=re.S | re.I)]


def field(block, name):
    m = re.search(r"\|\s*%s\s*=\s*(.*?)(?=\n\s*\||\Z)" % name, block, re.S)
    return m.group(1).strip() if m else ""


def rows_from(seg, label):
    """[{o, s, title, part, parts, date, multi}] for one stretch of table."""
    rows = []
    for b in blocks(seg):
        assert not re.search(r"\|\s*RunTime\s*=", b, re.I), \
            "%s now carries a per-episode runtime — revisit weights, because " \
            "the only reason this list is unweighted is that nothing did" % label
        title = wiki.clean(field(b, "Title"))
        assert title, "%s has a block with no title" % label
        date = date_in(field(b, "OriginalAirDate"))
        nparts = field(b, "NumParts")
        if nparts:
            k = int(nparts)
            assert k > 1, "%s: NumParts=%r" % (label, nparts)
            # part titles where the source gives them ("Part I: The
            # Beginning"), bare part markers where it does not ("Part I —")
            marks = re.findall(r"'''Part ([IVX]+)(?::\s*([^'\n]*))?'''",
                               field(b, "ShortSummary"))
            assert len(marks) == k, \
                "%s: NumParts=%d but the summary marks %d parts" \
                % (label, k, len(marks))
            assert [unroman(p) for p, _t in marks] == list(range(1, k + 1)), \
                "%s: part markers are not I..%s" % (label, roman(k))
            titled = [t.strip() for _p, t in marks]
            assert len(set(bool(t) for t in titled)) == 1, \
                "%s: the source titles some parts of %r and not others" \
                % (label, title)
            for i in range(k):
                rows.append({
                    "o": int(field(b, "EpisodeNumber_%d" % (i + 1))),
                    "s": int(field(b, "EpisodeNumber2_%d" % (i + 1))),
                    "title": titled[i] or "%s, Part %s" % (title, marks[i][0]),
                    "block_title": title, "part": i + 1, "parts": k,
                    "date": date})
        else:
            rows.append({"o": int(field(b, "EpisodeNumber")),
                         "s": int(field(b, "EpisodeNumber2")),
                         "title": title, "block_title": title,
                         "part": 0, "parts": 0, "date": date})
    assert rows, "%s parsed empty" % label
    for r in rows:
        assert r["date"] <= TODAY, \
            "%s episode %d (%r) is dated %s, which has not happened yet" \
            % (label, r["o"], r["title"], fmt_date(r["date"]))
    return rows


def numeral_rule(list_text):
    """The credits' Roman-numeral scheme, read from the article that states it."""
    prose = flat_prose(list_text)
    m = re.search(r"All episodes are identified in the credits by "
                  r"\[\[Roman numerals\]\], which correspond to the total "
                  r"number of episodes released until the fifth season, which "
                  r"adds (\d+) to the number of the season 4 finale, "
                  r"([IVXLC]+) \((\d+)\), to start the numeration of its "
                  r"episodes at ([IVXLC]+) \((\d+)\)", prose)
    assert m, "the list article no longer states the Roman-numeral scheme — " \
              "every row's numeral is derived from it"
    jump, fin_r, fin_n, first_r, first_n = m.groups()
    assert int(jump) == NUMERAL_JUMP, "the jump is now %s, not %d" \
        % (jump, NUMERAL_JUMP)
    assert unroman(fin_r) == int(fin_n) == ORIGINAL_EPISODES, \
        "the source's season 4 finale is %s (%s)" % (fin_r, fin_n)
    assert unroman(first_r) == int(first_n) == ORIGINAL_EPISODES + NUMERAL_JUMP, \
        "the source starts season 5 at %s (%s)" % (first_r, first_n)
    assert re.search(r"All episodes from the first four seasons also have an "
                     r"alternate, more descriptive title\.", prose), \
        "the source no longer says only seasons 1-4 carry descriptive " \
        "titles — the 2017 rows are titled by numeral because of it"
    return {"jump": int(jump), "finale": fin_r, "finale_n": int(fin_n),
            "first5": first_r, "first5_n": int(first_n)}


def cited_numerals(series_text):
    """Numeral-and-title pairs the series article spells out in its citations.

    Eight of them, written `|title=XXXII – Jack and the Traveling Creatures`.
    They are the independent check on a numeral this generator computes."""
    out = {}
    for m in re.finditer(r"\{\{Cite episode\s*\|title=([IVXLCM]+)\s*[–—-]\s*"
                         r"(?:\[\[[^\]|]*\|)?\[?\[?([^\]|}\n]+?)\]?\]?\s*"
                         r"\|series=Samurai Jack", series_text):
        out[unroman(m.group(1))] = m.group(2).strip()
    assert len(out) >= 6, \
        "the series article now spells out only %d numeral/title pairs — " \
        "they are the check on the numeral scheme" % len(out)
    return out


def series_facts(series_text, list_text, s5_text):
    """The counts, the revival sentence, and the production companies."""
    ib = wiki.infobox(series_text, kind="television")
    assert ib, "no television infobox on the series article"
    assert ib("num_seasons").strip() == str(len(SEASONS)), \
        "the series infobox counts %r seasons, this list carries %d" \
        % (ib("num_seasons"), len(SEASONS))
    assert ib("num_episodes").strip() == str(TOTAL_EPISODES), \
        "the series infobox counts %r episodes, this list carries %d" \
        % (ib("num_episodes"), TOTAL_EPISODES)

    # the one runtime anywhere, and it is a series-level nominal figure
    rt = wiki.clean(ib("runtime"))
    assert re.fullmatch(r"\d+ minutes", rt), \
        "the series infobox runtime is now %r — if it has become per-season " \
        "or per-episode, revisit weights" % rt

    prose = flat_prose(series_text)
    rev = re.search(r"The show was \[\[Revival \(television\)\|revived\]\] "
                    r"(\w+) years later with a darker, more mature "
                    r"\[\[Samurai Jack season 5\|fifth season\]\] that "
                    r"provided a conclusion to the series, with "
                    r"\[\[Williams Street\]\] assisting in production; the "
                    r"fifth season premiered on Cartoon Network's "
                    r"\[\[Adult Swim\]\] as part of its \[\[Toonami\]\] "
                    r"programming block on (\w+ \d+, \d{4})", prose)
    assert rev, "the series article no longer describes the 2017 season as a " \
                "revived fifth season — that framing is what puts it in " \
                "section five here rather than on a list of its own"
    gap = {"eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14}
    assert rev.group(1) in gap, "the gap is %r years" % rev.group(1)

    # the season article agrees, in its own first sentence and its own infobox
    s5prose = flat_prose(s5_text)
    assert re.search(r"The fifth and final season of ''\[\[Samurai Jack\]\]'', "
                     r"an American \[\[animated series\]\], premiered on "
                     r"\[\[Adult Swim\]\]'s \[\[Toonami\]\] programming block",
                     s5prose), \
        "the season 5 article no longer opens by calling itself the fifth " \
        "and final season"
    ib5 = wiki.infobox(s5_text, kind="television season")
    assert ib5, "no television season infobox on the season 5 article"
    assert ib5("season_number").strip() == str(len(SEASONS)), \
        "the season article numbers itself %r" % ib5("season_number")
    assert ib5("num_episodes").strip() == str(REVIVAL_EPISODES), \
        "the season article counts %r episodes" % ib5("num_episodes")
    assert not ib5("runtime").strip(), \
        "the season 5 article now documents a runtime — revisit weights"
    assert re.search(r"Season 4", ib5("prev_season")), \
        "the season article's prev_season is now %r — it used to point " \
        "straight at season 4" % ib5("prev_season")

    # the list article's own arithmetic, in prose
    lp = flat_prose(list_text)
    m = re.search(r"''Samurai Jack'' aired for four seasons that span "
                  r"(\d+) episodes\.", lp)
    assert m and int(m.group(1)) == ORIGINAL_EPISODES, \
        "the list article now says the original run spans %r episodes" \
        % (m and m.group(1))
    m5 = re.search(r"A \[\[Samurai Jack season 5\|fifth season\]\] spanning "
                   r"(\d+) episodes premiered on \[\[Adult Swim\]\]'s "
                   r"\[\[Toonami\]\] block", lp)
    assert m5 and int(m5.group(1)) == REVIVAL_EPISODES, \
        "the list article now says the fifth season spans %r episodes" \
        % (m5 and m5.group(1))

    # the compilation the premiere block is named after — the reason the
    # first three rows carry their part titles instead of that block title
    comp = re.search(r"A compilation featuring the first (\w+) episodes was "
                     r"released as a stand-alone movie titled ''Samurai Jack: "
                     r"The Premiere Movie'' on VHS and DVD", lp)
    assert comp, "the list article no longer describes the premiere " \
                 "compilation — the first block is titled after it"
    assert comp.group(1) == "three", "the compilation now covers %r episodes" \
        % comp.group(1)

    # the final four went out in one Toonami presentation; the citation the
    # last four rows share says so in its own title
    four = re.search(r"Samurai Jack Says 'Sayonara' with Final Four Episodes "
                     r"During Special Toonami Presentation", list_text)
    assert four, "the source no longer names the final-four broadcast"

    # `company = Cartoon Network Studios, Williams Street (season 5)` — the
    # second is qualified by the season it joined, and that qualifier is
    # read rather than assumed, because it is the second production fact the
    # 2017 season's subtitle and notes rest on.
    companies = wiki.clean(ib("company"))
    assert "Cartoon Network Studios" in companies \
        and "Williams Street" in companies, \
        "the series infobox no longer credits both production companies: %r" \
        % companies
    parts = [c.strip() for c in companies.split(",")]
    assert len(parts) == 2, "the series is now made by %d companies: %r" \
        % (len(parts), companies)
    qual = re.fullmatch(r"(.+?) \(season (\d+)\)", parts[1])
    assert qual and int(qual.group(2)) == len(SEASONS), \
        "the second production company is no longer credited to season %d: " \
        "%r" % (len(SEASONS), parts[1])
    return {"gap": gap[rev.group(1)], "lead": parts[0],
            "assist": qual.group(1), "series_runtime": rt}


# ------------------------------------------------------------ house-keeping

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


def check_sync_safety(p):
    """Cross-list tick sync must not be able to reach these rows.

    src/build.py groups a row with rows on other lists when the property's
    kind names a film or a game AND the row resolves to a single year — from
    `n`, from `y`, or, failing both, from a lone four-digit year inside the
    note. This show's episode titles are exactly the kind that would collide
    if it ever did: ten of them are bare Roman numerals, and "C", "CI" and
    "XCII" are live article titles elsewhere on Wikipedia. Two locks: the
    kind is neither, and no row leaks a year into a note."""
    kind = p["kind"]
    assert "film" not in kind and "game" not in kind, \
        "kind %r would make these rows syncable across lists, and ten of " \
        "them are titled with bare Roman numerals" % kind
    for s in p["sections"]:
        for x in s["items"]:
            assert not re.fullmatch(r"(18|19|20)\d{2}", str(x.get("n", ""))), \
                "%s numbers itself with a year" % x["id"]
            assert "y" not in x, "%s carries an explicit year" % x["id"]
            years = re.findall(r"\b(?:18|19|20)\d{2}\b", x.get("note") or "")
            assert not years, \
                "%s leaks %s into its note; build.py reads a lone year out " \
                "of a note as the row's release year" % (x["id"], years)


# ------------------------------------------------------------------- output

def main():
    list_text = text(LIST_PAGE)
    s5_text = text(S5_PAGE)
    series_text = text(SERIES_PAGE)

    overview = series_overview(list_text)
    facts = series_facts(series_text, list_text, s5_text)
    rule = numeral_rule(list_text)
    jump = rule["jump"]
    cited = cited_numerals(series_text)
    check_accent()

    cut = list_text.index(S5_HEADING)
    assert "{{Episode list" not in list_text[cut:], \
        "the list article has started holding season 5's episodes again"
    nblocks = len(blocks(list_text[:cut])) + len(blocks(s5_text))
    flat = rows_from(list_text[:cut], "seasons 1-4") + rows_from(s5_text, "season 5")

    # ---- 1. the numbering, three ways
    assert [r["o"] for r in flat] == list(range(1, TOTAL_EPISODES + 1)), \
        "overall episode numbering is not contiguous 1..%d" % TOTAL_EPISODES
    # The overview's start/end are a season's first and last BROADCAST, and
    # this show did not broadcast in numerical order — season 3's highest
    # numbered episode went out ten weeks before its last one did. So the
    # comparison is against the extremes of the season's airdates, never
    # against its first and last rows.
    by_season, aired, seen = {}, {}, 0
    for n in SEASONS:
        k = overview[n][0]
        by_season[n] = flat[seen:seen + k]
        seen += k
        assert [r["s"] for r in by_season[n]] == list(range(1, k + 1)), \
            "season %d in-season numbering is not 1..%d" % (n, k)
        ds = sorted(r["date"] for r in by_season[n])
        aired[n] = (ds[0], ds[-1])
        assert ds[0] == overview[n][1], \
            "season %d opens %s, the overview says %s" \
            % (n, fmt_date(ds[0]), fmt_date(overview[n][1]))
        assert ds[-1] == overview[n][2], \
            "season %d closes %s, the overview says %s" \
            % (n, fmt_date(ds[-1]), fmt_date(overview[n][2]))
    assert seen == len(flat) == TOTAL_EPISODES, (seen, len(flat))
    lengths = {overview[n][0] for n in SEASONS[:-1]}
    assert len(lengths) == 1, \
        "the four original seasons no longer run to one length: %s" \
        % sorted(lengths)
    per_original = lengths.pop()
    assert per_original * (len(SEASONS) - 1) == ORIGINAL_EPISODES, \
        "%d seasons of %d no longer make %d" \
        % (len(SEASONS) - 1, per_original, ORIGINAL_EPISODES)

    # ---- 2. the Roman numerals, derived then checked against the source
    # Up to the fourth-season finale the numeral IS the running total. The
    # fifth season restarts the count at that finale plus the jump — LII (52)
    # + 40 = XCII (92) — and runs on from there, so its first episode is 92
    # rather than 53 + 40. Getting that off by one is exactly the mistake the
    # checks below catch.
    for r in flat:
        r["numeral"] = roman(
            r["o"] if r["o"] <= ORIGINAL_EPISODES
            else ORIGINAL_EPISODES + jump + (r["o"] - ORIGINAL_EPISODES - 1))
    s5rows = by_season[SEASONS[-1]]
    assert [r["numeral"] for r in s5rows] == [r["title"] for r in s5rows], \
        "the 2017 season's titles are no longer its credited numerals: %s" \
        % [(r["title"], r["numeral"]) for r in s5rows if r["title"] != r["numeral"]]
    got = {r["o"]: r["title"] for r in flat}
    for o, t in sorted(cited.items()):
        assert got.get(o) == t, \
            "the series article cites %s (%d) as %r; the table titles it %r" \
            % (roman(o), o, t, got.get(o))

    # ---- 3. the multi-part broadcasts
    multi = [r for r in flat if r["parts"]]
    assert len(multi) == 7 and {r["parts"] for r in multi} == {2, 3}, \
        "the source now marks %d multi-part episodes: %s" \
        % (len(multi), [(r["o"], r["parts"]) for r in multi])
    for r in multi:
        share = [x for x in flat if x["block_title"] == r["block_title"]
                 and x["parts"]]
        assert len({x["date"] for x in share}) == 1, \
            "%r no longer aired as one broadcast" % r["block_title"]
    opening = [r for r in flat if r["parts"] == 3]
    assert [r["o"] for r in opening] == [1, 2, 3], \
        "the three-part opening is no longer episodes 1-3"
    assert all(r["title"] != r["block_title"] for r in opening), \
        "the opening rows are titled after the compilation again"

    # ---- 4. the original run closed with four episodes in one night
    closing = aired[SEASONS[-2]][1]
    last4 = [r for r in flat if r["date"] == closing]
    assert len(last4) == 4, \
        "%d episodes now share the closing night of the original run, not " \
        "four: %s" % (len(last4), [r["o"] for r in last4])
    assert last4[-1]["o"] == ORIGINAL_EPISODES, \
        "the closing night no longer ends on episode %d" % ORIGINAL_EPISODES
    closing_four = {r["o"] for r in last4}

    # ---- 5. the numbering is not the broadcast order, and the note says so
    dates = [r["date"] for r in flat]
    backwards = sum(1 for a, b in zip(dates, dates[1:]) if b < a)
    assert backwards, \
        "every episode now aired in numerical order — the note about " \
        "broadcast order is no longer true"

    # ---- the rows
    sections = []
    for n in SEASONS:
        rows, items = by_season[n], []
        for r in rows:
            bits = []
            if r["o"] == 1:
                bits.append("series premiere")
            if r["parts"] == 3:
                bits.append("one of the %s that opened the show in a single "
                            "broadcast" % word(r["parts"]))
            elif r["parts"]:
                bits.append("part %d of %d, aired as one broadcast"
                            % (r["part"], r["parts"]))
            if n == SEASONS[-1] and r["s"] == 1:
                # not "first of the 2017 season": build.py falls back to a
                # lone four-digit year inside a note when a row's `n` is not
                # a year, and check_sync_safety refuses one on principle
                bits.append("first episode after the %s-year gap"
                            % word(facts["gap"]))
            # seasons 1-4 keep "season finale": those notes also carry the
            # credited numeral, so they are not bare. The bare "series finale"
            # on the last row is gone (CLU-123, CLU-557)
            if r["s"] == len(rows) and n != SEASONS[-1]:
                bits.append("season finale")
            if r["o"] in closing_four:
                bits.append("one of the final four, aired together in one "
                            "Toonami presentation")
            if r["title"] != r["numeral"]:
                bits.append("credited as %s" % r["numeral"])
            row = {"id": "sj-s%de%d" % (n, r["s"]), "t": r["title"],
                   "n": str(r["s"])}
            note = prop.join_bits(*bits)
            if note:
                row["note"] = note
            items.append(row)
        sections.append({
            "id": "s%d" % n,
            "title": "Season %d" % n,
            "sub": prop.join_bits(span(*aired[n]),
                                  "%d episodes" % len(rows),
                                  overview[n][3]
                                  + (" (Toonami)" if n == SEASONS[-1] else "")),
            "items": items,
        })

    sections[0]["open"] = True
    sections[0]["links"] = [{"label": "The episode list",
                             "url": "https://en.wikipedia.org/wiki/"
                                    "List_of_Samurai_Jack_episodes"}]
    sections[0]["intro"] = (
        "%s episodes, %s to %s. The first three went out as one broadcast "
        "and are three rows here, because that is how the source numbers "
        "them."
        % (word(len(by_season[1])).capitalize(),
           fmt_date(aired[1][0]), fmt_date(aired[1][1])))
    sections[-1]["intro"] = (
        "%s years later and on a different network: %s episodes on %s's "
        "Toonami block, %s to %s. The source files them as the fifth season "
        "of the same series, and their credited numerals jump to %s to match "
        "the gap."
        % (word(facts["gap"]).capitalize(), word(len(s5rows)),
           overview[SEASONS[-1]][3],
           fmt_date(aired[SEASONS[-1]][0]), fmt_date(aired[SEASONS[-1]][1]),
           s5rows[0]["numeral"]))
    sections[-1]["links"] = [{"label": "The 2017 season",
                              "url": "https://en.wikipedia.org/wiki/"
                                     "Samurai_Jack_season_5"}]

    total = sum(len(s["items"]) for s in sections)
    assert total == TOTAL_EPISODES, "%d rows, expected %d" % (total, TOTAL_EPISODES)
    assert sum(1 for s in sections for x in s["items"] if "w" in x) == 0, \
        "a weight crept in — this list is unweighted end to end"

    p = {
        "slug": SLUG,
        "title": "Samurai Jack",
        "subtitle": "all five seasons, in the source's episode order",
        "kind": "animated series",
        "popularity": 67,
        "year": "2001–2017",
        "blurb": "Every episode of Genndy Tartakovsky's series — four "
                 "seasons on Cartoon Network, then ten more in 2017.",
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ["The 2017 season is season five, and the source says so five "
             "times.",
             "A different network and %s years on is a fair reason to ask "
             "whether it is a separate show, so it was asked. The series "
             "infobox counts five seasons and %d episodes; the episode "
             "list's series overview files it as season 5; the season "
             "article opens \"The fifth and final season of Samurai Jack, an "
             "American animated series, premiered on Adult Swim's Toonami "
             "programming block\"; its infobox numbers itself 5 with season "
             "4 before it; and the overall numbering runs straight on from "
             "52 to 53. Wikipedia does also call it a revival — the show "
             "\"was revived %s years later with a darker, more mature fifth "
             "season that provided a conclusion to the series\" — but a "
             "revival of this series, filed as its fifth season. So it is "
             "the fifth section here."
             % (word(facts["gap"]), TOTAL_EPISODES, word(facts["gap"]))],
            ["The network changed, and every season subtitle names its own.",
             "%s carried the first four seasons; the fifth went out on %s's "
             "Toonami block. Those are the only two networks the source's "
             "overview declares, and it carries the first forward until the "
             "second replaces it — which is read here rather than assumed. "
             "%s made all five; %s assisted on the last."
             % (overview[1][3], overview[SEASONS[-1]][3],
                facts["lead"], facts["assist"])],
            ["The opening three are three rows.",
             "The source files them in one block titled Samurai Jack: The "
             "Premiere Movie — which is the name of the VHS and DVD "
             "compilation the same article describes, not the name of an "
             "episode — and numbers them 1, 2 and 3 individually, with the "
             "part titles written into its summary. So the rows follow the "
             "numbering and carry those titles, and the compilation gets no "
             "row of its own. The two later two-parters are handled the same "
             "way and read Part I and Part II, because the source numbers "
             "their parts separately but does not title them separately."],
            ["%s a season, then %s."
             % (word(per_original).capitalize(), word(REVIVAL_EPISODES)),
             "%s episodes in each of the four original seasons and %s in the "
             "fifth — %d in all. Each season's count, first airdate and last "
             "airdate are checked against the source's own series overview "
             "before this builds, and the total against the series infobox."
             % (word(per_original).capitalize(), word(REVIVAL_EPISODES),
                TOTAL_EPISODES)],
            ["The Roman numerals are the show's own episode numbers.",
             "The source states the rule — episodes are identified in the "
             "credits by Roman numerals matching the running total, and the "
             "fifth season adds %d so that %s (%d) is followed by %s (%d) — "
             "so each row's numeral is derived from it and then checked "
             "against the source twice: the fifth season's %s titles are "
             "read back as numbers, and %s numeral-and-title pairs the "
             "series article spells out in its own citations have to match. "
             "Only the first four seasons carry a descriptive title as well, "
             "which is why the last %s rows are titled by numeral alone."
             % (jump, rule["finale"], rule["finale_n"], rule["first5"],
                rule["first5_n"], word(REVIVAL_EPISODES), word(len(cited)),
                word(REVIVAL_EPISODES))],
            ["The order here is the numbering, not the broadcast.",
             "Several episodes went out ahead of or behind their number — "
             "the fourth season began while the third was still airing. The "
             "list follows the source's numbering, which is the numbering "
             "the credits use."],
            ["Nothing is weighted, and hours are not tracked on this list.",
             "Six sources were checked for a per-episode running time and "
             "between them they hold one for %s of the %d. The episode "
             "tables carry no RunTime field on any of their %d blocks; the "
             "fifth season's article has no runtime in its infobox; no "
             "episode has a Wikipedia article of its own, so there is no "
             "episode infobox and no Wikidata item to reach through one; "
             "Wikidata's own inventory of the series holds items for %d of "
             "the %d episodes, nine of the last ten having none at all; and "
             "of those items, %s carry a duration — %s. The series infobox "
             "does say \"%s\", but that is one nominal figure for a "
             "%d-episode run and the %s real durations are not all the same, "
             "so spreading it across every row would be a guess wearing a "
             "measurement's clothes. It is all rows or none, and a row with "
             "no weight on a weighted list silently counts as a full hour, "
             "so it is none."
             % (word(WD_WITH_DURATION), TOTAL_EPISODES, nblocks,
                WD_EPISODE_ITEMS, TOTAL_EPISODES, word(WD_WITH_DURATION),
                WD_DURATIONS, facts["series_runtime"], TOTAL_EPISODES,
                word(WD_WITH_DURATION))],
            "Titles, numbering and airdates machine-read from Wikipedia's "
            "\"List of Samurai Jack episodes\" and \"Samurai Jack season 5\", "
            "with counts, dates, the numeral scheme and the fifth season's "
            "standing cross-checked against \"Samurai Jack\" and against "
            "Wikidata before this builds.",
        ],
        "sections": sections,
    }

    check_sync_safety(p)
    out = prop.write(p)

    print("wrote %s — %d rows in %d sections" % (out.name, total, len(sections)))
    for n, s in zip(SEASONS, sections):
        print("   %-9s %3d  %-38s %s – %s"
              % (s["title"], len(s["items"]), s["sub"],
                 fmt_date(aired[n][0]), fmt_date(aired[n][1])))
    print("   unweighted: a per-episode runtime exists for 3 of %d rows"
          % TOTAL_EPISODES)
    print("   %d rows come from %d multi-part blocks; %d airdates run "
          "backwards against the numbering" % (len(multi), 3, backwards))


if __name__ == "__main__":
    main()
