#!/usr/bin/env python3
"""Lay finished sprites out in pack slots, to be judged where they will be seen.

An icon on a white page is not an icon in a dark recessed socket: a sprite that
looks crisp on paper can vanish into the slot it lives in. So this composites
each one onto the socket's own colour, read off `IntervalHud.cpp`.

  slots.py out.png [name ...]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from matte import read_png, write_png, OUT, SIDE

SOCKET = (0.052, 0.034, 0.022)      # Recess, from IntervalHud.cpp
COLS = 6


def main():
    out = sys.argv[1]
    names = sys.argv[2:] or sorted(f[:-4] for f in os.listdir(OUT) if f.endswith('.png'))
    rows = (len(names) + COLS - 1) // COLS
    W, H = SIDE * COLS, SIDE * rows
    buf = bytearray(W * H * 4)
    r, g, b = [int(c * 255) for c in SOCKET]
    for i in range(0, len(buf), 4):
        buf[i], buf[i + 1], buf[i + 2], buf[i + 3] = r, g, b, 255
    for k, n in enumerate(names):
        w, h, lanes, depth, px = read_png(os.path.join(OUT, n + '.png'))
        cx, cy = (k % COLS) * SIDE, (k // COLS) * SIDE
        for y in range(h):
            for x in range(w):
                s = (y * w + x) * 4
                a = px[s + 3] / 255.0
                if not a:
                    continue
                o = ((cy + y) * W + cx + x) * 4
                for c in range(3):
                    buf[o + c] = int(px[s + c] * a + buf[o + c] * (1 - a))
    write_png(out, W, H, bytes(buf))
    print('%d sprites, %dx%d' % (len(names), W, H))


main()
