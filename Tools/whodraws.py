#!/usr/bin/env python3
"""whodraws.py: which table actually owns a word, and which rows are dead.

parts.py builds the look out of several tables, and the later ones WIN. So a
row can be edited, reasoned about and commented at length while nothing in the
world is drawn from it. That has now cost time twice:

  * `landmark.haystack` was composed into a base course, a rope and a cone.
    The Village kit's `Hay1` is handed to it further down the file, so the
    photograph came back without a pixel changed.
  * `spoil-heap` and `ore-heap`, the same, against the Nature kit's rocks.

CLAUDE.md already says to test through the window's own interface rather than
by reading the tables. This is that rule for this file: it asks the LOOK ASSET
what it ended up with, after every table has had its turn.

    python3 Tools/whodraws.py                 every word, and what draws it
    python3 Tools/whodraws.py stump heap      only words matching these
    python3 Tools/whodraws.py --dead          rows in parts.py nothing reads

`--dead` is the one to run before authoring parts for anything. It lists every
word that parts.py gives a composed shape to and that the applied table then
draws from a kit mesh or with no parts at all, which means the authoring would
go nowhere.
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpc

LOOK = '/Game/Interval/IntervalLook.IntervalLook'
TABLES = ('Props', 'PropsUpper')


def applied(table):
    r = rpc.call('editor_toolset.toolsets.object.ObjectTools', 'get_properties',
                 {'instance': {'refPath': LOOK}, 'properties': [table]})
    d = json.loads(json.loads(r)['returnValue'])[table]
    return d if isinstance(d, dict) else {}


def where(mesh):
    if '/Engine/BasicShapes/' in mesh:
        return 'primitive'
    if '/Game/Interval/' in mesh:
        return 'kit'
    return 'none' if not mesh or mesh == 'None' else 'other'


def rows():
    out = {}
    for t in TABLES:
        for w, row in applied(t).items():
            if not isinstance(row, dict):
                continue
            mesh = row.get('mesh') or {}
            mesh = mesh.get('refPath', '') if isinstance(mesh, dict) else str(mesh)
            out[w] = (mesh, len(row.get('parts') or []), len(row.get('stages') or []))
    return out


def main():
    args = [a for a in sys.argv[1:]]
    dead = '--dead' in args
    args = [a for a in args if not a.startswith('--')]
    live = rows()

    if dead:
        # what parts.py THINKS it composes
        import parts
        authored = {}
        for name in dir(parts):
            t = getattr(parts, name)
            if not isinstance(t, dict):
                continue
            for w, row in t.items():
                if isinstance(row, dict) and row.get('parts'):
                    authored[w] = (name, len(row['parts']))
        print('rows parts.py composes that the window does not draw from:')
        n = 0
        for w, (tbl, k) in sorted(authored.items()):
            for key in (w, 'landmark.' + w):
                if key not in live:
                    continue
                mesh, got, stages = live[key]
                if got == 0 and stages == 0:
                    print('   %-24s %-16s %d part(s) authored, %s drawn as %s'
                          % (key, tbl, k, '0 drawn,', where(mesh)))
                    n += 1
        print('%d dead row(s)' % n)
        return

    print('%-26s %-10s %-44s %s' % ('word', 'drawn by', 'mesh', 'parts'))
    for w in sorted(live):
        if args and not any(a in w for a in args):
            continue
        mesh, k, stages = live[w]
        short = mesh.replace('/Engine/BasicShapes/', '').replace('/Game/Interval/', '')
        print('%-26s %-10s %-44s %d%s'
              % (w, where(mesh), short, k, '  (+%d stages)' % stages if stages else ''))


if __name__ == '__main__':
    main()
