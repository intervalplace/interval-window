#!/usr/bin/env python3
"""HOW BIG IS EVERY CREATURE, REALLY.

The bear was a bear trap and the mountain-goat was a sheep, and both were found
by somebody looking at the screen and saying so. That is a bad way to find
them: there are twenty-three creatures and a person meets them one at a time,
in the dark, over weeks.

So this measures the whole bestiary at once, from the SOURCE FILES rather than
from the engine. `get_bounds` on a skeletal mesh reports the ANIMATED extent --
a clip that translates the root makes a goblin four hundred metres long -- so
the numbers here come from the glTF's own accessor bounds, which are the bind
pose and cannot be inflated by an animation. Static meshes are measured the
same way from their .obj or .glb.

It prints what each creature is DRAWN at, in metres, next to what that animal
plausibly is, and marks the ones worth looking at. It changes nothing.

  bestiary.py
"""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import parts
import glbsize
import fbxsize

# Roughly how long a real one is, nose to tail, in metres. Only a sanity bar:
# a creature within a factor of two of this is not worth a second look.
PLAUSIBLE = {
    'wolf': 1.3, 'bear': 2.0, 'mountain-goat': 1.2, 'shore-crab': 0.3,
    'fen-adder': 1.0, 'boar': 1.5, 'sheep': 1.3, 'carrion-crow': 0.5,
    'goblin': 1.3, 'troll': 2.9, 'scree-imp': 0.9, 'great-spider': 2.0,
    'dragon': 8.0, 'siren': 1.8, 'quencher': 1.2, 'mere-lamprey': 1.0,
    'dummy': 1.8, 'risen': 1.8, 'skeleton-knight': 1.8, 'barrow-wight': 1.8,
    'gibbet-dead': 1.8, 'gibbet-king': 1.9, 'butt': 1.0,
}

# Every place a creature's source might sit. The Bestiary kit keeps its
# exports several folders deep, which is why five of the undead came back as
# "no source file" the first time this ran.
ART = {
    'Wild': os.path.join(ROOT, 'Art', 'Wild'),
    'WildStatic': os.path.join(ROOT, 'Art', 'WildStatic'),
    'Beasts': os.path.join(ROOT, 'Art', 'Beasts'),
    'Bestiary': os.path.join(
        ROOT, 'Art', 'Bestiary', 'Bestiary - Dungeon Monsters Kit[Source]',
        'Exports', 'GLB (Godot-Unreal)'),
    'RPGCharacters': os.path.join(ROOT, 'Art', 'RPGCharacters'),
}


def measure(path):
    """How big this creature is ONCE IMPORTED, in metres.

    THE READERS ALREADY EXIST and they exist for a reason. `glbsize.extent`
    applies the node transforms, which the accessor bounds alone do not --
    read those raw and a wolf measures six centimetres, because the scale
    lives in the scene graph. `fbxsize.extent` knows the FBX container.
    Writing a third reader here would have been a third thing to get wrong.

    THE FILE IS NOT THE ASSET, though, and that cost a night. Interchange
    bakes a glTF's armature scale into the bind pose on top of the node chain
    `extent` already walked, so most of Art/Wild arrives a hundred times the
    size its own file reports and a scale chosen from the file alone drew a
    fen-adder ninety metres long. `glbsize.baked` is that factor; multiplying
    by it is what makes the `drawn` column below agree with the picture, which
    is the only thing this report is for.
    """
    # Both readers answer ((x, y, z), longest); the .obj branch below returns
    # the triple alone, so everything is normalised to a triple here.
    if path.endswith('.fbx'):
        return list(fbxsize.extent(path)[0])
    if path.endswith('.obj'):
        lo = [1e30] * 3
        hi = [-1e30] * 3
        for line in open(path):
            if not line.startswith('v '):
                continue
            v = [float(x) for x in line.split()[1:4]]
            for i in range(3):
                lo[i] = min(lo[i], v[i]); hi[i] = max(hi[i], v[i])
        if lo[0] > 1e29:
            return None
        # An .obj carries no units and Unreal reads it as centimetres.
        return [(hi[i] - lo[i]) / 100.0 for i in range(3)]
    over = glbsize.baked(path)
    return [v * over for v in glbsize.extent(path)[0]]


def find(folder):
    """The source file for a creature folder, wherever it lives.

    SPELLED EXACTLY, because this disk does not care about case and this
    project does. `mere-lamprey` uses Art/Beasts/Snake.fbx and `fen-adder`
    uses Art/Wild/snake.glb, and they are deliberately different animals --
    but `os.path.isfile('Art/Wild/Snake.glb')` is true on macOS, so the
    lamprey was measured against the adder's file and reported at a hundred
    metres. The listing is the authority on how a name is spelled.
    """
    for where in ART.values():
        try:
            there = set(os.listdir(where))
        except OSError:
            continue
        for ext in ('.glb', '.gltf', '.obj', '.fbx'):
            if folder + ext in there:
                return os.path.join(where, folder + ext)
    return None


def main():
    rows = []
    tables = [('BEASTS', parts.BEASTS), ('WILD_BEASTS', parts.WILD_BEASTS),
              ('WILD_STILL', parts.WILD_STILL), ('DARK_BEASTS', parts.DARK_BEASTS)]
    for tname, table in tables:
        for word, entry in table.items():
            folder, scale = entry[0], entry[1]
            src = find(folder)
            if not src:
                # THE DEAD WEAR THE CITIZENS' OWN BODY. `Risen_Male` and
                # `Risen_Female` are not a creature kit at all -- they are the
                # same mesh a citizen is built from, so they are human-sized
                # by construction and there is no separate source to measure.
                note = ('the citizens\' own body -- human-sized by construction'
                        if folder.startswith('Risen') else 'no source file')
                rows.append((word, folder, tname, scale, None, None, note))
                continue
            try:
                ext = measure(src)
            except Exception as exc:
                rows.append((word, folder, tname, scale, None, None, str(exc)[:40]))
                continue
            if not ext:
                rows.append((word, folder, tname, scale, None, None, 'unreadable'))
                continue
            drawn = max(ext) * scale
            want = PLAUSIBLE.get(word)
            note = ''
            if want:
                off = drawn / want
                if off > 2.0 or off < 0.5:
                    note = 'LOOK -- %.1fx a real one' % off
            rows.append((word, folder, tname, scale, max(ext), drawn, note))

    rows.sort(key=lambda r: (r[6] == '', r[0]))
    print('%-18s %-12s %-12s %7s %9s %9s  %s'
          % ('word', 'folder', 'table', 'scale', 'file (m)', 'drawn (m)', 'note'))
    for word, folder, tname, scale, ext, drawn, note in rows:
        print('%-18s %-12s %-12s %7.4f %9s %9s  %s'
              % (word, folder, tname, scale,
                 '%.2f' % ext if ext else '-',
                 '%.2f' % drawn if drawn else '-', note))

    # AND A NUMBER TO CHECK, so this can stand beside the other measures.
    #
    # It was not one, and that is how a troll two hundred and eighty-five
    # metres tall stood on the moor while every audit read clean: audit_art
    # walks the Nature folder and the worn kits and has never looked at a
    # creature, so nothing in the project was counting them.
    measured = [r for r in rows if r[5] is not None]
    looks = [r for r in measured if r[6]]
    print()
    print('creatures drawn at a plausible size  %d of %d measured'
          % (len(measured) - len(looks), len(measured)))
    if looks:
        print('  worth a look: %s' % ', '.join(r[0] for r in looks))


if __name__ == '__main__':
    main()
