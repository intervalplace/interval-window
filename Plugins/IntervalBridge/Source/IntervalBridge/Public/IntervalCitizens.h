// IntervalCitizens.h -- the people and the beasts, drawn between two intervals.
//
// THE ONE RULE THIS FILE EXISTS TO KEEP. The world advances once a second.
// Everything smooth about this window is a number between 0 and 1 measured
// against that second, and that number is COSMETIC: it is never read back,
// never rounded into a position, never allowed to decide which tile anybody
// is standing on, and never consulted when an intent is made. A citizen is on
// the tile the last frame said they were on. The figure you can see sliding
// between two tiles is a drawing of a citizen, not the citizen.
//
// That distinction is the whole reason a renderer at 120 fps is safe to put in
// front of a world that ticks at 1 Hz. Break it -- let the drawn position feed
// a click, a reach test, or a "which tile am I on" -- and the window starts
// acting on an interval that has already passed, which is the failure that
// makes a smooth client walk one step and stop.
//
// So: nothing in this file is public except what it draws. There is no
// accessor for an interpolated position, on purpose.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IntervalTypes.h"
#include "IntervalStructures.h"
#include "Blueprint/UserWidget.h"
#include "IntervalCitizens.generated.h"

class UIntervalBridgeSubsystem;
class USkeletalMesh;
class USkeletalMeshComponent;
class UWidgetComponent;
class UTextBlock;
class UInstancedStaticMeshComponent;
class UAnimSequence;
class UFont;
class UStaticMeshComponent;
class UMaterialInterface;

/** One drawn person. Pooled by the world's id for them, so a name plate does not flicker. */
USTRUCT()
struct FIntervalCitizenView
{
	GENERATED_BODY()

	UPROPERTY(Transient)
	TObjectPtr<USkeletalMeshComponent> Mesh;

	/** The rest of the body, following the first one's pose. */
	UPROPERTY(Transient)
	TArray<TObjectPtr<USkeletalMeshComponent>> Limbs;

	UPROPERTY(Transient)
	TObjectPtr<UWidgetComponent> Plate;

	/**
	 * WHAT THEY JUST SAID, over their head.
	 *
	 * A separate component from the plate and not another line on it, because
	 * the plate is what somebody IS -- their name, their calling, how far they
	 * have come -- and it is there always. Speech is an event: it appears, it
	 * is read, it goes. Running the two together would mean a name that jumps
	 * about whenever anybody talks, and a line of talk that looks like a title.
	 *
	 * It is made the first time this person says anything, so the crowd in a
	 * market does not cost a widget each for silence.
	 */
	UPROPERTY(Transient)
	TObjectPtr<UWidgetComponent> Bubble;

	/** Wall-clock seconds the bubble should stay up until. */
	double BubbleUntil = 0.0;

	/**
	 * What to put in it, kept rather than written straight in.
	 *
	 * A UWidgetComponent does not build its user widget when it is created --
	 * it builds it when it is next ticked -- so setting the text at the moment
	 * somebody speaks wrote into a widget whose own children did not exist
	 * yet, and the bubble appeared over their head empty and in the wrong
	 * colours. Holding the words here and applying them from the tick, where
	 * the widget is certainly built, is the fix.
	 */
	FString Spoken;
	bool bSpokenFar = false;
	bool bSpokenShown = false;

	/**
	 * The most hit points this creature has ever been seen with.
	 *
	 * The world sends a beast's CURRENT health and never its maximum -- the
	 * maximum is in MOB_STATS, which is the engine's and not ours to copy. But
	 * a wound is a FRACTION, and without a maximum "14" says nothing: a troll
	 * at fourteen is nearly dead and a crow at fourteen is untouched.
	 *
	 * So the window remembers the highest it has seen. A creature is almost
	 * always met whole, so the first sighting is the maximum in practice; and
	 * if it is met already wounded the bar simply starts full and is honest
	 * from there, which is better than a number with no scale. It rises if a
	 * beast is ever seen higher, so a healed or respawned one corrects itself.
	 */
	int32 TopHp = 0;

	/**
	 * WHAT THEY HAD LAST INTERVAL, so a drop can be seen.
	 *
	 * The world sends hitpoints and never damage: a blow is the DIFFERENCE
	 * between two intervals, which is how `window-web` has always made its
	 * splats (§7ca). Starts at -1 so the first frame a body is seen on cannot
	 * read as a wound: somebody met already hurt has simply always been hurt as
	 * far as this window knows, and inventing a number over their head for it
	 * would be the window reporting a blow nobody struck.
	 */
	int32 LastHp = -1;

	/**
	 * A RUNG SOMEBODY ELSE CLIMBED.
	 *
	 * Standing is the sum of a citizen's skill levels, derived by the engine
	 * and already on every plate, so a rise of one IS a level gained and the
	 * window needs nothing new from the world to know it.
	 *
	 * -1 means never seen, which is why a stranger who walks into view at
	 * standing 300 is not congratulated for all three hundred of them.
	 *
	 * WHY THIS IS NOT A LINE IN THE CHAT. "When someone else levels up I think
	 * it should be visible too but without being spammy. So others can
	 * congratulate etc but also not being spammed to death by everyone
	 * leveling." The frame only carries citizens near enough to be drawn, so
	 * saying it over their head is limited by the thing that should limit it:
	 * whether you are standing near them. It also answers WHO, which a line in
	 * a feed has to spell out, and it cannot push anybody's conversation off
	 * the top of the screen.
	 */
	int32 StandingWas = -1;
	/** When that happened, so the plate can say so and then stop. */
	double RoseAt = -1e9;

	/** This citizen's own copy of the clothing material, holding their number. */
	UPROPERTY(Transient)
	TObjectPtr<class UMaterialInstanceDynamic> Cloth;

	/** Skirt, hood: hung on bones once, and left alone. */
	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> Wearing;

	/**
	 * Everything they are holding and wearing, in one list.
	 *
	 * Kept flat with a SIGNATURE of what it is showing, rather than a
	 * component per slot: a slot can want one piece or four now, and chasing
	 * that per slot is bookkeeping for a thing that changes when somebody
	 * picks up a sword and not otherwise.
	 */
	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> Kit;

	/**
	 * The dust under them, attached to the figure so it simply travels with
	 * them -- which is also how the emitter knows they are moving, since it
	 * spawns per unit of the component's own travel rather than per second.
	 */
	UPROPERTY(Transient)
	TObjectPtr<class UNiagaraComponent> Dust;

	/**
	 * WHAT A SPELL LEFT ON THEM, for as long as it lasts.
	 *
	 * ONE COMPONENT, NOT SIX. A citizen can carry several marks at once and
	 * drawing all of them would be a bonfire of overlapping effects around
	 * somebody who is, after all, still just standing there. So one component
	 * shows the mark that is worst, and `MarkWord` is what it is currently
	 * showing: when the word changes the asset and the colour are swapped,
	 * and when there is nothing left it is switched off.
	 */
	UPROPERTY(Transient)
	TObjectPtr<class UNiagaraComponent> Mark;

	/** Which mark that component is currently showing, or none. */
	FName MarkWord;

	/**
	 * A LAMP FOR THE ROOM YOU ARE IN.
	 *
	 * A building in this world has walls and a roof, and the sun is usually
	 * low, so the inside of one is honestly in shadow. Honestly and
	 * unreadably: "when you're inside a building it's pretty illegible what's
	 * going on in there". The roof already dissolves for whoever is under it;
	 * what is left is a dark room seen from above.
	 *
	 * So the citizen carries a light indoors and nothing outdoors, where the
	 * sun does the work and a lamp would only wash the ground out. It is on
	 * the LOCAL citizen alone: a lantern on everybody would light a street
	 * through its own walls.
	 */
	TObjectPtr<class UPointLightComponent> Lamp;

	/** How far they have walked since their last footfall, in centimetres. */
	float Walked = 0.f;

	/**
	 * THEIR PACE, AVERAGED, and which interval it was last averaged on.
	 *
	 * A citizen crosses one tile per interval and stands still for three, so
	 * the speed between the last two frames is 200 or it is 0 and never the
	 * truth, which is about fifty. Fed straight to the animation it flipped
	 * the clip's rate between its ceiling and its floor once a second. A pace
	 * is an average, so this is one -- taken once per INTERVAL, not once per
	 * frame, or it converges inside a sixth of a second and averages nothing.
	 */
	float Pace = 0.f;
	int64 PacedAt = -1;

	FString Carrying;

	/** Which of the wardrobe's outfits this citizen drew, or INDEX_NONE. */
	int32 Outfit = INDEX_NONE;

	/** Kept between intervals so somebody who stops does not snap back to facing north. */
	float Yaw = 0.f;

	/**
	 * WHICH WAY IT IS ACTUALLY POINTING, as opposed to which way it is going.
	 *
	 * A figure's heading is read off the difference between the tile it was on
	 * and the tile it is on, so it changes in quarter turns and eighth turns
	 * and nothing in between. Applied straight to the mesh, a citizen rounding
	 * a corner does not turn: they are facing east, and then on one frame they
	 * are facing north. This chases `Yaw` instead, which is the whole of the
	 * difference between a thing that walks and a thing that is being dragged
	 * around a board.
	 */
	float YawShown = 0.f;
	bool bYawKnown = false;

	bool bWalking = false;

	/** The word this citizen was last seen doing, so a motion is not restarted. */
	FName Verb;
	bool bSeenThisFrame = false;
};

/**
 * A speech bubble: a line of talk on a plate, over somebody's head.
 *
 * It has a board behind it and the name plate does not, and that is the point.
 * A name floating over a head reads as a label on the world; a line of speech
 * has to read as something a PERSON is doing, and the thing that says so is
 * the little panel it sits on -- the same ink and gilt as the chat log it is
 * also appearing in, so a player can see at a glance that the two are the
 * same words.
 */
UCLASS()
class INTERVALBRIDGE_API UIntervalBubbleWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual TSharedRef<SWidget> RebuildWidget() override;

	void Set(const FString& Text, bool bFar);

private:
	UPROPERTY() TObjectPtr<class UBorder> Edge;
	UPROPERTY() TObjectPtr<class UBorder> FaceOf;
	UPROPERTY() TObjectPtr<UTextBlock> Line;
};

/**
 * One name plate. A WIDGET, not a UTextRenderComponent.
 *
 * TextRender drew nothing here -- not at any size, from any angle, with font
 * and material explicitly assigned and the component reporting itself visible
 * and in range. Five rebuilds ruled out every cause outside the component. The
 * door then rendered UMG text perfectly at the first attempt in the same
 * viewport, which settled it: the fault is in TextRender, and the way through
 * is the machinery that already works.
 *
 * Drawn in SCREEN space, which also disposes of the question that cost two of
 * those rebuilds -- a screen-space widget always faces the camera and holds
 * its size, so there is no facing to get backwards and no distance at which
 * the text becomes unreadable before it is culled.
 */
UCLASS()
class INTERVALBRIDGE_API UIntervalPlateWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual TSharedRef<SWidget> RebuildWidget() override;
	void Set(const FString& Text, const FLinearColor& Colour, float Size);

	/** What they are doing this second, under the name and in its own hand. */
	/**
	 * The line under the name: what they are doing, in a smaller italic.
	 *
	 * `bCrowed` is for the one thing on that line that is an EVENT rather than
	 * a state. It is set upright and full size, because a rung climbed written
	 * in the same hand as "gather" is a rung nobody notices.
	 */
	void Doing(const FString& Text, float Size, bool bCrowed = false);

private:
	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> Label;

	/** The deed, on its own line and in its own hand. */
	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> Deed;
};

/**
 * A NUMBER WHERE THE BLOW LANDED.
 *
 * The world sends hitpoints and never damage, so a blow is the difference
 * between two intervals. Until this existed the only sign that anything had
 * connected was ten characters of bar on a nameplate crawling leftwards, which
 * tells you somebody is losing and never tells you by how much, or whether the
 * last swing was the lucky one.
 *
 * ITS OWN WIDGET, not a third line on the plate. The plate is what somebody IS
 * and the bubble is what they SAID; both belong to a person and stay with
 * them. A splat belongs to a MOMENT and to a place on the ground, it outlives
 * neither, and several of them exist at once over one head during a flurry.
 * Running it through the plate would mean six numbers fighting for one line.
 *
 * Screen space, like the plate, for the reason given there: it faces the
 * camera by construction and holds its size, so there is no facing to get
 * backwards and no distance at which it becomes unreadable before it is culled.
 */
UCLASS()
class INTERVALBRIDGE_API UIntervalSplatWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual TSharedRef<SWidget> RebuildWidget() override;

	/** The number, its colour, and how far through its life it is (0..1). */
	void Show(int32 Amount, const FLinearColor& Tint, float Through);

private:
	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> Figure;
};

/**
 * One number in flight: where it started, when, and what it says.
 *
 * `Delay` is what makes a flurry read as a burst rather than a stack. Six
 * blows land on the same interval and at the same place, so without it they
 * are six widgets at one point and a reader sees one number.
 */
USTRUCT()
struct FIntervalSplat
{
	GENERATED_BODY()

	UPROPERTY(Transient)
	TObjectPtr<UWidgetComponent> Widget;

	/** Where the body was when it was struck. The splat does not follow it. */
	FVector Origin = FVector::ZeroVector;

	double At = 0.0;
	float Delay = 0.f;

	/** Sideways offset in centimetres, so a burst fans instead of stacking. */
	float Fan = 0.f;

	int32 Amount = 0;

	/** A blow somebody took, rather than one they landed. */
	bool bOnMe = false;
};

UCLASS()
class INTERVALBRIDGE_API AIntervalCitizens : public AActor
{
	GENERATED_BODY()

public:
	AIntervalCitizens();

	/**
	 * WHERE THIS WINDOW LAST DREW SOMEBODY, in world space.
	 *
	 * Not where the world says they are. The world hands over whole tiles once
	 * an interval; everything between two intervals is this window's own
	 * interpolation, and a body is drawn at the interpolated place. Anything
	 * ELSE that follows a citizen has to follow the same place or the two
	 * disagree for most of every second.
	 *
	 * The camera is why this exists. It was following the TILE, which moves two
	 * hundred centimetres in one step once a second, and easing toward it --
	 * so it lurched forward and settled back on every tick, for the whole of a
	 * walk, while the citizen it was following glided. It was reported as the
	 * camera panning a little and snapping back, over and over, every tick.
	 */
	UFUNCTION(BlueprintPure, Category = "Interval")
	bool LastDrawnAt(const FString& Id, FVector& OutLocation) const;

	virtual void Tick(float DeltaSeconds) override;

	// ---- people ----

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|People")
	TObjectPtr<USkeletalMesh> CitizenMesh;

	/** A look asset to take the motions from; unset, the conventional one. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|People")
	TObjectPtr<class UIntervalLook> Look;

	/** Fallbacks for a project with no look asset. The table wins where it answers. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|People")
	TObjectPtr<UAnimSequence> IdleAnimation;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|People")
	TObjectPtr<UAnimSequence> WalkAnimation;

	/** The mannequin is about 180cm and stands on its feet, so this is usually 1. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|People")
	float CitizenScale = 1.f;

	// ---- beasts ----

	/**
	 * A look for each kind of mob, keyed by the world's own word for it, in
	 * exactly the shape AIntervalStructures uses. Nothing in C++ writes a word
	 * down; a kind with no entry is not drawn and is named in the log.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Beasts")
	TMap<FName, FIntervalPropKind> Mobs;

	/**
	 * THE BESTIARY THE LOOK HOLDS, PREFERRED OVER THE ONE ON THIS ACTOR.
	 *
	 * The same arrangement IntervalStructures already makes for its props, and
	 * for the same reason: the look asset is what the pipeline writes and the
	 * actor is what survives in the level when no asset answers.
	 *
	 * Without it the loop was simply open. `apply.py` READ the mob table off
	 * this actor, edited it, and wrote it to the LOOK -- while every draw here
	 * read the actor. So a mob's art could be corrected, saved, verified in the
	 * asset and still never appear: the goblins stayed engine cylinders through
	 * several rounds of "fixing" them, because nothing was reading the thing
	 * being fixed.
	 */
	const TMap<FName, FIntervalPropKind>& Bestiary() const;

	// ---- name plates ----

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Plates")
	bool bShowNamePlates = true;

	/**
	 * SOMEBODY SPOKE. Bound to the bridge, so the words go over the head that
	 * said them as well as into the log.
	 *
	 * UFUNCTION, and not decoratively: this is bound with AddDynamic, which
	 * finds the handler BY NAME through reflection and fails at runtime with
	 * one line in the log if the macro is missing.
	 */
	UFUNCTION()
	void Overheard(const FIntervalSaid& Said);

	/** How long a line stays over a head. Long enough to read, short enough to go. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Plates")
	float BubbleSeconds = 7.f;

	/** How far above the feet the bubble floats -- clear of the name plate. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Plates")
	float BubbleHeight = 330.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Plates")
	float PlateHeight = 215.f;

	/** Centimetres. Beyond this a plate is unreadable and only costs frame time. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Plates")
	float PlateMaxDistance = 9000.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Plates")
	float PlateSize = 13.f;

	// ---- §7ca: the numbers over a fight ----

	/** Off, and a fight is a bar crawling leftwards again. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Splats")
	bool bShowSplats = true;

	/** How long a number stays up. Long enough to read, short enough to clear. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Splats")
	float SplatSeconds = 1.1f;

	/** How far it rises over that life, in centimetres. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Splats")
	float SplatRise = 110.f;

	/** Where it starts, above the feet: over the body and under the plate. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Splats")
	float SplatHeight = 150.f;

	/** Seconds between the blows of one flurry, so six read as six. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Splats")
	float SplatStagger = 0.07f;

	/** Centimetres between the blows of one flurry, fanned about the body. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Splats")
	float SplatFan = 26.f;

	/**
	 * The ceiling on numbers in the air at once.
	 *
	 * A battle of forty citizens all flurrying is forty-odd widgets an
	 * interval, and a window that spends its frame on numbers has stopped
	 * being a window. Past this the oldest is retired early.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Splats")
	int32 SplatsAtOnce = 48;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Plates")
	FLinearColor PlateColour = FLinearColor(0.92f, 0.90f, 0.82f, 1.f);

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	UFUNCTION()
	void HandleFrame();

	/**
	 * Hide the pawn's own body, which is a camera and not a person.
	 *
	 * The project was started from the TopDown template and its character
	 * blueprint carries Epic's `SKM_Manny_Simple`. Every citizen in this
	 * world -- the player's own included -- is built from the frame the
	 * bridge sends and stood where the world says; the pawn exists only to
	 * hang a camera and an input mode off. Its mannequin was drawn ninety-five
	 * centimetres under the player for as long as this window has existed,
	 * which from a top-down camera reads as a pale figure crouched at their
	 * feet. See the note at the call site for why it is not done in BeginPlay.
	 */
	void HideTheCameraBody();

private:
	/** Whether HideTheCameraBody has found the pawn yet. */
	bool bCameraBodyHidden = false;

	/** The first eight hex digits of an id, as the browser window reads them. */
	static uint32 KeyOfId(const FString& Id);

	/** A stable number in 0..1 for one citizen, from the world's id for them. */
	static float UnitFromId(const FString& Id);

	/** What the world says this citizen is doing, in its own word. */
	FName VerbFor(const struct FIntervalEntity& Who, bool bMoving, int32 Outfit) const;

	/**
	 * WHICH ROW OF THE BESTIARY THIS CREATURE TAKES.
	 *
	 * A mob's `type` is not always the whole of what it is. An `incursion` wears
	 * a FACE -- woodwraith, gargoyle, drownling, wilds-shade, haunt -- chosen by
	 * what its target was doing when it came, and the browser windows have drawn
	 * one silhouette in five skins off that word since it existed. The field is
	 * already in the frame; nothing here had been asking for it.
	 *
	 * So the more specific row wins, exactly as it does for a node's
	 * `type.kind`: `incursion.woodwraith` if the level drew one, otherwise
	 * `incursion`, which is the generic and is what an unfamiliar face falls
	 * back to. A world that grows a sixth face still draws.
	 */
	FName MobKey(const struct FIntervalEntity& Mob) const;

	/**
	 * The row for a verb: the outfit's own table first, then the window's.
	 * See FIntervalOutfit::Motions for why an outfit may have one.
	 */
	const struct FIntervalMotion* MotionFor(int32 Outfit, FName Verb) const;

	void PlayVerb(class USkeletalMeshComponent* InMesh, FName Verb, int32 Outfit,
		float Speed) const;

	/** Hangs one piece on a bone, or moves an existing one to a new piece. */
	class UStaticMeshComponent* Hang(class USkeletalMeshComponent* On,
		class UStaticMeshComponent* Existing, const struct FIntervalPropPart& Piece,
		class UMaterialInterface* Fallback = nullptr) const;

	/** What this citizen is holding and wearing, from the world's own words. */
	void Dress(struct FIntervalCitizenView& View, const struct FIntervalEntity& Who, FName Verb) const;

	/** A beast's verb, out of the beast's own table. See FIntervalPropKind::Motions. */
	void PlayBeast(class USkeletalMeshComponent* InMesh, const struct FIntervalPropKind& Kind,
		FName Verb, const FString& Id, float Speed) const;

	/** Whether any row exists for a verb, in the outfit's table or the window's. */
	bool HasMotion(int32 Outfit, FName Verb) const;

	/** What the world says is in a slot, or NAME_None. */
	static FName Wearing(const struct FIntervalEntity& Who, const TCHAR* Slot);

	/**
	 * GIVES ONE PERSON THEIR OWN COLOURS.
	 *
	 * The art names every region of a figure -- Skin, Hair, Eye, Beige, Gold --
	 * and each name is its own material carrying its own colour. So a citizen
	 * is NOT painted over with one material; each of their materials is taken
	 * as it stands and given one number, `Shift`, which is them. What that
	 * number is allowed to move is set per material from its name, once, when
	 * the art is imported: eyes not at all, skin a little, cloth freely.
	 *
	 * The dyed instances are shared between citizens who land on the same
	 * shift, because there is no visible difference between two people dyed
	 * identically and a great deal of difference in how many instances a full
	 * street costs.
	 */
	void Dye(class USkeletalMeshComponent* Piece, class UMaterialInterface* Fallback,
		float Shift);

	/**
	 * Where to draw an entity right now: its last interval's tile, its
	 * previous one, and the fraction of a second between them. Returns false
	 * for anybody who has only just appeared, who is simply placed.
	 *
	 * IT STARTS EACH STRIDE FROM WHERE THE FIGURE ACTUALLY IS. Lerping from
	 * the previous TILE is right only if the previous stride finished, and
	 * intervals do not arrive on time: measured on this world they land
	 * anywhere between 744 and 1032 milliseconds apart. An early one caught a
	 * figure three quarters of the way across a tile and restarted the lerp
	 * from the tile behind, which snaps them half a metre backwards and then
	 * drags them forwards again -- several times a minute, at exactly the
	 * moment the eye is following them. Beginning from the drawn position
	 * instead costs one vector per entity and cannot snap, because the new
	 * stride starts where the old one had got to.
	 */
	bool DrawnPosition(const FString& Id, const FIntervalEntity& Now,
		const TMap<FString, FIntervalEntity>& Before, float Alpha, int64 Tick,
		FVector& OutLocation, bool& bOutMoving);

	/** Where each entity was last drawn, and for which interval. */
	struct FIntervalStride
	{
		FVector From = FVector::ZeroVector;
		FVector At = FVector::ZeroVector;
		int64 Tick = 0;
	};
	TMap<FString, FIntervalStride> Strides;

	/** One footfall, from the pool of voices. */
	void Footfall(const struct FIntervalFootfall& Fall, const FVector& At);

	/**
	 * THE SOUND OF A DEED, ONCE PER DEED.
	 *
	 * `deed` is the world's record of what a citizen did on this interval and
	 * it is present for exactly that interval. But a frame arrives once a
	 * second and the window draws sixty times in between, so reading it
	 * straight would sound the same cast every frame until the next one came.
	 * This remembers the last deed heard from each citizen and speaks only
	 * when it changes.
	 *
	 * AN ONGOING ACTION IS THE OTHER HALF, and it was missing entirely. An
	 * instant deed happens once; `gather` and the two attacks run on by
	 * themselves, interval after interval, and a rule that speaks only when
	 * the word CHANGES gives a citizen one axe blow and then ten minutes of
	 * silent chopping. So an action is sounded once per world interval for as
	 * long as it runs, which is also the rate the blows actually land at.
	 */
	void DeedHeard(const FString& Id, const struct FIntervalEntity& Who,
		const FName& Verb, const FVector& At, bool bOngoing, int64 Tick);

	/** The last deed sounded for each citizen, so one deed makes one noise. */
	TMap<FString, FName> LastDeed;

	/** And the interval it was sounded on, which is what paces an action. */
	TMap<FString, int64> LastDeedTick;

	/**
	 * §7dn/§7dq: THE THRESHOLD TILE, KEPT BECAUSE `VerbFor` CANNOT SEE A FRAME.
	 *
	 * The two gaps on the island that a citizen does not walk through. The
	 * frame carries the tile only when somebody is within two of it, so this is
	 * -1 almost always, and it is read where the walk is settled rather than
	 * passed down: `VerbFor` takes one entity and no frame, and threading a
	 * whole frame through it to answer one question about one tile would make
	 * every other caller carry it too.
	 */
	int32 ThresholdTileX = -1;
	int32 ThresholdTileY = -1;

	void UpdatePeople(float Alpha, const FVector& ViewLocation, bool bHaveView,
		float DeltaSeconds);
	void UpdateBeasts(float Alpha, float DeltaSeconds, const FVector& ViewLocation);

	UPROPERTY(Transient)
	TMap<FString, FIntervalCitizenView> Citizens;

	UPROPERTY(Transient)
	TMap<FName, TObjectPtr<UInstancedStaticMeshComponent>> BeastPools;

	/** Which mob id sits at which instance index, per kind. Rebuilt only when the cast changes. */
	TMap<FName, TArray<FString>> BeastOrder;

	/** One component per beast that has a skeleton, keyed by the world's id. */
	UPROPERTY(Transient)
	TMap<FString, FIntervalCitizenView> BeastViews;

	/**
	 * Numbers in flight, and the widgets they are borrowing.
	 *
	 * POOLED, because a splat lives about a second and a fight makes them by
	 * the dozen: making and destroying a UWidgetComponent at that rate is the
	 * kind of cost that does not show up until somebody is in a real battle,
	 * which is the worst moment to find it. A retired splat hands its widget
	 * back and the next blow takes it again.
	 */
	UPROPERTY(Transient)
	TArray<FIntervalSplat> Splats;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UWidgetComponent>> SpareSplats;

	/** Put a number in the air over a place. See §7ca. */
	void Splat(const FVector& Where, int32 Amount, float Fan, float Delay, bool bOnMe);

	/** Work out what a body just took, and say it. */
	void SplatsFor(struct FIntervalCitizenView& View, const struct FIntervalEntity& Body,
		const FVector& Where, bool bOnMe);

	/** Move, fade and retire the ones in the air. */
	void DriveSplats();

	UPROPERTY(Transient)
	TObjectPtr<UIntervalBridgeSubsystem> Bridge;

	/** The weather collection, read for how wet and how windy it is. */
	UPROPERTY(Transient)
	TObjectPtr<class UMaterialParameterCollection> Weathers;

	UPROPERTY(Transient)
	TObjectPtr<class AIntervalGround> Ground;

	/**
	 * A ROUND-ROBIN OF VOICES FOR FEET, rather than one spawned per step.
	 *
	 * A spawned sound takes its attenuation from an asset, and these want
	 * theirs from the look -- so they are components this actor owns, with
	 * their settings written on them, handed out in turn. It also caps the
	 * cost: however many people are crossing a market place, there are eight
	 * footfalls in the air at once and the ninth takes the oldest voice.
	 */
	UPROPERTY(Transient)
	TArray<TObjectPtr<class UAudioComponent>> Feet;

	int32 NextFoot = 0;

	/** One dyed instance per (material, shift), shared by everyone who matches. */
	UPROPERTY(Transient)
	TMap<FString, TObjectPtr<class UMaterialInstanceDynamic>> Dyed;

	uint64 LastCastDigest = 0;
	TSet<FName> Reported;
};
