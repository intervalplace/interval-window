// IntervalStructures.h -- the things the world says are standing there.
//
// Walls, palisades, hedges, fences, railings, signposts, hearths, wells, and
// every gatherable: all of them arrive in a frame as an id, a position and a
// word. This actor draws them and knows nothing else about them.
//
// WHY THERE IS NO SWITCH IN HERE. IntervalTypes.h puts it plainly: a renderer
// may switch on the world's strings to choose a mesh, but it may never decide
// what one MEANS. A `switch (Kind)` in C++ is the second kind of decision
// wearing the clothes of the first -- it fixes, in a compiled binary, which
// words exist. The generator adds words (v7 added three ground kinds and two
// isles nobody had drawn), and a build that has to be recompiled to see a new
// one is a window that goes stale between foundings.
//
// So the mapping from word to mesh is DATA, edited in the level. C++ writes
// down no word at all. A word with no entry simply is not drawn, which is the
// honest result for a thing this window has never heard of -- and it is
// visible in the log rather than silent.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IntervalTypes.h"
#include "IntervalStructures.generated.h"

class UInstancedStaticMeshComponent;
class UIntervalBridgeSubsystem;
class AIntervalGround;
class UStaticMesh;
class UMaterialInterface;

/**
 * One piece of a thing that is not a single shape.
 *
 * A well is a drum of stone, a pair of posts, a beam across them and a little
 * roof; a fountain is a basin, a plinth and a spout. Drawn as ONE primitive
 * each they read as a barrel and a bollard, which is what they were doing.
 *
 * Nothing in C++ knows what a well looks like. A level says that the word
 * `well` is drawn as these five pieces at these offsets, exactly as it
 * already says that the word `wall` is drawn as a scaled cube -- so a world
 * that has never heard of wells costs this window nothing, and a world that
 * grows a new word needs no build.
 */
USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalPropPart
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<UStaticMesh> Mesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<UMaterialInterface> Material;

	/** Where this piece sits relative to the node's own tile centre, in centimetres. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	FVector Offset = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	FRotator Rotation = FRotator::ZeroRotator;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	FVector Scale = FVector(1.f, 1.f, 1.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	bool bCastShadow = true;

	/**
	 * A bone to hang this on, for the pieces that go on a person rather than
	 * on the ground: `hand_r` for what they are holding, `head` for a hood,
	 * `pelvis` for a skirt. Left empty -- which is every prop on the island --
	 * the piece sits where its offset puts it and nothing looks for a bone.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	FName Bone;
};

/**
 * Several pieces that travel together.
 *
 * A hatchet is a haft AND a head; drawn as a haft alone it is a stick, which
 * is what every tool on the island was. One piece was enough for a barrel and
 * is not enough for anything somebody made. A map cannot hold an array
 * directly, which is the only reason this is a struct rather than a list.
 */
USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalKit
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TArray<FIntervalPropPart> Pieces;
};

/**
 * ONE CLIP, FOR A THING THAT CARRIES NOTHING.
 *
 * `FIntervalMotion` is the citizens' row and it holds what they are HOLDING --
 * the hatchet in the swing, the rod in the cast -- which means it has to know
 * about prop parts, which means IntervalMotion.h includes IntervalStructures.h
 * and a beast table declared over there cannot come back the other way without
 * a circular include.
 *
 * It is also more than a wolf needs. A wolf has a clip, a speed and whether it
 * loops. This is that, and the smaller struct is the honest one.
 */
USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalBeastMotion
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<class UAnimSequence> Anim;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0.05"))
	float Rate = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	bool bLoop = true;

	/**
	 * THE GROUND SPEED THIS CLIP WAS CUT FOR, in centimetres a second.
	 *
	 * A walk cycle is a fixed number of steps a second. Play it while the
	 * figure crosses the ground at some other speed and the feet slide -- and
	 * they slide in BOTH directions here, because a citizen in this world
	 * moves a whole tile in an interval when they are going somewhere and not
	 * at all when they are not, with nothing in between.
	 *
	 * So the clip is sped up and slowed down to match how fast the figure is
	 * actually travelling. Zero means "play it as authored", which is right
	 * for everything that is not locomotion: a hatchet swing is not faster
	 * because its owner was running a moment ago.
	 *
	 * It cannot be derived. These clips carry no root motion, so there is no
	 * distance in them to divide by; it is a number to set by watching the
	 * feet, and two hundred -- one tile an interval -- is where it starts
	 * because that is the speed everything was tuned at before this existed.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0"))
	float Pace = 0.f;
};

/** How to draw one word the world uses. Every field is a look, never a meaning. */
/**
 * ONE STAGE OF SOMETHING THAT GROWS.
 *
 * See FIntervalPropKind::Stages. `At` is the fraction of the way from sown to
 * ripe at which this stage takes over, so 0 is bare ground and 1 is ready to
 * cut.
 */
USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalPropStage
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval",
		meta = (ClampMin = "0", ClampMax = "1"))
	float At = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TArray<FIntervalPropPart> Parts;
};

USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalPropKind
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<UStaticMesh> Mesh;

	/**
	 * A skeleton, for the things that move on their own. Set, this is drawn
	 * instead of the static mesh, one component per creature rather than one
	 * instance in a pool -- the cost of a skeleton is the point of it, and
	 * there are a dozen beasts in view where there are ten thousand walls.
	 * The motions come from the same table the citizens use.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<class USkeletalMesh> Skeletal;

	/**
	 * THE OTHER ONES IT MIGHT BE.
	 *
	 * A wood in which every tree is the same tree is a wallpaper, and that is
	 * what one mesh per word gives: the kit ships five common trees, five
	 * pines, five twisted and five dead, and a word could name exactly one of
	 * them. Listed here, a node picks one by ITS OWN ID -- so the crooked oak
	 * at the ford is the same crooked oak in every window and tomorrow, which
	 * is the property that makes it a landmark somebody can name.
	 *
	 * Left empty, the kind is the single `Mesh` it always was.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TArray<TObjectPtr<UStaticMesh>> Variants;

	/**
	 * THE REST OF A FIGURE, where one mesh is not a whole person.
	 *
	 * A shopkeeper is a person, and this window's people are MODULAR: a bare
	 * body carrying the head and the hands, and an outfit over it that stops at
	 * the collar. A keeper given the outfit alone is headless and one given the
	 * body alone is naked, so a prop that wants to be a person needs both.
	 *
	 * `Skeletal` leads and carries the animation; everything here follows its
	 * pose, bone for bone, which costs one evaluation for the whole figure --
	 * exactly the arrangement AIntervalCitizens already uses, and for the same
	 * reason. Left empty, a prop is the single mesh it always was.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TArray<TObjectPtr<class USkeletalMesh>> SkeletalParts;

	/**
	 * WHAT THIS CREATURE DOES, in its own animations.
	 *
	 * The comment above used to say "the motions come from the same table the
	 * citizens use", and that was true and useless: the citizens' table holds
	 * clips authored for the citizens' skeleton, and a wolf will not accept
	 * one. So every beast in the world had been standing in its BIND POSE
	 * since the first one was drawn -- a sheep frozen mid-stride, a wolf on
	 * its back with its legs in the air -- and it read as a broken import
	 * rather than as a creature that had never been told to do anything.
	 *
	 * Keyed by the same verbs the citizens use -- `still`, `walk`, `felled` --
	 * so one word means one thing across the whole window, and filled from
	 * each creature's OWN folder: every pack ships `Idle`, `Walk`, `Death`
	 * under the creature's name, and the table is built by matching those
	 * rather than by anybody typing out a hundred and forty paths.
	 *
	 * A word with no row leaves whatever was playing alone. There is no
	 * general fallback and there must not be: falling back to the citizens'
	 * idle is how a wolf ends up doing a person's breathing.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TMap<FName, FIntervalBeastMotion> Motions;


	/** Optional override; the mesh's own material is used when this is unset. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<UMaterialInterface> Material;

	/** Multiplied onto the mesh. A tile is 200cm, so 1,1,1 on a 100cm cube is half a tile. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	FVector Scale = FVector(1.f, 1.f, 1.f);

	/** Lifts the mesh off the ground plane, for things whose pivot is centred. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	float ZOffset = 0.f;

	/**
	 * HOW THE ART WAS MODELLED, as opposed to how it stands.
	 *
	 * Half the third-party art in this project is authored Y-up and arrives
	 * lying on its back -- the .obj helms did, and so does every bear that has
	 * been tried. It is not a broken import and there is nothing to fix in the
	 * file: it is a convention, and a convention is a number.
	 *
	 * Applied before the world's own yaw, so a creature still turns to face
	 * where it is going. Zero for everything that came in standing, which is
	 * most of it.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	FRotator Lean = FRotator::ZeroRotator;

	/**
	 * Degrees of rotation this kind may take. The angle is a pure function of
	 * the node's own id, so it is the same in every window and on every run --
	 * a barrel does not spin when you walk away and come back, and two
	 * citizens describing the same barrel describe the same barrel.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0", ClampMax = "360"))
	float YawJitter = 0.f;

	/**
	 * TURN THIS KIND TO FACE ALONG THE LINE IT IS PART OF.
	 *
	 * A fence, a hedge, a railing and a garden wall are all panels: each one
	 * is longer than it is thick, and a run of them only reads as a barrier if
	 * every panel lies ALONG the run. Without this they all faced the same
	 * way, which looked right on whichever axis the mesh happened to point
	 * down and wrong by ninety degrees on the other -- so a rectangular pen
	 * came out with two good sides and two sides of panels standing across
	 * their own line, leaving gaps you could see through.
	 *
	 * The facing is read from the node's ORTHOGONAL NEIGHBOURS of the same
	 * word, which is the only honest source: the world says where the posts
	 * are and says nothing about which way they face, so the line itself has
	 * to be the answer. A lone panel with no neighbours keeps yaw zero, and a
	 * corner takes the run it can see, preferring the one along X so that two
	 * windows given the same corner always draw it the same way.
	 *
	 * It is a flag rather than a rule about particular words, because which
	 * words are panels is the level's business -- this file writes down no
	 * world word, and a founding that invents a new kind of fence should not
	 * need a recompile to have it stand straight.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	bool bAlignToRun = false;

	/** Fraction of the scale this kind may vary by, again from the id alone. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0", ClampMax = "0.9"))
	float ScaleJitter = 0.f;

	/**
	 * Fraction the HEIGHT may vary by, separately from the footprint, so a
	 * house can be tall and narrow or low and broad rather than simply bigger.
	 * Where the node belongs to a building the figure comes from the building
	 * rather than the tile, so one house stands at one height all the way
	 * round -- per-tile height on a wall gives you a saw, not a house.
	 *
	 * The pivot is assumed centred and ZOffset half the height, which holds
	 * for everything drawn on a cube: the offset is scaled by the same figure
	 * so the wall grows upward off the ground instead of sinking into it.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0", ClampMax = "0.9"))
	float HeightJitter = 0.f;

	/**
	 * Hide this while the world says it is spent. A stump that still looks
	 * like a tree is a window telling a citizen they can chop something the
	 * world will refuse them, which §4's legibility rule exists to prevent.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	bool bHideWhenDepleted = false;

	/** Casts a shadow. Off for flat things; a shadow per pebble is a frame budget spent badly. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	bool bCastShadow = true;

	/**
	 * A LIGHT, for the things that burn.
	 *
	 * There are hearths, watchfires, forges and torches all over this island
	 * and until now not one of them lit anything: after dark the only light in
	 * the world was the sky, and a village at midnight was a silhouette with
	 * nothing going on in it. Zero intensity means no light, which is what
	 * almost every kind wants.
	 *
	 * A light is expensive and a hundred and fifty hearths are more than any
	 * frame can pay for, so only the nearest few are lit -- see the pool in
	 * AIntervalStructures. Which few changes as a citizen walks, and nothing
	 * about the world changes with it.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Fire")
	float LightIntensity = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Fire")
	FLinearColor LightColour = FLinearColor(1.f, 0.56f, 0.22f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Fire")
	float LightRadius = 900.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Fire")
	float LightHeight = 60.f;

	/** How much it gutters. Nothing that burns is steady. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Fire", meta = (ClampMin = "0", ClampMax = "1"))
	float LightFlicker = 0.34f;

	/** Lit only after dark, which is true of a hearth and not of a forge. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Fire")
	bool bLightAtNightOnly = true;

	/**
	 * THE SMOKE OFF IT.
	 *
	 * A light is what a fire is at night and smoke is what it is by day. From
	 * four hundred metres up a hearth's flame is two pixels and invisible; its
	 * smoke is a lean grey stroke fifteen metres long, and it is the only
	 * thing in an aerial photograph that says a village is lived in rather
	 * than built. Unset means no smoke, which is what most kinds want.
	 *
	 * It rides the same budget as the light -- the nearest few, re-aimed as
	 * the citizen walks -- because a hundred and fifty smoke columns is a
	 * hundred and fifty simulations and no frame can pay for that either.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Fire")
	TObjectPtr<class UNiagaraSystem> Smoke;

	/** Where the smoke leaves, above the fire's own light, in the open. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Fire")
	float SmokeHeight = 40.f;

	/**
	 * And where it leaves when the tile is ROOFED.
	 *
	 * Smoke that starts at the hearth inside a house comes out through the
	 * thatch, which is a hole in the roof rather than a chimney. The fire is
	 * the world's fact; that its smoke should appear above the ridge instead
	 * of inside the room is entirely this window's arrangement, and the window
	 * already knows which tiles are roofed because it built the roofs.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Fire")
	float SmokeHeightRoofed = 430.f;

	/** How big the column is. A forge smokes harder than a cook fire. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Fire")
	float SmokeScale = 1.f;

	/** Smoking only after dark, which almost nothing wants. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Fire")
	bool bSmokeAtNightOnly = false;

	/**
	 * WHAT IT SOUNDS LIKE.
	 *
	 * A fire is heard from much further than it is seen from, and it is the
	 * one sound in a settlement that is unmistakably a PLACE rather than a
	 * bed -- everything else the window plays is the air the citizen is
	 * standing in, and this comes from over there. It rides the same budget
	 * as the light and the smoke.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Fire")
	TObjectPtr<class USoundBase> Burning;

	/** How loud, and how far off it can be heard, in centimetres. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Fire")
	float BurningVolume = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Fire")
	float BurningHeard = 2600.f;

	/**
	 * Further pieces, drawn at the same tile and turned by the same angle.
	 * Leave it empty and the kind is one shape, as it always was. Mesh may be
	 * unset when there are parts, for a thing that is ALL parts.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TArray<FIntervalPropPart> Parts;

	/**
	 * WHAT IT LOOKS LIKE PART OF THE WAY THROUGH GROWING.
	 *
	 * A plot is not one picture. The world sows it, twelve minutes pass --
	 * GROW_TICKS_RIPE is 720 -- and it is ready to harvest; then it is cut and
	 * it is bare earth again. Drawn with one set of parts it was a crop the
	 * whole time, including before anybody had planted anything, which is the
	 * same fault as a stump that still looks like a tree: the window telling a
	 * citizen something the world will not honour.
	 *
	 * Each stage carries the fraction of the way to ripe at which it takes
	 * over, and its own pieces. The LAST stage whose `At` has been reached
	 * wins, so they are read in order and `At = 0` is the unsown bed. `Parts`
	 * above is used when a kind has no stages at all, which is nearly all of
	 * them.
	 *
	 * The ripeness comes from the node's own `plantedAt`, so this needs
	 * nothing from the bridge that the frame does not already carry, and a
	 * window that joins halfway through sees the right stage immediately
	 * rather than starting everything from seed.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TArray<FIntervalPropStage> Stages;

	/**
	 * How many ticks from sown to ripe, for a kind that has `Stages`. The
	 * world's own number is 720 (twelve minutes); it is a property rather than
	 * a constant here because this window does not hold opinions about the
	 * world's arithmetic -- apply.py writes what the engine says.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	int32 RipeTicks = 720;
};

UCLASS()
class INTERVALBRIDGE_API AIntervalStructures : public AActor
{
	GENERATED_BODY()

public:
	AIntervalStructures();

	/**
	 * What to draw for each word the world uses, keyed by the world's own
	 * word. An entry may be keyed `type` or `type.kind` -- the more specific
	 * is preferred -- so a level can give one sort of landmark its own mesh
	 * without anything in C++ learning that the distinction exists.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<class UIntervalLook> Look;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TMap<FName, FIntervalPropKind> Props;

	/**
	 * A SECOND thing to draw for the same word, on top of the first.
	 *
	 * Generic on purpose, though what it exists for is the jetty: an English
	 * town house carries its upper storey out over the street on the ends of
	 * the floor joists, so the first floor is wider than the ground floor and
	 * throws a shadow along the wall beneath it. That overhang is half of why
	 * a medieval street looks the way it does, and it cannot be painted on --
	 * it is the building being a different width at two heights.
	 *
	 * A word with no entry here simply has one layer.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TMap<FName, FIntervalPropKind> PropsUpper;

	/**
	 * The ground, which is the only thing that knows where the buildings are.
	 * Left unset it finds one in the level.
	 *
	 * A told node says a wall is at a tile. It does not say whether that tile
	 * is part of a house or the wall of a yard, and those want to look nothing
	 * alike -- a garden wall drawn as a jettied, timber-framed, two-storey
	 * house wall reads as a roofless building, which is what made the towns
	 * look unfinished. Only the footprint knows, and the ground has it.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<AIntervalGround> Ground;

	/**
	 * WHAT A BUILDING IS FOR, and therefore what it is built of.
	 *
	 * The world already says what stands inside each building -- an anvil, a
	 * brewpot, a vault, an altar -- so a building's TRADE is told, not guessed.
	 * This maps the world's word for a thing to a word of the level's own
	 * choosing for the construction its building takes, and a wall then looks
	 * up `wall.<that word>` before anything else.
	 *
	 * Both sides are data. C++ knows only that a building may have a trade and
	 * that a trade may change how its walls are drawn; it does not know that
	 * forges exist, or that they are built of stone.
	 *
	 * Where a building holds several, the FIRST in this map wins, so order it
	 * from the most telling to the least: a hall with a hearth in it is a hall.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TMap<FName, FName> TradeOf;

	/** Log every word that arrived with no entry, once each. Silence hides a stale window. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	bool bReportUndrawnKinds = true;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	UFUNCTION()
	void HandleFrame();

	UFUNCTION()
	void HandleGroundChanged();

private:
	/**
	 * Which plots OUR citizen has sown, and on what tick -- read out of the
	 * frame's own `crops`, which is a player field and not a node one. See
	 * AIntervalStructures::SownAt.
	 */
	TMap<FString, int64> Crops;
	int64 CropsTick = -1;

	int64 SownAt(const FString& NodeId);

	void Rebuild(const FIntervalFrame& Frame);
	class UIntervalLook* LookAsset() const { return Look; }

	UInstancedStaticMeshComponent* ComponentFor(FName Key, const FIntervalPropKind& Kind);
	UInstancedStaticMeshComponent* PoolFor(FName Key, UStaticMesh* Mesh,
		UMaterialInterface* Material, bool bCastShadow);

	/** Puts the few lights there are at the nearest things that burn. */
	void TendFires(const struct FIntervalFrame& Frame);

	/**
	 * Draws the things the world says are standing there that are PEOPLE.
	 *
	 * A shopkeeper was a cylinder with a hat on it, which is what every prop in
	 * this window is: an instance in a pool of one mesh. A person cannot be
	 * that -- they are modular and they are animated -- so the few nodes whose
	 * kind names a skeleton get a component each instead of an instance, built
	 * the way a citizen is built.
	 *
	 * Returns true if it took the node, so the instanced path knows to leave
	 * it alone.
	 */
	bool StandFigure(const FString& Id, const struct FIntervalPropKind& Kind,
		const FVector& Where, float Yaw, float Scale);

	/** One component per figure, keyed by the world's id. Followers hang off it. */
	UPROPERTY(Transient)
	TMap<FString, TObjectPtr<class USkeletalMeshComponent>> Figures;

	/** Which figures were wanted this interval; the rest are taken down. */
	TSet<FString> FiguresSeen;

	/**
	 * Builds the walls the world says are standing, as masonry rather than as
	 * scaled cubes. Rebuilt only when the set of told stones changes.
	 */
	void BuildPalisades(const struct FIntervalFrame& Frame);

	UPROPERTY(Transient)
	TObjectPtr<class UProceduralMeshComponent> Palisades;

	/** What the wall looked like last interval. Masonry is slow to change. */
	uint64 PalisadeDigest = 0;

	/** How many point lights the window will pay for at once. */
	UPROPERTY(EditAnywhere, Category = "Interval|Fire", meta = (ClampMin = "0", ClampMax = "64"))
	int32 FireLights = 14;

	UPROPERTY(Transient)
	TArray<TObjectPtr<class UPointLightComponent>> Fires;

	/**
	 * One smoke column per lit fire, index for index with `Fires` above.
	 * Kept parallel deliberately: the budget, the sort and the "is it dark
	 * enough to bother" question are all answered once, for both.
	 */
	UPROPERTY(Transient)
	TArray<TObjectPtr<class UNiagaraComponent>> Smokes;

	/** The weather collection, read for the gale the smoke leans in. */
	UPROPERTY(Transient)
	TObjectPtr<class UMaterialParameterCollection> Weathers;

	/** One crackle per lit fire, index for index with `Fires`. */
	UPROPERTY(Transient)
	TArray<TObjectPtr<class UAudioComponent>> Crackles;

	/** A stack and its cap per roofed fire, index for index with `Fires`. */
	UPROPERTY(Transient)
	TArray<TObjectPtr<class UStaticMeshComponent>> Stacks;

	UPROPERTY(Transient)
	TArray<TObjectPtr<class UStaticMeshComponent>> Caps;

	UPROPERTY(Transient)
	TMap<FName, TObjectPtr<UInstancedStaticMeshComponent>> Pools;

	UPROPERTY(Transient)
	TObjectPtr<UIntervalBridgeSubsystem> Bridge;

	/** Cheap digest of what was drawn last, so a still world is not rebuilt every interval. */
	uint64 LastDigest = 0;

	TSet<FName> Reported;
};
