// Thatch. Courses run ALONG the roof, parallel to the eaves -- running them
// down the slope is the commonest way a thatched roof comes out looking like
// corrugated iron.
//
// `House` is the building's own seed, carried in the vertex colour by
// AIntervalChunk: a hash of the building's corner in world tiles, so this roof
// weathers the same way in every window and no two houses in a street alike.

float3 W = P;
float h = saturate(House);

float Deep0  = 26.0 + 9.0 * h;
float Row    = W.z / Deep0;
float Course = frac(Row);
float Lip = 1.0 - smoothstep(0.0, 0.42, Course);

float Comb = frac((W.x + W.y) / 7.0);
float Straw = 0.86 + 0.28 * abs(Comb - 0.5);

// PATCHES THE SIZE OF A REPAIR, not of a hand. At ninety centimetres this
// was a fine speckle that averaged to one flat tone from any distance a roof
// is actually seen at -- which is the whole complaint about the roofs. A
// thatch is renewed a few square metres at a time and the patches read as
// patches.
float Patch = frac(sin(dot(floor(float2(W.x, W.y) / 240.0), float2(19.77, 41.13))) * 28461.7);
// And no two COURSES were cut in the same season either.
float Aged  = frac(sin(floor(Row) * 91.71 + 3.3) * 19273.5);

// A thatch is renewed in patches over decades: one house is fresh straw, its
// neighbour twenty years grey, the damp one on the north side green.
float3 Fresh = float3(0.300, 0.222, 0.108);
float3 Grey  = float3(0.150, 0.140, 0.116);
float3 Moss  = float3(0.086, 0.110, 0.056);

float Age = saturate(h * 1.25);
float3 C = lerp(Fresh, Grey, Age);
C = lerp(C, Moss, saturate((Patch - 0.54) * 2.2) * (0.35 + 0.65 * Age));
C *= Straw;
// The lip of each course is in its own shadow. Deepened from a third: a
// thatched roof is a stack of bundles and the line under each one is the only
// thing at this distance that says so.
C *= 1.0 - 0.46 * Lip;
C *= 0.93 + 0.15 * Aged;
C *= 0.92 + 0.20 * frac(h * 7.3);

// ---- THE ROOF STANDS ASIDE WHEN YOU COME CLOSE ----
//
// A roof that is permanently half missing so the inside can be seen is a bad
// trade: the town reads as ruined from every distance, to buy something only
// wanted up close. So the roof is SOLID, and dissolves only for the person
// standing under it -- within about eight metres it is gone, by sixteen it is
// whole, and in between it thins out. The dither is the material's own
// (bDitherOpacityMask), so temporal AA resolves it into a soft fade rather
// than a checkerboard.
//
// Nothing about this is shared: it is a property of where THIS camera is
// standing, so it never reaches the world, and two citizens looking at the
// same house still see the same house.
// MEASURED TO THE PERSON, NOT THE CAMERA.
//
// This was `distance(W, Cam)`, and the camera in this window sits some
// twenty-five metres above the ground: it is never within eight metres of a
// roof, so the dissolve almost never fired and the roof over a citizen who
// had walked indoors stayed solid. "When you're inside a building it's pretty
// illegible what's going on in there" -- it was, because you were under it.
//
// `Walk` is the citizen's own interpolated position, out of the same shared
// collection every plant on the island reads to lean away from their boots.
// Measured flat, so a roof three metres over their head still clears: the
// height between them is exactly what should NOT count.
float D = distance(float2(W.x, W.y), float2(Walk.x, Walk.y));
// ---- AND IT IS A RING AND NOT A FADE ----
//
// This dissolved over eight and a third metres, which meant every pixel of
// every roof in that ring was strictly between nought and one -- and a masked
// material with a dithered opacity mask draws a partial pixel as a DITHER. A
// whole roof came out as a crawling stipple, regenerated every frame. It is
// the flicker that was reported off the stream, and the wall and the timber
// frame had the same fault in a different spelling; see the long note in
// wall.hlsl.
//
// A dither is for a thin EDGE. So the dissolve is a ring three metres wide
// that sweeps across the roof as the citizen walks under it, rather than a
// fade that holds the whole roof half-drawn for ever. It still opens
// smoothly, because the ring is what moves.
Mask = smoothstep(950.0, 1250.0, D);

// ---- AND THE COURSES ARE A HAND DEEP ----
//
// Everything above is paint: the courses were drawn as darker bands and the
// combing as a lighter stripe, and from above a roof came out as a tan slab
// with faint lines ruled across it. What makes thatch read as thatch is that
// each course is a BUNDLE laid over the one below, and the lip at the bottom
// of it throws a line of shadow the whole width of the roof.
//
// The slope is taken analytically from the same profile the shading uses, so
// the shadow lands exactly where the dark band is rather than beside it.
// `Course` runs up the roof in world Z, so the height gradient is purely
// vertical and only has to be flattened onto the face this pixel is on.
float3 Nn = normalize(N);
float  Deep = 26.0 + 9.0 * h;
// d/dCourse of smoothstep(0, 0.42, Course), which is the bundle's own back.
float  t    = saturate(Course / 0.42);
float  Rise = (6.0 * t * (1.0 - t) / 0.42) / Deep;

// AND THE COMBING ACROSS IT. Seven centimetres is a spar's width; held at
// every range it is a shimmering corduroy, so it goes first as the roof
// recedes and the courses outlive it.
float  Fine = saturate(1.0 - (D - 700.0) / 1800.0);
// HELD MUCH FURTHER THAN THE COMBING IS. A course is a third of a metre and
// is still several pixels across from where this window actually watches from;
// the first pass faded it out by sixty metres on the reasoning that applies to
// the seven-centimetre combing, and the roofs went back to being tan slabs.
float  Near = saturate(1.0 - (D - 2500.0) / 14000.0);
float  Ribs = ((Comb < 0.5) ? 1.0 : -1.0) * (1.0 / 7.0) * 0.55 * Fine;

// The face's own up-slope, flattened into its plane: displacement measured in
// world Z tilts the normal against it.
float3 Zt = float3(0.0, 0.0, 1.0) - Nn.z * Nn;
float3 Xt = float3(0.7071, 0.7071, 0.0);
Xt = Xt - dot(Xt, Nn) * Nn;
Normal = normalize(Nn - Zt * Rise * 2.6 * Near - Xt * Ribs);

Rough = 0.97;
return C;
