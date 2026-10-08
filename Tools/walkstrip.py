#!/usr/bin/env python3
"""A strip of consecutive frames of something walking, in one MCP session.

WHY A STRIP AND NOT A NUMBER. The world ticks once a second and hands this
window whole tiles; everything between two ticks is this window's own
interpolation, and whether that reads as walking or as a chess piece being slid
about is not something a single photograph can answer. Several frames in a row
can: a figure that interpolates advances a little in every frame, and one that
does not sits still and then jumps.

`cap.py` opens a fresh MCP session per photograph, which costs more wall clock
than a tick lasts. This keeps one session and photographs as fast as the editor
will answer.

  walkstrip.py out.png <n> <x> <y> <z> <pitch> <yaw> <roll>
"""
import base64, os, re, subprocess, sys, time
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import rpc
import sheet

out = sys.argv[1]
count = int(sys.argv[2])
x, y, z, p, yw, r = [float(v) for v in sys.argv[3:9]]

args = {'bShowUI': False, 'annotations': [],
        'captureTransform': {'location': {'x': x, 'y': y, 'z': z},
                             'rotation': {'pitch': p, 'yaw': yw, 'roll': r}}}

frames = []
t0 = time.time()
for i in range(count):
    answer = rpc.raw('EditorToolset.EditorAppToolset', 'CaptureViewport', args)
    found = re.search(r'"data\\?"\s*:\s*\\?"([A-Za-z0-9+/=]+)', answer)
    if not found:
        print(answer[:300])
        raise SystemExit(1)
    path = '%s/_walk_%02d.png' % (os.path.dirname(out), i)
    open(path, 'wb').write(base64.b64decode(found.group(1)))
    frames.append((time.time() - t0, path))

print('%d frames over %.1f s -- %.2f s apart, so about %.1f frames a tick'
      % (count, frames[-1][0], frames[-1][0] / max(1, count - 1),
         1.0 / max(1e-6, frames[-1][0] / max(1, count - 1))))

# Down to a strip width first: a contact sheet of full frames is unreadable
# and enormous.
cell = 430
for _, path in frames:
    subprocess.run(['sips', '-Z', str(cell), path], capture_output=True)

tiles = [sheet.read(path) for _, path in frames]
cw, ch = tiles[0][0], tiles[0][1]
cols = 3
rows = (len(tiles) + cols - 1) // cols
W, H = cw * cols, ch * rows
buf = bytearray(W * H * 3)
for n, (w, h, px) in enumerate(tiles):
    ox, oy = (n % cols) * cw, (n // cols) * ch
    for row in range(min(h, ch)):
        src = row * w * 3
        dst = ((oy + row) * W + ox) * 3
        buf[dst:dst + min(w, cw) * 3] = px[src:src + min(w, cw) * 3]
sheet.write(out, W, H, bytes(buf))
for _, path in frames:
    os.remove(path)
print(out)
