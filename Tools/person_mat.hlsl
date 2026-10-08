// THE MASTER MATERIAL FOR THE PEOPLE.
//
// The glTF importer parents everything it brings in to Unreal's Substrate
// master material, and Substrate is not enabled in this project -- so a figure
// arrives with its textures correctly assigned and renders flat grey. It looks
// exactly like a missing texture and is nothing of the sort. This is the third
// time that has cost an afternoon, so it is written here as well as in the
// notes.
//
// Re-doing the material by hand buys two things back. The weather: a citizen
// darkens and slicks in the same rain as the field they are standing in,
// because `Wet` comes from the one collection the hour writes to. And the
// citizen: `Shift` is one number off their own key -- the same number the
// browser window derives -- turning their clothes around the colour wheel
// without touching how light or how saturated the artist painted them.

float3 C = max(Base, 0.0);

// LIFTING A SHEET THAT WAS PAINTED FOR A DIFFERENT SHADER.
//
// One number per sheet, multiplied into the albedo. A multiply rather than a
// curve, because it keeps the relations the artist painted -- the pale tips
// stay pale against the dark heart of a clump -- and because one number is a
// thing a level can tune by looking.
//
// IT IS 1.0 EVERYWHERE AT PRESENT, AND THAT IS THE POINT OF THE NOTE. This
// input was added to rescue leaf sheets that "measured" near black, and the
// measurement was the thing that was wrong: it averaged a 1024-square palette
// whose 78% transparent area the decoder had composited onto flat grey. Over
// the opaque pixels a leaf is (88,123,0), an ordinary green. The canopies were
// black because leaf CARDS were lit on one side only, which is fixed where the
// two-sided override is set, not here. Reach for this only for art that is
// genuinely painted dark, and measure with alpha kept before believing it.
C *= Lift;

// WHAT MAY BE DYED. These atlases are one sheet per outfit covering cloth,
// leather, steel AND the skin of the face and hands, so the region cannot be
// read off a material name the way the flat-coloured art allows. It can be
// read off the pixel: cloth is the saturated, mid-bright part of the sheet;
// skin is pale and warm, leather and iron are dark and nearly grey. Get this
// wrong in the generous direction and everybody in a blue tunic has blue hands.
float Mx = max(C.r, max(C.g, C.b));
float Mn = min(C.r, min(C.g, C.b));
float Chroma = Mx - Mn;
float S = (Mx > 1e-5) ? Chroma / Mx : 0.0;

float IsCloth = smoothstep(0.12, 0.30, S)
              * smoothstep(0.02, 0.08, Mx)
              * (1.0 - smoothstep(0.40, 0.70, Mx));

// --- turn the hue, keep the light ---
float H = 0.0;
if (Chroma > 1e-5)
{
	if (Mx == C.r)      { H = (C.g - C.b) / Chroma; }
	else if (Mx == C.g) { H = (C.b - C.r) / Chroma + 2.0; }
	else                { H = (C.r - C.g) / Chroma + 4.0; }
	H = frac(H / 6.0 + 1.0);
}
// Centred on zero, so half a street shifts warm and half cool rather than
// everybody drifting the same way from the artist's colour.
H = frac(H + (Shift - 0.5) * 0.24 * saturate(Strength) * IsCloth + 1.0);

float  h6 = H * 6.0;
float  X  = Chroma * (1.0 - abs(fmod(h6, 2.0) - 1.0));
float3 R  = (h6 < 1.0) ? float3(Chroma, X, 0.0)
          : (h6 < 2.0) ? float3(X, Chroma, 0.0)
          : (h6 < 3.0) ? float3(0.0, Chroma, X)
          : (h6 < 4.0) ? float3(0.0, X, Chroma)
          : (h6 < 5.0) ? float3(X, 0.0, Chroma)
                       : float3(Chroma, 0.0, X);
C = R + Mn;

// HAIR IS NOT PAINTED, IT IS DYED.
//
// The hairstyles ship as neutral grey -- measured, not assumed: both atlases
// average about (143,143,141) with everything between 88 and 178, which is
// strand detail and no colour at all. It is meant to be tinted, so the colour
// comes from the citizen like everything else about them, off a different
// turn of the same key so that a fair-haired woman is not obliged to wear a
// particular tunic.
//
// The palette is six colours hair actually comes in. A hue wheel is the wrong
// instrument here: it would give somebody green hair eventually, and there is
// no village in which that reads as variety.
if (HairTint > 0.5)
{
	float Luma = dot(C, float3(0.299, 0.587, 0.114));
	float T = frac(Shift * 7.0);
	int   i = (int)floor(T * 6.0);
	float3 P = (i == 0) ? float3(0.0113, 0.0097, 0.0091)   // black
	         : (i == 1) ? float3(0.0444, 0.0231, 0.0124)   // dark brown
	         : (i == 2) ? float3(0.1499, 0.0665, 0.0273)   // brown
	         : (i == 3) ? float3(0.2519, 0.0705, 0.0220)   // auburn
	         : (i == 4) ? float3(0.5647, 0.3613, 0.0703)   // fair
	                    : float3(0.3250, 0.3057, 0.2698);  // grey
	// Divided by the atlas's own mean so the palette arrives at the
	// brightness it was chosen at, with the strands modulating around it.
	C = P * saturate(Luma / 0.283);
}

// THE PALLOR OF THE DEAD.
//
// This world has four words for a corpse that walks -- `risen`, `barrow-wight`,
// `gibbet-dead`, `gibbet-king` -- and one for a skeleton knight. A cartoon
// skeleton with a round skull and black eye sockets was tried and was plainly
// wrong beside these people; what reads right is the SAME BODY, drained. So
// the figure is the citizens' own, desaturated toward bone and cooled.
//
// It is a parameter rather than a second set of textures because the living
// and the dead are the same art, and a corpse is a thing that happens to a
// person rather than a different species.
if (Pallor > 0.001)
{
	float Grey = dot(C, float3(0.299, 0.587, 0.114));
	// Not pure grey: bone is warm-pale and dead flesh is faintly green, and a
	// flat grey figure reads as untextured rather than as dead.
	C = lerp(C, Grey * float3(0.94, 0.95, 0.88), saturate(Pallor));
}

// ORM is the glTF convention: occlusion in red, roughness in green, metal in
// blue. Some of these sheets are a plain ROUGHNESS map instead, and the naive
// reading of one of those is a trap I fell straight into: a greyscale map has
// a mid-grey blue channel, so metalness came out around a half. Half-metallic
// skin is not skin. It is bronze, and a citizen who looked cast rather than
// born is exactly how it was spotted.
//
// So metalness is CAPPED per material, and the cap is zero unless the sheet is
// a real ORM. Roughness and occlusion read correctly off a greyscale map
// either way, which is why only this channel needed saying.
// THE OCCLUSION, WHERE THERE IS ONE TO READ.
//
// Art without an ORM sheet has its COLOUR map hung in the slot, and a colour
// map's red channel is not occlusion. Believing it told the renderer that a
// leaf in open air was in a cave -- see the note beside `AOFloor` in
// make_person_mat.py, which cost most of a night. The floor is 0 for sheets
// that really are ORM, and 1 for sheets that are only standing in.
AO    = max(saturate(ORM.r), saturate(AOFloor));
Rough = saturate(ORM.g);
Metal = min(saturate(ORM.b), MetalMax);

// NOT EVERYTHING SHIPS AN ORM SHEET. The hairstyles come with a colour map and
// a normal map and nothing else, and reading roughness out of the colour map
// makes dark hair mirror-smooth -- a black bob with a highlight like a car
// bonnet. `RoughFloor` is the least rough this surface is allowed to be, which
// is a thing the art cannot say and a level can.
Rough = max(Rough, RoughFloor);
Metal = Metal * (1.0 - RoughFloor);

// ONLY THE HEAD, WHERE THIS IS A BODY UNDER CLOTHES.
//
// A citizen is an outfit plus a bare body, and the bare body is there for ONE
// reason: the outfits stop at the collar and somebody has to supply the face.
// The free body is Quaternius's "Superhero" physique and the outfits are cut
// for his "Regular" one, so the chest and the biceps stand several centimetres
// outside the shirt -- not fighting it for the depth buffer, simply bigger
// than it. No amount of holding the cloth off the skin fixes a body that does
// not fit the clothes.
//
// So the body below the collar is not drawn at all. `Cut` is a height in the
// figure's own BIND POSE -- which is what Skin is, the vertex before any bone
// has moved it, so a raised arm does not take a shoulder's worth of skin with
// it. Above the cut is a head and a neck; below it, the outfit is the only
// thing there, and the outfit brings its own hands.
// AND THE SHEET'S OWN ALPHA, WHERE THE SURFACE IS A CARD.
//
// A leaf is not a rectangle. Leaves, grass and flowers are flat quads wearing
// an atlas that is three-quarters empty, and the alpha channel is the only
// record of where the leaf ends. This line did not read it: the mask was the
// collar test alone, foliage sets `Cut` so far below the mesh that the test
// always passes, and so every card came out fully opaque -- a little green
// leaf in the middle of a black tile. A whole wood of them read as dark
// shattered glass, and the trunk in the same tree looked perfectly well,
// because bark is solid geometry with nothing to cut.
//
// `Cover` is zero for a person, whose sheet is opaque and whose only cut is
// the collar, so nothing about a citizen changes here.
Mask = (Skin.z >= Cut) ? lerp(1.0, saturate(Sheet), saturate(Cover)) : 0.0;

// (`Puff`, which holds cloth off skin, is a plain multiply of the vertex normal
// wired straight to World Position Offset in the graph. It cannot live in this
// node: a Custom node that reads a vertex interpolator is a PIXEL-shader node,
// and world position offset is a VERTEX-shader output --
//   "Custom interpolator outputs only available in pixel shaders."
// One node cannot be both.)

// Rain darkens whatever it lands on and tightens the highlight, exactly as it
// does to the ground.
float W = saturate(Wet);
C     *= lerp(1.0, 0.78, W);
Rough  = lerp(Rough, Rough * 0.45, W);

// LIGHT THAT COMES THROUGH A LEAF.
//
// ---- ONE SHEET, AND THOUSANDS OF COPIES OF IT ----
//
// A meadow is tens of thousands of the same blade, a wood is the same five
// trees, and every terrain in the world scatters exactly ONE mesh. Drawn from
// one sheet they are the same colour to the last pixel, and a field of perfect
// clones reads as unfinished however good the single copy is. Nothing about
// the grass is wrong. There is only one of it.
//
// `Vary` is the engine's per-instance random: one number per copy, fixed for
// the life of that copy. Fixed matters -- anything derived from view or time
// makes the field shimmer as the camera moves, which is worse than clones.
//
// TWO AXES, because brightness alone reads as dirt rather than as variety.
// Hue drifts between a cool blue-green and a warm yellow-green, which is the
// spread a real canopy has across a season and across how much light each
// plant gets; value spreads separately and by less, so nothing goes black or
// blows out.
//
// `Varies` is zero by default, so a person, an anvil and a wall are untouched.
// This belongs to things the world stamps out in thousands, not to things
// there is one of -- and a shirt that changed colour per citizen would be a
// bug rather than a meadow.
if (Varies > 0.001)
{
	float V = frac(Vary);
	float H = frac(Vary * 3.7 + 0.13);
	float3 Cool = float3(0.88, 1.02, 0.94);
	float3 Warm = float3(1.10, 1.03, 0.80);
	C *= lerp(1.0, lerp(Cool, Warm, H) * (0.84 + 0.30 * V), saturate(Varies));
}

// A leaf is a translucent sheet a tenth of a millimetre thick, and most of
// what you see of a canopy from below or against the sun is light that went
// THROUGH it, not light that bounced off it. A renderer that only bounces
// gives you the thing this window had all night: a tree whose sunward cards
// are bright green and whose every other card is black, with a terminator
// down the trunk you could cut yourself on. It is not too little ambient --
// the sky here is already physically scaled -- it is a missing transport path.
//
// So this output feeds Subsurface Colour on the foliage copy of this master,
// which is built with the Two Sided Foliage shading model. It is ignored by
// the person copy, where a shirt does not glow.
//
// Greener and lighter than the albedo, because chlorophyll passes green and
// eats red: a backlit leaf is the brightest, purest green in any wood.
// AND MORE OF IT THAN A FIRST PASS GAVE. A canopy of cards self-shadows
// heavily -- every leaf is standing behind four others -- so the light that
// matters most is the light coming THROUGH, and at 1.6x green it was still
// losing to the shadowing. Lifted, and lifted most in green, because that is
// the channel chlorophyll actually passes; the red and blue stay low so the
// canopy warms towards the sun rather than washing out to white.
// ---- AND WHAT TIME OF YEAR IT IS ----
//
// The year turns in twenty-eight days off the constitutional day index alone,
// so two people in the same field on different windows see the same autumn
// without the engine having a word for a season. `sky.mjs` has computed these
// three for as long as it has computed the weather; nothing had read them.
//
// ONLY THE LEAVES. This file is one shader compiled into TWO materials --
// M_IntervalPerson and M_IntervalFoliage -- and a shirt does not go gold in
// October. There is no runtime flag telling them apart, because they are
// separate materials rather than two branches of one, so `make_person_mat.py`
// substitutes LEAFY_FLAG for 1.0 or 0.0 as it writes the code. It is a
// compile-time constant and the whole block folds away in the person copy.
//
// The three overlap at their edges and that is deliberate: a week of autumn
// runs into a week of winter, so the canopy is still half gold when the first
// frost dulls it. High summer is all three at zero and needs no term.
if (LEAFY_FLAG > 0.5)
{
	float A = saturate(Autumn), Wn = saturate(Winter), Sp = saturate(Spring);

	// AUTUMN, which is a hue rotation and not a tint. Multiplying a green leaf
	// by orange gives mud, because the green channel it is strongest in is the
	// one being multiplied down. Rotating the hue towards red keeps the leaf's
	// own value and variation -- the pale ones stay pale -- and that variation
	// is what stops a wood in October reading as one flat sheet of rust.
	float3 Gold = float3(C.r * 1.34 + C.g * 0.52, C.g * 0.62 + C.r * 0.10, C.b * 0.34);
	C = lerp(C, saturate(Gold), A * 0.88);

	// WINTER dulls rather than whitens. Snow on a canopy is the ground's job,
	// not the leaf's; what a frost does to what is left up there is take the
	// colour out of it and darken it slightly. Desaturating towards the leaf's
	// own luminance keeps the light and dark of the canopy intact.
	float L = dot(C, float3(0.299, 0.587, 0.114));
	C = lerp(C, lerp(C, float3(L, L, L) * 0.86, 0.72), Wn);

	// SPRING is the smallest of the three on purpose. A blossom blush over the
	// whole island would be a stranger sight than autumn; this lifts the
	// lightest leaves towards pink and leaves the deep ones green, which is
	// what a wood in blossom actually looks like from any distance.
	float Tips = saturate((L - 0.22) * 2.6);
	C = lerp(C, saturate(C * float3(1.16, 0.97, 1.06) + float3(0.05, 0.01, 0.04) * Tips),
	         Sp * 0.55);
}

Trans = saturate(C * float3(1.35, 2.45, 0.85) + float3(0.02, 0.05, 0.01));

return C;
