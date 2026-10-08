// Copyright interval.
//
// THE AIR THE WINDOW LOOKS THROUGH.
//
// Exposure, grade, occlusion, bloom: none of it is a fact about the world and
// all of it is the difference between a render and a picture. It is spawned
// rather than placed for the same reason the sound is -- a level actor cannot
// be saved from here, so anything that must survive a rebuild has to come
// from the plugin or from an asset (IntervalLook.h).
//
// The exposure band is deliberately narrow and deliberately low. Auto-exposure
// given its head turns a thatched roof into a white sheet the moment a citizen
// looks up, and turns the moor black the moment they look down; the world has
// weather and an hour of its own, and the window should not be arguing with
// them every time the camera turns.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IntervalAir.generated.h"

class UPostProcessComponent;

UCLASS()
class INTERVALBRIDGE_API AIntervalAir : public AActor
{
	GENERATED_BODY()

public:
	AIntervalAir();

	virtual void BeginPlay() override;

	/** Applies the grade below to the component. Called on spawn. */
	UFUNCTION(BlueprintCallable, Category = "Interval")
	void Compose();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Interval")
	TObjectPtr<UPostProcessComponent> Air;

	/** The band auto-exposure is allowed to move in. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Light")
	float ExposureLow = 0.12f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Light")
	float ExposureHigh = 1.4f;

	/** Pulls detail back out of deep shade without flattening the whole frame. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Light")
	float ShadowLift = 0.62f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Light")
	float Bloom = 0.38f;

	/** Cool in the shade, warm in the sun: the whole of what makes daylight read as daylight. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Grade")
	FLinearColor ShadowTint = FLinearColor(0.94f, 0.97f, 1.06f, 1.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Grade")
	FLinearColor HighlightTint = FLinearColor(1.05f, 1.01f, 0.94f, 1.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Grade")
	float Vignette = 0.32f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Grade")
	float Grain = 0.06f;
};
