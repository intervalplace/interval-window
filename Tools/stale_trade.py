#!/usr/bin/env python3
"""Correct three comments that describe rules this world no longer has.

WHY THIS IS WORTH A SCRIPT. `engine.js` is argued out in its own comments and
that is most of what makes it readable. It also makes a stale comment
expensive: the prose is what a reader trusts, and twice now it has been
trusted and been wrong.

Both of these went into the printed handbook before anybody noticed.

  THE TIDE. §7dv still says "The tide gates one thing: a voice at RANGE...
  What the tide opens is the far channel -- and the stint is the licence to
  use it." `anyTideOpen` is exported and called from NOWHERE: not in the
  engine, not in serve.mjs, not in unreal-bridge.mjs. The gating was removed
  because a ninety-minute daily allowance is already the constraint and
  limiting speech on top of it doubles a limit the world only meant to impose
  once. What the tide still does is announce itself, which is the Schelling
  point §7dx describes and is worth keeping.

  THE KEEPERS. Two notes in PRICES say "a keeper will take dragon-bones and
  pays..." and "a keeper will take a bone spear, and pays...". §6l repealed
  `case 'sell'` -- "A keeper buys nothing" -- so nothing in this world pays a
  citizen for an item at all. The prices are what a STALL ASKS. They still
  matter, because PRAYER_KEEP saves the dearest PRICED thing you carry, which
  is exactly the argument the bone-spear note makes and is the reason these
  entries are priced rather than unpriced.

NO RULE CHANGES. Only comments, and the script proves it: every exported
table is compared before and after, and nothing is kept unless they match.

THE HASH MOVES ANYWAY, because the hash is over the file and a comment is in
the file. That is the whole reason to do this NOW: the pillar has not been
redeployed since the last change, so this rides along on a founding that has
to happen regardless instead of costing one of its own.

  stale_trade.py            say what would change
  stale_trade.py --apply    change it
"""
import os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BRIDGE = os.path.join(os.path.dirname(ROOT), 'interval-bridge')
ENGINE = os.path.join(BRIDGE, 'engine.js')

EDITS = [
    # ---- the tide gates nothing ----
    ("""// The tide gates one thing: a voice at RANGE. Speech to the person standing
// next to you is never gated, because that is not the network, that is being
// somewhere, and being somewhere is the one thing this world has always said
// a script cannot do. What the tide opens is the far channel -- and the
// stint is the licence to use it. Present by declaration, and the band up.
//
// It gates NOTHING ELSE. No yield rises in a tide, no seam gives more, no
// blow lands harder. The moment a tide pays, a citizen declares stints for
// the pay and the length they name stops being what they meant. Then it is
// a raid night with a different word on it.""",
     """// THE TIDE GATES NOTHING AT ALL, and that is deliberate.
//
// It used to open a voice at RANGE: speech to somebody beside you was always
// free, and the far channel waited for a tide with a stint as the licence to
// use it. That was removed. A citizen may only be played ninety minutes a
// day, and gating speech on top of that doubles a constraint the world meant
// to impose once -- it made two scarcities out of one and the second one only
// stopped people talking.
//
// `anyTideOpen` survives as an export and is called from nowhere. It is kept
// because a window may reasonably want to draw the tide; nothing in the rules
// consults it. If a later founding wants to gate something on a tide, this is
// the function for it, and the burden is on that founding to say why a second
// limit earns its place.
//
// AND IT MUST NEVER PAY. No yield rises in a tide, no seam gives more, no blow
// lands harder. The moment a tide pays, a citizen declares stints for the pay
// and the length they name stops being what they meant. Then it is a raid
// night with a different word on it.
//
// What the tide IS, now, is a clock everybody can read and nobody can move:
// see §7dx, where the longest one announces itself and names where people
// actually stood. That is a Schelling point, and it is the whole of the
// feature.""".rstrip()),

    # ---- keepers pay nothing ----
    ("""  // a keeper will take dragon-bones and pays what a curiosity is worth to
  // somebody who will never see the beast. THREE thousand ordinary bones fetch
  // six thousand, so five hundred is far under what the thing does: a keeper is
  // the worst buyer in the world for it and a mourner the best, which is how
  // every Wilds good in this table is priced.""",
     """  // §6l: NOBODY BUYS THIS, OR ANYTHING. `case 'sell'` is repealed and a keeper
  // buys nothing, so this is what a STALL ASKS for one and never what a
  // citizen is paid. The note here used to say a keeper "will take
  // dragon-bones and pays what a curiosity is worth", which described a trade
  // this world stopped having; it reached the printed handbook before anybody
  // caught it.
  //
  // The number still does real work: PRAYER_KEEP saves the dearest PRICED
  // thing a citizen carries, so a price is what makes a thing savable. Five
  // hundred against six thousand for the bones themselves says plainly that
  // the beast is worth more to a mourner than to any stall."""),

    ("""  // §7cm: a keeper will take a bone spear, and pays for the bones rather than
  // the work -- two dragon-bones is a thousand and the haft is nothing. Priced
  // rather than unpriced ON PURPOSE: PRAYER_KEEP saves "the dearest PRICED
  // thing you carry", and a weapon whose entire argument is about being nearly
  // dead must be a thing prayer can be asked to save. It just cannot be asked
  // to save it from snapping.""",
     """  // §7cm: priced for the bones rather than the work -- two dragon-bones is a
  // thousand and the haft is nothing. Nobody buys it: see the note above, and
  // §6l, which repealed selling altogether.
  //
  // Priced rather than unpriced ON PURPOSE: PRAYER_KEEP saves "the dearest
  // PRICED thing you carry", and a weapon whose entire argument is about being
  // nearly dead must be a thing prayer can be asked to save. It just cannot be
  // asked to save it from snapping."""),
]

CHECK = """
  const A = (await import('./engine.js')).default
  const B = (await import('./_engine_check.js')).default
  const ka = Object.keys(A).sort(), kb = Object.keys(B).sort()
  if (ka.join() !== kb.join()) { console.log('EXPORTS DIFFER'); process.exit(1) }
  let bad = 0
  for (const k of ka) {
    const a = A[k], b = B[k]
    if (typeof a === 'function') continue
    const sa = JSON.stringify(a instanceof Set ? [...a].sort() : a)
    const sb = JSON.stringify(b instanceof Set ? [...b].sort() : b)
    if (sa !== sb) { bad++; console.log('  ' + k + ' CHANGED') }
  }
  console.log('CHECK ' + ka.length + ' exports compared, ' + bad + ' changed')
  process.exit(bad ? 1 : 0)
"""


def main(apply):
    src = open(ENGINE).read()
    out = src
    for old, new in EDITS:
        if out.count(old) != 1:
            print('  NOT FOUND (%d matches), nothing written:\n    %s'
                  % (out.count(old), old.strip().splitlines()[0][:88]))
            return 1
        out = out.replace(old, new, 1)
    print('  %d comments, %d bytes -> %d' % (len(EDITS), len(src), len(out)))
    if not apply:
        print('\nnothing written. run with --apply to do it.')
        return 0

    tmp = os.path.join(BRIDGE, '_engine_check.js')
    open(tmp, 'w').write(out)
    r = subprocess.run(['node', '--input-type=module', '-e', CHECK],
                       cwd=BRIDGE, capture_output=True, text=True)
    print((r.stdout + r.stderr).strip()[-700:])
    os.remove(tmp)
    if r.returncode:
        print('\nthe world is not the same world. nothing changed.')
        return 1
    shutil.copy(ENGINE, ENGINE + '.before-stale')
    open(ENGINE, 'w').write(out)
    print('\ndone. the world is now named:')
    subprocess.run(['shasum', '-a', '256', ENGINE])
    return 0


if __name__ == '__main__':
    sys.exit(main('--apply' in sys.argv))
