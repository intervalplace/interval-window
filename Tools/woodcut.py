#!/usr/bin/env python3
"""A DAY'S WOODCUTTING, START TO FINISH, THROUGH THE WINDOW.

Everything here is a gesture a person makes: a click on the island map to
travel, a right click on the stall to buy, a right click in the pack to wield,
a left click on a tree to chop. Nothing calls a deed directly -- that is the
harness, and a window that can only be played by a harness is not a window.

The route is the one the world actually has, measured rather than assumed:
a citizen is born at Anchor, the only lumber stall on the island is in
Millbrook seventy-two tiles north, and the nearest fellable tree is sixty-six
tiles west of that. There is no shorter way; see Tools/conflicts.sh and the
worldgen notes for why that is the design and not a fault.

  woodcut.py            -- the whole run
  woodcut.py chop       -- just the chopping, if already standing at a tree
"""
import json
import math
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
HAND = os.path.join(HERE, 'hand.py')
S = ('/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/'
     'd4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/')

STALL = (452, 208)        # the lumber keeper's counter, in Millbrook
BESIDE = (452, 210)       # open ground beside it, which a citizen can stand on
TREES = [(396, 197), (396, 198)]
BY_THE_TREES = (397, 198)
ISLAND_TAB = (3990, 1633)  # the fourth door, above the pack

# The pack is three across and four down; these are the centres of its twelve
# sockets in viewport pixels, measured off a screenshot rather than derived
# from the layout constants, because the layout has moved twice this session.
PACK_COLS = (3734, 3851, 3971)
PACK_ROWS = (1784, 1906, 2028, 2150)
# A menu opens at the cursor and its first line sits about this far below it.
FIRST_LINE = 88


def hand(*args, quiet=True):
    out = subprocess.run(['python3', HAND] + [str(a) for a in args],
                         capture_output=True, text=True).stdout.strip()
    if not quiet:
        print('   ', out.splitlines()[-1] if out else '(nothing)', flush=True)
    return out


def here():
    for line in reversed(hand('here').splitlines()):
        if line.startswith('['):
            x, y = line.strip('[]').split(',')
            return int(x), int(y)
    return None


def me():
    """What the world says about this citizen, right now.

    THE WHOLE POINT OF THIS FUNCTION. The first version of this script did the
    right gestures in the right order, logged every one of them as done, and
    achieved NOTHING: the buy was dropped because the citizen was still two
    tiles from the counter, so there was no hatchet, so thirty swings at a tree
    with bare hands produced no logs and no skill -- and the log said
    "swing 30" thirty times.
    #
    A script that cannot read a screen must ask the world instead. Every step
    below now checks its own work against this, and a step that did not take
    is retried rather than logged as done.
    """
    try:
        out = subprocess.run(['zsh', os.path.join(HERE, 'mestate.sh')],
                             capture_output=True, text=True, timeout=30)
        return json.loads(out.stdout.strip())
    except Exception:
        return {}


def left():
    return me().get('left', '?')


def say(what):
    print('%s  %s' % (time.strftime('%H:%M:%S'), what), flush=True)


def island(on):
    """Open or close the island map. It is a toggle, like every tab."""
    hand('click', *ISLAND_TAB)
    time.sleep(2)


def travel(tx, ty, patience=40):
    """Walk somewhere by clicking it on the world map, and keep at it.

    Fifteen tiles a hop: the window routes over ground it has actually been
    sent, and a longer ask is a route through country it cannot see, which it
    honestly refuses. See Tools/journey.py for the same reasoning.
    """
    island(True)
    was, stuck = None, 0
    for step in range(patience):
        at = here()
        if not at:
            say('lost sight of the citizen'); island(False); return None
        gap = math.hypot(tx - at[0], ty - at[1])
        say('  at %d,%d  %d tiles from %d,%d' % (at[0], at[1], gap, tx, ty))
        if gap <= 2:
            island(False); return at
        stuck = stuck + 1 if at == was else 0
        was = at
        if stuck >= 2:
            # Round whatever is in the way, alternating hand and reaching
            # further each time -- a barn's wall is longer than one sidestep.
            turn = math.radians(60 * (1 if stuck % 2 else -1))
            b = math.atan2(ty - at[1], tx - at[0]) + turn
            hand('isle', at[0] + int(round(14 * math.cos(b))),
                 at[1] + int(round(14 * math.sin(b))))
            time.sleep(22)
            continue
        hop = min(gap, 15.0)
        hand('isle', at[0] + int(round((tx - at[0]) * hop / gap)),
             at[1] + int(round((ty - at[1]) * hop / gap)))
        time.sleep(hop + 8)
    island(False)
    return here()


def buy_hatchet(tries=6):
    """Ask the keeper, and keep asking until the gold actually moves.

    A buy is DROPPED if the citizen is not standing at the counter -- the hand
    says "lumber is 2 tiles off; walking there first" and the deed is
    abandoned, which reads in a log as a purchase that happened. So this
    watches the purse: twenty gold leaving it is the only proof there is.
    """
    before = me().get('gold', 0)
    for i in range(tries):
        hand('ground')
        hand('pick', STALL[0], STALL[1], 0)
        time.sleep(14)
        now = me()
        if 'iron-hatchet' in (now.get('pack') or []):
            say('  bought it -- %d gold left' % now.get('gold', -1))
            return True
        say('  the counter did not answer (gold still %s); stepping up and '
            'asking again' % now.get('gold'))
        # A pace closer each time: the stall wants a citizen at its counter.
        hand('isle', BESIDE[0], BESIDE[1])
        time.sleep(12)
    return False


def wield_hatchet(tries=4):
    """Right click the hatchet and take `wield`, then check the world agrees."""
    for i in range(tries):
        pack = me().get('pack') or []
        if 'iron-hatchet' not in pack:
            return me().get('weapon') == 'iron-hatchet'
        slot = pack.index('iron-hatchet')
        x = PACK_COLS[slot % 3]
        y = PACK_ROWS[slot // 3]
        hand('right', x, y)
        time.sleep(1.5)
        hand('click', x, y + FIRST_LINE)
        time.sleep(5)
        if me().get('weapon') == 'iron-hatchet':
            say('  wielded')
            return True
    return False


ROW_STEP = 62          # how far apart a menu's lines are, in viewport pixels


def empty_the_pack():
    """Put the LOGS down, and nothing else.

    TWO THINGS THIS GETS RIGHT THAT THE FIRST VERSION DID NOT.
    
    It clicks the line that says `drop`, not the first line. `drop` is sorted
    LAST on purpose -- so that a left click can never throw away the sword
    somebody just walked sixty tiles for -- and the moment fletching was added
    the first line on a log became "fletch a bow". The sweep dutifully made
    four bows, a wand and a torch, and un-wielded the hatchet. Funny once.
    Which line is `drop` now comes from the world, in `dropRow`.

    And it touches only logs. The hatchet lives in the pack between swings and
    a sweep that took everything took that too.
    """
    now = me()
    pack = now.get('pack') or []
    rows = now.get('dropRow') or []
    put = 0
    for slot, item in enumerate(pack):
        if not item or 'log' not in item:
            continue
        row = rows[slot] if slot < len(rows) else 0
        x = PACK_COLS[slot % 3]
        y = PACK_ROWS[slot // 3]
        hand('right', x, y)
        time.sleep(0.7)
        hand('click', x, y + FIRST_LINE + row * ROW_STEP)
        time.sleep(0.7)
        put += 1
    say('  put down %d logs' % put)
    return put


def chop(rounds=260):
    """Swing at a tree, over and over, the way a person does."""
    hand('ground')
    swings = 0
    for i in range(rounds):
        at = here()
        if not at:
            break
        tree = min(TREES, key=lambda t: abs(t[0] - at[0]) + abs(t[1] - at[1]))
        hand('go', *tree)
        swings += 1
        time.sleep(13)
        # ELEVEN SWINGS FILLS A PACK. Twelve sockets, one of them holding the
        # arrows a citizen is born with, and a log to a swing.
        if swings % 10 == 0:
            now = me()
            logs = sum(1 for i in (now.get('pack') or []) if i and 'log' in i)
            say('  swing %d -- woodcraft %s, %s logs, %s min left'
                % (swings, now.get('woodcraft'), logs, now.get('left')))
            if now.get('stoodDown'):
                say('  the day is spent'); break
            # ONLY SWEEP A PACK THAT HAS SOMETHING IN IT. The first version
            # swept regardless and threw away the arrows a citizen is born
            # with, for nothing.
            if logs >= 2:
                empty_the_pack()
    return swings


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'chop':
        chop(); return
    say('setting off from %s' % (here(),))
    say('to the lumber stall at %d,%d' % BESIDE)
    travel(*BESIDE)
    say('buying a hatchet')
    if not buy_hatchet():
        say('could not buy a hatchet; stopping rather than swinging at a tree '
            'with bare hands'); return
    say('wielding it')
    if not wield_hatchet():
        say('bought it and could not wield it; stopping'); return
    say('to the trees at %d,%d' % BY_THE_TREES)
    travel(*BY_THE_TREES)
    say('chopping')
    chop()
    say('done, %s min left' % left())


if __name__ == '__main__':
    main()
