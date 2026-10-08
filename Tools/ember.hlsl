// AN EMBER. A spark off a fire, one sprite, a few pixels across.
//
// Additive, unlit, and deliberately tiny. The point of embers over a hearth is
// not that you can see them; it is that a fire with none is a lamp. They are
// drawn as a hard bright core with a soft halo, because that is what a
// point of light does to a camera and a flat disc does not.

float2 P = UV - 0.5;
float  R = saturate(length(P) * 2.0);
float  Core = saturate(1.0 - R);

// A GUTTER, NOT A FADE. Embers wink: they turn as they rise and present
// different faces. Two periods that share no factor, off the particle's own
// seed, so no two spark together.
float Wink = 0.62 + 0.38 * sin(T * 11.0 + Seed * 62.83)
                  * sin(T * 4.3 + Seed * 21.17);

// A spark dies suddenly at the end of its climb rather than gently.
float Left = saturate(1.0 - pow(Age, 3.0));

float Spark = (pow(Core, 4.0) * 2.4 + pow(Core, 1.6) * 0.30) * Wink * Left;

Opacity = saturate(Spark * PA);

// Additive: what is returned IS what lands on the frame, so the colour has to
// carry the brightness. The core is hotter than the halo.
return PC * Spark * PA;
