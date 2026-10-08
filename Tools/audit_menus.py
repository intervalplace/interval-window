#!/usr/bin/env python3
"""WHAT EVERY THING IN A TOWN OFFERS, read off the window's own menu builder.

The standing rule is that a right-click lists only what is possible right now,
and three classes of impossible line have been closed by finding them one at a
time with a cursor. That is slow and only ever looks at whatever happened to be
under the mouse. `Tools/menus.py` runs inside the editor and asks `TargetsAt`
and `OptionsFor` -- the same two functions the menu is built from -- for every
tile within reach of the citizen, and writes the answers out. This reads them.

It does NOT replace clicking. A menu that is correct and opens off-screen is
still broken, and only a real cursor finds that. This is for the other half:
whether the LINES are right, over a whole town at once.

  exec py <scratchpad>/menus.py     in the editor, with the window playing
  audit_menus.py                    here
"""
import collections, json, os, sys

S = ('/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/'
     'd4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/')


def main(argv):
    path = argv[0] if argv else S + 'menus.json'
    if not os.path.exists(path):
        print('no sweep at %s -- run menus.py in the editor first' % path)
        return 1
    d = json.load(open(path))
    print('citizen at %s, reach %d: %d things and %d tiles of open ground'
          % (d['at'], d.get('reach', 0), len(d['tiles']), d.get('ground', 0)))
    if d.get('errors'):
        print('the sweep could not read %d of them:' % len(d['errors']))
        for e in d['errors'][:5]:
            print('   ' + str(e)[:120])
    print()

    # BY THE WORD THAT AFFORDS, which is the finer one where there is one: the
    # window asks the bridge for `landmark.wellspring` before `landmark`, so
    # that is the word a menu is decided by and the word to group under.
    by = {}
    for t in d['tiles']:
        key = t['sub'] or t['name']
        row = by.setdefault(key, {'n': 0, 'offers': set(), 'where': []})
        row['n'] += 1
        # BY THE VERB AND NOT BY THE LABEL. "walk here" is written out with
        # the tile in it -- `walk here  447, 278` -- so matching the words
        # kept every line in the world and said everything offered something.
        row['offers'].add(tuple(
            l for l, v in zip(t['lines'], t['verbs']) if v != 'walk'))
        if len(row['where']) < 3:
            row['where'].append('%d,%d' % (t['x'], t['y']))

    speaks = {k: v for k, v in by.items() if any(o for o in v['offers'])}
    mute = {k: v for k, v in by.items() if not any(o for o in v['offers'])}

    print('%d WORDS OFFER SOMETHING' % len(speaks))
    for k, row in sorted(speaks.items()):
        lines = sorted({' | '.join(o) for o in row['offers'] if o})
        print('  %-18s x%-4d %s' % (k[:18], row['n'], ' ;; '.join(lines)[:96]))
    print()
    print('%d WORDS OFFER ONLY "walk here"' % len(mute))
    print('  Most of these are right: a wall, a banner and an apple tree are')
    print('  scenery, and the world gives them no verb. What to look for is a')
    print('  word that ought to do something and is silent.')
    for k, row in sorted(mute.items(), key=lambda kv: -kv[1]['n']):
        print('  %-18s x%-4d  at %s' % (k[:18], row['n'], ', '.join(row['where'])))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
