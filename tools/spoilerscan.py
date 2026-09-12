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

THE ADJUDICATED CORPUS (Nathan, 2026-08-28: "All of this looks good"). These
are the cases the rules above did not settle, ruled once so nobody re-argues
them. This section is the point of the file — read it before adding a rule.

  1. A BARE ISSUE TITLE in the note field is not a spoiler; it is the comic's
     name. "Death and Glory", "The Dead Zone, Part 1", "Death on the Ice
     Field". ⚠ Unlike "The Night Gwen Stacy Died" these are unquoted, so
     nothing distinguishes a title from a description except knowing the list.
     **When writing new notes, quote the title** and this stops being a
     judgement call.
  2. A FIRST APPEARANCE whose character's name is itself a reveal word is fine
     where it was cover-billed — sandman's "Death's debut" is on every cover of
     that collection, which is exactly the carve-out his comics rule describes.
  3. A TEASE THAT NAMES NO OUTCOME is fine: "The Hobgoblin's identity", "its
     ending echoes forward", "an ending people argue about". It says a thing
     matters without saying what it is.
  4. A LOGLINE DESCRIBING A PREMISE is fine — but see the taste rule below.
  5. A FILM'S ACTUAL TITLE containing a reveal word is fine, same as 1.
  6. PRODUCTION AND BIOGRAPHICAL FACTS are not plot: "out six days after his
     death", "his last film", "aired as one hour-long episode".

⚠ THE TASTE RULE, and it is the one that needs a person rather than a regex.
Nathan, on premise notes: "make sure to do your best to make it so a premise
note is obviously not a crazy spoiler for something recommended to go in blind.
Like an explainer on the substance kind of ruins it a bit."

A premise note is a categorisation — body-swap's register is
`country · who swaps · mechanism · runtime`, and for Freaky Friday all of that
is on the poster. For a film whose turn IS the premise, it is not. The Substance
named "Elisabeth Sparkle and Sue", which gives away that a second self exists;
it now names only Elisabeth. **Where a work is best met cold, the note says
less.** No heuristic can find these — ask whether the trailer said it.

THE STRUCTURAL FINALE IS NOW RULED, AND IT IS DESTRUCTIVE. Nathan first
questioned it — "kind of a pointless message, if it doesnt even need to exist
right?" — and on 2026-08-28 ruled: "Yeah delete those notes if they're actually
pointless."

⚠ "Pointless" means CARRYING NOTHING, not mentioning a finale. Ten notes were
deleted: a bare "season finale" on the LAST row of a section already titled
"Season 1", where the header and the position already say it. **Thirty-two were
kept**, because they carry something the header does not — farscape's
"concluded in season 2", frasier's "aired as one hour-long episode",
childs-play's "the show was cancelled after three seasons", and
amazing-spider-man's "Stern's finale", which is a creator-run boundary rather
than a structural one. Deleting those would have destroyed real information
under cover of a tidy-up.

WHAT IT READS, and it used to read less than it claimed. Until CLU-276 this file
walked section subtitles and item notes and nothing else, so two whole surfaces
of the site were never scanned: the LIST-LEVEL `notes` array, and section
`intro`. A provenance note or a "how to use this page" note could carry a reveal
and the scan would come back clean, because it never opened the array. Both are
now walked, and the per-scope table prints so a count can be read for what it
covers.

Section TITLES stay out on purpose: "a section HEADER naming an arc is
structure, not a spoiler" is Nathan's ruling, and `sub` rides on the same ruling.
An `intro` does not — rule 08 of the note standard makes it prose for starting
cold, not a header — so it is judged like any other note.

⚠ THE VERDICTS ON THE TWO NEW SCOPES ARE NOT CALIBRATED, and the counts must not
be read as though they were. `judge()` was written against terse ROW notes and
adjudicated there ("All of this looks good", 2026-08-28). A list note and an
intro are long prose, and the RESURRECT branch matches a bare "return" in any
sense — so it fires on era names ("the 2010s returns"), work titles ("Samus
Returns", "Akaza Returns"), production facts ("the rest of the cast return"),
cancellations ("it would not return for a fifth"), renumberings ("the title
returns to its legacy count") and a director going back to London. Of the 48
SPOILER verdicts the two new scopes produce, I read about four as real.

The regex is NOT narrowed here, deliberately: the same branch is what catches a
genuine resurrection on a row note, Nathan adjudicated those verdicts as they
stand, and retuning it would quietly invalidate that sign-off. Calibrating for
long prose is its own job and belongs with CLU-123's corpus run. Until then the
new scopes are a corpus to read, not a verdict to act on.

Nothing here edits a property file. It prints a corpus for review, and always
exits 0: none of this gates a build.

    python tools/spoilerscan.py            # counts + the cases needing him
    python tools/spoilerscan.py --all      # every candidate with its verdict
"""
import collections
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


def note_strings(prop):
    """Every list-level note as one string, heading included.

    A note is either a bare string or a [heading, text] pair, and the heading is
    display text too — "Death of Superman." as a heading is as visible as it is
    in a body — so it is scanned rather than dropped.
    """
    out = []
    for n in prop.get("notes") or []:
        if isinstance(n, list):
            head = (n[0] if len(n) > 0 else "") or ""
            body = (n[1] if len(n) > 1 else "") or ""
            out.append(("%s %s" % (head, body)).strip())
        elif isinstance(n, str):
            out.append(n)
    return [s for s in out if s]


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
    scanned = collections.Counter()
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
        # Every display string a reader can see, in the four scopes that carry
        # prose. `list` and `intro` were the blind spot; see the docstring.
        scoped = [("list", t) for t in note_strings(d)]
        for s in d.get("sections") or []:
            scoped.append(("section", s.get("sub") or ""))
            scoped.append(("intro", s.get("intro") or ""))
            scoped += [("item", (r.get("note") or ""))
                       for r in (s.get("items") or [])]
        for where, text in scoped:
            if not text:
                continue
            notes += 1
            scanned[where] += 1
            if REVEAL.search(text):
                v, why, ask = judge(text, kind, where)
                hits.append((slug, kind, where, text, v, why, ask))

    print("notes scanned      : %d" % notes)
    print("   by scope        : %s"
          % ", ".join("%s %d" % (k, scanned[k])
                      for k in ("list", "section", "intro", "item")))
    print("reveal-word hits   : %d across %d lists"
          % (len(hits), len({h[0] for h in hits})))
    for v in ("SPOILER", "fine", "structure", "review"):
        print("   %-10s %d" % (v, len([h for h in hits if h[4] == v])))
    print("   by scope        : %s"
          % ", ".join("%s %d" % (k, len([h for h in hits if h[2] == k]))
                      for k in ("list", "section", "intro", "item")))
    raw = len([h for h in hits if h[2] in ("list", "intro")])
    if raw:
        print("   ^ %d of those are in `list`/`intro`, scopes opened by CLU-276 "
              "and NOT yet adjudicated" % raw)
        print("     (see the docstring: on long prose the return/resurrection "
              "branch is mostly false)")

    ask = [h for h in hits if h[6]]
    print()
    print("NEEDS A HUMAN: %d across %d lists"
          % (len(ask), len({h[0] for h in ask})))
    rows = hits if show_all else ask
    for slug, kind, where, text, v, why, _ in rows[:40]:
        print("  %-26s %-7s %s" % (slug[:26], where, text[:76]))
        print("       -> %s: %s" % (v, why))
    # The cap used to truncate in silence, which reads as "that was all of them".
    if len(rows) > 40:
        print("  ... %d more not shown (the list is capped at 40)"
              % (len(rows) - 40))


if __name__ == "__main__":
    main()
