#!/usr/bin/env python3
"""Generate properties/sailor-moon.json — the 1990s run, in broadcast order.

    python3 tools/make_sailor-moon.py

Two hundred episodes across five seasons, with the three films, the two
theatrical shorts and the three television specials each sitting on the date
it went out. 208 rows, one section per season, nothing weighted.

SAILOR MOON CRYSTAL IS NOT HERE, AND THAT IS THE DECISION THIS LIST HAD TO
MAKE. Crystal (2014– ) is a second, independent adaptation of the same Naoko
Takeuchi manga — the Fullmetal Alchemist situation exactly, where
properties/fullmetal-alchemist.json and properties/fma-brotherhood.json are
two lists rather than one. The source settles it in its own words, in two
places, both asserted in main() before anything is written:

  * the Crystal article's lead — "Crystal serves as a reboot by faithfully
    adapting the original manga by omitting much of the original materials
    from the first anime series"; and
  * the 1992 series article's lead — "A new animated adaptation, Sailor Moon
    Crystal, which is a reboot series that more closely follows the manga,
    began airing worldwide in July 2014".

A reboot that omits this series' material is not more of this series, and
Wikipedia keeps the two apart structurally as well as in prose: this list's
source article opens with a hatnote sending "the 2014 web series episode
list" to a separate List of Sailor Moon Crystal episodes, which main() also
asserts. Sections on this page would have been wrong twice over — Crystal
re-tells the same arcs, so the same story would appear on one list twice, and
its 39 episodes are numbered Act 1 upward in a scheme of their own.

So Crystal, and its two-part films Sailor Moon Eternal (2021) and Sailor Moon
Cosmos (2023), belong on a list of their own, which is a separate card and is
NOT built here. The notes on this page name it and say why, and are written
so that adding the pointer — the "also on clubd" sentence
properties/fullmetal-alchemist.json carries towards Brotherhood — is one
edit to one note when that list exists.

THE FILMS AND SPECIALS ARE PLACED, NOT PARKED. Every one of the eight
non-episode entries is dated by the source into the middle of a season's own
run, so this list uses the babylon-5 method: a film that opened while a
season was on the air sits inside that season's rows at the point it opened,
not in a section of its own. In the source's OVERALL numbering: the R film
opened between episodes 76 and 77, the S film between 116 and 117, the SuperS
film on the same day episode 158 aired, and the three SuperS specials went out
on a single Sunday between episodes 131 and 132 — which is what the source
means when it says they aired "in lieu of a regular episode near the beginning
of the SuperS season". Nothing here is placed by hand: each entry is filed by
comparing its date against the season boundaries and then against the
episodes, and main() asserts that every one landed exactly once. The note on
the page describes the same four slots in the IN-SEASON numbers the rows
actually display, and placement_of() generates that sentence out of the
sequence it built, so the note cannot drift from where the rows ended up.

ROW NUMBERS ARE THE JAPANESE NUMBERS, AND THE ENGLISH DIFFERENCE IS A NOTE.
The 1990s English dub cut and merged episodes, and the source records it
precisely: the season 1 and R episode tables carry a column the table header
itself labels DiC, holding the dub's number for each episode, an em dash
where the dub dropped one, and 40a/40b for the two that became a single dub
episode. Read straight, that column says six episodes were never dubbed and
two became one — seven numbers lost out of the first 89 — and three separate
sentences in the source say the same thing independently: "DIC had mandated
cuts to content and length, which reduced the first 89 episodes by seven",
season one's "the season's 46 episodes were cut down to 40", and R's
"omitting only one of the season's 43 episodes". All three are asserted
against the column in scratch/agent-sailor/build_data.py. What this list will
NOT do is reconstruct a dub running order, because the source does not give
one: it gives numbers, and only for the first two seasons. So the rows are
numbered the Japanese way from end to end, and the eight affected rows carry
a note saying what the dub did to them.

NOTHING IS WEIGHTED, AND THE HUNT WAS EXHAUSTIVE. Five sources were checked
for a per-episode running time and four of them hold nothing at all:

  * the episode tables' own RunTime fields — not one of the 200 episode
    blocks, or the 3 special blocks, carries one;
  * the five season articles' infoboxes — every runtime field empty;
  * the series article's infobox — runtime empty;
  * an article per episode — there is none. Not one of the 200 Title cells is
    even a wikilink, and fetching all 200 titles as article names finds 143
    that do not exist, 36 redirects (24 of them back into the episode list),
    17 unrelated articles, and 4 titles that both exist and mention Sailor
    Moon — three disambiguation pages and a 1947 Joe McDoakes short whose
    article carries a hatnote pointing back at the episode list;
  * Wikidata — 135 items declare membership of this series, and exactly TEN
    of them carry a P2047. Ten runtimes out of two hundred episodes.

The films do publish runtimes (61, 61 and 62 minutes), and that is the trap
rather than the answer: an unweighted row resolves to one hour, so weighting
three films beside 200 unweighted episodes would have the strip claim each
half-hour episode takes sixty minutes. It is all rows or none, it is none,
main() asserts none, and the film runtimes ride in the row notes as text.

Everything is machine-read. scratch/agent-sailor/fetch.py primes the wikitext
cache 40 titles a request; scratch/agent-sailor/census.py runs the runtime
hunt above; scratch/agent-sailor/build_data.py parses the five season
articles, the list article, the series article and the three film articles
and writes the committed tools/data/sailor-moon.json, asserting as it goes
that each season's parsed count matches both the list article's series
overview and the season article's own infobox, that the in-season numbering
runs 1..N, that the overall numbering is contiguous 1..200, that airdates are
in broadcast order and match the infobox's first and last, and that the
series infobox still reads "200 + 3 TV specials".
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop  # noqa: E402

SLUG = "sailor-moon"
DATA = pathlib.Path(__file__).resolve().parent / "data" / "sailor-moon.json"

ACCENT = "#A81E5E"       # the deep rose of the first season's title card
ACCENT_DARK = "#F79FD4"  # ...lifted to moonlight pink for dark mode

ROWS = 208               # 200 episodes + 3 films + 2 shorts + 3 specials

MONTHS = ["", "January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

# Sort order within a date. Episodes come first because a broadcast happened
# on the day and a cinema programme opened on it; a short and its feature are
# one programme, and the order between those two rows is not a claim the
# source supports — see the note on the page.
KIND_ORDER = {"episode": 0, "film": 1, "short": 2, "special": 3}

# One sentence per season, saying what it adapts. Every fact inside them —
# thirteen chapters, the two R arcs, the Infinity and Dream arcs, the 6 + 28
# split of Sailor Stars — is read from the season articles by build_data.py
# and asserted there; these sentences are assembled from those values rather
# than restating them, which is why they interpolate.
INTRO = {
    1: "Where it starts. %(episodes)s episodes adapting the first "
       "%(chapters)s chapters of Naoko Takeuchi's manga.",
    2: "Two story arcs: the self-contained %(a0)s arc, which the manga does "
       "not have, and then the %(a1)s arc, adapting the %(v0)s through "
       "%(v1)s volumes. The first film opened in cinemas partway through the "
       "run and sits where it opened.",
    3: "Adapts the manga's %(arc)s arc. The second film opened in the middle "
       "of the season.",
    4: "Adapts the manga's %(arc)s arc. Three television specials went out "
       "together in place of an episode early on, and the third film opened "
       "near the end.",
    5: "The last season. Its first %(first)s episodes are a self-contained "
       "arc the manga does not have; the remaining %(rest)s adapt its "
       "%(arc)s arc. No 1990s English dub of this season was made, so its "
       "titles here are translations rather than dub titles.",
}

WORDS = {1: "one", 2: "two", 3: "three", 6: "six", 10: "ten", 13: "thirteen",
         28: "twenty-eight", 46: "forty-six"}


def word(n):
    """A count spelled out, for prose. Raises rather than falling back to a
    digit, so a source that changes one of these numbers stops the build
    instead of producing a sentence that starts with a numeral."""
    assert n in WORDS, "no word for %r — add it to WORDS" % n
    return WORDS[n]


def fmt_date(d):
    return "%s %d, %d" % (MONTHS[d[1]], d[2], d[0])


def english_list(bits, last="and"):
    bits = [str(b) for b in bits]
    if len(bits) == 1:
        return bits[0]
    return ", ".join(bits[:-1]) + " %s " % last + bits[-1]


def or_list(bits):
    return english_list(bits, "or")


def load():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    assert d["total_episodes"] == 200, d["total_episodes"]
    assert sum(d["overview_counts"].values()) == 200
    for n, rows in d["seasons"].items():
        assert len(rows) == d["overview_counts"][n] == \
            d["season_meta"][n]["episodes"], \
            "season %s disagrees with itself about its length" % n
    ov = sorted(r["o"] for rows in d["seasons"].values() for r in rows)
    assert ov == list(range(1, 201)), "overall numbering is not 1..200"
    assert not d["series"]["runtime"], \
        "the series now documents a runtime — revisit weights"
    return d


def entries(d):
    """Every non-episode row, as (date, kind, payload), before placement."""
    out = []
    for f in d["films"]:
        out.append((f["d"], "film", f))
    for s in d["shorts"]:
        out.append((s["d"], "short", s))
    for s in d["specials"]:
        out.append((s["d"], "special", s))
    assert len(out) == 8, len(out)
    return out


def merged_partners(d):
    """{overall: [in-season numbers of the episodes it merged with]}.

    Read out of the DiC column rather than named here: a cell like 40a says
    this episode is one half of dub episode 40, and the other halves are
    whatever else carries the same stem."""
    stems = {}
    for rows in d["seasons"].values():
        for r in rows:
            if r["dic"] and re.fullmatch(r"\d+[a-z]", r["dic"]):
                stems.setdefault(re.sub(r"[a-z]$", "", r["dic"]), []).append(r)
    out = {}
    for stem, group in stems.items():
        assert len(group) > 1, \
            "dub episode %s is lettered but has only one half" % stem
        for r in group:
            out[r["o"]] = [x["e"] for x in group if x["o"] != r["o"]]
    return out


def episode_note(r, merged):
    bits = []
    if r["o"] == 1:
        bits.append("Series premiere")
    # no "Series finale" on episode 200: the last row of the last season
    # already says it (CLU-123, CLU-557)
    if r["dic"] == "—":
        bits.append("Never dubbed into English at the time")
    if r["o"] in merged:
        others = english_list(["%d" % e for e in merged[r["o"]]])
        bits.append("The original English dub ran this and episode %s as a "
                    "single episode" % others)
    return prop.join_bits(*bits)


def placement_of(seq, label):
    """One phrase per date on which something other than an episode went out,
    written in the numbers the reader can see on the page.

    The rows show each episode's number INSIDE its season, so a note saying
    the first film opened "between 76 and 77" would be true of the source and
    invisible on the page. These phrases are generated from the sequence that
    was actually built, so they cannot drift from where the rows ended up."""
    out = []
    dates = sorted({tuple(dt) for dt, _o, k, _x in seq if k != "episode"})
    for dt in dates:
        here = [(k, x) for d2, _o, k, x in seq
                if tuple(d2) == dt and k != "episode"]
        same = [x for d2, _o, k, x in seq
                if tuple(d2) == dt and k == "episode"]
        before = [x for d2, _o, k, x in seq
                  if k == "episode" and tuple(d2) < dt]
        after = [x for d2, _o, k, x in seq
                 if k == "episode" and tuple(d2) > dt]
        if all(k == "special" for k, _x in here):
            subject = "the %s television specials" % word(len(here))
        else:
            subject = english_list([x["t"] for _k, x in here])
        if same:
            where = "on the day episode %d of %s aired" % (same[-1]["e"], label)
        else:
            assert before and after, \
                "%s sits outside the season's own run" % subject
            where = "between episodes %d and %d of %s" \
                    % (before[-1]["e"], after[0]["e"], label)
        out.append("%s %s" % (subject, where))
    return out


def build_sections(d):
    merged = merged_partners(d)
    pending = entries(d)
    sections, placed, places = [], [], []
    for n in range(1, 6):
        rows = d["seasons"][str(n)]
        meta = d["season_meta"][str(n)]
        head = d["headings"][str(n)]
        mine = [e for e in pending if meta["first"] <= e[0] <= meta["last"]]
        items, counts = [], {"episode": len(rows), "film": 0, "short": 0,
                             "special": 0}

        seq = [(r["d"], KIND_ORDER["episode"], "episode", r) for r in rows]
        for date, kind, payload in mine:
            seq.append((date, KIND_ORDER[kind], kind, payload))
            counts[kind] += 1
            placed.append((kind, payload))
        seq.sort(key=lambda x: (x[0], x[1]))

        for _date, _ord, kind, x in seq:
            if kind == "episode":
                item = {"id": "sm-%d" % x["o"], "t": x["t"], "n": str(x["e"])}
                note = episode_note(x, merged)
                if note:
                    item["note"] = note
            elif kind == "film":
                item = {
                    "id": "sm-film-%s" % prop.slug(x["t"].split(":")[0]),
                    "t": x["t"], "n": str(x["d"][0]), "q": x["q"],
                    "note": prop.join_bits("Feature film",
                                           "%d minutes" % x["runtime"],
                                           "released %s" % fmt_date(x["d"])),
                }
            elif kind == "short":
                item = {
                    "id": "sm-short-%s" % prop.slug(x["t"]),
                    "t": x["t"], "n": str(x["d"][0]),
                    "note": prop.join_bits(
                        "Theatrical short",
                        "screened with %s" % x["film"]),
                }
            else:
                item = {
                    "id": "sm-special-%d" % x["n"],
                    "t": x["t"], "n": str(x["d"][0]),
                    "note": prop.join_bits(
                        "Television special",
                        "one of three that went out together in place of an "
                        "episode"),
                }
            items.append(item)

        parts = ["%d episodes" % counts["episode"]]
        for kind, one, many in (("film", "film", "films"),
                                ("short", "short", "shorts"),
                                ("special", "special", "specials")):
            if counts[kind]:
                parts.append("%s %s" % (word(counts[kind]),
                                        one if counts[kind] == 1 else many))
        sec = {
            "id": "s%d" % n,
            "title": head["heading"],
            "sub": prop.join_bits(head["span"], english_list(parts)),
            "intro": season_intro(d, n),
            "items": items,
        }
        assert head["span"] == year_span(seq), \
            "season %d spans %s, the article's heading says %s" \
            % (n, year_span(seq), head["span"])
        sections.append(sec)
        places += placement_of(seq, head["heading"].split(": ")[-1])
        pending = [e for e in pending if e not in mine]

    assert not pending, \
        "%d entries fell outside every season: %s" \
        % (len(pending), [e[2].get("t") for e in pending])
    assert len(placed) == 8, "%d of 8 entries placed" % len(placed)
    assert len(places) == 4, \
        "expected four dates carrying something other than an episode, " \
        "got %d" % len(places)
    return sections, places


def year_span(seq):
    ys = [d[0] for d, _o, _k, _x in seq]
    a, b = min(ys), max(ys)
    return str(a) if a == b else "%d–%02d" % (a, b % 100)


def season_intro(d, n):
    a = d["arcs"][str(n)]
    if n == 1:
        return INTRO[1] % {"episodes": word(a["episodes"]).capitalize(),
                           "chapters": word(a["chapters"])}
    if n == 2:
        return INTRO[2] % {"a0": a["arcs"][0], "a1": a["arcs"][1],
                           "v0": a["volumes"][0], "v1": a["volumes"][1]}
    if n in (3, 4):
        return INTRO[n] % {"arc": a["arc"]}
    return INTRO[5] % {"first": word(a["split"][0]),
                       "rest": word(a["split"][1]), "arc": a["arc"]}


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


def sync_keys(sections):
    """The cross-list keys this property will contribute, computed the way
    src/build.py computes them, so they can be reported rather than guessed.

    This matters here because the kind string contains "film", which makes
    EVERY row on the list syncable — so an episode note carrying a lone year
    would quietly mint a film key. The assertion below is the guard."""
    keys = []
    for s in sections:
        for x in s["items"]:
            n = str(x.get("n", ""))
            if re.fullmatch(r"(18|19|20)\d{2}", n):
                y = n
            else:
                found = set(re.findall(r"\b((?:18|19|20)\d{2})\b",
                                       x.get("note") or ""))
                y = found.pop() if len(found) == 1 else None
            row = []
            if y:
                row.append(prop.normt(x["t"]) + "|" + y + "|f")
            if x.get("q"):
                row.append(x["q"] + "|f")
            if row:
                keys.append((x["id"], row))
    return keys


def main():
    d = load()
    check_accent()
    sections, places = build_sections(d)
    sections[0]["open"] = True

    total = sum(len(s["items"]) for s in sections)
    assert total == ROWS, "%d rows, expected %d" % (total, ROWS)
    eps = [x for s in sections for x in s["items"] if x["id"].startswith("sm-")
           and re.fullmatch(r"sm-\d+", x["id"])]
    assert len(eps) == 200, "%d episode rows" % len(eps)
    assert {x["id"] for x in eps} == {"sm-%d" % i for i in range(1, 201)}, \
        "the episode ids are not sm-1..sm-200"

    # all or nothing, and it is nothing (CLU-131)
    assert not any("w" in x for s in sections for x in s["items"]), \
        "a weight crept in — this list is unweighted end to end"

    # no episode row may leak a bare year into a note: the kind string carries
    # "film", so every row on this list is a sync candidate
    for x in eps:
        # (?<!\d)...(?!\d) is verbatim from build.py's _year_of. \b is
        # WEAKER and was the bug: no word boundary sits between the 0 and
        # the s of "1990s", so eight dub notes slipped past this guard and
        # did mint film sync keys.
        assert not re.search(r"(?<!\d)((?:18|19|20)\d{2})(?!\d)",
                             x.get("note") or ""), \
            "episode row %s leaks a year into its note: %r" \
            % (x["id"], x["note"])
        assert not re.fullmatch(r"(18|19|20)\d{2}", x["n"]), \
            "episode row %s is numbered with a year" % x["id"]

    keys = sync_keys(sections)
    assert len(keys) == 8, \
        "%d rows would mint a sync key, expected the 8 non-episode rows" \
        % len(keys)
    assert sum(1 for _i, ks in keys if len(ks) == 2) == 3, \
        "expected the three films to carry a Wikidata key as well as a " \
        "title+year one"

    # the eight rows the dub touched, and the sentence that counts them
    touched = [x for x in eps if "English" in (x.get("note") or "")]
    assert len(touched) == len(d["dub"]["cut"]) + len(d["dub"]["merged"]) == 8, \
        "%d rows carry a dub note, the source accounts for %d" \
        % (len(touched), len(d["dub"]["cut"]) + len(d["dub"]["merged"]))

    # the source's own "this article is not about…" hatnote, as prose
    others = english_list(["%s (%s)" % (s["article"].split(" (")[0], s["what"])
                           for s in d["siblings"]])

    # The runtime hunt's own numbers, so the note that describes it cannot
    # drift from what census.py actually found.
    cz = d["census"]
    rt = cz["wikidata_series_members_with_p2047"]
    n_rt = len(rt)
    rt_values = sorted(set(rt.values()))
    assert n_rt and n_rt * 4 < 200, \
        "%d of 200 episodes now carry a Wikidata duration — past a quarter " \
        "of the run the weights question is worth reopening" % n_rt
    assert cz["article_census"].get("own", 0) == 4 \
        and not cz["wikilinked_titles"], \
        "the per-episode article census has changed: %r" % cz["article_census"]

    p = {
        "slug": SLUG,
        "title": "Sailor Moon",
        "subtitle": "the 1990s anime, with the films and specials where they "
                    "went out",
        "kind": "anime & films",
        "popularity": 80,
        "year": "1992–1997",
        "blurb": "All 200 episodes of the original run — five seasons and "
                 "five years — with the three films, the two theatrical "
                 "shorts and the three specials each sitting on the date it "
                 "went out.",
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ["Sailor Moon Crystal is a different adaptation, and it is not on "
             "this list.",
             "Crystal (2014– ) is not more of this series; it is a second "
             "anime made from the same manga. Its own article says it "
             "\"serves as a reboot by faithfully adapting the original manga "
             "by omitting much of the original materials from the first anime "
             "series\", and this series' article says the same thing from the "
             "other side: \"A new animated adaptation, Sailor Moon Crystal, "
             "which is a reboot series that more closely follows the manga, "
             "began airing worldwide in July 2014.\" The source keeps them "
             "structurally apart as well — the episode list this page is "
             "built from opens by sending anyone after \"the 2014 web series "
             "episode list\" to a separate list of its own. So Crystal, and "
             "its films Sailor Moon Eternal and Sailor Moon Cosmos, belong on "
             "a page of their own rather than in sections here, where they "
             "would tell these same arcs a second time. This is the same call "
             "the catalogue already makes for Fullmetal Alchemist, which has "
             "two lists for two adaptations of one manga."],
            ["The films and specials sit on the dates they went out.",
             "All eight of them opened or aired while a season was still on "
             "the air, so none of them gets a section of its own. Working "
             "from the release dates the source gives: " + "; ".join(places)
             + ". The specials in particular are where the source puts them "
             "— it says they went out \"in lieu of a regular episode near the "
             "beginning of the SuperS season\", and the gap in that season's "
             "airdates is exactly where they land. Each film's row gives its "
             "runtime. A short and the feature it screened with were one "
             "cinema programme, so those two rows sit side by side; which of "
             "the pair you start with is not something the source settles."],
            ["The numbers are the Japanese numbers.",
             "The 1990s English dub cut six episodes and ran two more as one, "
             "which lost seven numbers out of the first 89 — the source puts "
             "it as \"DIC had mandated cuts to content and length, which "
             "reduced the first 89 episodes by seven\", and records the effect "
             "per episode in the tables themselves. From the third season the "
             "Canadian broadcaster renumbered to match the Japanese run, so "
             "dub numbers 83 to 89 were never used there, while the same "
             "episodes on Cartoon Network in the United States did use them "
             "and did not line up. None of that is a running order this list "
             "can rebuild, and the source does not give one, so every row "
             "here is numbered the Japanese way and the eight affected rows "
             "carry a note saying what the dub did to them."],
            ["Titles are the ones the source's table gives.",
             "That column is headed \"DiC title\" for the first two seasons "
             "and \"Cloverway title\" for the next two, with a translation of "
             "the Japanese title where an episode never got an English one. "
             "The fifth season has no English column at all, because the "
             "1990s dub stopped after four — \"The first four seasons were "
             "originally dubbed in English and released in North America by "
             "DIC Entertainment and Cloverway\" — so those 34 titles are "
             "translations throughout. The mix is the source's, not an "
             "editorial choice made here."],
            ["Nothing is weighted, and hours are not tracked on this list.",
             "Five places were checked for a per-episode running time. Not "
             "one of the 200 episode entries carries a runtime field; none of "
             "the five season articles has one; the series article has none; "
             "no episode has an article of its own, and none of the 200 "
             "title cells is even a link; and of the %d Wikidata items that "
             "declare themselves part of this series, exactly %s carry a "
             "duration — and those %s read %s minutes. %s out of two hundred "
             "cannot weight a list. The three films do publish runtimes, and "
             "weighting only them would be worse than weighting nothing: an "
             "unweighted row counts as a full hour, so two hundred episodes "
             "that the handful of measured durations put at %s minutes would "
             "read as two hundred hours. Every row counts one, and the films "
             "give their lengths in the row note instead."
             % (cz["distinct_series_members"], word(n_rt), word(n_rt),
                or_list(rt_values), word(n_rt).capitalize(),
                or_list(rt_values))],
            ["What else is not here.",
             "The source article for this list opens by naming everything it "
             "is not about, and that list is the exclusion list: " + others
             + ". Each is a separate production rather than a part of this "
             "run, and Crystal has a note of its own above. Naoko Takeuchi's "
             "manga is the work all of them adapt, and it is not tracked "
             "here either."],
            "Titles, numbering, airdates and the English dub's own numbering "
            "column machine-read from Wikipedia's five Sailor Moon season "
            "articles, the episode list, the series article and the three "
            "film articles, with runtimes and film identity from Wikidata; "
            "every season's count is checked against both the list article's "
            "series overview and the season article's infobox, and the "
            "overall numbering asserted contiguous 1 to 200, before this "
            "builds.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d rows in %d sections (%d episodes, %d films, "
          "%d shorts, %d specials)"
          % (out.name, total, len(sections), len(eps), len(d["films"]),
             len(d["shorts"]), len(d["specials"])))
    for s in sections:
        print("   %-24s %3d  %s" % (s["title"], len(s["items"]), s["sub"]))
    print("   runtime hunt: %d/200 episodes with a Wikidata duration, "
          "%d with an article of their own, %d table runtime fields"
          % (len(cz["wikidata_series_members_with_p2047"]), 0, 0))
    print("   sync keys:")
    for i, ks in keys:
        print("     %-34s %s" % (i, "  ".join(ks)))


if __name__ == "__main__":
    main()
