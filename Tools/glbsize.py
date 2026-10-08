#!/usr/bin/env python3
"""How big a thing in a .glb actually is, measured from the file.

The companion to fbxsize.py, and it exists for the same reason: `get_bounds`
on a skeletal mesh reports the ANIMATED extent, so a beast whose walk clip
translates the root comes back hundreds of metres long and every scale derived
from it is wrong by that factor. `goblin_a` measured 462 metres and the whole
bestiary was drawn a centimetre and a half tall.

A glTF is kinder than an FBX about this: every POSITION accessor already
carries its own `min` and `max`, so the bind-pose extent is READ rather than
computed. What it does not carry is where the mesh sits in the scene, so the
node hierarchy's scaling still has to be walked and applied.

  glbsize.py wolf_a.glb [...]     -> name, extent in metres, longest axis
"""
import json, struct, sys


def chunks(path):
    """(the glTF JSON, the binary blob) out of a .glb -- or a plain .gltf.

    The two are one format in two containers. Quaternius's older packs ship
    `.glb`; his Ultimate Animated Animals ships self-contained `.gltf`, which
    is the same JSON with its buffers inlined as data URIs. Reading only the
    first meant a model could be in the project and unmeasurable.
    """
    if path.endswith('.gltf'):
        import base64
        js = json.load(open(path))
        bin_ = b''
        for b in js.get('buffers', []):
            uri = b.get('uri', '')
            if uri.startswith('data:'):
                bin_ += base64.b64decode(uri.split(',', 1)[1])
            elif uri:
                bin_ += open(os.path.join(os.path.dirname(path), uri), 'rb').read()
        return js, bin_
    raw = open(path, 'rb').read()
    magic, _version, _length = struct.unpack('<III', raw[:12])
    assert magic == 0x46546C67, '%s is not a .glb' % path
    at, js, bin_ = 12, None, b''
    while at < len(raw):
        clen, ctype = struct.unpack('<II', raw[at:at + 8])
        body = raw[at + 8:at + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(body.decode('utf-8'))
        elif ctype == 0x004E4942:
            bin_ = body
        at += 8 + clen + ((4 - clen % 4) % 4 if clen % 4 else 0)
    return js, bin_


def extent(path):
    """(x, y, z) size in METRES, and the longest axis.

    Walks the scene so each mesh is measured where it actually sits. A glTF is
    in metres by convention and these packs honour it, so no unit guessing is
    needed -- unlike the FBX bestiary, where every model carries its own
    hundredfold.
    """
    js, _ = chunks(path)
    nodes = js.get('nodes', [])
    meshes = js.get('meshes', [])
    acc = js.get('accessors', [])
    lo = [1e30] * 3
    hi = [-1e30] * 3

    def visit(idx, scale, offset):
        n = nodes[idx]
        s = n.get('scale', [1.0, 1.0, 1.0])
        t = n.get('translation', [0.0, 0.0, 0.0])
        # No rotation is applied. These are bind poses standing upright and a
        # rotation only ever turns the box, never grows it; the longest axis --
        # which is all any scale here is taken from -- is unchanged.
        sc = [scale[a] * s[a] for a in range(3)]
        off = [offset[a] + t[a] * scale[a] for a in range(3)]
        if 'mesh' in n:
            for prim in meshes[n['mesh']].get('primitives', []):
                p = prim.get('attributes', {}).get('POSITION')
                if p is None:
                    continue
                a = acc[p]
                if 'min' not in a or 'max' not in a:
                    continue
                for k in range(3):
                    for v in (a['min'][k], a['max'][k]):
                        w = off[k] + v * sc[k]
                        if w < lo[k]: lo[k] = w
                        if w > hi[k]: hi[k] = w
        for c in n.get('children', []):
            visit(c, sc, off)

    scenes = js.get('scenes', [])
    roots = scenes[js.get('scene', 0)].get('nodes', []) if scenes else range(len(nodes))
    for r in roots:
        visit(r, [1.0, 1.0, 1.0], [0.0, 0.0, 0.0])
    if lo[0] > hi[0]:
        return None, None
    size = tuple(hi[a] - lo[a] for a in range(3))
    return size, max(size)



def baked(path):
    """What the IMPORTER multiplies this file by, over and above `extent`.

    `extent` answers about the FILE and is the right number for choosing a
    scale from scratch. It is not the number the engine ends up with, and the
    gap between them is a hundred for most of Art/Wild: Quaternius hangs each
    creature under an armature node scaled by 100, `extent` applies that once
    walking the node chain, and Interchange applies it AGAIN when it bakes the
    bind pose. So an ogre the file calls 5.6 m arrives in the project at 560 m,
    and a scale worked out from the file alone draws a troll two hundred and
    eighty-five metres tall lying across the moor.

    That was reported from the stream as trees out of Super Mario, which is a
    fair description of a fen-adder ninety metres long.

    The one file in Art/Wild with no scaled armature is `deer.gltf`, and it is
    the one creature whose scale never needed correcting. That is the control
    that found this rule:

        what the engine measures = extent(file) * baked(file)

    Returns 1.0 for a file with no scaled node, which is most of them.
    """
    js, _ = chunks(path)
    big = 1.0
    for n in js.get('nodes', []):
        sc = n.get('scale')
        if sc and max(sc) > big:
            big = max(sc)
    return big

if __name__ == '__main__':
    for p in sys.argv[1:]:
        try:
            size, longest = extent(p)
            name = p.split('/')[-1]
            if size is None:
                print('%-20s no positions found' % name)
            else:
                print('%-20s %6.2f x %6.2f x %6.2f m   longest %6.2f'
                      % (name, size[0], size[1], size[2], longest))
        except Exception as e:
            print('%-20s %s' % (p.split('/')[-1], e))
