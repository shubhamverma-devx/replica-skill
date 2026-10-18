#!/usr/bin/env python3
"""Generate every exercise animation as a Lottie file.

    python3 build.py <output-dir>

Runs the ground check first and refuses to write if any foot drifts, so a hovering
figure cannot reach the app.
"""

import os
import sys

import exercises
import fk
import rig

# Horizontal travel is intended in these (the hips move back); everywhere else the
# figure must not slide sideways.
AUTHORED_X = {"bodyweight_squat", "hamstring_stretch", "reverse_lunge"}


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    problems = []

    for key, motion in exercises.MOTIONS.items():
        fk.ground_lock(motion, authored_x=key in AUTHORED_X)
        issues = fk.ground_check(motion)
        if issues:
            problems.append("%s: %s" % (key, "; ".join(issues)))

    if problems:
        print("refusing to write - feet drift:", file=sys.stderr)
        for p in problems:
            print("  " + p, file=sys.stderr)
        return 1

    for key, motion in exercises.MOTIONS.items():
        doc = rig.build(
            name=motion["title"],
            keyframes=motion["keyframes"],
            duration=motion.get("duration", 2.0),
            root=motion.get("root", (256, 268)),
            root_rot=motion.get("root_rot", 0),
            root_motion=motion.get("root_motion"),
            fit_box=fk.bbox(motion),
        )
        path = os.path.join(out_dir, key + ".json")
        rig.write(doc, path)
        print("%-22s %5.1f KB  %4d frames" % (key, os.path.getsize(path) / 1024.0, doc["op"]))

    print("\n%d animations written to %s" % (len(exercises.MOTIONS), out_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "out"))
