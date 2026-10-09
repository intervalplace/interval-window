#include "IntervalStructures.h"
#include "IntervalAnim.h"

#include "IntervalBridgeSubsystem.h"
#include "Serialization/JsonSerializer.h"
#include "Dom/JsonObject.h"
#include "IntervalGeometry.h"
#include "IntervalLook.h"
#include "Components/PointLightComponent.h"
#include "IntervalGround.h"
#include "EngineUtils.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "ProceduralMeshComponent.h"
#include "IntervalMotion.h"
#include "Animation/AnimSequence.h"
#include "Engine/SkeletalMesh.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"
#include "Components/AudioComponent.h"
#include "Sound/SoundAttenuation.h"

// §: NEVER `cond ? Bridge->GetFrame() : FIntervalFrame()`.
//
// It reads as a reference with a safe default and it is neither. The two arms
// of a conditional must have one type and one value category, so a reference
// on the left and a TEMPORARY on the right make the WHOLE expression a prvalue
// -- and binding it to `const FIntervalFrame&` then deep-copies the entire
// world: a TMap of every entity in sight, each one a TMap of strings. Every
// call. The `const&` on the left is what makes it look free.
//
// It cost the packaged client its frame rate. `AIntervalStructures::SownAt`
// does this and is called once per node from `Rebuild`, which runs on every
// chunk raised -- so walking into new country copied the world a few hundred
// times a chunk. A `sample` of the running game put 1,178 of 2,045 stacks
// inside the frame's copy constructor, under `SownAt`, under `RaiseChunk`.
//
// One shared empty frame, and both arms are real references.
// ONE NAME EACH, BECAUSE A UNITY BUILD HAS NO FILE SCOPE.
//
// `static` at file scope gives internal linkage in a translation unit of its
// own, and a unity build does not give it one: IntervalHand, IntervalHud and
// IntervalStructures each kept an empty frame under the same name, and the
// module stopped building the moment two of them were pasted together. Same
// fault as the colours and as `Round`, in the one place a scan for those two
// would not have looked.
static const FIntervalFrame GStructuresEmptyFrame;


DEFINE_LOG_CATEGORY_STATIC(LogIntervalStructures, Log, All);

namespace
{
	/**
	 * A hash of the node's own id. NOT a hash of position: the world handed us
	 * this id and it is stable across intervals, so a barrel keeps its angle
	 * when it is evicted from view and streamed back, and two windows showing
	 * the same barrel agree about it. Nothing here decides where anything is.
	 */
	uint32 IdHash(const FString& Id)
	{
		uint32 H = 2166136261u;
		for (TCHAR C : Id)
		{
			H ^= static_cast<uint32>(C);
			H *= 16777619u;
		}
		return H;
	}

	float UnitFromHash(uint32 H, uint32 Salt)
	{
		const uint32 X = (H ^ (Salt * 2654435761u)) * 2246822519u;
		return static_cast<float>((X >> 8) & 0xFFFFFF) / static_cast<float>(0xFFFFFF);
	}
}

AIntervalStructures::AIntervalStructures()
{
	PrimaryActorTick.bCanEverTick = false;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}

// WHEN OUR CITIZEN SOWED THIS PLOT, or 0 if they did not.
//
// The sowing is NOT on the node. `p.crops[plotId]` is on the PLAYER, and the
// engine says why in as many words -- §6o, "the row is the CITIZEN'S. The
// ground is nobody's" -- so two citizens can each have a crop coming on in the
// same square of earth and neither can see the other's.
//
// This was got wrong first: the stages read the node's `plantedAt`, which no
// executor ever writes. All twelve hundred plots in view carry 0, so every bed
// would have stayed bare for ever and looked like it was working.
//
// Parsed once a frame, because `crops` arrives as raw JSON in one field and a
// thousand plots each parsing it is a thousand parses of the same string.
int64 AIntervalStructures::SownAt(const FString& NodeId)
{
	const FIntervalFrame& Frame = Bridge ? Bridge->GetFrame() : GStructuresEmptyFrame;
	if (CropsTick != Frame.Tick)
	{
		CropsTick = Frame.Tick;
		Crops.Reset();
		if (const FString* Raw = Frame.Me.Fields.Find(TEXT("crops")))
		{
			TSharedPtr<FJsonObject> Obj;
			const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(*Raw);
			if (FJsonSerializer::Deserialize(Reader, Obj) && Obj.IsValid())
			{
				for (const TPair<FString, TSharedPtr<FJsonValue>>& Row : Obj->Values)
				{
					double When = 0.0;
					if (Row.Value.IsValid() && Row.Value->TryGetNumber(When))
					{
						Crops.Add(Row.Key, static_cast<int64>(When));
					}
				}
			}
		}
	}
	const int64* Found = Crops.Find(NodeId);
	return Found ? *Found : 0;
}

void AIntervalStructures::BeginPlay()
{
	Super::BeginPlay();

	UGameInstance* GameInstance = GetGameInstance();
	Bridge = GameInstance ? GameInstance->GetSubsystem<UIntervalBridgeSubsystem>() : nullptr;
	if (!Bridge)
	{
		UE_LOG(LogIntervalStructures, Error, TEXT("no bridge subsystem: is the plugin enabled?"));
		return;
	}

	Bridge->OnFrame.AddDynamic(this, &AIntervalStructures::HandleFrame);

	if (!Ground)
	{
		TActorIterator<AIntervalGround> It(GetWorld());
		if (It) { Ground = *It; }
	}
	if (Ground)
	{
		Ground->OnGroundChanged.AddDynamic(this, &AIntervalStructures::HandleGroundChanged);
	}

	// The bridge may already be several intervals in by the time a level opens.
	if (Bridge->GetFrame().Tick > 0)
	{
		HandleFrame();
	}
}

void AIntervalStructures::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (Bridge)
	{
		Bridge->OnFrame.RemoveDynamic(this, &AIntervalStructures::HandleFrame);
	}
	if (Ground)
	{
		Ground->OnGroundChanged.RemoveDynamic(this, &AIntervalStructures::HandleGroundChanged);
	}
	Super::EndPlay(EndPlayReason);
}

void AIntervalStructures::HandleGroundChanged()
{
	// The answer to "is there a building under this tile" just changed
	// somewhere, so everything drawn against the old answer is stale.
	LastDigest = 0;
	if (Bridge && Bridge->GetFrame().Tick > 0)
	{
		Rebuild(Bridge->GetFrame());
	}
}

void AIntervalStructures::HandleFrame()
{
	// The frame is READ rather than handed over: a dynamic delegate copies
	// whatever it carries, and what this used to carry was the whole world.
	// See FIntervalFrameEvent in IntervalBridgeSubsystem.h.
	if (!Bridge) { return; }
	const FIntervalFrame& Frame = Bridge->GetFrame();
	// A digest of what is standing where. The island's furniture changes when
	// somebody chops something, not sixty times a second, and clearing ten
	// thousand instances every interval to put back the same ten thousand is
	// the kind of cost that gets paid forever because nobody measured it.
	uint64 Digest = static_cast<uint64>(Frame.Nodes.Num()) * 1099511628211ull;
	for (const TPair<FString, FIntervalEntity>& Pair : Frame.Nodes)
	{
		const FIntervalEntity& Node = Pair.Value;
		uint64 Row = IdHash(Node.Id);
		Row = Row * 31 + static_cast<uint32>(Node.X);
		Row = Row * 31 + static_cast<uint32>(Node.Y);
		if (const FString* Spent = Node.Fields.Find(TEXT("depletedUntil")))
		{
			Row = Row * 31 + GetTypeHash(*Spent);
		}
		Digest ^= Row;   // order-independent: a TMap does not promise one
	}

	// AND WHAT IS LYING ON THE GROUND. Loot is the fastest-changing thing in
	// the world -- it falls when something dies and expires a hundred intervals
	// later -- so leaving it out of the digest would mean a drop appearing only
	// when somebody happened to fell a tree nearby, and never disappearing.
	for (const TPair<FString, FIntervalEntity>& Pair : Frame.Ground)
	{
		const FIntervalEntity& Item = Pair.Value;
		uint64 Row = IdHash(Item.Id);
		Row = Row * 31 + static_cast<uint32>(Item.X);
		Row = Row * 31 + static_cast<uint32>(Item.Y);
		Digest ^= Row;
	}

	if (Digest == LastDigest)
	{
		return;
	}
	LastDigest = Digest;
	Rebuild(Frame);
}

UInstancedStaticMeshComponent* AIntervalStructures::ComponentFor(FName Key, const FIntervalPropKind& Kind)
{
	return PoolFor(Key, Kind.Mesh, Kind.Material, Kind.bCastShadow);
}

UInstancedStaticMeshComponent* AIntervalStructures::PoolFor(
	FName Key, UStaticMesh* Mesh, UMaterialInterface* Material, bool bCastShadow)
{
	if (TObjectPtr<UInstancedStaticMeshComponent>* Found = Pools.Find(Key))
	{
		return Found->Get();
	}

	UInstancedStaticMeshComponent* Pool = NewObject<UInstancedStaticMeshComponent>(this);
	Pool->SetupAttachment(RootComponent);
	Pool->SetMobility(EComponentMobility::Movable);
	Pool->SetStaticMesh(Mesh);
	// Nothing here is walked into or clicked: the hand talks to the bridge in
	// tiles, never to a collider.
	Pool->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Pool->NumCustomDataFloats = 1;   // the building seed, for the material
	Pool->RegisterComponent();
	// MATERIAL AFTER REGISTRATION, and it is not a style preference. Setting
	// an override before the component has a render state leaves the mesh's
	// own slot in place, and every one of these is an engine primitive whose
	// own slot is the checkered grid material. The whole town came out in
	// brown-grey check and read as a lighting fault rather than a missing
	// assignment, which is why it took a grove of trees to notice.
	if (Material)
	{
		Pool->SetMaterial(0, Material);
	}
	Pool->SetCastShadow(bCastShadow);
	Pools.Add(Key, Pool);
	return Pool;
}

void AIntervalStructures::Rebuild(const FIntervalFrame& Frame)
{
	// The masonry first: it draws some of the same words the prop pass below
	// would otherwise draw as cubes, and the pass below skips whatever it took.
	BuildPalisades(Frame);

	for (const TPair<FName, TObjectPtr<UInstancedStaticMeshComponent>>& Pair : Pools)
	{
		if (Pair.Value)
		{
			Pair.Value->ClearInstances();
		}
	}

	// Figures are components, not instances, so they have to be taken down by
	// hand when the world stops naming them -- a keeper whose stall is gone
	// otherwise stands in the field forever.
	FiguresSeen.Reset();

	// PASS ONE: WHAT IS EACH BUILDING FOR.
	//
	// The world says what stands inside a building; the level says which of
	// those words tells you what the building IS. Nothing here knows what a
	// forge is -- only that some words are more telling than others, and that
	// the level ordered them.
	TMap<int64, FName> TradeByBuilding;
	if (Ground && TradeOf.Num() > 0)
	{
		TArray<FName> Order;
		TradeOf.GenerateKeyArray(Order);
		TMap<int64, int32> BestRank;
		for (const TPair<FString, FIntervalEntity>& Pair : Frame.Nodes)
		{
			const FIntervalEntity& Node = Pair.Value;
			const FName Word(*Node.Kind);
			const FName* Trade = TradeOf.Find(Word);
			if (!Trade) { continue; }
			const int64 Key = Ground->BuildingKeyAtTile(Node.X, Node.Y);
			if (Key == 0) { continue; }
			const int32 Rank = Order.IndexOfByKey(Word);
			int32& Best = BestRank.FindOrAdd(Key, MAX_int32);
			if (Rank < Best) { Best = Rank; TradeByBuilding.Add(Key, *Trade); }
		}
	}

	// THE TABLES COME FROM THE ASSET WHEN THERE IS ONE. They used to live on
	// this actor, and an external-actor package is a thing this project cannot
	// save under automation -- so a session's worth of look went with every
	// rebuild. What is still on the actor is honoured when no asset answers.
	const UIntervalLook* Chosen = UIntervalLook::Resolve(LookAsset());
	const TMap<FName, FIntervalPropKind>& Table =
		(Chosen && Chosen->Props.Num() > 0) ? Chosen->Props : Props;
	const TMap<FName, FIntervalPropKind>& UpperTable =
		(Chosen && Chosen->PropsUpper.Num() > 0) ? Chosen->PropsUpper : PropsUpper;

	TendFires(Frame);

	// WHERE EVERY WORD IS STANDING, gathered before anything is drawn.
	//
	// A panel cannot know which way to face without seeing its neighbours, and
	// the frame is a map keyed by id, not by tile -- so asking "is there
	// another fence east of me?" during the draw would be a scan of every node
	// in the world, per node. One pass up front makes it a lookup.
	//
	// Keyed by the bare word rather than the drawn kind: a run of fence is a
	// run of fence whether or not the level has split it into sorts.
	TMap<FName, TSet<int64>> TilesByWord;
	for (const TPair<FString, FIntervalEntity>& Pair : Frame.Nodes)
	{
		const FIntervalEntity& N = Pair.Value;
		if (N.Kind.IsEmpty()) { continue; }
		TilesByWord.FindOrAdd(FName(*N.Kind)).Add(
			(static_cast<int64>(N.X) << 32) ^ static_cast<uint32>(N.Y));
	}
	auto StandsAt = [&TilesByWord](const FName& Word, int32 X, int32 Y)
	{
		const TSet<int64>* Tiles = TilesByWord.Find(Word);
		return Tiles && Tiles->Contains((static_cast<int64>(X) << 32) ^ static_cast<uint32>(Y));
	};

	int32 Drawn = 0;
	for (const TPair<FString, FIntervalEntity>& Pair : Frame.Nodes)
	{
		const FIntervalEntity& Node = Pair.Value;
		if (Node.Kind.IsEmpty())
		{
			continue;
		}
		// Already built as masonry. Drawing it again as a scaled cube puts a
		// garden wall inside a curtain wall, which is visible from a long way
		// off and looks like the wall has a seam down it.
		if (Chosen && Chosen->Palisades.Contains(FName(*Node.Kind)))
		{
			continue;
		}

		// The more specific entry wins, so a level may single out one sort of
		// a word without this file ever learning that the sort exists.
		const FIntervalPropKind* Kind = nullptr;
		FName Key;
		if (const FString* Sub = Node.Fields.Find(TEXT("kind")))
		{
			if (!Sub->IsEmpty())
			{
				Key = FName(Node.Kind + TEXT(".") + *Sub);
				Kind = Table.Find(Key);
			}
		}
		// THE WINDOW'S OWN FACT, not the world's word. Whether this tile is
		// under a roof is something this window worked out from the footprint;
		// the world never said it. A level may key a look on it --
		// `wall.roofed` against `wall.unroofed` -- so a house wall and a yard
		// wall can be different things without anything in C++ deciding which.
		const uint8 Seed = Ground ? Ground->BuildingSeedAtTile(Node.X, Node.Y) : 0;
		const int64 Building = Ground ? Ground->BuildingKeyAtTile(Node.X, Node.Y) : 0;
		if (!Kind && Building != 0)
		{
			if (const FName* Trade = TradeByBuilding.Find(Building))
			{
				Key = FName(Node.Kind + TEXT(".") + Trade->ToString());
				Kind = Table.Find(Key);
			}
		}
		if (!Kind)
		{
			Key = FName(Node.Kind + (Seed ? TEXT(".roofed") : TEXT(".unroofed")));
			Kind = Table.Find(Key);
		}
		if (!Kind)
		{
			Key = FName(*Node.Kind);
			Kind = Table.Find(Key);
		}
		// A KIND WITH STAGES IS DRAWN, even when `Parts` is empty -- its pieces
		// live in the stages instead, and an unsown plot legitimately has none
		// at all beyond its bed.
		if (!Kind || (!Kind->Mesh && !Kind->Skeletal && Kind->Variants.Num() == 0
			&& Kind->Parts.Num() == 0 && Kind->Stages.Num() == 0))
		{
			if (bReportUndrawnKinds && !Reported.Contains(Key))
			{
				Reported.Add(Key);
				UE_LOG(LogIntervalStructures, Warning,
					TEXT("the world says '%s' is standing here and this window has no mesh for it"),
					*Key.ToString());
			}
			continue;
		}

		if (Kind->bHideWhenDepleted)
		{
			if (const FString* Spent = Node.Fields.Find(TEXT("depletedUntil")))
			{
				if (FCString::Atoi64(**Spent) > Frame.Tick)
				{
					continue;
				}
			}
		}

		const uint32 H = IdHash(Node.Id);

		// WHERE THE VARIATION COMES FROM. A node's own id, normally: two
		// barrels standing side by side should not be the same barrel. But
		// anything that is PART OF A BUILDING takes its figure from the
		// building instead, or one house gets four walls of four thicknesses
		// and reads as a ruin rather than a house.
		auto Spread = [&](float Fraction, uint32 Salt)
		{
			if (Fraction <= 0.f) { return 1.f; }
			const float U = Building != 0
				? UIntervalGeometry::BuildingUnit(Building, Salt)
				: UnitFromHash(H, Salt);
			return 1.f - Fraction + U * Fraction * 2.f;
		};

		float Yaw = Kind->YawJitter > 0.f ? UnitFromHash(H, 1) * Kind->YawJitter : 0.f;
		bool bCorner = false;

		// ...unless this kind is a panel, in which case the line decides. See
		// bAlignToRun: a fence that does not lie along its own run is a fence
		// with holes in it.
		if (Kind->bAlignToRun)
		{
			const FName Word(*Node.Kind);
			const bool bAlongX = StandsAt(Word, Node.X - 1, Node.Y)
				|| StandsAt(Word, Node.X + 1, Node.Y);
			const bool bAlongY = StandsAt(Word, Node.X, Node.Y - 1)
				|| StandsAt(Word, Node.X, Node.Y + 1);
			// A corner can see both, and ONE panel cannot lie along two runs.
			// Preferring X was deterministic and left the other arm hanging in
			// the air a whole tile short -- which is what a fenced plot looked
			// like from above: four sides that never met at any corner. So a
			// corner gets a second panel, below, and this only picks which one
			// is first.
			bCorner = bAlongX && bAlongY;
			if (bAlongX) { Yaw = 0.f; }
			else if (bAlongY) { Yaw = 90.f; }
		}
		// A PANEL DOES NOT WOBBLE IN LENGTH.
		//
		// Scale jitter is what stops a hundred boulders reading as one boulder
		// a hundred times, and it is exactly wrong for anything that has to
		// MEET its neighbour: at fourteen per cent a two-metre fence panel
		// comes out anywhere between 1.72 and 2.28 metres, so a straight run
		// is a row of different-length rails with daylight at most of the
		// posts and an overlap at the rest. That is precisely how it looked.
		const float Jit = Kind->bAlignToRun ? 1.f : Spread(Kind->ScaleJitter, 2);

		// Height is its own question, so that a house may be tall and narrow
		// rather than merely bigger. For a building the answer is the world's
		// one rule, which the ROOF asks in the same words -- the level does
		// not get a say, because a level that set it per kind could put the
		// thatch somewhere the walls are not.
		// ---- A WALL UNDULATES. IT DOES NOT STEP ----
		//
		// This was `Spread(Kind->HeightJitter, 5)`, and `Spread` reads the hash
		// of the NODE'S OWN ID. Every segment of a run therefore drew an
		// independent height, which is white noise: two neighbours two metres
		// apart could differ by a fifth of the wall, so the top edge stepped at
		// every joint and the whole run read as a row of separate blocks at
		// angles to each other. Reported from the window as walls that are
		// "all corners".
		//
		// The intent was right and is worth keeping -- the note over `TOPS` in
		// apply.py says a dead-level coping over forty tiles is the tell, and
		// it is. A wall laid by hand undulates, but it undulates SLOWLY: the
		// courses drift over ten or twenty metres, not between one stone and
		// the next.
		//
		// So the height comes from POSITION on a coarse grid, smoothed. One
		// value every four tiles, interpolated both ways with a smoothstep, so
		// neighbouring segments agree closely, the run drifts over eight metres
		// and nothing anywhere is dead level. Position rather than id also
		// means two walls meeting at a corner agree about the height there,
		// which an id hash could never do.
		auto Undulate = [](int32 Gx, int32 Gy)
		{
			uint32 h = 2166136261u;
			h = (h ^ static_cast<uint32>(Gx * 73856093)) * 16777619u;
			h = (h ^ static_cast<uint32>(Gy * 19349663)) * 16777619u;
			h ^= h >> 13;
			return static_cast<float>(h & 0xffffu) / 65535.f;
		};
		float Tall = 1.f;
		if (Building != 0)
		{
			Tall = UIntervalGeometry::BuildingHeight(Building);
		}
		else if (Kind->HeightJitter > 0.f)
		{
			const int32 Gx = Node.X >> 2, Gy = Node.Y >> 2;
			const float Fx = static_cast<float>(Node.X - (Gx << 2)) * 0.25f;
			const float Fy = static_cast<float>(Node.Y - (Gy << 2)) * 0.25f;
			const float Sx = Fx * Fx * (3.f - 2.f * Fx);
			const float Sy = Fy * Fy * (3.f - 2.f * Fy);
			const float U = FMath::Lerp(
				FMath::Lerp(Undulate(Gx, Gy), Undulate(Gx + 1, Gy), Sx),
				FMath::Lerp(Undulate(Gx, Gy + 1), Undulate(Gx + 1, Gy + 1), Sx), Sy);
			Tall = 1.f - Kind->HeightJitter + U * Kind->HeightJitter * 2.f;
		}

		FVector Location = UIntervalGeometry::TileToWorld(Node.X, Node.Y);
		// The pivot is centred and the offset is half the height, so the same
		// figure on both keeps the base on the ground instead of sinking it.
		Location.Z += Kind->ZOffset * Tall;

		// A PERSON IS NOT AN INSTANCE. Where a kind names a skeleton this node
		// gets a component of its own and the pooled path is skipped.
		//
		// SKIPPED, NOT ABANDONED. This used to `continue`, which jumped the
		// whole remainder of the loop -- including the PARTS below -- so the
		// moment keepers stopped being cylinders and became people, every
		// keeper's kit stopped being drawn with them. The brewer's barrel, the
		// wizard's staff, the smith's anvil, the runner's sack: all still in
		// the look, none of them on the ground, and no way to tell one trade
		// from another in a market place. `apply.py` was then told to clear
		// those parts, which made the data agree with the omission and hid it
		// for good. A keeper's tools are not their body, and only the body is
		// replaced by the figure.
		const bool bStood = (Kind->Skeletal != nullptr);
		if (bStood)
		{
			StandFigure(Node.Id, *Kind, UIntervalGeometry::TileToWorld(Node.X, Node.Y),
				Yaw, Jit);
		}

		// WHICH OF THEM THIS ONE IS. Off the node's own id, so a wood is a wood
		// and the tree at the ford is the same tree in every window. Each
		// variant needs its own pool, because a pool is one mesh.
		UStaticMesh* Shape = Kind->Mesh.Get();
		FName PoolKey = Key;
		if (Kind->Variants.Num() > 0)
		{
			const int32 Which = static_cast<int32>(H % static_cast<uint32>(Kind->Variants.Num()));
			if (Kind->Variants[Which])
			{
				Shape = Kind->Variants[Which].Get();
				PoolKey = FName(*FString::Printf(TEXT("%s#%d"), *Key.ToString(), Which));
			}
		}

		if (Shape && !bStood)
		{
			UInstancedStaticMeshComponent* Pool =
				PoolFor(PoolKey, Shape, Kind->Material.Get(), Kind->bCastShadow);
			FVector Size = Kind->Scale * Jit;
			Size.Z = Kind->Scale.Z * Jit * Tall;
			// ---- AND HOW THE ART WAS MODELLED, BEFORE THE WORLD TURNS IT ----
			//
			// `Lean` has existed on the prop kind all along and was read only
			// by the BEASTS. Its own note says what it is for: "how the art
			// was modelled, as opposed to how it stands", which is as true of
			// a log as of a bear. Without it here a base mesh could only ever
			// stand upright, so a log pile had to be built out of `Parts` --
			// which carry a rotation -- and its base stood on its end like a
			// drum among them.
			//
			// Applied BEFORE the world's own yaw, exactly as the beasts apply
			// it, so a kind that leans still turns with its tile.
			const int32 At = Pool->AddInstance(
				FTransform((FRotator(0.f, Yaw, 0.f).Quaternion()
					* Kind->Lean.Quaternion()).Rotator(), Location, Size), true);
			// AND THE OTHER ARM OF A CORNER. Two panels crossing on one tile
			// is what a real corner post is: the run going east meets the run
			// going south and neither of them stops short.
			if (bCorner)
			{
				const int32 Across = Pool->AddInstance(
					FTransform(FRotator(0.f, Yaw + 90.f, 0.f), Location, Size), true);
				if (Pool->NumCustomDataFloats > 0)
				{
					Pool->SetCustomDataValue(Across, 0,
						static_cast<float>(Seed) / 255.f, true);
				}
			}
			// Which house this is, for the material: a hash of the building's own
			// corner in world tiles, so every wall of one house agrees and no two
			// houses in a street are washed the same.
			if (Pool->NumCustomDataFloats > 0)
			{
				Pool->SetCustomDataValue(At, 0, static_cast<float>(Seed) / 255.f, true);
			}
		}
		// THE OTHER PIECES. A well is a drum, two posts, a beam and a little
		// roof; drawn as one primitive it is a barrel. Each piece rides in its
		// own pool -- one draw call per piece across the whole island, not one
		// per well -- and is turned by the node's own angle so a signpost and
		// its arm point the same way.
		// AND WHICH SET OF PIECES, for a thing that grows.
		//
		// A plot was drawn the same from the moment it was tilled to the moment
		// it was cut -- a crop standing in ground nobody had sown. The node
		// carries `plantedAt`, and the world ripens it over `RipeTicks`, so the
		// stage is arithmetic on two numbers the frame already has. The LAST
		// stage whose `At` has been passed wins; a kind with no stages uses
		// `Parts` exactly as it always did, which is nearly all of them.
		//
		// `plantedAt` of zero is not "sown at the beginning of time", it is
		// NOT SOWN -- the engine writes 0 into an empty plot -- so it is read
		// as the bare stage rather than as fully ripe, which is what treating
		// it as a tick would have given.
		const TArray<FIntervalPropPart>* Pieces = &Kind->Parts;
		if (Kind->Stages.Num() > 0)
		{
			float Ripeness = 0.f;
			const int64 Sown = SownAt(Node.Id);
			if (Sown > 0 && Kind->RipeTicks > 0)
			{
				Ripeness = FMath::Clamp(
					float(Frame.Tick - Sown) / float(Kind->RipeTicks), 0.f, 1.f);
			}
			for (const FIntervalPropStage& Stage : Kind->Stages)
			{
				if (Ripeness + KINDA_SMALL_NUMBER >= Stage.At)
				{
					Pieces = &Stage.Parts;
				}
			}
		}
		for (int32 Part = 0; Part < Pieces->Num(); ++Part)
		{
			const FIntervalPropPart& Piece = (*Pieces)[Part];
			if (!Piece.Mesh)
			{
				continue;
			}
			// Hung on a bone by `Stand` above, not dropped on the tile here.
			if (bStood && !Piece.Bone.IsNone())
			{
				continue;
			}
			const FRotator Turn(0.f, Yaw, 0.f);
			FVector Where = UIntervalGeometry::TileToWorld(Node.X, Node.Y);
			FVector Local = Piece.Offset * Jit;
			Local.Z = Piece.Offset.Z * Jit * Tall;
			Where += Turn.RotateVector(Local);

			FVector PieceSize = Piece.Scale * Jit;
			PieceSize.Z = Piece.Scale.Z * Jit * Tall;

			UInstancedStaticMeshComponent* PiecePool = PoolFor(
				FName(*FString::Printf(TEXT("%s#%d"), *Key.ToString(), Part)),
				Piece.Mesh, Piece.Material, Piece.bCastShadow);
			const int32 PieceAt = PiecePool->AddInstance(
				FTransform(Turn + Piece.Rotation, Where, PieceSize), true);
			if (PiecePool->NumCustomDataFloats > 0)
			{
				PiecePool->SetCustomDataValue(PieceAt, 0, static_cast<float>(Seed) / 255.f, true);
			}
		}
		++Drawn;

		// The second storey, if this word has one. Same position, same angle,
		// its own width and height -- which is what makes it a jetty rather
		// than a taller wall.
		if (const FIntervalPropKind* Upper = UpperTable.Find(Key))
		{
			if (Upper->Mesh)
			{
				FVector Above = UIntervalGeometry::TileToWorld(Node.X, Node.Y);
				// Rides up with the storey below it: its offset already
				// clears the lower wall, so the same figure carries both.
				Above.Z += Upper->ZOffset * Tall;
				const float UpperJit = Spread(Upper->ScaleJitter, 3);
				FVector UpperSize = Upper->Scale * UpperJit;
				UpperSize.Z = Upper->Scale.Z * UpperJit * Tall;
				UInstancedStaticMeshComponent* UpperPool =
					ComponentFor(FName(*(Key.ToString() + TEXT(".upper"))), *Upper);
				const int32 UpAt = UpperPool->AddInstance(
					FTransform(FRotator(0.f, Yaw, 0.f), Above, UpperSize), true);
				if (UpperPool->NumCustomDataFloats > 0)
				{
					UpperPool->SetCustomDataValue(UpAt, 0, static_cast<float>(Seed) / 255.f, true);
				}
			}
		}
	}

	// ---- WHAT IS LYING ON THE GROUND ----
	//
	// Every drop in this world was INVISIBLE. A beast dies, its bones lie on
	// the tile for a hundred intervals and expire, and the only way to know
	// they were ever there was to read the socket. Loot is the one thing a
	// citizen is actively looking for after a fight, and it was the one thing
	// the window did not draw.
	//
	// Drawn from the item's OWN art where it has some -- a dropped hatchet is
	// the hatchet, lying down -- and from a plain bundle where it has none,
	// which is most of them: bones, ore, seeds and logs have no mesh of their
	// own and do not need one to be seen and stood on.
	//
	// AND IT IS A THING YOU STAND ON, not one you stand beside. The world
	// refuses a pickup unless the citizen is ON the tile (`g2.x !== p.x`),
	// unlike buying and gathering which want adjacency -- so it is drawn low
	// and centred, where a foot would go, rather than propped up like furniture.
	int32 Lying = 0;
	for (const TPair<FString, FIntervalEntity>& Pair : Frame.Ground)
	{
		const FIntervalEntity& Item = Pair.Value;
		const FString* What = Item.Fields.Find(TEXT("item"));
		const FName Word(What ? **What : TEXT(""));

		const FIntervalPropKind* Kind = Table.Find(FName(*(FString(TEXT("dropped.")) + Word.ToString())));
		if (!Kind) { Kind = Table.Find(FName(TEXT("dropped"))); }
		if (!Kind || !Kind->Mesh) { continue; }

		// Its own id decides how it fell, so a pile of three does not stack
		// into one shape and nothing shifts when you look away.
		const uint32 H = IdHash(Item.Id);
		const float Yaw = UnitFromHash(H, 1) * 360.f;
		const float Off = 34.f;
		FVector Where = UIntervalGeometry::TileToWorld(Item.X, Item.Y);
		Where.X += (UnitFromHash(H, 2) - 0.5f) * Off;
		Where.Y += (UnitFromHash(H, 3) - 0.5f) * Off;
		Where.Z += Kind->ZOffset;

		UInstancedStaticMeshComponent* Pool = ComponentFor(
			FName(*(FString(TEXT("dropped#")) + Word.ToString())), *Kind);
		Pool->AddInstance(FTransform(FRotator(0.f, Yaw, 0.f), Where, Kind->Scale), true);
		++Lying;
	}

	UE_LOG(LogIntervalStructures, Log, TEXT("tick %lld: drew %d of %d things standing, %d lying"),
		Frame.Tick, Drawn, Frame.Nodes.Num(), Lying);

	// ---- WHAT DREW THIS TILE ----
	//
	// Asked by writing a tile into the look; answered here and put back. See
	// the note over `WhatDrewX` in IntervalLook.h for why it is asked that way
	// and why it exists at all: reading a thing's identity off a photograph
	// named four wrong things before it named a right one, and the window has
	// known the answer the whole time.
	if (Chosen && Chosen->WhatDrewX >= 0.f && Chosen->WhatDrewY >= 0.f)
	{
		const int32 AskX = FMath::RoundToInt(Chosen->WhatDrewX);
		const int32 AskY = FMath::RoundToInt(Chosen->WhatDrewY);
		// A BLOCK, NOT A TILE. Asking one tile means knowing which tile to
		// ask, and knowing that has been the whole difficulty: a tile read
		// off a photograph has been wrong four times out of five. A block
		// forty tiles square is the frame a survey shot covers, so one
		// question answers for everything in the picture.
		const FVector Centre = UIntervalGeometry::TileToWorld(AskX, AskY);
		const float Reach = UIntervalGeometry::TileSize * 20.f;
		UE_LOG(LogIntervalStructures, Warning,
			TEXT("WHATDREW block around tile %d,%d (%.0f,%.0f), 40 tiles square:"),
			AskX, AskY, Centre.X, Centre.Y);

		// mesh name -> how many, and where one of them stands
		TMap<FString, int32> Tally;
		TMap<FString, FVector> Where;
		TMap<FString, FString> Owner;
		int32 Found = 0;
		for (TActorIterator<AActor> It(GetWorld()); It; ++It)
		{
			TArray<UInstancedStaticMeshComponent*> Here;
			It->GetComponents(Here);
			for (UInstancedStaticMeshComponent* Pool : Here)
			{
				if (!Pool || !Pool->GetStaticMesh()) { continue; }
				const FString Mesh = Pool->GetStaticMesh()->GetName();
				const int32 Count = Pool->GetInstanceCount();
				for (int32 i = 0; i < Count; ++i)
				{
					FTransform T;
					if (!Pool->GetInstanceTransform(i, T, true)) { continue; }
					const FVector P = T.GetLocation();
					if (FMath::Abs(P.X - Centre.X) > Reach
					 || FMath::Abs(P.Y - Centre.Y) > Reach) { continue; }
					++Found;
					Tally.FindOrAdd(Mesh)++;
					if (!Where.Contains(Mesh))
					{
						Where.Add(Mesh, P);
						Owner.Add(Mesh, Pool->GetName());
					}
				}
			}
		}
		Tally.ValueSort([](int32 A, int32 B) { return A > B; });
		for (const TPair<FString, int32>& Row : Tally)
		{
			const FVector P = Where[Row.Key];
			UE_LOG(LogIntervalStructures, Warning,
				TEXT("WHATDREW   %-26s x%-5d  one at tile %d,%d  component=%s"),
				*Row.Key, Row.Value,
				FMath::FloorToInt(P.X / UIntervalGeometry::TileSize),
				FMath::FloorToInt(P.Y / UIntervalGeometry::TileSize),
				*Owner[Row.Key]);
		}
		UE_LOG(LogIntervalStructures, Warning,
			TEXT("WHATDREW %d instance(s) of %d distinct mesh(es)"), Found, Tally.Num());

		// Put the question back, so one write asks exactly once.
		UIntervalLook* Mutable = const_cast<UIntervalLook*>(Chosen);
		Mutable->WhatDrewX = -1.f;
		Mutable->WhatDrewY = -1.f;
	}

	for (auto It = Figures.CreateIterator(); It; ++It)
	{
		if (FiguresSeen.Contains(It.Key()))
		{
			continue;
		}
		if (USkeletalMeshComponent* Gone = It.Value().Get())
		{
			Gone->DestroyComponent();   // its followers are its children and go with it
		}
		It.RemoveCurrent();
	}
}

void AIntervalStructures::TendFires(const FIntervalFrame& Frame)
{
	const UIntervalLook* Chosen = UIntervalLook::Resolve(LookAsset());
	const TMap<FName, FIntervalPropKind>& Table =
		(Chosen && Chosen->Props.Num() > 0) ? Chosen->Props : Props;

	// ---- ONLY THE NEAREST FEW ----
	// A hundred and fifty hearths is a hundred and fifty shadow-casting lights
	// and no frame can pay for that. The window lights the ones a citizen
	// could actually see the light of, and moves them as they walk. Nothing
	// about the world changes with which ones are lit; this is a budget, not
	// a fact.
	const FVector Here = Frame.bHasMe
		? UIntervalGeometry::TileToWorld(Frame.Me.X, Frame.Me.Y)
		: FVector::ZeroVector;

	struct FEmber { float Away; FVector At; const FIntervalPropKind* Kind; uint32 Seed; bool bIndoors; FIntPoint Tile; };
	TArray<FEmber> Embers;
	for (const TPair<FString, FIntervalEntity>& Pair : Frame.Nodes)
	{
		const FIntervalEntity& Node = Pair.Value;
		const FIntervalPropKind* Kind = nullptr;
		if (const FString* Sub = Node.Fields.Find(TEXT("kind")))
		{
			Kind = Table.Find(FName(Node.Kind + TEXT(".") + *Sub));
		}
		if (!Kind) { Kind = Table.Find(FName(*Node.Kind)); }
		if (!Kind || Kind->LightIntensity <= 0.f)
		{
			continue;
		}
		FVector At = UIntervalGeometry::TileToWorld(Node.X, Node.Y);
		At.Z += Kind->LightHeight;
		const float Away = FVector::DistSquared(At, Here);
		// UNDER A ROOF IT IS NIGHT ALL DAY. `bLightAtNightOnly` exists so the
		// window does not pay for a hundred hearths in broad daylight, and
		// outdoors that is right. Indoors it is exactly wrong: a roof stops the
		// sky, so a hall whose fire is out until dusk is a black hole in the
		// middle of a bright afternoon -- which is what a shopkeeper standing
		// in one looked like. The window already works out which tiles are
		// roofed, for the walls; this is the same question.
		const bool bIndoors = Ground && Ground->BuildingKeyAtTile(Node.X, Node.Y) != 0;
		Embers.Add({ Away, At, Kind, IdHash(Node.Id), bIndoors, FIntPoint(Node.X, Node.Y) });
	}
	Embers.Sort([](const FEmber& A, const FEmber& B) { return A.Away < B.Away; });

	const int32 Want = FMath::Min(FireLights, Embers.Num());
	while (Fires.Num() < Want)
	{
		UPointLightComponent* Lamp = NewObject<UPointLightComponent>(this);
		Lamp->SetupAttachment(RootComponent);
		Lamp->SetMobility(EComponentMobility::Movable);
		Lamp->SetCastShadows(false);      // a hearth lighting a room, not a stage
		Lamp->bUseInverseSquaredFalloff = false;
		Lamp->RegisterComponent();
		Fires.Add(Lamp);
	}

	// How dark it is, which is the world's number and not this file's opinion.
	// HOW DARK IT IS -- AND THE SAME ANSWER THE SKY IS USING.
	//
	// This read the frame's own day amount and nothing else, which is right
	// until `ForceDay` is set: the sky then draws noon while the hearths still
	// think it is midnight, and a photograph taken to check the smoke came
	// back with a watchfire at full strength burning a white hole in a sunlit
	// meadow. Two opinions about what time it is is one too many, and the
	// override belongs to the look, so the look is asked first here exactly as
	// it is in the hour.
	float Day = Frame.Sky.bValid ? FMath::Clamp(Frame.Sky.DayAmount, 0.f, 1.f) : 1.f;
	if (Chosen && Chosen->ForceDay >= 0.f)
	{
		Day = FMath::Clamp(Chosen->ForceDay, 0.f, 1.f);
	}
	const float Night = 1.f - Day;
	const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;

	for (int32 i = 0; i < Fires.Num(); ++i)
	{
		UPointLightComponent* Lamp = Fires[i];
		if (!Lamp) { continue; }
		if (i >= Want)
		{
			Lamp->SetVisibility(false);
			continue;
		}
		const FEmber& E = Embers[i];
		const float Dark = (E.Kind->bLightAtNightOnly && !E.bIndoors) ? Night : 1.f;
		if (Dark <= 0.02f)
		{
			Lamp->SetVisibility(false);
			continue;
		}
		// Nothing that burns is steady. Two waves that share no period, so it
		// gutters rather than pulses, and each fire on its own phase.
		const float Phase = static_cast<float>(E.Seed % 997u) * 0.0063f;
		const float Gutter = 1.f
			+ E.Kind->LightFlicker * 0.5f * FMath::Sin(Now * 7.3f + Phase)
			+ E.Kind->LightFlicker * 0.3f * FMath::Sin(Now * 17.9f + Phase * 3.1f);

		Lamp->SetWorldLocation(E.At);
		Lamp->SetVisibility(true);
		Lamp->SetLightColor(E.Kind->LightColour);
		Lamp->SetAttenuationRadius(E.Kind->LightRadius);
		Lamp->SetIntensity(E.Kind->LightIntensity * Dark * FMath::Max(0.f, Gutter));
		// A FIRE IS NOT A POINT OF LIGHT, and drawn as one it erases itself.
		//
		// A point light obeys the inverse square all the way in, so a hearth
		// bright enough to light a yard at night is, forty centimetres away,
		// bright enough to blow the ring of stones around it to pure white.
		// The fire came out as a white blob with grass round it and the
		// hearth it was built in was not visible at all -- which was read as
		// the flame being too hot and was not: it was the lamp, at point
		// blank, on its own fireplace.
		//
		// A source radius says the light comes off a BALL of burning gas about
		// the size of the fire rather than out of a mathematical point. Inside
		// that radius the falloff flattens, so the stones and the logs are lit
		// instead of obliterated, and nothing changes at any distance where
		// the fire is actually being looked at. It is also simply true, which
		// is usually the sign of the right knob.
		Lamp->SetSourceRadius(FMath::Max(12.f, E.Kind->LightHeight * 0.75f));
		Lamp->SetSoftSourceRadius(FMath::Max(18.f, E.Kind->LightHeight * 1.30f));
		// AND HOW MUCH OF IT HANGS IN THE AIR. From four hundred metres up a
		// hearth's light on the ground is a few pixels; the glow it puts into
		// the air around itself is a soft disc several times the size, and it
		// is most of what a lit village looks like from here. It costs nothing
		// extra -- the volumetric fog is already being computed for the sun.
		Lamp->SetVolumetricScatteringIntensity(
			Chosen ? FMath::Max(0.f, Chosen->FireHaze) : 1.f);
	}

	// ---- AND THE SMOKE OFF THEM ----
	//
	// The same fires, sorted the same way, on the same budget -- but a
	// different question. A light is what a fire is after dark; smoke is what
	// it is by day, and from this camera it is the more visible of the two.
	// So this loop asks whether the kind smokes, not whether it is night.
	while (Smokes.Num() < Want)
	{
		UNiagaraComponent* Column = NewObject<UNiagaraComponent>(this);
		Column->SetupAttachment(RootComponent);
		Column->SetMobility(EComponentMobility::Movable);
		// NOT AUTO-ACTIVATE AND NOT AUTO-DESTROY. These components are a pool:
		// they are re-aimed at whichever fires are nearest as the citizen
		// walks, so one destroying itself when its column runs dry would take
		// a slot out of the pool for good.
		Column->SetAutoActivate(false);
		Column->SetAutoDestroy(false);
		Column->SetCastShadow(false);
		Column->RegisterComponent();
		Smokes.Add(Column);
	}

	// HOW HARD IT IS BLOWING, READ RATHER THAN RECKONED.
	//
	// The hour already worked this out from the world's own overcast and rain
	// and wrote it on the collection every material reads. Reading it back off
	// the same collection is the only arrangement in which the smoke and the
	// meadow are GUARANTEED to agree -- a second copy of the arithmetic here
	// would agree until one of them was edited.
	if (!Weathers)
	{
		Weathers = LoadObject<UMaterialParameterCollection>(
			nullptr, TEXT("/Game/Interval/MPC_IntervalSky.MPC_IntervalSky"));
	}
	const float Blow = Weathers
		? UKismetMaterialLibrary::GetScalarParameterValue(this, Weathers, TEXT("Gale"))
		: 0.34f;
	// The prevailing direction is written down once, in wind.hlsl, and the
	// same two numbers are repeated here: one island, one wind. Smoke takes
	// far more of it than a stem does, because a stem is rooted and a puff
	// weighs nothing -- a column that leans a few degrees in a rising gale is
	// a chimney in still air with extra steps.
	const FVector Gust = FVector(0.82f, 0.57f, 0.f).GetSafeNormal()
		* (90.f + 470.f * FMath::Clamp(Blow, 0.f, 1.f));

	for (int32 i = 0; i < Smokes.Num(); ++i)
	{
		UNiagaraComponent* Column = Smokes[i];
		if (!Column) { continue; }
		const FIntervalPropKind* Kind = (i < Want) ? Embers[i].Kind : nullptr;
		// A HARD POINTER, like every other asset in the look. The look asset is
		// deliberately the one thing that holds the world's art loaded; a soft
		// pointer here would be the only exception and it is not worth being
		// one -- it also does not survive the look asset being written from
		// JSON, which is how every row in it is set.
		UNiagaraSystem* Plume = Kind ? Kind->Smoke.Get() : nullptr;
		if (!Plume || (Kind->bSmokeAtNightOnly && Night <= 0.02f))
		{
			if (Column->IsActive()) { Column->Deactivate(); }
			Column->SetVisibility(false);
			continue;
		}
		const FEmber& E = Embers[i];
		if (Column->GetAsset() != Plume)
		{
			Column->SetAsset(Plume);
		}
		// WHERE THE ROOF ACTUALLY IS OVER THIS FIRE, if a chunk holds it. A
		// flat number was standing in for this and it is only right for a
		// cottage -- over a hall the smoke started five metres below the
		// ridge, inside the thatch.
		const float Ridge = Ground ? Ground->RoofTopAtTile(E.Tile.X, E.Tile.Y)
			: AIntervalGround::NoRoof;
		// WHERE THE SMOKE LEAVES. Outdoors, just above the flame. Under a roof
		// it has to appear above the RIDGE instead, or a hall is a room slowly
		// filling with its own smoke and the village looks like it is not on
		// fire only because the roof hides it. That the tile is roofed is this
		// window's own fact -- it built the roof -- and not something the world
		// ever said.
		FVector At = E.At;
		// NOT `Ridge > 0.f`: a roof over ground four metres below sea level
		// reports a negative height and is still a roof. See NoRoof.
		// AND NOT WHILE THE ROOF IS LIFTED. The window takes the roof off the
		// building the citizen is walking into, and the stack goes with it, so
		// smoke leaving where the flue used to end is smoke pouring out of
		// nothing. Indoors it then rises off the fire like any other fire.
		const bool bRoofed = Ridge > AIntervalGround::NoRoof * 0.5f
			&& Ground && Ground->RoofShownAtTile(E.Tile.X, E.Tile.Y);
		if (E.bIndoors && bRoofed && Chosen && Chosen->ChimneyMesh)
		{
			// OUT OF THE CHIMNEY'S MOUTH. The stack is built below on the same
			// number, so the smoke leaves exactly where the flue ends rather
			// than near it.
			At.Z = Ridge + Chosen->ChimneyRise + Chosen->ChimneyCapHigh * 0.5f;
		}
		else
		{
			At.Z += E.bIndoors ? Kind->SmokeHeightRoofed : Kind->SmokeHeight;
		}
		Column->SetWorldLocation(At);
		Column->SetWorldScale3D(FVector(FMath::Max(0.01f, Kind->SmokeScale)));
		Column->SetVisibility(true);
		Column->SetVariableVec3(TEXT("Wind"), Gust);
		if (!Column->IsActive())
		{
			Column->Activate();
		}
	}

	// ---- AND WHAT THEY SOUND LIKE ----
	//
	// The same fires again, and the one sound in a settlement that comes from
	// somewhere rather than being the air itself. Spatialised, and attenuated
	// per kind: a forge carries further than a cook fire because a forge is
	// louder, not because it is nearer.
	while (Crackles.Num() < Want)
	{
		UAudioComponent* Voice = NewObject<UAudioComponent>(this);
		Voice->SetupAttachment(RootComponent);
		Voice->SetMobility(EComponentMobility::Movable);
		Voice->bAutoActivate = false;
		Voice->bAllowSpatialization = true;
		// ITS OWN ATTENUATION, not an asset. A settings asset is one more
		// thing that can go missing between a rebuild and a level; these are
		// three numbers and they belong to the kind that is burning.
		Voice->bOverrideAttenuation = true;
		Voice->RegisterComponent();
		Crackles.Add(Voice);
	}

	// ---- THE CHIMNEYS ----
	//
	// One stack per roofed fire, standing on the roof over the hearth. The
	// world said a fire burns on that tile and the window worked out that the
	// tile is roofed and how high the roof is over it; the only opinion here is
	// what a flue looks like.
	const bool bStacks = Chosen && Chosen->ChimneyMesh && Chosen->ChimneyMaterial;
	if (bStacks)
	{
		auto Grow = [&](TArray<TObjectPtr<UStaticMeshComponent>>& Pool)
		{
			while (Pool.Num() < Want)
			{
				UStaticMeshComponent* Piece = NewObject<UStaticMeshComponent>(this);
				Piece->SetupAttachment(RootComponent);
				Piece->SetMobility(EComponentMobility::Movable);
				Piece->SetCollisionEnabled(ECollisionEnabled::NoCollision);
				Piece->SetStaticMesh(Chosen->ChimneyMesh);
				Piece->SetMaterial(0, Chosen->ChimneyMaterial);
				Piece->RegisterComponent();
				Pool.Add(Piece);
			}
		};
		Grow(Stacks);
		Grow(Caps);
	}

	for (int32 i = 0; i < Stacks.Num(); ++i)
	{
		UStaticMeshComponent* Stack = Stacks[i];
		UStaticMeshComponent* Cap = (i < Caps.Num()) ? Caps[i] : nullptr;
		const FEmber* E = (i < Want) ? &Embers[i] : nullptr;
		// ---- A CHIMNEY GOES WHEN ITS ROOF GOES ----
		//
		// `RoofShownAtTile` rather than `RoofTopAtTile`, because the roof lift
		// does not change the world's data: the house is still roofed, the
		// citizen inside is still indoors and still wants their lamp. It is
		// only not DRAWN. The stack was asking the first question and standing
		// on the answer, so walking up to any house left its flue hanging in
		// mid air over an open shell. Photographed from the window in Anchor.
		const bool bShown = E && Ground && Ground->RoofShownAtTile(E->Tile.X, E->Tile.Y);
		const float Ridge = (E && E->bIndoors && Ground && bShown)
			? Ground->RoofTopAtTile(E->Tile.X, E->Tile.Y) : AIntervalGround::NoRoof;
		if (!Stack || !E || Ridge <= AIntervalGround::NoRoof * 0.5f)
		{
			if (Stack) { Stack->SetVisibility(false); }
			if (Cap) { Cap->SetVisibility(false); }
			continue;
		}
		// THE ENGINE CUBE IS A METRE, so a scale is a size in metres. The base
		// is sunk well below the roof surface: a stack that starts exactly at
		// the thatch shows daylight under itself wherever the slope runs away
		// from the tile centre.
		const float W = FMath::Max(10.f, Chosen->ChimneyWidth);
		const float Rise = FMath::Max(20.f, Chosen->ChimneyRise);
		const float Sunk = 110.f;
		const float Base = Ridge - Sunk;
		const float Top = Ridge + Rise;
		Stack->SetWorldLocation(FVector(E->At.X, E->At.Y, (Base + Top) * 0.5f));
		Stack->SetWorldScale3D(FVector(W / 100.f, W / 100.f, (Top - Base) / 100.f));
		Stack->SetVisibility(true);
		if (Cap)
		{
			const float CW = W + 2.f * FMath::Max(0.f, Chosen->ChimneyCapOut);
			const float CH = FMath::Max(4.f, Chosen->ChimneyCapHigh);
			Cap->SetWorldLocation(FVector(E->At.X, E->At.Y, Top + CH * 0.5f));
			Cap->SetWorldScale3D(FVector(CW / 100.f, CW / 100.f, CH / 100.f));
			Cap->SetVisibility(true);
		}
	}

	for (int32 i = 0; i < Crackles.Num(); ++i)
	{
		UAudioComponent* Voice = Crackles[i];
		if (!Voice) { continue; }
		const FIntervalPropKind* Kind = (i < Want) ? Embers[i].Kind : nullptr;
		USoundBase* Crackle = Kind ? Kind->Burning.Get() : nullptr;
		if (!Crackle)
		{
			if (Voice->IsPlaying()) { Voice->Stop(); }
			continue;
		}
		Voice->SetWorldLocation(Embers[i].At);
		FSoundAttenuationSettings& Reach = Voice->AttenuationOverrides;
		Reach.bAttenuate = true;
		Reach.bSpatialize = true;
		Reach.AttenuationShape = EAttenuationShape::Sphere;
		Reach.DistanceAlgorithm = EAttenuationDistanceModel::NaturalSound;
		// The radius inside which it is at full voice -- a fire does not get
		// louder as you put your face in it.
		Reach.AttenuationShapeExtents = FVector(140.f, 0.f, 0.f);
		Reach.FalloffDistance = FMath::Max(100.f, Kind->BurningHeard);
		if (Voice->Sound != Crackle)
		{
			Voice->SetSound(Crackle);
			Voice->Stop();
		}
		Voice->SetVolumeMultiplier(FMath::Max(0.f, Kind->BurningVolume));
		if (!Voice->IsPlaying())
		{
			// EACH ONE STARTED AT ITS OWN POINT IN THE LOOP. Fourteen copies
			// of a nine-second crackle all started together is not fourteen
			// fires, it is one fire played loudly -- the pops line up and the
			// whole village ticks in unison.
			Voice->Play(static_cast<float>(Embers[i].Seed % 8971u) * 0.001f);
		}
	}
}

// ---------------------------------------------------------------------------
// THE WALLS THE WORLD SAYS ARE THERE.
//
// `palisade` is the world's own word, and the world is precise about it: eight
// hundred and forty-two tiles across this founding, a hundred and eighty-six
// of them ringing Anchor. The GAPS in that ring are the gates -- the world
// simply leaves tiles out and stands a `guard` in each opening -- so nothing
// here invents a gateway or has to work out where one belongs.
//
// The word was already being drawn, as a scaled cube, which is a garden wall.
// What this adds is the BUILDING of it: a curtain with thickness, teeth along
// the top, a tower where the run turns, and a pier where a run stops at a
// gate. All of that is a level's opinion about how to draw a word. None of it
// is an opinion about where a wall is.
void AIntervalStructures::BuildPalisades(const FIntervalFrame& Frame)
{
	const UIntervalLook* Wardrobe = UIntervalLook::Resolve(Look);
	if (!Wardrobe || Wardrobe->Palisades.Num() == 0)
	{
		return;
	}

	// WHICH TILES, and of which word. A tile is claimed by the first entry that
	// names its type, so a founding that grows `wall.stone` needs a row and no
	// build.
	TMap<FIntPoint, FName> Stones;
	uint64 Digest = 1469598103934665603ull;
	for (const TPair<FString, FIntervalEntity>& Pair : Frame.Nodes)
	{
		const FIntervalEntity& Node = Pair.Value;
		// `Kind` here is the frame's `type` -- a palisade carries no sub-kind at
		// all, which is exactly why a sweep of sub-kinds could not see one.
		const FName Word(*Node.Kind);
		if (!Wardrobe->Palisades.Contains(Word)) { continue; }
		Stones.Add(FIntPoint(Node.X, Node.Y), Word);
		Digest = (Digest ^ static_cast<uint64>(Node.X * 73856093 ^ Node.Y * 19349663))
			* 1099511628211ull;
	}
	if (Digest == PalisadeDigest)
	{
		return;   // the same wall as last interval. Masonry is slow to change.
	}
	PalisadeDigest = Digest;

	// READING A DASHED LINE AS A LINE.
	//
	// The told tiles are a line SAMPLED: around Anchor they alternate, one
	// told and the next left out, the whole way round. Taken literally that is
	// a picket of free-standing slabs with seventy holes in it, and it is what
	// the wall looked like from the road. A gap of `CloseGapsUpTo` tiles with
	// stone on both sides is closed; a gap wider than that is left, and that
	// is where the gates are -- the same holes the world already puts a guard
	// and a road through. See the note on the property.
	{
		TArray<TPair<FIntPoint, FName>> Bridged;
		for (const TPair<FIntPoint, FName>& Stone : Stones)
		{
			const FIntervalPalisade& K = Wardrobe->Palisades.FindChecked(Stone.Value);
			const int32 Reach = FMath::Clamp(K.CloseGapsUpTo, 0, 4);
			static const FIntPoint Ways[2] = { FIntPoint(1, 0), FIntPoint(0, 1) };
			for (const FIntPoint& Way : Ways)
			{
				for (int32 Span = 1; Span <= Reach; ++Span)
				{
					// Stone on the far side of a hole exactly `Span` wide.
					const FIntPoint Far = Stone.Key + Way * (Span + 1);
					if (!Stones.Contains(Far)) { continue; }
					bool bHollow = true;
					for (int32 i = 1; i <= Span; ++i)
					{
						if (Stones.Contains(Stone.Key + Way * i)) { bHollow = false; break; }
					}
					if (!bHollow) { continue; }
					for (int32 i = 1; i <= Span; ++i)
					{
						Bridged.Add(TPair<FIntPoint, FName>(Stone.Key + Way * i, Stone.Value));
					}
					break;   // the nearest stone across the hole is the one that counts
				}
			}
		}
		for (const TPair<FIntPoint, FName>& Fill : Bridged)
		{
			Stones.Add(Fill.Key, Fill.Value);
		}
	}

	if (!Palisades)
	{
		Palisades = NewObject<UProceduralMeshComponent>(this);
		Palisades->SetupAttachment(RootComponent);
		Palisades->SetMobility(EComponentMobility::Movable);
		Palisades->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Palisades->RegisterComponent();
	}
	if (Stones.Num() == 0)
	{
		Palisades->ClearAllMeshSections();
		return;
	}

	const float TileSize = UIntervalGeometry::GetTileSize();

	// ---- ONE SECTION PER MATERIAL, WHICH IS THE WHOLE POINT OF THE MAP ----
	//
	// This built ONE section for every wall and every boundary work on the
	// island, and then chose its material like this:
	//
	//     for (const TPair<FName, FIntervalPalisade>& Pair : Wardrobe->Palisades)
	//         if (Pair.Value.Material) { SetMaterial(0, ...); break; }
	//
	// -- the FIRST entry a TMap happened to iterate, painted over all of it.
	// So the map looked like a map of materials and was not one. Every word's
	// material was read off the asset, stored, and thrown away, and the whole
	// island took whichever key hashed first.
	//
	// That is why a town's boundary came out as an unbroken run of cottage
	// wall, windows and all: `wall` carries the timber-frame plaster and won
	// the race. It is also why setting the palisade's own material to a plain
	// timber appeared to do nothing, twice. Nothing was reading it. The bug
	// was never in the choice of material; it was that the choice had no
	// effect, and a wrong value and an ignored value look identical from the
	// outside.
	//
	// The bucket is keyed on the MATERIAL and not on the word, so the five
	// words that share plaster still share one section and one draw call.
	struct FRun
	{
		TArray<FVector> Vertices;
		TArray<int32> Triangles;
		TArray<FVector> Normals;
		TArray<FVector2D> UVs;
		TArray<FLinearColor> Colors;
		TArray<FProcMeshTangent> Tangents;
	};
	TArray<UMaterialInterface*> Faces;   // section index -> what paints it
	TArray<FRun> Runs;
	auto RunFor = [&](UMaterialInterface* Face) -> FRun&
	{
		const int32 Had = Faces.IndexOfByKey(Face);
		if (Had != INDEX_NONE) { return Runs[Had]; }
		Faces.Add(Face);
		return Runs.AddDefaulted_GetRef();
	};
	// Set once per tile, before any of that tile's boxes are built. A null
	// here would be a box built into nothing, so the tile loop sets it on the
	// line after it looks the tile's word up and nothing else touches it.
	FRun* Into = nullptr;

	// One box, six flat-shaded faces, like everything else built by hand here.
	// ---- A WALL THAT IS NOT SQUARE TO THE WORLD ----
	//
	// `Box` takes a min and a max corner, so everything it builds is aligned to
	// the world grid. That is right for a run going due north or due east and
	// wrong for everything else, and the generator samples a wall's line into
	// TILES, so a run that goes diagonally arrives here as a staircase. Every
	// step of it saw neighbours on both axes, `bAlongX` won, and each step drew
	// an X-aligned slab whatever direction the wall was actually turning. Two
	// consecutive steps then met only at a corner, and the end faces stood out
	// square to the run: reported from the window as a wall with something
	// sticking out at ninety degrees every few metres.
	//
	// `Slab` is the same six faces built from a FRAME instead -- a centre, a
	// direction along the run and one across it -- so a wall can lie at any
	// angle. `Box` is kept and is now written in terms of it, because towers
	// and gateposts genuinely are square to the world and should stay that way.
	auto Corners = [&](const FVector C[8], float Seed)
	{
		FRun& R = *Into;
		static const int32 Faces[6][4] = {
			{4, 5, 6, 7}, {0, 3, 2, 1}, {0, 1, 5, 4},
			{2, 3, 7, 6}, {1, 2, 6, 5}, {3, 0, 4, 7} };
		for (const int32 (&Face)[4] : Faces)
		{
			const int32 Base = R.Vertices.Num();
			for (int32 i = 0; i < 4; ++i) { R.Vertices.Add(C[Face[i]]); }
			FVector N = FVector::CrossProduct(R.Vertices[Base + 1] - R.Vertices[Base],
				R.Vertices[Base + 3] - R.Vertices[Base]).GetSafeNormal();
			if (N.IsNearlyZero()) { N = FVector::UpVector; }
			for (int32 i = 0; i < 4; ++i)
			{
				R.Normals.Add(N);
				// Metres, so a masonry material courses at a believable size
				// however long the run is.
				R.UVs.Add(FVector2D((R.Vertices[Base + i].X + R.Vertices[Base + i].Y) / 100.f,
								  R.Vertices[Base + i].Z / 100.f));
				// WHITE, PLUS THE SEED. This wrote `(Seed, 0, 0, 1)` -- the
				// tile's own seed in red and zero in the other two, meant as a
				// SIGNAL for the masonry material to weather by. The material
				// does not read it as a signal; it multiplies by it, like
				// every other material here. So every stone of every wall came
				// out with no green and no blue in it at all: black, with a
				// faint red cast that varied per tile, which read as unlit
				// geometry rather than as a wall and is why the walls in a
				// settlement were dark slabs.
				//
				// The seed still travels, in ALPHA, which nothing multiplies
				// by on an opaque material -- so a masonry material can still
				// weather tile by tile if one is ever written, and the stone
				// is the colour of the stone until then.
				R.Colors.Add(FLinearColor(1.f, 1.f, 1.f, Seed));
				R.Tangents.Add(FProcMeshTangent(1.f, 0.f, 0.f));
			}
			R.Triangles.Add(Base); R.Triangles.Add(Base + 1); R.Triangles.Add(Base + 2);
			R.Triangles.Add(Base); R.Triangles.Add(Base + 2); R.Triangles.Add(Base + 3);
		}
	};

	// Square to the world, for the things that genuinely are: towers, piers.
	auto Box = [&](const FVector& Min, const FVector& Max, float Seed)
	{
		const FVector C[8] = {
			{Min.X, Min.Y, Min.Z}, {Max.X, Min.Y, Min.Z},
			{Max.X, Max.Y, Min.Z}, {Min.X, Max.Y, Min.Z},
			{Min.X, Min.Y, Max.Z}, {Max.X, Min.Y, Max.Z},
			{Max.X, Max.Y, Max.Z}, {Min.X, Max.Y, Max.Z} };
		Corners(C, Seed);
	};

	// A length of wall from one point to another, of a given thickness, at
	// whatever angle the two points imply.
	auto Slab = [&](const FVector& From, const FVector& To, float HalfWide,
		float Z0, float Z1, float Seed)
	{
		FVector Along = To - From;
		Along.Z = 0.f;
		if (Along.IsNearlyZero()) { return; }
		Along.Normalize();
		const FVector Across(-Along.Y, Along.X, 0.f);
		const FVector A = From + Across * HalfWide, B = From - Across * HalfWide;
		const FVector D = To + Across * HalfWide, E = To - Across * HalfWide;
		const FVector C[8] = {
			{B.X, B.Y, Z0}, {E.X, E.Y, Z0}, {D.X, D.Y, Z0}, {A.X, A.Y, Z0},
			{B.X, B.Y, Z1}, {E.X, E.Y, Z1}, {D.X, D.Y, Z1}, {A.X, A.Y, Z1} };
		Corners(C, Seed);
	};

	int32 Towers = 0, Posts = 0;
	// ---- WHERE THE TOWERS GO, DECIDED BEFORE ANY ARE BUILT ----
	//
	// A STAIRCASE IS NOT A ROW OF CORNERS.
	//
	// The told tiles are a line SAMPLED, and once the gaps in them are closed a
	// run that goes diagonally comes out as a staircase: every tile of it has a
	// neighbour along X and a neighbour along Y. Asked tile by tile "do I have
	// neighbours on two axes", every one of them answers yes, and eight hundred
	// and eighty-two wall tiles produced a hundred and seventy-three towers --
	// one every five tiles, in clumps of four and five leaning on each other.
	// From the shore it looked like a stack of drums somebody had abandoned.
	//
	// There is no local test that tells a staircase from a corner, because
	// locally they are the same shape. What tells them apart is SPACING: a
	// curtain wall has a tower now and then, and whatever the tile-by-tile rule
	// thinks, two towers three tiles apart are one tower drawn twice. So the
	// candidates are gathered first and then thinned, greedily, in a fixed
	// order so the same wall thins the same way every interval and a tower does
	// not wander when a tile is added at the far end of the island.
	TSet<FIntPoint> Towered;
	{
		TArray<FIntPoint> Wants;
		for (const TPair<FIntPoint, FName>& Stone : Stones)
		{
			const FIntPoint At = Stone.Key;
			const bool bW = Stones.Contains(FIntPoint(At.X - 1, At.Y));
			const bool bE = Stones.Contains(FIntPoint(At.X + 1, At.Y));
			const bool bN = Stones.Contains(FIntPoint(At.X, At.Y - 1));
			const bool bS = Stones.Contains(FIntPoint(At.X, At.Y + 1));
			const int32 Near = (bW ? 1 : 0) + (bE ? 1 : 0) + (bN ? 1 : 0) + (bS ? 1 : 0);
			// Exactly two neighbours, one on each axis, is a turn. Three or
			// four is the inside of a mass and wants plain wall. None at all is
			// a stone standing on its own, which IS a tower.
			if ((Near == 2 && (bW || bE) && (bN || bS)) || Near == 0)
			{
				Wants.Add(At);
			}
		}
		Wants.Sort([](const FIntPoint& A, const FIntPoint& B)
			{ return A.X != B.X ? A.X < B.X : A.Y < B.Y; });
		const FIntervalPalisade& Any = Wardrobe->Palisades.FindChecked(Stones.begin()->Value);
		const int32 Apart = FMath::Max(3, Any.TowerEvery);
		for (const FIntPoint& Want : Wants)
		{
			bool bCrowded = false;
			for (const FIntPoint& Had : Towered)
			{
				if (FMath::Abs(Had.X - Want.X) < Apart && FMath::Abs(Had.Y - Want.Y) < Apart)
				{
					bCrowded = true;
					break;
				}
			}
			if (!bCrowded)
			{
				Towered.Add(Want);
			}
		}
	}

	for (const TPair<FIntPoint, FName>& Stone : Stones)
	{
		const FIntPoint At = Stone.Key;
		const FIntervalPalisade& K = Wardrobe->Palisades.FindChecked(Stone.Value);
		// This tile's word decides what paints it, and every box built below
		// goes into that word's bucket.
		Into = &RunFor(K.Material.Get());

		const bool bW = Stones.Contains(FIntPoint(At.X - 1, At.Y));
		const bool bE = Stones.Contains(FIntPoint(At.X + 1, At.Y));
		const bool bN = Stones.Contains(FIntPoint(At.X, At.Y - 1));
		const bool bS = Stones.Contains(FIntPoint(At.X, At.Y + 1));
		const int32 Neighbours = (bW ? 1 : 0) + (bE ? 1 : 0) + (bN ? 1 : 0) + (bS ? 1 : 0);
		const bool bAlongX = bW || bE;
		const bool bAlongY = bN || bS;

		// The tile's own number, so no two courses weather alike.
		const uint32 Hashed = static_cast<uint32>(At.X * 73856093) ^ static_cast<uint32>(At.Y * 19349663);
		const float Seed = static_cast<float>(Hashed % 1000u) / 1000.f;

		const FVector Centre = UIntervalGeometry::TileToWorld(At.X, At.Y);
		const float Half = K.Thickness * 0.5f;
		const float HalfTile = TileSize * 0.5f;

		// Worked out above, for the whole wall at once: a turn that is far
		// enough from the last turn to be worth a tower of its own.
		const bool bCorner = Towered.Contains(At);
		const bool bSpaced = K.TowerEvery > 0 && Neighbours == 2 && !bCorner
			&& (((At.X + At.Y) % K.TowerEvery) == 0);
		if (bCorner || bSpaced)
		{
			const float Wide = Half + K.TowerWiden;
			Box(Centre - FVector(Wide, Wide, 0.f),
				Centre + FVector(Wide, Wide, K.Height + K.TowerRise), Seed);
			++Towers;
			continue;
		}

		// A PIER WHERE THE RUN STOPS. One neighbour means this is the last
		// stone before a gap, and a gap is a gateway: it wants a gatepost, not
		// a wall sawn off.
		if (Neighbours == 1)
		{
			const float Wide = Half + K.GatepostWiden;
			Box(Centre - FVector(Wide, Wide, 0.f),
				Centre + FVector(Wide, Wide, K.Height + K.GatepostRise), Seed);
			++Posts;
			continue;
		}

		// ---- THE CURTAIN, WHICH GOES WHERE THE WALL GOES ----
		//
		// This used to pick ONE axis -- `bAlongX ? X : Y` -- and lay a slab
		// along it. On a straight run that is right. On a turn, and on every
		// step of the staircase a diagonal run arrives as, it is not: such a
		// tile has neighbours on both axes, X won every time, and the slab was
		// laid across the run rather than along it. Consecutive steps then
		// touched only at a corner and each one's end face stood square to the
		// wall, which is the thing reported from the window as sticking out at
		// ninety degrees.
		//
		// A stone is now joined to the neighbours it actually has. The wall
		// runs from the midpoint of the gap to one neighbour, through this
		// tile, to the midpoint of the gap to the next: a straight run comes
		// out exactly as before, a turn comes out as a chamfer across the
		// corner, and a junction of three or four gets an arm to each. Because
		// every arm ends halfway to its neighbour, and that neighbour's arm
		// ends at the same point, the courses still meet with no seam.
		const FIntPoint Sides[4] = {
			FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1) };
		const bool Has[4] = { bW, bE, bN, bS };
		TArray<FVector, TInlineAllocator<4>> Ends;
		for (int32 i = 0; i < 4; ++i)
		{
			if (Has[i])
			{
				Ends.Add(Centre + FVector(Sides[i].X, Sides[i].Y, 0.f) * HalfTile);
			}
		}
		// One COURSE of the wall, at a height and a thickness: through the tile
		// when there are two ways out of it, and an arm to each when there are
		// more. The curtain, its coping and its footing are the same shape at
		// three thicknesses, so they are drawn by the same few lines and cannot
		// drift apart.
		auto Course = [&](float HalfWide, float Z0, float Z1)
		{
			if (Ends.Num() == 2)
			{
				Slab(Ends[0], Ends[1], HalfWide, Z0, Z1, Seed);
			}
			else
			{
				for (const FVector& End : Ends)
				{
					Slab(Centre, End, HalfWide, Z0, Z1, Seed);
				}
			}
		};
		Course(Half, 0.f, K.Height);

		// AND THE DIRECTION THE WALL ACTUALLY RUNS, for the teeth below. Taken
		// from the two ways out rather than from whichever axis happened to win
		// a boolean: on a turn these differ by forty-five degrees and it is the
		// difference between a merlon that sits on the wall and one that sits
		// across it.
		FVector Along(1.f, 0.f, 0.f), Across(0.f, 1.f, 0.f);
		if (Ends.Num() == 2)
		{
			FVector Dir = Ends[1] - Ends[0];
			Dir.Z = 0.f;
			if (!Dir.IsNearlyZero())
			{
				Dir.Normalize();
				Along = Dir;
				Across = FVector(-Dir.Y, Dir.X, 0.f);
			}
		}
		else if (bAlongY && !bAlongX)
		{
			Along = FVector(0.f, 1.f, 0.f);
			Across = FVector(1.f, 0.f, 0.f);
		}

		// ---- A COPING AND A FOOTING, WHICH IS WHAT STOPS IT BEING CARD ----
		//
		// The curtain above is one flat box, and a flat box seen from a
		// top-down camera is a rectangle with a thin strip on top of it. There
		// is nothing anywhere on it for light to break across, so it reads as
		// a cut-out standing in the grass -- said exactly that way: "why do
		// the walls here look like cardboard".
		//
		// Real masonry answers this with two mouldings, and they are the
		// cheapest detail in architecture: a COPING that oversails the top by
		// an inch or two, and a FOOTING that spreads at the bottom. Each
		// throws a hard shadow line the length of the wall, and those two
		// lines are the whole difference between a solid and a plane. They are
		// one box each, so a wall costs three boxes a tile instead of one.
		//
		// The proportions are taken from the wall's OWN numbers rather than
		// from new settings, because a coping is a fixed fraction of a wall in
		// every tradition that has ever built one -- and because a level that
		// could set them separately could set them wrong.
		const float Cope = FMath::Max(K.Thickness * 0.22f, 9.f);
		const float CopeTall = FMath::Max(K.Height * 0.045f, 8.f);
		Course(Half + Cope, K.Height - CopeTall, K.Height);

		const float Foot = FMath::Max(K.Thickness * 0.28f, 11.f);
		const float FootTall = FMath::Max(K.Height * 0.07f, 12.f);
		Course(Half + Foot, 0.f, FootTall);

		// THE TEETH. Laid out along this tile rather than along the whole run,
		// so a merlon never straddles the mouth of a gate and the pattern
		// starts afresh at every tower.
		const float Pitch = K.MerlonWidth + K.EmbrasureWidth;
		if (Pitch > 1.f && K.MerlonHeight > 0.f)
		{
			const int32 Teeth = FMath::Max(1, FMath::FloorToInt(TileSize / Pitch));
			const float Spare = (TileSize - Teeth * Pitch) * 0.5f;
			for (int32 T = 0; T < Teeth; ++T)
			{
				const float Start = -HalfTile + Spare + T * Pitch;
				Slab(Centre + Along * Start,
					Centre + Along * (Start + K.MerlonWidth), Half,
					K.Height, K.Height + K.MerlonHeight, Seed);
			}
		}
	}

	Palisades->ClearAllMeshSections();
	int32 Built = 0;
	for (int32 i = 0; i < Runs.Num(); ++i)
	{
		FRun& R = Runs[i];
		if (R.Vertices.Num() == 0) { continue; }
		Palisades->CreateMeshSection_LinearColor(i, R.Vertices, R.Triangles, R.Normals,
			R.UVs, R.Colors, R.Tangents, false);
		// A null face is left to the component's default rather than skipped:
		// an unpainted wall is a bug worth seeing, not one worth hiding.
		if (Faces[i]) { Palisades->SetMaterial(i, Faces[i]); }
		Built += R.Vertices.Num();
	}
	UE_LOG(LogTemp, Log, TEXT("[interval] palisades: %d stones, %d towers, %d gateposts, %d vertices in %d section(s)"),
		Stones.Num(), Towers, Posts, Built, Runs.Num());
}

// ---------------------------------------------------------------------------
// THE ONES THAT ARE PEOPLE.
//
// Every other thing this actor draws is an INSTANCE in a pool: one mesh, one
// transform, thousands of them for nothing. A shopkeeper cannot be that. This
// window's people are modular -- a bare body carrying the head and the hands,
// and an outfit over it that stops at the collar -- and they are animated, and
// an instanced static mesh is neither of those things.
//
// So the handful of nodes whose kind names a skeleton get a component each,
// built exactly the way AIntervalCitizens builds a citizen: the first part
// leads and carries the animation, the rest follow its pose bone for bone, and
// the followers hang off the LEADER rather than off this actor so that they
// are not culled the moment the actor's origin leaves the frustum.
bool AIntervalStructures::StandFigure(const FString& Id, const FIntervalPropKind& Kind,
	const FVector& Where, float Yaw, float Scale)
{
	if (!Kind.Skeletal)
	{
		return false;
	}
	FiguresSeen.Add(Id);

	TObjectPtr<USkeletalMeshComponent>* Found = Figures.Find(Id);
	USkeletalMeshComponent* Lead = Found ? Found->Get() : nullptr;
	if (!Lead)
	{
		Lead = NewObject<USkeletalMeshComponent>(this);
		Lead->SetupAttachment(RootComponent);
		Lead->SetMobility(EComponentMobility::Movable);
		Lead->SetSkeletalMesh(Kind.Skeletal.Get());
		Lead->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Lead->SetAnimInstanceClass(UIntervalAnimInstance::StaticClass());
		Lead->SetAnimationMode(EAnimationMode::AnimationBlueprint);
		Lead->RegisterComponent();

		for (const TObjectPtr<USkeletalMesh>& Part : Kind.SkeletalParts)
		{
			if (!Part) { continue; }
			USkeletalMeshComponent* Piece = NewObject<USkeletalMeshComponent>(this);
			Piece->SetupAttachment(Lead);
			Piece->SetMobility(EComponentMobility::Movable);
			Piece->SetSkeletalMesh(Part.Get());
			Piece->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Piece->RegisterComponent();
			Piece->AttachToComponent(Lead, FAttachmentTransformRules::SnapToTargetIncludingScale);
			Piece->SetLeaderPoseComponent(Lead);
			// The leader's bounds decide what is drawn for the whole figure,
			// and an outfit is smaller than the body it hangs on.
			Piece->SetBoundsScale(2.f);
		}

		// ---- AND WHAT THEY WEAR ON A BONE ----
		//
		// A keeper's hat was a `Parts` entry with a WORLD offset: an instanced
		// static mesh dropped at the tile, a hundred and seventy-odd
		// centimetres up, and nothing else. It could not track a head, because
		// it was never attached to one. So it floated over the short, sank
		// into the tall, stayed put when the figure turned, and hung in the
		// air while they walked out from under it. There is a note further up
		// this project that sits the hats back down by arithmetic -- for a
		// 182cm cylinder that no longer exists -- which is the same guess made
		// once more.
		//
		// A bone is not a guess. Anything in `Parts` that names one is hung on
		// it here, exactly as `AIntervalCitizens::Hang` hangs a citizen's
		// gear, and is SKIPPED by the instanced pass below so it is not drawn
		// twice. Parts with no bone -- the brewer's barrel, the smith's anvil,
		// the staff leaning beside a shepherd -- are furniture standing on the
		// ground beside somebody and still belong where they were.
		for (const FIntervalPropPart& Worn : Kind.Parts)
		{
			if (Worn.Bone.IsNone() || !Worn.Mesh) { continue; }
			UStaticMeshComponent* Hung = NewObject<UStaticMeshComponent>(this);
			Hung->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Hung->SetMobility(EComponentMobility::Movable);
			Hung->RegisterComponent();
			Hung->AttachToComponent(Lead,
				FAttachmentTransformRules::SnapToTargetNotIncludingScale, Worn.Bone);
			Hung->SetStaticMesh(Worn.Mesh);
			if (Worn.Material) { Hung->SetMaterial(0, Worn.Material.Get()); }
			Hung->SetRelativeTransform(
				FTransform(Worn.Rotation, Worn.Offset, Worn.Scale));
			Hung->SetCastShadow(Worn.bCastShadow);
		}

		// STANDING, not frozen mid-stride. A keeper who is never told what to do
		// is doing the thing a keeper does, which is stand at their stall.
		if (const UIntervalLook* Wardrobe = UIntervalLook::Resolve(Look))
		{
			if (const FIntervalMotion* Still = Wardrobe->Motions.Find(TEXT("still")))
			{
				if (Still->Anim)
				{
					if (UIntervalAnimInstance* Inst =
						Cast<UIntervalAnimInstance>(Lead->GetAnimInstance()))
					{
						// Off their own id, so a row of keepers is not one
						// keeper breathing in unison.
						Inst->CrossFade(Still->Anim,
							Still->Rate * (0.88f + 0.24f * (IdHash(Id) % 100u) / 100.f),
							true, 0.f,
							(IdHash(Id) % 997u) / 997.f * Still->Anim->GetPlayLength());
					}
				}
			}
		}
		Figures.Add(Id, Lead);
	}

	Lead->SetWorldLocation(Where + FVector(0.f, 0.f, Kind.ZOffset));
	Lead->SetWorldRotation(FRotator(0.f, Yaw, 0.f));
	Lead->SetWorldScale3D(Kind.Scale * Scale);
	Lead->SetVisibility(true);
	return true;
}
