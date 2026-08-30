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
import hashlib
import json
import pathlib
import re
import sys

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
            # a satellite is UNLISTED, not hidden: it leaves the browsing
            # surfaces and its rows stay in search, so the honest way to find
            # one is to search for something inside it. The shelf keeps it —
            # filtering it out of there would strand a list you had been
            # ticking for a week with no door back to it.
            **({"satellite": True} if p.get("satellite") else {}),
            # grab-bag lists welcome a random pick; everything else is
            # ordered and only ever offers its next unticked item
            **({"random": True} if p.get("random") else {}),
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

    html = TEMPLATE.read_text(encoding="utf-8")
    for ph in ("__MANIFEST__", "__BUILD__", "__SYNCVER__"):
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
    stamp = hashlib.sha1(html.encode("utf-8"))
    for f in files:
        stamp.update(f.read_bytes())
    build = stamp.hexdigest()[:12]

    html = html.replace("__BUILD__", build)
    for ph in ("__MANIFEST__", "__BUILD__", "__SYNCVER__"):
        if ph in html:
            fail("%s was not replaced" % ph)

    with OUTPUT.open("w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    with BUILDFILE.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"build": build}) + "\n")

    print("wrote index.html, properties/index.json and build.json")
    print("  build %s" % build)
    print("  catalogue: popularity desc, pinned to the head: %s"
          % ", ".join(PINNED))
    for i, p in enumerate(props, 1):
        print("  %3d. %-22s pop %3d  %4d %-9s %s%s"
              % (i, p["slug"], p["popularity"], p["_total"], p["unit"]["many"],
                 "pinned " if p["slug"] in PINNED else "",
                 "scheduled" if p.get("schedule") else ""))


if __name__ == "__main__":
    main()
