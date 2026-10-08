# THE THREE CC0 PACKS THAT CLOSE THE PRIMITIVE BACKLOG.
#
# `Tools/audit.py` says every WORD the world uses has a row -- 52 node types,
# 117 node kinds, 23 keepers, 7 stalls, all drawn -- and that seventy-one of
# those rows are still a scaled cube, cylinder, cone or sphere. Over half of
# the seventy-one are `landmark.*`, and the rest are the things a citizen
# stands next to every day: the well, the fence, the market stall, the mill.
#
# WHY THESE PACKS AND NOT THE OBVIOUS ONE. KayKit is CC0, well made, and was
# turned down on sight -- its proportions are stylised toward a small-scale
# strategy look and beside a Quaternius citizen it reads as a different game.
# Everything already in this window is Quaternius, so staying inside that
# catalogue makes scale and style a guarantee rather than a judgement.
#
#   Medieval Village Pack   44 models  Well, Fence, Hay, Cart, MarketStand x2,
#                                      Mill, Bell, Bell_Tower, Gazebo, Bonfire
#   Ultimate Modular Ruins  50 models  Arches, columns, bricks, floors -- the
#                                      ruined half of the landmark vocabulary
#   Farm Buildings          13 models  Windmill, TowerWindmill, barns, a Well
#
# All three are CC0 1.0 Universal, declared in each pack's OWN License.txt --
# read from the file, not inferred from an aggregator, which is the rule this
# project keeps because Poly Pizza once labelled a Quaternius pack CC BY 3.0
# that the author releases CC0 (see Art/RPGCharacters/LICENCE.txt).
#
# EACH PACK GETS ITS OWN FOLDER, and not for tidiness: Barrel, Cart, Crate,
# Fence and Well each appear in more than one of them, and a flat destination
# would have them silently overwrite each other in import order.
import os, json, unreal

ROOT = os.path.abspath(os.path.join(unreal.Paths.project_dir(), 'Art'))
OUT = (r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/"
       r"d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/village.json")

# (folder under Art, subpath to the FBX, destination in /Game)
PACKS = [
    ('MedievalVillage', 'FBX',  '/Game/Interval/Village'),
    ('Ruins',           '',     '/Game/Interval/Ruins'),
    ('FarmBuildings',   '',     '/Game/Interval/Farm'),
    ('Ships',           '',     '/Game/Interval/Ships'),
]

tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary
report = {'errors': [], 'packs': {}}


def pipeline():
    p = unreal.InterchangeGenericAssetsPipeline()
    mesh = p.get_editor_property('mesh_pipeline')
    mesh.set_editor_property('import_static_meshes', True)
    mesh.set_editor_property('import_skeletal_meshes', False)
    p.get_editor_property('animation_pipeline').set_editor_property('import_animations', False)
    return p


tasks = []
for folder, sub, dest in PACKS:
    art = os.path.join(ROOT, folder, sub) if sub else os.path.join(ROOT, folder)
    if not os.path.isdir(art):
        report['errors'].append('missing ' + art)
        continue
    names = sorted(f for f in os.listdir(art) if f.lower().endswith('.fbx'))
    report['packs'][folder] = {'found': len(names), 'dest': dest}
    for f in names:
        t = unreal.AssetImportTask()
        t.set_editor_property('filename', os.path.join(art, f))
        t.set_editor_property('destination_path', dest)
        t.set_editor_property('destination_name', os.path.splitext(f)[0])
        t.set_editor_property('automated', True)
        t.set_editor_property('replace_existing', True)
        t.set_editor_property('save', True)
        over = unreal.InterchangePipelineStackOverride()
        over.add_pipeline(pipeline())
        t.set_editor_property('options', over)
        tasks.append(t)

# ONE CALL for all of them: a hundred and seven separate imports would each pay
# the Interchange start-up, which is the slow part.
tools.import_asset_tasks(tasks)

# WHAT ACTUALLY LANDED, AND HOW BIG IT IS.
#
# The size is not a curiosity. Every one of these has to stand beside a citizen
# 1.81 m tall, and the Farm pack is from 2018 -- three years older than the
# others and a shade simpler -- so its scale is the one most likely to be off.
# Measuring here saves guessing at a number in parts.py later.
for folder, sub, dest in PACKS:
    rows = []
    for p in sorted(lib.list_assets(dest, recursive=True, include_folder=False)):
        data = lib.find_asset_data(p)
        if str(data.asset_class_path.asset_name) != 'StaticMesh':
            continue
        mesh = lib.load_asset(p)
        b = mesh.get_bounding_box()
        size = b.max - b.min
        slots = [str(s.material_slot_name) for s in mesh.static_materials]
        rows.append({'path': p, 'name': p.rsplit('/', 1)[-1],
                     'cm': [round(size.x, 1), round(size.y, 1), round(size.z, 1)],
                     'slots': slots})
    report['packs'].setdefault(folder, {})['meshes'] = rows
    report['packs'][folder]['imported'] = len(rows)

with open(OUT, 'w') as f:
    json.dump(report, f, indent=1)
unreal.log('VILLAGE IMPORT DONE: ' + json.dumps(
    {k: v.get('imported') for k, v in report['packs'].items()}))
