#!/bin/zsh
# FILM THE WINDOW WHILE IT IS PLAYED.
#
# Not a screen recording: this machine has never been granted Screen Recording
# and `screencapture` answers "could not create image from display". It does
# not matter, because the thing worth filming is the VIEWPORT and the engine
# will photograph that on request -- which is also how every still in this
# session was taken. The editor's panels and menu bar are not in the film for
# the same reason, which is a feature.
#
# Each frame is cropped to the viewport and shrunk immediately, and the
# full-size original is deleted, because an hour of 5120-wide PNGs is twenty
# gigabytes and an hour of 1100-wide ones is half of one.
#
# ---- IT MUST NOT COST THE THING IT IS FILMING ----
#
# A frame a second was too expensive and it showed on the stream at once:
# "it seems very very laggy and walking is... weird". Each `shot showui` is a
# five-thousand-pixel-wide readback and a ten-megabyte PNG written on the game
# thread, so a frame a second spent a fifth of every second not drawing -- and
# in a window whose entire job between two ticks is smooth interpolation, that
# is the one cost that is never worth paying. Smoothness is the product;
# footage of it is not.
#
# So the default is a frame every three seconds. The film is a faster
# timelapse, which nobody minds, and the walk is a walk.
#
#   film.sh start [width] [seconds]  -- begin, in the background
#   film.sh stop            -- end, and say how many frames were taken
#   film.sh cut out.mp4 fps -- assemble what was taken
set -e
P="/Users/matsjulner/Documents/Unreal Projects/interval"
S="/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad"
REEL="$S/reel"
LONG="${2:-1100}"
EVERY="${3:-3}"

case "${1:-start}" in
start)
  rm -rf "$REEL" "$P/Saved/Screenshots"
  mkdir -p "$REEL"
  echo "running" > "$S/film.on"
  (
    # The viewport's rectangle inside the window, worked out ONCE. It is the
    # same arithmetic see.sh does per shot, and doing it per shot at a frame a
    # second means an AppleScript round trip a second for an hour.
    eval "$(python3 - <<'PY'
import json, subprocess
SP = ('/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/'
      'd4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/')
c = json.load(open(SP + 'hand.cal.json'))
geom = subprocess.run(['osascript', '-e',
    'tell application "System Events" to tell process "UnrealEditor" to get '
    'position of window 1'], capture_output=True, text=True).stdout.strip()
wx, wy = [int(v) for v in geom.split(', ')]
px = c['kx']
print('OX=%d' % round((-c['ox'] / c['kx'] - wx) * px))
print('OY=%d' % round((-c['oy'] / c['ky'] - wy) * px))
print('VW=%d' % int(c['vw']))
print('VH=%d' % int(c['vh']))
PY
)"
    N=0
    while [ -f "$S/film.on" ]; do
      echo "exec shot showui" >> "$S/play.cmd"
      sleep "$EVERY"
      for F in "$P/Saved/Screenshots"/**/*.png(N); do
        N=$((N + 1))
        OUT=$(printf "$REEL/f%06d.png" "$N")
        sips -c "$VH" "$VW" --cropOffset "$OY" "$OX" "$F" --out "$OUT" >/dev/null 2>&1 \
          && sips -Z "$LONG" "$OUT" --out "$OUT" >/dev/null 2>&1 || rm -f "$OUT"
        rm -f "$F"
      done
    done
  ) >/dev/null 2>&1 &
  echo "filming into $REEL"
  ;;
stop)
  rm -f "$S/film.on"
  sleep 3
  echo "$(ls "$REEL" 2>/dev/null | wc -l | tr -d ' ') frames"
  ;;
cut)
  OUT="${2:-$S/interval.mp4}"
  FPS="${3:-20}"
  "$S/mp4" "$OUT" "$FPS" "$REEL"/*.png
  ;;
esac
