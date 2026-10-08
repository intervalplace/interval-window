// SMOKE, DRAWN RATHER THAN TEXTURED.
//
// The obvious way to put smoke over a hearth is a soft grey circle on a
// sprite sheet. The obvious way is also the one that gives the trick away
// from directly above, which is the only angle this window ever looks from: a
// column of identical circles rising in a line reads as a stack of coins.
// What makes smoke read as smoke is that every puff has a DIFFERENT RAGGED
// EDGE and that the edge keeps moving while the puff climbs.
//
// So there is no texture here at all. The puff is a disc with value noise
// eaten into it, the noise is offset by the particle's own random number so no
// two puffs share a silhouette, and the offset creeps with the particle's age
// so the silhouette boils. Three octaves is enough at the size a chimney is on
// screen, and it costs less than the bandwidth of the sheet it replaces.
//
// IT IS LIT, not emissive. A hearth's smoke at noon is a pale grey thing the
// sun shines through and at dusk it is an orange-lit thing over a roof; a flat
// grey circle is neither. The material is translucent with a volumetric
// lighting mode, so the sun and the hearth's own point light both reach it for
// about the cost of a vertex.

float2 P = UV - 0.5;
float  R = saturate(length(P) * 2.0);

// THE NOISE, THREE OCTAVES, BOILING.
//
// `Seed` is the particle's own random number, so two puffs leaving the same
// chimney a second apart are not the same shape. `Age` creeps the field so one
// puff's edge churns as it climbs rather than holding one frozen outline all
// the way up -- a frozen outline is what makes a rising sprite look like a
// rising sprite.
float2 Q = UV * 2.6 + float2(Seed * 37.13, Seed * 17.77 - Age * 0.62 - T * 0.04);
float  N = 0.0;
float  A = 0.5;
for (int o = 0; o < 3; ++o)
{
	float2 I = floor(Q);
	float2 F = frac(Q);
	F = F * F * (3.0 - 2.0 * F);
	float a = frac(sin(dot(I + float2(0.0, 0.0), float2(127.1, 311.7))) * 43758.5453);
	float b = frac(sin(dot(I + float2(1.0, 0.0), float2(127.1, 311.7))) * 43758.5453);
	float c = frac(sin(dot(I + float2(0.0, 1.0), float2(127.1, 311.7))) * 43758.5453);
	float d = frac(sin(dot(I + float2(1.0, 1.0), float2(127.1, 311.7))) * 43758.5453);
	N += A * lerp(lerp(a, b, F.x), lerp(c, d, F.x), F.y);
	A *= 0.5;
	Q *= 2.03;
}
N /= 0.875;

// THE PUFF. A disc, bitten into by the noise, with a soft shoulder so the
// edge is smoke and not a paper cut-out.
float Mask = saturate((1.0 - R) * 1.40 - (1.0 - N) * 0.88);
Mask = smoothstep(0.0, 0.40, Mask);

// DISPERSING, NOT FADING.
//
// Multiplying the whole puff by (1 - Age) fades it like a dimmer and looks
// like one. Smoke goes away by getting THINNER AT THE EDGE first, so the
// erosion is subtracted from the mask before the shoulder rather than
// multiplied after it -- an old puff is a smaller, rattier puff, not a
// ghostly full-sized one.
Mask = saturate(Mask - Age * Age * 0.55);

// SOFT WHERE IT MEETS A ROOF.
//
// `Soft` is a depth fade. Without it the sprite's flat quad cuts a visible
// straight line across the thatch it is rising off, which is the single
// loudest tell a particle system has.
Opacity = saturate(Mask * PA * Thin * Soft);

// The colour is the particle's, so a level can have a cook fire's smoke be
// paler than a forge's without another material.
return PC;
