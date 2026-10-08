#!/usr/bin/env python3
"""Synthesise the ambience beds.

There is no field recording to hand and the themes are music, not weather.
Wind, surf, a river and rain are all shaped noise, so shaped noise is what
these are: white noise through one-pole filters, breathed by slow modulation.
Nothing tries to fake a blackbird -- a bad blackbird is worse than none.

Every bed LOOPS SEAMLESSLY, which needs two things. The modulation is built
from sinusoids with a whole number of cycles per loop, so it meets itself at
the join; and the noise itself is circularly cross-faded, the tail mixed back
over the head, so the filter's memory joins up too.
"""
import array, math, os, random, struct, sys, wave

RATE = 22050
SECS = 24.0
N = int(RATE * SECS)
XF = int(RATE * 1.5)          # the circular cross-fade

def noise(seed):
    r = random.Random(seed)
    return [r.uniform(-1.0, 1.0) for _ in range(N + XF)]

def lowpass(src, hz, times=1):
    a = 1.0 - math.exp(-2.0 * math.pi * hz / RATE)
    out = src
    for _ in range(times):
        y, res = 0.0, [0.0] * len(out)
        for i, x in enumerate(out):
            y += a * (x - y)
            res[i] = y
        out = res
    return out

def highpass(src, hz):
    a = math.exp(-2.0 * math.pi * hz / RATE)
    y, xp, out = 0.0, 0.0, [0.0] * len(src)
    for i, x in enumerate(src):
        y = a * (y + x - xp)
        xp = x
        out[i] = y
    return out

def lfo(cycles, depth, phase=0.0):
    """A whole number of cycles per loop, so the join is silent."""
    w = 2.0 * math.pi * cycles / N
    return [1.0 - depth + depth * 0.5 * (1.0 + math.sin(w * i + phase)) for i in range(N)]

def wrap(sig):
    """Mix the tail back over the head so the loop has no seam."""
    out = sig[:N]
    for i in range(XF):
        k = i / XF
        out[i] = out[i] * k + sig[N + i] * (1.0 - k)
    return out

def mix(*layers):
    out = [0.0] * N
    for sig, gain in layers:
        for i in range(N):
            out[i] += sig[i] * gain
    return out

def write(name, sig, peak=0.62):
    m = max(1e-9, max(abs(v) for v in sig))
    k = peak / m
    data = array.array('h', (int(max(-32767, min(32767, v * k * 32767))) for v in sig))
    with wave.open(name, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(data.tobytes())
    print(' ', os.path.basename(name), f'{len(sig)/RATE:.0f}s')

def modulate(sig, env):
    return [sig[i] * env[i] for i in range(N)]

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

def bed(name, build):
    write(os.path.join(OUT, name + '.wav'), build())

# Open country: a broad, soft wind with long gusts and nothing else in it.
bed('amb-open', lambda: modulate(
    wrap(lowpass(noise(1), 420.0, 2)),
    [a * b for a, b in zip(lfo(3, 0.55), lfo(7, 0.25, 1.1))]))

# High ground: harder, with an edge that whistles over the top.
bed('amb-high', lambda: mix(
    (modulate(wrap(lowpass(noise(2), 700.0, 2)), lfo(5, 0.6)), 1.0),
    (modulate(wrap(highpass(lowpass(noise(3), 2600.0), 1100.0)), lfo(11, 0.8, 0.4)), 0.35)))

# Woodland: the same wind further off, and leaves, which are brighter and
# rattle rather than breathe.
bed('amb-wood', lambda: mix(
    (modulate(wrap(lowpass(noise(4), 300.0, 2)), lfo(3, 0.5)), 0.7),
    (modulate(wrap(highpass(lowpass(noise(5), 5200.0), 1600.0)),
              [a * b for a, b in zip(lfo(9, 0.7), lfo(23, 0.5, 2.0))]), 0.55)))

# Fen: low air over water, and reeds, which are drier and thinner than leaves.
bed('amb-fen', lambda: mix(
    (modulate(wrap(lowpass(noise(6), 220.0, 2)), lfo(2, 0.4)), 1.0),
    (modulate(wrap(highpass(lowpass(noise(7), 3800.0), 2200.0)), lfo(13, 0.85, 0.9)), 0.22),
    (modulate(wrap(lowpass(highpass(noise(8), 400.0), 1400.0)), lfo(17, 0.6, 2.4)), 0.18)))

# Sea: surge. The long swell is what makes it the sea and not a river.
bed('amb-sea', lambda: mix(
    (modulate(wrap(lowpass(noise(9), 900.0, 2)),
              [a * b for a, b in zip(lfo(4, 0.85), lfo(9, 0.3, 0.7))]), 1.0),
    (modulate(wrap(highpass(lowpass(noise(10), 6000.0), 2400.0)), lfo(4, 0.9, 0.35)), 0.3)))

# River: steadier and brighter -- running water does not breathe.
bed('amb-river', lambda: mix(
    (wrap(lowpass(noise(11), 1500.0, 2)), 0.8),
    (modulate(wrap(highpass(lowpass(noise(12), 7000.0), 1800.0)), lfo(19, 0.35)), 0.55)))

# Underground: pressure, and the room the sound is in.
bed('amb-deep', lambda: mix(
    (wrap(lowpass(noise(13), 90.0, 3)), 1.0),
    (modulate(wrap(lowpass(highpass(noise(14), 700.0), 2000.0)), lfo(29, 0.95, 1.7)), 0.09)))

# A settled place: no voices, which would be a lie about who is there, but the
# low hum that a lot of small sounds at a distance add up to.
bed('amb-town', lambda: mix(
    (modulate(wrap(lowpass(noise(15), 260.0, 2)), lfo(3, 0.35)), 1.0),
    (modulate(wrap(lowpass(highpass(noise(16), 300.0), 1200.0)),
              [a * b for a, b in zip(lfo(7, 0.6), lfo(31, 0.7, 1.3))]), 0.28)))
