// STANDING WATER, in a basin or a hollow.
//
// Not the sea -- the sea is ground, and the ground material draws it. This is
// the water in things people made or the land collected: a fountain's basin, a
// dew pond, a bog pool, a birdbath.
//
// Three things make water read as water and none of them is blue. It is DARK
// looking straight down and bright at a glancing angle, which is Fresnel and
// is most of it. It is SMOOTH, so what you see in it is the sky. And it MOVES,
// in rings that cross and never repeat.

float2 P = W.xy;

// Rings that cross at angles sharing no period: a grid of sines is a grid.
float T = Time * 0.9;
float R1 = sin(P.x * 0.21 + P.y * 0.13 + T * 2.1);
float R2 = sin(P.x * -0.11 + P.y * 0.26 - T * 1.7 + 1.9);
float R3 = sin(P.x * 0.37 - P.y * 0.31 + T * 3.3 + 0.6);
float Ripple = R1 * 0.5 + R2 * 0.34 + R3 * 0.18;

// The slope of that, which is the normal. Gently -- water in a basin is
// nearly flat, and a strong normal here reads as crumpled foil.
float2 Slope = float2(
    0.21 * cos(P.x * 0.21 + P.y * 0.13 + T * 2.1) * 0.5
  + -0.11 * cos(P.x * -0.11 + P.y * 0.26 - T * 1.7 + 1.9) * 0.34
  + 0.37 * cos(P.x * 0.37 - P.y * 0.31 + T * 3.3 + 0.6) * 0.18,
    0.13 * cos(P.x * 0.21 + P.y * 0.13 + T * 2.1) * 0.5
  + 0.26 * cos(P.x * -0.11 + P.y * 0.26 - T * 1.7 + 1.9) * 0.34
  + -0.31 * cos(P.x * 0.37 - P.y * 0.31 + T * 3.3 + 0.6) * 0.18);

Nrm = normalize(float3(-Slope * 6.0, 1.0));

// Rain pocks the surface: more chop, and the shine goes off it a little.
float Chop = saturate(Rain);
Nrm = normalize(float3(Nrm.xy * (1.0 + Chop * 2.6), 1.0));

Rough = lerp(0.035, 0.22, Chop);
Metal = 0.0;
// Peat water is brown, a fountain's is nearly clear over pale stone. Both are
// dark: water absorbs, and what is not absorbed is the sky bouncing off it.
return float3(0.014, 0.024, 0.030) + 0.010 * Ripple;
