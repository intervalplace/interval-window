// IntervalBridgeSubsystem.h -- the whole of this project's C++.
//
// It connects to unreal-bridge.mjs on localhost, parses what arrives, and
// broadcasts it. It does not model, predict, correct, reconcile or decide
// anything. Three rules, and they are the reason the rest of the window is
// allowed to be as large and as pretty as it likes:
//
//   1. IT HOLDS NO KEY. Signing happens in the bridge process. A compromised
//      .uproject cannot act as the citizen.
//   2. IT STAMPS NO TICK. An intent leaves here as a verb and some integers;
//      the bridge stamps the interval. A renderer running at 120 fps can
//      therefore never act on an interval that has already passed, which is
//      the failure mode that makes a smooth client walk one step and stop.
//   3. IT NAMES NOTHING. Terrain codes, entity kinds and table values are
//      whatever the bridge said they were, this session.

#pragma once

#include "CoreMinimal.h"
#include "Containers/Ticker.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "IntervalTypes.h"
#include "IntervalBridgeSubsystem.generated.h"

class IWebSocket;
class FJsonObject;

// ---- THE FRAME IS NOT PASSED. IT IS FETCHED. ----
//
// This carried `const FIntervalFrame&` and it cost more than everything it
// was told. A DYNAMIC delegate marshals its arguments through `ProcessEvent`,
// and marshalling a struct means COPYING it -- so every broadcast deep-copied
// the whole world: every player, mob, node and ground item, each with its own
// string maps inside it. Five actors listen, so that happened five times an
// interval, and again for every terrain chunk raised, which is where a sample
// of the stalled window caught it:
//
//   AIntervalGround::BuildQueued -> RaiseChunk -> ProcessEvent
//     -> AIntervalStructures::Rebuild -> FIntervalFrame::FIntervalFrame(const&)
//
// The game thread sat at a hundred per cent of one core doing nothing but
// copying maps of strings, which is the whole of why the window took minutes
// to open and then read frames slower than they arrived.
//
// Passing nothing costs nothing. Every handler already has the subsystem and
// `GetFrame()` returns the very member this used to broadcast, so they read it
// directly -- which is what `HandleGroundChanged` had been doing all along.
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FIntervalFrameEvent);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FIntervalTerrainChunkEvent, const FIntervalTerrainChunk&, Chunk);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FIntervalRefusedEvent, const FIntervalRefusal&, Refusal);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FIntervalChatEvent, const FIntervalSaid&, Said);
/** §9f: and the ones with no speaker, which the world says to everybody. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FIntervalCryEvent, const FIntervalCry&, Cry);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FIntervalConnectionEvent, bool, bConnected);
/** The bridge has said who we are and what this world is. Safe to build from here. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FIntervalReadyEvent);

UCLASS()
class INTERVALBRIDGE_API UIntervalBridgeSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	// ---- events ----

	UPROPERTY(BlueprintAssignable, Category = "Interval")
	FIntervalReadyEvent OnReady;

	UPROPERTY(BlueprintAssignable, Category = "Interval")
	FIntervalFrameEvent OnFrame;

	UPROPERTY(BlueprintAssignable, Category = "Interval")
	FIntervalTerrainChunkEvent OnTerrainChunk;

	UPROPERTY(BlueprintAssignable, Category = "Interval")
	FIntervalRefusedEvent OnRefused;

	UPROPERTY(BlueprintAssignable, Category = "Interval")
	FIntervalChatEvent OnChat;

	/** Fired for each thing the world cries out, once, in the order it
	 *  happened. Already watermarked by the bridge: joining a world does
	 *  not replay the hour of news that happened before you arrived. */
	UPROPERTY(BlueprintAssignable, Category = "Interval")
	FIntervalCryEvent OnCry;

	UPROPERTY(BlueprintAssignable, Category = "Interval")
	FIntervalConnectionEvent OnConnectionChanged;

	/** The terrain list grew: a world exists with ground this build has never drawn. */
	UPROPERTY(BlueprintAssignable, Category = "Interval")
	FIntervalConnectionEvent OnTileNamesChanged;

	// ---- talking ----

	/** Defaults to ws://127.0.0.1:7777, overridable with -intervalbridge=<url>. */
	UFUNCTION(BlueprintCallable, Category = "Interval")
	void Connect(const FString& Url);

	UFUNCTION(BlueprintPure, Category = "Interval")
	bool IsConnected() const;

	UFUNCTION(BlueprintCallable, Category = "Interval")
	void RequestTerrain(int32 X0, int32 Y0, int32 W, int32 H, int32 Skirt = 0);

	/**
	 * Send one intent. Type is the world's own verb; Numbers and Text are its
	 * fields. Nothing is validated here on purpose -- the engine's normalizer
	 * is the only thing entitled to an opinion, and a refusal comes back
	 * through OnRefused with the reason in it.
	 */
	UFUNCTION(BlueprintCallable, Category = "Interval")
	void SendIntent(const FString& Type, const TMap<FString, int32>& Numbers, const TMap<FString, FString>& Text);

	/**
	 * SAY SOMETHING. Chat is not a deed.
	 *
	 * It is out of band like a refusal: not in the world's input schemas, not
	 * signed, not consensus, and it advances nothing. It is relayed by the
	 * bridge in both directions and nothing in between reads it.
	 *
	 * This window could hear the island from the first day and never answer
	 * it. In a world whose whole rhythm -- a tick a second, a walk that takes
	 * minutes, a crop that takes twelve -- exists to leave people room to talk
	 * to each other, a window that cannot talk is not a window on this world.
	 */
	UFUNCTION(BlueprintCallable, Category = "Interval")
	void SendChat(const FString& Text, const FString& Scope = TEXT("near"));

	/**
	 * The same, for a deed that carries a TRUE OR FALSE.
	 *
	 * The world's normalizer types its fields, and `confirm` on a pickup must
	 * be a boolean -- not 1, not "true". Sent through the integer map it
	 * arrived as the number 1 and was refused every single time, which meant
	 * this window could not pick anything up off the ground at all: a drop
	 * fell, sat there for its hundred intervals, and expired.
	 *
	 * Kept as its own entry point rather than widening the common one, so the
	 * sixty-eight deeds that carry only scalars are not made to think about a
	 * map they never use.
	 */
	void SendIntentBool(const FString& Type, const TMap<FString, int32>& Numbers,
		const TMap<FString, FString>& Text, const TMap<FString, bool>& Flags);

	/**
	 * One deed whose field is a LIST of integers.
	 *
	 * `SendIntent` carries scalars, which covers sixty-eight of the world's
	 * sixty-nine verbs. `consign` names several of the citizen's own pack
	 * slots at once, and a list is not a scalar. Still transport: the array
	 * is written out exactly as handed over, and nothing here knows what a
	 * slot is for.
	 */
	UFUNCTION(BlueprintCallable, Category = "Interval")
	void SendIntentList(const FString& Type, const FString& Field, const TArray<int32>& Values);

	/**
	 * `offer_trade`, which is the one deed with four fields of three shapes.
	 *
	 * A key, a list of slots, an item that MAY BE NULL, and a count of coin.
	 * `SendIntentList` carries a list and nothing beside it, and SendIntent
	 * carries scalars and no list, so this deed gets its own door -- the same
	 * reason `consign` has one.
	 *
	 * An empty `WantItem` is sent as a JSON NULL, not as an empty string and
	 * not left out: the engine is explicit that "omission is not a
	 * representation", and both demand fields travel on every offer.
	 */
	void SendOfferTrade(const FString& To, const TArray<int32>& GiveSlots,
		const FString& WantItem, int32 WantGold);

	/** Ask for a whole world again, after a stall or a long background. */
	UFUNCTION(BlueprintCallable, Category = "Interval")
	void Resync();

	/**
	 * Get this citizen into the world, whatever that currently takes.
	 *
	 * One word. The bridge knows that birth is two-phase, how long the wait
	 * is, and that a bare spawn with no wait behind it is refused forever --
	 * the same reason sdk.mjs keeps that knowledge in one place instead of in
	 * every executor. Safe to call every interval; what is happening comes
	 * back through OnRefused so a citizen is never left wondering.
	 */
	UFUNCTION(BlueprintCallable, Category = "Interval")
	void EnterWorld();

	// ---- CARRYING A CITIZEN BETWEEN WINDOWS ----
	//
	// Somebody starts in the browser because it costs nothing and downloads
	// this window later. Without these they arrive as a stranger: the bridge
	// mints a fresh key on first run and their browser citizen stays behind.
	//
	// THE KEY NEVER COMES THROUGH HERE. These send a verb and nothing else. The
	// bridge owns the clipboard, the file and the secret, exactly as it owns the
	// signing, and this window is told only what happened. Handing the key to
	// Unreal so it could show somebody their own key would give away the one
	// property the whole split exists for: a compromised .uproject cannot act
	// as you, because it has nothing to act with.
	void CarryCitizenOut();
	void CarryCitizenIn();

	// What the bridge said about the last carry: shown on the title card, since
	// that is where a person decides who they are.
	FString CarrySaid;
	bool bCarryWorked = false;

	// ---- what we were told ----

	UFUNCTION(BlueprintPure, Category = "Interval")
	const FIntervalFrame& GetFrame() const { return Frame; }

	/**
	 * WHAT CAN BE DONE WITH EACH KIND OF NODE, as the bridge derived it from
	 * the engine's own executor. Keyed by node TYPE.
	 *
	 * This window never decides that a well affords drinking. It is told, the
	 * same way it is told what a terrain code means, and for the same reason:
	 * a table of affordances kept here would be a hand copy, right the day it
	 * was typed and wrong the day the engine changed.
	 */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	TMap<FString, FIntervalAffords> Affords;

	/** What each ITEM affords, keyed by the world's word for it. */
	UPROPERTY(BlueprintReadOnly, Category = "Interval")
	TMap<FString, FIntervalAffords> ItemAffords;

	/**
	 * WHAT A THING IN THE PACK CAN BE MADE INTO.
	 *
	 * `fletch` is one verb for seven makes and the engine chooses by looking
	 * at the make AND the item: a log becomes a bow, a torch, a wand or a
	 * staff, and arrows come from BONES. The bridge derives it; this only
	 * holds it, the same way `StallSells` holds what a stall keeps.
	 */
	TMap<FString, FIntervalAffords> ItemMakes;

	/**
	 * Verb -> the field it names its target in, for the verbs that name one.
	 * A verb absent from this takes no target: the world finds the thing the
	 * citizen is standing beside. See the note where it is parsed.
	 */
	UPROPERTY()
	TMap<FString, FString> VerbTarget;

	/** Verb -> every field its schema names. */
	UPROPERTY()
	TMap<FString, FIntervalAffords> VerbFields;

	/**
	 * WHAT A CITIZEN MAY SWEAR THEMSELVES TO: calling -> the craft it rests
	 * on. Seventeen of them, and an oath asks for `SwearLevel` in that craft,
	 * so a window that offered all seventeen would be offering fifteen rows
	 * the world refuses. Both numbers come from the engine.
	 */
	/**
	 * §7cf: WHAT EACH BOOK HOLDS, from the engine's own table.
	 *
	 * The window kept a hand copy so it could draw the spell list, which is
	 * the drift the engine warns about where `speaks` lives: the gate is one
	 * table so six call sites cannot disagree, and a seventh copy in another
	 * language is that mistake with more steps.
	 */
	UPROPERTY()
	TMap<FString, FIntervalAffords> Books;

	/** Whether this citizen's book holds that word. */
	bool Speaks(const FString& Book, const FString& Word) const
	{
		const FIntervalAffords* Held = Books.Find(Book.IsEmpty() ? TEXT("common") : Book);
		return Held && Held->Verbs.Contains(Word);
	}

	/**
	 * Whether this citizen could say that word at all.
	 *
	 * A spell is not an ordinary verb: the world gates it on the BOOK a
	 * citizen carries -- `speaks(p, 'transmute', state)` -- and a newcomer
	 * with the common book was offered it on every item in their pack, which
	 * the world declines before it becomes an event. `Speaks` has been here
	 * since the spell list was drawn; nothing had ever asked it about a menu
	 * line.
	 *
	 * A word no book holds is an ordinary verb and passes untouched, which is
	 * the safe way round: a line the world refuses is a nuisance, a line that
	 * never appears is a verb nobody can reach.
	 */
	bool MaySpeak(const FString& Verb) const
	{
		bool bIsAWord = false;
		for (const TPair<FString, FIntervalAffords>& Book : Books)
		{
			if (Book.Value.Verbs.Contains(Verb)) { bIsAWord = true; break; }
		}
		if (!bIsAWord) { return true; }
		const FString* Mine = Frame.Me.Fields.Find(TEXT("book"));
		return Speaks(Mine ? *Mine : FString(), Verb);
	}

	UPROPERTY()
	TMap<FString, FString> Callings;

	/**
	 * §7ds: WHAT A KEEPER'S TRADE IS CALLED, from the world's own
	 * `CALLING_NAMES`: `banker` to "the banker", `lumber` to "the axe man".
	 *
	 * A hundred and fifty-seven keepers stand on the island, each with a name
	 * the world gave it and eighty-one of them with a kind. This window knew
	 * the name and not the trade, so a street in Anchor was people called
	 * things with no way to tell which one takes a deposit.
	 *
	 * NO KEEPER CARRIES WORDS, which is the difference between this and the
	 * signposts. A sign has a `text` and reading it is reading. A keeper has a
	 * name and a trade, and both are facts the world states, so the window can
	 * say who they are without inventing a line of dialogue.
	 */
	UPROPERTY()
	TMap<FString, FString> KeeperTrades;

	/** "Delia, the banker", or just the name where the world gave no trade. */
	UFUNCTION(BlueprintCallable, Category = "Interval")
	FString WhoIs(const FString& Name, const FString& Kind) const
	{
		if (Name.IsEmpty() && Kind.IsEmpty()) { return FString(); }
		const FString* Trade = Kind.IsEmpty() ? nullptr : KeeperTrades.Find(Kind);
		if (Name.IsEmpty()) { return Trade ? *Trade : Kind; }
		if (!Trade) { return Name; }
		return FString::Printf(TEXT("%s, %s"), *Name, **Trade);
	}

	UPROPERTY()
	int32 SwearLevel = 50;

	/**
	 * WHICH VERBS WANT A CRAFT LEVEL, and how much.
	 *
	 * The bridge reads these out of the engine and sends them at boot, so the
	 * number is the world's rather than a second copy kept here. Everything
	 * else about whether a deed is possible is answered per frame by where the
	 * citizen is standing and what is in their pack; a level changes slowly
	 * enough that the window can be told the bar and check it itself.
	 *
	 * A verb with no row is offered, which is the safe way round: a line the
	 * world refuses is a nuisance, a line that never appears is a verb nobody
	 * can reach.
	 */
	struct FIntervalVerbBar { FString Craft; int32 Level = 0; };
	TMap<FString, FIntervalVerbBar> VerbNeeds;

	/** Whether this citizen is far enough along a craft for this verb. */
	bool MeetsBar(const FString& Verb) const
	{
		const FIntervalVerbBar* Bar = VerbNeeds.Find(Verb);
		if (!Bar) { return true; }
		const FIntervalCraft* Craft = Frame.Levels.Find(Bar->Craft);
		return Craft && Craft->Level >= Bar->Level;
	}

	/**
	 * WHICH ITEMS WANT A CRAFT LEVEL BEFORE THEY CAN BE TAKEN UP.
	 *
	 * The same idea as `VerbNeeds`, asked per ITEM, because that is how the
	 * world asks it: `wield` itself has no bar, and the bar lives on the thing
	 * being picked up. A citizen with prowess 1 who finds the old chain -- the
	 * rarest drop in the world, and the one item gold cannot buy -- was
	 * offered "wield old chain" and the world answered with silence.
	 *
	 * An item may want more than one craft, so this is a list per item and all
	 * of them must be met.
	 */
	TMap<FString, TArray<FIntervalVerbBar>> WieldNeeds;

	/** Whether this citizen is far enough along to take that thing up. */
	bool CanTakeUp(const FString& Item) const
	{
		const TArray<FIntervalVerbBar>* Bars = WieldNeeds.Find(Item);
		if (!Bars) { return true; }
		for (const FIntervalVerbBar& Bar : *Bars)
		{
			const FIntervalCraft* Craft = Frame.Levels.Find(Bar.Craft);
			if (!Craft || Craft->Level < Bar.Level) { return false; }
		}
		return true;
	}

	/**
	 * Whether this citizen is actually WEARING that thing.
	 *
	 * `unwield` is offered on anything equippable, which is right for the four
	 * cells above the pack and wrong for the pack itself: taking a thing off
	 * asks for a SLOT, and a chain lying in a bag is in no slot. The line
	 * appeared under every weapon, every helm and every shield a citizen was
	 * carrying rather than wearing, and did nothing at all when clicked.
	 *
	 * The world sends `equipment.<slot>` flattened a level by the frame
	 * parser, the same shape AIntervalCitizens::Wearing reads to know what to
	 * draw in a hand.
	 */
	bool IsWorn(const FString& Item) const
	{
		return !WornSlotOf(Item).IsEmpty();
	}

	/**
	 * Which slot a thing is worn in, or empty if it is not worn at all.
	 *
	 * `unwield` names a SLOT and not an item -- `{ gear: 'weapon' }` -- and
	 * every menu line knows only the item it was drawn for, so this is the
	 * step between them. Without it the pack's `unwield` line filed a deed
	 * carrying `slot`, a number, into a field the world types as a name: a
	 * line that had been in the menu since the menu existed and had never once
	 * taken a helmet off anybody.
	 */
	FString WornSlotOf(const FString& Item) const
	{
		if (Item.IsEmpty()) { return FString(); }
		static const TCHAR* Slots[] = { TEXT("weapon"), TEXT("head"),
			TEXT("body"), TEXT("legs"), TEXT("offhand") };
		for (const TCHAR* Slot : Slots)
		{
			const FString Base = FString(TEXT("equipment.")) + Slot;
			for (const FString& Key : { Base + TEXT(".item"), Base })
			{
				if (const FString* Named = Frame.Me.Fields.Find(Key))
				{
					if (*Named == Item) { return FString(Slot); }
				}
			}
		}
		return FString();
	}

	/** §5a: the standing a name costs. Names are scarce and permanent. */
	UPROPERTY()
	int32 NameStanding = 50;

	/**
	 * §5r-iv: how many of the island's countries a citizen must have stood in
	 * before they may swear to a trade. Zero means this founding asks for none.
	 */
	UPROPERTY()
	int32 SwearCountries = 0;

	/**
	 * §5k: the level every craft outside a citizen's own trade stops at, for
	 * ever. It is what swearing costs, and the swear page says it before the
	 * click rather than leaving a player to find out in a month.
	 */
	UPROPERTY()
	int32 CapOther = 70;

	/**
	 * The longest stint this founding allows, in intervals. Zero means the
	 * founding has no such oath and the window must not offer one.
	 */
	UPROPERTY()
	int32 StintCap = 0;

	/**
	 * Whether this window could actually file that verb.
	 *
	 * The menu used to offer everything the engine said a thing afforded, and
	 * some of those deeds want a word the window has no way to ask for: a
	 * `grave` wants the name to cut, a `dedicate` wants who to. Offered, they
	 * became rows that were refused the instant they were clicked -- and since
	 * a way-post affords nothing else, `grave` was its DEFAULT, so an ordinary
	 * click on the ground beside one filed a grave instead of a walk. Crossing
	 * open country turned into a stream of refusals.
	 *
	 * The window can supply the thing pointed at, a fighting style, and an
	 * item or recipe it offered by name itself. Anything else it cannot, and
	 * says so by not offering the deed -- until there is a screen that asks.
	 */
	bool CanFile(const FString& Verb, bool bHaveArgument,
		EIntervalTargetKind Kind = EIntervalTargetKind::Node) const
	{
		const FIntervalAffords* Found = VerbFields.Find(Verb);
		if (!Found)
		{
			return true;      // no schema known: let the world decide
		}
		// WHICH ROW IS ASKING, because the answer differs by row.
		//
		// A pack row knows its slot; a node does not. Once the bridge learned
		// to read the GATE as well as the executor, a vault correctly began
		// affording `deposit` and `withdraw` -- and both went straight onto
		// the vault's own right-click menu with no slot and no item in them,
		// as two rows that are refused the instant they are pressed. The
		// verbs are right, the node is right, and the ROW is the wrong place
		// to offer them from: they belong to the cells, which is where they
		// already are.
		const bool bHasSlot = Kind == EIntervalTargetKind::Pack;
		const bool bHasGround = Kind == EIntervalTargetKind::Drop;
		const bool bHasCount = Kind == EIntervalTargetKind::Vault;
		// THE THING POINTED AT, under whichever word this verb's schema spells
		// it. `still` and `mendp` say `target`, `recall` says `to`, `part`
		// says `who` -- all the same idea, and all of them a thing the player
		// has just clicked on.
		const FString* Points = VerbTarget.Find(Verb);
		for (const FString& Field : Found->Verbs)
		{
			if (Points && Field == *Points)
			{
				continue;
			}
			if (Field == TEXT("nodeId") || Field == TEXT("mobId")
				|| Field == TEXT("targetId") || Field == TEXT("style"))
			{
				continue;
			}
			// AND WHAT A MENU LINE ALWAYS KNOWS ABOUT ITSELF.
			//
			// A pack row knows which `slot` it is, a thing on the ground
			// knows its `groundId`, a worn thing knows its `gear`, and
			// `confirm` is this window's own answer to the world's guard on
			// taking what is not yours. Every one of these is already filled
			// in by the deed that files it -- see `PickUp` and `Unwield` --
			// so a verb that names one is not a verb the window cannot file.
			//
			// This mattered the moment the bridge stopped dropping the first
			// field of every schema: `wield` is `{ slot }` and nothing else,
			// so with `slot` unaccounted for, every verb the pack affords
			// would have vanished from the pack's own menu.
			if ((Field == TEXT("slot") || Field == TEXT("gear")) && bHasSlot)
			{
				continue;
			}
			if ((Field == TEXT("groundId") || Field == TEXT("confirm")) && bHasGround)
			{
				continue;
			}
			if ((Field == TEXT("item") || Field == TEXT("qty")) && bHasCount)
			{
				continue;
			}
			// THE THREE WORDS A MENU LINE CAN CARRY. `buy` says `item`,
			// `smith` says `recipe`, `fletch` says `make` -- all three name a
			// THING rather than a place, and all three are chosen by which
			// line the player picked. Leaving `make` off this list meant
			// fletching was derived by the bridge, sent to the window, listed
			// against every log in the pack, and then silently filtered out
			// one step before it could be drawn.
			if ((Field == TEXT("item") || Field == TEXT("recipe")
				|| Field == TEXT("make") || Field == TEXT("look"))
				&& bHaveArgument)
			{
				continue;
			}
			// A FIGURE THE WINDOW WILL ASK FOR. `ask`, `n` and `pay` are
			// numbers no menu can offer sensibly -- a stall's price is any
			// sum at all -- so the row opens a box instead of filing. See the
			// `Figures` table in `ActOnWith`.
			if (Field == TEXT("ask") || Field == TEXT("n") || Field == TEXT("pay"))
			{
				continue;
			}
			return false;
		}
		return true;
	}

	/** What each thing takes to make. */
	UPROPERTY()
	TMap<FString, FIntervalStock> Recipes;

	/** What one kind of stall sells, and for how much. */
	UPROPERTY()
	TMap<FString, FIntervalStock> StallSells;

	/** The goods at a stall of this kind, in the engine's own order. */
	const FIntervalStock* StockOf(const FString& Kind) const
	{
		return StallSells.Find(Kind);
	}

	/** Empty when the verb takes no target at all. */
	UFUNCTION(BlueprintCallable, Category = "Interval|Bridge")
	FString TargetFieldFor(const FString& Verb) const
	{
		const FString* Found = VerbTarget.Find(Verb);
		return Found ? *Found : FString();
	}

	/** The verbs this item affords, or an empty list. */
	UFUNCTION(BlueprintPure, Category = "Interval")
	/** What this item may be fletched into. Empty when it may not be. */
	TArray<FString> MakesFromItem(const FString& Item) const
	{
		if (const FIntervalAffords* Found = ItemMakes.Find(Item))
		{
			return Found->Verbs;
		}
		return {};
	}

	TArray<FString> AffordsForItem(const FString& Item) const
	{
		if (const FIntervalAffords* Found = ItemAffords.Find(Item))
		{
			return Found->Verbs;
		}
		return TArray<FString>();
	}

	/** The verbs this node type affords, or an empty list. */
	UFUNCTION(BlueprintPure, Category = "Interval")
	TArray<FString> AffordsFor(const FString& NodeType) const
	{
		if (const FIntervalAffords* Found = Affords.Find(NodeType))
		{
			return Found->Verbs;
		}
		return TArray<FString>();
	}

	/**
	 * What a place of this type will take, for a verb that names both a place
	 * and a slot. Empty when the world has no such rule, or when this is not
	 * one of those verbs.
	 *
	 * Keyed `verb|nodetype`, because the window only ever asks about one pair:
	 * the fire it is pointed at and the deed it is about to do there. Derived
	 * from the engine's own handlers; see `fuelsByNode` in the bridge.
	 */
	UPROPERTY()
	TMap<FString, FIntervalAffords> TakesAt;

	/**
	 * What this place takes, asked by the finer word first and the plain one
	 * after, the same way everything else in this window asks.
	 */
	UFUNCTION(BlueprintPure, Category = "Interval")
	TArray<FString> TakenAt(const FString& Verb, const FString& NodeType,
		const FString& Kind) const
	{
		if (!Kind.IsEmpty())
		{
			if (const FIntervalAffords* Fine =
				TakesAt.Find(Verb + TEXT("|") + NodeType + TEXT(".") + Kind))
			{
				return Fine->Verbs;
			}
		}
		if (const FIntervalAffords* Found = TakesAt.Find(Verb + TEXT("|") + NodeType))
		{
			return Found->Verbs;
		}
		return TArray<FString>();
	}

	/**
	 * WHERE THE DEAD COME BACK, and what that place is called.
	 *
	 * §6c returns a citizen to the founding's own spawn, whole. A death lasts
	 * five intervals and the window had nothing to say in them, because it
	 * knew somebody was dead and not where they were about to be.
	 *
	 * Announced once: the genesis fixes the spawn, so this cannot move within
	 * a world. Empty when a founding names no such place.
	 */
	UPROPERTY()
	FString ReturnPlace;
	UPROPERTY()
	int32 ReturnX = -1;
	UPROPERTY()
	int32 ReturnY = -1;

	/**
	 * Whether this verb names a place AND a thing in the pack.
	 *
	 * There are two in the world, `stoke` and `brew`, and they are the reason
	 * this question is asked rather than the names being written down. Such a
	 * verb belongs to the PLACE: you point at the fire and it asks which fuel.
	 * Offered the other way round, on the fuel's own row, a citizen standing
	 * between a furnace and a watchfire could feed the wrong one, and the only
	 * thing that says which they meant is which one they clicked.
	 */
	bool NamesPlaceAndSlot(const FString& Verb) const
	{
		const FIntervalAffords* Found = VerbFields.Find(Verb);
		return Found && Found->Verbs.Contains(TEXT("slot"))
			&& Found->Verbs.Contains(TEXT("nodeId"));
	}

	/**
	 * WHAT OUR OWN HAND JUST DID, because the world will not remember it.
	 *
	 * A citizen's `action` is the only thing the frame says about what
	 * somebody is DOING, and the world admits exactly five of them --
	 * `gather`, `attack`, `attackp`, `walk` and `raise`. Everything else a
	 * citizen can do resolves inside the interval it was asked for and leaves
	 * no trace: cooking, smithing, planting, fletching, eating, drinking,
	 * taking something off the ground. Asked what that citizen is doing on the
	 * tick they cooked a fish, the world says `null`, truthfully -- by the time
	 * the frame is written the fish is cooked.
	 *
	 * So the figure stood perfectly still through every trade it practised,
	 * and there was nothing in the frame that could have told it not to.
	 *
	 * This is the window remembering, which is squarely the window's job: the
	 * world ticks once a second and everything between two ticks is this
	 * window's to draw. The deed DID happen, on this tick, and holding the
	 * motion for a beat after it is interpolation in exactly the sense that
	 * walking between two tiles is.
	 *
	 * It is only ever OUR citizen. Somebody else cooking on the far side of
	 * the square sends us nothing, so we cannot know, and drawing a guess
	 * would be inventing world state -- which this window does not do.
	 */
	FName Doing;

	/** Seconds on the platform clock, past which `Doing` is stale. */
	double DoingUntil = 0.0;

	UFUNCTION(BlueprintPure, Category = "Interval")
	FString GetPlayerId() const { return PlayerId; }

	UFUNCTION(BlueprintPure, Category = "Interval")
	FString GetWorldId() const { return WorldId; }

	/**
	 * The path to the file that IS this citizen, as the bridge reports it.
	 * A path, never the bytes: see IntervalDoor.h.
	 */
	UFUNCTION(BlueprintPure, Category = "Interval")
	FString GetKeyFile() const { return KeyFile; }

	UFUNCTION(BlueprintPure, Category = "Interval")
	void GetWorldSize(int32& OutW, int32& OutH) const { OutW = WorldW; OutH = WorldH; }

	/** Index with a terrain code from a chunk. Out of range yields an empty string. */
	UFUNCTION(BlueprintPure, Category = "Interval")
	FString GetTileName(uint8 Code) const;

	UFUNCTION(BlueprintPure, Category = "Interval")
	const TArray<FString>& GetTileNames() const { return TileNames; }

	/**
	 * Read a value out of the tables the pillar served this session, by dotted
	 * path. This is how a widget shows a price without any build of this
	 * project ever having contained one.
	 */
	UFUNCTION(BlueprintPure, Category = "Interval")
	float GetTableNumber(const FString& Path, float Fallback = 0.f) const;

	UFUNCTION(BlueprintPure, Category = "Interval")
	FString GetTableString(const FString& Path, const FString& Fallback = TEXT("")) const;

	/** Raw, for anything the two accessors above cannot reach. */
	UFUNCTION(BlueprintPure, Category = "Interval")
	FString GetTablesJson() const { return TablesJson; }

	/** Where the founder seated the settlements, as raw JSON. Told beats derived. */
	UFUNCTION(BlueprintPure, Category = "Interval")
	FString GetSettlementsJson() const { return SettlementsJson; }

	UFUNCTION(BlueprintPure, Category = "Interval")
	FString GetWaysJson() const { return WaysJson; }

	/** The settlements, parsed. Empty until `hello` has arrived. */
	const TArray<FIntervalSettlement>& GetSettlements() const { return Settlements; }

	/**
	 * Every tile the founder actually LAID a road on.
	 *
	 * Told, not derived: the bridge fetches /api/roads precisely because a
	 * window that worked out its own roads would disagree with the one next to
	 * it. A gate belongs where a road crosses a town's edge, and this is the
	 * only honest way to know where that is.
	 */
	const TSet<FIntPoint>& GetWays() const { return Ways; }

	// ---- motion ----

	/**
	 * 0 at the interval just received, 1 at the next one due. EVERY bit of
	 * smoothness in this window is this number, and it is COSMETIC: it is
	 * never read back into an intent, never rounded into a position, never
	 * allowed to decide which tile anyone is standing on. The world advances
	 * once a second and nothing drawn here may pretend otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = "Interval")
	float GetInterpAlpha() const;

	/** How long an interval is, in seconds -- the world's own tempo. */
	UFUNCTION(BlueprintPure, Category = "Interval")
	float GetTickSeconds() const { return static_cast<float>(TickSeconds); }

	/** The interval before the current one, for interpolating from. */
	UFUNCTION(BlueprintPure, Category = "Interval")
	const FIntervalFrame& GetPreviousFrame() const { return PrevFrame; }

private:
	void HandleConnected();
	void HandleConnectionError(const FString& Error);
	void HandleClosed(int32 StatusCode, const FString& Reason, bool bWasClean);
	void HandleMessage(const FString& Message);
	void ScheduleReconnect();
	void SendRaw(const TSharedRef<FJsonObject>& Object);

	/**
	 * ONE LINE TO THE BRIDGE, WHEREVER THE BRIDGE IS.
	 *
	 * On a desktop it is a Node process beside the game and this writes into a
	 * loopback socket. With `-intervalbridge=inproc` there is no such process:
	 * the bridge is the world's own JavaScript running inside this one, and the
	 * same bytes are handed straight across. Nothing above this line knows
	 * which, and nothing above this line should.
	 */
	void Say(const FString& Text);

	/**
	 * THE BRIDGE THAT IS NOT A PROCESS.
	 *
	 * `-intervalbridge=inproc` runs `unreal-bridge.mjs` in this process instead
	 * of dialling one that is already running. It is the same file the desktop
	 * runs, on Unreal's HTTP, Unreal's WebSockets and the game thread's clock in
	 * place of Node's -- see FIntervalScript and interval-bridge/portable.
	 *
	 * WHY IT IS WORTH HAVING ON A DESKTOP TOO. It is what iOS has to do, since
	 * a phone will not have a second process; proving it here, against a window
	 * that already works, is the whole reason it exists. It also means a
	 * downloaded client needs no Node installed to play.
	 */
	void OpenInProcessBridge();

	TSharedPtr<IWebSocket> Socket;
	FString Endpoint;
	FTimerHandle ReconnectTimer;
	float ReconnectDelay = 1.f;

	/** True when the bridge is inside this process rather than beside it. */
	bool bInProcess = false;

	/** The game thread's turn of the world's clock; see FIntervalScript::Pump. */
	FTSTicker::FDelegateHandle PumpHandle;

	FIntervalFrame Frame;
	FIntervalFrame PrevFrame;
	double FrameArrivedAt = 0.0;
	double TickSeconds = 1.0;

	/**
	 * HOW LONG AN INTERVAL ACTUALLY TAKES TO ARRIVE, as opposed to how long
	 * the world says one lasts.
	 *
	 * These are not the same number and the difference is visible. `tickMs`
	 * is a thousand; a frame crossing a socket arrives every thousand
	 * milliseconds PLUS whatever the network and the sender were doing, and
	 * that jitter lands squarely in the middle of the only thing this window
	 * does between ticks, which is move people. Smoothed towards what is
	 * actually being seen, and held inside a sane band so one stalled second
	 * cannot convince it that intervals are five seconds long.
	 */
	double TickMeasured = 1.0;

	/**
	 * THE SLOW TAIL, not the average. See `GetInterpAlpha`.
	 *
	 * Rises instantly to any interval longer than itself and decays slowly
	 * back, so it tracks how late the LATEST intervals get rather than how
	 * long a typical one takes. Sizing the walk against this is what stops the
	 * figure finishing its stride and standing still until the world speaks.
	 */
	double TickSlowest = 1.0;

	FString PlayerId;
	FString WorldId;
	FString KeyFile;
	int32 WorldW = 0;
	int32 WorldH = 0;

	TArray<FString> TileNames;
	TSharedPtr<FJsonObject> Tables;
	FString TablesJson;
	FString SettlementsJson;
	FString WaysJson;

	TArray<FIntervalSettlement> Settlements;
	TSet<FIntPoint> Ways;

	/** Reads the two above out of the JSON `hello` brought, once. */
	void ReadFounding(const TSharedPtr<class FJsonObject>& Root);
};
