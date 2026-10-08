#!/usr/bin/env python3
"""The GAME, during a play session, at the size it is actually drawn.

WHY THIS EXISTS. There was no way to photograph the running game properly.

  `cap.py` asks the editor to capture its viewport, which is the right thing
  in Simulate and the wrong thing in Play: the level viewport behind the play
  window is what gets grabbed, so the picture is an empty grey grid.

  `editshot.py` grabs the whole editor window and caps it at about 1280 px
  across. The game is then perhaps half of that, with the outliner and the
  toolbars taking the rest, and a citizen's hands are a dozen pixels. Every
  judgement about how the world LOOKS, made while actually playing it, has
  been made from that.

So this takes the screen directly, and only the part of it the game is drawn
on. `hand.py cal` already measures that rectangle -- it has to, in order to
click on things -- so the numbers are read rather than guessed, and a window
that has been moved only needs `cal` run again.

`screencapture -R` takes SCREEN POINTS and writes NATIVE PIXELS, so on this
display the result is twice the rectangle: the full 4075x2260 the game is
rendering, not a thumbnail of it.

  gameshot.py out.png              the whole viewport
  gameshot.py out.png 1400         ...scaled down to 1400 wide afterwards
"""
import json, os, subprocess, sys

S = ('/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-'
     'interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/')
CAL = S + 'hand.cal.json'


def rect():
    """The viewport in screen points, from the hand's own calibration."""
    with open(CAL) as f:
        c = json.load(f)
    # viewportPixel = k * screenPoint + o, so screenPoint = (pixel - o) / k
    x0 = (0.0 - c['ox']) / c['kx']
    y0 = (0.0 - c['oy']) / c['ky']
    x1 = (c['vw'] - c['ox']) / c['kx']
    y1 = (c['vh'] - c['oy']) / c['ky']
    return int(round(x0)), int(round(y0)), int(round(x1 - x0)), int(round(y1 - y0))


if __name__ == '__main__':
    out = sys.argv[1]
    x, y, w, h = rect()
    # -x is "no camera noise", which matters when this runs every few seconds.
    subprocess.run(['screencapture', '-x', '-R%d,%d,%d,%d' % (x, y, w, h), out],
                   check=True)
    if len(sys.argv) > 2:
        subprocess.run(['sips', '-Z', sys.argv[2], out],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    got = subprocess.run(['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', out],
                         capture_output=True, text=True).stdout.split()
    print('%s  viewport at screen %d,%d %dx%d points -> %s x %s pixels'
          % (out, x, y, w, h, got[-3], got[-1]))
