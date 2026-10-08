#!/usr/bin/env python3
"""Every sprite on one sheet, so they can be judged against each other.

A pack is looked at as a GRID, not one icon at a time, and faults that are
invisible alone are obvious in a row: a thing lying on its side, a thing
facing away, one blade pointing north-east while the four beside it point
north-west. Nothing in this project had ever put them side by side.

  sheet.py out.png [cols] [name...]   all of Art/Icons, or just these
"""
import os, struct, sys, zlib

SP = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SP)
ICONS = os.path.join(ROOT, 'Art', 'Icons')
CELL = 128
PAD = 6
BG = (28, 24, 18)


def read(path):
    d = open(path, 'rb').read()
    i, idat = 8, b''
    w = h = ct = 0
    while i < len(d):
        ln = struct.unpack('>I', d[i:i + 4])[0]
        typ = d[i + 4:i + 8]
        if typ == b'IHDR':
            w, h, _bd, ct = struct.unpack('>IIBB', d[i + 8:i + 18])
        elif typ == b'IDAT':
            idat += d[i + 8:i + 8 + ln]
        i += 12 + ln
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    raw = zlib.decompress(idat)
    stride = w * ch
    prev = bytearray(stride)
    pos = 0
    rows = []
    for _y in range(h):
        f = raw[pos]; pos += 1
        line = bytearray(raw[pos:pos + stride]); pos += stride
        for x in range(stride):
            a = line[x - ch] if x >= ch else 0
            b = prev[x]
            c = prev[x - ch] if x >= ch else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        prev = line
        rows.append(bytes(line))
    return w, h, ch, rows


def write(path, w, h, px):
    def chunk(tag, body):
        c = tag + body
        return struct.pack('>I', len(body)) + c + struct.pack('>I', zlib.crc32(c))
    raw = b''.join(b'\x00' + bytes(px[y]) for y in range(h))
    open(path, 'wb').write(
        b'\x89PNG\r\n\x1a\n'
        + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
        + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def main(argv):
    out = argv[0] if argv else '/tmp/sheet.png'
    cols = int(argv[1]) if len(argv) > 1 else 12
    want = argv[2:]
    names = sorted(f[:-4] for f in os.listdir(ICONS) if f.endswith('.png'))
    if want:
        names = [n for n in names if n in want]
    rows_n = (len(names) + cols - 1) // cols
    W = cols * (CELL + PAD) + PAD
    H = rows_n * (CELL + PAD) + PAD
    sheet = [bytearray(BG * W) for _ in range(H)]
    for i, n in enumerate(names):
        try:
            w, h, ch, px = read(os.path.join(ICONS, n + '.png'))
        except Exception:
            continue
        cx = PAD + (i % cols) * (CELL + PAD)
        cy = PAD + (i // cols) * (CELL + PAD)
        for y in range(min(h, CELL)):
            src = px[y]
            dst = sheet[cy + y]
            for x in range(min(w, CELL)):
                s = src[x * ch:x * ch + ch]
                a = s[3] if ch == 4 else 255
                if not a:
                    continue
                o = (cx + x) * 3
                for k in range(3):
                    dst[o + k] = (s[k] * a + dst[o + k] * (255 - a)) // 255
    write(out, W, H, sheet)
    print('%d sprites, %d by %d -> %s' % (len(names), W, H, out))
    return 0


sys.exit(main(sys.argv[1:]))
