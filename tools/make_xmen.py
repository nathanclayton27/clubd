#!/usr/bin/env python3
"""Generate properties/x-men.json — the comprehensive X-Men reading list.

    python3 tools/make_xmen.py

The spine is the two flagship lineages, every issue rowed:

  X-Men (1963) #1-544        which becomes Uncanny X-Men and runs to 2011
  X-Men (1991) #1-275        which becomes New X-Men at #114, X-Men again at
                             #157, and X-Men Legacy at #208

From 1991 to 2001 the two flagships ran in lockstep — 113 issues each, ending
together — so they are read in pairs, each month's Uncanny then its X-Men. The
same pairing carries 2004-2008 (Uncanny #444-494 against X-Men #157-207, again
equal) and 2008-2011 (Uncanny #500+ against Legacy).

Cross-title chapters follow the house rule: spliced in at the point they are
read, as ◆ rows sized by how many issues they are, never appended at the end.
The 2011-2019 era is deliberately one row per run rather than per issue — the
line fragmented into a dozen titles and no one reads it straight through — and
the notes say so.

Series links resolve against tools/data/marvel_series_index.json and the build
fails on a slug that is not in it. Notes say what an issue IS — a debut, a
creator boundary, an arc name — never what happens in it.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from spiderman_data import weave  # noqa: E402  (generic; lives there historically)

SLUG = "x-men"

_INDEX = json.loads((pathlib.Path(__file__).resolve().parent / "data"
                     / "marvel_series_index.json").read_text(encoding="utf-8"))


def S(slug):
    assert slug in _INDEX, "not in the Marvel index: %r" % slug
    return "https://www.marvel.com/comics/series/%s/%s" % (_INDEX[slug], slug)


L = lambda label, slug: {"label": label, "url": S(slug)}

# ------------------------------------------------------------------- notes --
U_NOTES = {
    1: "The X-Men and Magneto debut", 4: "The Brotherhood debuts",
    12: "Juggernaut debuts", 14: "The Sentinels debut",
    28: "Banshee debuts", 56: "Neal Adams arrives",
    66: "The last new issue before the reprint years",
    94: "The All-New team's monthlies begin — Claremont from here",
    101: "The Phoenix", 108: "Byrne arrives",
    120: "Alpha Flight debuts", 129: "Kitty Pryde and Emma Frost debut",
    130: "Dazzler debuts", 129 + 1000: None,
    134: "The Dark Phoenix Saga in full swing",
    137: "The Phoenix saga concludes", 138: "An era ends; Cyclops steps away",
    139: "Kitty joins", 141: "Days of Future Past, part 1",
    142: "Days of Future Past, part 2 — and the indicia says Uncanny now",
    148: "Caliban debuts", 158: "Rogue's first issue here",
    161: "Magneto's backstory", 171: "Rogue joins the team",
    186: "“Lifedeath” — Barry Windsor-Smith", 193: "Twentieth-anniversary issue",
    200: "The Trial of Magneto", 201: "Baby Nathan — and Whilce Portacio later",
    205: "“Wounded Wolf” — Windsor-Smith again", 210: "The Mutant Massacre begins",
    212: "Massacre: Wolverine vs Sabretooth",
    221: "Mister Sinister debuts", 244: "Jubilee debuts",
    248: "Jim Lee's first issue", 266: "Gambit debuts",
    281: "The new era — Whilce Portacio, and the Gold team",
    350: "“Trial of Gambit” — a big one", 390: "“The Cure”",
    393: "Eve of Destruction ends the volume's long march",
    500: "Fraction and Brubaker take it to San Francisco",
    510: "Greg Land, Sisterhood", 522: "A long-awaited return",
    544: "The final issue of the 1963 series",
}
U_STARS = {94: 2, 101: 1, 129: 1, 137: 2, 141: 2, 142: 2, 171: 1, 186: 1,
           200: 1, 210: 1, 266: 1, 281: 1, 350: 1, 500: 1, 544: 1}

X2_NOTES = {
    1: "The best-selling comic issue of all time — Claremont and Jim Lee",
    4: "Omega Red debuts", 14: "X-Cutioner's Song, chapters here",
    25: "Fatal Attractions — the famous one", 30: "The wedding issue",
    41: "Legion Quest concludes; everything stops",
    50: "Genesis revealed", 53: "Onslaught teased",
    114: "Morrison begins — “E Is for Extinction”",
    115: "Cassandra Nova", 132: "“Ambient magnetic fields” — the quiet one",
    141: "“Planet X” begins", 150: "Planet X concludes",
    154: "Morrison's last — “Here Comes Tomorrow” ends",
    157: "Austen's Reload — the title is X-Men again",
    166: "Milligan begins", 188: "Carey begins — “Supernovas”",
    205: "Messiah Complex, chapters here",
    208: "The title becomes X-Men: Legacy — Professor X's book",
    235: "Second Coming, chapters here",
}
X2_STARS = {1: 2, 25: 2, 41: 1, 114: 2, 150: 1, 154: 2, 188: 1, 208: 1}


def u(n):
    t = "Uncanny X-Men" if n >= 142 else "X-Men"
    x = {"id": "xm-u%d" % n, "t": t, "n": "#%d" % n, "w": 1}
    if U_NOTES.get(n):
        x["note"] = U_NOTES[n]
    if n in U_STARS:
        x["star"] = U_STARS[n]
    return x


def x2(n):
    if n >= 208:
        t = "X-Men: Legacy"
    elif n >= 157:
        t = "X-Men vol. 2"
    elif n >= 114:
        t = "New X-Men"
    else:
        t = "X-Men vol. 2"
    x = {"id": "xm-x%d" % n, "t": t, "n": "#%d" % n, "w": 1}
    if X2_NOTES.get(n):
        x["note"] = X2_NOTES[n]
    if n in X2_STARS:
        x["star"] = X2_STARS[n]
    return x


def it(key, title, num, note="", star=0, w=1, opt=0):
    x = {"id": "xm-" + key, "t": title, "n": num, "w": w}
    if note:
        x["note"] = note
    if star:
        x["star"] = star
    if opt:
        x["opt"] = 1
    return x


def urange(a, b):
    return [u(n) for n in range(a, b + 1)]


def xrange2(a, b):
    return [x2(n) for n in range(a, b + 1)]


def pairs(us, xs):
    """Each month's Uncanny, then its X-Men. Tails follow whole."""
    out = []
    for i in range(max(len(us), len(xs))):
        if i < len(us):
            out.append(us[i])
        if i < len(xs):
            out.append(xs[i])
    return out


def run(key, title, span, w, note="", opt=1):
    return it(key, title, span, note, 0, w, opt)


# ------------------------------------------------------------ From the Ashes --
# The era ran July 2024 to December 2025 (Wikipedia, "X-Men: From the Ashes"):
# X-Men (vol. 7) #1-22, Uncanny X-Men (vol. 6) #1-21, Exceptional X-Men #1-13.
# The two flagships share two crossovers ("Raid on Graymalkin" alternates
# between them issue by issue), so they are read in release order. Release
# dates are each issue's ReleaseDate on the Marvel Database, read 2026-11-11.
ASH_X = ["2024-07-10", "2024-08-14", "2024-08-28", "2024-09-18", "2024-10-02",
         "2024-10-23", "2024-11-06", "2024-12-04", "2024-12-25", "2025-01-29",
         "2025-02-12", "2025-02-26", "2025-03-12", "2025-04-02", "2025-04-23",
         "2025-05-07", "2025-06-04", "2025-06-18", "2025-07-02", "2025-08-13",
         "2025-08-27", "2025-09-24"]                       # X-Men #1-22
ASH_U = ["2024-08-07", "2024-09-11", "2024-09-25", "2024-10-16", "2024-11-13",
         "2024-11-27", "2024-12-11", "2025-01-08", "2025-01-22", "2025-02-19",
         "2025-03-05", "2025-03-26", "2025-04-09", "2025-05-14", "2025-05-28",
         "2025-06-25", "2025-07-09", "2025-07-23", "2025-08-06", "2025-09-03",
         "2025-09-17"]                                      # Uncanny #1-21
ASH_NOTES = {
    ("x", 1): "MacKay's flagship",
    ("u", 1): "Simone's book",
    ("x", 8): "“Raid on Graymalkin” begins — it alternates with Uncanny",
    ("u", 11): "“X-Manhunt” begins",
}


def ash(kind, n):
    """One From the Ashes issue. Each #1 keeps the id its placeholder row had,
    so a tick on the old 'ongoing' row lands on the first issue."""
    title, first, pre = {"x": ("X-Men (2024)", "ash-xmen", "ash-x"),
                         "u": ("Uncanny X-Men (2024)", "ash-uncanny", "ash-u"),
                         "e": ("Exceptional X-Men", "ash-exceptional", "ash-e")}[kind]
    key = first if n == 1 else "%s%d" % (pre, n)
    return it(key, title, "#%d" % n, ASH_NOTES.get((kind, n), ""))


def ash_flagships():
    assert len(ASH_X) == 22 and len(ASH_U) == 21
    dated = ([(d, "x", n) for n, d in enumerate(ASH_X, 1)]
             + [(d, "u", n) for n, d in enumerate(ASH_U, 1)])
    assert len({d for d, _, _ in dated}) == len(dated), "same-day issues"
    return [ash(k, n) for _, k, n in sorted(dated)]


# ---------------------------------------------------------------- sections --
SECTIONS = [
    {
        "id": "silver", "title": "The Silver Age", "sub": "#1–66 · 1963–70",
        "open": True,
        "links": [L("The series", "xmen_1963_2011")],
        "intro": "Lee and Kirby for nineteen issues, then a rotating bench "
                 "until Roy Thomas and Neal Adams close it out. Historically "
                 "essential, famously skippable — the star ratings are honest "
                 "about which is which.",
        "items": urange(1, 66),
    },
    {
        "id": "reprints", "title": "The reprint years", "sub": "#67–93 · 1970–75",
        "links": [L("The series", "xmen_1963_2011")],
        "items": [it("reprints", "X-Men #67–93", "◆",
                     "Twenty-seven issues of reprints while the book was on "
                     "life support. Nothing new inside; counted so the run is "
                     "complete, skipped by everyone.", 0, 27, 1)],
    },
    {
        "id": "allnew", "title": "Giant-Size and the All-New team",
        "sub": "1975–80 · #94–128",
        "links": [L("Giant-Size X-Men", "giantsize_xmen_1975_2005"),
                  L("The series", "xmen_1963_2011")],
        "intro": "Wein and Cockrum build the new team in one Giant-Size issue, "
                 "Claremont takes the book the issue after, and does not let "
                 "go for sixteen years.",
        "items": [it("gsx1", "Giant-Size X-Men", "#1",
                     "The All-New, All-Different team debuts", 2)]
                 + urange(94, 128),
    },
    {
        "id": "phoenix", "title": "Dark Phoenix and Days of Future Past",
        "sub": "#129–143 · 1980–81 · Claremont and Byrne at full power",
        "links": [L("The series", "xmen_1963_2011")],
        "items": urange(129, 143),
    },
    {
        "id": "eighties", "title": "Paul Smith to the Trial of Magneto",
        "sub": "#144–200 · 1981–85 · with the graphic novel and the Wolverine series",
        "links": [L("The series", "xmen_1963_2011"),
                  L("God Loves, Man Kills", "xmen_god_loves_man_kills_extended_cut_2020"),
                  L("Wolverine (1982)", "wolverine_1982"),
                  L("Kitty Pryde & Wolverine", "kitty_pryde_and_wolverine_1984_1985")],
        "items": weave(
            urange(144, 200),
            ("xm-u167", it("glmk", "God Loves, Man Kills", "◆",
                           "Marvel Graphic Novel #5 — outside continuity, and "
                           "one of the two or three best X-Men stories ever "
                           "told", 2, 1)),
            ("xm-u171", it("wolv82", "Wolverine", "#1–4",
                           "The Claremont/Miller series — read before the "
                           "Japan issues that follow", 2, 4)),
            ("xm-u192", it("kpw", "Kitty Pryde and Wolverine", "#1–6",
                           "", 0, 6, 1)),
        ),
    },
    {
        "id": "massacre", "title": "The Massacre to Inferno",
        "sub": "#201–243 · 1986–89 · the crossover era begins",
        "links": [L("The series", "xmen_1963_2011"),
                  L("X-Factor", "xfactor_1986_1998"),
                  L("New Mutants", "new_mutants_1983_1991")],
        "items": weave(
            urange(201, 243),
            ("xm-u211", it("massacre", "Mutant Massacre, the other chapters", "◆",
                           "X-Factor #9–11, New Mutants #46, Thor #373–374, "
                           "Power Pack #27, Daredevil #238 — around Uncanny "
                           "#210–213", 1, 8)),
            ("xm-u227", it("fotm", "Fall of the Mutants, the other chapters", "◆",
                           "X-Factor #24–26 and New Mutants #59–61 — parallel "
                           "stories, no interleave needed", 0, 6, 1)),
            ("xm-u242", it("inferno", "Inferno, the other chapters", "◆",
                           "X-Factor #36–39 and New Mutants #71–73, interleaved "
                           "with Uncanny #240–243", 1, 7)),
        ),
    },
    {
        "id": "outback", "title": "The Outback and X-Tinction",
        "sub": "#244–280 · 1989–91",
        "links": [L("The series", "xmen_1963_2011"),
                  L("X-Factor", "xfactor_1986_1998"),
                  L("New Mutants", "new_mutants_1983_1991")],
        "items": weave(
            urange(244, 280),
            ("xm-u270", it("xtinction", "X-Tinction Agenda, the other chapters", "◆",
                           "New Mutants #95–97 and X-Factor #60–62 — the order "
                           "runs Uncanny, New Mutants, X-Factor each round", 1, 6)),
            ("xm-u280", it("muir", "The Muir Island Saga concludes", "◆",
                           "X-Factor #69–70, straight after Uncanny #280", 0, 2)),
        ),
    },
    {
        "id": "bluegold", "title": "Blue and Gold",
        "sub": "1991–95 · Uncanny #281–321 in pairs with X-Men #1–41",
        "links": [L("Uncanny", "xmen_1963_2011"),
                  L("X-Men (1991)", "xmen_1991_2001"),
                  L("X-Factor", "xfactor_1986_1998"),
                  L("X-Force", "xforce_1991_2002")],
        "intro": "Two flagships from here: Jim Lee's X-Men #1 launches beside "
                 "Uncanny and the two run in lockstep for a decade. Read in "
                 "pairs — each month's Uncanny, then its X-Men.",
        "items": weave(
            pairs(urange(281, 321), xrange2(1, 41)),
            ("xm-x16", it("xcs", "X-Cutioner's Song, the other chapters", "◆",
                          "X-Factor #84–86 and X-Force #16–18 — twelve parts "
                          "in all, cycling Uncanny, X-Factor, X-Men, X-Force",
                          1, 6)),
            ("xm-x25", it("fatal", "Fatal Attractions, the other chapters", "◆",
                          "X-Factor #92, X-Force #25, Wolverine #75, Excalibur "
                          "#71 — around Uncanny #304 and X-Men #25", 1, 4)),
        ),
    },
    {
        "id": "aoa", "title": "The Age of Apocalypse",
        "sub": "1995 · four months where every book became something else",
        "links": [L("X-Men: Alpha", "xmen_alpha_1995"),
                  L("X-Men: Omega", "xmen_omega_1_1995"),
                  L("The Chosen", "age_of_apocalypse_the_chosen_1995")],
        "items": [
            it("aoa-alpha", "X-Men: Alpha", "#1", "The world ends; the event begins", 2),
            it("aoa-line", "The Age of Apocalypse titles", "◆",
               "Every X-book replaced for four issues each — Astonishing, "
               "Amazing, Weapon X, Generation Next, Factor X, Gambit and the "
               "X-Ternals, X-Calibre, X-Man, X-Universe", 1, 36),
            it("aoa-omega", "X-Men: Omega", "#1", "The event concludes", 2),
        ],
    },
    {
        "id": "nineties", "title": "Onslaught to Eve of Destruction",
        "sub": "1995–2001 · Uncanny #322–393 in pairs with X-Men #42–113",
        "links": [L("Uncanny", "xmen_1963_2011"),
                  L("X-Men (1991)", "xmen_1991_2001")],
        "items": weave(
            pairs(urange(322, 393), xrange2(42, 113)),
            ("xm-x55", it("onslaught", "Onslaught, the core chapters", "◆",
                          "Onslaught: X-Men, Onslaught: Marvel Universe, "
                          "Onslaught: Epilogue — around X-Men #55–56", 1, 3)),
            ("xm-u346", it("ozt", "Operation: Zero Tolerance, the other chapters", "◆",
                           "X-Force, Generation X, Wolverine and Cable chapters "
                           "— parallel, dip in as curiosity demands", 0, 8, 1)),
        ),
    },
    {
        "id": "morrison", "title": "Morrison's New X-Men",
        "sub": "#114–156 · 2001–04 · read it straight",
        "links": [L("New X-Men", "new_xmen_2001_2004")],
        "intro": "The same series, renamed. Morrison runs #114–154 as one long "
                 "novel and it reads best with nothing interleaved; #155–156 "
                 "close the volume out.",
        "items": xrange2(114, 156),
    },
    {
        "id": "meanwhile", "title": "Uncanny in the meantime",
        "sub": "#394–443 · 2001–04 · runs alongside Morrison, largely separate",
        "links": [L("The series", "xmen_1963_2011")],
        "intro": "Casey then Austen. If you abridge anywhere in the whole "
                 "list, abridge here.",
        "items": urange(394, 443),
    },
    {
        "id": "astonishing", "title": "Whedon's Astonishing X-Men",
        "sub": "#1–24 · 2004–08 · plus the Giant-Size finale",
        "links": [L("Astonishing", "astonishing_xmen_2004_2013")],
        "items": [it("ast%d" % n, "Astonishing X-Men", "#%d" % n,
                     "“Gifted” begins — Whedon and Cassaday" if n == 1 else "",
                     2 if n == 1 else 0) for n in range(1, 25)]
                 + [it("gsax", "Giant-Size Astonishing X-Men", "#1",
                       "The run's finale", 1)],
    },
    {
        "id": "reload", "title": "Reload to Messiah Complex",
        "sub": "2004–08 · Uncanny #444–494 in pairs with X-Men #157–207",
        "links": [L("Uncanny", "xmen_1963_2011"),
                  L("X-Men vol. 2", "xmen_2004_2008"),
                  L("House of M", "house_of_m_2005"),
                  L("Deadly Genesis", "xmen_deadly_genesis_2005_2006"),
                  L("Messiah Complex", "xmen_messiah_complex_2007_2008")],
        "items": weave(
            pairs(urange(444, 494), xrange2(157, 207)) + urange(495, 499),
            ("xm-x174", it("hom", "House of M", "#1–8",
                           "The 2005 event — the line pivots on it", 2, 8)),
            ("xm-u474", it("genesis", "X-Men: Deadly Genesis", "#1–6",
                           "Leads straight into Uncanny #475", 1, 6)),
            ("xm-u491", it("mc", "Messiah Complex, the other chapters", "◆",
                           "The one-shot, New X-Men #44–46 and X-Factor #25–27, "
                           "interleaved with Uncanny #492–494 and X-Men "
                           "#205–207", 2, 8)),
        ),
    },
    {
        "id": "utopia", "title": "San Francisco to Schism",
        "sub": "2008–11 · Uncanny #500–544 in pairs with Legacy #208–275",
        "links": [L("Uncanny", "xmen_1963_2011"),
                  L("X-Men: Legacy", "xmen_legacy_2008_2012"),
                  L("Second Coming", "xmen_second_coming_2010"),
                  L("Schism", "xmen_schism_2011")],
        "items": weave(
            pairs(urange(500, 543), xrange2(208, 251))
            + [it("schism%d" % n, "X-Men: Schism", "#%d" % n,
                  "The split that defines the next decade" if n == 1 else "",
                  1 if n == 1 else 0) for n in range(1, 6)]
            + [u(544)] + xrange2(252, 275),
            ("xm-u513", it("utopia-x", "Utopia, the crossover chapters", "◆",
                           "Dark Avengers/Uncanny X-Men: Utopia and Exodus, "
                           "around Uncanny #513–514", 0, 4, 1)),
            ("xm-u525", it("second", "Second Coming, the other chapters", "◆",
                           "The one-shots and the X-Force, New Mutants and "
                           "X-Men chapters, interleaved with Uncanny #523–525 "
                           "and Legacy #235–237", 2, 10)),
        ),
    },
    {
        "id": "wilderness", "title": "The wilderness years",
        "sub": "2011–19 · one row per run — the line fragments",
        "links": [L("Uncanny (2011)", "uncanny_xmen_2011_2012"),
                  L("Wolverine & the X-Men", "wolverine_and_the_xmen_2011_2014"),
                  L("AvX", "avengers_vs_xmen_2012"),
                  L("All-New X-Men", "allnew_xmen_2012_2015"),
                  L("Uncanny (2013)", "uncanny_xmen_2013_2015"),
                  L("X-Men (2013)", "xmen_2013_2015"),
                  L("Extraordinary", "extraordinary_xmen_2015_2017"),
                  L("Gold", "xmen_gold_2017_2018"),
                  L("Blue", "xmen_blue_2017_2018"),
                  L("Uncanny (2018)", "uncanny_xmen_2018_2019")],
        "intro": "After Schism the line splits into a dozen books and no one "
                 "reads it straight through, so this era is one row per run "
                 "rather than per issue. Say the word and any of these gets "
                 "the per-issue treatment.",
        "items": [
            run("w-unc2011", "Uncanny X-Men (2011)", "#1–20", 20,
                "Gillen — Cyclops's Utopia side", 0),
            run("w-watx", "Wolverine & the X-Men", "#1–42", 42,
                "Aaron — the school side, and the era's best book", 0),
            run("w-avx", "Avengers vs. X-Men", "#0–12", 13,
                "The 2012 event the era bends around", 0),
            run("w-anxm", "All-New X-Men", "#1–41", 41,
                "Bendis begins — the original five, displaced", 0),
            run("w-unc2013", "Uncanny X-Men (2013)", "#1–35", 35,
                "Bendis — the revolution side"),
            run("w-bota", "Battle of the Atom", "#1–2", 2,
                "Bookends of the 2013 crossover; the chapters run through the "
                "Bendis books"),
            run("w-x2013", "X-Men (2013)", "#1–26", 26, "Brian Wood's team book"),
            run("w-extra", "Extraordinary X-Men", "#1–20", 20,
                "Lemire, after Secret Wars"),
            run("w-anxm2", "All-New X-Men (2015)", "#1–19", 19, ""),
            run("w-unc2016", "Uncanny X-Men (2016)", "#1–19", 19, ""),
            run("w-gold", "X-Men Gold", "#1–36", 36, "ResurrXion, the Kitty side"),
            run("w-blue", "X-Men Blue", "#1–36", 36, "ResurrXion, the original five"),
            run("w-ast17", "Astonishing X-Men (2017)", "#1–17", 17, ""),
            run("w-unc2018", "Uncanny X-Men (2018)", "#1–22", 22,
                "Disassembled, then the road to the ending", 0),
            run("w-red18", "X-Men Red (2018)", "#1–11", 11, "Taylor's Jean book"),
        ],
    },
    {
        "id": "krakoa", "title": "Krakoa",
        "sub": "2019–24 · House of X to the fall",
        "links": [L("House of X", "house_of_x_2019"),
                  L("Powers of X", "powers_of_x_2019_2020"),
                  L("X-Men (2019)", "xmen_2019_2021"),
                  L("Inferno", "inferno_2021_2022"),
                  L("X-Men (2021)", "xmen_2021_2024"),
                  L("Immortal X-Men", "immortal_xmen_2022_2023"),
                  L("Fall of the House of X", "fall_of_the_house_of_x_2024"),
                  L("Rise of the Powers of X", "rise_of_the_powers_of_x_2024")],
        "intro": "Hickman resets everything in twelve issues, read in the "
                 "published interleave. The spine after that is X-Men, "
                 "Inferno, Immortal, and the two closing minis; the wider "
                 "line is optional rows at the end.",
        "items":
            [it("hoxpox%d" % i, t, n,
                "Read in this order — the two series interleave" if i == 1 else "",
                2 if i == 1 else 0)
             for i, (t, n) in enumerate([
                 ("House of X", "#1"), ("Powers of X", "#1"), ("Powers of X", "#2"),
                 ("House of X", "#2"), ("House of X", "#3"), ("Powers of X", "#3"),
                 ("House of X", "#4"), ("Powers of X", "#4"), ("House of X", "#5"),
                 ("Powers of X", "#5"), ("House of X", "#6"), ("Powers of X", "#6"),
             ], start=1)]
            + [it("x19-%d" % n, "X-Men (2019)", "#%d" % n,
                  "Hickman's flagship" if n == 1 else "", 1 if n == 1 else 0)
               for n in range(1, 12)]
            + [it("xos", "X of Swords", "◆",
                  "Creation, the chapters across the line, Destruction — 22 "
                  "parts; X-Men #12–15 fall inside it", 1, 18)]
            + [it("x19-%d" % n, "X-Men (2019)", "#%d" % n) for n in range(12, 22)]
            + [it("hg21", "The Hellfire Gala, first night", "◆",
                  "Planet-Size X-Men #1 is the one that matters", 1, 1)]
            + [it("inf-%d" % n, "Inferno", "#%d" % n,
                  "Hickman closes his ledger" if n == 1 else "", 1 if n == 1 else 0)
               for n in range(1, 5)]
            + [it("x21-%d" % n, "X-Men (2021)", "#%d" % n,
                  "Duggan's team, after the Gala" if n == 1 else "")
               for n in range(1, 36)]
            + [it("imm-%d" % n, "Immortal X-Men", "#%d" % n,
                  "Gillen — the Quiet Council, and the era's spine from here"
                  if n == 1 else "", 1 if n == 1 else 0)
               for n in range(1, 11)]
            + [it("sos", "Sins of Sinister", "◆",
                  "The one-shot, three three-issue minis and Dominion — a "
                  "ten-part detour the line takes together", 1, 11)]
            + [it("imm-%d" % n, "Immortal X-Men", "#%d" % n) for n in range(11, 19)]
            + [y for k in range(1, 6) for y in (
                  it("fohx-%d" % k, "Fall of the House of X", "#%d" % k,
                     "The era ends in pairs — Fall, then Rise, each month"
                     if k == 1 else "", 1 if k == 1 else 0),
                  it("ropx-%d" % k, "Rise of the Powers of X", "#%d" % k))]
            + [
                run("k-marauders", "Marauders", "#1–27", 27, "The wider line, if you want it"),
                run("k-excalibur", "Excalibur", "#1–26", 26, ""),
                run("k-xforce", "X-Force", "#1–49", 49, ""),
                run("k-hellions", "Hellions", "#1–18", 18, ""),
                run("k-newmutants", "New Mutants", "#1–33", 33, ""),
                run("k-red", "X-Men Red (2022)", "#1–18", 18,
                    "Ewing's Arakko book — the best of the satellites"),
            ],
    },
    {
        "id": "ashes", "title": "From the Ashes",
        "sub": "2024–25 · X-Men and Uncanny in release order, then Exceptional",
        "links": [L("X-Men (2024)", "xmen_2024_present"),
                  L("Uncanny (2024)", "uncanny_xmen_2024_present"),
                  L("Exceptional", "exceptional_xmen_2024_2025"),
                  L("X-Manhunt Omega", "xmanhunt_omega_xmh_2025_present")],
        "items": weave(
            ash_flagships()
            + [it("ash-exceptional", "Exceptional X-Men", "#1",
                  "Ewing's Chicago book")]
            + [ash("e", n) for n in range(2, 14)],
            ("xm-ash-x13", it("ash-manhunt", "X-Manhunt, the other chapters", "◆",
                              "NYX #9, Storm #6, X-Factor #8, X-Force #9 and "
                              "X-Manhunt Omega #1 — around Uncanny #11 and "
                              "X-Men #13", 0, 5)),
        ),
    },
    {
        "id": "revelation", "title": "Age of Revelation",
        "sub": "2025 · the ongoing books give way to limited series",
        "links": [L("Overture", "xmen_age_of_revelation_overture_aor_2025_present"),
                  L("Amazing X-Men", "amazing_xmen_2025"),
                  L("Unbreakable X-Men", "unbreakable_xmen_2025"),
                  L("Book of Revelation", "xmen_book_of_revelation_2025"),
                  L("Finale", "xmen_age_of_revelation_finale_2025_present")],
        "items": [
            it("aor-0", "X-Men: Age of Revelation", "#0",
               "The prelude, published in July 2025"),
            it("aor-overture", "X-Men: Age of Revelation Overture", "#1",
               "The event begins"),
            it("aor-amazing", "Amazing X-Men", "#1–3",
               "MacKay — one of the event's three flagship titles", 0, 3),
            it("aor-unbreakable", "Unbreakable X-Men", "#1–3",
               "Simone — another of the three", 0, 3),
            it("aor-book", "X-Men: Book of Revelation", "#1–3",
               "MacKay — the event's core title", 0, 3),
            it("aor-line", "The other Age of Revelation titles", "◆",
               "Binary, Laura Kinney: Sabretooth, Longshots, Rogue Storm, "
               "Iron & Frost, Sinister's Six, The Last Wolverine, Omega Kids, "
               "Radioactive Spider-Man, Cloak or Dagger, Expatriate X-Men, "
               "Undeadpool and X-Vengers, three issues each, and the World of "
               "Revelation one-shot", 0, 40, 1),
            it("aor-finale", "X-Men: Age of Revelation Finale", "#1",
               "The event concludes"),
        ],
    },
    {
        "id": "tomorrow", "title": "Shadows of Tomorrow",
        "sub": "2026– · the current era, still being written",
        "links": [L("X-Men (2024)", "xmen_2024_present"),
                  L("Uncanny (2024)", "uncanny_xmen_2024_present")],
        "items": [
            it("sot-xmen", "X-Men (2024)", "ongoing",
               "MacKay's flagship, from #23 — per-issue rows when the era "
               "completes", 0, 0),
            it("sot-uncanny", "Uncanny X-Men (2024)", "ongoing",
               "Simone's book, from #22", 0, 0),
            it("sot-dnx", "DNX", "#1–5",
               "The 2026 event, with X-Men #35–41 and Fantastic Four "
               "#17–18. #5 is not out yet — due 18 November 2026", 0, 0),
        ],
    },
]


def main():
    ids = [x["id"] for s in SECTIONS for x in s["items"]]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, "duplicate ids: %s" % dupes[:8]

    # the spine must be complete: every issue of both lineages exactly once
    us = sorted(int(x["id"][4:]) for s in SECTIONS for x in s["items"]
                if x["id"].startswith("xm-u") and x["id"][4:].isdigit())
    # #67-93 are the reprint years, deliberately one collapsed row
    want = list(range(1, 67)) + list(range(94, 545))
    assert us == want, "Uncanny lineage has gaps: %d issues" % len(us)
    xs = sorted(int(x["id"][4:]) for s in SECTIONS for x in s["items"]
                if x["id"].startswith("xm-x") and x["id"][4:].isdigit())
    assert xs == list(range(1, 276)), "v2 lineage has gaps: %d issues" % len(xs)

    total = len(ids)
    issues = sum(x["w"] for s in SECTIONS for x in s["items"])

    prop = {
        "slug": SLUG,
        "title": "X-Men",
        "subtitle": "the comprehensive reading list — both flagships, complete",
        "kind": "comics",
        "popularity": 86,
        "year": "1963–",
        "blurb": "Every issue of the two flagship lineages from 1963 to the "
                 "Age of Revelation — about %d issues — with the crossovers "
                 "spliced in where you read them." % round(issues),
        "unit": {"one": "entry", "many": "entries"},
        "weightUnit": {"one": "issue", "many": "issues"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": "#8A6D1F" if False else "#B08A2E",
        "accentDark": "#E8C45C",
        "tiers": False,
        "notes": [
            ["Two spines, read in pairs.", "From 1991 the line has two "
             "flagships that ran in lockstep — Uncanny #281–393 against X-Men "
             "#1–113, ending together — so they are rowed in pairs: each "
             "month's Uncanny, then its X-Men. The same pairing carries "
             "2004–08 and 2008–11, and From the Ashes reads its two in "
             "release order. Everything else is one title at a time."],
            ["◆ marks chapters published outside the flagships.", "Crossovers "
             "are spliced in at the point you read them, sized by how many "
             "issues they are, never dumped at the end of a section."],
            ["The wilderness years are one row per run.", "After Schism the "
             "line fragments into a dozen books and nobody reads 2011–19 "
             "straight through. Each run is one row weighted by its issue "
             "count; say the word and any of them gets per-issue rows."],
            ["No spoilers.", "Notes say what an issue is — a debut, a creator "
             "boundary, an arc name — never what happens in it. The stars "
             "carry the “this one matters” signal."],
            ["Shadows of Tomorrow is ongoing.", "The current era gets placeholder "
             "rows weighing nothing; per-issue rows arrive when runs "
             "complete, so the list never carries invented issue counts."],
            "Series links resolve against Marvel's own database ids. Order "
            "and era boundaries assembled from the standard reading orders; "
            "issue ranges verified against Marvel's series listings.",
        ],
        "sections": SECTIONS,
    }

    out = pathlib.Path(__file__).resolve().parent.parent / "properties" / ("%s.json" % SLUG)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(prop, indent=2, ensure_ascii=False) + "\n")

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d entries, %d issues" % (len(SECTIONS), total, round(issues)))
    for s in SECTIONS:
        w = sum(x["w"] for x in s["items"])
        print("   %-38s %4d entries %5d issues" % (s["title"][:38], len(s["items"]), w))


if __name__ == "__main__":
    main()
