#!/usr/bin/env python3
"""Put a thing in the citizen's hand, in THIS WINDOW ONLY, to look at it.

The offsets for every tool and weapon were reasoned rather than looked at,
because a citizen carries nothing until they pick something up and picking
something up is a deed in a world other people live in. This changes the
window's own table and nothing else: no intent is sent, the world is not
asked, and the next frame from the bridge says exactly what it said before.

  tryhold.py iron-hatchet      # hold it while standing
  tryhold.py --off             # put it down again
"""
import json, os, subprocess, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
from parts import WEAR, kit, CUBE, ROCK

# THE TABLE THE WINDOW WILL ACTUALLY DRAW FROM, not a second copy of it.
#
# This used to import `WORN` out of parts.py, which stopped being the truth the
# day the item table moved into apply.py: it went on offering a KayKit hatchet
# long after the window had stopped owning one. The look asset is what the
# window reads, so it is what this reads.
def read_worn():
    t = call('get_properties', {'instance': {'refPath': LOOK}, 'properties': ['Worn']})
    return json.loads(json.loads(t)['returnValue'])['Worn']
LOOK = '/Game/Interval/IntervalLook.IntervalLook'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'

def call(tool, args):
    json.dump(args, open(SP + '/_h.json', 'w'))
    out = subprocess.run([sys.executable, SP + '/mcp.py', OBJ, tool, SP + '/_h.json'],
                         capture_output=True, text=True).stdout
    return json.loads(out)['result']['content'][0]['text']

def read_motions():
    t = call('get_properties', {'instance': {'refPath': LOOK}, 'properties': ['Motions']})
    return json.loads(json.loads(t)['returnValue'])['Motions']

motions = read_motions()

want = sys.argv[1] if len(sys.argv) > 1 else '--off'
WORN = read_worn()
named = {'hatchet': WORN.get('iron-hatchet'), 'pickaxe': WORN.get('iron-pickaxe'),
         'rod': WORN.get('rod'),
         # A block big enough to find, on the bone, with no offset at all --
         # so where it appears tells you what the bone is and whether the
         # attachment happened, in one look.
         'probe': kit(WEAR(CUBE, ROCK, 'hand_r', 0.30, 0.30, 0.30)),
         'probehead': kit(WEAR(CUBE, ROCK, 'head', 0.30, 0.30, 0.30))}
# SEVERAL AT ONCE. Every piece names its own bone, so a kit can be the
# concatenation of several kits and they all hang where they belong -- a sword
# in the right hand, a bow in the left, a helm on the head. One restart shows
# four things instead of one, which matters when a restart is the slow part.
GROUPS = {
    'arms': ['iron-sword', 'wooden-bow', 'iron-helm', 'iron-plate'],
    'work': ['pickaxe', 'rod', 'iron-spear', 'iron-mell'],
}
if want in GROUPS:
    pieces = []
    for w in GROUPS[want]:
        k = named.get(w) or WORN.get(w)
        if k:
            pieces += k['pieces']
    kit = {'pieces': pieces}
else:
    kit = named.get(want) or WORN.get(want)

still = dict(motions['still'])
if want == '--off' or not kit:
    still['bHoldsTool'] = False
    print('empty-handed')
else:
    still['held'] = kit
    still['bHoldsTool'] = True
    print('holding', want, 'with', len(kit['pieces']), 'pieces')
motions['still'] = still

# Lengths first, then contents -- see the note in apply.py.
import copy
was = read_motions()
grow = copy.deepcopy(was)
grow['still'] = dict(was['still'])
have_n = len(was['still'].get('held', {}).get('pieces', []))
need_n = len(still.get('held', {}).get('pieces', []))
if need_n != have_n:
    pieces = list(was['still'].get('held', {}).get('pieces', []))
    pad = pieces[-1] if pieces else still['held']['pieces'][0]
    while len(pieces) < need_n:
        pieces.append(copy.deepcopy(pad))
    grow['still']['held'] = {'pieces': pieces[:need_n]}
    call('set_properties', {'instance': {'refPath': LOOK},
                            'values': json.dumps({'Motions': grow})})
print(call('set_properties', {'instance': {'refPath': LOOK},
                              'values': json.dumps({'Motions': motions})}))
