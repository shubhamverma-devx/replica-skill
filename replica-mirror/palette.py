#!/usr/bin/env python3
"""Read the real colours out of a reference screenshot.

    python3 palette.py shot.png                 # the dominant flat colours
    python3 palette.py shot.png --at 540 1200   # one pixel
    python3 palette.py shot.png --region 0 900 1080 1400

Guessing a palette from memory is how a clone ends up almost-right. Screenshots
carry the real values, so read them instead. Flat UI fills occupy large areas of
one exact colour, which is what `--flat` ranks; gradients and photographs spread
across many near-neighbours and are filtered out.

Standard library only. PNG decoding is reused from replica-diff.
"""

import argparse
import os
import sys
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
for _candidate in (os.path.join(_HERE, "..", "replica-diff"), _HERE):
    if os.path.isfile(os.path.join(_candidate, "imgdiff.py")):
        sys.path.insert(0, os.path.abspath(_candidate))
        break

try:
    from imgdiff import read_png
except ImportError:
    sys.exit("palette: needs imgdiff.py from the replica-diff skill beside this one.")


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(rgb)


def _luma(rgb):
    return (299 * rgb[0] + 587 * rgb[1] + 114 * rgb[2]) // 1000


def dominant(rows, width, height, region=None, top=12, step=2):
    x0, y0, x1, y1 = region or (0, 0, width, height)
    counts = Counter()
    for y in range(max(0, y0), min(height, y1), step):
        row = rows[y]
        for x in range(max(0, x0), min(width, x1), step):
            counts[row[x]] += 1
    total = sum(counts.values()) or 1
    return [(rgb, 100.0 * n / total) for rgb, n in counts.most_common(top)]


def describe(rgb):
    r, g, b = rgb
    mx, mn = max(rgb), min(rgb)
    chroma = mx - mn
    lum = _luma(rgb)
    if chroma < 18:
        if lum > 245:
            return "white / card"
        if lum > 225:
            return "page background"
        if lum > 150:
            return "light grey"
        if lum > 80:
            return "mid grey / muted text"
        return "near-black / text"
    if b == mx and b - r > 30:
        return "blue (primary)"
    if r == mx and g > b:
        return "orange / coral"
    if r == mx:
        return "red / pink"
    if g == mx:
        return "green"
    return "accent"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Sample colours from a screenshot.")
    ap.add_argument("image")
    ap.add_argument("--at", nargs=2, type=int, metavar=("X", "Y"))
    ap.add_argument("--region", nargs=4, type=int, metavar=("X0", "Y0", "X1", "Y1"))
    ap.add_argument("--top", type=int, default=12)
    args = ap.parse_args(argv)

    width, height, rows = read_png(args.image)

    if args.at:
        x, y = args.at
        if not (0 <= x < width and 0 <= y < height):
            sys.exit("palette: %d,%d is outside %dx%d" % (x, y, width, height))
        rgb = rows[y][x]
        print("  %s  rgb%s  %s" % (_hex(rgb), rgb, describe(rgb)))
        return 0

    region = tuple(args.region) if args.region else None
    print("  %s  %dx%d%s" % (os.path.basename(args.image), width, height,
                             "  region %s" % (region,) if region else ""))
    print()
    print("  %-9s %-7s %s" % ("hex", "area", "reads as"))
    for rgb, pct in dominant(rows, width, height, region, args.top):
        print("  %-9s %-7s %s" % (_hex(rgb), "%.1f%%" % pct, describe(rgb)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
