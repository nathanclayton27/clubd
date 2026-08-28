"""CLU-123: run the reveal-word heuristic over every note and judge each hit.

The rules this applies, all Nathan's, from CLU-59 (2026-08-24) and CLU-123
(2026-08-27):

  * a section HEADER naming an arc is structure, not a spoiler; the same words
    on an item note are a spoiler;
  * viewing and skip advice is never a spoiler;
  * tone warnings are not spoilers unless brutal;
  * a creator-run boundary is "totally fine not a spoiler";
  * a resurrection or return is "never not spoil that one" — always tagged;
  * a first appearance is fine on COMICS ONLY, and only where it was already
    cover-billed or solicited; a surprise entry takes the tag, and every
    non-comics list takes the tag;
  * a logline is fine only if it matches the publisher's own original copy;
  * ambiguous defaults to hidden until adjudicated.

⚠ ONE PATTERN IS DELIBERATELY NOT APPLIED. The structural finale ("the last
episode of the season") — Nathan questioned it rather than ruling: "kind of a
pointless message, if it doesnt even need to exist right?" The proposed answer
was to DELETE such notes where a section header already shows the structure.
That is destructive and has never been approved, so this reports those notes
and changes nothing about them.

Nothing here edits a property file. It prints a corpus for review.

    python tools/spoilerscan.py            # counts + the cases needing him
    python tools/spoilerscan.py --all      # every candidate with its verdict
"""
import glob
import io
import json
import os
import re
import sys

REVEAL = re.compile(
    r"\b(kill(s|ed|er)?|dies|died|death|dead|finale|final\s+episode|twist|"
    r"reveal(s|ed|ing)?|betray(s|ed|al)?|identity|returns?|resurrect\w*|"
    r"comes?\s+back|is\s+back|last\s+episode|ending|the\s+end\b)\b", re.I)

ADVICE = re.compile(
    r"\b(watch|read|play|skip|start|stop|begin|version|cut|dub|sub|"
    r"collection|available|streaming|order|optional|instead|first|before|"
    r"after|edition|remaster|port|delisted|recap)\b", re.I)

QUOTED = re.compile(r'[“"][^”"]{4,}[”"]')
ALTTITLE = re.compile(r'\balso (published|known|released|titled) as\b', re.I)
CREATOR_END = re.compile(r"\b\w+(’s|'s)\s+(finale|final|last|run ends?)\b", re.I)
FIRST_APP = re.compile(r"\bfirst\s+appearance\b", re.I)
RUN_BOUND = re.compile(r"\b(run|era)\s+(starts?|begins?|opens?|ends?)\b|"
                       r"\b(starts?|begins?)\s+(here|with)\b", re.I)
RESURRECT = re.compile(r"\b(resurrect\w*|returns?\b|is\s+back|comes?\s+back|"
                       r"revived?)\b", re.I)
STRUCTURAL = re.compile(r"\b(last|final)\s+(episode|issue|chapter|part|"
                        r"volume|entry)\b|\bfinale\b|"
                        r"\bthe\s+end\s+of\s+the\s+\w+\s+"
                        r"(continuity|run|saga|era)\b|"
                        r"\bthe\s+end\s+of\s+the\s+(run|original\s+run|"
                        r"television\s+continuity|infinity\s+saga)\b|"
                        r"\bthe\s+(trilogy|saga)'?s\s+(close|end)\b", re.I)

COMICS = ("comics", "manga")

# Broadcast, release and biography. "Aired as one hour-long episode" and "out
# six days after his death" are facts about the making of a thing, not about
# what happens inside it.
PRODUCTION = re.compile(
    r"\b(aired|airs|broadcast|released?|out\s+(six|five|\d+)\s+\w+|"
    r"one\s+hour-long|two-and-a-half-hour|posthumous\w*|stock\s+footage|"
    r"look-alike|stunt\s+double|written\s+as|directed|produced|"
    r"finished\s+\w+\s+years?\s+after)\b", re.I)

# Story CONTENT rather than position: a proper name that is not the work's own,
# a war ending, a character doing something. Deliberately narrow — it is the
# difference between "Series finale" (fine) and "the Lambent, Adam Fenix, and
# the end of the war" (not).
NAMES_PLOT = re.compile(
    r"\bthe\s+end\s+of\s+the\s+(war|world|universe)\b|"
    r"\b(murderer|killer)\s*:|"
    r"·\s*[A-Z][a-z]+\s+[A-Z][a-z]+,\s+and\s+the\s+end\b|"
    r"\b(and\s+the\s+end\s+of\s+the)\b", re.I)


def judge(note, kind, where):
    """(verdict, rule, needs_nathan)"""
    if where == "section":
        return "structure", "a section header naming an arc is structure", False
    # The work's own NAME is not a reveal. "The Night Gwen Stacy Died" is what
    # the issue is called, exactly as "Everything dies" is a quoted arc title
    # on the Secret Wars list — a case the note standard already settled.
    if QUOTED.search(note):
        return "fine", "a quoted story or issue title is the thing's name", False
    # Bibliography, not plot: Agatha Christie novels were retitled for other
    # markets, so "Also published as Death in the Air" is a catalogue fact.
    if ALTTITLE.search(note):
        return "fine", "an alternate publication title, not a reveal", False
    # Content beats position. This is checked BEFORE the structural branch
    # because a note can be both — "The trilogy's close — the Lambent, Adam
    # Fenix, and the end of the war" is a position marker that then says what
    # happens, and the second half is what matters.
    if NAMES_PLOT.search(note):
        return ("SPOILER", "names story content, not just a position", False)
    if RESURRECT.search(note):
        return "SPOILER", "a resurrection or return — \"never not spoil that one\"", False
    if FIRST_APP.search(note):
        if any(c in (kind or "").lower() for c in COMICS):
            return ("review", "first appearance on comics — legal only if it "
                    "was cover-billed or solicited, which the note does not say",
                    True)
        return "SPOILER", "first appearance outside comics always takes the tag", False
    if CREATOR_END.search(note):
        return "fine", "a creator run ending is a run boundary, not a reveal", False
    if RUN_BOUND.search(note):
        return "fine", "a creator-run boundary — \"is totally fine not a spoiler\"", False
    # Production and biography are not plot. "Out six days after his death"
    # is a fact about Bruce Lee, not about the film; "aired as one hour-long
    # episode" is a broadcast fact.
    if PRODUCTION.search(note) and not NAMES_PLOT.search(note):
        return "fine", "a production or biographical fact, not a reveal", False
    if STRUCTURAL.search(note):
        # A bare position marker says WHERE you are, not what happens —
        # "Series finale", "season finale", "Part 2 of the three-part finale".
        # Nathan separately thinks many of these are pointless, but pointless
        # and spoiler are different questions and only the first is unruled.
        if not NAMES_PLOT.search(note):
            return ("fine", "a structural position marker — says where you are, "
                    "not what happens", False)
        return ("SPOILER", "a finale note that also names story elements — the "
                "position is fine, the contents are not", False)
    if ADVICE.search(note) and not re.search(r"\b(dies|death|killer|betray)\b",
                                             note, re.I):
        return "fine", "viewing or skip advice is never a spoiler", False
    return "review", "ambiguous — defaults to hidden until adjudicated", True


def main():
    show_all = "--all" in sys.argv
    notes = 0
    hits = []
    for p in sorted(glob.glob("properties/*.json")):
        if p.endswith("search.json"):
            continue
        try:
            d = json.loads(io.open(p, encoding="utf-8").read())
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        slug = os.path.basename(p)[:-5]
        kind = d.get("kind") or ""
        for s in d.get("sections") or []:
            for where, text in ([("section", s.get("sub") or "")]
                                + [("item", (r.get("note") or ""))
                                   for r in (s.get("items") or [])]):
                if not text:
                    continue
                notes += 1
                if REVEAL.search(text):
                    v, why, ask = judge(text, kind, where)
                    hits.append((slug, kind, where, text, v, why, ask))

    print("notes scanned      : %d" % notes)
    print("reveal-word hits   : %d across %d lists"
          % (len(hits), len({h[0] for h in hits})))
    for v in ("SPOILER", "fine", "structure", "review"):
        print("   %-10s %d" % (v, len([h for h in hits if h[4] == v])))

    ask = [h for h in hits if h[6]]
    print()
    print("NEEDS A HUMAN: %d across %d lists"
          % (len(ask), len({h[0] for h in ask})))
    for slug, kind, where, text, v, why, _ in (hits if show_all else ask)[:40]:
        print("  %-26s %-7s %s" % (slug[:26], where, text[:76]))
        print("       -> %s: %s" % (v, why))


if __name__ == "__main__":
    main()
