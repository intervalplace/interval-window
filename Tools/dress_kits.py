#!/usr/bin/env python3
"""Dress the three kits that nothing ever dressed: Ruins, Village and Farm.

WHAT WAS WRONG. `dress_props.py` covers `/Game/Interval/Props`, `dress_nature`
covers the nature kit, `dress_universal` the people. Nothing covered the Ruins,
the Medieval Village or the Farm packs at all, so every mesh in them kept the
material its FBX import invented -- `FBXLegacyPhongSurfaceMaterial` -- and a
legacy Phong material is not one of this project's masters. It draws, which is
why nobody noticed, and it takes NONE of the world: no rain darkening it, no
wetness, no hour, no grain, no dye. A well, a windmill, a bell tower, two
boats, a bonfire, the bridge sections, the columns, the arches and the rubble
were all lit by a different set of rules from the ground they stood on.

Found by `Tools/audit_art.py`, which walks every table in parts.py and asks of
every slot whether the chain of parents reaches a master this project owns.
Twenty-five meshes and sixty-five slots did not.

HOW THEY ARE DRESSED. These kits are flat-coloured, like the nature one and
like everything this project forges: no textures, one material per colour, and
the SLOT IS NAMED AFTER THE COLOUR -- `Stone_Dark`, `DarkWood`, `RoofTiles`,
`Hay`. So the palette below is the table, the slot name is the key, and a kit
that adds a colour needs a row here and nothing else.

The colours are this project's, not the kit author's: northern, muted, and the
same stone and timber the walls and the ground already use, so a ruin standing
in a meadow belongs to the meadow.

  dress_kits.py
"""
import json, os, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import rpc

MASTER = '/Game/Interval/Materials/M_IntervalFlat.M_IntervalFlat'
HUES = '/Game/Interval/Kits/Hues'
# AND THE SHIPS, which are a fourth kit in a folder of their own: the ferry
# that crosses the river, the upturned boat on a beach and the wreck. Found
# the second time the audit was run, after the first three were dressed --
# which is the argument for having the audit at all.
KITS = ('/Game/Interval/Ruins', '/Game/Interval/Village', '/Game/Interval/Farm',
        '/Game/Interval/Ships')
MI = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools'
SM = 'editor_toolset.toolsets.static_mesh.StaticMeshTools'
AST = 'editor_toolset.toolsets.asset.AssetTools'
call = rpc.call

# slot name -> (r, g, b, roughness, grain)
#
# Grain is the world-space mottle every flat surface in this window gets so it
# does not read as plastic; stone takes more of it than metal does.
PALETTE = {
    # ---- stone, which is most of a ruin ----
    'Main':        (0.290, 0.288, 0.280, 0.86, 0.15),
    'Stone':       (0.265, 0.268, 0.272, 0.86, 0.15),
    'Stone_Light': (0.355, 0.358, 0.362, 0.85, 0.14),
    'Stone_Dark':  (0.195, 0.198, 0.202, 0.88, 0.16),
    'Grey':        (0.300, 0.305, 0.312, 0.86, 0.14),
    'DarkGrey':    (0.180, 0.182, 0.186, 0.88, 0.15),
    'White':       (0.620, 0.612, 0.585, 0.84, 0.12),
    'Beige':       (0.520, 0.470, 0.380, 0.86, 0.13),
    # `Highlights` is the kit's edge accent on masonry: a shade up, not a
    # different material.
    'Highlights':  (0.345, 0.342, 0.334, 0.84, 0.12),
    # ---- timber ----
    'Wood':        (0.400, 0.267, 0.157, 0.88, 0.18),
    'Wood_Light':  (0.470, 0.345, 0.200, 0.88, 0.18),
    'LightWood':   (0.470, 0.345, 0.200, 0.88, 0.18),
    'DarkWood':    (0.230, 0.150, 0.088, 0.90, 0.18),
    'Wood_Side':   (0.330, 0.220, 0.130, 0.90, 0.19),
    'WoodSide':    (0.330, 0.220, 0.130, 0.90, 0.19),
    'Bark':        (0.302, 0.224, 0.149, 0.92, 0.22),
    'Brown':       (0.300, 0.205, 0.125, 0.89, 0.18),
    # ---- roofs and thatch ----
    'RoofTiles':     (0.330, 0.200, 0.150, 0.88, 0.16),
    'RoofTiles_Red': (0.400, 0.170, 0.130, 0.88, 0.16),
    'Hay':           (0.560, 0.450, 0.220, 0.94, 0.20),
    # ---- metal ----
    'Metal':       (0.300, 0.310, 0.330, 0.50, 0.08),
    'Metal_Light': (0.470, 0.487, 0.515, 0.42, 0.07),
    'Steel':       (0.541, 0.565, 0.600, 0.40, 0.07),
    'Bell':        (0.420, 0.330, 0.140, 0.36, 0.06),
    # ---- the rest ----
    'Leather':     (0.329, 0.231, 0.149, 0.82, 0.14),
    'Bag':         (0.545, 0.463, 0.333, 0.92, 0.18),
    'Red':         (0.380, 0.150, 0.120, 0.86, 0.14),
    'LightRed':    (0.480, 0.240, 0.190, 0.86, 0.14),
    'Black':       (0.090, 0.088, 0.086, 0.90, 0.10),
    # A WINDOW IS A HOLE. Nearly black, because a small opening into an unlit
    # room is the darkest thing on a sunlit wall -- the same argument the
    # timber frame makes about its own openings.
    'Windows':     (0.045, 0.052, 0.062, 0.70, 0.06),
    # ---- and the rest of what these three kits name ----
    'DarkRed':     (0.280, 0.110, 0.090, 0.88, 0.15),
    'LightBrown':  (0.420, 0.300, 0.180, 0.88, 0.17),
    'DarkBrown':   (0.200, 0.135, 0.085, 0.90, 0.18),
    'Plaster':     (0.520, 0.495, 0.430, 0.90, 0.16),
    'RoofBlack':   (0.120, 0.122, 0.128, 0.86, 0.14),
    'Green':       (0.150, 0.230, 0.110, 0.90, 0.18),
    'Flag':        (0.400, 0.150, 0.130, 0.92, 0.16),
    'Gold':        (0.769, 0.588, 0.208, 0.34, 0.06),
    'DarkMetal':   (0.180, 0.185, 0.195, 0.52, 0.08),
    'Orange':      (0.620, 0.330, 0.120, 0.86, 0.14),
    'Candle':      (0.620, 0.580, 0.470, 0.80, 0.10),
    'Light':       (0.700, 0.560, 0.330, 0.70, 0.08),
    'Pages':       (0.847, 0.796, 0.667, 0.90, 0.10),
    'Soup':        (0.667, 0.482, 0.243, 0.70, 0.10),
    'Bag_Inside':  (0.300, 0.250, 0.180, 0.92, 0.18),
    # Four books on a shelf, in four bindings, because a shelf of one colour
    # is a shelf of one book repeated.
    'Book':        (0.300, 0.120, 0.100, 0.86, 0.12),
    'Book2':       (0.150, 0.190, 0.280, 0.86, 0.12),
    'Book3':       (0.220, 0.230, 0.150, 0.86, 0.12),
    'Book4':       (0.280, 0.180, 0.110, 0.86, 0.12),
    # ---- and the ships ----
    'Fabric':      (0.560, 0.530, 0.470, 0.94, 0.16),
    'Sail':        (0.600, 0.570, 0.505, 0.94, 0.16),
    # The kit names one slot after its hex colour, which is near white.
    'F2F2F2':      (0.700, 0.695, 0.680, 0.90, 0.12),
}

# SLOTS THAT MUST KEEP WHAT THEY HAVE.
#
# A leaf card is a flat quad wearing an atlas that is three-quarters empty, and
# the alpha channel is the only record of where the leaf ends. Binding a flat
# colour to one does not give it a colour, it gives it a green RECTANGLE -- the
# `dark shattered glass` failure written up in person_mat.hlsl, arrived at from
# the other direction. Smoke and fire cards are the same shape of thing.
#
# So these are left with whatever they came in wearing, which is honest: they
# want the foliage master and a real atlas, not a colour.
KEEP = ('texture', 'leaf', 'smoke', 'fire')

call('EditorToolset.EditorAppToolset', 'StopPIE', {})

made = {}
for name, (r, g, b, rough, grain) in sorted(PALETTE.items()):
    path = '%s/%s.%s' % (HUES, name, name)
    call(AST, 'delete', {'path': path.split('.')[0]})
    call(MI, 'create', {'folder_path': HUES, 'asset_name': name,
                        'parent': {'refPath': MASTER}})
    call(MI, 'set_vector_parameter', {'instance': {'refPath': path},
         'name': 'DiffuseColor', 'value': {'r': r, 'g': g, 'b': b, 'a': 1.0}})
    for param, v in (('Rough', rough), ('Grain', grain), ('Course', 0.0),
                     ('Plank', 0.0),
                     # Nothing standing in a field takes a citizen's dye.
                     ('Strength', 0.0), ('Shift', 0.5)):
        call(MI, 'set_scalar_parameter',
             {'instance': {'refPath': path}, 'name': param, 'value': v})
    call(AST, 'save_assets', {'asset_paths': [path.split('.')[0]]})
    made[name] = path
print('dressed %d kit colours' % len(made))

# AND BOUND TO EVERY MESH IN THE THREE KITS, not to a list of the ones that
# happened to be noticed. The asset registry is the truth about what was
# imported; a mesh added tomorrow is dressed by running this again.
bound = missed = 0
unknown = {}
for folder in KITS:
    try:
        rows = json.loads(call(AST, 'find_assets',
            {'folder_path': folder, 'name': '', 'recursive': True,
             'asset_type': {'refPath': '/Script/Engine.StaticMesh'}}))['returnValue']
    except Exception as exc:
        print('%s: cannot list (%s)' % (folder, str(exc)[:70]))
        continue
    for row in rows:
        path = row if isinstance(row, str) else row.get('refPath', '')
        if not path or '/Hues/' in path:
            continue
        mesh = {'refPath': path if '.' in path.split('/')[-1]
                else '%s.%s' % (path, path.split('/')[-1])}
        try:
            slots = json.loads(call(SM, 'get_material_slots', {'mesh': mesh}))['returnValue']
        except Exception:
            continue                      # not a static mesh: a texture, an anim
        if not slots:
            continue
        for s in slots:
            if any(k in s.lower() for k in KEEP):
                continue
            if s not in made:
                unknown.setdefault(s, 0)
                unknown[s] += 1
                missed += 1
                continue
            call(SM, 'set_material', {'mesh': mesh, 'slot_name': s,
                                      'material': {'refPath': made[s]}})
            bound += 1
        call(AST, 'save_assets', {'asset_paths': [mesh['refPath'].split('.')[0]]})
print('bound %d slots, %d with no colour named' % (bound, missed))
for s, n in sorted(unknown.items(), key=lambda r: -r[1]):
    print('   no row for slot %-22s (%d meshes)' % (s, n))
print('NOW RUN apply.py')
