#!/usr/bin/env python3
"""Generate properties/dragon-ball-manga.json.

    python tools/make_db_manga.py

The original 519 chapters, numbered straight through as serialized, one
section per collected volume — the Viz split the Wikipedia chapter lists use:
Dragon Ball volumes 1–16 (chapters 1–194) and Dragon Ball Z volumes 1–26
(chapters 195–519, which Viz renumbers 1–325; those sections carry both
numbers). Then Dragon Ball Super, a separate series on indefinite hiatus
since March 2024, as one section.

Super stops at the last chapter collected into a volume because that is
where the Wikipedia chapter list stops — the count is asserted against that
list, and chapters serialized since are not in it, so they are not invented
here. Rerun the pipeline to extend it.

Everything numeric comes from tools/data/db_manga.json, which
scratch/dragonball/parse.py builds from the Wikipedia chapter lists and
asserts against the articles' own counts: per-volume chapter lists must tile
with no gap or overlap, and the totals must match the leads (519 chapters in
42 volumes; 24 Super volumes).
"""
import json
import pathlib

SLUG = "dragon-ball-manga"

DATA = pathlib.Path(__file__).resolve().parent / "data" / "db_manga.json"
OUT = pathlib.Path(__file__).resolve().parent.parent / "properties" / (SLUG + ".json")

# the totals the group signed up for; the build fails rather than drift
EXPECTED = {"chapters": 519, "volumes": 42, "part1": 16, "part2": 26,
            "super_volumes": 24}

L1 = [{"label": "The chapter list",
       "url": "https://en.wikipedia.org/wiki/List_of_Dragon_Ball_chapters_(series)"}]
L2 = [{"label": "The chapter list",
       "url": "https://en.wikipedia.org/wiki/List_of_Dragon_Ball_Z_chapters"}]
LS = [{"label": "The chapter list",
       "url": "https://en.wikipedia.org/wiki/List_of_Dragon_Ball_Super_chapters"}]


def chapter_items(prefix, first, last):
    return [{"id": "%s-%d" % (prefix, c), "t": "Chapter", "n": str(c)}
            for c in range(first, last + 1)]


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    orig, sup = data["original"], data["super"]

    assert orig["chapters"] == EXPECTED["chapters"], orig["chapters"]
    assert orig["volumes"] == EXPECTED["volumes"], orig["volumes"]
    assert len(orig["part1"]) == EXPECTED["part1"], len(orig["part1"])
    assert len(orig["part2"]) == EXPECTED["part2"], len(orig["part2"])
    assert sup["volumes"] == EXPECTED["super_volumes"], sup["volumes"]

    # volumes must tile the chapters with no gap or overlap
    run = orig["part1"] + orig["part2"]
    assert run[0]["first"] == 1 and run[-1]["last"] == orig["chapters"]
    for a, b in zip(run, run[1:]):
        assert b["first"] == a["last"] + 1, "gap after chapter %d" % a["last"]
    assert orig["part2"][0]["z_first"] == 1
    assert orig["part2"][-1]["z_last"] == orig["chapters"] - orig["part1"][-1]["last"]
    vols = sup["vols"]
    assert vols[0]["first"] == 1 and vols[-1]["last"] == sup["chapters"]
    for a, b in zip(vols, vols[1:]):
        assert b["first"] == a["last"] + 1, "Super gap after chapter %d" % a["last"]

    sections = []
    for v in orig["part1"]:
        sections.append({
            "id": "v-%d" % v["vol"],
            "title": "Volume %d" % v["vol"],
            "sub": "chapters %d–%d · %s" % (v["first"], v["last"], v["title"]),
            "links": L1,
            "items": chapter_items("dbm", v["first"], v["last"]),
        })
    for v in orig["part2"]:
        sections.append({
            "id": "zv-%d" % v["vol"],
            "title": "Z Volume %d" % v["vol"],
            "sub": "chapters %d–%d (Z %d–%d) · %s"
                   % (v["first"], v["last"], v["z_first"], v["z_last"],
                      v["title"]),
            "links": L2,
            "items": chapter_items("dbm", v["first"], v["last"]),
        })
    sections.append({
        "id": "super",
        "title": "Dragon Ball Super",
        "sub": "chapters 1–%d · on hiatus" % sup["chapters"],
        "intro": "A separate series, drawn by Toyotarou, begun in 2015 and on "
                 "indefinite hiatus since March 2024. "
                 "Chapter %d is the last one collected into a volume, which "
                 "is as far as the chapter list goes." % sup["chapters"],
        "links": LS,
        "items": chapter_items("dbsm", 1, sup["chapters"]),
    })

    ids = [x["id"] for s in sections for x in s["items"]]
    total = len(ids)
    assert len(ids) == len(set(ids)), "duplicate item ids"
    assert total == orig["chapters"] + sup["chapters"], total
    assert len(sections) == orig["volumes"] + 1, len(sections)

    prop = {
        "slug": SLUG,
        "title": "Dragon Ball (manga)",
        "subtitle": "Akira Toriyama",
        "kind": "manga",
        "popularity": 78,
        "year": "1984–",
        "blurb": "The original %d chapters in %d volumes, then Dragon Ball "
                 "Super — %d so far, on indefinite hiatus."
                 % (orig["chapters"], orig["volumes"], sup["chapters"]),
        "unit": {"one": "chapter", "many": "chapters"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": "#B03A2E",
        "accentDark": "#EF8A7A",
        "tiers": False,
        "notes": [
            ["Two numberings.", "Chapters run 1–%d straight through, as "
             "serialized. Viz splits the same run into Dragon Ball (volumes "
             "1–%d, chapters 1–%d) and Dragon Ball Z (volumes 1–%d, "
             "renumbered 1–%d); the Z sections carry both numbers."
             % (orig["chapters"], len(orig["part1"]),
                orig["part1"][-1]["last"], len(orig["part2"]),
                orig["part2"][-1]["z_last"])],
            ["Super.", "A separate series by Toyotarou, on indefinite hiatus "
             "since March 2024. Chapters "
             "here stop at %d — the last one collected into a volume, which "
             "is as far as the Wikipedia chapter list goes. Rerun the "
             "generator to extend it." % sup["chapters"]],
            ["Volumes.", "Sections are the collected volumes; boundaries are "
             "parsed from the Wikipedia chapter lists and checked to tile "
             "the chapters with no gap or overlap."],
        ],
        "sections": sections,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d chapters (%d original + %d Super)"
          % (len(sections), total, orig["chapters"], sup["chapters"]))
    print("  longest section: %d chapters" % max(len(s["items"]) for s in sections))


if __name__ == "__main__":
    main()
