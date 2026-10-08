// WIND, AS A VERTEX OFFSET.
//
// A meadow where every blade stands dead still is the tell that gives a
// rendering away faster than anything else in it, and this one had ninety
// thousand blades all rigid. This bends them.
//
// IT IS ITS OWN NODE, and it has to be. The material's other Custom node reads
// a vertex interpolator to find out where it sits on a figure, which makes it a
// PIXEL-shader node, and world position offset is a VERTEX-shader output -- so
// one node cannot do both. That is written down at length in person_mat.hlsl;
// this is the other half of it.
//
// Nothing sways unless a level says it does: `Sway` is nothing by default, so
// people and anvils and walls are unaffected and only what a level calls a
// plant is moved.

// HOW FAR UP THE PLANT THIS VERTEX IS, in metres, from the mesh's own origin.
//
// `PreSkinnedPosition`, NOT `LocalPosition`. Local position is fine on a static
// mesh and breaks the material on a SKELETAL one -- and it breaks it silently:
// the recompile reports clean, every tree in the world renders correctly, and
// every person turns the default grey, because only the skeletal permutation
// failed. Pre-skinned position is the vertex before any bone moved it, which
// is the same thing on a tree and the right thing on a body.
// These meshes stand on the ground at z = 0, so local Z is height above root:
// a trunk hardly moves, a leaf at the top moves most. `Stiff` is the height at
// which a plant is fully bending -- small for grass, large for an oak.
float Up   = max(Local.z, 0.0) / 100.0;
float Bend = pow(saturate(Up / max(Stiff, 0.05)), 1.7);

// THE SAME WIND EVERYWHERE, so a field leans together -- BUT NOT IN ONE PIECE.
//
// Phase comes from WORLD position, not from the mesh's own, or every clump
// bends identically in place and the field pulses rather than ripples.
//
// THIS HAS NOW BEEN CALLED AN OCEAN TWICE, and the second time it was still an
// ocean after the wavelengths had been shortened fivefold -- which is how the
// real fault got found, because shortening the waves did not touch it.
//
// A ZERO-MEAN SINE IS THE BUG. The lean was `Gust * Dir` with Gust swinging
// evenly about nought, so every blade travelled the same distance UPWIND as
// downwind, over and over, at a fixed rate. Grass does not do that. Grass
// leans one way -- downwind -- and what varies is HOW FAR, between a light
// lean and a hard one. A field of blades rocking symmetrically through the
// vertical is, to the eye, a surface oscillating about a rest plane, and a
// surface oscillating about a rest plane is water. Shorter waves only made it
// choppier water.
//
// AND THE WAVES WERE CRAWLING. The dominant term moved at about a metre a
// second and the terms ran in DIFFERENT directions, one of them upwind of the
// others, so they beat against each other into a standing pattern that sat
// still in the field and breathed. Swell, again, and for the second reason.
//
// So: the strength is one-signed and never lets a blade past upright; every
// front travels WITH the prevailing wind; and they travel at something like
// the speed of the wind that is carrying them, which over a meadow is metres
// per second, not centimetres.

// The prevailing wind. One direction for the whole island, because a wind that
// blows four ways at once reads as a shiver rather than as weather.
float2 Dir  = normalize(float2(0.82, 0.57));
float2 Side = float2(-Dir.y, Dir.x);

// In METRES, along the wind and across it. Working in the wind's own frame is
// what lets a gust be long across the field and short along it, which is the
// shape a gust front actually has.
float2 Metres = World.xy * 0.01;
float  Along  = dot(Metres, Dir);
float  Across = dot(Metres, Side);

// TWO GUSTS, BOTH RUNNING DOWNWIND. Nine metres at six metres a second, and
// three and a half at seven -- so they overtake each other slowly instead of
// standing still against each other. The small `Across` terms bow the fronts
// so they are not infinite straight lines ruled over the field.
// AND NOT SO MUCH OF IT. Read from above, a field under this was a SEA: the
// two fronts swung the lean across its whole range, from a quarter to a full
// one, and they did it coherently over nine metres, so a camera looking down
// at forty metres of meadow saw four or five stripes of grass rolling through
// it in step. That is what an ocean looks like and it is not what a meadow
// looks like.
//
// Three changes, all of them to the COHERENT part, because the coherent part
// is the whole of what reads as a wave:
//
//   the amplitudes halve, so a gust is a change in the wind rather than the
//   difference between calm and gale;
//   the fronts lengthen (0.70 -> 0.38 along the wind), so a field holds two
//   of them instead of five and they stop reading as stripes;
//   and the floor comes up in `Push` below, which narrows the swing again.
//
// What is NOT reduced is `Flut`, the per-plant term. That is the part with no
// pattern in it, and it is what keeps the field alive once the rolling is
// gone. Taking the wave out of grass should leave it moving, not still.
float Gust = 0.50
           + 0.14 * sin(Along * 0.38 - Time *  3.10 + Across * 0.09)
           + 0.11 * sin(Along * 0.95 - Time *  8.40 + Across * 0.28);
Gust = saturate(Gust);

// AND EVERY PLANT ON ITS OWN. Off its own half-metre of ground, so neighbours
// are never in step. This is most of what separates grass from cloth: a blade
// is light enough to be moved by the turbulence inside a gust and not only by
// the gust.
float Own   = frac(sin(dot(floor(World.xy * 0.02), float2(12.9898, 78.233))) * 43758.5);
float Flut  = sin(Time * (5.5 + 3.4 * Own) + Own * 6.283);

// `Gale` is the world's weather; `Sway` is how much this plant gives to it.
// ONE-SIGNED: a quarter lean at the quietest and a full one in a gust, and
// never a negative, so nothing ever leans into the wind.
// The floor was a quarter, so a gust front multiplied the lean by four as it
// passed. Over half now: a gust is felt as a change rather than watched as a
// swell.
float Push = Sway * Bend * (0.55 + 0.45 * Gust) * (0.28 + 0.80 * saturate(Gale));

// A little sideways flutter, which is the only part that is allowed to change
// sign, and it is small: it makes a blade shiver rather than the field rock.
float Wag = Sway * Bend * Flut * 0.16 * (0.28 + 0.80 * saturate(Gale));

// SOMEBODY WALKING THROUGH IT.
//
// `Walker` is where the citizen is standing, set once a frame by the hour and
// read by every plant on the island. Within about a metre and a half of a pair
// of boots the grass is pushed radially away and flattened a little, and it
// springs back behind them because the only thing remembered is where they are
// NOW. It costs one vector and it is the difference between walking through a
// meadow and walking through a photograph of one.
//
// AND ONLY A PLANT IS TRODDEN. `Sway` is the one thing in this material that
// says "this surface is vegetation", and the tread was not asking. A citizen's
// tunic has Sway 0 -- so it does not bend in the wind, correctly -- but it was
// standing at EXACTLY the walker's position, because the walker IS that
// citizen. Tread came out 1, the shove came out at forty-six centimetres
// straight out along every vertex, and the man in the market place was a green
// balloon with boots. The push has to be gated by the same thing the wind is.
float2 Away = World.xy - Walker.xy;
float  Near = length(Away);
float  Tread = 1.0 - smoothstep(40.0, 165.0, Near);
float  Plant = saturate(Sway * 0.25);
if (Tread > 0.001 && Near > 0.001 && Plant > 0.001)
{
	// Flat near the feet and standing again at the edge of the circle, and
	// only the parts of the plant that are off the ground are moved at all.
	float Shove = Tread * Bend * 46.0 * Plant;
	return float3((Away / Near) * Shove, -Tread * Bend * 18.0 * Plant)
	     + float3((Dir * Push + Side * Wag) * (1.0 - Tread * 0.7), 0.0);
}

// And a little lift, so a blade bends rather than shearing sideways.
return float3(Dir * Push + Side * Wag, -Push * 0.18);
