#!/bin/zsh
# WHAT THE PLAYER IS LOOKING AT, in viewport pixels.
#
# `shot showui` photographs the whole editor window -- menus, Outliner, Details
# and all -- and the window is not the game. Aiming a click off such a picture
# means subtracting the panel layout by eye every time, which is how a click
# lands on a roof instead of the thing beside it.
#
# So the viewport is CROPPED OUT, using the same origin `hand.py cal` measured
# by asking the engine where the pointer went. What comes out is in the exact
# coordinates hand.py takes, so a thing found at 2036,1510 in the picture is
# clicked at 2036,1510 with no arithmetic in between.
#
#   see.sh out.png [longest-side]
set -e
P="/Users/matsjulner/Documents/Unreal Projects/interval"
SP="/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad"
OUT="${1:-$SP/see.png}"
LONG="${2:-1400}"

rm -rf "$P/Saved/Screenshots"
echo "exec shot showui" >> "$SP/play.cmd"
for _ in $(seq 1 120); do
  F=$(find "$P/Saved/Screenshots" -name "*.png" 2>/dev/null | head -1); [ -n "$F" ] && break
  sleep 2
done
[ -n "$F" ] || {
  # NINE TIMES OUT OF TEN IT IS apply.py. Its FIRST act is StopPIE -- see the
  # note at the top of it -- so a photograph asked for any time after a
  # `apply.py` in the same session comes back empty, the remote is still
  # armed, the editor is still up, and nothing says which of the three is
  # missing. Play again before blaming the hand.
  echo "no screenshot: PIE is probably stopped. apply.py stops it; play.sh starts it."
  exit 1
}
sleep 1

python3 - "$F" "$OUT" "$LONG" <<'PY'
import json, subprocess, sys
F, OUT, LONG = sys.argv[1], sys.argv[2], int(sys.argv[3])
SP = ('/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/'
      'd4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/')
c = json.load(open(SP + 'hand.cal.json'))
# The editor window's own position, so the screenshot's origin is known. The
# window is the thing photographed; the viewport is a rectangle inside it.
geom = subprocess.run(['osascript', '-e',
    'tell application "System Events" to tell process "UnrealEditor" to get '
    'position of window 1'], capture_output=True, text=True).stdout.strip()
wx, wy = [int(v) for v in geom.split(', ')]
px = c['kx']                      # viewport pixels per screen point
ox = round((-c['ox'] / c['kx'] - wx) * px)
oy = round((-c['oy'] / c['ky'] - wy) * px)
w, h = int(c['vw']), int(c['vh'])
subprocess.run(['sips', '-c', str(h), str(w), '--cropOffset', str(oy), str(ox),
                F, '--out', OUT], check=True, capture_output=True)
subprocess.run(['sips', '-Z', str(LONG), OUT, '--out', OUT],
               check=True, capture_output=True)
print('viewport %dx%d cropped from %d,%d -- picture is %d wide, so multiply by %.3f'
      % (w, h, ox, oy, LONG, w / float(LONG)))
PY
