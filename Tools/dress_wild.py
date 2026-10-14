#!/usr/bin/env python3
"""Give the wild bestiary materials this project renders.

THE ARTIST'S COLOURS, KEPT. The glTF importer builds a full Material per slot
with the colour as a `Constant3Vector` in LINEAR -- a wolf's coat is
(0.147, 0.152, 0.135) and its nose is (0.022, 0.022, 0.022) -- and those are
the numbers Quaternius chose. Nothing here invents a colour: each is read out
of the material the import made and put on an instance of M_IntervalFlat,
which is the one master for anything that is a flat colour.

What they gain by moving is the weather and the grain: a wolf standing in the
rain now darkens with the ground it is standing on, which the imported
material could not do.
"""
import json, os, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import rpc

WILD = '/Game/Interval/Wild/'
FLAT = '/Game/Interval/Materials/M_IntervalFlat.M_IntervalFlat'
MI = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools'
SK = 'editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
AS = 'editor_toolset.toolsets.asset.AssetTools'

rpc.call('EditorToolset.EditorAppToolset', 'StopPIE', {})

ROOT = os.path.join(os.path.dirname(SP), 'Content', 'Interval', 'Wild')


def colour_of(material):
    """The artist's colour, or None if this material was built some other way."""
    for which in ('MaterialExpressionConstant3Vector_0',
                  'MaterialExpressionConstant3Vector_1'):
        got = rpc.call(OBJ, 'get_properties',
                       {'instance': {'refPath': material + ':' + which},
                        'properties': ['Constant']})
        try:
            return json.loads(json.loads(got)['returnValue'])['Constant']
        except Exception:
            continue
    return None


# What colour a creature is when its own file will not say. Only the ones that
# need it: everything imported from glTF brings its own.
FALLBACK = {
    'bear': {'r': 0.115, 'g': 0.068, 'b': 0.042},   # dark brown fur
    # The Giant that stands in for a troll brought no colour either, so it
    # came out the pale grey of an untextured block and read as unfinished
    # geometry rather than as a creature. Mossy stone: a thing that has been
    # standing in the crags a long time.
    'ogre': {'r': 0.150, 'g': 0.165, 'b': 0.128},
}

# ---- AND A COLOUR TOO DARK TO BE A COLOUR ----
#
# FALLBACK above is for a slot whose file says nothing. This is for one whose
# file says almost nothing: the scree imp's `Ghost_Main` arrives at
# (0.018, 0.004, 0.023), which is fifteen times darker than the very same
# mesh's secondary slot and is black on any page. The imp printed in the
# handbook as a floating tan patch with two black smears either side of it,
# while its DEPTH pass showed a winged creature with a body and a head: the
# camera, the framing and the geometry were all correct and the body was
# painted out.
#
# Keyed by creature AND slot, because the imp's other slot is a perfectly
# ordinary (0.301, 0.21, 0.134) and must not be touched. A dusky violet-grey:
# dark and cold, which is what a thing called a ghost should be, and visible,
# which it was not.
TOO_DARK = {
    ('monster_a', 'Ghost_Main'): {'r': 0.105, 'g': 0.085, 'b': 0.135},
}

made = 0
lifted = []
for beast in sorted(os.listdir(ROOT)):
    mesh = '%s%s/%s.%s' % (WILD, beast, beast, beast)
    if not os.path.isfile(os.path.join(ROOT, beast, beast + '.uasset')):
        continue
    # SKELETAL OR STATIC, THE SAME JOB. Most of these carry a rig; the bears
    # and the fourth goblin do not, and a static mesh keeps its slots under a
    # different property and takes them back through a different tool. The
    # colours and the instances are identical either way.
    got = rpc.call(OBJ, 'get_properties', {'instance': {'refPath': mesh},
                                           'properties': ['Materials']})
    kind, slots = SK, None
    try:
        slots = json.loads(json.loads(got)['returnValue'])['Materials']
    except Exception:
        got = rpc.call(OBJ, 'get_properties', {'instance': {'refPath': mesh},
                                               'properties': ['StaticMaterials']})
        try:
            slots = json.loads(json.loads(got)['returnValue'])['StaticMaterials']
            kind = 'editor_toolset.toolsets.static_mesh.StaticMeshTools'
        except Exception:
            print(beast, 'no material list:', got[:90])
            continue

    for i, slot in enumerate(slots):
        name = slot.get('materialSlotName') or ('Slot%d' % i)
        # THE IMPORT'S OWN MATERIAL, BY NAME -- not whatever the mesh points
        # at now.
        #
        # This used to read the colour off the material currently in the slot,
        # which works exactly once. On a second run the slot already holds the
        # instance this script made last time, that instance has no
        # `Constant3Vector`, the read fails, and every colour falls back to the
        # grey default -- so a crab that was red became a grey crab the moment
        # anybody re-ran the script. Interchange names its material after the
        # slot, so the original is always findable by name and a re-run is a
        # no-op.
        was = '%s%s/%s.%s' % (WILD, beast, name, name)
        rgb = colour_of(was)
        if not rgb:
            # A slot whose colour cannot be read keeps a plain stone grey
            # rather than the engine's checker: a grey wolf is wrong, a
            # checkered one is broken, and one of those is easier to spot.
            #
            # BUT SOME CREATURES HAVE AN OBVIOUS COLOUR, and where the source
            # carries none we may as well say it. The white bear arrived as a
            # Wavefront .obj -- converted out of a .blend, which is the only
            # form the one CC0 bear in the world ships in -- and an .obj has
            # no materials at all, so it stood in the Greenwood the colour of
            # a rock. A table of the few that need it beats leaving them grey
            # and beats inventing a colour for every creature that already
            # brought one.
            rgb = FALLBACK.get(beast, {'r': 0.18, 'g': 0.18, 'b': 0.18})
        elif (beast, name) in TOO_DARK:
            # Read, and read as very nearly nothing. See TOO_DARK above.
            rgb = TOO_DARK[(beast, name)]
            lifted.append('%s/%s' % (beast, name))
        made_name = 'MW_%s_%s' % (beast, name)
        path = '%s%s/%s.%s' % (WILD, beast, made_name, made_name)
        rpc.call(AS, 'delete', {'path': path.split('.')[0]})
        rpc.call(MI, 'create', {'folder_path': WILD + beast,
                                'asset_name': made_name,
                                'parent': {'refPath': FLAT}})
        rpc.call(MI, 'set_vector_parameter', {'instance': {'refPath': path},
                 'name': 'DiffuseColor',
                 'value': {'r': rgb['r'], 'g': rgb['g'], 'b': rgb['b'], 'a': 1.0}})
        for param, v in (('Rough', 0.90), ('Course', 0.0), ('Grain', 0.07),
                         ('Strength', 0.0), ('Shift', 0.5)):
            rpc.call(MI, 'set_scalar_parameter',
                     {'instance': {'refPath': path}, 'name': param, 'value': v})
        rpc.call(AS, 'save_assets', {'asset_paths': [path.split('.')[0]]})
        rpc.call(kind, 'set_material', {'mesh': {'refPath': mesh},
                                       'slot_name': name,
                                       'material': {'refPath': path}})
        made += 1
    rpc.call(AS, 'save_assets', {'asset_paths': [mesh.split('.')[0]]})
    print('%-12s %d slots' % (beast, len(slots)))
print('dressed:', made, 'slots')


# ---------------------------------------------------------------------------
# AND THE THREE THAT CARRY A TEXTURE INSTEAD OF A COLOUR.
#
# A raven, a mermaid and a fourth goblin came out of the same shop with an
# ATLAS -- one sheet each, no ORM -- and no rig, so they are static meshes with
# a textured material rather than flat-coloured skeletons. They go on
# M_IntervalPerson, which is where textured art lives, with the occlusion floor
# up because a colour map in the ORM slot is not occlusion.
PERSON = '/Game/Interval/Materials/M_IntervalPerson.M_IntervalPerson'
SM = 'editor_toolset.toolsets.static_mesh.StaticMeshTools'

# ---- THE TEXTURE, NOT THE MATERIAL NAMED AFTER IT ----
#
# This said 'Atlas' and 'Atlas_Diffuse', which are the MATERIALS the glTF
# import built. The texture they sample is `base_color_texture`, which is what
# interchange calls it and what every one of these three carries.
#
# So `set_texture_parameter` was handed a material where it wanted a texture,
# answered "is not valid Texture for property 'value'", and that answer went
# nowhere: this script does not look at what rpc.call returns. The instances
# came out with NO texture parameters at all -- nine scalars and nothing else
# -- and M_IntervalPerson with no base colour is black.
#
# That is why the carrion crow and the siren printed as dark lumps in the
# handbook while their depth passes showed a crow with a beak and a tail and a
# figure among rocks. The camera was right, the framing was right, the mesh was
# right, and the colour was never connected.
SHEETED = {
    'raven':    'base_color_texture',
    'mermaid':  'base_color_texture',
    'goblin_d': 'base_color_texture',
}
for beast, sheet in SHEETED.items():
    mesh = '%s%s/%s.%s' % (WILD, beast, beast, beast)
    name = 'MW_%s' % beast
    path = '%s%s/%s.%s' % (WILD, beast, name, name)
    tex = '%s%s/%s.%s' % (WILD, beast, sheet, sheet)
    rpc.call(AS, 'delete', {'path': path.split('.')[0]})
    rpc.call(MI, 'create', {'folder_path': WILD + beast, 'asset_name': name,
                            'parent': {'refPath': PERSON}})
    for slot in ('BaseColorTexture', 'ORMTexture'):
        # LOOKED AT, because the last time this was not, a wrong asset name
        # failed silently for however long it took somebody to notice two
        # creatures were black in a printed book.
        said = rpc.call(MI, 'set_texture_parameter', {'instance': {'refPath': path},
                        'name': slot, 'value': {'refPath': tex}})
        if 'not valid' in str(said) or 'error' in str(said).lower():
            print('  %s %s: %s' % (beast, slot, str(said)[:90]))
    for param, v in (('Strength', 0.0), ('Puff', 0.0), ('Cut', -100000.0),
                     ('HairTint', 0.0), ('MetalMax', 0.0), ('RoughFloor', 0.86),
                     ('Sway', 0.0), ('Lift', 1.0), ('AOFloor', 1.0)):
        rpc.call(MI, 'set_scalar_parameter',
                 {'instance': {'refPath': path}, 'name': param, 'value': v})
    rpc.call(AS, 'save_assets', {'asset_paths': [path.split('.')[0]]})
    got = rpc.call(SM, 'get_material_slots', {'mesh': {'refPath': mesh}})
    try:
        slots = json.loads(got)['returnValue']
    except Exception:
        print(beast, 'slots?', got[:80]); continue
    for sl in slots:
        rpc.call(SM, 'set_material', {'mesh': {'refPath': mesh}, 'slot_name': sl,
                                      'material': {'refPath': path}})
    rpc.call(AS, 'save_assets', {'asset_paths': [mesh.split('.')[0]]})
    print('%-10s -> %s (%d slots)' % (beast, name, len(slots)))

if lifted:
    print('lifted out of a near-black: %s' % ', '.join(lifted))
