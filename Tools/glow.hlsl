// A GLOW-WORM.
//
// Lampyris noctiluca does not flash like the American firefly: the female
// sits in the grass and shines steadily for an hour or two, brightening and
// fading over many seconds. So this breathes rather than blinks, and each one
// breathes at its own rate -- `Which` is that worm's own number, arriving as
// per-instance data, and the only thing that distinguishes it from the one in
// the next tuft.
//
// Cold green, which is what the light actually is, and only at night: the
// `Night` scalar is one minus how much daylight the world says there is, so
// they come up at dusk and are gone by dawn without anything deciding when
// dusk is.

float Slow = Time * (0.19 + Which * 0.26) + Which * 31.0;
float Breath = 0.34 + 0.66 * (0.5 + 0.5 * sin(Slow * 6.2831));

// A few sit dark for a while, as they do.
float Awake = step(0.12, frac(Which * 17.3 + floor(Slow * 0.5) * 0.41));

float Lit = Breath * Awake * saturate(Night);
return float3(0.40, 1.00, 0.44) * Lit * 0.85;
