// Copyright interval.
//
// WHAT THE WINDOW HEARS.
//
// Two things, and they behave quite differently.
//
// The AMBIENCE is a bed: it is always running, it follows the ground the
// citizen is standing on, and it cross-fades rather than cuts, because the
// edge of the Fens is a place you walk over and not a door you go through.
//
// The MUSIC is a piece. It arrives when you reach somewhere and is then left
// alone to finish -- restarting it every time a citizen steps back across a
// boundary is the single most reliable way to make a good theme hateful. A
// country is heard once per visit and not again until you have been somewhere
// else, which is the rule the browser window settled on for the same reason.
//
// Neither knows what any word means. The level maps the world's own word for
// the ground to a sound, and a word with no entry is silent.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IntervalSound.generated.h"

class UAudioComponent;
class UIntervalBridgeSubsystem;
class AIntervalGround;
class UIntervalLook;
struct FIntervalFrame;

UCLASS()
class INTERVALBRIDGE_API AIntervalSound : public AActor
{
	GENERATED_BODY()

public:
	AIntervalSound();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;
	virtual void Tick(float DeltaSeconds) override;

	/** A look asset to take the sounds from; unset, the conventional one. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<UIntervalLook> Look;

	/** How loud the bed sits under everything. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0", ClampMax = "2"))
	float AmbienceVolume = 0.55f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0", ClampMax = "2"))
	float MusicVolume = 0.42f;

	/** Seconds to trade one bed for the next. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0.1", ClampMax = "30"))
	float CrossFade = 3.5f;

	/**
	 * How long a citizen must stay somewhere before it counts as having
	 * arrived. Without it, a boundary you can stand astride starts a theme
	 * every time you shift your weight.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0", ClampMax = "120"))
	float SettleSeconds = 6.f;

private:
	UFUNCTION()
	void HandleFrame();

	UIntervalLook* Chosen() const;
	void SetBed(class USoundBase* Next);

	UPROPERTY(Transient)
	TObjectPtr<UIntervalBridgeSubsystem> Bridge;

	UPROPERTY(Transient)
	TObjectPtr<AIntervalGround> Ground;

	/** Two beds, so one can fade up while the other fades down. */
	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> BedA;

	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> BedB;

	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> Piece;

	/** Rain, twice: in the open and heard from under a roof. */
	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> RainOpen;

	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> RainRoof;

	/** Daylight in the open: sparse birdsong, silent at night and in rain. */
	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> Birds;

	/** The weather collection, read for how hard it is raining. */
	UPROPERTY(Transient)
	TObjectPtr<class UMaterialParameterCollection> Weathers;

	/** Chased rather than switched: a doorway is a tile wide. */
	float Indoors = 0.f;

	/**
	 * §6c: 0 to 1 through the hush over a death, on the same pace as the wash
	 * over the screen so the two read as one thing happening. The music is
	 * DIPPED rather than stopped: a piece plays once a session, and stopping
	 * it would spend the country's only music on a goblin.
	 */
	float Grief = 0.f;

	bool bBedIsA = true;
	float Fade = 1.f;              // 0..1 through the current cross-fade

	FName Standing;                // the word under the citizen right now
	FName Settled;                 // the word it has been for long enough
	float StandingFor = 0.f;

	/**
	 * THE PIECES ALREADY HEARD, FOR THE WHOLE SESSION.
	 *
	 * Each of the nine pieces plays at most once between launching the window
	 * and closing it, which is also the span of a citizen's daily allowance.
	 * "I think they should only play (max) once per playing session... so that
	 * even if a player for example starts at anchor then moves around the map
	 * then returns to anchor it doesn't play the soundtrack again. For scarcity
	 * so that the tracks are more memorable."
	 *
	 * KEYED ON THE PIECE, NOT ON THE GROUND, and that is the half of this that
	 * is a bug fix rather than a choice. Nine pieces cover thirty surface
	 * words: `floor`, `flag`, `cobble` and `plaza` are all the Anchor's, and
	 * `trail`, `trodden`, `causey`, `bridge`, `greenwood` and `forest` are all
	 * the road's. Held as words, walking off Anchor's flagstones onto its
	 * cobbles was a new country and started the same piece again, and a walk
	 * down a wooded road could start the road's piece six times.
	 *
	 * Nothing clears it. Leaving a country used to make it hearable again,
	 * which is what made this a visit rather than a session.
	 */
	TSet<FName> Heard;
};
