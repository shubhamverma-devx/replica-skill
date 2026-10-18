"""Forward kinematics in world space, for validating a pose before it ships.

Used by the ground check: a foot that is meant to be planted must not drift
vertically between keyframes, or the figure looks like it is hovering.
"""

import math
import rig

SPEC = {b[0]: b for b in rig.SKELETON}
PARENT_LEN = {"root": 0}
for _n, _p, _l, _w, _a, _r in rig.SKELETON:
    PARENT_LEN[_n] = _l


def _apply(point, angle_deg, origin):
    """Rotate `point` (a local offset) clockwise by angle, then translate."""
    a = math.radians(angle_deg)
    x, y = point
    return (origin[0] + x * math.cos(a) - y * math.sin(a),
            origin[1] + x * math.sin(a) + y * math.cos(a))


def tip(bone, pose, root=(256, 268), root_rot=0):
    """World position of the far end of `bone`."""
    chain = []
    cur = bone
    while cur != "root":
        chain.append(cur)
        cur = SPEC[cur][1]
    chain.reverse()

    origin = root
    angle = root_rot
    for name in chain:
        _n, parent, length, _w, along, _r = SPEC[name]
        offset = PARENT_LEN[parent] * along
        origin = _apply((0, offset), angle, origin)
        angle += pose[name]
    return _apply((0, SPEC[bone][2]), angle, origin)


def ground_check(motion, bones=("footNear", "footFar"), tolerance=6.0):
    """Report feet that move vertically while they should be planted.

    A foot is treated as planted in a keyframe when it is within `tolerance` of the
    lowest position that foot reaches across the whole motion.
    """
    rest = rig.rest_pose()
    root = motion.get("root", (256, 268))
    rrot = motion.get("root_rot", 0)
    rm = motion.get("root_motion")

    rows = []
    for t, partial in motion["keyframes"]:
        pose = dict(rest); pose.update(partial)
        r, rr = root, rrot
        if rm:
            n = min(rm, key=lambda k: abs(k[0] - t))
            r = (root[0] + n[1], root[1] + n[2]); rr = n[3]
        rows.append((t, {b: tip(b, pose, r, rr) for b in bones}))

    issues = []
    for b in bones:
        ys = [row[1][b][1] for row in rows]
        lowest = max(ys)
        planted = [(t, y) for (t, pos), y in zip(rows, ys) if lowest - y < 40]
        if len(planted) > 1:
            spread = max(y for _, y in planted) - min(y for _, y in planted)
            if spread > tolerance:
                issues.append("%s drifts %.1fpx while planted" % (b, spread))
    return issues


def ground_lock(motion, bones=("footNear", "footFar"), authored_x=True):
    """Hold the ground line steady.

    Locking one named foot is wrong for anything that alternates: on a marching
    frame the chosen foot is the raised one, and solving to it drags the whole body
    down. So the reference is the LOWEST foot in each keyframe - whichever is bearing
    weight - and only the vertical offset is solved. Horizontal motion stays as
    authored, because a hip travelling back in a squat is intended and a figure
    sliding sideways is not.
    """
    rest = rig.rest_pose()
    root = motion.get("root", (256, 268))
    rrot = motion.get("root_rot", 0)
    times = [t for t, _ in motion["keyframes"]]
    existing = {t: (dx, dy, r) for t, dx, dy, r in (motion.get("root_motion") or [])}

    def at(t):
        if t in existing:
            return existing[t]
        if not existing:
            return (0, 0, rrot)
        return existing[min(existing, key=lambda k: abs(k - t))]

    def lowest(t, dx, dy, r):
        pose = dict(rest)
        pose.update(dict(motion["keyframes"])[t])
        return max(tip(b, pose, (root[0] + dx, root[1] + dy), r)[1] for b in bones)

    dx0, dy0, r0 = at(times[0])
    baseline = lowest(times[0], dx0, dy0, r0)

    solved = []
    for t in times:
        dx, dy, r = at(t)
        if not authored_x:
            dx = 0
        solved.append((t, dx, dy + (baseline - lowest(t, dx, dy, r)), r))

    motion["root_motion"] = solved
    return motion


def bbox(motion, pad=14.0):
    """Tight bounds of the figure across every keyframe, in world coordinates.

    Used to frame each motion. A squat and a push-up occupy very different shapes,
    so a single fixed canvas leaves one of them tiny; fitting per motion means every
    exercise fills its thumbnail.
    """
    rest = rig.rest_pose()
    root = motion.get("root", (256, 268))
    rrot = motion.get("root_rot", 0)
    rm = motion.get("root_motion")

    xs, ys = [], []
    for t, partial in motion["keyframes"]:
        pose = dict(rest); pose.update(partial)
        r, rr = root, rrot
        if rm:
            n = min(rm, key=lambda k: abs(k[0] - t))
            r = (root[0] + n[1], root[1] + n[2]); rr = n[3]

        for bone, parent, length, width, along, _rest in rig.SKELETON:
            end = tip(bone, pose, r, rr)
            # the bone's own origin is its parent's tip along the attachment point
            start = _origin(bone, pose, r, rr)
            if bone == "head":
                cx, cy = _head_centre(pose, r, rr)
                reach = rig.HEAD_RADIUS + pad
                xs += [cx - reach, cx + reach]; ys += [cy - reach, cy + reach]
                continue
            reach = width / 2.0 + pad
            for (x, y) in (start, end):
                xs += [x - reach, x + reach]; ys += [y - reach, y + reach]

    return min(xs), min(ys), max(xs), max(ys)


def _origin(bone, pose, root, root_rot):
    chain = []
    cur = bone
    while cur != "root":
        chain.append(cur)
        cur = SPEC[cur][1]
    chain.reverse()
    origin, angle = root, root_rot
    for name in chain:
        _n, parent, _l, _w, along, _r = SPEC[name]
        origin = _apply((0, PARENT_LEN[parent] * along), angle, origin)
        angle += pose[name]
    return origin


def _head_centre(pose, root, root_rot):
    origin = _origin("head", pose, root, root_rot)
    chain = []
    cur = "head"
    while cur != "root":
        chain.append(cur); cur = SPEC[cur][1]
    angle = root_rot + sum(pose[b] for b in chain)
    return _apply((0, rig.HEAD_RADIUS + rig.NECK), angle, origin)
