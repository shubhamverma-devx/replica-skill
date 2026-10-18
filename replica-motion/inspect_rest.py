"""Print rest positions of the bones we drive, to learn the rig's orientation."""
import sys
import bpy

path = sys.argv[sys.argv.index("--") + 1]
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=path)

arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
mesh = next(o for o in bpy.data.objects if o.type == "MESH")
print("ARMSCALE", tuple(round(v, 4) for v in arm.scale))
print("MESHDIM", tuple(round(v, 3) for v in mesh.dimensions))
print("MESHMIN", tuple(round(v, 3) for v in mesh.bound_box[0]))

want = ["Hips", "Spine", "Spine1", "Spine2", "Neck", "Head",
        "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand",
        "RightArm", "RightForeArm",
        "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase",
        "RightUpLeg", "RightLeg", "RightFoot"]
for w in want:
    b = arm.data.bones.get("mixamorig5:" + w)
    if not b:
        continue
    h = arm.matrix_world @ b.head_local
    t = arm.matrix_world @ b.tail_local
    d = (t - h).normalized()
    print("BONE %-14s head=(%6.2f,%6.2f,%6.2f) dir=(%5.2f,%5.2f,%5.2f) len=%.3f"
          % (w, h.x, h.y, h.z, d.x, d.y, d.z, (t - h).length))
