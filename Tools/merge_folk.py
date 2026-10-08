# ONE MESH PER PERSON, so a keeper can be a person.
#
# A citizen is two skeletal meshes -- the bare body, which carries the head and
# the hands, and the outfit over it. That is fine for a citizen, which is built
# out of components at runtime, and no good at all for a PROP: a prop kind
# holds one skeletal mesh, so a keeper wired to an outfit is a headless shop-
# keeper and one wired to the base body is a naked one.
#
# Unreal will merge two meshes that share a skeleton into one. The result keeps
# both material slots, so the neck cut and the cloth stand-off still do their
# work exactly as before.
import json, unreal

BASE = '/Game/Interval/Universal/Base/'
PEOPLE = '/Game/Interval/Universal/People/'
OUT_DIR = '/Game/Interval/Universal/Folk'
OUT = r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/folk.json"

lib = unreal.EditorAssetLibrary
report = {'made': [], 'errors': []}

WHO = {
    'Folk_Male_Peasant':   ('Superhero_Male_FullBody',   'Male_Peasant'),
    'Folk_Female_Peasant': ('Superhero_Female_FullBody', 'Female_Peasant'),
    'Folk_Male_Ranger':    ('Superhero_Male_FullBody',   'Male_Ranger'),
    'Folk_Female_Ranger':  ('Superhero_Female_FullBody', 'Female_Ranger'),
}

skeleton = lib.load_asset('/Game/Interval/Universal/Anims/UAL_Skeleton.UAL_Skeleton')

for made, (body, outfit) in WHO.items():
    a = lib.load_asset(BASE + body + '.' + body)
    b = lib.load_asset(PEOPLE + outfit + '.' + outfit)
    if a is None or b is None:
        report['errors'].append('missing source for ' + made)
        continue
    params = unreal.SkeletalMeshMergeParams()
    params.set_editor_property('meshes_to_merge', [a, b])
    params.set_editor_property('skeleton', skeleton)
    params.set_editor_property('needs_cpu_access', False)
    try:
        merged = unreal.SkeletalMergingLibrary.merge_meshes(params)
    except Exception as e:
        report['errors'].append('%s: %s' % (made, str(e)[:200]))
        continue
    if merged is None:
        report['errors'].append(made + ': merge returned nothing')
        continue
    # THE MERGE RETURNS A TRANSIENT MESH. It lives in the transient package and
    # disappears with the process; saving "it" by path saves nothing at all, and
    # reports success while doing so. Duplicating it into a real package is what
    # makes an asset, and the duplicate's return value is the only honest test.
    path = '%s/%s' % (OUT_DIR, made)
    if lib.does_asset_exist(path):
        lib.delete_asset(path)
    # AssetTools.duplicate_asset takes an OBJECT, which is what is needed here;
    # EditorAssetLibrary.duplicate_loaded_asset wants something already in a
    # real package and refuses a transient one.
    copy = unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(
        made, OUT_DIR, merged)
    if copy is None:
        report['errors'].append(made + ': duplicate into ' + path + ' failed')
        continue
    if not lib.save_loaded_asset(copy, False):
        report['errors'].append(made + ': save failed')
        continue
    if not lib.does_asset_exist(path):
        report['errors'].append(made + ': saved but not on disk')
        continue
    report['made'].append(path)

with open(OUT, 'w') as f:
    json.dump(report, f, indent=1)
unreal.log('FOLK MERGED')
