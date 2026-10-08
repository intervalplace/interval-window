#!/bin/zsh
# What the ground is, in the world's own words. See soil.mjs.
# It runs from the bridge's own directory because `ws` is its dependency.
SP="$(cd "$(dirname "$0")" && pwd)"
B="$(dirname "$(dirname "$SP")")/interval-bridge"
cp "$SP/soil.mjs" "$B/_soil.mjs"
(cd "$B" && node _soil.mjs "$@")
rm -f "$B/_soil.mjs"
