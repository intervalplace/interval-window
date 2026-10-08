// Copyright interval.
//
// THE WORLD'S OWN HOUR, POINTED AT THE WINDOW'S OWN SUN.
//
// Until this existed the window was permanently at noon on a fine day while
// the world was at whatever hour it was actually at -- a citizen could stand
// in a landscape at three in the morning and see full daylight, and two
// citizens in the same field could not agree on where their shadows fell.
//
// Nothing here decides anything. The bridge computes the sky from the shared
// ladder that every window uses, and hands over flat numbers: the sun is this
// far up, on this bearing, it is this overcast, it is raining this hard. This
// file turns those into a light, a fog and a sound of rain. It does not know
// what a season is, or how long a day is, or that weather is hashed off the
// day -- and that ignorance is what makes it impossible for this window to
// disagree with any other about the weather.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IntervalTypes.h"
#include "IntervalHour.generated.h"

class ADirectionalLight;
class ASkyLight;
class AExponentialHeightFog;
class UIntervalBridgeSubsystem;
class UStaticMeshComponent;
class UMaterialInstanceDynamic;

UCLASS()
class INTERVALBRIDGE_API AIntervalHour : public AActor
{
	GENERATED_BODY()

public:
	AIntervalHour();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;
	virtual void Tick(float DeltaSeconds) override;

	/**
	 * Move the sky to where this instant is, between the last two intervals.
	 *
	 * The world sends a sky once a second and the sun travels the whole second
	 * at once unless somebody interpolates it, which is this window's job
	 * between ticks. It uses the bridge's own interpolation fraction, the same
	 * one the citizens are walked by, so the sun and the people under it move
	 * on one clock. A forced hour is left exactly where the dial put it.
	 */
	void FollowSky();

	/** Brightest the sun gets, at noon on a clear day. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Light")
	float NoonBrightness = 6.2f;

	/**
	 * What is left when the sun is down.
	 *
	 * Not nothing. At a tenth of noon the island went to pitch and a citizen
	 * could not see the ground they were standing on, which is not what night
	 * is like anywhere that has a moon and is not what anybody wants to spend
	 * half of every twenty-four minutes looking at. Night here is dim, blue
	 * and legible.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Light")
	float NightBrightness = 0.55f;

	/**
	 * ---- WHAT THE SUN WAS LAST ACTUALLY SET TO ----
	 *
	 * Moving a directional light that a sky atmosphere is attached to makes
	 * the engine recompute the atmosphere's lookup tables and re-capture the
	 * sky light. This actor was setting the sun's rotation, intensity and
	 * colour EVERY FRAME, so both ran every frame: `SkyAtmosphereEditor` cost
	 * 5.5 ms of a 33 ms frame and `CaptureConvolveSkyEnvMap` spiked to 13.4.
	 *
	 * For nothing. A day here is 2400 intervals and an interval is a second,
	 * so the sun moves 0.15 degrees a second -- six thousandths of a degree in
	 * a frame at twenty-five. Below these thresholds the change is not
	 * describable on screen, let alone visible, and the work is the same as if
	 * the sun had crossed the sky.
	 */
	FRotator LastAim = FRotator(-1000.f, 0.f, 0.f);
	float LastIntensity = -1.f;
	FLinearColor LastTone = FLinearColor(-1.f, -1.f, -1.f, -1.f);

	/** The sky light's colour last set, so it is only written when it moves. */
	FLinearColor LastSkyTone = FLinearColor(-1.f, -1.f, -1.f, -1.f);

	/** Where the moon was last aimed and how bright it last was, so neither is
	 *  written to the light unless it actually moved. */
	FRotator LastMoonAim = FRotator(-999.f, -999.f, 0.f);
	float LastMoonLit = -1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Light")
	FLinearColor NoonColour = FLinearColor(1.f, 0.97f, 0.92f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Light")
	FLinearColor LowSunColour = FLinearColor(1.f, 0.62f, 0.34f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Light")
	FLinearColor NightColour = FLinearColor(0.42f, 0.54f, 0.86f);

	/**
	 * WHAT COLOUR THE SKY'S OWN LIGHT IS, which until now was nothing.
	 *
	 * The sun's colour has always followed the hour. The sky's never did: its
	 * INTENSITY was driven every tick and its colour was left at pure white,
	 * so roughly two thirds of the light in this world came from a source with
	 * no hour, no weather and no colour in it. That is the whole reason every
	 * hour looked like an overcast noon and why warming the grade barely
	 * registered -- a tint over a picture lit by white is still lit by white.
	 *
	 * Real skylight is the colour of the sky it falls out of: blue at midday,
	 * amber near the horizon, deep blue after dark, and washed toward grey
	 * under cloud, which is exactly what overcast MEANS.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	FLinearColor SkyDayColour = FLinearColor(0.62f, 0.74f, 1.f);

	/** The sky's light with the sun near the horizon: it goes amber too. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	FLinearColor SkyLowColour = FLinearColor(1.f, 0.78f, 0.55f);

	/** And after dark, which is deep rather than black. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	FLinearColor SkyNightColour = FLinearColor(0.30f, 0.40f, 0.74f);

	/**
	 * Cloud takes the colour out of the sky before it takes the light: an
	 * overcast day is bright and grey, not dim and blue.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	FLinearColor SkyOvercastColour = FLinearColor(0.88f, 0.90f, 0.94f);

	/** How thick the air gets when it is overcast, over whatever the level set. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Light")
	float OvercastFog = 2.6f;

	/** The sphere the stars are drawn on, and how far out it stands. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	TObjectPtr<UStaticMesh> DomeMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	TObjectPtr<UMaterialInterface> DomeMaterial;

	/** In centimetres. Big enough that the island is inside it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	float DomeRadius = 4000000.f;

	/** The rain curtain: a cylinder that rides with the camera. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Rain")
	TObjectPtr<class UStaticMesh> RainMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Rain")
	TObjectPtr<class UMaterialInterface> RainMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Rain")
	float RainRadius = 4500.f;

	/** How far out glow-worms are placed, in tiles. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Night", meta = (ClampMin = "2", ClampMax = "60"))
	int32 GlowReach = 26;

	/** Roughly how many tiles in a hundred carry one. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Night", meta = (ClampMin = "0", ClampMax = "100"))
	int32 GlowPerHundred = 14;

	/**
	 * Below zero, the world decides. At or above, this is how hard it rains
	 * whatever the world says -- for looking at weather that is not happening.
	 * A day is twenty-four minutes and the wet ones are hashed off the day, so
	 * waiting for rain to arrive is not a way to find out whether rain works.
	 *
	 * IT CHANGES NOTHING BUT PIXELS. Nobody gets wet, no yield moves, and the
	 * next frame from the bridge still says what it said.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Rain")
	float ForceRain = -1.f;

private:
	/** How hard it is raining right now: the asset's word, then this actor's, then the world's. */
	// Not `Sky` and not `Weather`: this actor already has a field of each
	// name -- a sky light and the curtain's material instance.
	float RainNow(const struct FIntervalSky& Aloft) const;

	/** How wide the curtain is: the asset's word, then this actor's. */
	float RainSpan() const;

	UFUNCTION()
	void HandleFrame();

	UPROPERTY(Transient) TObjectPtr<UIntervalBridgeSubsystem> Bridge;
	UPROPERTY(Transient) TObjectPtr<ADirectionalLight> Sun;

	/**
	 * ---- THE MOON ----
	 *
	 * There was none, and the absence was being paid for in a number:
	 * `NightBrightness` sits at 0.55 with a note saying a tenth of noon sent
	 * the island pitch black, "which is not what night is like anywhere that
	 * has a moon". So night was lit by a constant chosen to keep the ground
	 * visible, with nothing overhead to explain where that light came from.
	 *
	 * SPAWNED, AND SPAWNED LATE. The sun is found by taking the first
	 * `ADirectionalLight` in the world, so a second one placed in the level
	 * would be a coin toss over which is which. This one is made in code AFTER
	 * that search has run, which is the one ordering where the two cannot be
	 * confused.
	 *
	 * IT DOES NOT CAST SHADOWS. A second shadowed directional light is most of
	 * the cost of the first, and moonlight shadows are faint enough that
	 * nobody would find them. This is light, not geometry.
	 */
	UPROPERTY(Transient) TObjectPtr<ADirectionalLight> Moon;

	/** Brightest the moon gets, full and clear, against the sun's 6.2. */
	// Private, so it is EditAnywhere without BlueprintReadWrite: the header
	// guard refuses a blueprint-writable private member, correctly.
	UPROPERTY(EditAnywhere, Category = "Interval|Light")
	float MoonBrightness = 0.42f;

	/** Moonlight is the sun's light twice reflected: cool, and never white. */
	// Private, so it is EditAnywhere without BlueprintReadWrite: the header
	// guard refuses a blueprint-writable private member, correctly.
	UPROPERTY(EditAnywhere, Category = "Interval|Light")
	FLinearColor MoonColour = FLinearColor(0.62f, 0.72f, 1.f);

	/**
	 * How many intervals the moon takes to go round from full to full.
	 *
	 * A real month is far too long for a world whose day is twenty-four
	 * minutes: nobody would ever see a second full moon. This is eleven days
	 * of the world's own time, so a citizen who plays for a week watches it
	 * wax and wane once, and "wait for the dark of the moon" is a thing two
	 * people could actually agree on.
	 */
	// Private, so it is EditAnywhere without BlueprintReadWrite: the header
	// guard refuses a blueprint-writable private member, correctly.
	UPROPERTY(EditAnywhere, Category = "Interval|Light")
	int32 MoonPeriod = 19008;

	/** The world's own interval, kept so the moon's phase can be worked out. */
	int64 WorldTick = 0;
	UPROPERTY(Transient) TObjectPtr<ASkyLight> Sky;
	UPROPERTY(Transient) TObjectPtr<AExponentialHeightFog> Air;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Curtain;

	/**
	 * THE NIGHT SKY. A sphere big enough to hold the island, carrying the star
	 * material, centred on the citizen and drawn from the inside.
	 *
	 * Its SIZE and POSITION do not matter to what is drawn on it: the stars
	 * are worked out from the view ray, so they sit at infinity whatever the
	 * dome is doing. The sphere is only there to give the shader somewhere to
	 * run, and it rides with the citizen for the same reason the rain drum
	 * does -- so it is never behind them.
	 */
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Dome;

	/**
	 * THE SECOND DOME, which carries the rainbow.
	 *
	 * Inside the star dome and drawn the same way: additive, unlit, and worked
	 * out from the view ray, so its size and position are nothing but somewhere
	 * for the shader to run. `Bowed` is its own instance because the two things
	 * it is told -- which way the sun is and how much of a bow the world says
	 * there is -- are read by nothing else on the island, and the weather
	 * collection is the one asset here that cannot be added to lightly.
	 */
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Arc;

	/**
	 * THE MOON'S OWN DISC, hung on the dome beside the stars.
	 *
	 * A sphere, left to be lit by the real sun like anything else in the
	 * world. That is the whole trick: a lit sphere placed where the moon is
	 * shows the phase the moon actually has, so no material has to be told
	 * which crescent to draw and the disc cannot drift out of step with the
	 * light, because the two are the same geometry.
	 */
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Disc;

	/** How far off the moon's disc is hung, in centimetres. Far enough to sit
	 *  outside anything a citizen can climb and near enough to stay inside the
	 *  far plane. */
	UPROPERTY(EditAnywhere, Category = "Interval|Light")
	float MoonFar = 320000.f;

	/** How wide the disc is at that distance, in centimetres. */
	UPROPERTY(EditAnywhere, Category = "Interval|Light")
	float MoonWide = 9000.f;
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> Bowed;

	/**
	 * HOW MUCH OF A BOW IS BEING SHOWN, eased.
	 *
	 * The world's own number steps once an interval and a rainbow that snaps
	 * into the sky is a light being switched on. This is what is actually
	 * drawn, and it takes about ten seconds to arrive and about twenty to go,
	 * because that is the way of them: they come up as the rain clears and
	 * fade rather than stop.
	 */
	float BowShown = 0.f;

	UPROPERTY(Transient) TObjectPtr<class UInstancedStaticMeshComponent> Glimmer;
	UPROPERTY(Transient) TObjectPtr<class AIntervalGround> Ground;
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> GlowLit;
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> Weather;

	FIntervalSky Now;
	UPROPERTY(Transient) TObjectPtr<class UMaterialParameterCollection> Weathers;
	float Wetness = 0.f;
	bool  bSheltered = false;

	/**
	 * §7dq: HOW FAR UNDERGROUND, and whether the citizen brought a light.
	 *
	 * `bSheltered` above is a BUILDING: a roof, a doorway, and daylight coming
	 * in at the windows. A cave is not that. The Smother has rock over it and
	 * eight things in it that steel does nothing to, and the mouth refuses
	 * anybody not carrying fire -- so the dark is the rule rather than the
	 * weather, and it is read off the ground's name rather than off a roof
	 * footprint.
	 *
	 * `Want` is the target the frame sets; `Underground` eases toward it, so
	 * walking through the mouth is a fade. A torch burns down, so `bCarriedLight`
	 * can go false under somebody who is already inside.
	 */
	float UndergroundWant = 0.f;
	float Underground = 0.f;
	bool  bCarriedLight = false;
	float Indoors = 0.f;
	FIntPoint Lit = FIntPoint(MIN_int32, MIN_int32);
	FVector Standing = FVector::ZeroVector;
	bool bStanding = false;
	float BaseFog = -1.f;
};
