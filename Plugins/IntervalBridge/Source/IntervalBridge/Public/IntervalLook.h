// Copyright interval.
//
// EVERY LOOK IN ONE ASSET, ON PURPOSE.
//
// All of this used to live on the level's own actors, which is where an
// Unreal project normally puts it. It cannot stay there. The actors are
// external-actor packages, and nothing available to this project can save one
// under automation: a whole session's worth of meshes, offsets and materials
// lived in memory and went with the editor every time the plugin was rebuilt.
// An asset saves. So the look lives in an asset, and the level only points at
// one -- or does not, and the window loads the one at the conventional path.
//
// Nothing in here is a fact about the world. It is a table of how to draw
// words the world uses, and a world that has never used a word costs nothing.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "IntervalStructures.h"
#include "IntervalRoof.h"
#include "IntervalScatter.h"
#include "IntervalSpan.h"
#include "IntervalMotion.h"
#include "IntervalLook.generated.h"

class UMaterialInterface;
class USoundBase;

/**
 * ONE WAY OF BEING DRESSED.
 *
 * The art is modular by outfit: a farmer's body, head, legs and feet are four
 * meshes on one skeleton, and so are a king's. A citizen takes whichever of
 * these their own key lands on, which is what stops a street being one figure
 * repeated -- before any dye is applied at all, the woman at the well is
 * simply wearing different clothes from the man at the forge.
 *
 * The FIRST part is the one that carries the animation and the one whose
 * bounds decide what is drawn, so a BODY goes first. With an arm at the head
 * of the list the rest of the person was culled and a forearm walked about on
 * its own.
 */
USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalOutfit
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TArray<TObjectPtr<class USkeletalMesh>> Parts;

	/**
	 * HOW THIS OUTFIT MOVES, where it cannot move the way the rest do.
	 *
	 * An animation belongs to a skeleton, and a pack's men and its women are
	 * not rigged alike -- the men have fingers and the women do not, so the
	 * same walk cannot be played on both. An outfit may therefore carry its
	 * own table, consulted before the window's general one; an outfit that
	 * shares the common skeleton leaves this empty and costs nothing.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TMap<FName, FIntervalMotion> Motions;

	/**
	 * THE HEADS OF HAIR THAT SUIT THIS OUTFIT.
	 *
	 * Chosen from by a DIFFERENT slice of the citizen's key than the outfit
	 * itself, so hair and clothes vary independently: four outfits and four
	 * hairstyles is sixteen people, not four. Listed per outfit rather than
	 * once for the window because a hairstyle is cut for a head -- the pack's
	 * buns and its beard are not interchangeable -- and because an outfit that
	 * covers the head, a hood or a helm, wants none of them at all.
	 *
	 * Left empty, nobody in this outfit has any, which is a shaven head and a
	 * perfectly good answer for a hood.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TArray<TObjectPtr<class USkeletalMesh>> Hair;
};

/**
 * HOW A TOLD WALL IS BUILT.
 *
 * `palisade` is the world's own word and the world says where every one of them
 * is, tile by tile: eight hundred and forty-two across this founding, a
 * hundred and eighty-six of them ringing Anchor. The gaps in that ring are the
 * gates -- the world leaves them empty and stands a `guard` in each one -- so
 * nothing here has to guess where a way through belongs.
 *
 * (Written down because I got it wrong first: a sweep of the nodes for a
 * wall-shaped KIND found nothing and I concluded the wall was this window's
 * invention. `palisade` is a node TYPE and carries no kind at all, which is why
 * it was invisible to that sweep. The lesson is the usual one -- when a
 * measurement says a thing the world obviously has does not exist, the
 * measurement is wrong.)
 *
 * What a level supplies is only the BUILDING of it. The word was already drawn
 * as a scaled cube, which is a garden wall; this makes it a curtain with
 * thickness, teeth along the top, and a tower where the run turns.
 */
USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalPalisade
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<UMaterialInterface> Material;

	/** How high the walkway stands above the ground, in centimetres. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "50"))
	float Height = 640.f;

	/** How thick the curtain is. A castle wall you can see the depth of. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "20"))
	float Thickness = 260.f;

	/** The teeth along the top: how tall, how wide, and how wide the gaps. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	float MerlonHeight = 160.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	float MerlonWidth = 115.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	float EmbrasureWidth = 95.f;

	/**
	 * A tower wherever the run TURNS, and every so many tiles along a straight
	 * stretch. Zero puts them only where the wall turns, which is what a small
	 * work gets. Corners are found from the told tiles themselves, so a tower
	 * lands where the world actually bent its wall.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0"))
	int32 TowerEvery = 9;

	/** How much taller and wider than the curtain a tower stands. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	float TowerRise = 300.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	float TowerWiden = 170.f;

	/**
	 * A pier where a run simply STOPS, which is the mouth of a gate. The world
	 * gates a town by leaving tiles out, so the end of a run is a gatepost and
	 * wants to look like one rather than like a wall that was cut off.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	float GatepostRise = 190.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	float GatepostWiden = 90.f;

	/**
	 * HOW WIDE A HOLE IN THE LINE IS STILL WALL.
	 *
	 * The world's palisade tiles are a line SAMPLED, not a line drawn: around
	 * Anchor they alternate, one tile told and the next left out, all the way
	 * round. Taking each told tile as a tile of wall and nothing else built a
	 * hundred and forty-one gateposts and about seventy holes -- a picket of
	 * free-standing stone slabs rather than a curtain, which is exactly what it
	 * looked like from the road.
	 *
	 * So a gap of this many tiles or fewer, with told stone on both sides of
	 * it, is closed up. It is not inventing a wall anywhere the world did not
	 * put one: it is reading a dashed line as a line. A gate is then a gap
	 * WIDER than this -- four metres and up, which is a gate a cart fits
	 * through -- and the gatepost, the guard and the road all still land where
	 * the world left the hole.
	 *
	 * Zero takes the tiles exactly as told.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0", ClampMax = "4"))
	int32 CloseGapsUpTo = 1;
};

/**
 * The sound of a boot on one kind of ground.
 *
 * SEVERAL OF EACH, and that is not indulgence. One sample played at two steps
 * a second is the most recognisable artificial sound a window can make -- the
 * ear finds the repeat within about four paces and never loses it again. A
 * handful, chosen at random and pitched a little either way, is past where
 * anyone can hear the pattern.
 */
USTRUCT(BlueprintType)
struct FIntervalRite
{
	GENERATED_BODY()

	/** Which of the four shapes: a burst, a gathering, a ring or a rise. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<class UNiagaraSystem> System;

	/**
	 * THE COLOUR IS WHAT TELLS TWO RITES APART.
	 *
	 * A rot and an unmaking are the same motion, things flying outward from a
	 * pair of hands. One is dark, wet and slow; the other is bright and quick.
	 * Four systems and a colour each is why there are not eleven systems to
	 * keep in step.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	FLinearColor Tint = FLinearColor::White;

	/** How big, against the system's own size. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0.05", ClampMax = "8"))
	float Scale = 1.f;

	/** How far up the body it happens, in cm. Hands are about a metre. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0", ClampMax = "400"))
	float Rise = 100.f;
};

USTRUCT(BlueprintType)
struct FIntervalFootfall
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TArray<TObjectPtr<class USoundBase>> Sounds;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0", ClampMax = "4"))
	float Volume = 1.f;

	/** How far either side of its own pitch a step may land. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0", ClampMax = "0.5"))
	float PitchJitter = 0.12f;
};

/**
 * ONE SPECIES OF BIRD: what it is and what it is made of.
 *
 * A mesh and a material together, because they are never chosen apart -- a
 * gull's shape with a crow's colour is neither bird. Two parallel maps keyed
 * by the same word would let exactly that drift happen silently.
 */
USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalFowl
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<class UStaticMesh> Mesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<class UMaterialInterface> Hue;
};

UCLASS(BlueprintType)
class INTERVALBRIDGE_API UIntervalLook : public UDataAsset
{
	GENERATED_BODY()

public:
	/** Where a window looks when a level names no look of its own. */
	static const TCHAR* DefaultPath;

	/** Loads the level's look, or the conventional one, or nothing. */
	static UIntervalLook* Resolve(UIntervalLook* Named);

	/** What to draw for each word the world uses for a thing that stands. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TMap<FName, FIntervalPropKind> Props;

	/** The storey above, for the kinds that have one. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TMap<FName, FIntervalPropKind> PropsUpper;

	/** What to draw for each word the world uses for something that moves. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TMap<FName, FIntervalPropKind> Mobs;

	/** What grows on each ground the world names. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TMap<FName, FIntervalScatterKind> Scatter;

	/** What a roof is made of, for each ground the world calls roofed. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TMap<FName, FIntervalRoofKind> Roofs;

	/**
	 * What a crossing is made of: the deck slab and the pier under it.
	 *
	 * ONE, not a table by ground. Every other look here is keyed by the
	 * world's word for a tile because a meadow and a moor grow different
	 * plants; a bridge is a bridge. The world has exactly one ground kind for
	 * a decked crossing and ten crossings on the island, and giving them a map
	 * would only invite a second stone that no founding asks for.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	FIntervalSpan Span;

	/**
	 * What everyone wears, hung on bones so it moves with them.
	 *
	 * Painting clothes on the engine's figure got the COLOURS right and left
	 * the silhouette of a shop dummy -- a person with a tunic drawn on rather
	 * than a person in a tunic. These are real pieces: a skirt on the pelvis,
	 * a hood on the head. A citizen's own number scales them a little, so a
	 * street is not one figure repeated.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|People")
	TArray<FIntervalPropPart> Clothing;

	/**
	 * What to draw for a thing the world says somebody is wearing or carrying,
	 * keyed by the world's own word for the item. A word with no entry is not
	 * drawn, which is better than drawing the wrong thing.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|People")
	TMap<FName, FIntervalKit> Worn;

	/**
	 * THE PARTS A PERSON IS MADE OF.
	 *
	 * The art this project uses is modular: a body, two arms, two legs and a
	 * head, each its own skeletal mesh, all sharing one skeleton. They are
	 * drawn as one figure by giving the first the animation and telling the
	 * rest to follow its pose -- which is how modular characters have always
	 * been done, and has the happy property that a citizen can be given a
	 * different head without being given a different body.
	 *
	 * Left empty, the single `CitizenMesh` below is used instead.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|People")
	TArray<TObjectPtr<class USkeletalMesh>> CitizenParts;

	/**
	 * THE WARDROBE. Every way of being dressed the window may draw.
	 *
	 * A citizen picks one by their own key, so they wear the same clothes in
	 * every window and the same tomorrow. Left empty, everybody wears
	 * `CitizenParts` above, which is the one-outfit case.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|People")
	TArray<FIntervalOutfit> Outfits;

	/**
	 * How big a person is, over whatever the art was modelled at.
	 *
	 * It lives here rather than on the citizens actor because a level actor's
	 * properties cannot be saved from here, and a figure that is the wrong
	 * height is the wrong height every time the editor restarts.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|People", meta = (ClampMin = "0.1", ClampMax = "5"))
	float CitizenScale = 1.f;

	/**
	 * THE DUST A PAIR OF BOOTS LIFTS.
	 *
	 * The smallest effect in the window and close to the most valuable. A
	 * figure crossing a dry yard with nothing happening underneath it is
	 * SLIDING, and no amount of work on the walk cycle fixes that, because the
	 * tell is not the legs -- it is that the ground does not notice them.
	 *
	 * Unset and nobody raises any. The system spawns per unit TRAVELLED rather
	 * than per second, so it emits nothing at all while somebody stands still
	 * and nothing here has to ask whether they are walking.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Folk")
	TObjectPtr<class UNiagaraSystem> StepDust;

	/** How big a puff. One is about right for a person on dry earth. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Folk")
	float StepDustScale = 1.f;

	/** How far above the feet it leaves. An ankle, not a knee. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Folk")
	float StepDustRise = 6.f;

	/**
	 * What a citizen is made of.
	 *
	 * The only skeleton to hand is the engine's grey figure, and grey plastic
	 * is a costume like any other -- it just happens to be a shop dummy's. This
	 * material draws clothes from position in the figure's own space, the same
	 * way the half-timbering is drawn, and takes a `Who` scalar so that a
	 * street is not everyone in the same tunic.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|People")
	TObjectPtr<UMaterialInterface> PersonMaterial;

	/**
	 * How a citizen moves, keyed by the world's word for what they are doing.
	 * See IntervalMotion.h.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|People")
	TMap<FName, FIntervalMotion> Motions;

	/**
	 * What a place sounds like, keyed by the world's own word for the ground.
	 *
	 * The window never decides that a moor is bleak. A level says the word
	 * `moor` is played as this piece, exactly as it says the word `pine` is
	 * drawn as a dark cone -- and a world that uses a word no entry covers is
	 * simply not scored, which is quieter than being scored wrongly.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sound")
	TMap<FName, TObjectPtr<USoundBase>> Music;

	/** The bed under everything, keyed the same way and always looping. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sound")
	TMap<FName, TObjectPtr<USoundBase>> Ambience;

	/**
	 * GROUND THAT TAKES ITS SOUND FROM WHAT IT BORDERS.
	 *
	 * Sand is the case that forced this. A beach and a riverbank are the same
	 * word, so keying the bed on the tile underfoot made every riverbank in
	 * the world play the sea -- a citizen standing beside a stream ten tiles
	 * wide heard surf, which is wrong in a way you notice immediately and
	 * cannot un-notice.
	 *
	 * The tile cannot answer it because the tile does not know. What a bank
	 * borders does: it is sand BESIDE a river, or sand BESIDE the sea, and the
	 * neighbouring ground is the only place that difference is written down.
	 *
	 * So a word listed here does not use its own bed. The nearest tile that is
	 * NOT a borrower and DOES have a bed wins, searched outward so the closest
	 * water is the one you hear. A bank with nothing near it falls back to its
	 * own entry, which is why it should still have one.
	 *
	 * It names no water and no sand: which words are ambiguous is the level's
	 * business, and a founding that grows a new kind of shore says so here
	 * rather than in a rebuild.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sound")
	TSet<FName> BorrowsAmbience;

	/**
	 * Ground the window may not wall across.
	 *
	 * Measured, not assumed: of the tiles ringing a roofed room, every one
	 * that carries a wall stands on raw country or a trail, and the one or two
	 * that carry nothing stand on flagstone or cobble. The generator lays a
	 * threshold where the way in is. So a covered tile with paving under it is
	 * a DOORWAY, and closing it is how every house on the island ended up
	 * walled shut.
	 *
	 * The window still learns nothing about what `flag` means -- a level names
	 * the grounds, and a world that names none simply has no doors cut.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TSet<FName> Thresholds;

	/**
	 * The rain curtain: a cylinder that rides with whoever is looking, and the
	 * material that draws streaks down the inside of it. HOW HARD it rains is
	 * the world's number and the same for everybody; where each streak falls
	 * is this window's own dice, like the dither on the thatch.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	TObjectPtr<class UStaticMesh> RainMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	TObjectPtr<UMaterialInterface> RainMaterial;

	/**
	 * HOW WIDE THE CURTAIN IS, in centimetres.
	 *
	 * It has to be bigger than the view. At fourteen metres you could see where
	 * the rain stopped -- from a camera a few metres off the citizen's shoulder
	 * the far wall of the drum was a clean vertical line with a dry village
	 * behind it, which reads as a rain machine following one person around.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky", meta = (ClampMin = "200"))
	float RainRadius = 4500.f;

	/**
	 * Below zero, the world decides how hard it rains. At or above, this does,
	 * whatever the world says -- for looking at weather that is not happening.
	 *
	 * IT LIVES HERE AND NOT ON THE HOUR ACTOR, where it used to, and the move
	 * was not tidiness. A level-placed actor's SAVED property beats the C++
	 * default, and an external-actor package is a thing this project cannot
	 * write under automation -- so the knob was unreachable from here and
	 * changing the default did nothing at all, silently. An asset saves.
	 *
	 * It changes nothing but pixels: nobody gets wet, no yield moves, and the
	 * next frame from the bridge still says exactly what it said.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	float ForceRain = -1.f;

	/**
	 * Below zero, the world decides how much cloud there is. At or above, this
	 * does.
	 *
	 * THE RAIN AND THE CLOUD ARE NOT THE SAME KNOB, and until now only the
	 * rain had one. Cloud is the larger of the two by far: it takes two thirds
	 * off the sun, puts a third onto the sky light, multiplies the fog by
	 * `OvercastFog`, and turns the sky the flat colour of `SkyOvercastColour`.
	 * Rain, next to that, is wet ground and falling lines.
	 *
	 * So "show me this on a clear day" was a thing nobody could ask for.
	 * `ForceRain` of zero still left the cloud exactly where the world had it,
	 * and every photograph taken to settle an argument about how grey this
	 * world is was taken under whatever cloud happened to be over it. Two
	 * sessions of them landed on flat overcast and were read as the window
	 * being washed out.
	 *
	 * Worse, the founding tick is day nought, and in this generator's weather
	 * day nought is flat overcast. A world is refounded often while it is
	 * being built, so the FIRST thing anybody sees of a new world is reliably
	 * its dullest weather.
	 *
	 * It changes nothing but pixels, like the other two: no deed is sent and
	 * the next frame from the bridge says exactly what it said.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	float ForceCloud = -1.f;

	/**
	 * WHAT A CLICK LEAVES ON THE GROUND.
	 *
	 * Unlit, translucent, two-sided, and it reads BOTH the colour and the fade
	 * off the mesh's own vertex colours -- so one material draws every mark
	 * this window makes, in any colour, at any opacity, without a material
	 * instance per mark and without a parameter anybody has to remember to set.
	 *
	 * It replaces the Top Down template's blue cross, which was never ours:
	 * `BP_TopDownController` spawned it on every click, in a colour and a shape
	 * that belong to an engine sample.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Hand")
	TObjectPtr<class UMaterialInterface> MarkMaterial;

	/**
	 * Below zero, the world decides what hour it is. At or above, this does:
	 * 0 is the middle of the night and 1 is noon.
	 *
	 * It exists for the same reason `ForceRain` does, and for a sharper one.
	 * A day here is long in wall-clock terms, so photographing a change made to
	 * the ground or the foliage can mean waiting the better part of an hour for
	 * the sun -- and a screenshot taken in the dark is not a check, it is a
	 * guess with a picture attached. More than one thing in these notes was
	 * "measured" at midnight and got the wrong answer for it.
	 *
	 * IT CHANGES NOTHING BUT PIXELS. The world's own hour is still what every
	 * other window sees, no deed is sent, and the next frame from the bridge
	 * says exactly what it said.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	float ForceDay = -1.f;

	/**
	 * THE MOON'S DISC: a plain sphere, lit by the sun like anything else.
	 *
	 * Left empty there is no disc and the moonlight still falls, which is the
	 * right way round -- the light is what changes how a night feels and the
	 * shape in the sky is what makes anybody look up.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	TObjectPtr<class UStaticMesh> MoonMesh = nullptr;

	/** What it is made of. Pale, rough and not emissive; see AIntervalHour. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	TObjectPtr<class UMaterialInterface> MoonMaterial = nullptr;

	/**
	 * HOW MUCH OF THE SKY'S LIGHT REACHES THE GROUND, over what the capture
	 * says by itself.
	 *
	 * A face that the sun cannot see is lit by the sky and by nothing else,
	 * and with this at one a palisade's north side, a canopy's far half and the
	 * ground under a wall all came out BLACK -- not dark, black, with a
	 * terminator down the middle of a tower you could cut yourself on. Four
	 * separate wrong diagnoses went past before anybody measured the ratio: a
	 * lift on the leaf albedo, a normal map, two-sidedness, an sRGB flag.
	 *
	 * It is a number and not a fix because nobody here can prove what the
	 * right ratio is from first principles: the sun in this window is 6.2 in
	 * whatever units the project settled on rather than the hundred thousand
	 * lux of a real noon, and a sky captured against that sun comes out in
	 * proportion to it. So the ratio is a thing to LOOK at, and this is the
	 * knob to look with.
	 *
	 * Outdoors, in daylight, the sky is worth something like a sixth of the
	 * sun on a vertical surface. It should never be zero and it is not a
	 * substitute for the sun: turn it far enough up and the world goes flat,
	 * because a world lit from everywhere has no shape.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky", meta = (ClampMin = "0"))
	float SkyLift = 1.f;

	/**
	 * HOW MUCH OF THE LAND'S HEIGHT THIS WINDOW DRAWS.
	 *
	 * One draws the island as the generator computed it. Zero draws it flat,
	 * which is what this window did before it was given the elevation field at
	 * all, and which has now been asked for three times from the stream --
	 * "when it was flat it looked great", "it doesn't look like a small hill,
	 * it looks weird", "maybe we just shouldn't draw elevation at all".
	 *
	 * Between the two is a shallower island: the same hills, less of them.
	 *
	 * IT COSTS THE WORLD NOTHING EITHER WAY. That field routes roads and
	 * nothing else reads it, so a flat island and a hilly one are the same
	 * world drawn twice. Which is why this is a dial and not an argument.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Ground",
		meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float LandRelief = 1.f;

	/**
	 * A CHIMNEY, WHICH THE SMOKE HAS BEEN MANAGING WITHOUT.
	 *
	 * Smoke was given to every hearth before anything was given for it to come
	 * out of, so over a roofed building it appeared from a point in mid-air
	 * above the ridge. From four hundred metres up that reads as a fault in
	 * the drawing rather than as a fire.
	 *
	 * It is placed where the HEARTH is -- the world said a fire burns on that
	 * tile -- and it rises from the roof surface over that tile, which the
	 * roof builder now keeps. Nothing here decides where a chimney goes; a
	 * chimney goes over the fire.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Fire")
	TObjectPtr<class UStaticMesh> ChimneyMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Fire")
	TObjectPtr<class UMaterialInterface> ChimneyMaterial;

	/** How thick the stack is, and how far it stands above the thatch. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Fire")
	float ChimneyWidth = 62.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Fire")
	float ChimneyRise = 155.f;

	/** The cap: a course that oversails the stack, which is what stops rain. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Fire")
	float ChimneyCapOut = 15.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Fire")
	float ChimneyCapHigh = 22.f;

	/**
	 * RAIN YOU CAN HEAR, and stop hearing when you step under a roof.
	 *
	 * Two recordings rather than one filtered one. Rain in the open is a broad
	 * hiss with almost nothing under it; rain heard from under a thatch is the
	 * hiss gone entirely, a soft patter, and the odd heavy drop off the eaves.
	 * Crossfading between them as somebody crosses a threshold is most of what
	 * makes a roof feel like shelter -- and the window already knows which
	 * tiles are roofed, because it built the roofs.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sound")
	TObjectPtr<class USoundBase> RainSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sound")
	TObjectPtr<class USoundBase> RainRoofSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sound", meta = (ClampMin = "0", ClampMax = "2"))
	float RainVolume = 0.62f;

	/**
	 * DAYLIGHT IN THE OPEN, which the window had no sound for at all.
	 *
	 * A meadow at noon with a fire somewhere and nothing else is not quiet,
	 * it is EMPTY -- and the absence was reported by someone watching long
	 * before any part of the renderer was. Birds are the cheapest thing that
	 * makes outdoor air sound inhabited.
	 *
	 * Mostly silence by construction: the file is eight per cent sounding and
	 * the rest gaps, because a continuous chirping loop becomes a ringtone
	 * inside a minute. It is gated on day, on being out from under a roof,
	 * and against rain -- birds stop when it rains, and a track that does not
	 * is worse than no track, because the ear notices the lie.
	 */
	/**
	 * WHICH WAY THE FIGURE ITSELF FACES, in degrees, before it is turned.
	 *
	 * Unreal takes +X as forward and these meshes do not: measured from their
	 * own bounds, Male_Ranger is 180 cm across X and 37 cm across Y, which is
	 * a T-pose with the arms along X -- so side to side is X and the front of
	 * the body points along Y.
	 *
	 * The heading was never wrong. `Atan2(dY, dX)` gives the true direction of
	 * travel; the body was simply mounted ninety degrees to it, so a citizen
	 * walking south went south while facing east. It reads as walking sideways,
	 * and it is the other half of the complaint that first came in as
	 * "marching in place while moonwalking diagonally backwards" -- that report
	 * was two faults wearing one description, and only the marching was fixed.
	 *
	 * Data rather than a constant because it belongs to the ART, not to this
	 * window: a founding that ships figures facing the other way changes the
	 * number instead of the code, and the sign can be flipped with an apply
	 * rather than a rebuild.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|People", meta = (ClampMin = "-180", ClampMax = "180"))
	float CitizenFacingYaw = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Interval|Sound")
	TObjectPtr<class USoundBase> BirdSound;

	/**
	 * AND WHAT LIVES ON THIS PARTICULAR GROUND, keyed by the world's own word
	 * for it, exactly as the ambience beds and the footfalls are.
	 *
	 * `BirdSound` above is a meadow at noon, and it was playing over the moor,
	 * over the shingle and over the peat as well -- one birdsong everywhere,
	 * which is the audio version of one mesh standing in for every prop. What
	 * a place SOUNDS like is most of what tells you where you are, and this
	 * window already knows which country the ground underfoot belongs to.
	 *
	 * So the high bleak ground gets crows, the shore gets gulls and the fens
	 * get frogs; `BirdSound` remains the fallback for the green and settled
	 * words, which is what it was drawn for. A word with no row here takes it.
	 *
	 * Asked for from the stream, and the reasoning came with it: "sound of
	 * crows in moor instead of regular bird song ... details like these are in
	 * my opinion what will give this window a big jump."
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Interval|Sound")
	TMap<FName, TObjectPtr<class USoundBase>> GroundVoices;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Interval|Sound")
	float BirdVolume = 0.55f;

	/**
	 * WHAT A FOOTFALL SOUNDS LIKE ON EACH GROUND, keyed by the world's own
	 * word for that ground. A word with no entry is silent, which is the same
	 * rule the ambience beds follow and the right one: the window should not
	 * invent a noise for ground it has never been told about.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sound")
	TMap<FName, FIntervalFootfall> Footfalls;

	/**
	 * What a deed SOUNDS like, keyed on the world's own verb.
	 *
	 * The world records `deed` for every citizen on the interval they do
	 * something, which is how the window already knows which motion to play.
	 * This is the other half of the same fact. A deed with no row here is
	 * silent, which is most of them: banking and walking about want no noise.
	 *
	 * It reuses the footfall structure because the need is identical, several
	 * takes of one sound played a little either side of their own pitch, and a
	 * second structure saying the same thing would only drift from this one.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TMap<FName, FIntervalFootfall> DeedSounds;

	/**
	 * What a deed LOOKS like, keyed on the world's own verb, beside what it
	 * sounds like. Sorcery is the reason this exists: eleven spells across two
	 * books that a bystander could not see at all.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sound")
	TMap<FName, FIntervalRite> Rites;

	/**
	 * AND WHAT A SPELL LEAVES ON WHOEVER IT LANDED ON.
	 *
	 * A rite is the casting and it is over in a moment. These are the other
	 * half, and they are the half that matters to the person it happened to:
	 * `stilled`, `withered`, `rotting`, `rooted`, `branded`, `burning`. The
	 * bridge has been forwarding them for some time as `marks.<word>`, holding
	 * the intervals REMAINING so the window never does arithmetic with the
	 * world's clock, and the window drew none of them -- so a citizen who had
	 * been rooted to the spot looked exactly like a citizen standing still,
	 * and the spell that did it may as well not have been cast.
	 *
	 * Keyed on the word, and it reuses the rite's own shape because a mark
	 * wants the same four things: a system, a colour to tell it from the
	 * others, a size and a height up the body. What differs is that a mark
	 * PERSISTS -- it is switched on while the world says the condition lasts
	 * and switched off when the count reaches nothing.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sound")
	TMap<FName, FIntervalRite> Marks;

	/** How far a citizen walks between one footfall and the next, in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sound", meta = (ClampMin = "10"))
	float StepEvery = 76.f;

	/** Past this, nobody's feet are worth a voice. In centimetres. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sound")
	float StepHeard = 3600.f;

	/** The sphere the stars are drawn on, and what draws them. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	TObjectPtr<class UStaticMesh> StarMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	TObjectPtr<class UMaterialInterface> StarMaterial;

	/**
	 * AND THE SPHERE THE RAINBOW IS DRAWN ON, which is a second one of the
	 * same thing.
	 *
	 * The world has reported a `rainbow` in every frame's sky since the
	 * beginning and the window has never drawn it. It is its own dome rather
	 * than another pass on the stars' because the two have nothing to say to
	 * each other -- one belongs to the night and one cannot exist without the
	 * sun -- and because an additive unlit dome costs a pass of a shader that
	 * returns black on almost every frame of the world's life.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	TObjectPtr<class UStaticMesh> BowMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	TObjectPtr<class UMaterialInterface> BowMaterial;

	/**
	 * How strong a bow the world's own number is worth drawing as.
	 *
	 * The engine reports `rainbow` as a share, and a share of one drawn at
	 * full strength is a stripe of pure hues across the sky, which is what a
	 * rainbow looks like in a painting and not what one looks like. A real one
	 * is faint; this is the knob that says how faint, and it is deliberately
	 * low.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky", meta = (ClampMin = "0", ClampMax = "4"))
	float BowStrength = 0.85f;

	/**
	 * A BOW, ASKED FOR, FOR LOOKING AT ONE.
	 *
	 * The same licence as `ForceDay` and `ForceRain` and needed more than
	 * either: the world reports a rainbow for a few minutes of its week, and
	 * a thing that cannot be summoned is a thing that can only be checked by
	 * waiting for weather. Negative means the world decides, which is what it
	 * must be left at -- somebody is watching the stream.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky", meta = (ClampMin = "-1", ClampMax = "1"))
	float ForceBow = -1.f;

	/**
	 * THE BIRD, AND WHAT BEATS ITS WINGS.
	 *
	 * Forged rather than borrowed: the bestiary's raven is a PERCHED bird with
	 * its wings folded, and seen from twenty metres above it is a dark lump.
	 * `Tools/make_art.py` authors one in the air instead, at a crow's real
	 * size -- 44 cm long and 94 across -- and `M_IntervalWings` flaps it in the
	 * vertex shader, the same way the grass bends and the chain swings.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	TObjectPtr<class UStaticMesh> BirdMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	TObjectPtr<class UMaterialInterface> BirdMaterial;

	/**
	 * How many birds are in a skein, and how often one crosses.
	 *
	 * SPACING IS THE WHOLE THING, exactly as it is for the birdsong these fly
	 * beside: a sky with a steady supply of birds in it is an aquarium. The
	 * gap is in seconds and is deliberately long.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky", meta = (ClampMin = "0", ClampMax = "80"))
	int32 FlockSize = 11;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky", meta = (ClampMin = "0", ClampMax = "600"))
	float FlockEvery = 42.f;

	/**
	 * AND WHAT LIVES ON THE GROUND, which so far is a frog in the fens.
	 *
	 * Scenery rather than a mob: nothing here is in any frame, nothing can be
	 * struck, and the world is never told. See AIntervalSmallLife, which puts
	 * them only on ground the world itself calls wet.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	TObjectPtr<class UStaticMesh> FrogMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	TObjectPtr<class UMaterialInterface> FrogMaterial;

	/** How many are in sight at once. Seven is a fen; forty is a plague. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky", meta = (ClampMin = "0", ClampMax = "60"))
	int32 FrogCount = 7;

	// ---- AND THE BUTTERFLIES, WHICH ARE THE OTHER HALF OF A LIVING FIELD ----
	//
	// One mesh, two materials. An instanced component carries a single
	// material, so the two species over a meadow are two components over the
	// same eight-centimetre mesh rather than one component reading per-instance
	// colour, which would want a material master of its own for two hues.

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<class UStaticMesh> ButterflyMesh;

	/** The common one: a white, which is what most of a field is. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<class UMaterialInterface> ButterflyPale;

	/** And the one worth looking up for, about a third of them. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<class UMaterialInterface> ButterflyBright;

	/** How many over a meadow. More than the frogs, because each is smaller
	 *  and because a field with three butterflies over it reads as three
	 *  butterflies rather than as a field. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	int32 ButterflyCount = 14;

	/**
	 * WHICH BIRD FLIES OVER WHICH COUNTRY.
	 *
	 * The voices were split four ways after the note about "crows in moor
	 * instead of regular bird song", and the PICTURE was not: one mesh flew
	 * over all twenty-seven grounds, so a citizen on the moor heard crows and
	 * watched a songbird, and on the shore heard gulls and watched a crow. It
	 * is the same fault one layer across and it survived because sound was the
	 * half somebody noticed.
	 *
	 * Keyed on the world's own word for the ground, exactly as `GroundVoices`,
	 * `Ambience` and the footfalls are. A word with no row of its own keeps
	 * `BirdMesh`, which is the fallback and is the crow.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TMap<FName, FIntervalFowl> SkyBirds;

	/** How many birds stand on a shore or in a square. More than the frogs,
	 *  because a flock is the point: three gulls on a beach is three gulls,
	 *  and twenty is a shore. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	int32 StandingCount = 16;

	// ---- AND WHAT FALLS OUT OF THE WOODS IN AUTUMN ----
	//
	// One mesh, two hues, for the butterflies' reason: an instanced component
	// carries one material. Gold and rust, which is a wood turning rather than
	// a wood that has turned -- every leaf the same colour is a filter, and two
	// is enough to read as a drift.

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<class UStaticMesh> LeafMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<class UMaterialInterface> LeafGold;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<class UMaterialInterface> LeafRust;

	/** How many at the height of autumn. Scaled DOWN by the season, so this is
	 *  the peak and not the constant: at `autumn` of a quarter it is a quarter
	 *  of this, which is a few leaves turning rather than a drift. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	int32 LeafCount = 26;

	/**
	 * AIR YOU CAN SEE LIGHT IN.
	 *
	 * The level has had a height fog since the beginning and it has only ever
	 * been a haze on the horizon -- a screen-space tint, with no idea that
	 * there is anything in front of it. Turning the volumetric path on makes
	 * the fog a real medium: the sun throws shafts through a gap in a roof,
	 * every hearth on the island glows in the air around it after dark, and
	 * the smoke that now leaves every chimney is lit from the side instead of
	 * being a grey shape pasted over the village.
	 *
	 * It is the single biggest thing the window can do with light, and it is
	 * also the most expensive, which is why it is a number a level sets rather
	 * than something compiled in.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	bool bVolumetricAir = true;

	/** How far out the lit air is computed, in centimetres. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	float HazeDepth = 24000.f;

	/**
	 * HOW MUCH AIR THERE IS ON A CLEAR DAY.
	 *
	 * Every other atmospheric number is authored here and this one was not: the
	 * hour read the density off whatever ExponentialHeightFog actor the level
	 * happened to contain, kept it as `BaseFog`, and scaled that up for rain.
	 * So the one value that decides how much of the island you can see was the
	 * only one nobody was choosing, and it was whatever somebody dropped into
	 * the level once.
	 *
	 * IT SHOULD NOT BE CLEAR TO THE HORIZON. The island is 896 by 512 tiles and
	 * seeing all of it at once makes it small, while the whole texture of this
	 * world is that walking somewhere costs real time. Haze is the cheapest
	 * thing that argues for size: a far shore that goes soft says there is more
	 * out there, and one you can read every tree on says there is not.
	 *
	 * Negative keeps whatever the level set, which is how a project with no
	 * opinion still works.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	float AirDensity = 0.018f;

	/**
	 * How forward-scattering the air is, from -1 to 1.
	 *
	 * This is the shaft knob. At zero the air scatters evenly and fog is fog;
	 * pushed towards one it scatters along the light's own direction, which is
	 * what makes a beam a beam. Real air is around 0.7 and looks it.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky", meta = (ClampMin = "-0.9", ClampMax = "0.9"))
	float HazeForward = 0.62f;

	/** What colour the air is when light goes through it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	FLinearColor HazeTint = FLinearColor(0.82f, 0.86f, 0.96f);

	/** How much of the sun's light the air catches. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	float SunHaze = 1.1f;

	/**
	 * And how much of a HEARTH'S. Much more than the sun's, and deliberately:
	 * a fire in the open at night is seen as a glow in the air long before
	 * anything it lights is, and that glow is the whole reason for lighting
	 * the fires at all from the distance this window watches from.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Fire")
	float FireHaze = 3.4f;

	/**
	 * How dark it has to get before the glow-worms come out: nought is noon
	 * and one is the middle of the night.
	 *
	 * At the old threshold of a twentieth they were lit through the whole of
	 * the afternoon -- a hard-edged pale green disc lying on the mud of the
	 * market place in full sun, because an unlit emissive circle does not care
	 * what else is going on. A glow-worm is a dusk animal and should arrive at
	 * dusk.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky", meta = (ClampMin = "0", ClampMax = "1"))
	float GlowAfter = 0.34f;

	/**
	 * THE AIR, which is the post process and belongs to the plugin.
	 *
	 * `AIntervalAir` spawns itself unbound at priority ten, OVER anything the
	 * level carries -- which is the right design and was worth finding out
	 * about the hard way: an afternoon went into tuning the level's own
	 * PostProcessVolume, and every property the air overrides was quietly
	 * winning. A level volume can still set what the air leaves alone, and
	 * nothing else.
	 *
	 * So the handful of numbers a world might want to differ on live here,
	 * where an asset can hold them and a script can write them.
	 *
	 * `ExposureAt` below zero keeps the automatic band, which is narrow on
	 * purpose (see AIntervalAir). At or above zero the exposure is PINNED
	 * there and the hour is the only thing that changes the brightness of the
	 * picture -- which is what a window onto a world with an hour in it
	 * probably wants, and is a matter of taste rather than of correctness.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Air")
	float ExposureAt = -1.f;

	/** How hard the tonemapper crushes the dark end. Lower opens shadows. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Air", meta = (ClampMin = "0", ClampMax = "1"))
	float FilmToe = 0.40f;

	/**
	 * HOW STEEP THE MIDDLE OF THE CURVE IS, which is contrast.
	 *
	 * This was 0.92 and fixed in code, on the reasoning that a world looked at
	 * for hours should not be shouting. Quiet became flat: with the sky light
	 * white and running at better than twice the sun, everything was pushed
	 * toward the middle from the light's end, and a gentle curve then declined
	 * to pull it back out. The two faults were separate and looked like one.
	 *
	 * It is a knob rather than a constant because contrast is a matter of
	 * taste and this world is looked at on a lot of different screens.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Air", meta = (ClampMin = "0.5", ClampMax = "1.5"))
	float FilmContrast = 1.04f;

	/**
	 * HOW MUCH COLOUR THERE IS.
	 *
	 * Was fixed at 1.04 in `AIntervalAir`, which is as close to "leave it
	 * alone" as makes no difference. It belongs beside the contrast for the
	 * same reason the contrast does: it is a matter of taste, this world is
	 * looked at on a lot of different screens, and neither is a fact about the
	 * world that a window may not have an opinion on.
	 *
	 * One is the picture the renderer hands over. Above one the greens, the
	 * thatch and the water get their colour back; far above it the whole
	 * island turns to poster paint, and the line between the two is a thing to
	 * be LOOKED at rather than argued about.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Air", meta = (ClampMin = "0.5", ClampMax = "2"))
	float FilmColour = 1.25f;

	/**
	 * AND WHAT COLOUR THE LIGHT IS CALLED WHITE, in kelvin.
	 *
	 * There was no white balance at all: the picture came out at whatever
	 * neutral the tonemapper assumed, which is 6500K and is daylight at noon
	 * in a clear sky. A world of thatch, timber, cut stone and hearths is not
	 * a noon-lit world, and the complaint it drew was the right one -- it
	 * reads cold.
	 *
	 * This is the temperature the renderer corrects FOR, so it works the way
	 * round that always surprises: ABOVE 6500 the image warms, because the
	 * light is being treated as cooler than it is and the correction pushes
	 * the other way.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Air", meta = (ClampMin = "4000", ClampMax = "10000"))
	float FilmWarmth = 7600.f;

	/**
	 * THE LAMP OVER WHOEVER IS INDOORS, by day and by night.
	 *
	 * A room with its roof dissolved and its walls cut to waist height is
	 * legible by day because the sky is in it. At night it is a black hole
	 * with a nameplate floating over it, so the window puts a hearth-coloured
	 * light above the citizen -- and that light has now been wrong in both
	 * directions three times running. Nine thousand blew the figure into a
	 * white blob; three thousand two hundred blew the floor out instead; nine
	 * hundred still did, because at night the exposure opens right up and the
	 * number that reads as a hearth at noon reads as a flare at midnight.
	 *
	 * THEY LIVE HERE SO THEY CAN BE TUNED WITHOUT A BUILD. Every previous
	 * round of this cost a compile, an editor restart and a walk back to a
	 * lit room, which is about four minutes to see one number. Out of the look
	 * asset they can be written by a script between two photographs.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Air", meta = (ClampMin = "0"))
	float LampByDay = 60.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Air", meta = (ClampMin = "0"))
	float LampByNight = 160.f;

	/** How far the lamp reaches, in centimetres. A room, not a bulb. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Air", meta = (ClampMin = "100"))
	float LampReach = 1050.f;

	/** Screen-space occlusion: a corner should darken, but not much. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Air", meta = (ClampMin = "0", ClampMax = "2"))
	float Occlusion = 0.45f;

	/**
	 * THE GATE: the door you come in through.
	 *
	 * Every other window has one -- a plate with the world's name on it, the
	 * theme playing, and the world itself moving behind the glass while you
	 * decide to go in. This window opens straight into somebody's life, which
	 * is abrupt in a way the others are not.
	 *
	 * It is only ever shown when there is a player controller to show it to,
	 * so Simulate -- which is how every photograph in these notes was taken --
	 * is untouched.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Gate")
	bool bGate = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Gate")
	TObjectPtr<class USoundBase> GateTheme;

	/** How far out the camera stands while the gate is up, in centimetres. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Gate", meta = (ClampMin = "500"))
	float GateReach = 4200.f;

	/** How high, and how fast it goes round: degrees a second. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Gate")
	float GateRise = 1900.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Gate")
	float GateTurn = 2.4f;

	/**
	 * AND WHERE THE WINDOW WATCHES FROM ONCE YOU ARE IN.
	 *
	 * The gate's camera does not hand the view back to the template's pawn
	 * when it opens -- it stops going round and settles behind the citizen,
	 * and stays there. That is not a shortcut, it is what this window IS: a
	 * view onto somebody's life in a world that is running whether or not
	 * anybody is looking. There is no pawn to drive. Handing the view back
	 * put a mannequin on the template's blue disc at the origin, which is
	 * sea, and is what "enter the world" meant for about ten minutes.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Gate", meta = (ClampMin = "100"))
	float WatchReach = 1250.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Gate")
	float WatchRise = 820.f;

	/**
	 * HOW FAR DOWN IT LOOKS, in degrees, which is the number anybody actually
	 * wants to turn.
	 *
	 * `WatchReach` and `WatchRise` are a distance out and a height up, and the
	 * angle is what falls out of them -- so tilting the camera means solving a
	 * triangle by hand and getting the distance wrong in the process. Set this
	 * and the pair above are re-derived from it, keeping their SLANT: the
	 * camera stays exactly as far from the citizen and only the angle moves,
	 * which is what "tilt" means and is not what changing either number alone
	 * does. Negative leaves the pair as they are.
	 *
	 * WHY IT IS WORTH A KNOB. This window showed no sky at all, at any zoom,
	 * and the reason was one number: at fifty degrees down with a field
	 * fifty-eight degrees tall, the TOP of the frame looks twenty-one degrees
	 * BELOW the horizon. Nothing in the air could ever be seen -- not a bird,
	 * not weather, not the rainbow the world has been reporting all along.
	 * The threshold is twenty-nine degrees and it is hard: shallower than that
	 * there is sky, steeper than that there is none.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Gate", meta = (ClampMin = "-1", ClampMax = "89"))
	float WatchPitch = -1.f;

	/**
	 * HOW MUCH OF THE FRAME IS SKY, which is what an angle was standing in for.
	 *
	 * `WatchPitch` fixes the camera's angle, and an angle does not decide how
	 * much sky you see: the FIELD does, and the vertical field depends on the
	 * shape of the window. Measured on two of them at the same pitch of
	 * twenty-four degrees:
	 *
	 *     16:9  window   vertical field 58.7   top of frame  +5.3 degrees
	 *     2.25  window   vertical field 48.0   top of frame   0.0 degrees
	 *
	 * The same camera, and one has a band of sky and the other has none at
	 * all, the horizon sitting exactly on the top edge. A phone in landscape
	 * is about 2.17 and would have had none either, which would have made the
	 * whole tilt pointless on the platform it was partly done for.
	 *
	 * So the number to set is the share of the frame above the horizon, and
	 * the angle is worked out from it and from the field the window actually
	 * has. Every shape of window, and the phone, then show the same sky.
	 * `WatchPitch` still wins where it is set, for anyone who wants an angle.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Gate", meta = (ClampMin = "0", ClampMax = "0.5"))
	float SkyShare = 0.12f;

	/** Which way the window stands, in degrees clockwise from north. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Gate")
	float WatchBearing = 218.7f;

	/** How lazily it follows. Larger is tighter; a citizen should not judder. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Gate", meta = (ClampMin = "0.1"))
	float WatchLag = 2.2f;

	/**
	 * GLOW-WORMS.
	 *
	 * Not a flourish borrowed from somewhere warmer: Lampyris noctiluca is an
	 * English hedgerow animal and a summer night in long grass is exactly
	 * where you would see one. They are placed by hashing the world tile they
	 * sit on, so the same tuft glows in every window and "past the third light
	 * along the hedge" is a direction somebody can give.
	 *
	 * The grounds they are found on are named by a level, like the thresholds.
	 * A world that names none simply has no glow-worms.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	TObjectPtr<class UStaticMesh> GlowMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	TObjectPtr<UMaterialInterface> GlowMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Sky")
	TSet<FName> GlowGround;

	/** The ground itself. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TObjectPtr<UMaterialInterface> GroundMaterial;

	/**
	 * HOW A WALL IS BUILT, keyed by the world's own word for it.
	 *
	 * `palisade` today; `wall.stone` or anything else the world grows, without
	 * a build. A word with an entry here is drawn as masonry by
	 * AIntervalStructures::BuildPalisades and is SKIPPED by the ordinary prop
	 * path, so the two never draw the same tile twice.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval")
	TMap<FName, FIntervalPalisade> Palisades;
};
