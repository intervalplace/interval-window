#!/bin/zsh
# Where the rivers can be crossed. See ways.mjs.
# It runs from the bridge's own directory because `ws` is its dependency.
SP="$(cd "$(dirname "$0")" && pwd)"
B="$(dirname "$(dirname "$SP")")/interval-bridge"
cp "$SP/ways.mjs" "$B/_ways.mjs"
(cd "$B" && node _ways.mjs "$@")
rm -f "$B/_ways.mjs"
