"""HowLongToBeat story hours, behind the verify-by-name gate.

The gate is the house rule that once kept a text adventure called Lost Pig
out of Metal Gear: a result only counts when its name normalizes to what
was asked for, and (when a year is given) its release year sits inside the
window. Games that fail ship unweighted with a note — never a guessed
number.

Why this module talks to the site itself
----------------------------------------
The `howlongtobeatpy` package is DEAD and must not be used. Its bundled
endpoint extractor points at /api/search, which 404s against the current
site, and it swallows the failure: every query returns None. It does not
raise. A generator built on it silently unweights an entire catalogue and
nobody notices — which is exactly what happened, twice, on the same night.
There is no fallback path to it here on purpose; `search()` below speaks the
protocol the site actually serves, and raises when it cannot.

The protocol, as of 2026-11-11 (CLU-650). Read straight out of the site's
own search provider: the Next.js chunk /_next/static/chunks/0ovmds8czs1lw.js
loaded by https://howlongtobeat.com/ (module 50286, the one holding the
string "/api/search/site"). Chunk names are content hashes and change with
every deploy; to re-find it, fetch the home page, pull each
/_next/static/chunks/*.js it lists, and grep for "/api/search/site".

  * GET  /api/search/site/init?t=<ms>  hands out {token} and nothing else.
    The rotating hpKey/hpVal pair it also handed out (still there when this
    module was last repaired, 2026-08-24) is gone.
  * POST /api/search/site  wants JSON with exactly one auth header,
    x-auth-token: <token>. No x-hp-* headers, nothing spliced into the body.
  * The body's filters are now {mode: "include", values: [...]} objects:
    searchOptions.games.platform, .year (which replaced rangeYear) and
    .gameplay.perspective/.flow/.genre (difficulty is gone). rangeTime is
    {min, max} built with parseInt, so an unset bound serializes as null.
  * 403 means the token expired: the site takes a new one from init and
    retries once. 429 means "Too many searches, please wait a minute".
  * Search terms are matched one at a time, so they must be split on
    PUNCTUATION, not whitespace: "Mega Man: Maverick Hunter X" split on
    spaces asks for a game containing the term "Man:" and finds nothing.
    (The site's own box splits on " ", which is why it misses these.)
    Found by scratch/megaman/hltb_probe.py reading the site's own Next.js
    chunks; that one fix recovered seven Mega Man rows.

Failing loudly
--------------
A dead endpoint now raises `LookupBroken` instead of returning an empty
result set. "No game by that name" and "the lookup is broken" are different
answers and a generator must never confuse them — confusing them is how a
94-game catalogue quietly lost its weights.

Self-check (run it after any change here, and whenever a build's weights
look thin):

    python tools/gwlib/hltb.py --self-check

It asks for three known things — a plain title, a title with a colon in it,
and a title that must NOT verify — and exits non-zero if any answer stops
being plausible.
"""
import json
import pathlib
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request

HLTB = "https://howlongtobeat.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")

# Terms are matched one by one, so punctuation stuck to a word kills the
# search. Latin-1/Latin Extended-A survive so accented titles keep their
# shape ("Pokémon" stays one term).
_TERMS = re.compile(r"[^0-9A-Za-zÀ-ɏ]+")


class LookupBroken(RuntimeError):
    """The HowLongToBeat endpoint changed, moved, or refused us.

    Raised instead of returning nothing, so a broken lookup fails a build
    rather than silently unweighting it. If you see this, run the self-check
    and then re-probe the site's Next.js chunks the way
    scratch/megaman/hltb_probe.py does.
    """


def _norm(t):
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    t = re.sub(r"[^a-z0-9]+", " ", t).strip()
    return re.sub(r"^(the|a|an) ", "", t)


def terms(query):
    """Search terms for `query`, split on punctuation rather than spaces."""
    return [t for t in _TERMS.split(query) if t]


class Result(object):
    """The attribute shape `story_hours` reads off a search result.

    Both prior implementations grew their own one-class adapter over the raw
    JSON; this is that class, kept here so callers stop writing it again.
    `comp_main` is seconds, exactly as the site reports it.
    """

    __slots__ = ("game_id", "game_name", "release_world", "comp_main")

    def __init__(self, d):
        self.game_id = d.get("game_id")
        self.game_name = d.get("game_name") or ""
        self.release_world = d.get("release_world")
        self.comp_main = d.get("comp_main") or 0

    def __repr__(self):
        return "<Result %s %r %s %ss>" % (self.game_id, self.game_name,
                                          self.release_world, self.comp_main)


FIELDS = ("game_id", "game_name", "release_world", "comp_main",
          "comp_plus", "comp_100")


def _request(url, data=None, headers=None, timeout=45):
    h = {"User-Agent": UA, "Referer": HLTB + "/", "Origin": HLTB,
         "accept": "*/*"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


class Session(object):
    """A live /api/search/site session: the token from /init.

    Optionally disk-caches raw rows per query, so a re-run costs nothing and
    the misses stay reviewable. One cache file per session directory, keyed
    by query string — the shape scratch/megaman/fetch_hltb.py used, which
    survives a query list growing without re-fetching what it already knows.
    """

    def __init__(self, cache_dir=None, pause=1.5):
        self.pause = pause
        self.calls = 0
        self.cache_path = None
        self.cache = {}
        if cache_dir:
            self.cache_path = pathlib.Path(cache_dir) / "hltb_raw.json"
            if self.cache_path.exists():
                self.cache = json.loads(
                    self.cache_path.read_text(encoding="utf-8"))
        self.refresh()

    def refresh(self):
        """Take a fresh token."""
        try:
            d = json.loads(_request(
                "%s/api/search/site/init?t=%d" % (HLTB, time.time() * 1000)))
        except (urllib.error.HTTPError, urllib.error.URLError, OSError,
                ValueError) as e:
            raise LookupBroken("cannot open a session with %s: %s" % (HLTB, e))
        if not isinstance(d, dict) or not d.get("token"):
            raise LookupBroken(
                "the init endpoint no longer hands out a 'token' (got %s)"
                % (sorted(d) if isinstance(d, dict) else type(d).__name__))
        self.token = d["token"]

    def _post(self, query):
        def unset():
            return {"mode": "include", "values": []}
        payload = {
            "searchType": "games", "searchTerms": terms(query),
            "searchPage": 1, "size": 20,
            "searchOptions": {
                "games": {"userId": 0, "platform": unset(),
                          "sortCategory": "popular",
                          "rangeCategory": "main",
                          "rangeTime": {"min": None, "max": None},
                          "gameplay": {"perspective": unset(),
                                       "flow": unset(), "genre": unset()},
                          "year": unset(), "modifier": ""},
                "users": {"sortCategory": "postcount"},
                "lists": {"sortCategory": "follows"},
                "filter": "", "sort": 0, "randomizer": 0},
            "useCache": True}
        headers = {"Content-Type": "application/json",
                   "x-auth-token": self.token}
        body = json.dumps(payload).encode("utf-8")
        out = json.loads(_request(HLTB + "/api/search/site", body, headers))
        if "data" not in out:
            raise LookupBroken(
                "search response has no 'data' key (got %s) — the protocol "
                "moved again" % sorted(out)[:8])
        return [{k: g.get(k) for k in FIELDS} for g in out["data"]]

    def rows(self, query, tries=4):
        """Raw row dicts for `query`, cached, retried, token refreshed."""
        if query in self.cache:
            return self.cache[query]
        last = None
        for attempt in range(tries):
            try:
                got = self._post(query)
                break
            except (urllib.error.HTTPError, urllib.error.URLError, OSError,
                    ValueError) as e:
                last = e
                # 429 is the site's "wait a minute"; a 403 (expired token)
                # or anything else is retried soon on a fresh token
                busy = getattr(e, "code", None) == 429
                time.sleep(30 if busy else 4 * (attempt + 1))
                try:
                    self.refresh()
                except LookupBroken:
                    pass
        else:
            raise LookupBroken("HowLongToBeat refused %r %d times: %s"
                               % (query, tries, last))
        self.calls += 1
        self.cache[query] = got
        if self.cache_path:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(
                json.dumps(self.cache, indent=1, ensure_ascii=False) + "\n",
                encoding="utf-8", newline="\n")
        time.sleep(self.pause)
        return got

    def search(self, query):
        """`Result` objects for `query`, ready for `story_hours`."""
        return [Result(d) for d in self.rows(query)]


_SESSION = None


def search(name, session=None):
    """`Result` objects for `name` from the live endpoint.

    Raises LookupBroken if the endpoint cannot be spoken to. An empty list
    means HowLongToBeat genuinely knows nothing by that name — which is a
    fact about the game, not about the lookup.
    """
    global _SESSION
    if session is None:
        if _SESSION is None:
            _SESSION = Session()
        session = _SESSION
    return session.search(name)


def story_hours(name, year=None, year_slack=2, results=None):
    """Main-story hours for `name`, or None with a reason.

    `results` is a list of search results (injected so callers control
    fetching/caching/retries); when omitted the live endpoint is asked.
    Returns (hours, entry, reason) where hours is None if nothing verified.
    comp_main is seconds.

    When a `year` is given, name matches are considered nearest-year-first.
    Two Bond games are both called "GoldenEye 007" (1997 and 2010) and the
    gate used to return on whichever the site listed first, rejecting the
    other as a year mismatch; scratch/bondgames/collect.py had to pre-sort
    its rows to work around it. The gate does that itself now — it still
    checks the year, it just stops picking a losing candidate on purpose.
    """
    if results is None:
        results = search(name)
    want = _norm(name)

    def named(r):
        got = _norm(getattr(r, "game_name", "") or "")
        # HLTB suffixes some DLC entries with a literal " DLC"
        return got == want or got == want + " dlc"

    hits = [r for r in results if named(r)]
    if year:
        hits.sort(key=lambda r: abs(int(getattr(r, "release_world", 0) or 0)
                                    - year))
    for r in hits:
        ry = getattr(r, "release_world", None)
        if year and ry and abs(int(ry) - year) > year_slack:
            return None, r, ("year mismatch: HLTB says %s, wanted %d"
                             % (ry, year))
        secs = getattr(r, "comp_main", 0) or 0
        if secs <= 0:
            return None, r, "verified by name but no main-story figure"
        return round(secs / 3600.0, 2), r, "ok"
    return None, None, ("no result named %r (had: %s)"
                        % (name, [getattr(r, "game_name", "?")
                                  for r in results[:4]]))


# --------------------------------------------------------------------------
# self-check
# --------------------------------------------------------------------------

# (query, year, low, high) — low/high bracket a plausible main-story figure
# generously. The point is not precision; it is that a real number comes
# back at all, and that a colon in a title still finds the game.
PROBES = [
    ("Halo: Combat Evolved", 2001, 5.0, 20.0),
    ("Mega Man: Maverick Hunter X", 2006, 2.0, 15.0),
]

# Must NOT verify: the gate has to keep refusing things that are not the game
# asked for, or every check above is meaningless.
NEGATIVE = "Zzyzx Quest Of The Nonexistent Marmot"


def self_check(verbose=True):
    """Ask for known titles and confirm plausible answers come back.

    Returns the number of failures; prints what it found. A future endpoint
    change makes this fail loudly instead of quietly unweighting a whole
    catalogue.
    """
    bad = []
    session = Session()
    for name, year, lo, hi in PROBES:
        try:
            hours, rec, why = story_hours(name, year, results=session.search(name))
        except LookupBroken as e:
            bad.append("%s: lookup broken: %s" % (name, e))
            if verbose:
                print("  FAIL %-32s lookup broken: %s" % (name, e))
            continue
        if hours is None:
            bad.append("%s: no figure (%s)" % (name, why))
        elif not lo <= hours <= hi:
            bad.append("%s: %.2f h is outside the plausible %.0f-%.0f h"
                       % (name, hours, lo, hi))
        if verbose:
            print("  %-4s %-32s %s h  (%s)"
                  % ("ok" if hours and lo <= hours <= hi else "FAIL",
                     name, hours, why))

    try:
        hours, _, why = story_hours(NEGATIVE, results=session.search(NEGATIVE))
    except LookupBroken as e:
        bad.append("negative control: lookup broken: %s" % e)
        hours, why = None, str(e)
    else:
        if hours is not None:
            bad.append("the gate accepted %r as %s h — verify-by-name is "
                       "no longer verifying" % (NEGATIVE, hours))
    if verbose:
        print("  %-4s %-32s refused (%s)"
              % ("ok" if hours is None else "FAIL", NEGATIVE[:32], why[:60]))
        print("%d live call%s, %d failure%s"
              % (session.calls, "" if session.calls == 1 else "s",
                 len(bad), "" if len(bad) == 1 else "s"))
    for b in bad:
        print("  !! %s" % b)
    return len(bad)


if __name__ == "__main__":
    if "--self-check" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(1 if self_check() else 0)
    for arg in sys.argv[1:]:
        h, rec, why = story_hours(arg)
        print("%-44s %s  (%s)" % (arg, h, why))
