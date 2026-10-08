# A FROG, for the fens.
#
#   blender --background --python Tools/blend/frog.py
#
# The last of the four things asked for in one line off the stream: "crows in
# moor instead of regular bird song / birds flying in the sky / maybe
# occasional rainbow after rain / maybe a frog here and there hopping around on
# the ground in the fens... details like these are in my opinion what will give
# this window a big jump."
#
# MEASURED, AND SMALL ON PURPOSE. A common frog is about nine centimetres nose
# to vent and a big toad thirteen; this is thirteen, which is the honest top of
# the range and still only a few pixels from where this camera stands. The
# temptation is to make it the size of a cat so it can be seen, and that is the
# mistake this project has already made once with an axe the size of a door. A
# frog is small. What carries it is the HOP, because motion is read long before
# shape is, and `AIntervalSmallLife` throws it along a real arc.
#
# WHY NOT `forge.py`. A frog is the most organic thing this world has needed:
# a squat dome, a wide mouth, eyes that sit ON TOP of the skull rather than in
# it, and folded back legs. The forge has a blob and a lathe, and a frog made
# of those is a potato with dots.
import bpy
import bmesh
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', '..', 'Art', 'Forged'))


def body():
    """Squat, widest behind the shoulders, with a blunt wide head.

    Rings again rather than a squashed sphere, because the profile has to be
    different front and back: a frog's head is a wedge and its rump is a dome,
    and a sphere is neither.
    """
    bm = bmesh.new()
    # (x nose to rump, half-width, half-height, how far the section sits up)
    profile = [
        (6.5, 0.6, 0.5, 0.9),      # the snout
        (5.2, 1.9, 1.2, 1.1),
        (3.6, 3.0, 1.9, 1.3),      # the jaw, which is most of the head
        (1.6, 3.4, 2.3, 1.5),
        (-0.6, 3.6, 2.6, 1.6),     # the shoulders
        (-3.0, 3.3, 2.5, 1.5),
        (-5.2, 2.5, 1.9, 1.2),     # the rump
        (-6.4, 1.0, 0.8, 0.9),
    ]
    rings = []
    SEG = 12
    for x, hw, hh, up in profile:
        ring = []
        for s in range(SEG):
            a = 2.0 * math.pi * s / SEG
            # FLAT UNDERNEATH. A frog sitting on mud is not a ball resting on
            # a point: the belly is a plane. Squashing only the lower half is
            # the difference between an animal and a bead.
            z = math.sin(a)
            z = z * hh if z > 0 else z * hh * 0.45
            ring.append(bm.verts.new((x, math.cos(a) * hw, z + up)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        lo, hi = rings[i], rings[i + 1]
        for s in range(SEG):
            t = (s + 1) % SEG
            bm.faces.new((lo[s], lo[t], hi[t], hi[s]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    me = bpy.data.meshes.new('body')
    bm.to_mesh(me)
    bm.free()
    return bpy.data.objects.new('body', me)


def eye(side):
    """An eye, ON the skull rather than in it, which is the whole silhouette.

    Seen from directly above -- which is how this window sees everything -- a
    frog is an oval with two bumps at the front. Take the bumps away and it is
    a stone.
    """
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=1.25)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(3.4, 1.9 * side, 3.5))
    me = bpy.data.meshes.new('eye')
    bm.to_mesh(me)
    bm.free()
    return bpy.data.objects.new('eye', me)


def leg(side):
    """A back leg, folded: thigh out and back, shin forward, foot flat.

    Folded rather than extended, because a frog at rest is folded and this one
    is at rest for most of every hop. Three segments swept as a tube, which is
    the one thing a forge could have done and the rest of the animal is not.
    """
    bm = bmesh.new()
    path = [(-2.2, 2.8 * side, 1.8),    # the hip
            (-5.6, 4.4 * side, 1.6),    # the knee, out behind
            (-2.6, 5.2 * side, 1.0),    # the ankle, forward again
            (0.6, 5.0 * side, 0.5)]     # the foot, flat on the ground
    radii = [1.5, 1.1, 0.75, 0.5]
    rings = []
    SEG = 6
    for (p, r) in zip(path, radii):
        ring = []
        for s in range(SEG):
            a = 2.0 * math.pi * s / SEG
            ring.append(bm.verts.new((p[0] + math.cos(a) * r * 0.75,
                                      p[1],
                                      p[2] + math.sin(a) * r)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        lo, hi = rings[i], rings[i + 1]
        for s in range(SEG):
            t = (s + 1) % SEG
            bm.faces.new((lo[s], lo[t], hi[t], hi[s]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    me = bpy.data.meshes.new('leg')
    bm.to_mesh(me)
    bm.free()
    return bpy.data.objects.new('leg', me)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    parts = [body(), eye(1), eye(-1), leg(1), leg(-1)]
    for o in parts:
        scene.collection.objects.link(o)
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    frog = bpy.context.view_layer.objects.active
    frog.name = 'frog'

    bpy.ops.object.shade_smooth()
    bpy.ops.object.modifier_add(type='WEIGHTED_NORMAL')
    bpy.context.object.modifiers["WeightedNormal"].keep_sharp = True
    bpy.ops.object.modifier_apply(modifier="WeightedNormal")

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')

    # `Herb` is the palette's green. A frog is not the same green as grass and
    # the material instance can be told so later; what matters here is that the
    # slot is a palette NAME, or `dress_forged.py` has nothing to bind and the
    # frog arrives grey.
    frog.data.materials.append(bpy.data.materials.new('Herb'))

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'frog.obj')
    bpy.ops.wm.obj_export(filepath=path, export_selected_objects=False,
                          export_materials=True, export_uv=True,
                          export_normals=True, export_triangulated_mesh=False,
                          forward_axis='Y', up_axis='Z')
    xs = [v.co.x for v in frog.data.vertices]
    ys = [v.co.y for v in frog.data.vertices]
    zs = [v.co.z for v in frog.data.vertices]
    print('FROG %d verts %d faces   %.1f long x %.1f wide x %.1f tall cm -> %s'
          % (len(frog.data.vertices), len(frog.data.polygons),
             max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), path))


main()
