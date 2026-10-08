# The CC0 Fantasy Props MegaKit, as static meshes.
#
# Most of the furniture of this world is currently a scaled cube: the world
# says `anvil`, `barrel`, `bed`, `table`, `bench`, `cart`, `banner`, `brewpot`,
# and each of them is drawn as a box of about the right size. This pack has the
# real thing for nearly all of them, and -- the reason it was fetched -- a
# PICKAXE and a TORCH, which are words the world uses for tools and which no
# weapon pack had.
import os, json, unreal

ART  = os.path.abspath(os.path.join(unreal.Paths.project_dir(), 'Art', 'Props'))
DEST = '/Game/Interval/Props'
OUT  = r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/props.json"

tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary
report = {'errors': [], 'made': 0}

def pipeline():
    p = unreal.InterchangeGenericAssetsPipeline()
    mesh = p.get_editor_property('mesh_pipeline')
    mesh.set_editor_property('import_static_meshes', True)
    mesh.set_editor_property('import_skeletal_meshes', False)
    # Nothing is said about combining: each file holds ONE mesh with two
    # material slots, bark and leaves, so the default already does the right
    # thing. (`combine_static_meshes` is deprecated in 5.8 and its replacement
    # enum is not exposed to Python under any name `unreal` will admit to.)
    p.get_editor_property('animation_pipeline').set_editor_property('import_animations', False)
    return p

tasks = []
for f in sorted(os.listdir(ART)):
    if not f.endswith('.gltf'):
        continue
    t = unreal.AssetImportTask()
    t.set_editor_property('filename', os.path.join(ART, f))
    t.set_editor_property('destination_path', DEST)
    t.set_editor_property('destination_name', os.path.splitext(f)[0])
    t.set_editor_property('automated', True)
    t.set_editor_property('replace_existing', True)
    t.set_editor_property('save', True)
    over = unreal.InterchangePipelineStackOverride()
    over.add_pipeline(pipeline())
    t.set_editor_property('options', over)
    tasks.append(t)

# One call: sixty-eight separate imports each pay the Interchange start-up.
tools.import_asset_tasks(tasks)

kinds = {}
for p in sorted(lib.list_assets(DEST, recursive=True, include_folder=False)):
    kinds.setdefault(str(lib.find_asset_data(p).asset_class_path.asset_name), []).append(p)
report['kinds'] = {k: len(v) for k, v in kinds.items()}
report['meshes'] = kinds.get('StaticMesh', [])
report['materials'] = kinds.get('Material', []) + kinds.get('MaterialInstanceConstant', [])
report['textures'] = kinds.get('Texture2D', [])
with open(OUT, 'w') as f:
    json.dump(report, f, indent=1)
unreal.log('PROPS IMPORT DONE')
