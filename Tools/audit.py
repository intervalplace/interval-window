#!/usr/bin/env python3
"""What the world has words for, against what this window draws.

The point of the exercise is not the number. It is that a word with no entry
is SILENTLY not drawn -- the window logs it once and carries on -- so the only
way to know the coverage is to ask both sides and subtract.
"""
import json, os, subprocess, sys
import rpc as _rpc
SP = os.path.dirname(os.path.abspath(__file__))
LOOK = '/Game/Interval/IntervalLook.IntervalLook'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
SCRATCH = ("/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/"
           "d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad")

def call(tool, args):
    # One session for the whole script; see Tools/rpc.py. This one always
    # talks to ObjectTools, so the toolset is bound here rather than passed.
    return _rpc.call(OBJ, tool, args)


look = json.loads(json.loads(call('get_properties', {
    'instance': {'refPath': LOOK},
    'properties': ['Props', 'Mobs', 'Worn', 'Motions', 'Scatter', 'Palisades']}))['returnValue'])
world = json.load(open(SCRATCH + '/world.json'))

props = set(look['Props'])
mobs = set(look['Mobs'])
worn = set(look['Worn'])

def report(title, words, have, *prefixes):
    """A word counts as drawn under ANY of the keys the window might use.

    The lookup prefers `type.kind` over `type`, and the same sub-kind can
    arrive under several types -- `banker` is a keeper, `bows` is both a keeper
    and a stall -- so checking one prefix reports two dozen false gaps.
    """
    words = sorted(set(words))
    tries = ('',) + prefixes
    missing = [w for w in words if not any((p + w) in have for p in tries)]
    print('%-14s %3d words, %3d drawn, %3d MISSING' % (title, len(words),
          len(words) - len(missing), len(missing)))
    if missing:
        print('    ' + ' '.join(missing))
    return missing

# A WORD WITH AN ENTRY IS NOT THE SAME AS A WORD THAT IS DRAWN.
#
# Every mob in this world has a row, and most of those rows are a cylinder out
# of /Engine/BasicShapes with a tinted material on it. A goblin that is a green
# cylinder counts as covered by any test that only asks "is there a row", which
# is how a bestiary of twenty-four can look finished and read as a car park.
# So the audit asks the second question too.
def placeheld(entry):
    def meshes(e):
        for key in ('mesh', 'skeletal'):
            v = e.get(key)
            if isinstance(v, dict) and v.get('refPath'):
                yield v['refPath']
        for piece in e.get('parts') or []:
            v = piece.get('mesh')
            if isinstance(v, dict) and v.get('refPath'):
                yield v['refPath']
        for piece in (e.get('held') or {}).get('pieces') or []:
            v = piece.get('mesh')
            if isinstance(v, dict) and v.get('refPath'):
                yield v['refPath']
        # AND `pieces` AT THE TOP LEVEL, which is the shape every WORN row has
        # and which this did not look at. The consequence was not a small
        # under-count: `meshes()` found nothing in a worn row, `bool(got)` was
        # therefore False, and all seventy of them scored as drawn -- while
        # being, to the last one, cylinders and spheres out of BasicShapes. The
        # audit reported "worn 0 of 70 are still an engine primitive" for as
        # long as the table has existed.
        # AND THE STAGES. A plot's crop lives in `stages`, not in `parts` --
        # bare earth, shoots, standing -- so a row whose bed is a flat cube and
        # whose plants are real meshes scored as a primitive. The same blindness
        # as `pieces`, one level deeper.
        for stage in e.get('stages') or []:
            for piece in stage.get('parts') or []:
                v = piece.get('mesh')
                if isinstance(v, dict) and v.get('refPath'):
                    yield v['refPath']
        for piece in e.get('pieces') or []:
            v = piece.get('mesh')
            if isinstance(v, dict) and v.get('refPath'):
                yield v['refPath']
            elif isinstance(v, str) and v and v != 'None':
                yield v
    got = list(meshes(entry))
    return bool(got) and all('/Engine/BasicShapes/' in m for m in got)

# WORDS WHERE A PRIMITIVE IS GENUINELY THE SHAPE OF THE THING.
#
# Counting a wall as unfinished work because it is a scaled cube makes this
# number meaningless, and a meaningless number gets ignored. `parts.HONEST`
# lists them WITH A REASON EACH; nothing may go in it because it is hard.
sys.path.insert(0, SP)
from parts import HONEST

def stand_ins(title, table):
    bad = sorted(k for k, v in table.items()
                 if isinstance(v, dict) and placeheld(v) and k not in HONEST)
    kept = sorted(k for k in table if k in HONEST)
    print('%-14s %3d of %3d are still an engine primitive' % (title, len(bad), len(table)))
    if bad:
        print('    ' + ' '.join(bad))
    if kept:
        print('    (%d drawn as primitives ON PURPOSE -- see parts.HONEST)' % len(kept))

print('=== what the world names, against what the window draws ===')
report('weapons', world['weapons'], worn)
report('armour', world['armour'], worn)
report('mobs', world['mobs'], mobs)
# ---- NODE TYPES, FROM THE ENGINE AND NOT FROM A SAMPLE ----
#
# This read `world['frameTypes']` and said "52 words, 52 drawn, 0 MISSING" for
# a long time, and it was measuring the wrong thing. `frameTypes` is the set of
# types that have been SEEN IN A FRAME -- a sample of a living world, not its
# vocabulary -- so a node type that exists and is merely rare came out as
# perfect coverage.
#
# Fourteen did. `cart`, `market`, `house`, `altar`, `bell`, `waystone`, `span`,
# `spanwork`, `crier`, `butt`, `dummy`, `fire`, `rock` and `eel-buck` are all in
# the engine's own `NODE_TYPES` and NONE of them had a row in the window at all.
# A cart is not obscure, either: §7do, it is what a dead hauler drops, with a
# shelf anybody may `unload`, and the window has never drawn one.
#
# The engine exports the list. Nothing else should ever be asked.
ENGINE_TYPES = json.loads(subprocess.run(
    ['node', '-e', 'process.stdout.write(JSON.stringify('
                   'require("../interval-bridge/engine.js").NODE_TYPES))'],
    cwd=os.path.dirname(SP), capture_output=True, text=True, check=True).stdout)
report('node types', ENGINE_TYPES, props)
report('node kinds', [k.split('.', 1)[1] for k in world['frameKinds']], props,
       'landmark.', 'keeper.', 'stall.', 'wall.')
report('keepers', world['keeperKinds'], props, 'keeper.', 'stall.')
report('stalls', world['stalls'], props, 'stall.', 'keeper.')

print()
print('=== and of the rows that exist, which are still stand-ins ===')
stand_ins('mobs', look['Mobs'])
stand_ins('props', look['Props'])
stand_ins('worn', look['Worn'])
