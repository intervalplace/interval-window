#!/bin/zsh
# Ask the bridge what is near the citizen. See find.mjs.
# It runs from the bridge's own directory because `ws` is its dependency.
SP="$(cd "$(dirname "$0")" && pwd)"
B="$(dirname "$(dirname "$SP")")/interval-bridge"
cp "$SP/find.mjs" "$B/_find.mjs"
(cd "$B" && node _find.mjs "$@")
rm -f "$B/_find.mjs"
