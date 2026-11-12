#!/usr/bin/env python3
"""Collect real lengths for every row of properties/nasuverse.json.

    PYTHONIOENCODING=utf-8 python scratch/nasuverse/collect.py

Writes tools/data/nasuverse.json, which tools/make_nasuverse.py reads. The
generator itself never touches the network, so it stays byte-for-byte
re-runnable; this script is the only thing that fetches.

Nasuverse is six media in one hour-weighted list, so it needs three sources
and refuses a number when none of them has one:

  * GAMES and VISUAL NOVELS -> HowLongToBeat main-story figures, through
    tools/gwlib/hltb.py's verify-by-name gate. A record only counts when its
    name normalizes to the row's and its year sits inside the window.
  * FILMS and ANIME -> the runtime the work's own Wikipedia infobox carries,
    read here rather than typed. A row is weighted only when that box gives
    ONE unambiguous figure: a single runtime for a one-off, or a single
    per-episode runtime AND a single integer episode count for a series.
  * NOVELS and MANGA -> nothing. Pages are not hours, which is the same
    refusal tools/make_dune.py and tools/make_middle_earth.py make.

Anything that fails ships UNWEIGHTED with the reason written into the data
file, where the generator asserts it exists. The rules that produced the
refusals below, in the order they bit:

  * A RANGE IS NOT A FIGURE. Carnival Phantasm's episodes run "8-20
    minutes"; Unlimited Blade Works lists three different lengths. Picking
    one, or averaging them, would be inventing.
  * A COUNT WITH A PLUS IN IT IS NOT A COUNT. "10 + OVA", "13 + 2 SP",
    "21 + 1 special" cannot be multiplied by anything.
  * NEVER BILL THE SAME THING TWICE. The Garden of Sinners row IS the seven
    2007-2009 films, and "A Study in Murder, Part 2" is the seventh of them
    with a row of its own, so only the seven-film row carries the hours.
    Same rule that leaves Mega Man Battle Network 3's Blue and White halves
    unweighted.
  * A REMASTER IS NOT A SEPARATE ENTRY. HowLongToBeat times Fate/stay night
    and Fate/hollow ataraxia once each; the 2024 and 2025 remasters have no
    record of their own, and copying the original's figure across editions
    is exactly the guess this list refuses to make.

One correction shipped with this: the row for The Garden of Sinners: Mirai
Fukuin carried 61 minutes, which is the runtime of Gate of 7th Heaven, the
2009 recap film. Mirai Fukuin (Future Gospel, 28 September 2013) is 88
minutes in its own article AND in the film-series box's per-film list. The
figure comes from those two agreeing sources now.

Wikipedia pages are cached next to this file so a re-run costs nothing.
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from gwlib import hltb, wiki  # noqa: E402
from make_nasuverse import WORKS, item_id  # noqa: E402

CACHE = HERE / "wiki"
OUT = ROOT / "tools" / "data" / "nasuverse.json"

# ---------------------------------------------------------------- HowLongToBeat
# id -> the exact name HowLongToBeat files the game under, or None with the
# reason it has no record that identifies THIS row.
HLTB_QUERY = {
    # visual novels
    "nasu-vn-tsukihime": "Tsukihime",
    "nasu-vn-kagetsu-tohya": "Kagetsu Tohya",
    "nasu-vn-fate-stay-night": "Fate/stay night",
    "nasu-vn-fate-hollow-ataraxia": "Fate/hollow ataraxia",
    "nasu-vn-witch-on-the-holy-night": "Witch on the Holy Night",
    "nasu-vn-tsukihime-a-piece-of-blue-glass-moon":
        "Tsukihime -A piece of blue glass moon-",
    "nasu-vn-fate-stay-night-remastered": None,
    "nasu-vn-fate-hollow-ataraxia-remastered": None,
    "nasu-vn-tsukihime-the-other-side-of-red-garden": None,
    # games
    "nasu-game-melty-blood": "Melty Blood",
    "nasu-game-melty-blood-re-act": "Melty Blood Re-ACT",
    "nasu-game-melty-blood-act-cadenza": "Melty Blood: Act Cadenza",
    "nasu-game-fate-tiger-colosseum": "Fate/tiger colosseum",
    "nasu-game-fate-unlimited-codes": "Fate/unlimited codes",
    "nasu-game-fate-tiger-colosseum-upper": "Fate/tiger colosseum Upper",
    "nasu-game-melty-blood-actress-again": "Melty Blood: Actress Again",
    "nasu-game-fate-extra": "Fate/Extra",
    "nasu-game-fate-extra-ccc": "Fate/Extra CCC",
    "nasu-game-fate-grand-order": "Fate/Grand Order",
    "nasu-game-fate-extella-the-umbral-star": "Fate/Extella: The Umbral Star",
    "nasu-game-fate-extella-link": "Fate/Extella Link",
    "nasu-game-melty-blood-type-lumina": "Melty Blood: Type Lumina",
    "nasu-game-fate-samurai-remnant": "Fate/Samurai Remnant",
}

# Why a None above is a None — checked against the search results themselves,
# cached in hltb_raw.json next to this file.
NO_HLTB = {
    "nasu-vn-fate-stay-night-remastered":
        "HowLongToBeat has one Fate/stay night record (#3416, the 2004 "
        "visual novel) and none for the 2024 remaster — and that record's "
        "own platform list already includes the remaster's Switch and PC "
        "releases, so its 58.70 h covers both rows and belongs to neither "
        "alone. Same shape as the bond-games rows HowLongToBeat files "
        "under one entry.",
    "nasu-vn-fate-hollow-ataraxia-remastered":
        "HowLongToBeat has one Fate/hollow ataraxia record (#20806, 2005) "
        "and none for the 2025 remaster; that record's platform list "
        "already spans Switch and PC, so its figure covers both rows",
    "nasu-vn-tsukihime-the-other-side-of-red-garden":
        "announced with no release date — there is nothing to time yet",
}

# What the reader sees when a row carries no number. Kept short; the full
# reason lives in the data file.
SHORT = {
    "nasu-vn-fate-stay-night-remastered":
        "HowLongToBeat times the visual novel once, not each remaster, so "
        "this row carries no length",
    "nasu-vn-fate-hollow-ataraxia-remastered":
        "HowLongToBeat times the visual novel once, not each remaster, so "
        "this row carries no length",
    "nasu-vn-tsukihime-the-other-side-of-red-garden": "Not released yet",
    "nasu-game-fate-tiger-colosseum-upper":
        "HowLongToBeat has the game but no main-story figure for it",
    "nasu-film-the-garden-of-sinners-a-study-in-murder-part-2":
        "The seventh of the seven films above, and counted there",
    "nasu-tv-carnival-phantasm":
        "Episodes run 8 to 20 minutes, so no one length fits the row",
    "nasu-tv-fate-stay-night-unlimited-blade-works":
        "Three different episode lengths and an OVA, so no one length fits "
        "the row",
    "nasu-tv-fate-kaleid-liner-prisma-illya":
        "Four seasons under one row, so no one length fits it",
    "nasu-tv-fate-extra-last-encore":
        "Episodes run 24 to 50 minutes, so no one length fits the row",
    "nasu-film-witch-on-the-holy-night":
        "Not released yet — due 20 November 2026",
    "nasu-game-fate-extra-record": "Not released yet — due 28 January 2027",
    "nasu-game-melty-blood-twi-lumina": "Not released yet — due 22 April 2027",
    "nasu-tv-fate-kaleid-liner-prisma-illya-finale":
        "Not released yet — due 2027",
}

# Announced works WITH a release date. They ship as w: 0, not as an
# unweighted row: a row with no `w` counts as one invented hour on the page,
# and a work that is not out should count as nothing until it opens. Each
# date was read off the work's own article (2026-11-11).
UNRELEASED = {
    "nasu-film-witch-on-the-holy-night":
        "dated 20 November 2026 in Japan by the Witch on the Holy Night "
        "article — not out yet, so there is no runtime to read",
    "nasu-game-fate-extra-record":
        "dated 28 January 2027 by its own article (Gematsu, 3 September "
        "2026) — not out yet, so HowLongToBeat has nothing to time",
    "nasu-game-melty-blood-twi-lumina":
        "dated 22 April 2027 by the Melty Blood: Type Lumina article "
        "(Gematsu, 11 September 2026) — not out yet, so HowLongToBeat has "
        "nothing to time",
    "nasu-tv-fate-kaleid-liner-prisma-illya-finale":
        "the fifth and final season, set to premiere in 2027 by the "
        "Fate/kaleid liner Prisma Illya article — not out yet, so there is "
        "no runtime to read",
}

# --------------------------------------------------------------------- Wikipedia
# id -> (page, box selector, mode, extra). Modes:
#   "one"    a single `runtime = N minutes`
#   "series" `runtime = N minutes` times a clean integer episode count
#   "parts"  a collapsible per-part runtime list; `extra` is how many of the
#            parts this row covers, counted from the first
# The box selector matches the infobox's own `title` (animanga boxes) or the
# literal "television"/"film" for a plain {{Infobox television|film}}.
WIKI_RUNTIME = {
    "nasu-film-the-garden-of-sinners":
        ("The Garden of Sinners", "film series", "parts", 7),
    "nasu-film-fate-grand-order-final-singularity-grand-temple-of-time-solomon":
        ("Fate/Grand Order: Final Singularity-Grand Temple of Time: Solomon",
         "film", "one", None),
    "nasu-film-the-garden-of-sinners-mirai-fukuin":
        ("The Garden of Sinners: Future Gospel", "film", "one", None),
    # carried 62 minutes until 2026-11-11, which is the runtime of the 2019
    # Prisma Phantasm OVA; the film's own box says 90
    "nasu-film-prisma-illya-vow-in-the-snow":
        ("Fate/kaleid liner Prisma Illya: Vow in the Snow", "film", "one",
         None),
    "nasu-tv-fate-stay-night":
        ("Fate/stay night (2006 TV series)", "television", "series", None),
    "nasu-tv-today-s-menu-for-the-emiya-family":
        # the box carries no title; "ona" is its own `type` field
        ("Today's Menu for the Emiya Family", "ona", "series", None),
    "nasu-tv-fate-grand-order-first-order":
        ("Fate/Grand Order", "First Order", "one", None),
    "nasu-tv-fate-grand-order-moonlight-lostroom":
        ("Fate/Grand Order", "Moonlight/Lostroom", "one", None),
}

# Figures already in the list that this script does not source. Each is a
# runtime read off the work's own article when the row was written; they are
# repeated here so the data file is the single place a weight comes from.
KEPT_MINUTES = {
    "nasu-film-fate-stay-night-unlimited-blade-works": (105, "Fate/stay night: Unlimited Blade Works (film)"),
    "nasu-film-the-garden-of-sinners-epilogue": (33, "The Garden of Sinners"),
    "nasu-film-prisma-illya-oath-under-snow": (95, "Fate/kaleid liner Prisma Illya: Oath Under Snow"),
    "nasu-film-fate-stay-night-heaven-s-feel-i-presage-flower": (120, "Fate/stay night: Heaven's Feel"),
    "nasu-film-fate-stay-night-heaven-s-feel-ii-lost-butterfly": (117, "Fate/stay night: Heaven's Feel"),
    "nasu-film-fate-stay-night-heaven-s-feel-iii-spring-song": (122, "Fate/stay night: Heaven's Feel"),
    "nasu-tv-fate-strange-fake-whispers-of-dawn": (55, "Fate/strange Fake"),
}

# Rows with no source at all, and why. Every one of these was looked for in
# the work's own article and in Wikidata before being written down.
NO_LENGTH = {
    "nasu-film-the-garden-of-sinners-a-study-in-murder-part-2":
        "film VII of the seven the row above covers; weighting it here too "
        "would bill the same 121 minutes twice",
    "nasu-film-fate-grand-order-divine-realm-of-the-round-table-camelot-wandering-agateram":
        "the Camelot film-series box on Fate/Grand Order leaves its runtime "
        "field empty, the films have no articles of their own, and Wikidata "
        "carries no P2047 for either part",
    "nasu-film-fate-grand-order-divine-realm-of-the-round-table-camelot-paladin-agateram":
        "the Camelot film-series box on Fate/Grand Order leaves its runtime "
        "field empty, the films have no articles of their own, and Wikidata "
        "carries no P2047 for either part",
    "nasu-tv-lunar-legend-tsukihime":
        "the Tsukihime article's own box gives 12 episodes and no runtime; "
        "there is no separate article and no Wikidata P2047",
    "nasu-tv-carnival-phantasm":
        "episodes run 8-20 minutes by the article's own box — a range is "
        "not a figure, and picking one end would be inventing",
    "nasu-tv-fate-zero":
        "the article's box gives 25 episodes and no runtime; Wikidata holds "
        "no P2047 for the series and no episode items at all",
    "nasu-tv-fate-kaleid-liner-prisma-illya":
        "one row covering four seasons the article counts as \"10 + OVA\" "
        "and more — no single length fits it",
    "nasu-tv-fate-stay-night-unlimited-blade-works":
        "the article lists three episode lengths (23, 47 and 10 minutes) "
        "over \"26 + OVA\" episodes — no single figure covers it",
    "nasu-tv-fate-apocrypha":
        "the article's box gives 25 episodes and no runtime, and Wikidata "
        "has no P2047",
    "nasu-tv-the-case-files-of-lord-el-melloi-ii":
        "the article counts \"13 + 2 SP\" episodes and gives no runtime",
    "nasu-tv-lord-el-melloi-ii-s-case-files-rail-zeppelin-grace-note-a-grave-keeper-a-cat-and-a-mage":
        "the Episode 0 special has no runtime in the article and no "
        "Wikidata item",
    "nasu-tv-lord-el-melloi-ii-s-case-files-rail-zeppelin-grace-note-special-edition":
        "the New Year's Eve special has no runtime in the article and no "
        "Wikidata item",
    "nasu-tv-fate-grand-order-absolute-demonic-front-babylonia":
        "the article counts \"21 + 1 special\" episodes and gives no runtime",
    "nasu-tv-fate-grand-carnival":
        "the article's box gives 2 episodes and no runtime",
    "nasu-tv-fate-strange-fake":
        "the Fate/Strange Fake article's tv-series box gives 13 episodes and "
        "no runtime",
    # weighted 13 x 24 minutes until 2026-11-11; the article's box (now an
    # {{Infobox anime video}}) has since widened its runtime to a range
    "nasu-tv-fate-extra-last-encore":
        "the article's box gives 13 episodes at \"24–50 minutes\" — a range "
        "is not a figure, and picking one end would be inventing",
}

# Whole media that carry no hours by rule, not by accident.
NO_LENGTH_MEDIA = {
    "novel": "prose has no runtime — page counts differ by edition and are "
             "not hours, the same refusal dune and middle-earth make",
    "manga": "comics have no runtime — chapter counts are not hours",
}
SHORT_MEDIA = {"novel": "Pages aren't hours", "manga": "Pages aren't hours"}


def video_boxes(text):
    """(title_or_type, body) for every {{Infobox animanga/Video}} on a page.

    A box ends where the next infobox begins. Cutting at the first "\\n}}"
    instead would stop inside {{English anime licensee}}, and taking a fixed
    window would read the NEXT box's title — which is how Today's Menu for
    the Emiya Family briefly reported itself as a manga volume list.
    """
    out = []
    starts = [x.start() for x in re.finditer(r"\{\{Infobox ", text)]
    for m in re.finditer(r"\{\{Infobox animanga/Video", text):
        nxt = next((s for s in starts if s > m.start()), len(text))
        body = text[m.start():nxt]
        # [ \t] rather than \s around the "=": \s eats the newline, and an
        # empty `| title =` then swallowed the NEXT field's value whole
        title = re.search(r"^[ \t]*\|[ \t]*title[ \t]*=[ \t]*(.+?)[ \t]*$",
                          body, re.M)
        kind = re.search(r"^[ \t]*\|[ \t]*type[ \t]*=[ \t]*(.+?)[ \t]*$",
                         body, re.M)
        out.append(((title.group(1) if title else
                     (kind.group(1) if kind else "")), body))
    return out


def field(body, name):
    m = re.search(r"^\s*\|\s*%s\s*=\s*(.*?)(?=\n\s*\|\s*[a-z_ ]+\s*=|\n\}\})"
                  % name, body, re.M | re.S)
    return m.group(1).strip() if m else ""


def one_int(s):
    """The integer `s` is, or None if it is a range, a list or has a rider."""
    s = re.sub(r"<[^>]+>|\{\{[^{}]*\}\}", " ", s or "").strip()
    return int(s) if re.fullmatch(r"\d+", s) else None


def minutes_of(page, selector, mode, extra):
    """Minutes for one row, off the page's own infobox. Raises if the shape
    the row was written against is gone — a silent zero is how a catalogue
    loses its weights."""
    text = wiki.wikitext(page, cache_dir=str(CACHE))
    assert text, "no wikitext for %r" % page

    if selector in ("television", "film"):
        f = wiki.infobox(text, kind=r"%s|anime video" % selector)
        assert f, "no {{Infobox %s}} on %r" % (selector, page)
        body = None
        runtime, eps = f("runtime"), f("num_episodes")
    else:
        boxes = [b for t, b in video_boxes(text) if t == selector]
        assert len(boxes) == 1, \
            "%r has %d animanga/Video boxes titled %r" % (page, len(boxes),
                                                          selector)
        body = boxes[0]
        runtime, eps = field(body, "runtime"), field(body, "episodes")

    if mode == "parts":
        # Read the "N minutes (ep. K)" pairs, NOT every number in the field:
        # the collapsible list's own title is "45-121 minutes", and a plain
        # `(\d+) minutes` sweep picks that 121 up as if it were a part. It
        # happened to give the right total here only because ep. 7 is also
        # 121 and got pushed off the end of the slice — luck, not parsing.
        got = {int(k): int(v) for v, k in re.findall(
            r"(\d+)\s*minutes\s*<small>\(ep\.\s*(\d+)\)</small>", runtime)}
        n = one_int(eps)
        assert n and sorted(got) == list(range(1, n + 1)), \
            "%r's %r box lists parts %s for %r episodes — the per-part " \
            "runtime list and the episode count disagree" \
            % (page, selector, sorted(got), eps[:20])
        assert n >= extra, "%r has %d parts, this row covers %d" \
            % (page, n, extra)
        take = [got[i] for i in range(1, extra + 1)]
        return sum(take), ("%s — %r box, parts 1-%d of its own per-part "
                           "runtime list (%s min) out of %d"
                           % (page, selector, extra,
                              " + ".join(str(x) for x in take), n))

    mins = re.fullmatch(r"(\d+)\s*minutes?", runtime.strip())
    assert mins, "%r's %r box no longer gives one plain runtime: %r" \
        % (page, selector, runtime[:80])
    mins = int(mins.group(1))

    if mode == "one":
        return mins, "%s — %r box, runtime %d minutes" % (page, selector, mins)

    n = one_int(eps)
    assert n, "%r's %r box no longer gives one plain episode count: %r" \
        % (page, selector, eps[:60])
    return mins * n, ("%s — %r box, %d episodes at %d minutes"
                      % (page, selector, n, mins))


def main():
    rows = [(item_id(media, name), media, name, date)
            for media, name, date, _note in WORKS]
    ids = [r[0] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate row ids"

    session = hltb.Session(cache_dir=str(HERE))
    out = {}
    for rid, media, name, date in rows:
        year = int(date[:4]) if date != "TBA" else None
        rec = {"t": name, "media": media, "w": None}

        if rid in UNRELEASED:
            rec["w"] = 0
            rec["why"] = UNRELEASED[rid]
        elif rid in HLTB_QUERY:
            q = HLTB_QUERY[rid]
            if q is None:
                rec["why"] = NO_HLTB[rid]
            else:
                hours, hit, why = hltb.story_hours(
                    q, year, results=session.search(q))
                if hours:
                    rec["w"] = hours
                    rec["source"] = ("HowLongToBeat #%s %r (%s) — main story "
                                     "%.2f h, verified by name"
                                     % (hit.game_id, hit.game_name,
                                        hit.release_world, hours))
                else:
                    rec["why"] = "HowLongToBeat: %s" % why
        elif rid in WIKI_RUNTIME:
            page, selector, mode, extra = WIKI_RUNTIME[rid]
            mins, how = minutes_of(page, selector, mode, extra)
            rec["w"] = round(mins / 60.0, 2)
            rec["minutes"] = mins
            rec["source"] = how
        elif rid in KEPT_MINUTES:
            mins, page = KEPT_MINUTES[rid]
            rec["w"] = round(mins / 60.0, 2)
            rec["minutes"] = mins
            rec["source"] = "%s — %d minutes, read when the row was written" \
                % (page, mins)
        elif media in NO_LENGTH_MEDIA:
            rec["why"] = NO_LENGTH_MEDIA[media]
        elif rid in NO_LENGTH:
            rec["why"] = NO_LENGTH[rid]
        else:
            raise SystemExit("no length rule for %s (%s)" % (rid, name))

        if not rec["w"]:
            assert rec.get("why"), "unweighted %s with no reason" % rid
            short = SHORT.get(rid) or SHORT_MEDIA.get(media) or \
                "No published length for it"
            rec["short"] = short
            assert 0 < len(short) < 120, short
        out[rid] = rec

    weighted = [r for r in out.values() if r["w"]]
    doc = {
        "what": "Per-row lengths in hours for properties/nasuverse.json. "
                "Written by scratch/nasuverse/collect.py; read by "
                "tools/make_nasuverse.py, which never fetches.",
        "rules": "Games and visual novels: HowLongToBeat main story through "
                 "gwlib.hltb's verify-by-name gate. Films and anime: the "
                 "runtime the work's own Wikipedia infobox carries, and only "
                 "when it gives one unambiguous figure. Novels and manga: "
                 "nothing, because pages are not hours. Every null carries "
                 "the reason it is null.",
        "weights": out,
    }
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8", newline="\n")

    for rid, rec in out.items():
        if rec["w"]:
            print("  %-56s %7.2f h  %s" % (rec["t"][:56], rec["w"],
                                           rec["source"][:52]))
        else:
            print("  %-56s    ----   %s" % (rec["t"][:56], rec["why"][:52]))
    print("\n%d/%d weighted (%.1f hours), %d unweighted, %d live HLTB calls"
          % (len(weighted), len(out), sum(r["w"] for r in weighted),
             len(out) - len(weighted), session.calls))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
