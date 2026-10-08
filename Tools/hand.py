#!/usr/bin/env python3
"""A REAL HAND: the operating system's own mouse and keyboard, into the window.

WHY THIS EXISTS. `playremote.py` is a keyboard for the HAND -- it calls
AIntervalHand's deeds directly. Everything it files is real, signed and
refusable, but it enters the window below the interface: no pointer moves, no
button is pressed, no widget is hit-tested. A window can therefore pass every
test it runs and still be unplayable, and that is exactly what happened. The
gate was setting `FInputModeGameOnly` the instant a citizen crossed it, which
routes no mouse event to UMG at all; the chat line, the pack slots and the
right-click menu had never once been reachable by a person, and nothing found
it, because nothing had ever tried to CLICK.

So this drives the actual cursor with CGEvents, through cliclick, into whatever
window is in front. It is slower and clumsier than calling a function, which is
the point: it can only do what a player can do.

COORDINATES. Arguments are VIEWPORT PIXELS -- what the engine itself reports,
what a screenshot of the viewport is measured in. The mapping onto screen
points is affine and is measured, never assumed: `hand.py cal` moves the
pointer to three places and asks the engine where it thinks the pointer went.
It has to be measured because the viewport sits at an offset inside the editor
window that depends on the panel layout, and on a Retina display one screen
point is two viewport pixels. Guessing either is a click in the wrong place,
which in this world files the wrong deed.

Re-run `cal` after anything that moves or resizes the editor window.

  hand.py cal
  hand.py move  2000 1100
  hand.py click 2000 1100          # left: the default deed
  hand.py right 2000 1100          # right: every option
  hand.py type  "hello stranger"
  hand.py key   return
  hand.py where                    # what the engine says the pointer is on
  hand.py ground                   # learn viewport <-> world, once per camera
  hand.py go    520 209            # click the TILE at 520,209
  hand.py at    520 209            # right-click it instead
  hand.py trek  754 230            # keep clicking until you get there
  hand.py road  754 230            # ask the map for a route and walk it
  hand.py far   754 230            # click the MINIMAP toward it: one long walk
  hand.py pick  754 230 0          # right-click that tile, take option 0
"""
import json, math, os, subprocess, sys, time

S = ('/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/'
     'd4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/')
MOUSE = S + 'mouse.json'
CAL = S + 'hand.cal.json'
CMD = S + 'play.cmd'


def cliclick(*args):
    subprocess.run(['cliclick', *args], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def front():
    """The editor has to be the front window or the events go elsewhere."""
    subprocess.run(['osascript', '-e',
                    'tell application "System Events" to tell process '
                    '"UnrealEditor" to set frontmost to true'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def asked():
    """What the engine currently believes about the pointer.

    Written by `probe.py`, which runs on the editor's Slate post-tick. The wait
    is not politeness -- the editor drops to a frame every three seconds while
    it is streaming chunks in, and reading the file too soon gives the position
    from BEFORE the move, which reads as a mapping that is subtly wrong rather
    than as a file that is stale.
    """
    was = os.path.getmtime(MOUSE) if os.path.exists(MOUSE) else 0
    for _ in range(60):
        time.sleep(0.5)
        if os.path.exists(MOUSE) and os.path.getmtime(MOUSE) > was:
            try:
                with open(MOUSE) as f:
                    return json.load(f)
            except ValueError:
                continue
    raise SystemExit('the probe is not writing: is it armed, and is PIE up?')


def calibrate(tries=3):
    """Measure the screen-to-viewport map, and insist on a straight answer.

    It fails in one way and one way only: the editor was not the front window
    for part of the sweep, so some of the samples are where the pointer was
    BEFORE it moved. That shows up as a fit that does not pass its own check --
    a residual of hundreds of pixels rather than none -- and the right response
    is to take the sweep again rather than to stop, because the cause is
    transient by nature.
    """
    for attempt in range(tries):
        try:
            return once()
        except SystemExit:
            if attempt == tries - 1:
                raise
            print('  ...the sweep did not hold still; taking it again')
            time.sleep(3)


def once():
    front()
    seen = []
    for sx, sy in ((400, 300), (1600, 900), (900, 600)):
        cliclick('m:%d,%d' % (sx, sy))
        got = asked()
        seen.append((sx, sy, got['x'], got['y']))
        print('screen %5d,%-5d -> viewport %7.0f,%-7.0f' % (sx, sy, got['x'], got['y']))
    (ax, ay, avx, avy), (bx, by, bvx, bvy), _ = seen
    kx = (bvx - avx) / (bx - ax)
    ky = (bvy - avy) / (by - ay)
    cal = {'kx': kx, 'ky': ky, 'ox': avx - kx * ax, 'oy': avy - ky * ay,
           'vw': got['vw'], 'vh': got['vh'], 'scale': got['scale']}
    # The third point is not used to fit; it is used to DISAGREE. A mapping
    # fitted on two points always fits those two points.
    px, py, tvx, tvy = seen[2]
    off = max(abs(kx * px + cal['ox'] - tvx), abs(ky * py + cal['oy'] - tvy))
    cal['residual'] = off
    with open(CAL, 'w') as f:
        json.dump(cal, f, indent=1)
    print('viewport %.0fx%.0f, %.2f px per screen point, origin at screen '
          '%.1f,%.1f, worst check %.1f px'
          % (cal['vw'], cal['vh'], kx, -cal['ox'] / kx, -cal['oy'] / ky, off))
    if off > 2.0:
        raise SystemExit('the mapping is not linear -- something moved mid-calibration')


def ground(tries=3):
    for attempt in range(tries):
        try:
            return ground_once()
        except SystemExit:
            if attempt == tries - 1:
                raise
            print('  ...no ground under the pointer; taking it again')
            time.sleep(3)


def ground_once():
    """Learn how a step across the viewport moves across the world.

    A session is played in tiles -- walk to 520,209, mine the seam at 754,230 --
    and clicking a tile means knowing where on the glass it is. The camera is
    fixed in angle and height and only ever slides to follow the citizen, so
    the 2x2 part of that map is constant and is measured once here; the OFFSET
    changes every time the citizen takes a step and is re-read at the moment of
    each click, from wherever the pointer happens to be.
    """
    # ---- READ, NOT WALKED ----
    #
    # This used to move the pointer to three places and ask where it had
    # landed, and it could not be relied on: `get_mouse_position` answers only
    # after the viewport has PROCESSED a mouse event, and moving the cursor is
    # not one of those. The first sample after a click was right and the second
    # was None every time, which came out as "the probe is not reporting a
    # ground hit: is PIE up?" -- naming the one thing that was fine.
    #
    # The probe deprojects the same three points itself, every tick, from the
    # numbers rather than from the cursor. Nothing here touches the mouse.
    cal = load()
    got = asked()
    fixed = got.get('fixed') or {}
    if not all(k in fixed for k in ('a', 'b', 'c')):
        raise SystemExit('the probe is not reporting its fixed points: re-arm '
                         'it with `exec py <scratchpad>/probe.py`')
    seen = []
    for key, (vx, vy) in (('a', (1400, 800)), ('b', (2600, 800)),
                          ('c', (1400, 1600))):
        seen.append((vx, vy, fixed[key][0], fixed[key][1]))
        print('viewport %5d,%-5d -> world %9.1f,%-9.1f' % (vx, vy, fixed[key][0], fixed[key][1]))
    (ax, ay, awx, awy), (bx, _, bwx, bwy), (_, cy, cwx, cwy) = seen
    # Columns of the matrix: what one viewport pixel of X, and one of Y, do.
    ex = ((bwx - awx) / (bx - ax), (bwy - awy) / (bx - ax))
    ey = ((cwx - awx) / (cy - ay), (cwy - awy) / (cy - ay))
    cal['ex'], cal['ey'] = list(ex), list(ey)
    with open(CAL, 'w') as f:
        json.dump(cal, f, indent=1)
    print('one viewport pixel = %.1f,%.1f across and %.1f,%.1f down'
          % (ex[0], ex[1], ey[0], ey[1]))


def aim(tx, ty):
    """The viewport point standing on tile tx,ty, as things are right now.

    THE MAP IS RE-MEASURED EVERY TIME, because it costs nothing now. It used to
    cost three pointer moves and a wait, so it was measured once and cached --
    and a cached map is wrong the moment the camera turns or zooms, which this
    one does: the gate binds Q and E to turn and the scroll wheel to zoom. Two
    calibrations taken twenty minutes apart differed by a fifth in scale and
    thirty degrees in direction, and the aim that came out of the stale one put
    the cursor on the citizen's own tile when it was asked for the well beside
    them. The probe deprojects its three points every tick; reading them again
    is a file read.
    """
    ground()
    c = load()
    if 'ex' not in c:
        raise SystemExit('run `hand.py ground` first')
    # WHERE WE ARE, ASKED FRESH. The camera has moved if the citizen has --
    # and asked WITHOUT moving the pointer, for the reason in `ground`.
    mx, my = int(c['vw'] * 0.5), int(c['vh'] * 0.5)
    # ---- AND WAITED FOR, BECAUSE THE CAMERA SLIDES ----
    #
    # The camera follows the citizen smoothly, so for a second or so after a
    # walk ends the middle of the screen is not yet the tile they are standing
    # on. Everything here is measured FROM that middle, so an aim taken during
    # the slide is off by however far the camera still had to go -- which came
    # out as right-clicking a well one tile away and getting the citizen's own
    # tile back. Read until it stops moving.
    mid = None
    for _ in range(20):
        now = (asked().get('fixed') or {}).get('mid')
        if not now:
            raise SystemExit('the probe is not reporting where the middle of '
                             'the screen is: re-arm it')
        if mid and abs(now[0] - mid[0]) < 1.0 and abs(now[1] - mid[1]) < 1.0:
            break
        mid = now
    here = {'world': mid}
    # The centre of the wanted tile, not its corner: a click on the seam
    # between two tiles is a coin toss.
    wx, wy = (tx + 0.5) * 200.0, (ty + 0.5) * 200.0
    dx, dy = wx - here['world'][0], wy - here['world'][1]
    (a, b), (cc, d) = c['ex'], c['ey']
    det = a * d - b * cc
    if abs(det) < 1e-9:
        raise SystemExit('the ground map is degenerate -- re-run `hand.py ground`')
    vx = mx + (d * dx - cc * dy) / det
    vy = my + (a * dy - b * dx) / det
    return vx, vy


def here_now():
    """Where the citizen is standing, asked of the window rather than the world.

    The middle of the screen IS the citizen: the camera is fixed in angle and
    height and only slides to follow them. Read off the probe's own deprojected
    centre, so this needs no pointer either.
    """
    mid = (asked().get('fixed') or {}).get('mid')
    if not mid:
        return None
    return [int(mid[0] // 200.0), int(mid[1] // 200.0)]


def trek(tx, ty, patience=200):
    """Walk somewhere further away than the screen.

    A click can only land on ground the citizen can SEE, and this camera shows
    about a dozen tiles across -- so anywhere worth going is dozens of clicks
    away. That is not a limitation of the harness, it is what playing this
    window is actually like, and it is worth saying plainly: there is no map in
    this window and no way to travel except by walking to the edge of what you
    can see, over and over. A player crossing the island does this three
    hundred times.

    Each step aims at the target, clamps the aim to the far edge of the glass
    when the target is beyond it, clicks, and waits roughly the tick per tile
    the world charges for a walk.
    """
    c = load()
    edge = 120.0
    stuck = 0
    was = None
    detour = None      # (dx, dy, steps left) -- see the note below
    for step in range(patience):
        at = here_now()
        if not at:
            raise SystemExit('cannot see where the citizen is standing')
        if at == [tx, ty]:
            print('arrived at %d,%d in %d clicks' % (tx, ty, step))
            return at
        # ROUND THE WALL, WHICH IS WHAT A PLAYER DOES.
        #
        # A click walks TOWARD a place and the world walks as far as it can;
        # with a building in the way that is nowhere at all, and clicking the
        # same spot again does the same nothing forever. The island is walled
        # settlements joined by lanes, so this happens constantly and is not an
        # edge case: a citizen who cannot get round a wall cannot leave the
        # yard they were born in.
        #
        # So when a step moves nobody, the next aim is a short hop in some
        # OTHER direction -- the eight compass points, tried in order of how
        # nearly they still point at the goal, so the first few attempts are a
        # slide along the wall rather than a walk back the way we came. Each
        # further failure takes the next candidate and lengthens the hop. Any
        # success clears the count and the walk resumes straight at the goal.
        stuck = stuck + 1 if at == was else 0
        was = at
        # AND ONCE ROUND, STAY ROUND FOR A WHILE.
        #
        # Sliding one step along a wall and then aiming at the goal again walks
        # straight back into the same wall, which is the loop this spent forty
        # clicks in: out, back, out, back, never more than two tiles from where
        # it started. A detour that works is COMMITTED to for several steps, so
        # the citizen gets clear of the building before pointing at the goal
        # again -- which is how a person walks round a barn.
        if detour and detour[2] > 0 and stuck == 0:
            dx, dy, left = detour
            detour = (dx, dy, left - 1)
            try:
                vx, vy = aim(at[0] + dx * 4, at[1] + dy * 4)
                vx, vy = clear_of_hud(max(0, min(c['vw'] - 1, vx)),
                                      max(0, min(c['vh'] - 1, vy)), c)
                sx, sy = screen(int(vx), int(vy))
                front()
                cliclick('m:%d,%d' % (sx, sy))
                time.sleep(0.35)
                cliclick('c:.')
                print('  ...round the wall, %d more that way' % (left - 1))
                sys.stdout.flush()
                time.sleep(5.0)
                continue
            except SystemExit:
                detour = None
        if stuck >= 2:
            gx, gy = tx - at[0], ty - at[1]
            gl = max((gx * gx + gy * gy) ** 0.5, 1.0)
            ways = sorted(
                ((dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                 if (dx or dy)),
                key=lambda d: -(d[0] * gx + d[1] * gy) / (gl * ((d[0]**2 + d[1]**2) ** 0.5)))
            dx, dy = ways[(stuck - 2) % len(ways)]
            hop = 3 + (stuck - 2) // len(ways) * 3
            ax, ay = at[0] + dx * hop, at[1] + dy * hop
            detour = (dx, dy, 4)
            print('  ...blocked at %s; trying %+d,%+d for %d tiles' % (at, dx, dy, hop))
            sys.stdout.flush()
            try:
                vx, vy = aim(int(ax), int(ay))
            except SystemExit:
                continue
        else:
            vx, vy = aim(tx, ty)
        mx, my = c['vw'] * 0.5, c['vh'] * 0.5
        dx, dy = vx - mx, vy - my
        # CLAMPED ALONG THE LINE, not per-axis: clamping X and Y separately
        # bends the direction and walks the citizen into the scenery beside
        # the path rather than along it.
        span = max(abs(dx) / (mx - edge), abs(dy) / (my - edge), 1.0)
        vx, vy = mx + dx / span, my + dy / span
        vx, vy = clear_of_hud(vx, vy, c)
        sx, sy = screen(int(vx), int(vy))
        front()
        cliclick('m:%d,%d' % (sx, sy))
        time.sleep(0.35)
        cliclick('c:.')
        # The world walks a tile a tick, and a tick is a second.
        reach = (abs(dx / span) * abs(c['ex'][0]) + abs(dy / span) * abs(c['ey'][0])) / 200.0
        waited = min(max(reach, 2.0), 14.0)
        print('  step %2d: at %s, clicked %.0f,%.0f, waiting %.0fs'
              % (step + 1, at, vx, vy, waited))
        sys.stdout.flush()
        time.sleep(waited)
    print('gave up %d clicks short of %d,%d' % (patience, tx, ty))
    return here_now()


def road(tx, ty, sight=80):
    """Walk somewhere properly: read the map, then follow the road.

    `trek` walks AT a place and feels its way round whatever is in front of
    it, which is fine in open country and hopeless in a town. The island is
    walled settlements joined by lanes, and a citizen inside one who aims
    straight at a stall outside it spends fifty clicks bouncing off the same
    building -- which is exactly what happened, and is not a fault in the
    window: it is what a player does when they have not looked at the map.

    So this looks at the map. `Tools/map.sh` reads the walls the frame already
    carries and returns a route through them, broken into STRAIGHT RUNS -- the
    corners, in other words, which are precisely the places a player clicks.
    Each one is then walked to with a real click, in order.
    """
    here = here_now()
    print('reading the map from %s to %d,%d' % (here, tx, ty))
    sys.stdout.flush()
    out = subprocess.run(
        ['zsh', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'map.sh'),
         str(sight), str(tx), str(ty)],
        capture_output=True, text=True, timeout=600).stdout
    line = next((l for l in out.splitlines() if l.startswith('straight runs:')), None)
    if not line:
        print('no route within %d tiles -- walking at it instead' % sight)
        return trek(tx, ty)
    legs = []
    for bit in line.split(':', 1)[1].split('|'):
        parts = bit.split()
        if len(parts) == 3 and parts[0] == 'walk':
            legs.append((int(parts[1]), int(parts[2])))
    print('%d corners to turn' % len(legs))
    sys.stdout.flush()
    for i, (lx, ly) in enumerate(legs):
        print('-- corner %d of %d: %d,%d' % (i + 1, len(legs), lx, ly))
        sys.stdout.flush()
        at = trek(lx, ly, patience=30)
        if at != [lx, ly]:
            # The route was computed from one frame and the world has moved on,
            # or something is standing in the lane. Read the map again from
            # wherever we actually are rather than pressing on down a road that
            # is no longer under our feet.
            print('   did not make that corner; re-reading the map')
            sys.stdout.flush()
            return road(tx, ty, sight)
    print('road walked to %d,%d' % (tx, ty))
    return here_now()


# WHERE THE MENU'S ROWS LAND, relative to the click that opened it.
#
# The menu opens AT the cursor (see IntervalMenu.cpp) with a small header and
# then one row per option, so the rows are at a fixed offset from the click and
# there is no need to photograph the screen and find them by eye every time.
# Measured off two menus at different places and different lengths; a row is
# about thirty UMG units and this viewport draws at 2.09, hence sixty-four.
# The X is a SMALL inset from the plate's left edge, not the middle of a row:
# the plate opens at the cursor and its rows are as wide as their longest
# label, so a middle measured off one menu is outside the next. Forty pixels
# in from the corner is inside every row of every menu. The Y is the header
# plus one row, measured off three of them.
MENU_FIRST = (44, 84)
MENU_ROW = 74


def settle(tries=20):
    """Wait until the citizen has stopped, and the camera with them.

    Aiming at a TILE means asking where the ground is under a given pixel, and
    the camera is still sliding after the citizen stops: a click computed
    mid-slide lands a tile or two off, which for a right click means the menu
    opens on empty ground and for the click after it means walking somewhere
    nobody asked to go. That looked like the menu being unreliable and was
    really the picture still moving.
    """
    was = None
    still = 0
    for _ in range(tries):
        at = here_now()
        still = still + 1 if at == was else 0
        was = at
        if still >= 1:
            return at
        time.sleep(1.0)
    return was


def pick(tx, ty, which):
    """Right-click a tile and take the n-th thing it offers.

    This is two real clicks with the real mouse, in the order a player makes
    them. It is not a shortcut past the menu: if the menu does not open, or
    does not have that many rows, the second click lands on the world and does
    whatever a left click there does -- which is exactly the mistake a player
    makes, and worth being able to see.
    """
    settle()
    vx, vy = aim_true(tx, ty)
    c = load()
    if not (0 <= vx < c['vw'] and 0 <= vy < c['vh']):
        raise SystemExit('tile %d,%d is off the glass' % (tx, ty))
    sx, sy = screen(int(vx), int(vy))
    front()
    cliclick('m:%d,%d' % (sx, sy))
    time.sleep(0.4)
    cliclick('rc:.')
    time.sleep(1.2)
    ox = int(vx) + MENU_FIRST[0]
    oy = int(vy) + MENU_FIRST[1] + which * MENU_ROW
    # The menu is clamped into the viewport when it would run off the edge, so
    # a click near the bottom or the right is not where this thinks it is.
    # Rather than guess at the clamp, refuse and let the caller walk closer.
    if not (0 <= ox < c['vw'] - 8 and 0 <= oy < c['vh'] - 8):
        raise SystemExit('the menu would be off the glass -- stand nearer')
    sx, sy = screen(ox, oy)
    cliclick('m:%d,%d' % (sx, sy))
    time.sleep(0.4)
    cliclick('c:.')
    print('picked option %d on %d,%d (menu row at viewport %d,%d)'
          % (which, tx, ty, ox, oy))


def clear_of_hud(vx, vy, c):
    """Push a point off the interface and back onto the world.

    THE PACK IS IN THE BOTTOM RIGHT AND IT IS CLICKABLE.
    ------------------------------------------------------------------
    `trek` aims at a place beyond the edge of the screen by clamping the point
    back inside it, which puts the click near a border -- and the bottom right
    border is the pack, whose slots do the default thing to whatever is in
    them when clicked. A citizen crossing the island that way quietly emptied
    their own bag: the arrows and the iron pickaxe they had just walked sixty
    tiles and spent twenty gold on were gone, with nothing in any log to say
    where, because dropping a thing you clicked on is not an error.

    This is a fault in the HARNESS and not in the window -- a person does not
    click their own inventory by accident while walking -- but it has to be
    fixed here or no long journey is safe.
    """
    w, h = c['vw'], c['vh']
    # The chat band across the bottom, generously: it is centred and about a
    # fifth of the height, and the input line sits under it.
    if vy > h - 560:
        vy = h - 560
    # And the column at the right: vitals, tabs and the pack.
    if vx > w - 520 and vy > h - 900:
        vx = w - 520
    return vx, vy


def aim_true(tx, ty, tries=4):
    """Aim at a tile and then CHECK, because the ground is not flat.

    `aim` solves a linear map from the screen to the world, which is exact for
    a plane -- and the world is not one. The probe intersects the cursor's ray
    with z = 0, so on a raised plateau the point it reports is the place that
    ray crosses sea level, several tiles beyond the rock the cursor is actually
    over. Asking for 754,230 in the delving put the cursor on 755,236, the menu
    opened on empty sand, and the click after it walked somewhere nobody chose.
    Everything about that looked like the menu misbehaving.
    #
    So the aim is corrected against the engine's own answer: point, ask what
    tile that is, and shift by the difference until it agrees. Two rounds is
    usually enough; the correction is applied through the same linear map,
    which is locally right even where it is globally wrong.
    """
    c = load()
    vx, vy = aim(tx, ty)
    (a, b), (cc, d) = c['ex'], c['ey']
    det = a * d - b * cc
    for _ in range(tries):
        sx, sy = screen(int(max(0, min(c['vw'] - 1, vx))),
                        int(max(0, min(c['vh'] - 1, vy))))
        front()
        cliclick('m:%d,%d' % (sx, sy))
        got = asked()
        at = got.get('tile')
        if not at:
            break
        if at == [tx, ty]:
            return vx, vy
        dx = (tx - at[0]) * 200.0
        dy = (ty - at[1]) * 200.0
        vx += (d * dx - cc * dy) / det
        vy += (a * dy - b * dx) / det
    return vx, vy


# THE MINIMAP'S PLACE ON THE GLASS, derived rather than measured.
#
# It is a fixed size in interface units at a fixed inset from the top right,
# and the viewport reports its own scale -- so where it is can be worked out
# instead of photographed, and stays right if the window is resized.
MAP_TILES = 113          # Reach * 2 + 1, from IntervalHud.h
MAP_UNITS = 210.0        # MapSide, from IntervalHud.cpp
MAP_EDGE = 17.0          # MapEdge -- the dark band the compass letters sit on
MAP_INSET = 12.0         # the canvas margin
# The plate is a band of two round a face padded by five across and three and
# three-quarters down -- see `Board` in IntervalHud.cpp. The map's own face
# therefore begins nineteen units in from the right and a little under
# eighteen down from the top.
MAP_PAD_X = 7.0
MAP_PAD_Y = 5.75


def map_face(c):
    """(left, top, pixels-per-tile) of the minimap image, in viewport pixels.

    The picture is inset inside its plate by MAP_EDGE on every side now -- the
    dark band the four compass letters stand on, which was added when they
    turned out to be unreadable over the terrain itself.
    """
    k = c['scale']
    side = MAP_UNITS * k
    right = c['vw'] - (MAP_INSET + MAP_PAD_X + MAP_EDGE) * k
    top = (MAP_INSET + MAP_PAD_Y + MAP_EDGE) * k
    return right - side, top, side / MAP_TILES


def map_pixel(c, dx, dy):
    """Where a tile OFFSET from the citizen falls on the minimap, in pixels.

    THE MAP TURNS WITH THE CAMERA. It is drawn forward-up -- screen-up is
    whichever way the citizen is looking -- so a tile due north of somebody
    facing west is drawn on the right-hand side of the picture. Aiming at it
    with north-up arithmetic, which is what this did before the map could
    turn, walks somewhere else entirely and looks like a click that missed.

    The transform is the one in `UIntervalMapWidget::Repaint`, read the other
    way: a world offset onto the picture. The yaw comes from the probe, which
    asks the camera manager, because that is the only thing that knows.
    """
    import math
    yaw = math.radians(float(c.get('yaw', 0.0)))
    cos, sin = math.cos(yaw), math.sin(yaw)
    across = -sin * dx + cos * dy
    down = -(cos * dx + sin * dy)
    left, top, per = map_face(c)
    half = MAP_TILES / 2.0
    return (left + (half + across) * per, top + (half + down) * per)


def far(tx, ty):
    """Walk a long way by clicking the map, which is what it is for.

    A click on the WORLD can only ask for a walk as far as the camera sees --
    about six tiles. A click on the map asks for as far as the map shows, which
    is fifty-six each way: one click instead of ten. A target beyond the map is
    clamped to its edge, so a journey of three hundred tiles is a handful of
    clicks in the right direction rather than fifty.
    """
    settle()
    at = here_now()
    if not at:
        raise SystemExit('cannot see where the citizen is standing')
    c = dict(load())
    # THE YAW, FROM THE PROBE. The calibration knows the glass; only the engine
    # knows which way the camera is facing, and the map is drawn facing that
    # way. Without this every long walk goes off at an angle.
    try:
        with open(MOUSE) as f:
            c['yaw'] = json.load(f).get('yaw', 0.0)
    except Exception:
        c['yaw'] = 0.0
    # INSIDE THE DISC, NOT INSIDE THE SQUARE. The picture is round now, so the
    # corners of its box are plate and not map; clamping to a square put the
    # far diagonal clicks on the border, where they are swallowed and the
    # citizen does not move -- which reads as a broken map rather than as an
    # aim two tiles wide. A radius keeps every click on ground at every angle.
    lim = MAP_TILES / 2.0 - 3.0
    dx = float(tx - at[0])
    dy = float(ty - at[1])
    span = math.hypot(dx, dy)
    if span > lim:
        dx, dy = dx * lim / span, dy * lim / span
    dx, dy = int(round(dx)), int(round(dy))
    vx, vy = map_pixel(c, dx, dy)
    sx, sy = screen(int(vx), int(vy))
    front()
    cliclick('m:%d,%d' % (sx, sy))
    time.sleep(0.3)
    cliclick('c:.')
    print('map click for %+d,%+d (toward %d,%d)' % (dx, dy, tx, ty))
    return dx, dy



def isle_face():
    """The island map's rectangle, in viewport pixels, as the WINDOW reports it.

    Not derived. Every attempt to work a widget's rectangle out from the chain
    of paddings that produced it -- two borders, a size box, a viewport scale --
    has been wrong within a day of writing it, because one of those numbers
    always moves. The world map logs its own geometry every time it paints, so
    this reads the last line it wrote.

    Slate measures in absolute desktop pixels; the viewport's own origin is the
    calibration's, so subtracting it puts the answer in the coordinates every
    other command here already speaks.
    """
    ax = ay = aw = ah = tw = th = None
    with open('/tmp/ue.log') as f:
        for line in f:
            if '[isle] face ' in line:
                bits = line.split('[isle] face ')[1].split()
                ax, ay, aw, ah = [float(v) for v in bits[:4]]
                tw, th = int(bits[5]), int(bits[6])
    if ax is None:
        raise SystemExit('the island map has not painted: open its tab first')
    c = load()
    ox = -c['ox'] / c['kx']          # the viewport's origin, in screen points
    oy = -c['oy'] / c['ky']
    k = c['kx']                      # viewport pixels per screen point
    return ax - ox * k, ay - oy * k, aw, ah, tw, th


def isle(tx, ty):
    """Walk somewhere by clicking it on the world map.

    THE MAP WITH NO ROTATION IN IT. The minimap turns with the camera, so
    aiming at it means reading back through a yaw that is still interpolating
    while the citizen walks -- a small error over five tiles and a large one
    over fifty, which is why a walk aimed due north kept setting off
    north-east. The island is drawn north-up at a pixel a tile and does not
    move, so a click on it is simply the place.
    """
    left, top, wide, high, tw, th = isle_face()
    vx = left + (tx + 0.5) * wide / tw
    vy = top + (ty + 0.5) * high / th
    sx, sy = screen(int(vx), int(vy))
    front()
    cliclick('m:%d,%d' % (sx, sy))
    time.sleep(0.3)
    cliclick('c:.')
    print('island click for %d,%d at viewport %d,%d' % (tx, ty, vx, vy))
    return tx, ty


def load():
    if not os.path.exists(CAL):
        raise SystemExit('no calibration: run `hand.py cal` first')
    with open(CAL) as f:
        return json.load(f)


def screen(vx, vy):
    """Viewport pixels -> screen points, and refuse to click off the glass."""
    c = load()
    if not (0 <= vx < c['vw'] and 0 <= vy < c['vh']):
        raise SystemExit('%d,%d is outside the viewport (%.0fx%.0f)'
                         % (vx, vy, c['vw'], c['vh']))
    return int(round((vx - c['ox']) / c['kx'])), int(round((vy - c['oy']) / c['ky']))


def note(what):
    """Tell the window what was pressed, so the stream shows it.

    The HUD draws its own pointer and its own "left click" flash because Pixel
    Streaming sends the viewport and the operating system's cursor is not in
    the viewport. The flash is driven off the button state, so it needs nothing
    from here -- but the LINE is written into the feed, so that a recording of
    a session says what was done and not only what happened.
    """
    try:
        with open(CMD, 'a') as f:
            f.write(what + '\n')
    except OSError:
        pass


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    verb = sys.argv[1]
    if verb == 'cal':
        return calibrate()
    if verb == 'where':
        front()
        cliclick('p')
        got = asked()
        return print('viewport %.0f,%.0f of %.0fx%.0f'
                     % (got['x'], got['y'], got['vw'], got['vh']))
    if verb == 'type':
        front()
        # `t:` types a literal string. A colon in the text would end the
        # argument, so it goes through as a keystroke instead.
        cliclick('t:' + ' '.join(sys.argv[2:]))
        return print('typed')
    if verb == 'isle':
        return isle(int(sys.argv[2]), int(sys.argv[3]))
    if verb == 'key':
        front()
        cliclick('kp:' + sys.argv[2])
        return print('pressed %s' % sys.argv[2])
    if verb == 'ground':
        return ground()
    if verb == 'trek':
        return trek(int(sys.argv[2]), int(sys.argv[3]))
    if verb == 'road':
        return road(int(sys.argv[2]), int(sys.argv[3]))
    if verb == 'far':
        return far(int(sys.argv[2]), int(sys.argv[3]))
    if verb == 'pick':
        return pick(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
    if verb == 'here':
        return print(here_now())
    if verb in ('go', 'at'):
        tx, ty = int(sys.argv[2]), int(sys.argv[3])
        # STILL FIRST, THEN AIM, THEN CLICK WITH NOTHING IN BETWEEN.
        #
        # The camera follows the citizen, so a screen point that was over the
        # right tile a second ago is over a different one now. `aim_true`
        # leaves the cursor exactly where it verified, and the click is made
        # from there without moving again -- moving again means re-deriving the
        # point from a camera that has meanwhile slid, which is how a click
        # meant for a seam of iron became a walk into the desert.
        settle()
        vx, vy = aim_true(tx, ty)
        c = load()
        if not (0 <= vx < c['vw'] and 0 <= vy < c['vh']):
            raise SystemExit(
                'tile %d,%d is off the glass at viewport %.0f,%.0f -- a citizen '
                'can only click what they can see, so walk part of the way first'
                % (tx, ty, vx, vy))
        cliclick('c:.' if verb == 'go' else 'rc:.')
        print('%s tile %d,%d at viewport %.0f,%.0f'
              % ('clicked' if verb == 'go' else 'right-clicked', tx, ty, vx, vy))
        return
    if verb in ('move', 'click', 'right', 'double'):
        vx, vy = int(sys.argv[2]), int(sys.argv[3])
        sx, sy = screen(vx, vy)
        front()
        # MOVE FIRST, ALWAYS, AND THEN PAUSE. A click posted at a coordinate
        # the pointer has not yet reached is hit-tested against whatever was
        # under the OLD position -- Slate reads the cursor it last saw, not the
        # one in the event. The pause is for the editor's frame rate, which
        # drops to a third of a hertz while the world streams in.
        cliclick('m:%d,%d' % (sx, sy))
        time.sleep(0.4)
        if verb == 'click':
            cliclick('c:.')
        elif verb == 'right':
            cliclick('rc:.')
        elif verb == 'double':
            cliclick('dc:.')
        print('%s at viewport %d,%d (screen %d,%d)' % (verb, vx, vy, sx, sy))
        return
    raise SystemExit('unknown: %s\n%s' % (verb, __doc__))


main()
