# The head slot, which had no art at all.
#
# Six of this world's thirteen armour words are a helm and the character kits
# in use carry none. These three are CC0 from OpenGameArt -- see the README
# beside them, which records where each declaration was read.
#
# A helm and a crown are RIGID: they hang on the `Head` bone the way a sword
# hangs on `hand_r`, so they want importing as static meshes and nothing else.
import os, json, unreal

ART  = os.path.abspath(os.path.join(unreal.Paths.project_dir(), 'Art', 'Armour'))
DEST = '/Game/Interval/Armour'
OUT  = r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/armour.json"

tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary
report = {'errors': [], 'kinds': {}}

def options():
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

tasks = []
for f in sorted(os.listdir(ART)):
    if not f.lower().endswith(('.obj', '.fbx')):
        continue
    t = unreal.AssetImportTask()
    t.set_editor_property('filename', os.path.join(ART, f))
    t.set_editor_property('destination_path', DEST)
    t.set_editor_property('destination_name', os.path.splitext(f)[0].replace(' ', '_'))
    t.set_editor_property('automated', True)
    t.set_editor_property('replace_existing', True)
    t.set_editor_property('save', True)
    t.set_editor_property('options', options())
    tasks.append(t)
tools.import_asset_tasks(tasks)

# The textures come in beside them; an .obj brings no material worth keeping.
for f in sorted(os.listdir(ART)):
    if not f.lower().endswith(('.png', '.jpg')):
        continue
    t = unreal.AssetImportTask()
    t.set_editor_property('filename', os.path.join(ART, f))
    t.set_editor_property('destination_path', DEST)
    t.set_editor_property('automated', True)
    t.set_editor_property('replace_existing', True)
    t.set_editor_property('save', True)
    tools.import_asset_tasks([t])

kinds = {}
for p in sorted(lib.list_assets(DEST, recursive=True, include_folder=False)):
    kinds.setdefault(str(lib.find_asset_data(p).asset_class_path.asset_name), []).append(p)
report['kinds'] = {k: v for k, v in kinds.items()}
with open(OUT, 'w') as f:
    json.dump(report, f, indent=1)
unreal.log('ARMOUR IMPORT DONE')
