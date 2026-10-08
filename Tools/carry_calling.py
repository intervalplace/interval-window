#!/usr/bin/env python3
"""Carry the swearing across a founding, so a sworn citizen survives the crossing.

WHAT WENT WRONG. The pillar refused to start with `buildWorld produced an
invalid state (woodcraft past the ceiling)`. That message is correct about the
state it was shown and says nothing about the cause, which is three files away.

`xpCeiling` reads ONE field: `p.calling`. A citizen who has sworn has no ceiling
in their own skill and 70 in every other; a citizen who has not is held at 50 in
everything. `IMPORT_FIELDS` -- the complete list of what a founding may carry --
named pid, skills, name, hp, vaults, inventory and weapon, and did not name the
calling. `serve.mjs` therefore never sent one, `validateImports` would have
refused it if it had, and `seatImport` never applied one. So every citizen
carried into a new world arrived UNSWORN, and a forester at woodcraft 70 was
seated as an unsworn citizen holding 70 in a skill capped at 50.

The world then refused itself. Nothing was corrupt: the founding built a state
the rules forbid, and `validateState` did exactly its job.

AND IT IS WORSE THAN A LOST WORD. Dropping the swearing does not just cost the
title. It retroactively makes every hour a citizen spent past level 50 illegal,
which means the crossing cannot even seat them -- the further a citizen got, the
more certain it was that the next founding would not start.

WHAT THIS CHANGES.

  engine.js   `calling` joins IMPORT_FIELDS
              validateImports checks it: a known calling, and the same level 50
              the swearing itself demands, plus the ceiling checked at the door
              so the refusal names the import instead of the built world
              seatImport applies it BEFORE the body is measured, because maxHp
              asks what the citizen is sworn to
  serve.mjs   the carry list sends it

NO OTHER BEHAVIOUR MOVES. Nothing else reads `imp.calling`, and a citizen who
never swore carries null and is seated exactly as before.

STILL LEFT BEHIND, deliberately, and worth a separate look: `sworn_by` (which
master, and when) and `apprentices`. A crossing loses the lineage. That is a
smaller loss than the ceiling and a wider change, so it is not in here.

  carry_calling.py            say what would change
  carry_calling.py --apply    change it
"""
import os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BRIDGE = os.path.join(os.path.dirname(ROOT), 'interval-bridge')
ENGINE = os.path.join(BRIDGE, 'engine.js')
SERVE = os.path.join(BRIDGE, 'serve.mjs')

ENGINE_EDITS = [
    # ---- the list of what a founding may carry ----
    ("const IMPORT_FIELDS = new Set(['pid', 'skills', 'name', 'hp', 'vaults', 'inventory', 'weapon']);",
     "// §5k: `calling` is in this list because `xpCeiling` reads it. A crossing\n"
     "// that drops the swearing does not lose a title, it makes every hour the\n"
     "// citizen spent past level 50 illegal, and the founding then refuses the\n"
     "// state it has just built. See the note in validateImports.\n"
     "const IMPORT_FIELDS = new Set(['pid', 'skills', 'name', 'hp', 'vaults', 'inventory', 'weapon', 'calling']);"),

    # ---- and what it has to clear to be believed ----
    ("""    if (imp.inventory !== undefined) {
      if (!Array.isArray(imp.inventory) || imp.inventory.length > INV_SLOTS) return 'malformed imported inventory';""",
     """    // §5k: THE SWEARING CROSSES WITH THEM, AND IS RE-EARNED AT THE DOOR.
    //
    // A carried citizen used to arrive with no calling at all, because this
    // validator's field list did not admit one. `xpCeiling` reads exactly that
    // field, so an unsworn citizen is held at level 50 in everything: a
    // forester carried at woodcraft 70 was seated as an unsworn citizen
    // holding 70 in a skill capped at 50, and `validateState` refused the
    // world the founding had just finished building.
    //
    // It is checked here rather than trusted, against the same level the
    // swearing itself demands, because an import is the one door into this
    // world that no validated input ever passed through.
    if (imp.calling !== undefined && imp.calling !== null) {
      if (typeof imp.calling !== 'string' || !Object.prototype.hasOwnProperty.call(SWORN, imp.calling))
        return 'import carries an unknown calling';
      if (levelForXp(imp.skills?.[SWORN[imp.calling].skill] ?? 0) < SWEAR_LEVEL)
        return 'import carries a calling it has not earned';
    }
    // AND THE CEILING IS CHECKED AT THE DOOR TOO. `validateState` already
    // refuses a state past the ceiling and remains the backstop that matters,
    // but it names a skill and not a citizen: the founding failed with three
    // words and no pid, and the cause was in a different file. Asked here, the
    // refusal points at the import that is wrong.
    for (const [sk, xp] of Object.entries(imp.skills ?? {})) {
      const ceil = xpCeiling({ calling: imp.calling ?? undefined, skills: imp.skills }, sk);
      if (ceil !== Infinity && xp > ceil) return `import carries ${sk} past the ceiling`;
    }
    if (imp.inventory !== undefined) {
      if (!Array.isArray(imp.inventory) || imp.inventory.length > INV_SLOTS) return 'malformed imported inventory';"""),

    # ---- and it is applied before the body is measured ----
    ("""  for (const k of Object.keys(p.skills)) if (c.skills?.[k] !== undefined) p.skills[k] = c.skills[k];
  // §5j: the frame is flat and a calling may move it. It is NOT a skill.""",
     """  for (const k of Object.keys(p.skills)) if (c.skills?.[k] !== undefined) p.skills[k] = c.skills[k];
  // §5k: AND THE SWEARING IS APPLIED BEFORE THE FRAME IS MEASURED, because the
  // line below asks `maxHp` what this citizen is sworn to. Validated already.
  if (c.calling != null) p.calling = c.calling;
  // §5j: the frame is flat and a calling may move it. It is NOT a skill."""),
]

SERVE_EDITS = [
    ("""      hp: p.hp, // (rescued again from the comment a bad merge swallowed it into)""",
     """      hp: p.hp, // (rescued again from the comment a bad merge swallowed it into)
      // §5k: AND WHAT THEY SWORE. Without this the crossing seats everyone as
      // an unsworn citizen, whose ceiling is level 50 in every skill, and the
      // new world refuses itself the moment anybody carried has passed it.
      calling: p.calling ?? null,"""),
]


def patch(path, edits):
    src = open(path).read()
    out = src
    for old, new in edits:
        if old not in out:
            print('  NOT FOUND in %s, nothing written:\n    %s'
                  % (os.path.basename(path), old.strip().splitlines()[0][:92]))
            return None, None
        if out.count(old) != 1:
            print('  AMBIGUOUS in %s (%d matches), nothing written'
                  % (os.path.basename(path), out.count(old)))
            return None, None
        out = out.replace(old, new, 1)
    print('  %-12s %d edits, %d bytes -> %d'
          % (os.path.basename(path), len(edits), len(src), len(out)))
    return src, out


# THE WORLD IS ASKED WHETHER THE CROSSING NOW WORKS, which is the only check
# worth running: found a world, carry a sworn forester at woodcraft 70, and see
# whether the state that comes out is one the rules accept.
#
# AND IT IS RUN WITH THE CANDIDATE STANDING IN FOR THE ENGINE, not beside it.
# The first cut imported the new engine as `_engine_check.js` and got `worldgen
# interval-expanse-v7 is not registered on this node` three times: a worldgen
# registers itself with the engine module it imported, and two copies of a
# module are two nodes as far as that register is concerned. So the candidate is
# written over `engine.js` for the length of the check and the original is put
# back if anything at all goes wrong.
CHECK = """
  const E = (await import('./engine.js')).default
  const WG = await import('./worldgen-expanse7.mjs')
  const { rulesHash } = await import('./rules-hash.mjs')
  const say = console.log
  const quiet = console.log; console.log = () => {}
  const RH = rulesHash(new URL('./', import.meta.url))
  const pid = 'a'.repeat(64)
  const forester = {
    pid, name: 'alder', hp: 64, calling: 'forester',
    skills: Object.fromEntries(E.SKILLS.map(s => [s, 0])),
    inventory: [], vaults: {}, weapon: null,
  }
  forester.skills.woodcraft = E.XP_TABLE[70]
  const found = (imported) => {
    const g = WG.makeExpanse7Genesis(WG.TALLYHOLM_SEED, RH, 0)
    g.imported = imported
    const bad = E.validateGenesis(g)
    if (bad) return { refused: bad }
    const s = WG.buildWorld(g)
    return { state: s, bad: E.validateState(s) }
  }
  console.log = quiet
  const a = found([forester])
  say('  a sworn forester at woodcraft 70:  ' + (a.refused ? 'REFUSED ' + a.refused
      : (a.bad ? 'BAD STATE ' + a.bad : 'seated, calling ' + a.state.players[pid]?.calling
         + ', woodcraft level ' + E.levelForXp(a.state.players[pid]?.skills?.woodcraft ?? 0))))
  console.log = () => {}
  const unsworn = { ...forester, calling: null }
  const b = found([unsworn])
  console.log = quiet
  say('  the same citizen unsworn:          ' + (b.refused ? 'refused, ' + b.refused
      : (b.bad ? 'BAD STATE ' + b.bad : 'SEATED, which it should not be')))
  console.log = () => {}
  const cheat = { ...forester, calling: 'smith' }
  const c = found([cheat])
  console.log = quiet
  say('  a forester claiming smith:         ' + (c.refused ? 'refused, ' + c.refused
      : 'SEATED, which it should not be'))
  const ok = a.state && !a.bad && a.state.players[pid]?.calling === 'forester'
    && b.refused && c.refused
  say('CHECK ' + (ok ? 'passed' : 'FAILED'))
  process.exit(ok ? 0 : 1)
"""


def main(apply):
    e_src, e_out = patch(ENGINE, ENGINE_EDITS)
    if e_out is None:
        return 1
    s_src, s_out = patch(SERVE, SERVE_EDITS)
    if s_out is None:
        return 1
    if not apply:
        print('\nnothing written. run with --apply to do it.')
        return 0

    for path, tag in ((ENGINE, '.before-calling'), (SERVE, '.before-calling')):
        shutil.copy(path, path + tag)
    open(ENGINE, 'w').write(e_out)
    open(SERVE, 'w').write(s_out)
    try:
        r = subprocess.run(['node', '--input-type=module', '-e', CHECK],
                           cwd=BRIDGE, capture_output=True, text=True)
        print((r.stdout + r.stderr).strip()[-1400:])
    except BaseException:
        open(ENGINE, 'w').write(e_src)
        open(SERVE, 'w').write(s_src)
        raise
    if r.returncode:
        open(ENGINE, 'w').write(e_src)
        open(SERVE, 'w').write(s_src)
        print('\nthe crossing still does not work. the old files are back.')
        return 1
    print('\ndone. the world is now named:')
    subprocess.run(['shasum', '-a', '256', ENGINE])
    return 0


if __name__ == '__main__':
    sys.exit(main('--apply' in sys.argv))
