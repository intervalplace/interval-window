#!/bin/zsh
# One capture session at a chosen hour, then the hour handed back to the world.
#
# The last step matters: `ForceDay` is a diagnostic and leaving it on would mean
# the window quietly disagreed with every other window about what time it is.
# apply.py writes -1 back, which is "the world decides".
set -e
SP="$(dirname "$0")"
OUT=/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad
LOOK='/Game/Interval/IntervalLook.IntervalLook'

setday () {
  python3 "$SP/call_look.py" "$1"
}

python3 "$SP/mcp.py" editor_toolset.toolsets.object.ObjectTools set_properties \
  <(printf '{"instance":{"refPath":"%s"},"values":"{\\"ForceDay\\":0.88}"}' "$LOOK") >/dev/null
"$SP/sim.sh" 75

python3 "$SP/cap.py" $OUT/N_meadow.png  86250 47350 210 -7 218.7 0 1300
python3 "$SP/cap.py" $OUT/N_wood.png    84600 46000 320 -8  40   0 1300
python3 "$SP/cap.py" $OUT/N_town.png    93820 53360 210 -7 218.7 0 1300
python3 "$SP/cap.py" $OUT/N_gate.png    93100 48900 260 -4  90   0 1300
python3 "$SP/cap.py" $OUT/N_close.png   86020 47200 120 -2 218.7 0 1300

# Two frames three seconds apart, over grass, to measure the wind.
python3 "$SP/cap.py" $OUT/W1.png 84600 46000 200 -3 40 0 700
sleep 3
python3 "$SP/cap.py" $OUT/W2.png 84600 46000 200 -3 40 0 700
python3 - <<'PY'
import sys; sys.path.insert(0,'Tools')
from sheet import read
O="/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad"
w,h,a=read(O+'/W1.png'); _,_,b=read(O+'/W2.png')
n=moved=0
for y in range(h//3,h):
    for x in range(w):
        i=(y*w+x)*3; n+=1
        if abs(a[i]-b[i])+abs(a[i+1]-b[i+1])+abs(a[i+2]-b[i+2])>18: moved+=1
print('WIND %.1f%% of the ground half moved in three seconds' % (100.0*moved/max(n,1)))
PY

echo "--- handing the hour back to the world"
python3 "$SP/apply.py" | tail -1
