#!/bin/zsh
# Close and relaunch the interval editor with the MCP port actually free.
#
# CrashReportClient is started alongside the editor and INHERITS its listening
# sockets. When the editor exits the reporter lingers holding 127.0.0.1:8000,
# so the next editor logs "HttpListener unable to bind" and comes up with no
# MCP server at all -- while `nc -z 8000` still succeeds, because the dead
# editor's socket is the thing answering. Every symptom points at a hung
# editor. Clear the reporter, then relaunch.
UE="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
PROJ="/Users/matsjulner/Documents/Unreal Projects/interval/interval.uproject"

# A WEDGED EDITOR DOES NOT ANSWER SIGTERM. When the MCP server stops replying
# the whole process is usually stuck, and `kill` then waits forever on a thing
# that is never going to tidy itself up -- which turns "restart the editor"
# into a script that hangs and looks like the editor is merely slow to close.
# Ask politely for twenty seconds, then insist.
PID=$(pgrep -f "UnrealEditor.*interval.uproject" | head -1)
if [ -n "$PID" ]; then
  kill "$PID" 2>/dev/null
  for _ in $(seq 1 20); do ps -p "$PID" >/dev/null 2>&1 || break; sleep 1; done
  if ps -p "$PID" >/dev/null 2>&1; then
    echo "editor ignored SIGTERM, forcing"
    kill -9 "$PID" 2>/dev/null
    while ps -p "$PID" >/dev/null 2>&1; do sleep 1; done
  fi
fi
pkill -9 -f CrashReportClient 2>/dev/null
while lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; do
  lsof -tnP -iTCP:8000 -sTCP:LISTEN | xargs -r kill -9 2>/dev/null
  sleep 1
done
echo "port 8000 free"
[ "$1" = "--stop" ] && exit 0

# AND THE RESTORE PROMPT, WHICH IS A MODAL DIALOG NOBODY IS THERE TO CLICK.
#
# An editor that did not exit cleanly leaves Saved/Autosaves/PackageRestoreData
# behind, and the next one opens a "these packages have newer auto-saved
# versions -- restore them?" box before it finishes starting. Under automation
# that is invisible and fatal: the process is up, the MCP port is LISTENING and
# answers connections, and every call times out, because dispatch runs on a
# game thread that is sitting in a modal loop at frame zero. It looks exactly
# like a hung editor and it cost twenty minutes of staring at a log whose last
# line was a font loading successfully.
#
# Deleting the file declines the restore, which is the right answer here: every
# asset these scripts touch is saved explicitly by the script that touched it.
rm -f "$(dirname "$PROJ")/Saved/Autosaves/PackageRestoreData.json"

# AND THE THROTTLE, WHICH IS WHY THE REMOTE KEPT GOING DEAF.
#
# The editor stops ticking Slate when its window is not in the foreground, and
# this session drives it entirely from another application. `playremote.py`
# reads its command file from a Slate post-tick callback, so an unfocused
# editor simply stopped consuming commands -- silently, with the file filling
# up and nothing in any log. It cost several rounds of "the remote is flaky"
# before the pattern showed: it always worked for a minute after a restart,
# which is exactly how long the window kept focus.
#
# The remote tries to turn this off from inside the tick, which cannot work:
# the tick is the thing that is not running. So it is set here, in the config
# the editor reads at startup, before anything needs it.
ED_INI="$(dirname "$PROJ")/Saved/Config/Mac/EditorPerProjectUserSettings.ini"
mkdir -p "$(dirname "$ED_INI")"
if ! grep -q "bThrottleCPUWhenNotForeground=False" "$ED_INI" 2>/dev/null; then
  printf '\n[/Script/UnrealEd.EditorPerformanceSettings]\nbThrottleCPUWhenNotForeground=False\n' >> "$ED_INI"
fi
# -abslog, because this project has no Saved/Logs at all and every diagnostic
# written with UE_LOG this session went nowhere. Debugging a renderer without a
# log is how an afternoon goes into photographing dry meadows.
# CONSOLE COMMANDS AT STARTUP, for A/B-ing a renderer setting without
# committing it to DefaultEngine.ini. There is no cvar SETTER on the MCP
# surface -- only SearchCVars, which reads -- so this is the only way to try
# one. Set UE_EXEC before calling:  UE_EXEC='r.Foo 0' ue.sh
EXEC=()
[ -n "$UE_EXEC" ] && EXEC=(-ExecCmds="$UE_EXEC")

# PIXEL STREAMING, so the window can be watched from a phone: UE_STREAM=1 ue.sh
#
# The arg names are not the cvar names. PixelStreaming2 builds them by deleting
# the dots and renaming the prefix back to "PixelStreaming" (singular, no 2), so
# PixelStreaming2.Editor.StartOnLaunch is -PixelStreamingEditorStartOnLaunch.
# Guessing this wrong is silent -- an unrecognised arg is just ignored and the
# editor comes up looking perfectly healthy, streaming nothing.
#
# UseRemoteSignallingServer is the important one. Without it the editor starts
# its OWN signalling server, which (a) wants port 80, needing root on macOS, and
# (b) re-runs get_ps_servers.sh on every launch, which deletes the built
# frontend. Tools/watch.sh runs the server instead; this just connects to it.
STREAM=()
if [ -n "$UE_STREAM" ]; then
  STREAM=(-PixelStreamingEditorUseRemoteSignallingServer
          -PixelStreamingConnectionURL="ws://127.0.0.1:${STREAMER_PORT:-8888}"
          -PixelStreamingEditorStartOnLaunch
          -PixelStreamingEditorSource="${UE_STREAM_SOURCE:-LevelEditorViewport}"
          -PixelStreamingID=interval)
fi
# ANYTHING ELSE THE EDITOR HAS TO BE TOLD ON ITS COMMAND LINE.
#
# The one that matters is where the bridge is. By default the window dials a
# Node process on 127.0.0.1:7777; `-intervalbridge=inproc` runs the world's own
# bridge INSIDE the editor instead, on Unreal's HTTP and Unreal's WebSockets,
# with no Node anywhere -- which is what a phone has to do and is therefore
# worth being able to try here in one word:
#
#   UE_ARGS='-intervalbridge=inproc -intervalkey=unreal-key-inproc.json' ue.sh
#
# Split on spaces deliberately: every argument this takes is a flag or a
# flag=value and none of them has a space in it.
ARGS=()
[ -n "$UE_ARGS" ] && ARGS=(${=UE_ARGS})
("$UE" "$PROJ" -ModelContextProtocolStartServer "${EXEC[@]}" "${STREAM[@]}" "${ARGS[@]}" -log -abslog=/tmp/ue.log \
  > /tmp/editor.log 2>&1 &)
echo "relaunched"

# AND CHECK THAT THE DOOR ACTUALLY OPENED.
#
# The toolsets can all register and the HTTP server still not bind -- seen
# once, with no error in the log and the editor otherwise healthy, ticking
# frames and listening only on 1985. From outside it looks exactly like an
# editor that is slow to start, and every call times out for as long as you
# are willing to wait. Four minutes is longer than a cold start on this
# machine; past that, it is not coming.
for _ in $(seq 1 48); do
  sleep 5
  if lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "port 8000 listening"

# ---- AND WAKE IT UP ----
#
# Unreal throttles the editor to about three frames a second whenever its
# window is not in the foreground, which under automation is always. That is
# not only a measurement problem: every `sim.sh 60` was giving the world about
# a hundred and seventy frames to build itself in instead of two thousand, so
# every warm-up in this project has been ten times longer than it needed to be.
#
# Neither Config/DefaultEditorPerProjectUserSettings.ini nor the saved per-user
# config turns it off. The live object does.
(cd "$(dirname "$0")" && python3 unthrottle.py) >/dev/null 2>&1 || true
    exit 0
  fi
done
# ---- AND IF IT DID NOT, TRY AGAIN ----
#
# This happens perhaps one launch in four, and the answer has always been
# "run ue.sh again" -- which cost half a dozen manual retries in one session,
# each one indistinguishable from a real failure until it was tried. A script
# whose documented remedy is to run the script again should run itself again.
# Twice, then give up, so a genuinely broken editor is still reported rather
# than looped over.
ATTEMPT=${UE_ATTEMPT:-1}
if [ "$ATTEMPT" -lt 3 ]; then
  echo "port 8000 never bound -- relaunching (attempt $((ATTEMPT + 1)) of 3)"
  UE_ATTEMPT=$((ATTEMPT + 1)) exec "$0" "$@"
fi
echo "WARNING: the editor is up but nothing is listening on 8000 after 3 tries"
exit 1
