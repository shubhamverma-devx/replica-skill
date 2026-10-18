"""Render poses to an SVG contact sheet using the same forward kinematics as rig.py.

This is the check that the angles are right before anything is written as Lottie.
Needs rsvg-convert (or any SVG viewer) only for the PNG step.
"""

import sys
import rig


def _bone_svg(bone, length, width, colour):
    if bone == "head":
        return ('<circle cx="0" cy="%.1f" r="%.1f" fill="%s"/>'
                % (rig.HEAD_RADIUS + rig.NECK, rig.HEAD_RADIUS, colour))
    return ('<rect x="%.1f" y="0" width="%.1f" height="%.1f" rx="%.1f" fill="%s"/>'
            % (-width / 2.0, width, length, width / 2.0, colour))


def figure(pose, root=(256, 268), root_rot=0):
    """Nested <g> mirrors the Lottie parenting exactly: translate then rotate."""
    children = {}
    for bone, parent, _l, _w, _a, _r in rig.SKELETON:
        children.setdefault(parent, []).append(bone)
    spec = {b[0]: b for b in rig.SKELETON}
    parent_len = {"root": 0}
    for bone, _p, length, _w, _a, _r in rig.SKELETON:
        parent_len[bone] = length

    order = [b[0] for b in rig.SKELETON]
    order.reverse()  # far limbs first so near limbs paint on top

    def emit(bone):
        _n, parent, length, width, along, _rest = spec[bone]
        offset = parent_len[parent] * along
        inner = _bone_svg(bone, length, width, rig.TONE[bone])
        for child in children.get(bone, []):
            inner += emit(child)
        return ('<g transform="translate(0,%.2f) rotate(%.2f)">%s</g>'
                % (offset, pose[bone], inner))

    body = "".join(emit(b) for b in children.get("root", []))
    return ('<g transform="translate(%.1f,%.1f) rotate(%.2f)">%s</g>'
            % (root[0], root[1], root_rot, body))


def sheet(frames, cols=4, cell=512, bg="#14171C", path="preview.svg"):
    """frames: list of (label, pose, root, root_rot)."""
    rows = (len(frames) + cols - 1) // cols
    w, h = cols * cell, rows * cell
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
           'viewBox="0 0 %d %d"><rect width="%d" height="%d" fill="%s"/>'
           % (w, h, w, h, w, h, bg)]
    for i, (label, pose, root, root_rot) in enumerate(frames):
        x, y = (i % cols) * cell, (i // cols) * cell
        out.append('<g transform="translate(%d,%d)">' % (x, y))
        out.append('<rect x="8" y="8" width="%d" height="%d" rx="24" fill="#0B0D10"/>'
                   % (cell - 16, cell - 16))
        out.append(figure(pose, root, root_rot))
        out.append('<text x="24" y="%d" fill="#A3AEBE" font-family="sans-serif" '
                   'font-size="26">%s</text>' % (cell - 28, label))
        out.append("</g>")
    out.append("</svg>")
    with open(path, "w") as fh:
        fh.write("".join(out))
    return path


def poses_of(keyframes, root=(256, 268), root_rot=0, root_motion=None):
    rest = rig.rest_pose()
    out = []
    for i, (t, partial) in enumerate(keyframes):
        full = dict(rest)
        full.update(partial)
        r, rr = root, root_rot
        if root_motion:
            # nearest root keyframe by time
            nearest = min(root_motion, key=lambda k: abs(k[0] - t))
            r = (root[0] + nearest[1], root[1] + nearest[2])
            rr = nearest[3]
        out.append(("t=%.2f" % t, full, r, rr))
    return out


if __name__ == "__main__":
    sheet(poses_of([(0.0, {})]), cols=1, path=sys.argv[1] if len(sys.argv) > 1 else "preview.svg")
