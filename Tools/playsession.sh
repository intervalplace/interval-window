#!/bin/zsh
# Start a session this window can be PLAYED in: editor up, remote armed, world
# built, hour held at NOON so what happens can be seen.
#
# A QUARTER IS NOON. This held the hour at 0.95 and called it daylight, and
# 0.95 is the small hours before dawn: see the note on ForceDay in
# IntervalHour.cpp, where 0 is sunrise, a quarter is noon, a half is sunset and
# three quarters is midnight. Every session started by this script since has
# been at night, which is why photographs taken through it came out too dark to
# judge anything by and a grip was argued about rather than looked at.
#
# WHY IT EXISTS. `ue.sh` on its own restarts the editor WITHOUT the play
# remote, and the failure is silent -- do.sh goes on writing commands, nothing
# reads them, and the citizen simply never moves. That cost a long stretch of
# chasing a walking bug that was really a disarmed console.
#
#   playsession.sh            -- simulate: free camera, no gate, no panel
#   playsession.sh play       -- play: watch camera, panel and feed
set -e
SP="$(cd "$(dirname "$0")" && pwd)"
S=/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad
rm -f "$S/play.cmd"
UE_EXEC="py $SP/playremote.py" "$SP/ue.sh" | tail -1
python3 "$SP/mcp.py" editor_toolset.toolsets.object.ObjectTools set_properties \
  <(printf '{"instance":{"refPath":"/Game/Interval/IntervalLook.IntervalLook"},"values":"{\\"ForceDay\\":0.25,\\"bGate\\":false}"}') >/dev/null
if [ "$1" = "play" ]; then "$SP/play.sh" 60 >/dev/null; else "$SP/sim.sh" 55 >/dev/null; fi
"$SP/around.sh" 1 | head -3
