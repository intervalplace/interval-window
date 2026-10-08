# A BUTTERFLY, for the meadows and the chalk.
#
#   blender --background --python Tools/blend/butterfly.py
#
# Asked for off the back of the birds: "we added birds in the sky for
# atmosphere, but I think we should add like butterflies (closer to the ground
# so they're actually visible) in the farmlands and stuff like that too, I
# think it makes the world more alive."
#
# THE POINT IS THAT IT IS LOW. A crow is eight metres up and reads as a
# silhouette against the sky; it is atmosphere you notice above you. This is at
# knee height over the grass you are standing in, which is the other half of a
# place being alive, and it is why the shape matters more here than it does on
# the bird: you are closer to it.
#
# MEASURED, AND AT THE TOP OF THE RANGE ON PURPOSE. A small white is about
# 5 cm across and a peacock 6.5; this is 9, which is a large white or a
# swallowtail and the honest top of what flies over a field. The frog's script
# argues the opposite case and is right about a frog: it sits still, so size is
# all it has. A butterfly is never still, and what carries it is MOTION and
# COLOUR -- `AIntervalSmallLife` bobs it and rolls it, and the roll is the
# whole flap. Even so, 5 cm here would be two pixels and a rumour.
#
# FLAT WINGS, AND THAT IS LOAD-BEARING. The flap is not in the mesh and not in
# the material: the actor rolls the whole body about its forward axis, so the
# wing area you see goes from full to an edge and back. That reads as a beat
# from a camera looking down, costs nothing beyond the transform already being
# written, and needs no second material master the way the bird's wing beat
# did. It only works if the wings lie in the XY plane, so they do.
#
# WHY NOT `forge.py`. The same three reasons as the bird: no UVs, no mirror,
# and no smoothing. A wing wants a soft outer edge and the two sides must be
# the same wing, not two attempts at one.
import bpy
import bmesh
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'interval', 'Art', 'Forged')
if not os.path.isdir(OUT):
    OUT = os.path.abspath(os.path.join(HERE, '..', '..', 'Art', 'Forged'))

SPAN = 8.5          # cm, tip to tip (the outline reaches 4.25 either side)
BODY = 2.6          # cm, head to tail


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def body():
    """The abdomen: a thin tapered tube along +X.

    Barely visible and built anyway, because without it the two wings meet in
    a line and the thing reads as a folded leaf. Six segments: it is two
    millimetres across and nobody will ever count them.
    """
    # LONG ENOUGH TO REACH THE HINDWING ROOT, which the first one was not: the
    # hindwings hang from x = -1.8 and the body stopped at -1.3, so the pair
    # were pinned to nothing and the gap showed from above.
    profile = [
        (-2.00, 0.07),      # the tail
        (-1.40, 0.19),
        (-0.60, 0.27),      # the thorax, where all four wings hang
        (0.30, 0.24),
        (1.05, 0.16),
        (1.45, 0.05),       # the head
    ]
    bm = bmesh.new()
    rings = []
    SEG = 6
    for x, r in profile:
        ring = []
        for s in range(SEG):
            a = 2.0 * math.pi * s / SEG
            ring.append(bm.verts.new((x, math.sin(a) * r, math.cos(a) * r)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        lo, hi = rings[i], rings[i + 1]
        for s in range(SEG):
            t = (s + 1) % SEG
            bm.faces.new((lo[s], lo[t], hi[t], hi[s]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    me = bpy.data.meshes.new('body')
    bm.to_mesh(me)
    bm.free()
    return bpy.data.objects.new('body', me)


def wing(outline, thick):
    """One wing, as a flat plate with a section.

    `outline` is the leading edge from the shoulder outward and then back
    along the trailing edge, in the XY plane. The plate is given a thickness
    that falls to nothing at the tip, which is what stops a wing reading as a
    sheet of card: a real one is thickest where it meets the body.
    """
    bm = bmesh.new()
    top, bot = [], []
    n = len(outline)
    for i, (x, y) in enumerate(outline):
        # thickest at the shoulder (y small), nothing at the tip
        t = thick * (1.0 - min(1.0, abs(y) / (SPAN * 0.5)) ** 0.7)
        top.append(bm.verts.new((x, y, t)))
        bot.append(bm.verts.new((x, y, -t)))
    bm.faces.new(top)
    bm.faces.new(list(reversed(bot)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((top[i], top[j], bot[j], bot[i]))
    me = bpy.data.meshes.new('wing')
    bm.to_mesh(me)
    bm.free()
    return bpy.data.objects.new('wing', me)


def smooth(pts, per=4):
    """A closed outline through the given corners, rounded.

    TWO ATTEMPTS GOT THIS WRONG IN OPPOSITE DIRECTIONS. Written as a polygon
    of seven corners, each wing read as an arrowhead: at nine centimetres the
    silhouette IS the animal and hard corners say cut-out. Written as a polar
    lobe swung from the thorax, the maths was smooth and the shape was not a
    wing -- four teardrops floating clear of the body, because a lobe closing
    to a point at both ends cannot also meet the body along an edge.

    So: the corners are chosen by hand, where they belong, and a Catmull-Rom
    spline is run through them. The control points say what shape it is and the
    spline says that a wing edge is a curve. Four samples a span is twenty-odd
    points round a wing, which is smooth at any size this is ever drawn.
    """
    n = len(pts)
    out = []
    for i in range(n):
        p0, p1 = pts[(i - 1) % n], pts[i]
        p2, p3 = pts[(i + 1) % n], pts[(i + 2) % n]
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            out.append(tuple(
                0.5 * ((2 * p1[c])
                       + (-p0[c] + p2[c]) * t
                       + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                       + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3)
                for c in (0, 1)))
    return out


def wings():
    """Four of them: a forewing and a hindwing, mirrored.

    The two shapes are what makes this a butterfly and not a moth. The forewing
    is the longer, reaches FORWARD as well as out, and carries a squared tip; the
    hindwing is a rounder lobe tucked behind it. A moth's two are the same
    rounded shape, which is exactly the thing to avoid.

    EVERY OUTLINE STARTS AND ENDS ON THE THORAX, at a y of a millimetre or two,
    so the four wings and the body are one silhouette rather than five objects
    near each other. The forewing's trailing edge and the hindwing's leading
    edge overlap, as a real pair sit, which closes the notch that otherwise
    reads as a bite taken out of each side.
    """
    # THE STEP BETWEEN THEM IS THE WHOLE SILHOUETTE. Drawn with the two lobes
    # reaching equally far out, they merge into one rounded blade a side and
    # the insect reads as a heart. A butterfly's forewing goes a long way
    # further out than its hindwing, and the shoulder where one gives way to
    # the other is the notch the eye uses to tell what it is looking at. So the
    # forewing tip is at 4.3 cm and the hindwing's outer lobe stops at 2.6.
    fore = [
        (1.45, 0.18),     # the shoulder, at the front of the thorax
        (1.70, 1.40),     # the leading edge, nearly straight: a forewing is
        (1.55, 2.90),     # a triangle before it is anything else
        (1.05, 3.95),
        # THE APEX WANTS A CORNER, and a spline through evenly spaced points
        # will not give one: seen from above the forewing came out as a tall
        # egg, which is a moth. Three points close together turn the curve
        # sharply over a short distance, which is a tip. It is the same trick
        # the hull of a boat uses and it costs two vertices.
        (0.70, 4.22),
        (0.25, 4.34),     # the tip, out and a little forward
        (-0.18, 4.18),
        (-0.55, 3.85),    # and away round the outer margin
        (-1.05, 2.70),
        (-1.10, 1.50),    # and the trailing edge cuts back in: the notch
        (-0.55, 0.50),
        (-0.20, 0.16),
    ]
    hind = [
        (-0.70, 0.14),
        (-0.95, 1.25),    # its leading edge runs under the forewing
        (-1.45, 2.25),
        (-2.15, 2.60),    # the outer lobe, well short of the forewing's tip
        (-2.85, 2.15),
        (-3.05, 1.15),
        (-2.70, 0.30),
        (-1.80, 0.10),
    ]
    out = []
    for shape, thick in ((fore, 0.085), (hind, 0.070)):
        for side in (1.0, -1.0):
            # WRITTEN TWICE RATHER THAN MIRRORED WITH A MODIFIER, because the
            # winding has to flip with the side or one wing lights inside out,
            # and a modifier applied later is one more thing to forget.
            pts = [(x, y * side) for x, y in smooth(shape)]
            if side < 0:
                pts = list(reversed(pts))
            out.append(wing(pts, thick))
    return out


def main():
    clear()
    parts = [body()] + wings()
    for ob in parts:
        bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = parts[0]
    for ob in parts:
        ob.select_set(True)
    bpy.ops.object.join()
    moth = bpy.context.view_layer.objects.active
    moth.name = 'butterfly'

    # SMOOTH, then sharpen anything that should be an edge. The body is round
    # and the wings are plates: an auto-smooth angle keeps the first and leaves
    # the second alone, which is one line instead of two meshes.
    for p in moth.data.polygons:
        p.use_smooth = True
    mod = moth.modifiers.new('sharp', 'EDGE_SPLIT')
    mod.split_angle = math.radians(40.0)

    # UVs, which the importer requires. A planar unwrap is right here: the
    # whole thing is flat and nothing is textured, so this exists to satisfy
    # `UVs.IsValidIndex` rather than to carry a picture.
    bpy.ops.object.select_all(action='DESELECT')
    moth.select_set(True)
    bpy.context.view_layer.objects.active = moth
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0))
    bpy.ops.object.mode_set(mode='OBJECT')

    # ONE SLOT, AND ITS NAME IS A PALETTE KEY, or `dress_forged.py` has nothing
    # to bind and it arrives grey. The actor sets the material itself, so this
    # name only has to exist; the two species are two materials in the look,
    # over one mesh.
    moth.data.materials.append(bpy.data.materials.new('Fleece'))

    path = os.path.join(OUT, 'butterfly.obj')
    bpy.ops.object.select_all(action='DESELECT')
    moth.select_set(True)
    bpy.ops.wm.obj_export(filepath=path, export_selected_objects=False,
                          export_materials=True, export_uv=True,
                          export_normals=True, export_triangulated_mesh=False,
                          forward_axis='Y', up_axis='Z')

    xs = [v.co.x for v in moth.data.vertices]
    ys = [v.co.y for v in moth.data.vertices]
    zs = [v.co.z for v in moth.data.vertices]
    print('BUTTERFLY %d verts %d faces   %.1f long x %.1f span x %.1f deep cm'
          % (len(moth.data.vertices), len(moth.data.polygons),
             max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)))
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for line in open(path):
        if line.startswith('v '):
            q = [float(v) for v in line.split()[1:4]]
            for i in range(3):
                lo[i] = min(lo[i], q[i])
                hi[i] = max(hi[i], q[i])
    print('  on disk: length %.1f along X, span %.1f along Y, depth %.1f -> %s'
          % (hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2], path))
    if hi[1] - lo[1] < hi[0] - lo[0]:
        print('  THE AXES ARE SWAPPED: the span must be along Y, see the note above')
    if abs((hi[1] - lo[1]) - SPAN) > 0.6:
        print('  SPAN IS %.1f cm AND IT SHOULD BE %.1f' % (hi[1] - lo[1], SPAN))


main()
