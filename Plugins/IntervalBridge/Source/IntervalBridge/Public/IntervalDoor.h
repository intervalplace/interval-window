// IntervalDoor.h -- where a citizen finds out where they are.
//
// The same door every other window has: the world's id, the interval it is on,
// the last interval that is FINALIZED, how many witnesses stand behind that,
// and which citizen you are. A tick that keeps climbing while the finalized
// tick does not is a world that is running but not agreeing, and a citizen is
// entitled to see the difference rather than to wonder why nothing they do
// sticks.
//
// WHAT THE DOOR DOES NOT DO IS HOLD THE KEY. The file named here is the
// citizen; a person may copy it, back it up, or carry it to another vessel
// with their own hands. Its bytes do not come through this socket and are
// never in this process. An exported key that passed through here would be in
// the editor's memory, in its crash dumps, and in whatever the editor happens
// to write to disk -- which is a great deal. The plugin cannot sign, and it
// also cannot leak what it was never given.
//
// The widget builds its own tree in C++ and needs no asset, which keeps the
// door in the same place as the rules it displays.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Blueprint/UserWidget.h"
#include "IntervalDoor.generated.h"

class UIntervalBridgeSubsystem;
class UTextBlock;
class UVerticalBox;

UCLASS()
class INTERVALBRIDGE_API UIntervalDoorWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void NativeTick(const FGeometry& Geometry, float DeltaSeconds) override;

	/** The feed is drawn by the hand; this is the plate of facts above it. */
	UPROPERTY(Transient)
	TObjectPtr<UIntervalBridgeSubsystem> Bridge;

private:
	UTextBlock* AddRow(UVerticalBox* Box, const FLinearColor& Colour, int32 Size);

	UPROPERTY(Transient) TObjectPtr<UTextBlock> WorldRow;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> CitizenRow;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> IntervalRow;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> AgreementRow;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> StandingRow;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> KeyRow;
};

UCLASS()
class INTERVALBRIDGE_API AIntervalDoor : public AActor
{
	GENERATED_BODY()

public:
	AIntervalDoor();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Door")
	bool bShowDoor = true;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	UPROPERTY(Transient)
	TObjectPtr<UIntervalDoorWidget> Widget;
};
