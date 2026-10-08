// IntervalScatter.h -- what grows on a kind of ground, and where.
//
// A fern is not consensus. Nothing in the constitution cares where one grows,
// and the pillar does not send them. But "meet me by the crooked oak" is a
// sentence people say, and a window that rolled its own dice for decoration
// makes it a lie -- so placement here is a pure function of the ONE byte the
// bridge sends per tile, and of nothing else. No clock, no random stream, no
// per-machine state. Every Unreal window grows the same tuft on the same tile
// forever, and so would any other window that read the byte the same way.
//
// THE RULE THAT OUTRANKS PRETTINESS: decoration must never look gatherable.
// The world sends a small, fixed set of things a citizen may actually chop or
// mine, and they are drawn by AIntervalStructures with a silhouette language
// of their own -- tall cones, big boulders. Scatter must stay visually
// subordinate to those: low, small, and never tall enough to be mistaken for
// something you can walk up to and use. A window that scatters a thousand
// beautiful trees has made the game unplayable while making the screenshot
// better.

#pragma once

#include "CoreMinimal.h"
#include "IntervalScatter.generated.h"

class UStaticMesh;
class UMaterialInterface;

/** What grows on one kind of ground. Every field is a look, never a meaning. */
USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalScatterKind
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<UStaticMesh> Mesh;

	/**
	 * THE OTHER THINGS THIS GROUND GROWS.
	 *
	 * A ground had exactly one mesh, so a meadow was tens of thousands of
	 * copies of a single tuft and a wood was one bush repeated to the horizon.
	 * Per-instance colour variation helps and cannot fix it: every copy still
	 * has the same SILHOUETTE, and a field of one outline reads as stamped
	 * however well each stamp is drawn.
	 *
	 * `Mesh` remains the first and the fallback -- a ground that names nothing
	 * here behaves exactly as it did -- and these are the alternatives. Which
	 * one a given plant is comes out of the SAME tile byte that decided where
	 * it stands, so the arrangement stays a pure function of the tile: every
	 * window that reads it this way grows the same plant in the same spot, and
	 * "meet me by the crooked oak" keeps meaning something.
	 *
	 * Each distinct mesh costs one instanced component per chunk, so this is a
	 * handful of variants and not a catalogue.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TArray<TObjectPtr<UStaticMesh>> Variants;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<UMaterialInterface> Material;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	FVector Scale = FVector(0.3f, 0.3f, 0.3f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	float ZOffset = 0.f;

	/**
	 * Share of this ground's tiles that carry one. The seed byte is uniform
	 * over 0..255, so this is very nearly the fraction of tiles you get.
	 * Keep it low: scatter is the cheapest thing to overspend on and the
	 * frame budget belongs to shadows and ground.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0", ClampMax = "1"))
	float PerTile = 0.f;

	/**
	 * HOW MANY TIMES A TILE IS ASKED, not how many it gets.
	 *
	 * A tile is two metres across and was allowed exactly one thing growing on
	 * it, so a meadow at ninety per cent was ninety per cent of tiles carrying
	 * ONE tuft -- a lawn with weeds in it rather than a sward. Each try gets
	 * its own scramble of the same tile byte and its own place within the tile,
	 * so the arrangement is still a pure function of the tile and every window
	 * that reads it the same way still agrees about it.
	 *
	 * The cost is linear and the count is a level's to choose: grass wants six
	 * or eight, a boulder field wants one.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "1", ClampMax = "16"))
	int32 PerTileCount = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0", ClampMax = "360"))
	float YawJitter = 360.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0", ClampMax = "0.9"))
	float ScaleJitter = 0.25f;

	/** Centimetres. 0 draws it to the horizon, which for 450,000 tiles is a mistake. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0"))
	float MaxDrawDistance = 18000.f;

	/** Off by default: a shadow per tuft is a frame budget spent in the wrong place. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	bool bCastShadow = false;

	/** Keep it off a made way. People walk there; that is what makes it a way. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	bool bAvoidWays = true;
};
