#!/bin/zsh
# PLAY, not Simulate -- which is the only way to see the gate.
#
# Simulate spawns no player pawn and so no player controller, and the gate
# takes itself down when there is none. Everything else in this project is
# photographed in Simulate for exactly that reason: a free camera over a world
# that is building itself. This is the other thing, the one a person sees.
SP="$(dirname "$0")"
echo '{}' > "$SP/_stop.json"
python3 "$SP/mcp.py" EditorToolset.EditorAppToolset StopPIE "$SP/_stop.json" >/dev/null 2>&1
sleep 5
cat > "$SP/_play.json" <<'J'
{"options":{"bSimulate":false,"playMode":"PlayMode_InViewPort","warmupSeconds":10}}
J
python3 "$SP/mcp.py" EditorToolset.EditorAppToolset StartPIE "$SP/_play.json" >/dev/null
sleep ${1:-30}
echo playing
