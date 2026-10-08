#!/bin/zsh
# Walk to a tile, however many runs it takes.
#
# A `walk` is one straight run and the world ends it after a few tiles, so a
# journey across the island is a series of them -- which is exactly what a
# person does by clicking again. This is that, with a limit, and it stops when
# the citizen stops making progress rather than hammering a wall.
#
#   travel.sh <x> <y> [tries]
SP="$(cd "$(dirname "$0")" && pwd)"
X=$1; Y=$2; TRIES=${3:-12}
LAST=""
for i in $(seq 1 $TRIES); do
  NOW=$("$SP/around.sh" 1 | head -1 | sed -E 's/ME ([0-9]+),([0-9]+).*/\1,\2/')
  if [ "$NOW" = "$X,$Y" ]; then echo "arrived at $NOW after $((i-1)) runs"; exit 0; fi
  if [ "$NOW" = "$LAST" ]; then echo "stopped at $NOW -- no progress"; exit 1; fi
  LAST="$NOW"
  echo "  $NOW -> $X,$Y"
  "$SP/do.sh" walk "$X" "$Y"
  sleep 18
done
echo "still at $("$SP/around.sh" 1 | head -1 | sed -E 's/ME ([0-9]+),([0-9]+).*/\1,\2/') after $TRIES runs"
