# Rendering with a real character

The parametric rig in this skill produces a mannequin: correct poses, correct
timing, visibly not a person. That is fine for a prototype and not fine for
anything users pay for.

This is the upgrade. It keeps the rig's poses, timing, framing and ground lock
and swaps only the body, by retargeting onto a modelled, skinned, rigged
character the user supplies.

## Getting a character

The user downloads it; do not sign into an account on their behalf.

- **Mixamo** (mixamo.com, free Adobe account). Characters tab, pick one,
  Download as **FBX Binary**, pose **T-pose**. Clothed and skinned, ~50 MB.
- **CC0 base meshes** (Ryan King on Gumroad, Blender Studio). Unrigged, so you
  build the armature and bind with automatic weights first.

Check the licence covers commercial use before anything ships.

## Learn the rig before posing it

Never assume an orientation. Run `inspect_rest.py` and read it off:

```bash
blender --background --python inspect_rest.py -- character.fbx
```

A Mixamo character comes back Z-up, facing **-Y**, with T-pose arms along
**±X**, about 1.78 m tall, bones prefixed `mixamorig:` or `mixamorig5:`. So the
sagittal plane is YZ and every joint angle is a rotation about world **X**. A
different rig will differ, and guessing costs more than the one command.

## The four things that will waste your afternoon

All four were hit building this, and each fails *silently* - the script
succeeds, the render is wrong.

1. **The FBX ships an action.** Even a T-pose download. Leave it attached and
   the animation system re-evaluates every bone from its keyframes at render
   time: the bones move when you inspect them, the mesh renders in rest pose.
   Clear it on every object, and remove the actions:

   ```python
   for ob in bpy.data.objects:
       ob.animation_data_clear()
   ```

2. **`pose_bone.matrix` is in armature space, which is not world space.** The
   FBX importer leaves the armature Y-up inside a Z-up scene. Rotating about
   "X" there is not the axis the rest pose measurement showed. Convert:

   ```python
   world = arm.matrix_world @ pb.matrix
   pb.matrix = arm.matrix_world.inverted() @ (T(head) @ R @ T(-head) @ world)
   ```

3. **Do not touch the armature's own transform.** The importer stores the
   axis conversion there; assigning `rotation_euler` destroys it and the figure
   renders lying on its side. Parent the armature to an empty and transform
   that.

4. **`mode_set` needs the object active *and selected*.** Without the select it
   is a no-op in background, and every frame comes out in rest pose.

## Retargeting

`render_character.py` maps the 2D rig's joints onto the humanoid:

| rig joint | bone | angle |
| --- | --- | --- |
| torso | Spine, Spine1, Spine2 | `(a - 180)`, split across the three so the back curves |
| upper arm | LeftArm / RightArm | `a - 180`, after dropping 90 degrees out of T-pose |
| forearm | LeftForeArm / RightForeArm | `a` |
| thigh | LeftUpLeg / RightUpLeg | `a` |
| shin | LeftLeg / RightLeg | `a` |
| foot | LeftFoot / RightFoot | `a + 90` |

Pose parent-first and update the view layer between bones, or children inherit
a stale parent.

Spreading the torso lean over three spine bones is what stops the figure
hinging at the waist like a doll.

## Grounding and framing

Pose first, then drop the whole figure so its lowest vertex sits at z=0. Doing
it from the mesh rather than the skeleton accounts for shoes.

Prone motions sit low and run wide, so they need their own camera height and
zoom; a single framing leaves the standing poses tiny or the push-ups cropped.

## Output

```bash
./render_all_character.sh character.fbx out/ 24 256
```

24 frames per motion, tiled 6x4 by ffmpeg, compressed with cwebp. Sprite sheets
rather than animated WebP: decoding animated WebP needs `ImageDecoder` on API
28, and a sheet plus a frame index works on every version.
