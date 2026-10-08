# THE ART THIS SCRIPT IMPORTED HAS BEEN DELETED.
#
# The kit it reads from was dropped on judgement, not on licence -- see
# UNREAL-SESSIONS-0-2.md -- and the 261 MB it occupied was removed once
# nothing referenced it. The script is kept because it is the record of
# HOW the art was brought in, and because the pack is CC0 and can be
# fetched again. It will do nothing until it is.
import json, unreal
lib = unreal.EditorAssetLibrary
out = {'fixed': [], 'sizes': []}
for p in lib.list_assets('/Game/Interval/KayKit', recursive=True, include_folder=False):
    d = lib.find_asset_data(p)
    if str(d.asset_class_path.asset_name) != 'Texture2D':
        continue
    t = lib.load_asset(p)
    # A PALETTE ATLAS MUST BE POINT SAMPLED. These packs paint a whole
    # character from a texture a few dozen pixels across: every material on
    # the model is one texel of it. Filtered bilinearly, each texel blends
    # into its neighbours and the entire figure comes out a muddy grey --
    # which looks exactly like a missing texture and is not one.
    t.set_editor_property('filter', unreal.TextureFilter.TF_NEAREST)
    t.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
    lib.save_asset(p, False)
    out['fixed'].append(p.split('/')[-1])
    out['sizes'].append([t.blueprint_get_size_x(), t.blueprint_get_size_y()])
with open(r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/tex.json", 'w') as f: json.dump(out, f, indent=1)
unreal.log('TEX FIXED')
