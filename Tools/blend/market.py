# THE MARKET AND WHAT THE KEEPERS HOLD, authored instead of assembled.
#
#   blender --background --python Tools/blend/market.py
#
# After the hats, 124 primitive pieces were left in the look across 54 rows.
# The largest single group was the stalls: 60 pieces, and 56 of them were the
# SAME SEVEN PARTS repeated across eight stall rows -- four legs, two posts and
# a flat slab of cloth, all cubes. One authored frame replaces all of it.
#
# The rest here are things a keeper holds or stands beside, which is where a
# primitive is least forgivable: it is next to a person, at the scale a person
# reads, in the middle of a town.
#
# WHAT IS NOT HERE, BECAUSE IT ALREADY EXISTS. Four of the keepers' props were
# fixed by pointing at meshes this project already owns and nobody had
# connected: a real Sheep for the shepherd, `fishing_rod` for the fisher,
# `Sawmill_saw` for the sawyer and `Pouch_Large` for the seed keeper. Authoring
# those would have been making a second one of something.
#
# MEASURED. A citizen is 181 cm and a market stall's counter is at 88, which is
# where the old cubes put it and is right: a counter is hip height.
import bpy
import bmesh
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', '..', 'Art', 'Forged'))


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def box(bm, x0, y0, z0, x1, y1, z1):
    """An axis-aligned box, by its two corners. Timber is boxes and saying so
    is not a placeholder: what was wrong with the stall was the CLOTH."""
    vs = [bm.verts.new(v) for v in (
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
              (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([vs[i] for i in f])


def finish(name, bm, material, smooth=False):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    if smooth:
        bpy.ops.object.shade_smooth()
        bpy.ops.object.modifier_add(type='WEIGHTED_NORMAL')
        bpy.context.object.modifiers["WeightedNormal"].keep_sharp = True
        bpy.ops.object.modifier_apply(modifier="WeightedNormal")
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.data.materials.append(bpy.data.materials.new(material))
    return ob


def save(ob, filename):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, filename)
    bpy.ops.wm.obj_export(filepath=path, export_selected_objects=False,
                          export_materials=True, export_uv=True,
                          export_normals=True, export_triangulated_mesh=False,
                          forward_axis='Y', up_axis='Z')
    xs = [v.co.x for v in ob.data.vertices]
    ys = [v.co.y for v in ob.data.vertices]
    zs = [v.co.z for v in ob.data.vertices]
    print('%-14s %3d verts %3d faces  %.0f x %.0f x %.0f cm -> %s'
          % (ob.name, len(ob.data.vertices), len(ob.data.polygons),
             max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), filename))


# ---------------------------------------------------------------------------

def awning():
    """THE STALL'S FRAME AND ITS CLOTH, as one mesh.

    Seven cubes became this. Six of them were the frame and a frame IS square
    timber, so the legs and posts are still boxes here and that is correct. The
    seventh was the awning: a flat slab 186 x 130 x 6 cm tilted six degrees,
    which is a board, not cloth.

    WHAT MAKES IT CLOTH IS THE SAG. The canopy is built as two slopes off a
    ridge with each span dipping in the middle, so the eaves hang lower than
    the line between the posts. That dip is the whole difference, and it is
    four centimetres: enough to catch the light differently along its length
    and nowhere near enough to look like a tent.
    """
    bm = bmesh.new()
    # four legs, 10 cm square, to the counter at 88
    for sx in (-68, 68):
        for sy in (-38, 38):
            box(bm, sx - 5, sy - 5, 0, sx + 5, sy + 5, 88)
    # two posts carrying the ridge, 9 cm square, to 188
    for sx in (-78, 78):
        box(bm, sx - 4.5, -4.5, 0, sx + 4.5, 4.5, 188)
    # the cloth. A ridge along x at 190, eaves at 176, and the middle of each
    # span dipping to 172: cloth held at its corners does not stay flat.
    RIDGE, EAVE, DIP = 190.0, 176.0, 172.0
    SPAN = 6                                  # samples along the stall
    xs = [-93.0 + 186.0 * i / SPAN for i in range(SPAN + 1)]
    # how far the ridge itself sags between the two posts
    def ridge_z(x):
        u = (x + 93.0) / 186.0
        return RIDGE - 5.0 * math.sin(math.pi * u)
    def eave_z(x):
        u = (x + 93.0) / 186.0
        return EAVE - (EAVE - DIP) * math.sin(math.pi * u)
    top, near, far = [], [], []
    for x in xs:
        top.append(bm.verts.new((x, 0.0, ridge_z(x))))
        near.append(bm.verts.new((x, -65.0, eave_z(x))))
        far.append(bm.verts.new((x, 65.0, eave_z(x))))
    cloth = []
    for i in range(SPAN):
        cloth.append(bm.faces.new((near[i], near[i + 1], top[i + 1], top[i])))
        cloth.append(bm.faces.new((top[i], top[i + 1], far[i + 1], far[i])))
    # AND THE CLOTH HAS A THICKNESS. Built as a single surface it is a plane:
    # lit from one side, invisible edge-on, and from under the stall you see
    # straight through the roof. Three centimetres is canvas rather than a
    # sheet of paper, and it gives the eaves an edge to catch the light on.
    bmesh.ops.solidify(bm, geom=cloth, thickness=-3.0)
    return finish('stall_awning', bm, 'Cloth')


def skep():
    """A BEE SKEP: coiled straw, the thing a beekeeper actually keeps bees in.

    It was a sphere. A skep is a dome of coiled rope-straw with a flat top and
    a doorway at the bottom, and the COILS are what say straw: six visible
    steps up the side rather than a smooth curve. 42 cm across and 38 tall,
    which is a real one.
    """
    bm = bmesh.new()
    SEG = 14
    rings = [(0.0, 21.0), (5.0, 21.0), (5.5, 20.4), (11.0, 20.4),
             (11.5, 19.2), (17.0, 19.2), (17.5, 17.4), (23.0, 17.4),
             (23.5, 14.8), (29.0, 14.8), (29.5, 11.0), (34.0, 11.0),
             (34.5, 6.0), (38.0, 6.0), (38.0, 0.0)]
    made = []
    for z, r in rings:
        if r <= 0.001:
            made.append([bm.verts.new((0.0, 0.0, z))]); continue
        made.append([bm.verts.new((math.cos(2 * math.pi * s / SEG) * r,
                                   math.sin(2 * math.pi * s / SEG) * r, z))
                     for s in range(SEG)])
    for lo, up in zip(made, made[1:]):
        if len(up) == 1:
            for s in range(SEG):
                bm.faces.new((lo[s], lo[(s + 1) % SEG], up[0]))
        else:
            for s in range(SEG):
                bm.faces.new((lo[s], lo[(s + 1) % SEG],
                              up[(s + 1) % SEG], up[s]))
    bm.faces.new(made[0])
    return finish('skep', bm, 'Wheat')


def clamp():
    """A CHARCOAL CLAMP: earth heaped over burning wood, which is a cone.

    So why author it. The cone was RIGHT in outline and wrong in every other
    way: perfectly circular, perfectly smooth, and perfectly symmetrical, which
    is not what a heap of turf shovelled over a fire looks like. This is the
    same cone with the radius jittered around it and a flat crown where the
    collier opens it, which is all a heap needs to stop reading as geometry.
    """
    bm = bmesh.new()
    SEG = 16
    prof = [(0.0, 62.0), (14.0, 55.0), (28.0, 45.0), (42.0, 32.0),
            (52.0, 19.0), (58.0, 11.0)]
    made = []
    for i, (z, r) in enumerate(prof):
        ring = []
        for s in range(SEG):
            a = 2 * math.pi * s / SEG
            # a repeatable wobble: the same heap every time the script runs
            k = 1.0 + 0.055 * math.sin(s * 2.3 + i * 1.7) + 0.03 * math.cos(s * 4.1)
            ring.append(bm.verts.new((math.cos(a) * r * k, math.sin(a) * r * k, z)))
        made.append(ring)
    for lo, up in zip(made, made[1:]):
        for s in range(SEG):
            bm.faces.new((lo[s], lo[(s + 1) % SEG], up[(s + 1) % SEG], up[s]))
    bm.faces.new(made[0])
    bm.faces.new(made[-1])            # the flat crown, opened to draw
    return finish('charcoal_clamp', bm, 'Soot')


def slab():
    """THE QUARRIER'S SLAB, carried on the shoulder.

    A cube is a slab, which is why this one survived every look. What a cube is
    not is STONE: it has four square corners and six flat faces, and a piece
    that came off a face under a wedge has neither. This is a box with every
    corner pulled about and one face left flat, because that face is the split.
    """
    bm = bmesh.new()
    W, D, H = 24.0, 12.0, 70.0
    pts = [(-W / 2, -D / 2, 0), (W / 2, -D / 2, 0), (W / 2, D / 2, 0), (-W / 2, D / 2, 0),
           (-W / 2, -D / 2, H), (W / 2, -D / 2, H), (W / 2, D / 2, H), (-W / 2, D / 2, H)]
    jog = [(0, 0, 0), (1.8, -0.9, 0), (-1.2, 1.4, 0), (0.9, 0.6, 0),
           (-2.1, 1.1, -3.2), (1.4, 1.8, -1.6), (-0.8, -1.5, -4.4), (2.2, -1.2, -2.0)]
    vs = [bm.verts.new((p[0] + j[0], p[1] + j[1], p[2] + j[2]))
          for p, j in zip(pts, jog)]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
              (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([vs[i] for i in f])
    return finish('stone_slab', bm, 'Rock')


def main():
    for make, filename in ((awning, 'stall_awning.obj'), (skep, 'skep.obj'),
                           (clamp, 'charcoal_clamp.obj'), (slab, 'stone_slab.obj')):
        fresh()
        save(make(), filename)
    print('4 market pieces written to %s' % OUT)


main()
