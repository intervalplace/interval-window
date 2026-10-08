# The three that carry no rig.
#
# `import_wild.py` asks Interchange for skeletal meshes and gets nothing from
# these -- a raven, a mermaid and a fourth goblin came in as TEXTURES and no
# mesh at all, which looks like a failed import and is not: the .glb has no
# skin in it. They are static, so they are imported as static, and a crow
# perched on a gibbet does not need a rig anyway.
import os, json, unreal

ART  = os.path.abspath(os.path.join(unreal.Paths.project_dir(), 'Art', 'WildStatic'))
DEST = '/Game/Interval/Wild'
OUT  = r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/wildstatic.json"

tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary


def pipeline():
    p = unreal.InterchangeGenericAssetsPipeline()
    mesh = p.get_editor_property('mesh_pipeline')
    mesh.set_editor_property('import_static_meshes', True)
    mesh.set_editor_property('import_skeletal_meshes', False)
    p.get_editor_property('animation_pipeline').set_editor_property('import_animations', False)
    return p


tasks = []
for f in sorted(os.listdir(ART)):
    # .obj TOO. The white bear is CC0 and ships only as a `.blend`, which
    # Unreal cannot read without Blender installed -- so it is converted here
    # by Tools/blendmesh.py, which reads the .blend's own struct catalogue, and
    # arrives as a Wavefront .obj. Interchange takes that happily.
    if not (f.endswith('.glb') or f.endswith('.obj')):
        continue
    name = os.path.splitext(f)[0]
    t = unreal.AssetImportTask()
    t.set_editor_property('filename', os.path.join(ART, f))
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
with open(OUT, 'w') as f:
    json.dump({'static': kinds.get('StaticMesh', [])}, f, indent=1)
unreal.log('WILD STATIC IMPORT DONE')
