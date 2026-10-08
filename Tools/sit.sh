#!/bin/zsh
# SIT DOWN AND PLAY: a session driven by a real mouse, from the title card on.
#
# `playsession.sh` is the other kind of session -- it arms the remote, which
# calls the hand's deeds directly, and it turns the GATE OFF because nothing
# out there could click it. That is an automation harness, and a window can
# pass everything it does and still be unplayable: the gate was setting
# `FInputModeGameOnly` on the way through, so no mouse event reached UMG at
# all, and every clickable thing in this window had been unreachable by a
# person since the day it was written. Nothing found it, because nothing had
# ever tried to click.
#
# So this one leaves the gate UP and crosses it with the pointer, like a
# player. Everything afterwards goes through `hand.py`, which moves the
# operating system's own cursor.
#
#   sit.sh          -- editor, stream, PIE, calibrate, cross the gate
#   sit.sh nogate   -- the same but stop at the title card
set -e
SP="$(cd "$(dirname "$0")" && pwd)"
S=/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad
rm -f "$S/play.cmd"

UE_STREAM=1 UE_EXEC="py $SP/playremote.py" "$SP/ue.sh" | tail -1
# The probe reports where the engine thinks the pointer is; hand.py calibrates
# against it. It is armed through the remote rather than at launch because
# -ExecCmds takes one script and the remote is the one that must come first.
until grep -q "remote armed" "$S/play.log" 2>/dev/null && \
      [ "$(tail -1 "$S/play.log")" = "$(grep 'remote armed' "$S/play.log" | tail -1)" ]; do sleep 3; done
"$SP/play.sh" 30 >/dev/null 2>&1 || true

# AFTER PIE, NOT BEFORE. `playremote.py` looks the hand up before it reads the
# verb, and with no PIE there is no hand, so every command sent ahead of the
# world -- including this one, which wants nothing from the hand at all -- is
# answered with "no hand yet" and thrown away.
echo "exec py $S/probe.py" >> "$S/play.cmd"

# THE WORLD IS STILL ARRIVING. Chunks stream in for a few minutes after PIE
# starts and the editor drops to a frame every three seconds while they do.
# Calibrating through that is not wrong, only slow; clicking through it is
# what dropped the clicks that started all this.
echo "--- waiting for the world"
until [ -f "$S/mouse.json" ] && [ $(( $(date +%s) - $(stat -f %m "$S/mouse.json") )) -lt 8 ]; do sleep 5; done

python3 "$SP/hand.py" cal
[ "$1" = "nogate" ] && exit 0

# THE TITLE CARD, CROSSED WITH THE POINTER. The button is centred and sits a
# fixed way down the card, so its place is known -- but it is checked, because
# a click on the wrong pixel here reads as a gate that will not open.
python3 "$SP/hand.py" click $(( 4075 / 2 )) 1514
sleep 4
if grep -q "the gate opens" /tmp/ue.log; then
  echo "--- the gate opens"
else
  echo "--- the gate did NOT open: photograph it with see.sh and find the button"
  exit 1
fi
