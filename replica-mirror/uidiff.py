#!/usr/bin/env python3
"""Compare two apps' layouts element by element, not by eye.

    python3 uidiff.py capture <package> out.xml
    python3 uidiff.py diff reference.xml clone.xml
    python3 uidiff.py diff reference.xml clone.xml --tolerance 8

Screenshots tell you something is wrong. This tells you what, where and by how
much, for every element at once, so a screen can be corrected in one pass instead
of one anchor per round trip.

Elements are matched on their text first and their position second, so the output
also names what the reference has that the clone does not - a missing row is a
harder error than a misplaced one and is invisible in a pixel diff.

Reads `uiautomator dump`, so it needs a connected device and nothing else.
"""

import argparse
import os
import re
import subprocess
import sys
import time


def adb(*args, device=None):
    cmd = ["adb"] + (["-s", device] if device else []) + list(args)
    out = subprocess.run(cmd, capture_output=True)
    return out.stdout.decode("utf-8", "replace")


def capture(package, path, device=None, settle=3.0):
    adb("shell", "monkey", "-p", package, "-c",
        "android.intent.category.LAUNCHER", "1", device=device)
    time.sleep(settle)
    for _ in range(3):
        adb("shell", "uiautomator", "dump", "/sdcard/uidiff.xml", device=device)
        xml = adb("shell", "cat", "/sdcard/uidiff.xml", device=device)
        if "<node" in xml:
            with open(path, "w") as fh:
                fh.write(xml)
            return path
        time.sleep(1.0)
    sys.exit("uidiff: could not dump the view hierarchy")


def nodes(xml):
    out = []
    for match in re.finditer(r"<node[^>]*?/?>", xml):
        tag = match.group(0)

        def attr(name):
            found = re.search(name + r'="([^"]*)"', tag)
            return found.group(1) if found else ""

        bounds = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', tag)
        if not bounds:
            continue
        x0, y0, x1, y1 = map(int, bounds.groups())
        text = attr("text").strip()
        desc = attr("content-desc").strip()
        if not text and not desc and attr("clickable") != "true":
            continue
        out.append({
            "text": text, "desc": desc,
            "label": text or desc,
            "cls": attr("class").split(".")[-1],
            "x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0,
            "clickable": attr("clickable") == "true",
        })
    return out


def normalise(s):
    s = s.lower().replace("&amp;", "&").replace(" ", " ")
    return re.sub(r"[^a-z0-9]+", "", s)


def match(a_nodes, b_nodes):
    """Pair elements by text, then by nearest unmatched position."""
    pairs = []
    used = set()

    by_text = {}
    for i, n in enumerate(b_nodes):
        key = normalise(n["label"])
        if key:
            by_text.setdefault(key, []).append(i)

    for a in a_nodes:
        key = normalise(a["label"])
        picked = None
        for i in by_text.get(key, []):
            if i not in used and key:
                picked = i
                break
        if picked is None and not key:
            # unlabelled: fall back to the nearest unmatched box of a similar size
            best, best_d = None, 1e9
            for i, b in enumerate(b_nodes):
                if i in used or normalise(b["label"]):
                    continue
                if abs(b["w"] - a["w"]) > max(40, a["w"] * 0.5):
                    continue
                d = abs(b["x"] - a["x"]) + abs(b["y"] - a["y"])
                if d < best_d:
                    best, best_d = i, d
            if best is not None and best_d < 320:
                picked = best
        if picked is not None:
            used.add(picked)
            pairs.append((a, b_nodes[picked]))
        else:
            pairs.append((a, None))

    extras = [b for i, b in enumerate(b_nodes) if i not in used]
    return pairs, extras


def report(pairs, extras, tolerance):
    missing = [a for a, b in pairs if b is None]
    moved = []
    for a, b in pairs:
        if b is None:
            continue
        dy, dx = b["y"] - a["y"], b["x"] - a["x"]
        dh, dw = b["h"] - a["h"], b["w"] - a["w"]
        if max(abs(dy), abs(dx), abs(dh), abs(dw)) >= tolerance:
            moved.append((a, b, dx, dy, dw, dh))

    print("  %d elements in the reference, %d matched, %d missing, %d extra"
          % (len(pairs), len(pairs) - len(missing), len(missing), len(extras)))
    print()

    if missing:
        print("  MISSING from the clone")
        for a in missing:
            print("    %-34s at x=%-5d y=%-5d %dx%d"
                  % (a["label"][:34] or "(" + a["cls"] + ")", a["x"], a["y"], a["w"], a["h"]))
        print()

    if extras:
        print("  EXTRA in the clone (not in the reference)")
        for b in extras:
            print("    %-34s at x=%-5d y=%-5d"
                  % (b["label"][:34] or "(" + b["cls"] + ")", b["x"], b["y"]))
        print()

    if moved:
        moved.sort(key=lambda m: -abs(m[4 - 1]))
        print("  OFF POSITION (clone minus reference, pixels; + is right/down/bigger)")
        print("    %-34s %6s %6s %6s %6s" % ("element", "dx", "dy", "dw", "dh"))
        for a, b, dx, dy, dw, dh in sorted(moved, key=lambda m: m[0]["y"]):
            print("    %-34s %6d %6d %6d %6d"
                  % (a["label"][:34] or "(" + a["cls"] + ")", dx, dy, dw, dh))
        print()

    aligned = len(pairs) - len(missing) - len(moved)
    print("  %d of %d elements are within %dpx" % (aligned, len(pairs), tolerance))
    return 1 if (missing or moved) else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Element-level layout diff of two apps.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    cap = sub.add_parser("capture", help="dump one app's current screen")
    cap.add_argument("package")
    cap.add_argument("out")
    cap.add_argument("--device")
    cap.add_argument("--settle", type=float, default=3.0)

    dif = sub.add_parser("diff", help="compare two dumps")
    dif.add_argument("reference")
    dif.add_argument("clone")
    dif.add_argument("--tolerance", type=int, default=10,
                     help="pixels of slack before an element counts as moved")

    args = ap.parse_args(argv)

    if args.cmd == "capture":
        print("  " + capture(args.package, args.out, args.device, args.settle))
        return 0

    a = nodes(open(args.reference).read())
    b = nodes(open(args.clone).read())
    print("  %s: %d elements" % (os.path.basename(args.reference), len(a)))
    print("  %s: %d elements" % (os.path.basename(args.clone), len(b)))
    print()
    pairs, extras = match(a, b)
    return report(pairs, extras, args.tolerance)


if __name__ == "__main__":
    sys.exit(main())
