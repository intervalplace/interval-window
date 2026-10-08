# HALF OF THIS PACK IS GONE. `Men` and `Women` -- the modern modular
# characters, a hi-vis worker and a business suit among them -- were
# dropped on judgement and deleted. `Weapons` stays: every blade, bow
# and shield a citizen carries is still out of it.
# Imports the CC0 Quaternius modular people. Runs in the editor's own Python,
# because the MCP server has no asset-import tool at all.
#
# The pack is laid out exactly the way this project already builds a citizen:
# one outfit is four skeletal meshes -- Body, Head, Legs, Feet -- sharing a
# single rig, plus one Animations.fbx holding the whole motion set. So a Body
# is imported first to mint the skeleton, everything else is imported against
# that skeleton, and the animations land on it last.
import os, json, unreal

ART  = os.path.abspath(os.path.join(unreal.Paths.project_dir(), 'Art', 'Quaternius'))
DEST = '/Game/Interval/Quaternius'
OUT  = r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/quat.json"

tools = unreal.AssetToolsHelpers.get_asset_tools()
lib   = unreal.EditorAssetLibrary
report = {'imported': [], 'errors': [], 'skeletons': {}, 'anims': [], 'materials': []}


def options(skeleton=None, anim=False):
    ui = unreal.FbxImportUI()
    ui.set_editor_property('import_mesh', not anim)
    ui.set_editor_property('import_as_skeletal', True)
    ui.set_editor_property('import_animations', anim)
    ui.set_editor_property('import_materials', True)
    ui.set_editor_property('import_textures', True)
    ui.set_editor_property('mesh_type_to_import',
                           unreal.FBXImportType.FBXIT_ANIMATION if anim
                           else unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    ui.set_editor_property('create_physics_asset', False)
    if skeleton is not None:
        ui.set_editor_property('skeleton', skeleton)
    sk = ui.get_editor_property('skeletal_mesh_import_data')
    sk.set_editor_property('import_morph_targets', False)
    sk.set_editor_property('convert_scene', True)
    sk.set_editor_property('force_front_x_axis', False)
    an = ui.get_editor_property('anim_sequence_import_data')
    an.set_editor_property('import_meshes_in_bone_hierarchy', False)
    an.set_editor_property('animation_length',
                           unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
    return ui


def run(path, dest, name, skeleton=None, anim=False):
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
    t.set_editor_property('options', options(skeleton, anim))
    tools.import_asset_tasks([t])
    made = [str(p) for p in t.get_editor_property('imported_object_paths')]
    if not made:
        report['errors'].append('nothing from ' + os.path.basename(path))
    report['imported'] += made
    return made


for side in ('Men', 'Women'):
    root = os.path.join(ART, side)
    if not os.path.isdir(root):
        report['errors'].append('no ' + root)
        continue
    outfits = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
    skeleton = None

    for outfit in outfits:
        folder = os.path.join(root, outfit)
        # Body first: its import is what mints the shared skeleton.
        for part in ('Body', 'Head', 'Legs', 'Feet', 'Backpack'):
            fbx = os.path.join(folder, '%s_%s.fbx' % (outfit, part))
            if not os.path.exists(fbx):
                continue
            made = run(fbx, '%s/%s/%s' % (DEST, side, outfit),
                       '%s_%s' % (outfit, part), skeleton)
            if skeleton is None:
                for p in made:
                    a = lib.load_asset(p.split('.')[0] + '.' + p.split('.')[-1]) \
                        if '.' in p else lib.load_asset(p)
                    if isinstance(a, unreal.SkeletalMesh):
                        skeleton = a.get_editor_property('skeleton')
                        report['skeletons'][side] = str(skeleton.get_path_name())

    anims = os.path.join(root, 'Animations.fbx')
    if os.path.exists(anims) and skeleton is not None:
        run(anims, '%s/%s/Anims' % (DEST, side), 'Q', skeleton, anim=True)

# What actually landed, and of what kind -- the importer's own account of it.
kinds = {}
for p in sorted(lib.list_assets(DEST, recursive=True, include_folder=False)):
    d = lib.find_asset_data(p)
    c = str(d.asset_class_path.asset_name)
    kinds.setdefault(c, []).append(p)
report['kinds'] = {k: v for k, v in kinds.items()}
report['anims'] = kinds.get('AnimSequence', [])
report['materials'] = kinds.get('MaterialInstanceConstant', []) + kinds.get('Material', [])

with open(OUT, 'w') as f:
    json.dump(report, f, indent=1)
unreal.log('QUATERNIUS IMPORT DONE')
