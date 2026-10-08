# WHERE THE ENGINE THINKS THE POINTER IS.
#
# Needed to map the real, operating-system cursor onto viewport coordinates.
# Screen Recording is not granted to this terminal, so the desktop cannot be
# photographed and the viewport's rectangle cannot be read off a picture; the
# engine is asked instead, which is the more honest answer anyway -- it reports
# where the click will actually LAND, not where a rectangle appears to be.
import json, unreal

S = ('/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/'
     'd4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/')

def probe(delta):
    out = {}
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        pc = unreal.GameplayStatics.get_player_controller(w, 0)
        got = pc.get_mouse_position()
        out['raw'] = str(got)
        # TWO FLOATS, NOT THREE. The Blueprint signature is a bool return plus
        # two out-params, but Unreal's Python binding hands back only the
        # out-params here -- (x, y). Reading it as (ok, x, y) silently used the
        # X as a boolean and threw on the missing third.
        if isinstance(got, (tuple, list)) and len(got) >= 2:
            out['x'] = float(got[-2]); out['y'] = float(got[-1])
        vp = unreal.WidgetLayoutLibrary.get_viewport_size(w)
        out['vw'] = float(vp.x); out['vh'] = float(vp.y)
        out['scale'] = float(unreal.WidgetLayoutLibrary.get_viewport_scale(w))
        # AND WHICH TILE THAT IS.
        #
        # Aiming a click at a pixel is fine for a button and useless for a
        # world: a session is played in tiles -- walk to 520,209, mine the seam
        # at 754,230 -- and the map from one to the other depends on where the
        # camera happens to be. The ground plane is z=0, so the cursor ray is
        # intersected with it and the answer divided by the tile size. This is
        # a question, not a deed; nothing is filed by asking it.
        # TWO SHAPES. Like `get_mouse_position`, this binding sometimes drops
        # the bool return and hands back just the two out-params, so the ray is
        # taken from the END of the tuple rather than from a fixed index.
        # AND WHERE THE CAMERA IS POINTING.
        #
        # The minimap turns with the camera now, so a click on it is read back
        # through the camera's yaw. Anything aiming at the map from outside
        # has to know the same number or it walks somewhere else entirely --
        # and this is the only place that can answer, because the yaw is the
        # camera manager's and not a thing the bridge has ever heard of.
        try:
            out['yaw'] = float(pc.player_camera_manager.get_camera_rotation().yaw)
        except Exception:
            pass
        # ---- AND FOUR POINTS THAT DO NOT DEPEND ON THE POINTER AT ALL ----
        #
        # `get_mouse_position` only answers after the viewport has PROCESSED a
        # mouse event, and moving the cursor is not one: the first read after a
        # click is right and every read after a bare move is None. So the
        # calibration that measured the ground by moving the pointer to three
        # places could take one sample and never the second, which surfaced as
        # "the probe is not reporting a ground hit: is PIE up?" -- naming the
        # one thing that was fine.
        #
        # `deproject_screen_position_to_world` takes the point as an argument.
        # Three fixed points and the centre are deprojected every tick, so the
        # ground map and the camera's offset can both be read without touching
        # the mouse. See `ground` and `aim` in hand.py.
        fixed = {}
        for name, (fx, fy) in (('a', (1400.0, 800.0)), ('b', (2600.0, 800.0)),
                               ('c', (1400.0, 1600.0)),
                               ('mid', (out['vw'] * 0.5, out['vh'] * 0.5))):
            try:
                r = pc.deproject_screen_position_to_world(fx, fy)
                if r and len(r) >= 2:
                    o, d = r[-2], r[-1]
                    if abs(d.z) > 1e-6:
                        t = -o.z / d.z
                        fixed[name] = [round(o.x + d.x * t, 1),
                                       round(o.y + d.y * t, 1)]
            except Exception:
                pass
        if fixed:
            out['fixed'] = fixed

        hit = pc.deproject_mouse_position_to_world()
        out['hit'] = str(hit)
        if hit and len(hit) >= 2:
            o, d = hit[-2], hit[-1]
            if abs(d.z) > 1e-6:
                t = -o.z / d.z
                gx, gy = o.x + d.x * t, o.y + d.y * t
                out['world'] = [round(gx, 1), round(gy, 1)]
                out['tile'] = [int(gx // 200.0), int(gy // 200.0)]
    except Exception as exc:
        out['err'] = str(exc)
    with open(S + 'mouse.json', 'w') as f:
        json.dump(out, f)

# ONE CALLBACK ONLY, AND THE NEWEST ONE. Each `py` exec gets a fresh namespace,
# so without a guard every reload would add another ticker -- but the first
# guard REFUSED the reload instead, which meant an edit to this file could not
# be loaded into a running editor at all. An hour went into wondering why a
# change to the probe changed nothing: the old function was still the one
# ticking, and it said "PROBE already armed" to say so.
#
# So the old one is taken off and the new one put on.
_old = getattr(unreal, '_ivl_probe', None)
if _old is not None:
    try:
        unreal.unregister_slate_post_tick_callback(_old)
    except Exception:
        pass
unreal._ivl_probe = unreal.register_slate_post_tick_callback(probe)
unreal.log('PROBE armed' if _old is None else 'PROBE re-armed, replacing the old one')
