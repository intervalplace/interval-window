# THE CINDER-CROWN: the rarest thing anybody in this world will ever wear.
#
#   blender --background --python Tools/blend/cinder_crown.py
#
# WHAT IT IS, out of `engine.js`. It falls from the DRAGON, one in two thousand
# and forty-eight on a roll counted per citizen (§6ba, the Reading Rule, so it
# cannot be timed by holding the beast at a point of life and watching the
# beacon). It lands in the same shared pile as the magic stones, "to be fought
# over at the pickup". And §6da: "worn on the head, defends nothing -- pure
# cosmetic".
#
# So it protects nobody, buys nothing, and is worth exactly what it looks like.
# It was being drawn as `Iron_Crown` out of the armour kit: a plain circlet
# with four points, the same object a hundred games have. The rarest cosmetic
# in a world should not be a stock prop, and a thing called a CINDER crown
# should have been in a fire.
#
# WHAT IT IS MADE OF. Cinder is what is left when something has burned: light,
# black, cracked, and still holding heat in the fissures. So the band is
# broken rather than cast -- a ring of burnt masses fused together, with deep
# splits between them -- and its points are not fleurs but the spines a fire
# leaves, uneven, some snapped short. Two materials: `Soot` for the body and
# `Ember` for the cracks, which is a separate slot so the cracks can be given
# an emissive of their own and a citizen wearing this can be picked out of a
# market square at night. That is the entire purpose of the object.
#
# MEASURED. A head is about 22 cm across, so the band is 23 cm outside and the
# tallest spine stands 11 cm, which is a crown and not a helmet.
import bpy
import bmesh
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', '..', 'Art', 'Forged'))

R_IN, R_OUT = 9.8, 11.5      # the band, in centimetres
LUMPS = 9                    # burnt masses round the ring


def band(bm, rng, tag):
    """A ring of fused lumps, not a cast hoop.

    Each segment gets its own radius and height, so the band has the uneven,
    bitten profile of something that cooled in a fire rather than in a mould.
    The splits between lumps are where the ember material goes.
    """
    # TWELVE SAMPLES A LUMP, not six. At six, the quad at a seam was a sixth
    # of a lump wide and a third of the band tall -- so the ember faces came
    # out as big rectangles round the outside and the crown read as a black
    # thing with TEETH. Twelve halves them, and the recess below sinks them.
    PER = 12
    SEG = LUMPS * PER
    rings = []
    for level, (zz, swell) in enumerate(((0.0, 1.0), (2.6, 1.06), (5.2, 0.94))):
        ring = []
        for s in range(SEG):
            a = 2.0 * math.pi * s / SEG
            # Which lump this sample belongs to, and how near its middle:
            # fat at the middle of a lump, pinched at the split.
            t = (s % PER) / float(PER)
            pinch = 0.72 + 0.28 * math.sin(math.pi * t)
            grit = 1.0 + (rng.random() - 0.5) * 0.09
            r_in = R_IN * (2.0 - pinch) * 0.5 * grit
            r_out = R_OUT * pinch * swell * grit
            # AND THE SEAM IS A GROOVE. Pulled in more than a centimetre, so
            # the ember sits DOWN IN a split catching shadow on both sides,
            # rather than sitting on the surface like an inlay.
            if s % PER == 0:
                r_out *= 0.84
            ring.append((a, r_in, r_out, zz + (rng.random() - 0.5) * 0.7))
        rings.append(ring)

    verts = []
    for ring in rings:
        row = []
        for a, r_in, r_out, zz in ring:
            row.append((bm.verts.new((math.cos(a) * r_in, math.sin(a) * r_in, zz)),
                        bm.verts.new((math.cos(a) * r_out, math.sin(a) * r_out, zz))))
        verts.append(row)
    SEGN = len(verts[0])
    for L in range(len(verts) - 1):
        for s in range(SEGN):
            t = (s + 1) % SEGN
            lo, hi = verts[L], verts[L + 1]
            face = bm.faces.new((lo[s][1], lo[t][1], hi[t][1], hi[s][1]))
            # THE SPLIT BETWEEN TWO LUMPS, tagged here rather than worked out
            # from the geometry afterwards. The first version tested "inside
            # the band and low down", which is the whole inner surface of a
            # crown: 240 of 432 faces came out glowing, and a crown that is
            # more ember than cinder is a lamp. There are six samples to a
            # lump and the split is the one at the seam.
            if s % PER == 0:
                face[tag] = 1
            bm.faces.new((lo[t][0], lo[s][0], hi[s][0], hi[t][0]))   # inside
    for s in range(SEGN):
        t = (s + 1) % SEGN
        bm.faces.new((verts[0][s][0], verts[0][t][0],
                      verts[0][t][1], verts[0][s][1]))               # underneath
        top = verts[-1]
        bm.faces.new((top[t][0], top[s][0], top[s][1], top[t][1]))   # the rim
    return verts[-1]


def spine(bm, a, height, lean, rng):
    """One burnt point: a tapered spike, bent, and not the same as its
    neighbours. A crown of nine identical points is a gear."""
    base = 5.2
    steps = [(0.0, 1.0), (0.34, 0.66), (0.66, 0.36), (1.0, 0.0)]
    rings = []
    for t, w in steps:
        # It leans outward and twists a little as it rises, the way a thing
        # that softened in heat does.
        # BARELY OUTWARD. The first version leaned by up to six centimetres
        # and the crown came out thirty across, which is a head and a half.
        r = R_OUT * 0.86 + lean * t * 0.9
        z = 5.2 + height * t
        aa = a + lean * t * 0.05
        ring = []
        half = base * 0.5 * w
        if w <= 0.0:
            ring.append(bm.verts.new((math.cos(aa) * r, math.sin(aa) * r, z)))
        else:
            for k in range(4):
                b = aa + (k - 1.5) * (half / max(r, 1.0)) * 0.9
                rr = r + ((k in (1, 2)) and half * 0.45 or 0.0)
                ring.append(bm.verts.new((math.cos(b) * rr, math.sin(b) * rr,
                                          z + (rng.random() - 0.5) * 0.5)))
        rings.append(ring)
    for i in range(len(rings) - 2):
        lo, hi = rings[i], rings[i + 1]
        for k in range(len(lo)):
            j = (k + 1) % len(lo)
            bm.faces.new((lo[k], lo[j], hi[j], hi[k]))
    tip = rings[-1][0]
    last = rings[-2]
    for k in range(len(last)):
        j = (k + 1) % len(last)
        bm.faces.new((last[k], last[j], tip))


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rng = random.Random(6062)          # §6da, so the crown is the same crown
    bm = bmesh.new()
    # THE LAYER IS MADE BEFORE ANY FACE IS, and that is not tidiness. Adding a
    # custom-data layer reallocates the face data, which invalidates every
    # BMFace reference Python is holding -- so a list of faces gathered first
    # and tagged afterwards dies with "BMesh data of type BMFace has been
    # removed". Made first, every face is tagged as it is born.
    tag = bm.faces.layers.int.new('ember')
    band(bm, rng, tag)
    # NINE SPINES OF DIFFERENT HEIGHTS, two of them snapped short. A fire does
    # not leave a symmetrical thing behind, and the asymmetry is most of why
    # this reads as burnt rather than forged.
    # AND SHORTER. Sixteen centimetres of crown on a twenty-two centimetre
    # head is a helmet with holes in it. The tallest spine is now seven, so
    # the whole thing stands about twelve: a band with points, worn ON a head.
    tall = [7.0, 4.6, 6.1, 2.0, 6.5, 5.1, 2.5, 5.7, 4.1]
    for i, h in enumerate(tall):
        spine(bm, 2.0 * math.pi * i / LUMPS, h, 1.0 + rng.random() * 0.8, rng)
    # The tags survive `to_mesh` as a mesh attribute, which is why they are a
    # bmesh layer rather than a list of indices: `to_mesh` renumbers.
    me = bpy.data.meshes.new('cinder_crown')
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new('cinder_crown', me)
    bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)

    # Burnt stone is not smooth. Auto-smooth keeps the lumps rounded and the
    # splits between them sharp, which is the whole surface.
    bpy.ops.object.shade_smooth()
    bpy.ops.object.modifier_add(type='WEIGHTED_NORMAL')
    bpy.context.object.modifiers["WeightedNormal"].keep_sharp = True
    bpy.ops.object.modifier_apply(modifier="WeightedNormal")

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')

    # TWO SLOTS, AND THE SECOND ONE IS THE POINT. `Soot` is the burnt body;
    # `Ember` is given to the faces deepest inside the splits, so
    # `dress_forged.py` can make that one emissive and the crown carries its
    # own light. A cosmetic whose entire job is to be seen should be visible
    # after dark.
    # `CrustBurnt` AND NOT `Soot`. Soot is (0.114, 0.110, 0.118), which is
    # very nearly black: lit from one side the crown came out as a silhouette
    # with no form in it at all, a hole in the picture. Charred stone is not
    # black, it is a warm dark brown, and this one also sits with the embers
    # instead of fighting them.
    o.data.materials.append(bpy.data.materials.new('CrustBurnt'))
    o.data.materials.append(bpy.data.materials.new('Ember'))
    me = o.data
    marked = me.attributes.get('ember')
    if marked is not None:
        for i, poly in enumerate(me.polygons):
            if marked.data[i].value:
                poly.material_index = 1
        me.attributes.remove(marked)

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'cinder_crown.obj')
    bpy.ops.wm.obj_export(filepath=path, export_selected_objects=False,
                          export_materials=True, export_uv=True,
                          export_normals=True, export_triangulated_mesh=False,
                          forward_axis='Y', up_axis='Z')
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    embers = sum(1 for p in me.polygons if p.material_index == 1)
    print('CROWN %d verts %d faces (%d of them ember)   %.1f x %.1f x %.1f cm'
          % (len(me.vertices), len(me.polygons), embers,
             max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)))
    print('  -> %s' % path)


main()
