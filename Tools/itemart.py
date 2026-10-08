#!/usr/bin/env python3
"""Which mesh each of the world's items is drawn with.

One table, written down once, because three separate things need it and had
been deriving it three different ways: the icon renderer, the audit, and
`parts.py` when it dresses a citizen.

Two sources, in this order. A thing somebody WEARS or WIELDS already has a
mesh, and `parts.py` knows which -- a sword in the pack must be the same sword
that is on the citizen's back, so that is read straight out of `WORN` rather
than chosen again here. Everything else is what the world is MADE of, and those
were forged by `make_goods.py`; they are matched by name.

  itemart.py          writes items.json and says what is still missing
"""
import json, os, sys

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
ROOT = os.path.dirname(SP)
S = ('/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/'
     'd4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/')


def paths(value, found):
    """Every /Game/... path inside a kit row, whatever shape the row is."""
    if isinstance(value, str):
        if value.startswith('/Game/'):
            found.append(value)
    elif isinstance(value, dict):
        for v in value.values():
            paths(v, found)
    elif isinstance(value, (list, tuple)):
        for v in value:
            paths(v, found)


def main():
    import parts
    items = json.load(open(S + 'scope.json'))['items']
    have, lack = {}, []
    for name in items:
        found = []
        paths(parts.WORN.get(name), found)
        if found:
            have[name] = found[0]
            continue
        # Unreal asset names take no hyphens, so the forge writes underscores.
        stem = name.replace('-', '_')
        if os.path.exists(os.path.join(ROOT, 'Art', 'Forged', stem + '.obj')):
            have[name] = '/Game/Interval/Forged/%s.%s' % (stem, stem)
        else:
            lack.append(name)
    json.dump({'have': have, 'lack': lack}, open(S + 'items.json', 'w'), indent=1)
    print('%d items: %d have a mesh, %d do not' % (len(items), len(have), len(lack)))
    if lack:
        print('  still missing: %s' % ' '.join(lack))


main()
