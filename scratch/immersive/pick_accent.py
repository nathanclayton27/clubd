#!/usr/bin/env python3
"""Pick the immersive-sim accent pair by measuring it against the catalogue.

    python scratch/immersive/pick_accent.py

Same method as scratch/fps/pick_accent.py: read every accent and accentDark
already shipping in properties/index.json, convert to CIE Lab, and score
candidates by nearest neighbour (CIE76 delta-E) across BOTH palettes at once,
because a new card has to be distinguishable from every other card on the
wall and not just from the ones in its own theme. Prints the ranking so the
pick is arguable in a diff instead of eyeballed.
"""
import colorsys
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SLUG = "immersive"


def srgb_to_lab(hexstr):
    r, g, b = (int(hexstr[i:i + 2], 16) / 255.0 for i in (1, 3, 5))

    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = lin(r), lin(g), lin(b)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 1.00000
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3.0) if t > 0.008856 else 7.787 * t + 16 / 116.0

    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def de(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def hexof(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h / 360.0, s, v)
    return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))


def lum(h):
    def lin(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def ratio(a, b):
    la, lb = sorted((lum(a) + 0.05, lum(b) + 0.05))
    return lb / la


def main():
    index = json.loads((ROOT / "properties" / "index.json")
                       .read_text(encoding="utf-8"))
    index = [e for e in index if e["slug"] != SLUG]
    taken = []
    for e in index:
        for key in ("accent", "accentDark"):
            if e.get(key):
                taken.append((e["slug"] + "." + key, srgb_to_lab(e[key]),
                              e[key]))
    print("compared against %d colours from %d shipped lists"
          % (len(taken), len(index)))

    def nearest(hexstr):
        lab = srgb_to_lab(hexstr)
        return min(((de(lab, l), n, h) for n, l, h in taken))

    for label, sats, vals in (
            ("accent    ", (0.55, 0.7, 0.85, 1.0), (0.40, 0.5, 0.6)),
            ("accentDark", (0.35, 0.5, 0.65, 0.8), (0.85, 0.93, 1.0))):
        rows = []
        for hue in range(0, 360, 5):
            for s in sats:
                for v in vals:
                    c = hexof(hue, s, v)
                    d, who, hx = nearest(c)
                    rows.append((d, hue, c, who, hx))
        rows.sort(reverse=True)
        print("\n%s — best-separated candidates" % label)
        seen = set()
        for d, hue, c, who, hx in rows:
            if hue // 20 in seen:
                continue
            seen.add(hue // 20)
            print("   h=%3d  %s  nearest %.1f  %s %s" % (hue, c, d, who, hx))
            if len(seen) >= 10:
                break

    # The thematic first choices for this genre are all amber and gold — the
    # 0451 keypad, Thief's lantern, Rapture's brass — and the catalogue has no
    # room left in them: every one lands inside delta-E 6 of something already
    # shipping, and lantern gold is 2.5 from best-directors-cuts. Blue is
    # worse (the pick that scored 2.2 against dc-anthology). What is empty is
    # the violet corner, which still reads right for a genre of neon signage
    # in the dark, so that is where the pair comes from.
    print("\nshortlist (thematic candidates, scored):")
    for name, pair in (
            ("keypad amber     ", ("#8A6A00", "#FFCC33")),
            ("Rapture brass    ", ("#7A5A12", "#E8BE5C")),
            ("whale-oil teal   ", ("#0F6E7A", "#4FE0E8")),
            ("Typhon ink blue  ", ("#1E4F9E", "#7FAEFF")),
            ("lantern gold     ", ("#8A5A00", "#FFC04C")),
            ("SHODAN green     ", ("#0E7A5A", "#3FE0A8")),
            ("CHOSEN violet    ", ("#71189E", "#D98CFF"))):
        out = []
        for c in pair:
            d, who, hx = nearest(c)
            out.append("%s nearest %.1f (%s %s)" % (c, d, who, hx))
        print("   %s  %s" % (name, "  |  ".join(out)))

    # the search that produced the pick: sweep the violet band and keep the
    # pairs that clear 4.5:1 on white and 7:1 on the dark ground, ranked by
    # their worse nearest-neighbour distance
    print("\nviolet band, best-separated pairs clearing both contrasts:")
    rows = []
    for hue in range(255, 300, 5):
        for s1 in (0.7, 0.85, 1.0):
            for v1 in (0.45, 0.55, 0.62):
                c1 = hexof(hue, s1, v1)
                if ratio(c1, "#FFFFFF") < 4.5:
                    continue
                d1 = nearest(c1)
                for s2 in (0.35, 0.45, 0.55):
                    for v2 in (0.9, 0.97, 1.0):
                        c2 = hexof(hue, s2, v2)
                        if ratio(c2, "#111418") < 7:
                            continue
                        d2 = nearest(c2)
                        rows.append((min(d1[0], d2[0]), hue, c1, c2, d1, d2))
    rows.sort(reverse=True)
    for d, hue, c1, c2, d1, d2 in rows[:6]:
        print("   min %.1f  h=%3d  %s (%.1f %s)  %s (%.1f %s)"
              % (d, hue, c1, d1[0], d1[1], c2, d2[0], d2[1]))

    print("\ncontrast of the pick:")
    for c, ground in (("#71189E", "#FFFFFF"), ("#D98CFF", "#111418")):
        print("   %s on %s  %.2f:1" % (c, ground, ratio(c, ground)))


if __name__ == "__main__":
    main()
