#!/usr/bin/env python3
"""Generate properties/dragon-ball.json.

    python tools/make_db_anime.py

One row per episode across the whole franchise in broadcast order: Dragon
Ball (153), Z (291), GT (64), Kai's slot, Super (131), Daima (20). Z and
Super are split into the saga groupings their Wikipedia episode lists use —
the season sets — because 291 episodes is not one section; Dragon Ball and
GT keep one section per series with saga boundaries in the section intro.

Kai is a re-cut of Z, not a new story, so it is one optional row sitting in
its broadcast slot rather than 167 rows that would double-count Z. The
theatrical films and TV specials (GT's A Hero's Legacy included) are left
out; they belong to a films page later.

Everything numeric comes from tools/data/db_anime.json, which
scratch/dragonball/parse.py builds from the Wikipedia episode lists and
asserts against the articles' own counts (lead totals, series-overview sums,
and the counted episode rows where the article carries them). Episode titles
are deliberately absent — five series of them is a lot of printed facts, and
each section links the list that has them.
"""
import json
import pathlib
import unicodedata

SLUG = "dragon-ball"

DATA = pathlib.Path(__file__).resolve().parent / "data" / "db_anime.json"
OUT = pathlib.Path(__file__).resolve().parent.parent / "properties" / (SLUG + ".json")

# the totals the group signed up for; the build fails rather than drift
EXPECTED = {"db": 153, "z": 291, "gt": 64, "super": 131, "daima": 20}
KAI_INTL = 167

LISTS = {
    "db": "https://en.wikipedia.org/wiki/List_of_Dragon_Ball_episodes",
    "z": "https://en.wikipedia.org/wiki/List_of_Dragon_Ball_Z_episodes",
    "gt": "https://en.wikipedia.org/wiki/List_of_Dragon_Ball_GT_episodes",
    "super": "https://en.wikipedia.org/wiki/List_of_Dragon_Ball_Super_episodes",
    "daima": "https://en.wikipedia.org/wiki/Dragon_Ball_Daima#Episodes",
    "kai": "https://en.wikipedia.org/wiki/List_of_Dragon_Ball_Z_Kai_episodes",
}

# item-id prefix per series; never change these, they are the saved progress
IDP = {"db": "db-og", "z": "db-z", "gt": "db-gt", "super": "db-s",
       "daima": "db-dai"}


def slugify(t):
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    keep = "".join(c.lower() if ("a" <= c.lower() <= "z" or c.isdigit()) else "-"
                   for c in t)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def short_saga(name):
    for suffix in (" Sagas", " Saga"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def years_of(span):
    a = int(span[:4])
    b = span.split("–")[-1] if "–" in span else span[:4]
    b = int(b) if len(b) == 4 else (a // 100) * 100 + int(b)
    return a, b


def episode_items(prefix, first, last):
    return [{"id": "%s-%d" % (prefix, e), "t": "Episode", "n": str(e)}
            for e in range(first, last + 1)]


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    series = {s["key"]: s for s in data["series"]}

    for key, want in EXPECTED.items():
        got = series[key]["total"]
        assert got == want, "%s: data says %d episodes, expected %d" % (key, got, want)
        spans = series[key]["sagas"]
        assert spans[0]["first"] == 1 and spans[-1]["last"] == want
        for a, b in zip(spans, spans[1:]):
            assert b["first"] == a["last"] + 1, "%s: saga gap at %d" % (key, b["first"])
    kai = data["kai"]
    assert kai["international"] == KAI_INTL, kai

    def one_section(key, sid):
        s = series[key]
        sagas = s["sagas"]
        intro = None
        if len(sagas) > 1:
            words = {2: "Two", 3: "Three", 4: "Four", 9: "Nine"}
            intro = "%s sagas: %s." % (
                words.get(len(sagas), str(len(sagas))),
                ", ".join("%s (%d–%d)" % (short_saga(g["name"]),
                                          g["first"], g["last"])
                          for g in sagas))
        sec = {
            "id": sid,
            "title": s["title"],
            "sub": "%s · episodes 1–%d" % (s["years"], s["total"]),
            "links": [{"label": "Episode list", "url": LISTS[key]}],
            "items": episode_items(IDP[key], 1, s["total"]),
        }
        if intro:
            sec["intro"] = intro
        return sec

    def saga_sections(key, prefix):
        s = series[key]
        return [{
            "id": "%s-%s" % (prefix, slugify(g["name"])),
            "title": g["name"],
            "sub": "%s · episodes %d–%d" % (s["title"], g["first"], g["last"]),
            "links": [{"label": "Episode list", "url": LISTS[key]}],
            "items": episode_items(IDP[key], g["first"], g["last"]),
        } for g in s["sagas"]]

    kai_section = {
        "id": "s-kai",
        "title": "Dragon Ball Z Kai",
        "sub": "%s · a re-cut of Z, not a new series" % kai["years"],
        "links": [{"label": "Episode list", "url": LISTS["kai"]}],
        "items": [{
            "id": "db-kai",
            "t": "Dragon Ball Z Kai",
            "n": kai["years"],
            "opt": 1,
            "note": "Z's %d episodes re-cut to %d (%d internationally) to "
                    "track the manga. Tick it if Kai is how you watched Z."
                    % (kai["z_episodes"], kai["japan"], kai["international"]),
        }],
    }

    sections = ([one_section("db", "s-db")]
                + saga_sections("z", "z")
                + [one_section("gt", "s-gt"), kai_section]
                + saga_sections("super", "su")
                + [one_section("daima", "s-daima")])

    ids = [x["id"] for s in sections for x in s["items"]]
    episodes = sum(EXPECTED.values())
    assert len(ids) == len(set(ids)), "duplicate item ids"
    assert len(ids) == episodes + 1, (len(ids), episodes)
    assert len(sections) == 1 + 9 + 1 + 1 + 5 + 1, len(sections)

    first_year = years_of(series["db"]["years"])[0]
    last_year = years_of(series["daima"]["years"])[1]

    prop = {
        "slug": SLUG,
        "title": "Dragon Ball (anime)",
        "kind": "anime",
        "popularity": 89,
        "year": "%d–%d" % (first_year, last_year),
        "blurb": "%d episodes in broadcast order, Dragon Ball through Daima; "
                 "Kai is one optional row." % episodes,
        "unit": {"one": "episode", "many": "episodes"},
        "verb": {"base": "watch", "past": "watched", "ing": "watching"},
        "accent": "#C4661F",
        "accentDark": "#F0A45C",
        "tiers": False,
        "notes": [
            ["Sagas.", "Z and Super are split into the saga groupings their "
                       "episode lists use — the season sets. Dragon Ball and "
                       "GT keep one section per series, saga boundaries in "
                       "the section intro."],
            ["Kai.", "A re-cut of Z, not a new story: %d episodes down to %d "
                     "in Japan, %d internationally. One optional row stands "
                     "in for the whole thing." % (kai["z_episodes"],
                                                 kai["japan"],
                                                 kai["international"])],
            ["Films.", "The theatrical films and TV specials — GT's A Hero's "
                       "Legacy included — are left out. They are a later "
                       "page."],
            ["Complete.", "Through Daima (%s), the newest series. If a new "
                          "one airs, rerun the generator."
                          % series["daima"]["years"]],
            # Unheaded, last: the colophon (CLU-275 rule 6). The sources block
            # in tools/data/db_anime.json is what this reports.
            "Episode counts, years and saga groupings machine-read from "
            "Wikipedia's episode lists for Dragon Ball, Z, GT, Super and Kai "
            "and from the Dragon Ball Daima article; every total is asserted "
            "against the articles' own — lead counts, series-overview sums and "
            "the counted episode rows — before this builds. Z's check is its "
            "lead total against its overview sum, because its per-episode "
            "tables live in nine season articles this does not read.",
        ],
        "sections": sections,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d rows (%d episodes + the Kai row)"
          % (len(sections), len(ids), episodes))
    for s in sections:
        print("   %-58s %4d" % (s["title"] + "  (" + s["sub"] + ")",
                                len(s["items"])))


if __name__ == "__main__":
    main()
