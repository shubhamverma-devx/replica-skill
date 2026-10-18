"""Drive a Mixamo character with the exercise rig's poses. Run inside Blender.

    blender --background --python render_character.py -- \
        --fbx Ch38_nonPBR.fbx --poses poses.json --motion bodyweight_squat \
        --out /tmp/frames --frames 24 --size 256

The 2D rig already holds the poses, the timing, the framing and the ground lock.
This retargets them onto a real modelled, skinned, rigged body, so the figure is a
person instead of a stack of primitives.

Orientation, read off the rest pose rather than assumed:

    Z is up, the character faces -Y, and the T-pose arms lie along +/-X.

So the sagittal plane is YZ and every joint angle becomes a rotation about world
X. The arms are the exception: they start pointing sideways, so each is first
dropped 90 degrees about Y to hang at the side, and only then takes its sagittal
angle. The whole armature is then turned +90 about Z so the character faces
screen-right, matching the 2D rig, plus a yaw for a readable three-quarter view.
"""

import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

PREFIX = "mixamorig5:"
UNIT = 0.01  # rig pixels -> metres, and the character is ~1.78 m

# my joint -> (mixamo bone, share of the angle). The torso lean is spread over the
# three spine bones so the back curves instead of hinging at one point.
SPINE = [("Spine", 0.34), ("Spine1", 0.34), ("Spine2", 0.32)]
LIMBS = {
    "armNearU": "LeftArm", "armNearL": "LeftForeArm",
    "armFarU": "RightArm", "armFarL": "RightForeArm",
    "legNearU": "LeftUpLeg", "legNearL": "LeftLeg", "footNear": "LeftFoot",
    "legFarU": "RightUpLeg", "legFarL": "RightLeg", "footFar": "RightFoot",
}
# order matters: a parent must be posed before its children
ORDER = ["Spine", "Spine1", "Spine2", "Neck", "Head",
         "LeftArm", "LeftForeArm", "RightArm", "RightForeArm",
         "LeftUpLeg", "LeftLeg", "LeftFoot",
         "RightUpLeg", "RightLeg", "RightFoot"]


def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def rotate(arm, pb, axis, degrees):
    """Rotate a pose bone about a WORLD axis through its own head.

    `pose_bone.matrix` is in armature space, and the FBX importer leaves that space
    Y-up while the scene is Z-up. Rotating there silently uses the wrong axis - the
    first attempt swung the arms backwards instead of down. Converting through
    `matrix_world` keeps every angle in the frame the rest pose was measured in.
    """
    if abs(degrees) < 1e-6:
        return
    world = arm.matrix_world @ pb.matrix
    head = world.to_translation()
    R = Matrix.Rotation(math.radians(degrees), 4, axis)
    posed = Matrix.Translation(head) @ R @ Matrix.Translation(-head) @ world
    pb.matrix = arm.matrix_world.inverted() @ posed
    bpy.context.view_layer.update()


def angles_for(pose):
    """My joint angles -> degrees of X rotation per mixamo bone."""
    out = {}
    lean = pose.get("torso", 180.0) - 180.0
    for bone, share in SPINE:
        out[bone] = lean * share
    out["Head"] = pose.get("head", 0.0)

    for mine, bone in LIMBS.items():
        a = pose.get(mine, 0.0)
        if mine.startswith("arm") and mine.endswith("U"):
            out[bone] = a - 180.0
        elif mine.startswith("arm"):
            out[bone] = a
        elif mine.startswith("foot"):
            out[bone] = a + 90.0
        else:
            out[bone] = a
    return out


def make_root(arm):
    """An empty above the armature, so whole-figure transforms do not clobber the
    axis conversion the FBX importer baked into the armature's own rotation."""
    root = bpy.data.objects.new("rig_root", None)
    bpy.context.collection.objects.link(root)
    arm.parent = root
    arm.matrix_parent_inverse = Matrix.Identity(4)
    return root


def apply_pose(arm, root, pose, root_offset, root_rot, yaw):
    # Pose in the neutral frame: matrix_world is read during posing, so leaving the
    # previous frame's root transform on would bake it into every bone.
    root.rotation_euler = (0.0, 0.0, 0.0)
    root.location = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    # mode_set acts on the active object and needs it selected; without this the
    # call is a no-op in background and every frame renders the rest pose.
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    if arm.mode != "POSE":
        raise RuntimeError("could not enter pose mode (mode=%s)" % arm.mode)

    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()

    # drop both arms out of the T-pose before anything sagittal is applied
    rotate(arm, arm.pose.bones[PREFIX + "LeftArm"], "Y", 90.0)
    rotate(arm, arm.pose.bones[PREFIX + "RightArm"], "Y", -90.0)

    degrees = angles_for(pose)
    for bone in ORDER:
        pb = arm.pose.bones.get(PREFIX + bone)
        if pb is not None:
            rotate(arm, pb, "X", degrees.get(bone, 0.0))

    bpy.ops.object.mode_set(mode="OBJECT")
    # +90 about Z faces the character screen-right; yaw turns it off pure profile
    root.rotation_euler = (math.radians(root_rot), 0.0, math.radians(90.0 + yaw))
    root.location = (0.0, -root_offset[0] * UNIT, -root_offset[1] * UNIT)
    bpy.context.view_layer.update()


def ground(root):
    """Drop the figure so its lowest vertex sits on z=0, after posing."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    lowest = None
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        evaluated = ob.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        for v in mesh.vertices:
            z = (evaluated.matrix_world @ v.co).z
            lowest = z if lowest is None else min(lowest, z)
        evaluated.to_mesh_clear()
    if lowest is not None:
        root.location.z -= lowest
        bpy.context.view_layer.update()
    return lowest


def setup_scene(size, zoom, cam_z):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "Standard"

    bpy.ops.object.camera_add(location=(0, -6, cam_z), rotation=(math.pi / 2, 0, 0))
    cam = bpy.context.object
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 2.3 * zoom
    scene.camera = cam

    bpy.ops.object.light_add(type="SUN", location=(3, -5, 6))
    key = bpy.context.object
    key.data.energy = 3.2
    key.data.angle = math.radians(16)
    key.rotation_euler = (math.radians(50), 0, math.radians(28))

    bpy.ops.object.light_add(type="AREA", location=(-4, -4, 1.4))
    fill = bpy.context.object
    fill.data.energy = 220
    fill.data.size = 8
    fill.rotation_euler = (math.radians(84), 0, math.radians(-50))

    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.45
    scene.world = world
    return cam


def interpolate(keyframes, t):
    if t <= keyframes[0][0]:
        return keyframes[0][1]
    for i in range(len(keyframes) - 1):
        t0, a0 = keyframes[i]
        t1, a1 = keyframes[i + 1]
        if t0 <= t <= t1:
            u = (t - t0) / ((t1 - t0) or 1.0)
            u = u * u * (3 - 2 * u)
            return {k: a0.get(k, 0) + (a1.get(k, a0.get(k, 0)) - a0.get(k, 0)) * u
                    for k in set(a0) | set(a1)}
    return keyframes[-1][1]


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--fbx", required=True)
    ap.add_argument("--poses", required=True)
    ap.add_argument("--motion", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--frames", type=int, default=24)
    ap.add_argument("--only", type=int, default=None)
    ap.add_argument("--size", type=int, default=256)
    ap.add_argument("--zoom", type=float, default=1.0)
    ap.add_argument("--yaw", type=float, default=-22.0)
    ap.add_argument("--camz", type=float, default=0.95,
                    help="camera height; drop it for prone motions")
    args = ap.parse_args(argv)

    data = json.load(open(args.poses))
    motion = data["motions"][args.motion]
    rest = data["rest"]

    clear()
    bpy.ops.import_scene.fbx(filepath=args.fbx)
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")

    # Mixamo ships an action even on a T-pose download. Leave it attached and the
    # animation system re-evaluates every bone from its keyframes at render time,
    # silently discarding the pose we just set - the bones move, the mesh does not.
    for ob in bpy.data.objects:
        ob.animation_data_clear()
    for action in list(bpy.data.actions):
        bpy.data.actions.remove(action)

    root = make_root(arm)
    bpy.context.view_layer.objects.active = arm

    setup_scene(args.size, args.zoom, args.camz)
    os.makedirs(args.out, exist_ok=True)

    keyframes = [(t, {**rest, **p}) for t, p in motion["keyframes"]]
    root_motion = motion.get("root_motion") or [[0, 0, 0, motion.get("root_rot", 0)]]

    indices = [args.only] if args.only is not None else list(range(args.frames))
    for i in indices:
        t = i / float(args.frames)
        pose = interpolate(keyframes, t)
        rm = min(root_motion, key=lambda k: abs(k[0] - t))

        bpy.context.view_layer.objects.active = arm
        apply_pose(arm, root, pose, (rm[1], rm[2]), rm[3], args.yaw)
        ground(root)

        bpy.context.scene.render.filepath = os.path.join(args.out, "f%03d.png" % i)
        bpy.ops.render.render(write_still=True)

    print("RENDERED %d frames to %s" % (len(indices), args.out))


if __name__ == "__main__":
    main()
