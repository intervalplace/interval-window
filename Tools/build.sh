#!/bin/zsh
# Stop the editor, rebuild the plugin, bring it back.
# Stopping first is not politeness: the editor holds the dylib open and the
# link step fails halfway, leaving a module that loads but is a version behind.
set -e
SP="$(dirname "$0")"
"$SP/ue.sh" --stop
# THE WHOLE LOG, AND THEN THE PART THAT MATTERS.
#
# This piped straight into `tail -25`, which is fine when a build works and a
# trap when one does not: a compile error is printed where it happens, the
# summary scrolls past it, and the last twenty-five lines are deprecation
# notes from the engine's own headers. A failed build was read as a clean one,
# the editor came up with no IntervalBridge at all and asked to rebuild it,
# and the half hour after that was spent looking for the wrong thing.
#
# So the full log is kept, every error line is printed, and the exit status is
# the compiler's rather than tail's. `set -e` at the top then stops the script
# instead of carrying on to launch an editor that has nothing to load.
LOG=/tmp/intervalbuild.log
# `set -e` at the top would stop the script the instant the compiler returns
# non-zero, before any of the reporting below runs, which is the opposite of
# what this is for. The status is caught by hand and re-raised at the end.
set +e
"/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh" \
  intervalEditor Mac Development \
  -project="/Users/matsjulner/Documents/Unreal Projects/interval/interval.uproject" \
  -waitmutex > "$LOG" 2>&1
STATUS=$?
grep -E "error:|Result: Failed" "$LOG" || true
tail -4 "$LOG"
echo "(full log: $LOG)"
exit $STATUS
