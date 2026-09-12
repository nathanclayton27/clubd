#!/usr/bin/env python3
"""Generate properties/eastwood.json.

    PYTHONIOENCODING=utf-8 python tools/make_eastwood.py

Clint Eastwood's features in release order — ONE list, not two. Every film he
directed or starred in is a single row, and the row says which of the two jobs
he did on it. Everything here is machine-read from tools/data/eastwood.json,
collected by scratch/agent-eastwood/collect.py from Wikipedia's "Clint
Eastwood filmography", the "Clint Eastwood" article, and each film's own
article. Nothing is typed in from memory, and every claim the copy makes is
asserted against the data that produced it before anything is written.

ONE LIST, NOT TWO — THE STRUCTURAL DECISION
-------------------------------------------
Splitting the directing from the acting is the obvious move and it is wrong.
It would put *Unforgiven* and *Gran Torino* on two different pages, and a tick
on either would mean half a thing: he directed and starred in both, so both
lists would want the row and neither could own it. Twenty-four of these
sixty-nine films are films he did both jobs on. So there is one row per film,
in release order, with the role on the row — *directed*, *starred*, or both —
and *Dirty Harry* (starred) sits between *Play Misty for Me* (both) and *Joe
Kidd* (starred) because that is the order they came out in.

THE ROSTER RULE, AND WHAT IT LEAVES OUT
---------------------------------------
Every film in the filmography's ==Film== section that he **directed**, plus
every one in which he has a **credited acting role**. That is 69 of the 82
films those tables list between them. The thirteen it leaves out, all named in
the notes on the page:

  * **Eight uncredited appearances.** Seven are the 1955–57 contract-player
    walk-ons — *Revenge of the Creature*, *Tarantula*, *Lady Godiva of
    Coventry*, *Never Say Goodbye*, *Star in the Dust*, *Away All Boats*,
    *Escapade in Japan* — and the eighth is his cameo as himself in *Casper*
    (1995). The source lists all eight and marks every one of them
    "Uncredited" in its own Notes column; that flag is the source
    distinguishing them, and this list follows it. "Starred" has to mean
    something, and an unbilled jet-squadron leader is not a role.
    Two uncredited cameos are NOT excluded — *Breezy* and *American Sniper*,
    because he directed both, so the row exists on directing grounds and the
    note names the cameo.
  * **Four documentary appearances as himself** — *Gary Cooper: American Life,
    American Legend* (1989), *Kurosawa's Way* (2011), *Casting By* (2012),
    *Sad Hill Unearthed* (2017). The table marks each "Documentary film".
    Turning up to talk about somebody else's work is not a film role.
  * **One producer-only credit**, *The Stars Fell on Henrietta* (1995): the
    filmography's Director column says no and he is not in it. Producing is
    not one of the two jobs this list tracks. (*Tightrope* and *Trouble with
    the Curve* are also Director=no, but he stars in both, so both are rows.)

**Television is out**, and the source is why: the filmography keeps it in a
separate ==Television== section, not in ==Film==. That is eleven acting
credits including the eight seasons of *Rawhide*, and two directing credits —
an *Amazing Stories* episode and a *The Blues* instalment. The four
executive-producer documentaries in the film section are out for the same
reason as the producing: not one of the two jobs.

THE SECTIONS ARE THE ARTICLE'S, NOT THIS FILE'S
-----------------------------------------------
The five sections are the five ===Career=== headings on the "Clint Eastwood"
article, with their own year ranges and their own titles. main() reads them
out of the wikitext and builds the sections from the parsed ranges, so a
rewrite upstream breaks the build rather than leaving five hand-picked decades
pretending to be sourced. The first heading names *Rawhide*, which is
television and therefore not a row; the section intro says so rather than
leaving a reader hunting for it.

WEIGHTS: ONE SOURCE, THE FILM'S OWN INFOBOX
-------------------------------------------
Every bar is the running time stated in that film's own Wikipedia infobox,
in hours. One source for all 69, chosen over Wikidata's P2047 because P2047
carries two or three competing values on twelve of these films with nothing on
the statements to tell them apart, and because gwlib's rank-blind reader takes
the longest — which would have shipped *The Good, the Bad and the Ugly* at its
177-minute Italian premiere length and *The Enforcer* at 112 minutes for a
film its own article says runs 96. The infobox gives exactly one figure per
film and every one of the 69 has one, so there is nothing to adjudicate and no
row goes unweighted.

ALTERNATE CUTS: ONE ROW, THE THEATRICAL LENGTH, THE CUT IN THE NOTE
-------------------------------------------------------------------
A sweep of all 81 film articles for a sentence stating a running time next to
a word meaning "a particular version" finds exactly one film on this list with
a real second version: *The Good, the Bad and the Ugly*. It gets one row, per
HOW-IT-WORKS: the bar measures the 174-minute version Italian cinemas showed
(what the infobox states), and the note names the 177-minute premiere and the
161-minute American prints. A second row would either double the film's hours
or carry no weight in a fully weighted list, and it would pair with nothing
anywhere, because rows pair across lists by title and year.

Data:   scratch/agent-eastwood/collect.py -> tools/data/eastwood.json
Accent: scratch/agent-eastwood/accent.py
"""
import json
import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki                                 # noqa: E402
from gwlib.prop import join_bits, slug                       # noqa: E402

SLUG = "eastwood"
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "tools" / "data" / "eastwood.json"

ORD = ("first", "second", "third", "fourth", "fifth")
WORDS = ("no", "one", "two", "three", "four", "five", "six", "seven", "eight",
         "nine", "ten", "eleven", "twelve", "thirteen")

# The five ===Career=== headings, keyed by the start year the article gives
# them, with the intro this list writes for each. The years and the titles
# come from the article; only the prose is ours, and every number in it is
# interpolated from the rows the section actually holds.
SECTION_IDS = {1954: "contract", 1963: "leone", 1970: "harry",
               1990: "acclaim", 2010: "late"}


def word(n):
    return WORDS[n] if n < len(WORDS) else str(n)


def and_list(names):
    names = list(names)
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


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
    """{sync key -> [list titles]} for the other film lists already shipped —
    read off the catalogue on disk so the note naming the shared films cannot
    go stale, and so a new list arriving with one of these films shows up as a
    diff here."""
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


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    table = data["films"]
    lead = data["lead_text"]

    # ---- the two tables the roster comes from ----------------------------
    assert len(data["acting_rows"]) == 67, len(data["acting_rows"])
    assert len(data["directing_rows"]) == 43, len(data["directing_rows"])
    assert len(data["execprod_rows"]) == 4, len(data["execprod_rows"])
    assert len(table) == 82, len(table)

    # ---- the roster rule, and the thirteen it drops ----------------------
    unc = [f for f in table if f["uncredited"] and not f["directed"]]
    doc = [f for f in table if f["doc"]]
    prod = [f for f in table if f["produced"] and not f["directed"]
            and not f["acted"]]
    dropped = {f["t"] for f in unc + doc + prod}
    assert len(dropped) == 13, sorted(dropped)
    assert len(unc) == 8 and len(doc) == 4 and len(prod) == 1, \
        (len(unc), len(doc), len(prod))
    assert [f["t"] for f in prod] == ["The Stars Fell on Henrietta"], prod
    # every dropped uncredited row says "Uncredited" in the source's own Notes
    # column, and every dropped documentary says "Documentary film" — the
    # exclusions are the source's flags, not this file's opinion
    assert all("uncredited" in f["actnote"].lower() for f in unc), \
        [f["actnote"] for f in unc]
    assert all("documentary" in f["actnote"].lower() for f in doc), \
        [f["actnote"] for f in doc]
    # the two uncredited cameos that stay, because he directed those films
    cameos = [f for f in table if f["uncredited"] and f["directed"]]
    assert [f["t"] for f in cameos] == ["Breezy", "American Sniper"], cameos

    films = [f for f in table if f["t"] not in dropped]
    assert len(films) == 69, len(films)
    for f in films:
        f["both"] = f["directed"] and f["acted"] and not f["uncredited"]
        f["dir_only"] = f["directed"] and not f["both"]
        f["act_only"] = not f["directed"]
    both = [f for f in films if f["both"]]
    dir_only = [f for f in films if f["dir_only"]]
    act_only = [f for f in films if f["act_only"]]
    assert len(both) == 24 and len(dir_only) == 16 and len(act_only) == 29, \
        (len(both), len(dir_only), len(act_only))
    # the count of directed films matches the source's own Director column
    yes = [r for r in data["directing_rows"] if r["cols"][1].strip() == "Yes"]
    assert len(yes) == len(both) + len(dir_only) == 40, len(yes)

    # ---- release order ---------------------------------------------------
    for f in films:
        assert f["release_dates"], f["t"]
        f["rel"] = f["release_dates"][0]
        assert f["rel"][:4] in (str(f["year"]), str(f["year"] - 1),
                                str(f["year"] + 1)), (f["t"], f["rel"])
    films.sort(key=lambda f: (f["year"], f["rel"], f["t"]))
    assert films[0]["t"] == "Francis in the Navy" and films[0]["year"] == 1955
    assert films[-1]["t"] == "Juror #2" and films[-1]["year"] == 2024
    for a, b in zip(films, films[1:]):
        assert (a["year"], a["rel"]) <= (b["year"], b["rel"]), (a["t"], b["t"])

    # ---- weights: the film's own infobox, all 69 of them ------------------
    for f in films:
        assert len(f["runtime_mins"]) == 1, (f["t"], f["runtime_raw"])
        f["mins"] = f["runtime_mins"][0]
        assert 60 <= f["mins"] <= 200, (f["t"], f["mins"])
    assert all(f["has_infobox"] for f in films)
    # the twelve films where Wikidata carries competing values, which is why
    # the infobox is the source here and not P2047
    multi = [f for f in table
             if len({s["amount"] for s in f["p2047_seen"]}) > 1]
    assert len(multi) == 12, [f["t"] for f in multi]
    gbu = next(f for f in films if f["t"] == "The Good, the Bad and the Ugly")
    assert sorted(s["amount"] for s in gbu["p2047_seen"]) == [161.0, 177.0]
    assert gbu["mins"] == 174, gbu["mins"]

    # ---- alternate cuts: the sweep found exactly one ----------------------
    cut = [f for f in films
           if len([s for s in f["cut_sentences"]
                   if re.search(r"\bversion|\bcut to\b|\bprints\b", s)]) >= 2]
    assert [f["t"] for f in cut] == ["The Good, the Bad and the Ugly"], \
        [f["t"] for f in cut]
    prem = next(s for s in gbu["cut_sentences"] if "premiere version" in s)
    ital = next(s for s in gbu["cut_sentences"] if "Italian cinemas" in s)
    intl = next(s for s in gbu["cut_sentences"] if "international version" in s)
    gbu_prem = int(re.search(r"(\d{3}) minutes", prem).group(1))
    gbu_ital = int(re.search(r"(\d{3}) minutes", ital).group(1))
    gbu_us = int(re.search(r"runtime of (\d{3}) minutes", intl).group(1))
    assert (gbu_prem, gbu_ital, gbu_us) == (177, 174, 161), \
        (gbu_prem, gbu_ital, gbu_us)
    assert gbu["mins"] == gbu_ital, "the bar is no longer the Italian release"

    # ---- the facts the row notes are built from, all read out of the lead --
    def lead_says(phrase):
        assert phrase in lead, "the lead no longer says: %s" % phrase
        return phrase

    lead_says("made his directorial debut with Play Misty for Me")
    debut = next(f for f in films if f["directed"])
    assert debut["t"] == "Play Misty for Me" and debut["year"] == 1971, debut

    m = re.search(r"spawned (\w+) more films: (.+?)\.", lead)
    assert m and m.group(1) == "four", lead[:0] or m
    harry = [(re.sub(r"^and ", "", t.strip(" ,")), int(y)) for t, y in
             re.findall(r"([A-Za-z' ]+?) \((\d{4})\)", m.group(2))]
    assert [t for t, _ in harry] == ["Magnum Force", "The Enforcer",
                                     "Sudden Impact", "The Dead Pool"], harry
    harry_no = {"Dirty Harry": 1}
    for i, (t, _y) in enumerate(harry):
        harry_no[t] = i + 2
    assert len(harry_no) == 5

    m = re.search(r"Dollars Trilogy: (.+?), which weren't released in the "
                  r"United States until (\d{4})", lead)
    assert m, "the lead no longer describes the Dollars Trilogy"
    dollars = [re.sub(r"^and ", "", t.strip(" ,")) for t, _ in
               re.findall(r"([A-Za-z',. ]+?) \((\d{4})\)", m.group(1))]
    assert dollars == ["A Fistful of Dollars", "For a Few Dollars More",
                       "The Good, the Bad and the Ugly"], dollars
    us_year = m.group(2)
    # the same three films, arrived at independently: the acting table tags
    # exactly these with its own "See also: Man with No Name" note
    tagged = [f["t"] for f in films if "Man with No Name" in f["actnote"]]
    assert tagged == dollars, (tagged, dollars)

    lead_says("generated a sequel, Any Which Way You Can")
    lead_says("Pale Rider, which was the highest-grossing western of the 1980s")
    lead_says("starred opposite an orangutan in the action-comedy "
              "Every Which Way but Loose")
    lead_says("the companion war films Flags of Our Fathers and Letters from "
              "Iwo Jima, which depict the Battle of Iwo Jima from the "
              "perspectives of the U.S. and Japan, respectively")
    lead_says("Academy Awards for Best Director and Best Picture for his 1992 "
              "western Unforgiven")
    lead_says("once again won the Academy Awards for Best Picture and "
              "Director, this time for Million Dollar Baby")
    lead_says("making Mystic River the first film to win both categories "
              "since Ben Hur in 1959")
    lead_says("His most recent acting role was for the film Cry Macho (2021)")
    last_role = [f for f in films if f["acted"] and not f["uncredited"]][-1]
    assert last_role["t"] == "Cry Macho", last_role["t"]

    # The lead and the table disagree about when he first produced: the lead
    # says his producing debut was Firefox and Honkytonk Man in 1982, and the
    # table marks Breezy (1973) {{Yes}} in its Producer column. THE SOURCE
    # WINS is no help when the source contradicts itself, so this list makes
    # no producing claim anywhere — producing is not one of the two jobs it
    # tracks. The assert keeps that reasoning attached to the fact.
    lead_says("Eastwood's debut as a producer began in 1982 with two films, "
              "Firefox and Honkytonk Man")
    early_prod = [f["t"] for f in table if f["produced"] and f["year"] < 1982]
    assert early_prod == ["Breezy"], early_prod

    # ---- the lead cross-check: every italicised link in the lead is either
    # a shipped row or a named exclusion, and nothing falls between ---------
    shipped = {f["target"]: f for f in films}
    stray = []
    for link in data["lead_links"]:
        if link["target"] not in shipped:
            stray.append(link["shown"])
    assert sorted(stray) == ["Ben Hur", "Rawhide"], stray
    # Ben-Hur is not an Eastwood film at all — the lead names it for the
    # Mystic River statistic. Rawhide is the television series.
    assert any(r["t"] == "Rawhide" for r in data["tv_actor"]), data["tv_actor"]

    # and the reverse: every shipped row came out of one of the two tables
    from_tables = {r["t"] for r in data["acting_rows"]} | \
                  {r["t"] for r in data["directing_rows"]}
    assert all(f["t"] in from_tables for f in films), \
        [f["t"] for f in films if f["t"] not in from_tables]

    # ---- row notes --------------------------------------------------------
    def note_for(f):
        role = f["role"]
        if f["both"]:
            bits = ["Directed and starred as %s" % role]
        elif f["dir_only"]:
            bits = ["Directed"]
        else:
            bits = ["Starred as %s" % role]

        if f["t"] == "Play Misty for Me":
            bits.append("His first film as director")
        if f["t"] in dollars:
            bits.append("The %s of Sergio Leone's Dollars Trilogy"
                        % ORD[dollars.index(f["t"])])
        if f["t"] in harry_no:
            bits.append("The %s of five Dirty Harry films" % ORD[harry_no[f["t"]] - 1])
        if f["t"] == "The Witches":
            seg = re.search(r'Segment: "(.+?)"', f["actnote"]).group(1)
            bits.append("A portmanteau film; his part is the segment %s" % seg)
        if f["t"] == "Any Which Way You Can":
            bits.append("Sequel to Every Which Way but Loose")
        if f["t"] == "Every Which Way but Loose":
            bits.append("An action comedy played opposite an orangutan")
        if f in cameos:
            bits.append("He appears in it too, uncredited")
        if f["t"] == "The Good, the Bad and the Ugly":
            bits.append("The bar is the %d-minute version Italian cinemas "
                        "showed; the premiere ran %d minutes and most "
                        "American prints %d" % (gbu_ital, gbu_prem, gbu_us))
        if f["t"] == "Pale Rider":
            bits.append("The highest-grossing western of the 1980s")
        if f["t"] in ("Unforgiven", "Million Dollar Baby"):
            bits.append("Won Best Picture and Best Director")
        if f["t"] == "Mystic River":
            bits.append("The first film since Ben-Hur to take both Best Actor "
                        "and Best Supporting Actor")
        if f["t"] in ("Flags of Our Fathers", "Letters from Iwo Jima"):
            side = "American" if f["t"].startswith("Flags") else "Japanese"
            other = ("Letters from Iwo Jima" if side == "American"
                     else "Flags of Our Fathers")
            bits.append("Companion film to %s — the same battle from the "
                        "%s side" % (other, side))
        if f["t"] == "Cry Macho":
            bits.append("His last acting role")
        if f is films[-1]:
            bits.append("His last film so far")
        return join_bits(*bits)

    # ---- sections: the article's own career headings -----------------------
    # the heading text as written, minus the italic markup around the two
    # titles it names — never hand-stripped, see gwlib.wiki.clean
    heads = [(int(lo), int(hi), wiki.clean(t)) for lo, hi, t in
             data["career_heads"]]
    assert heads[0][2] == "Acting debut and Rawhide", heads[0]
    assert [lo for lo, _, _ in heads] == sorted(SECTION_IDS), heads
    assert all(b == a + 1 for (_, a, _), (b, _, _) in zip(heads, heads[1:])), \
        "the article's career ranges no longer tile"

    counts = {}
    for lo, hi, _t in heads:
        got = [f for f in films if lo <= f["year"] <= hi]
        counts[lo] = (len(got), sum(1 for f in got if f["both"]),
                      sum(1 for f in got if f["dir_only"]),
                      sum(1 for f in got if f["act_only"]))
    assert [counts[k][0] for k in sorted(counts)] == [4, 8, 28, 18, 11], counts
    assert counts[1954][1] + counts[1954][2] == 0, counts[1954]
    assert counts[1963][1] + counts[1963][2] == 0, counts[1963]
    assert counts[2010][2] == 8, counts[2010]

    early_unc = [f for f in unc if f["year"] <= 1962]
    assert len(early_unc) == 7, [f["t"] for f in early_unc]

    # two numbers the intros quote, both computed from release dates rather
    # than remembered: the gap between his first film as director and Dirty
    # Harry, and his age when the last film came out
    import datetime
    dt = lambda s: datetime.date(*(int(p) for p in s.split("-")))
    gap = (dt(next(f["rel"] for f in films if f["t"] == "Dirty Harry"))
           - dt(debut["rel"])).days // 7
    assert gap == 9, gap
    birth = dt(data["birth"])
    last = dt(films[-1]["rel"])
    age = last.year - birth.year - ((last.month, last.day) < (birth.month,
                                                              birth.day))
    assert age == 94, age

    def intro_for(lo):
        n, b, d, a = counts[lo]
        if lo == 1954:
            return ("The contract-player years: %s credited film roles across "
                    "four years, none of them large. %s more parts from the "
                    "same stretch went out uncredited and are not rows here. "
                    "The heading is the article's own, and the Rawhide in it "
                    "is the television series that made him famous while "
                    "these were happening — television is not on this list."
                    % (word(a), word(len(early_unc)).capitalize()))
        if lo == 1963:
            return ("Three films for Sergio Leone turn a television cowboy "
                    "into a star, and the five that follow are what that "
                    "stardom bought. He directs none of these; the whole "
                    "section is acting. The years on the trilogy rows are the "
                    "Italian releases — America did not see any of the "
                    "three until %s." % us_year)
        if lo == 1970:
            return ("The biggest stretch of the career and the one where the "
                    "two jobs start running together: %d films in twenty "
                    "years, %s of them directed. Play Misty for Me is his "
                    "first as director and Dirty Harry followed it into "
                    "cinemas %s weeks later. %s of these he both directed "
                    "and starred in."
                    % (n, word(b + d), word(gap), word(b).capitalize()))
        if lo == 1990:
            return ("Two Best Picture wins sit in this section — Unforgiven "
                    "near the start of it and Million Dollar Baby in the "
                    "middle — and it is where he begins making films he is "
                    "not in: %s of these %d he directed without appearing, "
                    "against %s in the twenty years before."
                    % (word(d), n, word(counts[1970][2])))
        return ("The retirement years, and almost entirely directing: %s of "
                "these %s he directed without appearing. Cry Macho is his "
                "last acting role and Juror #2, out in the year he turned %d, "
                "his last film so far." % (word(d), word(n), age))

    sections = []
    for lo, hi, title in heads:
        got = [f for f in films if lo <= f["year"] <= hi]
        assert got, lo
        items = []
        for f in got:
            it = {"id": "ce-%d-%s" % (f["year"], slug(f["t"])),
                  "t": f["t"], "n": str(f["year"]),
                  "w": round(f["mins"] / 60.0, 2)}
            n = note_for(f)
            if n:
                it["note"] = n
            items.append(it)
        sections.append({
            "id": SECTION_IDS[lo], "title": title,
            "sub": "%d–%d · %d films · %d hours"
                   % (got[0]["year"], got[-1]["year"], len(got),
                      round(sum(f["mins"] for f in got) / 60.0)),
            "intro": intro_for(lo), "items": items})
    sections[0]["open"] = True

    rows = [x for s in sections for x in s["items"]]
    assert len(rows) == 69, len(rows)
    assert all(isinstance(x["w"], float) and x["w"] > 0 for x in rows), \
        [x["id"] for x in rows if not x.get("w")]
    assert all(x.get("note") for x in rows), \
        [x["id"] for x in rows if not x.get("note")]
    for s in sections:
        assert all(a["n"] <= b["n"] for a, b in zip(s["items"], s["items"][1:])), \
            "%s is out of year order" % s["title"]
    mins = sum(f["mins"] for f in films)
    hours = round(sum(x["w"] for x in rows), 2)
    assert abs(hours - mins / 60.0) < 0.3, (hours, mins / 60.0)

    # ---- the films this list shares with other lists here ------------------
    keys = {normt(f["t"]) + "|" + str(f["year"]): f["t"] for f in films}
    shared = overlaps(keys)
    assert len(shared) == 5, sorted(shared)
    by_list = {}
    for k, titles in shared.items():
        for t in titles:
            by_list.setdefault(t, []).append(keys[k])
    order = [f["t"] for f in films]
    phrases = ["%s %s also on %s"
               % (and_list(sorted(by_list[t], key=order.index)),
                  "is" if len(by_list[t]) == 1 else "are", t)
               for t in sorted(by_list, key=lambda t: (-len(by_list[t]), t))]
    sharing = ("%s. Ticking one ticks the rest: film rows pair across lists by "
               "title and year, so a film watched here is watched there. "
               "Nothing is duplicated and no hours are counted twice, because "
               "every list totals only its own rows." % "; ".join(phrases))
    # The assert is on what the NOTE says, not on which other lists exist. It
    # used to read `list(by_list) == ["Best Picture"]`, which was a count of
    # other lists dressed up as a check on the sentence: the day
    # kevin-bacon.json picked up Mystic River there were two, and the generator
    # stopped dead before writing anything (CLU-533) on a catalogue growing,
    # which is the one thing it has to survive. What must stay true as more
    # lists arrive is that every list a shared film is on, and every shared
    # film, is NAMED in the sentence a reader actually gets — which is the
    # thing the assert was there to protect.
    for name, titles in by_list.items():
        assert name in sharing, (name, sharing)
        for film in titles:
            assert film in sharing, (film, sharing)
    named = {f for ts in by_list.values() for f in ts}
    assert named == {keys[k] for k in shared}, \
        (sorted(named), sorted(keys[k] for k in shared))

    p = {
        "slug": SLUG,
        "title": "Clint Eastwood",
        "subtitle": "directed or starred in, one row per film",
        "kind": "films",
        # A household name a long way outside film fandom — the Man with No
        # Name, Dirty Harry, four Academy Awards and a seventy-year career —
        # and a movie star as well as a director, which is what puts him above
        # the director-only lists here (Ridley Scott and Scorsese at 75,
        # Hitchcock 77) and level with Tom Cruise, the other star's list. Below
        # Spielberg at 84. See POPULARITY.md.
        "popularity": 79,
        "year": "1955–2024",
        "blurb": "Sixty-nine films in release order — about %d hours. "
                 "One row per film whether he directed it, starred in it or "
                 "did both, because %d of them are both." % (round(hours),
                                                             len(both)),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        # Measured in CIELAB against every accent in properties/index.json;
        # see scratch/agent-eastwood/accent.py. Every dust-and-ochre colour
        # anyone would reach for first is taken and taken closely — the Leone
        # desert sun lands 6.6 from Fallout's, Almeria dust 5.7 from
        # Frieren's, Dirty Harry's San Francisco slate 2.7 from The Wire's.
        # The sagebrush green of the poncho and the high-plains scrub is the
        # one signature colour with room in it, 14.3 worst-case against 17.5
        # for the freest pair anywhere on the wheel.
        "accent": "#70825E",
        "accentDark": "#9CB183",
        "tiers": False,
        "notes": [
            ["One list, not two, and every row says which job he did.",
             "Splitting the directing from the acting is the obvious move and "
             "it is the wrong one: %d of these %d films are films he directed "
             "AND starred in, so Unforgiven and Gran Torino would land on two "
             "pages and a tick on either would mean half a thing. So there is "
             "one row per film, in release order, and the note names the role "
             "— directed, starred, or both. %d he directed without "
             "appearing; %d he acted in for other directors."
             % (len(both), len(films), len(dir_only), len(act_only))],
            ["Directed or credited on screen — %d of the %d films the "
             "filmography lists." % (len(films), len(table)),
             "The %s it leaves out. %s uncredited appearances: the 1955–57 "
             "contract-player walk-ons — %s — and his cameo as "
             "himself in Casper. The source lists all of them and marks every "
             "one uncredited in its own notes column, which is the "
             "source drawing the line rather than this list; an unbilled "
             "jet-squadron leader is not a role. Breezy and American Sniper "
             "keep their rows despite being the same kind of cameo, because he "
             "directed both, and the row says so. Also out: %s appearances as "
             "himself in documentaries about other people, and one "
             "producer-only credit, The Stars Fell on Henrietta — "
             "producing is not one of the two jobs this list tracks, which is "
             "also why Tightrope and Trouble with the Curve ARE here: he "
             "produced without directing, but he stars in both."
             % (word(len(dropped)), word(len(unc)).capitalize(),
                and_list([f["t"] for f in early_unc]), word(len(doc)))],
            ["No television.",
             "The source keeps it in a separate section from the films, and "
             "that is the line this list takes: %s acting credits including "
             "the eight seasons of Rawhide, and %s directing credits — an "
             "Amazing Stories episode and an instalment of The Blues. The %s "
             "documentaries he executive produced are out for the same reason "
             "the producing is."
             % (word(len(data["tv_actor"])), word(len(data["tv_dir"])),
                word(len(data["execprod_rows"])))],
            ["The five sections are the article's own.",
             "Not five invented decades: they are the five career headings on "
             "the Clint Eastwood article, with their year ranges and their "
             "titles as written. The first one names Rawhide, which is "
             "television and therefore not a row on the page it heads."],
            ["Bar widths are runtimes, from each film's own infobox.",
             "One source for all %d, and every one of them has a figure, so no "
             "row goes unweighted. Wikidata's runtime property was the "
             "alternative and lost: it carries two or three competing values on "
             "%s of these films with nothing on the statements to separate "
             "them, and the longest-wins reading would have shipped The Good, "
             "the Bad and the Ugly at its 177-minute Italian premiere length "
             "and The Enforcer at 112 minutes for a film its own article says "
             "runs %d." % (len(films), word(len(multi)),
                           next(f["mins"] for f in films
                                if f["t"] == "The Enforcer"))],
            ["One film here has a second version, and it still gets one row.",
             "A sweep of all %d film articles for a sentence stating a running "
             "time beside a word meaning a particular version turns "
             "up exactly one: The Good, the Bad and the Ugly, which premiered "
             "in Italy at %d minutes, played Italian cinemas at %d after Leone "
             "cut a scene, and reached America at %d. The bar measures the %d, "
             "which is what its infobox states, and the row note names the "
             "others. A second row would either double that film's hours "
             "— you do not watch it twice — or carry no weight in a "
             "list where every other row has some, and it would pair with "
             "nothing anywhere, because rows pair across lists by title and "
             "year." % (len(table) - 1, gbu_prem, gbu_ital, gbu_us, gbu_ital)],
            ["%s of these films are on another list here." % word(len(shared)).capitalize(),
             sharing],
            "Roster and roles from Wikipedia's Clint Eastwood filmography, "
            "read from the acting and directing tables themselves; the five "
            "sections and the facts on the rows from the Clint Eastwood "
            "article; runtimes and the alternate-cut lengths from each film's "
            "own article.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d films, %d minutes, %.2f hours"
          % (out.name, len(rows), mins, hours))
    print("   %d directed and starred, %d directed only, %d starred only"
          % (len(both), len(dir_only), len(act_only)))
    for s in sections:
        print("   %-52s %2d  %s" % (s["title"][:52], len(s["items"]), s["sub"]))
    print("   shared: %s"
          % "; ".join("%s: %s" % (t, ", ".join(by_list[t])) for t in by_list))


if __name__ == "__main__":
    main()
