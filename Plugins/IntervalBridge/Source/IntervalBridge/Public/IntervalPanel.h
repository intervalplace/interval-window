// Copyright interval.
//
// WHAT THE CITIZEN IS CARRYING, WEARING, AND WORTH.
//
// The window could draw a whole island and could not tell you what was in your
// own pack. Every other window shows it; this one had the payload -- the
// frame's `me` carries the inventory, the equipment, the purse, the skills --
// and drew none of it.
//
// ALWAYS ON, AND ALSO A KEY. Which of those is right is a question for whoever
// plays it: a panel that is always up is one fewer thing to remember and one
// less place to look, and a panel behind a key leaves the world unobstructed.
// Rather than guess, this does both -- it is up by default and Tab puts it
// away -- so both answers can be tried without a build.
//
// IT READS AND IT DOES NOT ACT. Every deed in this window goes through
// AIntervalHand, which is the only thing allowed to send one; this draws what
// the last frame said and nothing else. Nothing here decides what an item is
// worth, whether a spell may be cast, or whether a slot may be worn -- it
// prints the world's own words.
//
// NOTHING HAPPENS WITHOUT A PLAYER CONTROLLER, like the gate: Simulate has
// none, which is how every photograph in these notes is taken, so the panel is
// simply absent there.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Blueprint/UserWidget.h"
#include "IntervalPanel.generated.h"

class UIntervalBridgeSubsystem;
class UTextBlock;
class UBorder;
class UVerticalBox;
class AIntervalHand;

UCLASS()
class INTERVALBRIDGE_API UIntervalPanelWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UIntervalPanelWidget(const FObjectInitializer& Init);

	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void NativeTick(const FGeometry& Geometry, float DeltaSeconds) override;
	virtual FReply NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Key) override;

	/** Set by the actor that made it, so the panel can find the world. */
	UPROPERTY(Transient) TObjectPtr<UIntervalBridgeSubsystem> Bridge;
	UPROPERTY(Transient) TObjectPtr<class AIntervalPanel> Owner;

private:
	UTextBlock* Line(UVerticalBox* Into, const FLinearColor& Tint, int32 Size, bool bBold);
	void Refresh();

	UPROPERTY(Transient) TObjectPtr<UBorder> Frame;
	UPROPERTY(Transient) TObjectPtr<UBorder> FeedFrame;
	UPROPERTY(Transient) TObjectPtr<UVerticalBox> Column;
	UPROPERTY(Transient) TObjectPtr<UVerticalBox> FeedColumn;

	UPROPERTY(Transient) TObjectPtr<UTextBlock> PurseRow;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> BodyRow;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> DoingRow;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> HoursRow;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> HaulRow;
	UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> PackRows;
	UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> WornRows;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> SkillRow;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> BookRow;
	UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> SpellRows;
	UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> FeedRows;

	bool bShown = true;
	int64 DrawnAt = -1;
};

UCLASS()
class INTERVALBRIDGE_API AIntervalPanel : public AActor
{
	GENERATED_BODY()

public:
	AIntervalPanel();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;

	/** How many pack slots the world gives a citizen. Read from the frame. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Panel")
	int32 PackSlots = 12;

	/** The equip slots, in the order they are worn, top to bottom. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Panel")
	TArray<FString> WornOrder = { TEXT("head"), TEXT("body"), TEXT("legs"),
		TEXT("weapon"), TEXT("offhand") };

	/**
	 * THE TWO BOOKS, AND NOTHING IN BOTH.
	 *
	 * Eleven spells, not two. A citizen speaks one book or the other -- the
	 * frame says which in `book` -- and turns from one to the next at an
	 * ossuary, which takes as well as gives. The panel shows the book they
	 * actually speak, because showing a caster spells they cannot cast is
	 * worse than showing none.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Panel")
	TArray<FString> CommonBook = { TEXT("still"), TEXT("seal"), TEXT("transmute"),
		TEXT("mend"), TEXT("mendp"), TEXT("unmake"), TEXT("anchor") };

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Panel")
	TArray<FString> BarrowBook = { TEXT("waking"), TEXT("rot"), TEXT("taking"),
		TEXT("withering") };

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Panel")
	bool bShowPanel = true;

	UPROPERTY(Transient) TObjectPtr<UIntervalPanelWidget> Widget;

	/** The one thing allowed to send a deed, found once. The feed lives on it. */
	UPROPERTY(Transient) TObjectPtr<AIntervalHand> Hand;

	/** The door, so the panel can stay out of its way until it opens. */
	UPROPERTY(Transient) TObjectPtr<class AIntervalGate> Gate;

	UPROPERTY()
	TObjectPtr<class UIntervalMenuWidget> Menu;

	UPROPERTY()
	TObjectPtr<class AIntervalHud> HudActor;
};
