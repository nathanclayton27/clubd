"""Pins for the seven CLU-167 parser defects, the two found fixing them, the six
found in the fix, and the two the review of those six found still standing.

    python tools/test_wiki_parser.py

Exit 0 and a green count means clean. No test framework — nothing in this repo
uses one, and this file should run from a bare clone.

EVERY CHECK IS A PIN, NOT A SPOT TEST. A test that only asserts today's right
answer cannot tell a fixed parser from a fixture that never exercised the bug,
so each case asserts twice:

  1. gwlib.wiki, as it stands, gets the right answer; and
  2. the rule that HAD the bug, re-implemented below, gets the exact wrong
     answer that was measured — proving this fixture really does land on it.

So reverting a fix fails (1), and swapping a fixture for a tamer excerpt fails
(2). There are three before-photographs, because there were three rounds of this:

  `_old_*`   the parser as it was at commit 5ad60de, before CLU-167. The seven
             original defects are pinned against these.
  `_d98_*`   the CLU-167 fix as it was at commit d9895ed, which fixed all seven
             and introduced three of its own — it deleted every argument-less
             template it did not recognise, read |RTitle as a plain title, and
             read episode numbers out of a template's arguments and out of the
             two halves of a decimal. Those three are pinned against these.
  `_005_*`   the round-2 parser at commit 005d1ee, which fixed all fifteen of
             those and still fabricated two episode TITLES: it let a footnote
             marker's NAME be part of a title ("The X-Filesdouble dagger"), and
             it let an RTitle that is one whole parenthetical be a title (13
             Frieren shorts called "(Official English title not available)").

None of the three may ever be "fixed"; they are photographs. Each isolates the
one rule that changed in its case and calls the live module for the rest, which
is why each one names the rule it is standing in for. Run this file against
005d1ee's gwlib/wiki.py and exactly the five round-3 tests below fail, while the
other 33 pass — which is the whole claim a pin is making.

The fixtures in tools/data/wiki_fixtures/ are verbatim excerpts of the real
articles, one per case. They are tracked deliberately: the test is worthless
without them, and a test that passes only on the machine that wrote it is the
"someone else pulls the repo and runs it" failure this project has paid for.
Every count quoted in a docstring here is over these tracked fixtures and is
re-derived by the check beside it; counts over the gitignored corpus of cached
articles live in tools/measure_wiki_parser.py, which prints them rather than
remembering them.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import wiki  # noqa: E402

FIX = pathlib.Path(__file__).resolve().parent / "data" / "wiki_fixtures"


def fixture(name):
    return (FIX / (name + ".wiki")).read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# The parser as it was, so each fixture can be shown to hit the defect.
# --------------------------------------------------------------------------
_OLD_BLOCKS = re.compile(r"\{\{(?:#invoke:)?Episode list"
                         r"(?:\s*\|\s*sublist\s*\|[^|\n]*|/sublist[^|}\n]*)?"
                         r"\s*(\|.*?)\n\s*\}\}", re.S | re.I)


def _old_blocks(text):
    """Old block finder: terminated by a LINE-INITIAL `}}` only (defects 1, 2)."""
    return ["\n" + m.group(1) for m in _OLD_BLOCKS.finditer(text)]


def _old_field(block, name):
    """Old field reader: `\\s*` after the `=` crosses newlines (defect 4)."""
    m = re.search(r"\|\s*%s\s*=\s*(.*?)(?=\n\s*\||\Z)" % name, block, re.S)
    return m.group(1).strip() if m else ""


def _old_num(v):
    """Old number reader: the first run of digits, the rest discarded (defect 3)."""
    m = re.search(r"\d+", v)
    return int(m.group(0)) if m else None


def _old_clean(t):
    """Old clean(): no comment rule (defect 5); an argument-less template falls
    through to bare brace-stripping and survives as its own name (defect 7)."""
    t = re.sub(r"<ref[^>]*/>", "", t or "")
    t = re.sub(r"<ref.*?</ref>", "", t, flags=re.S)
    for _ in range(3):
        t = re.sub(r"\{\{\s*(?:efn|refn|sfn|notetag)[^{}]*\}\}", "", t, flags=re.I)
    t = re.sub(r"<br\s*/?>", ", ", t)
    t = re.sub(r"\{\{(?:ubl|unbulleted list|plainlist)\s*\|", "", t, flags=re.I)
    t = re.sub(r"\s*\n\s*\*\s*", ", ", t)
    t = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", t)
    t = re.sub(r"\[\[([^\]]+)\]\]", r"\1", t)
    t = re.sub(r"\{\{[^{}|]*\|(?:[^{}|]*\|)*([^{}|]*)\}\}", r"\1", t)
    t = t.replace("{{", "").replace("}}", "").replace("''", "")
    return re.sub(r"\s+", " ", t).strip(" ,|")


# --------------------------------------------------------------------------
# The CLU-167 fix as it was at d9895ed, so the three defects IT introduced can
# be shown to be what these fixtures land on. One rule each, verbatim.
# --------------------------------------------------------------------------
_D98_BARE = {
    "hsp": "", "nbsp": " ", "thinsp": " ", "shy": "", "wbr": "", "zwsp": "",
    "snd": " – ", "spnd": " – ", "sndash": " – ", "spndash": " – ",
    "spaced en dash": " – ", "ndash": "–", "en dash": "–", "mdash": "—",
    "em dash": "—", "spaces": " ", "'": "'", "'s": "'s",
}


def _d98_bare(name):
    """clean()'s argument-less-template rule at d9895ed: resolve against a fixed
    table and DROP anything not in it, "because a template name is never the
    text a reader wants". {{Yes}}, {{No}}, {{TBA}} and {{n/a}} are not in it."""
    return _D98_BARE.get(name.strip().lower(), "")


def _d98_title(fields):
    """episodes()' title rule at d9895ed: Title -> RTitle -> AltTitle, cleaned,
    then `.strip('"')` — which takes one quote off each end of display markup
    and ships whatever is left."""
    return wiki.clean(wiki.field(fields, "Title", "RTitle", "AltTitle")
                      or "").strip('"')


def _d98_numbers(fields, base="EpisodeNumber"):
    """numbers()' digit rule at d9895ed: every run of digits in the CLEANED
    value, so a template's own arguments and both halves of a decimal each come
    back as an episode."""
    return [int(d) for d in re.findall(r"\d+", wiki.clean(fields.get(base) or ""))]


# --------------------------------------------------------------------------
# The THIRD before-photograph: the parser at 005d1ee, which fixed all fifteen
# above and left two titles fabricated. One rule each, written out rather than
# derived from the live module, because a photograph that tracks the thing it
# photographs is not a photograph.
# --------------------------------------------------------------------------
_005_BARE_RENDERS = {
    "hsp": "", "nbsp": " ", "thinsp": " ", "shy": "", "wbr": "", "zwsp": "",
    "snd": " – ", "spnd": " – ", "sndash": " – ", "spndash": " – ",
    "spaced en dash": " – ", "ndash": "–", "en dash": "–", "mdash": "—",
    "em dash": "—", "spaces": " ", "'": "'", "'s": "'s",
    "pagename": "", "episode cast": "",
}


def _005_clean(t):
    """clean() at 005d1ee: the live function with _BARE_RENDERS as it was — no
    footnote-marker family — so {{double dagger}} and {{asterisk}} missed the
    allowlist and took rule 7's keep-the-NAME default, which is right for
    {{yes}} and {{TBA}} and fabricates for a marker."""
    live = wiki._BARE_RENDERS
    wiki._BARE_RENDERS = _005_BARE_RENDERS
    try:
        return wiki.clean(t)
    finally:
        wiki._BARE_RENDERS = live


def _005_display_title(raw):
    """display_title() at 005d1ee: accept a wholly-quoted value, refuse one
    still carrying a quote or an HTML tag, and accept EVERYTHING else — which
    let a legend marker stay welded to a name and let a whole parenthetical be
    a name. _WHOLLY_QUOTED is the live one; it did not change."""
    t = _005_clean(raw or "")
    m = wiki._WHOLLY_QUOTED.match(t)
    if m:
        return m.group(1).strip()
    if '"' in t or "<" in t or ">" in t:
        return ""
    return t


# --------------------------------------------------------------------------
# The FOURTH before-photograph: the parser at b51e564, the round-3 fix as it
# merged. It fixed the argument-LESS marker and the whole parenthetical, and
# left standing the two defects CLU-531 carded: a marker written WITH an
# argument still leaked the argument, and a bare placeholder was still a title.
#
# Both are swaps of the one thing that moved rather than copies of the whole
# function, exactly as _005_clean is: for the marker it is the pattern that
# recognises an argumented marker, and for the placeholder it is the set of
# words that are not names. Switch them off and the module IS b51e564 --
# display_title()'s only other change was `return m.group(1).strip()` becoming
# an assignment, which is the same function when the set is empty.
# --------------------------------------------------------------------------
_B51_NOTHING = re.compile(r"(?!x)x")       # matches nowhere in any string


def _b51_clean(t):
    """clean() at b51e564: no argumented-marker pass, so `{{dagger|sup=yes}}`
    and `{{double dagger|alt=Award winner}}` fell through to the keep-the-last-
    argument rule and an editor's rendering hint became display text."""
    live = wiki._MARKER_WITH_ARGS
    wiki._MARKER_WITH_ARGS = _B51_NOTHING
    try:
        return wiki.clean(t)
    finally:
        wiki._MARKER_WITH_ARGS = live


def _b51_display_title(raw):
    """display_title() at b51e564: reading that clean(), and with no
    placeholder rule — so a value with no quote, no tag, no marker glyph and
    no brackets left in it was a title, whatever it said."""
    live_m, live_p = wiki._MARKER_WITH_ARGS, wiki._PLACEHOLDER_TITLES
    wiki._MARKER_WITH_ARGS, wiki._PLACEHOLDER_TITLES = _B51_NOTHING, frozenset()
    try:
        return wiki.display_title(raw)
    finally:
        wiki._MARKER_WITH_ARGS, wiki._PLACEHOLDER_TITLES = live_m, live_p


# --------------------------------------------------------------------------
# 1. a block closed at the first line-initial `}}` and swallowed the next row
# --------------------------------------------------------------------------
def test_inline_close_does_not_swallow_the_next_row():
    t = fixture("ds9-s5-assignment-tribbleations")

    eq(len(_old_blocks(t)), 1, "old: two rows read as one")
    eq(len(wiki.templates(t, "Episode list")), 2, "new: two blocks")

    eps = wiki.episodes(t)
    eq(len(eps), 2, "Deep Space Nine season 5 rows")
    eq([e.title for e in eps],
       ["The Assignment", "Trials and Tribble-ations"], "both titles present")
    eq([(e.num_overall, e.num_in_season) for e in eps],
       [(103, 5), (104, 6)], "both rows numbered")

    # The row that closes inline (`|LineColor=1C39BB}}`) is row 1; the old
    # reader's single oversized block took every field from it, which is how
    # "Trials and Tribble-ations" left no trace at all — not a blank row, no row.
    old = _old_blocks(t)[0]
    eq(_old_field(old, "EpisodeNumber"), "103", "old block starts at row 1")
    ok("Trials and Tribble-ations" in old, "old block ran on into row 2")
    ok("Trials and Tribble-ations" not in
       _old_clean(_old_field(old, "Title")), "old: row 2's title unreachable")

    # Each block is brace-balanced and carries its own 11 arguments.
    for b in wiki.templates(t, "Episode list"):
        eq(b.count("{{"), b.count("}}"), "block is brace-balanced")
    eq([len(e.fields) for e in eps], [11, 11], "11 fields per row")


def test_a_row_that_closes_inline_with_nothing_after_it_survives():
    """The milder half of defect 1 was a swallowed row. The worse half: with no
    later `\\n}}` to stop at, an inline-closed LAST row matched nothing and
    vanished, so a table simply ended short with no wrong title to notice."""
    t = fixture("ds9-s5-assignment-tribbleations")
    alone = wiki.templates(t, "Episode list")[0]  # the inline-closed row, solo
    ok(alone.rstrip().endswith("|LineColor=1C39BB}}"), "this row closes inline")

    eq(len(_old_blocks(alone)), 0, "old: the row deletes itself")
    eq(len(wiki.episodes(alone)), 1, "new: the row is read")
    eq(wiki.episodes(alone)[0].title, "The Assignment", "and keeps its title")


# --------------------------------------------------------------------------
# 2. a multi-line nested template ended the block early
# --------------------------------------------------------------------------
def test_nested_multiline_template_does_not_end_the_block():
    t = fixture("enterprise-s1-strange-new-world")
    ok(re.search(r"\n\s+\}\}\n", t), "the nested {{StoryTeleplay}} closes on its own line")

    old = _old_blocks(t)[0]
    eq(_old_field(old, "EpisodeNumber"), "", "old: numbering fell outside the block")
    eq(_old_num(_old_field(old, "EpisodeNumber")), None, "old: ships unnumbered")
    ok("LineColor" not in old, "old block was cut at the nested close")

    e, = wiki.episodes(t)
    eq((e.num_overall, e.num_in_season), (4, 4), "Strange New World is 4 / 4x04")
    eq(e.title, "Strange New World", "title")
    eq(e.year, 2001, "year")
    for name in ("EpisodeNumber", "EpisodeNumber2", "ProdCode", "Viewers",
                 "ShortSummary", "LineColor", "WrittenBy"):
        ok(name in e.fields, "%s is inside the block" % name)
    ok("slabel" not in e.fields,
       "the nested template's own pipes are not read as fields")
    ok(e.fields["WrittenBy"].startswith("{{StoryTeleplay"), "WrittenBy whole")


# --------------------------------------------------------------------------
# 3a. EpisodeNumber read as the first number only (`53<hr>54`)
# --------------------------------------------------------------------------
def test_hr_separated_numbers_are_both_read():
    t = fixture("madmen-s5-a-little-kiss")
    f = wiki.template_fields(wiki.templates(t, "Episode list")[0])
    eq(f["EpisodeNumber"], "53<hr>54", "the source says two numbers")

    eq(_old_num("53<hr>54"), 53, "old: 54 silently discarded")
    eq(wiki.numbers(f), [53, 54], "new: both overall numbers")
    eq(wiki.numbers(f, "EpisodeNumber2"), [1, 2], "both in-season numbers")

    e, = wiki.episodes(t)
    eq(e.nums, [53, 54], "row exposes both numbers")
    eq(e.nums2, [1, 2], "and both in-season")
    eq((e.num_overall, e.num_in_season), (53, 1),
       "the 5-tuple still reports the first, for the 22 positional callers")
    eq(e.title, "A Little Kiss", "title")


# --------------------------------------------------------------------------
# 3b. a NumParts row numbered EpisodeNumber_1 / _2 was read as no episode
# --------------------------------------------------------------------------
def test_numbered_suffix_parts_are_collected():
    t = fixture("enterprise-s1-broken-bow")
    old = _old_blocks(t)[0]
    ok("EpisodeNumber_1" in old, "the old block was complete — this is not defect 2")
    eq(_old_field(old, "EpisodeNumber"), "",
       "old: `_1` sits between the name and the `=`, so nothing matched")

    f = wiki.template_fields(wiki.templates(t, "Episode list")[0])
    eq(f["NumParts"], "2", "NumParts")
    eq(wiki.numbers(f), [1, 2], "the two-hour pilot is episodes 1 and 2")
    eq(wiki.numbers(f, "EpisodeNumber2"), [1, 2], "in-season likewise")
    ok(wiki.numbers(f) != [2], "NumParts is not mistaken for a number")
    ok(wiki.numbers(f) != [12], "the suffixed digits are not concatenated")

    e, = wiki.episodes(t)
    eq(e.nums, [1, 2], "row exposes both")
    eq(e.numparts, "2", "and NumParts as written")
    eq(e.title, "Broken Bow", "title")


def test_numparts_alone_does_not_trigger_the_suffix_read():
    """Doctor Who's serials carry NumParts with ONE EpisodeNumber and no
    `EpisodeNumber_` at all. A reader that branches on NumParts — as two of the
    private copies did — returns nothing for every one of them, so the trigger
    is the presence of `EpisodeNumber_1`."""
    serial = ("{{Episode list\n|EpisodeNumber=44\n|Serial=yes\n|NumParts=5\n"
              "|Title=The Rebel Flesh\n|OriginalAirDate={{Start date|2011|5|21}}\n}}")
    f = wiki.template_fields(serial)
    eq(f["NumParts"], "5", "five broadcasts")
    ok("EpisodeNumber_1" not in f, "but no suffixed numbers")
    eq(wiki.numbers(f), [44], "one episode number, not five and not none")


# --------------------------------------------------------------------------
# 4a. an EMPTY field ate its own newline and read back as the line below
# --------------------------------------------------------------------------
def test_empty_field_does_not_read_the_line_below():
    t = fixture("bleach-tybw-ep412")
    old = _old_blocks(t)[0]
    eq(_old_clean(_old_field(old, "Title")), "RTitle =",
       "old: a field NAME shipped as an episode title")

    f = wiki.template_fields(wiki.templates(t, "Episode list")[0])
    eq(f["Title"], "", "present and blank, by construction")
    eq(f["RTitle"], "", "so is RTitle")
    for name in ("DirectedBy", "WrittenBy", "Aux2", "Aux3", "AltDate",
                 "ShortSummary"):
        eq(f[name], "", "%s is present and blank" % name)
    eq(len(f), 13, "all 13 arguments visible")

    e, = wiki.episodes(t)
    eq(e.title, "", "an unannounced title stays empty")
    ok("RTitle" not in e.title, "and is never a field name")
    eq((e.num_overall, e.num_in_season), (412, 46), "numbering still read")
    eq(e.year, 2026, "air date still read")

    # The three-way answer: blank-but-present is not the same as absent.
    eq(wiki.field(f, "Title", "RTitle"), "", "present but blank -> ''")
    eq(wiki.field(f, "Nonexistent"), None, "absent -> None")


# --------------------------------------------------------------------------
# 4b. the same defect on a non-Wikipedia infobox: `|chapters=` -> the arc name
# --------------------------------------------------------------------------
def test_blank_field_on_a_fandom_template_is_not_the_next_line():
    """A blank `|chapters=` means the episode adapts no manga — it is filler.
    Read as the arc name, a filler episode looks canonical, so this defect
    changes a classification and not just a string."""
    t = fixture("bleach-fandom-ep335-infobox")

    eq(_old_field(t, "chapters"),
       "|arc            =[[Reigai Uprising|Gotei 13 Invading Army arc]]",
       "old shape: a filler episode reads as adapted")
    eq(len(wiki.episodes(t)), 0, "not an Episode list, and never was")
    eq(wiki.infobox(t), None, "infobox() is gated to film|television")

    # The generic readers are the point of the card: this template was
    # unreachable through gwlib at all, which is why a private reader got
    # written by a caller with no episode table.
    b, = wiki.templates(t, "Template:Bleach Wiki:Episode Template")
    f = wiki.template_fields(b)
    eq(f["chapters"], "", "blank, meaning anime-original")
    ok("chapters" in f, "and present, so the caller can tell blank from absent")
    eq(f["arc"], "[[Reigai Uprising|Gotei 13 Invading Army arc]]", "arc intact")
    eq(f["episodenumber"], "335", "episode number")
    eq(f["title"], "{{PAGENAME}}", "raw value preserved, not cleaned")
    eq(wiki.numbers(f, "episodenumber"), [335], "numbers() reads it too")
    ok("Title" not in f, "keys are case-sensitive, as MediaWiki parameters are")


# --------------------------------------------------------------------------
# 5. clean() left HTML comments in
# --------------------------------------------------------------------------
def test_html_comments_are_stripped_from_titles():
    t = fixture("invincible-s1-we-need-to-talk")
    raw = wiki.template_fields(wiki.templates(t, "Episode list",
                                              keep_comments=True)[0])["Title"]
    ok("<!--" in raw, "the source title carries an editor's note inline")
    ok(len(_old_clean(raw)) > 200, "old: a 200+ character title")
    ok("Do NOT change this" in _old_clean(raw), "old: the note shipped as the title")

    e, = wiki.episodes(t)
    eq(e.title, "We Need to Talk", "just the title")
    ok("<!--" not in e.title and "MOS:CT" not in e.title, "no note")
    eq(wiki.clean(raw), "We Need to Talk", "clean() strips comments itself")
    eq(wiki.clean("T<!--n-->"), "T", "and does it before anything else")
    eq(wiki.clean("A<!--{{x|y}}|z=-->B"), "AB",
       "a comment cannot confuse the template or pipe passes")


def test_commented_out_rows_are_not_invented():
    """The ordering that stops fabrication. Bleach parks unaired episodes inside
    `<!--…-->`; a brace counter over raw text finds them and returns episodes
    that do not exist — worse than dropping rows, and the one failure the
    no-invented-data rule speaks to directly."""
    t = ("{{Episode list\n|EpisodeNumber=1\n|Title=Real\n"
         "|OriginalAirDate={{Start date|2024|1|1}}\n}}\n"
         "<!--\n{{Episode list\n|EpisodeNumber=2\n|Title=\n|RTitle=\n"
         "|OriginalAirDate=\n}}\n-->\n")
    eq([e.title for e in wiki.episodes(t)], ["Real"], "only the real row")
    eq(len(wiki.templates(t, "Episode list")), 1, "the hidden row is not a block")
    eq(len(wiki.templates(t, "Episode list", keep_comments=True)), 2,
       "unless the caller asks for it explicitly")


def test_a_comment_inside_a_word_is_removed_not_padded():
    """Doctor Who series 9 writes `[[Jamie Mathieson]] a<!--Do not change to &;
    they were not credited that way-->nd Steven Moffat`. A comment can sit
    INSIDE a word, so removing one by padding it with spaces — which is the
    tempting way to keep byte offsets stable — turns "and" into "a nd"."""
    t = ("{{Episode list\n|EpisodeNumber=256\n|Title=The Girl Who Died\n"
         "|WrittenBy=[[Jamie Mathieson]] a<!--Do not change to &-->nd "
         "Steven Moffat\n|OriginalAirDate={{Start date|2015|10|17}}\n}}\n")
    f = wiki.template_fields(wiki.templates(t, "Episode list")[0])
    eq(f["WrittenBy"], "[[Jamie Mathieson]] and Steven Moffat",
       "the word survives whole")
    eq(wiki.clean(f["WrittenBy"]), "Jamie Mathieson and Steven Moffat",
       "and cleans to prose, not 'a nd'")
    ok("  " not in f["WrittenBy"], "no run of padding spaces left behind")


def test_offsets_survive_the_removals():
    """templates() deletes comments and conditional-transclusion wrappers before
    it counts braces, so the offset it reports has to be mapped back to the
    text the caller actually passed in."""
    t = ("<!--a long comment that shifts everything after it-->\n"
         "== Season 1 ==\n{{Episode list\n|EpisodeNumber=1\n|Title=Pilot\n"
         "|OriginalAirDate={{Start date|2024|1|1}}\n}}\n")
    (start, block), = wiki.templates(t, "Episode list", offsets=True)
    eq(t[start:start + 14], "{{Episode list", "offset points into the ORIGINAL text")
    eq(t[:start].count("== Season 1 =="), 1, "so the heading above is findable")


def test_numbers_cleans_before_it_looks_for_digits():
    """`19<ref name="finale2"/>` is episode 19, not episodes 19 and 2. An
    episode conjured out of a ref name is fabricated catalogue data."""
    for raw, want in ((r'19<ref name="finale2"/>', [19]),
                      ("19{{efn|name=n3}}", [19]),
                      ("12<!--do not change to 13-->", [12]),
                      ("1&ndash;2", [1, 2]),
                      ("86<hr />87", [86, 87]),
                      ("", []),
                      ("TBA", [])):
        eq(wiki.numbers({"EpisodeNumber": raw}), want, "numbers(%r)" % raw)


# --------------------------------------------------------------------------
# 6. only |Title was read, never |RTitle
# --------------------------------------------------------------------------
def test_rtitle_is_read_when_there_is_no_title():
    t = fixture("blackmirror-bandersnatch")
    old = _old_blocks(t)[0]
    eq(_old_field(old, "Title"), "", "old: no |Title on the row, so nothing")
    eq(_old_clean(_old_field(old, "Title")), "", "old: a nameless row")

    f = wiki.template_fields(wiki.templates(t, "Episode list")[0])
    ok("Title" not in f, "the row genuinely has no Title")
    eq(wiki.field(f, "Title", "RTitle"),
       "''[[Black Mirror: Bandersnatch|Bandersnatch]]''",
       "field() falls back, and hands back the RAW value, links included")

    e, = wiki.episodes(t)
    eq(e.title, "Bandersnatch", "the interactive film has its name")
    eq((e.num_overall, e.num_in_season), (None, None),
       "unnumbered is correct here — Bandersnatch has no episode number")
    eq(e.nums, [], "and says so as an empty list, not a guess")
    eq(e.year, 2018, "year")


# --------------------------------------------------------------------------
# 7. clean() rendered an argument-less template as its own name
# --------------------------------------------------------------------------
def test_argumentless_templates_do_not_render_as_their_name():
    t = fixture("blackmirror-uss-callister-into-infinity")
    raw = wiki.template_fields(wiki.templates(t, "Episode list")[0])["Title"]
    ok("{{hsp}}" in raw, "the source title carries a hair space template")
    eq(_old_clean(raw), "USS Callisterhsp: Into Infinity",
       "old: the template's NAME shipped inside the title")

    e, = wiki.episodes(t)
    eq(e.title, "USS Callister: Into Infinity", "Black Mirror series 7's finale")
    eq((e.num_overall, e.num_in_season), (33, 6), "numbering")

    # Defect 7 was never about {{hsp}}. clean()'s keep-the-last-argument rule
    # requires a pipe, so EVERY argument-less template fell through to bare
    # brace-stripping; fixing hsp alone would have left the class open.
    for raw_t, old_wrong, new_right in (
            ("X{{nbsp}}Y", "XnbspY", "X Y"),
            ("A{{snd}}B", "AsndB", "A – B"),
            ("{{PAGENAME}}", "PAGENAME", ""),
            ("{{Episode cast}} [[Cristin Milioti]]",
             "Episode cast Cristin Milioti", "Cristin Milioti")):
        eq(_old_clean(raw_t), old_wrong, "old clean(%r)" % raw_t)
        eq(wiki.clean(raw_t), new_right, "new clean(%r)" % raw_t)

    eq(wiki.clean("{{sort|Callister, USS|USS Callister}}"), "USS Callister",
       "a template WITH arguments still keeps its last one")


# --------------------------------------------------------------------------
# 8. real wikitext is not brace-balanced
# --------------------------------------------------------------------------
def test_conditional_transclusion_does_not_break_brace_counting():
    """Doctor Who season 6 writes `<noinclude>{{refn|group=N|</noinclude>`
    `<includeonly>{{efn|</includeonly>` — two opening braces of which MediaWiki
    renders one. Counted raw the page has one more `{{` than `}}`, and every
    private copy of this parser asserts balance, so it would refuse the page."""
    t = ("{{Episode list\n|EpisodeNumber=44\n|Title=The Rebel Flesh"
         "<noinclude>{{refn|group=N|note</noinclude>"
         "<includeonly>{{efn|note</includeonly>}}"
         "\n|OriginalAirDate={{Start date|2011|5|21}}\n}}\n")
    eq(t.count("{{") - t.count("}}"), 1, "raw, the page has one brace too many")
    for view in (wiki.direct_view, wiki.transcluded_view):
        v = view(t)
        eq(v.count("{{"), v.count("}}"), "balanced in %s" % view.__name__)

    # direct_view is the one templates() uses, because a page's own view is
    # where <noinclude> rating columns live and the old regex read them.
    ok("Aux4" in wiki.direct_view("|Viewers=1<noinclude>|Aux4 = 77</noinclude>"),
       "direct_view keeps a noinclude field")
    ok("Aux4" not in
       wiki.transcluded_view("|Viewers=1<noinclude>|Aux4 = 77</noinclude>"),
       "transcluded_view drops it, as the parent page does")

    e, = wiki.episodes(t)
    eq(e.title, "The Rebel Flesh", "and the row reads")
    eq(e.num_overall, 44, "with its number")


# --------------------------------------------------------------------------
# 9. the opening pattern tolerated no whitespace after `{{`
# --------------------------------------------------------------------------
def test_newline_after_the_open_braces_still_matches():
    """The Office's episode list writes `{{\\nEpisode list`, which the old
    pattern could not match at all — a latent row-dropper of exactly this kind."""
    t = ("{{\nEpisode list\n|EpisodeNumber=37\n|Title=Pay Day\n"
         "|OriginalAirDate={{Start date|2009|6|18}}\n}}\n")
    eq(len(_old_blocks(t)), 0, "old: the row was invisible")
    eq([e.title for e in wiki.episodes(t)], ["Pay Day"], "new: the row is read")


# --------------------------------------------------------------------------
# B1. dropping an unknown argument-less template DELETED the cell's content
# --------------------------------------------------------------------------
def test_an_argumentless_template_that_is_the_cell_keeps_its_name():
    """The Child's Play franchise article states an unreleased film's date and
    director as `{{TBA}}` and nothing else. Dropped, the row reads as released
    with no date, which is what tripped make_childs-play.py's own assert:
    `assert f["released"] or "TBA" in f["date_cell"]`."""
    t = fixture("childsplay-franchise-films")
    rows = wiki.table_rows(t, 1, header_probe='! scope="row"')
    eq(len(rows), 9, "nine films in the Films table")

    title_line, cols = rows[7]
    ok("Untitled ''Chucky'' film" in title_line, "the unreleased one")
    eq(wiki.clean(cols[0]), "TBA",
       "its release-date cell is the word TBA, and nothing else")

    eq(_d98_bare("TBA"), "", "d9895ed: dropped, so the cell came back empty")
    eq(wiki.clean("{{TBA}}"), "TBA", "and now it does not")

    # the rows around it are unaffected either way, which is what made the
    # deletion quiet: only the cells whose whole content was a template moved.
    # clean() does not render {{Start date}} — it keeps the last argument, which
    # is the day — and that is the same before and after.
    eq(wiki.clean(rows[6][1][0]), "03", "a dated row is unchanged")
    ok("Curse of Chucky" in rows[5][0], "and the {{efn}} row is still read")
    eq(wiki.clean(rows[5][1][0]), "24",
       "its footnote gone whole, its date cell as it always was")


def test_the_status_template_family_is_text_not_decoration():
    """{{yes}}, {{no}}, {{TBA}}, {{n/a}}, {{won}}, {{nom}} and {{?}} are how
    every awards table and filmography crosstab on Wikipedia says what it says:
    the template's NAME is the entire rendered content of the cell. Measured
    over the cached corpus, dropping them took 498 fields off Jackie Chan's
    filmography and emptied Clint Eastwood's director and producer columns —
    which is why the rule is an allowlist of templates that render nothing and
    a default of keeping the name.

    No fixture: a bare `{{yes}}` has no article context to excerpt, and the
    crosstab that pays for it is pinned by the {{TBA}} case above."""
    for name in ("yes", "no", "Yes", "No", "TBA", "n/a", "na", "won", "nom",
                 "nominated", "ya", "?", "unknown", "win", "notnom"):
        eq(_d98_bare(name), "", "d9895ed dropped {{%s}}" % name)
        eq(wiki.clean("{{%s}}" % name), name,
           "{{%s}} renders as its own name, verbatim case" % name)

    # and the allowlist still wins, so defect 7 does not come back
    for raw, want in (("X{{hsp}}Y", "XY"), ("X{{nbsp}}Y", "X Y"),
                      ("A{{snd}}B", "A – B"), ("{{PAGENAME}}", ""),
                      ("{{Episode cast}} [[Cristin Milioti]]", "Cristin Milioti")):
        eq(wiki.clean(raw), want, "clean(%r)" % raw)


def test_parser_functions_render_as_nothing_not_as_their_source():
    """`{{#expr:5861430+14688240}}` is arithmetic MediaWiki performs. Leaking
    the source text states a number that is not the answer — the pre-CLU-167
    reader did that to 103 CONviewers fields — and this module does not evaluate
    parser functions, so the honest answer is nothing at all."""
    eq(_old_clean("{{#expr:5861430+14688240}}"), "#expr:5861430+14688240",
       "old: the sum's source text shipped as if it were the sum")
    eq(wiki.clean("{{#expr:5861430+14688240}}"), "", "and now nothing does")
    eq(wiki.numbers({"CONviewers": "{{#expr:7.487 round 2}}"}, "CONviewers"), [],
       "so a caller gets no number and fails its own coverage assert")


# --------------------------------------------------------------------------
# B2. reading |RTitle as a plain title FABRICATED eleven Farscape titles
# --------------------------------------------------------------------------
def test_rtitle_that_is_display_markup_does_not_become_a_title():
    """RTitle is where a source puts what |Title cannot hold. Farscape's
    two-parters put the part marker there — `"Nerve" (Part 1)` — and `.strip('"')`
    takes off the trailing quote and leaves `Nerve" (Part 1)`."""
    t = fixture("farscape-s1-nerve-rtitle")
    plain, nerve, hidden = [wiki.template_fields(b)
                            for b in wiki.templates(t, "Episode list")]

    eq(nerve["RTitle"], '"Nerve" (Part 1)', "the source's own display markup")
    ok("Title" not in nerve, "and there is no |Title to prefer")
    eq(_d98_title(nerve), 'Nerve" (Part 1)',
       "d9895ed: a stray quote and a part marker, shipped as an episode title")
    eq(_d98_title(hidden), 'The Hidden Memory" (Part 2)', "and again")

    e_plain, e_nerve, e_hidden = wiki.episodes(t)
    eq(e_nerve.title, "", "an empty title is better than a wrong one")
    eq(e_nerve.rtitle, '"Nerve" (Part 1)',
       "and the raw value is on the row, so a caller can read the part number")
    eq(e_hidden.title, "", "likewise")
    eq((e_nerve.num_overall, e_nerve.num_in_season), (19, 19), "still numbered")
    eq(e_nerve.year, 2000, "still dated")

    # the control: a row on the same table with a real |Title is untouched
    eq(e_plain.title, "Back and Back and Back to the Future", "|Title still wins")
    eq(e_plain.rtitle, "", "and carries no RTitle")


def test_rtitle_that_is_plainly_a_title_is_still_read():
    """The other half, and the reason this is a rule and not a revert: defect 6
    was real. Bandersnatch files its name under RTitle because it has no episode
    number, and three shapes of RTitle are a title and nothing else."""
    t = fixture("blackmirror-bandersnatch")
    e, = wiki.episodes(t)
    eq(e.title, "Bandersnatch", "an italicised link is a title")

    for raw, want in (
            ("''[[Babylon 5: The Gathering]]''", "Babylon 5: The Gathering"),
            ('"[[The Five Doctors]]"', "The Five Doctors"),
            ("Prologue", "Prologue"),
            ("[[Coolio]] & [[Don Rickles]]", "Coolio & Don Rickles"),
            ('"Nerve" (Part 1)', ""),
            ('"Meanwhile, in the TARDIS..." (Part 1)', ""),
            ("''[[Gamera vs. Barugon]]''<br />''<small>(Daikaijū Kettō)</small>''",
             "")):
        eq(wiki.display_title(raw), want, "display_title(%r)" % raw)

    ok(wiki.display_title("A<small>B</small>") == "",
       "clean() strips no HTML tags, so a value still carrying one is refused")


# --------------------------------------------------------------------------
# B3. numbers() read episodes out of template arguments and out of decimals
# --------------------------------------------------------------------------
def test_a_decimal_episode_number_is_one_episode_not_two():
    """Attack on Titan's recap specials are numbered 3.5, 3.25 and 3.75 on the
    list page. Read as digit runs they are episodes 3 and 5, 3 and 25, 3 and 75
    — five episodes conjured out of three, on an article cached in this repo."""
    t = fixture("decimal-and-anchored-episode-numbers")
    rows = [wiki.template_fields(b) for b in wiki.templates(t, "Episode list")]
    eq([r["EpisodeNumber"] for r in rows[:3]], ["3.5", "3.25", "3.75"],
       "the source's own numbering")

    eq([_d98_numbers(r) for r in rows[:3]], [[3, 5], [3, 25], [3, 75]],
       "d9895ed: six episodes where the source states three")
    eq([wiki.numbers(r) for r in rows[:3]], [[3.5], [3.25], [3.75]],
       "one each, and as written — int() would fold all three onto episode 3")

    eps = wiki.episodes(t)
    eq([e.num_overall for e in eps[:3]], [3.5, 3.25, 3.75],
       "the 5-tuple reports the row's own number")
    eq([e.num_in_season for e in eps[:3]], [1, 2, 3], "whole ones stay ints")
    ok(all(isinstance(e.num_in_season, int) for e in eps[:3]),
       "so a caller that only ever sees whole numbers sees ints")
    eq(eps[0].title, "Ilse's Notebook: Memoirs of a Scout Regiment Member",
       "and the row is otherwise unchanged")


def test_a_template_in_a_number_field_does_not_add_an_episode():
    """Doctor Who's two-part stories anchor their rows: `192a{{anchor|ep192}}`.
    clean() resolves that to its last argument, "ep192", so the row reported
    episode 192 twice. {{small}} and {{ref label}} do the same."""
    t = fixture("decimal-and-anchored-episode-numbers")
    dw = wiki.template_fields(wiki.templates(t, "Episode list")[3])
    eq(dw["EpisodeNumber"], "192a{{anchor|ep192}}", "the source's own anchor")

    eq(_d98_numbers(dw), [192, 192], "d9895ed: the anchor's own digits, again")
    eq(wiki.numbers(dw), [192], "once, which is how many times it aired")

    for raw, want in ((r'19<ref name="finale2"/>', [19]),
                      ("19{{efn|name=n3}}", [19]),
                      ("5 {{small|(''22'')}}", [5]),
                      ("44<br />193.5", [44, 193.5]),
                      ("31{{ref label|a|1}}", [31])):
        eq(wiki.numbers({"EpisodeNumber": raw}), want, "numbers(%r)" % raw)


def test_the_suffixed_walk_counts_parts_and_cannot_hang():
    """The `_1`/`_2` walk was indexed by how many NUMBERS it had collected, so a
    part carrying two of them skipped the next part, and a part carrying none
    looked for the same key forever. It walks parts now."""
    eq(wiki.numbers({"EpisodeNumber_1": "53<hr>54", "EpisodeNumber_2": "55"}),
       [53, 54, 55], "a two-number first part does not swallow the second")
    eq(wiki.numbers({"EpisodeNumber_1": "", "EpisodeNumber_2": "7"}), [7],
       "an empty first part does not loop forever")
    eq(wiki.numbers({"EpisodeNumber_1": "1", "EpisodeNumber_2": "2",
                     "EpisodeNumber_3": "3"}), [1, 2, 3], "three parts, in order")

    f = wiki.template_fields(
        wiki.templates(fixture("enterprise-s1-broken-bow"), "Episode list")[0])
    eq(wiki.numbers(f), [1, 2], "Broken Bow is still episodes 1 and 2")


def test_a_numparts_disagreement_is_reported_and_not_raised():
    """NumParts counts BROADCASTS and the suffixed keys count numbers, which the
    old cross-check conflated and then raised over — taking the row, and through
    episodes() the whole page, down over an inconsistency in the source."""
    # three parts' worth of numbers over two parts is not a disagreement, and
    # this is the case the old cross-check raised over
    notes = []
    eq(wiki.numbers({"EpisodeNumber_1": "53<hr>54", "EpisodeNumber_2": "55",
                     "NumParts": "2"}, notes=notes), [53, 54, 55],
       "two parts, three numbers, and no complaint about it")
    eq(notes, [], "because NumParts counts parts, which is what is compared")

    # a real disagreement: one numbered part against a claim of two broadcasts
    notes = []
    eq(wiki.numbers({"EpisodeNumber_1": "1", "NumParts": "2"}, notes=notes), [1],
       "the number still comes back")
    eq(len(notes), 1, "and the disagreement is recorded")
    ok("NumParts" in notes[0], "naming what disagreed: %r" % (notes[0:1],))

    notes = []
    eq(wiki.numbers({"EpisodeNumber_1": "1", "EpisodeNumber_2": "2",
                     "NumParts": "2"}, notes=notes), [1, 2], "agreement")
    eq(notes, [], "says nothing")


# --------------------------------------------------------------------------
# B5. one malformed block used to take the whole page, and all 69 callers, down
# --------------------------------------------------------------------------
def test_one_unclosed_block_does_not_empty_the_page():
    """A vandalised or mid-edit article emptying a catalogue list is worse than
    the row-dropping this file was rewritten to stop. The old regex skipped one
    malformed row and returned the rest; so does this, and it says which."""
    t = ("{{Episode list\n|EpisodeNumber=1\n|Title=Pilot\n"
         "|OriginalAirDate={{Start date|2024|1|1}}\n}}\n"
         "{{Episode list\n|EpisodeNumber=2\n|Title=Vandalised\n|Aux1={{\n"
         "{{Episode list\n|EpisodeNumber=3\n|Title=Third\n"
         "|OriginalAirDate={{Start date|2024|1|15}}\n}}\n")
    notes = []
    eq([e.title for e in wiki.episodes(t, notes=notes)], ["Pilot", "Third"],
       "every row but the damaged one survives, on both sides of it")
    eq(len(notes), 1, "and the skip is reported, not silent")
    ok("unclosed" in notes[0] and "Episode list" in notes[0],
       "naming what was skipped: %r" % (notes[0:1],))

    eq(wiki.templates("{{Episode list\n|Title=x\n"), [],
       "a page that is nothing but an unclosed block yields no rows")
    eq(raises(lambda: wiki.episodes("{{Episode list\n|Title=x\n")), None,
       "and raises nothing doing it")


# --------------------------------------------------------------------------
# B6. a sublist POINTER is not a row, and two of the three shapes invented one
# --------------------------------------------------------------------------
def test_a_sublist_pointer_is_not_an_episode():
    """`{{Episode list/sublist|List of Foo episodes}}` names the page the real
    rows live on. It carries no named argument, so it is plumbing — and a
    nameless, unnumbered, undated row emitted from it is an invented episode,
    two lines under a comment promising not to invent one."""
    for t in ("{{#invoke:Episode list|sublist|List of Foo episodes}}",
              "{{Episode list/sublist|List of Foo episodes}}",
              "{{Episode list/sublist|List of Foo episodes\n}}",
              "{{Episode list}}",
              "{{Episode list\n|List of Foo episodes\n}}"):
        eq(wiki.episodes(t), [], "not a row: %r" % t)
        eq(len(wiki.templates(t, "Episode list")), 1,
           "though it IS a template, and templates() still returns it")

    # the third shape is the one the PRE-CLU-167 reader also got wrong, and its
    # `\n\s*}}` terminator is why only that one of the three reached it
    eq(len(_old_blocks("{{Episode list/sublist|List of Foo episodes\n}}")), 1,
       "old: an invented row of its own, since before CLU-167")

    # and a sublist pointer that DOES carry rows' worth of fields is still a row
    f = fixture("enterprise-s1-broken-bow")
    e, = wiki.episodes(f)
    eq(e.title, "Broken Bow", "a real sublist row is untouched")
    eq(e.fields[1], "Star Trek: Enterprise season 1", "positional page name kept")


# --------------------------------------------------------------------------
# C1. a marker template's NAME shipped welded onto a title
# --------------------------------------------------------------------------
def test_a_marker_templates_name_does_not_become_part_of_a_title():
    """The 1998 film's row in "List of The X-Files episodes" files its name
    under RTitle and puts the mythology-arc marker after it:

        |RTitle=''[[The X-Files (film)|The X-Files]]''{{double dagger}}

    {{double dagger}} carries no argument, so it missed _BARE_RENDERS and took
    rule 7's keep-the-name default — and unlike {{yes}} or {{TBA}}, a marker's
    name DESCRIBES its glyph instead of being it. The row came back titled
    "The X-Filesdouble dagger", a string that is nowhere in the article, in a
    list of every X-Files episode."""
    t = fixture("xfiles-film-row-double-dagger")
    e, = wiki.episodes(t)

    eq(e.fields["RTitle"],
       "''[[The X-Files (film)|The X-Files]]''{{double dagger}}",
       "the source's own value, read whole")
    ok("Title" not in e.fields, "and there is no |Title to prefer")

    eq(_005_clean(e.fields["RTitle"]), "The X-Filesdouble dagger",
       "005d1ee: the template's NAME, welded to the end of the name")
    eq(_005_display_title(e.fields["RTitle"]), "The X-Filesdouble dagger",
       "and display_title() saw no quote and no tag, so it shipped it")

    eq(wiki.clean("{{double dagger}}"), "‡",
       "the marker now renders the glyph it renders")
    eq(e.title, "The X-Files", "and the row is titled what the source calls it")
    eq(e.rtitle, "The X-Files‡",
       "with the raw value still on the row, marker and all")
    eq(e.year, 1998, "still dated")
    eq(e.num_overall, None, "and still unnumbered, as a film row is")


def test_a_legend_marker_is_not_part_of_the_name():
    """Rendering the glyph alone would have shipped "The X-Files‡". The article
    says above the table that a double dagger marks a mythology episode, so it
    is apparatus ABOUT the row in exactly the sense a <ref> is — and clean()
    has always removed those. Stripping it loses nothing: what is left is the
    link label the source wrote."""
    t = fixture("xfiles-film-row-double-dagger")
    ok("are episodes in the series' alien" in t,
       "the fixture carries the article's own legend for the marker")

    for raw, want in (("''[[The X-Files (film)|The X-Files]]''{{double dagger}}",
                       "The X-Files"),
                      ("''[[Foo]]''{{double-dagger}}", "Foo"),
                      ("[[Bar]] {{dagger}}", "Bar"),
                      ('"[[Baz]]"{{dagger}}', "Baz")):
        eq(wiki.display_title(raw), want, "display_title(%r)" % raw)

    eq(wiki.display_title("M*A*S*H"), "M*A*S*H",
       "`*` is a character titles use, so it is not in the strip set")
    eq(wiki.display_title("''Nerve''{{dagger}} (Part 1)"), "",
       "and stripping a marker does not smuggle a part marker past the rest")


def test_a_marker_template_alone_in_a_cell_still_says_something():
    """The guard on the fix. Round one of CLU-167 dropped every argument-less
    template it did not recognise and deleted 498 fields from Jackie Chan's
    filmography; a marker is exactly the shape that would reopen that, because
    in an awards or filmography crosstab {{dagger}} IS the whole cell and means
    "posthumous" by the article's own legend. Rendering the glyph keeps the
    cell marked; dropping it would say the opposite of what the source says."""
    for raw, want in (("{{dagger}}", "†"), ("{{double dagger}}", "‡"),
                      ("{{double-dagger}}", "‡"), ("{{asterisk}}", "*"),
                      ("{{Dagger}}", "†"), ("{{Double Dagger}}", "‡")):
        eq(wiki.clean(raw), want, "clean(%r)" % raw)
        ok(wiki.clean(raw) != "", "and it is never empty: %r" % raw)

    eq(_005_clean("{{asterisk}}"), "asterisk",
       "005d1ee leaked this one too — the Criterion list marks its "
       "out-of-print films with it")
    eq(wiki.clean("[[King Kong (1933 film)|King Kong]]{{asterisk}}"),
       "King Kong*", "so a marked film is marked, not called 'King Kongasterisk'")


# --------------------------------------------------------------------------
# C2. an editor saying there is NO title shipped as the title
# --------------------------------------------------------------------------
def test_an_rtitle_that_is_a_whole_parenthetical_is_not_a_title():
    """Thirteen Frieren sponsored shorts write `| Title =` blank and
    `| RTitle = ''(Official English title not available)''`. display_title()
    only ever asked whether anything quote-shaped or tag-shaped was left after
    clean(), so all thirteen came back as episodes CALLED "(Official English
    title not available)" — an editor stating there is no English title,
    published as the English title.

    It is the invented-data failure in its best disguise: a sentence in a title
    column reads as an answer, and unlike a dropped row nothing about the list
    looks short."""
    t = fixture("frieren-short-with-no-english-title")
    real, short = wiki.episodes(t)

    eq(short.fields["Title"], "",
       "the source has the field and deliberately has nothing in it")
    eq(short.fields["RTitle"], "''(Official English title not available)''",
       "and says so under RTitle")

    eq(_005_display_title(short.fields["RTitle"]),
       "(Official English title not available)",
       "005d1ee: the note itself, shipped as the episode's name")
    eq(short.title, "", "an empty title is better than a wrong one")
    eq(short.rtitle, "(Official English title not available)",
       "and the note is still on the row for a caller that wants it")
    eq(short.year, 2023, "the row is otherwise read exactly as before")

    # the control: a real |Title on the same page, which must not move
    eq(real.title, "Spell to Make Clothes Clean and Spotless",
       "|Title still wins and is untouched")
    eq((real.num_overall, real.num_in_season), (11, 11), "still numbered")


def test_a_title_that_merely_contains_a_parenthesis_is_kept():
    """The guard on that fix, and the reason it is 'wholly' and not 'contains'.
    Refusing any title with a bracket in it would drop real names — a bracketed
    alias, a disambiguator, a year — and trade one fabrication for a silent
    row of blanks, which is the trade this module refuses in both directions."""
    for raw, want in (
            ("''[[Cowboy Bebop: The Movie]]'' (''Knockin' on Heaven's Door'')",
             "Cowboy Bebop: The Movie (Knockin' on Heaven's Door)"),
            ("Prologue (2015)", "Prologue (2015)"),
            ("[[The Gift (The X-Files)|The Gift]]", "The Gift"),
            ("(Official English title not available)", ""),
            ("''(TBA)''", ""),
            ("(no title)", "")):
        eq(wiki.display_title(raw), want, "display_title(%r)" % raw)

    eq(wiki.display_title("(A) and (B)"), "(A) and (B)",
       "two parentheticals are not ONE parenthetical, so the rule leaves them")


# --------------------------------------------------------------------------
# D1. a marker template's ARGUMENT shipped welded onto a name (CLU-531)
# --------------------------------------------------------------------------
def test_a_marker_templates_arguments_do_not_become_part_of_a_name():
    """Round three taught _BARE_RENDERS the marker glyphs and fixed
    `{{double dagger}}`. It did not touch `{{double dagger|alt=...}}`, which is
    the SAME template with a rendering hint on it, so that one still took the
    keep-the-last-argument rule and handed the hint back as display text.

    The Palme d'Or article's "Multiple winners" table marks the directors who
    won for consecutive films that way, and its own legend above the table
    explains the glyph. `[[Bille August]] {{double dagger|alt=Consecutive
    films}}` came back as "Bille August alt=Consecutive films", and
    display_title() accepted it because nothing quote-shaped, tag-shaped or
    bracket-shaped was left in it — the identical fabrication to
    "The X-Filesdouble dagger", one round on."""
    t = fixture("palme-dor-consecutive-winner-marker")
    ok("have won for consecutive films" in t,
       "the fixture carries the article's own legend for the marker")
    rows = [l for l in t.splitlines()
            if l.startswith("|") and "{{double dagger|" in l]
    eq(len(rows), 3, "three of the ten directors are marked")

    cell = rows[0][1:].strip()
    eq(cell, "[[Bille August]] {{double dagger|alt=Consecutive films}}",
       "the source's own cell, read whole")
    eq(_b51_clean(cell), "Bille August alt=Consecutive films",
       "b51e564: the template's ARGUMENT, welded to the end of the name")
    eq(_b51_display_title(cell), "Bille August alt=Consecutive films",
       "and display_title() saw no quote and no tag, so it shipped it")
    eq(wiki.clean(cell), "Bille August ‡",
       "the marker now renders the glyph it renders")
    eq(wiki.display_title(cell), "Bille August",
       "and the name is what the source calls him")

    # written without the space, which is how the card reproduced it and how
    # the four Korean awards articles write it
    tight = "[[Bille August]]{{double dagger|alt=Consecutive films}}"
    eq(_b51_clean(tight), "Bille Augustalt=Consecutive films",
       "b51e564: and with no space to make it look like two things")
    eq(wiki.display_title(tight), "Bille August", "it is still one name")


def test_an_argumented_marker_alone_in_a_cell_still_says_something():
    """The guard on that fix, and it is the same guard as the argument-less
    one: `{{dagger|sup=yes}}` is the whole content of a great many awards-table
    cells, where the article's legend says it means posthumous or deceased, and
    an emptied cell states the opposite of a marked one. So the ARGUMENT is
    dropped and the GLYPH is rendered — and it is a rule about four template
    names, not about arguments, because for almost every other template the
    last argument is the content."""
    for raw, want in (("{{dagger|sup=yes}}", "†"),
                      ("{{double dagger|alt=Award winner}}", "‡"),
                      ("{{double-dagger|alt=x}}", "‡"),
                      ("{{asterisk|sup=yes}}", "*"),
                      ("{{Dagger|SUP=yes}}", "†"),
                      ("{{Double Dagger|alt=Award winner}}", "‡")):
        eq(wiki.clean(raw), want, "clean(%r)" % raw)
        ok(wiki.clean(raw) != "", "and it is never empty: %r" % raw)
        eq(_b51_clean(raw), raw[raw.index("|") + 1:].rstrip("}"),
           "b51e564 kept the whole argument, `alt=` and all: %r" % raw)

    # every name the pattern recognises has a glyph to render, so the two
    # spellings of the rule cannot drift apart
    for name in wiki._MARKER_TEMPLATES:
        ok(name in wiki._BARE_RENDERS,
           "{{%s}} renders the same glyph with or without arguments" % name)

    # and the narrowness: an argumented template that is NOT a marker still
    # keeps its last argument, which is where its content is
    for raw, want in (("{{sort|Kong, King|King Kong}}", "King Kong"),
                      ("{{Start date|2024|1|1}}", "1"),
                      ("{{small|(''22'')}}", "(22)")):
        eq(wiki.clean(raw), want,
           "clean(%r) is untouched by the marker rule" % raw)


# --------------------------------------------------------------------------
# D2. a bare placeholder shipped as an episode title (CLU-531)
# --------------------------------------------------------------------------
def test_an_rtitle_that_is_only_a_placeholder_is_not_a_title():
    """Mystery Science Theater 3000's season 14 has a scheduled episode with no
    announced film: the row carries no |Title and `| RTitle = TBA`. It is the
    Frieren shape — an editor writing where the name will go, rather than a
    name — with nothing bracket-shaped or template-shaped to key off, so round
    three left it standing and the row came back as an episode called "TBA"."""
    t = fixture("mst3k-s14-tba-rtitle")
    before, tba, after = wiki.episodes(t)

    eq(tba.fields["RTitle"], "TBA", "the source's own value")
    ok("Title" not in tba.fields, "and there is no |Title to prefer")
    eq(_b51_display_title(tba.fields["RTitle"]), "TBA",
       "b51e564: the placeholder, shipped as the episode's name")
    eq(tba.title, "", "an empty title is better than a wrong one")
    eq(tba.rtitle, "TBA",
       "and the raw value is still on the row for a caller that wants it")
    eq((tba.num_overall, tba.num_in_season), (233, 3),
       "the row is otherwise read exactly as before")
    eq(tba.year, 2026, "still dated")

    # the controls: the rows either side of it must not move
    eq(before.title, "Deathsport", "a real RTitle on the same table is a title")
    eq(after.title, "Space Raiders", "likewise")


def test_a_title_that_merely_contains_a_placeholder_word_is_kept():
    """The guard, and it has two halves. clean() must not move at all: {{TBA}}
    is the entire content of an awards or release-date cell and keeping its name
    is what stopped 498 Jackie Chan fields being deleted, so the refusal lives
    in display_title() and nowhere else. And it is a WHOLE-value match, so a
    real title that carries the letters is untouched."""
    eq(wiki.clean("{{TBA}}"), "TBA",
       "clean() still says what the cell says — the B1 pin, restated here")
    eq(wiki.clean("TBA"), "TBA", "and a bare one is still text")

    for raw, want in (("TBA", ""), ("{{TBA}}", ""), ("tba", ""),
                      ("''TBA''", ""), ('"TBA"', ""), ("TBD", ""),
                      ("N/A", ""), ("?", ""),
                      ("Tbilisi", "Tbilisi"), ("TBA and TBD", "TBA and TBD"),
                      ("To Be Announced (Part 1)", "To Be Announced (Part 1)"),
                      ("The N/A Files", "The N/A Files")):
        eq(wiki.display_title(raw), want, "display_title(%r)" % raw)

    for raw in ("TBA", "n/a"):
        eq(_b51_display_title(raw), raw,
           "b51e564 accepted %r as a name" % raw)


# --------------------------------------------------------------------------
# The public surface the card exists to provide
# --------------------------------------------------------------------------
def test_the_promised_machinery_is_public():
    """The point of CLU-167 is that the next list does not write another private
    brace counter, so these four are part of the module's contract."""
    for name in ("templates", "template_fields", "field", "numbers"):
        ok(callable(getattr(wiki, name, None)), "wiki.%s() is public" % name)


def test_episodes_still_unpacks_as_the_five_tuple():
    """22 generators unpack this positionally. The shape does not move."""
    t = fixture("ds9-s5-assignment-tribbleations")
    for e in wiki.episodes(t):
        eq(len(e), 5, "five elements")
        n1, n2, title, year, block = e
        eq((n1, n2, title, year, block), tuple(e), "unpacks in order")
        ok(isinstance(n1, int) and isinstance(n2, int), "numbers are ints")
        ok(block.startswith("\n|"), "block keeps its leading pipe")
        ok(not block.rstrip().endswith("}}"),
           "and keeps its old shape: no trailing template close")
    # and equality against a plain tuple still holds, for callers that compare
    e = wiki.episodes(t)[1]
    eq(e == (104, 6, "Trials and Tribble-ations", 1996, e.block), True,
       "compares equal to the plain tuple")


def test_template_fields_keeps_positional_arguments():
    """`{{Episode list/sublist|Star Trek: Enterprise season 1}}` names a page.
    It lands under an integer key rather than being dropped, so nothing on the
    block is silently lost."""
    f = wiki.template_fields(
        wiki.templates(fixture("enterprise-s1-broken-bow"), "Episode list")[0])
    eq(f[1], "Star Trek: Enterprise season 1", "the sublist page name survives")
    eq(wiki.field(f, "Title"),
       "[[Broken Bow (Star Trek: Enterprise)|Broken Bow]]", "raw title")


def test_templates_reports_offsets_into_the_text_it_was_given():
    """Hunter x Hunter forked partly because gwlib returned no offsets: it
    slices the page at its `=== headings ===` to attribute each row to an arc."""
    t = "== Season 5 ==\n" + fixture("ds9-s5-assignment-tribbleations")
    pairs = wiki.templates(t, "Episode list", offsets=True)
    eq(len(pairs), 2, "two rows")
    for start, block in pairs:
        eq(t[start:start + 14], "{{Episode list", "offset lands on the block")
    ok(pairs[0][0] < pairs[1][0], "in page order")
    eq(t[:pairs[0][0]].count("=="), 2, "the heading above row 1 is findable")
    eq([e.start for e in wiki.episodes(t)], [p[0] for p in pairs],
       "rows carry the same offset")


def test_infobox_is_untouched():
    """infobox() never had defect 4 (it used `[ \\t]*`) or defect 5 (it strips
    comments), and it has ~100 callers. It is deliberately not changed here."""
    t = ("{{Infobox film\n| name = A Film\n| runtime = 90 minutes"
         "<!--per BBFC-->\n| director = [[X]]\n| gross =\n| budget = $1\n}}\n")
    ib = wiki.infobox(t)
    ok(ib is not None, "reads a film infobox")
    eq(ib("runtime"), "90 minutes", "comments still pre-stripped")
    eq(ib("gross"), "", "an empty field is still empty, not the line below")
    eq(ib("budget"), "$1", "and the line below is still itself")
    eq(wiki.infobox("{{Infobox album\n|x=1\n}}"), None, "still gated by kind")


# --------------------------------------------------------------------------
# runner
# --------------------------------------------------------------------------
FAILED = []
CHECKS = [0]


def eq(got, want, why):
    CHECKS[0] += 1
    if got != want:
        FAILED.append("%s\n      got  %r\n      want %r" % (why, got, want))


def ok(cond, why):
    CHECKS[0] += 1
    if not cond:
        FAILED.append("%s\n      expected a true value" % why)


def raises(fn):
    try:
        fn()
    except Exception as e:  # noqa: BLE001 - the exception IS the return value
        return e
    return None


def main():
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    bad = 0
    for name, fn in tests:
        before = len(FAILED)
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            FAILED.append("%s raised %s: %s" % (name, type(e).__name__, e))
        if len(FAILED) > before:
            bad += 1
            print("FAIL %s" % name)
            for f in FAILED[before:]:
                print("   - %s" % f)
    print("\n%d tests, %d checks, %d failed" % (len(tests), CHECKS[0], bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
