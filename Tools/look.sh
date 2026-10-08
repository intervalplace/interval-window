#!/bin/zsh
# PHOTOGRAPH THE GAME, with no calibration in the way. See Tools/frame.py.
#
#   look.sh out.png [longest-side]
set -e
P="/Users/matsjulner/Documents/Unreal Projects/interval"
SP="/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad"
OUT="${1:-$SP/look.png}"
LONG="${2:-1400}"
rm -rf "$P/Saved/Screenshots"
echo "exec shot showui" >> "$SP/play.cmd"
for _ in $(seq 1 90); do
  F=$(find "$P/Saved/Screenshots" -name "*.png" 2>/dev/null | head -1); [ -n "$F" ] && break
  # SLATE ONLY TICKS AN EDITOR SOMETHING IS POINTING AT, so the request is not
  # even READ until the pointer moves. See the note in playremote.py.
  python3 "$P/Tools/hand.py" move $((1200 + RANDOM % 200)) $((880 + RANDOM % 120)) >/dev/null 2>&1 || true
  sleep 2
done
[ -n "$F" ] || { echo "no screenshot: is PIE up? apply.py stops it."; exit 1; }
python3 "$P/Tools/frame.py" "$F" "$OUT" "$LONG"
