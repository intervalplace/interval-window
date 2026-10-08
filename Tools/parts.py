import math

# How the level says a well is drawn. Nothing here is a meaning: it is a list
# of shapes at offsets, the same kind of statement as "a wall is a scaled cube".
CUBE='/Engine/BasicShapes/Cube.Cube'; CYL='/Engine/BasicShapes/Cylinder.Cylinder'
CONE='/Engine/BasicShapes/Cone.Cone'; SPH='/Engine/BasicShapes/Sphere.Sphere'

# AND THE AUTHORED ART THAT IS REPLACING THEM. `FORGED` says the same thing
# three hundred lines below, but the tables in this file are built at import
# time starting a few lines from here, so a name they use has to exist by now.
def FORGED_PATH(n): return '/Game/Interval/Forged/%s.%s' % (n, n)

def M(n): return {'refPath': f'/Game/Interval/Materials/{n}.{n}'}

# The props kit, by name. `GEAR` below is the same thing; this exists
# because the stall goods are declared before it.
def GEAR_PATH(n): return '/Game/Interval/Props/%s.%s' % (n, n)
STONE,TIMBER,THATCH,ROCK,CLOTH,CANOPY = (M(x) for x in
    ('MI_PropStone','MI_PropTimber','MI_PropThatch','MI_PropRock','MI_PropCloth','MI_PropCanopy'))

def P(mesh, mat, sx, sy, sz, ox=0.0, oy=0.0, oz=0.0, pitch=0.0, yaw=0.0, roll=0.0, shadow=True):
    return {'mesh': {'refPath': mesh}, 'material': mat,
            'offset': {'x': ox, 'y': oy, 'z': oz},
            'rotation': {'pitch': pitch, 'yaw': yaw, 'roll': roll},
            'scale': {'x': sx, 'y': sy, 'z': sz}, 'bCastShadow': shadow}

def trunk(r, h, mat=TIMBER):
    return [P(CYL, mat, r, r, h / 100.0, oz=h / 2.0)]

PARTS = {
  # A drum of stone with a coping, a pair of posts, the windlass beam across
  # them, a little thatched hood and a bucket on the rope.
  'well': [
    P(CYL, STONE,  1.30, 1.30, 0.16, oz=76),
    P(CUBE, TIMBER, 0.13, 0.13, 2.00, ox=-50, oz=172),
    P(CUBE, TIMBER, 0.13, 0.13, 2.00, ox=50,  oz=172),
    P(CUBE, TIMBER, 1.24, 0.16, 0.16, oz=268),
    P(CYL, TIMBER,  0.20, 0.20, 0.26, oz=268, roll=90),
    P(CUBE, THATCH, 1.30, 1.50, 0.08, ox=-30, oz=300, pitch=32),
    P(CUBE, THATCH, 1.30, 1.50, 0.08, ox=30,  oz=300, pitch=-32),
    P(CYL, TIMBER,  0.34, 0.34, 0.30, oz=190),
  ],
  # Basin, rim, plinth, upper bowl, finial.
  'fountain': [
    P(CYL, STONE, 1.92, 1.92, 0.14, oz=46),
    P(CYL, STONE, 0.54, 0.54, 0.92, oz=90),
    P(CYL, STONE, 0.98, 0.98, 0.16, oz=142),
    P(SPH, STONE, 0.34, 0.34, 0.34, oz=164),
  ],
  # ---- A SIGN IS READ AT EYE HEIGHT ----
  #
  # A PART'S `oz` IS FROM THE PROP'S OWN ORIGIN, AND THE ORIGIN IS NOT THE
  # GROUND. The post is a 2.3 m cylinder dropped at `zOffset` 115, so its
  # middle is 115 cm up and a board written at `oz=204` hangs at 319 above the
  # field: a foot and a half over the head of anybody reading it, on all two
  # hundred and thirteen signposts in the world. Writing the number as though
  # it were a height above the ground is the easy mistake and it is the one
  # that was made.
  #
  # 80 and 50 put the two arms at 195 and 165 above the field, which is a
  # fingerpost: the top arm at the top of a tall man's eyeline, the second
  # below it.
  'signpost': [
    P(CUBE, TIMBER, 0.92, 0.10, 0.20, ox=38, oz=80),
    P(CUBE, TIMBER, 0.74, 0.10, 0.18, oy=-30, oz=50, yaw=90),
  ],
  # A trestle under a cloth awning. SEVEN CUBES ONCE, and because every
  # `stall.<trade>` row inherits this list, those seven were fifty-six of the
  # hundred and twenty-four primitive pieces left in the whole look: the single
  # biggest group, and one mesh fixes all of it. The frame is still square
  # timber, because square timber is what a frame is; what was wrong was the
  # awning, a flat slab 186 x 130 x 6 tilted six degrees, which is a board.
  # See blend/market.py: it sags now, and it has a thickness.
  'stall': [
    P(FORGED_PATH('stall_awning'), None, 1.0, 1.0, 1.0),
  ],
  # THE FIRES ARE BUILT BELOW, out of a ring of stone and round logs -- see
  # `hearthstead`. They were two crossed CUBES standing on a cylinder half a
  # metre tall, which is where "what is that cylinder the flame is burning
  # through" came from: the drum was the hearth.
  'hearth':    None,        # replaced by hearthstead(), below
  'campfire':  None,
  'watchfire': None,
  # A bell needs something to hang from.
  'bellwork': [
    P(CUBE, TIMBER, 0.12, 0.12, 2.20, ox=-42, oz=110),
    P(CUBE, TIMBER, 0.12, 0.12, 2.20, ox=42,  oz=110),
    P(CUBE, TIMBER, 1.10, 0.14, 0.14, oz=218),
    P(CONE, ROCK,   0.60, 0.60, 0.62, oz=176, pitch=180),
  ],
  'tollgate': [
    P(CUBE, TIMBER, 0.18, 0.18, 1.90, ox=-92, oz=95),
    P(CUBE, TIMBER, 0.18, 0.18, 1.90, ox=92,  oz=95),
  ],
  'smokerack': [
    P(CUBE, TIMBER, 1.30, 0.08, 0.08, oz=146),
    P(CUBE, TIMBER, 1.30, 0.08, 0.08, oz=112),
  ],
  # The shoal gibbet: the same beam, over water, with the cage below it.
  'gibbet-shoal': [
    P(CUBE, TIMBER, 0.86, 0.14, 0.14, ox=34, oz=214),
    P(GEAR_PATH('Chain_Coil'), None, 0.5, 0.5, 0.5, ox=62, oz=196),
    P(GEAR_PATH('Cage_Small'), None, 1.0, 1.0, 1.0, ox=62, oz=120),
  ],
  'sawpit': [
    P(CUBE, TIMBER, 0.14, 0.14, 0.80, ox=-62, oz=40),
    P(CUBE, TIMBER, 0.14, 0.14, 0.80, ox=62,  oz=40),
    P(CUBE, TIMBER, 1.50, 0.22, 0.10, oz=84),
  ],
  'ferry':  [P(CUBE, TIMBER, 0.12, 0.12, 1.60, ox=-70, oz=80)],
  'anvil':  [P(CUBE, TIMBER, 0.46, 0.46, 0.44, oz=22)],
  'brewpot':[P(CUBE, STONE, 0.98, 0.98, 0.22, oz=11)],
  'landmark':[P(CYL, STONE, 0.34, 0.34, 1.50, oz=147)],
  'dedication':[P(SPH, STONE, 0.42, 0.42, 0.42, oz=158)],
  # A TREE IS A TREE NOW, not a cone on a stick.
  #
  # These were a cone of canopy standing on a cylinder of trunk, out of the
  # engine's basic shapes, and they read as exactly that: cheap at a hundred
  # metres and cheaper at ten. CC0 art (Quaternius, Stylized Nature MegaKit)
  # brings a real trunk with real bark and a real canopy, so the only pieces
  # left here are the ones the MESH cannot carry -- the gallows' beam.
  'tree':           [],
  'oak-tree':       [],
  'ironbark-tree':  [],
  'heartwood-tree': [],
  'gallows-oak':    [
    P(CUBE, TIMBER, 0.92, 0.14, 0.14, ox=40, oz=248),
    P(CUBE, TIMBER, 0.10, 0.10, 0.56, ox=78, oz=218),
  ],
}

# ---------------------------------------------------------------------------
# WHAT GROWS, AND WHICH TREE IT IS.
#
# The world names fifteen sorts of tree between its gatherable nodes and its
# landmarks, and the kit has five common trees, five pines, five twisted and
# five dead. Nothing here decides what a yew IS: the world said `yew`, and
# this says a window draws that word as a dark dense conifer at seven-eighths
# height. A word with no entry keeps whatever it had.
#
# The twisted trees are RED -- measured, not assumed: their leaf sheet averages
# (64,24,24) against (38,46,19) for the common one. That is the artist's autumn
# species and it is used where a blood-coloured tree reads as character: the
# thorn, the rag-tree, the wind-thorn on the moor.
def WOOD(name):
    return '/Game/Interval/Nature/%s.%s' % (name, name)


# ---------------------------------------------------------------------------
# A HEARTH THAT LOOKS LIKE A HEARTH.
#
# It was a CYLINDER: ninety centimetres across, half a metre tall, with two
# crossed cubes on top of it for logs and the flame standing in the middle. It
# was noticed the moment somebody looked into a room -- "what is that cylinder
# in the corner?" and, of the fire itself, "the cylinder box it is in... the
# flame is burning through it." Both were the same object.
#
# What a hearth actually is, in this world and in the one outside it: a BED OF
# ASH with a RING OF STONE round it to keep the fire in, and WOOD on top. All
# three exist here already -- the Stylized Nature kit is CC0 and its pebbles
# and rocks are the same meshes the scree, shingle and crags are scattered
# from. Nobody had built a fireplace out of them.
#
# The stones are laid by arithmetic rather than by hand so that every hearth in
# the world is the same hearth: a ring is a ring, and a fire in Anchor and a
# fire on the moor should be recognisably the same thing done by the same
# people. They vary in size and sit at varied angles, from the index, so the
# ring is not a clock face -- but it is the SAME variation everywhere, which is
# the rule every other scatter in this window follows.
_HEARTH_STONES = ('Pebble_Round_1', 'Pebble_Round_3', 'Pebble_Square_2',
                  'Pebble_Round_2', 'Pebble_Square_4', 'Pebble_Round_5',
                  'Pebble_Square_1', 'Pebble_Round_4')

def hearthstead(radius, stone, logs, log_len, log_r, log_z, count=8):
    """A ring of stone with wood laid in it. Lengths in centimetres."""
    out = []
    for i in range(count):
        a = 2.0 * math.pi * i / count
        # Two numbers off the index: one shifts the stone round the ring a
        # little, one changes its size. Deterministic, so every window agrees.
        a += ((i * 37 % 13) / 13.0 - 0.5) * 0.28
        s = stone * (0.80 + 0.42 * ((i * 53 % 17) / 17.0))
        out.append(P(WOOD(_HEARTH_STONES[i % len(_HEARTH_STONES)]), None,
                     s, s, s * (0.82 + 0.3 * ((i * 29 % 7) / 7.0)),
                     ox=radius * math.cos(a), oy=radius * math.sin(a),
                     oz=0.0, yaw=(i * 61) % 360, roll=((i * 23 % 9) - 4) * 2.0))
    # AND THE WOOD IS ROUND. A log is a cylinder and was a box, which costs
    # nothing to put right and is most of why the fuel read as joinery.
    for j in range(logs):
        a = 40.0 + j * (150.0 / max(logs, 1))
        out.append(P(CYL, TIMBER, log_r, log_r, log_len / 100.0,
                     oz=log_z, yaw=a, roll=90.0,
                     pitch=((j % 2) * 2 - 1) * 7.0))
    return out


# How big each fire's stead is: the ring's radius, the size of a stone in it,
# how many logs, how long they are, how thick, and how high they lie.
FIRESTEADS = {
    'hearth':    (52.0, 1.15, 3, 66.0, 0.11, 16.0, 8),
    'campfire':  (44.0, 1.00, 3, 56.0, 0.10, 14.0, 7),
    # A watchfire is a bonfire on a platform: no ring of stones, just a great
    # deal of timber, and it is two metres off the ground already.
    'watchfire': (0.0,  0.00, 5, 120.0, 0.18, 232.0, 0),
}

# word -> (mesh, scale). The meshes stand about seven metres and sit on the
# ground already, so a scale of one is an ordinary full-grown tree.
# SCALED AGAINST A PERSON AND A COTTAGE, not against nothing.
#
# The meshes stand about seven metres at a scale of one, which put a common
# tree half again as tall as the houses and made the country look like a
# redwood forest with a village lost in it. A citizen is 1.81 m and a cottage
# is about four; an English oak beside one is five or six metres, not eleven.
#
# ---- AND "ABOUT SEVEN METRES" IS TRUE OF ONLY HALF THE KIT ----
#
# Measured in the running world, from the meshes themselves:
#
#   CommonTree_1..5    7.0 - 9.4 m      the assumption holds
#   Pine_1..5          7.3 - 10.2 m     near enough
#   DeadTree_2..5     11.5 - 16.4 m     half again to twice
#   TwistedTree_1..5  15.7 - 19.0 m     more than twice
#
# So every scale below was chosen against a mesh height that is wrong for the
# twisted and the dead ones, and the error is not small: `willow` came out at
# fourteen metres and `ironbark-tree` at twelve, against the five or six the
# note above asks for. On the horizon they read as columns rather than trees,
# which is how they were noticed -- somebody looking at a screenshot asked what
# the very tall structures in the background were, and guessed standing stones.
#
# THE SCALES BELOW ARE NOW AGAINST THE MEASURED HEIGHT, not against seven. The
# drawn height in metres is in the comment beside each one that was changed, so
# the next person can check the arithmetic without a running editor.
TREES = {
  'tree':            ('CommonTree_1',  0.72),
  'oak-tree':        ('CommonTree_3',  0.86),
  'ironbark-tree':   ('TwistedTree_1', 0.48),   # 8.0 m: the hard tree, grand but not a tower
                                                # was 0.74, which drew it at 12.4
  'heartwood-tree':  ('CommonTree_4',  0.98),
  'gallows-oak':     ('CommonTree_5',  0.82),
  'grove-plot':      ('CommonTree_2',  0.26),
  'pine':            ('Pine_2',        0.80),
  'old-oak':         ('CommonTree_3',  0.92),
  'old-oak-lm':      ('CommonTree_3',  0.84),
  'avenue-oak':      ('CommonTree_5',  0.76),
  'elder-tree':      ('CommonTree_1',  0.40),
  'willow':          ('TwistedTree_2', 0.37),   # 7.0 m; was 0.74, which drew it at 14.0
  'yew':             ('Pine_4',        0.64),
  'apple-tree':      ('CommonTree_2',  0.46),
  'pear-tree':       ('CommonTree_4',  0.46),
  'thorn':           ('TwistedTree_4', 0.30),
  'wind-thorn':      ('TwistedTree_5', 0.38),
  'rag-tree':        ('TwistedTree_3', 0.36),
  'dead-tree':       ('DeadTree_2',    0.57),   # 6.5 m; was 0.70, which drew it at 8.0
  'burnt-tree':      ('DeadTree_4',    0.47),   # 6.0 m; was 0.66, which drew it at 8.4
  'topiary':         ('Bush_Common',   0.80),
  # 2.4 m, to agree with `landmark.reeds` further down, which is the row the
  # generator actually seats and which drew four metres of reed. No founding
  # places a bare `reeds`, so this one has never been seen; it is set to the
  # same height so that the next person to read the two does not have to work
  # out which of them was wrong.
  'reeds':           ('Grass_Wispy_Tall', 0.33),   # 2.4 m; was 0.55
}

# Where a kind has grown a trunk, the canopy has to rise off the ground by the
# height of it, or the tree is a cone with a stick inside.
LIFT = {'tree': (3.00, 4.00, 300), 'oak-tree': (3.40, 4.40, 330),
        'ironbark-tree': (2.80, 4.90, 365), 'heartwood-tree': (3.60, 5.20, 390),
        'gallows-oak': (3.20, 4.10, 315)}

# ---- AND A THING WHOSE PIVOT IS NOT AT ITS FOOT ----
#
# A prop is dropped with its ORIGIN on the ground, which is right for a mesh
# modelled standing on zero and wrong for one modelled about its middle or
# hung from its top. `Banner_1` runs from -155 to +84 about its own origin, so
# dropped at zOffset 0 it put FIVE FEET of itself under the field and showed
# the top eighty centimetres: reported from the window as banners that are
# almost underground, on all forty of them.
#
# This is a short list on purpose. `audit_size.py` measures every prop's mesh
# against its offset and the only other things standing below their own base
# are BOULDERS, between twenty-six and thirty-eight centimetres each, and a
# rock bedded into the ground is what a rock does. The number here is the
# mesh's own `min.z`, read out of the editor rather than guessed.
SUNK = {'banner': 155.0}


# ---------------------------------------------------------------------------
# THE LANDMARKS.
#
# `landmark` is the second most numerous word the world uses -- two and a half
# thousand of them in one neighbourhood -- and it carries EIGHTY-NINE different
# sub-kinds: pine, willow, standing-stone, barrel, bed, grave, skep, spoil-heap.
# Keyed only as `landmark`, every one of them was the same stone drum, which is
# most of why the country read as repeated. The lookup already prefers
# `type.kind` over `type`, so all of this is a table, and a sub-kind with no
# entry falls back to the plain one and is still drawn.
#
# Nothing here decides what a pine IS. The world said `pine`; this says a
# window draws that word as a narrow dark cone on a thin trunk.
def K(mesh, mat, sx, sy, sz, z, yaw=0.0, jit=0.0, parts=None, shadow=True):
    return {'mesh': {'refPath': mesh}, 'material': mat,
            'scale': {'x': sx, 'y': sy, 'z': sz}, 'zOffset': z,
            'yawJitter': yaw, 'scaleJitter': jit, 'heightJitter': 0.0,
            'bHideWhenDepleted': False, 'bCastShadow': shadow,
            'parts': parts or []}

def T(cw, ch, cz, tr, th, canopy=CONE, mat=CANOPY, jit=0.16):
    """A tree: a canopy standing off the ground on a trunk."""
    return K(canopy, mat, cw, cw, ch, cz, 360, jit,
             [P(CYL, TIMBER, tr, tr, th / 100.0, oz=th / 2.0)])

def legs(w, d, h, r=0.09):
    return [P(CUBE, TIMBER, r, r, h / 100.0, ox=x, oy=y, oz=h / 2.0)
            for x in (-w, w) for y in (-d, d)]

LANDMARKS = {
  # --- what grows ---
  'pine':        T(2.10, 4.20, 300, 0.32, 140),
  'old-oak-lm':  T(3.40, 3.40, 290, 0.62, 150),
  'old-oak':     T(3.50, 3.50, 300, 0.66, 155),
  'avenue-oak':  T(2.90, 3.30, 285, 0.54, 145),
  'elder-tree':  T(1.80, 1.50, 165, 0.34, 100, SPH),
  'willow':      T(3.00, 2.30, 260, 0.44, 130, SPH),
  'yew':         T(2.20, 2.10, 200, 0.46, 110, SPH),
  'apple-tree':  T(2.00, 1.70, 190, 0.34, 115, SPH),
  'pear-tree':   T(1.90, 1.90, 200, 0.32, 120, SPH),
  'topiary':     K(SPH, M('MI_PropHedge'), 1.20, 1.20, 1.40, 95, 360, 0.12),
  'thorn':       T(1.30, 0.95, 100, 0.22, 60, SPH, jit=0.22),
  'wind-thorn':  K(SPH, CANOPY, 1.40, 1.10, 0.90, 105, 360, 0.20,
                   [P(CYL, TIMBER, 0.22, 0.22, 0.70, oz=35, pitch=16)]),
  'rag-tree':    T(1.40, 1.10, 110, 0.24, 65, SPH, jit=0.18),
  'reeds':       K(CONE, M('MI_ScatterReed'), 1.40, 1.30, 1.30, 65, 360, 0.24),
  # --- what stands up on its own ---
  'standing-stone': K(CUBE, ROCK, 0.55, 0.38, 2.20, 108, 360, 0.20),
  # A MARKER, NOT A MONUMENT. Four of these stand at the corners of every
  # bridge so a crossing can be seen from across a field, and until now they
  # wore the standing stone's word and the standing stone's art: four
  # two-metre megaliths ringing a little bridge in ploughed country, which is
  # a great deal of ceremony for a place to put your feet.
  #
  # Waist high, squat and squared, and barely turned: a stone somebody cut and
  # set, where the Brandline's stones are stones somebody RAISED. The
  # difference should be visible at a glance, because the Brandline means
  # something and a bridge means "bridge".
  'bridge-stone':   K(CUBE, STONE, 0.42, 0.36, 0.95, 46, 22, 0.10),
  'sentinel':       K(CUBE, ROCK, 0.72, 0.50, 3.10, 152, 360, 0.14),
  'fallen-stone':   K(CUBE, ROCK, 2.00, 0.70, 0.42, 20, 360, 0.18),
  'glass-stone':    K(SPH, ROCK, 0.80, 0.80, 1.10, 54, 360, 0.16),
  'milestone':      K(CUBE, STONE, 0.34, 0.24, 0.92, 46, 360, 0.10),
  'way-post':       K(CYL, TIMBER, 0.16, 0.16, 2.10, 105, 360, 0.08,
                      [P(CUBE, TIMBER, 0.70, 0.09, 0.16, ox=30, oz=186)]),
  'tally-post':     K(CYL, TIMBER, 0.18, 0.18, 1.70, 85, 360, 0.08),
  'cairn':          K(SPH, ROCK, 1.30, 1.30, 0.50, 18, 360, 0.16,
                      [P(SPH, ROCK, 0.90, 0.90, 0.42, oz=48),
                       P(SPH, ROCK, 0.50, 0.50, 0.30, oz=78)]),
  'stone-heap':     K(SPH, ROCK, 1.25, 1.25, 0.50, 16, 360, 0.22),
  'rubble-heap':    K(SPH, ROCK, 1.35, 1.35, 0.45, 14, 360, 0.24),
  'spoil-heap':     K(CONE, ROCK, 1.70, 1.70, 0.85, 42, 360, 0.20),
  'ore-heap':       K(CONE, ROCK, 1.30, 1.30, 0.70, 35, 360, 0.20),
  'ash-heap':       K(CONE, ROCK, 1.30, 1.30, 0.50, 25, 360, 0.20),
  'cut-face':       K(CUBE, ROCK, 1.90, 0.90, 1.60, 80, 0, 0.10),
  # --- what somebody left there ---
  'barrel':   K(CYL, TIMBER, 0.62, 0.62, 0.86, 43, 360, 0.10),
  'skep':     K(SPH, THATCH, 0.62, 0.62, 0.56, 22, 360, 0.10),
  'haystack': K(CONE, THATCH, 1.80, 1.80, 1.90, 95, 360, 0.16),
  'peat-stack': K(CUBE, ROCK, 1.30, 0.90, 0.80, 40, 360, 0.12),
  'turf-stack': K(CUBE, CANOPY, 1.30, 0.90, 0.70, 35, 360, 0.12),
  'withy-stack': K(CONE, TIMBER, 1.10, 1.10, 1.20, 60, 360, 0.16),
  # ---- THREE LOGS, LYING DOWN ----
  #
  # A cylinder's axis is Z, so a log lying on the ground is a cylinder ROLLED
  # a quarter turn, and its length is its Z scale. This was authored as
  # (1.60, 0.52, 0.52) with no roll on the base, which is not a log: it is a
  # drum a metre and a half across and half a metre tall, and against the
  # ground it read as a loaf half buried in the grass. Only the two parts were
  # rolled, and they kept the same wrong scale, so they were elliptical.
  #
  # `Lean` is how a base mesh turns -- the parts have had `roll` all along and
  # the base simply had nothing passed to it. Lengths along Z now, diameter on
  # X and Y, and each log lifted by its own radius so it RESTS on the ground
  # rather than sinking to its waist in it.
  # THE PARTS ARE NOT IN THE BASE'S FRAME, which is worth saying because the
  # obvious guess is that they are. A part carries its own rotation in world
  # terms and the base's `Lean` does not reach it, so each log needs its own
  # quarter turn and its own world offsets: one beside on X, one over the join
  # and up on Z. Two down and one across them: a stack, not a heap.
  #
  # AND A PART IS MEASURED FROM THE GROUND, not from the base it sits beside.
  # The base gets its radius from `zOffset`; a part gets nothing, so the two
  # that were written at nought and forty-eight lay buried to their middles
  # while the base rested properly on the turf. Each carries its own lift now:
  # a radius for the one on the ground, a radius and a diameter for the one on
  # top of the pair.
  'log-pile': K(CYL, TIMBER, 0.52, 0.52, 1.60, 26, 360, 0.12,
                [P(CYL, TIMBER, 0.52, 0.52, 1.60, ox=56, oz=26, roll=90),
                 P(CYL, TIMBER, 0.52, 0.52, 1.60, ox=28, oz=71, roll=90)],
                ) | {'lean': {'pitch': 0.0, 'yaw': 0.0, 'roll': 90.0}},
  'stump':    K(CYL, TIMBER, 0.64, 0.64, 0.44, 22, 360, 0.18),
  'windfall': K(SPH, CANOPY, 1.20, 1.10, 0.40, 14, 360, 0.20),
  'table':    K(CUBE, TIMBER, 1.30, 0.80, 0.10, 76, 0, 0.06, legs(55, 30, 72)),
  'bench':    K(CUBE, TIMBER, 1.20, 0.38, 0.09, 44, 0, 0.06, legs(48, 12, 40)),
  'bed':      K(CUBE, TIMBER, 1.50, 0.90, 0.34, 17, 0, 0.05,
                [P(CUBE, CLOTH, 1.44, 0.84, 0.16, oz=42)]),
  'shelf':    K(CUBE, TIMBER, 1.10, 0.32, 0.08, 112, 0, 0.05,
                [P(CUBE, TIMBER, 1.10, 0.32, 0.08, oz=-40),
                 P(CUBE, TIMBER, 0.08, 0.30, 1.20, ox=-50, oz=-52),
                 P(CUBE, TIMBER, 0.08, 0.30, 1.20, ox=50, oz=-52)]),
  'hurdle':       K(CUBE, TIMBER, 1.80, 0.10, 0.86, 43, 0, 0.06),
  'sheep-hurdle': K(CUBE, TIMBER, 1.70, 0.10, 0.74, 37, 0, 0.06),
  'barricade':    K(CUBE, TIMBER, 1.80, 0.40, 1.00, 50, 0, 0.08,
                    [P(CUBE, TIMBER, 1.90, 0.12, 0.14, oz=64, pitch=24)]),
  'scarecrow': K(CYL, TIMBER, 0.14, 0.14, 1.80, 90, 360, 0.06,
                 [P(CUBE, TIMBER, 1.10, 0.10, 0.10, oz=130),
                  P(SPH, CLOTH, 0.34, 0.34, 0.34, oz=176)]),
  'wheel-rut': K(CUBE, ROCK, 1.80, 1.10, 0.04, 2, 0, 0.0, None, False),
  # --- what is left of somebody ---
  'grave':      K(CUBE, CANOPY, 1.50, 0.70, 0.18, 9, 0, 0.08,
                  [P(CUBE, STONE, 0.42, 0.14, 0.52, ox=-62, oz=26)]),
  'bone-pile':  K(SPH, STONE, 0.95, 0.95, 0.34, 11, 360, 0.20),
  'skull-pile': K(SPH, STONE, 0.80, 0.80, 0.40, 14, 360, 0.18),
  'sheep-skull': K(SPH, STONE, 0.32, 0.32, 0.26, 10, 360, 0.16),
  # ---- AND THE WEB IS A WEB NOW ----
  #
  # It went through three wrong answers before anybody authored one: a coil of
  # rope out of the props kit (invisible in grass, which is how it was
  # reported), a flat terracotta slab hanging at seventy centimetres, and a
  # pale slab lying on the ground that read as paving. No CC0 kit this project
  # uses has a web in it.
  #
  # So it is forged, like the bone piles and the chains: eleven spokes out of
  # an off-centre hub and a spiral sagging between them, 1.75 metres across and
  # under two centimetres thick. See `web()` in make_art.py. It carries its own
  # silk material, so nothing is named here.
  'web':        K(FORGED_PATH('web'), None, 1.0, 1.0, 1.0, 9, 360, 0.14, None, False),
  'dead-tree':  K(CYL, TIMBER, 0.40, 0.40, 2.60, 130, 360, 0.20,
                  [P(CUBE, TIMBER, 0.90, 0.12, 0.12, ox=30, oz=210, pitch=-28),
                   P(CUBE, TIMBER, 0.70, 0.12, 0.12, ox=-24, oz=170, pitch=26)]),
  'burnt-tree': K(CYL, ROCK, 0.36, 0.36, 2.20, 110, 360, 0.20,
                  [P(CUBE, ROCK, 0.70, 0.11, 0.11, ox=24, oz=180, pitch=-32)]),
  # A GALLOWS IS SQUARED TIMBER and a post and a beam are honestly cuboids --
  # what makes it a GIBBET rather than a frame is the cage on the end of the
  # chain, and the props kit has both. Hung off the beam at its far end, which
  # is where a body was left to be seen from the road.
  'gibbet':     K(CUBE, TIMBER, 0.20, 0.20, 2.60, 130, 360, 0.06,
                  [P(CUBE, TIMBER, 0.90, 0.14, 0.14, ox=36, oz=246),
                   P(GEAR_PATH('Chain_Coil'), None, 0.5, 0.5, 0.5, ox=66, oz=228),
                   P(GEAR_PATH('Cage_Small'), None, 1.0, 1.0, 1.0, ox=66, oz=150)]),
}


# The remaining forty. Nothing rare enough to skip: a cave mouth drawn as the
# same drum as a beehive is exactly the flatness this table exists to undo.
def wheels(r, y, z, mat=TIMBER):
    return [P(CYL, mat, r, r, 0.14, oy=-y, oz=z, roll=90),
            P(CYL, mat, r, r, 0.14, oy=y, oz=z, roll=90)]

LANDMARKS.update({
  'cart':         K(CUBE, TIMBER, 1.60, 0.90, 0.42, 62, 360, 0.08,
                    wheels(0.60, 50, 32) + [P(CUBE, TIMBER, 1.10, 0.10, 0.10, ox=104, oz=48)]),
  'broken-cart':  K(CUBE, TIMBER, 1.50, 0.85, 0.38, 34, 360, 0.10,
                    [P(CYL, TIMBER, 0.58, 0.58, 0.14, oy=-48, oz=20, roll=90),
                     P(CYL, TIMBER, 0.58, 0.58, 0.14, oy=60, oz=6, roll=64)]),
  'hay-wain':     K(CUBE, THATCH, 1.80, 1.00, 0.90, 86, 360, 0.08, wheels(0.64, 54, 34)),
  'trestle':      K(CUBE, TIMBER, 1.40, 0.36, 0.09, 82, 360, 0.08,
                    [P(CUBE, TIMBER, 0.09, 0.62, 0.78, ox=-56, oz=39),
                     P(CUBE, TIMBER, 0.09, 0.62, 0.78, ox=56, oz=39)]),
  'sawhorse':     K(CUBE, TIMBER, 1.00, 0.12, 0.12, 62, 360, 0.08,
                    [P(CUBE, TIMBER, 0.08, 0.50, 0.62, ox=-34, oz=31),
                     P(CUBE, TIMBER, 0.08, 0.50, 0.62, ox=34, oz=31)]),
  'chopping-block': K(CYL, TIMBER, 0.62, 0.62, 0.56, 28, 360, 0.12,
                      [P(CUBE, ROCK, 0.08, 0.30, 0.34, oz=70, pitch=22)]),
  'wood-chips':   K(CYL, TIMBER, 1.10, 1.10, 0.08, 4, 360, 0.20, None, False),
  'ladder':       K(CUBE, TIMBER, 0.09, 0.09, 2.40, 118, 360, 0.08,
                    [P(CUBE, TIMBER, 0.09, 0.09, 2.40, oy=44, oz=0)] +
                    [P(CUBE, TIMBER, 0.06, 0.46, 0.06, oy=22, oz=z) for z in (-80, -30, 20, 70)]),
  'scaffold':     K(CUBE, TIMBER, 0.12, 0.12, 2.80, 140, 360, 0.08,
                    [P(CUBE, TIMBER, 0.12, 0.12, 2.80, ox=90, oz=0),
                     P(CUBE, TIMBER, 1.10, 0.10, 0.10, ox=45, oz=120),
                     P(CUBE, TIMBER, 1.10, 0.44, 0.07, ox=45, oz=126)]),
  'gazebo-post':  K(CYL, TIMBER, 0.20, 0.20, 2.40, 120, 360, 0.08,
                    [P(CONE, THATCH, 1.00, 1.00, 0.44, oz=142)]),
  # --- somebody's work, left standing ---
  'charcoal-ring':  K(CYL, ROCK, 1.50, 1.50, 0.14, 7, 360, 0.14, None, False),
  'charcoal-clamp': K(CONE, ROCK, 1.70, 1.70, 1.10, 55, 360, 0.16,
                      [P(CYL, ROCK, 0.24, 0.24, 0.30, oz=118)]),
  'crude-hearth':   K(CYL, ROCK, 0.90, 0.90, 0.22, 11, 360, 0.16,
                      [P(CUBE, TIMBER, 0.50, 0.11, 0.11, oz=26, yaw=28),
                       P(CUBE, TIMBER, 0.50, 0.11, 0.11, oz=26, yaw=-54)]),
  'scorched-ring':  K(CYL, ROCK, 1.40, 1.40, 0.05, 3, 360, 0.16, None, False),
  'daub-mark':      K(CUBE, STONE, 0.60, 0.06, 0.80, 96, 360, 0.10),
  'peat-cut':       K(CUBE, ROCK, 1.80, 1.20, 0.30, -6, 0, 0.10),
  'slag-lump':      K(SPH, ROCK, 0.70, 0.70, 0.42, 14, 360, 0.24),
  'shot-hole':      K(CYL, ROCK, 0.80, 0.80, 0.24, -6, 360, 0.18),
  'cave-mouth':     K(SPH, ROCK, 2.40, 1.60, 1.90, 10, 360, 0.14,
                      [P(SPH, ROCK, 1.30, 0.90, 1.20, oy=-40, oz=0)]),
  'wellspring':     K(CYL, ROCK, 1.30, 1.30, 0.30, 12, 360, 0.10,
                      [P(CYL, STONE, 1.00, 1.00, 0.06, oz=30)]),
  # --- water and the edge of it ---
  'dew-pond':      K(CYL, ROCK, 1.70, 1.70, 0.16, 4, 360, 0.12, None, False),
  'bog-pool':      K(CYL, ROCK, 1.60, 1.40, 0.12, 3, 360, 0.16, None, False),
  'fish-trap':     K(CONE, TIMBER, 0.70, 0.70, 1.10, 40, 360, 0.14, None, False),
  'eel-rack':      K(CUBE, TIMBER, 1.60, 0.10, 0.10, 128, 360, 0.08,
                    [P(CUBE, TIMBER, 0.10, 0.10, 1.30, ox=-72, oz=-63),
                     P(CUBE, TIMBER, 0.10, 0.10, 1.30, ox=72, oz=-63)] +
                    [P(CUBE, CLOTH, 0.05, 0.05, 0.50, ox=x, oz=-26) for x in (-40, 0, 40)]),
  'upturned-boat': K(SPH, TIMBER, 2.20, 0.90, 0.60, 26, 360, 0.10),
  'shipwreck':     K(SPH, TIMBER, 3.20, 1.30, 0.80, 22, 360, 0.10,
                    [P(CUBE, TIMBER, 0.14, 0.14, 2.60, ox=40, oz=100, pitch=24)]),
  'staithe':       K(CUBE, TIMBER, 2.00, 1.20, 0.14, 44, 0, 0.08,
                    [P(CUBE, TIMBER, 0.14, 0.14, 0.90, ox=x, oy=y, oz=-8)
                     for x in (-80, 80) for y in (-46, 46)]),
  'drowned-bell':  K(CONE, ROCK, 0.90, 0.90, 0.90, 46, 360, 0.10, None),
  # --- what the land was before ---
  'sunken-wall':   K(CUBE, ROCK, 1.90, 0.60, 0.34, 10, 0, 0.12),
  'half-wall':     K(CUBE, STONE, 1.80, 0.56, 1.00, 48, 0, 0.12),
  'window-arch':   K(CUBE, STONE, 0.28, 0.60, 2.10, 104, 360, 0.08,
                    [P(CUBE, STONE, 0.28, 0.60, 2.10, oy=120),
                     P(CUBE, STONE, 0.28, 1.70, 0.30, oy=60, oz=90)]),
  'broken-tower':  K(CYL, STONE, 2.40, 2.40, 3.40, 170, 360, 0.14,
                    [P(CYL, STONE, 2.30, 2.30, 0.50, oz=210, pitch=5)]),
  'mill':          K(CYL, STONE, 2.20, 2.20, 3.20, 160, 360, 0.08,
                    [P(CONE, THATCH, 2.60, 2.60, 1.20, oz=380),
                     P(CUBE, TIMBER, 0.14, 3.40, 0.28, ox=120, oz=300, roll=30),
                     P(CUBE, TIMBER, 0.14, 3.40, 0.28, ox=120, oz=300, roll=120)]),
  'siege-engine':  K(CUBE, TIMBER, 2.00, 1.20, 0.40, 40, 360, 0.08,
                    wheels(0.70, 68, 36) +
                    [P(CUBE, TIMBER, 0.16, 0.16, 2.40, oz=180, pitch=-38),
                     P(CUBE, TIMBER, 0.60, 0.60, 0.20, ox=-70, oz=268)]),
  'tally-half':    K(CUBE, TIMBER, 0.18, 0.10, 1.20, 60, 360, 0.10),
  # --- the small marks people leave ---
  'flowerbed':  K(CUBE, M('MI_PropHedge'), 1.60, 1.00, 0.16, 8, 360, 0.10, None, False),
  'birdbath':   K(CYL, STONE, 0.30, 0.30, 0.80, 40, 360, 0.08,
                 [P(CYL, STONE, 0.78, 0.78, 0.14, oz=46)]),
  'salt-lick':  K(CUBE, STONE, 0.44, 0.44, 0.30, 15, 360, 0.16),
  'dew-mark':   K(CUBE, ROCK, 0.30, 0.30, 0.42, 21, 360, 0.14),
  'wool-snag':  K(CUBE, CLOTH, 0.26, 0.26, 0.20, 34, 360, 0.20,
                 [P(CUBE, TIMBER, 0.07, 0.07, 0.50, oz=-10)]),
})


# ---------------------------------------------------------------------------
# THE KEEPERS AND THE STALLS.
#
# `keeper` carries twenty-two sub-kinds and `stall` seven, and both were one
# mesh. At this distance a robe colour says almost nothing and a SILHOUETTE
# says everything, so each keeper gets a hat and the thing they are holding,
# and each stall gets its goods on the trestle.
def KEEP(mat, h, parts):
    return K(CYL, mat, 0.52, 0.52, h / 100.0, h / 2.0, 360, 0.05, parts)

# ---- A HAT IS HEAD-SIZED ----
#
# Every brim in here was set by eye against the CYLINDER a keeper used to be,
# and a cylinder is 52cm across. They were never re-measured when keepers
# became people, so a beekeeper's brim was NINETY CENTIMETRES on a person
# fifty centimetres wide. Photographed from the watch camera, which looks
# almost straight down, that is not a hat -- it is a disc with boots under it,
# and it is exactly what was reported: "wtf is this?"
#
# `w` is still written the way it always was. HEAD divides it down to something
# a person could wear, so every entry below stays readable as the proportion it
# was meant to be and none of them had to be re-typed.
#
#   a broad straw brim   ~48cm      a cap or a coif   ~30cm
#   a helmet             ~26cm      shoulders, for scale, ~45cm
HEAD = 0.60

def hat(mesh, mat, w, t, z):
    return P(mesh, mat, w * HEAD, w * HEAD, t, oz=z)

# ---- AND THE HATS ARE REAL NOW ----
#
# Every `hat()` above was a CONE, a CYLINDER or a SPHERE out of
# /Engine/BasicShapes, scaled and parked at head height. The bodies were right
# all along -- a skeletal mesh in peasant clothing -- so what a person saw was
# somebody standing in a market square with a traffic cone on their head. It
# was reported exactly that way: "one was wearing a triangle shape and one was
# wearing a cylinder. On their heads."
#
# `Tools/blend/hats.py` authors six: a straw hat, a flat cap, a tall pointed
# hat, a beekeeper's hat, the veil that hangs off it, and a plain metal
# skullcap. They are modelled in centimetres at the size a head actually is,
# so unlike `hat()` they are NOT scaled by anything here: scale 1, and the only
# number is where the brim sits.
#
# THAT NUMBER IS THE KEEPER'S OWN HEIGHT LESS EIGHT. `KEEP` is given the height
# of the person, which is the top of their head; a hat's band sits just below
# that and its crown goes above. One rule for all of them rather than fifteen
# hand-set offsets that drift the first time a body changes.
#
# The path is spelled out rather than calling `FORGED`, which is defined three
# hundred lines below this: `KEEPERS` is built at import time, right here, so a
# helper it uses cannot depend on a name the module has not reached yet.
def fhat(name, h):
    """A hat, ON THE HEAD BONE.

    `h` was the height above the TILE to drop the hat at, which is how a hat
    comes to float: it was never attached to anybody. The figure's own head is
    wherever their animation and their height put it, and no number measured
    against the ground can follow that.

    The argument is kept because every caller passes a plausible crown height
    and throwing them all away would lose the one thing they do record -- which
    trades wear their hat high and which wear it low. It is read as a nudge
    about the mean now rather than as a height: a hat written for 182 sits a
    little prouder than one written for 170, by the difference between them.

    THE NOTE THIS PARAGRAPH USED TO CARRY WAS WRONG, and it is worth leaving
    the correction here because it cost more than this file. It said a bone's X
    runs ALONG the bone and that a piece needs a quarter turn to stand up. It
    does not: on this rig up is +Z with no pitch at all, which is what the code
    below has always done and what the paragraph never caught up with. The same
    sentence was copied over the hand, where it produced a grip measured on a
    staff long enough to hide the error -- see GRIP.
    """
    # AND A HELM IS NOT A CAP. Every hat came through here with no material and
    # kept whatever the forged mesh carried, which is bare white -- so a
    # watchman's helm, a collier's helm, a beekeeper's veil and a banker's cap
    # were the same pale shape. The piece cannot ask the keeper what they are
    # made of (the kind's own material is cleared when a keeper becomes a
    # person), so it is decided by what the hat IS, which is in its name.
    worn = P('/Game/Interval/Forged/%s.%s' % (name, name), HAT_STUFF(name),
             1.0, 1.0, 1.0,
             oz=HAT_CROWN + HAT_LIFT.get(name, 0.0) + (h - 176.0) * 0.25,
             pitch=0.0)
    # `WEAR` does exactly this and is defined further down the file than the
    # keeper table that calls us, so the bone is set by hand rather than by
    # moving a definition a thousand lines.
    worn['bone'] = 'head'
    return worn

def HAT_STUFF(name):
    """What a hat is made of, from its own word."""
    if 'helm' in name:
        return STONE          # steel, like the rest of the armour
    if 'straw' in name or 'net' in name:
        return THATCH         # a straw hat is straw, and so is a bee veil's net
    return CLOTH

# How far along the head bone a hat's own origin sits, in centimetres. One
# number, measured by looking: see `fhat`. The hats are modelled with their
# pivot at the brim, so this is roughly the distance from the head bone to the
# top of the skull on this rig.
HAT_CROWN = 12.0

# AND A BRIM HANGS BELOW THE BAND. The five hats here are modelled with z=0 at
# the band, so one HAT_CROWN serves them all -- except that a kettle hat's brim
# starts two and a half centimetres BELOW it, and a keeper stands with their
# head tilted down, which tips the front of a brim forward over the eyes. Three
# centimetres puts the face back under it instead of behind it.
HAT_LIFT = {'hat_helm': 3.0}

# ---- THE KIT'S OWN HELMS WERE TRIED HERE AND DO NOT WORK ----
#
# `Bucket_Helmet2` is CC0 (Art/Armour/README.md), modelled at life size and
# already in place -- 20 x 25 x 24 cm, standing between 155 and 179 cm, which
# is chin to crown on a 180cm figure. The note on blend/hats.py said the kit's
# helms were passed over only because a keeper's hat used to be a static part
# at a height above the tile rather than a thing on the head bone, and that
# stopped being true. So it was hung on the bone and photographed.
#
# It does not work, and the reason is not an offset. A great helm has a FACE.
# Its opening has to line up with one, and a keeper's head bone tilts down
# while they stand still, so the helm arrives pushed onto the chin. Half the
# citizens in this world wear hoods, and a bucket helm does not go over a hood.
#
# `hat_helm` is a KETTLE HAT instead -- a brim and a dome, symmetric, so it
# does not care which way a head is turned, and worn over a hood the way the
# real one was worn over a coif. See `helm()` in blend/hats.py.

# ---- AND A STAFF IS A STAFF ----
#
# It was an eight-centimetre cylinder: a broom handle with no head, no taper
# and no grain, standing beside the keeper. This project already owns a real
# one -- Quaternius' RPG Characters pack is CC0, it is already in `Art/`, and
# `import_wizard.py` already brings its staff in as `Wizard_Staff1`. Nobody had
# connected the two.
#
# The mesh is 2.6 metres tall with its pivot on the floor, so `h` here is read
# as the height in metres the staff should actually stand and turned into a
# scale. Nothing is centred and nothing is offset upward, which is the one
# thing the cylinder version got wrong and never showed, because a featureless
# pole looks the same either way up.
# ---- AND THE REST OF THE KIT IS REAL TOO ----
#
# A keeper's trade is told by what they have BESIDE them, and every one of
# those was a scaled primitive: the brewer's barrel was a cylinder, the
# miller's sack a cube, the armourer's anvil a squat cylinder, the toll's
# strongbox a smaller cube. Standing next to a person with a face, they read
# as exactly what they were.
#
# Quaternius' Fantasy Props MegaKit is CC0 and this project imported it some
# sessions ago -- Barrel, Bag, Crate, Anvil, Cauldron, WeaponStand, Mug and
# eighty more are already sitting in /Game/Interval/Props and are already used
# by FURNITURE below at scale 1.00, which is to say they come in at real size.
# Nobody had pointed the keepers at them.
#
# Pivots are on the floor, so `oz` is 0 unless the thing is meant to be held up.
def kit_prop(name, ox=40.0, oy=0.0, oz=0.0, s=1.0, yaw=0.0, pitch=0.0, roll=0.0):
    return P(GEAR_PATH(name), None, s, s, s,
             ox=ox, oy=oy, oz=oz, yaw=yaw, pitch=pitch, roll=roll)

# ======================= WHERE A HAND HOLDS A THING =======================
#
# A thing in a hand is a mesh hung on the `hand_r` bone with a relative
# transform, and a relative transform turns a mesh about the MESH'S OWN PIVOT.
# That one fact is what every number in this section used to get wrong.
#
# WHAT WAS HERE BEFORE, AND WHY IT LOOKED RIGHT. `GRIP` was (8, 30, 0), and the
# note over it said those numbers put a thing in the palm instead of the wrist.
# They did not. They were arrived at by looking at a watchman's STAFF, and a
# staff is 2.4 metres long: wherever you put its pivot, the shaft still runs
# through the fist, so it reads as held. Photographed properly, that staff's
# heel stands on the GROUND -- which puts its pivot about 95cm ABOVE the hand.
# The offset was never the hand. It was the number that happened to plant a
# long shaft in the mud, and it was then handed to every weapon in the kit. A
# 53cm hatchet given it floats in the air beside the shoulder, which is exactly
# what was reported and exactly what the photographs show.
#
# WHAT IS HERE NOW, measured the same way but on something SHORT, where the
# pivot has nowhere to hide: `Axe_Small` hung at offset (0, 0, 0) and turn
# (0, 0, 145) sits in the fist, haft through the hand, head up, a stub of haft
# below. So the bone's own origin IS the grip, and the hand needs no offset.
#
# THE TURN IS UNCHANGED and is the one number in here anybody ever looked at.
# Nought leaves a shaft up and to the left at about forty degrees; -35 stands
# it up and stands it UPSIDE DOWN, crown at the ground; the quarter turn has to
# go the other way round the circle. 145. Every mesh in this kit runs along its
# own +Z -- see kit_bounds.json, which was read out of the editor rather than
# remembered -- so this one turn stands all of them up.
GRIP = (0.0, 0.0, 0.0)
GRIP_TURN = (0.0, 0.0, 145.0)


import json as _json, os as _os
try:
    KIT_BOUNDS = _json.load(open(_os.path.join(
        _os.path.dirname(_os.path.abspath(__file__)), 'kit_bounds.json')))
except (IOError, ValueError):
    KIT_BOUNDS = {}   # re-run kit_bounds.py against a live editor

# HOW FAR UP ITSELF A THING IS HELD, from its butt, as a fraction of its length.
GRIP_ALONG = {
    # Hafted: the hand goes near the end, and the weight is out at the head.
    'Axe': 0.09, 'Axe_Double': 0.09, 'Axe_Small': 0.10, 'Axe_Bronze': 0.12,
    'Hammer_Double': 0.10, 'Hammer_Small': 0.11, 'Pickaxe_Bronze': 0.12,
    # Bladed: just above the pommel.
    'Sword': 0.07, 'Sword_2': 0.07, 'Sword_Big': 0.06, 'Sword_Golden': 0.07,
    'Sword_Bronze': 0.09, 'Claymore': 0.06, 'Dagger': 0.09, 'Dagger_2': 0.09,
    # Long hafts are gripped well up, or they drag.
    'Spear': 0.30, 'Scythe': 0.14,
    # A bow is held at the riser, which is its middle.
    'Bow_Evil': 0.50, 'Bow_Golden': 0.50,
    'Bow_Wooden': 0.50, 'Bow_Wooden2': 0.50,
    # A staff has no entry: `staff()` works its fraction out from the keeper's
    # hand height, so the heel reaches the ground whatever length it is.
    # A shield is held at its boss, about a third down from the rim.
    'Shield_Heater': 0.66, 'Shield_Heater_2': 0.66,
    'Shield_Round': 0.55, 'Shield_Round_2': 0.55,
    'Shield_Celtic_Golden': 0.62, 'Shield_Wooden': 0.55,
    # Odds and ends, held about the middle.
    'Torch_Metal': 0.25, 'Whetstone': 0.50, 'Arrow': 0.50,
}
GRIP_ALONG_DEFAULT = 0.15

# AND ACROSS ITS THICKNESS, which only a shield has an opinion about. A sword
# is gripped through the middle of its own haft and the fraction below is 0.5
# for everything that is. A shield is NOT: it is held by a strap behind its
# face, so a fist placed at the middle of a fifteen-centimetre board comes out
# THROUGH it, which is what the photograph showed -- a brown hand sitting in
# the middle of the boards like a stain. 0.0 is the mesh's -Y face, 1.0 its +Y.
GRIP_ACROSS = {
    'Shield_Heater': 0.0, 'Shield_Heater_2': 0.0,
    'Shield_Round': 0.0, 'Shield_Round_2': 0.0,
    'Shield_Celtic_Golden': 0.0, 'Shield_Wooden': 0.0,
}
GRIP_ACROSS_DEFAULT = 0.5

# HOW HIGH THE HAND IS when a keeper is standing still, in centimetres off
# the ground. Read off the photograph of the watchman: his fist sits a shade
# over half way up a 180cm figure. Only the staff needs it, because only the
# staff reaches the ground.
HAND_HIGH = 93.0


def _turned(v, pitch, yaw, roll):
    """A vector through a rotator, the way the engine turns one."""
    import math
    sp, cp = math.sin(math.radians(pitch)), math.cos(math.radians(pitch))
    sy, cy = math.sin(math.radians(yaw)),   math.cos(math.radians(yaw))
    sr, cr = math.sin(math.radians(roll)),  math.cos(math.radians(roll))
    ax = (cp * cy, cp * sy, sp)
    ay = (sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp)
    az = (-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp)
    return tuple(v[0] * ax[i] + v[1] * ay[i] + v[2] * az[i] for i in range(3))


def grip_offset(mesh, scale, pitch, yaw, roll, frac=None):
    """Where the mesh's PIVOT must sit so that its grip lands in the fist."""
    b = KIT_BOUNDS.get(mesh)
    if not b:
        return GRIP
    lo, hi = b['min'][2], b['max'][2]
    if hi - lo <= 0.0:
        return GRIP
    if frac is None:
        frac = GRIP_ALONG.get(mesh, GRIP_ALONG_DEFAULT)
    # The fist, in the mesh's own space, as an offset from the mesh's pivot.
    yl, yh = b['min'][1], b['max'][1]
    across = GRIP_ACROSS.get(mesh, GRIP_ACROSS_DEFAULT)
    fist = ((0.0),
            (yl + across * (yh - yl)) * scale,
            (lo + frac * (hi - lo)) * scale)
    # Turn it the way the thing is turned, then stand the pivot back by it.
    away = _turned(fist, pitch, yaw, roll)
    return tuple(GRIP[i] - away[i] for i in range(3))



STAFF_MESH = '/Game/Interval/Folk/Wizard_Staff1.Wizard_Staff1'
STAFF_TALL = 2.60

def staff(mat=None, h=2.0, z=100, lean=6.0):
    """A staff, HELD, rather than standing on the ground beside somebody.

    It was a prop at `ox=34`: planted in the mud a third of a metre to the
    keeper's right, leaning six degrees, and no more theirs than a fence post.
    A shepherd's crook and a watchman's stave are things a person is holding.

    AND ITS HEEL ON THE GROUND, which is the whole of why `z` is in the
    signature. A staff is not carried clear of the mud like a sword; a watchman
    leans on his and a drover plants hers. So the fist does not close at a fixed
    fraction of the shaft the way it does on an axe -- it closes level with the
    hand, wherever that is, and the shaft below it reaches down as far as it
    reaches. A short staff is therefore gripped proportionally higher up than a
    long one, and both stand on the ground.

    `z` is each trade's own answer to how high up they take it, in centimetres,
    and HAND_HIGH is where the hand actually is -- measured off the photograph
    that found the grip, not assumed.
    """
    s = h / STAFF_TALL
    lo, hi = KIT_BOUNDS['Wizard_Staff1']['min'][2], KIT_BOUNDS['Wizard_Staff1']['max'][2]
    frac = min(max(HAND_HIGH / (h * 100.0), 0.05), 0.9)
    turn = (GRIP_TURN[0] + lean, GRIP_TURN[1], GRIP_TURN[2])
    ox, oy, oz = grip_offset('Wizard_Staff1', s, *turn, frac=frac)
    worn = P(STAFF_MESH, mat, s, s, s, ox=ox, oy=oy, oz=oz,
             pitch=turn[0], yaw=turn[1], roll=turn[2])
    worn['bone'] = 'hand_r'
    return worn


KEEPERS = {
  'banker':    KEEP(CLOTH, 176, [fhat('hat_cap', 176),
                                 kit_prop('BookStand', ox=40, yaw=-30)]),
  'merchant':  KEEP(CLOTH, 178, [fhat('hat_cap', 178),
                                 kit_prop('Crate_Wooden', ox=44, yaw=16)]),
  # the veil is a second part at the same offset: cloth where the hat is
  # straw, and it hangs to the shoulder (see blend/hats.py)
  'beekeeper': KEEP(CLOTH, 174, [fhat('hat_veil', 174), fhat('hat_net', 174),
                                 P(FORGED_PATH('skep'), None, 1.0, 1.0, 1.0, ox=34, oz=0)]),
  'wizard':    KEEP(CLOTH, 182, [fhat('hat_point', 182), staff(h=2.3, z=115)]),
  'collier':   KEEP(ROCK, 172, [fhat('hat_helm', 172),
                                P(FORGED_PATH('charcoal_clamp'), None, 1.0, 1.0, 1.0, ox=54, oz=0)]),
  'brewer':    KEEP(CLOTH, 174, [kit_prop('Barrel', ox=46, yaw=24)]),
  'drover':    KEEP(CLOTH, 176, [fhat('hat_straw', 176), staff(h=2.1, z=105)]),
  'innkeeper': KEEP(CLOTH, 172, [kit_prop('Barrel_Apples', ox=44, yaw=-18),
                                 kit_prop('Stool', ox=-40, oy=34)]),
  'shepherd':  KEEP(CLOTH, 176, [fhat('hat_straw', 176),
                                 staff(h=2.2, z=110),
                                 # THE LAST PRIMITIVE ON A KEEPER, and it wants
                                 # more than a swap: this world HAS a sheep, at
                                 # Beasts/Sheep/Sheep, but it is SKELETAL and
                                 # `P` places static meshes. A shepherd with a
                                 # real sheep beside her needs the mechanism
                                 # the mobs use, not another prop row.
                                 P(SPH, CLOTH, 0.44, 0.60, 0.40, ox=-46, oy=30, oz=22)]),
  'miller':    KEEP(CLOTH, 174, [fhat('hat_cap', 174),
                                 kit_prop('Bag', ox=42, yaw=40)]),
  'watchman':  KEEP(ROCK, 180, [fhat('hat_helm', 180), staff(h=2.4, z=120, lean=4)]),
  'mourner':   KEEP(CLOTH, 170, [fhat('hat_point', 170)]),
  'quarrier':  KEEP(ROCK, 174, [P(FORGED_PATH('stone_slab'), None, 1.0, 1.0, 1.0, ox=36, oz=78, pitch=28),
                                kit_prop('Vase_Rubble_Medium', ox=-46, yaw=52)]),
  'sawyer':    KEEP(CLOTH, 176, [P('/Game/Interval/Village/Sawmill_saw.Sawmill_saw', None,
                                   1.0, 1.0, 1.0, ox=38, oz=100, pitch=14)]),
  'fisher':    KEEP(CLOTH, 172, [fhat('hat_straw', 172),
                                 P(FORGED_PATH('fishing_rod'), None, 1.0, 1.0, 1.0, ox=34, oz=96, pitch=34)]),
  'arms':      KEEP(ROCK, 178, [fhat('hat_helm', 178),
                                kit_prop('WeaponStand', ox=44, yaw=-14)]),
  'armour':    KEEP(ROCK, 176, [fhat('hat_helm', 176),
                                kit_prop('Anvil', ox=46, yaw=18)]),
  'bows':      KEEP(CLOTH, 176, [kit_prop('WeaponStand', ox=42, yaw=28)]),
  # ---- THE TIMBER TRADE DOES NOT KEEP AN ANVIL ----
  #
  # This was `Anvil_Log`, which the kit names for the LOG it stands on: the
  # mesh is a steel anvil with a smith's tongs hanging off it. The lumber
  # keeper was given a forge because the filename begins with the word.
  # Reported from the road, in the plainest possible terms: "why is there an
  # anvil here at the lumber stall".
  #
  # Sawn logs are what a timber trade has beside it, and this file now knows
  # how to lie one down: length on Z, a quarter turn, lifted by its own radius.
  'lumber':    KEEP(CLOTH, 178, [P(CYL, TIMBER, 0.52, 0.52, 1.60, ox=46, oz=26, roll=90),
                                 P(CYL, TIMBER, 0.52, 0.52, 1.60, ox=46, oy=58, oz=26, roll=90),
                                 P(CYL, TIMBER, 0.52, 0.52, 1.60, ox=46, oy=29, oz=71, roll=90)]),
  'delver':    KEEP(ROCK, 172, [fhat('hat_helm', 172),
                                kit_prop('Pickaxe_Bronze', ox=40, oz=6, pitch=-74)]),
  'toll':      KEEP(CLOTH, 176, [fhat('hat_cap', 176),
                                 kit_prop('Crate_Metal', ox=42, yaw=-22)]),
  'seed':      KEEP(CLOTH, 172, [P(GEAR_PATH('Pouch_Large'), None, 1.0, 1.0, 1.0, ox=40, oz=0)]),
}

# A stall is a trestle under an awning; what distinguishes one is what is on it.
def STALL(goods):
    return K(CUBE, TIMBER, 1.60, 1.00, 0.12, 90, 0, 0.05, [
        P(CUBE, TIMBER, 0.10, 0.10, 0.88, ox=x, oy=y, oz=44)
        for x in (-68, 68) for y in (-38, 38)
    ] + [
        P(CUBE, TIMBER, 0.09, 0.09, 1.00, ox=-78, oz=138),
        P(CUBE, TIMBER, 0.09, 0.09, 1.00, ox=78, oz=138),
        P(CUBE, CLOTH, 1.86, 1.30, 0.06, oz=190, pitch=6),
    ] + goods)

# ---------------------------------------------------------------------------
# WHAT IS ON THE COUNTER.
#
# Every stall in the world is the same trestle -- `Stall_Empty`, real art out
# of the props kit -- and that is right: a market stall IS a trestle under an
# awning, and seven different trestles would be seven different markets. What
# was wrong is that every one of them was EMPTY, so the stall selling bows, the
# one selling helmets and the one selling fish were three identical bare
# tables. The world names seven kinds and it is the only place a citizen can
# buy anything; the whole of what distinguishes them was who stood behind.
#
# So these are GOODS ONLY. They are hung on the trestle the props table
# already gives each stall, after that table has had its say -- an earlier
# attempt built a whole stall out of cubes here and was silently overwritten by
# it, which is what happens when two tables both think they own a word.
#
# The goods are the ones the stall actually SELLS, and the world says which:
# `stalls` in the hello payload prices an iron-hatchet at the lumber stall, a
# pickaxe at the delve, a bow, a staff and a wand at the bows. Nothing here
# decides what a stall sells.
#
# The offsets are a guess to be PHOTOGRAPHED, not a measurement, exactly like
# the armour: a sword modelled by somebody else is not modelled around this
# trestle's counter, and the only way to place it is to put it there and look.
WEAP = lambda n: '/Game/Interval/Quaternius/Kit/%s.%s' % (n, n)
WORN_ART = lambda n: '/Game/Interval/Armour/%s.%s' % (n, n)



# Thirty-six weapons and thirteen pieces of armour, by family rather than one
# row at a time: what distinguishes `iron-sword` from `steel-sword` at forty
# paces is the colour of the metal, not the shape of it.
# ---------------------------------------------------------------------------
# THIRTY-SEVEN WEAPONS, AND THEY WERE ALL WHITE BOXES.
#
# Photographed with `gallery.py arms`, every weapon and every piece of armour
# in this world came back as a heap of cubes and cylinders out of BasicShapes.
# The audit had been reporting "worn 0 of 70 are still an engine primitive"
# the whole time, because its placeholder test did not understand the shape a
# worn row has and found no meshes in one at all. It does now: 63 of 70.
#
# The art was already here. Quaternius' Medieval Weapons kit is CC0 and has
# been imported since the session that fetched the pickaxe and the torch out of
# it -- `KIT` in apply.py names two dozen meshes, and WORN used none of them.
#
# WHAT REPLACES THE COLOUR TRICK. The families below were built on the idea
# that "what distinguishes iron-sword from steel-sword at forty paces is the
# colour of the metal, not the shape of it", and that was right for a cube with
# a tint on it. A real mesh carries its own material and flat-colouring over it
# throws away the art, so the tiers are told apart by MESH instead where the
# kit has more than one: Sword, Sword_2, Sword_Golden, Sword_Big. Where it does
# not, they share, which is honest -- a quick-javelin is a javelin.
#
# THE HAND IS A HAND ON THIS RIG. The note above about negative offsets is
# about a skeleton with no finger bones, where `hand_r` kept its parent's
# direction and ran wrist-to-elbow. The citizens are on Epic's own rig, which
# HAS fingers, so these hang at the origin of the bone the way the motion-held
# tools in apply.py already do -- and those were seen working in the world.
# ---- THE ONE MESH IN THE KIT THAT IS NOT AUTHORED AT THIS SCALE ----
#
# `Axe_Small` is about five and a half times the size of every other hand tool
# in the set. Hung on the hand bone unscaled it reaches from a citizen's fist
# to well past the tree they are cutting, and read as a log rather than a
# hatchet: "i see the hatchet is still humongous btw".
#
# It was corrected twice before and in the wrong places both times. First only
# for the GATHERING axe, which is the one a chopping animation puts in the
# hand, leaving a citizen who merely WIELDED one carrying a beam. Then in
# apply.py's own weapon table, which is built BEFORE `WORN` is merged over the
# top of it -- so `ARMED` below, at scale one, quietly won.
#
# The correction belongs to the MESH and to nothing else, so it lives here,
# beside the function that mounts a mesh on a bone, and every path that asks
# for a piece of the kit gets it. There is no table left that can outrank it.
# ---------------------------------------------------------------------------
# HOW BIG EACH MESH ACTUALLY IS.
#
# This table had ONE entry in it -- `Axe_Small` -- put there because somebody
# looked at a screenshot and said "the hatchet is still humongous". Every other
# weapon and every shield in the kit was drawn at scale one, and the kit is
# modelled about five and a half times life size: a `Sword` is 547 mesh units
# long, so a citizen with an iron sword was carrying five and a half metres of
# steel. A `Shield_Heater` came out a metre ninety across and two and a half
# high, which is a barn door, and standing in front of the citizen it was the
# reason you could not see them -- the figure was behind their own shield.
#
# MEASURED, NOT GUESSED. Every number below is a target size in centimetres
# divided by the mesh's own longest dimension, read out of the editor with
# StaticMeshTools.get_bounds. The targets are what the object is, at the
# citizen's 181 cm: a hatchet is 53, an arming sword is 100, a spear is 215,
# a heater shield is 62 tall. The method checks itself on the one entry that
# was already right -- 53 / 297.68 comes out at 0.178, against the 0.18 that
# was arrived at by eye.
#
# A mesh with no row here is drawn at its own size, which is correct for
# anything this project forged or authored.
MESH_SCALE = {
    # --- the Quaternius kit, modelled about 5.5x life size ---
    'Arrow':                0.274,   # 75 cm
    'Axe':                  0.152,   # 80
    'Axe_Double':           0.149,   # 95
    'Axe_Small':            0.178,   # 53 -- the one that was already right
    'Bow_Evil':             0.286,   # 165
    'Bow_Golden':           0.300,   # 165
    'Bow_Wooden':           0.294,   # 160
    'Bow_Wooden2':          0.294,   # 160
    'Claymore':             0.210,   # 140
    'Dagger':               0.132,   # 35
    'Dagger_2':             0.120,   # 38
    'Hammer_Double':        0.189,   # 95
    'Hammer_Small':         0.171,   # 75
    'Scythe':               0.304,   # 170
    'Spear':                0.221,   # 215
    'Sword':                0.183,   # 100
    'Sword_2':              0.194,   # 105
    'Sword_Big':            0.209,   # 135
    'Sword_Golden':         0.176,   # 105
    # --- the shields, which were the worst of it ---
    'Shield_Celtic_Golden': 0.158,   # 68 tall
    'Shield_Heater':        0.242,   # 62
    'Shield_Heater_2':      0.240,   # 63
    'Shield_Round':         0.266,   # 56
    'Shield_Round_2':       0.267,   # 56
    # --- the props kit, which is nearer life size and was still not right ---
    'Pickaxe_Bronze':       0.668,   # 80
    'Torch_Metal':          0.802,   # 52
    'Axe_Bronze':           0.919,   # 76
    'Sword_Bronze':         0.848,   # 96
    'Shield_Wooden':        0.886,   # 55
    'Whetstone':            0.154,   # 18 -- it was being drawn at over a metre
}

def ON(mesh, s=1.0, ox=0.0, oy=0.0, oz=105.0, pitch=0.0, yaw=0.0, roll=0.0):
    """One thing lying on a stall's counter, AT LIFE SIZE.

    It used to say "at its own size", and it meant it: `s` went straight into
    the scale. The Quaternius weapon kit is modelled at about five and a half
    times life -- which is the entire reason MESH_SCALE exists, twenty lines
    up -- and the goods on a stall were the one place in this file that did not
    go through it. So the bowyer's stall carried a FIVE AND A HALF METRE bow
    and the armourer's a seven-and-a-half metre spear, laid across a counter a
    metre high, in the middle of every market town on the island.
    Nobody measured them because nothing measured an assembly until
    `audit_size.py` learned to add a prop's parts to its base.

    `s` keeps its old meaning as the nudge each piece wanted relative to its
    neighbours -- the spear was already written 0.8 because it looked longest --
    and MESH_SCALE now does the work of making a sword a sword.
    """
    k = s * MESH_SCALE.get(mesh.rsplit('/', 1)[-1].split('.')[0], 1.0)
    return P(mesh, None, k, k, k, ox, oy, oz, pitch, yaw, roll, shadow=True)


STALL_GOODS = {
  # Blades laid flat, and a dagger. The world sells an iron dagger, sword and
  # spear here.
  'arms':   [ON(WEAP('Sword'), 0.9, ox=-28, oy=-6, pitch=90, yaw=8),
             ON(WEAP('Sword_2'), 0.9, ox=4, oy=10, pitch=90, yaw=-14),
             ON(WEAP('Spear'), 0.8, ox=30, oy=-14, pitch=90, yaw=40),
             ON(WEAP('Dagger'), 0.9, ox=22, oy=16, pitch=90, yaw=64)],
  # An iron helm is what it sells; the shield is the sign.
  'armour': [ON(WORN_ART('Knight_Helmet1'), 1.0, ox=-24),
             ON(WORN_ART('Helmet1'), 1.0, ox=20, oy=10),
             ON(WEAP('Shield_Heater'), 0.9, ox=2, oy=-42, oz=60, pitch=74)],
  # A hatchet, and the timber it is for. Sawn logs ARE cylinders, and saying so
  # is not a placeholder.
  'lumber': [ON(GEAR_PATH('Axe_Bronze'), 0.9, ox=-30, oy=4, pitch=90, yaw=20),
             P(CYL, TIMBER, 0.90, 0.26, 0.26, ox=26, oy=-12, oz=112, roll=90),
             P(CYL, TIMBER, 0.76, 0.22, 0.22, ox=22, oy=16, oz=130, roll=90)],
  # A bow, a staff and a wand: the three things the bowyer sells.
  'bows':   [ON(WEAP('Bow_Wooden'), 1.0, ox=-30, oy=-18, oz=98, pitch=-14, yaw=12),
             ON(WEAP('Bow_Wooden2'), 1.0, ox=30, oy=-16, oz=98, pitch=-11, yaw=-9),
             ON(WEAP('Arrow'), 1.0, ox=-4, oy=6, pitch=90, yaw=30)],
  # A pick, and what it brings up.
  'delve':  [ON(GEAR_PATH('Pickaxe_Bronze'), 1.0, ox=-28, oy=-12, pitch=64, yaw=18),
             P(SPH, ROCK, 0.26, 0.26, 0.18, ox=8, oy=4, oz=110),
             P(SPH, ROCK, 0.20, 0.20, 0.15, ox=24, oy=-8, oz=108)],
  # Sacks and a crate of roots.
  'seed':   [ON(GEAR_PATH('FarmCrate_Carrot'), 0.8, ox=-26, oy=2, oz=96),
             ON(GEAR_PATH('Pouch_Large'), 1.0, ox=18, oy=8),
             ON(GEAR_PATH('Bag'), 1.0, ox=34, oy=-10)],
  # A rod is what it sells; the barrel is to salt the catch in. No kit here has
  # a fish, and a cube is not a fish, so the stall is shown by its gear.
  'fisher': [ON(GEAR_PATH('Barrel'), 0.8, ox=-34, oy=4, oz=92),
             ON(GEAR_PATH('Bucket_Wooden_1'), 1.0, ox=14, oy=-8),
             ON(GEAR_PATH('Rope_2'), 1.0, ox=32, oy=10)],
}

# A stall is a trestle under an awning; what distinguishes one is what is on it.

# ---------------------------------------------------------------------------
# WHAT BURNS.
#
# There are hearths, watchfires, forges and torches all over this island and
# until now not one of them lit anything: after dark the only light in the
# world was the sky. A kind with an intensity gets one of the few point lights
# the window pays for, if it is near enough to be worth one.
# A FIRE THAT ERASES ITS OWN HEARTH IS TOO BRIGHT.
#
# These were set so that a lit village reads from four hundred metres up, and
# they do that. What they also did was saturate every surface within about two
# metres to pure white -- so the ring of stones, the logs and the ash the fire
# is built in were not merely hard to see, they were GONE, and the fire was a
# white hole with grass round it. It was read as bloom and it was not: with
# `r.BloomQuality 0` the white hole is still there. It is the lamp.
#
# Cut to about a third, which is bright enough to light a yard and no longer
# bright enough to delete a hearth. What carries the distant reading instead is
# the thing that was always better at it: `FireHaze`, the volumetric glow the
# lamp puts into the air, which is a soft disc several times the size of the
# light on the ground and costs nothing extra. The flames themselves are three
# tongues now and read as fire on their own.
# A FIRE YOU CAN SEE, RATHER THAN A CIRCLE YOU CANNOT LOOK AT.
#
# The watchfire was 2300 over fifteen metres, which from above is not a fire at
# all: it is a bright disc with something lost in the middle of it. The flame,
# the logs and whoever is standing at it were all inside the blown-out part, so
# the one thing the light existed to show was the one thing it hid.
#
# INTENSITY CAME DOWN FURTHER THAN REACH. The pool of light is the good part
# and it is most of what a settlement looks like after dark; what was wrong was
# how hard it burned at the centre. A smaller, softer fire still throws its
# circle and you can see what is burning.
FIRE = {
    'hearth':      (560.0, 640.0, 55.0, 0.30, True),
    'crude-hearth':(380.0, 480.0, 40.0, 0.38, True),
    'campfire':    (520.0, 600.0, 45.0, 0.42, True),
    'watchfire':   (1250.0, 1150.0, 190.0, 0.34, True),
    'furnace':     (1700.0, 1000.0, 110.0, 0.22, False),
    'smith':       (1180.0, 820.0, 90.0, 0.26, False),
    'brewpot':     (340.0, 420.0, 40.0, 0.30, True),
    'smokerack':   (260.0, 380.0, 35.0, 0.40, True),
    'brimstone-vent': (620.0, 650.0, 30.0, 0.50, False),
    'anvil':       (230.0, 340.0, 30.0, 0.55, False),
}
FIRE_COLOUR = {
    'brimstone-vent': {'r': 0.52, 'g': 1.00, 'b': 0.44, 'a': 1.0},
    'furnace': {'r': 1.00, 'g': 0.42, 'b': 0.14, 'a': 1.0},
    'smith':   {'r': 1.00, 'g': 0.44, 'b': 0.16, 'a': 1.0},
    'anvil':   {'r': 1.00, 'g': 0.38, 'b': 0.12, 'a': 1.0},
}

FLAME = M('M_IntervalFlame')

# The fire itself, sitting in whatever holds it. Nothing casts a shadow -- a
# flame is a light, not a thing in the way of one -- and nothing is hidden by
# day, because a fire in daylight is still a fire.
# `z` IS WHERE THE FLAME STANDS, NOT WHERE ITS MIDDLE IS.
#
# The engine's cone is centred on its own origin, so `oz=52` on a cone 138cm
# tall put the BASE of the flame seventeen centimetres UNDERGROUND and its
# widest part exactly level with the ring of stones -- which is why the fire
# came out through the side of the hearth it was sitting in. Reported as "the
# cylinder box it is in... the flame is burning through it", and it was: the
# cone went through the near rim and out the front.
#
# It was never visible while the heights were small, and it got worse the
# moment the cones were given headroom to stand up in, because a taller cone
# centred on the same point reaches further down as well as further up. Two
# changes that are each right on their own and wrong together, which is the
# usual way.
#
# So `z` is read as the height the fire BURNS FROM -- the top of the fuel --
# and the centring is arithmetic nobody has to hold in their head again.
def fire(w, h, z, ox=0.0, oy=0.0, shadow=False):
    return P(CONE, FLAME, w, w, h, ox=ox, oy=oy, oz=z + h * 50.0, shadow=shadow)

# ---- THREE TONGUES, NOT ONE CONE ----
#
# A fire was ONE cone, and from this camera one cone is one triangle. However
# much the material wobbles its outline -- and it does; measured, nearly two
# pixels in five change between one frame and the next -- a single smooth
# wedge reads as a shape that is shimmering rather than as fire. It was called
# what it looked like: "it kind of looks like a LED lamp".
#
# The fix is structural rather than more shader. A real fire is several tongues
# at different heights crossing each other, and the silhouette of THAT is never
# a triangle for two frames running. Three cones, one tall in the middle and
# two shorter and leaning out, is enough -- the eye stops being able to find
# the underlying shape, which is the whole job.
#
# AND THEY GUTTER SEPARATELY FOR FREE. flame.hlsl takes each fire's rhythm from
# where it STANDS, so three cones a few centimetres apart already have three
# different phases and three different tear patterns. Nothing had to be passed
# in and nothing here knows how the material works; the seed grid simply had to
# be made fine enough to tell them apart (it was a metre, which rounded all
# three to the same answer -- see `Cell` in flame.hlsl).
def hearthfire(w, h, z):
    lean = w * 34.0            # centimetres: about a third of the radius
    # All three stand on the same fuel; it is their HEIGHTS that differ, which
    # is what a fire looks like. (Before `fire` took a base this was not true:
    # three cones sharing a centre reached three different distances below the
    # ground, and the shortest one was the only one not coming out of the side
    # of the hearth.)
    return [
        fire(w,        h,        z),
        fire(w * 0.62, h * 0.70, z, ox=-lean, oy=lean * 0.35),
        fire(w * 0.54, h * 0.58, z, ox=lean * 0.55, oy=-lean * 0.80),
    ]

# THE CONE IS NOT THE FLAME, IT IS THE ROOM THE FLAME STANDS IN. The tongue
# gutters somewhere around three-fifths of the way up and never touches the
# top, so a cone sized to the flame you want gives you a flame two-thirds that
# tall -- which is how a campfire came to be shorter than the ring of stones
# around it. Every height here is the old one with that headroom added.
# Every `z` here is now the TOP OF THE FUEL -- the crossed logs, the ring of
# stones, the platform, the pot's stand -- taken from the parts listed at the
# top of this file rather than guessed. A flame that starts at the rim cannot
# come out through it.
FLAMES = {
    'hearth':       hearthfire(0.62, 1.05, 22),   # on top of the Bonfire mesh
    'crude-hearth': hearthfire(0.50, 0.84, 20),   # a ring of stone 22 tall
    'campfire':     hearthfire(0.70, 1.38, 24),   # on top of the Bonfire mesh
    'watchfire':    hearthfire(1.10, 2.85, 244),  # a bonfire ON a platform
    'furnace':      hearthfire(0.72, 0.99, 112),
    'smith':        hearthfire(0.52, 0.72, 78),
    'brewpot':      hearthfire(0.44, 0.57, 20),   # the stand is 22 tall
    'smokerack':    hearthfire(0.34, 0.45, 10),
}

WATER = M('M_IntervalWater')

# Standing water, in things people made or the land collected. Not the sea --
# the sea is ground and the ground material draws it. A disc just inside the
# rim, just below it, which is where water sits.
def pool(w, z, h=0.03):
    return P(CYL, WATER, w, w, h, oz=z, shadow=False)

POOLS = {
    # THE WATER WAS INSIDE THE STONE. A fountain's basin here is a wide disc
    # 14cm thick standing at z=46, so it fills z 39 to 53 -- and the water was
    # a 3cm sheet at z=40, which is z 38.5 to 41.5. Entirely buried, and wider
    # stone around it, so every fountain in the world was a dry tiered plinth.
    # The water sits just clear of the basin's top now.
    'fountain':   pool(1.74, 55),
    'wellspring': pool(1.16, 28),
    'dew-pond':   pool(1.58, 6),
    'bog-pool':   pool(1.48, 4),
    'birdbath':   pool(0.68, 50),
    'salt-pan':   pool(1.46, 16),
    'well':       pool(1.02, 24),
    # ---- AND THE LOOKING-GLASS, WHICH IS THE ONE WORD THAT WANTED A SHADER
    # RATHER THAN A MESH ----
    #
    # A mirror is a flat reflective plane. No kit here has one and no kit
    # needs to: `M_IntervalWater` is already a mirror -- roughness near zero,
    # which is precisely "puts the sky and the far bank on the surface" -- and
    # a disc of it in a stone ring is a looking-glass. The pool table is where
    # that disc comes from, so it goes here rather than in a props table.
    'looking-glass': pool(0.62, 74),
}

# The fires, now that `hearthstead` and the table above both exist.
for _w, (_r, _s, _n, _ll, _lr, _lz, _c) in FIRESTEADS.items():
    PARTS[_w] = hearthstead(_r, _s, _n, _ll, _lr, _lz, _c)


# AND THE DRUM THEY STOOD ON IS NOW A BED OF ASH.
#
# The base mesh of these three words is a C++ default that nothing had ever
# overridden -- a cylinder 90cm across and 50cm TALL. Flattened to a few
# centimetres it is what it should always have been: the burnt ground the fire
# is built on, which is a real thing a hearth has and which the ring of stones
# now sits around rather than on top of.
FIREBEDS = {
    'hearth':    (CYL, ROCK, 1.12, 1.12, 0.05, 2.5),
    'campfire':  (CYL, ROCK, 0.96, 0.96, 0.04, 2.0),
    'watchfire': (CYL, ROCK, 1.30, 1.30, 0.06, 3.0),
}


# ---------------------------------------------------------------------------
# THE THREE CC0 PACKS, AND THE FIRST THING MEASURING THEM SAID.
#
# `Tools/import_village.py` brings in 124 meshes from Quaternius' Medieval
# Village, Ultimate Modular Ruins and Farm Buildings packs -- all CC0, all the
# same author as everything else in this window, which is why they were chosen
# over KayKit: beside a Quaternius citizen, KayKit reads as a different game.
#
# THEY ARE NOT ALL AT THE SAME SCALE, and that is worth knowing before anything
# is placed. Measured on import, comparing the barrel each pack ships:
#
#     Medieval Village    barrel 20cm tall      about half scale
#     Ultimate Ruins      barrel 107cm tall     true scale
#     Farm Buildings      barrel n/a, Well 215cm, Windmill 972cm   true scale
#
# So the Village pack is multiplied and the other two are not. The factor is
# about 2.2 across its buildings and props -- its Well comes to 125cm against
# the Farm pack's 215cm for the same object, its market stall to 105cm against
# a stall a person has to stand under. Each row below carries its own number
# anyway, because a haystack and a bell tower do not need the same lie.
#
# Where two packs have the same thing, the one at TRUE scale wins: the well and
# the fence come from the Farm pack, not the Village one.
def VIL(n): return '/Game/Interval/Village/%s.%s' % (n, n)
# The meshes this project forged for itself -- see Tools/make_art.py.
def FORGED(n): return '/Game/Interval/Forged/%s.%s' % (n, n)


# THE COLOUR A FORGED MESH IS PAINTED, by palette name. `dress_forged.py` makes
# one material instance per `forge.PALETTE` key in this folder, so a name here
# is a name there and a typo arrives in the world as grey.
def HUE(n): return '/Game/Interval/Forged/Hues/%s.%s' % (n, n)
def RUIN(n): return '/Game/Interval/Ruins/%s.%s' % (n, n)
def FARM(n): return '/Game/Interval/Farm/%s.%s' % (n, n)

# word -> (mesh path, scale, yawJitter). Read as FURNITURE is read.
VILLAGE = {
  # --- the things a citizen stands next to every day ---
  'well':            (FARM('Well'),        1.00, 360.0),
  # A fence is drawn PER TILE and a tile is two metres. The Farm pack's fence
  # is a 5.9-metre run -- three tiles of it -- so the Village one is used here
  # instead: at 2.5 it comes to 198cm long and 82cm high, which is a tile and
  # a fence.
  'fence':           (VIL('Fence'),        2.50, 0.0),
  'railing':         (VIL('Fence'),        2.50, 0.0),
  'landmark.half-wall':  (RUIN('Bricks'),  1.00, 360.0),
  'landmark.rubble-heap':(RUIN('Bricks'),  0.80, 360.0),
  'landmark.broken-tower':(RUIN('Column_Round'), 1.00, 360.0),
  'landmark.window-arch':(RUIN('Arch_Round'), 1.00, 360.0),
  'landmark.sunken-wall':(RUIN('BridgeSection'), 1.00, 360.0),
  'landmark.staithe':(RUIN('BridgeSection'), 1.10, 0.0),
  # 'landmark.barricade' IS NOT HERE ANY MORE. It drew a barricade as `Brick`:
  # ONE BRICK, seventy-four centimetres of it, twenty-seven times over the
  # island. `PARTS` already had a barricade -- 1.8 m of timber with a brace --
  # and this was hiding it. Found by `audit_size.py` the moment every word was
  # given a declared size: nobody was ever going to walk up to twenty-seven
  # bricks and work out they were meant to be barricades.
  # --- the countryside ---
  'landmark.mill':   (FARM('Windmill'),    1.00, 360.0),
  # The hay is a 12cm prop in the Village pack -- a bale, not a stack -- so it
  # takes the biggest multiplier here by some way. Watch it before trusting it:
  # ten times is far enough to show the polygons.
  'landmark.haystack':(VIL('Hay1'),       10.00, 360.0),
  'landmark.gazebo-post':(VIL('Gazebo'),   2.20, 360.0),
  'bellwork':        (VIL('Bell_Tower'),   2.20, 360.0),
  # `cart` and `broken-cart` are NOT here. They already had real art --
  # Stall_Cart_Empty, out of the Fantasy Props kit, in FURNITURE below -- and
  # adding a second row for them here only made a word with two owners, which
  # is the fault this file has already been bitten by twice today. The Village
  # pack's Cart is the better mesh and swapping to it is a one-line change in
  # FURNITURE if anybody wants it; what is not acceptable is both.
}

# ---------------------------------------------------------------------------
# THE FOURTEEN THE AUDIT WAS NOT LOOKING AT.
#
# `Tools/audit.py` read `frameTypes` -- the node types SEEN in a sample of a
# living world -- and reported 52 of 52 drawn. The engine's own `NODE_TYPES`
# has sixty-six, and the fourteen it never asked about had NO ROW AT ALL.
#
# It surfaced from a question about one of them: "i think cart is used for
# hauling, when a hauler dies the killer can loot it?" It is -- §7do, a cart is
# what a dead hauler spills, with a shelf anybody may `unload`, and the window
# had never drawn one. The answer given was that `cart` was not a world word,
# which was read off the WINDOW's own props table. That is the wrong table to
# ask, and the audit was asking it too.
#
# What the engine says each of them is, since none is obvious from the name:
#
#   cart      §7do  a dead hauler's spill; keeps a shelf, anybody may unload
#   market    §6al  a citizen's OWN stall, raised over twenty intervals
#   fire            a plain fire, beside campfire, hearth and watchfire
#   rock            a plain rock, beside iron-rock and the rest
#   dummy     §7t   the training yard: a dummy takes a blow
#   butt      §7t   ...and a butt takes an arrow. Straw.
#   span      §7a   a wild crossing FINISHED -- decking, walkable
#   spanwork  §7a   the same crossing rising, a pool with a history
#   bell            beside bellwork
#   altar           something a verb needs to stand next to
#   eel-buck        a trap a citizen SETS, in water
#   crier           a person who stands and calls
#   house     §7dj  domestic masonry, as against a town's curtain wall
#   waystone        v1-v5 only; nothing in v6 or v7 seats one, and the type is
#                   kept so those worlds stay foundable. Drawn anyway: a word
#                   this window cannot draw is a word this window cannot draw.
UNSEEN = {
  'cart':      (VIL('Cart'),             2.20, 360.0),
  'market':    (VIL('MarketStand_1'),    2.10, 0.0),
  # `Bell1`, NOT `Bell`. The import names a material after its slot, so the
  # pack's `Bell` material took the name and the mesh became `Bell1` -- the
  # same thing happened to Bag and Hay. Pointing at the material instead cost
  # an entire run: see the note on `write` in apply.py.
  'bell':      (VIL('Bell1'),            2.20, 360.0),
  'span':      (RUIN('BridgeSection'),   1.00, 0.0),
  'spanwork':  (RUIN('BridgeSection'),   0.80, 0.0),
  'altar':     (RUIN('Column_Round_Short'), 1.00, 360.0),
  'rock':      (WOOD('Rock_Medium_1'),   1.00, 360.0),
  'waystone':  (WOOD('Rock_Medium_3'),   1.30, 360.0),
  'dummy':     (GEAR_PATH('Dummy'),      1.00, 360.0),
  # A butt is a mound of straw with a mark on it. The Village pack's hay is a
  # 12cm bale, so this is the same stretch the haystack takes and wants the
  # same look before it is trusted.
  'butt':      (VIL('Hay1'),             6.00, 360.0),
  # A wicker trap, sunk at the water's edge. `Cage_Small` is the nearest thing
  # in the props kit and it is close: a slatted box that holds something.
  'eel-buck':  (GEAR_PATH('Cage_Small'), 1.00, 360.0),
}

# AND THREE THAT ARE BEST DRAWN AS SOMETHING THIS WINDOW ALREADY DRAWS.
#
# Not laziness: `fire` IS a fire, `crier` IS a person standing in a street, and
# `house` is masonry that blocks exactly as a wall does -- §7dj says the whole
# point of the word is to tell a wall you live behind from a wall you shelter
# behind, which is a difference in MEANING and not in what it looks like from
# four hundred metres up. Copying the row is the honest answer; inventing a
# distinct shape for each would be inventing a fact about the world.
LIKEWISE = {
    'fire':   'campfire',
    'crier':  'keeper',
    'house':  'wall',
}


# ---------------------------------------------------------------------------
# THE SECOND PASS OVER THE LANDMARKS.
#
# Fifty-seven prop rows were still primitives after the first pass and over
# half of them were `landmark.*`. These are the ones the three CC0 packs and
# the kits already here can answer. What is NOT here is as deliberate: see
# `HONEST` below, and the four words at the end of this comment.
#
# Still waiting on art, and named so they are not quietly forgotten:
#   ferry, landmark.upturned-boat, landmark.shipwreck -- nothing in any kit
#     here is a boat, and a boat is not a shape that can be faked with a box.
#   landmark.siege-engine -- likewise.
#   landmark.bone-pile, landmark.skull-pile, landmark.sheep-skull -- there are
#     skeletons in the bestiary but they are whole animated creatures, not a
#     heap of bones.
#   looking-glass -- a mirror wants a flat reflective plane and its own
#     material, which is a shader job rather than a mesh job.
VILLAGE2 = {
  # --- somebody's work, left standing ---
  'landmark.scarecrow':    (GEAR_PATH('Dummy'),           1.00, 360.0),
  # 'landmark.stump' IS NOT HERE, for the same reason the lumber keeper no
  # longer has one: `Anvil_Log` is an anvil, and a stump in a wood is a stump.
  # `PARTS` has one -- a short wide timber cylinder -- which is exactly what is
  # left when a tree is felled.
  # A SKEP IS A BEEHIVE, and this project already has one.
  #
  # It was drawn as `Pot_1`, a pot, at a third again life size -- which from
  # any distance is a big upturned vessel standing in a field, and was reported
  # as looking like anything but a hive. The beekeeper beside it has had the
  # right mesh all along: `Forged/skep`, a stepped dome of coiled straw, built
  # for exactly this word. Two tables named the same thing and only one of them
  # knew what it was.
  'landmark.skep':         (FORGED('skep'),               1.10, 360.0),
  'landmark.birdbath':     (GEAR_PATH('Vase_2'),          1.40, 360.0),
  'landmark.peat-stack':   (VIL('Package_1'),             2.20, 360.0),
  'landmark.turf-stack':   (VIL('Package_2'),             2.20, 360.0),
  'muck-heap':             (VIL('Hay1'),                  8.00, 360.0),
  # A wool-snag is wool caught on a fence, so it is a fence.
  'landmark.wool-snag':    (VIL('Fence'),                 2.00, 360.0),
  # --- cut stone ---
  # A dedication is "cut stone with one name on it", §6bp, and a milestone, a
  # way-post and a headstone are the same object at three sizes.
  'dedication':            (RUIN('Column_Round_Short'),   1.00, 360.0),
  'landmark.milestone':    (RUIN('Column_Round_Short'),   0.55, 360.0),
  'landmark.way-post':     (RUIN('Column_Round_Short'),   0.70, 360.0),
  'landmark.grave':        (RUIN('Column_Round_Short'),   0.45, 360.0),
  'landmark.wellspring':   (VIL('Rock_1'),                2.40, 360.0),
  # --- the ruined and the drowned ---
  'ossuary':               (RUIN('Doors_RoundArch_Covered'), 1.00, 0.0),
  'landmark.drowned-bell': (VIL('Bell1'),                 2.00, 360.0),
  # A windfall is a tree that came down. Laid over, which is the whole word.
  'landmark.windfall':     (RUIN('DeadTree_1'),           1.00, 360.0),
  # A BLOOMERY, NOT A CHIMNEY. `Column_Square` at 1.00 is four metres tall and
  # seventy centimetres square, which is a pillar; a furnace a smith works at is
  # chest-to-head high and squat. Nothing in the kits is a bloomery, so this
  # stays the column and is cut down to something a person could reach into.
  'furnace':               (RUIN('Column_Square'),        0.55, 360.0),
  # A crude-hearth is a landmark, not a fire word, so the FIREWOOD table above
  # never reached it -- that table sets PARTS and a landmark's parts come from
  # LANDMARKS instead. Pointed straight at the bonfire here.
  'landmark.crude-hearth': (VIL('Bonfire'),               1.70, 360.0),
  # A fountain is a basin with something standing in the middle of it; the
  # water is already there, from POOLS.
  'fountain':              (RUIN('Column_Round_Short'),   1.30, 360.0),
  # A tollgate is a barrier across a road, which is a long fence.
  'tollgate':              (VIL('Fence'),                 3.20, 0.0),
  # The bare `landmark` fallback -- whatever the world names that this window
  # has no finer word for. A stone is the least wrong thing to put there.
  'landmark':              (VIL('Rock_2'),                1.60, 360.0),
  # The frame the glass is set in; the glass itself is in POOLS.
  'looking-glass':         (RUIN('Column_Round_Short'),   0.80, 360.0),
  # FORGED. See make_art.py -- three heaps of bone and a trebuchet, none of
  # which any kit here had and none of which a box could stand in for.
  # ---- AND BIG ENOUGH TO BE A HEAP ----
  #
  # MEASURED, because "too small" is a thing that can be settled with a number.
  # The forged bone pile is 44 by 38 by 13 centimetres; at the 1.30 it was
  # written with it came out 58 across and 17 high, which is ankle height and a
  # hand's span -- a few bones dropped in the grass rather than the thing a
  # beast has been dragging kills back to. A barrel standing beside it is 70 by
  # 70 by 90.
  #
  # Reported as "bonepiles too were super small". Taken to about a metre
  # across, which is a heap somebody would walk around. The skull pile goes
  # with it; a single sheep skull is a single sheep skull and stays life size.
  'landmark.bone-pile':    (FORGED('bone_pile'),          2.40, 360.0),
  'landmark.skull-pile':   (FORGED('skull_pile'),         2.00, 360.0),
  'landmark.sheep-skull':  (FORGED('sheep_skull'),        1.00, 360.0),
  # The trebuchet is forged at 1.8m and a real one is nearer five, so this is
  # the one forged piece that is multiplied -- the shape was authored, the
  # size was not thought about hard enough at the time.
  'landmark.siege-engine': (FORGED('siege_engine'),       2.60, 360.0),
}

# ---- AND THE BOATS, WHICH NOTHING ELSE COULD HAVE STOOD IN FOR ----
#
# `ferry`, `landmark.upturned-boat` and `landmark.shipwreck` were the last
# three words in the prop backlog that a box genuinely could not answer: a hull
# is a curve and a curve is the one shape a primitive has none of. Quaternius'
# Ships Pack is CC0 (its own License.txt) and has a rowboat, a lifeboat and a
# viking ship.
#
# MEASURED AND MULTIPLIED. The pack is about quarter scale like the Medieval
# Village one -- its `Boat` is 87cm long, which is a toy -- so these carry the
# biggest factors in this file after the haystack.
def SHIP(n): return '/Game/Interval/Ships/%s.%s' % (n, n)

BOATS = {
  'ferry':                   (SHIP('Boat'),        4.00, 360.0),
  'landmark.upturned-boat':  (SHIP('Boat'),        3.60, 360.0),
  # A wreck is a ship that is no longer a ship, and the only thing here that
  # says so without new art is that it is a big hull lying where a hull should
  # not be. The roll is what makes it a wreck rather than a moored ship.
  'landmark.shipwreck':      (SHIP('Viking_Ship'), 1.50, 360.0),
}
VILLAGE2.update(BOATS)

# ---------------------------------------------------------------------------
# WHAT IS GROWING IN A PLOT.
#
# The world says `plot` and carries `plantedAt` on it. Drawn as a crate, a
# field of plots was a field of boxes. What a plot looks like is a rectangle of
# turned earth with things coming up out of it in rows -- so that is what it
# is: a low dark bed, and plants standing in it.
#
# The plants are the Stylized Nature kit's, the same meshes the meadow is
# already scattered with, which is what keeps a sown field looking like it
# belongs to this world rather than like a set dressing dropped on it.
def SOWN(bed_w, bed_d, plant, n=6, spread=52.0, s=1.0):
    """A bed of turned earth with a crop standing in rows in it."""
    out = []
    for i in range(n):
        # Two rows, offset, which is how anything is planted by hand.
        row = i % 2
        along = (i // 2) - ((n // 2 - 1) / 2.0)
        out.append(P(WOOD(plant), None, s, s, s,
                     ox=along * spread, oy=(row - 0.5) * spread * 0.9,
                     oz=6.0, yaw=(i * 67) % 360))
    return out

# ---- THE BED REACHES THE NEXT RIDGE ----
#
# A furlong is drawn `^p.p.p.p.p.p.p.p.^`: strips of crop with a FURROW
# between each pair, which is what an open field is and is historically right.
# The furrow is not drawn at all, though -- it is left as whatever the ground
# under it already was -- so half of every field came out as meadow grass and
# the whole thing read as a few vegetable patches dropped on a lawn rather
# than as ploughed land. Reported exactly that way: "just a couple plots in
# the field, it doesn't really look like a field".
#
# The bed was 168cm on a 200cm tile, so it did not even fill its own square.
# Widened along the FURROW axis -- x, which is the one the drawing alternates
# on -- until two neighbouring beds meet in the middle of the furrow between
# them: 392 is a tile either side of centre, so the pair closes the gap
# exactly. Down the rows the plots are already adjacent, so y only has to
# reach its own tile's edges.
#
# NOTHING IS ADDED TO THE WORLD BY THIS. The furrow is still not a node, the
# count of farmable plots is unchanged, and the engine's tick costs exactly
# what it did -- which is the whole reason for doing it this way rather than
# ploughing the gaps with two and a half thousand more nodes.
PLOT_BED = (CUBE, TIMBER, 3.92, 2.04, 0.06, 3.0)
# MEASURED, NOT GUESSED, AND THE FIRST GUESS WAS BADLY WRONG. `Plant_7_Big` is
# 131cm ACROSS and 25cm tall -- a wide flat mat of purple flowers, not a crop --
# so six of them at full size overlapped into a two-metre carpet and a field of
# plots came back as a bank of lilac. A crop in a bed is a small upright shoot:
# `Clover_1` is 80 x 76 x 115cm, and at a third of that it is 30cm of green
# standing in turned earth, which is what a sown plot looks like.
#
#   (plant, how many, scale, how far apart in centimetres)
PLOTS = {
    'plot':               ('Clover_1',       8, 0.38, 40.0),
    'landmark.flowerbed': ('Flower_3_Group', 6, 0.35, 46.0),
}

# ---------------------------------------------------------------------------
# AND A PLOT IS NOT ONE PICTURE.
#
# The world sows it, twelve minutes pass -- GROW_TICKS_RIPE is 720 -- and it is
# ready to cut; then it is harvested and it is bare earth again. Drawn with one
# set of plants it was a standing crop the whole time, INCLUDING BEFORE ANYBODY
# HAD PLANTED ANYTHING, which is the same fault as a stump that still looks
# like a tree: the window promising something the world will refuse.
#
# Three stages, chosen by the node's own `plantedAt` against this number:
#
#   0.00  TILLED   bare turned earth. What an unsown plot is, and what a
#                  harvested one goes back to -- the engine writes plantedAt 0
#                  into an empty plot, which the window reads as this.
#   0.18  SHOOTS   a few small things showing, not yet in rows you could count
#   0.62  STANDING the full crop, which is what it was always drawn as
#
# The window does not decide WHEN a plot ripens -- 720 is the engine's number
# and apply.py copies it in. It decides only what each part of the way looks
# like, which is the whole of this window's job.
GROW_TICKS_RIPE = 720

def plot_stages(plant, n, s, gap):
    return [
        (0.00, []),
        (0.18, SOWN(0, 0, plant, max(3, n // 2), gap * 1.35, s * 0.42)),
        (0.62, SOWN(0, 0, plant, n, gap, s)),
    ]

# ---------------------------------------------------------------------------
# AND THE WORDS WHERE A PRIMITIVE IS THE RIGHT ANSWER.
#
# The audit counts any row built only from /Engine/BasicShapes as a stand-in,
# which is the correct default and is wrong for about twenty words. A wall IS a
# scaled cube. A scorch mark on the ground IS a flat disc. Counting those as
# unfinished work makes the number meaningless, and a meaningless number gets
# ignored -- which is how "worn 0 of 70 are still an engine primitive" survived
# for so long.
#
# So they are listed, with the reason, and the audit is told. A word may only
# go in here because a primitive is GENUINELY its shape -- never because it is
# hard, and never because nobody has got to it.
HONEST = {
  'wall':            'a wall is a scaled cube; the timber-frame material tells it',
  'wall.roofed':     'as wall',
  'wall.unroofed':   'as wall',
  'wall.stone':      'as wall',
  'wall.forge':      'as wall',
  'wall.trade':      'as wall',
  'rampart':         'a curtain wall is a bigger cube',
  'house':           'copies `wall`, which is honestly a cube -- §7dj, the word\n                      exists to tell a wall you live behind from one you shelter\n                      behind, which is a difference in meaning and not in shape',
  'signpost':        'a post and a board, which is two cuboids',
  'landmark.scorched-ring':  'a burnt patch of ground is a flat disc',
  'landmark.charcoal-ring':  'likewise',
  'landmark.shot-hole':      'a hole is a disc',
  'landmark.wheel-rut':      'a rut is a groove in the ground',
  'landmark.dew-mark':       'a mark is a mark',
  'landmark.daub-mark':      'likewise',
  'landmark.bog-pool':       'standing water is a disc, and it has a pool on it',
  'landmark.dew-pond':       'likewise',
  'landmark.wood-chips':     'a scatter of chips is a patch',
  'landmark.ash-heap':       'a heap is a cone',
  'landmark.charcoal-clamp': 'a covered mound is a cone, which is why it is one',
  'landmark.peat-cut':       'a cut in the ground is a box taken out of it',
  # ---- NOTHING WORN IS LISTED HERE ANY MORE ----
  #
  # The chains, the rods and the horn were exempted on the grounds that a
  # chain is a ring of metal and a horn is a cone. That argument was refused,
  # and rightly: "we can't use weapons as cylinders or cubes that's just ..
  # no go". A thing a citizen wears or wields is looked at closely and IS the
  # silhouette; the honest-primitive argument only ever held for what is
  # underfoot or architectural. The horn is forged now; the chains and rods
  # are the last two and are owed the same.
  'fishing-spot':    'a place in the water, drawn as the ripple it is',
  'deep-fish-spot':  'likewise',
  'eel-spot':        'likewise',
}


# THE STALLS ARE A FAMILY. The world has seven trades and they share a mesh;
# what tells them apart is the goods on the trestle, which STALL_GOODS already
# hangs and which this must not disturb -- so the stalls are listed apart from
# the table above, and applied without clearing `parts`.
STALL_MESH = (VIL('MarketStand_1'), 2.10, 0.0)

# THE FUEL A FIRE IS BUILT FROM. `Bonfire` is the UNLIT one: the pack also
# ships `Bonfire_Lit`, which carries its own `Fire` material, and this window
# already has a flame that gutters in three tongues and takes its rhythm from
# where the fire stands. A painted flame under a real one is worse than either.
FIREWOOD = {
    'campfire':            (VIL('Bonfire'), 2.20),
    'hearth':              (VIL('Bonfire'), 2.05),
    # A watchfire is a bonfire on a platform and a crude-hearth is the same
    # fire built by somebody with no stones to hand. Both were left out of the
    # first pass and both had the ring of pebbles instead.
    'watchfire':           (VIL('Bonfire'), 3.40),
    'landmark.crude-hearth': (VIL('Bonfire'), 1.70),
}
# AND THEN THE REAL FIREWOOD, where there is some.
#
# The ring of pebbles above was built by hand because there was no fire art in
# the project. There is now: the Medieval Village pack ships a `Bonfire` -- a
# laid pile of split logs with stones round it, which is the whole hearth in
# one mesh and better than the arithmetic ring at every size.
#
# IT HAS TO HAPPEN HERE AND NOT IN apply.py. `burn()` lays the three flame
# tongues into `parts`, so anything that ASSIGNS parts after it silently
# deletes the fire -- which is exactly what the first attempt did: the campfire
# came back as a bare pile of wood with no flame on it at all.
for _w, (_mesh, _s) in FIREWOOD.items():
    PARTS[_w] = [P(_mesh, None, _s, _s, _s, oz=0.0)]


def fill(props):
    """Puts water in everything that holds it."""
    for word, water in POOLS.items():
        if word in props:
            props[word]['parts'] = list(props[word].get('parts', [])) + [water]


def burn(props):
    """Puts a flame in everything that has a light in it.

    A flame is a LIST of tongues now, not one cone -- see `hearthfire`."""
    for word, tongues in FLAMES.items():
        if word in props:
            props[word].setdefault('parts', [])
            props[word]['parts'] = list(props[word]['parts']) + list(tongues)


# ---------------------------------------------------------------------------
# AND WHAT SMOKES.
#
# A light is what a fire is after dark. Smoke is what it is by DAY, and from a
# camera four hundred metres up it is much the more visible of the two: the
# flame is two pixels and the column is a fifteen-metre stroke leaning downwind.
# It is the one thing in an aerial view that says a village is lived in rather
# than merely built.
#
# (scale, how far above the flame it leaves, and how far above it when the tile
# is ROOFED -- because a hearth indoors has to put its smoke over the ridge or
# the hall simply fills with it behind the thatch.)
HEARTH = {'refPath': '/Game/Interval/FX/NS_Hearth.NS_Hearth'}
CRACKLE = {'refPath': '/Game/Interval/Audio/amb_fire.amb_fire'}
SMOKE = {
    'hearth':         (1.00,  60.0, 500.0),
    'crude-hearth':   (0.80,  45.0, 470.0),
    'campfire':       (1.05,  55.0, 480.0),
    # A watchfire is a bonfire on a platform: it smokes like one, and it is
    # never under a roof, so the roofed height is only there for the arithmetic.
    'watchfire':      (1.70, 210.0, 620.0),
    # A FORGE SMOKES HARDEST. It is the one fire on the island that is kept in
    # all day whether anyone needs light or not, which is also why its own
    # light is not night-only.
    'furnace':        (1.55, 130.0, 520.0),
    'smith':          (1.15, 100.0, 500.0),
    'brewpot':        (0.55,  45.0, 470.0),
    # Named for it.
    'smokerack':      (0.80,  40.0, 460.0),
    'brimstone-vent': (1.25,  35.0,  35.0),
}


def smoke(props):
    """Puts a column of smoke over everything that burns hard enough to have one."""
    for word, (scale, high, roofed) in SMOKE.items():
        if word not in props:
            continue
        props[word]['smoke'] = HEARTH
        # A FIRE IS HEARD FROM FURTHER THAN IT IS SEEN FROM, and it is the one
        # sound in a settlement that comes from somewhere rather than being the
        # air itself. It carries in proportion to how big the fire is, which is
        # what `scale` already says.
        props[word]['burning'] = CRACKLE
        props[word]['burningVolume'] = round(0.55 + 0.45 * scale, 3)
        props[word]['burningHeard'] = round(1500.0 + 1300.0 * scale, 1)
        props[word]['smokeScale'] = scale
        props[word]['smokeHeight'] = high
        props[word]['smokeHeightRoofed'] = roofed
        # Smoke by day AND by night: unlike the light, which is a budget
        # dodge, this one is simply true of a fire.
        props[word]['bSmokeAtNightOnly'] = False


def light(props):
    for word, (power, reach, high, flicker, dark) in FIRE.items():
        if word not in props:
            continue
        props[word]['lightIntensity'] = power
        props[word]['lightRadius'] = reach
        props[word]['lightHeight'] = high
        props[word]['lightFlicker'] = flicker
        props[word]['bLightAtNightOnly'] = dark
        props[word]['lightColour'] = FIRE_COLOUR.get(
            word, {'r': 1.00, 'g': 0.56, 'b': 0.22, 'a': 1.0})


# ---------------------------------------------------------------------------
# WHAT A PERSON WEARS AND CARRIES.
#
# Painting clothes on the engine's figure got the colours right and left the
# silhouette of a shop dummy. These are real pieces hung on bones, so they move
# with whoever is wearing them.
def WEAR(mesh, mat, bone, sx, sy, sz, ox=0.0, oy=0.0, oz=0.0,
         pitch=0.0, yaw=0.0, roll=0.0, shadow=True):
    w = P(mesh, mat or STONE, sx, sy, sz, ox, oy, oz, pitch, yaw, roll, shadow)
    if mat is None:
        w['material'] = None
    w['bone'] = bone
    return w

# The skirt of the tunic and a hood. Offsets and rotations here are in BONE
# space, which on this skeleton is not the same as the world's -- they were
# arrived at by hanging the piece, looking at it, and moving it.
# THE BONE'S AXES ARE NOT THE WORLD'S. On this skeleton a bone's X runs ALONG
# the bone -- up the spine, up through the skull -- so a piece hung with no
# rotation lies on its side, which is how the first skirt came out pointing
# sideways across the street. A pitch of -90 turns a piece's own up onto the
# bone's, and an offset that means "higher" is +X rather than +Z.
#
# Neither carries a material: a garment with none takes the WEARER'S, which is
# the clothing material banded by height, so the skirt comes out the colour of
# that citizen's tunic without anything looking up what colour it is.
CLOTHING = [
    dict(WEAR(CONE, None, 'pelvis', 0.66, 0.66, 0.62, ox=-24.0, pitch=-90.0),
         material=None),
    dict(WEAR(SPH, None, 'head', 0.34, 0.31, 0.31, ox=6.0, pitch=-90.0),
         material=None),
]

# Weapons and armour, by family rather than one row at a time: the world names
# thirty-six weapons and what distinguishes `iron-sword` from `steel-sword` at
# forty paces is the colour of the metal, not the shape of it.
IRON, STEEL, FINE = ROCK, STONE, M('MI_PropStone')
METAL = {'iron': IRON, 'steel': STEEL, 'quick': FINE, 'gold': FINE,
         'bone': FINE, 'shell': FINE, 'great': STEEL, 'old': IRON, 'king': CLOTH}

def metal_of(word):
    return METAL.get(word.split('-')[0], IRON)

# A KIT IS A LIST OF PIECES. A hatchet is a haft AND a head; drawn as a haft
# alone it is a stick, which is what every tool on the island was. A sword has
# a blade, a guard and a grip, and at forty paces the guard is most of what
# says it is a sword and not a bar.
WORN = {}



def kit(*pieces):
    return {'pieces': list(pieces)}

def metal_of(word):
    return METAL.get(word.split('-')[0], IRON)

# THE HAND BONE'S X RUNS UP THE ARM, not out past the fingers. Hung at a
# positive offset the hatchet floated behind the citizen's shoulder, which is
# how this was found out: there is no finger bone on this skeleton for `hand_r`
# to point at, so it keeps its parent's direction and that runs wrist to elbow.
# Everything held therefore hangs at a NEGATIVE offset -- beyond the fingers,
# which with the arms down is toward the ground.
def blade(length, guard):
    def make(mat):
        return kit(
            WEAR(CUBE, mat, 'hand_r', 0.035, 0.09, length / 100.0,
                 ox=-(length / 2.0 + 6.0), pitch=-90.0),
            WEAR(CUBE, TIMBER, 'hand_r', 0.055, 0.055, 0.13, ox=1.0, pitch=-90.0),
            WEAR(CUBE, mat, 'hand_r', 0.05, guard / 100.0, 0.035, ox=-6.0, pitch=-90.0),
        )
    return make

def hafted(length, head, wide):
    def make(mat):
        return kit(
            WEAR(CYL, TIMBER, 'hand_r', 0.055, 0.055, length / 100.0,
                 ox=-(length / 2.0 - 14.0), pitch=-90.0),
            WEAR(CUBE, mat, 'hand_r', 0.10, wide / 100.0, head / 100.0,
                 ox=-(length - 16.0), pitch=-90.0),
        )
    return make

def bow(size):
    # UPRIGHT, along the arm. Rolled ninety degrees it lay flat and came out as
    # a lance through the citizen's ribs and out the far side.
    def make(mat):
        return kit(
            WEAR(CYL, TIMBER, 'hand_l', 0.04, 0.04, size / 100.0, ox=-10.0, pitch=-90.0),
            WEAR(CUBE, CLOTH, 'hand_l', 0.012, 0.012, size / 100.0,
                 ox=-10.0, oy=6.0, pitch=-90.0),
        )
    return make

def weapon(word, shape):
    WORN[word] = shape(metal_of(word))


# ---- HOW A KIT ITEM SITS IN THE FIST ----
#
# These were hung on the bone with no rotation at all, which is not the same
# as the right one, and it was reported off the stream: "the way he holds the
# shield and hatchet is a little .. off."
#
# It is measurable rather than a matter of taste. Read `hand_r` and `hand_l`
# out of the pose the window was actually showing and turn the bone's own axes
# into the body's space, and a mesh whose blade runs +Z -- which is how this
# whole kit is modelled, checked against the bounds of the sword, the spear,
# the dagger and the hatchet -- came out pointing (-0.15, 0.53, -0.83). That
# is a hatchet held HEAD DOWN behind the leg, which is exactly what the
# photograph shows. The shield, whose face is its local +Y, faced
# (-0.46, 0.78, 0.42): a tea tray held up at the sky.
#
# So the two rotations below are derived and not dialled. They are the answer
# to "what relative rotation puts the blade up and forward, and the shield's
# face out from the body", and because a relative rotation is in BONE space it
# is the same grip in every pose afterwards -- a hand that turns turns what it
# is holding.
#
#   blade (+Z local) -> ( 0.05,  0.60,  0.80)   up and forward
#   edge  (+X local) -> (-0.04,  0.80, -0.60)   facing the way they face
#   shield face (+Y) -> ( 0.38,  0.92,  0.05)   out from the body
#   shield top  (+Z) -> (-0.02, -0.05,  1.00)   up
#
# NOT VERTICAL, DELIBERATELY. The first derivation stood the haft almost
# straight up, which is correct and invisible: this camera looks down at about
# sixty degrees, so an upright weapon is three pixels of foreshortening. Fifty
# degrees off the horizontal reads as a weapon from above and still reads as a
# grip from the side.
GRIP_WEAPON = (68.5, 102.7, -164.0)     # pitch, yaw, roll
GRIP_SHIELD = (-9.1, -132.6, -155.1)

# ---- AND WHERE ALONG ITSELF THE THING IS HELD ----
#
# Turning the grip the right way round was only half of it, and the other half
# was reported the same way: "hatchet and shield placement is still slightly
# off". A rotation says which way a thing points; it says nothing about which
# part of it is in the fist, and both of these are modelled about their own
# geometric MIDDLE.
#
# THE SHIELD rode at the ear. `Shield_Heater` is 62 cm tall at the scale this
# world draws it and its origin is its centre, so hung on a hand that the
# shield idle holds up at chest height, half of it stood above the hand and the
# top of it reached past the head. A shield is gripped at its boss, which on a
# heater is about a third down, and it is carried in against the body rather
# than out at arm's length. Eighteen centimetres down and five in.
#
# THE AXE had a quarter of its haft below the fist. `Axe_Small` runs from -124
# to +173 about its origin, which at this scale is 22 cm of haft hanging below
# the hand and 31 cm of blade above it -- so it was held like a walking stick
# gripped in the middle. A hand takes an axe near the butt, so the mesh goes up
# its own haft by thirteen centimetres.
#
# Both are expressed in BONE space, because that is what a relative offset on a
# socket is, and both were worked out by turning the direction wanted in the
# body's own space through the bone's measured axes -- the same arithmetic as
# the rotations above, and for the same reason: this project has never once got
# a number like this right by choosing it.
# ---- THE TWO NUMBERS ABOVE ARE GONE, AND HERE IS WHY ----
#
# They were typed, one pair for every weapon and one pair for every shield, and
# they could not have been right for more than one mesh each. A relative
# transform on a bone turns a mesh about the MESH'S OWN PIVOT, and the pivot is
# in a different place on every mesh in the kit: `Sword` sits 15% up from its
# butt, near the hilt, which is roughly where a hand goes; `Axe_Small` sits 42%
# up its haft, which is nowhere near. One offset served both, so the sword was
# nearly right and the hatchet floated a hand's width clear of the fist -- and
# that is what the photograph of the watchman showed.
#
# So the offset is no longer chosen. It is DERIVED, from three things:
#
#   1. GRIP and GRIP_TURN, the hand's own transform. Measured once, by eye, on
#      the watchman's staff, and the only numbers here anybody looked at.
#   2. The mesh's own extent, read out of the editor into `kit_bounds.json`.
#      Every weapon in this kit runs along its own +Z, which is the same axis
#      the staff runs along -- so the hand's turn serves all of them.
#   3. GRIP_ALONG, how far up the thing itself the fist closes, as a fraction
#      of its length from the butt. That is a fact about the OBJECT, not about
#      this skeleton or this camera, so it is the one thing worth writing down.
#
# The check that this is not another story told about numbers: the staff's own
# fraction is its pivot's, 0.632, which makes its correction exactly zero and
# leaves the one grip known to be right exactly where it was.
def held(mesh, bone='hand_r', s=1.0, ox=None, oy=None, oz=None,
         pitch=None, yaw=None, roll=None):
    # EVERY WEAPON IN THIS KIT RUNS ALONG ITS OWN +Z, and so does the staff the
    # hand was measured on -- see kit_bounds.json. So a weapon takes the hand's
    # own turn, and does not need one reasoned out from its blade's axes.
    grip = GRIP_SHIELD if bone == 'hand_l' else GRIP_TURN
    if pitch is None: pitch = grip[0]
    if yaw is None:   yaw = grip[1]
    if roll is None:  roll = grip[2]
    k = s * MESH_SCALE.get(mesh, 1.0)
    where = grip_offset(mesh, k, pitch, yaw, roll)
    if ox is None: ox = where[0]
    if oy is None: oy = where[1]
    if oz is None: oz = where[2]
    return kit(WEAR(KIT_PATH(mesh), None, bone, k, k, k, ox, oy, oz,
                    pitch, yaw, roll))

KIT_NAMES = ('Arrow', 'Axe', 'Axe_Double', 'Axe_Small', 'Bow_Evil', 'Bow_Golden',
             'Bow_Wooden', 'Bow_Wooden2', 'Claymore', 'Dagger', 'Dagger_2',
             'Hammer_Double', 'Hammer_Small', 'Scythe', 'Shield_Celtic_Golden',
             'Shield_Heater', 'Shield_Heater_2', 'Shield_Round', 'Shield_Round_2',
             'Spear', 'Sword', 'Sword_2', 'Sword_Big', 'Sword_Golden')
PROP_KIT = ('Pickaxe_Bronze', 'Torch_Metal', 'Axe_Bronze', 'Sword_Bronze',
            'Shield_Wooden', 'Whetstone')

def KIT_PATH(n):
    if n in PROP_KIT:
        return '/Game/Interval/Props/%s.%s' % (n, n)
    return '/Game/Interval/Quaternius/Kit/%s.%s' % (n, n)

# word -> the mesh it is drawn as. Tiers differ by mesh where the kit allows.
ARMED = {
    # blades
    # THE TWO DAGGERS SWAPPED WHEN THE KIT WAS REPAINTED. `Dagger_2` is the
    # one whose blade sits in the slot the kit calls `Gold`, and that slot is
    # this project's STARMETAL -- see dress_weapons.py, which explains why the
    # kit's `Golden` meshes are the quick tier here. Left as it was, the STEEL
    # dagger would have come out with a quickmetal blade, which is a worse lie
    # than two daggers sharing a shape. So the fancy one goes to the quick
    # dagger, and iron and steel share `Dagger` the way iron and steel spears
    # already share `Spear`.
    'iron-dagger': 'Dagger',      'steel-dagger': 'Dagger',
    'quick-dagger': 'Dagger_2',
    'iron-sword': 'Sword',        'steel-sword': 'Sword_2',
    'quick-sword': 'Sword_Golden', 'bare-blade': 'Sword_Bronze',
    'great-sword': 'Sword_Big',
    # hafted
    'iron-spear': 'Spear',        'steel-spear': 'Spear',
    'quick-spear': 'Spear',        'bone-spear': 'Spear',
    # THE THREE JAVELINS ARE NOT HERE ANY MORE: a javelin is thrown and a
    # spear is thrust, the world says so in as many words (`ranged`,
    # `selfAmmo`, reach 3 against reach 2), and they were the same mesh.
    'iron-mell': 'Hammer_Small',  'steel-mell': 'Hammer_Small',
    'quick-mell': 'Hammer_Double', 'great-mell': 'Hammer_Double',
    'iron-hatchet': 'Axe_Small',  'steel-hatchet': 'Axe',
    'quick-hatchet': 'Axe_Double', 'great-hatchet': 'Axe_Double',
    'iron-pickaxe': 'Pickaxe_Bronze',  'steel-pickaxe': 'Pickaxe_Bronze',
    'quick-pickaxe': 'Pickaxe_Bronze',  'great-pickaxe': 'Pickaxe_Bronze',
    'torch': 'Torch_Metal',
    # THE SCYTHE has been in the kit all along and nothing used it. `spade` is
    # the nearest word this world has to a long-hafted working tool.
    'spade': 'Scythe',
    # bows, which the kit has four of
    'wooden-bow': 'Bow_Wooden',   'heartwood-bow': 'Bow_Wooden',
    # `hollow-bow` and `horn-bow` are forged; see below. They were both this
    # same longbow, which is neither of them.
    'sigil-bow': 'Bow_Evil',      'dragonbow': 'Bow_Golden',
    # THE TWO CROSSBOWS ARE NOT HERE ANY MORE. They were `Bow_Wooden2`, which
    # is a longbow, and a longbow and a crossbow have nothing in common but a
    # string: one is a tall D held upright beside the body and the other is a
    # short wide cross held level and pointed. Forged; see below.
}
for _w, _m in ARMED.items():
    WORN[_w] = held(_m)

# ---- AND THE ARMOUR ----
#
# Three helmets, a crown, a cuirass and a pair of shoulder pads, all CC0 off
# OpenGameArt and all already imported -- see Art/Armour/README.md. The helms
# were a SPHERE with a disc under it and the plate was a cylinder about the
# spine, which the comment above defends on the grounds that "a cylinder about
# the spine is a breastplate from every angle". It is, and it is also a barrel.
ARMOUR_PATH = lambda n: '/Game/Interval/Armour/%s.%s' % (n, n)
HELMS = {
    'iron-helm': 'Helmet1',        'steel-helm': 'Knight_Helmet1',
    'quick-helm': 'Knight_Helmet3', 'gold-helm': 'Knight_Helmet2',
    # `shell-helm` and `great-helm` ARE NOT HERE ANY MORE. Both pointed at
    # `Bucket_Helmet2`, one cylinder with an eye slit doing duty for the two
    # dearest helms in the world, so a shorekeeper's season of crab shell and a
    # smith's two quick-alloy looked the same as each other and cheaper than
    # iron. Both are authored now; see below.
    # §  the cinder-crown had no row at all until the audit was fixed, and
    #    then it was `Iron_Crown` out of the armour kit -- a stock circlet
    #    with four even points, the same object a hundred games have. See
    #    below: it is authored now, because of what it is.
}
# The .obj art is modelled Y-up and arrives lying on its back, and these sit on
# a HEAD bone besides -- so the roll and the offsets are the ones apply.py
# already worked out for the guards at the gates, which were photographed.
# AND THE HELMS, WHICH ARE THREE DIFFERENT SOURCE SCALES WEARING ONE NUMBER.
#
# All six were drawn at 13, and the comment above admitted it was a guess to be
# photographed. Measured: the three `Knight_Helmet` meshes are about right at
# that number, `Helmet1` and `Iron_Crown` are authored a hundred times smaller
# and came out under three centimetres -- a helm the size of a thimble, sitting
# inside the wearer's skull -- and `Bucket_Helmet2` is authored a hundred times
# LARGER and came out over three metres, which is a helmet you could live in.
# Same table, same guess, three different answers.
HELM_SCALE = {
    'Helmet1':        100.0,   # 27 cm tall
    'Knight_Helmet1':  16.1,   # 27
    'Knight_Helmet2':  13.7,   # 28
    'Knight_Helmet3':  14.2,   # 28
    'Bucket_Helmet2':   1.20,  # 30
    'Iron_Crown':      91.7,   # 22 across
}
for _w, _m in HELMS.items():
    _k = HELM_SCALE.get(_m, 13.0)
    WORN[_w] = kit(WEAR(ARMOUR_PATH(_m), None, 'head', _k, _k, _k,
                        ox=0.0, oy=0.0, oz=0.0, roll=-90.0))
# AND SEVEN BODIES IN SEVEN METALS, WHICH WAS SEVEN BODIES IN ONE.
#
# The kit has exactly one cuirass and it always will, so the body cannot tier
# by shape the way the helms do. Passing `None` here made every plate in the
# world take the mesh's own material, so a citizen in quickmetal looked like a
# citizen in iron -- and the plate is the largest thing anybody wears, so it
# is the one piece that decides what a figure reads as down the road.
#
# The colours live in dress_armour.py, which explains why they sit darker than
# the forge palette and why quickmetal is violet.
#
# `king-shroud` is NOT in this table. It used to share the cuirass here and it
# has had a forged mesh of its own since -- see below -- because a shroud is
# cloth and not a breastplate, which is what the world says and what `METAL`
# in this file already agreed.
PLATE_METAL = {
    'iron-plate': 'MP_PlateIron',   'steel-plate': 'MP_PlateSteel',
    'quick-plate': 'MP_PlateStar',   'gold-plate':  'MP_PlateGold',
    'shell-plate': 'MP_PlateShell', 'great-plate': 'MP_PlateGreat',
}
# The names are the grades from `tiers.py`, which is where the colours come
# from: the plate on a citizen and the plate in their pack are the same metal
# because they are the same row.
assert set(PLATE_METAL) == {g + '-plate' for g in
                            ('iron', 'steel', 'quick', 'gold', 'shell', 'great')}
for _w, _mat in PLATE_METAL.items():
    WORN[_w] = kit(WEAR(ARMOUR_PATH('Cuirass'), {'refPath': ARMOUR_PATH(_mat)},
                        'spine_03', 22.0, 22.0, 22.0,
                        ox=2.0, oz=0.0, roll=-90.0))
# THE CHAINS ARE WEAPONS, AND WERE DRAWN AS JEWELLERY.
#
# `old-chain` and `gold-chain` were a torc: fourteen links about `spine_03`,
# a ring of metal at the throat. That is a reading of the WORD and not of the
# world. The engine puts `old-chain` in TWO_HANDED beside the spears and the
# great sword, gives it a blow, a reach and a swing EVERY interval, prices it
# at nothing because gold cannot buy it, and makes it the rarest thing that
# drops anywhere on the island. Drawn round somebody's neck, the one weapon a
# citizen might play a decade for could not be told from a necklace.
#
# So it hangs from the fist: twenty-six links falling ninety centimetres,
# alternating flat and upright, rusted because it comes out of the ground
# rather than off an anvil. See `chain()` in make_art.py.
#
# BUILT HANGING, which is the one place these depart from the rod's
# convention: the wand, the siphon and the handgonne all run UP from the grip
# at the origin because that is the way a held shaft points, and a chain does
# not point, it falls. The mesh runs DOWN from the grip and the pitch is the
# rod's turned through the difference.
WORN['old-chain'] = kit(WEAR(FORGED('old_chain'), None, 'hand_r',
                             1.0, 1.0, 1.0, pitch=-171.0))
WORN['gold-chain'] = kit(WEAR(FORGED('gold_chain'), None, 'hand_r',
                              1.0, 1.0, 1.0, pitch=-171.0))

# ---- THE CINDER-CROWN, AUTHORED BECAUSE OF WHAT IT IS ----
#
# It falls from the DRAGON, one in two thousand and forty-eight, on a roll
# counted per citizen so it cannot be timed by holding the beast at a point of
# life and watching the beacon (§6ba). It lands in the shared pile with the
# magic stones, "to be fought over at the pickup". And §6da is blunt about what
# it does: "worn on the head, defends nothing -- pure cosmetic".
#
# So it protects nobody and buys nothing, and is worth exactly what it looks
# like. It was being drawn as `Iron_Crown` from the armour kit: a plain circlet
# with four even points. The rarest cosmetic in a world should not be a stock
# prop, and a thing called a CINDER crown should have been in a fire.
#
# `Tools/blend/cinder_crown.py` makes it out of nine burnt masses fused into a
# ring, with splits between them and nine uneven spines, two of them snapped
# short -- because a fire does not leave a symmetrical thing behind, and the
# asymmetry is most of why it reads as burnt rather than forged. 24 cm across
# and 12.5 tall, which is a crown on a 22 cm head and not a helmet.
#
# TWO SLOTS. `Soot` is the body; `Ember` is the eighteen faces deep in the
# splits, which take an additive emissive that breathes like a coal and lifts
# at night (Tools/cinder.hlsl). A cosmetic whose whole worth is being seen
# should be visible after dark.
WORN['cinder-crown'] = kit(WEAR(FORGED('cinder_crown'), None, 'head',
                                1.0, 1.0, 1.0, 0.0, 0.0, 8.0))

# ---- AND THE TWO HELMS THAT SHARED A BUCKET ----
#
# See Tools/blend/great_helm.py and shell_helm.py for what each one is and
# why. They are authored in centimetres against a head that is 22 cm across,
# so they hang at scale one like every other forged piece, where the kit's
# helms need a scale factor apiece because three different people modelled
# them at three different sizes.
#
# The great helm is a barrel and drops past the jaw, so it hangs a little
# lower than the shell, which is a carapace and sits over the skull.
WORN['great-helm'] = kit(WEAR(FORGED('great_helm'), None, 'head',
                              1.0, 1.0, 1.0, 0.0, 0.0, -1.5))
WORN['shell-helm'] = kit(WEAR(FORGED('shell_helm'), None, 'head',
                              1.0, 1.0, 1.0, 0.0, 0.0, 3.0))

# ---- THE WAYFARER'S HOOD, WHICH NOTHING DREW AT ALL ----
#
# Two items in this world are not WORDS. A hood is `hood:<64 hex>:<tick>` and a
# fall stone is `fallstone:<64 hex>:<tick>` -- unique objects minted for one
# citizen at one moment, which `engine.js` gambit-cases in `isEquippable` so
# that they never enter the `EQUIPPABLE` set. Every audit this project runs
# reported "every equippable word in the world has a mesh" and was telling the
# truth while missing both, because they are not words.
#
# `AIntervalCitizens` now folds a minted name onto the rows below before it
# looks anything up. These are the rows.
#
# AND IT IS WORTH MORE CARE THAN ANYTHING ELSE A PERSON CAN WEAR. The engine's
# own note (§6ax): granted once for walking every trade, it survives the death
# that annihilates every other pack, it never expires where all other ground
# rots in a hundred ticks, and it carries the tick it was minted at -- "the
# only record in the world placed by history rather than by a generator". A
# citizen who had earned one walked about bare-headed.
#
# So it is AUTHORED (Tools/blend/hood.py) rather than dressed out of a kit, and
# it is deliberately not the ranger's hood in another colour: a deep cowl drawn
# back to a point, and a mantle over the shoulders that nothing else in this
# world has. From this camera a mantle is a dark disc round a pale head, and
# there is no other silhouette like it on the island.
#
# ON THE HEAD BONE, with the cowl's rim at the jaw, so it sits OVER a head
# rather than on top of one.
WORN['wayfarer-hood'] = kit(WEAR(FORGED('wayfarer_hood'), None, 'head',
                                 1.0, 1.0, 1.0, 0.0, 0.0, 9.0))

# AND THE FALL STONE, the other minted name. It is a head slot too -- see
# `slotOf` in engine.js -- and it is a STONE, so it is the graver's own rock
# rather than anything new: a small dark lump, worn rather than carried.
# IT IS RUBBLE, and the engine says so in as many words: "Rubble is what the
# mountain gives everybody; a fall-stone is what it gives the citizen who
# finished a boulder. Same rock, same swing, and the only difference is that it
# was the last one." It had been drawn with the quick-stone's crystal, which
# made the plainest object in the world look like the rarest, and lost the
# whole point of it. Nothing about a fall stone is worth more than any other
# rock except who broke it and on which day, and those are in its name.
WORN['fall-stone'] = kit(WEAR(FORGED('rubble'), None, 'head',
                              0.7, 0.7, 0.7, 0.0, 0.0, 14.0))

# ---- THE SWORN SASH, WORN BY WHOEVER HAS MASTERED THEIR TRADE ----
#
# Mastery is the largest thing a citizen can do and the window said nothing
# about it: a hundred in your own calling and a newcomer stood side by side
# looked the same. Asked for directly -- "I think we should paint something on
# the citizen when it reaches that fact".
#
# EXACTLY ONE, EVER. §5k of the engine: "Nothing unsworn passes fifty and
# nothing outside your own trade passes seventy." `MASTERY` is a hundred, so a
# citizen reaches it in their own sworn calling or in nothing at all. A mark
# that could accumulate would be telling a lie about the rules, which is what
# the first design of this did.
#
# NINE, FOR NINE SKILLS, not seventeen for seventeen callings. At the size this
# camera draws a person the MATERIAL is what carries, and nine materials are
# nine things somebody can learn to read across a market square; seventeen
# would be a colour chart. Which calling they swore is already a word on the
# nameplate. The sash says the trade.
#
# ONE MESH, NINE HUES. The shape of a sash does not depend on the trade, only
# what it is cut from does -- so `Tools/blend/sash.py` exports once and this
# hangs it nine times, which is nine material instances rather than nine
# meshes. See `SASH_HUE` in dress_forged.py for the colours.
#
# ON THE SPINE, not a hand or a head. The wayfarer's hood already owns the head
# and drapes a mantle over both shoulders; a sash goes over one shoulder and
# down across the body, which is a strong diagonal from every angle and the
# most legible shape there is on a figure ninety pixels tall.
SASH_SKILLS = {
    'woodcraft':    'Wood',
    'earthcraft':   'Iron',
    'shorecraft':   'Shell',
    'hearthcraft':  'Wheat',
    'prowess':      'Steel',
    'marksmanship': 'Keratin',
    'sorcery':      'Magic',
    'mourning':     'Bone',
    'wayfaring':    'Leather',
}
for _skill, _hue in SASH_SKILLS.items():
    WORN['sworn.' + _skill] = kit(WEAR(FORGED('sworn_sash'),
                                       HUE(_hue + 'Sash'), 'spine_03',
                                       1.0, 1.0, 1.0, 0.0, 0.0, 0.0))

# Kept under their old names because apply.py imports them, and pointed at the
# real meshes now rather than at three cubes on a stick.
HATCHET = held('Axe_Small')
PICKAXE = held('Pickaxe_Bronze')

# ========================= THE GRIP MEASURING RIG ==========================
# A GRIP can only be judged from a picture of a hand, and the only hands this
# project can photograph at full resolution are a KEEPER'S: a keeper stands
# still in a world the free camera can walk up to, where `cap.py` renders at
# whatever size is asked. A citizen holding a weapon exists only inside a Play
# session, and a Play capture is the whole editor window scaled to 1280px, in
# which a fist is about a dozen pixels across. That is why `GRIP_WEAPON_OFF`
# was DERIVED rather than measured, and why it is the one grip in this file
# nobody has ever actually looked at.
#
# So the watchman borrows a weapon for as long as it takes to look at it. It
# costs nothing when it is not asked for, and it is how GRIP was found to be
# wrong: the staff it was measured on is long enough to read as held wherever
# its pivot sits, and an axe is not.
#
#   INTERVAL_MEASURE_GRIP=1            hang the thing on the watchman
#   INTERVAL_GRIP_MESH=Sword           which thing (default Axe_Small)
#   INTERVAL_GRIP_SHIELD=Shield_Heater and one in the off hand
#   INTERVAL_GRIP_BARE=1               take his own staff away first, so it is
#                                      not standing in front of what is measured
#   INTERVAL_GRIP_OFF / _ROT           override the derivation, to test one
#
# The offset and the turn are read from the environment so a measurement is one
# apply and one photograph, rather than an edit to a constant that then has to
# be remembered and undone. INTERVAL_GRIP_OFF="x,y,z", INTERVAL_GRIP_ROT="p,y,r".
if __import__('os').environ.get('INTERVAL_MEASURE_GRIP'):
    _env = __import__('os').environ
    def _three(key, fallback):
        raw = _env.get(key)
        return tuple(float(v) for v in raw.split(',')) if raw else fallback
    _o = _three('INTERVAL_GRIP_OFF', None)
    _r = _three('INTERVAL_GRIP_ROT', None)
    _mesh = _env.get('INTERVAL_GRIP_MESH', 'Axe_Small')
    _arg = {}
    if _o: _arg.update(ox=_o[0], oy=_o[1], oz=_o[2])
    if _r: _arg.update(pitch=_r[0], yaw=_r[1], roll=_r[2])
    if _env.get('INTERVAL_GRIP_BARE'):
        KEEPERS['watchman']['parts'] = [
            q for q in KEEPERS['watchman']['parts']
            if q['mesh']['refPath'] != STAFF_MESH]
    KEEPERS['watchman']['parts'].extend([
        held(_mesh, **_arg)['pieces'][0],
    ] + ([held(_env['INTERVAL_GRIP_SHIELD'], bone='hand_l')['pieces'][0]]
         if _env.get('INTERVAL_GRIP_SHIELD') else []))
# ======================= END THE GRIP MEASURING RIG ========================

# ---- THE SHIELDS, WHICH HAD NO ROW AT ALL ----
#
# `iron-shield`, `steel-shield` and `quick-shield` are equippable, take the
# offhand, and were not in this table. The kit has FIVE shields and none was
# used. Found by diffing the engine's own EQUIPPABLE against what is drawn --
# the same sweep that turned up the fourteen missing node types.
SHIELDS = {'iron-shield': 'Shield_Heater', 'steel-shield': 'Shield_Heater_2',
           'quick-shield': 'Shield_Celtic_Golden'}
# AND AT THE ANGLE A SHIELD IS ACTUALLY CARRIED, which `held` now knows: see
# GRIP_SHIELD above. This used to pass `pitch=-91` -- a number reasoned from
# another mesh's photograph rather than from this one's axes -- and it left the
# face pointing at the sky, which is how it was reported from the stream.
for _w, _m in SHIELDS.items():
    WORN[_w] = held(_m, bone='hand_l')

# ---- THE STAVES ----
#
# `staff`, `bone-staff`, `heartwood-staff` and `goo-staff` all take the weapon
# slot and none had a mesh. The real staff this project already owns is
# Quaternius' RPG Characters one, CC0, imported as `Wizard_Staff1` -- the same
# mesh the keepers were given when their broom handles were taken away.
STAFF_HELD = '/Game/Interval/Folk/Wizard_Staff1.Wizard_Staff1'
# `staff` and `heartwood-staff` keep it: those two ARE the same stick in a
# better wood, which is what the world means by them. The other two are not --
# see the forged pair below.
for _w in ('staff', 'heartwood-staff'):
    WORN[_w] = kit(WEAR(STAFF_HELD, None, 'hand_r', 0.72, 0.72, 0.72))
# ---- AND THE THREE THAT WERE BORROWED FROM SOMETHING ELSE ----
#
# All three were stand-ins and two of them were bad ones. A wand was this same
# staff at a fifth scale, which is a twig with a staff's proportions; a
# fire-siphon was a torch; and a handgonne was `Hammer_Small`, so a citizen
# firing a gun swung a mallet. The pack sprites repeated the lie, because the
# icons are rendered from whatever is in this table.
#
# No CC0 kit here has any of the three, so they are FORGED -- see the tail of
# `make_art.py`, which measures each one against a citizen of 181cm.
#
# `pitch=-116` is the rod's angle, which was photographed: these are all built
# z-up with the grip at the origin, exactly as the rod is, so they hang in the
# hand the same way.

# Forty centimetres: a turned shaft with a leather grip, two iron ferrules and
# a stone in four claws at the tip. Short enough to go up a sleeve, which is
# the difference between a wand and a baton.
WORN['wand'] = kit(WEAR(FORGED('wand'), None, 'hand_r', 1.0, 1.0, 1.0,
                        pitch=-116.0))

# Eighty centimetres, and a PUMP rather than a burning thing: a bronze barrel
# in two banded courses, a narrow nozzle well past the hand, a plunger with a
# cross handle out of the butt, and the tank slung underneath that gives it its
# silhouette. A torch has none of that and never could.
WORN['fire-siphon'] = kit(WEAR(FORGED('fire_siphon'), None, 'hand_r',
                               1.0, 1.0, 1.0, pitch=-116.0))

# A metre, most of it pole. The fifteenth-century shape, which barely changed
# for a hundred years: a short thick iron barrel socketed onto a wooden tiller
# that goes under the arm, reinforcing rings thickest over the powder, a
# touch-hole and pan on the side, an open bore at the muzzle, and no lock of
# any kind, because you fired it with a match in your other hand.
WORN['handgonne'] = kit(WEAR(FORGED('handgonne'), None, 'hand_r',
                             1.0, 1.0, 1.0, pitch=-116.0))

# ---- AND SIX MORE THE WORLD MADE GAMBIT AND THE WINDOW DREW AS GENERIC ----
#
# Found by `Tools/audit_items.py`, which asks a question nothing had asked: how
# many DISTINCT item words are drawn by the SAME mesh, and which of those are
# a FAMILY -- one noun in several metals, which is right and is what the five
# swords are -- and which are simply a word sharing a silhouette with a word it
# is not a grade of. Seven meshes came back in the second pile. These six are
# the ones where the world itself says the item is gambit: it puts a bar on
# picking the thing up at all, and the bar is high.
#
#   crossbow        marksmanship 25      was a longbow
#   great-crossbow  marksmanship 70      was the same longbow
#   quick-flail      prowess 55, pierces  was a double-headed hammer
#   barb            prowess 45, cleaves  was a plain dagger
#   bone-staff      sorcery 40, 880g     was the generic wizard's staff
#   goo-staff       sorcery 70           was the same staff -- and sorcery 70
#                                        is the highest bar on anything there is
#
# A citizen who has spent a year reaching sorcery 70 and carries the rarest
# implement in the world should not be holding the same stick as the newcomer
# beside them. That is the whole argument, and it is the same one that got the
# wand, the fire-siphon and the handgonne forged.

# Seventy-seven centimetres of tiller with a sixty-centimetre iron prod, a
# string caught at the nut, a bridle of cord, and the lever underneath that no
# bow has and every crossbow does.
WORN['crossbow'] = kit(WEAR(FORGED('crossbow'), None, 'hand_r',
                            1.0, 1.0, 1.0, pitch=-116.0))

# The siege one: a metre of oak, a steel prod nearly a metre across, the
# STIRRUP you put a boot through to span it, and a windlass on the butt. The
# world gives it marksmanship 70, `breaks` and `burns`; it should look like an
# hour's work to load, because it is.
WORN['great-crossbow'] = kit(WEAR(FORGED('great_crossbow'), None, 'hand_r',
                                  1.0, 1.0, 1.0, pitch=-116.0))

# A haft, three links of chain and a spiked quick head. Built running DOWN from
# the grip like the old chain, because that is the only way `hang.hlsl` can
# tell how far below the fist a vertex is -- and a flail head that does not
# swing is a mace with a gap in it.
WORN['quick-flail'] = kit(WEAR(FORGED('star_flail'), None, 'hand_r',
                              1.0, 1.0, 1.0, pitch=-171.0))

# A hook: a heavy curved blade with the edge on the INSIDE and a spur off the
# back of the curve. Thirty centimetres, because the world gives it reach 1.
WORN['barb'] = kit(WEAR(FORGED('barb'), None, 'hand_r',
                        1.0, 1.0, 1.0, pitch=-116.0))

# Long bones lashed end to end with a binding at each joint, and a skull held
# in a cradle of four ribs at the head. It reads as ASSEMBLED, which is the
# difference between a bone staff and a stick.
WORN['bone-staff'] = kit(WEAR(FORGED('bone_staff'), None, 'hand_r',
                              1.0, 1.0, 1.0, pitch=-116.0))

# A shaft that leans rather than stands, and a head of the stuff itself held in
# three iron claws, with three gouts of it hanging off and stretching down the
# shaft. The drips are the silhouette; a blob on a stick is a mace.
WORN['goo-staff'] = kit(WEAR(FORGED('goo_staff'), None, 'hand_r',
                             1.0, 1.0, 1.0, pitch=-116.0))

# A hundred and fifty centimetres against a spear's two metres, half the
# thickness, a narrow barbed head, and the THONG wound at the balance with its
# loop left hanging -- the thing your fingers go through, which doubles the
# range and is the one detail that names the weapon. One mesh for all three
# metals, which is the same arrangement the three spears already had.
for _w in ('iron-javelin', 'steel-javelin', 'quick-javelin'):
    WORN[_w] = kit(WEAR(FORGED('javelin'), None, 'hand_r', 1.0, 1.0, 1.0,
                        pitch=-116.0))

# THE BEST BODY ARMOUR IN THE WORLD, which was the cheapest one's breastplate.
#
# 22 against iron-plate's 9, eight hundred gold, prowess 40 -- and a citizen
# wearing one looked exactly like a citizen in the plate a newcomer buys. A
# shroud is not a breastplate: it is a mantle, cloth over mail, with the hood
# thrown back, and it is cut asymmetrically because a cloak drawn symmetrically
# reads as a tabard on a coat-hanger.
WORN['king-shroud'] = kit(WEAR(FORGED('king_shroud'), None, 'spine_03',
                               1.0, 1.0, 1.0, pitch=-90.0))

# ---- AND THE TWO BOWS THAT WERE THE SAME LONGBOW ----
#
# `Bow_Wooden2` is a tall D, and neither of these is one. The audit called them
# a family because `hollow` and `horn` had been listed among the GRADES, which
# they are not: a grade is a different metal or wood of the same noun, and
# these are two nouns.
#
#   hollow-bow  45 gold, accuracy -10, `noAmmo` and `selfAmmo` -- it needs no
#               arrows because it makes its own out of itself
#   horn-bow    400 gold, reach 5, and a FLURRY: three blows on a six-tick
#               recovery, one of the four gambits in the world
#
# A composite recurve: limbs that bend away and then turn BACK at the tips,
# horn on the belly, sinew glued down the back, a wound riser between them.
# The double curve is the whole silhouette and is what a longbow does not have.
WORN['horn-bow'] = kit(WEAR(FORGED('horn_bow'), None, 'hand_r',
                            1.0, 1.0, 1.0, pitch=-116.0))

# A hollow stave, open at both ends so the bore can be seen, split down one
# side and bound where the split would have run on, with a cord that is not
# well strung. Nothing at forty-five gold is.
WORN['hollow-bow'] = kit(WEAR(FORGED('hollow_bow'), None, 'hand_r',
                              1.0, 1.0, 1.0, pitch=-116.0))

# ---- WHAT A CITIZEN IS CARRYING WHEN IT IS A BAR OF METAL ----
#
# Seven items take the WEAPON slot and are not weapons: gold-bar, iron, steel,
# quick-alloy, quick-grit, quick-ingot and shot. A citizen carrying one drew an
# empty hand. There is no ingot in any kit here -- and there does not need to
# be, because a bar of metal IS a cuboid, and the Ruins pack's `Brick` is a
# cuboid with a bevel and a little wear on it. Scaled down and given the metal's
# own colour it is an ingot, which is the one case in this file where a
# primitive-shaped answer is not a stand-in but the actual shape of the thing.
INGOT = '/Game/Interval/Ruins/Brick.Brick'
for _w in ('gold-bar', 'iron', 'steel', 'quick-alloy', 'quick-ingot'):
    WORN[_w] = kit(WEAR(INGOT, metal_of(_w), 'hand_r', 0.34, 0.34, 0.34))

# EXCEPT THE TWO THAT ARE NOT BARS. Of the seven, `shot` is lead balls for a
# handgonne and `quick-grit` is grit, which is by definition not a shape. Both
# were drawn as the same bevelled cuboid as a gold bar. They are carried the
# way loose heavy things are carried -- in a bag tied at the neck -- so they
# get a pouch, and what is spilling out of it is what tells them apart: four
# lead balls, or a scatter of quick grit.
WORN['shot'] = kit(WEAR(FORGED('shot'), None, 'hand_r',
                        1.0, 1.0, 1.0, pitch=-116.0))
WORN['quick-grit'] = kit(WEAR(FORGED('star_grit'), None, 'hand_r',
                             1.0, 1.0, 1.0, pitch=-116.0))

# ---- AND FIVE THAT ARE STILL WAITING FOR ART ----
#
# THE MASKS. `hare-mask`, `hart-mask`, `raven-mask` and `wolf-mask` are head
# slots and each is supposed to be a different animal's face. Nothing in any
# kit here is a mask, and the four animals that ARE here -- raven, wolf, hare --
# are whole skeletal creatures, not faces. Putting a helmet on instead would be
# worse than a primitive, because a helmet says something false; a plain plate
# over the face says only "there is something on this head", which is true.
# THESE WANT REAL ART and are the clearest remaining case for fetching some.
# FORGED, NOT FOUND. Nothing in any CC0 kit is an animal mask, and a helmet
# would have said something false. `Tools/make_art.py` writes them: a dished
# face plate twenty centimetres across with a muzzle, a beak, ears or antlers
# on the front -- which is what tells the four apart across a market square,
# and is why they could not share one mesh with a tint the way the swords do.
for _w in ('hare-mask', 'hart-mask', 'raven-mask', 'wolf-mask'):
    WORN[_w] = kit(WEAR(FORGED(_w.replace('-', '_')), None, 'head',
                        1.0, 1.0, 1.0, ox=4.0, pitch=-90.0))
# THE GREAVES. `gold-legs` is the only leg slot in the world and the armour kit
# has a cuirass, a crown, three helms and a pair of shoulder pads -- nothing for
# a leg. A band about the pelvis is where greaves sit and is honest about being
# a band.
# Greaves: two shells about the shins with a knee cop over each, forged for
# the one leg slot in the world.
WORN['gold-legs'] = kit(WEAR(FORGED('gold_legs'), None, 'pelvis',
                             1.0, 1.0, 1.0, oz=-58.0))
# A HORN is a cone, which is the whole of what a horn is.
# A drinking horn with a banded metal rim, which is what makes it a thing
# somebody owns rather than a piece fallen off an animal.
WORN['horn'] = kit(WEAR(FORGED('horn'), None, 'hand_l', 1.0, 1.0, 1.0))

# FORGED: a three-section pole with whippings at the joints, a bound leather
# grip, a butt cap, a reel and the line off the tip. The old one was two
# cylinders and was defended as "not a stand-in for a rod; it IS one", which
# was the same argument made for the chains and refused for the same reason.
ROD = kit(WEAR(FORGED('fishing_rod'), None, 'hand_r', 1.0, 1.0, 1.0,
               pitch=-116.0))
for w in ('rod', 'oak-rod', 'ironbark-rod', 'heartwood-rod'):
    WORN[w] = ROD

# ---------------------------------------------------------------------------
# THE FURNITURE OF THE WORLD, AS FURNITURE.
#
# Nearly everything the world says is standing about was a SCALED CUBE: an
# anvil was a box, a barrel a cylinder, a bed a box with four sticks under it.
# CC0 art (Quaternius, Fantasy Props MegaKit) has the real thing for most of
# them -- and, the reason it was fetched at all, a PICKAXE and a TORCH, which
# are words this world uses for tools and which no weapon pack had.
#
# Nothing here decides what an anvil IS. The world said `anvil`; this says a
# window draws that word as this mesh at this size. A word with no entry keeps
# the cube it had, which is still an honest answer.
def GEAR(name):
    return '/Game/Interval/Props/%s.%s' % (name, name)

# word -> (mesh, scale, yaw jitter). These are modelled in centimetres and
# standing on the ground, like the trees, so nothing is lifted.
FURNITURE = {
  'anvil':            ('Anvil',            1.00, 180.0),
  'brewpot':          ('Cauldron',         1.10, 360.0),
  'barrel':           ('Barrel',           1.00, 360.0),
  'table':            ('Table_Large',      1.00, 0.0),
  'bench':            ('Bench',            1.00, 0.0),
  'bed':              ('Bed_Twin1',        1.00, 0.0),
  'shelf':            ('Shelf_Simple',     1.00, 0.0),
  'cart':             ('Stall_Cart_Empty', 1.00, 360.0),
  'broken-cart':      ('Stall_Cart_Empty', 0.95, 360.0),
  'trestle':          ('Workbench',        1.00, 360.0),
  # 'chopping-block' IS NOT HERE EITHER. `Anvil_Log` is named for the log it
  # stands on and IS a steel anvil with a smith's tongs hanging off it, and it
  # had been handed to three separate words on the strength of its filename:
  # the lumber keeper, the stump landmark and this. A block you split wood on
  # is a block you split wood on, and `PARTS` has one with the axe already in
  # it.
  'banner':           ('Banner_1',         1.00, 0.0),
  # 'web' IS NOT HERE, and was: it drew a spider's web as `Rope_1`, a coiled
  # rope. The same mistake as the log pile and the withy stack -- a kit mesh
  # that has nothing to do with the word, overriding geometry that was already
  # closer. Reported as "there should be big webs around the spider, I couldn't
  # even see them", which is what a coil of rope lying in grass looks like.
  #
  # `PARTS` has a flat sheet for it, which is at least web-shaped. This kit has
  # no web in it, so a real one wants authoring; the sheet is the honest
  # stand-in until then and a rope never was.
  # 'withy-stack' AND 'log-pile' ARE NOT HERE, and were.
  #
  # Both were drawn as `Crate_Wooden`, which is a crate: a box with planks and
  # corner irons. A log pile is cut timber stacked in the open and a withy
  # stack is a bundle of willow rods, and neither is a box. Reported in one
  # line, which is all it takes once you have seen it: "a log pile looks like
  # a crate".
  #
  # The entries were worse than nothing, because `PARTS` ALREADY HAS BOTH and
  # this table overrides it: three cylinders lying across each other for the
  # logs, a timber cone for the withies. The crate was not filling a gap, it
  # was covering up geometry that was already right. A kit mesh is only an
  # improvement when the kit actually has the thing, and this one has no
  # firewood in it at all.
  'hurdle':           ('Peg_Rack',         1.00, 360.0),
  'sheep-hurdle':     ('Peg_Rack',         1.00, 360.0),
  # 'scaffold' IS NOT HERE EITHER. `WeaponStand` is a rack for swords and is
  # 1.4 m; a scaffold is 2.8 m of timber and `PARTS` has it.
  'tally-post':       ('BookStand',        1.00, 360.0),
  'tally-half':       ('BookStand',        0.85, 360.0),
}

# ---------------------------------------------------------------------------
# WHAT GROWS UNDERFOOT, AS PLANTS RATHER THAN AS GREEN PEBBLES.
#
# Every one of the seventeen scattered grounds was a SQUASHED SPHERE -- an
# engine ball at (0.21, 0.21, 0.12), which is forty-two centimetres across and
# twenty-four high, painted green and dropped on two tiles in five. Close to,
# they read as exactly what they are: green pebbles lying on a lawn. That is
# the first thing anybody asks about when they look at the ground.
#
# The same CC0 nature kit that supplied the trees has the real thing: grass in
# two lengths and two sorts, clover, ferns, bushes, mushrooms, and pebbles for
# the places where a pebble is the honest answer.
#
# ground -> (mesh, scale, per-tile chance). The world names the ground; this
# says what a window grows on it, and a ground with no entry grows nothing.
# The fourth number is HOW MANY TIMES the tile is asked, which is new: a tile
# used to be allowed exactly one thing growing on it, so a meadow at ninety per
# cent was ninety per cent of tiles carrying ONE tuft. Seven tries at eighty
# per cent is a sward. See FIntervalScatterKind::PerTileCount.
#
# AND SO IS THE GRASS. At a scale of one these blades stood chest-high on a
# citizen -- a meadow of pampas with a man wading through it. Grass in a
# pasture is ankle to shin: a fifth of the mesh, and rather more of it, so the
# ground reads as a sward instead of as a few reeds poking out of a lawn.
UNDERFOOT = {
  # ---- MANY AND SMALL, NOT FEW AND LARGE ----
  #
  # The open grass was seven tries a tile at about a third scale, which comes
  # out as five or six separate CLUMPS standing a hand's breadth apart with
  # painted ground between them, each one tall enough to read as a plant in
  # its own right. The eye does not see a field; it sees a floor with pot
  # plants on it, and the tile grid shows through between them. Reported as
  # "too big or too sparse", which is exactly right: it is both, and they are
  # the same fault.
  #
  # Twice the tries at two thirds the height is the same amount of greenery
  # arranged as a sward. Only the three open grasses change -- fern, bush,
  # reed and the stony grounds are meant to be individual things standing
  # apart, and making those denser would be a different mistake.
  'meadow':      ('Grass_Common_Tall', 0.21, 0.9, 15),
  'heartlands':  ('Grass_Common_Short', 0.22, 0.9, 15),
  'downs':       ('Grass_Wispy_Short', 0.20, 0.84, 13),
  'trodden':     ('Grass_Wispy_Short', 0.18, 0.3, 3),
  'greenwood':   ('Fern_1', 0.42, 0.5, 4),
  'forest':      ('Bush_Common', 0.28, 0.38, 3),
  'wilds':       ('Plant_1', 0.36, 0.45, 4),
  'fens':        ('Grass_Wispy_Tall', 0.32, 0.55, 5),
  'moor':        ('Plant_7', 0.28, 0.5, 5),
  'peat':        ('Plant_7', 0.22, 0.3, 3),
  'crags':       ('Rock_Medium_1', 0.35, 0.24, 2),
  'scree':       ('Pebble_Square_1', 0.55, 0.4, 3),
  'gravel':      ('Pebble_Round_1', 0.45, 0.26, 3),
  'mountain':    ('Rock_Medium_2', 0.4, 0.2, 2),
  'chalk':       ('Pebble_Round_3', 0.45, 0.2, 2),
  'shingle':     ('Pebble_Round_2', 0.55, 0.45, 4),
  'sand':        ('Pebble_Round_5', 0.35, 0.12, 2),
  # ---------------------------------------------------------------------------
  # AND THE SPINE, WHICH IS NOT A GROUND AT ALL.
  #
  # `ridge` is a reserved key: the island's spine has no terrain of its own --
  # its tiles read as ordinary `crags`, the same as the whole eastern third of
  # the world -- so the bridge tells the window WHERE it is and this says what
  # grows there. It is the one place a tile's planting is decided by something
  # other than what it is made of.
  #
  # Big rock, and a great deal of it. A wall that two named passes cross, and
  # that the generator SHUTS one of, should be the most obvious thing on the
  # map; drawn as rough country it was invisible, and a citizen walked into it
  # sixty times before anything said there was a mountain there. Nearly every
  # tile carries stone and most carry several, so the run reads as one mass
  # rather than as a scatter of boulders with gaps a person could walk.
  # ---- A RIDGE IS ROCK SHOWING THROUGH, NOT A WALL OF IT ----
  #
  # This was ('Rock_Medium_2', 1.35, 0.95, 4): FOUR tries a tile at ninety-five
  # per cent, which is very nearly four boulders on every two-metre tile, each
  # of them FOUR METRES across. A ridge came out as a continuous rampart of
  # stone two or three deep, and that is what has been reported from the window
  # for weeks as "big grey rock tentacles": from a mile off, a line of
  # overlapping four-metre boulders along a skyline reads as lumps and arches,
  # and the gaps between them read as holes you could walk through.
  #
  # THE FLICKER IS THE SAME ROW. Scatter is culled at two hundred metres, hard
  # and without a fade, so a whole ridge of them appears and vanishes in one
  # step as the citizen walks -- which is the "going up and down". They are
  # grey because they are the kit's own rock with no material override, which
  # is also why they read as uncoloured rather than as stone.
  #
  # Rock showing through a hill is OCCASIONAL and it is person-sized. 2.3 m,
  # and about one boulder every three tiles instead of four every one.
  'ridge':       ('Rock_Medium_2', 0.75, 0.30, 2),
}

# ---------------------------------------------------------------------------
# THE BESTIARY, AS ANIMALS RATHER THAN AS COLOURED CYLINDERS.
#
# The world names twenty-four mobs and twenty-one of the drawn ones were an
# engine primitive with a tinted material on it: a goblin was a green cylinder,
# a wolf a brown cube, a dragon a big box. CC0 art (Quaternius) has real,
# animated creatures for most of them.
#
# Where the kit has no such animal the row is LEFT ALONE rather than filled
# with something that is nearly right. A crow drawn as a bat is a worse answer
# than a crow drawn as a cylinder, because the cylinder does not claim to be
# anything.
# THE FOLDER IS NOT ALWAYS THE NAME. The importer renamed the skeleton mesh to
# `Skeleton1` because an asset of type Skeleton already owned `Skeleton` in that
# folder, and the FOLDER kept the original -- so the obvious path is wrong for
# exactly one beast, and one bad object reference makes the setter refuse the
# WHOLE Mobs map. That is how eleven of twenty-two mobs quietly went missing.
BEAST_FOLDER = {'Skeleton1': 'Skeleton',
                'Risen_Male': 'Risen', 'Risen_Female': 'Risen'}

def BEAST(name):
    folder = BEAST_FOLDER.get(name, name)
    return '/Game/Interval/Beasts/%s/%s.%s' % (folder, name, name)

# THE DEAD AND THE CONJURED WEAR CLOTHES.
#
# Every humanoid below is the citizens' own body, and that body is a BARE one:
# an outfit is a separate mesh following its pose, which is how a citizen is
# built. A row that names no outfit is a row that walks the moor in its
# underwear. `None` is for the things that are not people.
# ---------------------------------------------------------------------------
# THE WILD ONES, which are not in the Beasts folder.
#
# Ten of this world's mobs were an engine primitive with a tinted material on
# it. The CC0 art that has them is genuinely hard to reach -- four routes were
# tried and one worked; see Tools/polypizza.py -- and it lands in its own
# folder, one creature to a folder, because every pack of Quaternius's names
# its animations `Idle`, `Walk`, `Attack` and they would fight.
#
# THE SCALES ARE A RATIO, NOT A GUESS. These .glb files import at something
# like a hundred times life size -- a crab measures two hundred and fifty
# metres across -- so each scale is (the size the thing should be) divided by
# (the size it arrived at), measured from its own bounds. A wolf is 1.3 m nose
# to tail, a goat 1.2 m, a troll 2.85 m, a crab a hand's breadth.
def WILD(name):
    return '/Game/Interval/Wild/%s/%s.%s' % (name, name, name)


# word -> (skeletal mesh, scale, z offset[, outfit])
BEASTS = {
  # MEASURED, NOT GUESSED. `Sheep` is 5.9 m nose to tail at scale one and `Pig`
  # is 10.3 m, which are not animals, they are barns. Both kits are authored at
  # a size this world does not use and were taken at face value. A ewe is about
  # 1.3 m long and 0.9 m at the shoulder; a boar is about 1.5 m and heavier,
  # and the scales below are those divided by what the meshes actually measure.
  'sheep':          ('Sheep',       0.22,  0.0),
  'boar':           ('Pig',         0.15,  0.0),
  # (`fen-adder` is deliberately NOT here. The kit's snake has cartoon eyes the
  #  size of its head, and a thing that claims to be a snake and is a cartoon
  #  is worse than a shape that claims nothing. It keeps its primitive until
  #  there is a snake that belongs in this world.)
  # ---- THESE THREE WERE THE SIZE OF BUILDINGS, AND ONE OF THEM WAS THE
  #      THING ON THE HORIZON ----
  #
  # The note above says the scales here are measured and not guessed, and for
  # the sheep and the boar they are: both are worked out from the mesh's own
  # bounds against a real animal. Nobody ever did that for the monsters, and
  # the monsters are the meshes with the widest spread of author scale in the
  # project. `Tools/audit_size.py` now measures all twenty-four.
  #
  # THE SPIDER WAS 8.3 METRES ACROSS. `Spider` is 5.9 m leg to leg in the file
  # and it was multiplied by 1.4. That is not a spider, it is a roof on eight
  # legs, and it is what was reported from the window for weeks as "big rock
  # tentacles that go up and down": a grey arch, several in a row, standing
  # above the tree line on the horizon and gone the next time anybody looked.
  # They are its LEGS, seen side on from half a mile away, and they came and
  # went because the thing they belong to walks. 2.4 m is still the largest
  # animal on the island and still too big to want to meet.
  #
  # THE DRAGON stood 8.76 m -- within a metre of the bellworks, the tallest
  # thing anybody builds here. A dragon is allowed to be the biggest beast in
  # the world without being the tallest object in it. 5 m.
  'great-spider':   ('Spider',      0.40,  0.0),
  'dragon':         ('Dragon',      1.30,  0.0),
  # A LAMPREY IS NOT A CLOWNFISH.
  #
  # `Fish3` is an orange-and-white tropical reef fish, chosen because the kit
  # had three fish in it and this word wanted a fish. A mere-lamprey is an
  # eel -- long, sinuous, jawless -- and lives in fresh water in a fen. The
  # reef fish was found by rendering the whole bestiary onto one sheet, which
  # is the only way anybody was going to see it: nothing takes a citizen to
  # the mere, so nobody had ever met one.
  #
  # `Snake` is the eel-shaped thing this kit actually has, and it is not the
  # same asset as the `snake` the fen-adder uses -- that one is Art/Wild's
  # glTF, this is Art/Beasts' FBX. 3.04 m in the file and a lamprey is about
  # one, so 0.33.
  'mere-lamprey':   ('Snake',       0.33,  0.0),
  # 3.7 m of jelly, which is a cottage. A thing that drinks a well dry is about
  # the size of the well. 1.6 m.
  'quencher':       ('Slime',       0.52,  0.0),
  # THE DEAD ARE THE LIVING, DRAINED.
  #
  # A cartoon skeleton -- round skull, black eye sockets -- was tried for these
  # five words and is plainly wrong beside people modelled at human
  # proportions. It is the same mistake as the chibi adventurers, in a smaller
  # place. What reads right is the citizens' OWN body, uncut and drained of
  # colour: see `Pallor` in person_mat.hlsl, and Risen_* which is a copy of the
  # base figure so that dressing a corpse cannot touch the living.
  'risen':          ('Risen_Male',   1.00,  0.0, 'Male_Peasant'),
  'barrow-wight':   ('Risen_Male',   1.08,  0.0, 'Male_Peasant'),
  'gibbet-dead':    ('Risen_Female', 1.00,  0.0, 'Female_Peasant'),
  # The king of the gibbets keeps a hood, being the one who raises the rest.
  'gibbet-king':    ('Risen_Male',   1.18,  0.0, 'Male_Ranger'),
  'skeleton-knight':('Risen_Male',   1.04,  0.0, 'Male_Ranger'),
}

# ---------------------------------------------------------------------------
# WHAT EACH CREATURE'S CLIPS ARE CALLED.
#
# Every one of these packs ships its animations under the creature's own name
# -- `wolf_aAnimalArmature_Idle`, `SheepArmature_Idle`,
# `SpiderHumanArmature_Spider_Death` -- so the table is built by MATCHING
# rather than by anybody typing out a hundred and forty asset paths, which
# would be wrong the first time a pack is re-imported under a different name.
#
# The verbs are the citizens' verbs, because a word should mean one thing
# across the whole window: `still`, `walk`, `felled`, `fight`.
BEAST_VERB = (
    # (verb, the endings that mean it, in order of preference)
    ('still',  ('_Idle', 'Idle')),
    ('walk',   ('_Walk', 'Walk', '_Gallop', 'Gallop', '_Run', 'Run',
                '_Swim', 'Swim', '_Fly', 'Fly')),
    ('felled', ('_Death', 'Death')),
    ('fight',  ('_Attack', 'Attack', '_Bite', 'Bite')),
)

# Clips that match a verb's word and are not that verb. `Idle_HitReact_Left`
# is a flinch, `Jump_ToIdle` is a landing, and either one looped for ever is a
# creature having a fit.
BEAST_NOT = ('HitReact', 'ToIdle', '_2', 'Jump', 'Sit', 'Sleep', 'Eating')


def beast_motions(folder_on_disk, content_path):
    """{verb: asset path} for one creature, read off its own folder."""
    import os as _os
    if not _os.path.isdir(folder_on_disk):
        return {}
    clips = [f[:-7] for f in sorted(_os.listdir(folder_on_disk))
             if f.endswith('.uasset')]
    # A clip is an animation if it is not the mesh, the skeleton, the physics
    # asset, a material or a texture -- all of which this project names.
    clips = [c for c in clips
             if not c.endswith('_Skeleton') and not c.endswith('_PhysicsAsset')
             and not c.startswith('MW_') and not c.startswith('T_')]
    out = {}
    for verb, endings in BEAST_VERB:
        for ending in endings:
            hit = [c for c in clips
                   if c.endswith(ending) and not any(b in c for b in BEAST_NOT)]
            if hit:
                # The shortest name is the plainest clip: `Idle` over
                # `Idle_LookAround`, which is the one a creature should be
                # doing when nothing is happening.
                pick = sorted(hit, key=len)[0]
                out[verb] = '%s/%s.%s' % (content_path, pick, pick)
                break
    return out


# The wild ones are kept apart because they take a different path helper, not
# because they are a different kind of thing.
# word -> (folder, scale, z offset)
WILD_BEASTS = {
  # A HUNDRED, TWICE, IN OPPOSITE DIRECTIONS.
  #
  # These scales were wrong twice, by the same factor, in both directions, and
  # the second mistake was made while fixing the first. It is worth writing the
  # whole thing down because the two measurements available here disagree and
  # only one of them is the one that gets drawn.
  #
  # FIRST the scales were computed against `get_bounds`, read as though it were
  # the model. It is not: it is the ANIMATED extent, and goblin_a came back at
  # 462 metres because a clip translates its root a long way. Divide a real
  # animal's size by 462 and every beast is drawn a centimetre and a half tall.
  # Reported from the stream as "now they're invisible".
  #
  # SO they were recomputed from the glTF itself with Tools/glbsize.py, which
  # reads the accessor bounds and walks the node transforms. That number is
  # honest about the FILE and says nothing about the ASSET, and the two differ
  # here by a hundred: every file in Art/Wild but one hangs its creature under
  # an armature node scaled by 100, and Interchange bakes that into the bind
  # pose on the way in. Multiplying the scales by a hundred to undo the first
  # mistake made the second one, and a fen-adder ninety metres long lay across
  # the moor with its head in the air. Reported from the stream as trees out of
  # Super Mario.
  #
  # SO the numbers below divide the size the animal should be by the size the
  # ASSET IN THE PROJECT measures -- `get_bounds`, the lying one -- because
  # that inflation is in the mesh and is therefore in the picture. Where a clip
  # really does translate the root the two disagree again and the source file
  # is right; the way to tell them apart is that a baked armature scale is the
  # SAME factor for every mesh in the pack, and an animation's reach is not.
  #
  # `deer.gltf` is the one file in Art/Wild with no scaled armature, which is
  # why it is the one beast that was never wrong, and it is the control that
  # settled this.
  'wolf':           ('wolf_a',    0.002341, 0.0),   # 1.3m nose to tail
  # A GOAT THAT WAS A SHEEP, AND IS NOW A DEER.
  #
  # `goat.glb` was fetched by filename and the mesh inside it is called
  # `Sheep` -- so the mountain-goat and the world's actual sheep were the same
  # animal, drawn twice. Quaternius has no goat anywhere in his catalogue and
  # neither does any other CC0 kit reachable from here, so this is the nearest
  # neighbour rather than the right word: a deer has the slender legs, the
  # narrow chest and the high alpine carriage a goat has, where a sheep has
  # none of them.
  #
  # Scaled to a GOAT and not to a deer. The world says `mountain-goat` and the
  # size is what tells a citizen how far away it is; 1.2 m over the 4.40 m the
  # file measures.
  #
  # THIS IS THE ONE ROW WITH NO HUNDRED IN IT, and it is not an exception that
  # was made, it is the control that found the rule: `deer.gltf` is the only
  # file in Art/Wild that does not hang its creature under an armature scaled
  # by 100, so the file and the asset agree about it and its scale never
  # needed correcting. Every other row above is a hundredth of what the source
  # file alone would suggest. See the note over this table.
  'mountain-goat':  ('deer',      0.2729, 0.0),   # 1.2m
  'shore-crab':     ('crab',      0.001180, 0.0),  # a hand's breadth, but readable
  'fen-adder':      ('snake',     0.002964, 0.0),  # 0.9m
  # A GOBLIN IS GREEN, AND THIS KIT HAS FOUR TO CHOOSE FROM.
  #
  # `goblin_a` was picked by name and is not a goblin: it is a BLUE creature
  # with a BASEBALL BAT, which was reported from the stream in as many words.
  # Photographed all four before choosing this time -- `goblin_b` has no
  # textures at all and renders as grey blocks, `goblin_d` is the smallest, and
  # `goblin_c` is green, has pointed ears, a belt and a spiked wooden club.
  # 4.68m in the file, drawn at 1.3m like the one it replaces.
  'goblin':         ('goblin_c',  0.002775, 0.0),  # 1.3m, a small person
  'troll':          ('ogre',      0.005085, 0.0),  # 2.85m, the biggest thing that walks
  'scree-imp':      ('monster_a', 0.001636, 0.0),  # 0.9m, made of the crags it lives in
}

# THE DARK ONES, out of the Bestiary kit.
#
# NOT CC0 -- Quaternius Asset License v1.0, see Art/Bestiary/LICENCE-NOTE.txt.
# Using them here is expressly permitted; redistributing the raw files is not.
#
# THE SCALES ARE VERY NEARLY ONE, and that is the point: this kit is modelled at
# human scale already. Measured from their own bounds against a citizen at
# 1.81m -- Skeleton_A stands 1.79m, Skeleton_B 1.82m -- so they belong in the
# same street rather than arriving from another game.
#
# `barrow-wight` is DELIBERATELY NOT HERE. It keeps the citizens' own body
# drained of colour, which was a considered choice and is written up over
# BEASTS: a wight is a risen person, not a bare skeleton, and a bone figure
# would say the wrong thing about what it is. The skeleton-knight is the one
# that had no art at all.
def DARK(name):
    return '/Game/Interval/Dark/%s.%s' % (name, name)

DARK_BEASTS = {
  # `skeleton-knight` is the world's word. `skeleton` is NOT -- the bestiary
  # report said so the moment it was added, which is what that report is for.
  # Skeleton_A stays imported and unused until a founding has a word for it.
  # Measured 2.02m from its own glTF, which agrees with the editor -- this
  # kit's bounds are honest, unlike the Wild one's.
  'skeleton-knight': ('Skeleton_B', 0.8932, 0.0),
}

# AND THE THREE WITH NO RIG, which are static meshes and so go in a different
# field. A crow on a gibbet does not need a skeleton; a siren, arguably, does,
# and will get one when there is a rigged CC0 one to give her.
# word -> (folder, scale, z offset)
WILD_STILL = {
  # A HUNDRED AGAIN, in both of these: see the long note over WILD_BEASTS.
  # `raven.glb` and `mermaid.glb` hang their meshes under a node scaled by 100
  # exactly as the animated ones do, so a crow was drawn forty-four metres
  # across and a siren stood a hundred and eighty-seven metres out of the sea.
  # The intent these numbers were written with is unchanged -- a 0.44 m crow,
  # a 1.87 m siren -- and only the hundred has gone.
  'carrion-crow':   ('raven',    0.0058, 32.0, (0.0, 0.0, 0.0)),
  'siren':          ('mermaid',  0.0068,  0.0, (0.0, 0.0, 0.0)),
  # THE BEAR ARRIVES LYING DOWN. Measured, not guessed: 247 cm long, 198 cm
  # through, and 51 cm from top to bottom -- which is a bear on its side, or
  # rather a bear modelled Y-up. A quarter turn of roll stands it on its feet,
  # and the scale then makes it two metres nose to tail, which is a bear.
  # A BEAR AT LAST, AND IT IS NOT A BEAR TRAP.
  #
  # `bear_a` and `bear_b` both hold a mesh called `BearTrap_Open` with no rig
  # and no animations -- fetched by filename, years ago, and never looked at.
  # It drew as a grey arc half-sunk in the grass and was read from the stream
  # as exactly what it is: "this is a bear trap, not a bear". No rotation was
  # ever going to fix it; 2.5 m long by 2.0 m wide by 0.5 m tall is not a bear
  # in any orientation, it is a flat ring with jaws.
  #
  # This one is CC0 by Phelippeau Rudy, off OpenGameArt, and is the only CC0
  # bear that exists anywhere reachable: Quaternius has none in any pack,
  # poly.pizza's only CC0 bear IS the trap, and every other one is CC-BY, which
  # cannot ship in an open repository. It came as a `.blend` and nothing else,
  # so Tools/blendmesh.py reads it -- see that file for why reading a .blend is
  # reasonable rather than heroic.
  #
  # 9.352 m in the file and a bear is about two, so 0.2139. The mesh's feet sit
  # 3.242 m below its origin, which at that scale is 69 cm: without the lift it
  # would stand buried to the shoulder, which is the fault the trap had and the
  # one worth not repeating. No lean -- it is modelled upright and facing along
  # its own length.
  'bear':           ('bear',     0.2139, 69.3, (0.0, 0.0, 0.0)),
}

# ---------------------------------------------------------------------------
# AND THE INCURSION, WHICH IS FIVE THINGS.
#
# `incursion` is a mob TYPE with a `face` under it -- the generic word is the
# fallback, not the creature. The window looks up `incursion.<face>` first and
# `incursion` after, the same way a node prefers `type.kind`; see MobKey in
# IntervalCitizens.cpp.
#
# One silhouette in five skins, which is the decision the browser windows made
# and there is no reason for this one to disagree: the same figure the risen
# use, painted whole in the material of the country it came out of. It stands a
# little taller than a person and a little off the ground, because the thing
# has no feet -- the browser draws it drifting, with a seep under it instead of
# a shadow.
#
# word -> (skeletal mesh, scale, z offset, material)
# THE HOOD IS THE WHOLE SILHOUETTE. The browser draws these as a hooded thing
# with a ragged hem, so the ranger's outfit -- which is the only hooded one in
# the wardrobe -- goes over the body, and the country's material is painted
# over BOTH. A wraith is one colour from cowl to hem; that is what makes it a
# conjured thing rather than somebody in a cloak.
FACES = {
  'incursion.woodwraith':   ('Risen_Male',   1.16, 14.0, 'MI_FaceWoodwraith', 'Male_Ranger'),
  'incursion.gargoyle':     ('Risen_Male',   1.20, 12.0, 'MI_FaceGargoyle',   'Male_Ranger'),
  'incursion.drownling':    ('Risen_Female', 1.14, 14.0, 'MI_FaceDrownling',  'Female_Ranger'),
  'incursion.wilds-shade':  ('Risen_Female', 1.18, 16.0, 'MI_FaceWildsShade', 'Female_Ranger'),
  'incursion.haunt':        ('Risen_Male',   1.15, 16.0, 'MI_FaceHaunt',      'Male_Ranger'),
  # The generic, for a face this window has never heard of. A world that grows
  # a sixth one still draws something, and it is the pale one.
  'incursion':              ('Risen_Male',   1.15, 16.0, 'MI_FaceHaunt',      'Male_Ranger'),
}

# And the two that are not creatures at all: a training dummy and an archery
# butt, which the props kit has as actual objects.
DRILL = {
  'dummy': ('Dummy',       1.00),
  'butt':  ('WeaponStand', 1.00),
}

# ---------------------------------------------------------------------------
# THE KEEPERS, WHO ARE PEOPLE.
#
# Twenty-three trades stand at stalls and doorways in this world and every one
# of them was a cylinder with a hat on it. They are people, and this window has
# people: the same modular figures the citizens are made of, a bare body
# carrying the head and the hands and an outfit over it.
#
# A prop kind holds ONE skeletal mesh, so the rest of the figure goes in
# `skeletalParts` and follows its pose -- see AIntervalStructures::StandFigure,
# which is the citizens' own arrangement moved across.
#
# Nothing here decides what a brewer IS. The world said `brewer`; this says a
# window draws that word as a woman in peasant dress. Which trade wears what is
# a level's opinion and a poor one is still an opinion: a watchman in a
# ranger's hood reads as a watchman, and that is the whole job.
UNI_BASE   = '/Game/Interval/Universal/Base/'
UNI_PEOPLE = '/Game/Interval/Universal/People/'

MALE   = UNI_BASE + 'Superhero_Male_FullBody.Superhero_Male_FullBody'
FEMALE = UNI_BASE + 'Superhero_Female_FullBody.Superhero_Female_FullBody'

def FOLK(body, outfit, z=0.0, scale=1.0):
    return {'body': body, 'outfit': UNI_PEOPLE + outfit + '.' + outfit,
            'z': z, 'scale': scale}

# The armed trades wear the ranger's hood; everyone else is in peasant cloth.
# Men and women are alternated so a market is a market.
KEEPER_FOLK = {
  'banker':     FOLK(MALE,   'Male_Peasant'),
  'merchant':   FOLK(FEMALE, 'Female_Peasant'),
  'beekeeper':  FOLK(MALE,   'Male_Peasant'),
  'brewer':     FOLK(FEMALE, 'Female_Peasant'),
  'collier':    FOLK(MALE,   'Male_Peasant'),
  'drover':     FOLK(MALE,   'Male_Peasant'),
  'innkeeper':  FOLK(FEMALE, 'Female_Peasant'),
  'miller':     FOLK(MALE,   'Male_Peasant'),
  'shepherd':   FOLK(FEMALE, 'Female_Peasant'),
  'sawyer':     FOLK(MALE,   'Male_Peasant'),
  'quarrier':   FOLK(MALE,   'Male_Peasant'),
  'delver':     FOLK(MALE,   'Male_Peasant'),
  'fisher':     FOLK(FEMALE, 'Female_Peasant'),
  'seed':       FOLK(FEMALE, 'Female_Peasant'),
  'lumber':     FOLK(MALE,   'Male_Peasant'),
  'toll':       FOLK(MALE,   'Male_Ranger'),
  'watchman':   FOLK(MALE,   'Male_Ranger'),
  'arms':       FOLK(MALE,   'Male_Ranger'),
  'armour':     FOLK(MALE,   'Male_Ranger'),
  'bows':       FOLK(FEMALE, 'Female_Ranger'),
  'mourner':    FOLK(FEMALE, 'Female_Ranger'),
  'wizard':     FOLK(MALE,   'Male_Ranger'),
  'delve':      FOLK(MALE,   'Male_Peasant'),
}

# ---------------------------------------------------------------------------
# AND THE REST OF WHAT STANDS ABOUT.
#
# Everything here is a word the world uses that was being drawn as a scaled
# primitive and for which one of the two CC0 kits has the actual object. Where
# neither kit has the thing, the word is LEFT as it was: a cube that claims
# nothing is a better answer than a barrel pretending to be a beehive.
#
# The ore nodes are the ones worth having. There are eight words for a rock you
# can mine in this world and every one of them was a cone.
NATURE_PROPS = {
  # --- rock, which the nature kit does properly ---
  'iron-rock':        ('Rock_Medium_1',  1.00),
  'coal-rock':        ('Rock_Medium_2',  0.95),
  'gold-rock':        ('Rock_Medium_3',  0.95),
  'quick-rock':       ('Rock_Medium_1',  0.90),
  'mother-lode':      ('Rock_Medium_2',  1.40),
  'rockfall':         ('Rock_Medium_3',  1.20),
  'salt-pan':         ('Rock_Medium_1',  0.70),
  'brimstone-vent':   ('Rock_Medium_2',  0.80),
  # ---- A STANDING STONE STANDS. IT IS NOT A BOULDER ----
  #
  # `Rock_Medium_3` is 342 by 348 by 232 centimetres, so at the 1.30 written
  # here a standing stone came out four and a half metres across and three
  # high: a glacial erratic sitting in a meadow, which is what was reported as
  # "what's this big ass boulder doing here, wrong scale small rock?". The
  # sentinel at 1.80 was six metres of the same boulder.
  #
  # What makes a standing stone a standing stone is that it is TALL and THIN
  # and somebody stood it up. `PARTS` has both already -- 55 by 38 by 220 for
  # the stone, 72 by 50 by 310 for the sentinel -- and this table was hiding
  # them. The Nature kit has no pillar in it: three boulders and a path, so
  # there is nothing here to swap to and nothing to swap for.
  #
  # The fifth time this pattern has turned up today, after the log pile, the
  # withy stack, the web, the skep and the anvil: a kit mesh chosen on the
  # strength of its name, overriding geometry that was already right.
  'landmark.fallen-stone':   ('Rock_Medium_1', 1.10),
  'landmark.glass-stone':    ('Rock_Medium_2', 0.80),
  'landmark.cut-face':       ('Rock_Medium_1', 1.30),
  'landmark.cave-mouth':     ('Rock_Medium_2', 1.60),
  'landmark.salt-lick':      ('Rock_Medium_1', 0.55),
  'landmark.stone-heap':     ('Rock_Medium_3', 0.85),
  'landmark.ore-heap':       ('Rock_Medium_1', 0.75),
  'landmark.spoil-heap':     ('Rock_Medium_2', 0.90),
  'landmark.slag-lump':      ('Rock_Medium_3', 0.60),
  'landmark.cairn':          ('Rock_Medium_1', 0.95),
  # 'landmark.rubble-heap' IS NOT HERE. It was a boulder, and the Ruins pack
  # has an actual heap of broken masonry -- see VILLAGE above, which owns the
  # word now. A rock is a rock; rubble is what a wall becomes.
  # --- and a hedge is a hedge ---
  'hedge':            ('Bush_Common',    0.85),
  'landmark.topiary': ('Bush_Common',    1.05),
  # A reed bed is tall wispy grass, and the kit has tall wispy grass. It was a
  # green cone, which is what the user saw and called a green dot.
  # 2.4 m. THIS is the row that wins -- there are three tables in this file
  # with an opinion about reeds and only this one is keyed `landmark.reeds`,
  # which is what the generator seats. At 2.40 it drew FOUR METRES of reed,
  # taller than the cottage behind it and twice the tallest reed there is.
  'landmark.reeds':   ('Grass_Wispy_Tall', 1.44),   # 2.4 m; was 2.40, drawn at 4.0
}

PROP_PROPS = {
  'hoard':                ('Coin_Pile_2',      1.00),
  'store':                ('Crate_Wooden',     1.00),
  'vault':                ('Crate_Metal',      1.00),
  # 'stall' IS NOT HERE ANY MORE, on purpose. The Medieval Village pack has a
  # real market stand -- a trestle with a striped awning over it -- and the
  # word now has ONE owner, `STALL_MESH`, applied in apply.py. Left in both
  # tables, this one ran later and silently won; the comment further up this
  # file about "two tables both thinking they own a word" is about exactly
  # this word, and it happened again.
  'smokerack':            ('Peg_Rack',         1.00),
  'sawpit':               ('Workbench_Drawers', 1.00),
  'smith':                ('Anvil_Log',        1.00),
  'stamp':                ('Anvil_Log',        0.85),
  # 'plot' and 'landmark.flowerbed' ARE NOT HERE any more -- see SOWN below.
  # A plot was drawn as a CRATE OF CARROTS, so a field of them read as a
  # scattering of boxes dropped in the grass, and it was asked about on sight:
  # "what are those things?" A plot is a patch of tilled earth that a citizen
  # sows and harvests; the crop is the point and the crate was never in it.
  'landmark.eel-rack':    ('Peg_Rack',         1.00),
  'landmark.fish-trap':   ('Cage_Small',       1.00),
  'landmark.hay-wain':    ('Stall_Cart_Empty', 1.05),
  'landmark.sawhorse':    ('Workbench',        0.90),
  # 'landmark.ladder' IS NOT HERE. It drew a ladder as `Peg_Rack` -- 1.18 m,
  # which is shorter than the citizen climbing it. A ladder reaches a roof, and
  # `PARTS` has one: 2.4 m with rungs.
  # --- AND WHERE THE KIT HAS THE ACTUAL THING, IT TAKES THE ACTUAL THING ---
  #
  # These eight were assembled out of engine primitives -- a barrel was a
  # drum, a bed was a box with a smaller box on it -- back when there was no
  # furniture in the project. There is now. A composed landmark is still the
  # right answer for a cairn or a scarecrow, which no kit ships; it is the
  # wrong answer for a barrel.
  'landmark.barrel':      ('Barrel',            1.00),
  'landmark.bench':       ('Bench',             1.00),
  'landmark.bed':         ('Bed_Twin1',         1.00),
  'landmark.table':       ('Table_Large',       1.00),
  'landmark.trestle':     ('Table_Large',       0.92),
  'landmark.shelf':       ('Shelf_Simple',      1.00),
  'landmark.cart':        ('Stall_Cart_Empty',  1.00),
  'landmark.broken-cart': ('Stall_Cart_Empty',  0.92),
}

# Every stall of a trade is the same trestle; what differs is who stands at it
# and what is laid out on it. The trestle itself comes from `STALL_MESH` now --
# see the note where `stall` used to sit in the table above.

# ---------------------------------------------------------------------------
# AND WHICH OF THE FIVE IT IS.
#
# The kit ships five common trees, five pines, five twisted and five dead. A
# word that names one of them makes a wood out of one tree repeated; a word
# that names all five makes a wood. The node's own id chooses, so the crooked
# oak at the ford is the same crooked oak in every window and tomorrow.
#
# Only the species with real variety are listed. An apple tree and a pear tree
# are the same common-tree mesh at different sizes and always will be, and
# saying so five times would not change that.
VARIETY = {
  'tree':           ['CommonTree_1', 'CommonTree_2', 'CommonTree_3', 'CommonTree_4', 'CommonTree_5'],
  'oak-tree':       ['CommonTree_3', 'CommonTree_4', 'CommonTree_5'],
  'old-oak':        ['CommonTree_3', 'CommonTree_4', 'CommonTree_5'],
  'old-oak-lm':     ['CommonTree_3', 'CommonTree_4', 'CommonTree_5'],
  'avenue-oak':     ['CommonTree_1', 'CommonTree_5', 'CommonTree_2'],
  'pine':           ['Pine_1', 'Pine_2', 'Pine_3', 'Pine_4', 'Pine_5'],
  'yew':            ['Pine_3', 'Pine_4', 'Pine_5'],
  'ironbark-tree':  ['TwistedTree_1', 'TwistedTree_2', 'TwistedTree_3'],
  'heartwood-tree': ['CommonTree_4', 'CommonTree_3'],
  # A WILLOW IS NOT RED. The twisted trees carry the kit's autumn sheet --
  # measured at (167,23,23), genuinely red and right for a thorn -- and giving
  # it to the willows as well put a belt of scarlet along every watercourse.
  'willow':         ['CommonTree_2', 'CommonTree_1', 'CommonTree_5'],
  'thorn':          ['TwistedTree_4', 'TwistedTree_3', 'TwistedTree_1'],
  'wind-thorn':     ['TwistedTree_5', 'TwistedTree_4'],
  'rag-tree':       ['TwistedTree_3', 'TwistedTree_1'],
  'dead-tree':      ['DeadTree_1', 'DeadTree_2', 'DeadTree_3', 'DeadTree_4', 'DeadTree_5'],
  'burnt-tree':     ['DeadTree_4', 'DeadTree_5', 'DeadTree_3'],
  'gallows-oak':    ['CommonTree_5', 'CommonTree_3'],
}


# §11d: THE RUNNER'S LOAD.
#
# A consignment empties the pack into a container, and until this existed the
# window drew a hauler carrying five slots of goods exactly like somebody
# carrying nothing. It is the one state that makes a citizen lawfully
# strikeable by anybody, so it is the LAST thing that should be invisible.
#
# Deliberately a bundle on the back and not a cart or a mount. The world has
# neither: `cart` is a node type for what a dead hauler SPILLS, and the
# constitution names the trade RUNNER rather than carter precisely because the
# load is carried on foot and at risk. Drawing a vehicle here would quietly
# contradict the rule the window is supposed to be showing.
#
# Hung off spine_03 at a positive X, which on this skeleton is BEHIND the
# citizen -- the same lesson the hatchet taught at the hand bone, where a
# positive offset put the blade over the shoulder instead of in the fist.
# AND THE CRATES ARE REAL CRATES NOW. The Medieval Village pack has `Package_1`
# and `Package_2` -- a bound bundle and a roped box -- which is what a load is,
# and they were two scaled cubes until the packs arrived.
HAUL_LOAD = kit(
    WEAR(VIL('Package_1'), None, 'spine_03', 1.5, 1.5, 1.5,
         ox=16.0, oz=2.0, pitch=6.0),
    WEAR(VIL('Package_2'), None, 'spine_03', 1.1, 1.1, 1.1,
         ox=20.0, oz=22.0, pitch=-8.0, yaw=12.0),
    # The cord over the shoulders, which is what makes it read as carried
    # rather than as a box floating behind a person.
    WEAR(CUBE, CLOTH, 'spine_03',
         0.05, 0.30, 0.05, ox=4.0, oz=16.0, pitch=28.0),
)
WORN['haul'] = HAUL_LOAD
