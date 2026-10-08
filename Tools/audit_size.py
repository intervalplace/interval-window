#!/usr/bin/env python3
"""How big is every drawn thing in this world, actually, in metres.

WHY. A prop's scale in `IntervalLook` means nothing on its own: it multiplies
whatever size the mesh happens to have been modelled at, and the kits in this
project disagree about that by a factor of five -- the Quaternius weapons are
about 5.5x life size, the armour is life size and in place, the engine's own
Cube is one metre. So a scale of 2.4 is a 2.4 metre boulder on one mesh and a
thirteen metre one on another, and the only way anybody has ever caught that is
by walking into it and taking a photograph.

This asks the editor for every mesh's real extent and multiplies. It reads the
Props table back OUT of the look asset rather than re-deriving it from
parts.py, so what it measures is what the engine will draw, including every
override and every late patch apply.py makes.

    python3 Tools/audit_size.py            # everything the world seats
    python3 Tools/audit_size.py 600        # only things over six metres
    python3 Tools/audit_size.py all        # including art nothing seats

`world_kinds.json` says which node types this founding actually places, and is
written by `world-kinds.mjs` on the bridge side. Re-run that when the generator
changes what it seats; without it this measures a lot of art nobody can reach.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpc
from expected_size import EXPECT

# Pass `all` to measure every row, including art for node types no generator
# seats any more.
only_seated = 'all' not in sys.argv

LOOK = '/Game/Interval/IntervalLook.IntervalLook'
SM = 'editor_toolset.toolsets.static_mesh.StaticMeshTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'mesh_bounds.json')

# WHAT COUNTS AS TOO BIG, in centimetres, by what the thing is. A world drawn
# at human scale has very few things taller than a house in it, and anything
# here that is has been found by somebody noticing it on the horizon.
TALL_ENOUGH = 900.0


def props():
    out = rpc.call(OBJ, 'get_properties',
                   {'instance': {'refPath': LOOK}, 'properties': ['Props']})
    return json.loads(json.loads(out)['returnValue'])['Props']


def bounds(path, cache):
    if path in cache:
        return cache[path]
    txt = rpc.call(SM, 'get_bounds', {'mesh': {'refPath': path}})
    nums = re.findall(r'-?\d+\.\d+(?:[eE][-+]?\d+)?|-?\d+(?=[,}])', txt)
    cache[path] = [float(v) for v in nums[:6]] if len(nums) >= 6 else None
    return cache[path]


def _rot(v, r):
    """A point through a rotator, the way the engine turns one."""
    import math
    sp, cp = math.sin(math.radians(r[0])), math.cos(math.radians(r[0]))
    sy, cy = math.sin(math.radians(r[1])), math.cos(math.radians(r[1]))
    sr, cr = math.sin(math.radians(r[2])), math.cos(math.radians(r[2]))
    ax = (cp * cy, cp * sy, sp)
    ay = (sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp)
    az = (-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp)
    return [v[0] * ax[i] + v[1] * ay[i] + v[2] * az[i] for i in range(3)]


def _corners(b, scale, rot, off):
    """The eight corners of one piece, where they actually end up."""
    lo = [b[i] * scale[i] for i in range(3)]
    hi = [b[i + 3] * scale[i] for i in range(3)]
    out = []
    for cx in (lo[0], hi[0]):
        for cy in (lo[1], hi[1]):
            for cz in (lo[2], hi[2]):
                t = _rot([cx, cy, cz], rot)
                out.append([t[i] + off[i] for i in range(3)])
    return out


def _xyz(d, default=0.0):
    if not isinstance(d, dict):
        return [default] * 3
    return [d.get(k, default) for k in ('x', 'y', 'z')]


def span(path, scale, cache, parts=None):
    """How big the WHOLE THING is, base and every piece hung on it.

    Measuring the base mesh alone is how a sawpit read as 42 centimetres: the
    bench is 42cm and the three timbers that make it a saw frame are PARTS. A
    prop in this world is an assembly far more often than it is one mesh, so
    measuring one mesh answers a question nobody asked.
    """
    b = bounds(path, cache)
    if not b:
        return None
    sc = [scale.get(k, 1.0) for k in ('x', 'y', 'z')]
    pts = _corners(b, sc, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0])
    for q in (parts or []):
        m = q.get('mesh')
        mp = (m.get('refPath') or '').strip() if isinstance(m, dict) else ''
        if not mp or mp == 'None' or q.get('bone') not in (None, 'None'):
            continue              # a part on a BONE moves with a figure
        pb = bounds(mp, cache)
        if not pb:
            continue
        r = q.get('rotation') or {}
        pts += _corners(pb,
                        _xyz(q.get('scale'), 1.0),
                        [r.get('pitch', 0.0), r.get('yaw', 0.0), r.get('roll', 0.0)],
                        _xyz(q.get('offset')))
    return [max(c[i] for c in pts) - min(c[i] for c in pts) for i in range(3)]


if __name__ == '__main__':
    # `all` is a word, not a height; take the first argument that is a number.
    sizes = [a for a in sys.argv[1:] if a.replace('.', '', 1).isdigit()]
    floor = float(sizes[0]) if sizes else 0.0
    # WHAT THE WORLD ACTUALLY SEATS. Written by `kinds.mjs` on the bridge side.
    # Without it this measures a lot of art nobody can walk up to: `waystone`
    # is 4.5 metres across and wrong, and is also v1-v5 only -- SPEC §29t says
    # there are none in v7 -- so it is not a fault, it is a leftover. A count
    # beside each row says how many of the thing stand in the world, and a dash
    # says none do.
    seated = {}
    kp = os.path.join(HERE, 'world_kinds.json')
    if os.path.exists(kp):
        seated = json.load(open(kp))
    cache = {}
    if os.path.exists(CACHE):
        cache = json.load(open(CACHE))
    rows, blind = [], []
    for name, p in props().items():
        m = p.get('mesh')
        # a prop with no mesh of its own writes the string "None", not a struct
        path = (m.get('refPath') or '').strip() if isinstance(m, dict) else ''
        if not path or path == 'None':
            continue
        sc = p.get('scale') or {}
        got = span(path, sc, cache, p.get('parts'))
        if got is None:
            blind.append(name)
            continue
        rows.append((max(got), name, got, path.rsplit('/', 1)[-1]))
    json.dump(cache, open(CACHE, 'w'), indent=0, sort_keys=True)
    rows.sort(reverse=True)
    shown = 0
    off, undeclared = [], []
    for big, name, got, mesh in rows:
        n = seated.get(name)
        if seated and only_seated and not n:
            continue
        # ---- AGAINST WHAT THE PROJECT SAYS THE THING IS ----
        #
        # CHECKED FOR EVERY ROW, PRINTED FOR SOME. `floor` only decides how
        # much of the table is worth reading; a thing the wrong size is worth
        # knowing about whether or not it is tall enough to make the listing.
        # Asking the question inside the printing loop meant `audit_size.py
        # 600` silently checked nothing under six metres, which is most of the
        # world and all of the faults that made it small.
        #
        # `TALL_ENOUGH` could only ever catch a prop bigger than a house, which
        # is one fault out of many: a sawpit at forty-two centimetres and a
        # ladder shorter than the person climbing it are both well under it.
        # `expected_size.py` states a range per word, so the test stops being
        # "does this look odd" and becomes "is it what we said it was".
        want = EXPECT.get(name)
        flag = ''
        if want and (big / 100.0 < want[0] or big / 100.0 > want[1]):
            flag = '  <-- SAID %.1f to %.1f m' % want
            off.append((name, big / 100.0, want, n or 0))
        elif not want:
            undeclared.append(name)
        elif big >= TALL_ENOUGH and n:
            flag = '  <-- taller than a house, and said to be'
        if big < floor:
            continue
        print('%7.2f m  %-30s %6s  %5.1f x %5.1f x %5.1f  %s%s'
              % (big / 100.0, name, ('x%d' % n) if n else '-',
                 got[0] / 100, got[1] / 100, got[2] / 100, mesh, flag))
        shown += 1
    print('\n%d drawn thing(s) measured, %d shown' % (len(rows), shown))
    if off:
        print('\n---- %d NOT THE SIZE THE PROJECT SAYS THEY ARE ----' % len(off))
        off.sort(key=lambda r: -r[3])
        for name, big, want, n in off:
            how = 'too big' if big > want[1] else 'too small'
            print('  x%-6s %-26s %6.2f m, %s (said %.1f to %.1f)'
                  % (n or '-', name, big, how, want[0], want[1]))
    else:
        print('\nevery declared thing is the size it was declared.')
    if undeclared:
        print('\n%d word(s) nobody has declared a size for yet: %s'
              % (len(undeclared), ', '.join(sorted(undeclared)[:10])
                 + (' ...' if len(undeclared) > 10 else '')))
    if blind:
        print('no bounds (skeletal or missing): ' + ', '.join(sorted(blind)[:12])
              + (' ...' if len(blind) > 12 else ''))


# ---------------------------------------------------------------------------
# AND THE MOBS, which are skeletal and so measure through a different door.
#
# Twenty-nine beasts, each a mesh from a different CC0 pack, each authored at
# whatever size its author liked -- the note in parts.py records a crab that
# arrived two hundred and fifty metres across. Every one of those scales is a
# ratio somebody worked out by hand, and a ratio worked out by hand is exactly
# the kind of number this file exists to check.
SK = 'editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools'


def mobs():
    out = rpc.call(OBJ, 'get_properties',
                   {'instance': {'refPath': LOOK}, 'properties': ['Mobs']})
    return json.loads(json.loads(out)['returnValue'])['Mobs']


def mob_bounds(path, cache):
    """A skeletal mesh answers with a DIFFERENT STRUCT, and it matters.

    A static mesh gives {min, max} in its own space. A skeletal mesh gives
    {origin, boxExtent, sphereRadius}, and boxExtent is the HALF extent -- so
    reading it as a corner, which the first pass here did, reports every beast
    at half its size and can report a negative one. A dragon came out 4.2m and
    is 8.5. Nothing is measured here that is not read from its own struct.
    """
    if path in cache:
        return cache[path]
    txt = rpc.call(SK, 'get_bounds', {'mesh': {'refPath': path}})
    try:
        b = json.loads(txt)['returnValue']
        e, o = b['boxExtent'], b['origin']
        cache[path] = {'size': [e['x'] * 2, e['y'] * 2, e['z'] * 2],
                       'top': o['z'] + e['z']}
    except (ValueError, KeyError, TypeError):
        cache[path] = None
    return cache[path]


def audit_mobs():
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    rows, blind = [], []
    for name, m in mobs().items():
        sk = m.get('skeletal')
        path = (sk.get('refPath') or '').strip() if isinstance(sk, dict) else ''
        if not path or path == 'None':
            continue
        b = mob_bounds(path, cache)
        if not b:
            blind.append(name)
            continue
        sc = m.get('scale')
        k = sc.get('x', 1.0) if isinstance(sc, dict) else (sc or 1.0)
        got = [v * k for v in b['size']]
        rows.append((max(got), name, got, k, path.rsplit('/', 1)[-1],
                     b['top'] * k))
    json.dump(cache, open(CACHE, 'w'), indent=0, sort_keys=True)
    rows.sort(reverse=True)
    print('\n---- THE BESTIARY, AS DRAWN ----')
    for big, name, got, k, mesh, top in rows:
        flag = '  <-- BIGGER THAN A HOUSE' if big >= 600 else ''
        print('%7.2f m  %-20s %5.1f x %5.1f x %5.1f  stands %5.2f m  %s%s'
              % (big / 100.0, name, got[0] / 100, got[1] / 100, got[2] / 100,
                 top / 100, mesh, flag))
    if blind:
        print('no bounds: ' + ', '.join(sorted(blind)))
