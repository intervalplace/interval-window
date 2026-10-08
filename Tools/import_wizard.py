# THE WIZARD, and the rest of Quaternius' RPG characters.
#
# Oberon stands in a ring of eight standing stones beside his own hearth and was
# drawn as a cylinder with a cone on it, then as a peasant in a ranger's hood.
# Neither is a wizard, which is a thing somebody watching said out loud.
#
# CC0, read from the author's own page and from OpenGameArt -- see
# Art/RPGCharacters/LICENCE.txt, which also records why the Modular Fantasy
# Outfits pack was NOT used (its wizard is behind a paid tier) and why the Poly
# Pizza listing of the same author's wizard was not trusted (that site labels it
# CC BY; the author releases CC0).
#
# THESE ARE NOT ON THE UNIVERSAL SKELETON. The citizens share UAL_Skeleton and
# retarget one animation library across every outfit; this pack is its own rig
# with its own clips. So it is imported WITHOUT being forced onto that skeleton
# -- forcing it would silently mangle the bind pose -- and it keeps its own.
# A keeper stands still, so what it mostly needs is to exist and to idle.
import os, json, unreal

ART  = os.path.abspath(os.path.join(unreal.Paths.project_dir(), 'Art', 'RPGCharacters',
                                    'RPG Characters - Nov 2020'))
DEST = '/Game/Interval/Folk'
OUT  = r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/wizard.json"

tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary
report = {'errors': [], 'made': {}}

def run(path, dest, name, skeletal=True, anims=True):
    if not os.path.exists(path):
        report['errors'].append('missing ' + path); return []
    p = unreal.InterchangeGenericAssetsPipeline()
    mesh = p.get_editor_property('mesh_pipeline')
    mesh.set_editor_property('import_static_meshes', not skeletal)
    mesh.set_editor_property('import_skeletal_meshes', skeletal)
    mesh.set_editor_property('create_physics_asset', False)
    p.get_editor_property('animation_pipeline').set_editor_property('import_animations', anims)
    over = unreal.InterchangePipelineStackOverride()
    over.add_pipeline(p)
    t = unreal.AssetImportTask()
    t.set_editor_property('filename', path)
    t.set_editor_property('destination_path', dest)
    t.set_editor_property('destination_name', name)
    t.set_editor_property('automated', True)
    t.set_editor_property('replace_existing', True)
    t.set_editor_property('save', True)
    t.set_editor_property('options', over)
    tools.import_asset_tasks([t])
    made = [str(x) for x in t.get_editor_property('imported_object_paths')]
    if not made: report['errors'].append('nothing from ' + name)
    report['made'][name] = made
    return made

# The wizard first, and the cleric with him: a mourner in a robe is a better
# mourner than a peasant in a pointed hat, and the pack has one already.
for who in ('Wizard', 'Cleric', 'Monk'):
    run(os.path.join(ART, 'FBX', who + '.fbx'), DEST, who)
run(os.path.join(ART, 'FBX', 'Only Weapons', 'Wizard_Staff.fbx'),
    DEST, 'Wizard_Staff', skeletal=False, anims=False)

for tex in ('Wizard_Texture', 'Cleric_Texture', 'Monk_Texture', 'Wizard_Staff_Texture'):
    run(os.path.join(ART, 'Textures', tex + '.png'), DEST + '/Textures', tex,
        skeletal=False, anims=False)

kinds = {}
for p in sorted(lib.list_assets(DEST, recursive=True, include_folder=False)):
    kinds.setdefault(str(lib.find_asset_data(p).asset_class_path.asset_name), []).append(p)
report['kinds'] = kinds
with open(OUT, 'w') as f: json.dump(report, f, indent=1)
unreal.log('WIZARD IMPORT DONE')
