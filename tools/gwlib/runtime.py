"""Which of a film's runtimes a list should weigh it at (CLU-178, CLU-365).

A film does not have one runtime. It has a theatrical length, often several by
territory, usually a longer cut sold later, sometimes a first assembly nobody
saw, and — if it is silent — a different length at every projection speed.
Wikidata's P2047 collects all of them as bare numbers with the provenance
stripped off, which is why every list weighted from "the longest P2047 in
range" eventually ships a length the film was never released at:

    Q184843  Blade Runner   112 and 116, both rank `normal`, no qualifiers
    Q509913  Legend         114 (P518 = director's cut) and 125, both `normal`

Neither item carries a deprecated or a preferred statement, so the rank-aware
reader CLU-178 asked for changes nothing on Blade Runner — longest returns 116,
first returns the shipped 112, and the film's own article says 117 minutes
cited to the BBFC. On Legend a qualifier-aware reader correctly sets 114 aside
as the director's cut and then returns 125, Scott's first assembly: a length
nothing was ever released at. Rank is not the defect. **Provenance is**, and
P2047 does not carry it.

An {{Infobox film}} does. It prints every length the article stands behind and
labels each one — "(US version)", "(first cut)", "(Cannes cut)", "(20 fps)" —
so the choice can be made on what a figure IS rather than on how big it is.
That is the rule CLU-365 moved cult-classics onto, and this module is that
rule written down once instead of per generator.

The rule
--------
Given the labelled figures a box prints, in document order:

  1. A box stating a RANGE ("112-126 minutes") is declining to answer, and so
     is this. The row keeps whatever it has and the generator says so.
  2. A figure whose label marks a version that was not released AS THE FILM is
     dropped — a first cut, a workprint, a festival or premiere cut later
     replaced, a director's cut, an extended or unrated edition, a re-edit.
     These are the figures that produced every defect on the card. A cut that
     WAS the release keeps its place, including a "final cut" (Andrei Rublev's
     183 minutes is the film; its 205-minute first cut is not) and a territory
     variant ("Italian version", "France").
  3. A figure labelled with a projection speed other than 24 fps is dropped.
     A silent film's minute count is a function of the speed it is shown at,
     and 24 fps is the speed every circulating release runs at — which is the
     card's own argument against Blade Runner's 112, a 25fps PAL transfer.
  4. The first figure still standing is the answer, and its label is the
     citation.

What it deliberately does not do
--------------------------------
It never averages, never estimates, and never prefers a figure for being
longer or shorter. Where the rule yields nothing the caller keeps the number
it already had and reports it; a weight is a number a reader can check against
the film's own article, or it is not this module's business.

Territory order is the article's, not a preference of ours. Where a box lists
four national cuts the first is the original release in every case in the
catalogue so far, and where it is not, the generator's own exception table is
the place to say so with a citation — see make_ss.py's L'Atalante.
"""
import re

# A label saying "this length is not the film as it was released". Matched as a
# substring of the lowercased label, so "cannes cut" catches "(Cannes cut)" and
# "the Cannes cut".
#
# The five marked below are the ones a row in this catalogue exercises today,
# and each is named against the row that forced it. The rest are the same class
# of thing and are listed so the next author does not have to rediscover them
# one build at a time — they are siblings, not sightings, and a label that
# turns out to belong on the other side of this line should be moved rather
# than worked around.
#
# "restored version" is deliberately NOT here. A restoration is usually the
# only version in circulation, so it is a perfectly good weight; L'Atalante is
# the case where the box's *other* figure is the distributor's mutilation, and
# that is settled by a named exception with a citation in make_ss.py rather
# than by a rule that would quietly downgrade every restoration.
NOT_THE_RELEASE = (
    "first cut",            # EXERCISED: Andrei Rublev's 205 minutes
    "cannes cut",           # EXERCISED: The Leopard's 195 minutes
    "premiere",             # EXERCISED: The Shining's 146, pulled after a week
    "director's cut",       # EXERCISED: Legend's 114 minutes
    "complete novel",       # EXERCISED: The Outsiders' 114-minute re-edit
    "extended",             # EXERCISED: Far and Away's 170-minute cut
    "rough cut",
    "workprint",
    "first assembly",
    "directors cut",
    "director's edition",
    "unrated",
    "uncut",
    "special edition",
    "redux",
)

# "(20 fps)" — a silent film at a speed nothing is projected at today.
_FPS = re.compile(r"(\d{1,3})\s*fps", re.I)
STANDARD_FPS = 24


def _rejected(label):
    """Why this figure is not a candidate, or None if it is one."""
    low = (label or "").lower()
    for bad in NOT_THE_RELEASE:
        if bad in low:
            return bad
    m = _FPS.search(low)
    if m and int(m.group(1)) != STANDARD_FPS:
        return "%s fps" % m.group(1)
    return None


def weigh(cuts, range_stated=False):
    """(minutes, why) — the length to weigh, from [(minutes, label)] in order.

    `cuts` is what the film's own infobox prints, document order preserved;
    `range_stated` is True where the field gives a range rather than figures.
    Returns (None, why) when the box cannot settle it, and the caller must then
    keep the figure the row already carries rather than invent one.

    >>> weigh([(117, "")])
    (117, 'the only figure the box prints')
    >>> weigh([(89, "US version"), (93, "European version"),
    ...        (114, "director's cut")])[0]
    89
    >>> weigh([(205, "first cut"), (183, "final cut")])[0]
    183
    >>> weigh([(110, "20 fps"), (82, "24 fps")])[0]
    82
    >>> weigh([(126, "different sources")], range_stated=True)
    (None, 'the box states a range, not a figure')
    """
    if range_stated:
        return None, "the box states a range, not a figure"
    if not cuts:
        return None, "the box prints no figure in minutes"
    kept, dropped = [], []
    for minutes, label in cuts:
        why = _rejected(label)
        if why:
            dropped.append((minutes, why))
        else:
            kept.append((minutes, label))
    if not kept:
        return None, ("every figure is a version that was not the release: %s"
                      % ", ".join("%d (%s)" % d for d in dropped))
    minutes, label = kept[0]
    if len(cuts) == 1:
        return minutes, "the only figure the box prints"
    why = label or "the figure the box leads with"
    if dropped:
        why += ", ahead of " + ", ".join("%d (%s)" % d for d in dropped)
    elif len(kept) > 1:
        why += ", the first of %d the box prints" % len(kept)
    return minutes, why


if __name__ == "__main__":
    import doctest
    fails, ran = doctest.testmod()
    print("%d doctests, %d failed" % (ran, fails))
