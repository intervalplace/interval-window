#!/usr/bin/env python3
"""A CRACKED STONE FRAME for the title card, drawn here with no editor.

WHAT IT REPLACES. The card had a two-pixel ember hairline above the word
INTERVAL and another below it, and the objection to them was not that they
looked bad: it was that they look like every generated title slide there has
ever been. "The line above and below INTERVAL kind of screams AI and is very
generic." A motif that appears on ten thousand other pictures says nothing
about this world, however neatly it is drawn.

So: a border made of the thing the island is made of. Stone, cut, with the
cracks a cut stone has, and a carved inner edge so the words sit INSIDE
something rather than between two marks.

IT IS A NINE-SLICE. Unreal's Box brush takes one texture and a margin, stretches
the four edges and leaves the corners alone, so the frame fits any size the
title happens to be. That is why the corners here carry the heavy detail and
the edges are deliberately uniform along their length: an edge with a feature
in the middle of it smears when it stretches.

NO RANDOMNESS THAT IS NOT SEEDED. Every crack comes off a fixed hash, so the
frame is the same stone every time this runs, and re-running it is a no-op
rather than a new picture to re-approve.

  stoneframe.py [out.png]
"""
import math, os, struct, sys, zlib

SIDE = 256
MARGIN = 56           # the nine-slice margin, in pixels, matched in the widget
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'Art', 'UI', 'stone_frame.png')


def h(x, y, salt):
    """The same integer hash the rest of this project uses for placement."""
    n = (x * 374761393 + y * 668265263 + salt * 1442695041) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) & 0xFFFFFFFF
    n = (n * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFFFFFF) / 0xFFFFFFFF


def noise(x, y, scale, salt):
    """Value noise: four corners of a cell, smoothed. Enough for stone grain,
    and short enough to read."""
    fx, fy = x / scale, y / scale
    x0, y0 = int(math.floor(fx)), int(math.floor(fy))
    tx, ty = fx - x0, fy - y0
    sx = tx * tx * (3 - 2 * tx)
    sy = ty * ty * (3 - 2 * ty)
    a = h(x0, y0, salt)
    b = h(x0 + 1, y0, salt)
    c = h(x0, y0 + 1, salt)
    d = h(x0 + 1, y0 + 1, salt)
    return (a * (1 - sx) + b * sx) * (1 - sy) + (c * (1 - sx) + d * sx) * sy


def grain(x, y):
    """Stone at three scales: the block, the mottling, and the tooth."""
    return (noise(x, y, 46.0, 11) * 0.55
            + noise(x, y, 17.0, 23) * 0.30
            + noise(x, y, 5.0, 37) * 0.15)


def edge_distance(x, y):
    """How far inside the frame's band this pixel is, 0 at either lip and 1 in
    the middle of the stone. Outside the band it is negative."""
    band = MARGIN
    d = min(x, y, SIDE - 1 - x, SIDE - 1 - y)
    if d >= band:
        return -1.0                      # the hole in the middle
    return d / float(band)


# ---- THE CRACKS ARE DRAWN, NOT SAMPLED ----
#
# Two passes of this were made out of noise ridges and both came out looking
# like a jigsaw, for a reason no amount of tuning fixes: the contours of smooth
# value noise are ROUNDED and they close on themselves, so what you get is
# loops and lobes. A crack in stone is the opposite of that. It is a run of
# nearly straight segments that changes direction abruptly, branches at an
# angle, and travels from somewhere to somewhere rather than coming back on
# itself.
#
# So it is drawn: a seeded walk that steps, turns a little, occasionally turns
# a lot, and sometimes spawns a child going off at an angle. Rasterised once
# into a mask the main loop reads, which is also far cheaper than sampling
# three noise fields per pixel.
CRACKS = [[0.0] * SIDE for _ in range(SIDE)]


def _mark(x, y, weight):
    xi, yi = int(x), int(y)
    if 0 <= xi < SIDE and 0 <= yi < SIDE:
        if weight > CRACKS[yi][xi]:
            CRACKS[yi][xi] = weight


def _walk(x, y, angle, life, weight, salt, depth=0):
    """One crack, and the children it throws off."""
    step = 0
    while step < life:
        _mark(x, y, weight)
        # a little softness either side, so a crack has an edge rather than
        # being a single hard pixel that vanishes when the frame is scaled
        _mark(x + math.cos(angle + 1.57), y + math.sin(angle + 1.57), weight * 0.45)
        _mark(x + math.cos(angle - 1.57), y + math.sin(angle - 1.57), weight * 0.45)
        x += math.cos(angle)
        y += math.sin(angle)
        step += 1
        r = h(int(x), int(y), salt + step)
        angle += (r - 0.5) * 0.22                    # the constant wander
        if r > 0.97:
            angle += (h(step, int(x), salt) - 0.5) * 1.5   # and the sharp turn
        if depth < 2 and r < 0.012:
            _walk(x, y, angle + (0.7 if r < 0.006 else -0.7),
                  int(life * 0.45), weight * 0.7, salt + 991, depth + 1)
        if not (0 <= x < SIDE and 0 <= y < SIDE):
            return


def _split_the_stone():
    """Start them on the outer edge and send them inward: a crack that begins
    in the middle of a face and ends there looks drawn on."""
    for i in range(14):
        r = h(i, 7, 5150)
        side = i % 4
        t = h(i, 13, 606) * SIDE
        if side == 0:
            x, y, a = t, 0.0, 1.57
        elif side == 1:
            x, y, a = t, float(SIDE - 1), -1.57
        elif side == 2:
            x, y, a = 0.0, t, 0.0
        else:
            x, y, a = float(SIDE - 1), t, 3.14
        _walk(x, y, a + (r - 0.5) * 1.1, int(40 + r * 90), 0.7 + r * 0.3, 400 + i * 37)


_split_the_stone()


def crack(x, y):
    return CRACKS[y][x]


def main():
    px = bytearray()
    STONE = (0.42, 0.40, 0.36)           # the rock the island is cut from
    for y in range(SIDE):
        px.append(0)                      # PNG filter byte: none
        for x in range(SIDE):
            d = edge_distance(x, y)
            if d < 0.0:
                px += bytes((0, 0, 0, 0))  # the middle is a hole
                continue

            g = grain(x, y)
            v = 0.72 + g * 0.46

            # THE CARVED LIP. The inner edge is cut, so it catches light on
            # its upper face and drops to shadow on its lower one. Without
            # this the frame is a textured rectangle rather than something
            # with a thickness.
            lip = max(0.0, 1.0 - abs(d - 0.20) * 5.2)
            v += lip * 0.44
            shade = max(0.0, 1.0 - abs(d - 0.05) * 6.0)
            v -= shade * 0.48

            # and the outer arris, lit from above like everything else here
            outer = max(0.0, 1.0 - abs(d - 0.92) * 8.0)
            v += outer * 0.16

            v -= crack(x, y) * 0.52

            # THE CORNERS CARRY THE WEIGHT. A nine-slice stretches its edges
            # and leaves the corners alone, so anything that must not smear
            # belongs here. Darkened slightly, as a corner block of stone is.
            if min(x, SIDE - 1 - x) < MARGIN and min(y, SIDE - 1 - y) < MARGIN:
                v -= 0.06

            v = max(0.0, min(1.0, v))
            # fade the very lip of the hole so the words are not fenced by a
            # hard pixel edge
            a = 1.0 if d > 0.06 else max(0.0, d / 0.06)
            px += bytes((int(STONE[0] * v * 255), int(STONE[1] * v * 255),
                         int(STONE[2] * v * 255), int(a * 255)))

    def chunk(tag, body):
        c = tag + body
        return struct.pack('>I', len(body)) + c + struct.pack('>I', zlib.crc32(c))

    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', struct.pack('>IIBBBBB', SIDE, SIDE, 8, 6, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(bytes(px), 9))
           + chunk(b'IEND', b''))
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    with open(OUT, 'wb') as f:
        f.write(png)
    print('stone frame %dx%d, nine-slice margin %d -> %s'
          % (SIDE, SIDE, MARGIN, os.path.abspath(OUT)))


main()
