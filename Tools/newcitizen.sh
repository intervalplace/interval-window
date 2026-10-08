#!/bin/zsh
# A FRESH CITIZEN, because the one we had has used their day.
#
# The world gives a citizen ninety minutes a day and then takes every deed it
# is offered. What that looks like from inside the window is a citizen who
# stops moving: the walk is filed, the world declines it, and -- until the feed
# was put in the chat box -- nothing whatever was said about why. Hours can go
# into "the pathfinding is broken" before anybody checks whether the world is
# still listening.
#
# The standing instruction is to mint a new key pair and carry on as somebody
# else. The bridge does the minting itself: point it at a key file that does
# not exist and it writes one. The private key never leaves this machine and
# never enters Unreal, which is the whole architecture.
#
#   newcitizen.sh            -- next free key file
#   newcitizen.sh 12         -- that one
set -e
B="/Users/matsjulner/Documents/Unreal Projects/interval-bridge"
cd "$B"

if [ -n "$1" ]; then
  N="$1"
else
  N=2
  while [ -f "unreal-key-$N.json" ]; do N=$((N + 1)); done
fi
KEY="./unreal-key-$N.json"

OLD=$(pgrep -f "unreal-bridge.mjs" | head -1)
if [ -n "$OLD" ]; then
  echo "retiring the bridge at pid $OLD"
  kill "$OLD" 2>/dev/null || true
  for _ in $(seq 1 15); do pgrep -f unreal-bridge.mjs >/dev/null || break; sleep 1; done
  pkill -9 -f unreal-bridge.mjs 2>/dev/null || true
fi

echo "starting a bridge on $KEY"
(node unreal-bridge.mjs --pillar https://interval.place --port 7777 --key "$KEY" \
   > /tmp/bridge.log 2>&1 &)
for _ in $(seq 1 40); do grep -q "citizen " /tmp/bridge.log 2>/dev/null && break; sleep 1; done
grep -E "minted|citizen " /tmp/bridge.log | tail -2
