#!/usr/bin/env python3
"""Give the imported nature kit materials this project can actually render.

The glTF importer parents everything to Unreal's Substrate master, which is
disabled here, so every tree arrives grey. One instance per atlas the kit
ships, then hung on every slot that used the grey original.
"""
import json, os, subprocess, sys
import rpc as _rpc
SP = os.path.dirname(os.path.abspath(__file__))
WOOD = '/Game/Interval/Nature/'
# TWO MASTERS, AND WHICH ONE A THING TAKES IS ABOUT LIGHT PASSING THROUGH IT.
# A leaf, a blade of grass and a petal are thin translucent sheets and most of
# what you see of them backlit is light that went through; bark, stone and a
# mushroom cap are not, and putting them on the foliage master makes a boulder
# glow from inside. See make_person_mat.py.
OPAQUE = '/Game/Interval/Materials/M_IntervalPerson.M_IntervalPerson'
SOFT   = '/Game/Interval/Materials/M_IntervalFoliage.M_IntervalFoliage'
MI = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools'
SM = 'editor_toolset.toolsets.static_mesh.StaticMeshTools'
AS = 'editor_toolset.toolsets.asset.AssetTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'

def call(toolset, tool, args):
    # One session for the whole script; see Tools/rpc.py.
    return _rpc.call(toolset, tool, args)


call('EditorToolset.EditorAppToolset', 'StopPIE', {})

# A LEAF IS NOT MADE OF BARK.
#
# Every sheet in this kit except the three barks ships without a normal map,
# and the stand-in for the missing ones used to be the bark normal -- which
# carves deep vertical grooves across a flat leaf card, throws half its pixels'
# normals away from the sun and mottles the canopy into noise. `FLAT` is the
# engine's own unperturbed normal: the card is then lit by the geometry it
# actually has, which for a card is the right answer.
FLAT = '/Engine/EngineMaterials/DefaultNormal.DefaultNormal'


def tex(name):
    if name == 'FLAT':
        return {'refPath': FLAT}
    return {'refPath': WOOD + name + '.' + name}

# THE SHEETS ARE NOT DARK; THE FIRST MEASUREMENT OF THEM WAS WRONG.
#
# `Leaves_NormalTree_C` reads as an average of (38,46,19) in sRGB -- near
# black -- if you average the whole file, and that number is what sent this
# project hunting for a brightness fix that was never needed. The file is a
# 1024-square PALETTE: 78% of it is fully transparent, and the decoder here
# composites transparency onto a flat (24,24,24) grey so a contact sheet has
# something to show. Averaging the empty 78% in is averaging the grey in.
#
# Measured over the OPAQUE pixels only (`sheet.read_raw`, which keeps alpha)
# the leaf is a single flat (88,123,0) -- 0.16 luminance in linear, an
# ordinary healthy green. Every sheet in the kit measures sensibly that way.
# So `Lift` is 1.0 everywhere here, and what actually made the canopies read
# as black silhouettes was single-sided lighting on leaf CARDS: see the
# two-sided override further down.
#
# The kit ships colour and, for bark only, a normal map. Nothing has an ORM
# sheet, so roughness is told rather than read -- see `RoughFloor`. Bark and
# leaves are both thoroughly matte; nothing in a wood is polished.
# The last two numbers are the wind: see the note where they are set.
#
# BARK AND LEAVES OF ONE TREE SHARE BOTH. The trunk is held still by `Stiff`,
# not by a smaller `Sway` -- give the canopy more sway than the trunk it grows
# out of and the two surfaces separate at the join, which is a tree tearing in
# half in a breeze. The pines share the common bark sheet, so they share its
# numbers as well.
SHEETS = {
    'Bark_NormalTree1':  ('Bark_NormalTree',   'Bark_NormalTree_Normal',   0.92, 20.0, 4.2, 1.0, False),
    'Bark_DeadTree1':    ('Bark_DeadTree',     'Bark_DeadTree_Normal',     0.94, 10.0, 4.0, 1.0, False),
    'Bark_TwistedTree1': ('Bark_TwistedTree',  'Bark_TwistedTree_Normal',  0.92, 18.0, 3.4, 1.0, False),
    'Leaves_NormalTree': ('Leaves_NormalTree_C',  'FLAT', 0.88, 20.0, 4.2, 1.0, True),
    'Leaves_TwistedTree':('Leaves_TwistedTree_C', 'FLAT', 0.88, 18.0, 3.4, 1.0, True),
    'Leaves_Pine':       ('Leaf_Pine_C',          'FLAT', 0.88, 20.0, 4.2, 1.0, True),
    'Leaves1':           ('Leaves',              'FLAT',  0.88, 16.0, 1.1, 1.0, True),
    'Grass1':            ('Grass',               'FLAT',  0.90, 26.0, 0.22, 1.0, True),
    'Flowers1':          ('Leaves',              'FLAT',  0.88, 18.0, 0.3, 1.0, True),
    'Mushrooms1':        ('Mushrooms',           'FLAT',  0.86, 0.0, 1.0, 1.0, False),
    'PathRocks':         ('PathRocks_Diffuse',   'FLAT',  0.80, 0.0, 1.0, 1.0, False),
    'Rocks':             ('Rocks_Diffuse',       'FLAT',  0.80, 0.0, 1.0, 1.0, False),
}

# HOW MUCH EACH SHEET VARIES FROM COPY TO COPY.
#
# Anything the world stamps out in thousands wants it; anything with structure
# of its own does not. Rocks are left alone deliberately: a boulder whose
# colour wanders reads as a different STONE, and the crags should look like one
# country rather than a gravel pit of assorted minerals.
VARIES = {
    'Leaves_NormalTree': 1.0, 'Leaves_TwistedTree': 1.0, 'Leaves_Pine': 0.85,
    'Leaves1': 1.0, 'Grass1': 1.0, 'Flowers1': 0.9,
    'Bark_NormalTree1': 0.45, 'Bark_DeadTree1': 0.45, 'Bark_TwistedTree1': 0.45,
    'Mushrooms1': 0.5,
}

made = {}
for slot, (base, normal, rough, sway, stiff, lift, soft) in SHEETS.items():
    name = 'MP_' + slot.rstrip('1')
    path = '%s%s.%s' % (WOOD, name, name)
    call(AS, 'delete', {'path': path.split('.')[0]})
    call(MI, 'create', {'folder_path': '/Game/Interval/Nature',
                        'asset_name': name,
                        'parent': {'refPath': SOFT if soft else OPAQUE}})
    call(MI, 'set_texture_parameter', {'instance': {'refPath': path},
         'name': 'BaseColorTexture', 'value': tex(base)})
    call(MI, 'set_texture_parameter', {'instance': {'refPath': path},
         'name': 'NormalTexture', 'value': tex(normal)})
    # No ORM sheet exists anywhere in this kit, so the colour map stands in and
    # the floor below is what stops wet bark coming out like polished stone.
    call(MI, 'set_texture_parameter', {'instance': {'refPath': path},
         'name': 'ORMTexture', 'value': tex(base)})
    # A CARD IS CUT BY ITS OWN ALPHA; SOLID GEOMETRY IS NOT.
    #
    # `soft` is already this table's word for "this sheet is a card" -- it is
    # what picks the foliage master over the opaque one -- so it is the right
    # thing to ask. Leaves, grass and flowers get their shape from the atlas's
    # alpha; bark, rocks and mushrooms are solid and must not be cut, or they
    # would be punched full of holes by an alpha channel that means nothing.
    for param, v in (('Cover', 1.0 if soft else 0.0),
                     ('Strength', 0.0), ('Puff', 0.0), ('Cut', -100000.0),
                     ('HairTint', 0.0), ('MetalMax', 0.0), ('RoughFloor', rough),
                     # `Sway` is how far it moves at full gale, in centimetres;
                     # `Stiff` the height in metres at which it is fully bending,
                     # which is what holds a trunk still under a moving canopy.
                     # Bark and leaves of one tree MUST match or the tree tears.
                     ('Sway', sway), ('Stiff', stiff),
                     ('Varies', VARIES.get(slot, 0.0)),
                     # The colour map is standing in for the ORM, so its red
                     # channel is not occlusion and must not be believed.
                     ('AOFloor', 1.0),
                     # How far this sheet's albedo is lifted; see person_mat.hlsl.
                     ('Lift', lift)):
        call(MI, 'set_scalar_parameter',
             {'instance': {'refPath': path}, 'name': param, 'value': v})
    # TWO-SIDED, FOR ANYTHING THAT IS A CARD.
    #
    # A blade of grass and a clump of leaves are single-sided planes, and half
    # of any clump faces away from you. Lit on one side only, that half renders
    # BLACK -- which is what made a green meadow look like a field of burnt
    # stubble, and the tree canopies read as silhouettes at noon.
    #
    # It is set on the INSTANCE rather than the master, because the master is
    # also what people are made of and a two-sided person is a person you can
    # see the inside of.
    if sway > 0.0:
        call(OBJ, 'set_properties', {'instance': {'refPath': path}, 'values': json.dumps(
            {'BasePropertyOverrides': {'bOverride_TwoSided': True, 'TwoSided': True}})})
    call(AS, 'save_assets', {'asset_paths': [path.split('.')[0]]})
    # THE SLOT NAMES ARE NOT THE MATERIAL NAMES. The importer had to rename
    # `Bark_NormalTree` to `Bark_NormalTree1` because a TEXTURE of that name
    # already existed in the folder, but the mesh's slot kept the original.
    # Both spellings are registered or seven of the twelve sheets go unused.
    made[slot] = path
    made[slot.rstrip('1')] = path
    print(name)

# ONE MESH WANTS A DIFFERENT SHEET FROM ITS SLOT.
#
# `Leaves_TwistedTree_C` is genuinely red -- measured at (64,24,24), against
# (38,46,19) for the common tree -- so the twisted trees are an autumn species
# on purpose and look right. Bush_Common happens to share their slot, and a
# bright red bush under every hedge does not. It takes the green sheet.
#
# AND `Leaves1` WAS THE WRONG PLACE TO SEND THEM. Its texture is `Leaves`,
# which is not a leaf sheet at all -- it is the kit's 1024-square PALETTE, and
# the note at the top of this file already records that it is 78% transparent.
# A mesh whose UVs run across the whole atlas renders it literally: pale paper
# flecked with every colour in the kit, which is what every bush in the world
# has looked like. It was reported as "the bushes look unfinished", and they
# were not unfinished -- they were wearing the colour chart.
#
# `Leaves_NormalTree` is the actual green leaf sheet, which is what a bush
# under a hedge should be wearing and what the override was reaching for.
OVERRIDE = {'Bush_Common': {'Leaves_TwistedTree': 'Leaves_NormalTree'},
            'Bush_Common_Flowers': {'Leaves_TwistedTree': 'Leaves_NormalTree'}}


# ---- THE MESH LIST COMES OFF THE DISK WHEN THE REPORT IS GONE ----
#
# This read a json the IMPORTER wrote, in the session scratchpad. A scratchpad
# does not survive, and the day it was missing `rebuild.sh` ran this script,
# got a FileNotFoundError, carried on to the next one, and left every nature
# mesh bound to material instances whose master had just been deleted and
# re-created -- which is the silent grey this project has been caught by twice
# already. The rebuild reported nothing but one line of traceback in a list of
# fifteen.
#
# `dress_forged.py` learned the same lesson and wrote it down: the names come
# off the disk, not out of one script. The registry knows every static mesh in
# the folder the importer put them in, and it knows it after a restart.
def _meshes_on_disk(folder):
    found = call('editor_toolset.toolsets.asset.AssetTools', 'find_assets',
                 {'folder_path': folder, 'name': '', 'recursive': True,
                  'asset_type': {'refPath': '/Script/Engine.StaticMesh'}})
    try:
        got = json.loads(found)['returnValue']
    except Exception:
        return []
    # THE REGISTRY ANSWERS WITH A PACKAGE PATH AND THE TOOLSETS WANT AN OBJECT
    # PATH. `find_assets` gives `/Game/X/Petal_1`; `get_material_slots` refuses
    # that and wants `/Game/X/Petal_1.Petal_1`, and the refusal is one line of
    # "is not a valid Object" per mesh in a script that prints a lot -- so it
    # reads as noise rather than as every mesh being skipped.
    return [q if '.' in q.rsplit('/', 1)[-1] else q + '.' + q.rsplit('/', 1)[-1]
            for q in got]


def _mesh_list(report, folder):
    try:
        return json.load(open(report))['meshes']
    except Exception:
        got = _meshes_on_disk(folder)
        print('no import report; took %d meshes off the disk in %s' % (len(got), folder))
        return got

meshes = _mesh_list(
    r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/"
    r"d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/nature.json", '/Game/Interval/Nature')
missed = set()
for mesh in meshes:
    slots = call(SM, 'get_material_slots', {'mesh': {'refPath': mesh}})
    try:
        slots = json.loads(slots)['returnValue']
    except Exception:
        print('  ?', mesh, slots[:60]); continue
    short = mesh.split('/')[-1].split('.')[0]
    for s in slots:
        want = OVERRIDE.get(short, {}).get(s, s)
        if want in made:
            call(SM, 'set_material', {'mesh': {'refPath': mesh}, 'slot_name': s,
                                      'material': {'refPath': made[want]}})
        else:
            missed.add(s)
    call(AS, 'save_assets', {'asset_paths': [mesh.split('.')[0]]})
print('meshes dressed:', len(meshes), 'slots with no sheet:', sorted(missed))
