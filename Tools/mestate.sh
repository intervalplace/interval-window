#!/bin/zsh
SP="$(cd "$(dirname "$0")" && pwd)"
B="$(dirname "$(dirname "$SP")")/interval-bridge"
cp "$SP/mestate.mjs" "$B/_me.mjs"
(cd "$B" && node _me.mjs) 2>/dev/null
rm -f "$B/_me.mjs"
