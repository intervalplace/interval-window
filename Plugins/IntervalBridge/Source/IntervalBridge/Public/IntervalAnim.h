// Copyright interval.
//
// WHY ANYTHING THAT MOVES IN THIS WINDOW SNAPS.
//
// Every figure here is driven by `USkeletalMeshComponent::PlayAnimation`, which
// is the single-node path: it sets one sequence and plays it. There is no blend
// in it at all. So a citizen who stops walking does not settle into standing,
// they are standing, on the next frame, mid-stride -- and a wolf that starts
// walking teleports its legs into the first frame of the walk. It is the
// single loudest thing wrong with how this world moves, and it is loud in a way
// that reads as "unfinished" rather than as "stylised".
//
// This is the smallest honest fix: a native animation instance that keeps TWO
// clips -- the one it is leaving and the one it is arriving at -- and blends
// between them. No Animation Blueprint, no graph, no asset. Two sequences, two
// times, one alpha.
//
// IT EXTRACTS THE POSES ITSELF rather than hosting `FAnimNode_SequencePlayer`s.
// The node API moves between engine versions and its fields are private behind
// setters that come and go; `UAnimSequence::GetAnimationPose` has been stable
// for years and does exactly what is needed. Owning the clock also buys the two
// things the old path could not do: a play rate that follows how fast the
// figure is ACTUALLY crossing the ground, so the feet stop sliding, and a start
// offset per creature so a flock does not breathe in unison.

#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimInstanceProxy.h"
#include "IntervalAnim.generated.h"

class UAnimSequence;

/** One clip, and where it has got to. */
USTRUCT()
struct FIntervalPlaying
{
	GENERATED_BODY()

	UPROPERTY(Transient)
	TObjectPtr<UAnimSequence> Anim;

	float Time = 0.f;
	float Rate = 1.f;
	bool bLoop = true;

	void Advance(float DeltaSeconds);
};

USTRUCT()
struct FIntervalAnimProxy : public FAnimInstanceProxy
{
	GENERATED_BODY()

	FIntervalAnimProxy() = default;
	explicit FIntervalAnimProxy(UAnimInstance* InInstance) : FAnimInstanceProxy(InInstance) {}

	// `Update` and `Evaluate`, not the `_AnyThread` pair -- those are
	// FAnimNode_Base's, and marking them override here compiles to nothing
	// and silently never runs.
	virtual void Update(float DeltaSeconds) override;
	virtual bool Evaluate(FPoseContext& Output) override;

	/** The clip being left, and the clip being arrived at. */
	FIntervalPlaying Leaving;
	FIntervalPlaying Arriving;

	/** 0 is wholly the old clip, 1 wholly the new one. */
	float Blend = 1.f;

	/** How long the crossing takes, in seconds. Zero is a cut. */
	float Over = 0.25f;
};

UCLASS()
class INTERVALBRIDGE_API UIntervalAnimInstance : public UAnimInstance
{
	GENERATED_BODY()

public:
	/**
	 * Go to this clip, over this long.
	 *
	 * Called from the game thread whenever the world's word for what something
	 * is doing changes. Asking for the clip that is already arriving does
	 * nothing, so this is safe to call every frame -- and it is, because the
	 * verb is recomputed every frame.
	 */
	void CrossFade(UAnimSequence* Next, float Rate, bool bLoop, float Over, float StartAt = 0.f);

	/** The clip that is arriving, for the caller to compare against. */
	UAnimSequence* Arriving() const { return Wanted; }

	/** Speeds up or slows the clip that is arriving, without restarting it. */
	void SetRate(float Rate);

protected:
	virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
	virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy) override;

private:
	FIntervalAnimProxy Proxy;

	UPROPERTY(Transient)
	TObjectPtr<UAnimSequence> Wanted;

	friend struct FIntervalAnimProxy;
};

/**
 * WHAT A FIGURE COSTS WHEN NOBODY IS LOOKING AT IT, which should be nothing.
 *
 * This world stands up about a thousand skeletal meshes at once: 655 for the
 * citizens and mobs and 350 for the keepers at their stalls, every one of them
 * with its own animation instance. Not one of them had either of the two
 * settings that decide what an off-screen figure costs, so a shepherd on the
 * far side of the island was having its pose evaluated, bone by bone, sixty
 * times a second so that nothing could see it. Measured: the keepers alone
 * were 9.7 ms of a 71 ms frame.
 *
 *   OnlyTickPoseWhenRendered -- a figure out of every view evaluates nothing.
 *     It keeps ticking its animation BLUEPRINT, so it still knows what it is
 *     doing and is in the right pose the frame it comes back into view; what
 *     it stops doing is the skeleton.
 *
 *   update rate optimisation -- a figure that IS rendered but is small and far
 *     away evaluates its pose every second or fourth frame and interpolates
 *     between, which at thirty metres on a top-down camera is a difference
 *     nobody can see. The engine picks the rate off the screen size.
 *
 * Both are per component and both are free. Called on the LEAD of a figure;
 * the followers take the lead's pose and evaluate nothing of their own.
 *
 * The draw distance is a separate matter and is NOT set here: what a citizen
 * can see is the world's business and belongs in a level's own tables.
 */
INTERVALBRIDGE_API void IntervalThriftyFigure(class USkeletalMeshComponent* Lead);
