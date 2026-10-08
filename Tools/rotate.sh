#!/bin/zsh
# ROTATE TO A FRESH CITIZEN, when the old one has spent their ninety minutes.
#
# The world allows 5400 intervals of PRESENCE in any rolling 86400-interval
# window. Spend them and the citizen is STOOD DOWN -- still standing there,
# still holding everything, simply unable to act until the window rolls. The
# engine's own comment is clear that a second keypair is not a way around that
# ceiling, it is the PRICE of it: skills, standing, kept names, sworn callings
# and located vaults all stay behind with the citizen who earned them.
#
# So this never destroys a key. The old file stays exactly where it is, and the
# citizen in it keeps their hatchet and their logs and can be returned to once
# the window has rolled. The bridge mints a new citizen for any --key path that
# does not exist yet, so rotating is only a matter of naming a new one.
#
# IT COSTS FIVE MINUTES. The world's VIGIL_TICKS is 300 -- "five minutes at a
# second an interval. FIVE, NOT TEN, AND NOT SEVENTEEN" -- and the bridge now
# reads it out of the hello tables instead of keeping a hand copy that went
# stale when the interval changed from 600ms to a second.

set -e
B="/Users/matsjulner/Documents/Unreal Projects/interval-bridge"
NAME=$1
if [ -z "$NAME" ]; then
  n=2
  while [ -f "$B/unreal-key-$n.json" ]; do n=$((n+1)); done
  NAME="unreal-key-$n.json"
fi
[ -f "$B/$NAME" ] && echo "note: $NAME already exists -- returning to that citizen, not minting one"

OLD=$(pgrep -f "node unreal-bridge.mjs" || true)
if [ -n "$OLD" ]; then
  echo "standing the old bridge down (its key file is untouched)"
  pkill -f "node unreal-bridge.mjs" || true
  sleep 2
fi
cd "$B"
(node unreal-bridge.mjs --pillar https://interval.place --port 7777 --key "./$NAME" > /tmp/bridge.log 2>&1 &)
sleep 20
grep -E "minted|citizen|adopted" /tmp/bridge.log | tail -3
echo
echo "now the five-minute wait (VIGIL_TICKS, read from the world): the window knocks,"
echo "and the panel says how far through the wait the citizen is."
