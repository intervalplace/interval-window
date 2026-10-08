// Copyright interval.

#include "IntervalHour.h"
#include "GameFramework/PlayerController.h"
#include "Camera/PlayerCameraManager.h"

#include "Components/DirectionalLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "IntervalGround.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"
#include "Engine/DirectionalLight.h"
#include "Engine/ExponentialHeightFog.h"
#include "Engine/SkyLight.h"
#include "EngineUtils.h"
#include "IntervalBridgeSubsystem.h"
#include "IntervalLook.h"
#include "IntervalGeometry.h"
#include "Materials/MaterialInstanceDynamic.h"

AIntervalHour::AIntervalHour()
{
	PrimaryActorTick.bCanEverTick = true;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));

	Curtain = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Rain"));
	Curtain->SetupAttachment(RootComponent);
	Curtain->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Curtain->SetCastShadow(false);
	Curtain->bVisibleInRayTracing = false;
	Curtain->SetVisibility(false);

	// THE STARS. Drawn from the inside of a very large sphere, so: no shadow,
	// no ray tracing, no collision, and nothing that would make the renderer
	// think it is a thing in the world rather than the far wall of it.
	Dome = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Dome"));
	Dome->SetupAttachment(RootComponent);
	Dome->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Dome->SetCastShadow(false);
	Dome->bVisibleInRayTracing = false;
	Dome->SetVisibility(false);

	// ---- AND THE MOON'S DISC ----
	//
	// Its own component rather than part of the star dome, because it MOVES
	// and the stars do not. It casts no shadow and is not collided with: it
	// is a very long way away and is scenery.
	//
	// IT IS LIT, NOT EMISSIVE, which is the whole of why this works. An
	// ordinary sphere with an ordinary material, standing where the moon
	// stands, is lit by the same sun that lights the island -- so it shows the
	// real phase without anything being told what a crescent looks like, and
	// it cannot fall out of step with the moonlight on the ground.
	Disc = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Disc"));
	Disc->SetupAttachment(RootComponent);
	Disc->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Disc->SetCastShadow(false);
	Disc->bVisibleInRayTracing = false;
	Disc->SetVisibility(false);

	Arc = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Arc"));
	Arc->SetupAttachment(RootComponent);
	Arc->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Arc->SetCastShadow(false);
	Arc->bVisibleInRayTracing = false;
	Arc->SetVisibility(false);

	Glimmer = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Glimmer"));
	Glimmer->SetupAttachment(RootComponent);
	Glimmer->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Glimmer->SetCastShadow(false);
	Glimmer->NumCustomDataFloats = 1;   // which glow-worm this is, for its own rhythm
	Glimmer->SetVisibility(false);
}

namespace
{
	// THE LIGHT AND THE FOG, IN A BUILD WITHOUT AN EDITOR IN IT.
	//
	// `ADirectionalLight::GetComponent()` and the fog actor's twin are
	// EDITOR-ONLY accessors. Everything here worked for as long as the window
	// only ever ran inside the editor, and the first attempt to package a
	// standalone client failed on eight lines of this file.
	//
	// The runtime accessor is `GetLightComponent()`, which answers the base
	// class; the cast is safe because the actor is a directional light by
	// construction. The fog actor's component is a plain UPROPERTY with a
	// getter that exists in both.
	UDirectionalLightComponent* Beam(ADirectionalLight* Light)
	{
		return Light ? Cast<UDirectionalLightComponent>(Light->GetLightComponent())
		             : nullptr;
	}

	UExponentialHeightFogComponent* Haze(AExponentialHeightFog* Fog)
	{
		return Fog ? Fog->GetComponent() : nullptr;
	}
}


void AIntervalHour::BeginPlay()
{
	Super::BeginPlay();

	// The level's own lights, whatever they are. A window that spawned its
	// own would end up with two suns the moment anybody placed one.
	TActorIterator<ADirectionalLight> FoundSun(GetWorld());
	Sun = FoundSun ? *FoundSun : nullptr;
	TActorIterator<ASkyLight> FoundSky(GetWorld());
	Sky = FoundSky ? *FoundSky : nullptr;
	TActorIterator<AExponentialHeightFog> FoundAir(GetWorld());
	Air = FoundAir ? *FoundAir : nullptr;

	// ---- THE SUN'S MOBILITY WARNING IS NOISE, AND WAS LEFT ALONE ----
	//
	// The level's directional light is Static and this actor turns it every
	// frame, so the engine says "Mobility of DirectionalLight_1 :
	// LightComponent0 has to be 'Movable' if you'd like to move" once per
	// frame, for ever. It looks like a frozen sun and is not one: forcing the
	// hour to two different times swings the shadows right across the ground,
	// which is the only test that matters.
	//
	// Setting the mobility here at BeginPlay was tried, to quiet it. It did
	// not quiet it, and the editor then died on the NEXT teardown of the play
	// session with a null in shutdown -- so a cosmetic log fix bought a crash.
	// If it is ever worth doing it belongs on the level's light itself, not on
	// a component the editor is already holding.

	// ---- AND THE MOON, MADE HERE AND NOT BEFORE ----
	//
	// After the search above, so `TActorIterator<ADirectionalLight>` cannot
	// pick it up and mistake it for the sun. See the note on `Moon`.
	if (!Moon)
	{
		FActorSpawnParameters How;
		How.ObjectFlags |= RF_Transient;
		Moon = GetWorld()->SpawnActor<ADirectionalLight>(
			ADirectionalLight::StaticClass(), FTransform::Identity, How);
		if (Moon)
		{
			// A NAME IN THE OUTLINER IS AN EDITOR-ONLY THING, and this was not
			// guarded. `SetActorLabel` does not exist in a game target, so the
			// plugin compiled for `intervalEditor` and failed for `interval`:
			// every packaged client since the moon went in has been the last
			// binary that built, silently, because the editor never stopped
			// working. `IntervalGround.cpp` already wraps its own label this
			// way and that is the convention I missed.
#if WITH_EDITOR
			Moon->SetActorLabel(TEXT("Moon"));
#endif
			if (UDirectionalLightComponent* Beamlet =
					Cast<UDirectionalLightComponent>(Moon->GetLightComponent()))
			{
				Beamlet->SetCastShadows(false);
				Beamlet->SetIntensity(0.f);
				Beamlet->SetLightColor(MoonColour);
				// It must not take the atmosphere over from the sun: only one
				// directional light may own the sky, and that one is the sun.
				Beamlet->SetAtmosphereSunLight(false);
				// ---- NOR THE FORWARD PASS ----
				//
				// `SetAtmosphereSunLight(false)` is not enough on its own and
				// the editor says so in red across the top of the viewport:
				// "Multiple directional lights are competing to be the single
				// one used for forward shading, translucent, water or
				// volumetric fog." Left alone the engine picks whichever is
				// BRIGHTER, so at night the moon would quietly take over the
				// water and the volumetric haze from the sun.
				//
				// Priority is a plain ranking and the sun wins it always.
				Beamlet->ForwardShadingPriority = 0;
				if (Sun)
				{
					if (UDirectionalLightComponent* Boss =
							Cast<UDirectionalLightComponent>(Sun->GetLightComponent()))
					{
						Boss->ForwardShadingPriority = 10;
						Boss->MarkRenderStateDirty();
					}
				}
				Beamlet->MarkRenderStateDirty();
			}
		}
	}

	// ---- AND A FLOOR UNDER THE SHADE, SET ONCE ----
	//
	// The sky light's occlusion had no floor: anything the sky could not see
	// directly got NO sky at all, so the shaded side of a wall, or a lane
	// between two of them, came out as a void. It read as broken geometry
	// rather than as shadow -- a settlement looked like a row of black slabs
	// with brick tops, and the first question anybody asked about it was
	// whether the walls were rotated the wrong way. They were not; there was
	// simply no light on three of their four sides.
	//
	// A floor of a little over half means a surface in full shade still gets
	// half the sky, which is what standing in the shade of a wall on a bright
	// day actually looks like, and the tint is the colour of that sky rather
	// than black. The radius is pulled in so the effect is contact shading
	// between near surfaces instead of a whole lane being darkened by walls
	// ten metres away.
	if (Sky && Sky->GetLightComponent())
	{
		// `Vault`, because `Dome` is already a field on this actor.
		USkyLightComponent* Vault = Sky->GetLightComponent();
		Vault->SetMobility(EComponentMobility::Movable);
		// ---- AND IT HAS TO KEEP LOOKING AT THE SKY ----
		//
		// A sky light captures the world around it ONCE and then multiplies
		// that capture by its intensity for ever. This one was made movable so
		// the hour could drive it, and the intensity was raised to six -- and
		// none of that mattered, because six times a capture taken against a
		// black sky is still black. Every face the sun could not see came out
		// as a pure black cut-out, which is precisely what a wall in the shade
		// looked like: "why do the walls here look like cardboard".
		//
		// Real-time capture is what a movable sky light in front of a sky
		// atmosphere is for. The dome is then re-read as the sun moves, so the
		// shaded side of a wall at noon is lit by the blue of the sky above it
		// -- which is what standing in shade on a bright day actually looks
		// like -- and dusk warms the shadows instead of switching them off.
		Vault->SourceType = ESkyLightSourceType::SLS_CapturedScene;
		Vault->bRealTimeCapture = true;
		Vault->MinOcclusion = 0.55f;
		Vault->OcclusionTint = FColor(110, 122, 140, 255);
		Vault->OcclusionMaxDistance = 300.f;
		Vault->bLowerHemisphereIsBlack = false;
		Vault->MarkRenderStateDirty();
	}

	if (Sun && Beam(Sun))
	{
		// A light that is not movable cannot follow an hour.
		Beam(Sun)->SetMobility(EComponentMobility::Movable);
		Sun->SetActorEnableCollision(false);
	}
	if (Sky && Sky->GetLightComponent())
	{
		Sky->GetLightComponent()->SetMobility(EComponentMobility::Movable);
	}
	if (Air && Haze(Air))
	{
		// THE LOOK DECIDES HOW THICK THE AIR IS, and the level is the fallback
		// rather than the other way round. This used to take whatever density
		// the level's fog actor carried, which made the one number that
		// decides how far you can see the only atmospheric value not authored
		// with the rest. See IntervalLook::AirDensity.
		const UIntervalLook* Wardrobe = UIntervalLook::Resolve(nullptr);
		BaseFog = (Wardrobe && Wardrobe->AirDensity >= 0.f)
			? Wardrobe->AirDensity
			: Haze(Air)->FogDensity;
	}
	// The curtain comes from the look asset, like everything else that has to
	// survive a rebuild; the properties on this actor are only a fallback for
	// a project that has no look.
	const UIntervalLook* Look = UIntervalLook::Resolve(nullptr);
	UStaticMesh* Drum = (Look && Look->RainMesh) ? Look->RainMesh.Get() : RainMesh.Get();
	UMaterialInterface* Streaks = (Look && Look->RainMaterial)
		? Look->RainMaterial.Get() : RainMaterial.Get();
	UE_LOG(LogTemp, Log, TEXT("[interval] curtain: look=%s drum=%s streaks=%s component=%s"),
		Look ? TEXT("yes") : TEXT("NO"),
		Drum ? *Drum->GetName() : TEXT("NULL"),
		Streaks ? *Streaks->GetName() : TEXT("NULL"),
		Curtain ? TEXT("yes") : TEXT("NO"));
	if (Drum && Streaks && Curtain)
	{
		Curtain->SetStaticMesh(Drum);
		Weather = UMaterialInstanceDynamic::Create(Streaks, this);
		Curtain->SetMaterial(0, Weather);
	}

	// THE STAR DOME, from the look for the same reason the curtain is.
	if (Look && Look->StarMesh && Look->StarMaterial && Dome)
	{
		Dome->SetStaticMesh(Look->StarMesh);
		Dome->SetMaterial(0, Look->StarMaterial);
	}
	// AND THE MOON'S, the same way. Without a mesh there is simply no disc and
	// the moonlight still works, which is the right way round: the light is
	// the part that matters and the picture in the sky is the part that is
	// nice to have.
	if (Look && Look->MoonMesh && Disc)
	{
		Disc->SetStaticMesh(Look->MoonMesh);
		if (Look->MoonMaterial) { Disc->SetMaterial(0, Look->MoonMaterial); }
		Disc->SetWorldScale3D(FVector(MoonWide / 100.f));
	}

	// AND THE BOW'S, on its own instance because it is told two things a frame.
	if (Look && Look->BowMesh && Look->BowMaterial && Arc)
	{
		Arc->SetStaticMesh(Look->BowMesh);
		Bowed = UMaterialInstanceDynamic::Create(Look->BowMaterial, this);
		Arc->SetMaterial(0, Bowed);
	}

	if (Look && Look->GlowMesh && Glimmer)
	{
		Glimmer->SetStaticMesh(Look->GlowMesh);
		if (Look->GlowMaterial)
		{
			GlowLit = UMaterialInstanceDynamic::Create(Look->GlowMaterial, this);
			Glimmer->SetMaterial(0, GlowLit);
		}
	}
	// THE ONE PLACE EVERY MATERIAL READS THE WEATHER FROM. Without it, telling
	// the ground it is raining means finding a hundred and twelve chunk
	// materials and setting each, and the thatch and the timber could not be
	// told at all.
	Weathers = LoadObject<UMaterialParameterCollection>(
		nullptr, TEXT("/Game/Interval/MPC_IntervalSky.MPC_IntervalSky"));

	TActorIterator<AIntervalGround> FoundGround(GetWorld());
	Ground = FoundGround ? *FoundGround : nullptr;

	if (const UGameInstance* GI = GetGameInstance())
	{
		Bridge = GI->GetSubsystem<UIntervalBridgeSubsystem>();
		if (Bridge) { Bridge->OnFrame.AddDynamic(this, &AIntervalHour::HandleFrame); }
	}
}

void AIntervalHour::EndPlay(const EEndPlayReason::Type Reason)
{
	if (Bridge) { Bridge->OnFrame.RemoveDynamic(this, &AIntervalHour::HandleFrame); }
	Super::EndPlay(Reason);
}

float AIntervalHour::RainNow(const FIntervalSky& Aloft) const
{
	// THE ASSET FIRST, THEN THIS ACTOR, THEN THE WORLD.
	//
	// The override used to live only on this actor, and a level-placed actor's
	// saved value beats the C++ default -- so changing the default did nothing
	// and did it silently, which cost an hour of photographing dry meadows.
	if (const UIntervalLook* Wardrobe = UIntervalLook::Resolve(nullptr))
	{
		if (Wardrobe->ForceRain >= 0.f) { return Wardrobe->ForceRain; }
	}
	if (ForceRain >= 0.f) { return ForceRain; }
	return Aloft.Rain;
}

float AIntervalHour::RainSpan() const
{
	if (const UIntervalLook* Wardrobe = UIntervalLook::Resolve(nullptr))
	{
		if (Wardrobe->RainRadius > 0.f) { return Wardrobe->RainRadius; }
	}
	return RainRadius;
}

void AIntervalHour::HandleFrame()
{
	// The frame is READ rather than handed over: a dynamic delegate copies
	// whatever it carries, and what this used to carry was the whole world.
	// See FIntervalFrameEvent in IntervalBridgeSubsystem.h.
	if (!Bridge) { return; }
	const FIntervalFrame& Frame = Bridge->GetFrame();
	if (Frame.Sky.bValid) { Now = Frame.Sky; }
	// The moon's phase is a fact about the world's clock, not about this
	// window, so every window shows the same moon on the same night.
	WorldTick = Frame.Tick;

	// ---- §7dq: AND WHETHER THERE IS SKY OVERHEAD AT ALL ----
	//
	// The Smother is a cave in the Cragscar with eight quenchers in it. Steel
	// passes through them, only fire tells, and the mouth refuses anybody not
	// carrying a light. The whole place is built on the dark: its own note in
	// the generator says the mouth needs no marker "because the dark either
	// side of it is the marker".
	//
	// There was no dark. The sun does not care what is over a tile, so a cave
	// was lit exactly like the fellside outside it, and a citizen walked into
	// the one place in the world that is about the absence of light and found
	// it at noon. `Surface` carries the ground's name now, and `cave` is the
	// one this has to answer to.
	//
	// SET AS A TARGET, NOT AS A STATE. Walking in and out is a step, so a
	// boolean here would snap the sun off between two frames and read as a
	// bug. The approach is eased in Tick, over about three quarters of a
	// second, which is the time it takes to walk through a mouth.
	UndergroundWant = Frame.Surface.Equals(TEXT("cave"), ESearchCase::IgnoreCase)
		? 1.f : 0.f;
	// And what the citizen is carrying, because in a cave that is the only
	// light there is. The engine answers this (§7dq-iii) and a torch burns
	// down, so it goes false under somebody standing in the dark.
	bCarriedLight = Frame.bLit;

	// THE HOUR, OVERRIDDEN, FOR LOOKING. A day is long in wall-clock terms and
	// a change to the ground photographed at midnight is not a check. When a
	// level asks for an hour, the sun is put where that hour would put it and
	// everything downstream -- the light, the fog, the wetness, the fires --
	// follows from the same numbers it always did.
	if (const UIntervalLook* Wardrobe = UIntervalLook::Resolve(nullptr))
	{
		if (Wardrobe->ForceDay >= 0.f)
		{
			// ---- THE SAME ARITHMETIC THE WORLD USES, NOT AN IMITATION ----
			//
			// This invented its own: elevation lerped over -14 to +58 degrees,
			// warmth as a straight line, daylight equal to the dial. All three
			// were wrong, and wrong in ways that hid one another.
			//
			// `sky.mjs` is the truth and it is four lines long:
			//
			//     elev    = sin(dayF * 2pi)
			//     elevDeg = elev * 62
			//     dayAmt  = clamp(elev * 4, 0, 1)
			//     warm    = clamp(1 - |elev| * 2.6, 0, 1)
			//
			// The RANGE matters most. The world puts the sun sixty-two degrees
			// under at midnight, far past the end of astronomical twilight and
			// properly dark. This override could not reach below fourteen,
			// which is nautical twilight -- so every "night" anybody ever
			// pinned for a photograph was in fact dusk, the sky stayed grey,
			// and the obvious conclusion was that the world's night was
			// broken. It was not. The dial was.
			//
			// `ForceDay` is the world's own `dayF` now: 0 is sunrise, a
			// quarter is noon, a half is sunset, three quarters is midnight.
			const float DayF = FMath::Clamp(Wardrobe->ForceDay, 0.f, 1.f);
			const float E = FMath::Sin(DayF * 2.f * PI);
			Now.ElevationDeg = E * 62.f;
			Now.DayAmount = FMath::Clamp(E * 4.f, 0.f, 1.f);
			Now.Warm = FMath::Clamp(1.f - FMath::Abs(E) * 2.6f, 0.f, 1.f);

		}
		if (Wardrobe->ForceBow >= 0.f)
		{
			Now.Rainbow = FMath::Clamp(Wardrobe->ForceBow, 0.f, 1.f);
		}
		// AND HERE AS WELL AS IN `FollowSky`, because `FollowSky` returns
		// early when the hour is forced -- and "a clear noon" is the one
		// request that forces both. Applied in only one of the two places,
		// this dial did nothing in the only case anybody would reach for it,
		// and the photograph taken to prove the sky was fine came back
		// overcast with the override apparently set.
		if (Wardrobe->ForceCloud >= 0.f)
		{
			Now.Overcast = FMath::Clamp(Wardrobe->ForceCloud, 0.f, 1.f);
		}
	}
	// WHERE THE WEATHER HAS TO BE, which is around whoever is in it. The
	// obvious anchor is the camera, and it is wrong twice: there is no player
	// controller at all while the editor is simulating, so the curtain sat at
	// the world origin and it rained in the sea; and a camera is not a person.
	// The citizen is a place the world actually named.
	if (Frame.bHasMe)
	{
		Standing = UIntervalGeometry::TileToWorld(Frame.Me.X, Frame.Me.Y);
		bStanding = true;
		// UNDER A ROOF, RAIN STOPS. The window already works out which tiles a
		// building covers -- it is how the walls know what house they belong
		// to -- so whether a citizen is indoors is a thing it can simply look
		// up. Rain falling through a thatched roof onto somebody's hearth is
		// the sort of detail whose absence nobody can name and whose presence
		// everybody feels.
		bSheltered = Ground && Ground->BuildingKeyAtTile(Frame.Me.X, Frame.Me.Y) != 0;
	}
}

// ---- THE SKY BETWEEN TWO INTERVALS ----
//
// Everything in a sky is a plain number except two, and those two go round.
// `Bearing` is degrees clockwise from north and `DayFraction` runs 0 to 1 and
// starts again, so a straight lerp across the seam -- 359 degrees to 1, or
// 0.99 to 0.01 -- sends the sun the long way round at tremendous speed, once
// per day, which is a worse fault than the one being fixed.
static float TweenDegrees(float From, float To, float Through)
{
	// The shortest way round, so the sun never spins backwards through north.
	return From + FMath::UnwindDegrees(To - From) * Through;
}

static float TweenCycle(float From, float To, float Through)
{
	float Gap = To - From;
	if (Gap > 0.5f) { Gap -= 1.f; }
	else if (Gap < -0.5f) { Gap += 1.f; }
	float At = From + Gap * Through;
	if (At < 0.f) { At += 1.f; }
	else if (At >= 1.f) { At -= 1.f; }
	return At;
}

static FIntervalSky BetweenSkies(const FIntervalSky& From, const FIntervalSky& To,
	float Through)
{
	FIntervalSky Out = To;
	Out.ElevationDeg = FMath::Lerp(From.ElevationDeg, To.ElevationDeg, Through);
	Out.DayAmount    = FMath::Lerp(From.DayAmount,    To.DayAmount,    Through);
	Out.Warm         = FMath::Lerp(From.Warm,         To.Warm,         Through);
	Out.Overcast     = FMath::Lerp(From.Overcast,     To.Overcast,     Through);
	Out.Rain         = FMath::Lerp(From.Rain,         To.Rain,         Through);
	Out.Aurora       = FMath::Lerp(From.Aurora,       To.Aurora,       Through);
	Out.Rainbow      = FMath::Lerp(From.Rainbow,      To.Rainbow,      Through);
	Out.Spring       = FMath::Lerp(From.Spring,       To.Spring,       Through);
	Out.Autumn       = FMath::Lerp(From.Autumn,       To.Autumn,       Through);
	Out.Winter       = FMath::Lerp(From.Winter,       To.Winter,       Through);
	Out.Bearing      = TweenDegrees(From.Bearing,     To.Bearing,      Through);
	Out.DayFraction  = TweenCycle(From.DayFraction,   To.DayFraction,  Through);
	return Out;
}

// ---- THE SUN MOVES BETWEEN INTERVALS, NOT AT THEM ----
//
// `HandleFrame` took the sky straight off the frame, and a frame arrives once
// a second, so the sun jumped a whole second of travel at a time: "last night
// I saw the sun set and it didn't move smoothly, it ticked once per interval
// like a second hand of a watch". Everything downstream followed the same
// staircase, which is why a sunset showed it worst: the light, the fog and the
// warmth all step together at the moment the elevation does.
//
// The window already knows how to do this and the sun was the one thing not
// using it. `GetInterpAlpha` is how far through the current interval we are,
// smoothed against the jitter of a frame crossing a socket, and it is the same
// number the citizens are walked by -- so the sun now moves in step with the
// people standing under it rather than on a clock of its own.
void AIntervalHour::FollowSky()
{
	if (!Bridge)
	{
		return;
	}
	const UIntervalLook* Wardrobe = UIntervalLook::Resolve(nullptr);
	// A FORCED HOUR DOES NOT EASE. The dial is set and the photograph is taken
	// in the same breath, so a sun halfway to the hour that was asked for is a
	// worse answer than no dial at all. `HandleFrame` has already put the sky
	// exactly where the dial says; leave it alone.
	if (Wardrobe && Wardrobe->ForceDay >= 0.f)
	{
		return;
	}
	const FIntervalSky& To = Bridge->GetFrame().Sky;
	const FIntervalSky& From = Bridge->GetPreviousFrame().Sky;
	if (!To.bValid)
	{
		return;
	}
	Now = From.bValid
		? BetweenSkies(From, To, FMath::Clamp(Bridge->GetInterpAlpha(), 0.f, 1.f))
		: To;
	// AND THE OVERRIDES THAT ARE NOT THE HOUR still stand, because they are
	// set independently of it. Re-applied after the tween rather than before,
	// since the tween rebuilds the whole sky from the two frames.
	if (Wardrobe && Wardrobe->ForceBow >= 0.f)
	{
		Now.Rainbow = FMath::Clamp(Wardrobe->ForceBow, 0.f, 1.f);
	}
	// The cloud, for the same reason and in the same place. See the note on
	// `ForceCloud`: it is the knob that decides whether a day is grey, and the
	// rain override was never it.
	if (Wardrobe && Wardrobe->ForceCloud >= 0.f)
	{
		Now.Overcast = FMath::Clamp(Wardrobe->ForceCloud, 0.f, 1.f);
	}
}

void AIntervalHour::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	// BEFORE ANYTHING READS IT. Everything below works off `Now`, so the sky
	// has to be moved to where this instant actually is first.
	FollowSky();
	if (!Now.bValid)
	{
		return;
	}

	// ---- WHERE THE SUN IS ----
	// Bearing is degrees clockwise from north and elevation is degrees above
	// the horizon; a light points ALONG its forward vector, so a sun that is
	// up must point down. Below the horizon it is held a little under, so the
	// night keeps a direction to it rather than snapping about.
	const float Elev = FMath::Max(Now.ElevationDeg, -8.f);
	const FRotator Aim(-Elev, Now.Bearing + 180.f, 0.f);

	const float Day = FMath::Clamp(Now.DayAmount, 0.f, 1.f);
	const float Dim = FMath::Lerp(1.f, 0.34f, FMath::Clamp(Now.Overcast, 0.f, 1.f));
	// §7dq: ...and rock over your head beats any weather. Eased with the same
	// `FInterpTo` the shelter below uses, for the same reason it gives: "a
	// doorway is a tile wide and stepping across it should not switch the
	// weather off like a light". A cave mouth is a tile wide too.
	Underground = FMath::FInterpTo(Underground, UndergroundWant, DeltaSeconds, 2.4f);
	// A FLOOR, NOT A BLACKOUT. The same argument the sky light's floor makes
	// above: "a black night is a night nobody plays through". A citizen who
	// walks in without a light should be unable to see what is coming, which
	// is the point of the gate, and should still be able to find the way out.
	// Six per cent of the daylight is that: shapes and no detail.
	const float Roof = FMath::Lerp(1.f, bCarriedLight ? 0.16f : 0.06f, Underground);

	if (Sun && Beam(Sun))
	{
		UDirectionalLightComponent* Shine = Beam(Sun);
		// ---- ONLY WHEN IT HAS ACTUALLY MOVED ----
		//
		// See the note over `LastAim` in the header. Setting any of these
		// three makes the engine rebuild the sky atmosphere's tables and
		// re-capture the sky light, and this did all three every frame while
		// the sun crosses the sky at 0.15 degrees a SECOND.
		//
		// A twentieth of a degree is about a third of an interval's movement,
		// so the sun still steps several times a second and no eye can find
		// the step. The thresholds on the other two are the same idea: a
		// thousandth of the noon intensity, and a colour change nothing can
		// name.
		const float Want = FMath::Lerp(NightBrightness, NoonBrightness * Dim, Day) * Roof;
		// Warm is how near the horizon the sun is, which is the whole of why
		// evening light is orange: a longer path through more air.
		FLinearColor Tone = FMath::Lerp(NoonColour, LowSunColour, FMath::Clamp(Now.Warm, 0.f, 1.f));
		// ---- AND THE BLUE OF NIGHT ONLY ONCE THE SUN HAS GONE ----
		//
		// This read `Lerp(NightColour, Tone, Day)`, which mixed the night's
		// blue into the sun by however far the daylight fell short of full --
		// and `Warm` rises on exactly the same falling sun. So the two fought:
		// at a low sun the tone went orange and was then pulled a fifth of the
		// way back toward (0.42, 0.54, 0.86) in the same breath. Measured at
		// four degrees of elevation the light came out (244, 221, 206), barely
		// warm at all, where the warmth asked for was about (255, 194, 146).
		//
		// Night is the sun being DOWN, not the daylight being less than
		// perfect. Above the horizon there is no blue in sunlight; below it,
		// over about six degrees, there is nothing else.
		const float Gone = FMath::Clamp(-Now.ElevationDeg / 6.f, 0.f, 1.f);
		Tone = FMath::Lerp(Tone, NightColour, Gone);

		if (!Aim.Equals(LastAim, 0.05f))
		{
			Sun->SetActorRotation(Aim);
			LastAim = Aim;
		}
		if (FMath::Abs(Want - LastIntensity) > NoonBrightness * 0.001f)
		{
			Shine->SetIntensity(Want);
			LastIntensity = Want;
		}
		if (!Tone.Equals(LastTone, 0.002f))
		{
			Shine->SetLightColor(Tone);
			LastTone = Tone;
		}
	}
	// ---- THE MOON ----
	//
	// THE PHASE IS WHERE IT IS, NOT HOW BRIGHT IT IS. The first cut aimed the
	// moon permanently opposite the sun and faked the phase with a brightness
	// curve, which is wrong twice over: opposite the sun IS full, so the disc
	// would have read full on every night of the cycle while its own light
	// said otherwise, and a new moon would have hung at midnight as a dark
	// hole in the sky.
	//
	// A moon is where it is because of its phase. New moon sits with the sun
	// and is a daytime object nobody notices; full moon sits opposite and is
	// up the whole night; the quarters stand ninety degrees off. Carry the
	// phase in the POSITION and all of it falls out by itself, including how
	// much of the disc the sun lights -- which is the phase anybody actually
	// looks at.
	//
	// THE PATH IS APPROXIMATED, KNOWINGLY. The world says where the sun is
	// NOW, not where it would be at another hour, so the sky's arc is taken as
	// a sine: read the sun's elevation back into an angle, add the phase, take
	// an elevation forward again. This is not astronomy and does not need to
	// be. It puts the moon in the right part of the sky at the right phase,
	// which is all anybody can check from the ground.
	if (Moon && Moon->GetLightComponent())
	{
		const float Phase = MoonPeriod > 0
			? static_cast<float>(static_cast<double>(
					((WorldTick % MoonPeriod) + MoonPeriod) % MoonPeriod)
				/ static_cast<double>(MoonPeriod))
			: 0.5f;
		const float Top = 58.f;
		const float SunAngle = FMath::Asin(
			FMath::Clamp(Now.ElevationDeg / Top, -1.f, 1.f));
		const float MoonAngle = SunAngle + Phase * 2.f * PI;
		const float MoonElev = Top * FMath::Sin(MoonAngle);
		const float MoonBear = Now.Bearing + Phase * 360.f;

		// How much of it the sun lights: nothing when it shares the sky with
		// the sun, all of it when it is opposite. The same number that placed
		// it decides how bright it is, so disc and light cannot disagree.
		// `Shown`, not `Lit`: the actor already has a field of that name.
		const float Shown = 0.5f - 0.5f * FMath::Cos(Phase * 2.f * PI);
		const float Up = FMath::Clamp((MoonElev + 2.f) / 8.f, 0.f, 1.f);
		// And daylight drowns it long before it sets.
		const float Dark = FMath::Clamp(-Now.ElevationDeg / 8.f, 0.f, 1.f);
		const float Want = MoonBrightness * Shown * Up * Dark
			* FMath::Lerp(1.f, 0.2f, FMath::Clamp(Now.Overcast, 0.f, 1.f));

		// A light points ALONG its forward vector, so it is aimed from the
		// moon toward the ground: the same half-turn the sun's aim takes.
		const FRotator MoonAim(-MoonElev, MoonBear + 180.f, 0.f);
		if (!MoonAim.Equals(LastMoonAim, 0.05f))
		{
			Moon->SetActorRotation(MoonAim);
			LastMoonAim = MoonAim;
		}
		if (FMath::Abs(Want - LastMoonLit) > 0.002f)
		{
			Moon->GetLightComponent()->SetIntensity(Want);
			LastMoonLit = Want;
		}
		if (Disc)
		{
			const FVector Out = FRotationMatrix(
				FRotator(MoonElev, MoonBear, 0.f)).GetUnitAxis(EAxis::X);
			Disc->SetRelativeLocation(Out * MoonFar);
			// Shown whenever it is above the horizon at all, lit or not: a new
			// moon against a dusk sky is a real thing to see.
			Disc->SetVisibility(MoonElev > -2.f, true);
		}
	}

	if (Sky && Sky->GetLightComponent())
	{
		// The sky itself is most of the light on an overcast day and nearly
		// all of it at night, so it does not fade with the sun.
		// The sky is most of the light on an overcast day and nearly all of it
		// at night, so it does not fade with the sun -- and it does not fade
		// far. A black night is a night nobody plays through.
		// AND HOW MUCH OF IT REACHES THE GROUND. See `SkyLift` on the look
		// asset: with the capture taken at face value every surface the sun
		// cannot see came out black, which is not what standing in the shade
		// of a wall on a bright day looks like.
		float Lift = 1.f;
		if (const UIntervalLook* Wardrobe = UIntervalLook::Resolve(nullptr))
		{
			Lift = FMath::Max(Wardrobe->SkyLift, 0.f);
		}
		// AND A REAL DAY IN IT. This read `Lerp(0.85, 1.0, Day)` -- a night
		// with eighty-five per cent of noon's ambient, which is not a night.
		// It also made `SkyLift` useless as a knob: raising it far enough to
		// put light on the shaded side of a wall at midday lit the whole world
		// at midnight by the same amount, so it had been left at 1.9, which is
		// too little for either. Separating the two lets the day be lifted a
		// long way without touching the dark.
		//
		// AND THEN IT WAS LIFTED TOO FAR. Freed to rise, `SkyLift` went to SIX
		// on the look asset, which put the sky light at 6.4 against a sun of
		// 2.9: better than two thirds of all the light in the world arriving
		// from a source that casts no shadow. Every surface got lit from
		// everywhere, shadows went shallow, colour washed out, and the whole
		// island read as a model of itself under a softbox. It is the reason
		// daylight looked grey, and no amount of grading could have fixed it,
		// because the fault was in the light and not in the picture.
		//
		// Measured at noon, 6.0 against 2.2: mean luma 107 -> 91, saturation
		// 22 -> 26, and the sea, the thatch and the fields all get their
		// colour back. The dial lives on the look asset so it can be moved
		// without a rebuild; if the shaded side of a wall ever goes too dark
		// the answer is the occlusion floor below, not another lift here.
		//
		// The floor is not zero and is not meant to be: a black night is a
		// night nobody plays through, and this world is played at all hours.
		Sky->GetLightComponent()->SetIntensity(Lift *
			FMath::Lerp(0.14f, 1.0f, Day) * FMath::Lerp(1.f, 1.35f, Now.Overcast) * Roof);

		// ---- AND ITS COLOUR, WHICH NOTHING HAD EVER SET ----
		//
		// This light was pure white at every hour of every day. It is the
		// larger half of the light in this world -- measured at a clear
		// morning it ran 6.4 against the sun's 2.9 -- so the sun could be as
		// orange as it liked and the picture stayed neutral. See the note
		// beside `SkyDayColour`.
		//
		// The night blend is keyed on the sun being BELOW the horizon, not on
		// the daylight falling short, for the same reason the sun's is: keyed
		// the other way the two cancel, and the hour that is supposed to be
		// warmest comes out the least warm of all.
		const float SkyGone = FMath::Clamp(-Now.ElevationDeg / 6.f, 0.f, 1.f);
		FLinearColor SkyTone = FMath::Lerp(
			SkyDayColour, SkyLowColour, FMath::Clamp(Now.Warm, 0.f, 1.f));
		SkyTone = FMath::Lerp(SkyTone, SkyNightColour, SkyGone);
		// Cloud last, because it takes colour OUT of whatever the sky was.
		SkyTone = FMath::Lerp(SkyTone, SkyOvercastColour,
			FMath::Clamp(Now.Overcast, 0.f, 1.f));
		if (!SkyTone.Equals(LastSkyTone, 0.002f))
		{
			Sky->GetLightComponent()->SetLightColor(SkyTone);
			LastSkyTone = SkyTone;
		}
	}
	if (Air && Haze(Air) && BaseFog > 0.f)
	{
		UExponentialHeightFogComponent* Mist = Haze(Air);
		const float Wet = FMath::Max(Now.Overcast, Now.Rain);
		Mist->SetFogDensity(BaseFog * FMath::Lerp(1.f, OvercastFog, Wet));

		// ---- AND THE AIR ITSELF ----
		//
		// Everything above is a haze on the horizon: a tint applied to what is
		// already drawn, which knows nothing about what is standing in front
		// of it. The volumetric path makes the fog a MEDIUM -- the sun throws
		// shafts through a gap in a roof, a hearth glows in the air around
		// itself after dark, and the smoke leaving every chimney is lit rather
		// than pasted on.
		if (const UIntervalLook* Wardrobe = UIntervalLook::Resolve(nullptr))
		{
			Mist->SetVolumetricFog(Wardrobe->bVolumetricAir);
			if (Wardrobe->bVolumetricAir)
			{
				Mist->SetVolumetricFogDistance(FMath::Max(1000.f, Wardrobe->HazeDepth));
				Mist->SetVolumetricFogScatteringDistribution(
					FMath::Clamp(Wardrobe->HazeForward, -0.9f, 0.9f));
				Mist->SetVolumetricFogAlbedo(Wardrobe->HazeTint.ToFColor(true));
				// THICKER WHEN IT IS WET AND THINNER AT NIGHT.
				//
				// Wet air holds more of what light passes through it, which is
				// why a rainy afternoon has visible beams and a clear one has
				// almost none. The night is thinned deliberately and not
				// physically: at full strength every hearth on the island
				// became a lantern in a sea fog and the village stopped having
				// any dark in it at all.
				Mist->SetVolumetricFogExtinctionScale(
					FMath::Lerp(0.8f, 2.4f, Wet) * FMath::Lerp(0.55f, 1.f, Day));
			}
		}
	}

	// HOW MUCH OF THE SUN THE AIR CATCHES. Separate from the light's own
	// intensity: a bright sun through clean air throws no beam at all, and it
	// is the air that decides, not the sun.
	if (Sun && Beam(Sun))
	{
		float Catch = 1.f;
		if (const UIntervalLook* Wardrobe = UIntervalLook::Resolve(nullptr))
		{
			Catch = FMath::Max(0.f, Wardrobe->SunHaze);
		}
		Beam(Sun)->SetVolumetricScatteringIntensity(Catch);
	}

	// ---- TELLING EVERYTHING ELSE ----
	// Wet is not rain: ground stays dark and shining for a while after a
	// shower and takes a while to darken when one starts, the way real ground
	// does. So it chases the rain rather than tracking it.
	{
		// HOW FAR INDOORS, eased. Not a hard cut: a doorway is a tile wide and
		// stepping across it should not switch the weather off like a light.
		//
		// Worked out HERE rather than beside the rain, where it used to live.
		// Down there it sat inside `if (Curtain)`, so on a build with no rain
		// curtain it stayed at nought for ever -- which did not matter while
		// only the rain read it, and does now that the walls do.
		Indoors = FMath::FInterpTo(Indoors, bSheltered ? 1.f : 0.f, DeltaSeconds, 3.2f);
		const float Falling = RainNow(Now);
		Wetness = FMath::FInterpTo(Wetness, FMath::Max(Falling, Now.Overcast * 0.25f),
			DeltaSeconds, 0.22f);
		if (Weathers)
		{
			UKismetMaterialLibrary::SetScalarParameterValue(this, Weathers, TEXT("Rain"), Falling);
			// HOW HARD IT IS BLOWING, from the weather the world already
			// reports. Nothing here invents a wind: a wet grey day is a windy
			// one and a still bright one is not, and both of those numbers
			// come off the same interval count every window reads.
			// A clear day is still a breezy one. The floor used to be 0.18,
			// which on a cloudless morning left the whole island dead still --
			// correct arithmetic and wrong weather. Nothing outdoors is ever
			// completely motionless.
			const float Blow = 0.34f + 0.66f * FMath::Max(Now.Overcast, Falling);
			UKismetMaterialLibrary::SetScalarParameterValue(this, Weathers, TEXT("Gale"), Blow);
			// WHERE THE BOOTS ARE. Every plant on the island reads this and the
			// ones within a metre or so of it lean out of the way. It is the
			// citizen's own tile centre, interpolated like everything else
			// drawn, and nothing is remembered from one frame to the next --
			// the grass springs back behind them because the only thing it
			// ever knew was where they are now.
			//
			// THE ALPHA IS HOW FAR INDOORS THEY ARE, and the timber walls read
			// it: under a roof the walls around the citizen come down to the
			// waist, because a dissolved roof over a two-metre-seventy storey
			// still hides whoever is standing in it. `Indoors` is the eased
			// version of the same shelter test the rain uses, so a doorway is
			// a walk and not a switch.
			UKismetMaterialLibrary::SetVectorParameterValue(this, Weathers, TEXT("Walker"),
				FLinearColor(Standing.X, Standing.Y, Standing.Z, Indoors));
			UKismetMaterialLibrary::SetScalarParameterValue(this, Weathers, TEXT("Day"), Day);
			UKismetMaterialLibrary::SetScalarParameterValue(this, Weathers, TEXT("Wet"), Wetness);
			UKismetMaterialLibrary::SetScalarParameterValue(this, Weathers, TEXT("Night"), 1.f - Day);

			// ---- AND WHAT TIME OF YEAR IT IS ----
			//
			// The year turns in twenty-eight days, off `dayIdx % 28` and
			// nothing else, so it is the same arithmetic as the hour: every
			// window over this world agrees without the engine having a word
			// for a season. These three have been arriving in the frame for as
			// long as the weather has and nothing had ever read them.
			//
			// Not smoothed. A season moves by about one part in three thousand
			// per interval, so the interpolation that the rain and the wetness
			// need would be measuring nothing. What it is at this instant is
			// what it is.
			UKismetMaterialLibrary::SetScalarParameterValue(this, Weathers, TEXT("Autumn"), Now.Autumn);
			UKismetMaterialLibrary::SetScalarParameterValue(this, Weathers, TEXT("Winter"), Now.Winter);
			UKismetMaterialLibrary::SetScalarParameterValue(this, Weathers, TEXT("Spring"), Now.Spring);
		}
	}

	// ---- THE GLOW-WORMS ----
	// Placed by hashing the world tile, so the same tuft glows in every
	// window; rebuilt only when the citizen crosses into a new tile, because
	// two thousand transforms a frame for something nobody is looking at
	// directly is a frame budget spent badly.
	if (Glimmer && Glimmer->GetStaticMesh() && bStanding)
	{
		const float Dark = 1.f - FMath::Clamp(Now.DayAmount, 0.f, 1.f);
		// A DUSK ANIMAL ARRIVES AT DUSK. At a twentieth they were out all
		// afternoon, reading as pale green discs painted on the ground.
		float After = 0.34f;
		if (const UIntervalLook* Wardrobe = UIntervalLook::Resolve(nullptr))
		{
			After = FMath::Clamp(Wardrobe->GlowAfter, 0.f, 1.f);
		}
		Glimmer->SetVisibility(Dark > After);
		if (GlowLit) { GlowLit->SetScalarParameterValue(TEXT("Night"), Dark); }

		const FIntPoint Here(FMath::FloorToInt(Standing.X / UIntervalGeometry::TileSize),
			FMath::FloorToInt(Standing.Y / UIntervalGeometry::TileSize));
		if (Here != Lit && Dark > After)
		{
			Lit = Here;
			const UIntervalLook* Look = UIntervalLook::Resolve(nullptr);
			Glimmer->ClearInstances();
			TArray<FTransform> Where;
			for (int32 DY = -GlowReach; DY <= GlowReach; ++DY)
			{
				for (int32 DX = -GlowReach; DX <= GlowReach; ++DX)
				{
					const int32 TX = Here.X + DX, TY = Here.Y + DY;
					const uint32 H = UIntervalGeometry::HashTile(TX, TY) ^ 0x9e3779b9u;
					if (static_cast<int32>(H % 100u) >= GlowPerHundred)
					{
						continue;
					}
					// Only where a level says they are found -- long grass and
					// hedgerow, not a flagged market square.
					if (Look && Look->GlowGround.Num() > 0 && Ground)
					{
						if (!Look->GlowGround.Contains(Ground->GroundWordAtTile(TX, TY)))
						{
							continue;
						}
					}
					const float OX = static_cast<float>((H >> 8) & 0xffu) / 255.f;
					const float OY = static_cast<float>((H >> 16) & 0xffu) / 255.f;
					const float OZ = static_cast<float>((H >> 24) & 0xffu) / 255.f;
					FVector At = UIntervalGeometry::TileToWorld(TX, TY);
					At.X += (OX - 0.5f) * UIntervalGeometry::TileSize;
					At.Y += (OY - 0.5f) * UIntervalGeometry::TileSize;
					At.Z += 14.f + OZ * 46.f;
					// Big enough that the COLOUR reads. At five centimetres
					// each one was three pixels and every one of them came out
					// white, whatever the material said; a glow-worm that is
					// not green is just a bright dot.
					Where.Add(FTransform(FRotator::ZeroRotator, At, FVector(0.10f)));
				}
			}
			for (int32 i = 0; i < Where.Num(); ++i)
			{
				const int32 At = Glimmer->AddInstance(Where[i], true);
				Glimmer->SetCustomDataValue(At, 0,
					static_cast<float>(i % 97) / 97.f, i == Where.Num() - 1);
			}
		}
	}

	// ---- THE STARS ----
	// Nothing here decides when night is: the material reads `Night` off the
	// one collection the hour writes to, and simply has nothing to show while
	// the sky is bright. The dome is kept up all the time rather than switched,
	// because switching it is a visible pop and leaving it costs one draw of a
	// sphere that is empty by day.
	if (Dome && Dome->GetStaticMesh())
	{
		const FVector Eye = bStanding ? Standing : GetActorLocation();
		Dome->SetWorldLocation(Eye);
		// The engine sphere is a metre across, so this is radius over fifty.
		const float Span = FMath::Max(1000.f, DomeRadius) / 50.f;
		Dome->SetWorldScale3D(FVector(Span));
		Dome->SetVisibility(Day < 0.995f);
	}

	// ---- THE RAINBOW ----
	//
	// The world has been reporting one all along and nothing drew it. Where it
	// goes in the sky is not decided here: the shader is given the direction of
	// the sun and works out the circle at forty-two degrees from the opposite
	// direction, which is what a rainbow is. So it sits correctly when the
	// camera turns, it is low when the sun is high, and it is not there at all
	// once the sun passes forty-two degrees -- all of which comes out of the
	// arithmetic rather than out of anybody's judgement.
	if (Arc && Arc->GetStaticMesh() && Bowed)
	{
		// IT ARRIVES SLOWLY AND LEAVES MORE SLOWLY. The world's number steps
		// once an interval; a bow that snapped into the sky would be a lamp.
		const float WantBow = FMath::Clamp(Now.Rainbow, 0.f, 1.f);
		BowShown = FMath::FInterpTo(BowShown, WantBow, DeltaSeconds,
			WantBow > BowShown ? 0.10f : 0.05f);

		const FVector Eye = bStanding ? Standing : GetActorLocation();
		Arc->SetWorldLocation(Eye);
		// A little inside the stars, which matters to nothing -- both are
		// additive and neither writes depth -- and costs nothing to be tidy
		// about.
		const float Span = FMath::Max(1000.f, DomeRadius) * 0.9f / 50.f;
		Arc->SetWorldScale3D(FVector(Span));

		// THE WHOLE GEOMETRY, IN ONE VECTOR. `Aim` is where the sunlight is
		// GOING; the direction of the sun itself is the other way about, and
		// getting that backwards puts the bow round the sun, which is a halo
		// and a different thing entirely.
		const FVector Toward = -Aim.Vector();
		Bowed->SetVectorParameterValue(TEXT("Sun"),
			FLinearColor(Toward.X, Toward.Y, Toward.Z, 1.f));
		const UIntervalLook* Wardrobe = UIntervalLook::Resolve(nullptr);
		const float Strength = Wardrobe ? Wardrobe->BowStrength : 0.85f;
		Bowed->SetScalarParameterValue(TEXT("Bow"), BowShown * Strength);
		// NOTHING TO DRAW IS NOTHING DRAWN. Unlike the stars, which are up all
		// night, a bow is there for a few minutes of a world's week -- so the
		// dome comes down rather than running a shader that returns black.
		Arc->SetVisibility(BowShown > 0.002f);
	}

	// ---- THE RAIN ----
	// A cylinder around the camera with streaks falling down it. Rain that is
	// drawn where the weather is rather than where the camera is costs a
	// hundred times as much and looks the same from inside it.
	if (Curtain)
	{
		const float Falling = RainNow(Now);
		const float Wet = Falling * (1.f - Indoors * 0.94f);
		const bool bWet = Wet > 0.02f;
		Curtain->SetVisibility(bWet);
		if (bWet)
		{
			// ---- AROUND THE EYE, AND HERE IS WHY IT CHANGED ----
			//
			// This was centred on the CITIZEN, for a good reason: while the
			// editor is simulating there is a controller that answers with the
			// world origin, so a camera-centred curtain rained in the sea a
			// kilometre away. That reason is still true, and it is handled by
			// the fallback below rather than by giving up on the camera.
			//
			// What centring on the citizen cannot fix is that this curtain is
			// a HOLLOW DRUM with the streaks on its inside wall, and there is
			// no rain anywhere between the middle and that wall. Centred on a
			// citizen at a radius wider than the camera is far, the player sits
			// in a dry hole with a ring of rain around the edge of the world:
			// reported from the window as rain that starts a long way off, that
			// the citizen never walks in, while the ground at their feet wets
			// anyway because the GROUND reads the weather number directly.
			//
			// The drum is small and rides with the lens instead. Then the wall
			// is a fixed distance from the eye whatever the camera is doing,
			// the citizen is always well inside it, and the rain is in front of
			// you rather than around the horizon. A real curtain of rain is the
			// nearest few metres of air; this is now that.
			FVector Eye = bStanding ? Standing : GetActorLocation();
			if (const UWorld* W = GetWorld())
			{
				if (const APlayerController* PC = W->GetFirstPlayerController())
				{
					if (PC->PlayerCameraManager)
					{
						const FVector Lens = PC->PlayerCameraManager->GetCameraLocation();
						// NOT THE ORIGIN. A simulating editor answers with it,
						// and a kilometre of sea is the symptom. Anything that
						// far from the citizen is not a camera watching them.
						if (!bStanding
							|| FVector::DistSquared(Lens, Standing) < 1.0e8)
						{
							Eye = Lens;
						}
					}
				}
			}
			Curtain->SetWorldLocation(Eye);
			const float Drum = RainSpan();
			Curtain->SetWorldScale3D(FVector(Drum / 50.f, Drum / 50.f, Drum / 50.f));
			if (Weather)
			{
				Weather->SetScalarParameterValue(TEXT("Rain"), Wet);
				Weather->SetScalarParameterValue(TEXT("Day"), Day);
				Weather->SetVectorParameterValue(TEXT("Foot"), FLinearColor(Eye));
				// The drum's own size, so the streaks can be sized in metres of
				// world instead of in fractions of a cylinder. Widen the drum
				// without telling the material and every streak widens with it.
				Weather->SetScalarParameterValue(TEXT("Radius"), RainSpan());
			}
		}
	}
}
