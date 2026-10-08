#!/usr/bin/env python3
"""GO SOMEWHERE FAR, BY CLICKING THE MAP, AND KEEP GOING WHEN IT STICKS.

`trek` clicks the WORLD, which can only ask for ground the camera can see --
about six tiles -- and answers a wall with greedy sidesteps that lose to any
building with a corner. `far` clicks the MINIMAP, which hands the whole request
to the window's own A* and routes round buildings properly; what it has never
had is patience. This is the patience.

The recovery is the interesting part. When two clicks in a row leave the
citizen where they were, the router has decided the way it wanted is shut --
so the next click is aimed deliberately SIDEWAYS, alternating left and right of
the bearing and reaching further each time. That is what a person does when a
barn is in the way, and it is the only thing that reliably clears the walled
capitals, whose walls are long enough that a one-tile sidestep just meets more
wall.
"""
import math, subprocess, sys, time

HAND = '/Users/matsjulner/Documents/Unreal Projects/interval/Tools/hand.py'


def run(*args):
    return subprocess.run(['python3', HAND] + list(args),
                          capture_output=True, text=True).stdout.strip()


def here():
    out = run('here')
    for line in reversed(out.splitlines()):
        if line.startswith('['):
            x, y = line.strip('[]').split(',')
            return int(x), int(y)
    return None


def journey(tx, ty, patience=200, close=3, by='isle'):
    """`by` is which map to click.

    'isle' is the world map and is the right answer for anything further than
    the minimap draws. It is north-up and does not move, so a click on it is
    simply the place -- where the minimap turns with the camera and has to be
    read back through a yaw that is still interpolating while the citizen
    walks, which is a small error over five tiles and a large one over fifty.
    """
    was, stuck, swing = None, 0, 0
    for step in range(patience):
        at = here()
        if not at:
            print('lost sight of the citizen'); return None
        gap = math.hypot(tx - at[0], ty - at[1])
        print('%3d  at %d,%d  %d tiles out' % (step, at[0], at[1], gap), flush=True)
        if gap <= close:
            print('arrived'); return at
        if at == was:
            stuck += 1
        else:
            stuck, swing = 0, 0
        was = at
        if stuck >= 2:
            # SIDEWAYS, further each time, alternating hand. The bearing is
            # kept so the detour is still broadly toward where we are going.
            swing += 1
            turn = math.radians(55 * (1 if swing % 2 else -1))
            reach = 12 + 6 * (swing // 2)
            b = math.atan2(ty - at[1], tx - at[0]) + turn
            ax = at[0] + int(round(reach * math.cos(b)))
            ay = at[1] + int(round(reach * math.sin(b)))
            print('     stuck; going round by %d tiles to %d,%d' % (reach, ax, ay), flush=True)
            run(by, str(ax), str(ay))
            time.sleep(reach + 6)
            continue
        # ---- IN BOUNDED HOPS, NOT IN ONE ENORMOUS ASK ----
        #
        # A click on the island map can name a place two hundred tiles away,
        # and the window's router will honestly try to solve the whole thing
        # at once. Over that distance it is solving mostly ground it has never
        # been sent, against a patience of a couple of dozen replans, and when
        # it gives up it gives up on the WHOLE journey -- which from outside
        # looks like a citizen standing on a beach doing nothing at all, over
        # and over, which is exactly what happened.
        #
        # Forty tiles at a time is about what the router reliably solves, and
        # it is also how a person travels: you aim at the next thing you can
        # see your way to, not at the far coast.
        # FIFTEEN, AND THE NUMBER MATTERS.
        #
        # The window routes over ground it has actually been SENT -- the
        # chunks around the citizen -- and treats everything beyond as
        # unreachable, which is honest. Ask it for forty tiles and the goal is
        # outside that entirely: no route exists, nothing is filed, and the
        # citizen stands on a beach while the router quietly re-plans a
        # journey it cannot make. That is exactly what it looked like from the
        # outside, and it cost ten minutes of a ninety-minute day.
        #
        # Fifteen is comfortably inside the loaded region at every camera
        # distance, so every hop is a route the window can actually see.
        HOP = 15.0
        if gap > HOP:
            ax = at[0] + int(round((tx - at[0]) * HOP / gap))
            ay = at[1] + int(round((ty - at[1]) * HOP / gap))
        else:
            ax, ay = tx, ty
        run(by, str(ax), str(ay))
        # A TICK A TILE, which is what the world charges, plus a little for the
        # route to be planned and the first step to be filed.
        time.sleep(min(gap, HOP) + 6)
    print('gave up short'); return here()


if __name__ == '__main__':
    # WHICH MAP TO CLICK, because the island map has to be OPEN to be clicked
    # and the minimap never is not. `isle_face` reads the last geometry the
    # world map logged, and a log survives the editor that wrote it -- so with
    # the tab shut it aims at a rectangle from a previous session and every
    # click lands on the ground behind it, which from outside looks exactly
    # like a citizen who has decided not to walk anywhere.
    #
    #   journey.py X Y          -- the island map (open its tab first)
    #   journey.py X Y far      -- the minimap, which is always there
    journey(int(sys.argv[1]), int(sys.argv[2]),
            by=sys.argv[3] if len(sys.argv) > 3 else 'isle')
