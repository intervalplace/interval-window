// Copyright interval.

#pragma once

#include "CoreMinimal.h"
#include "IntervalStructures.h"
#include "IntervalMotion.generated.h"

class UAnimSequence;

/**
 * How a citizen moves while the world says they are doing a thing.
 *
 * Keyed, like every other table here, by the WORLD'S OWN WORD. The engine
 * gives a citizen an action of `gather`, `attack`, `attackp` or `raise`, and
 * a level says what each of those looks like. Two words are the window's own
 * and are marked as such where they are set: `still`, for a citizen the world
 * says nothing about, and `felled`, which is worked out from hit points.
 *
 * Nothing in C++ decides that gathering is a swing. A world that grows a new
 * verb needs a new row and no build.
 */
USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalMotion
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<UAnimSequence> Anim;

	/**
	 * Most verbs loop. A deed takes a while and the world keeps saying it is
	 * happening, so a swing that plays once and stops leaves a citizen frozen
	 * mid-chop for the rest of the interval; looping it reads as working.
	 * Dying does not loop.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	bool bLoop = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0.05", ClampMax = "4"))
	float Rate = 1.f;

	/**
	 * THE GROUND SPEED THIS CLIP WAS CUT FOR, in centimetres a second.
	 *
	 * A walk cycle is a fixed number of steps a second. Play it while the
	 * figure crosses the ground at some other speed and the feet slide -- and
	 * they slide in BOTH directions here, because a citizen in this world
	 * moves a whole tile in an interval when they are going somewhere and not
	 * at all when they are not, with nothing in between.
	 *
	 * So the clip is sped up and slowed down to match how fast the figure is
	 * actually travelling. Zero means "play it as authored", which is right
	 * for everything that is not locomotion: a hatchet swing is not faster
	 * because its owner was running a moment ago.
	 *
	 * It cannot be derived. These clips carry no root motion, so there is no
	 * distance in them to divide by; it is a number to set by watching the
	 * feet, and two hundred -- one tile an interval -- is where it starts
	 * because that is the speed everything was tuned at before this existed.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0"))
	float Pace = 0.f;


	/**
	 * What is in their hand while they are doing it.
	 *
	 * A swing is a swing; what makes it FELLING A TREE rather than mining a
	 * seam is the hatchet. The verb for gathering carries the kind of thing
	 * being gathered -- `gather.tree`, `gather.iron-rock` -- so a level can
	 * give each its own tool and its own tempo without the window learning
	 * that a tree is made of wood.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	FIntervalKit Held;

	/** Set when this motion's own tool should replace whatever they carry. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	bool bHoldsTool = false;
};
