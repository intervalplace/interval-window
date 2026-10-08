// IntervalRoof.h -- what covers a building, and how steeply.
//
// A roof here is GEOMETRY, not a box. An English medieval house is a steep
// gable: two planes leaning against a ridge that runs the length of the
// building, ending in a triangle of wall at each end. A flat slab reads as a
// warehouse at any distance, and no amount of texture fixes it.
//
// None of it is invented. The generator already answers, per tile, whether a
// citizen standing there is indoors, so a building's footprint is in the
// terrain plane, told. The roof is that footprint dilated over its own walls;
// the ridge is the long axis of the footprint; the pitch is the only number a
// person chooses. Nothing measures a building that the world did not already
// describe.

#pragma once

#include "CoreMinimal.h"
#include "IntervalRoof.generated.h"

class UMaterialInterface;

USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalRoofKind
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<UMaterialInterface> Material;

	/** Where the eaves sit: the top of the walls this roof rests on, in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	float EavesHeight = 270.f;

	/**
	 * Centimetres of rise per tile from eaves to ridge. A medieval thatched
	 * roof is steep -- 45 to 55 degrees -- because thatch sheds water by slope
	 * alone. A tile is 200cm, so 200 here is 45 degrees and anything under
	 * about 140 stops reading as a roof at all.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	float RisePerTile = 210.f;

	/** How far the eaves stand out past the wall, in cm. Medieval eaves overhang hard. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	float Overhang = 34.f;

	/** Ridge height is clamped here so a hall does not become a spire. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	float MaxRise = 520.f;


	/**
	 * What the window closes the roof's perimeter with when the world names
	 * no wall there. Unset, the thatch material is used, which is wrong but
	 * visible -- better than the daylight that was there before.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<UMaterialInterface> WallMaterial;

	/** What a door leaf is made of. Unset, no leaf is hung and the way stands open. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<UMaterialInterface> DoorMaterial;

	/** Head height of a doorway. The closure above this is the lintel. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "80", ClampMax = "400"))
	float DoorHeight = 182.f;

	/** How wide the opening is, of the two metres the tile gives it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "40", ClampMax = "200"))
	float DoorWidth = 98.f;

	/** How far that closure sits inside the tile edge, so a drawn wall hides it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0", ClampMax = "60"))
	float Inset = 7.f;

	/** How far it carries below zero, so ground relief cannot open a gap under it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0", ClampMax = "200"))
	float Footing = 40.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	bool bCastShadow = true;
};
