# A contact sheet of one item at several rotations, so a pose can be CHOSEN.
#
# WHY THIS EXISTS. `icons.py` turns anything with a long axis onto one
# diagonal, and leaves anything roughly cubic exactly as its mesh was
# authored, on the reasoning that "for those the three-quarter view is already
# the readable one". That holds only while everything cubic was authored the
# same way up, and the helms were not: four come from an OpenGameArt kit lying
# on their backs and two are forged by this project standing upright, so the
# armour page printed four helms on their backs beside two standing.
#
# `parts.py` knows the answer for WEARING one -- the kit helms carry
# roll=-90 -- but that rotation is in BONE space, where X runs along the bone,
# and the icon camera is in world space. It cannot be lifted across.
#
# So the pose is chosen the way this project chooses anything it cannot
# derive: by looking at it. This renders one word at every rotation in a list
# and writes them into the scratchpad to be tiled and read.
#
#     Tools/pyrun.sh standprobe.py
#
# Edit WORDS and TRIES below. The answer goes in `STAND` in icons.py.
import json
import os
import sys

import unreal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

S = ('/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/'
     'd4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/')
OUT = S + 'standprobe'
SIDE = 256
FAR = 200000.0

WORDS = ['iron-helm', 'steel-helm', 'quick-helm', 'gold-helm',
         'great-helm', 'shell-helm']

# (roll, pitch, yaw) -- unreal.Rotator's own order, which is NOT pitch first.
TRIES = [
    (0.0, 0.0, 0.0),
    (-90.0, 0.0, 0.0),
    (-90.0, 0.0, 90.0),
    (-90.0, 0.0, 180.0),
    (-90.0, 0.0, 270.0),
    (90.0, 0.0, 0.0),
    (0.0, -90.0, 0.0),
    (0.0, 90.0, 0.0),
]


def world():
    es = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    return es.get_game_world() or es.get_editor_world()


_target = None


def target():
    global _target
    if _target is None:
        _target = unreal.RenderingLibrary.create_render_target2d(
            SIDE, SIDE, unreal.TextureRenderTargetFormat.RTF_RGBA8)
    return _target


def shoot(w, mesh_path, name, turn, tag):
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not mesh:
        return '%s: no mesh at %s' % (name, mesh_path)
    if hasattr(mesh, 'get_bounding_box'):
        b = mesh.get_bounding_box()
    else:
        sb = mesh.get_bounds()
        o, e = sb.origin, sb.box_extent
        b = unreal.Box(unreal.Vector(o.x - e.x, o.y - e.y, o.z - e.z),
                       unreal.Vector(o.x + e.x, o.y + e.y, o.z + e.z))
    size = b.max - b.min
    mid = (b.max + b.min) * 0.5
    reach = max(size.x, size.y, size.z)
    if reach <= 0:
        return '%s: no size' % name

    # The same camera icons.py stands an ITEM in front of.
    look = unreal.Rotator(0.0, -30.0, 135.0)
    fwd = look.get_forward_vector()
    here = unreal.Vector(FAR, FAR, FAR)
    spun = unreal.MathLibrary.greater_greater_vector_rotator(
        unreal.Vector(mid.x, mid.y, mid.z), turn)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, here - spun)
    actor.set_actor_rotation(turn, False)
    cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SceneCapture2D, here, unreal.Rotator(0, 0, 0))
    try:
        c = cam.get_component_by_class(unreal.SceneCaptureComponent2D)
        c.projection_type = unreal.CameraProjectionMode.ORTHOGRAPHIC
        c.texture_target = target()
        c.set_editor_property('capture_every_frame', False)
        c.set_editor_property('capture_on_movement', False)
        c.set_editor_property('always_persist_rendering_state', True)
        cam.set_actor_rotation(look, False)
        cam.set_actor_location(here - fwd * (reach * 3.0), False, False)
        right, up = look.get_right_vector(), look.get_up_vector()
        span = 0.0
        for cx in (b.min.x, b.max.x):
            for cy in (b.min.y, b.max.y):
                for cz in (b.min.z, b.max.z):
                    v = unreal.MathLibrary.greater_greater_vector_rotator(
                        unreal.Vector(cx - mid.x, cy - mid.y, cz - mid.z), turn)
                    span = max(span, abs(v.dot(right)), abs(v.dot(up)))
        c.ortho_width = max(span * 2.0 * 1.08, 0.01)
        c.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
        c.show_flag_settings = [
            unreal.EngineShowFlagsSetting(show_flag_name=f, enabled=False)
            for f in ('Lighting', 'Tonemapper', 'Bloom', 'EyeAdaptation',
                      'AntiAliasing', 'Fog', 'AtmosphericFog', 'MotionBlur',
                      'ToneCurve', 'ColorGrading', 'ScreenSpaceReflections',
                      'AmbientOcclusion')]
        c.capture_scene()
        c.capture_scene()
        unreal.RenderingLibrary.export_render_target(
            w, c.texture_target, OUT, '%s__%s.png' % (name, tag))
        return None
    finally:
        unreal.EditorLevelLibrary.destroy_actor(actor)
        unreal.EditorLevelLibrary.destroy_actor(cam)


def main():
    os.makedirs(OUT, exist_ok=True)
    items = json.load(open(S + 'items.json'))['have']
    w = world()
    errs = []
    for name in WORDS:
        path = items.get(name)
        if not path:
            errs.append('%s: not in items.json' % name)
            continue
        for i, t in enumerate(TRIES):
            e = shoot(w, path, name, unreal.Rotator(*t), '%d' % i)
            if e:
                errs.append(e)
    print('STANDPROBE wrote %d words x %d tries into %s'
          % (len(WORDS), len(TRIES), OUT))
    for e in errs:
        print('  ! ' + e)


main()
