// Copyright interval.
//
// THE GATE: the door you come in through.
//
// Every other window has one. You arrive at a plate with the world's name on
// it, the theme is playing, the world itself is moving behind the glass, and
// you press a button to go in. This window used to open straight into the
// middle of somebody's life, which is abrupt in a way the others are not --
// and, more to the point, gives you nothing to look at while the bridge is
// still finding the world.
//
// It is the browser's gate and not a new idea: the same words, the same order,
// the same single button. What it does NOT carry is the key row. The flat
// window offers to export and import a key because the key is in that tab;
// here it is in the bridge, and the plugin cannot sign and cannot leak what it
// was never given. The gate says where the file is and stops there.
//
// NOTHING HAPPENS WITHOUT A PLAYER CONTROLLER. Simulate has none -- it is how
// every photograph in these notes is taken -- so the gate is simply absent
// there, and no capture has to know it exists.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Blueprint/UserWidget.h"
#include "IntervalGate.generated.h"

class UIntervalBridgeSubsystem;
class UTextBlock;
class UButton;
class UBorder;
class UAudioComponent;
class UPostProcessComponent;
class ACameraActor;

UCLASS()
class INTERVALBRIDGE_API UIntervalGateWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void NativeTick(const FGeometry& Geometry, float DeltaSeconds) override;
	virtual void NativeConstruct() override;

	/**
	 * ENTER OPENS THE DOOR, and so does the button.
	 *
	 * The flat window's gate takes the Enter key as well as the press, and a
	 * person who has just typed something should not have to find the mouse
	 * again. It is also the only way anything but a person can open this --
	 * the PIE viewport's UMG does not appear in the editor's Slate tree, so
	 * the button cannot be clicked by automation and the key can.
	 */
	virtual FReply NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Key) override;

	/**
	 * AND SO DOES A PRESS ANYWHERE ON THE CARD.
	 *
	 * This card has exactly one action on it. A person who aims at the button
	 * and lands two pixels outside it has told us plainly what they want, and
	 * answering that with nothing at all is the single worst thing a title
	 * screen can do -- it is indistinguishable from a window that has hung,
	 * and it was reported as exactly that: "it launched / nothing happens
	 * when I click enter the world".
	 */
	virtual FReply NativeOnMouseButtonDown(const FGeometry& Geometry,
		const FPointerEvent& Mouse) override;

	UPROPERTY(Transient) TObjectPtr<UIntervalBridgeSubsystem> Bridge;

	/** The gate that owns this, told when the button is pressed. */
	UPROPERTY(Transient) TObjectPtr<class AIntervalGate> Gate;

private:
	UFUNCTION()
	void OnEnter();

	// ---- CARRYING A CITIZEN IN OR OUT ----
	//
	// These sit on the title card because that is where a person decides who
	// they are: it is the one screen that already says which file is the
	// citizen. Neither ever touches the key. They send a verb, the bridge does
	// the work with the clipboard and the file, and `CarrySaid` on the
	// subsystem is what comes back to be shown.
	UFUNCTION()
	void OnCarryOut();
	UFUNCTION()
	void OnCarryIn();

	UPROPERTY(Transient) TObjectPtr<UTextBlock> StatusRow;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> StandingRow;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> KeyRow;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> EnterLabel;
	UPROPERTY(Transient) TObjectPtr<UButton> EnterButton;
	UPROPERTY(Transient) TObjectPtr<UButton> CarryOutButton;
	UPROPERTY(Transient) TObjectPtr<UButton> CarryInButton;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> CarryRow;

	/** The title, the rules line, the two rules and the bars: all fade in. */
	UPROPERTY(Transient) TArray<TObjectPtr<UWidget>> Rising;
	UPROPERTY(Transient) TObjectPtr<UBorder> TopBar;
	UPROPERTY(Transient) TObjectPtr<UBorder> FootBar;

	float Age = 0.f;
};

UCLASS()
class INTERVALBRIDGE_API AIntervalGate : public AActor
{
	GENERATED_BODY()

public:
	AIntervalGate();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	/** Take the gate down and hand the view back to whoever was holding it. */
	UFUNCTION(BlueprintCallable, Category = "Interval")
	void Enter();

	/** Whether the gate is still up. */
	bool IsWaiting() const { return bWaiting; }

public:
	/**
	 * How far the player has turned the camera, in degrees off the look
	 * asset's own bearing. A window control, not a deed: see the note in Tick.
	 */
	UPROPERTY(BlueprintReadWrite, Category = "Interval|Gate")
	float Spin = 0.f;

	/** Degrees a second while a turn key is held. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Gate")
	float SpinRate = 85.f;

	/**
	 * How far out the wheel has pulled the camera, as a multiple of the
	 * wardrobe's own distance. One is the shot the world was framed for.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Gate")
	float Pull = 1.f;

	/** Where the cursor was last frame while the right button was held. */
	FVector2D Dragged = FVector2D::ZeroVector;
	bool bDragging = false;

	/**
	 * ---- AND THE TWO GESTURES A PHONE HAS INSTEAD ----
	 *
	 * Turning is a drag and zooming is a pinch, because those are the two
	 * things a hand does to a map without being told. Neither collides with
	 * the hand's tap and long press: a finger that has travelled past the
	 * hand's slop is a drag and can no longer be either of those, which is the
	 * same rule the right mouse button already follows.
	 *
	 * `Pinched` is the distance between two fingers last frame. Nought means
	 * there were not two.
	 */
	FVector2D Swiped = FVector2D::ZeroVector;
	bool bSwiping = false;
	float Pinched = 0.f;

private:
	/** Where the camera should be looking: the citizen if there is one. */
	FVector Heart() const;

	/**
	 * Cached, because Heart() runs every frame and finding this by class walks
	 * every actor in a world that holds thousands of them. Weak, so a level
	 * that has not built its people yet simply falls back to the tile.
	 */
	UPROPERTY(Transient)
	TWeakObjectPtr<class AIntervalCitizens> Drawn;

	UPROPERTY(Transient) TObjectPtr<UIntervalBridgeSubsystem> Bridge;
	UPROPERTY(Transient) TObjectPtr<UIntervalGateWidget> Plate;
	UPROPERTY(Transient) TObjectPtr<ACameraActor> Eye;
	UPROPERTY(Transient) TObjectPtr<UAudioComponent> Theme;
	UPROPERTY(Transient) TObjectPtr<AActor> WasWatching;

	/**
	 * THE WORLD IS BEHIND GLASS WHILE THE GATE IS UP.
	 *
	 * Depth of field, a deeper vignette and a little less colour, thrown over
	 * the whole view at a priority above the air's and taken off again when
	 * the gate opens. It is the difference between a menu drawn on top of a
	 * game and a title card: the eye is told, without being asked, that the
	 * words are the near thing and the country is the far one.
	 */
	UPROPERTY(Transient) TObjectPtr<UPostProcessComponent> Glass;

	float Turned = 0.f;
	float Waited = 0.f;
	bool bWaiting = false;

	/**
	 * WHAT THE WATCHING CAMERA IS EASING, and it is not its own position.
	 *
	 * See the note in Tick. The camera stands exactly on a circle round
	 * `Watching` at `Bearing` and `Pulled`, and it is those three that are
	 * smoothed -- so turning is an orbit at a constant radius instead of a
	 * chase across the chord, which fell inside the circle and climbed back
	 * out of it every time anybody turned.
	 */
	FVector Watching = FVector::ZeroVector;
	float Bearing = 0.f;
	float Pulled = 1.f;
	bool bWatched = false;
};
