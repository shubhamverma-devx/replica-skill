#!/usr/bin/env python3
"""Capture screenshots from a connected Android device, for side-by-side work.

    python3 capture.py --list
    python3 capture.py --package com.example.app --out shots/home.png
    python3 capture.py --package com.example.app --out shots/s.png --scroll 1
    python3 capture.py --ads-off          # airplane mode on, to stop ad interference
    python3 capture.py --ads-on

Only adb. The device must already be connected and the app installed; this never
installs, signs in, or buys anything.

Free apps run interstitials that hijack navigation mid-capture - a tap lands on a
banner and the browser opens instead of the next screen. Airplane mode stops that
and costs nothing, so `--ads-off` is usually the first call of a session.
"""

import argparse
import os
import subprocess
import sys
import time


def adb(*args, device=None, binary=False):
    cmd = ["adb"] + (["-s", device] if device else []) + list(args)
    try:
        out = subprocess.run(cmd, capture_output=True, check=False)
    except FileNotFoundError:
        sys.exit("capture: adb is not on PATH")
    if out.returncode != 0:
        sys.exit("capture: %s failed: %s" % (" ".join(cmd), out.stderr.decode().strip()))
    return out.stdout if binary else out.stdout.decode()


def devices():
    rows = []
    for line in adb("devices").splitlines()[1:]:
        if "\t" in line:
            serial, state = line.split("\t", 1)
            rows.append((serial.strip(), state.strip()))
    return rows


def find_device(package=None):
    live = [s for s, state in devices() if state == "device"]
    if not live:
        sys.exit("capture: no device. Start an emulator or plug a phone in.")
    if package:
        holders = [s for s in live
                   if package in adb("shell", "pm", "list", "packages", package, device=s)]
        if holders:
            return holders[0]
        sys.exit("capture: %s is not installed on %s" % (package, ", ".join(live)))
    return live[0]


def screenshot(path, device=None):
    data = adb("exec-out", "screencap", "-p", device=device, binary=True)
    if not data.startswith(b"\x89PNG"):
        sys.exit("capture: screencap returned something that is not a PNG")
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description="Screenshot an Android app over adb.")
    ap.add_argument("--list", action="store_true", help="list connected devices")
    ap.add_argument("--device", help="adb serial, when more than one is attached")
    ap.add_argument("--package", help="launch this package first, and verify it exists")
    ap.add_argument("--activity", help="explicit component, e.g. pkg/.MainActivity")
    ap.add_argument("--out", default="shot.png")
    ap.add_argument("--scroll", type=int, default=0, help="swipes up before capturing")
    ap.add_argument("--settle", type=float, default=2.5, help="seconds to wait before capture")
    ap.add_argument("--ads-off", action="store_true", help="airplane mode on")
    ap.add_argument("--ads-on", action="store_true", help="airplane mode off")
    args = ap.parse_args(argv)

    if args.list:
        for serial, state in devices() or [("(none)", "")]:
            print("  %-22s %s" % (serial, state))
        return 0

    device = args.device or find_device(args.package)

    if args.ads_off or args.ads_on:
        value = "true" if args.ads_off else "false"
        adb("shell", "cmd", "connectivity", "airplane-mode", value, device=device)
        print("  airplane mode %s on %s" % ("enabled" if args.ads_off else "disabled", device))
        if not args.package:
            return 0

    if args.package:
        if args.activity:
            adb("shell", "am", "start", "-n", args.activity, device=device)
        else:
            adb("shell", "monkey", "-p", args.package, "-c",
                "android.intent.category.LAUNCHER", "1", device=device)
        time.sleep(args.settle)

    for _ in range(args.scroll):
        adb("shell", "input", "swipe", "540", "1800", "540", "900", "300", device=device)
        time.sleep(0.8)

    time.sleep(args.settle if not args.package else 0.6)
    print("  %s  (%s)" % (screenshot(args.out, device), device))
    return 0


if __name__ == "__main__":
    sys.exit(main())
