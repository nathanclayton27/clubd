#!/usr/bin/env python3
"""Collect HowLongToBeat main-story hours for the immersive-sim canon.

    python scratch/immersive/fetch_hltb.py

Every figure goes through tools/gwlib/hltb.py's verify-by-name gate: a result
counts only when its name normalizes to the title asked for and its release
year sits within two years of the one asked for. Anything the gate refuses is
written down with the reason instead of a number.

Raw rows land in scratch/immersive/hltb_raw.json (the Session cache), the
verified per-key result in scratch/immersive/hltb.json. Re-running costs
nothing; delete the raw cache to re-fetch.

Two titles need the search string separated from the verified name, the same
trick scratch/fps/fetch_hltb.py needed for F.E.A.R.:

  * "System Shock" and "Prey" are each two games HowLongToBeat calls by the
    same name (1994/2023 and 2006/2017). The gate's nearest-year sort picks
    the right one; nothing here has to.
  * "Dark Messiah of Might and Magic" searched under its own name asks the
    site for a game containing the term "of" and finds nothing useful, so the
    row searches for "Dark Messiah Might Magic" and still VERIFIES against
    the full title. Only the query changes; the gate is untouched.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from gwlib import hltb  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent

# key, name to VERIFY against, release year, (optional) string to SEARCH with
QUERIES = [
    ("uu", "Ultima Underworld: The Stygian Abyss", 1992),
    ("ss1", "System Shock", 1994),
    ("thief", "Thief: The Dark Project", 1998),
    ("ss2", "System Shock 2", 1999),
    ("thief2", "Thief II: The Metal Age", 2000),
    ("deusex", "Deus Ex", 2000),
    ("arx", "Arx Fatalis", 2002),
    ("thief3", "Thief: Deadly Shadows", 2004),
    ("bloodlines", "Vampire: The Masquerade - Bloodlines", 2004),
    ("darkmessiah", "Dark Messiah of Might and Magic", 2006,
     "Dark Messiah Might Magic"),
    ("bioshock", "BioShock", 2007),
    ("hr", "Deus Ex: Human Revolution", 2011),
    ("dishonored", "Dishonored", 2012),
    ("mankind", "Deus Ex: Mankind Divided", 2016),
    ("dishonored2", "Dishonored 2", 2016),
    ("prey", "Prey", 2017),
    ("voidbastards", "Void Bastards", 2019),
    ("crueltysquad", "Cruelty Squad", 2021),
    ("deathloop", "Deathloop", 2021),
    ("weirdwest", "Weird West", 2022),
    ("mosalina", "Mosa Lina", 2023),
    ("shadowsofdoubt", "Shadows of Doubt", 2023),
    ("skindeep", "Skin Deep", 2025),
]


def main():
    session = hltb.Session(cache_dir=str(HERE))
    out = {}
    for row in QUERIES:
        key, query, year = row[0], row[1], row[2]
        search = row[3] if len(row) > 3 else query
        rows = session.search(search)
        hours, rec, why = hltb.story_hours(query, year, results=rows)
        out[key] = {
            "query": query, "search": search, "want_year": year,
            "name": getattr(rec, "game_name", None),
            "year": getattr(rec, "release_world", None),
            "main_h": hours, "why": why,
            "candidates": sorted({(r.game_name, r.release_world)
                                  for r in rows})[:8],
        }
        print("%-16s %-44s %-8s %s"
              % (key, out[key]["name"] or "-", hours, why[:70]))

    (HERE / "hltb.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")
    got = sum(1 for v in out.values() if v["main_h"])
    print("\n%d/%d verified, %d live calls"
          % (got, len(QUERIES), session.calls))


if __name__ == "__main__":
    main()
