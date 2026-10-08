#!/bin/zsh
# Run one of the editor-Python scripts as a commandlet, with the editor closed.
#
# THERE IS NO PYTHON OVER MCP. The toolsets can make assets and set properties
# but they cannot import one, so anything that calls `unreal.AssetImportTask`
# has to run inside the editor's own interpreter -- and the commandlet wants
# the project to itself, so the editor must be down for it and comes back after.
#
#   pyrun.sh import_armour.py [...more scripts...]
set -e
SP="$(cd "$(dirname "$0")" && pwd)"   # ABSOLUTE: the commandlet resolves -script against the ENGINE binary directory, not the shell's
UE="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd"
PROJ="/Users/matsjulner/Documents/Unreal Projects/interval/interval.uproject"
"$SP/ue.sh" --stop
for s in "$@"; do
  echo "--- $s"
  "$UE" "$PROJ" -run=pythonscript -script="$SP/$s" -unattended -nopause -nosplash \
    2>&1 | grep -Ei "DONE|Error|Warning: Failed|Traceback|cannot" | head -30
done
