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
7. clean()'s inline-template rule needs a pipe, so EVERY argument-less template
   fell through to stripping the braces and survived as its own name: {{hsp}}
   became "hsp" ("USS Callisterhsp: Into Infinity"), and so did {{nbsp}},
   {{snd}}, {{PAGENAME}} and {{Episode cast}}. Fixing hsp alone would have left
   the class open, so clean() now resolves argument-less templates by name and
   drops the ones it does not know.

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

numbers() cleans a value before looking for digits for the same family of
reason — `19<ref name="finale2"/>` yields [19, 2] otherwise, and an episode 2
conjured out of a ref name is fabricated catalogue data.

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

Measured against every cached article in the repo — 579 of 4,393 carry an
{{Episode list}} — 11 pages change row count: 9 gain rows the old reader dropped,
and 2 lose rows that were commented out and never existed (Bleach's table does
both at once, shedding five phantoms and gaining one real row). Of the 13,617
rows on pages whose count is unchanged, 571 titles change, every one of them from
blank or mangled to right, and 13,577 blocks come back byte-identical; the rest
are longer, because a nested template no longer truncates them. No page that
parsed before fails now, and none did before either.

The fixture set pins episodes(), clean(), templates(), template_fields(),
field() and numbers(). It does NOT exercise table_rows() or infobox(), which are
the module's two other public readers and are deliberately unchanged here — so
this file is pinned in the places CLU-167 touched, not everywhere.
"""
import collections
import json
import pathlib
import re
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


# Argument-less templates, which clean()'s keep-the-last-argument rule cannot
# see because it requires a pipe. Left to the old brace-stripping fallthrough
# every one of these surfaced as its own NAME in display text: {{hsp}} shipped
# "USS Callisterhsp: Into Infinity". Anything not listed here is dropped rather
# than rendered, because a template name is never the text a reader wants.
_BARE_TEMPLATES = {
    "hsp": "", "nbsp": " ", "thinsp": " ", "shy": "", "wbr": "", "zwsp": "",
    "snd": " – ", "spnd": " – ", "sndash": " – ", "spndash": " – ",
    "spaced en dash": " – ", "ndash": "–", "en dash": "–", "mdash": "—",
    "em dash": "—", "spaces": " ", "'": "'", "'s": "'s",
}


def clean(t):
    """Wikitext -> display text. Comments go first, then footnotes vanish whole;
    wikilinks keep their label; inline templates keep their last argument;
    argument-less templates resolve by name (and drop if unknown, never
    rendering as the word "hsp"); italics drop."""
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
    t = re.sub(r"\{\{([^{}|]*)\}\}",
               lambda m: _BARE_TEMPLATES.get(m.group(1).strip().lower(), ""), t)
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


def templates(text, name="Episode list", offsets=False, keep_comments=False):
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

    Raises ValueError on a block whose braces never close. Real pages reach that
    state through conditional transclusion, which direct_view() resolves first,
    so what survives that is genuinely broken input and worth stopping on.
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
            raise ValueError("unclosed {{%s}} template at offset %d: %r"
                             % (name, index[m.start()],
                                view[m.start():m.start() + 120]))
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


def numbers(fields, base="EpisodeNumber"):
    """Every episode number a row claims under `base`, in order, as written.

    Two notations say the same thing and the old reader lost both. `53<hr>54`
    is one Mad Men row covering episodes 53 and 54; `EpisodeNumber_1` /
    `EpisodeNumber_2` is Broken Bow, the two-hour Enterprise pilot, covering 1
    and 2. Returns [53, 54] and [1, 2].

    The branch is on `base_1` being present, NOT on NumParts. NumParts means
    "this was N broadcasts", which is not the same claim: Doctor Who's season 6
    serials carry NumParts of 4 to 10 with a single EpisodeNumber and no
    `EpisodeNumber_` anywhere, so a NumParts-triggered reader returns nothing
    for every one of them. Where both are present they are cross-checked.

    The value is cleaned before digits are looked for, and that ordering is not
    cosmetic: `19<ref name="finale2"/>` yields [19, 2] otherwise, and an
    episode 2 invented out of a ref name is fabricated catalogue data.

    Returns [] when the field is missing or carries no number — reporting what
    the source says, including that it says nothing. The generators assert
    their own coverage.
    """
    if ("%s_1" % base) in fields:
        out = []
        while ("%s_%d" % (base, len(out) + 1)) in fields:
            out += _digits(fields["%s_%d" % (base, len(out) + 1)])
        parts = fields.get("NumParts", "")
        want = _digits(parts)
        if want and len(out) != want[0]:
            raise ValueError("%s_1.. gave %r but NumParts says %r"
                             % (base, out, parts))
        return out
    return _digits(fields.get(base, ""))


def _digits(value):
    return [int(d) for d in re.findall(r"\d+", clean(value or ""))]


class Episode(collections.namedtuple(
        "Episode", "num_overall num_in_season title year block")):
    """One {{Episode list}} row.

    Unpacks as the 5-tuple it always was, because 22 generators unpack it
    positionally and this file is not the place to move them. `num_overall` and
    `num_in_season` stay int-or-None and stay the FIRST number, so a caller
    that never knew a row could carry two sees exactly what it saw before.
    What the tuple cannot express hangs off the row instead:

        .fields    every argument on the block, from template_fields()
        .nums      all overall numbers, e.g. [53, 54] or [1, 2]
        .nums2     all in-season numbers
        .numparts  NumParts as written, or ""
        .start     offset of the block in the text handed to episodes()
    """


def episodes(text):
    """Episode-list entries: (num_overall, num_in_season, title, year, block).

    A composition of templates(), template_fields(), field() and numbers(); see
    Episode for the numbers a row can now carry that the tuple cannot hold.
    Handles {{Episode list}}, {{Episode list/sublist|Page}}, and
    {{#invoke:Episode list|sublist|Page}}; keeps the leading pipe inside the
    block so the first field is findable, and `block` keeps the shape it always
    had, since some generators re-read it with regexes of their own.

    The title falls back Title -> RTitle -> AltTitle, and empty titles stay
    empty (an empty title once containment-matched everything) — but an empty
    one here now means the source genuinely has no title yet, not that the
    field was read under the wrong name.
    """
    out = []
    for start, block in templates(text, "Episode list", offsets=True):
        f = template_fields(block)
        body = block[2:-2]
        cuts = _depth0_pipes(body)
        if not cuts:
            # The old pattern required `(\|.*?)`, so a bare `{{Episode list}}`
            # with no arguments was never a row. It still is not one: emitting an
            # empty row here would be inventing the thing this card is about.
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
        legacy = "\n" + re.sub(r"\n\s*\Z", "", body[cuts[min(skip, len(cuts) - 1)]:])
        nums = numbers(f, "EpisodeNumber")
        nums2 = numbers(f, "EpisodeNumber2")
        title = clean(field(f, "Title", "RTitle", "AltTitle") or "").strip('"')
        ym = re.search(r"(19|20)\d{2}", field(f, "OriginalAirDate") or "")
        e = Episode(nums[0] if nums else None, nums2[0] if nums2 else None,
                    title, int(ym.group(0)) if ym else None, legacy)
        e.fields, e.nums, e.nums2 = f, nums, nums2
        e.numparts, e.start = f.get("NumParts", ""), start
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
