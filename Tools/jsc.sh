#!/bin/zsh
# Run a script against the world's rules in JavaScriptCore, with no Node.
#
# THIS IS THE iOS PORT, TESTED ON A MAC. JavaScriptCore is the engine iOS
# already has and the only one an app may run, so "does the world work under
# JSC" is the whole question -- and it can be answered here, today, without a
# device, a certificate or a toolchain, because macOS ships the same engine
# with a shell.
#
#   jsc.sh portable/try.mjs
set -e
JSC=/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc
B="/Users/matsjulner/Documents/Unreal Projects/interval-bridge"
[ -x "$JSC" ] || { echo "no JavaScriptCore shell on this machine"; exit 1; }
cd "$B" && "$JSC" -m "$1"
