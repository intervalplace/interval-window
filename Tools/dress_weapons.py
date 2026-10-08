#!/usr/bin/env python3
"""Give the weapons kit this world's colours instead of the kit author's.

WHAT WAS REPORTED. That the shield and the plate body look like Templar kit:
a white field with red marks on it, which belongs to somebody else's world and
not to this one.

WHAT IS ACTUALLY THERE. No heraldry at all. Every mesh in the Quaternius
weapons pack is flat-coloured and its slots are named for the colour, so
`Shield_Heater` has exactly four: `Steel`, `DarkWood`, `LightWood` and
`LightSteel`. `Cuirass` has one, `Armor`, and it is a single dark steel. There
is no cross, no charge and no device anywhere in the pack.

What the eye is doing instead is reading two of those four colours as a device.
As the FBX arrived, `LightSteel` was (0.37, 0.39, 0.43) -- which sRGB lifts to
about two thirds of the way to white, and makes it the brightest thing on a
citizen, brighter than any cloth they own -- and `LightWood` was
(0.19, 0.08, 0.04), which is nearer red than brown. A pale field, red marks
across it, a boss in the middle. The eye finishes the job.

So there is nothing to remove. `dress_quaternius.py` already re-parents these
onto M_IntervalFlat, which is why they take the rain and the hour properly; it
simply left the numbers as imported. This is the other half of that job, and it
is the same principle `dress_kits.py` states for the Ruins, Village and Farm
packs: the colours are this project's, not the kit author's.

  dress_weapons.py            # and then nothing: the instances are shared, so
                              # every blade, haft, shaft and shield changes
"""
import json, os, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import rpc
import tiers

MI = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools'
SM = 'editor_toolset.toolsets.static_mesh.StaticMeshTools'
AST = 'editor_toolset.toolsets.asset.AssetTools'
call = rpc.call

KIT = '/Game/Interval/Quaternius/Kit'
FLAT = '/Game/Interval/Materials/M_IntervalFlat.M_IntervalFlat'

# name -> (r, g, b, roughness, grain)
#
# THE NUMBERS ARE NOT NEW. `forge.PALETTE` is where this project keeps what
# iron, steel, oak, leather, soot and quick-stone actually look like, and
# `dress_kits.py` already copies those same values onto the Ruins, Village and
# Farm packs. So this table is mostly a map from a kit slot name to a colour
# this world already owns, and a hatchet's haft is now the same oak as a
# cart's.
#
# THE RED WAS THE WHOLE COMPLAINT. `LightWood` arrived at (0.19, 0.08, 0.04),
# which is four parts red to one part green -- not a wood at all. It is the
# field of every shield in the pack and the haft of every axe. Beside the pale
# metal of the cross bands it made a white shield with red marks on it, which
# is the device it was reported as. `Oak` is (0.49, 0.36, 0.21), and that is a
# plank.
#
# THE THREE METALS ARE SORTED BY JOB, not by their names, which are the kit
# author's. `Steel` is the dull frame and the fittings, so it takes this
# world's IRON; `DarkSteel` is every blade in the pack, so it takes this
# world's STEEL and is polished smooth enough to catch the sky; `LightSteel`
# is the studs and the edge accent, a shade up from the frame, the way
# `Highlights` sits a shade up from masonry in the kits.
PALETTE = {
    'Steel':      (0.353, 0.365, 0.396, 0.52, 0.08),   # forge Iron: frames, rims
    'DarkSteel':  (0.541, 0.565, 0.600, 0.30, 0.05),   # forge Steel: the blades
    'LightSteel': (0.600, 0.615, 0.640, 0.38, 0.06),   # a shade up: studs, edges
    'DarkWood':   (0.278, 0.180, 0.106, 0.90, 0.18),   # forge WoodDark
    'LightWood':  (0.490, 0.357, 0.208, 0.88, 0.18),   # forge Oak
    'DarkBrown':  (0.329, 0.231, 0.149, 0.92, 0.16),   # forge Leather: grips
    'Black':      (0.114, 0.110, 0.118, 0.86, 0.10),   # forge Soot
    'White':      (0.784, 0.769, 0.729, 0.90, 0.10),   # forge Fletch: strings
    'Red':        (0.412, 0.204, 0.176, 0.88, 0.12),   # forge Heartgrain
    # THE CLAYMORE'S BLADE, and nothing else in the pack, so this is a free
    # choice. At the kit's value it came out rose pink. Dark and blood-iron
    # instead: the one blade here that is not steel reads as old and ill-made
    # rather than as a toy.
    'LightRed':   (0.300, 0.140, 0.125, 0.40, 0.08),

    # ---- AND STARMETAL, WHICH THIS KIT CALLS GOLD ----
    #
    # The kit's `Golden` meshes are this project's STAR tier and always have
    # been: parts.py draws `quick-sword` as Sword_Golden and `quick-shield` as
    # Shield_Celtic_Golden. So the slot named `Gold` is not gold here, it is
    # quickmetal, and it was the one colour in the pack actively telling a lie
    # about what a citizen was holding.
    #
    # AND THE COLOUR IS `tiers.py`'s, NOT ONE INVENTED HERE. That file already
    # decides what each grade's metal reads as and the inventory sprites have
    # been drawn from it since there were sprites, so a quick sword in a hand
    # and the same sword in the pack have to be the one row or they are two
    # different swords. `tiers.TIERS['quick']` is the pale blue of quick-alloy.
    'Gold':       tiers.TIERS['quick'] + (0.32, 0.06),        # quickmetal
    'LightGold':  (0.760, 0.860, 1.000, 0.26, 0.05),         # its highlight
    # The quick-shield's facing, a shade under the bands that cross it.
    'LightBlue':  (0.430, 0.545, 0.720, 0.36, 0.06),
    # AND ITS BOSS IS THE STONE ITSELF. A green gem in the middle of the
    # rarest shield on the island belonged to another world. A quick-stone
    # does not: it is what the shield is made of, seven ingots back.
    'Green':      (0.435, 0.353, 0.663, 0.28, 0.05),   # forge Magic
}

call('EditorToolset.EditorAppToolset', 'StopPIE', {})

# FOUND, NOT NAMED. The four instances are shared by the whole pack, but the
# import has made copies before now -- there is a second set under
# /Game/Interval/Ships -- and a colour set on one of two identically named
# materials is the worst kind of half-fix, because the thing that still looks
# wrong is a different asset with the same name. So: ask the registry which
# instances are actually there, and dress every one of them that this table
# knows a colour for.
rows = json.loads(call(AST, 'find_assets',
    {'folder_path': KIT, 'name': '', 'recursive': True,
     'asset_type': {'refPath': '/Script/Engine.MaterialInstanceConstant'}}
    ))['returnValue']
found = {}
for row in rows:
    path = row if isinstance(row, str) else row.get('refPath', '')
    if not path:
        continue
    short = path.split('/')[-1].split('.')[0]
    if short in PALETTE:
        found[short] = path if '.' in path.split('/')[-1] else '%s.%s' % (path, short)

for name in sorted(PALETTE):
    if name not in found:
        print('%-12s NOT FOUND under %s' % (name, KIT))
        continue
    r, g, b, rough, grain = PALETTE[name]
    path = found[name]
    call(MI, 'set_vector_parameter', {'instance': {'refPath': path},
         'name': 'DiffuseColor', 'value': {'r': r, 'g': g, 'b': b, 'a': 1.0}})
    for param, v in (('Rough', rough), ('Grain', grain), ('Course', 0.0),
                     ('Plank', 0.0),
                     # A SWORD IS THE WORLD'S SWORD, not this person's, so no
                     # part of what a citizen carries takes their key's dye.
                     # `dress_quaternius.py` says the same thing where it sets
                     # Strength to zero for everything under /Kit/; repeated
                     # here so running this alone leaves nothing half-set.
                     ('Strength', 0.0), ('Shift', 0.5)):
        call(MI, 'set_scalar_parameter',
             {'instance': {'refPath': path}, 'name': param, 'value': v})
    call(AST, 'save_assets', {'asset_paths': [path.split('.')[0]]})
    print('%-12s (%.3f %.3f %.3f)  rough %.2f  grain %.2f   %s'
          % (name, r, g, b, rough, grain, path))

# ---------------------------------------------------------------------------
# AND THE TWO PLAIN SHIELDS, WHICH WERE THE SAME SHIELD IN THE SAME METAL.
#
# `iron-shield` is drawn as Shield_Heater and `steel-shield` as
# Shield_Heater_2, which is tiering by SHAPE -- and those two shapes differ by
# a bevel and the pattern of the studs. At forty paces, and in the pack, they
# were the same object. The world does not think so: one is four iron and an
# oak log, the other three steel and an ironbark plank, and steel is a hundred
# and twenty where iron is thirty-four.
#
# The shields cannot tier by a material override the way the plate does,
# because each has four slots and a single override would turn the oak planks
# into metal along with the frame. But they are separate ASSETS, so their metal
# slots can be bound separately, and that loses nothing: Shield_Heater keeps
# the shared iron the rest of the kit wears, and Shield_Heater_2 gets steel and
# silver, a clear step brighter.
#
# The quick-shield needs nothing here. It is Shield_Celtic_Golden, whose slots
# are its own, and they are quickmetal already.
TIER = {
    'ShieldSteel':      (0.541, 0.565, 0.600, 0.40, 0.07),   # forge Steel
    'ShieldSteelLight': (0.659, 0.671, 0.678, 0.34, 0.06),   # forge Silver
}
for name, (r, g, b, rough, grain) in sorted(TIER.items()):
    path = '%s/%s.%s' % (KIT, name, name)
    call(AST, 'delete', {'path': path.split('.')[0]})
    call(MI, 'create', {'folder_path': KIT, 'asset_name': name,
                        'parent': {'refPath': FLAT}})
    call(MI, 'set_vector_parameter', {'instance': {'refPath': path},
         'name': 'DiffuseColor', 'value': {'r': r, 'g': g, 'b': b, 'a': 1.0}})
    for param, v in (('Rough', rough), ('Grain', grain), ('Course', 0.0),
                     ('Plank', 0.0), ('Strength', 0.0), ('Shift', 0.5)):
        call(MI, 'set_scalar_parameter',
             {'instance': {'refPath': path}, 'name': param, 'value': v})
    call(AST, 'save_assets', {'asset_paths': [path.split('.')[0]]})

STEEL_SHIELD = '%s/Shield_Heater_2.Shield_Heater_2' % KIT
for slot, name in (('Steel', 'ShieldSteel'), ('LightSteel', 'ShieldSteelLight')):
    call(SM, 'set_material', {'mesh': {'refPath': STEEL_SHIELD}, 'slot_name': slot,
         'material': {'refPath': '%s/%s.%s' % (KIT, name, name)}})
call(AST, 'save_assets', {'asset_paths': [STEEL_SHIELD.split('.')[0]]})
print('steel-shield wears steel and silver; iron-shield keeps the kit iron')

# AND SAY WHAT WEARS THEM, because four materials is a small number and the
# list of things that change is not.
worn = {}
meshes = json.loads(call(AST, 'find_assets',
    {'folder_path': KIT, 'name': '', 'recursive': True,
     'asset_type': {'refPath': '/Script/Engine.StaticMesh'}}))['returnValue']
for row in meshes:
    path = row if isinstance(row, str) else row.get('refPath', '')
    if not path:
        continue
    mesh = {'refPath': path if '.' in path.split('/')[-1]
            else '%s.%s' % (path, path.split('/')[-1])}
    try:
        slots = json.loads(call(SM, 'get_material_slots', {'mesh': mesh}))['returnValue']
    except Exception:
        continue
    for s in slots or ():
        if s in PALETTE:
            worn.setdefault(s, []).append(path.split('/')[-1].split('.')[0])
for name in sorted(worn):
    print('%-12s on %d meshes: %s' % (name, len(worn[name]),
          ', '.join(sorted(worn[name])[:6]) + (' ...' if len(worn[name]) > 6 else '')))
