"""Build properties/sitcoms.json — the sitcom shelf, one row per show.

CLU-532, and the third of these after tools/make_marvel_comics.py (CLU-480)
and tools/make_dc_comics.py (CLU-449). A BOX SET: every row carries
`into: "<slug>"` pointing at a sitcom that already exists as its own property,
which is what makes src/build.py derive `_hub`, and a hub gets `mega: true` in
the manifest for free. Nothing declares `mega` here — two sources for one fact
is how the two come to disagree.

WHY THIS SHELF EXISTS, AND WHY IT IS NOT A GENRE FIELD. Nathan, CLU-508:
"certain tv should land in a different list like sitcoms, drama, crime, etc."
Then on CLU-235, approving the four British lists: "go ahead and add these to
the upcoming sitcom medium list under their own section called british sitcoms
or something like that I think." That sentence is why the first section is
titled exactly `British sitcoms` and holds exactly those four — a chip on a
genre field could never have held a section, which is the whole reason this is
a box set rather than CLU-510's tagging pass.

NOTHING IS TYPED BY HAND except the section prose and which slugs belong. The
titles, the year ranges, the counts, this list's own year span and the count in
its blurb are read back out of the target files, because a hand-written count
rots the day a show gains an episode.

WHAT A SITCOM IS HERE, because the line had to be drawn somewhere and a shelf
that cannot say what it is will drift:

    a SCRIPTED COMEDY SERIES with a RECURRING CAST, comedy first.

That admits the animated ones — Bob's Burgers and Rick and Morty call
themselves sitcoms in their own blurbs — and it excludes four comedy lists
that are on the site and are not sitcoms: MST3K riffs films, Jackass is
unscripted, Nathan Fielder's shows are unscripted and are one creator's body of
work, and the Muppets list is a film series with a variety show attached. It
also excludes the hour-long comedy-dramas, Psych and Chuck. Every one of those
is named in NOT_SITCOM with its reason rather than quietly missing, and the
notes on the page say the same thing out loud to the reader.

WHY THE STRIP IS UNWEIGHTED. Not a choice — a fact about the targets. None of
the fifteen lists behind this one carries a single `w`, because the episode
lists they are read from publish no per-episode runtime, so build.py derives no
weight for any door and every mark is the same width. That is also the only
reason the shelf can hold all fifteen at once: build.py refuses, correctly, to
draw a measured mark beside an unmeasured one —

    "A weighted strip cannot carry an unweighted row - it would draw as a
     default-sized mark beside a real one."

so a single weighted sitcom list would have to either weight all fifteen or sit
off the shelf. `psych` (about 90 hours) and `chuck` (about 65) are weighted and
are the two live cases; both are hour-long comedy-dramas and are excluded on
what they are, so the weight rule and the genre rule happen to agree today.
facts() asserts the premise rather than trusting it, so the day a sitcom list
gains runtimes this generator fails instead of the build.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop as P  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROPS = ROOT / "properties"

# Grouped the way a reader chooses one: where it was made and whether it is
# drawn, which between them decide what a sitcom feels like far more than its
# decade does. British first because it is the shortest way onto the shelf —
# four runs of six-episode series against five American runs of nine seasons —
# and because it is the section Nathan asked for by name.
SECTIONS = [
    ("british", "British sitcoms",
     "1975–2023, and that last date is a pilot taped in 1982 and first "
     "screened forty-one years later · short series with years between them, "
     "and between them the quickest way onto this shelf.",
     ["fawlty-towers", "blackadder", "peep-show", "the-thick-of-it"]),
    ("network", "American network sitcoms",
     "1972–2013 · the network half-hour at full length, NBC and CBS, none of "
     "these runs shorter than seven seasons. This is where most of the shelf "
     "sits.",
     ["mash", "golden-girls", "seinfeld", "frasier", "the-office"]),
    ("animated", "Animated sitcoms",
     "1989– · the animated half-hour, Fox to Adult Swim. The only section "
     "still adding episodes.",
     ["the-simpsons", "futurama", "archer", "bobs-burgers", "rick-and-morty",
      "president-curtis"]),
]

# Every television list on the site is either a door above or named here with
# the reason it is not a sitcom. Nothing is allowed to be neither.
#
# This guard is the shape tools/make_dc_comics.py grew after its first draft
# quietly omitted `jla-morrison` and the only thing that noticed was a row count
# read by eye. A new comedy list added six months from now cannot be silently
# left off this shelf: the generator stops until somebody decides which side of
# the line it is on, and "it is not a sitcom" has to be written down as a phrase
# a reviewer can argue with.
#
# WHAT THE GUARD CAN SEE, stated plainly because a guard trusted past its reach
# is worse than none. Its population is every list whose `kind` string mentions
# television — 62 lists today, TVISH below. `kind` is a medium word on every
# list in the catalogue (CLU-510 measured all 27 values and none of them names a
# genre), so this can only ever ask "is this a television list", never "is this
# a comedy". Two kinds of list sit outside it on purpose:
#
#   * the 35 lists whose kind is `anime`. An anime comedy is not a sitcom, and
#     the anime chip on the wall is already its shelf. Urusei Yatsura is the
#     live case — a romantic comedy, and weighted, so it could not join a
#     uniformly unweighted strip either.
#   * `mixed` (nasuverse), the one kind naming no medium at all.
#
# The gated list is skipped on its flag and never by name, the way src/build.py
# skips it, so nothing here can tell anyone it exists.
NOT_SITCOM = {
    "avatar": "animated action-adventure",
    "babylon-5": "space opera",
    "battlestar-galactica": "science-fiction drama",
    "black-mirror": "science-fiction anthology",
    "bottle-episodes": "a formal device across 32 shows, not a show",
    "breaking-bad": "crime drama",
    "buffy-angel": "fantasy drama",
    "chainsaw-man": "anime action",
    "childs-play": "horror",
    "chuck": "hour-long action comedy-drama, and weighted in hours",
    "columbo": "crime, feature-length",
    "dc-animation": "a superhero survey of the screen",
    "dc-anthology": "a superhero survey of the screen",
    "deadwood": "western drama",
    "demon-slayer": "anime action",
    "directors": "a box set of filmographies, like this one",
    "doctor-who": "science fiction",
    "expanse": "science fiction",
    "farscape": "science fiction",
    "friday-night-lights": "sports drama",
    "gilmore-girls": "an hour-long comedy-drama, not a half-hour sitcom",
    "gossip-girl": "teen drama",
    "invincible": "animated superhero drama",
    "jackass": "comedy, but unscripted stunts rather than a sitcom",
    "lanterns": "superhero drama",
    "lost": "science-fiction drama",
    "mad-men": "period drama",
    "marvel-animation": "a superhero survey of the screen",
    "matt-johnson": "one director's body of work",
    "mcu-anthology": "a superhero survey of the screen",
    "mst3k": "comedy, but riffed films rather than a situation comedy",
    "muppets": "a film series with a variety show attached",
    "nathan-fielder": "comedy, but unscripted, and one creator's body of work",
    "psych": "hour-long comedy-drama procedural, and weighted in hours",
    "raimi": "one director's body of work",
    "samurai-jack": "animated action",
    "star-trek": "science fiction",
    "star-wars": "space opera",
    "the-sopranos": "crime drama",
    "the-wire": "crime drama",
    "time-loops": "a formal device across films and shows, not a show",
    "tremors": "creature horror, and mostly films",
    "twilight-zone": "science-fiction anthology",
    "twin-peaks": "mystery drama",
    "vampire-diaries": "supernatural teen drama",
    "x-files": "science fiction",
    "yuyu-hakusho": "anime action",
}

# The four Nathan named, and the section he named them for. Asserted rather than
# trusted: the whole card is this sentence, and a refactor that dropped one of
# them would still produce a valid shelf and a wrong one.
BRITISH = ("peep-show", "blackadder", "the-thick-of-it", "fawlty-towers")
BRITISH_SECTION = "British sitcoms"

WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
         7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven",
         12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen",
         16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen",
         20: "twenty"}

YEAR = re.compile(r"\b(?:18|19|20)\d{2}\b")
TVISH = re.compile(r"\btv\b|show|series|episode", re.I)


def read(slug):
    f = PROPS / (slug + ".json")
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def facts(slug):
    """Everything the row says, read out of the target itself."""
    d = read(slug)
    if d is None:
        return None
    items = [x for sec in d["sections"] for x in sec["items"]]
    # Assert the premise the whole shelf rests on rather than trusting it. One
    # weighted sitcom list appearing later turns the strip into the mix
    # build.py refuses, and the generator should be where that is discovered.
    weighted = [x["id"] for x in items if "w" in x]
    assert not weighted, \
        "%s weights rows (%s ...) — a door into it would derive a real " \
        "weight and the strip could no longer carry the unweighted ones" \
        % (slug, ", ".join(weighted[:3]))
    core = [x for x in items if not x.get("opt")]
    # build.py fails a door whose target has no non-optional row, because
    # nothing could ever complete it and the roll-up would never fire.
    assert core, "%s has no non-optional rows — nothing could complete it" % slug
    nopt = len(items) - len(core)
    unit = (d.get("unit") or {}).get("many", "entries")
    note = ("%d %s" % (len(core), unit) if not nopt
            else "%d + %d optional" % (len(core), nopt))
    span = (d.get("year") or "").strip()
    years = [int(y) for y in YEAR.findall(span)]
    return {"title": d["title"], "n": span, "note": note, "unit": unit,
            "first": years[0] if years else 9999,
            "last": years[-1] if years else 0,
            # "2011–" means still running, and the shelf's own span has to stay
            # open if any door behind it is
            "open": bool(re.search(r"[–-]\s*$", span))}


def audit_the_catalogue(mine):
    """Refuse to run while any television list is neither a door nor excluded."""
    tv, claimed = set(), {}
    for f in sorted(PROPS.glob("*.json")):
        if f.name in ("index.json", "search.json"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("secret") or d.get("generate"):
            continue
        if TVISH.search(d.get("kind") or "") and d.get("slug") != "sitcoms":
            tv.add(d["slug"])
        # A list can hang under one row only — build.py fails a second parent
        # outright, because a tick would roll into two places. Cheaper to find
        # here than in a build this agent is not allowed to run.
        for sec in d.get("sections", []):
            for x in sec.get("items", []):
                ptr = x.get("into") or x.get("beside")
                if ptr and d.get("slug") != "sitcoms":
                    claimed[ptr] = "%s row %s" % (d["slug"], x["id"])

    loose = sorted(tv - set(mine) - set(NOT_SITCOM))
    if loose:
        raise SystemExit(
            "television list(s) accounted for nowhere: %s — put each on the "
            "shelf or in NOT_SITCOM with the reason it is not a sitcom"
            % ", ".join(loose))
    stale = sorted((set(mine) | set(NOT_SITCOM)) - tv)
    if stale:
        raise SystemExit("named here but not a television list any more: %s"
                         % ", ".join(stale))
    taken = sorted("%s (already %s)" % (s, claimed[s]) for s in mine
                   if s in claimed)
    if taken:
        raise SystemExit("already the close-up of another list: %s"
                         % ", ".join(taken))


def main():
    mine = [s for _, _, _, ss in SECTIONS for s in ss]
    assert len(mine) == len(set(mine)), "a slug is on the shelf twice"
    audit_the_catalogue(mine)

    rows_by_sec, missing, total = [], [], 0
    allf = []
    for sid, stitle, sub, slugs in SECTIONS:
        items = []
        for slug in slugs:
            f = facts(slug)
            if f is None:
                missing.append(slug)
                continue
            total += 1
            allf.append(f)
            items.append({
                # permanent, and deliberately the target's own slug: an id
                # derived from a title would move the day a list is retitled,
                # and a moved id destroys everyone's ticks
                "id": "sit-" + slug,
                "t": f["title"],
                "n": f["n"],
                "note": f["note"],
                "into": slug,
            })
        items.sort(key=lambda x: facts(x["into"])["first"])
        rows_by_sec.append((sid, stitle, sub, items))

    if missing:
        raise SystemExit("no property file for: %s" % ", ".join(missing))

    # Nathan's sentence, checked rather than assumed.
    brit = [s for sid, st, _, ss in rows_by_sec if st == BRITISH_SECTION
            for s in [x["into"] for x in ss]]
    assert brit, "no section titled %r" % BRITISH_SECTION
    assert set(brit) == set(BRITISH), \
        "the %r section must hold exactly %s, holds %s" \
        % (BRITISH_SECTION, sorted(BRITISH), sorted(brit))

    # The shelf's span is the union of the spans behind it, so it cannot
    # disagree with them the way a typed range would.
    span = "%d–%s" % (min(f["first"] for f in allf),
                      "" if any(f["open"] for f in allf)
                      else max(f["last"] for f in allf))

    prop = {
        "slug": "sitcoms",
        "title": "Sitcoms",
        "subtitle": "%d sitcoms, each its own list" % total,
        "kind": "tv",
        "year": span,
        # POPULARITY.md, the 90-100 band: "household name well outside its own
        # audience". The sitcom is one in the plainest sense — the word needs no
        # explaining to anybody — so the shelf sits with Marvel Comics at 90,
        # a tie the build breaks on title and which POPULARITY.md calls legal
        # and expected.
        #
        # AND IT DELIBERATELY SITS BELOW ONE OF ITS OWN DOORS. The Marvel shelf
        # reasoned that "a hub should sit above the lists it opens"; that rule
        # was read off a shelf whose best-known child was 87, and it does not
        # survive a child like The Simpsons at 93. POPULARITY.md says this
        # number is the footprint of the underlying work, not a shelf's rank
        # over its own contents, and no genre word is better known than the most
        # famous show standing on it. Nothing is buried by the tie either: a box
        # set is drawn in its own row above the wall, so this never appears
        # beside The Simpsons to be outranked by it.
        "popularity": 90,
        "unit": {"one": "show", "many": "shows"},
        "verb": {"base": "watch", "ing": "watching", "past": "watched"},
        "accent": "#B5771A",
        "accentDark": "#E8B23C",
        # spelled rather than printed as a digit: a blurb is prose and
        # "15 sitcoms" reads as a table cell. Derived either way, so the
        # sentence still cannot disagree with the shelf.
        "blurb": "%s sitcoms as one list. Each row opens that show's own page, "
                 "and finishing that page ticks the row here."
                 % WORDS.get(total, str(total)).capitalize(),
        "notes": [
            ["Every row is a door.",
             "Hover a row and a loupe appears with a fraction beside it — how "
             "far into that show you already are. Opening it takes you to its "
             "own page, an ordinary list with its own strip, its own schedule "
             "and its own clubs. Nothing about it changes because it is "
             "reachable from here, and every one of these fifteen still has "
             "its own tile in the catalogue."],
            ["Ticking works in both directions.",
             "Marking a row here ticks that whole show, and finishing that "
             "show marks the row here. Unticking a row only takes back the "
             "ticks this page put there — anything you had already marked "
             "yourself stays marked."],
            ["Every mark is the same width, and that is not a shrug.",
             "None of the lists behind this page carries a runtime, because "
             "the episode listings they are read from publish none. So each "
             "door counts one, and Fawlty Towers is drawn as wide as Bob's "
             "Burgers. The episode count sits on each row instead, where it is "
             "a fact rather than a guess at how long you will be — and it is "
             "the number to read before picking one."],
            ["What counts as a sitcom here.",
             "A scripted comedy series with a recurring cast, comedy first. "
             "Which leaves four comedy lists on the site off this shelf on "
             "purpose: Mystery Science Theater 3000 riffs films, Jackass is "
             "unscripted, everything Nathan Fielder made is unscripted and is "
             "his own body of work rather than a show, and the Muppets list is "
             "a film series with a variety show attached. Psych and Chuck are "
             "funny and run an hour, which makes them comedy-dramas and puts "
             "them on the site without putting them here."],
            ["The British four sit together.",
             "Fawlty Towers, Blackadder, Peep Show and The Thick of It shipped "
             "as four separate lists and belong in one section — short series, "
             "years apart, and between them the quickest way onto this shelf. "
             "All four keep their own tiles as well."],
            # The counts on the rows are the LISTS' counts, not the shows'
            # — The Simpsons row reads 226 where the show has passed 800 — and
            # a reader who does not know that reads the shelf wrong. Derived
            # nowhere, because these are the five editorial choices on the
            # pages behind the rows; each is checked against that page's own
            # subtitle before this ships.
            ["Some rows stop short, and each page says why.",
             "The Simpsons here is seasons 1 to 10 and stops there on purpose. "
             "Frasier is the original eleven seasons, not the 2023 revival. The "
             "Office is the American series, which is also why the British "
             "section is four shows and not five — the series it was remade "
             "from is not on clubd yet. Blackadder counts entries rather than "
             "episodes because the specials and the pilot are rows too, and "
             "Futurama's count takes in its four films. Every one of those is "
             "the decision of the page behind the row, and that page argues "
             "for it."],
            ["Television is bigger than this.",
             "There is no Cheers here, no Parks and Recreation, no Always "
             "Sunny, no Curb, no Only Fools and Horses, no Fleabag. Every row "
             "on this page is a list that already exists; the rest are written "
             "down as work still to do, and each will get a row here once it "
             "is built rather than a promise of one now."],
            # Unheaded, last: the colophon (CLU-275 rule 6). A box set's
            # provenance is unusual — it has no sources of its own, only the
            # lists behind it — so the note says that rather than naming a wiki
            # this page never read.
            "Every row is read out of the list it opens. The title, the years "
            "and the count on each row are taken from that list's own file "
            "when the page is built, so nothing here can drift from the page "
            "behind it, and none of it was typed in. The sources are on those "
            "%s pages, each naming its own. What is a judgement, and mine, is "
            "which shows count as sitcoms and how they are grouped."
            % WORDS.get(total, str(total)),
        ],
        "sections": [
            {"id": sid, "title": stitle, "sub": sub, "items": items}
            for sid, stitle, sub, items in rows_by_sec
        ],
    }

    out = P.write(prop)
    print("wrote %s — %d rows across %d sections, span %s"
          % (out.name, total, len(rows_by_sec), span))
    for sid, stitle, sub, items in rows_by_sec:
        fs = [facts(x["into"]) for x in items]
        print("  %-26s %d rows  %d–%s  %s"
              % (stitle, len(items), min(f["first"] for f in fs),
                 "" if any(f["open"] for f in fs)
                 else max(f["last"] for f in fs),
                 ", ".join(x["into"] for x in items)))
        for x, f in zip(items, fs):
            print("      %-22s %-12s %s" % (x["into"], f["n"], f["note"]))
    print("  unweighted by construction: no target carries a `w`, so every "
          "door derives none")
    print("  guard: %d television lists in scope — %d doors, %d named in "
          "NOT_SITCOM" % (total + len(NOT_SITCOM), total, len(NOT_SITCOM)))


if __name__ == "__main__":
    main()
