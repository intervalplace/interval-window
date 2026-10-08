// IntervalChunk.h -- one rectangle of ground.
//
// The mesh is a flat grid with cosmetic relief. What each tile IS lives in a
// control texture rather than in geometry or in C++: one texel per tile,
// nearest-sampled, R = terrain code, G = made way, B = scatter seed. The
// material reads that texel and chooses a layer.
//
// This is why the project can be told about a terrain it has never heard of
// and keep drawing: an unknown code lands on the fallback layer and the
// ground is still there. The alternative -- a mesh section per terrain type,
// built from a C++ switch -- would have to be edited and recompiled every
// time the generator learns a new word.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IntervalTypes.h"
#include "IntervalScatter.h"
#include "IntervalSpan.h"
#include "IntervalStructures.h"
#include "IntervalRoof.h"
#include "IntervalChunk.generated.h"

class UProceduralMeshComponent;
class UTexture2D;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class UInstancedStaticMeshComponent;

UCLASS()
class INTERVALBRIDGE_API AIntervalChunk : public AActor
{
	GENERATED_BODY()

public:
	AIntervalChunk();

	/** Build, or rebuild in place when the same ground arrives again. */
	/**
	 * Build, or rebuild in place when the same ground arrives again.
	 *
	 * ScatterByCode is indexed by the terrain code itself, resolved from the
	 * names the bridge sent this session. The chunk never learns what a code
	 * means; it is handed a look for each one and an empty look for the rest.
	 */
	void Build(const FIntervalTerrainChunk& Chunk, UMaterialInterface* GroundMaterial,
		const TArray<FIntervalScatterKind>& ScatterByCode,
		const FIntervalScatterKind& SpineScatter,
		const TArray<FIntervalRoofKind>& RoofByCode,
		const TArray<uint8>& ThresholdByCode,
		const TArray<uint8>& ShapeByCode, const FIntervalSpan& SpanLook,
		uint8 RiverCode, bool bAffectIndirect);

	/**
	 * WHAT THIS TILE DOES TO THE LAND UNDER IT: 0 leaves it alone, 1 is water
	 * and lies in a basin, 2 is a floor and is levelled. Indexed by the
	 * world's own tile code, worked out once by the ground from the tile
	 * names, because a chunk has the codes and not the words.
	 */
	static constexpr uint8 ShapeLand = 0;
	static constexpr uint8 ShapeWater = 1;
	static constexpr uint8 ShapeFloor = 2;
	/**
	 * 3 IS A DECK: a road laid over water, which is both and neither.
	 *
	 * It stands where a way stands, because that is what a citizen walks on
	 * and it is the reason a bridge works at all -- ask the water question
	 * first and the crossing sinks into the thing it exists to cross. But it
	 * is DRAWN as the channel it spans, with the slab and the piers built on
	 * top as separate stone, so that a bridge has an underside.
	 */
	static constexpr uint8 ShapeDeck = 3;

	/** Tile coordinates of this chunk's corner. */
	UFUNCTION(BlueprintPure, Category = "Interval")
	FIntPoint GetOrigin() const { return FIntPoint(OriginX, OriginY); }

	/** The terrain code at a world tile, or 255 if that tile is not in this chunk. */
	UFUNCTION(BlueprintPure, Category = "Interval")
	uint8 GetCodeAtTile(int32 TileX, int32 TileY) const;

	/**
	 * Which building covers a world tile, as that building's own seed, or 0
	 * where nothing is built. The seed is a hash of the building's corner in
	 * WORLD tiles, so it is the same answer whichever chunk is asked and in
	 * whatever order the chunks arrived.
	 *
	 * This exists because the things standing on a tile are drawn from told
	 * nodes, which know a wall is at a tile but not whether that tile is part
	 * of a house or the wall of a yard. Those want to look completely
	 * different, and only the footprint knows which is which.
	 */
	UFUNCTION(BlueprintPure, Category = "Interval")
	uint8 GetBuildingSeedAtTile(int32 TileX, int32 TileY) const;

	/**
	 * WHICH building covers a world tile -- its corner, packed -- or 0 for
	 * none. A seed is enough to make two houses look different; it is not
	 * enough to say that this wall and that anvil are the same building,
	 * because a byte collides. The key does not.
	 */
	int64 GetBuildingKeyAtTile(int32 TileX, int32 TileY) const;

	/** How high the roof stands over a world tile, or a negative number. */
	float GetRoofTopAtTile(int32 TileX, int32 TileY) const;

	/** The scatter seed at a world tile. Decoration reads this and nothing else. */
	UFUNCTION(BlueprintPure, Category = "Interval")
	uint8 GetSeedAtTile(int32 TileX, int32 TileY) const;

	UFUNCTION(BlueprintPure, Category = "Interval")
	bool IsWayAtTile(int32 TileX, int32 TileY) const;

	/** Ground height at a world position, for putting anything else on top of it. */
	UFUNCTION(BlueprintPure, Category = "Interval")
	float GetReliefAt(int32 TileX, int32 TileY) const;

	/**
	 * THE BUILDING THE CITIZEN IS STANDING IN, WHICH IS NOT DRAWN.
	 *
	 * A town from above is roofs, and a citizen inside one is under it: you
	 * cannot see where you are or where the door was. Nothing in this window
	 * used to lift, so navigating a town meant walking by memory.
	 *
	 * Zero is "draw everything", which is the ordinary case and what every
	 * chunk holds until somebody steps indoors.
	 */
	TSet<int64> HideBuildings;

	/** Set them, and rebuild the roofs if the set actually changed. */
	void SetHideBuildings(TSet<int64>&& Keys);

	/**
	 * THE TILES SOMEBODY HAS PLOUGHED, which grow no grass.
	 *
	 * A plot is a NODE and the scatter is laid by the CHUNK off the ground's
	 * own code, so the two knew nothing about each other and wild grass came
	 * up through every furrow on the island. Ploughed ground is bare ground:
	 * that is what ploughing is for.
	 *
	 * In world tiles, not local ones, because the ground actor collects them
	 * from the frame and does not know this chunk's corner.
	 */
	void SetTilled(TSet<FIntPoint>&& Tiles);


protected:
	UPROPERTY(VisibleAnywhere, Category = "Interval")
	TObjectPtr<UProceduralMeshComponent> Mesh;

	UPROPERTY(Transient)
	TObjectPtr<UTexture2D> ControlTexture;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> MaterialInstance;

	/** One pool per terrain code that grows anything. Emptied and refilled on rebuild. */
	UPROPERTY(Transient)
	// Keyed by ground code AND which variant of it, since one instanced
	// component draws exactly one mesh. See FIntervalScatterKind::Variants.
	TMap<uint32, TObjectPtr<UInstancedStaticMeshComponent>> ScatterPools;

	/** The roofs of this chunk, as one mesh: gables, hips and all. */
	UPROPERTY(VisibleAnywhere, Category = "Interval")
	TObjectPtr<UProceduralMeshComponent> RoofMesh;

	/** What `BuildRoofs` was last given, so lifting a roof needs no refounding. */
	TArray<FIntervalRoofKind> RoofKindsWere;
	TArray<uint8> ThresholdWere;

	/** ...and what `BuildScatter` was last given, for the same reason. */
	TArray<FIntervalScatterKind> ScatterWere;
	FIntervalScatterKind SpineWere;
	TSet<FIntPoint> Tilled;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInterface> RoofMaterial;

private:
	void BuildControlTexture(const FIntervalTerrainChunk& Chunk);
	void BuildScatter(const TArray<FIntervalScatterKind>& ScatterByCode,
		const FIntervalScatterKind& SpineScatter);
	void BuildRoofs(const TArray<FIntervalRoofKind>& RoofByCode,
		const TArray<uint8>& ThresholdByCode);
	void BuildMesh(const FIntervalTerrainChunk& Chunk);

	/** The deck slabs and piers of any crossing that passes through here. */
	void BuildSpans();
	int32 IndexOf(int32 TileX, int32 TileY) const;

	/**
	 * Level every building onto one height and blend the land into it.
	 * Runs before the ground mesh, because the ground mesh asks.
	 */
	void BuildFloors(const TArray<FIntervalRoofKind>& RoofByCode);

	int32 OriginX = 0;
	int32 OriginY = 0;
	int32 Width = 0;
	int32 Height = 0;

	/**
	 * Border the planes carry beyond the interior, and the row length that
	 * comes with it. Local(x, y) reads the planes in INTERIOR coordinates and
	 * will happily take -1 or Width: that is the whole point of the skirt.
	 */
	int32 Skirt = 0;
	int32 Stride = 0;

	FORCEINLINE bool HasLocal(int32 LocalX, int32 LocalY) const
	{
		return LocalX >= -Skirt && LocalY >= -Skirt
			&& LocalX < Width + Skirt && LocalY < Height + Skirt;
	}

	FORCEINLINE int32 Local(int32 LocalX, int32 LocalY) const
	{
		return (LocalY + Skirt) * Stride + (LocalX + Skirt);
	}

	/**
	 * THE FLOOR UNDER A BUILDING, FLAT, one value a tile over the skirted grid.
	 *
	 * A building is levelled onto one height, because a building has a floor
	 * and a floor is flat. The GROUND under it was not: `GroundAt` answered
	 * each floor tile with its own eased height, which still follows the hill,
	 * so on a slope the walls stood level over a floor that fell away beneath
	 * them. Measured on the terrace west of Anchor: eight and a half metres of
	 * drop under one continuous roof. What it looks like is a hall perched on
	 * a warped mesa, which is how it was reported.
	 *
	 * So the floor is decided ONCE per building, here, before the ground mesh
	 * is built, and both the ground and the roof read it -- which is the only
	 * arrangement in which they cannot disagree.
	 *
	 * `NoFloor` for every tile no building covers. A real floor can be far
	 * below sea level, so the sentinel has to be past anything the elevation
	 * field can reach; see AIntervalGround::NoRoof for the same argument.
	 */
	static constexpr float NoFloor = -1.e7f;
	TArray<float> FloorZ;

	TArray<uint8> Codes;
	TArray<uint8> Ways;

	/** Water under each tile, which the ground kind hides on a crossing. */
	TArray<uint8> Wet;

	/** The island's spine, one byte a tile. See FIntervalTerrainChunk::Spine. */
	TArray<uint8> Spine;
	TArray<uint8> Seeds;

	/** Tile code -> what it does to the land. See the constants above. */
	TArray<uint8> Shapes;

	/**
	 * The ground height at a tile of this chunk, in centimetres: what anything
	 * standing here stands ON. A deck is a road and answers as one.
	 */
	float HeightOfTile(int32 WorldX, int32 WorldY, int32 Index) const;

	/**
	 * THE SAME HEIGHT, FOR THE TRIANGLES ONLY, which is where a bridge comes
	 * from.
	 *
	 * These two were one function, and that is why this window had no bridges.
	 * The height a thing STANDS at and the height the ground is DRAWN at are
	 * the same number everywhere on the island except under a crossing, where
	 * the road is held up in the air by stone and the river runs beneath it.
	 * Splitting them costs one call site and buys the whole thing: the mesh
	 * digs the channel out, the deck is built over it, and nothing that walks,
	 * stands, floats, grows or is placed notices any of it -- because none of
	 * them ask this question.
	 *
	 * Cosmetic by construction. If it ever answers a question about where
	 * something IS, this has become a second opinion about the world and the
	 * bug will be a citizen standing in a river.
	 */
	float DrawHeightOfTile(int32 LocalX, int32 LocalY, int32 Index) const;

	/** The surface a citizen's feet are on: the drawn one, except on a deck. */
	float StandHeightOfTile(int32 LocalX, int32 LocalY, int32 Index) const;

	/** Whether a tile of the skirted grid is a decked crossing. */
	bool IsDeckLocal(int32 LocalX, int32 LocalY) const;

	/** And whether there is water under it. See FIntervalTerrainChunk::Wet. */
	bool IsWetLocal(int32 LocalX, int32 LocalY) const;

	/** Whether any tile here is, so the rest of it costs nothing anywhere else. */
	bool bHasDeck = false;

	/** What a crossing is made of, and the pools its stone is drawn from. */
	UPROPERTY(Transient)
	FIntervalSpan Span;

	/**
	 * The world's code for river, or 255 where this founding has none.
	 *
	 * A DECK IS PAINTED AS THE WATER IT CROSSES. The control texture carries
	 * one terrain code a tile and the material colours the ground from it, so
	 * a bridge tile left as itself paints flagstones across the dug channel --
	 * paving at the bottom of a river, with the real deck floating over it.
	 */
	uint8 RiverCode = 255;

	UPROPERTY(Transient)
	TObjectPtr<UInstancedStaticMeshComponent> DeckPool;

	UPROPERTY(Transient)
	TObjectPtr<UInstancedStaticMeshComponent> PierPool;

	/**
	 * THE PARAPET, WHICH IS AUTHORED AND NOT BORROWED.
	 *
	 * The kit's deck section has a kerb along each edge and it is nine and a
	 * half centimetres tall -- right at the scale the piece was drawn for and
	 * invisible from this camera, which looks down on the island from a long
	 * way up. A bridge seen from above with nothing along its sides reads as a
	 * paved causeway, which is the complaint this whole piece of work started
	 * from. No kit in this project has a parapet, a balustrade or a low wall,
	 * so the wall is built here: a run of stone along each side of the span,
	 * flat-shaded like everything else, in the deck's own material.
	 */
	UPROPERTY(VisibleAnywhere, Category = "Interval")
	TObjectPtr<UProceduralMeshComponent> SpanMesh;

	/** Interior only, Width x Height: which building covers each tile, 0 for none. */
	TArray<int64> BuildingKey;

	/**
	 * How high the roof is over each tile, in centimetres, or a negative
	 * number where nothing covers it.
	 *
	 * KEPT BECAUSE THE ROOF BUILDER ALREADY KNOWS. The gable's height at any
	 * point is worked out from the building's span and ridge while the surface
	 * is being laid; anything else that wants it -- a chimney, above all --
	 * would otherwise have to repeat that arithmetic from outside and would
	 * drift away from it the first time the pitch was edited.
	 */
	TArray<float> RoofTop;
};
