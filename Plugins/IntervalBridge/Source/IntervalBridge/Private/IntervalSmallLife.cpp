// Copyright interval.

#include "IntervalSmallLife.h"

#include "IntervalBridgeSubsystem.h"
#include "IntervalGeometry.h"
#include "IntervalGround.h"
#include "IntervalLook.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"

DEFINE_LOG_CATEGORY_STATIC(LogIntervalSmallLife, Log, All);

namespace
{
	/**
	 * WHICH GROUND HAS FROGS ON IT.
	 *
	 * The world's own words, and only the wet ones. `fens` is the obvious one;
	 * `peat` is the same country a little drier and a frog is certainly in it;
	 * `river` is a bank. A frog on `moor` or `crags` would be the same fault
	 * as one birdsong over every country, which is what the voices were fixed
	 * for this morning.
	 */
	bool bFrogGround(const FName Word)
	{
		return Word == TEXT("fens") || Word == TEXT("peat")
			|| Word == TEXT("river");
	}

	/**
	 * AND WHICH GROUND HAS BUTTERFLIES OVER IT.
	 *
	 * The open flowering country, in the world's own words. `meadow` and
	 * `heartlands` are the farmed middle of the island, which is what was
	 * asked for; `downs` is the open sheep country above it; `chalk` is downland
	 * proper and is the one ground in the real world most associated with them.
	 *
	 * NOT THE FENS, which have the frogs, and not `moor`, `crags`, `wilds`,
	 * `scree` or `mountain`: those are the hard country and putting a butterfly
	 * on them would be the same fault as one birdsong over every biome. Not the
	 * paved words either -- `cobble`, `flag`, `plaza`, `floor` -- because a
	 * butterfly over a market square is a window that has stopped paying
	 * attention. A `trail` runs through meadows, so a citizen walking the road
	 * sees them to either side of it, which is where they should be.
	 */
	bool bWingGround(const FName Word)
	{
		return Word == TEXT("meadow") || Word == TEXT("heartlands")
			|| Word == TEXT("downs") || Word == TEXT("chalk");
	}

	/**
	 * AND WHICH GROUND HAS BIRDS STANDING ON IT.
	 *
	 * Two countries, and which one decides which bird. The shore is where the
	 * gulls already call and where nothing has ever been visible; the paved
	 * ground of a town is where meadow songbirds were playing because that
	 * ground had no voice row of its own and fell through to the default.
	 *
	 * Returns the word the look is keyed on, or None where nothing stands.
	 */
	/** The two woods, which are the only ground anything falls out of. */
	bool bWoodGround(const FName Word)
	{
		return Word == TEXT("forest") || Word == TEXT("greenwood");
	}

	FName StandingFor(const FName Word)
	{
		if (Word == TEXT("sand") || Word == TEXT("shingle"))
		{
			return TEXT("shore");
		}
		if (Word == TEXT("floor") || Word == TEXT("flag")
			|| Word == TEXT("cobble") || Word == TEXT("plaza"))
		{
			return TEXT("town");
		}
		return NAME_None;
	}
}

AIntervalSmallLife::AIntervalSmallLife()
{
	PrimaryActorTick.bCanEverTick = true;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));

	Frogs = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Frogs"));
	Frogs->SetupAttachment(RootComponent);
	Frogs->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Frogs->SetMobility(EComponentMobility::Movable);
	// NO SHADOW. A bird's shadow is worth more than the bird because it says
	// how high it is; a frog is ON the ground and its shadow would be a smudge
	// under a thing four pixels across, for a shadow map's worth of work.
	Frogs->SetCastShadow(false);
	Frogs->bVisibleInRayTracing = false;
	Frogs->SetReceivesDecals(false);
	Frogs->SetBoundsScale(4.f);

	// TWO SPECIES, BECAUSE AN INSTANCED COMPONENT CARRIES ONE MATERIAL. A white
	// and a bright one over the same mesh, which is what is actually over a
	// field: the small white is the commonest butterfly on farmland in the
	// world this island is drawn from, and the bright one is the tortoiseshell
	// that makes you look up.
	Whites = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Whites"));
	Brights = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Brights"));
	Standing = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Standing"));
	LeavesGold = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("LeavesGold"));
	LeavesRust = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("LeavesRust"));
	for (UInstancedStaticMeshComponent* Comp : { Whites.Get(), Brights.Get(),
		Standing.Get(), LeavesGold.Get(), LeavesRust.Get() })
	{
		Comp->SetupAttachment(RootComponent);
		Comp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Comp->SetMobility(EComponentMobility::Movable);
		// NO SHADOW, for the frog's reason doubled: this is eight centimetres
		// of wing and it is in the air, so its shadow would be a moving smudge
		// the size of a leaf, for a shadow map's worth of work per butterfly.
		Comp->SetCastShadow(false);
		Comp->bVisibleInRayTracing = false;
		Comp->SetReceivesDecals(false);
		Comp->SetBoundsScale(4.f);
	}
	// EXCEPT THAT A STANDING BIRD CASTS ONE. The butterflies and the frogs do
	// not, because a shadow under a thing four pixels across is a smudge. A
	// gull is fifty-eight centimetres and it is ON the sand: its shadow is the
	// whole of how it reads as standing there rather than hovering a hand's
	// breadth above it, and it is the first thing that would look wrong.
	if (Standing) { Standing->SetCastShadow(true); }
}

void AIntervalSmallLife::BeginPlay()
{
	Super::BeginPlay();

	const UIntervalLook* Wardrobe = UIntervalLook::Resolve(Look);
	if (Wardrobe && Wardrobe->FrogMesh && Frogs)
	{
		Frogs->SetStaticMesh(Wardrobe->FrogMesh);
		if (Wardrobe->FrogMaterial)
		{
			Frogs->SetMaterial(0, Wardrobe->FrogMaterial);
		}
	}
	else
	{
		UE_LOG(LogIntervalSmallLife, Warning,
			TEXT("no frog in the wardrobe; the fens will stay empty"));
	}

	if (Wardrobe && Wardrobe->ButterflyMesh)
	{
		for (UInstancedStaticMeshComponent* Comp : { Whites.Get(), Brights.Get() })
		{
			if (!Comp) { continue; }
			Comp->SetStaticMesh(Wardrobe->ButterflyMesh);
		}
		if (Whites && Wardrobe->ButterflyPale)
		{
			Whites->SetMaterial(0, Wardrobe->ButterflyPale);
		}
		if (Brights && Wardrobe->ButterflyBright)
		{
			Brights->SetMaterial(0, Wardrobe->ButterflyBright);
		}
	}
	else
	{
		UE_LOG(LogIntervalSmallLife, Warning,
			TEXT("no butterfly in the wardrobe; the meadows will stay empty"));
	}

	if (Wardrobe && Wardrobe->LeafMesh)
	{
		for (UInstancedStaticMeshComponent* Comp : { LeavesGold.Get(), LeavesRust.Get() })
		{
			if (Comp) { Comp->SetStaticMesh(Wardrobe->LeafMesh); }
		}
		if (LeavesGold && Wardrobe->LeafGold) { LeavesGold->SetMaterial(0, Wardrobe->LeafGold); }
		if (LeavesRust && Wardrobe->LeafRust) { LeavesRust->SetMaterial(0, Wardrobe->LeafRust); }
	}

	if (UGameInstance* GameInstance = GetGameInstance())
	{
		Bridge = GameInstance->GetSubsystem<UIntervalBridgeSubsystem>();
	}
	TActorIterator<AIntervalGround> Land(GetWorld());
	Ground = Land ? *Land : nullptr;
}

void AIntervalSmallLife::Gather(int32 TileX, int32 TileY)
{
	Hoppers.Reset();
	if (Frogs) { Frogs->ClearInstances(); }

	const UIntervalLook* Wardrobe = UIntervalLook::Resolve(Look);
	const int32 Most = Wardrobe ? FMath::Max(0, Wardrobe->FrogCount) : 7;
	if (Most == 0 || !Ground)
	{
		UE_LOG(LogIntervalSmallLife, Warning,
			TEXT("no frogs wanted here: count %d, ground %s"),
			Most, Ground ? TEXT("yes") : TEXT("NO"));
		return;
	}

	// ---- WHEREVER THE GROUND IS WET, WITHIN SIGHT ----
	//
	// Every tile in a small square is asked what it is, and a frog is put on
	// the ones that answer wet. That is a hundred and twenty-odd questions,
	// once, when a citizen crosses into a new tile -- not per frame -- and the
	// ground answers them out of a chunk it has already built.
	//
	// SCATTERED WITHIN THE TILE, not centred on it. Two metres of tile with
	// one frog exactly in the middle of it is a grid, and a grid of frogs is
	// the least frog-like thing there is.
	const int32 Reach = 6;
	TArray<FIntPoint> Wet;
	for (int32 dy = -Reach; dy <= Reach; ++dy)
	{
		for (int32 dx = -Reach; dx <= Reach; ++dx)
		{
			const FIntPoint At(TileX + dx, TileY + dy);
			if (bFrogGround(Ground->GroundWordAtTile(At.X, At.Y)))
			{
				Wet.Add(At);
			}
		}
	}
	if (Wet.Num() == 0)
	{
		// ---- AND THIS TILE IS NOT SETTLED, IT IS UNANSWERED ----
		//
		// `Around` used to be written at the top of this function, before the
		// ground had been asked anything. That is a trap and it is the same
		// one `AIntervalGround::Want` documents about chunks: a citizen who
		// stands still while the ground under them is still streaming gets ONE
		// gather, it finds nothing because no chunk has been built yet, and
		// the tile is then marked as done for ever. Standing on a riverbank
		// with fifty-one wet tiles round them, the answer was nought frogs and
		// nothing in any log, because the retry could only happen by walking
		// somewhere else and coming back.
		//
		// So `Around` is committed only when the ground actually answered.
		// A gather that found nothing leaves it alone and the next one, three
		// quarters of a second later, asks again.
		return;
	}
	Around = FIntPoint(TileX, TileY);
	UE_LOG(LogIntervalSmallLife, Log,
		TEXT("%d wet tiles within %d of %d,%d; putting %d frogs on them"),
		Wet.Num(), Reach, TileX, TileY, FMath::Min(Most, Wet.Num()));

	const int32 Want = FMath::Min(Most, Wet.Num());
	for (int32 i = 0; i < Want; ++i)
	{
		const FIntPoint At = Wet[FMath::RandRange(0, Wet.Num() - 1)];
		FFrog Frog;
		FVector Where = UIntervalGeometry::TileToWorld(At.X, At.Y);
		Where.X += FMath::FRandRange(-90.f, 90.f);
		Where.Y += FMath::FRandRange(-90.f, 90.f);
		Where.Z = Ground->GroundHeightAtTile(At.X, At.Y);
		Frog.From = Where;
		Frog.To = Where;
		Frog.Through = -1.f;
		// A LONG FIRST WAIT, staggered, or seven frogs all hop together the
		// moment a citizen arrives and the fen reads as a mechanism.
		Frog.Rests = FMath::FRandRange(0.5f, 9.f);
		Frog.Yaw = FMath::FRandRange(0.f, 360.f);
		Frog.Size = FMath::FRandRange(0.82f, 1.25f);
		Hoppers.Add(Frog);
		if (Frogs) { Frogs->AddInstance(FTransform::Identity, true); }
	}
}

bool AIntervalSmallLife::bFlyingWeather() const
{
	if (!Bridge) { return false; }
	const FIntervalSky& Sky = Bridge->GetFrame().Sky;
	// NOT AT NIGHT. Butterflies are day-flying and moths are the other thing;
	// a meadow full of them at midnight is the window saying it does not know
	// what time it is. `DayAmount` saturates, so this is "properly light".
	if (Sky.DayAmount < 0.45f) { return false; }
	// NOT IN RAIN. They shelter under leaves and the world draws rain, so a
	// butterfly riding through a downpour is a thing you would notice.
	if (Sky.Rain > 0.30f) { return false; }
	// AND NOT IN WINTER, which the world already knows about and nothing else
	// in this window had asked. It is the cheapest seasonal detail available:
	// the meadows simply empty, and fill again in spring.
	if (Sky.Winter > 0.55f) { return false; }
	return true;
}

void AIntervalSmallLife::GatherWings(int32 TileX, int32 TileY)
{
	Flutters.Reset();
	if (Whites) { Whites->ClearInstances(); }
	if (Brights) { Brights->ClearInstances(); }

	const UIntervalLook* Wardrobe = UIntervalLook::Resolve(Look);
	const int32 Most = Wardrobe ? FMath::Max(0, Wardrobe->ButterflyCount) : 14;
	if (Most == 0 || !Ground || !bFlyingWeather())
	{
		return;
	}

	// The same sweep the frogs do, over the open ground instead of the wet.
	const int32 Reach = 6;
	TArray<FIntPoint> Open;
	for (int32 dy = -Reach; dy <= Reach; ++dy)
	{
		for (int32 dx = -Reach; dx <= Reach; ++dx)
		{
			const FIntPoint At(TileX + dx, TileY + dy);
			if (bWingGround(Ground->GroundWordAtTile(At.X, At.Y)))
			{
				Open.Add(At);
			}
		}
	}
	if (Open.Num() == 0)
	{
		// Committed only when the ground answered, for the reason the frogs'
		// `Around` documents at length: a tile marked done against a ground
		// that had not streamed in yet can never be retried.
		return;
	}
	Afield = FIntPoint(TileX, TileY);

	const int32 Want = FMath::Min(Most, Open.Num());
	for (int32 i = 0; i < Want; ++i)
	{
		const FIntPoint At = Open[FMath::RandRange(0, Open.Num() - 1)];
		FFlutter Moth;
		FVector Where = UIntervalGeometry::TileToWorld(At.X, At.Y);
		Where.X += FMath::FRandRange(-90.f, 90.f);
		Where.Y += FMath::FRandRange(-90.f, 90.f);
		Moth.Ground = Ground->GroundHeightAtTile(At.X, At.Y);
		Moth.At = FVector(Where.X, Where.Y, Moth.Ground);
		Moth.Yaw = FMath::FRandRange(0.f, 360.f);
		// SLOW, AND SLOWER THAN IT LOOKS. A butterfly covers very little
		// ground; what reads as speed is the lurching, so the drift is held
		// down and the bob is given the range instead.
		Moth.Speed = FMath::FRandRange(22.f, 52.f);
		// KNEE HEIGHT, which is the whole request: high enough to be over the
		// grass and low enough to be in frame beside a citizen rather than
		// somewhere above them like the crows.
		Moth.Height = FMath::FRandRange(25.f, 105.f);
		Moth.Bob = FMath::FRandRange(0.f, 6.28f);
		Moth.BobRate = FMath::FRandRange(2.6f, 5.2f);
		Moth.BobDeep = FMath::FRandRange(10.f, 26.f);
		Moth.Roll = FMath::FRandRange(0.f, 6.28f);
		// ABOUT THREE AND A HALF BEATS A SECOND, which is roughly a real one
		// and is slow enough to be seen as a flap rather than as a flicker.
		Moth.RollRate = FMath::FRandRange(18.f, 26.f);
		Moth.Until = FMath::FRandRange(0.4f, 2.2f);
		// MEASURED, THEN NUDGED, AND SAYING SO. The mesh is 8.7 cm across,
		// which is a large white at the honest top of the range. At the watch
		// camera's 1150 out and 1380 up that is 4.6 pixels on a 1920 screen,
		// against the frog's 6.9 -- and the frog sits still, where this is the
		// thing that was asked for BECAUSE it should be visible. So the spread
		// brackets the frog instead of sitting under it: 8.3 to 12.2 cm, which
		// is 4.4 to 6.5 pixels, and a real swallowtail is 10. Nothing here is
		// bigger than an insect that exists.
		Moth.Size = FMath::FRandRange(0.95f, 1.40f);
		// A THIRD BRIGHT. Mostly whites, because that is what a field is, and
		// the bright ones are worth more for being fewer.
		Moth.bBright = FMath::FRand() < 0.34f ? 1 : 0;
		UInstancedStaticMeshComponent* Comp = Moth.bBright ? Brights : Whites;
		Moth.Slot = Comp ? Comp->GetInstanceCount() : 0;
		Flutters.Add(Moth);
		if (Comp) { Comp->AddInstance(FTransform::Identity, true); }
	}
	UE_LOG(LogIntervalSmallLife, Log,
		TEXT("%d open tiles within %d of %d,%d; %d butterflies over them"),
		Open.Num(), Reach, TileX, TileY, Want);
}

void AIntervalSmallLife::GatherLeaves(int32 TileX, int32 TileY)
{
	Leaves.Reset();
	if (LeavesGold) { LeavesGold->ClearInstances(); }
	if (LeavesRust) { LeavesRust->ClearInstances(); }
	LeavesWanted = 0;

	const UIntervalLook* Wardrobe = UIntervalLook::Resolve(Look);
	if (!Wardrobe || !Ground || !Bridge || !Wardrobe->LeafMesh) { return; }

	// HOW MUCH AUTUMN THERE IS, which decides how many rather than whether.
	// `autumn` is a petal: it climbs to one in the middle of the season and
	// falls away either side, so a wood turns, drifts, and goes bare, and the
	// window never has to be told which week it is.
	const float Season = Bridge->GetFrame().Sky.Autumn;
	if (Season < 0.12f) { return; }

	const int32 Most = FMath::Max(0, Wardrobe->LeafCount);
	const int32 Want = FMath::RoundToInt(Most * Season);
	if (Want <= 0) { return; }

	const int32 Reach = 5;
	TArray<FIntPoint> Wood;
	for (int32 dy = -Reach; dy <= Reach; ++dy)
	{
		for (int32 dx = -Reach; dx <= Reach; ++dx)
		{
			const FIntPoint At(TileX + dx, TileY + dy);
			if (bWoodGround(Ground->GroundWordAtTile(At.X, At.Y)))
			{
				Wood.Add(At);
			}
		}
	}
	if (Wood.Num() == 0) { return; }
	Awood = FIntPoint(TileX, TileY);
	LeavesWanted = Want;

	for (int32 i = 0; i < Want; ++i)
	{
		const FIntPoint At = Wood[FMath::RandRange(0, Wood.Num() - 1)];
		FLeaf Leaf;
		FVector Where = UIntervalGeometry::TileToWorld(At.X, At.Y);
		Where.X += FMath::FRandRange(-95.f, 95.f);
		Where.Y += FMath::FRandRange(-95.f, 95.f);
		Leaf.Ground = Ground->GroundHeightAtTile(At.X, At.Y);
		// STARTED PART-WAY DOWN, every one of them at a different height. All
		// twenty released from the canopy at once is a bucket being emptied,
		// and it happens again every time a citizen walks into a new tile.
		Leaf.At = FVector(Where.X, Where.Y,
			Leaf.Ground + FMath::FRandRange(40.f, 780.f));
		Leaf.Fall = FMath::FRandRange(34.f, 68.f);
		Leaf.Swing = FMath::FRandRange(0.f, 6.28f);
		Leaf.SwingRate = FMath::FRandRange(1.4f, 3.0f);
		Leaf.SwingWide = FMath::FRandRange(16.f, 42.f);
		Leaf.Drift = FMath::FRandRange(0.f, 360.f);
		Leaf.Spin = FMath::FRandRange(0.f, 360.f);
		Leaf.SpinRate = FMath::FRandRange(-90.f, 90.f);
		Leaf.Size = FMath::FRandRange(0.85f, 1.25f);
		Leaf.Rest = FMath::FRandRange(6.f, 20.f);
		Leaf.bRust = FMath::FRand() < 0.42f ? 1 : 0;
		UInstancedStaticMeshComponent* Comp = Leaf.bRust ? LeavesRust : LeavesGold;
		Leaf.Slot = Comp ? Comp->GetInstanceCount() : 0;
		Leaves.Add(Leaf);
		if (Comp) { Comp->AddInstance(FTransform::Identity, true); }
	}
	UE_LOG(LogIntervalSmallLife, Log,
		TEXT("%d wooded tiles within %d of %d,%d; %d leaves down (autumn %.2f)"),
		Wood.Num(), Reach, TileX, TileY, Want, Season);
}

void AIntervalSmallLife::Fall(FLeaf& Who, float DeltaSeconds)
{
	if (Who.Lying >= 0.f)
	{
		// ---- LYING WHERE IT LANDED ----
		//
		// And then carried back up rather than destroyed. The instance count
		// never changes, so a wood that a citizen stands in for an hour
		// allocates nothing after the first gather, and the drift underfoot is
		// always being renewed from above the way a real one is.
		Who.Lying += DeltaSeconds;
		if (Who.Lying > Who.Rest)
		{
			Who.Lying = -1.f;
			Who.At.Z = Who.Ground + FMath::FRandRange(620.f, 820.f);
			Who.At.X += FMath::FRandRange(-140.f, 140.f);
			Who.At.Y += FMath::FRandRange(-140.f, 140.f);
			Who.Rest = FMath::FRandRange(6.f, 20.f);
			Who.SpinRate = FMath::FRandRange(-90.f, 90.f);
			if (Ground)
			{
				const int32 Tx = FMath::FloorToInt(Who.At.X / UIntervalGeometry::TileSize);
				const int32 Ty = FMath::FloorToInt(Who.At.Y / UIntervalGeometry::TileSize);
				Who.Ground = Ground->GroundHeightAtTile(Tx, Ty);
			}
		}
		return;
	}

	Who.At.Z -= Who.Fall * DeltaSeconds;
	Who.Swing += DeltaSeconds * Who.SwingRate;
	Who.Spin += DeltaSeconds * Who.SpinRate;
	if (Who.At.Z <= Who.Ground + 1.f)
	{
		Who.At.Z = Who.Ground + 1.f;
		Who.Lying = 0.f;
	}
}

void AIntervalSmallLife::GatherStanders(int32 TileX, int32 TileY)
{
	Standers.Reset();
	if (Standing) { Standing->ClearInstances(); }
	StandingKind = NAME_None;

	const UIntervalLook* Wardrobe = UIntervalLook::Resolve(Look);
	if (!Wardrobe || !Ground) { return; }

	// WHICH COUNTRY, FROM THE TILE THE CITIZEN IS ON. The sweep below then
	// only accepts ground of that same kind, so a citizen standing on the
	// quay where a town meets the shore gets one or the other rather than
	// gulls and doves mixed on the same twenty tiles.
	const FName Kind = StandingFor(Ground->GroundWordAtTile(TileX, TileY));
	if (Kind.IsNone()) { return; }
	const FIntervalFowl* Fowl = Wardrobe->SkyBirds.Find(
		Kind == TEXT("shore") ? FName(TEXT("sand")) : FName(TEXT("cobble")));
	if (!Fowl || !Fowl->Mesh) { return; }

	const int32 Reach = 7;
	TArray<FIntPoint> Spots;
	for (int32 dy = -Reach; dy <= Reach; ++dy)
	{
		for (int32 dx = -Reach; dx <= Reach; ++dx)
		{
			const FIntPoint At(TileX + dx, TileY + dy);
			if (StandingFor(Ground->GroundWordAtTile(At.X, At.Y)) == Kind)
			{
				Spots.Add(At);
			}
		}
	}
	if (Spots.Num() == 0) { return; }

	Ashore = FIntPoint(TileX, TileY);
	StandingKind = Kind;
	if (Standing && Standing->GetStaticMesh() != Fowl->Mesh)
	{
		Standing->SetStaticMesh(Fowl->Mesh);
		if (Fowl->Hue) { Standing->SetMaterial(0, Fowl->Hue); }
	}

	const int32 Most = FMath::Max(0, Wardrobe->StandingCount);
	const int32 Want = FMath::Min(Most, Spots.Num());
	for (int32 i = 0; i < Want; ++i)
	{
		const FIntPoint At = Spots[FMath::RandRange(0, Spots.Num() - 1)];
		FStander Bird;
		FVector Where = UIntervalGeometry::TileToWorld(At.X, At.Y);
		Where.X += FMath::FRandRange(-80.f, 80.f);
		Where.Y += FMath::FRandRange(-80.f, 80.f);
		Where.Z = Ground->GroundHeightAtTile(At.X, At.Y);
		Bird.From = Where;
		Bird.To = Where;
		Bird.Flew = -1.f;
		Bird.Yaw = FMath::FRandRange(0.f, 360.f);
		Bird.Size = FMath::FRandRange(0.88f, 1.14f);
		// STAGGERED, or twenty gulls turn their heads in unison and the shore
		// reads as a mechanism. The same note the frogs' first wait carries.
		Bird.Fidget = FMath::FRandRange(0.5f, 7.f);
		Standers.Add(Bird);
		if (Standing) { Standing->AddInstance(FTransform::Identity, true); }
	}
	UE_LOG(LogIntervalSmallLife, Log,
		TEXT("%d tiles of %s within %d of %d,%d; %d birds standing"),
		Spots.Num(), *Kind.ToString(), Reach, TileX, TileY, Want);
}

void AIntervalSmallLife::Startle(FStander& Who, const FVector& Citizen, float DeltaSeconds)
{
	if (Who.Flew < 0.f)
	{
		// ---- GOING UP BECAUSE SOMEBODY WALKED INTO THEM ----
		//
		// Four metres, which is two tiles. Nearer than that and a citizen is
		// standing among them before anything happens, which reads as birds
		// that have not noticed; much further and they leave before you have
		// seen them, which is worse than their not being there.
		const float Near = FVector::Dist2D(Who.From, Citizen);
		if (Near < 400.f)
		{
			// AWAY FROM THE CITIZEN, not in a random direction. A bird that
			// goes up and flies TOWARD the thing that startled it is the
			// clearest possible tell that nothing here is really reacting.
			FVector Off = Who.From - Citizen;
			Off.Z = 0.f;
			if (Off.IsNearlyZero()) { Off = FVector(1.f, 0.f, 0.f); }
			Off.Normalize();
			// and a little sideways, so twenty birds do not leave along twenty
			// lines that all meet at the citizen
			const float Skew = FMath::DegreesToRadians(FMath::FRandRange(-40.f, 40.f));
			const FVector Fan(Off.X * FMath::Cos(Skew) - Off.Y * FMath::Sin(Skew),
				Off.X * FMath::Sin(Skew) + Off.Y * FMath::Cos(Skew), 0.f);
			Who.To = Who.From + Fan * FMath::FRandRange(900.f, 2200.f);
			if (Ground)
			{
				const int32 Tx = FMath::FloorToInt(Who.To.X / UIntervalGeometry::TileSize);
				const int32 Ty = FMath::FloorToInt(Who.To.Y / UIntervalGeometry::TileSize);
				Who.To.Z = Ground->GroundHeightAtTile(Tx, Ty);
			}
			Who.Yaw = FMath::RadiansToDegrees(FMath::Atan2(Fan.Y, Fan.X));
			Who.Flew = 0.f;
			return;
		}

		// ---- OR JUST STANDING THERE ----
		//
		// Which is nearly all of it. A gull on a beach turns on the spot every
		// few seconds and does nothing else, and that small turn is what keeps
		// a row of them from reading as decals.
		Who.Fidget -= DeltaSeconds;
		if (Who.Fidget <= 0.f)
		{
			Who.Yaw = FMath::Fmod(Who.Yaw + FMath::FRandRange(-70.f, 70.f) + 360.f, 360.f);
			Who.Fidget = FMath::FRandRange(2.f, 8.f);
		}
		return;
	}

	// About two seconds in the air over that distance, which is a bird leaving
	// rather than a bird teleporting.
	Who.Flew += DeltaSeconds * 0.55f;
	if (Who.Flew >= 1.f)
	{
		Who.Flew = -1.f;
		Who.From = Who.To;
		Who.Fidget = FMath::FRandRange(1.5f, 6.f);
	}
}

void AIntervalSmallLife::Flutter(FFlutter& Who, float DeltaSeconds)
{
	// ---- SITTING, WHICH IS THE RARE THING ----
	//
	// The frog above is still nine times out of ten and this is the reverse:
	// it settles now and then, briefly, and that is what makes the drifting
	// read as flight rather than as a thing on a wire. Wings go still, which
	// is the one moment the shape can actually be seen.
	if (Who.Settled > 0.f)
	{
		Who.Settled -= DeltaSeconds;
		return;
	}

	Who.Until -= DeltaSeconds;
	if (Who.Until <= 0.f)
	{
		// A NEW MIND, OFTEN. The heading turns by up to sixty degrees every
		// second or two, which is what makes the path lurch. A butterfly that
		// held a heading would be a bee.
		Who.Yaw = FMath::Fmod(Who.Yaw + FMath::FRandRange(-60.f, 60.f) + 360.f, 360.f);
		Who.Until = FMath::FRandRange(0.4f, 2.2f);
		Who.Height = FMath::Clamp(Who.Height + FMath::FRandRange(-22.f, 22.f), 18.f, 120.f);
		if (FMath::FRand() < 0.07f)
		{
			Who.Settled = FMath::FRandRange(1.2f, 4.5f);
			return;
		}
	}

	const float Rad = FMath::DegreesToRadians(Who.Yaw);
	Who.At.X += FMath::Cos(Rad) * Who.Speed * DeltaSeconds;
	Who.At.Y += FMath::Sin(Rad) * Who.Speed * DeltaSeconds;
	// IT FOLLOWS THE LAND. The meadows roll, and "nearly flat" is what puts a
	// butterfly inside a bank -- the same note the frog's landing carries.
	if (Ground)
	{
		const int32 Tx = FMath::FloorToInt(Who.At.X / UIntervalGeometry::TileSize);
		const int32 Ty = FMath::FloorToInt(Who.At.Y / UIntervalGeometry::TileSize);
		Who.Ground = FMath::FInterpTo(Who.Ground,
			Ground->GroundHeightAtTile(Tx, Ty), DeltaSeconds, 3.f);
	}
	Who.Bob += DeltaSeconds * Who.BobRate;
	Who.Roll += DeltaSeconds * Who.RollRate;
}

void AIntervalSmallLife::Leap(FFrog& Who, float DeltaSeconds)
{
	if (Who.Through < 0.f)
	{
		Who.Rests -= DeltaSeconds;
		if (Who.Rests > 0.f)
		{
			return;
		}
		// ---- AND OFF IT GOES ----
		//
		// A short hop and a new heading, both small: a frog crossing a fen in
		// straight metre-long bounds is a rabbit. Twenty to fifty centimetres
		// and a turn of up to a right angle is an animal that has not decided
		// where it is going, which is the truth about a frog.
		const float Turn = FMath::FRandRange(-90.f, 90.f);
		Who.Yaw = FMath::Fmod(Who.Yaw + Turn + 360.f, 360.f);
		const float Rad = FMath::DegreesToRadians(Who.Yaw);
		const float Far = FMath::FRandRange(20.f, 50.f);
		Who.From = Who.To;
		Who.To = Who.From + FVector(FMath::Cos(Rad) * Far,
			FMath::Sin(Rad) * Far, 0.f);
		// IT LANDS ON THE GROUND AND NOT AT THE HEIGHT IT LEFT. The fens are
		// nearly flat, and "nearly" is what puts a frog inside a bank.
		if (Ground)
		{
			const int32 Tx = FMath::FloorToInt(Who.To.X / UIntervalGeometry::TileSize);
			const int32 Ty = FMath::FloorToInt(Who.To.Y / UIntervalGeometry::TileSize);
			Who.To.Z = Ground->GroundHeightAtTile(Tx, Ty);
		}
		Who.Through = 0.f;
		return;
	}

	// About a third of a second in the air, which is what a hop of this length
	// takes and is short enough that the eye reads it as one movement.
	Who.Through += DeltaSeconds * 3.1f;
	if (Who.Through >= 1.f)
	{
		Who.Through = -1.f;
		Who.From = Who.To;
		// SITTING IS MOST OF BEING A FROG. Two to eleven seconds, which is
		// long enough that a fen is mostly still and a hop is an event.
		Who.Rests = FMath::FRandRange(2.f, 11.f);
	}
}

void AIntervalSmallLife::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// SAID ONCE, AND SAYING WHICH. An empty fen that should not be empty is
	// indistinguishable from an empty fen that should be, and this actor has
	// four ways to be silently idle. Naming which one is the whole diagnosis;
	// without it the answer is a rebuild and a guess.
	// THE FROG'S MESH IS NOT A CONDITION OF THE BUTTERFLIES. This guard used to
	// name `Frogs` because frogs were all there was, and leaving it that way
	// would have made a missing frog empty the meadows as well as the fens --
	// two unrelated things failing together for no reason anybody could see.
	// What is shared is the bridge, the ground and a citizen to stand near;
	// each creature's own mesh is checked where that creature is gathered.
	if (!Bridge || !Ground || !Bridge->GetFrame().bHasMe)
	{
		// THROTTLED, NOT ONCE. The first version said this a single time and
		// that time was the first tick, before any frame had arrived -- so it
		// reported "citizen NO", which was true then and told nothing about
		// the steady state a minute later. A diagnostic that can only describe
		// the moment before the thing it is diagnosing is worse than none.
		Quiet -= DeltaSeconds;
		if (Quiet <= 0.f)
		{
			Quiet = 10.f;
			UE_LOG(LogIntervalSmallLife, Warning,
				TEXT("nothing small is alive: frog mesh %s, butterfly mesh %s, ")
				TEXT("bridge %s, ground %s, citizen %s"),
				(Frogs && Frogs->GetStaticMesh()) ? TEXT("yes") : TEXT("NO"),
				(Whites && Whites->GetStaticMesh()) ? TEXT("yes") : TEXT("NO"),
				Bridge ? TEXT("yes") : TEXT("NO"),
				Ground ? TEXT("yes") : TEXT("NO"),
				(Bridge && Bridge->GetFrame().bHasMe) ? TEXT("yes") : TEXT("NO"));
		}
		return;
	}
	const FIntervalFrame& Frame = Bridge->GetFrame();

	// ASKED WHEN A CITIZEN MOVES, not every frame. The ground's word for a
	// hundred and twenty tiles is cheap once and silly sixty times a second.
	Asked += DeltaSeconds;
	const FIntPoint Here(Frame.Me.X, Frame.Me.Y);
	if (Frogs && Frogs->GetStaticMesh() && Here != Around && Asked > 0.75f)
	{
		Asked = 0.f;
		Gather(Here.X, Here.Y);
	}

	// ---- AND THE BUTTERFLIES, OVER THE OPEN GROUND ----
	//
	// Gathered on their own tile and their own clock. Sharing the frogs' meant
	// that a citizen on a riverbank with a meadow behind them got one or the
	// other depending on which sweep had answered first.
	//
	// THE WEATHER IS ASKED EVERY FRAME AND IT IS ONE COMPARISON. Night falls
	// and rain arrives while a citizen stands still, so a gate that was only
	// read at gather time would leave a field of butterflies out in the dark
	// until somebody walked far enough to trigger a rebuild.
	if (!bFlyingWeather())
	{
		if (Flutters.Num() > 0)
		{
			Flutters.Reset();
			if (Whites) { Whites->ClearInstances(); }
			if (Brights) { Brights->ClearInstances(); }
			Afield = FIntPoint(-9999, -9999);
		}
	}
	else
	{
		AskedWings += DeltaSeconds;
		if (Here != Afield && AskedWings > 0.75f)
		{
			AskedWings = 0.f;
			GatherWings(Here.X, Here.Y);
		}
	}

	for (FFlutter& Who : Flutters)
	{
		Flutter(Who, DeltaSeconds);

		FVector Where = Who.At;
		float Roll = 0.f;
		float Pitch = 0.f;
		if (Who.Settled > 0.f)
		{
			// ON THE GROUND, WINGS OPEN AND STILL. Not closed: a butterfly at
			// rest in sunshine holds them flat, and flat is the one pose where
			// the shape this mesh spent its vertices on can be read at all.
			Where.Z = Who.Ground + 1.5f;
		}
		else
		{
			Where.Z = Who.Ground + Who.Height
				+ FMath::Sin(Who.Bob) * Who.BobDeep;
			// THE ROLL IS THE WINGBEAT, and it is the whole reason the mesh has
			// flat wings. Seen from above, a body rolling fifty-odd degrees
			// either way takes its wings from full face to nearly an edge and
			// back, which is a beat. Nothing here is animated and nothing is
			// skinned: it is the transform that was being written anyway.
			Roll = FMath::Sin(Who.Roll) * 52.f;
			// and it noses up as it rises and down as it falls, which costs one
			// cosine and is what stops it reading as a disc on a string
			Pitch = FMath::Cos(Who.Bob) * 14.f;
		}

		UInstancedStaticMeshComponent* Comp = Who.bBright ? Brights : Whites;
		if (Comp && Comp->IsValidInstance(Who.Slot))
		{
			Comp->UpdateInstanceTransform(Who.Slot,
				FTransform(FRotator(Pitch, Who.Yaw, Roll), Where, FVector(Who.Size)),
				true, false, true);
		}
	}
	if (Flutters.Num() > 0)
	{
		if (Whites) { Whites->MarkRenderStateDirty(); }
		if (Brights) { Brights->MarkRenderStateDirty(); }
	}

	// ---- AND THE LEAVES, WHICH ONLY EXIST FOR PART OF THE YEAR ----
	//
	// Re-gathered when the citizen moves OR when the season has carried the
	// wanted count somewhere else, so a wood fills as autumn comes on and
	// thins as it goes without anybody walking anywhere.
	AskedLeaves += DeltaSeconds;
	if (AskedLeaves > 0.75f)
	{
		const float Season = Frame.Sky.Autumn;
		const UIntervalLook* Wardrobe = UIntervalLook::Resolve(Look);
		const int32 Should = (Wardrobe && Season >= 0.12f)
			? FMath::RoundToInt(FMath::Max(0, Wardrobe->LeafCount) * Season) : 0;
		if (Here != Awood || FMath::Abs(Should - LeavesWanted) > 2)
		{
			AskedLeaves = 0.f;
			if (Should == 0)
			{
				Leaves.Reset();
				if (LeavesGold) { LeavesGold->ClearInstances(); }
				if (LeavesRust) { LeavesRust->ClearInstances(); }
				LeavesWanted = 0;
				Awood = FIntPoint(-9999, -9999);
			}
			else
			{
				GatherLeaves(Here.X, Here.Y);
			}
		}
	}
	for (FLeaf& Leaf : Leaves)
	{
		Fall(Leaf, DeltaSeconds);

		FVector Where = Leaf.At;
		FRotator Turn(0.f, Leaf.Spin, 0.f);
		if (Leaf.Lying < 0.f)
		{
			// ---- THE SWING IS THE WHOLE OF IT ----
			//
			// A falling leaf is not a dropped stone. It is a plate, so it
			// stalls, tips, slides off to one side, and does the same the
			// other way: the path is a flat zigzag rather than a line, and
			// without it twenty leaves descending in parallel are rain.
			const float Rad = FMath::DegreesToRadians(Leaf.Drift);
			const float Side = FMath::Sin(Leaf.Swing) * Leaf.SwingWide;
			Where.X += FMath::Cos(Rad) * Side;
			Where.Y += FMath::Sin(Rad) * Side;
			// AND IT LIES OVER AS IT SLIDES, which is the same motion seen on
			// the leaf itself: it banks into each side of the swing and is
			// flattest as it crosses the middle.
			Turn.Roll = FMath::Cos(Leaf.Swing) * 55.f;
			Turn.Pitch = FMath::Sin(Leaf.Swing * 0.5f) * 20.f;
		}

		UInstancedStaticMeshComponent* Comp = Leaf.bRust ? LeavesRust : LeavesGold;
		if (Comp && Comp->IsValidInstance(Leaf.Slot))
		{
			Comp->UpdateInstanceTransform(Leaf.Slot,
				FTransform(Turn, Where, FVector(Leaf.Size)), true, false, true);
		}
	}
	if (Leaves.Num() > 0)
	{
		if (LeavesGold) { LeavesGold->MarkRenderStateDirty(); }
		if (LeavesRust) { LeavesRust->MarkRenderStateDirty(); }
	}

	// ---- AND THE BIRDS ON THE GROUND, WHICH ARE THE ONES THAT NOTICE YOU ----
	//
	// Not gated on the weather. A gull stands on a beach in the rain and at
	// night, which is most of what a gull is; the butterflies' three gates are
	// about an insect and would be wrong here.
	AskedStanding += DeltaSeconds;
	if (Here != Ashore && AskedStanding > 0.75f)
	{
		AskedStanding = 0.f;
		GatherStanders(Here.X, Here.Y);
	}
	if (Standers.Num() > 0 && Standing)
	{
		const FVector Citizen = UIntervalGeometry::TileToWorld(Frame.Me.X, Frame.Me.Y);
		for (int32 i = 0; i < Standers.Num(); ++i)
		{
			FStander& Bird = Standers[i];
			Startle(Bird, Citizen, DeltaSeconds);

			FVector Where = Bird.From;
			float Pitch = 0.f;
			float Roll = 0.f;
			if (Bird.Flew >= 0.f)
			{
				const float T = FMath::Clamp(Bird.Flew, 0.f, 1.f);
				Where = FMath::Lerp(Bird.From, Bird.To, T);
				// UP HARD AND DOWN SLOWLY, which is how a bird leaves the
				// ground: the climb is the alarm and the glide down is not.
				// A symmetrical arc reads as a thrown stone.
				const float Rise = 260.f;
				Where.Z += Rise * FMath::Sin(FMath::Pow(T, 0.7f) * PI);
				Pitch = FMath::Cos(FMath::Pow(T, 0.7f) * PI) * 26.f;
				// a bank into the turn at the start, levelling out
				Roll = FMath::Sin(T * PI) * 18.f * (1.f - T);
			}
			Standing->UpdateInstanceTransform(i,
				FTransform(FRotator(Pitch, Bird.Yaw, Roll), Where, FVector(Bird.Size)),
				true, false, true);
		}
		Standing->MarkRenderStateDirty();
	}

	if (Hoppers.Num() == 0)
	{
		return;
	}

	for (int32 i = 0; i < Hoppers.Num(); ++i)
	{
		FFrog& Who = Hoppers[i];
		Leap(Who, DeltaSeconds);

		FVector Where = Who.From;
		float Pitch = 0.f;
		if (Who.Through >= 0.f)
		{
			const float T = FMath::Clamp(Who.Through, 0.f, 1.f);
			Where = FMath::Lerp(Who.From, Who.To, T);
			// THE ARC, which is the whole animation. A parabola peaking at a
			// third of the hop's length: high enough to read as a jump from
			// above and low enough that it is not a bird.
			const float Rise = FVector::Dist2D(Who.From, Who.To) * 0.34f;
			Where.Z += Rise * 4.f * T * (1.f - T);
			// AND IT NOSES UP AND THEN DOWN, which costs one cosine and is
			// the difference between a frog and a hovering disc.
			Pitch = FMath::Cos(T * PI) * 22.f;
		}

		const FRotator Facing(Pitch, Who.Yaw, 0.f);
		Frogs->UpdateInstanceTransform(i,
			FTransform(Facing, Where, FVector(Who.Size)), true, false, true);
	}
	Frogs->MarkRenderStateDirty();
}
