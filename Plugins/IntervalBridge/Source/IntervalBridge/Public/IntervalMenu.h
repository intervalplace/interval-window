// Copyright interval.
//
// THE RIGHT-CLICK MENU.
//
// Until this, a player could do one of the world's sixty-nine verbs. Ninety-odd
// deeds were wired, filable, and reachable only by writing a line into a text
// file -- which is an automation harness, not a way to play. Nothing on screen
// had a button on it except the door.
//
// The arrangement is RuneScape's, and it was asked for by name: a LEFT click
// does the default thing to whatever is under the cursor, a RIGHT click lists
// everything that thing affords. It suits this world particularly well, because
// the obvious thing to do to another citizen is trade rather than violence and
// no single click could carry that distinction.
//
// WHAT IT MAY DECIDE, AND WHAT IT MAY NOT. This draws a list and calls the
// hand. It does not know that a well affords drinking -- the bridge derives
// that from the engine and sends it in `hello` -- and it does not know whether
// a deed will be allowed. The world refuses, and the feed says so. A menu that
// hid the options it guessed were illegal would be a second copy of the rules,
// which is the drift this whole project is built to refuse.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "IntervalTypes.h"
#include "IntervalMenu.generated.h"

class UBorder;
class UVerticalBox;
class UTextBlock;
class AIntervalHand;
class UIntervalBridgeSubsystem;

/**
 * One row of the menu. A button carries no payload of its own, so the verb and
 * the target it belongs to ride here and the widget is the thing clicked.
 */
UCLASS()
class INTERVALBRIDGE_API UIntervalMenuRow : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual TSharedRef<SWidget> RebuildWidget() override;

	UPROPERTY() FString Verb;
	/** What the verb is about, when it is about a thing: an item, a recipe. */
	UPROPERTY() FString With;
	UPROPERTY() FIntervalTarget On;
	UPROPERTY() FString Label;
	UPROPERTY() bool bIsDefault = false;

	/**
	 * THIS LINE OPENS A SECOND PAGE RATHER THAN DOING SOMETHING.
	 *
	 * `fletch` is one verb for four makes. Listing all four in the main menu
	 * is four lines for one idea; listing the verb once and the makes when it
	 * is chosen is a submenu, which is what every window of this shape does.
	 */
	UPROPERTY() bool bOpensList = false;

	UPROPERTY() TObjectPtr<AIntervalHand> Hand;

	UFUNCTION()
	void Chosen();

	/** Set by the owning menu so a choice can close it. */
	UPROPERTY() TObjectPtr<class UIntervalMenuWidget> Menu;
};

UCLASS()
class INTERVALBRIDGE_API UIntervalMenuWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual TSharedRef<SWidget> RebuildWidget() override;

	/**
	 * Show every option of everything under the cursor. Empty closes it.
	 *
	 * UFUNCTION, and not decoratively: this is bound to the hand's delegate
	 * with AddDynamic, which looks the handler up BY NAME through reflection.
	 * Without the macro it compiles perfectly and fails at runtime with one
	 * line in the log -- "Unable to bind delegate to 'Offer'" -- and the menu
	 * simply never appears, which reads as a widget that is not being drawn
	 * rather than as an event that is not arriving.
	 */
	UFUNCTION()
	void Offer(const TArray<FIntervalTarget>& Targets);

	void Close();

	/** The second page: what this thing can be fletched into. */
	/**
	 * THE SECOND PAGE: the things a verb could be about, in the same plate.
	 * See `AIntervalHand::ChoicesFor` for where the list comes from.
	 */
	void OfferChoices(const FIntervalTarget& On, const FString& Head,
		const TArray<FIntervalOption>& Choices);

	UPROPERTY() TObjectPtr<AIntervalHand> Hand;
	UPROPERTY() TObjectPtr<UIntervalBridgeSubsystem> Bridge;

private:
	UPROPERTY() TObjectPtr<UBorder> Plate;
	UPROPERTY() TObjectPtr<UVerticalBox> Rows;
	UPROPERTY() TObjectPtr<UTextBlock> Head;
};
