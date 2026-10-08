// RAIN, ON A CYLINDER THAT RIDES WITH THE CITIZEN.
//
// Rain drawn where the weather is rather than where somebody is costs a
// hundred times as much and looks identical from inside it. This is one
// cylinder centred on whoever is standing in it, with streaks falling down
// the inside of it.
//
// IT HAS TO BE BIGGER THAN THE VIEW. At fourteen metres across you could see
// where the rain stopped: from a camera a few metres off the citizen's
// shoulder the far wall of the cylinder was a clean vertical line with a dry
// village behind it, which reads as a rain machine following one person
// around. Everything below that is written in terms of `Radius` so the
// cylinder can be as wide as it needs to be without the streaks growing with
// it -- a column is an ANGLE, and the same angle at three times the radius is
// three times the width of wall.
//
// FROM WORLD POSITION, NOT FROM THE MESH'S UVs. The first version banded the
// streaks by the cylinder's own texture coordinates and drew nothing at all:
// the engine's cylinder lays its side into a corner of the sheet, so the
// coordinate that was supposed to run from the ground to the sky barely moved
// and every streak fell outside the part of the cycle that is lit. World
// position has no such opinion, and it has the better property anyway -- the
// rain stands still in the world while the citizen walks through it.
//
// How hard it rains is the WORLD'S number, arithmetic on the interval count,
// the same for everybody. Which drop falls where is this window's own dice,
// like the dither on the thatch, and nothing is decided by it.

// THE COLUMN IS AN ANGLE, NOT A GRID SQUARE.
//
// Quantising world x and y into cells looked reasonable and drew CONFETTI:
// this is a cylinder, so a cell sixteen centimetres across is sixteen
// centimetres of curved wall, and a drop that fills it is a white brick a
// hand's breadth wide hanging at fourteen metres. What makes a streak a
// streak is that it is thin the way round and long the way down, and the way
// round a cylinder is the angle.
float2 Flat = W.xy - Foot.xy;
float  Ang  = atan2(Flat.y, Flat.x);

// ANGULAR, AND DELIBERATELY NOT SCALED BY RADIUS.
//
// Widening the drum, I first made the column count grow with it so a column
// stayed four centimetres of wall whatever the size -- which is exactly
// backwards and drew NOTHING at all. A streak is seen, not measured: four
// centimetres at fourteen metres is a few pixels wide, and the same four
// centimetres at forty-five metres is a third of that and falls below one
// pixel, where it averages into a faint grey wash. Fixed ANGLE is fixed
// apparent width, so a distant streak is correctly wider in the world.
float Fine  = Ang * 320.0;              // about two thousand columns around
float Col   = floor(Fine);
float Seed  = frac(sin(Col * 12.9898) * 43758.5453);

// Thin within the column: most of each one is empty air.
float Thin = 1.0 - smoothstep(0.10, 0.30, abs(frac(Fine) - 0.5));

// Centimetres a second, and a streak every metre and a half -- BOTH scaled
// with the drum, for the same reason the columns are not. Length and speed
// are seen at a distance too, so a curtain three times as far away needs
// streaks three times as long falling three times as fast to look the same.
float Grow  = Radius / 1400.0;
float Fall  = (620.0 + Seed * 320.0) * Grow;
float V     = (W.z + Time * Fall) / (150.0 * Grow);
float Along = frac(V + Seed);

// Long the way down, with a head and a tail.
float Dash = smoothstep(0.0, 0.03, Along) * (1.0 - smoothstep(0.10, 0.62, Along));

// Only some columns carry a drop at a time, and heavier rain means more of
// them do. That is the only thing `Rain` changes: a drop falls at the same
// speed in a shower as in a downpour, because it does.
float Busy = step(1.0 - saturate(Rain) * 0.78, frac(Seed * 7.31 + floor(V) * 0.371));

float A = Dash * Busy * Thin;

// Fade the very top and bottom, which hides the ends of the cylinder.
float Up = (W.z - Foot.z) / (Radius * 0.93);
A *= 1.0 - smoothstep(0.55, 1.0, abs(Up));

// AND FADE THE SILHOUETTE, which is the other place the drum shows.
//
// Looking at the inside of a cylinder, the wall is face-on in the middle of
// the view and edge-on at the sides, and edge-on is exactly where it stops
// being rain and starts being the rim of a barrel. Where the surface turns
// away from the eye there is no honest amount of rain to draw, so draw none:
// the band of streaks then ends in nothing instead of in a line.
// (`Eye`, not `V`: there is already a float V above, counting the fall.)
A *= smoothstep(0.04, 0.40, abs(dot(normalize(N), normalize(Eye))));

// Thinner very close to the eye, so flying the camera up against the wall of
// the drum does not paint the whole screen white.
float Deep = length(W - CamPos) / Radius;
A *= smoothstep(0.0, 0.25, Deep);

Opacity = A * (0.55 + 0.35 * saturate(Rain));

// ONE MID GREY, WHICHEVER WAY THE LIGHT IS.
//
// This was painted bright, to be visible at night, and then vanished in
// daylight -- brighter than a dark scene reads, and against a bright sky a
// bright streak reads as nothing at all. Real rain is neither: it is the same
// grey water in both cases, and what changes is what is behind it. Blended
// over the scene, one mid value darkens a bright sky and lightens a dark
// field, which is exactly what rain does to both.
return float3(0.56, 0.61, 0.72);
