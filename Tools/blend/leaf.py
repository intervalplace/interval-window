# A FALLEN LEAF, for the woods in autumn.
#
#   blender --background --python Tools/blend/leaf.py
#
# The world has computed `spring`, `autumn` and `winter` since the sky was
# written and NOTHING in this window has ever read them, so the seasons changed
# the date and nothing else. The butterflies emptying out of the meadows in
# winter was the first thing that did; this is the second, and it is the one
# somebody would actually mention to another player.
#
# MEASURED. An English oak leaf is 10 to 12 cm long and about 6 across, a birch
# nearer 5. This is 10 by 6, which is the oak, because the woods it falls in
# are drawn with oaks in them -- the Hollybarrow avenue is twenty-three of them
# by the generator's own count.
#
# SIMPLE, NOT LOBED. An oak leaf's lobes are its whole character in the hand
# and are entirely invisible at the five pixels this is ever drawn at, where
# the only things that read are the long axis, the point and the stalk. Lobes
# would cost sixty vertices to say nothing. The same argument the crow's
# silhouette makes, one scale smaller.
#
# IT IS A PLATE WITH A FOLD, not a flat quad. A leaf lying on the ground is
# never flat -- it curls along the midrib as it dries, and that curl is what
# catches the light and stops a drift of them reading as stickers on the
# grass. One number, and it is the difference between leaves and confetti.
import bpy
import bmesh
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'interval', 'Art', 'Forged')
if not os.path.isdir(OUT):
    OUT = os.path.abspath(os.path.join(HERE, '..', '..', 'Art', 'Forged'))

LONG = 10.0
WIDE = 6.0
CURL = 0.9      # cm the edges rise above the midrib


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    half = WIDE * 0.5

    # ---- A GRID ALONG THE MIDRIB, NOT A FAN FROM AN OUTLINE ----
    #
    # The first version drew the blade's edge as a closed spline and fanned
    # each segment back to whichever midrib vertex was nearest. That leaves
    # wedges between segments that chose different ribs, and the leaf rendered
    # with four holes punched through it in a pattern regular enough to look
    # deliberate. A fan from a curve to a line is not a triangulation.
    #
    # Rows across the leaf instead: for each step along the length, three
    # points -- one edge, the midrib, the other edge -- and quads between
    # consecutive rows. No gaps are possible, the midrib stays a crease where
    # the curl folds, and the width is a function anybody can read.
    N = 16
    rows = []
    bm = bmesh.new()
    for i in range(N + 1):
        u = i / N
        x = -LONG * 0.42 + u * LONG
        # WIDEST PAST THE MIDDLE, which is what makes it a leaf and not an
        # almond. The sine peaks where its argument is a half, so an exponent ABOVE
        # one pushes that past the midpoint: 1.3 puts the widest part at 0.59 of
        # the way to the tip. It was 0.78 first, which moved it the other way.
        w = half * math.sin(math.pi * u ** 1.3) ** 0.85
        lift = CURL * (0.45 + 0.55 * u)
        rows.append([
            bm.verts.new((x, -w, lift if w > 0.01 else 0.0)),
            bm.verts.new((x, 0.0, 0.0)),
            bm.verts.new((x, w, lift if w > 0.01 else 0.0)),
        ])
    for i in range(N):
        a, b = rows[i], rows[i + 1]
        for k in (0, 1):
            try:
                bm.faces.new((a[k], a[k + 1], b[k + 1], b[k]))
            except ValueError:
                pass

    me = bpy.data.meshes.new('leaf')
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new('leaf', me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)

    # A LEAF HAS TWO SIDES AND BOTH ARE SEEN, because it tumbles as it falls.
    # A single-sided blade vanishes for half of every turn, which is the one
    # thing that would make this read as a bug rather than as weather.
    sol = ob.modifiers.new('thick', 'SOLIDIFY')
    sol.thickness = 0.06
    bpy.ops.object.modifier_apply(modifier=sol.name)

    for p in ob.data.polygons:
        p.use_smooth = True
    sharp = ob.modifiers.new('sharp', 'EDGE_SPLIT')
    sharp.split_angle = math.radians(50.0)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0))
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.data.materials.append(bpy.data.materials.new('Gold'))

    path = os.path.join(OUT, 'leaf.obj')
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
    print('LEAF %d verts %d faces  %.1f long x %.1f wide x %.1f deep cm -> %s'
          % (len(ob.data.vertices), len(ob.data.polygons),
             hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2], path))
    if abs((hi[0] - lo[0]) - LONG) > 1.0:
        print('  LENGTH IS %.1f AND SHOULD BE %.1f' % (hi[0] - lo[0], LONG))


main()
