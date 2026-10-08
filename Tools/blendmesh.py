#!/usr/bin/env python3
"""Pull the meshes out of a .blend and write them as Wavefront OBJ.

WHY THIS EXISTS. The only CC0 bear on the whole reachable internet -- OpenGame
Art's "White Bear (Low poly)", public domain, by Phelippeau Rudy -- ships as a
`.blend` and nothing else. Quaternius has no bear in any of his packs, poly.pizza's
only CC0 bear is the bear TRAP that has been standing in for one, and every other
bear out there is CC-BY, which this project cannot ship. The choice was to install
Blender on somebody's machine to convert one file, or to read the file.

A .blend is not a closed format. It is a dump of Blender's own structs with the
CATALOGUE OF THOSE STRUCTS included in it -- the `DNA1` block -- precisely so
that a later Blender can read an earlier one. That catalogue is all a reader
needs: walk the blocks, read the DNA, find the Mesh, follow its pointers to the
vertex and loop arrays, and write them out. No guessing at offsets and nothing
version-specific, because the version describes itself.

  blendmesh.py in.blend out.obj
"""
import struct
import sys


def read(path):
    d = open(path, 'rb').read()
    if d[:7] != b'BLENDER':
        raise SystemExit('%s is not an uncompressed .blend' % path)
    psize = 8 if d[7:8] == b'-' else 4
    end = '<' if d[8:9] == b'v' else '>'
    return d, psize, end


def blocks(d, psize, end):
    """Every block in the file: (code, sdna index, count, payload)."""
    at = 12
    head = end + '4si' + ('Q' if psize == 8 else 'I') + 'ii'
    size = struct.calcsize(head)
    while at < len(d):
        code, ln, old, sdna, nr = struct.unpack_from(head, d, at)
        at += size
        yield code.rstrip(b'\0'), old, sdna, nr, d[at:at + ln]
        at += ln
        if code.startswith(b'ENDB'):
            return


def dna(payload, end):
    """The catalogue: field names, type names, type sizes and struct layouts."""
    at = 8                                    # 'SDNA' 'NAME'
    n = struct.unpack_from(end + 'i', payload, at)[0]; at += 4
    names = []
    for _ in range(n):
        z = payload.index(b'\0', at); names.append(payload[at:z].decode()); at = z + 1
    at = (at + 3) & ~3
    at += 4                                   # 'TYPE'
    n = struct.unpack_from(end + 'i', payload, at)[0]; at += 4
    types = []
    for _ in range(n):
        z = payload.index(b'\0', at); types.append(payload[at:z].decode()); at = z + 1
    at = (at + 3) & ~3
    at += 4                                   # 'TLEN'
    lens = list(struct.unpack_from(end + '%dh' % len(types), payload, at))
    at += 2 * len(types)
    at = (at + 3) & ~3
    at += 4                                   # 'STRC'
    n = struct.unpack_from(end + 'i', payload, at)[0]; at += 4
    structs = []
    for _ in range(n):
        t, f = struct.unpack_from(end + 'hh', payload, at); at += 4
        fields = []
        for _ in range(f):
            ft, fn = struct.unpack_from(end + 'hh', payload, at); at += 4
            fields.append((ft, fn))
        structs.append((t, fields))
    return names, types, lens, structs


def layout(names, types, lens, structs, want, psize):
    """{field name: (offset, type name, size)} for one struct, by name."""
    for t, fields in structs:
        if types[t] != want:
            continue
        out, at = {}, 0
        for ft, fn in fields:
            nm = names[fn]
            # A name carries its own shape: `*mvert` is a pointer, `co[3]` an
            # array. The DNA has no separate place for either.
            count = 1
            body = nm
            while '[' in body:
                a = body.index('['); b = body.index(']')
                count *= int(body[a + 1:b]); body = body[:a] + body[b + 1:]
            wide = psize if nm.startswith('*') else lens[ft]
            out[body.lstrip('*')] = (at, types[ft], wide, count, nm.startswith('*'))
            at += wide * count
        return out
    raise SystemExit('no %s in this .blend' % want)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    d, psize, end = read(src)
    dna_payload = None
    found = []
    for code, old, sdna, nr, payload in blocks(d, psize, end):
        if code == b'DNA1':
            dna_payload = payload
        found.append((code, old, sdna, nr, payload))
    names, types, lens, structs = dna(dna_payload, end)
    by_old = {old: (sdna, nr, payload) for code, old, sdna, nr, payload in found}

    MESH = layout(names, types, lens, structs, 'Mesh', psize)
    MVERT = layout(names, types, lens, structs, 'MVert', psize)
    MLOOP = layout(names, types, lens, structs, 'MLoop', psize)
    MPOLY = layout(names, types, lens, structs, 'MPoly', psize)
    P = 'Q' if psize == 8 else 'I'

    verts, faces, base = [], [], 0
    for code, old, sdna, nr, payload in found:
        if code != b'ME':
            continue
        get = lambda f: struct.unpack_from(end + {2: 'h', 4: 'i', 8: 'q'}[MESH[f][2]]
                                           if not MESH[f][4] else end + P,
                                           payload, MESH[f][0])[0]
        pv, pl, pp = get('mvert'), get('mloop'), get('mpoly')
        nv, nl, npoly = get('totvert'), get('totloop'), get('totpoly')
        if not (pv in by_old and pl in by_old and pp in by_old):
            continue
        vb = by_old[pv][2]; lb = by_old[pl][2]; pb = by_old[pp][2]
        off, _, wide, _, _ = MVERT['co']
        for i in range(nv):
            x, y, z = struct.unpack_from(end + '3f', vb, i * lens_of(MVERT) + off)
            # TWO CONVERSIONS, AND THE SECOND ONE IS THE ONE THAT BITES.
            #
            # Blender is Z-up and right-handed where OBJ and this project's
            # other art are Y-up, so the axes swap -- that much is obvious and
            # the bear arrives standing.
            #
            # The units are not obvious. A .blend is in METRES and an OBJ
            # carries no units at all, so Unreal reads its raw numbers as
            # CENTIMETRES: a 9.35 m bear imported as a 9.35 cm one, was then
            # scaled to a fifth of that, and stood two centimetres tall in the
            # grass. Nothing warned -- the mesh loaded, the pool filled, the
            # instances were placed, and the creature was simply too small to
            # see, which looks exactly like a creature that is not drawn.
            verts.append((x * 100.0, z * 100.0, -y * 100.0))
        lo, _, _, _, _ = MLOOP['v']
        loops = [struct.unpack_from(end + 'i', lb, i * lens_of(MLOOP) + lo)[0]
                 for i in range(nl)]
        so, _, _, _, _ = MPOLY['loopstart']
        to, _, _, _, _ = MPOLY['totloop']
        for i in range(npoly):
            s = struct.unpack_from(end + 'i', pb, i * lens_of(MPOLY) + so)[0]
            n = struct.unpack_from(end + 'i', pb, i * lens_of(MPOLY) + to)[0]
            faces.append([base + loops[s + k] + 1 for k in range(n)])
        base += nv

    with open(dst, 'w') as f:
        f.write('# from %s by Tools/blendmesh.py\n' % src)
        for v in verts:
            f.write('v %.6f %.6f %.6f\n' % v)
        for p in faces:
            f.write('f ' + ' '.join(str(i) for i in p) + '\n')
    print('%s -> %s: %d vertices, %d faces' % (src, dst, len(verts), len(faces)))


def lens_of(lay):
    """How wide one element of a struct is: the end of its last field."""
    return max(off + wide * count for off, _, wide, count, _ in lay.values())


if __name__ == '__main__':
    main()
