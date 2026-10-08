#!/usr/bin/env python3
"""Photograph the whole editor window, Slate and all.

`cap.py` photographs the level viewport and REQUIRES a camera transform, which
is exactly right for a world and exactly wrong for a user interface: it moves
the editor camera to wherever you asked and renders that, so a gate drawn in
UMG over a running game does not appear in it at all. This asks Slate for the
window instead, so what comes back is what a person is looking at.

  editshot.py out.png
"""
import base64, os, re, subprocess, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import rpc

out = sys.argv[1]
answer = rpc.raw('EditorToolset.EditorAppToolset', 'CaptureEditorImage', {})
found = re.search(r'"data\\?"\s*:\s*\\?"([A-Za-z0-9+/=]+)', answer)
if not found:
    print(answer[:400])
    raise SystemExit(1)
open(out, 'wb').write(base64.b64decode(found.group(1)))
# Down in steps, for the same reason cap.py does it: one big point-sample
# turns text into a comb.
for _ in range(2):
    subprocess.run(['sips', '-Z', '2600', out], capture_output=True)
subprocess.run(['sips', '-Z', '1400', out], capture_output=True)
print(out)
