#!/usr/bin/env python3
"""Generate properties/hellboy.json.

    python tools/make_hellboy.py

The Mignolaverse reading order in collected volumes, everything from
Wikipedia's List of Hellboy comics collections tables (tools/data/
hellboy.json, built and asserted by scratch/agent-books/parse_hellboy.py):

  Hellboy volumes 1–12, in trade order (which is the in-universe order);
  B.P.R.D.: the Plague of Frogs years — trades 1–14 with the unnumbered
  1948 spliced in after 1947, as the table's own 1946–1948 cycle groups
  them; B.P.R.D.: Hell on Earth 1–15; Hellboy in Hell; The Devil You Know
  as the closing cycle; and an optional section of wider spokes as
  series-level rows weighted by their volume counts.

Links live on section headers only. Unit is the volume.

ABOUT THE ROWS THAT CARRY NO `w`, because a weight audit will ask. This
list weighs in VOLUMES, not hours — `weightUnit` says so — and a collected
trade is exactly one volume. A row with no `w` is worth 1 downstream, which
is not a fallback here but the correct figure, so the 47 main-line rows are
fully weighted already and there is no gap to fill. The only rows that need
a number are the four series-level spokes, which stand in for 9, 6, 5 and
10 volumes apiece and say so.

What would be wrong is converting to another unit. HowLongToBeat has
nothing to say about comics, and issue counts are a DIFFERENT unit: putting
issues on a volume-weighted list would silently change what every number on
the page means. The count assert below is the guard — it adds the explicit
spoke weights to the implicit one-per-trade and must equal 47 + 30.
"""
import json
import pathlib

SLUG = "hellboy"
WP = "https://en.wikipedia.org/wiki/"
LIST_URL = WP + "List_of_Hellboy_comics"


def slugify(t):
    # CLU-430. This fold DELETES a straight apostrophe (`The Emperor's Soul`
    # gives the-emperors-soul) and left U+2019 alone, so a curly one reached
    # the isalnum test below and became a dash instead. Two spellings of one
    # title would reach two ids, and an id is the `item_id` every tick and
    # thumb is stored against — moving one unticks the row for everyone
    # holding it. Drop both forms: that is the correction THIS direction
    # needs, and the opposite of what the folds that dash a straight
    # apostrophe need.
    t = t.replace("'", "").replace("’", "").replace("‘", "")
    keep = "".join(c.lower() if c.isalnum() else "-" for c in t)
    keep = keep.encode("ascii", "ignore").decode("ascii")
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def main():
    here = pathlib.Path(__file__).resolve().parent
    d = json.loads((here / "data" / "hellboy.json").read_text(encoding="utf-8"))

    def vol_rows(vols, prefix, extra_note=None):
        out = []
        for v in vols:
            note = "Vol. %d" % v["vol"]
            if extra_note:
                more = extra_note(v)
                if more:
                    note += " · " + more
            out.append({"id": "%s-%d" % (prefix, v["vol"]), "t": v["title"],
                        "n": str(v["year"]), "note": note})
        return out

    hb = vol_rows(d["hellboy"], "hb-v")
    assert len(hb) == 12

    def war_note(v):
        return ("the 1946–1948 war-era cycle"
                if v["cycle"] == "1946–1948" else None)

    pof = vol_rows(d["plague"], "hb-pof", war_note)
    w48 = d["war_1948"]
    i47 = next(i for i, x in enumerate(d["plague"]) if x["title"] == "1947")
    pof.insert(i47 + 1, {
        "id": "hb-1948", "t": "1948", "n": str(w48["year"]),
        "note": "Unnumbered — completes the 1946–1948 war-era trilogy"})
    assert len(pof) == 15

    hoe = vol_rows(d["hell_on_earth"], "hb-hoe")
    hell = vol_rows(d["in_hell"], "hb-hell")
    dyk = vol_rows(d["devil_you_know"], "hb-dyk")
    assert (len(hoe), len(hell), len(dyk)) == (15, 2, 3)

    spoke_meta = [
        ("abe", "Abe Sapien"), ("lobster", "Lobster Johnson"),
        ("witchfinder", "Sir Edward Grey, Witchfinder"),
        ("hb-bprd", "Hellboy and the B.P.R.D."),
    ]
    spokes = []
    for key, name in spoke_meta:
        s = d["spokes"][key]
        assert s["name"] == name
        spokes.append({
            "id": "hb-s-" + slugify(name), "t": name,
            "n": "%d vols" % s["vols"], "w": s["vols"], "opt": 1,
            "note": "%s to %s — one tick covers the series"
                    % (s["first"], s["last"])})

    def yspan(rows):
        ys = sorted(int(r["n"]) for r in rows)
        return "%d–%d" % (ys[0], ys[-1])

    sections = [
        {"id": "hellboy", "title": "Hellboy",
         "sub": "volumes 1–12 · %s" % yspan(hb), "open": True,
         "links": [{"label": "Hellboy", "url": WP + "Hellboy"},
                   {"label": "Collected editions", "url": LIST_URL}],
         "intro": "Mignola's own book, in trade order — Seed of "
                  "Destruction to The Storm and the Fury. This is the "
                  "spine; everything else branches off it.",
         "items": hb},
        {"id": "plague", "title": "B.P.R.D.: the Plague of Frogs years",
         "sub": "trades 1–14, plus 1948 · %s" % yspan(pof),
         "links": [{"label": "Collected editions", "url": LIST_URL}],
         "intro": "The Bureau becomes the main event. Volumes 9 and 13 "
                  "are the wartime books the list files under its "
                  "1946–1948 cycle, and the unnumbered 1948 follows them "
                  "here to keep that trilogy whole.",
         "items": pof},
        {"id": "hell-on-earth", "title": "B.P.R.D.: Hell on Earth",
         "sub": "volumes 1–15 · %s" % yspan(hoe),
         "links": [{"label": "Collected editions", "url": LIST_URL}],
         "items": hoe},
        {"id": "in-hell", "title": "Hellboy in Hell",
         "sub": "2 volumes · %s · Mignola returns to the drawing board"
                % yspan(hell),
         "links": [{"label": "Collected editions", "url": LIST_URL}],
         "items": hell},
        {"id": "devil-you-know", "title": "B.P.R.D.: The Devil You Know",
         "sub": "3 volumes · %s · the closing cycle" % yspan(dyk),
         "links": [{"label": "Collected editions", "url": LIST_URL}],
         "items": dyk},
        {"id": "spokes", "title": "The wider Mignolaverse",
         "sub": "series-level rows · optional",
         "links": [{"label": "Abe Sapien", "url": WP + "Abe_Sapien"},
                   {"label": "Lobster Johnson",
                    "url": WP + "Lobster_Johnson"},
                   {"label": "Collected editions", "url": LIST_URL}],
         "intro": "One row per spoke series, weighted by how many "
                  "collected volumes it runs. Dip in per volume if a "
                  "spoke earns per-volume rows later.",
         "items": spokes},
    ]

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == 51 and len(set(ids)) == 51, len(ids)
    assert all(i == slugify(i) and i.isascii() for i in ids)
    assert not any("url" in x for s in sections for x in s["items"])
    assert all(s.get("links") for s in sections)
    # A bare row is one volume — the unit's own value, not a missing figure.
    # Only the series-level spokes stand in for more than one.
    trades = [x for s in sections if s["id"] != "spokes" for x in s["items"]]
    assert not any("w" in x for x in trades), \
        "a trade row grew a weight; one trade is one volume by definition"
    assert all(isinstance(x.get("w"), int) and x["w"] > 1 for x in spokes), \
        "a spoke row must carry the volume count it stands in for"
    total_vols = sum(x.get("w", 1) for s in sections for x in s["items"])
    assert total_vols == 47 + 30, total_vols

    prop = {
        "slug": SLUG,
        "title": "Hellboy",
        "subtitle": "the Mignolaverse in collected volumes",
        "kind": "comics",
        "popularity": 57,
        "year": "1994–2019",
        "blurb": "The reading order in trades: Hellboy 1–12, the two "
                 "B.P.R.D. cycles, Hellboy in Hell and The Devil You Know "
                 "— 47 volumes of the main line, with the spokes optional.",
        "unit": {"one": "volume", "many": "volumes"},
        "weightUnit": {"one": "volume", "many": "volumes"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": "#9C271B",
        "accentDark": "#66C2BC",
        "tiers": False,
        "notes": [
            ["Volumes, not issues.",
             "Every row is a collected trade, in the order the numbered "
             "spines put them — Hellboy first, then the B.P.R.D. cycles, "
             "Hellboy in Hell, and The Devil You Know to close. That is "
             "also broadly publication order; the strands run in parallel "
             "and interleaving them further is a rabbit hole this list "
             "stays out of."],
            ["1946, 1947, 1948.",
             "The war-era books sit inside the B.P.R.D. trade numbering "
             "as volumes 9 and 13, and Wikipedia's list files them under "
             "their own 1946–1948 cycle; the unnumbered 1948 is spliced "
             "in after 1947 so the trilogy reads together."],
            ["The spokes are one row each.",
             "Abe Sapien, Lobster Johnson, Witchfinder and Hellboy and "
             "the B.P.R.D. are optional series-level rows weighted by "
             "their volume counts. Frankenstein Underground, Young "
             "Hellboy, the one-shots and the non-canon books are beyond "
             "this list."],
            "Volume lists, numbering, cycles and years from the "
            "collections tables of Wikipedia's List of Hellboy comics.",
        ],
        "sections": sections,
    }

    out = here.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json — %d rows, %d volumes weighted" % (SLUG, len(ids),
                                                            total_vols))
    for s in sections:
        print("   %-36s %2d  %s" % (s["title"][:36], len(s["items"]),
                                    s["sub"][:40]))


if __name__ == "__main__":
    main()
