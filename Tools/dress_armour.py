#!/usr/bin/env python3
"""Give the helms a material this project renders, and hang them on heads."""
import json, os, subprocess, sys
import rpc as _rpc
SP = os.path.dirname(os.path.abspath(__file__))
KIT = '/Game/Interval/Armour/'
MASTER = '/Game/Interval/Materials/M_IntervalPerson.M_IntervalPerson'
MI = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools'
SM = 'editor_toolset.toolsets.static_mesh.StaticMeshTools'
AS = 'editor_toolset.toolsets.asset.AssetTools'

def call(toolset, tool, args):
    # One session for the whole script; see Tools/rpc.py.
    return _rpc.call(toolset, tool, args)


call('EditorToolset.EditorAppToolset', 'StopPIE', {})

def tex(n):
    return {'refPath': KIT + n + '.' + n}

# mesh -> (its one slot's sheet, normal, metal cap)
WEAR = {
    'Helmet1':        ('MetalTexture',       None,                  1.0),
    'Bucket_Helmet2': ('Bucket_Helmet',      None,                  1.0),
    'Iron_Crown':     ('Iron_Crown_Diffuse', 'Iron_Crown_Normal',   1.0),
}
for mesh, (base, normal, metal) in WEAR.items():
    name = 'MP_' + mesh.rstrip('012')
    path = '%s%s.%s' % (KIT, name, name)
    call(AS, 'delete', {'path': path.split('.')[0]})
    call(MI, 'create', {'folder_path': '/Game/Interval/Armour',
                        'asset_name': name, 'parent': {'refPath': MASTER}})
    call(MI, 'set_texture_parameter', {'instance': {'refPath': path},
         'name': 'BaseColorTexture', 'value': tex(base)})
    call(MI, 'set_texture_parameter', {'instance': {'refPath': path},
         'name': 'NormalTexture', 'value': tex(normal or base)})
    # No ORM anywhere in these; the colour map stands in and the floor below is
    # what keeps a helmet from coming out like a mirror.
    call(MI, 'set_texture_parameter', {'instance': {'refPath': path},
         'name': 'ORMTexture', 'value': tex(base)})
    for param, v in (('Strength', 0.0), ('Puff', 0.0), ('Cut', -100000.0),
                     ('HairTint', 0.0), ('Pallor', 0.0), ('Sway', 0.0),
                     ('MetalMax', metal), ('RoughFloor', 0.34),
                     # Colour map in the ORM slot: do not read occlusion off it.
                     ('AOFloor', 1.0)):
        call(MI, 'set_scalar_parameter', {'instance': {'refPath': path},
                                          'name': param, 'value': v})
    call(AS, 'save_assets', {'asset_paths': [path.split('.')[0]]})

    m = '%s%s.%s' % (KIT, mesh, mesh)
    raw = call(SM, 'get_material_slots', {'mesh': {'refPath': m}})
    try:
        slots = json.loads(raw)['returnValue']
    except Exception:
        print(mesh, 'slots?', raw[:90]); continue
    for s in slots:
        call(SM, 'set_material', {'mesh': {'refPath': m}, 'slot_name': s,
                                  'material': {'refPath': path}})
    call(AS, 'save_assets', {'asset_paths': [m.split('.')[0]]})
    print(mesh, '->', name, slots)


# ---------------------------------------------------------------------------
# AND THE KNIGHT'S PIECES, WHICH CARRY NO TEXTURE AT ALL.
#
# Quaternius's CC0 Knight is flat-coloured: three materials, one diffuse value
# each, no sheets. So they go on M_IntervalFlat like every other flat-coloured
# thing in this project rather than on the textured master, and get their
# colour, their roughness and their world-space grain from there.
FLAT = '/Game/Interval/Materials/M_IntervalFlat.M_IntervalFlat'

# name -> (r, g, b, dry roughness, grain)
# Steel that has been worn and oiled, not showroom chrome: a bright mirror on a
# figure this size reads as plastic, and every helm in the world being the same
# mirror reads as a uniform.
#
# AND THEN THE SIX BODIES, WHICH WERE ONE BODY.
#
# `iron-plate`, `steel-plate`, `quick-plate`, `gold-plate`, `shell-plate` and
# `great-plate` are six different things in the world -- they cost different
# metals, they are worn at different levels, and the cheapest is a day's work
# where the dearest is a season's -- and all six were drawn as the same
# Cuirass wearing the same MP_Steel. A citizen in quickmetal could not be told
# from a citizen in iron, which takes the whole point out of wearing it.
#
# The helms tier by SHAPE, because the kit happens to have five of them. The
# body has one mesh and always will, so it tiers by METAL.
#
# THE COLOURS ARE NOT NEW AND MUST NOT BE. `Tools/tiers.py` already decides
# what each grade's metal reads as, and the inventory sprites have been drawn
# from it for as long as there have been sprites. A second palette invented
# here would put a citizen in a breastplate that does not match its own icon,
# which is a worse fault than the one being fixed. So the table is imported,
# not restated, and a grade whose colour changes there changes here without
# anybody remembering to.
#
# `king-shroud` has no row: it is cloth, not metal, and has a forged mesh of
# its own.
import tiers

PLATE = {
    'MP_Steel':      (0.185, 0.192, 0.205, 0.34, 0.05),
    'MP_Iron':       (0.128, 0.128, 0.132, 0.46, 0.06),
}
# How smooth each grade is, which `tiers.py` has no opinion about because an
# icon is shaded by one light this project chooses. On a body in the world it
# matters: a cheap plate is hammered and a dear one is polished.
FINISH = {'iron': (0.46, 0.06), 'steel': (0.34, 0.05), 'quick': (0.30, 0.05),
          'great': (0.26, 0.04), 'gold': (0.30, 0.05), 'shell': (0.58, 0.11)}
for _grade, (_rough, _grain) in FINISH.items():
    _r, _g, _b = tiers.TIERS[_grade]
    PLATE['MP_Plate' + _grade.capitalize()] = (_r, _g, _b, _rough, _grain)
for name, (r, g, b, rough, grain) in PLATE.items():
    path = '%s%s.%s' % (KIT, name, name)
    call(AS, 'delete', {'path': path.split('.')[0]})
    call(MI, 'create', {'folder_path': '/Game/Interval/Armour',
                        'asset_name': name, 'parent': {'refPath': FLAT}})
    call(MI, 'set_vector_parameter', {'instance': {'refPath': path},
         'name': 'DiffuseColor', 'value': {'r': r, 'g': g, 'b': b, 'a': 1.0}})
    for param, v in (('Rough', rough), ('Course', 0.0), ('Grain', grain),
                     ('Strength', 0.0), ('Shift', 0.5)):
        call(MI, 'set_scalar_parameter',
             {'instance': {'refPath': path}, 'name': param, 'value': v})
    call(AS, 'save_assets', {'asset_paths': [path.split('.')[0]]})

KNIGHT = {
    'Cuirass':             'MP_Steel',
    'Knight_Helmet1':      'MP_Steel',
    'Knight_Helmet2':      'MP_Iron',
    'Knight_Helmet3':      'MP_Steel',
    'Knight_ShoulderPads': 'MP_Iron',
}
# EXCEPT WHERE A MESH NAMES A SLOT AFTER SOMETHING IT IS NOT MADE OF.
# `Knight_Helmet3` is the quick-helm here, and it has a slot the kit author
# called `Golden` for the band round its brow. Bound to MP_Steel with the rest
# of it, the one piece of trim on the rarest helm in the world was the same
# metal as the rest of the helm. It takes quickmetal, the same violet the quick
# plate and the quick weapons take, so a citizen in the quick set is in one
# metal from head to hand.
SLOT = {('Knight_Helmet3', 'Golden'): 'MP_PlateStar'}
for mesh, mat in KNIGHT.items():
    m = '%s%s.%s' % (KIT, mesh, mesh)
    raw = call(SM, 'get_material_slots', {'mesh': {'refPath': m}})
    try:
        slots = json.loads(raw)['returnValue']
    except Exception:
        print(mesh, 'slots?', raw[:90]); continue
    for sl in slots:
        use = SLOT.get((mesh, sl), mat)
        call(SM, 'set_material', {'mesh': {'refPath': m}, 'slot_name': sl,
                                  'material': {'refPath': '%s%s.%s' % (KIT, use, use)}})
    call(AS, 'save_assets', {'asset_paths': [m.split('.')[0]]})
    print(mesh, '->', mat, slots)
