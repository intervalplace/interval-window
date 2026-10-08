# HALF OF THIS PACK IS GONE. `Men` and `Women` -- the modern modular
# characters, a hi-vis worker and a business suit among them -- were
# dropped on judgement and deleted. `Weapons` stays: every blade, bow
# and shield a citizen carries is still out of it.
# Brings in the CC0 medieval weapons as static meshes, then re-parents EVERY
# material the Quaternius import made onto M_IntervalFlat.
#
# Re-parenting keeps `DiffuseColor`, because the new parent asks for a
# parameter of exactly that name -- so the artist's palette arrives intact and
# nothing has to copy a colour anywhere. What is set here is the other half:
# `Strength`, how much of this region a citizen's own key may turn. The art
# names its own materials, so this is read off the name rather than guessed.
import os, json, unreal

ART  = os.path.abspath(os.path.join(unreal.Paths.project_dir(), 'Art', 'Quaternius'))
DEST = '/Game/Interval/Quaternius'
FLAT = '/Game/Interval/Materials/M_IntervalFlat.M_IntervalFlat'
OUT  = r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/dress.json"

tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary
report = {'kit': [], 'reparented': [], 'errors': []}

# ---- the weapons, as static meshes ----------------------------------------
def static_options():
    ui = unreal.FbxImportUI()
    ui.set_editor_property('import_mesh', True)
    ui.set_editor_property('import_as_skeletal', False)
    ui.set_editor_property('import_animations', False)
    ui.set_editor_property('import_materials', True)
    ui.set_editor_property('import_textures', True)
    ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_STATIC_MESH)
    sm = ui.get_editor_property('static_mesh_import_data')
    sm.set_editor_property('combine_meshes', True)
    sm.set_editor_property('convert_scene', True)
    sm.set_editor_property('generate_lightmap_u_vs', False)
    return ui

weapons = os.path.join(ART, 'Weapons')
tasks = []
if os.path.isdir(weapons):
    for f in sorted(os.listdir(weapons)):
        if not f.lower().endswith('.fbx'):
            continue
        t = unreal.AssetImportTask()
        t.set_editor_property('filename', os.path.join(weapons, f))
        t.set_editor_property('destination_path', DEST + '/Kit')
        t.set_editor_property('destination_name', os.path.splitext(f)[0])
        t.set_editor_property('automated', True)
        t.set_editor_property('replace_existing', True)
        t.set_editor_property('save', True)
        t.set_editor_property('options', static_options())
        tasks.append(t)
    tools.import_asset_tasks(tasks)
    for t in tasks:
        report['kit'] += [str(p) for p in t.get_editor_property('imported_object_paths')]
else:
    report['errors'].append('no ' + weapons)

# ---- one parent for the lot -----------------------------------------------
# How far a citizen's own key may turn each region of them. Eyes never move --
# an odd eye colour is the first thing that reads as WRONG rather than as
# variety. Skin barely moves. Cloth moves most, because that is where a crowd
# is told apart. Anything in their hands does not move at all: a sword is the
# world's sword, not this person's.
ALLOW = {'eye': 0.0, 'eyebrows': 0.0, 'skin': 0.2, 'hair': 0.6}

flat = lib.load_asset(FLAT)
if flat is None:
    report['errors'].append('no M_IntervalFlat')
else:
    for p in sorted(lib.list_assets(DEST, recursive=True, include_folder=False)):
        d = lib.find_asset_data(p)
        if str(d.asset_class_path.asset_name) != 'MaterialInstanceConstant':
            continue
        mi = lib.load_asset(p)
        name = p.split('/')[-1].split('.')[0].lower()
        was = mi.get_editor_property('parent')
        mi.set_editor_property('parent', flat)
        strength = 0.0 if '/Kit/' in p else ALLOW.get(name, 1.0)
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            mi, 'Strength', strength)
        lib.save_asset(p, False)
        report['reparented'].append([p, was.get_name() if was else '?', strength])

with open(OUT, 'w') as f:
    json.dump(report, f, indent=1)
unreal.log('QUATERNIUS DRESSED')
