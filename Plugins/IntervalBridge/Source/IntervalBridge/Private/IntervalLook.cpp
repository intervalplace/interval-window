// Copyright interval.

#include "IntervalLook.h"

#include "UObject/ConstructorHelpers.h"

const TCHAR* UIntervalLook::DefaultPath = TEXT("/Game/Interval/IntervalLook.IntervalLook");

UIntervalLook* UIntervalLook::Resolve(UIntervalLook* Named)
{
	// A level may name its own; most will not, and a project with one window
	// should not have to. Falling back to a fixed path is a convention, not a
	// fact: a build that finds nothing there draws nothing and says so, which
	// is the same answer it gives for a word it has no mesh for.
	if (Named)
	{
		return Named;
	}
	return LoadObject<UIntervalLook>(nullptr, DefaultPath);
}
