#!/bin/zsh
# Run the coverage report from the bridge's directory, where `ws` lives.
set -e
SP="$(cd "$(dirname "$0")" && pwd)"
B="$(dirname "$(dirname "$SP")")/interval-bridge"
cp "$SP/coverage.mjs" "$B/_coverage.mjs"
(cd "$B" && node _coverage.mjs "$@")
rm -f "$B/_coverage.mjs"
