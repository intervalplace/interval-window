// A FLAME.
//
// The fires cast light and the fires themselves were cold shapes: a hearth was
// a ring of stone with nothing in it. This is the thing in it -- a cone, lit
// from within, ragged at the top and never still.
//
// MEASURED FROM THE INSTANCE, NOT THE WORLD. A hearth on a hill and a hearth
// in a fen are at different heights, so the gradient from white at the base to
// dark at the tip has to be relative to the piece itself. `O` is where this
// instance sits; the mesh's own texture coordinates would have done as well on
// a cone, but the cylinder's UVs lied once already this session and there is
// no reason to trust a cone's on the strength of that.
//
// Nothing here is told by the world. A fire is a fire; how bright the frame
// makes it is exposure's business, and a fire looks brighter at night for the
// same reason a real one does.

// THE INSTANCE'S OWN SIZE, not a number typed into the material. A hearth
// flame and a watchfire share this material and are four times apart in
// height; `B` is the half-extent of whichever one is being shaded, so the
// gradient and the feathering are right for both without a parameter either
// of them has to be told.
float Height = max(B.z * 2.0, 4.0);
float Wide   = max(B.x, 2.0);
float Up = saturate((W.z - O.z) / Height + 0.5);

// Each fire on its own rhythm, from where it stands -- so two hearths in one
// room do not gutter in unison, and the same hearth gutters the same way in
// every window that draws it.
// SEVEN CENTIMETRES, NOT A METRE. This grid exists so that two hearths in one
// room do not gutter together and so that the same hearth gutters the same way
// in every window -- both of which need only that it be a pure function of
// WHERE the fire stands. At a metre it also rounded the three tongues of a
// single fire (see `hearthfire` in parts.py) into one cell, so they beat in
// perfect unison and the fire pulsed as a block. Fine enough to tell tongues
// apart, still pure, still the same answer everywhere.
float2 Cell = floor(O.xy / 7.0);
float  Seed = frac(sin(dot(Cell, float2(12.9898, 78.233))) * 43758.5453);
float  T    = Time * (2.6 + Seed * 1.9) + Seed * 41.0;

// Two waves that share no period: it wavers rather than pulses.
float Lick = 0.74 + 0.26 * sin(T * 6.2831) + 0.14 * sin(T * 2.73 * 6.2831 + 1.1);

// A flame is white at the heart, orange through the body and nearly out at the
// tip; a fire drawn in one colour reads as a traffic cone.
//
// BUT THIS WINDOW LOOKS STRAIGHT DOWN, and that changes which end of the ramp
// a person actually sees. From the side you read a flame bottom to top and the
// white heart is a small bright core with orange above it. From overhead you
// are looking DOWN THE AXIS: the heart fills the middle of the shape and the
// tip is a thin ring around the edge, so the ramp that reads as fire from the
// side reads as a pale blob from here. A campfire in Anchor was a cream-white
// paper cone in a ring of stones.
//
// So the heart is pulled back until it survives the tonemapper with its hue
// intact. It is still the hottest and brightest part of the fire -- the ramp
// and the ordering are untouched -- but at 3.40 red and 2.30 green it clipped
// both channels at this window's pinned exposure (0.62) and arrived as white.
// The point of the heart is that it is hotter, not that it is blown out.
//
// AND THEN IT WAS PULLED BACK TOO FAR. Softening the silhouette (below) and
// thinning the body fixed "it looks like a lamp" and bought "it looks like a
// smudge": at noon, over lit grass, a translucent wedge at this emissive is
// barely there. The clipping that the pull-back was guarding against came from
// a shape that was nearly SOLID and nearly one colour, so the whole flame
// arrived as one blown-out area. With a real gradient and feathered edges the
// hot core is a few pixels across and can afford to be hot, which is the whole
// point of it.
//
// AND THEN BACK DOWN AGAIN, BECAUSE THERE ARE THREE OF THEM NOW. These were
// raised to 2.90 while a fire was still ONE cone. A fire is three overlapping
// tongues (see `hearthfire` in parts.py) and translucent layers ADD, so the
// place where all three cross -- which is the middle, which is the part you
// look at -- arrived at something like three times the intended heat and bloom
// spread a white hole several metres across the grass. It was read as the
// point light being wrong and it was not; the light already follows `ForceDay`
// correctly, and this was the flame lighting up its own surroundings.
//
// So the numbers go back to roughly where they were when one nearly-solid cone
// carried the whole fire, because three thin ones now sum to about the same
// thing. The lesson is only that these are a property of the WHOLE fire, not
// of a cone, and they have to be retuned whenever the number of tongues does.
float3 Heart = float3(1.80, 0.86, 0.25);
float3 Body  = float3(1.42, 0.50, 0.11);
float3 Tip   = float3(0.86, 0.24, 0.05);
float3 C = lerp(Heart, Body, smoothstep(0.00, 0.42, Up));
C = lerp(C, Tip, smoothstep(0.42, 1.00, Up));

// ---- WHY IT LOOKED LIKE A LAMP ----
//
// Reported, and correctly: "i don't think that really looks like flames, it
// kind of looks like a LED lamp, the flames are not moving at all or very
// faintly, maybe the cone is bigger than the flames underneath."
//
// It was a solid opaque triangle with a hard edge and a notch in it where the
// brazier rim cut across, and the diagnosis is in the line that used to be
// here:
//
//     float Rad = length(W.xy - O.xy) / Wide;
//
// `Wide` is the half-extent of the whole INSTANCE -- the radius of the cone at
// its BASE. A cone tapers, so at two-thirds of the way up its actual radius is
// a third of that, every pixel of it comes out at Rad under 0.33, and the
// feather -- which only begins at 0.30 -- never touches it. The bottom inch of
// the flame was soft and everything above it was a poster-paint wedge with the
// mesh's own silhouette. The comment above about feathering "or it is a
// triangle" was right about the danger and wrong about having avoided it.
//
// Normalising against the radius AT THIS HEIGHT fixes it everywhere at once:
// `r` is now 0 on the axis and 1 at the surface of the cone whatever height
// you are at, so the flame is feathered from base to tip and never reaches the
// mesh's edge at all. The cone stops being a shape and becomes what it should
// always have been -- a region of space the flame is drawn inside.
float  Cw  = max(Wide * (1.0 - Up * 0.92), Wide * 0.08);
float  Rad = length(W.xy - O.xy) / Cw;

// ---- AND WHY IT DID NOT MOVE ----
//
// It did move: the opacity breathed between 0.72 and 1.0 and the top was cut
// at a wandering height. But an opacity that breathes between 0.72 and SOLID
// is not a flame guttering, it is a lamp on a dimmer -- the eye reads motion
// in a SILHOUETTE, and this one was pinned to the mesh.
//
// So the outline itself is what moves now. Three tongues around the axis,
// turning slowly and beating at different rates, pushed up the flame by a
// term in `Up` so a ripple travels from the fire to the tip rather than the
// whole thing pulsing at once. That last part is most of it: fire rises, and
// anything that brightens and dims uniformly is a bulb.
float  Ang  = atan2(W.y - O.y, W.x - O.x);
float  Roll = T * 1.7;
float  Lap  = sin(Ang * 3.0 + Roll + Up * 7.0)
            + 0.62 * sin(Ang * 5.0 - Roll * 1.7 + Up * 11.0 + 2.1)
            + 0.38 * sin(Ang * 2.0 + Roll * 2.6 - Up * 5.0 - 0.7);
Lap *= 0.34;

// Ragged, and raggeder the higher it goes -- the top of a flame is where it is
// coming apart. The lick rides the threshold, so the whole tongue rises and
// falls instead of the colour merely brightening.
// HOW TALL THE TONGUE IS THIS INSTANT. It never reaches the top of the cone
// -- a flame that touches its own bounding box is a flame you have cropped.
float Tear = frac(sin((floor(Up * 9.0) + Cell.x * 3.1 + Cell.y * 7.7) * 91.17) * 4137.9);
float Top = 0.58 + 0.22 * Lick + 0.12 * Tear + 0.18 * Lap;
float Edge = 1.0 - smoothstep(Top, Top + 0.30, Up);

// FEATHERED, or it is a triangle. A flame is a volume: you see through more of
// it down the middle than at the sides, and the sides are where it is thinning
// into smoke. The threshold wanders with the tongues, so the OUTLINE licks
// instead of the fill merely brightening.
float Feather = 1.0 - smoothstep(0.26 + Lap * 0.22, 0.92 + Lap * 0.20, Rad);

// A FLAME IS NOT OPAQUE, and the old one nearly was. Held under three-quarters
// even at the heart, the far side of it shows through and the grass behind the
// hearth is visible past the edges -- which is what says "hot gas" rather than
// "painted cone". The base is thicker than the tip, because there is more fire
// down there to look through.
// THICK AT THE HEART AND THIN AT THE EDGES -- which is not the same as thin
// everywhere, and the first attempt at this made it thin everywhere. What you
// see through is the SIDES of a flame, where it is turning into smoke; down
// the middle there is a great deal of fire in the way. `Feather` above already
// carries the sideways thinning, so this only has to say that the tip is
// wispier than the base.
float Body2 = lerp(0.96, 0.46, smoothstep(0.10, 0.90, Up));
Opacity = saturate(Edge * Feather * Body2 * (0.74 + 0.26 * Lick));
return C * (0.78 + 0.40 * Lick + 0.14 * Lap);
