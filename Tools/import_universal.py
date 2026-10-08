# Imports the CC0 "Universal" people: four fantasy outfits and the shared
# animation library, all on ONE rig.
#
# glTF goes through Interchange, not the old FBX importer, so the skeleton is
# named on a pipeline object rather than on an FbxImportUI. The animation
# library is imported FIRST and its skeleton is the one everybody else joins,
# because it is the file that defines what the motions are rigged to -- doing
# it the other way round gives four skeletons and no animation that will play
# on any of them.
import os, json, unreal

ART  = os.path.abspath(os.path.join(unreal.Paths.project_dir(), 'Art', 'Universal'))
DEST = '/Game/Interval/Universal'
OUT  = r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/uni.json"

tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary
report = {'errors': [], 'made': {}, 'skeleton': None}


def pipeline(skeleton=None, meshes=True, anims=True):
    p = unreal.InterchangeGenericAssetsPipeline()
    mesh = p.get_editor_property('mesh_pipeline')
    mesh.set_editor_property('bImportStaticMeshes' if False else 'import_static_meshes', False)
    mesh.set_editor_property('import_skeletal_meshes', meshes)
    mesh.set_editor_property('create_physics_asset', False)
    anim = p.get_editor_property('animation_pipeline')
    anim.set_editor_property('import_animations', anims)
    common = p.get_editor_property('common_skeletal_meshes_and_animations_properties')
    if skeleton is not None:
        common.set_editor_property('skeleton', skeleton)
    return p


def run(path, dest, name, skeleton=None, meshes=True, anims=True):
    if not os.path.exists(path):
        report['errors'].append('missing ' + path)
        return []
    t = unreal.AssetImportTask()
    t.set_editor_property('filename', path)
    t.set_editor_property('destination_path', dest)
    t.set_editor_property('destination_name', name)
    t.set_editor_property('automated', True)
    t.set_editor_property('replace_existing', True)
    t.set_editor_property('save', True)
    over = unreal.InterchangePipelineStackOverride()
    over.add_pipeline(pipeline(skeleton, meshes, anims))
    t.set_editor_property('options', over)
    try:
        tools.import_asset_tasks([t])
    except Exception as e:
        report['errors'].append('%s: %s' % (name, str(e)[:200]))
        return []
    made = [str(p) for p in t.get_editor_property('imported_object_paths')]
    if not made:
        report['errors'].append('nothing from ' + os.path.basename(path))
    report['made'][name] = made
    return made


# 1. The motions, and with them the skeleton everybody shares.
run(os.path.join(ART, 'Anims', 'UAL1_Standard.glb'), DEST + '/Anims', 'UAL')

skeleton = None
for p in lib.list_assets(DEST + '/Anims', recursive=True, include_folder=False):
    if str(lib.find_asset_data(p).asset_class_path.asset_name) == 'Skeleton':
        skeleton = lib.load_asset(p)
        report['skeleton'] = p
        break
if skeleton is None:
    report['errors'].append('no skeleton came out of the animation library')

# 2. The people, joined to it.
# THE OTHER EIGHT, from the paid Source tier of the same CC0 pack.
#
# The free tier is Ranger and Peasant only -- which is why this window had four
# outfits and no robe, and why fourteen keeper trades were all wearing the same
# peasant shirt. Same kit, same base characters, same skeleton, so they join the
# animation library exactly as the first four did.
for who in ('Male_Peasant', 'Female_Peasant', 'Male_Ranger', 'Female_Ranger',
            'Male_Wizard', 'Female_Wizard', 'Male_Noble', 'Female_Noble',
            'Male_Knight', 'Female_Knight',
            'Male_Knight_Cloth', 'Female_Knight_Cloth'):
    run(os.path.join(ART, 'Whole', who + '.gltf'), DEST + '/People', who,
        skeleton, meshes=True, anims=False)

kinds = {}
for p in sorted(lib.list_assets(DEST, recursive=True, include_folder=False)):
    c = str(lib.find_asset_data(p).asset_class_path.asset_name)
    kinds.setdefault(c, []).append(p)
report['kinds'] = kinds

with open(OUT, 'w') as f:
    json.dump(report, f, indent=1)
unreal.log('UNIVERSAL IMPORT DONE')
