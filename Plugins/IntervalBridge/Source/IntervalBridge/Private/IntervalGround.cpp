#include "IntervalGround.h"
#include "IntervalWings.h"
#include "IntervalSmallLife.h"
#include "IntervalSmallLife.h"
#include "TimerManager.h"
#include "Engine/World.h"
#include "IntervalLook.h"
#include "IntervalSound.h"
#include "IntervalAir.h"
#include "IntervalGate.h"
#include "IntervalHour.h"
#include "EngineUtils.h"

#include "IntervalBridgeSubsystem.h"
#include "IntervalChunk.h"
#include "IntervalGeometry.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"

DEFINE_LOG_CATEGORY_STATIC(LogIntervalGround, Log, All);

AIntervalGround::AIntervalGround()
{
	// IT TICKS NOW, and only to pace the ground. See BuildQueued: a chunk
	// built the instant it arrived cost a six-second frame when several
	// arrived together.
	//
	// AND THIS LINE ALONE IS NOT ENOUGH, which cost the whole island for a
	// while: this actor is PLACED IN THE LEVEL, and a level actor is loaded
	// from what was saved. `bCanEverTick` was serialised as false long before
	// this line existed, the saved value won, Tick never ran, no queued chunk
	// was ever built and the world came up as the inside of the sky with the
	// buildings floating in it. It is forced again in BeginPlay, where it
	// applies to the instance that actually exists.
	PrimaryActorTick.bCanEverTick = true;
}

static bool FindAnySound_Impl(UWorld* World)
{
	TActorIterator<AIntervalSound> It(World);
	return static_cast<bool>(It);
}

const TArray<uint8>& AIntervalGround::ShapeOfTiles() const
{
	// ---- WHAT EACH KIND OF GROUND DOES TO THE LAND UNDER IT ----
	//
	// The landscape is arithmetic on a tile's coordinates, so anything may ask
	// for it; what a chunk cannot work out alone is whether a tile is WATER or
	// a FLOOR, because it holds the world's numeric codes and the words live
	// out here. This turns the words into a table once and hands it over.
	//
	// By NAME and not by number: a founding that adds a tile shifts every code
	// after it, and a table of numbers written by hand would then sink the
	// wrong ground. The world says what it calls things and this believes it.
	static const TSet<FString> Waters = { TEXT("sea"), TEXT("river"), TEXT("fens") };
	static const TSet<FString> Floors = { TEXT("floor"), TEXT("flag") };
	// A DECK IS ITS OWN SHAPE, and `causey` is deliberately not one.
	//
	// The world has two words for a road that crosses wet ground: a BRIDGE,
	// which is carried over the water on stone, and a CAUSEY, which is an
	// embankment heaped up through it. The earth ramp this window drew for
	// both is the wrong answer for the first and very nearly the right one
	// for the second, so only `bridge` is built.
	static const TSet<FString> Decks = { TEXT("bridge") };

	if (Bridge && Shape.Num() != Bridge->GetTileNames().Num())
	{
		const TArray<FString>& Named = Bridge->GetTileNames();
		Shape.Init(AIntervalChunk::ShapeLand, Named.Num());
		for (int32 i = 0; i < Named.Num(); ++i)
		{
			if (Decks.Contains(Named[i]))       { Shape[i] = AIntervalChunk::ShapeDeck; }
			else if (Waters.Contains(Named[i])) { Shape[i] = AIntervalChunk::ShapeWater; }
			else if (Floors.Contains(Named[i])) { Shape[i] = AIntervalChunk::ShapeFloor; }
		}
	}
	return Shape;
}


void AIntervalGround::BeginPlay()
{
	Super::BeginPlay();
	// ---- A TIMER, NOT A TICK ----
	//
	// The ground has to do a little work every frame to pace chunk building,
	// and getting a tick onto THIS actor turned out to be a fight not worth
	// having. It is PLACED IN THE LEVEL, so it loads from what was saved, and
	// `bCanEverTick` was serialised false long before there was a reason for
	// it to be true; the saved value beats the constructor. Setting it in
	// BeginPlay does not help either, because a tick FUNCTION is registered
	// with the level during actor registration, which has already happened --
	// so the flag flips, `SetActorTickEnabled` enables a function that was
	// never registered, and nothing runs. Registering it by hand ran it once
	// and then stopped.
	//
	// The symptom was exact and silent all three times: chunks arrived and
	// queued -- a hundred and twelve of them -- and were never built, so the
	// island came up as the inside of the sky with the buildings floating in
	// it. A looping timer needs none of that machinery and cannot be
	// overridden by what a level saved years ago.
	GetWorldTimerManager().SetTimer(GroundBeat, this,
		&AIntervalGround::BuildQueued, 1.f / 60.f, true);


	// THE GROUND ANNOUNCES ITSELF, so that everything which places a thing on
	// a tile lands on the landscape without being handed a pointer to it. See
	// `UIntervalGeometry::GroundProvider`. A weak pointer, because the level
	// outlives no actor and a stale capture here would be a crash on travel.
	{
		TWeakObjectPtr<const AIntervalGround> Self(this);
		// ---- HOW MUCH OF THE LAND TO DRAW, before anything asks for it ----
		//
		// Read here rather than per tile: it is one number for the whole
		// island and LandAt is called some hundreds of thousands of times
		// building a chunk. See `LandRelief` in IntervalLook.h for why it is
		// a dial at all.
		if (const UIntervalLook* Look = UIntervalLook::Resolve(Look_))
		{
			UIntervalGeometry::Relief() = FMath::Clamp(Look->LandRelief, 0.f, 1.f);
		}
		UIntervalGeometry::GroundProvider() = [Self](int32 X, int32 Y)
		{
			return Self.IsValid() ? Self->GroundHeightAtTile(X, Y)
			                      : UIntervalGeometry::LandAt(X, Y);
		};
		// ---- AND WHERE THE TOWNS ARE ----
		//
		// Ground inside a settlement is graded like the street through it; see
		// the note in UIntervalGeometry::GroundAt. The rects come from the
		// founder by way of `hello`, so this asks the bridge each time rather
		// than caching a list that would be empty for the first few seconds
		// and wrong forever after.
		UIntervalGeometry::TownProvider() = [Self](int32 X, int32 Y) -> float
		{
			if (!Self.IsValid() || !Self->Bridge) { return 0.f; }
			float Most = 0.f;
			for (const FIntervalSettlement& Town : Self->Bridge->GetSettlements())
			{
				// HOW FAR OUTSIDE, in tiles, on the worse axis. Zero inside.
				const int32 OutX = FMath::Max(0,
					FMath::Max(Town.MinX() - X, X - Town.MaxX()));
				const int32 OutY = FMath::Max(0,
					FMath::Max(Town.MinY() - Y, Y - Town.MaxY()));
				const float Out = static_cast<float>(FMath::Max(OutX, OutY));
				// A RING, NOT AN EDGE. Ten tiles of it: a town whose grading
				// stopped dead at its boundary would have a lip round it, and
				// a lip is the very fault this is here to remove. Ten is wider
				// than the eight-tile ripple being flattened, so the ripple
				// comes back gradually rather than all at once.
				const float Weight = 1.f - FMath::Clamp(Out / 10.f, 0.f, 1.f);
				Most = FMath::Max(Most, Weight * Weight * (3.f - 2.f * Weight));
			}
			return Most;
		};
	}

	// THE WINDOW BRINGS ITS OWN VOICE. The sound actor cannot be placed in the
	// level and left there: a level actor is an external-actor package, and
	// nothing here can save one (IntervalLook.h). So it is spawned, like the
	// look is loaded, from a convention rather than from the map.
	if (!FindAnySound_Impl(GetWorld()))
	{
		GetWorld()->SpawnActor<AIntervalSound>();
	}
	{
		TActorIterator<AIntervalAir> It(GetWorld());
		if (!It) { GetWorld()->SpawnActor<AIntervalAir>(); }
	}
	{
		// The gate takes itself down again if there is no player controller,
		// which is every Simulate session and so every photograph.
		TActorIterator<AIntervalGate> It(GetWorld());
		if (!It) { GetWorld()->SpawnActor<AIntervalGate>(); }
	}
	{
		TActorIterator<AIntervalHour> It(GetWorld());
		if (!It) { GetWorld()->SpawnActor<AIntervalHour>(); }
	}
	{
		// BIRDS. Nothing about them is the world's business: no deed makes a
		// flock and none is recorded, which is why they are spawned here with
		// the rest of the window's own furniture rather than drawn off a frame.
		TActorIterator<AIntervalWings> It(GetWorld());
		if (!It) { GetWorld()->SpawnActor<AIntervalWings>(); }
	}
	{
		// AND WHAT IS ON THE GROUND. Scenery, exactly like the birds: no deed
		// makes a frog, none is recorded, and nothing in any frame mentions
		// one. It puts them only where the world's own word for the ground is
		// wet, which is the same rule the crows and the gulls follow.
		TActorIterator<AIntervalSmallLife> It(GetWorld());
		if (!It) { GetWorld()->SpawnActor<AIntervalSmallLife>(); }
	}

	UGameInstance* GameInstance = GetGameInstance();
	Bridge = GameInstance ? GameInstance->GetSubsystem<UIntervalBridgeSubsystem>() : nullptr;
	if (!Bridge)
	{
		UE_LOG(LogIntervalGround, Error, TEXT("no bridge subsystem: is the plugin enabled?"));
		return;
	}

	Bridge->OnFrame.AddDynamic(this, &AIntervalGround::HandleFrame);
	Bridge->OnTerrainChunk.AddDynamic(this, &AIntervalGround::HandleChunk);
	Bridge->OnReady.AddDynamic(this, &AIntervalGround::HandleReady);

	if (!Bridge->GetWorldId().IsEmpty())
	{
		HandleReady();   // the bridge was already up when this level opened
	}
}

void AIntervalGround::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	// AND STOPS ANSWERING WHEN IT GOES. The weak pointer makes a stale call
	// harmless, but leaving a closure bound to a dead level means the next
	// one answers with the bare land until its own ground starts.
	UIntervalGeometry::GroundProvider() = nullptr;
	UIntervalGeometry::TownProvider() = nullptr;

	if (Bridge)
	{
		Bridge->OnFrame.RemoveDynamic(this, &AIntervalGround::HandleFrame);
		Bridge->OnTerrainChunk.RemoveDynamic(this, &AIntervalGround::HandleChunk);
		Bridge->OnReady.RemoveDynamic(this, &AIntervalGround::HandleReady);
	}
	Super::EndPlay(EndPlayReason);
}

void AIntervalGround::HandleReady()
{
	if (!bWholeIsland || !Bridge)
	{
		return;
	}

	// Every chunk the island has. Fine for a screenshot or the chart; not
	// what anyone should play on.
	int32 WorldW = 0, WorldH = 0;
	Bridge->GetWorldSize(WorldW, WorldH);
	const int32 ChunkTiles = UIntervalGeometry::ChunkTiles;
	for (int32 CY = 0; CY * ChunkTiles < WorldH; ++CY)
	{
		for (int32 CX = 0; CX * ChunkTiles < WorldW; ++CX)
		{
			Want(FIntPoint(CX, CY));
		}
	}
}

void AIntervalGround::HandleFrame()
{
	// The frame is READ rather than handed over: a dynamic delegate copies
	// whatever it carries, and what this used to carry was the whole world.
	// See FIntervalFrameEvent in IntervalBridgeSubsystem.h.
	if (!Bridge) { return; }
	const FIntervalFrame& Frame = Bridge->GetFrame();
	if (!Frame.bHasMe)
	{
		return;
	}
	// ---- WHAT IS DRAWN COMES FIRST, AND BEFORE THE STREAMING GUARD ----
	//
	// This used to read `if (bWholeIsland || !Frame.bHasMe) return;`, and the
	// level's own ground actor has `bWholeIsland` SAVED AS TRUE -- a
	// level-placed actor's saved property beats the C++ default, which is the
	// same trap `RainRadius` was moved onto the look asset to escape. So the
	// whole of this function was dead in the only configuration anybody plays
	// in, and the two things below -- lifting the roof off the building the
	// citizen is in, and keeping grass out of a ploughed field -- were written,
	// built, and never once ran. Both were reported as still broken, correctly.
	//
	// Neither has anything to do with whether chunks stream. They are about
	// what a chunk DRAWS, which is a question whether the island arrives in
	// pieces or all at once, so they sit above the guard and the guard keeps
	// only the streaming it was written for.

	// ---- THE ROOF OVER THE CITIZEN COMES OFF ----
	//
	// A town seen from above is roofs. Walk into one and you are under it,
	// with no way to see where you are standing or where the door was, which
	// is why moving about a town has been reported as too hard to navigate.
	//
	// Every chunk is told, because a building may straddle a chunk edge and a
	// terrace under one long roof is ONE building to the builder. The call is
	// an integer compare on all but the one that changed, and the one that
	// changed rebuilds only its own roofs. Nothing happens at all while the
	// citizen is out of doors, which is nearly always.
	{
		// ---- WHAT IS BETWEEN THE EYE AND THE CITIZEN, NOT WHAT THEY STAND IN
		//
		// The first cut of this hid the building the citizen was INSIDE, which
		// is the obvious rule and is not the one that matters. Walking into a
		// town, what stops you seeing your own character is almost never the
		// roof over their head: it is the roofs and walls of the houses between
		// them and the camera, which that rule does not touch at all. Measured
		// by walking into Millbrook with it on: the screen was still three
		// quarters roof and the citizen was a name label with nothing under it.
		//
		// So the rule is occlusion. March the ground line from the citizen to
		// the lens, a tile at a time, and take every building it crosses. For a
		// camera looking down at a citizen that footprint IS what blocks the
		// view, and it costs a few dozen lookups.
		TSet<int64> Hide;
		if (const int64 Inside = BuildingKeyAtTile(Frame.Me.X, Frame.Me.Y))
		{
			Hide.Add(Inside);
		}
		if (const UWorld* W = GetWorld())
		{
			if (const APlayerController* PC = W->GetFirstPlayerController())
			{
				if (PC->PlayerCameraManager)
				{
					const FVector Lens = PC->PlayerCameraManager->GetCameraLocation();
					int32 Ex = 0, Ey = 0;
					UIntervalGeometry::WorldToTile(Lens, Ex, Ey);
					const int32 Dx = Ex - Frame.Me.X, Dy = Ey - Frame.Me.Y;
					// Capped: a controller that answers with the world origin
					// would otherwise march the width of the island.
					const int32 Steps = FMath::Min(
						FMath::Max(FMath::Abs(Dx), FMath::Abs(Dy)), 48);
					for (int32 i = 1; i <= Steps; ++i)
					{
						const float T = static_cast<float>(i) / static_cast<float>(Steps);
						const int32 Tx = Frame.Me.X + FMath::RoundToInt(Dx * T);
						const int32 Ty = Frame.Me.Y + FMath::RoundToInt(Dy * T);
						if (const int64 Key = BuildingKeyAtTile(Tx, Ty))
						{
							Hide.Add(Key);
						}
					}
				}
			}
		}
		// KEPT, so that anything standing ON a roof can ask whether that roof
		// is still being drawn. The chimneys ask; see RoofShownAtTile.
		Hidden = Hide;
		for (const TPair<FIntPoint, TObjectPtr<AIntervalChunk>>& Pair : Live)
		{
			if (AIntervalChunk* Chunk = Pair.Value.Get())
			{
				Chunk->SetHideBuildings(TSet<int64>(Hide));
			}
		}
	}

	// ---- AND WHICH GROUND HAS BEEN PLOUGHED ----
	//
	// The scatter is laid by the chunk off the ground's own code; a plot is a
	// node in the frame. Neither knew about the other, so wild grass grew up
	// through the furrows of every field on the island. Ploughed ground is
	// bare, which is the entire point of ploughing it.
	//
	// Gathered once and handed to every chunk, which keeps only the tiles that
	// fall inside it and does nothing at all unless the set changed.
	{
		static const TSet<FName> Worked = {
			FName(TEXT("plot")), FName(TEXT("grove-plot")),
			FName(TEXT("landmark.flowerbed")),
		};
		// A BED IS WIDER THAN ITS TILE. The plot's own bed is 3.92 m across and
		// a tile is 2, so it reaches 96 cm into the tile either side of the one
		// the node stands on. Marking only the node's tile left grass growing
		// through the outer third of every bed on the island, which is what the
		// first attempt at this looked like: better, and still wrong.
		TSet<FIntPoint> Ploughed;
		for (const TPair<FString, FIntervalEntity>& Node : Frame.Nodes)
		{
			if (!Worked.Contains(FName(*Node.Value.Kind)))
			{
				continue;
			}
			Ploughed.Add(FIntPoint(Node.Value.X, Node.Value.Y));
			Ploughed.Add(FIntPoint(Node.Value.X - 1, Node.Value.Y));
			Ploughed.Add(FIntPoint(Node.Value.X + 1, Node.Value.Y));
		}
		for (const TPair<FIntPoint, TObjectPtr<AIntervalChunk>>& Pair : Live)
		{
			if (AIntervalChunk* Chunk = Pair.Value.Get())
			{
				Chunk->SetTilled(TSet<FIntPoint>(Ploughed));
			}
		}
	}

	// AND NOW THE STREAMING, which an island built in one piece does not need.
	if (bWholeIsland)
	{
		return;
	}

	const FIntPoint Centre = UIntervalGeometry::ChunkOf(Frame.Me.X, Frame.Me.Y);
	if (Centre == LastCentre)
	{
		// A CITIZEN WHO HAS NOT CROSSED A CHUNK EDGE NEEDS NOTHING -- unless
		// ground they are standing on never arrived.
		//
		// This returned unconditionally, so the only moment a stranded chunk
		// could be asked for again was the moment a citizen crossed into a new
		// chunk. Somebody standing in a hole would stand in it for ever, and
		// the hole is the whole sky: no ground, no scatter, no roads, just the
		// inside of the sky sphere. Found exactly that way -- a citizen at
		// 632,314 with not one chunk actor alive anywhere in the world.
		const double Since = FPlatformTime::Seconds();
		bool bStale = false;
		for (const TPair<FIntPoint, double>& Ask : Pending)
		{
			if (Since - Ask.Value >= ChunkPatience) { bStale = true; break; }
		}
		if (!bStale)
		{
			return;
		}
	}
	LastCentre = Centre;

	for (int32 DY = -Rings; DY <= Rings; ++DY)
	{
		for (int32 DX = -Rings; DX <= Rings; ++DX)
		{
			Want(FIntPoint(Centre.X + DX, Centre.Y + DY));
		}
	}
	ReleaseFarChunks(Centre);
}

void AIntervalGround::Want(const FIntPoint& Chunk)
{
	if (Chunk.X < 0 || Chunk.Y < 0 || Live.Contains(Chunk) || !Bridge)
	{
		return;
	}
	// ASKED ALREADY -- BUT NOT FOR EVER.
	//
	// A chunk still waiting for its answer is not asked again, or a citizen
	// walking along a chunk edge would ask five times a second. It used to be
	// asked again NEVER, and that is what emptied the south-east of the island:
	// a reply that does not arrive -- the bridge restarted with requests in
	// flight, which happened a dozen times in one session -- stranded that
	// ground for the life of the play session. The chunk was never requested
	// again, never built, and the window drew the inside of the sky sphere
	// where the country should have been.
	const double Now = FPlatformTime::Seconds();
	if (const double* AskedAt = Pending.Find(Chunk))
	{
		if (Now - *AskedAt < ChunkPatience)
		{
			return;
		}
		UE_LOG(LogIntervalGround, Warning,
			TEXT("chunk %d,%d went unanswered for %.1fs, asking again"),
			Chunk.X, Chunk.Y, Now - *AskedAt);
	}

	int32 WorldW = 0, WorldH = 0;
	Bridge->GetWorldSize(WorldW, WorldH);
	const int32 ChunkTiles = UIntervalGeometry::ChunkTiles;
	const int32 X0 = Chunk.X * ChunkTiles;
	const int32 Y0 = Chunk.Y * ChunkTiles;
	if (WorldW > 0 && (X0 >= WorldW || Y0 >= WorldH))
	{
		return;   // off the edge of the world; the sea is drawn, not streamed
	}

	// Clip the last chunk to the island rather than asking for tiles that do
	// not exist. The mirror would answer for them -- it is a pure function of
	// coordinates -- but they are not part of this world and drawing them
	// would put ground where the map ends.
	const int32 W = WorldW > 0 ? FMath::Min(ChunkTiles, WorldW - X0) : ChunkTiles;
	const int32 H = WorldH > 0 ? FMath::Min(ChunkTiles, WorldH - Y0) : ChunkTiles;

	Pending.Add(Chunk, Now);
	// One tile of border, read and never drawn: it is what lets this chunk's
	// vertices and eaves agree with the chunk next door.
	// FOUR tiles of border, not one. Relief needs to see one tile past the
	// edge; a ROOF needs to see the whole building, because its ridge is the
	// long axis of a footprint that may begin in the chunk next door. Four
	// covers every house on the island and costs 5184 bytes a plane instead
	// of 4096 -- terrainChunk is a pure function of coordinates, so a wider
	// border is only ever bytes.
	Bridge->RequestTerrain(X0, Y0, W, H, 4);
}

void AIntervalGround::ResolveScatter()
{
	// The tables come from the look asset when there is one; see IntervalLook.h
	// for why they cannot simply live on this actor.
	const UIntervalLook* Look = UIntervalLook::Resolve(Look_);
	const TMap<FName, FIntervalScatterKind>& ScatterTable =
		(Look && Look->Scatter.Num() > 0) ? Look->Scatter : Scatter;
	const TMap<FName, FIntervalRoofKind>& RoofTable =
		(Look && Look->Roofs.Num() > 0) ? Look->Roofs : Roofs;

	// The level keys its scatter by the world's own word; a chunk arrives
	// carrying codes. The list that maps one to the other is built by the
	// bridge at runtime and GROWS -- this founding appended three terrains
	// mid-session -- so the lookup is rebuilt from the current list every time
	// ground arrives, and a code past the end of it simply grows nothing.
	ScatterByCode.Reset();
	RoofByCode.Reset();
	ThresholdByCode.Reset();
	// WHAT GROWS ON THE SPINE, under a word that is not a terrain.
	//
	// The ridge has no ground of its own -- its tiles are ordinary `crags` --
	// so it cannot be looked up by code like everything else here. It takes a
	// reserved key in the same table instead, which keeps it a LEVEL's opinion
	// about how a ridge looks rather than a second table to keep in step. A
	// level that names nothing leaves the spine planted like the ground under
	// it, which is what this window did before it was told where the ridge was.
	SpineScatter = FIntervalScatterKind();
	if (const FIntervalScatterKind* Rock = ScatterTable.Find(FName(TEXT("ridge"))))
	{
		SpineScatter = *Rock;
	}
	if (!Bridge)
	{
		return;
	}
	const TArray<FString>& Names = Bridge->GetTileNames();
	ScatterByCode.SetNum(Names.Num());
	RoofByCode.SetNum(Names.Num());
	ThresholdByCode.SetNumZeroed(Names.Num());
	for (int32 Index = 0; Index < Names.Num(); ++Index)
	{
		if (const FIntervalScatterKind* Found = ScatterTable.Find(FName(*Names[Index])))
		{
			ScatterByCode[Index] = *Found;
		}
		ThresholdByCode[Index] = Look && Look->Thresholds.Contains(FName(*Names[Index])) ? 1 : 0;
		if (const FIntervalRoofKind* Roof = RoofTable.Find(FName(*Names[Index])))
		{
			RoofByCode[Index] = *Roof;
		}
	}
}

void AIntervalGround::HandleChunk(const FIntervalTerrainChunk& Chunk)
{
	// ---- ARRIVING IS NOT BUILDING ----
	//
	// This built the whole chunk right here, in the socket handler, the
	// instant the bytes landed. One chunk is a procedural mesh, a control
	// texture, every scatter instance, every roof and every floor in it --
	// and chunks do not arrive one at a time. Crossing a chunk edge asks for
	// a rank of them and they come back together, so the work landed in a
	// single frame: the frame timer caught one at SIX SECONDS.
	//
	// From the chair that is a window that stops dead when you walk, which is
	// how it was reported: "walking is extremely buggy... it really
	// struggles". So the chunk is kept and the tick builds it against a
	// budget, nearest first.
	const FIntPoint Key = UIntervalGeometry::ChunkOf(Chunk.X0, Chunk.Y0);
	Pending.Remove(Key);
	// A CHUNK THAT ARRIVES TWICE REPLACES ITSELF. The bridge re-sends ground
	// that has changed, and building the old one after the new one would draw
	// yesterday's world.
	for (FIntervalTerrainChunk& Waiting : Queued)
	{
		if (UIntervalGeometry::ChunkOf(Waiting.X0, Waiting.Y0) == Key)
		{
			Waiting = Chunk;
			return;
		}
	}
	Queued.Add(Chunk);
}

void AIntervalGround::BuildQueued()
{
	if (Queued.Num() == 0)
	{
		return;
	}
	// NEAREST FIRST, because the ground a citizen is standing on matters more
	// than the ground at the edge of sight, and because the one case that
	// must never be slow is walking into country that has not arrived.
	const FIntPoint Centre = LastCentre;
	Queued.Sort([&Centre](const FIntervalTerrainChunk& A, const FIntervalTerrainChunk& B)
	{
		const FIntPoint Ka = UIntervalGeometry::ChunkOf(A.X0, A.Y0);
		const FIntPoint Kb = UIntervalGeometry::ChunkOf(B.X0, B.Y0);
		const int32 Da = FMath::Abs(Ka.X - Centre.X) + FMath::Abs(Ka.Y - Centre.Y);
		const int32 Db = FMath::Abs(Kb.X - Centre.X) + FMath::Abs(Kb.Y - Centre.Y);
		return Da < Db;
	});

	const double Began = FPlatformTime::Seconds();
	const double Budget = static_cast<double>(FMath::Max(1.f, BuildBudgetMs)) / 1000.0;
	while (Queued.Num() > 0)
	{
		// THE BUDGET IS CHECKED BEFORE A CHUNK, NOT DURING ONE. A half-built
		// chunk is a hole in the world, so this never stops in the middle of
		// one; it declines to START another once the budget is spent. The
		// first one of a frame therefore always goes through, which is what
		// makes a citizen walking into new country see ground rather than sky.
		const FIntervalTerrainChunk Next = Queued[0];
		Queued.RemoveAt(0);
		RaiseChunk(Next);
		if (FPlatformTime::Seconds() - Began >= Budget)
		{
			break;
		}
	}
}

void AIntervalGround::RaiseChunk(const FIntervalTerrainChunk& Chunk)
{
	if (ScatterByCode.Num() == 0 || (Bridge && ScatterByCode.Num() != Bridge->GetTileNames().Num()))
	{
		ResolveScatter();
	}

	const FIntPoint Key = UIntervalGeometry::ChunkOf(Chunk.X0, Chunk.Y0);

	TObjectPtr<AIntervalChunk>* Existing = Live.Find(Key);
	AIntervalChunk* Actor = Existing ? Existing->Get() : nullptr;

	if (!Actor)
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		Actor = GetWorld()->SpawnActor<AIntervalChunk>(AIntervalChunk::StaticClass(),
			UIntervalGeometry::TileCornerToWorld(Chunk.X0, Chunk.Y0), FRotator::ZeroRotator, Params);
		if (!Actor)
		{
			return;
		}
#if WITH_EDITOR
		Actor->SetActorLabel(FString::Printf(TEXT("Ground_%d_%d"), Key.X, Key.Y));
#endif
		Live.Add(Key, Actor);
	}

	const UIntervalLook* Look = UIntervalLook::Resolve(Look_);
	UMaterialInterface* Ground = (Look && Look->GroundMaterial) ? Look->GroundMaterial.Get() : GroundMaterial.Get();
	// WHAT THE CHANNEL UNDER A CROSSING IS PAINTED AS, by the world's own word
	// and not by a number: a founding that adds a terrain shifts every code
	// after it, and a hand-written code would paint a bridge's river as
	// whatever happened to move into that slot.
	uint8 RiverCode = 255;
	if (Bridge)
	{
		const int32 Found = Bridge->GetTileNames().IndexOfByKey(FString(TEXT("river")));
		if (Found != INDEX_NONE && Found < 255)
		{
			RiverCode = static_cast<uint8>(Found);
		}
	}
	const UIntervalLook* SpanLook = UIntervalLook::Resolve(Look_);
	static const FIntervalSpan NoSpan;
	Actor->Build(Chunk, Ground, ScatterByCode, SpineScatter, RoofByCode,
		ThresholdByCode, ShapeOfTiles(), SpanLook ? SpanLook->Span : NoSpan,
		RiverCode, bGroundAffectsIndirect);

	// Say so. A wall placed before its ground existed was told there was no
	// building under it and drew itself as a yard wall; it has to hear that
	// the answer has changed.
	OnGroundChanged.Broadcast();
}

void AIntervalGround::ReleaseFarChunks(const FIntPoint& Centre)
{
	// One ring of slack, so a citizen pacing back and forth across a chunk
	// edge does not rebuild the same ground every other interval.
	const int32 Keep = Rings + 1;
	TArray<FIntPoint> Doomed;
	for (const TPair<FIntPoint, TObjectPtr<AIntervalChunk>>& Pair : Live)
	{
		if (FMath::Abs(Pair.Key.X - Centre.X) > Keep || FMath::Abs(Pair.Key.Y - Centre.Y) > Keep)
		{
			Doomed.Add(Pair.Key);
		}
	}
	for (const FIntPoint& Key : Doomed)
	{
		if (TObjectPtr<AIntervalChunk>* Actor = Live.Find(Key))
		{
			if (*Actor)
			{
				(*Actor)->Destroy();
			}
		}
		Live.Remove(Key);
	}
}

uint8 AIntervalGround::BuildingSeedAtTile(int32 TileX, int32 TileY) const
{
	const FIntPoint Key = UIntervalGeometry::ChunkOf(TileX, TileY);
	if (const TObjectPtr<AIntervalChunk>* Found = Live.Find(Key))
	{
		if (const AIntervalChunk* Chunk = Found->Get())
		{
			return Chunk->GetBuildingSeedAtTile(TileX, TileY);
		}
	}
	return 0;
}

uint8 AIntervalGround::CodeAtTile(int32 TileX, int32 TileY) const
{
	const FIntPoint Key = UIntervalGeometry::ChunkOf(TileX, TileY);
	const TObjectPtr<AIntervalChunk>* Found = Live.Find(Key);
	const AIntervalChunk* Chunk = Found ? Found->Get() : nullptr;
	return Chunk ? Chunk->GetCodeAtTile(TileX, TileY) : 255;
}

float AIntervalGround::GroundHeightAtTile(int32 TileX, int32 TileY) const
{
	const FIntPoint Key = UIntervalGeometry::ChunkOf(TileX, TileY);
	const TObjectPtr<AIntervalChunk>* Found = Live.Find(Key);
	if (const AIntervalChunk* Chunk = Found ? Found->Get() : nullptr)
	{
		return Chunk->GetReliefAt(TileX, TileY);
	}
	// NOT ZERO. Ground that has not arrived is still ground, and a citizen who
	// walked off the edge of the loaded world would drop to sea level and
	// climb back out again a second later. The bare land is the same answer
	// the chunk will give for everything but a way, water or a floor.
	return UIntervalGeometry::LandAt(TileX, TileY);
}

FName AIntervalGround::GroundWordAtTile(int32 TileX, int32 TileY) const
{
	const FIntPoint Key = UIntervalGeometry::ChunkOf(TileX, TileY);
	const TObjectPtr<AIntervalChunk>* Found = Live.Find(Key);
	const AIntervalChunk* Chunk = Found ? Found->Get() : nullptr;
	if (!Chunk || !Bridge)
	{
		return NAME_None;
	}
	const uint8 Code = Chunk->GetCodeAtTile(TileX, TileY);
	const TArray<FString>& Names = Bridge->GetTileNames();
	return Names.IsValidIndex(Code) ? FName(*Names[Code]) : NAME_None;
}

bool AIntervalGround::RoofShownAtTile(int32 TileX, int32 TileY) const
{
	if (!IsRoofedAtTile(TileX, TileY))
	{
		return false;
	}
	// A roof the occlusion rule has taken away is not there to stand on. The
	// key is 0 where no building covers the tile, and 0 is never in the set.
	const int64 Key = BuildingKeyAtTile(TileX, TileY);
	return Key == 0 || !Hidden.Contains(Key);
}

float AIntervalGround::RoofTopAtTile(int32 TileX, int32 TileY) const
{
	const FIntPoint Key = UIntervalGeometry::ChunkOf(TileX, TileY);
	if (const TObjectPtr<AIntervalChunk>* Found = Live.Find(Key))
	{
		if (const AIntervalChunk* Chunk = Found->Get())
		{
			return Chunk->GetRoofTopAtTile(TileX, TileY);
		}
	}
	return NoRoof;
}

int64 AIntervalGround::BuildingKeyAtTile(int32 TileX, int32 TileY) const
{
	const FIntPoint Key = UIntervalGeometry::ChunkOf(TileX, TileY);
	if (const TObjectPtr<AIntervalChunk>* Found = Live.Find(Key))
	{
		if (const AIntervalChunk* Chunk = Found->Get())
		{
			return Chunk->GetBuildingKeyAtTile(TileX, TileY);
		}
	}
	return 0;
}
