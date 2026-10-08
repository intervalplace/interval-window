#!/usr/bin/env python3
"""Give the imported fantasy props materials this project can render.

The kit is trim-sheeted: four atlases -- cloth, furniture, metal, props --
and every one of the ninety-three meshes uses some combination of them. Each
ships a real ORM, so unlike the nature kit the metal channel is worth having.
"""
import json, os, subprocess, sys
import rpc as _rpc
SP = os.path.dirname(os.path.abspath(__file__))
KIT = '/Game/Interval/Props/'
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

# slot -> (sheet, metal cap, roughness floor)
SHEETS = {
    'MI_Trim_Cloth':        ('T_Trim_Cloth',     0.0, 0.0),
    'MI_Banner':            ('T_Trim_Cloth',     0.0, 0.0),
    'MI_Trim_Furniture':    ('T_Trim_Furniture', 0.4, 0.0),
    'MI_Trim_Metal':        ('T_Trim_Metal',     1.0, 0.0),
    'MI_Trim_Metal_Vertex': ('T_Trim_Metal',     1.0, 0.0),
    'MI_Trim_Props':        ('T_Trim_Props',     1.0, 0.0),
    'MI_Trim_Props_Vertex': ('T_Trim_Props',     1.0, 0.0),
}

made = {}
for slot, (sheet, metal, rough) in SHEETS.items():
    name = 'MP_' + slot.replace('MI_', '')
    path = '%s%s.%s' % (KIT, name, name)
    call(AS, 'delete', {'path': path.split('.')[0]})
    call(MI, 'create', {'folder_path': '/Game/Interval/Props',
                        'asset_name': name, 'parent': {'refPath': MASTER}})
    for param, t in (('BaseColorTexture', sheet + '_BaseColor'),
                     ('NormalTexture', sheet + '_Normal'),
                     ('ORMTexture', sheet + '_ORM')):
        call(MI, 'set_texture_parameter',
             {'instance': {'refPath': path}, 'name': param, 'value': tex(t)})
    for param, v in (('Strength', 0.0), ('Puff', 0.0), ('Cut', -100000.0),
                     ('HairTint', 0.0), ('MetalMax', metal), ('RoughFloor', rough)):
        call(MI, 'set_scalar_parameter',
             {'instance': {'refPath': path}, 'name': param, 'value': v})
    call(AS, 'save_assets', {'asset_paths': [path.split('.')[0]]})
    # Both spellings: the importer renames a material that collides with a
    # texture of the same name, and the mesh's SLOT keeps the original.
    made[slot] = path
    made[slot + '1'] = path
    print(name)


# ---- THE MESH LIST COMES OFF THE DISK WHEN THE REPORT IS GONE ----
#
# This read a json the IMPORTER wrote, in the session scratchpad. A scratchpad
# does not survive, and the day it was missing `rebuild.sh` ran this script,
# got a FileNotFoundError, carried on to the next one, and left every prop
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
    r"d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/props.json", '/Game/Interval/Props')
missed = set()
for mesh in meshes:
    raw = call(SM, 'get_material_slots', {'mesh': {'refPath': mesh}})
    try:
        slots = json.loads(raw)['returnValue']
    except Exception:
        continue
    for s in slots:
        if s in made:
            call(SM, 'set_material', {'mesh': {'refPath': mesh}, 'slot_name': s,
                                      'material': {'refPath': made[s]}})
        else:
            missed.add(s)
    call(AS, 'save_assets', {'asset_paths': [mesh.split('.')[0]]})
print('meshes dressed:', len(meshes), 'slots with no sheet:', sorted(missed))
