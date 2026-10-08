# THE ART THIS SCRIPT IMPORTED HAS BEEN DELETED.
#
# The kit it reads from was dropped on judgement, not on licence -- see
# UNREAL-SESSIONS-0-2.md -- and the 261 MB it occupied was removed once
# nothing referenced it. The script is kept because it is the record of
# HOW the art was brought in, and because the pack is CC0 and can be
# fetched again. It will do nothing until it is.
import json, unreal
lib = unreal.EditorAssetLibrary
out = {}
m = lib.load_asset('/Game/Interval/KayKit/People/Rogue_Hooded/SkeletalMeshes/Rogue_Body.Rogue_Body')
mats = m.get_editor_property('materials')
out['slots'] = []
for s in mats:
    mi = s.get_editor_property('material_interface')
    out['slots'].append(mi.get_path_name() if mi else None)
# what textures came in
out['assets'] = [p for p in lib.list_assets('/Game/Interval/KayKit/People/Rogue_Hooded',
                 recursive=True, include_folder=False)
                 if 'Material' in str(lib.find_asset_data(p).asset_class_path.asset_name)
                 or 'Texture' in str(lib.find_asset_data(p).asset_class_path.asset_name)]
# bounds, for the scale question
b = m.get_bounds()
out['extent'] = [b.box_extent.x, b.box_extent.y, b.box_extent.z]
with open(r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/mat.json", 'w') as f: json.dump(out, f, indent=1)
unreal.log('MAT WRITTEN')
