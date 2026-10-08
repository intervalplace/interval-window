#!/usr/bin/env python3
"""The GAME out of a picture of the whole editor, found rather than measured.

`see.sh` crops the viewport using the rectangle `hand.py cal` measured, which
is the right way round when a click has to land where the picture says. It has
one failure and it is silent: the editor window can change size between the
calibration and the photograph -- a restart, a display change, somebody
dragging it -- and then the crop is of the wrong rectangle. What comes out is
not obviously wrong, it is BLANK, and a blank picture reads as a window that is
not drawing rather than as a crop that missed.

This asks the picture instead. The editor's panels are a near-uniform dark
grey; the game is not uniform anywhere. So the viewport is the largest block of
rows and columns that are not flat, and no calibration enters into it.

  frame.py shot.png out.png [longest-side]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matte

CHROME = 46          # anything this dark and this grey is a panel
SPREAD = 10          # how far the three channels may differ and still be grey


def flat(px, o):
    r, g, b = px[o], px[o + 1], px[o + 2]
    return (max(r, g, b) < CHROME
            and max(r, g, b) - min(r, g, b) < SPREAD)


def main(a):
    src, dst = a[0], a[1]
    long_side = int(a[2]) if len(a) > 2 else 1400
    w, h, lanes, depth, px = matte.read_png(src)
    step = lanes * (depth // 8)

    # Sampled rather than counted in full: a five-megapixel screenshot read
    # pixel by pixel in Python is about a minute, and every tenth pixel gives
    # the same answer in under a second.
    def live_row(y):
        n = 0
        for x in range(0, w, 16):
            if not flat(px, (y * w + x) * step):
                n += 1
        return n

    def live_col(x):
        n = 0
        for y in range(0, h, 16):
            if not flat(px, (y * w + x) * step):
                n += 1
        return n

    # LOW THRESHOLDS, because a night scene is mostly dark and a strict test
    # throws away the top and bottom of it -- which came back as a letterbox
    # slice of a town rather than a picture of one.
    rows = [y for y in range(0, h, 4) if live_row(y) > (w // 16) * 0.12]
    cols = [x for x in range(0, w, 4) if live_col(x) > (h // 16) * 0.12]
    if not rows or not cols:
        print('no game in this picture: every row is editor chrome')
        return 1
    # THE LARGEST RUN, not the whole span. The Outliner has coloured text in
    # it and the toolbar has icons, so both answer "not flat" here and there;
    # taking min and max would stretch the crop across the entire window.
    def longest(vals, step_):
        best = (vals[0], vals[0]); run = (vals[0], vals[0])
        for v in vals[1:]:
            # A GENEROUS JOIN. A band of near-black sky inside the viewport is
            # not a panel, and splitting the run there is how a picture of a
            # town at night came back as a letterbox strip of its middle.
            if v - run[1] <= step_ * 24:
                run = (run[0], v)
            else:
                if run[1] - run[0] > best[1] - best[0]:
                    best = run
                run = (v, v)
        return run if run[1] - run[0] > best[1] - best[0] else best

    y0, y1 = longest(rows, 4)
    x0, x1 = longest(cols, 4)
    print('the game is at %d,%d to %d,%d in a %dx%d picture'
          % (x0, y0, x1, y1, w, h))
    # THE PATHS GO THROUGH A SHELL, so a space in one of them splits the
    # command in two and zoom.py is handed a fragment. This project lives in
    # "Unreal Projects"; the first version of this line failed on the space
    # and the only symptom was a missing output file.
    import subprocess
    zoom = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zoom.py')
    r = subprocess.run(['python3', zoom, src, dst, str(x0), str(y0),
                        str(x1), str(y1), '1'], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(dst):
        print('the crop failed: %s' % (r.stderr.strip()[-200:] or 'no output'))
        return 1
    # And down to something that can be looked at.
    w2, h2, l2, d2, p2 = matte.read_png(dst)
    k = max(1, max(w2, h2) // long_side)
    if k > 1:
        ow, oh = w2 // k, h2 // k
        out = bytearray(ow * oh * 4)
        s2 = l2 * (d2 // 8)
        for y in range(oh):
            for x in range(ow):
                o = ((y * k) * w2 + (x * k)) * s2
                q = (y * ow + x) * 4
                out[q], out[q + 1], out[q + 2], out[q + 3] = p2[o], p2[o + 1], p2[o + 2], 255
        matte.write_png(dst, ow, oh, bytes(out))
        print('  -> %dx%d' % (ow, oh))
    return 0


sys.exit(main(sys.argv[1:]))
