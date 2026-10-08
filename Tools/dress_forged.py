#!/usr/bin/env python3
"""Give the forged meshes their colours, off `M_IntervalFlat`.

An OBJ's .mtl names a diffuse colour per material and Unreal's importer makes
a MaterialInstanceConstant for each -- of ITS OWN parent, not of this
project's. Photographed, every forged piece came back grey: the shapes were
right and the palette had gone. The wolf mask, the antlers, the gold greaves
and the bones were all the same putty.

So the instances are rebuilt here against `M_IntervalFlat`, which is the one
master anything flat-coloured in this window hangs off -- exactly as
`make_prop.py` does for the primitives. That buys three things beyond the
colour, and they are the reason it is worth doing properly rather than just
setting a base colour on the imported instance:

  THE WEATHER. A bone pile darkens in the same rain as the ground it lies on.
  GRAIN. World-space mottle, so a trebuchet's beams are not one flat tan.
  And one master to change when the look of the world changes.

`forge.PALETTE` is the source of the colours, so the .mtl and the material
instance cannot drift: both are generated from the same dict.
"""
import os
import sys

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import rpc
from forge import PALETTE

MASTER = '/Game/Interval/Materials/M_IntervalFlat.M_IntervalFlat'
FOLDER = '/Game/Interval/Forged'
# THE COLOURS LIVE APART FROM THE MESHES, and that is not tidiness.
#
# This made one material per palette key alongside the meshes, and Unreal
# treats asset names as case-INSENSITIVE -- so a colour called `Coal` and a
# forged mesh called `coal` were the same name. The material won, the mesh
# could not be imported at all, and every lookup of it returned a material,
# which surfaced much later as "MaterialInstanceConstant has no attribute
# get_bounding_box". Thirteen goods were lost that way. A separate folder
# makes the whole class of collision impossible instead of renaming colours
# one at a time forever.
HUES = FOLDER + '/Hues'
MI = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools'
AS = 'editor_toolset.toolsets.asset.AssetTools'

# How each surface behaves beyond its colour. Roughness first: bone and horn
# are matte, metal is not, and leather sits between. `Grain` is the world-space
# mottle; a little on everything so nothing reads as plastic.
#             rough  grain
FINISH = {
    'Bone':     (0.86, 0.14),
    'BoneDark': (0.90, 0.16),
    'Wood':     (0.88, 0.18),
    'WoodDark': (0.90, 0.18),
    'Iron':     (0.52, 0.10),
    'Steel':    (0.40, 0.08),
    'Gold':     (0.34, 0.06),
    'Fur':      (0.94, 0.22),
    'FurLight': (0.94, 0.22),
    'FurDark':  (0.95, 0.20),
    'Feather':  (0.78, 0.16),
    'Leather':  (0.82, 0.14),
    'Cloth':    (0.92, 0.18),
    'Keratin':  (0.62, 0.12),
}

# WHICH FORGED MESHES HANG, and how far down they hang.
#
# A hanging thing gets its colour off `M_IntervalHang` instead of
# `M_IntervalFlat`: the same graph with a swing wired into the world position
# offset. It is a second master rather than a parameter on the first because a
# world position offset is paid by every instance of the material that has one,
# and `M_IntervalFlat` is worn by every wall and roof in every settlement --
# see the note at the top of make_hang.py.
#
# The chain was reported from the stream the day it landed: "it should also
# sway, not be straight like an arrow". A loose thing that does not move reads
# as a stick painted to look like the thing.
#
#   mesh -> (how long the run is in cm, how far the tip travels in cm)
# NINE CENTIMETRES WAS NOT A SWAY, IT WAS A NUMBER. At the distance this
# camera stands a citizen of 181 cm is about sixty pixels, so nine centimetres
# of travel at the tip is three pixels and is not visible at all. Twenty-six
# is a chain swinging from the hand of somebody walking, which is the thing
# being drawn.
HANGS = {
    'old_chain':  (91.0, 26.0),
    'gold_chain': (91.0, 26.0),
    # AND THE FLAIL, whose head hangs on three links off the end of a haft.
    # The haft is rigid and the shader cannot know that, so it flexes by a
    # quarter of the amplitude at its far end -- three and a half centimetres,
    # which is one pixel at the distance this camera stands, and cheaper than a
    # second material for one weapon. A flail head that does not move is a mace
    # with a gap in it.
    'star_flail': (72.0, 14.0),
}
HANG_MASTER = '/Game/Interval/Materials/M_IntervalHang.M_IntervalHang'

rpc.call('EditorToolset.EditorAppToolset', 'StopPIE', {})
made = 0
for name, (r, g, b) in sorted(PALETTE.items()):
    path = '%s/%s.%s' % (HUES, name, name)
    rough, grain = FINISH.get(name, (0.85, 0.15))
    rpc.call(AS, 'delete', {'path': path.split('.')[0]})
    rpc.call(MI, 'create', {'folder_path': HUES, 'asset_name': name,
                            'parent': {'refPath': MASTER}})
    rpc.call(MI, 'set_vector_parameter', {'instance': {'refPath': path},
             'name': 'DiffuseColor', 'value': {'r': r, 'g': g, 'b': b, 'a': 1.0}})
    for param, v in (('Rough', rough), ('Course', 0.0), ('Grain', grain),
                     ('Plank', 0.0),
                     # Nothing forged takes a citizen's dye, the same as
                     # nothing composed does.
                     ('Strength', 0.0), ('Shift', 0.5)):
        rpc.call(MI, 'set_scalar_parameter',
                 {'instance': {'refPath': path}, 'name': param, 'value': v})
    rpc.call(AS, 'save_assets', {'asset_paths': [path.split('.')[0]]})
    made += 1
    print('%-10s %.3f %.3f %.3f  rough %.2f' % (name, r, g, b, rough))
print('dressed %d forged materials' % made)

# ---- AND A HANGING TWIN FOR EVERY COLOUR A HANGING MESH WEARS ----
#
# One twin per colour rather than one per mesh: two chains of the same rust are
# the same material, and the two numbers that differ between hanging objects
# are set per INSTANCE on these, which a mesh with its own length would need
# its own twin for. Nothing hangs at two lengths in the same colour yet; when
# something does, this is the line that has to grow a key.
import subprocess as _sub
_hangs = set()
for _m, (_len, _amp) in HANGS.items():
    _obj = os.path.join(os.path.dirname(SP), 'Art', 'Forged', _m + '.obj')
    _mtl = _obj[:-4] + '.mtl'
    if not os.path.exists(_mtl):
        continue
    for _line in open(_mtl):
        if _line.startswith('newmtl '):
            _hangs.add((_line.split()[1].strip(), _len, _amp))
for _hue, _len, _amp in sorted(_hangs):
    _name = _hue + 'Hang'
    _path = '%s/%s.%s' % (HUES, _name, _name)
    _r, _g, _b = PALETTE[_hue]
    _rough, _grain = FINISH.get(_hue, (0.85, 0.15))
    rpc.call(AS, 'delete', {'path': _path.split('.')[0]})
    rpc.call(MI, 'create', {'folder_path': HUES, 'asset_name': _name,
                            'parent': {'refPath': HANG_MASTER}})
    rpc.call(MI, 'set_vector_parameter', {'instance': {'refPath': _path},
             'name': 'DiffuseColor', 'value': {'r': _r, 'g': _g, 'b': _b, 'a': 1.0}})
    for _param, _v in (('Rough', _rough), ('Course', 0.0), ('Grain', _grain),
                       ('Plank', 0.0), ('Strength', 0.0), ('Shift', 0.5),
                       ('HangLength', _len), ('HangAmp', _amp)):
        rpc.call(MI, 'set_scalar_parameter',
                 {'instance': {'refPath': _path}, 'name': _param, 'value': _v})
    rpc.call(AS, 'save_assets', {'asset_paths': [_path.split('.')[0]]})
    print('%-10s hangs %.0f cm, tip travels %.0f cm' % (_name, _len, _amp))

# ---- AND A FLYING TWIN, FOR THE ONE MESH THAT HAS WINGS ----
#
# The same argument as the hanging twin above, one word different: a wing beat
# is a world position offset, a world position offset is paid by every instance
# of the material that carries one, and `M_IntervalFlat` is worn by every wall
# in every settlement. So the bird gets its own master and its own colour off
# it, and nothing that does not fly is asked to think about flying.
#
# ONE COLOUR, because there is one bird. When there are gulls as well as crows
# this is the line that grows a key -- and it should grow one, because a gull
# is white and a crow is not, and drawing both in the same dark is the same
# mistake as playing one birdsong over every country.
WINGS_MASTER = '/Game/Interval/Materials/M_IntervalWings.M_IntervalWings'
for _hue in ('Feather',):
    _name = _hue + 'Wing'
    _path = '%s/%s.%s' % (HUES, _name, _name)
    _r, _g, _b = PALETTE[_hue]
    _rough, _grain = FINISH.get(_hue, (0.85, 0.15))
    rpc.call(AS, 'delete', {'path': _path.split('.')[0]})
    rpc.call(MI, 'create', {'folder_path': HUES, 'asset_name': _name,
                            'parent': {'refPath': WINGS_MASTER}})
    rpc.call(MI, 'set_vector_parameter', {'instance': {'refPath': _path},
             'name': 'DiffuseColor', 'value': {'r': _r, 'g': _g, 'b': _b, 'a': 1.0}})
    for _param, _v in (('Rough', _rough), ('Course', 0.0), ('Grain', _grain),
                       ('Plank', 0.0), ('Strength', 0.0), ('Shift', 0.5),
                       ('Span', 47.0), ('Amp', 16.0), ('Rate', 2.4)):
        rpc.call(MI, 'set_scalar_parameter',
                 {'instance': {'refPath': _path}, 'name': _param, 'value': _v})
    rpc.call(AS, 'save_assets', {'asset_paths': [_path.split('.')[0]]})
    print('%-10s beats %.1f times a second, tip travels %.0f cm' % (_name, 2.4, 16.0))

# ---- AND THE EMBERS IN THE CINDER-CROWN'S CRACKS ----
#
# The crown has two slots: `Soot` for the burnt body, which is an ordinary
# instance off the flat master like everything else here, and `Ember` for the
# eighteen faces deep in the splits between its lumps. That second one cannot
# come off the flat master, because what is wanted is not a colour, it is a
# LIGHT: an additive unlit emissive that breathes like a coal and lifts at
# night. See Tools/cinder.hlsl.
#
# It is worth the extra master for one item because of what the item is. It
# falls from the dragon, one in two thousand and forty-eight, and defends
# nothing whatever -- "pure cosmetic" in §6da. Its entire worth is being seen,
# so it had better be visible after dark.
# THIS REPLACES THE ONE THE PALETTE LOOP ABOVE ALREADY MADE. `Ember` is a
# `forge.PALETTE` key, so that loop makes it off the flat master like every
# other colour; this deletes it and makes it again off the cinder master. The
# order matters and it is the order the file is in.
CINDER = '/Game/Interval/Materials/M_IntervalCinder.M_IntervalCinder'
_epath = '%s/Ember.Ember' % HUES
rpc.call(AS, 'delete', {'path': _epath.split('.')[0]})
rpc.call(MI, 'create', {'folder_path': HUES, 'asset_name': 'Ember',
                        'parent': {'refPath': CINDER}})
rpc.call(MI, 'set_scalar_parameter',
         {'instance': {'refPath': _epath}, 'name': 'Bright', 'value': 1.0})
rpc.call(AS, 'save_assets', {'asset_paths': [_epath.split('.')[0]]})
print('Ember     is alight, off M_IntervalCinder')

# ---- AND A SASH IN EACH TRADE'S OWN MATERIAL ----
#
# The sworn sash is ONE mesh worn by nine skills, and what differs between them
# is what it is cut from: iron for the smith, shell for the fisher, bone for
# the mourner. So nine material instances off the same master rather than nine
# meshes, which is the same arrangement the five grades of sword already use.
#
# THE NAMES ARE SUFFIXED `Sash` and not reused, because a sash of iron is not
# the same surface as a horseshoe of iron: cloth-over-plate at this size wants
# to be a little softer and a little less mirror than the bare metal, or a
# smith reads as somebody wearing a road sign.
SASH_HUE = ('Wood', 'Iron', 'Shell', 'Wheat', 'Steel', 'Keratin', 'Magic',
            'Bone', 'Leather')
for _hue in SASH_HUE:
    _name = _hue + 'Sash'
    _path = '%s/%s.%s' % (HUES, _name, _name)
    _r, _g, _b = PALETTE[_hue]
    _rough, _grain = FINISH.get(_hue, (0.85, 0.15))
    rpc.call(AS, 'delete', {'path': _path.split('.')[0]})
    rpc.call(MI, 'create', {'folder_path': HUES, 'asset_name': _name,
                            'parent': {'refPath': MASTER}})
    rpc.call(MI, 'set_vector_parameter', {'instance': {'refPath': _path},
             'name': 'DiffuseColor', 'value': {'r': _r, 'g': _g, 'b': _b, 'a': 1.0}})
    for _param, _v in (('Rough', min(0.95, _rough + 0.10)), ('Course', 0.0),
                       ('Grain', _grain), ('Plank', 0.0),
                       ('Strength', 0.0), ('Shift', 0.5)):
        rpc.call(MI, 'set_scalar_parameter',
                 {'instance': {'refPath': _path}, 'name': _param, 'value': _v})
    rpc.call(AS, 'save_assets', {'asset_paths': [_path.split('.')[0]]})
print('sashes cut from %d materials' % len(SASH_HUE))

# ---- AND BIND THEM TO THE MESHES, WHICH NOTHING ELSE WILL DO ----
#
# The OBJ importer does NOT bind a slot to a material that already exists at
# the destination with the same name -- which was the assumption, and it is
# wrong in both directions: with `import_materials` on it makes its own and
# this script deletes them; with it off the slots come out bound to None. Two
# rounds of grey came from that.
#
# So the binding is explicit. Every forged mesh's slots are named after the
# palette entry the forge wrote into the .mtl, so this is a lookup and cannot
# drift: `forge.PALETTE` names the colour, the OBJ names the slot, and this
# joins them.
SM = 'editor_toolset.toolsets.static_mesh.StaticMeshTools'
import json as _json
# THE NAMES COME OFF THE DISK, not out of one script.
#
# This used to read `make_art.PIECES`, which knew about the thirteen pieces
# that existed when it was written. `make_goods.py` then forged forty-nine
# more and every one of them came out grey, silently -- the dresser reported
# success, because it had bound everything in the list it was looking at.
# Art/Forged is the truth about what was forged; both scripts write into it.
ART = os.path.join(os.path.dirname(SP), 'Art', 'Forged')
meshes = sorted(f[:-4] for f in os.listdir(ART) if f.lower().endswith('.obj'))
bound = missing = 0
for name in meshes:
    mesh = {'refPath': '%s/%s.%s' % (FOLDER, name, name)}
    try:
        slots = _json.loads(rpc.call(SM, 'get_material_slots',
                                     {'mesh': mesh}))['returnValue']
    except Exception:
        continue
    for slot in slots:
        if slot not in PALETTE:
            print('  %s: slot %r has no palette entry' % (name, slot))
            missing += 1
            continue
        rpc.call(SM, 'set_material', {
            'mesh': mesh, 'slot_name': slot,
            # HUES, NOT FOLDER. The colours moved to their own folder to stop
            # them colliding with the meshes by name, and this line kept
            # pointing at where they used to be -- so every `set_material`
            # named a material that no longer existed, was accepted without
            # complaint, and left the slot bound to nothing. The script still
            # counted it and reported "0 unmatched"; the goods came out grey.
            # A HANGING MESH TAKES THE TWIN. Same colour, same finish, and a
            # swing in the world position offset; see HANGS above.
            'material': {'refPath': '%s/%s.%s' % (
                HUES, slot + ('Hang' if name in HANGS else ''),
                slot + ('Hang' if name in HANGS else ''))}})
        bound += 1
    rpc.call(AS, 'save_assets', {'asset_paths': ['%s/%s' % (FOLDER, name)]})
    print('  bound %-14s %s' % (name, ', '.join(slots)))
print('bound %d slots across the forged meshes (%d unmatched)' % (bound, missing))
print('RUN ORDER: make_art.py -> import_forged.py -> dress_forged.py -> apply.py')
print('This script must come LAST of the three, because it binds the mesh')
print('slots explicitly and a re-import resets them to None. The importer')
print('does not bind by name in either direction -- with import_materials on')
print('it makes its own instances, with it off it binds nothing -- and two')
print('rounds of grey came from assuming otherwise.')
