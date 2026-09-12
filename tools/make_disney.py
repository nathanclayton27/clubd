#!/usr/bin/env python3
"""Generate properties/disney.json.

    python3 tools/make_disney.py

Every Disney film in release order — theatrical, television and direct-to-video
— with the acquired properties left out: no Star Wars, no Marvel, no Pixar, no
20th Century, no Muppets. Walt Disney Pictures, Disney Channel and Disneytoon
are the studio's own output, and that is what "a Disney movie" means here.

Sources, machine-read into tools/data/disney.json:
  - List of Walt Disney Pictures films          theatrical
  - List of Disney Channel original films       television
  - List of Disneytoon Studios productions      direct-to-video
with runtimes from Wikidata (P2047). Where the same film appears on two lists,
Disneytoon's word wins on how it was released — the Walt Disney Pictures list
files Bambi II as theatrical because it had a cinema release outside North
America, and the studio that made it is the better authority. Disneytoon's own
Release-type cell can name two channels — "Direct-to-video/Theatrical" — and
where it does, the direct-to-video half wins. Three rows read that way (Bambi
II, Tinker Bell, and Mickey, Donald, Goofy: The Three Musketeers), and a
substring test filed all three as theatrical, which left Bambi II at tier 1
while the channel note below named it as a direct-to-video example (CLU-306).

**The same title is not the same film.** Rows are deduplicated on title AND
year, not on title alone. On the title alone, first one wins, so the 1992
Aladdin shadowed the 2019 one and all nineteen live-action remakes were absent
from a list whose Revival note advertises them (CLU-303). Every genuine
cross-source duplicate in this data shares a release date, so the year tells a
remake from a duplicate — and the year rather than the full date because the
Disney Channel list gives The Cheetah Girls 2 two different 2006 dates.

**Distributed is not made.** The Walt Disney Pictures list carries a Notes
column, and it says so when Disney only handled distribution — Ponyo's reads
"North American distribution only; produced by Studio Ghibli". Twenty-three
rows carry that marker in one wording or another and none of them belong on a
list of what Disney made; a reader found two Studio Ghibli films here and was
right. DISTONLY below reads the column the parse used to ignore. It does NOT
replace the acquired-properties blocklist: of the 38 titles that blocklist
removes, the marker catches exactly one (Toy Story, which Disney did only
distribute). The other 37 are co-productions — the source calls them
"co-production with Pixar Animation Studios" — so the marker is silent on them
and the blocklist stays.

The blocklist matches names, which makes a one-word Pixar title dangerous. Two
of them, matched on word boundaries, were removing five of Disney's own films:
"Up" took Honey, I Blew Up the Kid, Up, Up, and Away, Gotta Kick It Up! and
Growing Up Wild, and "Soul" took America's Heart and Soul (CLU-305). Those two
now have to match a whole title. The same shape of risk remains for Cars,
Brave, Coco and Luca, which are still word-boundary patterns because they have
sequels to catch; no title in the current source trips them.

Tiers are release channels, not rankings:
  1 theatrical   2 television   3 direct-to-video
A finish date paces you through the theatrical line; the checkbox adds the
rest. The channels are also filter chips, so "no TV movies" is one click.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop as gwprop  # noqa: E402

SLUG = "disney"
ROOT = pathlib.Path(__file__).resolve().parent.parent

# The source's own marker for a film Disney released but did not make. Every
# wording in the article ends the same way — "distribution only" — after a
# territory that varies: "North American", "international", "Benelux",
# "U.S., Scandinavian, Australian and New Zealand", or nothing at all.
DISTONLY = re.compile(r"distribution only", re.I)

# Rows the old parse invented and shipped, kept here by name so that dropping
# them cannot be mistaken for an id rename. Each is a production company or a
# streaming service read out of a Notes cell: the row was one cell short — the
# "In development" table has no date column, and elsewhere the date is carried
# by a rowspan — so the parse read the title cell as the date and the notes
# cell as the title. scratch/agent-disney/parse.py now rejects a row whose
# first cell is not a real date.
PHANTOM = {
    "dis-1997-agbo": "notes of the in-development Hercules remake",
    "dis-2007-centro-digital-pictures-limited":
        "notes of The Secret of the Magic Gourd",
    "dis-2019-disney": "notes of Noelle — the Disney+ row",
}

KIND = {
    "theatrical": (1, "Theatrical", []),
    "television": (2, "Television", ["TV movie"]),
    "direct-to-video": (3, "Direct-to-video", ["Direct-to-video"]),
}

ERAS = [
    ("walt", "Walt's era", 0, 1966,
     "Snow White to The Jungle Book — the films made while Walt Disney was "
     "alive, which is the canon the studio still measures itself against."),
    ("after", "After Walt", 1967, 1988,
     "The studio wobbles for twenty years: live-action comedies, the scruffy "
     "seventies animation, and the beginnings of the Disney Channel."),
    ("renaissance", "The Renaissance", 1989, 1999,
     "The Little Mermaid through Tarzan, and alongside it the first wave of "
     "direct-to-video sequels and Disney Channel movies."),
    ("aughts", "The two thousands", 2000, 2009,
     "The sequel factory at full tilt, the DCOM golden age, and the slow slide "
     "of hand-drawn animation."),
    ("revival", "The Revival", 2010, 2019,
     "Tangled, Frozen, Moana — and the live-action remakes begin."),
    ("plus", "The Disney+ era", 2020, 9999,
     "Streaming first, cinemas second, and the remakes keep coming."),
]


def slug(t):
    """Deliberately NOT gwlib.prop.slug. That one ASCII-folds, which would
    rewrite `dis-2004-the-lion-king-1½` and `dis-2008-high-school-musical-el-
    desafío` — two live ids whose ticks would vanish with them."""
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def item_id(f):
    return "dis-%s-%s" % (f["date"][:4], slug(f["t"]))


def shipped_ids():
    """Item ids in the property as it stands on disk, so the write can prove it
    renamed none of them. Empty on a first build."""
    p = ROOT / "properties" / ("%s.json" % SLUG)
    if not p.exists():
        return set()
    old = json.loads(p.read_text(encoding="utf-8"))
    return {x["id"] for s in old.get("sections", []) for x in s["items"]}


def main():
    data = ROOT / "tools" / "data" / ("%s.json" % SLUG)
    allfilms = json.loads(data.read_text(encoding="utf-8"))

    # Nathan's ruling on CLU-274: keep the list's stated rule and drop the rows
    # that break it. The source marks them; we used to ignore the column.
    dropped = [f for f in allfilms if DISTONLY.search(f.get("note") or "")]
    films = [f for f in allfilms if f not in dropped]
    assert dropped, "no distribution-only markers found — did the notes column "\
                    "stop being parsed?"

    films.sort(key=lambda f: (f["date"], f["t"]))

    sections = []
    for key, title, lo, hi, intro in ERAS:
        got = [f for f in films if lo <= int(f["date"][:4]) <= hi]
        if not got:
            continue
        items = []
        for f in got:
            tier, label, tags = KIND[f["kind"]]
            bits = list(tags)
            if not f.get("runtime") and int(f["date"][:4]) > 2025:
                bits.append("Not out yet")
            items.append({
                "id": item_id(f),
                "t": f["t"], "n": f["date"][:4],
                "w": round((f.get("runtime") or 0) / 60.0, 2),
                "tier": tier,
                "tags": [label],
                **({"note": " · ".join(bits)} if bits else {}),
            })
        counts = {}
        for f in got:
            counts[f["kind"]] = counts.get(f["kind"], 0) + 1
        parts = ["%d theatrical" % counts.get("theatrical", 0),
                 "%d TV" % counts["television"] if counts.get("television") else "",
                 "%d direct-to-video" % counts["direct-to-video"]
                 if counts.get("direct-to-video") else ""]
        sec = {"id": key, "title": title,
               "sub": "%d–%d · %s · %d hours"
                      % (int(got[0]["date"][:4]), int(got[-1]["date"][:4]),
                         ", ".join(p for p in parts if p),
                         round(sum(f.get("runtime") or 0 for f in got) / 60.0)),
               "intro": intro, "items": items}
        if key == "walt":
            sec["open"] = True
        assert all(a["n"] <= b["n"] for a, b in zip(sec["items"], sec["items"][1:])), \
            "%s out of order" % title
        sections.append(sec)

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(films), (len(ids), len(films))

    # Every id the property carries today must survive, except the ones this
    # build removes on purpose. prop.write() raises on any other loss.
    legacy = shipped_ids() - {item_id(f) for f in dropped} - set(PHANTOM)

    n = {}
    for f in films:
        n[f["kind"]] = n.get(f["kind"], 0) + 1
    hours = sum(f.get("runtime") or 0 for f in films) / 60.0
    nort = sum(1 for f in films if not f.get("runtime"))

    p = {
        "slug": SLUG,
        "title": "Disney",
        "subtitle": "the studio's own films, in release order",
        "kind": "films",
        "popularity": 96,
        "year": "1937–",
        "blurb": "%d films from Snow White on — %d theatrical, %d television, "
                 "%d direct-to-video — about %d hours."
                 % (len(films), n["theatrical"], n["television"],
                    n["direct-to-video"], round(hours)),
        "unit": {"one": "film", "many": "films"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "itemOrder": "number-first",
        "accent": "#1F4FA8",
        "accentDark": "#6F9BE8",
        "tiers": True,
        "random": True,
        "itemTiers": True,
        "paceTiers": [1],
        "paceLabel": "the TV movies and direct-to-video sequels",
        "filter": {
            "key": "channel", "label": "Show", "mode": "exclude",
            "values": ["Theatrical", "Television", "Direct-to-video"],
        },
        "notes": [
            # First, because it is the question a reader asks first — someone
            # went looking for Toy Story, did not find it, and had to reach
            # the second note to learn why.
            ["This is what Disney itself made.", "No acquired properties: no "
             "Star Wars, no Marvel, no Pixar, no 20th Century, no Muppets. "
             "Those are their own studios, and several have their own lists "
             "here. Nor anything Disney only released for somebody else — the "
             "source marks those in its notes column and %d films drop out on "
             "it, Ponyo and The Secret World of Arrietty among them. What is "
             "left is Walt Disney Pictures, Disney Channel and Disneytoon."
             % len(dropped)],
            ["Tiers are release channels, not rankings.", "1 is theatrical, 2 is "
             "television, 3 is direct-to-video. A finish date paces you through "
             "the theatrical line — %d films — and the checkbox under the bar "
             "adds the other two. The chips at the top hide a channel entirely."
             % n["theatrical"]],
            ["Where a film sits on two lists, the studio that made it wins.",
             "Several direct-to-video sequels had cinema releases outside North "
             "America and appear on the theatrical list because of it. Bambi II "
             "and Tarzan II are direct-to-video here because Disneytoon says so, "
             "and it made them."],
            ["Bar widths are runtimes.", "From Wikidata, for %d of the %d. The "
             "%d without one — mostly sixties and seventies live-action — weigh "
             "nothing rather than a guess." % (len(films) - nort, len(films), nort)],
            "Film lists from Wikipedia: Walt Disney Pictures films, Disney "
            "Channel original films, and Disneytoon Studios productions.",
        ],
        "sections": sections,
    }

    out = gwprop.write(p, legacy_ids=sorted(legacy))

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d films, %d hours" % (len(sections), len(ids), round(hours)))
    for s in sections:
        print("   %-20s %4d  %s" % (s["title"], len(s["items"]), s["sub"][:56]))
    print("  dropped %d distribution-only rows:" % len(dropped))
    for f in dropped:
        print("   %-44s %s  %s" % (f["t"][:44], f["date"][:4], f["note"][:58]))
    print("  legacy ids checked: %d" % len(legacy))
    print("  -> %s" % out)


if __name__ == "__main__":
    main()
