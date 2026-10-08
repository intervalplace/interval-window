# THE ART THIS SCRIPT IMPORTED HAS BEEN DELETED.
#
# The kit it reads from was dropped on judgement, not on licence -- see
# UNREAL-SESSIONS-0-2.md -- and the 261 MB it occupied was removed once
# nothing referenced it. The script is kept because it is the record of
# HOW the art was brought in, and because the pack is CC0 and can be
# fetched again. It will do nothing until it is.
# Imports the CC0 KayKit art. Runs inside the editor's own Python, because
# there is no sound- or glTF-import tool on the MCP server.
import os, unreal

ART = os.path.join(unreal.Paths.project_dir(), 'Art', 'KayKit')
ART = os.path.abspath(ART)

def find(*parts):
    for root, _dirs, files in os.walk(ART):
        for f in files:
            p = os.path.join(root, f)
            if all(s.lower() in p.lower() for s in parts):
                return p
    return None

tasks = []
def add(path, dest, name):
    if not path or not os.path.exists(path):
        print('MISSING', name)
        return
    t = unreal.AssetImportTask()
    t.filename = path
    t.destination_path = dest
    t.destination_name = name
    t.automated = True
    t.replace_existing = True
    t.save = True
    tasks.append(t)

# The people, with their animations: a hooded figure for the common citizen,
# a knight for anybody in plate, and a skeleton for what walks at night.
for who, glb in (('RogueHooded', 'Rogue_Hooded.glb'),
                 ('Knight', 'Knight.glb'),
                 ('Rogue', 'Rogue.glb'),
                 ('Barbarian', 'Barbarian.glb'),
                 ('SkeletonWarrior', 'Skeleton_Warrior.glb'),
                 ('SkeletonMinion', 'Skeleton_Minion.glb')):
    add(find(glb), '/Game/Interval/KayKit/People', who)

# What they carry. Static meshes, one per thing the world has a word for.
WEAPONS = ['sword_1handed', 'sword_2handed', 'dagger', 'axe_1handed', 'axe_2handed',
           'staff', 'wand', 'crossbow_1handed', 'crossbow_2handed', 'quiver', 'arrow',
           'shield_round', 'shield_square', 'shield_spikes', 'shield_badge']
for w in WEAPONS:
    add(find('assets', 'gltf', w + '.gltf'), '/Game/Interval/KayKit/Kit', w)

print('importing', len(tasks))
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

lib = unreal.EditorAssetLibrary
made = 0
for t in tasks:
    for folder in (t.destination_path,):
        for a in lib.list_assets(folder, recursive=True, include_folder=False):
            made += 1
print('ASSETS NOW', made)
for a in sorted(set(lib.list_assets('/Game/Interval/KayKit', recursive=True, include_folder=False)))[:40]:
    print('  ', a)
