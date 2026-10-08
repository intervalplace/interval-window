#!/usr/bin/env python3
"""INVENTORY SPRITES DRAWN FROM THE GEOMETRY, with no editor in the way.

`icons.py` photographs each item in Unreal in three passes and `matte.py`
shades them here. That arrangement is right and it is how most of the pack was
made -- but it depends on a scene capture asking the renderer's GBuffer for
base colour, and since `r.Substrate` went on that pass comes back neutral for
every item in the world. What was ruled out, at length, is in the note at the
top of `icons.py`'s `main`: it is not the shader compiler, not Lumen, not the
art, not the material instances, and not the capture's timing. Every slot
painted bright red through a dynamic instance still captured as (31,31,31).

The forged half of the pack does not need a renderer at all. Everything in
`Art/Forged` is an .obj with an .mtl beside it naming its slots, and every slot
is a flat colour out of `forge.PALETTE`. So the sprite can be drawn here, from
the same numbers the mesh was built from, under the same light `matte.py` uses
-- and the result cannot depend on the hour, the weather, the exposure, the
deferred path or which year's GBuffer the engine has this release.

WHAT IT COPIES FROM `icons.py`, deliberately, so the two kinds of sprite sit
beside each other in the same pack without looking like two packs:

  * the three-quarter view, from above and off to one side
  * the rule that a FLAT thing is turned to show its broad face, tipped
    twenty-five degrees so it is not a cut-out, and a roughly cubic thing is
    left exactly as it was authored
  * the framing, on the item's corners projected onto the camera's own axes
  * the light: one key over the left shoulder, a cool fill opposite, a
    generous ambient, and the sRGB encode done once at the very end
  * rendered at 512 and averaged down to 128 in premultiplied space, which IS
    the anti-aliasing

  sprite.py crossbow star_flail      by forged mesh name
  sprite.py --all                    every .obj in Art/Forged
"""
import math, os, struct, sys, zlib

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
from forge import PALETTE

ROOT = os.path.dirname(SP)
SRC = os.path.join(ROOT, 'Art', 'Forged')
OUT = os.path.join(ROOT, 'Art', 'Icons')
BIG = 512
SIDE = 128
# The same two lights `matte.py` reads its sprites by; see the note there.
KEY = (-0.40, 0.42, 0.82)
FILL = (0.45, -0.40, -0.10)


def srgb(x):
    if x <= 0.0031308:
        return 12.92 * x
    return 1.055 * (x ** (1.0 / 2.4)) - 0.055


def load(name):
    """Vertices, triangles and the palette colour of each triangle."""
    path = os.path.join(SRC, name + '.obj')
    vs, tris, cols = [], [], []
    cur = (0.5, 0.5, 0.5)
    for line in open(path, errors='ignore'):
        if line.startswith('v '):
            p = line.split()
            vs.append((float(p[1]), float(p[2]), float(p[3])))
        elif line.startswith('usemtl '):
            slot = line.split(None, 1)[1].strip()
            if slot not in PALETTE:
                raise SystemExit('%s uses the slot %r, which the forge palette '
                                 'does not name' % (name, slot))
            cur = PALETTE[slot]
        elif line.startswith('f '):
            idx = []
            for tok in line.split()[1:]:
                n = int(tok.split('/')[0])
                idx.append(n - 1 if n > 0 else len(vs) + n)
            for k in range(1, len(idx) - 1):
                tris.append((idx[0], idx[k], idx[k + 1]))
                cols.append(cur)
    return vs, tris, cols


def basis(vs):
    """The camera's right, up and forward for this item.

    THE SAME TWO RULES `icons.py` USES. A roughly cubic thing is looked at from
    the usual three-quarter angle. A FLAT thing -- a bow, a shield, a
    breastplate -- is looked at down its thinnest axis instead, because a fixed
    angle that happens to look along the flat draws a stick; and then tipped
    twenty-five degrees off it, because face-on a flat thing has no thickness
    and reads as a cut-out.
    """
    lo = [min(v[k] for v in vs) for k in range(3)]
    hi = [max(v[k] for v in vs) for k in range(3)]
    size = [hi[k] - lo[k] for k in range(3)]

    def norm(v):
        n = math.sqrt(sum(c * c for c in v)) or 1.0
        return tuple(c / n for c in v)

    def cross(a, b):
        return (a[1] * b[2] - a[2] * b[1],
                a[2] * b[0] - a[0] * b[2],
                a[0] * b[1] - a[1] * b[0])

    flat = min(size) / (max(size) or 1e-6)
    if flat > 0.40:
        # pitch -30, yaw 135: over the shoulder and down, the angle every
        # inventory in this genre uses.
        p, y = math.radians(-30.0), math.radians(135.0)
        fwd = (math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), math.sin(p))
    else:
        thin = size.index(min(size))
        axis = [0.0, 0.0, 0.0]
        axis[thin] = 1.0
        # Tipped a quarter-turn's sixth about whichever world axis is most
        # across it, so an edge shows.
        other = (thin + 1) % 3
        about = [0.0, 0.0, 0.0]
        about[other] = 1.0
        a = math.radians(25.0)
        ca, sa = math.cos(a), math.sin(a)
        d = sum(axis[k] * about[k] for k in range(3))
        rot = cross(about, axis)
        fwd = tuple(axis[k] * ca + rot[k] * sa + about[k] * d * (1 - ca)
                    for k in range(3))
        fwd = tuple(-c for c in norm(fwd))
    fwd = norm(fwd)
    up0 = (0.0, 0.0, 1.0)
    if abs(fwd[2]) > 0.98:
        up0 = (0.0, 1.0, 0.0)
    right = norm(cross(up0, fwd))
    up = cross(fwd, right)
    return right, up, fwd


def draw(name):
    vs, tris, cols = load(name)
    if not vs:
        raise SystemExit(name + ' has no vertices')
    right, up, fwd = basis(vs)
    mid = tuple((max(v[k] for v in vs) + min(v[k] for v in vs)) * 0.5
                for k in range(3))

    # FRAMED ON WHAT IS ACTUALLY SEEN, not on the longest edge of the box: a
    # long thing seen from the corner lies along the diagonal and covers about
    # seven tenths of it, so framing on the box wastes a third of the sprite.
    span = 0.0
    for v in vs:
        d = tuple(v[k] - mid[k] for k in range(3))
        span = max(span, abs(sum(d[k] * right[k] for k in range(3))),
                   abs(sum(d[k] * up[k] for k in range(3))))
    scale = (BIG * 0.46) / (span or 1.0)

    colour = [0.0] * (BIG * BIG * 3)
    alpha = bytearray(BIG * BIG)
    depth = [1e30] * (BIG * BIG)

    kx, ky, kz = KEY
    fx, fy, fz = FILL
    for t, (ia, ib, ic) in enumerate(tris):
        if max(ia, ib, ic) >= len(vs):
            continue
        pa, pb, pc = vs[ia], vs[ib], vs[ic]
        ux, uy, uz = (pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2])
        wx, wy, wz = (pc[0] - pa[0], pc[1] - pa[1], pc[2] - pa[2])
        nx, ny, nz = (uy * wz - uz * wy, uz * wx - ux * wz, ux * wy - uy * wx)
        ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        nx, ny, nz = nx / ln, ny / ln, nz / ln
        # THE NORMAL IS TURNED TO FACE THE EYE, not left as the winding found
        # it. A forged mesh is a run of lathes and tubes and nothing checks
        # their winding, so half the faces would be lit from behind.
        if nx * fwd[0] + ny * fwd[1] + nz * fwd[2] > 0.0:
            nx, ny, nz = -nx, -ny, -nz
        key = max(nx * kx + ny * ky + nz * kz, 0.0)
        fill = max(nx * fx + ny * fy + nz * fz, 0.0)
        lit = 0.62 + 1.45 * key + 0.38 * fill
        r, g, b = cols[t]
        lr, lg, lb = min(r * lit, 1.0), min(g * lit, 1.0), min(b * lit, 1.0)

        pts = []
        for p in (pa, pb, pc):
            d = tuple(p[k] - mid[k] for k in range(3))
            sx = sum(d[k] * right[k] for k in range(3)) * scale + BIG * 0.5
            sy = -sum(d[k] * up[k] for k in range(3)) * scale + BIG * 0.5
            sz = sum(d[k] * fwd[k] for k in range(3))
            pts.append((sx, sy, sz))
        (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = pts
        det = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(det) < 1e-9:
            continue
        minx = max(0, int(min(x0, x1, x2)))
        maxx = min(BIG - 1, int(max(x0, x1, x2)) + 1)
        miny = max(0, int(min(y0, y1, y2)))
        maxy = min(BIG - 1, int(max(y0, y1, y2)) + 1)
        for py in range(miny, maxy + 1):
            for px in range(minx, maxx + 1):
                l0 = ((y1 - y2) * (px + 0.5 - x2) + (x2 - x1) * (py + 0.5 - y2)) / det
                l1 = ((y2 - y0) * (px + 0.5 - x2) + (x0 - x2) * (py + 0.5 - y2)) / det
                l2 = 1.0 - l0 - l1
                if l0 < 0 or l1 < 0 or l2 < 0:
                    continue
                z = l0 * z0 + l1 * z1 + l2 * z2
                i = py * BIG + px
                if z >= depth[i]:
                    continue
                depth[i] = z
                alpha[i] = 255
                colour[i * 3] = lr
                colour[i * 3 + 1] = lg
                colour[i * 3 + 2] = lb

    # REDUCED IN PREMULTIPLIED SPACE, so the emptiness around the silhouette is
    # not dragged into the colour of its edge.
    step = BIG // SIDE
    out = bytearray(SIDE * SIDE * 4)
    for oy in range(SIDE):
        for ox in range(SIDE):
            sr = sg = sb = sa = 0.0
            for dy in range(step):
                base = ((oy * step + dy) * BIG + ox * step)
                for dx in range(step):
                    i = base + dx
                    if not alpha[i]:
                        continue
                    sa += 1.0
                    sr += colour[i * 3]
                    sg += colour[i * 3 + 1]
                    sb += colour[i * 3 + 2]
            if sa <= 0.0:
                continue
            o = (oy * SIDE + ox) * 4
            out[o] = min(255, int(srgb(sr / sa) * 255 + 0.5))
            out[o + 1] = min(255, int(srgb(sg / sa) * 255 + 0.5))
            out[o + 2] = min(255, int(srgb(sb / sa) * 255 + 0.5))
            out[o + 3] = min(255, int(sa / (step * step) * 255 + 0.5))
    return bytes(out)


def write_png(path, side, px):
    rows = b''.join(b'\x00' + px[y * side * 4:(y + 1) * side * 4]
                    for y in range(side))

    def chunk(tag, body):
        c = tag + body
        return struct.pack('>I', len(body)) + c + struct.pack('>I', zlib.crc32(c))
    open(path, 'wb').write(
        b'\x89PNG\r\n\x1a\n'
        + chunk(b'IHDR', struct.pack('>IIBBBBB', side, side, 8, 6, 0, 0, 0))
        + chunk(b'IDAT', zlib.compress(rows, 9)) + chunk(b'IEND', b''))


# THE WORD THE PACK USES, which is not always the file's name: the forge writes
# `star_flail.obj` and the world calls it `quick-flail`, and three of them are
# one mesh worn by three words.
WORDS = {
    'javelin': ('iron-javelin', 'steel-javelin', 'quick-javelin'),
    # One rod, four words: the shaft is the same length of wood whatever it was
    # cut from, and the grade shows in the material rather than the shape.
    # `fishing-rod` is not a word this world uses, so without this row the
    # drawing landed in a file nothing ever opens and all four rods kept
    # whatever the editor had made of them.
    'fishing_rod': ('rod', 'oak-rod', 'heartwood-rod', 'ironbark-rod'),
    # AND THE TWO THE RENAME LEFT BEHIND. The asset names are still `star_*`,
    # which is right: renaming a mesh does not change what it is a mesh OF.
    # The pack asks for the word the world uses now.
    'star_flail': ('quick-flail',),
    'star_grit': ('quick-grit',),
    # AND THE FALL STONE, which is not in ITEMS because every one of them is
    # minted for one citizen -- `fallstone:<key>:<day>`, built on the hood
    # exactly -- so the item vocabulary, which only holds interchangeable
    # words, has never named it and nothing ever drew it. It is the same rock
    # rubble is, so it is the same drawing: what makes one worth more than
    # another is whose it was, which is in the name and not in the picture.
    'rubble': ('rubble', 'fall-stone'),
}


def main(argv):
    names = ([f[:-4] for f in sorted(os.listdir(SRC)) if f.endswith('.obj')]
             if argv[:1] == ['--all'] else argv)
    if not names:
        print(__doc__.strip().splitlines()[-2].strip())
        return 1
    for n in names:
        px = draw(n)
        for word in WORDS.get(n, (n.replace('_', '-'),)):
            write_png(os.path.join(OUT, word + '.png'), SIDE, px)
        drawn = sum(1 for i in range(3, len(px), 4) if px[i])
        print('%-16s %5d pixels -> %s' % (n, drawn,
              ', '.join(WORDS.get(n, (n.replace('_', '-'),)))))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
