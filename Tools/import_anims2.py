# THE SECOND ANIMATION LIBRARY, onto the skeleton the first one defined.
#
# Quaternius's Universal Animation Library 2, CC0, forty-three more clips on
# the SAME rig -- sixty-seven bones, every name identical, checked against
# UAL1_Standard.glb before this was written. So nothing retargets: the clips
# land beside the existing ones and every citizen, keeper and corpse in the
# world can play them, because they are all built on that one skeleton.
#
# THE SKELETON IS FOUND, NOT CREATED. Importing a glTF without naming a
# skeleton makes a NEW one, and a clip on a new skeleton will not play on the
# people -- which is the failure import_universal.py's own note describes, and
# it is silent: the assets arrive, the table points at them, and the citizen
# stands still. So this reads the skeleton out of the first library's folder
# and refuses to import at all if it is not there.
#
#   pyrun.sh import_anims2.py
import os, json, unreal

ART  = os.path.abspath(os.path.join(unreal.Paths.project_dir(),
                                    'Art', 'Universal', 'Anims2'))
DEST = '/Game/Interval/Universal/Anims2'
FIRST = '/Game/Interval/Universal/Anims'
OUT  = r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/anims2.json"

tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary
report = {'errors': [], 'clips': [], 'skeleton': None}

skeleton = None
for p in lib.list_assets(FIRST, recursive=True, include_folder=False):
    if str(lib.find_asset_data(p).asset_class_path.asset_name) == 'Skeleton':
        skeleton = lib.load_asset(p)
        report['skeleton'] = str(p)
        break

if skeleton is None:
    report['errors'].append(
        'no skeleton under %s -- run import_universal.py first' % FIRST)
else:
    p = unreal.InterchangeGenericAssetsPipeline()
    mesh = p.get_editor_property('mesh_pipeline')
    mesh.set_editor_property('import_static_meshes', False)
    # THE MESH COMES IN TOO, AND THAT IS NOT A CHOICE. A glTF's animations
    # hang off the SKINNED MESH node, so an import with skeletal meshes turned
    # off brings in the materials, reports success and lands not one clip --
    # which is exactly what the first run of this did. The mannequin arrives
    # beside them, is not in the wardrobe, and nothing draws it.
    mesh.set_editor_property('import_skeletal_meshes', True)
    mesh.set_editor_property('create_physics_asset', False)
    anim = p.get_editor_property('animation_pipeline')
    anim.set_editor_property('import_animations', True)
    common = p.get_editor_property('common_skeletal_meshes_and_animations_properties')
    common.set_editor_property('skeleton', skeleton)

    t = unreal.AssetImportTask()
    t.set_editor_property('filename', os.path.join(ART, 'UAL2_Standard.glb'))
    t.set_editor_property('destination_path', DEST)
    t.set_editor_property('destination_name', 'UAL2')
    t.set_editor_property('automated', True)
    t.set_editor_property('replace_existing', True)
    t.set_editor_property('save', True)
    over = unreal.InterchangePipelineStackOverride()
    over.add_pipeline(p)
    t.set_editor_property('options', over)
    try:
        tools.import_asset_tasks([t])
    except Exception as e:
        report['errors'].append(str(e)[:300])

    for q in sorted(lib.list_assets(DEST, recursive=True, include_folder=False)):
        if str(lib.find_asset_data(q).asset_class_path.asset_name) == 'AnimSequence':
            report['clips'].append(str(q))

with open(OUT, 'w') as f:
    json.dump(report, f, indent=1)
unreal.log('ANIMS2 DONE: %d clips, %d errors'
           % (len(report['clips']), len(report['errors'])))
