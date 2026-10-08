#!/bin/zsh
# REBUILD EVERYTHING, IN THE ONE ORDER THAT WORKS.
#
# Three separate traps live in this project and all three are silent. Running
# the scripts in any other order hits at least one of them and the only symptom
# is that the world comes out grey.
#
#   1. A master material is DELETED and re-created by its make_* script. Every
#      material instance parented to it then points at a trashed object and
#      renders as the default grey -- no warning, clean compile, and the
#      instance still reads back with all the right parameters. So every
#      dress_* script has to run after every make_* script.
#
#   2. The look asset holds hard references to meshes and materials, so it has
#      to be rebuilt last, after everything it points at exists.
#
#   2b. AND SO DOES THE LEVEL. The roof and wall materials are held by the
#      ground actor placed IN the level, not by the look -- apply.py copies
#      them out of it. Rebuilding those two masters without restarting the
#      editor first leaves the actor holding a trashed object, apply.py copies
#      the hole, and every roof in every settlement quietly stops being drawn.
#      Hence the restart below, which costs a minute and is not optional.
#
#   2c. AND `make_hang.py` IS A DUPLICATE OF make_flat's result, so it has to
#      run after it. Reorder the list below and the hanging master is built
#      from the PREVIOUS flat master, which is the one that was just deleted.
#
#   3. `make_mpc.py` must NOT delete the collection -- a material stores a
#      collection parameter's GUID, not its name, and a fresh collection mints
#      fresh GUIDs, which unbinds the weather from every material that reads
#      it. It updates in place for that reason; this is only a reminder.
#
# The bestiary is dressed by a commandlet, because re-parenting seventy-odd
# imported instances is not something the MCP surface can do in one call, and
# a commandlet needs the editor closed. It is therefore NOT in this script:
# run it separately when the beasts have gone grey.
set -e
SP="$(dirname "$0")"

# (make_post.py is NOT run here any more. It writes the level's own
#  PostProcessVolume, and `AIntervalAir` spawns itself unbound at priority ten
#  over the top of every property it sets. The air is tuned from the look
#  asset now -- see ExposureAt, FilmToe and Occlusion in apply.py.)

echo "--- the weather, updated in place"
python3 "$SP/make_mpc.py" | tail -1

echo "--- the master materials"
# `make_stars` and `make_bow` are in this list and were not: both are masters
# with no instances hanging off them, so nothing is orphaned by rebuilding
# them, and a sky shader that is only ever run by hand is a sky shader that
# silently falls a build behind.
for m in make_ground make_rain make_flame make_water make_glow \
         make_flat make_hang make_folk make_person_mat make_smoke make_thatch \
         make_tf make_stars make_bow; do
  printf '%-18s ' "$m"
  python3 "$SP/$m.py" 2>&1 | grep -E "compile:" | tr '\n' ' '; echo
done

echo "--- the instances, which the masters above have just orphaned"
for d in make_prop dress_nature dress_props dress_universal dress_armour make_dead; do
  printf '%-18s ' "$d"
  python3 "$SP/$d.py" 2>&1 | tail -1
done

# AFTER the materials, and for the same reason the instances are: the sprite
# renderers hold a pointer to M_IntervalSmoke, and make_smoke.py deletes and
# re-creates it. A Niagara system whose renderer points at a trashed material
# draws nothing at all, silently.
# THE EDITOR IS RESTARTED HERE, not for tidiness: see note 2b above.
echo "--- restarting, so the level re-resolves the masters just replaced"
"$SP/ue.sh" | tail -1

echo "--- the particle systems"
python3 "$SP/make_fx.py" | tail -2

echo "--- and the look asset, which points at all of it"
python3 "$SP/apply.py" | tail -1
