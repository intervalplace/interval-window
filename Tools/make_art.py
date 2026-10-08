#!/usr/bin/env python3
"""Forge the meshes no CC0 kit has, into Art/Forged as OBJ.

The words this covers, and why each one had nothing:

    hare-mask, hart-mask, raven-mask, wolf-mask
        Head slots, each supposed to be a different animal's face. Nothing in
        any kit here is a mask; the animals that ARE here are whole animated
        creatures, not faces. A helmet would have been worse than a primitive,
        because a helmet says something false.
    gold-legs
        The only leg slot in the world. The armour kit has a crown, three
        helms, a cuirass and shoulder pads, and nothing for a leg.
    bone-pile, skull-pile, sheep-skull
        There are skeletons in the bestiary, but they are animated creatures.
        A heap of bones is not a creature.
    siege-engine
        Nothing close in any kit.
    horn
        An offhand item that was a cone.

Run it, then `pyrun.sh import_forged.py`, then apply.py.

EVERYTHING IS IN CENTIMETRES AND SCALED TO A PERSON. A citizen is 181cm and a
head is about 22cm across, so a mask is 20cm wide and not 90 -- the number the
keepers' hats were wrong by before anybody measured them.
"""
import math
import os
import sys

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
from forge import Mesh

OUT = os.path.join(os.path.dirname(SP), 'Art', 'Forged')


# ---------------------------------------------------------------------------
# THE MASKS.
#
# All four share a face: an oval plate, twenty centimetres across, dished so it
# sits on a head rather than standing off it like a sign. What differs is what
# is on the front -- a muzzle, a beak, ears, antlers -- which is exactly how a
# person tells them apart across a market square, and is why the four could not
# share one mesh with a tint the way the swords do.
def face_outline(w=10.0, h=13.0, chin=0.72):
    """Half-width w, half-height h. Narrower at the chin than at the brow."""
    pts = []
    for i in range(16):
        a = 2.0 * math.pi * i / 16
        taper = 1.0 if math.sin(a) > 0 else chin
        pts.append((w * math.cos(a) * taper, h * math.sin(a)))
    return pts


def mask_base(m, mat='Fur'):
    # The plate, and a shallow brow ridge so it is not a flat disc.
    m.plate(face_outline(), 2.2, mat)
    m.blob((1.0, 0.0, 6.0), 7.0, mat, rings=4, segments=10,
           squash=(0.42, 1.30, 0.55))
    # Eye holes are read as dark, not as holes: two sunken discs. Cutting real
    # holes would need a boolean and buys nothing at this camera.
    for side in (-1, 1):
        m.blob((2.4, side * 4.2, 2.6), 1.9, 'FurDark', rings=3, segments=8,
               squash=(0.5, 1.0, 0.8))


def wolf_mask():
    m = Mesh()
    mask_base(m, 'Fur')
    # A long muzzle, tapering, with a dark nose on the end.
    m.tube([(1.0, 0.0, -1.0), (6.0, 0.0, -2.2), (11.0, 0.0, -3.4)],
           [5.2, 3.8, 2.4], 10, 'Fur')
    m.blob((12.0, 0.0, -3.6), 1.7, 'FurDark', rings=3, segments=8)
    # Two upright ears, set wide.
    for side in (-1, 1):
        m.plate([(0.0, 0.0), (4.6, 0.0), (2.2, 8.0)], 1.6, 'FurDark',
                origin=(0.0, side * 5.0, 10.0))
    return m, 'wolf_mask'


def hare_mask():
    m = Mesh()
    mask_base(m, 'FurLight')
    # A short muzzle and two very long ears -- the whole of what says hare.
    m.tube([(1.0, 0.0, -2.0), (5.0, 0.0, -3.0), (7.6, 0.0, -3.6)],
           [4.4, 3.2, 2.2], 10, 'FurLight')
    m.blob((8.4, 0.0, -3.7), 1.4, 'FurDark', rings=3, segments=8)
    for side in (-1, 1):
        m.tube([(0.0, side * 3.4, 11.0), (-1.0, side * 5.0, 19.0),
                (-1.6, side * 6.0, 26.0)],
               [2.6, 2.2, 1.2], 8, 'FurLight')
    return m, 'hare_mask'


def hart_mask():
    m = Mesh()
    mask_base(m, 'Fur')
    m.tube([(1.0, 0.0, -1.5), (6.0, 0.0, -2.6), (10.0, 0.0, -3.4)],
           [4.6, 3.4, 2.2], 10, 'Fur')
    m.blob((10.8, 0.0, -3.6), 1.5, 'FurDark', rings=3, segments=8)
    # Antlers: a main beam with three tines off it, mirrored. This is the one
    # piece here that could not be a primitive under any reading of the word.
    for side in (-1, 1):
        beam = [(0.0, side * 4.0, 11.0), (-1.0, side * 7.0, 19.0),
                (-2.0, side * 8.5, 27.0), (-2.0, side * 8.0, 34.0)]
        m.tube(beam, [2.0, 1.6, 1.3, 0.9], 6, 'Keratin')
        for i, (base, tip) in enumerate((
                ((-0.8, side * 6.2, 17.0), (2.5, side * 9.0, 22.0)),
                ((-1.7, side * 8.0, 24.0), (1.5, side * 12.0, 29.0)),
                ((-2.0, side * 8.4, 31.0), (0.5, side * 12.5, 35.0)))):
            m.tube([base, tip], [1.2, 0.5], 6, 'Keratin')
    return m, 'hart_mask'


def raven_mask():
    m = Mesh()
    mask_base(m, 'Feather')
    # A long straight beak, which is the whole silhouette of this one.
    m.tube([(1.0, 0.0, -1.0), (8.0, 0.0, -2.0), (15.0, 0.0, -3.0)],
           [4.0, 2.4, 0.6], 8, 'Keratin')
    # A crest of feathers over the brow.
    for i, side in enumerate((-1, -0.4, 0.4, 1)):
        m.plate([(0.0, 0.0), (2.4, 0.0), (1.2, 7.0 - abs(side) * 2.0)], 1.0,
                'Feather', origin=(-1.0, side * 4.0, 10.0))
    return m, 'raven_mask'


# ---------------------------------------------------------------------------
# THE GREAVES. Two shells about the shins, with a knee cop over each.
def gold_legs():
    m = Mesh()
    for side in (-1, 1):
        # A half-lathe: a leg shell wraps the front of the shin, not the back.
        m.lathe([(5.4, 0.0), (6.0, 6.0), (5.6, 20.0), (4.6, 34.0), (4.2, 40.0)],
                segments=8, material='Gold', origin=(0.0, side * 9.0, 0.0),
                sweep=230.0, cap=False)
        m.blob((0.0, side * 9.0, 41.0), 6.2, 'Gold', rings=4, segments=10,
               squash=(1.0, 1.0, 0.62))
    return m, 'gold_legs'


# ---------------------------------------------------------------------------
# THE BONES.
def _long_bone(m, base, length, r=1.9, mat='Bone', tilt=(0.0, 0.0)):
    """A shaft with a knuckle at each end, which is what a bone looks like."""
    dx = math.sin(math.radians(tilt[0])) * length
    dy = math.sin(math.radians(tilt[1])) * length
    tip = (base[0] + dx, base[1] + dy, base[2] + length * 0.25)
    m.tube([base, tip], [r, r * 0.9], 6, mat)
    for end, rr in ((base, r * 1.7), (tip, r * 1.6)):
        m.blob(end, rr, mat, rings=3, segments=7, squash=(1.0, 1.3, 0.8))


def _skull(m, centre, s=1.0, mat='Bone', seed=0):
    cx, cy, cz = centre
    m.blob((cx, cy, cz), 7.0 * s, mat, rings=5, segments=9,
           squash=(1.05, 0.92, 0.95), seed=seed)
    # A snout, and two sunken sockets.
    m.tube([(cx + 4.0 * s, cy, cz - 1.0 * s), (cx + 10.0 * s, cy, cz - 2.2 * s)],
           [4.2 * s, 2.6 * s], 7, mat)
    for side in (-1, 1):
        m.blob((cx + 4.6 * s, cy + side * 3.0 * s, cz + 1.6 * s), 1.9 * s,
               'BoneDark', rings=3, segments=7)


def bone_pile():
    m = Mesh()
    for i, (x, y, z, ln, t) in enumerate((
            (-8, -4, 2, 26, (74, 10)), (2, 6, 2, 22, (60, -30)),
            (6, -7, 2, 24, (80, 40)), (-3, 2, 5, 19, (52, 70)),
            (9, 3, 3, 17, (68, -60)), (-10, 6, 3, 21, (58, 24)))):
        _long_bone(m, (x, y, z), ln, 1.8, 'Bone' if i % 2 else 'BoneDark', t)
    m.blob((0.0, 0.0, 2.0), 9.0, 'BoneDark', rings=4, segments=9,
           squash=(1.4, 1.3, 0.28))
    return m, 'bone_pile'


def skull_pile():
    m = Mesh()
    for i, (x, y, z, s) in enumerate((
            (-7, -3, 7, 1.0), (6, 4, 7, 0.92), (0, -6, 7, 0.86),
            (-1, 5, 17, 0.8), (8, -5, 6, 0.74))):
        _skull(m, (x, y, z), s, 'Bone' if i % 2 else 'BoneDark', seed=i)
    for i, (x, y, z, ln, t) in enumerate((
            (-11, 5, 2, 18, (76, 20)), (11, -2, 2, 16, (70, -40)))):
        _long_bone(m, (x, y, z), ln, 1.6, 'BoneDark', t)
    return m, 'skull_pile'


def sheep_skull():
    m = Mesh()
    _skull(m, (0.0, 0.0, 6.0), 1.0, 'Bone')
    # The horns curl back and down, which is the only thing making this a
    # sheep's skull rather than any other skull.
    for side in (-1, 1):
        path, radii = [], []
        for i in range(7):
            a = math.radians(i * 46.0)
            path.append((-2.0 - 5.0 * math.sin(a) - i * 0.6,
                         side * (4.0 + 4.0 * math.sin(a * 0.7)),
                         10.0 + 5.0 * math.cos(a) - i * 1.4))
            radii.append(2.4 - i * 0.24)
        m.tube(path, radii, 7, 'Keratin')
    return m, 'sheep_skull'


# ---------------------------------------------------------------------------
# THE HORN, which was a cone.
def horn():
    m = Mesh()
    path, radii = [], []
    for i in range(9):
        a = math.radians(i * 22.0)
        path.append((i * 4.2, 3.0 * math.sin(a), -1.2 * i + 2.0 * math.cos(a)))
        radii.append(4.4 - i * 0.42)
    m.tube(path, radii, 10, 'Keratin')
    # A banded metal mouthpiece and a rim, which is what makes it a drinking
    # horn somebody owns rather than a piece fallen off an animal.
    m.lathe([(4.6, 0.0), (5.0, 1.4), (4.6, 2.6)], 10, 'Gold',
            origin=(-0.6, 0.0, 0.0))
    return m, 'horn'


# ---------------------------------------------------------------------------
# THE SIEGE ENGINE: a trebuchet. A frame of squared timber, a throwing arm over
# the axle and a counterweight hanging off the short end.
#
# This is the one forged piece that is mostly straight beams, and that is not a
# retreat to primitives: a trebuchet IS squared timber, and what makes it a
# siege engine rather than a box is that there are fourteen beams in the right
# arrangement.
def _beam(m, a, b, r, mat='Wood'):
    m.tube([a, b], [r, r], 4, mat)


def siege_engine():
    m = Mesh()
    for side in (-1, 1):
        y = side * 40.0
        _beam(m, (-70, y, 0), (70, y, 0), 7.0, 'WoodDark')          # sill
        _beam(m, (-34, y, 0), (0, y, 118), 6.0)                     # A-frame
        _beam(m, (34, y, 0), (0, y, 118), 6.0)
        _beam(m, (-34, y, 0), (34, y, 0), 5.0, 'WoodDark')
        _beam(m, (-20, y, 62), (20, y, 62), 4.5)                    # collar
    _beam(m, (0, -40, 118), (0, 40, 118), 6.5, 'Iron')              # axle
    # The arm, long end forward and low, short end back and up.
    _beam(m, (-52, 0, 150), (96, 0, 96), 5.0)
    # The counterweight box on the short end.
    m.lathe([(0.0, 0.0), (15.0, 0.0), (15.0, 26.0), (0.0, 26.0)], 4, 'WoodDark',
            origin=(-56.0, 0.0, 120.0))
    # The sling, hanging from the long end.
    _beam(m, (96, 0, 96), (104, 0, 56), 1.2, 'Leather')
    m.blob((104, 0, 50), 7.0, 'Iron', rings=4, segments=8)
    return m, 'siege_engine'


# ---------------------------------------------------------------------------
# THE TORC, which was a cylinder about the throat.
#
# A chain at the neck is a ring of links, and a ring of links is a circle of
# tubes -- the one thing the forge does most easily. The gap at the front is
# what makes it a torc a person put on rather than a hoop dropped over them.
def torc(material='Iron', name='torc_iron'):
    m = Mesh()
    r = 7.4
    for i in range(14):
        a = math.radians(-150.0 + i * (300.0 / 13))
        cx, cy = r * math.cos(a), r * math.sin(a)
        # Alternate links stand at right angles, which is how a chain lies.
        tall = i % 2 == 0
        path = ([(cx, cy, -1.5), (cx, cy, 1.5)] if tall
                else [(cx - 1.4 * math.sin(a), cy + 1.4 * math.cos(a), 0.0),
                      (cx + 1.4 * math.sin(a), cy - 1.4 * math.cos(a), 0.0)])
        m.tube(path, [1.5, 1.5], 6, material)
    # The two finials at the open ends.
    for s in (-1, 1):
        a = math.radians(s * 152.0)
        m.blob((r * math.cos(a), r * math.sin(a), 0.0), 2.2, material,
               rings=3, segments=8)
    return m, name


def _link(m, centre, upright, material, long=5.4, wide=3.1, wire=1.15):
    """One oval link, swept as a closed loop of wire.

    The long axis always runs along the chain (z); what alternates is which
    way the OVAL faces, because that is the only thing that makes a row of
    rings read as a chain rather than as a stack of washers.
    """
    cx, cy, cz = centre
    path = []
    steps = 14
    for i in range(steps + 1):
        a = 2.0 * math.pi * (i % steps) / steps
        across = wide * math.sin(a)
        path.append((cx + (0.0 if upright else across),
                     cy + (across if upright else 0.0),
                     cz + long * math.cos(a)))
    m.tube(path, [wire] * len(path), 6, material)


def chain(material='Rust', name='old_chain'):
    """THE OLD CHAIN, which was a torc round somebody's throat.

    The world is unambiguous about what this is: `old-chain` is in the
    engine's TWO_HANDED set, it has a blow and a reach, and it is the one item
    in the world gold cannot buy. The window had it as a NECKLACE -- fourteen
    flat links about `spine_03` -- which is a reading of the word rather than
    of the world, and it meant the rarest weapon on the island was drawn as
    jewellery and could not be told from the gold chain beside it.

    Held, it hangs: nine links falling eighty-eight centimetres from the
    fist, alternating flat and upright the way a chain actually lies, with a
    heavier ring at the grip and a drift down the run so it hangs rather than
    stands. Built z-up with the grip at the origin, which is the convention
    every forged held thing here uses -- see the note over `wand` in parts.py.

    AND IT STOPS ABOVE THE GROUND. A citizen's fist is about ninety
    centimetres up when they are standing, so a chain longer than that lies
    through the paving rather than on it.

    HEAVY LINKS, AND THAT IS NOT A STYLE CHOICE. The first cut of this had
    twenty-six links at two centimetres each, which is what a real chain of
    this length is and which photographed as a thin brown LINE: at the
    distance this camera stands, a citizen of 181 cm is about sixty pixels, so
    a two-centimetre link is well under one. Six-centimetre links read as
    links. The rule this window keeps running into is that a thing modelled at
    life size is not the same as a thing legible at the size it is drawn, and
    the drawing is what there is.
    """
    m = Mesh()
    links = 9
    pitch = 8.6
    for i in range(links):
        z = -(i + 1) * pitch
        # A HANG, NOT A ROD. A chain held out straight is a bar; the drift is
        # small and grows down the run, which is what weight looks like.
        lean = (i / float(links)) ** 2
        _link(m, (3.4 * lean, 1.2 * lean, z), i % 2 == 0, material)
    # The ring at the grip, heavier because it is the one taking the weight.
    _link(m, (0.0, 0.0, -1.0), True, material,
          long=7.0, wide=4.6, wire=1.5)
    return m, name


def old_chain():
    return chain('Rust', 'old_chain')


def gold_chain():
    return chain('Gold', 'gold_chain')


def torc_iron():
    return torc('Iron', 'torc_iron')


def torc_gold():
    return torc('Gold', 'torc_gold')


# ---------------------------------------------------------------------------
# THE ROD, which was two scaled cylinders.
#
# It was defended as already being exactly what a rod is -- a tapered pole with
# a line off the tip -- and that defence was refused along with the rest. A rod
# a person owns has a bound grip, a whipping where the sections join and a reel
# on it, and none of those is a cylinder.
def fishing_rod():
    m = Mesh()
    # The pole: three sections, each thinner, with a whipping between them.
    m.tube([(0, 0, 0), (0, 0, 52)], [1.30, 1.02], 8, 'Wood')
    m.tube([(0, 0, 52), (0, 0, 108)], [1.00, 0.72], 8, 'WoodDark')
    m.tube([(0, 0, 108), (0, 0, 168)], [0.70, 0.30], 6, 'Wood')
    for z in (52, 108):
        m.lathe([(1.2, 0.0), (1.4, 1.6), (1.2, 3.0)], 8, 'Leather',
                origin=(0.0, 0.0, z - 1.5))
    # The grip, bound in leather, and the butt cap.
    m.lathe([(1.7, 0.0), (1.9, 6.0), (1.9, 20.0), (1.6, 24.0)], 8, 'Leather')
    m.lathe([(1.9, 0.0), (2.1, 1.6), (1.6, 2.6)], 8, 'Iron',
            origin=(0.0, 0.0, -2.6))
    # The reel, off one side above the grip.
    m.lathe([(0.0, 0.0), (3.4, 0.0), (3.4, 2.2), (0.0, 2.2)], 10, 'Iron',
            origin=(0.0, 3.0, 28.0))
    # And the line, from the tip down past the rod -- two millimetres of it,
    # which is nothing to draw and is the whole reason the silhouette reads.
    m.tube([(0, 0, 168), (6, 0, 120), (9, 0, 58)], [0.22, 0.20, 0.18], 4, 'Cloth')
    return m, 'fishing_rod'


# ---------------------------------------------------------------------------
# THE WAND, which was a staff shrunk to a fifth.
#
# Scaling a two-metre staff down to forty centimetres does not make a wand. It
# makes a twig, and it keeps the staff's proportions -- a thick shaft with a
# head on it -- at a size where those proportions read as a broken branch. A
# wand is its own object: short, turned, and thin enough that the hand around
# it is most of what you see.
#
# Thirty-four centimetres, because that is a forearm, and a wand that cannot be
# worn up a sleeve is a baton.
def wand():
    m = Mesh()
    # The shaft, tapering to almost nothing. Two sections so the taper is not
    # a single straight cone, which is the shape that reads as a dowel.
    m.tube([(0, 0, 8), (0, 0, 22)], [0.82, 0.62], 8, 'WoodDark')
    m.tube([(0, 0, 22), (0, 0, 34)], [0.60, 0.26], 6, 'WoodDark')
    # The grip: leather over the lower third, with the turn at the top of it.
    m.lathe([(0.95, 0.0), (1.08, 1.4), (1.08, 7.2), (0.92, 8.6)], 8, 'Leather')
    # A ferrule where the binding stops, and a butt cap, both iron. These two
    # rings are what say somebody made this rather than cut it.
    m.lathe([(1.02, 0.0), (1.14, 1.0), (1.02, 1.9)], 8, 'Iron',
            origin=(0.0, 0.0, 8.4))
    m.lathe([(1.00, 0.0), (1.12, 0.9), (0.70, 1.7)], 8, 'Iron',
            origin=(0.0, 0.0, -1.7))
    # AND THE SET STONE. A wand ends in something, or it is a stick: four
    # claws of iron closing on a stone, which is how a stone is held in
    # anything a person could actually carry.
    for i in range(4):
        a = math.radians(45.0 + i * 90.0)
        m.tube([(0.30 * math.cos(a), 0.30 * math.sin(a), 33.0),
                (0.95 * math.cos(a), 0.95 * math.sin(a), 36.4)],
               [0.30, 0.20], 4, 'Iron')
    m.blob((0.0, 0.0, 36.6), 1.35, 'Magic', rings=4, segments=8)
    return m, 'wand'


# ---------------------------------------------------------------------------
# THE FIRE-SIPHON, which was a torch.
#
# A torch at least burns at the right end, which is the whole of what it had
# going for it. A siphon is not a burning thing; it is a PUMP -- a bronze
# cylinder with a plunger in the butt, a tank of the stuff it throws slung
# under it, and a narrow nozzle that the flame comes out of some way past the
# hand. Held out, the silhouette is long and straight with a lump underneath,
# and nothing about that is a torch.
#
# Seventy-two centimetres: a two-handed thing, held out and away from you,
# which is what everybody who ever used one did with it.
def fire_siphon():
    m = Mesh()
    # The barrel, bronze, in two courses so the joint can be banded.
    m.tube([(0, 0, 6), (0, 0, 34)], [3.10, 2.95], 10, 'Gold')
    m.tube([(0, 0, 34), (0, 0, 56)], [2.85, 2.40], 10, 'Gold')
    # Iron bands: at the breech, at the joint and under the nozzle. Three,
    # because a bronze tube with no bands on it is a length of pipe.
    for z in (7.5, 33.0, 54.0):
        m.lathe([(3.15, 0.0), (3.45, 1.1), (3.15, 2.2)], 10, 'Iron',
                origin=(0.0, 0.0, z))
    # The nozzle, stepping down twice to a mouth a finger across, and a flare
    # at the end so the flame has somewhere to leave from.
    m.tube([(0, 0, 56), (0, 0, 66)], [2.20, 1.15], 8, 'Iron')
    m.lathe([(1.15, 0.0), (1.85, 2.4), (1.55, 3.2)], 8, 'Iron',
            origin=(0.0, 0.0, 66.0))
    # THE TANK, slung under the barrel and off to one side, which is where the
    # weight of one actually hung. This is the lump that makes the silhouette.
    m.lathe([(0.0, 0.0), (3.6, 1.2), (4.2, 5.0), (4.2, 13.0),
             (3.4, 16.4), (0.0, 17.6)], 10, 'Iron', origin=(0.0, -5.2, 12.0))
    # The feed pipe from the tank into the breech.
    m.tube([(0.0, -5.2, 27.0), (0.0, -2.6, 30.5), (0.0, 0.0, 31.0)],
           [0.85, 0.85, 0.85], 6, 'Gold')
    # The plunger out of the butt, with its handle across: this is the part
    # that says pump, and it is the part a torch could never have.
    m.lathe([(3.35, 0.0), (3.55, 1.6), (3.10, 2.8)], 10, 'Iron',
            origin=(0.0, 0.0, 3.2))
    m.tube([(0, 0, -11), (0, 0, 4)], [0.95, 0.95], 6, 'Steel')
    m.tube([(-4.4, 0, -11.6), (4.4, 0, -11.6)], [1.15, 1.15], 6, 'WoodDark')
    # And the grip, wound leather where the off hand takes it.
    m.lathe([(3.05, 0.0), (3.25, 1.2), (3.25, 8.4), (3.00, 9.6)], 10,
            'Leather', origin=(0.0, 0.0, 16.0))
    return m, 'fire_siphon'


# ---------------------------------------------------------------------------
# THE HANDGONNE, which was a mallet.
#
# `Hammer_Small` is not a near miss. A citizen firing a gun swung a hammer,
# which is wrong about the silhouette, wrong about the length and wrong about
# what the thing is for -- and the pack sprite said the same, because it showed
# a bow. There is nothing like it in any kit here, so it is forged.
#
# The shape is the fifteenth-century one and it barely changed for a hundred
# years: a short thick iron barrel socketed onto a wooden tiller that goes
# under the arm, a touch-hole with a pan beside it, and no lock of any kind --
# you fired it with a match in your other hand. Ninety-eight centimetres, most
# of which is pole.
def handgonne():
    m = Mesh()
    # The tiller: a stout pole, squared a little at the butt where it sits
    # under the arm.
    m.tube([(0, 0, 0), (0, 0, 48)], [2.35, 2.05], 8, 'WoodDark')
    m.tube([(0, 0, 48), (0, 0, 60)], [2.05, 2.30], 8, 'WoodDark')
    m.lathe([(2.55, 0.0), (2.80, 1.8), (2.20, 3.4)], 8, 'Iron',
            origin=(0.0, 0.0, -3.4))
    # The socket: the barrel's tail is a cone driven onto the tiller, and the
    # step where it stops is the loudest line on the whole thing.
    m.lathe([(2.35, 0.0), (3.30, 4.0), (3.55, 9.0)], 10, 'Iron',
            origin=(0.0, 0.0, 55.0))
    # The barrel, thick at the breech where the charge sits and thinner at the
    # muzzle, which is the only reason a gun of this age looks like a gun.
    m.tube([(0, 0, 64), (0, 0, 84)], [3.55, 3.05], 10, 'Iron')
    m.tube([(0, 0, 84), (0, 0, 95)], [3.00, 2.80], 10, 'Iron')
    # Reinforcing rings, thickest over the powder.
    for z, r in ((66.0, 3.85), (78.0, 3.45), (91.0, 3.10)):
        m.lathe([(r, 0.0), (r + 0.45, 1.3), (r, 2.6)], 10, 'Iron',
                origin=(0.0, 0.0, z))
    # The muzzle: a flare, and the bore sunk into it so the end is a hole
    # rather than a disc. A gun whose muzzle is capped reads as a club.
    m.lathe([(2.80, 0.0), (3.40, 1.6), (3.30, 2.6), (2.05, 2.9),
             (2.00, -3.6)], 10, 'Iron', origin=(0.0, 0.0, 95.0), cap=False)
    # The touch-hole pan, out on the side over the breech, with its little
    # fence: the one detail that says this is fired with a match.
    m.lathe([(0.0, 0.0), (1.9, 0.0), (1.9, 1.5), (1.05, 1.5)], 8, 'Iron',
            origin=(3.3, 0.0, 69.0))
    m.tube([(3.3, 0.0, 66.5), (3.3, 0.0, 69.2)], [0.45, 0.45], 4, 'Soot')
    # And the hand: wound cord where the forward hand grips the tiller.
    m.lathe([(2.30, 0.0), (2.55, 1.2), (2.55, 11.0), (2.25, 12.2)], 8,
            'Leather', origin=(0.0, 0.0, 30.0))
    return m, 'handgonne'


# ---------------------------------------------------------------------------
# THE CROSSBOWS, which were a bow.
#
# The world has two of them and is emphatic about both: `crossbow` wants
# marksmanship 25, `great-crossbow` wants 70, breaks what it hits and burns.
# The window drew each as `Bow_Wooden2`, which is a longbow -- and a longbow
# and a crossbow have nothing in common but a string. One is a tall D held
# upright beside the body; the other is a short wide cross held level and
# pointed, and at this camera the difference is the whole silhouette.
#
# A crossbow is a TILLER with a PROD across its nose, a nut where the string is
# caught and a lever under it. The prod is short and stiff and bends almost not
# at all, which is why it is drawn nearly straight: a crossbow prod that curves
# like a bow's limb is a bow lying on its side.
def _crossbow(m, span, tiller, prod_r, wood, metal, string='Fletch'):
    """One crossbow. `span` is tip to tip across; `tiller` is butt to nose."""
    half = span * 0.5
    # THE TILLER, along +Z: butt at the shoulder, nose at the far end. Squared
    # rather than round, because a stock is carved from a plank.
    m.tube([(0, 0, 0), (0, 0, tiller * 0.62)], [2.35, 2.05], 4, wood)
    m.tube([(0, 0, tiller * 0.62), (0, 0, tiller)], [2.05, 1.75], 4, wood)
    # The butt, flared where it sits against the shoulder.
    m.lathe([(2.6, 0.0), (3.1, 1.6), (2.4, 3.2)], 4, wood,
            origin=(0.0, 0.0, -3.2))
    # THE PROD, across +Y at the nose, nearly straight and tapering to the
    # tips. Three sections a side so it has some sweep without being a bow.
    for side in (-1, 1):
        m.tube([(0.0, 0.0, tiller - 3.0),
                (0.0, side * half * 0.45, tiller - 2.4),
                (0.0, side * half * 0.80, tiller - 1.0),
                (0.0, side * half, tiller + 1.2)],
               [prod_r, prod_r * 0.86, prod_r * 0.66, prod_r * 0.40], 6, metal)
    # THE STRING, caught at the nut and run to both tips. Drawn slack-side
    # back, which is how one is carried.
    for side in (-1, 1):
        m.tube([(0.0, side * half, tiller + 1.2),
                (0.0, side * half * 0.5, tiller * 0.74),
                (0.0, 0.0, tiller * 0.60)],
               [0.34, 0.34, 0.34], 4, string)
    # The bridle that lashes the prod to the tiller: two turns of cord, which
    # is how every one of these was actually held together.
    for z in (tiller - 3.6, tiller - 1.6):
        m.lathe([(2.4, 0.0), (2.75, 0.7), (2.4, 1.4)], 6, 'Leather',
                origin=(0.0, 0.0, z))
    # The nut in its housing, and the groove the bolt lies in: two lines down
    # the top of the tiller, which is what says this is aimed and not drawn.
    m.lathe([(1.9, 0.0), (2.3, 1.2), (1.9, 2.4)], 8, metal,
            origin=(0.0, 0.0, tiller * 0.60))
    m.tube([(0.0, 0.0, tiller * 0.62), (0.0, 0.0, tiller - 2.0)],
           [0.55, 0.55], 4, 'Soot')
    # AND THE LEVER UNDER IT, which no bow has and every crossbow does.
    m.tube([(1.9, 0.0, tiller * 0.58), (3.4, 0.0, tiller * 0.46)],
           [0.75, 0.55], 4, metal)


def crossbow():
    # Seventy-two centimetres of tiller and a sixty-centimetre prod: a plain
    # one, wood and iron, that a citizen at marksmanship 25 could carry.
    m = Mesh()
    _crossbow(m, span=60.0, tiller=72.0, prod_r=1.9, wood='WoodDark',
              metal='Iron')
    return m, 'crossbow'


def great_crossbow():
    # The siege one: a metre of tiller, a steel prod nearly a metre across,
    # and a STIRRUP at the nose -- the iron loop you put a boot through to span
    # it, which is the plainest possible sign that this is not drawn by hand.
    m = Mesh()
    _crossbow(m, span=96.0, tiller=104.0, prod_r=2.6, wood='Oak',
              metal='Steel')
    # The stirrup, hanging forward and down off the nose.
    m.tube([(0.0, -3.2, 101.0), (0.0, -6.0, 107.0), (0.0, 0.0, 112.0),
            (0.0, 6.0, 107.0), (0.0, 3.2, 101.0)],
           [0.95, 0.95, 0.95, 0.95, 0.95], 5, 'Steel')
    # And the windlass: a cranked drum on the butt with its cord, which is the
    # other half of why this one takes a minute to load and hits for twelve.
    m.lathe([(0.0, 0.0), (3.0, 0.6), (3.0, 5.2), (0.0, 5.8)], 8, 'WoodDark',
            origin=(0.0, 0.0, 5.0))
    m.tube([(0.0, 0.0, 10.8), (0.0, 4.6, 12.6)], [0.60, 0.60], 4, 'Steel')
    m.tube([(0.0, 4.6, 12.6), (0.0, 4.6, 16.4)], [0.75, 0.75], 4, 'WoodDark')
    return m, 'great_crossbow'


# ---------------------------------------------------------------------------
# THE STAR-FLAIL, which was a double-headed hammer.
#
# The world gives it prowess 55 and `pierces`, and a hammer pierces nothing.
# A flail is a haft, a length of CHAIN and a head that swings on the end of it,
# and the chain is the whole point: it is why the thing goes round a shield.
# The links are the same `_link` the old chain is made of, so the two read as
# the same metalwork by the same hands.
def star_flail():
    m = Mesh()
    # BUILT RUNNING DOWN -Z, like the chain and for the same reason: the sway
    # in `hang.hlsl` measures how far a vertex is BELOW the grip, and anything
    # built the other way up gets a drop of zero and stands out of the fist
    # like an arrow. See the note over `Local` in hang.hlsl.
    #
    # The haft is rigid and the shader cannot know that, so it flexes by a
    # quarter of the amplitude at its far end -- three and a half centimetres,
    # which is a pixel at the distance this camera stands, and cheaper than a
    # second material for one weapon.
    # The haft: short, because a flail is swung and not thrust.
    m.tube([(0, 0, 0), (0, 0, -38)], [1.55, 1.40], 8, 'WoodDark')
    m.lathe([(1.75, 0.0), (2.05, -1.3), (1.55, -2.6)], 8, 'Steel',
            origin=(0.0, 0.0, 2.6))
    m.lathe([(1.55, 0.0), (1.80, -1.2), (1.80, -10.0), (1.50, -11.2)], 8,
            'Leather', origin=(0.0, 0.0, -3.0))
    # The cap and the swivel ring the chain hangs from.
    m.lathe([(1.45, 0.0), (1.95, -1.4), (1.60, -2.8)], 8, 'Steel',
            origin=(0.0, 0.0, -38.0))
    _link(m, (0.0, 0.0, -43.6), True, 'Steel', long=4.6, wide=2.8, wire=1.0)
    # THREE LINKS, alternating upright and flat the way a real chain lies.
    for i in range(3):
        _link(m, (0.0, 0.0, -47.6 - i * 3.8), i % 2 == 1, 'Steel',
              long=4.8, wide=2.9, wire=1.05)
    # THE HEAD, and it is quick metal: a ball with eight spikes, because
    # `pierces` is a thing the world says about this and not about a mell.
    head_z = -62.0
    m.blob((0.0, 0.0, head_z), 4.4, 'Silver', rings=5, segments=10)
    for i in range(8):
        a = math.radians(i * 45.0)
        tilt = 0.55 if i % 2 else -0.55
        m.tube([(3.2 * math.cos(a), 3.2 * math.sin(a), head_z + tilt),
                (7.6 * math.cos(a), 7.6 * math.sin(a), head_z + tilt * 2.4)],
               [1.30, 0.18], 4, 'Silver')
    m.tube([(0.0, 0.0, head_z - 3.6), (0.0, 0.0, head_z - 8.2)],
           [1.30, 0.18], 4, 'Silver')
    m.tube([(0.0, 0.0, head_z + 3.6), (0.0, 0.0, head_z + 7.4)],
           [1.30, 0.18], 4, 'Silver')
    return m, 'star_flail'


# ---------------------------------------------------------------------------
# THE BARB, which was a dagger.
#
# Prowess 45 and `cleaves`, which is a thing four weapons in the world do and
# a dagger is not one of them. A barb is a HOOK: a heavy curved blade with the
# edge on the inside and a spur off the back, the shape you pull rather than
# push. Drawn short, because the world gives it reach 1.
def barb():
    m = Mesh()
    # The grip, and a guard that is only a disc -- there is no fencing with
    # this.
    m.lathe([(0.0, 0.0), (1.55, 0.8), (1.70, 2.0), (1.70, 10.5),
             (1.40, 12.0)], 8, 'Leather')
    m.lathe([(2.6, 0.0), (2.9, 0.9), (2.2, 1.8)], 8, 'Iron',
            origin=(0.0, 0.0, 12.0))
    m.lathe([(1.5, 0.0), (1.9, 1.1), (1.2, 2.2)], 8, 'Iron',
            origin=(0.0, 0.0, -2.2))
    # THE BLADE, swept forward and round: a plate lathed along a curve would
    # not do it, so it is a run of flattened tube that turns through most of a
    # right angle and thins as it goes.
    pts, radii = [], []
    for i in range(7):
        t = i / 6.0
        a = math.radians(t * 86.0)
        r = 15.0
        pts.append((r * math.sin(a), 0.0, 14.0 + r * (1.0 - math.cos(a))))
        radii.append(2.30 - 1.85 * t)
    m.tube(pts, radii, 4, 'Steel')
    # The edge, on the INSIDE of the curve, as a thin lip: which side a hook
    # cuts on is the only thing anybody needs to read about it.
    lip, lipr = [], []
    for i in range(7):
        t = i / 6.0
        a = math.radians(t * 86.0)
        r = 12.6
        lip.append((r * math.sin(a), 0.0, 14.6 + r * (1.0 - math.cos(a))))
        lipr.append(0.85 - 0.55 * t)
    m.tube(lip, lipr, 3, 'Steel')
    # AND THE SPUR off the back of the curve, which is the barb itself.
    m.tube([(6.4, 0.0, 19.0), (10.6, 0.0, 15.6)], [1.40, 0.16], 4, 'Steel')
    return m, 'barb'


# ---------------------------------------------------------------------------
# THE TWO STAVES THE WORLD MADE GAMBIT, which were the same generic staff.
#
# There are four staff words and one mesh. Two of them deserve that: `staff`
# and `heartwood-staff` are the same stick in a better wood, which is what the
# world means by them. The other two are not:
#
#   bone-staff  sorcery 40, and eight hundred and eighty gold
#   goo-staff   sorcery 70 -- the highest requirement on anything in the world
#
# A citizen who has spent a year reaching sorcery 70 and holds the rarest
# implement there is should not be carrying the same stick as the newcomer
# beside them. That is the whole argument for this file.
def bone_staff():
    m = Mesh()
    # A shaft of long bones lashed end to end -- three sections with a binding
    # at each joint, so it reads as ASSEMBLED and not as carved wood.
    m.tube([(0, 0, 0), (0, 0, 44)], [1.55, 1.45], 7, 'Bone')
    m.tube([(0, 0, 44), (0, 0, 88)], [1.45, 1.35], 7, 'Bone')
    m.tube([(0, 0, 88), (0, 0, 124)], [1.35, 1.20], 7, 'BoneDark')
    for z in (44.0, 88.0):
        m.lathe([(1.55, 0.0), (1.90, 1.0), (1.90, 3.2), (1.55, 4.2)], 7,
                'Leather', origin=(0.0, 0.0, z - 2.1))
    m.lathe([(1.35, 0.0), (1.75, 1.1), (1.20, 2.2)], 7, 'BoneDark',
            origin=(0.0, 0.0, -2.2))
    # THE SKULL at the head, small and tilted, held in a cradle of four ribs.
    _skull(m, (0.0, 0.0, 131.0), 0.62, 'Bone', seed=3)
    for i in range(4):
        a = math.radians(45.0 + i * 90.0)
        m.tube([(1.0 * math.cos(a), 1.0 * math.sin(a), 123.0),
                (3.1 * math.cos(a), 3.1 * math.sin(a), 130.0),
                (2.0 * math.cos(a), 2.0 * math.sin(a), 136.5)],
               [0.55, 0.42, 0.26], 4, 'BoneDark')
    return m, 'bone_staff'


def goo_staff():
    m = Mesh()
    # A shaft that is not straight: this is the one thing in the world that
    # wants sorcery seventy, and it should look like it grew rather than like
    # it was cut. Four sections, each leaning a little further.
    path = [(0.0, 0.0, 0.0), (1.2, 0.6, 34.0), (0.4, -0.8, 66.0),
            (2.0, 0.5, 96.0), (1.0, 0.0, 120.0)]
    m.tube(path, [1.70, 1.55, 1.50, 1.60, 1.35], 8, 'Bark')
    m.lathe([(1.80, 0.0), (2.15, 1.1), (1.55, 2.2)], 8, 'BarkIron',
            origin=(0.0, 0.0, -2.2))
    m.lathe([(1.65, 0.0), (1.95, 1.2), (1.95, 9.0), (1.60, 10.2)], 8,
            'Leather', origin=(0.6, 0.3, 22.0))
    # THE HEAD: a socket of iron claws holding a mass of the stuff, with three
    # gouts of it hanging off and stretching down the shaft. The drips are the
    # silhouette -- a blob on a stick is a mace.
    for i in range(3):
        a = math.radians(30.0 + i * 120.0)
        m.tube([(1.0 + 0.9 * math.cos(a), 0.9 * math.sin(a), 116.0),
                (1.0 + 3.4 * math.cos(a), 3.4 * math.sin(a), 122.0)],
               [0.70, 0.45], 4, 'BarkIron')
    m.blob((1.0, 0.0, 126.0), 5.2, 'Herb', rings=5, segments=10,
           squash=(1.0, 1.0, 1.15))
    for i, (dx, dy, drop, r) in enumerate((
            (3.6, 1.2, 11.0, 1.55), (-2.2, 3.0, 7.5, 1.20),
            (-1.4, -3.4, 14.0, 1.35))):
        m.tube([(1.0 + dx, dy, 124.0),
                (1.0 + dx * 1.05, dy * 1.05, 124.0 - drop * 0.55),
                (1.0 + dx * 0.95, dy * 0.95, 124.0 - drop)],
               [r, r * 0.72, 0.18], 5, 'Herb')
        m.blob((1.0 + dx * 0.95, dy * 0.95, 124.0 - drop - 1.1), r * 0.8,
               'Herb', rings=3, segments=7)
    return m, 'goo_staff'


# ---------------------------------------------------------------------------
# THE KING-SHROUD, which was the same cuirass as an iron plate.
#
# It is the best body armour in the world -- 22 against iron-plate's 9 -- it
# costs eight hundred gold, it wants prowess 40, and a citizen wearing one
# looked exactly like a citizen in the cheapest plate there is. A shroud is
# not a breastplate either: it is a mantle, cloth over mail, with a hood.
#
# Built about the origin so it hangs from the shoulders, and deliberately
# ASYMMETRIC -- the drape falls further on one side -- because a cloak drawn
# symmetrically reads as a tabard on a coat-hanger.
def king_shroud():
    m = Mesh()
    # The mail underneath, a short shirt about the chest.
    m.lathe([(0.0, 18.0), (16.5, 15.0), (18.0, 6.0), (18.5, -10.0),
             (17.0, -22.0)], 12, 'Steel')
    # THE MANTLE over it: a cone of cloth off the shoulders, cut away at the
    # front so the mail shows. Two lathes, the second longer and turned, which
    # is the whole of the asymmetry.
    m.lathe([(2.0, 22.0), (14.0, 19.0), (20.0, 6.0), (23.0, -14.0),
             (24.0, -30.0)], 12, 'Cloth')
    m.lathe([(0.0, 20.0), (12.0, 17.0), (19.0, 2.0), (22.5, -20.0),
             (23.0, -41.0)], 12, 'Cloth', origin=(-3.5, 2.0, 0.0))
    # THE HOOD, thrown back: a half-dome behind the neck with a fold at its
    # mouth. This is the piece that says shroud from behind, which is where
    # this camera usually is.
    m.blob((-11.0, 0.0, 19.0), 9.5, 'Cloth', rings=4, segments=10,
           squash=(0.85, 1.05, 1.15))
    m.lathe([(7.0, 0.0), (9.8, 3.0), (9.4, 6.5), (6.4, 8.0)], 10, 'Cloth',
            origin=(-9.0, 0.0, 22.0))
    # The collar band and the clasp, which is where the gold in eight hundred
    # gold went.
    m.lathe([(9.5, 0.0), (11.2, 2.0), (10.6, 4.4)], 12, 'Gold',
            origin=(0.0, 0.0, 19.0))
    m.blob((9.6, 0.0, 19.5), 2.4, 'Gold', rings=3, segments=8,
           squash=(0.6, 1.0, 1.0))
    # And the hem, weighted, so the cloth ends in a line rather than a fade.
    m.lathe([(24.0, 0.0), (25.0, -1.6), (23.4, -3.0)], 12, 'Gold',
            origin=(0.0, 0.0, -30.0))
    return m, 'king_shroud'


# ---------------------------------------------------------------------------
# THE JAVELIN, which was a spear.
#
# Three of them -- iron, steel and quick -- all drawn as `Spear`, the same mesh
# as the three spears they are not. The world is clear that they are different
# weapons: a spear is reach 2 and melee, a javelin is reach 3, `ranged` and
# `selfAmmo`, which is to say you throw it and then it is gone.
#
# A thrown shaft is SHORTER and MUCH thinner than a thrust one, and it carries
# a thong at the balance point -- the loop your fingers go through, which is
# what doubles the range and is the one detail that names the weapon.
def javelin():
    m = Mesh()
    # The shaft: a hundred and forty, against a spear's two metres, and half
    # the thickness. Tapered from the grip to both ends.
    m.tube([(0, 0, 0), (0, 0, 52)], [0.90, 1.10], 6, 'Wood')
    m.tube([(0, 0, 52), (0, 0, 124)], [1.10, 0.85], 6, 'Wood')
    # The butt, capped, because a javelin stands in the ground between throws.
    m.lathe([(0.95, 0.0), (1.15, -1.2), (0.55, -2.6)], 6, 'Iron',
            origin=(0.0, 0.0, 0.0))
    # THE HEAD: a long narrow leaf with a socket, and barbs at the shoulder.
    m.lathe([(0.90, 0.0), (1.55, 2.0), (1.45, 6.0)], 6, 'Iron',
            origin=(0.0, 0.0, 124.0))
    m.tube([(0, 0, 130), (0, 0, 137), (0, 0, 148)],
           [1.45, 2.05, 0.12], 4, 'Iron')
    for side in (-1, 1):
        m.tube([(0.0, side * 0.9, 131.0), (0.0, side * 3.2, 127.6)],
               [0.85, 0.10], 3, 'Iron')
    # AND THE THONG, wound at the balance and left in a loop. This is the
    # javelin.
    m.lathe([(1.12, 0.0), (1.55, 1.0), (1.55, 5.6), (1.12, 6.8)], 6,
            'Leather', origin=(0.0, 0.0, 49.0))
    m.tube([(1.5, 0.0, 52.0), (4.6, 1.2, 49.0), (5.0, 0.0, 44.0),
            (3.0, -1.4, 43.0), (1.5, 0.0, 46.0)],
           [0.42, 0.42, 0.42, 0.42, 0.42], 4, 'Leather')
    return m, 'javelin'


# ---------------------------------------------------------------------------
# THE POUCH, for the two things that were bricks and are not bars.
#
# Seven items take the weapon slot and are not weapons, and a bar of metal IS
# a cuboid, so `Brick` is an honest ingot for gold-bar, iron, steel,
# quick-alloy and quick-ingot. Two of the seven are not bars at all:
#
#   shot       lead balls for a handgonne
#   quick-grit  grit, which is by definition not a shape
#
# Neither is a brick and both are carried the same way -- loose, in a bag, tied
# at the neck. One pouch does both; what differs is what is spilling out of it.
def _pouch(m, fill, name_mat):
    # The bag: a lathe that bulges low and pinches at the neck, which is what
    # a bag full of heavy small things actually does.
    m.lathe([(0.0, 0.0), (5.4, 1.2), (7.2, 4.4), (7.0, 9.0),
             (4.6, 12.4), (3.0, 14.2), (3.2, 16.0), (0.0, 16.6)], 10, 'Sack')
    # The tie, and the two ends of the cord left hanging.
    m.lathe([(3.1, 0.0), (3.9, 0.8), (3.9, 2.0), (3.1, 2.8)], 10, 'Leather',
            origin=(0.0, 0.0, 12.8))
    for side in (-1, 1):
        m.tube([(2.8 * side, 0.6 * side, 13.8), (5.6 * side, 1.4 * side, 11.0),
                (6.2 * side, 0.8 * side, 7.4)],
               [0.34, 0.30, 0.16], 3, 'Leather')
    # And what is in it, spilling at the neck: three of them, so the eye can
    # tell lead shot from quick grit without reading the label.
    for i, (dx, dy, dz, r) in enumerate(fill):
        m.blob((dx, dy, dz), r, name_mat, rings=3, segments=7)


def shot():
    m = Mesh()
    _pouch(m, ((0.0, 0.0, 16.8, 1.85), (2.3, 1.0, 16.2, 1.65),
               (-1.6, -1.8, 16.0, 1.55), (4.6, -0.6, 2.2, 1.75)), 'Iron')
    return m, 'shot'


def star_grit():
    m = Mesh()
    # Grit is smaller and there is more of it, and it is quick metal.
    _pouch(m, ((0.0, 0.6, 16.6, 1.05), (1.9, -0.8, 16.4, 0.85),
               (-1.7, 1.2, 16.2, 0.95), (0.8, 2.0, 15.9, 0.75),
               (3.4, 1.2, 1.6, 0.90), (-3.0, -2.2, 1.4, 0.80)), 'Silver')
    return m, 'star_grit'


# ---------------------------------------------------------------------------
# THE TWO BOWS THAT WERE THE SAME LONGBOW.
#
# `audit_items.py` counts a FAMILY as one noun in several metals or woods, and
# `hollow` and `horn` were listed as grades so that `hollow-bow` and `horn-bow`
# came back as a family and nobody looked. They are not:
#
#   hollow-bow  45 gold. hit 2, accuracy -10, and `noAmmo` with `selfAmmo`:
#               it needs no arrows because it makes its own.
#   horn-bow    400 gold. hit 8, reach 5, and a FLURRY -- three blows with a
#               six-tick recovery, one of the four gambits in the world.
#
# Forty-five gold against four hundred, and a gambit. Drawing both as
# `Bow_Wooden2` -- which is a LONGBOW, a tall D -- says neither.
#
# Both are built centred on the grip, limbs running along Z, because that is
# where a bow is held. The other forged weapons run from the grip upward; a bow
# is the one thing in the hand whose middle is the part you hold.
def _limb(m, up, reach, sweep, tip, mat, back):
    """One limb, from the grip out to its tip. `up` is +1 or -1 along Z.

    A RECURVE IS TWO CURVES, which is the whole of why it is worth drawing at
    all: the limb bends away from the archer and then the last part of it turns
    BACK toward them. A limb drawn as one arc is a longbow lying on its side.
    """
    pts, radii, backs = [], [], []
    for i in range(9):
        t = i / 8.0
        # away for the first three quarters, and back over the last quarter
        bend = math.sin(t * math.pi * 0.78)
        curl = max(0.0, t - 0.74) / 0.26
        x = -sweep * bend + tip * curl * curl
        z = up * reach * t
        pts.append((x, 0.0, z))
        radii.append(1.55 - 1.05 * t)
        backs.append((x - 0.9, 0.0, z))
    m.tube(pts, radii, 6, mat)
    # THE SINEW ON THE BACK, a darker strip glued the length of the limb: the
    # one detail that says composite rather than carved.
    m.tube(backs, [r * 0.42 for r in radii], 4, back)
    return pts[-1]


def horn_bow():
    m = Mesh()
    top = _limb(m, 1, 52.0, 11.0, 7.0, 'Keratin', 'Bark')
    bot = _limb(m, -1, 52.0, 11.0, 7.0, 'Keratin', 'Bark')
    # The grip: a riser of wood between the limbs, wound with leather.
    m.tube([(0, 0, -9), (0, 0, 9)], [1.85, 1.85], 8, 'WoodDark')
    m.lathe([(1.95, 0.0), (2.25, 1.2), (2.25, 11.0), (1.95, 12.2)], 8,
            'Leather', origin=(0.0, 0.0, -6.0))
    # The nocks, and the string between them. The string runs on the BELLY
    # side, which is what makes a recurve read as strung rather than as a
    # piece of scrap.
    for end in (top, bot):
        m.blob((end[0], 0.0, end[2]), 1.05, 'Bark', rings=3, segments=6)
    m.tube([(top[0], 0.0, top[2]), (1.5, 0.0, 0.0), (bot[0], 0.0, bot[2])],
           [0.30, 0.34, 0.30], 4, 'Fletch')
    return m, 'horn_bow'


def hollow_bow():
    m = Mesh()
    # A HOLLOW STAVE, and open at both ends. The world says it needs no arrows
    # because it makes its own, so what it has to look like is a thing you
    # could break a splinter off: a tube, thin-walled, with a visible bore.
    #
    # AND BENT, WHICH THE FIRST CUT WAS NOT. Drawn dead straight with a cord
    # close in against it, the sprite came back as a white stick standing among
    # seven bows -- the one silhouette in the pack that did not say what it
    # was. A bow is a bow because it is BENT and because there is daylight
    # between the stave and the string; a cheap one is bent badly and strung
    # slack, which is a different shape from a longbow and still a bow.
    def stave(t):
        """Along the stave, -1 at one tip to +1 at the other."""
        return (-7.0 * (1.0 - t * t), 0.0, 66.0 * t)

    pts = [stave(i / 8.0 * 2.0 - 1.0) for i in range(9)]
    radii = [1.55 + 0.55 * (1.0 - abs(i / 8.0 * 2.0 - 1.0)) for i in range(9)]
    m.tube(pts, radii, 8, 'Bone')
    # The bores. Lathed with `cap=False` and a profile that turns back inside
    # itself, so the end is a HOLE and not a disc: a capped tube is a stick.
    for end in (pts[0], pts[-1]):
        up = 1.0 if end[2] > 0 else -1.0
        m.lathe([(1.60, 0.0), (1.85, up * 1.4), (1.75, up * 2.6),
                 (1.05, up * 2.9), (1.00, -up * 5.0)], 8, 'Bone',
                origin=(end[0], 0.0, end[2]), cap=False)
    # A SPLIT down the belly, bound with cord where it would have run on: a bow
    # that is coming apart and is still cheaper than arrows.
    m.tube([(pts[2][0] + 1.6, 0.0, pts[2][2]),
            (pts[6][0] + 1.6, 0.0, pts[6][2])], [0.28, 0.28], 3, 'BoneDark')
    for i in (1, 4, 7):
        m.lathe([(2.00, 0.0), (2.40, 1.0), (2.00, 2.0)], 8, 'Leather',
                origin=(pts[i][0], 0.0, pts[i][2]))
    # AND THE CORD, well clear of the stave, which is the daylight that makes
    # the shape read at the size a pack slot is.
    m.tube([(pts[0][0], 0.0, pts[0][2]), (1.2, 0.0, 0.0),
            (pts[-1][0], 0.0, pts[-1][2])],
           [0.48, 0.52, 0.48], 4, 'Fletch')
    return m, 'hollow_bow'


# ---------------------------------------------------------------------------
# A BIRD ON THE WING, which no kit here has and which the sky needed.
#
# The bestiary has a raven, and a raven is a PERCHED bird: wings folded, feet
# under it, modelled to stand on something. Seen from this window's camera at
# twenty metres up it is a dark lump. What a bird in the air is, from above, is
# a silhouette -- two long wings and a wedge of tail -- and that is nearly all
# of what has to be right, because at this distance nothing else is legible.
#
# So it is forged rather than borrowed, at the size of a real one: a carrion
# crow is about 47 cm nose to tail and 95 cm across the wings, and the whole
# point of the thing is that it reads as SMALL against a field. The window's
# other flying scale mistake -- the axe the size of a door -- came from not
# measuring, so this one is measured.
#
# FLAT, AND THAT IS NOT LAZINESS. The wings are plates two millimetres thick.
# They are going to be bent by a vertex shader on every frame (see wings.hlsl),
# and a wing with volume bends into a crease; a wing that is a sheet bends the
# way a wing does. It is also the difference between twelve triangles and two
# hundred, and there are two dozen of these in the air at once.
def bird():
    m = Mesh()
    # The body, along +X, nose forward. A lathe rather than a blob so the taper
    # from breast to tail is under control: a bird is not an egg.
    body = [(0.0, -1.0), (2.2, 2.0), (3.1, 7.0), (2.9, 13.0),
            (2.0, 19.0), (1.0, 23.0), (0.0, 25.0)]
    m.lathe(body, segments=8, material='Feather', origin=(-11.0, 0.0, 0.0))
    # AND IT IS LYING DOWN. The lathe revolves about Z and a bird flies along
    # X, so the profile above is built standing and then laid flat here --
    # which is one transform rather than a second lathe that sweeps about X.
    m.v = [(z - 11.0, y, -x) for (x, y, z) in m.v]

    # The head, and a beak that is most of what says which way it is going.
    m.blob((13.5, 0.0, 1.2), 3.4, 'Feather', rings=4, segments=8,
           squash=(1.0, 0.9, 0.85))
    m.lathe([(1.5, 0.0), (0.9, 2.0), (0.0, 4.6)], segments=6,
            material='Keratin', origin=(0.0, 0.0, 0.0))

    # ---- THE WINGS ----
    #
    # Swept back and tapering, which is a crow rather than a gull, and drawn as
    # an outline in (Y, Z) that `plate` extrudes along X -- so the "thickness"
    # is the wing's CHORD and the outline is its plan. Read from the shoulder
    # out: leading edge forward, tip, then the trailing edge back in.
    #
    # The root is at the shoulder and not at the middle, so a shader that bends
    # on |Y| pivots where a shoulder is.
    span = 47.0
    for side in (1.0, -1.0):
        outline = [
            (0.0 * side, 6.5), (14.0 * side, 6.0), (30.0 * side, 4.2),
            (span * side, 1.4), (span * side, -0.6), (32.0 * side, -3.0),
            (16.0 * side, -5.0), (0.0 * side, -6.0),
        ]
        if side < 0:
            outline.reverse()
        # `plate` extrudes along X and wants (y, z); the wing is a plan in
        # (y, x), so the outline's second number is the FORE-AND-AFT position
        # and the extrusion is the thickness. Built the other way about here:
        # the outline is (y, z) with z used as x, and the whole thing is turned
        # after, which keeps `plate`'s own convention untouched.
        first = len(m.v)
        m.plate(outline, 0.4, 'Feather', origin=(0.0, 0.0, 0.0))
        for i in range(first, len(m.v)):
            x, y, z = m.v[i]
            m.v[i] = (z + 1.0, y, x * 0.5 + 1.6)

    # The tail: a flat wedge, which is the other half of the silhouette.
    tail = [(0.0, 0.0), (5.5, -13.0), (0.0, -16.5), (-5.5, -13.0)]
    first = len(m.v)
    m.plate(tail, 0.4, 'Feather', origin=(0.0, 0.0, 0.0))
    for i in range(first, len(m.v)):
        x, y, z = m.v[i]
        m.v[i] = (z - 11.0, y, x * 0.5 + 1.0)
    return m, 'bird'


def web():
    """AN ORB WEB: spokes out of a hub, and a spiral hung between them.

    The world has thirty-three of these around the spiders and NO kit here has
    a web in it. It was drawn as `Rope_1` -- a coil of rope lying in the grass,
    which is why it was reported as invisible -- and then as a flat square,
    which read as a paving slab. Neither is a web, and a web is one of the
    easiest things there is to author: it is a few straight lines and a spiral.

    Built FLAT, in the XY plane, so it lies across a gap the way an orb web
    does. Nothing here is round: a spider lays its spokes at uneven angles and
    the spiral sags between them, and both of those are what stop it reading as
    a dartboard. The sag is the whole trick -- a spiral drawn with a compass is
    a target, and the same spiral pulled in a little between each pair of
    spokes is a thing that was spun.
    """
    m = Mesh()
    SPOKES = 11
    R = 95.0
    THREAD = 0.9

    # The spokes are not evenly spaced and not all the same length. The hub
    # sits off centre, which is also true of the real thing.
    ang = []
    for i in range(SPOKES):
        a = 2.0 * math.pi * i / SPOKES
        a += math.sin(i * 2.7) * 0.11          # uneven, and the same every time
        ang.append(a)
    reach = [R * (0.86 + 0.14 * abs(math.sin(i * 1.9))) for i in range(SPOKES)]
    hub = (4.0, -3.0, 0.0)

    for i, a in enumerate(ang):
        tip = (hub[0] + math.cos(a) * reach[i],
               hub[1] + math.sin(a) * reach[i], 0.0)
        m.tube([hub, tip], THREAD, segments=4, material='Silk')

    # And the spiral, in rings from the hub outward, each leg pulled in toward
    # the hub so the thread hangs between its two spokes instead of bowing out.
    for ring in range(1, 7):
        t = ring / 7.0
        for i in range(SPOKES):
            j = (i + 1) % SPOKES
            a0, a1 = ang[i], ang[j]
            r0, r1 = reach[i] * t, reach[j] * t
            p0 = (hub[0] + math.cos(a0) * r0, hub[1] + math.sin(a0) * r0, 0.0)
            p1 = (hub[0] + math.cos(a1) * r1, hub[1] + math.sin(a1) * r1, 0.0)
            # the sag: halfway along, and a tenth of the way back to the hub
            am = (a0 + a1) * 0.5 if j else (a0 + a1 + 2.0 * math.pi) * 0.5
            rm = (r0 + r1) * 0.5 * 0.90
            mid = (hub[0] + math.cos(am) * rm, hub[1] + math.sin(am) * rm, 0.0)
            m.tube([p0, mid, p1], THREAD * 0.8, segments=4, material='Silk')
    return m, 'web'


PIECES = (web, wolf_mask, hare_mask, hart_mask, raven_mask,
          gold_legs, bone_pile, skull_pile, sheep_skull, horn, siege_engine,
          torc_iron, torc_gold, old_chain, gold_chain, fishing_rod,
          wand, fire_siphon, handgonne,
          crossbow, great_crossbow, star_flail, barb, bone_staff, goo_staff,
          bird,
          king_shroud, javelin, shot, star_grit, horn_bow, hollow_bow)

if __name__ == '__main__':
    for fn in PIECES:
        m, name = fn()
        path = m.write(os.path.join(OUT, name + '.obj'), name)
        # The size is printed because every scale mistake in this project has
        # come from not measuring: the hat brim, the haystack, the purple
        # plots. A forged piece has no excuse -- its size is chosen here.
        xs = [p[0] for p in m.v]; ys = [p[1] for p in m.v]; zs = [p[2] for p in m.v]
        print('%-14s %5d verts %5d faces   %5.1f x %5.1f x %5.1f cm'
              % (name, len(m.v), len(m.faces),
                 max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)))
