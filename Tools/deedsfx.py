#!/usr/bin/env python3
"""The sound of a deed, and in particular the sound of the eleven spells.

Sorcery was silent and had no animation either, for the same reason: no spell
sets an `action`, so nothing about a cast reached the window at all. The world
does record `deed`, the verb a citizen performed on an interval, and the window
reads it now. This makes the noise that goes with it.

THE SAME RESONATORS AS THE FOOTFALLS. `sfx.py` builds a boot on a board out of
filtered noise through a two-pole resonator, and a spell is the same kind of
problem: there is no recording to hand, and a bad imitation of a magical noise
is worse than no noise. Everything here is shaped noise with an envelope, which
is not pretending to be anything.

THE TWO BOOKS SOUND DIFFERENT ON PURPOSE. The common book refuses, repairs and
unmakes, and the engine says of it "not one hurts anybody": those are clean,
tuned and mostly rising. The barrow book is the one that does harm, and it is
untuned, low and dry.

  deedsfx.py <out-dir>
"""
import math, os, sys

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
from sfx import RATE, noise, lowpass, highpass, ring, env, mul, mix, write


def secs(n):
    return int(n * RATE)


def tone(seed, length, hz, q=30.0, attack=0.004, decay=0.30, curve=2.2):
    """A struck note: a click of noise through a resonator, then an envelope."""
    hit = mul(noise(seed, length), env(length, 0.0005, 0.002, 6.0))
    body = ring(hit, hz, q)
    return mul(body, env(length, attack, decay, curve))


def sweep(seed, length, lo, hi, q=22.0, steps=26):
    """A note that slides. Built as overlapping struck notes rather than as a
    real glide, because a chain of short rings reads as a slide and a phase
    accumulator here would want a proper oscillator this file does not have."""
    out = [0.0] * length
    for k in range(steps):
        u = k / max(1, steps - 1)
        at = int(u * length * 0.72)
        span = length - at
        if span <= 0:
            continue
        hz = lo * ((hi / lo) ** u)
        part = tone(seed + k * 17, span, hz, q, 0.001, 0.055, 3.0)
        for i in range(span):
            out[at + i] += part[i] * (0.35 + 0.65 * (1.0 - abs(0.5 - u) * 2.0))
    return out


def breath(seed, length, hz, width=1, gain=1.0):
    """Air: noise with the top taken off and a slow swell."""
    air = lowpass(noise(seed, length), hz, width)
    return mul(air, env(length, 0.06, 0.55, 1.6))


# ---------------------------------------------------------------------------
# THE COMMON BOOK. Clean, tuned, and none of it does harm.

def still():
    """THE STILLING: a held ring that is cut off.

    It stops a fight. So the sound is a note that is going somewhere and is
    not allowed to get there: a fifth struck and ringing, and then silence
    arriving early and hard. The cut is the whole idea and it has to be
    abrupt enough to feel like an interruption rather than a fade.
    """
    n = secs(0.85)
    out = mix(n, (tone(11, n, 294.0, 44.0, 0.006, 0.9, 1.2), 1.0),
                 (tone(12, n, 441.0, 40.0, 0.008, 0.9, 1.2), 0.62))
    stop = secs(0.42)
    for i in range(stop, n):
        # Four milliseconds of ramp, which is a cut without a click.
        k = max(0.0, 1.0 - (i - stop) / (0.004 * RATE))
        out[i] *= k
    return out


def seal():
    """HOLDING A DROPPED PACK: a lock set over it, once and for good.

    NOT "shutting a way", which is what the engine's own summary comment still
    says of this spell. §6bn changed it and the list was never brought along:
    what it does is lock a dead citizen's pack so only they can lift it, and
    hold off the rot while it lasts. It can be cast on a given pile once ever.

    So it is a weight coming down and then a latch: the heavy part says the
    pile is not going anywhere, and the ring on top says it was shut by
    somebody rather than merely dropped.
    """
    n = secs(0.8)
    knock = mul(noise(21, n), env(n, 0.001, 0.05, 5.0))
    at = secs(0.16)
    span = n - at
    latch = mix(span, (tone(23, span, 1320.0, 64.0, 0.001, 0.30, 2.4), 1.0),
                      (tone(24, span, 880.0, 52.0, 0.001, 0.22, 2.6), 0.45))
    out = mix(n, (ring(knock, 96.0, 12.0), 1.0),
                 (ring(knock, 61.0, 9.0), 0.8),
                 (mul(lowpass(noise(22, n), 220.0, 2), env(n, 0.002, 0.5, 2.6)), 0.35))
    for i in range(span):
        out[at + i] += latch[i] * 0.5
    return out


def transmute():
    """TURNING A THING INTO MONEY: a shimmer that resolves into a coin.

    It is the one spell worked on an object in your own hand, so it is close,
    small and bright, and it ENDS on something recognisable rather than
    trailing off: the thing is gone and the money is there.
    """
    n = secs(0.95)
    shine = sweep(31, n, 520.0, 1560.0, 26.0, 22)
    coin_at = secs(0.55)
    span = n - coin_at
    coin = mix(span, (tone(33, span, 1860.0, 60.0, 0.001, 0.34, 2.0), 1.0),
                     (tone(34, span, 2480.0, 55.0, 0.001, 0.26, 2.2), 0.55))
    out = mix(n, (shine, 0.7))
    for i in range(span):
        out[coin_at + i] += coin[i] * 0.95
    return out


def unmake():
    """TAKING A THING APART: one note becoming several, downward."""
    n = secs(0.9)
    parts = []
    for k, hz in enumerate((680.0, 494.0, 370.0, 262.0)):
        at = secs(0.04 + k * 0.075)
        span = n - at
        parts.append((at, tone(41 + k, span, hz, 30.0, 0.002, 0.26, 2.4)))
    out = [0.0] * n
    for at, sig in parts:
        for i in range(len(sig)):
            out[at + i] += sig[i] * 0.8
    crack = mul(highpass(noise(45, n), 1800.0), env(n, 0.001, 0.12, 4.0))
    return mix(n, (out, 1.0), (crack, 0.22))


def mend():
    """CLOSING YOUR OWN WOUNDS: warm, rising, and over quickly."""
    n = secs(0.8)
    return mix(n, (tone(51, n, 392.0, 38.0, 0.03, 0.42, 1.8), 1.0),
                  (tone(52, n, 523.3, 34.0, 0.06, 0.40, 1.8), 0.7),
                  (breath(53, n, 900.0, 2), 0.16))


def mendp():
    """CLOSING SOMEBODY ELSE'S: the same warmth, but sent.

    A wand is what sends it, so there is a departure at the front that
    `mend` does not have: air leaving, then the note arriving.
    """
    n = secs(0.9)
    send = mul(lowpass(noise(61, n), 2600.0), env(n, 0.004, 0.10, 4.0))
    at = secs(0.10)
    span = n - at
    warm = mix(span, (tone(62, span, 392.0, 38.0, 0.02, 0.44, 1.8), 1.0),
                     (tone(63, span, 523.3, 34.0, 0.04, 0.40, 1.8), 0.7))
    out = mix(n, (send, 0.5))
    for i in range(span):
        out[at + i] += warm[i]
    return out


# §6bq: THE RECALL HAD A SOUND AND THE CONSTITUTION REPEALED THE SPELL.
# It was a long wind-up that snapped shut, written for the one thing in either
# book that neither refused, repaired nor unmade anything. The world has no
# voluntary teleport left, so nothing can ever ask for it.


def invoke():
    """PRESSING A SIGIL: three stones, at an altar, kneeling.

    Grinding stone and then a struck bell, because the making of the thing is
    work and the finish of it is not.
    """
    n = secs(1.1)
    grind = mul(lowpass(noise(81, n), 700.0, 2), env(n, 0.03, 0.42, 1.5))
    at = secs(0.5)
    span = n - at
    bell = mix(span, (tone(82, span, 660.0, 70.0, 0.001, 0.55, 1.6), 1.0),
                     (tone(83, span, 990.0, 60.0, 0.001, 0.40, 1.8), 0.4))
    out = mix(n, (grind, 0.55))
    for i in range(span):
        out[at + i] += bell[i] * 0.85
    return out


# ---------------------------------------------------------------------------
# THE BARROW BOOK. Untuned, low and dry. None of it resolves.

def rot():
    """THE ROT: wet, low, and it keeps going after it should have stopped."""
    n = secs(1.0)
    churn = mul(lowpass(noise(91, n), 300.0, 3), env(n, 0.02, 0.62, 1.3))
    burst = mul(lowpass(noise(92, n), 900.0, 1), env(n, 0.001, 0.09, 5.0))
    return mix(n, (churn, 1.0), (burst, 0.3),
                  (ring(burst, 73.0, 8.0), 0.45))


def taking():
    """THE TAKING: a pull inward. The only sound here that runs backwards."""
    n = secs(0.9)
    # Falling rather than rising, which is what makes it read as a draw in
    # rather than a push out.
    draw = sweep(101, n, 900.0, 180.0, 20.0, 24)
    suck = mul(lowpass(noise(102, n), 1400.0, 2), env(n, 0.30, 0.18, 1.1))
    return mix(n, (draw, 0.75), (suck, 0.4))


def waking():
    """THE WAKING: calling something up. Hollow, and it answers."""
    n = secs(1.25)
    call = mix(n, (tone(111, n, 147.0, 26.0, 0.05, 0.75, 1.3), 1.0),
                  (tone(112, n, 220.5, 22.0, 0.08, 0.60, 1.4), 0.45))
    at = secs(0.62)
    span = n - at
    # The answer, a fifth below and dry: something that was not there before.
    answer = mul(ring(mul(noise(113, span), env(span, 0.002, 0.02, 5.0)), 98.0, 14.0),
                 env(span, 0.01, 0.5, 1.6))
    out = mix(n, (call, 0.8), (breath(114, n, 380.0, 3), 0.2))
    for i in range(span):
        out[at + i] += answer[i] * 0.7
    return out


def withering():
    """THE WITHERING: dry, long, and descending. Nothing in it is wet."""
    n = secs(1.4)
    rasp = mul(highpass(noise(121, n), 900.0), env(n, 0.10, 0.85, 1.2))
    fall = sweep(122, n, 420.0, 96.0, 16.0, 28)
    return mix(n, (rasp, 0.55), (fall, 0.7))


# ---------------------------------------------------------------------------
# AND THE DEEDS THAT ARE NOT SPELLS but were also silent. Cheap to add while
# the path exists, and each one is a thing a citizen does dozens of times.

def bury():
    n = secs(0.8)
    dig = mul(lowpass(noise(131, n), 420.0, 2), env(n, 0.01, 0.45, 1.6))
    return mix(n, (dig, 1.0), (ring(dig, 84.0, 7.0), 0.3))


def smith():
    """A hammer on an anvil: the one sound in this world everybody knows."""
    n = secs(0.9)
    blow = mul(noise(141, n), env(n, 0.0004, 0.004, 7.0))
    return mix(n, (ring(blow, 1180.0, 90.0), 1.0),
                  (ring(blow, 1770.0, 70.0), 0.5),
                  (ring(blow, 232.0, 16.0), 0.35))


def drink():
    n = secs(0.7)
    gulp = mul(lowpass(noise(151, n), 600.0, 2), env(n, 0.01, 0.26, 2.4))
    return mix(n, (gulp, 1.0), (ring(gulp, 210.0, 12.0), 0.4))


def eat():
    n = secs(0.6)
    bite = mul(lowpass(noise(161, n), 1500.0, 1), env(n, 0.003, 0.20, 3.0))
    return mix(n, (bite, 1.0))


# ---------------------------------------------------------------------------
# AND THE FOUR GAMBITS. A weapon's own move, and seven weapons have one.
#
# They already looked different: the look asset has a motion per weapon, so a
# dagger's flurry and a maul's whole-body blow are plainly not the same thing.
# Heard, they were one noise. These are keyed the same way the motions are,
# `gambit.<what is in the hand>`, so a kind shared by two weapons is one sound.

def flurry():
    """SEVERAL BLOWS AT ONCE: four strikes inside a heartbeat."""
    n = secs(0.75)
    out = [0.0] * n
    for k, at in enumerate((0.00, 0.075, 0.15, 0.225)):
        a = secs(at)
        span = n - a
        if span <= 0:
            continue
        cut = mul(highpass(noise(201 + k * 13, span), 1200.0),
                  env(span, 0.0008, 0.055, 5.0))
        part = mix(span, (cut, 1.0), (ring(cut, 2100.0 - k * 120.0, 46.0), 0.55))
        for i in range(span):
            out[a + i] += part[i] * (1.0 - k * 0.12)
    return out


def whole():
    """ONE BLOW WITH EVERYTHING IN IT: slow, low and it lands once."""
    n = secs(1.0)
    swing = mul(lowpass(noise(211, n), 1100.0, 1), env(n, 0.12, 0.10, 2.0))
    at = secs(0.26)
    span = n - at
    hit = mul(noise(212, span), env(span, 0.0006, 0.006, 6.0))
    land = mix(span, (ring(hit, 128.0, 11.0), 1.0), (ring(hit, 74.0, 8.0), 0.8),
                     (mul(lowpass(noise(213, span), 400.0, 2),
                          env(span, 0.002, 0.42, 2.2)), 0.45))
    out = mix(n, (swing, 0.35))
    for i in range(span):
        out[at + i] += land[i]
    return out


def now():
    """IT GOES OFF AT ONCE: a siphon, so it is pressure and then fire."""
    n = secs(0.95)
    crack = mul(noise(221, n), env(n, 0.0005, 0.012, 6.0))
    roar = mul(lowpass(noise(222, n), 1800.0, 1), env(n, 0.01, 0.55, 1.7))
    return mix(n, (ring(crack, 420.0, 18.0), 0.7), (roar, 1.0))


def far():
    """ONE SHOT, A LONG WAY: nine tiles, and it is aimed."""
    n = secs(1.1)
    draw = mul(highpass(noise(231, n), 700.0), env(n, 0.22, 0.06, 2.4))
    at = secs(0.30)
    span = n - at
    loose = mul(noise(232, span), env(span, 0.0006, 0.018, 5.5))
    shot = mix(span, (ring(loose, 620.0, 30.0), 1.0),
                     (ring(loose, 240.0, 14.0), 0.6))
    tail = mul(lowpass(noise(233, span), 900.0, 2), env(span, 0.02, 0.62, 1.4))
    out = mix(n, (draw, 0.45))
    for i in range(span):
        out[at + i] += shot[i] + tail[i] * 0.35
    return out


def report():
    """ONE SHOT WITH EVERYTHING IN IT: a handgonne going off.

    It used to be filed as a flurry and it never was one. §6af-vii collapsed
    the burst to a single blow when a citizen's flesh became flat, and put the
    damage into `hit: 36`, the hardest in the world, against the worst accuracy
    in the world. The engine's own word for what a gonne does is a report:
    "both barrels are one report, and no louder".

    So: a crack with almost nothing before it, a deep body under it, and a tail
    that goes on longer than anything else in this file. The tail is the point.
    A gun is loud after it has finished being loud.
    """
    n = secs(1.6)
    crack = mul(noise(241, n), env(n, 0.0004, 0.010, 7.0))
    body = mix(n, (ring(crack, 88.0, 7.0), 1.0), (ring(crack, 143.0, 9.0), 0.6))
    blast = mul(lowpass(noise(242, n), 2600.0, 1), env(n, 0.001, 0.16, 4.0))
    tail = mul(lowpass(noise(243, n), 700.0, 2), env(n, 0.02, 1.05, 1.15))
    return mix(n, (crack, 0.5), (body, 1.0), (blast, 0.55), (tail, 0.40))


# ---------------------------------------------------------------------------
# THE WORK. The eleven spells had sounds and an axe did not.
#
# `gather` is the most common thing anybody does in this world -- felling,
# mining and fishing all go through it -- and it was silent, along with combat,
# cooking and lighting a fire. Fifty-eight of the world's sixty-nine verbs made
# no noise at all, so a citizen could cut a tree down for ten minutes in total
# quiet while the animation swung perfectly.
#
# These are keyed by WHAT IS IN THE HAND, because that is what the window can
# refine on (IntervalCitizens.cpp: it tries `verb.<held>` and falls back to the
# plain verb). It is also the truer rule: the noise of gathering is the noise
# of the tool, and a citizen pulling herbs up by hand should not sound like an
# axe.

def chop():
    """AN AXE BITING WOOD. A bite, then the tree answering.

    Two parts, and the second is what makes it wood rather than a hit: the
    edge going in is a short broadband crack, and what follows is the trunk
    ringing low and dead. Wood has almost no sustain, so the resonator is
    heavily damped -- a high Q here sounds like a xylophone, which is a plank,
    not a tree.
    """
    n = secs(0.7)
    bite = mul(noise(311, n), env(n, 0.0006, 0.012, 6.0))
    edge = mix(n, (ring(bite, 2100.0, 26.0), 0.55), (ring(bite, 3400.0, 18.0), 0.30))
    trunk = mix(n, (ring(bite, 168.0, 9.0), 1.0), (ring(bite, 247.0, 7.0), 0.55))
    splinter = mul(highpass(noise(312, n), 2600.0), env(n, 0.002, 0.09, 4.0))
    return mix(n, (edge, 0.8), (trunk, 1.0), (splinter, 0.28))


def mine():
    """A PICK ON STONE. Harder, brighter and shorter than the axe.

    Stone does not absorb the way wood does, so this keeps a real ring and a
    little grit falling after it. The pitch sits above the anvil's so a mine
    and a smithing are not confused across a market place.
    """
    n = secs(0.75)
    strike = mul(noise(321, n), env(n, 0.0004, 0.006, 7.0))
    stone = mix(n, (ring(strike, 1520.0, 70.0), 1.0),
                   (ring(strike, 2260.0, 55.0), 0.45),
                   (ring(strike, 390.0, 14.0), 0.35))
    grit = mul(highpass(noise(322, n), 3200.0), env(n, 0.03, 0.30, 2.8))
    return mix(n, (stone, 1.0), (grit, 0.22))


def angle():
    """A LINE GOING OUT OVER WATER, and the small sound of it landing.

    Named for the old word rather than `fish`, which is also an item. It is
    the quietest thing in this file on purpose: fishing is done standing still
    and a loud one would wear out in a minute.
    """
    n = secs(0.95)
    cast = mul(highpass(noise(331, n), 900.0), env(n, 0.05, 0.16, 2.2))
    at = secs(0.34)
    span = n - at
    plop = mul(noise(332, span), env(span, 0.001, 0.05, 5.0))
    water = mix(span, (ring(plop, 620.0, 22.0), 1.0), (ring(plop, 330.0, 14.0), 0.6))
    ripple = mul(lowpass(noise(333, span), 1400.0, 2), env(span, 0.02, 0.5, 1.5))
    out = mix(n, (cast, 0.40))
    for i in range(span):
        out[at + i] += water[i] * 0.75 + ripple[i] * 0.18
    return out


def pull():
    """GATHERING WITH NOTHING IN YOUR HANDS: a stalk giving way.

    The fallback, for everything picked rather than struck. No resonator at
    all: it is a tear, and a tear has no note in it.
    """
    n = secs(0.45)
    tear = mul(highpass(noise(341, n), 1500.0), env(n, 0.006, 0.20, 2.6))
    soil = mul(lowpass(noise(342, n), 500.0, 2), env(n, 0.01, 0.16, 2.0))
    return mix(n, (tear, 1.0), (soil, 0.35))


def strike():
    """STEEL ON STEEL. The ordinary swing, which had no sound at all.

    Only the gambits made a noise, so a fight was five silent blows and one
    loud one. This is the blow itself: an edge meeting an edge, with enough
    ring to be metal and enough noise under it to be a body behind it.
    """
    n = secs(0.6)
    hit = mul(noise(351, n), env(n, 0.0004, 0.005, 7.0))
    steel = mix(n, (ring(hit, 2480.0, 85.0), 1.0),
                   (ring(hit, 3720.0, 60.0), 0.40),
                   (ring(hit, 940.0, 30.0), 0.45))
    weight = mul(lowpass(noise(352, n), 700.0, 2), env(n, 0.001, 0.10, 4.0))
    return mix(n, (steel, 1.0), (weight, 0.40))


def thud():
    """A FIST, OR A CLUB: the same blow with the metal taken out."""
    n = secs(0.5)
    hit = mul(noise(361, n), env(n, 0.0008, 0.018, 5.5))
    return mix(n, (ring(hit, 190.0, 8.0), 1.0),
                  (ring(hit, 96.0, 6.0), 0.7),
                  (mul(lowpass(noise(362, n), 900.0, 2), env(n, 0.001, 0.07, 4.5)), 0.5))


def loose():
    """A BOWSTRING LET GO. Draw, release, and the arrow leaving."""
    n = secs(0.7)
    draw = mul(highpass(noise(371, n), 800.0), env(n, 0.16, 0.05, 2.6))
    at = secs(0.22)
    span = n - at
    snap = mul(noise(372, span), env(span, 0.0005, 0.014, 6.0))
    string = mix(span, (ring(snap, 760.0, 34.0), 1.0), (ring(snap, 290.0, 16.0), 0.5))
    fly = mul(highpass(noise(373, span), 2200.0), env(span, 0.01, 0.22, 2.2))
    out = mix(n, (draw, 0.35))
    for i in range(span):
        out[at + i] += string[i] + fly[i] * 0.25
    return out


def kindle():
    """A FIRE CATCHING: a scrape, then air taking hold."""
    n = secs(1.1)
    scrape = mul(highpass(noise(381, n), 2400.0), env(n, 0.004, 0.10, 3.5))
    at = secs(0.18)
    span = n - at
    catch = mul(lowpass(noise(382, span), 2000.0, 1), env(span, 0.12, 0.70, 1.3))
    crackle = mul(highpass(noise(383, span), 3000.0), env(span, 0.20, 0.55, 1.8))
    out = mix(n, (scrape, 0.70))
    for i in range(span):
        out[at + i] += catch[i] * 0.55 + crackle[i] * 0.22
    return out


def char():
    """FOOD OVER A FIRE: a hiss that settles rather than a bang."""
    n = secs(1.0)
    hiss = mul(highpass(noise(391, n), 1800.0), env(n, 0.03, 0.70, 1.4))
    fat = mul(lowpass(noise(392, n), 1100.0, 2), env(n, 0.06, 0.55, 1.6))
    return mix(n, (hiss, 1.0), (fat, 0.45))


def whittle():
    """FLETCHING: a blade taken down a shaft, several times."""
    n = secs(0.9)
    out = [0.0] * n
    for k in range(3):
        at = secs(0.02 + k * 0.26)
        span = n - at
        if span <= 0:
            continue
        pass_ = mul(highpass(noise(401 + k, span), 1600.0), env(span, 0.02, 0.15, 2.4))
        for i in range(span):
            out[at + i] += pass_[i] * (1.0 - k * 0.18)
    return out


def grind():
    """A QUERN, OR A STONE ON AN EDGE: low, continuous and rough."""
    n = secs(1.2)
    rough = mul(lowpass(noise(411, n), 1600.0, 1), env(n, 0.08, 0.85, 1.2))
    body = ring(rough, 210.0, 6.0)
    rasp = mul(highpass(noise(412, n), 2600.0), env(n, 0.10, 0.75, 1.5))
    return mix(n, (rough, 0.8), (body, 0.6), (rasp, 0.25))


def effort():
    """A CITIZEN'S OWN VOICE: the breath a blow is thrown on.

    No vowel and no pitch tracking: a formant pair over filtered noise, which
    reads as a person making an effort without pretending to be a recording of
    one. It plays UNDER the deed sounds, which is why it is quiet and short.
    """
    n = secs(0.42)
    air = mul(noise(421, n), env(n, 0.012, 0.22, 2.0))
    voiced = mix(n, (ring(air, 620.0, 12.0), 1.0),
                    (ring(air, 1180.0, 9.0), 0.55),
                    (ring(air, 148.0, 7.0), 0.45))
    return mul(voiced, env(n, 0.02, 0.26, 1.8))


def hurt():
    """AND THE ONE FOR TAKING A BLOW: shorter, higher, cut off."""
    n = secs(0.36)
    air = mul(noise(431, n), env(n, 0.004, 0.16, 3.0))
    voiced = mix(n, (ring(air, 780.0, 14.0), 1.0),
                    (ring(air, 1460.0, 10.0), 0.5),
                    (ring(air, 196.0, 8.0), 0.40))
    return mul(voiced, env(n, 0.006, 0.20, 2.6))


# ---------------------------------------------------------------------------
# AND THE REST OF WHAT A BODY DOES. Second pass: the verbs left over that are
# a physical act rather than a menu. Trade, banking and following stay silent
# on purpose -- the window's own note says banking makes no sound worth
# hearing, and it is right.

def horn():
    """THE HORN IN THE OFF HAND. §6bv, and the loudest thing a citizen owns.

    It asks for nothing but the shield you are not wearing, and it is heard
    across a valley, so it carries further than anything else here: a slow
    swell rather than a blast, on a harmonic series rather than one note,
    because a single resonator sounds like a bottle.
    """
    n = secs(1.9)
    breathin = mul(noise(441, n), env(n, 0.09, 1.30, 1.15))
    parts = [(146.0, 1.0), (292.0, 0.62), (438.0, 0.34), (584.0, 0.18), (876.0, 0.09)]
    out = mix(n, *[(ring(breathin, hz, 120.0), g) for hz, g in parts])
    # the air that does not become a note, which is what makes it blown
    air = mul(lowpass(noise(442, n), 1600.0, 2), env(n, 0.07, 1.10, 1.3))
    return mix(n, (out, 1.0), (air, 0.18))


def clatter():
    """SOMETHING PUT DOWN, OR DROPPED. Small, dry, over at once."""
    n = secs(0.4)
    fall = mul(noise(451, n), env(n, 0.001, 0.03, 5.5))
    return mix(n, (ring(fall, 430.0, 20.0), 1.0),
                  (ring(fall, 1140.0, 26.0), 0.4),
                  (mul(lowpass(noise(452, n), 800.0, 2), env(n, 0.002, 0.10, 3.5)), 0.45))


def sheathe():
    """TAKING SOMETHING UP OR PUTTING IT AWAY: leather, then a little steel."""
    n = secs(0.55)
    slide = mul(highpass(noise(461, n), 1400.0), env(n, 0.02, 0.22, 2.2))
    at = secs(0.20)
    span = n - at
    seat = mul(noise(462, span), env(span, 0.001, 0.03, 5.0))
    metal = mix(span, (ring(seat, 1680.0, 48.0), 1.0), (ring(seat, 620.0, 22.0), 0.5))
    out = mix(n, (slide, 0.75))
    for i in range(span):
        out[at + i] += metal[i] * 0.45
    return out


def nockup():
    """A SHAFT ON THE STRING: wood on wood, then the string taking it."""
    n = secs(0.35)
    seat = mul(noise(471, n), env(n, 0.0008, 0.02, 5.0))
    return mix(n, (ring(seat, 880.0, 30.0), 0.7),
                  (ring(seat, 2200.0, 40.0), 0.45),
                  (mul(highpass(noise(472, n), 2000.0), env(n, 0.004, 0.09, 3.0)), 0.35))


def page():
    """CHANGING THE BOOK YOU SPEAK FROM. A leaf turned, and nothing else."""
    n = secs(0.5)
    turn_ = mul(highpass(noise(481, n), 2200.0), env(n, 0.03, 0.22, 1.9))
    settle = mul(lowpass(noise(482, n), 900.0, 2), env(n, 0.10, 0.18, 2.4))
    return mix(n, (turn_, 1.0), (settle, 0.30))


def hull():
    """THE CROSSING: water along a boat, and the oar in it."""
    n = secs(1.5)
    wash = mul(lowpass(noise(491, n), 1200.0, 2), env(n, 0.18, 1.10, 1.2))
    at = secs(0.45)
    span = n - at
    pull_ = mul(lowpass(noise(492, span), 700.0, 2), env(span, 0.08, 0.45, 1.5))
    creak = ring(mul(noise(493, span), env(span, 0.02, 0.30, 2.5)), 310.0, 20.0)
    out = mix(n, (wash, 1.0))
    for i in range(span):
        out[at + i] += pull_[i] * 0.45 + creak[i] * 0.22
    return out


def oath():
    """SWEARING A CALLING: the one thing a citizen does once and cannot undo.

    So it is the only sound in this file that RESOLVES rather than stopping: a
    low note and a fifth above it, arriving together and held. Nothing struck,
    nothing bright. It should feel like a decision rather than an event.
    """
    n = secs(1.7)
    hit = mul(noise(501, n), env(n, 0.05, 1.20, 1.1))
    return mix(n, (ring(hit, 131.0, 90.0), 1.0),
                  (ring(hit, 196.0, 85.0), 0.70),
                  (ring(hit, 262.0, 80.0), 0.40),
                  (mul(lowpass(noise(502, n), 900.0, 2), env(n, 0.10, 0.95, 1.3)), 0.16))


# ---------------------------------------------------------------------------
# THE THIRD PASS: WHAT A CITIZEN DOES WITH GOODS, MONEY AND A WORKSHOP.
#
# These were silent for a reason nothing in this file could have fixed. The
# window keys a noise off the world's `deed`, the world recorded thirty-two
# verbs, and everything a citizen does at a market stall, a furnace, a sawpit,
# a brewpot or a bank was not among them. The engine records them now, so they
# can be heard; this is what they sound like.
#
# NO TWO WORKSHOPS SHARE A NOISE. A citizen standing in a town hears a sawpit,
# a furnace and a quern going at once, and if two of them are the same burst of
# filtered noise the town has one texture instead of three. The three are
# separated by WHERE THE ENERGY IS: the saw is a repeated stroke with nothing
# below 300Hz, the furnace is a continuous rush with nothing above 2kHz, and
# the quern (already written) is the grind between them.

def coin():
    """MONEY CHANGING HANDS. Several small pieces, dry, into a palm.

    Not one coin: a count. Six strikes inside a third of a second at slightly
    different pitches, which is what a handful sounds like and is also the
    only way to tell this from a key being dropped. The tails are left to
    overlap on purpose -- coins land on each other, not in silence.
    """
    n = secs(0.55)
    out = [0.0] * n
    for k in range(6):
        at = secs(0.012 + k * 0.038 + (k % 3) * 0.009)
        span = n - at
        if span <= 0:
            continue
        tap = mul(noise(510 + k, span), env(span, 0.0004, 0.004, 7.0))
        bit = mix(span, (ring(tap, 3100.0 + k * 215.0, 90.0), 1.0),
                        (ring(tap, 5200.0 + k * 170.0, 70.0), 0.45),
                        (ring(tap, 1400.0, 30.0), 0.22))
        gain = 1.0 - k * 0.11
        for i in range(span):
            out[at + i] += bit[i] * gain
    # the purse itself, under all of it
    cloth = mul(highpass(noise(519, n), 2600.0), env(n, 0.02, 0.26, 2.0))
    return mix(n, (out, 1.0), (cloth, 0.14))


def sack():
    """A LOAD OF GOODS SHIFTED: canvas, then the contents settling.

    The commonest of the new ones -- consigning, delivering, hauling,
    unloading, stocking a shelf and taking fish off a rack all use it -- so it
    is deliberately the plainest thing here. A soft body with a short rustle
    on the front and no note anywhere in it: a sack that rang would be a bell
    in a sack.
    """
    n = secs(0.6)
    weave = mul(highpass(noise(521, n), 1800.0), env(n, 0.008, 0.18, 2.4))
    body = mul(lowpass(noise(522, n), 420.0, 3), env(n, 0.004, 0.22, 3.0))
    at = secs(0.13)
    span = n - at
    settle = mul(lowpass(noise(523, span), 1100.0, 2), env(span, 0.02, 0.30, 2.2))
    out = mix(n, (weave, 0.55), (body, 1.0))
    for i in range(span):
        out[at + i] += settle[i] * 0.30
    return out


def build():
    """TIMBER RAISED: a mallet on a peg, three times, and the frame taking it.

    Raising a stall, building a brewpot and laying the first plank of a wild
    span are the same act with different timber in it, so they share this.
    Three blows rather than one, because nobody drives a peg home in one, and
    the third is softer: it is the one that seats it.
    """
    n = secs(1.25)
    out = [0.0] * n
    for k, (at, gain) in enumerate(((0.00, 1.0), (0.33, 0.95), (0.66, 0.6))):
        a = secs(at)
        span = n - a
        hit = mul(noise(531 + k, span), env(span, 0.0008, 0.016, 5.5))
        peg = mix(span, (ring(hit, 310.0, 11.0), 1.0),
                        (ring(hit, 148.0, 8.0), 0.65),
                        (ring(hit, 940.0, 16.0), 0.30))
        knock = mul(lowpass(noise(534 + k, span), 1500.0, 2), env(span, 0.001, 0.07, 4.0))
        for i in range(span):
            out[a + i] += peg[i] * gain + knock[i] * 0.35 * gain
    return out


def unbuild():
    """THE SAME FRAME COMING APART. Named this way because `break` is a
    keyword, and `dismantle` is the verb rather than the noise.

    A nail drawn is the one sound in this file with a RISING pitch in it, and
    that is the whole character of it: wood letting go of iron squeals upward
    as the nail comes out. Then the board drops.
    """
    n = secs(1.1)
    squeal = sweep(541, secs(0.45), 430.0, 1150.0, q=38.0, steps=18)
    out = mix(n, ([squeal[i] if i < len(squeal) else 0.0 for i in range(n)], 0.55))
    at = secs(0.46)
    span = n - at
    drop = mul(noise(542, span), env(span, 0.0008, 0.020, 5.0))
    board = mix(span, (ring(drop, 196.0, 9.0), 1.0), (ring(drop, 285.0, 7.0), 0.5),
                      (mul(lowpass(noise(543, span), 900.0, 2),
                           env(span, 0.002, 0.14, 3.2)), 0.5))
    for i in range(span):
        out[at + i] += board[i] * 0.9
    return out


def sawing():
    """A SAW THROUGH A LOG: four strokes, and the cut getting easier.

    A saw is the clearest rhythm in a town and the thing that makes a sawpit
    identifiable from across a street, so it keeps a real stroke pattern
    rather than being one burst. Nothing below 300Hz: that is the band the
    furnace owns, and a town where the two overlap is mud.
    """
    n = secs(1.6)
    out = [0.0] * n
    for k in range(4):
        at = secs(0.04 + k * 0.38)
        span = min(secs(0.34), n - at)
        if span <= 0:
            continue
        # the stroke itself: broadband, shaped like a push rather than a hit
        rasp_ = mul(highpass(noise(551 + k, span), 900.0), env(span, 0.05, 0.16, 1.4))
        teeth = mix(span, (ring(rasp_, 1750.0, 12.0), 0.55),
                          (ring(rasp_, 2600.0, 9.0), 0.35))
        for i in range(span):
            out[at + i] += (rasp_[i] * 0.8 + teeth[i]) * (1.0 - k * 0.07)
    return out


def furnace():
    """ORE IN A FURNACE: a rush of air, and the charge going in.

    The opposite shape to the saw. No stroke, no edge, nothing bright: a long
    low roar that swells and falls away, with the clatter of the charge at the
    front. It is the loudest low thing in a town and it should be audible
    through everything else without competing with any of it.
    """
    n = secs(2.0)
    roar = mul(lowpass(noise(561, n), 520.0, 3), env(n, 0.35, 1.35, 1.1))
    # the draught, a fifth of the way up and much quieter, so it is a fire and
    # not a landslide
    draught = mul(lowpass(highpass(noise(562, n), 300.0), 1700.0, 2),
                  env(n, 0.30, 1.20, 1.2))
    charge = mul(noise(563, n), env(n, 0.001, 0.05, 4.5))
    ore = mix(n, (ring(charge, 1180.0, 24.0), 1.0), (ring(charge, 680.0, 16.0), 0.6))
    return mix(n, (roar, 1.0), (draught, 0.30), (ore, 0.40))


def feed():
    """A LOG ONTO A LIT FIRE. The thump, and then the fire answering.

    Distinct from `kindle`, which is a fire being STARTED and is all strike
    and catch. This is a fire that is already going being given something: a
    dull knock, a shower of sparks, and the flame coming up for a second.
    """
    n = secs(1.3)
    knock = mul(noise(571, n), env(n, 0.001, 0.025, 5.0))
    log = mix(n, (ring(knock, 176.0, 8.0), 1.0), (ring(knock, 262.0, 6.0), 0.45))
    at = secs(0.09)
    span = n - at
    flare = mul(lowpass(highpass(noise(572, span), 400.0), 2600.0, 2),
                env(span, 0.10, 0.80, 1.3))
    sparks = mul(highpass(noise(573, span), 4200.0), env(span, 0.04, 0.55, 2.4))
    out = mix(n, (log, 1.0))
    for i in range(span):
        out[at + i] += flare[i] * 0.55 + sparks[i] * 0.16
    return out


def pour():
    """WATER INTO A POT. The only sound here with a note that MOVES.

    A vessel filling raises its pitch as the air column in it shortens, and
    that rise is the entire reason anybody recognises the sound. Without it
    this is a tap running.
    """
    n = secs(1.4)
    stream = mul(lowpass(highpass(noise(581, n), 700.0), 4200.0, 2),
                 env(n, 0.09, 1.05, 1.2))
    vessel = sweep(582, n, 300.0, 720.0, q=26.0, steps=22)
    return mix(n, (stream, 1.0), (vessel, 0.38))


def sizzle():
    """FOOD MEETING HEAT. A hiss that arrives all at once and dies back.

    Cooking already had no noise and it is one of the most common things
    anybody does with a fire. The attack is almost instant, because that is
    what going into a hot pan is, and the tail is long and even.
    """
    n = secs(1.5)
    hiss = mul(highpass(noise(591, n), 2400.0), env(n, 0.008, 1.10, 1.5))
    fat = mul(lowpass(highpass(noise(592, n), 800.0), 3000.0, 2),
              env(n, 0.02, 0.85, 1.6))
    # the one spit that makes it food rather than steam
    at = secs(0.33)
    span = n - at
    spit = mul(highpass(noise(593, span), 5000.0), env(span, 0.0008, 0.05, 5.0))
    out = mix(n, (hiss, 1.0), (fat, 0.45))
    for i in range(span):
        out[at + i] += spit[i] * 0.35
    return out


def sow():
    """A HAND IN SOIL, AND SEED GOING DOWN.

    Nearly the quietest thing in the file, after angling. Planting is done
    kneeling and a loud one would be wrong whatever it was made of. No note:
    soil has none.
    """
    n = secs(0.7)
    dig = mul(lowpass(noise(601, n), 700.0, 3), env(n, 0.02, 0.26, 2.0))
    at = secs(0.26)
    span = n - at
    grain_ = mul(highpass(noise(602, span), 3400.0), env(span, 0.004, 0.16, 3.2))
    out = mix(n, (dig, 1.0))
    for i in range(span):
        out[at + i] += grain_[i] * 0.30
    return out


def wicker():
    """AN EEL BUCK PUSHED UNDER. Woven withies, then water closing over it.

    The withies are a creak, not a crack: a buck is green wood bent, and it
    complains rather than breaking. The water is the same family as the
    angler's plop, deliberately, because they are the same river.
    """
    n = secs(1.2)
    creak = ring(mul(noise(611, n), env(n, 0.04, 0.40, 1.8)), 420.0, 26.0)
    withy = mul(highpass(noise(612, n), 1600.0), env(n, 0.05, 0.30, 2.0))
    at = secs(0.34)
    span = n - at
    under = mul(lowpass(noise(613, span), 1300.0, 2), env(span, 0.03, 0.55, 1.5))
    swirl = mul(lowpass(noise(614, span), 600.0, 2), env(span, 0.12, 0.60, 1.3))
    out = mix(n, (creak, 0.8), (withy, 0.35))
    for i in range(span):
        out[at + i] += under[i] * 0.55 + swirl[i] * 0.30
    return out


def stake():
    """A SURVEYOR'S MARK: a stake driven into ground, twice.

    Surveying pays in distance walked, so it is the sound a citizen makes at
    the far end of a long journey, and it wants to feel like arriving. Lower
    and heavier than the builder's mallet, into earth rather than into timber,
    so there is almost no ring on it at all.
    """
    n = secs(0.95)
    out = [0.0] * n
    for k, (at, gain) in enumerate(((0.0, 1.0), (0.30, 0.8))):
        a = secs(at)
        span = n - a
        drive = mul(noise(621 + k, span), env(span, 0.0010, 0.022, 5.0))
        wood = mix(span, (ring(drive, 240.0, 7.0), 1.0), (ring(drive, 390.0, 5.0), 0.4))
        earth = mul(lowpass(noise(623 + k, span), 380.0, 3), env(span, 0.002, 0.14, 3.0))
        for i in range(span):
            out[a + i] += (wood[i] * 0.8 + earth[i] * 0.7) * gain
    return out


def quill():
    """DRAWING UP A CHARTER. A nib on paper, and nothing else.

    Distinct from `page`, which is a leaf TURNED. This is writing: short
    strokes with gaps between them, all of it high and dry, and it is the
    smallest sound in the file because one citizen in a world ever draws the
    first charter.
    """
    n = secs(1.35)
    out = [0.0] * n
    for k, (at, length) in enumerate(((0.02, 0.17), (0.26, 0.12), (0.46, 0.21),
                                      (0.78, 0.10), (0.98, 0.15))):
        a, span = secs(at), secs(length)
        if a + span > n:
            span = n - a
        stroke = mul(highpass(noise(631 + k, span), 3600.0), env(span, 0.01, length * 0.8, 1.6))
        for i in range(span):
            out[a + i] += stroke[i] * (0.9 - k * 0.07)
    return out


def graze():
    """FORAGE, TAKEN OFF THE GROUND AND EATEN WHERE IT LIES.

    It is two acts in one interval, so it is two sounds in one file: the stalk
    giving way, and then the bite, about a fifth of a second behind it. Neither
    `pull` nor `eat` on its own is right, because the whole character of forage
    is that it never gets as far as the pack. A citizen stooping to eat in the
    middle of a fight should not sound like somebody pocketing a log.
    """
    n = secs(0.95)
    tear = mul(highpass(noise(651, n), 1500.0), env(n, 0.006, 0.18, 2.6))
    soil = mul(lowpass(noise(652, n), 500.0, 2), env(n, 0.01, 0.14, 2.0))
    out = mix(n, (tear, 0.9), (soil, 0.30))
    at = secs(0.22)
    span = n - at
    # the bite: soft, wet and low, with nothing bright in it
    bite = mul(lowpass(noise(653, span), 900.0, 2), env(span, 0.004, 0.09, 3.6))
    jaw = ring(mul(noise(654, span), env(span, 0.002, 0.05, 4.5)), 240.0, 10.0)
    chew = mul(lowpass(noise(655, span), 1300.0, 2), env(span, 0.16, 0.34, 1.8))
    for i in range(span):
        out[at + i] += bite[i] * 0.85 + jaw[i] * 0.30 + chew[i] * 0.22
    return out


def chime():
    """DEDICATING A STONE. One struck note, allowed to ring out.

    A dedication is a citizen putting their name on something permanent and
    paying for the privilege, and it is the only act in this group that is
    meant to be ceremonial. So: struck stone, a long tail, and a fifth above
    it that arrives a moment late -- which is what a big stone does and what
    stops it sounding like a triangle.
    """
    n = secs(2.2)
    out = mix(n, (tone(641, n, 174.0, 150.0, 0.004, 1.70, 1.15), 1.0),
                 (tone(642, n, 523.0, 110.0, 0.006, 1.10, 1.35), 0.22))
    at = secs(0.11)
    span = n - at
    fifth = tone(643, span, 261.0, 140.0, 0.010, 1.50, 1.20)
    for i in range(span):
        out[at + i] += fifth[i] * 0.52
    return out



def felled():
    """A CITIZEN GOING DOWN. The fall, and one low note under it.

    This is the only sound in the window for something that happens TO a
    citizen and cannot be taken back inside the interval, so it is built to be
    unmistakable rather than informative: weight meeting the ground, and a deep
    struck note with a long tail, in a register nothing else here occupies.

    Deliberately NOT a cry. About half of all blows already carry the worker's
    own voice, so a scream laid on top of those reads as a fight going badly
    rather than as an ending. It also has to work for somebody ELSE's death
    across a street, where a shriek would be alarming and a low note is a
    fact.

    Long, at two and a half seconds against a tenth for a footfall, because
    the world holds its breath for five intervals here and the sound should
    still be going when a player looks up to see what happened.
    """
    n = secs(2.5)
    # The fall: broad and soft, with no timber in it. Cloth and weight.
    drop = mul(lowpass(noise(901, n), 520.0, 2), env(n, 0.004, 0.24, 4.2))
    body = mix(n, (ring(drop, 94.0, 5.0), 1.0), (ring(drop, 139.0, 4.0), 0.45))
    # And the note, a moment after the body lands, so the two read as cause
    # and consequence rather than as one event.
    at = secs(0.12)
    span = n - at
    low = tone(902, span, 87.0, 190.0, 0.006, 2.00, 1.10)
    out = mix(n, (body, 1.0))
    for i in range(span):
        out[at + i] += low[i] * 0.80
    return out


# ---- THE VOICE, LAID UNDER A BLOW ----
#
# The window picks ONE sound at random from a row's list
# (IntervalCitizens::Footfall), so a grunt cannot be layered by adding it as a
# second entry: it would sometimes play INSTEAD of the axe. And a grunt on
# every single swing is worse than none, because the repeat is the thing you
# end up hearing.
#
# So the voice is baked into a SECOND VARIANT of the blow, and both variants
# go in the row. About half the swings carry a voice and half do not, which is
# what a person working actually sounds like, and it needs nothing from the
# C++ that the footfalls did not already need.
def voiced(make, gain=0.55, at=0.02):
    """The blow with a breath under it, starting fractionally after the hit."""
    blow = make()
    n = len(blow)
    out = list(blow)
    start = secs(at)
    breath_ = effort()
    for i in range(min(len(breath_), n - start)):
        out[start + i] += breath_[i] * gain
    return out


# The ones a citizen is visibly putting their back into. Angling and whittling
# are not on it: nobody grunts casting a line.
VOICED = ('chop', 'mine', 'strike', 'thud', 'grind')


# Which weapon does which. The world owns this table; it is repeated here only
# so the wav files can be named, and `audit_motion.py` reads the real engine
# and says so if the two have drifted.
GAMBITS = {
    'quick-dagger': flurry, 'horn-bow': flurry,
    'quick-mell': whole, 'great-mell': whole,
    'fire-siphon': now, 'dragonbow': far, 'handgonne': report,
}
# The same table as names, which is what `apply.py` wants: it needs the name of
# the wav, not the function that made it, and reaching for `__name__` at the
# call site reads like a trick.
GAMBIT_KIND = {weapon: make.__name__ for weapon, make in GAMBITS.items()}

# ---- WHAT IS IN THE HAND DECIDES WHAT THE WORK SOUNDS LIKE ----
#
# The window refines a deed's sound by the held item before falling back to the
# plain verb (IntervalCitizens.cpp), which is the same path the gambits take.
# So one row per TOOL, not per tree: `gather.iron-hatchet` is an axe in wood
# whatever is being felled, and a citizen with nothing in their hands falls
# through to `gather` and pulls the thing up instead.
#
# This lives here, beside the synths, for the same reason GAMBIT_KIND does:
# `apply.py` runs inside the editor and cannot load engine.js. The item names
# are the engine's, and `audit_items.py` reads the real registry, so a tool
# renamed out from under this is reported rather than silently losing its noise.
_HATCHETS = ('iron-hatchet', 'steel-hatchet', 'quick-hatchet', 'great-hatchet')
_PICKS = ('iron-pickaxe', 'steel-pickaxe', 'quick-pickaxe', 'great-pickaxe')
_RODS = ('rod', 'oak-rod', 'ironbark-rod', 'heartwood-rod')
_BLADES = ('iron-dagger', 'steel-dagger', 'quick-dagger',
           'iron-sword', 'steel-sword', 'quick-sword', 'great-sword',
           'bone-spear', 'iron-spear', 'steel-spear', 'quick-spear')
_BOWS = ('wooden-bow', 'horn-bow', 'heartwood-bow', 'sigil-bow', 'dragonbow',
         'crossbow', 'great-crossbow')
_BLUNT = ('iron-mell', 'steel-mell', 'quick-mell', 'great-mell', 'quick-flail')

# verb -> {held item or None for the fallback: the wav's kind}
WORK_SOUNDS = {
    'gather': dict([(None, 'pull')]
                   + [(t, 'chop') for t in _HATCHETS]
                   + [(t, 'mine') for t in _PICKS]
                   + [(t, 'angle') for t in _RODS]),
    'attack': dict([(None, 'thud')]
                   + [(w, 'strike') for w in _BLADES]
                   + [(w, 'strike') for w in _BLUNT]
                   + [(w, 'loose') for w in _BOWS]),
    # bare hands, always: `attackp` is a citizen hitting a citizen, and the
    # engine gives it no weapon row of its own
    'attackp': {None: 'thud'},
    # the crafts that were silent beside the anvil that was not
    'fletch': {None: 'whittle'},
    'grind': {None: 'grind'},
    'char': {None: 'char'},
    'kindle': {None: 'kindle'},
    'light': {None: 'kindle'},
    'lay': {None: 'pull'},
    'pickup': {None: 'pull'},
    'lift': {None: 'pull'},
    # the second pass: physical acts, not menus. Trade, banking and following
    # stay silent on purpose.
    'sound': {None: 'horn'},        # §6bv: the horn in the off hand
    'drop': {None: 'clatter'},
    'wield': {None: 'sheathe'},
    'unwield': {None: 'sheathe'},
    'nock': {None: 'nockup'},
    'turn': {None: 'page'},         # §7ce: changing the book you speak from
    'sail': {None: 'hull'},         # §7bu: the crossing, where a boat waits
    'swear': {None: 'oath'},
    'grave': {None: 'bury'},        # §7do: grave goods, behind a squeeze
    'rifle': {None: 'pull'},
    # §6bq: `stamp` was here and is not a verb the world has. So was `anchor`,
    # for a spell the constitution repealed, and `mend` was keyed on the spell
    # rather than on `cast`, which is the word the world actually writes down.

    # ---- AND THE THIRD PASS: GOODS, MONEY AND THE WORKSHOPS ----
    #
    # Every one of these was silent until the engine began recording the deed,
    # so none is a replacement for a noise that was wrong: they are the first
    # sound these verbs have ever had.
    'cast': {None: 'mend'},         # the one spell cast by that name; the rest are their own verbs

    # money: six verbs, one noise, a count of coins out of a purse
    'buy': {None: 'coin'},
    'pay': {None: 'coin'},          # §14: the toll at a wild span
    'deposit': {None: 'coin'},
    'deposit_all': {None: 'coin'},
    'withdraw': {None: 'coin'},
    'take_market': {None: 'coin'},

    # and goods moved in bulk, which is the commonest of the three
    'consign': {None: 'sack'},
    'deliver': {None: 'sack'},
    'haul': {None: 'sack'},
    'unload': {None: 'sack'},
    'collect': {None: 'sack'},
    'stock_market': {None: 'sack'},
    'harvest': {None: 'pull'},      # a crop coming up is a stalk giving way

    # timber: raised, and taken down again
    'build_brewpot': {None: 'build'},
    'raise': {None: 'build'},       # an ACTION, so it is heard once an interval while it runs
    'found': {None: 'build'},
    'dismantle': {None: 'unbuild'},
    'dismantle_market': {None: 'unbuild'},

    # the workshops, each in its own band so a town has three textures
    'saw': {None: 'sawing'},
    'smelt': {None: 'furnace'},
    # §6c: NOT A DEED, AND IT STILL NEEDS A ROW. `felled` is this window's own
    # word: the world reports hit points and never announces a death, so
    # nothing in `deed` or `action` will ever carry it. The citizens actor
    # speaks it when it sees health at nothing, exactly once, the same way it
    # already chooses the falling MOTION. See AIntervalCitizens::UpdatePeople.
    'felled': {None: 'felled'},
    'stoke': {None: 'feed'},
    'brew': {None: 'pour'},
    'cook': {None: 'sizzle'},

    # and the rest of what a body does out of doors
    'plant': {None: 'sow'},
    'sapling': {None: 'sow'},
    'setbuck': {None: 'wicker'},
    'survey': {None: 'stake'},
    'charter': {None: 'quill'},
    'dedicate': {None: 'chime'},
    'forage': {None: 'graze'},      # §6ba: the one deed the world names for itself
    'offer': {None: 'chime'},       # §6: goods given up at an ossuary, which is the same ceremony
    'release': {None: 'sack'},      # a consignment coming home into the pack
    'accept_trade': {None: 'sack'}, # and goods crossing between two people
    'stint': {None: 'oath'},        # §7dv: an oath, like swearing a calling
}

# The voice is not a row of its own: see VOICED above, which bakes it into a
# second variant of the blow so the window's pick-one cannot play it alone.

DEEDS = {
    # the common book
    'still': (still, 0.085), 'seal': (seal, 0.090), 'transmute': (transmute, 0.070),
    'unmake': (unmake, 0.075), 'mend': (mend, 0.070), 'mendp': (mendp, 0.072),
    'invoke': (invoke, 0.078),
    # the barrow book
    'rot': (rot, 0.088), 'taking': (taking, 0.078),
    'waking': (waking, 0.086), 'withering': (withering, 0.082),
    # and the everyday ones
    'bury': (bury, 0.080), 'smith': (smith, 0.082),
    'drink': (drink, 0.070), 'eat': (eat, 0.066),
    # THE WORK, which was the largest silence: gathering is the commonest
    # thing anybody does and it made no noise at all. These are chosen by what
    # is in the hand, so one row here serves every axe in the world.
    'chop': (chop, 0.092), 'mine': (mine, 0.090), 'angle': (angle, 0.062),
    'pull': (pull, 0.060),
    # and combat, where only the gambits could be heard
    'strike': (strike, 0.088), 'thud': (thud, 0.084), 'loose': (loose, 0.078),
    # the rest of the crafts
    'kindle': (kindle, 0.074), 'char': (char, 0.066),
    'whittle': (whittle, 0.064), 'grind': (grind, 0.070),
    # the citizen's own voice, laid UNDER a blow rather than instead of it
    'effort': (effort, 0.052), 'hurt': (hurt, 0.056),
    # and the rest of what a body does
    'horn': (horn, 0.105), 'clatter': (clatter, 0.070), 'sheathe': (sheathe, 0.062),
    'nockup': (nockup, 0.058), 'page': (page, 0.050), 'hull': (hull, 0.068),
    'oath': (oath, 0.080),
    # and the third pass: goods, money and the workshops
    'coin': (coin, 0.078), 'sack': (sack, 0.062), 'build': (build, 0.086),
    'unbuild': (unbuild, 0.076), 'sawing': (sawing, 0.070),
    'furnace': (furnace, 0.072), 'feed': (feed, 0.074), 'pour': (pour, 0.060),
    'sizzle': (sizzle, 0.058), 'sow': (sow, 0.050), 'wicker': (wicker, 0.058),
    'stake': (stake, 0.082), 'quill': (quill, 0.044), 'chime': (chime, 0.088),
    'graze': (graze, 0.056),
    # and the one thing that is not work at all
    'felled': (felled, 0.095),
}


if __name__ == '__main__':
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for name, (make, level) in sorted(DEEDS.items()):
        write(os.path.join(out, 'deed-%s.wav' % name), make(), rms=level)
    # the second variant of the heavy work, with the citizen's own voice in it
    for name in VOICED:
        make, level = DEEDS[name]
        write(os.path.join(out, 'deed-%s-v.wav' % name),
              voiced(make), rms=DEEDS[name][1])
    # One file per KIND, not per weapon: three weapons share the flurry and
    # two share the whole-body blow, and three copies of one sound is three
    # things to keep in step.
    for kind, make in (('flurry', flurry), ('whole', whole), ('now', now),
                       ('far', far), ('report', report)):
        write(os.path.join(out, 'gambit-%s.wav' % kind), make(), rms=0.090)
    print('%d deed sounds (%d with a voiced twin) and 5 gambits: %s'
          % (len(DEEDS), len(VOICED), ', '.join(sorted(DEEDS))))
