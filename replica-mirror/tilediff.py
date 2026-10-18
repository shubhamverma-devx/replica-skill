#!/usr/bin/env python3
"""Tile-by-tile comparison of a reference screenshot against the clone's.

    python3 tilediff.py original.png clone.png
    python3 tilediff.py original.png clone.png --grid 16 --worst 15
    python3 tilediff.py original.png clone.png --bands      # vertical rhythm only
    python3 tilediff.py original.png clone.png --annotate out.png

Where `imgdiff` gives one score for a whole screen, this says WHICH part is wrong
and WHY, which is what you need to actually fix it. Every tile is measured three
ways, because the three failures need different fixes:

    colour    mean RGB differs        -> wrong token, wrong fill, wrong tint
    layout    edge structure differs  -> wrong size, position, radius, spacing
    ink       dark-pixel density      -> wrong font, weight, or text size

A tile can fail one and pass the others. "Colour 41, layout 3" means the shape is
right and the fill is wrong; "colour 2, layout 38" means the opposite. Reported
coordinates are in the ORIGINAL image's pixel space.

Standard library only. PNG decoding is reused from replica-diff.
"""

import argparse
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
for _candidate in (os.path.join(_HERE, "..", "replica-diff"), _HERE):
    if os.path.isfile(os.path.join(_candidate, "imgdiff.py")):
        sys.path.insert(0, os.path.abspath(_candidate))
        break

try:
    from imgdiff import read_png, write_png, to_width, gray, edges
except ImportError:
    sys.exit("tilediff: needs imgdiff.py from the replica-diff skill beside this one.")


def _mean_rgb(rows, r0, c0, r1, c1):
    n = 0
    tr = tg = tb = 0
    for r in range(r0, r1):
        row = rows[r]
        for c in range(c0, c1):
            p = row[c]
            tr += p[0]
            tg += p[1]
            tb += p[2]
            n += 1
    if n == 0:
        return (0, 0, 0)
    return (tr // n, tg // n, tb // n)


def _ink(g, r0, c0, r1, c1, cutoff=140):
    dark = 0
    n = 0
    for r in range(r0, r1):
        row = g[r]
        for c in range(c0, c1):
            if row[c] < cutoff:
                dark += 1
            n += 1
    return 0.0 if n == 0 else 100.0 * dark / n


def _edge_rate(e, r0, c0, r1, c1):
    on = 0
    n = 0
    for r in range(r0, r1):
        row = e[r]
        for c in range(c0, c1):
            if row[c]:
                on += 1
            n += 1
    return 0.0 if n == 0 else 100.0 * on / n


def _edge_mismatch(ea, eb, r0, c0, r1, c1):
    """Percentage of pixels where exactly one image has an edge."""
    diff = 0
    n = 0
    for r in range(r0, r1):
        ra, rb = ea[r], eb[r]
        for c in range(c0, c1):
            if bool(ra[c]) != bool(rb[c]):
                diff += 1
            n += 1
    return 0.0 if n == 0 else 100.0 * diff / n


def _hex(rgb):
    return "#%02X%02X%02X" % rgb


def analyse(path_a, path_b, grid=12, work_width=480, edge_threshold=24):
    a = read_png(path_a)
    b = read_png(path_b)
    wa, ha, rows_a = to_width(a, work_width)
    wb, hb, rows_b = to_width(b, work_width)

    height = min(ha, hb)
    width = min(wa, wb)
    scale = a[0] / float(work_width)

    ga, gb = gray(rows_a), gray(rows_b)
    ea, eb = edges(ga, edge_threshold), edges(gb, edge_threshold)

    cols = grid
    rows_n = max(1, int(round(grid * height / float(width))))
    tile_w = width / float(cols)
    tile_h = height / float(rows_n)

    tiles = []
    for ri in range(rows_n):
        for ci in range(cols):
            r0, r1 = int(ri * tile_h), max(int(ri * tile_h) + 1, int((ri + 1) * tile_h))
            c0, c1 = int(ci * tile_w), max(int(ci * tile_w) + 1, int((ci + 1) * tile_w))
            r1, c1 = min(r1, height), min(c1, width)

            ma = _mean_rgb(rows_a, r0, c0, r1, c1)
            mb = _mean_rgb(rows_b, r0, c0, r1, c1)
            colour = max(abs(ma[0] - mb[0]), abs(ma[1] - mb[1]), abs(ma[2] - mb[2]))
            layout = _edge_mismatch(ea, eb, r0, c0, r1, c1)
            ink = abs(_ink(ga, r0, c0, r1, c1) - _ink(gb, r0, c0, r1, c1))

            tiles.append({
                "row": ri, "col": ci,
                "x": int(c0 * scale), "y": int(r0 * scale),
                "w": int((c1 - c0) * scale), "h": int((r1 - r0) * scale),
                "colour": round(colour, 1),
                "layout": round(layout, 1),
                "ink": round(ink, 1),
                "a_hex": _hex(ma), "b_hex": _hex(mb),
                "severity": round(colour * 0.45 + layout * 1.0 + ink * 0.8, 1),
            })

    return {
        "tiles": tiles, "cols": cols, "rows": rows_n,
        "scale": scale, "work": (width, height),
        "size_a": (a[0], a[1]), "size_b": (b[0], b[1]),
    }


def bands(report, threshold=6.0):
    """Collapse tiles into horizontal bands - catches vertical rhythm problems.

    A header sitting too close to the status bar, a card with the wrong padding, a
    section gap that is 8dp instead of 20dp: these shift everything below them, and
    show up as one band after another drifting rather than as one bad tile.
    """
    out = []
    for ri in range(report["rows"]):
        row = [t for t in report["tiles"] if t["row"] == ri]
        if not row:
            continue
        out.append({
            "row": ri,
            "y": row[0]["y"],
            "h": row[0]["h"],
            "colour": round(sum(t["colour"] for t in row) / len(row), 1),
            "layout": round(sum(t["layout"] for t in row) / len(row), 1),
            "ink": round(sum(t["ink"] for t in row) / len(row), 1),
        })
    return [b for b in out if max(b["colour"] * 0.45, b["layout"], b["ink"]) >= threshold]


def label(tile):
    bits = []
    if tile["colour"] >= 12:
        bits.append("colour")
    if tile["layout"] >= 8:
        bits.append("layout")
    if tile["ink"] >= 6:
        bits.append("ink")
    return "+".join(bits) if bits else "minor"


def annotate(path_a, report, out_path, worst):
    """Write the original with the worst tiles outlined, for a visual read."""
    w, h, src = read_png(path_a)
    rows = [list(r) for r in src]
    for t in worst:
        x0, y0 = max(0, t["x"]), max(0, t["y"])
        x1, y1 = min(w - 1, t["x"] + t["w"]), min(h - 1, t["y"] + t["h"])
        for thickness in range(4):
            for x in range(x0, x1):
                for y in (y0 + thickness, y1 - thickness):
                    if 0 <= y < h:
                        rows[y][x] = (255, 0, 0)
            for y in range(y0, y1):
                for x in (x0 + thickness, x1 - thickness):
                    if 0 <= x < w:
                        rows[y][x] = (255, 0, 0)
    write_png(out_path, w, h, rows)
    return out_path


def main(argv=None):
    ap = argparse.ArgumentParser(description="Tile-by-tile screenshot comparison.")
    ap.add_argument("original")
    ap.add_argument("clone")
    ap.add_argument("--grid", type=int, default=12, help="tiles across (default 12)")
    ap.add_argument("--worst", type=int, default=12, help="how many tiles to list")
    ap.add_argument("--bands", action="store_true", help="horizontal bands only")
    ap.add_argument("--annotate", metavar="OUT.png", help="write the original with boxes")
    ap.add_argument("--fail-over", type=float, default=None,
                    help="exit 1 when the worst tile's severity exceeds this")
    args = ap.parse_args(argv)

    report = analyse(args.original, args.clone, grid=args.grid)

    print("  %s  %dx%d" % (os.path.basename(args.original), *report["size_a"]))
    print("  %s  %dx%d" % (os.path.basename(args.clone), *report["size_b"]))
    if report["size_a"] != report["size_b"]:
        print("  note: different sizes, compared after scaling to equal width")
    print()

    if args.bands:
        rows = bands(report)
        if not rows:
            print("  vertical rhythm matches")
            return 0
        print("  bands that differ (y in the original's pixels)")
        print("  %-8s %-8s %-8s %-8s" % ("y", "colour", "layout", "ink"))
        for b in rows:
            print("  %-8d %-8.1f %-8.1f %-8.1f" % (b["y"], b["colour"], b["layout"], b["ink"]))
        return 0

    worst = sorted(report["tiles"], key=lambda t: -t["severity"])[:args.worst]

    print("  worst tiles (coordinates in the original)")
    print("  %-22s %-7s %-7s %-6s %-9s %-9s %s"
          % ("region", "colour", "layout", "ink", "original", "clone", "what"))
    for t in worst:
        print("  %-22s %-7.1f %-7.1f %-6.1f %-9s %-9s %s"
              % ("x=%d y=%d %dx%d" % (t["x"], t["y"], t["w"], t["h"]),
                 t["colour"], t["layout"], t["ink"], t["a_hex"], t["b_hex"], label(t)))

    overall = sum(t["severity"] for t in report["tiles"]) / len(report["tiles"])
    print()
    print("  mean severity %.1f over %d tiles" % (overall, len(report["tiles"])))

    if args.annotate:
        print("  annotated: %s" % annotate(args.original, report, args.annotate, worst))

    if args.fail_over is not None and worst and worst[0]["severity"] > args.fail_over:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
