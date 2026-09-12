#!/usr/bin/env python3
"""Generate properties/jackie-chan.json.

    PYTHONIOENCODING=utf-8 python tools/make_jackie-chan.py

Jackie Chan's acting credits in year order, one row per film. Everything here
is machine-read from tools/data/jackie-chan.json, collected by
scratch/agent-jackie/collect.py from Wikipedia's "Jackie Chan filmography",
the "Jackie Chan" article, each linked film's own article, and Wikidata.
Nothing is typed in from memory, and every claim the copy makes is asserted
against the data that produced it before anything is written.

THE CREDIT RULE: THE SOURCE'S OWN "CREDITED AS -> ACTOR" COLUMN
---------------------------------------------------------------
The ==As actor== table has a **Credited as** header spanning two yes/no
columns, **Actor** and **Producer**. That first column is the whole rule:

    A row is a film here when the filmography's own Actor column says yes.

191 rows, 157 with Actor = yes. The 34 it says no to are credits where he
never appears: 21 producer-only rows (Read Lips, Rouge, Rice Rhapsody,
Everlasting Regret, Golden Job and the rest), and 13 more where he is neither
actor nor producer — A Touch of Zen and The Private Eyes (the notes say
"Stuntman Only"), The Young Dragons, The 36 Crazy Fists, Dance of Death,
Immortal Warriors and The Outlaw Brothers (action director / stunt
coordinator), The Magnificent Monk ("As writer"), Game of Death ("In scripts
only"), Center Stage, Gen-Y Cops and Home Operation ("Presenter only"), and
Painted Faces. A watch list is a list of films you can watch him in.

THE BIT PARTS AND THE STUNT WORK STAY, AND THE SAME COLUMN IS WHY
------------------------------------------------------------------
This is the decision the list turns on, because the first fifteen years are
almost entirely extra work, and it is settled by the table rather than by
taste. The Actor column says **yes** to the Bruce Lee films — Fist of Fury
(1972), where the Role column reads "Jing Wu's Student", and Enter the Dragon
(1973), "One Of Han's Prison Security Guards", notes "Also Stuntman" — so
both are rows. It says **no** to A Touch of Zen (1971), whose note is
"Stuntman Only", so that is not a row. On-screen bit parts are in; pure stunt
and crew credits are out; the source drew the line, not this file.

The Role and Notes columns then say what each credit was, in the source's own
words, and every row carries them: "As Extra", "As Stuntman", "Uncredited",
"An uncredited extra", "A cameo", "Brief appearance". Nothing is dressed up.

What the source does NOT carry is a per-film credited-name column, so no row
claims one. The "Jackie Chan" article records that his stage name was changed
to Sing Lung for New Fist of Fury in 1976, and the 1976 section says so; it
is a fact about the career, not a claim about any individual credit.

TWO ROWS ARE DROPPED FOR HAVING NO DATE AT ALL
-----------------------------------------------
Rush Hour 4 and Armour of God IV: Ultimatum sit under a Year column reading
"TBA". The house rule for announced work needs the source to give it a date,
even just a year, and the source gives neither — so 157 - 2 = 155 rows.
(The Wikidata gate caught Rush Hour 4 independently: its wikilink resolves to
an item published in 1998, i.e. the first film.)

SHORTS, DOCUMENTARIES AND TELEVISION ARE OUT, AND THE SOURCE IS WHY
-------------------------------------------------------------------
The filmography keeps each in its own section: a ===Short film=== table of 5,
a ==Documentaries== table of 15, and ==Television== with 4 scripted series
and 4 reality shows. That separation is the line this list takes, exactly as
the Kevin Bacon and Clint Eastwood lists took it.

TITLES: THE TABLE'S, WITH EVERY OTHER NAME ON THE ROW
------------------------------------------------------
These films carry three and four English names each. The row title is the one
the filmography table itself prints — so "Vampire Effect", "Battle Creek
Brawl", "Armour of God (Operation Condor)", because that is what the source
wrote. Every other name the source gives goes on the row after "Also known
as": the film's own article title where it differs, then the alternate names
that article marks in bold in its lead. 44 rows carry at least one.

THE IDS ARE WHY THAT IS SAFE
-----------------------------
`q` is the film's Wikidata id, resolved from the wikilink the table's own
title cell gives — never from a title lookup, which is exactly how a 1956
film got attached to a 1960 row elsewhere this week — and gated on the item's
P31 naming a film. 133 of the 155 rows carry one; the 22 that do not are rows
the table never linked, and they ship with no id rather than a wrong one.
The source proves the point on itself: its own ==As director== table titles
two of the same films differently ("Armour of God", "Project A Part II"), and
all 13 of its rows match a row here on the id when 2 of 13 do not match on
the title.

ALTERNATE CUTS: ONE ROW EACH, EVERY LENGTH NAMED
-------------------------------------------------
Eight films state more than one running time in their own infobox, because
they were re-cut for release abroad — Rumble in the Bronx at 106 minutes and
a 90-minute US re-cut, Armour of God II at 107 and 91, Supercop 95 and 91,
Dragon Blade 127 and 103, New Fist of Fury 118 and 82, Island of Fire 125,
96 and 96, Fist to Fist 85 and 70, The Protector 95 and 92. Each gets one
row, per HOW-IT-WORKS, and the note gives the article's figures verbatim
rather than picking a winner — on The Protector it is the US cut that is
longer, so "the original is the long one" would have been false.

WEIGHTS: NONE, AND CLU-131 IS WHY
----------------------------------
30 of the 155 rows have no running time in any source read here: 22 films the
table never linked to an article, and 8 more whose article has no runtime
anywhere. Under CLU-131 a row with no `w` on a weighted list silently counts
as one hour, so a list cannot mix. 30 of 155 is a fifth of the early career,
not a rounding error, and zero-weighting them would draw a bar chart whose
whole first section is invisible. So the list ships unweighted and says so.
Flipping WEIGHTED below is one edit if the lead disagrees, but the 30 rows
would then all have to carry w: 0.

Data:   scratch/agent-jackie/collect.py -> tools/data/jackie-chan.json
Accent: scratch/agent-jackie/accent.py · Sync: scratch/agent-jackie/sync.py
"""
import json
import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop                                       # noqa: E402
from gwlib.prop import join_bits, slug                       # noqa: E402

SLUG = "jackie-chan"
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "tools" / "data" / "jackie-chan.json"

# Flip to True only after giving the 30 runtime-less rows an explicit w: 0
# (see the weights note in the docstring).
WEIGHTED = False

WORDS = ("no", "one", "two", "three", "four", "five", "six", "seven", "eight",
         "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
         "sixteen", "seventeen", "eighteen", "nineteen", "twenty",
         "twenty-one", "twenty-two", "twenty-three", "twenty-four",
         "twenty-five", "twenty-six", "twenty-seven", "twenty-eight",
         "twenty-nine", "thirty")

# The Notes column of the ==As actor== table, on the rows that keep one,
# turned into row prose. Every distinct note on a shipped row must appear
# here or main() fails, so a rewrite upstream breaks the build instead of
# shipping wikitext or silence. "Also director" is deliberately None: the
# ==As director== table is what the directing credit is read from.
SRC_NOTE = {
    "": None,
    "Also director": None,                  # the As director table says it
    "Also Stuntman": "He did the stunt work in it too",
    "Cameo": "A cameo",
    "Cantonese & Mandarin dub": "He voiced the Cantonese and Mandarin dubs",
    "Directioral debut": None,              # said last, after the credit

    "Guest appearance": "A guest appearance",
    "Hollywood debut": "His Hollywood debut",
    "Mandarin dub": "He voiced the Mandarin dub",
    "Presenter": "He presented it too",
    "Uncredited": "Uncredited",
    "Uncredited co-director": "He co-directed it, uncredited",
    "Uncredited extra": "An uncredited extra",
}

# Two Role cells describe the size of the appearance instead of naming a
# part, and "As Cameo" reads as a character. "Cameo" is the source's own
# word for it — it is one of the Notes column's values as well, asserted
# below — and "Brief appearance" is the same kind of cell.
ROLE_AS_NOTE = {"Cameo": "A cameo", "Brief appearance": "A brief appearance"}

SECTION_IDS = ["e1962", "e1976", "e1980", "e1988", "e1999", "e2008"]


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


def overlaps(keys, qids):
    """{list title -> [film titles]} for every other syncable list on disk,
    matched on build.py's two lanes: normalized title + year + medium, and the
    Wikidata id. Read off the catalogue so the note naming the shared films
    cannot go stale."""
    out = {}
    for f in sorted((ROOT / "properties").glob("*.json")):
        if f.stem in ("index", "search", SLUG):
            continue
        p = json.loads(f.read_text(encoding="utf-8"))
        kind = p.get("kind") or ""
        if p.get("secret") or not ("film" in kind or "game" in kind):
            continue
        medium = "g" if "game" in kind else "f"
        for s in p.get("sections", []):
            for x in s.get("items", []):
                y = year_of(x, str(x.get("n", "")))
                hit = None
                if y and (normt(x["t"]) + "|" + y + "|" + medium) in keys:
                    hit = keys[normt(x["t"]) + "|" + y + "|" + medium]
                q = x.get("q")
                if isinstance(q, str) and q + "|" + medium in qids:
                    hit = qids[q + "|" + medium]
                if hit and hit not in out.setdefault(p["title"], []):
                    out[p["title"]].append(hit)
    return out


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    table = data["films"]
    lab = data["p31_labels"]

    assert len(table) == 191, len(table)
    assert len(data["shorts"]) == 5, len(data["shorts"])
    assert len(data["directed"]) == 13, len(data["directed"])
    assert len(data["docs"]) == 15, len(data["docs"])
    assert len(data["tv_scripted"]) == 4 and len(data["tv_reality"]) == 4, \
        (len(data["tv_scripted"]), len(data["tv_reality"]))

    def p31(f):
        return {lab.get(p, p) for p in f.get("p31") or []}

    # ---- the credit rule, and the rows it drops --------------------------
    acted = [f for f in table if f["actor"] == "yes"]
    crew = [f for f in table if f["actor"] != "yes"]
    assert len(acted) == 157 and len(crew) == 34, (len(acted), len(crew))
    prod_only = [f for f in crew if f["producer"] == "yes"]
    neither = [f for f in crew if f["producer"] != "yes"]
    assert len(prod_only) == 21 and len(neither) == 13, \
        (len(prod_only), len(neither))
    # the line the whole list turns on: the Bruce Lee films are Actor=yes with
    # a named role, the stunt-only credit is Actor=no
    fof = next(f for f in table if f["t_src"] == "Fist of Fury")
    etd = next(f for f in table if f["t_src"] == "Enter the Dragon")
    toz = next(f for f in table if f["t_src"] == "A Touch of Zen")
    assert (fof["actor"], fof["role"]) == ("yes", "Jing Wu's Student"), fof["role"]
    assert (etd["actor"], etd["note_src"]) == ("yes", "Also Stuntman"), etd
    assert etd["role"] == "One Of Han's Prison Security Guards", etd["role"]
    assert (toz["actor"], toz["note_src"]) == ("no", "Stuntman Only"), toz
    # role and notes both, because the source has four malformed cells —
    # `| rowspan=2 {{n/a}}` with no pipe before the content — which MediaWiki
    # renders as literal text and which therefore shift the two rows after
    # them one column left. All four are Actor=no rows, so nothing shipped is
    # affected, and the guard below keeps it that way.
    stunt_out = sorted(f["t_src"] for f in neither
                       if re.search(r"stunt", f["role_raw"] + " " + f["note_src"],
                                    re.I))
    assert stunt_out == ["A Touch of Zen", "Dance of Death", "Immortal Warriors",
                         "The 36 Crazy Fists", "The Private Eyes"], stunt_out
    malformed = sorted(f["t_src"] for f in table
                       if "rowspan" in f["role_raw"] + f["note_src"])
    assert malformed == ["Dance of Death", "The Inspector Wears Skirts",
                         "The Private Eyes"], malformed
    assert all(f["actor"] == "no" for f in table if f["t_src"] in malformed)
    # and the on-screen stunt/extra credits that stay, on the same column
    stunt_in = [f["t_src"] for f in acted if f["role"] == "Stuntman"]
    assert stunt_in == ["The Awaken Punch", "Fist of Unicorn", "Fist to Fist"], \
        stunt_in

    # ---- the two rows with no date at all --------------------------------
    undated = [f for f in acted if not f["year"]]
    assert [f["t_src"] for f in undated] == ["Rush Hour 4",
                                             "Armour of God IV: Ultimatum"], undated
    assert all(f["year_raw"] == "TBA" for f in undated), undated
    rh4 = next(f for f in undated if f["t_src"] == "Rush Hour 4")
    assert rh4["pubyears"] == [1998], rh4["pubyears"]     # the id gate agrees

    films = [f for f in acted if f["year"]]
    assert len(films) == 155, len(films)
    for a, b in zip(films, films[1:]):
        assert a["year"] <= b["year"], (a["t_src"], b["t_src"])
    assert films[0]["t_src"] == "Big and Little Wong Tin Bar", films[0]["t_src"]
    assert films[0]["year"] == 1962 and films[-1]["year"] == 2026

    # ---- directing, from the source's own second table -------------------
    # joined on the Wikidata id, because two of its thirteen titles are
    # spelled differently from the acting table's
    by_q = {f["qid"]: f for f in films if f["qid"]}
    directed = {}
    for d in data["directed"]:
        assert d["dir"] == "yes", d
        assert d["qid"] in by_q, d["t_src"]
        directed[d["qid"]] = d
    assert len(directed) == 13, len(directed)
    title_mismatch = sorted(d["t_src"] for d in data["directed"]
                            if d["t_src"] not in {f["t_src"] for f in films})
    assert title_mismatch == ["Armour of God", "Project A Part II"], title_mismatch
    hyena = next(d for d in data["directed"] if d["t_src"] == "The Fearless Hyena")
    assert hyena["year"] == "1979", hyena["year"]

    # ---- weights: the gap that decides the whole list --------------------
    no_rt = [f for f in films if not f["runtime_mins"]]
    unlinked = [f for f in films if not f["target"]]
    assert len(unlinked) == 22, len(unlinked)
    assert len(no_rt) == 30, len(no_rt)
    assert all(not f["has_article"] for f in unlinked), unlinked
    # the 8 that have an article but still no runtime
    art_no_rt = sorted(f["t_src"] for f in no_rt if f["has_article"])
    assert len(art_no_rt) == 8, art_no_rt
    assert not WEIGHTED, "give the 30 runtime-less rows an explicit w: 0 first"

    # ---- alternate cuts ---------------------------------------------------
    cuts = [f for f in films if len(set(f["runtime_mins"])) > 1]
    assert len(cuts) == 8, [f["t_src"] for f in cuts]
    cutnames = [f["t_src"] for f in cuts]
    assert cutnames == ["Fist to Fist", "New Fist of Fury", "The Protector",
                        "Island of Fire", "Armour of God II: Operation Condor",
                        "Supercop", "Rumble in the Bronx", "Dragon Blade"], cutnames
    ritb = next(f for f in cuts if f["t_src"] == "Rumble in the Bronx")
    assert ritb["runtime_mins"] == [106, 90], ritb["runtime_mins"]
    prot = next(f for f in cuts if f["t_src"] == "The Protector")
    # the row that stops this file claiming the original is always the longest
    assert prot["runtime_raw"] == "95 minutes (US), 92 minutes (HK)", \
        prot["runtime_raw"]

    # ---- ids ---------------------------------------------------------------
    def has_id(f):
        return bool(f["qid"] and f["year_gate"]
                    and any("film" in c for c in p31(f)))

    with_q = [f for f in films if has_id(f)]
    assert len(with_q) == 133, len(with_q)
    assert len(with_q) == len(films) - len(unlinked), (len(with_q), len(unlinked))
    assert len({f["qid"] for f in with_q}) == 133

    # ---- titles and the alternates ----------------------------------------
    def alts_of(f):
        return ([f["alt_article"]] if f["alt_article"] else []) + f["alts"]

    alted = [f for f in films if alts_of(f)]
    assert len(alted) == 44, len(alted)
    for t, want in {
            "Drunken Master II": ["The Legend of Drunken Master"],
            "Vampire Effect": ["The Twins Effect"],
            "Battle Creek Brawl": ["The Big Brawl"],
            "Armour of God (Operation Condor)": ["Armour of God"],
            "Supercop": ["Jackie Chan's Supercop"],
            "Twin Dragons": ["Brother vs. Brother", "Duel of Dragons",
                             "When Dragons Collide", "Double Dragons"]}.items():
        got = alts_of(next(f for f in films if f["t_src"] == t))
        assert got == want, (t, got)

    # ---- the facts the copy is built from, read out of the articles -------
    flead = data["lead_text"]
    era = data["era_text"]
    heads = data["era_heads"]

    def lead_says(phrase):
        assert phrase in flead, \
            "the filmography lead no longer says: %s" % phrase
        return phrase

    lead_says("Jackie Chan began his film career as an extra child actor in "
              "the 1962 film Big and Little Wong Tin Bar")
    lead_says("Ten years later, he was a stuntman opposite Bruce Lee in "
              "1972's Fist of Fury and 1973's Enter the Dragon")
    lead_says("His first major breakthrough was the 1978 kung fu action "
              "comedy film Snake in the Eagle's Shadow")

    # ---- sections: the article's own era headings -------------------------
    spans = []
    for h in heads:
        m = re.match(r"^(\d{4})[–-](\d{4}|present):\s*(.+)$", h)
        if m:
            spans.append((int(m.group(1)),
                          9999 if m.group(2) == "present" else int(m.group(2)),
                          m.group(3).strip(), h))
    assert len(spans) == 6, [s[3] for s in spans]
    assert [s[0] for s in spans] == [1962, 1976, 1980, 1988, 1999, 2008], spans
    assert spans[-1][3].startswith("2008–present"), spans[-1][3]
    # the one overlap: 1980 is claimed by two headings, and the article's own
    # prose settles it — both 1980 films are discussed under 1980-1987 and
    # neither is mentioned under 1976-1980
    overlap = [y for y in range(1900, 2100)
               if sum(1 for lo, hi, _, _ in spans if lo <= y <= hi) > 1]
    assert overlap == [1980], overlap
    for t in ("The Young Master", "The Big Brawl"):
        assert t in era[spans[2][3]], t
        assert t not in era[spans[1][3]], t
    assert "His first Hollywood film was The Big Brawl in 1980" in era[spans[2][3]]
    assert "His stage name was changed to" in era[spans[1][3]], "stage name"

    def sec_of(y):
        hit = None
        for i, (lo, hi, _, _) in enumerate(spans):
            if lo <= y <= hi:
                hit = i                     # the LAST span wins the overlap
        return hit

    buckets = [[f for f in films if sec_of(f["year"]) == i]
               for i in range(len(spans))]
    assert [len(b) for b in buckets] == [34, 17, 19, 23, 19, 43], \
        [len(b) for b in buckets]
    assert sum(len(b) for b in buckets) == 155

    # the 100th-film fact, from that film's own lead
    y1911 = next(f for f in films if f["t_src"] == "1911")
    assert "100th film as an actor" in y1911["lead_wt"], y1911["lead_wt"][:200]

    # ---- row notes ---------------------------------------------------------
    src_notes = {f["note_src"] for f in films}
    assert src_notes == set(SRC_NOTE), sorted(src_notes ^ set(SRC_NOTE))
    # "Cameo" is the source's own note vocabulary, which is what makes a Role
    # cell reading "Cameo" a credit descriptor rather than a character name
    assert "Cameo" in src_notes and "Cameo" in ROLE_AS_NOTE
    roles = {f["role"] for f in films}
    assert set(ROLE_AS_NOTE) <= roles, sorted(set(ROLE_AS_NOTE) - roles)
    # every row the Notes column calls "Also director" really is in the other
    # table, so dropping that note loses nothing
    for f in films:
        if f["note_src"] == "Also director":
            assert f["qid"] in directed, f["t_src"]

    def note_for(f):
        bits = []
        if f["role"] and f["role"] not in ROLE_AS_NOTE:
            bits.append("As himself" if f["role"].lower() == "himself"
                        else "As %s" % f["role"])
        if alts_of(f):
            bits.append("Also known as %s" % and_list(alts_of(f)))
        if f["role"] in ROLE_AS_NOTE:
            bits.append(ROLE_AS_NOTE[f["role"]])
        extra = SRC_NOTE[f["note_src"]]
        if extra and extra not in bits:
            bits.append(extra)
        d = directed.get(f["qid"])
        verbs = []
        if d:
            verbs.append("co-directed" if d["note_src"] == "Co-director"
                         else "directed")
            if d["writer"] == "yes":
                verbs.append("wrote")
        if f["producer"] == "yes" or (d and d["prod"] == "yes"):
            verbs.append("produced")
        if verbs:
            bits.append("He %s it too" % and_list(verbs))
        if len(set(f["runtime_mins"])) > 1:
            bits.append("Cut differently for different markets — its article "
                        "gives %s" % f["runtime_raw"])
        if f["note_src"] == "Directioral debut":
            bits.append("His first film as a director")
        if f["t_src"] == "Big and Little Wong Tin Bar":
            bits.append("His first film, at eight")
        if f["t_src"] == "Snake in the Eagle's Shadow":
            bits.append("His first major breakthrough")
        if f["t_src"] == "1911":
            bits.append("Its article calls it his 100th film as an actor")
        return join_bits(*bits)

    # ---- section intros, every number in them computed ---------------------
    def n_cuts(i):
        return sum(1 for f in buckets[i] if len(set(f["runtime_mins"])) > 1)

    def n_dir(i):
        return sum(1 for f in buckets[i] if f["qid"] in directed)

    def n_us(i):
        return sum(1 for f in buckets[i]
                   if "United States" in (f.get("country") or ""))

    def n_voice(i):
        return sum(1 for f in buckets[i] if "(voice)" in f["role"])

    def n_unlinked(i):
        return sum(1 for f in buckets[i] if not f["target"])

    assert [n_cuts(i) for i in range(6)] == [1, 1, 1, 4, 0, 1], \
        [n_cuts(i) for i in range(6)]
    assert [n_dir(i) for i in range(6)] == [0, 1, 6, 4, 0, 2], \
        [n_dir(i) for i in range(6)]
    assert [n_us(i) for i in range(6)] == [1, 0, 4, 4, 7, 14], \
        [n_us(i) for i in range(6)]
    assert n_voice(5) > sum(n_voice(i) for i in range(5)), \
        [n_voice(i) for i in range(6)]
    assert n_unlinked(0) == 16, n_unlinked(0)
    assert buckets[1][0]["t_src"] == "New Fist of Fury", buckets[1][0]["t_src"]
    assert {"Rush Hour 2", "Rush Hour 3", "The Tuxedo", "Shanghai Noon"} <= \
        {f["t_src"] for f in buckets[4]}
    assert buckets[2][0]["t_src"] == "The Young Master", buckets[2][0]["t_src"]
    assert buckets[2][-1]["t_src"] == "Project A II", buckets[2][-1]["t_src"]
    assert buckets[5][0]["t_src"] == "The Forbidden Kingdom", buckets[5][0]
    sitas = next(f for f in buckets[1]
                 if f["t_src"] == "Snake in the Eagle's Shadow")
    dm = next(f for f in buckets[1] if f["t_src"] == "Drunken Master")
    assert sitas["year"] == dm["year"] == 1978, (sitas["year"], dm["year"])

    def intro_for(i):
        got = buckets[i]
        n, lo, hi = len(got), got[0]["year"], got[-1]["year"]
        if i == 0:
            return ("%s years of extra work, bit parts and stunt falls, and "
                    "every one of them is a row because the source's Actor "
                    "column says yes to it. That same column is what keeps A "
                    "Touch of Zen out, where its note reads Stuntman Only. "
                    "Both Bruce Lee films are in — he is a named henchman in "
                    "each. %s of these %d never got a Wikipedia article at "
                    "all, so they carry no id."
                    % (word(hi - lo + 1).capitalize(),
                       word(n_unlinked(i)).capitalize(), n))
        if i == 1:
            return ("%s films in four years, and the turn is in the middle of "
                    "them: Snake in the Eagle's Shadow, which the filmography "
                    "calls his first major breakthrough, and Drunken Master "
                    "in the same year. The name changes here too — the "
                    "article says his stage name was changed for New Fist of "
                    "Fury, the first film in this section — and so does the "
                    "first film he directed." % word(n).capitalize())
        if i == 2:
            return ("The article's heading for this era claims 1980 and so "
                    "does the one before it. Its own prose breaks the tie: "
                    "both 1980 films are discussed here and neither is "
                    "mentioned there. So it opens on The Young Master and "
                    "Battle Creek Brawl, his Hollywood debut, and closes on "
                    "Project A II — %d films, %s of which he directed."
                    % (n, word(n_dir(i))))
        if i == 3:
            return ("%s films, and the run most people mean by Jackie Chan: "
                    "Police Story 2, Drunken Master II, Rumble in the Bronx, "
                    "then Rush Hour. It is also where the re-cutting "
                    "concentrates — %s of the %s films on this list with more "
                    "than one running time are in here."
                    % (word(n).capitalize(), word(n_cuts(i)), word(len(cuts))))
        if i == 4:
            return ("%s films and not one of them re-cut, which no other "
                    "section can say. %s name the United States among their "
                    "countries, up from %s in the section before — Shanghai "
                    "Noon, both Rush Hour sequels, The Tuxedo — and %s of the "
                    "%d rows are cameos or guest spots."
                    % (word(n).capitalize(), word(n_us(i)).capitalize(),
                       word(n_us(i - 1)),
                       word(sum(1 for f in got
                                if f["note_src"] in ("Cameo", "Guest appearance")
                                or f["role"] == "Cameo")), n))
        return ("The biggest section on the page at %d films, because the "
                "article's last heading is open-ended: it reads 2008 to "
                "present and has since 2008. From The Forbidden Kingdom to "
                "%d, taking in 1911, which its own article calls his 100th "
                "film as an actor. %s rows are voice roles, more than the "
                "rest of the list put together." % (n, hi, word(n_voice(i)).capitalize()))

    # ---- build --------------------------------------------------------------
    sections = []
    for i, (lo, hi, title, head) in enumerate(spans):
        got = buckets[i]
        items = []
        for f in got:
            it = {"id": "jc-%d-%s" % (f["year"], slug(f["t_src"])),
                  "t": f["t_src"], "n": str(f["year"])}
            note = note_for(f)
            if note:
                it["note"] = note
            if has_id(f):
                it["q"] = f["qid"]
            items.append(it)
        span = ("%d" % got[0]["year"] if got[0]["year"] == got[-1]["year"]
                else "%d–%d" % (got[0]["year"], got[-1]["year"]))
        sections.append({"id": SECTION_IDS[i], "title": title,
                         "sub": "%s · %d films" % (span, len(got)),
                         "intro": intro_for(i), "items": items})
    sections[0]["open"] = True

    rows = [x for s in sections for x in s["items"]]
    assert len(rows) == 155, len(rows)
    assert len({x["id"] for x in rows}) == 155, "duplicate row id"
    assert all("w" not in x for x in rows), "this list is unweighted"
    assert sum(1 for x in rows if "q" in x) == 133
    assert sum(1 for x in rows if x.get("note")) == 155 - sum(
        1 for f in films if not note_for(f))
    for s in sections:
        assert all(a["n"] <= b["n"] for a, b in zip(s["items"], s["items"][1:]))

    # ---- the films this list shares with other lists here ------------------
    keys = {normt(f["t_src"]) + "|" + str(f["year"]) + "|f": f["t_src"]
            for f in films}
    qids = {f["qid"] + "|f": f["t_src"] for f in films if has_id(f)}
    shared = overlaps(keys, qids)
    # What was true when this was written. A NEW list arriving with one of
    # these films must not break the build — sibling agents ship lists daily
    # and the prose below is computed from `shared` — so these are subset
    # checks. What must never change is that these seven still pair: a group
    # going missing means a title or a year drifted (CLU-191/CLU-247).
    for k, v in {
            "Best Picture": ["Beauty and the Beast"],
            "Cult Classics": ["Enter the Dragon"],
            "Disney": ["Beauty and the Beast", "Mulan"],
            "The Criterion Collection": ["Police Story", "Police Story 2",
                                         "Supercop"],
            # the four martial-arts lists built alongside this one. If one of
            # these ever fails it means that list dropped the film or renamed
            # it AND lost its id — delete the line only after checking which.
            "Bruce Lee": ["Fist of Fury", "Enter the Dragon", "Fist of Unicorn"],
            "Jet Li": ["The Forbidden Kingdom", "The Founding of a Republic"],
            "Donnie Yen": ["Vampire Effect", "The Twins Effect II",
                           "Shanghai Knights"],
            "Jean-Claude Van Damme": ["Kung Fu Panda 2", "Kung Fu Panda 3"],
    }.items():
        if k in shared or k in ("Best Picture", "Cult Classics", "Disney",
                                "The Criterion Collection"):
            assert set(v) <= set(shared.get(k) or []), (k, shared.get(k))
    # Vampire Effect is the row that proves the ids earn their keep: Donnie
    # Yen's list calls the same 2003 film The Twins Effect, so the title lane
    # cannot see it and only the shared Wikidata id pairs them.
    if "Donnie Yen" in shared:
        assert "Vampire Effect" in shared["Donnie Yen"], shared["Donnie Yen"]
    paired = sorted({t for v in shared.values() for t in v},
                    key=[f["t_src"] for f in films].index)
    assert len(paired) >= 5, paired
    sharing = ("%s. Ticking one ticks the other: rows pair across lists by "
               "title and year, and by the film's Wikidata id where a list "
               "carries one. The ids are doing nearly all of the work here — "
               "they are how the Criterion discs pair at all, since Criterion "
               "numbers its rows instead of dating them, and how this list's "
               "Vampire Effect finds the same 2003 film on the Donnie Yen "
               "list, where it is called The Twins Effect. Nothing is "
               "duplicated and no hours are counted twice, because every "
               "list totals only its own rows."
               % "; ".join("%s on %s" % (and_list(v), k)
                           for k, v in sorted(shared.items())))

    p = {
        "slug": SLUG,
        "title": "Jackie Chan",
        "subtitle": "every acting credit, in year order",
        "kind": "films",
        # Household-name band, level with the two other actors at the top of
        # this catalogue: Clint Eastwood and Tom Cruise are both 79 and he is
        # recognised as widely, in more countries, off Rush Hour, The Karate
        # Kid and Kung Fu Panda alone. Below 80 because that band is
        # franchise-scale here (Godzilla, Nolan, Sailor Moon) and this is one
        # performer. POPULARITY.md says the gap between 79 and 80 is noise.
        "popularity": 79,
        "year": "1962–2026",
        "blurb": "A hundred and fifty-five films over sixty-four years, from "
                 "uncredited extra to Hollywood and back. Every credit the "
                 "filmography marks him an actor in.",
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        # Measured in CIELAB against every accent in properties/index.json;
        # see scratch/agent-jackie/accent.py. Gold is the obvious colour here
        # — Golden Harvest made most of these — and it is also, at this grid
        # resolution, very nearly the freest pair left in a 202-list
        # catalogue: 15.6 worst-case CIE76 against 16.0 for the best pair
        # anywhere on the wheel (a magenta with nothing to do with him).
        # Everything brighter in the same hue is taken and taken closely:
        # #C9A227 is Deadwood exactly, #8A6D1F is 2.5 from Star Wars, the
        # Rush Hour orange 4.1 from Mission: Impossible, the flag red 7.0
        # from FLCL.
        #
        # CLU-544 corrected the dark half. That reasoning measured PAIRS in
        # CIE76, and both mistakes mattered: the dark tone it picked, #A68930,
        # was Bruce Lee's #A68930 exactly, and comparing pairs could not see it
        # because the two lists' light halves differ. #C08800 is the same brass
        # one step brighter, dE00 7.97 from Bruce Lee and 6.6 from Jet Li — the
        # three martial-arts lists stay a family, which is deliberate, without
        # two of them being the same colour. Light half untouched.
        "accent": "#4B3B06",
        "accentDark": "#C08800",
        "tiers": False,
        "notes": [
            ["The list is the source's Actor column, nothing else.",
             "The filmography's acting table has a Credited as header over "
             "two yes-or-no columns, Actor and Producer, and the first one is "
             "the whole rule: a row is here when it says yes. %d of its %d "
             "rows do. That is what settles the hard case — the early career "
             "is almost all extra work and stunt work, and the column says "
             "yes to the Bruce Lee films, where he is a named henchman in "
             "both Fist of Fury and Enter the Dragon, and no to A Touch of "
             "Zen, whose note reads Stuntman Only. On-screen bit parts are "
             "in. Pure stunt and crew credits are out. Each row then says "
             "what the credit was in the source's own words, down to "
             "Uncredited and As Extra."
             % (len(acted), len(table))],
            ["The %d rows it says no to, and what they are."
             % len(crew),
             "%s producer-only credits — Read Lips, Rouge, Rice Rhapsody, "
             "Everlasting Regret, Golden Job and the rest — and %s more where "
             "he is neither: A Touch of Zen and The Private Eyes (Stuntman "
             "Only), The Young Dragons, The 36 Crazy Fists, Dance of Death, "
             "Immortal Warriors and The Outlaw Brothers (action director or "
             "stunt coordinator), The Magnificent Monk (As writer), Game of "
             "Death (In scripts only), Center Stage, Gen-Y Cops and Home "
             "Operation (Presenter only), and Painted Faces. Two more rows "
             "go for a different reason: Rush Hour 4 and Armour of God IV "
             "sit under a Year column reading TBA, and announced work needs "
             "a date from the source, even just a year."
             % (word(len(prod_only)).capitalize(), word(len(neither)))],
            ["Films only, and the source drew that line too.",
             "The filmography keeps short films in their own table (%s of "
             "them), documentaries in another (%s), and television in a third "
             "(%s scripted series and %s reality shows). None of that is "
             "here, which is the rule the Kevin Bacon and Clint Eastwood "
             "lists follow. What the source does not carry anywhere is a "
             "credited-name column, so no row claims one; the article does "
             "say his stage name was changed for New Fist of Fury in 1976, "
             "and the section covering that year says so."
             % (word(len(data["shorts"])), word(len(data["docs"])),
                word(len(data["tv_scripted"])), word(len(data["tv_reality"])))],
            ["Three and four names a film, and the row carries all of them.",
             "The title on each row is the one the filmography table itself "
             "prints, which is why it says Vampire Effect, Battle Creek Brawl "
             "and Armour of God (Operation Condor). Every other name the "
             "source gives follows it after Also known as — the film's own "
             "article title where that differs, then the alternates that "
             "article marks in bold. %d rows carry at least one, and Twin "
             "Dragons carries four. This is also why the ids matter: %d rows "
             "carry the film's Wikidata id, taken from the wikilink the "
             "table's own title cell gives and never from a title lookup, "
             "and the %d that do not are rows the source never linked — they "
             "ship with no id rather than a wrong one. The source proves the "
             "point on itself, since its own directing table spells two of "
             "the same films differently and all thirteen still match on the "
             "id." % (len(alted), len(with_q), len(unlinked))],
            ["%s films exist in more than one cut. Each still gets one row."
             % word(len(cuts)).capitalize(),
             "They were re-cut for release abroad, sometimes losing twenty "
             "minutes: %s. The note on each gives its article's figures "
             "verbatim instead of picking a winner, because on The Protector "
             "it is the US cut that runs longer. A second row would pair "
             "wrongly across lists and count the film twice."
             % and_list("%s at %s" % (f["t_src"],
                                      " and ".join("%d" % m for m in
                                                   dict.fromkeys(f["runtime_mins"])))
                        for f in cuts)],
            ["No bar widths, and that is deliberate.",
             "%d of the %d rows have no running time in any source read here "
             "— %d are films the filmography never linked to an article, and "
             "%s more have an article with no runtime in it. A list cannot "
             "mix weighted and unweighted rows, because a row with no weight "
             "silently counts as one hour, and zero-weighting a fifth of the "
             "early career would draw a chart whose first section is "
             "invisible. So nothing here is weighted and every film counts "
             "as one."
             % (len(no_rt), len(films), len(unlinked), word(len(art_no_rt)))],
            ["The six sections are the article's own eras.",
             "Not invented decades: they are the six dated subheadings under "
             "Film career on the Jackie Chan article, with the year ranges "
             "stripped off the front and left in the section subtitles. One "
             "of them, 1976-1980, overlaps the next, 1980-1987, and the "
             "article's own prose breaks the tie — both 1980 films are "
             "discussed under the later heading and neither is mentioned "
             "under the earlier one, so 1980 sits there. The last heading "
             "reads 2008 to present, which is why the last section is the "
             "biggest."],
            ["%s of these films are on another list here."
             % word(len(paired)).capitalize(), sharing],
            "Roster, credits, roles and every scope decision from Wikipedia's "
            "Jackie Chan filmography, read from the acting, short film, "
            "directing, documentary and television tables themselves; the "
            "sections and the career facts from the Jackie Chan article; the "
            "alternate titles and the alternate-cut running times from each "
            "film's own article; the cross-list ids from Wikidata.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d films, unweighted, %d with ids"
          % (out.name, len(rows), len(with_q)))
    for s in sections:
        print("   %-6s %-46s %3d  %s"
              % (s["id"], s["title"][:46], len(s["items"]), s["sub"]))
    print("   shared: %s"
          % "; ".join("%s: %s" % (k, ", ".join(v))
                      for k, v in sorted(shared.items())))


if __name__ == "__main__":
    main()
