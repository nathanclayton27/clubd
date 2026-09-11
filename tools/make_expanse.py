#!/usr/bin/env python3
"""Generate properties/expanse.json — The Expanse, books and show in one order.

    PYTHONIOENCODING=utf-8 python tools/make_expanse.py

Two strands, one chronology, the Buffy & Angel treatment applied to a novel
series and its adaptation: the nine novels, the nine short works the series
article's own table numbers, and the six television seasons, every row placed
on the date it arrived — a book by its publication date, a season by its
premiere. Nothing is reordered to sit an adaptation next to what it adapts.

Rows are unweighted and count one apiece (CLU-222). Page counts and audiobook
lengths are published for the books; no per-episode runtime exists anywhere in
the sources this repo reads, the only figure the show publishes is a
series-level 42-63 minute range, and weights are all-or-nothing — a row
without one silently counts as an hour. A season and a novel are not the same
sitting in any case, so nothing here is weighted and the page counts live in
the row notes.

The spine Nathan asked for is the nine novels and the six seasons, so those
fifteen rows are required and the nine short works ride along as optional
ones. The rule for which short works: every entry the article's own table
numbers, 0.1 through 9.5 — seven novellas and two short stories, by that
table's own typography. Memory's Legion is not a row; it is those works in one
box, and the table gives it no number for that reason. The Last Flight of the
Cassandra is a row and is the awkward one: five pages, published only inside
the role-playing game's rulebook, the only short work with no audiobook.

Sources, all machine-read, nothing typed in by hand:
  * The Expanse (novel series) — the Novels and Short stories and novellas
    tables (number, title, pages, audio, publication date, setting), and the
    infobox's own list of the nine novels as a second check on the titles.
  * List of The Expanse episodes — the Series overview (episode counts,
    premiere and finale dates, networks), each season's own sentence saying
    what it adapts, and every episode block in all six seasons.
  * The Expanse (TV series) — the infobox's 6 seasons / 62 episodes / runtime
    range, the Syfy cancellation and Amazon pickup dates, and the Dragon Tooth
    comic continuation named in the not-here note.

The assertion that earns the list its one interesting note: each season's
final episode is named for the novel it lands on, and the sixth of those names
is the sixth of nine books. That is checked against the novels table every
run, so the day somebody films a seventh the build fails instead of quietly
leaving the note wrong.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki                                    # noqa: E402

SLUG = "expanse"
CACHE = prop.ROOT / "scratch" / SLUG

NOVELS_PAGE = "The Expanse (novel series)"
EPISODES_PAGE = "List of The Expanse episodes"
SHOW_PAGE = "The Expanse (TV series)"

NOVELS = 9
SHORTS = ["0.1", "0.5", "0.7", "1.5", "2.5", "3.5", "6.5", "7.5", "9.5"]
SEASONS = 6
EPISODES = 62
RPG_SHORT = "The Last Flight of the Cassandra"

# What each season adapts, in this list's words, with the terms each claim
# stands on. Every term is asserted against that season's own sentence on the
# episode-list article before the note is written.
ADAPTS = {
    1: ("Adapts the first half of Leviathan Wakes",
        ["first half", "Leviathan Wakes"]),
    2: ("Finishes Leviathan Wakes and opens Caliban's War, and adapts the "
        "short story Drive",
        ["Leviathan Wakes", "Caliban's War", "Drive"]),
    3: ("Finishes Caliban's War over six episodes, then Abaddon's Gate",
        ["Caliban's War", "Abaddon's Gate", "episodes 1–6"]),
    4: ("Almost all of Cibola Burn, with Gods of Risk behind episode 2",
        ["Cibola Burn", "Gods of Risk", "episode 2"]),
    5: ("Adapts Nemesis Games", ["Nemesis Games"]),
    6: ("The last season — Babylon's Ashes, with the short story "
        "Strange Dogs",
        ["final season", "Babylon's Ashes", "Strange Dogs"]),
}

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

CELL = re.compile(r"^[|!]\s*(?:([^|\[{]*=[^|\[{]*)\|)?\s*(.*)$", re.S)


def fetch(page):
    t = wiki.wikitext(page, cache_dir=str(CACHE))
    assert t, "could not read %s" % page
    return t.replace("’", "'")


def wikitable(text, header, ncols):
    """The rows of the first wikitable after `header`, rowspan carried down.

    Positional cell reading with no rowspan carry is the bug that silently
    staled a year column twice elsewhere in this repo, and the Setting column
    of the short-works table spans three rows.
    """
    i = text.index(header)
    seg = text[i:text.index("\n|}", i)]
    out, pending = [], {}
    for block in seg.split("\n|-")[1:]:
        lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
        raw = iter(l for l in lines if l[:1] in "|!")
        cols = []
        for c in range(ncols):
            if c in pending:
                cols.append(pending[c][1])
                pending[c][0] -= 1
                if not pending[c][0]:
                    del pending[c]
                continue
            m = CELL.match(next(raw, "|"))
            attrs, content = m.group(1) or "", m.group(2)
            cols.append(content)
            span = re.search(r"rowspan=\"?(\d+)", attrs)
            if span and int(span.group(1)) > 1:
                pending[c] = [int(span.group(1)) - 1, content]
        out.append(cols)
    assert not pending, "a rowspan ran off the end of %s" % header
    return out


def date(cell):
    """The {{dts|YYYY-MM-DD}} a publication-date cell carries."""
    m = re.search(r"dts\|(\d{4}-\d{2}-\d{2})", cell)
    assert m, "no dts date in %r" % cell[:60]
    return m.group(1)


def tdate(field):
    """{{Start date|Y|M|D}} / {{End date|Y|M|D}} as YYYY-MM-DD."""
    m = re.search(r"\{\{(?:start|end) date\|(\d+)\|(\d+)\|(\d+)", field, re.I)
    assert m, "no template date in %r" % field
    return "%04d-%02d-%02d" % tuple(int(x) for x in m.groups())


def longdate(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return "%s %d, %d" % (MONTHS[m - 1], d, y)


def monthyear(iso):
    y, m, _ = (int(x) for x in iso.split("-"))
    return "%s %d" % (MONTHS[m - 1], y)


def span(rows):
    ys = sorted({r["date"][:4] for r in rows})
    return ys[0] if ys[0] == ys[-1] else "%s–%s" % (ys[0], ys[-1])


# ---------------------------------------------------------------- the books
def books(text):
    """The nine novels and the nine short works, from their own two tables."""
    novels = []
    for cols in wikitable(text, "=== Novels ===", 6):
        no, title, pages, audio, pub = (wiki.clean(c) for c in cols[:5])
        novels.append({"no": int(no), "t": title, "pages": int(pages),
                       "audio": audio, "date": date(cols[4]), "kind": "novel"})
    assert [b["no"] for b in novels] == list(range(1, NOVELS + 1)), \
        "the novels table is not 1..%d contiguous" % NOVELS

    # the infobox's own list of the novels, as a second reading of the titles
    box = text[text.index("{{Infobox book series"):]
    listed = re.findall(r"\*\s*''\[\[([^\]|]+)\]\]\s*''\s*\((\d{4})\)",
                        box[:box.index("\n}}")])
    assert len(listed) == NOVELS, "infobox lists %d novels" % len(listed)
    for b, (name, year) in zip(novels, listed):
        assert b["t"] == name and b["date"][:4] == year, (b, name, year)

    titles = {b["t"] for b in novels}
    shorts, collection = [], None
    for cols in wikitable(text, "===Short stories and novellas===", 7):
        no, raw_t = wiki.clean(cols[0]), cols[1].strip()
        title, setting = wiki.clean(cols[1]).strip('"'), wiki.clean(cols[2])
        if not no:
            collection = title
            continue
        # the table's own typography: quoted is a short story, italic a novella
        quoted = raw_t.lstrip("|").strip().startswith('"')
        italic = raw_t.lstrip("|").strip().startswith("''")
        assert quoted != italic, "cannot tell what %r is" % title
        # every book a setting names has to be one of the nine
        named = [t for t in titles if t in setting]
        assert named, "setting %r names no novel" % setting
        assert re.fullmatch(r"(?:Before|During|Between|From before|After) .*",
                            setting), "unexpected setting %r" % setting
        shorts.append({"no": no, "t": title, "pages": int(wiki.clean(cols[3])),
                       "audio": wiki.clean(cols[4]), "date": date(cols[5]),
                       "kind": "story" if quoted else "novella",
                       "setting": setting})
    assert [s["no"] for s in shorts] == SHORTS, [s["no"] for s in shorts]
    assert sum(1 for s in shorts if s["kind"] == "story") == 2, \
        "the table's typography no longer splits 7 novellas and 2 stories"
    assert collection and "Memory's Legion" in collection, \
        "the unnumbered collection row is gone: %r" % collection

    # the RPG-exclusive short story: the one row with no audiobook, and the
    # only one whose publication cell names the rulebook it hides in
    for r in novels + shorts:
        assert bool(r["audio"]) == (r["t"] != RPG_SHORT), \
            "%s: audiobook column changed" % r["t"]
    rpg = next(s for s in shorts if s["t"] == RPG_SHORT)
    assert "Role-Playing Game" in text[text.index(RPG_SHORT):][:1200], \
        "the rulebook footnote on %s is gone" % RPG_SHORT
    assert rpg["pages"] == 5, rpg
    assert "except the RPG exclusive short story have been released as " \
           "audiobooks" in text, "the audiobook sentence changed"
    return novels, shorts


# ------------------------------------------------------------------ the show
def seasons(eps, show, novels):
    """The six seasons from the Series overview, checked episode by episode."""
    ov = eps[eps.index("{{Series overview"):eps.index("</onlyinclude>")]
    heads = [m.start() for m in re.finditer(r"^===\s*Season \d \(", eps, re.M)]
    heads.append(eps.index("==Webisodes=="))
    assert len(heads) == SEASONS + 1, "%d season headings" % (len(heads) - 1)

    out, network = [], None
    for n in range(1, SEASONS + 1):
        def field(key):
            m = re.search(r"\|\s*%s%d\s*=\s*(.*)" % (key, n), ov)
            return m.group(1).strip() if m else None

        count = int(field("episodes"))
        net, start, end = field("network"), field("start"), field("released")
        assert (start is None) != (end is None), \
            "season %d declares both a start and a release" % n
        first = tdate(start or end)
        last = tdate(field("end")) if field("end") else None
        # the overview declares a network only when it changes
        if net:
            network = wiki.clean(net)
        else:
            assert network, "season %d has no network to inherit" % n

        seg = eps[heads[n - 1]:heads[n]]
        sentence = wiki.clean(re.match(r"^===[^=]*===\n(.*)", seg).group(1))
        blocks = re.findall(r"\{\{Episode list(.*?)\n\s*\}\}", seg, re.S)
        assert len(blocks) == count, \
            "season %d: %d blocks, overview says %d" % (n, len(blocks), count)
        assert not re.search(r"RunTime", seg), \
            "season %d publishes episode runtimes now — weight this list" % n
        titles, airs = [], []
        for blk in blocks:
            titles.append(wiki.clean(
                re.search(r"\|\s*Title\s*=\s*(.*)", blk).group(1)))
            airs.append(tdate(re.search(
                r"\|\s*OriginalAirDate\s*=\s*(.*)", blk).group(1)))
        assert airs == sorted(airs), "season %d airs out of order" % n
        assert airs[0] == first, (n, airs[0], first)
        assert last is None or airs[-1] == last, (n, airs[-1], last)
        # the fact this list is built to say: the finale carries the book's name
        assert titles[-1] == novels[n - 1]["t"], \
            "season %d finale is %r, book %d is %r" \
            % (n, titles[-1], n, novels[n - 1]["t"])

        phrase, terms = ADAPTS[n]
        for term in terms:
            assert term in sentence, \
                "season %d sentence no longer says %r: %r" % (n, term, sentence)
        out.append({"no": n, "t": "The Expanse — Season %d" % n,
                    "date": first, "end": last, "episodes": count,
                    "network": network, "kind": "season", "adapts": phrase})

    assert sum(s["episodes"] for s in out) == EPISODES, "episode total moved"
    for key, want in (("num_seasons", str(SEASONS)),
                      ("num_episodes", str(EPISODES))):
        got = re.search(r"\|\s*%s\s*=\s*(\S+)" % key, show).group(1)
        assert got == want, "%s is %s, not %s" % (key, got, want)
    runtime = re.search(r"\|\s*runtime\s*=\s*(.*)", show).group(1).strip()
    assert re.fullmatch(r"\d+–\d+ minutes", runtime), \
        "the show publishes %r, not a range — weight this list" % runtime
    assert "On May 11, 2018, Syfy canceled the series after three seasons" \
           in eps, "the cancellation sentence changed"
    assert "on May 26, [[Amazon Video]] announced that it would produce a " \
           "fourth season" in eps, "the Amazon pickup sentence changed"
    assert len(re.findall(r"\{\{Episode list",
                          eps[eps.index("==Webisodes=="):])) == 5, \
        "the One Ship webisode count changed"
    return out, runtime


# ------------------------------------------------------------------- the rows
def row(r):
    if r["kind"] == "novel":
        return {"id": "ex-n%d-%s" % (r["no"], prop.slug(r["t"])), "t": r["t"],
                "n": monthyear(r["date"]),
                "note": prop.join_bits("Novel %d of %d" % (r["no"], NOVELS),
                                       "%d pages" % r["pages"])}
    if r["kind"] == "season":
        when = longdate(r["date"])
        if r["end"]:
            when = "%s to %s" % (when, longdate(r["end"]))
        else:
            when = "%s, released all at once" % when
        return {"id": "ex-tv%d" % r["no"], "t": r["t"],
                "n": monthyear(r["date"]),
                "note": prop.join_bits(
                    "%d episodes on %s" % (r["episodes"], r["network"]),
                    when, r["adapts"])}
    label = "Novella" if r["kind"] == "novella" else "Short story"
    extra = ("Published only inside The Expanse Role-Playing Game rulebook, "
             "and the one short work with no audiobook"
             if r["t"] == RPG_SHORT else None)
    return {"id": "ex-s%s-%s" % (r["no"].replace(".", "-"), prop.slug(r["t"])),
            "t": r["t"], "n": monthyear(r["date"]), "opt": 1,
            "note": prop.join_bits(
                label, "%d pages" % r["pages"],
                "set %s%s" % (r["setting"][0].lower(), r["setting"][1:]),
                extra)}


def main():
    novel_text = fetch(NOVELS_PAGE)
    episode_text = fetch(EPISODES_PAGE)
    show_text = fetch(SHOW_PAGE)

    novels, shorts = books(novel_text)
    tv, runtime = seasons(episode_text, show_text, novels)
    assert "final episode of each season sharing its name with the " \
           "respective book" in novel_text, "the naming claim is gone"
    tooth = wiki.clean(show_text[show_text.index("In January 2023"):][:400])
    for claim in ("Dragon Tooth", "12-issue comic book series",
                  "set between Babylon's Ashes and Persepolis Rising"):
        assert claim in tooth, "the not-here note lost %r: %r" % (claim, tooth)

    rows = sorted(novels + shorts + tv, key=lambda r: r["date"])
    dates = [r["date"] for r in rows]
    assert len(set(dates)) == len(dates), "two rows share a date — order them"
    first_tv, last_tv = tv[0]["date"], tv[-1]["date"]
    before = [r for r in rows if r["date"] < first_tv]
    both = [r for r in rows if first_tv <= r["date"] <= last_tv]
    after = [r for r in rows if r["date"] > last_tv]
    assert len(before) + len(both) + len(after) == len(rows)
    assert all(r["kind"] != "season" for r in before + after), \
        "the split put a season outside the years the show ran"
    assert len(both) == len(tv) + 7 and len(after) == 1, \
        "%d / %d rows either side" % (len(both), len(after))

    sections = [
        {"id": "before", "title": "Before the show",
         "sub": "%s · %d entries" % (span(before), len(before)),
         "intro": "Four and a half years of books, and nothing to watch yet.",
         "items": [row(r) for r in before], "open": True},
        {"id": "both", "title": "Both strands at once",
         "sub": "%s · %d entries" % (span(both), len(both)),
         "intro": "From the December 2015 premiere the books and the show run "
                  "side by side, and each row sits on the date it arrived — a "
                  "season on the day it started, a book on the day it was "
                  "published.",
         "items": [row(r) for r in both]},
        {"id": "after", "title": "After the show",
         "sub": "%s · %d entry" % (span(after), len(after)),
         "items": [row(r) for r in after]},
    ]

    p = {
        "slug": SLUG,
        "title": "The Expanse",
        "subtitle": "the novels and the seasons in one chronology",
        "kind": "books & tv",
        "popularity": 61,
        "year": "%s–%s" % (rows[0]["date"][:4], rows[-1]["date"][:4]),
        "blurb": "James S. A. Corey's nine novels, the nine short works and "
                 "the six television seasons in one order, by the date each "
                 "one arrived.",
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "read and watch", "past": "done",
                 "ing": "working through"},
        "accent": "#0F3A5C",
        "accentDark": "#FB7B0E",
        "tiers": False,
        "notes": [
            ["One list, two strands.",
             "The nine novels and the six seasons are the spine, ordered by "
             "the day each arrived: a book by its publication date, a season "
             "by its premiere. Nothing is moved to sit an adaptation next to "
             "the book it adapts, which is the whole point — the weave is "
             "what the order shows."],
            ["The show stops partway through the books.",
             "Six seasons were made and Amazon announced the sixth as the "
             "last. Each season's final episode is named for the novel it "
             "lands on, and the sixth of those names is Babylon's Ashes — "
             "book six of nine. Persepolis Rising, Tiamat's Wrath and "
             "Leviathan Falls have never been filmed, so the last three novel "
             "rows here say nothing beyond what they are. The authors have "
             "called season six a pause rather than a conclusion."],
            ["The short works are optional rows, and here is the rule.",
             "A short work is here if the series article's own table numbers "
             "it — nine of them, 0.1 through 9.5, which that table's "
             "typography splits into seven novellas and two short stories. "
             "Each row says where the source sets it, because publication "
             "order is not story order: Drive came out a year and a half "
             "after Leviathan Wakes and is set before it. Memory's Legion is "
             "not a row — it is those works in one box, and the table gives "
             "it no number for that reason. The Last Flight of the Cassandra "
             "is the awkward one and it is here anyway: five pages, published "
             "only inside the role-playing game's rulebook, the only short "
             "work with no audiobook. All nine are optional, so the list is "
             "finished without them."],
            ["It changed channels halfway.",
             "Syfy cancelled the show after three seasons on May 11, 2018, "
             "and Amazon announced a fourth on May 26, so the rows change "
             "network at season four and the release pattern changes with "
             "it. Nothing about the order changes."],
            ["Nothing is weighted, and this is what was checked.",
             "Rows count one apiece. The books publish pages and audiobook "
             "lengths, every one of them except the rulebook short story, and "
             "the show publishes nothing per episode: no episode block in any "
             "of the six seasons carries a running time, and the only figure "
             "the series states is a %s range for the whole run. Weights are "
             "all-or-nothing — a row without one silently counts as an hour — "
             "and a season and a novel are not the same sitting in any case, "
             "so the page counts sit in the row notes and the home page's "
             "hour bar leaves this list alone. The build re-reads every "
             "episode block each run and fails if runtimes start appearing."
             % runtime.replace(" minutes", "-minute")],
            ["Not here.",
             "The Dragon Tooth comics, twelve issues announced in January "
             "2023 and set between Babylon's Ashes and Persepolis Rising. The "
             "five One Ship webisodes that shipped alongside season six "
             "inside Prime Video's X-Ray menu. The board game, the "
             "role-playing game and the video games. This list is the prose "
             "and the show."],
            "Novels and short works — number, title, pages, audiobook length, "
            "publication date and the setting each one is filed under — "
            "machine-read from the two tables in Wikipedia's The Expanse "
            "(novel series), with the article's own infobox list of the nine "
            "novels read as a second check on the titles and years. Episode "
            "counts, premiere and finale dates, networks and the sentence "
            "saying what each season adapts from List of The Expanse "
            "episodes, every one cross-checked against that article's Series "
            "overview and against the show article's own 6 seasons and 62 "
            "episodes. Each season finale's title is asserted against the "
            "novel it shares a name with before this builds.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d rows in %d sections"
          % (out.name, len(rows), len(sections)))
    for s in sections:
        opt = sum(1 for x in s["items"] if x.get("opt"))
        print("   %-22s %2d row%s (%d optional)  %s"
              % (s["title"], len(s["items"]),
                 "" if len(s["items"]) == 1 else "s", opt, s["sub"]))
    print("   %d novels, %d short works, %d seasons, %d episodes behind them"
          % (len(novels), len(shorts), len(tv), EPISODES))


if __name__ == "__main__":
    main()
