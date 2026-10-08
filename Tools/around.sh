#!/bin/zsh
# Ask the bridge what is near the citizen. See around.mjs.
# It runs from the bridge's own directory because `ws` is its dependency.
SP="$(cd "$(dirname "$0")" && pwd)"
B="$(dirname "$(dirname "$SP")")/interval-bridge"
cp "$SP/around.mjs" "$B/_around.mjs"
(cd "$B" && node _around.mjs "$@")
rm -f "$B/_around.mjs"
