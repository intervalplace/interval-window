#!/usr/bin/env python3
"""The forty-nine goods that never had a shape.

Two thirds of this world's vocabulary was already modelled, because somebody
wears or wields it. The rest is what the world is MADE of -- ore, logs, fish,
bread, wool, arrows, a rolled charter -- and none of it had a mesh at all,
because nothing ever holds an ore. They were the items the pack drew as a
letter.

They are forged rather than fetched. There is no CC0 kit of "one hundred and
thirty medieval inventory items" that matches this project's flat, low-poly
look, and hunting one would mean either a mismatched style or a licence that
cannot ship in an open repository. Every shape here is built from the four
operations in `forge.py` -- revolve, extrude, sweep, lump -- which is the same
way the masks and the siege engine were made.

THEY ARE FAMILIES, NOT FORTY-NINE ONE-OFFS. A raw fish, a cooked fish, a burnt
fish and a salted fish are one shape and four colours, and saying so once is
both less code and a more honest description of the world: the engine treats
them as one food in four states. The same goes for the ores, the logs and the
broths. Only the things that are really different -- a sheaf of grain, a coil
of wool, a rolled charter, a bundle of arrows -- get their own hand.

  make_goods.py            writes Art/Forged/<name>.obj for each
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forge import Mesh

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'Art', 'Forged')

# The colours the goods need and the armoury did not. Flat, unlit values in the
# same register as the rest of the palette -- these are read as albedo under
# this project's own light, not as finished pixels.
# (The goods' colours live in `forge.PALETTE` itself -- see the note there:
#  `dress_forged.py` reads that dict, and a colour declared anywhere else
#  never reaches Unreal.)

# ---- the families -------------------------------------------------------

def lump(colour, seed=0, flecks=None):
    """A broken piece of something dug out of the ground.

    Three stones of different sizes leaning on each other, because one sphere
    is a ball and a ball is not an ore. The optional flecks are the reason a
    gold ore is not a grey ore with a different tint -- the metal shows in the
    stone, which is how anybody knows there is any.
    """
    m = Mesh()
    for i, (c, r, sq) in enumerate((
            ((0.0, 0.0, 6.5), 7.0, (1.0, 0.85, 0.80)),
            ((7.5, 2.0, 4.5), 5.0, (0.95, 1.0, 0.75)),
            ((-4.0, -5.5, 4.0), 4.4, (1.05, 0.9, 0.85)))):
        m.blob(c, r, colour, rings=4, segments=7, squash=sq, seed=seed + i)
    if flecks:
        for i, c in enumerate(((2.0, -3.0, 10.5), (-6.0, 1.5, 8.0),
                               (8.5, 4.0, 8.0), (0.5, 5.0, 9.5))):
            m.blob(c, 1.7, flecks, rings=3, segments=6, seed=seed + 40 + i)
    return m


def logs(bark, core):
    """Three lengths of a felled trunk, stacked as they are carried."""
    m = Mesh()
    for i, (y, z, r) in enumerate(((0.0, 8.0, 7.5), (15.0, 7.0, 6.5),
                                   (7.5, 20.0, 7.0))):
        m.tube([(-32.0, y, z), (32.0, y, z)], r, segments=9, material=bark)
        # The cut end, which is the only part of a log that is not bark.
        m.lathe([(0.0, 0.0), (r * 0.94, 0.0), (r * 0.94, 1.2), (0.0, 1.2)],
                segments=9, material=core, origin=(32.0, y, z))
    return m


def fish(colour, length=34.0, slim=False):
    """A fish seen from the side: a body, a tail and one fin.

    `slim` is the eel, which is the same animal drawn out four times as long
    and is genuinely how this world talks about them.
    """
    m = Mesh()
    half = length * 0.5
    thick = 2.2 if slim else 4.5
    deep = length * (0.07 if slim else 0.20)
    body = []
    steps = 9
    for i in range(steps + 1):
        t = i / float(steps)
        x = -half + length * 0.82 * t
        # Fat a third of the way along, tapering both ways -- the shape of
        # every fish and of nothing else.
        r = deep * math.sin(math.pi * (0.15 + 0.85 * t)) ** 0.7
        body.append(((x, 0.0, 0.0), max(r, 0.6)))
    m.tube([p for p, _ in body], [r for _, r in body], segments=7,
           material=colour)
    tail = half * 0.82
    m.plate([(0.0, 0.0), (length * 0.16, deep * 0.9),
             (length * 0.16, -deep * 0.9)], thick * 0.35, colour,
            origin=(tail, 0.0, 0.0))
    if not slim:
        m.plate([(0.0, 0.0), (-length * 0.12, deep * 1.1),
                 (length * 0.06, deep * 0.9)], thick * 0.3, colour,
                origin=(0.0, 0.0, 0.0))
    return m


def loaf(colour):
    """A round loaf with a slashed top."""
    m = Mesh()
    m.blob((0.0, 0.0, 5.0), 9.0, colour, rings=5, segments=9,
           squash=(1.1, 0.85, 0.60))
    for x in (-3.0, 0.0, 3.0):
        m.tube([(x, -4.0, 9.0), (x, 4.0, 9.0)], 0.7, segments=5,
               material=colour)
    return m


def vessel(liquid, tall=False):
    """A cup or a bowl, with what is in it.

    The liquid is a separate disc a little below the rim, which is the whole
    difference between a full bowl and an empty one.
    """
    m = Mesh()
    if tall:
        wall = [(4.2, 0.0), (4.6, 1.0), (4.6, 13.0), (5.2, 14.0), (5.2, 15.0),
                (4.4, 15.0), (4.0, 13.5), (4.0, 1.4), (3.6, 0.6), (0.0, 0.4)]
        m.lathe(wall, segments=12, material='Wood')
        # The handle.
        m.tube([(5.0, 0.0, 12.0), (8.5, 0.0, 10.0), (8.5, 0.0, 5.0),
                (5.0, 0.0, 3.0)], 0.9, segments=6, material='Wood')
        m.lathe([(0.0, 13.2), (4.2, 13.2)], segments=12, material=liquid)
    else:
        m.lathe([(7.5, 0.0), (8.0, 1.0), (9.0, 6.0), (8.2, 6.2),
                 (7.4, 1.6), (6.8, 1.0), (0.0, 0.8)],
                segments=12, material='Wood')
        m.lathe([(0.0, 5.0), (7.8, 5.0)], segments=12, material=liquid)
    return m


def sack(colour, tie='Sack'):
    """A tied sack: what flour, powder and seed are carried in."""
    m = Mesh()
    m.blob((0.0, 0.0, 9.0), 9.5, colour, rings=5, segments=9,
           squash=(1.0, 0.95, 1.05))
    m.lathe([(3.4, 17.0), (2.0, 19.0), (2.6, 21.5), (1.2, 22.5)],
            segments=8, material=tie, cap=False)
    return m


def sheaf(stalk, head):
    """A bound bundle of stalks, heavier at the top: grain, and forage."""
    m = Mesh()
    for i in range(9):
        a = 2.0 * math.pi * i / 9.0
        lean = 2.6
        bx, by = math.cos(a) * 2.0, math.sin(a) * 2.0
        tx, ty = math.cos(a) * lean * 2.4, math.sin(a) * lean * 2.4
        m.tube([(bx, by, 0.0), (bx * 1.2, by * 1.2, 14.0), (tx, ty, 26.0)],
               [0.55, 0.5, 0.45], segments=5, material=stalk)
        m.blob((tx, ty, 28.5), 2.2, head, rings=3, segments=6,
               squash=(0.55, 0.55, 1.6), seed=i)
    # The binding, which is what makes it a sheaf and not a handful.
    m.lathe([(3.4, 11.0), (3.4, 14.0)], segments=10, material='Leather',
            cap=False)
    return m


def coil(colour):
    """A rolled fleece."""
    m = Mesh()
    for i, (z, r) in enumerate(((3.5, 7.5), (9.0, 8.5), (14.5, 7.0))):
        m.blob((0.0, 0.0, z), r, colour, rings=4, segments=9,
               squash=(1.15, 1.0, 0.55), seed=i * 3)
    return m


def scroll(sealed):
    """A rolled sheet. Sealed with wax, it is a charter; open, it is a chart."""
    m = Mesh()
    m.lathe([(0.0, 0.0), (3.6, 0.0), (3.6, 26.0), (0.0, 26.0)],
            segments=11, material='Vellum')
    # The loose edge, so it reads as rolled paper rather than as a dowel.
    m.plate([(3.5, 1.0), (7.2, 3.0), (7.0, 4.2), (3.4, 2.4)], 24.0, 'Vellum',
            origin=(0.0, 0.0, 1.0))
    if sealed:
        m.lathe([(0.0, 0.0), (2.6, 0.0), (2.6, 1.0), (0.0, 1.0)],
                segments=9, material='Wax', origin=(4.4, 2.6, 13.0))
    else:
        m.tube([(0.0, 0.0, -1.5), (0.0, 0.0, 27.5)], 0.8, segments=6,
               material='Leather')
    return m


def arrows(head, lit=False):
    """A handful of arrows, points up, as they sit in a quiver.

    Shaft, head and fletching: three parts, because an arrow drawn as a stick
    is a stick. The fletching is what makes the silhouette read at the size of
    a pack slot -- it is the only part that is not a line.
    """
    m = Mesh()
    for i, (x, y, lean) in enumerate(((0.0, 0.0, 0.0), (3.6, 1.2, 1.8),
                                      (-3.2, 1.8, -1.6), (0.8, -3.0, 0.9))):
        top = 34.0
        m.tube([(x, y, 0.0), (x + lean, y, top)], 0.55, segments=5,
               material='Wood')
        m.lathe([(0.0, 0.0), (1.5, 1.0), (1.1, 2.0), (0.0, 6.0)],
                segments=6, material=head,
                origin=(x + lean, y, top))
        if lit:
            m.blob((x + lean, y, top + 7.0), 2.6, 'Ember', rings=3, segments=6,
                   squash=(0.8, 0.8, 1.5), seed=i)
        for f in range(3):
            a = 2.0 * math.pi * f / 3.0
            m.plate([(0.0, 0.0), (0.0, 7.0), (2.4, 6.0), (2.2, 0.6)],
                    0.25, 'Fletch',
                    origin=(x + math.cos(a) * 0.5, y + math.sin(a) * 0.5, 1.5))
    return m


def planks():
    m = Mesh()
    for i, (y, z) in enumerate(((0.0, 1.6), (0.0, 4.6), (1.5, 7.6))):
        m.plate([(y - 7.0, z - 1.3), (y + 7.0, z - 1.3),
                 (y + 7.0, z + 1.3), (y - 7.0, z + 1.3)], 62.0, 'Plank',
                origin=(-31.0, 0.0, 0.0))
    return m


def shell():
    """A crab's back: a domed plate with legs folded under."""
    m = Mesh()
    m.blob((0.0, 0.0, 3.0), 9.0, 'Shell', rings=5, segments=10,
           squash=(1.0, 0.82, 0.42))
    for i in range(4):
        for s in (-1.0, 1.0):
            y = 6.0 * s
            x = -4.5 + i * 3.2
            m.tube([(x, y * 0.7, 2.0), (x - 1.5, y * 1.5, 1.0),
                    (x - 3.5, y * 1.9, 3.0)], 0.8, segments=5,
                   material='Shell')
    return m


def sigil():
    """A struck disc on a thong: the world's token of a promise."""
    m = Mesh()
    m.lathe([(0.0, 0.0), (6.0, 0.0), (6.0, 1.1), (0.0, 1.1)],
            segments=14, material='Gold')
    m.lathe([(0.0, 1.1), (3.2, 1.1), (3.2, 1.8), (0.0, 1.8)],
            segments=10, material='Iron')
    m.tube([(0.0, 6.0, 0.5), (0.0, 9.5, 0.5)], 0.7, segments=6,
           material='Leather')
    return m


def graver():
    """A chisel for cutting a name into stone."""
    m = Mesh()
    m.tube([(0.0, 0.0, 0.0), (0.0, 0.0, 11.0)], [2.2, 1.8], segments=8,
           material='Wood')
    m.lathe([(1.6, 0.0), (1.6, 8.0), (0.3, 11.0), (0.0, 11.4)],
            segments=8, material='Steel', origin=(0.0, 0.0, 11.0))
    return m


def crystal(colour):
    """A grown mineral: saltpetre, and the magic stone."""
    m = Mesh()
    for i, (x, y, h, r) in enumerate(((0.0, 0.0, 14.0, 3.6),
                                      (4.2, 1.5, 9.0, 2.6),
                                      (-3.4, 2.4, 7.0, 2.2),
                                      (1.0, -3.8, 6.0, 2.0))):
        m.lathe([(0.0, 0.0), (r, 1.0), (r, h * 0.62), (0.0, h)],
                segments=6, material=colour, origin=(x, y, 0.0))
    return m


def bones(colour):
    """A few long bones crossed, with a knuckle at each end."""
    m = Mesh()
    for i, (ax, ay, bx, by, z) in enumerate((
            (-13.0, -3.0, 13.0, 2.0, 2.2),
            (-10.0, 5.0, 12.0, -5.0, 4.4),
            (-6.0, -6.0, 8.0, 7.0, 6.2))):
        m.tube([(ax, ay, z), (bx, by, z)], 1.5, segments=7, material=colour)
        for (ex, ey) in ((ax, ay), (bx, by)):
            for s in (-1.0, 1.0):
                m.blob((ex + s * 0.6, ey + s * 1.4, z + 0.6), 2.2, colour,
                       rings=3, segments=6, seed=i)
    return m


# ---- the forty-nine -----------------------------------------------------

GOODS = {
    # dug out of the ground
    'ore':          lambda: lump('Rock', 1),
    'iron-ore':     lambda: lump('Rock', 2, 'IronOre'),
    'gold-ore':     lambda: lump('Rock', 3, 'GoldOre'),
    'coal':         lambda: lump('Soot', 4),
    'brimstone':    lambda: lump('RockDark', 5, 'Sulphur'),
    'rubble':       lambda: lump('RockDark', 6),
    'charcoal':     lambda: lump('Soot', 7, 'Ember'),
    'grave-silver': lambda: lump('RockDark', 8, 'Silver'),
    'saltpetre':    lambda: crystal('Nitre'),
    'quick-stone':  lambda: crystal('Magic'),
    # cut down
    'logs':         lambda: logs('Bark', 'Wood'),
    'oak-logs':     lambda: logs('Bark', 'Oak'),
    'heartwood':    lambda: logs('Bark', 'Heartgrain'),
    'ironbark':     lambda: logs('BarkIron', 'BarkIron'),
    'planks':       planks,
    # pulled out of the water
    'raw-fish':          lambda: fish('Fish'),
    'cooked-fish':       lambda: fish('FishCooked'),
    'burnt-fish':        lambda: fish('FishBurnt'),
    'salt-fish':         lambda: fish('FishSalt'),
    'deep-fish':         lambda: fish('PottageDeep', 42.0),
    'cooked-deep-fish':  lambda: fish('FishCooked', 42.0),
    'burnt-deep-fish':   lambda: fish('FishBurnt', 42.0),
    'salt-deep-fish':    lambda: fish('FishSalt', 42.0),
    'eel':               lambda: fish('EelSkin', 52.0, True),
    'cooked-eel':        lambda: fish('FishCooked', 52.0, True),
    'burnt-eel':         lambda: fish('FishBurnt', 52.0, True),
    'smoked-eel':        lambda: fish('EelSmoked', 52.0, True),
    'lamprey-spit':      lambda: fish('EelSmoked', 46.0, True),
    'crab-shell':        shell,
    # cooked, brewed, ground
    'bread':        lambda: loaf('Crust'),
    'burnt-bread':  lambda: loaf('CrustBurnt'),
    'ale':          lambda: vessel('AleBrown', True),
    'broth':        lambda: vessel('Pottage'),
    'deep-broth':   lambda: vessel('PottageDeep'),
    'holy-water':   lambda: vessel('Water', True),
    'flour':        lambda: sack('Meal'),
    'gunpowder':    lambda: sack('Powder', 'Wax'),
    'seeds':        lambda: sack('Wheat'),
    # grown and gathered
    'grain':        lambda: sheaf('Wheat', 'Wheat'),
    'forage':       lambda: sheaf('Herb', 'Herb'),
    'wool':         lambda: coil('Fleece'),
    # written, made, left behind
    'chart':        lambda: scroll(False),
    'charter':      lambda: scroll(True),
    'sigil':        sigil,
    'graver':       graver,
    'arrows':       lambda: arrows('Iron'),
    'fire-arrows':  lambda: arrows('Iron', True),
    'bones':        lambda: bones('Bone'),
    'dragon-bones': lambda: bones('BoneDark'),
}


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    # A NAME UNREAL CAN HOLD. Asset names take no hyphens, and a good called
    # `iron-ore` would arrive as `iron_ore` anyway -- so it is written that way
    # here and the mapping is stated once, in `parts.py`, rather than guessed
    # at in three places.
    for name in sorted(GOODS):
        m = GOODS[name]()
        m.write(os.path.join(OUT, name.replace('-', '_') + '.obj'))
    print('forged %d goods into %s' % (len(GOODS), OUT))


main()
