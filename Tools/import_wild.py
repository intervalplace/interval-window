# The wild bestiary, as animated skeletal meshes.
#
# Ten of this world's mobs were an engine primitive with a tinted material on
# it -- a wolf was a brown cube, a goblin a green cylinder -- because the CC0
# packs that have them are genuinely hard to reach. See Tools/polypizza.py for
# the four routes tried and the one that worked; every file here is CC0 by
# Quaternius, with the licence read off its own page.
#
# SKELETAL, AND WITH THE ANIMATIONS. These .glb files carry a rig and a dozen
# clips each, which is the whole reason for taking them over a static mesh: a
# wolf that does not move is a statue of a wolf. The animations land beside the
# mesh and the window's motion table can name them.
import os, json, unreal

ART  = os.path.abspath(os.path.join(unreal.Paths.project_dir(), 'Art', 'Wild'))
DEST = '/Game/Interval/Wild'
OUT  = r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/wild.json"

tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary
report = {'errors': []}


def pipeline():
    p = unreal.InterchangeGenericAssetsPipeline()
    mesh = p.get_editor_property('mesh_pipeline')
    mesh.set_editor_property('import_static_meshes', False)
    mesh.set_editor_property('import_skeletal_meshes', True)
    # (`combine_skeletal_meshes` does not exist on this pipeline in 5.8 --
    #  the property is gone and nothing in `unreal` answers to it. Each file
    #  holds one creature anyway, so there is nothing to combine.)
    anim = p.get_editor_property('animation_pipeline')
    anim.set_editor_property('import_animations', True)
    return p


tasks = []
for f in sorted(os.listdir(ART)):
    # .gltf AS WELL AS .glb. Quaternius ships the Ultimate Animated Animals
    # pack as self-contained `.gltf` -- one JSON file with its buffers inlined
    # as data URIs -- where the older packs came as `.glb`. They are the same
    # format in two containers and Interchange reads both; refusing one of them
    # meant a model could be fetched, sit in the folder, and never arrive.
    if not (f.endswith('.glb') or f.endswith('.gltf')):
        continue
    name = os.path.splitext(f)[0]
    t = unreal.AssetImportTask()
    t.set_editor_property('filename', os.path.join(ART, f))
    # A FOLDER EACH. Every one of these brings a skeleton, a physics asset, a
    # material and a dozen animations with the same names -- `Idle`, `Walk`,
    # `Attack` -- and dropping them all in one folder means eleven creatures
    # fighting over the word `Idle`.
    t.set_editor_property('destination_path', DEST + '/' + name)
    t.set_editor_property('destination_name', name)
    t.set_editor_property('automated', True)
    t.set_editor_property('replace_existing', True)
    t.set_editor_property('save', True)
    over = unreal.InterchangePipelineStackOverride()
    over.add_pipeline(pipeline())
    t.set_editor_property('options', over)
    tasks.append(t)

tools.import_asset_tasks(tasks)

kinds = {}
for p in sorted(lib.list_assets(DEST, recursive=True, include_folder=False)):
    kinds.setdefault(str(lib.find_asset_data(p).asset_class_path.asset_name), []).append(p)
report['kinds'] = {k: len(v) for k, v in kinds.items()}
report['skeletal'] = kinds.get('SkeletalMesh', [])
report['anims'] = kinds.get('AnimSequence', [])
with open(OUT, 'w') as f:
    json.dump(report, f, indent=1)
unreal.log('WILD IMPORT DONE')
