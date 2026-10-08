#!/usr/bin/env python3
"""Give the handgonne a gambit of its own, and correct four stale comments.

THE HANDGONNE'S KIND WAS DOING NOTHING. It is written `gambit: 'flurry'`, and
a flurry is "several blows land in one tick", but §6af-vii scaled every burst
down when a citizen's flesh became a flat sixty-four: four of the seven gambits
could empty a bar in one interval and the handgonne could do it in all three
styles. Its blows were collapsed to ONE and the damage went into that shot,
`hit: 36`, which is by a distance the hardest blow in the world, paid for with
the worst accuracy at minus twenty and the slowest cadence at every four.

So the label was inert: the flurry branch loops over `blows`, and looping once
is an ordinary blow. The handbook printed the contradiction plainly, kind
`flurry` beside blows `1`, which is how it was noticed.

`report` is a gun's discharge, and this engine already reaches for the word:
§6av, "both barrels are one report, and no louder". It is not a word any other
game's mechanic wears, which is the standing rule about naming in this world.

NO BEHAVIOUR CHANGES. Nothing branches on `flurry` except the default blow
count, and the handgonne states its own, so the loop still runs once and the
damage, accuracy, reach and recovery are all untouched. This names what the
weapon already does.

AND FOUR COMMENTS THAT NO LONGER DESCRIBE THE CODE. Three of them misled a
reader of this file today:

  * the §6af list says "three of them", names `quick-mell` as `'now'` twice
    when the table has it as `'whole'`, still lists a `'true'` kind that was
    retired, and never mentions `'whole'` at all;
  * the `far` note says a gambit "costs TWO ordinary blows", which is the
    DEFAULT recovery, twice a weapon's cadence. Every weapon with a gambit
    states its own, so the default never applies and the real cost runs from
    three quarters of a blow to four;
  * §6df already spotted that one and left a note pointing at it rather than
    fixing it, so the note goes too;
  * the `BOOKS` summary says `seal  shut a way`. §6bn changed that spell to
    lock a dead citizen's dropped pack so only they can lift it, and hold off
    the rot while it lasts.

  gambit_report.py            say what would change
  gambit_report.py --apply    change it
"""
import os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BRIDGE = os.path.join(os.path.dirname(ROOT), 'interval-bridge')
ENGINE = os.path.join(BRIDGE, 'engine.js')

EDITS = [
    # ---- the kind itself ----
    ("  'handgonne':     { gambit: 'flurry', blows: 1, rec: 3, hit: 36, every: 4, reach: 4,   // §6af-vii",
     "  'handgonne':     { gambit: 'report', blows: 1, rec: 3, hit: 36, every: 4, reach: 4,   // §6af-vii"),

    # ---- the list of kinds, which described three and had two of them wrong ----
    ("""//   'flurry' quick-dagger, horn-bow, handgonne -- several blows land in one
//            tick. Was 'twice' until it stopped being two, and the horn-bow
//            briefly had 'volley', which was the same mechanic under a second
//            name. One behaviour, one word.
//   'now'    quick-mell -- gated on a SPENT arm, so it interrupts
//   'far'    dragonbow -- the blow grows with the range it crossed
//   'now'    quick-mell    it swings whatever your arm says
//   'true'   horn-bow     the shot cannot miss""",
     """//   'flurry' quick-dagger, horn-bow -- several blows land in one tick. Was
//            'twice' until it stopped being two, and the horn-bow briefly had
//            'volley', which was the same mechanic under a second name. One
//            behaviour, one word.
//   'whole'  quick-mell, great-mell -- one blow at the weapon's hardest, with
//            the accuracy scaled down to pay for it. It waits for the arm.
//   'now'    fire-siphon -- gated on a merely SPENT arm rather than the full
//            cadence, so it interrupts. It pays the recovery in full after.
//   'far'    dragonbow -- the blow grows with the range it crossed, INSTEAD of
//            the weapon's own weight and not as well as it.
//   'report' handgonne -- one shot with everything in it. §6af-vii collapsed
//            its burst to a single blow when flesh became flat, and the damage
//            went into `hit: 36`, the hardest in the world, against the worst
//            accuracy in the world. Nothing branches on this name: it exists
//            so the table stops calling a single shot a flurry.
//
// 'true' is NOT in this list and must not come back: it made the horn-bow
// unmissable, and certainty cannot be priced, because its worth scales
// inversely with the target's hit rate and no fixed recovery is neutral across
// armour. See the note in the blow loop, which still guards the name."""),

    # ---- what a gambit costs, which is not two blows ----
    ("""        // AND IT MUST BE DAMAGE-NEUTRAL AT ITS BEST, which is the rule every
        // other gambit in this world obeys. A gambit spends the arm for this
        // cycle AND the next, so it costs TWO ordinary blows; 'flurry' pays two
        // blows back, 'true' pays certainty, 'now' pays timing. At three""",
     """        // AND IT MUST BE DAMAGE-NEUTRAL AT ITS BEST, which is the rule every
        // other gambit in this world obeys. What a gambit costs is its
        // RECOVERY measured against that weapon's own cadence, `rec / every`,
        // and it is not the same for any two of them: four ordinary blows for
        // a quick-dagger, three for a horn-bow, two for a mell or a dragonbow,
        // one and a half for a great-mell, three quarters for a handgonne. The
        // default is twice the cadence and no weapon uses it. Each kind pays
        // that cost back in its own coin: 'flurry' in blows, 'whole' in size,
        // 'now' in timing, 'far' in distance, 'report' in one enormous and
        // unreliable shot. At three"""),

    # ---- and the note that pointed at it ----
    ("""        // fired both barrels off a single load. The comment below still says a
        // gambit "costs TWO ordinary blows" and `flurry` "pays two blows back"
        // -- which was true when a flurry WAS two blows. §6af-iii raised it to
        // six and lengthened the recovery to match, correctly, for the damage;
        // nobody came back for the ammunition.""",
     """        // fired both barrels off a single load. The comment below used to say
        // a gambit "costs TWO ordinary blows" and `flurry` "pays two blows
        // back" -- true when a flurry WAS two blows. §6af-iii raised it to six
        // and lengthened the recovery to match, correctly, for the damage;
        // nobody came back for the ammunition, and nobody came back for the
        // comment either until it had misled a reader. It is corrected now."""),

    # ---- and the spell that stopped shutting a way ----
    ("  //   seal      shut a way",
     """  //   seal      hold a dropped pack for whoever lost it
  //             (§6bn: only they may lift it, and it does not rot meanwhile)"""),
]


def main(apply):
    src = open(ENGINE).read()
    out = src
    for old, new in EDITS:
        if old not in out:
            print('  NOT FOUND, nothing written:\n    %s' % old.strip()[:96])
            return 1
        out = out.replace(old, new, 1)
    # NOT a line diff. Two of these edits change how many lines a comment
    # block has, so a zipped line-by-line count reports every line after the
    # first insertion as different and prints a number like fifteen thousand,
    # which is alarming and meaningless.
    print('  %d edits, %d bytes -> %d' % (len(EDITS), len(src), len(out)))
    if not apply:
        print('\nnothing written. run with --apply to do it.')
        return 0

    tmp = os.path.join(BRIDGE, '_engine_check.js')
    open(tmp, 'w').write(out)
    # THE WORLD IS ASKED WHETHER IT STILL WORKS BEFORE ANY OF THIS IS KEPT.
    js = """
      const A = (await import('./engine.js')).default
      const B = (await import('./_engine_check.js')).default
      const ka = Object.keys(A).sort(), kb = Object.keys(B).sort()
      if (ka.join() !== kb.join()) { console.log('EXPORTS DIFFER'); process.exit(1) }
      let bad = 0
      for (const [w, v] of Object.entries(A.WEAPONS)) {
        const u = B.WEAPONS[w]
        for (const f of ['blows', 'rec', 'hit', 'every', 'reach', 'acc']) {
          if ((v ?? {})[f] !== (u ?? {})[f]) { bad++; console.log('  ' + w + '.' + f + ' moved') }
        }
      }
      const kinds = (M) => Object.fromEntries(Object.entries(M.WEAPONS)
        .filter(([, v]) => v && v.gambit).map(([w, v]) => [w, v.gambit]))
      console.log('kinds before: ' + JSON.stringify(kinds(A)))
      console.log('kinds after : ' + JSON.stringify(kinds(B)))
      console.log('CHECK exports ' + ka.length + ', weapon numbers moved ' + bad)
      process.exit(bad ? 1 : 0)
    """
    r = subprocess.run(['node', '--input-type=module', '-e', js],
                       cwd=BRIDGE, capture_output=True, text=True)
    print((r.stdout + r.stderr).strip()[-900:])
    os.remove(tmp)
    if r.returncode:
        print('the changed world does not match the old one. nothing changed.')
        return 1
    shutil.copy(ENGINE, ENGINE + '.before-report')
    open(ENGINE, 'w').write(out)
    print('\ndone. the world is now named:')
    subprocess.run(['shasum', '-a', '256', ENGINE])
    return 0


if __name__ == '__main__':
    sys.exit(main('--apply' in sys.argv))
