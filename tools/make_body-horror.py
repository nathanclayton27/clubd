#!/usr/bin/env python3
"""Generate properties/body-horror.json.

    python tools/make_body-horror.py

Body horror as a canon: the 19 films a panel of eleven published best-of-body-
horror lists agrees on, in release order, Eraserhead to The Substance. A survey
of a genre, not a filmography — Cronenberg has four rows here and no more claim
on the genre than the count gives him.

The gate
--------
A curated list has no authority except its sources, so this one names them and
then obeys them. Eleven published articles were fetched whole and parsed by
scratch/body-horror/parse_lists.py into scratch/body-horror/votes.json; a film
ships only if **at least three of the eleven name it**. Nothing was added
because it felt right, and nothing that cleared three was dropped.

The panel, largest first:

  * Vulture, "The 25 Goopiest, Grodiest, Gnarliest Body Horror Movies, Ranked"
  * SyFy Wire, "25 body horror movies that made our bones hurt" (via the
    Internet Archive; the syfy.com original is gone)
  * IndieWire, "The 22 Best Body Horror Movies"
  * Creepy Catalog, "The Best Body Horror Movies Ever"
  * BFI, "10 great body horror films"
  * Screen Rant, "10 Best Body Horror Movies Of All Time"
  * Den of Geek, "Body Horror Movies More Disturbing Than The Substance"
  * Mental Floss, "…These 7 Great Body Horror Movies"
  * No Film School, "7 Best Body Horror Movies of All Time"
  * The Week, "The best body horror movies to watch after 'The Substance'"
  * Collider, "Essential Body Horror Movies to Explain the History of the Genre"

A second, differently-shaped check runs against Wikipedia's "List of body
horror media": every one of the 19 is on it. That article answers "is this
body horror at all", which a best-of list assumes rather than argues, and it
is the same kind of cross-read that the FPS canon does with Den of Geek.

Where the gate is weak, said plainly
------------------------------------
Three things are worth a reader's suspicion, and none of them is hidden:

  1. **The panel is small and modern.** Eleven lists, most published after
     2020, all in English. Wikipedia indexes twenty published features for
     first-person shooters; there is no equivalent aggregator for this genre,
     so the panel had to be assembled by hand from what is still online.
  2. **It undercounts animation and non-English cinema.** Akira is named by
     one of the eleven and Tetsuo by seven, which is less a judgement about
     the two films than a fact about who writes these lists. A panel with
     more critics and fewer streaming-guide listicles would seat Akira.
  3. **Two of the eleven are keyed to The Substance** ("more disturbing
     than", "to watch after"), so they exclude it by construction. That
     depresses its count rather than inflating it: it clears the gate on
     three of the nine lists that could have named it.

Two Valnet titles were fetched and are NOT sources, for reasons recorded in
scratch/body-horror/parse_lists.py rather than buried: CBR writes its headings
as sentences with the film's title inside them, and MovieWeb serves only the
bottom half of its own ranking without JavaScript. Collider's "10 Essential
Body Horror Films You Might Not Have Heard Of" was fetched and excluded on
principle — a list that selects for obscurity is the opposite of a canon, and
counting it would have moved films onto this one for being unknown. Of the
eleven that remain, two (Screen Rant, Collider) are Valnet mastheads; collapse
them into a single voice and the roster does not change, which this file
asserts rather than claims.

What the gate threw out
-----------------------
Six films a reader would expect, with their counts:

  * Akira (1988) — one list. See weakness 2.
  * Possession (1981) — one list, at Vulture's number seven.
  * Alien (1979) — one list. The chestburster is body horror; the film is
    filed as science fiction almost everywhere.
  * Scanners (1981) and Raw (2016) — two lists each, one short.
  * Annihilation (2018) — named by none of the eleven.

Shivers, Rabid and Dead Ringers each land on one list or none, which is why
this file holds four Cronenbergs rather than nine. The filmography list is
where the rest of them live.

Runtimes
--------
Every row is weighted, and every weight is the runtime printed in that film's
own Wikipedia infobox, in hours to two decimals. Collected by
scratch/body-horror/collect_films.py, which resolves each article by trying
"<title> (<year> film)", "<title> (film)" and "<title>" and keeping the first
that carries a film infobox dated within a year of the panel's consensus — so
even the article names are derived rather than typed. A missing runtime is an
assertion failure here, not an estimate.

Deliberate overlaps
-------------------
The Thing also sits on the John Carpenter list; The Fly, Videodrome, The Brood
and Crimes of the Future also sit on the Cronenberg one; Eraserhead is on David
Lynch, Titane on the Palme d'Or, Tusk on A24, The Substance on Best Picture,
Altered States on Criterion. That is intended — a survey and a filmography
answer different questions — and the years here are asserted to match those
files so cross-list tick sync groups them.
"""
import json
import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop as P  # noqa: E402

SLUG = "body-horror"
CACHE = P.ROOT / "scratch" / "body-horror"

# the gate: how many of the eleven published lists must name a film
MIN_LISTS = 3
PANEL = 11

ACCENT, ACCENT_DARK = "#B2415F", "#F2879C"

# key, section, note. The count of lists is prepended to each note by main(),
# so the evidence rides on the row and the list can be argued with.
ROSTER = [
    # ------------------------------------------------------------ first wave
    ("Eraserhead", 1977, "first",
     "David Lynch's first feature, cast in 1971 at the AFI Conservatory and "
     "not finished until 1977 — black and white, and scored and sound-"
     "designed by Lynch himself."),
    ("The Brood", 1979, "first",
     "Written by Cronenberg after his own divorce: a psychotherapist's "
     "clinic, a custody fight, and a treatment that turns what a patient "
     "feels into something you can touch."),
    ("Altered States", 1980, "first",
     "Ken Russell filming Paddy Chayefsky's 1978 novel, drawn from John C. "
     "Lilly's isolation-tank research. Chayefsky fell out with Russell and "
     "took his name off the credits."),
    ("The Thing", 1982, "first",
     "John Carpenter at an Antarctic research station. A tenth of the budget "
     "went on Rob Bottin's creature effects; the reviews were bad, and the "
     "reputation was rebuilt on video."),
    ("Videodrome", 1983, "first",
     "Cronenberg on television: a cable programmer chases a pirate signal "
     "that carries nothing but a room and a beating. Rick Baker did the "
     "effects in two months rather than the six he wanted."),
    # ---------------------------------------------------------- effects boom
    ("Re-Animator", 1985, "boom",
     "Stuart Gordon's directorial debut, a Lovecraft story played as farce — "
     "a medical student, a glowing serum and a morgue with a night shift."),
    ("The Fly", 1986, "boom",
     "Cronenberg remaking the 1958 picture as an illness rather than an "
     "accident. Chris Walas and Stephan Dupuis won the Oscar for the makeup."),
    ("Hellraiser", 1987, "boom",
     "Clive Barker adapting his own novella — a puzzle box, and the beings "
     "it summons. Disappointed by earlier adaptations of his work, he took "
     "the directing job himself."),
    ("Street Trash", 1987, "boom",
     "J. Michael Muro's directorial debut: a Brooklyn liquor store finds a "
     "crate of 1920s drink in the cellar and sells it cheap to the men "
     "living rough nearby."),
    ("Society", 1989, "boom",
     "Brian Yuzna's directorial debut, a Beverly Hills satire with Screaming "
     "Mad George as effects designer. It played Cannes in 1989 and had no US "
     "release until 1992."),
    ("Tetsuo: The Iron Man", 1989, "boom",
     "Shinya Tsukamoto's step up from 8mm shorts to 16mm — black and white, "
     "stop-motion, and a score by Chu Ishikawa."),
    # ------------------------------------------------------------- after the
    ("Slither", 2006, "after",
     "James Gunn's directorial debut, a small-town creature picture built to "
     "the shape of the 1980s ones it is answering."),
    ("Teeth", 2007, "after",
     "Written and directed by Mitchell Lichtenstein, and named for the "
     "vagina dentata folk trope its high-school heroine turns out to have."),
    ("American Mary", 2012, "after",
     "Jen and Sylvia Soska's film about a surgical student who, broke, "
     "starts taking clients from the extreme body-modification scene."),
    ("Tusk", 2014, "after",
     "Kevin Smith filming a premise he had improvised on his own podcast — a "
     "podcaster goes to Manitoba to interview a retired sailor."),
    ("Possessor", 2020, "after",
     "Brandon Cronenberg's film about an assassin who carries out her "
     "contracts by possessing other people's bodies, and then struggles to "
     "get back out of one."),
    ("Titane", 2021, "after",
     "Julia Ducournau's second feature and the Palme d'Or of its year — she "
     "is the first woman to have won it outright."),
    ("Crimes of the Future", 2022, "after",
     "Cronenberg in a near future where evolution has sped up and surgery is "
     "staged for an audience. It reuses the title of his own 1970 film and "
     "is not a remake of it."),
    ("The Substance", 2024, "after",
     "Coralie Fargeat's film about a televised fitness star, dropped at "
     "fifty, who takes a black-market drug that grows her a younger double. "
     "The first body horror film nominated for Best Picture."),
]

SECTIONS = [
    ("first", "The first wave", 1977, 1983,
     "Before the genre had a name: the term “body horror” reaches print in a "
     "1983 Philip Brophy essay, the year Videodrome came out. Five films "
     "that make the body itself the thing that goes wrong."),
    ("boom", "The effects boom", 1985, 1989,
     "Five years in which the effects shop was the budget — latex, "
     "prosthetics and stop-motion, from a Lovecraft farce to a Tokyo "
     "apartment shot on 16mm. Then the run stops."),
    ("after", "After the gap", 2006, 2024,
     "Nothing between 1989 and 2006 clears the gate. That is the panel's "
     "verdict rather than a filter, and read top to bottom it makes a claim "
     "worth arguing with: the genre went quiet, came back as comedy, and "
     "from Titane on turned into awards cinema."),
]


WORDS = ("none", "one", "two", "three", "four", "five", "six", "seven",
         "eight", "nine", "ten", "eleven", "twelve")


def word(n):
    """Small counts read as words in the notes; the number is still computed,
    so a changed source moves the prose instead of contradicting it."""
    return WORDS[n] if 0 <= n < len(WORDS) else str(n)


def normt(t):
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    t = re.sub(r"[^a-z0-9]+", " ", t).strip()
    return re.sub(r"^(the|a|an) ", "", t)


def year_in_note(x, n):
    """build.py's rule for a film row's sync year: the `n` field when it is a
    plain year, else the single year in the note, else nothing."""
    if re.fullmatch(r"(18|19|20)\d{2}", n):
        return n
    found = set(re.findall(r"\b((?:18|19|20)\d{2})\b", x.get("note") or ""))
    return found.pop() if len(found) == 1 else None


def overlaps(mine):
    """Every film-kind row in the catalogue that would share a sync group with
    one of ours — checked against the files as they are on disk, because a
    year that disagrees by one silently splits the group."""
    found = {}
    for f in sorted((P.ROOT / "properties").glob("*.json")):
        if f.name in ("index.json", "search.json", "%s.json" % SLUG):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if "film" not in (d.get("kind") or "") or d.get("secret"):
            continue
        for s in d.get("sections", []):
            for x in s.get("items", []):
                key = normt(x["t"])
                if key not in mine:
                    continue
                y = year_in_note(x, str(x.get("n", "")))
                if y and int(y) == mine[key]:
                    found.setdefault("%s|%s|f" % (key, y), []).append(
                        (d["slug"], x["id"]))
    return found


def main():
    votes = json.loads((CACHE / "votes.json").read_text(encoding="utf-8"))
    films = json.loads((CACHE / "films.json").read_text(encoding="utf-8"))
    listing = (CACHE / "List-of-body-horror-media.wiki").read_text(
        encoding="utf-8")

    # ---- the panel is the one this file describes ------------------------
    assert len(votes["sources"]) == PANEL, \
        "the panel is %d lists, this file says %d" % (
            len(votes["sources"]), PANEL)
    sizes = {k: len(v["films"]) for k, v in votes["sources"].items()}
    assert sum(sizes.values()) == 148, \
        "the panel casts %d votes, expected 148" % sum(sizes.values())

    # ---- the gate decides membership, not the roster ---------------------
    gated = {normt(f["title"]): f for f in votes["films"]
             if f["n"] >= MIN_LISTS}
    want = {normt(t) for t, _, _, _ in ROSTER}
    assert set(gated) == want, \
        "roster and gate disagree: %s" % sorted(set(gated) ^ want)
    assert len(ROSTER) == 19, len(ROSTER)

    # collapsing the two Valnet mastheads into one voice must not change it
    def collapsed(lists):
        return len({"valnet" if s in ("screenrant", "collider3") else s
                    for s in lists})
    still = {normt(f["title"]) for f in votes["films"]
             if collapsed(f["lists"]) >= MIN_LISTS}
    assert still == want, \
        "the roster depends on Valnet counting twice: %s" % sorted(still ^ want)

    facts = {normt(f["vote_title"]): f for f in films}
    assert set(facts) == want, \
        "collected facts and roster disagree: %s" % sorted(set(facts) ^ want)

    # ---- the No Film School director pairing, closed against Wikipedia ----
    # Its list prints no years, so "The Fly" was resolved by the director it
    # names. Check that against the infobox of the film that vote landed on.
    fly = facts[normt("The Fly")]
    assert "Cronenberg" in fly["director"] and fly["year"] == 1986, \
        "the undated Fly vote resolved to %r (%s)" % (fly["director"],
                                                      fly["year"])
    assert "nofilmschool" in gated[normt("The Fly")]["lists"], \
        "the resolved Fly vote is missing from the count"

    entries = []
    for title, year, sec, note in ROSTER:
        key = normt(title)
        rec, vote = facts[key], gated[key]
        assert rec["year"] == year, \
            "%s: infobox says %s, roster says %d" % (title, rec["year"], year)
        assert vote["year"] == year, \
            "%s: the panel dates it %s" % (title, vote["year"])
        assert rec["runtime"], "no infobox runtime for %s" % title
        assert 60 <= rec["runtime"] <= 200, \
            "%s runtime %r is not a feature" % (title, rec["runtime"])
        # Genre membership — the second and differently-shaped check. The
        # film must sit on a table row of Wikipedia's list article that
        # links its title AND carries its year, which is stricter than a
        # bare title match: "Society" alone would hit any link containing
        # the word. Two rows are shaped oddly and still pass on their own
        # terms — The Fly is filed under the 1958 original with "the 1986
        # remake" in the notes column, and Hellraiser is filed as a
        # franchise dated "1987–present".
        assert any(re.search(r"\[\[[^\]|]*%s[^\]]*\]\]" % re.escape(title),
                             line) and str(year) in line
                   for line in listing.splitlines()
                   if line.startswith("|") and "||" in line), \
            "%s (%d) is not a dated row of Wikipedia's List of body horror " \
            "media" % (title, year)
        assert MIN_LISTS <= vote["n"] <= PANEL, vote["n"]
        w = round(rec["runtime"] / 60.0, 2)
        assert w > 0, title
        entries.append({
            "id": "bh-%d-%s" % (year, P.slug(title)),
            "t": title, "n": str(year), "w": w, "year": year, "sec": sec,
            "note": P.join_bits("%d of %d lists" % (vote["n"], PANEL), note),
            "lists": vote["n"], "runtime": rec["runtime"],
        })

    years = [e["year"] for e in entries]
    assert years == sorted(years), "the roster is out of release order"
    weighted = [e for e in entries if "w" in e]
    assert len(weighted) == len(entries) == 19, \
        "every row must carry a runtime; %d of %d do" % (len(weighted),
                                                         len(entries))
    total_min = sum(e["runtime"] for e in entries)
    total_h = sum(e["w"] for e in entries)

    # ---- the overlaps have to actually group -----------------------------
    mine = {normt(e["t"]): e["year"] for e in entries}
    groups = overlaps(mine)
    for title, slug in (("The Thing", "carpenter"), ("The Fly", "cronenberg")):
        key = "%s|%d|f" % (normt(title), mine[normt(title)])
        assert any(s == slug for s, _ in groups.get(key, [])), \
            "%s (%d) does not meet %s — the sync group would not form" % (
                title, mine[normt(title)], slug)
    # every list the overlap note names by hand has to be one we really meet
    met = {s for v in groups.values() for s, _ in v}
    named = {"carpenter", "cronenberg", "david-lynch", "criterion",
             "palme-dor", "a24", "best-picture"}
    assert named <= met, \
        "the overlap note names lists we do not group with: %s" % sorted(
            named - met)

    sections = []
    for key, stitle, lo, hi, intro in SECTIONS:
        got = [e for e in entries if e["sec"] == key]
        assert got, "empty section %s" % key
        assert all(lo <= e["year"] <= hi for e in got), \
            "%s holds a film outside %d-%d" % (key, lo, hi)
        sub = " · ".join([
            "%d–%d" % (got[0]["year"], got[-1]["year"]),
            "%d films" % len(got),
            "%d hours" % round(sum(e["runtime"] for e in got) / 60.0)])
        sections.append({
            "id": key, "title": stitle, "sub": sub, "intro": intro,
            "items": [{k: v for k, v in e.items()
                       if k in ("id", "t", "n", "w", "note")} for e in got]})
    sections[0]["open"] = True

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)) == len(ROSTER), (len(ids),)

    # ---- the accent pair is ours alone -----------------------------------
    for f in sorted((P.ROOT / "properties").glob("*.json")):
        if f.name in ("index.json", "search.json", "%s.json" % SLUG):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        assert (d.get("accent"), d.get("accentDark")) != (ACCENT, ACCENT_DARK), \
            "accent pair already used by %s" % d.get("slug")
        assert d.get("accent") != ACCENT, \
            "%s already uses accent %s" % (d.get("slug"), ACCENT)

    by = {normt(e["t"]): e for e in entries}
    top = max(entries, key=lambda e: e["lists"])
    bare = sum(1 for e in entries if e["lists"] == MIN_LISTS)

    # counts for the notes, looked up rather than remembered — a near-miss
    # quoted from memory is exactly the kind of claim this file exists to
    # avoid making
    tally = {normt(f["title"]): f for f in votes["films"]}

    def named_by(title, year):
        f = tally.get(normt(title))
        assert f is None or f["year"] == year, \
            "%s is dated %s in the panel, not %d" % (title, f["year"], year)
        return f["n"] if f else 0

    misses = [("Akira", 1988), ("Possession", 1981), ("Alien", 1979),
              ("Scanners", 1981), ("Raw", 2016), ("Annihilation", 2018)]
    miss_n = {t: named_by(t, y) for t, y in misses}
    assert all(n < MIN_LISTS for n in miss_n.values()), miss_n
    assert miss_n["Annihilation"] == 0, miss_n
    # the two lists that are keyed to The Substance cannot name it
    keyed = ("denofgeek2", "theweek")
    could = PANEL - len(keyed)
    sub = gated[normt("The Substance")]
    assert not (set(sub["lists"]) & set(keyed)), \
        "a Substance-keyed list somehow names The Substance"
    akira = miss_n["Akira"]
    tetsuo = by[normt("Tetsuo: The Iron Man")]["lists"]

    # the 1989–2006 hole is the panel's, not the genre's: count what the
    # Wikipedia list holds from the decade the gate skips entirely
    nineties = sum(1 for line in listing.splitlines()
                   if line.startswith("|") and "||" in line
                   and re.search(r"\|\|\s*199\d", line))
    assert nineties > 20, "only %d 1990s rows on the list article" % nineties
    assert not any(1990 <= e["year"] <= 2005 for e in entries), \
        "the gap note is wrong — something lands in it"
    shortest = min(entries, key=lambda e: e["runtime"])
    longest = max(entries, key=lambda e: e["runtime"])
    cronenbergs = [e for e in entries
                   if facts[normt(e["t"])]["director"] == "David Cronenberg"]
    assert len(cronenbergs) == 4, [e["t"] for e in cronenbergs]

    prop = {
        "slug": SLUG,
        "title": "Body Horror",
        "subtitle": "the films the genre's canon agrees on, in release order",
        "kind": "films",
        # A genre survey, not a franchise. Everyone who watches horror knows
        # the term and most of these titles; almost nobody outside horror
        # does — the 45-55 band in POPULARITY.md. Set at the brief's 50, one
        # below Zombie Films' neighbours and beneath the Cronenberg
        # filmography it overlaps, per that file's second signal.
        "popularity": 50,
        # A canon, like the Cronenberg list beside it — a shape of film,
        # not a sequence anyone is meant to work through
        # (Nathan, CLU-372, approved 2026-08-27). Prerequisites, where any
        # exist, live in tools/data/sequences.json and are enforced separately.
        "random": True,
        "year": "1977–2024",
        "blurb": "Every film here is named by at least three of eleven "
                 "published best-of-body-horror lists, Eraserhead to The "
                 "Substance — about %d hours, in the order they came out."
                 % round(total_h),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": ACCENT,
        "accentDark": ACCENT_DARK,
        "tiers": False,
        "notes": [
            ["The gate, and the eleven lists behind it.",
             "A film is here only if at least three of eleven published "
             "best-of-body-horror articles name it: Vulture, SyFy Wire, "
             "IndieWire, Creepy Catalog, the BFI, Screen Rant, Den of Geek, "
             "Mental Floss, No Film School, The Week and Collider. Each was "
             "read in full and counted rather than summarised. Every one of "
             "the %d also appears on Wikipedia's “List of body horror "
             "media”, which is the separate question of whether a film is "
             "body horror at all. %s leads with %d of the eleven, and %s "
             "rows clear the gate with exactly three — the count sits on "
             "every row, so you can argue with it."
             % (len(entries), top["t"], top["lists"], word(bare))],
            ["The gate is small, and it shows.",
             "There is no aggregator for this genre the way Wikipedia keeps "
             "one for first-person shooters, so the panel was assembled by "
             "hand from what is still online: eleven lists, most published "
             "since 2020, all in English. That undercounts animation and "
             "non-English work — Akira is named by %s of the eleven and "
             "Tetsuo: The Iron Man by %s, which says more about who writes "
             "these lists than about either film. Two of the eleven are also "
             "keyed to The Substance (“more disturbing than”, “to watch "
             "after”) and so cannot name it; it clears the gate on %s of the "
             "%s that could."
             % (word(akira), word(tetsuo), word(sub["n"]), word(could))],
            ["%s names a reader will miss." % word(len(misses)).capitalize(),
             "Akira (1988), Possession (1981) and Alien (1979) are named by "
             "%s list each; Scanners (1981) and Raw (2016) by %s apiece, one "
             "short; Annihilation (2018) by none of the eleven. Following "
             "the sources when they are inconvenient is the whole point of "
             "naming them, and it is also why Cronenberg has four rows here "
             "rather than nine — Shivers, Rabid and Dead Ringers do not "
             "clear three lists, and the filmography is where the rest of "
             "them live."
             % (word(miss_n["Akira"]), word(miss_n["Raw"]))],
            ["Seventeen years with nothing in them.",
             "The gate puts %d films between 1977 and 1989 and then nothing "
             "at all until Slither in 2006. The genre did not stop — "
             "Wikipedia's list of body horror media carries %d titles from "
             "the 1990s alone — but not one of them is named by three of "
             "these eleven lists. Read top to bottom it makes a claim worth "
             "arguing with: that body horror is a practical-effects art "
             "form, and that it went quiet for as long as the effects did."
             % (sum(1 for e in entries if e["year"] <= 1989), nineties)],
            ["The same film can sit on two lists here, and should.",
             "The Thing is also on John Carpenter; The Fly, Videodrome, The "
             "Brood and Crimes of the Future are also on Cronenberg; "
             "Eraserhead is on David Lynch, Altered States on Criterion, "
             "Titane on the Palme d'Or, Tusk on A24 and The Substance on "
             "Best Picture. A survey of a genre and a filmography answer "
             "different questions, so both hold the row — and ticking it in "
             "one place ticks it in the other."],
            ["Bar widths are runtimes.",
             "All %d rows are weighted, and every weight is the runtime "
             "printed in that film's own Wikipedia infobox — %s at %d "
             "minutes is the shortest, %s at %d the longest, %d hours in "
             "total. No runtime was estimated; a missing one stops the "
             "generator." % (len(entries), shortest["t"],
                             shortest["runtime"], longest["t"],
                             longest["runtime"], round(total_h))],
            "Contents from eleven published best-of-body-horror lists "
            "(Vulture, SyFy Wire, IndieWire, Creepy Catalog, BFI, Screen "
            "Rant, Den of Geek, Mental Floss, No Film School, The Week, "
            "Collider), cross-read against Wikipedia's “List of body horror "
            "media”; runtimes from each film's Wikipedia infobox.",
        ],
        "sections": sections,
    }

    P.write(prop)

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d films — all weighted, %d min (%.1f hours)"
          % (len(sections), len(ids), total_min, total_h))
    print("  gate: >=%d of %d published lists; %d votes across %d films"
          % (MIN_LISTS, PANEL, sum(sizes.values()), len(votes["films"])))
    for s in sections:
        print("   %-18s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))
    print("  sync groups these rows would join:")
    for k in sorted(groups):
        if groups[k]:
            print("   %-34s %s" % (k, ", ".join(s for s, _ in groups[k])))
    assert by  # keeps the by-title index honest if a note starts using it


if __name__ == "__main__":
    main()
