#!/bin/zsh
SP="$(cd "$(dirname "$0")" && pwd)"
B="$(dirname "$(dirname "$SP")")/interval-bridge"
cp "$SP/allowance.mjs" "$B/_allow.mjs"
(cd "$B" && node _allow.mjs) 2>/dev/null
rm -f "$B/_allow.mjs"
