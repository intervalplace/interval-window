#!/usr/bin/env python3
"""Give the imported people a material that this project can actually render.

One instance per atlas the pack ships, each pointed at its own three textures,
then hung on the slot of every mesh that used the grey Substrate original.
"""
import json, os, subprocess, sys
import rpc as _rpc
SP = os.path.dirname(os.path.abspath(__file__))
ART = '/Game/Interval/Universal/People/'
MASTER = '/Game/Interval/Materials/M_IntervalPerson.M_IntervalPerson'
MI = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools'
SK = 'editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools'
AS = 'editor_toolset.toolsets.asset.AssetTools'

def call(toolset, tool, args):
    # One session for the whole script; see Tools/rpc.py.
    return _rpc.call(toolset, tool, args)


# Stop the session first. Rebuilding an asset the running world is using wedges
# the editor solidly -- it holds the port, accepts connections and answers
# nothing -- and it wedges on the FIRST call, so stopping afterwards is too late.
call('EditorToolset.EditorAppToolset', 'StopPIE', {})
def tex(name):
    return {'refPath': ART + name + '.' + name}

# The outfits carry an ORM sheet; the bare skins ship a plain roughness map,
# which reads correctly through the same slot -- see the note in the shader.
# The fourth number is `Puff`: how far this surface stands off the body, in
# centimetres. A citizen is the bare base body plus an outfit modelled at the
# same size on the same skeleton, so a shirt and a chest are COINCIDENT and
# fight for the depth buffer pixel by pixel -- which drew a man in a linen
# shirt with his bare chest punching through it in blotches. Cloth is not
# painted on skin; it hangs a few millimetres off it, and saying so once here
# is the whole fix.
SHEETS = {
    # These two carry a REAL ORM sheet, so their metal channel is worth having:
    # a ranger's buckles and a peasant's belt fittings are metal.
    'MI_Peasant':        ('T_Peasant_BaseColor', 'T_Peasant_Normal', 'T_Peasant_ORM', 1.0, 0.8, 1.0),
    'MI_Ranger':         ('T_Ranger_BaseColor',  'T_Ranger_Normal',  'T_Ranger_ORM', 1.0, 0.8, 1.0),
    # ---- AND THE FOUR THAT WERE NEVER DRESSED AT ALL ----
    #
    # `import_universal.py` brings in six outfits in both sexes. This table
    # had two of them. The other four kept the material the FBX import made --
    # `MI_Knight`, `MI_Noble`, `MI_Wizard` -- which is parented to nothing this
    # project owns, and when `make_person_mat.py` deleted and re-created
    # `M_IntervalPerson` they were left pointing at a trashed object.
    #
    # A material instance whose parent has been trashed draws NOTHING. So a
    # citizen in a knight's surcoat was a floating head with a nameplate over
    # it, and the head was there because the head comes off the base body,
    # which IS dressed. Found by projecting the citizen's own head bone to the
    # screen, cropping to that pixel, and seeing floorboards.
    #
    # All three carry a real ORM sheet, so their metal channel means something:
    # mail, a noble's clasps, the fittings on a wizard's belt.
    'MI_Knight':         ('T_Knight_BaseColor', 'T_Knight_Normal', 'T_Knight_ORM', 1.0, 0.8, 1.0),
    'MI_Noble':          ('T_Noble_BaseColor',  'T_Noble_Normal',  'T_Noble_ORM',  1.0, 0.8, 1.0),
    'MI_Wizard':         ('T_Wizard_BaseColor', 'T_Wizard_Normal', 'T_Wizard_ORM', 1.0, 0.9, 0.6),
    # Skin does not take a dye. Somebody's face is not a garment.
    # These are a plain roughness map standing in for an ORM, so their blue
    # channel is mid-grey and means nothing. Skin is not metal.
    'MI_Regular_Male':   ('T_Regular_Male_Dark_BaseColor', 'T_Regular_Male_Normal',
                          'T_Regular_Male_Roughness', 0.0, 0.0, 0.0),
    'MI_Regular_Female': ('T_Regular_Female_Dark_BaseColor', 'T_Regular_Female_Normal',
                          'T_Regular_Female_Roughness', 0.0, 0.0, 0.0),
}

made = {}
for slot, (base, normal, orm, dye, puff, metal) in SHEETS.items():
    name = 'MP_' + slot.replace('MI_', '')
    path = '/Game/Interval/Universal/People/%s.%s' % (name, name)
    call(AS, 'delete', {'path': path.split('.')[0]})
    print(name, call(MI, 'create', {'folder_path': '/Game/Interval/Universal/People',
                                    'asset_name': name,
                                    'parent': {'refPath': MASTER}})[:70])
    for param, t in (('BaseColorTexture', base), ('NormalTexture', normal),
                     ('ORMTexture', orm)):
        call(MI, 'set_texture_parameter',
             {'instance': {'refPath': path}, 'name': param, 'value': tex(t)})
    call(MI, 'set_scalar_parameter',
         {'instance': {'refPath': path}, 'name': 'Strength', 'value': dye})
    call(MI, 'set_scalar_parameter',
         {'instance': {'refPath': path}, 'name': 'Puff', 'value': puff})
    call(MI, 'set_scalar_parameter',
         {'instance': {'refPath': path}, 'name': 'Cut', 'value': -100000.0})
    call(MI, 'set_scalar_parameter',
         {'instance': {'refPath': path}, 'name': 'RoughFloor', 'value': 0.0})
    call(MI, 'set_scalar_parameter',
         {'instance': {'refPath': path}, 'name': 'MetalMax', 'value': metal})
    # A REAL ORM SHEET KEEPS ITS OCCLUSION; A STAND-IN MUST NOT BE BELIEVED.
    # The outfits ship `*_ORM`; the two skins have only a roughness map, whose
    # red channel is roughness and would be read as a face sitting in a cave.
    call(MI, 'set_scalar_parameter',
         {'instance': {'refPath': path}, 'name': 'AOFloor',
          'value': 0.0 if orm.endswith('_ORM') else 1.0})
    call(AS, 'save_assets', {'asset_paths': [path.split('.')[0]]})
    made[slot] = path

# The bases, which is where a citizen's head, eyes and hands come from. The
# eyes and the eyebrows are separate slots on the same figure; none of them is
# a garment, so none of them takes a dye.
BASE = '/Game/Interval/Universal/Base/'

def btex(name):
    return {'refPath': BASE + name + '.' + name}

BASES = {
    'MI_Superhero_Male':   ('T_Superhero_Male_Dark', 'T_Superhero_Male_Normal',
                            'T_Superhero_Male_Roughness'),
    'MI_Superhero_Female': ('T_Superhero_Female_Dark_BaseColor', 'T_Superhero_Female_Normal',
                            'T_Superhero_Female_Roughness'),
    'MI_Hair_1':           ('T_Hair_1_BaseColor', 'T_Hair_2_Normal', 'T_Hair_1_BaseColor'),
    'MI_Hair_2':           ('T_Hair_2_BaseColor', 'T_Hair_2_Normal', 'T_Hair_2_BaseColor'),
    'MI_Eyes':             ('T_Eye_Brown', 'T_Hair_2_Normal', 'T_Eye_Brown'),
}
# NECK HEIGHT, in the figure's own bind pose. The base body measures 181 cm
# from sole to crown; a collar sits at about six sevenths of that. Below it
# nothing of this body is drawn, because the outfit is there instead -- see the
# note in person_mat.hlsl for why the body cannot simply be worn under the
# clothes. Hair and eyes are on the head and so are never cut.
NECK = 152.0
for slot, (base, normal, orm) in BASES.items():
    name = 'MP_' + slot.replace('MI_', '')
    path = '%s%s.%s' % (BASE, name, name)
    call(AS, 'delete', {'path': path.split('.')[0]})
    print(name, call(MI, 'create', {'folder_path': '/Game/Interval/Universal/Base',
                                    'asset_name': name,
                                    'parent': {'refPath': MASTER}})[:70])
    for param, t in (('BaseColorTexture', base), ('NormalTexture', normal),
                     ('ORMTexture', orm)):
        call(MI, 'set_texture_parameter',
             {'instance': {'refPath': path}, 'name': param, 'value': btex(t)})
    call(MI, 'set_scalar_parameter', {'instance': {'refPath': path},
                                      'name': 'Strength', 'value': 0.0})
    call(MI, 'set_scalar_parameter', {'instance': {'refPath': path},
                                      'name': 'Puff', 'value': 0.0})
    call(MI, 'set_scalar_parameter', {'instance': {'refPath': path}, 'name': 'Cut',
                                      'value': NECK if 'Superhero' in slot else -100000.0})
    call(MI, 'set_scalar_parameter', {'instance': {'refPath': path}, 'name': 'RoughFloor',
                                      'value': 0.0 if 'Superhero' in slot else 0.6})
    call(MI, 'set_scalar_parameter', {'instance': {'refPath': path},
                                      'name': 'MetalMax', 'value': 0.0})
    # None of the bases has an ORM: skin is a roughness map, hair and eyes are
    # their own colour map. See `AOFloor`.
    call(MI, 'set_scalar_parameter', {'instance': {'refPath': path},
                                      'name': 'AOFloor', 'value': 1.0})
    call(AS, 'save_assets', {'asset_paths': [path.split('.')[0]]})
    made[slot] = path

for who in ('Superhero_Male_FullBody', 'Superhero_Female_FullBody'):
    mesh = '%s%s.%s' % (BASE, who, who)
    slots = json.loads(call(SK, 'get_material_slots', {'mesh': {'refPath': mesh}}))['returnValue']
    for s in slots:
        if s in made:
            call(SK, 'set_material', {'mesh': {'refPath': mesh}, 'slot_name': s,
                                      'material': {'refPath': made[s]}})
            print(' ', who, s, '->', made[s].split('/')[-1])
        else:
            print(' ', who, s, 'UNMATCHED')
    call(AS, 'save_assets', {'asset_paths': [mesh.split('.')[0]]})

# EVERY OUTFIT MESH, not the four that happened to be listed. A mesh missing
# from here keeps whatever the importer gave it, which is the fault above.
for who in ('Male_Peasant', 'Female_Peasant', 'Male_Ranger', 'Female_Ranger',
            'Male_Knight', 'Female_Knight',
            'Male_Knight_Cloth', 'Female_Knight_Cloth',
            'Male_Noble', 'Female_Noble',
            'Male_Wizard', 'Female_Wizard'):
    mesh = '/Game/Interval/Universal/People/%s.%s' % (who, who)
    slots = json.loads(call(SK, 'get_material_slots', {'mesh': {'refPath': mesh}}))['returnValue']
    for s in slots:
        if s in made:
            r = call(SK, 'set_material', {'mesh': {'refPath': mesh}, 'slot_name': s,
                                          'material': {'refPath': made[s]}})
            print(' ', who, s, '->', made[s].split('/')[-1], r[:40])
        else:
            print(' ', who, s, 'UNMATCHED')
    call(AS, 'save_assets', {'asset_paths': [mesh.split('.')[0]]})

# THE HAIR. It ships with a colour map and a normal map and no ORM sheet, so
# the roughness has to be told rather than read -- see `RoughFloor`. The
# hairstyles all use one of two atlases between them.
HAIRDO = '/Game/Interval/Universal/Hair/'

def htex(name):
    return {'refPath': HAIRDO + name + '.' + name}

hairmade = {}
for slot, sheet in (('MI_Hair_1', 'T_Hair_1'), ('MI_Hair_2', 'T_Hair_2')):
    name = 'MP_Do_' + slot.replace('MI_Hair_', '')
    path = '%s%s.%s' % (HAIRDO, name, name)
    call(AS, 'delete', {'path': path.split('.')[0]})
    print(name, call(MI, 'create', {'folder_path': '/Game/Interval/Universal/Hair',
                                    'asset_name': name,
                                    'parent': {'refPath': MASTER}})[:70])
    call(MI, 'set_texture_parameter', {'instance': {'refPath': path},
         'name': 'BaseColorTexture', 'value': htex(sheet + '_BaseColor')})
    call(MI, 'set_texture_parameter', {'instance': {'refPath': path},
         'name': 'NormalTexture', 'value': htex(sheet + '_Normal')})
    # No ORM sheet exists, so the colour map stands in for it and the floor
    # below is what stops dark hair coming out polished.
    call(MI, 'set_texture_parameter', {'instance': {'refPath': path},
         'name': 'ORMTexture', 'value': htex(sheet + '_BaseColor')})
    for param, v in (('Strength', 0.0), ('Puff', 0.0), ('Cut', -100000.0),
                     ('RoughFloor', 0.62), ('HairTint', 1.0), ('MetalMax', 0.0),
                     # Colour map in the ORM slot again; see `AOFloor`.
                     ('AOFloor', 1.0)):
        call(MI, 'set_scalar_parameter',
             {'instance': {'refPath': path}, 'name': param, 'value': v})
    call(AS, 'save_assets', {'asset_paths': [path.split('.')[0]]})
    hairmade[slot] = path

for who in ('Hair_Buzzed', 'Hair_SimpleParted', 'Hair_Long', 'Hair_Beard',
            'Hair_Buns', 'Hair_BuzzedFemale'):
    mesh = '%s%s.%s' % (HAIRDO, who, who)
    slots = json.loads(call(SK, 'get_material_slots', {'mesh': {'refPath': mesh}}))['returnValue']
    for sl in slots:
        if sl in hairmade:
            call(SK, 'set_material', {'mesh': {'refPath': mesh}, 'slot_name': sl,
                                      'material': {'refPath': hairmade[sl]}})
            print(' ', who, sl, '->', hairmade[sl].split('/')[-1])
        else:
            print(' ', who, sl, 'UNMATCHED')
    call(AS, 'save_assets', {'asset_paths': [mesh.split('.')[0]]})
