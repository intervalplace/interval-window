#!/usr/bin/env python3
"""Turn the three render passes into one inventory sprite.

WHY THE ARITHMETIC IS HERE AND NOT IN THE ENGINE. `icons.py` photographs each
item three times -- albedo, world normal, device depth -- and keeps no lit
frame at all, because a lit frame carries the hour it was taken at. The light
an icon is read by belongs to the interface, not to the world, so it is applied
here: one key light over the shoulder, a dim fill from the opposite side, and
a little rim so a dark item still has an edge against a dark slot.

The matte comes from the depth pass. Unreal draws depth REVERSED, so the value
is exactly zero everywhere nothing was drawn; there is no keying colour to pick
and no coloured fringe to clean up afterwards.

Reduced at the end rather than rendered small: the sprite is taken at 512 and
averaged down to 128, and that average IS the anti-aliasing, done in
premultiplied space so a dark edge does not pick up a halo of the background
it never had.

  matte.py <name> [...]        reads Art/Icons/raw, writes Art/Icons
  matte.py --stats <file.png>  what is actually in a pass, when one looks blank
"""
import os, struct, sys, zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'Art', 'Icons', 'raw')
OUT = os.path.join(ROOT, 'Art', 'Icons')

# The things whose art is honestly neutral, so the grey guard below must not
# refuse them. See the long note beside it. Keep this list short and give each
# entry a reason; a name in here is a name the guard can no longer protect.
TRULY_NEUTRAL = {
    'sheep',        # its mesh's own materials are named `Black` and `White`
}
SIDE = 128


def read_png(path):
    """(w, h, [r,g,b,a] per pixel as bytes). Only what Unreal exports."""
    raw = open(path, 'rb').read()
    assert raw[:8] == b'\x89PNG\r\n\x1a\n', '%s is not a PNG' % path
    i, idat, w, h, depth, kind = 8, [], 0, 0, 8, 6
    while i + 8 <= len(raw):
        n = struct.unpack('>I', raw[i:i + 4])[0]
        tag = raw[i + 4:i + 8]
        body = raw[i + 8:i + 8 + n]
        if tag == b'IHDR':
            w, h, depth, kind = struct.unpack('>IIBB', body[:10])
        elif tag == b'IDAT':
            idat.append(body)
        elif tag == b'IEND':
            break
        i += 12 + n
    lanes = {0: 1, 2: 3, 4: 2, 6: 4}[kind]
    step = lanes * (depth // 8)
    data = zlib.decompress(b''.join(idat))
    out = bytearray(w * h * lanes * (depth // 8))
    stride = w * step
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = data[p]; p += 1
        line = bytearray(data[p:p + stride]); p += stride
        if f == 1:
            for x in range(step, stride): line[x] = (line[x] + line[x - step]) & 255
        elif f == 2:
            for x in range(stride): line[x] = (line[x] + prev[x]) & 255
        elif f == 3:
            for x in range(stride):
                a = line[x - step] if x >= step else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x - step] if x >= step else 0
                c = prev[x - step] if x >= step else 0
                b = prev[x]
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, lanes, depth, bytes(out)


def write_png(path, w, h, rgba):
    rows = b''.join(b'\x00' + rgba[y * w * 4:(y + 1) * w * 4] for y in range(h))
    def chunk(tag, body):
        return (struct.pack('>I', len(body)) + tag + body +
                struct.pack('>I', zlib.crc32(tag + body) & 0xffffffff))
    open(path, 'wb').write(
        b'\x89PNG\r\n\x1a\n' +
        chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) +
        chunk(b'IDAT', zlib.compress(rows, 9)) + chunk(b'IEND', b''))


def stats(path):
    w, h, lanes, depth, px = read_png(path)
    per = depth // 8
    print('%s  %dx%d  %d lanes  %d-bit' % (os.path.basename(path), w, h, lanes, depth))
    for c in range(lanes):
        vals = px[c * per::lanes * per]
        print('   lane %d: min %3d  max %3d  mean %6.2f  nonzero %d/%d'
              % (c, min(vals), max(vals), sum(vals) / float(len(vals)),
                 sum(1 for v in vals if v), len(vals)))


# THE ALBEDO PASS IS LINEAR, and it took a measurement to be sure.
#
# `RTF_RGBA8` is a plain eight-bit target, not `RTF_RGBA8_SRGB`, so the bytes
# in it are light and not encoded light -- a material painted 0.150 arrives as
# byte 38, which is exactly 0.150, and not as byte 107, which is what it would
# be if the buffer held sRGB. Decoding it on the way in therefore applies the
# curve BACKWARDS, and the whole sheet came out nearly black while every
# individual number looked reasonable. The bytes are used as they are; the one
# encode happens at the very end.
#
# (Viewed in any ordinary picture viewer the raw passes look far too dark for
# the same reason: the viewer assumes sRGB. That is the pass being correct,
# not the pass being wrong.)
def srgb(x):
    """Linear back to sRGB, once, at the very end."""
    if x <= 0.0031308:
        return 12.92 * x
    return 1.055 * (x ** (1.0 / 2.4)) - 0.055


# THE LIGHT AN ICON IS READ BY. Over the left shoulder and a little above,
# which is where every reader expects light to come from, with a cool fill
# opposite so the shadow side is legible rather than black.
KEY = (-0.40, 0.42, 0.82)
FILL = (0.45, -0.40, -0.10)

# THE TIER. See `tiers.py` for why the grade is carried by the colour of the
# metal. `icons.py` handles it properly, by overriding the mesh's metal slots
# before the render -- but a few meshes (the pickaxes, the helmets) are a
# single material with everything painted into one texture, and there is no
# slot to override. Those are tinted here instead, by brightness: on such a
# mesh the metal is the bright part and the haft is the dark part, which is
# true of every one of them and is checked by eye rather than assumed.
from tiers import tier_of

def temper(r, g, b, tint, cut, ref):
    """Give a bright pixel the tier's colour, keeping exactly its shading.

    The ratio, not the value: a pixel half as bright as its neighbour stays
    half as bright, so the form the render found is untouched and only the hue
    moves. `cut` is the brightness below which a pixel is taken to be haft
    rather than head.
    """
    v = (r + g + b) / 3.0
    if v < cut:
        return r, g, b
    # AGAINST THE ITEM'S OWN METAL, NOT AGAINST THE TINT.
    #
    # Dividing by the tint's own mean and then multiplying by the tint cancels
    # the tint's BRIGHTNESS and leaves only its hue -- so dull iron, bright
    # steel and blackened great-iron all came out the same medium silver,
    # which is precisely the thing these colours exist to tell apart. The
    # reference is what this mesh's metal was painted, so a pixel half as
    # bright as the rest of the head stays half as bright and the grade's own
    # value comes through.
    k = v / (ref or 1.0)
    return tint[0] * k, tint[1] * k, tint[2] * k


_SLOTTED = None


def _by_slot():
    """The items the renderer already coloured by overriding a material slot."""
    global _SLOTTED
    if _SLOTTED is None:
        try:
            import json
            _SLOTTED = set(json.load(open(os.path.join(RAW, 'by_slot.json'))))
        except Exception:
            _SLOTTED = set()
    return _SLOTTED


def compose(name):
    src = os.path.join(RAW, name)
    aw, ah, al, ad, alb = read_png(src + '.a.png')
    nw, nh, nl, nd, nrm = read_png(src + '.n.png')
    dw, dh, dl, dd, dep = read_png(src + '.d.png')
    assert aw == nw == dw and ah == nh == dh, '%s: passes disagree on size' % name
    step = aw // SIDE
    assert step * SIDE == aw, '%s: %d does not reduce to %d' % (name, aw, SIDE)

    kx, ky, kz = KEY
    fx, fy, fz = FILL
    # ONLY WHEN THE RENDERER COULD NOT DO IT PROPERLY. `icons.py` writes the
    # names it handled by slot override; anything in that list is already the
    # right colour and must not be tinted twice.
    tint = None if name in _by_slot() else tier_of(name)
    cut = 0.0
    ref = 1.0
    if tint:
        # THE CUT IS MEASURED, NOT PICKED. Two thirds of the way up this item's
        # own brightness range: on a one-material tool the head is the bright
        # third and the haft is the rest, and a fixed threshold would tint a
        # pale wooden bow and miss a dark iron head.
        lit = sorted(((alb[i] + alb[i + 1] + alb[i + 2]) / 765.0)
                     for i in range(0, len(alb), 4)
                     if dep[i] or dep[i + 1] or dep[i + 2])
        cut = lit[int(len(lit) * 0.55)] if lit else 0.0
        metal = [v for v in lit if v >= cut]
        ref = sum(metal) / len(metal) if metal else 1.0

    out = bytearray(SIDE * SIDE * 4)
    for oy in range(SIDE):
        for ox in range(SIDE):
            # PREMULTIPLIED, so the reduction does not drag the emptiness
            # around the silhouette into the colour of its edge.
            sr = sg = sb = sa = 0.0
            snx = sny = snz = 0.0
            for dy in range(step):
                row = ((oy * step + dy) * aw + ox * step) * 4
                for dx in range(step):
                    i = row + dx * 4
                    # REVERSED DEPTH: zero is nothing at all. Any pixel the
                    # renderer touched has a value here.
                    if not (dep[i] or dep[i + 1] or dep[i + 2]):
                        continue
                    sa += 1.0
                    sr += alb[i] / 255.0
                    sg += alb[i + 1] / 255.0
                    sb += alb[i + 2] / 255.0
                    snx += nrm[i] / 127.5 - 1.0
                    sny += nrm[i + 1] / 127.5 - 1.0
                    snz += nrm[i + 2] / 127.5 - 1.0
            o = (oy * SIDE + ox) * 4
            if sa <= 0.0:
                continue
            a = sa / (step * step)
            r, g, b = sr / sa, sg / sa, sb / sa
            if tint:
                r, g, b = temper(r, g, b, tint, cut, ref)
            ln = (snx * snx + sny * sny + snz * snz) ** 0.5
            if ln > 1e-4:
                snx, sny, snz = snx / ln, sny / ln, snz / ln
            key = max(snx * kx + sny * ky + snz * kz, 0.0)
            fill = max(snx * fx + sny * fy + snz * fz, 0.0)
            # AMBIENT HIGH, KEY HIGHER. An icon is not a photograph: the
            # side facing away from the light still has to be read at
            # thirty-two pixels, so the fill-in is generous and the key is
            # strong enough to keep the form. These numbers were set by
            # looking at the sheet, not derived.
            lit = 0.62 + 1.45 * key + 0.38 * fill
            out[o] = min(255, int(srgb(min(r * lit, 1.0)) * 255 + 0.5))
            out[o + 1] = min(255, int(srgb(min(g * lit, 1.0)) * 255 + 0.5))
            out[o + 2] = min(255, int(srgb(min(b * lit, 1.0)) * 255 + 0.5))
            out[o + 3] = min(255, int(a * 255 + 0.5))
    # WRITTEN BESIDE THE REAL ONE, NOT OVER IT. The guard at the foot of this
    # file measures the composed sprite and stops the run when it is neutral,
    # which is the right thing to do and was happening too late: the file had
    # already been written, so a failed render replaced a hundred and thirty
    # good sprites with a hundred and thirty grey ones and the guard's only
    # effect was to say so. The sprite goes into place in `keep` below, once
    # it has been looked at.
    write_png(os.path.join(OUT, name + '.pending.png'), SIDE, SIDE, bytes(out))
    return sum(1 for i in range(3, len(out), 4) if out[i])


def _spread(path):
    """How far apart the colour channels are, averaged over what is drawn.

    Zero means every opaque pixel has red, green and blue equal, which is the
    default material's signature and is what a not-yet-compiled shader draws.
    """
    import struct
    import zlib
    d = open(path, 'rb').read()
    i, idat, w, h = 8, b'', 0, 0
    while i < len(d):
        ln = struct.unpack('>I', d[i:i + 4])[0]
        typ = d[i + 4:i + 8]
        if typ == b'IHDR':
            w, h = struct.unpack('>II', d[i + 8:i + 16])
        elif typ == b'IDAT':
            idat += d[i + 8:i + 8 + ln]
        i += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * 4 + 1
    seen, total = 0, 0
    for y in range(h):
        row = raw[y * stride + 1:(y + 1) * stride]
        for x in range(w):
            r, g, b, a = row[x * 4:x * 4 + 4]
            if a > 200:
                seen += 1
                total += max(r, g, b) - min(r, g, b)
    return (total // seen) if seen else None


if __name__ == '__main__':
    if sys.argv[1:2] == ['--stats']:
        for f in sys.argv[2:]:
            stats(f)
        raise SystemExit
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    names = sys.argv[1:] or sorted(
        f[:-6] for f in os.listdir(RAW) if f.endswith('.a.png'))
    # AND A GREY ICON IS A FAILED ICON, SAID OUT LOUD.
    #
    # An item whose material's shader is not compiled yet renders with the
    # DEFAULT material, which is neutral grey. Nothing errors, every file is
    # written, and what comes out is a sprite that looks deliberate -- see the
    # note at the top of icons.sh, which was written the FIRST time this cost a
    # day. It cost part of a second one: a material instance created earlier in
    # the same session needs longer than the three minutes that script waits,
    # and both chains came back r == g == b at 80.
    #
    # So the pixels are measured rather than trusted. Grey is not a colour any
    # item in this world is: the greyest real thing here is steel, and steel
    # has a blue in it that survives averaging.
    def keep(n):
        was = os.path.join(OUT, n + '.pending.png')
        os.replace(was, os.path.join(OUT, n + '.png'))

    def drop(n):
        try:
            os.remove(os.path.join(OUT, n + '.pending.png'))
        except OSError:
            pass

    flat = []
    for n in names:
        px = compose(n)
        print('%-22s %5d pixels' % (n, px))
        try:
            hue = _spread(os.path.join(OUT, n + '.pending.png'))
        except Exception:
            keep(n)
            continue
        # EXACTLY neutral, and not merely grey. The greyest things this world
        # has are real: rubble comes back at 1 and coal at 2, because no entry
        # in the forge palette is exactly neutral and the light is not either.
        # The default material IS exactly neutral, so zero is the signature
        # and anything above it is an item that happens to be grey.
        #
        # EXCEPT WHERE THE ART REALLY IS NEUTRAL, which the forge palette
        # never is but a fetched pack can be. The sheep's mesh ships two
        # materials and they are named `Black` and `White`; a white fleece has
        # red, green and blue equal because that is what white means. It sat
        # here being re-photographed eight times a round, twice, waiting for a
        # shader that had been ready the whole time.
        #
        # Named rather than loosened. Raising the threshold would blind the
        # guard to the failure it exists to catch, and that failure has cost
        # this project more than one day. An exception with a reason attached
        # costs nothing and stays readable.
        if px and hue is not None and hue < 1 and n not in TRULY_NEUTRAL:
            flat.append((n, hue))
            drop(n)                    # the sprite already there was better
        else:
            keep(n)
    if flat:
        print()
        print('GREY, WHICH MEANS THE SHADER WAS NOT READY AND NOT THAT THE '
              'ITEM IS GREY:')
        for n, hue in flat:
            print('  %-22s red, green and blue identical everywhere' % n)
        print('  render these again into an editor that has been up longer:')
        print('  the warm in icons.sh is a guess and a material instance made')
        print('  in the same session has needed more than four minutes of it.')
        # AND SAID IN THE EXIT CODE, not only on the screen. This printed its
        # complaint and returned zero, so `icons.sh` -- which is `set -e` and
        # pipes this through `tail -2` -- finished happily with a pack full of
        # grey. A guard nobody's script can act on is a comment.
        raise SystemExit(2)

