---
name: replica-mirror
description: >-
  Makes a clone's screens actually look like the original's, by capturing both
  over adb and comparing them tile by tile until the differences are gone. Reports
  which region is wrong and whether it is colour, layout or type, samples the real
  hex values out of the reference so the palette is measured instead of guessed,
  and loops until each screen matches. Use when the user says "it doesn't look the
  same", "make it pixel perfect", "match the design exactly", "compare the
  screenshots", "what's different", "copy their colours", "same font", or after
  /replica-build when a screen is meant to mirror the original.
---

# replica-mirror

The parity score in `/replica-diff` answers "is the feature there". This answers
"does it look right", which is a different question and the one users notice
first.

Works on anything you can screenshot. The tools assume Android over adb; for web
or iOS, capture however you normally do and skip to step 2.

```
replica/ui/             paired view-hierarchy dumps, one per screen
replica/screens/        reference screenshots of the original
replica/clone-screens/  the same screens from the clone, same device, same size
replica/mirror-log.md   one line per screen per pass: what differed, what changed
```

## The rules

Match **layout, spacing, type and colour**. Do not ship their logo, wordmark,
app name, photographs, illustrations or copy. Those are the things a store
takedown is actually about; the grid and the greys are not.

Capture only from the user's own device, from an app they installed themselves.

## Step 1: capture both, identically

Same device, same resolution, same theme, same scroll position. A comparison
between a 1080x2400 original and a 1440x3120 clone measures the device, not the
design.

```bash
python3 capture.py --ads-off                                   # stop interstitials
python3 capture.py --package com.their.app --out replica/screens/s13.png
python3 capture.py --package com.your.app  --out replica/clone-screens/S13.png
```

Free apps run ads that hijack navigation: a tap meant for a card opens a browser,
and the screenshot you get is an advertiser's landing page. Airplane mode is the
cheapest fix. **Check every capture is the screen you meant** - a misfired shot
silently poisons every comparison after it.

Ad frequency climbs the longer you navigate, and cached creatives still fire in
airplane mode. When a session degrades to an ad on every launch, stop pressing
back and ask the user whether their copy may be cleared: `pm clear` resets the
frequency cap, but it also wipes their progress in that app, so it is their
call, not yours. Verify every dump actually contains the screen you wanted
(`grep` for a string only it has) rather than trusting that the tap landed.

## Step 2: read the real palette, do not guess one

```bash
python3 palette.py replica/screens/s13.png                     # dominant flats
python3 palette.py replica/screens/s13.png --region 0 1000 1080 1900
python3 palette.py replica/screens/s13.png --at 540 1200       # one pixel
```

Write the sampled values straight into the design tokens. A remembered blue is
always a bit wrong, and "a bit wrong" across a whole screen reads as a different
product. Sample: the page background, the card fill, the primary, the muted text,
every accent, and each badge or pill.

When a sampled value fails contrast, say so and let the user decide. Matching a
2.8:1 grey is a real choice with a real cost, not a detail to bury.

## Step 3: diff the layout element by element

**Do this before looking at pixels.** A screenshot says something is wrong; this
says what, where and by how much, for every element at once, which is the
difference between fixing a screen in one pass and fixing one anchor per round
trip.

```bash
python3 uidiff.py capture com.their.app  ref.xml
python3 uidiff.py capture com.your.app   clone.xml
python3 uidiff.py diff ref.xml clone.xml --tolerance 10
```

It reports three things:

- **MISSING** - in the reference, absent from the clone. A missing row is a
  harder error than a misplaced one and is invisible in a pixel diff.
- **EXTRA** - in the clone, not in the reference.
- **OFF POSITION** - every matched element's dx, dy, dw, dh in pixels.

Read the dy column top to bottom. If the numbers grow as you go down, the error
is **cumulative spacing**, not any single component: each section is adding a
little and by mid-screen you are a whole card out. Fix the tokens, not the
elements.

Convert with the device's density before changing code: on a 1080-wide phone at
3x, 1dp is 3px, so a 30px gap is 10dp.

## Step 4: compare tile by tile

```bash
python3 tilediff.py replica/screens/s13.png replica/clone-screens/S13.png
python3 tilediff.py ... --bands                    # vertical rhythm only
python3 tilediff.py ... --grid 16 --annotate out.png
```

Three numbers per tile, because the three failures need different fixes:

| reading | meaning | what to change |
| --- | --- | --- |
| colour | mean RGB differs | the token, fill or tint |
| layout | edge structure differs | size, position, radius, spacing |
| ink | dark-pixel density differs | font family, weight or size |

`colour 41, layout 3` is a right shape with a wrong fill. `colour 2, layout 38`
is the reverse. Fix what the numbers actually say.

**`--bands` first.** One wrong padding near the top pushes everything below it
down, and that shows up as band after band drifting rather than as a single bad
tile. Fix the rhythm, then the tiles.

## Step 5: identify the typeface, do not assume it

Crop the same heading from both at 3x and set them one above the other. Look at
the single/double-storey `a`, the `g` descender, the `G` spur, the `y` tail and
the relative widths.

```bash
sips -c 120 560 --cropOffset 460 60 shot.png --out t.png
sips -z 360 1680 t.png --out t_big.png
```

Then render your candidates at matched cap height and compare. The first guess is
usually wrong in width, which is invisible in isolation and obvious side by side.
If the original uses a licensed font, pick the closest open one and say which.

## Step 6: loop

One screen at a time, worst band first, re-capture after every change. Stop when
the remaining differences are only the things you are deliberately not copying -
their photographs, their logo, their copy. Those will never converge, so do not
chase them; note them in the log and move on.

```
pass 1  S13  bands 1066-1777 colour 70-164   -> card artwork, deliberate
pass 2  S13  header colour 31 ink 12         -> title 26sp -> 23sp, flame solid
pass 3  S13  bands clean except card artwork -> done
```

## Honesty

Report what the numbers say. A screen that still differs after three passes is a
screen that still differs; say which parts and why. Never quote a score as
"close" when the tool said otherwise, and never claim a match you have not
re-captured and re-measured.

## Output

Updated tokens and components, `replica/clone-screens/` refreshed,
`replica/mirror-log.md` with a line per pass, and a plain summary: which screens
match, which do not, and what is left that you chose not to copy. Next:
`/replica-test`, or `/replica-diff` for the feature score.
