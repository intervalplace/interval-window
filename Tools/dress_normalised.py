#!/usr/bin/env python3
"""Paint a normalised mesh that kept its own colours.

`Tools/normalise.py --keep` is the mode for anything ALIVE: it throws the
texture away like the other mode, but keeps the artist's colour rather than
matching it to `forge.PALETTE`, and writes the colours beside the mesh as
`<word>.colours.json`. This reads that and builds one M_IntervalFlat instance
per slot, then binds it.

WHY NOT THE PALETTE, which this file is next to the proof of. `forge.PALETTE`
is a palette for this world's authored PROPS -- bone, iron, oak, thatch, ale,
fish -- and it holds exactly one real green. A goblin's hide is a perfectly
ordinary (0.137, 0.192, 0.030) and the nearest entry by hue is `Sulphur`,
because the one green is a long way off and a yellow is nearer. A yellow
goblin is not a coherent goblin.

What makes a creature belong here is the MASTER MATERIAL, not the palette: the
same flat shading, the same Rough and Grain, the same weather off the same
collection. That is exactly what dress_wild.py already does for the creatures
this project fetched, and this is the same job for one that came in through
normalise.py instead.

    python3 Tools/dress_normalised.py [word ...]

With no argument it dresses every `*.colours.json` in Art/Forged.
"""
import json
import os
import sys

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import rpc

ART = os.path.join(os.path.dirname(SP), 'Art', 'Forged')
DEST = '/Game/Interval/Forged'
FLAT = '/Game/Interval/Materials/M_IntervalFlat.M_IntervalFlat'
MI = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools'
SM = 'editor_toolset.toolsets.static_mesh.StaticMeshTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
AS = 'editor_toolset.toolsets.asset.AssetTools'

# The same four numbers dress_wild.py gives a creature, so one that arrives
# this way and one that was fetched are shaded identically. `Strength` is
# nothing: a wolf is the colour a wolf is, and the per-citizen dye has no
# business on an animal.
LOOK = (('Rough', 0.90), ('Course', 0.0), ('Grain', 0.07),
        ('Strength', 0.0), ('Shift', 0.5))


def dress(word):
    side = os.path.join(ART, word + '.colours.json')
    if not os.path.exists(side):
        return '%s: no %s' % (word, os.path.basename(side))
    colours = json.load(open(side))
    mesh = '%s/%s.%s' % (DEST, word, word)

    got = rpc.call(OBJ, 'get_properties', {'instance': {'refPath': mesh},
                                           'properties': ['StaticMaterials']})
    try:
        slots = json.loads(json.loads(got)['returnValue'])['StaticMaterials']
    except Exception:
        return '%s: no material list (is it imported?)' % word

    made, lost = 0, []
    for i, slot in enumerate(slots):
        name = slot.get('materialSlotName') or ('Slot%d' % i)
        rgb = colours.get(name)
        if rgb is None:
            lost.append(name)
            continue
        path = '%s/%s.%s' % (DEST, name, name)
        rpc.call(AS, 'delete', {'path': path.split('.')[0]})
        rpc.call(MI, 'create', {'folder_path': DEST, 'asset_name': name,
                                'parent': {'refPath': FLAT}})
        rpc.call(MI, 'set_vector_parameter',
                 {'instance': {'refPath': path}, 'name': 'DiffuseColor',
                  'value': {'r': rgb[0], 'g': rgb[1], 'b': rgb[2], 'a': 1.0}})
        for param, v in LOOK:
            rpc.call(MI, 'set_scalar_parameter',
                     {'instance': {'refPath': path}, 'name': param, 'value': v})
        rpc.call(AS, 'save_assets', {'asset_paths': [path.split('.')[0]]})
        # LOOKED AT, because dress_wild.py did not and a wrong asset name
        # failed silently for however long it took somebody to notice two
        # creatures were black in a printed book.
        said = rpc.call(SM, 'set_material', {'mesh': {'refPath': mesh},
                                             'slot_name': name,
                                             'material': {'refPath': path}})
        if 'not valid' in str(said) or 'error' in str(said).lower():
            lost.append('%s (%s)' % (name, str(said)[:60]))
            continue
        made += 1
    rpc.call(AS, 'save_assets', {'asset_paths': [mesh.split('.')[0]]})
    out = '%s: %d of %d slots' % (word, made, len(slots))
    if lost:
        out += '   NOT DRESSED: ' + ', '.join(lost)
    return out


def main():
    words = sys.argv[1:]
    if not words:
        words = sorted(f[:-len('.colours.json')] for f in os.listdir(ART)
                       if f.endswith('.colours.json'))
    if not words:
        print('nothing to dress: no *.colours.json in Art/Forged')
        return
    for w in words:
        print('   ' + dress(w))


if __name__ == '__main__':
    main()
