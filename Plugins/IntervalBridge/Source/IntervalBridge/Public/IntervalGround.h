// IntervalGround.h -- asks for the ground the citizen is standing on, and
// throws away the ground they have walked out of.
//
// Drop one of these in the level. It waits for the bridge, follows `me`, and
// keeps a square of chunks around them. Nothing in here predicts, guesses or
// generates: every tile it draws was computed by terrain-mirror.mjs, which
// is checked against the engine tile for tile.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IntervalTypes.h"
#include "IntervalScatter.h"
#include "IntervalStructures.h"
#include "IntervalRoof.h"
#include "IntervalGround.generated.h"

class AIntervalChunk;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FIntervalGroundChanged);
class UIntervalBridgeSubsystem;
class UMaterialInterface;

UCLASS()
class INTERVALBRIDGE_API AIntervalGround : public AActor
{
	GENERATED_BODY()

public:
	AIntervalGround();

	/** The one material every chunk instances. Set it in the level. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<UMaterialInterface> GroundMaterial;

	/** A look asset to take the tables from; unset, the conventional one. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (DisplayName = "Look"))
	TObjectPtr<class UIntervalLook> Look_;

	/** Rings of chunks kept around the citizen. 1 is a 3x3 of 64-tile chunks. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0", ClampMax = "4"))
	int32 Rings = 1;

	/** Draw the whole island regardless of where the citizen is. For the chart, and for screenshots. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	bool bWholeIsland = false;

	/**
	 * What grows on each kind of ground, keyed by the world's own word for it.
	 * A word with no entry grows nothing, which is the right answer for ground
	 * this window has never been told about.
	 *
	 * Keyed by NAME rather than by code on purpose: a code is an index into a
	 * list the bridge builds at runtime and may append to, so level data keyed
	 * by number would silently mean something else the day a founding adds a
	 * terrain. The name is what the world actually calls it.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TMap<FName, FIntervalScatterKind> Scatter;

	/**
	 * Whether the ground CONTRIBUTES to Lumen's indirect lighting. It always
	 * receives either way.
	 *
	 * Off by default, and not as a performance dodge. A chunk is a flat
	 * 128 m square, so Lumen's surface cache covers the whole of it with one
	 * very coarse card and then reads the indirect term back out of it -- which
	 * is the soft blotching that has been in every wide shot since the hour was
	 * committed. A flat plane bouncing light onto itself contributes almost
	 * nothing worth having; taking it out of the Lumen scene costs a little
	 * green bounce onto the walls above it and removes the artefact.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	bool bGroundAffectsIndirect = false;

	/**
	 * Which building covers a world tile, as that building's own seed, or 0
	 * where nothing is built. Asked by whatever draws the things standing on
	 * the ground, which knows a wall is at a tile but not whether that tile
	 * belongs to a house or to the wall of a yard.
	 */
	UFUNCTION(BlueprintPure, Category = "Interval")
	uint8 BuildingSeedAtTile(int32 TileX, int32 TileY) const;

	/**
	 * What the world calls the ground at a world tile, or NAME_None where no
	 * chunk holds it yet. The WORD, not a code: a code is this session's
	 * index and means nothing outside it, and the things that ask this --
	 * what to play, what to breathe -- are keyed by the world's own word.
	 */
	UFUNCTION(BlueprintPure, Category = "Interval")
	FName GroundWordAtTile(int32 TileX, int32 TileY) const;

	/**
	 * THE GROUND'S HEIGHT AT A TILE, for everything that stands on it.
	 *
	 * The landscape is a pure function of the tile (see
	 * `UIntervalGeometry::GroundAt`), and the only thing that cannot be worked
	 * out from the coordinates alone is whether the tile is a way, water or a
	 * floor. This asks the chunk that owns it, and falls back to the bare land
	 * for ground that has not streamed in yet -- which is right: a citizen
	 * walking into an unloaded chunk should rise with the hill they are on,
	 * not step onto a plane.
	 */
	UFUNCTION(BlueprintPure, Category = "Interval")
	float GroundHeightAtTile(int32 TileX, int32 TileY) const;

	/**
	 * The raw terrain code on a tile, or 255 where no chunk is loaded.
	 *
	 * `GroundWordAtTile` answers with the world's NAME for it, which is what
	 * anything reasoning about terrain wants. The minimap wants the code: it
	 * paints a hundred and thirty tiles a side, once a second, and turning
	 * each of them into an FName and back is a great deal of work to arrive
	 * at a colour.
	 */
	uint8 CodeAtTile(int32 TileX, int32 TileY) const;

	/** WHICH building covers a world tile, or 0. See AIntervalChunk. */
	int64 BuildingKeyAtTile(int32 TileX, int32 TileY) const;

	/**
	 * How high the roof stands over a world tile, in centimetres, or a
	 * negative number where nothing covers it or no chunk holds it yet.
	 * Asked by anything that has to stand ON a roof -- a chimney.
	 */
	UFUNCTION(BlueprintPure, Category = "Interval")
	float RoofTopAtTile(int32 TileX, int32 TileY) const;

	/**
	 * WHAT "NO ROOF" LOOKS LIKE, and why it is not minus one.
	 *
	 * It was minus one, and callers asked `>= 0.f`. That worked while every
	 * roof in the world was built up from Z = 0, so every roof top was a
	 * positive number. Roofs stand on the ground now, and most of Anchor is
	 * below sea level, so a perfectly real roof can report a negative height
	 * -- at which point "is there a roof over this tile" started answering no
	 * for the low half of every settlement, and the rain came through it.
	 *
	 * So the sentinel is a number no ground on this island can reach: the
	 * elevation field spans about twenty-four metres either side of nothing.
	 */
	static constexpr float NoRoof = -1.e7f;

	/** Whether anything at all covers this tile. Prefer this to comparing. */
	UFUNCTION(BlueprintPure, Category = "Interval")
	bool IsRoofedAtTile(int32 TileX, int32 TileY) const
	{
		return RoofTopAtTile(TileX, TileY) > NoRoof * 0.5f;
	}

	/**
	 * Whether this tile's roof is BEING DRAWN, which is not the same question.
	 *
	 * `IsRoofedAtTile` answers out of the world's own data, and it is right to:
	 * a citizen who walks into a house is indoors whether or not the window has
	 * lifted the roof off to let them see, and the things that ask it -- the
	 * lamp, the shelter, the rain -- all want that answer.
	 *
	 * A chimney is the other question. A stack stands ON the roof, so when the
	 * roof came off for navigation the chimney was left hanging in the air over
	 * an open shell, with its smoke still pouring out of nothing. Photographed
	 * from the window in Anchor: the building open to the sky and its flue
	 * floating above the gap where the ridge had been.
	 */
	bool RoofShownAtTile(int32 TileX, int32 TileY) const;

	/**
	 * Ground arrived or was rebuilt. Anything that asked BuildingSeedAtTile
	 * before the chunk existed got told 0, and needs to ask again.
	 */
	UPROPERTY(BlueprintAssignable, Category = "Interval")
	FIntervalGroundChanged OnGroundChanged;

	/**
	 * What roofs each kind of ground, keyed by the world's own word for it.
	 *
	 * A ROOF IS NOT INVENTED HERE. The generator already answers, per tile,
	 * whether a citizen standing on it is indoors -- that is what makes a tile
	 * a room's floor rather than the lane outside it. So the footprint of
	 * every building on the island is already in the terrain plane, told, and
	 * a roof is that footprint raised to the height of the walls around it.
	 * Nothing measures a building, guesses its extent, or decides where one
	 * ends and the next begins; each tile roofs itself and they meet.
	 *
	 * One slab per tile, exactly one tile wide, so neighbours tile edge to
	 * edge with nothing overlapping and no coplanar faces to fight.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TMap<FName, FIntervalRoofKind> Roofs;

	/**
	 * ---- AND WHY THERE IS NO CONSOLE COMMAND FOR THE HEIGHT DIAL ----
	 *
	 * One was written: `SetLandRelief 0` set the dial, destroyed every chunk
	 * and asked for them again, so the island's height could be turned while
	 * looking at it. It cannot work, and the reason is worth keeping.
	 *
	 * The BRIDGE decides what ground to send and does not send the same chunk
	 * twice. So the window drops its chunks, asks again, and is told nothing,
	 * because from the bridge's side that ground was delivered already. What
	 * is left is a console command that permanently removes the world.
	 *
	 * `LandRelief` on the look asset does the same job at the next play, which
	 * is where it belongs until the bridge has a word for "send it again".
	 */

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	UFUNCTION()
	void HandleFrame();

	UFUNCTION()
	void HandleChunk(const FIntervalTerrainChunk& Chunk);

	UFUNCTION()
	void HandleReady();

private:
	/**
	 * The buildings whose roofs are suppressed this frame, as computed for the
	 * occlusion rule in HandleFrame. Kept so that anything standing on a roof
	 * can ask whether that roof is still there.
	 */
	TSet<int64> Hidden;

	void Want(const FIntPoint& Chunk);
	void ReleaseFarChunks(const FIntPoint& Centre);
	void ResolveScatter();

	/** Scatter looks indexed by terrain code, rebuilt whenever the name list changes. */
	TArray<FIntervalScatterKind> ScatterByCode;

	/**
	 * What grows on the island's spine, which is not a terrain code.
	 *
	 * The ridge's tiles are ordinary `crags` and it is the one place where a
	 * tile's planting is decided by something other than what it is made of.
	 * Resolved from the look beside the rest; see AIntervalChunk::BuildScatter.
	 */
	FIntervalScatterKind SpineScatter;

	/** Roof looks indexed by terrain code, rebuilt with the scatter. */
	TArray<FIntervalRoofKind> RoofByCode;

	/** 1 where the level says that ground is a threshold; see IntervalLook.h. */
	UPROPERTY(Transient)
	TArray<uint8> ThresholdByCode;

	UPROPERTY(Transient)
	TMap<FIntPoint, TObjectPtr<AIntervalChunk>> Live;

	/** Tile code -> what that ground does to the land. See `ShapeOfTiles`. */
	mutable TArray<uint8> Shape;
	const TArray<uint8>& ShapeOfTiles() const;

	/**
	 * Chunks asked for and not yet answered.
	 *
	 * THIS USED TO BE A PERMANENT VETO, and it cost the south-east of the
	 * island. `Want` refuses to ask for a chunk that is already pending --
	 * correctly, or a citizen crossing a chunk edge would ask five times a
	 * second -- and the ONLY thing that cleared an entry was the reply
	 * arriving. So a reply that never came stranded that chunk for the life of
	 * the play session: the ground was never requested again, never built, and
	 * the window drew the inside of the sky sphere where the country should
	 * be. Restarting the bridge with requests in flight does exactly that, and
	 * this session restarted it a dozen times.
	 *
	 * Each entry now carries the time it was asked, and a request that has gone
	 * unanswered long enough is asked again.
	 */
	TMap<FIntPoint, double> Pending;
	FIntPoint LastCentre = FIntPoint(MIN_int32, MIN_int32);

	/**
	 * ---- CHUNKS THAT HAVE ARRIVED AND ARE NOT BUILT YET ----
	 *
	 * A chunk used to be BUILT the instant it arrived, inside the socket
	 * handler. One chunk is a procedural mesh, a control texture, every
	 * scatter instance, every roof and every floor in it; several arriving in
	 * the same frame is all of that work in one frame, and the frame timer
	 * caught a SIX SECOND one. What that is from the chair is a window that
	 * stops dead whenever you cross a chunk edge, which is exactly how it was
	 * reported: "walking is extremely buggy... it really struggles".
	 *
	 * So arriving chunks queue here and the tick builds them against a time
	 * budget, nearest first. The ground still appears; it appears over two or
	 * three frames instead of in one enormous one.
	 */
	TArray<FIntervalTerrainChunk> Queued;

	/** The timer that paces chunk building. See BeginPlay for why not a tick. */
	FTimerHandle GroundBeat;

	/** Build whatever is queued, nearest first, until the budget is spent. */
	void BuildQueued();

	/** Build one chunk now. What HandleChunk used to do inline. */
	void RaiseChunk(const FIntervalTerrainChunk& Chunk);

	/**
	 * Milliseconds of a frame this actor will spend building ground.
	 *
	 * Eight is about half a frame at sixty and a fifth of one at fifteen, and
	 * a chunk takes longer than that on its own -- so this does not promise to
	 * fit a chunk in, it promises to start at most one more once the budget is
	 * spent. The alternative is a partial chunk, which is a hole in the world.
	 */
	float BuildBudgetMs = 8.f;

	/**
	 * How long to wait for a chunk before asking again, in seconds.
	 *
	 * Long enough that a busy bridge is not asked twice for the same ground,
	 * short enough that a citizen walking into a stranded chunk sees the
	 * country appear rather than the sky.
	 */
	static constexpr double ChunkPatience = 4.0;

	UPROPERTY(Transient)
	TObjectPtr<UIntervalBridgeSubsystem> Bridge;
};
