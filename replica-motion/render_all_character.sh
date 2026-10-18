#!/bin/bash
# Render every motion with the real character, then tile into sprite sheets.
set -e
B=/Applications/Blender.app/Contents/MacOS/Blender
FBX="$1"; OUT="$2"; FRAMES="${3:-24}"; SIZE="${4:-256}"
mkdir -p "$OUT/sheets"
# prone motions sit low and run wide, so they need their own framing
frame_args() {
  case "$1" in
    push_up|forearm_plank|mountain_climber) echo "--camz 0.45 --zoom 0.95" ;;
    *) echo "--camz 0.95 --zoom 1.0" ;;
  esac
}
for m in $(python3 -c "import json;print(' '.join(json.load(open('poses.json'))['motions']))"); do
  rm -rf "$OUT/$m"; mkdir -p "$OUT/$m"
  $B --background --python render_character.py -- \
     --fbx "$FBX" --poses poses.json --motion "$m" --out "$OUT/$m" \
     --frames "$FRAMES" --size "$SIZE" $(frame_args "$m") >/dev/null 2>&1
  ffmpeg -y -loglevel error -i "$OUT/$m/f%03d.png" -filter_complex "tile=6x4" "$OUT/sheets/$m.png"
  cwebp -quiet -q 88 -alpha_q 92 "$OUT/sheets/$m.png" -o "$OUT/sheets/$m.webp"
  printf "%-22s %s\n" "$m" "$(du -h "$OUT/sheets/$m.webp" | cut -f1)"
done
echo "DONE sheets in $OUT/sheets"
