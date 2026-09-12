"""Static sweep: every property, every convention, every stray artifact.

Checks the classes of bug this project has actually shipped: wikitext plumbing
leaking into display strings, "0 films and" phrasing, ids that break build.py,
filter values with no tagged rows, paceTiers pointing at tiers nobody uses,
missing or out-of-range popularity values, accents two lists cannot be told
apart by (per theme, in CIEDE2000, with the whole distribution printed), accents
too faint to see against the page they are drawn on, weights that are negative
or absurd, empty or placeholder text where a reader would see it, a
hard-coded count or hours figure in a section subtitle or a blurb that the rows
no longer support, and the one mechanically checkable half of the note standard.

Two exit levels. FINDINGS fail the build (CI runs this file and reads only its
exit code). NOTICES print and do not, because they are rules whose bar was read
off two exemplar lists and which shipped lists break for reasons a regex cannot
tell from a defect. A lint that cries wolf gets read as noise, and 0 findings
then stops meaning anything — which is exactly how rule 06 went unchecked for
weeks while `findings: 0` was quoted as proof it held.
"""
import json
import math
import pathlib
import re
import collections

PROPS = pathlib.Path("properties")
ID_OK = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
WIKI_JUNK = re.compile(r"\[\[|\]\]|\{\{|\}\}|<ref|</ref|''|&nbsp;|<br|\|\||File:|thumb\|"
                       r"|rowspan=|colspan=|scope=|align=|style=")
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
ZERO_PHRASE = re.compile(r"\b0 (films?|seasons?|games?|episodes?|entries|shows?|winners?)\b")

# ---------------------------------------------------------------- stated counts
# 53 of the generators write a literal count into a `sub` or `blurb` rather than
# computing it, so a row added later drifts away from the prose and nothing
# notices. Every one of those claims reconciles today; this is the net that keeps
# it that way.
#
# It is deliberately a REGRESSION NET, NOT A PROOF. It arms about 862 of the
# 1,056 count claims and 361 of the 379 hour claims, and stays silent on the two
# shapes it cannot judge — compound subtitles ("20 films and 88 seasons") and
# hour figures derived from `N min` inside row notes rather than from weights.
# The naive rule (claim == len(items)) was measured first and produces 36 false
# failures and zero true ones, so each guard below is load-bearing:
#
#   * len(cs) == 1 and the ADDEND guard exclude compound prose that is correct
#     ("43 episodes, with the film where it opened", "6 films + 1 not Eon").
#   * span() counts a range row as the episodes it covers, which is the only
#     reason the TV lists pass: frasier, seinfeld, m*a*s*h, the-office,
#     golden-girls, x-files and star-trek merge double-numbered broadcasts into
#     one row and state the BROADCAST count on purpose.
#   * the hour tolerances absorb rounding, not error. Generators round from raw
#     minutes while `w` is stored per row to two decimals, so re-summing lands
#     up to an hour off on criterion/s1001 (says 166, sums 166.52) and three
#     others. Exact equality would fail those four immediately.
#   * APPROX skips averages — persona "averages 84 hours each" is not a total.
COUNT = re.compile(
    r"\b(\d[\d,]*|one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
    r"twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
    r"twenty|thirty|forty|fifty|sixty|a)\s+"
    r"(films?|episodes?|games?|entries|entry|seasons?|features?|novels?|books?|"
    r"issues?|volumes?|chapters?|stories|story|shorts?|specials?|serials?|"
    r"shows?|winners?|parts?|sessions?|cuts?|works?|broadcasts?|releases?|OVAs?)\b",
    re.I)
ADDEND = re.compile(r"\bplus\b|\+|\bwith\b|\band\b|\bof\b|\bnot\b|\boptional\b"
                    r"|\bbonus\b|\bunaired\b|\beither side\b|\bin \d+ rows\b|,", re.I)
HOURS = re.compile(r"\b(\d[\d,]*)\s+hours?\b")
APPROX = re.compile(r"\beach\b|\baverages?\b|\bapiece\b", re.I)
# The dash class must include U+2010..U+2015. The property files use U+2013 in
# `n` values like "S4E1-2"; an ASCII-only hyphen makes every ranged row count as
# one and the count rule then fires on all seven TV lists at once.
RANGE = re.compile(r"(\d+)\s*[‐-―-]\s*(\d+)\s*$")


def span(n):
    """How many numbered things a row covers. "S4E1-2" is two episodes."""
    m = RANGE.search(str(n or ""))
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if b >= a:
            return b - a + 1
    return 1


def wsum(items):
    """Total weight, or None when any row is unweighted.

    Mirrors the rule already set in src/build.py: a partial total is refused
    rather than averaged, because an unweighted row means "length unverified"
    and inventing one is the bug CLU-131 is about.
    """
    if not items:
        return None
    tot = 0.0
    for x in items:
        w = x.get("w")
        if not isinstance(w, (int, float)) or isinstance(w, bool) or w < 0:
            return None
        tot += w
    return tot


# ------------------------------------------------------------- the note standard
# Ruled by Nathan on CLU-275, 2026-08-28 ("4 and 6 are good", and rule 02
# narrowed: "verdicts are allowed but like make it sparing and only for if
# something is about if its worth your time etc."). Written out in full in
# scratch/DECISIONS.md, which is gitignored, so the nine rules are restated here
# because this is the committed copy:
#
#   01 No plot, ever. A quoted arc title and a formal property are not plot.
#   02 A verdict is allowed sparingly and only about whether a thing is worth
#      your time. Measured bar: 10 of 83 notes, about one in eight.
#   03 A row note answers one of four questions and nothing else: where am I in
#      the run, what do I do, whose is it, what is it called.
#   04 Length scales with how many rows the reader passes: under 60 characters
#      once a list is past ~100 rows.
#   05 Repetition is correct. Never de-duplicate a note for tidiness.
#   06 Every list ends with an unheaded note naming the source. No heading is
#      what makes it read as a colophon rather than advice. Where the source is
#      genuinely unknown the note says so rather than guessing.
#   07 Explain clubd's own machinery only where this list is unusual.
#   08 A section intro is for starting cold, and most sections do not get one.
#   09 The section `sub` is a dateline: when, then how much it matters.
#
# WHAT IS ENFORCED HERE, and it is deliberately only rule 06's structural half.
# A note is a string; nine of these ten rules are about what the string MEANS.
#
#   FINDING  a list carries no notes at all, so nothing says where it came from.
#            This is the shape that actually shipped: fma-brotherhood, the #2
#            pinned list in the catalogue, had an empty notes array for weeks.
#   FINDING  a note is structurally empty — a blank string, or a [head, text]
#            pair whose text half is blank. A reader sees a heading and nothing.
#   NOTICE   the last note carries a heading, so it reads as one more piece of
#            advice rather than as the colophon rule 06 asks for. Eight lists.
#   NOTICE   no note anywhere contains a word that names a source. A keyword
#            proxy, never a proof: it cannot tell a real provenance note from a
#            note that happens to say "Wikipedia", which is why it only notices.
#
# WHAT IS NOT ENFORCED, each for a measured reason rather than for effort:
#
#   rule 01  a regex cannot separate "the best opening issue of the saga" from
#            "the issue where he dies" — the ruling itself says so. Human rule,
#            checked at review; the corpus run is CLU-123.
#   rule 02  measured across the catalogue: one list of 230 sits above the
#            one-in-eight bar (civil-war, 4 of 23), and all four of its notes
#            are legitimate worth-your-time calls. The check would flag a
#            compliant list and nothing else.
#   rule 04  measured: 816 notes across 39 shipped lists are over 60 characters
#            on a list past 100 rows, and the long ones are mostly deliberate
#            registers (japanese-cinema runs `country / director / runtime`).
#            The bar was read off two exemplar lists; it does not survive
#            contact with the catalogue as a pass/fail.
#   rule 06  "names the source" is left to the keyword notice above, and is
#            checked across the whole notes array rather than on the last note,
#            because naruto, naruto-manga and one-piece-manga close on a status
#            note and name their source one note earlier — CLU-534 ruled that
#            satisfies the substance of the rule.
#   coverage CLU-276 asked for a flag on note coverage between ~5% and ~95%
#            without a declared reason. The declaration would be a `noteKind`
#            field, and no property file has one, so the check would be a bare
#            coverage threshold with no way to say "deliberate" — 100+ lists
#            sit in that band. It needs the schema field first.
#
# The gated list is exempt from all of it, by Nathan's ruling on CLU-536: "the
# secret.json file is just for haha funnies. no need to apply any outstanding
# rules to it." It is exempted on the `secret` flag, the same way src/build.py
# exempts it, rather than by slug.
PROVENANCE = re.compile(
    r"\b(wikipedia|wikidata|wiki|marvel database|comic ?vine|grand comics|"
    r"howlongtobeat|hltb|backloggd|imdb|tmdb|epguides|letterboxd|"
    r"sources?|sourced|cross-checked|compiled|comes? from|came from|"
    r"taken from|read off|read out of|according to|episode list(ing)?|"
    r"reading order|press|calendar|database|\.com|\.org|\.net)\b", re.I)


# ------------------------------------------------------------- accent distance
# CLU-544. Two lists wore an identical colour for weeks and the check meant to
# catch it passed them, because it compared the PAIR (accent, accentDark) and
# each collision was in one half of the pair with the other half different. The
# pair is not what anybody sees: accentOf() in src/template.html renders ONE of
# the two at a time, chosen by prefers-color-scheme, so the comparison has to be
# per theme -- light against light, dark against dark, with `accentDark or
# accent` standing in for a list that declares no dark tone. Comparing pairs hid
# four exact collisions: frasier/one-location-films and mcu-anthology/seinfeld
# on `accent`, bruce-lee/jackie-chan and cates-venom/directors on `accentDark`.
#
# Distance is CIEDE2000 over sRGB -> D65 XYZ -> CIE Lab, written out here rather
# than imported, because this repo runs on a bare stdlib python and a lint
# nobody can execute is not a lint. Plain CIE76 (euclidean Lab) was measured
# against it across the whole catalogue first and is not good enough in the
# blues, which is where this catalogue is crowded: dc-animation/dc-anthology is
# dE76 6.09 and dE00 1.15, so CIE76 calls a pair nobody can separate
# "comfortably apart". Where the two disagree, CIEDE2000 is the one that matches
# what is on screen.
#
# WHICH LEVEL, and why:
#   FINDING  two lists rendering the IDENTICAL hex in the same theme. Mechanical,
#            unambiguous, and there are none, so it cannot turn main red unless
#            somebody actually ships a collision.
#   NOTICE   a pair under dE00 1.0 (the CIE line below which a normal observer
#            sees no difference at all), and an accent under 3:1 against the
#            ground it is drawn on. Both are real, neither is worth a red build.
#   NOTHING  everything above that, however tight. 1,036 light pairs sit under
#            the 8.0 floor tools/make_grand-theft-auto.py holds itself to and 350
#            under 5.0, so a build failing at either would have gone red around
#            the ninetieth list. What was actually missing is not refusal, it is
#            that nobody knew how tight it had got -- so the census prints the
#            whole distribution on every build and refuses almost nothing.
# The grounds are the real tokens from src/template.html: --card and --paper, in
# :root and in the prefers-color-scheme: dark block.
GROUNDS = {"light": ("#F2F2EE", "#E6E7E2"),
           "dark": ("#1B1E22", "#131518")}
IMPERCEPTIBLE = 1.0   # dE00 below which there is nothing to see
MIN_CONTRAST = 3.0    # WCAG 1.4.11, non-text contrast for a graphical mark
WP = (0.95047, 1.0, 1.08883)  # D65


def _chan(hexv):
    h = hexv.lstrip("#")
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


def _linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lab(hexv):
    """sRGB hex -> CIE Lab (D65)."""
    r, g, b = (_linear(c) for c in _chan(hexv))
    xyz = (r * 0.4124564 + g * 0.3575761 + b * 0.1804375,
           r * 0.2126729 + g * 0.7151522 + b * 0.0721750,
           r * 0.0193339 + g * 0.1191920 + b * 0.9503041)

    def f(t):
        return t ** (1 / 3.0) if t > 216 / 24389.0 else (841 / 108.0) * t + 4 / 29.0

    fx, fy, fz = (f(v / w) for v, w in zip(xyz, WP))
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def de2000(p1, p2):
    """CIEDE2000 between two Lab triples, kL = kC = kH = 1."""
    L1, a1, b1 = p1
    L2, a2, b2 = p2
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = (C1 + C2) / 2.0
    G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25.0 ** 7))) if Cb else 0.5
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360 if (a1p or b1) else 0.0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360 if (a2p or b2) else 0.0
    dLp, dCp = L2 - L1, C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    else:
        dhp = h2p - h1p - 360 if h2p > h1p else h2p - h1p + 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2.0)
    Lbp, Cbp = (L1 + L2) / 2.0, (C1p + C2p) / 2.0
    if C1p * C2p == 0:
        hbp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hbp = (h1p + h2p) / 2.0
    elif h1p + h2p < 360:
        hbp = (h1p + h2p + 360) / 2.0
    else:
        hbp = (h1p + h2p - 360) / 2.0
    T = (1 - 0.17 * math.cos(math.radians(hbp - 30))
         + 0.24 * math.cos(math.radians(2 * hbp))
         + 0.32 * math.cos(math.radians(3 * hbp + 6))
         - 0.20 * math.cos(math.radians(4 * hbp - 63)))
    SL = 1 + (0.015 * (Lbp - 50) ** 2) / math.sqrt(20 + (Lbp - 50) ** 2)
    SC = 1 + 0.045 * Cbp
    SH = 1 + 0.015 * Cbp * T
    RT = (-math.sin(math.radians(60 * math.exp(-(((hbp - 275) / 25.0) ** 2))))
          * 2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25.0 ** 7))) if Cbp else 0.0
    return math.sqrt((dLp / SL) ** 2 + (dCp / SC) ** 2 + (dHp / SH) ** 2
                     + RT * (dCp / SC) * (dHp / SH))


# Four of Sharma's published CIEDE2000 reference pairs, kept here because a
# silently wrong distance function makes this census go quiet rather than wrong,
# and quiet is how rule 06 went unchecked for weeks. The full 23-pair set was run
# against this implementation and every one agrees to 1e-4; these four are the
# ones that catch the mistakes actually easy to make -- the hue-difference sign
# convention, the 275-degree rotation term, and the near-neutral guard.
for _p1, _p2, _want in (
        ((50.0, 2.6772, -79.7751), (50.0, 0.0, -82.7485), 2.0425),
        ((50.0, 2.49, -0.001), (50.0, -2.49, 0.0011), 7.2195),
        ((50.0, 2.5, 0.0), (73.0, 25.0, -18.0), 27.1492),
        ((2.0776, 0.0795, -1.135), (0.9033, -0.0636, -0.5514), 0.9082)):
    _got = de2000(_p1, _p2)
    assert abs(_got - _want) < 2e-4, (
        "CIEDE2000 is wrong: %r vs %r should be %.4f, got %.4f"
        % (_p1, _p2, _want, _got))


def contrast(h1, h2):
    """WCAG relative-luminance ratio between two hex colours."""
    def lum(h):
        r, g, b = (_linear(c) for c in _chan(h))
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    a, b = lum(h1), lum(h2)
    if a < b:
        a, b = b, a
    return (a + 0.05) / (b + 0.05)


def note_text(note):
    """(heading, body) for either note shape: a bare string or [head, text]."""
    if isinstance(note, list):
        return (note[0] if len(note) > 0 else "") or "", \
               (note[1] if len(note) > 1 else "") or ""
    return "", (note or "")


def plain(s):
    """ASCII-safe echo. Notes carry U+00B7 and U+2013, and printing one raw
    raises UnicodeEncodeError on a Windows console — which turns a lint finding
    into a crash that shows nothing. Same reason the count messages stay ASCII.
    """
    return str(s).encode("ascii", "backslashreplace").decode("ascii")


findings = collections.defaultdict(list)
notices = collections.defaultdict(list)
accents, pops = {"light": {}, "dark": {}}, {}

# Ahead of whatever popularity says, these two open the catalogue. Kept in step
# with PINNED in src/build.py; if they diverge, the manifest check below is
# what catches it. See POPULARITY.md.
PINNED = ["hickman-secret-wars", "fma-brotherhood"]

for f in sorted(PROPS.glob("*.json")):
    if f.name in ("index.json", "search.json"):
        continue
    slug = f.stem
    try:
        p = json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:
        findings[slug].append("INVALID JSON: %s" % e)
        continue

    if p.get("slug") != slug:
        findings[slug].append("slug mismatch: %r" % p.get("slug"))
    for field in ("title", "unit"):
        if not p.get(field):
            findings[slug].append("missing %s" % field)
    u = p.get("unit") or {}
    if not (u.get("one") and u.get("many")):
        findings[slug].append("unit incomplete")

    # Catalogue position. A list with no popularity is the drift this field
    # exists to stop: it would take whatever the sort gave it and nobody would
    # notice. Refuse it here so the next build fails instead of shipping a
    # catalogue ordered by accident. Equal values are fine and expected — the
    # build breaks those on title — so a shared value is not a finding.
    if "order" in p:
        findings[slug].append(
            "carries `order`, replaced by `popularity` — see POPULARITY.md")
    pop = p.get("popularity")
    if pop is None:
        findings[slug].append(
            "no popularity value — every list needs one, see POPULARITY.md")
    elif isinstance(pop, bool) or not isinstance(pop, int) or not 0 <= pop <= 100:
        findings[slug].append(
            "popularity %r is not a whole number from 0 to 100" % pop)
    else:
        pops[slug] = pop
    for k in ("accent", "accentDark"):
        v = p.get(k)
        if v and not HEX.match(v):
            findings[slug].append("%s not hex: %r" % (k, v))
    # What each theme actually renders, for the census after the loop. The
    # dark fallback mirrors accentOf(): `(dark && accentDark) || accent`.
    if HEX.match(p.get("accent") or ""):
        accents["light"][slug] = p["accent"].upper()
        accents["dark"][slug] = (p.get("accentDark") or p["accent"]).upper()

    ids, tiers_used, tags_used = [], set(), set()
    for s in p.get("sections", []):
        if not s.get("items"):
            findings[slug].append("empty section %r" % s.get("id"))
        if not ID_OK.match(s.get("id", "")):
            findings[slug].append("bad section id %r" % s.get("id"))
        for text_field in ("title", "sub", "intro"):
            v = s.get(text_field) or ""
            if WIKI_JUNK.search(v):
                findings[slug].append("wikitext junk in section %s %s: %r"
                                      % (s.get("id"), text_field, v[:60]))
            if ZERO_PHRASE.search(v):
                findings[slug].append("zero-phrase in section %s: %r"
                                      % (s.get("id"), v[:60]))

        # A subtitle that states one plain count, and nothing that would make it
        # a sum of parts, has to match either the rows or the things they cover.
        # Findings stay pure ASCII on purpose: subs carry U+00B7 and U+2013, and
        # echoing one into a message raises UnicodeEncodeError on a Windows
        # console, turning a lint finding into a crash that shows nothing.
        sub = s.get("sub") or ""
        items = s.get("items", [])
        cs = COUNT.findall(sub)
        if len(cs) == 1 and cs[0][0][:1].isdigit() and not ADDEND.search(sub):
            claim = int(cs[0][0].replace(",", ""))
            covered = sum(span(x.get("n", "")) for x in items)
            if claim != len(items) and claim != covered:
                findings[slug].append(
                    "section %s says %d %s but has %d rows covering %d"
                    % (s.get("id"), claim, cs[0][1].lower(), len(items), covered))
        tw = wsum(items)
        if tw is not None and not APPROX.search(sub):
            for h in HOURS.findall(sub):
                if abs(int(h.replace(",", "")) - tw) > 1.0:
                    findings[slug].append(
                        "section %s says %s hours but its rows weigh %.1f"
                        % (s.get("id"), h, tw))

        for x in s.get("items", []):
            ids.append(x.get("id"))
            # build.py only enforces the strict charset on slugs and section
            # ids; item ids with accents and dots are live and load-bearing.
            # What actually breaks: whitespace, quotes, angle brackets.
            xid = x.get("id") or ""
            if not xid or re.search(r"[\s\"'<>&\\]", xid):
                findings[slug].append("dangerous item id %r" % xid)
            if not x.get("t"):
                findings[slug].append("item with no title: %r" % x.get("id"))
            w = x.get("w")
            if w is not None and (not isinstance(w, (int, float)) or w < 0 or w > 300):
                findings[slug].append("odd weight %r on %s" % (w, x.get("id")))
            tiers_used.add(x.get("tier") or s.get("tier") or 1)
            for t in x.get("tags") or []:
                tags_used.add(t)
            for text_field in ("t", "n", "note"):
                v = x.get(text_field)
                if isinstance(v, str) and WIKI_JUNK.search(v):
                    findings[slug].append("wikitext junk in %s.%s: %r"
                                          % (x.get("id"), text_field, v[:70]))
    dupes = [k for k, c in collections.Counter(ids).items() if c > 1]
    if dupes:
        findings[slug].append("duplicate ids: %s" % dupes[:4])

    # A blurb's hours figure may legitimately mean any of three scopes, and all
    # three are in use: pixar's "about 52 hours" excludes the optional shorts,
    # raimi's "about 30 hours" excludes the TV rows, and pokemon's "add 237
    # more" is the optional remainder. So a claim passes if it matches any of
    # them, and only a figure matching none is a finding.
    blurb = p.get("blurb") or ""
    if blurb and not APPROX.search(blurb):
        allit = [x for s in p.get("sections", []) for x in s.get("items", [])]
        tot = wsum(allit)
        if tot is not None:
            req = sum(x.get("w", 0) for x in allit if not x.get("opt"))
            for h in HOURS.findall(blurb):
                v = int(h.replace(",", ""))
                if min(abs(v - tot), abs(v - req), abs(v - (tot - req))) > 1.5:
                    findings[slug].append(
                        "blurb says %s hours; rows weigh %.1f total, %.1f required"
                        % (h, tot, req))

    flt = p.get("filter")
    if flt:
        vals = set(flt.get("values") or [])
        dead = vals - tags_used
        if dead:
            findings[slug].append("filter values with no tagged rows: %s" % sorted(dead))
        stray = tags_used - vals
        if stray:
            findings[slug].append("tags not in filter values: %s" % sorted(stray))
    elif tags_used:
        findings[slug].append("rows carry tags but no filter is declared: %s"
                              % sorted(tags_used)[:4])

    pt = p.get("paceTiers")
    if pt:
        missing = set(pt) - tiers_used
        if missing:
            findings[slug].append("paceTiers %s includes unused tier(s) %s"
                                  % (pt, sorted(missing)))

    alt = p.get("altSections")
    if alt:
        alt_ids = [x["id"] for s in alt.get("sections", []) for x in s.get("items", [])]
        if not set(alt_ids) <= set(ids):
            findings[slug].append("altSections invents ids")

    # ---- notes: wikitext hygiene, then the note standard (see the block above)
    notes = p.get("notes") or []
    exempt = bool(p.get("secret"))
    for i, note in enumerate(notes):
        head, text = note_text(note)
        if WIKI_JUNK.search(text) or WIKI_JUNK.search(head):
            findings[slug].append("wikitext junk in notes: %r" % plain(text[:70]))
        if not text.strip() and not exempt:
            findings[slug].append(
                "note %d has no text%s — rule 06" % (i, " under the heading %r"
                                                     % plain(head[:40]) if head.strip() else ""))
    if not notes and not exempt:
        findings[slug].append(
            "no notes at all, so nothing says where this list came from — "
            "rule 06 wants a closing provenance note")
    if notes and not exempt:
        head, text = note_text(notes[-1])
        if head.strip():
            notices[slug].append(
                "rule 06: the last note is headed %r, so it reads as advice "
                "rather than as the list's colophon" % plain(head[:40]))
        if not any(PROVENANCE.search(note_text(n)[1]) for n in notes):
            notices[slug].append(
                "rule 06: no note names where the data came from (keyword "
                "proxy, so check it by eye before acting)")

# ------------------------------------------------------------- accent census
# Runs over the whole catalogue at once, which is the point: every earlier
# version of this rule lived inside ONE generator and measured that generator
# against everybody else, so 51 of the 239 generators now carry some private
# variant of it and the other 188 carry none. That is backwards. A list is not
# hard to pick out because of how IT was built, it is hard to pick out because of
# what is next to it, so the check belongs where the whole wall is visible.
#
# It reports, and with one exception does not refuse. See the level argument next
# to de2000() above.
census_lines = []
for theme in ("light", "dark"):
    rendered = accents[theme]
    labs = {s: lab(h) for s, h in rendered.items()}
    slugs = sorted(labs)

    # FINDING: the identical hex in the same theme. Two cards with no difference
    # at all to find, whatever the other theme happens to do.
    groups = collections.defaultdict(list)
    for s in slugs:
        groups[rendered[s]].append(s)
    for hexv, group in sorted(groups.items()):
        if len(group) > 1:
            for s in group:
                findings[s].append(
                    "%s theme renders %s and so does %s - the identical colour, "
                    "not merely a close one; repaint whichever list the colour "
                    "means less for" % (theme, hexv,
                                        ", ".join(x for x in group if x != s)))

    pairs = []
    for i, a in enumerate(slugs):
        for b in slugs[i + 1:]:
            pairs.append((de2000(labs[a], labs[b]), a, b))
    pairs.sort()

    # NOTICE: under the imperceptibility line but not identical. Named on one
    # side of the pair only, so the count is the number of collisions rather
    # than twice it.
    for d, a, b in pairs:
        if d >= IMPERCEPTIBLE:
            break
        if rendered[a] != rendered[b]:
            notices[a].append(
                "%s theme: dE00 %.2f from %s (%s vs %s) - under the 1.0 line, so "
                "the hexes differ and nothing visible does"
                % (theme, d, b, rendered[a], rendered[b]))

    # NOTICE: too faint to see on the surface it is drawn on. The accent lands on
    # the card (--card) and on the page behind it (--paper); the tighter of the
    # two decides whether the dot reads at all.
    card, paper = GROUNDS[theme]
    for s in slugs:
        c = min(contrast(rendered[s], card), contrast(rendered[s], paper))
        if c < MIN_CONTRAST:
            notices[s].append(
                "%s theme: %s is only %.2f:1 against the page ground, under the "
                "3:1 floor for a non-text mark - the dot and a started card's "
                "top edge go faint" % (theme, rendered[s], c))

    # the distribution, printed every build. Pairs are sorted, so the first time
    # a slug appears is its own nearest neighbour.
    nn = {}
    for d, a, b in pairs:
        nn.setdefault(a, d)
        nn.setdefault(b, d)
    near = sorted(nn.values())
    bands = " ".join("<%.0f:%d" % (f, sum(1 for x in pairs if x[0] < f))
                     for f in (1.0, 2.0, 5.0, 8.0))
    census_lines.append(
        "  %-5s %3d lists, %5d pairs | identical:%d %s | nearest-neighbour "
        "median dE00 %.1f" % (theme, len(slugs), len(pairs),
                              sum(1 for x in pairs if x[0] == 0.0), bands,
                              near[len(near) // 2] if near else 0.0))
    for d, a, b in pairs[:4]:
        census_lines.append("        dE00 %5.2f  %-24s %-8s %-24s %s"
                            % (d, a, rendered[a], b, rendered[b]))

# ---- the committed tree must be self-consistent: every manifest entry has
# its property file and vice versa. A masked git add once shipped a manifest
# offering seven pages whose JSON 404'd on the live site.
manifest_file = PROPS / "index.json"
if manifest_file.exists():
    entries = json.loads(manifest_file.read_text(encoding="utf-8"))
    manifest = {m["slug"] for m in entries}
    on_disk = {f.stem for f in PROPS.glob("*.json")
               if f.name not in ("index.json", "search.json")}
    for miss in sorted(manifest - on_disk):
        findings[miss].append("IN MANIFEST BUT NO FILE — would 404 live")
    for stray in sorted(on_disk - manifest):
        findings[stray].append("file not in manifest — rebuild before commit")

    # ---- the shipped catalogue must be the one the data describes. A stale
    # manifest is the failure mode here: the numbers get edited, nobody
    # rebuilds, and the live page keeps yesterday's order.
    for m in entries:
        want = pops.get(m["slug"])
        if want is not None and m.get("popularity") != want:
            findings[m["slug"]].append(
                "manifest popularity %r but file says %d — rebuild before commit"
                % (m.get("popularity"), want))
    seq = [m["slug"] for m in entries]
    expected = sorted(
        [m for m in entries if m["slug"] in pops],
        key=lambda m: (PINNED.index(m["slug"]) if m["slug"] in PINNED
                       else len(PINNED), -pops[m["slug"]], m["title"]))
    if [m["slug"] for m in expected] != [s for s in seq if s in pops]:
        findings["(catalogue)"].append(
            "manifest order is not popularity order — rebuild before commit")
    top6 = seq[:6]
    for s in PINNED:
        if s not in top6:
            at = seq.index(s) + 1 if s in seq else "absent"
            findings[s].append(
                "pinned to the catalogue top 6 but sits at #%s — check PINNED "
                "in src/build.py, then rebuild" % at)

total = sum(len(v) for v in findings.values())
# index.json and search.json are generated, not properties — subtracting one
# counted search.json as a list and reported one more than the catalogue holds
print("properties checked:",
      len([p for p in PROPS.glob('*.json')
           if p.name not in ('index.json', 'search.json')]))
print("findings:", total)
# There is no allowlist any more. The three standing exceptions here were all
# duplicate `order` values (lanterns/cyberpunk-edgerunners, metal-gear/civil-war,
# one-pace/monster); `order` is gone, and popularity ties are legal by design
# because the build breaks them on title. Nothing is expected to be tolerated.
for slug in sorted(findings):
    for msg in findings[slug]:
        print("  %-18s %s" % (slug, msg))

# Notices do not touch the exit code. They are the note-standard rules that
# shipped lists break for reasons a regex cannot separate from a defect, so
# failing on them would turn main red over placement nits and teach everyone to
# ignore the lint. Printed under their own heading so nobody mistakes a notice
# for a finding, or a clean findings count for a clean catalogue.
notice_total = sum(len(v) for v in notices.values())
print("notices:", notice_total, "(reported, do not fail the build)")
for slug in sorted(notices):
    for msg in notices[slug]:
        print("  %-18s %s" % (slug, msg))

# The census prints whether or not it had anything to say, because the number
# nobody had was how tight the catalogue has become - 1,036 light pairs under the
# floor one generator refuses at, and the wall could not have told you.
print("accent census (CIEDE2000, per theme; dE00 1.0 is the line below which "
      "there is nothing to see):")
for line in census_lines:
    print(line)

if total:
    print("\n%d finding(s)" % total)
    raise SystemExit(1)
