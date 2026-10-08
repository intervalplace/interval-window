#!/usr/bin/env python3
"""EVERY MESH THE WINDOW DRAWS: is it dressed, and is it the right size?

Two faults were found by hand tonight and each had been in the world for weeks
because nothing looked for them:

  UNDRESSED. A mesh keeps the material its FBX import invented. That material
  is parented to nothing this project owns, and when a master is deleted and
  re-created it is left pointing at a trashed object -- which renders NOTHING,
  silently. Four of six outfits, and the wizard's staff, were like this.

  MIS-SIZED. A kit is modelled at some scale of its author's choosing and the
  window draws it at one. The Quaternius weapon kit is about five and a half
  times life size, so a citizen's sword was five and a half metres and their
  shield was a barn door standing between them and the camera.

Both are mechanical to look for, so this looks. It reports rather than fixes:
what the right size for a thing IS is a judgement, and the point here is to
put every suspect in front of somebody at once instead of one a fortnight.

  audit_art.py
"""
import json, os, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import rpc

OBJ = 'editor_toolset.toolsets.object.ObjectTools'
SM = 'editor_toolset.toolsets.static_mesh.StaticMeshTools'

# The masters this project renders with. A material whose chain reaches none of
# these is not ours, whatever it is called.
OURS = ('M_IntervalFlat', 'M_IntervalPerson', 'M_IntervalFoliage',
        'M_IntervalWall', 'M_IntervalThatch', 'M_IntervalTimberFrame',
        'M_IntervalGround', 'M_IntervalGlow', 'M_IntervalWater',
        'M_IntervalFlame', 'M_IntervalSmoke', 'M_IntervalStars',
        'M_IntervalRain', 'M_IntervalFolk', 'M_IntervalDead')

def paths(value, found):
    if isinstance(value, str):
        if value.startswith('/Game/'):
            found.append(value)
    elif isinstance(value, dict):
        for v in value.values():
            paths(v, found)
    elif isinstance(value, (list, tuple)):
        for v in value:
            paths(v, found)

def main():
    import parts
    seen = {}
    # Everything a citizen wears or carries, AND everything that stands about.
    #
    # The first sweep looked only at what is worn, because that is where both
    # faults had been found. It missed three whole kits: nothing dresses the
    # Ruins, Village or Farm meshes, and a mesh nothing dresses keeps the
    # material its import invented. So the sweep is over every mesh the window
    # names, wherever it names it from.
    # EVERY DICTIONARY IN parts.py, not a list of the ones somebody remembered.
    # That list is exactly how three kits came to have no dresser: a table is
    # added, and the thing that walks the tables is not told.
    tables = [('worn', parts.WORN)]
    for name in dir(parts):
        if name.startswith('_') or name == 'WORN':
            continue
        val = getattr(parts, name)
        if isinstance(val, dict) and val:
            tables.append((name.lower(), val))
    for where, table in tables:
        for word, row in table.items():
            found = []
            paths(row, found)
            for p in found:
                if '/Materials/' in p or '/Hues/' in p:
                    continue
                seen.setdefault(p, []).append('%s:%s' % (where, word))

    # AND THE TREES, WHICH NAME THEIR MESH WITHOUT A PATH.
    #
    # `TREES` and `VARIETY` hold bare kit names -- `CommonTree_3` -- because a
    # tree is always from the nature kit and the folder never varies. Walking
    # for `/Game/` paths therefore found not one tree, and the tallest things
    # in the world were reported without a single tree among them. Which is a
    # quiet way for the audit to miss the exact question it was built to
    # answer: somebody looked at a picture and asked why the trees were so big.
    for name in ('TREES', 'VARIETY'):
        table = getattr(parts, name, None)
        if not isinstance(table, dict):
            continue
        for word, row in table.items():
            picks = row if isinstance(row, (list, tuple)) else [row]
            for pick in picks:
                mesh = pick[0] if isinstance(pick, (list, tuple)) else pick
                if not isinstance(mesh, str) or '/' in mesh:
                    continue
                seen.setdefault('/Game/Interval/Nature/%s.%s' % (mesh, mesh),
                                []).append('%s:%s' % (name.lower(), word))
    print('%d distinct meshes the window names' % len(seen))
    print()
    bad_size, bad_dress, tall = [], [], []
    for path in sorted(seen):
        name = path.split('/')[-1].split('.')[0]
        words = seen[path]
        # its own size
        try:
            b = json.loads(json.loads(rpc.call(SM, 'get_bounds',
                {'mesh': {'refPath': path}}))['returnValue']) \
                if False else json.loads(rpc.call(SM, 'get_bounds',
                {'mesh': {'refPath': path}}))['returnValue']
            span = max(b['max'][k] - b['min'][k] for k in ('x', 'y', 'z'))
        except Exception:
            continue
        scale = parts.MESH_SCALE.get(name)
        if scale is None:
            # the scale the kit row actually uses, read back off the row
            scale = 1.0
            for w in words:
                if w.startswith('trees:'):
                    row = parts.TREES.get(w[6:])
                    if isinstance(row, (list, tuple)) and len(row) > 1:
                        scale = row[1]
                    continue
                if not w.startswith('worn:'):
                    continue
                kit = parts.WORN.get(w[5:], {})
                for piece in kit.get('pieces', []):
                    if piece.get('mesh', {}).get('refPath') == path:
                        scale = piece['scale']['x']
                        break
        drawn = span * scale
        # A thing a person wears or carries is between a whetstone and a spear.
        tall.append((name, drawn, scale, words))
        worn_only = all(w.startswith('worn:') for w in words)
        if worn_only and (drawn < 8.0 or drawn > 260.0):
            bad_size.append((name, drawn, scale, words[:3]))
        # and whether it is dressed
        try:
            mats = json.loads(rpc.call(OBJ, 'get_properties',
                {'instance': {'refPath': path},
                 'properties': ['StaticMaterials']})['returnValue']
                if False else json.loads(rpc.call(OBJ, 'get_properties',
                {'instance': {'refPath': path},
                 'properties': ['StaticMaterials']}))['returnValue'])
        except Exception:
            continue
        for slot in mats.get('StaticMaterials', []):
            mi = (slot.get('materialInterface') or {}).get('refPath', '')
            if not mi:
                bad_dress.append((name, slot.get('materialSlotName'), 'NONE', ''))
                continue
            # FOLLOW THE CHAIN. `MP_Steel` and `WoodDark` are ours; what says
            # so is not their name but the master at the end of their parents.
            # Checking the name alone reported every correctly dressed mesh in
            # the project, which is a report nobody reads twice.
            chain, at = [], mi
            for _ in range(5):
                if any(o in at for o in OURS):
                    break
                try:
                    got = json.loads(rpc.call(OBJ, 'get_properties',
                        {'instance': {'refPath': at}, 'properties': ['Parent']}))
                    par = json.loads(got['returnValue']).get('Parent')
                except Exception:
                    par = None
                if not par or not par.get('refPath'):
                    break
                at = par['refPath']
                chain.append(at.split('/')[-1].split('.')[0])
            if not any(o in at for o in OURS):
                bad_dress.append((name, slot.get('materialSlotName'),
                                  mi.split('/')[-1].split('.')[0],
                                  ' -> '.join(chain) or '(no parent)'))
    print('SUSPECT SIZES (drawn size in cm, at the scale the window uses):')
    for n, d, s, w in sorted(bad_size, key=lambda r: -r[1]):
        print('  %-22s %8.1f cm   scale %.3f   %s' % (n, d, s, ' '.join(w)))
    print()
    # AND THE BIGGEST THINGS IN THE WORLD, WHATEVER THEY ARE.
    #
    # A worn thing can be judged against a range -- nothing a citizen carries
    # is under a whetstone or over a spear -- and a prop cannot: a bell tower
    # and a barrel are both correct. So the props are not judged, they are
    # LISTED, biggest first, next to a citizen's 181 cm. Anything absurd is
    # obvious in one line, which is all this needs to be: the eye is a poor
    # judge of a tree seen at an unknown distance, and this is not.
    print('THE TALLEST THINGS THE WINDOW DRAWS (a citizen is 181 cm):')
    for n, d, s, w in sorted(tall, key=lambda r: -r[1])[:18]:
        print('  %-22s %8.1f cm   scale %.3f   %s' % (n, d, s, ' '.join(w[:2])))
    print()
    print('SUSPECT MATERIALS (a slot whose material is not one of ours):')
    if not bad_dress:
        print('  (none: every slot reaches one of this project\'s masters)')
    for n, slot, mi, chain in bad_dress:
        print('  %-22s %-24s %-22s %s' % (n, slot, mi, chain))

main()
