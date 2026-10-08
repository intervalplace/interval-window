#!/usr/bin/env python3
"""EVERY WORD THE WORLD USES, AND WHETHER THIS WINDOW DRAWS IT.

The standing goal has three legs and two of them are measured: `coverage.sh`
counts the verbs a mouse can reach and `audit_art.py` counts the meshes that
are dressed and sized. This is the third: the WORDS. A world that says `ossuary`
and a window that has never heard of one draws nothing at all there, and a
citizen walks past an empty patch of grass with a deed waiting on it.

Two sources, because they answer different halves of the question:

  what the world AFFORDS -- the bridge derives this from the engine at boot,
  and every one of these words has a deed attached to it, so a word here that
  is not drawn is a deed nobody can find.

  what the GENERATOR PLANTS -- read out of the founding's own worldgen module.
  Most of these have no deed at all: a standing stone, a cairn, a signpost.
  They are scenery, and scenery that is missing is a world with holes in it.

  audit_words.py
"""
import json, os, re, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
BRIDGE = '/Users/matsjulner/Documents/Unreal Projects/interval-bridge'

def drawn_words():
    """Every word this window names a mesh for, however it names it.

    TWO SOURCES, because there are two. Most of the vocabulary is in parts.py,
    but a handful of words -- `guard`, `keeper` -- were placed in the level
    long before that file existed and still live on the ground actor, which
    `apply.py` copies out of it. Reading parts.py alone reported those two as
    words the world uses and the window has never heard of, which is exactly
    backwards: they are drawn, and they are drawn from the older table.

    So the LOOK ASSET is asked as well, when an editor is up. It is the thing
    the window actually reads, which makes it the authority; parts.py alone is
    the fallback for running this with nothing open.
    """
    import parts
    out = set()
    for name in dir(parts):
        if name.startswith('_'):
            continue
        val = getattr(parts, name)
        if isinstance(val, dict):
            for key in val:
                if isinstance(key, str):
                    out.add(key)
    try:
        import rpc
        got = rpc.call('editor_toolset.toolsets.object.ObjectTools',
                       'get_properties',
                       {'instance': {'refPath':
                            '/Game/Interval/IntervalLook.IntervalLook'},
                        'properties': ['Props', 'PropsUpper', 'Ramparts']})
        held = json.loads(json.loads(got)['returnValue'])
        for table in held.values():
            if isinstance(table, dict):
                out |= {k for k in table if isinstance(k, str)}
    except Exception as exc:
        print('  (no editor: reading parts.py alone -- %s)' % str(exc)[:60])
    return out

# WHICH MODULES THIS FOUNDING IS ACTUALLY MADE OF.
#
# The bridge keeps every generator it has ever been asked for, so the folder
# holds expanse2 through expanse7 side by side. Reading all of them counted
# words from foundings this world was never built from -- `boundary-stone` is
# planted by expanse4 and by nothing else -- and reported them as holes.
FOUNDING = ('worldgen-expanse7.mjs', 'worldgen-country-v7.mjs',
            'worldgen-holdings-v7.mjs', 'worldgen-camps-v7.mjs')

def planted():
    """The node kinds this founding plants, as the generator plants them.

    A node arrives through `put(tag, type, x, y, { kind: 'x' })`, so that call
    is what is read -- both the type it is given and the kind inside its row.
    Reading every `kind:` in the file instead swept up the names of holdings,
    camps and settlements, which are PLANS: a `barn` is a holding that expands
    into a roofed building, not a thing standing on a tile, and the window
    draws it through the roof system rather than through a mesh.
    """
    words = set()
    for f in FOUNDING:
        path = os.path.join(BRIDGE, f)
        if not os.path.exists(path):
            continue
        src = open(path).read()
        for m in re.finditer(
                r"put\(\s*[^,]+,\s*'([a-z][a-z0-9.\-]*)'([^;]{0,240}?)\)\s*(?:;|$)",
                src, re.M):
            words.add(m.group(1))
            inner = re.search(r"kind\s*:\s*'([a-z][a-z0-9.\-]*)'", m.group(2))
            if inner:
                words.add(m.group(1) + '.' + inner.group(1))
    return words

def main():
    have = drawn_words()
    try:
        afford = set(json.load(open('/tmp/_kinds.json')))
    except Exception:
        afford = set()
        print('  (no /tmp/_kinds.json: run the bridge query first)')

    def undrawn(words):
        # A word may be named four ways, because four tables name things four
        # ways: whole (`well`), as a landmark (`landmark.mill`), by its stem
        # (`keeper` for `keeper.toll`), or by its TRADE alone -- the keepers
        # are keyed `drover`, `wizard`, `watchman`, without the `keeper.` in
        # front, because what differs between two keepers is the trade.
        miss = []
        for w in sorted(words):
            bits = w.split('.')
            names = {w, 'landmark.' + w, bits[0], bits[-1]}
            if names & have:
                continue
            miss.append(w)
        return miss

    print('')
    a = undrawn(afford)
    print('  words the world affords a deed on   %d' % len(afford))
    print('  of those, nothing is drawn for      %d' % len(a))
    if a:
        for i in range(0, len(a), 6):
            print('   ', ' '.join(a[i:i + 6]))
    p = planted()
    b = undrawn(p)
    print('')
    print('  kinds the generator plants          %d' % len(p))
    print('  of those, nothing is drawn for      %d' % len(b))
    if b:
        for i in range(0, len(b), 6):
            print('   ', ' '.join(b[i:i + 6]))

main()
