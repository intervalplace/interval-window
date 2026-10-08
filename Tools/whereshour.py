# Which actor is the hour, and what does it actually think ForceRain is?
#
# The C++ default was changed and nothing happened, which points at a
# LEVEL-PLACED actor whose saved value wins over the default. GetVisibleActors
# cannot see it -- the hour has no primitive of its own in frustum -- so ask
# the level itself.
import json, unreal
OUT = r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/hour.json"
found = []
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in sub.get_all_level_actors():
    n = a.get_class().get_name()
    if 'Interval' in n:
        row = {'class': n, 'path': a.get_path_name(), 'label': a.get_actor_label()}
        for p in ('ForceRain', 'RainRadius', 'NightBrightness'):
            try:
                row[p] = a.get_editor_property(p)
            except Exception:
                pass
        found.append(row)
json.dump(found, open(OUT, 'w'), indent=1)
unreal.log('HOUR REPORT WRITTEN')
