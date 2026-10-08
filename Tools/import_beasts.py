# The CC0 bestiary, as skeletal meshes with their own animations.
#
# Twenty-one of this world's twenty-two drawn mobs were an ENGINE CYLINDER with
# a tinted material: a goblin was a green cylinder, a wolf a brown cube, a
# dragon a big box. Every one of them counted as "drawn" by any test that only
# asks whether a row exists, which is how a bestiary of twenty-four can look
# finished and read as a car park.
import os, json, unreal

ART  = os.path.abspath(os.path.join(unreal.Paths.project_dir(), 'Art', 'Beasts'))
DEST = '/Game/Interval/Beasts'
OUT  = r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/beasts.json"

tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary
report = {'errors': [], 'made': {}}

def options():
    ui = unreal.FbxImportUI()
    ui.set_editor_property('import_mesh', True)
    ui.set_editor_property('import_as_skeletal', True)
    ui.set_editor_property('import_animations', True)
    ui.set_editor_property('import_materials', True)
    ui.set_editor_property('import_textures', True)
    ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    ui.set_editor_property('create_physics_asset', False)
    sk = ui.get_editor_property('skeletal_mesh_import_data')
    sk.set_editor_property('import_morph_targets', False)
    sk.set_editor_property('convert_scene', True)
    an = ui.get_editor_property('anim_sequence_import_data')
    an.set_editor_property('import_meshes_in_bone_hierarchy', False)
    an.set_editor_property('animation_length',
                           unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
    return ui

# Every beast brings its OWN skeleton. They are different animals; a wolf's
# spine is not a spider's, and nothing here wants to share a rig between them.
tasks = []
for f in sorted(os.listdir(ART)):
    if not f.lower().endswith('.fbx'):
        continue
    name = os.path.splitext(f)[0].replace(' ', '_')
    t = unreal.AssetImportTask()
    t.set_editor_property('filename', os.path.join(ART, f))
    t.set_editor_property('destination_path', DEST + '/' + name)
    t.set_editor_property('destination_name', name)
    t.set_editor_property('automated', True)
    t.set_editor_property('replace_existing', True)
    t.set_editor_property('save', True)
    t.set_editor_property('options', options())
    tasks.append(t)
tools.import_asset_tasks(tasks)

kinds = {}
for p in sorted(lib.list_assets(DEST, recursive=True, include_folder=False)):
    kinds.setdefault(str(lib.find_asset_data(p).asset_class_path.asset_name), []).append(p)
report['kinds'] = {k: len(v) for k, v in kinds.items()}
report['meshes'] = kinds.get('SkeletalMesh', [])
report['materials'] = kinds.get('MaterialInstanceConstant', []) + kinds.get('Material', [])
report['anims'] = kinds.get('AnimSequence', [])
with open(OUT, 'w') as f:
    json.dump(report, f, indent=1)
unreal.log('BEASTS IMPORT DONE')
