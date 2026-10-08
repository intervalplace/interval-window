#!/usr/bin/env python3
"""How big a thing in an FBX actually is, measured from the file.

WHY THIS EXISTS, AND IT IS THE SAME REASON A THIRD TIME.

`get_bounds` on a skeletal mesh reports the ANIMATED extent, not the model's.
`goblin_a` came back at 462 metres because one of its clips walks the root a
long way, every wild beast was scaled by dividing a real animal's size by that
462, and the whole bestiary was drawn about a centimetre and a half tall --
first reported from the stream as cylinders walking around, then, once they
drew at all, as "now they're invisible".

The glTF beasts were fixed by reading the source file. The FBX bestiary has
the same trap and no reader, so this is that reader. It takes the bind-pose
vertex positions straight out of the file and asks nothing of the engine.

  fbxsize.py Sheep.fbx [...]      -> name, extent in metres, longest axis

A binary FBX is a tree of nodes. Each node is a header (three integers, a
name), a property list, then children, and the list ends with a null record.
`Vertices` is a node whose single property is a double array, which may be
zlib-compressed -- that array is the model, in centimetres, before any bone
moved it.
"""
import struct, sys, zlib


def _props(buf, at, count):
    """The property list of one node, as python values. Arrays come back whole."""
    out = []
    for _ in range(count):
        kind = chr(buf[at]); at += 1
        if kind in 'CBYIL':
            n = {'C': 1, 'B': 1, 'Y': 2, 'I': 4, 'L': 8}[kind]
            fmt = {'C': '<b', 'B': '<b', 'Y': '<h', 'I': '<i', 'L': '<q'}[kind]
            out.append(struct.unpack(fmt, buf[at:at + n])[0])
            at += n
        elif kind in 'FD':
            n = 4 if kind == 'F' else 8
            out.append(struct.unpack('<f' if kind == 'F' else '<d', buf[at:at + n])[0])
            at += n
        elif kind in 'SR':
            n = struct.unpack('<I', buf[at:at + 4])[0]; at += 4
            out.append(buf[at:at + n]); at += n
        elif kind in 'fdlib':
            length, enc, clen = struct.unpack('<III', buf[at:at + 12]); at += 12
            raw = buf[at:at + clen]; at += clen
            if enc == 1:
                raw = zlib.decompress(raw)
            fmt = {'f': 'f', 'd': 'd', 'l': 'q', 'i': 'i', 'b': 'b'}[kind]
            out.append(struct.unpack('<%d%s' % (length, fmt), raw) if kind in 'fd' else None)
        else:
            raise ValueError('unknown property %r' % kind)
    return out, at


def _tree(path):
    """(vertex arrays, mesh Lcl Scaling) for one file.

    THE VERTICES ARE NOT THE MODEL. An FBX geometry is stored in its own space
    and the Model node that carries it holds an `Lcl Scaling` -- Quaternius
    ships these at 65 to 100 -- so the raw numbers are a shape, not a size. A
    sheep measures nine units and a dragon four; multiplied out they are 5.9m
    and 3.9m, which is the order a sheep and a dragon actually come in.
    """
    buf = open(path, 'rb').read()
    assert buf[:20] == b'Kaydara FBX Binary  ', path
    version = struct.unpack('<I', buf[23:27])[0]
    # 7500 and later widened the three node integers from 32 to 64 bits.
    wide = version >= 7500
    step = 8 if wide else 4
    fmt = '<QQQ' if wide else '<III'
    arrays, scales = [], []

    def walk(at, end, inside):
        while at < end:
            head = buf[at:at + step * 3]
            if len(head) < step * 3:
                return
            endoff, nprops, _plen = struct.unpack(fmt, head)
            at += step * 3
            namelen = buf[at]; at += 1
            name = buf[at:at + namelen]; at += namelen
            # THE NULL RECORD. A node list ends with a header of all zeroes
            # rather than with a count, so this is the terminator, not a node.
            if endoff == 0:
                return
            vals, after = _props(buf, at, nprops)
            if name == b'Vertices' and vals and vals[0]:
                arrays.append(vals[0])
            here = inside
            if name == b'Model':
                # A Model's third property is its kind. Only a `Mesh` carries
                # geometry; the rest of the 26-odd Models in one of these files
                # are the skeleton's limbs, and their scaling is not the
                # model's.
                here = (len(vals) > 2 and vals[2] == b'Mesh')
            if name == b'P' and inside and vals and vals[0] == b'Lcl Scaling':
                scales.append(vals[-3])
            if after < endoff:
                walk(after, endoff, here)
            at = endoff

    walk(27, len(buf), False)
    return arrays, scales


def vertices(path):
    """Every `Vertices` array in the file, concatenated."""
    return _tree(path)[0]


def extent(path):
    """(x, y, z) size in METRES, and the longest of the three."""
    arrays, scales = _tree(path)
    # One mesh per file in this pack; where there are several (a dragon has
    # eyes of its own) they share a scaling, so the first is the model's.
    mul = scales[0] if scales else 1.0
    lo = [1e30] * 3
    hi = [-1e30] * 3
    for arr in arrays:
        for i in range(0, len(arr) - 2, 3):
            for a in range(3):
                v = arr[i + a]
                if v < lo[a]: lo[a] = v
                if v > hi[a]: hi[a] = v
    if lo[0] > hi[0]:
        return None, None
    size = tuple((hi[a] - lo[a]) * mul / 100.0 for a in range(3))
    return size, max(size)


if __name__ == '__main__':
    for p in sys.argv[1:]:
        try:
            size, longest = extent(p)
            if size is None:
                print('%-28s no vertices found' % p.split('/')[-1])
            else:
                print('%-28s %6.2f x %6.2f x %6.2f m   longest %6.2f'
                      % (p.split('/')[-1], size[0], size[1], size[2], longest))
        except Exception as e:
            print('%-28s %s' % (p.split('/')[-1], e))
