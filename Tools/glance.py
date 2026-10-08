#!/usr/bin/env python3
"""Look at a mesh WITHOUT the editor: three orthographic silhouettes, shaded.

Deciding whether a kit's mesh is the right art is a question about its SHAPE,
and the obvious way to answer it -- spawn it in the level and photograph it --
costs a round trip through the editor, disturbs a window somebody is watching,
and wants PIE stopped. Every kit in this project also ships its meshes as
Wavefront .obj beside the .fbx, which is a text file with the vertices in it.

So this reads the .obj and draws it: front, side and top, flat-shaded from a
fixed light, with a painter's depth sort. It is not a render and is not meant
to be one. It answers "is that bridge section an arch or a slab, and is it
crumbled at the ends", which is the only question worth asking before deciding
whether to use a mesh or author a new one.

  glance.py Art/Ruins/BridgeSection.obj [out.png]

The three panels are the XY, ZY and XZ planes. They are NOT labelled front,
side and top because the project's two kinds of .obj disagree about up: a
Quaternius kit is Y-up and anything out of `forge.py` is Z-up.
"""
import os, struct, sys, zlib

SIDE = 360          # per view; the sheet is three of these side by side
PAD = 12


def load(path):
    """Vertices and triangles from a Wavefront .obj. Faces are fanned."""
    vs, tris = [], []
    for line in open(path, 'r', errors='ignore'):
        if line.startswith('v '):
            p = line.split()
            vs.append((float(p[1]), float(p[2]), float(p[3])))
        elif line.startswith('f '):
            idx = []
            for tok in line.split()[1:]:
                n = int(tok.split('/')[0])
                idx.append(n - 1 if n > 0 else len(vs) + n)
            for k in range(1, len(idx) - 1):
                tris.append((idx[0], idx[k], idx[k + 1]))
    return vs, tris


def view(vs, tris, axes, flip):
    """One orthographic projection: (u, v) on screen, w toward the eye."""
    au, av, aw = axes
    W = H = SIDE
    buf = bytearray([26, 22, 18] * (W * H))          # the ink board's own dark
    if not tris:
        return buf
    us = [v[au] for v in vs]
    vsn = [v[av] for v in vs]
    lo_u, hi_u = min(us), max(us)
    lo_v, hi_v = min(vsn), max(vsn)
    span = max(hi_u - lo_u, hi_v - lo_v, 1e-6)
    s = (SIDE - 2 * PAD) / span
    cu, cv = (lo_u + hi_u) / 2, (lo_v + hi_v) / 2

    def to_px(v):
        x = (v[au] - cu) * s + SIDE / 2
        y = (v[av] - cv) * s * (-1 if flip else 1) + SIDE / 2
        return x, y

    depth = [-1e30] * (W * H)
    for a, b, c in tris:
        if max(a, b, c) >= len(vs):
            continue
        pa, pb, pc = vs[a], vs[b], vs[c]
        # flat normal, for the one light
        ux, uy, uz = (pb[0]-pa[0], pb[1]-pa[1], pb[2]-pa[2])
        vx, vy, vz = (pc[0]-pa[0], pc[1]-pa[1], pc[2]-pa[2])
        nx, ny, nz = (uy*vz - uz*vy, uz*vx - ux*vz, ux*vy - uy*vx)
        ln = (nx*nx + ny*ny + nz*nz) ** 0.5 or 1.0
        nx, ny, nz = nx/ln, ny/ln, nz/ln
        lit = 0.30 + 0.70 * max(0.0, nx*0.40 + ny*0.28 + nz*0.87)
        shade = (int(210*lit), int(196*lit), int(172*lit))
        w = (pa[aw] + pb[aw] + pc[aw]) / 3.0
        (x0, y0), (x1, y1), (x2, y2) = to_px(pa), to_px(pb), to_px(pc)
        minx = max(0, int(min(x0, x1, x2)));  maxx = min(W-1, int(max(x0, x1, x2)) + 1)
        miny = max(0, int(min(y0, y1, y2)));  maxy = min(H-1, int(max(y0, y1, y2)) + 1)
        d = (y1-y2)*(x0-x2) + (x2-x1)*(y0-y2)
        if abs(d) < 1e-9:
            continue
        for py in range(miny, maxy + 1):
            for px in range(minx, maxx + 1):
                l0 = ((y1-y2)*(px+0.5-x2) + (x2-x1)*(py+0.5-y2)) / d
                l1 = ((y2-y0)*(px+0.5-x2) + (x0-x2)*(py+0.5-y2)) / d
                l2 = 1.0 - l0 - l1
                if l0 < 0 or l1 < 0 or l2 < 0:
                    continue
                i = py * W + px
                if w <= depth[i]:
                    continue
                depth[i] = w
                buf[i*3:i*3+3] = bytes(shade)
    return buf


def png(path, width, height, rows):
    raw = b''.join(b'\x00' + bytes(r) for r in rows)
    def chunk(tag, body):
        c = tag + body
        return struct.pack('>I', len(body)) + c + struct.pack('>I', zlib.crc32(c))
    out = b'\x89PNG\r\n\x1a\n'
    out += chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    out += chunk(b'IDAT', zlib.compress(raw, 6))
    out += chunk(b'IEND', b'')
    open(path, 'wb').write(out)


def main(argv):
    src = argv[0]
    dst = argv[1] if len(argv) > 1 else os.path.splitext(src)[0] + '.glance.png'
    vs, tris = load(src)
    if not vs:
        print('no vertices in ' + src); return 1
    lo = [min(v[k] for v in vs) for k in range(3)]
    hi = [max(v[k] for v in vs) for k in range(3)]
    print('%s  %d verts %d tris  span %.1f x %.1f x %.1f (obj units)'
          % (os.path.basename(src), len(vs), len(tris),
             hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2]))
    # THE THREE PLANES, AND NOT "FRONT, SIDE, TOP" -- because the two kinds of
    # .obj in this project do not agree about which way is up. A Quaternius kit
    # exports Y-up, so its XY plane is the elevation; `forge.py` builds in
    # centimetres with Z as height, so ITS XZ plane is. Naming the columns
    # after the axes is the only labelling that is true of both.
    views = [view(vs, tris, (0, 1, 2), True),
             view(vs, tris, (2, 1, 0), True),
             view(vs, tris, (0, 2, 1), True)]
    W = SIDE * 3
    rows = []
    for y in range(SIDE):
        row = bytearray()
        for v in views:
            row += v[y*SIDE*3:(y+1)*SIDE*3]
        rows.append(row)
    png(dst, W, SIDE, rows)
    print('wrote ' + dst + '   (XY | ZY | XZ; a forged piece is Z-up, a kit is Y-up)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
