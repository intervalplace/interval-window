# The hairstyles, which ship as their own meshes rigged to the head bone. The
# base body carries a face, eyes and eyebrows but no hair, so without these
# every citizen in the world is the same shaven man.
import os, json, unreal

ART  = os.path.abspath(os.path.join(unreal.Paths.project_dir(), 'Art', 'Universal', 'Hair'))
DEST = '/Game/Interval/Universal/Hair'
OUT  = r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/hair.json"

tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary
report = {'errors': [], 'made': {}}

skeleton = lib.load_asset('/Game/Interval/Universal/Anims/UAL_Skeleton.UAL_Skeleton')
if skeleton is None:
    report['errors'].append('no UAL_Skeleton')

def run(path, name):
    if not os.path.exists(path):
        report['errors'].append('missing ' + path); return
    p = unreal.InterchangeGenericAssetsPipeline()
    mesh = p.get_editor_property('mesh_pipeline')
    mesh.set_editor_property('import_static_meshes', False)
    mesh.set_editor_property('import_skeletal_meshes', True)
    mesh.set_editor_property('create_physics_asset', False)
    p.get_editor_property('animation_pipeline').set_editor_property('import_animations', False)
    if skeleton is not None:
        p.get_editor_property('common_skeletal_meshes_and_animations_properties') \
         .set_editor_property('skeleton', skeleton)
    over = unreal.InterchangePipelineStackOverride()
    over.add_pipeline(p)
    t = unreal.AssetImportTask()
    t.set_editor_property('filename', path)
    t.set_editor_property('destination_path', DEST)
    t.set_editor_property('destination_name', name)
    t.set_editor_property('automated', True)
    t.set_editor_property('replace_existing', True)
    t.set_editor_property('save', True)
    t.set_editor_property('options', over)
    tools.import_asset_tasks([t])
    made = [str(x) for x in t.get_editor_property('imported_object_paths')]
    if not made: report['errors'].append('nothing from ' + name)
    report['made'][name] = made

for who in ('Hair_Buzzed', 'Hair_SimpleParted', 'Hair_Long', 'Hair_Beard',
            'Hair_Buns', 'Hair_BuzzedFemale'):
    run(os.path.join(ART, who + '.gltf'), who)

kinds = {}
for p in sorted(lib.list_assets(DEST, recursive=True, include_folder=False)):
    kinds.setdefault(str(lib.find_asset_data(p).asset_class_path.asset_name), []).append(p)
report['kinds'] = kinds
with open(OUT, 'w') as f: json.dump(report, f, indent=1)
unreal.log('HAIR IMPORT DONE')
