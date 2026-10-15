# THE SIREN, who was a tentacle and a ship.
#
#   blender --background --python Tools/blend/siren.py
#
# WHAT SHE WAS. `parts.WILD_STILL` pointed her at `Art/Wild/mermaid.glb`, and
# that file holds one mesh. It is called `Sea monster Scene`: forty-three
# thousand vertices of a kraken wrapped round a sailing ship, fetched by
# filename and never opened. Scaled to 1.87 m and stood on a beach it reads as
# a tentacle and a boat, which is exactly what it is.
#
# THIS IS THE THIRD TIME IN THIS PROJECT and the other two are written down in
# parts.py a few lines apart: `raven.glb` holds a blue and green bird called
# Ernest, and both bear files hold a mesh called `BearTrap_Open`. The lesson
# is the same each time and it is not about any one asset -- a file named for
# what you wanted is not evidence of what is in it.
#
# WHAT SHE IS, WHICH THE ENGINE IS UNUSUALLY CLEAR ABOUT.
#
#   she copies your levels, your weapon and your quiver, so the fight is
#   exactly even at any level, forever (§6br)
#   she is ALONE on the island
#   she does not wander: "a siren sits on her strand and sings" (§6ac)
#   she gives up the graver, "the mirror of yourself is the source of the one
#   item you cannot use on yourself"
#
# So she is not a decorative mermaid. She is a DROWNED DOUBLE -- the engine
# calls her the mirror of yourself twice -- and that is what the art says:
# pallid skin the colour of bone rather than of a person, hair soaked dark and
# hanging, and a tail that is cold sea-green and not a jewel. A reader who
# meets her should think "that is me, and it has been in the water".
#
# SEATED, because she sits. The silhouette is the brief: an upright torso with
# a long tail curling away beside her, which no other thing in this world has.
# Nothing else here is half one thing and half another.
#
# MEASURED. 187 cm from tail tip to crown, which is the length `parts.py`
# already intended for her -- the note there works back from a glTF scaled by
# a hundred to "a 1.87 m siren". Seated she stands about 120 of it.
#
# THREE MATERIALS, all already in `forge.PALETTE`: `Bone` for the skin,
# `EelSkin` for the tail, `Feather` for the hair.
import bpy
import bmesh
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'interval', 'Art', 'Forged')
if not os.path.isdir(OUT):
    OUT = os.path.abspath(os.path.join(HERE, '..', '..', 'Art', 'Forged'))

SKIN, SCALE_, HAIR = 0, 1, 2      # material slots, in the order appended below
SIDES = 7                          # odd, so no two faces of a limb are parallel


def tube(bm, pts, radii, mat, squash=1.0):
    """A tapered tube through a polyline, capped at both ends.

    The same skinning stones.py uses. A siren is tubes: a tail, a trunk, two
    arms and a neck, and the only thing that is not is the fluke.
    """
    rings = []
    for i, (p, r) in enumerate(zip(pts, radii)):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        d = [b[j] - a[j] for j in range(3)]
        n = math.sqrt(sum(v * v for v in d)) or 1.0
        d = [v / n for v in d]
        up = (0.0, 1.0, 0.0) if abs(d[2]) > 0.9 else (0.0, 0.0, 1.0)
        s = (up[1] * d[2] - up[2] * d[1], up[2] * d[0] - up[0] * d[2],
             up[0] * d[1] - up[1] * d[0])
        sn = math.sqrt(sum(v * v for v in s)) or 1.0
        s = [v / sn for v in s]
        t = (d[1] * s[2] - d[2] * s[1], d[2] * s[0] - d[0] * s[2],
             d[0] * s[1] - d[1] * s[0])
        ring = []
        for k in range(SIDES):
            ang = 2.0 * math.pi * k / SIDES
            c, si = math.cos(ang) * r, math.sin(ang) * r * squash
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
    return rings


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bm = bmesh.new()

    # ---- THE TAIL ----
    #
    # From the fluke, forward and up to the hips. It curls: a tail laid
    # straight is a fish somebody dropped, and the curl is what says she is
    # sitting rather than stranded.
    tail = []
    rad = []
    N = 9
    for i in range(N + 1):
        u = i / N                      # 0 at the fluke, 1 at the hips
        x = -78.0 + 86.0 * u + 14.0 * math.sin(u * 2.6)
        z = 6.0 + 46.0 * (u ** 1.5)
        tail.append((x, 0.0, z))
        # thin at the fluke, thickest two thirds along, narrowing into the hips
        rad.append(2.5 + 11.0 * math.sin(min(u * 1.25, 1.0) * math.pi) + 5.0 * u)
    tube(bm, tail, rad, SCALE_, squash=0.74)

    # ---- THE FLUKE ----
    #
    # Two flat lobes, not a cone. A tail fin read end-on is nothing at all, so
    # it is a plate: wide across, almost no thickness, and swept back.
    fx, fz = -78.0, 6.0
    lobes = []
    for sgn in (1.0, -1.0):
        a = bm.verts.new((fx + 6.0, 0.0, fz))
        b = bm.verts.new((fx - 24.0, sgn * 26.0, fz + 20.0))
        c = bm.verts.new((fx - 30.0, sgn * 9.0, fz - 6.0))
        d = bm.verts.new((fx - 8.0, sgn * 2.0, fz - 2.0))
        for tri in ((a, b, c), (a, c, d)):
            f = bm.faces.new(tri)
            f.material_index = SCALE_
        lobes.append((a, b, c, d))

    # ---- THE TRUNK ----
    #
    # Hips to shoulders, leaning back a little: she is propped on the strand,
    # not standing to attention.
    trunk = []
    trad = []
    M = 6
    for i in range(M + 1):
        u = i / M
        x = 8.0 - 7.0 * u
        z = 52.0 + 52.0 * u
        trunk.append((x, 0.0, z))
        # ---- THE WAIST IS THE WHOLE SILHOUETTE ----
        #
        # The first cut ran 13cm all the way up with a 3cm pinch, and she came
        # out a PILLAR: a slab with a head on it. A human reads as a human
        # because the waist is narrower than both the hips and the shoulders,
        # and at this size that one curve is doing all of the work. Hips 14,
        # waist 9, shoulders 15.
        trad.append(14.0 - 7.0 * math.sin(u * math.pi) ** 1.4 + 5.0 * u ** 2)
    tube(bm, trunk, trad, SKIN, squash=0.74)

    # ---- THE NECK AND HEAD ----
    # A THINNER NECK AND A BIGGER HEAD. Both were wrong the same way: the
    # neck was nearly as thick as the skull, which reads as a stump, and the
    # head was small enough to vanish. A head is about a seventh of a figure.
    neck = [(1.2, 0.0, 103.0), (0.6, 0.0, 111.0)]
    tube(bm, neck, [4.4, 4.0], SKIN)
    head = [(0.4, 0.0, 110.0), (0.0, 0.0, 119.0), (0.4, 0.0, 127.0),
            (1.0, 0.0, 131.0)]
    tube(bm, head, [6.4, 11.0, 9.0, 4.0], SKIN, squash=0.86)

    # ---- THE ARMS ----
    #
    # One down to the rock she is propped on, one across her. Asymmetry is
    # what keeps a figure from reading as a toy soldier, and it costs nothing.
    arm_a = [(-1.0, 13.0, 100.0), (2.0, 20.0, 84.0), (6.0, 20.0, 66.0),
             (10.0, 17.0, 56.0)]
    tube(bm, arm_a, [5.4, 4.2, 3.6, 3.0], SKIN)
    arm_b = [(-1.0, -13.0, 100.0), (4.0, -17.0, 88.0), (12.0, -13.0, 80.0)]
    tube(bm, arm_b, [5.4, 4.0, 3.2], SKIN)

    # ---- THE HAIR ----
    #
    # Over the crown and down the back, in one piece. Soaked hair hangs; it
    # does not fan. This is the darkest thing on her and it is what carries
    # the head at a distance, where the face is four pixels and the hair is a
    # shape.
    hair = [(1.5, 0.0, 132.0), (-4.0, 0.0, 126.0), (-9.0, 0.0, 113.0),
            (-11.0, 0.0, 99.0), (-11.0, 0.0, 86.0)]
    hrad = [8.0, 10.0, 8.6, 6.8, 4.6]
    tube(bm, hair, hrad, HAIR, squash=0.62)

    bm.verts.index_update()
    bm.normal_update()
    me = bpy.data.meshes.new('siren')
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new('siren', me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)

    # FACETED, like everything else here. See Tools/blend/README.md: there is
    # no subdivision in this pipeline and a smoothed low-poly figure reads as
    # a melted one.
    for p in ob.data.polygons:
        p.use_smooth = False

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0))
    bpy.ops.object.mode_set(mode='OBJECT')

    for mat in ('Bone', 'EelSkin', 'Feather'):
        ob.data.materials.append(bpy.data.materials.new(mat))

    path = os.path.join(OUT, 'siren.obj')
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
    length = math.hypot(hi[0] - lo[0], hi[2] - lo[2])
    print('SIREN %d verts %d faces  %.0f long x %.0f across x %.0f tall cm'
          % (len(ob.data.vertices), len(ob.data.polygons),
             hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]))
    print('      tail tip to crown %.0f cm (parts.py intended 187)' % length)


main()
