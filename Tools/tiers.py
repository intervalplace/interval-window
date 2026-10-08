#!/usr/bin/env python3
"""What grade a thing is, and what colour that grade should read as.

The world has four or five grades of nearly every tool and weapon, and the CC0
kits this project draws them from do not have four or five of every tool: an
iron pickaxe, a steel pickaxe, a quick pickaxe and a great pickaxe are all one
mesh. Rendered honestly they are four identical icons, and a pack in which a
player cannot tell their best axe from their worst has to be read by hovering
over every slot -- which is the thing the sprites were drawn to stop.

So the grade is carried by the COLOUR OF THE METAL, which is how this genre has
always done it and how anybody reading a pack expects to be told. The haft
stays wood and the grip stays leather: those do not change with the grade, and
a bronze-handled steel axe would be a lie about the item.

One table, imported by the renderer (which overrides the mesh's metal slots)
and by the compositor (which handles the meshes that have only one slot).
"""

# THESE ARE LINEAR ALBEDO, AND THEY ARE FURTHER APART THAN THEY LOOK.
#
# The value here is multiplied by the icon light (up to about 1.3) and then
# encoded to sRGB, and sRGB pulls dark values up hard: 0.27 linear arrives on
# screen at about 0.63, which is mid grey. The first set of these was chosen by
# eye as sRGB and every grade came out the same medium silver. They are spaced
# in the space they are actually used in, so that on screen the run reads
# blackened, dull, bright, brilliant.
TIERS = {
    'iron':      (0.235, 0.248, 0.272),   # dull, cold, cheap
    'steel':     (0.430, 0.455, 0.490),   # bright and clean
    'quick':      (0.600, 0.740, 0.960),   # the pale blue of quick-alloy
    'great':     (0.090, 0.096, 0.112),   # blackened: heavy two-handed work
    'gold':      (0.560, 0.360, 0.065),
    'bone':      (0.640, 0.610, 0.500),
    'shell':     (0.520, 0.240, 0.140),
    'sigil':     (0.270, 0.180, 0.520),
    'dragon':    (0.340, 0.060, 0.045),
    'heartwood': (0.320, 0.090, 0.070),
    'ironbark':  (0.120, 0.125, 0.118),
}

# WHICH SLOTS ARE THE METAL. The kits name their material slots, and the names
# are plain: `Steel`, `LightSteel`, `DarkSteel`, `Gold`, `LightGold`, `Iron`,
# `Armor`, `Blade`. Anything whose name contains one of these is the part that
# changes with the grade; `LightWood`, `DarkWood`, `Leather` and `Fletch` are
# not, and are left alone.
METAL = ('steel', 'iron', 'gold', 'silver', 'metal', 'armor', 'armour',
         'blade', 'edge', 'helmet', 'helm', 'shield', 'plate', 'mail')
NOT_METAL = ('wood', 'leather', 'fletch', 'cloth', 'rope', 'bone', 'horn')


def tier_of(name):
    """The grade a name announces, or None for things that have no grade.

    A grade is only ever a PREFIX -- `gold-helm`, `quick-sword`. A bare `sigil`,
    `iron`, `steel` or `heartwood` is a thing in its own right (a token, a bar,
    a timber) and must keep the colour its own material gives it: without the
    hyphen test the sigil came out the purple of sigil-bows and the iron bar
    came out the grey of iron weapons, which is a different item being drawn.
    """
    if '-' not in name:
        return None
    return TIERS.get(name.split('-')[0])


def is_metal(slot):
    low = str(slot).lower()
    if any(w in low for w in NOT_METAL):
        return False
    return any(w in low for w in METAL)
