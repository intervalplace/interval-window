#include "IntervalChunk.h"

#include "Components/InstancedStaticMeshComponent.h"

#include "IntervalGround.h"
#include "IntervalGeometry.h"
#include "ProceduralMeshComponent.h"
#include "Engine/Texture2D.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "TextureResource.h"

DEFINE_LOG_CATEGORY_STATIC(LogIntervalChunk, Log, All);

AIntervalChunk::AIntervalChunk()
{
	PrimaryActorTick.bCanEverTick = false;

	Mesh = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("Ground"));
	Mesh->bUseAsyncCooking = true;
	// The world decides where anyone may stand; nothing here does. Collision
	// exists only so the cursor can be traced against the ground for
	// click-to-walk, and it must never be the thing that stops a citizen.
	Mesh->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Mesh->SetCollisionResponseToAllChannels(ECR_Ignore);
	Mesh->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
	SetRootComponent(Mesh);
	RoofMesh = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("Roofs"));
	RoofMesh->SetupAttachment(Mesh);
	RoofMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	RoofMesh->bUseAsyncCooking = true;
	SpanMesh = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("Spans"));
	SpanMesh->SetupAttachment(Mesh);
	SpanMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	SpanMesh->bUseAsyncCooking = true;
}

int32 AIntervalChunk::IndexOf(int32 TileX, int32 TileY) const
{
	// Answers for the INTERIOR only. The skirt is there to be read while
	// building, not to be reported as ground this chunk owns -- two chunks
	// both claiming the same tile is how a seam becomes a disagreement.
	const int32 LocalX = TileX - OriginX;
	const int32 LocalY = TileY - OriginY;
	if (LocalX < 0 || LocalY < 0 || LocalX >= Width || LocalY >= Height)
	{
		return INDEX_NONE;
	}
	return Local(LocalX, LocalY);
}

uint8 AIntervalChunk::GetCodeAtTile(int32 TileX, int32 TileY) const
{
	const int32 Index = IndexOf(TileX, TileY);
	return Codes.IsValidIndex(Index) ? Codes[Index] : 255;
}

uint8 AIntervalChunk::GetBuildingSeedAtTile(int32 TileX, int32 TileY) const
{
	const int32 LocalX = TileX - OriginX;
	const int32 LocalY = TileY - OriginY;
	if (LocalX < 0 || LocalY < 0 || LocalX >= Width || LocalY >= Height
		|| BuildingKey.Num() != Width * Height)
	{
		return 0;
	}
	const int64 Key = BuildingKey[LocalY * Width + LocalX];
	if (Key == 0) { return 0; }
	// Derived from the key, not stored beside it, so the wall and the roof of
	// one house cannot drift apart.
	const int32 CornerX = static_cast<int32>((Key >> 32) & 0xFFFFFFFF) - 0x40000000;
	const int32 CornerY = static_cast<int32>(Key & 0xFFFFFFFF) - 0x40000000;
	return static_cast<uint8>(1 + (UIntervalGeometry::HashTile(CornerX, CornerY) % 255));
}

float AIntervalChunk::GetRoofTopAtTile(int32 TileX, int32 TileY) const
{
	const int32 LocalX = TileX - OriginX;
	const int32 LocalY = TileY - OriginY;
	if (LocalX < 0 || LocalY < 0 || LocalX >= Width || LocalY >= Height
		|| RoofTop.Num() != Width * Height)
	{
		return AIntervalGround::NoRoof;
	}
	return RoofTop[LocalY * Width + LocalX];
}

int64 AIntervalChunk::GetBuildingKeyAtTile(int32 TileX, int32 TileY) const
{
	const int32 LocalX = TileX - OriginX;
	const int32 LocalY = TileY - OriginY;
	if (LocalX < 0 || LocalY < 0 || LocalX >= Width || LocalY >= Height
		|| BuildingKey.Num() != Width * Height)
	{
		return 0;
	}
	return BuildingKey[LocalY * Width + LocalX];
}

uint8 AIntervalChunk::GetSeedAtTile(int32 TileX, int32 TileY) const
{
	const int32 Index = IndexOf(TileX, TileY);
	return Seeds.IsValidIndex(Index) ? Seeds[Index] : 0;
}

bool AIntervalChunk::IsWayAtTile(int32 TileX, int32 TileY) const
{
	const int32 Index = IndexOf(TileX, TileY);
	return Ways.IsValidIndex(Index) && Ways[Index] != 0;
}

float AIntervalChunk::HeightOfTile(int32 WorldX, int32 WorldY, int32 Index) const
{
	// A BUILDING'S FLOOR IS FLAT, and it was decided before this was asked.
	// See FloorZ: without this the ground under a levelled building still
	// followed the hill, and the walls stood over a floor that fell away.
	if (FloorZ.IsValidIndex(Index) && FloorZ[Index] > NoFloor * 0.5f)
	{
		return FloorZ[Index];
	}
	uint8 Shape = ShapeLand;
	if (Codes.IsValidIndex(Index) && Shapes.IsValidIndex(Codes[Index]))
	{
		Shape = Shapes[Codes[Index]];
	}
	// A DECK STANDS WHERE A ROAD STANDS, whether or not the founders' road
	// list happens to name the tile. It is the road: the world put it there
	// to carry one across water, and a crossing that answered with the land
	// height would drop the road into the river at both ends.
	const bool bIsWay = (Shape == ShapeDeck)
		|| (Ways.IsValidIndex(Index) && Ways[Index] != 0);
	return UIntervalGeometry::GroundAt(WorldX, WorldY, bIsWay,
		Shape == ShapeWater, Shape == ShapeFloor);
}

bool AIntervalChunk::IsDeckLocal(int32 LocalX, int32 LocalY) const
{
	if (!HasLocal(LocalX, LocalY))
	{
		return false;
	}
	const int32 Index = Local(LocalX, LocalY);
	return Codes.IsValidIndex(Index) && Shapes.IsValidIndex(Codes[Index])
		&& Shapes[Codes[Index]] == ShapeDeck;
}

bool AIntervalChunk::IsWetLocal(int32 LocalX, int32 LocalY) const
{
	if (!HasLocal(LocalX, LocalY))
	{
		return false;
	}
	const int32 Index = Local(LocalX, LocalY);
	return Wet.IsValidIndex(Index) && Wet[Index] != 0;
}

float AIntervalChunk::DrawHeightOfTile(int32 LocalX, int32 LocalY, int32 Index) const
{
	const float Stood = HeightOfTile(OriginX + LocalX, OriginY + LocalY, Index);
	if (!Span.Any() || Span.Channel <= 0.f)
	{
		return Stood;
	}
	uint8 Shape = ShapeLand;
	if (Codes.IsValidIndex(Index) && Shapes.IsValidIndex(Codes[Index]))
	{
		Shape = Shapes[Codes[Index]];
	}
	// ---- HOW FAR IS THIS TILE FROM BEING UNDER A BRIDGE ----
	//
	// ONLY WATER IS DUG, and that is the whole of the second attempt at this.
	// The first asked the ground kind, which calls every tile of a crossing
	// `bridge` -- including its paved approach, which on this island is most
	// of them: a hundred and thirty-five of two hundred and thirty-four bridge
	// tiles are dry land. So a three-metre channel was dug along sixty tiles
	// of road, through both banks, and the road arrived at the top of a pit.
	//
	// `Wet` says which tiles have water under them and comes from the
	// generator itself; see FIntervalTerrainChunk::Wet.
	if (!IsWetLocal(LocalX, LocalY))
	{
		return Stood;
	}
	if (Shape != ShapeDeck && Shape != ShapeWater)
	{
		return Stood;
	}
	int32 Near = MAX_int32;
	const int32 Reach = FMath::Max(0, Span.ChannelEase);
	for (int32 DY = -Reach; DY <= Reach && Near > 0; ++DY)
	{
		for (int32 DX = -Reach; DX <= Reach; ++DX)
		{
			// A DRY deck tile is a bank, not a crossing, and digging toward it
			// would undercut the abutment the road stands on.
			if (!IsDeckLocal(LocalX + DX, LocalY + DY)
				|| !IsWetLocal(LocalX + DX, LocalY + DY))
			{
				continue;
			}
			Near = FMath::Min(Near, FMath::Max(FMath::Abs(DX), FMath::Abs(DY)));
			if (Near == 0)
			{
				break;
			}
		}
	}
	if (Near > Reach)
	{
		return Stood;   // nowhere near a crossing; the river is the river
	}
	// The road's own height, which is where the deck will be laid: the dug bed
	// is measured DOWN FROM THE ROAD and not down from the water, so the
	// clearance under a bridge is the same on every crossing on the island
	// however deep the water beside it happens to lie.
	const float Road = UIntervalGeometry::GroundAt(OriginX + LocalX, OriginY + LocalY,
		true, false, false);
	const float Bed = Road - Span.Channel;
	// Eased back to the ordinary water level over the last few tiles, so the
	// channel is a channel and not a rectangular hole with walls at the ends.
	const float T = Reach > 0 ? static_cast<float>(Near) / static_cast<float>(Reach) : 0.f;
	const float Smooth = T * T * (3.f - 2.f * T);
	return FMath::Lerp(Bed, Stood, Smooth);
}

// ---- A DECK IS WALKED ON, NOT WADED THROUGH ----
//
// `DrawHeightOfTile` digs a channel under a crossing so there is daylight
// beneath the bridge, and `FIntervalSpan::Channel` says in as many words what
// that is for: "THIS IS A DRAWING, NOT A DEPTH ... nothing that walks, stands,
// floats or is placed asks this question: the chunk keeps the standing height
// exactly as it was and digs only the TRIANGLES. A citizen on the bridge is on
// the road, at the road's height, in this window and in every other."
//
// It was not. `GetReliefAt` IS the standing height, and on a chunk carrying a
// deck it read the drawn triangles -- so a citizen who walked onto a bridge
// went three and a third metres down with them and crossed along the river
// bed, under their own bridge. Reported from the window: "when walking on the
// bridge the character is walking along the water floor instead".
//
// The deck slab's paving is laid at the road's height -- that is the whole
// purpose of `DeckKerb`, which exists so the slab is hung by its paving rather
// than by the top of its kerb -- so a deck tile's walkable surface is the road
// and nothing else. Every other tile keeps the drawn surface, because that is
// what `GetReliefAt` is for: see its own note about posts beside water
// hanging in the air.
//
// The neighbours matter as much as the tile. This is averaged over a 3x3, so
// a dry bank tile beside a crossing would be pulled down by the dug deck tiles
// next to it, and the approach to a bridge would dip. Answering for the deck
// here rather than at the top of GetReliefAt fixes the approach too.
float AIntervalChunk::StandHeightOfTile(int32 LocalX, int32 LocalY, int32 Index) const
{
	if (IsDeckLocal(LocalX, LocalY))
	{
		return UIntervalGeometry::GroundAt(OriginX + LocalX, OriginY + LocalY,
			true, false, false);
	}
	return DrawHeightOfTile(LocalX, LocalY, Index);
}

float AIntervalChunk::GetReliefAt(int32 TileX, int32 TileY) const
{
	const int32 Index = IndexOf(TileX, TileY);
	if (!Codes.IsValidIndex(Index))
	{
		return 0.f;
	}
	// ---- THE HEIGHT OF THE SURFACE YOU CAN SEE, NOT OF THE TILE ----
	//
	// This returned the tile's own height, and that is not where the ground
	// IS. The mesh gives every VERTEX the average of the four tiles meeting at
	// it (see `ReliefAtVertex` in Build, and the note there about plateaus),
	// so the drawn surface over a tile's centre is the average of that tile's
	// four corners -- which is a weighted mean of the nine tiles around it,
	// not the one tile under it. The two agree only where the ground is flat.
	//
	// Beside water they disagree badly, because `GroundAt` digs a water tile
	// a metre and a half below the land. A dry shore tile with water on one
	// side has two of its four corners pulled down by a quarter of that each;
	// with water on two sides, three of them. So the drawn sand under a
	// marker post's feet sits as much as three quarters of a metre below where
	// the post was placed, and the post hangs in the air.
	//
	// It was reported as a shadow fault, and that is exactly how it looks: the
	// shadow is cast correctly, it just lands on ground that is nowhere near
	// the thing's feet, and at a low sun it detaches completely. Every window
	// screenshot of the Anchor shore has this in it.
	//
	// Sampled with the same function the mesh used -- `DrawHeightOfTile` where
	// this chunk carries a bridge, `HeightOfTile` otherwise -- so placement and
	// drawing cannot drift apart again.
	//
	// The weights are what the two averagings come to: a corner is a quarter
	// each of four tiles, and the centre is a quarter each of four corners, so
	// the nine tiles land on [1 2 1; 2 4 2; 1 2 1] over sixteen.
	const int32 LX = TileX - OriginX;
	const int32 LY = TileY - OriginY;
	static const int32 Weight[3][3] = { {1, 2, 1}, {2, 4, 2}, {1, 2, 1} };
	float Sum = 0.f;
	int32 Total = 0;
	for (int32 DY = -1; DY <= 1; ++DY)
	{
		for (int32 DX = -1; DX <= 1; ++DX)
		{
			const int32 NX = LX + DX, NY = LY + DY;
			if (!HasLocal(NX, NY))
			{
				continue;   // off the skirt: the tiles we do have decide it
			}
			const int32 N = Local(NX, NY);
			const int32 W = Weight[DY + 1][DX + 1];
			Sum += W * (bHasDeck ? StandHeightOfTile(NX, NY, N)
			                     : HeightOfTile(TileX + DX, TileY + DY, N));
			Total += W;
		}
	}
	return Total > 0 ? Sum / Total : HeightOfTile(TileX, TileY, Index);
}

void AIntervalChunk::Build(const FIntervalTerrainChunk& Chunk, UMaterialInterface* GroundMaterial,
	const TArray<FIntervalScatterKind>& ScatterByCode,
	const FIntervalScatterKind& SpineScatter,
	const TArray<FIntervalRoofKind>& RoofByCode,
	const TArray<uint8>& ThresholdByCode,
	const TArray<uint8>& ShapeByCode, const FIntervalSpan& SpanLook,
	uint8 RiverCodeIn, bool bAffectIndirect)
{
	Shapes = ShapeByCode;
	Span = SpanLook;
	RiverCode = RiverCodeIn;
	// See AIntervalGround::bGroundAffectsIndirect for why this is normally off.
	Mesh->SetAffectDynamicIndirectLighting(bAffectIndirect);
	Mesh->SetAffectDistanceFieldLighting(bAffectIndirect);

	OriginX = Chunk.X0;
	OriginY = Chunk.Y0;
	Width = Chunk.W;
	Height = Chunk.H;
	Skirt = Chunk.Skirt;
	Stride = Width + Skirt * 2;
	Codes = Chunk.Tiles;
	Ways = Chunk.Ways;
	Spine = Chunk.Spine;
	Seeds = Chunk.Seeds;
	Wet = Chunk.Wet;

	// Short planes were already refused by the subsystem, but a chunk that
	// somehow arrived ragged would be drawn as ground that is not there, and
	// a hole in the island looks exactly like terrain.
	const int32 Expected = Stride * (Height + Skirt * 2);
	if (Codes.Num() != Expected)
	{
		UE_LOG(LogIntervalChunk, Error, TEXT("chunk %d,%d has %d codes for %d tiles"), OriginX, OriginY, Codes.Num(), Expected);
		return;
	}
	Ways.SetNumZeroed(Expected);
	Spine.SetNumZeroed(Expected);
	Seeds.SetNumZeroed(Expected);
	// A bridge older than this plane sends none: everything reads dry, no
	// channel is dug anywhere, and the crossings are drawn flat -- which is
	// what they were before, rather than a trench through the island.
	Wet.SetNumZeroed(Expected);

	// Asked once, here, because every later question about a crossing is a
	// search of a neighbourhood and there are ten crossings on an island of
	// four hundred and fifty thousand tiles.
	bHasDeck = false;
	for (int32 i = 0; i < Codes.Num() && !bHasDeck; ++i)
	{
		bHasDeck = Shapes.IsValidIndex(Codes[i]) && Shapes[Codes[i]] == ShapeDeck;
	}

	SetActorLocation(UIntervalGeometry::TileCornerToWorld(OriginX, OriginY));

	// BEFORE THE GROUND MESH, which asks it for every tile a building covers.
	BuildFloors(RoofByCode);
	BuildControlTexture(Chunk);
	BuildMesh(Chunk);

	if (GroundMaterial)
	{
		if (!MaterialInstance || MaterialInstance->Parent != GroundMaterial)
		{
			MaterialInstance = UMaterialInstanceDynamic::Create(GroundMaterial, this);
		}
		MaterialInstance->SetTextureParameterValue(TEXT("Control"), ControlTexture);
		// The material needs the size to step exactly one texel per tile.
		// (interior tiles, interior tiles, skirt). The material needs the skirt
		// to map a UV into a texture that is bigger than the ground it covers.
		MaterialInstance->SetVectorParameterValue(TEXT("ChunkSize"),
			FLinearColor(Width, Height, Skirt, 0.f));
		// AND HOW BIG A TILE IS. The material derives its tile coordinates
		// from WORLD POSITION now rather than from the interpolated UV -- see
		// the note over `T` in ground.hlsl -- and world position is in
		// centimetres, so it needs the scale. Set from the geometry so there
		// is one number and not two.
		MaterialInstance->SetScalarParameterValue(TEXT("TileSize"),
			UIntervalGeometry::GetTileSize());
		Mesh->SetMaterial(0, MaterialInstance);
	}

	// ---- ROOFS BEFORE SCATTER, BECAUSE NOTHING GROWS INDOORS ----
	//
	// These ran the other way round, and `RoofTop` is filled by BuildRoofs, so
	// the scatter had no way to know a tile was inside a house. Grass grew on
	// the floor of every building on the island. Nobody saw it for as long as
	// the roof was on; lifting the roof to make a town navigable put it on
	// screen in every settlement at once, a lawn in the middle of somebody's
	// hall. Same fault as the grass standing in a ploughed furrow, found the
	// same way: by looking.
	RoofKindsWere = RoofByCode;
	ThresholdWere = ThresholdByCode;
	BuildRoofs(RoofByCode, ThresholdByCode);
	ScatterWere = ScatterByCode;
	SpineWere = SpineScatter;
	BuildScatter(ScatterByCode, SpineScatter);
	BuildSpans();
}

// ---------------------------------------------------------------------------
// LEVEL EVERY BUILDING, AND BLEND THE LAND INTO IT.
//
// This is the same flood fill `BuildRoofs` does, run earlier and for a
// different answer: the roof pass wants each building's ridge, and this wants
// each building's FLOOR. It has to be earlier because the ground mesh is built
// before the roofs are and the ground mesh is what asks.
//
// The two must agree exactly or the wall meets the floor at a seam, so they do
// not each work it out: this writes the number down and the roof pass reads it.
void AIntervalChunk::BuildFloors(const TArray<FIntervalRoofKind>& RoofByCode)
{
	const int32 SW = Stride;
	const int32 SH = Height + Skirt * 2;
	FloorZ.Init(NoFloor, SW * SH);
	if (Codes.Num() != SW * SH)
	{
		return;
	}

	// The footprint, dilated by one to carry the floor out under the walls --
	// the same two steps, in the same order, as section 1 of BuildRoofs. A
	// building whose floor stopped at the inside face would have its own wall
	// standing on the hill instead of on itself.
	TArray<uint8> Cover;
	Cover.SetNumZeroed(SW * SH);
	for (int32 i = 0; i < SW * SH; ++i)
	{
		const uint8 Code = Codes[i];
		if (Code < RoofByCode.Num() && RoofByCode[Code].Material)
		{
			Cover[i] = 1;
		}
	}
	{
		TArray<uint8> Wider = Cover;
		for (int32 Y = 0; Y < SH; ++Y)
		{
			for (int32 X = 0; X < SW; ++X)
			{
				if (Cover[Y * SW + X]) { continue; }
				for (int32 DY = -1; DY <= 1 && !Wider[Y * SW + X]; ++DY)
				{
					for (int32 DX = -1; DX <= 1; ++DX)
					{
						const int32 NX = X + DX, NY = Y + DY;
						if (NX < 0 || NY < 0 || NX >= SW || NY >= SH) { continue; }
						if (Cover[NY * SW + NX]) { Wider[Y * SW + X] = 1; break; }
					}
				}
			}
		}
		Cover = MoveTemp(Wider);
	}

	// One building at a time, and its floor is the MEAN of the ground it
	// stands on.
	//
	// Not the centre tile, which is what this used when the base was worked
	// out in the roof pass: on a slope the centre is an arbitrary height and
	// the building either floats at one end or is buried at the other. The
	// mean beds it in -- a cutting on the uphill side, a plinth on the down --
	// which is what levelling a site for a building actually does.
	TArray<int32> Comp;
	Comp.Init(INDEX_NONE, SW * SH);
	TArray<int32> Stack;
	for (int32 Start = 0; Start < SW * SH; ++Start)
	{
		if (!Cover[Start] || Comp[Start] != INDEX_NONE)
		{
			continue;
		}
		TArray<int32> Blob;
		Stack.Reset();
		Stack.Add(Start);
		Comp[Start] = Start;
		double Sum = 0.0;
		while (Stack.Num())
		{
			const int32 At = Stack.Pop();
			Blob.Add(At);
			const int32 X = At % SW, Y = At / SW;
			Sum += UIntervalGeometry::GroundAt(OriginX + X - Skirt,
				OriginY + Y - Skirt, false, false, true);
			const int32 Steps[4][2] = { {1,0}, {-1,0}, {0,1}, {0,-1} };
			for (const auto& D : Steps)
			{
				const int32 NX = X + D[0], NY = Y + D[1];
				if (NX < 0 || NY < 0 || NX >= SW || NY >= SH) { continue; }
				const int32 N = NY * SW + NX;
				if (Cover[N] && Comp[N] == INDEX_NONE)
				{
					Comp[N] = Start;
					Stack.Add(N);
				}
			}
		}
		const float Base = static_cast<float>(Sum / FMath::Max(1, Blob.Num()));
		for (const int32 At : Blob)
		{
			FloorZ[At] = Base;
		}
	}

	// ---- AND AN APRON, SO THE PLATFORM IS NOT A CLIFF ----
	//
	// A levelled site meets the land somewhere, and where it does there is a
	// step exactly as tall as the levelling. Left alone, a building on a hill
	// sits on a mesa with a vertical edge -- which is what was reported: "some
	// buildings are kind of weirdly sitting on top of a hill".
	//
	// One ring of tiles outside the footprint is brought halfway to the floor,
	// and the ground mesh averages the four tiles meeting at each vertex, so
	// what the eye gets is a ramp of about two tiles rather than a wall. It is
	// still a platform, which is honest -- somebody levelled this ground -- but
	// it is a platform you could walk up.
	// TWO RINGS, AND THE FIRST ONE IS CAPPED.
	//
	// One ring at half blend was not enough where the hill rises against a
	// building. Measured on that same terrace: the ground on the uphill side
	// came out two metres ABOVE the floor, which does not read as a bank -- it
	// buries the bottom of the wall and most of the doorway, and a door you
	// step down two metres through is worse than the plinth this set out to
	// fix.
	//
	// So the ring touching the building is held within a DOORSTEP of the floor
	// (ninety centimetres up, a metre and a half down), and a second ring
	// carries the rest of the difference. What a steep site gets is a cutting
	// on the uphill side and a bank on the down, which is what digging a level
	// site for a building actually leaves behind.
	const float StepUp = 90.f, StepDown = 150.f;
	TArray<float> Rings = FloorZ;
	for (int32 Ring = 0; Ring < 2; ++Ring)
	{
		TArray<float> Next = Rings;
		const float Pull = (Ring == 0) ? 0.66f : 0.34f;
		const float Up = (Ring == 0) ? StepUp : StepUp * 3.f;
		const float Down = (Ring == 0) ? StepDown : StepDown * 2.4f;
		for (int32 Y = 0; Y < SH; ++Y)
		{
			for (int32 X = 0; X < SW; ++X)
			{
				const int32 At = Y * SW + X;
				if (Rings[At] > NoFloor * 0.5f) { continue; }
				// THE MEAN OF EVERY FLOOR IT TOUCHES, not the first one found.
				//
				// A hill town has terraces at different heights with a strip of
				// street between them, and that strip touches both. Taking
				// whichever neighbour the scan happened to reach first made the
				// strip belong entirely to one of them, so the step between two
				// houses landed in one tile instead of being shared. Averaging
				// puts the street halfway, which is where a street between two
				// terraces goes.
				double Sum = 0.0;
				int32 Count = 0;
				for (int32 DY = -1; DY <= 1; ++DY)
				{
					for (int32 DX = -1; DX <= 1; ++DX)
					{
						const int32 NX = X + DX, NY = Y + DY;
						if (NX < 0 || NY < 0 || NX >= SW || NY >= SH) { continue; }
						const float Z = Rings[NY * SW + NX];
						if (Z > NoFloor * 0.5f) { Sum += Z; ++Count; }
					}
				}
				if (Count == 0) { continue; }
				const float Near = static_cast<float>(Sum / Count);
				const float Land = UIntervalGeometry::GroundAt(
					OriginX + X - Skirt, OriginY + Y - Skirt, false, false, false);
				Next[At] = FMath::Clamp(FMath::Lerp(Land, Near, Pull),
					Near - Down, Near + Up);
			}
		}
		Rings = MoveTemp(Next);
	}
	FloorZ = MoveTemp(Rings);
}

void AIntervalChunk::BuildControlTexture(const FIntervalTerrainChunk& Chunk)
{
	// One texel per tile. NEAREST, uncompressed, no sRGB: this is data, and a
	// bilinear filter would invent terrains halfway between two real ones.
	// THE SKIRT GOES IN THE TEXTURE TOO.
	//
	// The material warps which texel a pixel reads, so that a country's edge
	// is a ragged line rather than a staircase of tile corners. A warp that
	// can leave the interior would read the clamped edge texel at a chunk
	// boundary and print a seam -- the same class of fault as the relief seam
	// and the lost eaves, and the same answer: give it the border to read.
	const int32 TexW = Width + Skirt * 2;
	const int32 TexH = Height + Skirt * 2;
	ControlTexture = UTexture2D::CreateTransient(TexW, TexH, PF_B8G8R8A8);
	if (!ControlTexture)
	{
		return;
	}
	ControlTexture->Filter = TF_Nearest;
	ControlTexture->SRGB = false;
	ControlTexture->CompressionSettings = TC_VectorDisplacementmap;
	ControlTexture->AddressX = TA_Clamp;
	ControlTexture->AddressY = TA_Clamp;
	ControlTexture->NeverStream = true;

	FTexture2DMipMap& Mip = ControlTexture->GetPlatformData()->Mips[0];
	uint8* Pixels = static_cast<uint8*>(Mip.BulkData.Lock(LOCK_READ_WRITE));
	for (int32 Texel = 0; Texel < TexW * TexH; ++Texel)
	{
		const int32 Index = Texel;
		// BGRA on the wire to the GPU; the material reads R, G, B as
		// terrain code, made way, scatter seed.
		uint8 Code = Codes[Index];
		uint8 Way = Ways[Index] ? 255 : 0;
		// A DECK IS NOT GROUND, so the ground under it is painted as the water
		// it crosses and the road mark is taken off it. Leaving the tile as
		// itself lays flagstones along the bottom of the dug channel, with the
		// real deck floating a few metres above them -- paving underwater,
		// which is what this drew before the crossings were built.
		if (bHasDeck && Shapes.IsValidIndex(Code) && Shapes[Code] == ShapeDeck
			&& RiverCode != 255)
		{
			Code = RiverCode;
			Way = 0;
		}
		Pixels[Texel * 4 + 0] = Seeds[Index];        // B
		Pixels[Texel * 4 + 1] = Way;                 // G
		Pixels[Texel * 4 + 2] = Code;                // R
		Pixels[Texel * 4 + 3] = 255;                 // A
	}
	Mip.BulkData.Unlock();
	ControlTexture->UpdateResource();

	// WHAT THE GROUND ACTUALLY THINKS IT IS.
	//
	// Temporary, and earning its place: a whole quarter of the island drew as
	// flat colour with no roads and no scatter, and every property on the way
	// in read correctly -- chunk in the right place, component visible, right
	// material, right texture size. The one thing never looked at was the
	// CODES, and a code is the only input that decides a ground's colour, its
	// road and what grows on it.
	{
		int32 Tally[256] = { 0 };
		for (int32 i = 0; i < Codes.Num(); ++i) { Tally[Codes[i]]++; }
		FString Top;
		for (int32 Pass = 0; Pass < 4; ++Pass)
		{
			int32 Best = 0;
			for (int32 c = 1; c < 256; ++c) { if (Tally[c] > Tally[Best]) { Best = c; } }
			if (Tally[Best] <= 0) { break; }
			Top += FString::Printf(TEXT("%d x%d  "), Best, Tally[Best]);
			Tally[Best] = 0;
		}
		// Log, not Warning: a hundred and twelve of these arrive on every
		// session start and they are a diagnostic, not a complaint.
		UE_LOG(LogIntervalChunk, Log, TEXT("chunk %d,%d codes: %s"), OriginX, OriginY, *Top);
	}
}

void AIntervalChunk::BuildMesh(const FIntervalTerrainChunk& Chunk)
{
	const float TileSize = UIntervalGeometry::TileSize;
	const int32 VertsX = Width + 1;
	const int32 VertsY = Height + 1;

	// ---- EVERY TILE'S DRAWN HEIGHT, ONCE ----
	//
	// A vertex reads four tiles and a tile is read by four vertices, so each
	// tile's height was worked out four times over. That cost nothing while
	// the answer was arithmetic; under a crossing it is a search of the
	// neighbourhood for the nearest deck tile, and four times over a chunk is
	// eight hundred thousand cell tests inside an eight-millisecond budget.
	//
	// So the grid is filled first, skirt and all, and the vertices read it.
	// `bHasDeck` keeps every chunk with no bridge in it exactly as cheap as it
	// was, which is all but a handful on the island.
	const int32 GridW = Width + Skirt * 2;
	const int32 GridH = Height + Skirt * 2;
	TArray<float> DrawZ;
	DrawZ.SetNumUninitialized(GridW * GridH);
	for (int32 GY = 0; GY < GridH; ++GY)
	{
		for (int32 GX = 0; GX < GridW; ++GX)
		{
			const int32 LX = GX - Skirt;
			const int32 LY = GY - Skirt;
			const int32 Index = Local(LX, LY);
			DrawZ[GY * GridW + GX] = bHasDeck
				? DrawHeightOfTile(LX, LY, Index)
				: HeightOfTile(OriginX + LX, OriginY + LY, Index);
		}
	}

	// Relief is per-tile, so a vertex takes the average of the tiles that
	// meet at it. Without that the ground is a field of little plateaus with
	// a seam at every tile edge, which is the boardgame look the whole
	// session is trying to leave behind.
	auto ReliefAtVertex = [&](int32 VX, int32 VY)
	{
		float Sum = 0.f;
		int32 Count = 0;
		// ALL FOUR TILES, INCLUDING THE ONES NEXT DOOR. This used to skip any
		// tile outside the chunk, so at a shared edge the chunk on the left
		// averaged the last tile it had and the chunk on the right averaged
		// the first tile IT had -- two different answers for a vertex they
		// both own, and the ground split along every chunk boundary. With the
		// skirt both sides read the same four tiles and agree exactly.
		for (int32 DY = -1; DY <= 0; ++DY)
		{
			for (int32 DX = -1; DX <= 0; ++DX)
			{
				const int32 TX = VX + DX;
				const int32 TY = VY + DY;
				if (!HasLocal(TX, TY))
				{
					continue;
				}
				// `TX` is a LOCAL tile index, negative inside the skirt, so
				// the row in the grid is that plus the skirt. Reading it as
				// though it were already a grid index would shift every
				// chunk's landscape by four tiles against its neighbour's,
				// which is a seam in the one place a seam is most visible:
				// the horizon line.
				Sum += DrawZ[(TY + Skirt) * GridW + (TX + Skirt)];
				++Count;
			}
		}
		return Count > 0 ? Sum / Count : 0.f;
	};

	TArray<FVector> Vertices;
	TArray<FVector2D> UVs;
	TArray<FVector> Normals;
	TArray<FLinearColor> Colors;
	TArray<FProcMeshTangent> Tangents;
	TArray<int32> Triangles;

	Vertices.Reserve(VertsX * VertsY);
	UVs.Reserve(VertsX * VertsY);
	Normals.Reserve(VertsX * VertsY);
	Colors.Reserve(VertsX * VertsY);
	Tangents.Reserve(VertsX * VertsY);
	Triangles.Reserve(Width * Height * 6);

	TArray<float> Relief;
	Relief.SetNumUninitialized(VertsX * VertsY);
	for (int32 VY = 0; VY < VertsY; ++VY)
	{
		for (int32 VX = 0; VX < VertsX; ++VX)
		{
			Relief[VY * VertsX + VX] = ReliefAtVertex(VX, VY);
		}
	}

	for (int32 VY = 0; VY < VertsY; ++VY)
	{
		for (int32 VX = 0; VX < VertsX; ++VX)
		{
			const float Z = Relief[VY * VertsX + VX];
			Vertices.Add(FVector(VX * TileSize, VY * TileSize, Z));

			// UVs run 0..1 across the chunk, so the material's texel step is
			// 1/Width: sampling the centre of a tile's texel is
			// (TileX + 0.5) / Width, which the material does itself.
			UVs.Add(FVector2D(static_cast<float>(VX) / Width, static_cast<float>(VY) / Height));

			const float Left  = Relief[VY * VertsX + FMath::Max(VX - 1, 0)];
			const float Right = Relief[VY * VertsX + FMath::Min(VX + 1, VertsX - 1)];
			const float Up    = Relief[FMath::Max(VY - 1, 0) * VertsX + VX];
			const float Down  = Relief[FMath::Min(VY + 1, VertsY - 1) * VertsX + VX];
			FVector Normal = FVector(Left - Right, Up - Down, 2.f * TileSize);
			Normal.Normalize();
			Normals.Add(Normal);
			Tangents.Add(FProcMeshTangent(1.f, 0.f, 0.f));
			Colors.Add(FLinearColor::White);
		}
	}

	for (int32 TY = 0; TY < Height; ++TY)
	{
		for (int32 TX = 0; TX < Width; ++TX)
		{
			const int32 TopLeft = TY * VertsX + TX;
			const int32 TopRight = TopLeft + 1;
			const int32 BottomLeft = TopLeft + VertsX;
			const int32 BottomRight = BottomLeft + 1;

			Triangles.Add(TopLeft);    Triangles.Add(BottomLeft); Triangles.Add(TopRight);
			Triangles.Add(TopRight);   Triangles.Add(BottomLeft); Triangles.Add(BottomRight);
		}
	}

	Mesh->ClearAllMeshSections();
	Mesh->CreateMeshSection_LinearColor(0, Vertices, Triangles, Normals, UVs, Colors, Tangents, true);
}

void AIntervalChunk::BuildScatter(const TArray<FIntervalScatterKind>& ScatterByCode,
	const FIntervalScatterKind& SpineScatter)
{
	for (const TPair<uint32, TObjectPtr<UInstancedStaticMeshComponent>>& Pair : ScatterPools)
	{
		if (Pair.Value)
		{
			Pair.Value->ClearInstances();
		}
	}
	const bool bHasSpine = (SpineScatter.Mesh != nullptr) && SpineScatter.PerTile > 0.f;
	if (ScatterByCode.Num() == 0 && !bHasSpine)
	{
		return;
	}

	const float TileSize = UIntervalGeometry::TileSize;

	for (int32 Y = 0; Y < Height; ++Y)
	{
		for (int32 X = 0; X < Width; ++X)
		{
			const int32 Index = Local(X, Y);
			const uint8 Code = Codes[Index];
			// THE SPINE GROWS ROCK, WHATEVER THE GROUND UNDER IT SAYS.
			//
			// The ridge is a PREDICATE, not a ground: its tiles come back as
			// ordinary `crags`, the same as the whole eastern third of the
			// world, so the island's one great wall -- the thing two named
			// passes cross and the generator shuts one of -- was drawn as open
			// rough country. Told where it is (see FIntervalTerrainChunk::Spine)
			// this plants the ridge's own scatter there instead of the ground's,
			// which is the only place in this window where a tile's planting is
			// decided by something other than what it is made of.
			//
			// A road over the ridge is still a road: the two passes and
			// whatever the founders lay across them stay clear, or the window
			// would wall up the only ways through.
			const bool bOnSpine = bHasSpine && Spine.IsValidIndex(Index)
				&& Spine[Index] != 0 && Ways[Index] == 0;
			if (!bOnSpine && Code >= ScatterByCode.Num())
			{
				continue;   // ground this window was told about but shown nothing for
			}
			const FIntervalScatterKind& Kind = bOnSpine ? SpineScatter : ScatterByCode[Code];
			if (!Kind.Mesh || Kind.PerTile <= 0.f)
			{
				continue;
			}
			if (Kind.bAvoidWays && Ways[Index] != 0)
			{
				continue;
			}
			// ---- AND NOTHING GROWS WILD ON PLOUGHED GROUND ----
			//
			// A plot is a node and this is laid off the ground's own code, so
			// neither knew about the other and wild grass came up through every
			// furrow in every field on the island. Ploughing ground is the act
			// of making it bare; grass standing in it says nobody has worked it
			// for a year.
			if (Tilled.Num() > 0
				&& Tilled.Contains(FIntPoint(OriginX + X, OriginY + Y)))
			{
				continue;
			}
			// ---- NOR UNDER A ROOF ----
			//
			// `RoofTop` is filled by BuildRoofs, which now runs first. A tile
			// with a roof over it is the inside of a building, and the inside
			// of a building is a floor. An unroofed yard keeps its weeds,
			// which is right: nobody has put a lid on it.
			//
			// NOT `Index`. `Local()` returns the index into `Codes`, which
			// carries the skirt, and `RoofTop` is the chunk's own tiles with
			// no skirt on them. Indexing one with the other walks off the end,
			// which the engine caught at once: "Array index out of bounds:
			// 4252 into an array of size 4096", 4096 being 64 by 64.
			const int32 Bare = Y * Width + X;
			if (RoofTop.Num() == Width * Height
				&& RoofTop[Bare] > AIntervalGround::NoRoof * 0.5f)
			{
				continue;
			}

			// EVERYTHING BELOW COMES OUT OF ONE BYTE, and that is the whole
			// point: the byte is tileHash(x, y, 97), the generator's own pure
			// function, so this arrangement is identical in every window that
			// reads it the same way. Nothing here consults a clock, a random
			// stream, or where the camera is.
			//
			//   the byte itself decides WHETHER anything grows,
			//   one fixed scramble of it decides WHERE, and at WHAT ANGLE.
			//
			// Reusing the same byte for both correlates them a little -- a
			// sparse ground's tufts favour one corner -- which is invisible at
			// one item per four square metres and is the price of not inventing
			// a second plane that no other window would agree with.
			const uint8 Seed = Seeds[Index];
			const int32 Tries = FMath::Clamp(Kind.PerTileCount, 1, 16);
			for (int32 Try = 0; Try < Tries; ++Try)
			{
			// EACH TRY IS ITS OWN SCRAMBLE OF THE SAME BYTE. The byte is still
			// tileHash(x, y, 97) -- the generator's own pure function -- so a
			// tile's whole arrangement remains identical in every window that
			// reads it this way, however many things are on it. Nothing here
			// consults a clock, a random stream, or where the camera is.
			const uint32 S = (static_cast<uint32>(Seed) * 2654435761u)
				^ (static_cast<uint32>(Try) * 2246822519u);
			if (static_cast<float>((S >> 24) & 255u) / 255.f >= Kind.PerTile)
			{
				continue;
			}

			const float OffsetX = (static_cast<float>((S >> 4) & 15) + 0.5f) / 16.f;
			const float OffsetY = (static_cast<float>((S >> 9) & 15) + 0.5f) / 16.f;
			const float Yaw = (static_cast<float>((S >> 14) & 63) / 64.f) * Kind.YawJitter;
			const float Jit = Kind.ScaleJitter > 0.f
				? 1.f - Kind.ScaleJitter + (static_cast<float>((S >> 20) & 31) / 31.f) * Kind.ScaleJitter * 2.f
				: 1.f;

			// ON THE GROUND, WHICH IS NO LONGER A PLANE. Scatter was placed at
			// a fixed height because the land was flat to within a hand's
			// breadth; on a hillside the same code leaves grass hanging in
			// the air above the slope and buried under the one below it.
			const FVector Location(
				(OriginX + X + OffsetX) * TileSize,
				(OriginY + Y + OffsetY) * TileSize,
				Kind.ZOffset + HeightOfTile(OriginX + X, OriginY + Y, Index));

			// WHICH OF THIS GROUND'S PLANTS THIS ONE IS.
			//
			// Out of the same scramble that placed it, so the choice is a pure
			// function of the tile like everything else here -- and taken from
			// bits nothing else has used, or the variety would correlate with
			// the position and a wood would sort itself into stripes.
			//
			// One instanced component draws one mesh, so each variant needs a
			// pool of its own; the key carries both.
			const int32 Kinds = Kind.Variants.Num() + 1;
			const int32 Which = Kinds > 1
				? static_cast<int32>((S >> 2) & 255u) % Kinds : 0;
			UStaticMesh* Grown = (Which == 0) ? Kind.Mesh.Get()
				: Kind.Variants[Which - 1].Get();
			if (!Grown)
			{
				Grown = Kind.Mesh.Get();     // a variant the level left empty
			}
			// A POOL IS ONE MESH, and the spine's rock is not the ground's
			// plant even where the ground code is the same -- the crags scatter
			// pebbles and the ridge above them stands in boulders. Keyed past
			// the end of the code space so the two can never share a pool.
			const uint32 PoolKey = bOnSpine
				? (0xFFFF0000u | static_cast<uint32>(Which & 255))
				: ((static_cast<uint32>(Code) << 8) | static_cast<uint32>(Which & 255));

			TObjectPtr<UInstancedStaticMeshComponent>* Existing = ScatterPools.Find(PoolKey);
			UInstancedStaticMeshComponent* Pool = Existing ? Existing->Get() : nullptr;
			if (!Pool)
			{
				Pool = NewObject<UInstancedStaticMeshComponent>(this);
				Pool->SetupAttachment(Mesh);
				Pool->SetMobility(EComponentMobility::Movable);
				Pool->SetStaticMesh(Grown);
				Pool->SetCollisionEnabled(ECollisionEnabled::NoCollision);
				// ---- PER INSTANCE, NOT PER COMPONENT ----
				//
				// `SetCullDistance` is UPrimitiveComponent's, and it hides the
				// WHOLE POOL at once: every boulder a chunk owns is one
				// component, so a ridge of them did not fade, it blinked. Walk
				// toward a skyline and a hundred metres of rock arrives in a
				// single step; walk away and it leaves the same way. That is
				// what has been reported as the stones going up and down.
				//
				// `SetCullDistances` is the instanced mesh's own, and it is
				// measured from each INSTANCE. Rocks then go one at a time, by
				// their own distance, which is what a horizon does. The band
				// between the two numbers is the fade: a little under three
				// quarters of the way out, so there is room to go gradually
				// rather than a second hard edge further away.
				if (Kind.MaxDrawDistance > 0.f)
				{
					const int32 Far = FMath::RoundToInt(Kind.MaxDrawDistance);
					Pool->SetCullDistances(FMath::RoundToInt(Far * 0.72f), Far);
				}
				Pool->RegisterComponent();
				// After registration: see the note in IntervalStructures.cpp.
				// An override set before the render state exists is dropped,
				// and the mesh keeps the engine's checkered grid material.
				if (Kind.Material)
				{
					Pool->SetMaterial(0, Kind.Material);
				}
				Pool->SetCastShadow(Kind.bCastShadow);
				ScatterPools.Add(PoolKey, Pool);
			}

			Pool->AddInstance(FTransform(FRotator(0.f, Yaw, 0.f), Location, Kind.Scale * Jit), true);
			}   // each try
		}
	}
}

// ---------------------------------------------------------------------------
// THE CROSSINGS: A DECK OVER A CHANNEL, ON PIERS.
//
// The world names a road over water `bridge` and says nothing else about it --
// no length, no width, no arch. Everything below is read off the tiles:
// which way the crossing runs is whichever direction its deck tiles run
// FURTHEST, how wide it is is how many of them lie side by side, and where the
// piers go is a count along it. So the same code draws the eighteen-tile span
// east of Anchor and the three-tile one in the fens without being told which
// is which, and a founding that lays a new road across a new river gets a
// bridge on it the first time the ground arrives.
//
// ONE SLAB PER ROW, NOT PER TILE. The kit's deck section carries a low kerb
// along each of its long edges, which is right at the edge of a crossing and
// wrong anywhere else: laid tile by tile across a bridge three tiles wide it
// would leave two stone ribs running down the middle of the road. So a row is
// drawn as one slab stretched over the whole width, and the kerbs land where
// kerbs belong. The paving stretches with it, which is the price and is worth
// it; the alternative is a parapet mesh this kit does not have.
// ---------------------------------------------------------------------------
void AIntervalChunk::BuildSpans()
{
	if (DeckPool) { DeckPool->ClearInstances(); }
	if (PierPool) { PierPool->ClearInstances(); }
	if (SpanMesh) { SpanMesh->ClearAllMeshSections(); }
	if (!bHasDeck || !Span.Any())
	{
		return;
	}

	// The parapet, gathered as one mesh and given to the component at the end:
	// a run of stone along each side of the crossing. See SpanMesh.
	TArray<FVector> WallV;
	TArray<int32> WallT;
	TArray<FVector> WallN;
	TArray<FVector2D> WallUV;
	TArray<FLinearColor> WallC;
	TArray<FProcMeshTangent> WallTan;
	// A BOX, SIX FACES, EACH WITH ITS OWN FOUR CORNERS. Flat shading is not a
	// setting in this window, it is what you get by never sharing a vertex
	// between two faces -- which is how every other authored surface here is
	// built and why the island reads the way it does.
	//
	// THE WINDING IS CHECKED RATHER THAN REASONED ABOUT. Unreal's front face
	// is the one whose corners wind the other way from the usual convention,
	// in a left-handed space, and a box got wrong that way is invisible from
	// outside and solid from within -- which looks like a parapet that is not
	// being built at all. Six cross products a box is nothing, and it cannot
	// be got wrong by anybody reading this later either.
	auto Box = [&](const FVector& Centre, const FVector& Half, float YawDeg)
	{
		const FRotator Turn(0.f, YawDeg, 0.f);
		// bit 0 is +X, bit 1 is +Y, bit 2 is +Z.
		static const int32 Face[6][4] = {
			{ 1, 3, 7, 5 }, { 0, 4, 6, 2 },   // +X, -X
			{ 2, 6, 7, 3 }, { 0, 1, 5, 4 },   // +Y, -Y
			{ 4, 5, 7, 6 }, { 0, 2, 3, 1 },   // +Z, -Z
		};
		static const FVector Facing[6] = {
			FVector( 1, 0, 0), FVector(-1, 0, 0), FVector(0,  1, 0),
			FVector( 0,-1, 0), FVector( 0, 0, 1), FVector(0,  0,-1),
		};
		FVector Corner[8];
		for (int32 i = 0; i < 8; ++i)
		{
			Corner[i] = FVector(
				(i & 1) ? Half.X : -Half.X,
				(i & 2) ? Half.Y : -Half.Y,
				(i & 4) ? Half.Z : -Half.Z);
		}
		for (int32 F = 0; F < 6; ++F)
		{
			const int32 Base = WallV.Num();
			const FVector Out = Turn.RotateVector(Facing[F]);
			FVector Quad[4];
			for (int32 K = 0; K < 4; ++K)
			{
				Quad[K] = Centre + Turn.RotateVector(Corner[Face[F][K]]);
			}
			// Unreal draws a triangle whose geometric cross product points
			// AWAY from the eye; see the ground's own winding in BuildMesh.
			const bool bFlip = FVector::CrossProduct(Quad[1] - Quad[0],
				Quad[2] - Quad[0]).Dot(Out) > 0.f;
			for (int32 K = 0; K < 4; ++K)
			{
				WallV.Add(Quad[K]);
				WallN.Add(Out);
				WallUV.Add(FVector2D((K == 1 || K == 2) ? 1.f : 0.f,
					(K >= 2) ? 1.f : 0.f));
				WallC.Add(FLinearColor::White);
				WallTan.Add(FProcMeshTangent(1.f, 0.f, 0.f));
			}
			if (bFlip)
			{
				WallT.Add(Base); WallT.Add(Base + 2); WallT.Add(Base + 1);
				WallT.Add(Base); WallT.Add(Base + 3); WallT.Add(Base + 2);
			}
			else
			{
				WallT.Add(Base); WallT.Add(Base + 1); WallT.Add(Base + 2);
				WallT.Add(Base); WallT.Add(Base + 2); WallT.Add(Base + 3);
			}
		}
	};

	const float TileSize = UIntervalGeometry::TileSize;
	const FBox DeckBox = Span.Deck->GetBoundingBox();
	const FVector DeckSpan = DeckBox.GetSize();
	if (DeckSpan.X <= 1.f || DeckSpan.Y <= 1.f)
	{
		return;   // a mesh with no footprint would scale to infinity
	}

	auto Pool = [this](TObjectPtr<UInstancedStaticMeshComponent>& Slot,
		UStaticMesh* Stone, UMaterialInterface* Skin) -> UInstancedStaticMeshComponent*
	{
		if (!Slot)
		{
			Slot = NewObject<UInstancedStaticMeshComponent>(this);
			Slot->SetupAttachment(Mesh);
			Slot->SetMobility(EComponentMobility::Movable);
			Slot->SetStaticMesh(Stone);
			// NO COLLISION, like every other instanced thing in this window.
			// Nothing here is walked on by a physics body: a citizen stands
			// where the world says they stand, and the deck is drawn under
			// them because `GroundAt` already answers a crossing with the
			// road's own height.
			Slot->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Slot->RegisterComponent();
			// After registration: an override set before the render state
			// exists is dropped and the mesh keeps the engine's grid.
			if (Skin)
			{
				Slot->SetMaterial(0, Skin);
			}
		}
		return Slot.Get();
	};

	// HOW FAR THE DECK RUNS THROUGH A TILE, one axis at a time. The skirt is
	// four tiles, so a chunk can see four past its own edge; every crossing in
	// this founding is three tiles wide, so a row is never wider than what can
	// be seen and never has to be guessed at.
	auto Run = [this](int32 LX, int32 LY, int32 DX, int32 DY, int32& Lo, int32& Hi)
	{
		Lo = Hi = 0;
		while (IsDeckLocal(LX + DX * (Lo - 1), LY + DY * (Lo - 1))) { --Lo; }
		while (IsDeckLocal(LX + DX * (Hi + 1), LY + DY * (Hi + 1))) { ++Hi; }
	};

	int32 Slabs = 0, Piers = 0;
	for (int32 Y = 0; Y < Height; ++Y)
	{
		for (int32 X = 0; X < Width; ++X)
		{
			if (!IsDeckLocal(X, Y))
			{
				continue;
			}
			int32 XLo, XHi, YLo, YHi;
			Run(X, Y, 1, 0, XLo, XHi);
			Run(X, Y, 0, 1, YLo, YHi);
			const int32 AlongX = XHi - XLo + 1;
			const int32 AlongY = YHi - YLo + 1;
			// The crossing runs whichever way it runs furthest. A tie is a
			// square patch of deck, which is a junction of two crossings; it
			// takes Y and the other arm's own tiles take X, which is as good
			// an answer as the tiles contain.
			const bool bTravelY = AlongY >= AlongX;
			// Across the way: the row this tile belongs to.
			const int32 AcrossLo = bTravelY ? XLo : YLo;
			const int32 AcrossHi = bTravelY ? XHi : YHi;
			const int32 WideTiles = AcrossHi - AcrossLo + 1;

			// ONE CHUNK DRAWS EACH ROW, AND IT IS THE ONE HOLDING ITS FIRST
			// TILE. A row can straddle a chunk boundary -- both chunks can see
			// all of it through the skirt, and both would lay the same slab in
			// the same place, which is a second set of triangles in exactly
			// the same plane. Anchoring on the first tile across picks one.
			if (AcrossLo != 0)
			{
				continue;
			}

			// The tile in the middle of the row, for the height the whole row
			// is laid at: a bridge is level across its width even where the
			// land under it is not.
			const int32 CentreX = bTravelY ? X + (AcrossLo + AcrossHi) / 2 : X;
			const int32 CentreY = bTravelY ? Y : Y + (AcrossLo + AcrossHi) / 2;
			const int32 CentreIndex = Local(CentreX, CentreY);
			const float Road = HeightOfTile(OriginX + CentreX, OriginY + CentreY, CentreIndex);
			// AND THE MIDDLE OF THE ROW IN CENTIMETRES, which is not the middle
			// of that tile. An odd row has a tile in the middle and an even one
			// has a JOINT there, so taking the centre tile's own centre puts a
			// two-tile crossing half a tile off its own road. Every crossing in
			// this founding is three wide, so the fault would have waited for a
			// founding that laid a narrow one.
			const float MidX = (OriginX + X + (bTravelY ? (AcrossLo + AcrossHi + 1) * 0.5f : 0.5f))
				* TileSize;
			const float MidY = (OriginY + Y + (bTravelY ? 0.5f : (AcrossLo + AcrossHi + 1) * 0.5f))
				* TileSize;

			// The slab is laid exactly one tile ALONG the crossing, so
			// consecutive rows abut with no seam and no overlap whatever the
			// kit's own size happens to be.
			const float Wide = WideTiles * TileSize;
			const float ScaleAlong = TileSize / DeckSpan.Y;
			// ---- AND AS MANY SLABS ACROSS AS IT TAKES ----
			//
			// One slab stretched over the whole width was the first answer and
			// it is why the crossing came back looking like a row of bread
			// loaves: the kit's deck is two and a half metres of half-metre
			// paving, and a six-metre road made of one of them has stones a
			// metre and a quarter across, each with the bevel that was drawn
			// for a stone a quarter that size. Enlarging a stone does not
			// make a bigger stone; it makes a stone drawn at the wrong scale,
			// and the eye reads that instantly from any distance.
			//
			// So the row is made of however many slabs keep the stone close to
			// the size it was cut at, sharing the width equally. The kerbs
			// meet where two slabs do, which leaves a seam a hand's breadth
			// high down the road -- the mark of one course of paving against
			// the next, which is what a stone bridge actually has.
			const int32 Lanes = FMath::Max(1,
				FMath::RoundToInt(Wide / (DeckSpan.X * ScaleAlong)));
			const float LaneWide = Wide / Lanes;
			const float ScaleAcross = LaneWide / DeckSpan.X;
			// The thickness follows the ALONG scale and not the across one: a
			// six-metre crossing would otherwise have a deck two feet thick
			// because it is wide, which is a different bridge.
			const FVector DeckScale(ScaleAcross, ScaleAlong, ScaleAlong);
			// WHERE THE MESH ACTUALLY IS INSIDE ITSELF. This kit's deck is not
			// centred on its own pivot -- it sits a metre and a half to one
			// side -- so placing the pivot at the tile centre puts the stone
			// in the river beside the bridge. Measured and subtracted.
			const FVector Centre = DeckBox.GetCenter();
			const float Yaw = bTravelY ? Span.DeckYaw : Span.DeckYaw + 90.f;
			const FRotator Turn(0.f, Yaw, 0.f);
			const FVector Pivot = Turn.RotateVector(
				FVector(-Centre.X * DeckScale.X, -Centre.Y * DeckScale.Y, 0.f));
			for (int32 Lane = 0; Lane < Lanes; ++Lane)
			{
				// From the edge of the crossing inwards, so the outermost
				// slab's kerb lands on the outermost edge where it belongs.
				const float Off = (Lane + 0.5f) * LaneWide - Wide * 0.5f;
				const FVector Where(
					MidX + Pivot.X + (bTravelY ? Off : 0.f),
					MidY + Pivot.Y + (bTravelY ? 0.f : Off),
					// The deck's PAVING is the road, so the mesh hangs below
					// it -- and the paving is the top of the box less the kerb.
					Road - (DeckBox.Max.Z - Span.DeckKerb) * DeckScale.Z);
				Pool(DeckPool, Span.Deck, Span.DeckMaterial)
					->AddInstance(FTransform(Turn, Where, DeckScale), true);
				++Slabs;
			}

			// How far under the road the deck's own stone stops, which is
			// where anything hung below it starts.
			const float DeckDrop =
				(DeckBox.GetSize().Z - Span.DeckKerb) * DeckScale.Z;

			// ---- THE PARAPET, WHERE THERE IS WATER TO FALL INTO ----
			//
			// Not along the whole word. Most of a crossing on this island is
			// its paved approach -- a hundred and thirty-five of the two
			// hundred and thirty-four bridge tiles are dry -- and a stone wall
			// run down sixty tiles of open road is a palisade, not a bridge. So
			// the wall is built over the water and one tile onto each bank,
			// which is where a real one is built and for the same reason.
			bool bWall = false;
			for (int32 Step = -1; Step <= 1 && !bWall; ++Step)
			{
				for (int32 Off = AcrossLo; Off <= AcrossHi && !bWall; ++Off)
				{
					const int32 WX = bTravelY ? X + Off : X + Step;
					const int32 WY = bTravelY ? Y + Step : Y + Off;
					bWall = IsWetLocal(WX, WY);
				}
			}
			// Whether this row carries a rank of piers, which the spandrel
			// needs as well: the side wall is solid where the stone goes down
			// into the water and open between, which is what an arch is.
			const int32 AlongTile = bTravelY ? (OriginY + Y) : (OriginX + X);
			const bool bPierRow = Span.PierEvery <= 1
				|| (AlongTile % Span.PierEvery) == 0;
			if (bWall && Span.Parapet > 0.f)
			{
				const float Half = Span.ParapetThick * 0.5f;
				// A COPING ON TOP, which is what turns a kerb into a wall at
				// this distance: one course of stone set a little proud, so
				// the parapet has a line along it and does not read as a bar.
				const float Coping = FMath::Min(14.f, Span.Parapet * 0.25f);
				for (int32 Side = 0; Side < 2; ++Side)
				{
					const float AcrossCm = (Side == 0 ? -1.f : 1.f)
						* (Wide * 0.5f - Half);
					const FVector Mid(
						MidX + (bTravelY ? AcrossCm : 0.f),
						MidY + (bTravelY ? 0.f : AcrossCm),
						Road);
					const FVector Body = bTravelY
						? FVector(Half, TileSize * 0.5f, (Span.Parapet - Coping) * 0.5f)
						: FVector(TileSize * 0.5f, Half, (Span.Parapet - Coping) * 0.5f);
					Box(Mid + FVector(0.f, 0.f, (Span.Parapet - Coping) * 0.5f),
						Body, 0.f);
					const FVector Cap = bTravelY
						? FVector(Half + 5.f, TileSize * 0.5f, Coping * 0.5f)
						: FVector(TileSize * 0.5f, Half + 5.f, Coping * 0.5f);
					Box(Mid + FVector(0.f, 0.f, Span.Parapet - Coping * 0.5f),
						Cap, 0.f);

					// ---- AND THE SPANDREL, UNDER THE DECK ----
					//
					// It used to be built ONLY on the pier rows, so between
					// two ranks of piers there was nothing under the deck at
					// all: from any low angle the bridge was a slab of road
					// with daylight beneath it and then water, which was
					// reported as reading like a cliff edge.
					//
					// A stone bridge has no gap there. It has an ARCH, and an
					// arcade of them is the whole of what a bridge looks like
					// from the side. So the wall is carried across EVERY tile
					// and its depth is what curves: full over the piers, where
					// the stone goes down into the water, and drawn up toward
					// the crown of each bay. The void left underneath is the
					// arch, and it is a real void rather than a painted one.
					if (Span.Spandrel > 0.f)
					{
						// HOW FAR ACROSS THE BAY THIS TILE IS, 0 at a rank of
						// piers and 1 at the next. `PierEvery` of one or less
						// means a pier under every tile, so there is no bay
						// and the wall is simply solid.
						float Crown = 0.f;
						if (Span.PierEvery > 1)
						{
							const int32 Into = ((AlongTile % Span.PierEvery)
								+ Span.PierEvery) % Span.PierEvery;
							const float Across = static_cast<float>(Into)
								/ static_cast<float>(Span.PierEvery);
							// A HALF SINE, which is the shape of a round arch
							// and needs no table. Nought at each pier, one at
							// the middle of the bay.
							Crown = FMath::Sin(PI * Across);
						}
						// THE WALL NEVER CLOSES COMPLETELY. Even at the crown
						// a real arch carries a course or two of stone over
						// it, and at this distance a wall that vanished
						// entirely would blink the bridge's edge in and out
						// as the camera moved along it.
						const float Deep = Span.Spandrel
							* FMath::Lerp(1.f, 0.22f, Crown);
						const FVector Face = bTravelY
							? FVector(Half, TileSize * 0.5f, Deep * 0.5f)
							: FVector(TileSize * 0.5f, Half, Deep * 0.5f);
						// Hung from the deck's underside, which is where the
						// road's own stone stops.
						Box(Mid + FVector(0.f, 0.f,
							-DeckDrop - Deep * 0.5f), Face, 0.f);
					}
				}
			}

			if (!Span.Pier)
			{
				continue;
			}
			// A RANK OF PIERS EVERY FEW TILES, counted in WORLD tiles so that
			// the rhythm does not restart at a chunk boundary -- and on the
			// same rows the spandrel above closes, because a spandrel closes
			// where the stone goes down.
			if (!bPierRow)
			{
				continue;
			}
			const FBox PierBox = Span.Pier->GetBoundingBox();
			const float PierTall = PierBox.GetSize().Z;
			if (PierTall <= 1.f)
			{
				continue;
			}
			const float Under = Road - DeckDrop;
			// The bed, which is what the ground mesh was dug down to.
			const float Bed = Road - Span.Channel;
			const float Stand = Under - Bed;
			if (Piers == 0)
			{
				// SAID OUT LOUD, ONCE PER CHUNK. Whether a crossing has any
				// daylight under it is invisible in a photograph -- the deck
				// is over the gap and the camera looks down on it -- and an
				// evening went into squinting at pixels for an answer these
				// three numbers give exactly.
				UE_LOG(LogIntervalChunk, Log,
					TEXT("chunk %d,%d crossing at %d,%d: road %.0f, deck under "
					     "%.0f, bed %.0f, so %.0f cm of daylight"),
					OriginX, OriginY, OriginX + X, OriginY + Y,
					Road, Under, Bed, Stand);
			}
			if (Stand <= 20.f)
			{
				continue;   // nothing to hold up; the channel was not dug
			}
			const float PierScale = Stand / PierTall;
			// One at each side of the crossing, under the edge of the deck,
			// which is where the weight is and where they can be seen from.
			//
			// AND SET A LITTLE PROUD OF IT. A pier tucked exactly under a
			// six-metre deck is invisible from a camera that looks down on the
			// island: the deck is over it. Standing it out by a third of a
			// metre puts its cutwater in daylight, which is what says from
			// above that the road is being HELD UP rather than heaped up.
			const float Proud = 34.f;
			for (int32 Side = 0; Side < 2; ++Side)
			{
				const int32 Off = (Side == 0) ? AcrossLo : AcrossHi;
				const int32 PX = bTravelY ? X + Off : X;
				const int32 PY = bTravelY ? Y : Y + Off;
				if (!IsWetLocal(PX, PY))
				{
					continue;   // the bank: a pier here stands on dry ground
				}
				const float Out = (Side == 0 ? -Proud : Proud);
				const FVector Foot(
					(OriginX + PX + 0.5f) * TileSize + (bTravelY ? Out : 0.f),
					(OriginY + PY + 0.5f) * TileSize + (bTravelY ? 0.f : Out),
					Bed - PierBox.Min.Z * PierScale);
				Pool(PierPool, Span.Pier, Span.PierMaterial)
					->AddInstance(FTransform(Turn, Foot,
						FVector(PierScale)), true);
				++Piers;
				if (WideTiles == 1)
				{
					break;   // a single-tile crossing gets one pier, not two in a hole
				}
			}
		}
	}
	if (SpanMesh && WallV.Num() > 0)
	{
		SpanMesh->CreateMeshSection_LinearColor(0, WallV, WallT, WallN, WallUV,
			WallC, WallTan, false);
		// The deck's own material, so the wall is the same stone as the road
		// it stands on rather than a second opinion about what a bridge is
		// made of. The kit dressing put it there; nothing here picks a colour.
		UMaterialInterface* Stone = Span.DeckMaterial
			? Span.DeckMaterial.Get() : Span.Deck->GetMaterial(0);
		if (Stone)
		{
			SpanMesh->SetMaterial(0, Stone);
		}
	}
	if (Slabs > 0)
	{
		UE_LOG(LogIntervalChunk, Log,
			TEXT("chunk %d,%d spans: %d slabs, %d piers, %d parapet faces"),
			OriginX, OriginY, Slabs, Piers, WallT.Num() / 3);
	}
}

void AIntervalChunk::SetHideBuildings(TSet<int64>&& Keys)
{
	// The common case is "the same buildings as last frame", which is every
	// frame the citizen is standing still and most of the ones they are not.
	if (Keys.Num() == HideBuildings.Num() && HideBuildings.Includes(Keys))
	{
		return;
	}
	HideBuildings = MoveTemp(Keys);
	if (RoofKindsWere.Num() > 0)
	{
		BuildRoofs(RoofKindsWere, ThresholdWere);
	}
}

void AIntervalChunk::SetTilled(TSet<FIntPoint>&& Tiles)
{
	// Only when it actually changed: this is asked every frame and a field is
	// ploughed about as often as anything in this world ever changes.
	if (Tiles.Num() == Tilled.Num() && Tilled.Includes(Tiles))
	{
		return;
	}
	Tilled = MoveTemp(Tiles);
	if (ScatterWere.Num() > 0 || SpineWere.Mesh)
	{
		BuildScatter(ScatterWere, SpineWere);
	}
}

void AIntervalChunk::BuildRoofs(const TArray<FIntervalRoofKind>& RoofByCode,
	const TArray<uint8>& ThresholdByCode)
{
	if (RoofMesh)
	{
		RoofMesh->ClearAllMeshSections();
	}
	if (RoofByCode.Num() == 0 || !RoofMesh)
	{
		return;
	}

	const float TileSize = UIntervalGeometry::TileSize;
	const int32 SW = Stride;
	const int32 SH = Height + Skirt * 2;

	// ---- 1. THE FOOTPRINT, AS THE WORLD DESCRIBED IT ----
	// A room's floor is where the generator says a citizen is indoors, so the
	// footprint of every building is already here, told. Read it across the
	// whole skirt: a building may begin in the chunk next door, and its ridge
	// depends on how long it is over there too.
	BuildingKey.Init(0, Width * Height);
	RoofTop.Init(AIntervalGround::NoRoof, Width * Height);

	TArray<uint8> Roofed;
	Roofed.SetNumZeroed(SW * SH);
	for (int32 Y = 0; Y < SH; ++Y)
	{
		for (int32 X = 0; X < SW; ++X)
		{
			const uint8 Code = Codes[Y * SW + X];
			if (Code < RoofByCode.Num() && RoofByCode[Code].Material)
			{
				Roofed[Y * SW + X] = Code + 1;
			}
		}
	}
	// ...dilated by one, to carry the roof out over the walls the room stands
	// in. The wall ring is exactly the tiles touching an inside tile, and a
	// lane is two tiles away, so this covers the walls and stops at the street.
	TArray<uint8> Cover = Roofed;
	for (int32 Y = 0; Y < SH; ++Y)
	{
		for (int32 X = 0; X < SW; ++X)
		{
			if (Roofed[Y * SW + X])
			{
				continue;
			}
			uint8 Mark = 0;
			for (int32 DY = -1; DY <= 1 && !Mark; ++DY)
			{
				for (int32 DX = -1; DX <= 1; ++DX)
				{
					const int32 NX = X + DX, NY = Y + DY;
					if (NX < 0 || NY < 0 || NX >= SW || NY >= SH) { continue; }
					if (const uint8 Near = Roofed[NY * SW + NX]) { Mark = Near; break; }
				}
			}
			Cover[Y * SW + X] = Mark;
		}
	}

	// ---- 2. ONE BUILDING AT A TIME ----
	// Flood fill the covered tiles into connected buildings, so each gets its
	// own ridge. Two houses sharing a wall are one building to this, which is
	// what they are to look at as well: a terrace under one long roof.
	TArray<int32> Comp;
	Comp.Init(INDEX_NONE, SW * SH);
	struct FRoofBuilding { int32 MinX, MaxX, MinY, MaxY; uint8 Kind; float Rise; float Seed; int64 Key; float Eaves; float Base; };
	TArray<FRoofBuilding> Buildings;
	TArray<int32> Stack;
	for (int32 Y = 0; Y < SH; ++Y)
	{
		for (int32 X = 0; X < SW; ++X)
		{
			const int32 Start = Y * SW + X;
			if (!Cover[Start] || Comp[Start] != INDEX_NONE)
			{
				continue;
			}
			const int32 Id = Buildings.Num();
			FRoofBuilding B{ X, X, Y, Y, Cover[Start], 0.f, 0.f, 0, 0.f };
			Stack.Reset();
			Stack.Push(Start);
			Comp[Start] = Id;
			while (Stack.Num())
			{
				const int32 At = Stack.Pop();
				const int32 AX = At % SW, AY = At / SW;
				B.MinX = FMath::Min(B.MinX, AX); B.MaxX = FMath::Max(B.MaxX, AX);
				B.MinY = FMath::Min(B.MinY, AY); B.MaxY = FMath::Max(B.MaxY, AY);
				for (int32 DY = -1; DY <= 1; ++DY)
				{
					for (int32 DX = -1; DX <= 1; ++DX)
					{
						const int32 NX = AX + DX, NY = AY + DY;
						if (NX < 0 || NY < 0 || NX >= SW || NY >= SH) { continue; }
						const int32 N = NY * SW + NX;
						if (Cover[N] && Comp[N] == INDEX_NONE) { Comp[N] = Id; Stack.Push(N); }
					}
				}
			}
			// NO TWO HOUSES ALIKE, AND THE SAME TWO HOUSES IN EVERY WINDOW.
			//
			// The seed is a hash of the building's own corner IN WORLD TILES,
			// so it does not depend on which chunk drew it, on what order the
			// chunks arrived, or on anything this machine happens to know. A
			// house keeps its pitch and its thatch when you walk away and come
			// back, and two citizens describing the same roof describe the
			// same roof -- the rule the scatter plane is built on, applied to
			// a building instead of a fern.
			{
				const int32 WorldX = OriginX + B.MinX - Skirt;
				const int32 WorldY = OriginY + B.MinY - Skirt;
				B.Key = (static_cast<int64>(WorldX + 0x40000000) << 32)
					| static_cast<int64>(WorldY + 0x40000000);
				B.Seed = static_cast<float>(UIntervalGeometry::HashTile(WorldX, WorldY) % 255) / 254.f;

				const FIntervalRoofKind& K = RoofByCode[B.Kind - 1];
				// A village roofline is not one pitch repeated. Rafters were
				// cut to the timber that was there.
				B.Rise = K.RisePerTile * (0.84f + 0.34f * B.Seed);

				// WHERE THIS ROOF SITS. Not the kind's eaves height but this
				// building's, because the walls underneath took their height
				// from the same key through the same function. Ask it any
				// other way and the thatch floats a hand above the timber on
				// half the houses in the street.
				// A BIG BUILDING HAS BIG WALLS. Held at one height for everything,
				// a twenty-metre hall came out as a cottage wall under eight
				// metres of thatch -- a circus tent, not a barn. The rise is set
				// by the span the roof has to cross, so the eaves have to answer
				// the same span or the proportion runs away with the building.
				// Reads only the footprint, which the window worked out itself.
				const int32 Short = FMath::Min(B.MaxX - B.MinX, B.MaxY - B.MinY) + 1;
				// Gently: the walls the level draws stop at their own height and
				// the closure carries on above them, so every centimetre of
				// growth here is a centimetre of wall the window invented.
				const float Grown = FMath::Min(0.88f + 0.062f * Short, 1.50f);
				B.Eaves = K.EavesHeight * Grown * UIntervalGeometry::BuildingHeight(B.Key);

				// ---- AND THE GROUND IT STANDS ON ----
				//
				// EVERY ROOF AND EVERY WALL THIS FUNCTION BUILDS USED TO START
				// AT Z = 0, which was right for exactly as long as the island
				// was flat. The window draws the generator's own elevation
				// field now, and measured across one settlement the ground
				// runs from -567 to +158 while the roofs all sat between 687
				// and 849 -- so the same cottage was six metres tall on the
				// high side of Anchor and thirteen on the low side, and a
				// citizen standing on the ground was four metres below their
				// own floor. That is what "I still can't see my character
				// inside a building" turned out to be.
				//
				// ONE HEIGHT FOR THE WHOLE BUILDING, because a building is
				// levelled: it has a floor, and a floor is flat even where
				// the field under it is not.
				//
				// READ, NOT RECKONED. `BuildFloors` decided this before the
				// ground mesh was built, because the ground mesh had to ask
				// it too; working it out a second time here is how a wall
				// comes to meet its own floor at a seam. It is the mean of
				// the eased ground over the whole footprint, which beds the
				// building into a slope instead of hanging it off the height
				// of whichever tile happened to be in the middle.
				const int32 Mid = Local(B.MinX + (B.MaxX - B.MinX) / 2 - Skirt,
					B.MinY + (B.MaxY - B.MinY) / 2 - Skirt);
				B.Base = (FloorZ.IsValidIndex(Mid) && FloorZ[Mid] > NoFloor * 0.5f)
					? FloorZ[Mid]
					: UIntervalGeometry::GroundAt(
						OriginX + (B.MinX + B.MaxX) / 2 - Skirt,
						OriginY + (B.MinY + B.MaxY) / 2 - Skirt, false, false, true);
			}
			Buildings.Add(B);
		}
	}

	// ---- 3. THE RIDGE, AND THE HEIGHT OF EVERY CORNER ----
	// The ridge runs along the building's LONG axis, which is what a ridge
	// does: a hall is long and its roof is long. Height falls away from it in
	// a straight line to the eaves, which is a gable.
	auto HeightAtVertex = [&](int32 VX, int32 VY) -> float
	{
		// A corner is shared by up to four tiles; it belongs to whichever
		// building covers any of them. Taking the TALLEST answer keeps the
		// surface closed where two buildings meet.
		//
		// NOT MINUS ONE. Roof heights include the ground now and the ground
		// goes below nothing, so a starting value of -1 would have WON against
		// every real corner on the low side of a settlement and flattened the
		// roof to sea level there.
		float Best = AIntervalGround::NoRoof;
		for (int32 DY = -1; DY <= 0; ++DY)
		{
			for (int32 DX = -1; DX <= 0; ++DX)
			{
				const int32 TX = VX + DX, TY = VY + DY;
				if (TX < 0 || TY < 0 || TX >= SW || TY >= SH) { continue; }
				const int32 Id = Comp[TY * SW + TX];
				if (Id == INDEX_NONE) { continue; }
				const FRoofBuilding& B = Buildings[Id];
				const FIntervalRoofKind& K = RoofByCode[B.Kind - 1];
				const int32 SpanX = B.MaxX - B.MinX + 1;
				const int32 SpanY = B.MaxY - B.MinY + 1;
				const bool bRidgeAlongX = SpanX >= SpanY;
				const float Across = bRidgeAlongX ? static_cast<float>(VY) : static_cast<float>(VX);
				const float Lo = bRidgeAlongX ? B.MinY : B.MinX;
				const float Hi = (bRidgeAlongX ? B.MaxY : B.MaxX) + 1.f;
				const float Ridge = (Lo + Hi) * 0.5f;
				const float Half = (Hi - Lo) * 0.5f;
				const float Up = FMath::Min(
					FMath::Max(0.f, Half - FMath::Abs(Across - Ridge)) * B.Rise, K.MaxRise);
				Best = FMath::Max(Best, B.Base + B.Eaves + Up);
			}
		}
		return Best;
	};

	// ---- 4. THE SURFACE, THE GABLE ENDS, AND WHAT HOLDS IT UP ----
	//
	// Two surfaces, because they are two materials. The thatch is one; the
	// DAUB is the closure under the eaves, and it exists because a roof needs
	// something to stand on and the world does not always say what.
	//
	// The world tells us which tiles are roofed and, separately, where walls
	// stand. Those two do not have to agree, and at a hall or a barn they do
	// not: the roof covers twenty tiles and the world names walls on six of
	// them. Drawn straight, that is a roof hanging in the air with daylight
	// under it all the way through -- which is exactly what it was doing.
	//
	// So the window closes the ROOF'S OWN perimeter down to the ground. That
	// invents nothing: the world said this ground is roofed, and a roof stands
	// on something. Where the world does name a wall, the wall is drawn in
	// front of this and this is never seen -- which is why it is set back a
	// little from the tile edge rather than sitting exactly on it, where the
	// two would fight for the same pixels.
	struct FSurface
	{
		TArray<FVector> Vertices;
		TArray<int32> Triangles;
		TArray<FVector> Normals;
		TArray<FVector2D> UVs;
		TArray<FLinearColor> Colors;
		TArray<FProcMeshTangent> Tangents;
	};
	FSurface Roof;
	FSurface Daub;
	FSurface Doors;
	const FIntervalRoofKind* Kind = nullptr;
	auto Corner = [&](float VX, float VY, float Z) -> FVector
	{
		// Local to the chunk actor, which stands at the interior corner.
		// Takes fractions because the daub is set back from the tile edge.
		return FVector((VX - Skirt) * TileSize, (VY - Skirt) * TileSize, Z);
	};
	// The building's seed rides in the vertex colour, which is how the roof
	// material knows that THIS house is greyer and mossier than the one beside
	// it without anything having to look a building up.
	float QuadSeed = 0.f;
	// How tall the wall this quad belongs to is, in tens of metres, so that
	// the frame material can put the wall plate at the TOP of the wall instead
	// of at a fixed height. Without it a five-metre hall was framed for the
	// first two and a half and blank above, which is what gave the big
	// buildings their packing-crate look.
	float QuadTop = 0.f;
	auto QuadOn = [&](FSurface& S, const FVector& A, const FVector& B, const FVector& C, const FVector& D,
		bool bWall = false)
	{
		const int32 Base = S.Vertices.Num();
		S.Vertices.Add(A); S.Vertices.Add(B); S.Vertices.Add(C); S.Vertices.Add(D);
		FVector N = FVector::CrossProduct(B - A, D - A).GetSafeNormal();
		if (N.IsNearlyZero()) { N = FVector::UpVector; }
		// The seed in the red channel, and a ZERO BLUE as the flag that says so.
		// A static mesh's vertex colour defaults to opaque white, so blue < 0.5
		// is a reliable way for a material to tell "this vertex was built by the
		// window and carries a building seed" from "this is an instanced cube
		// and the seed arrives as per-instance data" -- and one material can
		// then draw both without either side knowing about the other.
		const FLinearColor Tag(QuadSeed, bWall ? QuadTop : 1.f - QuadSeed, 0.f, 1.f);
		// A wall needs a tangent that lies IN it. The roof's flat (1,0,0) is
		// parallel to the normal on a north-south wall, which collapses the
		// basis and leaves the frame material reading a garbage axis.
		const FProcMeshTangent Tan = bWall
			? FProcMeshTangent((B - A).GetSafeNormal(), false)
			: FProcMeshTangent(1, 0, 0);
		for (int32 i = 0; i < 4; ++i) { S.Normals.Add(N); S.Colors.Add(Tag); S.Tangents.Add(Tan); }
		S.UVs.Add(FVector2D(0, 0)); S.UVs.Add(FVector2D(1, 0)); S.UVs.Add(FVector2D(1, 1)); S.UVs.Add(FVector2D(0, 1));
		// WOUND THE SAME WAY AS THE GROUND, which is the only reference in this
		// file that was known to face the right way. Wound the other way the
		// roof is front-facing DOWNWARD: you see straight into every building
		// from outside and see a complete thatch ceiling from inside, which is
		// exactly what it did. The supplied normal still points up, so the
		// surface is lit by the sky it faces -- geometry decides what is drawn,
		// the normal decides how it is lit, and they are allowed to differ.
		S.Triangles.Add(Base); S.Triangles.Add(Base + 2); S.Triangles.Add(Base + 1);
		S.Triangles.Add(Base); S.Triangles.Add(Base + 3); S.Triangles.Add(Base + 2);
	};
	auto Quad = [&](const FVector& A, const FVector& B, const FVector& C, const FVector& D)
	{
		QuadOn(Roof, A, B, C, D);
	};

	// Only the interior is drawn; the skirt was read, never rendered.
	for (int32 Y = Skirt; Y < Height + Skirt; ++Y)
	{
		for (int32 X = Skirt; X < Width + Skirt; ++X)
		{
			const uint8 Marked = Cover[Y * SW + X];
			if (!Marked)
			{
				continue;
			}
			if (!Kind) { Kind = &RoofByCode[Marked - 1]; }
			const FIntervalRoofKind& K = RoofByCode[Marked - 1];
			const int32 Id = Comp[Y * SW + X];
			{
				QuadSeed = (Id != INDEX_NONE) ? Buildings[Id].Seed : 0.f;
				BuildingKey[(Y - Skirt) * Width + (X - Skirt)] =
					(Id != INDEX_NONE) ? Buildings[Id].Key : 0;
			}
			// ---- EXCEPT WHATEVER STANDS BETWEEN THE EYE AND THE CITIZEN ----
			//
			// Its roof, its walls and its door are simply not built. The tile
			// keeps its `BuildingKey` above, which is what the rain asks to
			// know whether somebody is sheltered, so going indoors still stops
			// the weather even though the roof over them is not drawn.
			const float H00 = HeightAtVertex(X, Y);
			const float H10 = HeightAtVertex(X + 1, Y);
			const float H11 = HeightAtVertex(X + 1, Y + 1);
			const float H01 = HeightAtVertex(X, Y + 1);

			// THE HIGHEST OF THE FOUR CORNERS, for whatever has to stand on
			// this roof. A chimney passing through a slope must clear the
			// upper edge of the tile it comes through, not the average of it,
			// or it disappears into the thatch on the ridge side.
			//
			// ---- AND IT IS RECORDED EVEN WHEN THE ROOF IS NOT DRAWN ----
			//
			// This sat BELOW the hide test, so lifting a roof wiped the height
			// of the roof it lifted, for exactly the one building the citizen
			// was standing in. The rain was never affected: it asks
			// `BuildingKey`, which is set above and stays. The LAMP asks this,
			// and only burns where there is a roof, so it went out the moment
			// somebody stepped through a door and came back on when they left.
			// How high the roof stands is a fact about the world; whether it is
			// drawn is a fact about the camera, and only the second belongs
			// below the test.
			if (RoofTop.Num() == Width * Height)
			{
				RoofTop[(Y - Skirt) * Width + (X - Skirt)] =
					FMath::Max(FMath::Max(H00, H10), FMath::Max(H11, H01));
			}

			// Not built rather than hidden: these are three mesh sections for
			// a whole chunk and there is no way to hide one house's share of
			// them. `SetHideBuildings` runs this again when the citizen crosses
			// a threshold, which is a few times a minute at worst and only ever
			// for the one chunk that answered.
			if (HideBuildings.Num() > 0 && Id != INDEX_NONE
				&& HideBuildings.Contains(Buildings[Id].Key))
			{
				continue;
			}

			// The slope itself, pushed out a little at the eaves so the roof
			// oversails the wall the way a thatched one does.
			const float O = K.Overhang / TileSize;
			const float X0 = X - (Cover[Y * SW + FMath::Max(X - 1, 0)] ? 0.f : O);
			const float X1 = X + 1 + (Cover[Y * SW + FMath::Min(X + 1, SW - 1)] ? 0.f : O);
			const float Y0 = Y - (Cover[FMath::Max(Y - 1, 0) * SW + X] ? 0.f : O);
			const float Y1 = Y + 1 + (Cover[FMath::Min(Y + 1, SH - 1) * SW + X] ? 0.f : O);
			Quad(
				FVector((X0 - Skirt) * TileSize, (Y0 - Skirt) * TileSize, H00),
				FVector((X1 - Skirt) * TileSize, (Y0 - Skirt) * TileSize, H10),
				FVector((X1 - Skirt) * TileSize, (Y1 - Skirt) * TileSize, H11),
				FVector((X0 - Skirt) * TileSize, (Y1 - Skirt) * TileSize, H01));

			// THE GABLE. Where the roof stops, the wall below it has to reach
			// up to meet the slope, or you can see under the eaves and into an
			// empty building. On the long sides both corners sit at eaves
			// height and this face has no area; at the ends it is the triangle
			// that makes the building a gable rather than a shed.
			// The wall's OWN height, and where the bottom of it sits. Kept
			// apart on purpose: `Tall` is what the frame material is told (it
			// wants a height, not a level) and `Base` is the ground this
			// building was levelled onto. See the note by B.Base above.
			const float Tall = (Id != INDEX_NONE) ? Buildings[Id].Eaves : K.EavesHeight;
			const float Base = (Id != INDEX_NONE) ? Buildings[Id].Base : 0.f;
			const float Eaves = Base + Tall;

			// Set back from the tile edge, so that where a wall IS drawn the
			// daub is inside it instead of fighting it for the same pixels;
			// and carried below zero so the ground's relief cannot open a
			// gap of daylight along the bottom of a house.
			const float In = K.Inset / TileSize;
			const float Sill = Base - K.Footing;
			QuadTop = Tall / 1000.f;

			// ---- IS THIS TILE A WAY IN? ----
			// Measured, not assumed. Of the tiles ringing a roofed room, every
			// one that carries a wall stands on raw country or a trail; the one
			// or two that carry nothing stand on flagstone. The generator lays a
			// threshold where the door is, and the level names which grounds
			// count. Close one of those and the house is walled shut, which is
			// what every house on the island was.
			const uint8 Here = Codes[Y * SW + X];
			// ONE DOOR PER THRESHOLD, not one per exposed face. A threshold on
			// a corner has two faces open to the street, and cutting both put
			// a door through each and left the corner of the house missing.
			bool bWay = ThresholdByCode.IsValidIndex(Here) && ThresholdByCode[Here] != 0;

			// A doorway is a hole with a head on it: a jamb either side, a
			// lintel over, and the leaf set back in the reveal.
			//
			// THE LEAF LIES IN THE WALL, NOT ACROSS IT. Hung on a jamb and
			// swung open it was a slab standing out in the street at an angle,
			// the wrong size for the hole it came out of and attached to
			// nothing -- a door in the way that a plank leaning on a shed is a
			// door. Set back a hand's breadth into the opening it reads as
			// what it is, and the reveal gives it somewhere to sit.
			//
			// Not every house is shut up. Which ones stand open is the
			// building's own number, so it is the same door open in every
			// window and the same one shut.
			const float HalfW = FMath::Min(K.DoorWidth, TileSize - 40.f) * 0.5f / TileSize;
			const float Head = Base + FMath::Min(K.DoorHeight, Tall - 30.f);
			const float Reveal = 13.f / TileSize;
			const bool bAjar = (Id != INDEX_NONE)
				&& UIntervalGeometry::BuildingUnit(Buildings[Id].Key, 7u) > 0.66f;

			auto Opening = [&](bool bAlongY, float Fixed, float Inward,
				float A0, float A1, bool bFlip)
			{
				auto At = [&](float Along, float Z, float Off = 0.f)
				{
					const float F = Fixed + Inward * Off;
					return bAlongY ? Corner(F, Along, Z) : Corner(Along, F, Z);
				};
				const float Mid = (A0 + A1) * 0.5f;
				const float L0 = Mid - HalfW, L1 = Mid + HalfW;

				// ---- THE SURROUND: A JAMB EITHER SIDE, A HEAD, AND A STEP ----
				//
				// The opening above is a HOLE, and that is all it was: the daub
				// stops, the dark starts, and nothing says where the wall ends.
				// Photographed in daylight a doorway read as a rectangle
				// somebody had painted on the plaster, which is the whole of
				// what was wrong with it.
				//
				// A real opening is framed. Two posts standing a little proud,
				// a beam across the head, and a step at the foot, all in the
				// leaf's own timber: the frame is what gives the hole a shadow
				// line and a thickness, and the step is what stops it running
				// into the mud. None of it is decoration -- it is the three
				// pieces a doorway is actually built out of.
				//
				// Wound BOTH WAYS, on purpose. Which face of the building a
				// given call is drawing is decided three branches away, and a
				// six-centimetre trim that came out inside-out would be
				// invisible from the one side that matters. Both windings cost
				// four triangles a piece and cannot be wrong.
				if (K.DoorMaterial)
				{
					const float Jamb = FMath::Min(15.f / TileSize, HalfW * 0.6f);
					const float Proud = -6.f / TileSize;
					const float Step = 9.f;
					const float Beam = FMath::Min(16.f, FMath::Max(0.f, Eaves - Head));
					auto Band = [&](float Lo, float Hi, float Z0, float Z1)
					{
						if (Hi <= Lo || Z1 <= Z0) { return; }
						QuadOn(Doors, At(Lo, Z0, Proud), At(Hi, Z0, Proud),
							At(Hi, Z1, Proud), At(Lo, Z1, Proud), true);
						QuadOn(Doors, At(Lo, Z1, Proud), At(Hi, Z1, Proud),
							At(Hi, Z0, Proud), At(Lo, Z0, Proud), true);
					};
					Band(L0 - Jamb, L0, Base + Step, Head);            // the posts
					Band(L1, L1 + Jamb, Base + Step, Head);
					Band(L0 - Jamb, L1 + Jamb, Head, Head + Beam);     // the head
					Band(L0 - Jamb, L1 + Jamb, Base, Base + Step);     // the step
				}

				if (bFlip)
				{
					QuadOn(Daub, At(L0, Sill), At(A0, Sill), At(A0, Head), At(L0, Head), true);
					QuadOn(Daub, At(A1, Sill), At(L1, Sill), At(L1, Head), At(A1, Head), true);
					QuadOn(Daub, At(A1, Head), At(A0, Head), At(A0, Eaves), At(A1, Eaves), true);
					if (K.DoorMaterial && !bAjar)
					{
						QuadOn(Doors, At(L1, Base, Reveal), At(L0, Base, Reveal),
							At(L0, Head, Reveal), At(L1, Head, Reveal), true);
					}
				}
				else
				{
					QuadOn(Daub, At(A0, Sill), At(L0, Sill), At(L0, Head), At(A0, Head), true);
					QuadOn(Daub, At(L1, Sill), At(A1, Sill), At(A1, Head), At(L1, Head), true);
					QuadOn(Daub, At(A0, Head), At(A1, Head), At(A1, Eaves), At(A0, Eaves), true);
					if (K.DoorMaterial && !bAjar)
					{
						QuadOn(Doors, At(L0, Base, Reveal), At(L1, Base, Reveal),
							At(L1, Head, Reveal), At(L0, Head, Reveal), true);
					}
				}
			};

			if (!Cover[Y * SW + FMath::Max(X - 1, 0)] || X == 0)
			{
				Quad(Corner(X, Y + 1, Eaves), Corner(X, Y, Eaves), Corner(X, Y, H00), Corner(X, Y + 1, H01));
				if (bWay) { bWay = false; Opening(true, X + In, 1.f, Y + 1, Y, true); }
				else
				{
					QuadOn(Daub, Corner(X + In, Y + 1, Sill), Corner(X + In, Y, Sill),
						Corner(X + In, Y, Eaves), Corner(X + In, Y + 1, Eaves), true);
				}
			}
			if (!Cover[Y * SW + FMath::Min(X + 1, SW - 1)] || X == SW - 1)
			{
				Quad(Corner(X + 1, Y, Eaves), Corner(X + 1, Y + 1, Eaves), Corner(X + 1, Y + 1, H11), Corner(X + 1, Y, H10));
				if (bWay) { bWay = false; Opening(true, X + 1 - In, -1.f, Y, Y + 1, false); }
				else
				{
					QuadOn(Daub, Corner(X + 1 - In, Y, Sill), Corner(X + 1 - In, Y + 1, Sill),
						Corner(X + 1 - In, Y + 1, Eaves), Corner(X + 1 - In, Y, Eaves), true);
				}
			}
			if (!Cover[FMath::Max(Y - 1, 0) * SW + X] || Y == 0)
			{
				Quad(Corner(X, Y, Eaves), Corner(X + 1, Y, Eaves), Corner(X + 1, Y, H10), Corner(X, Y, H00));
				if (bWay) { bWay = false; Opening(false, Y + In, 1.f, X, X + 1, false); }
				else
				{
					QuadOn(Daub, Corner(X, Y + In, Sill), Corner(X + 1, Y + In, Sill),
						Corner(X + 1, Y + In, Eaves), Corner(X, Y + In, Eaves), true);
				}
			}
			if (!Cover[FMath::Min(Y + 1, SH - 1) * SW + X] || Y == SH - 1)
			{
				Quad(Corner(X + 1, Y + 1, Eaves), Corner(X, Y + 1, Eaves), Corner(X, Y + 1, H01), Corner(X + 1, Y + 1, H11));
				if (bWay) { bWay = false; Opening(false, Y + 1 - In, -1.f, X + 1, X, true); }
				else
				{
					QuadOn(Daub, Corner(X + 1, Y + 1 - In, Sill), Corner(X, Y + 1 - In, Sill),
						Corner(X, Y + 1 - In, Eaves), Corner(X + 1, Y + 1 - In, Eaves), true);
				}
			}
		}
	}

	if (Roof.Vertices.Num() == 0)
	{
		return;
	}
	RoofMesh->CreateMeshSection_LinearColor(0, Roof.Vertices, Roof.Triangles,
		Roof.Normals, Roof.UVs, Roof.Colors, Roof.Tangents, false);
	if (Daub.Vertices.Num() > 0)
	{
		RoofMesh->CreateMeshSection_LinearColor(1, Daub.Vertices, Daub.Triangles,
			Daub.Normals, Daub.UVs, Daub.Colors, Daub.Tangents, false);
	}
	if (Doors.Vertices.Num() > 0)
	{
		RoofMesh->CreateMeshSection_LinearColor(2, Doors.Vertices, Doors.Triangles,
			Doors.Normals, Doors.UVs, Doors.Colors, Doors.Tangents, false);
	}
	if (Kind)
	{
		RoofMesh->SetMaterial(0, Kind->Material);
		RoofMesh->SetMaterial(1, Kind->WallMaterial ? Kind->WallMaterial.Get() : Kind->Material.Get());
		if (Kind->DoorMaterial) { RoofMesh->SetMaterial(2, Kind->DoorMaterial); }
		RoofMesh->SetCastShadow(Kind->bCastShadow);
	}
}
