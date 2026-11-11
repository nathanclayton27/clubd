#!/usr/bin/env python3
"""Generate properties/street-fighter.json.

    PYTHONIOENCODING=utf-8 python tools/make_street-fighter.py

Twenty games and six films, in release order, 1987 to October 2026. Every
fact below is read out of tools/data/street-fighter.json, collected by
scratch/agent-sf/collect.py from Wikipedia wikitext, Wikidata and
HowLongToBeat. Nothing is typed from memory; the asserts re-check every claim
the prose makes, and the sentences the notes paraphrase are stored whole so a
Wikipedia edit that removes one fails this file instead of quietly outliving
it.

WHAT COUNTS AS ONE GAME
-----------------------
This is the whole editorial question on a Street Fighter list, and it is not
close to arbitrary — the source answers it, in words, twice over.

The rule shipped here: **a row is a game Wikipedia documents in an article of
its own, inside the franchise's Main series.** Ports, bundled re-releases and
free updates the source folds into another game's article are not rows;
compilations that box up games already on this list are not rows either.

That rule is not mine. Both halves come off the page:

  * `List of Street Fighter video games` splits itself into "Main series"
    and "Other games", and says of the second: "These games are not part of
    the mainline Street Fighter series, but involve Street Fighter
    characters." The roster below is every Street Fighter game linked from
    the first section. Twenty of them.
  * Wikipedia NUMBERS the Street Fighter II versions, in their own leads, and
    the count runs to eight:

        Champion Edition   "the first of several updated versions of
                           Street Fighter II: The World Warrior (1991)"
        Hyper Fighting     "the third arcade version of Street Fighter II"
        Super SFII         "the fourth game in the Street Fighter II
                           sub-series of Street Fighter games"
        Super SFII Turbo   "the fifth installment in the Street Fighter II
                           sub-series"
        Hyper SFII         a port "in which players can control any versions
                           of the main characters from the five Street
                           Fighter II games previously released"
        HD Remix           "designed ... to be the sixth definitive version
                           of Street Fighter II, although it is in fact the
                           seventh"
        Ultra SFII         "the eighth definitive version of the game"

    One, three, four, five, seventh, eighth, and the two that fill the gaps.
    A source that counts to eight is not describing one game with revisions.
    So Street Fighter II is eight rows, and the notes say so on the page.

The same rule cuts the other way at the modern end, which is what makes it a
rule rather than a preference. `Street Fighter V: Arcade Edition`,
`Street Fighter V: Champion Edition`, `Ultra Street Fighter IV`,
`Super Street Fighter IV: 3D Edition` and `Street Fighter 6 Years 1-2
Fighters Edition` are all named in the same list article — and every one of
them is a redirect into another game's article, or not a link at all. Nobody
sits down to play Street Fighter V and then separately plays Champion
Edition; the source knows that and files it accordingly. Champion Edition
(1992) was a coin-op you had to find a different cabinet for, and the source
knows that too.

Length was not a reason to go either way: zombie-films ships 605 rows.

THE SUB-SERIES QUESTIONS, EACH ANSWERED BY THE SOURCE
-----------------------------------------------------
  Alpha / Zero       IN, one row per numbered game. `List of Street Fighter
                     video games` files the Alpha series under Main series.
                     The franchise article's lead used to agree, counting
                     "the other six main games in the series" — II, Alpha,
                     III, IV, V and 6 — but since 28 October 2026 it says
                     "the other five", which leaves Alpha out of the count.
                     That phrase links straight to the video-games list,
                     whose Main series still holds Alpha, and that section is
                     the rule. `Zero` is the same games'
                     Japanese title, not other games, so it is a note and not
                     a row. (`List of Street Fighter media` disagrees and
                     files Alpha under spin-offs; the video-games list is the
                     franchise article's own {{Main}} link and matches its
                     section headings, so it wins.)
  EX 1/2/3           OUT. Not a close call and not my call: the same list
                     article files EX under "Other games", the section that
                     opens "These games are not part of the mainline Street
                     Fighter series". The franchise article agrees — "Capcom
                     co-produced a 3D fighting game Street Fighter EX with
                     Arika" — and Arika owns half that cast, which is why
                     those characters ended up in Fighting EX Layer instead.
  Marvel vs. Capcom  OUT, with SNK vs. Capcom, Tatsunoko vs. Capcom,
  and the crossovers Street Fighter X Tekken, X-Men vs. Street Fighter and
                     Capcom Fighting Evolution — all under "Other games".
                     They are crossovers with their own franchises attached;
                     Marvel vs. Capcom is somebody else's list.
  Final Fight        OUT, and it is the interesting one. The franchise
                     article says Street Fighter II came "following an
                     unsuccessful attempt to brand the 1989 beat 'em up game
                     Final Fight as the Street Fighter sequel", and the list
                     article says the series was "originally intended as
                     direct sequel to the original Street Fighter". The
                     attempt failed, Street Fighter II is the sequel, and
                     Final Fight sits under "Other games" — a beat 'em up
                     that shares a city, not a fighting game that shares a
                     line.
  Compilations       OUT: Street Fighter Collection, the Anniversary
                     Collection, Alpha Anthology and the 30th Anniversary
                     Collection are boxes holding rows that are already here.
  The 1995 tie-ins   OUT. The two `Street Fighter: The Movie` fighting games
                     are in "Other games" too.

WHAT COUNTS AS ONE FILM
-----------------------
The mirror of the same doctrine: **a film is a work Wikipedia files with
{{Infobox film}} in an article of its own.** Six qualify, and the test does
real work at both edges.

  in    Street Fighter II: The Animated Movie (1994), Street Fighter (1994),
        Street Fighter Alpha: The Animation (2000), Street Fighter Alpha:
        Generations (2005), Street Fighter: The Legend of Chun-Li (2009),
        Street Fighter (2026).
  out   Street Fighter IV: The Ties That Bind — `List of Street Fighter
        media` lists it under Films, but its "article" is a section of the
        Street Fighter IV page. Street Fighter: Round One: Fight! is listed
        there too and is a red link.
  out   TELEVISION, all of it. Street Fighter II V (1995) and the American
        cartoon (1995-97) are in that same media list's own
        ===Television series=== section; Street Fighter: Assassin's Fist
        (2014) and Street Fighter: Resurrection (2016) carry
        {{Infobox television}} and describe themselves as web series, whatever
        section they are filed under. Nathan asked for the games and the
        films. Keeping television off is also what keeps the sync medium
        honest — see below, there is no letter for it.

A live-action film IS a row at the end. It shipped as dated announced work
under Nathan's rule of 2026-08-26, and Wikipedia now says it "premiered on
October 12, 2026 ... and was theatrically released in the US by Paramount
Pictures on October 16, 2026, in IMAX" — so it is out, and the row is an
ordinary one. Undated work stays off, and nothing here is undated.

THE ROW MEDIUM, WHICH THIS LIST CANNOT DO WITHOUT
--------------------------------------------------
build.py groups cross-list ticks by a medium letter and used to derive it
from the property's kind string. On a "films & games" list that put every
row, films included, in the game lane — the-matrix lost five pairings to it
before anyone noticed. A row may now declare "m", and the kind is only a
fallback. On THIS list the fallback would be "g" for all twenty-six rows, so
every row here carries its own letter: "f" on the six films, "g" on the
twenty games. The assert below refuses to emit a row without one.

WEIGHTS: THIS LIST SHIPS UNWEIGHTED, AND THAT IS THE FINDING
-------------------------------------------------------------
HowLongToBeat has a main-story figure for all twenty games. They were all
fetched, they are all in tools/data/street-fighter.json, and they are not
used, because a number existing is not a number meaning something.

  * Nineteen of the twenty measure one run up an arcade ladder: 0.68 h for
    Street Fighter Alpha, 1.66 h for Super Street Fighter II Turbo. Nobody
    has ever finished Super Turbo in an hour and three quarters. The figure
    describes the credits roll, not the game — and Super Turbo is a game
    people have been playing for thirty years.
  * The twentieth is Street Fighter 6 at 17.34 h, and that one is real:
    World Tour is "a single-player story mode featuring a customizable
    player avatar exploring 3D environments". It is a different quantity
    wearing the same label. Weighted, one row would own a third of the whole
    bar, and the page would say something false in its most visible place.
  * The figures contradict each other on the same fights. Hyper Street
    Fighter II is a port of Super Turbo with a version selector bolted on;
    HowLongToBeat says 2.23 h against Super Turbo's 1.66 h. That gap is
    sampling noise, and a bar drawn from it would render the noise as fact.
  * Four of the twenty only answer to a title HowLongToBeat spells its own
    way, and 3rd Strike returns nothing at all under the name Wikipedia
    uses.

And the films would land among them: 1.7 h for the 1994 movie, sitting
indistinguishably beside a 1.66 h "playthrough" of Super Turbo, implying the
two are the same size of commitment.

All-or-nothing (CLU-131): a row with no `w` on a WEIGHTED list is silently
worth one hour, so there is no half-measure available — weight the films and
the list lies about the games. Unweighted, every row weighs 1, TOTALW ==
TOTAL, and the counters say "8 / 26", which is exactly the true statement
this list can make. The assert below refuses ANY `w`, including a `w: 0` on
the 2026 film: the front end turns weighting on when a single row carries a
number, and one zero would put "25 hours" on a page that measures nothing.

ORDER
-----
Release order, and the source supplies it twice. Each game's first release
date comes from its own infobox, and the resulting sequence is checked
against the {{Timeline of release years}} in `List of Street Fighter video
games`, whose 1992a/1992b/1997a/1997d/2008a/2008b/2010a/2010b keys settle
every within-year tie the same way. Films are placed by their own infobox
release dates, which is how the two 1994 films land after Super Turbo and in
the right order relative to each other.

Data:   scratch/agent-sf/fetch.py    -> scratch/agent-sf/wiki/
        scratch/agent-sf/hltb_probe.py, scratch/agent-sf/collect.py
                                     -> tools/data/street-fighter.json
Accent: scratch/agent-sf/accent.py
"""
import json
import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop
from gwlib.prop import join_bits, slug

SLUG = "street-fighter"
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "tools" / "data" / "street-fighter.json"

# section id -> (title, span, intro)
SECTIONS = ["first", "sf2", "alpha3", "gap", "sf4", "modern"]

# which section each row belongs to, keyed by the Wikipedia article the
# source linked. Release order does the sequencing inside them.
SECTION_OF = {
    "Street Fighter (video game)": "first",

    "Street Fighter II": "sf2",
    "Street Fighter II: Champion Edition": "sf2",
    "Street Fighter II: Hyper Fighting": "sf2",
    "Super Street Fighter II": "sf2",
    "Super Street Fighter II Turbo": "sf2",
    "Street Fighter II: The Animated Movie": "sf2",
    "Street Fighter (1994 film)": "sf2",

    "Street Fighter Alpha": "alpha3",
    "Street Fighter Alpha 2": "alpha3",
    "Street Fighter III": "alpha3",
    "Street Fighter III: 2nd Impact": "alpha3",
    "Street Fighter Alpha 3": "alpha3",
    "Street Fighter III: 3rd Strike": "alpha3",

    "Street Fighter Alpha: The Animation": "gap",
    "Hyper Street Fighter II": "gap",
    "Street Fighter Alpha: Generations": "gap",

    "Street Fighter IV": "sf4",
    "Super Street Fighter II Turbo HD Remix": "sf4",
    "Street Fighter: The Legend of Chun-Li": "sf4",
    "Super Street Fighter IV": "sf4",
    "Super Street Fighter IV: Arcade Edition": "sf4",

    "Street Fighter V": "modern",
    "Ultra Street Fighter II: The Final Challengers": "modern",
    "Street Fighter 6": "modern",
    "Street Fighter (2026 film)": "modern",
}

# Row notes. Every one paraphrases a sentence checked by `said()` in main();
# terse, and about what the entry IS rather than what happens in it.
NOTES = {
    "Street Fighter (video game)":
        "Capcom's first competitive fighting game, and where the six-button "
        "layout and the command special moves come from",
    "Street Fighter II":
        "The first one-on-one fighting game to give both players a roster to "
        "choose from, and the game the genre grew out of",
    "Street Fighter II: Champion Edition":
        "The first of eight versions the source counts: the four bosses become "
        "playable and both players may pick the same character",
    "Street Fighter II: Hyper Fighting":
        "The third, sold as an enhancement kit that dropped into a Champion "
        "Edition cabinet — faster, with new special moves",
    "Super Street Fighter II":
        "The fourth, and the first game on CP System II hardware: a full "
        "graphical overhaul and four new characters",
    "Super Street Fighter II Turbo":
        "The fifth, and the one tournaments still run. Super Combos arrive "
        "here, and so does Akuma",
    "Street Fighter II: The Animated Movie":
        "The anime feature, out four months ahead of the live-action one. The "
        "Alpha games took their look from it",
    "Street Fighter (1994 film)":
        "The live-action one, with Jean-Claude Van Damme as Guile and Raúl "
        "Juliá in his last theatrical role — one of two 1994 films adapting "
        "Street Fighter II",
    "Street Fighter Alpha":
        "The first all-new Street Fighter since 1991, set before II and "
        "carrying younger versions of its cast. Street Fighter Zero in Asia "
        "and Mexico",
    "Street Fighter Alpha 2":
        "Chain Combos out, Custom Combos in, and five more characters",
    "Street Fighter III":
        "A clean sheet on new CPS III hardware: every returning character "
        "dropped except Ryu and Ken, which is what the subtitle means",
    "Street Fighter III: 2nd Impact":
        "An update to New Generation — new mechanics, new characters, and the "
        "bonus rounds come back",
    "Street Fighter Alpha 3":
        "The third and last Alpha: three selectable fighting styles, and the "
        "roster out to 28 characters",
    "Street Fighter III: 3rd Strike":
        "The second and final update to III, and the one still played: five "
        "more characters, and the parry system improved",
    "Street Fighter Alpha: The Animation":
        "A direct-to-video anime feature built on Alpha 2. Street Fighter "
        "Zero: The Movie in Japan",
    "Hyper Street Fighter II":
        "The last arcade Street Fighter II, and a hybrid of all five that came "
        "before — pick which version of a character you want. Its cabinet is "
        "in the Museum of Modern Art's collection",
    "Street Fighter Alpha: Generations":
        "An anime feature made for the English-language market; Japan did not "
        "get it until it was bundled with the 2009 live-action film",
    "Street Fighter IV":
        "The first original main entry in eleven years, and the one that "
        "brought the series back",
    "Super Street Fighter II Turbo HD Remix":
        "Super Turbo redrawn in HD by UDON, with balance changes by design "
        "director David Sirlin — the seventh version of Street Fighter II by "
        "the source's own count",
    "Street Fighter: The Legend of Chun-Li":
        "A non-canonical spin-off, released as a theatrical tie-in to Street "
        "Fighter IV",
    "Super Street Fighter IV":
        "Ten more characters, sold standalone below full price, and said at "
        "the time to mark the definitive end of the IV line",
    "Super Street Fighter IV: Arcade Edition":
        "An update to Super, out in arcades a year before it reached consoles",
    "Street Fighter V":
        "PlayStation 4 and PC only, and 16 characters at launch — the story "
        "mode and thirty more fighters arrived afterwards",
    "Ultra Street Fighter II: The Final Challengers":
        "Super Turbo again, on Switch, in pixel art or HD. The eighth "
        "definitive version by the source's count, thirty years after the "
        "first game",
    "Street Fighter 6":
        "The seventh main entry, and the only one here with a real "
        "single-player campaign: World Tour is a story mode with your own "
        "avatar and a 3D world to walk around",
    # shipped as dated announced work with "Not out yet"; it opened in US
    # theatres on 16 Oct 2026, so the marker is gone
    "Street Fighter (2026 film)": (
        "Kitao Sakurai",
        "The third live-action feature, in IMAX from 16 October"),
}

INTROS = {
    "first": (
        "Where it starts", "1987",
        "One arcade cabinet, two playable characters and a punishing set of "
        "special-move inputs. It sold well enough to matter and nothing like "
        "what came next; everything below is downstream of the sequel."),
    "sf2": (
        "Street Fighter II", "1991–1994",
        "Five games and two films in four years. The five are the arcade "
        "versions Wikipedia numbers one to five in their own leads — each was "
        "a different cabinet you had to go and find, and the differences "
        "between them are still argued about. The films close the section "
        "because both of them adapt this game and both came out in 1994, four "
        "months apart."),
    "alpha3": (
        "Alpha and III", "1995–1999",
        "Two lines running at once. Alpha goes backwards, to a prequel cast "
        "drawn in the anime film's style; III goes forwards and throws almost "
        "everyone out. The two lines overlap year by year, and release order "
        "interleaves them."),
    "gap": (
        "Between III and IV", "2000–2005",
        "Eleven years pass between 3rd Strike and the next original game. "
        "What fills them: two direct-to-video anime features, and one last "
        "arcade Street Fighter II that exists to hold all the earlier ones "
        "at once."),
    "sf4": (
        "Street Fighter IV", "2008–2010",
        "The revival, and the busiest thirty months on this list. A new main "
        "entry, two updates to it, a hand-redrawn Super Turbo, and the second "
        "live-action film — released as a tie-in to the game at the top of "
        "the section."),
    "modern": (
        "V, 6, and back to the cinema", "2016–2026",
        "Two main entries, one more Street Fighter II, and a third live-action "
        "film."),
}


# --------------------------------------------------------------------------
# the cross-list overlap, computed rather than remembered
# --------------------------------------------------------------------------
def normt(t):
    """build.py's sync-key normalizer, copied so this generator computes the
    same groups the build will."""
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    t = re.sub(r"[^a-z0-9]+", " ", t).strip()
    return re.sub(r"^(the|a|an) ", "", t)


def year_of(x, n):
    """build.py's year-for-sync rule: the row number when it is a plain year,
    else an explicit y, else the single year named in the note."""
    if re.fullmatch(r"(18|19|20)\d{2}", n):
        return n
    explicit = str(x.get("y", ""))
    if re.fullmatch(r"(18|19|20)\d{2}", explicit):
        return explicit
    found = set(re.findall(r"\b((?:18|19|20)\d{2})\b", x.get("note") or ""))
    return found.pop() if len(found) == 1 else None


def catalogue_rows():
    """Every syncable row already shipped, read off disk so this cannot go
    stale: (slug, medium, normalized title, year, display title, qid)."""
    out = []
    for f in sorted((ROOT / "properties").glob("*.json")):
        if f.stem in ("index", "search", SLUG):
            continue
        p = json.loads(f.read_text(encoding="utf-8"))
        if p.get("secret"):
            continue
        kind = p.get("kind") or ""
        if not ("film" in kind or "game" in kind):
            continue
        prop_medium = "g" if "game" in kind else "f"
        for s in p.get("sections", []):
            for x in s.get("items", []):
                out.append((p["slug"], x.get("m") or prop_medium,
                            normt(x["t"]), year_of(x, str(x.get("n", ""))),
                            x["t"], x.get("q")))
    return out


def sync_report(mine):
    """Groups this list would join, plus the ones it would join if a row sat
    in the wrong medium lane.

    `mine` is [(normalized title, year, qid, medium letter)]. Each row here
    carries its own letter, so a film pairs with film lists and a game with
    game lists — the thing a "films & games" list could not do while one
    property-wide letter spoke for every row.
    """
    shipped = catalogue_rows()
    forms, would_have = {}, {}
    for title, year, qid, mymedium in mine:
        for oslug, omedium, otitle, oyear, odisp, oq in shipped:
            hit = ((year and oyear == year and otitle == title)
                   or (qid and oq and oq == qid))
            if not hit:
                continue
            key = "%s|%s|%s" % (title, year, omedium)
            (forms if omedium == mymedium else would_have).setdefault(
                key, []).append((oslug, odisp))
    return forms, would_have


def near_misses():
    """Shipped rows that NAME this franchise without being one of its rows.

    There is exactly one, and it is worth printing rather than hiding: the
    Mega Man list carries Street Fighter X Mega Man (2012). It is a Mega Man
    platformer with Street Fighter bosses, filed by the source under "Other
    games", so the roster rule excludes it and the pairing it would have made
    does not happen. A rule that never costs anything is not a rule.
    """
    return [(s, disp, y) for s, _m, t, y, disp, _q in catalogue_rows()
            if "street fighter" in t]


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    games = {g["target"]: g for g in data["games"]}
    films = {f["target"]: f for f in data["films"]}
    claims = data["claims"]

    def said(pagename, key, *musts):
        """A sentence the source gave us, re-checked for what we quote of it."""
        s = claims["%s|%s" % (pagename, key)]
        for m in musts:
            assert m in s, "%s.%s no longer says %r: %r" % (pagename, key, m, s)
        return s

    # ---- the roster is the source's, and the source still says so ----------
    assert len(games) == 20, sorted(games)
    assert len(films) == 6, sorted(films)
    assert set(SECTION_OF) == set(games) | set(films), \
        sorted(set(SECTION_OF) ^ (set(games) | set(films)))
    assert set(NOTES) == set(SECTION_OF), \
        sorted(set(NOTES) ^ set(SECTION_OF))

    # the Main series link set, checked whole: every link in that section is a
    # roster row, a named exclusion, or hardware. Wikipedia adding a game
    # fails this file rather than shipping a list that quietly misses it.
    linked = set(data["main_series_links"])
    assert set(games) <= linked, sorted(set(games) - linked)
    assert set(data["not_a_row"]) <= linked, sorted(data["not_a_row"])
    assert "Super Street Fighter IV: 3D Edition" in data["not_a_row"]
    assert sum(1 for v in data["not_a_row"].values()
               if v == "compilation") == 5, data["not_a_row"]

    # ---- the eight-version count, quoted from eight different places -------
    said("List of Street Fighter video games", "other_games",
         "not part of the mainline Street Fighter series")
    said("Street Fighter II: Champion Edition", "first_update",
         "first of several updated versions of Street Fighter II")
    said("Street Fighter II: Hyper Fighting", "third",
         "third arcade version of Street Fighter II")
    said("Street Fighter II: Hyper Fighting", "upgrade_kit", "enhancement kit")
    said("Super Street Fighter II", "fourth",
         "fourth game in the Street Fighter II sub-series")
    said("Super Street Fighter II", "cps2", "CP System II hardware")
    said("Super Street Fighter II Turbo", "fifth", "fifth installment")
    said("Hyper Street Fighter II", "five_games",
         "five Street Fighter II games previously released")
    said("Hyper Street Fighter II", "moma", "Museum of Modern Art")
    seventh = said("Super Street Fighter II Turbo HD Remix", "seventh",
                   "sixth definitive version of Street Fighter II",
                   "it is in fact the seventh")
    said("Super Street Fighter II Turbo HD Remix", "udon", "UDON Entertainment")
    said("Ultra Street Fighter II: The Final Challengers", "eighth",
         "eighth definitive version of the game")
    said("Ultra Street Fighter II: The Final Challengers", "switch",
         "for the Nintendo Switch")
    # eight versions, and eight rows carrying the Street Fighter II name
    sf2rows = [t for t in games
               if re.search(r"Street Fighter II\b", t) and "III" not in t]
    assert len(sf2rows) == 8, sorted(sf2rows)

    # ---- the exclusions, each with the sentence that excludes it -----------
    # "six" until 28 Oct 2026, "five" since: Alpha rests on the Main series
    # section alone now (see the docstring)
    said("Street Fighter", "other_main",
         "the other five main games in the series")
    said("Street Fighter", "ex_arika",
         "Capcom co-produced a 3D fighting game", "with Arika")
    said("Street Fighter", "final_fight_brand",
         "unsuccessful attempt to brand", "Final Fight as the Street Fighter "
         "sequel")
    said("List of Street Fighter video games", "final_fight_sequel",
         "originally intended as direct sequel to the original Street Fighter")
    assert data["not_a_film"] == {
        "Street Fighter IV#Anime": "a section of the Street Fighter IV article",
        "Street Fighter: Round One: Fight!": "no article — a red link",
        "Street Fighter: Assassin's Fist": "Infobox television — a web series",
    }, data["not_a_film"]
    # television, refused on the source's own filing rather than on taste
    tv = {t["target"]: t for t in data["tv"]}
    assert len(tv) == 4, sorted(tv)
    assert not any(t["infobox_film"] for t in tv.values()), \
        [k for k, v in tv.items() if v["infobox_film"]]
    assert tv["Street Fighter: Assassin's Fist"]["infobox_tv"], tv
    assert "web series" in tv["Street Fighter: Assassin's Fist"]["lead"], tv
    assert "web series" in tv["Street Fighter: Resurrection"]["lead"], tv
    assert not set(tv) & set(SECTION_OF), sorted(set(tv) & set(SECTION_OF))
    # the media list's own section names are where the film/TV line comes from
    secs = data["media_list_sections"]
    assert "Films" in secs and "Television series" in secs, secs

    # ---- per-row facts, re-checked -----------------------------------------
    said("Street Fighter (video game)", "first_competitive",
         "first competitive fighting game produced by the company")
    said("Street Fighter (video game)", "six_button",
         "six-button controls and the use of command-based special moves")
    said("Street Fighter", "choice_of_characters",
         "first one-on-one fighting game to give players a choice")
    said("Street Fighter", "ce_bosses",
         "four computer-controlled boss characters are human-playable",
         "two players can choose the same character")
    said("Super Street Fighter II", "four_new", "introduces four new characters")
    said("Street Fighter", "super_combos", "Super Combos", "Akuma")
    said("Street Fighter", "alpha_look", "heavily influenced by Street Fighter "
         "II: The Animated Movie")
    said("Street Fighter", "alpha_zero", "Street Fighter Zero in Asia and Mexico")
    said("Street Fighter", "custom_combos",
         "Chain Combo system in favor of Custom Combos")
    said("Street Fighter", "alpha2_five", "adds five new characters to the roster")
    said("Street Fighter Alpha", "prequel", "prequel to Street Fighter II")
    said("Street Fighter Alpha 3", "third_final", "third and final installment")
    said("Street Fighter", "alpha3_28", "roster to 28 characters")
    said("Street Fighter III", "discarded",
         "discarded every previous character except for Ryu and Ken")
    said("Street Fighter III: 2nd Impact", "update",
         "an update of Street Fighter III: New Generation")
    said("Street Fighter III: 2nd Impact", "bonus_rounds",
         "brings back bonus rounds")
    said("Street Fighter III: 3rd Strike", "second_final",
         "second and final updated version of Street Fighter III")
    said("Street Fighter III: 3rd Strike", "five_new",
         "adding five new characters")
    said("Street Fighter III: 3rd Strike", "parry",
         "improvements to the parry system")
    said("Super Street Fighter II Turbo HD Remix", "balance",
         "balance changes to gameplay")
    hiatus = said("Street Fighter IV", "hiatus", "a hiatus of eleven years")
    said("Super Street Fighter IV", "definitive_end", "definitive end")
    said("Street Fighter", "super4_ten", "includes ten additional characters")
    said("Super Street Fighter IV: Arcade Edition", "update",
         "is an update to Super Street Fighter IV")
    said("Super Street Fighter IV: Arcade Edition", "ported",
         "ported in 2011 for")
    said("Street Fighter V", "post_launch",
         "16 characters at launch", "30 additional characters were added")
    said("Street Fighter 6", "seventh_main", "seventh main entry")
    world = said("Street Fighter 6", "world_tour",
                 "single-player story mode featuring a customizable player "
                 "avatar")
    said("Street Fighter II: The Animated Movie", "anime_film",
         "adaptation of the 1991 video game")
    said("Street Fighter (1994 film)", "two_films",
         "one of two films released in 1994", "following Street Fighter II: "
         "The Animated Movie")
    said("Street Fighter (1994 film)", "cast",
         "Jean-Claude Van Damme", "final theatrical film role")
    # the film's own article spells him "Raul Julia"; the franchise article
    # spells him "Raúl Juliá", which is the man's name, so the note does too
    said("Street Fighter", "vandamme", "Jean-Claude Van Damme as Guile",
         "Raúl Juliá")
    said("Street Fighter Alpha: The Animation", "ova", "is a 2000 OVA",
         "Street Fighter Zero: The Movie")
    said("Street Fighter Alpha: Generations", "english_market",
         "produced specifically for the English-language market")
    said("Street Fighter: The Legend of Chun-Li", "spinoff",
         "non-canonical spin-off and theatrical tie-in to Street Fighter IV")
    sf26 = said("Street Fighter (2026 film)", "release",
                "theatrically released in the US",
                "October 16, 2026", "IMAX")
    # out now: the row carries no "Not out yet", and the note's "from 16
    # October" is the US theatrical date, not the 12 October premiere
    assert films["Street Fighter (2026 film)"]["runtime"], \
        films["Street Fighter (2026 film)"]
    said("Street Fighter (2026 film)", "third_live_action",
         "third live-action feature-length film")
    said("Street Fighter", "sixty_million", "60 million units")
    said("Street Fighter", "longest_running",
         "longest-running fighting game franchise")

    # ---- what the source says about dates, and about ids -------------------
    rows = []
    for target, rec in list(games.items()) + list(films.items()):
        medium = "g" if target in games else "f"
        y, mo, d, prec = rec["first"]
        assert prec == 3, \
            "%s has no full release date, only %s" % (target, rec["first"])
        assert rec["qid"] and re.fullmatch(r"Q[1-9]\d*", rec["qid"]), rec
        assert rec["p31_ok"], (target, rec["p31"])
        assert rec["gate_p577"] or rec["gate_desc"], (target, rec["pubyears"])
        x = {"id": "sf-%s-%d-%s" % (medium, y, slug(rec["t"])),
             "t": rec["t"], "n": str(y),
             # the row says which lane it belongs in; the list is both, and
             # the property-kind fallback would file all 26 as games
             "m": medium, "q": rec["qid"]}
        bits = NOTES[target]
        note = join_bits(*(bits if isinstance(bits, tuple) else (bits,)))
        assert note
        x["note"] = note
        rows.append((x, target, medium, (y, mo, d)))

    # exactly one row per work, no id collisions, and no weights anywhere
    assert len(rows) == 26, len(rows)
    ids = [x["id"] for x, _t, _m, _d in rows]
    assert len(ids) == len(set(ids)), sorted(ids)
    assert all(x.get("m") in ("f", "g") for x, _t, _m, _d in rows), \
        [x["id"] for x, _t, _m, _d in rows if x.get("m") not in ("f", "g")]
    assert all("w" not in x for x, _t, _m, _d in rows), \
        "a weight appeared on an unweighted list: one number turns weighting " \
        "on for the whole page and every other row silently becomes an hour"
    nf = sum(1 for _x, _t, m, _d in rows if m == "f")
    ng = sum(1 for _x, _t, m, _d in rows if m == "g")
    assert (nf, ng) == (6, 20), (nf, ng)

    # ---- release order, checked against the source's own timeline ----------
    rows.sort(key=lambda r: r[3])
    order = [t for _x, t, _m, _d in rows]
    assert order[0] == "Street Fighter (video game)", order[0]
    assert order[-1] == "Street Fighter (2026 film)", order[-1]
    tlseq = [(t, games[t]["timeline"][0]) for _x, t, m, _d in rows if m == "g"]
    assert all(k for _t, k in tlseq), tlseq
    assert [k for _t, k in tlseq] == sorted(k for _t, k in tlseq), tlseq
    # the two 1994 films sit after the 1994 game and in their own right order
    y94 = [t for _x, t, _m, (y, _mo, _d) in rows if y == 1994]
    assert y94 == ["Super Street Fighter II Turbo",
                   "Street Fighter II: The Animated Movie",
                   "Street Fighter (1994 film)"], y94
    # the two arithmetic claims the notes make, done from the dates
    anim, live = (films["Street Fighter II: The Animated Movie"]["first"],
                  films["Street Fighter (1994 film)"]["first"])
    gapm = (live[0] - anim[0]) * 12 + live[1] - anim[1]
    assert gapm == 4, (anim, live, gapm)          # "four months ahead"
    assert (games["Ultra Street Fighter II: The Final Challengers"]["first"][0]
            - games["Street Fighter (video game)"]["first"][0]) == 30

    # ---- the numbers that exist and are deliberately not used --------------
    hl = {t: games[t]["hltb"]["main_h"] for t in games}
    assert all(v for v in hl.values()), \
        [t for t, v in hl.items() if not v]      # all twenty have a figure
    sf6h = hl["Street Fighter 6"]
    ladder = sorted(v for t, v in hl.items() if t != "Street Fighter 6")
    assert sf6h > 5 * ladder[-1], (sf6h, ladder[-1])
    assert ladder[0] < 0.8 and ladder[-1] < 3.5, (ladder[0], ladder[-1])
    # the same fights, two different numbers
    assert hl["Hyper Street Fighter II"] > hl["Super Street Fighter II Turbo"], hl
    # what a weighted version of this page would have looked like: game hours
    # plus film runtimes, with one row owning a third of the bar
    film_h = round(sum(f["runtime"] / 60.0 for f in films.values()
                       if f["runtime"]), 2)
    total_if_weighted = round(sum(hl.values()) + film_h, 2)
    share = sf6h / total_if_weighted
    assert 0.30 < share < 0.36, (sf6h, total_if_weighted, share)

    # ---- sections -----------------------------------------------------------
    by_section = {k: [] for k in SECTIONS}
    for x, target, _m, _d in rows:
        by_section[SECTION_OF[target]].append((x, target))
    sections = []
    for key in SECTIONS:
        items = by_section[key]
        assert items, key
        title, span, intro = INTROS[key]
        g = sum(1 for _x, t in items if t in games)
        f = len(items) - g
        bits = []
        if g:
            bits.append("%d game%s" % (g, "" if g == 1 else "s"))
        if f:
            bits.append("%d film%s" % (f, "" if f == 1 else "s"))
        sections.append({
            "id": key, "title": title,
            "sub": "%s · %s" % (span, " · ".join(bits)),
            "intro": intro,
            "items": [x for x, _t in items]})
    sections[0]["open"] = True
    assert sum(len(s["items"]) for s in sections) == 26

    years = [int(x["n"]) for s in sections for x in s["items"]]
    assert years == sorted(years), years

    # ---- what this list shares with the rest of the catalogue ---------------
    mine = [(normt(x["t"]), x["n"], x["q"], x["m"]) for x, _t, _m, _d in rows]
    forms, would_have = sync_report(mine)
    assert not would_have, (
        "a Street Fighter row matches a shipped row on title+year or on work "
        "id but sits in the other medium lane (%s). Every row here carries "
        "its own 'm', so this means the per-row medium regressed in "
        "src/build.py or here — it is NOT fixed by renaming an id."
        % sorted(would_have))

    p = {
        "slug": SLUG,
        "title": "Street Fighter",
        "subtitle": "the games and the films, in the order they arrived",
        # films AND games; build.py reads this string for the medium chips on
        # the card wall and in search. The SYNC medium is per-row — see the
        # docstring before changing either.
        "kind": "films & games",
        # Band 80-89: a mainstream audience recognises the title on sight.
        # Street Fighter II is the fighting game nearly everyone has played,
        # the franchise has sold 60 million units and Guinness calls it the
        # longest-running in its genre, and a third live-action film opened in
        # October 2026. It sits over Final Fantasy (82) and Resident Evil (80),
        # under Grand Theft Auto (86) and Pokemon (88), and a shade over The
        # Matrix (83), the catalogue's other films-and-games list.
        # See POPULARITY.md.
        "popularity": 85,
        "year": "1987–2026",
        "blurb": "Twenty games and six films in release order — every arcade "
                 "version the source counts as its own, from the 1987 cabinet "
                 "to the film that opened in October 2026.",
        "unit": {"one": "entry", "many": "entries"},
        "verb": {"base": "watch and play", "past": "done",
                 "ing": "working through"},
        # measured in CIE76 against every accent in properties/index.json —
        # 200 lists, 400 accents, when this was picked; see
        # scratch/agent-sf/accent.py. A grid sweep of the warm band found
        # these two the freest points in it: #990000 sits 11.1 from Bob's
        # Burgers' #B4331C and #FF7700 sits 13.6 from Bleach's #E85A0C, with
        # nothing else nearer. They are also the Street Fighter II logo's own
        # pair — deep red outline, hot orange fill. The obvious alternatives
        # were all taken: a logo orange lands 1.3 from Body Swap's dark, the
        # logo yellow is Big O's dark exactly, and a Hadouken blue is 1.9
        # from Doctor Who.
        "accent": "#990000",
        "accentDark": "#FF7700",
        "tiers": False,
        "notes": [
            ["Street Fighter II is eight rows, and that is the source's count.",
             "Wikipedia numbers the versions in their own words: Champion "
             "Edition is \"the first of several updated versions\", Hyper "
             "Fighting \"the third arcade version\", Super the \"fourth game "
             "in the sub-series\", Super Turbo \"the fifth installment\"; "
             "Hyper Street Fighter II holds \"the five Street Fighter II "
             "games previously released\"; HD Remix was meant to be the sixth "
             "and is \"in fact the seventh\"; Ultra Street Fighter II is "
             "\"the eighth definitive version\". A source that counts to "
             "eight is not describing one game with revisions, so this list "
             "does not collapse them. Each was a separate thing you had to go "
             "and find — a different cabinet, a different cartridge, a "
             "different download."],
            ["The same rule cuts the other way after 2010.",
             "A row is a game Wikipedia gives an article of its own. Street "
             "Fighter V: Arcade Edition, Street Fighter V: Champion Edition, "
             "Ultra Street Fighter IV, Super Street Fighter IV: 3D Edition "
             "and Street Fighter 6 Years 1-2 Fighters Edition are all named "
             "in the same source, and every one of them is a redirect into "
             "another game's page or not a link at all. They are patches and "
             "ports, and nobody sits down to play them separately. "
             "Compilations are out for the same reason: the Anniversary "
             "Collection and the 30th Anniversary Collection are boxes "
             "holding rows that are already here."],
            ["What is not on the list, and on whose say-so.",
             "The source splits itself into \"Main series\" and \"Other "
             "games\", and says of the second that they \"are not part of the "
             "mainline Street Fighter series, but involve Street Fighter "
             "characters\". Everything in that half stays off. Street Fighter "
             "EX 1-3 are the ones people will ask about: Capcom "
             "\"co-produced\" them \"with Arika\", who own half that cast, "
             "and both source lists file them outside the main series. Marvel "
             "vs. Capcom, SNK vs. Capcom, Street Fighter X Tekken and X-Men "
             "vs. Street Fighter are crossovers with another franchise "
             "attached. Final Fight is the closest call and still out: Street "
             "Fighter II arrived \"following an unsuccessful attempt to brand "
             "the 1989 beat 'em up game Final Fight as the Street Fighter "
             "sequel\" — the attempt failed, and II is the sequel."],
            ["Six films, and no television.",
             "A film here is a work Wikipedia files as a film with an article "
             "of its own. That admits the two 1994 features, the two Alpha "
             "anime, The Legend of Chun-Li and the one that opened in October "
             "2026. "
             "It excludes Street Fighter IV: The Ties That Bind, which lives "
             "as a section of the game's page, and Round One: Fight!, which "
             "has no page at all. Television is off the list by the same "
             "source's own filing: Street Fighter II V and the 1995 American "
             "cartoon sit in its Television series section, and Assassin's "
             "Fist and Resurrection describe themselves as web series."],
            ["No hours on this list, on purpose.",
             "HowLongToBeat has a main-story figure for all twenty games, and "
             "none of them are used. Nineteen measure a single run up an "
             "arcade ladder — under an hour for Street Fighter Alpha, an hour "
             "and three quarters for Super Street Fighter II Turbo, three and "
             "a half at the very top — which is nothing like how anyone has "
             "played these games for thirty years. The twentieth, Street "
             "Fighter 6, measures a genuine single-player campaign and comes "
             "to seventeen hours: weighted, that one row would own a third of "
             "the whole bar. And the numbers "
             "disagree with themselves: Hyper Street Fighter II is Super "
             "Turbo with a version selector, and it reports half an hour "
             "longer. A bar drawn from that would be confidently wrong, so "
             "this list counts entries instead."],
            ["The order is release order, twice checked.",
             "Every date comes from the entry's own Wikipedia infobox, and "
             "the resulting sequence is checked against the release timeline "
             "in the source's own list article, which settles the ties inside "
             "1992, 1997, 2008 and 2010 the same way. That is why the two "
             "1994 films sit after Super Street Fighter II Turbo rather than "
             "at the top of the year."],
            "Games and films from Wikipedia — the Street Fighter franchise "
            "article, List of Street Fighter video games, List of Street "
            "Fighter media, and each work's own page; work ids from Wikidata, "
            "checked against each item's own type and year; the unused "
            "playtime figures from HowLongToBeat.",
        ],
        "sections": sections,
    }

    out = prop.write(p)
    print("wrote %s — %d entries (%d games, %d films), unweighted"
          % (out.name, len(ids), ng, nf))
    for s in sections:
        print("   %-30s %2d  %s" % (s["title"], len(s["items"]), s["sub"]))
    print("   sync groups formed: %s"
          % (", ".join(sorted(forms)) if forms else
             "none — nothing else in the catalogue carries a Street Fighter "
             "game or film"))
    nm = near_misses()
    print("   shipped rows naming the franchise: %s"
          % (nm if nm else "none"))
    print("   hltb, collected and unused: %s"
          % ", ".join("%s %s" % (games[t]["t"].split(":")[0], hl[t])
                      for t in ("Street Fighter Alpha", "Street Fighter 6")))
    print("   %s" % seventh[:110])
    print("   %s" % hiatus[:110])
    print("   %s" % sf26[:110])
    print("   %s" % world[:110])


if __name__ == "__main__":
    main()
