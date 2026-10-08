// Copyright interval.
//
// WHAT THIS CITIZEN HAS SEEN OF THE ISLAND.
//
// The map has always refused to draw a tile whose chunk has not arrived, which
// is unusual and right: it does not know what is there, and saying so is a
// better drawing than an invented green field. But it forgot the moment you
// walked away, so the picture was only ever the hundred-odd tiles around you
// and the island beyond them was permanently blank.
//
// This remembers. A tile drawn once stays drawn -- dimmer, because it is a
// memory rather than a sight -- and after a few days of walking the map is a
// record of where this citizen has been. That is worth having in its own
// right, and it is what makes a world map worth opening at all: an 896 by 512
// picture handed out complete at birth is a satellite photograph, and this
// world does not have satellites. It has people who walk.
//
// ---- WHY IT BELONGS TO THE CITIZEN AND NOT TO THE WINDOW ----
//
// It is saved under the player's own id, so a fresh key pair starts with a
// blank island. That is the honest reading of a world where presence is
// rationed to ninety minutes a day: the map is a thing you earn by spending
// that time, and a new citizen has not spent any. It also means the world map
// says something about WHO YOU ARE rather than about which machine you happen
// to be sitting at.
//
// ---- AND WHY IT IS NOT WORLD KNOWLEDGE ----
//
// The rule this whole project is built on is that the bridge holds the key and
// all world knowledge, and Unreal holds only pixels. This does not breach it.
// It stores no rule, no affordance, no meaning: it is a record of which tiles
// this window has DRAWN and what code it drew them with. The terrain codes
// came from the bridge in the first place and are still meaningless here --
// the window can no more say what `peat` affords today than it could before.
// A window remembering its own drawing is the same kind of fact as a window
// knowing where its own camera is pointing.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "IntervalMemory.generated.h"

UCLASS()
class INTERVALBRIDGE_API UIntervalMemorySubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Deinitialize() override;

	/**
	 * Attach to an island and a citizen, loading whatever they have seen of it
	 * before. Safe to call every frame: it does the work once.
	 */
	void Bind(int32 InWide, int32 InHigh, const FString& PlayerId);

	/** This tile was drawn, with this terrain code. 255 means "no chunk". */
	void Note(int32 X, int32 Y, uint8 Code);

	/** What was drawn here once, or 255 for ground this citizen has never seen. */
	uint8 Recall(int32 X, int32 Y) const;

	bool IsBound() const { return Wide > 0 && High > 0; }
	int32 GetWide() const { return Wide; }
	int32 GetHigh() const { return High; }

	/** How many tiles of the island this citizen has laid eyes on. */
	int32 GetSeenCount() const { return SeenCount; }

	/** Write it out. Called on a timer and on the way down. */
	void Save();

private:
	FString FileFor(const FString& PlayerId) const;

	/**
	 * One byte a tile: 255 for never seen, otherwise the terrain code it was
	 * drawn with. An island is 896 by 512, so the whole memory is 448 KiB --
	 * small enough that there is no cleverness to justify here.
	 */
	TArray<uint8> Seen;
	int32 Wide = 0;
	int32 High = 0;
	int32 SeenCount = 0;
	FString Path;
	/** Nothing to write since the last write; do not churn the disk. */
	bool bDirty = false;
	double SavedAt = 0.0;
};
