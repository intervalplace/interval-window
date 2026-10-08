#!/usr/bin/env python3
"""Which mesh each creature is drawn with, for the icon renderer.

`itemart.py` does this for the hundred and thirty items and the handbook draws
a picture beside every one of them. It drew none beside any creature, so a
reader met twenty-two names and no faces, which is exactly the gap the item
pictures exist to close.

THE ANSWER IS ALREADY IN THE LOOK. `IntervalLook.Mobs` is the table the window
draws the world's creatures from, so asking anything else would be a second
opinion about a settled fact. Each row is a kit of pieces the same way a
citizen's clothes are, and the first `/Game/...` path in it is the body.

The incursion's five disguises are left out: they are one creature wearing
five faces and the book names it once.

  beastart.py            writes beasts.json and says what is missing
"""
import json, os, re, sys

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
from rpc import call

S = ('/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/'
     'd4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/')
LOOK = '/Game/Interval/IntervalLook.IntervalLook'


def main():
    raw = call('editor_toolset.toolsets.object.ObjectTools', 'get_properties',
               {'instance': {'refPath': LOOK}, 'properties': ['Mobs']})
    mobs = json.loads(json.loads(raw)['returnValue'])['Mobs']
    out, lack, poses = {}, [], {}
    for name in sorted(mobs):
        # `incursion.haunt` and the rest are faces of `incursion`, not
        # creatures of their own.
        if '.' in name:
            continue
        row = mobs[name]
        found = re.findall(r'/Game/[A-Za-z0-9_]+(?:/[A-Za-z0-9_]+)*\.[A-Za-z0-9_]+',
                           json.dumps(row))
        if found:
            out[name] = found[0]
            # ---- AND THE POSE IT STANDS IN ----
            #
            # These are SKELETAL meshes and the pack rigs them flat: the bind
            # pose is a creature lying spread out, which is what the icon
            # renderer photographed and why the whole contact sheet read as
            # animals on their sides. The world never shows that pose because
            # it plays an idle the moment a beast is drawn.
            #
            # So the idle comes along with the mesh, and the renderer poses the
            # thing before photographing it, exactly as the world does.
            try:
                anim = row.get('motions', {}).get('still', {}).get('anim')
                if isinstance(anim, dict) and anim.get('refPath'):
                    poses[name] = anim['refPath']
            except Exception:
                pass
        else:
            lack.append(name)
    json.dump(out, open(S + 'beasts.json', 'w'), indent=1)
    json.dump(poses, open(S + 'beastposes.json', 'w'), indent=1)
    print('%d creatures, %d have a mesh' % (len(out) + len(lack), len(out)))
    if lack:
        print('  no mesh: %s' % ' '.join(lack))
    return 0


sys.exit(main())
