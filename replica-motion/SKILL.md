---
name: replica-motion
description: >-
  Generates a clone's character animations instead of licensing them: a
  parametric humanoid rig posed by keyframed joint angles and written straight out
  as Lottie, with a forward-kinematics ground check that refuses to ship a figure
  whose planted foot drifts. Turns the usual four-figure animation line item into
  a script. Use when the user says "we need exercise animations", "make the
  animations", "the figures look bad", "animate the character", "we can't afford
  an animator", or when /replica-design finds the original's animation library is
  the asset that cannot be copied.
---

# replica-motion

Some clones are blocked by one asset, not by code. A fitness app is hundreds of
exercise animations; a language app is its character set; a meditation app is its
illustration library. Commissioning that is weeks and thousands.

This generates it. A skeleton of parented capsules, posed by joint angles,
written as Lottie JSON. Around 9 KB per animation, regenerable, and owned
outright.

It will not match a studio's hand-keyed 3D. It will beat a placeholder, ship, and
cost nothing - and the rig is the part that is hard to redo later, so the art
style can be replaced without touching the poses.

## The rules

Generated from a rig **you** define. Never trace, sample, rotoscope, or convert
the original's animation files, and never decode its frame sequences to read the
poses back out. Study the exercise, not their asset.

## Files

```
rig.py         skeleton, FK transforms, Lottie writer
exercises.py   the motions, as keyframed joint angles
fk.py          world-space solver, ground check, bounding box
build.py       writes every motion, refusing bad ones
posters.py     single held poses, for card artwork
preview.py     SVG contact sheet, for checking poses before export
```

## Step 1: understand the conventions before posing anything

Lottie rotation is clockwise-positive in a y-down space. At rotation 0 a bone
points **down**. So the rest pose stands the torso up with 180, and every other
angle is read relative to its parent:

```
torso      180 upright; higher leans the chest forward (the figure faces right)
thigh        0 straight down; negative swings the knee forward
shin         0 straight; positive folds the heel back
upper arm  180 hanging; lower raises the arm forward, higher swings it back
forearm      0 straight; negative flexes the elbow
```

Posing blind does not work. Every sign is easy to get backwards, and a knee
drives through the floor as readily as toward the chest.

## Step 2: preview before you export

```bash
python3 preview.py /tmp/rest.svg && rsvg-convert -w 420 /tmp/rest.svg -o /tmp/rest.png
```

Render a contact sheet of the characteristic pose of every motion and **look at
it**. Fix proportions here - a head that rotates into the torso, arms hidden
inside the body - before anything is written as Lottie.

## Step 3: let the ground check do the QA

```bash
python3 build.py ../../app/src/main/assets/animations
```

`build.py` refuses to write when a planted foot drifts. This is not ceremony: a
figure that hovers, slides or sinks looks broken immediately and is hard to spot
in a 2-second loop by eye.

`fk.ground_lock()` solves the vertical offset per keyframe against the **lowest**
foot. Locking one named foot is wrong for anything that alternates - on a
marching frame the named foot is the raised one, and solving to it drags the
whole body down.

For a prone motion, author the tilt and let the lock solve the translation: a
push-up pivots at the toes, so a hand-written vertical drop slides the feet.

## Step 4: fit each motion to its own frame

A squat is tall; a push-up is wide. One fixed canvas leaves one of them tiny in a
thumbnail. `fk.bbox()` measures the motion across every keyframe and `rig.build`
scales about it, so each animation fills its frame.

## Step 5: posters

`posters.py` holds one pose and flattens it to a single tone. That is the card
artwork - the role stock photography plays in the original, filled with the
product's own figure, in the same style as the animations.

## Adding an exercise

1. Add a `MOTIONS` entry: title, duration, keyframes as partial poses over rest.
2. First and last keyframe identical, or the loop jumps.
3. Preview it. Look at it.
4. `build.py`. If the ground check complains, the pose is wrong, not the check.

## Colour and presentation

`NEAR` and `FAR` give the two-tone depth. Draw the figure on a **fixed** stage
colour rather than the theme surface: one asset set then reads correctly in light
and dark, instead of needing two.

## When to go further

If the product needs photoreal figures, this rig is still the right first step -
it fixes the timing, the framing and the pose library, which is most of the work.
Swapping the renderer later changes how a figure looks, not what it does.

## Output

Animations in the app's asset directory, a regeneration command in the project
README, and a note in `replica/design/assets.md` recording that the animation
line item is closed and what it was replaced with.
