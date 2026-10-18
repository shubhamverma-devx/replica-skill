#!/usr/bin/env python3
"""Single-pose figures used as card artwork.

Same rig as the exercise animations, held on one frame and flattened to a single
tone, so a card can carry the product's own illustration instead of stock
photography of a stranger.

    python3 posters.py <output-dir>
"""

import os
import sys

import exercises
import fk
import rig

# pose to hold, and the flat tone
POSTERS = {
    "poster_fullbody": ("bodyweight_squat", 1, "#FFFFFF", "#DCE8FB"),
    "poster_core": ("forearm_plank", 0, "#FFFFFF", "#DCE8FB"),
    "poster_strength": ("push_up", 0, "#FFFFFF", "#DCE8FB"),
}


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for name, (motion_key, frame, near, far) in POSTERS.items():
        motion = exercises.MOTIONS[motion_key]
        fk.ground_lock(motion)
        t, partial = motion["keyframes"][frame]

        rm = motion.get("root_motion")
        root = motion.get("root", (256, 268))
        rrot = motion.get("root_rot", 0)
        if rm:
            n = min(rm, key=lambda k: abs(k[0] - t))
            root = (root[0] + n[1], root[1] + n[2])
            rrot = n[3]

        held = {"keyframes": [(0.0, partial), (1.0, partial)],
                "root": root, "root_rot": rrot, "root_motion": None}

        doc = rig.build(
            name=name,
            keyframes=held["keyframes"],
            duration=0.5,
            root=root,
            root_rot=rrot,
            fit_box=fk.bbox(held),
            fill=0.96,
            colours=(near, far),
        )
        path = os.path.join(out_dir, name + ".json")
        rig.write(doc, path)
        print("%-20s %5.1f KB" % (name, os.path.getsize(path) / 1024.0))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "out"))
