#!/usr/bin/env python3
"""Photograph an asset's own thumbnail, for art that nobody is wearing yet.

A helm or a breastplate cannot be judged in the world until the world happens
to give one to somebody, and it will not. This asks the editor for the asset's
own render instead.

  asset_shot.py out.png /Game/Path/Asset [...more assets...]
"""
import base64, json, os, re, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import rpc, sheet

APP = 'EditorToolset.EditorAppToolset'


def shot(path, out):
    r = rpc.raw(APP, 'CaptureAssetImage', {'assetPath': path, 'imageSize': 512})
    m = re.search(r'"data\\?"\s*:\s*\\?"([A-Za-z0-9+/=]+)', r)
    if not m:
        print(path, 'NO IMAGE', r[:200])
        return None
    open(out, 'wb').write(base64.b64decode(m.group(1)))
    return out


if __name__ == '__main__':
    out, assets = sys.argv[1], sys.argv[2:]
    made = []
    for i, a in enumerate(assets):
        p = '%s.%d.png' % (out, i)
        if shot(a, p):
            made.append(p)
            print(a.split('/')[-1])
    if made:
        tiles = [sheet.read(p) for p in made]
        cw = max(t[0] for t in tiles); ch = max(t[1] for t in tiles)
        cols = min(4, len(tiles)); rows = (len(tiles) + cols - 1) // cols
        W, H = cw * cols, ch * rows
        board = bytearray(b'\x18' * (W * H * 3))
        for i, (w, h, rgb) in enumerate(tiles):
            ox, oy = (i % cols) * cw, (i // cols) * ch
            for y in range(h):
                d = ((oy + y) * W + ox) * 3
                board[d:d + w * 3] = rgb[y * w * 3:(y + 1) * w * 3]
        sheet.write(out, W, H, board)
        print(out, W, H)
