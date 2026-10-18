# WHAT IS ACTUALLY IN THE WORLD, counted rather than guessed.
#
# WHY. The frame sampler says the world costs 64 ms a frame and `r.ScreenPercentage
# 25` -- a sixteenth of the pixels -- does not move that number at all. A cost
# that does not care how many pixels it draws is not shading: it is per-OBJECT
# work on the CPU, which means the answer is a count, and a count can simply be
# taken.
#
# It reports actors by class and, for the ones that matter, how many primitive
# components hang off them and how many of those are instanced. A thousand
# instanced copies of one mesh is one draw call and nearly free; a thousand
# separate components is a thousand, and that is the difference this file
# exists to show.
#
#   echo "exec py .../census.py" >> play.cmd
import collections
import json

import unreal

OUT = ('/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/'
       'd4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/census.json')


def world():
    es = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    return es.get_game_world() or es.get_editor_world()


def main():
    w = world()
    actors = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor)
    by_class = collections.Counter()
    prims = 0
    instanced_comps = 0
    instances = 0
    static_comps = 0
    skeletal_comps = 0
    worst = []
    for a in actors:
        cls = str(a.get_class().get_name())
        by_class[cls] += 1
        here = 0
        for c in a.get_components_by_class(unreal.PrimitiveComponent):
            prims += 1
            here += 1
            if isinstance(c, unreal.InstancedStaticMeshComponent):
                instanced_comps += 1
                try:
                    instances += c.get_instance_count()
                except Exception:
                    pass
            elif isinstance(c, unreal.StaticMeshComponent):
                static_comps += 1
            elif isinstance(c, unreal.SkeletalMeshComponent):
                skeletal_comps += 1
        if here > 50:
            worst.append((here, cls, str(a.get_name())))
    worst.sort(reverse=True)
    report = {
        'actors': len(actors),
        'primitive_components': prims,
        'instanced_components': instanced_comps,
        'instances_inside_them': instances,
        'plain_static_components': static_comps,
        'skeletal_components': skeletal_comps,
        'by_class': by_class.most_common(14),
        'actors_with_most_components': worst[:12],
    }
    with open(OUT, 'w') as f:
        json.dump(report, f, indent=1)
    unreal.log('CENSUS %d actors, %d primitive components, %d plain static, '
               '%d instanced holding %d instances'
               % (len(actors), prims, static_comps, instanced_comps, instances))


main()
