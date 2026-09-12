#!/usr/bin/env python3
"""Generate properties/ridley-scott.json.

    PYTHONIOENCODING=utf-8 python tools/make_ridley_scott.py

Every feature Ridley Scott has directed and released, in release order — the
rows of the Feature film table in Wikipedia's "Ridley Scott filmography",
every one of which is a bare {{yes}} in the Director column. The table holds
thirty; twenty-nine of them have come out.

WHY SIX SECTIONS, AND WHERE THE LINES FALL

Every division is something a source states, checked below rather than felt:

  * 1977–1985 — the four films with a bare "no" in the filmography's own
    Producer column. He directs these and produces none of them.
  * 1987–1992 — the first producer credits: executive producer on Someone to
    Watch Over Me, full producer on Thelma & Louise and 1492. The boundary is
    literally the first non-"no" cell in that column.
  * 1996–2000 — after the longest break of the career to that point, four
    years. It closes on Gladiator, the last film on the list he did not
    produce.
  * 2001–2010 — from Hannibal on, the Producer column is {{yes}} on every
    remaining row without exception, so this is where that run starts.
  * 2012–2017 — Prometheus and Alien: Covenant, which the Alien franchise's
    own Wikidata item names as parts of it alongside the 1979 film, and four
    others; five of the six went out through 20th Century Fox.
  * 2021–2024 — after the four-year gap that ties 1992–1996 as the longest of
    his career, four films through four different distributors.

THE ALTERNATE CUTS: ONE ROW PER FILM, AND WHY

Five of these films exist in more than one version according to the sources
— Alien, Blade Runner, Legend, Kingdom of Heaven and Napoleon — and Blade
Runner's own article counts seven of itself. None of them gets a second row.

  * A row is a thing to watch and tick. Blade Runner: The Final Cut is not a
    second film to get through, so a second row would either double Blade
    Runner's hours in the total — you do not watch it twice — or have to
    carry w: 0, which mixes weighted and unweighted rows in a weighted list.
  * The tracker pairs film rows across lists by title and year. A row called
    Blade Runner: The Final Cut (2007) would match nothing anywhere and would
    split the tick group this list shares with Criterion and Sight & Sound.
  * So the cut lives in the row note, which names which version the bar is
    measuring and what else exists. That is the honest shape: one film, one
    row, one number, and the number says what it is.

RUNTIMES

All twenty-nine from Wikidata P2047 and nothing else, each gated on a P577
publication year within a year of the filmography's year, and each read at
statement rank — gwlib's reader is rank-blind and takes the longest, which
here would ship Legend's never-released first cut for a film that went out at
89 minutes. The collector's rule, and every value it saw, are in
scratch/ridley/collect.py; the asserts below re-check that the three ambiguous
items still look the way the notes say they do.

Kingdom of Heaven is the one deliberate exception, and it is an editorial
ruling rather than a data one. Nathan, 2026-08-25: the director's cut is the
version to watch, here and on any other list that ever carries the film, and
the bar measures it. So the collector still reads the theatrical 144 by its
own rule and this file overrides it to the 190 Wikidata labels as the
director's cut — one visible line, a number the source already carries, and
the only row on the list that does not measure what played in cinemas.

That ruling is also why one row on this list does not display the film's
title. The Kingdom of Heaven row is titled "Kingdom of Heaven (Director's
Cut)", stated in CUT_TITLES below and asserted before the file is written.
On clubd a cut is its own film: rows pair across lists on normalised title
plus year, so a row that recommends the 190-minute cut while displaying the
bare film name is the same work as the theatrical Kingdom of Heaven wherever
else the catalogue carries it, and ticking one would tick the other. That is
the bug that produced the rule — unticking the E.T. director's cut unticked
E.T. and cost somebody a true record of something they had watched.

It makes this the one deliberate cross-list pair in the catalogue:
best-directors-cuts ships the identical title for the identical year, so those
two rows are the same work on purpose and go on syncing. The assert below
checks that from this end, the way make_best-directors-cuts.py checks its
sibling from the other.

Blade Runner is the deliberate opposite and must not be "fixed" to match: this
list measures the 1982 theatrical release, best-directors-cuts measures The
Final Cut, and those two rows are meant to be different works.

The title was typed into properties/ridley-scott.json by hand in c422a85 and
this generator went on emitting the bare film name, so until CLU-537 a rebuild
would have stripped it back — inside a 279-line indent reformat from the same
commit, where it read as housekeeping. Same accident as CLU-448.

Data:   scratch/ridley/collect.py -> scratch/ridley/ridley_data.json
Accent: scratch/ridley/accent.py
"""
import json
import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop
from gwlib.prop import join_bits, slug

SLUG = "ridley-scott"
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "scratch" / "ridley" / "ridley_data.json"

ALIEN_FRANCHISE = "Q1990792"        # the franchise item, not the 1979 film

# The displayed title of every row on this list that is a CUT rather than the
# release — one of them. Stated rather than derived, because the shipped
# parenthetical is an editorial name and not a string the sources carry, and
# re-asserted against the finished rows before anything is written. See the
# module docstring for why a row recommending a cut has to name it.
CUT_TITLES = {"Kingdom of Heaven": "Kingdom of Heaven (Director's Cut)"}

# The list this one shares a cut row with on purpose.
PAIRED_WITH = "best-directors-cuts"

ERAS = [
    ("first", "The first four", 1977, 1985,
     "A duel picture out of Joseph Conrad, then Alien, Blade Runner and "
     "Legend. The filmography's Producer column is a bare no on all four: he "
     "directs these and produces none of them. Two of the three National Film "
     "Registry inductees on this list are here, and so are three of the five "
     "films the sources say exist in more than one version."),
    ("producing", "The first producer credits", 1987, 1992,
     "The column changes. Someone to Watch Over Me is the first film he takes "
     "any producing credit on — executive producer — and Thelma & Louise and "
     "1492: Conquest of Paradise are the first he produces outright. Three of "
     "the four are American productions; 1492 is a French, Spanish and "
     "British one."),
    ("nineties", "Four years off, then Gladiator", 1996, 2000,
     "Four years between 1492 and White Squall, the longest break of the "
     "career to that point. Two of the three that follow went out through "
     "Buena Vista. Gladiator closes the run, and it is the last film on this "
     "list he did not produce — it also carries the second of his two "
     "camera-operator credits, uncredited this time."),
    ("producer", "Producer on every one", 2001, 2010,
     "Eight films in ten years, and from Hannibal onward the Producer column "
     "is yes on every single row to the end of the list. Six of the eight are "
     "adaptations: Thomas Harris, Mark Bowden, Eric Garcia, Peter Mayle, Mark "
     "Jacobson and David Ignatius in turn."),
    ("prequels", "Back to the Alien films", 2012, 2017,
     "Prometheus arrives thirty-three years after Alien and Alien: Covenant "
     "five years after that; the Alien franchise's Wikidata item names all "
     "three as parts of itself. Five of these six went out through 20th "
     "Century Fox."),
    ("recent", "After the four-year gap", 2021, 2024,
     "Another four-year break, tying 1992 to 1996 as the longest of his "
     "career, and then four films in four years through four different "
     "distributors. 2017 and 2021 are the only years on this list carrying "
     "two Ridley Scott releases each."),
]


# --------------------------------------------------------------------------
# the cross-list overlap, computed rather than remembered
# --------------------------------------------------------------------------
def normt(t):
    """build.py's sync-key normalizer, copied so this generator computes the
    same groups the build will."""
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    t = re.sub(r"[^a-z0-9]+", " ", t).strip()
    return re.sub(r"^(the|a|an) ", "", t)


def year_of(x, n):
    """build.py's year-for-sync rule: the row number when it is a plain year,
    else an explicit y, else the single year named in the note."""
    if re.fullmatch(r"(18|19|20)\d{2}", n):
        return n
    explicit = str(x.get("y", ""))
    if re.fullmatch(r"(18|19|20)\d{2}", explicit):
        return explicit
    found = set(re.findall(r"\b((?:18|19|20)\d{2})\b", x.get("note") or ""))
    return found.pop() if len(found) == 1 else None


def overlaps(keys):
    """{sync key -> [list titles]} for the other film lists already shipped.

    Computed off the catalogue on disk instead of typed, so the note naming
    the shared films cannot quietly go stale, and so a second list arriving
    with one of these films shows up as a diff here.
    """
    out = {}
    for f in sorted((ROOT / "properties").glob("*.json")):
        if f.stem in ("index", "search", SLUG):
            continue
        p = json.loads(f.read_text(encoding="utf-8"))
        if p.get("secret") or "film" not in (p.get("kind") or ""):
            continue
        for s in p.get("sections", []):
            for x in s.get("items", []):
                y = year_of(x, str(x.get("n", "")))
                if not y:
                    continue
                k = normt(x["t"]) + "|" + y
                if k in keys and p["title"] not in out.get(k, []):
                    out.setdefault(k, []).append(p["title"])
    return out


def and_list(names):
    names = list(names)
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


WORDS = ("no", "one", "two", "three", "four", "five", "six", "seven", "eight",
         "nine", "ten", "eleven", "twelve")


def word(n):
    """Small counts read as words in prose; anything bigger stays a numeral."""
    return WORDS[n] if n < len(WORDS) else str(n)


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    table, shorts = data["films"], data["shorts"]

    # ---- the table, and the one row that is not a shipped film -------------
    assert len(table) == 30, len(table)
    assert table[0]["t"] == "The Duellists" and table[0]["year"] == 1977, table[0]
    # The Dog Stars: its own article calls it upcoming and dates it after the
    # day this data was collected, and its Wikidata item carries no runtime at
    # all. Both have to hold for it to stay off; when it releases, this fails.
    pending = [f for f in table if f["upcoming"]]
    assert [f["t"] for f in pending] == ["The Dog Stars"], pending
    dogstars = pending[0]
    assert dogstars["release_date"] > data["collected"], \
        "The Dog Stars has released — add the row and reweigh"
    assert not dogstars["p2047_seen"], \
        "The Dog Stars grew a Wikidata runtime — revisit the exclusion"

    films = [f for f in table if not f["upcoming"]]
    assert len(films) == 29, len(films)
    films.sort(key=lambda f: (f["year"], f["release_date"] or "9999-99-99",
                              f["t"]))
    assert films[-1]["t"] == "Gladiator II" and films[-1]["year"] == 2024, \
        films[-1]
    assert all(f["year"] <= g["year"] for f, g in zip(films, films[1:])), \
        "films are not in release order"
    # the only two years with two films, and the release dates that order them
    doubles = sorted(y for y in {f["year"] for f in films}
                     if sum(1 for f in films if f["year"] == y) > 1)
    assert doubles == [2017, 2021], doubles
    for y in doubles:
        got = [f for f in films if f["year"] == y]
        assert all(a["release_date"] < b["release_date"]
                   for a, b in zip(got, got[1:])), \
            "%d is not in release-date order: %s" % (y, [f["t"] for f in got])
    assert [f["t"] for f in films if f["year"] == 2021] == \
        ["The Last Duel", "House of Gucci"], \
        "The Last Duel came out first; alphabetical order would invert them"

    # ---- runtimes ---------------------------------------------------------
    assert all(f["runtime"] and f["runtime_src"] == "P2047" for f in films), \
        "unweighted row in a weighted list: %s" \
        % [f["t"] for f in films if not f["runtime"]]
    assert all(f["qid"] and f["year_gate"] for f in films), \
        [f["t"] for f in films if not (f["qid"] and f["year_gate"])]
    assert all(f["pubyears"] for f in films), \
        [f["t"] for f in films if not f["pubyears"]]
    # every shipped number is a value that is actually on a statement —
    # nothing averaged, nothing rounded from somewhere else, nothing typed
    assert all(float(f["runtime"]) in {s["amount"] for s in f["p2047_seen"]}
               for f in films), \
        [(f["t"], f["runtime"], [s["amount"] for s in f["p2047_seen"]])
         for f in films
         if float(f["runtime"]) not in {s["amount"] for s in f["p2047_seen"]}]
    assert all(s["unit"] == "Q7727" for f in films for s in f["p2047_seen"]), \
        [(f["t"], s["unit"]) for f in films for s in f["p2047_seen"]
         if s["unit"] != "Q7727"]

    # Three items carry more than one live value, and each is a different
    # shape of the same problem. If any of them changes, the row notes and the
    # runtime note are wrong, so the build stops rather than shipping stale
    # prose about them.
    multi = {f["t"]: f for f in films
             if len({s["amount"] for s in f["p2047_seen"]}) > 1}
    assert set(multi) == {"Blade Runner", "Legend", "Kingdom of Heaven"}, \
        sorted(multi)

    br = multi["Blade Runner"]
    assert sorted(s["amount"] for s in br["p2047_seen"]) == [112.0, 116.0], br
    assert br["runtime"] == 116 and not any(s["parts"] for s in br["p2047_seen"])
    assert [m for m, _ in br["cuts"]] == [117], br["cuts"]
    assert "corroborated" in br["runtime_why"], br["runtime_why"]
    assert br["article"]["versions_claim"].startswith("Seven different versions"), \
        br["article"]["versions_claim"]
    assert "only version over which Scott retained artistic control" in \
        br["article"]["lead"], br["article"]["lead"]

    lg = multi["Legend"]
    assert sorted(s["amount"] for s in lg["p2047_seen"]) == [114.0, 125.0], lg
    assert lg["runtime"] == 114, lg["runtime"]
    # the 114 is the one Wikidata itself labels a director's cut, and the
    # article states the same three lengths the row note names
    assert [s["part_labels"] for s in lg["p2047_seen"] if s["amount"] == 114.0] \
        == [["director's cut"]], lg["p2047_seen"]
    assert lg["cuts"] == [[89, "US version"], [93, "European version"],
                          [114, "director's cut"]], lg["cuts"]

    koh = multi["Kingdom of Heaven"]
    labelled = {s["amount"]: "/".join(s["part_labels"])
                for s in koh["p2047_seen"]}
    assert labelled == {144.0: "theatrical version",
                        190.0: "director's cut"}, labelled
    assert koh["runtime"] == 144, koh["runtime"]
    # Nathan's ruling, 2026-08-25: Kingdom of Heaven means the director's cut,
    # here and on any future list that carries the film, and the bar measures
    # that cut rather than the theatrical release. It is the one row on this
    # list that does not measure what played in cinemas, and that is the point
    # — the theatrical version is the one nobody recommends. The collector
    # still picks the theatrical value by its own rule; the override lives
    # here, in one visible place, and uses a number Wikidata already carries
    # and labels itself. Nothing is typed in.
    koh["runtime"] = int(max(labelled))
    assert koh["runtime"] == 190, koh["runtime"]

    # Napoleon carries one Wikidata value but its article states two lengths;
    # that is the fourth film whose row note has to name a cut.
    nap = next(f for f in films if f["t"] == "Napoleon")
    assert [m for m, _ in nap["cuts"]] == [157, 205], nap["cuts"]
    assert nap["cuts"][1][1].lower() == "director's cut", nap["cuts"]
    assert nap["runtime"] == 158, nap["runtime"]

    # Alien has one value and one stated length, but its own article carries a
    # Director's Cut section; it is the fifth noted film for that reason.
    al = next(f for f in films if f["t"] == "Alien")
    assert al["article"]["version_heads"] == ["Director's Cut"], \
        al["article"]["version_heads"]
    assert al["runtime"] == 117 and len(al["p2047_seen"]) == 1

    # Four rows where the single Wikidata value and the article's single
    # stated length differ by more than a minute. One source, kept to — but
    # named, so nobody has to discover it.
    # Kingdom of Heaven sits out of this check on purpose: its article states
    # one length, the theatrical 144, and the row deliberately measures the
    # 190-minute cut instead. That is the ruling above, not a source
    # disagreement, so counting it here would bury a decision among accidents.
    drift = [f for f in films
             if f is not koh
             and not any(abs(f["runtime"] - m) <= 1 for m, _ in f["cuts"])]
    assert {f["t"] for f in drift} == \
        {"Someone to Watch Over Me", "1492: Conquest of Paradise",
         "White Squall", "Matchstick Men"}, [f["t"] for f in drift]
    assert all(len(f["cuts"]) == 1 for f in drift), \
        "a drifting row also has more than one stated length"

    # ---- what the era intros claim ----------------------------------------
    by_year = {f["year"]: f for f in films if f["year"] not in doubles}
    first4 = [f for f in films if f["year"] <= 1985]
    assert len(first4) == 4 and all(f["producer_cell"] == "{{no}}"
                                    for f in first4), \
        [(f["t"], f["producer_cell"]) for f in first4]
    assert by_year[1977]["article"]["based_on"] == "Joseph Conrad", \
        by_year[1977]["article"].get("based_on")
    registry = [f for f in films if "National Film Registry" in f["tablenote"]]
    assert [f["t"] for f in registry] == \
        ["Alien", "Blade Runner", "Thelma & Louise"], [f["t"] for f in registry]
    assert len([f for f in registry if f["year"] <= 1985]) == 2, registry
    # the films whose sources give more than one length: the three items with
    # two P2047 values, plus the two whose own article states more than one
    # (Napoleon) or carries a whole section about a second cut (Alien). These
    # five, and only these five, get a cut named on the row.
    manycut = [f for f in films
               if len({s["amount"] for s in f["p2047_seen"]}) > 1
               or len(f["cuts"]) > 1 or f["article"].get("version_heads")]
    assert [f["t"] for f in manycut] == \
        ["Alien", "Blade Runner", "Legend", "Kingdom of Heaven",
         "Napoleon"], [f["t"] for f in manycut]
    assert len([f for f in manycut if f["year"] <= 1985]) == 3, manycut

    # the first non-"no" producer cell in the whole run, and what it says
    first_credit = next(f for f in films if f["producer_cell"] != "{{no}}")
    assert first_credit["t"] == "Someone to Watch Over Me", first_credit["t"]
    assert first_credit["exec_produced"] and not first_credit["produced"], \
        first_credit["producer_cell"]
    era2 = [f for f in films if 1987 <= f["year"] <= 1992]
    assert len(era2) == 4, [f["t"] for f in era2]
    assert [f["t"] for f in era2 if f["produced"]] == \
        ["Thelma & Louise", "1492: Conquest of Paradise"], \
        [f["t"] for f in era2 if f["produced"]]
    us = [f for f in era2 if "United States" in f["article"].get("country", "")]
    assert len(us) == 3 and by_year[1992] not in us, [f["t"] for f in us]
    for c in ("France", "Spain", "United Kingdom"):
        assert c in by_year[1992]["article"]["country"], \
            by_year[1992]["article"]["country"]

    # the four-year gaps, and that they are the two longest
    gaps = [(b["year"] - a["year"], a["year"], b["year"])
            for a, b in zip(films, films[1:]) if b["year"] > a["year"]]
    assert max(g for g, _, _ in gaps) == 4, gaps
    fours = sorted((lo, hi) for g, lo, hi in gaps if g == 4)
    assert fours == [(1992, 1996), (2017, 2021)], fours
    assert max(g for g, lo, _ in gaps if lo <= 1992) == 4, \
        "1992-1996 is not the longest break to that point"

    era3 = [f for f in films if 1996 <= f["year"] <= 2000]
    assert len(era3) == 3, [f["t"] for f in era3]
    bv = [f for f in era3 if "Buena Vista" in f["article"].get("distributor", "")]
    assert [f["t"] for f in bv] == ["White Squall", "G.I. Jane"], \
        [f["t"] for f in bv]
    # Gladiator is the last row that is not a plain {{yes}} producer credit
    notyes = [f for f in films if f["producer_cell"] != "{{yes}}"]
    assert notyes[-1]["t"] == "Gladiator" and notyes[-1]["year"] == 2000, \
        notyes[-1]["t"]
    assert all(f["produced"] for f in films if f["year"] >= 2001), \
        [f["t"] for f in films if f["year"] >= 2001 and not f["produced"]]
    camera = [f for f in films if "camera operator" in f["tablenote"]]
    assert [f["t"] for f in camera] == ["The Duellists", "Gladiator"], \
        [f["t"] for f in camera]
    assert "uncredited" in camera[1]["tablenote"] and \
        "uncredited" not in camera[0]["tablenote"], \
        [f["tablenote"] for f in camera]

    era4 = [f for f in films if 2001 <= f["year"] <= 2010]
    assert len(era4) == 8, [f["t"] for f in era4]
    adapted = [f for f in era4 if f["article"].get("based_on")]
    assert [f["article"]["based_on"] for f in adapted] == \
        ["Thomas Harris", "Mark Bowden", "Eric Garcia", "Peter Mayle",
         "Mark Jacobson", "David Ignatius"], \
        [(f["t"], f["article"].get("based_on")) for f in era4]

    era5 = [f for f in films if 2012 <= f["year"] <= 2017]
    assert len(era5) == 6, [f["t"] for f in era5]
    franchise = next(e for e in data["sweep_extras"]
                     if e["qid"] == ALIEN_FRANCHISE)
    assert "franchise" in franchise["desc"], franchise["desc"]
    inside = [f for f in films if f["qid"] in franchise["parts"]]
    assert [f["t"] for f in inside] == \
        ["Alien", "Prometheus", "Alien: Covenant"], [f["t"] for f in inside]
    assert by_year[2012]["year"] - by_year[1979]["year"] == 33
    assert next(f for f in films if f["t"] == "Alien: Covenant")["year"] - \
        by_year[2012]["year"] == 5
    fox = [f for f in era5
           if "20th Century Fox" in f["article"].get("distributor", "")]
    assert len(fox) == 5 and "All the Money in the World" not in \
        [f["t"] for f in fox], [f["t"] for f in fox]

    era6 = [f for f in films if f["year"] >= 2021]
    assert len(era6) == 4, [f["t"] for f in era6]
    dists = [f["article"]["distributor"].split(",")[0].split("(")[0].strip()
             for f in era6]
    assert len(set(dists)) == 4, dists

    # ---- what is not here -------------------------------------------------
    assert len(shorts) == 5, len(shorts)
    weightable = [s for s in shorts if s["runtime"]]
    assert [s["t"] for s in weightable] == ["Boy and Bicycle"], weightable
    assert [s["t"] for s in shorts if not s["qid"]] == \
        ["Thunder Perfect Mind", "The Crossing", "The Journey", "Behold"], \
        [s["t"] for s in shorts]
    crossing = next(s for s in shorts if s["t"] == "The Crossing")
    assert "Alien: Covenant" in crossing["tablenote"], crossing["tablenote"]
    tv = data["television"]
    lost = [e for e in tv["Director"] if "- lost" in e]
    assert len(tv["Director"]) == 7 and len(lost) == 5, \
        (len(tv["Director"]), len(lost))
    ep = " ".join(data["exec_producer_only"]) + " " + \
        " ".join(tv["Executive producer"])
    assert "Raised by Wolves (also directed 2 episodes)" in ep and \
        "Dope Thief (also directed pilot episode)" in ep, tv["Executive producer"]
    assert len(data["producer_only"]) == 23 and \
        len(data["exec_producer_only"]) == 24, \
        (len(data["producer_only"]), len(data["exec_producer_only"]))
    assert data["producer_only"][0].startswith("The Browning Version") and \
        "Alien: Romulus" in " ".join(data["producer_only"]), \
        data["producer_only"][:2]
    # the P57 sweep found one feature-length thing the filmography's own
    # tables do not list, and Wikidata's own description says what it is
    anthology = next(e for e in data["sweep_extras"]
                     if e["label"] == "All the Invisible Children")
    assert "anthology film directed by" in anthology["desc"], anthology["desc"]
    directors = [n for n in re.split(r",\s*|\s+&\s+|\s+and\s+",
                                     anthology["desc"].split("directed by")[1])
                 if n.strip()]
    assert len(directors) == 8 and "Ridley Scott" in directors, directors

    # ---- row notes: every one of them read out of the data above ----------
    def note_for(f):
        bits = []
        if f in registry:
            y = re.search(r"in (\d{4})", f["tablenote"]).group(1)
            bits.append("In the National Film Registry since %s" % y)
        if f in camera:
            bits.append("Scott also operated camera, uncredited"
                        if "uncredited" in f["tablenote"]
                        else "Scott also operated camera")
        if f["t"] == "Alien":
            bits.append("The bar is the 1979 release; a director's cut "
                        "followed in 2003")
        elif f["t"] == "Blade Runner":
            n = br["article"]["versions_claim"].split()[0]
            bits.append("%s versions of the film exist. The bar is the "
                        "1982 theatrical one; The Final Cut of 2007 is the "
                        "only version Scott controlled" % n)
        elif f["t"] == "Legend":
            bits.append("The bar is the %d-minute director's cut, the only "
                        "released length Wikidata records; the film went out "
                        "at %d minutes in America and %d in Europe"
                        % (lg["runtime"], lg["cuts"][0][0], lg["cuts"][1][0]))
        elif f["t"] == "Kingdom of Heaven":
            bits.append("Watch the %d-minute director's cut, not the "
                        "%d-minute theatrical release — the bar measures the "
                        "cut" % (koh["runtime"], int(min(labelled))))
        elif f["t"] == "Napoleon":
            bits.append("The bar is the theatrical release; a %d-minute "
                        "director's cut also exists" % nap["cuts"][1][0])
        return join_bits(*bits)

    # ---- sections ---------------------------------------------------------
    sections = []
    for key, title, lo, hi, intro in ERAS:
        got = [f for f in films if lo <= f["year"] <= hi]
        assert got, key
        items = []
        for f in got:
            # the id keys on the FILM and never on the displayed title,
            # because an id is where a tick is stored
            it = {"id": "rs-%d-%s" % (f["year"], slug(f["t"])),
                  "t": CUT_TITLES.get(f["t"], f["t"]), "n": str(f["year"]),
                  "w": round(f["runtime"] / 60.0, 2)}
            n = note_for(f)
            if n:
                it["note"] = n
            items.append(it)
        sections.append({
            "id": key, "title": title,
            "sub": "%d–%d · %d films · %d hours"
                   % (got[0]["year"], got[-1]["year"], len(got),
                      round(sum(f["runtime"] for f in got) / 60.0)),
            "intro": intro, "items": items})
    sections[0]["open"] = True

    placed = sum(len(s["items"]) for s in sections)
    assert placed == len(films), (placed, len(films))
    for s in sections:
        assert all(a["n"] <= b["n"] for a, b in zip(s["items"], s["items"][1:])), \
            "%s is out of year order" % s["title"]
    # ---- the cut name, re-asserted on every run ---------------------------
    # A row that recommends a cut has to display the cut. Checked against the
    # finished rows rather than against the table, because a table nothing
    # reads is what CLU-537 actually was: the title existed in the shipped
    # JSON and the generator never emitted it.
    shipped = {x["id"]: x["t"] for sec in sections for x in sec["items"]}
    # The table is not optional and it is not a free list. Exactly the rows
    # whose bar measures a cut rather than the release have to name that cut,
    # and Kingdom of Heaven is the only row on this list where that is true —
    # it is the one runtime overridden above, from the theatrical 144 to the
    # 190 Wikidata labels a director's cut. Asserting the SET means deleting
    # the entry fails the build instead of quietly restoring the bare film
    # name, which is the whole of CLU-537.
    assert set(CUT_TITLES) == {koh["t"]}, (
        "CUT_TITLES must name exactly the rows whose bar measures a cut: "
        "expected %r, got %r" % ([koh["t"]], sorted(CUT_TITLES)))
    for f in films:
        disp = CUT_TITLES.get(f["t"])
        if not disp:
            continue
        rid = "rs-%d-%s" % (f["year"], slug(f["t"]))
        assert shipped.get(rid) == disp, (
            "%s ships %r, not %r. A row that recommends a cut must name it, "
            "or it shares an identity with the theatrical copy on every "
            "other list and ticking one ticks the other"
            % (rid, shipped.get(rid), disp))
        own_or_extended = (
            (disp.startswith(f["t"] + " (") and disp.endswith(")"))
            or disp.startswith(f["t"] + ": "))
        assert own_or_extended, (
            "%r neither extends %r nor is a released title of its own"
            % (disp, f["t"]))
        assert slug(f["t"]) in rid and disp not in rid, (
            "the id must key on the film, never on the displayed "
            "title: %s" % rid)

    # The one deliberate cross-list pair. best-directors-cuts carries the same
    # film for the same year and must display the same title, or the two rows
    # stop being the same work and the pair breaks from this end without
    # anything on either list looking wrong. Its ids are
    # "<prefix>-<year>-<slug of the film>", the same shape as this list's, so
    # the rows line up on the film rather than on the title under test.
    #
    # Only CUT_TITLES rows are checked, and that is the point: Blade Runner is
    # on both lists and the titles differ ON PURPOSE — theatrical here, The
    # Final Cut there, two different works. Widening this assert to every
    # shared film would demand they match and would be wrong.
    pair = ROOT / "properties" / ("%s.json" % PAIRED_WITH)
    if pair.exists():
        theirs = {tuple(x["id"].split("-", 2)[1:]): x["t"]
                  for sec in json.loads(pair.read_text(encoding="utf-8"))
                  ["sections"] for x in sec["items"]}
        for f in films:
            disp = CUT_TITLES.get(f["t"])
            got = theirs.get((str(f["year"]), slug(f["t"])))
            if not disp or got is None:
                continue
            assert got == disp, (
                "%s: this list ships %r and %s ships %r. The pair holds "
                "only while both rows name the same version"
                % (f["t"], disp, PAIRED_WITH, got))

    noted = {x["t"] for s in sections for x in s["items"] if x.get("note")}
    assert noted == {"The Duellists", "Alien", "Blade Runner", "Legend",
                     "Thelma & Louise", "Gladiator",
                     "Kingdom of Heaven (Director's Cut)",
                     "Napoleon"}, sorted(noted)
    # a row with no `w` in a weighted list is silently worth one hour, and a
    # row at zero would mix the two kinds — neither is allowed here
    rows = [x for s in sections for x in s["items"]]
    assert all(isinstance(x.get("w"), float) and x["w"] > 0 for x in rows), \
        [x["id"] for x in rows if not x.get("w")]

    mins = sum(f["runtime"] for f in films)
    hours = round(sum(x["w"] for x in rows), 2)
    assert abs(hours - mins / 60.0) < 0.2, (hours, mins / 60.0)

    # ---- the films this list shares with other lists here ------------------
    keys = {normt(f["t"]) + "|" + str(f["year"]): f["t"] for f in films}
    shared = overlaps(keys)
    assert len(shared) == 9, sorted(shared)
    by_list = {}
    for k, titles in shared.items():
        for t in titles:
            by_list.setdefault(t, []).append(keys[k])
    assert set(by_list["Alien & Predator"]) == \
        {"Alien", "Prometheus", "Alien: Covenant"}, by_list["Alien & Predator"]
    order = [f["t"] for f in films]
    phrases = [
        "%s on %s" % (and_list(sorted(by_list[t], key=order.index)), t)
        for t in sorted(by_list, key=lambda t: (-len(by_list[t]), t))]
    sharing = ("%s. Ticking one ticks the other: film rows are paired across "
               "lists by title and year, so a film watched here is watched "
               "there. Nothing is duplicated and no hours are counted twice, "
               "because every list totals only its own rows."
               % "; ".join(phrases))

    p = {
        "slug": SLUG,
        "title": "Ridley Scott",
        "subtitle": "the directed features, in release order",
        "kind": "films",
        # Four films most people can name without being told, a fifty-year run
        # still going, and a knighthood — the Kubrick and Scorsese band rather
        # than the Spielberg one, and deliberately a point under the Alien &
        # Predator list this one shares three films with. See POPULARITY.md.
        "popularity": 75,
        "year": "1977–2024",
        "blurb": "Twenty-nine features in release order, The Duellists to "
                 "Gladiator II — about %d hours. The films with famous "
                 "alternate cuts get one row each, with the cut named on the "
                 "row." % round(hours),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        # measured in CIELAB against every accent in properties/index.json —
        # all 272 of them, 136 lists, when this was picked; see
        # scratch/ridley/accent.py. The obvious picks are all spoken for: the
        # Blade Runner street amber lands 10.6 from Ghost in the Shell's, the
        # spinner blue 3.0 from The Office's, the Nostromo green 2.3 from One
        # Pace's, and the cold industrial green IS Alien & Predator's — the
        # list this one shares three films with. This burnt-terracotta pair is
        # the free corner of his own palette, 16.6 from its nearest neighbour
        # (Robin Williams' #8A4A2E) against 18.3 for the freest pair anywhere
        # on the wheel, a magenta with nothing to do with him.
        "accent": "#A67159",
        "accentDark": "#F2B8A6",
        "tiers": False,
        "notes": [
            ["One row per film, cuts and all.",
             "Five of these exist in more than one version according to the "
             "sources — Alien, Blade Runner, Legend, Kingdom of Heaven and "
             "Napoleon — and Blade Runner's own article counts seven of "
             "itself. "
             "None of them gets a second row. A row is something to watch and "
             "tick, and The Final Cut is not a second film to get through: a "
             "second row would either double that film's hours or have to "
             "carry no weight at all, and this list has no unweighted rows in "
             "it. So the cut is named on the row instead, and the note says "
             "which version the bar is measuring."],
            ["Bar widths are runtimes, and three of them took a decision.",
             "All 29 come from Wikidata's runtime property, in hours, each "
             "gated on a release year within a year of the filmography's. "
             "Three items carry more than one value. Kingdom of Heaven labels "
             "its two: 144 minutes for the theatrical version and 190 for the "
             "director's cut, and this list takes the director's cut. It is "
             "the one row here that does not measure what played in cinemas, "
             "and that is the point — the long version is the one worth "
             "watching, so it is the one the row recommends and the one the "
             "bar counts. "
             "Blade Runner carries 112 and 116 with nothing to tell them "
             "apart, and Legend carries a labelled 114-minute director's cut "
             "beside an unlabelled 125 — which is neither of the two lengths "
             "it was released at, and which its own article explains as the "
             "first cut Scott assembled before the film was trimmed. For "
             "those two the film's own article decides, because it states the "
             "length of every version that actually came out; the choice is "
             "always between numbers Wikidata already carries, and no number "
             "is ever typed in from somewhere else."],
            ["Four rows where the two sources disagree by a few minutes.",
             "Someone to Watch Over Me, 1492: Conquest of Paradise, White "
             "Squall and Matchstick Men each carry a single Wikidata runtime "
             "that runs three to seven minutes short of the single figure "
             "their own articles give. None of the four has an alternate cut "
             "and nothing says which number is right, so all 29 rows keep to "
             "the one source rather than becoming a blend of two — the same "
             "rule the rest of this catalogue follows."],
            ["The Dog Stars is not here yet.",
             "The filmography's table has thirty rows; this list has 29. The "
             "thirtieth is The Dog Stars, which its own article calls "
             "upcoming and dates to 28 August 2026, and which carries no "
             "published runtime anywhere. It joins the day it comes out."],
            ["Directing only, and features only.",
             "The producing is not here — %d films he produced and %d he "
             "executive produced, from The Browning Version to Alien: "
             "Romulus, are other directors' work. Neither is the television: "
             "%s directing credits, %s of them episodes that no longer exist, "
             "plus the two episodes of Raised by Wolves and the Dope Thief "
             "pilot. Nor the commercials, the 1984 Apple spot included. The "
             "%s short films are out for a plainer reason — %s of them have "
             "no Wikidata item at all and so cannot be weighted, and one of "
             "those, The Crossing, is a prologue to Alien: Covenant, which is "
             "already a row here. All the Invisible Children, which a sweep "
             "of everything Wikidata credits him with directing turned up, is "
             "an anthology feature by %s directors and is not on the "
             "filmography's own feature table."
             % (len(data["producer_only"]), len(data["exec_producer_only"]),
                word(len(tv["Director"])), word(len(lost)),
                word(len(shorts)), word(len(shorts) - len(weightable)),
                word(len(directors)))],
            ["%d of these films are on other lists here." % len(shared),
             sharing],
            "Filmography from Wikipedia's Ridley Scott filmography, read from "
            "the table itself; runtimes from Wikidata, gated on a matching "
            "release year and read at statement rank; the alternate-cut "
            "lengths from the same Wikidata statements and from each film's "
            "own article.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == 29, len(ids)
    print("wrote %s — %d films, %d minutes, %.2f hours"
          % (out.name, len(ids), mins, hours))
    for s in sections:
        print("   %-32s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))
    print("   shared with other lists: %d films — %s"
          % (len(shared),
             "; ".join("%s: %s" % (t, ", ".join(by_list[t])) for t in by_list)))


if __name__ == "__main__":
    main()
