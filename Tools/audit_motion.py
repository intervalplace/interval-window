#!/usr/bin/env python3
"""WHICH DEEDS HAVE AN ANIMATION AND WHICH DO NOT.

The standing goal for this window is that every word the world uses is drawn
properly, every thing a citizen can DO is wired, and every deed has its own
animation. The first two are measured: `coverage.sh` counts the verbs a mouse
can reach, and `audit_art.py` counts the meshes that are dressed and sized.
Nothing measured the third, so this does.

It reads the engine's own list of verbs and the `MOTIONS` table in apply.py,
and says which verbs a citizen performs with no motion of their own -- they
fall back to standing still, which is not wrong so much as silent: the deed
happens, the feed says so, and the figure does not move.

A verb the world does TO a citizen wants no animation and is not counted.

  audit_motion.py
"""
import os, re, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)

# THE ENGINE THIS WINDOW ACTUALLY PLAYS, not a copy of one.
#
# This pointed at a download folder, so it was auditing the window against a
# different world: it went on reporting `transmute` as a verb with no animation
# after the world had renamed that spell to `transmute`, and it would have
# stayed silent about any verb the real engine gained. An audit aimed at the
# wrong world passes and fails for the wrong reasons.
ENGINE = os.path.join(SP, '..', '..', 'interval-bridge', 'engine.js')
# Same list `coverage.mjs` keeps, and for the same reason: a body rots and an
# hour wakes you. Nobody animates those.
NOT_OURS = {'move', 'rot', 'spawn', 'stop', 'taking', 'turn', 'waking',
            'withering'}

def engine_verbs():
    src = open(ENGINE).read()
    return sorted(set(re.findall(r"inp\.type === '([a-z_]+)'", src)))

def motion_keys():
    """The verbs `apply.py` names a motion for, read from its source.

    NOT BY IMPORTING IT. `apply.py` talks to a running editor from its first
    line, so importing it to read one table means starting Unreal -- which is
    four minutes to answer a question that is answerable from the text.

    The table is a literal followed by a handful of `for _x in (...)` loops
    that fill it, so both shapes are read: quoted keys inside the `MOTIONS = {`
    block, and the tuples of every loop that assigns into `MOTIONS[...]`.
    """
    src = open(os.path.join(SP, 'apply.py')).read()
    at = src.index('MOTIONS = {')
    block = src[at:src.index('\n}', at)]
    keys = set(re.findall(r"^\s*'([a-z_]+)':", block, re.M))
    for loop in re.finditer(
            r"for _\w+ in \(([^)]*)\):\s*\n\s*MOTIONS\[_\w+\]", src):
        keys |= set(re.findall(r"'([a-z_]+)'", loop.group(1)))
    keys |= set(re.findall(r"MOTIONS\['([a-z_]+)'\]", src))
    return keys


# ---- AND THE OTHER HALF OF THE QUESTION, WHICH THIS DID NOT ASK ----
#
# "Does this verb have a motion" is not the same as "can this motion ever
# play", and for a long time only the first was measured. The window settles a
# figure's animation from the world's `deed` or from `action.type`, and the
# engine writes `deed` only for the verbs in its own DEEDS list. A motion keyed
# on anything else is a clip in the project that nothing can ever ask for.
#
# Counted by rows, the table read 82 of 82. Counted by what the world can
# actually NAME, fifty-four of those clips were unreachable, including every
# gambit and all four spells of the barrow book. The engine records them now.
# This keeps the count honest from here on.
# WHAT THE WINDOW NAMES FOR ITSELF, read from the C++ rather than listed, so a
# clip reached by the walking path is not reported as dead. `walk` and `idle`
# never come from a verb at all: they come from whether the figure moved.
def window_names():
    cpp = os.path.join(SP, '..', 'Plugins', 'IntervalBridge', 'Source',
                       'IntervalBridge', 'Private', 'IntervalCitizens.cpp')
    return set(re.findall(r'TEXT\("([a-z_]+)"\)', open(cpp).read()))


# AND THE VERBS THE WORLD KEEPS PRIVATE ON PURPOSE. Everything a citizen does
# that a bystander would see is written down as a deed. These are the rest:
# talk, bookkeeping, and two that are nobody else's business. A motion keyed on
# one of them cannot play, and that is the intended answer rather than a fault
# -- but it is written here, with the reason, so the judgement can be argued
# with instead of being invisible.
KEPT_PRIVATE = {
    # said rather than done: only the acceptance moves anything, and that is a deed
    'offer_trade', 'cancel_trade',
    # an apprenticeship is three conversations
    'teach', 'attend', 'part',
    # who you walk behind, and who you count a friend
    'follow', 'unfollow', 'befriend', 'unfriend',
    # what you call yourself and what you wear, which are yours
    'claim_name', 'set_look',
    # bookkeeping: a price chalked up, a chart read, a citizen shelved or
    # brought back, and the two the world does to a body rather than the other
    # way round
    'price_market', 'read_chart', 'archive', 'restore', 'move', 'spawn',
    # §6ch: the waystones are gone, so this is refused for everyone forever
    'recall',
    # the verb that starts the `raise` action; the window is told the action
    'raise_market',
}


def world_can_name():
    src = open(ENGINE).read()
    verbs = set(re.findall(r"inp\.type === '([a-z_]+)'", src))
    at = src.index('const DEEDS = [')
    deeds = set(re.findall(r"'([a-z_]+)'", src[at:src.index('];', at)]))
    acts = set(re.findall(r"action\s*=\s*\{[^}]*type:\s*'([a-z_]+)'", src))
    # a handler may name a deed the input did not: taking forage arrives as
    # `pickup` and is eating, so the word is overwritten after the act
    own = set(re.findall(r"\.deed = '([a-z_]+)'", src))
    return (deeds & (verbs | own)) | acts


WINDOW_NAMES = window_names()


def main():
    motions = motion_keys()
    verbs = [v for v in engine_verbs() if v not in NOT_OURS]
    # A motion may be keyed on the verb, or on `verb.something` for a deed
    # whose animation depends on what it is done to (gather at a tree, at a
    # rock, at the water).
    has = {k.split('.')[0] for k in motions}
    missing = [v for v in verbs if v not in has]
    named = world_can_name() | WINDOW_NAMES
    unreachable = sorted(v for v in has if v in engine_verbs()
                         and v not in named and v not in KEPT_PRIVATE)
    print('')
    print('  verbs a citizen performs      %d' % len(verbs))
    print('  with a motion of their own    %d' % (len(verbs) - len(missing)))
    print('  standing still                %d' % len(missing))
    print('')
    if missing:
        print('  NO ANIMATION:')
        for i in range(0, len(missing), 7):
            print('   ', ' '.join(missing[i:i + 7]))
        print('')
    print('  %d verbs named in the motions table' % len(motions))
    print('  %d of them nothing can ever ask for' % len(unreachable))
    if unreachable:
        for i in range(0, len(unreachable), 7):
            print('   ', ' '.join(unreachable[i:i + 7]))
    print('')
    print('  %s' % ('PASS' if not missing and not unreachable
                    else 'FAIL: a clip nobody can ask for is not an animation'))

main()

# ---- AND THE GAMBITS, WHICH ARE NAMED IN TWO PLACES ----
#
# `deedsfx.py` maps each weapon that has a gambit to one of the four kinds, so
# that `apply.py` can name a sound for it without loading the engine, which it
# cannot do from inside the editor. That table is a copy of a fact the world
# owns, and a copy can drift. This is the thing that notices.
def gambits():
    import re
    src = open(ENGINE).read()
    world = dict(re.findall(r"'([a-z-]+)':\s*\{[^}]*?gambit:\s*'([a-z]+)'", src))
    sys.path.insert(0, SP)
    from deedsfx import GAMBIT_KIND as ours
    print()
    print('  gambits in the world      %4d' % len(world))
    print('  gambits the window knows  %4d' % len(ours))
    for w in sorted(set(world) | set(ours)):
        if world.get(w) != ours.get(w):
            print('    %-16s world says %-8s window says %s'
                  % (w, world.get(w, 'none'), ours.get(w, 'none')))
    if world == ours:
        print('  they agree')


gambits()
