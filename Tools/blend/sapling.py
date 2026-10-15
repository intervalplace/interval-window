# A SAPLING, which the world has always handed out and never drawn.
#
#   blender --background --python Tools/blend/sapling.py
#
# WHY IT WAS MISSING FOR SO LONG. Felling a GROWN grove reverts the plot and
# gives the feller a sapling, so that the ring can be started again: the
# engine's own note says "felling produces the means to replant, so a bald
# ring is a thing people chose rather than a thing that merely happened". It
# is priced at 40 and planting consumes one. It had no mesh, no icon and no
# row anywhere in the art, because it was not in `ITEMS` either -- see §6bf --
# and every tool in this project takes its list of things from there. The
# handbook printed a sapling with an empty space where its picture goes, which
# is what finally pointed at it.
#
# MEASURED. A nursery whip -- a one-year tree lifted bare-root for planting --
# is 60 to 90 cm with a stem under a centimetre and a half thick, which is
# exactly what a citizen would be carrying. 70 cm, and a citizen is 181.
#
# THE STEM IS DRAWN THICKER THAN IT IS, and that is deliberate rather than a
# measuring error. At a true 7mm across it rendered as a wire: a dark hairline
# with leaves apparently floating beside it, which is not what the rest of
# this world looks like. The kit everything here is matched to builds in
# chunky facets, and the stem is about 23mm across so that it still reads as
# wood at the size anybody sees it. The height, which is the number a player
# can compare against their own citizen, is the real one.
#
# IT IS A WHIP WITH ROOTS, AND THE ROOTS ARE THE WHOLE POINT. A stem with
# leaves on it is a stick with leaves on it, and at the size this is drawn the
# difference between a sapling and a branch somebody picked up is whether it
# has a root system hanging off the bottom. That is the silhouette that says
# "this is to be planted" without a word, and it is the same argument leaf.py
# makes about a leaf's curl: one feature, chosen because it is the one that
# reads.
#
# NO SOIL ON THEM. The forge palette has no earth in it -- fifty-three
# entries and the nearest is an iron ore -- and inventing a colour here would
# put a fifty-fourth in one file that `dress_forged.py` would then have to
# find. Bare-root is also what a nursery whip actually is, so the roots are
# `Bark` like the stem and nothing is pretending.
#
# TWO MATERIALS, both already in the palette: `Bark` for the wood and `Herb`
# for the leaves, which is the one real green there is.
import bpy
import bmesh
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'interval', 'Art', 'Forged')
if not os.path.isdir(OUT):
    OUT = os.path.abspath(os.path.join(HERE, '..', '..', 'Art', 'Forged'))

TALL = 70.0          # cm, the whole thing including the roots below the collar
STEM = 56.0          # cm of stem above the root collar
BASE_R = 1.15        # cm, stem radius at the collar
TIP_R = 0.34         # cm, at the growing tip
ROOTS = 5
ROOT_LEN = 15.0
LEAVES = 9
SIDES = 7            # around the stem: odd, so no two faces are coplanar pairs


def tube(bm, pts, radii, mat):
    """A tapered tube through a polyline, capped at both ends."""
    rings = []
    for i, (p, r) in enumerate(zip(pts, radii)):
        # the direction the tube is running at this point
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        d = [b[j] - a[j] for j in range(3)]
        n = math.sqrt(sum(v * v for v in d)) or 1.0
        d = [v / n for v in d]
        # any two vectors across it; the stem is near-vertical so X is safe
        up = (1.0, 0.0, 0.0) if abs(d[2]) > 0.9 else (0.0, 0.0, 1.0)
        s = (up[1] * d[2] - up[2] * d[1], up[2] * d[0] - up[0] * d[2],
             up[0] * d[1] - up[1] * d[0])
        sn = math.sqrt(sum(v * v for v in s)) or 1.0
        s = [v / sn for v in s]
        t = (d[1] * s[2] - d[2] * s[1], d[2] * s[0] - d[0] * s[2],
             d[0] * s[1] - d[1] * s[0])
        ring = []
        for k in range(SIDES):
            ang = 2.0 * math.pi * k / SIDES
            c, si = math.cos(ang) * r, math.sin(ang) * r
            ring.append(bm.verts.new((p[0] + s[0] * c + t[0] * si,
                                      p[1] + s[1] * c + t[1] * si,
                                      p[2] + s[2] * c + t[2] * si)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(SIDES):
            f = bm.faces.new((rings[i][k], rings[i][(k + 1) % SIDES],
                              rings[i + 1][(k + 1) % SIDES], rings[i + 1][k]))
            f.material_index = mat
    for ring, flip in ((rings[0], True), (rings[-1], False)):
        f = bm.faces.new(ring[::-1] if flip else ring)
        f.material_index = mat


def blade(bm, at, along, side, length, width, mat):
    """One simple leaf: rows across a midrib, as leaf.py argues for."""
    N = 4
    rows = []
    for i in range(N + 1):
        u = i / N
        # widest a third of the way out, tapering to a point
        w = width * math.sin(math.pi * min(u * 1.15, 1.0)) ** 0.7
        mid = [at[j] + along[j] * length * u for j in range(3)]
        # a fold along the midrib, so a leaf is never a flat sticker
        lift = [0.0, 0.0, w * 0.22]
        rows.append((
            bm.verts.new(tuple(mid[j] - side[j] * w + lift[j] for j in range(3))),
            bm.verts.new(tuple(mid[j] for j in range(3))),
            bm.verts.new(tuple(mid[j] + side[j] * w + lift[j] for j in range(3))),
        ))
    for i in range(N):
        for a, b in ((0, 1), (1, 2)):
            f = bm.faces.new((rows[i][a], rows[i][b], rows[i + 1][b], rows[i + 1][a]))
            f.material_index = mat


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bm = bmesh.new()

    # ---- THE STEM ----
    #
    # A whip leans. A dead straight stem reads as a dowel, and the lean is two
    # numbers rather than a curve anybody has to tune.
    pts, radii = [], []
    N = 7
    for i in range(N + 1):
        u = i / N
        z = u * STEM
        pts.append((math.sin(u * 1.5) * 2.2, 0.0, z))
        radii.append(BASE_R + (TIP_R - BASE_R) * u)
    tube(bm, pts, radii, 0)

    # ---- THE ROOTS ----
    #
    # Splayed down and out from the collar, each one tapering to nothing. Five
    # is enough to read as a root system and few enough to stay countable at
    # the size this is drawn.
    for i in range(ROOTS):
        ang = 2.0 * math.pi * i / ROOTS + 0.3
        dx, dy = math.cos(ang), math.sin(ang)
        rp, rr = [], []
        M = 3
        for j in range(M + 1):
            u = j / M
            # out and down, curling under as it goes
            rp.append((dx * ROOT_LEN * u * 0.72,
                       dy * ROOT_LEN * u * 0.72,
                       -ROOT_LEN * (u ** 1.5) * 0.95))
            rr.append(BASE_R * 0.62 * (1.0 - u) + 0.05)
        tube(bm, rp, rr, 0)

    # ---- THE LEAVES ----
    #
    # On the top half only, which is where a whip's leaves are: the lower buds
    # have not broken. Alternating round the stem rather than opposite, which
    # is the oak's habit and is also what stops them reading as a ladder.
    for i in range(LEAVES):
        u = 0.46 + 0.52 * (i / max(LEAVES - 1, 1))
        z = u * STEM
        lean = math.sin(u * 1.5) * 2.2
        ang = i * 2.39996        # the golden angle, which is what a stem does
        dx, dy = math.cos(ang), math.sin(ang)
        # out from the stem and tilted up a little
        along = (dx * 0.93, dy * 0.93, 0.36)
        n = math.sqrt(sum(v * v for v in along))
        along = tuple(v / n for v in along)
        side = (-dy, dx, 0.0)
        blade(bm, (lean + dx * BASE_R * 0.8, dy * BASE_R * 0.8, z),
              along, side, 9.2, 3.4, 1)

    bm.verts.index_update()
    me = bpy.data.meshes.new('sapling')
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new('sapling', me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)

    # A LEAF HAS TWO SIDES AND BOTH ARE SEEN, the argument leaf.py makes.
    sol = ob.modifiers.new('thick', 'SOLIDIFY')
    sol.thickness = 0.05
    sol.use_rim = True
    bpy.ops.object.modifier_apply(modifier=sol.name)

    for p in ob.data.polygons:
        p.use_smooth = True
    sharp = ob.modifiers.new('sharp', 'EDGE_SPLIT')
    sharp.split_angle = math.radians(44.0)
    bpy.ops.object.modifier_apply(modifier=sharp.name)

    # UVs OR THE IMPORTER THROWS. See the README: the OBJ out of forge.py
    # carries none and that is what broke the bird.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0))
    bpy.ops.object.mode_set(mode='OBJECT')

    # NAMED FROM `forge.PALETTE`, or dress_forged.py binds nothing and the
    # whole thing arrives grey.
    for name in ('Bark', 'Herb'):
        ob.data.materials.append(bpy.data.materials.new(name))

    path = os.path.join(OUT, 'sapling.obj')
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
    tall = hi[2] - lo[2]
    print('SAPLING %d verts %d faces  %.1f tall x %.1f x %.1f cm -> %s'
          % (len(ob.data.vertices), len(ob.data.polygons),
             tall, hi[0] - lo[0], hi[1] - lo[1], path))
    if abs(tall - TALL) > 6.0:
        print('  HEIGHT IS %.1f AND SHOULD BE ABOUT %.1f' % (tall, TALL))


main()
