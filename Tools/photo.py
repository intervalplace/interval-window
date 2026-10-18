# A PHOTOGRAPH OF THE RUNNING WINDOW, from inside the running window.
#
# WHY THIS EXISTS. Every other way of getting a picture out of this project
# failed in one session: `see.sh` wants a probe that is not armed, `shot.sh`
# wants tool results that are not there, `CaptureViewport` hands back the
# editor's viewport rather than the game's, and `screencapture` grabs whatever
# window happens to be in front, which was a browser. So a whole afternoon of
# work on what the window DRAWS was done by reasoning about it, which is the
# one thing this project's own rules say not to do.
#
# The one capture path that is known to work here is the one the icon pipeline
# uses: a SceneCapture2D into a render target, exported as a PNG. icons.py
# spawns its camera with `EditorLevelLibrary.spawn_actor_from_class`, which
# REFUSES while the editor is in play mode -- "The Editor is currently in a
# play mode" -- and play mode is the only time there is a world to photograph.
#
# A capture component cannot be made from Python either: `register_component`
# and `add_component_by_class` are both absent from the 5.8 Python surface, so
# a component built there never joins the scene and never captures. Asked the
# editor rather than guessed a third time; `dir()` on the pawn and on the
# component is worth reading before trying.
#
# WHAT DOES WORK is the engine's own shot command against the viewport, with
# the viewport camera put where the picture wants it. `HighResShot` in a live
# session writes the GAME view, which is the thing to look at.
#
#   echo "exec py Tools/photo.py" >> play.cmd          the citizen's own view
#   INTERVAL_PHOTO_AT=1 echo ...                       see below
#
# Settings, all through the environment so no edit is needed to take a
# different picture:
#
#   INTERVAL_PHOTO_OUT    where to write it (default the scratchpad)
#   INTERVAL_PHOTO_SIDE   pixels, square (default 1024)
#   INTERVAL_PHOTO_NEAR   metres back from what is being looked at (default 0,
#                         which means the citizen's own camera, not a close-up)
#   INTERVAL_PHOTO_OF     part of a skeletal mesh's name to look at instead,
#                         e.g. Superhero. The nearest one wins.
#   INTERVAL_PHOTO_AT     "x,y" IN TILES: which figure to mean. The world's own
#                         coordinates, so `mestate.sh` says where a citizen is
#                         and this points at them. Without it the nearest
#                         figure to the camera wins, which in a simulate
#                         session is whoever the free camera drifted near.
#   INTERVAL_PHOTO_HIGH   centimetres up from the figure's feet to aim at
#                         (default 110, which is a person's hands)
#   INTERVAL_PHOTO_BONE   aim at this bone instead of a height off the floor.
#                         `hand_r` is the fist everything is hung on, so this
#                         is how to look at a grip rather than at a person.
#   INTERVAL_PHOTO_ROUND  degrees round the figure to stand, 0 being IN FRONT
#                         of them and 90 at their left shoulder. Relative to
#                         the figure's own facing, because "north" is not a
#                         side of a person and a citizen who turns would
#                         otherwise take the picture with them.
#                         A grip has to be looked at from more than one side:
#                         a weapon pointing straight at the camera reads as
#                         correct from exactly one angle and is not.
import math
import os
import unreal

OUT = os.environ.get(
    'INTERVAL_PHOTO_OUT',
    '/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/'
    'd4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad')
SIDE = int(os.environ.get('INTERVAL_PHOTO_SIDE', '1024'))
NEAR = float(os.environ.get('INTERVAL_PHOTO_NEAR', '0'))
OF = os.environ.get('INTERVAL_PHOTO_OF', '')
AT = os.environ.get('INTERVAL_PHOTO_AT', '')
HIGH = float(os.environ.get('INTERVAL_PHOTO_HIGH', '110'))
BONE = os.environ.get('INTERVAL_PHOTO_BONE', '')
ROUND = float(os.environ.get('INTERVAL_PHOTO_ROUND', '0'))
NAME = os.environ.get('INTERVAL_PHOTO_NAME', 'photo')


def world():
    es = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    return es.get_game_world() or es.get_editor_world()


def closest_figure(w, here, want):
    """The nearest skeletal mesh whose own name carries `want`."""
    best, far = None, 1e18
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
            m = c.skeletal_mesh
            if not m or want.lower() not in str(m.get_name()).lower():
                continue
            at = c.get_world_location()
            d = (at - here).length()
            if d < far:
                best, far = c, d
    return best, far


def main():
    w = world()
    cam = unreal.GameplayStatics.get_player_camera_manager(w, 0)
    here = cam.get_camera_location() if cam else unreal.Vector(0, 0, 500)
    if AT:
        # A TILE IS TWO METRES and a tile's corner is its index times that.
        tx, ty = (float(v) for v in AT.split(','))
        here = unreal.Vector(tx * 200.0, ty * 200.0, 0.0)

    if OF:
        comp, how_far = closest_figure(w, here, OF)
        if not comp:
            unreal.log_warning('PHOTO: nothing here is a %s' % OF)
            return
        if BONE:
            at = comp.get_socket_location(BONE)
            unreal.log('PHOTO: aimed at the bone %s' % BONE)
        else:
            at = comp.get_world_location() + unreal.Vector(0, 0, HIGH)
        back = max(NEAR, 0.4) * 100.0
        # ROUND THE FIGURE BY CHOICE, not by wherever the camera happened to
        # be: pointed at a citizen's own tile the two are the same point, and
        # the first cut of this fell back to due north every time and
        # photographed the same shoulder twice.
        rad = math.radians(ROUND + comp.get_world_rotation().yaw + 180.0)
        toward = unreal.Vector(math.cos(rad), math.sin(rad), 0.0)
        where = at - toward * back + unreal.Vector(0, 0, back * 0.25)
        facing = unreal.MathLibrary.find_look_at_rotation(where, at)
        unreal.log('PHOTO: %s, %.1f m from the camera'
                   % (str(comp.skeletal_mesh.get_name()), how_far / 100.0))
        # THE VIEWPORT IS THE CAMERA. In a simulate session this is the free
        # camera, and the shot command photographs whatever it sees.
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(where, facing)

    # The shot lands in Saved/Screenshots; the caller is told the name to look
    # for rather than left to find it.
    unreal.SystemLibrary.execute_console_command(
        None, 'HighResShot %dx%d filename=%s' % (SIDE, SIDE, NAME))
    unreal.log('PHOTO asked for %s.png under Saved/Screenshots' % NAME)


main()
