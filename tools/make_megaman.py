#!/usr/bin/env python3
"""Generate properties/mega-man.json.

    python3 tools/make_megaman.py

Every game with Mega Man on the box, scoped by one source the owner picked:
"the mega man compendium" on Backloggd (backloggd.com/u/ade/list/
the-mega-man-compendium-/), a 94-game list whose own description is "every
mega man game ever sorted by release date". Contents and order are its call,
not this file's — including the Chinese licensed PC releases and the Japanese
feature-phone toys that no franchise summary bothers with.

Two things the source does not settle, settled here and said out loud:

  * It has no sections. It is one flat grid sorted by release date, and its
    site offers the same 94 under six other sorts. The sections below read
    each title's own sub-series off its name — Classic, X, Legends, Battle
    Network, Zero, ZX, Star Force — with the Classic-universe odd jobs and
    the one crossover in a last section. Inside every section the order is
    the compendium's own: release date, oldest first.
  * It carries no years or lengths. Years come from each game's own Backloggd
    page; the roster those pages produced is distilled into
    tools/data/megaman-compendium.json, which is what this reads — the raw
    page cache stays out of the repo, and the generator no longer depends on
    an untracked scratch directory to run. Hours are HowLongToBeat
    main-story figures behind tools/gwlib/hltb.py's verify-by-name gate,
    collected by scratch/megaman/fetch_hltb.py into tools/data/megaman.json.

Anything the gate refused ships UNWEIGHTED, and the reason is kept in the
data file rather than replaced with a guess: HowLongToBeat has never heard of
most of the feature-phone games, and a made-up number would go straight into
a reader's pace. Unweighted rows count as an hour apiece to the page's
arithmetic, which is the floor, not a claim.

The compendium advertises "94 Games" and enumerates 94. Both numbers are
asserted below; if the list ever grows and only one of them moves, this
build fails rather than quietly shipping the wrong count.

One row is not the compendium's, and the page says so (CLU-617): Mega Man:
Dual Override, the twelfth main Classic game, dated 2027. Dated unreleased
work belongs on lists, and the compendium could not be re-read to see whether
it has caught up (Backloggd answers plain requests with a bot wall). It is in
ADDED below, weighs nothing until it is out, and its id is pinned rather than
minted from a Backloggd game id; the page ships the 94 plus ADDED.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gwlib import prop as P  # noqa: E402

SLUG = "mega-man"
ADVERTISED = 94

BN = "Mega Man Battle Network "
SF = "Mega Man Star Force"

# The rows that are one half (or third) of a versioned release. HowLongToBeat
# files these under the numbered game — there is one "Mega Man Battle Network
# 3" record, not a Blue and a White — so putting that figure on both rows
# would bill a reader twice for a game they play once. They ship unweighted
# and say why, which is the same rule as everything else here: no number
# unless a record verifies as this row's game.
PAIRED = frozenset((
    "1758", "1757",                    # Battle Network 3 Blue / White
    "1759", "1760",                    # Battle Network 4 Red Sun / Blue Moon
    "1761", "1762",                    # Battle Network 5 Protoman / Colonel
    "1764", "1765",                    # Battle Network 6 Falzar / Gregar
    "1783", "1782", "1781",            # Star Force Dragon / Leo / Pegasus
    "1785", "1784",                    # Star Force 2 Ninja / Saurian
    "1786", "1787",                    # Star Force 3 Black Ace / Red Joker
))

# The only titles that differ from the compendium's, and why: it calls three
# separate games "Mega Man" and nothing else — the 1987 NES original, an
# American-built 1990 DOS game, and a 1995 North American Game Gear release.
# Three identical rows would be unreadable, so the later two carry the
# platform their own Backloggd page gives them. Every other row is checked
# against the source string.
RENAMED = {
    "78132": "Mega Man (DOS)",
    "1738": "Mega Man (Game Gear)",
}

# Dated work the compendium cannot be shown to carry yet. Each row goes last
# in its section and ships with w: 0 until it is out. The id is PINNED: if a
# re-read of the compendium lists the game, map its game id to this id rather
# than minting mm-<gid>, or every tick on the row is lost. main() fails until
# someone does.
# id, section, title, year, note
ADDED = [
    ("mm-dual-override", "classic", "Mega Man: Dual Override", 2027,
     "Not out yet — dated 2027, and the bar stays empty until HowLongToBeat "
     "has hours for it. The twelfth main Classic game and the first since "
     "11, with Proto Man playable alongside Mega Man."),
]

# section key -> title, intro
SECTIONS = [
    ("classic", "Classic",
     "The blue one, the numbered line, and everything that plays like it: "
     "the NES six, the five Game Boy entries, the 16-bit and 32-bit "
     "sequels, the two American-built DOS games, the remakes, and the "
     "eight-bit throwbacks that restarted the count in 2008."),
    ("x", "X",
     "The 1993 spin-off that gave the formula a dash, a wall climb and "
     "hidden armour upgrades, plus its handheld condensations, its RPG, "
     "its 3D detour and the remake."),
    ("legends", "Legends",
     "Called Dash in Japan: the fully 3D branch with towns, dungeons and a "
     "different Mega Man, its one spin-off, and the Japanese and Chinese "
     "releases that carried the name afterwards."),
    ("battle-network", "Battle Network",
     "The reboot into a networked world, where fights happen on a 3x3 grid "
     "with a deck of Battle Chips. Twelve of these are the main line's "
     "paired versions; the rest are the arcade cabinets, handheld oddities "
     "and phone episodes the line spun off in Japan."),
    ("zero", "Zero",
     "Four Game Boy Advance games that hand the lead to Zero and grade "
     "every mission you finish."),
    ("zx", "ZX",
     "The Zero line continued long afterwards on the DS, as one connected "
     "map rather than a stage select."),
    ("star-force", "Star Force",
     "Battle Network's successor on the DS, moving the same grid battles "
     "from wired networks to the air — and, like its parent, shipping in "
     "paired and tripled versions."),
    ("side", "Everything else with Mega Man on the box",
     "The Classic universe's odd jobs, which the compendium counts and most "
     "franchise summaries do not: two arcade boss-rush cabinets, a board "
     "game, football, a kart racer, an animated adventure, licensed Chinese "
     "PC releases, a decade of Japanese feature-phone toys, and the one "
     "crossover Capcom adopted from its own fans."),
]

# Backloggd game_id, section, display title, note.
# Order inside each section is the compendium's own (release date, oldest
# first); the assert at the bottom checks that against the cached list.
ROSTER = [
    # ---------------------------------------------------------------- classic
    ("1714", "classic", "Mega Man",
     "NES. The first one: eight Robot Masters, a stage you pick, and the rule "
     "that beating one hands you its weapon."),
    ("1715", "classic", "Mega Man 2",
     "NES. The one that fixed the formula and sold; still the series' front "
     "door."),
    ("1716", "classic", "Mega Man 3",
     "NES. Adds the slide and Rush, the dog who turns into whatever you need "
     "to cross a gap."),
    ("78132", "classic", "Mega Man (DOS)",
     "DOS. Not a port — an American-built PC game with its own Robot Masters, "
     "licensed out and made outside Capcom."),
    ("1733", "classic", "Mega Man: Dr. Wily's Revenge",
     "Game Boy. The handheld line starts, drawing its bosses from the first "
     "two NES games."),
    ("1717", "classic", "Mega Man 4",
     "NES. Introduces the chargeable Buster, which the series never takes "
     "back."),
    ("1734", "classic", "Mega Man II",
     "Game Boy. The second handheld entry, and the only one made by a "
     "different studio from the rest of the Game Boy line."),
    ("1735", "classic", "Mega Man III",
     "Game Boy. The handheld line back on its usual team, building from NES "
     "3 and 4."),
    ("1718", "classic", "Mega Man 5",
     "NES. Beat the bird joins the support cast."),
    ("88384", "classic", "Mega Man 3: The Robots are Revolting",
     "DOS. The second and last of the American-built PC pair, and unrelated "
     "to the NES Mega Man 3."),
    ("1736", "classic", "Mega Man IV",
     "Game Boy. Draws on NES 4 and 5, and adds a shop between stages."),
    ("1719", "classic", "Mega Man 6",
     "NES. The last NES entry; Rush becomes armour you wear instead of a "
     "vehicle you ride."),
    ("1737", "classic", "Mega Man V",
     "Game Boy. The handheld line's finale, and the only one whose bosses "
     "are all original — the Stardroids."),
    ("1727", "classic", "Mega Man: The Wily Wars",
     "Mega Drive. 16-bit remakes of the first three NES games plus a short "
     "original chapter; a cartridge in Japan and Europe, a Sega Channel "
     "download in North America."),
    ("1720", "classic", "Mega Man 7",
     "SNES. The 16-bit Classic entry, with bigger sprites and a hub you "
     "shop in."),
    ("1738", "classic", "Mega Man (Game Gear)",
     "Game Gear. A handheld remix assembled from NES 4 and 5, released only "
     "in North America."),
    ("1721", "classic", "Mega Man 8",
     "PlayStation and Saturn. The first with animated cutscenes and voice "
     "acting."),
    ("1726", "classic", "Mega Man & Bass",
     "Super Famicom, later Game Boy Advance. Two playable characters who "
     "move very differently, built on Mega Man 8's engine."),
    ("1739", "classic", "Rockman & Forte: Mirai kara no Chousensha",
     "WonderSwan, Japan only. A different game from Mega Man & Bass, despite "
     "sharing its Japanese name."),
    ("12937", "classic", "Mega Man Powered Up",
     "PSP. A remake of the 1987 original in a rounded style, with the Robot "
     "Masters playable and a stage editor."),
    ("1722", "classic", "Mega Man 9",
     "Downloadable. A deliberate return to NES limits: eight-bit art, no "
     "slide, no charge shot."),
    ("1723", "classic", "Mega Man 10",
     "Downloadable. The eight-bit follow-up, with an easy mode and extra "
     "playable characters."),
    ("76723", "classic", "Mega Man 11",
     "The modern Classic entry: hand-drawn 2.5D art, and a gear system that "
     "will slow time or strengthen your shots at a price."),
    # ---------------------------------------------------------------------- x
    ("1741", "x", "Mega Man X",
     "SNES. The spin-off that adds a dash, a wall climb and armour upgrades "
     "hidden in the stages."),
    ("1742", "x", "Mega Man X2",
     "SNES. Uses a cartridge chip for wireframe effects, and adds an air "
     "dash."),
    ("1743", "x", "Mega Man X3",
     "SNES. Zero becomes playable in a limited way, and the ride armours "
     "branch out."),
    ("1744", "x", "Mega Man X4",
     "PlayStation and Saturn. Zero becomes a full second campaign with his "
     "own moveset."),
    ("290873", "x", "Rockman X Shùxué Xuànfēng",
     "Windows, China only. A licensed educational release wearing the X "
     "cast."),
    ("1749", "x", "Mega Man Xtreme",
     "Game Boy Color. A handheld condensation of stages from X and X2."),
    ("1745", "x", "Mega Man X5",
     "PlayStation. Written as the line's ending, with Zero playable "
     "throughout."),
    ("1750", "x", "Mega Man Xtreme 2",
     "Game Boy Color. The handheld follow-up, with X and Zero as separate "
     "campaigns."),
    ("1746", "x", "Mega Man X6",
     "PlayStation. Made quickly after X5, and the most contested entry in "
     "the line."),
    ("1747", "x", "Mega Man X7",
     "PlayStation 2. The move into 3D, and the debut of a third playable "
     "character."),
    ("1751", "x", "Mega Man X: Command Mission",
     "GameCube and PS2. A turn-based RPG spin-off with a party to build."),
    ("1748", "x", "Mega Man X8",
     "PlayStation 2. Back to sidescrolling, with a mid-stage character swap."),
    ("24275", "x", "Mega Man: Maverick Hunter X",
     "PSP. A remake of the first X with reworked stages and a second "
     "campaign for Vile."),
    ("252996", "x", "Mega Man X Dive Offline",
     "The one-purchase offline build of a live-service X action game, made "
     "after its servers closed."),
    # ---------------------------------------------------------------- legends
    ("1752", "legends", "Mega Man Legends",
     "PlayStation. Fully 3D action-adventure with towns and dungeons, and a "
     "different Mega Man entirely."),
    ("290875", "legends", "Rockman Dash Zhěngjiù Dìqiú Dàmàoxiǎn",
     "Windows, China only. A licensed PC release carrying the Legends name."),
    ("234973", "legends",
     "Rockman Dash 2: Episode 1 - Roll-chan Kiki Ippatsu! no Maki",
     "Japan only. A short standalone chapter put out ahead of Legends 2."),
    ("1753", "legends", "The Misadventures of Tron Bonne",
     "PlayStation. A Legends spin-off led by Tron Bonne and her Servbots, "
     "built out of mission-sized puzzles."),
    ("1754", "legends", "Mega Man Legends 2",
     "PlayStation. The direct sequel, and where the line stops."),
    ("290977", "legends", "Rockman Dash Golf",
     "Japanese feature phones. A Legends-branded golf game on a service that "
     "closed years ago."),
    ("229209", "legends", "Rockman Dash: 5tsu no Shima no Daibouken!",
     "Japanese feature phones. A Legends-branded mobile adventure, same "
     "closed service."),
    # ---------------------------------------------------------- battle network
    ("1755", "battle-network", BN.strip(),
     "GBA. The reboot into a networked world: real-time battles on a grid, "
     "fought with a deck of Battle Chips."),
    ("1756", "battle-network", BN + "2",
     "GBA. Doubles down on chip customisation and adds Style Changes."),
    ("1758", "battle-network", BN + "3 Blue",
     "GBA. One half of a paired release — Blue and White differ in chips and "
     "bosses, and one is meant to be enough."),
    ("1757", "battle-network", BN + "3 White",
     "GBA. The other half of the third pair."),
    ("1768", "battle-network", "Rockman EXE WS",
     "WonderSwan Color, Japan only. A short side game on Bandai's handheld."),
    ("1766", "battle-network", "Mega Man Network Transmission",
     "GameCube. The same world as a 2D action-platformer rather than a grid "
     "RPG."),
    ("1767", "battle-network", "Mega Man Battle Chip Challenge",
     "GBA. Battles resolve from a deck you build beforehand — the card game "
     "without the moving around."),
    ("37354", "battle-network", "RockMan EXE N1 Battle",
     "WonderSwan Color, Japan only. A tournament-shaped battler."),
    ("1759", "battle-network", BN + "4: Red Sun",
     "GBA. Paired versions again, this time around a tournament."),
    ("1760", "battle-network", BN + "4: Blue Moon",
     "GBA. The other half of the fourth pair."),
    ("1769", "battle-network", "Rockman EXE 4.5: Real Operation",
     "GBA, Japan only. Runs on the cartridge's clock, and has you direct a "
     "Navi rather than steer one."),
    ("1761", "battle-network", BN + "5: Team Protoman",
     "GBA. The fifth pair splits by which team of Navis comes with you."),
    ("265957", "battle-network", "Rockman EXE Phantom of Network",
     "Japanese feature phones. An episode for a service long since closed."),
    ("1762", "battle-network", BN + "5: Team Colonel",
     "GBA. The other team of the fifth pair."),
    ("1771", "battle-network", "Rockman EXE The Medal Operation",
     "Arcade, Japan only. A coin-op cabinet built around the EXE cast."),
    ("1772", "battle-network", "Rockman EXE Battle Chip Stadium",
     "Arcade, Japan only. A cabinet that dispenses Battle Chips and plays "
     "their battles out."),
    ("1764", "battle-network", BN + "6: Cybeast Falzar",
     "GBA. Half of the last pair, and the end of the main line."),
    ("1765", "battle-network", BN + "6: Cybeast Gregar",
     "GBA. The other half of the last pair."),
    ("265959", "battle-network", "Rockman EXE Legend of Network",
     "Japanese feature phones. A mobile RPG on the closed service."),
    ("1774", "battle-network", "Rockman.EXE Operate Shooting Star",
     "DS, Japan only. A remake of the first Battle Network with a Star Force "
     "crossover attached."),
    # ------------------------------------------------------------------- zero
    ("1775", "zero", "Mega Man Zero",
     "GBA. Zero's own line: faster, harder, and it ranks every mission you "
     "finish."),
    ("1776", "zero", "Mega Man Zero 2",
     "GBA. Adds forms that grow out of how you actually fight."),
    ("1777", "zero", "Mega Man Zero 3",
     "GBA. Layers a chip-based customisation system over the same shape."),
    ("1778", "zero", "Mega Man Zero 4",
     "GBA. The line's finale, with weather controls that change how a stage "
     "behaves."),
    # --------------------------------------------------------------------- zx
    ("1779", "zx", "Mega Man ZX",
     "DS. The Zero line picked up long afterwards, as one connected map you "
     "travel rather than a stage select."),
    ("1780", "zx", "Mega Man ZX Advent",
     "DS. The follow-up, with two leads and forms taken from the bosses."),
    # ------------------------------------------------------------- star force
    ("1783", "star-force", SF + ": Dragon",
     "DS. Battle Network's successor, with the grid battles moved off the "
     "wires. One of three launch versions."),
    ("1782", "star-force", SF + ": Leo",
     "DS. The second of the three; they differ in powers and some bosses."),
    ("1781", "star-force", SF + ": Pegasus",
     "DS. The third of the three."),
    ("1785", "star-force", SF + " 2: Zerker x Ninja",
     "DS. The sequel narrows to two versions."),
    ("1784", "star-force", SF + " 2: Zerker x Saurian",
     "DS. The other half of that pair."),
    ("1786", "star-force", SF + " 3: Black Ace",
     "DS. Half of the last pair, and the end of the line."),
    ("1787", "star-force", SF + " 3: Red Joker",
     "DS. The other half of the last pair."),
    # ------------------------------------------------------------------- side
    ("1729", "side", "Wily & Right no RockBoard: That's Paradise",
     "Famicom, Japan only. A property-trading board game with the Classic "
     "cast."),
    ("1730", "side", "Mega Man Soccer",
     "SNES. Robot Masters play football, special shots and all."),
    ("1724", "side", "Mega Man: The Power Battle",
     "Arcade. Boss rush as a fighting-game cabinet: pick a character, skip "
     "the stages."),
    ("1725", "side", "Mega Man 2: The Power Fighters",
     "Arcade. The bigger sequel cabinet, with four to choose from."),
    ("1731", "side", "Mega Man Battle & Chase",
     "PlayStation. A kart racer with parts you bolt on; it skipped North "
     "America at the time."),
    ("1732", "side", "Super Adventure Rockman",
     "PlayStation and Saturn, Japan only. A branching animated adventure "
     "with light shooting sections."),
    ("66918", "side", "Rockman no Huángjīn Dìguó",
     "Windows, China only. A licensed PC release using the Classic cast."),
    ("84307", "side", "Rockman Strategy",
     "Windows, China only. A licensed strategy game using the Classic cast."),
    ("281347", "side", "Rockman Panic Fire",
     "Japanese feature phones. A falling-block puzzle game; the service is "
     "closed."),
    ("290979", "side", "Rockman Bug Sweeper",
     "Japanese feature phones. Minesweeper in Classic-series dressing."),
    ("288142", "side", "Rockman Tennis",
     "Japanese feature phones. Exactly what the title says."),
    ("290983", "side", "Mega Man Space Rescue",
     "Java-era mobile phones. A short arcade-style Capcom mobile game."),
    ("290981", "side", "Mega Man Rush Marine",
     "Java-era mobile phones. A short underwater one, from the same run."),
    ("290956", "side", "Rockman The Puzzle Battle",
     "Japanese feature phones. A competitive puzzle game on the closed "
     "service."),
    ("290964", "side", "Rockman no Dot Art Logic",
     "Japanese feature phones. Nonograms that resolve into series sprites."),
    ("64138", "side", "Rockman Xover",
     "iOS, Japan only. A tap-controlled social game; its service has closed."),
    ("45184", "side", "Street Fighter X Mega Man",
     "Windows. A fan-made crossover Capcom adopted and put out free for the "
     "series' 25th anniversary."),
]


def main():
    root = pathlib.Path(__file__).resolve().parent.parent
    src = json.loads((root / "tools" / "data" / "megaman-compendium.json")
                     .read_text(encoding="utf-8"))
    hours = json.loads((root / "tools" / "data" / "megaman.json")
                       .read_text(encoding="utf-8"))
    games = src["games"]

    # The source against itself: it prints "94 Games" and lists 94. The
    # enumerated entries are what ships; the advertised number is the alarm.
    assert len(games) == src["advertised"] == ADVERTISED, \
        ("the compendium no longer agrees with itself or with this file: "
         "advertised %s, enumerated %d, expected %d"
         % (src["advertised"], len(games), ADVERTISED))

    by_gid = {g["gid"]: g for g in games}
    pos = {g["gid"]: g["pos"] for g in games}
    assert len(by_gid) == len(games), "the compendium repeats a game id"
    assert {r[0] for r in ROSTER} == set(by_gid), \
        "roster/compendium mismatch: %s" % sorted(
            {r[0] for r in ROSTER} ^ set(by_gid))
    assert set(hours) == set(by_gid), \
        "hours file/compendium mismatch: %s" % sorted(set(hours) ^ set(by_gid))
    for gid, _, t, _note in ROSTER:
        want = RENAMED.get(gid, by_gid[gid]["t"])
        assert t == want, \
            "row %s says %r, the compendium says %r" % (gid, t, by_gid[gid]["t"])
    listed = {P.normt(g["t"]) for g in games}
    for aid, key, t, _year, _note in ADDED:
        assert key in {k for k, *_ in SECTIONS}, "%s: no section %s" % (aid, key)
        assert P.normt(t) not in listed, \
            ("the compendium now lists %r: give its game id the pinned id %s "
             "and take it out of ADDED" % (t, aid))
    total = ADVERTISED + len(ADDED)

    order = [k for k, *_ in SECTIONS]
    sections, seen = [], []
    for key, title, intro in SECTIONS:
        rows = [r for r in ROSTER if r[1] == key]
        assert rows, "empty section %s" % key
        rows.sort(key=lambda r: pos[r[0]])
        items = []
        for gid, _, t, note in rows:
            g = by_gid[gid]
            h = hours[gid]
            x = {"id": "mm-%s" % gid, "t": t, "n": str(g["year"])}
            if h["main_h"]:
                x["w"] = h["main_h"]
            elif gid in PAIRED:
                note = P.join_bits(
                    note.rstrip("."),
                    "HowLongToBeat times the numbered game rather than each "
                    "version, so this row carries no length")
            else:
                note = P.join_bits(note.rstrip("."),
                                   "HowLongToBeat has no story time for it")
            x["note"] = note
            items.append(x)
            seen.append(gid)
        for aid, akey, t, year, note in ADDED:
            if akey == key:
                items.append({"id": aid, "t": t, "n": str(year), "w": 0,
                              "note": note})
        years = [int(x["n"]) for x in items]
        assert years == sorted(years), "%s is out of the compendium's order" % key
        wtd = [x for x in items if x.get("w")]
        bits = ["%d–%d" % (years[0], years[-1]) if years[0] != years[-1]
                else str(years[0]),
                "%d game%s" % (len(items), "" if len(items) == 1 else "s")]
        if wtd:
            bits.append("%d hours story across %d"
                        % (round(sum(x["w"] for x in wtd)), len(wtd)))
        sections.append({"id": key, "title": title, "sub": " · ".join(bits),
                         "intro": intro, "items": items})
    sections[0]["open"] = True
    assert [s["id"] for s in sections] == order, "sections lost their order"

    ids = [x["id"] for s in sections for x in s["items"]]
    assert len(ids) == len(set(ids)) == total, (len(ids), len(set(ids)))
    assert sorted(seen) == sorted(by_gid), "an entry was dropped between passes"

    weighted = [x for s in sections for x in s["items"] if x.get("w")]
    notout = [x for s in sections for x in s["items"] if x.get("w") == 0]
    assert len(notout) == len(ADDED), "a not-out-yet row lost its w: 0"
    total_h = sum(x["w"] for x in weighted)
    unweighted = total - len(weighted) - len(notout)
    unpaired = sum(1 for s in sections for x in s["items"]
                   if "w" not in x and x["id"][3:] not in PAIRED)
    years = sorted(int(x["n"]) for s in sections for x in s["items"])
    # The blurb and notes below name Dual Override as the one addition.
    assert [a[2] for a in ADDED] == ["Mega Man: Dual Override"], \
        "ADDED changed: reword the blurb and notes that name the addition"

    prop = {
        "slug": SLUG,
        "title": "Mega Man",
        "subtitle": "the whole franchise, by sub-series, in release order",
        "kind": "games",
        "popularity": 63,
        "year": "%d–%d" % (years[0], years[-1]),
        "blurb": "%d games — every one with Mega Man on the box, from the 1987 "
                 "NES original to the offline X Dive, with Dual Override still "
                 "to come. %d carry a verified story length, about %d hours "
                 "between them."
                 % (total, len(weighted), round(total_h)),
        "unit": {"one": "game", "many": "games"},
        "verb": {"base": "play", "past": "played", "ing": "playing"},
        "itemOrder": "number-first",
        "accent": "#6868A0",
        "accentDark": "#B4C4FC",
        "tiers": False,
        "notes": [
            ["One source, and it chose the scope.",
             "This is “the mega man compendium” on Backloggd — one "
             "person's list, described by its own author as “every mega man "
             "game ever sorted by release date”. That is why the licensed "
             "Chinese PC releases and a decade of Japanese feature-phone toys "
             "are here: the compendium counts them, so this counts them. "
             "Nothing has been dropped, and one game has been added: Mega "
             "Man: Dual Override, the next Classic game, dated 2027."],
            ["The sections are not the source's.",
             "The compendium has none — it is one flat grid of %d, sorted by "
             "release date. The sections here read each title's own "
             "sub-series off its name, and the order inside every one of them "
             "is still the compendium's: release date, oldest first. Read a "
             "section top to bottom and you are reading that branch exactly "
             "as the compendium has it. Dual Override, the one addition, "
             "comes last in Classic." % ADVERTISED],
            ["%d of the %d have no length, and none has been invented."
             % (unweighted + len(notout), total),
             "Hours are HowLongToBeat main-story figures, and only where a "
             "record verifies by name and by release year. %d rows have no "
             "such record at all — the arcade cabinets, the Japanese "
             "feature-phone games, the licensed Chinese PC releases — and a "
             "plausible-looking guess for any of them would go straight into "
             "your finish date. %d more are the paired versions below. All "
             "%d say which they are and count as an hour apiece: a floor, not "
             "a claim. The last is Dual Override, which is not out yet and "
             "weighs nothing until it is."
             % (unpaired, unweighted - unpaired, unweighted)],
            ["Paired versions are separate rows, and deliberately unweighted.",
             "Battle Network 3 through 6 and all three Star Force games "
             "shipped in two or three versions apiece, and the compendium "
             "lists every one. So does this. But HowLongToBeat times the "
             "numbered game rather than each version — there is one Battle "
             "Network 3 record, not a Blue and a White — and putting that "
             "figure on both rows would bill you twice for a game you play "
             "once. Playing one of a pair is the normal thing to do; tick "
             "the one you played."],
            ["What “release order” means for a %d-game list." % total,
             "Everything is dated from its own Backloggd page except Dual "
             "Override, which carries the year Capcom announced. Where two "
             "games share a year the compendium's order is kept as it stands "
             "— the source sorted them, not this file. Three of its entries "
             "are called nothing but Mega Man: the 1987 NES game, an "
             "American-built DOS game from 1990, and a North American Game "
             "Gear release from 1995. The later two carry their platform in "
             "brackets here so they can be told apart; that is the only place "
             "a title has been changed."],
            "Contents and order from “the mega man compendium” by ade on "
            "Backloggd; years from each game's Backloggd page, Dual "
            "Override's from Wikipedia; story hours "
            "from HowLongToBeat, verified by name and release year.",
        ],
        "sections": sections,
    }

    P.write(prop)

    print("wrote %s.json" % SLUG)
    print("  %d sections, %d games — %d weighted (%d hours), %d unweighted, "
          "%d not out yet" % (len(sections), len(ids), len(weighted),
                              round(total_h), unweighted, len(notout)))
    for s in sections:
        print("   %-40s %3d  %s" % (s["title"][:40], len(s["items"]), s["sub"]))


if __name__ == "__main__":
    main()
