// Half timbering, drawn rather than textured: a frame of oak with panels of
// limewashed daub. Sill, wall plate, mid rail, studs, and a brace across each
// upper panel. All straight lines, which are cheap.
//
// Driven by WORLD position so the frame runs continuously along a terrace
// rather than restarting at every tile -- restarting is what gives away a
// wall built out of repeated cubes.
//
// `House` is the building's own seed, arriving as per-instance custom data.
// AIntervalChunk flood-fills the footprints the generator described and hashes
// each building's corner IN WORLD TILES, so every wall of one house agrees,
// no two houses in a street are washed alike, and the answer does not depend
// on which chunk drew the wall or in what order the chunks arrived.

// WHO IS ASKING. A wall of this house may arrive two ways. Most of it is
// instanced cubes, and the seed rides in per-instance custom data. But where
// the world named no wall and the window closed the roof's own perimeter
// instead, the surface is a procedural mesh, which has no per-instance data
// at all -- and read straight it came back zero: the closest studding money
// could buy, no braces, and the palest limewash, on every hall on the island.
//
// A static mesh's vertex colour is opaque white unless somebody painted it,
// so a ZERO BLUE is a safe signal that these vertices were built by the
// window and carry the seed in red. One material, both kinds of wall,
// neither knowing the other exists.
float3 W = P;
float Up = W.z;
float3 N = abs(Parameters.TangentToWorld[2]);
float Along = (N.x > N.y) ? W.y : W.x;
float h = (VC.b < 0.5) ? saturate(VC.r) : saturate(House);

// HOW TALL THIS WALL IS. An instanced cube is always a storey, so 270 is
// right for it. A hall is not: the window closes a big roof's perimeter down
// to the ground, and that wall can be five metres. Framed for 270 regardless,
// a barn came out with its plate halfway up and nothing above it -- which is
// most of why the big buildings read as packing crates. The height rides in
// the green channel, in tens of metres, put there by whoever built the quad.
float Top = (VC.b < 0.5 && VC.g > 0.05) ? (VC.g * 1000.0) : 270.0;

float T = 0.0;
T = max(T, 1.0 - smoothstep(0.0, 16.0, abs(Up - 8.0)));                 // sill
T = max(T, 1.0 - smoothstep(0.0, 18.0, abs(Up - (Top - 8.0))));         // wall plate
// Rails divide the height into storeys of roughly two metres, because that is
// what the timber came in and what a floor wants to be.
float Bays = max(1.0, floor(Top / 200.0 + 0.35));
float Rail = Top / Bays;
// The rails themselves, written out rather than looped: a Custom node is one
// expression in a bigger shader and a loop with a break in it is where that
// stops being true. Four is as many storeys as anything here stands.
T = max(T, (1.0 - smoothstep(0.0, 13.0, abs(Up - Rail))) * step(1.5, Bays));
T = max(T, (1.0 - smoothstep(0.0, 13.0, abs(Up - Rail * 2.0))) * step(2.5, Bays));
T = max(T, (1.0 - smoothstep(0.0, 13.0, abs(Up - Rail * 3.0))) * step(3.5, Bays));

// stud spacing varies by house: close studding was a boast, and only the
// well-off could afford that much oak
float Spacing = 42.0 + 30.0 * h;
float Stud = abs(frac(Along / Spacing) - 0.5) * Spacing;
T = max(T, 1.0 - smoothstep(0.0, 10.0, Stud));

// and only some houses are braced, which is most of what stops a street
// looking stamped out
float Brace = abs(frac((Along + Up * 0.9) / 104.0) - 0.5) * 104.0;
float Upper = Top * (Bays - 1.0) / Bays;
float Panel = step(Upper + 12.0, Up) * step(Up, Top - 14.0);
T = max(T, (1.0 - smoothstep(0.0, 9.0, Brace)) * Panel * step(0.38, h));

// ---- AND A WAY TO LOOK OUT ----
//
// The walls had no openings at all. A terrace of blank panels reads as a
// stockade rather than as houses, and after dark it is the single loudest
// thing missing from the window: a village at night with no lit windows in it
// is a village nobody is home in.
//
// UNGLAZED, because glass in a cottage is centuries away. What is here is a
// hole with a mullion down the middle and a heavy oak sill and head -- which
// is what a window was, and which is also why it reads so strongly at night:
// there is nothing between the fire inside and the street.
//
// WHICH BAYS HAVE ONE IS THE HOUSE'S OWN BUSINESS, off the same seed that
// decides its studding and its limewash, so a street has blank gables and
// windowed fronts and no two houses agree -- and it is the same on every
// window that computes it, because the seed came from the building's corner
// in world tiles.
float WinPitch = Spacing * 3.0;
float WinIx    = floor(Along / WinPitch);
float WinAt    = frac(Along / WinPitch);
float WinOwn   = frac(sin(WinIx * 45.23 + h * 337.7) * 4321.77);

// Up the storey this pixel is in, so an upper floor gets its own windows
// rather than the ground floor's repeated.
float Floor  = floor(Up / Rail);
float InFlat = Up - Floor * Rail;

// A sill at a bit under half the storey and a head at three quarters: high
// enough to be above a bench, low enough to be under the rail.
float Sill = Rail * 0.40;
float Head = Rail * 0.72;
// Nothing in the roof triangle, and nothing in the bottom half-metre.
float Fits = step(Sill, InFlat) * step(InFlat, Head) * step(46.0, Up) * step(Up, Top - 30.0);
float Wide = step(0.22, WinAt) * step(WinAt, 0.68);
float Hole = Fits * Wide * step(WinOwn, 0.62);

// THE MULLION. One upright, oak, down the middle of the opening -- and it is
// what makes the hole a window instead of a missing panel.
float MidOff = abs(WinAt - 0.45) * WinPitch;
float Mull = Hole * (1.0 - smoothstep(0.0, 5.5, MidOff));

// The sill and the head are timber too, and heavier than a stud.
float Edge = Wide * step(WinOwn, 0.62)
           * max(1.0 - smoothstep(0.0, 7.0, abs(InFlat - Sill)),
                 1.0 - smoothstep(0.0, 6.0, abs(InFlat - Head)))
           * step(46.0, Up) * step(Up, Top - 30.0);

// The opening takes the studding out of its own width -- a window is framed,
// not studded across.
T = T * (1.0 - saturate(Hole - Mull));
T = max(T, saturate(Mull + Edge));

// LIMEWASH WAS NOT ALWAYS WHITE. It was tinted with whatever was to hand --
// ox blood, ochre, copperas -- so a street runs cream, buff and pink.
float3 Cream = float3(0.520, 0.495, 0.430);
float3 Ochre = float3(0.470, 0.375, 0.225);
float3 Pink  = float3(0.495, 0.390, 0.355);
float3 Daub = lerp(Cream, Ochre, saturate(h * 2.1 - 0.18));
Daub = lerp(Daub, Pink, saturate(h * 2.5 - 1.42));

float3 Oak = float3(0.055, 0.040, 0.028) * (0.82 + 0.50 * frac(h * 5.7));

float G = frac(sin(dot(floor(float2(Along, Up) / 24.0), float2(12.99, 78.23))) * 43758.55);
Daub *= 0.90 + 0.16 * G;
Daub *= 1.0 - 0.30 * saturate((40.0 - Up) / 40.0);

// ---- AND THE OAK STANDS PROUD OF THE DAUB ----
//
// The frame was painted on: a dark stripe in the same plane as the panel
// beside it, which from any angle but straight on reads as a pattern rather
// than as carpentry. A stud is a hand thick and the daub is packed between the
// studs, not over them, so there is a real step at every edge and a line of
// shadow down one side of every timber.
//
// `T` is already a SOFT mask -- each piece is a smoothstep over nine to
// eighteen centimetres -- so its screen derivatives describe the shoulder of
// that step rather than a single pixel, which is what makes this a bevel and
// not a wire. Taken in world units and put back through the surface's own
// tangent frame, so it is right on a wall a chunk built and on an instanced
// cube alike, neither of which agrees with the other about UVs.
float3 Nn = normalize(Nrm);
float  Prd = saturate(T) * 3.0;          // three centimetres of oak
float3 dPx = ddx(W), dPy = ddy(W);
float3 Rx  = cross(dPy, Nn);
float3 Ry  = cross(Nn, dPx);
float  Det = dot(dPx, Rx);
float3 Slope = (abs(Det) > 1e-6) ? (ddx(Prd) * Rx + ddy(Prd) * Ry) / Det : float3(0.0, 0.0, 0.0);
// Gone by forty metres: a three-centimetre step is far under a pixel by then,
// and a sub-pixel bevel is not carpentry, it is a wall that crawls.
float  Hold = saturate(1.0 - (distance(W, Cam) - 900.0) / 3100.0);
Normal = normalize(Nn - Slope * Hold);

// ---- WHAT IS BEHIND THE OPENING ----
//
// By day, the inside of an unlit room, which from outside is very nearly
// black -- and looking nearly black is correct: a small opening into a large
// dark space is the darkest thing on a sunlit street.
//
// By night it is the hearth, and THAT is the whole point of the exercise. The
// fire is already there, already lit, already flickering on its own phase; all
// this has to do is let it out. Some houses are dark, because some houses are
// asleep, and which ones is the house's own number again.
float3 Room = float3(0.010, 0.009, 0.008);
float  Wake = step(0.22, frac(h * 13.7 + 0.31));
// CUBED, for the same reason the stars are. `Night` is one minus the
// daylight, so it is already a tenth before the sun is anywhere near down --
// and at a tenth every window in the village was a dim orange rectangle in
// broad afternoon, which is the specific tell that these are painted on. They
// should come up at dusk and not before it.
float  Dusk = saturate(Night);
float  Lit  = Dusk * Dusk * Dusk * Wake;
// A hearth is not a lamp: warm, and not very bright, and it gutters. Slowly,
// and on this house's own phase, so a street does not pulse in unison.
float  Gutter = 0.82 + 0.18 * sin(View.GameTime * 2.7 + h * 62.83)
                     * sin(View.GameTime * 6.1 + h * 21.17);
float3 Fire = float3(1.00, 0.52, 0.18) * 2.6 * Gutter;
float  Pane = saturate(Hole - Mull);

float3 Colour = lerp(Daub, Oak, saturate(T));
Colour = lerp(Colour, Room, Pane);

// Emissive rather than lit, because what is behind the hole is not a surface
// this window is drawing -- it is a room it is not drawing at all.
Glow = Fire * Pane * Lit;

// ---- AND WHEN YOU ARE INSIDE, THE WALLS COME DOWN TO THE WAIST ----
//
// The roof already dissolves over whoever is under it, and that was not
// enough. A storey is two metres seventy and a person is under two, so from a
// camera twenty-five metres up an open-roofed room is still a box with
// somebody at the bottom of it, and the one thing you cannot see in it is the
// citizen. Taking the wall off above the waist leaves the room its plan --
// sill, lower panel, every corner where it was -- and removes only the part
// that was hiding the figure.
//
// AND IT IS THE ROOF'S OWN TEST, to the centimetre. The first version of this
// gated the cut on being INDOORS -- the alpha of `Walk`, which the hour sets
// from the same shelter test the rain uses -- and that was wrong in the one
// place it mattered. The roof dissolve is not gated on anything but distance,
// so walking down a street takes the roofs off the houses beside you and
// leaves their walls standing: a row of open boxes two metres seventy deep
// with a dark floor at the bottom, which is precisely what "you can't see
// what's going on in there" is a description of. A roof that has gone and a
// wall that has not is worse than both standing.
//
// So the two use the SAME numbers -- 820 to 1650, measured flat to the
// citizen -- and a building opens all at once or not at all.
//
// `Walk` is the citizen's own interpolated position out of the shared
// collection. Its alpha carries how far indoors they are; nothing here reads
// it any more, and it is left in place because the sound and the rain do.

// ---- AND THE CUT MOVES; IT DOES NOT FADE ----
//
// This is the whole of the flicker that was reported off the stream. A masked
// material with `DitherOpacityMask` draws its PARTIAL pixels as a dither, on
// the understanding that they are a thin edge and the temporal filter will
// resolve them. Fading the mask's AMPLITUDE with distance breaks that
// understanding completely: every pixel of every wall in the eight-metre ring
// around the citizen came out strictly between nought and one, so entire walls
// and entire roofs were drawn as a stipple, and the stipple crawled because
// the pattern is regenerated every frame. Photographed twice a second apart it
// is a different pattern each time.
//
// It survives turning off the fog, the global illumination, the particles and
// all translucency, which is what proved it was the geometry's own mask.
//
// So the distance no longer scales the mask. It moves the CUTTING PLANE: near
// the citizen the plane is at brow height, and as they walk away it rises up
// through the roof until it is above everything and the building is whole
// again. The mask is then nought or one everywhere except a sixty-centimetre
// band at the plane, which is a few pixels tall on screen and is exactly the
// thin edge a dither is for.
float Away = distance(float2(W.x, W.y), float2(Walk.x, Walk.y));
float Close = 1.0 - smoothstep(820.0, 1650.0, Away);
// A metre and a third, which is half a storey: the room keeps its plan and its
// corners, and loses the course that was standing between you and the floor.
// Plus nine metres as the citizen walks away, which is over any roof in this
// world and is how the building closes up again.
float Waist = Walk.z + 135.0 + (1.0 - Close) * 900.0;
Mask = 1.0 - smoothstep(Waist, Waist + 60.0, Up);

Rough = lerp(0.88, 0.70, saturate(T));
return Colour;
