#!/usr/bin/env python3
"""Cut a rectangle out of a screenshot and blow it up, with no dependencies.

Looking closely at one corner of a 1400-pixel frame is most of how anything in
this window gets checked, and the alternative -- walking the citizen nearer and
taking another photograph -- moves the world and costs a minute each time.

  zoom.py in.png out.png x0 y0 x1 y1 [factor]
"""
import os, struct, sys, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matte


def main(a):
    src, dst = a[0], a[1]
    x0, y0, x1, y1 = (int(v) for v in a[2:6])
    k = int(a[6]) if len(a) > 6 else 2
    w, h, lanes, depth, px = matte.read_png(src)
    step = lanes * (depth // 8)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w, x1), min(h, y1)
    cw, ch = (x1 - x0) * k, (y1 - y0) * k
    rows = []
    for y in range(ch):
        sy = y0 + y // k
        row = bytearray()
        for x in range(cw):
            sx = x0 + x // k
            i = (sy * w + sx) * step
            row += bytes(px[i:i + 3])
        rows.append(row)
    raw = b''.join(b'\x00' + bytes(r) for r in rows)

    def chunk(tag, body):
        c = tag + body
        return struct.pack('>I', len(body)) + c + struct.pack('>I', zlib.crc32(c))
    open(dst, 'wb').write(
        b'\x89PNG\r\n\x1a\n'
        + chunk(b'IHDR', struct.pack('>IIBBBBB', cw, ch, 8, 2, 0, 0, 0))
        + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))
    print('%s -> %s  %dx%d' % (os.path.basename(src), os.path.basename(dst), cw, ch))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
