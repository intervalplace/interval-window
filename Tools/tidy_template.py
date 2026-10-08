# PUT AWAY THE TEMPLATE'S DEMO ROOM.
#
# This project was started from Unreal's TopDown template, and the template's
# own scenery is still in the level: twenty cubes, twenty quarter-cylinders,
# twelve ramps, a cylinder, a grey floor and a sky sphere, all in a forty-metre
# patch at the world origin. The island is nine hundred metres away, so nobody
# has ever seen them -- but they are fifty-five drawn actors and fifty-five
# shadow casters in every frame of a window that is careful about both, and a
# camera that ever reaches the origin finds a grey room floating in the sea.
#
# Found by Tools/audit_drawn.py, which asks the running window what it is
# actually drawing and subtracts what the tables name. Nothing else could have
# found them: every audit before it started from the tables, and a mesh no
# table names is a mesh no audit looks at.
#
# HIDDEN, NOT DELETED. The floor is what the pawn stands on before the island
# streams in, and hiding keeps collision where deleting does not.
#
# AND THE SKY SPHERE IS LEFT ALONE, deliberately. It is a 16.4 km ball at the
# origin and the island sits about a kilometre away, so it ENCLOSES the world:
# it is not a prop off in a corner like the cubes, it is behind everything. The
# window draws its own sky -- a sky atmosphere, volumetric clouds and an hour
# that passes -- and the template's mesh sky is very probably doing nothing at
# all behind it, but "very probably" is not a reason to remove the thing the
# horizon might be made of.
#
# THE TEST HAS NOW BEEN DONE, and the guess above was right. Hidden and shown
# at true midnight, the sky strip measured 32.4 against 34.3 -- about two
# levels out of thirty-four, which is nothing. `SM_SkySphere` carries
# `/Engine/EngineSky/M_SimpleSkyDome`, a fixed pale gradient that knows nothing
# about the hour, and it is comprehensively hidden behind the sky atmosphere
# the window draws for itself.
#
# It was suspected of being the reason night looked grey rather than dark. It
# was not: that was the exposure and a sky light with no colour in it, both of
# which are fixed in AIntervalHour and AIntervalAir. So the ball stays, because
# it still costs nothing and the reason to remove it turned out not to exist.
#
# WORTH KNOWING IF ANYONE LOOKS FOR IT AGAIN: its actor LABEL is `SM_SkySphere`
# and its object NAME is `StaticMeshActor_0`. A probe that searches names finds
# nothing and reports, wrongly, that there is no sky sphere in the world.
#
#   pyrun.sh tidy_template.py
import unreal

DEMO = ('SM_Cube', 'SM_Cylinder', 'SM_QuarterCylinder', 'SM_Ramp',
        'SM_Template_Map_Floor')
LEVEL = '/Game/TopDown/Lvl_TopDown'

unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
hid = 0
for a in sub.get_all_level_actors():
    if not isinstance(a, unreal.StaticMeshActor):
        continue
    c = a.static_mesh_component
    m = c.get_editor_property('static_mesh') if c else None
    if not m or str(m.get_name()) not in DEMO:
        continue
    a.set_actor_hidden_in_game(True)
    c.set_editor_property('hidden_in_game', True)
    c.set_cast_shadow(False)
    hid += 1

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
# WARNING, NOT LOG. A commandlet filters LogPython at Log verbosity and prints
# it at Display, so `unreal.log` from a script run this way says nothing at all
# -- which is indistinguishable from a script that did nothing.
unreal.log_warning('TIDY hid %d template actors' % hid)
