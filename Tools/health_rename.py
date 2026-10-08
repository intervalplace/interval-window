#!/usr/bin/env python3
"""Rename the world's `hp` to `health`, everywhere a person can see it and in
the rules that carry it.

WHY. The window showed `hp`, the handbook said `hitpoints` and the engine's own
prose said `flesh`: three vocabularies for one number. The window and the book
were settled on `health` -- "Everything doesn't have to be special word for this
world. Health is immediately understood by anyone" -- and this brings the rules
into line so there is one word from the state field to the printed page.

`hp` is an abbreviation of `hitpoints`, which is a term borrowed from other
games. `health` is plain English and needs no explaining to anybody.

WHAT MOVES. Three identifiers, by word boundary:

    hp        -> health          the state field, and the calling's bonus
    maxHp     -> maxHealth
    HP_FLAT   -> HEALTH_FLAT

and the same word wherever the bridge and the window read it.

THE CHECKPOINT PROBLEM, AND WHY IT IS SMALL. `hp` is a state field, so every
saved world has it under the old name and `IMPORT_FIELDS` names it. A refounding
does not read an old state directly: `serve.mjs` walks the old players and
BUILDS imports from them, so it is the one place that has to understand both
spellings. It is taught to, and the note there says why.

AND THE HASH MOVES, which is the whole reason to do it now. The pillar has not
been redeployed since the carried-calling fix, so this rides along on a founding
that has to happen anyway instead of costing one of its own. Once expanse7 is
deployed and people are playing, the same change costs a second founding.

  health_rename.py            say what would change
  health_rename.py --apply    change it
"""
import os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BRIDGE = os.path.join(os.path.dirname(ROOT), 'interval-bridge')
ENGINE = os.path.join(BRIDGE, 'engine.js')
WINDOW = os.path.join(ROOT, 'Plugins', 'IntervalBridge', 'Source', 'IntervalBridge')

# WORD BOUNDARIES, ALWAYS. `maxHp` carries a capital H so `\bhp\b` cannot reach
# inside it, and the three are applied longest-first so no rename eats another.
WORDS = [
    (re.compile(r'\bHP_FLAT\b'), 'HEALTH_FLAT'),
    (re.compile(r'\bmaxHp\b'), 'maxHealth'),
    (re.compile(r'\bhp\b'), 'health'),
]


def renamed(text):
    for pat, to in WORDS:
        text = pat.sub(to, text)
    return text


def files():
    out = [ENGINE]
    for f in ('serve.mjs', 'unreal-bridge.mjs'):
        p = os.path.join(BRIDGE, f)
        if os.path.exists(p):
            out.append(p)
    for base, _dirs, names in os.walk(WINDOW):
        for n in names:
            if n.endswith(('.cpp', '.h')):
                out.append(os.path.join(base, n))
    return out


CHECK = """
  const E = (await import('./engine.js')).default
  const WG = await import('./worldgen-expanse7.mjs')
  const { rulesHash } = await import('./rules-hash.mjs')
  const quiet = console.log; console.log = () => {}
  const g = WG.makeExpanse7Genesis(WG.TALLYHOLM_SEED,
    rulesHash(new URL('./', import.meta.url)), 0)
  const s = WG.buildWorld(g)
  const pid = 'a'.repeat(64)
  E.addPlayer(s, pid, g.worldW >> 1, g.worldH >> 1)
  const p = s.players[pid]
  console.log = quiet
  const keys = Object.keys(p).sort()
  console.log('a fresh citizen has: ' + (keys.includes('health') ? 'health' : 'NO health')
    + (keys.includes('hp') ? ' AND STILL hp' : ', no hp'))
  console.log('health = ' + p.health + ', maxHealth = ' + E.maxHp)
  console.log('IMPORT_FIELDS carries health: ' + /['"]health['"]/.test(
    (await import('node:fs')).readFileSync('./engine.js','utf8')
      .match(/const IMPORT_FIELDS[^;]+;/)[0]))
  const bad = E.validateState(s)
  console.log('the built world validates: ' + (bad || 'yes'))
  process.exit(bad ? 1 : 0)
"""


def main(apply):
    todo = []
    for p in files():
        src = open(p).read()
        out = renamed(src)
        if out != src:
            n = sum(len(pat.findall(src)) for pat, _ in WORDS)
            todo.append((p, src, out, n))
    if not todo:
        print('  nothing to rename')
        return 0
    for p, _s, _o, n in todo:
        print('  %-52s %4d' % (os.path.relpath(p, os.path.dirname(ROOT)), n))
    print('  %d files' % len(todo))
    if not apply:
        print('\nnothing written. run with --apply to do it.')
        return 0

    for p, src, out, _n in todo:
        shutil.copy(p, p + '.before-health')
        open(p, 'w').write(out)
    # ---- AND serve.mjs MUST READ BOTH, because old checkpoints say `hp` ----
    sp = os.path.join(BRIDGE, 'serve.mjs')
    s2 = open(sp).read()
    old = "      health: p.health, // (rescued again from the comment a bad merge swallowed it into)"
    new = ("      // BOTH SPELLINGS, and only here. Every checkpoint written before\n"
           "      // the rename says `hp`; this is the one place a world built under\n"
           "      // the old rules is read by the new ones, so it is the one place\n"
           "      // that has to know the old word.\n"
           "      health: p.health ?? p.hp,")
    if old in s2:
        open(sp, 'w').write(s2.replace(old, new, 1))
        print('  serve.mjs reads both spellings')

    r = subprocess.run(['node', '--input-type=module', '-e', CHECK],
                       cwd=BRIDGE, capture_output=True, text=True)
    print((r.stdout + r.stderr).strip()[-900:])
    if r.returncode:
        for p, src, _o, _n in todo:
            open(p, 'w').write(src)
        print('\nthe world does not build. everything is back as it was.')
        return 1
    print('\ndone. the world is now named:')
    subprocess.run(['shasum', '-a', '256', ENGINE])
    return 0


if __name__ == '__main__':
    sys.exit(main('--apply' in sys.argv))
