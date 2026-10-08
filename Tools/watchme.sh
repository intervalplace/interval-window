#!/bin/zsh
# Watch whether the world takes a deed. See watchme.mjs.
# It runs from the bridge's own directory because `ws` is its dependency.
SP="$(cd "$(dirname "$0")" && pwd)"
B="$(dirname "$(dirname "$SP")")/interval-bridge"
cp "$SP/watchme.mjs" "$B/_watchme.mjs"
(cd "$B" && node _watchme.mjs "$@")
rm -f "$B/_watchme.mjs"
