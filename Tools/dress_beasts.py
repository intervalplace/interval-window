# Re-parents the bestiary's materials onto M_IntervalFlat.
#
# The FBX importer parents them to the engine's legacy Phong template, which
# carries the artist's colour under `DiffuseColor`. M_IntervalFlat asks for a
# parameter of exactly that name, so re-parenting keeps every colour without
# anything having to copy one -- the same trick the modular people used.
#
# `Strength` is nothing: a wolf is the colour a wolf is, and the per-citizen
# dye has no business on an animal.
import json, unreal

DEST = '/Game/Interval/Beasts'
FLAT = '/Game/Interval/Materials/M_IntervalFlat.M_IntervalFlat'
OUT = r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/dressbeasts.json"

lib = unreal.EditorAssetLibrary
flat = lib.load_asset(FLAT)
report = {'errors': [], 'done': 0}
if flat is None:
    report['errors'].append('no M_IntervalFlat')
else:
    for p in sorted(lib.list_assets(DEST, recursive=True, include_folder=False)):
        if str(lib.find_asset_data(p).asset_class_path.asset_name) != 'MaterialInstanceConstant':
            continue
        mi = lib.load_asset(p)
        mi.set_editor_property('parent', flat)
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            mi, 'Strength', 0.0)
        lib.save_asset(p, False)
        report['done'] += 1
with open(OUT, 'w') as f:
    json.dump(report, f, indent=1)
unreal.log('BEASTS DRESSED')
