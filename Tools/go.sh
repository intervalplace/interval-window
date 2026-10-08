#!/bin/zsh
# WALK THERE, AROUND WHATEVER IS IN THE WAY.
#
# travel.sh files a straight run and gives up when the citizen stops making
# progress, which is right for open country and useless in a town: a wall three
# tiles long ends the journey. map.sh knows where the walls are, so this walks
# the route map.sh finds -- one straight run at a time, re-routing after every
# arrival because the route goes stale the moment the citizen moves and more of
# the world comes into view.
#
#   go.sh <x> <y> [tries]
SP="$(cd "$(dirname "$0")" && pwd)"
X=$1; Y=$2; TRIES=${3:-20}
# IS THERE A WINDOW AT ALL?
#
# Every deed this tool files goes into a file that the LIVE EDITOR reads on
# its tick. With no play session there is no hand to read it, every line is
# dropped with "no hand yet" in the remote's own log, and the citizen stands
# still -- which is indistinguishable from the world refusing every step. That
# cost twenty-two minutes of a citizen's day and an investigation into the
# ninety-minute ceiling, the crags, the ridge predicate and the crossing rules,
# none of which were the problem.
LOG="/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/play.log"
# ONLY WHAT THE PING ITSELF ANSWERED. Reading the tail of the log catches
# whatever was there before -- including the very "no hand yet" lines from the
# session this is checking has been fixed -- so the mark is taken first and
# only what lands after it is read.
MARK=$(wc -l < "$LOG" 2>/dev/null || echo 0)
"$SP/do.sh" ping-the-hand
sleep 3
if tail -n +$((MARK + 1)) "$LOG" 2>/dev/null | grep -q 'no hand yet'; then
  echo "there is no play session: the window is not running, so nothing can be filed."
  echo "  start one with  Tools/play.sh  and cross the gate with  do.sh gate"
  exit 1
fi
for i in $(seq 1 $TRIES); do
  NOW=$("$SP/around.sh" 1 | head -1 | sed -E 's/ME ([0-9]+),([0-9]+).*/\1 \2/')
  CX=${NOW% *}; CY=${NOW#* }
  if [ "$CX" = "$X" ] && [ "$CY" = "$Y" ]; then echo "arrived $X,$Y in $((i-1)) runs"; exit 0; fi
  # One straight run at a time. Taking the whole route and firing it blind is
  # what failed before: the hand files the remainder of a walk itself, so a
  # queued second command collides with the leg already in flight.
  # THE MAP ONLY SEES SO FAR. A target beyond it has no route at all, which
  # is not the same as being unreachable -- so a distant goal is clamped to
  # the edge of sight and walked toward, one eyeful at a time.
  DX=$((X - CX)); DY=$((Y - CY))
  AX=${DX#-}; AY=${DY#-}
  FAR=$AX; [ $AY -gt $AX ] && FAR=$AY
  TX=$X; TY=$Y
  # HOW FAR TO AIM. The world allows WALK_MAX_STEPS = 512 in ONE deed -- its
  # own comment says a single walk can carry a citizen across the map -- so
  # the only real limit is how far the map can see to route. Aiming eleven
  # tiles ahead was paying six deeds for what one would do, and made crossing
  # the island a job of minutes instead of seconds.
  if [ $FAR -gt 50 ]; then
    TX=$((CX + DX * 50 / FAR)); TY=$((CY + DY * 50 / FAR))
  fi
  RUNS=$("$SP/map.sh" 60 "$TX" "$TY" 2>/dev/null | grep '^straight runs:' \
         | sed -E 's/^straight runs: *//')
  if [ -z "$RUNS" ]; then echo "no route to $X,$Y from $CX,$CY (out of sight or walled in)"; exit 1; fi
  # A LEG THAT ENDS WHERE IT BEGAN IS NOT A LEG.
  #
  # The route is computed from the ROUTE'S first tile, which is not always the
  # tile the citizen is standing on -- so the first straight run can name the
  # citizen's own square. That files `walk` with no direction at all, which the
  # world refuses ("a walk that goes nowhere is not a walk"), and the next pass
  # computes the same route and files the same nothing: twenty identical
  # refusals and a citizen who never moved, which is exactly what was seen.
  # So the first run that actually goes somewhere is the one taken.
  LEG=''
  # Split on the bar. Written with `tr` and a plain loop rather than a zsh
  # array, because this file is run with `bash go.sh` as often as with zsh.
  while IFS= read -r _L; do
    [ -z "$_L" ] && continue
    _P=$(echo "$_L" | sed -E 's/.*walk ([0-9]+) ([0-9]+).*/\1 \2/')
    if [ "$_P" != "$CX $CY" ]; then LEG="$_P"; break; fi
  done <<EOF
$(echo "$RUNS" | tr '|' '\n')
EOF
  if [ -z "$LEG" ]; then echo "every leg of the route ends where it began, at $CX,$CY"; exit 1; fi
  # WAIT AS LONG AS THE RUN ACTUALLY TAKES, and no longer. A citizen walks one
  # tile per interval, so a twelve-tile run needs twelve seconds and a one-tile
  # run needs about four -- and a flat wait spends the difference doing nothing.
  # Crossing the island, most runs are short (the scatter makes paths wiggle),
  # so the flat nine seconds was mostly idling.
  LX=${LEG% *}; LY=${LEG#* }
  RX=$((LX - CX)); RY=$((LY - CY)); RX=${RX#-}; RY=${RY#-}
  RUN=$RX; [ $RY -gt $RX ] && RUN=$RY
  echo "  at $CX,$CY -> walk $LEG  (${RUN} tiles)"
  "$SP/do.sh" walk $LEG
  sleep $((RUN + 4))
  # A RUN THAT MOVED NOBODY, TRIED AGAIN ONE TILE AT A TIME.
  #
  # A `walk` is a straight run and the world takes it whole or not at all, so a
  # single tile anywhere along it that the map cannot see -- a beast standing
  # in the road, a wall the frame did not carry that far -- refuses the entire
  # leg. The map then recomputes the same route, files the same run, and is
  # refused again: twenty identical failures and a citizen who never moved.
  # Observed repeatedly, and always with the same tell -- the FIRST step of the
  # refused run is accepted on its own.
  #
  # So when a leg moves nobody, take one tile in the same direction. One step
  # is the smallest thing the world can refuse for a reason the map does not
  # know, and taking it shifts the citizen far enough that the next route is a
  # different route rather than the same one again.
  NOW2=$("$SP/around.sh" 1 | head -1 | sed -E 's/ME ([0-9]+),([0-9]+).*/\1 \2/')
  NX=${NOW2% *}; NY=${NOW2#* }
  if [ "$NX" = "$CX" ] && [ "$NY" = "$CY" ]; then
    SX=$CX; SY=$CY
    [ $LX -gt $CX ] && SX=$((CX + 1)); [ $LX -lt $CX ] && SX=$((CX - 1))
    [ $LY -gt $CY ] && SY=$((CY + 1)); [ $LY -lt $CY ] && SY=$((CY - 1))
    if [ $RUN -gt 1 ]; then
      echo "    run refused; one tile instead -> $SX,$SY"
      "$SP/do.sh" walk $SX $SY
      sleep 5
      NOW3=$("$SP/around.sh" 1 | head -1 | sed -E 's/ME ([0-9]+),([0-9]+).*/\1 \2/')
      NX=${NOW3% *}; NY=${NOW3#* }
    fi
    # AND IF EVEN ONE TILE IS REFUSED, GO ROUND THE CORNER.
    #
    # The map sees ten tiles and the world sees everything, so a route can
    # aim through a thing the frame never carried -- a keeper standing in a
    # doorway, a beast that respawned onto the one diagonal every route wants.
    # Re-routing then produces the SAME route and the same refusal: observed
    # twenty times in a row, four separate times in one journey, with a citizen
    # who never moved an inch.
    # So the two tiles either side of the blocked step are tried in turn. One
    # of them almost always opens, and moving at all is what makes the next
    # route a different route instead of the same one again.
    if [ "$NX" = "$CX" ] && [ "$NY" = "$CY" ]; then
      for TRY in "$SX $CY" "$CX $SY"; do
        [ "$TRY" = "$CX $CY" ] && continue
        echo "    step refused; trying round the corner -> $TRY"
        "$SP/do.sh" walk $TRY
        sleep 5
        NOW4=$("$SP/around.sh" 1 | head -1 | sed -E 's/ME ([0-9]+),([0-9]+).*/\1 \2/')
        [ "$NOW4" != "$CX $CY" ] && break
      done
    fi
  fi
done
# WHERE IT ACTUALLY GOT TO, ASKED AFRESH.
#
# This printed `$CX,$CY`, which is the position read at the TOP of the last
# iteration -- before that iteration's walk. So a run that made progress right
# up to the last tile reported the tile before it, and a journey that was
# moving steadily the whole time read as "gave up ... at" the place it started
# from. That sent this session chasing imaginary walls more than once.
FIN=$("$SP/around.sh" 1 | head -1 | sed -E 's/ME ([0-9]+),([0-9]+).*/\1,\2/')
if [ "$FIN" = "$X,$Y" ]; then
  echo "arrived $X,$Y"
else
  echo "out of tries after $TRIES runs -- at $FIN, still short of $X,$Y"
fi
