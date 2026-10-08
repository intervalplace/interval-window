#!/usr/bin/env python3
"""WHICH ITEMS ARE DRAWN AS SOMETHING ELSE, and how many share the same thing.

The window has a mesh for most of the world's hundred and thirty-two item
words, and `audit_art.py` already checks that every mesh it uses is dressed and
the right size. This asks the other question, which nothing asked: how many
DISTINCT words are drawn by the SAME mesh, and which of those deserve better.

A shared mesh is not automatically wrong. Five grades of the same sword are the
same shape in different metal and should be; that is what the world means by
`steel-sword` and `quick-sword`, and a kit that draws them from one mesh with
five dyes is right. What is wrong is a word the world made GAMBIT being drawn
as the generic thing beside it -- a fire-siphon as a staff, a chain as a sword,
a king's shroud as a shirt -- because the silhouette is what a player reads.

So this sorts the sharing into two piles by asking the world, not by taste:

  A FAMILY is a set of words that differ only by their metal or wood. The
  world's own naming says so -- `iron-`, `steel-`, `quick-`, `gold-` in front of
  the same noun -- and one mesh in several dyes is the right answer.

  EVERYTHING ELSE is a word sharing a mesh with a word it is not a grade of,
  and every one of those is a judgement to make rather than a fact to report.

  audit_items.py            the report
  audit_items.py --sharing  only the meshes more than one word uses
"""
import json, os, re, sys, urllib.request

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import parts

# The metals and woods the world puts in front of a noun. Taken from the item
# list itself rather than invented: every one of these appears as a prefix on
# at least two different nouns.
# THE MATERIALS AND THE SIZES, and nothing else. `horn`, `hollow`, `sigil` and
# `dragon` were in here and should not have been: a horn bow is a composite
# recurve that costs four hundred gold and has a FLURRY, and a hollow bow is
# the forty-five-gold beginner's bow that makes its own arrows. Calling those
# two a family hid the fact that they are drawn by one mesh, which is the
# exact thing this file exists to find. A grade is a different METAL or WOOD
# or SIZE of the same noun; anything else is two nouns.
GRADES = ('iron', 'steel', 'quick', 'gold', 'shell', 'bone', 'oak', 'heartwood',
          'ironbark', 'wooden', 'great')


def stem(word):
    """The noun under a grade: `quick-sword` -> `sword`, `bread` -> `bread`."""
    for g in GRADES:
        if word.startswith(g + '-'):
            return word[len(g) + 1:]
    return word


def engine_src():
    """engine.js's own text. The tables below are not exported as data."""
    src = os.path.join(os.path.dirname(SP), '..', 'interval-bridge', 'engine.js')
    src = os.path.normpath(src)
    if not os.path.exists(src):
        src = os.path.join(os.path.dirname(os.path.dirname(SP)), 'interval-bridge', 'engine.js')
    return open(src, errors='ignore').read()


def world_items():
    """Every item word the world names, read off the rules themselves."""
    text = engine_src()
    words = set()
    # ITEMS and PRICES are the two that between them name everything.
    for table in ('const ITEMS = ', 'const PRICES = '):
        at = text.find(table)
        if at < 0:
            continue
        end = text.find('\n}', at)
        for m in re.finditer(r"'([a-z][a-z-]*)'", text[at:end]):
            words.add(m.group(1))
    # The five EQUIP_SLOTS read as item words out of the same block and are
    # not items: a citizen does not carry a `head`.
    return words - {'weapon', 'head', 'body', 'offhand', 'legs'}


def equippable():
    """The words a citizen can actually WEAR or HOLD.

    Everything else -- bread, ore, logs, eel -- lives in the pack and on the
    ground and is never on a body, so it needs an inventory sprite and no worn
    mesh at all. Reporting those together as "drawn by nothing" made a list of
    fifty-four words that looked like a gap and was not one; the gap is the
    ones a citizen can put on.
    """
    text = engine_src()
    # BUILT OUT OF THE RECIPES AND NOT WRITTEN DOWN: the rules say
    # `new Set([...Object.keys(RECIPES), 'wooden-bow', ...])`, so the set is
    # the smithing and fletching table plus a handful of things nobody makes.
    # Reading the literal alone gave nine words and called the other hundred
    # and twenty-three a gap; reading RECIPES as well is what the rules do.
    out = set()
    at = text.find('const EQUIPPABLE = new Set([')
    if at < 0:
        return None
    end = text.find(']', at)
    out |= {m.group(1) for m in re.finditer(r"'([a-z][a-z-]*)'", text[at:end])}
    at = text.find('const RECIPES = {')
    if at < 0:
        return None
    depth, i = 0, text.index('{', at)
    for j in range(i, len(text)):
        if text[j] == '{':
            depth += 1
        elif text[j] == '}':
            depth -= 1
            if depth == 0:
                break
    # Only the KEYS of the table, which are the things made -- not the
    # ingredients inside each row, which are ore and logs and are not worn.
    for m in re.finditer(r"^\s{2}'?([a-z][a-z-]*)'?\s*:", text[i:j], re.M):
        out.add(m.group(1))
    return out


def mesh_of(word):
    """What the window actually draws for a word, as an asset path, or None."""
    row = parts.WORN.get(word)
    if not row:
        return None
    # A kit is `{'pieces': [...]}`, and the first piece carrying a mesh is the
    # thing the eye reads; the rest are a scabbard, a strap, a second glove.
    pieces = row.get('pieces') if isinstance(row, dict) else row
    for piece in (pieces or []):
        m = piece.get('mesh') if isinstance(piece, dict) else None
        if isinstance(m, dict):
            m = m.get('refPath')
        if m:
            return str(m)
    return None


def main(argv):
    words = sorted(world_items())
    drawn, undrawn, by_mesh = {}, [], {}
    for w in words:
        m = mesh_of(w)
        if m is None:
            undrawn.append(w)
            continue
        drawn[w] = m
        by_mesh.setdefault(m, []).append(w)

    print('the world names %d item words; %d have a mesh, %d have none'
          % (len(words), len(drawn), len(undrawn)))
    print()

    families, mixed = [], []
    for mesh, ws in sorted(by_mesh.items()):
        if len(ws) < 2:
            continue
        stems = {stem(w) for w in ws}
        (families if len(stems) == 1 else mixed).append((mesh, sorted(ws)))

    print('MESHES SHARED BY A FAMILY -- one noun in several metals, which is right')
    for mesh, ws in families:
        print('  %-28s %s' % (mesh.split('/')[-1].split('.')[0], ', '.join(ws)))
    print()
    print('MESHES SHARED BY WORDS THAT ARE NOT A FAMILY -- each one a judgement')
    if not mixed:
        print('  (none)')
    for mesh, ws in mixed:
        print('  %-28s %s' % (mesh.split('/')[-1].split('.')[0], ', '.join(ws)))
    print()
    wearable = equippable()
    if wearable is None:
        print('could not read EQUIPPABLE out of the rules; the gap below is '
              'every word with no worn mesh, wearable or not')
        gap, fine = undrawn, []
    else:
        gap = [w for w in undrawn if w in wearable]
        fine = [w for w in undrawn if w not in wearable]
    print('A CITIZEN CAN WEAR OR HOLD IT AND NOTHING DRAWS IT: %d' % len(gap))
    for i in range(0, len(gap), 6):
        print('  ' + ', '.join(gap[i:i + 6]))
    if not gap:
        print('  (none -- every equippable word in the world has a mesh)')
    if '--sharing' not in argv:
        print()
        print('NEVER ON A BODY, so a worn mesh would never be seen (%d). These '
              'live' % len(fine))
        print('in the pack and on the ground, where the sprite is what is read.')
        for i in range(0, len(fine), 6):
            print('  ' + ', '.join(fine[i:i + 6]))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
