#!/usr/bin/env python3
"""The material instances everything composed out of primitives wears.

These fourteen were made by hand in an early session and existed only as
assets: no script, no record of why a stone is 0.33 grey and a hedge is 0.07
green, and no way to rebuild them after a master was replaced. They are here
now, with their numbers and with what each number is for.

They hang off M_IntervalFlat, which is the one master for anything that is a
flat colour. It gives them three things the hand-made master could not:

  THE WEATHER. A stone wall now darkens and shines in the same rain as the
  ground it stands on. It did not before, which is the sort of difference
  nobody names and everybody sees.

  GRAIN. World-space mottle at two scales, so a six-metre wall is not one
  continuous tone across forty square metres.

  COURSES. Where `Course` is not zero the surface is laid up as masonry --
  blocks of that height, every other row offset by half a block, a dark
  mortar line between them and no two stones quite the same colour. It is
  the difference between a town wall and a tan cardboard box.
"""
import json, os, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import rpc

MASTER = '/Game/Interval/Materials/M_IntervalFlat.M_IntervalFlat'
# THE WALLS HANG OFF THEIR OWN MASTER, and only the walls. `M_IntervalWall` is
# `M_IntervalFlat` with a cutaway in it and a masked blend mode; see the head
# of wall.hlsl for why that could not be a switch on the flat one. The colours
# below are the same stone and the same limewashed timber the props use -- a
# wall and a stone trough are quarried out of the same hill -- so the two pairs
# are deliberately identical and differ only in what happens when you walk up
# to them.
WALL_MASTER = '/Game/Interval/Materials/M_IntervalWall.M_IntervalWall'
WALLS = ('MI_WallStone', 'MI_WallTimber', 'MI_WallPalisade', 'MI_WallDoor')
FOLDER = '/Game/Interval/Materials'
MI = 'editor_toolset.toolsets.material_instance.MaterialInstanceTools'
AS = 'editor_toolset.toolsets.asset.AssetTools'

# name -> (r, g, b, dry roughness, course height in cm, grain)
#
# A course of 42 cm is a big dressed block, which is what a town wall is built
# of; a cottage's plinth is the same wall in miniature and takes the same
# stone, because it was quarried by the same people.
KIND = {
    # COOLER AND DARKER THAN IT WAS. At (0.33, 0.32, 0.30) -- a light warm
    # grey -- a six-metre town wall under a low sun read as sandstone, or
    # rather as tan cardboard, which is the specific thing the courses were
    # added to stop. Northern building stone is grey and it is not bright.
    'MI_PropStone':    (0.205, 0.213, 0.220, 0.85, 42.0, 0.10,  0.0),
    'MI_PropRock':     (0.195, 0.186, 0.176, 0.80,  0.0, 0.17,  0.0),
    'MI_PropTimber':   (0.165, 0.112, 0.068, 0.90,  0.0, 0.11, 23.0),
    'MI_PropThatch':   (0.205, 0.158, 0.092, 0.94,  0.0, 0.15, 31.0),
    'MI_PropCloth':    (0.330, 0.130, 0.098, 0.78,  0.0, 0.07,  0.0),
    'MI_PropCanopy':   (0.044, 0.082, 0.040, 0.96,  0.0, 0.14,  0.0),
    'MI_PropHedge':    (0.072, 0.128, 0.056, 0.95,  0.0, 0.14,  0.0),
    'MI_ScatterGrass': (0.225, 0.300, 0.115, 0.95,  0.0, 0.13,  0.0),
    'MI_ScatterHeath': (0.200, 0.150, 0.098, 0.95,  0.0, 0.13,  0.0),
    'MI_ScatterReed':  (0.235, 0.245, 0.125, 0.95,  0.0, 0.13,  0.0),
    'MI_MobBeast':     (0.105, 0.072, 0.048, 0.92,  0.0, 0.08,  0.0),
    'MI_MobBone':      (0.310, 0.296, 0.252, 0.84,  0.0, 0.08,  0.0),
    'MI_MobFoul':      (0.088, 0.115, 0.058, 0.90,  0.0, 0.08,  0.0),
    'MI_MobGreat':     (0.145, 0.048, 0.044, 0.80,  0.0, 0.08,  0.0),
    # And the three that cut away. Same numbers as MI_PropStone and
    # MI_PropTimber above, on purpose.
    'MI_WallStone':    (0.205, 0.213, 0.220, 0.85, 42.0, 0.10,  0.0),
    'MI_WallTimber':   (0.165, 0.112, 0.068, 0.90,  0.0, 0.11, 23.0),
    # ---- AND THE STOCKADE, WHICH IS THE SAME TIMBER THAT DOES CUT AWAY ----
    #
    # Byte for byte MI_PropTimber. It exists because of where that one hangs:
    # the props' master is opaque and has no cutaway, and the palisade was
    # moved onto it deliberately -- see the note beside `palisade` in apply.py
    # -- to stop a town's stockade being drawn as a continuous run of cottage
    # wall with windows in it. That fixed the windows and quietly took the
    # cutaway away with them, so the one thing a citizen cannot see past when
    # they walk into a town was the ring of timber around the whole of it.
    # The house walls opened, the roofs lifted, and the person stayed hidden
    # behind the stockade.
    #
    # The palisade is not a prop. It is a wall, it is six metres of it in
    # every direction, and it belongs on the master that knows what to do
    # when somebody stands behind it.
    'MI_WallPalisade': (0.165, 0.112, 0.068, 0.90,  0.0, 0.11, 23.0),
    # ---- AND THE DOOR, FOR THE SAME REASON AGAIN ----
    #
    # A door leaf is 182 cm of timber and the wall it is hung in cuts away at
    # 135. On the props' master the leaf does not cut, so walking up to a house
    # opened the wall and left the door standing in the gap on its own, a slab
    # of oak holding up nothing. Same six numbers, same timber; it opens with
    # the wall it belongs to.
    'MI_WallDoor':     (0.165, 0.112, 0.068, 0.90,  0.0, 0.11, 23.0),
}

# ---------------------------------------------------------------------------
# THE INCURSION'S FIVE FACES.
#
# `incursion` is not one creature. The event fixes on a citizen and wears a
# face chosen by what they were doing -- a woodwraith when they chop, a
# gargoyle when they mine, a drownling when they fish -- and the open country
# gives the other two. The browser windows have drawn ONE silhouette in five
# skins off that word since it existed, and this window had not been asking
# for it: `face` was in the frame all along.
#
# The colours are the browser's own, copied as the hex the other windows use
# and converted here rather than eyeballed, so a woodwraith is the same green
# in Unreal as it is in a tab. That is the whole point of the shared world.
def srgb(hexed):
    """A web colour to linear, which is what a material wants."""
    v = [int(hexed[i:i + 2], 16) / 255.0 for i in (1, 3, 5)]
    return [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in v]


FACE = {
    'MI_FaceWoodwraith':  '#4a5a2c',   # bark and leaf, out of the greenwood
    'MI_FaceGargoyle':    '#5a5650',   # stone and ore, out of the crags
    'MI_FaceDrownling':   '#2f5a52',   # drowned green, out of the fens
    'MI_FaceWildsShade':  '#241f2a',   # near black, out of the wilds
    'MI_FaceHaunt':       '#6a6a72',   # pale, and what an unnamed one wears
}
for _name, _hex in FACE.items():
    _r, _g, _b = srgb(_hex)
    # Matte, and grainier than anything a person wears: it is conjured of the
    # country it came out of, not woven.
    KIND[_name] = (_r, _g, _b, 0.92, 0.0, 0.16, 0.0)

rpc.call('EditorToolset.EditorAppToolset', 'StopPIE', {})
for name, (r, g, b, rough, course, grain, plank) in KIND.items():
    path = '%s/%s.%s' % (FOLDER, name, name)
    rpc.call(AS, 'delete', {'path': path.split('.')[0]})
    rpc.call(MI, 'create', {'folder_path': FOLDER, 'asset_name': name,
                            'parent': {'refPath': WALL_MASTER if name in WALLS
                                       else MASTER}})
    rpc.call(MI, 'set_vector_parameter', {'instance': {'refPath': path},
             'name': 'DiffuseColor', 'value': {'r': r, 'g': g, 'b': b, 'a': 1.0}})
    for param, v in (('Rough', rough), ('Course', course), ('Grain', grain),
                     ('Plank', plank),
                     # Nothing composed takes a citizen's dye. A wall is a wall
                     # in every window.
                     ('Strength', 0.0), ('Shift', 0.5)):
        rpc.call(MI, 'set_scalar_parameter',
                 {'instance': {'refPath': path}, 'name': param, 'value': v})
    rpc.call(AS, 'save_assets', {'asset_paths': [path.split('.')[0]]})
    print(name)
print('NOW RUN apply.py')
