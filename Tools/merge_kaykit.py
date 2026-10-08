# THE ART THIS SCRIPT IMPORTED HAS BEEN DELETED.
#
# The kit it reads from was dropped on judgement, not on licence -- see
# UNREAL-SESSIONS-0-2.md -- and the 261 MB it occupied was removed once
# nothing referenced it. The script is kept because it is the record of
# HOW the art was brought in, and because the pack is CC0 and can be
# fetched again. It will do nothing until it is.
# KayKit characters are MODULAR: a body, two arms, two legs, a head, a cape,
# each imported as its own skeletal mesh with its own skeleton. Animating them
# together needs one shared skeleton; drawing them as one thing needs a merge.
#
# NOTE ON OUTPUT: print() is swallowed when the editor runs as a commandlet, so
# anything worth knowing is written to a file. An hour went into wondering why
# a script that "executed successfully" had said nothing at all.
import json, unreal

OUT = r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/kaykit.json"
lib = unreal.EditorAssetLibrary
ROOT = '/Game/Interval/KayKit/People'
report = {}

for folder in ('Rogue_Hooded', 'Knight', 'Barbarian',
               'Skeleton_Warrior', 'Skeleton_Minion', 'Skeleton_Rogue'):
    base = ROOT + '/' + folder
    entry = {'exists': lib.does_directory_exist(base),
             'meshes': [], 'skeletons': [], 'anims': 0, 'anim_skeletons': []}
    if entry['exists']:
        for p in lib.list_assets(base, recursive=True, include_folder=False):
            d = lib.find_asset_data(p)
            cls = str(d.asset_class_path.asset_name)
            if cls == 'SkeletalMesh':
                entry['meshes'].append(p)
            elif cls == 'Skeleton':
                entry['skeletons'].append(p)
            elif cls == 'AnimSequence':
                entry['anims'] += 1
                if len(entry['anim_skeletons']) < 3:
                    a = lib.load_asset(p)
                    sk = a.get_editor_property('skeleton')
                    entry['anim_skeletons'].append(sk.get_path_name() if sk else None)
    report[folder] = entry

with open(OUT, 'w') as f:
    json.dump(report, f, indent=1)
unreal.log('KAYKIT REPORT WRITTEN')
