// IntervalTypes.h -- the only shapes this project is allowed to know.
//
// Note what is NOT here: no entity kinds, no item list, no tool list, no
// terrain enum. Everything the world contains arrives as a string the
// bridge was told, and is stored as a string. A renderer may switch on
// those strings to choose a mesh; it may never decide what one MEANS.
//
// The day somebody adds `enum class EIntervalTerrain` to this file is the
// day check-window-unreal.mjs starts failing, and it will be right.

#pragma once

#include "CoreMinimal.h"
#include "IntervalTypes.generated.h"

/**
 * §9f: A THING THE WORLD SAYS TO EVERYBODY AT ONCE.
 *
 * Not speech. `announce()` has seventy-four call sites and none of them has a
 * speaker: a dragon risen, the last lamprey dead, a stall fallen in the grass,
 * every first and every mastery, and the deep tide turning -- which since the
 * tide was cut to one window is the entire point of that feature.
 *
 * THE BROWSER WINDOWS READ THIS OFF THE WORLD AND THIS ONE CANNOT. They are
 * handed the whole state and take `state.announce` from it; this window is
 * given a curated frame, and nothing in that frame carried the list. So the
 * deluxe client was the only window in which the tide did nothing visible
 * whatever. The bridge forwards them now, watermarked at the tick it joined so
 * that arriving does not replay an hour of old news.
 */
USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalCry
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Interval|Chat")
	FString Text;

	/** The interval it happened on, which is not always the one it arrives on. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval|Chat")
	int64 Tick = 0;
};

/**
 * SOMETHING SOMEBODY SAID.
 *
 * Chat carries more than a name and a line because this world has more than
 * names in it. A speaker has a CALLING -- a smith, a mourner, an archer --
 * which is the thing a stranger most wants to know before they answer; and
 * they are STANDING SOMEWHERE, on an island where "meet me by the crooked
 * oak" is an ordinary sentence and a line with no place attached is half a
 * message. Both are derived by the bridge from the world's own functions, so
 * the calling here is the calling on the nameplate and the place here is the
 * place on everybody else's screen.
 *
 * And there are TWO CHANNELS, which is the world's arrangement and not this
 * window's: `near` reaches the people the world already says you are standing
 * with, `far` reaches the island. They are different things to say, so they
 * are told apart on sight rather than run together into one log.
 */

USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalSaid
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Interval|Chat")
	FString SpeakerId;

	UPROPERTY(BlueprintReadOnly, Category = "Interval|Chat")
	FString Name;

	UPROPERTY(BlueprintReadOnly, Category = "Interval|Chat")
	FString Text;

	/** What they swore to. Empty for a citizen who has sworn to nothing yet. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval|Chat")
	FString Calling;

	/** Where they were standing, in the generator's own naming. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval|Chat")
	FString Place;

	/** `near` or `far`, verbatim. This window does not decide which is which. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval|Chat")
	FString Scope;

	UPROPERTY(BlueprintReadOnly, Category = "Interval|Chat")
	int32 Standing = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Interval|Chat")
	int32 X = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Interval|Chat")
	int32 Y = 0;
};

/** One thing standing somewhere. Position is authoritative; the rest is verbatim. */
USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalEntity
{
	GENERATED_BODY()

	/** The world's id for it. Stable across intervals; use it for actor identity. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString Id;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 X = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 Y = 0;

	/** Whatever the world called it, unexamined. Empty when it did not say. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString Kind;

	/** Every other field, flattened to strings. Nested objects arrive as raw JSON. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	TMap<FString, FString> Fields;
};

/** What sort of thing is being pointed at. */
UENUM(BlueprintType)
enum class EIntervalTargetKind : uint8
{
	Ground   UMETA(DisplayName = "Ground"),
	Node     UMETA(DisplayName = "Node"),
	Mob      UMETA(DisplayName = "Mob"),
	Citizen  UMETA(DisplayName = "Citizen"),
	/**
	 * A THING IN THE PACK, which is pointed at the same way as a thing in the
	 * world and had no way of being. The pack's slots took a left click and
	 * did their default deed; a right click did nothing at all, so `eat` and
	 * `drop` -- and for anything already wielded, `unwield` -- were reachable
	 * only if they happened to be first in the list. It is the same fault the
	 * world had before the menu existed, in the other half of the screen.
	 *
	 * Such a target carries the SLOT in X, because that is what the world's
	 * verbs name, and the item's own word in Name.
	 */
	Pack     UMETA(DisplayName = "Pack"),
	/**
	 * A THING LYING ON THE GROUND.
	 *
	 * The world drops things constantly -- what a citizen puts down, what
	 * spills when somebody dies, what bursts out of a dropped consignment,
	 * what a beast leaves behind -- and the window drew them and offered
	 * nothing. `drop` was reachable from the first day and `pickup` never
	 * was, so a thing put down was a thing gone: an iron dagger was dropped
	 * by accident twenty gold after it was bought, and there was no gesture
	 * in the window that could get it back.
	 *
	 * `Id` is the world's `groundId`, which is what the deed names.
	 */
	Drop     UMETA(DisplayName = "Drop"),
	/**
	 * §6g: A THING IN THE VAULT AT THE COUNTER THE CITIZEN IS STANDING AT.
	 *
	 * `withdraw` names an ITEM and a COUNT, and the world finds the counter --
	 * so like `buy` and `smith` it could never be a row on a node, and unlike
	 * them there was nowhere to show what the vault even held. Three verbs
	 * (`deposit`, `deposit_all`, `withdraw`) were wired in this hand from the
	 * first sweep and not one of them had a gesture that could reach it: a
	 * citizen could put nothing away and take nothing out, ever.
	 *
	 * `Name` is the item's word and `X` is how many are in the vault, which is
	 * what a menu row needs to offer "withdraw all" without asking again.
	 */
	Vault    UMETA(DisplayName = "Vault"),
};

/**
 * ONE THING A PLAYER CAN POINT AT.
 *
 * Everything in this world stands on a tile, so a pick is not a ray against
 * geometry -- it is "what does the frame say is on this square". That is also
 * the honest answer when a tree's canopy overhangs the tile next to it: the
 * world thinks in tiles and so should the cursor.
 */
USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalTarget
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	EIntervalTargetKind Kind = EIntervalTargetKind::Ground;

	/** The world's id for it. Empty for bare ground. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString Id;

	/** The world's word for what it is -- `tree`, `wolf`, `keeper`. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString Type;

	/** Its finer word where the world gave one -- `oak-tree`, `keeper.miller`. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString Sub;

	/** What to call it on screen. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString Name;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 X = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 Y = 0;

	/**
	 * WHAT MAY ACTUALLY BE DONE TO THIS, right now, by this citizen.
	 *
	 * Only filled for a citizen, and only by the bridge, which has the whole
	 * state and can answer questions this window cannot: whether you are both
	 * in the Wilds, whether they are already a friend, whether there is an
	 * apprenticeship between you at all. Empty for everything else, which is
	 * why the other branches of `OptionsFor` do not consult it.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	TArray<FString> May;
};

/** One line on the right-click menu. */
/** The goods one kind of stall keeps, and their prices. */
USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalStock
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	TMap<FString, int32> Price;
};

USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalOption
{
	GENERATED_BODY()

	/** The world's own verb, sent unexamined. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString Verb;

	/** What the line reads, e.g. "gather  oak-tree". */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString Label;

	/** True for the one a left click performs. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	bool bDefault = false;

	/**
	 * The thing the verb is about, when the verb is about a thing rather than
	 * a place. `buy` names an ITEM and the world finds the counter; so does
	 * `smith`, which names a recipe. Empty for every verb that names only
	 * what it is pointed at.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString Argument;

	/**
	 * Whether choosing this line opens ANOTHER page rather than filing a deed.
	 *
	 * Most second pages are the last word: a stall's goods, an anvil's
	 * recipes, the makes a log has in it. An offer of trade is not -- it needs
	 * WHAT you are giving and then WHAT you want for it, which is two
	 * questions, and asking both at once would mean a page with a line for
	 * every item crossed with every price.
	 *
	 * So a page may say that its own lines lead further. The menu carries the
	 * answer so far in `Argument` and asks again with it, which is how a third
	 * page knows what the second one was told.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	bool bMore = false;
};

/**
 * THE VERBS ONE KIND OF NODE AFFORDS.
 *
 * A struct rather than a bare TArray because Unreal's reflection will not hold
 * a TMap of arrays, and this has to be a UPROPERTY so the panel and the hand
 * can both read it.
 */
USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalAffords
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	TArray<FString> Verbs;
};

/**
 * ONE SETTLEMENT, AS THE FOUNDER SEATED IT.
 *
 * The bridge already carries this in `hello` and the window has been keeping
 * it as raw JSON and never reading it. It is the only thing the world says
 * about a town as a WHOLE rather than tile by tile: where it sits, how far it
 * reaches, and what KIND it is -- a capital, a garrison, a market, a village.
 *
 * `Kind` is the world's own word and nothing in C++ knows what any of them
 * mean. A level says how each is drawn, exactly as it says how a ground or a
 * verb is drawn, and a founding that invents a new kind of town costs a row
 * and no build.
 */
USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalSettlement
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Interval") FString Tag;
	UPROPERTY(BlueprintReadOnly, Category = "Interval") FString Name;

	/** The world's own word: capital, garrison, market, port, village... */
	UPROPERTY(BlueprintReadOnly, Category = "Interval") FName Kind;
	UPROPERTY(BlueprintReadOnly, Category = "Interval") FName Ring;

	/** The seat, in tiles, and how far the town reaches from it. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval") int32 X = 0;
	UPROPERTY(BlueprintReadOnly, Category = "Interval") int32 Y = 0;
	UPROPERTY(BlueprintReadOnly, Category = "Interval") int32 W = 0;
	UPROPERTY(BlueprintReadOnly, Category = "Interval") int32 H = 0;

	/** The bounds as tiles, half-open: [MinX, MaxX] inclusive. */
	int32 MinX() const { return X - (W / 2); }
	int32 MaxX() const { return X + (W / 2); }
	int32 MinY() const { return Y - (H / 2); }
	int32 MaxY() const { return Y + (H / 2); }
};

/**
 * What the light is doing.
 *
 * ARITHMETIC ON THE INTERVAL COUNT, computed by the bridge from the shared
 * ladder every window uses, so it is the same sky for everybody and readable
 * forwards and backwards forever. This window points a sun at these numbers
 * and holds no opinion about how they were arrived at -- it does not know what
 * a season is, or that a day is 2400 intervals, or that the weather is hashed
 * off the day. It knows the sun is 12 degrees up and bearing 84, and that is
 * a thing you can draw.
 */
USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalSky
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Interval") bool bValid = false;

	/** Degrees above the horizon, negative at night. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval") float ElevationDeg = 45.f;

	/** Degrees clockwise from north. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval") float Bearing = 180.f;

	/** 0 at night, 1 in full day. Not the same as elevation: it saturates. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval") float DayAmount = 1.f;

	/** How near the horizon the sun is, which is what makes light warm. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval") float Warm = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "Interval") float Overcast = 0.f;
	UPROPERTY(BlueprintReadOnly, Category = "Interval") float Rain = 0.f;
	UPROPERTY(BlueprintReadOnly, Category = "Interval") float Aurora = 0.f;
	UPROPERTY(BlueprintReadOnly, Category = "Interval") float Rainbow = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "Interval") float Spring = 0.f;
	UPROPERTY(BlueprintReadOnly, Category = "Interval") float Autumn = 0.f;
	UPROPERTY(BlueprintReadOnly, Category = "Interval") float Winter = 0.f;

	/** Where in the day we are, 0 at sunrise. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval") float DayFraction = 0.f;
};

USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalCraft
{
	GENERATED_BODY()

	/** What the craft is at, by the engine's own ladder. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 Level = 1;

	/** The experience in it, which is what the world actually stores. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 Xp = 0;

	/**
	 * The rungs either side: where this level began and where the next one
	 * starts. `Next` is zero at the top of the ladder, where there is no next.
	 *
	 * Both are walked by the bridge out of `levelForXp`, because inverting a
	 * formula by hand is how two copies of a rule start disagreeing.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 From = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 Next = 0;
};

/** One interval, as the bridge last heard it. */
USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalFrame
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int64 Tick = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	bool bHasMe = false;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FIntervalEntity Me;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	TMap<FString, FIntervalEntity> Players;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	TMap<FString, FIntervalEntity> Mobs;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	TMap<FString, FIntervalEntity> Nodes;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	TMap<FString, FIntervalEntity> Ground;

	/**
	 * Whether this citizen is in the world yet, and how far through the wait
	 * they are. Birth is two-phase and the second half is refused inside the
	 * state machine, where no refusal comes back down the socket -- so without
	 * this a window can only show silence. One of: in, waiting, ripe, lapsed,
	 * unknown. What those mean is the bridge's business; showing them is ours.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FIntervalSky Sky;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString BirthState;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 BirthWaited = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 BirthRipeAt = 0;

	/**
	 * WHETHER THIS FRAME IS OF THE WORLD OR OF A PRACTICE OF IT.
	 *
	 * §0: a key the world has never heard of is in Nought -- the same island,
	 * the same seed, the same towns and beasts, computed by the same functions
	 * and run by the resident's own machine. Nothing done there is recorded and
	 * nothing crosses over. The bridge runs it and pushes it down this socket
	 * in the ordinary shape, deliberately, so that every panel, menu and deed
	 * in this window works on the practice island without knowing it exists.
	 *
	 * Which is exactly why this is here. Being unable to tell the practice
	 * from the country is the one failure Nought must not have, so the window
	 * says so somewhere that never scrolls away for as long as it is true.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	bool bNought = false;

	/**
	 * §6g: THE BANK COUNTER WITHIN REACH, AND WHAT IS IN IT.
	 *
	 * A vault is local: what a citizen put away at Anchor is at Anchor, and
	 * standing at Thornbury's counter shows Thornbury's. Which counter that is
	 * gets decided by the bridge, because it is the world's rule; this is only
	 * what came back.
	 *
	 * `bAtVault` false means there is no counter in reach and there is no bank
	 * screen to open. `bAtVault` true with an empty `Vault` means a counter
	 * with nothing in it, which is a different sentence and has to read
	 * differently -- otherwise a citizen at their own empty vault is told
	 * there is no bank here.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	bool bAtVault = false;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	TMap<FString, int32> Vault;

	/**
	 * §5c: THE TRADE STANDING BETWEEN TWO PEOPLE.
	 *
	 * `OfferFrom` is somebody else's offer to this citizen -- their key, so
	 * `accept_trade` can name it -- and it is only ever filled for somebody
	 * standing beside them, because that is the world's own condition for
	 * taking one. An offer nobody can accept is a button that cannot work.
	 *
	 * `MineTo` is the offer this citizen has out, which is what makes
	 * `cancel_trade` mean anything: without it the window could not tell an
	 * offer that was never made from one nobody has answered.
	 *
	 * Both are worked out by the bridge, because an offer lives on the
	 * OTHER citizen's record and no amount of looking at the one being drawn
	 * would find it.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString OfferFrom;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString OfferName;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString OfferGives;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString OfferWants;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString MineTo;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString MineGives;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString MineWants;

	/**
	 * WHAT THE GROUND THIS CITIZEN IS STANDING ON CAN BE USED FOR.
	 *
	 * A family of this world's verbs is "do this thing out of your pack, AT
	 * that place" -- cook at a hearth, grind at a mill, brew at a smokerack,
	 * bury at an ossuary, stoke a furnace, deposit at a vault. All of them are
	 * afforded by the NODE and all of them take a `slot`, which is a thing
	 * only the pack knows, so drawn on the node they are rows with a hole in
	 * them that the world refuses. Cooking was offered on every hearth on the
	 * island and had never once worked.
	 *
	 * They belong on the pack's rows and appear there exactly while the place
	 * that allows them is in reach. The bridge decides what is in reach,
	 * because orthogonal adjacency is the world's rule and not this window's.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	TArray<FString> AtHand;

	/**
	 * WHAT CANNOT BE DONE AT ALL FROM HERE, whatever it is pointed at.
	 *
	 * The affordance tables answer what the ground allows and what a thing
	 * allows; neither is the right shape for a verb whose conditions are about
	 * the CITIZEN -- where they stand and what is in their hand. Transmuting
	 * is one: it is an affordance of every priced item, a hundred and five of
	 * them, so a newcomer in Anchor with a hatchet had it under every single
	 * thing in their pack and the world declined all of it silently.
	 *
	 * Worked out in the bridge, where the whole state is. See verbsBarred.
	 */
	UPROPERTY()
	TArray<FString> Barred;

	/**
	 * AND WHAT MAY BE DONE ON THE TILE ITSELF.
	 *
	 * A few deeds name nothing at all: a watchfire is kindled where you stand,
	 * a stall is raised where you stand, a marker is surveyed by standing on
	 * it. There is nothing to point at, so there was no gesture and all three
	 * were unreachable. Their conditions are the world's and the bridge reads
	 * them; this is the answer.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	TArray<FString> Underfoot;

	/**
	 * WHAT EACH CRAFT IS AT, AS A LEVEL rather than as raw experience.
	 *
	 * The window printed the experience, so forty felled trees read as
	 * "woodcraft 720" -- a number about bookkeeping, not about the citizen.
	 * The ladder is the engine's and the bridge walks it, which is also what
	 * lets the window notice a CROSSING: a level-up is only an event if
	 * somebody says where the rungs are.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	TMap<FString, FIntervalCraft> Levels;

	/**
	 * CLOSING TIME: how many intervals of presence this citizen has left.
	 *
	 * The world allows 5400 -- ninety minutes -- in any rolling 86400-interval
	 * window, and spending them does not log a citizen out or take anything.
	 * They are STOOD DOWN: present and not acting, standing where they stood,
	 * until the window rolls far enough to let them act again.
	 *
	 * The window MUST show this. A stood-down citizen and a broken bridge look
	 * exactly alike from here -- deeds stop landing and nothing says why -- and
	 * that silence is the one failure this whole seam exists to prevent. It
	 * counts PRESENCE, not deeds, so it runs down while standing still and a
	 * citizen who is only watching still needs the warning.
	 *
	 * CeilingLeft <= CeilingWarn is the world's own "nearly out" band, not one
	 * chosen here. The arithmetic is the bridge's; ours is to draw it.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 CeilingLeft = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 CeilingAllow = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 CeilingWarn = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	bool bStoodDown = false;

	/**
	 * What the world calls the ground the citizen is standing on.
	 *
	 * The generator names every region and every settlement, and the bridge
	 * derives it with the generator's own `regionNameAt` -- so this is the
	 * same name the chat line puts after a speaker and the same name on
	 * everybody else's screen. Empty for open country the world has not
	 * named, which is honest and not a gap.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString Place;

	/**
	 * THE SURFACE UNDERFOOT, BY NAME, and the one thing the window needs it for
	 * is knowing when it is underground.
	 *
	 * §7dq puts eight quenchers in a cave in the Cragscar: steel passes through
	 * them, only fire tells, and the mouth refuses anybody not carrying a
	 * light. The place is written around the dark -- its own note says the mouth
	 * needs no marker "because the dark either side of it is the marker" -- and
	 * until the generator could say `cave` every tile in it answered `crags`,
	 * exactly like the fellside outside, so this window drew a cave as a patch
	 * of hillside in daylight.
	 *
	 * It is the ground's NAME and not a flag, because the window already draws
	 * twenty-six surfaces by name and a boolean called `bUnderground` would be
	 * the twenty-seventh thing to keep in step.
	 *
	 * CALLED `Surface` BECAUSE `Underfoot` IS TAKEN, by the list of verbs that
	 * may be done on this tile. The bridge nearly shipped a second `underfoot`
	 * key in the frame literal, which would have silently replaced that list
	 * and broken kindling, raising a stall and surveying -- and the only thing
	 * that caught it was this header already having a field of that name.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString Surface;

	/**
	 * Whether the citizen is carrying something burning.
	 *
	 * §7dq-iii: ASKED OF THE ENGINE, NEVER WORKED OUT HERE. The rule has four
	 * parts -- the weapon table's `burns`, the fire-siphon's fuel, a quiver of
	 * fire arrows, and a torch's clock -- and it decides both whether a citizen
	 * may enter the Smother and whether anything they do inside it has any
	 * effect. A torch BURNS DOWN, so this is a per-interval answer and not a
	 * state: it goes false under a citizen standing in the dark.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	bool bLit = false;

	/**
	 * §7dn/§7dq: WHAT THE GROUND AHEAD WILL ASK, within two tiles of the only
	 * two thresholds on the island: the squeeze into the Whitechalk barrow,
	 * which takes nobody carrying more than three slots, and the Smother's
	 * mouth, which takes nobody without a light.
	 *
	 * The ground does the refusing, so the engine simply does not move the
	 * citizen -- which in a window reads as an invisible wall. You walk at it,
	 * nothing happens, and there is no error because nothing went wrong.
	 *
	 * SAID ON APPROACH, NOT AFTER THE FACT. A refusal that arrives once the
	 * step has failed explains something that already looks broken. Empty
	 * where there is no threshold in reach, which is almost everywhere.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString ThresholdSays;

	/** Whether the citizen may pass it as they stand. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	bool bThresholdOpen = false;

	/**
	 * AND WHICH TILE IT IS, which the window needs for a different reason than
	 * the sentence does. A threshold is the one place on the island where a
	 * citizen does not simply walk from one tile to the next: they go low and
	 * push through a gap, or stoop into a hole in a hillside. Drawn as an
	 * ordinary stride it reads as walking through rock.
	 *
	 * Minus one where there is no threshold within reach, which is almost
	 * everywhere. Two tiles only, so a citizen crossing one is somebody you are
	 * standing beside.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 ThresholdX = -1;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 ThresholdY = -1;

	/**
	 * The last interval that is SETTLED, and who settled it. The tick climbs
	 * whether or not anyone agrees; this only moves when the witnesses do, and
	 * the gap between them is the difference between a world that is running
	 * and a world that is running and agreeing.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int64 FinalizedTick = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 Witnesses = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 Quorum = 0;
};

/**
 * A rectangle of ground. Three planes, one byte per tile, row-major from
 * (X0, Y0): the terrain code (index into GetTileNames; 255 means the bridge
 * is older than the world and could not name it), whether the tile carries a
 * made way, and the scatter seed.
 *
 * The scatter seed is not decoration's private business. Two citizens who
 * arrange to meet at a landmark that only the renderer knows about must find
 * the same landmark, so placement is a pure function of this byte and never
 * of a local random stream.
 */
// NOT FIntervalChunk: UHT refuses a struct and an actor that reduce to the
// same engine name, and AIntervalChunk is the thing that draws one of these.
USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalTerrainChunk
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 X0 = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 Y0 = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 W = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 H = 0;

	/**
	 * Tiles of border the planes carry on every side, beyond the interior
	 * rectangle above. A chunk that can only see its own tiles cannot agree
	 * with its neighbour about anything computed from a neighbourhood -- a
	 * vertex's relief, a building's eaves -- so it is given a little of the
	 * ground next door to read and never to draw.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int32 Skirt = 0;

	/** (W + 2*Skirt) x (H + 2*Skirt), row-major from (X0 - Skirt, Y0 - Skirt). */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	TArray<uint8> Tiles;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	TArray<uint8> Ways;

	/**
	 * The island's spine, one byte a tile.
	 *
	 * NOT A GROUND. The ridge is a predicate in the generator and the tiles
	 * along it come back as ordinary `crags`, the same as the whole eastern
	 * third of the world -- so the most important piece of geography there is,
	 * the wall that two named passes cross and that the generator shuts one of,
	 * was indistinguishable from open country and drawn as rough ground.
	 *
	 * Told, not derived, for the same reason the roads are: a window that
	 * worked out its own ridge would disagree with the one beside it. This says
	 * WHERE the ridge is and never what a ridge means.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	TArray<uint8> Spine;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	TArray<uint8> Seeds;

	/**
	 * Whether there is WATER under each tile, one byte apiece.
	 *
	 * NOT DERIVABLE FROM `Tiles`. A road laid over a river comes back as the
	 * ground kind `bridge`, and that word says what the surface is and nothing
	 * about what it spans -- on this island a hundred and thirty-five of the
	 * two hundred and thirty-four bridge tiles are dry, because a crossing's
	 * paved approach carries the same word as its middle. The window needs the
	 * difference to know where to dig a channel under a deck and where the
	 * bank is, and got it wrong in exactly that way the first time: a
	 * three-metre trench gouged along the road for sixty tiles.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	TArray<uint8> Wet;
};

/** A refusal. Out of band, non-consensus: your own error, shown to you. */
USTRUCT(BlueprintType)
struct INTERVALBRIDGE_API FIntervalRefusal
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString Of;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	int64 Tick = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	FString Why;

	/**
	 * Whether this is actually an ANSWER rather than a refusal.
	 *
	 * Some of what the world says back arrives on this channel without being
	 * a no -- a knock that started the wait, a crossing that worked. Printing
	 * those with "refused" in front of them tells a citizen the opposite of
	 * what happened, and the word at the front is the one they believe.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	bool bOk = false;
};

/**
 * WHAT A WORD LOOKS LIKE WHEN A PERSON READS IT.
 *
 * The world names things with hyphenated keys -- `old-chain`, `iron-hatchet`,
 * `cinder-crown` -- and those keys are the world's, not the window's: they
 * travel in every frame and every deed, and the engine, the node and every
 * other window agree on them. They must never change.
 *
 * But a hyphen is a fact about an IDENTIFIER and the interface has no business
 * leaking it. Asked for plainly: "items should not have the hyphen in the
 * name. For example old-chain should just be old chain instead, it looks a lot
 * better without."
 *
 * So this is the one place a key becomes a label, and everywhere a name
 * reaches an eye calls it: the pack, the menus, the examine line, the feed,
 * the stalls, the bank. Nothing sent back to the world passes through here,
 * and nothing looked up in a table does either -- only the drawing.
 *
 * AND THE MINTED NAMES ARE HANDLED HERE TOO, because they are the one kind of
 * key that is not a word at all. A wayfarer's hood is `hood:<64 hex>:<tick>`
 * and a fall stone is `fallstone:<64 hex>:<tick>`: unique objects, minted for
 * one citizen, and the last thing anybody wants to read is the hex.
 */
namespace IntervalName
{
	inline FString Spoken(const FString& Key)
	{
		if (Key.StartsWith(TEXT("hood:")))
		{
			return TEXT("wayfarer's hood");
		}
		if (Key.StartsWith(TEXT("fallstone:")))
		{
			return TEXT("fall stone");
		}
		// AND AN ATTUNED CHART, which is the third minted family and the one
		// that was missed. `chart:<place>` is an ordinary chart that has been
		// bound to a waystone, and the place is the whole of what it is for,
		// so unlike the other two the suffix is worth SAYING rather than
		// hiding. Without this it read as "chart:millbrook" in the pack.
		if (Key.StartsWith(TEXT("chart:")))
		{
			const FString Place = Key.RightChop(6).Replace(TEXT("-"), TEXT(" "));
			return Place.IsEmpty() ? TEXT("chart") : TEXT("chart to ") + Place;
		}
		return Key.Replace(TEXT("-"), TEXT(" "));
	}

	inline FString Spoken(const FName& Key)
	{
		return Spoken(Key.ToString());
	}

	/**
	 * THE WORD A TABLE IS KEYED ON, for a key that may have been minted.
	 *
	 * `Spoken` is for a person to read; this is for the window to look things
	 * up with. Three families in this world are not words at all -- a hood, a
	 * fall stone and an attuned chart all carry a hash or a place after a
	 * colon -- and every table the window owns is keyed on the plain word.
	 *
	 * IT IS ONE FUNCTION BECAUSE IT WAS THREE. The wardrobe folded `hood:` and
	 * `fallstone:` to their rows and drew them correctly, and the pack's
	 * `IconFor` did not, so the one citizen in the world who had earned a hood
	 * saw it on their head and an empty square in their pack. A key like this
	 * turns into the asset name `hood:aaaa..._1200`, which is not a legal
	 * asset name and never matches anything, so the lookup failed silently and
	 * cached the failure.
	 */
	inline FString Row(const FString& Key)
	{
		if (Key.StartsWith(TEXT("hood:"))) { return TEXT("wayfarer-hood"); }
		if (Key.StartsWith(TEXT("fallstone:"))) { return TEXT("fall-stone"); }
		if (Key.StartsWith(TEXT("chart:"))) { return TEXT("chart"); }
		return Key;
	}

	inline FName Row(const FName& Key)
	{
		const FString Folded = Row(Key.ToString());
		return Folded == Key.ToString() ? Key : FName(*Folded);
	}
}
