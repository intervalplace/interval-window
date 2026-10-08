#!/usr/bin/env python3
"""WHICH DEEDS CAN BE HEARD, AND WHICH ROWS CAN NEVER PLAY.

`audit_motion.py` asks which verbs have an animation. This asks the same
question of the noise, and it asks a second one the motion audit did not:
whether a row in the table can ever be REACHED.

WHY THAT SECOND QUESTION IS THE WHOLE POINT. The window plays a noise for a
citizen by reading the world's `deed`, which the engine sets only for the verbs
in its own `DEEDS` list, or by reading `action.type`, which only four verbs ever
set. A row keyed on anything else is a wav on disk with no path to a speaker.

Counting the ROWS says the table is full. Counting what the world can NAME says
how much of it is audible. The two disagreed by sixteen noises and fifty-four
animations, including every gambit, the whole barrow book, and the axe -- all
written, all wired, none of them reachable. An audit that counts rows passes
while the world is silent.

  audit_sound.py
"""
import os, re, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)

ENGINE = os.path.join(SP, '..', '..', 'interval-bridge', 'engine.js')

# The four verbs that set an `action` instead of leaving a `deed`. They run on
# by themselves and the window sounds them once per interval for as long as
# they last. Read from the engine rather than listed, so a fifth cannot appear
# without this noticing.
def engine_words():
    src = open(ENGINE).read()
    verbs = set(re.findall(r"inp\.type === '([a-z_]+)'", src))
    at = src.index('const DEEDS = [')
    deeds = set(re.findall(r"'([a-z_]+)'", src[at:src.index('];', at)]))
    acts = set()
    for m in re.finditer(r"action\s*=\s*\{[^}]*type:\s*'([a-z_]+)'", src):
        acts.add(m.group(1))
    # AND THE DEEDS THE ENGINE NAMES FOR ITSELF. A deed is normally the verb a
    # citizen sent, but a handler may overwrite it where the verb does not
    # describe what happened: taking forage arrives as `pickup` and is eating.
    # Such a word is not an `inp.type` and is still a real deed, so it counts.
    own = set(re.findall(r"\.deed = '([a-z_]+)'", src))
    return verbs | own, deeds, acts


def main():
    verbs, deeds, acts = engine_words()
    # WHAT THE WINDOW CAN EVER BE TOLD. A deed the world records, or an action
    # it leaves running. Nothing else reaches a speaker.
    named = (deeds & verbs) | acts

    # ---- AND THE WINDOW'S OWN WORDS, WHICH THE WORLD NEVER WRITES ----
    #
    # The world reports hit points and never announces a death, so `felled` is
    # a word this window coins for itself out of health at nothing -- the same
    # way it coins the falling MOTION. It is spoken by the citizens actor
    # rather than read from a frame (see AIntervalCitizens::UpdatePeople), so
    # it is genuinely reachable and this audit cannot see the path.
    #
    # Listed rather than ignored, and listed HERE rather than being quietly
    # dropped from the check, because the check is the thing that catches a row
    # nobody wired. A window word that is not in this set is still a fault.
    WINDOW_WORDS = {'felled'}
    named |= WINDOW_WORDS

    from deedsfx import WORK_SOUNDS, GAMBIT_KIND
    src = open(os.path.join(SP, 'apply.py')).read()
    at = src.index("have['DeedSounds'] = {")
    block = src[at:src.index('\n}', at)]
    spelled = set(re.findall(r"\('([a-z_]+)', [0-9.]+\)", block))
    rows = set(WORK_SOUNDS) | spelled
    # a gambit is only ever done with a weapon, so its rows are all refined
    if GAMBIT_KIND:
        rows.add('gambit')

    # AND THE RITES, which are drawn rather than heard but are looked up by the
    # same word and go wrong the same way.
    at = src.index("have['Rites'] = {")
    rites = set(re.findall(r"\('([a-z_]+)',\s+\w+,",
                           src[at:src.index('\n}', at)]))

    silent = sorted(named - rows)
    unreachable = sorted(rows - named)
    stray_rites = sorted(rites - named)
    deeds_not_verbs = sorted(deeds - verbs)

    print('')
    print('  verbs the world can name     %d' % len(named))
    print('    of them, with a sound      %d' % (len(named) - len(silent)))
    print('    silent                     %d' % len(silent))
    print('')
    if silent:
        print('  SILENT:')
        for i in range(0, len(silent), 6):
            print('   ', ' '.join(silent[i:i + 6]))
        print('')
    print('  sound rows                   %d' % len(rows))
    print('    that can never play        %d' % len(unreachable))
    if unreachable:
        print('     ', ' '.join(unreachable))
    print('  rite rows that can never play %d' % len(stray_rites))
    if stray_rites:
        print('     ', ' '.join(stray_rites))
    print('  DEEDS entries that are not verbs %d' % len(deeds_not_verbs))
    if deeds_not_verbs:
        print('     ', ' '.join(deeds_not_verbs))
    print('')
    bad = len(unreachable) + len(stray_rites) + len(deeds_not_verbs)
    print('  %s' % ('PASS' if bad == 0 else 'FAIL: %d rows name a word the world never writes' % bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
