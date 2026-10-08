#!/usr/bin/env python3
"""Every held mesh's own bounding box, read from the editor and kept as data.

WHY THIS FILE EXISTS. A thing held in a hand is placed by a relative transform
on a bone, and a relative transform turns a mesh about the mesh's OWN PIVOT.
Every weapon in the Quaternius kit is modelled about its geometric middle, so
turning a three-metre axe to the angle a hand holds it at swings its pivot a
third of a metre away from the fist -- and no offset typed by hand can fix that
for more than one mesh at a time, because every mesh is a different length.

So the offset stops being typed. It is DERIVED, per mesh, from where the grip
actually falls on that mesh, which is a fraction along the mesh's own longest
axis. That needs the mesh's extent, and this reads it from the editor rather
than from somebody's memory of opening the asset once.

Run it when the kit changes. It writes `kit_bounds.json` beside itself.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpc
import parts

SM = 'editor_toolset.toolsets.static_mesh.StaticMeshTools'
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'kit_bounds.json')


def bounds(path):
    txt = rpc.call(SM, 'get_bounds', {'mesh': {'refPath': path}})
    nums = [float(v) for v in re.findall(r'[-\d.]+(?:[eE][-+]?\d+)?', txt)]
    if len(nums) < 6:
        return None
    return {'min': nums[0:3], 'max': nums[3:6]}


def every_held_mesh():
    """Every mesh this project puts in a hand, by its asset path."""
    seen = {}
    for name in parts.KIT_NAMES:
        seen[name] = parts.KIT_PATH(name)
    for name in parts.PROP_KIT:
        seen[name] = parts.KIT_PATH(name)
    seen['Wizard_Staff1'] = parts.STAFF_MESH
    return seen


if __name__ == '__main__':
    out, missed = {}, []
    for name, path in sorted(every_held_mesh().items()):
        b = bounds(path)
        if b is None:
            missed.append(name)
            continue
        out[name] = b
        lo, hi = b['min'], b['max']
        span = [hi[i] - lo[i] for i in range(3)]
        axis = max(range(3), key=lambda i: span[i])
        print('%-24s %5.0f x %5.0f x %5.0f   long axis %s' %
              (name, span[0], span[1], span[2], 'XYZ'[axis]))
    json.dump(out, open(OUT, 'w'), indent=1, sort_keys=True)
    print('\n%d mesh(es) measured -> %s' % (len(out), OUT))
    if missed:
        print('NO BOUNDS: ' + ', '.join(missed))
