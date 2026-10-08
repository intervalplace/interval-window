# LOOK AT A FORGED PIECE, without the editor and without the world.
#
#   blender --background --python Tools/blend/render.py -- <name> [out.png]
#
# The window is the real test and always will be, but it is a poor place to
# INSPECT one object: the piece is eight pixels across, the hour is whatever
# the world says, and getting a citizen to hold the thing means owning it. A
# turntable of three-quarter views on a plain ground answers "is the shape
# right" in one look and costs no play time.
#
# THE MATERIALS ARE THE PALETTE'S, read out of `forge.py`, so what comes out is
# the colour the world will draw. Anything named `Ember` is given an emission
# instead of a diffuse, because in the world it is an additive unlit emissive
# and a matte orange would be a lie about the one thing that piece does.
import bpy
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'Tools'))
try:
    from forge import PALETTE
except Exception:
    PALETTE = {}

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
name = argv[0] if argv else 'cinder_crown'
out = argv[1] if len(argv) > 1 else os.path.join('/tmp', name + '.png')

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=os.path.join(ROOT, 'Art', 'Forged', name + '.obj'),
                      forward_axis='Y', up_axis='Z')
obj = bpy.context.selected_objects[0]
obj.name = name

# ---- THE COLOURS THE WORLD WILL USE ----
for slot in obj.material_slots:
    m = slot.material
    if m is None:
        continue
    key = m.name.split('.')[0]
    r, g, b = PALETTE.get(key, (0.6, 0.6, 0.6))
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial')
    if key == 'Ember':
        # An additive emissive in the world, so an emission here. Bright
        # enough to bloom a little against the soot, which is what an ember
        # deep in a crack actually does.
        sh = nt.nodes.new('ShaderNodeEmission')
        sh.inputs['Color'].default_value = (1.0, 0.42, 0.10, 1.0)
        # NINE BLEW THEM WHITE. An ember is orange and an over-driven
        # emission is a light bulb; three and a half keeps the hue.
        sh.inputs['Strength'].default_value = 3.5
    else:
        sh = nt.nodes.new('ShaderNodeBsdfPrincipled')
        sh.inputs['Base Color'].default_value = (r, g, b, 1.0)
        sh.inputs['Roughness'].default_value = 0.72
    nt.links.new(sh.outputs[0], o.inputs['Surface'])

# ---- A PLAIN ROOM ----
#
# Dark, because every piece in this world is seen against ground and sky
# rather than against paper, and a burnt thing on white reads as a smudge.
world = bpy.data.worlds.new('room')
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.03, 0.03, 0.035, 1)

# ---- CENTIMETRES ARE NOT METRES ----
#
# Everything this project forges is authored in centimetres, because a citizen
# is 181 and every scale mistake here came from not measuring. Blender reads
# those numbers as METRES, so a 24 cm crown arrives 24 m across -- and the
# first render put the key light eighty-five "metres" away at a watt and a
# half per square metre. What came out was a black silhouette with the
# emission blown white, which reads as a fault in the mesh and was a fault in
# the arithmetic.
#
# So the piece is scaled to metres before anything is aimed at it, and the
# lights below are then ordinary numbers for an object you could hold.
obj.scale = (0.01, 0.01, 0.01)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

lo = min(v.co.z for v in obj.data.vertices)
hi = max(v.co.z for v in obj.data.vertices)
wide = max(max(abs(v.co.x), abs(v.co.y)) for v in obj.data.vertices)
span = max(hi - lo, wide * 2.0)

# How far the camera will stand, needed by the lamps above it.
dist = span * 3.4

key = bpy.data.objects.new('key', bpy.data.lights.new('key', 'AREA'))
# ---- LIT BY ARITHMETIC, NOT BY EYE ----
#
# Sixty watts at eighty-five centimetres on a quarter-metre object blew the
# whole crown white, which is the same failure as the first render in the
# other direction. An area lamp of P watts at distance d delivers roughly
# P / (4*pi*d^2); a surface of albedo a then renders near a * E * 0.5. For
# charred stone (a = 0.18) to land around a third of the way up the range,
# E wants to be about four, so P is about four times 4*pi*d^2.
#
# Written as the formula rather than the answer, so changing the framing does
# not silently change the exposure.
# MEASURED AND CORRECTED ONCE, rather than reasoned at twice. The estimate
# above came out about two and a half times hot -- charred stone of albedo
# 0.18 rendered at 0.78, which is beige. An area lamp is not a point source
# and the half in the formula was optimistic; 0.22 is what the picture says.
key.data.energy = 4.0 * (4.0 * math.pi * dist * dist) * 0.22
key.data.size = span * 1.6
key.location = (span * 1.6, -span * 1.9, span * 2.2)
key.rotation_euler = (math.radians(52), 0, math.radians(40))
bpy.context.scene.collection.objects.link(key)

fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'AREA'))
fill.data.energy = key.data.energy * 0.22
fill.data.size = span * 2.4
fill.location = (-span * 2.0, span * 1.2, span * 0.8)
fill.rotation_euler = (math.radians(75), 0, math.radians(-125))
bpy.context.scene.collection.objects.link(fill)

# THREE-QUARTER AND A LITTLE ABOVE, which is roughly how the window's own
# camera meets a thing on a citizen's head.
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
cam.data.lens = 70
cam.location = (dist * 0.72, -dist * 0.66, (lo + hi) * 0.5 + dist * 0.42)
cam.rotation_euler = (math.radians(63), 0, math.radians(47.5))
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam

sc = bpy.context.scene
# WHICHEVER EEVEE THIS BUILD HAS. Blender renamed it to BLENDER_EEVEE_NEXT
# and then back again, so the name is looked up rather than assumed -- a
# hard-coded one fails with an enum error and no picture.
_engines = sc.render.bl_rna.properties['engine'].enum_items.keys()
sc.render.engine = ('BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in _engines
                    else 'BLENDER_EEVEE')
sc.render.resolution_x, sc.render.resolution_y = 900, 900
sc.render.film_transparent = False
sc.render.filepath = out
# STANDARD, NOT AGX. Blender's default view transform desaturates anything
# bright, which turned an orange ember into a white one -- the same complaint
# twice over, once from the lighting and once from the tone map.
try:
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.exposure = 0.0
except Exception:
    pass
try:
    sc.eevee.use_bloom = True
except Exception:
    pass            # EEVEE Next moved bloom into the compositor; no matter
bpy.ops.render.render(write_still=True)
print('RENDERED %s  (%.1f x %.1f x %.1f cm) -> %s'
      % (name, wide * 200, wide * 200, (hi - lo) * 100, out))
