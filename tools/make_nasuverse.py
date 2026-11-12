#!/usr/bin/env python3
"""Generate properties/nasuverse.json.

    python3 tools/make_nasuverse.py

Type-Moon's shared universe — Fate, Tsukihime, Melty Blood, Kara no Kyoukai,
Witch on the Holy Night — organised by media type, release order inside each.

Dates come from Wikipedia's Type-Moon release list and the individual work
articles' infoboxes, read rather than typed. Where only a year could be
confirmed the entry shows the year and nothing finer; nothing here is a guess.

LENGTHS come from tools/data/nasuverse.json, which scratch/nasuverse/
collect.py builds out of three sources and no guesses: HowLongToBeat
main-story figures behind gwlib.hltb's verify-by-name gate for the games and
visual novels, the work's own Wikipedia infobox runtime for the films and
anime, and nothing at all for the novels and manga, because pages are not
hours. This file never fetches — it reads that data file and asserts every
row is accounted for, so running it twice produces identical output.

A row with no length keeps its reason. The data file carries the full one
and the generator refuses to emit a row without it; the row's own note gets
the short version, so a reader can see why a bar has no number on it. The
reasons are real and various: an announced visual novel with no release
date, an anime whose article gives a RANGE of episode lengths rather than a
figure, a Kara no Kyoukai film that is already inside the seven-film row
above it, remasters HowLongToBeat times once under the original.

An announced work WITH a release date (even a bare year) is the one row that
carries an explicit w: 0 rather than no weight: it is not out, so its bar
stays empty until it opens instead of counting as an invented hour. The data
file marks it with "w": 0 and the reason says when it is due. An announced
work with no date at all (Red Garden) keeps the plain unweighted form.

Tier 2 marks a work its own remake supersedes — the 2000 Tsukihime, the 2004
Fate/stay night, the 2005 Fate/hollow ataraxia. They stay in the list because
this is a catalogue of what exists, but a finish date paces you through the
versions actually worth starting on. Nothing else is ranked: the "where to
start" advice lives in the notes rather than being invented per row.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from gwlib import prop as P  # noqa: E402

SLUG = "nasuverse"
DATA = pathlib.Path(__file__).resolve().parent / "data" / "nasuverse.json"

# (media, title, date, note)
# date is YYYY-MM-DD where confirmed, or YYYY where only the year is.
# Lengths are NOT here — they live in tools/data/nasuverse.json so there is
# exactly one place a weight can come from.
WORKS = [
    # ---------------------------------------------------------------- novels
    ("novel", "The Garden of Sinners", "1998-10",
     "Kara no Kyoukai. Nasu's first work, serialised before Type-Moon existed."),
    ("novel", "Fate/Zero", "2006-12-29",
     "Urobuchi's prequel to Fate/stay night, in four volumes"),
    ("novel", "Fate/Apocrypha", "2012-12-29", ""),
    ("novel", "The Case Files of Lord El-Melloi II", "2014-12-30",
     "Detective stories set between Fate/Zero and Fate/stay night"),
    ("novel", "Fate/strange Fake", "2015-01-10", "Ryohgo Narita"),
    # ------------------------------------------------------------ visual novels
    ("vn", "Tsukihime", "2000-12-28",
     "The doujin visual novel everything else grew out of. The 2021 remake "
     "rewrites and expands it."),
    ("vn", "Kagetsu Tohya", "2001-08-13", "Tsukihime fan disc"),
    ("vn", "Fate/stay night", "2004-01-30",
     "Three routes — Fate, Unlimited Blade Works, Heaven's Feel — read in that "
     "order. Play the 2024 remaster instead."),
    ("vn", "Fate/hollow ataraxia", "2005-10-28",
     "Sequel to Fate/stay night. Play the 2025 remaster instead."),
    ("vn", "Witch on the Holy Night", "2012-04-12",
     "Mahoutsukai no Yoru. Standalone, and needs nothing else read first. "
     "English release 2022."),
    ("vn", "Tsukihime -A piece of blue glass moon-", "2021-08-26",
     "The remake, retelling the first half of Tsukihime. Worldwide 2024."),
    ("vn", "Fate/stay night Remastered", "2024-08-08",
     "The version to play — and the first official release outside Japan"),
    ("vn", "Fate/hollow ataraxia Remastered", "2025-08-07",
     "The version to play, released worldwide"),
    ("vn", "Tsukihime -The other side of red garden-", "TBA",
     "The second half of the remake. Announced, no release date."),
    # ----------------------------------------------------------------- games
    ("game", "Melty Blood", "2002-12-28",
     "Fighting game with French-Bread, and a direct Tsukihime sequel in story"),
    ("game", "Melty Blood Re-ACT", "2004-05-30", "Expanded follow-up to Melty Blood"),
    ("game", "Melty Blood: Act Cadenza", "2005-03-25",
     "The arcade version, following Re-ACT"),
    ("game", "Fate/tiger colosseum", "2007-09-13", "PSP fighting game"),
    ("game", "Fate/unlimited codes", "2008-06-11", "Arcade, PS2 and PSP fighting game"),
    ("game", "Fate/tiger colosseum Upper", "2008-06-16",
     "Follow-up to Fate/tiger colosseum, with an expanded roster"),
    ("game", "Melty Blood: Actress Again", "2008-09-19",
     "Arcade sequel to Act Cadenza; later revised as Current Code"),
    ("game", "Fate/Extra", "2010-07-22",
     "PSP dungeon-crawling RPG, and its own branch of the setting — "
     "Fate/Extra Last Encore follows from it"),
    ("game", "Fate/Extra CCC", "2013-03-28", "Side story to Fate/Extra"),
    ("game", "Fate/Grand Order", "2015-07-30",
     "The mobile RPG, still running, and the largest single body of story in the universe"),
    ("game", "Fate/Extella: The Umbral Star", "2016-11-10",
     "Action RPG, an original story"),
    ("game", "Fate/Extella Link", "2018-06-07",
     "Sequel to Fate/Extella: The Umbral Star"),
    ("game", "Melty Blood: Type Lumina", "2021-09-30",
     "Reboot of the fighting game, following the Tsukihime remake"),
    ("game", "Fate/Samurai Remnant", "2023-09-28",
     "Action RPG set during a Holy Grail War in Edo-period Japan"),
    ("game", "Fate/Extra Record", "2027-01-28", "Remake of Fate/Extra"),
    ("game", "Melty Blood: Twi-Lumina", "2027-04-22",
     "Sequel to Melty Blood: Type Lumina"),
    # ------------------------------------------------------------ anime series
    ("tv", "Lunar Legend Tsukihime", "2003-10-10", "J.C.Staff's Tsukihime adaptation"),
    ("tv", "Fate/stay night", "2006-01-07",
     "Studio Deen. 24 episodes, following the Fate route."),
    ("tv", "Carnival Phantasm", "2011-08-12",
     "Comedy OVA crossing Fate and Tsukihime, from the Take Moon parody manga"),
    ("tv", "Fate/Zero", "2011-10-01", "ufotable. 25 episodes across two cours."),
    ("tv", "Fate/kaleid liner Prisma Illya", "2013",
     "Magical-girl spin-off, four seasons from here"),
    ("tv", "Fate/stay night: Unlimited Blade Works", "2014-10-05",
     "ufotable. 26 episodes plus an OVA, adapting the second route."),
    ("tv", "Fate/Grand Order: First Order", "2016-12-31",
     "Television special adapting the Grand Order game's prologue"),
    ("tv", "Fate/Apocrypha", "2017",
     "An alternate continuity, unconnected to Fate/stay night"),
    ("tv", "Fate/Grand Order: Moonlight/Lostroom", "2017-12-31",
     "Animation short following First Order, written by Nasu"),
    ("tv", "Lord El-Melloi II's Case Files {Rail Zeppelin} Grace note "
           "— A Grave Keeper, a Cat, and a Mage", "2018-12-31",
     "Episode 0, aired before the series"),
    ("tv", "Fate/Extra Last Encore", "2018-01-28",
     "Shaft's series following the Fate/Extra game"),
    ("tv", "Today's Menu for the Emiya Family", "2018", "Comedy cooking spin-off"),
    ("tv", "Lord El-Melloi II's Case Files {Rail Zeppelin} Grace note", "2019-07-06",
     "Troyca's 13 episodes, adapting the Rail Zeppelin case. Set ten years "
     "after Fate/Zero."),
    ("tv", "Fate/Grand Order: Absolute Demonic Front Babylonia", "2019-10-05",
     "The Babylonia singularity from the Grand Order game, animated by CloverWorks"),
    ("tv", "Lord El-Melloi II's Case Files {Rail Zeppelin} Grace note "
           "— Special Edition", "2021-12-31", "New Year's Eve special"),
    ("tv", "Fate/Grand Carnival", "2020-12-31",
     "Successor to Carnival Phantasm, using the Grand Order cast"),
    ("tv", "Fate/strange Fake: Whispers of Dawn", "2023-07-02", "One-off special"),
    ("tv", "Fate/strange Fake", "2024-12-31",
     "A-1 Pictures' 13 episodes, following Whispers of Dawn. The first aired "
     "on New Year's Eve 2024, the other twelve from January to March 2026."),
    ("tv", "Fate/kaleid liner Prisma Illya Finale", "2027",
     "The fifth and final season"),
    # ----------------------------------------------------------------- films
    ("film", "The Garden of Sinners", "2007-12-01",
     "Seven films, released 2007–2009, adapting the novels out of chronological order"),
    ("film", "Fate/stay night: Unlimited Blade Works", "2010-01-23",
     "Studio Deen's film of the second route"),
    ("film", "The Garden of Sinners: A Study in Murder, Part 2", "2009-08-08", ""),
    ("film", "The Garden of Sinners: Epilogue", "2011-02-02", ""),
    ("film", "The Garden of Sinners: Mirai Fukuin", "2013-09-28",
     "The Garden of Sinners: The Future Gospel"),
    ("film", "Fate/kaleid liner Prisma Illya: Vow in the Snow", "2017-08-26",
     "Follows the Prisma Illya series"),
    ("film", "Fate/kaleid liner Prisma Illya: Oath Under Snow", "2019-06-14",
     "Follows Vow in the Snow"),
    ("film", "Fate/stay night: Heaven's Feel I. presage flower", "2017-10-14",
     "ufotable. The third route, over three films — watch after Unlimited "
     "Blade Works."),
    ("film", "Fate/stay night: Heaven's Feel II. lost butterfly", "2019-01-12",
     "Second of the three"),
    ("film", "Fate/stay night: Heaven's Feel III. spring song", "2020-08-15",
     "Last of the three"),
    ("film", "Fate/Grand Order — Divine Realm of the Round Table: Camelot, "
             "Wandering; Agateram", "2020-12-05",
     "First of two films adapting the Grand Order game's Camelot chapter"),
    ("film", "Fate/Grand Order — Divine Realm of the Round Table: Camelot, "
             "Paladin; Agateram", "2021-05-15", "Second of the two"),
    ("film", "Fate/Grand Order: Final Singularity — Grand Temple of Time: Solomon",
     "2021-07-30",
     "CloverWorks' film of the game's final chapter, following Babylonia"),
    ("film", "Witch on the Holy Night", "2026-11-20",
     "ufotable's film of the visual novel"),
    # ----------------------------------------------------------------- manga
    ("manga", "Fate/kaleid liner Prisma Illya", "2007-09-26",
     "Long-running spin-off, and the source of the anime seasons"),
    ("manga", "Today's Menu for the Emiya Family", "2016-01-26", ""),
]

# Item ids are load-bearing — a saved group's progress is a list of them — so a
# retitled entry keeps the slug it was first published under.
PIN = {
    "Lord El-Melloi II's Case Files {Rail Zeppelin} Grace note":
        "the-case-files-of-lord-el-melloi-ii",
    "Fate/kaleid liner Prisma Illya: Vow in the Snow":
        "prisma-illya-vow-in-the-snow",
    "Fate/kaleid liner Prisma Illya: Oath Under Snow":
        "prisma-illya-oath-under-snow",
}

# Works their own remake supersedes. They stay listed, but a finish date skips
# them — you would start on the remake, not on these.
SUPERSEDED = {
    ("vn", "Tsukihime"),
    ("vn", "Fate/stay night"),
    ("vn", "Fate/hollow ataraxia"),
}

MEDIA = [
    ("vn", "Visual novels", "where almost all of it starts",
     "Nasu's own works, and the primary text for everything else. Fate/stay "
     "night and Tsukihime are the two entry points; Witch on the Holy Night "
     "stands completely alone and needs nothing read first."),
    ("tv", "Anime series", "", ""),
    ("film", "Films", "", ""),
    ("game", "Games", "",
     "Melty Blood carries real Tsukihime story rather than being a spin-off, "
     "and Fate/Grand Order is by volume the largest body of story Type-Moon "
     "has written."),
    ("novel", "Novels", "light novels and Nasu's early prose", ""),
    ("manga", "Manga", "", ""),
]


def sortkey(d):
    """Year-only dates sort mid-year, so they land among their own year.

    "TBA" sorts last: an announced work with no date belongs at the end of its
    section rather than at some invented point inside it.
    """
    if d == "TBA":
        return ("9999", "12", "31")
    parts = d.split("-")
    return (parts[0], parts[1] if len(parts) > 1 else "07",
            parts[2] if len(parts) > 2 else "01")


def slug(t):
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def item_id(media, name):
    """The row's id. Ids are load-bearing — a saved group's progress is a
    list of them — so PIN keeps a retitled work on the slug it shipped
    under. scratch/nasuverse/collect.py imports this so the data file and
    the rows can never key differently."""
    return "nasu-%s-%s" % (media, PIN.get(name) or slug(name))


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))["weights"]

    sections = []
    for key, title, sub, intro in MEDIA:
        got = sorted([w for w in WORKS if w[0] == key], key=lambda w: sortkey(w[2]))
        items = []
        for _, name, date, note in got:
            rid = item_id(key, name)
            assert rid in data, "no length verdict for %s (%s)" % (rid, name)
            d = data[rid]
            assert d["t"] == name, \
                "%s: data file calls it %r, WORKS calls it %r" % (rid, d["t"], name)
            x = {"id": rid, "t": name, "n": date.split("-")[0]}
            if (key, name) in SUPERSEDED:
                x["tier"] = 2
            if d.get("w"):
                x["w"] = d["w"]
                assert 0 < x["w"] < 400, "absurd weight on %s: %r" % (rid, x["w"])
            else:
                # No number without a reason. The long version lives in the
                # data file; the row wears the short one so a bar with no
                # figure on it explains itself.
                assert d.get("why") and d.get("short"), \
                    "unweighted %s with no reason" % rid
                note = P.join_bits(note.rstrip("."), d["short"])
                if d.get("w") == 0:
                    # announced with a date: not out, so the bar stays
                    # empty rather than counting an invented hour
                    x["w"] = 0
            if note:
                x["note"] = note
            items.append(x)
        dated = [w for w in got if w[2] != "TBA"]
        years = "%s–%s" % (dated[0][2][:4], dated[-1][2][:4])
        hours = sum(x.get("w", 0) for x in items)
        wtd = sum(1 for x in items if x.get("w"))
        bits = [years, sub, "%d entries" % len(items)]
        if wtd:
            bits.append("about %d hours across %d" % (round(hours), wtd)
                        if wtd < len(items) else "about %d hours" % round(hours))
        sec = {"id": key, "title": title,
               "sub": " · ".join(p for p in bits if p),
               "items": items}
        if intro:
            sec["intro"] = intro
        if key == "vn":
            sec["open"] = True
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(WORKS), (len(ids), len(WORKS))
    assert set(ids) == set(data), \
        "rows and length verdicts disagree: %s" % sorted(set(ids) ^ set(data))
    # every date is a year, a month, a full date, or an honest TBA
    for _, name, d, _ in WORKS:
        assert d == "TBA" or len(d) in (4, 7, 10), "%s: odd date %r" % (name, d)
    titles = {w[1] for w in WORKS}
    keyed = {(w[0], w[1]) for w in WORKS}
    assert not (set(PIN) - titles), "PIN names a work not in WORKS: %s" % (set(PIN) - titles)
    assert not (SUPERSEDED - keyed), "SUPERSEDED names a work not in WORKS: %s" % (SUPERSEDED - keyed)
    superseded = sum(1 for s in sections for x in s["items"] if x.get("tier") == 2)
    assert superseded == len(SUPERSEDED), (superseded, len(SUPERSEDED))

    weighted = [x for s in sections for x in s["items"] if x.get("w")]
    total_h = sum(x["w"] for x in weighted)
    unweighted = len(ids) - len(weighted)

    prop = {
        "slug": SLUG,
        "title": "Nasuverse",
        "subtitle": "Type-Moon's shared universe, by media type",
        "kind": "mixed",
        "popularity": 47,
        "year": "1998–",
        "blurb": "%d works across six media, in release order within each. "
                 "%d carry a verified length — about %d hours of games, "
                 "visual novels, films and anime." % (len(WORKS),
                                                      len(weighted),
                                                      round(total_h)),
        "unit": {"one": "work", "many": "works"},
        "verb": {"base": "read", "past": "done", "ing": "working through"},
        "accent": "#8A2E4A",
        "accentDark": "#E884A6",
        "tiers": True,
        "itemTiers": True,
        "paceTiers": [1],
        "paceLabel": "the originals their remakes replaced",
        "notes": [
            ["Where to start.", "Fate/stay night or Tsukihime, both visual "
             "novels. If you would rather watch than read: Fate/Zero, then "
             "Unlimited Blade Works, then the three Heaven's Feel films. Witch "
             "on the Holy Night and Kara no Kyoukai are standalone and need "
             "nothing else first."],
            ["Organised by medium, not by story.", "There is no single reading "
             "order for this universe — the works branch rather than continue — "
             "so this lists what exists in each medium, oldest first. The notes "
             "say where something sits when it matters."],
            ["Dates.", "Read from Wikipedia's Type-Moon release list and the "
             "individual work articles rather than typed from memory. Where only "
             "a year could be confirmed, only the year is shown."],
            ["Tier 2 means a remake replaced it.", "The 2000 Tsukihime, the 2004 "
             "Fate/stay night and the 2005 Fate/hollow ataraxia are all still "
             "listed, because this is a record of what exists — but you would "
             "start on the remake, so a finish date skips them unless you tick "
             "the box under the bar."],
            ["Not here.", "The many drama CDs, art books and short stories that "
             "exist mostly in Japanese. Grand Order itself is one entry, which "
             "undersells it by several hundred hours."],
            ["Where the hours come from — and where they stop.",
             "Games and visual novels carry HowLongToBeat main-story figures, "
             "verified by name against the work they belong to. Films and "
             "anime carry the runtime the work's own Wikipedia article gives, "
             "and only where it gives one plain figure. %d of the %d rows "
             "have one; the other %d carry a reason instead of a number, and "
             "the reason is on the row. An anime whose article says its "
             "episodes run 8 to 20 minutes has no single length; a novel has "
             "no length at all. Rows without a number count as one entry "
             "each, which is a floor, not a claim."
             % (len(weighted), len(WORKS), unweighted)],
            "Additions and corrections in this list came from a pull request by "
            "adeadeadeadeade; the dates were confirmed against Wikipedia before "
            "being taken. Lengths from HowLongToBeat and from each work's own "
            "Wikipedia article, collected by scratch/nasuverse/collect.py.",
        ],
        "sections": sections,
    }

    out = P.write(prop)

    print("wrote %s" % out.name)
    print("  %d sections, %d works, %d weighted (%.1f h), %d unweighted"
          % (len(sections), len(ids), len(weighted), total_h, unweighted))
    for s in sections:
        print("   %-16s %2d  %s" % (s["title"], len(s["items"]), s["sub"][:62]))


if __name__ == "__main__":
    main()
