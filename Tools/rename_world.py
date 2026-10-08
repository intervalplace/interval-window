#!/usr/bin/env python3
"""Rename two words in the world, everywhere at once, before the founding.

WHY THIS IS A SCRIPT AND NOT A SERIES OF EDITS. Both of these renames reach
`engine.js`, whose SHA is the world's name, and also the bridge and the window
that talk to it. Done one file at a time there is a window of minutes in which
the window offers a verb the world refuses, and the failure looks like a bug in
the menu rather than a half-finished rename. So it is one command that either
changes everything or changes nothing, and it checks the world still loads and
still says the same things before it keeps the result.

IT CAN ONLY BE RUN ONCE, AND ONLY NOW. The rules were fixed at the founding and
a founded world cannot be renamed: changing one character of engine.js makes a
different world with a different name. expanse7 has not been publicly founded,
so this is free today and never again.

  STAR BECOMES QUICK. The metal was `star-*` and the stone it is smelted from
  was `magic-stone`, which is two vocabularies for one chain and neither of
  them right. Nothing falls out of the sky here: §7 has the stone MINED in the
  Wilds, so `star` described nothing, and it is also the word every other game
  uses. `magic` was worse: this world names its magic sorcery, sigils, the
  barrow-work, the withering, never `magic`, and `magic-rock` was the one flat
  genre label in the whole vocabulary. `quick` is the old sense of living, as
  in the quick and the dead, as in quicksilver: a stone that is not inert, and
  smelted, a metal better than iron.

  ALCH BECOMES TRANSMUTE. The spell was already called `transmute` everywhere
  a person could read it: the level ladder says "transmute" and the verb said
  `alch`. The craft and the person keep their words, because `alchemy` is what
  the craft is and an `alchemist` is who does it. It is the SPELL that was
  named after the trade rather than after itself.

  SPECIAL BECOMES GAMBIT. "Special attack" is RuneScape's name and reads as
  borrowed the moment anybody sees it. A gambit is a move you spend something
  to make, which is what this actually is: it costs a bar that took the whole
  fight to fill, it can be interrupted, and it may not come off.

  `spec` is TWO WORDS in this engine and only one of them moves. As a field on
  a weapon, `{ spec: 'flurry' }`, it is the mechanic and becomes `gambit`. In
  "spec §5a" and "(spec 5f)" it means the constitution, and `specVersion` is
  the constitution's version, so those stay. So do `species`, `specific`,
  `specialist` and `specialisation`, which are ordinary English.

  rename_world.py            say what would change
  rename_world.py --apply    change it
"""
import json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # the Unreal project
BRIDGE = os.path.join(os.path.dirname(ROOT), 'interval-bridge')
ENGINE = os.path.join(BRIDGE, 'engine.js')

# Everything that speaks this vocabulary.
#
# A HAND-WRITTEN LIST WAS NOT ENOUGH AND THE MISS WAS EXPENSIVE. The first run
# named the engine, the bridge and eight window scripts, which felt thorough
# and covered a third of what actually speaks these words. `alchWhere` is a
# GENESIS FIELD, so `worldgen-expanse7.mjs` writes it into every founding, and
# the renamed engine then refused the genesis its own worldgen had just built:
#
#   refusing to build a world from an invalid genesis: unknown genesis field alchWhere
#
# So the bridge is taken WHOLE. Every .mjs and .js beside `engine.js`, which is
# 178 files of which 55 carried one of these words, plus the window's own
# scripts. `node_modules` is not ours and is left alone.
def _bridge_files():
    out = []
    for f in sorted(os.listdir(BRIDGE)):
        if f.endswith(('.mjs', '.js')) and not f.startswith('.'):
            out.append(os.path.join(BRIDGE, f))
    return out


FILES = [ENGINE] + [f for f in _bridge_files() if f != ENGINE] + [
    os.path.join(HERE, f) for f in sorted(os.listdir(HERE))
    if f.endswith('.py') and f not in ('rename_world.py',)
]

# ---------------------------------------------------------------------------
# WORDS THAT MUST SURVIVE UNTOUCHED.
#
# `alchemy` is the craft and `alchemist` is the person, and both keep their
# names: it is the SPELL that was misnamed. `start`, `restart` and the rest
# merely contain the letters of `star`. Each one is parked behind a sentinel
# for the length of the pass so no rule below can reach it.
KEEP = ['alchemy', 'Alchemy', 'ALCHEMY', "alchemy's", 'alchemist', 'Alchemist',
        'ALCHEMIST', 'alchemists',
        # `spec` the constitution, not `spec` the weapon field. And the
        # ordinary English words that merely begin the same way.
        'specVersion', 'SPEC_VERSION', 'specialist', 'specialisation',
        'specialists', 'species', 'specific', 'specifically', 'specially',
        'spec §', 'spec 5', 'spec 4', 'spec 2', 'SPEC.md',
        'startsWith', 'restarting', 'restarted', 'restarts', 'starting',
        'started', 'starter', 'startup', 'mayStart', 'tickStart', 'Started',
        'restart', 'starts', 'start']

TOOLS = ['grit', 'ingot', 'alloy', 'stone', 'forged', 'clad', 'sword', 'dagger',
         'flail', 'hatchet', 'helm', 'javelin', 'mell', 'pickaxe', 'plate',
         'shield', 'spear', 'rock', 'metal', 'gear']

def rules():
    """Every replacement, longest first so nothing is half-matched."""
    out = []
    # ---- the stone and the metal ----
    for a, b in (('magic-stones', 'quick-stones'), ('Magic-stones', 'Quick-stones'),
                 ('magic-stone', 'quick-stone'), ('Magic-stone', 'Quick-stone'),
                 ('magic-rocks', 'quick-rocks'), ('MAGIC-ROCK', 'QUICK-ROCK'),
                 ('magic-rock', 'quick-rock'), ('Magic-rock', 'Quick-rock'),
                 ('magicDepleteTicks', 'quickDepleteTicks'),
                 ('MAGIC_ROCK_MINING', 'QUICK_ROCK_MINING'),
                 ('starmetal', 'quickmetal'), ('Starmetal', 'Quickmetal'),
                 ('stargear', 'quickgear'),
                 ('_isStar', '_isQuick'), ('_star', '_quick')):
        out.append((a, b))
    for t in TOOLS:
        out.append(('star-' + t, 'quick-' + t))
        out.append(('Star-' + t, 'Quick-' + t))
    # ---- the spell ----
    for a, b in (('ALCH_EVERY_BARE', 'TRANSMUTE_EVERY_BARE'),
                 ('ALCH_EVERY_HEART', 'TRANSMUTE_EVERY_HEART'),
                 ('ALCH_EVERY_STAFF', 'TRANSMUTE_EVERY_STAFF'),
                 ('ALCH_PAYS', 'TRANSMUTE_PAYS'), ('ALCH_REQ', 'TRANSMUTE_REQ'),
                 ('ALCH_SHARE', 'TRANSMUTE_SHARE'), ('ALCH_OF', 'TRANSMUTE_OF'),
                 ('alchEveryFor', 'transmuteEveryFor'),
                 ('alchXpFor', 'transmuteXpFor'),
                 ('alchValue', 'transmuteValue'),
                 ('alchWhere', 'transmuteWhere'),
                 ('lastAlch', 'lastTransmute'),
                 ('alchable', 'transmutable'), ('alching', 'transmuting'),
                 ('alched', 'transmuted'), ('alchs', 'transmutes'),
                 # ---- the weapon's own move ----
                 ("special's", "gambit's"), ('specials', 'gambits'),
                 ('Special', 'Gambit'), ('SPECIAL', 'GAMBIT'),
                 ('special', 'gambit'),
                 ('.spec', '.gambit'), ("'spec'", "'gambit'"),
                 ('spec:', 'gambit:'), ('spec !', 'gambit !')):
        out.append((a, b))
    return out


def pass_over(text):
    """One file, with the keepers parked out of reach."""
    for i, word in enumerate(KEEP):
        text = text.replace(word, '\x00K%d\x00' % i)
    for a, b in rules():
        text = text.replace(a, b)
    # The bare words, once nothing compound is left to catch them.
    text = re.sub(r'\bstar\b', 'quick', text)
    text = re.sub(r'\bStar\b', 'Quick', text)
    text = re.sub(r'\balch\b', 'transmute', text)
    text = re.sub(r'\bALCH\b', 'TRANSMUTE', text)
    text = re.sub(r'\bAlch\b', 'Transmute', text)
    for i, word in enumerate(KEEP):
        text = text.replace('\x00K%d\x00' % i, word)
    return text


def check(tmp_engine):
    """Does the renamed world still load, and still say the same things?"""
    js = """
      const A = (await import('%s')).default
      const B = (await import('%s')).default
      const ren = (s) => String(s)
        .replace(/^magic-stone$/, 'quick-stone').replace(/^magic-rock$/, 'quick-rock')
        .replace(/^star-/, 'quick-').replace(/^stargear$/, 'quickgear')
        .replace(/^alch$/, 'transmute')
      let bad = 0, tables = 0
      const ka = Object.keys(A).sort(), kb = Object.keys(B).sort()
      if (ka.join() !== kb.join()) { console.log('EXPORTS DIFFER'); process.exit(1) }
      for (const k of ka) {
        const a = A[k]
        if (!a || typeof a !== 'object') continue
        const one = Array.isArray(a) ? a.map(ren).join('|')
                                     : Object.keys(a).map(ren).sort().join('|')
        const two = Array.isArray(B[k]) ? B[k].map(String).join('|')
                                        : Object.keys(B[k] || {}).sort().join('|')
        tables++
        if (one !== two) { bad++; console.log('  differs: ' + k) }
      }
      console.log('CHECK exports ' + ka.length + ' tables ' + tables + ' mismatched ' + bad)
      process.exit(bad ? 1 : 0)
    """ % (ENGINE.replace(' ', '%20'), tmp_engine.replace(' ', '%20'))
    r = subprocess.run(['node', '--input-type=module', '-e', js],
                       cwd=BRIDGE, capture_output=True, text=True)
    print((r.stdout + r.stderr).strip()[-900:])
    return r.returncode == 0


def main(apply):
    counts = {}
    for f in FILES:
        if not os.path.exists(f):
            print('  (no %s)' % os.path.relpath(f, ROOT))
            continue
        was = open(f).read()
        now = pass_over(was)
        n = sum(1 for a, b in zip(was.split('\n'), now.split('\n')) if a != b)
        counts[f] = n
        print('  %-44s %4d lines' % (os.path.relpath(f, os.path.dirname(ROOT)), n))
        if apply and n:
            open(f + '.renamed', 'w').write(now)

    if not apply:
        print('\nnothing written. run with --apply to do it.')
        return 0

    # THE WORLD IS CHECKED BEFORE ANY OF IT IS KEPT.
    if counts.get(ENGINE):
        tmp = os.path.join(BRIDGE, '_engine_check.js')
        shutil.copy(ENGINE + '.renamed', tmp)
        ok = check(tmp)
        os.remove(tmp)
        if not ok:
            for f in counts:
                if os.path.exists(f + '.renamed'):
                    os.remove(f + '.renamed')
            print('the renamed world does not match the old one. nothing changed.')
            return 1

    for f, n in counts.items():
        if not n:
            continue
        shutil.copy(f, f + '.before-rename')
        os.replace(f + '.renamed', f)
    print('\ndone. the old files are kept beside the new ones as .before-rename')
    print('the world is now named:')
    subprocess.run(['shasum', '-a', '256', ENGINE])
    return 0


if __name__ == '__main__':
    sys.exit(main('--apply' in sys.argv))
