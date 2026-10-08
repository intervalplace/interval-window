// Which layer a tile takes is chosen by the code in its control texel, and
// that code is an index the bridge handed us this session. What an index
// MEANS is not this material's business and no build of this project holds
// an opinion about it. An index past the end of the table is not an error --
// it is a world with ground this build has never drawn -- so it falls back
// to layer 0, which is why layer 0 must look like plausible ground.

// ---- THE WARP ----
// A tile is a square and the ground is not. Sampled straight, every country's
// edge is a staircase of 2m corners and the island reads as graph paper: the
// heath meets the moor along a line no weather ever drew.
//
// So the LOOKUP POSITION is warped -- not the code, not the boundary. Each
// pixel asks "which tile am I in" from a point shifted a little way through a
// standing wave, so the answer changes along a ragged line instead of a
// square one. Three things keep this honest:
//
//   the code is still sampled HARD, on a texel centre, so a pixel shows one
//   country's ground and never a smear of two;
//
//   the warp is a pure function of WORLD position -- no time, no chunk, no
//   view -- so it is the same ragged line in every window that computes it,
//   and two citizens looking at the same edge see the same edge;
//
//   the amplitude is held under HALF A TILE, which buys the invariant that
//   matters: at a tile's centre the warp cannot reach past its own texel, so
//   the ground under your feet is always your tile's ground. Where the Fens
//   end is still a tile boundary and still the bridge's answer; this only
//   stops that boundary from being drawn with a set square.
float2 Wp = W.xy;
float2 Warp;
Warp.x = sin(Wp.x * 0.0173 + Wp.y * 0.0091)
       + 0.55 * sin(Wp.x * 0.0412 - Wp.y * 0.0367)
       + 0.30 * sin(Wp.y * 0.1010 + 1.7);
Warp.y = sin(Wp.y * 0.0161 - Wp.x * 0.0104)
       + 0.55 * sin(Wp.y * 0.0389 + Wp.x * 0.0341)
       + 0.30 * sin(Wp.x * 0.0970 + 4.1);
Warp *= 0.140;        // amplitudes sum to 1.85 -> at most 0.259 of a tile

// ---- WHERE TO READ ----
// The control texture carries the SKIRT as well as the ground, so a warped
// read near a chunk's edge lands on the neighbour's real code instead of on
// the clamped border texel. Without the skirt the warp would print a seam
// down every chunk join -- the same fault as the relief seam and the lost
// eaves, and the same answer: give it the border to read.
float2 Size = max(ChunkSize.xy, float2(1.0, 1.0));
float  Sk   = max(ChunkSize.z, 0.0);
float2 Tex  = Size + 2.0 * Sk;
float2 Inv  = 1.0 / Tex;

// ---- TILE COORDINATES, FROM THE WORLD AND NOT FROM THE UV ----
//
// This read `UV * Size + Sk`, and a UV is interpolated across a TRIANGLE.
// The ground is a grid of quads, each split into two triangles on the same
// diagonal; lift the four corners of a quad to different heights and it stops
// being planar, so the UV interpolates differently in each of its halves and
// everything drawn from it KINKS along the diagonal they share. Every quad on
// the island kinks the same way, so a hillside came out as a weave of shears:
// paving stones went from square to parallelograms, and it was reported three
// times over as "the slopes and hills look off", "weird distorted angles" and
// "it doesn't look like a small hill, it looks weird".
//
// World position cannot do that. The ground is a heightfield, so its XY is the
// tile grid exactly, whatever the mesh does with Z -- and a chunk actor is
// spawned at its own corner tile, which is what `Origin` is. `ChunkSize.w`
// carries the tile size in centimetres; a zero there means an instance from
// before this existed, and the old reading is kept for it rather than dividing
// by nothing.
float2 T    = (Tile > 0.0) ? ((W.xy - Origin.xy) / Tile + Sk)
                           : (UV * Size + Sk);

// ---- WHAT WAS LAID BY HAND KEEPS ITS EDGE ----
// The warp is right for country. It is wrong for flagstone: people lay a
// square SQUARE, and wandering its edge by half a metre turned every lane and
// market place into a puddle of mud with grass islands in it. So the tile is
// read twice -- once where it really is, once through the warp -- and the
// straight answer wins wherever the straight answer is something somebody
// paved. Both reads are hard samples of a real texel; neither invents a code.
float2 Straight = (floor(T) + 0.5) * Inv;
float4 Laid = Texture2DSample(Control, ControlSampler, Straight);
int    Flat = (int)(Laid.r * 255.0 + 0.5);
bool   ByHand = (Flat == 2 || Flat == 3 || Flat == 14 || Flat == 15
              || Flat == 20 || Flat == 21);

float2 Tw   = ByHand ? T : (T + Warp);
float2 Snap = ByHand ? Straight : ((floor(Tw) + 0.5) * Inv);
float4 Ctl  = ByHand ? Laid : Texture2DSample(Control, ControlSampler, Snap);

int   Code = (int)(Ctl.r * 255.0 + 0.5);
float Seed = Ctl.b;

// ---- THE WAY, RECONSTRUCTED SMOOTHLY ----
// The CODE is sampled hard, on the texel centre, and must stay that way: a
// blurred code is a blurred answer to where the Fens end, and two citizens
// have to be able to agree on that. Wear is not a boundary anyone meets at,
// so the way mask gets its own bilinear reconstruction -- four taps, lerped.
// Without it every rut restarts at the tile edge and the road reads as a
// ladder instead of a track. It reads from the WARPED position too, so that
// the verge stays pinned to the ground it is scuffing.
float2 P = Tw - 0.5;
float2 f = frac(P);
float2 b = (floor(P) + 0.5) * Inv;
float g00 = Texture2DSample(Control, ControlSampler, b).g;
float g10 = Texture2DSample(Control, ControlSampler, b + float2(Inv.x, 0.0)).g;
float g01 = Texture2DSample(Control, ControlSampler, b + float2(0.0, Inv.y)).g;
float g11 = Texture2DSample(Control, ControlSampler, b + Inv).g;
float Way = lerp(lerp(g00, g10, f.x), lerp(g01, g11, f.x), f.y);

// rgb = albedo, a = roughness. Indices only, on purpose.
float4 L[27];
L[0]  = float4(0.160, 0.235, 0.090, 0.92);
L[1]  = float4(0.230, 0.165, 0.100, 0.95);
L[2]  = float4(0.245, 0.238, 0.226, 0.80);
L[3]  = float4(0.300, 0.292, 0.274, 0.72);
L[4]  = float4(0.235, 0.228, 0.208, 0.93);
L[5]  = float4(0.480, 0.420, 0.280, 0.90);
L[6]  = float4(0.225, 0.218, 0.208, 0.91);
L[7]  = float4(0.600, 0.592, 0.560, 0.86);
L[8]  = float4(0.085, 0.065, 0.048, 0.95);
L[9]  = float4(0.030, 0.030, 0.032, 0.95);
L[10] = float4(0.105, 0.165, 0.082, 0.93);
L[11] = float4(0.010, 0.026, 0.048, 0.06);
L[12] = float4(0.018, 0.046, 0.072, 0.09);
L[13] = float4(0.190, 0.188, 0.180, 0.88);
L[14] = float4(0.185, 0.130, 0.078, 0.86);
L[15] = float4(0.225, 0.198, 0.152, 0.90);
L[16] = float4(0.058, 0.105, 0.058, 0.94);
L[17] = float4(0.078, 0.145, 0.068, 0.93);
L[18] = float4(0.195, 0.188, 0.178, 0.89);
L[19] = float4(0.118, 0.148, 0.092, 0.90);
L[20] = float4(0.175, 0.128, 0.082, 0.88);
L[21] = float4(0.270, 0.263, 0.248, 0.76);
L[22] = float4(0.140, 0.128, 0.082, 0.93);
L[23] = float4(0.180, 0.255, 0.100, 0.92);
L[24] = float4(0.250, 0.290, 0.140, 0.91);
L[25] = float4(0.330, 0.318, 0.292, 0.88);
L[26] = float4(0.200, 0.160, 0.110, 0.94);

if (Code < 0 || Code >= 27) { Code = 0; }
float4 G = L[Code];

float3 Albedo = G.rgb * (0.94 + 0.12 * Seed);
float  R      = G.a;

// ---- GRAIN ----
// One flat colour per country is the other half of the graph-paper look: the
// warp fixes the edges and leaves the middle dead. A little world-space
// mottle at two scales -- coarse patches the size of a few tiles, fine
// break-up at arm's length -- gives the ground somewhere for the eye to land
// without saying anything about what the ground IS.
// PLANE WAVES, NOT PRODUCTS. sin(ax) * sin(by) is a grid of alternating cells
// by construction -- it made the whole island tartan the first time. Waves
// crossing at angles that share no common period look like country.
float m1 = sin(Wp.x * 0.0087 + Wp.y * 0.0063)
         + 0.7 * sin(Wp.x * -0.0051 + Wp.y * 0.0104 + 1.9);
float m2 = sin(Wp.x * 0.0410 - Wp.y * 0.0337 + 0.6)
         + 0.7 * sin(Wp.x * 0.0288 + Wp.y * 0.0461 - 2.3);
float Grain = (m1 * 0.42 + m2 * 0.19);
Albedo *= (1.0 + 0.085 * Grain);
R       = saturate(R + 0.05 * Grain);

// ---- AND AT THE SCALE OF A FIELD ----
//
// The grain above works at seven metres and at one and a half, which is the
// right range for somebody standing in it. From four hundred metres up it is
// all below a pixel and averages out, and a meadow becomes one flat green
// across the whole of a founding -- which is what the aerials were showing.
// This is the octave the aerial view needs: forty-five metres, half a field,
// low contrast, and warmer where it is lighter, because ground that catches
// more sun is drier as well as brighter.
float Field = sin(Wp.x * 0.00113 + Wp.y * 0.00081)
            + 0.60 * sin(Wp.x * -0.00071 + Wp.y * 0.00134 + 2.4);
Field *= 0.62;                       // amplitudes sum to 1.6
Albedo *= lerp(float3(0.955, 0.965, 0.985), float3(1.055, 1.035, 0.985),
               saturate(Field * 0.5 + 0.5));

// WHAT WEAR MAY NOT TOUCH.
// Water and decking: the generator has already said what that tile is, and a
// road ON a bridge is the bridge.
// And ANYTHING SOMEBODY PAVED. The made-way mask runs straight down a town's
// streets, so blending worn earth over it turned every lane, square and room
// floor in all fifteen settlements to mud -- people lay flagstone precisely
// so that it does NOT become a rut. The generator distinguishes the paved
// kinds from the beaten ones; this only has to respect the distinction.
float Bare = 1.0;
if (Code == 11 || Code == 12 || Code == 14) Bare = 0.0;          // water, decking
if (Code == 2 || Code == 3 || Code == 15 || Code == 20 || Code == 21) Bare = 0.0;  // laid by hand

// ---- THE VERGE ----
// Nobody walks a line. The grass beside a way is scuffed, drier and paler
// than the country it belongs to, and that fringe is most of what makes a
// road look used rather than drawn. A narrow band, or the whole country goes
// brown and the road stops being a road.
float Verge = smoothstep(0.10, 0.34, Way) * (1.0 - smoothstep(0.34, 0.62, Way)) * Bare;
Albedo = lerp(Albedo, lerp(G.rgb, float3(0.245, 0.215, 0.130), 0.6), Verge * 0.65);
R      = lerp(R, 0.95, Verge * 0.5);

// ---- THE WAY ITSELF ----
//
// AND IT IS DARK ON PURPOSE. This was lightened once, on the theory that a
// beaten path is dry dust and catches the light -- and that was the wrong
// reading of the same picture: "I don't think the colour or shade of the
// trails is the problem. They make sense to be dark too, like worn grass
// where the mud comes up, that is dark not light." Worn grass in this
// climate is mud coming up through it, and mud is darker than the field.
//
// The trail is also RIGHT to be there, including inside a town, which was
// worth settling before touching any of it: "in a town there is a lot of
// walking and not everybody walks only on the paved road so it makes sense
// there would be trails too". They are desire paths. A town of nothing but
// laid stone would be the poorer picture.
float Core = smoothstep(0.40, 0.80, Way) * Bare;
float3 Worn = float3(0.175, 0.135, 0.095) * (0.90 + 0.20 * Seed);
Albedo = lerp(Albedo, Worn, Core * 0.9);
R      = lerp(R, 0.95, Core * 0.9);

// ---- RUTS ----
// Two grooves either side of the crown. Distance from the centreline is just
// (1 - Way) now that Way is a smooth field, so the grooves run continuously
// along the track and bend with it without anything knowing its direction.
// On a paved square Way is 1 everywhere, the distance collapses to zero and
// no rut is cut -- which is the right answer for a square.
float d = 1.0 - saturate(Way);
float rut = exp(-pow((d - 0.26) * 8.5, 2.0)) * Core;
Albedo *= (1.0 - 0.30 * rut);
R      = lerp(R, 0.60, rut * 0.75);   // packed smooth by what rolls over it

// ---- HOW FAR AWAY THE EYE IS ----
// Wanted twice below: once by the close-range surface and once by the rain
// rings. Both are detail at the scale of a hand, and both are noise rather
// than detail once that scale falls under a pixel.
float Away = length(CamPos - W);

// ---- CLOSE UP, THE SURFACE ITSELF ----
//
// A NORMAL, WHICH THIS MATERIAL REFUSED FOR A LONG TIME -- and the refusal
// was right about a different thing. What was tried before was a normal
// derived from the HEIGHT FIELD, and that cannot work at this camera: across
// a valley one pixel is most of a tile, the height field folds several times
// inside it, and what comes out is a hard grid laid over the whole country.
//
// This is not that. It is three plane waves at a hand's breadth, with nothing
// to do with the terrain, and it is written as waves precisely so the slope
// can be had EXACTLY rather than by differencing a sampled height -- which is
// where the grid came from. Waves crossing at angles that share no common
// period have no lattice to find.
//
// AND IT GOES AWAY. The last attempt faded with distance too and left a
// visible line where it gave up; the difference here is that the amplitude is
// small enough that the fade has nothing to show. It is gone by about thirty
// metres, which is past everything the watch camera holds in focus.
float2 K1 = float2( 0.0611, -0.0429);
float2 K2 = float2(-0.0347,  0.0724);
float2 K3 = float2( 0.1490,  0.1130);
float  A1 = dot(Wp, K1) + 0.7, A2 = dot(Wp, K2) + 2.9, A3 = dot(Wp, K3) - 1.3;
float  Bump  = sin(A1) + 0.74 * sin(A2) + 0.42 * sin(A3);
float2 Tilt  = cos(A1) * K1 + 0.74 * cos(A2) * K2 + 0.42 * cos(A3) * K3;
float  Grit  = saturate(1.0 - (Away - 900.0) / 2400.0);
// Rougher where it stands proud and slightly darker in the hollows, which is
// what dust in a hollow does and what makes the relief read as earth rather
// than as embossing.
Albedo *= (1.0 + 0.050 * Bump * Grit);
R       = saturate(R + 0.030 * Bump * Grit);
// A tenth of a radian at most: ground, not rubble.
float2 Relief = Tilt * 0.90 * Grit;
// ---- AND WHEN IT IS WET ----
//
// Wet ground is two things at once and only one of them is obvious. It is
// DARKER, because water fills the air between the grains and stops them
// scattering light back out; and it is SMOOTHER, because the same water fills
// in the surface, which is why a road shines after rain and a dry one never
// does. Doing only the first gives you mud with the lights off.
//
// Where water COLLECTS is not everywhere. It runs off grass and stands in the
// ruts a cart cut, so the shine follows the wear the material already knows
// about -- which is the whole reason the ruts were worth having.
float Soak = saturate(Wet);
float Pool = saturate(rut * 1.6 + Core * 0.35) * Soak;

Albedo *= lerp(1.0, 0.62, Soak * (0.55 + 0.45 * saturate(Way)));
Albedo = lerp(Albedo, Albedo * 0.72, Pool);
R = lerp(R, 0.34, Soak * 0.55);
R = lerp(R, 0.08, Pool);          // standing water is a mirror

// ---- AND WHILE IT IS ACTUALLY FALLING ----
//
// `Wet` above is the ground REMEMBERING rain: it lags a shower by half a
// minute either way, which is right for how long a road stays dark. `Rain` is
// whether drops are landing NOW, and that is a different picture entirely --
// a hundred rings a second, each one opening and gone.
//
// AND IT IS A NORMAL, WHICH THIS MATERIAL OTHERWISE REFUSES TO WRITE.
//
// A procedural normal off the height field was tried and taken out again, for
// the reason set out above: across a valley one pixel is most of a tile and
// the result is graph paper. A rain ring is not that. It is not derived from
// the terrain at all, it exists only while it is raining, and it is at a scale
// -- forty centimetres -- where a normal is telling the truth rather than
// approximating a fold. Roughness alone would not do it: flat ground under an
// even sky reflects the same thing at every roughness, so a ring drawn only in
// roughness is invisible except to the sun's own glint.
//
// SO IT IS A WORLD-SPACE NORMAL. The material is set to world space rather
// than tangent space, which means this has to hand back the surface's OWN
// normal when nothing is raining -- `N` unchanged, which is exactly what the
// renderer would have used anyway. It costs nothing and it avoids depending on
// the tangents of a mesh this window generates at runtime.
float3 Nrm = normalize(normalize(N) + float3(Relief, 0.0));
float  Fall = saturate(Rain);
if (Fall > 0.01)
{
	// A RING IS A FEW PIXELS AT A HUNDRED METRES AND LESS THAN ONE AT FOUR
	// HUNDRED. Drawn all the way out it is not rain, it is a field of
	// shimmering noise that crawls when the camera moves -- so it is faded out
	// past about twelve metres and gone by forty, where the wet darkening and
	// the falling streaks carry it instead.
	float Close = saturate(1.0 - (Away - 1200.0) / 2800.0);
	float Show  = Fall * Close;
	if (Show > 0.01)
	{
		// TWO GRIDS, DIFFERENT SIZES, OFFSET FROM EACH OTHER. One grid of
		// rings is a lattice, and a lattice is what the eye finds first: the
		// rings land in rows and the rain reads as a printed pattern. Two
		// incommensurate grids have no shared row to find.
		float2 Slope = 0.0;
		float  Ring  = 0.0;
		for (int g = 0; g < 2; ++g)
		{
			float  Cell = g == 0 ? 44.0 : 67.0;
			float2 Q  = (W.xy + float2(g * 21.0, g * 47.0)) / Cell;
			float2 Id = floor(Q);
			float2 Fr = frac(Q) - 0.5;
			float  Rnd = frac(sin(dot(Id, float2(127.1, 311.7))) * 43758.5453);
			// NOT EVERY CELL, EVERY CYCLE. Rain is not a sprinkler: a drop
			// lands here and not there, and a grid in which every square is
			// always ringing is a grid you can see. About a third of them are
			// live at a time, and which third changes as the cycle turns over.
			float  Live = frac(sin(dot(Id, float2(269.5, 183.3))) * 27182.8459);
			if (Live > 0.38) { continue; }
			// Each cell on its own phase, so the rings do not pulse together.
			float  Cyc = frac(Time * 1.45 + Rnd);
			float  Rad = Cyc * 0.44;
			float  D   = length(Fr);
			// A crest that opens outwards and dies as it goes. The gaussian is
			// what makes it a RING rather than a disc.
			//
			// THE WIDTH IS THE WHOLE THING. The first pass used a band a
			// twenty-fourth of a cell wide with a slope multiplier of
			// thirty-four, on the reasoning that a real ripple is thin and
			// steep. Both are true of a ripple and neither survives being
			// sampled: at a centimetre and a half across, every ring was
			// narrower than a pixel from any camera that could see the ground,
			// and a near-vertical facet at that size turns the whole meadow
			// into wet gravel -- which is exactly what it looked like. Wide
			// and shallow reads as water; thin and steep reads as grit.
			float  Band = exp(-pow((D - Rad) * 11.0, 2.0)) * (1.0 - Cyc);
			Ring  += Band;
			// The crest's own slope: uphill towards the ring from inside,
			// downhill from outside, which is what a ripple is.
			Slope += normalize(Fr + 1e-5) * Band * (Rad - D) * 8.0;
		}
		Ring = saturate(Ring);
		Nrm = normalize(Nrm + float3(Slope * Show * 0.5, 0.0));
		// The wet ring is momentarily a mirror, and a shade darker, which is
		// the same two facts about wet ground written above at another scale.
		R = lerp(R, 0.12, Ring * Show * 0.70);
		Albedo *= lerp(1.0, 0.92, Ring * Show);
	}
}

// ---- THE DECKING ----
//
// A bridge and a causey were flat coloured tiles: the ground material knew to
// keep wear off them and nothing else, so the one structure in this world that
// a citizen builds with their own planks read as a slab of paint laid over the
// water.
//
// Planks run ACROSS a span, never along it -- that is how a deck is laid and
// it is what tells the eye which way the crossing goes. Which way that is is
// not in the frame either, so it is taken from the neighbours: a deck tile
// with decking east and west of it is a span running east-west, and its boards
// lie north-south. The same question the fences ask, asked of the ground.
if (Code == 14 || Code == 15)
{
	float AlongX = 0.0;
	float AlongY = 0.0;
	[unroll] for (int d = 1; d <= 2; ++d)
	{
		float2 Ex = (floor(Tw + float2(d, 0)) + 0.5) * Inv;
		float2 Wx = (floor(Tw - float2(d, 0)) + 0.5) * Inv;
		float2 Ny = (floor(Tw + float2(0, d)) + 0.5) * Inv;
		float2 Sy = (floor(Tw - float2(0, d)) + 0.5) * Inv;
		int Ce = (int)(Texture2DSample(Control, ControlSampler, Ex).r * 255.0 + 0.5);
		int Cw = (int)(Texture2DSample(Control, ControlSampler, Wx).r * 255.0 + 0.5);
		int Cn = (int)(Texture2DSample(Control, ControlSampler, Ny).r * 255.0 + 0.5);
		int Cs = (int)(Texture2DSample(Control, ControlSampler, Sy).r * 255.0 + 0.5);
		AlongX += ((Ce == 14 || Ce == 15) ? 1.0 : 0.0) + ((Cw == 14 || Cw == 15) ? 1.0 : 0.0);
		AlongY += ((Cn == 14 || Cn == 15) ? 1.0 : 0.0) + ((Cs == 14 || Cs == 15) ? 1.0 : 0.0);
	}
	// Boards lie across the run. A single isolated deck tile falls to X, which
	// is arbitrary and is the same arbitrary answer in every window.
	float Across = (AlongY > AlongX) ? W.x : W.y;
	float Length = (AlongY > AlongX) ? W.y : W.x;

	// ONE BOARD EVERY TWENTY-TWO CENTIMETRES, which is a plank a person could
	// actually have carried here, and the gap between them is a shadow line
	// rather than a hole -- you can see daylight through a real deck, and a
	// black line at this scale reads as one without costing geometry.
	float Board = Across / 22.0;
	float Seam = abs(frac(Board) - 0.5) * 2.0;        // 0 at the joint
	float Joint = 1.0 - smoothstep(0.62, 0.96, Seam);

	// Each board its own timber: they were cut from different trees and they
	// weather differently, which is most of what stops a deck reading as one
	// printed texture.
	float Plank = frac(sin(floor(Board) * 78.233) * 43758.5);
	Albedo *= 0.88 + 0.24 * Plank;
	Albedo *= 1.0 - Joint * 0.55;

	// The grain, along the board, and a little wear down the middle where feet
	// go -- a bridge is a road and gets walked exactly where a road does.
	float Grain = sin(Length * 0.9 + Plank * 20.0) * 0.5 + 0.5;
	Albedo *= 0.96 + 0.08 * Grain;

	// The joint is a groove, not a stripe. Without this the boards are a
	// pattern; with it they are boards.
	float2 Cut = (AlongY > AlongX) ? float2(1.0, 0.0) : float2(0.0, 1.0);
	float Edge = (frac(Board) < 0.5) ? -1.0 : 1.0;
	Nrm = normalize(Nrm + float3(Cut * Edge * Joint * 0.55, 0.0));

	// Bare timber underfoot: matte, and a shade rougher at the joints where
	// the dirt collects.
	R = lerp(0.86, 0.94, Joint);
}

// ---- THE SAND ----
//
// Sand was the flattest ground in the world: one beige, the common mottle, and
// nothing else. It is the ground a citizen sees most closely -- every bank and
// every beach -- and at this camera height a flat fill reads as paper.
//
// Two things, and both are cheap. GRAIN, at a scale you would actually see
// grains at, which is finer than the mottle every other ground shares. And
// RIPPLES: wind and water both leave sand in parallel bands, which is the one
// pattern that says sand and not dust. They run across the prevailing wind --
// the same direction the grass leans -- so the country agrees with itself.
if (Code == 5 || Code == 7)
{
	// The ripple, in world space so it does not swim when the camera moves.
	float2 Rp = W.xy * 0.055;
	float Ridge = sin(Rp.x * 0.57 - Rp.y * 0.82)
	            + 0.45 * sin(Rp.x * 1.31 - Rp.y * 1.90 + 1.3);
	// Broken up, or it is corduroy: real ripples fork and die out.
	float Break = sin(W.x * 0.011 + W.y * 0.017) * 0.5 + 0.5;
	Ridge *= 0.45 + 0.55 * Break;

	// Grain: fine, and only just visible. Sand that sparkles reads as gravel.
	float Grit = frac(sin(dot(floor(W.xy * 0.55), float2(12.9898, 78.233))) * 43758.5);

	Albedo *= 1.0 + Ridge * 0.045 + (Grit - 0.5) * 0.055;

	// The ripple has a SHAPE, not just a colour. A few millimetres of relief is
	// all it takes at this angle, and it is what stops the bands reading as a
	// pattern printed on a flat sheet.
	float2 Crest = float2(
		0.57 * cos(Rp.x * 0.57 - Rp.y * 0.82) + 0.59 * cos(Rp.x * 1.31 - Rp.y * 1.90 + 1.3),
	   -0.82 * cos(Rp.x * 0.57 - Rp.y * 0.82) - 0.86 * cos(Rp.x * 1.31 - Rp.y * 1.90 + 1.3));
	Nrm = normalize(Nrm + float3(Crest * 0.085 * (0.45 + 0.55 * Break), 0.0));

	// Dry sand is not polished, and wet sand at the water's edge is.
	R = lerp(R, 0.86, 0.5);
}

// ---- WHAT SOMEBODY LAID, STONE BY STONE ----
//
// Cobble, flag and plaza were three greys with the common mottle over them,
// and a flat grey with a mottle is POURED CONCRETE -- which is what the street
// through Anchor looked like, because that is what it was. Asked what it is
// standing on, the world answers `flag` down the length of the street, `cobbl`
// where the ways cross and `floor` inside the houses; three different words,
// three different trades, and one colour for all of them.
//
// A paved surface is not one surface. It is a few hundred SEPARATE STONES,
// each found or cut on a different day, each sitting a little proud or a
// little sunk, with dirt in the joints between them. The thing that says
// somebody LAID this rather than somebody POURED it is simply that you can see
// where one stone ends and the next begins.
//
// So the pattern is CELLULAR, not a grid. A grid of squares is a bathroom
// floor: the eye finds the lattice at once and the square goes flat again.
// Scattering one stone per cell and asking which stone a pixel is NEAREST
// gives stones that are all different shapes and still tile the plane with no
// gaps and no overlaps -- which is exactly what a paviour achieves by eye, and
// for the same reason.
//
// Three numbers carry all three kinds:
//   SETT -- how big a stone is. A cobble is what one hand can set down; a
//           flagstone is a slab two people carry; a plaza is dressed ashlar
//           laid by a mason who had the whole square to fill.
//   JIT  -- how far a stone's centre may wander from its cell. A found cobble
//           sits wherever it fits. Ashlar is cut square and does not wander.
//   GAP  -- how wide the joint is. Cobble is bedded in sand with a finger's
//           width between; ashlar is a hairline.
// and one more that is not a number: flag and plaza are laid in COURSES and
// cobble is not, so the slabs get a running bond and the cobbles do not.
if (Code == 2 || Code == 3 || Code == 21)
{
	// HOW BIG A STONE IS, in centimetres of world.
	// A COBBLE TILE IS USUALLY A MENDED BIT OF A FLAGGED STREET. The world
	// interleaves the two words along one road -- five flags, two cobbles, a
	// flag, two cobbles -- so a cobble drawn as a wholly different material
	// turns a street into a patchwork quilt. Bigger setts and a tighter joint
	// than a cobbled yard would have, so the patch reads as the same road,
	// repaired, rather than as somewhere else.
	float  Sett = (Code == 2) ? 36.0  : ((Code == 21) ? 84.0  : 126.0);
	// AND HOW WIDE THE JOINT IS, as a fraction of a stone. Cobble is bedded in
	// sand with a finger's width between; ashlar is a hairline. Both were
	// first set by eye at about half these numbers and both were invisible: a
	// cobble is roughly ten pixels across at this camera, so a joint at nine
	// hundredths of a stone is under a pixel and the street came back flat.
	// Measured off a photograph, which is the only way this was ever going to
	// be right.
	float  Gap  = (Code == 2) ? 0.098 : ((Code == 21) ? 0.078 : 0.046);

	// A STONE SMALLER THAN A PIXEL IS NOISE, NOT DETAIL -- the same rule the
	// grit and the rain rings already follow, and the reason both of those
	// fade. Big stones survive further out than small ones, so the range is
	// measured in stones rather than in metres and every kind fades where its
	// own detail stops being visible.
	float Vis = saturate(1.0 - (Away - Sett * 220.0) / (Sett * 330.0));
	if (Vis > 0.004)
	{
		float  Edge;          // distance to the joint, in stones
		float2 Kid;           // which stone, as two numbers that never change
		float2 Fall;          // which way the face slopes, at the joint

		if (Code == 2)
		{
			// ---- COBBLE IS FOUND STONE, SO IT IS CELLULAR ----
			//
			// A grid of squares is a bathroom floor: the eye finds the lattice
			// at once and the street goes flat again. Scattering one stone per
			// cell and asking which stone a pixel is NEAREST gives stones that
			// are all different shapes and still tile the plane with no gaps
			// and no overlaps -- which is what a paviour achieves by eye, and
			// for the same reason.
			float2 Cp = W.xy / Sett;
			float2 Ci = floor(Cp);
			float2 Cf = Cp - Ci;

			// PASS ONE: which stone this pixel belongs to.
			float  Bd = 8.0;
			float2 Mr = float2(0.0, 0.0);
			float2 Mg = float2(0.0, 0.0);
			[unroll] for (int sj = -1; sj <= 1; ++sj)
			{
				[unroll] for (int si = -1; si <= 1; ++si)
				{
					float2 Gv = float2(si, sj);
					float2 Kc = Ci + Gv;
					float2 Hs;
					Hs.x = frac(sin(dot(Kc, float2(127.1, 311.7))) * 43758.5);
					Hs.y = frac(sin(dot(Kc, float2(269.5, 183.3))) * 43758.5);
					float2 Pt = Gv + 0.5 + (Hs - 0.5) * 0.78;
					float2 Rv = Pt - Cf;
					float  Dd = dot(Rv, Rv);
					if (Dd < Bd) { Bd = Dd; Mr = Rv; Mg = Gv; }
				}
			}

			// PASS TWO: HOW FAR THE JOINT IS, which is a different question and
			// cannot be answered from the first pass. The distance to the
			// nearest stone CENTRE is a cone, and drawn as a joint it gives
			// every stone a dark blob in the middle and nothing at its edge.
			// The distance to the BORDER is the distance to the plane halfway
			// between this stone and each of its neighbours, taken at its
			// smallest: a real edge, the same width all the way round, which
			// is what mortar is.
			float Eg = 8.0;
			[unroll] for (int tj = -1; tj <= 1; ++tj)
			{
				[unroll] for (int ti = -1; ti <= 1; ++ti)
				{
					float2 Gv = Mg + float2(ti, tj);
					float2 Kc = Ci + Gv;
					float2 Hs;
					Hs.x = frac(sin(dot(Kc, float2(127.1, 311.7))) * 43758.5);
					Hs.y = frac(sin(dot(Kc, float2(269.5, 183.3))) * 43758.5);
					float2 Pt = Gv + 0.5 + (Hs - 0.5) * 0.78;
					float2 Rv = Pt - Cf;
					float2 Dv = Rv - Mr;
					// BRANCHLESS, AND NOT FOR SPEED. Written as
					// `if (Ln > eps) Eg = min(Eg, ... * rsqrt(Ln))` this
					// material would not COMPILE: Metal's shader converter
					// rejected the ray-tracing hit shader with "Unhandled FP64
					// usage", Unreal failed the whole material, and -- the part
					// that cost the afternoon -- kept the last shader map that
					// HAD compiled and went on drawing with it. Every edit to
					// this file afterwards rendered as though it had never been
					// made, silently, including the diagnostics written to find
					// out why. Same arithmetic, no branch, no rsqrt: clean.
					float  Ln = max(dot(Dv, Dv), 0.00001);
					float  Hd = dot(0.5 * (Rv + Mr), Dv / sqrt(Ln));
					Eg = min(Eg, (dot(Dv, Dv) > 0.00001) ? Hd : 8.0);
				}
			}
			Edge = Eg;
			Kid  = Ci + Mg;
			// `Mr` points AT the centre, so the face falls the other way.
			Fall = (Bd > 0.000001) ? normalize(Mr) : float2(0.0, 0.0);
		}
		else
		{
			// ---- BUT A SLAB IS CUT SQUARE AND LAID IN COURSES ----
			//
			// The first version ran flag and plaza through the same cells as
			// the cobble, offsetting alternate rows by half a stone for the
			// running bond. Photographed, every street in Anchor came out
			// HEXAGONAL -- which is exactly right and exactly wrong: a square
			// lattice with every other row shifted by a half IS a hexagonal
			// lattice, and the Voronoi of one is honeycomb. It read as modern
			// concrete pavers, which is the thing this whole section exists to
			// stop.
			//
			// A slab is not found, it is cut, so it does not want cells at all.
			// A jittered brick grid gives real rectangles, a real running bond,
			// and a joint that is genuinely straight -- and it is cheaper than
			// the eighteen hashes the cellular path spends.
			//
			// AND THEY RUN WITH THE STREET, WHICH IS NOT IN THE FRAME.
			//
			// The first version laid the courses on the WORLD's axes. Anchor's
			// streets run diagonally, so the grid crossed them at an angle and
			// the two arms of one crossroads came out looking like two
			// different pavements -- which is what was reported: "why is there
			// such a mix of different types?" Some of that mix is the world's
			// own (it says `flag` and `cobble` tile by tile along the same
			// street) and this part was not: it was one pattern seen at two
			// obliquities.
			//
			// Nobody lays flagstone across a road. The direction is taken the
			// same way the decking above takes its planks -- by asking which
			// way the paving CONTINUES -- so a street is laid along itself
			// without this material knowing what a street is. At a crossing
			// the two counts tie and it falls to X, which is arbitrary and is
			// the same arbitrary answer in every window.
			float PaveX = 0.0;
			float PaveY = 0.0;
			[unroll] for (int pd = 1; pd <= 2; ++pd)
			{
				float2 Pe = (floor(T + float2(pd, 0)) + 0.5) * Inv;
				float2 Pw = (floor(T - float2(pd, 0)) + 0.5) * Inv;
				float2 Pn = (floor(T + float2(0, pd)) + 0.5) * Inv;
				float2 Ps = (floor(T - float2(0, pd)) + 0.5) * Inv;
				int Qe = (int)(Texture2DSample(Control, ControlSampler, Pe).r * 255.0 + 0.5);
				int Qw = (int)(Texture2DSample(Control, ControlSampler, Pw).r * 255.0 + 0.5);
				int Qn = (int)(Texture2DSample(Control, ControlSampler, Pn).r * 255.0 + 0.5);
				int Qs = (int)(Texture2DSample(Control, ControlSampler, Ps).r * 255.0 + 0.5);
				PaveX += ((Qe == 2 || Qe == 3 || Qe == 21) ? 1.0 : 0.0)
				       + ((Qw == 2 || Qw == 3 || Qw == 21) ? 1.0 : 0.0);
				PaveY += ((Qn == 2 || Qn == 3 || Qn == 21) ? 1.0 : 0.0)
				       + ((Qs == 2 || Qs == 3 || Qs == 21) ? 1.0 : 0.0);
			}
			bool RunY = (PaveY > PaveX);
			// Wider than deep, which is how a slab is cut and most of why a
			// flagged street reads as LAID rather than as tiled. The long axis
			// lies ALONG the run.
			float2 Cell = RunY ? float2(Sett * 0.68, Sett) : float2(Sett, Sett * 0.68);
			float2 Bp   = W.xy / Cell;
			// Half a stone, course by course -- offsetting ACROSS the run,
			// which is what a running bond is.
			if (RunY) { Bp.y += 0.5 * fmod(abs(floor(Bp.x)), 2.0); }
			else      { Bp.x += 0.5 * fmod(abs(floor(Bp.y)), 2.0); }
			float2 Bi = floor(Bp);
			float2 Bf = Bp - Bi;

			// A mason works to a line and still does not work to a micrometre.
			// A few per cent of wander on each joint is the difference between
			// stone and vinyl, and it is keyed to the stone so the two sides of
			// one joint agree about where it is.
			float2 Wob;
			Wob.x = frac(sin(dot(Bi, float2(23.71, 91.13))) * 29283.5) - 0.5;
			Wob.y = frac(sin(dot(Bi, float2(61.09, 17.47))) * 31791.5) - 0.5;
			float2 Bw = Bf + Wob * 0.085;

			// Distance to the nearest of the four edges of this rectangle.
			// The y axis is squashed, so it is scaled back before comparing --
			// otherwise the long joints read twice as wide as the short ones.
			float2 Dx = min(Bw, 1.0 - Bw);
			float  Ex = RunY ? (Dx.x * 0.68) : Dx.x;
			float  Ey = RunY ? Dx.y : (Dx.y * 0.68);
			Edge = min(Ex, Ey);
			Kid  = Bi;
			// The face falls toward whichever joint is nearest, along its axis.
			Fall = (Ex < Ey) ? float2((Bw.x < 0.5) ? -1.0 : 1.0, 0.0)
			                 : float2(0.0, (Bw.y < 0.5) ? -1.0 : 1.0);
			Fall = -Fall;    // outward from the stone's middle
		}

		float Seam = 1.0 - smoothstep(0.0, Gap, Edge);       // 1 in the joint

		float Hn = frac(sin(dot(Kid, float2(12.9898, 78.233))) * 43758.5);
		float Hm = frac(sin(dot(Kid, float2(39.3468, 11.1352))) * 24634.5);
		float Hk = frac(sin(dot(Kid, float2(74.7141, 52.9137))) * 19733.5);

		// EACH STONE ITS OWN STONE. This is most of the effect and it is worth
		// being clear why: the joints alone give you a PATTERN, and a pattern
		// is still a printed thing. It is the fact that no two stones are the
		// same grey -- some warmer, some colder, some plainly darker rock --
		// that makes them read as quarried and carried and set by somebody.
		//
		// The first setting of these numbers was too timid and the street came
		// back looking poured again with lines drawn on it. A quarry is not
		// uniform and neither is what gets carted from it.
		float3 Tone = lerp(float3(0.86, 0.870, 0.905),
		                   float3(1.16, 1.120, 1.035), Hn);
		Tone *= 0.74 + 0.48 * Hm;
		// AND ONE STONE IN EIGHT IS A DIFFERENT ROCK ALTOGETHER, which is what
		// happens when a road is mended over two hundred years.
		Tone = lerp(Tone, Tone * float3(0.78, 0.74, 0.70),
		            smoothstep(0.86, 1.0, Hk));
		float3 Paved = Albedo * Tone;

		// AND THE FACE OF A STONE IS NOT SMOOTH EITHER. A pock at about a
		// hand's breadth -- it was at four centimetres first, which is under a
		// pixel here, and read as sand blown over the street rather than as
		// the face of anything. Keyed to the STONE as well as to the world so
		// that it stops dead at the joint instead of running across it: a
		// texture that crosses a joint is the giveaway that the joints are
		// painted on.
		float Pock = frac(sin(dot(floor(W.xy * 0.085) + Kid * 7.0,
		                          float2(12.9898, 78.233))) * 43758.5);
		Paved *= 0.945 + 0.110 * Pock;

		// WHAT IS IN THE JOINT IS NOT SHADOW, IT IS DIRT: sand, moss, and
		// whatever the street has dropped into it. Drawn black it is a wire
		// grid laid over the ground; drawn as dirt it is mortar.
		float3 Mortar = float3(0.125, 0.118, 0.098) * (0.80 + 0.40 * Seed);
		Paved = lerp(Paved, Mortar, Seam * 0.88);

		// A COBBLE IS A DOME AND A FLAGSTONE IS A SLAB WITH ITS EDGES KNOCKED
		// OFF, and both fall out of the same number -- how near the joint the
		// pixel is. A stone lit from one side with a flat normal is a painted
		// stone, and this is the whole difference between a cobbled street and
		// a photograph of one.
		float Crown = (Code == 2) ? 1.0 : 0.34;
		float Slope = Crown * (1.0 - smoothstep(0.0, Gap * 3.4, Edge));
		Nrm = normalize(Nrm - float3(Fall * Slope * 0.55 * Vis, 0.0));

		// AND THEY ARE WALKED ON. The crown of a stone takes the feet and goes
		// smooth; the joint holds grit and stays rough. That contrast is what
		// separates a street from a stone floor nobody has ever used, and it is
		// what catches the light after rain.
		float Rs = lerp(0.40 + 0.30 * Hm, 0.95, Seam);

		Albedo = lerp(Albedo, Paved, Vis);
		R      = lerp(R, Rs, Vis);
	}
}

// ---- AND THE FLOOR OF A HOUSE ----
//
// `floor` is its own word and its own colour -- brown, not grey -- so it is
// boards, not stone, and it was getting neither. The decking above cannot draw
// it: a deck works out which way it runs by looking for more deck to the east
// and west, and a room is a blob with deck on all four sides of it.
//
// A room does not have to say which way its boards run, because a BUILDING
// does: boards are laid the length of the house and every room in it agrees.
// So the direction comes from a twelve-metre block of the world, which is
// bigger than any room in this world and smaller than a street -- one hash,
// one answer, and every floor inside one house lies the same way.
if (Code == 20)
{
	float Way20 = frac(sin(dot(floor(W.xy / 1200.0),
	                           float2(45.164, 22.813))) * 43758.5453);
	float Across = (Way20 < 0.5) ? W.x : W.y;
	float Along  = (Way20 < 0.5) ? W.y : W.x;

	// Indoor boards are wider than a bridge's: a floor is planed timber laid
	// on joists, not whatever could be carried out over the water.
	float Board = Across / 28.0;
	float Gap20 = abs(frac(Board) - 0.5) * 2.0;
	float Joint = 1.0 - smoothstep(0.66, 0.97, Gap20);

	float Plank = frac(sin(floor(Board) * 78.233) * 43758.5);
	Albedo *= 0.90 + 0.20 * Plank;
	Albedo *= 1.0 - Joint * 0.42;

	float Vein = sin(Along * 0.7 + Plank * 20.0) * 0.5 + 0.5;
	Albedo *= 0.965 + 0.070 * Vein;

	float2 Cut = (Way20 < 0.5) ? float2(1.0, 0.0) : float2(0.0, 1.0);
	float  Lip = (frac(Board) < 0.5) ? -1.0 : 1.0;
	Nrm = normalize(Nrm + float3(Cut * Lip * Joint * 0.38, 0.0));

	// A floor indoors is swept and waxed where it is walked and dull in the
	// joints, which is the opposite way round from a street and reads as inside.
	R = lerp(0.62, 0.92, Joint);
}

// ---- THE WATER ----
//
// Until now a river was a flat blue tile with the land's own mottle on it: no
// depth, no shore, no movement, and the same roughness as a meadow. It read as
// a painted ribbon, which is exactly what it was.
//
// Three things make water read as water, and none of them is the colour blue:
//
//   IT GETS DEEPER AWAY FROM THE BANK. A river with one flat colour is a road
//   that happens to be blue. The depth is not in the frame -- the world says
//   "river", not "how deep" -- so it is measured HERE, by asking the control
//   texture how much of the neighbourhood is also water. A tile with water on
//   every side is open channel; a tile with land beside it is the shallows.
//   Two radii, so the gradient survives a channel only a few tiles across.
//
//   IT MOVES. Two crossing wave trains at different rates and angles, which
//   never line up and so never show their period. The normal is perturbed, not
//   the height -- this is a flat sheet of ground and must stay one -- and the
//   lighting does the rest.
//
//   IT IS A MIRROR. Roughness near zero is most of the effect: it is what puts
//   the sky and the far bank on the surface and separates water from wet mud,
//   which is the one thing this ground was already good at drawing.
//
// The foam is the fourth thing and the one that sells the edge. A hard line
// where water meets sand reads as a cut-out; a band that wanders with the
// waves reads as a shore.
if (Code == 11 || Code == 12)
{
	// HOW OPEN THIS WATER IS. Sampled hard, like the code itself, because a
	// blurred answer here would smear the bank.
	// SAMPLED AROUND THE PIXEL, NOT AROUND THE TILE.
	//
	// The first version offset from `Snap` -- the tile CENTRE -- so every pixel
	// in a tile got the same nine answers and the depth was a step function two
	// metres wide. The river came out in visible squares, which is the graph
	// paper this whole material was written to avoid, only in water.
	//
	// Offsetting from the pixel's own warped position instead makes the count
	// move continuously as the eye travels: each tap still lands hard on one
	// tile's code -- no smearing of what a tile IS -- but WHICH tiles the nine
	// taps hit changes smoothly, and the average of them does too.
	float Near = 0.0;
	float Far  = 0.0;
	[unroll] for (int oy = -1; oy <= 1; ++oy)
	{
		[unroll] for (int ox = -1; ox <= 1; ++ox)
		{
			float2 O = float2(ox, oy);
			// Still snapped to a texel centre -- a blended code is a blended
			// answer about what a tile IS, which this material forbids. What
			// moves with the pixel is WHICH texel each tap lands on.
			float2 U1 = (floor(Tw + O * 1.15) + 0.5) * Inv;
			float4 N1 = Texture2DSample(Control, ControlSampler, U1);
			int C1 = (int)(N1.r * 255.0 + 0.5);
			Near += (C1 == 11 || C1 == 12 || C1 == 14) ? 1.0 : 0.0;
			float2 U2 = (floor(Tw + O * 2.90) + 0.5) * Inv;
			float4 N2 = Texture2DSample(Control, ControlSampler, U2);
			int C2 = (int)(N2.r * 255.0 + 0.5);
			Far += (C2 == 11 || C2 == 12 || C2 == 14) ? 1.0 : 0.0;
		}
	}
	// 9 taps each. Nine means every neighbour is water; the shallows are
	// anything less. Far is weighted lower -- it decides the middle of a
	// broad water, where Near has already saturated.
	float Open = saturate((Near - 2.0) / 7.0);
	float Wide = saturate((Far  - 2.0) / 7.0);
	float Deep = saturate(Open * 0.65 + Wide * 0.35);
	// EIGHTEEN TAPS STILL STEP, just eighteen times instead of once. The last
	// of the staircase is broken by the swell itself -- the surface is moving
	// anyway, so letting the depth wander with it hides the remaining edges in
	// something that is supposed to be wandering.
	// (this wander is three metres across, so it survives much further out than
	//  the ripple does -- but it is still a pattern, and at the horizon it is
	//  the last thing left making a grid. It leans on the same fade, late.)
	// ---- AND THE GRID AT THE HORIZON IS THIS, NOT THE RIPPLE ----
	//
	// The note above calls it: "it is still a pattern, and at the horizon it is
	// the last thing left making a grid." It was two trains, and two trains
	// interfere into a lattice as surely as sin(ax) * sin(by) does. At three
	// metres across, photographed from fifty metres up, the open sea came out
	// as a field of identical teardrops at a fixed pitch. That is the whole of
	// what was reported, and it is in the water's DEPTH, not in its normal:
	// lighter and darker blobs, not glints, which is how you tell the two
	// apart by eye.
	//
	// Four trains now, at periods of roughly 2.3, 2.0, 1.8 and 1.4 metres that
	// share no ratio, and the total amplitude held where it was so the water is
	// no busier than it was -- only less regular.
	float Settle = saturate(1.0 - (Away - 9000.0) / 14000.0);
	Deep = saturate(Deep + (sin(W.x * 0.021 + W.y * 0.017) * 0.028
	                      + sin(W.x * -0.013 + W.y * 0.029) * 0.022
	                      + sin(W.x * 0.0337 + W.y * -0.0112) * 0.019
	                      + sin(W.x * 0.0089 + W.y * 0.0451) * 0.015) * Settle);

	// THE COLOUR OF DEPTH. Shallow water is the BANK seen through a little
	// water -- which is why it takes its tint from the sand it is lying on
	// rather than from a paler blue. Deep water is its own colour and nearly
	// opaque.
	float3 Shallow = float3(0.42, 0.50, 0.44);
	float3 Middle  = float3(0.20, 0.34, 0.38);
	float3 Deepest = float3(0.055, 0.115, 0.165);
	// ---- OPENNESS IS NOT DEPTH, AND A RIVER IS NEVER OPEN ----
	//
	// `Deep` blends Open (how much water within a tile and a bit) with Wide
	// (how much within three), and both colour steps were driven off the
	// blend. That is right for a coast, where the two rise together as you
	// wade out, and wrong for a river, which is never open at any point along
	// it: the Great River is three to four tiles across, so even mid-channel
	// `Wide` stays near nothing, `Deep` never passes about 0.7, and the whole
	// river was drawn in the SHALLOW colour -- which takes its tint from the
	// sand it lies on, by design, because shallow water is the bank seen
	// through a little water.
	//
	// So the island's rivers read as dry sandy scars with a pale trickle down
	// the middle, while a lake twice as wide a few hundred metres away reads
	// as water. Photographed from above at twenty tiles across: three tiles of
	// water, of which one was blue.
	//
	// The two steps ask the two questions separately now. Whether this is
	// WATER rather than wet sand is a question about the near count, which
	// saturates mid-channel on anything three tiles across. Whether it is DEEP
	// enough to go dark is a question about the wide count, which only broad
	// water can answer. Open sea has both and is unchanged.
	float3 Wat = lerp(Shallow, Middle, saturate(Open * 1.35));
	Wat = lerp(Wat, Deepest, saturate(Wide * 1.25));

	// THE SURFACE. Two trains crossing at an angle, at rates that do not
	// divide into one another, plus a slow third that breaks up the pair.
	//
	// AND IT GOES CALM WITH DISTANCE, which is not an optimisation, it is what
	// water looks like. The surface here is very nearly a MIRROR -- roughness
	// between 0.02 and 0.055 -- and a mirror tilted eight degrees in bands a
	// metre wide throws the sky back in bands a metre wide. Close up that is
	// ripple. At a hundred metres a metre is a few pixels, the bands land on
	// and off the sampling grid, and what comes out is a hard regular
	// cross-hatch over the whole water: a pond photographed from the far bank
	// read as corrugated iron.
	//
	// Real water does the same thing for real: the ripples do not vanish, but
	// past a certain distance they average out within the eye and what is left
	// is a flat sheet of sky. So the detail is faded and the mirror is kept.
	// Same shape as `Grit` further up, which fades the ground's own hand-scale
	// relief for the same reason and was written after the same fault.
	float Calm = saturate(1.0 - (Away - 2200.0) / 6500.0);
	// ---- AND THE WAVES GET LONGER, NOT JUST SMALLER ----
	//
	// Fading the AMPLITUDE is half the answer and it is the half that does not
	// work. The note above has the diagnosis exactly right: at a hundred metres
	// a metre is a few pixels, "the bands land on and off the sampling grid,
	// and what comes out is a hard regular cross-hatch over the whole water".
	// That is an aliasing fault, and shrinking a pattern that is already below
	// the pixel does not cure aliasing. Photographed across the water at
	// Fenmarch it was still corrugated iron from shore to horizon.
	//
	// So the near water keeps its one-and-a-half-metre ripple and the far water
	// is given a five-metre swell instead: the same waves, stretched, so what
	// reaches the eye at distance is always several pixels across and cannot
	// land between samples. Which is also what real water does, because what
	// survives being looked at from far away is the long swell and not the
	// chop on top of it.
	// SCALING THE WAVELENGTH BY DISTANCE WAS WRONG, and the picture said so at
	// once: `Calm` is measured from the CAMERA, so warping the waves by it
	// warps their PHASE radially, and the sea came out in concentric rings
	// centred on the eye that would travel with it. A pattern that follows the
	// camera is the oldest giveaway there is.
	//
	// So the phase never moves. There are two wave sets at fixed scales: a five
	// metre SWELL, which is always there and is what survives being looked at
	// from far away, and a metre-and-a-half CHOP added on top of it, faded out
	// with distance because below a pixel it is not detail, it is moire. Adding
	// detail in cannot shift what is underneath, so nothing rings.
	// ---- AND THE REASON IT STILL LOOKED LIKE A GRID ----
	//
	// Sinusoids interfere into lattices. That is what they do, and no number of
	// them cures it: two trains give a coarse lattice, four give a finer one,
	// and every version of this that answered the fault by adding another wave
	// made the mesh tighter rather than making it go away. Reported twice,
	// correctly, by somebody looking at the water rather than at the code.
	//
	// So the waves are not changed; the WATER UNDER THEM is pushed about. A
	// slow, very long offset, fifteen to thirty metres across, is added to the
	// coordinate the waves are read at. Every crest then wanders, no two parts
	// of the sea are in step, and the pattern has no cell to repeat: the same
	// trains, read off a surface that is no longer flat graph paper.
	//
	// This is cheap. It is four more sines at a frequency low enough that they
	// cost nothing in detail, and it does the work that twice as many wave
	// trains could not.
	float2 Warp;
	Warp.x = sin(W.x * 0.0041 + W.y * 0.0027 + Time * 0.21)
	       + sin(W.x * -0.0019 + W.y * 0.0052 + Time * 0.13) * 0.8;
	Warp.y = sin(W.x * 0.0033 + W.y * -0.0045 + Time * 0.17)
	       + sin(W.x * 0.0058 + W.y * 0.0021 + Time * 0.09) * 0.8;
	// EASED BACK from 210. At that strength the crests curled into whorls and
	// the sea read as marbling rather than water: the lattice was gone and
	// something worse had replaced it. Eighty is enough to stop any two
	// stretches being in step, which is all that was ever needed, and leaves
	// the waves looking like waves.
	float2 Wrp = W.xy + Warp * 80.0;

	// A five metre SWELL, always there, which is what survives distance; and a
	// metre-and-a-half CHOP on top, faded out with distance because below a
	// pixel it is not detail, it is moire. Both read off the warped position.
	//
	// The phase is never scaled by anything the camera knows. An earlier cut
	// scaled the WAVELENGTH by distance and the sea came out in concentric
	// rings centred on the eye, which travelled with it.
	float2 Ws = Wrp * 0.013;
	float2 Wc = Wrp * 0.045;
	float SwellL = sin(Ws.x * 1.00 + Ws.y * 0.62 + Time * 0.58)
	             + sin(Ws.x * -0.74 + Ws.y * 1.31 + Time * 0.42) * 0.85;
	float SwellC = sin(Wc.x * 1.00 + Wc.y * 0.62 + Time * 1.15)
	             + sin(Wc.x * -0.74 + Wc.y * 1.31 + Time * 0.83) * 0.85;
	float Swell = SwellL + SwellC * Calm;
	// Each coefficient is the wave's DIRECTION times its amplitude, because
	// this is the gradient of the swell and not a decoration. The swell leans
	// less than the chop: it is longer as well as taller.
	float2 Ripple;
	Ripple.x = (cos(Ws.x * 1.00 + Ws.y * 0.62 + Time * 0.58) * 1.00
	          - cos(Ws.x * -0.74 + Ws.y * 1.31 + Time * 0.42) * 0.63) * 0.75
	         + (cos(Wc.x * 1.00 + Wc.y * 0.62 + Time * 1.15) * 1.00
	          - cos(Wc.x * -0.74 + Wc.y * 1.31 + Time * 0.83) * 0.63) * Calm;
	Ripple.y = (cos(Ws.x * 1.00 + Ws.y * 0.62 + Time * 0.58) * 0.62
	          + cos(Ws.x * -0.74 + Ws.y * 1.31 + Time * 0.42) * 1.11) * 0.75
	         + (cos(Wc.x * 1.00 + Wc.y * 0.62 + Time * 1.15) * 0.62
	          + cos(Wc.x * -0.74 + Wc.y * 1.31 + Time * 0.83) * 1.11) * Calm;
	// Flatter in the shallows: a ripple needs water under it, and a full
	// swell running up onto a sandbank is the giveaway of a fake sea.
	float Chop = lerp(0.18, 1.0, Deep);
	// NEVER PERFECTLY STILL. Taking the ripple all the way to nothing was
	// tried and is worse than the hatch it cured: this surface is a mirror,
	// and a mirror needs something to reflect. A world built at runtime has no
	// reflection captures in it, so a dead flat mirror has nothing to show and
	// goes BLACK -- the pond photographed afterwards read as a basin of mud.
	// What the ripple was really doing at that distance was catching the sun.
	float Soften = lerp(0.26, 1.0, Calm);
	Nrm = normalize(float3(Ripple * 0.085 * Chop * Soften, 1.0));

	// THE FOAM. Where the water is thin, and wandering with the swell so the
	// edge is never a contour line. Brightest right at the sand.
	//
	// SOFT AT BOTH ENDS. `saturate(Swell * 0.42 + 0.55)` CLIPS: the swell runs
	// past the top and the bottom of that range for most of its cycle, so the
	// lace spent most of its time pinned at nought or at one and what came out
	// was hard-edged bands of white with torn edges -- which photographs as
	// scalloped paper laid on the river rather than as foam. `smoothstep` over
	// the same range eases in and out instead of arriving at a corner.
	//
	// AND A NARROWER BAND. Foam belongs where the water is thin enough to
	// break, which is nearer the sand than 0.30 of the depth; at that width it
	// reached a good way out into the channel.
	// AND NARROWER AGAIN. At 0.20 the lace still reached most of the way across
	// a three-tile river, so two thirds of the water was white.
	float Edge = 1.0 - smoothstep(0.01, 0.12, Deep);
	float Lace = smoothstep(-1.1, 1.1, Swell);
	float Foam = saturate(Edge * (0.40 + 0.60 * Lace));
	Wat = lerp(Wat, float3(0.82, 0.85, 0.83), Foam * 0.48);

	// A MIRROR, except where it is breaking. Foam is the one part of water
	// that is not smooth, which is why it reads as foam and not as paint.
	float Rw = lerp(0.055, 0.020, Deep);
	Rw = lerp(Rw, 0.55, Foam * 0.8);

	// Rain dimples the surface; it does not make it wet.
	Rw = lerp(Rw, Rw + 0.06, saturate(Rain));

	// AND FAR WATER IS A SHEEN, NOT A MIRROR, which is the other half of the
	// same fix. A rough surface spreads one sun into a wide soft band instead
	// of a thousand hard glints, so distant water stays bright and stays water
	// without resolving into a grid. It is also true: a sheet of water a
	// hundred metres off is never mirror-smooth, there is always some wind.
	Rw = lerp(0.26, Rw, Calm);

	Albedo = Wat;
	R = Rw;
}

Normal = Nrm;
Rough = R;
return Albedo;
