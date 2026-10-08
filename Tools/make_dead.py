#!/usr/bin/env python3
"""The walking dead, made out of the living.

This world has five words for a corpse that walks. They were a cartoon
skeleton with a round skull and black eye sockets, which is plainly wrong
beside these people -- and before that, `skeleton-knight` pointed at the
CITIZENS' base body, whose materials are cut off at the neck so that clothes
can cover the rest. It had been rendering as a floating head.

So the dead get a body of their own: the same figure, uncut, drained of colour.
"""
import json, os, subprocess, sys
import rpc as _rpc
SP = os.path.dirname(os.path.abspath(__file__))
BASE = '/Game/Interval/Universal/Base/'
DEAD = '/Game/Interval/Beasts/Risen'
MASTER = '/Game/Interval/Materials/M_IntervalPerson.M_IntervalPerson'
MI = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools'
SK = 'editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools'
AS = 'editor_toolset.toolsets.asset.AssetTools'

def call(toolset, tool, args):
    # One session for the whole script; see Tools/rpc.py.
    return _rpc.call(toolset, tool, args)


call('EditorToolset.EditorAppToolset', 'StopPIE', {})

# One pallid sheet per skin, uncut, so a corpse is a whole body.
SKINS = {
    'MP_Dead_Male':   ('T_Superhero_Male_Dark', 'T_Superhero_Male_Normal',
                       'T_Superhero_Male_Roughness'),
    'MP_Dead_Female': ('T_Superhero_Female_Dark_BaseColor', 'T_Superhero_Female_Normal',
                       'T_Superhero_Female_Roughness'),
    'MP_Dead_Hair':   ('T_Hair_1_BaseColor', 'T_Hair_2_Normal', 'T_Hair_1_BaseColor'),
    'MP_Dead_Eyes':   ('T_Eye_Brown', 'T_Hair_2_Normal', 'T_Eye_Brown'),
}
for name, (base, normal, orm) in SKINS.items():
    path = '%s%s.%s' % (BASE, name, name)
    call(AS, 'delete', {'path': path.split('.')[0]})
    call(MI, 'create', {'folder_path': '/Game/Interval/Universal/Base',
                        'asset_name': name, 'parent': {'refPath': MASTER}})
    for param, t in (('BaseColorTexture', base), ('NormalTexture', normal),
                     ('ORMTexture', orm)):
        call(MI, 'set_texture_parameter', {'instance': {'refPath': path}, 'name': param,
                                           'value': {'refPath': BASE + t + '.' + t}})
    for param, v in (('Strength', 0.0), ('Puff', 0.0),
                     # CUT AT THE COLLAR, like the living. This used to be
                     # uncut, on the reasoning that a corpse wears no outfit --
                     # and then the first contact sheet of the bestiary showed
                     # what that actually looks like, which is a naked
                     # bodybuilder in briefs walking across a moor. The dead
                     # wear peasant cloth now (see BEASTS), so the body below
                     # the collar is covered and must not be drawn: the free
                     # base figure is a broader physique than the outfits are
                     # cut for and stands several centimetres outside them.
                     ('Cut', 152.0 if 'Male' in name or 'Female' in name else -100000.0),
                     ('HairTint', 0.0), ('MetalMax', 0.0), ('RoughFloor', 0.0),
                     # A roughness map, not an ORM: its red is roughness.
                     ('AOFloor', 1.0),
                     ('Pallor', 0.88)):
        call(MI, 'set_scalar_parameter', {'instance': {'refPath': path},
                                          'name': param, 'value': v})
    call(AS, 'save_assets', {'asset_paths': [path.split('.')[0]]})
    print(name)

# A copy of the body, so dressing it as a corpse cannot touch the living.
for who, sheet in (('Superhero_Male_FullBody', 'MP_Dead_Male'),
                   ('Superhero_Female_FullBody', 'MP_Dead_Female')):
    made = 'Risen_' + ('Male' if 'Male_' in who else 'Female')
    dst = '%s/%s' % (DEAD, made)
    call(AS, 'delete', {'path': dst})
    r = call(AS, 'duplicate', {'path': BASE + who, 'new_path': dst})
    print(made, r[:60])
    mesh = '%s.%s' % (dst, made)
    raw = call(SK, 'get_material_slots', {'mesh': {'refPath': mesh}})
    try:
        slots = json.loads(raw)['returnValue']
    except Exception:
        print('  slots?', raw[:120]); continue
    for s in slots:
        want = ('MP_Dead_Hair' if 'Hair' in s else
                'MP_Dead_Eyes' if 'Eye' in s else sheet)
        call(SK, 'set_material', {'mesh': {'refPath': mesh}, 'slot_name': s,
                                  'material': {'refPath': '%s%s.%s' % (BASE, want, want)}})
        print('  ', s, '->', want)
    call(AS, 'save_assets', {'asset_paths': [dst]})
