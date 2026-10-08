// Copyright interval.

#include "IntervalMemory.h"

#include "HAL/FileManager.h"
#include "HAL/PlatformFileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

DEFINE_LOG_CATEGORY_STATIC(LogIntervalMemory, Log, All);

namespace
{
	// A citizen who has seen nothing. 255 is also what the ground answers for
	// a chunk it does not hold, so the same value means "not known" at both
	// ends and there is no second vocabulary to keep in step.
	constexpr uint8 Unseen = 255;
	/** At most once a minute. The memory is small; the disk is not the point. */
	constexpr double WriteEvery = 60.0;
}

FString UIntervalMemorySubsystem::FileFor(const FString& PlayerId) const
{
	// UNDER THE CITIZEN'S OWN ID, and only the first twelve of it -- the same
	// prefix every log line and every nameplate uses, so a person looking in
	// the folder can tell whose map is whose without a lookup table.
	return FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("interval"),
		FString::Printf(TEXT("seen-%s.map"), *PlayerId.Left(12)));
}

void UIntervalMemorySubsystem::Bind(int32 InWide, int32 InHigh, const FString& PlayerId)
{
	if (InWide <= 0 || InHigh <= 0 || PlayerId.IsEmpty())
	{
		return;
	}
	const FString Want = FileFor(PlayerId);
	if (Wide == InWide && High == InHigh && Path == Want)
	{
		return;   // already attached to this island for this citizen
	}

	// A DIFFERENT CITIZEN IS A DIFFERENT MAP. When the day's ninety minutes
	// are spent the thing to do is mint a fresh key and carry on as somebody
	// else -- and that somebody has not walked anywhere yet. Carrying the old
	// map across would be the window telling a lie about a citizen's own
	// history, which is the one thing it must not do.
	if (bDirty)
	{
		Save();
	}
	Wide = InWide;
	High = InHigh;
	Path = Want;
	Seen.Init(Unseen, Wide * High);
	SeenCount = 0;
	bDirty = false;
	SavedAt = FPlatformTime::Seconds();

	TArray<uint8> OnDisk;
	if (FFileHelper::LoadFileToArray(OnDisk, *Path) && OnDisk.Num() == Seen.Num())
	{
		Seen = MoveTemp(OnDisk);
		for (uint8 Code : Seen)
		{
			if (Code != Unseen) { ++SeenCount; }
		}
	}
	else if (OnDisk.Num() > 0)
	{
		// A MAP OF A DIFFERENT ISLAND. The file is keyed by citizen and not by
		// world, so a citizen who has walked on two foundings would otherwise
		// read one's memory onto the other's geography -- a map that is wrong
		// everywhere and looks right. Starting over is the only honest answer.
		UE_LOG(LogIntervalMemory, Warning,
			TEXT("[interval] the remembered map is %d tiles and this island is %d; starting fresh"),
			OnDisk.Num(), Seen.Num());
	}
	UE_LOG(LogIntervalMemory, Log,
		TEXT("[interval] %s has seen %d of %d tiles"),
		*PlayerId.Left(12), SeenCount, Seen.Num());
}

void UIntervalMemorySubsystem::Note(int32 X, int32 Y, uint8 Code)
{
	if (Code == Unseen || X < 0 || Y < 0 || X >= Wide || Y >= High)
	{
		return;
	}
	uint8& Held = Seen[Y * Wide + X];
	if (Held == Code)
	{
		return;
	}
	if (Held == Unseen)
	{
		++SeenCount;
	}
	Held = Code;
	bDirty = true;

	// ON A TIMER, not on every change: a citizen walking crosses a hundred new
	// tiles a minute and writing 448 KiB a hundred times a minute is how a
	// smooth window starts hitching once an hour.
	const double Now = FPlatformTime::Seconds();
	if (Now - SavedAt > WriteEvery)
	{
		Save();
	}
}

uint8 UIntervalMemorySubsystem::Recall(int32 X, int32 Y) const
{
	if (X < 0 || Y < 0 || X >= Wide || Y >= High)
	{
		return Unseen;
	}
	return Seen[Y * Wide + X];
}

void UIntervalMemorySubsystem::Save()
{
	if (Path.IsEmpty() || Seen.Num() == 0)
	{
		return;
	}
	SavedAt = FPlatformTime::Seconds();
	if (!bDirty)
	{
		return;
	}
	if (FFileHelper::SaveArrayToFile(Seen, *Path))
	{
		bDirty = false;
	}
	else
	{
		UE_LOG(LogIntervalMemory, Warning,
			TEXT("[interval] could not write the remembered map to %s"), *Path);
	}
}

void UIntervalMemorySubsystem::Deinitialize()
{
	// THE LAST THING IT DOES. A citizen who walked for an hour and then shut
	// the window should not lose the hour.
	Save();
	Super::Deinitialize();
}
