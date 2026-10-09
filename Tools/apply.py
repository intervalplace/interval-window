#!/usr/bin/env python3
"""Gather the level's look into the look asset, with this session's additions.

The look used to live on the level's own actors. It cannot: those are
external-actor packages and nothing here can save one under automation, so a
session's worth of meshes and offsets went with the editor on every rebuild.
This reads whatever the actors still carry, lays this session's work over it,
writes the result to /Game/Interval/IntervalLook and SAVES -- an asset saves.

Run it after any editor restart until the asset is the only copy; after that
it is the record of what changed and why, and running it is a no-op.
"""
import copy
import json, os, subprocess, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import rpc as _rpc
from parts import (PARTS, LIFT, SUNK, LANDMARKS, KEEPERS, STALL_GOODS, TREES, WOOD, GEAR_PATH,
                   FIREBEDS, VILLAGE, VILLAGE2, STALL_MESH, UNSEEN, LIKEWISE,
                   PLOTS, PLOT_BED, SOWN, plot_stages, GROW_TICKS_RIPE,
                   FURNITURE, GEAR, UNDERFOOT, BEASTS, BEAST, DRILL,
                   KEEPER_FOLK, NATURE_PROPS, PROP_PROPS, VARIETY, FACES,
                   WILD_BEASTS, WILD_STILL, WILD, DARK_BEASTS, DARK, beast_motions,
                   CLOTHING, WORN, HATCHET, PICKAXE, ROD, MESH_SCALE,
                   light, burn, fill, smoke)

LVL = '/Game/TopDown/Lvl_TopDown.Lvl_TopDown:PersistentLevel.'
STRUCT = LVL + 'IntervalStructures_UAID_A4FC143F8D45860303_1132341583'
GROUND = LVL + 'IntervalGround_UAID_A4FC143F8D45840303_1178801231'
CITIZENS = LVL + 'IntervalCitizens_UAID_A4FC143F8D45870303_1233687759'
LOOK = '/Game/Interval/IntervalLook.IntervalLook'

# Free-standing stonework and fencing: nothing roofs these, so the height comes
# from the tile's own id and the top of the run undulates the way a wall laid
# by hand undulates. A dead-level coping over forty tiles is the tell.
TOPS = {'wall': 0.10, 'wall.unroofed': 0.10, 'wall.stone': 0.08,
        'fence': 0.14, 'hedge': 0.16, 'railing': 0.08, 'palisade': 0.06}
TIMBER = {'refPath': '/Game/Interval/Materials/M_IntervalTimberFrame.M_IntervalTimberFrame'}

def call(toolset, tool, args):
    # One session for the whole script; see Tools/rpc.py.
    return _rpc.call(toolset, tool, args)


OBJ = 'editor_toolset.toolsets.object.ObjectTools'

# STOP THE SESSION BEFORE TOUCHING ANY ASSET.
#
# Rewriting the look asset while a Simulate session is running wedges the
# editor solidly: it holds the port, accepts connections and answers nothing,
# and it wedges on the FIRST call, so a StopPIE sent afterwards never lands.
# That is three editors killed in one session. The guard costs one call.
call('EditorToolset.EditorAppToolset', 'StopPIE', {})

def read(obj, *props):
    t = call(OBJ, 'get_properties', {'instance': {'refPath': obj}, 'properties': list(props)})
    if t.startswith('GetObjectProperties'):
        raise SystemExit(t)
    return json.loads(json.loads(t)['returnValue'])

def write(obj, values):
    return call(OBJ, 'set_properties', {'instance': {'refPath': obj}, 'values': json.dumps(values)})

# ---- AND IT MUST BE ABLE TO START FROM NOTHING ----
#
# This script DELETES the look and makes a fresh one further down, so a run
# that fails between those two points leaves no asset at all. The next run then
# died on the line below, reading properties off a thing that was not there,
# and the error said "Expecting value: line 1 column 1" rather than "the look
# is gone" -- so the recovery this file already has, further down, could never
# be reached.
#
# The recovery is real: every table below falls back to the actors placed in
# the level, which carry their own copies. All this needed was for the asset to
# exist so the read could come back empty rather than throw.
if 'returnValue' not in call(OBJ, 'get_properties',
                             {'instance': {'refPath': LOOK}, 'properties': ['Motions']}):
    print('the look was missing; making an empty one to rebuild into')
    # THE SAME TOOLSET THE REAL CREATE USES, further down: a data asset is
    # made by `DataAssetTools`, and `AssetTools` answers "Unknown tool create".
    call('editor_toolset.toolsets.data_asset.DataAssetTools', 'create',
         {'folder_path': '/Game/Interval', 'asset_name': 'IntervalLook',
          'asset_type': {'refPath': '/Script/IntervalBridge.IntervalLook'}})

have = read(LOOK, 'Props', 'PropsUpper', 'Mobs', 'Scatter', 'Roofs', 'GroundMaterial')
# THE ACTOR STILL HOLDS THE LONGER TABLE, AND THE LONGER ONE WINS.
#
# This script reads the look asset and writes it back, so a table that is short
# by half stays short by half forever -- and a refused write leaves exactly
# that. The citizens actor carries the original mob table; where it has more
# rows than the asset does, the asset is the damaged copy.
_actor_mobs = read(CITIZENS, 'Mobs').get('Mobs') or {}
if len(_actor_mobs) > len(have.get('Mobs') or {}):
    print('mobs: asset has %d rows, actor has %d -- taking the actor\'s'
          % (len(have.get('Mobs') or {}), len(_actor_mobs)))
    have['Mobs'] = _actor_mobs
# Prefer what the asset already holds; fall back to the actors the first time.
if not have.get('Props'):
    have['Props'] = read(STRUCT, 'Props')['Props']
    have['PropsUpper'] = read(STRUCT, 'PropsUpper')['PropsUpper']
if not have.get('Mobs'):
    have['Mobs'] = read(CITIZENS, 'Mobs')['Mobs']
if not have.get('Scatter'):
    g = read(GROUND, 'Scatter', 'Roofs', 'GroundMaterial')
    have['Scatter'], have['Roofs'] = g['Scatter'], g['Roofs']
    have['GroundMaterial'] = g['GroundMaterial']

# ---------------------------------------------------------------------------
# BUILT FROM SCRATCH EVERY RUN.
#
# The property setter will change an array's SIZE or its CONTENTS in one call,
# never both. It says so per property and then carries on, so the rest of the
# write lands and the refused part is silently missing -- which is how every
# flame added to every hearth went missing without a word. A two-pass dance
# survives growth and does not survive removal.
#
# So the asset is deleted and remade, and every write is an addition into a
# fresh object. This file is then the only thing that decides what the look
# contains, which was already true in spirit and is now true in fact.
call('editor_toolset.toolsets.asset.AssetTools', 'delete',
     {'path': '/Game/Interval/IntervalLook'})
call('editor_toolset.toolsets.data_asset.DataAssetTools', 'create',
     {'folder_path': '/Game/Interval', 'asset_name': 'IntervalLook',
      'asset_type': {'refPath': '/Script/IntervalBridge.IntervalLook'}})

# What the level's own actors still carry is the starting point: the meshes,
# scales and materials for every word, set long before this file existed.
have = {
    'Props': read(STRUCT, 'Props')['Props'],
    'PropsUpper': read(STRUCT, 'PropsUpper')['PropsUpper'],
    'Mobs': read(CITIZENS, 'Mobs')['Mobs'],
}
g = read(GROUND, 'Scatter', 'Roofs', 'GroundMaterial')
have['Scatter'], have['Roofs'] = g['Scatter'], g['Roofs']
have['GroundMaterial'] = g['GroundMaterial']

# ---------------------------------------------------------------------------
# WHAT ELSE EACH GROUND GROWS.
#
# Every terrain scattered exactly ONE mesh, so a meadow was tens of thousands
# of copies of a single tuft and a wood was one bush to the horizon. Colour
# variation helped and could not fix it: every copy still had the same
# SILHOUETTE, and one outline repeated reads as stamped however well it is
# drawn.
#
# Chosen so each ground still reads as ITSELF -- this is variety within a
# country, not a botanical garden. The fens get tall wispy grass and reeds and
# nothing flowering; the downs get short dry grass and clover; a meadow is
# allowed a few flowers because that is what makes it a meadow rather than a
# lawn. Stone grounds get other stones, not plants.
#
# Kept to a handful each: every distinct mesh is one more instanced component
# per chunk.
GROWS = {
    'heartlands': ['Grass_Common_Tall', 'Clover_1', 'Grass_Wispy_Short'],
    'meadow':     ['Grass_Common_Short', 'Flower_4_Single', 'Clover_2', 'Grass_Wispy_Tall'],
    'downs':      ['Grass_Common_Short', 'Clover_1'],
    'greenwood':  ['Plant_1', 'Bush_Common', 'Mushroom_Common'],
    'forest':     ['Fern_1', 'Plant_1_Big', 'Mushroom_Laetiporus'],
    'wilds':      ['Plant_7', 'Grass_Wispy_Tall', 'Plant_1_Big'],
    'fens':       ['Grass_Wispy_Short', 'Plant_7_Big'],
    'moor':       ['Plant_7_Big', 'Grass_Wispy_Short'],
    'peat':       ['Grass_Wispy_Short'],
    'crags':      ['Rock_Medium_2', 'Pebble_Square_2'],
    'scree':      ['Pebble_Square_2', 'Pebble_Square_3'],
    'gravel':     ['Pebble_Round_2', 'Pebble_Round_4'],
    'mountain':   ['Rock_Medium_1', 'Pebble_Square_1'],
    'chalk':      ['Pebble_Round_1', 'Pebble_Round_4'],
    'shingle':    ['Pebble_Round_1', 'Pebble_Round_3', 'Pebble_Round_5'],
    'sand':       ['Pebble_Round_1', 'Pebble_Round_3'],
    'trodden':    ['Grass_Common_Short'],
    # THE SPINE, in three stones rather than one. A ridge of a single repeated
    # boulder reads as a fence of identical lumps; three sizes of the same
    # stone read as rock. The row is created just below -- `ridge` is not a
    # terrain and arrives with no row of its own -- and it MUST be created
    # before this loop runs, or it keeps whichever row it was copied from and
    # the island's spine sprouts clover.
    'ridge':      ['Rock_Medium_1', 'Rock_Medium_3'],
}
# `ridge` IS NOT A GROUND AND THE TABLE HAS NO ROW FOR IT.
#
# Every other key here names a terrain the world sends, so the map arrives with
# a row already made. The spine does not: it is a predicate, its tiles read as
# `crags`, and the bridge tells the window where it is separately. The row is
# made by copying the shape of one that exists, because these are struct
# defaults and inventing the keys by hand is how a setter comes to refuse the
# whole map.
import copy as _copy
if 'ridge' not in have['Scatter'] and have['Scatter']:
    have['Scatter']['ridge'] = _copy.deepcopy(next(iter(have['Scatter'].values())))

for _ground, _also in GROWS.items():
    _row = have['Scatter'].get(_ground)
    if not _row:
        continue
    # Never the row's own mesh again -- it is already variant zero, and listing
    # it twice would simply make it twice as likely.
    _first = str((_row.get('mesh') or {}).get('refPath', '')).split('/')[-1].split('.')[0]
    _row['variants'] = [{'refPath': '/Game/Interval/Nature/%s.%s' % (_m, _m)}
                        for _m in _also if _m != _first]

# ---- AND THE CRAGS ARE NOT A BOULDER FIELD ----
#
# Measured, because the eye said "weird" and the eye was right: `Rock_Medium_1`
# is 3.2 x 3.0 x 2.3 metres before scaling, and crags drew it at 0.35, which is
# an eighth over a metre across, at 0.24 over two tries a tile. That is one
# metre-wide boulder every other tile, forever, on every crag on the island.
#
# Every other stone ground uses PEBBLES: gravel draws a 22 cm Pebble_Round_1,
# scree a 24 cm Pebble_Square_1. Crags was the only ground outside the ridges
# scattering something a person could not step over, and at twice the spacing
# of a fence post.
#
# A crag is a rocky slope with the odd real boulder on it, not a field of them.
# Half as many, a little smaller, and a much wider spread of sizes, so what is
# left reads as rock that fell rather than as one mesh stamped over a hill.
for _hill, _per, _sc, _jit in (('crags', 0.11, 0.30, 0.55),):
    _row = have['Scatter'].get(_hill)
    if _row:
        _row['perTile'] = _per
        _row['scale'] = {'x': _sc, 'y': _sc, 'z': _sc}
        _row['scaleJitter'] = _jit

# ---- A FERN IN A WOOD IS NOT WHITE ----
#
# `greenwood` scatters `Fern_1` half a tile apart wearing the kit's own
# material, which is a pale, almost white green. One fern is a fern; one every
# other tile, from the height a citizen's camera actually sits at, is a field
# of pale blotches on a dark floor, and at the range the settlement sweep was
# shot from it reads as scree lying in a wood.
#
# Every other ground scatters something already in this project's palette or
# something the kit got right. This is the one that fights it, so it is given
# the scatter green the grasses wear.
for _wood, _mat in (('greenwood', 'MI_ScatterGrass'),):
    _row = have['Scatter'].get(_wood)
    if _row:
        _row['material'] = {'refPath': '/Game/Interval/Materials/%s.%s' % (_mat, _mat)}

# WORDS THAT ARE PANELS, and must lie ALONG the line they belong to.
#
# A fence, a hedge and a railing are each longer than they are thick, and a run
# of them only reads as a barrier if every piece faces down the run. They all
# faced one way, which was right on whichever axis the mesh pointed down and
# ninety degrees wrong on the other -- so a rectangular pen came out with two
# solid sides and two sides of panels standing across their own line.
#
# Palisades and roofed walls are NOT here: those are built as masonry on a
# different path entirely, and telling them to turn would fight it.
ALIGNED = ('fence', 'hedge', 'railing', 'wall', 'wall.unroofed', 'wall.stone')

props = have['Props']

# ---------------------------------------------------------------------------
# THE WORDS THE WORLD RENAMED, STILL SITTING IN THE WINDOW.
#
# `magic-rock` became `quick-rock` and `rampart` became `palisade`. Both
# renames reached the engine and the generator and stopped there, and because
# `have` is rebuilt from the level's actor on every run the dead rows would be
# carried for ever.
#
# A dead word is not harmless. It is a table claiming to answer for something,
# and while `magic-rock` sat here looking like a rock that was handled, the
# thirteen `quick-rock` nodes standing in the Wilds were drawn as nothing at
# all. The stale row is exactly what made the missing one easy to miss.
#
# Tools/undrawn.py reports this in both directions now, so a third rename
# cannot do it again quietly.
for _dead in ('magic-rock', 'rampart'):
    props.pop(_dead, None)

# ---------------------------------------------------------------------------
# WHAT A DROP LOOKS LIKE LYING ON THE GROUND.
#
# Loot was invisible: the frame carried it, the window drew nothing, and the
# only way to know a beast had left anything was to read the socket. It is also
# the one thing a citizen is actively looking for after a fight.
#
# `dropped` is the fallback and most drops use it -- bones, ore, seeds and logs
# have no mesh of their own and do not need one to be seen and stood on. A
# `dropped.<item>` entry overrides it where the item HAS art, so a dropped
# hatchet is a hatchet rather than a bag.
#
# Small, low and flat: this is a thing you stand ON -- the world refuses a
# pickup unless the citizen is on the tile, unlike buying and gathering, which
# want adjacency -- so it must not look like furniture you walk up to.
def _lying(mesh, s=0.5, z=0.0):
    return {'mesh': {'refPath': GEAR_PATH(mesh)}, 'material': None,
            'scale': {'x': s, 'y': s, 'z': s}, 'zOffset': z,
            'yawJitter': 360.0, 'scaleJitter': 0.10, 'bCastShadow': True,
            'parts': [], 'heightJitter': 0.0}

props['dropped'] = _lying('Pouch_Large', 0.75)
for _item, _mesh, _sz in (
        ('logs',   'Anvil_Log',     0.55),
        ('ore',    'Crate_Metal',   0.34),
        ('seeds',  'Pouch_Large',   0.60),
        ('forage', 'FarmCrate_Apple', 0.34),
        ('arrows', 'Bag',           0.45)):
    props['dropped.' + _item] = _lying(_mesh, _sz)

for k, v in TOPS.items():
    if k in props: props[k]['heightJitter'] = v
for k in ALIGNED:
    if k in props:
        # `bAlignToRun`, WITH THE b. This asset keeps Unreal's prefix on its
        # booleans -- bCastShadow, bHideWhenDepleted -- and a key that is not a
        # property is dropped in silence: the write succeeds, the flag never
        # arrives, and the fences stay exactly as wrong as they were. Written
        # once as `alignToRun` and it cost a whole round of "I thought you
        # fixed the fence".
        props[k]['bAlignToRun'] = True
        # AND A PANEL HAS TO REACH ITS NEIGHBOUR. A tile is 200cm and the fence
        # cube was scaled to 180, so even a correctly turned run had twenty
        # centimetres of daylight at every post.
        if k in ('fence', 'railing'):
            _sc = props[k].get('scale') or {}
            _sc['x'] = 2.0
            props[k]['scale'] = _sc
for k, v in PARTS.items():
    if k in props: props[k]['parts'] = v
# A landmark is eighty-nine different things wearing one cylinder. Keyed
# `landmark.<kind>`, each gets its own; anything not named here still falls
# back to the plain `landmark` entry and is still drawn.
# THE FIRE'S OWN BODY, BEFORE THE FLAME IS PUT IN IT.
#
# `hearth`, `campfire` and `watchfire` came out of C++ as a cylinder ninety
# centimetres across and HALF A METRE TALL with a timber colour on it, and
# nothing in this file had ever said otherwise -- so every fire in the world
# was a drum with a flame standing on it. Flattened here to the bed of ash it
# should be; the ring of stones and the logs are `PARTS`, built in parts.py.
for _w, (_mesh, _mat, _sx, _sy, _sz, _z) in FIREBEDS.items():
    if _w in props:
        props[_w]['mesh'] = {'refPath': _mesh}
        props[_w]['material'] = _mat
        props[_w]['scale'] = {'x': _sx, 'y': _sy, 'z': _sz}
        props[_w]['zOffset'] = _z
        # A ring of stone laid by people does not spin; the STONES vary, and
        # that variation is already baked into where each one sits.
        props[_w]['yawJitter'] = 360.0
        props[_w]['scaleJitter'] = 0.04

light(props)
burn(props)
smoke(props)
fill(props)
for k, v in LANDMARKS.items():
    props['landmark.' + k] = v
for k, v in KEEPERS.items():
    props['keeper.' + k] = v

# EVERY TRADE'S STALL EXISTS AS ITS OWN WORD, even though they share a mesh.
# The props table below only touches words that are already here -- it is a
# table of how to draw a thing, not of which things there are -- so each one
# has to be brought into being first, out of the plain `stall` the world falls
# back to. What distinguishes them is added last, after that table: see the
# goods at the foot of this file.
for _trade in STALL_GOODS:
    props['stall.' + _trade] = copy.deepcopy(props.get('stall', {}))
# ...and the plain one goes back to being a modest lump, since it now stands
# for whatever this table has not got to yet rather than for all of them.
if 'landmark' in props:
    props['landmark']['parts'] = []

for k, (s, z, off) in LIFT.items():
    if k in props:
        props[k]['scale'] = {'x': s, 'y': s, 'z': z}
        props[k]['zOffset'] = off


# ---------------------------------------------------------------------------
# AND THE TREES ARE TREES.
#
# Every word in TREES takes a real mesh with its own bark and its own leaves,
# in place of the cone-on-a-cylinder it had. The mesh carries its own
# materials, so `material` is cleared: naming one here would paint bark over
# the canopy. `landmark.` is tried as well as the bare word because the world
# sends most of these as a landmark's sub-kind.
for word, (mesh, scale) in TREES.items():
    for key in (word, 'landmark.' + word):
        if key not in props:
            continue
        props[key]['mesh'] = {'refPath': WOOD(mesh)}
        props[key]['material'] = None
        # AND THE OLD TRUNK COMES DOWN.
        #
        # Every one of these words was a CONE ON A CYLINDER before there were
        # real trees: the cone was the kind's `mesh` and the cylinder was a
        # `part` standing under it. Giving the kind a real mesh replaced the
        # cone and said nothing about the cylinder, so for as long as there
        # have been trees in this world each one has been drawn with a bare
        # timber post beside its trunk -- which is what somebody watching
        # finally named as "the tree seems to have two trunks".
        #
        # The PARTS table already clears these, but it is applied to the bare
        # word and the `landmark.` entries are built AFTER it, so the scenery
        # trees -- which is most of the trees on the island -- never got it.
        # Cleared here, where both keys are in hand, and any piece the table
        # does want is put back: a gallows-oak keeps its gibbet.
        props[key]['parts'] = list(PARTS.get(word) or [])
        props[key]['scale'] = {'x': scale, 'y': scale, 'z': scale}
        # The meshes are modelled standing on the ground, so nothing is lifted.
        props[key]['zOffset'] = 0.0
        props[key]['yawJitter'] = 360.0
        props[key]['scaleJitter'] = max(props[key].get('scaleJitter', 0.0), 0.14)
        props[key]['bCastShadow'] = True

# And which of the five each tree is. The node's own id picks; see
# FIntervalPropKind::Variants.
for word, meshes in VARIETY.items():
    for key in (word, 'landmark.' + word):
        if key not in props:
            continue
        props[key]['variants'] = [{'refPath': WOOD(m)} for m in meshes]

# And the furniture, the same way. The mesh carries its own materials and its
# own legs, so both the material and the assembled `parts` are cleared -- four
# sticks under a real table is four sticks through the floor.

# ---------------------------------------------------------------------------
# THE CC0 PACKS, WIRED.
#
# Same shape as FURNITURE below and deliberately BEFORE it, so that anything
# the older table also claims still wins -- this is the new art, and a word
# that already had a considered answer keeps it until somebody looks at both.
#
# Each scale here was MEASURED on import, not guessed: see `VILLAGE` in
# parts.py for why the Medieval Village pack is multiplied and the other two
# are not.
_villaged = []
for word, (mesh, scale, yaw) in list(VILLAGE.items()) + list(VILLAGE2.items()):
    for key in (word, 'landmark.' + word):
        if key not in props:
            continue
        props[key]['mesh'] = {'refPath': mesh}
        props[key]['material'] = None      # the packs carry their own colours
        props[key]['parts'] = []
        props[key]['scale'] = {'x': scale, 'y': scale, 'z': scale}
        props[key]['zOffset'] = 0.0
        props[key]['yawJitter'] = yaw
        props[key]['scaleJitter'] = 0.05
        props[key]['bCastShadow'] = True
        _villaged.append(key)
# A BOAT THAT IS UPSIDE DOWN OR WRECKED HAS TO LIE THAT WAY. `pitchOffset` and
# `rollOffset` are what the ridge rocks already use; nothing else in the tables
# above needs them, so they are set here rather than widening every row.
for _w, _pitch, _roll in (('landmark.upturned-boat', 0.0, 180.0),
                          ('landmark.shipwreck', 7.0, 24.0)):
    if _w in props:
        props[_w]['pitchOffset'] = _pitch
        props[_w]['rollOffset'] = _roll

# THE STALLS KEEP THEIR GOODS. `parts` is what STALL_GOODS hangs on the
# trestle and it is the only thing telling a bowyer from a baker, so unlike
# the loop above this one leaves it alone.
_stall_mesh, _stall_scale, _stall_yaw = STALL_MESH
for _key in [k for k in props if k == 'stall' or k.startswith('stall.')]:
    props[_key]['mesh'] = {'refPath': _stall_mesh}
    props[_key]['material'] = None
    props[_key]['scale'] = {'x': _stall_scale, 'y': _stall_scale, 'z': _stall_scale}
    props[_key]['zOffset'] = 0.0
    props[_key]['yawJitter'] = _stall_yaw
    props[_key]['bCastShadow'] = True
    _villaged.append(_key)

print('village: %d words drawn from the new packs' % len(_villaged))

# IT HAS TO RUN LATE, AND THAT COSTS SOMETHING THAT MUST BE PAID BACK.
#
# Late, because `landmark.*` and `stall.*` do not EXIST as words until the
# tables above have created them -- moved earlier, this loop matched five words
# instead of twenty-four and said so.
#
# What it costs: this loop ASSIGNS `parts`, because a real mesh replaces the
# primitives that were standing in for it, and `fill()` has already put the
# water into the wells by now. So the water is put back, below. The same trap
# caught the fires first -- the campfire came back as a bare pile of wood with
# no flame on it -- and that one is fixed at the source, in parts.py, where the
# firewood is set before `burn()` ever runs.
fill(props)

# ---------------------------------------------------------------------------
# THE WORDS THE WINDOW HAD NO ROW FOR AT ALL.
#
# These are not stand-ins being upgraded -- the props table had no key for any
# of them, so the world could hand one over and the window would draw NOTHING
# and log it once. See `UNSEEN` in parts.py for how they were found and for
# what the engine says each one is.
#
# A row is CREATED here where there is none, which is why this loop does not
# check `key in props` the way every other one does.
_unseen = 0
for word, (mesh, scale, yaw) in UNSEEN.items():
    row = props.get(word) or {}
    row['mesh'] = {'refPath': mesh}
    row['material'] = None
    row['parts'] = list(row.get('parts') or [])
    row['scale'] = {'x': scale, 'y': scale, 'z': scale}
    row['zOffset'] = row.get('zOffset') or 0.0
    row['yawJitter'] = yaw
    row['scaleJitter'] = 0.06
    row['bCastShadow'] = True
    props[word] = row
    _unseen += 1

print('unseen: %d words that had no row at all now have one' % _unseen)

# ---- THE SOWN GROUND ----
#
# A bed of turned earth with a crop standing in it. This has to run AFTER the
# village loops (which clear `parts`) and BEFORE nothing in particular, and it
# is the only prop in the file whose parts are generated rather than listed --
# because six plants in two offset rows is arithmetic, and writing them out by
# hand is how a row ends up with five.
_mesh, _mat, _sx, _sy, _sz, _bz = PLOT_BED
for _w, (_plant, _n, _s, _gap) in PLOTS.items():
    if _w not in props:
        continue
    props[_w]['mesh'] = {'refPath': _mesh}
    props[_w]['material'] = _mat
    props[_w]['scale'] = {'x': _sx, 'y': _sy, 'z': _sz}
    props[_w]['zOffset'] = _bz
    # THE STAGES, not one set of parts. See `plot_stages` in parts.py. `parts`
    # is left empty deliberately: a kind with stages never reads it, and
    # leaving the ripe crop in there would have every unsown plot drawing a
    # full harvest for one frame before the stage was picked.
    props[_w]['parts'] = []
    props[_w]['stages'] = [{'at': _at, 'parts': _pieces}
                           for _at, _pieces in plot_stages(_plant, _n, _s, _gap)]
    props[_w]['ripeTicks'] = GROW_TICKS_RIPE
    props[_w]['yawJitter'] = 0.0      # a bed is dug square to the field
    # AND IT DOES NOT WOBBLE IN SIZE, for the reason a fence panel does not:
    # now that neighbouring beds MEET, a four per cent jitter is a sixteen
    # centimetre gap at one joint and an overlap at the next, and a field of
    # those reads as broken ground rather than as ploughing.
    props[_w]['scaleJitter'] = 0.0
    props[_w]['scaleJitter'] = 0.04
    props[_w]['bCastShadow'] = True
print('sown: %d beds' % len(PLOTS))

for word, (mesh, scale, yaw) in FURNITURE.items():
    for key in (word, 'landmark.' + word):
        if key not in props:
            continue
        props[key]['mesh'] = {'refPath': GEAR(mesh)}
        props[key]['material'] = None
        props[key]['parts'] = []
        props[key]['scale'] = {'x': scale, 'y': scale, 'z': scale}
        props[key]['zOffset'] = 0.0
        props[key]['yawJitter'] = yaw
        props[key]['bCastShadow'] = True
# ---------------------------------------------------------------------------
# AND THE GROUND GROWS PLANTS.
#
# The scatter meshes carry their own materials, so `material` is cleared: a
# fern painted with the old flat grass instance is a green fern-shaped pebble,
# which is no better than the ball it replaced.
for ground, (mesh, scale, chance, tries) in UNDERFOOT.items():
    k = have['Scatter'].get(ground)
    if not k:
        continue
    k['mesh'] = {'refPath': WOOD(mesh)}
    k['material'] = None
    k['scale'] = {'x': scale, 'y': scale, 'z': scale}
    k['zOffset'] = 0.0
    k['perTile'] = chance
    k['perTileCount'] = tries
    k['yawJitter'] = 360.0
    k['scaleJitter'] = 0.30
    # A tuft of grass casting a shadow costs more than the tuft is worth, and
    # there are tens of thousands of them. A MOUNTAIN IS NOT A TUFT: the ridge
    # is the one thing here big enough that its shadow is most of what makes it
    # read as high ground from directly above, and there are a few thousand of
    # it rather than tens of thousands.
    k['bCastShadow'] = (ground == 'ridge')
    if ground == 'ridge':
        # Less wander than a planting. A ridge is one mass of rock; boulders
        # that vary wildly read as a gravel pit rather than as a mountain.
        k['scaleJitter'] = 0.22

# What the window closes a roof's perimeter with where the world names no wall.
for r in have['Roofs'].values():
    r['wallMaterial'] = TIMBER
    # HOW FAR THE DAUB IS CARRIED BELOW THE FLOOR.
    #
    # A building is levelled onto ONE height -- the eased ground under the
    # middle of its footprint -- because a building has a floor and a floor is
    # flat. The field under a five-tile house on a slope is not, so the ground
    # at a far corner can sit a hand's breadth above or below that one height,
    # and where it sits below there is a line of daylight under the wall.
    #
    # Forty centimetres was the allowance while every building started at sea
    # level and the only variation was the ground's own roughness. Ninety
    # covers the slope as well, and costs nothing: what is carried below the
    # floor is under the ground everywhere it is not needed.
    r['footing'] = 90.0
    # NOT `MI_PropTimber`: that one cannot cut away, and a door is hung in a
    # wall that does. See the note beside MI_WallDoor in make_prop.py.
    r['doorMaterial'] = {'refPath': '/Game/Interval/Materials/MI_WallDoor.MI_WallDoor'}

# WHERE THE WINDOW MAY NOT BUILD A WALL. Of the tiles ringing a roofed room,
# every one that carries a wall stands on raw country or a trail; the one or
# two that carry nothing stand on `flag` or `cobble`, and not one walled tile
# in the measurement stood on either. The generator lays a threshold at the
# door. Naming those two here is the whole of what the window knows about it.
have['Thresholds'] = ['flag', 'cobble']

# ---------------------------------------------------------------------------
# WHAT A CROSSING IS MADE OF.
#
# The world names a road over water `bridge`, and until now the window's whole
# answer to that was to refuse to sink it: a way is graded and water lies in a
# basin, so a bridge tile came out at the road's height with the river a metre
# and a half below and solid earth between them. What that draws is a causeway
# -- an embankment with a road on top -- and it was reported from the stream
# as a cliff edge, which is exactly right.
#
# Both pieces were already in the project and had never been placed by
# anything: the Ruins kit ships a stone deck slab with a low kerb along each
# long edge, and a four-metre pier with a base, a capital and a cutwater
# footprint. Everything about the SHAPE of a crossing -- which way it runs,
# how wide it is, where the piers fall -- the chunk reads off the world's own
# tiles; this says only what the stone looks like.
_SPAN_MESH = '/Game/Interval/Ruins/%s.%s'


def _kerb_rise(obj_name):
    """How far the deck's kerb stands above the part people walk on, in cm.

    MEASURED, because the slab is hung from the top of its bounding box and on
    a kerbed deck that is the top of the KERB. Hanging the road there sinks the
    paving by the kerb's height and everybody on the bridge floats a hand's
    breadth above it. Unreal can ask a mesh for its box and not for its
    surface; this can read the vertices, so it does.

    The paving is the commonest height in the upper half of the mesh -- a deck
    is mostly deck -- and the kerb is the highest point there is.
    """
    import collections
    path = os.path.join(SP, '..', 'Art', 'Ruins', obj_name + '.obj')
    ys = [float(l.split()[2]) for l in open(path) if l.startswith('v ')]
    if not ys:
        return 0.0
    lo, hi = min(ys), max(ys)
    tops = collections.Counter(round(y, 3) for y in ys if y >= lo + (hi - lo) * 0.5)
    paving = tops.most_common(1)[0][0]
    return round((hi - paving) * 100.0, 1)      # the kit imports at a hundred


have['Span'] = {
    'deck': {'refPath': _SPAN_MESH % ('BridgeSection', 'BridgeSection')},
    'deckMaterial': None,        # the kit dressing already gave it stone
    # The slab's local +X carries its kerbs, which is the axis that must run
    # across the way. This kit is modelled that way round, so no turn.
    'deckYaw': 0.0,
    'deckKerb': _kerb_rise('BridgeSection'),
    'pier': {'refPath': _SPAN_MESH % ('Column_BridgeSupport', 'Column_BridgeSupport')},
    'pierMaterial': None,
    # A rank a side every second tile. Every tile is eighteen columns a side on
    # the crossing east of Anchor, which reads as a wall and not as a bridge.
    'pierEvery': 2,
    # HOW DEEP THE CHANNEL UNDER A CROSSING IS DUG, in centimetres below the
    # road. Water lies 150 below the land, which leaves a metre of daylight
    # under a deck a third of a metre thick -- a crack, not a crossing. This is
    # a DRAWING and not a depth: the chunk digs the triangles and leaves every
    # height anything stands at exactly where it was, so a citizen on the
    # bridge is on the road in this window and in every other.
    'channel': 330.0,
    'channelEase': 3,
    # A wall along each side, built rather than borrowed: no kit in this
    # project has a parapet, and the kit deck's own kerb is nine centimetres,
    # which is invisible from the camera this window looks through.
    'parapet': 78.0,
    'parapetThick': 30.0,
    # The wall along each side BELOW the deck, between the arches. At this
    # camera the deck hides everything under it, so the spandrel is the only
    # part of a bridge's structure that can actually be seen.
    'spandrel': 150.0,
}
print('span: deck kerb measured at %.1f cm' % have['Span']['deckKerb'])

# ---------------------------------------------------------------------------
# WHAT EACH GROUND SOUNDS LIKE.
#
# Keyed by the world's own word, the same way the meshes are. The window holds
# no opinion that a moor is bleak; this table says the word `moor` is played as
# that piece, and a world using a word with no entry is simply not scored.
#
# The themes are the ones the browser window plays, which is the point: a
# citizen who knows Anchor by its music should know it here too. `theme-flat`
# and `theme-deep` are that window's own arrangements rather than places, so
# they are not mapped to any ground.
def snd(n):
    return {'refPath': '/Game/Interval/Audio/%s.%s' % (n, n)}

AMBIENCE = {
    'amb_open':  ['meadow', 'heartlands', 'trail', 'trodden', 'chalk', 'gravel', 'downs'],
    'amb_high':  ['moor', 'crags', 'mountain', 'scree', 'wilds'],
    'amb_wood':  ['forest', 'greenwood'],
    'amb_fen':   ['fens', 'peat'],
    'amb_sea':   ['sea', 'shingle', 'sand'],
    'amb_river': ['river', 'bridge', 'causey'],
    'amb_deep':  ['cave'],
    'amb_town':  ['floor', 'flag', 'cobble', 'plaza'],
}
MUSIC = {
    'theme_hearth':  ['heartlands', 'meadow'],
    'theme_anchor':  ['floor', 'flag', 'cobble', 'plaza'],
    'theme_road':    ['trail', 'trodden', 'causey', 'bridge', 'greenwood', 'forest'],
    'theme_downs':   ['downs', 'chalk', 'shingle', 'sand'],
    'theme_crags':   ['crags', 'mountain', 'scree', 'gravel'],
    'theme_fens':    ['fens', 'peat'],
    'theme_moor':    ['moor'],
    'theme_wilds':   ['wilds'],
    'theme_gallery': ['cave'],
}
# ---------------------------------------------------------------------------
# HOW A CITIZEN MOVES WHILE THE WORLD SAYS THEY ARE DOING A THING.
#
# `walk`, `attack`, `attackp`, `gather` and `raise` are the engine's own words,
# read straight off a citizen's `action`. `still` and `felled` are the window's:
# the world says nothing about a citizen who is doing nothing, and it reports
# hit points rather than announcing a death.
#
# Every working verb LOOPS. A deed takes a while and the world keeps saying it
# is happening, so a swing that plays once leaves a citizen frozen mid-chop for
# the rest of the interval; looping it reads as working at something. Dying is
# the exception -- it is the one thing that happens exactly once.
MN = '/Game/Characters/Mannequins/Anims'
def mot(path, loop=True, rate=1.0):
    n = path.rsplit('/', 1)[-1]
    return {'anim': {'refPath': '%s.%s' % (path, n)}, 'bLoop': loop, 'rate': rate}

have['GlowMesh'] = {'refPath': '/Engine/BasicShapes/Sphere.Sphere'}
have['GlowMaterial'] = {
    'refPath': '/Game/Interval/Materials/M_IntervalGlow.M_IntervalGlow'}
# Long grass and hedgerow, not a flagged market square. Glow-worms want damp
# rough ground with something to climb; these are the words for that here.
have['GlowGround'] = ['meadow', 'heartlands', 'downs', 'moor', 'fens', 'peat',
                      'greenwood', 'forest', 'wilds', 'trail']

have['RainMesh'] = {'refPath': '/Engine/BasicShapes/Cylinder.Cylinder'}
have['RainMaterial'] = {
    'refPath': '/Game/Interval/Materials/M_IntervalRain.M_IntervalRain'}
# ---- EIGHTEEN METRES, AND IT RIDES WITH THE LENS NOW ----
#
# It was forty-five, and the note here said why: at fourteen you could see
# where the rain stopped, because the drum was centred on the CITIZEN and the
# camera sits well off their shoulder, so its far wall came into view as a
# clean vertical line with a dry village behind it. Widening the drum pushed
# that wall out of shot.
#
# It also pushed the RAIN out of shot, and that is the fault that was reported
# from the window: "rain starts far away from the character, the character
# never walks in rain". This curtain is a HOLLOW drum with the streaks on its
# inside wall and nothing in between, so a forty-five metre one centred on a
# citizen leaves them in a dry hole with weather around the horizon, while the
# ground at their feet wets anyway because the ground material reads the
# weather number for itself. The two halves of the world disagreed in plain
# sight.
#
# The drum follows the CAMERA now rather than the citizen (see IntervalHour),
# so the wall is a fixed distance from the eye whatever the camera is doing and
# the old complaint cannot come back: there is no angle from which its far side
# is nearer than its near side. Eighteen metres puts the near wall just beyond
# arm's reach and the far wall past anything the eye is reading, and the
# citizen is comfortably inside it.
have['RainRadius'] = 1800.0
# Below zero, the world decides. Above, this does -- for looking at weather
# that is not happening. It lives on the ASSET because a level-placed actor's
# saved property beats the C++ default, silently, which is how an hour went
# into photographing dry meadows and wondering why the override did nothing.
# THE LAMP OVER WHOEVER IS INDOORS. Tuned here rather than in C++, because
# every previous round of it cost a build and an editor restart to see one
# number. See IntervalLook.h.
# Measured against the exposure by photographing a lit room at each: 160 left
# the room black, 400 blew the floor out and took the citizen with it, 320 is
# a hearth. By day the sky is doing most of the work through a dissolved roof
# and cut walls, so the lamp only has to stop the corners going flat.
have['LampByDay'] = 110.0
have['LampByNight'] = 320.0
have['LampReach'] = 1050.0

have['ForceRain'] = -1.0
# And the cloud, which is the one that actually decides whether a day is grey.
have['ForceCloud'] = -1.0
# ---- HOW MUCH COLOUR, AND WHAT THE LIGHT IS CALLED WHITE ----
#
# The picture sat at the renderer's own neutral: saturation barely touched and
# NO white balance at all, which is 6500K, noon under a clear sky. A world of
# thatch, timber, cut stone and hearths is not a noon-lit world and it read
# cold -- "a little too bland, should we have more saturation and contrast for
# a warmer and cosier look".
#
# MEASURED on the same frame at Anchor, land only, with the sim restarted
# between the two because `AIntervalAir` composes once at BeginPlay and never
# ticks: warmth (mean red minus blue) goes from -3.3 to +7.8, which is the
# difference between a picture leaning blue and one leaning red. Thatch goes
# gold, the earth goes red, the water stops being steel.
#
# Both are knobs on the look, beside the contrast, for the reason that one
# gives: it is a matter of taste and this world is looked at on a lot of
# different screens.
have['FilmColour'] = 1.25
have['FilmWarmth'] = 7600.0
# And the mark a click leaves. See `MarkMaterial`: one unlit translucent
# material for every mark, with the colour and the fade carried in the mesh.
have['MarkMaterial'] = {
    'refPath': '/Game/Interval/Materials/M_IntervalMark.M_IntervalMark'}
# ---- AND THE GROUND'S OWN MATERIAL, WHICH NOTHING IN CODE OWNED ----
#
# `AIntervalGround` takes the look's GroundMaterial if it has one and falls
# back to its own, which was set by hand on the actor in the level and had been
# the real answer for as long as anybody could remember -- the look's was None.
#
# That is a pointer stored in a .umap and nowhere else, and `make_ground.py`
# DELETES AND RECREATES the material asset every run, by design, so that the
# file on disk is the only thing deciding what it contains. The first time that
# ran, the level's pointer was left dangling and the whole island went one flat
# colour: no furrows in a field, no cobbles in a street, no water in a pond,
# because every tile read the same default control texture. It took a careful
# before-and-after of the same frame to see that the shader change under
# suspicion was innocent and the REBUILD was the fault.
#
# So the look names it, apply.py runs after every rebuild, and the level's own
# pointer stops being load-bearing.
have['GroundMaterial'] = {
    'refPath': '/Game/Interval/Materials/M_IntervalGround.M_IntervalGround'}
# And the hour, for the same reason and with the same rule: below zero the
# world decides. Set it to 0.9 to photograph something at noon without waiting
# the better part of an hour for one.
have['ForceDay'] = -1.0
# HOW MUCH OF THE SKY REACHES THE GROUND. One is the capture taken at face
# value, which put a black face on everything the sun could not see. See the
# note on `SkyLift` in IntervalLook.h -- this number is meant to be looked at,
# not derived.
# ---- HOW MUCH OF THE LAND'S HEIGHT THE WINDOW DRAWS ----
#
# One is the island as the generator computed it; zero is flat, which is what
# this window drew before it was given the field at all. It is a dial because
# the question is a matter of looking: "when it was flat it looked great",
# "it doesn't look like a small hill, it looks weird", "maybe we just
# shouldn't draw elevation at all" -- three times from the stream, and an
# argument is not what settles that.
#
# The world does not care either way. The elevation field routes roads and
# nothing else reads it, so flat and hilly are the same world drawn twice.
# ZERO, FOR NOW, AND THE REASON IS IN THE PICTURES.
#
# Photographed from one spot at one hour with the dial at 1 and at 0: on the
# sloped version the PAVING SHEARS. Its stones go from square to
# parallelograms and the pattern kinks along a line -- which is exactly what
# was reported, three times, in the words "the slopes and hills look off",
# "weird distorted angles" and "it doesn't look like a small hill, it looks
# weird". Flat, the same stones are square and the town reads cleanly.
#
# IT IS NOT THE HEIGHT, IT IS THE MESH. The ground is a grid of quads, each
# split into two triangles on the same diagonal, and the material draws its
# pattern from the interpolated UV. Lift the four corners to different heights
# and the quad is no longer planar, so the UV interpolates differently in each
# of its two triangles and the pattern kinks along the diagonal they share.
# Every quad on the island kinks the same way, which is why it reads as a
# weave of angles rather than as a hill.
#
# So this is a stopgap and says so. The island can have its height back the
# day the ground material derives its pattern from WORLD POSITION instead of
# from the interpolated UV, which no quad's shape can distort.
have['LandRelief'] = 0.0

# ---- AND THIS IS WHY THE DAY WAS GREY ----
#
# Six was written here, and the note in IntervalHour that explains why six is
# wrong was written AFTERWARDS and never made it back into this file. So the
# measurement existed, the reasoning existed, and the asset still carried the
# number the reasoning rejects -- which is the worst of the three states to be
# in, because reading the engine said one thing and running it said another.
#
# At six the sky light stood at 6.4 against a sun of 2.9. More than two thirds
# of all the light in the world arrived from a source that casts no shadow, so
# every surface was lit from every direction at once: no shadow under the
# eaves, no shaded side on a wall, no shape in a roof. Photographed at the
# palisade at Millbrook, over the land only and ignoring the sky, dropping six
# to 2.2 moves the contrast from 0.179 of the mean brightness to 0.220 and the
# chroma from 0.138 to 0.152. In the picture it is not subtle: the wall gets a
# shadow, the thatch gets a slope, the fire goes orange and the field goes
# green.
#
# It must be judged NORMALISED. The raw contrast and chroma both fall as the
# lift comes down, simply because the whole frame is darker, and reading those
# two numbers alone says six is best. It is the ratio to the mean that says
# what the eye says.
#
# If the shaded side of a wall ever goes too dark, the answer is `Occlusion`
# below and not another lift here. That is what the engine's note says and it
# is right: lifting this is paying for shadow detail with every shadow in the
# world.
have['SkyLift'] = 2.2      # see the note in IntervalHour: this is DAYLIGHT
                           # ambient now, and the night has its own factor

# A CHIMNEY for every hearth under a roof. The stack stands on the roof over
# the fire -- the world says a fire burns on that tile, and the roof builder
# now keeps how high its own surface is there, so nothing guesses.
have['ChimneyMesh'] = {'refPath': '/Engine/BasicShapes/Cube.Cube'}
have['ChimneyMaterial'] = {'refPath': '/Game/Interval/Materials/MI_PropStone.MI_PropStone'}
have['ChimneyWidth'] = 62.0
have['ChimneyRise'] = 155.0
have['ChimneyCapOut'] = 15.0
have['ChimneyCapHigh'] = 22.0

# ---- AIR YOU CAN SEE LIGHT IN ----
#
# The level has had a height fog from the beginning and it has only ever been
# a tint on the horizon. Turning the volumetric path on makes it a medium: the
# sun throws shafts, every hearth glows in the air around it after dark, and
# the smoke that now leaves every chimney is lit from the side rather than
# pasted over the village.
# THE NIGHT SKY. The engine's own sphere, turned inside out by a two-sided
# material; what is drawn on it comes from the view ray, so the dome's size and
# position never enter into it.
have['StarMesh'] = {'refPath': '/Engine/BasicShapes/Sphere.Sphere'}
have['StarMaterial'] = {'refPath': '/Game/Interval/Materials/M_IntervalStars.M_IntervalStars'}

# AND THE RAINBOW, on a second sphere of the same kind. The world has reported
# `rainbow` in every frame's sky since the beginning and nothing drew it:
# "maybe occasional rainbow after rain". Where it sits is not a placement, it
# is an angle -- forty-two degrees from the point opposite the sun -- so the
# shader is given the sun and works the rest out; see Tools/bow.hlsl.
have['BowMesh'] = {'refPath': '/Engine/BasicShapes/Sphere.Sphere'}
have['BowMaterial'] = {'refPath': '/Game/Interval/Materials/M_IntervalBow.M_IntervalBow'}
# FAINT, DELIBERATELY. A share of one drawn at full strength is a stripe of
# pure hues, which is a rainbow in a painting. A real one you have to look for.
have['BowStrength'] = 0.85

# AND THE BIRDS. Forged rather than borrowed -- the bestiary's raven is a
# PERCHED bird and from this camera a folded pair of wings is a dark lump --
# and flapped in the vertex shader by its own master, the same way the grass
# bends and the chain swings. See Tools/wings.hlsl.
have['BirdMesh'] = {'refPath': '/Game/Interval/Forged/bird.bird'}
# ---- AND WHICH BIRD FLIES OVER WHICH COUNTRY ----
#
# The voices were split four ways after "crows in moor instead of regular bird
# song" and the picture was not: one mesh flew over all twenty-seven grounds.
# A citizen on the moor heard crows and watched a songbird; on the shore they
# heard gulls and watched a crow.
#
# The same grouping the voices use, so what you hear and what you see are the
# same animal. `Tools/blend/fowl.py` builds all four from one set of measured
# numbers: a gull is not a pale crow, it is a longer, narrower, more swept wing
# on a shorter body, and that is what tells them apart at a few pixels.
def _fowl(mesh, hue):
    return {'Mesh': {'refPath': '/Game/Interval/Forged/%s.%s' % (mesh, mesh)},
            'Hue': {'refPath': '/Game/Interval/Forged/Hues/%s.%s' % (hue, hue)}}


SKYBIRDS = {
    # the shore, where the gulls already call
    ('gull', 'Fleece'): ['sea', 'shingle', 'sand'],
    # the green and settled country, which is what a songbird belongs to
    ('songbird', 'Fur'): ['meadow', 'heartlands', 'downs', 'chalk', 'trail',
                          'trodden', 'gravel', 'forest', 'greenwood', 'river',
                          'bridge', 'causey', 'fens'],
    # the towns, which had meadow songbirds purely because nobody chose
    ('dove', 'Cloth'): ['floor', 'flag', 'cobble', 'plaza'],
    # and the high bleak ground keeps the crow, which is what `bird` is: moor,
    # crags, mountain, scree, wilds and peat fall through to it on purpose.
}
have['SkyBirds'] = {w: _fowl(m, h) for (m, h), words in SKYBIRDS.items() for w in words}
# AND HOW MANY STAND ON THE GROUND. `AIntervalSmallLife` puts them on the shore
# and in the paved squares, where they lift when a citizen walks into them --
# the first small life in this window that reacts to anybody at all.
have['StandingCount'] = 16

# ---- AND THE LEAVES, WHICH ARE THE SEASON MADE VISIBLE ----
#
# The world has computed spring, autumn and winter since the sky was written
# and nothing in this window had ever read them: the seasons changed the date
# and nothing else. Leaves fall in `forest` and `greenwood`, and the COUNT is
# the peak rather than the constant -- `AIntervalSmallLife` multiplies it by
# the season, which is a petal climbing to one in the middle of autumn, so a
# wood turns, drifts and goes bare without the window being told which week it
# is. Gold and rust together, because a wood that has all turned at once is a
# colour filter and a wood turning is a wood.
have['LeafMesh'] = {'refPath': '/Game/Interval/Forged/leaf.leaf'}
have['LeafGold'] = {'refPath': '/Game/Interval/Forged/Hues/Gold.Gold'}
have['LeafRust'] = {'refPath': '/Game/Interval/Forged/Hues/Ember.Ember'}
have['LeafCount'] = 26
have['BirdMaterial'] = {'refPath': '/Game/Interval/Forged/Hues/FeatherWing.FeatherWing'}
# ELEVEN IN A SKEIN AND ONE SKEIN A MINUTE OR SO, which is spacing and not
# stinginess: the same reasoning as the birdsong they fly beside, where the
# file is eight per cent sounding and the rest gaps. A sky with a steady supply
# of birds in it is an aquarium.
have['FlockSize'] = 11
have['FlockEvery'] = 42.0

# AND WHAT LIVES ON THE GROUND. The last of the four things asked for in one
# line: "maybe a frog here and there hopping around on the ground in the fens".
# Scenery and not a mob: nothing here is in any frame and nothing can be struck.
# `AIntervalSmallLife` puts them only where the world's own word for the ground
# is wet, which is the same rule the crows and the gulls follow.
have['FrogMesh'] = {'refPath': '/Game/Interval/Forged/frog.frog'}
have['FrogMaterial'] = {'refPath': '/Game/Interval/Forged/Hues/Herb.Herb'}
# SEVEN, which is a fen. Forty would be a plague, and a frog is thirteen
# centimetres: what carries at this distance is the hop, not the count.
have['FrogCount'] = 7

# ---- AND THE BUTTERFLIES, OVER THE OPEN GROUND ----
#
# The second half of the same request as the birds: "we added birds in the sky
# for atmosphere, but I think we should add like butterflies (closer to the
# ground so they're actually visible) in the farmlands and stuff like that too,
# I think it makes the world more alive."
#
# A crow is eight metres up and reads as a silhouette; this is at knee height
# in the grass a citizen is standing in. `AIntervalSmallLife` puts them only on
# `meadow`, `heartlands`, `downs` and `chalk` -- the open flowering country --
# and takes them away at night, in rain, and in winter.
#
# TWO MATERIALS OVER ONE MESH, because an instanced component carries one
# material and these are two species rather than one species with a tint. The
# pale is the small white, which is most of what is over a field; `Ember` is
# the tortoiseshell, about a third of them, and is the one that makes you look.
have['ButterflyMesh'] = {'refPath': '/Game/Interval/Forged/butterfly.butterfly'}
have['ButterflyPale'] = {'refPath': '/Game/Interval/Forged/Hues/Fleece.Fleece'}
have['ButterflyBright'] = {'refPath': '/Game/Interval/Forged/Hues/Ember.Ember'}
# FOURTEEN, which is a meadow in summer. The frogs are seven and a frog is
# thirteen centimetres sitting still; this is nine centimetres and never still,
# so it takes more of them before a field reads as having butterflies in it
# rather than as having a butterfly in it.
have['ButterflyCount'] = 14

have['bVolumetricAir'] = True
have['HazeDepth'] = 24000.0
# HOW MUCH AIR THERE IS ON A CLEAR DAY, and the reason it is now here at all:
# the hour read this off whatever fog actor the level happened to hold, so the
# single number deciding how far you can see was the only atmospheric value
# nobody was choosing. The island is 896 by 512 tiles and seeing all of it at
# once makes it small; a far shore that goes soft says there is more out there.
# The rain multiplier in IntervalHour still stacks on top of this.
have['AirDensity'] = 0.018
# The shaft knob. Real air scatters forwards and looks it; at zero, fog is fog.
have['HazeForward'] = 0.62
have['HazeTint'] = {'r': 0.82, 'g': 0.86, 'b': 0.96, 'a': 1.0}
have['SunHaze'] = 1.1
# A HEARTH CATCHES FAR MORE OF THE AIR THAN THE SUN DOES, on purpose. From
# this camera a fire's light on the ground is a few pixels and the glow it
# hangs in the air is a soft disc several times the size -- which is most of
# what a lit village looks like from here.
have['FireHaze'] = 3.4
# And how dark it has to be before a glow-worm is out. A twentieth had them
# lit in the middle of the afternoon.
have['GlowAfter'] = 0.34

# ---------------------------------------------------------------------------
# THE AIR, AND THE GATE.
#
# These live on the asset because `AIntervalAir` spawns itself UNBOUND at
# priority ten, over anything the level carries. An afternoon went into tuning
# the level's own PostProcessVolume and every property the air overrides was
# quietly winning; the level is the wrong place and `Tools/make_post.py` is
# kept only as the record of that.
#
# Pinned exposure: minimum equal to maximum, so the hour is the only thing
# that changes how bright the picture is. Below zero would keep the automatic
# band, which is narrow (0.12 to 1.4) and compresses a night towards a day by
# about three and a half stops rather than cancelling it outright.
have['ExposureAt'] = 0.62
# How hard the tonemapper crushes the dark end. The air's own default was
# 0.62, at which a palisade's north face and a canopy's far side land on the
# flat of the curve and come out black.
have['FilmToe'] = 0.40
have['Occlusion'] = 0.45

# The gate: the plate you come in through, with the theme playing and the
# world turning behind it. `theme_flat` is the world's OPENING track -- it is
# what the browser windows start with on first touch -- and not a region's.
have['bGate'] = True
have['GateTheme'] = {'refPath': '/Game/Interval/Audio/theme_flat.theme_flat'}
have['GateReach'] = 4200.0
have['GateRise'] = 1900.0
have['GateTurn'] = 2.4
# And where it stands once you are in: behind the citizen's shoulder, at the
# same bearing every photograph in these notes was taken from.
# A WINDOW, not a shoulder. At 1250 out and 820 up the camera sits about a
# third of the way up the sky and the citizen is a silhouette against their own
# doorway; the whole point of this one is that you can see the country they are
# standing in.
# THE DUST UNDER A PAIR OF BOOTS. Spawned per unit travelled, so it emits
# nothing at all while somebody stands still and nothing in C++ has to ask
# whether they are walking.
have['StepDust'] = {'refPath': '/Game/Interval/FX/NS_Step.NS_Step'}
have['StepDustScale'] = 1.0
have['StepDustRise'] = 6.0

have['WatchReach'] = 1150.0
have['WatchRise'] = 1380.0
# ---- AND HOW FAR DOWN IT LOOKS, WHICH IS NOW A NUMBER AND NOT A TRIANGLE ----
#
# 1150 out and 1380 up is fifty degrees down, and fifty degrees down is a
# window with NO SKY IN IT. Measured off the live camera rather than guessed:
# the field is fifty-eight degrees tall, so the top of the frame looked
# twenty-one degrees BELOW the horizon, at every zoom -- the wheel scales the
# whole triangle and leaves the angle alone. Nothing in the air could ever be
# seen: not a bird, not weather, and not the rainbow the world has been
# reporting in every frame since the beginning.
#
# The threshold is twenty-nine degrees and it is hard. Twenty-four puts the top
# of the frame five degrees ABOVE the horizon, which is a band of sky about a
# twelfth of the height -- enough to see weather standing over the country and
# birds crossing it, and shallow enough that the citizen is still looked down
# on rather than stood beside.
#
# The slant is kept, so the camera is exactly as far from the citizen as it
# was and only the angle moved. Turn this one number to argue with it.
# NOT AN ANGLE ANY MORE. See `SkyShare` in IntervalLook.h: the same angle gives
# a band of sky on one window shape and none on another, because the vertical
# field is what decides it. Minus one leaves the angle to be worked out.
have['WatchPitch'] = -1.0
have['SkyShare'] = 0.12
have['WatchBearing'] = 218.7
have['WatchLag'] = 2.2
# ---------------------------------------------------------------------------
# THE TOWN WALLS.
#
# Keyed by the WORLD'S OWN WORD. `palisade` is a node type the world uses eight
# hundred and forty-two times in this founding -- a hundred and eighty-six of
# them ringing Anchor, with the gates left as gaps and a `guard` standing in
# each one. The window was already drawing the word, as a scaled cube, which is
# a garden wall; this says how to BUILD it instead.
#
# Nothing here decides where a wall is. A founding that grows a second masonry
# word costs a row and no build.
# THE WALL INSTANCES, NOT THE PROP ONES. They are the same stone and the same
# limewashed timber; what they have that the prop materials do not is the
# cutaway, so the walls of the building a citizen is standing in come down to
# waist height along with its roof. A stone trough keeps MI_PropStone and stays
# whole, which is right: you are not standing inside a trough.
STONE = {'refPath': '/Game/Interval/Materials/MI_WallStone.MI_WallStone'}
# AND A BOUNDARY WORK IS NOT ONE OF THEM. Whatever a town's outer work is made
# of, it is not a room anybody stands inside: cutting it to waist height as
# somebody walks past would read as a town that has been slighted. It keeps its
# whole height. The name is from when this was stone, and the stone material is
# kept here because the ruins and the quay still want it.
CURTAIN = {'refPath': '/Game/Interval/Materials/MI_PropStone.MI_PropStone'}

have['Palisades'] = {
    'palisade': {
        # ---- A PALISADE, NOT A CASTLE ----
        #
        # This was a stone curtain: six and a half metres to the walkway, two
        # and a half thick, with merlons, embrasures and a tower every nine
        # tiles. Anchor and Millbrook are a port and a market. Nobody in this
        # world besieges anybody, there is no siege in the rules and no army to
        # hold one off, and a castle wall round a market says a thing about the
        # place that is not true of it. On the ground it read as a flat grey
        # cliff: a six-metre extrusion with no gate you can see, no walk on top
        # anybody can reach, and nothing about it that says somebody built it.
        #
        # NOTHING CHANGES ABOUT MOVEMENT. The rules still say a boundary work
        # stands on these tiles and the gate rule still finds its mouth where
        # the run stops; nothing walks anywhere it could not walk before. The
        # same builder makes a palisade when the numbers say palisade.
        #
        # THE WORLD'S WORD DID CHANGE, THOUGH, and that is a founding. While
        # this was only a drawing the node could stay `rampart` and no founding
        # was needed. But SPEC fixes the NAME of a thing and forbids a window
        # to disagree, and `rampart` means earth and stone -- so once the
        # drawing became timber, either the picture was wrong or the word was.
        # The node is `palisade` now. See the note beside "A palisade is not a
        # house wall" in SPEC.
        # PLAIN TIMBER, NOT THE TIMBER FRAME. The first cut of this used
        # `TIMBER`, which is the HOUSE WALL material: wattle and daub between
        # a frame, with windows in it. So the town's palisade came out as a
        # continuous run of cottage wall, windows and all, which is worse than
        # the stone it replaced because at least the stone was not pretending
        # to be somebody's front room. Plain plank is what a driven pole should
        # look like.
        # ---- AND IT MUST CUT AWAY, WHICH IS WHY IT IS NOT `MI_PropTimber` ----
        #
        # That reading was right about the colour and wrong about the master.
        # `MI_PropTimber` hangs off the props' master, which is opaque and has
        # no cutaway in it, so of the whole of a town only the stockade stayed
        # standing when a citizen walked in behind it: the roofs lifted, the
        # house walls opened to brow height, and the ring of timber around the
        # outside carried on hiding the person. It was the single worst thing
        # about moving around a town and it looked like a bug in the cutaway,
        # which it was not -- the cutaway was never on this wall.
        #
        # `MI_WallPalisade` is the same six numbers on the wall master. Same
        # timber, same plank spacing, same grain; it opens.
        'material': {'refPath': '/Game/Interval/Materials/MI_WallPalisade.MI_WallPalisade'},
        # Two and a half metres of upright timber: over a person's head, which
        # is the whole job of a stockade, and not a fortification.
        # ---- A TOOTH MUST BE AT LEAST AS WIDE AS THE WALL IS THICK ----
        #
        # This was 55 thick with merlons 25 wide, and 25 is less than half of
        # 55: every tooth was therefore WIDER ACROSS THE WALL THAN ALONG IT, a
        # fin standing square to the run, five of them to every two-metre tile.
        # Reported from the window as "some wall sticking out at a 90 degree
        # angle every meter or something", which is exactly what it was.
        #
        # A stake top is square in plan. So the wall is thinned to 38 and the
        # tooth widened to match it, which also makes a stockade the thickness
        # a stockade is: a run of posts a foot and a bit through, rather than a
        # masonry curtain nearly two feet thick pretending to be timber.
        'height': 250.0, 'thickness': 38.0,
        # The tooth and its gap must DIVIDE THE TILE. A tile is two metres and
        # the teeth are laid out per tile, so a pitch of 2.10 m gave one
        # merlon per tile starting five centimetres before the tile began --
        # which happens to look passable and is arithmetic nobody intended.
        # 1.15 + 0.85 is a tooth and a crenel of about the right proportions
        # for a wall this high, and it lands on the tile exactly.
        # THE TEETH BECOME THE POSTS. A palisade is poles driven side by side
        # and cut off at a point, which is the same geometry as a crenellation
        # at a quarter of the size: a short tooth, a narrow gap, repeated.
        #
        # AND IT STILL HAS TO DIVIDE THE TILE, for the reason the old note
        # gave. A tile is two metres and 25 + 15 is forty centimetres, so five
        # posts land on every tile exactly and the run never drifts.
        # 38 and 12 give four posts to a tile, each one square in plan, with a
        # finger of daylight between them. Anything narrower than `thickness`
        # here comes out as a fin again, whatever the other numbers say.
        'merlonHeight': 45.0, 'merlonWidth': 38.0, 'embrasureWidth': 12.0,
        # No towers on a stockade. Zero puts a post only where the run TURNS,
        # which is a corner pole braced a little heavier, and that is a thing
        # a village actually does.
        'towerEvery': 0, 'towerRise': 85.0, 'towerWiden': 35.0,
        # And a gatepost where the world stopped driving poles: a pair of
        # uprights either side of the opening, which is what a gate is here.
        'gatepostRise': 95.0, 'gatepostWiden': 45.0,
        # The world tells this wall every OTHER tile. One is "close a hole a
        # single tile wide"; a real gate is wider than that and stays open.
        # See the note on CloseGapsUpTo in IntervalLook.h.
        'closeGapsUpTo': 1,
    },
    # AND THE SECOND MASONRY WORD, which is the one above promised would cost
    # a row and no build.
    #
    # `wall` was still a scaled cube -- a 200x200x300 block dropped on each
    # tile, with yaw jitter spinning it and scale jitter shrinking it. Two
    # things follow from that and both were visible the moment anybody walked
    # along one: a square block is as thick as it is long, so a run of them is
    # a row of piers rather than a wall, and a block scaled between 1.83 and
    # 2.05 on a two-metre pitch leaves up to seventeen centimetres of daylight
    # at every joint. Asked plainly -- "are those palisade walls or whatever
    # they are, rotated the wrong way? Shouldn't they connect to form a wall?"
    # -- the answer is that they were never turned at all and never touched.
    #
    # The palisade builder already solves all of it: it lays stone ALONG the
    # run, joins tile to tile, turns corners and leaves the world's gaps
    # alone. A house wall is the same construction at domestic proportions --
    # §7dj is explicit that `house` and `wall` differ in meaning and not in
    # shape -- so it is the same builder with smaller numbers and no teeth.
    'wall': {
        'material': STONE,
        # Three metres and seventy centimetres thick: a wall you shelter
        # behind, plainly not one you defend.
        'height': 300.0, 'thickness': 70.0,
        # NO CRENELLATIONS. A merlon on a cottage is a folly; zero here means
        # the coping runs flat along the top.
        'merlonHeight': 0.0, 'merlonWidth': 0.0, 'embrasureWidth': 0.0,
        # AND NO TOWERS. `towerEvery` of zero is none at all -- a drum tower
        # every nine tiles of a yard wall would be a castle.
        'towerEvery': 0, 'towerRise': 0.0, 'towerWiden': 0.0,
        # A post where a run stops is right at any scale: it is what a wall
        # does where a door is.
        'gatepostRise': 40.0, 'gatepostWiden': 30.0,
        'closeGapsUpTo': 1,
    },
}

# AND EVERY OTHER WORD FOR THE SAME MASONRY.
#
# The builder is keyed on the node's KIND, and the world has four words for a
# wall: `wall`, `wall.roofed`, `wall.unroofed`, `wall.stone`. Moving only the
# first of them meant a settlement was drawn TWICE -- the tiles whose kind was
# `wall` came out as proper coursed masonry, and the tiles with any of the
# other three were still the old scaled cube standing beside it in the
# timber-frame material, which on a two-metre block reads as a black slab. The
# two interleaved, which is why a wall looked like alternating brick and void
# and why nothing about it could be explained by shadow.
#
# They differ in what is ON them, not in what they are made of: §7dj is
# explicit that the words exist to tell a wall you live behind from one you
# shelter behind. So they are the same stone.
# A WALL IS NOT ALWAYS STONE, and the first version of this made every one of
# them so. The settlement went uniformly dark slate, and what had been lost was
# not light but PLASTER: the timber-framed walls of a house are the pale
# surfaces in a village, and replacing them with curtain-wall masonry made a
# hamlet look like a quarry. §7dj again -- the words differ in what you do
# behind them, and a house is rendered as a house.
PLASTER = {'refPath': '/Game/Interval/Materials/MI_WallTimber.MI_WallTimber'}
for _also, _face in (('wall.roofed', PLASTER), ('wall.unroofed', PLASTER),
                     ('wall.stone', STONE)):
    have['Palisades'][_also] = dict(have['Palisades']['wall'])
    have['Palisades'][_also]['material'] = _face
have['Palisades']['wall']['material'] = PLASTER

# ---------------------------------------------------------------------------
# THE PEOPLE, AND WHAT THEY CARRY.
#
# CC0 art by Quaternius: the Universal Base Characters, the free half of his
# Modular Character Outfits - Fantasy, his Universal Animation Library, and his
# Medieval Weapons. Two packs were tried and dropped before this one and both
# failures are worth writing down, because they were failures of JUDGEMENT and
# not of pipeline:
#
#   KayKit's adventurers are lovely and are CHIBI -- a big-headed four-foot
#   figure looks like a visitor from another game standing next to a timbered
#   house modelled at human scale. Proportion, not polygon count, was the
#   problem.
#
#   Quaternius's older Ultimate Modular Characters have exactly the right
#   proportions and are a MODERN pack: its "Worker" is a hi-vis jacket and a
#   hard hat, its "Adventurer" a business suit and tie. Only the women's
#   Medieval and Witch belonged here at all.
#
# This one is fantasy on purpose: peasants in linen and leather, rangers in
# hooded green. Four outfits, two bodies, ONE SKELETON between all of them and
# the animation library -- which is why there is a single motion table again.
#
# A citizen is TWO MESHES: the bare body, which is where the head, the eyes,
# the hair and the hands come from, and the outfit over it, which stops at the
# collar. The body goes first: the first part carries the animation and its
# bounds decide what is drawn, and a headless figure is what an outfit alone
# gives you.
UNI  = '/Game/Interval/Universal'
QUAT = '/Game/Interval/Quaternius'

MALE   = UNI + '/Base/Superhero_Male_FullBody.Superhero_Male_FullBody'
FEMALE = UNI + '/Base/Superhero_Female_FullBody.Superhero_Female_FullBody'

# WHAT IS ON THEIR HEAD. The base body has a face, eyes and eyebrows and no
# hair at all, so without these every citizen in the world is the same shaven
# man. They are listed PER OUTFIT and picked by a different slice of the
# citizen's key than the outfit itself, so four outfits and four heads of hair
# is sixteen people rather than four.
#
# The rangers get none: they are hooded, and a bun through a hood is worse than
# no bun. A bald man under a hood is just a man under a hood.
def hair(*names):
    return [{'refPath': '%s/Hair/%s.%s' % (UNI, n, n)} for n in names]

MENS_HAIR    = hair('Hair_SimpleParted', 'Hair_Buzzed', 'Hair_Beard', 'Hair_Long')
WOMENS_HAIR  = hair('Hair_Long', 'Hair_Buns', 'Hair_BuzzedFemale', 'Hair_SimpleParted')

def outfit(body, worn, hairdos=None):
    return {'parts': [{'refPath': body},
                      {'refPath': '%s/People/%s.%s' % (UNI, worn, worn)}],
            'hair': hairdos or [],
            'motions': {}}

def anim(name):
    return '%s/Anims/UAL%s.UAL%s' % (UNI, name, name)


# AND THE SECOND LIBRARY.
#
# Quaternius's Universal Animation Library 2, CC0, on the same rig bone for
# bone -- sixty-seven names, checked against the first before a clip of it was
# imported. It exists because the first library ran out: it has forty-three
# clips and none of them is a throw, a chop, a sowing, a carry or a shield, so
# a javelin was thrown by slashing the air, an oak was felled with a sword
# swing, and a hauler carrying a consignment across the island leaned on it.
#
# Every row that names one of these says WHY it is better than what it
# replaced, because a borrowed clip that reads wrong is a placeholder and the
# only way to tell the two apart is to say which is which.
def anim2(name):
    return '%s/Anims2/UAL2%s.UAL2%s' % (UNI, name, name)


def m2(name, loop=True, rate=1.0, held=None, pace=0.0):
    """A motion out of the second library. Same shape as `m`."""
    return {'anim': {'refPath': anim2(name)}, 'bLoop': loop, 'rate': rate,
            'held': held or {'pieces': []}, 'bHoldsTool': held is not None,
            'pace': pace}

# WHAT A PERSON CARRIES, out of two CC0 kits: Quaternius's Medieval Weapons
# for the blades and bows, and his Fantasy Props for the two things no weapon
# pack had -- a PICKAXE and a TORCH, both of which are words this world uses.
KIT = {n: '%s/Kit/%s.%s' % (QUAT, n, n) for n in (
    'Arrow', 'Axe', 'Axe_Double', 'Axe_Small', 'Bow_Evil', 'Bow_Golden',
    'Bow_Wooden', 'Bow_Wooden2', 'Claymore', 'Dagger', 'Dagger_2',
    'Hammer_Double', 'Hammer_Small', 'Scythe', 'Shield_Celtic_Golden',
    'Shield_Heater', 'Shield_Heater_2', 'Shield_Round', 'Shield_Round_2',
    'Spear', 'Sword', 'Sword_2', 'Sword_Big', 'Sword_Golden')}
KIT.update({n: '/Game/Interval/Props/%s.%s' % (n, n) for n in (
    'Pickaxe_Bronze', 'Torch_Metal', 'Axe_Bronze', 'Sword_Bronze',
    'Shield_Wooden', 'Whetstone')})

# The rig is EPIC'S OWN -- root, pelvis, spine_01..03, clavicle_l, hand_r,
# index_01_l -- which is worth knowing twice over: the bone is `hand_r`, and
# any animation made for the Unreal mannequin will play on these people
# without retargeting. It also has real finger bones, so this hand is oriented
# like a hand. The engine's simple mannequin had none, its `hand_r` X ran up
# the arm for want of anything below it to define otherwise, and that is how a
# hatchet came to hang behind somebody's shoulder for an afternoon.
# ---- AND HOW IT SITS IN THE FIST ----
#
# Every one of these was hung on the bone with NO ROTATION AT ALL, which means
# each kit item was worn however its author happened to model it. Reported from
# a photograph: "the way he holds the shield and hatchet is a little .. off."
#
# It was worse than off and it is measurable. Read the bone's own axes out of
# the pose the window was showing, and a mesh whose blade runs +Z -- which is
# how this whole kit is modelled, checked against the bounds of the sword, the
# spear, the dagger and the hatchet -- came out pointing (-0.15, 0.53, -0.83)
# in the body's own space. That is a hatchet held HEAD DOWN, hanging behind
# the leg, which is exactly what the picture shows. The shield, whose face is
# its local +Y, faced (-0.46, 0.78, 0.42): tipped up at the sky.
#
# So the grip is a rotation and the rotation is derived rather than dialled.
# The two numbers below are the answer to "what relative rotation puts the
# blade up and a little forward, and the shield's face out from the body", in
# the pose the idle holds. It is a BONE-space rotation, so it is the same
# grip in every pose afterwards: a hand that turns turns what it is holding.
#
#   blade (+Z local)  -> ( 0.05,  0.60,  0.80)   up and forward
#   edge  (+X local)  -> (-0.04,  0.80, -0.60)   facing the way they face
#   shield face (+Y)  -> ( 0.38,  0.92,  0.05)   out from the body
#   shield top  (+Z)  -> (-0.02, -0.05,  1.00)   up
#
# THE PROJECT'S OWN PROPS ARE NOT TOUCHED. `parts.HATCHET`, `PICKAXE` and `ROD`
# were authored for this hand and already sit right; only the two CC0 kits
# needed telling which way round they were.
# The same two numbers as `parts.GRIP_WEAPON` and `parts.GRIP_SHIELD`, which
# is where the derivation is written down. They are repeated rather than
# imported because this file's `hand` and that file's `held` are two spellings
# of the same idea and joining them is a bigger change than this was.
GRIP_WEAPON = dict(pitch=68.5, yaw=102.7, roll=-164.0)
GRIP_SHIELD = dict(pitch=-9.1, yaw=-132.6, roll=-155.1)
# AND WHERE ALONG ITSELF EACH IS HELD; see `parts.GRIP_WEAPON_OFF` for the
# reasoning. Both meshes are modelled about their middle, so the axe hung a
# quarter of its haft below the fist and the shield stood up past the ear.
GRIP_WEAPON_OFF = dict(ox=1.0, oy=12.1, oz=-4.6)
GRIP_SHIELD_OFF = dict(ox=8.0, oy=-10.3, oz=13.6)


def hand(mesh, bone='hand_r', s=1.0, ox=None, oy=None, oz=None,
         pitch=None, yaw=None, roll=None):
    # The grip, unless a caller has a reason of its own. `hand_l` is the off
    # hand and the only thing held there is a shield.
    grip = GRIP_SHIELD if bone == 'hand_l' else GRIP_WEAPON
    where = GRIP_SHIELD_OFF if bone == 'hand_l' else GRIP_WEAPON_OFF
    if pitch is None: pitch = grip['pitch']
    if yaw is None:   yaw   = grip['yaw']
    if roll is None:  roll  = grip['roll']
    if ox is None: ox = where['ox']
    if oy is None: oy = where['oy']
    if oz is None: oz = where['oz']
    # The mesh's own correction, from parts.py, so no caller here carries a
    # number for it and no later table can outrank it.
    k = s * MESH_SCALE.get(mesh, 1.0)
    return {'pieces': [{
        'mesh': {'refPath': KIT[mesh]},
        'material': None,
        'offset': {'x': ox, 'y': oy, 'z': oz},
        'rotation': {'pitch': pitch, 'yaw': yaw, 'roll': roll},
        'scale': {'x': k, 'y': k, 'z': k},
        'bCastShadow': True, 'bone': bone}]}

# The gathering tools, at last with the right heads on them: a hatchet for
# wood, a PICKAXE for stone rather than the two-handed hammer that stood in for
# one, and -- see THE ROD below -- a rod over the water rather than a spear.
# THE AXE CAME OUT THE SIZE OF A DOOR. Every other hand tool in this kit sits
# right at 1.0, so the scale is not a global mistake -- `Axe_Small` is simply
# authored several times larger than the rest of the set, and hung on the hand
# bone unscaled it reached from the citizen's fist to well past the tree they
# were cutting. Measured off the screen against a citizen at 1.8 m, it was
# about five and a half times what it should be.

AXE  = hand('Axe_Small')
PICK = hand('Pickaxe_Bronze')
HAMR = hand('Hammer_Small')
TORCH = hand('Torch_Metal')
BOW  = hand('Bow_Wooden')

# ---- THE ROD, WHICH ALREADY EXISTED ----
#
# Fishing was drawn as a citizen KNEELING WITH A SPEAR, and it was noticed the
# first time anybody looked at it: "and kneeling with a fishing rod? Isn't that
# weird?" -- which is the right question, and the answer is that it was not a
# rod and they were not fishing. They were playing a repair animation with a
# weapon in their hand.
#
# Two separate faults, and they are worth keeping separate:
#
#   THE POSE. `Fixing_Kneeling` is somebody down on one knee working at
#   something on the GROUND in front of them. It was chosen because "kneeling
#   at the water's edge" sounds right written down. Watched, the hands are
#   busy at the dirt and the head is down: it reads as mending a wheel, and no
#   part of it is aimed at the water. What fishing looks like from this camera
#   is a figure STANDING STILL with a long thin thing out over the water, and
#   the standing still IS the deed -- the silhouette is the rod, not the body.
#
#   THE TOOL. It was a spear, which has a blade on it, chosen because the
#   weapons kit has no rod in it. But THIS PROJECT ALREADY HAS ONE: `parts.ROD`
#   -- a 170cm tapering timber pole with a cloth line hanging off the tip,
#   built out of primitives the same way every well and gibbet in the world is,
#   and already hung on any citizen carrying the `rod` item. The motion had
#   simply never been told about it. A thing this window can already draw was
#   substituted for with a worse thing, which is the failure the placeholder
#   rule exists to catch.
def m(name, loop=True, rate=1.0, held=None, pace=0.0):
    # `pace` is the ground speed the clip was cut for, in centimetres a
    # second; see FIntervalMotion::Pace. Only locomotion has one -- a hatchet
    # swing is not faster because its owner was running a moment ago.
    return {'anim': {'refPath': anim(name)}, 'bLoop': loop, 'rate': rate,
            'held': held or {'pieces': []}, 'bHoldsTool': held is not None,
            'pace': pace}

# ---------------------------------------------------------------------------
# EVERY DEED GETS A BODY.
#
# Eight motions covered a world with sixty-nine verbs in it. Everything else a
# citizen did -- cooking, smithing, planting, fletching, brewing, buying,
# burying -- was drawn as a person standing perfectly still, because there was
# nothing in the table to draw instead. The instruction is flat: "we need to
# add animations for everything if that wasn't implied."
#
# WHY IT WAS NOT SIMPLY A MISSING TABLE ENTRY. The world admits exactly five
# kinds of `action` -- `gather`, `attack`, `attackp`, `walk`, `raise` -- and
# every other deed resolves inside the interval it was asked for. Asked what a
# citizen is doing on the tick they cooked a fish, the world answers `null`,
# and it is right: the fish is cooked. So there was no word to key on, and
# adding rows here alone would have changed nothing. The window now remembers
# what its own hand filed for a beat afterwards -- see
# UIntervalBridgeSubsystem::Doing -- and these are the rows that beat draws.
#
# WHAT THE CLIPS ARE. This pack has forty-three of them and none was cut for a
# medieval trade, so every row below is a borrowed clip and the only question
# that matters is what the SILHOUETTE says at this camera. They are grouped by
# what the BODY does, not by what the deed means, because that is the only
# thing a viewer can actually see:
#
#   kneel and work at the ground   planting, kindling, burying, cooking
#   reach and handle               fletching, brewing, grinding, reading
#   stoop and take                 picking up, buying, drawing from a chest
#   swing a tool                   smithing, breaking a thing apart
#   lean into it                   hauling, raising a stall, working bellows
#   talk with the hands            offering, swearing, chartering, asking
#   cast                           spells
#   hold a light up                lighting a torch
#   draw a bow                     nocking
#
# Where a clip is a stretch it is said so on the row rather than left to be
# found, which is the standing rule about placeholders in this project.
MOTIONS = {
    'still':   m('Idle_Loop'),
    # TWO HUNDRED IS ONE TILE AN INTERVAL, which is as fast as anybody in
    # this world moves -- so at full speed the walk plays exactly as it always
    # did, and everything slower than that now moves its legs slower too.
    'walk':    m('Walk_Loop', pace=200.0),
    'move':    m('Walk_Loop', pace=200.0),
    'gather':  m('PickUp_Table', rate=0.9),
    'attack':  m('Sword_Attack'),
    'attackp': m('Punch_Cross'),
    'felled':  m('Death01', loop=False),
    'hurt':    m('Hit_Chest', loop=False),
}

# ---- LEAN INTO IT ----
# `raise` IS THE WORLD'S WORD FOR BUILDING A MARKET STALL -- §6al, "raising a
# stall is work, not a click", twenty intervals of standing in the open with
# your goods on you. It was drawn as `Spell_Simple_Shoot`: a citizen putting up
# a trestle table fired a magic missile at it for twenty seconds. Leaning into
# something heavy is what the deed is.
# `dismantle` joined them when the motions were counted rather than assumed:
# taking a thing apart is the same work as putting it up, and it had been
# standing perfectly still while it happened.
# `stoke` LEFT THIS GROUP. Working a bellows is leaning on something; feeding a
# log to a watchfire is a stoop, and it belongs with the rest of the fire.
for _lean in ('raise', 'raise_market', 'smelt',
              'dismantle', 'dismantle_market', 'unmake'):
    MOTIONS[_lean] = m('Push_Loop', rate=0.7)
# EXCEPT HAULING, WHICH IS WALKING WITH SOMETHING HEAVY. `haul` and `unload`
# were in the list above and should never have been: a consignment is carried
# across the island, not shoved, and `Push_Loop` is a person leaning on a thing
# that is not moving. The second library has the carry.
# `haul` IS THE MOMENT OF TAKING IT UP, not the carrying. The world files the
# deed once and the citizen then WALKS with the load for as long as it takes to
# cross the island, so the carry belongs on the walk and not here.
MOTIONS['haul'] = m('PickUp_Table', rate=0.8)
MOTIONS['unload'] = m2('Chest_Open', loop=False)
# AND THE WALK, FOR AS LONG AS THEY HAVE IT. The window already knows who is
# carrying a consignment -- it draws the crate, see bCarryingLoad in
# IntervalCitizens.cpp -- and every hauler on the island walked as though their
# hands were empty while a crate rode on their shoulder. `walk.hauling` is the
# same refinement `gather.<node>` and `attack.<weapon>` use.
MOTIONS['walk.hauling'] = m2('Walk_Carry_Loop', pace=200.0)

# ---- KNEEL AND WORK AT THE GROUND ----
# The clip that was wrong for fishing is right for these: the hands ARE at the
# ground, which is where you put a seed, a body, a foundation or a pot on a
# fire.
# `stoke` and `offer` joined it. A log goes INTO a fire the way a pot goes onto
# one, and goods given up at an ossuary are left at the stone the way grave
# goods are: both were elsewhere because nobody had looked at what the act is.
for _kneel in ('setbuck', 'kindle', 'light_fire', 'grave', 'stoke', 'offer',
               'bury', 'lay', 'found', 'cook', 'dedicate', 'seal'):
    MOTIONS[_kneel] = m('Fixing_Kneeling', rate=0.75)
# EXCEPT THE FARMING, WHICH HAS ITS OWN CLIPS NOW. Planting a seed, watering a
# bed and taking a crop off it were the same repair-kneel, and they are three
# different things a person does standing up. The second library has all three
# cut for exactly these deeds, which is rare enough to be worth saying.
MOTIONS['plant'] = m2('Farm_PlantSeed', loop=False)
MOTIONS['sapling'] = m2('Farm_PlantSeed', loop=False, rate=0.8)
# (`Farm_Watering` is imported and NOT used. This founding has no watering
#  verb -- the engine's cases are plant, sapling, harvest, taking, ripe, rot
#  and withering, and none of them is a can tipped at a bed. It is left unwired
#  rather than hung on a verb it does not describe, which is the same rule the
#  bestiary keeps for a crow drawn as a bat.)
MOTIONS['harvest'] = m2('Farm_Harvest', loop=False)

# ---- REACH AND HANDLE ----
# Work at waist height with both hands: a fletcher's bench, a still, a quern, a
# chart on a table. `Interact` is a single reach-and-do and it loops, which is
# what any of these looks like repeated.
# `brew` and `saw` left it, and `charter` and `turn` arrived. Tipping food into
# a pot of water is a POUR, and a saw is a stroke against resistance; neither is
# a reach. Drawing up a charter is a chart on a table, which is the example this
# comment already used, and changing the book you speak from was standing
# perfectly still.
for _handle in ('fletch', 'transmute', 'build_brewpot', 'grind', 'make',
                'char', 'stamp', 'sound', 'read_chart', 'look', 'charter',
                'set_look', 'claim_name', 'recall', 'waking', 'attend',
                'calling', 'ripe', 'rot', 'taking', 'withering', 'restore',
                'archive', 'spawn', 'survey', 'turn'):
    MOTIONS[_handle] = m('Interact', rate=0.85)
# ---- §7dn/§7dq: THE TWO GAPS NOBODY WALKS THROUGH ----
#
# The squeeze into the Whitechalk barrow and the Smother's mouth. Both are a
# hole in rock, both refuse a citizen for a reason the ground decides, and both
# were drawn as an ordinary stride -- so entering either one was a figure
# walking upright into a hillside, which is the thing that reads as teleporting
# rather than as going in.
#
# `Crouch_Fwd_Loop` had never been used and is exactly the shape: the body low
# and still moving forward. It loops, because a squeeze is as long as the gap
# is, and it is paced off the walk so a citizen pushing through does not
# suddenly scramble.
MOTIONS['squeeze'] = m('Crouch_Fwd_Loop', pace=200.0, rate=0.8)

# A BREW IS A POUR. The second library has one and nothing was using it.
MOTIONS['brew'] = m2('Farm_Watering', loop=False)
# AND A SAW IS A STROKE. `Push_Loop` is a body leaning its weight into
# something that does not give, which is a saw through a log exactly.
MOTIONS['saw'] = m('Push_Loop', rate=0.95)
# EATING IS NOT REACHING ACROSS A BENCH. `Interact` is a hand going out to a
# thing at waist height, which is fair for a quern and wrong for a loaf: the
# hand goes to the MOUTH. The second library cut one for it.
# §6ba: AND FORAGE IS BOTH. It is taken off the ground and eaten in the same
# interval, and it is the mouth that makes it read as forage rather than as a
# citizen pocketing something, so it goes with eating rather than with taking.
for _consume in ('eat', 'drink', 'forage'):
    MOTIONS[_consume] = m2('Consume', loop=False)

# ---- STOOP AND TAKE ----
# Anything that moves a thing between the ground, a shelf, a chest and a pack.
# It is the same motion `gather` already uses and that is not a coincidence:
# from above, picking a turnip and taking a loaf off a stall are one gesture.
#
# AND IT HAPPENS ONCE, so it must not loop. Every one of these is an instant
# deed: the world records it for exactly one interval and then the word is
# gone. The clip is 0.92 seconds at this rate, which is just inside an
# interval, so a looping row restarted it with a tenth of a second left and the
# figure snapped back to the start of the reach before the deed was over. Short
# enough to be easy to miss, exactly long enough to look like a glitch.
#
# `gather` is NOT in this list and keeps its loop on purpose. It is the same
# clip and the opposite case: an action that runs on by itself for as long as
# the tree lasts, where restarting the reach is the whole point.
for _take in ('pickup', 'drop', 'collect', 'buy', 'lift', 'release',
              'deliver', 'pay', 'stock_market', 'price_market', 'take_market',
              'wield', 'unwield', 'gear', 'nock_arrow'):
    MOTIONS[_take] = m('PickUp_Table', loop=False, rate=0.9)
# EXCEPT THE ONES THAT ARE A CHEST. Drawing from a hoard, putting something
# into it, going through a dead hauler's cart: the hands go to a lid at knee
# height and lift it, which is a different gesture from taking a turnip off the
# ground and is the one the second library cut.
for _chest in ('withdraw', 'deposit', 'deposit_all', 'consign', 'rifle'):
    MOTIONS[_chest] = m2('Chest_Open', loop=False)

# ---- TALK WITH THE HANDS ----
# Every deed that is really two people agreeing something. None of them moves
# anything, and a figure gesturing is the only honest picture of a bargain.
# `part` and `teach` joined them for the same reason `dismantle` joined the
# leaners: `audit_motion.py` counted, and these three were the whole of what
# it found. Parting from somebody you were following and teaching an
# apprentice are both two people agreeing something, which is what this clip
# is for.
for _talk in ('offer_trade', 'cancel_trade',
              'befriend', 'unfriend', 'ask', 'follow', 'unfollow',
              'part', 'teach', 'confirm', 'trade'):
    MOTIONS[_talk] = m('Idle_Talking_Loop')

# ---- EXCEPT WHERE SOMETHING IS ACTUALLY PROMISED ----
#
# Four of the deeds above are not talk and were drawn as talk. `accept_trade`
# is the one moment in a bargain when goods cross between two people; the rest
# of the group is the arguing before it. `swear` is a citizen choosing the
# single calling they will master and it cannot be undone. `stint` is an oath
# with a number on it. Drawn as a figure gesturing on a loop, the three biggest
# commitments in the world looked like chatter, and they looked like chatter
# for as long as the loop ran, which for an instant deed is wrong twice over.
#
# A nod, once. It is a small gesture for a large thing, and that is the point:
# it happens and it is over, which is what these deeds are.
for _given in ('accept_trade', 'swear', 'stint'):
    MOTIONS[_given] = m2('Yes', loop=False)

# ---- THE ELEVEN SPELLS ----
#
# Sorcery was one gesture. Every casting verb pointed at `Spell_Simple_Shoot`,
# so transmuting a log, healing a friend and laying the withering on somebody
# were the same magic missile, and the four barrow spells were not wired at
# all. It was worse than it looked: no spell sets an `action`, so until the
# window learned to read `deed` nothing about a cast reached it and the clips
# below had nothing to fire them.
#
# WHAT THERE IS TO WORK WITH. The first pack has four spell clips and only one
# was ever used: `Spell_Simple_Enter` raises the hands, `Spell_Simple_Idle_Loop`
# holds them out, `Spell_Simple_Shoot` sends, `Spell_Simple_Exit` lowers them.
# Four shapes, which is enough to separate sending from holding from drawing
# back. The rest come from the second library.
#
# The two books read differently on purpose. The common book raises its hands
# and holds them: it refuses, repairs and unmakes, and the engine says so, "not
# one hurts anybody". The barrow book reaches, claws and throws.

# ---- the common book ----
# HOLDING A FIGHT STILL is a refusal, and the second library has a refusal.
# `Idle_No_Loop` is not a stretch here: §: "magic is the skill of refusing",
# and the stilling is its capstone at eighty-five.
MOTIONS['still'] = m2('Idle_No_Loop', loop=False, rate=0.9)
# SHUTTING A WAY is bracing something closed.
MOTIONS['seal'] = m2('Shield_OneShot', loop=False)
# TRANSMUTING is a working held over the thing in your hand, and it is the one
# spell you do to an object rather than to a person.
MOTIONS['transmute'] = m('Spell_Simple_Idle_Loop', rate=1.0)
# TAKING A THING APART: the hands open and it comes apart between them.
MOTIONS['unmake'] = m2('Chest_Open', loop=False, rate=0.9)
# CLOSING YOUR OWN WOUNDS is drawn inward, toward yourself.
MOTIONS['mend'] = m('Spell_Simple_Enter', loop=False)
# CLOSING SOMEBODY ELSE'S is sent, and a wand is what sends it.
MOTIONS['mendp'] = m('Spell_Simple_Shoot', loop=False, rate=0.9)
# THE RECALL is the longest thing in the book: a held channel, and you may be
# cut down in the middle of it.
MOTIONS['anchor'] = m('Spell_Simple_Idle_Loop', rate=0.6)
# PRESSING A SIGIL happens at an altar, kneeling, with three stones.
MOTIONS['invoke'] = m('Fixing_Kneeling', rate=0.9)
# `cast` is the world's word for two of the above, told apart by `spell`. The
# window asks for the plain word when it has no finer row, so this is the one
# that catches a cast whose spell the window did not name.
MOTIONS['cast'] = m('Spell_Simple_Shoot', loop=False, rate=0.8)

# ---- the barrow book ----
# THE ROT is clawed downward. `Zombie_Scratch` is the second library's and it
# is the only clip in either pack that reaches and tears.
MOTIONS['rot'] = m2('Zombie_Scratch', loop=False, rate=0.85)
# THE TAKING pulls: the hands come back toward the caster.
MOTIONS['taking'] = m('Spell_Simple_Exit', loop=False, rate=0.8)
# THE WAKING calls something up, so it is a call.
MOTIONS['waking'] = m2('Idle_Rail_Call', loop=False, rate=0.85)
# THE WITHERING is the slowest thing either book does: held out, and long.
MOTIONS['withering'] = m('Spell_Simple_Shoot', loop=False, rate=0.5)

# A WEAPON'S OWN TRICK IS NOT A SPELL, and it had been sharing a row with one.
# The four kinds of `gambit` are handled below on their own terms.
# 0.62 seconds against a one-second deed: looped, the blow landed and then
# began again before the interval was out.
MOTIONS['gambit'] = m('Spell_Simple_Shoot', loop=False, rate=0.8)

# ---- AND THE ONES THAT CARRY SOMETHING ----
# A hammer at an anvil, a torch held up, a bow drawn. These three are the rows
# where the TOOL does the telling and the clip only has to not contradict it.
MOTIONS['smith'] = m('Sword_Attack', rate=0.5, held=HAMR)
MOTIONS['light'] = m('Idle_Torch_Loop', held=TORCH)
# A STRETCH, SAID SO: `Pistol_Aim_Neutral` is a two-handed level aim, which is
# an archer's stance with the wrong grip. It is the only forward-aimed pose in
# the pack and a bow in the hand carries it; watch it before trusting it.
# NOCKING IS FEEDING THE WEAPON, NOT AIMING IT. `Pistol_Aim_Neutral` is the
# arm already out and the shot about to happen, which is the interval AFTER
# this one. The reload is both hands at the chest putting something into the
# weapon, and that is what laying an arrow on a string looks like from above.
MOTIONS['nock'] = m('Pistol_Reload', loop=False, held=BOW)
# A tiller is not a steering wheel, but both are two hands out in front of a
# person who is going somewhere without walking.
MOTIONS['sail'] = m('Driving_Loop')
# ---- STANDING WITH SOMETHING IN YOUR HANDS ----
#
# `still_armed` was a row nothing ever asked for: no verb in the world is
# `still_armed`, and the window never built that name, so it sat in the table
# being counted and never once drawn. Standing keys on what is HELD now, the
# same way a blow does -- see `InHand` in AIntervalCitizens::VerbFor -- so
# these are the rows that name is finally reachable through.
#
# A SHIELD, AT LAST. This world has four of them and a citizen wearing one has
# never been drawn using it: the off hand held a heater shield and the body
# stood exactly as it would empty-handed. `Idle_Shield_Loop` is the second
# library's, and it is a guard: weight on the back foot, shield up and across.
for _shield in ('iron-shield', 'steel-shield', 'quick-shield', 'wooden-shield'):
    MOTIONS['still.' + _shield] = m2('Idle_Shield_Loop')
# AND A BLADE IN THE HAND IS NOT HANDS BY YOUR SIDES. `Sword_Idle` was already
# in the library and already right; it had nothing to be keyed on until now.
for _armed in ('iron-sword', 'steel-sword', 'quick-sword', 'great-sword',
               'bare-blade', 'iron-dagger', 'steel-dagger', 'quick-dagger',
               'barb', 'iron-spear', 'steel-spear', 'quick-spear', 'bone-spear'):
    MOTIONS['still.' + _armed] = m('Sword_Idle')

# ---------------------------------------------------------------------------
# ONE SWING FOR EVERY WEAPON IN THE WORLD, WHICH IS WHAT IT LOOKED LIKE.
#
# `attack` was a single row -- `Sword_Attack` -- and the world has forty-odd
# arms in it. A bowman loosed an arrow by slashing the air; a gunner fired a
# handgonne the same way, holding a gun; a wizard swung a staff like a
# broadsword; the old chain, which is the rarest thing on the island, was
# swung exactly like an iron dagger. `gambit` was worse: the world gives four
# different tricks -- a flurry, a whole-body blow, a spout of fire, a long
# shot -- and all four played a magic missile.
#
# The window now asks for `attack.<what is in the hand>` and falls back to
# `attack`, which is the same rule `gather.<node>` has always used; see
# AIntervalCitizens::VerbFor. So a row is needed only where the body should
# NOT be swinging a blade, and a sword is left alone because a sword swinging
# is what the clip is.
#
# WHAT THERE IS TO WORK WITH. This pack has forty-three clips and three of
# them point forwards: `Pistol_Shoot`, `Pistol_Aim_Neutral` and
# `Spell_Simple_Shoot`. That is enough to separate a shot from a swing and a
# spell from both, and it is not enough for a spear thrust or a chain whirl,
# which have no clip anywhere in the CC0 packs reached so far. Those keep the
# swing and differ by TEMPO, which is said here rather than left to be found.

# A SHOT IS NOT A SWING. `Pistol_Shoot` is a two-handed level discharge, which
# is a bow loosed, a crossbow tripped and a handgonne fired; the weapon in the
# hand is drawn from the world's own equipment, so the same clip reads as three
# different things because three different objects are in it.
for _shot in ('wooden-bow', 'hollow-bow', 'horn-bow', 'heartwood-bow',
              'sigil-bow', 'dragonbow', 'crossbow', 'great-crossbow'):
    MOTIONS['attack.' + _shot] = m('Pistol_Shoot', loop=False)
# A GUN IS SLOWER THAN A BOW and recovers for four intervals; the clip at
# three-quarters speed is the difference between loosing and touching off.
MOTIONS['attack.handgonne'] = m('Pistol_Shoot', loop=False, rate=0.75)
# THE SIPHON IS PUMPED. It is held level and worked, not swung, and what comes
# out of it keeps burning -- so the body does what it does for a gun and the
# fire does the telling.
MOTIONS['attack.fire-siphon'] = m('Pistol_Shoot', loop=False, rate=0.7)

# A STAFF CASTS. `Spell_Simple_Shoot` is the one place it belongs, and these
# are the four words that hold one.
for _staff in ('staff', 'bone-staff', 'heartwood-staff', 'goo-staff', 'wand'):
    MOTIONS['attack.' + _staff] = m('Spell_Simple_Shoot', loop=False, rate=0.9)

# A JAVELIN IS THROWN. Three words in the world are one -- iron, steel and
# quick -- and all three swung a sword while holding a throwing spear, which is
# as wrong as a bow being swung. `OverhandThrow` is the second library's, and
# it is the only clip in either pack that lets go of anything.
for _thrown in ('iron-javelin', 'steel-javelin', 'quick-javelin'):
    MOTIONS['attack.' + _thrown] = m2('OverhandThrow', loop=False)

# A CHAIN AND A FLAIL SWING FASTER THAN A SWORD, and the world says so: the
# old chain lands a blow EVERY interval where a sword lands one in two. There
# is no whirl in any pack here, so this is the swing at the tempo the world
# charges for it, which is the honest half of the difference.
for _whirl in ('old-chain', 'gold-chain', 'quick-flail'):
    MOTIONS['attack.' + _whirl] = m('Sword_Attack', loop=False, rate=1.45)
# A SPADE IS A POOR WEAPON, says §7al, and swings every third interval.
MOTIONS['attack.spade'] = m('Sword_Attack', loop=False, rate=0.6)

# ---- AND THE FOUR GAMBITS, WHICH WERE ONE SPELL ----
#
# The world gives exactly seven weapons a `spec` and there are four kinds of
# it. Drawn as `Spell_Simple_Shoot`, a dagger's flurry and a maul's
# whole-body blow were the same magic missile, and neither looked like what
# the world had just charged for.
#
#   flurry  quick-dagger, horn-bow, handgonne   several blows at once
#   whole   quick-mell, great-mell              one blow with everything in it
#   now     fire-siphon                        it goes off immediately
#   far     dragonbow                          one shot, a long way
# A FLURRY IS FOUR BLOWS, and the second library has them: `Sword_Regular_A`,
# `_B` and `_C` are a three-hit combo and `_Combo` is all of them run together.
# One sword swing played at twice speed is a person swinging faster; this is a
# person landing several blows, which is what §6ag charges the quick-dagger's
# recovery for.
MOTIONS['gambit.quick-dagger'] = m2('Sword_Regular_Combo', loop=False, rate=1.15)
# AND A WHOLE-BODY BLOW IS THE LAST ONE OF THAT COMBO, which is the heaviest
# cut in either library: the feet set, the hips come round, and it takes long
# enough that the four intervals of recovery §6ag charges look earned.
for _whole in ('quick-mell', 'great-mell'):
    MOTIONS['gambit.' + _whole] = m2('Sword_Regular_C', loop=False, rate=0.65)
MOTIONS['gambit.horn-bow'] = m('Pistol_Shoot', loop=False, rate=1.8)
MOTIONS['gambit.handgonne'] = m('Pistol_Shoot', loop=False, rate=1.5)
MOTIONS['gambit.fire-siphon'] = m('Pistol_Shoot', loop=False, rate=1.2)
# A LONG SHOT IS AIMED. Nine tiles is the longest reach in the world and the
# only one worth taking time over, so this is the loose at three-fifths speed.
MOTIONS['gambit.dragonbow'] = m('Pistol_Shoot', loop=False, rate=0.6)

# A swing is a swing; what makes it felling a tree rather than cutting a seam
# is the TOOL and the TEMPO, and the pack has an axe and a mattock.
# AND FELLING IS CHOPPING. This was `Sword_Attack` with an axe put in the
# hand, which is a fencer's cut delivered at a trunk: the blade comes across
# the body rather than down into the wood, and an axe held that way bounces off
# a tree in every frame. The second library has a chop cut for a tree, and it
# loops, which is what felling one is.
for wood in ('tree', 'oak-tree', 'ironbark-tree', 'heartwood-tree',
             'gallows-oak', 'grove-plot'):
    MOTIONS['gather.' + wood] = m2('TreeChopping_Loop', rate=0.85, held=AXE)
for stone in ('iron-rock', 'coal-rock', 'gold-rock', 'quick-rock',
              'mother-lode', 'rockfall', 'salt-pan', 'brimstone-vent'):
    MOTIONS['gather.' + stone] = m('Sword_Attack', rate=0.55, held=PICK)
# FISHING IS STANDING STILL. See THE ROD above for why it is no longer a kneel
# and no longer a spear. `Sword_Idle` is a standing hold that breathes, which
# is exactly what waiting for a bite looks like, and the rod does the rest.
for water in ('fishing-spot', 'deep-fish-spot', 'eel-spot'):
    MOTIONS['gather.' + water] = m('Sword_Idle', rate=0.6, held=ROD)

# EIGHT, NOT FOUR. Every citizen in the world drew from two outfits, so a
# market place was the same two people repeated. The noble and the knight are
# in here deliberately: a town has people of different station in it, and a
# street where everyone is a peasant reads as a costume department rather than
# as a place.
have['Outfits'] = [
    outfit(MALE,   'Male_Peasant', MENS_HAIR),
    outfit(FEMALE, 'Female_Peasant', WOMENS_HAIR),
    outfit(MALE,   'Male_Ranger'),
    outfit(FEMALE, 'Female_Ranger'),
    outfit(MALE,   'Male_Noble', MENS_HAIR),
    outfit(FEMALE, 'Female_Noble', WOMENS_HAIR),
    outfit(MALE,   'Male_Knight_Cloth'),
    outfit(FEMALE, 'Female_Knight_Cloth'),
]
# ---------------------------------------------------------------------------
# AND THE KEEPERS ARE PEOPLE, not posts.
#
# Every keeper in the world was built out of primitives -- a cylinder for a
# body, a cone for a hat -- from before there was a human figure to draw. The
# citizens standing beside them have had real bodies for a long time, so a
# trader was a white post wearing a party hat next to somebody with a face.
#
# It was noticed, as these things are, about the one keeper who is a character:
# Oberon the wizard, who stands in a ring of eight standing stones beside his
# own hearth and was drawn as a tube.
#
# The body is the citizens' own, hung the same way the risen are: `skeletal`
# for the figure and `skeletalParts` for what it is wearing. Their KIT stays --
# a keeper's hat, staff, barrel or sack is what says which trade they are, and
# those are still the primitives they always were, now hung on somebody.
# AND NOW EACH TRADE HAS ITS OWN CLOTHES.
#
# There were two outfits in this project and fourteen keeper trades, so a
# banker, a miller and a shepherd all stood in the same peasant shirt and the
# only thing telling them apart was the hat. The paid tier of the same CC0 kit
# adds a wizard, a noble and two knights, which is enough to dress a town.
#
# The wizard is the one this was bought for: Oberon stands in a ring of eight
# standing stones beside his own hearth, and was a cylinder, then a peasant in
# a ranger's hood. He has a robe now.
KEEPER_WEARS = {
    'wizard':    ('Male_Wizard',    MALE),    # the robe, at last
    'watchman':  ('Male_Knight',    MALE),    # a man with a staff and mail
    'banker':    ('Male_Noble',     MALE),    # money dresses well
    'merchant':  ('Male_Noble',     MALE),
    'mourner':   ('Female_Wizard',  FEMALE),  # robed, which is what a mourner is
    'innkeeper': ('Female_Noble',   FEMALE),
    'shepherd':  ('Male_Ranger',    MALE),    # outdoors, hooded
    'drover':    ('Male_Ranger',    MALE),
    'beekeeper': ('Male_Peasant',   MALE),
    'brewer':    ('Female_Peasant', FEMALE),
    'miller':    ('Male_Peasant',   MALE),
    'collier':   ('Male_Peasant',   MALE),
    'quarrier':  ('Male_Peasant',   MALE),
    'sawyer':    ('Male_Peasant',   MALE),
}
for _trade, _row in KEEPERS.items():
    _key = 'keeper.' + _trade
    if _key not in props:
        continue
    _wears, _body = KEEPER_WEARS.get(_trade, ('Male_Peasant', MALE))
    props[_key]['skeletal'] = {'refPath': _body}
    props[_key]['skeletalParts'] = [
        {'refPath': '%s/People/%s.%s' % (UNI, _wears, _wears)}]
    # THE CYLINDER BODY GOES -- AND IT HAS TO BE THE STRING.
    #
    # `None` here is a JSON null, and this asset does not take a null for an
    # object reference: it wants the four characters "None", exactly as the
    # note on the Mobs table above records. Handed a null it kept the old mesh,
    # so every keeper stood as a human figure with their own discarded cylinder
    # still standing beside them -- which is the pale post next to Oberon.
    props[_key]['mesh'] = 'None'
    props[_key]['material'] = None
    # THE HAT IS ON THE HEAD BONE NOW, so the arithmetic that used to sit it
    # down is gone. It read: anything standing above 190cm -- the top of the
    # 182cm cylinder the hats were authored against -- is moved to 176. Both
    # numbers were guesses at a crown height, and a guess cannot follow a head
    # that moves: the figure's own animation, its height and its scale jitter
    # all put the skull somewhere the tile cannot know about. See `fhat`.
    props[_key]['scale'] = {'x': 1.0, 'y': 1.0, 'z': 1.0}
    props[_key]['zOffset'] = 0.0
    # A person does not spin on the spot, and two keepers facing different ways
    # in one market reads as two people rather than as two copies.
    props[_key]['yawJitter'] = 360.0
    props[_key]['scaleJitter'] = 0.04

have['CitizenParts'] = []
have['Motions'] = MOTIONS
# The art is modelled at human height, and the doorways were cut for it.
have['CitizenScale'] = 1.0
# The art brings its own materials now, one per atlas, and the window keeps
# them and tells each one which citizen is wearing it -- so there is no
# procedural clothing material left to name.
have['PersonMaterial'] = None

# And what the world says somebody is carrying, by its own word for the item.
# EVERY WEAPON THE WORLD HAS A WORD FOR.
#
# Thirty-seven of them in `tables.weapons`, plus the shields out of `prices`
# and the four tiers of hatchet and pickaxe out of `gatherTools`. They are
# grouped by SHAPE, because that is what a mesh is: the world's tiers -- iron,
# steel, quick, great -- are the same weapon better made, and where the kit has
# a plainer and a finer version of a shape the tiers are spent on that.
#
# A word with no entry here is simply not drawn, which is the honest answer for
# a thing this window has never heard of.
WEAPON_MESH = {
    # --- blades ---
    'Dagger':        ('iron-dagger', 'barb'),
    'Dagger_2':      ('steel-dagger', 'quick-dagger'),
    'Sword_Bronze':  ('bare-blade',),
    'Sword':         ('iron-sword',),
    'Sword_2':       ('steel-sword',),
    'Sword_Golden':  ('quick-sword',),
    'Sword_Big':     ('great-sword',),
    'Claymore':      ('bone-sword',),
    # --- hafted ---
    'Axe_Small':     ('iron-hatchet',),
    'Axe':           ('steel-hatchet',),
    'Axe_Bronze':    ('quick-hatchet',),
    'Axe_Double':    ('great-hatchet',),
    'Pickaxe_Bronze': ('iron-pickaxe', 'steel-pickaxe', 'quick-pickaxe',
                       'great-pickaxe', 'spade'),
    'Hammer_Small':  ('iron-mell', 'steel-mell', 'quick-flail'),
    'Hammer_Double': ('quick-mell', 'great-mell'),
    'Scythe':        ('lamprey-spit',),
    # --- poles: spears, javelins, staves and every sort of rod ---
    'Spear':         ('iron-spear', 'steel-spear', 'quick-spear', 'bone-spear',
                      'iron-javelin', 'steel-javelin', 'quick-javelin',
                      'bone-staff', 'staff', 'heartwood-staff',
                      'rod', 'oak-rod', 'ironbark-rod', 'heartwood-rod'),
    # --- what throws things ---
    'Bow_Wooden':    ('wooden-bow', 'crossbow'),
    'Bow_Wooden2':   ('horn-bow', 'heartwood-bow', 'great-crossbow'),
    'Bow_Golden':    ('sigil-bow',),
    'Bow_Evil':      ('hollow-bow', 'dragonbow'),
    # --- light and fire ---
    # (`fire-siphon` and `wand` were here, borrowing the torch. Both are
    #  forged now -- see the tail of parts.py, which overrides this table
    #  anyway and which the pack sprites are rendered from.)
    'Torch_Metal':   ('torch',),
}

# THE HEAD. Six of this world's thirteen armour words are a helm and there was
# no helm in any kit in use; these are CC0 from OpenGameArt (see Art/Armour).
# A helm is RIGID -- it hangs on the `Head` bone the way a sword hangs on
# `hand_r` -- so it needs no rig of its own.
#
# The offsets are a guess to be photographed, not a measurement: a helmet
# modelled by somebody else is not modelled around this skeleton's head.
ARMOUR = {n: '/Game/Interval/Armour/%s.%s' % (n, n) for n in
          ('Helmet1', 'Bucket_Helmet2', 'Iron_Crown',
           'Knight_Helmet1', 'Knight_Helmet2', 'Knight_Helmet3',
           'Knight_ShoulderPads', 'Cuirass')}

def head(mesh, s=1.0, oz=0.0, ox=0.0, pitch=0.0):
    return {'pieces': [{
        'mesh': {'refPath': ARMOUR[mesh]},
        'material': None,
        'offset': {'x': ox, 'y': 0.0, 'z': oz},
        'rotation': {'pitch': pitch, 'yaw': 0.0, 'roll': 0.0},
        'scale': {'x': s, 'y': s, 'z': s},
        'bCastShadow': True, 'bone': 'Head'}]}

# THE TWO .obj FILES CAME IN A HUNDRED TIMES TOO SMALL. Measured, not guessed:
# the helmet and the crown are 0.2 cm across as imported, because an .obj
# carries no unit and these were modelled in metres; the .fbx bucket helm came
# in at 20-25 cm, which is a helmet. A head is about twenty centimetres.
#
# The knight's three helms are 1.6 cm across as imported and a head is about
# twenty, so thirteen. They are here for VARIETY: eight helm words sharing
# three meshes made an army in a uniform, and a great helm and a quick helm
# are not the same object in any world that bothered to name them separately.
HEAD_MESH = {
    'Helmet1':        (100.0, ('iron-helm',)),
    'Bucket_Helmet2': (1.0,   ('great-helm',)),
    'Iron_Crown':     (100.0, ('gold-helm', 'king-shroud')),
    'Knight_Helmet1': (13.0,  ('steel-helm',)),
    'Knight_Helmet2': (13.0,  ('shell-helm',)),
    'Knight_Helmet3': (13.0,  ('quick-helm',)),
}

# THE BODY, which had no art at all until the knight was cut up.
#
# `Cuirass` is a slice out of Quaternius's CC0 Knight -- see Art/Armour/README
# and Tools/slice_obj.py. It hangs on `spine_03` the way a helm hangs on
# `Head`, and it is rolled a quarter turn because the .obj is modelled Y-up
# and arrives lying on its back: a breastplate that reads as a sheet of paper
# is a breastplate photographed edge-on, which is what the first rack of it was.
def plate(mesh, s=1.0, oz=0.0, ox=0.0, pads=None, ps=1.0, pz=0.0):
    """A breastplate, and the pauldrons that go over it.

    TWO PIECES, because one is not enough. The cuirass is a band cut out of a
    knight, open at the neck and the arm holes, and on its own it reads as a
    tub -- it has no shoulder. The same pack's shoulder pads close the top of
    it, and a plate with pauldrons is what anybody means by plate armour.
    """
    def piece(which, size, up, along=0.0):
        return {'mesh': {'refPath': ARMOUR[which]}, 'material': None,
                'offset': {'x': along, 'y': 0.0, 'z': up},
                'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': -90.0},
                'scale': {'x': size, 'y': size, 'z': size},
                'bCastShadow': True, 'bone': 'spine_03'}
    out = [piece(mesh, s, oz, ox)]
    if pads:
        out.append(piece(pads, ps, pz))
    return {'pieces': out}

# A citizen's chest is about forty-two centimetres across and the cut is two
# units wide as imported, so twenty-one is life size; the knight it came off is
# broader than these people, so it is held a little under that.
BODY_MESH = {
    'Cuirass': (20.0, ('iron-plate', 'steel-plate', 'gold-plate',
                       'great-plate', 'quick-plate', 'shell-plate')),
}
# The pads are 2.6 units across as imported and a pair of shoulders is about
# fifty centimetres, so nineteen; they sit at the top of the cuirass.
PAULDRONS = ('Knight_ShoulderPads', 19.0, 22.0)

# The off hand. A shield is held, not worn, and it is held in the OTHER hand --
# which this rig has, properly oriented, because it has fingers.
OFFHAND_MESH = {
    'Shield_Heater':         ('iron-shield',),
    'Shield_Heater_2':       ('steel-shield',),
    'Shield_Celtic_Golden':  ('quick-shield', 'gold-chain'),
    'Shield_Round':          ('old-chain',),
    # (`shell-plate` used to be here, drawn as a wooden shield held in the off
    #  hand, because the body slot had no art. A plate is not a shield.)
    'Shield_Wooden':         (),
}

worn = {}
for mesh, words in WEAPON_MESH.items():
    for w in words:
        worn[w] = hand(mesh)
for mesh, words in OFFHAND_MESH.items():
    for w in words:
        worn[w] = hand(mesh, bone='hand_l')
for mesh, (size, words) in HEAD_MESH.items():
    for w in words:
        # Up onto the crown of the head, not through the middle of it.
        worn[w] = head(mesh, s=size, oz=9.0)
for mesh, (size, words) in BODY_MESH.items():
    for w in words:
        worn[w] = plate(mesh, s=size, oz=4.0, ox=1.0,
                        pads=PAULDRONS[0], ps=PAULDRONS[1], pz=PAULDRONS[2])
# §11d: the runner's load, which is worn art like any other -- it just is not
# worn by choice. Merged last so a founding could override it by name.
worn.update(WORN)
have['Worn'] = worn

# ---------------------------------------------------------------------------
# AND THE REST OF WHAT STANDS ABOUT, out of the two kits.
#
# Both tables are word -> (mesh, scale); the only difference is which kit the
# mesh lives in. The mesh carries its own materials and its own construction,
# so both the material and the assembled primitives are cleared.
# A WORD WITH A MESH AND NO ROW WAS DROPPED IN SILENCE.
#
# This loop only ever DECORATED a row that already existed, so a word named
# here but absent from the asset's table fell straight through the `continue`
# and kept no mesh at all. `quick-rock` was exactly that: thirteen of them
# standing in the Wilds, a minable earthcraft node worth 23 experience, and
# the window drew nothing on the tile. It had a correct entry in NATURE_PROPS
# the whole time -- `Rock_Medium_1` at 0.90 -- and this line threw it away.
#
# The window had been saying so all along, once per rebuild: "the world says
# 'quick-rock' is standing here and this window has no mesh for it". The
# report is worth trusting over any reading of these tables.
#
# So a missing row is now MADE rather than skipped, patterned on the sibling
# named in KIN where there is one. That matters for the flags this file never
# sets -- `bHideWhenDepleted` above all -- which a rock has to share with the
# other rocks or it stays standing after it has been mined out.
KIN = {
    'quick-rock': 'iron-rock',
}
for table, where in ((NATURE_PROPS, WOOD), (PROP_PROPS, GEAR)):
    for word, (mesh, scale) in table.items():
        k = props.get(word)
        if not k:
            k = props[word] = copy.deepcopy(props.get(KIN.get(word, ''), {}))
        k['mesh'] = {'refPath': where(mesh)}
        k['material'] = None
        k['parts'] = []
        k['scale'] = {'x': scale, 'y': scale, 'z': scale}
        k['zOffset'] = 0.0
        k['yawJitter'] = 360.0
        k['scaleJitter'] = max(k.get('scaleJitter', 0.0), 0.16)
        k['bCastShadow'] = True

# ---------------------------------------------------------------------------
# A HEDGE IS NOT A ROW OF SHRUBS.
#
# `hedge` took `Bush_Common` at a uniform 0.85 -- a round bush 1.6m across --
# stamped once per tile. From the side that is a bush; from THIS camera, which
# looks straight down, you see the top of a dense shrub where the leaf cards
# overlap completely, so it reads as a smooth green boulder. Fifty of them in
# rows around the fields at the goblin pound read as a heap of boulders rather
# than as an enclosure, and it was mistaken for a rendering fault twice --
# once for wrong art and once for a level of detail, which `r.ForceLOD 0`
# disproved.
#
# The art is right and the SHAPE was wrong. A hedge is low, clipped and
# CONTINUOUS: wider than its tile so that neighbours merge into one line
# instead of standing apart as beads, and well under head height so a citizen
# is the tallest thing in a field. A tile is 200cm and the bush is 191 wide, so
# 1.15 reaches its neighbour with a little to spare, and 0.46 puts the top at
# about 73cm -- a hedge somebody keeps, rather than one gone wild.
#
# `bAlignToRun` is already set for hedges further up, so a run turns to follow
# its own line; that only reads as a hedge once the pieces actually touch.
if 'hedge' in props:
    props['hedge']['scale'] = {'x': 1.15, 'y': 1.15, 'z': 0.46}
    # Less wander than the other plantings. A kept hedge is level along its
    # top; jitter that is right for scattered bushes makes a clipped line look
    # chewed.
    props['hedge']['scaleJitter'] = 0.05
    props['hedge']['heightJitter'] = 0.06

# ---- AND WHAT IS ON EACH STALL'S COUNTER ----
#
# AFTER the props table, deliberately. Every stall is the same trestle and
# should be -- a market stall IS a trestle under an awning -- but every one of
# them was bare, so the stall selling bows and the one selling fish were the
# same empty table. These are the goods only, hung on the mesh that table has
# just given each word.
#
# An earlier attempt built a whole stall out of cubes further up this file and
# was silently overwritten HERE, which is what happens when two tables both
# think they own a word. The goods go last so there is no argument about it.
for _trade, _goods in STALL_GOODS.items():
    _word = 'stall.' + _trade
    if _word in props:
        props[_word]['parts'] = list(props[_word].get('parts') or []) + list(_goods)


# ---------------------------------------------------------------------------
# ---- AND THE PARTS AGAIN, FOR THE ROWS THAT DID NOT EXIST YET ----
#
# `PARTS` is applied near the top of this file, under `if k in props` -- and
# for FOURTEEN of its twenty-three rows that test was false, because the row
# the parts belong to is created LATER, by one of the kit tables further down.
# The parts were then dropped on the floor without a word.
#
# What that cost, counted against what the generator actually seats: a sawpit
# with no saw frame over it, drawn as a 42cm workbench; an anvil off its block;
# six ferries with no pole; three tollgates with no posts; four smoke racks
# with no rails; a brewpot off its hearth; nine dedications with no head on
# them; and the island's one bellworks with no frame and no bell-roof. The
# sawpit is the one that gives it away -- `audit_size.py` measured it at 42
# centimetres, which is a doll's workbench, and the three timbers that make it
# a sawpit were sitting in a table nobody read.
#
# This is the same fault as the stall above and is written the same way round:
# the late pass is ADDITIVE ONLY. It fills a row whose parts are still empty
# and never touches one that something else has already furnished, so nothing
# here can overwrite a deliberate choice made between there and here.
#
# `landmark` is skipped on purpose. It is the bare fallback for a kind this
# table has not got to yet, and it is cleared further up with a note saying so.
for _k, _v in PARTS.items():
    if _k == 'landmark':
        continue
    if _k in props and not props[_k].get('parts'):
        props[_k]['parts'] = _v


# ---- AND THE ONES WHOSE PIVOT IS NOT AT THEIR FOOT ----
#
# LATE, for the same reason the parts above are late: this ran up with LIFT and
# was quietly overwritten by the kit table that gives `banner` its mesh, which
# sets a zOffset of its own. The banner stayed five feet under the field and
# the only way to tell was to measure it. See `SUNK` in parts.py.
for _k, _up in SUNK.items():
    if _k in props:
        props[_k]['zOffset'] = _up


# ---------------------------------------------------------------------------
# AND THE KEEPERS ARE PEOPLE.
#
# `skeletal` leads and carries the standing animation; `skeletalParts` follows
# its pose. The primitives each keeper was assembled from are cleared, or the
# hat and the cylinder stand inside the person.
# A STALL IS NOT A KEEPER. The world has both words: `stall.arms` is the trestle
# with the goods on it and `keeper.arms` is the armourer standing behind it.
# Turning both into people put a shopkeeper where the shop should be.
# The guards at the gates are people as well. The world stands one in each gap
# it leaves in a town's palisades, and a guard drawn as a cylinder in a gateway
# is the most conspicuous cylinder in the world.
if 'guard' in props:
    KEEPER_FOLK['__guard__'] = KEEPER_FOLK['watchman']

# AND THE KEEPER WHOSE TRADE THE WORLD DOES NOT NAME.
#
# Twenty-two `keeper.<trade>` rows were given bodies and the plain `keeper` row
# -- the one every keeper the frame does not name a trade for actually falls
# back to -- was left exactly as it was found: /Engine/BasicShapes/Cylinder,
# fifty-two centimetres across and a hundred and seventy-five tall, standing
# where a person should be.
#
# It was found the way these things are found, by somebody looking at a room:
# "what is that cylinder in the corner?" It was Delia, a keeper in a house in
# Anchor, whose node carries a `type` and a `name` and no `kind` at all. The
# fallback is not an edge case -- it is what the world hands over most of the
# time -- and it had been invisible because every row anybody thought to check
# was one of the twenty-two.
#
# No hat and no kit, because nothing here knows the trade and guessing one
# would be this window inventing a fact about the world. A person with no
# badge is the honest picture, and it is a person.
KEEPER_FOLK['__any__'] = KEEPER_FOLK['innkeeper']

for trade, folk in KEEPER_FOLK.items():
    for key in (('guard',) if trade == '__guard__'
                else ('keeper',) if trade == '__any__'
                else ('keeper.' + trade,)):
        k = props.get(key)
        if not k:
            continue
        k['skeletal'] = {'refPath': folk['body']}
        k['skeletalParts'] = [{'refPath': folk['outfit']}]
        k['mesh'] = 'None'
        # THE KIT IS NOT THE BODY, AND CLEARING BOTH THREW THE TOOLS AWAY.
        #
        # This cleared every primitive a keeper was assembled from, for the
        # good reason written above: the hat and the cylinder would otherwise
        # stand inside the person. But a keeper's parts are not only their
        # body -- they are the BARREL beside the brewer, the staff in the
        # wizard's hand, the sack at the runner's feet, the anvil by the
        # smith. Measured in the world: `keeper.brewer` came back with
        # `parts: []`, so every trade in every town stood empty-handed and
        # there was no way to tell a brewer from a banker.
        #
        # The hat was the only piece that needed moving and it is ALREADY
        # moved, thirty lines up, where anything sitting above 190cm -- the top
        # of the old cylinder -- is sat back down onto a human crown. So the
        # kit is kept, and what is dropped is the cylinder alone, which is the
        # `mesh` above and was never one of these parts.
        k['parts'] = list(k.get('parts') or [])
        k['material'] = None
        k['scale'] = {'x': folk['scale'], 'y': folk['scale'], 'z': folk['scale']}
        k['zOffset'] = folk['z']
        k['yawJitter'] = 360.0
        k['scaleJitter'] = 0.05
        k['bCastShadow'] = True

# A GUARD IS IN ARMOUR. The world stands one in each gap it leaves in a town's
# palisades, and a man in a hood is not what is standing in a gateway. The
# cuirass and the helm are the same meshes the armour words use, hung on the
# figure as static parts rather than on bones -- a guard at a gate stands
# still, and a part is the cheaper of the two.
if 'guard' in props:
    g = props['guard']
    # ---- THE ARMOUR STAYS AT A FIXED HEIGHT, AND HERE IS WHY ----
    #
    # These three are parts with WORLD offsets -- cuirass at 132cm above the
    # tile, helmet at 172, pauldrons at 150 -- which is the same shape as the
    # fault the keepers' hats had, and hanging them on `spine_02`, `head` and
    # `spine_03` was tried for exactly that reason.
    #
    # It came out WORSE and the change was reverted. On a bone the three
    # pieces read as badges pinned to the chest rather than as armour, and
    # nothing about the guard was reported wrong in the first place. The
    # difference from the hats is that a guard does not move: the world stands
    # one in each gap in a town's palisade and leaves them there, so a height
    # measured from the ground is a height measured from THEIR ground, every
    # time. The hats were broken because keepers differ in height and walk.
    #
    # If this is ever revisited it wants the sizes worked out again from the
    # bone's own frame, not the numbers below, which were chosen against the
    # tile.
    g['parts'] = [
        {'mesh': {'refPath': ARMOUR['Cuirass']}, 'material': None,
         'offset': {'x': 2.0, 'y': 0.0, 'z': 132.0},
         'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': -90.0},
         'scale': {'x': 22.0, 'y': 22.0, 'z': 22.0}, 'bCastShadow': True},
        {'mesh': {'refPath': ARMOUR['Knight_Helmet2']}, 'material': None,
         'offset': {'x': 0.0, 'y': 0.0, 'z': 172.0},
         'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': -90.0},
         'scale': {'x': 13.0, 'y': 13.0, 'z': 13.0}, 'bCastShadow': True},
        # The same pauldrons the plate words wear, so a guard and a citizen in
        # plate are wearing the same armour and not two different ideas of it.
        {'mesh': {'refPath': ARMOUR['Knight_ShoulderPads']}, 'material': None,
         'offset': {'x': 0.0, 'y': 0.0, 'z': 150.0},
         'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': -90.0},
         'scale': {'x': 21.0, 'y': 21.0, 'z': 21.0}, 'bCastShadow': True},
    ]

# ---------------------------------------------------------------------------
# AND THE BEASTS ARE BEASTS.
#
# A mob with a `skeletal` mesh is drawn as a skeletal mesh and the primitive is
# ignored, so the cylinder each of these used to be simply stops being asked
# for. A word not in this table keeps whatever it had.
UNI_PEOPLE = '/Game/Interval/Universal/People/'
for word, row in BEASTS.items():
    mesh, scale, zoff = row[0], row[1], row[2]
    outfit = row[3] if len(row) > 3 else None
    m = have['Mobs'].get(word)
    if not m:
        continue
    m['skeletal'] = {'refPath': BEAST(mesh)}
    # AND WHAT IT IS WEARING. The humanoids in the bestiary are the citizens'
    # own body, which is bare; the outfit follows its pose exactly as it does
    # on a living person. See the note on the table.
    m['skeletalParts'] = ([{'refPath': '%s%s.%s' % (UNI_PEOPLE, outfit, outfit)}]
                          if outfit else [])
    m['material'] = None
    m['scale'] = {'x': scale, 'y': scale, 'z': scale}
    m['zOffset'] = zoff
    m['yawJitter'] = 0.0

# THE RISEN BORROW THE WIGHT'S BODY, AND IT HAS TO HAPPEN BEFORE THE COUNT.
#
# This stood thirty lines BELOW the diagnostic, so every run reported `risen`
# as a word with art and no row -- and then gave it a row immediately after. A
# check that cries wolf is worse than no check: a stale note about unarted
# beasts is exactly what sent a later session shopping for art this project
# already had.
if 'risen' not in have['Mobs'] and 'barrow-wight' in have['Mobs']:
    import copy as _copy
    have['Mobs']['risen'] = _copy.deepcopy(have['Mobs']['barrow-wight'])
    have['Mobs']['risen']['scale'] = {'x': 0.98, 'y': 0.98, 'z': 0.98}

# WHICH WORDS THE BESTIARY NEVER REACHED.
#
# Every loop above and below quietly does `if not m: continue`, so a beast the
# world uses but the Mobs table has no row for keeps the engine primitive it
# was born with -- a goblin stays a green cylinder -- and nothing anywhere says
# so. That silence is the same one that lost the stall goods, and it is worth
# one line of noise to never spend an evening on it again.
_missing = sorted(w for w in
                  (set(BEASTS) | set(WILD_BEASTS) | set(WILD_STILL) | set(DARK_BEASTS) | set(DRILL))
                  if w not in have['Mobs'])
if _missing:
    print('BESTIARY: %d word(s) have art but NO row in Mobs, so they stay '
          'primitives: %s' % (len(_missing), ' '.join(_missing)))
print('BESTIARY: Mobs holds %d rows' % len(have['Mobs']))

# The drill yard: a dummy and a butt are furniture, not animals.
for word, (mesh, scale) in DRILL.items():
    m = have['Mobs'].get(word)
    if not m:
        continue
    m['mesh'] = {'refPath': GEAR(mesh)}
    # THE STRING, not a null. A null object reference comes back out of this
    # asset as the four characters "None", and handing the setter a JSON null
    # instead makes it refuse the WHOLE Mobs map -- which silently left the
    # table half written and eleven of the twenty-two mobs simply gone.
    m['skeletal'] = 'None'
    m['material'] = None
    m['scale'] = {'x': scale, 'y': scale, 'z': scale}
    m['zOffset'] = 0.0

# The skeleton-knight is a person-shaped thing and can wear the same skeleton;
# the dummies and butts are what their names say and stay as they were.
# A WORD THE TABLE NEVER HAD A ROW FOR.
#
# The Mobs map came from the citizens actor and carries twenty-two rows; the
# world names twenty-four. A word with no row is SILENTLY not drawn -- the
# window logs it once and carries on -- so the only way to find one is to ask
# both sides and subtract, which is what Tools/audit.py is for.
#
# `risen` is the fifth of the five words for a corpse that walks, and takes the
# same drained copy of a citizen's own body that the other four do.
#
# (`incursion` is the other missing word and is NOT given a row here. Nothing
#  in the frame says what an incursion looks like, and a cylinder that claims
#  to be one is worse than the gap: the gap is at least findable. It wants
#  asking about before it is drawn.)
# AND THE WILD ONES, out of their own folder. Same shape as the row above; the
# only difference is which kit the mesh came out of.
for _word, (_folder, _scale, _z) in WILD_BEASTS.items():
    _m = have['Mobs'].get(_word)
    if not _m:
        continue
    _m['skeletal'] = {'refPath': WILD(_folder)}
    _m['skeletalParts'] = []
    _m['material'] = None
    _m['scale'] = {'x': _scale, 'y': _scale, 'z': _scale}
    _m['zOffset'] = _z
    _m['yawJitter'] = 0.0

# The rigless ones take `mesh`, not `skeletal`, and are drawn out of a pool
# like every other static thing.
# AND THE DARK ONES, out of the Bestiary kit. Same shape as the row above; the
# only difference is which folder the mesh came out of -- and that this kit is
# NOT CC0 (Quaternius Asset License v1.0, Art/Bestiary/LICENCE-NOTE.txt).
#
# `skeleton-knight` had no art whatever: it was an engine primitive, in a world
# whose Wilds are made of them. It stands 1.82m against a citizen's 1.81m.
for _word, (_folder, _scale, _z) in DARK_BEASTS.items():
    _m = have['Mobs'].get(_word)
    if not _m:
        continue
    _m['skeletal'] = {'refPath': DARK(_folder)}
    _m['skeletalParts'] = []
    _m['material'] = None
    _m['scale'] = {'x': _scale, 'y': _scale, 'z': _scale}
    _m['zOffset'] = _z
    _m['yawJitter'] = 0.0

for _word, (_folder, _scale, _z, _lean) in WILD_STILL.items():
    _m = have['Mobs'].get(_word)
    if not _m:
        continue
    _m['mesh'] = {'refPath': WILD(_folder)}
    _m['lean'] = {'pitch': _lean[0], 'yaw': _lean[1], 'roll': _lean[2]}
    _m['skeletal'] = 'None'
    _m['skeletalParts'] = []
    _m['material'] = None
    _m['scale'] = {'x': _scale, 'y': _scale, 'z': _scale}
    _m['zOffset'] = _z
    _m['yawJitter'] = 360.0

# THE INCURSION'S FIVE FACES, which the table has no rows for at all.
#
# `incursion` is a TYPE and the creature is under it: the world sends `face`
# with every one, and the browser windows have drawn five skins off that word
# since it existed. The rows are minted here rather than read off the actor,
# because the actor never had them -- which is why the audit called `incursion`
# undrawn and why it stayed undrawn until somebody who knows the world said
# what it was.
#
# A row is a copy of a walking corpse, which is already the right silhouette
# and the right rig, with the country's colour painted over the whole of it.
if 'barrow-wight' in have['Mobs']:
    import copy as _copy
    for _word, (_mesh, _scale, _z, _mat, _fit) in FACES.items():
        _row = _copy.deepcopy(have['Mobs']['barrow-wight'])
        _row['skeletal'] = {'refPath': BEAST(_mesh)}
        _row['skeletalParts'] = [{'refPath': '/Game/Interval/Universal/People/%s.%s'
                                  % (_fit, _fit)}]
        _row['mesh'] = 'None'
        _row['material'] = {'refPath': '/Game/Interval/Materials/%s.%s' % (_mat, _mat)}
        _row['scale'] = {'x': _scale, 'y': _scale, 'z': _scale}
        _row['zOffset'] = _z
        _row['yawJitter'] = 0.0
        have['Mobs'][_word] = _row

# ---------------------------------------------------------------------------
# AND WHAT EVERY BEAST DOES WHEN NOBODY IS ASKING.
#
# Every creature in this window with a rig of its own had been standing in its
# BIND POSE since the first one was drawn -- a sheep frozen mid-stride, a wolf
# on its back with its legs in the air -- because the only motion table there
# was held clips authored for the citizens' skeleton, which a wolf will not
# accept. It read as a broken import and it was a creature that had never been
# told to do anything.
#
# The table is filled from each creature's OWN folder, by matching the names
# the packs already use. A creature whose folder holds no clips gets no table,
# which is exactly right for the risen and the five faces an incursion wears:
# those ARE the citizens' body, so the wardrobe's own clips fit them and the
# window falls through to them. See FIntervalPropKind::Motions.
# AND THE CYLINDER EACH OF THEM USED TO BE, taken out.
#
# A row drawn as a skeleton ignores its `mesh`, so the engine primitive every
# beast started life as was sitting in the table under the animal -- harmless,
# and a lie that any future reader of the data would have to know to discount.
# The audit already scored these rows as drawn, because it asks whether ALL of
# a row's meshes are primitives; this makes the row itself say so.
for _row in have['Mobs'].values():
    _sk = _row.get('skeletal')
    if isinstance(_sk, dict) and _sk.get('refPath'):
        _mesh = _row.get('mesh')
        if isinstance(_mesh, dict) and '/Engine/BasicShapes/' in (_mesh.get('refPath') or ''):
            _row['mesh'] = 'None'

_MOTION_ROOT = os.path.join(SP, '..', 'Content')
_verbed = 0
for _word, _row in have['Mobs'].items():
    _sk = _row.get('skeletal')
    if not isinstance(_sk, dict) or not _sk.get('refPath'):
        continue
    _path = _sk['refPath'].split('.')[0]          # /Game/Interval/Wild/wolf_a/wolf_a
    _folder = _path.rsplit('/', 1)[0]             # /Game/Interval/Wild/wolf_a
    _disk = os.path.join(_MOTION_ROOT, *_folder.split('/')[2:])
    _clips = beast_motions(_disk, _folder)
    if not _clips:
        continue
    _row['motions'] = {
        _verb: {'anim': {'refPath': _asset},
                # A LITTLE SLOWER THAN AUTHORED, and each creature at its own
                # pace. These clips are cut for a game where a wolf crosses a
                # room; here it crosses a country at the world's tempo, and a
                # gallop played at speed reads as a cartoon.
                'rate': 0.85 if _verb == 'walk' else 0.8,
                'bLoop': _verb != 'felled',
                # Same tile-an-interval reference as the citizens'.
                'pace': 200.0 if _verb == 'walk' else 0.0}
        for _verb, _asset in _clips.items()}
    _verbed += 1
print('beasts given their own motions:', _verbed)

# (`skeleton-knight` used to be forced onto the LIVING base figure here, back
#  when it was the only way to get it off a cartoon skeleton. That gave it a
#  living man's face and, once the bestiary started wearing clothes, a bare
#  one -- the living copy is uncut and undressed. It takes the drained copy
#  out of BEASTS with everybody else now, and the override is gone.)

# ---------------------------------------------------------------------------
# WHAT A BOOT SOUNDS LIKE ON EACH GROUND.
#
# The WORLD'S words on the left, a surface on the right. The vocabulary here is
# the same list the ambience beds use, because that list was built from what the
# world actually says; a ground word with no entry is silent, which is the same
# rule the beds follow and the right one -- the window should not invent a
# noise for ground it has never been told about.
FOOTING = {
    # Anything you walk through rather than on.
    'grass': ['meadow', 'heartlands', 'downs', 'moor', 'wilds',
              'greenwood', 'forest'],
    # Beaten, dry, and dead underfoot.
    'earth': ['trail', 'trodden', 'chalk', 'peat', 'sand', 'causey'],
    # Laid by hand, or broken by weather -- both ring.
    'stone': ['flag', 'cobble', 'plaza', 'gravel', 'scree', 'crags',
              'mountain', 'cave', 'shingle'],
    # A board with a space under it.
    'wood':  ['floor', 'bridge'],
    # Standing water, and the one you can hear from furthest away.
    'water': ['fens', 'river', 'sea'],
}
# WHICH GROUND CANNOT ANSWER FOR ITSELF. A beach and a riverbank are both
# `sand`, and shingle is the same story, so these take the bed of whatever
# water or country they border rather than assuming the sea.
have['BorrowsAmbience'] = ['sand', 'shingle']

have['Footfalls'] = {
    word: {'sounds': [snd('step_%s%d' % (surface, v)) for v in (1, 2, 3)],
           'volume': 0.85 if surface == 'grass' else 1.0,
           'pitchJitter': 0.12}
    for surface, words in FOOTING.items() for word in words
}
# ---- AND WHAT A DEED SOUNDS LIKE ----
#
# Keyed on the world's own verb, which the window reads out of `deed` and
# which is present for exactly the interval the deed happened on.
#
# SORCERY WAS SILENT AND SO WAS EVERY OTHER INSTANT DEED. There was no path
# for it at all: no spell sets an `action`, so nothing about a cast reached the
# window, and the window had no table to look a deed up in even if it had.
# Both halves exist now, so the eleven spells across the two books each get
# their own noise, and so do four everyday deeds that are worth hearing.
#
# A DEED WITH NO ROW IS SILENT, and most are. Banking, buying and walking
# about want no noise, and a window that made one for every verb would be
# exhausting inside a minute.
#
# One take each rather than three. A footfall repeats every stride and needs
# variety or the repeat is audible; a citizen casts the withering a handful of
# times in an evening, so the pitch jitter alone is enough.
have['DeedSounds'] = {
    verb: {'sounds': [snd('deed_' + verb)], 'volume': vol, 'pitchJitter': 0.06}
    for verb, vol in (
        # the common book: it refuses, repairs and unmakes
        ('still', 1.0), ('seal', 0.95), ('transmute', 0.8), ('unmake', 0.85),
        ('mendp', 0.85), ('invoke', 0.9),
        # §6bq: `anchor` was here for a spell the constitution repealed, and
        # `mend` was keyed on the spell's name. The world writes down the VERB,
        # and the verb is `cast`, so mending is reached from the work table
        # below like every other act. Both rows were unreachable.

        # the barrow book: the one that does harm
        ('rot', 1.0), ('taking', 0.9), ('waking', 1.0), ('withering', 0.95),
        # and the everyday deeds that were also silent
        ('bury', 0.85), ('smith', 1.0), ('drink', 0.7), ('eat', 0.65),
    )
}

# ---- AND THE GAMBITS, WHICH THE WORLD DECIDES ----
#
# A gambit is a weapon's own move and seven weapons have one, in four kinds.
# The motions above already give each weapon its own clip; this is the noise,
# keyed the same way, `gambit.<what is in the hand>`.
#
# ONE TABLE, IN THE FILE THAT MAKES THE SOUNDS. This script runs inside the
# editor and cannot load `engine.js`, so the mapping from weapon to kind lives
# in `deedsfx.py` beside the four synths and is imported here rather than
# written out twice. `audit_motion.py` reads the real engine and says so if
# the two have drifted.
from deedsfx import GAMBIT_KIND as _gambits
have['DeedSounds'].update({
    'gambit.' + weapon: {'sounds': [snd('gambit_' + kind)],
                         'volume': 1.0, 'pitchJitter': 0.07}
    for weapon, kind in sorted(_gambits.items())
})

# A blow lands harder than a stalk coming up. These are the levels the
# synthesiser was tuned at, carried through so one table decides loudness
# rather than each wav being written louder than the last.
_WORK_VOL = {'chop': 1.0, 'mine': 1.0, 'strike': 1.0, 'thud': 0.95,
             'loose': 0.85, 'grind': 0.8, 'kindle': 0.8, 'char': 0.7,
             'whittle': 0.7, 'angle': 0.65, 'pull': 0.6,
             # the horn is meant to be heard across a valley and is the one
             # thing here allowed to be louder than a blow
             'horn': 1.0, 'oath': 0.9, 'hull': 0.7, 'clatter': 0.7,
             'sheathe': 0.6, 'nockup': 0.6, 'page': 0.5,
             # THE THIRD PASS, AND THESE ARE SET BY HOW FAR THEY CARRY rather
             # than by how interesting they are. A furnace and a saw are heard
             # across a town, which is why a town sounds like a town; a nib on
             # paper is heard by the person holding it and nobody else.
             'furnace': 1.0, 'sawing': 0.95, 'build': 0.95, 'unbuild': 0.9,
             'chime': 0.9, 'stake': 0.85, 'feed': 0.8, 'coin': 0.7,
             'sizzle': 0.7, 'pour': 0.65, 'sack': 0.6, 'wicker': 0.6,
             'sow': 0.45, 'quill': 0.35, 'graze': 0.55}


# ---- AND THE WORK, WHICH WAS THE LARGEST SILENCE ----
#
# Fifty-eight of the world's sixty-nine verbs made no sound at all, while every
# one of the eighty-two had a motion of its own. The worst of it was `gather`:
# felling, mining and fishing all go through that verb, it is the commonest
# thing anybody does, and a citizen could cut a tree down for ten minutes in
# total quiet with the axe swinging perfectly. Combat was the same -- only the
# gambit could be heard, so a fight was five silent blows and one loud one.
#
# Keyed by WHAT IS IN THE HAND, which is the refinement the window already
# does (`verb.<held>`, then the plain verb). One row per tool rather than per
# tree: an axe in oak and an axe in ironbark are an axe. A citizen with empty
# hands falls through to the plain verb and pulls the thing up instead.
from deedsfx import WORK_SOUNDS as _work, VOICED as _voiced


def _work_row(kind):
    # Two entries where there is a voiced twin, so the window's pick-one lands
    # on a grunt about half the time rather than on every swing.
    names = ['deed_' + kind] + (['deed_%s_v' % kind] if kind in _voiced else [])
    return {'sounds': [snd(n) for n in names],
            'volume': _WORK_VOL.get(kind, 0.9), 'pitchJitter': 0.09}


have['DeedSounds'].update({
    (verb if held is None else verb + '.' + held): _work_row(kind)
    for verb, rows in sorted(_work.items())
    for held, kind in sorted(rows.items(), key=lambda kv: (kv[0] is not None, kv[0]))
})

# ---- AND WHAT A RITE LOOKS LIKE ----
#
# Four shapes, eleven spells. The shape is the motion and the colour is what
# tells two rites with the same motion apart: a rot and an unmaking are both
# things flying out of a pair of hands, and one is dark, wet and slow while
# the other is quick and pale.
#
# THE TWO BOOKS ARE TWO PALETTES, on purpose. The common book refuses, repairs
# and unmakes, and the engine says of it "not one hurts anybody": it is pale,
# warm where it heals and cold where it refuses. The barrow book is the one
# that harms and it is dark, and there is nothing warm anywhere in it.
#
# Rise is how far up the body it happens. A hundred is about the hands; zero
# is at the feet, which is where anything that spreads along the ground goes.
def _fx(n):
    return {'refPath': '/Game/Interval/FX/%s.%s' % (n, n)}

BURST, GATHER, RING, RISE = (_fx('NS_RiteBurst'), _fx('NS_RiteGather'),
                             _fx('NS_RiteRing'), _fx('NS_RiteRise'))
have['Rites'] = {
    verb: {'system': shape, 'tint': {'r': r, 'g': g, 'b': b, 'a': 1.0},
           'scale': scale, 'rise': rise}
    for verb, shape, (r, g, b), scale, rise in (
        # ---- the common book ----
        # The stilling holds a fight: a ring going out at the feet, cold and
        # pale, and the one rite in the book that reaches other people.
        ('still',     RING,   (0.62, 0.74, 0.92), 1.35, 10.0),
        # Shutting a way is heavier and lower than the stilling, and stone.
        ('seal',      RING,   (0.52, 0.50, 0.46), 1.05, 6.0),
        # Transmuting draws a thing in and leaves money: gold, at the hands.
        ('transmute', GATHER, (0.86, 0.68, 0.26), 0.85, 105.0),
        # An unmaking throws it outward instead. The same gold, coming apart.
        ('unmake',    BURST,  (0.80, 0.66, 0.34), 0.95, 100.0),
        # Mending is the warm one, and it climbs. Keyed on `cast`, which is
        # the word the world actually records: §6bq leaves `mend` the only
        # spell still cast by that verb, and the rest are verbs of their own.
        ('cast',      RISE,   (0.95, 0.72, 0.42), 0.90, 55.0),
        # Sent rather than kept, so it is brighter and a little higher.
        ('mendp',     RISE,   (1.00, 0.80, 0.50), 1.00, 95.0),
        # §6bq: the recall was the tallest thing in either book and the world
        # repealed it. Nothing can ask for it, so nothing draws it.
        # Pressing a sigil happens kneeling, at an altar, in front of you.
        ('invoke',    GATHER, (0.55, 0.45, 0.78), 0.80, 60.0),
        # ---- the barrow book: nothing here is warm ----
        # The rot spreads out and falls.
        ('rot',       BURST,  (0.22, 0.30, 0.16), 1.15, 70.0),
        # The taking pulls, and it is the coldest of the four.
        ('taking',    GATHER, (0.30, 0.34, 0.40), 1.00, 95.0),
        # The waking calls something up out of the ground.
        ('waking',    RING,   (0.34, 0.26, 0.34), 1.20, 4.0),
        # The withering is grey, dry and the slowest thing either book does.
        ('withering', RISE,   (0.44, 0.42, 0.38), 1.10, 90.0),
    )
}

# ---- AND WHAT THE SPELL LEAVES ON WHOEVER IT LANDED ON ----
#
# THE OTHER HALF, AND THE HALF THAT LASTS. Every row above is a casting and is
# over inside the interval it happened in. These are the conditions the world
# then carries on the TARGET, and the bridge has been forwarding them all
# along as `marks.<word>` holding the intervals remaining. The window drew
# none of them, so a citizen who had been rooted to the spot looked exactly
# like a citizen who had chosen to stand still, and the spell that did it may
# as well not have been cast.
#
# TWO SHAPES, SIX WORDS, on the same argument as the rites. Burning, rotting
# and withering are all something happening to a BODY and read as a slow column
# clinging to the figure; being rooted and being stilled are something holding
# a body in PLACE and read at the feet. The colour does the rest.
#
# The branding is the odd one and it is deliberately the only bright mark in
# the list: it is a public fact about somebody rather than an injury, so it
# sits high, near the shoulders, where a person's face is.
AURA, GROUND = _fx('NS_MarkAura'), _fx('NS_MarkGround')
have['Marks'] = {
    word: {'system': shape, 'tint': {'r': r, 'g': g, 'b': b, 'a': 1.0},
           'scale': scale, 'rise': rise}
    for word, shape, (r, g, b), scale, rise in (
        # On fire. The only mark that is doing damage every interval, and the
        # brightest thing in the list because of it.
        ('burning',  AURA,   (1.00, 0.52, 0.16), 1.15, 78.0),
        # The rot: dark, wet and low on the body.
        ('rotting',  AURA,   (0.26, 0.34, 0.18), 1.05, 62.0),
        # The withering: grey and dry, and it hangs higher and thinner.
        ('withered', AURA,   (0.52, 0.50, 0.46), 0.90, 88.0),
        # A brand is a mark on the person, not a wound. Pale and high.
        ('branded',  AURA,   (0.86, 0.72, 0.40), 0.70, 128.0),
        # Rooted: held by the ground, so it is the ground's own colour.
        ('rooted',   GROUND, (0.34, 0.30, 0.18), 1.20, 4.0),
        # Stilled: the same hold, cold, and it matches the rite that casts it.
        ('stilled',  GROUND, (0.62, 0.74, 0.92), 1.10, 4.0),
    )
}

# About a stride. Shorter and a walk becomes a trot; longer and the feet and
# the sound come apart, which is worse than no sound at all.
have['StepEvery'] = 76.0
have['StepHeard'] = 3600.0

# RAIN, TWICE: in the open, and heard from under a thatch. The window already
# knows which tiles are roofed, because it built the roofs.
have['RainSound'] = snd('amb_rain')
have['RainRoofSound'] = snd('amb_rainroof')
have['BirdSound'] = snd('amb_birds')

# ---- AND WHAT LIVES ON EACH GROUND ----
#
# `amb_birds` is a meadow at noon, and it was the only voice this world had:
# the same songbirds over the moor, over the shingle and over the peat.
# Reported from the stream, with the reasoning attached -- "sound of crows in
# moor instead of regular bird song ... details like these are in my opinion
# what will give this window a big jump."
#
# Three more voices, keyed off the world's OWN words for the ground exactly as
# the beds and the footfalls are. A word with no row here keeps the songbirds,
# which is right: they belong to the green and settled country and always did.
#
#   CROWS on the high bleak ground -- moor, crags, mountain, scree, the wilds
#         and the peat. The ground with no trees on it.
#   GULLS on the shore.
#   FROGS in the fens, which are the one place in this world that is all water
#         and reeds and has never had a voice at all.
#
# `IntervalSound` also reads the hour and the rain differently for each of
# them, because a crow is not a songbird about weather and a frog is not one
# about nightfall; see the note there.
VOICES = {
    'amb_crows': ['moor', 'crags', 'mountain', 'scree', 'wilds', 'peat'],
    'amb_gulls': ['sea', 'shingle', 'sand'],
    'amb_frogs': ['fens'],
}
have['GroundVoices'] = {w: snd(v) for v, words in VOICES.items() for w in words}
# WHICH WAY THE FIGURES FACE. Measured from the meshes themselves: Male_Ranger
# is 180 cm across X and 37 cm across Y -- a T-pose with the arms along X -- so
# the body fronts along Y while Unreal takes +X as forward. Without this a
# citizen walks south facing east, which reads as walking sideways.
# If they come out walking backwards instead, this is +90: one apply, no build.
# MOVED TO THE END, AND THAT MATTERS. Run where it used to be, this copied
# `keeper` before the keepers were given human bodies, so `crier` -- a person
# who stands in a street and calls -- came out as the cylinder a keeper was
# three hundred lines earlier. A copy is only as good as the moment it is
# taken.
# AND THE THREE THAT ARE ANOTHER WORD, COPIED WHOLE.
#
# `deepcopy`, because two words sharing one dict is two words that cannot ever
# be told apart again -- and because the fire's flame tongues are in `parts`,
# which a shallow copy would hand to both.
for _word, _like in LIKEWISE.items():
    if _like in props:
        props[_word] = copy.deepcopy(props[_like])
        _unseen += 1
    else:
        print('  LIKEWISE: no row for %s to copy for %s' % (_like, _word))
print('likewise: %d words copied from another word' % len(LIKEWISE))

have['CitizenFacingYaw'] = -90.0
have['RainVolume'] = 0.62

have['Ambience'] = {w: snd(a) for a, words in AMBIENCE.items() for w in words}
have['Music'] = {w: snd(t) for t, words in MUSIC.items() for w in words}

# ---- AND IF THE LOOK DID NOT TAKE, SAY SO AND STOP ----
#
# `write` returns whatever the editor said, and this printed it and carried on.
# The editor rejects the WHOLE properties blob if any single entry is bad --
# one mesh path pointing at a material instead of a static mesh threw out
# every other change in the run -- and the `save:` line on the next line still
# said `true`, because saving an unchanged asset succeeds. So a run could
# report success and change nothing, and did.
_look = write(LOOK, have)
print('look:', _look)
if 'returnValue' not in _look or 'true' not in _look:
    raise SystemExit('THE LOOK WAS REJECTED AND NOTHING IN THIS RUN TOOK. '
                     'The editor validates every entry and refuses the lot if '
                     'one is wrong; the message above names it.')
print('save:', call('editor_toolset.toolsets.asset.AssetTools', 'save_assets',
                    {'asset_paths': ['/Game/Interval/IntervalLook']}))

# ---------------------------------------------------------------------------
# AND THE LEVEL POINTS AT THE LOOK, which until now nothing did.
#
# `UIntervalLook::Resolve(nullptr)` falls back to loading the wardrobe by a
# fixed path, and that convention is fine at runtime and invisible to the
# COOK: a cook walks outwards from the maps through hard pointers, and a path
# in C++ is not a pointer. So the first packaged client shipped without the
# wardrobe, and every citizen in it was an untextured mannequin standing
# beside a cylinder where a fountain should be.
#
# The actors already have the property. Setting it makes the reference real,
# which brings the whole wardrobe -- and every mesh, material and texture it
# names -- along behind it, without cooking the art nothing uses.
# `GROUND` has no wardrobe of its own and does not want one; it is left out
# rather than written to and refused.
for _who in (CITIZENS, STRUCT):
    _r = write(_who, {'Look': {'refPath': LOOK}})
    if 'true' not in _r:
        print('could not point %s at the look: %s' % (_who.split('.')[-1], _r))
print('level points at the look')
# THE LEVEL IS AN ASSET LIKE ANY OTHER as far as saving goes, and the pointer
# only counts once it is on disk: an unsaved level is a reference the cook
# never sees, which is the whole fault this is fixing.
print('save level:', call('editor_toolset.toolsets.asset.AssetTools', 'save_assets',
                          {'asset_paths': ['/Game/TopDown/Lvl_TopDown']}))
