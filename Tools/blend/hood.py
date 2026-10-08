# THE WAYFARER'S HOOD, which is the most important thing anybody wears here.
#
#   blender --background --python Tools/blend/hood.py
#
# WHAT IT IS, out of the engine's own notes (§6ax). It is granted once, to a
# citizen who has walked every trade -- "1200 is seventy-odd in all seventeen,
# a long way into every trade and the end of none". Nothing GIVES it, because
# the authority that would have dissolved at the founding. It survives the
# death that annihilates every other pack. It never expires, where all other
# ground rots in a hundred ticks. It carries the tick it was minted at, so a
# hood lying in the deep Wilds years later says whose it was and how far they
# got: "the only record in the world placed by history rather than by a
# generator."
#
# AND THE WINDOW DREW NOTHING AT ALL. Its item name is `hood:<64 hex>:<tick>`
# rather than a word, so the wardrobe lookup found no row and the one citizen
# in the world who had earned otherwise walked about bare-headed.
#
# SO IT IS NOT THE RANGER'S HOOD IN ANOTHER COLOUR. This one has to read
# across a market square as something nobody else has: a deep cowl, and a
# mantle over the shoulders that no other garment in this world has. The
# silhouette is the whole of it at this distance.
#
# MEASURED. A head is about 22 cm across and a citizen is 181 cm; the cowl is
# 26 cm across so it sits OVER a head rather than on it, and the mantle falls
# 30 cm, which is to the shoulder blade.
import bpy
import bmesh
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', '..', 'Art', 'Forged'))


def cowl():
    """The hood itself: a dome drawn out to a point at the back.

    Built as stacked rings so the profile is under control. A sphere with a
    lattice would be fewer lines and would not let the back of the head be a
    different shape from the front, which is the whole character of a cowl --
    it hangs behind and is drawn forward over the brow.
    """
    bm = bmesh.new()
    # (z up the head, half-depth front-to-back, half-width, centre offset back)
    profile = [
        (-4.0, 12.0, 12.0, 1.5),     # the open rim, at the jaw
        (2.0, 13.0, 13.0, 1.5),
        (8.0, 13.0, 12.6, 1.0),
        (13.0, 11.6, 11.0, 0.0),
        (17.0, 9.0, 8.4, -1.0),
        (20.0, 5.6, 5.2, -2.5),
        (22.0, 2.2, 2.0, -4.5),      # drawn back to a point
        (22.4, 0.4, 0.4, -6.5),
    ]
    rings = []
    SEG = 14
    for z, hd, hw, back in profile:
        ring = []
        for s in range(SEG):
            a = 2.0 * math.pi * s / SEG
            ring.append(bm.verts.new((math.cos(a) * hd + back,
                                      math.sin(a) * hw, z)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        lo, hi = rings[i], rings[i + 1]
        for s in range(SEG):
            t = (s + 1) % SEG
            bm.faces.new((lo[s], lo[t], hi[t], hi[s]))
    # The rim is left OPEN: a face across it is a mask, and this is a hood.
    bm.faces.new(rings[-1])
    me = bpy.data.meshes.new('cowl')
    bm.to_mesh(me)
    bm.free()
    return bpy.data.objects.new('cowl', me)


def mantle():
    """The shoulder cape, which is what nobody else in this world has.

    A skirt of cloth from the neck out over the shoulders, cut longer at the
    back than the front. Two rings and a hem: the shape is simple and the
    LENGTH is what reads, because from above a mantle is a dark disc round a
    pale head and there is nothing else on the island shaped like that.
    """
    bm = bmesh.new()
    SEG = 16
    # (z, radius, how much longer at the back)
    tiers = [(-3.0, 9.0, 0.0), (-11.0, 17.0, 3.0), (-19.0, 22.0, 6.0),
             (-26.0, 24.0, 8.0)]
    rings = []
    for z, r, back in tiers:
        ring = []
        for s in range(SEG):
            a = 2.0 * math.pi * s / SEG
            # `back` stretches the half that is behind the citizen, so the
            # hem hangs to the shoulder blade and clears the collarbone.
            reach = r + back * max(0.0, math.cos(a))
            ring.append(bm.verts.new((math.cos(a) * reach + back * 0.4,
                                      math.sin(a) * r, z)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        lo, hi = rings[i], rings[i + 1]
        for s in range(SEG):
            t = (s + 1) % SEG
            bm.faces.new((lo[s], lo[t], hi[t], hi[s]))
    bm.faces.new(list(reversed(rings[0])))
    # The hem is open, so the cloth has an inside. Two-sided in the material.
    me = bpy.data.meshes.new('mantle')
    bm.to_mesh(me)
    bm.free()
    return bpy.data.objects.new('mantle', me)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    parts = [cowl(), mantle()]
    for o in parts:
        scene.collection.objects.link(o)
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    hood = bpy.context.view_layer.objects.active
    hood.name = 'wayfarer_hood'

    # CLOTH IS SMOOTH AND HAS NO FACETS. The weighted normal keeps the hem and
    # the rim as creases while the dome rounds -- which is the one thing
    # `forge.py` could not do and the reason this is authored here.
    bpy.ops.object.shade_smooth()
    bpy.ops.object.modifier_add(type='WEIGHTED_NORMAL')
    bpy.context.object.modifiers["WeightedNormal"].keep_sharp = True
    bpy.ops.object.modifier_apply(modifier="WeightedNormal")

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')

    # `Cloth` is a palette entry, so `dress_forged.py` already makes the
    # material instance and binds it by name.
    hood.data.materials.append(bpy.data.materials.new('Cloth'))

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'wayfarer_hood.obj')
    bpy.ops.wm.obj_export(filepath=path, export_selected_objects=False,
                          export_materials=True, export_uv=True,
                          export_normals=True, export_triangulated_mesh=False,
                          forward_axis='Y', up_axis='Z')
    xs = [v.co.x for v in hood.data.vertices]
    ys = [v.co.y for v in hood.data.vertices]
    zs = [v.co.z for v in hood.data.vertices]
    print('HOOD %d verts %d faces   %.1f deep x %.1f wide x %.1f tall cm -> %s'
          % (len(hood.data.vertices), len(hood.data.polygons),
             max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), path))


main()
