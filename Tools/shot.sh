#!/bin/zsh
# Decode the newest MCP viewport capture into a PNG I can actually look at.
S="/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad"
F=$(ls -t "/Users/matsjulner/.claude/projects/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/tool-results/"*.txt | head -1)
OUT="$S/${1:-shot}.png"
python3 - "$F" "$OUT" <<'PY'
import sys, re, base64
src, out = sys.argv[1], sys.argv[2]
s = open(src).read()
m = re.search(r'"data"\s*:\s*"([^"]+)"', s)
open(out, 'wb').write(base64.b64decode(m.group(1)))
cam = re.search(r'"cameraLocation":\{[^}]*\}', s)
print(cam.group(0) if cam else '')
PY
sips -Z 1100 "$OUT" >/dev/null 2>&1
echo "$OUT"
