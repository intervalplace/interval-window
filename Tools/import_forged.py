# The meshes this project forged for itself, as static meshes.
#
# `Tools/make_art.py` writes OBJ into Art/Forged for the ten words no CC0 kit
# had anything for. They come in exactly the way the CC0 armour does -- static,
# with the flat materials their .mtl names -- and the only thing worth saying
# about the import is `convert_scene`, which is what turns an OBJ's Y-up into
# Unreal's Z-up. The forge writes Z-up already, so it is OFF here; with it on,
# every mask arrived lying on its back, which is the same lying-down the CC0
# .obj armour does and the reason that flag exists at all.
import os, json, unreal

ART = os.path.abspath(os.path.join(unreal.Paths.project_dir(), 'Art', 'Forged'))
DEST = '/Game/Interval/Forged'
OUT = (r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/"
       r"d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/forged.json")

tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary
report = {'errors': [], 'meshes': []}


def options():
    ui = unreal.FbxImportUI()
    ui.set_editor_property('import_mesh', True)
    ui.set_editor_property('import_as_skeletal', False)
    ui.set_editor_property('import_animations', False)
    # FALSE, AND THE ORDER MATTERS. `dress_forged.py` builds the material
    # instances against this project's own master before this runs; with
    # this True the importer makes its own alongside them and the mesh
    # binds to whichever survives, which the first time round was neither
    # -- every slot came out None and every forged piece was grey.
    ui.set_editor_property('import_materials', False)
    ui.set_editor_property('import_textures', False)
    ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_STATIC_MESH)
    sm = ui.get_editor_property('static_mesh_import_data')
    sm.set_editor_property('combine_meshes', True)
    # Z-UP ALREADY. See the note at the top.
    sm.set_editor_property('convert_scene', False)
    sm.set_editor_property('generate_lightmap_u_vs', False)
    return ui


tasks = []
if not os.path.isdir(ART):
    report['errors'].append('no Art/Forged -- run Tools/make_art.py first')
else:
    for f in sorted(os.listdir(ART)):
        if not f.lower().endswith('.obj'):
            continue
        t = unreal.AssetImportTask()
        t.set_editor_property('filename', os.path.join(ART, f))
        t.set_editor_property('destination_path', DEST)
        t.set_editor_property('destination_name', os.path.splitext(f)[0])
        t.set_editor_property('automated', True)
        t.set_editor_property('replace_existing', True)
        t.set_editor_property('save', True)
        t.set_editor_property('options', options())
        tasks.append(t)
    tools.import_asset_tasks(tasks)

# MEASURED ON THE WAY IN, like the packs. A forged mesh has less excuse than a
# fetched one for being the wrong size -- its dimensions were chosen in
# make_art.py -- so this is really checking that nothing was lost or rotated
# between writing the OBJ and Unreal reading it.
for p in sorted(lib.list_assets(DEST, recursive=True, include_folder=False)):
    data = lib.find_asset_data(p)
    if str(data.asset_class_path.asset_name) != 'StaticMesh':
        continue
    mesh = lib.load_asset(p)
    b = mesh.get_bounding_box()
    s = b.max - b.min
    report['meshes'].append({
        'path': p, 'name': p.rsplit('/', 1)[-1],
        'cm': [round(s.x, 1), round(s.y, 1), round(s.z, 1)],
        'slots': [str(x.material_slot_name) for x in mesh.static_materials]})

with open(OUT, 'w') as f:
    json.dump(report, f, indent=1)
unreal.log('FORGED IMPORT DONE: %d meshes' % len(report['meshes']))
