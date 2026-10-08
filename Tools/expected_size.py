#!/usr/bin/env python3
"""HOW BIG EACH THING IS SUPPOSED TO BE, in metres, as a claim rather than a feeling.

WHY. `audit_size.py` could say how big a thing IS. It could not say whether
that was right, so the only test was somebody looking at it -- and looking is
unreliable in a way this project has now paid for several times. A giant spider
eight and a third metres across stood in the Greenwood for weeks. A market
stall sold a bow five and a half metres long in every town on the island. A
sawpit was a forty-two centimetre workbench. None of them was hidden; all of
them were simply never measured against anything.

A range, not a number, because a prop legitimately varies: a cart is between
two and four metres depending on the cart. The range is what a reasonable
person would accept if they walked up to the thing with a tape. If a measured
size falls outside it, either the art is wrong or this file is, and both are
worth knowing.

THE LONGEST DIMENSION is what is compared, because that is what reads first and
what goes wrong: the spider was wrong across, the banner was wrong up.

UNDECLARED WORDS ARE REPORTED, not ignored. A word with no row here is one
nobody has yet said anything about, and the audit prints how many there are so
the gap is visible and shrinks rather than being quietly tolerated.
"""

# word -> (least, most) in metres, of the thing's longest dimension
EXPECT = {
    # ---- the island's few big things ----
    'bellwork':                 (6.0, 12.0),   # a bell tower
    'landmark.mill':            (6.0, 12.0),   # a windmill, sails and all
    'landmark.shipwreck':       (4.0, 12.0),
    'watchfire':                (2.5, 6.0),    # a beacon on a pole
    'landmark.siege-engine':    (3.0, 6.0),

    # ---- trees. A full oak is a big thing and is allowed to be ----
    'tree':                     (3.0, 9.0),
    'oak-tree':                 (5.0, 11.0),
    'landmark.old-oak':         (5.0, 11.0),
    'landmark.old-oak-lm':      (5.0, 11.0),
    'heartwood-tree':           (5.0, 11.0),
    'ironbark-tree':            (5.0, 11.0),
    'gallows-oak':              (4.0, 9.0),
    'landmark.avenue-oak':      (4.0, 9.0),
    'landmark.pine':            (4.0, 9.0),
    'landmark.yew':             (3.0, 8.0),
    'landmark.willow':          (3.0, 9.0),
    'landmark.dead-tree':       (3.0, 8.0),
    'landmark.burnt-tree':      (3.0, 8.0),
    'landmark.thorn':           (2.0, 7.0),
    'landmark.wind-thorn':      (2.0, 7.0),
    'landmark.rag-tree':        (2.0, 7.0),
    'landmark.apple-tree':      (2.5, 6.0),
    'landmark.pear-tree':       (2.5, 6.0),
    'landmark.elder-tree':      (2.0, 5.0),
    'landmark.topiary':         (0.8, 2.5),
    'hedge':                    (1.0, 3.0),
    'landmark.reeds':           (1.0, 3.0),
    'landmark.stump':           (0.3, 1.0),
    'landmark.windfall':        (1.5, 5.0),

    # ---- rock, which is bedded in and allowed to be lumpy ----
    'rockfall':                 (1.5, 5.0),
    'landmark.cut-face':        (2.0, 6.0),
    'landmark.fallen-stone':    (1.5, 5.0),
    'landmark.cairn':           (0.8, 3.5),
    'landmark.stone-heap':      (1.0, 3.5),
    'landmark.spoil-heap':      (1.0, 3.5),
    'landmark.ore-heap':        (1.0, 3.0),
    'landmark.slag-lump':       (0.5, 2.5),
    'landmark.rubble-heap':     (0.8, 3.0),
    'landmark.glass-stone':     (0.8, 3.0),
    'landmark.salt-lick':       (0.4, 2.0),
    'mother-lode':              (1.5, 5.0),
    'gold-rock':                (1.0, 4.0),
    'iron-rock':                (1.0, 4.0),
    'quick-rock':               (1.0, 4.0),
    'coal-rock':                (1.0, 4.0),
    'brimstone-vent':           (1.0, 3.5),
    'landmark.cave-mouth':      (2.0, 6.0),
    # Stood up by people, so TALL AND THIN and person-scale, not boulders.
    'landmark.standing-stone':  (1.5, 3.5),
    'landmark.sentinel':        (2.0, 4.5),
    'landmark.bridge-stone':    (0.5, 1.6),
    'landmark.milestone':       (0.5, 1.5),
    'landmark.way-post':        (0.8, 2.5),
    'landmark.tally-post':      (0.8, 2.5),
    'landmark.tally-half':      (0.6, 2.0),
    'landmark.grave':           (0.4, 1.5),
    'landmark.daub-mark':       (0.3, 1.2),
    'landmark.dew-mark':        (0.2, 1.0),
    'landmark.shot-hole':       (0.4, 1.5),

    # ---- a person is 1.8 m, and everything they handle is read against that --
    'signpost':                 (1.6, 2.6),    # a post you read at eye height
    'landmark.scarecrow':       (1.4, 2.4),
    'landmark.gibbet':          (2.5, 4.5),
    'gibbet-shoal':             (2.0, 4.5),
    'ossuary':                  (1.8, 3.5),
    'dedication':               (1.2, 2.5),
    'landmark.broken-tower':    (2.0, 6.0),
    'landmark.window-arch':     (2.0, 5.0),
    'landmark.gazebo-post':     (2.0, 4.0),
    'landmark.scaffold':        (1.5, 4.0),
    'landmark.ladder':          (2.0, 4.5),    # a ladder reaches a roof
    'landmark.half-wall':       (1.0, 3.0),
    'landmark.sunken-wall':     (1.0, 3.5),
    'wall':                     (1.0, 3.5),
    'fence':                    (1.2, 3.0),
    'railing':                  (1.2, 3.0),
    'landmark.hurdle':          (1.0, 2.5),
    'landmark.sheep-hurdle':    (1.0, 2.5),
    'landmark.barricade':       (1.0, 3.0),
    'tollgate':                 (1.5, 3.5),

    # ---- the trades, and what stands at them ----
    'anvil':                    (0.6, 1.4),
    'smith':                    (0.6, 1.6),
    'stamp':                    (0.5, 1.4),
    'furnace':                  (1.2, 3.0),    # a bloomery, not a chimney
    'brewpot':                  (0.6, 1.6),
    'hearth':                   (0.6, 2.0),
    'landmark.crude-hearth':    (0.5, 1.6),
    'campfire':                 (0.8, 2.2),
    'sawpit':                   (1.2, 3.0),
    'smokerack':                (1.0, 2.5),
    'landmark.eel-rack':        (0.8, 2.2),
    'landmark.chopping-block':  (0.4, 1.2),
    'landmark.sawhorse':        (1.0, 2.2),
    'landmark.trestle':         (1.2, 3.0),
    'landmark.table':           (1.2, 3.2),
    'landmark.bench':           (1.2, 3.0),
    'landmark.bed':             (1.6, 2.6),
    'landmark.shelf':           (0.6, 2.0),
    'store':                    (0.5, 1.6),
    'vault':                    (0.5, 1.6),
    'hoard':                    (0.1, 0.8),
    'well':                     (1.0, 3.0),
    'fountain':                 (1.2, 3.5),
    'landmark.birdbath':        (0.5, 1.5),
    'looking-glass':            (0.8, 2.2),
    'landmark.drowned-bell':    (0.6, 2.2),

    # ---- the market ----
    'stall.armour':             (1.6, 3.2),
    'stall.arms':               (1.6, 3.2),
    'stall.bows':               (1.6, 3.2),
    'stall.delve':              (1.6, 3.2),
    'stall.fisher':             (1.6, 3.2),
    'stall.lumber':             (1.6, 3.2),
    'stall.seed':               (1.6, 3.2),

    # ---- carts, boats and what is carried ----
    'landmark.cart':            (1.8, 4.0),
    'landmark.broken-cart':     (1.8, 4.0),
    'landmark.hay-wain':        (2.0, 4.5),
    'ferry':                    (2.5, 5.5),
    'landmark.upturned-boat':   (2.0, 5.0),
    'landmark.staithe':         (1.5, 4.0),
    'landmark.barrel':          (0.5, 1.3),
    'landmark.fish-trap':       (0.4, 1.4),
    'landmark.log-pile':        (1.0, 2.6),
    'landmark.withy-stack':     (0.6, 2.0),
    'landmark.haystack':        (1.0, 3.0),
    'landmark.peat-stack':      (0.6, 2.0),
    'landmark.turf-stack':      (0.4, 1.6),
    'landmark.charcoal-clamp':  (1.0, 3.0),
    'landmark.charcoal-ring':   (0.8, 2.6),
    'landmark.ash-heap':        (0.6, 2.2),
    'muck-heap':                (0.6, 2.6),
    'landmark.wood-chips':      (0.4, 1.8),
    'landmark.skep':            (0.3, 1.0),

    # ---- the field ----
    'plot':                     (1.5, 4.5),
    'grove-plot':               (1.0, 3.0),
    'landmark.flowerbed':       (1.5, 4.5),
    'landmark.wheel-rut':       (1.0, 2.6),
    'landmark.peat-cut':        (1.0, 3.0),
    'landmark.scorched-ring':   (0.8, 2.6),
    'salt-pan':                 (1.0, 3.5),
    'landmark.dew-pond':        (1.0, 3.5),
    'landmark.bog-pool':        (1.0, 3.5),
    'landmark.wellspring':      (0.4, 1.6),

    # ---- the dead and the uncanny ----
    'landmark.bone-pile':       (0.5, 2.0),
    'landmark.skull-pile':      (0.4, 1.6),
    'landmark.sheep-skull':     (0.1, 0.6),
    'landmark.web':             (1.0, 3.0),
    'landmark.wool-snag':       (0.5, 2.2),

    # ---- the spots a citizen works, which are marks on the ground ----
    'fishing-spot':             (0.4, 1.6),
    'eel-spot':                 (0.4, 1.6),
    'deep-fish-spot':           (0.4, 1.6),

    # ---- and the banner, which was five feet underground ----
    'banner':                   (1.5, 3.5),
}
