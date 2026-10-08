# THE SWORN SASH: what a citizen wears when they have mastered their trade.
#
#   blender --background --python Tools/blend/sash.py
#
# WHY A MARK AT ALL. Mastery is the largest thing a citizen can do and the
# window said nothing about it: two people stood side by side, one of them a
# hundred in their own trade and the other a newcomer, and they looked the
# same. Asked for directly -- "I think we should paint something on the
# citizen when it reaches that fact".
#
# AND WHY THERE IS EXACTLY ONE OF THEM. The first design was a cord that gained
# a token per mastered craft, and it was wrong about the world: §5k of
# `engine.js` says "Nothing unsworn passes fifty and nothing outside your own
# trade passes seventy". `MASTERY` is a hundred and only a citizen's own SWORN
# calling can reach it, so nobody will ever hold two. Nothing in this world
# accumulates across crafts, and a mark that could grow would be telling a lie
# about the rules.
#
# The same note records that a cape once existed here and was repealed with the
# generalist it rewarded. This is not that cape coming back: the cape said you
# went far in one thing when going wide was the rival achievement, and going
# wide is no longer possible. Now there is only far.
#
# WHY A SASH AND NOT A SHOULDER PIECE. The wayfarer's hood already owns the
# head and drapes a mantle over both shoulders, and two marks fighting for one
# surface is two marks nobody can read. What is left, and what this camera
# actually sees, is the body: a sash is a single strong diagonal across it,
# which is the most legible shape there is on a figure ninety pixels tall, and
# it reads from the front, the back and the side. Under a mantle its lower half
# still shows, which is how cloth layers anyway.
#
# NINE OF THEM, NOT SEVENTEEN. The world has seventeen callings over nine
# skills. At this size the MATERIAL is what carries, and nine materials are
# nine things a person can learn to read across a market square; seventeen
# would be a colour chart. Which calling somebody swore is already a word in
# the interface. The skill is what the sash says.
import bpy
import bmesh
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', '..', 'Art', 'Forged'))

# skill -> the material it is cut from, which is what that trade handles all
# day. A key here must be a `forge.PALETTE` entry or `dress_forged.py` has
# nothing to make and the sash arrives grey.
CLOTH = {
    'woodcraft':    'Wood',      # the woodwright, the forester, the fletcher
    'earthcraft':   'Iron',      # the miner and the smith
    'shorecraft':   'Shell',     # the fisher and the cook
    'hearthcraft':  'Wheat',     # the farmer and the brewer
    'prowess':      'Steel',     # the fighter, the warden, the berserker
    'marksmanship': 'Keratin',   # the archer: horn, which is what a nock is
    'sorcery':      'Magic',     # the alchemist
    'mourning':     'Bone',      # the mourner
    'wayfaring':    'Leather',   # the cartographer and the runner
}


def band():
    """The sash: a strip over the left shoulder and down across the body.

    Swept as a ribbon along a path rather than built as a box, because a sash
    lies ON a body and a box would stand off it. Three-quarters of a turn
    around the torso, wider at the shoulder than at the hip, which is how the
    weight of one actually hangs.
    """
    bm = bmesh.new()
    # (t along the sash, angle round the body, height, radius out from spine,
    #  half-width of the strip)
    STEPS = 22
    rings = []
    for i in range(STEPS + 1):
        t = i / STEPS
        # From the left shoulder, forward across the chest, round to the right
        # hip: a little over half a turn, which is what makes it a diagonal
        # rather than a belt.
        a = math.radians(125.0 - 205.0 * t)
        z = 26.0 - 46.0 * t                      # shoulder down to hip
        r = 11.5 + 2.0 * math.sin(math.pi * t)   # bows out over the chest
        half = 3.4 - 1.3 * t                     # wide at the shoulder
        # The strip's own frame: along the path, and out from the body.
        out = (math.cos(a), math.sin(a), 0.0)
        # It leans as it falls, so the strip stays flat against the torso.
        lean = 0.42
        ring = []
        for s in (-1.0, 1.0):
            for d in (-0.55, 0.55):             # the thickness of the cloth
                ring.append(bm.verts.new((
                    out[0] * (r + d) - out[1] * 0.0,
                    out[1] * (r + d) + out[0] * 0.0,
                    z + s * half * lean + s * half * 0.9)))
        rings.append(ring)
    # Four verts a ring: front-in, front-out, back-in, back-out, in that order,
    # so the quads below close the strip into a solid with an edge.
    for i in range(len(rings) - 1):
        lo, hi = rings[i], rings[i + 1]
        for a, b in ((0, 1), (1, 3), (3, 2), (2, 0)):
            bm.faces.new((lo[a], lo[b], hi[b], hi[a]))
    bm.faces.new((rings[0][0], rings[0][1], rings[0][3], rings[0][2]))
    bm.faces.new((rings[-1][2], rings[-1][3], rings[-1][1], rings[-1][0]))
    me = bpy.data.meshes.new('sash')
    bm.to_mesh(me)
    bm.free()
    return bpy.data.objects.new('sash', me)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    o = band()
    bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)

    bpy.ops.object.shade_smooth()
    bpy.ops.object.modifier_add(type='WEIGHTED_NORMAL')
    bpy.context.object.modifiers["WeightedNormal"].keep_sharp = True
    bpy.ops.object.modifier_apply(modifier="WeightedNormal")

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')

    # ONE MESH, NINE MATERIALS. The shape of a sash does not depend on the
    # trade; only what it is cut from does. So this exports once and
    # `parts.py` hangs it nine times with a different hue on each, which is
    # nine material instances rather than nine meshes.
    o.data.materials.append(bpy.data.materials.new('Cloth'))

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'sworn_sash.obj')
    bpy.ops.wm.obj_export(filepath=path, export_selected_objects=False,
                          export_materials=True, export_uv=True,
                          export_normals=True, export_triangulated_mesh=False,
                          forward_axis='Y', up_axis='Z')
    xs = [v.co.x for v in o.data.vertices]
    ys = [v.co.y for v in o.data.vertices]
    zs = [v.co.z for v in o.data.vertices]
    print('SASH %d verts %d faces   %.1f x %.1f x %.1f cm -> %s'
          % (len(o.data.vertices), len(o.data.polygons),
             max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), path))
    print('  worn by nine skills: %s' % ', '.join(sorted(CLOTH)))


main()
