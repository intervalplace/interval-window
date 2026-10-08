#!/bin/zsh
# Simulate, not Play: the level viewport then shows the play world while the
# camera stays a free editor camera, which is the only way to photograph a
# world that is built at runtime. See UNREAL-SESSIONS-0-2.md §24.
SP="$(dirname "$0")"
# STOP FIRST. Calling StartPIE while a session is already running does not
# restart it, it does nothing -- so the actors survive, and a change to the
# look asset appears not to have taken when in fact it was never re-read. That
# cost an hour of staring at a hatchet hanging behind somebody's shoulder.
echo '{}' > "$SP/_stop.json"
python3 "$SP/mcp.py" EditorToolset.EditorAppToolset StopPIE "$SP/_stop.json" >/dev/null 2>&1
sleep 5
cat > "$SP/_sim.json" <<'J'
{"options":{"bSimulate":true,"playMode":"PlayMode_Simulate","warmupSeconds":10}}
J
python3 "$SP/mcp.py" EditorToolset.EditorAppToolset StartPIE "$SP/_sim.json" >/dev/null
sleep ${1:-45}
echo simulating
