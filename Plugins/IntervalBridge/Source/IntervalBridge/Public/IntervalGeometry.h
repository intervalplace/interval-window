// IntervalGeometry.h -- where a tile is, in centimetres.
//
// ONE PLACE, and everything downstream asks it: the ground, the citizens,
// the mobs, the gatherables, the camera. Two actors that each did their own
// multiplication would drift by exactly the amount nobody notices until a
// citizen is standing half a tile inside a wall.
//
// The grid is the world's: +X east, +Y south, origin at tile (0,0). A tile
// is a fixed real size and the whole island is small enough that a single
// origin is fine -- 192x96 tiles at 2 m is under four kilometres across.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "IntervalGeometry.generated.h"

UCLASS()
class INTERVALBRIDGE_API UIntervalGeometry : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/** Centimetres per tile edge. Two metres: a citizen occupies one tile and reads as a person on it. */
	static constexpr float TileSize = 200.f;

	/** Tiles per chunk edge. One draw call's worth of ground, one control texture. */
	static constexpr int32 ChunkTiles = 64;

	/**
	 * How far a building's height may wander either side of whatever the
	 * level gave its walls. ONE NUMBER, here, because the walls and the roof
	 * both have to arrive at the same answer or the thatch floats above the
	 * eaves. A level does not get to set it per kind for exactly that reason.
	 */
	static constexpr float BuildingHeightSpread = 0.12f;

	/**
	 * A stable number for a tile. Used to seed a building from its own corner
	 * IN WORLD TILES, so every chunk that touches that building gets the same
	 * answer, in any order, on any machine -- which is what lets the roof and
	 * the four walls of one house agree about what house they belong to.
	 */
	static uint32 HashTile(int32 TileX, int32 TileY)
	{
		uint32 H = 2166136261u;
		H = (H ^ static_cast<uint32>(TileX)) * 16777619u;
		H = (H ^ static_cast<uint32>(TileY)) * 16777619u;
		return H ^ (H >> 13);
	}

	/**
	 * A stable number in 0..1 for one BUILDING, drawn from the key its walls
	 * and its roof already share. Salt picks which question you are asking of
	 * it, so a house can be a little taller without also being a little
	 * thicker in the same proportion.
	 *
	 * Anything that has to LINE UP -- a roof sitting on the wall it covers --
	 * must ask this the same way in both places rather than each rolling its
	 * own, which is why it lives here beside HashTile and not in whichever
	 * file needed it first.
	 */
	static float BuildingUnit(int64 BuildingKey, uint32 Salt)
	{
		uint32 H = 2166136261u;
		H = (H ^ static_cast<uint32>(BuildingKey & 0xffffffff)) * 16777619u;
		H = (H ^ static_cast<uint32>((BuildingKey >> 32) & 0xffffffff)) * 16777619u;
		H = (H ^ Salt) * 16777619u;
		H ^= H >> 13;
		return static_cast<float>(H & 0xffffu) / 65535.f;
	}

	/**
	 * How tall this building stands, as a multiple of whatever height the
	 * level gave its walls. A street of identical eaves is the thing that
	 * reads as a model kit; a hand's breadth either way is the thing that
	 * reads as a street. THE ROOF CALLS THIS TOO -- that is the whole point
	 * of it being one function.
	 */
	static float BuildingHeight(int64 BuildingKey)
	{
		return BuildingKey
			? 1.f - BuildingHeightSpread + 2.f * BuildingHeightSpread * BuildingUnit(BuildingKey, 5u)
			: 1.f;
	}

	UFUNCTION(BlueprintPure, Category = "Interval|Geometry")
	static float GetTileSize() { return TileSize; }

	UFUNCTION(BlueprintPure, Category = "Interval|Geometry")
	static int32 GetChunkTiles() { return ChunkTiles; }

	/** The centre of a tile, at ground zero. */
	UFUNCTION(BlueprintPure, Category = "Interval|Geometry")
	/**
	 * ---- THE LIE OF THE LAND ----
	 *
	 * This world has no elevation and never has. The engine's terrain answers
	 * six questions -- blocked, water, road, country, spawn, crossing -- and
	 * height is not among them, because nothing in the rules depends on it: a
	 * citizen crosses one tile an interval whether the ground rises or not.
	 *
	 * So the island was drawn as a plane, with a fourteen-centimetre jitter
	 * per tile to keep it from reading as graph paper. On a two-metre tile
	 * that is surface texture, not landscape, and the answer to "do we have
	 * terrain" was honestly no.
	 *
	 * This is the landscape, and it is COSMETIC in the strict sense this
	 * window uses everywhere: it is computed from the tile's own coordinates,
	 * it is never sent anywhere, no deed is derived from it, and a window that
	 * ignored it would draw a different picture of the same world -- which is
	 * exactly what the flat windows do.
	 *
	 * It is a PURE FUNCTION of the tile, which is the whole of why it works.
	 * Chunks are built independently and must agree about a vertex they share;
	 * citizens, props, walls and water must all land on the same ground the
	 * mesh drew. A lookup would need every one of them to hold the terrain;
	 * arithmetic on two integers needs nothing at all.
	 */
	static float Hash01(int32 X, int32 Y)
	{
		uint32 H = static_cast<uint32>(X) * 374761393u
		         + static_cast<uint32>(Y) * 668265263u;
		H = (H ^ (H >> 13)) * 1274126177u;
		return static_cast<float>((H ^ (H >> 16)) & 0xffffffu)
		     / static_cast<float>(0xffffff);
	}

	/** Smoothstep, so an octave has no creases along its lattice. */
	static float Ease(float T) { return T * T * (3.f - 2.f * T); }

	/** One octave of value noise, in tiles, returning -1..1. */
	static float Swell(float X, float Y, float Wavelength)
	{
		const float FX = X / Wavelength;
		const float FY = Y / Wavelength;
		const int32 IX = FMath::FloorToInt(FX);
		const int32 IY = FMath::FloorToInt(FY);
		const float TX = Ease(FX - IX);
		const float TY = Ease(FY - IY);
		const float A = Hash01(IX, IY);
		const float B = Hash01(IX + 1, IY);
		const float C = Hash01(IX, IY + 1);
		const float D = Hash01(IX + 1, IY + 1);
		return FMath::Lerp(FMath::Lerp(A, B, TX), FMath::Lerp(C, D, TX), TY)
		       * 2.f - 1.f;
	}

	/**
	 * THE BARE LAND, before anything people did to it.
	 *
	 * Three octaves: a long swell you notice only by walking it, a rolling
	 * one that makes a field have a far side, and a fine one that keeps a
	 * hillside from looking upholstered. Deliberately gentle -- about five
	 * metres at the extremes, over a hundred and ninety metres of ground.
	 * A top-down camera turns any real gradient into a wall you cannot see
	 * past, and this world is read from above.
	 */
	/**
	 * THE ISLAND'S OWN ELEVATION, as the generator computed it.
	 *
	 * Held here rather than passed about, for the same reason the ground
	 * provider is: everything that stands on a tile needs it, and none of them
	 * should have to be handed a grid. Set once when the bridge says hello.
	 *
	 * `Step` is four tiles, because the field's finest octave is eight wide
	 * and sampling every fourth reproduces it. Between samples it is read
	 * bilinearly, which is how the generator itself reads it.
	 */
	struct FLand
	{
		TArray<uint8> V;
		int32 Step = 4;
		int32 W = 0;
		int32 H = 0;
	};
	static FLand& Land()
	{
		static FLand Held;
		return Held;
	}

	/**
	 * HOW MUCH GROUND A UNIT OF THE FIELD IS WORTH.
	 *
	 * The field runs 0..255 and spans about two hundred and forty of those
	 * across this island. At ten centimetres a unit that is some twenty-four
	 * metres from the fens to the crags, which reads as country from a camera
	 * this high without ever becoming a wall you cannot see past. The number
	 * is a drawing decision and nothing in the world depends on it.
	 */
	static constexpr float PerUnit = 10.f;

	/**
	 * ---- HOW MUCH OF THE LAND'S HEIGHT TO DRAW AT ALL ----
	 *
	 * One at the top, zero for a plane, anything between for a shallower
	 * island. It is a SWITCH rather than a setting because the question it
	 * answers is a matter of looking, not of argument, and it has been asked
	 * three times now: "when it was flat it looked great"; "it doesn't look
	 * like a small hill, it looks weird"; "maybe we just shouldn't draw
	 * elevation at all".
	 *
	 * Nothing in the world objects either way. The elevation field exists to
	 * route roads and nothing else reads it -- see the note over `elevAt` in
	 * terrain-mirror.mjs -- so a flat island and a hilly one are the same
	 * world, drawn two ways. That is exactly the kind of thing that should be
	 * one number somebody can turn while looking at it.
	 *
	 * Set from the look asset; see `LandRelief` in IntervalLook.h.
	 */
	static float& Relief()
	{
		static float Amount = 1.f;
		return Amount;
	}

	static float LandAt(int32 TileX, int32 TileY)
	{
		const FLand& L = Land();
		if (L.W <= 1 || L.H <= 1 || L.V.Num() < L.W * L.H)
		{
			// THE ISLAND HAS NOT ARRIVED YET. A plane is the honest answer:
			// inventing a landscape here would put hills where the roads are
			// not, and then move them when the real field turned up.
			return 0.f;
		}
		const float FX = FMath::Clamp(static_cast<float>(TileX) / L.Step,
			0.f, static_cast<float>(L.W - 1) - KINDA_SMALL_NUMBER);
		const float FY = FMath::Clamp(static_cast<float>(TileY) / L.Step,
			0.f, static_cast<float>(L.H - 1) - KINDA_SMALL_NUMBER);
		const int32 IX = FMath::FloorToInt(FX);
		const int32 IY = FMath::FloorToInt(FY);
		// EASED, LIKE EVERY OTHER LATTICE IN THIS FILE.
		//
		// `Ease` sits twenty lines up with the note "so an octave has no
		// creases along its lattice", and `Swell` has used it since it was
		// written. This, the one lattice that carries the REAL height field,
		// was reading it straight: linear between samples, so every boundary
		// of the four-tile grid was a crease in the land.
		//
		// That is half of what was reported as pale slabs lying in the
		// woods. A plateau with a cut edge reads as a laid thing; the same
		// plateau with a rounded edge reads as a rise.
		const float TX = Ease(FX - IX);
		const float TY = Ease(FY - IY);
		auto At = [&L](int32 X, int32 Y)
		{
			return static_cast<float>(L.V[Y * L.W + X]);
		};
		const float A = At(IX, IY);
		const float B = At(FMath::Min(IX + 1, L.W - 1), IY);
		const float C = At(IX, FMath::Min(IY + 1, L.H - 1));
		const float D = At(FMath::Min(IX + 1, L.W - 1), FMath::Min(IY + 1, L.H - 1));
		const float Units = FMath::Lerp(FMath::Lerp(A, B, TX), FMath::Lerp(C, D, TX), TY);
		// FROM THE MIDDLE OF THE RANGE, so the sea is below zero and the crags
		// above it, and the water plane has an obvious place to sit.
		return (Units - 128.f) * PerUnit * Relief();
	}

	/**
	 * AND WHAT PEOPLE AND WATER DID TO IT.
	 *
	 * A made way is GRADED: somebody levelled it, so it keeps the long swell
	 * and loses the roughness, which is what makes a road read as a road from
	 * above rather than as a ribbon of bumps.
	 *
	 * WATER LIES IN THE BOTTOM OF THINGS. Drawn at the land's own height a
	 * river runs over a ridge, which is the one thing a landscape may never
	 * do. It is pressed into a basin instead, below whatever is around it.
	 *
	 * A FLOOR IS FLAT, because a building is. Its tiles take the long swell
	 * alone, so a hall sits level and the ground meets it rather than the
	 * other way about; without this every cottage on a slope has one corner
	 * in the air.
	 */
	/**
	 * HOW BUILT-UP A TILE IS: 1 inside a settlement, 0 in open country, and a
	 * ring of in-between so there is no step at the edge. Announced by the
	 * ground actor when the settlements arrive, exactly as the height is.
	 *
	 * Absent -- in a test, before `hello` -- everything is open country, which
	 * is the behaviour this had before there was any such thing.
	 */
	using FTownWeight = TFunction<float(int32, int32)>;
	static FTownWeight& TownProvider()
	{
		static FTownWeight Provider;
		return Provider;
	}

	static float TownAt(int32 TileX, int32 TileY)
	{
		const FTownWeight& Provider = TownProvider();
		return Provider ? Provider(TileX, TileY) : 0.f;
	}

	static float GroundAt(int32 TileX, int32 TileY,
		bool bIsWay, bool bIsWater, bool bIsFloor)
	{
		// A GRADED SURFACE TAKES THE AVERAGE OF ITS NEIGHBOURS, which is what
		// levelling ground is: the slope survives and the lumps do not. Read
		// at four tiles, the field's own lattice, so a road follows the hill
		// it was routed along without answering every ripple in it.
		auto Eased = [&]()
		{
			return (LandAt(TileX - 4, TileY) + LandAt(TileX + 4, TileY)
			      + LandAt(TileX, TileY - 4) + LandAt(TileX, TileY + 4)
			      + LandAt(TileX, TileY) * 4.f) * 0.125f;
		};
		// ---- AND A TOWN IS GROUND PEOPLE HAVE LEVELLED ----
		//
		// A settlement came out as a PATCHWORK and was reported as one: "when
		// it was flat it looked great, now with the heightened ground and
		// terrain it just looks weird, as if the terrain wasn't lifted as it
		// should". Three different levellings met in one street -- a way and a
		// floor took the four-tile mean and were flat, ordinary ground kept
		// HALF its roughness, and the roughness it kept is the field's fine
		// octave, which is EIGHT tiles wide. So flat streets and flat building
		// pads sat among lumps the size of a garden, and the eye reads that as
		// plates laid on a rumpled cloth rather than as a hill.
		//
		// A WIDER MEAN, because four tiles cannot average out an eight-tile
		// wave. Sampling at eight as well as four does, and what is left is
		// the broad swell the thirty-two tile octave makes -- so a town still
		// sits on its hillside, it simply stops rippling between the houses.
		//
		// NOTHING IS BEING HIDDEN FROM THE WORLD BY THIS. That field exists to
		// route roads and nothing else reads it: see the note over `elevAt` in
		// terrain-mirror.mjs, where the fine octave is added on purpose so a
		// road keeps correcting instead of running straight for sixty tiles.
		// It was never meant to be looked at.
		const float Town = TownAt(TileX, TileY);
		const float Long = Eased();
		float Base = Long;
		if (Town > 0.f)
		{
			const float Levelled =
				(LandAt(TileX - 8, TileY) + LandAt(TileX + 8, TileY)
			   + LandAt(TileX, TileY - 8) + LandAt(TileX, TileY + 8)
			   + LandAt(TileX - 4, TileY) + LandAt(TileX + 4, TileY)
			   + LandAt(TileX, TileY - 4) + LandAt(TileX, TileY + 4)
			   + LandAt(TileX, TileY) * 4.f) / 12.f;
			Base = FMath::Lerp(Long, Levelled, Town);
		}
		// A WAY IS ASKED ABOUT FIRST, and the order is the whole of why a
		// bridge works: a causey crosses a river, so its tiles are both a way
		// and water, and the water answer would sink the bridge into the
		// thing it exists to cross.
		if (bIsWay || bIsFloor)
		{
			return Base;
		}
		if (bIsWater)
		{
			return Base - 150.f;
		}
		// HALFWAY TO THE GRADED HEIGHT, for ordinary ground.
		//
		// A way and a floor are levelled and the land beside them is not, so
		// wherever they meet there is a step exactly as big as the roughness
		// the levelling removed. Around a cottage that reads as a lip of bare
		// ground standing proud of the grass.
		//
		// Blending the land halfway toward the same eased height halves every
		// one of those steps at once, without needing to know how far a tile
		// is from the nearest road -- which is the honest version of this and
		// costs a distance field over the whole island. The hills keep their
		// shape; only the last hand's breadth of roughness goes.
		// AND IN A TOWN IT GOES ALL THE WAY. Half is right for open country,
		// where the land is the land; inside a settlement the ground between
		// the houses is graded the same as the street, which is what stops the
		// patchwork. The ring in `TownAt` walks this from 1 back to 0.5 rather
		// than stepping, so a town has no lip around it.
		// ---- AND A HAND'S BREADTH OF RELIEF, SO A PLATEAU IS NOT A TABLE ----
		//
		// The height field is a BYTE every four tiles. Wherever two
		// neighbouring samples land on the same byte, the interpolation
		// between them is exactly flat, and what the eye gets is an eight
		// metre table standing a finger above the grass: at noon its top
		// faces the sun and reads as a pale slab, and under a low sun it
		// throws a shadow. They are all over the open country and they were
		// taken for laid stone.
		//
		// Easing the lattice rounded their edges and could not help with the
		// middle, because a flat thing interpolated smoothly is still flat.
		// What is missing is detail finer than the field can hold, so it is
		// put back here: two octaves, together under one byte of the field's
		// own resolution, which means this can never change the shape of a
		// hill. It only stops the level places being mathematically level.
		//
		// NOT IN A TOWN, and not on a way or a floor, which return above.
		// Ground people have levelled is supposed to be flat; that is the
		// whole of what `Town` is for, and putting ripples back between the
		// houses would undo it.
		const float Micro = (Swell(static_cast<float>(TileX),
		                           static_cast<float>(TileY), 7.f) * 0.90f
		                   + Swell(static_cast<float>(TileX),
		                           static_cast<float>(TileY), 3.f) * 0.35f)
		                  * PerUnit * Relief() * (1.f - Town);
		return FMath::Lerp(LandAt(TileX, TileY), Base,
			FMath::Lerp(0.5f, 1.0f, Town)) + Micro;
	}

	/**
	 * ---- WHO KNOWS WHAT A TILE IS MADE OF ----
	 *
	 * The landscape is arithmetic on the coordinates and needs nothing, but
	 * three kinds of tile bend it: a way is graded, water lies in a basin, a
	 * floor is level. Only the ground actor knows which a tile is, because it
	 * holds the chunks, and `TileToWorld` is called from half this plugin --
	 * by citizens, beasts, walls, fences, props, the gate and the sun.
	 *
	 * Threading the ground through all of them would be a parameter added to
	 * thirty signatures to answer one question. Instead the ground announces
	 * itself here when it starts, and everything that places a thing on a tile
	 * gets the right height without knowing anything new.
	 *
	 * Absent -- in a test, before the level is up, in a headless run -- the
	 * bare land is the answer, which is correct everywhere except on the three
	 * kinds of tile above.
	 */
	using FGroundHeight = TFunction<float(int32, int32)>;
	static FGroundHeight& GroundProvider()
	{
		static FGroundHeight Provider;
		return Provider;
	}

	/** The ground's height at a tile, in centimetres. */
	static float GroundZ(int32 TileX, int32 TileY)
	{
		const FGroundHeight& Provider = GroundProvider();
		return Provider ? Provider(TileX, TileY) : LandAt(TileX, TileY);
	}

	static FVector TileToWorld(int32 TileX, int32 TileY)
	{
		return FVector((TileX + 0.5f) * TileSize, (TileY + 0.5f) * TileSize,
			GroundZ(TileX, TileY));
	}

	/** The corner, for chunk origins and anything that tiles. */
	UFUNCTION(BlueprintPure, Category = "Interval|Geometry")
	static FVector TileCornerToWorld(int32 TileX, int32 TileY)
	{
		return FVector(TileX * TileSize, TileY * TileSize, 0.f);
	}

	UFUNCTION(BlueprintPure, Category = "Interval|Geometry")
	static void WorldToTile(const FVector& Location, int32& OutTileX, int32& OutTileY)
	{
		OutTileX = FMath::FloorToInt(Location.X / TileSize);
		OutTileY = FMath::FloorToInt(Location.Y / TileSize);
	}

	/** Which chunk a tile belongs to. */
	UFUNCTION(BlueprintPure, Category = "Interval|Geometry")
	static FIntPoint ChunkOf(int32 TileX, int32 TileY)
	{
		return FIntPoint(FMath::FloorToInt(static_cast<float>(TileX) / ChunkTiles),
		                 FMath::FloorToInt(static_cast<float>(TileY) / ChunkTiles));
	}

	/**
	 * Cosmetic relief, in centimetres, from a tile's scatter seed.
	 *
	 * The world is flat: it has tiles, not heights, and nothing a citizen can
	 * do depends on elevation. This is a lie told for the camera's sake, and
	 * it is told IDENTICALLY IN EVERY WINDOW because it is a pure function of
	 * the seed byte the bridge sent. Two citizens looking at the same rise see
	 * the same rise. Keep the amplitude small enough that it never reads as
	 * cover, a wall, or anywhere you could stand.
	 */
	UFUNCTION(BlueprintPure, Category = "Interval|Geometry")
	static float ReliefFromSeed(uint8 Seed, bool bIsWay, float Amplitude = 14.f)
	{
		// A CHUNK CAN NOW SEE PAST ITS OWN EDGE, so this is no longer zero.
		//
		// It was. AIntervalChunk gives a vertex the average of the tiles that
		// meet at it, and a chunk used to hold only its own: at a shared edge
		// the chunk on the left averaged the last tile it had and the chunk on
		// the right averaged the first tile IT had, so the two disagreed about
		// the height of a vertex they both own and the ground split along every
		// chunk boundary -- a seam every 64 tiles, the full width of the island.
		//
		// The fix was never a smaller number. It was the one-tile skirt the
		// bridge now sends with every chunk: both sides read the same four
		// tiles and agree exactly. Keep the amplitude small enough that it
		// never reads as cover, a wall, or anywhere you could stand.

		if (bIsWay)
		{
			// a made way is graded: people flattened it, so the window does too
			return 0.f;
		}
		return ((static_cast<float>(Seed) / 255.f) - 0.5f) * 2.f * Amplitude;
	}
};
