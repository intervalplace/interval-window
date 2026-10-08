# THE ART THIS SCRIPT IMPORTED HAS BEEN DELETED.
#
# The kit it reads from was dropped on judgement, not on licence -- see
# UNREAL-SESSIONS-0-2.md -- and the 261 MB it occupied was removed once
# nothing referenced it. The script is kept because it is the record of
# HOW the art was brought in, and because the pack is CC0 and can be
# fetched again. It will do nothing until it is.
import json, unreal
lib = unreal.EditorAssetLibrary
folk = lib.load_asset('/Game/Interval/Materials/M_IntervalFolk.M_IntervalFolk')
out = {'reparented': [], 'skipped': []}
for p in lib.list_assets('/Game/Interval/KayKit', recursive=True, include_folder=False):
    d = lib.find_asset_data(p)
    if str(d.asset_class_path.asset_name) != 'MaterialInstanceConstant':
        continue
    mi = lib.load_asset(p)
    par = mi.get_editor_property('parent')
    name = par.get_name() if par else '?'
    mi.set_editor_property('parent', folk)
    lib.save_asset(p, False)
    out['reparented'].append([p.split('/')[-1], name])
with open(r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/reparent.json", 'w') as f: json.dump(out, f, indent=1)
unreal.log('REPARENTED')
