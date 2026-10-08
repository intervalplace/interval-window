// Copyright interval.
//
// BIRDS, IN THE AIR OVER THE ISLAND.
//
// Asked for from the stream in a list of the things that would lift this
// window most: "birds flying in the sky ... details like these are in my
// opinion what will give this window a big jump."
//
// AND THEY FLY LOW, WHICH IS NOT A COMPROMISE. This camera pitches fifty
// degrees down and the top of the frame looks twenty-one degrees BELOW the
// horizon: there is no sky in this window at all, ever, at any zoom. Birds put
// where a bird belongs would be birds nobody ever saw. What is in frame is the
// land, so that is where they are -- eight to thirty metres up, crossing the
// fields, seen from above and from behind as they go. Which is the better shot
// anyway: a skein of birds over a meadow with their shadows running along
// under them says more about a place than the same birds against blank sky.
//
// A FLOCK AT A TIME, AND THEN NOTHING. Birds are like the birdsong they are
// drawn beside: their realism is in their SPACING. A sky with a constant
// supply of birds in it is an aquarium. One skein crosses, and then the sky is
// empty for a while, and the empty while is what makes the next one worth
// looking up at.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IntervalWings.generated.h"

class UInstancedStaticMeshComponent;
class UIntervalBridgeSubsystem;
class UIntervalLook;
class AIntervalGround;

UCLASS()
class INTERVALBRIDGE_API AIntervalWings : public AActor
{
	GENERATED_BODY()

public:
	AIntervalWings();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	/** A look asset to take the bird from; unset, the conventional one. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<UIntervalLook> Look;

private:
	/**
	 * ONE COMPONENT FOR EVERY BIRD IN THE AIR, which is what makes this cost
	 * nothing. The flock is a set of transforms in one draw, and the wing beat
	 * is in the material, so the game thread's whole share of this is writing
	 * two dozen transforms a frame.
	 */
	UPROPERTY(Transient)
	TObjectPtr<UInstancedStaticMeshComponent> Flock;

	UPROPERTY(Transient)
	TObjectPtr<UIntervalBridgeSubsystem> Bridge;

	UPROPERTY(Transient)
	TObjectPtr<AIntervalGround> Ground;

	/**
	 * WHERE ONE BIRD SITS WITHIN ITS SKEIN.
	 *
	 * Held rather than worked out, so a flock keeps its shape: birds hold
	 * station on each other, and a formation recomputed from noise every frame
	 * is a cloud of midges.
	 */
	struct FBird
	{
		/** Across the line of flight, and along it: metres, in the flock's
		 *  own frame. */
		FVector2D Station = FVector2D::ZeroVector;
		/** How high above the flock's own height this one flies. */
		float Rise = 0.f;
		/** Its own beat, so the skein does not pulse as one animal. */
		float Wander = 0.f;
		/** And its own size, so eleven of one mesh is not a row of stamps. */
		float Size = 1.f;
	};

	/** Where the skein starts, where it is going, and how far along it is. */
	FVector From = FVector::ZeroVector;
	FVector Toward = FVector::ForwardVector;
	float Length = 0.f;
	float Travelled = 0.f;
	float Speed = 900.f;
	float Height = 1600.f;
	TArray<FBird> Birds;

	/** Seconds of empty sky still owed before the next skein. */
	float Quiet = 6.f;

	/** Lay out a new skein somewhere the citizen can see it. */
	void Gather();

	/** Take the skein down and start counting the quiet again. */
	void Scatter();
};
