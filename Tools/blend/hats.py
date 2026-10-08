# THE KEEPERS' HATS, which were engine primitives until somebody looked.
#
#   blender --background --python Tools/blend/hats.py
#
# Eighteen of the twenty-three keeper trades wore a shape out of
# /Engine/BasicShapes. Their bodies were right all along -- a proper skeletal
# mesh in peasant clothing -- and then a cone was parked at z=176, which is
# head height, in a thatch material. A person with a traffic cone on their
# head. It was found the way this project always finds these: by somebody
# playing and asking what the triangle was.
#
# There is precedent in `apply.py` for exactly this, about the plain `keeper`
# row being a cylinder "standing where a person should be", found by somebody
# asking what the cylinder in the corner was. That one was fixed. The per-trade
# hats were not.
#
# WHY AUTHORED AND NOT SOURCED. The kits have helmets -- Bucket_Helmet,
# Knight_Helmet, Helmet -- and those serve the trades that want metal on their
# heads. What no CC0 kit here has is civilian headwear: a straw hat, a flat
# cap, a tall pointed hat, a bee veil. So they are made, which is the standing
# rule when the art does not exist rather than settling for a scaled cube.
#
# FOUR SHAPES, FOURTEEN TRADES. The primitives already said what each was meant
# to be, and the sizes are taken from them rather than invented:
#
#   straw   a wide shallow cone in thatch      drover, fisher, shepherd
#   cap     a low cloth cylinder               banker, merchant, miller, toll
#   point   a tall narrow cone in cloth        wizard, mourner
#   veil    a wide TALL cone in thatch         beekeeper
#
# MEASURED. A head is about 22 cm across and a citizen is 181 cm, so a hat
# that sits ON a head has an opening near 23 and a brim wider than that by
# however much shade it is meant to give. The old cone was 48 cm across for
# the drover and that is a real wide-brimmed working hat, so it is kept.
import bpy
import bmesh
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', '..', 'Art', 'Forged'))

SEG = 16          # around. Twelve faceted visibly on the brim's outer edge.


def fresh():
    """An empty scene. Blender starts with a cube, a light and a camera."""
    bpy.ops.wm.read_factory_settings(use_empty=True)


def stack(bm, rings, capped=True):
    """Bridge a list of rings into a solid.

    Each ring is (z, radius). A radius of zero closes the shape to a point,
    which is what a pointed hat needs and what a fan of triangles gives; every
    other pair becomes a band of quads. Built this way rather than as a lathe
    modifier so the profile is a table somebody can read and change, which is
    the whole reason these live in the repository as scripts.
    """
    made = []
    for z, r in rings:
        if r <= 0.0001:
            made.append([bm.verts.new((0.0, 0.0, z))])
            continue
        loop = []
        for s in range(SEG):
            a = 2.0 * math.pi * s / SEG
            loop.append(bm.verts.new((math.cos(a) * r, math.sin(a) * r, z)))
        made.append(loop)
    bm.verts.ensure_lookup_table()
    for lower, upper in zip(made, made[1:]):
        if len(upper) == 1:                       # close to a point
            for s in range(SEG):
                bm.faces.new((lower[s], lower[(s + 1) % SEG], upper[0]))
        elif len(lower) == 1:
            for s in range(SEG):
                bm.faces.new((lower[0], upper[(s + 1) % SEG], upper[s]))
        else:
            for s in range(SEG):
                bm.faces.new((lower[s], lower[(s + 1) % SEG],
                              upper[(s + 1) % SEG], upper[s]))
    # A HAT IS CAPPED AND A VEIL IS NOT.
    #
    # Capping both ends makes a solid, which is right for a hat: an open rim
    # reads as a black crescent from above, and above is where this world is
    # looked at from. It is wrong for the veil. The first net was capped and
    # rendered as a bucket with a lid on it, because that is exactly what it
    # was. Cloth hanging off a brim is a sleeve, open at both ends.
    if capped:
        for end in (made[0], made[-1]):
            if len(end) > 1:
                bm.faces.new(end)
    return made


def build(name, rings, material, smooth=True, capped=True):
    bm = bmesh.new()
    stack(bm, rings, capped)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    if smooth:
        # Smooth with a weighted normal and sharp edges kept, so the brim's
        # rim stays a hard line while the crown rounds. Shading it flat makes
        # a sixteen-sided hat look like a sixteen-sided hat.
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
    zs = [v.co.z for v in ob.data.vertices]
    print('%-10s %3d verts %3d faces  %.0f cm across x %.0f tall -> %s'
          % (ob.name, len(ob.data.vertices), len(ob.data.polygons),
             max(xs) - min(xs), max(zs) - min(zs), filename))


# ---------------------------------------------------------------------------
# THE FOUR. z=0 is where the hat meets the head, so every one of these sits at
# the same offset on a citizen and the look's rows need one number, not four.

def straw():
    """A WIDE WORKING HAT, for people who stand in a field all day.

    The brim is what this is: 46 cm across, which is a real wide-brim, and it
    DROOPS. A flat brim reads as a disc and a drooping one reads as straw that
    has been rained on, which is the difference between a hat and a plate.
    """
    return [
        (-1.0, 0.0),          # under the brim, closed
        (-1.0, 23.0),         # the brim's outer edge, drooping below the band
        (1.6, 23.0),          # its thickness: straw is not paper
        (2.2, 13.0),          # back in to the crown
        (2.6, 11.6),          # the band
        (7.0, 10.6),
        (10.4, 8.0),
        (12.4, 4.2),
        (13.2, 0.0),          # the crown's low dome
    ]


def cap():
    """A FLAT CLOTH CAP with a short peak at the front.

    The peak is added after, as a separate ring stack, because a cap without
    one is a pudding basin. 27 cm across: it sits ON the head rather than over
    it, which is what separates a cap from a hat at a glance.
    """
    return [
        (0.0, 0.0),
        (0.0, 13.5),
        (1.4, 13.6),          # the roll of the band
        (3.0, 13.2),
        (6.2, 12.0),
        (8.4, 8.6),
        (9.4, 0.0),
    ]


def point():
    """A TALL TAPERING HAT. The wizard's, and the mourner's in another colour.

    42 cm of crown, which is most of a head again above the head, so it clears
    every other silhouette in a market square. It tapers to a soft point rather
    than a sharp one: a sharp tip is one vertex and reads as an artefact.
    """
    return [
        (-0.6, 0.0),
        (-0.6, 17.0),         # a modest brim, turned down
        (1.2, 16.4),
        (2.0, 11.4),          # the band
        (8.0, 10.2),
        (16.0, 8.2),
        (24.0, 6.0),
        (32.0, 3.8),
        (38.0, 2.0),
        (41.0, 0.9),
        (42.0, 0.0),          # soft point
    ]


def helm():
    """A KETTLE HAT: a brimmed war hat, for the trades that want iron on them.

    IT WAS A SKULLCAP AND THAT WAS THE WRONG SHAPE. Eight radii swept round
    with a brow band, which photographs as a smooth egg -- and worse, five
    trades wore the same egg, so a watchman, a collier and a miner were one
    silhouette. The band it was given to stop it being a boiled egg did not
    stop it being a boiled egg.

    THE KIT'S OWN HELMS WERE TRIED FIRST, which is what the old note here said
    should happen once a keeper's hat hung on the head bone rather than at a
    height above the tile. It does now, so `Bucket_Helmet2` was hung on it and
    photographed. It does not work, for a reason that has nothing to do with
    offsets: a great helm has a FACE, so its opening has to line up with one,
    and a keeper's head bone tilts down when they stand still. It came out
    pushed onto the chin with the wearer's hood out of the back of it. Half
    these citizens wear hoods and a bucket helm cannot be worn over a hood.

    A kettle hat can. It is a brim and a dome, it is symmetric, so it does not
    care which way a head is turned or tilted, it sits ON TOP of a hood the way
    the real thing was worn over a mail coif, and it is the right century. It
    is also the one medieval helm anybody recognises from its outline alone,
    which is what matters at the distance this world is usually seen from.

    37 cm across the brim and 21 tall. A real one is about that.
    """
    return [
        (-2.4, 0.0),
        (-2.4, 18.6),         # the brim's underside, out to the edge
        (0.0, 19.4),          # the rim turned up a little, so it takes a light
        (1.2, 18.4),
        (1.8, 13.6),          # and back in to the skull
        (3.2, 13.9),          # the brow band, standing proud of it
        (4.6, 13.2),
        (7.6, 12.6),
        (10.6, 11.4),
        (13.4, 9.6),
        (15.8, 7.0),
        (17.6, 3.8),
        (18.6, 0.0),          # a low dome, not a point
    ]


def veil():
    """THE BEEKEEPER'S HAT ITSELF: a wide brim and a taller crown.

    The veil is a SEPARATE piece (below), not the same stack carried downward.
    The first version did it in one mesh and it rendered as a bucket: a skirt
    the full width of the brim, straight-sided, in the same straw as the hat.
    A veil is a different fabric that HANGS, and the two things that say so are
    the taper and the colour. One mesh could have neither.
    """
    return [
        (-1.0, 0.0),
        (-1.0, 24.0),         # the brim, wider than the drover's
        (1.8, 24.0),
        (2.4, 13.0),
        (3.0, 11.6),
        (9.0, 10.8),
        (14.0, 8.4),
        (17.0, 4.4),
        (18.0, 0.0),
    ]


def net():
    """AND THE VEIL THAT HANGS OFF IT, to the shoulders.

    An OPEN SLEEVE, not a solid: see `stack`. The first one was capped at both
    ends and rendered as a bucket with a lid, which is what it was.

    The shape is what fabric does rather than what a cylinder does. It is
    tacked UNDER the brim at 21, so the brim overhangs it and you can see that
    it hangs rather than continues; it falls away to 24 where a hoop or the
    shoulders hold it out; and it gathers back to 18 at the hem. Eleven
    centimetres of movement across forty-two is enough to read at the distance
    this world is drawn from, and a straight-sided veil is not.
    """
    return [
        (0.0, 21.0),          # tacked under the brim, which overhangs it
        (-6.0, 23.0),
        (-16.0, 24.0),        # held out at its widest
        (-28.0, 22.4),
        (-38.0, 19.4),
        (-42.0, 18.0),        # gathered at the hem, on the shoulder
    ]


def main():
    made = []
    for name, profile, material, filename in (
        ('hat_straw', straw(), 'Wheat', 'hat_straw.obj'),
        ('hat_cap', cap(), 'Cloth', 'hat_cap.obj'),
        ('hat_point', point(), 'Cloth', 'hat_point.obj'),
        ('hat_helm', helm(), 'Iron', 'hat_helm.obj'),
        ('hat_veil', veil(), 'Wheat', 'hat_veil.obj'),
        # the veil hangs open at the hem, so it is not capped and not smoothed
        # into a solid: it is a sleeve of cloth, and shading it as one closed
        # body put a hard terminator across the front of it.
        ('hat_net', net(), 'Cloth', 'hat_net.obj'),
    ):
        fresh()
        ob = build(name, profile, material, capped=(name != 'hat_net'))
        save(ob, filename)
        made.append(name)
    print('%d hats written to %s' % (len(made), OUT))


main()
