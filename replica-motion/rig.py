"""Parametric 2D humanoid rig -> Lottie. Standard library only.

A bone is a rounded capsule drawn along its own +Y axis. Bones are parented, so a
pose is forward kinematics: each joint angle is relative to its parent, and the
whole figure is posed by a dict of {joint: degrees}.

Screen coordinates are y-down and Lottie rotation is clockwise, so at rotation 0 a
bone points straight down. The rest pose therefore rotates the torso by 180 to stand
it up, and every other angle is read relative to that. The figure faces right.
"""

import json

# ---------------------------------------------------------------- skeleton

# name: (parent, length, width, offset along the parent's bone, rest angle)
SKELETON = [
    ("torso",    "root",      112, 46, 0.0,  180),
    ("head",     "torso",       0, 0,  1.0,    0),   # ellipse, drawn separately
    ("armFarU",  "torso",      70, 20, 0.88,  168),
    ("armFarL",  "armFarU",    66, 17, 1.0,    0),
    ("legFarU",  "root",       92, 26, 0.0,    0),
    ("legFarL",  "legFarU",    88, 21, 1.0,    0),
    ("footFar",  "legFarL",    30, 14, 1.0,  -90),
    ("legNearU", "root",       92, 28, 0.0,    0),
    ("legNearL", "legNearU",   88, 23, 1.0,    0),
    ("footNear", "legNearL",   30, 15, 1.0,  -90),
    ("armNearU", "torso",      70, 22, 0.88,  192),
    ("armNearL", "armNearU",   66, 19, 1.0,    0),
]

HEAD_RADIUS = 31
NECK = 5   # gap between the top of the torso and the centre of the head

# Near limbs read as foreground, far limbs sit behind the torso. Two tones give depth
# without any shading. Both are from the app's own palette, and the figure is drawn
# on a white stage in every theme (see ExerciseAnimation.kt), the way an exercise
# illustration is normally presented.
NEAR = "#2F74EC"
FAR = "#15357F"
SKIN = "#2F74EC"

TONE = {
    "armFarU": FAR, "armFarL": FAR, "legFarU": FAR, "legFarL": FAR, "footFar": FAR,
    "torso": NEAR, "head": SKIN,
    "legNearU": NEAR, "legNearL": NEAR, "footNear": NEAR,
    "armNearU": NEAR, "armNearL": NEAR,
}

JOINTS = [b[0] for b in SKELETON]


def rest_pose():
    return {name: rest for name, _, _, _, _, rest in SKELETON}


# ---------------------------------------------------------------- lottie bits

def _rgba(hex_colour):
    h = hex_colour.lstrip("#")
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)] + [1]


def _ease_in(): return {"x": [0.33], "y": [0.0]}
def _ease_out(): return {"x": [0.67], "y": [1.0]}


def _rot_keys(values, frames):
    """values: list of (frame, degrees). Smooth, with an ease on every segment."""
    keys = []
    for i, (f, deg) in enumerate(values):
        k = {"t": f, "s": [deg]}
        if i < len(values) - 1:
            k["i"] = _ease_out()
            k["o"] = _ease_in()
        keys.append(k)
    return {"a": 1, "k": keys}


def _static(value):
    return {"a": 0, "k": value}


def _transform(pos, rot):
    return {
        "o": _static(100),
        "r": rot,
        "p": _static(pos + [0]),
        "a": _static([0, 0, 0]),
        "s": _static([100, 100, 100]),
    }


def _capsule(length, width, colour):
    return [{
        "ty": "gr",
        "it": [
            {"ty": "rc", "p": _static([0, length / 2.0]),
             "s": _static([width, length]), "r": _static(width / 2.0)},
            {"ty": "fl", "c": _static(_rgba(colour)), "o": _static(100), "r": 1},
            {"ty": "tr", "p": _static([0, 0]), "a": _static([0, 0]),
             "s": _static([100, 100]), "r": _static(0), "o": _static(100)},
        ],
    }]


def _ellipse(radius, colour, cy):
    return [{
        "ty": "gr",
        "it": [
            {"ty": "el", "p": _static([0, cy]), "s": _static([radius * 2, radius * 2])},
            {"ty": "fl", "c": _static(_rgba(colour)), "o": _static(100), "r": 1},
            {"ty": "tr", "p": _static([0, 0]), "a": _static([0, 0]),
             "s": _static([100, 100]), "r": _static(0), "o": _static(100)},
        ],
    }]


def build(name, keyframes, size=512, fps=30, duration=2.0,
          root=(256, 268), root_rot=0, root_motion=None, fit_box=None, fill=0.88,
          colours=None):
    """keyframes: list of (t in 0..1, {joint: degrees}) - partial poses, merged over rest.

    root_motion: optional list of (t, dx, dy, drot) applied to the whole figure.
    """
    total = int(round(fps * duration))
    rest = rest_pose()

    # Expand each partial pose over the rest pose, and resolve times to frames.
    poses = []
    for t, partial in keyframes:
        full = dict(rest)
        full.update(partial)
        poses.append((int(round(t * total)), full))

    # A poster uses one flat colour instead of the two-tone depth treatment.
    tone = dict(TONE)
    if colours:
        near, far = colours
        for bone in tone:
            tone[bone] = far if bone.startswith(("armFar", "legFar", "footFar")) else near

    layers = []
    index = {}

    # Root is a null that carries whole-body translation and tilt.
    root_keys = root_motion or [(0.0, 0, 0, root_rot)]
    root_pos_keys = [{"t": int(round(t * total)), "s": [root[0] + dx, root[1] + dy, 0],
                      "i": _ease_out(), "o": _ease_in()} for t, dx, dy, _ in root_keys]
    if len(root_pos_keys) == 1:
        root_p = _static([root[0] + root_keys[0][1], root[1] + root_keys[0][2], 0])
    else:
        root_pos_keys[-1].pop("i", None); root_pos_keys[-1].pop("o", None)
        root_p = {"a": 1, "k": root_pos_keys}

    root_rot_vals = [(int(round(t * total)), r) for t, _, _, r in root_keys]
    root_r = _static(root_rot_vals[0][1]) if len(root_rot_vals) == 1 else _rot_keys(root_rot_vals, total)

    # An outer null frames the motion. A squat is tall and a push-up is wide, so a
    # single fixed canvas leaves one of them small in its thumbnail; scaling about the
    # motion's own bounding box makes every exercise fill the frame.
    layers_fit = []
    fit_ind = 1
    if fit_box:
        x0, y0, x1, y1 = fit_box
        scale = fill * size / max(x1 - x0, y1 - y0)
        layers_fit.append({
            "ddd": 0, "ind": fit_ind, "ty": 3, "nm": "fit", "sr": 1,
            "ks": {"o": _static(0), "r": _static(0),
                   "p": _static([size / 2.0, size / 2.0, 0]),
                   "a": _static([(x0 + x1) / 2.0, (y0 + y1) / 2.0, 0]),
                   "s": _static([scale * 100, scale * 100, 100])},
            "ip": 0, "op": total, "st": 0, "bm": 0,
        })

    root_ind = 2 if fit_box else 1
    index["root"] = root_ind
    root_layer = {
        "ddd": 0, "ind": root_ind, "ty": 3, "nm": "root", "sr": 1,
        "ks": {"o": _static(0), "r": root_r, "p": root_p,
               "a": _static([0, 0, 0]), "s": _static([100, 100, 100])},
        "ip": 0, "op": total, "st": 0, "bm": 0,
    }
    if fit_box:
        root_layer["parent"] = fit_ind
    layers.extend(layers_fit)
    layers.append(root_layer)

    # Bones are emitted in SKELETON order; Lottie draws the first layer on top, so the
    # list is ordered far-limbs-last... actually first-listed paints last in our build,
    # so reverse at the end to get near limbs in front.
    ind = root_ind
    parent_len = {}
    for bone, parent, length, width, along, _rest in SKELETON:
        ind += 1
        index[bone] = ind
        offset = parent_len.get(parent, 0) * along
        parent_len[bone] = length

        vals = []
        for frame, pose in poses:
            vals.append((frame, pose[bone]))
        rot = _static(vals[0][1]) if len({v for _, v in vals}) == 1 else _rot_keys(vals, total)

        if bone == "head":
            shapes = _ellipse(HEAD_RADIUS, tone[bone], HEAD_RADIUS + NECK)
        else:
            shapes = _capsule(length, width, tone[bone])

        layers.append({
            "ddd": 0, "ind": ind, "ty": 4, "nm": bone, "parent": index[parent], "sr": 1,
            "ks": _transform([0, offset], rot),
            "shapes": shapes, "ip": 0, "op": total, "st": 0, "bm": 0,
        })

    # Painter's order: Lottie paints layer[0] on top, so reverse the bone list and keep
    # the root null first.
    head = len(layers_fit) + 1
    bones = layers[head:]
    bones.reverse()
    layers = layers[:head] + bones

    return {
        "v": "5.7.4", "fr": fps, "ip": 0, "op": total, "w": size, "h": size,
        "nm": name, "ddd": 0, "assets": [], "layers": layers,
        "meta": {"g": "RepRise motion rig - original work, generated"},
    }


def write(doc, path):
    with open(path, "w") as fh:
        json.dump(doc, fh, separators=(",", ":"))
    return path
