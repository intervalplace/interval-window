# THE ART THIS SCRIPT IMPORTED HAS BEEN DELETED.
#
# The kit it reads from was dropped on judgement, not on licence -- see
# UNREAL-SESSIONS-0-2.md -- and the 261 MB it occupied was removed once
# nothing referenced it. The script is kept because it is the record of
# HOW the art was brought in, and because the pack is CC0 and can be
# fetched again. It will do nothing until it is.
import json, unreal
OUT = r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/merged.json"
lib = unreal.EditorAssetLibrary
ROOT = '/Game/Interval/KayKit/People'
DEST = '/Game/Interval/KayKit/Folk'
out = {}

for folder, name in (('Rogue_Hooded', 'Villager'), ('Knight', 'Knight'),
                     ('Barbarian', 'Barbarian'),
                     ('Skeleton_Warrior', 'SkeletonWarrior'),
                     ('Skeleton_Minion', 'SkeletonMinion'),
                     ('Skeleton_Rogue', 'SkeletonRogue')):
    base = ROOT + '/' + folder
    if not lib.does_directory_exist(base):
        out[name] = 'no folder'; continue
    meshes, skel = [], None
    for p in lib.list_assets(base, recursive=True, include_folder=False):
        d = lib.find_asset_data(p)
        cls = str(d.asset_class_path.asset_name)
        if cls == 'SkeletalMesh':
            meshes.append(lib.load_asset(p))
        elif cls == 'Skeleton' and skel is None:
            skel = lib.load_asset(p)
    # A CAPE ON A VILLAGER IS A CLOAK ON EVERY VILLAGER. Left out; the ones who
    # should have one can have it hung on a bone like any other garment.
    meshes = [m for m in meshes if 'Cape' not in m.get_name()]
    try:
        params = unreal.SkeletalMeshMergeParams()
        params.set_editor_property('meshes_to_merge', meshes)
        params.set_editor_property('skeleton', skel)
        merged = unreal.SkeletalMergingLibrary.merge_meshes(params)
        if merged:
            # The merge hands back a TRANSIENT mesh -- it exists only in memory
            # and renaming it into a package fails. Duplicating it makes a real
            # asset in a real package, which is the thing worth keeping.
            path = DEST + '/' + name
            dup = lib.duplicate_loaded_asset(merged, path)
            if dup:
                lib.save_asset(path, False)
            out[name] = {'merged': path if dup else None,
                         'parts': [m.get_name() for m in meshes],
                         'skeleton': skel.get_path_name() if skel else None}
        else:
            out[name] = 'merge returned nothing'
    except Exception as e:
        out[name] = 'error: ' + str(e)[:200]

with open(OUT, 'w') as f:
    json.dump(out, f, indent=1)
unreal.log('MERGE DONE')
