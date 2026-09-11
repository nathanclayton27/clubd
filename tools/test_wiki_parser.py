"""Pins for the seven CLU-167 parser defects, plus the two found fixing them.

    python tools/test_wiki_parser.py

Exit 0 and a green count means clean. No test framework — nothing in this repo
uses one, and this file should run from a bare clone.

EVERY CHECK IS A PIN, NOT A SPOT TEST. A test that only asserts today's right
answer cannot tell a fixed parser from a fixture that never exercised the bug,
so each case asserts twice:

  1. gwlib.wiki, as it stands, gets the right answer; and
  2. the PRE-CLU-167 rule, re-implemented below in `_old_*`, gets the exact
     wrong answer that shipped in the card — proving this fixture really does
     land on the defect.

So reverting a fix fails (1), and swapping a fixture for a tamer excerpt fails
(2). The `_old_*` functions are copied verbatim from the parser as it was at
commit 5ad60de and must never be "fixed"; they are the before-photograph.

The fixtures in tools/data/wiki_fixtures/ are verbatim excerpts of the real
articles, one per case. They are tracked deliberately: the test is worthless
without them, and a test that passes only on the machine that wrote it is the
"someone else pulls the repo and runs it" failure this project has paid for.
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

    ok(isinstance(raises(lambda: wiki.templates("{{Episode list\n|Title=x\n")),
                  ValueError), "genuinely unclosed braces still raise")


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
