#!/bin/zsh
# Run the conflict report from the bridge's directory, where the generator is.
set -e
SP="$(cd "$(dirname "$0")" && pwd)"
B="$(dirname "$(dirname "$SP")")/interval-bridge"
cp "$SP/conflicts.mjs" "$B/_conflicts.mjs"
(cd "$B" && node _conflicts.mjs "$@")
rm -f "$B/_conflicts.mjs"
