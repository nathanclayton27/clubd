#!/usr/bin/env python3
"""Generate properties/worst-directors-cuts.json.

    python tools/make_worst-directors-cuts.py

The sibling of best-directors-cuts: five films where the later cut is the one
NOT to watch. The list works as a tracker because these are films you have
almost certainly seen — ticking a row is "seen it, and now I know which
version to avoid", not a viewing plan.

The gate
--------
Same shape as the best list and the same corpus: a film gets a row only if
**English Wikipedia says, in a sentence you can point at, that the later cut
landed worse than the release it replaced** — the added material panned, a
documented view that the original is the better film, or the people who made
it distancing themselves from the new version. The sentence may come from the
film's own article, the article about the cut, or Wikipedia's "Director's cut"
page.

Where the day-one reviews and the settled view disagree, the settled view
wins. That rule exists because of the crown jewel. *Donnie Darko: The
Director's Cut* opened to BETTER notices than the 2001 release — Metacritic 88
against 71, Ebert going from two and a half stars to three — and Wikipedia
still carries a section headed "Retrospective reviews" that opens
"Retrospective reviews of the director's cut have been more negative", lists
four critics saying the cut is the lesser film, and notes on the main article
that "many hardcore fans of the film tend to favor the theatrical cut". These
lists are advice about what to watch now, so the retrospective verdict governs
and the launch-week aggregate does not.

Every row carries its verdict and the paragraph it came from in
tools/data/directors-cuts.json, and this generator re-asserts on every run
that the quote is still there. scratch/agent-cuts/ holds the collector.

Why there are only five
-----------------------
Because the gate is real. The famous names that failed it:

  * Apocalypse Now (1979) — Redux holds 93% on Rotten Tomatoes and 92 on
    Metacritic in the article's own reporting. The consensus it quotes says
    "some say the new cut is inferior to the original", hedged, and one critic
    is quoted against it. A cut that scored 93% is not a cut that landed
    worse, whatever anyone remembers. Coppola trimmed twenty minutes of the
    Redux material back out for his 2019 Final Cut, which is the closest thing
    to an admission, but the gate asks about reception.
  * The Exorcist (1973) — the 2000 "Version You've Never Seen" scores HIGHER
    than the original on the aggregator the article cites, 88% against 78%.
  * Léon: The Professional (1994) — no comparative verdict at all, and Besson
    calls the ORIGINAL release the director's cut and the longer one "The
    Long Version".
  * Alien (1979) — Ridley Scott says the theatrical release was his cut and
    the 2003 one is called a director's cut "for marketing purposes", but the
    article says critical interest was re-ignited by it.
  * Superman II (1980) — the article documents a genuine three-way split on
    the Donner Cut, not a verdict.
  * The Warriors, Natural Born Killers, The Butterfly Effect, Rebel Moon,
    Highlander II — a cut exists and the article never compares its reception
    to the release's.

Hours
-----
This list ships UNWEIGHTED, on purpose and by the rule. Weighting is
all-or-nothing, and three of these five cuts have no published runtime
anywhere in Wikipedia or Wikidata: the 1997 Star Wars Special Edition, the
2002 E.T. anniversary version and the 2002 Amadeus Director's Cut. Guessing
one is not an option, and it would be a strange bar anyway — it would measure
the version you are being told to skip.

Titles, and why they are stated rather than derived
---------------------------------------------------
A row here displays the CUT's title, never the film's, and that is the whole
reason the list is safe to tick. Cross-list sync keys on normalised title +
year + medium, so a row titled "Star Wars" on a list of cuts would be the same
work as the theatrical Star Wars on every other list. That is not theory: this
list is where it happened. Unticking the E.T. director's cut unticked E.T., and
somebody lost a true record of a film they had actually seen.

The names cannot be computed from the data — Donnie Darko's cut carries its own
release title, the other four are the film plus a parenthetical — so CUT_TITLES
states all five and the build asserts on every run that each is either the
cut's own title or the film's title extended. The bare film name fails the
build. It has to: the titles were once added to the shipped JSON by hand while
this generator went on emitting film names, and a rebuild would have stripped
all five back with a diff that read as a tidy-up (CLU-448).

The YEAR on a row is still the film's ORIGINAL release year, not the cut's; the
cut's year is in the note.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop as P  # noqa: E402

SLUG = "worst-directors-cuts"
SIBLING = "best-directors-cuts"
DATA = pathlib.Path(__file__).resolve().parent / "data" / "directors-cuts.json"

# The displayed title of each row: the title of the CUT, which is what keeps a
# row here from being the same work as the theatrical copy elsewhere in the
# catalogue. Stated, not derived — see the docstring — and checked below. It
# lives here rather than in tools/data/directors-cuts.json because that file is
# collector output (scratch/agent-cuts/build_data.py rewrites it wholesale) and
# an editorial title put there would be lost the next time the cuts are
# re-collected.
CUT_TITLES = {
    "Star Wars": "Star Wars (Special Edition)",
    "E.T. the Extra-Terrestrial":
        "E.T. the Extra-Terrestrial (20th Anniversary Version)",
    "Amadeus": "Amadeus (Director's Cut)",
    "Cinema Paradiso": "Cinema Paradiso (The New Version)",
    "Donnie Darko": "Donnie Darko: The Director's Cut",
}

# The coded half of the gate: a verdict has to actually say worse.
VERDICT = re.compile(
    r"negativ|criticis|criticiz|criticism|panned|worse|lesser|inferior|"
    r"better film than|disown|regret", re.I)


def main():
    doc = json.loads(DATA.read_text(encoding="utf-8"))
    films = doc["films"]
    mine = [f for f in films if f["list"] == "worst"]
    theirs = [f for f in films if f["list"] == "best"]
    assert mine and theirs, "the data file lost one of the two lists"

    # ---- disjointness, twice: the shared data file, then whatever the
    # sibling property actually shipped
    keys = {(f["t"], f["n"]) for f in mine}
    clash = keys & {(f["t"], f["n"]) for f in theirs}
    assert not clash, "on both lists in the data file: %s" % sorted(clash)
    sib = P.ROOT / "properties" / ("%s.json" % SIBLING)
    if sib.exists():
        # keyed on the ROW ID, not the displayed title: both lists now title a
        # row with the cut rather than the film, so comparing film names
        # against what shipped would compare two different things and never
        # fire. The id is "<prefix>-<year>-<slug of the film>" on both lists.
        other = json.loads(sib.read_text(encoding="utf-8"))
        shipped = {tuple(x["id"].split("-", 2)[1:]) for s in other["sections"]
                   for x in s["items"]}
        clash = {(str(n), P.slug(t)) for t, n in keys} & shipped
        assert not clash, "%s already ships: %s" % (SIBLING, sorted(clash))

    # ---- the gate, re-asserted on every run
    for f in mine:
        assert f["quote"] in f["evidence"], \
            "%s: the verdict is no longer in its own evidence" % f["t"]
        assert VERDICT.search(f["quote"]), \
            "%s: %r is not a verdict, it is a description" % (f["t"], f["quote"])
        if f["mins"]:
            assert str(f["mins"]) in f["mins_evidence"], \
                "%s: %d min is not in the text it came from" % (f["t"], f["mins"])

    # the "hours are not tracked" note names the three cuts nobody measures;
    # if that ever stops being true the note is wrong and the build should say so
    unmeasured = sorted(f["t"] for f in mine if not f["mins"])
    assert unmeasured == ["Amadeus", "E.T. the Extra-Terrestrial",
                          "Star Wars"], unmeasured

    # ---- the naming rule, re-asserted on every run. A row on a list ABOUT
    # cuts must display the cut, and a cut's title is either its own release
    # title or the film's title extended. Anything else — the bare film name
    # above all — fails the build rather than shipping a row that shares an
    # identity with the theatrical copy on some other list.
    stray = set(CUT_TITLES) - {f["t"] for f in mine}
    assert not stray, \
        "CUT_TITLES names a film this list does not carry: %s" % sorted(stray)
    for f in mine:
        disp = CUT_TITLES.get(f["t"])
        assert disp, \
            "%s: no cut title. A cuts list must name the cut on the row; " \
            "the bare film name makes it the same work as the theatrical " \
            "copy elsewhere in the catalogue" % f["t"]
        own_title = P.normt(disp) == P.normt(f["cut"])
        extended = (disp.startswith(f["t"] + " (") and disp.endswith(")")) \
            or disp.startswith(f["t"] + ": ")
        assert own_title or extended, \
            "%s: %r names neither the cut (%r) nor the film extended" \
            % (f["t"], disp, f["cut"])

    mine.sort(key=lambda f: (f["n"], P.normt(f["t"])))
    items = []
    for f in mine:
        cut = f["cut"][0].upper() + f["cut"][1:]
        if f["cut_year"]:
            cut = "%s, %d" % (cut, f["cut_year"])
        items.append({
            # the id stays keyed on the FILM, because ids are where ticks are
            # stored; only the displayed title carries the cut
            "id": "wdc-%d-%s" % (f["n"], P.slug(f["t"])),
            "t": CUT_TITLES[f["t"]], "n": str(f["n"]),
            "note": P.join_bits(cut, f["changes"],
                                "%d min" % f["mins"] if f["mins"] else ""),
        })
    assert not any("w" in x for x in items), \
        "this list is unweighted; a stray w would make every other row weigh 1"

    sections = [{
        "id": "cuts", "title": "Watch the original instead",
        "sub": "%d–%d · %d films" % (mine[0]["n"], mine[-1]["n"], len(items)),
        "intro": "Five films and five versions of them to skip. Each note says "
                 "what the cut changes in kind — restored footage, a swapped "
                 "song, altered effects, explanatory text — and not what "
                 "happens, because most of the reason this list is fun is "
                 "that you have already seen these.",
        "open": True, "items": items}]

    prop = {
        "slug": SLUG,
        "title": "Worst Director's Cuts",
        "subtitle": "five films, five versions to skip",
        "kind": "films",
        # Sibling of best-directors-cuts (35) and narrower — five rows against
        # nineteen, and a warning list rather than a watchlist — so it sits
        # just under it, beside Real Time (30) and One Location (28).
        "popularity": 31,
        # A list of versions to avoid, in no particular order — there is
        # nothing to work through
        # (Nathan, CLU-372, approved 2026-08-27). Prerequisites, where any
        # exist, live in tools/data/sequences.json and are enforced separately.
        "random": True,
        "year": "1977–2001",
        "blurb": "%d films whose later cut is the one to avoid, from the Star "
                 "Wars Special Editions to the Donnie Darko director's cut. A "
                 "row exists only where Wikipedia says the cut landed worse."
                 % len(items),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": "#7A2130",
        "accentDark": "#E8737F",
        "tiers": False,
        "notes": [
            ["A list of things not to watch, which is the joke.",
             "You will have seen all five of these. Ticking a row means "
             "“seen it — and I know which version not to go back to”, so the "
             "bar fills up with films you have already enjoyed rather than "
             "homework. Nobody is asking you to sit through the wrong "
             "version to prove a point."],
            ["What earns a row.",
             "Wikipedia has to say, in a sentence you can point at, that the "
             "later cut landed worse than the release it replaced — the added "
             "material panned, a documented view that the original is the "
             "better film, or the people who made it distancing themselves "
             "from it. The verdict and the paragraph around it are stored "
             "with the row and re-checked every time this list is rebuilt. "
             "Films everyone “knows” have a bad cut are not here if their "
             "article does not say so, which is why Apocalypse Now Redux and "
             "the extended Exorcist are missing: both score HIGHER than the "
             "versions they replaced."],
            ["Where the reviews and the verdict disagree, the verdict wins.",
             "Donnie Darko is the case that sets the rule. The 2004 "
             "director's cut opened to better notices than the 2001 release — "
             "Metacritic 88 against 71 — and Wikipedia carries a whole "
             "section headed “Retrospective reviews” that opens “Retrospective "
             "reviews of the director's cut have been more negative”, quotes "
             "four critics calling it the lesser film, and notes that many of "
             "the film's own fans prefer the theatrical cut. This is a list "
             "about what to watch now, so the settled view governs and the "
             "launch-week aggregate does not."],
            ["No hours, and here is why.",
             "Three of these five cuts have no published runtime anywhere in "
             "Wikipedia or Wikidata: the 1997 Star Wars Special Edition, the "
             "2002 E.T. anniversary version, and the 2002 Amadeus Director's "
             "Cut. Weights on a list are all-or-nothing here — one row "
             "without a number would silently count as an hour and skew "
             "everything — and this house never guesses a runtime, so the "
             "list carries none at all. The two that ARE published, Cinema "
             "Paradiso and Donnie Darko, say so on their rows. The sibling "
             "list, Best Director's Cuts, is fully weighted on the length of "
             "the cut."],
            ["One row per film, paired with the rest of the catalogue.",
             "The year on a row is the film's original release year, not the "
             "cut's — the cut's year is in the note — because rows pair "
             "across lists by title and year. Tick Star Wars here and it "
             "ticks in the Star Wars list and in Best Picture; E.T. and "
             "Amadeus pair the same way, and Cinema Paradiso and Donnie "
             "Darko are new to the catalogue. No film appears on both this "
             "list and Best Director's Cuts, and both generators fail the "
             "build if one ever does."],
            "Verdicts read from English Wikipedia — the film articles, the "
            "article on Donnie Darko: The Director's Cut, “Changes in Star "
            "Wars re-releases” and the “Director's cut” page — with runtimes, "
            "where any exist, from the same articles.",
        ],
        "sections": sections,
    }

    P.write(prop)

    print("wrote %s.json" % SLUG)
    print("  %d films, unweighted (%d of them have no published cut runtime)"
          % (len(items), len(unmeasured)))
    print("  gate: a Wikipedia sentence saying the cut landed worse")
    for x in items:
        print("   %-30s %s  %s" % (x["t"], x["n"], x["note"][:64]))


if __name__ == "__main__":
    main()
