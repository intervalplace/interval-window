#!/usr/bin/env python3
"""The pointer, drawn as a made thing rather than a system arrow.

The first attempt was an arrow: correct, legible, and exactly what every
operating system already draws. Which was the objection -- "that cursor looks
like a normal cursor. Look at the old RPGs from like the mid 2000s, they had
such cool cursors which made it feel more alive and immersive... check Silkroad
online and guild wars".

What those have in common is worth writing down, because it is not decoration
for its own sake:

  IT IS AN OBJECT, NOT A SYMBOL. A tapered blade with a spine and a curved
  edge, cast in metal, lit from one side. It has a front and a back.

  IT IS GOLD OR BRONZE, not white. A warm metal reads on grass, on stone and
  on water, and it belongs to the same world as the brass on the panels.

  IT HAS A DARK OUTLINE AND A SHADOW, so it never disappears into whatever is
  behind it -- which on a top-down view of a whole landscape is most colours.

  AND IT IS ASYMMETRIC: a straight edge on one side, a concave sweep on the
  other, with a small ornament where the blade meets the tail. That asymmetry
  is most of why it reads as forged rather than drawn.

The shapes are bezier outlines, filled with a gradient along the blade and a
bright rim down the lit edge.

  cursors.py       writes Art/Icons/cursor_*.png
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from matte import write_png

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'Art', 'Icons')
# A BIGGER CANVAS, because the drawing on it is bigger. The shape still fills
# about ninety per cent of it, exactly as it did at 96, so everything measured
# as a fraction of the canvas below is unchanged -- see K.
SIDE = 128
SS = 3
# Everything in `render` that is a WIDTH rather than a shape -- the inward
# stroke that makes the outline, the offset the shadow is cast at -- was
# measured on a 96 canvas. They are fractions of the drawing, not absolute
# pixels, so they scale with it or a bigger cursor comes out with a hairline
# round it.
K = SIDE / 96.0                      # supersamples per axis

INK = (22, 16, 10)
GOLD_HI = (252, 232, 168)
GOLD = (214, 168, 74)
GOLD_LO = (126, 88, 32)
GEM = (128, 44, 40)


def bez(p0, p1, p2, p3, n=18):
    """A cubic, sampled. Enough points that the fill sees a curve."""
    out = []
    for i in range(n + 1):
        t = i / float(n)
        u = 1.0 - t
        out.append((
            u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0],
            u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1]))
    return out


def inside(px, py, poly):
    hit = False
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        if (ay > py) != (by > py):
            if px < ax + (py - ay) * (bx - ax) / (by - ay):
                hit = not hit
    return hit


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def render(path, blade, inlay=None, gem=None, tint=None):
    """Fill the outline with lit metal, outline it, and lay a shadow under it."""
    body = tint or (GOLD_HI, GOLD, GOLD_LO)
    xs = [p[0] for p in blade]
    ys = [p[1] for p in blade]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    buf = bytearray(SIDE * SIDE * 4)

    for y in range(SIDE):
        for x in range(SIDE):
            got = edge = shade = 0
            for sy in range(SS):
                for sx in range(SS):
                    px = x + (sx + 0.5) / SS
                    py = y + (sy + 0.5) / SS
                    if inside(px, py, blade):
                        got += 1
                        # An inward stroke: a sample close to the outside is
                        # outline. Done by probing rather than by offsetting
                        # the path, which keeps the silhouette exact.
                        if any(not inside(px + dx, py + dy, blade)
                               for dx, dy in ((1.6*K, 0), (-1.6*K, 0), (0, 1.6*K),
                                              (0, -1.6*K), (1.2*K, 1.2*K), (-1.2*K, -1.2*K),
                                              (1.2*K, -1.2*K), (-1.2*K, 1.2*K))):
                            edge += 1
                    # THE SHADOW, two pixels down and right, so the cursor sits
                    # above the world instead of being printed on it.
                    elif inside(px - 2.2*K, py - 2.6*K, blade):
                        shade += 1
            o = (y * SIDE + x) * 4
            if got:
                a = got / float(SS * SS)
                k = edge / float(got)
                # ALONG the blade, tip pale and tail deep: metal catches the
                # light where it is thin.
                run = (y - y0) / max(y1 - y0, 1.0)
                lit = mix(body[0], body[1], min(run * 1.9, 1.0))
                lit = mix(lit, body[2], max(run - 0.55, 0.0) / 0.45)
                # And a bright rim down the left, which is the lit side.
                across = (x - x0) / max(x1 - x0, 1.0)
                if across < 0.34:
                    lit = mix(lit, body[0], (0.34 - across) / 0.34 * 0.70)
                # And a thin catch of light just inside the lit edge, which is
                # what makes a flat fill look like polished metal.
                if 0.06 < across < 0.16 and 0.10 < run < 0.72:
                    lit = mix(lit, (255, 252, 236), 0.55)
                col = mix(lit, INK, k)
                # The cast channel, deep enough to be seen through the
                # gradient that runs over it.
                if inlay and inside(x + 0.5, y + 0.5, inlay) and k < 0.4:
                    col = mix(col, body[2], 0.80)
                if gem and inside(x + 0.5, y + 0.5, gem) and k < 0.4:
                    col = mix(GEM, body[0], 0.18)
                buf[o], buf[o+1], buf[o+2], buf[o+3] = col[0], col[1], col[2], int(a * 255)
            elif shade:
                a = shade / float(SS * SS) * 0.45
                buf[o], buf[o+1], buf[o+2], buf[o+3] = 8, 6, 4, int(a * 255)
    write_png(path, SIDE, SIDE, bytes(buf))


# ---- HOW FAR OVER IT LEANS, AND HOW BIG ----
#
# The first blade was drawn very nearly upright: tip at (6, 4), waist at
# (18, 66), which is seventy-nine degrees off the horizontal. That is the angle
# an operating system's I-beam stands at and not the angle a pointer does, and
# it was noticed straight away -- "i think the cursor should be a little bigger
# and more diagonal it's too straight/vertical".
#
# Both are one transform about the TIP, which is the hot spot and must not
# move: everything is rotated by LEAN and then scaled by GROW, so the point
# stays exactly where the mouse is and the blade swings out from under it.
# Eighteen degrees brings the blade to about sixty-one off the horizontal,
# which reads as an object lying across the screen rather than standing on it.
#
# AND EIGHTEEN IS ABOUT THE LIMIT, which is worth writing down because the
# obvious next thought is to lean it further. This blade's upper edge is a
# deep concave sweep from the ornament back to the tip; past twenty degrees or
# so that sweep comes level, and a broad gold shape with a horizontal top edge
# and a hook under it stops reading as a blade and starts reading as a PENNANT
# on a stick. Rendered at -12, -20 and -28 and compared: -28 is a flag. If it
# ever has to lean further than this the shape has to be narrowed as well, not
# just turned.
#
# The canvas is 128 rather than 96 to carry it: after leaning, the shape
# reaches (101, 119) at GROW, which leaves a margin on every side for the
# outline and the shadow and gives the bigger on-screen pointer the texels to
# be drawn from.
LEAN = -18.0
GROW = 1.60
TIP = (6.0, 4.0)


def lean(poly):
    """Swing a shape out about the tip and make it bigger, in that order."""
    a = math.radians(LEAN)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for x, y in poly:
        dx, dy = x - TIP[0], y - TIP[1]
        rx, ry = dx * ca - dy * sa, dx * sa + dy * ca
        out.append((TIP[0] + rx * GROW, TIP[1] + ry * GROW))
    return out


def point_blade():
    """A slender blade with a shoulder, a waist and a swept barb.

    Drawn long rather than wide. The first version was a triangle with a tail,
    which is the shape of a system arrow whatever colour it is painted; what
    makes the old MMO pointers read as objects is that the blade is three or
    four times longer than it is broad, the two edges are not mirror images,
    and there is a distinct SHOULDER where the blade ends and the ornament
    begins.
    """
    p = []
    # The lit edge: long, very slightly convex, tip to waist.
    p += bez((6, 4), (9, 26), (13, 48), (18, 66))
    # The waist, then the barb swept back and down.
    # A NARROWER TAIL. The first pass came to a club: the barb has to be
    # slender enough that the eye reads a blade with a hook, not a boot.
    p += bez((18, 66), (19, 72), (20, 76), (18, 81))
    p += bez((18, 81), (24, 88), (32, 88), (33, 79))
    p += bez((33, 79), (30, 70), (28, 62), (26, 55))
    # Up the inner edge to the shoulder.
    p += bez((26, 55), (32, 53), (38, 50), (43, 47))
    # The shoulder's own small point, which is the ornament.
    p += bez((43, 47), (50, 45), (56, 41), (58, 36))
    p += bez((58, 36), (49, 32), (40, 27), (33, 22))
    # And the deep concave sweep back to the tip.
    p += bez((33, 22), (24, 16), (14, 9), (6, 4))
    return p


def point_inlay():
    """The channel down the spine, cast a shade deeper than the face."""
    return (bez((13, 18), (17, 32), (21, 44), (25, 55))
            + bez((25, 55), (31, 51), (38, 46), (44, 41))
            + bez((44, 41), (34, 32), (23, 24), (13, 18)))


def point_gem():
    """One stone at the shoulder, where the ornament meets the blade."""
    out = []
    for i in range(16):
        a = 2.0 * math.pi * i / 16
        out.append((43.5 + math.cos(a) * 3.6, 36.5 + math.sin(a) * 3.4))
    return out


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    blade = lean(point_blade())
    inlay = lean(point_inlay())
    gem = lean(point_gem())
    render(os.path.join(OUT, 'cursor_point.png'), blade, inlay, gem)
    # THE SAME BLADE IN STEEL, for the pointer over something that cannot be
    # acted on -- a wall, another citizen's ground. Same object, colder metal.
    render(os.path.join(OUT, 'cursor_stay.png'), blade, inlay, gem,
           tint=((236, 240, 246), (158, 168, 182), (78, 86, 98)))
    print('forged 2 cursors into %s' % OUT)


main()
