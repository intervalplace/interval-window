// Copyright interval.

#include "IntervalWings.h"

#include "IntervalBridgeSubsystem.h"
#include "IntervalGeometry.h"
#include "IntervalGround.h"
#include "IntervalLook.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"

DEFINE_LOG_CATEGORY_STATIC(LogIntervalWings, Log, All);

AIntervalWings::AIntervalWings()
{
	PrimaryActorTick.bCanEverTick = true;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));

	Flock = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Flock"));
	Flock->SetupAttachment(RootComponent);
	Flock->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Flock->SetMobility(EComponentMobility::Movable);
	// A BIRD CASTS A SHADOW, and it is worth more than the bird.
	//
	// From directly above, a bird twenty metres up is a few pixels of dark
	// against a field. Its shadow is the same few pixels running along the
	// ground beneath it, and it is the shadow that says how HIGH the thing is
	// -- without one, a bird over a meadow reads as a leaf blowing across it.
	Flock->SetCastShadow(true);
	Flock->bCastDynamicShadow = true;
	// Nothing needs to see a bird in a reflection or a ray trace.
	Flock->bVisibleInRayTracing = false;
	Flock->SetReceivesDecals(false);
	// THEY ARE NOT WHERE THE ACTOR IS. Each bird's transform is in world
	// space, written every frame, so the component's own bounds have to be
	// allowed to be large or the whole skein is culled the moment the actor's
	// origin is off screen.
	Flock->SetBoundsScale(8.f);
}

void AIntervalWings::BeginPlay()
{
	Super::BeginPlay();

	const UIntervalLook* Wardrobe = UIntervalLook::Resolve(Look);
	if (Wardrobe && Wardrobe->BirdMesh && Flock)
	{
		Flock->SetStaticMesh(Wardrobe->BirdMesh);
		if (Wardrobe->BirdMaterial)
		{
			Flock->SetMaterial(0, Wardrobe->BirdMaterial);
		}
	}
	else
	{
		UE_LOG(LogIntervalWings, Warning,
			TEXT("no bird in the wardrobe; the sky will stay empty"));
	}

	if (UGameInstance* GameInstance = GetGameInstance())
	{
		Bridge = GameInstance->GetSubsystem<UIntervalBridgeSubsystem>();
	}
	TActorIterator<AIntervalGround> Land(GetWorld());
	Ground = Land ? *Land : nullptr;
	// A LITTLE WHILE BEFORE THE FIRST ONE. A skein crossing the frame in the
	// second the window opens is a skein nobody believes.
	Quiet = 5.f + FMath::FRand() * 9.f;
}

void AIntervalWings::Gather()
{
	const UIntervalLook* Wardrobe = UIntervalLook::Resolve(Look);
	const int32 Count = Wardrobe ? FMath::Max(0, Wardrobe->FlockSize) : 11;
	if (Count == 0 || !Bridge || !Bridge->GetFrame().bHasMe)
	{
		// SAID ONCE, because this runs every frame while the sky is empty.
		// An empty sky that should not be empty is indistinguishable from an
		// empty sky that should be, which is the whole reason for this line.
		static bool bSaid = false;
		if (!bSaid)
		{
			bSaid = true;
			UE_LOG(LogIntervalWings, Warning,
				TEXT("no skein: flock of %d, bridge %s, citizen %s"), Count,
				Bridge ? TEXT("yes") : TEXT("NO"),
				(Bridge && Bridge->GetFrame().bHasMe) ? TEXT("yes") : TEXT("NO"));
		}
		return;
	}


	// ---- AND WHICH BIRD IT IS, WHICH IS A FACT ABOUT THE GROUND ----
	//
	// Chosen when a skein is launched rather than every frame: a flock does not
	// change species in the air, and a citizen who walks from the downs to the
	// shore mid-crossing should watch the crows finish their line and the next
	// skein come over as gulls.
	//
	// SETTING THE MESH CLEARS THE INSTANCES, which is why this is here and not
	// after the loop below that adds them. It is also why the swap is guarded:
	// re-setting the same mesh every skein would throw the component's buffers
	// away for nothing.
	if (Ground)
	{
		const FIntervalEntity& Who = Bridge->GetFrame().Me;
		const FName Word = Ground->GroundWordAtTile(Who.X, Who.Y);
		const FIntervalFowl* Kind = Wardrobe ? Wardrobe->SkyBirds.Find(Word) : nullptr;
		UStaticMesh* WantMesh = (Kind && Kind->Mesh) ? Kind->Mesh.Get()
			: (Wardrobe ? Wardrobe->BirdMesh.Get() : nullptr);
		UMaterialInterface* WantHue = (Kind && Kind->Hue) ? Kind->Hue.Get()
			: (Wardrobe ? Wardrobe->BirdMaterial.Get() : nullptr);
		if (Flock && WantMesh && Flock->GetStaticMesh() != WantMesh)
		{
			Flock->SetStaticMesh(WantMesh);
			if (WantHue) { Flock->SetMaterial(0, WantHue); }
		}
	}

	// ---- WHERE A SKEIN CROSSES ----
	//
	// Across the citizen and not at them: a flock aimed at the person is a
	// flock that appears to be about something, and these are about nothing,
	// which is the point. The line is laid to pass within a few tiles of where
	// they are standing so that it crosses the frame rather than the county.
	const FIntervalEntity& Me = Bridge->GetFrame().Me;
	const FVector Here = UIntervalGeometry::TileToWorld(Me.X, Me.Y);

	const float Bearing = FMath::FRandRange(0.f, 360.f);
	const float Rad = FMath::DegreesToRadians(Bearing);
	Toward = FVector(FMath::Cos(Rad), FMath::Sin(Rad), 0.f);
	const FVector Across(-Toward.Y, Toward.X, 0.f);

	// Far enough out that the birds are already at speed when they enter the
	// frame, and far enough past that they leave it rather than vanishing.
	Length = 6500.f;
	// Near enough to cross the frame rather than the county, and not so near
	// that every skein goes over the citizen's head like a scripted event.
	const float Miss = FMath::FRandRange(-1100.f, 1100.f);
	From = Here - Toward * (Length * 0.5f) + Across * Miss;
	Travelled = 0.f;

	// ---- AND THEY FLY LOW, WHICH IS NOT A PREFERENCE ----
	//
	// The first version put them eight to thirty metres up, where a bird
	// crossing a field is. Not one was ever seen, and the reason is worth
	// writing down because it governs everything anybody ever wants to put in
	// the air over this island.
	//
	// The camera sits about eight metres above the citizen and looks down
	// fifty degrees; its field is fifty-eight degrees tall, so the TOP of the
	// frame looks twenty-one degrees BELOW the horizon. For a bird to be in
	// frame at all, the line from the camera down to it must be steeper than
	// that -- which means the bird has to be below the camera by at least
	// 0.38 of its distance away. At ten metres out that is a ceiling of four
	// metres; at twenty it is half a metre. Anything higher is above the
	// horizon and off the top of the screen, however big the sky is.
	//
	// THE CAMERA HAS SINCE BEEN TILTED UP, which changes the answer. At
	// twenty-four degrees down the eye sits about seven metres above the
	// citizen and the top of the frame is five degrees ABOVE the horizon, so
	// anything higher than the eye is in frame once it is far enough away:
	// a bird at eight metres shows from eight metres out, and at twenty is
	// comfortably inside the picture. See `WatchPitch` in IntervalLook.h.
	//
	// So: five to twelve metres, which is where a crow crossing a field
	// actually is, and the low end still reads for a bird passing close.
	Height = FMath::FRandRange(500.f, 1200.f);
	Speed = FMath::FRandRange(800.f, 1400.f);

	// ---- THE SHAPE OF THE SKEIN ----
	//
	// Not a V, and not for want of trying: a V is what everybody draws and it
	// is what geese do, and what crosses an island at thirty metres is a loose
	// straggling line with a couple of birds out of it. So each bird gets a
	// station of its own and keeps it, with a slow wander on top.
	Birds.Reset(Count);
	float Trail = 0.f;
	for (int32 i = 0; i < Count; ++i)
	{
		FBird Bird;
		Trail += FMath::FRandRange(120.f, 320.f);
		Bird.Station.X = FMath::FRandRange(-340.f, 340.f);
		Bird.Station.Y = -Trail;
		Bird.Rise = FMath::FRandRange(-90.f, 110.f);
		Bird.Wander = FMath::FRandRange(0.f, 100.f);
		// NOT ALL THE SAME SIZE. One mesh at one scale eleven times over is a
		// row of stamps; a tenth either way is the difference between a flock
		// and a formation, and costs nothing because it is in the transform
		// that was being written anyway.
		Bird.Size = FMath::FRandRange(0.82f, 1.12f);
		Birds.Add(Bird);
	}

	if (Flock)
	{
		Flock->ClearInstances();
		for (int32 i = 0; i < Count; ++i)
		{
			Flock->AddInstance(FTransform::Identity, true);
		}
	}
	// SAID AFTER THE HEIGHT IS CHOSEN, and that is not fussiness. The first
	// version of this line sat at the top of the function and printed the
	// field's LAST value -- sixteen metres, the header's default -- so the log
	// said the birds were flying where they had just been moved away from.
	// A log that reports the thing it was written to check is worse than none.
	UE_LOG(LogIntervalWings, Log, TEXT("a skein of %d crosses, %.1f m up"),
		Count, Height / 100.f);
}

void AIntervalWings::Scatter()
{
	Birds.Reset();
	if (Flock)
	{
		Flock->ClearInstances();
	}
	const UIntervalLook* Wardrobe = UIntervalLook::Resolve(Look);
	const float Every = Wardrobe ? FMath::Max(2.f, Wardrobe->FlockEvery) : 42.f;
	// HALF TO TWICE, so the sky never keeps time. A skein every forty seconds
	// exactly is a metronome, and a metronome is the one thing the ear and the
	// eye both notice.
	Quiet = Every * FMath::FRandRange(0.5f, 2.0f);
}

void AIntervalWings::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (!Flock || !Flock->GetStaticMesh())
	{
		return;
	}

	// ---- BIRDS KEEP HOURS ----
	//
	// They roost at dusk, and a sky full of them at midnight is the same kind
	// of wrong as birdsong in a downpour: nobody has to be told, the eye simply
	// knows. Read off the one collection the hour writes to, like everything
	// else that wants to know what time it is.
	float Daylight = 1.f;
	if (UMaterialParameterCollection* Weathers = LoadObject<UMaterialParameterCollection>(
		nullptr, TEXT("/Game/Interval/MPC_IntervalSky.MPC_IntervalSky")))
	{
		Daylight = FMath::Clamp(UKismetMaterialLibrary::GetScalarParameterValue(
			this, Weathers, TEXT("Day")), 0.f, 1.f);
	}

	if (Birds.Num() == 0)
	{
		Quiet -= DeltaSeconds;
		// Nothing flies in the dark. The quiet keeps counting down, so the
		// first light has a skein in it rather than a wait.
		if (Quiet <= 0.f && Daylight > 0.35f)
		{
			Gather();
		}
		return;
	}

	Travelled += Speed * DeltaSeconds;
	if (Travelled > Length)
	{
		Scatter();
		return;
	}

	const FVector Across(-Toward.Y, Toward.X, 0.f);
	const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;

	for (int32 i = 0; i < Birds.Num(); ++i)
	{
		const FBird& Bird = Birds[i];
		// A SLOW WANDER, NOT A JITTER. A bird holding a dead straight line is
		// a bullet; one that shivers is an insect. This is a few metres of
		// drift over several seconds, which is what a bird correcting itself
		// in moving air actually does.
		const float Drift = FMath::Sin(Now * 0.37f + Bird.Wander) * 110.f;
		const float Lift = FMath::Sin(Now * 0.52f + Bird.Wander * 1.7f) * 70.f;

		FVector Where = From
			+ Toward * (Travelled + Bird.Station.Y)
			+ Across * (Bird.Station.X + Drift);
		Where.Z = Height + Bird.Rise + Lift;

		// ABOVE THE GROUND AND NOT ABOVE SEA LEVEL. The island rises two
		// hundred metres from the fens to the crags; a flock at a fixed world
		// height crosses a moor by going through it.
		if (Ground)
		{
			const int32 TileX = FMath::FloorToInt(Where.X / UIntervalGeometry::TileSize);
			const int32 TileY = FMath::FloorToInt(Where.Y / UIntervalGeometry::TileSize);
			Where.Z += Ground->GroundHeightAtTile(TileX, TileY);
		}

		// AND THEY FACE THE WAY THEY ARE GOING, banked a little into the
		// drift. The bank is what turns a line of meshes into a line of
		// animals: an aeroplane leans into its turn and so does a crow.
		const float Yaw = FMath::RadiansToDegrees(FMath::Atan2(Toward.Y, Toward.X));
		const float Bank = FMath::Cos(Now * 0.37f + Bird.Wander) * 9.f;
		const FRotator Facing(0.f, Yaw, Bank);

		Flock->UpdateInstanceTransform(i,
			FTransform(Facing, Where, FVector(Bird.Size)), true, false, true);
	}
	Flock->MarkRenderStateDirty();
}
