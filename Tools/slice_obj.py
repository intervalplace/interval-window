#!/usr/bin/env python3
"""Cut one piece out of a Wavefront OBJ, by material and by height.

WHY THIS EXISTS.

Six of the world's thirteen armour words are `*-plate`, and no CC0 pack in use
ships a breastplate: the free tiers carry helms and nothing for the body. What
they do ship is Quaternius's CC0 Knight, whose whole suit of armour is ONE
material group called `Armor` running from the greaves to the gorget.

A `.obj` is a text file of vertices and faces. Taking the faces that use one
material, and of those the ones that sit between two heights, is a dozen lines
of arithmetic -- no mesh editor, no Blender, and nothing that has to be
installed. It is the same trade `sheet.py` makes for PNGs.

WHAT IT DOES NOT DO. It does not close the cut. A slice through a suit of
armour leaves the waist and the arm holes open, which is correct for a
breastplate worn over a body: the body is what you would see through them, and
it is there.

  slice_obj.py <in.obj> <out.obj> <material> <ymin> <ymax>
"""
import sys


def cut(src, dst, want, lo, hi):
    vs, vts, vns = [], [], []
    keep, cur = [], None
    for line in open(src):
        f = line.split()
        if not f:
            continue
        if f[0] == 'v':
            vs.append(tuple(float(x) for x in f[1:4]))
        elif f[0] == 'vt':
            vts.append(line.rstrip('\n'))
        elif f[0] == 'vn':
            vns.append(line.rstrip('\n'))
        elif f[0] == 'usemtl':
            cur = f[1]
        elif f[0] == 'f' and cur == want:
            idx = [int(t.split('/')[0]) - 1 for t in f[1:]]
            # THE WHOLE FACE OR NONE OF IT. A face with one corner inside the
            # band and three outside is a triangle stretched across the cut,
            # which reads as a shard of metal hanging in the air.
            ys = [vs[i][1] for i in idx]
            if min(ys) >= lo and max(ys) <= hi:
                keep.append(f[1:])

    # Re-index: an OBJ written with the original numbers refers to vertices
    # that are no longer in the file.
    seen, order = {}, []
    for face in keep:
        for tok in face:
            a = tok.split('/')
            key = tok
            if key not in seen:
                seen[key] = len(order) + 1
                order.append(a)

    # AND MOVE IT TO ITS OWN ORIGIN. A piece cut out of a whole figure keeps
    # that figure's origin, which for a chest piece is somewhere under its
    # feet -- so hanging it on a bone puts it a metre and a half below the
    # shoulder it belongs to, and the offset that fixes that is a number
    # nobody can read. Centred on itself, the socket offset means what it says.
    pick = [vs[int(a[0]) - 1] for a in order]
    mid = tuple(sum(v[k] for v in pick) / len(pick) for k in range(3))

    out = ['# cut from %s: material %s, y %.3f..%.3f' % (src, want, lo, hi)]
    for a in order:
        v = vs[int(a[0]) - 1]
        out.append('v %.6f %.6f %.6f' % (v[0] - mid[0], v[1] - mid[1], v[2] - mid[2]))
    for a in order:
        if len(a) > 1 and a[1]:
            out.append(vts[int(a[1]) - 1])
    for a in order:
        if len(a) > 2 and a[2]:
            out.append(vns[int(a[2]) - 1])
    out.append('usemtl %s' % want)
    for face in keep:
        bits = []
        for tok in face:
            n = seen[tok]
            a = tok.split('/')
            bits.append('%d/%s/%s' % (n, n if len(a) > 1 and a[1] else '',
                                      n if len(a) > 2 and a[2] else ''))
        out.append('f ' + ' '.join(bits))
    open(dst, 'w').write('\n'.join(out) + '\n')
    print('%s: %d faces, %d verts' % (dst, len(keep), len(order)))


if __name__ == '__main__':
    cut(sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5]))
