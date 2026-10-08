#!/usr/bin/env python3
"""Give the imported Folk meshes materials this project can render.

WHY THIS FILE EXISTS. `import_wizard.py` brings in the wizard, the cleric, the
monk and the wizard's staff, along with their textures -- and nothing ever
dressed them. The meshes kept the material the FBX importer invented, which is
parented to nothing this project owns, so they render flat.

It went unnoticed for a long time because the one that is visible is the
STAFF, which the keepers carry and which four of the world's weapon words are
drawn as: `staff`, `bone-staff`, `heartwood-staff` and `goo-staff`. It was
found by measuring the inventory sprites and asking which of them were
entirely achromatic: those four, and nothing else in the pack.

This is the third instance of the same fault tonight -- the Knight, Noble and
Wizard outfits had it, and the forged goods had it before them. The shape is
always the same: an import brings a mesh in, something else is written to
dress it, and a mesh that was added later is not in the list.
"""
import json, os, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import rpc

FOLK = '/Game/Interval/Folk/'
TEX = FOLK + 'Textures/'
MASTER = '/Game/Interval/Materials/M_IntervalPerson.M_IntervalPerson'
MI = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools'
SM = 'editor_toolset.toolsets.static_mesh.StaticMeshTools'
SK = 'editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools'
AS = 'editor_toolset.toolsets.asset.AssetTools'

call = rpc.call
call('EditorToolset.EditorAppToolset', 'StopPIE', {})

# ONE MATERIAL PER SHEET, NOT PER MESH.
#
# The slots are named after the texture they want -- `Wizard_Texture`,
# `Wizard_Staff_Texture` -- and a wizard has two of them, because the staff is
# modelled into the same skeletal mesh as the body. Dressing per MESH gave the
# staff slot the body's sheet, which is a wizard whose staff is made of wizard.
# So the sheets are the table and the slot name chooses.
SHEETS = ('Wizard_Texture', 'Cleric_Texture', 'Monk_Texture', 'Wizard_Staff_Texture')

# mesh -> whether it is skeletal. The three figures are; the staff prop is not,
# and a mesh's slots are read and set through a different toolset for each.
WEARS = {
    'Wizard_Staff1': False,
    'Wizard':        True,
    'Cleric':        True,
    'Monk':          True,
}

made = {}
for sheet in SHEETS:
    name = 'MP_' + sheet.replace('_Texture', '')
    path = '%s%s.%s' % (FOLK, name, name)
    call(AS, 'delete', {'path': path.split('.')[0]})
    call(MI, 'create', {'folder_path': FOLK[:-1], 'asset_name': name,
                        'parent': {'refPath': MASTER}})
    # The colour map goes in all three slots. These kits ship one sheet and no
    # ORM, so the roughness has to be told rather than read -- the same
    # arrangement the hair uses, and for the same reason.
    for param in ('BaseColorTexture', 'NormalTexture', 'ORMTexture'):
        call(MI, 'set_texture_parameter', {'instance': {'refPath': path},
             'name': param, 'value': {'refPath': TEX + sheet + '.' + sheet}})
    for param, v in (('Strength', 0.0),      # nothing here takes a citizen's dye
                     ('Puff', 0.0),
                     ('Cut', -100000.0),     # draw all of it
                     ('RoughFloor', 0.62),
                     ('MetalMax', 0.0),
                     ('AOFloor', 1.0)):      # no real ORM: do not believe it
        call(MI, 'set_scalar_parameter',
             {'instance': {'refPath': path}, 'name': param, 'value': v})
    call(AS, 'save_assets', {'asset_paths': [path.split('.')[0]]})
    made[sheet] = path
    print('%-22s -> %s' % (sheet, name))

# WHICH SHEET A SLOT WANTS. The slot name says so, and where it does not say
# anything this project recognises the mesh's own name decides -- the staff
# prop's only slot is called `Wizard_Staff`, which is the staff's sheet under
# a slightly different name.
def sheet_for(mesh, slot):
    if slot in made:
        return made[slot]
    if 'Staff' in slot or 'Staff' in mesh:
        return made['Wizard_Staff_Texture']
    for key, path in made.items():
        if key.split('_')[0] in mesh:
            return path
    return None

for mesh, skeletal in WEARS.items():
    ref = {'refPath': '%s%s.%s' % (FOLK, mesh, mesh)}
    tool = SK if skeletal else SM
    try:
        slots = json.loads(call(tool, 'get_material_slots', {'mesh': ref}))['returnValue']
    except Exception as exc:
        print('  %s: no slots (%s)' % (mesh, str(exc)[:60]))
        continue
    for s in slots:
        path = sheet_for(mesh, s)
        if not path:
            print('  %s %s UNMATCHED' % (mesh, s))
            continue
        call(tool, 'set_material', {'mesh': ref, 'slot_name': s,
                                    'material': {'refPath': path}})
        print('  %-16s %-24s -> %s' % (mesh, s, path.split('/')[-1].split('.')[0]))
    call(AS, 'save_assets', {'asset_paths': ['%s%s' % (FOLK, mesh)]})
print('NOW RUN apply.py')
