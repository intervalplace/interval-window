#!/bin/zsh
# One frame-time measurement, with an optional renderer setting changed.
#
# ---- WHAT WAS MEASURED, AND THE ONLY HONEST WAY TO READ IT ----
#
#   editor idle, no world at all ........ 25.4 ms   (39 fps)
#   the window, short-range AO off ...... 29.9 ms   (34 fps)   p99  92 ms
#   the window, AO ray traced ........... 38.8 ms   (26 fps)   p99 102 ms
#
# THE WORLD COSTS ABOUT FOUR AND A HALF MILLISECONDS. Everything else in those
# numbers is the editor: its own interface, Slate, asset management, a viewport
# inside a tool. A hundred and twelve chunks of terrain, the props, the people,
# fourteen fires with their smoke and their light in the air, the stars and the
# volumetric fog add up to less than a fifth of what the editor spends on
# existing. Any "frames per second" quoted from here is a statement about the
# EDITOR and must be said that way.
#
# The one number that was worth acting on came out of the differences, not the
# totals: ray-tracing Lumen's short-range ambient occlusion cost 12 ms -- most
# of the window's entire budget -- for contact darkening in corners. See the
# note in Config/DefaultEngine.ini.
#
# What is left to chase is the p99, not the median: the world adds 55 ms of
# occasional spike over the editor's own 37, which is a chunk being rebuilt as
# the citizen walks, not anything being drawn.
#
#   bench.sh "<label>" "<cvar command or empty>"
#
# Starts the editor with the frame sampler running, builds the world, lets the
# reading settle, and prints the median. Everything about this is the EDITOR
# drawing the world -- slower than a packaged build, and the right thing to
# compare against itself.
SP="$(cd "$(dirname "$0")" && pwd)"
S=/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad
LABEL="$1"
EXTRA="$2"
rm -f "$S/frametime.json"
CMDS="py $SP/frametime.py"
[ -n "$EXTRA" ] && CMDS="$CMDS,$EXTRA"
UE_EXEC="$CMDS" "$SP/ue.sh" >/dev/null 2>&1
# ---- AND WAKE THE EDITOR UP ----
#
# Unreal throttles the editor to about three frames a second whenever its
# window is not in the foreground, which is always here. It cost a whole
# afternoon: a frame-time reading of 344 ms that did not move when Lumen,
# volumetric fog and hardware ray tracing were each turned off in turn, and
# which the EMPTY editor with no world running reported as well. Neither
# DefaultEditorPerProjectUserSettings.ini nor the saved per-user config turns
# it off -- it has to be set on the live object.
(cd "$SP" && python3 unthrottle.py) >/dev/null 2>&1
"$SP/sim.sh" 60 >/dev/null 2>&1
# Let the reading settle: the first window is all shader compilation.
for i in 1 2 3 4 5 6; do
  sleep 25
  R=$(cat "$S/frametime.json" 2>/dev/null)
  case "$R" in *'"report": 3'*|*'"report": 4'*|*'"report": 5'*|*'"report": 6'*) break;; esac
done
python3 - "$LABEL" "$S/frametime.json" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[2]))
    print('%-46s %7.1f ms   %5.1f fps   p99 %7.1f' %
          (sys.argv[1], d['ms_median'], d['fps_median'], d['ms_p99']))
except Exception as e:
    print('%-46s no reading (%s)' % (sys.argv[1], e))
PY
