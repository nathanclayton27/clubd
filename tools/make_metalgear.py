#!/usr/bin/env python3
"""Generate properties/metal-gear.json.

    python3 tools/make_metalgear.py

Everything Metal Gear in release order: the saga, the side games, the remakes
and re-releases, and the on-paper extras.

Hours are HowLongToBeat main-story figures — story only, as asked — read from
tools/data/metalgear.json, which was collected from HLTB's own pages and
verified by name (the generator refuses a record whose name is not what it
expects). The extras that are not games weigh nothing rather than a guess.

Tiers are necessity, Kingdom Hearts style:
  1  the saga spine — skip it and something later will not land
  2  side stories that feed the saga: Ghost Babel, Portable Ops, Rising
  3  remakes, re-releases, spin-offs and extras

Two quirks worth knowing are in the notes: Ghost Babel shipped in the west
titled just "Metal Gear Solid", and the Master Collection's number is the
whole bundle, not a new game.
"""
import json
import pathlib

SLUG = "metal-gear"

# key in the data file, expected name there, tier, note, opt
ROSTER = [
    ("mg1", "Metal Gear", 1,
     "MSX2. Where sneaking starts — not the NES version.", 0),
    ("mg2", "Metal Gear 2: Solid Snake", 1,
     "MSX2, and the blueprint MGS1 rebuilds", 0),
    ("snakes-revenge", "Snake's Revenge", 3,
     "The western NES sequel, made without Kojima and outside the story — "
     "famous for goading him into making the real MG2", 1),
    ("mgs1", "Metal Gear Solid", 1, "", 0),
    ("vr", "Metal Gear Solid: VR Missions", 3, "Training discs, no story", 1),
    ("ghost-babel", "Metal Gear Solid", 2,
     "Ghost Babel — the Game Boy Color one, confusingly shipped west as just "
     "“Metal Gear Solid”. A side continuity, and excellent.", 0),
    ("mgs2", "Metal Gear Solid 2: Sons of Liberty", 1, "", 0),
    ("substance", "Metal Gear Solid 2: Substance", 3,
     "MGS2 with the VR and Snake Tales bolted on — the version to own, not a "
     "second read", 1),
    ("twin-snakes", "Metal Gear Solid: The Twin Snakes", 3,
     "The GameCube remake of MGS1, with MGS2 mechanics", 1),
    ("mgs3", "Metal Gear Solid 3: Snake Eater", 1, "", 0),
    ("acid", "Metal Gear Acid", 3,
     "Turn-based card game, its own continuity", 1),
    ("acid2", "Metal Gear Acid 2", 3, "", 1),
    ("subsistence", "Metal Gear Solid 3: Subsistence", 3,
     "MGS3 with the camera fixed and the MSX games included — the edition "
     "everything later is based on", 1),
    ("dgn", "Metal Gear Solid: Digital Graphic Novel", 3,
     "The Ashley Wood comic, playable on PSP; its Sons of Liberty sequel "
     "exists only as video on the MGS4 disc", 1),
    ("portable-ops", "Metal Gear Solid: Portable Ops", 2,
     "The Big Boss chapter between Snake Eater and Peace Walker — "
     "semi-canon, and the part Peace Walker quietly steps over", 0),
    ("po-plus", "Metal Gear Solid: Portable Ops Plus", 3,
     "Multiplayer expansion, no story", 1),
    ("mgs4", "Metal Gear Solid 4: Guns of the Patriots", 1, "", 0),
    ("peace-walker", "Metal Gear Solid: Peace Walker", 1,
     "Portable in shape, mainline in weight", 0),
    ("hd-collection", "Metal Gear Solid HD Collection", 3,
     "MGS2, MGS3 and Peace Walker in one box — the hours shown are the whole "
     "bundle", 1),
    ("se3d", "Metal Gear Solid: Snake Eater 3D", 3, "The 3DS port", 1),
    ("rising", "Metal Gear Rising: Revengeance", 2,
     "Platinum's sequel to MGS4 — a different genre entirely, and canon", 0),
    ("gz", "Metal Gear Solid V: Ground Zeroes", 1,
     "Short on purpose; the hinge into The Phantom Pain", 0),
    ("tpp", "Metal Gear Solid V: The Phantom Pain", 1, "", 0),
    ("survive", "Metal Gear Survive", 3,
     "The one made after Kojima left; outside the story", 1),
    ("master-collection", "Metal Gear Solid: Master Collection Vol. 1", 3,
     "MG1, MG2, MGS1–3 in one modern box — the hours shown are the whole "
     "bundle", 1),
    ("delta", "Metal Gear Solid Δ: Snake Eater", 3,
     "The 2025 remake of MGS3 — the modern way in, if the original's age "
     "puts anyone off", 1),
    ("master-collection-2", "Metal Gear Solid: Master Collection Vol. 2", 3,
     "MGS4, Peace Walker and Ghost Babel in one modern box — the hours shown "
     "are the whole bundle", 1),
]

# One row whose HLTB headline cannot be right, as (headline in the data file,
# hours shown). Vol. 2's headline main-story figure (comp_main) is 15 h, below
# all 7 of its main-story submissions (20 h 34 m to 33 h 43 m, checked
# 2026-11-12) and below MGS4 alone, so the row carries their median, 27 h.
# It applies only while the data file still holds that headline: re-pull
# game 181985 at the next refresh and drop the entry once the headline sits
# inside the submissions' range.
HOURS_OVERRIDE = {"master-collection-2": (15.0, 27.0)}

EXTRAS = [
    ("drama-cd", "Metal Gear Solid drama CDs", "1998–99",
     "Two volumes of side stories between MGS1 and 2, Japan only", 1),
    ("novel-mgs", "Metal Gear Solid (Raymond Benson)", "2008",
     "The MGS1 novelization", 1),
    ("novel-mgs2", "Metal Gear Solid 2 (Raymond Benson)", "2009", "", 1),
    ("novel-gotp", "Metal Gear Solid: Guns of the Patriots (Project Itoh)", "2012",
     "Kojima's friend's novel of MGS4 — the one with a reputation of its own",
     0),
]

ERAS = [
    ("msx", "The MSX era", 1987, 1997,
     "Two real games and one impostor. The MSX pair is the saga's actual "
     "foundation, and both are on Master Collection Vol. 1."),
    ("solid", "Solid", 1998, 2003,
     "The PlayStation reinvention, its expansions, and the Game Boy Color "
     "side path."),
    ("snakeeater", "Snake Eater and the PSP years", 2004, 2009,
     "The prequel turn, the card-game detour, and the portable Big Boss "
     "chapters."),
    ("bigboss", "Peace Walker to The Phantom Pain", 2010, 2017,
     "The saga runs backward to meet itself, and ends mid-sentence."),
    ("after", "After Kojima", 2018, 9999, ""),
]


def slug(t):
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def main():
    data = json.loads((pathlib.Path(__file__).resolve().parent / "data"
                       / "metalgear.json").read_text(encoding="utf-8"))

    entries = []
    for key, expect, tier, note, opt in ROSTER:
        rec = data.get(key)
        assert rec, "no HLTB record for %s" % key
        # Δ vs Delta and the like: compare loosely but on purpose
        got = rec["name"].replace("Δ", "Delta").lower()
        want = expect.replace("Δ", "Delta").lower()
        assert got == want, "record mismatch for %s: %r" % (key, rec["name"])
        year = str(rec["year"])[:4]
        hours = rec["main_h"]
        if key in HOURS_OVERRIDE and hours == HOURS_OVERRIDE[key][0]:
            hours = HOURS_OVERRIDE[key][1]
        x = {"id": "mgs-%s" % key, "t": expect, "n": year,
             "w": hours, "tier": tier, "year": int(year),
             "date": str(rec["year"]) if "-" in str(rec["year"]) else year + "-07-01"}
        if key == "ghost-babel":
            x["t"] = "Metal Gear: Ghost Babel"
        if key == "delta":
            x["t"] = "Metal Gear Solid Delta: Snake Eater"
        if note:
            x["note"] = note
        if opt:
            x["opt"] = 1
        entries.append(x)

    entries.sort(key=lambda e: (e["date"], e["t"]))

    sections = []
    for key, title, lo, hi, intro in ERAS:
        got = [e for e in entries if lo <= e["year"] <= hi]
        if not got:
            continue
        hours = sum(e["w"] for e in got)
        sec = {"id": key, "title": title,
               "sub": "%d–%d · %d entries · %d hours story"
                      % (got[0]["year"], got[-1]["year"], len(got), round(hours)),
               "items": [{k: v for k, v in e.items()
                          if k in ("id", "t", "n", "w", "tier", "opt")
                          or (k == "note" and v)} for e in got]}
        if intro:
            sec["intro"] = intro
        if key == "msx":
            sec["open"] = True
            # the MSX pair is the spine but the friction is real; a recap is a
            # legitimate on-ramp, and it lives on the header per the links rule
            sec["links"] = [{"label": "Story recap",
                             "url": "https://www.youtube.com/watch?v=lg8hX8lQrlo"}]
        sections.append(sec)

    sections.append({
        "id": "paper", "title": "On paper",
        "sub": "the drama CDs and the novels · optional",
        "items": [{"id": "mgs-x-%s" % k, "t": t, "n": n, "w": 0, "tier": 3,
                   **({"note": note} if note else {}), **({"opt": 1} if opt else {})}
                  for k, t, n, note, opt in EXTRAS],
    })

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(ids) == len(ROSTER) + len(EXTRAS), (len(ids),)
    t1 = [x for s in sections for x in s["items"] if x.get("tier") == 1]
    assert len(t1) == 9, "the saga spine should be 9 games, got %d" % len(t1)

    hours = sum(x["w"] for s in sections for x in s["items"])
    spine = sum(x["w"] for x in t1)

    prop = {
        "slug": SLUG,
        "title": "Metal Gear",
        "subtitle": "the whole saga in release order, sides and remakes included",
        "kind": "games",
        "popularity": 74,
        "year": "1987–",
        "blurb": "%d games and %d extras — about %d hours of story, %d of it "
                 "the saga spine." % (len(ROSTER), len(EXTRAS), round(hours),
                                      round(spine)),
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "play", "past": "played", "ing": "playing"},
        "itemOrder": "number-first",
        "accent": "#4A5D23",
        "accentDark": "#9DBB61",
        "tiers": True,
        "itemTiers": True,
        "paceTiers": [1, 2],
        "paceLabel": "the remakes, re-releases and extras",
        "notes": [
            ["Release order, on purpose.", "Metal Gear is the series where "
             "chronological order is a real alternative — MGS3 first, the Big "
             "Boss games, then the MSX pair and the Solid era. It works, but "
             "it spends every twist the release order was built around. Play "
             "it the way the audience met it; the in-universe order is for the "
             "second run."],
            ["Hours are story only.", "HowLongToBeat main-story figures, as "
             "asked — no completionist padding. The three collections show the "
             "whole bundle's hours, and the on-paper extras weigh nothing "
             "rather than a guess."],
            ["Tiers.", "1 is the saga spine: the MSX pair, MGS1–4, Peace "
             "Walker and both halves of V — about %d hours. 2 is the side "
             "stories that feed it: Ghost Babel, Portable Ops, Rising. 3 is "
             "remakes, re-releases, card games and extras; a finish date "
             "covers 1 and 2 and the checkbox adds the rest." % round(spine)],
            ["If the MSX games are a wall.", "The Story recap link on the "
             "first section — Barry Kramer's A Good Enough Summary of Metal "
             "Gear 1 & 2, sixteen minutes — covers everything MGS1 expects "
             "you to know. Honest substitute, not homework."],
            ["Two naming traps.", "The Game Boy Color game shipped west "
             "titled just “Metal Gear Solid” — it is Ghost Babel, a side "
             "continuity. And the NES “Metal Gear” is a compromised port; the "
             "MSX originals are the real ones and sit on Master Collection "
             "Vol. 1."],
            "Hours and dates from HowLongToBeat, collected from its own pages "
            "and verified by name.",
        ],
        "sections": sections,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d entries, %d hours (%d spine)"
          % (len(sections), len(ids), round(hours), round(spine)))
    for s in sections:
        print("   %-34s %2d  %s" % (s["title"], len(s["items"]), s["sub"][:44]))


if __name__ == "__main__":
    main()
