"""Static sweep: every property, every convention, every stray artifact.

Checks the classes of bug this project has actually shipped: wikitext plumbing
leaking into display strings, "0 films and" phrasing, ids that break build.py,
filter values with no tagged rows, paceTiers pointing at tiers nobody uses,
missing or out-of-range popularity values, duplicate accents, weights that are
negative or absurd, empty or placeholder text where a reader would see it, and
a hard-coded count or hours figure in a section subtitle or a blurb that the
rows no longer support.
"""
import json
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


findings = collections.defaultdict(list)
accents, pops = {}, {}

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
    a = (p.get("accent"), p.get("accentDark"))
    if a in accents:
        findings[slug].append("accent pair shared with %s" % accents[a])
    accents[a] = slug

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

    for note in p.get("notes", []):
        text = note[1] if isinstance(note, list) else note
        if WIKI_JUNK.search(text or ""):
            findings[slug].append("wikitext junk in notes: %r" % text[:70])

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
if total:
    print("\n%d finding(s)" % total)
    raise SystemExit(1)
