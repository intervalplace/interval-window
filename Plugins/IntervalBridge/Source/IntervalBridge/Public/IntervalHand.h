// IntervalHand.h -- the one place a citizen's intentions become deeds.
//
// RECONSTRUCTED. This file was destroyed by a careless `open(path, "w")` in a
// tooling script -- Python truncates before it reads -- and rebuilt from the
// three records that survived: every definition in IntervalHand.cpp, the
// UFUNCTION and UPROPERTY list UHT had already generated, and the members other
// files reach for. The behaviour is the .cpp's and is unchanged; what was lost
// was the prose, and where a comment mattered it has been written again rather
// than guessed at.
//
// WHAT THIS ACTOR IS. It turns a click, or a line in a script, into one of the
// world's own verbs and hands it to the bridge to be signed. It decides nothing
// about whether a deed is legal: the world owns that, refuses what it likes,
// and this only has to ask honestly and say plainly when the answer is no.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IntervalTypes.h"
#include "IntervalHand.generated.h"

class UIntervalBridgeSubsystem;

/**
 * One line of the feed: something the window has to say to whoever is holding
 * it. A refusal, a chat line, or a note that a deed could not be sent.
 */
USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalFeedLine
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Interval|Feed")
	FString Text;

	UPROPERTY(BlueprintReadOnly, Category = "Interval|Feed")
	int64 Tick = 0;

	/** Refusals are shown in the colour of a refusal; chat is not. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval|Feed")
	bool bRefusal = false;

	/** Wall-clock seconds when it was said, for fading it out. Not replicated. */
	double At = 0.0;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FIntervalFeedLineSignature,
	const FIntervalFeedLine&, Line);

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(
	FIntervalOptionsAsked, const TArray<FIntervalTarget>&, Targets);

UCLASS()
class INTERVALBRIDGE_API AIntervalHand : public AActor
{
	GENERATED_BODY()

public:
	AIntervalHand();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void Tick(float DeltaSeconds) override;

	/** The feed, newest last. The panel draws it; nothing else may write it. */
	UFUNCTION(BlueprintPure, Category = "Interval|Feed")
	const TArray<FIntervalFeedLine>& GetFeed() const { return Feed; }

	UPROPERTY(BlueprintAssignable, Category = "Interval|Feed")
	FIntervalFeedLineSignature OnFeedLine;

	/** A click on the ground walks there. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Hand")
	bool bClickToWalk = true;

	/**
	 * The old text overlay in the corner. Off: everything on it is now drawn
	 * properly elsewhere. See the note where it used to be spawned.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Hand")
	bool bShowOldPanel = false;

	/** Keep asking to be let in, once an interval, until we are standing somewhere. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Hand")
	bool bEnterAutomatically = false;

	/**
	 * Whether this actor draws the feed itself.
	 *
	 * Off, because IntervalPanel draws it properly and two copies of every
	 * refusal on screen is worse than none.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Feed")
	bool bDrawFeed = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Feed", meta = (ClampMin = "1"))
	int32 FeedLines = 6;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Feed", meta = (ClampMin = "0"))
	float FeedSeconds = 12.f;

	/**
	 * Furthest a single deed may ask for. The world may still refuse fewer.
	 *
	 * MATCHED TO THE WORLD, which allows WALK_MAX_STEPS = 512 and says in as
	 * many words that "a single deed can carry a citizen across the map and no
	 * further". This was 24, and that was a window-side cap with nothing behind
	 * it: it never changed WHERE a citizen went, only how many deeds the journey
	 * cost -- and deeds are not free, each one spending an interval of a
	 * citizen's ninety-minute allowance.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Hand", meta = (ClampMin = "1"))
	int32 MaxSteps = 512;

	UFUNCTION(BlueprintCallable, Category = "Interval|Feed")
	void Say(const FString& Text, int64 Tick, bool bRefusal);

	/**
	 * HOW TALL A THING IS ASSUMED TO BE WHEN YOU CLICK ON IT, in centimetres.
	 *
	 * The cursor used to pick a tile by crossing the ray with the ground plane
	 * and nothing else, which makes a thing's clickable area its FOOTPRINT: two
	 * metres by two. Everything in this world is drawn standing up. A signpost
	 * is three metres of post, a tree is seven, a keeper is a person -- and a
	 * click anywhere above their feet sent a ray straight over the top of them
	 * to land on the ground BEHIND, which is a different tile and usually an
	 * empty one. From a low camera the miss grows without limit: at ten degrees
	 * above the horizon the ground under a three-metre post is seventeen metres
	 * further away, which is eight tiles wrong.
	 *
	 * That is the whole of "I click all over the thing and nothing happens".
	 * The thing was never under the cursor; only its feet were, and its feet
	 * are the one part of it a player does not aim at.
	 *
	 * So the ray is crossed with a standing COLUMN on each tile that holds
	 * something, and the nearest column it actually pierces wins. One height
	 * for everything is deliberately blunt: a per-type table would be a second
	 * copy of what the window draws, and the second copy is always the one that
	 * is wrong. What it costs is that a tall tree is still a little
	 * under-clickable near its crown, and a low stone a little over-clickable
	 * above it, and neither is a thing anybody can feel.
	 *
	 * Ground is unaffected: a ray that pierces no column falls through to z = 0
	 * exactly as before, so walking to open country is the same click it was.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Hand", meta = (ClampMin = "0"))
	float PickHeight = 260.f;

	/**
	 * THE MARK A CLICK LEAVES, and why there are two of them.
	 *
	 * A player who clicks needs to know what they just told their citizen to
	 * do, BEFORE it happens: the world answers on the next interval, which is
	 * a whole second of not knowing whether the click landed on the ore or on
	 * the grass behind it. The Top Down template's blue cross said only "a
	 * click happened here", which is the least useful of the three things it
	 * could have said.
	 *
	 * So the mark says WHICH KIND of thing was filed, and the two are made
	 * different in shape as well as colour, because colour alone is no answer
	 * for the colour-blind and no answer at all on a bright field:
	 *
	 *   WALKING is a RING on the ground. A place, with nothing in it: you are
	 *   going there.
	 *
	 *   ACTING is four CORNER BRACKETS round the tile. A frame holds a thing
	 *   rather than naming a spot: you are doing something to what stands
	 *   here.
	 *
	 * Both settle inward over their life and fade out, so the mark is loudest
	 * at the instant it answers the click and gone before it can clutter.
	 */
	// NOT `bShowMark`: Unreal exposes a UPROPERTY and a UFUNCTION under the
	// same lower-case name to Python, so a flag called `bShowMark` and a
	// function called `ShowMark` both arrive as `show_mark` and the flag wins.
	// The symptom is "'bool' object is not callable" from a tool that looks
	// like it is calling the function and is in fact calling the field.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Hand")
	bool bDrawMarks = true;

	/** How long a mark lasts, in seconds. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Hand", meta = (ClampMin = "0.05"))
	float MarkSeconds = 0.85f;

	/** How far above the ground it lies, so it does not fight the turf. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Hand", meta = (ClampMin = "0"))
	float MarkLift = 5.f;

	/** The ring: going somewhere. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Hand")
	FLinearColor MarkWalkColour = FLinearColor(0.74f, 0.92f, 0.78f);

	/** The brackets: doing something to what stands there. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Hand")
	FLinearColor MarkActColour = FLinearColor(1.f, 0.72f, 0.30f);

	/** Put a mark on a tile. `bAction` chooses brackets over a ring. */
	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void ShowMark(int32 TileX, int32 TileY, bool bAction);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	bool TileUnderCursor(int32& OutX, int32& OutY) const;

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Deed(const FString& Verb, const TMap<FString, int32>& Numbers, const TMap<FString, FString>& Words);

private:
	/**
	 * Which tiles hold something, rebuilt once an interval.
	 *
	 * `TileUnderCursor` asks this up to sixty-four times for one cursor
	 * position and is itself called more than once a frame, and the frame
	 * carries thousands of nodes. Asking the frame each time would be a
	 * scan of all of them per step. Mobs move every interval and nodes do
	 * not, so the whole set is simply rebuilt when the tick changes.
	 */
	mutable TSet<int64> StoodOn;
	mutable int64 StoodOnAt = -1;
	void FreshenStoodOn() const;

	/** The mark's own mesh, rebuilt each frame while one is alive. */
	UPROPERTY(Transient)
	TObjectPtr<class UProceduralMeshComponent> Mark;

	FIntPoint MarkTile = FIntPoint::ZeroValue;
	double MarkAt = 0.0;
	bool bMarkAction = false;
	/** Whether a section exists, and of which shape, so it is UPDATED and not
	 *  torn down and rebuilt sixty times a second. */
	bool bMarkBuilt = false;
	bool bMarkBuiltAction = false;
	void DriveMark();
	static int64 TileKey(int32 X, int32 Y) { return static_cast<int64>(X) * 1000003LL + Y; }
public:

	/**
	 * A RIGHT CLICK HAPPENED, and these are the things under it.
	 *
	 * The hand does not draw the menu -- it has no business knowing what a
	 * widget is -- it says what was pointed at and the panel lists it. An
	 * empty broadcast means "close whatever is open", which is what a left
	 * click sends.
	 */
	UPROPERTY(BlueprintAssignable, Category = "Interval|Hand")
	FIntervalOptionsAsked OnOptions;

	// ---- POINTING AT THINGS ----
	//
	// Until this, a player could do exactly one of the world's sixty-nine
	// verbs -- walk -- because there was no way to say WHICH tree. Ninety-odd
	// BlueprintCallable deeds sat behind a text file nobody but the automation
	// harness ever wrote to.
	//
	// The model is RuneScape's, and it was asked for by name: left click does
	// the default thing, right click lists everything when there is more than
	// one. It suits a world where a citizen is as likely to want to trade with
	// somebody as to hit them, and where the difference cannot be guessed from
	// a single click.

	/** One thing that can be pointed at. */
	UFUNCTION(BlueprintPure, Category = "Interval|Hand")
	TArray<FIntervalTarget> TargetsAt(int32 TileX, int32 TileY) const;

	/** Whatever is under the mouse, nearest the cursor first. */
	UFUNCTION(BlueprintPure, Category = "Interval|Hand")
	TArray<FIntervalTarget> TargetsUnderCursor() const;

	/**
	 * Every option a target offers, in the order they should be listed: its
	 * own verbs first, then the ones that are always available.
	 */
	UFUNCTION(BlueprintPure, Category = "Interval|Hand")
	TArray<FIntervalOption> OptionsFor(const FIntervalTarget& Target) const;

	/**
	 * Do one of them. The verb decides which field carries the target, which
	 * is the only thing this needs to know about any of them -- a node goes in
	 * `nodeId`, a mob in `mobId`, a citizen in `targetId`.
	 */
	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void ActOn(const FString& Verb, const FIntervalTarget& Target);

	/**
	 * The verb a left click would perform right now, or empty for bare ground.
	 *
	 * The cursor changes shape by it: a pickaxe over a seam, a sword over a
	 * beast. That is the whole reason a window like this draws its own
	 * pointer -- so it can say what a click will DO before it is made.
	 */
	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	FString VerbUnderCursor() const;

	/**
	 * WHAT THIS VERB COULD BE ABOUT, HERE.
	 *
	 * Three of the world's verbs name a THING as well as a target: `buy` an
	 * item, `smith` a recipe, `fletch` a make. Each was flattened into the
	 * main menu -- one line per good, per recipe, per make -- which for a
	 * stall with a dozen goods is a dozen lines of one idea and pushes
	 * everything else off the bottom. "We should have right click fletch log
	 * and then bring up a menu, instead of all the fletch options appearing
	 * in one column."
	 *
	 * So the menu shows the verb once and asks HERE for the choices when the
	 * line is chosen. One place answers for all three, which is the point:
	 * the fourth such verb costs a case, not a fourth copy of the machinery.
	 *
	 * Empty means the verb is not one of those, or there is nothing to choose
	 * from -- a stall whose goods have not arrived, an anvil whose recipes the
	 * citizen cannot afford.
	 */
	TArray<FIntervalOption> ChoicesFor(const FIntervalTarget& Target,
		const FString& Verb, const FString& SoFar = FString()) const;

	/** As ActOn, for the verbs that name a thing as well as a place. */
	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void ActOnWith(const FString& Verb, const FIntervalTarget& Target,
		const FString& Argument);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Plain(const FString& Verb);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Gather(const FString& NodeId);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Attack(const FString& MobId, const FString& Style);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void AttackPerson(const FString& PlayerId, const FString& Style);

// ---------------------------------------------------------------------------
// AND THE FIFTEEN THE FIRST PASS MISSED.
//
// The first sweep read the world's schema table with a regular expression that
// only matched entries written on ONE LINE. Twenty-one were spread over
// several and came back looking like verbs that take no arguments at all --
// which is a worse failure than missing them, because a verb wired with the
// wrong fields is filed, refused, and looks like a rule of the world.
//
// These are the ones with a real validator `case` behind them. `cook`, `eat`,
// `harvest`, `plant` and `smelt` are in here: most of what a citizen does with
// their hands once they stop walking about.

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Brew(const FString& NodeD, int32 Slot);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Bury(int32 Slot);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Collect(const FString& NodeD);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Cook(int32 Slot);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Deposit(int32 Slot);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Dismantle(const FString& NodeD);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Eat(int32 Slot);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Harvest(const FString& NodeD);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Invoke();

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Plant(int32 Slot);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Saw();

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Smelt(const FString& Recipe);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Stoke(const FString& NodeD, int32 Slot);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Stop();

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Wield(int32 Slot);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Unwield(const FString& Gear);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Buy(const FString& Item);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Drop(int32 Slot);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void PickUp(const FString& GroundId, bool bConfirm);

	UFUNCTION(BlueprintCallable, Category = "Interval|Spells")
	void Cast(const FString& Spell);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Haul(const FString& NodeId);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Unload(const FString& NodeId);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Smith(const FString& Recipe);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void ClaimName(const FString& Name);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Follow(const FString& TargetId);

	UFUNCTION(BlueprintCallable, Category = "Interval|Spells")
	void Still(const FString& Target);

	UFUNCTION(BlueprintCallable, Category = "Interval|Spells")
	void MendOther(const FString& Target);

	UFUNCTION(BlueprintCallable, Category = "Interval|Spells")
	void Seal(const FString& GroundId);

	UFUNCTION(BlueprintCallable, Category = "Interval|Spells")
	void Unmake(const FString& GroundId);

	UFUNCTION(BlueprintCallable, Category = "Interval|Spells")
	void Transmute(int32 Slot);

	UFUNCTION(BlueprintCallable, Category = "Interval|Spells")
	void Waking(const FString& TargetId);

	UFUNCTION(BlueprintCallable, Category = "Interval|Spells")
	void Rot(const FString& TargetId);

	UFUNCTION(BlueprintCallable, Category = "Interval|Spells")
	void Taking(const FString& TargetId);

	UFUNCTION(BlueprintCallable, Category = "Interval|Spells")
	void Withering(const FString& TargetId);

	UFUNCTION(BlueprintCallable, Category = "Interval|Spells")
	void TurnBook();

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Release();

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Deliver(int32 Slot);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Consign(const TArray<int32>& Slots);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	bool WalkTo(int32 TileX, int32 TileY);

	/**
	 * Walk somewhere far off, round whatever is in the way.
	 *
	 * `WalkTo` files ONE run and the world walks it until something stops it,
	 * which for anything past the next building is immediately. That is fine
	 * for a click on ground the player can see -- they can see what is in the
	 * way -- and useless for a click on the MINIMAP, which is the one control
	 * whose whole purpose is to ask for a journey. A map click that stops
	 * against the first wall is a map click that does not work.
	 *
	 * So this searches first, over the tiles the window knows about: a tile
	 * with a node standing on it is closed, and so is water. The route is kept
	 * and its corners are filed one at a time as each leg finishes. It is not
	 * cleverer than a player -- it is what a player does when they look at the
	 * map and pick their way round the town.
	 */
	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	bool WalkRoute(int32 TileX, int32 TileY);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Enter();


	/**
	 * ARCHIVE AND RESTORE NEED A PROOF THIS WINDOW CANNOT MAKE.
	 *
	 * Their schemas want a `path` -- an object carrying `bits` and a list of
	 * `sibs`, which is a Merkle proof -- and `restore` wants a whole `record`
	 * besides. Those come from the archive, not from a citizen's hand, and
	 * nothing on this side holds one. Filed as they stand they are refused for a
	 * missing field, which is the world being right.
	 *
	 * They are left declared, and left honest: when this window learns to read
	 * the archive it will have a proof to pass and these will take it. Until
	 * then they are a wire with nothing on the end, and saying so here is better
	 * than a method that looks usable and never is.
	 */
	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Archive(const FString& Subject);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Befriend(const FString& TargetId);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Char(const FString& NodeId);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Charter(int32 Slot);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Dedicate(const FString& NodeId, int32 Pay);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Drink();

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Fletch(int32 Slot, const FString& Make);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Found(int32 X, int32 Y);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Grave(const FString& NodeId, const FString& Target);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Grind(int32 Slot);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Kindle();

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Lay(const FString& NodeId, int32 N);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Lift(const FString& NodeId);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Light(int32 Slot);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Move(int32 Dx, int32 Dy);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Nock(int32 Slot);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Offer(int32 Slot);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Pay();

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Restore();

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Rifle(const FString& NodeId, const FString& Item);

	// ---------------------------------------------------------------------
	// THE THIRTEEN THAT WERE STILL MISSING.
	//
	// This window was measured at seventy-one of the world's verbs and the
	// number was believed. It is eighty-four: an audit against the engine's own
	// validator -- every word that has BOTH a `case` in validate() and a row in
	// INPUT_SCHEMAS, which is the engine's own definition of a verb -- found
	// thirteen more. The first sweep's regex only matched schema rows that
	// began a line, and several share a line with the row before them
	// (`raise_market: {}, dismantle_market: {},`). That is the SAME mistake,
	// in the same table, that cost twenty-one verbs the first time.
	//
	// What was missing is not marginal. A citizen could not raise a market,
	// stock it, price it, take its coin or pull it down; could not offer a
	// trade to another citizen, accept one, or cancel one. Two whole economies
	// -- the one between citizens and the one a citizen runs themselves.

	/** Put up a market stall of your own. */
	UFUNCTION(BlueprintCallable, Category = "Interval|Market")
	void RaiseMarket();

	/** Put a slot of the pack on your own stall's shelf. */
	UFUNCTION(BlueprintCallable, Category = "Interval|Market")
	void StockMarket(int32 Slot);


	/** What your stall asks for what is on it. */
	UFUNCTION(BlueprintCallable, Category = "Interval|Market")
	void PriceMarket(int32 Ask);

	/** Take the coin your stall has made. */
	UFUNCTION(BlueprintCallable, Category = "Interval|Market")
	void TakeMarket();

	/** Pull your stall down. Whatever is on the shelf SPILLS. */
	UFUNCTION(BlueprintCallable, Category = "Interval|Market")
	void DismantleMarket();

	/**
	 * AN OFFER NAMED BUT NOT YET PRICED.
	 *
	 * The menu can ask "which of these eight sums"; it cannot ask "how many".
	 * So the last line of the price page hands the question to a box, and
	 * these hold the offer in the meantime: who it is for and which slot goes
	 * across. The interface watches them -- it is already redrawing the trade
	 * plate every interval -- rather than being told through a delegate, which
	 * is one more thing to unbind when the hand goes away.
	 */
	UPROPERTY() FString Asking;
	UPROPERTY() int32 AskingSlot = -1;

	/**
	 * ---- AND THE SAME BOX FOR EVERY OTHER NUMBER THE WORLD WANTS ----
	 *
	 * Four deeds take a figure and nothing else can supply one: a stall's
	 * price, how many planks to lay on a span, what to pay at a dedication,
	 * how long a stint runs. A menu cannot ask "how many"; it can only offer a
	 * handful of answers and hope one of them is the one you meant.
	 *
	 * So the box that was built to price a trade asks for all of them. When
	 * `AskingVerb` is set the plate puts it up with `AskingFor` as the prompt,
	 * and the figure typed is filed in `AskingField` on `AskingOn`.
	 */
	UPROPERTY() FString AskingVerb;
	UPROPERTY() FString AskingField;
	UPROPERTY() FString AskingFor;
	UPROPERTY() FIntervalTarget AskingOn;

	/**
	 * Offer a trade to another citizen.
	 *
	 * The one deed in the world with four fields of three different shapes, so
	 * it builds its own JSON like `consign` does. Both demand fields are always
	 * sent explicitly -- an item trade carries `wantGold: 0` and a gold trade
	 * carries `wantItem: null` -- because the engine says in as many words that
	 * "omission is not a representation".
	 */
	UFUNCTION(BlueprintCallable, Category = "Interval|Trade")
	void OfferTrade(const FString& ToPlayerId, const TArray<int32>& GiveSlots,
		const FString& WantItem, int32 WantGold);

	/** Take a trade somebody has offered you. */
	UFUNCTION(BlueprintCallable, Category = "Interval|Trade")
	void AcceptTrade(const FString& FromPlayerId);

	/** Withdraw an offer you made. */
	UFUNCTION(BlueprintCallable, Category = "Interval|Trade")
	void CancelTrade();

	/** Build a brewpot. */
	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void BuildBrewpot();

	/** Bank everything, rather than one slot at a time. */
	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void DepositAll();

	/** Read a chart that is in the pack. */
	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void ReadChart(int32 Slot);

	/** The recall spell: back to where you anchored. */
	UFUNCTION(BlueprintCallable, Category = "Interval|Spells")
	void Recall(const FString& ToId);

	/** Which face this citizen wears, 0-255. */
	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void SetLook(int32 Look);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Sail();

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Sapling(const FString& NodeId);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Setbuck();

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Sound();

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Gambit(const FString& TargetId, const FString& Style);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Stamp(int32 Slot);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Stint(int32 N);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Survey();

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Swear(const FString& Calling);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Turn();

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Unfollow();

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Unfriend(const FString& TargetId);

	UFUNCTION(BlueprintCallable, Category = "Interval|Hand")
	void Withdraw(const FString& Item, int32 Qty);
protected:
	UFUNCTION()
	void HandleRefused(const FIntervalRefusal& Refusal);

	UFUNCTION()
	void HandleChat(const FIntervalSaid& Said);

private:
	/**
	 * A DEED WAITING ON A WALK.
	 *
	 * Adjacency in this world is Manhattan distance one, and a deed filed from
	 * further off is refused with nothing said about distance -- which from
	 * the other side of the glass reads as the click having done nothing.
	 * So a click on something out of reach walks there and remembers what it
	 * was for, which is what a citizen would have done anyway.
	 */
	FString Pending;
	FIntervalTarget PendingOn;
	FString PendingWith;
	bool bMenuOpen = false;

	UPROPERTY(Transient)
	TObjectPtr<UIntervalBridgeSubsystem> Bridge;

	UPROPERTY()
	TArray<FIntervalFeedLine> Feed;

	/**
	 * WHERE A CLICK ASKED FOR, and how far through answering it we are.
	 *
	 * One `walk` is one straight run, so a click that is not on a ray out of
	 * where you stand needs the remainder afterwards. Two runs reach anywhere:
	 * the diagonal part, then the straight remainder.
	 */
public:
	/**
	 * Set by a widget that has already answered this frame's click.
	 *
	 * The hand reads the mouse from the player's input, and a widget that
	 * consumes a click does not stop that -- so a right click on a pack slot
	 * opened the slot's menu AND the world's, and the world's won, offering to
	 * walk to tile 0,0 because that is what is under a cursor that is over the
	 * interface. Whoever answers first says so here.
	 */
	int32 UiTookTheClick = 0;
	/** Where a right press landed, to tell a menu click from a camera turn. */
	FVector2D RightWentDown = FVector2D::ZeroVector;
	bool bRightMayMenu = false;

	/**
	 * ---- A FINGER, WHICH HAS ONLY ONE BUTTON ----
	 *
	 * This window's whole interaction model is two buttons: left does the
	 * default thing, right lists everything. A phone has neither, and the
	 * substitution every game of this shape makes is the right one because
	 * everybody already knows it: a TAP is the left button and a LONG PRESS is
	 * the right one.
	 *
	 * Held rather than worked out, because the difference between a tap, a
	 * hold and a drag is not a fact about one frame: it is how long the finger
	 * stayed and how far it went, and both have to be remembered from the
	 * moment it landed.
	 */
	double TouchDownAt = -1.0;
	FVector2D TouchDownWhere = FVector2D::ZeroVector;
	bool bTouchHeldFired = false;

	/** Seconds a finger must rest before it counts as asking for the menu. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "0.15", ClampMax = "2"))
	float LongPress = 0.42f;

	/**
	 * How far a finger may travel and still be a tap, in viewport pixels.
	 *
	 * Much larger than the mouse's six. A fingertip is a centimetre across and
	 * nobody's hand is steady on glass: six pixels would turn half the taps in
	 * the world into drags, and a drag does nothing but turn the camera.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval", meta = (ClampMin = "2", ClampMax = "120"))
	float TouchSlop = 26.f;

private:
	/** The corners still to turn, nearest first. Empty for a plain walk. */
	TArray<FIntPoint> Route;

	/**
	 * Where the route was FOR, and how many times it has been re-thought.
	 *
	 * A route is planned over what the window can see, and what it can see is
	 * a few dozen tiles of nodes round the citizen. Fifty tiles out it is
	 * planning through ground it knows nothing about, so it walks into things.
	 * The answer is not a better search -- it is to look again on arriving
	 * somewhere new, which is what a person does. The count stops that turning
	 * into a citizen shuffling against a wall for ever.
	 */
	FIntPoint RouteGoal = FIntPoint::ZeroValue;

public:
	/**
	 * WHERE THE CITIZEN IS TRYING TO GET TO, for the maps to draw.
	 *
	 * A click on a map fifty tiles wide sends somebody walking for a minute
	 * with nothing on screen to say where they asked to go: "otherwise you're
	 * walking blind it feels like". The route already knows; it simply had no
	 * way of being asked.
	 *
	 * Zero means no journey is under way. The world's own origin is a corner
	 * of the sea and nobody walks there, so it is safe as a nothing.
	 */
	FIntPoint GetRouteGoal() const { return Route.Num() > 0 ? RouteGoal : FIntPoint::ZeroValue; }

private:
	int32 Rethinks = 0;

	/**
	 * Tiles a walk has been stopped by, learned by being stopped.
	 *
	 * Kept for the session, not for ever: the world changes, a wall can be
	 * dismantled, and a citizen who remembers a door as shut for all time is
	 * worse off than one who tries it again tomorrow.
	 */
	/**
	 * TILES THE WORLD HAS REFUSED, AND WHEN.
	 *
	 * It was a bare set and never forgot anything, which is right for a wall
	 * and badly wrong for everything else that can stop a walk. A wolf
	 * standing in a gateway for one interval, another citizen crossing a
	 * bridge, a stall that is packed away an hour later -- every one of those
	 * was written down as permanently shut. An hour's walking laid a wall of
	 * phantom obstacles around the citizen and the router eventually decided
	 * there was no way out of anywhere, which from the chair looks exactly
	 * like a citizen standing still doing nothing at all. It cost most of a
	 * ninety-minute day.
	 *
	 * So each one now carries the tick it was learned on and is forgotten
	 * after `ForgetAfter`. Real walls are re-learned the moment they are
	 * walked into again, which costs one refused step; everything transient
	 * simply expires.
	 */
	TMap<FIntPoint, int64> Learned;

	/** Intervals before a refused tile is given the benefit of the doubt. */
	int32 ForgetAfter = 90;

	/** Guards the one retry a failed search is allowed. */
	bool bSecondThoughts = false;

	/** Intervals the citizen has been bound for a walk and not moved. */
	int32 StillFor = 0;

	FIntPoint Bound = FIntPoint::ZeroValue;
	bool bBound = false;

	/**
	 * §7dn/§7dq: the last thing a threshold said, so it is said once on
	 * arrival and again only if it changes -- which is the case worth
	 * hearing: a torch burning out in front of the Smother's mouth is the
	 * item doing what it is for, and the citizen should be told the door
	 * has just shut.
	 */
	FString LastThresholdSaid;
	int32 Legs = 0;
	FIntPoint LastSeenAt = FIntPoint::ZeroValue;

	/** The interval the current run was filed on. */
	int64 FiledAt = -1;

	/**
	 * `lastInput` as it stood when the current run was filed -- the ONLY signal
	 * a refused deed gives.
	 *
	 * The world does not answer a deed it declines: it says nothing at all and
	 * the citizen goes on standing there. The one trace is that `lastInput` --
	 * the last interval the world ACCEPTED something from this citizen -- never
	 * moves. Accepted, it advances; refused, it stays. Measured both ways before
	 * it was trusted.
	 */
	int64 FiledInput = -1;

	/**
	 * How many intervals to let the world answer in before calling it a refusal.
	 * Deeds measured at two to three intervals from filed to applied; five leaves
	 * room for a slow block without leaving a citizen watching a dead window.
	 */
	static constexpr int64 AnswerPatience = 5;

	/** So `enter` is a knock at a door, not a battering ram. */
	int64 LastEnterTick = -1;
};
