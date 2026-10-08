# THE SHELL HELM, which is a crab's back and should look like one.
#
#   blender --background --python Tools/blend/shell_helm.py
#
# WHY IT NEEDED AUTHORING. It shared `Bucket_Helmet2` with the great helm: one
# cylinder doing duty for the two dearest helms in the world, so the armour a
# shorekeeper spends a season on looked the same as the armour a smith spends
# two star-alloy on, and both looked like a bucket.
#
# IT IS NOT METAL AND MUST NOT READ AS METAL. `shell-plate` and `shell-helm`
# are made from a crab's shell: §  the crab-shell line is the shorecraft
# answer to plate, and the whole point of it is that a fisher can armour
# themselves from what the water gives instead of buying iron. So this is a
# CARAPACE: wide, low, fluted from the crown outward, and scalloped along the
# bottom edge the way a shell's margin actually is. Nothing on it is a band or
# a rivet, because nobody forged it.
#
# MEASURED. A head is about 22 cm across. This is 26 cm across and 18 tall,
# which is deliberately wider and lower than the great helm's 25 by 27: a shell
# sits over the skull and flares, where a barrel drops past the jaw.
import bpy
import bmesh
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', '..', 'Art', 'Forged'))

SIDES = 24          # more than the great helm: the flutes need somewhere to sit
FLUTES = 8          # ridges radiating from the crown


def carapace(bm):
    """The shell, as stacked rings with a flute running through them.

    The flute is the whole character and it costs one cosine: the radius at
    each vertex is swelled and pinched around the ring, so the surface leaves
    the crown in ridges instead of as a dome. A shell with no flutes is a
    bowl, and a bowl is what was already there.

    The sights are let into the profile the same way the great helm's are,
    because this project has no boolean anywhere in it and a recess has to be
    built rather than cut.
    """
    # (z from the rim, radius across, radius front-to-back, flute depth,
    #  how far the front is pulled in)
    profile = [
        (0.0,  13.0, 12.4, 0.9, 0.0),   # the margin, widest and flared
        (2.4,  12.6, 12.0, 1.0, 0.0),
        (6.0,  12.2, 11.6, 1.1, 0.0),
        (9.4,  11.9, 11.3, 1.1, 1.3),   # the sight line
        (11.2, 11.6, 11.0, 1.0, 1.3),
        (13.0, 10.9, 10.3, 0.9, 0.0),
        (15.6,  8.4,  8.0, 0.6, 0.0),   # the crown turns over
        (17.4,  4.6,  4.4, 0.3, 0.0),
        (18.2,  1.4,  1.3, 0.0, 0.0),   # and closes
    ]
    rings = []
    for z, rx, ry, flute, sunk in profile:
        ring = []
        for i in range(SIDES):
            a = 2.0 * math.pi * i / SIDES
            # THE RIDGES. Eight of them, and they run all the way round rather
            # than stopping at the back: a carapace is the same creature from
            # every side, which is most of what tells it from a forged piece.
            swell = flute * math.cos(FLUTES * a)
            cut = sunk if math.cos(a) > 0.66 else 0.0
            ring.append(bm.verts.new((math.cos(a) * (ry + swell - cut),
                                      math.sin(a) * (rx + swell - cut * 0.5), z)))
        rings.append(ring)
    for lower, upper in zip(rings, rings[1:]):
        for i in range(SIDES):
            j = (i + 1) % SIDES
            bm.faces.new((lower[i], lower[j], upper[j], upper[i]))
    bm.faces.new(rings[-1])
    return rings


def margin(bm, rings):
    """The scalloped lower edge.

    A shell does not end in a straight cut. The bottom ring is dropped in a
    wave that follows the same eight flutes, so each ridge runs down to a point
    and each valley lifts: the edge reads as grown rather than sawn, and it is
    the detail that says crab from across a market square.
    """
    lower = rings[0]
    skirt = []
    for i in range(SIDES):
        a = 2.0 * math.pi * i / SIDES
        v = lower[i]
        drop = 2.6 * max(0.0, math.cos(FLUTES * a)) + 0.5
        skirt.append(bm.verts.new((v.co.x * 1.03, v.co.y * 1.03, v.co.z - drop)))
    for i in range(SIDES):
        j = (i + 1) % SIDES
        bm.faces.new((lower[i], skirt[i], skirt[j], lower[j]))
    return skirt


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bm = bmesh.new()
    rings = carapace(bm)
    margin(bm, rings)

    # ---- THE BROW SPINE ----
    #
    # One ridge over the sights, thicker than the others and carried further
    # forward. A crab has a raised orbital exactly here, and without it the
    # front of the shell is the same as the back, which makes the whole thing
    # read as a bowl put on backwards.
    spine = []
    for k in range(7):
        a = math.radians(-34.0 + 68.0 * k / 6.0)
        spine.append([bm.verts.new((math.cos(a) * (11.4 + grow),
                                    math.sin(a) * (12.0 + grow), z))
                      for grow, z in ((0.0, 11.0), (1.35, 11.4),
                                      (1.35, 12.6), (0.0, 13.1))])
    for k in range(6):
        a, b = spine[k], spine[k + 1]
        for lo, hi in ((0, 1), (1, 2), (2, 3)):
            bm.faces.new((a[lo], b[lo], b[hi], a[hi]))

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
    mesh = bpy.data.meshes.new('shell_helm')
    bm.to_mesh(mesh)
    bm.free()
    helm = bpy.data.objects.new('shell_helm', mesh)
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
    mesh.materials.append(bpy.data.materials.new('Shell'))
    mesh.materials.append(bpy.data.materials.new('Keratin'))
    body = SIDES * 8 + 1 + SIDES
    for poly in mesh.polygons:
        poly.material_index = 0 if poly.index < body else 1

    # A BEVEL SO THE EDGES CATCH. Flat shading with hard corners is the look,
    # but a plate with a knife edge looks like paper; a tenth of a centimetre
    # gives every rim a highlight and costs almost nothing.
    bev = helm.modifiers.new('bevel', 'BEVEL')
    bev.width = 0.09
    bev.segments = 1
    bev.limit_method = 'ANGLE'
    bev.angle_limit = math.radians(34.0)
    bpy.ops.object.modifier_apply(modifier='bevel')

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')


    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'shell_helm.obj')
    bpy.ops.wm.obj_export(filepath=path, export_selected_objects=False,
                          export_materials=True, export_uv=True,
                          export_normals=True, export_triangulated_mesh=False,
                          forward_axis='Y', up_axis='Z')
    xs = [v.co.x for v in mesh.vertices]
    ys = [v.co.y for v in mesh.vertices]
    zs = [v.co.z for v in mesh.vertices]
    print('SHELL HELM %d verts %d faces   %.1f deep x %.1f wide x %.1f tall cm -> %s'
          % (len(mesh.vertices), len(mesh.polygons),
             max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), path))


main()
