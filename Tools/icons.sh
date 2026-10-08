#!/bin/zsh
# RENDER THE INVENTORY SPRITES, INTO A WARM EDITOR.
#
# `icons.py` used to be driven with `-ExecCmds` at editor launch, and that is
# the whole of what was wrong with it. The render fired about a dozen seconds
# after start, before the material shaders were ready, and a mesh whose
# material has no shader yet is drawn with the DEFAULT one -- so every pass
# rendered, every file was written, nothing errored, `matte.py` composed them
# happily, and what came out was a pack full of flat grey items that looked
# deliberate.
#
# It was found by measuring the pixels of an icon that had been correct for two
# days and was now r == g == b, and settled by rendering the same item into an
# editor that had been up for three minutes: (122, 100, 77), the right wood.
#
# So the editor is started FIRST, left alone, and only then told to render --
# through the remote hand, which is already how everything else in this project
# reaches a running editor.
#
# AND WITH PLAY STOPPED. `spawn_actor_from_object` refuses outright while the
# editor is in a play mode ("The Editor is currently in a play mode"), which
# comes back as "0 rendered, 2 errors" in the log and nothing on disk.
#
#   icons.sh                 -- every item
#   icons.sh rod,wand        -- just these
set -e
SP="$(cd "$(dirname "$0")" && pwd)"
S=/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad
# THE WARM IS NEARLY OVER. It was three minutes, then ten, and ten lost too --
# against ten meshes dressed in the same session, whose sprites came back
# EXACTLY neutral both times. Waiting was never going to work: a material's
# shader is compiled the first time something asks to draw it, and the asking
# IS this render, so the first render always draws with the default material
# however long anybody waits first. `icons.py` makes a throwaway pass now to
# put the request in, waits, and then renders the pass that is kept. What is
# left here is a minute for the editor to finish opening the level.
WARM="${WARM:-60}"

python3 "$SP/itemart.py" | tail -1
cp "$SP/icons.py" "$SP/tiers.py" "$SP/playremote.py" "$S/"
printf '%s' "${1:-}" > "$S/icons.only"

UE_EXEC="py $S/playremote.py" zsh "$SP/ue.sh" | tail -1
echo "--- letting the shader compiler finish (${WARM}s)"
sleep "$WARM"

echo '{}' > /tmp/_icons_stop.json
python3 "$SP/mcp.py" EditorToolset.EditorAppToolset StopPIE /tmp/_icons_stop.json >/dev/null 2>&1 || true
sleep 3

echo "exec py $S/icons.py" >> "$S/play.cmd"
# The render reports through icons.json; wait for it rather than guessing.
# LONG, because `icons.py` now takes the pack again for whatever came back
# exactly neutral, up to six times with three quarters of a minute between.
# A run that needs all of them is the run this wait exists for.
for _ in $(seq 1 600); do
  if [ -f "$S/icons.json" ] && [ "$(find "$S/icons.json" -newermt '-4 minutes' | wc -l)" -gt 0 ]; then
    break
  fi
  sleep 5
done
python3 - "$S/icons.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print('rendered %d, %d errors' % (len(d['done']), len(d['errors'])))
for e in d['errors'][:5]:
    print('  ', str(e)[:140])
PY
echo "--- shading them"
# NOT PIPED, so the grey guard's exit code survives. `set -e` at the top of
# this file means a pack of grey sprites now stops the run instead of being
# reported two lines above a success. See the tail of matte.py.
python3 "$SP/matte.py" > "$S/matte.log" 2>&1 || {
  tail -12 "$S/matte.log"
  echo "the sprites came out grey; nothing was kept that is worth keeping."
  exit 2
}
tail -2 "$S/matte.log"
