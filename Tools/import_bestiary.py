# THE UNDEAD, AND THE OTHER THINGS IN THE DARK.
#
# `skeleton-knight` and `barrow-wight` had no art at all: the first was an
# engine primitive and the second was a drained citizen. This pack has two
# skeletons, a werewolf, a demon knight and a troll.
#
# LICENCE: Quaternius Asset License v1.0, NOT CC0 -- see Art/Bestiary/
# LICENCE-NOTE.txt. Incorporating them into this window is expressly permitted;
# redistributing the raw files is not.
#
# The GLB export is the one marked "(Godot-Unreal)". These are their own rigs
# with their own clips, like the wild beasts, so nothing is forced onto the
# citizens' skeleton.
import os, json, unreal

ART  = os.path.join(unreal.Paths.project_dir(), 'Art', 'Bestiary',
                    'Bestiary - Dungeon Monsters Kit[Source]')
GLB  = os.path.join(ART, 'Exports', 'GLB (Godot-Unreal)')
TEX  = os.path.join(ART, 'Textures')
DEST = '/Game/Interval/Dark'
OUT  = r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/bestiary.json"

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
    over = unreal.InterchangePipelineStackOverride(); over.add_pipeline(p)
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

for who in ('Skeleton_A', 'Skeleton_B', 'Lycan', 'Hellwarden', 'Tidebreaker'):
    run(os.path.join(GLB, who + '.glb'), DEST, who)

if os.path.isdir(TEX):
    for f in sorted(os.listdir(TEX)):
        if f.lower().endswith('.png') and not f.startswith(('Exporting', 'Importing')):
            run(os.path.join(TEX, f), DEST + '/Textures', f[:-4], skeletal=False, anims=False)

kinds = {}
for p in sorted(lib.list_assets(DEST, recursive=True, include_folder=False)):
    kinds.setdefault(str(lib.find_asset_data(p).asset_class_path.asset_name), []).append(p)
report['kinds'] = kinds
with open(OUT, 'w') as f: json.dump(report, f, indent=1)
unreal.log('BESTIARY IMPORT DONE')
