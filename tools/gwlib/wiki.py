"""Wikipedia fetching and wikitext parsing, the shipped-and-burned edition.

Every regex here earned its shape from a real incident:
- rowspan carry: Robin Williams' year column silently went stale (two bugs)
- leading pipe: episode blocks' first field (usually Title) was invisible
- {{#invoke:Episode list|sublist}}: American Dad's season pages use it
- footnote templates removed whole: Troll 2 shipped "Fragassoefn|name=…"
- multi-line infobox fields: Toxic Avenger's {{Plainlist}} of directors
- comments stripped before field parsing: Free Fire's runtime line

CLU-167 collected seven more. Each was found by a list build that then wrote its
own parser to get around it, so none of the seven ever reached a shipped list —
they are near misses, caught at a generator's own asserts, and the price was a
dozen private copies of this file's job rather than a wrong catalogue. Every one
is fixed here and pinned by tools/test_wiki_parser.py, which asserts against the
verbatim article excerpts in tools/data/wiki_fixtures/, one per case:

1. episodes() closed a block at the first line-initial `}}`, so a row ending
   `|LineColor=1C39BB}}` ran on and swallowed the NEXT row — Deep Space Nine
   season 5 would have shipped without "Trials and Tribble-ations". A row that
   closes inline with nothing after it was worse: with no later `\\n}}` to stop
   at, the row vanished entirely.
2. a multi-line nested template ended the block early, wiping every field below
   it — Enterprise's "Strange New World" lost its numbering under WrittenBy.
3. EpisodeNumber read as the first number only, so `53<hr>54` was one episode;
   and a row numbering its parts `EpisodeNumber_1`/`_2` was none, because `_1`
   sits between the name and the `=`. NumParts is NOT the trigger for that
   second shape — Doctor Who's serials carry NumParts with one EpisodeNumber and
   no `EpisodeNumber_` at all, so numbers() branches on `_1` being present.
4. `\\s*` after a field's `=` let an EMPTY field eat its own newline and read
   back as the line below, so Bleach's unannounced `|Title =` came back as
   "RTitle =". template_fields() cannot do this: it splits on pipes at depth
   zero rather than searching for a value, so an empty field is "" by
   construction. The same defect on a bleach.fandom.com infobox read a blank
   `|chapters=` (meaning the episode adapts no manga) back as the arc name;
   that template was unreachable through this module at all, which is why
   templates()/template_fields() are public and not gated to Episode list.
   infobox() never had this defect — it already used `[ \\t]*` — and is left
   alone here.
5. clean() left HTML comments in, so two Invincible titles would have shipped
   with a 200-character editor's note glued on.
6. only |Title was read, never |RTitle, so Bandersnatch came back nameless.
   RTitle is free-form DISPLAY markup, though, so reading it as a title is a
   fabrication of its own — `"Nerve" (Part 1)` mangled eleven Farscape rows the
   first time this was fixed. display_title() takes an RTitle only where it is
   plainly a name and nothing else, the raw value is on the row as `.rtitle`
   either way, and an empty title is better than a wrong one.
7. clean()'s inline-template rule needs a pipe, so EVERY argument-less template
   fell through to stripping the braces and survived as its own name: {{hsp}}
   became "hsp" ("USS Callisterhsp: Into Infinity"), and so did {{nbsp}} and
   {{snd}}. clean() now renders the ones that render nothing — _BARE_RENDERS,
   an allowlist — and leaves every other one as its own name, because for
   {{yes}}, {{no}}, {{TBA}}, {{n/a}}, {{won}} and {{nom}} the name IS the text
   and it is the whole content of the cell. Dropping the unknown ones instead,
   which this file did for one round, deleted 498 fields from Jackie Chan's
   filmography alone; see _BARE_RENDERS for why the default has to be the
   leaky one.

Two more the seven did not name, both found while fixing them:

8. real wikitext is not brace-balanced. `<noinclude>{{refn|group=N|</noinclude>`
   `<includeonly>{{efn|</includeonly>` gives Doctor Who season 6 106 `{{` to 105
   `}}`, because MediaWiki renders only one of those two opens, and a brace
   counter that asserts balance refuses the page. templates() resolves the
   conditional transclusion first — direct_view(), the page's own view, which
   balances AND keeps the `<noinclude>|Aux4 = 77</noinclude>` rating columns the
   old regex read. transcluded_view() is the other half, for a caller that wants
   what the parent list page renders.
9. the opening pattern tolerated no whitespace after `{{`. The Office's episode
   list writes `{{\\nEpisode list`, which the old regex could not match at all —
   a latent row-dropper of exactly this kind.

AND SIX MORE IN THE FIX ITSELF, found by review before it shipped. The first
round of CLU-167 fixed all nine above and, being a rewrite, brought its own: it
deleted every argument-less template it did not recognise (7 above), read |RTitle
as a plain title (6 above), read episode numbers out of a template's arguments
and out of both halves of a decimal (see numbers()), refused a whole page over
one unbalanced block instead of skipping it (see templates()), turned a sublist
POINTER into a nameless row (see episodes()), and stated a paragraph of measured
counts of which four were wrong (see below). Three of the six invented catalogue
data, which is the thing this module exists not to do, so each of the six has its
own pin in tools/test_wiki_parser.py alongside the nine.

AND TWO MORE AFTER THAT, which the review of the six caught still standing. Both
were episode TITLES, and a wrong title is the expensive kind of wrong: a dropped
row shows up as a short list, and an invented one looks like an answer. Between
them they are the whole of what this round changed — run
tools/measure_wiki_parser.py against the round-2 parser and the only rows that
differ are these two articles' — and the count as of the commit that made the
change is in that commit's message rather than here, for the reason the last
paragraph of this docstring gives:

10. an argument-less template whose NAME describes a glyph rather than being the
    text. Rule 7 above says the name is usually the text, and for {{yes}} and
    {{nom}} it is — but `''[[The X-Files (film)|The X-Files]]''{{double dagger}}`
    came back as the title "The X-Filesdouble dagger", three words that are
    nowhere in the article. The markers now render their glyph in _BARE_RENDERS
    (‡, †, *) rather than their name, which keeps a cell that is nothing BUT a
    dagger saying something, and display_title() strips a marker glyph off a
    title, because a legend key is apparatus about the row in the same sense a
    <ref> is. Over the corpus {{double dagger}} was the only argument-less
    template that reached a title at all.
11. an RTitle that is one whole parenthetical is a note, not a name. Thirteen
    Frieren sponsored shorts write `| Title =` blank and `| RTitle =
    ''(Official English title not available)''`, and all thirteen shipped that
    sentence as the episode's title — an editor saying there is no title,
    published as one. display_title() refuses a value that is parenthesised end
    to end, the mirror of the quoted-end-to-end rule that ACCEPTS one.

Comments are REMOVED, and removed BEFORE blocks are found rather than after.
Both halves of that are load-bearing and each cost a bug:

- before, because Bleach's Thousand-Year Blood War table parks unaired episodes
  inside `<!--…-->`, and a brace counter over raw text finds those rows and
  invents four episodes that do not exist. Dropping a row is bad; conjuring one
  is worse, and it is the failure the no-invented-data rule speaks to directly.
- removed and not padded out with spaces, even though padding is the tempting
  way to keep byte offsets stable, because a comment can sit inside a WORD:
  Doctor Who series 9 writes `[[Jamie Mathieson]] a<!--Do not change to &-->nd`
  `Steven Moffat`, and padding turns "and" into "a nd". So templates() maps its
  offsets back to the text it was handed instead.

numbers() removes templates from a value and then cleans it before looking for
digits, for the same family of reason, and the corpus pays for each step:
`19<ref name="finale2"/>` yields an episode 2 out of a ref name if it is not
cleaned first, and `192a{{anchor|ep192}}` yields episode 192 twice if the anchor
is resolved to its argument rather than removed. A number is also read with its
decimal part, because `3.75` is one Attack on Titan recap special and not
episodes 3 and 75.

Blocks are found by counting braces and split on pipes at depth zero, which is
what eight other files under tools/ each wrote for themselves — make_avatar,
make_black_mirror, make_flcl, make_hunter_x_hunter, make_invincible,
make_the-big-o, make_the_office and make_vampire-diaries all carry their own
`depth += 1`, and more do under the gitignored scratch/. That machinery is
public here now — templates(), template_fields(), field(), numbers() — so the
next list does not write another copy.

One of those four is not the function CLU-167 first sketched. `field()` was going
to be a third regex reader taking (text, name); it takes (fields, *names)
instead and reads the dict template_fields() already built. Re-searching a block
once per field name is precisely how defect 4 happened, so a signature that
invites it would have reproduced the bug it was added to fix — and this file
already had two different private closures called `field`, which is trap enough.
What it adds instead is the distinction none of the private copies could express:
a field that is present and blank is not a field that is absent.

episodes() is a thin composition of the four. It keeps its exact 5-tuple because
22 generators unpack it positionally, and `block` is rebuilt byte-for-byte as the
old regex produced it — trailing-space quirk, inconsistent sublist handling and
all — because some of those generators re-read it with regexes of their own. The
numbers a row could not previously express hang off the returned rows as
attributes; see Episode.

WHAT IS PROVEN HERE, AND WHAT IS ONLY MEASURED. An earlier version of this
docstring carried a paragraph of counts — pages changed, rows changed, titles
changed. Every one of them was re-derived by a reviewer over the same articles
and four came back different, and nobody who clones this repo could have caught
that, because every input to the sweep lives under the gitignored scratch/. A
precise number that is both wrong and unverifiable is worse than no number: it
is the one part of a file like this that a later reader trusts instead of
re-deriving. So the counts are gone from here.

What stands in their place: tools/test_wiki_parser.py, which asserts against
tracked fixtures and runs from a bare clone, and tools/measure_wiki_parser.py,
which is the sweep itself — a named, runnable script rather than a remembered
result. Run it against a corpus of cached wikitext and it prints today's numbers
for today's parser; the numbers as of the commit that added it are in that
commit's message, where a figure is a dated record instead of a standing claim.
Counts quoted anywhere in this file are the ones that script prints, and they
are quoted only where the count is the point.

The fixture set pins episodes(), clean(), templates(), template_fields(),
field(), numbers() and display_title(). It does NOT exercise table_rows() or
infobox(), which are the module's two other public readers and are deliberately
unchanged here — so this file is pinned in the places CLU-167 touched, not
everywhere.

NOTHING IN THIS MODULE RAISES ON BAD INPUT. templates() skips a block whose
braces never close, numbers() reports a NumParts disagreement instead of
refusing the row, and episodes() therefore has no failure that can take a whole
page down and empty a catalogue list. Every such skip goes through note(): to
stderr always, and into a list the caller may pass as `notes=`. A parser that
silently skips what it cannot read is the bug this file was rewritten to fix,
so the skips are loud.
"""
import collections
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "GroupWatch/1.0 (reading-list builder)"
API = "https://en.wikipedia.org/w/api.php"


def get_json(url, tries=6):
    """GET a JSON API url with 429 backoff and network retries."""
    for n in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code != 429 or n == tries - 1:
                raise
            time.sleep(12 * (n + 1))
        except (urllib.error.URLError, TimeoutError):
            if n == tries - 1:
                raise
            time.sleep(5)


def wikitext(page, cache_dir=None, sleep=2.5):
    """Fetch a page's wikitext (redirects followed), optionally disk-cached."""
    if cache_dir:
        f = pathlib.Path(cache_dir) / (re.sub(r"[^A-Za-z0-9]+", "-", page) + ".wiki")
        if f.exists():
            return f.read_text(encoding="utf-8")
    q = urllib.parse.urlencode({"action": "parse", "page": page,
                                "prop": "wikitext", "format": "json",
                                "formatversion": "2", "redirects": "1"})
    d = get_json(API + "?" + q)
    time.sleep(sleep)
    if "error" in d:
        return None
    t = d["parse"]["wikitext"]
    if cache_dir:
        pathlib.Path(cache_dir).mkdir(parents=True, exist_ok=True)
        f.write_text(t, encoding="utf-8")
    return t


def search(query, limit=6):
    """Article titles matching a query — the way to find a page's real name."""
    q = urllib.parse.urlencode({"action": "query", "list": "search",
                                "srsearch": query, "srlimit": str(limit),
                                "format": "json", "formatversion": "2"})
    return [x["title"] for x in get_json(API + "?" + q)["query"]["search"]]


# Argument-less templates that render NOTHING, or nothing but a space or a
# dash. clean()'s keep-the-last-argument rule cannot see them because it
# requires a pipe, so without this table every one surfaced as its own NAME:
# {{hsp}} shipped "USS Callisterhsp: Into Infinity".
#
# This is an ALLOWLIST and the default is to keep the name, which is the
# opposite of what it looks like it should be. The reason is that for a large
# family of templates the name IS the rendered text, and it is the whole content
# of the cell: {{yes}}, {{no}}, {{TBA}}, {{n/a}}, {{won}}, {{nom}}, {{?}} and
# their kin are how every awards table and filmography crosstab on Wikipedia
# says what it says. Dropping an unknown argument-less template therefore
# deletes data rather than tidying it — measured over the cached corpus it takes
# 498 fields off Jackie Chan's filmography, empties Clint Eastwood's
# director/writer columns, and loses Donnie Yen's 14 "n/a"s.
#
# A blocklist cannot close that gap either: the corpus alone uses 5,907 distinct
# argument-less templates, led by {{nom}} (6,885 uses) and {{won}} (4,659). So
# the default is the one that cannot silently delete a column, and it is also
# exactly what the parser did before CLU-167 — which is why inverting the rule
# cannot regress any shipped list. The cost is the honest one: a decoration
# template nobody has seen yet leaks its name into display text, visibly, until
# somebody adds a line here.
_BARE_RENDERS = {
    "hsp": "", "nbsp": " ", "thinsp": " ", "shy": "", "wbr": "", "zwsp": "",
    "snd": " – ", "spnd": " – ", "sndash": " – ", "spndash": " – ",
    "spaced en dash": " – ", "ndash": "–", "en dash": "–", "mdash": "—",
    "em dash": "—", "spaces": " ", "'": "'", "'s": "'s",
    # A magic word, not a template: it renders the article's own title, which
    # this module has no way to know, so "" is the only honest answer.
    "pagename": "",
    # Renders the label that introduces a cast list inside a ShortSummary; the
    # cast names follow it in the wikitext and are kept.
    "episode cast": "",
    # Footnote MARKERS, and the one family where leaking the name does not
    # merely look untidy — it fabricates. The name is a DESCRIPTION of a glyph
    # rather than the glyph, so `''[[The X-Files (film)|The X-Files]]''`
    # `{{double dagger}}` came back as the title "The X-Filesdouble dagger",
    # three words that are nowhere in the article. Over the cached corpus this
    # is the ONLY argument-less template that reaches an episode title at all.
    #
    # They render their glyph here rather than dropping out, because the rest
    # of _BARE_RENDERS' argument is the same for them: {{dagger}} is the whole
    # content of a great many awards-table cells, where it means "posthumous"
    # or "deceased" by the article's own legend, and an emptied cell states
    # the opposite of a marked one. What a marker MEANS is never part of a
    # NAME, which is display_title()'s problem and is solved there.
    "dagger": "†", "double dagger": "‡", "double-dagger": "‡",
    "asterisk": "*",
}


def _bare(m):
    """One argument-less `{{name}}` as display text. See _BARE_RENDERS."""
    name = m.group(1).strip()
    if name.lower() in _BARE_RENDERS:
        return _BARE_RENDERS[name.lower()]
    if name.startswith("#"):
        # A parser function, not a template — {{#expr:5861430+14688240}} is
        # arithmetic MediaWiki performs and this module does not. Leaking the
        # source text ("#expr:5861430+14688240") states a number that is not
        # the answer, so it renders as nothing and a caller that needs the
        # figure gets [] from numbers() and fails its own coverage assert
        # instead of publishing a wrong one. Parser functions that DO carry
        # pipes still fall through to the keep-the-last-argument rule below;
        # that is a known limit, not a claim.
        return ""
    # The name is the text. Returned verbatim, uppercase and all — the source
    # writes {{Yes}} in Eastwood's crosstab and "Yes" is what the column says.
    return m.group(1)


def clean(t):
    """Wikitext -> display text. Comments go first, then footnotes vanish whole;
    wikilinks keep their label; inline templates keep their last argument;
    an argument-less template renders as its own name unless _BARE_RENDERS
    says it renders nothing; italics drop."""
    # First, and before the template passes: a comment can contain braces and
    # pipes of its own, and two Invincible titles carry a whole paragraph of
    # editor's note inline.
    t = re.sub(r"<!--.*?-->", "", t or "", flags=re.S)
    t = re.sub(r"<ref[^>]*/>", "", t)
    t = re.sub(r"<ref.*?</ref>", "", t, flags=re.S)
    for _ in range(3):
        t = re.sub(r"\{\{\s*(?:efn|refn|sfn|notetag)[^{}]*\}\}", "", t, flags=re.I)
    t = re.sub(r"<br\s*/?>", ", ", t)
    t = re.sub(r"\{\{(?:ubl|unbulleted list|plainlist)\s*\|", "", t, flags=re.I)
    t = re.sub(r"\s*\n\s*\*\s*", ", ", t)
    t = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", t)
    t = re.sub(r"\[\[([^\]]+)\]\]", r"\1", t)
    t = re.sub(r"\{\{([^{}|]*)\}\}", _bare, t)
    t = re.sub(r"\{\{[^{}|]*\|(?:[^{}|]*\|)*([^{}|]*)\}\}", r"\1", t)
    t = t.replace("{{", "").replace("}}", "").replace("''", "")
    return re.sub(r"\s+", " ", t).strip(" ,|")


# a table cell is `| content` or `| attrs | content`; the attrs test excludes
# link/template pipes so `[[A|B]]` and `{{sort|x|y}}` survive
_CELL = re.compile(r"^\|\s*(?:([^|\[{]*=[^|\[{]*)\|)?\s*(.*)$", re.S)


def table_rows(seg, ncols, header_probe="!scope=\"row\""):
    """Rows of a wikitable whose title cell is a `!scope="row"` header.

    Returns (title_line, cols) per row, with rowspan cells carried down to
    the rows they cover — the parsing that positional cell-picking got wrong
    three separate times. `ncols` counts the data columns to read, in table
    order, excluding the title header cell.
    """
    out, pending = [], {}
    for row in seg.split("\n|-"):
        lines = [l.strip() for l in row.strip().split("\n") if l.strip()]
        title_line = next((l for l in lines if l.startswith(header_probe)), None)
        if not title_line:
            continue
        raw = iter(l for l in lines
                   if l.startswith("|") and "text-align" not in l)
        cols = []
        for c in range(ncols):
            if c in pending:
                cols.append(pending[c][1])
                pending[c][0] -= 1
                if pending[c][0] == 0:
                    del pending[c]
                continue
            m = _CELL.match(next(raw, "|"))
            attrs, content = m.group(1) or "", m.group(2)
            cols.append(content)
            span = re.search(r"rowspan=\"?(\d+)", attrs)
            if span and int(span.group(1)) > 1:
                pending[c] = [int(span.group(1)) - 1, content]
        out.append((title_line, cols))
    return out


def _cut(text, patterns):
    """Delete every match of every pattern; return (view, map to `text` index).

    Deleting and not blanking, because a comment can sit inside a WORD:
    Doctor Who series 9 writes `[[Jamie Mathieson]] a<!--Do not change to &…-->`
    `nd Steven Moffat`, and padding that comment with spaces turns "and" into
    "a nd". MediaWiki removes comments outright, so this must too — which costs
    an index map, since templates() promises offsets into the text it was given.
    """
    spans = []
    for p in patterns:
        spans += [m.span() for m in re.finditer(p, text, re.S | re.I)]
    merged = []
    for s, e in sorted(spans):
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    out, index, i = [], [], 0
    for s, e in merged:
        out.append(text[i:s])
        index.extend(range(i, s))
        i = e
    out.append(text[i:])
    index.extend(range(i, len(text) + 1))
    return "".join(out), index


_CONDITIONAL_DIRECT = (r"<includeonly>.*?</includeonly>",
                       r"</?(?:noinclude|onlyinclude)>")
_CONDITIONAL_TRANSCLUDED = (r"<noinclude>.*?</noinclude>",
                            r"</?(?:includeonly|onlyinclude)>")


def direct_view(text):
    """The page as it reads on its own: <includeonly> removed, <noinclude>
    unwrapped. This is the view templates() parses, and why it has to.

    Season pages write `<noinclude>{{refn|group=N|</noinclude>`
    `<includeonly>{{efn|</includeonly>` — two opening braces for one closing
    `}}`, because MediaWiki renders only one of them. Counted raw, Doctor Who
    season 6 has 106 `{{` against 105 `}}` and a brace counter that asserts
    balance refuses the page. Either view balances. This is the one that keeps
    the FIELDS: a page's own view is where `<noinclude>|Aux4 = 77</noinclude>`
    rating columns live, and the old regex read them.
    """
    return _cut(text, _CONDITIONAL_DIRECT)[0]


def transcluded_view(text):
    """The page as it looks transcluded into a list-of-episodes article:
    <noinclude> removed, <includeonly> unwrapped. The counterpart to
    direct_view() for a caller that wants what the parent page renders."""
    return _cut(text, _CONDITIONAL_TRANSCLUDED)[0]


def _depth0_pipes(body):
    """Indices of the pipes in a template body that separate its arguments.

    Template depth and link depth are counted separately, so `{{t|[[A|B]]}}`
    nests correctly rather than either counter being fooled by the other.
    """
    out, depth, link, i, n = [], 0, 0, 0, len(body)
    while i < n:
        two = body[i:i + 2]
        if two == "{{":
            depth += 1
            i += 2
        elif two == "}}":
            depth -= 1
            i += 2
        elif two == "[[":
            link += 1
            i += 2
        elif two == "]]":
            link -= 1
            i += 2
        else:
            if body[i] == "|" and depth == 0 and link == 0:
                out.append(i)
            i += 1
    return out


def note(notes, message):
    """Record one irregularity: to `notes` if a caller gave a list, and always
    to stderr.

    Both halves are the point. A parser that skips what it cannot read and says
    nothing is the bug CLU-167 is about, wearing a different hat: the old regex
    also "skipped" the rows it could not parse. So every skip is visible on
    stderr where a generator's own output will carry it, and collectable by a
    caller that wants to assert on it.
    """
    if notes is not None:
        notes.append(message)
    sys.stderr.write("gwlib.wiki: %s\n" % message)
    return message


def templates(text, name="Episode list", offsets=False, keep_comments=False,
              notes=None):
    """Every `{{name…}}` on the page, whole, `{{` and `}}` included.

    Found by counting braces, so a block that closes inline on a field line
    (`|LineColor=1C39BB}}`) ends there instead of running on into the next one,
    and a multi-line nested template does not end it early. Matches
    `{{name}}`, `{{name/sublist|Page}}` and `{{#invoke:name|sublist|Page}}`,
    case-insensitively, tolerating a newline after the `{{` (The Office writes
    `{{\\nEpisode list`).

    `offsets=True` yields (start, block) pairs — the offset is into `text` as
    given, so a caller can attribute a row to the `== heading ==` above it
    without parsing the page twice.

    HTML comments are REMOVED before the scan, which is deliberate and is the
    difference between dropping rows and inventing them: Bleach's Thousand-Year
    Blood War table parks unaired episodes inside `<!--…-->`, and a raw scan
    returns them as five episodes that do not exist. Pass `keep_comments=True`
    only if you want those.

    A block whose braces never close is SKIPPED, and the skip is reported
    through note() — appended to `notes` if a caller passes a list, and written
    to stderr either way. It does not raise, and that is deliberate: this
    function has 69 callers reached through episodes(), and one vandalised or
    mid-edit article emptying a whole catalogue list is a worse failure than the
    row-dropping this file was rewritten to stop. The old regex skipped one
    malformed row and returned every other row on the page; so does this, and
    unlike the old regex it says which one.

    Raises nothing.
    """
    cuts = _CONDITIONAL_DIRECT if keep_comments else \
        (r"<!--.*?-->",) + _CONDITIONAL_DIRECT
    view, index = _cut(text, cuts)
    pat = (r"\{\{\s*(?:#invoke:\s*)?" + re.escape(name).replace(r"\ ", r"[ _]")
           + r"(?:\s*/\s*sublist)?\s*(?=[|}])")
    out = []
    for m in re.finditer(pat, view, flags=re.I):
        depth, i, n = 0, m.start(), len(view)
        while i < n:
            two = view[i:i + 2]
            if two == "{{":
                depth += 1
                i += 2
            elif two == "}}":
                depth -= 1
                i += 2
                if depth == 0:
                    break
            else:
                i += 1
        if depth != 0:
            note(notes, "skipped unclosed {{%s}} at offset %d: %r"
                 % (name, index[m.start()], view[m.start():m.start() + 90]))
            continue
        out.append((index[m.start()], view[m.start():i]) if offsets
                   else view[m.start():i])
    return out


_FIELD_NAME = re.compile(r"\A[A-Za-z][A-Za-z0-9_ .:/'-]*\Z")


def template_fields(block):
    """One whole template in, its arguments out as {name: raw value}.

    Splits on pipes at depth zero rather than searching the block for each name
    it wants, which is why an empty field cannot read back as the line below it:
    `| Title =` with nothing after the `=` is the empty string by construction,
    not a regex that swallowed its own newline. The distinction the callers need
    is therefore real — a field that is PRESENT and blank is a key mapped to
    "", a field that is ABSENT is a key that is not there.

    Keys are verbatim and CASE-SENSITIVE, because MediaWiki parameters are:
    Wikipedia's Episode list writes `Title`, bleach.fandom.com's episode
    template writes `title`, and folding them together would merge two
    namespaces. `EpisodeNumber_1` survives as its own key, which is the half of
    defect 3 the old reader could not see at all.

    Positional arguments — the `|Star Trek: Enterprise season 1` of a sublist —
    land under integer keys 1, 2, … rather than being dropped, so nothing in
    the block is silently lost.

    Raises ValueError when handed something that is not one whole template,
    which is a caller error rather than bad input: everything templates()
    returns is whole by construction, so episodes() cannot reach it.
    """
    if not (block.startswith("{{") and block.endswith("}}")):
        raise ValueError("not a whole template: %r" % (block[:60],))
    body = block[2:-2]
    cuts = _depth0_pipes(body)
    fields, pos = {}, 0
    for a, b in zip(cuts, cuts[1:] + [len(body)]):
        part = body[a + 1:b]
        eq = part.find("=")
        name = part[:eq].strip() if eq >= 0 else ""
        if eq >= 0 and _FIELD_NAME.match(name):
            fields[name] = part[eq + 1:].strip()
        else:
            pos += 1
            fields[pos] = part.strip()
    return fields


def field(fields, *names, default=None):
    """The first of `names` that carries a value, distinguishing three cases.

    Returns the raw value of the first name that is present AND non-blank; `""`
    if some name was present but every present one was blank — the source has
    the field and deliberately has nothing to put in it, which is Bleach episode
    412's unannounced title and a Bleach filler episode's empty `|chapters=`;
    and `default` (None) if none of the names is on the block at all.

    `field(f, "Title", "RTitle")` is defect 6 in one call: Bandersnatch files
    its name under RTitle because it has no episode number, and reading only
    Title returned a nameless row. The three-way answer is what generators
    currently fake with an `or` chain and an assert, or get wrong quietly.
    """
    for n in names:
        v = fields.get(n)
        if v is not None and v.strip():
            return v
    return "" if any(n in fields for n in names) else default


def numbers(fields, base="EpisodeNumber", notes=None):
    """Every episode number a row claims under `base`, in order, as written.

    Two notations say the same thing and the old reader lost both. `53<hr>54`
    is one Mad Men row covering episodes 53 and 54; `EpisodeNumber_1` /
    `EpisodeNumber_2` is Broken Bow, the two-hour Enterprise pilot, covering 1
    and 2. Returns [53, 54] and [1, 2].

    The branch is on `base_1` being present, NOT on NumParts. NumParts means
    "this was N broadcasts", which is not the same claim: Doctor Who's season 6
    serials carry NumParts of 4 to 10 with a single EpisodeNumber and no
    `EpisodeNumber_` anywhere, so a NumParts-triggered reader returns nothing
    for every one of them.

    NumParts is REPORTED where it disagrees with the suffixed numbers and never
    enforced, which is the correction of a round of this file getting it wrong
    in both directions at once. It used to raise, comparing NumParts against the
    COUNT OF NUMBERS — the very conflation the paragraph above says is not the
    same claim, since one part is free to carry two numbers over an `<hr>`. And
    the walk itself was indexed by how many numbers had been collected rather
    than by part, so `EpisodeNumber_1 = 53<hr>54` made it look for `_3` and skip
    `_2` entirely, while a `_1` carrying no digit at all looked for `_1` forever
    and hung. It now walks parts, 1, 2, 3, and stops at the first one missing.

    Templates are removed before digits are looked for, and the ordering is not
    cosmetic — every one of these is a real value in the cached corpus, and
    every wrong answer is an episode that does not exist:

        19<ref name="finale2"/>      [19]      not [19, 2] out of a ref name
        192a{{anchor|ep192}}         [192]     not [192, 192], twice over
        5 {{small|(''22'')}}         [5]       not [5, 22]; 22 is a production no.
        3.75                         [3.75]    not [3, 75]

    A number is a run of digits with an optional decimal part, so a decimal
    comes back as a float and as itself. `int()` folding 3.5 into 3 is how a
    recap special collides with the real episode 3, and two generators here
    already carry their own raw readers with a docstring explaining exactly
    that — make_gurren-lagann.py for episode 5.5 and make_vinland-saga.py for
    30.5 and 42.5. Callers that want whole episodes only can test the type;
    callers that want the row's own claim now have it.

    Returns [] when the field is missing or carries no number — reporting what
    the source says, including that it says nothing. The generators assert
    their own coverage.
    """
    if ("%s_1" % base) in fields:
        out, part = [], 1
        while ("%s_%d" % (base, part)) in fields:
            out += _digits(fields["%s_%d" % (base, part)])
            part += 1
        claimed = _digits(fields.get("NumParts", ""))
        if claimed and claimed[0] != part - 1:
            note(notes, "%s_1..%d against NumParts=%r: the row numbers %d "
                        "part(s) and claims %s" % (base, part - 1,
                                                   fields.get("NumParts"),
                                                   part - 1, claimed[0]))
        return out
    return _digits(fields.get(base, ""))


_NUMBER = re.compile(r"\d+(?:\.\d+)?")


def _digits(value):
    """Numbers in a field value: templates removed, then cleaned, then read.

    Templates go FIRST and whole, innermost out, because a template inside a
    number field is always decoration and its arguments carry digits of their
    own — `{{anchor|ep192}}`, `{{small|(''22'')}}`, `{{ref label|a|1}}`. Letting
    clean() resolve them to their last argument hands those digits back as
    episode numbers. Removing them can only lose a number the source stated
    inside a template, which no value in the cached corpus does, and losing one
    yields [] and a generator's own coverage assert rather than a wrong row.
    """
    t = value or ""
    for _ in range(6):
        stripped = re.sub(r"\{\{[^{}]*\}\}", "", t)
        if stripped == t:
            break
        t = stripped
    return [float(d) if "." in d else int(d)
            for d in _NUMBER.findall(clean(t))]


_WHOLLY_QUOTED = re.compile(r'"([^"]*)"\Z')

# The mirror of _WHOLLY_QUOTED, and it means the opposite. Quotes end to end
# say "the name is inside here"; PARENTHESES end to end say "this is a note
# about the name" — a gloss, a translation, a part marker, or an editor saying
# there is no name to give. Written with `[^()]*` for the same reason
# _WHOLLY_QUOTED is: it must match a value that is ONE parenthetical and
# nothing else, and leave `Cowboy Bebop: The Movie (Knockin' on Heaven's Door)`
# alone, which is a real title that happens to end in a bracketed alias.
_WHOLLY_PARENTHESISED = re.compile(r"\(([^()]*)\)\Z")

# Footnote-marker glyphs: what {{dagger}}, {{double dagger}} and their kin
# render as, now that _BARE_RENDERS gives them their glyph instead of their
# name. They are the article's own legend key — "Episodes marked with a double
# dagger (‡) are episodes in the series' alien mythology arc" — so they are
# apparatus ABOUT a row in exactly the sense a <ref> is, and clean() already
# removes those without anyone calling it a loss. `*` is deliberately absent:
# it is a character titles do use.
_MARKER_GLYPHS = "†‡§¶"


def display_title(raw):
    """An |RTitle / |AltTitle value as a plain title, or "" if it is not one.

    RTitle is free-form DISPLAY markup. It is where a source puts quoting, part
    markers and HTML precisely because |Title cannot hold them, so a value found
    there is not a title by virtue of being found there — it CONTAINS one, next
    to whatever else the editor wanted rendered in the cell:

        ''[[Babylon 5: The Gathering]]''      is a title, and only a title
        "Nerve" (Part 1)                     is a title plus a part marker
        ''[[Gamera vs. Barugon]]''<br />
          <small>''(Daikaijū Kettō…)''</small>  is a title plus a second title
        ''[[The X-Files (film)|The X-Files]]''
          {{double dagger}}                  is a title plus a legend marker
        ''(Official English title not available)''   is not a title at all

    So this accepts the first shape and answers for the rest, and the test is
    what is LEFT after clean(): a value wrapped in quotes end to end yields what
    is inside them, a value with no quoting and no HTML tag left in it is itself,
    and anything else is markup this module cannot resolve into one name. An
    empty title is better than a wrong one — and the raw field is still on the
    row, so a caller that knows its own source can read the part number out of
    it, which is what scratch/agent-farscape/parse.py does.

    Refusing is not cosmetic. `.strip('"')` over `"Nerve" (Part 1)` removes the
    trailing quote and nothing else, and Farscape ships eleven episodes called
    `Nerve" (Part 1)`; clean() strips no HTML tags at all, so Mystery Science
    Theater 3000's rows would ship with a `<small>` in the middle of them.

    The last two shapes are the round-3 corrections and they go opposite ways,
    because they are not the same kind of extra:

    - A LEGEND MARKER is stripped and the name kept. The dagger is the
      article's own footnote apparatus — the X-Files list says in so many words
      that a double dagger means a mythology episode — so it is about the row,
      not about the name, and removing it is what this module already does to
      every <ref> and {{efn}}. "The X-Files" is then the link label the source
      actually wrote, so nothing is invented and nothing is lost. (Before
      _BARE_RENDERS learned the glyph there was nothing to strip: the marker
      arrived as the WORDS "double dagger" welded to the end of the name.)
    - A WHOLE PARENTHETICAL is refused outright. Thirteen Frieren sponsored
      shorts write `| Title =` blank and `| RTitle = ''(Official English title
      not available)''`, which is an editor stating that there IS no English
      title; publishing it as one puts a sentence in the title column of a
      shipped list and it looks exactly like a real answer. A parenthesis is
      never a name — it is a gloss, a translation, a part marker, or this. Only
      a value that is ONE parenthetical end to end is refused, so a title
      carrying a bracketed alias keeps its name.
    """
    t = clean(raw or "")
    t = t.strip(_MARKER_GLYPHS + " ")
    if _WHOLLY_PARENTHESISED.match(t):
        return ""
    m = _WHOLLY_QUOTED.match(t)
    if m:
        return m.group(1).strip()
    if '"' in t or "<" in t or ">" in t:
        return ""
    return t


class Episode(collections.namedtuple(
        "Episode", "num_overall num_in_season title year block")):
    """One {{Episode list}} row.

    Unpacks as the 5-tuple it always was, because 22 generators unpack it
    positionally and this file is not the place to move them. `num_overall` and
    `num_in_season` stay the FIRST number, so a caller that never knew a row
    could carry two sees exactly what it saw before. They are None where the row
    states no number, an int where it states a whole one, and a float where it
    states 5.5 — see numbers() for why a recap special keeps its half.
    What the tuple cannot express hangs off the row instead:

        .fields    every argument on the block, from template_fields()
        .nums      all overall numbers, e.g. [53, 54] or [1, 2]
        .nums2     all in-season numbers
        .numparts  NumParts as written, or ""
        .rtitle    |RTitle, cleaned — display markup and all
        .alttitle  |AltTitle, cleaned
        .start     offset of the block in the text handed to episodes()

    `.rtitle` is the other half of display_title(): where the source's RTitle
    carries more than a name, `title` is empty and this is where the name went.
    """


def episodes(text, notes=None):
    """Episode-list entries: (num_overall, num_in_season, title, year, block).

    A composition of templates(), template_fields(), field(), numbers() and
    display_title(); see Episode for what a row carries that the tuple cannot.
    Handles {{Episode list}}, {{Episode list/sublist|Page}}, and
    {{#invoke:Episode list|sublist|Page}}; keeps the leading pipe inside the
    block so the first field is findable, and `block` keeps the shape it always
    had, since some generators re-read it with regexes of their own.

    The title is |Title, falling back to |RTitle then |AltTitle through
    display_title(), which takes one of those only where it is plainly a name
    and not a name wrapped in display markup. Empty titles stay empty (an empty
    title once containment-matched everything), and an empty one means the
    source has no title here that this module can read — not that the field was
    read under the wrong name.

    Raises nothing. A block it cannot read is skipped and reported through
    note(), to stderr and to `notes` if a caller passes a list.
    """
    out = []
    for start, block in templates(text, "Episode list", offsets=True,
                                  notes=notes):
        f = template_fields(block)
        body = block[2:-2]
        cuts = _depth0_pipes(body)
        if not any(isinstance(k, str) for k in f):
            # A block with no NAMED argument is not a row, and emitting one here
            # would be inventing exactly what this card is about. Three shapes
            # reach this line and all three are plumbing, not episodes: a bare
            # `{{Episode list}}`, and the two sublist pointers
            # `{{Episode list/sublist|List of Foo episodes}}` and
            # `{{#invoke:Episode list|sublist|List of Foo episodes}}`, whose only
            # arguments name the page the real rows live on. Each of them used to
            # come back as a nameless, unnumbered, undated row — two of them
            # newly, one of them since before CLU-167, and the comment that used
            # to sit here promised the opposite while guarding only the first.
            continue
        # `block` is reproduced byte-for-byte as the old regex built it, because
        # some generators re-read it with regexes of their own. Two quirks are
        # therefore deliberate. The old pattern consumed `|sublist|<page>` for
        # the {{#invoke:}} spelling — `[^|\n]*` for the page, so `| 1 = Naruto:
        # Shippuden season 1` went too — but left `|Page` in the block for
        # {{Episode list/sublist|Page}}, so the two forms disagree. And the
        # terminator `\n\s*}}` ate the newline before the close while keeping
        # any trailing space before it.
        skip = 0
        if re.match(r"\{\{\s*#invoke:", block) and len(cuts) >= 2:
            parts = [body[a + 1:b] for a, b
                     in zip(cuts, cuts[1:] + [len(body)])][:2]
            if parts[0].strip().lower() == "sublist" \
                    and "\n" not in parts[1].rstrip():
                skip = 2
        if skip >= len(cuts):
            # Everything on the block was sublist plumbing; the guard above has
            # already let those go, and this keeps the index below honest rather
            # than clamping it back onto an argument it means to skip.
            continue
        legacy = "\n" + re.sub(r"\n\s*\Z", "", body[cuts[skip]:])
        nums = numbers(f, "EpisodeNumber", notes=notes)
        nums2 = numbers(f, "EpisodeNumber2", notes=notes)
        rtitle = clean(f.get("RTitle") or "")
        alttitle = clean(f.get("AltTitle") or "")
        title = clean(field(f, "Title") or "").strip('"') \
            or display_title(f.get("RTitle")) or display_title(f.get("AltTitle"))
        ym = re.search(r"(19|20)\d{2}", field(f, "OriginalAirDate") or "")
        e = Episode(nums[0] if nums else None, nums2[0] if nums2 else None,
                    title, int(ym.group(0)) if ym else None, legacy)
        e.fields, e.nums, e.nums2 = f, nums, nums2
        e.numparts, e.start = f.get("NumParts", ""), start
        e.rtitle, e.alttitle = rtitle, alttitle
        out.append(e)
    return out


def infobox(text, kind=r"film|television"):
    """A field reader over the page's first infobox, comments pre-stripped,
    multi-line values captured whole (to the next field or the box close).

    Deliberately untouched by CLU-167. Its `[ \\t]*` after the `=` means it
    never had defect 4, it strips comments already so it never had defect 5, and
    it has ~100 callers whose output nobody has measured. Its real limits are
    that it is gated to {{Infobox film|television}} and reads a fixed window
    rather than the template's true extent; a caller that needs either — a
    Fandom episode template, say — should use
    `template_fields(templates(text, name)[0])` instead of widening this.
    """
    im = re.search(r"\{\{Infobox (%s)" % kind, text, re.I)
    if not im:
        return None
    box = re.sub(r"<!--.*?-->", "", text[im.start():im.start() + 6000], flags=re.S)

    def read(name):
        m = re.search(r"^\s*\|\s*%s[ \t]*=[ \t]*(.*?)"
                      r"(?=\n\s*\|\s*[a-z_ ]+[ \t]*=|\n\}\})" % name,
                      box, re.M | re.S | re.I)
        return m.group(1).strip() if m else ""

    return read
