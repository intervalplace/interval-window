#!/usr/bin/env python3
"""Every word the world can make, against every word the window can draw.

THE FAR SIDE OF A TRANSFORMATION IS THE PART THAT GOES UNSEEN.

The window already reports what it cannot draw, once per word per rebuild:

    grep "no mesh for it" /tmp/ue.log | sort -u

and that report is the better instrument for anything standing in the world
right now. But it can only speak about what IS standing. A word that a node
only BECOMES has nothing standing to report: `bell` wants twelve pulls and
three hands, `span` wants ten thousand planks. Both were missing from the
window and neither could have been found by looking at the world as it is.

So this asks the question from the other end: take every word the engine can
produce, including the ones it can only produce after a transformation, and
check each against the look asset that the window actually reads.

THE LOOK ASSET, NOT parts.py. Reading the Python tables to answer this got it
wrong twice in one hour: it missed NATURE_PROPS, so it called `quick-rock`
undrawn for the wrong reason, and it accused `palisade`, which the Palisades
table had all along. The asset is what the window reads and so the asset is
what gets asked.

Needs the editor up. Nothing here touches the world or the look; it reads.

  undrawn.py
"""
import json, os, re, subprocess, sys

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import rpc as _rpc

BRIDGE = os.path.join(os.path.dirname(os.path.dirname(SP)), 'interval-bridge')
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
LOOK = '/Game/Interval/IntervalLook.IntervalLook'
TABLES = ['Props', 'PropsUpper', 'Palisades', 'Scatter', 'Roofs', 'Mobs']


def drawable():
    """Every bare word the look asset answers to."""
    t = _rpc.call(OBJ, 'get_properties',
                  {'instance': {'refPath': LOOK}, 'properties': TABLES})
    d = json.loads(json.loads(t)['returnValue'])
    words = set()
    for table in TABLES:
        v = d.get(table)
        if isinstance(v, dict):
            words.update(v)
        elif isinstance(v, list):
            for row in v:
                if isinstance(row, dict):
                    for key in ('word', 'kind', 'name'):
                        if row.get(key):
                            words.add(row[key])
    # `wall.roofed` is a sort of `wall`, and a sort answers for its word.
    return set(w.split('.')[0] for w in words)


def makeable():
    """Every word the engine can stand up, by whatever route."""
    out = subprocess.run(
        ['node', '-e', "const E=require('./engine.js');"
         "console.log(JSON.stringify({n:E.NODE_TYPES,m:Object.keys(E.MOB_STATS)}))"],
        cwd=BRIDGE, capture_output=True, text=True, check=True)
    got = json.loads(out.stdout.strip().splitlines()[-1])
    words = {}
    for w in got['n']:
        words[w] = 'node type'
    for w in got['m']:
        words.setdefault(w, 'mob')
    # AND WHAT A NODE BECOMES, which is in no list at all: the engine simply
    # writes the new word onto the node. `bellwork` becomes `bell` and
    # `spanwork` becomes `span`, and those were the two that were missing.
    src = open(os.path.join(BRIDGE, 'engine.js'), encoding='utf-8').read()
    for w in re.findall(r"\.type = '([a-z-]+)'", src):
        words.setdefault(w, 'what a node becomes')
    return words


def main():
    can_draw = drawable()
    missing = [(w, why) for w, why in sorted(makeable().items())
               if w not in can_draw]
    print('the window can draw %d words' % len(can_draw))
    if not missing:
        print('every word the world can make has something to draw it')
        return 0
    print('THE WORLD CAN MAKE THESE AND THE WINDOW DRAWS NOTHING:')
    for w, why in missing:
        print('    %-20s %s' % (w, why))
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
