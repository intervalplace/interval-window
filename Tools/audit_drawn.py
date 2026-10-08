#!/usr/bin/env python3
"""WHAT THE WINDOW IS ACTUALLY DRAWING, against what it means to draw.

THE MEASURE THAT WAS MISSING. `audit_art.py` walks the tables in parts.py and
checks that every mesh they name is dressed and the right size. That is the
wrong way round for one whole class of fault: a mesh that NO table names is a
mesh no audit looks at, and it draws perfectly happily.

Epic's own `SKM_Manny_Simple` was drawn ninety-five centimetres under every
citizen in this world for as long as the window has existed. It comes with the
TopDown template the project was started from, it hangs off the player pawn --
which is a camera and was never meant to have a body -- and from a top-down
view it reads as a pale figure crouched at the citizen's feet. Three audits
read clean the whole time. It was found by somebody watching the stream and
saying "looks like it's standing on the shoulders of a mannequin".

So this asks the running window what it has on screen and subtracts what the
tables say it should. It needs the world to be PLAYING -- it reads the live
components, not the assets -- and it changes nothing.

  audit_drawn.py            -- with the window in the world
"""
import json
import os
import subprocess
import sys

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import parts

S = ('/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/'
     'd4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/')
PROBE = S + 'audit_drawn_probe.py'
OUT = S + 'audit_drawn.json'

# THROUGH THE REMOTE HAND, because there is no Python over MCP -- see the note
# at the top of pyrun.sh -- and a commandlet would need the editor closed,
# which is the one state in which nothing is being drawn.
PROBE_SRC = '''
import json, unreal
S = %r
out = {'drawn': [], 'error': None}
try:
    sub = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    w = sub.get_game_world()
    seen = {}
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        for c in a.get_components_by_class(unreal.PrimitiveComponent):
            if not c.is_visible():
                continue
            asset = None
            for prop in ('skeletal_mesh_asset', 'static_mesh'):
                try:
                    v = c.get_editor_property(prop)
                    if v:
                        asset = str(v.get_name())
                        break
                except Exception:
                    pass
            if not asset:
                continue
            seen.setdefault(asset, [0, str(a.get_name())])
            seen[asset][0] += 1
    out['drawn'] = sorted([[k, v[0], v[1]] for k, v in seen.items()])
except Exception as e:
    out['error'] = str(e)[:300]
with open(S + 'audit_drawn.json', 'w') as f:
    json.dump(out, f, indent=1)
unreal.log('AUDITDRAWN %%d kinds' %% len(out['drawn']))
''' % (S,)


def named():
    """Every mesh name any table in parts.py mentions, however it spells it."""
    out = set()

    def eat(v):
        if isinstance(v, str):
            # A content path, a bare mesh name, or a word. The last segment of
            # a path is the asset, which is what the engine reports.
            out.add(v.split('/')[-1].split('.')[0])
        elif isinstance(v, dict):
            for x in v.values():
                eat(x)
        elif isinstance(v, (list, tuple)):
            for x in v:
                eat(x)

    for name in dir(parts):
        if name.startswith('_'):
            continue
        eat(getattr(parts, name))

    # AND apply.py's OWN NAMES, read as text. It cannot be imported: it talks
    # to a running editor from its first line. The outfits, the hair and the
    # animation library are named there and nowhere else, and without this
    # every citizen's own body came back as "drawn and named by nothing",
    # which is the sort of noise that gets an audit ignored.
    import re
    for src in ('apply.py',):
        try:
            text = open(os.path.join(SP, src)).read()
        except OSError:
            continue
        for quoted in re.findall(r"['\"]([A-Za-z0-9_./-]+)['\"]", text):
            out.add(quoted.split('/')[-1].split('.')[0])
    return out


def main():
    open(PROBE, 'w').write(PROBE_SRC)
    try:
        os.remove(OUT)
    except OSError:
        pass
    with open(S + 'play.cmd', 'a') as f:
        f.write('exec py %s\n' % PROBE)
    import time
    for _ in range(40):
        time.sleep(1)
        if os.path.exists(OUT):
            break
    if not os.path.exists(OUT):
        print('the window did not answer: is it PLAYING, and is the remote armed?')
        print('  Tools/into.sh puts it in the world with the hand armed.')
        raise SystemExit(1)
    got = json.load(open(OUT))
    if got.get('error'):
        print('the probe failed:', got['error'])
        raise SystemExit(1)
    ours = named()
    # THE ENGINE'S OWN SHAPES ARE NOT A FAULT. A cube is how a chimney is
    # drawn and the look asset says so; what matters is art nobody chose.
    skip = {'Cube', 'Sphere', 'Plane', 'Cylinder', 'Cone'}
    stray = [r for r in got['drawn'] if r[0] not in ours and r[0] not in skip]
    print('%d kinds of mesh on screen' % len(got['drawn']))
    print('%d of them are ones this window names' % (len(got['drawn']) - len(stray)))
    print()
    if not stray:
        print('nothing on screen that no table asked for')
        return
    print('DRAWN AND NAMED BY NOTHING:')
    for name, count, owner in stray:
        print('  %-28s %4d  on %s' % (name, count, owner))


if __name__ == '__main__':
    main()
