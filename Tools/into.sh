#!/bin/zsh
# GET INTO THE WORLD, AND BE ABLE TO PHOTOGRAPH IT.
#
# Six steps, every one of which has failed on its own at least once tonight and
# every one of which is silent when it does. Written down because doing them by
# hand cost about an hour of a night's work:
#
#   1. the editor, with the remote hand armed. The hand is loaded through
#      -ExecCmds, which cannot carry a path with a space in it -- and this
#      project lives in "Unreal Projects" -- so the script is COPIED to the
#      scratchpad, whose path has none, and run from there.
#   2. THE LEVEL, EXPLICITLY. An editor that was restarted after a build often
#      comes up on an empty untitled map instead of the last one. PIE then
#      starts happily, the bridge connects happily, and the photograph is a
#      grey field with a grid on it.
#   3. play, not simulate.
#   4. the probe, which is what `hand.py cal` reads. It is armed through the
#      same command file as everything else and takes a few seconds to land.
#   5. calibrate. The editor's panel layout and window position change across
#      restarts, so yesterday's mapping crops the wrong rectangle -- which
#      looks exactly like an empty level, see step 2.
#   6. the gate. One click on the card, which now takes a press anywhere.
#
#   into.sh          -- all of it
#   into.sh nogate   -- stop before entering the world
set -e
SP="$(cd "$(dirname "$0")" && pwd)"
S=/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad

cp "$SP/playremote.py" "$SP/probe.py" "$S/"
UE_EXEC="py $S/playremote.py" zsh "$SP/ue.sh" | tail -1

echo '{"level_path":"/Game/TopDown/Lvl_TopDown"}' > /tmp/_into_lv.json
python3 "$SP/mcp.py" editor_toolset.toolsets.scene.SceneTools load_level /tmp/_into_lv.json >/dev/null 2>&1
sleep 4

zsh "$SP/play.sh" 55 | tail -1
sleep 3
# TWICE, AND THAT IS NOT SUPERSTITION. The first arm after a fresh PIE
# reliably comes back "the probe is not writing", and the second one lands.
# `hand.py cal` then fails on a stale mapping, which is indistinguishable
# from an empty level in the photograph that follows -- see step 5.
echo "exec py $S/probe.py" >> "$S/play.cmd"
sleep 7
echo "exec py $S/probe.py" >> "$S/play.cmd"
sleep 7
python3 "$SP/hand.py" cal | tail -1

[ "$1" = "nogate" ] && exit 0
python3 "$SP/hand.py" click 2038 1514 >/dev/null 2>&1
sleep 6
echo "in the world"
