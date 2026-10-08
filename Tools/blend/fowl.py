# THE FOUR BIRDS, from one set of measurements.
#
#   blender --background --python Tools/blend/fowl.py
#
# WHY THIS REPLACES `bird.py`. That script built one bird and the window flew it
# over everything. The ground voices had already been split four ways after the
# note about "crows in moor instead of regular bird song" -- so a citizen on the
# moor HEARD crows and SAW the same bird that flies over a meadow, and on the
# shore heard gulls and saw a crow. It is the identical fault, one layer across,
# and it survived because the sound was the half anybody noticed.
#
# ONE BUILDER, FOUR SETS OF NUMBERS. The alternative was four scripts that are
# each eighty per cent the same geometry, which the README in this folder argues
# against for materials and is worse here: a wing section improved in one of
# them and not the other three is a bird that does not match its own family.
#
# MEASURED, EVERY ONE. The proportions are what tell these apart at the size the
# window draws them -- a gull is not a dark crow, it is a LONGER, NARROWER wing
# on a shorter body, and a pigeon is a barrel with a small head. Guessing them
# would produce four birds of the same shape in four colours, which is worse
# than the one bird this replaces because it would look deliberate.
#
#   carrion crow   47 cm long   95 cm span   broad fingered wing
#   herring gull   58 cm long  140 cm span   long narrow pointed wing
#   blackbird      25 cm long   36 cm span   short round wing
#   wood pigeon    41 cm long   75 cm span   pointed wing, deep breast
import bpy
import bmesh
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'interval', 'Art', 'Forged')
if not os.path.isdir(OUT):
    OUT = os.path.abspath(os.path.join(HERE, '..', '..', 'Art', 'Forged'))

# name, length, span, chord, bulk, sweep, point, tailLen, tailFan, hue
#   chord  HOW BROAD THE WING IS AT THE BODY, in centimetres, measured like
#          everything else. It was derived from body length at first, which is
#          a crow's ratio and only a crow's: applied to a blackbird it gave a
#          36 cm span on a 6 cm chord, which is a tern. Span alone does not
#          tell two birds apart -- a gull and a crow are a similar distance
#          across -- and chord against span is most of what does.
#   bulk   how deep the body is for its length: a pigeon is a barrel
#   sweep  how far back the tip sits behind the shoulder, as a fraction of span
#   point  1 is a pointed gull's wing, 0 is a blackbird's round one
FOWL = [
    ('bird',     47.0,  95.0, 13.0, 1.00, 0.30, 0.45, 15.0, 5.0, 'Soot'),
    ('gull',     58.0, 140.0, 15.0, 0.86, 0.42, 0.90, 13.0, 4.4, 'Fleece'),
    ('songbird', 25.0,  36.0, 10.0, 1.08, 0.24, 0.14, 11.0, 3.4, 'Fur'),
    ('dove',     41.0,  75.0, 14.0, 1.26, 0.26, 0.55, 14.0, 4.6, 'Cloth'),
]


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def body(length, bulk):
    """The trunk: a tapered tube along +X, deepest at the breast.

    The profile is the crow's, scaled. It is not linear and never was -- a bird
    is deepest a third of the way back and tapers to nothing at the tail -- so
    the shape is kept and only the numbers move.
    """
    k = length / 47.0
    profile = [
        (-16.0, 0.6, 0.6), (-11.0, 2.0, 1.8), (-5.0, 3.3, 2.9),
        (0.0, 3.8, 3.2), (5.0, 3.4, 2.8), (9.5, 2.4, 2.0),
        (12.5, 2.6, 2.2), (15.5, 1.9, 1.7), (17.2, 0.7, 0.7), (21.0, 0.25, 0.25),
    ]
    bm = bmesh.new()
    rings = []
    SEG = 10
    for x, hz, hy in profile:
        ring = []
        for s in range(SEG):
            a = 2.0 * math.pi * s / SEG
            ring.append(bm.verts.new((x * k,
                                      math.sin(a) * hy * k * bulk,
                                      math.cos(a) * hz * k * bulk)))
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


def wing(span, length, chord_cm, sweep, point):
    """ONE wing along +Y, which the mirror turns into two.

    THE CHORD IS WHAT TELLS THEM APART, not the span. A gull and a crow are a
    similar distance across; what makes one a gull is that the wing stays
    narrow the whole way out and ends in a point, where a crow's is broad to
    the last third and then fingers. `point` runs between those two.
    """
    half = span * 0.5
    root = chord_cm                      # chord where it meets the body
    tip = root * (0.10 + 0.34 * (1.0 - point))
    plan = []
    N = 9
    for i in range(N):                   # out along the leading edge
        u = i / (N - 1.0)
        y = half * u
        # the leading edge sweeps back; a pointed wing sweeps harder
        lead = root * 0.5 - half * sweep * u ** 1.25
        plan.append((y, lead))
    for i in range(N - 1, -1, -1):       # and home along the trailing edge
        u = i / (N - 1.0)
        y = half * u
        chord = root * (1.0 - u) + tip * u
        # a round wing carries its chord to the tip, a pointed one loses it early
        chord *= 1.0 - point * 0.45 * u ** 0.7
        # AND EVERY WING CLOSES AT THE TIP. Without this the chord simply ran
        # out at whatever it happened to be and the end was cut square, which
        # from above is a model aeroplane -- the exact thing the first bird
        # script warned about and then avoided only by having one hand-drawn
        # plan. `p` decides HOW it closes: a blackbird's wing stays full and
        # then rounds off in the last tenth, a gull's narrows the whole way to
        # a point. One expression, and the difference between the two is the
        # difference between the birds.
        close = 2.0 + 8.0 * (1.0 - point)
        chord *= math.sqrt(max(0.0, 1.0 - u ** close))
        lead = root * 0.5 - half * sweep * u ** 1.25
        plan.append((y, lead - chord))
    bm = bmesh.new()
    top, bot = [], []
    for y, x in plan:
        u = min(y / max(half, 0.001), 1.0)
        thick = (length / 47.0) * (1.0 - u * 0.8)
        lift = u ** 1.6 * (half * 0.05)      # a shallow V, not a plank
        top.append(bm.verts.new((x, y, length * 0.038 + lift + thick)))
        bot.append(bm.verts.new((x, y, length * 0.038 + lift - thick)))
    n = len(plan)
    for i in range(n - 1):
        bm.faces.new((top[i], top[i + 1], bot[i + 1], bot[i]))
    bm.faces.new(list(reversed(top)))
    bm.faces.new(bot)
    me = bpy.data.meshes.new('wing')
    bm.to_mesh(me)
    bm.free()
    return bpy.data.objects.new('wing', me)


def tail(length, tail_len, fan):
    """A flat fan behind, which is the other half of the silhouette."""
    k = length / 47.0
    back = -length * 0.32
    bm = bmesh.new()
    plan = [(back, 0.0), (back - tail_len * k * 0.5, fan * k),
            (back - tail_len * k * 0.85, fan * k * 0.48),
            (back - tail_len * k, 0.0),
            (back - tail_len * k * 0.85, -fan * k * 0.48),
            (back - tail_len * k * 0.5, -fan * k)]
    top, bot = [], []
    for x, y in plan:
        top.append(bm.verts.new((x, y, 0.9 * k)))
        bot.append(bm.verts.new((x, y, 0.1 * k)))
    n = len(plan)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((top[i], top[j], bot[j], bot[i]))
    bm.faces.new(list(reversed(top)))
    bm.faces.new(bot)
    me = bpy.data.meshes.new('tail')
    bm.to_mesh(me)
    bm.free()
    return bpy.data.objects.new('tail', me)


def build(name, length, span, chord_cm, bulk, sweep, point, tail_len, fan, hue):
    clear()
    parts = [body(length, bulk), wing(span, length, chord_cm, sweep, point),
             tail(length, tail_len, fan)]
    for o in parts:
        bpy.context.collection.objects.link(o)
    bpy.context.view_layer.objects.active = parts[0]
    for o in parts:
        o.select_set(True)
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name

    # THE MIRROR IS THE WHOLE REASON THIS IS NOT IN `forge.py`: the left wing
    # IS the right wing and cannot drift from it.
    mir = ob.modifiers.new('mirror', 'MIRROR')
    mir.use_axis = (False, True, False)
    bpy.ops.object.modifier_apply(modifier=mir.name)

    for p in ob.data.polygons:
        p.use_smooth = True
    sharp = ob.modifiers.new('sharp', 'EDGE_SPLIT')
    sharp.split_angle = math.radians(40.0)

    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0))
    bpy.ops.object.mode_set(mode='OBJECT')

    ob.data.materials.append(bpy.data.materials.new(hue))

    path = os.path.join(OUT, name + '.obj')
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
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
    got_len, got_span = hi[0] - lo[0], hi[1] - lo[1]
    print('%-9s %3d verts  %.1f long x %.1f span cm  (wanted %.0f x %.0f)  %s'
          % (name, len(ob.data.vertices), got_len, got_span, length, span, hue))
    if abs(got_span - span) > span * 0.12:
        print('  SPAN IS WRONG: %.1f against %.1f' % (got_span, span))
    if got_span < got_len:
        print('  THE AXES ARE SWAPPED: the span must be along Y')


for row in FOWL:
    build(*row)
