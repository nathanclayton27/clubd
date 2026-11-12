#!/usr/bin/env python3
"""Generate properties/pta.json.

    PYTHONIOENCODING=utf-8 python tools/make_pta.py

Every feature Paul Thomas Anderson has directed, in release order — the ten
rows of the Feature films table in Wikipedia's "Paul Thomas Anderson
filmography", Hard Eight (1996) to One Battle After Another (2025). Every one
of those rows is a bare {{Yes}} in the Director column.

WHY THREE SECTIONS, AND WHERE THE LINES FALL

His own article names the spine: it says he is "noted for his collaborations
with the cinematographer Robert Elswit ... the composers Jon Brion and Jonny
Greenwood". Both of those collaborations end and begin at a single point in
the run, and the two points are where the sections divide. Neither line is a
mood; both are read off the infoboxes of the films themselves.

  * 1996–2002 — Elswit shot all four and the music is Brion's and Penn's.
    Hard Eight is the only row on the whole list where the filmography's own
    Producer column says No, and the only feature adapted from his own earlier
    work. Then five years with no feature.
  * 2007–2014 — Jonny Greenwood scores There Will Be Blood and has scored
    every Anderson feature since; he scored none before. Elswit shoots the
    first and the last of these three, and The Master is the one break in his
    run. Two of the three come from novels.
  * 2017–2025 — Elswit shot six of the first seven features and none of these.
    The filmography's DoP column marks two rows as his, Phantom Thread
    (uncredited) and Licorice Pizza, and both sit here; Michael Bauman shares
    the second and shot One Battle After Another alone.

WHAT STAYS OUT

  * The 24 music videos. Not features, and — the measured half of the reason —
    not one of the 24 has a Wikidata item naming him as director, so not one
    could carry a runtime from the single source this list weighs by.
  * The 13 short films. Only three of them (The Dirk Diggler Story, Cigarettes
    & Coffee, Couch) can be weighted from that source. Three of thirteen is a
    subset, not the shorts, and an unweighted row in a weighted list is
    silently counted as an hour downstream.
  * Junun (2015). The article files it in a second, differently shaped table
    under a Documentaries heading below the features, alongside the 2026
    concert film Cameron Winter at Carnegie Hall. And the prose settles it
    independently of the layout: in the sentence immediately after the Junun
    paragraph the article calls Phantom Thread his eighth film, and Phantom
    Thread is the eighth row of the feature table. Licorice Pizza is called
    the ninth, One Battle After Another the tenth. The source counts ten, and Junun is not one of them.
  * The Miscellaneous credits — four uncredited rewrites, a stand-by directing
    job, an executive producer credit — and the television, the stage play and
    the acting cameos.

RUNTIMES

All ten from Wikidata P2047 and nothing else, each gated on a P577 publication
year within a year of the filmography's year, and read at STATEMENT RANK. That
last part is load-bearing exactly once and spectacularly: One Battle After
Another's item carries 161 minutes and 162 minutes, both deprecated as
approximations, beside a preferred 9,691 seconds marked "most precise value".
gwlib.wikidata.runtime is rank-blind and takes the longest in-range value, so
it returns 162 — the rounded figure the database itself struck out. The
collector reads rank and unit instead; gwlib is left alone, because every
other list in the catalogue is built on its current behaviour.

Data: scratch/pta/collect.py -> scratch/pta/pta_data.json
Accent: scratch/pta/accent.py
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop
from gwlib.prop import slug

SLUG = "pta"
DATA = pathlib.Path(__file__).resolve().parent.parent / "scratch" / "pta" / "pta_data.json"

# small counts read as words in the shipped prose, but the count itself still
# comes off the collected data rather than being typed
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}

ERAS = [
    ("elswit", "Elswit, Brion and Penn", 1996, 2002,
     "Four features in six years with one team behind them. Robert Elswit "
     "shot all four; the music is Jon Brion's and Michael Penn's. Hard Eight "
     "is the only row on this list where the filmography's Producer column "
     "says no, and the only feature he adapted from his own earlier work. "
     "Then five years with no feature at all."),
    ("greenwood", "Jonny Greenwood arrives", 2007, 2014,
     "Greenwood has written the music for every Anderson feature from There "
     "Will Be Blood onward and for none before it, which is where this line "
     "falls. Elswit shot the first and the last of these three; The Master is "
     "the one break in a run of his that had held since 1996. Two of the "
     "three are adapted from novels."),
    ("bauman", "After Elswit", 2017, 2025,
     "Elswit shot six of the first seven features and none of these. The "
     "filmography's DoP column marks two rows as his, Phantom Thread "
     "(uncredited) and Licorice Pizza, and both are here; Michael Bauman "
     "shares the second of those and shot One Battle After Another on his "
     "own. Greenwood is still writing the music, and the three came out four "
     "years apart."),
]

# Row notes say what the film IS: where it came from, or who held the camera.
# Nothing here is typed from memory — every claim is cross-checked below
# against the table cell or the infobox field it came out of.
NOTES = {
    "Hard Eight": "His feature debut, from his own 1993 short Cigarettes & "
                  "Coffee · original title Sydney",
    "Punch-Drunk Love": "Its transitions are abstract video art by Jeremy Blake",
    "There Will Be Blood": "From the Upton Sinclair novel Oil!",
    "The Master": "Shot by Mihai Mălaimare Jr., the one break in Robert "
                  "Elswit's run",
    "Inherent Vice": "From the Thomas Pynchon novel",
    "Phantom Thread": "He shot it himself, uncredited",
    "Licorice Pizza": "He shares the cinematography credit with Michael Bauman",
    "One Battle After Another": "Inspired by the Thomas Pynchon novel Vineland",
}


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    films = data["features"]
    docs, shorts, mvs = data["documentaries"], data["shorts"], data["music_videos"]
    bio, labels = data["biography"], data["rank_labels"]

    # ---- the list itself ---------------------------------------------------
    assert len(films) == 10, len(films)
    assert films[0]["t"] == "Hard Eight" and films[0]["year"] == 1996, films[0]
    assert films[-1]["t"] == "One Battle After Another" and \
        films[-1]["year"] == 2025, films[-1]
    assert all(f["year"] <= g["year"] for f, g in zip(films, films[1:])), \
        "features are not in release order"
    assert len({f["year"] for f in films}) == 10, "two features share a year"
    # he wrote all ten — the table's own Writer column, and the infoboxes,
    # which put his name under `writer` on nine and `screenplay` on the tenth
    assert all(f["wrote"] for f in films), \
        [f["t"] for f in films if not f["wrote"]]
    assert all("Paul Thomas Anderson" in (f["article"].get("writer") or
                                          f["article"].get("screenplay") or "")
               for f in films), \
        [f["t"] for f in films
         if "Paul Thomas Anderson" not in (f["article"].get("writer") or
                                           f["article"].get("screenplay") or "")]

    # ---- runtimes: one source, one rank conflict, named ---------------------
    assert all(f["runtime"] for f in films), \
        "unweighted row in a weighted list: %s" \
        % [f["t"] for f in films if not f["runtime"]]
    assert all(f["runtime_src"] == "P2047" for f in films), \
        "a runtime came from somewhere other than P2047: %s" \
        % [(f["t"], f["runtime_src"]) for f in films
           if f["runtime_src"] != "P2047"]
    assert all(f["qid"] and f["year_gate"] for f in films), \
        [f["t"] for f in films if not (f["qid"] and f["year_gate"])]
    assert all(f["pubyears"] for f in films), \
        [f["t"] for f in films if not f["pubyears"]]

    # Nine items carry exactly one runtime statement, at normal rank, in
    # minutes. The tenth is the whole reason this list does not use gwlib's
    # reader, so it is checked value by value.
    plain = [f for f in films if len(f["p2047_seen"]) == 1]
    assert len(plain) == 9, [f["t"] for f in films if len(f["p2047_seen"]) != 1]
    assert all(s["rank"] == "normal" and s["unit"] == "Q7727"
               for f in plain for s in f["p2047_seen"]), \
        [(f["t"], f["p2047_seen"]) for f in plain
         if any(s["rank"] != "normal" for s in f["p2047_seen"])]

    obaa = films[-1]
    seen = {(s["amount"], labels[s["unit"]], s["rank"]) for s in obaa["p2047_seen"]}
    assert seen == {(161.0, "minute", "deprecated"),
                    (162.0, "minute", "deprecated"),
                    (9691.0, "second", "preferred")}, seen
    # Wikidata's own stated reasons, quoted rather than paraphrased in the note
    why = {s["rank"]: {p: [labels[i] for i in ids]
                       for p, ids in s["quals"].items()}
           for s in obaa["p2047_seen"]}
    dep = [s for s in obaa["p2047_seen"] if s["rank"] == "deprecated"]
    assert all("approximation" in [labels[i] for i in s["quals"]["P2241"]]
               for s in dep), why
    assert {labels[i] for s in dep for i in s["quals"]["P1013"]} == \
        {"truncation", "rounding"}, why
    pref = [s for s in obaa["p2047_seen"] if s["rank"] == "preferred"][0]
    assert [labels[i] for i in pref["quals"]["P7452"]] == ["most precise value"], why
    assert abs(obaa["runtime"] - 9691 / 60.0) < 1e-9, obaa["runtime"]
    # ...and the number a rank-blind reader would have shipped instead, so the
    # note's claim about it is a measurement rather than a story
    rankblind = max(s["amount"] for s in obaa["p2047_seen"]
                    if s["unit"] == "Q7727" and 15 <= s["amount"] <= 250)
    assert rankblind == 162.0, rankblind
    assert round(obaa["runtime"] / 60.0, 2) != round(rankblind / 60.0, 2), \
        "the rank conflict stopped changing the shipped weight — recheck the " \
        "item before trusting this list's reader over gwlib's"

    # ---- the collaborator lines the sections are cut on ---------------------
    def dp(f):
        return f["article"].get("cinematography", "")

    def score(f):
        return f["article"].get("music", "")

    elswit = [f["t"] for f in films if "Robert Elswit" in dp(f)]
    assert elswit == ["Hard Eight", "Boogie Nights", "Magnolia",
                      "Punch-Drunk Love", "There Will Be Blood",
                      "Inherent Vice"], elswit
    # six of the first seven, and none after 2014 — both halves of the line
    assert set(elswit) <= {f["t"] for f in films[:7]} and len(elswit) == 6, elswit
    assert not any("Robert Elswit" in dp(f) for f in films if f["year"] >= 2017)
    greenwood = [f["t"] for f in films if "Jonny Greenwood" in score(f)]
    assert greenwood == [f["t"] for f in films if f["year"] >= 2007] and \
        len(greenwood) == 6, greenwood
    assert all("Jon Brion" in score(f) or "Michael Penn" in score(f)
               for f in films if f["year"] <= 2002), \
        [(f["t"], score(f)) for f in films if f["year"] <= 2002]
    assert "Robert Elswit" in bio["sentences"]["collaborations"] and \
        "Jonny Greenwood" in bio["sentences"]["collaborations"] and \
        "Jon Brion" in bio["sentences"]["collaborations"], \
        bio["sentences"]["collaborations"]

    # the table's own Producer and DoP (cinematographer) columns
    unproduced = [f["t"] for f in films if not f["produced"]]
    assert unproduced == ["Hard Eight"], unproduced
    selfshot = [f["t"] for f in films if f["shot"]]
    assert selfshot == ["Licorice Pizza"], selfshot
    # Phantom Thread's cell is {{partial|Uncredited}}, and its infobox gives
    # the camera to him alone: the row note says exactly that
    unshot = [f["t"] for f in films if f["shot_uncredited"]]
    assert unshot == ["Phantom Thread"], unshot
    assert dp(films[7]) == "Paul Thomas Anderson", dp(films[7])
    assert "Michael Bauman" in dp(films[8]) and \
        "Paul Thomas Anderson" in dp(films[8]), dp(films[8])
    assert dp(films[9]) == "Michael Bauman", dp(films[9])
    assert dp(films[5]) == "Mihai Mălaimare Jr.", dp(films[5])
    # four years apart, three times over
    late = [f["year"] for f in films if f["year"] >= 2017]
    assert [b - a for a, b in zip(late, late[1:])] == [4, 4], late
    assert films[4]["year"] - films[3]["year"] == 5, "the five-year gap moved"

    # ---- what the row notes claim, checked against the source ---------------
    assert "Cigarettes & Coffee" in films[0]["article"]["based_on"] and \
        "Paul Thomas Anderson" in films[0]["article"]["based_on"], \
        films[0]["article"].get("based_on")
    # ...and it is the only one adapted from his own work, which is what the
    # first section's intro says
    ownwork = [f["t"] for f in films
               if "Anderson" in (f["article"].get("based_on") or "")]
    assert ownwork == ["Hard Eight"], ownwork
    novels = [f["t"] for f in films if 2007 <= f["year"] <= 2014
              and f["article"].get("based_on")]
    assert novels == ["There Will Be Blood", "Inherent Vice"], novels
    assert [s["t"] for s in shorts if s["t"] == "Cigarettes & Coffee"] and \
        [s["year"] for s in shorts if s["t"] == "Cigarettes & Coffee"] == [1993]
    assert films[0]["tablenote"] == "Original title: Sydney", films[0]["tablenote"]
    assert "Jeremy Blake" in films[3]["article"]["lead"], films[3]["article"]["lead"]
    assert "Upton Sinclair" in films[4]["article"]["based_on"] and \
        "''[[Oil!]]''" in films[4]["article"]["based_on_raw"], \
        films[4]["article"].get("based_on_raw")
    assert "Thomas Pynchon" in films[6]["article"]["based_on"], films[6]
    assert "''[[Vineland]]''" in films[9]["article"]["based_on_raw"] and \
        "Thomas Pynchon" in films[9]["article"]["based_on"], \
        films[9]["article"].get("based_on_raw")
    # "inspired by" rather than "from": the article's own prose calls it loose
    assert any(o["n"] == 10 and "loose adaptation" in o["window"]
               and "Vineland" in o["window"] for o in bio["ordinals"]), \
        bio["ordinals"]

    # ---- Junun, as the source's arithmetic rather than an opinion -----------
    assert [d["t"] for d in docs] == ["Junun", "Cameron Winter at Carnegie Hall"], \
        [d["t"] for d in docs]
    junun = docs[0]
    assert junun["t"] not in {f["t"] for f in films}, "Junun reached the features"
    assert junun["credit"] == "Director and camera operator", junun["credit"]
    assert junun["year"] == 2015 and junun["runtime"] == 54, junun
    # the table it sits in also holds his 2026 concert film, which has no
    # article of its own and links into the Live at Carnegie Hall album page:
    # a table of his non-fiction work rather than a second feature table
    assert docs[1]["year"] == 2026 and \
        docs[1]["credit"] == "Director and camera operator" and \
        docs[1]["section_of"] == \
        "Live at Carnegie Hall (Cameron Winter album)#Concert film", docs[1]
    assert "documentary" in bio["sentences"]["junun"], bio["sentences"]["junun"]
    # and the article's own numbering, which never counts it. Every "Anderson's
    # Nth film" the prose states must name the Nth row of the feature table;
    # three of the four are after 2015, so if Junun were a feature they would
    # all be off by one.
    assert len(bio["ordinals"]) >= 4, bio["ordinals"]
    for o in bio["ordinals"]:
        assert 1 <= o["n"] <= len(films), o
        assert films[o["n"] - 1]["t"] in o["window"], \
            "the article calls something else his %s film: %r" \
            % (o["said"], o["window"][:160])
    after = sorted({o["n"] for o in bio["ordinals"]
                    if films[o["n"] - 1]["year"] > junun["year"]})
    assert after == [8, 9, 10], after

    # ---- the music videos and the shorts, as arithmetic ---------------------
    assert len(mvs) == 24, len(mvs)
    assert (mvs[0]["year"], mvs[0]["performer"]) == (1997, "Michael Penn") and \
        "Try" in mvs[0]["t"], mvs[0]
    assert (mvs[-1]["year"], mvs[-1]["performer"]) == (2024, "The Smile") and \
        "Friend of a Friend" in mvs[-1]["t"], mvs[-1]
    # not one of the 24 has a Wikidata item claiming him as director, so not
    # one could be weighted from this list's single runtime source
    assert not any(v["qid"] for v in mvs), [v["t"] for v in mvs if v["qid"]]
    assert len(shorts) == 13, len(shorts)
    weightable = [s["t"] for s in shorts if s["runtime"]]
    assert weightable == ["The Dirk Diggler Story", "Cigarettes & Coffee",
                          "Couch"], weightable
    assert all(s["runtime_src"] == "P2047" for s in shorts if s["runtime"])
    assert len(weightable) * 3 < len(shorts), weightable   # a subset, not the shorts
    # the sweep found nothing the tables missed: ten features, Junun, and six
    # things that are shorts or television
    assert data["sweep_size"] == len(films) + 1 + len(data["sweep_extras"]), data["sweep_size"]
    assert {e["label"] for e in data["sweep_extras"]} == \
        {"Saturday Night Live", "The Dirk Diggler Story", "Cigarettes & Coffee",
         "Couch", "Back Beyond", "ANIMA"}, data["sweep_extras"]
    assert len(data["misc"]) == 6 and len(data["television"]) == 4, \
        (len(data["misc"]), len(data["television"]))
    uncredited = [m["t"] for m in data["misc"]
                  if m["credit"] == "Uncredited rewrite"]
    assert uncredited == ["Corky Romano", "Killers of the Flower Moon",
                          "Napoleon", "What Happens at Night"], uncredited
    assert [m["t"] for m in data["misc"] if m["credit"] == "Stand-by director"] \
        == ["A Prairie Home Companion"], data["misc"]
    assert [m["t"] for m in data["misc"] if m["credit"] == "Executive producer"] \
        == ["Waterlily Jaguar"], data["misc"]

    # ---- sections -----------------------------------------------------------
    sections = []
    for key, title, lo, hi, intro in ERAS:
        got = [f for f in films if lo <= f["year"] <= hi]
        assert got, key
        items = []
        for f in got:
            it = {"id": "pta-%d-%s" % (f["year"], slug(f["t"])),
                  "t": f["t"], "n": str(f["year"]),
                  "w": round(f["runtime"] / 60.0, 2)}
            if f["t"] in NOTES:
                it["note"] = NOTES[f["t"]]
            items.append(it)
        sec = {"id": key, "title": title,
               "sub": "%d–%d · %d films · about %d hours"
                      % (got[0]["year"], got[-1]["year"], len(got),
                         round(sum(f["runtime"] for f in got) / 60.0)),
               "intro": intro, "items": items}
        if key == "elswit":
            sec["open"] = True
        sections.append(sec)

    placed = sum(len(s["items"]) for s in sections)
    assert placed == len(films), (placed, len(films))
    for s in sections:
        assert all(a["n"] < b["n"] for a, b in zip(s["items"], s["items"][1:])), \
            "%s is out of year order" % s["title"]
    noted = {x["t"] for s in sections for x in s["items"] if x.get("note")}
    assert noted == set(NOTES), (sorted(noted), sorted(NOTES))
    # nothing unweighted anywhere: a row with no `w` in a weighted list is
    # silently worth one hour, and this list is weighted end to end
    assert all(isinstance(x.get("w"), float) and x["w"] > 0
               for s in sections for x in s["items"]), \
        [x["id"] for s in sections for x in s["items"] if not x.get("w")]

    hours = sum(x["w"] for s in sections for x in s["items"])
    mins = sum(f["runtime"] for f in films)
    assert abs(hours - mins / 60.0) < 0.1, (hours, mins / 60.0)

    # the infobox figures, for the note that discloses the disagreement. They
    # are never a weight; they exist here only so the note can quantify what
    # keeping to one source costs.
    box = {}
    for f in films:
        v = (f["article"].get("runtime") or "").split()[0]
        box[f["t"]] = int(v) if v.isdigit() else None
    assert all(box.values()), box
    differ = [(f["t"], f["runtime"], box[f["t"]]) for f in films
              if abs(box[f["t"]] - f["runtime"]) >= 0.5]
    # Boogie Nights left this list in November 2026, when Wikidata's figure
    # moved from 149 to the infobox's 155
    assert [t for t, _, _ in differ] == ["Hard Eight", "The Master"], differ
    # One Battle After Another is deliberately not in that list: its infobox
    # 162 is the same runtime rounded, which is exactly what Wikidata's
    # deprecated statement says it is
    assert abs(box[obaa["t"]] - obaa["runtime"]) < 0.5, \
        (box[obaa["t"]], obaa["runtime"])
    boxmins = sum(box.values())

    p = {
        "slug": SLUG,
        "title": "Paul Thomas Anderson",
        "subtitle": "the directed features",
        "kind": "films",
        # Enthusiast-canonical: anyone who follows film can name him, and the
        # name thins out quickly beyond that. Sits under the Coen Brothers (67)
        # and Wes Anderson (68), over David Lynch (64) and Akira Kurosawa (62).
        "popularity": 66,
        # Not a story, so not a sequence: the order these came out in
        # is a fact about the maker, not an instruction to the viewer
        # (Nathan, CLU-372). Prerequisites, where any exist, live in
        # tools/data/sequences.json and are enforced separately.
        "random": True,
        "year": "1996–2025",
        "blurb": "Ten features in release order, Hard Eight to One Battle "
                 "After Another — about %d hours." % round(hours),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        # measured against every accent in properties/index.json — see
        # scratch/pta/accent.py. Every obvious pick is taken: the Punch-Drunk
        # Love blue lands 6.4 from Persona's, the Inherent Vice purple 6.4 from
        # Evangelion's, the Magnolia green is Zelda's exactly. The catalogue's
        # freest corner is the magenta-to-aubergine band, and it is honestly
        # his — Jeremy Blake's video interludes and the Phantom Thread mauves.
        # Worst-case CIE76 17.0, against 18.3 for the freest pair on the whole
        # wheel; nearest neighbour is JoJo's #7A2E5F at 17.0.
        "accent": "#4C104A",
        "accentDark": "#A484A3",
        "tiers": False,
        "notes": [
            ["Ten features, and the count is the table's.",
             "The Feature films table in Wikipedia's Paul Thomas Anderson "
             "filmography has ten rows, Hard Eight to One Battle After "
             "Another, and every one of them is a bare yes in the Director "
             "column. A sweep of every Wikidata item that names him as "
             "director returns %d: these ten, Junun, and six things that are "
             "short films or television. Nothing the table left out is a "
             "feature." % data["sweep_size"]],
            ["Junun is not here.",
             "The article puts it in a second, differently shaped table under "
             "a Documentaries heading below the features, where his credit "
             "reads director and camera operator and the only other row is "
             "Cameron Winter at Carnegie Hall, a 2026 concert film. Wikidata "
             "gives it %d minutes. And "
             "the prose settles it independently of the layout: in the "
             "sentence straight after the Junun paragraph the article calls "
             "Phantom Thread his eighth film, and Phantom Thread is the "
             "eighth row of the feature table. Licorice Pizza is the ninth "
             "there and One Battle After Another the tenth. The source counts "
             "ten features, and Junun is not one of them."
             % junun["runtime"]],
            ["No music videos, no shorts, no rewrites.",
             "The article's Music Videos table has %d rows, from Michael "
             "Penn's Try in 1997 to The Smile's Friend of a Friend in 2024, "
             "and not one of them has a Wikidata item naming him as director "
             "— so not one could carry a runtime from the single source this "
             "list weighs by. The Short films table has %d rows and only "
             "three can be weighted from it: The Dirk Diggler Story, "
             "Cigarettes & Coffee and Couch. Three of thirteen is a subset "
             "rather than the shorts, and an unweighted row in a weighted "
             "list is silently counted as an hour. The Miscellaneous credits "
             "are other people's films: %s uncredited rewrites, a stand-by "
             "directing job on A Prairie Home Companion, "
             "and an executive producer credit on Waterlily Jaguar."
             % (len(mvs), len(shorts), WORDS[len(uncredited)])],
            ["Bar widths are runtimes, and one of them was contested.",
             "All ten come from Wikidata's P2047 and from nothing else, in "
             "hours, each gated on a release year within a year of the "
             "filmography's, and read at statement rank. Rank matters exactly "
             "once. One Battle After Another's item carries three runtimes: "
             "161 minutes and 162 minutes, both marked deprecated with the "
             "reason given as approximation — one truncated, one rounded — "
             "and 9,691 seconds, marked preferred for being the most precise "
             "value. That is 161 minutes and 31 seconds, and it is what this "
             "list weighs. A reader that ignored rank would have taken the "
             "longest of the three and shipped 162, a figure the database "
             "itself has struck out."],
            ["Two runtimes disagree with the film's own article.",
             "Wikidata says %d minutes for Hard Eight where its article's "
             "infobox says %d, and %d for The Master against %d. One source "
             "is kept for all ten rather "
             "than the longest number from whichever source offers it, "
             "because a list that mixes them is a list whose total means "
             "nothing. Going by the infoboxes instead would add about %d "
             "minutes to the %d hours."
             % (films[0]["runtime"], box["Hard Eight"],
                films[5]["runtime"], box["The Master"],
                round(boxmins - mins), round(hours))],
            "Filmography from Wikipedia's Paul Thomas Anderson filmography, "
            "read from the tables themselves; the writing, camera and music "
            "credits from each film's own article; runtimes from Wikidata, "
            "gated on a matching release year and read at statement rank.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == 10, len(ids)
    print("wrote %s — %d films, %.2f minutes, %.2f hours"
          % (out.name, len(ids), mins, hours))
    for s in sections:
        print("   %-26s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))
    print("   rank conflict on %s: %s -> kept %.2f min (%d s), rank-blind "
          "would give %d" % (obaa["t"],
                             [(s["amount"], labels[s["unit"]], s["rank"])
                              for s in obaa["p2047_seen"]],
                             obaa["runtime"], round(obaa["runtime"] * 60),
                             rankblind))
    print("   out: %d music videos, %d shorts (%d weightable), Junun (%d min)"
          % (len(mvs), len(shorts), len(weightable), junun["runtime"]))


if __name__ == "__main__":
    main()
