#!/bin/zsh
# Re-synthesise every sound the window makes, and import them.
#
# TWO SCRIPTS AND ONE IMPORTER. `ambience.py` makes the beds and themes -- the
# air a citizen is standing in, which cross-fades as they walk from one country
# into the next. `sfx.py` makes the sounds that belong to a PLACE: rain you can
# hear stop under a roof, a fire you can hear from across a market place, and a
# footfall that knows what it is standing on.
#
# THE SOURCES ARE NOT IN Content/. The editor watches that directory, and a
# re-synthesis used to greet the next editor with a "import these changed
# source files?" dialog -- a box nobody is there to click, under automation.
# They live in <project>/Audio and the importer reads them from there.
#
# The importer is editor Python, which wants the project to itself, so this
# closes the editor and brings it back.
set -e
SP="$(cd "$(dirname "$0")" && pwd)"
OUT="$(dirname "$SP")/Audio"
echo "--- the beds and the themes"
python3 "$SP/ambience.py" "$OUT" | tail -3
echo "--- rain, fire and footfalls"
python3 "$SP/sfx.py" "$OUT" | tail -3
echo "--- the sound of a deed"
python3 "$SP/deedsfx.py" "$OUT" | tail -1
echo "--- importing"
"$SP/pyrun.sh" import_audio.py
"$SP/ue.sh" | tail -1
echo "NOW RUN apply.py -- the look points at these by path"
