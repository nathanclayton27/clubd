#!/usr/bin/env python3
"""Generate properties/black-panther.json — the Black Panther reading list.

    python3 tools/make_black_panther.py

Sixty years of the mantle in main Marvel continuity, one row per issue: the
two Don McGregor arcs inside Jungle Action, Jack Kirby's own relaunch, the
1980s scraps, Christopher Priest's sixty-two issues, Reginald Hudlin's
forty-one, Shuri's twelve, the Hell's Kitchen detour, Ta-Nehisi Coates'
fifty, John Ridley's fifteen and Eve Ewing's ten.

WHERE THE NUMBERS COME FROM, AND WHY NONE OF THEM ARE GUESSED.
Every issue in this file is attested by a source that enumerates it, which is
almost always a collected edition's own contents list.
The generator parses the "Material collected" cells of Wikipedia's
`Black Panther collected editions` tables into a set of (series, volume,
issue) triples, and refuses to emit a row that is not in that set. So a
mistyped range does not ship a fake issue — it fails the build. Two smaller
sources fill gaps the collected-editions page does not cover:

  * `Jungle Action` — the vol. 2 issue range, and the fact that #23 is a
    reprint rather than a new chapter;
  * `Eve Ewing` — the bibliography line that closes the ninth volume at #10,
    which no collected edition on the other page enumerates.

The prose facts the notes lean on are asserted against the cached wikitext as
well (Kirby leaving at 12, Hudlin through 38, the fifteen-issue first volume,
the last thirteen Priest issues, the Klan arc's real ending). If Wikipedia is
rewritten under us, this generator stops rather than drifts.

THE FANTASTIC FOUR PROBLEM. He debuts in Fantastic Four #52-53 and comes back
in #54, #56 and #119 — and there is a Fantastic Four list in this catalogue
that carries those rows. Duplicating them here would put the same issue under
two ids and two sets of ticks, so this list carries none of them and says so
in a note and in the first section's intro. The prelude section is otherwise
exactly Marvel's own *Black Panther: The Early Marvel Years Omnibus* contents,
minus the Jungle Action issues, which are promoted to their own sections.

THE KIRBY DECISION, MADE RATHER THAN DODGED. The 1977 solo book is Tier 3 and
sits in publication order. Kirby was not continuing McGregor and nobody
continued Kirby; the abandoned "Panther vs. the Klan" story is picked back up
by Ed Hannigan in the volume's last three issues and finished in Marvel
Premiere #51-53, so those six issues are split off into their own Tier 2
section — they are the only ending Jungle Action has, and the Kirby twelve
are not.

UNWEIGHTED, like every comics list here: comics publish no per-issue reading
time, so no row carries `w` and there is no `weightUnit`.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop, wiki  # noqa: E402

SLUG = "black-panther"
CACHE = prop.ROOT / "scratch" / "blackpanther"

COLLECTED = "Black Panther collected editions"
JUNGLE = "Jungle Action"
EWING = "Eve Ewing"
CHARACTER = "Black Panther (character)"

_INDEX = json.loads((pathlib.Path(__file__).resolve().parent / "data"
                     / "marvel_series_index.json").read_text(encoding="utf-8"))


def S(slug):
    assert slug in _INDEX, "not in the Marvel index: %r" % slug
    return "https://www.marvel.com/comics/series/%s/%s" % (_INDEX[slug], slug)


def L(*pairs):
    return [{"label": a, "url": S(b)} for a, b in pairs]


# ------------------------------------------------------------- the sources --

DASHES = {"–": "-", "—": "-", "‒": "-", "−": "-"}


def flat(t):
    for a, b in DASHES.items():
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t)


def page(name):
    t = wiki.wikitext(name, cache_dir=CACHE)
    assert t, "could not fetch %r" % name
    return t


def unlink(t):
    """[[a|b]] -> b, [[a]] -> a. Titles in these tables are often linked."""
    t = re.sub(r"\[\[[^\]|]*\|([^\]]+)\]\]", r"\1", t)
    return re.sub(r"\[\[([^\]]+)\]\]", r"\1", t)


def normkey(t):
    t = t.lower().replace("&", "and").replace("'", "").replace("’", "")
    t = t.replace(".", "").strip()
    return re.sub(r"\s+", " ", t)


_CITE = re.compile(r"''(.+?)''\s*(?:\(?\bvol\.?\s*(\d+)\)?)?\s*#\s*", re.I)
_TOKEN = re.compile(r"(\d+(?:\.\d+)?)(?:\s*[-–—]\s*(\d+))?")
_SEP = re.compile(r"\s*(?:,|and)\s*")


def parse_citations(text):
    """(series, vol) -> {issue-string} for every `''Title'' (vol. N) #range`.

    The token loop stops at the first thing that is not an issue number, which
    is what keeps `#35-38, ''Annual'' #1` from swallowing the annual into the
    Black Panther set, and what keeps a trailing publication year out of it.
    """
    out = {}
    text = unlink(text)
    for m in _CITE.finditer(text):
        key = (normkey(m.group(1)), int(m.group(2)) if m.group(2) else None)
        pos = m.end()
        got = out.setdefault(key, set())
        while True:
            tm = _TOKEN.match(text, pos)
            if not tm:
                break
            a, b = tm.group(1), tm.group(2)
            if b is not None and "." not in a:
                lo, hi = int(a), int(b)
                assert lo <= hi <= lo + 600, "implausible range %s-%s" % (a, b)
                for n in range(lo, hi + 1):
                    got.add(str(n))
            else:
                got.add(a)
            pos = tm.end()
            sm = _SEP.match(text, pos)
            if not sm:
                break
            pos = sm.end()
    return out


ATTEST = {}


def attested(key, vol, issue):
    return (issue in ATTEST.get((key, vol), ())
            or issue in ATTEST.get((key, None), ()))


# -------------------------------------------------------------- the series --
# display title, the title the sources cite it under, volume, Marvel index slug

SERIES = {
    "tos":   ("Tales of Suspense", "tales of suspense", None, "tales_of_suspense_1959_1968"),
    "cap":   ("Captain America", "captain america", 1, "captain_america_1968_1996"),
    "avn":   ("Avengers", "avengers", 1, "avengers_1963_1996"),
    "dd":    ("Daredevil", "daredevil", 1, "daredevil_1964_1998"),
    "ddan":  ("Daredevil Annual", "daredevil annual", 1, "daredevil_annual_1967_1994"),
    "mtu":   ("Marvel Team-Up", "marvel team-up", None, None),
    "ast":   ("Astonishing Tales", "astonishing tales", None, "astonishing_tales_1970"),
    "ja":    ("Jungle Action", "jungle action", None, "jungle_action_1972_1976"),
    "bp1":   ("Black Panther (1977)", "black panther", 1, "black_panther_1977_1979"),
    "prem":  ("Marvel Premiere", "marvel premiere", None, "marvel_premiere_1972_1981"),
    "bp2":   ("Black Panther (1988)", "black panther", 2, "black_panther_1988"),
    "mcp":   ("Marvel Comics Presents", "marvel comics presents", None,
              "marvel_comics_presents_1988_1995"),
    "prey":  ("Black Panther: Panther's Prey", "black panther: panthers prey", None, None),
    "bp3":   ("Black Panther (1998)", "black panther", 3, "black_panther_1998_2003"),
    "dp":    ("Deadpool", "deadpool", 2, None),
    "crew":  ("The Crew", "the crew", None, "the_crew_2003_2004"),
    "bp4":   ("Black Panther (2005)", "black panther", 4, "black_panther_2005_2008"),
    "ann":   ("Black Panther Annual", "annual", None, "black_panther_annual_1_2008"),
    "bp5":   ("Black Panther (2009)", "black panther", 5, "black_panther_2009_2010"),
    "dw":    ("Doomwar", "doomwar", None, "doomwar_2010"),
    "klaws": ("Klaws of the Panther", "klaws of the panther", None, "klaws_of_the_panther_2010"),
    "mwf":   ("Black Panther: The Man Without Fear", "black panther: the man without fear",
              None, "black_panther_the_man_without_fear_2010_2011"),
    "mdma":  ("Black Panther: The Most Dangerous Man Alive",
              "black panther: the most dangerous man alive", None,
              "black_panther_the_most_dangerous_man_alive_2011_2012"),
    "bp6":   ("Black Panther (2016)", "black panther", 6, "black_panther_2016_2018"),
    "bp7":   ("Black Panther (2018)", "black panther", 7, "black_panther_2018_2021"),
    "bp8":   ("Black Panther (2021)", "black panther", 8, "black_panther_2021_2023"),
    "bp9":   ("Black Panther (2023)", "black panther", 9, "black_panther_2023_2024"),
    "wow":   ("Black Panther: World of Wakanda", "black panther: world of wakanda", None,
              "black_panther_world_of_wakanda_2016_2017"),
    "bpc":   ("Black Panther and the Crew", "black panther and the crew", None,
              "black_panther_and_the_crew_2017"),
    "llk":   ("Black Panther: Long Live the King", "black panther: long live the king", None,
              "black_panther_long_live_the_king_cmx_digital_comic_2017_2018"),
    "rise":  ("Rise of the Black Panther", "rise of the black panther", None,
              "rise_of_the_black_panther_2018"),
    "shuri": ("Shuri", "shuri", None, "shuri_2018_2019"),
}

MISSING = []


def rows(skey, nums, notes=None, stars=None, opts=None):
    """Rows for a run of issues, each checked against the parsed sources."""
    disp, cite, vol, _ = SERIES[skey]
    notes, stars, opts = notes or {}, stars or {}, opts or {}
    out = []
    for n in nums:
        key = str(n)
        if not attested(cite, vol, key):
            MISSING.append("%s %s#%s" % (cite, "vol %s " % vol if vol else "", key))
        out.append({
            "id": "%s-%s" % (prop.slug(disp), key.replace(".", "-")),
            "t": disp,
            "n": "#%s" % key,
            "note": notes.get(key, ""),
            "star": stars.get(key, 0),
            "opt": opts.get(key, 0),
            "url": "",
        })
    return out


def rng(a, b):
    return [str(n) for n in range(a, b + 1)]


# --------------------------------------------------------------- the notes --

N_CAP = {
    "97": "Captain America's feature, three issues before the book was renamed",
    "100": "Tales of Suspense becomes Captain America here",
}
# Keyed per title on purpose: Avengers #52 and Daredevil #52 are different
# issues, and one shared dict put the Avengers note on both of them.
N_AVN = {
    "52": "T'Challa joins the Avengers",
    "62": "Reprinted four years later as Jungle Action #5 — his first starring feature",
}
N_DD = {"69": "Reprinted mid-arc as Jungle Action #23"}
N_RAGE = {
    "6": "“Panther's Rage” begins — McGregor, Buckler and Billy Graham",
    "14": "The chapters get longer here, 18 to 19 pages",
}
N_KLAN = {
    "19": "“Panther vs. the Klan” begins",
    "24": "The last issue — the title was cancelled with the arc unfinished",
}
N_KIRBY = {"1": "Kirby writing, drawing and editing"}
N_PREM = {
    "13": "Ed Hannigan writing, Jerry Bingham pencilling",
    "14": "The Klan story is picked back up as a subplot",
    "51": "Where the Klan story finally ends, in an anthology title",
}
N_80S = {
    "1": "Peter B. Gillis and Denys Cowan",
    "13": "“Panther's Quest” — eight-page chapters inside the anthology",
    "37": "The last “Panther's Quest” chapter",
}
N_PREY = {"1": "McGregor and Dwayne Turner, square-bound"}
N_PRIEST1 = {"1": "Priest and Mark Texeira, under the Marvel Knights imprint"}
N_PRIEST2 = {"25": "Storm comes back into the book"}
N_KASPER = {"50": "Kasper Cole takes the lead; T'Challa becomes a supporting character"}
N_CREW = {"1": "Ran alongside the last Black Panther issues",
          "7": "Cancelled here"}
N_HUD1 = {
    "1": "Hudlin writing, John Romita Jr. pencilling",
    "7": "A House of M tie-in",
    "8": "Crosses with X-Men #175-176",
    "14": "“The Bride” begins",
}
N_HUD2 = {
    "19": "Seven issues of Civil War start here",
    "26": "“Four the Hard Way” — the Fantastic Four stint begins",
    "35": "Back to Wakanda for the last four",
}
N_AARON = {"39": "Jason Aaron takes over for the last three"}
N_SHURI5 = {"1": "Shuri's book — Hudlin scripting",
            "7": "Jonathan Maberry co-writes, then takes the book"}
N_DW = {"1": "With the Fantastic Four and the X-Men in it"}
N_MWF = {"513": "The numbering continues Daredevil's — Liss and Francavilla"}
N_MDMA = {"523.1": "A point-one issue; it sits after #523",
          "524": "The title changes here"}
N_C1 = {"1": "Coates and Brian Stelfreeze"}
N_C2 = {"166": "Marvel's legacy numbering — the same run, counting from 1966"}
N_C3 = {"1": "Coates again, with a new number one"}
N_RIDLEY = {"1": "John Ridley and Juann Cabal"}
N_EWING = {"1": "Eve Ewing and Chris Allen"}
N_WOW = {"1": "Coates with Roxane Gay, on the Dora Milaje"}
N_BPC = {"1": "Coates again, in Harlem"}
N_LLK = {"1": "Nnedi Okorafor"}
N_SHURI = {"1": "Okorafor again, with Shuri as the lead"}


def sections():
    out = []

    out.append({
        "id": "early", "title": "Before the solo book",
        "sub": "1968 into the 1970s — guest spots in other people's comics",
        "tier": 3,
        "intro": (
            "This is Marvel's own Black Panther: The Early Marvel Years omnibus, "
            "minus the Fantastic Four issues. He debuts in Fantastic Four #52–53 "
            "and comes back in #54, #56 and #119 — those rows are on the "
            "Fantastic Four list in this catalogue, and copying them here would give "
            "the same issue two sets of ticks.\n\n"
            "What is left is guest appearances in other people's books, so they are "
            "grouped by title the way the omnibus lists them rather than shuffled "
            "into one timeline. Nothing below depends on having read any of it."),
        "links": L(("Avengers", "avengers_1963_1996"),
                   ("Daredevil", "daredevil_1964_1998"),
                   ("Tales of Suspense", "tales_of_suspense_1959_1968"),
                   ("Astonishing Tales", "astonishing_tales_1970")),
        "items": (rows("tos", rng(97, 99), N_CAP)
                  + rows("cap", ["100"], N_CAP)
                  + rows("avn", ["52", "62", "73", "74", "77", "78", "79",
                                 "87", "112", "126"], N_AVN, {"52": 1})
                  + rows("dd", ["52", "69"], N_DD)
                  + rows("ddan", ["4"])
                  + rows("mtu", ["20"])
                  + rows("ast", ["6", "7"])),
    })

    out.append({
        "id": "rage", "title": "Panther's Rage",
        "sub": "1973–1975 — thirteen issues, and where the run actually starts",
        "tier": 1,
        "intro": (
            "Don McGregor was proofreading everything Marvel published when he "
            "pointed out that a comic called Jungle Action, set in Africa and "
            "starring white adventurers, was indefensible. Marvel gave him the book "
            "on one condition — keep it in Africa — and he handed it to the "
            "Black Panther.\n\n"
            "What he wrote is thirteen issues of one continuous story, planned and "
            "finished as a whole, which almost nobody in American superhero comics "
            "was doing in 1973. It is where Erik Killmonger comes from, and it is "
            "what every later writer goes back to. Start here."),
        "links": L(("Jungle Action", "jungle_action_1972_1976")),
        "items": rows("ja", rng(6, 18), N_RAGE, {"6": 2, "18": 1}),
    })

    out.append({
        "id": "klan", "title": "Panther vs. the Klan",
        "sub": "1976 — five issues, and no ending",
        "tier": 1,
        "intro": (
            "McGregor's second arc, and it does not finish: Jungle Action was "
            "cancelled at #24 with the story mid-flight. Marvel reasoned the "
            "character could still sell with a new approach, which is the next "
            "section.\n\n"
            "There is no #23 below because #23 is not a new chapter — it is a "
            "reprint of Daredevil #69, which is already in the section above. The "
            "ending this arc eventually got is two sections down."),
        "links": L(("Jungle Action", "jungle_action_1972_1976")),
        "items": rows("ja", ["19", "20", "21", "22", "24"], N_KLAN),
    })

    out.append({
        "id": "kirby", "title": "The Kirby run",
        "sub": "from January 1977 — the co-creator's own thing, and it ignores everything above",
        "tier": 3,
        "intro": (
            "Marvel relaunched the character in his own title with Jack Kirby — "
            "back from DC — writing, drawing and editing it. Kirby was not "
            "continuing McGregor. He was not continuing anything: it is twelve "
            "issues of Kirby at full volume, built around an artefact hunt, and it "
            "connects to nothing on either side of it.\n\n"
            "That is the honest answer to where it sits. It is Tier 3, it is in "
            "publication order because that is the only order it has, and skipping "
            "it costs you nothing later."),
        "links": L(("Black Panther (1977)", "black_panther_1977_1979")),
        "items": rows("bp1", rng(1, 12), N_KIRBY, {"1": 1}),
    })

    out.append({
        "id": "premiere", "title": "Where the Klan story ends",
        "sub": "1979–1980 — three years late, and by a different writer",
        "tier": 2,
        "intro": (
            "Kirby left after twelve issues. Ed Hannigan and Jerry Bingham took the "
            "last three, picked the abandoned Klan subplot back up — and were "
            "cancelled in turn, so the conclusion ran in Marvel Premiere, an "
            "anthology title, later the same year.\n\n"
            "McGregor wrote none of it. It is Tier 2 anyway, because it is the only "
            "ending those five Jungle Action issues have."),
        "links": L(("Black Panther (1977)", "black_panther_1977_1979"),
                   ("Marvel Premiere", "marvel_premiere_1972_1981")),
        "items": rows("bp1", rng(13, 15), N_PREM) + rows("prem", rng(51, 53), N_PREM),
    })

    out.append({
        "id": "eighties", "title": "The wilderness years",
        "sub": "1988–1991 — a miniseries, an anthology serial and a prestige book",
        "tier": 3,
        "intro": (
            "Nine years with no ongoing title, and then three things that are not "
            "one: a four-issue miniseries by Peter B. Gillis and Denys Cowan; "
            "“Panther's Quest”, which is McGregor again, published as "
            "twenty-five eight-page chapters inside the biweekly anthology Marvel "
            "Comics Presents and set in apartheid South Africa; and “Panther's "
            "Prey”, McGregor with Dwayne Turner.\n\n"
            "The Marvel Comics Presents rows are eight pages each, not whole issues. "
            "After this the character does not carry a book again until 1998."),
        "links": L(("Black Panther (1988)", "black_panther_1988"),
                   ("Marvel Comics Presents", "marvel_comics_presents_1988_1995")),
        "items": (rows("bp2", rng(1, 4), N_80S)
                  + rows("mcp", rng(13, 37), N_80S)
                  + rows("prey", rng(1, 4), N_PREY)),
    })

    out.append({
        "id": "priestone", "title": "Priest: The Client",
        "sub": "1998–2000 — the run everyone means",
        "tier": 1,
        "intro": (
            "Christopher Priest inherited a character with a reputation as a dull "
            "also-ran and rebuilt him as a head of state: Wakanda as a sovereign "
            "technological power, T'Challa as its king first and an Avenger a "
            "distant second, and a State Department attorney called Everett Ross "
            "narrating so that the reader has somebody to be.\n\n"
            "It is also, structurally, a political comedy. The first issue is "
            "deliberately hard to follow and the run spends sixty-two issues "
            "explaining itself. Coates calls this the classic run; if you read one "
            "Black Panther comic, read this one."),
        "links": L(("Black Panther (1998)", "black_panther_1998_2003")),
        "items": rows("bp3", rng(1, 17), N_PRIEST1, {"1": 2}),
    })

    out.append({
        "id": "priesttwo", "title": "Priest: Enemy of the State",
        "sub": "2000–2001 — the run at full tilt",
        "tier": 1,
        "intro": (
            "The middle stretch, and the point at which the shape of the thing "
            "becomes clear. Storm comes back into the book at #25.\n\n"
            "The Deadpool issue at the end is the other half of a crossover, "
            "collected inside the run by Marvel's own omnibus. It is optional."),
        "links": L(("Black Panther (1998)", "black_panther_1998_2003")),
        "items": rows("bp3", rng(18, 35), N_PRIEST2) + rows("dp", ["44"], {
            "44": "The Deadpool half of a crossover — collected inside the run"},
            None, {"44": 1}),
    })

    out.append({
        "id": "priestthree", "title": "Priest: the last stretch",
        "sub": "2001–2003 — fourteen issues before the book changes lead",
        "tier": 1,
        "intro": (
            "The title kept changing shape to survive, and Priest kept writing it. "
            "These are the last fourteen issues with T'Challa as the lead."),
        "links": L(("Black Panther (1998)", "black_panther_1998_2003")),
        "items": rows("bp3", rng(36, 49)),
    })

    out.append({
        "id": "kasper", "title": "Kasper Cole",
        "sub": "the end of the Priest run — thirteen issues in which T'Challa is the supporting cast",
        "tier": 2,
        "intro": (
            "The last thirteen issues of Priest's run replace the lead. Kasper Cole "
            "is a New York police officer in a costume he has no claim to, and "
            "T'Challa is a supporting character in his own title.\n\n"
            "Same writer, same run, same ending — which is why it is Tier 2 "
            "rather than optional. But if you are here for T'Challa, this is where "
            "he is least present."),
        "links": L(("Black Panther (1998)", "black_panther_1998_2003")),
        "items": rows("bp3", rng(50, 62), N_KASPER),
    })

    out.append({
        "id": "crew", "title": "The Crew",
        "sub": "2003 — the spin-off, cancelled at seven",
        "tier": 3,
        "intro": (
            "Priest again, running alongside the final Black Panther issues and "
            "cancelled with #7. Kasper Cole is in it."),
        "links": L(("The Crew", "the_crew_2003_2004")),
        "items": rows("crew", rng(1, 7), N_CREW),
    })

    out.append({
        "id": "hudlinone", "title": "Hudlin: Who is the Black Panther?",
        "sub": "2005–2006 — the restart that outsold Priest",
        "tier": 2,
        "intro": (
            "Reginald Hudlin started the book over from the beginning with John "
            "Romita Jr. drawing, retelling the origin for people who had never "
            "picked the character up. It sold better than any Black Panther comic "
            "before it, Priest's included.\n\n"
            "It reads nothing like Priest — broader, louder, and much more "
            "interested in T'Challa as a global player than as a puzzle. The House "
            "of M tie-in and the X-Men crossover are inside the run rather than "
            "bolted onto it."),
        "links": L(("Black Panther (2005)", "black_panther_2005_2008")),
        "items": rows("bp4", rng(1, 18), N_HUD1, {"1": 1}),
    })

    out.append({
        "id": "hudlintwo", "title": "Hudlin: the Civil War years",
        "sub": "2006–2008 — twenty issues and the annual",
        "tier": 2,
        "intro": (
            "The middle of the run goes straight through Marvel's Civil War, and "
            "then spends five issues — “Four the Hard Way” — with "
            "T'Challa and Storm standing in for two absent members of the Fantastic "
            "Four. Those are Black Panther issues, so they are here; the Fantastic "
            "Four's own issues from those months are on the Fantastic Four list."),
        "links": L(("Black Panther (2005)", "black_panther_2005_2008"),
                   ("Annual", "black_panther_annual_1_2008")),
        "items": rows("bp4", rng(19, 38), N_HUD2) + rows("ann", ["1"], {
            "1": "Collected with #35-38"}, None, {"1": 1}),
    })

    out.append({
        "id": "aaron", "title": "Secret Invasion",
        "sub": "2008 — three issues by somebody else",
        "tier": 3,
        "intro": (
            "Jason Aaron closes the fourth volume with a war story tied into the "
            "line-wide Skrull event. Three issues, and then the book stops."),
        "links": L(("Black Panther (2005)", "black_panther_2005_2008")),
        "items": rows("bp4", rng(39, 41), N_AARON),
    })

    out.append({
        "id": "shurivol", "title": "Shuri wears the mantle",
        "sub": "2009–2010 — the fifth volume, and it is not T'Challa's",
        "tier": 3,
        "intro": (
            "Hudlin again, with T'Challa's sister Shuri as the Black Panther. "
            "Jonathan Maberry co-writes #7 and takes the book from there.\n\n"
            "The list follows the mantle rather than the man, which is why twelve "
            "issues with a different person under the mask are in it."),
        "links": L(("Black Panther (2009)", "black_panther_2009_2010")),
        "items": rows("bp5", rng(1, 12), N_SHURI5),
    })

    out.append({
        "id": "doomwar", "title": "Doomwar",
        "sub": "2010 — six issues, plus a four-issue side book",
        "tier": 3,
        "intro": (
            "A crossover miniseries with the Fantastic Four and the X-Men in it, and "
            "the hinge between the Shuri book and where the character spends the "
            "next two years. Klaws of the Panther is a separate four-issue series "
            "from the same months and is marked optional."),
        "links": L(("Doomwar", "doomwar_2010"),
                   ("Klaws of the Panther", "klaws_of_the_panther_2010")),
        "items": rows("dw", rng(1, 6), N_DW) + rows(
            "klaws", rng(1, 4), None, None, {str(n): 1 for n in range(1, 5)}),
    })

    out.append({
        "id": "hellskitchen", "title": "The Man Without Fear",
        "sub": "2011–2012 — Daredevil's numbering, Daredevil's neighbourhood",
        "tier": 3,
        "intro": (
            "T'Challa takes over Daredevil's title at #513 and Daredevil's patch of "
            "New York with it: no Wakanda, no vibranium, a diner in Hell's Kitchen "
            "and a false name. David Liss writes; Francesco Francavilla draws the "
            "first stretch.\n\n"
            "The title becomes The Most Dangerous Man Alive at #524 and the "
            "numbering carries straight on. #523.1 is a point-one issue and sits "
            "where its number says it does."),
        "links": L(("The Man Without Fear", "black_panther_the_man_without_fear_2010_2011"),
                   ("The Most Dangerous Man Alive",
                    "black_panther_the_most_dangerous_man_alive_2011_2012")),
        "items": (rows("mwf", rng(513, 523), N_MWF)
                  + rows("mdma", ["523.1"] + rng(524, 529), N_MDMA)),
    })

    out.append({
        "id": "coatesone", "title": "A Nation Under Our Feet",
        "sub": "2016–2017 — Coates and Brian Stelfreeze",
        "tier": 1,
        "intro": (
            "Ta-Nehisi Coates' first twelve issues, and the book the modern "
            "character is built on. It opens by asking whether a country should have "
            "a king at all, from inside the king's head, and it does not let him off "
            "easily.\n\n"
            "It assumes almost nothing. If you want a starting point later than "
            "1973, this is the other one."),
        "links": L(("Black Panther (2016)", "black_panther_2016_2018")),
        "items": rows("bp6", rng(1, 12), N_C1, {"1": 2}),
    })

    out.append({
        "id": "coatestwo", "title": "Avengers of the New World",
        "sub": "2017–2018 — and the renumbering that lands mid-arc",
        "tier": 1,
        "intro": (
            "The second Coates arc, interrupted by Marvel's legacy renumbering: #18 "
            "is followed by #166, which is the same run counting from the "
            "character's first appearance in 1966 instead of from 2016. Nothing "
            "changes but the number on the cover."),
        "links": L(("Black Panther (2016)", "black_panther_2016_2018")),
        "items": rows("bp6", rng(13, 18) + rng(166, 172), N_C2),
    })

    out.append({
        "id": "coatesthree", "title": "The Intergalactic Empire of Wakanda",
        "sub": "2018–2021 — twenty-five issues, in space",
        "tier": 1,
        "intro": (
            "Coates' second volume is a space opera, and it is a harder sell than "
            "the first: it starts a long way from Wakanda and takes its time telling "
            "you why. It is also where he finishes what he started.\n\n"
            "Read it after the first volume. It does not work cold."),
        "links": L(("Black Panther (2018)", "black_panther_2018_2021")),
        "items": rows("bp7", rng(1, 25), N_C3, {"1": 1}),
    })

    out.append({
        "id": "around", "title": "Around the Coates run",
        "sub": "2016–2019 — five spin-offs, none of them load-bearing",
        "tier": 3,
        "intro": (
            "Books that ran alongside. World of Wakanda is Coates with Roxane Gay on "
            "the Dora Milaje; Black Panther and the Crew is Coates again, on a "
            "police-killing story in Harlem; Long Live the King and Shuri are both "
            "Nnedi Okorafor; Rise of the Black Panther goes back to the early "
            "years.\n\n"
            "The main run does not refer back to any of them."),
        "links": L(("World of Wakanda", "black_panther_world_of_wakanda_2016_2017"),
                   ("Black Panther and the Crew", "black_panther_and_the_crew_2017"),
                   ("Long Live the King",
                    "black_panther_long_live_the_king_cmx_digital_comic_2017_2018"),
                   ("Rise of the Black Panther", "rise_of_the_black_panther_2018"),
                   ("Shuri", "shuri_2018_2019")),
        "items": (rows("wow", rng(1, 6), N_WOW)
                  + rows("bpc", rng(1, 6), N_BPC)
                  + rows("llk", rng(1, 6), N_LLK)
                  + rows("rise", rng(1, 6))
                  + rows("shuri", rng(1, 10), N_SHURI)),
    })

    out.append({
        "id": "ridley", "title": "John Ridley",
        "sub": "2021–2023 — fifteen issues, and it is a spy story",
        "tier": 2,
        "intro": (
            "Ridley's run is espionage: a king with an intelligence service, and "
            "what he has been using it for. Juann Cabal draws the first arc.\n\n"
            "It follows Coates directly and reads better for it."),
        "links": L(("Black Panther (2021)", "black_panther_2021_2023")),
        "items": rows("bp8", rng(1, 15), N_RIDLEY),
    })

    out.append({
        "id": "ewing", "title": "Eve Ewing",
        "sub": "2023–2024 — ten issues, and the last ongoing so far",
        "tier": 2,
        "intro": (
            "Eve Ewing and Chris Allen — the first Black woman to write the "
            "book. Ten issues.\n\n"
            "This is the end of the list, not the end of the story. Anything newer "
            "than this is not here yet."),
        "links": L(("Black Panther (2023)", "black_panther_2023_2024")),
        "items": rows("bp9", rng(1, 10), N_EWING),
    })

    return out


# --------------------------------------------------------------- the prose --

PROSE = [
    (CHARACTER, "Kirby left the series after only 12 issues"),
    (CHARACTER, "Black Panther ran 15 issues"),
    (CHARACTER, "The last 13 issues of Priest's series (#50-62)"),
    (CHARACTER, "initially written by filmmaker Reginald Hudlin (through issue #38)"),
    (CHARACTER, "Jason Aaron concluded the fourth volume"),
    (CHARACTER, "Hudlin co-wrote issue #7 with Jonathan Maberry"),
    (CHARACTER, "he became the lead character in Daredevil beginning with issue #513"),
    (CHARACTER, "25 eight-page installments within the bi-weekly anthology series "
                "Marvel Comics Presents"),
    (JUNGLE, "ran in Jungle Action #6-24"),
    (JUNGLE, "except for issue #23, a reprint of Daredevil #69"),
    (JUNGLE, "was later picked up as a subplot in Black Panther #14-15"),
    (JUNGLE, "concluded in Marvel Premiere #51-53"),
    (EWING, "Black Panther Vol. 9 #1-10"),
]


def main():
    src = {name: page(name) for name in (COLLECTED, JUNGLE, EWING, CHARACTER)}

    for name in (COLLECTED, JUNGLE, EWING):
        for key, issues in parse_citations(src[name]).items():
            ATTEST.setdefault(key, set()).update(issues)
    assert len(ATTEST) > 30, "the collected-editions tables did not parse"

    clean = {name: flat(wiki.clean(t)) for name, t in src.items()}
    for name, needle in PROSE:
        assert flat(needle) in clean[name], \
            "source changed — %r no longer says %r" % (name, needle)

    SECTIONS = sections()
    assert not MISSING, (
        "%d issues are not attested by any source, so they are not going in the "
        "file: %s" % (len(MISSING), MISSING[:8]))

    total = sum(len(s["items"]) for s in SECTIONS)
    tiers = {1: 0, 2: 0, 3: 0}
    for s in SECTIONS:
        tiers[s["tier"]] += len(s["items"])
    for s in SECTIONS:
        assert s["items"], "empty section %s" % s["id"]
        for x in s["items"]:
            assert "w" not in x, "comics lists are unweighted (CLU-131)"

    ff = [x for s in SECTIONS for x in s["items"]
          if x["t"].lower().startswith("fantastic four")]
    assert not ff, "Fantastic Four rows belong to the Fantastic Four list: %s" % ff[:3]

    p = {
        "slug": SLUG,
        "title": "Black Panther",
        "subtitle": "The mantle in main Marvel continuity — T'Challa, "
                    "and Shuri while she wore it",
        "kind": "comics",
        "popularity": 70,
        "year": "1968–2024",
        "blurb": "%d issues from his first guest spots to the 2024 finale, in the "
                 "order they're meant to be read." % total,
        "unit": {"one": "issue", "many": "issues"},
        "verb": {"base": "read", "past": "read", "ing": "reading"},
        "accent": "#4E2A84",
        "accentDark": "#B08CE8",
        "tiers": True,
        "notes": [
            ["Tiers.",
             "1 is the readable path — McGregor, Priest and Coates, and nothing "
             "else. 2 is strongly recommended: Hudlin's run, the Kasper Cole "
             "stretch that ends Priest's, Ridley, Ewing, and the six issues that "
             "finish the Klan story. 3 is genuinely optional. The minimum viable "
             "path is Tier 1 alone."],
            ["One continuity, one mantle.",
             "All of this is main Marvel continuity — no Ultimate line, no "
             "what-ifs, no 2099. And the list follows the mantle rather than the "
             "man: Shuri is the Black Panther for the 2009 volume and Doomwar, so "
             "those issues are in, the same way every T'Challa volume is."],
            ["The Fantastic Four issues are not here, on purpose.",
             "He debuts in Fantastic Four #52–53 and returns in #54, #56 and "
             "#119. Those rows live on the Fantastic Four list in this catalogue; "
             "duplicating them would give one issue two ids and two sets of ticks. "
             "The 2006 stretch where T'Challa and Storm stand in on the team is "
             "different — those are Black Panther issues, and they are in."],
            ["Reading in Marvel Unlimited?",
             "Sections link to their Marvel series pages rather than to each issue, "
             "because Marvel only exposes the 20 most recent issues of a series to "
             "the outside world. The issue numbers tell you when to switch titles."],
            "Issue ranges machine-read from Wikipedia's Black Panther collected "
            "editions tables, with Jungle Action's own article for the vol. 2 range "
            "and the reprint at #23, and Eve Ewing's bibliography for the ninth "
            "volume. Every row is attested by a collected edition that names it; "
            "the generator refuses to emit one that is not. Series links resolve "
            "against Marvel's own series ids.",
        ],
        "sections": SECTIONS,
    }

    out = prop.write(p)
    print("wrote %s" % out.name)
    print("  %d sections, %d issues" % (len(SECTIONS), total))
    print("  tier 1: %d   tier 2: %d   tier 3: %d" % (tiers[1], tiers[2], tiers[3]))
    for s in SECTIONS:
        print("   T%d  %-34s %3d" % (s["tier"], s["title"][:34], len(s["items"])))


if __name__ == "__main__":
    main()
