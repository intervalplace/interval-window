# THE THREE STONES, which were boxes.
#
#   blender --background --python Tools/blend/stones.py
#
# WHAT THEY WERE. `Tools/audit.py` reports which rows in parts.py are still an
# engine primitive, and `whodraws.py --dead` says which of those actually
# reach the screen. Three did, with no parts under them at all:
#
#   standing-stone   a Cube, 55 x 38 x 220 cm, in rock
#   sentinel         a Cube, 72 x 50 x 310 cm, in rock
#   bridge-stone     a Cube, 42 x 36 x 95 cm, in stone
#
# A two-metre grey box standing by itself in a meadow is the most visible
# unfinished thing in this world, and the sentinel is a metre taller again.
# The other seven the audit names are composed out of sticks -- a ladder is
# two stiles and four rungs, a scaffold is poles, a withy stack is a cone and
# nine leaning rods -- and a ladder really is made of sticks, so those are
# left alone. These three are not made of boxes.
#
# WHY HERE AND NOT IN forge.py. `Tools/blend/README.md` draws the line: hard
# surfaces whose shape is a few numbers stay in the forge, and anything with
# an organic silhouette comes here. A split stone is the organic case -- what
# makes it read as stone rather than as masonry is that no two faces agree,
# and forge.py has no mirror, no boolean and no way to jitter a ring.
#
# AND THEY DO NOT COME TO A POINT. The first cut tapered to 0.62 of the base
# and lifted the crown by up to 7% of the height, and both tall stones read as
# OBELISKS: a pencil standing in a field, which is a monument somebody dressed
# rather than a block somebody stood on end. A menhir keeps most of its width
# all the way up and is blunt across the top. The taper is 0.82 and 0.86 now
# and the crown is barely proud of the last ring.
#
# THE SHAPE IS A TAPERED PRISM WITH EVERY VERTEX NUDGED, which is the whole
# trick and it is one loop. Rings of points from the base to the crown, the
# radius falling as it rises, each point pushed in or out and up or down by a
# little. Faceted, never smoothed: the flat faces catching light at different
# angles ARE the weathering, and a smoothed version of this reads as a
# beanbag.
#
# DETERMINISTIC. A fixed seed per stone, so the mesh is the same every time
# the script runs. The script is the asset and a rebuilt asset that differs
# from the one in the repository is not one.
#
# TWO MATERIALS, both already in `forge.PALETTE`: `Rock` for the body and
# `RockDark` for the foot. A stone is damp and lichened where it meets the
# ground and the band is what gives it a bottom at fifty metres, where the
# whole thing is twenty pixels tall and the silhouette is all there is.
import bpy
import bmesh
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'interval', 'Art', 'Forged')
if not os.path.isdir(OUT):
    OUT = os.path.abspath(os.path.join(HERE, '..', '..', 'Art', 'Forged'))

# name -> (tall cm, base across cm, seed, taper, lean cm, foot fraction)
#
# TALL IS THE NUMBER THE ROW ALREADY CHOSE, so the stone that appears is the
# size the world has always placed. Across is the wider of the two footprint
# numbers; the narrower one falls out of the squash below, because a standing
# stone is a slab and not a pillar.
STONES = {
    # A monolith somebody stood on end. Tapers hard, leans a little: a stone
    # that has been upright for a thousand years is never quite plumb, and the
    # lean is the difference between a menhir and a bollard.
    'standing_stone': dict(tall=220.0, across=55.0, squash=0.69, seed=701,
                           taper=0.82, lean=7.0, foot=0.16),
    # Taller and squarer on its feet, and barely leaning. The name is the
    # brief: this one is a watcher, so it stands rather than slouches.
    'sentinel':       dict(tall=310.0, across=72.0, squash=0.70, seed=702,
                           taper=0.86, lean=3.0, foot=0.13),
    # Squat, and worn on top because it is walked on. The least tapered of the
    # three: it is a block at a crossing, not a thing raised to be looked at.
    'bridge_stone':   dict(tall=95.0, across=42.0, squash=0.86, seed=703,
                           taper=0.88, lean=0.0, foot=0.22),
}

SIDES = 9        # odd, so the silhouette never shows two parallel faces
RINGS = 7        # base to crown


def stone(name, tall, across, squash, seed, taper, lean, foot):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rnd = random.Random(seed)
    bm = bmesh.new()

    half = across * 0.5
    rings = []
    for i in range(RINGS + 1):
        u = i / RINGS
        z = u * tall
        # ---- THE RADIUS FALLS AS IT RISES, WITH A WAIST ----
        #
        # A straight taper is a traffic cone. The sine term pinches it a third
        # of the way up and lets it swell again, which is what a split block
        # of rock actually does and is the only line here that is about
        # character rather than arithmetic.
        r = half * (1.0 - (1.0 - taper) * u) * (1.0 + 0.09 * math.sin(u * 3.4))
        ring = []
        for k in range(SIDES):
            ang = 2.0 * math.pi * k / SIDES
            # every vertex nudged: out or in, and up or down
            jr = r * (1.0 + rnd.uniform(-0.17, 0.17))
            jz = z + rnd.uniform(-0.035, 0.035) * tall / RINGS
            x = math.cos(ang) * jr + lean * u
            y = math.sin(ang) * jr * squash
            ring.append(bm.verts.new((x, y, jz)))
        rings.append(ring)

    # the body
    for i in range(RINGS):
        for k in range(SIDES):
            a, b = rings[i][k], rings[i][(k + 1) % SIDES]
            c, d = rings[i + 1][(k + 1) % SIDES], rings[i + 1][k]
            f = bm.faces.new((a, b, c, d))
            # ---- THE FOOT IS THE SECOND MATERIAL ----
            f.material_index = 1 if (i / RINGS) < foot else 0

    # ---- THE CROWN IS NOT FLAT ----
    #
    # Capping the top ring with one polygon gives a stone that looks sawn. A
    # single vertex lifted off-centre above it makes a crown with a fall to
    # it, which is what weather does to the top of anything left outside.
    tx = sum(v.co.x for v in rings[-1]) / SIDES + rnd.uniform(-0.1, 0.1) * half
    ty = sum(v.co.y for v in rings[-1]) / SIDES + rnd.uniform(-0.1, 0.1) * half
    tz = tall + rnd.uniform(0.01, 0.025) * tall
    top = bm.verts.new((tx, ty, tz))
    for k in range(SIDES):
        f = bm.faces.new((rings[-1][k], rings[-1][(k + 1) % SIDES], top))
        f.material_index = 0
    # and the underside, closed so the mesh is solid if anything ever looks up
    f = bm.faces.new(rings[0][::-1])
    f.material_index = 1

    bm.verts.index_update()
    bm.normal_update()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)

    # FACETED, DELIBERATELY. See the note at the top: the flat faces are the
    # weathering, and smoothing this makes a beanbag.
    for p in ob.data.polygons:
        p.use_smooth = False

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0))
    bpy.ops.object.mode_set(mode='OBJECT')

    # NAMED FROM forge.PALETTE, in this order, or dress_forged.py binds
    # nothing and the stone arrives grey in the engine's sense of grey.
    for mat in ('Rock', 'RockDark'):
        ob.data.materials.append(bpy.data.materials.new(mat))

    path = os.path.join(OUT, name + '.obj')
    bpy.ops.wm.obj_export(filepath=path, export_selected_objects=False,
                          export_materials=True, export_uv=True,
                          export_normals=True, export_triangulated_mesh=False,
                          forward_axis='Y', up_axis='Z')

    lo = [1e9] * 3
    hi = [-1e9] * 3
    for line in open(path):
        if line.startswith('v '):
            q = [float(v) for v in line.split()[1:4]]
            for i in range(3):
                lo[i] = min(lo[i], q[i])
                hi[i] = max(hi[i], q[i])
    got = hi[2] - lo[2]
    print('%-16s %4d verts %4d faces  %.0f tall x %.0f x %.0f cm'
          % (name, len(ob.data.vertices), len(ob.data.polygons),
             got, hi[0] - lo[0], hi[1] - lo[1]))
    # MEASURED AGAINST THE NUMBER THE ROW ALREADY USED, because the whole
    # point is that the stone that appears is the size the world placed.
    if abs(got - tall) > tall * 0.12:
        print('   HEIGHT IS %.0f AND THE ROW ASKS FOR %.0f' % (got, tall))


def main():
    print('--- stones')
    for name, kw in STONES.items():
        stone(name, **kw)
    print('--- done')


main()
