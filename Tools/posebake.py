#!/usr/bin/env python3
"""Bake a creature's idle into a static mesh, in Blender, for the ICON only.

WHY THIS EXISTS. The handbook photographs every creature, and eight of them
stand in a T-pose. They are not posed badly; they are not posed at all. A
skeletal mesh component in the editor never evaluates its animation, and five
ways of asking were tried and the bone did not move once -- see the long note
in `Tools/icons.py`. The way out needs a PoseableMeshComponent, and editor
Python in 5.8 cannot add one to an actor.

Blender has no such difficulty. The same .glb the creature was imported from
carries its idle, so the pose is applied there and what comes out is an
ordinary static mesh with the animation already in its vertices.

FOR THE PICTURE AND NOTHING ELSE. The world goes on drawing the rigged mesh
and animating it properly; this is a second copy that exists so a reader meets
a goblin standing rather than a goblin being measured for a coat.

THE SLOT NAMES ARE KEPT, because `dress_wild.py` made one material instance
per slot and named it `MW_<creature>_<slot>`. An export that renames them is
an export nobody can dress.

    blender --background --python Tools/posebake.py

It writes Art/Posed/<word>.obj, then `pyrun.sh import_posed.py` brings them in.
"""
import os
import sys

try:
    import bpy
    import mathutils
except ImportError:                      # not inside Blender
    sys.stderr.write(__doc__)
    sys.stderr.write('\nThis runs inside Blender:\n'
                     '  blender --background --python Tools/posebake.py\n')
    raise SystemExit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, 'Art', 'Wild')
OUT = os.path.join(ROOT, 'Art', 'Posed')

# word -> (source .glb, how tall it should stand in CENTIMETRES)
#
# The heights are the ones parts.py already chose and wrote down beside its
# own scale ratios: a goblin is a small person, a troll is the biggest thing
# that walks here, an imp is knee-high to either. Taken from there rather than
# invented, so the posed copy and the rigged one are the same size.
WANT = {
    'goblin':    ('goblin_c',  130.0),
    'troll':     ('ogre',      285.0),
    'scree-imp': ('monster_a',  90.0),
}

# ---- AND THE FIVE THAT HAVE NO ANIMATION OF THEIR OWN ----
#
# The risen, the barrow wight, the incursion and both gibbet corpses are built
# the way a citizen is: a bare body with an outfit following its pose. Neither
# half carries a clip, so there is nothing of theirs to bake -- but they are on
# the citizens' skeleton, and the Universal pack ships `Idle_Loop` for exactly
# that rig. Proved before it was built on: the action was assigned to the
# peasant's armature and a vertex of its body moved.
#
# The heights are 181 cm, which is what make_art.py measures a citizen at,
# times the scale the Mobs row already gives each of them.
PEOPLE = {
    'risen':        ('Superhero_Male_FullBody',   'Male_Peasant',      177.0),
    'barrow-wight': ('Superhero_Male_FullBody',   'Male_Knight_Cloth', 196.0),
    'gibbet-dead':  ('Superhero_Female_FullBody', 'Female_Peasant',    181.0),
    'gibbet-king':  ('Superhero_Male_FullBody',   'Male_Ranger',       214.0),
    'incursion':    ('Superhero_Male_FullBody',   'Male_Ranger',       208.0),
}
PEOPLE_ANIM = ('Anims/UAL1_Standard.glb', 'Idle_Loop')

# Male_Peasant.gltf and its kind also carry an `Icosphere`, which is a helper
# and not a person. It has 42 vertices and sampling it instead of the body is
# how an early probe reported that the pose had not moved anything.
NOT_A_PERSON = ('icosphere',)


# A QUARTER OF THE WAY IN, not frame zero. The first frame of an idle is very
# often still the rest pose, which is the thing this script exists to get away
# from; a quarter is past it and is not yet anywhere expressive.
ALONG = 0.25


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def idle_action():
    """The idle, and not a jump landing or a flinch that has `idle` in its name."""
    best = None
    for a in bpy.data.actions:
        n = a.name.lower()
        if 'idle' not in n:
            continue
        if any(bad in n for bad in ('jump', 'hit', 'react', 'to_idle', 'toidle')):
            continue
        # the plainest name wins, so `Idle` beats `Flying_Idle` beats the rest
        if best is None or len(a.name) < len(best.name):
            best = a
    return best


def obj_height(path):
    """How tall the written file actually is, in whatever unit it was written."""
    lo, hi = 1e9, -1e9
    try:
        with open(path) as f:
            for line in f:
                if line.startswith('v '):
                    z = float(line.split()[3])
                    lo = min(lo, z)
                    hi = max(hi, z)
    except OSError:
        return 0.0
    return hi - lo if hi > lo else 0.0


def export(word, meshes, tall_cm, how):
    # ---- TO THE SIZE THE WORLD ALREADY CHOSE ----
    #
    # Measured off the POSED mesh and not off the rig: a rig's bounds are its
    # animated extent, which is the trap parts.py records against these very
    # files. The depsgraph is asked for the evaluated mesh, which is the pose.
    # THE VERTICES, NOT THE BOUNDING BOX. `bound_box` on an evaluated object
    # did not follow the pose: the three creatures came out at 0.75, 0.79 and
    # 0.70 of the heights asked for, which is three different errors and so is
    # not a unit mistake. Walking the evaluated mesh is exact and costs a few
    # thousand vectors once.
    dg = bpy.context.evaluated_depsgraph_get()
    lo_z = 1e9
    hi_z = -1e9
    for o in meshes:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        for v in me.vertices:
            z = (ev.matrix_world @ v.co).z
            lo_z = min(lo_z, z)
            hi_z = max(hi_z, z)
        ev.to_mesh_clear()
    span = hi_z - lo_z
    if span <= 0:
        return '%s: no height' % word

    # Blender is in metres and this project is in centimetres.
    scale = (tall_cm / 100.0) / span

    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]

    os.makedirs(OUT, exist_ok=True)
    dest = os.path.join(OUT, word + '.obj')

    def write(g):
        # `apply_modifiers` is what bakes the armature into the vertices. Y
        # forward and Z up writes Blender's own axes unchanged, which is what
        # Tools/forge.py writes and so what import_forged already expects.
        bpy.ops.wm.obj_export(
            filepath=dest,
            export_selected_objects=True,
            apply_modifiers=True,
            export_materials=True,
            export_triangulated_mesh=True,
            forward_axis='Y',
            up_axis='Z',
            global_scale=g)

    # ---- AND THE FIT IS MEASURED OFF THE FILE, NOT PREDICTED ----
    #
    # The arithmetic says exported height is (measured span) x global_scale, so
    # one pass should land it. It does not: the three creatures came out at
    # 0.754, 0.787 and 0.701 of what was asked, which are THREE different
    # errors and so are not a unit mistake anywhere. Whatever the exporter is
    # doing between the evaluated mesh and the file, it is not worth another
    # hour of reading to find out, because the file itself can be measured and
    # the scale corrected in one more pass. Two exports of a few thousand
    # vertices costs nothing and cannot be wrong about its own result.
    write(scale * 100.0)
    got = obj_height(dest)
    if got > 0.0:
        write(scale * 100.0 * (tall_cm / got))
        got = obj_height(dest)
    return '%s -> %s  (%s, %.1f cm)' % (word, os.path.basename(dest),
                                        how, got)




def bake(word, stem, tall_cm):
    clear()
    src = os.path.join(SRC, stem + '.glb')
    if not os.path.exists(src):
        return '%s: no %s' % (word, src)
    bpy.ops.import_scene.gltf(filepath=src)

    arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    if arm is None:
        return '%s: no armature' % word
    act = idle_action()
    if act is None:
        return '%s: no idle among %s' % (word, [a.name for a in bpy.data.actions])

    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = act
    lo, hi = act.frame_range
    bpy.context.scene.frame_set(int(lo + (hi - lo) * ALONG))
    bpy.context.view_layer.update()

    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    if not meshes:
        return '%s: no mesh' % word

    return export(word, meshes, tall_cm, act.name)


def person(word, base, outfit, tall_cm):
    """A bare body plus the outfit that follows it, posed by a borrowed idle."""
    clear()
    uni = os.path.join(ROOT, 'Art', 'Universal')
    for path in (os.path.join(uni, 'Base', base + '.gltf'),
                 os.path.join(uni, 'Whole', outfit + '.gltf')):
        if not os.path.exists(path):
            return '%s: no %s' % (word, path)
        bpy.ops.import_scene.gltf(filepath=path)

    # WHAT THE ANIMATION PACK BRINGS WITH IT IS NOT PART OF THE PERSON. The
    # standard animation .glb carries its own preview figure, so importing it
    # adds `M_Main` and `M_Joints` to the scene and they were exported along
    # with the corpse. Only the meshes that were here BEFORE it arrived are
    # the person.
    mine = set(o.name for o in bpy.data.objects if o.type == 'MESH')
    anim, want = PEOPLE_ANIM
    bpy.ops.import_scene.gltf(filepath=os.path.join(uni, anim))
    act = next((a for a in bpy.data.actions if a.name == want), None)
    if act is None:
        return '%s: no %s in %s' % (word, want, anim)

    # EVERY armature, because the body and the outfit each brought their own
    # and both have to be told the same thing or the clothes stay behind.
    posed = 0
    for a in (o for o in bpy.data.objects if o.type == 'ARMATURE'):
        if a.animation_data is None:
            a.animation_data_create()
        try:
            a.animation_data.action = act
            # Blender 5 actions are slotted, and a slot has to be chosen for
            # this user or the assignment is accepted and does nothing.
            if getattr(act, 'slots', None):
                a.animation_data.action_slot = act.slots[0]
            posed += 1
        except Exception:
            pass
    if not posed:
        return '%s: no armature took the action' % word

    lo, hi = act.frame_range
    bpy.context.scene.frame_set(int(lo + (hi - lo) * ALONG))
    bpy.context.view_layer.update()

    meshes = [o for o in bpy.data.objects
              if o.type == 'MESH' and o.name in mine
              and not any(b in o.name.lower() for b in NOT_A_PERSON)]
    if not meshes:
        return '%s: no mesh' % word
    return export(word, meshes, tall_cm, '%s + %s' % (base, outfit))


def main():
    print('--- posebake')
    for word, (stem, tall) in sorted(WANT.items()):
        print('   ' + str(bake(word, stem, tall)))
    for word, (base, outfit, tall) in sorted(PEOPLE.items()):
        print('   ' + str(person(word, base, outfit, tall)))
    print('--- done')


main()
