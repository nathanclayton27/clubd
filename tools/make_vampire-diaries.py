#!/usr/bin/env python3
"""Generate properties/vampire-diaries.json — the CW series, 2009-2017.

    PYTHONIOENCODING=utf-8 python tools/make_vampire-diaries.py
    PYTHONIOENCODING=utf-8 python tools/make_vampire-diaries.py --refetch [cache-dir]

One row per episode, 171 rows covering all 171 episodes across eight
seasons, in broadcast order. No entry in the eight season tables spans two
episode numbers, so rows and episodes are the same number here — unlike The
X-Files, whose season nine finale is one row spanning 19-20.

Deliberately excluded, and named in the property notes: The Originals
(2013-2018), the spin-off this show's fourth season launches; Legacies
(2018-2022), which the show article calls a spin-off of The Originals rather
than of this show, and which a hidden editor note on that article says the CW
is explicit about; and Forever Yours, the retrospective the list page files
under "Special", which aired the same night as the finale and is not one of
the 171 numbered episodes.

WHERE THE FACTS COME FROM. `--refetch` machine-reads the eight "The Vampire
Diaries season N" articles plus "List of The Vampire Diaries episodes" and
"The Vampire Diaries", and rewrites tools/data/vampire-diaries-episodes.json.
Given a directory it caches wikitext there; given nothing it fetches live.
It reads the {{Episode list}} blocks with its own brace-counting reader
rather than gwlib.wiki.episodes(), whose terminator is the first line-initial
`}}` and which reads only the first number of a paired EpisodeNumber. This
one reads *every* number in a numbering field, and reads the split
`NumParts` fields beside it, so a row that spans two episodes raises rather
than shipping as one — the shape gwlib silently halves. It asserts the two
readers agree on overall number, in-season number, title and year, that
every season's in-season numbering is contiguous 1..N and equal to the list
page's own Series overview count, that the overall numbering is contiguous
1..171, and that every framing sentence a row note is built from is still on
the page.

A normal run touches no network. It reads the committed data file and
re-asserts the numbering and the counts, ties each row note to the row the
numbering says should carry it, and re-ties the footer's "aired the same
night as the finale" to the two dates the data file actually holds. Reader
agreement and the framing sentences are asserted where they are read, inside
`--refetch`, and cannot be re-checked from the data file.

FOUR ROW NOTES, AND NO FIFTH. The premiere, the backdoor pilot, the 100th,
and the crossover — each one a fact the section header does not carry. There
is deliberately **no "Series finale"** on the last row: CLU-123 ruled a bare
finale note on the last row of a section already titled "Season 8" pointless
and commit 4ef1b1d deleted ten of them, so this generator never emits one and
build() asserts the last row stays noteless. A last-row note is legal only
when it carries something the header cannot — frasier's "aired as one
hour-long episode", childs-play's "cancelled after three seasons" — and the
data file states nothing of the kind for this row. The crossover note quotes
the other show's episode title, per the adjudicated corpus in
tools/spoilerscan.py and buffy-angel's `Angel's "I Will Remember You"`.

NOTHING IS WEIGHTED, and that is a decision rather than an omission. No
season table publishes a runtime column — `--refetch` asserts that, so it is
a machine-read fact and not an impression — and the only runtime any source
states is a single "41-49 minutes" range for the whole series in the show
article's infobox. A labelled estimate would be legal (CLU-222), but the
episode lists here that do carry weights carry stated ones: Black Mirror
takes a published runtime from each episode's own article, Columbo a Runtime
column from the season tables. This list follows the long-run network shows
that have no such figure — The X-Files, Buffy, Frasier, M*A*S*H, Bob's
Burgers, Futurama — and stays unweighted rather than being the one show whose
hours are invented. Because an unweighted row silently counts as one hour
beside a weighted one (CLU-131), the choice is all or nothing: every row here
counts one, and the strip divides evenly across 171 marks.

POPULARITY 61 — a network hit that ran eight seasons and 171 episodes on The
CW and anchored a three-show universe, so it sits above its CW peer Gossip
Girl (57) and above Friday Night Lights (56); but it is genre television
whose name travels thinly outside the people who watch it, so it sits below
Buffy & Angel (68), Gilmore Girls (65) and Battlestar Galactica (62). It is
the flagship of its universe and the only list from it in the catalogue.
"""
import datetime
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki

SLUG = "vampire-diaries"
IDP = "tvd"
SEASONS = 8
TOTAL = 171

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "data" / ("%s-episodes.json" % SLUG)

LIST_PAGE = "List of The Vampire Diaries episodes"
SHOW_PAGE = "The Vampire Diaries"
SEASON_PAGE = "The Vampire Diaries season %d"

# Not machine-read: an editorial palette choice, and the only hand-picked
# input in this build. The show's own eight line colours are all within 5.2
# CIE76 of an accent already shipped — season one's #6C1F1F is 0.5 from The
# Sopranos' #6B1F1F — so none of them can be lifted, and this is a deep
# crimson in the same family instead. Measured against the 210 accent pairs
# shipped when it was picked, with
#     PYTHONIOENCODING=utf-8 python scratch/nolan/accent.py '#7E1440' '#EE9BB4'
# the nearest neighbours are #8C2A46 (rurouni-kenshin, 7.9) and #8A2E4A
# (nasuverse, 8.2) on the light side, #FF9DAF (scream, 8.0) and #E9A8C6
# (gossip-girl, 8.8) on the dark. That is clear of them, not far from them.
ACCENT, ACCENT_DARK = "#7E1440", "#EE9BB4"


# --------------------------------------------------------------------------
# the machine-read step: --refetch
# --------------------------------------------------------------------------

EPLIST = re.compile(r"\{\{\s*(?:#invoke:)?Episode list\b", re.I)


def blocks(text):
    """Every {{Episode list}} block, delimited by counting braces.

    gwlib.wiki.episodes() closes a block at the first line-initial `}}`, so a
    field holding a multi-line template ends it early and silently drops
    every field after it. Counting braces cannot do that.
    """
    out = []
    for m in EPLIST.finditer(text):
        i, depth = m.start(), 0
        while i < len(text):
            if text.startswith("{{", i):
                depth += 1
                i += 2
            elif text.startswith("}}", i):
                depth -= 1
                i += 2
                if depth == 0:
                    break
            else:
                i += 1
        assert depth == 0, "unbalanced Episode list block at offset %d" % m.start()
        out.append(text[m.start():i])
    return out


def bfield(block, name):
    """A named field of a block, to the next line-initial pipe or the end.

    The leading newline in the pattern matters: without it, Title also
    matches inside the block's own first line, and EpisodeNumber
    prefix-matches EpisodeNumber2, so the name is anchored and terminated
    explicitly.
    """
    m = re.search(r"\n\s*\|\s*%s\s*=\s*(.*?)(?=\n\s*\||\Z)" % name, block, re.S)
    return m.group(1).strip() if m else ""


def num(v):
    m = re.search(r"\d+", v or "")
    return int(m.group(0)) if m else None


def nums(v):
    """Every number in a numbering field, in order, refs and markup removed.

    A row covering two episodes writes both numbers into one field —
    `19<br />20` — and reading only the first is how such a row ships as a
    single episode with half its numbering. wiki.clean() first, so a
    footnote (`19<ref name="s2"/>`) cannot donate a digit.
    """
    return [int(x) for x in re.findall(r"\d+", wiki.clean(v or ""))]


def airdate(v):
    m = re.search(r"\{\{\s*[Ss]tart date\s*\|\s*(\d{4})\s*\|\s*(\d{1,2})"
                  r"\s*\|\s*(\d{1,2})", v or "")
    assert m, "no {{Start date}} in %r" % (v or "")[:80]
    return "%04d-%02d-%02d" % tuple(int(g) for g in m.groups())


def onlyinclude(text, page):
    m = re.findall(r"<onlyinclude>(.*?)</onlyinclude>", text, re.S)
    assert m, "no <onlyinclude> on %r" % page
    return "\n".join(m)


def refetch(cache=None):
    """Re-derive tools/data/vampire-diaries-episodes.json from Wikipedia."""
    def page(name):
        t = wiki.wikitext(name, cache_dir=cache)
        assert t, "no wikitext for %r" % name
        return t

    listtext, showtext = page(LIST_PAGE), page(SHOW_PAGE)

    # --- what the list page and the show article state -------------------
    overview = {int(m.group(1)): int(m.group(2))
                for m in re.finditer(r"\|\s*episodes(\d+)\s*=\s*(\d+)", listtext)}
    assert sorted(overview) == list(range(1, SEASONS + 1)), overview
    assert sum(overview.values()) == TOTAL, (overview, sum(overview.values()))

    years = {int(m.group(1)): m.group(2) for m in
             re.finditer(r"===\s*Season (\d+)\s*\(([^)]+)\)\s*===", listtext)}
    assert sorted(years) == list(range(1, SEASONS + 1)), years

    # the Series overview's own colour per season, kept beside the season
    # articles' LineColor so the one place they disagree is on the record
    ovcolors = {int(m.group(1)): "#" + m.group(2).upper() for m in
                re.finditer(r"\|\s*color(\d+)\s*=\s*#?([0-9A-Fa-f]{6})\b", listtext)}
    assert sorted(ovcolors) == list(range(1, SEASONS + 1)), ovcolors

    inf = wiki.infobox(showtext, kind=r"television")
    assert inf, "no television infobox on the show article"
    assert num(wiki.clean(inf("num_episodes"))) == TOTAL, wiki.clean(inf("num_episodes"))
    assert num(wiki.clean(inf("num_seasons"))) == SEASONS, wiki.clean(inf("num_seasons"))
    runtime = wiki.clean(inf("runtime"))
    network = wiki.clean(inf("network"))
    assert network == "The CW", network
    assert re.match(r"^\d+\s*[–-]\s*\d+ minutes$", runtime), runtime

    prose = wiki.clean(showtext)
    m = re.search(r"premiered on the CW on ([A-Z][a-z]+ \d{1,2}, \d{4}), and "
                  r"concluded on ([A-Z][a-z]+ \d{1,2}, \d{4}), having aired "
                  r"(\d+) episodes over (\w+) seasons", prose)
    assert m, "the show article's run sentence moved"
    assert int(m.group(3)) == TOTAL, m.group(3)
    premiere, finale = m.group(1), m.group(2)

    # --- the eight season articles ---------------------------------------
    seasons, seen_overall, linecolors, raws = {}, [], {}, {}
    for n in range(1, SEASONS + 1):
        raw = raws[n] = page(SEASON_PAGE % n)
        seg = onlyinclude(raw, SEASON_PAGE % n)
        bs = blocks(seg)

        # cross-check the brace reader against gwlib's, block for block
        theirs = wiki.episodes(seg)
        assert len(theirs) == len(bs), (n, len(theirs), len(bs))

        # nothing here publishes a per-episode runtime; the unweighted
        # decision rests on that, so it is asserted rather than assumed
        assert not re.search(r"\|\s*[A-Za-z0-9_]*[Rr]un ?[Tt]ime[A-Za-z0-9_]*\s*=",
                             raw), (n, "a runtime column appeared — see the docstring")

        rows = []
        for b, (t_overall, t_inseason, t_title, t_year, _) in zip(bs, theirs):
            # {{Episode list}} writes a two-episode row one of two ways: both
            # numbers in one field, or NumParts with the plain fields absent
            # and `_1`/`_2` suffixes carrying the halves (make_the_office.py
            # branches on the same field). Read both shapes; neither may
            # appear here, and the assert below is what says so.
            if bfield(b, "NumParts"):
                o_list = (nums(bfield(b, "EpisodeNumber_1"))
                          + nums(bfield(b, "EpisodeNumber_2")))
                e_list = (nums(bfield(b, "EpisodeNumber2_1"))
                          + nums(bfield(b, "EpisodeNumber2_2")))
            else:
                o_list = nums(bfield(b, "EpisodeNumber"))
                e_list = nums(bfield(b, "EpisodeNumber2"))
            title = wiki.clean(bfield(b, "Title")).strip('"')
            assert o_list and e_list, (n, title, "unnumbered row")
            assert title, (n, o_list, "empty title")
            assert len(o_list) == 1 and len(e_list) == 1, \
                (n, title, "row spans two numbers", o_list, e_list)
            overall, e = o_list[0], e_list[0]
            # the span's END, which the assert above has just proved equals
            # its start. The data file keeps it so build() can refuse a
            # hand-edited row that recorded a span after all.
            e2 = e_list[-1]
            d = airdate(bfield(b, "OriginalAirDate"))
            assert (t_overall, t_inseason, t_title, t_year) == \
                (overall, e, title, int(d[:4])), \
                ("reader disagreement", n, (t_overall, t_inseason, t_title, t_year),
                 (overall, e, title, int(d[:4])))
            row = {"e": e, "e2": e2, "overall": overall, "t": title,
                   "y": int(d[:4]), "d": d}
            if re.search(r"crossover", b, re.I):
                ct = wiki.clean(b)
                mm = re.search(r"crossover with ([^.,]+?) that concludes on "
                               r"\"([^\"]+)\"", ct, re.I)
                if mm:
                    row["xover"] = mm.group(1).strip().rstrip('"')
                    row["xover_ends"] = mm.group(2).strip()
                else:
                    mm = re.search(r"[^.]*crossover with ([^.,]+)", ct, re.I)
                    assert mm, (n, title, "crossover phrase unreadable")
                    row["xover"] = mm.group(1).strip().rstrip('"')
            rows.append(row)
            seen_overall.append(overall)

        # season eight writes its LineColor with a leading '#', the others do not
        lc = {m.group(1) for m in
              re.finditer(r"\|\s*LineColor\s*=\s*#?([0-9A-Fa-f]{6})\b", seg)}
        assert len(lc) == 1, (n, lc)
        linecolors[str(n)] = "#" + lc.pop().upper()

        inseason = [r["e"] for r in rows]
        assert inseason == list(range(1, len(inseason) + 1)), (n, inseason[:8])
        assert len(inseason) == overview[n], (n, len(inseason), overview[n])
        assert [r["d"] for r in rows] == sorted(r["d"] for r in rows), \
            (n, "air dates out of order")
        seasons[str(n)] = rows

    assert seen_overall == list(range(1, TOTAL + 1)), "overall numbering desynced"

    # --- the framing behind each row note --------------------------------
    flat = [r for k in sorted(seasons, key=int) for r in seasons[k]]
    titles = {r["t"] for r in flat}
    assert flat[0]["t"] == "Pilot", flat[0]["t"]
    assert flat[0]["d"] == "2009-09-10" and premiere == "September 10, 2009"
    assert flat[-1]["d"] == "2017-03-10" and finale == "March 10, 2017"
    assert flat[-1]["e"] == 16 and flat[-1]["overall"] == TOTAL, flat[-1]

    # the backdoor pilot: stated in the season four article's prose
    s4 = wiki.clean(raws[4])
    bd = re.search(r"back-?door pilot focused on the Originals, titled "
                   r"(?:''\[\[)?([^\]'|]+?)(?:\]\]'')?, would air on "
                   r"([A-Z][a-z]+ \d{1,2})", s4, re.I)
    assert bd, "the season four backdoor-pilot sentence moved"
    bd_row = next(r for r in flat if r["t"] == bd.group(1).strip()
                  and r["overall"] == 86)
    assert bd_row["e"] == 20 and bd_row["d"] == "2013-04-25", bd_row
    assert re.search(r"The Originals, The Vampire Diaries' spin-off series, had "
                     r"been picked up for a full season", s4), \
        "the season four pick-up sentence moved"
    bd_row["bdpilot"] = bd.group(1).strip()
    assert sum(1 for r in flat if r.get("bdpilot")) == 1
    assert re.search(r"fourth season consisted of 23 episodes instead of the "
                     r"usual 22 episodes", s4), "the 23-episode line moved"
    assert re.search(r"renewed for an eighth and final season by The CW",
                     wiki.clean(raws[8])), "the final-season sentence moved"

    # the hundredth: computed from the overall numbering AND named in the prose
    ep100 = next(r for r in flat if r["overall"] == 100)
    assert re.search(r"the series' 100th episode \"%s\"" % re.escape(ep100["t"]),
                     prose), "the 100th-episode sentence moved"
    ep100["milestone"] = "100th episode"

    # the crossover, and the episode of the other show it finishes on
    xs = [r for r in flat if r.get("xover")]
    assert len(xs) == 1, xs
    assert xs[0]["overall"] == 147 and xs[0]["e"] == 14, xs[0]
    assert xs[0]["xover"] == "The Originals", xs[0]["xover"]
    assert xs[0]["xover_ends"] and xs[0]["xover_ends"] not in titles, \
        ("the concluding episode belongs to the other show", xs[0])

    # --- the retrospective special, which is not one of the 171 ----------
    i, j = listtext.index("==Special=="), listtext.index("==Ratings==")
    sb = blocks(listtext[i:j])
    assert len(sb) == 1, len(sb)
    sp_title = wiki.clean(bfield(sb[0], "Title")).strip('"')
    sp_date = airdate(bfield(sb[0], "OriginalAirDate"))
    assert sp_title and sp_date == "2017-03-10", (sp_title, sp_date)
    assert re.search(r"Retrospective of the series", bfield(sb[0], "ShortSummary")), \
        "the special's framing moved"

    # --- the spin-offs, and which show each one spun off from ------------
    so = re.search(r"The television series The Originals \((\d{4}[^)]*)\).*?"
                   r"followed by a spin-?off of The Originals entitled "
                   r"Legacies \((\d{4}[^)]*)\)", prose, re.S)
    assert so, "the spin-off sentence moved"
    spinoffs = [{"t": "The Originals", "years": so.group(1).replace("-", "–"),
                 "of": SHOW_PAGE},
                {"t": "Legacies", "years": so.group(2).replace("-", "–"),
                 "of": "The Originals"}]
    # `so` is what asserts the parentage: the sentence it matches is the one
    # calling Legacies a spin-off OF The Originals, and the article carries a
    # hidden editor note saying the CW is explicit about it. The property's
    # note says it that way rather than flattening both into spin-offs of
    # this show.
    for s in spinoffs:
        assert re.match(r"^\d{4}–\d{4}$", s["years"]), s

    out = {
        "source": {
            "list": LIST_PAGE, "show": SHOW_PAGE,
            "seasons": [SEASON_PAGE % n for n in range(1, SEASONS + 1)],
            # which day these articles were read, so a later re-verification
            # knows what it is comparing against rather than assuming today's
            # revisions. Precedent: tools/data/king.json, a24.json, gundam.json.
            "fetched": datetime.date.today().isoformat(),
        },
        "years": {str(k): years[k] for k in sorted(years)},
        "stated": {"total": TOTAL, "seasons": SEASONS,
                   "per_season": {str(k): overview[k] for k in sorted(overview)},
                   "network": network, "runtime": runtime,
                   "per_episode_runtime_published": False,
                   "premiere": premiere, "finale": finale},
        "linecolors": {
            "season_pages": linecolors,
            "list_page": {str(k): ovcolors[k] for k in sorted(ovcolors)},
            "disagree": [str(k) for k in sorted(ovcolors)
                         if ovcolors[k] != linecolors[str(k)]],
        },
        "spinoffs": spinoffs,
        "skipped": [{"kind": "special", "t": sp_title, "d": sp_date,
                     "why": "a retrospective, outside the %d numbered episodes"
                            % TOTAL}],
        "seasons": seasons,
    }
    DATA.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")
    print("refetched %s — %d rows covering %d episodes"
          % (DATA.name, len(flat), len(seen_overall)))
    print("   runtime %r  network %r  run %s .. %s"
          % (runtime, network, premiere, finale))
    print("   line colours disagreeing with the list page: %s"
          % (out["linecolors"]["disagree"] or "none"))
    for r in flat:
        flags = {k: r[k] for k in ("bdpilot", "milestone", "xover", "xover_ends")
                 if k in r}
        if flags:
            print("   #%-3d %-34s %s" % (r["overall"], r["t"][:34], flags))


# --------------------------------------------------------------------------
# the build
# --------------------------------------------------------------------------

def shipped_ids():
    """Item ids in the property as it stands on disk, so the write can prove
    it renamed none of them. Empty on a first build."""
    p = prop.ROOT / "properties" / ("%s.json" % SLUG)
    if not p.exists():
        return set()
    old = json.loads(p.read_text(encoding="utf-8"))
    return {x["id"] for s in old.get("sections", []) for x in s["items"]}


def build():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    stated = data["stated"]
    assert stated["total"] == TOTAL, stated["total"]
    assert stated["seasons"] == SEASONS, stated["seasons"]
    assert stated["network"] == "The CW", stated["network"]
    assert stated["per_episode_runtime_published"] is False, stated
    assert len(data["seasons"]) == SEASONS, len(data["seasons"])
    assert sum(stated["per_season"].values()) == TOTAL, stated["per_season"]

    sections, overall = [], []
    for n in range(1, SEASONS + 1):
        rows = data["seasons"][str(n)]
        # 1..N with no gaps, so a desynced data file fails here rather than
        # shipping a season quietly missing an episode
        inseason = [r["e"] for r in rows]
        assert inseason == list(range(1, len(inseason) + 1)), (n, inseason[:8])
        assert len(inseason) == stated["per_season"][str(n)], \
            (n, len(inseason), stated["per_season"][str(n)])

        items = []
        for r in rows:
            assert r["e"] == r["e2"], (n, r)   # no double-length broadcast here
            overall.append(r["overall"])
            bits = []
            if n == 1 and r["e"] == 1:
                bits.append("Series premiere")
            if r.get("bdpilot"):
                bits.append("A backdoor pilot for the spin-off series %s"
                            % r["bdpilot"])
            if r.get("milestone"):
                bits.append("The series' %s" % r["milestone"])
            if r.get("xover"):
                # One sentence, one bit: join_bits separates independent
                # pieces, and "concludes on…" is a dependent clause of the
                # half before it. The other show's episode title is QUOTED —
                # the adjudicated corpus (tools/spoilerscan.py, item 1) says
                # an unquoted title is indistinguishable from a description,
                # and this one is also a famous play. The house precedent is
                # buffy-angel's `Angel's "I Will Remember You"`. No airdate
                # claim: The Originals' schedule is not read here.
                if r.get("xover_ends"):
                    bits.append("Begins a crossover with the spin-off %s that "
                                "concludes on its episode \"%s\", not listed here"
                                % (r["xover"], r["xover_ends"]))
                else:
                    bits.append("Begins a crossover with the spin-off %s"
                                % r["xover"])
            # NO "Series finale" HERE, deliberately. CLU-123, adjudicated:
            # a bare finale note on the last row of a section already titled
            # "Season 8" carries nothing the header and the position do not,
            # and commit 4ef1b1d deleted ten of them. A last-row note is only
            # worth writing if it carries a fact the header cannot — "aired as
            # one hour-long episode", "cancelled after three seasons" — and
            # the data file states none for this row.
            item = {"id": "%s-s%de%d" % (IDP, n, r["e"]), "t": r["t"],
                    "n": str(r["e"])}
            note = prop.join_bits(*bits)
            if note:
                item["note"] = note
            items.append(item)

        sec = {"id": "s%d" % n, "title": "Season %d" % n,
               "sub": "%s · %d episodes" % (data["years"][str(n)], len(items)),
               "items": items}
        if n == 1:
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == TOTAL, len(ids)
    assert overall == list(range(1, TOTAL + 1)), "overall numbering desynced"
    assert sections[0]["items"][0]["t"] == "Pilot", sections[0]["items"][0]
    assert sections[-1]["items"][-1]["t"] == "I Was Feeling Epic", \
        sections[-1]["items"][-1]
    # four: the premiere, the backdoor pilot, the 100th, the crossover
    assert sum(1 for s in sections for x in s["items"] if x.get("note")) == 4
    assert not sections[-1]["items"][-1].get("note"), \
        ("the last row carries a note again — CLU-123 says it must carry a "
         "fact the header does not", sections[-1]["items"][-1])

    # Every note lands where the numbering says it should, not merely on a row
    # that happens to carry the flag. The sentences behind these are asserted
    # in --refetch, where the pages are; this is the half that can be
    # re-checked from the data file.
    flat = [(n, r) for n in range(1, SEASONS + 1) for r in data["seasons"][str(n)]]
    titles = {r["t"] for _, r in flat}

    def only(key):
        hits = [(n, r) for n, r in flat if r.get(key)]
        assert len(hits) == 1, (key, hits)
        return hits[0]

    sn, bd = only("bdpilot")              # season four, and the row that aired it
    assert (sn, bd["e"], bd["overall"]) == (4, 20, 86), bd
    sn, mile = only("milestone")
    assert mile["milestone"] == "100th episode" and mile["overall"] == 100, mile
    assert flat[99][1] is mile, "the 100th-episode note is not on the 100th row"
    sn, xo = only("xover")
    assert (sn, xo["e"], xo["overall"]) == (7, 14, 147), xo
    assert xo["xover_ends"] not in titles, \
        ("the concluding episode belongs to the other show", xo)

    spin = data["spinoffs"]
    assert [s["t"] for s in spin] == ["The Originals", "Legacies"], spin
    assert spin[0]["of"] == "The Vampire Diaries", spin[0]
    assert spin[1]["of"] == spin[0]["t"], spin[1]   # Legacies spun off The Originals
    special = data["skipped"][0]
    assert special["kind"] == "special", special
    # the footer says the retrospective "aired the same night as the finale";
    # tie that to the data file rather than leaving it asserted only in
    # --refetch, where it was checked against a hardcoded date
    assert special["d"] == flat[-1][1]["d"], (special, flat[-1])

    # "41–49 minutes" reads as a range, not as a compound adjective
    rt = stated["runtime"].replace(" minutes", " minute")
    assert rt != stated["runtime"], stated["runtime"]

    year = "%d–%d" % (flat[0][1]["y"], flat[-1][1]["y"])

    p = {
        "slug": SLUG,
        "title": "The Vampire Diaries",
        "subtitle": "eight seasons on The CW",
        "kind": "tv",
        "popularity": 61,
        "year": year,
        "blurb": "All %d episodes of the CW series in broadcast order, "
                 "from the pilot to the finale." % TOTAL,
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ["The show itself, and nothing spun off it.", "%s (%s) and its "
             "own spin-off %s (%s) have their own runs; neither is listed "
             "here." % (spin[0]["t"], spin[0]["years"],
                        spin[1]["t"], spin[1]["years"])],
            ["The retrospective is not an episode.", "%s aired the same night "
             "as the finale and the episode list files it under Special, "
             "outside the %d numbered episodes." % (special["t"], TOTAL)],
            # Only what was actually machine-read: --refetch asserts no
            # season article carries a runtime field, and the range is the
            # show article's infobox. The old wording also claimed every
            # episode "fills the same network hour", which nothing here read.
            ["Nothing is weighted.", "The season articles publish no "
             "per-episode runtime, and the only figure any of these sources "
             "gives is a %s range for the whole series, so every row counts "
             "one and none is guessed." % rt],
            "Episode titles and airdates machine-read from the eight Wikipedia "
            "season articles; every season's numbering is asserted contiguous "
            "and equal to the episode list's own counts, and the overall "
            "numbering contiguous 1–%d, before this builds." % TOTAL,
        ],
        "sections": sections,
    }

    legacy = shipped_ids()
    out = prop.write(p, legacy_ids=sorted(legacy))
    print("wrote %s — %d rows covering %d episodes, %d ids kept"
          % (out.name, len(ids), len(overall), len(legacy)))
    for s in sections:
        print("   %-10s %3d  %s" % (s["title"], len(s["items"]), s["sub"]))
    for s in sections:
        for x in s["items"]:
            if x.get("note"):
                print("   note  %-30s %s" % (x["t"][:30], x["note"]))


def main():
    args = sys.argv[1:]
    if args and args[0] == "--refetch":
        refetch(args[1] if len(args) > 1 else None)
        return
    assert not args, "usage: make_vampire-diaries.py [--refetch [cache-dir]]"
    build()


if __name__ == "__main__":
    main()
