#!/usr/bin/env python3
"""Build index.html and the property manifest.

    python3 src/build.py

Property data is no longer inlined. The page boots, reads ?p=<slug>, and fetches
that property's JSON at runtime, so adding a show is dropping a file into
properties/ and rebuilding. This script's job is to validate those files and
write the manifest the property switcher reads.

Because the data is fetched, the page must be served over http — file:// blocks
fetch. Use `python3 -m http.server 8000`.
"""
import base64
import hashlib
import json
import pathlib
import re
import sys
# aliased: main() names the page it is assembling `html`
from html import escape as html_escape, unescape as html_unescape

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "src" / "template.html"
PROPS = ROOT / "properties"
OUTPUT = ROOT / "index.html"
MANIFEST = PROPS / "index.json"
BUILDFILE = ROOT / "build.json"

ID_OK = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")

# Two lists sit at the head of the catalogue by editorial decision, ahead of
# whatever their popularity says. This is deliberately a separate rule and not
# an inflated number: Secret Wars scores 44 and Brotherhood 83 on the honest
# scale, and both keep those values. Pinning is a statement about this club's
# front page; the popularity field stays a statement about the work. Order
# within the tuple is the order they appear. See POPULARITY.md.
PINNED = ("hickman-secret-wars", "fma-brotherhood")


def fail(msg):
    raise SystemExit("build failed: %s" % msg)


def load_property(path):
    try:
        prop = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as e:
        fail("%s is not valid JSON — %s" % (path.name, e))

    slug = prop.get("slug")
    if not slug:
        fail("%s has no slug" % path.name)
    if slug != path.stem:
        fail("%s declares slug %r — slug and filename must match" % (path.name, slug))
    if not ID_OK.match(slug):
        fail("%s: slug %r must be a valid html id" % (path.name, slug))

    for field in ("title", "unit"):
        if not prop.get(field):
            fail("%s has no %s" % (path.name, field))
    if not prop["unit"].get("one") or not prop["unit"].get("many"):
        fail("%s: unit needs both 'one' and 'many'" % path.name)

    # Catalogue position. `order` used to be a hand-assigned menu index that
    # drifted into ties and thematic clumps; `popularity` replaced it, and the
    # catalogue is sorted from it. Checked before anything else about the body
    # so an encrypted or generated list cannot skip it, and refused rather than
    # defaulted — a missing value would quietly bury or promote a new list.
    if "order" in prop:
        fail("%s still carries `order`, which was replaced by `popularity` — "
             "see POPULARITY.md" % path.name)
    pop = prop.get("popularity")
    if isinstance(pop, bool) or not isinstance(pop, int) or not 0 <= pop <= 100:
        fail("%s: popularity must be a whole number from 0 to 100, got %r — "
             "see POPULARITY.md for how to pick one" % (path.name, pop))

    # A generated property has no sections on disk: the page builds them from
    # the calendar when it loads, so the list grows by itself as days pass and
    # a static file would be stale the morning after it shipped. Everything
    # about it that can be checked ahead of time is checked here instead.
    # An encrypted property carries nothing to validate: its sections, its
    # generate block and its real title are all inside the ciphertext, and the
    # build has no key. Check the envelope and stop there.
    sec = prop.get("secret") or {}
    if sec.get("blob"):
        for field in ("salt", "iv", "iter"):
            if not sec.get(field):
                fail("%s: an encrypted property needs secret.%s" % (path.name, field))
        if prop.get("sections") or prop.get("generate"):
            fail("%s: an encrypted property must not also ship its contents"
                 % path.name)
        prop["_total"] = 0
        return prop

    gen = prop.get("generate")
    if gen:
        if prop.get("sections"):
            fail("%s: a generated property must not also carry sections" % path.name)
        if gen.get("kind") != "daily":
            fail("%s: generate.kind %r is not one this build knows"
                 % (path.name, gen.get("kind")))
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", gen.get("start", "")):
            fail("%s: generate.start must be a YYYY-MM-DD date" % path.name)
        if not isinstance(gen.get("slots"), int) or not 1 <= gen["slots"] <= 24:
            fail("%s: generate.slots must be a whole number from 1 to 24" % path.name)
        if not gen.get("idPrefix"):
            fail("%s: generate needs an idPrefix, since item ids are permanent"
                 % path.name)
        prop["_total"] = 0        # only today knows, and today is the reader's
        return prop

    if not prop.get("sections"):
        fail("%s has no sections" % path.name)

    seen = set()
    total = 0
    totalw = 0.0
    nweighted = 0
    for s in prop["sections"]:
        if not s.get("id"):
            fail("%s: a section has no id" % path.name)
        if not ID_OK.match(s["id"]):
            fail("%s: section id %r must be a valid html id" % (path.name, s["id"]))
        if not s.get("items"):
            fail("%s: section %r has no items" % (path.name, s["id"]))
        for x in s["items"]:
            if not x.get("id"):
                fail("%s: an item in %r has no id" % (path.name, s["id"]))
            # duplicate ids make two checkboxes move together, silently
            if x["id"] in seen:
                fail("%s: duplicate item id %r" % (path.name, x["id"]))
            seen.add(x["id"])
            total += 1
            # A weighted list measures itself in hours, so the home bars have
            # to as well (CLU-207). Summed here rather than in the template
            # because the template only ever sees the manifest, which has no
            # per-item anything. Absent `w` contributes nothing: a list is
            # weighted or it is not, and a half-weighted one is the CLU-131
            # trap rather than a thing to average over.
            w = x.get("w")
            if isinstance(w, (int, float)) and w >= 0:
                totalw += float(w)
                nweighted += 1

    prop["_total"] = total
    # only claim a weight total when EVERY row carries one; a partial total
    # would make the bar confidently wrong rather than honestly coarse
    prop["_totalw"] = round(totalw, 2) if (total and nweighted == total) else None
    return prop


# ---- one real file per public list, for crawlers (CLU-211) -----------------
# The site routes on the query string and serves one index.html, and a crawler
# runs no JavaScript: Discord fetches /?p=halo, reads the static head, and
# previews the generic site card for every list alike. So each public list
# gets a page of its own at l/<slug>.html carrying nothing but its own og:/
# twitter: tags and a bounce to the app — a meta refresh for a browser with no
# script, location.replace() for one with, so a person never sees it. A crawler
# reads the tags and stops. GitHub Pages serves a subdirectory's halo.html at
# /l/halo as well (it does so for the site's other subdirectory pages today),
# so that is the URL the tags call canonical.
#
# The build owns l/. A list that is renamed or removed takes its page with it,
# because a stale one would go on previewing a list that no longer exists.
#
# ⚠ The gated list never gets one (CLU-214). Its page would be a public,
# unlinked URL carrying its cover title, and unlinked is exactly how this repo
# has leaked before (CLU-196). It is skipped on the `secret` flag — never by
# name; nothing naming it may enter the repo — and the skip is then PROVED by
# check_embeds() rather than trusted. Its share link stays the app URL, which
# a crawler reads as the generic site card. A generated list is skipped too:
# its count is only known on the day it is read, and a card stating one would
# be wrong the morning after it shipped.
EMBEDS = ROOT / "l"
SITE = "https://clubd.watch"
OG_IMAGE = SITE + "/clubd-og.png"      # one image for every list until CLU-218


# --------------------------------------------------------------------- CLU-548
# Content-Security-Policy.
#
# The site is static files on GitHub Pages. There is no server and no way to
# add a response header, so the policy is delivered in a <meta http-equiv>,
# and four things a real header could do are simply not available:
#
#   * frame-ancestors is ignored in meta, and so is X-Frame-Options, so
#     nothing here stops clubd being framed. Clickjacking has to be answered
#     in the page (or by moving off Pages), not by this policy.
#   * report-uri / report-to are ignored in meta, so a violation in a real
#     browser is a console line nobody sees. scratch/qa2/csp_check.py is the
#     substitute: it drives the page and fails on any violation.
#   * Content-Security-Policy-Report-Only cannot be delivered by meta at all,
#     so there is no staging step. A policy that is wrong is a broken site on
#     the first load, which is why csp_check.py exists and why this function
#     refuses to guess about origins it has not been told about.
#   * sandbox is ignored in meta.
#
# A nonce would be worse than useless here: the page is a static file that
# GitHub Pages serves with Access-Control-Allow-Origin: *, so a "nonce" baked
# into it is a constant that anybody can read — which is exactly what a nonce
# must not be. Hashes are the right primitive for a generated static page, and
# this build is the thing that generates it, so it computes them.
CSP_SCRIPT_CDN = "https://cdn.jsdelivr.net"       # the supabase-js UMD bundle
CSP_FONT_CSS = "https://fonts.googleapis.com"     # the @font-face stylesheet
CSP_FONT_FILES = "https://fonts.gstatic.com"      # the woff2 files it names

# Every off-origin host the page may reach, listed by the element that reaches
# it. A <script src> or <link rel=stylesheet> pointing anywhere else fails the
# build rather than the page — which is the point: adding a CDN link is how a
# CSP gets quietly widened, and here it cannot be done without editing this
# tuple and saying so in the commit.
CSP_SCRIPT_HOSTS = (CSP_SCRIPT_CDN,)
CSP_STYLE_HOSTS = (CSP_FONT_CSS,)

HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
SCRIPT_EL = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.S)
STYLE_EL = re.compile(r"<style\b([^>]*)>(.*?)</style>", re.S)
SHEET_EL = re.compile(r'<link\b[^>]*\brel="stylesheet"[^>]*>')
ATTR_URL = re.compile(r'\b(?:href|src)="([^"]*)"')
# An inline event-handler attribute: a tag, then on<something>="  . The JS in
# this page assigns handlers as properties (`b.onclick = ()=>…`), which has no
# quote after the `=` and so cannot match.
INLINE_HANDLER = re.compile(r"<[a-zA-Z][^>]*?\son[a-z]+\s*=\s*[\"']")


def sha256_src(text):
    """A CSP hash-source over an inline element's content exactly as the
    browser will see it. The template is read with universal newlines and
    index.html is written with newline="\\n", so the string hashed here is the
    string served; hashing the file with CRLF in it would be a silent miss."""
    d = hashlib.sha256(text.encode("utf-8")).digest()
    return "'sha256-" + base64.b64encode(d).decode("ascii") + "'"


def csp_markup(html, page):
    """The page with HTML comments removed, which is what the element scan has
    to read. The first cut of this scanned the page as written and found two
    inline scripts, because the comment above __CSP__ says the words "script
    block" and once said them with angle brackets — a comment describing the
    policy broke the policy. Comments are stripped rather than worked around,
    and the closer counts are checked so that an unbalanced comment inside a
    script or style body fails here instead of silently shifting a hash."""
    out = HTML_COMMENT.sub("", html)
    for tag in ("</script>", "</style>"):
        if out.count(tag) != html.count(tag):
            fail("csp: removing HTML comments from %s also removed a %s, so an "
                 "unbalanced <!-- sits inside a script or style block. The "
                 "policy cannot be derived from a page that does not parse the "
                 "way it reads." % (page, tag))
    return out


def csp_meta(directives):
    body = "; ".join(directives)
    if '"' in body:
        fail("csp: a directive contains a quote and would break the attribute")
    return '<meta http-equiv="Content-Security-Policy" content="%s">' % body


def one_inline(kind, els, page):
    """The single inline <script>/<style> a page is allowed, as a hash-source.

    Refusing the second one is deliberate. Two inline blocks is not a problem
    in itself — two hashes would be fine — but it is nearly always someone
    adding a snippet without knowing the page is hash-pinned, and the failure
    they would otherwise get is a blank page in production.
    """
    inline = [b for a, b in els if "src=" not in a]
    if len(inline) != 1:
        fail("csp: %s carries %d inline <%s> block(s); the policy hashes "
             "exactly one. Add the second hash in build.py deliberately, or "
             "fold the block into the first." % (page, len(inline), kind))
    return sha256_src(inline[0])


def csp_off_origin(urls, allowed, what, page):
    """Split a page's subresource URLs into 'self' and named hosts, refusing
    any host nobody has declared."""
    hosts, selfish = [], False
    for u in urls:
        m = re.match(r"(?:https?:)?//[^/?#]+", u)
        if not m:
            selfish = True                     # relative: same origin
            continue
        origin = m.group(0)
        if not origin.startswith("http"):
            origin = "https:" + origin
        if origin not in allowed:
            fail("csp: %s loads %s from %s, which is not in %s in build.py. "
                 "Either drop the dependency or add the host there — a CDN "
                 "added without touching that tuple would be blocked at "
                 "runtime and the page would come up blank."
                 % (page, what, origin, what))
        if origin not in hosts:
            hosts.append(origin)
    return (["'self'"] if selfish else []) + hosts


def app_policy(html):
    """The policy for index.html, derived from the page it is about to guard.

    Everything here is read out of the finished page rather than written down
    twice, so the policy cannot drift from what the page actually does — the
    two hashes, the Supabase origin and the subresource hosts all come from
    the same string that gets written to disk.
    """
    markup = csp_markup(html, "index.html")
    m = INLINE_HANDLER.search(markup)
    if m:
        fail("csp: the page carries an inline event-handler attribute near "
             "%r. script-src-attr 'none' blocks it; assign the handler as a "
             "property instead." % markup[max(0, m.start() - 40):m.end() + 20])

    scripts = SCRIPT_EL.findall(markup)
    styles = STYLE_EL.findall(markup)
    script_hash = one_inline("script", scripts, "index.html")
    style_hash = one_inline("style", styles, "index.html")
    for body in [b for a, b in scripts if "src=" not in a] + \
                [b for a, b in styles if "src=" not in a]:
        if "__CSP__" in body:
            fail("csp: __CSP__ sits inside a hashed block, so substituting it "
                 "would invalidate the hash it carries")
        # the hash has to be over what the browser gets, and what the browser
        # gets is `html`, comments and all. If a comment lived inside a hashed
        # block, the body above would differ from the served one and this is
        # where that shows up rather than as a blank page.
        if body not in html:
            fail("csp: a hashed block contains an HTML comment, so the hash "
                 "would not match the page as served. Move the comment out.")

    script_src = csp_off_origin(
        [u for a, _ in scripts if "src=" in a for u in ATTR_URL.findall(a)],
        CSP_SCRIPT_HOSTS, "script-src", "index.html")
    style_src = csp_off_origin(
        [u for el in SHEET_EL.findall(markup) for u in ATTR_URL.findall(el)],
        CSP_STYLE_HOSTS, "style-src", "index.html")

    m = re.search(r"const SUPABASE_URL\s*=\s*'(https://[^']+)'", markup)
    if not m:
        fail("csp: could not find SUPABASE_URL in the page, so connect-src "
             "cannot be derived — it must never be hand-copied")
    sb = m.group(1).rstrip("/")

    return [
        # Anything not named below is blocked, and the fallbacks matter as much
        # as the rules: child-src, frame-src, worker-src, manifest-src,
        # media-src, object-src and prefetch-src all inherit this, and the page
        # uses none of them.
        "default-src 'none'",
        # The one inline block by hash, the one CDN by host. No 'unsafe-inline'
        # and no 'unsafe-eval': the page has no eval, no new Function and no
        # string setTimeout, and neither does the supabase-js bundle (checked).
        "script-src " + " ".join([script_hash] + script_src),
        # Free, because no element in the page has an inline handler (asserted
        # above): it blocks an injected onclick= even where the hash in
        # script-src would otherwise be the only gate.
        "script-src-attr 'none'",
        # Style is the one compromise, and it is 'unsafe-inline' because the
        # page carries 81 style="…" attributes, written by innerHTML at
        # runtime. Hashes cannot cover attributes (that needs
        # 'unsafe-hashes', which is a wider grant than this), and rewriting 81
        # of them into classes is a change to every render path in the page,
        # not a security fix. What it costs: injected CSS is allowed. What
        # keeps that small is the rest of the policy — img-src is 'self' and
        # data:, font-src is one host, so the usual CSS exfiltration channels
        # (background-image: url(attacker), @font-face src) have nowhere to
        # send anything.
        #
        # The -elem/-attr pair buys back the element half where it is
        # supported: Chrome, Edge and modern Firefox pin the <style> block to
        # its hash and refuse an injected <style>, while keeping attributes
        # permissive. A browser that supports neither ignores both lines and
        # falls back to style-src above, so the page is never broken by the
        # split — the hardening is additive.
        "style-src " + " ".join(style_src + ["'unsafe-inline'"]),
        "style-src-elem " + " ".join(style_src + [style_hash]),
        "style-src-attr 'unsafe-inline'",
        "font-src " + CSP_FONT_FILES,
        # data: is the favicon, which the page draws on a canvas every time the
        # eye moves and sets as a data: URL on <link rel=icon>.
        "img-src 'self' data:",
        # 'self' is properties/*.json and build.json; the Supabase origin is
        # read out of the page above. wss: is the same host, so it grants an
        # attacker nothing that the REST endpoint does not already, and it
        # means adding a realtime channel later is not an outage.
        "connect-src 'self' %s %s" % (sb, "wss://" + sb.split("//", 1)[1]),
        # No <base> in the page; with this, injecting one cannot repoint every
        # relative fetch in it.
        "base-uri 'none'",
        # One form (the gated list's password box) and it submits to itself.
        "form-action 'self'",
        # Both inherit default-src already; stated because they are the two
        # worth being unambiguous about.
        "object-src 'none'",
        "frame-src 'none'",
        # Nothing in the catalogue is http:// today and qa_lint would notice;
        # this makes a future one an upgrade rather than mixed content.
        "upgrade-insecure-requests",
    ]


def embed_policy(script_body):
    """A share page is a title, a link and a one-line redirect. It needs no
    styles, no images of its own and no network, so everything except that one
    hashed line is 'none'. img-src stays 'self' only because a browser asks
    for /favicon.ico on its own."""
    return [
        "default-src 'none'",
        "script-src " + sha256_src(script_body),
        "script-src-attr 'none'",
        "img-src 'self'",
        "base-uri 'none'",
        "form-action 'none'",
        "upgrade-insecure-requests",
    ]


def embed_of(p):
    """A list's description: its blurb, verbatim.

    The blurb is the one line under the title on the list page — a sentence,
    written to be read on its own, and where it states a count qa_lint holds
    that count to the rows. The first cut of this put the page's header line
    (`subtitle-or-kind · year · N units`) in front of it, and 81 of 209 cards
    then said the count twice, most of them opening lowercase, because the
    header is written to sit over a title and not to open a sentence. Discord
    caches a first embed for a long time and a wrong one is expensive to take
    back, so the card says exactly what the blurb says. CLU-213 may add to it.
    A list with no blurb falls back to the header line rather than to nothing.
    """
    blurb = (p.get("blurb") or "").strip()
    if blurb:
        return blurb
    n = p["_total"]
    unit = p["unit"]["one"] if n == 1 else p["unit"]["many"]
    return " · ".join(str(b) for b in (p.get("subtitle") or p.get("kind"),
                                        p.get("year"), "%d %s" % (n, unit)) if b)


def attr(s):
    """Attribute-safe, and only that: the default also turns an apostrophe
    into an entity, which makes Bob's Burgers unreadable in the file."""
    return html_escape(s, quote=False).replace('"', "&quot;")


def embed_page(p):
    app = "/?p=" + p["slug"]               # slugs pass ID_OK; nothing to escape
    title = attr(p["title"])
    desc = attr(embed_of(p))
    bounce = "location.replace(%s)" % json.dumps(app)
    return "\n".join([
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        # CLU-548 — after the charset (which must land in the first 1024 bytes)
        # and before anything fetchable, which on this page is the bounce below
        csp_meta(embed_policy(bounce)),
        '<meta name="referrer" content="strict-origin-when-cross-origin">',
        "<title>%s — clubd</title>" % title,
        '<meta property="og:site_name" content="clubd">',
        '<meta property="og:type" content="website">',
        '<meta property="og:url" content="%s/l/%s">' % (SITE, p["slug"]),
        '<meta property="og:title" content="%s">' % title,
        '<meta property="og:description" content="%s">' % desc,
        '<meta property="og:image" content="%s">' % OG_IMAGE,
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<meta name="twitter:title" content="%s">' % title,
        '<meta name="twitter:description" content="%s">' % desc,
        '<meta name="twitter:image" content="%s">' % OG_IMAGE,
        '<meta http-equiv="refresh" content="0;url=%s">' % app,
        "<script>%s</script>" % bounce,
        "</head>",
        "<body>",
        # for the browser that honours neither bounce: the page is not blank
        '<a href="%s">%s</a>' % (app, title),
        "</body>",
        "</html>",
        "",
    ])


def no_gated_page(props):
    """A page named for the gated list is removed and the build fails — it is
    never merely swept as stale, and no message names it. write_embeds() runs
    this before its sweep, so the sweep cannot print the name as a removed
    file; check_embeds() runs it again as the proof, after the pages are
    written."""
    for g in (p for p in props if p.get("secret")):
        own = EMBEDS / (g["slug"] + ".html")
        if own.exists():
            own.unlink()      # never leave it where `git add` could find it
            fail("l/ held a share page for the gated list; it has been removed "
                 "— nothing may write that file")


def write_embeds(props):
    public = [p for p in props if not p.get("secret") and not p.get("generate")]
    EMBEDS.mkdir(exist_ok=True)
    no_gated_page(props)
    want = {p["slug"] + ".html" for p in public}
    for f in EMBEDS.iterdir():
        if f.name in want or f.name.startswith("."):
            continue
        # a stale page is removed; anything else is refused rather than
        # deleted, because the build only ever owns what it wrote
        if f.is_file() and f.suffix == ".html":
            f.unlink()
            print("  embeds: removed stale l/%s" % f.name)
        else:
            fail("l/%s is not a share page — l/ holds only what this build "
                 "writes, one l/<slug>.html per public list" % f.name)
    for p in public:
        with (EMBEDS / (p["slug"] + ".html")).open("w", encoding="utf-8",
                                                    newline="\n") as f:
            f.write(embed_page(p))
    return public


def check_embeds(props, public):
    """Prove what write_embeds() promised, from the directory as it now is.

    Every fact here is read back from disk, not inferred from the loop that
    wrote it: l/ holds exactly one page per public list; no page is named for
    the gated list; and nothing the gated list is known by — a link to it, its
    slug or cover title as a title, its password hint, any piece of its
    ciphertext — appears inside any page. CLU-214 asked for a positive
    assertion rather than the absence of a line of code, and this is it. It
    runs on every build and fails the build.

    The slug is looked for where a link would put it — `?p=<slug>` and
    `/l/<slug>`, bounded by anything outside the slug alphabet, so
    `/l/<slug>.html` matches and `a-<slug>-b` does not — and as a whole value.
    Not as a bare word: the gated slug is an ordinary English word, and a
    public blurb that happens to use it is not a leak; a test that failed the
    build on it would send someone hunting for one. Its cover title is
    likewise an ordinary word that public blurbs use, so it is tested as a
    value — a <title>, a content="", the link text — rather than as a
    substring. Failure messages say "the gated list" and nothing more: build
    output gets pasted into cards.
    """
    gated = [p for p in props if p.get("secret")]
    # first, before any message that lists file names could name it
    no_gated_page(props)
    on_disk = {f.name for f in EMBEDS.iterdir() if not f.name.startswith(".")}
    want = {p["slug"] + ".html" for p in public}
    if on_disk != want:
        fail("l/ holds %d page(s) but the catalogue has %d public list(s); "
             "extra: %s, missing: %s"
             % (len(on_disk), len(want),
                ", ".join(sorted(on_disk - want)[:6]) or "none",
                ", ".join(sorted(want - on_disk)[:6]) or "none"))
    pages = [(f, f.read_bytes()) for f in sorted(EMBEDS.glob("*.html"))]
    values = re.compile(rb'content="([^"]*)"|<title>([^<]*)</title>|>([^<>]+)<')
    for g in gated:
        sec = g["secret"]
        link = re.compile(rb"([?&]p=|/l/)" + re.escape(g["slug"].encode("utf-8"))
                          + rb"(?![A-Za-z0-9_-])")
        titles = {t for t in (g["slug"], g.get("title"), sec.get("title")) if t}
        verbatim = [v.encode("utf-8") for v in
                    (sec.get("hint"), sec.get("salt"), sec.get("iv"), sec.get("blob"))
                    if v]
        for f, raw in pages:
            if link.search(raw):
                fail("l/%s links to the gated list — the build will not ship it"
                     % f.name)
            for m in values.finditer(raw):
                v = html_unescape(next(x for x in m.groups() if x is not None)
                                  .decode("utf-8")).strip()
                if v in titles or v.split(" — ")[0] in titles:
                    fail("l/%s carries the gated list's title — the build will "
                         "not ship it" % f.name)
            for piece in verbatim:
                if piece in raw:
                    fail("l/%s carries part of the gated list's envelope — the "
                         "build will not ship it" % f.name)
    print("  embeds: %d share page(s) in l/; none for the gated list, checked"
          % len(pages))


def main():
    if not PROPS.is_dir():
        fail("no properties/ directory")

    files = sorted(p for p in PROPS.glob("*.json")
                   if p.name not in ("index.json", "search.json"))
    if not files:
        fail("properties/ has no property files")

    props = [load_property(p) for p in files]

    slugs = [p["slug"] for p in props]
    if len(slugs) != len(set(slugs)):
        fail("two properties share a slug")

    # The README opens by counting the catalogue, and that number has now been
    # wrong three times — including once in the same commit that was fixing it,
    # because it was typed from the previous value rather than counted. A
    # sentence a human maintains against a number the build already knows is a
    # sentence that goes stale silently, so the build owns it now.
    rm = ROOT / "README.md"
    if rm.exists():
        txt = rm.read_text(encoding="utf-8")
        m = re.search(r"^(\d[\d,]*) lists, from a ", txt, re.M)
        if not m:
            fail("README.md no longer opens with '<N> lists, from a ' — either "
                 "restore that sentence or update this check in build.py")
        claimed = int(m.group(1).replace(",", ""))
        if claimed != len(props):
            fail("README.md says %d lists; the catalogue holds %d. Fix the "
                 "README — the number is not decoration, it is the first "
                 "thing anyone reads." % (claimed, len(props)))
        print("  README: %d lists, agrees with the catalogue" % len(props))


    # Catalogue order. There is no "default property" — a first-time visitor
    # gets the splash picker — so this is presentation only. Three rules, in
    # this order: the pins first, then popularity descending, then title. The
    # title tiebreak is what lets two lists honestly share a popularity value
    # without the catalogue shuffling between builds.
    missing_pins = [s for s in PINNED if s not in {p["slug"] for p in props}]
    if missing_pins:
        fail("pinned list(s) %s have no property file — fix the pin in "
             "build.py or restore the file" % ", ".join(missing_pins))
    props.sort(key=lambda p: (PINNED.index(p["slug"]) if p["slug"] in PINNED
                              else len(PINNED), -p["popularity"], p["title"]))

    # ---- satellites: close-ups and rabbit holes (CLU-30, CLU-29) --------
    # A row may point at another list. Two keys rather than one key plus a
    # type flag, because the direction decides both the glyph the row wears
    # and whether ticking rolls through — and because the build validates
    # them differently:
    #
    #   into:   "<slug>"   the same thing at finer grain. Rolls up BOTH ways.
    #   beside: "<slug>"   adjacent material. Never rolls up.
    #
    # `satellite: true` lives on the TARGET property, never on the link: the
    # link says where to go, the target says whether it is browsable. That is
    # what lets a hub row point at `kubrick`, which stays in the switcher,
    # with the identical field that points at a season page, which does not.
    byslug = {p["slug"]: p for p in props}

    def rows_of(p):
        return [x for sec in p.get("sections", []) for x in sec.get("items", [])]

    def retotal(p):
        """`w` may have just been derived, so the weight total is restated."""
        items = rows_of(p)
        ws = [x["w"] for x in items
              if isinstance(x.get("w"), (int, float)) and not isinstance(x.get("w"), bool)
              and x["w"] >= 0]
        p["_totalw"] = (round(sum(ws), 2)
                        if items and len(ws) == len(items) else None)

    roll = {}
    unresolved = []
    for p in props:
        if p.get("secret") or p.get("generate"):
            continue
        # ---- is this a hub? (CLU-79) -----------------------------------
        # A HUB IS A PROPERTY WHOSE EVERY ROW IS A DOOR — into or beside.
        # Nothing else: not a name, not a hand-set flag, not a row count.
        # Derived here rather than authored because a hand-written flag would
        # go on being true the day somebody adds a plain row, and then the
        # page would still be promising fifteen doors while holding fourteen.
        #
        # Read BEFORE the loop below strips a pointer with no target file
        # yet: a hub written months ahead of its targets is still a hub, and
        # a list should not fold and unfold as its neighbours land.
        rws = rows_of(p)
        # ---- is this a MEGA LIST? (CLU-508) -----------------------------
        # Nathan: "lets make a mega list section on the main page that takes all
        # of the mega lists (directors, mcu anthology, marvel comics, dc
        # anthology etc, (stuff that has close ups or will have close ups)) and
        # put them in their own section instead of the catalog list before".
        #
        # Note "or WILL have close ups". A hub — every row a door — is a mega
        # list by construction, and `directors` is the only one today. The other
        # five are anthologies whose rows are whole shows that have not been
        # spawned yet, and they are mega lists now rather than on the day the
        # spawning finishes. So the flag is DECLARED on the property, the way
        # `satellite` is, and a hub gets it for free.
        p["_mega"] = bool(p.get("mega"))
        p["_hub"] = bool(rws) and all(x.get("into") or x.get("beside")
                                      for x in rws)

        hub_w, hub_flat = [], []
        for x in rows_of(p):
            into, beside = x.get("into"), x.get("beside")
            if into and beside:
                fail("%s: row %r carries both `into` and `beside` — a row is "
                     "either the same thing magnified or adjacent material, "
                     "never both" % (p["slug"], x["id"]))
            ptr = into or beside
            if ptr is None:
                continue
            key = "into" if into else "beside"
            if not isinstance(ptr, str):
                fail("%s: row %r has a non-string `%s`" % (p["slug"], x["id"], key))
            if ptr == p["slug"]:
                fail("%s: row %r points at its own list" % (p["slug"], x["id"]))
            tgt = byslug.get(ptr)
            if tgt is None:
                # A dead door never ships. The pointer is stripped and the row
                # renders as its plain facts, so a hub can be written months
                # before its targets exist and each new file turns a chip on
                # at the next build with no edit to the hub.
                unresolved.append((p["slug"], x["id"], ptr))
                x.pop(key, None)
                continue
            if tgt.get("secret"):
                fail("%s: row %r points at %r, which is password-gated — a "
                     "chip on it would tell everyone the list exists"
                     % (p["slug"], x["id"], ptr))

            if key == "beside":
                # CLU-169. A rabbit hole is FOR adjacent material, and a
                # thorough parent already tends to carry some of it — so the
                # overlap is easy to reintroduce and has to be impossible
                # rather than fixed once. Ticking both surfaces would count
                # one work twice and move the reader's finish date for it.
                mine = {y["id"] for y in rows_of(p)}
                dup = sorted(mine & {y["id"] for y in rows_of(tgt)})
                if dup:
                    fail("%s: the rabbit hole on row %r points at %r, which "
                         "repeats %d row(s) the parent already carries: %s — "
                         "a reader ticking both surfaces is counted twice"
                         % (p["slug"], x["id"], ptr, len(dup),
                            ", ".join(dup[:6])))
                continue

            # a close-up: the target learns its parent from the derived map
            # rather than naming it back, so the fact is authored once
            if ptr in roll:
                fail("%s: %r is already the close-up of %s row %r — a list "
                     "can hang under one row only, or a tick would roll into "
                     "two places" % (p["slug"], ptr, roll[ptr][0], roll[ptr][1]))
            # The page needs the exact set that counts, not a count: it ticks
            # them on the way down and tests them on the way up, and it cannot
            # tell an `opt` row from GWIX.rows. Completion means every
            # non-optional row — making the optional ones mandatory would
            # contradict the word.
            need = [y["id"] for sec_ in tgt.get("sections", [])
                    for y in sec_.get("items", []) if not y.get("opt")]
            if not need:
                fail("%s: row %r opens %r, which has no non-optional rows — "
                     "nothing could ever complete it, so the roll-up would "
                     "never fire" % (p["slug"], x["id"], ptr))
            roll[ptr] = [p["slug"], x["id"], need]

            # Weights are the target's real hours, summed here, never typed:
            # a hand-written number rots the day the target gains a row.
            if "w" in x:
                fail("%s: row %r carries both `into` and a typed `w` — a "
                     "close-up's weight is its target's own hours, summed by "
                     "the build" % (p["slug"], x["id"]))
            if tgt.get("_totalw"):
                x["w"] = tgt["_totalw"]
                hub_w.append(x["id"])
            else:
                hub_flat.append((x["id"], ptr))

        # The test is the LIST's weighting, not just the other doors': a hub
        # of one weighted row and one unweighted door has the same problem as
        # a hub of two doors. Anything with a real weight beside a row of
        # unknown size makes the strip lie about proportion.
        anyw = any(isinstance(y.get("w"), (int, float))
                   and not isinstance(y.get("w"), bool) for y in rows_of(p))
        if hub_flat and (hub_w or anyw):
            # The template's weight fallback is per-property and all-or-
            # nothing, so it cannot rescue one row: an unweighted row would
            # draw as a default-sized mark beside a genuinely 88-hour one and
            # the strip would be quietly lying about proportion.
            fail("%s: %s open list(s) that carry no runtimes at all, on a "
                 "list whose other rows are weighted. A weighted strip cannot "
                 "carry an unweighted row — it would draw as a default-sized "
                 "mark beside a real one. Give the target runtimes, or drop "
                 "the row and say why in the list's notes."
                 % (p["slug"], ", ".join("%s -> %s" % t for t in hub_flat[:4])))
        if hub_w or hub_flat:
            retotal(p)

    if unresolved:
        print("  satellites: %d pointer(s) with no target file yet — the row "
              "ships as plain facts and the chip turns on when the file lands:"
              % len(unresolved))
        for sl, rid, ptr in unresolved[:12]:
            print("      %s / %s -> %s.json" % (sl, rid, ptr))
    if roll:
        print("  satellites: %d close-up(s) resolved" % len(roll))

    # CLU-508. Which lists are hubs, counted from the doors that actually
    # resolved. The build has always known this and always thrown it away, so
    # the page had no way to tell a hub from any other list — which the mega
    # list section needs, and so does ranking a hub above its own children in
    # search (CLU-509). Derived, never typed: a hub that gains a door gains the
    # count at the next build with no edit anywhere.
    doors = {}
    for _tgt, _r in roll.items():
        doors[_r[0]] = doors.get(_r[0], 0) + 1

    # ---- hubs, and what is missing from them (CLU-79) -------------------
    # Nathan: "make sure when adding new stuff that fits in any of these mega
    # lists is added to them." The step that does it is in
    # .claude/agents/property-builder.md, where the lists get built; this is
    # the net under that step, because a rule only obeyed by a person who
    # remembers it is a rule that lapses.
    #
    # "Belongs" has to be mechanical, or the line is a guess — and a guess
    # that names innocent lists every build is a line nobody reads by the
    # third week. So: one narrow rule per hub, and a hub with no honest rule
    # prints its own line and nothing else.
    #
    # Directors' rule is the property's own subtitle saying what one filmmaker
    # directed. Across today's 210 lists that phrasing appears on 20 and all
    # 20 are a single filmmaker's filmography, so it names nobody innocent.
    # It is deliberately incomplete in the other direction — kubrick,
    # tarantino, kurosawa, david-lynch and coen-brothers each word their
    # subtitle differently and this cannot see them — which is why it is a
    # hint printed under a hub and never a build failure.
    HUB_BELONGS = {
        "directors": ("a subtitle saying what one filmmaker directed",
                      lambda q: bool(re.search(r"\bdirect(?:ed|s)\b",
                                               q.get("subtitle") or ""))
                      and bool(re.search(r"film|anime",
                                         (q.get("kind") or "").lower()))),
        # CLU-480. Same shape, same limits: a comics list that names Marvel in
        # its own subtitle. Across today's 230 lists that matches 5 and all 5
        # are already doors on the shelf, so it names nobody innocent. It is
        # deliberately blind in the other direction — Thor, Venom, Ultimate
        # Marvel and Spider-Man After Civil War word their subtitles without
        # the publisher and this cannot see them — which is why it is a hint
        # printed under a hub and never a build failure.
        "marvel-comics": ("a comics subtitle that names Marvel",
                          lambda q: bool(re.search(r"\bMarvel\b",
                                                   q.get("subtitle") or ""))
                          and "comic" in (q.get("kind") or "").lower()),
    }
    for p in props:
        if not p.get("_hub"):
            continue
        # `hubdoors`, NOT `doors`: the CLU-508 block above binds `doors` to a
        # dict of hub -> count that the manifest reads further down, and reusing
        # the name here silently replaced it with a set. The build died on
        # `'set' object has no attribute 'get'` — loudly, which is the only
        # reason this cost minutes rather than a wrong manifest.
        hubdoors = {x.get("into") or x.get("beside") for x in rows_of(p)}
        print("  hub: %s — %d rows, every one a door, so its sections ship "
              "open" % (p["slug"], len(rows_of(p))))
        rule = HUB_BELONGS.get(p["slug"])
        if rule is None:
            continue
        want, belongs = rule
        absent = sorted(q["slug"] for q in props
                        if q["slug"] != p["slug"] and not q.get("secret")
                        and q["slug"] not in hubdoors and belongs(q))
        if absent:
            print("      %d list(s) carry %s and have no row here: %s"
                  % (len(absent), want, ", ".join(absent)))

    # medium tags for the search chips and the card wall — derived from the
    # kind string plus the unit, so mixed-media pages (MCU: films & shows)
    # surface under every medium they contain
    def media_of(p):
        k = (p.get("kind") or "").lower()
        u = (p.get("unit") or {}).get("one", "")
        m = set()
        if "film" in k or "movie" in k:
            m.add("movies")
        if re.search(r"\btv\b|show|series|episode", k):
            m.add("tv")
        if "anime" in k:
            m.add("anime")
        if "manga" in k or u == "chapter":
            m.add("manga")
        if "comic" in k or u == "issue":
            m.add("comics")
        if "book" in k or u in ("book", "novel"):
            m.add("books")
        if "game" in k:
            m.add("games")
        return sorted(m or {"other"})

    MEDIA_FIX = {"nasuverse": ["anime", "games", "manga", "movies"],
                 "bottle-episodes": ["tv"]}

    manifest = [
        {
            "slug": p["slug"],
            "media": MEDIA_FIX.get(p["slug"], media_of(p)),
            "title": p["title"],
            "subtitle": p.get("subtitle", ""),
            "kind": p.get("kind", ""),
            "year": p.get("year", ""),
            # carried through so the number that produced this order is
            # readable in the artifact it produced, and so a future "most
            # popular first" control needs no second build change
            "popularity": p["popularity"],
            "blurb": p.get("blurb", ""),
            "accent": p.get("accent", ""),
            "accentDark": p.get("accentDark", ""),
            "unit": p["unit"],
            # home says what the reader actually did — "played 3 today" on a
            # games list, not "ticked". Only the past tense travels; the other
            # two forms are read from the property itself, which home never
            # loads. Omitted where it is the "done" default so the manifest
            # does not grow 145 identical strings.
            **({"vpast": p["verb"]["past"]}
               if (p.get("verb") or {}).get("past", "done") != "done" else {}),
            "total": p["_total"],
            # present only on a fully weighted list — its absence is what
            # tells the front end to fall back to counting rows
            **({"totalw": p["_totalw"]} if p.get("_totalw") else {}),
            # home ranks schedule-active clubs first; the flag is all it needs
            **({"scheduled": True} if p.get("schedule") else {}),
            # how many rows open another list in full. Absent rather than 0 on
            # the 226 lists that have none, so the flag reads as a fact about
            # this list rather than a column of zeroes.
            **({"doors": doors[p["slug"]]} if doors.get(p["slug"]) else {}),
            # a satellite is UNLISTED, not hidden: it leaves the browsing
            # surfaces and its rows stay in search, so the honest way to find
            # one is to search for something inside it. The shelf keeps it —
            # filtering it out of there would strand a list you had been
            # ticking for a week with no door back to it.
            **({"satellite": True} if p.get("satellite") else {}),
            # grab-bag lists welcome a random pick; everything else is
            # ordered and only ever offers its next unticked item
            **({"random": True} if p.get("random") else {}),
            # CLU-79. Derived above, never authored — every row is a door.
            # It rides in the manifest rather than the property file because
            # the manifest is inlined in index.html and therefore in hand
            # before the first section is drawn: the page needs to know
            # whether to render the sections open, not to open them after.
            **({"hub": True} if p.get("_hub") else {}),
            # a hub is a mega list by construction; the rest say so themselves
            **({"mega": True} if (p.get("_mega") or p.get("_hub")) else {}),
            # the page needs these before first paint: one to know not to list
            # a locked property, the other to size a generated one
            # the switcher names a locked list by its cover title, not its own
            **({"secret": {"title": p["secret"].get("title", "Secret")}}
               if p.get("secret") else {}),
            **({"generate": p["generate"]} if p.get("generate") else {}),
        }
        for p in props
    ]

    with MANIFEST.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    # ---- the row index: one file powering global search and cross-list ----
    # tick sync. rows: [slug, id, title, n] for every visible property.
    # sync groups: film-kind rows (n = a plain year) that share a normalized
    # title+year across DIFFERENT lists — Dr. Strangelove on Kubrick,
    # Criterion and Best Picture is one group. Exact matches only.
    import unicodedata as _ud

    def _normt(t):
        t = _ud.normalize("NFKD", t)
        t = "".join(c for c in t if not _ud.combining(c)).lower()
        t = re.sub(r"[^a-z0-9]+", " ", t).strip()
        return re.sub(r"^(the|a|an) ", "", t)

    # A film's identity for sync is title+year, but plenty of lists number
    # their rows by something else: Criterion by spine (#700), Sight & Sound
    # by rank. Those 1,500-odd rows could never match anything, so ticking
    # Fantastic Mr. Fox on Wes Anderson left the Criterion copy untouched.
    # Both carry the year in the note, so fall back to it — but ONLY when the
    # note names exactly one year. A note with none (a box set) or several is
    # ambiguous, and a wrong year here would silently tick the wrong film.
    def _year_of(x, n):
        if re.fullmatch(r"(18|19|20)\d{2}", n):
            return n
        explicit = str(x.get("y", ""))
        if re.fullmatch(r"(18|19|20)\d{2}", explicit):
            return explicit
        found = set(re.findall(r"\b((?:18|19|20)\d{2})\b", x.get("note") or ""))
        return found.pop() if len(found) == 1 else None

    # `alias` collects key-pairs a single row proves are the same work — see
    # the merge below the loop.
    rows, groups, alias = [], {}, []
    for p in props:
        if p.get("secret"):
            continue
        # Films AND games. Sync was film-only, so a game on two lists never
        # matched — FPS canon overlaps Halo, Half-Life and Bond games, and
        # Lego Star Wars sits on two lists, none of which synced (CLU-179).
        # A game re-released under the same name in the same year is the
        # risk here, which films do not have; the shipped overlaps were
        # checked by hand and are all the same work.
        kind = p.get("kind") or ""
        # Films AND games sync, but never with EACH OTHER. Quantum of Solace
        # is a 2008 film and a 2008 game, Goldeneye is a film and a game —
        # same title, same year, different works, and syncing them would tick
        # a game you have not played. The medium rides in the group key so the
        # whole class of collision is impossible rather than hand-excluded.
        #
        # Two more things deliberately DO NOT sync, ruled by Nathan (CLU-180)
        # — do not "fix" either of these later:
        #
        #   An adaptation is not the work it adapts. `Christine (1983)` is a
        #   film on the Carpenter list and a novel on the Stephen King list.
        #   Watching the film must never tick the book. This will recur as the
        #   catalogue grows — every King adaptation, Dune, Middle-earth — and
        #   the answer is the same each time.
        #
        #   A riff is not the film it riffs. Thirteen MST3K episodes share a
        #   title and year with the films they play. Watching Manos with a
        #   robot silhouette in front of it is a different sitting from
        #   watching Manos, and the two lists count different things.
        #
        # Both fall out of the medium key already (books and tv are not
        # syncable kinds), so nothing enforces them beyond this comment and
        # the gate below. If sync is ever widened past films and games, these
        # two cases are the reason to widen it carefully.
        # A list can be honestly BOTH mediums — the-matrix is films and
        # games — and then the property kind cannot answer for a single
        # row. Deriving one letter from it filed that list's four films
        # in the game lane, where no film list could ever reach them, and
        # five exact title+year matches with the Wachowskis list silently
        # failed to pair. So a row may declare its own medium as "m", and
        # the kind is only the fallback — it stays untouched because it is
        # also the copy printed on the card wall and in search.
        prop_medium = "g" if "game" in kind else "f"
        syncable = "film" in kind or "game" in kind
        for s in p.get("sections", []):
            for x in s.get("items", []):
                n = str(x.get("n", ""))
                row = [p["slug"], x["id"], x["t"], n]
                # the fifth slot is this row's hours, and it only exists on a
                # fully weighted list — ~44KB across the catalogue, on a file
                # home already fetches
                if p.get("_totalw"):
                    row.append(x.get("w"))
                rows.append(row)
                if syncable:
                    rm = x.get("m")
                    assert rm is None or rm in ("f", "g"), (
                        "%s item %s: medium %r must be 'f' or 'g'"
                        % (p["slug"], x["id"], rm))
                    medium = rm or prop_medium
                    keys = []
                    y = _year_of(x, n)
                    if y:
                        keys.append(_normt(x["t"]) + "|" + y + "|" + medium)
                    # A canonical work id, where the generator could resolve
                    # one from its OWN source's link (CLU-191). It pairs rows
                    # title+year cannot: Casablanca is 1943 on Best Picture and
                    # 1942 on Criterion, and neither list is wrong — one cites
                    # the premiere, the other the general release. A rule of
                    # the form "subtract a year" fixes none of it, because
                    # different pairs disagree in different directions.
                    q = x.get("q")
                    if isinstance(q, str) and re.fullmatch(r"Q[1-9]\d*", q):
                        keys.append(q + "|" + medium)
                    for k in keys:
                        groups.setdefault(k, []).append([p["slug"], x["id"]])
                    if len(keys) > 1:
                        alias.append(keys)

    # A row carrying both kinds of key proves those keys name one work, so the
    # keys merge. That is what lets a list that HAS ids pair with a list that
    # does not — they meet through the row they share — and it is why this can
    # roll out one generator at a time instead of all at once.
    parent = {}

    def find(k):
        parent.setdefault(k, k)
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    for ks in alias:
        for k in ks[1:]:
            a, b = find(ks[0]), find(k)
            if a != b:
                parent[a] = b

    merged = {}
    for k, v in groups.items():
        m = merged.setdefault(find(k), {"keys": [], "rows": []})
        m["keys"].append(k)
        m["rows"] += v

    sync = {}
    for m in merged.values():
        seen, rws = set(), []
        for s, i in m["rows"]:
            if (s, i) not in seen:
                seen.add((s, i))
                rws.append([s, i])
        if len({s for s, _ in rws}) > 1:
            # Name the group by its id when it has one: a title+year key stops
            # being true the day either list re-dates the film, and the key is
            # what the one-time backfill hashes.
            ks = sorted(m["keys"])
            sync[next((k for k in ks if k[0] == "Q"), ks[0])] = rws
    # ---- watch prerequisites (CLU-373) --------------------------------
    # A run is an ordered list of STEPS; a row is offerable when every step
    # before its own has a ticked row. Steps rather than rows because one
    # work can sit on several lists and sync ties their ticks together.
    #
    # Resolved HERE because only the build sees the whole catalogue: a
    # Wikidata step expands to every list carrying that work, so a run
    # written once covers all of them — which is the only way the
    # cross-list case can work.
    have = {}
    for p_ in props:
        if p_.get("secret"):
            continue
        for s_ in p_.get("sections", []):
            for x in s_.get("items", []):
                have[p_["slug"] + "|" + x["id"]] = True
    byq = {}
    for k, v in groups.items():
        if k[0] == "Q":
            for sl, i in v:
                byq.setdefault(k.split("|")[0], set()).add(sl + "|" + i)

    seq = []
    seqf = ROOT / "tools" / "data" / "sequences.json"
    if seqf.exists():
        reg = json.loads(seqf.read_text(encoding="utf-8"))
        for r in reg.get("runs", []):
            steps = []
            for step in r["run"]:
                # A step may be one entry or several: several because the same
                # work sits on several lists and any copy counts as watched.
                rws = []
                for one in (step if isinstance(step, list) else [step]):
                    if re.fullmatch(r"Q[1-9]\d*", one):
                        rws += sorted(byq.get(one, ()))
                    else:
                        # A literal row. Fail loudly: a typo here would
                        # silently gate nothing, which is invisible and
                        # permanent.
                        if one not in have:
                            fail("sequences.json: run %r names %r, which is "
                                 "not a row in the catalogue"
                                 % (r.get("name"), one))
                        rws.append(one)
                rws = sorted(set(rws))
                if rws:
                    steps.append(rws)
            # a run of one step gates nothing; drop it rather than ship it
            if len(steps) > 1:
                seq.append(steps)
        print("  prerequisites: %d run(s) over %d step(s), %d row(s) gated"
              % (len(seq), sum(len(r) for r in seq),
                 sum(len(st) for r in seq for st in r[1:])))

    with (PROPS / "search.json").open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"rows": rows, "sync": sync, "seq": seq,
                            "roll": roll},
                           separators=(",", ":"), ensure_ascii=False) + "\n")
    print("  search index: %d rows, %d sync groups spanning %d lists"
          % (len(rows), len(sync),
             len({s for v in sync.values() for s, _ in v})))

    # The page's one-time cross-list backfill is keyed on this. Deriving it
    # from the sync map's own content means any build that adds, removes or
    # rewires a group re-runs that pass for everyone, so a newly added list
    # inherits ticks people already had on the list it pairs with. The key
    # used to be a version string bumped by hand, and that broke the first
    # time it mattered: Mission: Impossible shipped with eight verified groups
    # against Tom Cruise and no bump, so ticks made before it existed never
    # travelled (CLU-247). Adding a list is the common case; remembering to
    # edit a string in a different file was not.
    syncver = hashlib.sha1(
        json.dumps(sync, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False).encode("utf-8")).hexdigest()[:10]

    # the share pages, and the proof that the gated list has none — before
    # index.html is written, so a failed proof leaves the page as it was
    check_embeds(props, write_embeds(props))

    html = TEMPLATE.read_text(encoding="utf-8")
    for ph in ("__MANIFEST__", "__BUILD__", "__SYNCVER__", "__CSP__"):
        if ph not in html:
            fail("template.html is missing the %s placeholder" % ph)

    # the manifest is small and needed before first paint, so it is inlined;
    # the property bodies are not
    html = html.replace("__MANIFEST__", json.dumps(manifest, indent=2, ensure_ascii=False))
    # before the stamp below, so the page's content hash covers it
    html = html.replace("__SYNCVER__", syncver)

    # A content hash of everything that ends up in the page. GitHub Pages serves
    # index.html with a cache lifetime, so a browser can go on running an old
    # copy after a deploy. The page checks this against build.json and reloads
    # itself once if they differ, which is what saves anyone hard-refreshing.
    # Newlines are normalised before hashing, and that is load-bearing rather
    # than tidy. `.gitattributes` stores these files with LF and hands a
    # checkout whatever the platform wants, and a generator that writes with
    # write_text() and no newline= lands CRLF on Windows. Either way git calls
    # the file clean while the raw bytes differ from the ones CI reads, so a
    # stamp over read_bytes() came out different on the two machines and the
    # "committed build is current" check failed on every single push for
    # thirteen days — from 2026-08-28, when directors.json was first generated,
    # until this line. Pages deployed the whole time, which is why nothing said
    # so. The stamp must depend on the CONTENT of the catalogue and on nothing
    # about the machine that built it.
    stamp = hashlib.sha1(html.encode("utf-8"))
    for f in files:
        stamp.update(f.read_bytes().replace(b"\r\n", b"\n"))
    build = stamp.hexdigest()[:12]

    html = html.replace("__BUILD__", build)

    # CLU-548, and it has to be last: the policy carries a sha256 of the inline
    # <script>, and that block holds the build stamp, so hashing it before the
    # line above would pin a hash of a page that was never served. The stamp in
    # turn is computed over the page while __CSP__ is still a placeholder,
    # which is what keeps the two out of each other's way — neither depends on
    # the other's output.
    policy = app_policy(html)
    if html.count("__CSP__") != 1:
        # it was 2 for one build: the comment above the placeholder named it,
        # and str.replace put a whole second policy inside that comment
        fail("csp: __CSP__ appears %d times in the template; it must appear "
             "exactly once, and nothing may name it in prose"
             % html.count("__CSP__"))
    html = html.replace("__CSP__", csp_meta(policy))
    for ph in ("__MANIFEST__", "__BUILD__", "__SYNCVER__", "__CSP__"):
        if ph in html:
            fail("%s was not replaced" % ph)

    with OUTPUT.open("w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    with BUILDFILE.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"build": build}) + "\n")

    print("wrote index.html, properties/index.json and build.json")
    print("  build %s" % build)
    print("  csp: %d directives, hashes over 1 inline script + 1 inline style"
          % len(policy))
    print("  catalogue: popularity desc, pinned to the head: %s"
          % ", ".join(PINNED))
    for i, p in enumerate(props, 1):
        print("  %3d. %-22s pop %3d  %4d %-9s %s%s"
              % (i, p["slug"], p["popularity"], p["_total"], p["unit"]["many"],
                 "pinned " if p["slug"] in PINNED else "",
                 "scheduled" if p.get("schedule") else ""))


if __name__ == "__main__":
    main()
