#!/bin/zsh
# Stop the editor, rebuild the plugin, bring it back.
# Stopping first is not politeness: the editor holds the dylib open and the
# link step fails halfway, leaving a module that loads but is a version behind.
set -e
SP="$(dirname "$0")"
"$SP/ue.sh" --stop
"/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh" \
  intervalEditor Mac Development \
  -project="/Users/matsjulner/Documents/Unreal Projects/interval/interval.uproject" \
  -waitmutex 2>&1 | tail -25
