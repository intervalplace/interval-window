// Copyright interval.

#include "IntervalAnim.h"

#include "Animation/AnimSequence.h"
#include "Animation/AnimationPoseData.h"
#include "AnimationRuntime.h"

void FIntervalPlaying::Advance(float DeltaSeconds)
{
	if (!Anim)
	{
		return;
	}
	const float Length = Anim->GetPlayLength();
	if (Length <= 0.f)
	{
		return;
	}
	Time += DeltaSeconds * Rate;
	if (bLoop)
	{
		Time = FMath::Fmod(Time, Length);
		if (Time < 0.f) { Time += Length; }
	}
	else
	{
		// A DEATH HOLDS ITS LAST FRAME. Wrapping a felling animation is a
		// corpse that stands up again every two seconds, which is the sort of
		// thing nobody reports because nobody believes they saw it.
		Time = FMath::Clamp(Time, 0.f, Length);
	}
}

void FIntervalAnimProxy::Update(float DeltaSeconds)
{
	FAnimInstanceProxy::Update(DeltaSeconds);
	Leaving.Advance(DeltaSeconds);
	Arriving.Advance(DeltaSeconds);
	if (Blend < 1.f)
	{
		Blend = (Over > KINDA_SMALL_NUMBER)
			? FMath::Min(1.f, Blend + DeltaSeconds / Over)
			: 1.f;
		if (Blend >= 1.f)
		{
			// Once the crossing is done the old clip is dropped, so a figure
			// standing still is evaluating one pose and not two.
			Leaving.Anim = nullptr;
		}
	}
}

bool FIntervalAnimProxy::Evaluate(FPoseContext& Output)
{
	if (!Arriving.Anim)
	{
		return false;   // nothing to say; the reference pose stands
	}

	FAnimExtractContext Take(static_cast<double>(Arriving.Time), false);
	Take.bLooping = Arriving.bLoop;

	if (!Leaving.Anim || Blend >= 1.f)
	{
		FAnimationPoseData Data(Output);
		Arriving.Anim->GetAnimationPose(Data, Take);
		return true;
	}

	// TWO POSES, WEIGHTED. `BlendTwoPosesTogether` takes the weight of the
	// FIRST pose, so the old clip's share is one minus the crossing.
	FPoseContext Old(this), New(this);
	FAnimExtractContext Back(static_cast<double>(Leaving.Time), false);
	Back.bLooping = Leaving.bLoop;

	FAnimationPoseData OldData(Old);
	FAnimationPoseData NewData(New);
	Leaving.Anim->GetAnimationPose(OldData, Back);
	Arriving.Anim->GetAnimationPose(NewData, Take);

	FAnimationPoseData OutData(Output);
	FAnimationRuntime::BlendTwoPosesTogether(OldData, NewData, 1.f - Blend, OutData);
	return true;
}

FAnimInstanceProxy* UIntervalAnimInstance::CreateAnimInstanceProxy()
{
	return &Proxy;
}

void UIntervalAnimInstance::DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy)
{
	// The proxy is a member, not a heap object; there is nothing to free.
}

void UIntervalAnimInstance::CrossFade(UAnimSequence* Next, float Rate, bool bLoop,
	float Over, float StartAt)
{
	if (!Next)
	{
		return;
	}
	if (Next == Wanted)
	{
		// ALREADY ON THE WAY THERE. The verb is recomputed every frame, so
		// this is called every frame, and restarting the clip each time is a
		// figure that never gets past its first pose.
		Proxy.Arriving.Rate = Rate;
		return;
	}
	Wanted = Next;

	Proxy.Leaving = Proxy.Arriving;
	Proxy.Arriving.Anim = Next;
	Proxy.Arriving.Rate = Rate;
	Proxy.Arriving.bLoop = bLoop;
	Proxy.Arriving.Time = FMath::Clamp(StartAt, 0.f, Next->GetPlayLength());
	Proxy.Over = Over;
	// Nothing to cross from on the very first clip, so it simply begins.
	Proxy.Blend = Proxy.Leaving.Anim ? 0.f : 1.f;
}

void UIntervalAnimInstance::SetRate(float Rate)
{
	Proxy.Arriving.Rate = Rate;
}
