# THE ART THIS SCRIPT IMPORTED HAS BEEN DELETED.
#
# The kit it reads from was dropped on judgement, not on licence -- see
# UNREAL-SESSIONS-0-2.md -- and the 261 MB it occupied was removed once
# nothing referenced it. The script is kept because it is the record of
# HOW the art was brought in, and because the pack is CC0 and can be
# fetched again. It will do nothing until it is.
import json, unreal
lib = unreal.EditorAssetLibrary
out = {'parts': [], 'anims': {}, 'kit': [], 'mobparts': []}
WANT = ['Idle', 'Walking_A', '1H_Melee_Attack_Chop', '1H_Melee_Attack_Slice_Diagonal',
        '1H_Melee_Attack_Stab', 'Death_A', 'PickUp', 'Use_Item', 'Spellcast_Raise',
        'Running_A', 'Throw', 'Interact', 'Unarmed_Idle', '2H_Melee_Attack_Chop']
for p in lib.list_assets('/Game/Interval/KayKit/People/Rogue_Hooded', recursive=True, include_folder=False):
    d = lib.find_asset_data(p); cls = str(d.asset_class_path.asset_name)
    n = p.split('.')[-1]
    if cls == 'SkeletalMesh': out['parts'].append(p)
    elif cls == 'AnimSequence':
        for w in WANT:
            if n == 'RogueHooded' + w: out['anims'][w] = p
for p in lib.list_assets('/Game/Interval/KayKit/People/Skeleton_Warrior', recursive=True, include_folder=False):
    d = lib.find_asset_data(p)
    if str(d.asset_class_path.asset_name) == 'SkeletalMesh': out['mobparts'].append(p)
for p in lib.list_assets('/Game/Interval/KayKit/Kit', recursive=True, include_folder=False):
    d = lib.find_asset_data(p)
    if str(d.asset_class_path.asset_name) == 'StaticMesh': out['kit'].append(p)
with open(r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/paths.json", 'w') as f: json.dump(out, f, indent=1)
unreal.log('PATHS WRITTEN')
