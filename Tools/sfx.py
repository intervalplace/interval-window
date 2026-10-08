#!/usr/bin/env python3
"""Synthesise the sounds that belong to a PLACE rather than to a country.

`ambience.py` makes the beds: the air a citizen is standing in, always
running, cross-fading as they walk out of one country and into the next. This
makes the other kind -- rain you can hear stop when you step under a roof, a
fire you can hear from across a market place, and a footfall that knows what
it is standing on.

The same rule applies as over there: there is no field recording to hand, and
everything here is shaped noise rather than an imitation of a thing. A bad
recording of a blackbird is worse than no blackbird; a burst of filtered noise
with the right envelope is not pretending to be anything and reads as a
footstep because a footstep IS mostly a burst of filtered noise.

  sfx.py <out-dir>
"""
import array, math, os, random, sys, wave

RATE = 22050


def noise(seed, n):
    r = random.Random(seed)
    return [r.uniform(-1.0, 1.0) for _ in range(n)]


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


def ring(src, hz, q):
    """A two-pole resonator: what makes a knock sound like wood and not a thud.

    A footstep on a board excites the board, and the board has a note. This is
    that note -- one pole pair at `hz`, with `q` deciding how long it rings.
    """
    w = 2.0 * math.pi * hz / RATE
    r = math.exp(-math.pi * hz / (q * RATE))
    a1, a2 = 2.0 * r * math.cos(w), -r * r
    y1 = y2 = 0.0
    out = [0.0] * len(src)
    for i, x in enumerate(src):
        y = x + a1 * y1 + a2 * y2
        y2, y1 = y1, y
        out[i] = y
    return out


def env(n, attack, decay, curve=2.2):
    """Fast up, slow down, both in seconds. The shape IS the sound."""
    a = max(1, int(attack * RATE))
    out = [0.0] * n
    for i in range(n):
        if i < a:
            out[i] = i / a
        else:
            t = (i - a) / max(1e-6, decay * RATE)
            out[i] = math.exp(-curve * t) if t < 12.0 else 0.0
    return out


def mul(sig, e):
    return [sig[i] * e[i] for i in range(min(len(sig), len(e)))]


def mix(n, *layers):
    out = [0.0] * n
    for sig, gain in layers:
        for i in range(min(n, len(sig))):
            out[i] += sig[i] * gain
    return out


def write(path, sig, rms=0.09):
    """Levelled by RMS, not by peak -- and that is not a detail.

    Peak normalisation was the first version and it is measurably wrong here.
    A footstep on stone is a CLICK: almost all of its energy is in four
    milliseconds, so its peak is reached instantly and normalising to that peak
    leaves it at a third of the loudness of a footstep on grass, which has no
    attack at all and spreads its energy over seventy. The same fault made the
    fire ten times quieter than the rain. Loudness is roughly RMS; peak is only
    where the clipping is.

    So: scale to a target RMS, then soft-limit anything that would clip. The
    limiter is a tanh rather than a clamp because a clamp on a transient is
    itself a click.
    """
    r = math.sqrt(sum(v * v for v in sig) / max(1, len(sig)))
    k = rms / max(1e-9, r)
    out = [math.tanh(v * k * 1.05) * 0.94 for v in sig]
    data = array.array('h', (int(max(-32767, min(32767, v * 32767))) for v in out))
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data.tobytes())
    peak = max(abs(v) for v in out)
    print('  %-22s %5.2f s  rms %.3f  peak %.2f'
          % (os.path.basename(path), len(sig) / RATE, r * k, peak))


# THE OUTPUT DIRECTORY, ONLY WHEN THIS IS THE SCRIPT BEING RUN.
#
# `deedsfx.py` makes the sound of a deed out of the same resonators and
# envelopes as the footfalls, because a spell and a boot on a board are the
# same kind of problem and two sets of helpers would drift. It imports this
# file, and an import must not demand an argument or write a single wav.
OUT = sys.argv[1] if __name__ == '__main__' and len(sys.argv) > 1 else None
if OUT:
    os.makedirs(OUT, exist_ok=True)


# ---------------------------------------------------------------------------
# FOOTFALLS
#
# THREE OF EACH, and that is not indulgence. One sample played over and over
# at two steps a second is the most recognisable artificial sound a game can
# make -- the ear locks onto the repeat within about four paces and never lets
# go of it again. Three, chosen at random and pitched a little either way, is
# past where anyone can hear the pattern.
#
# What distinguishes one surface from another is almost entirely the ENVELOPE
# and the filter, not the material of the noise: earth absorbs and stops dead,
# grass swishes and has no attack at all, stone is a click with a room behind
# it, a board is a note, and water throws a handful of it up and lets it fall.
def footfall(name, seed, build):
    n = int(RATE * 0.42)

if __name__ == '__main__':
    write(os.path.join(OUT, 'step-%s.wav' % name), build(n, seed))


for v in range(3):
    s = 700 + v * 13

    # Beaten earth: a dull thud that stops. Almost no high end and no ring.
    footfall('earth%d' % (v + 1), s, lambda n, sd: mul(
        lowpass(noise(sd, n), 620.0, 2), env(n, 0.002, 0.045, 3.0)))

    # Grass: no attack worth the name, a short swish, and gone. Two bursts a
    # few milliseconds apart, because a boot in grass makes two sounds -- the
    # blades bending and the blades letting go.
    def grass(n, sd):
        a = mul(highpass(lowpass(noise(sd, n), 6200.0), 1500.0), env(n, 0.010, 0.055, 2.6))
        b = mul(highpass(lowpass(noise(sd + 1, n), 4800.0), 1900.0), env(n, 0.020, 0.075, 2.2))
        return mix(n, (a, 1.0), (b, 0.55))
    footfall('grass%d' % (v + 1), s, grass)

    # Flagstone: a hard click and the room it is in. The ring is what says
    # stone rather than board -- high, and it dies quickly.
    def stone(n, sd):
        click = mul(highpass(noise(sd, n), 2600.0), env(n, 0.0005, 0.010, 4.0))
        tail = mul(ring(mul(noise(sd + 2, n), env(n, 0.0005, 0.004, 5.0)), 1750.0, 7.0),
                   env(n, 0.001, 0.070, 2.4))
        body = mul(lowpass(noise(sd + 3, n), 900.0), env(n, 0.001, 0.025, 3.2))
        return mix(n, (click, 1.0), (tail, 0.55), (body, 0.40))
    footfall('stone%d' % (v + 1), s, stone)

    # A board: a note. Low, hollow, and it rings for longer than anything else
    # here because there is a space under it.
    def wood(n, sd):
        hit = mul(noise(sd, n), env(n, 0.0005, 0.006, 5.0))
        return mix(n,
                   (mul(ring(hit, 420.0, 11.0), env(n, 0.001, 0.11, 2.0)), 1.0),
                   (mul(ring(hit, 980.0, 6.0), env(n, 0.001, 0.05, 2.6)), 0.35),
                   (mul(lowpass(noise(sd + 4, n), 1200.0), env(n, 0.001, 0.020, 3.4)), 0.30))
    footfall('wood%d' % (v + 1), s, wood)

    # Shallow water: a splash goes UP and then comes down, so it is the one
    # footfall here whose envelope has a second half.
    def water(n, sd):
        up = mul(highpass(lowpass(noise(sd, n), 7000.0), 900.0), env(n, 0.004, 0.055, 2.0))
        # the fall back, delayed
        d = int(RATE * 0.055)
        down = [0.0] * n
        drip = mul(highpass(lowpass(noise(sd + 5, n), 5200.0), 1400.0), env(n, 0.010, 0.10, 2.4))
        for i in range(d, n):
            down[i] = drip[i - d]
        body = mul(lowpass(noise(sd + 6, n), 700.0), env(n, 0.002, 0.030, 3.0))
        return mix(n, (up, 1.0), (down, 0.45), (body, 0.35))
    footfall('water%d' % (v + 1), s, water)


# ---------------------------------------------------------------------------
# A FIRE.
#
# Two things at once and both are needed. The RUMBLE is the draught -- low,
# steady, slowly breathing -- and on its own it is a hairdryer. The CRACKLE is
# what makes it a fire: very short, very sharp transients at irregular
# intervals, and the irregularity matters more than the sound of any one of
# them. A crackle on a beat is a metronome.
def fire(secs=9.0, seed=31):
    """A hearth, not a broom.

    THE FIRST VERSION SOUNDED LIKE SOMEBODY SWEEPING THE FLOOR, and it was
    right to: its bed was noise lowpassed at 240Hz twice -- a rumble with
    nothing above it -- multiplied by a sine of exactly three cycles per loop.
    A low rumble that swells every three seconds IS a broom. Two things were
    wrong and both matter.

    A FIRE IS NOT A LOW SOUND. Most of what identifies one is the sizzle,
    which lives between one and five kilohertz. Filtering it away leaves the
    body of a fire with none of its voice, and the ear reaches for the nearest
    thing a slow low whoosh could be.

    AND A FIRE DOES NOT BREATHE ON A BEAT. Any periodic swell reads as a
    machine or a gesture -- a bellows, a broom, a saw. Real variation is
    irregular and much shallower than 45%. Two slow sines at incommensurate
    rates never line up inside a loop, so nothing in it has a period the ear
    can lock to.
    """
    n = int(RATE * secs)
    xf = int(RATE * 0.6)

    # The body: still low, but no longer the whole fire.
    body = lowpass(noise(seed, n + xf), 420.0, 2)
    # The sizzle, which is what actually says "fire". Band-limited noise up
    # where the ear looks for burning, kept well under the body so it reads as
    # part of one sound rather than a hiss laid on top of a rumble.
    sizz = highpass(lowpass(noise(seed + 3, n + xf), 5200.0, 1), 1100.0)
    base = [body[i] + sizz[i] * 0.55 for i in range(n + xf)]

    # Irregular, shallow breathing. 2.0 and 3.0 cycles per loop would beat
    # against each other on a three-second cycle -- the very thing being
    # fixed -- so they are deliberately incommensurate.
    for i in range(n + xf):
        a = 2.0 * math.pi * 2.0 / n
        b = 2.0 * math.pi * 5.0 / n
        wob = 0.5 * math.sin(a * i) + 0.5 * math.sin(b * i * 1.37 + 1.1)
        base[i] *= 0.88 + 0.12 * wob
    # Wrap the tail over the head so the filter's memory joins up.
    out = base[:n]
    for i in range(xf):
        k = i / xf
        out[i] = out[i] * k + base[n + i] * (1.0 - k)

    pops = [0.0] * n
    r = random.Random(seed + 9)
    t = 0.0
    while t < secs - 0.35:
        # Irregular: an exponential gap, which is what a Poisson process of
        # pops gives and what a fire actually does.
        t += r.expovariate(11.0) + 0.010
        if t >= secs - 0.35:
            break
        at = int(t * RATE)
        hard = r.random() ** 2.2               # a few loud ones, many small
        length = int(RATE * (0.006 + 0.030 * hard))
        tone = 900.0 + 2600.0 * r.random()
        burst = mul(ring(mul(noise(int(t * 9973) & 0xffff, length),
                             env(length, 0.0004, 0.004, 5.0)), tone, 4.0),
                    env(length, 0.0004, 0.010 + 0.030 * hard, 3.0))
        gain = 0.25 + 0.75 * hard
        for i in range(length):
            if at + i < n:
                pops[at + i] += burst[i] * gain
    # The crackles carry the fire now, so they are no longer under the bed.
    return mix(n, (out, 0.72), (pops, 1.15))


def chirp(length, f0, f1, curve=1.0):
    """One syllable: a swept tone, which is what a small bird actually makes.

    Birdsong is nearly pure tone that SLIDES. A fixed pitch reads as a beep
    and a noise burst reads as a click; the glide is the whole character, and
    the curve decides whether it rises like a question or falls away.
    """
    out = [0.0] * length
    phase = 0.0
    for i in range(length):
        k = (i / max(1, length - 1)) ** curve
        hz = f0 + (f1 - f0) * k
        phase += 2.0 * math.pi * hz / RATE
        # A touch of second harmonic: a pure sine is a test tone, and a real
        # syrinx is never quite pure.
        out[i] = math.sin(phase) + 0.18 * math.sin(2.0 * phase)
    return mul(out, env(length, 0.006, 0.9, 1.4))


def birds(secs=24.0, seed=71):
    """Daylight in the open, which until now was silent.

    NOT A CONTINUOUS TRACK. Birds are the clearest case of a sound whose
    realism is entirely in its spacing: a loop of steady chirping becomes a
    ringtone within a minute, while a call every few seconds with nothing
    between it disappears into the world and is only missed when it stops.
    So this is mostly silence, deliberately, and the loop is long enough that
    the pattern does not announce itself.

    Several voices, because one repeated call is one bird following you
    around. Each has its own pitch range and phrase shape.
    """
    n = int(RATE * secs)
    out = [0.0] * n
    r = random.Random(seed)

    # (low, high, syllables, gap between syllables, sweep curve, level)
    VOICES = [
        (3100.0, 4300.0, 3, 0.085, 0.8, 0.85),   # a quick rising triple
        (2300.0, 1700.0, 2, 0.130, 1.6, 0.70),   # a falling pair
        (4200.0, 4600.0, 5, 0.055, 1.0, 0.55),   # a thin fast trill
        (1900.0, 2600.0, 1, 0.000, 0.7, 0.60),   # one short rising note
    ]

    t = 0.6
    while t < secs - 1.2:
        lo, hi, syl, gap, curve, lvl = VOICES[r.randrange(len(VOICES))]
        # Each bird is a little off its neighbours; identical pitch twice is
        # what makes a loop sound like a loop.
        tune = 0.88 + 0.24 * r.random()
        at = t
        for _ in range(syl):
            length = int(RATE * (0.045 + 0.055 * r.random()))
            sig = chirp(length, lo * tune, hi * tune, curve)
            start = int(at * RATE)
            g = lvl * (0.55 + 0.45 * r.random())
            for i in range(length):
                if start + i < n:
                    out[start + i] += sig[i] * g
            at += gap + 0.010 * r.random()
        # The gap between calls, which is most of the track.
        t += 1.8 + r.expovariate(0.45)

    return out


    write(os.path.join(OUT, 'amb-birds.wav'), birds(), rms=0.030)


    write(os.path.join(OUT, 'amb-fire.wav'), fire(), rms=0.085)


# ---------------------------------------------------------------------------
# RAIN, TWICE.
#
# Rain in the open is a broad hiss with almost nothing under it. Rain heard
# from UNDER A THATCH is a different sound entirely -- the hiss is gone, the
# straw absorbs everything above a couple of kilohertz, and what is left is a
# soft patter with the odd heavy drop off the eaves. Crossfading between the
# two as somebody steps through a doorway is most of what makes a roof feel
# like shelter.
# ---------------------------------------------------------------------------
# THE OTHER VOICES, BECAUSE ONE BIRDSONG EVERYWHERE IS ONE MESH FOR EVERY PROP
#
# `birds()` above is a meadow at noon and it was playing over the moor, over
# the shingle and over the peat as well, which is the audio version of the
# thing this project spends most of its effort not doing. What a place sounds
# like is most of what tells you where you are, and the window already knows
# which country the ground underfoot belongs to.
#
# So: songbirds keep the green and settled ground; the high bleak ground gets
# CROWS; the shore gets GULLS; the fens get FROGS. Each is built the same way
# as everything else here -- a source with the right roughness through the
# right resonances, with the right envelope -- and none of them is pretending
# to be a recording.
# ---------------------------------------------------------------------------

def rasp(length, breaks, seed, jitter=0.06):
    """A rough pulse train: the voice behind a caw, a cry and a croak.

    `chirp` above is a swept SINE, which is right for a small bird because a
    small bird is very nearly a whistle. Nothing else here is. A crow, a gull
    and a frog are all a buzzing source driven through a resonant throat, and
    the buzz is what makes them harsh: a pulse train has every harmonic in it,
    so the resonances have something to pick out.

    `breaks` is the pitch over the sound as a list of hertz, interpolated --
    a gull's cry rises and then falls, and one number cannot say that. The
    jitter is what stops it reading as a synthesiser: no animal holds a pitch.
    """
    r = random.Random(seed)
    out = [0.0] * length
    phase = 0.0
    last = len(breaks) - 1
    for i in range(length):
        k = (i / max(1, length - 1)) * last
        lo = min(int(k), last)
        hi = min(lo + 1, last)
        hz = breaks[lo] + (breaks[hi] - breaks[lo]) * (k - lo)
        phase += hz / RATE * (1.0 + jitter * (r.random() - 0.5))
        if phase >= 1.0:
            phase -= 1.0
            out[i] = 1.0
    return out


def throat(src, formants, seed, breath=0.0):
    """Ring a source through several resonances, with optional rasp on top."""
    n = len(src)
    layers = [(ring(src, hz, q), g) for hz, q, g in formants]
    if breath > 0.0:
        layers.append((lowpass(highpass(noise(seed, n), 700.0), 5000.0), breath))
    return mix(n, *layers)


def caw(seed, near=1.0):
    """One crow. Short, harsh, and falling slightly, which is the whole of it.

    A caw that holds its pitch sounds like a duck. The fall is small -- a
    hundred hertz over a quarter of a second -- and it is the difference.
    """
    n = int(RATE * 0.30)
    src = rasp(n, [640.0, 590.0, 520.0], seed, jitter=0.11)
    body = throat(src, [(760.0, 6.0, 1.0), (1560.0, 8.0, 0.52),
                        (2750.0, 10.0, 0.26)], seed + 1, breath=0.30)
    # DISTANCE IS A FILTER AND NOT A FADER. A crow three fields away is not a
    # quiet crow, it is a crow with its top gone; turning one down instead
    # leaves it sitting on your shoulder at a whisper.
    if near < 1.0:
        body = lowpass(body, 900.0 + 2600.0 * near, 2)
    return mul(body, env(n, 0.010, 0.075 + 0.02 * near, 2.6))


def crows(secs=24.0, seed=311):
    """The moor, the crags and the peat: the ground with no trees on it.

    Crows call in GROUPS, two to four in a row with a beat between them, and
    then nothing for a long time. A single caw every few seconds reads as a
    machine; the grouping is what makes it a bird that has just noticed you.
    """
    n = int(RATE * secs)
    out = [0.0] * n
    r = random.Random(seed)
    t = 0.9
    while t < secs - 1.4:
        # Most of them are far off. A moor is big and mostly empty, and a
        # window full of close crows is a horror film.
        near = 0.25 + 0.75 * (r.random() ** 2.2)
        lvl = (0.30 + 0.70 * near) * (0.7 + 0.3 * r.random())
        at = t
        for _ in range(r.randint(2, 4)):
            one = caw(r.randrange(1 << 28), near)
            start = int(at * RATE)
            for i, v in enumerate(one):
                if start + i < n:
                    out[start + i] += v * lvl
            at += 0.30 + 0.16 * r.random()
        t += 3.0 + r.expovariate(0.30)
    return out


def gull_cry(seed, near=1.0):
    """One herring gull: up, then away. The bend is the bird."""
    n = int(RATE * 0.42)
    src = rasp(n, [1150.0, 2050.0, 1750.0, 980.0], seed, jitter=0.05)
    body = throat(src, [(1300.0, 9.0, 1.0), (2600.0, 12.0, 0.45),
                        (3900.0, 14.0, 0.18)], seed + 1, breath=0.18)
    if near < 1.0:
        body = lowpass(body, 1400.0 + 3600.0 * near, 2)
    return mul(body, env(n, 0.018, 0.16, 1.8))


def gulls(secs=24.0, seed=907):
    """The shore. Gulls laugh: a run of cries that speeds up and drops away."""
    n = int(RATE * secs)
    out = [0.0] * n
    r = random.Random(seed)
    t = 0.7
    while t < secs - 1.8:
        near = 0.2 + 0.8 * (r.random() ** 2.0)
        lvl = (0.28 + 0.72 * near) * (0.65 + 0.35 * r.random())
        at = t
        gap = 0.42 + 0.14 * r.random()
        for k in range(r.randint(3, 6)):
            one = gull_cry(r.randrange(1 << 28), near)
            start = int(at * RATE)
            # Each cry in a run is a little lower and a little quieter than
            # the one before, which is what makes it a run and not a list.
            fade = lvl * (1.0 - 0.10 * k)
            for i, v in enumerate(one):
                if start + i < n:
                    out[start + i] += v * fade
            at += gap
            gap *= 0.88
        t += 3.4 + r.expovariate(0.26)
    return out


def croak(seed, near=1.0):
    """One frog. A rattle, not a note: the pulses are slow enough to count."""
    n = int(RATE * 0.34)
    # THE PULSE RATE IS THE ANIMAL. Sixty a second is a rattle the ear can
    # hear the grain of; six hundred would be a pitch and this would be a duck.
    rate = 52.0 + 18.0 * random.Random(seed).random()
    src = rasp(n, [rate, rate * 0.92], seed, jitter=0.16)
    body = throat(src, [(430.0, 5.0, 1.0), (980.0, 7.0, 0.40),
                        (1700.0, 9.0, 0.14)], seed + 1, breath=0.12)
    if near < 1.0:
        body = lowpass(body, 600.0 + 1800.0 * near, 2)
    return mul(body, env(n, 0.020, 0.10, 2.0))


def frogs(secs=24.0, seed=1187):
    """The fens and the peat, after the reeds and before the water.

    Frogs answer each other. One starts, two more take it up, and then the
    whole pool stops at once for no reason anybody has ever established.
    """
    n = int(RATE * secs)
    out = [0.0] * n
    r = random.Random(seed)
    t = 0.5
    while t < secs - 1.2:
        near = 0.3 + 0.7 * (r.random() ** 1.6)
        lvl = (0.35 + 0.65 * near) * (0.6 + 0.4 * r.random())
        at = t
        for _ in range(r.randint(2, 7)):
            one = croak(r.randrange(1 << 28), near)
            start = int(at * RATE)
            for i, v in enumerate(one):
                if start + i < n:
                    out[start + i] += v * lvl
            at += 0.22 + 0.30 * r.random()
        t += 2.2 + r.expovariate(0.42)
    return out


    write(os.path.join(OUT, 'amb-crows.wav'), crows(), rms=0.028)
    write(os.path.join(OUT, 'amb-gulls.wav'), gulls(), rms=0.028)
    write(os.path.join(OUT, 'amb-frogs.wav'), frogs(), rms=0.026)


def rain_open(secs=16.0, seed=51):
    n = int(RATE * secs)
    xf = int(RATE * 1.2)
    hiss = highpass(lowpass(noise(seed, n + xf), 9000.0), 800.0)
    body = lowpass(highpass(noise(seed + 1, n + xf), 200.0), 2200.0)
    both = [hiss[i] + 0.45 * body[i] for i in range(n + xf)]
    for i in range(n + xf):
        w1 = 2.0 * math.pi * 2.0 / n
        w2 = 2.0 * math.pi * 5.0 / n
        both[i] *= (0.80 + 0.20 * 0.5 * (1.0 + math.sin(w1 * i))) \
                 * (0.88 + 0.12 * 0.5 * (1.0 + math.sin(w2 * i + 1.3)))
    out = both[:n]
    for i in range(xf):
        k = i / xf
        out[i] = out[i] * k + both[n + i] * (1.0 - k)
    return out


def rain_roof(secs=16.0, seed=61):
    n = int(RATE * secs)
    xf = int(RATE * 1.2)
    soft = lowpass(noise(seed, n + xf), 1500.0, 2)
    out = soft[:n]
    for i in range(xf):
        k = i / xf
        out[i] = out[i] * k + soft[n + i] * (1.0 - k)
    # And the drops off the eaves: sparse, low, and each one a small note.
    r = random.Random(seed + 3)
    drops = [0.0] * n
    t = 0.0
    while t < secs - 0.4:
        t += r.expovariate(3.0) + 0.05
        if t >= secs - 0.4:
            break
        at = int(t * RATE)
        length = int(RATE * 0.18)
        tone = 320.0 + 900.0 * r.random()
        d = mul(ring(mul(noise(int(t * 7919) & 0xffff, length),
                         env(length, 0.0005, 0.003, 5.0)), tone, 9.0),
                env(length, 0.001, 0.045, 2.6))
        for i in range(length):
            if at + i < n:
                drops[at + i] += d[i] * (0.3 + 0.7 * r.random())
    return mix(n, (out, 1.0), (drops, 0.55))


def learned(seed=907):
    """THE SOUND OF A CRAFT GOING UP A RUNG.

    A citizen fells forty trees and a number changes in a panel they have to
    open to see. That is bookkeeping, and a level in this world is not
    bookkeeping -- it is the thing they spent the afternoon on. So it gets a
    sound, and the sound has to be unmistakable at a glance of the ear: it is
    the only cue in this window that is a TUNE rather than a texture.

    Three notes, rising, struck rather than blown -- the same resonator the
    footfalls use, which is why it belongs to this window and not to a sound
    library. They overlap, so the third is still ringing over the first: a
    chord that arrives rather than three beeps in a row.

    Deliberately short. A fanfare that takes two seconds is a fanfare a player
    resents by the twentieth time, and this world has nine crafts in it.
    """
    secs = 1.15
    n = int(secs * RATE)
    out = [0.0] * n
    # A fifth and an octave over the root: the interval that reads as "up"
    # in every music anybody in this world would have heard.
    for k, (hz, at, gain) in enumerate((
            (392.0, 0.00, 1.00),
            (587.3, 0.085, 0.92),
            (784.0, 0.170, 0.85))):
        length = n - int(at * RATE)
        if length <= 0:
            continue
        # Struck: a click of noise through a resonator, which gives the note
        # a body and an edge rather than a sine's nothing.
        hit = mul(noise(seed + k * 31, length), env(length, 0.0004, 0.0018, 6.0))
        tone = ring(hit, hz, 26.0)
        # And a quiet octave above, so the note has a rim to it.
        tone = mix(length, (tone, 1.0), (ring(hit, hz * 2.0, 20.0), 0.22))
        body = mul(tone, env(length, 0.002, 0.34, 2.0))
        start = int(at * RATE)
        for i in range(length):
            out[start + i] += body[i] * gain
    return out


    write(os.path.join(OUT, 'cue-learned.wav'), learned(), rms=0.075)
    write(os.path.join(OUT, 'amb-rain.wav'), rain_open(), rms=0.105)
    write(os.path.join(OUT, 'amb-rainroof.wav'), rain_roof(), rms=0.085)
