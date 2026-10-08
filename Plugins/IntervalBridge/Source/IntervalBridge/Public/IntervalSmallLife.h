// Copyright interval.
//
// THE SMALL LIVING THINGS THAT ARE SCENERY, NOT MOBS.
//
// The world has a bestiary -- wolves, goblins, a dragon -- and every one of
// them is a thing the world knows about: it has a position the engine keeps, a
// kind, hit points, and a citizen may swing at it. This actor holds the other
// sort entirely. Nothing here is in any frame, nothing here can be struck, and
// nothing here is told to anybody. It is the window noticing that a fen with
// no frog in it is a photograph of a fen.
//
// Asked for in the same line as the birds and the crows: "maybe a frog here
// and there hopping around on the ground in the fens".
//
// KEYED TO THE GROUND, like the voices are. Frogs belong to the fens and to
// nowhere else, and a frog on a mountain is the same fault as one birdsong
// playing over every country. The ground's own word decides, which is the
// world's word and not the window's guess.
//
// AND A HOP IS A WHOLE-BODY MOTION, which is why there is no rig. A frog does
// not articulate its way across a puddle, it is thrown and it lands. An arc in
// C++ is both cheaper and more truthful than a skeleton would be, and it is
// the same argument the birds' wing-beat makes from the other side: that one
// IS an articulation, so it lives in a vertex shader.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IntervalSmallLife.generated.h"

class UInstancedStaticMeshComponent;
class UIntervalBridgeSubsystem;
class UIntervalLook;
class AIntervalGround;

UCLASS()
class INTERVALBRIDGE_API AIntervalSmallLife : public AActor
{
	GENERATED_BODY()

public:
	AIntervalSmallLife();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<UIntervalLook> Look;

private:
	UPROPERTY(Transient)
	TObjectPtr<UInstancedStaticMeshComponent> Frogs;

	UPROPERTY(Transient)
	TObjectPtr<UIntervalBridgeSubsystem> Bridge;

	UPROPERTY(Transient)
	TObjectPtr<AIntervalGround> Ground;

	/**
	 * ONE FROG, which spends most of its life sitting still.
	 *
	 * `Rests` is how long it will sit before the next hop, and it is most of
	 * the animal: a frog that hops continuously is a bouncing ball, and the
	 * sitting is what makes the hop worth seeing. `Through` runs 0 to 1 across
	 * one hop and is negative while it waits.
	 */
	struct FFrog
	{
		FVector From = FVector::ZeroVector;
		FVector To = FVector::ZeroVector;
		float Through = -1.f;
		float Rests = 0.f;
		float Yaw = 0.f;
		float Size = 1.f;
	};
	TArray<FFrog> Hoppers;

	/** Where the pool was gathered, so it is rebuilt when a citizen leaves it. */
	FIntPoint Around = FIntPoint(-9999, -9999);

	/** How long since the ground underfoot was asked about. */
	float Asked = 0.f;

	/** The same for the butterflies, which ask about different ground. One
	 *  timer for both meant the wings could only ever be gathered on the exact
	 *  frame the frogs were, which is most of the time never. */
	float AskedWings = 0.f;

	/** How long until this actor may complain again about being idle. */
	float Quiet = 0.f;

	/** Find wet ground near the citizen and put frogs on it. */
	void Gather(int32 TileX, int32 TileY);

	/** Send one frog somewhere else, or sit it down again. */
	void Leap(FFrog& Who, float DeltaSeconds);

	// ---- AND THE OTHER HALF OF A PLACE BEING ALIVE ----
	//
	// "We added birds in the sky for atmosphere, but I think we should add like
	// butterflies (closer to the ground so they're actually visible) in the
	// farmlands and stuff like that too."
	//
	// A crow is eight metres up and is a silhouette against the sky: it is
	// weather, more or less. This is at knee height in the grass a citizen is
	// standing in, which is the thing you actually walk through, and it is why
	// the open country gets it and the fens keep the frogs.
	//
	// TWO SPECIES, TWO COMPONENTS, ONE MESH. An instanced component carries one
	// material, so a white and a bright one are two components over the same
	// eight-centimetre mesh rather than a material that reads per-instance
	// data. Those two are what is actually over a field.

	UPROPERTY(Transient)
	TObjectPtr<UInstancedStaticMeshComponent> Whites;

	UPROPERTY(Transient)
	TObjectPtr<UInstancedStaticMeshComponent> Brights;

	/**
	 * ONE BUTTERFLY, which is never still for long.
	 *
	 * The opposite animal to the frog above it in every way that matters here.
	 * A frog is still for nine seconds and then is thrown; this drifts
	 * constantly and its stillness is the rare thing. So there is no `From` and
	 * `To`: there is a heading it wanders, a bob it rides, and a roll that is
	 * the wingbeat.
	 *
	 * THE ROLL IS THE FLAP, and it is why the mesh's wings are flat. Rolling
	 * the whole body about its forward axis takes the wings from full face to
	 * an edge and back, which from a camera looking down is a wingbeat. It
	 * costs nothing beyond the transform that was being written anyway, and it
	 * is the reason this needs no vertex animation the way the birds do.
	 */
	struct FFlutter
	{
		FVector At = FVector::ZeroVector;
		float Ground = 0.f;        // the height of the land under it
		float Yaw = 0.f;           // where it is drifting
		float Speed = 40.f;        // cm a second, which is slow
		float Height = 60.f;       // what it is bobbing around, above the land
		float Bob = 0.f;           // phase
		float BobRate = 4.f;
		float BobDeep = 18.f;      // how far up and down
		float Roll = 0.f;          // phase of the wingbeat
		float RollRate = 22.f;
		float Settled = 0.f;       // seconds left sitting on the ground
		float Until = 0.f;         // seconds until the next change of mind
		float Size = 1.f;
		int32 Slot = 0;            // which instance, in its own component
		uint8 bBright = 0;         // which of the two species
	};
	TArray<FFlutter> Flutters;

	/** Where the butterflies were gathered. Separate from the frogs' tile
	 *  because the two want different ground and may be gathered on different
	 *  intervals; sharing it meant a meadow beside a fen got one or the other. */
	FIntPoint Afield = FIntPoint(-9999, -9999);

	/** Open flowering ground near the citizen, with butterflies over it. */
	void GatherWings(int32 TileX, int32 TileY);

	/** Drift one butterfly, or set it down for a moment. */
	void Flutter(FFlutter& Who, float DeltaSeconds);

	/** Whether anything should be flying at all: not at night, not in the
	 *  rain, and not in winter. Kept in one place because all three are the
	 *  same question and a butterfly out in any of them is a bug people see. */
	bool bFlyingWeather() const;

	// ---- AND THE BIRDS THAT ARE ON THE GROUND RATHER THAN IN THE SKY ----
	//
	// The shore has gulls you can hear and never see, and a town square had
	// meadow songbirds purely because nobody had chosen anything for it. Both
	// are the same creature as far as this actor is concerned: a bird standing
	// on the ground that LIFTS WHEN YOU COME NEAR.
	//
	// That last part is why this is worth building rather than scattering more
	// scenery. The frogs ignore a citizen and so do the butterflies; nothing
	// small in this window has ever reacted to anybody. A flock of gulls that
	// goes up as you walk into it makes the place aware of you, which is a
	// different kind of alive from motion alone.
	//
	// ONE COMPONENT, NOT TWO, because a citizen stands on one ground at a time
	// and a shore is never a market square. The mesh is swapped when the
	// country under them changes, the way the sky flock's is.

	UPROPERTY(Transient)
	TObjectPtr<UInstancedStaticMeshComponent> Standing;

	/** ONE BIRD ON THE GROUND. `Flew` is negative while it is stood there and
	 *  runs 0 to 1 across one flight, which is the same shape the frog's hop
	 *  uses -- and for the same reason: a thing that is thrown and lands wants
	 *  an arc, not a rig. */
	struct FStander
	{
		FVector From = FVector::ZeroVector;
		FVector To = FVector::ZeroVector;
		float Flew = -1.f;
		float Yaw = 0.f;
		float Size = 1.f;
		float Fidget = 0.f;     // how long until it turns on the spot
	};
	TArray<FStander> Standers;

	/** Where they were gathered, and which bird they are. */
	FIntPoint Ashore = FIntPoint(-9999, -9999);
	FName StandingKind;
	float AskedStanding = 0.f;

	// ---- AND THE LEAVES, WHICH ARE THE SEASON MADE VISIBLE ----
	//
	// The world has computed `spring`, `autumn` and `winter` since the sky was
	// written and nothing in this window had ever read them, so the seasons
	// changed the date and nothing else. The butterflies leaving the meadows in
	// winter was the first thing that did; this is the second.
	//
	// SCALED BY THE SEASON, NOT SWITCHED BY IT. `autumn` is a triangular petal
	// that climbs to one in the middle of the season and falls away either
	// side, so the count is read off it directly: a few leaves as it turns, a
	// drift of them at the height of it, and none for most of the year. A
	// boolean would have thrown that shape away and made autumn a light switch.

	UPROPERTY(Transient)
	TObjectPtr<UInstancedStaticMeshComponent> LeavesGold;

	UPROPERTY(Transient)
	TObjectPtr<UInstancedStaticMeshComponent> LeavesRust;

	/**
	 * ONE LEAF, FALLING OR LYING.
	 *
	 * A falling leaf is not a dropped stone and the difference is entirely in
	 * the swing: it rocks from side to side as it goes, because it is a plate
	 * presenting alternate faces to the air. `Swing` is that pendulum and it is
	 * most of what makes this read as a leaf rather than as debris.
	 *
	 * `Lying` is how long it has been on the ground. They are not destroyed and
	 * remade -- the same instance is carried back up to the canopy when its
	 * time is out, so the count never changes and nothing is ever allocated
	 * while a citizen is standing in the wood.
	 */
	struct FLeaf
	{
		FVector At = FVector::ZeroVector;
		float Ground = 0.f;
		float Fall = 50.f;      // cm a second
		float Swing = 0.f;      // phase of the side-to-side rock
		float SwingRate = 2.2f;
		float SwingWide = 30.f; // cm either side
		float Drift = 0.f;      // which way the swing lies
		float Spin = 0.f;       // turning about its own stalk as it goes
		float SpinRate = 60.f;
		float Lying = -1.f;     // negative while it is still in the air
		float Rest = 0.f;       // how long it lies before it is carried back up
		float Size = 1.f;
		int32 Slot = 0;
		uint8 bRust = 0;
	};
	TArray<FLeaf> Leaves;

	FIntPoint Awood = FIntPoint(-9999, -9999);
	float AskedLeaves = 0.f;
	int32 LeavesWanted = 0;

	/** Find woodland near the citizen and start leaves falling over it. */
	void GatherLeaves(int32 TileX, int32 TileY);

	/** Carry one leaf down, or pick it up and start it again. */
	void Fall(FLeaf& Who, float DeltaSeconds);

	/** Put birds on the shore or in the square, whichever is underfoot. */
	void GatherStanders(int32 TileX, int32 TileY);

	/** Stand, turn about, or go up because somebody walked into them. */
	void Startle(FStander& Who, const FVector& Citizen, float DeltaSeconds);
};
