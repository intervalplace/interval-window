# THE GREAT HELM, which is the dearest thing anybody puts on their head.
#
#   blender --background --python Tools/blend/great_helm.py
#
# WHY IT NEEDED AUTHORING. `great-helm` and `shell-helm` both pointed at
# `Bucket_Helmet2` out of a CC0 kit, and that mesh is a cylinder with an eye
# slit cut in it. It is real art rather than a placeholder, but it reads as a
# primitive, and it was doing duty for BOTH of the two dearest helms in the
# world: the great helm costs two star-alloy, which is seven quick-ingots and
# a brimstone each, and it looked cheaper than the iron one.
#
# A GREAT HELM IS A BARREL, AND THAT IS NOT THE PROBLEM. The historical object
# really is a drum over the whole head. What makes one look forged rather than
# turned is everything the kit's mesh leaves off: the taper, the brow that
# stands out from the face, the reinforcing cross, the sight slits let into it
# and the breaths punched below them. So this does not avoid the barrel, it
# builds the barrel properly.
#
# MEASURED. A head is about 22 cm across and a citizen is 181 cm. This is 25 cm
# across the brow so it sits over a head with a padded cap under it, and 27 cm
# tall, which takes it from the crown to below the jaw, where a great helm
# ends. Compare the kit's, which was 30 tall and a uniform 24 wide.
import bpy
import bmesh
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', '..', 'Art', 'Forged'))

SIDES = 16          # faceted on purpose: this world is flat-shaded low poly


def barrel(bm):
    """The drum, as stacked rings so the profile is under control.

    A cylinder scaled by a lattice would be fewer lines and would give the
    same radius at every height, which is exactly the look being fixed. The
    profile below is the whole character: it swells at the brow, pulls in at
    the jaw, and turns over hard at the crown rather than ending in a lid.

    AND THE SIGHTS ARE IN THE PROFILE, not stuck on it. The first cut added
    them as little boxes, which is what `slab` does, so a slit meant to be
    LET INTO the face came out as a lump standing off it. A recess has to be
    an absence, and with no boolean anywhere in this project the only honest
    way to make one is to build the face with the dent already in it: two
    rings at the sight line whose front vertices sit further in than the rest.
    """
    # (z from the jaw, radius across, radius front-to-back, how far the front
    #  is pulled in at this height)
    profile = [
        (0.0,  11.4, 12.2, 0.0),   # the lower rim, at the jaw
        (2.0,  11.8, 12.6, 0.0),   # flared a little, so the edge reads as one
        (7.0,  12.1, 12.9, 0.0),
        (13.0, 12.5, 13.3, 0.0),   # the brow, the widest part
        (15.4, 12.4, 13.2, 1.5),   # the sight line: the face steps in
        (17.2, 12.3, 13.0, 1.5),   # and comes back out above it
        (18.6, 12.2, 12.8, 0.0),
        (22.0, 10.6, 11.0, 0.0),   # the crown begins to turn
        (25.0,  7.2,  7.5, 0.0),
        (27.0,  3.0,  3.1, 0.0),   # and closes, not quite to a point
    ]
    rings = []
    for z, rx, ry, sunk in profile:
        ring = []
        for i in range(SIDES):
            a = 2.0 * math.pi * i / SIDES
            # HOW FAR ROUND THE FACE IS. A great helm's sights run across the
            # front and stop at the temple; a groove that went all the way
            # round would be a join, not a slit.
            face = max(0.0, math.cos(a))
            cut = sunk * (1.0 if face > 0.62 else 0.0)
            ring.append(bm.verts.new((math.cos(a) * (ry - cut),
                                      math.sin(a) * (rx - cut * 0.5), z)))
        rings.append(ring)
    for lower, upper in zip(rings, rings[1:]):
        for i in range(SIDES):
            j = (i + 1) % SIDES
            bm.faces.new((lower[i], lower[j], upper[j], upper[i]))
    # A LID, NOT A DOME. A great helm's top is a flat plate riveted on, and
    # the flat catches the light differently from the drum, which is most of
    # what says the two parts were made separately.
    bm.faces.new(rings[-1])
    return rings


def band(bm, z0, z1, rx, ry, half, out, steps=9):
    """A strip of plate lying ON the drum, following its curve.

    THE FIRST CUT USED BOXES AND THEY FLOATED. A great helm's brow runs most
    of the way across the face, and the face is an ellipse: nineteen
    centimetres from temple to temple, the surface has already fallen four
    centimetres back from where it is at the nose. A straight box laid across
    that touches in the middle and hangs in the air at both ends, which is
    exactly how it rendered.

    So a band is an arc. It is swept through the same ellipse the drum is,
    a little further out, and capped at both ends.
    """
    inner, outer = [], []
    for k in range(steps):
        a = (-half) + (2.0 * half) * k / (steps - 1)
        for lst, grow in ((inner, 0.0), (outer, out)):
            lst.append([bm.verts.new((math.cos(a) * (ry + grow),
                                      math.sin(a) * (rx + grow), z))
                        for z in (z0, z1)])
    for k in range(steps - 1):
        (i0l, i0u), (i1l, i1u) = inner[k], inner[k + 1]
        (o0l, o0u), (o1l, o1u) = outer[k], outer[k + 1]
        bm.faces.new((o0l, o1l, o1u, o0u))          # the face of the band
        bm.faces.new((o0u, o1u, i1u, i0u))          # its top edge
        bm.faces.new((i0l, i1l, o1l, o0l))          # and its bottom
    for pair in (inner[0] + outer[0], outer[-1] + inner[-1]):
        bm.faces.new(pair[:2] + pair[2:][::-1])     # the two ends


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bm = bmesh.new()
    barrel(bm)

    # ---- THE BROW, AND A NOSE RIB ----
    #
    # NOT A CROSS. The first cut put a full band down the face and another
    # across it, standing well proud, and it came out as a crucifix on
    # somebody's head: the same fault the shields had before they were
    # repainted, and from the same instinct.
    #
    # What a great helm actually carries is a brow reinforce over the sights
    # and a short rib down the nose below them. The rib STOPS at the sight
    # line rather than running the length of the face, which is the whole
    # difference between armour and heraldry.
    band(bm, 13.3, 15.0, 12.45, 13.25, math.radians(52.0), 0.75)   # the brow
    band(bm, 3.0, 13.0, 12.2, 13.0, math.radians(5.5), 0.6, steps=3)  # the rib

    # ---- AND THE NORMALS MUST POINT OUT ----
    #
    # BLENDER RENDERS BOTH SIDES OF A FACE AND THE GAME DOES NOT. A ring loft
    # built by walking angles anticlockwise and stacking upward comes out wound
    # inside out, and Blender showed a perfectly good helm the whole time
    # because its viewport does not care. In the window, which culls back
    # faces, the same mesh is an empty shell: the sprite came out as a thin
    # crescent, which is the inside of the far wall seen through where the
    # outside should have been.
    #
    # `recalc_face_normals` walks the shell and turns every face outward, which
    # is right for anything closed and right enough for anything open with a
    # clear outside, and it costs one line.
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.faces.ensure_lookup_table()
    mesh = bpy.data.meshes.new('great_helm')
    bm.to_mesh(mesh)
    bm.free()
    helm = bpy.data.objects.new('great_helm', mesh)
    bpy.context.collection.objects.link(helm)
    bpy.context.view_layer.objects.active = helm
    helm.select_set(True)

    # ---- WHICH MATERIAL EACH FACE WEARS, BEFORE ANYTHING REORDERS THEM ----
    #
    # THE BEVEL RENUMBERS THE POLYGONS. The first cut appended the materials
    # and set the indices after applying it, so a count taken against the
    # mesh as it was built pointed at whatever the bevel had shuffled into
    # those slots: the carapace came out striped in two colours down its side.
    # Set here, before the modifier runs, and the bevel inherits each new face
    # from the face it grew out of.
    mesh.materials.append(bpy.data.materials.new('Soot'))
    mesh.materials.append(bpy.data.materials.new('Iron'))
    body = SIDES * 9 + 1
    for poly in mesh.polygons:
        poly.material_index = 0 if poly.index < body else 1

    # A BEVEL SO THE EDGES CATCH. Flat shading with hard corners is the look,
    # but a plate with a knife edge looks like paper; a tenth of a centimetre
    # gives every rim a highlight and costs almost nothing.
    bev = helm.modifiers.new('bevel', 'BEVEL')
    bev.width = 0.14
    bev.segments = 1
    bev.limit_method = 'ANGLE'
    bev.angle_limit = math.radians(40.0)
    bpy.ops.object.modifier_apply(modifier='bevel')

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')


    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'great_helm.obj')
    bpy.ops.wm.obj_export(filepath=path, export_selected_objects=False,
                          export_materials=True, export_uv=True,
                          export_normals=True, export_triangulated_mesh=False,
                          forward_axis='Y', up_axis='Z')
    xs = [v.co.x for v in mesh.vertices]
    ys = [v.co.y for v in mesh.vertices]
    zs = [v.co.z for v in mesh.vertices]
    print('GREAT HELM %d verts %d faces   %.1f deep x %.1f wide x %.1f tall cm -> %s'
          % (len(mesh.vertices), len(mesh.polygons),
             max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), path))


main()
