#include "IntervalHand.h"
#include "IntervalLook.h"
#include "ProceduralMeshComponent.h"
#include "IntervalStructures.h"

#include "IntervalGround.h"

#include "Algo/Reverse.h"

#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonReader.h"
#include "IntervalHud.h"
#include "IntervalPanel.h"
#include "EngineUtils.h"

#include "IntervalBridgeSubsystem.h"
#include "IntervalGeometry.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "Engine/Engine.h"
#include "GameFramework/PlayerController.h"

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
static const FIntervalFrame GEmptyFrame;


// The last interval the world ACCEPTED a deed from this citizen, as a number.
// Every field arrives as a string; a citizen who has never acted has none, and
// -1 is right for them -- any real acceptance is greater.
static int64 LastInputOf(const FIntervalFrame& Frame)
{
	if (!Frame.bHasMe)
	{
		return -1;
	}
	const FString* Seen = Frame.Me.Fields.Find(TEXT("lastInput"));
	return (Seen && !Seen->IsEmpty() && *Seen != TEXT("null")) ? FCString::Atoi64(**Seen) : -1;
}


DEFINE_LOG_CATEGORY_STATIC(LogIntervalHand, Log, All);

AIntervalHand::AIntervalHand()
{
	PrimaryActorTick.bCanEverTick = true;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}

void AIntervalHand::BeginPlay()
{
	Super::BeginPlay();

	// ---- THE MARK A CLICK LEAVES ----
	//
	// Spawned here rather than placed, for the reason the panel below gives.
	// It casts nothing and collides with nothing: it is a thing to look at for
	// less than a second and must never be a thing the cursor can hit, or the
	// mark from the last click would start swallowing the next one.
	// Attached and registered the way every other procedural mesh in this
	// plugin is. Giving the mark an ACTOR of its own was tried, to rule the
	// hand out as the owner, and it crashes: spawning an actor and making an
	// already-created component its root inside `BeginPlay` dies in
	// `RegisterComponent` with a null access. If the owner is ever suspected
	// again, the actor has to be spawned somewhere other than here.
	// ---- ON THE ACTOR THAT ALREADY DRAWS PROCEDURAL MESHES ----
	//
	// Built on the HAND, this component reported everything right -- one
	// section, registered, attached, movable, valid bounds, the correct world
	// location, a loaded material, visible -- and drew nothing, in Simulate
	// and in a real play session alike. The identical construction on
	// `AIntervalStructures` draws every wall, palisade and gatepost on the
	// island, so what differs is the OWNER.
	//
	// Giving it an actor of its own was tried and crashes: spawning one inside
	// `BeginPlay` and reparenting an existing component dies in
	// `RegisterComponent`. So it is hung on the structures actor, which is
	// already there, is already at the origin, and already does exactly this
	// for a living. The hand still owns the POINTER and decides what the mark
	// says; it simply is not the thing holding the geometry.
	TActorIterator<AIntervalStructures> Found(GetWorld());
	AIntervalStructures* Stage = Found ? *Found : nullptr;
	UObject* Owner = Stage ? static_cast<UObject*>(Stage) : static_cast<UObject*>(this);
	Mark = NewObject<UProceduralMeshComponent>(Owner);
	Mark->SetMobility(EComponentMobility::Movable);
	Mark->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mark->SetCastShadow(false);
	Mark->bReceivesDecals = false;
	USceneComponent* Hook = Stage ? Stage->GetRootComponent()
	                              : ToRawPtr(RootComponent);
	Mark->SetupAttachment(Hook);
	Mark->RegisterComponent();
	if (const UIntervalLook* Wardrobe = UIntervalLook::Resolve(nullptr))
	{
		if (Wardrobe->MarkMaterial) { Mark->SetMaterial(0, Wardrobe->MarkMaterial); }
	}

	// ---- AND THE PANEL THAT SHOWS WHAT IS IN THE PACK ----
	//
	// SPAWNED, NOT PLACED, for the same reason the air and the sound are: a
	// level actor cannot be saved from the automation this project is built
	// with, so anything that must survive a rebuild comes from the plugin.
	// The hand spawns it because the panel reads the hand's feed and because
	// the hand is the one thing that is always there when a citizen is.
	// AND NOW IT IS NOT SPAWNED AT ALL, by default.
	//
	// `AIntervalPanel` was the whole interface for a long time: a column of
	// grey text in the corner listing the pack, what was worn, what had been
	// learned and the book. Every one of those now has a proper home -- the
	// pack is a grid of sockets with sprites in it, and the other three are
	// behind the tabs above it -- so what is left is a second copy of all of
	// it, in the style the user asked to be rid of: "we also have to have
	// proper inventory visual, not the weird UI overlay we have now".
	//
	// It is kept, and kept working, because it is still the fastest way to
	// read everything the frame carries when something is wrong with the
	// window that replaced it. `bShowOldPanel` turns it back on.
	if (GetWorld() && GetWorld()->GetFirstPlayerController())
	{
		// THE HUD IS SPAWNED HERE NOW, AND THAT IS NOT A TIDY-UP.
		//
		// It used to be spawned by `AIntervalPanel`, along with the
		// right-click menu -- so the first thing that happened when the old
		// overlay was switched off was that the chat, the pack, the tabs and
		// the entire right-click menu went with it. The window came up with
		// nothing on it at all and nothing in any log, because none of it had
		// failed: none of it had been created. A thing the world cannot be
		// played without does not hang off a thing that can be turned off.
		TActorIterator<AIntervalHud> Screen(GetWorld());
		if (!Screen)
		{
			FActorSpawnParameters How;
			How.ObjectFlags |= RF_Transient;
			GetWorld()->SpawnActor<AIntervalHud>(AIntervalHud::StaticClass(),
				FTransform::Identity, How);
		}
		if (bShowOldPanel)
		{
			TActorIterator<AIntervalPanel> Already(GetWorld());
			if (!Already)
			{
				GetWorld()->SpawnActor<AIntervalPanel>(AIntervalPanel::StaticClass(),
					FTransform::Identity);
			}
		}
	}

	UGameInstance* GameInstance = GetGameInstance();
	Bridge = GameInstance ? GameInstance->GetSubsystem<UIntervalBridgeSubsystem>() : nullptr;
	if (!Bridge)
	{
		UE_LOG(LogIntervalHand, Error, TEXT("no bridge subsystem: is the plugin enabled?"));
		return;
	}
	Bridge->OnRefused.AddDynamic(this, &AIntervalHand::HandleRefused);
	Bridge->OnChat.AddDynamic(this, &AIntervalHand::HandleChat);

	if (APlayerController* PC = GetWorld()->GetFirstPlayerController())
	{
		PC->bShowMouseCursor = true;
		PC->bEnableClickEvents = true;
		PC->bEnableMouseOverEvents = true;

		// ---- AND THE MODE, FROM THE FIRST FRAME ----
		//
		// THE SAME FAULT THE GATE ALREADY FIXED ONCE, through a door its fix
		// did not cover. `IntervalGate` sets `GameAndUI` when a citizen
		// CROSSES THE THRESHOLD, and that is the only place it was ever set.
		// Everything before the crossing therefore ran in whatever mode the
		// engine left behind, which is game-only, and game-only routes no
		// mouse event to UMG at all.
		//
		// NOUGHT IS PLAYED BEFORE THE CROSSING. A new citizen knocks, waits
		// five minutes on the practice island, and spends that whole time in a
		// window where the pack cannot be clicked, no right-click menu opens
		// and the chat line cannot be typed in -- while the cursor is drawn,
		// because the three lines above ran. It looks like a window that is
		// working and is not, which is the worst shape this fault can take and
		// is exactly what the gate's own note says about it.
		//
		// Set here instead, because the HAND is the thing that needs UMG to
		// hear a click. The gate still takes UI-only while its card is up,
		// which is right -- a title card is modal -- and still hands back
		// GameAndUI when it opens. This only means the window is clickable
		// before anybody has crossed anything.
		FInputModeGameAndUI Mode;
		Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
		Mode.SetHideCursorDuringCapture(false);
		PC->SetInputMode(Mode);
	}
}

void AIntervalHand::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (Bridge)
	{
		Bridge->OnRefused.RemoveDynamic(this, &AIntervalHand::HandleRefused);
		Bridge->OnChat.RemoveDynamic(this, &AIntervalHand::HandleChat);
	}
	Super::EndPlay(EndPlayReason);
}

void AIntervalHand::HandleRefused(const FIntervalRefusal& Refusal)
{
	// VERBATIM. The world said why; this window does not improve on it,
	// translate it, or decide that some refusals are not worth mentioning.
	// AN ANSWER IS NOT A REFUSAL. Both arrive here, because both are the world
	// replying to something this window asked for, and the channel is the same
	// one for the same reason: a citizen should hear back either way.
	Say(Refusal.bOk
		? Refusal.Why
		: FString::Printf(TEXT("refused: %s, %s"), *Refusal.Of, *Refusal.Why),
		Refusal.Tick, true);
}

void AIntervalHand::HandleChat(const FIntervalSaid& Said)
{
	// NOTHING. AND THAT IS THE WHOLE FUNCTION.
	//
	// This used to put every chat line into the hand's feed, which is right
	// while the feed is the only place words can go. It is not any more: the
	// chat log draws a spoken line properly -- the speaker's name, calling and
	// place in gilt, the words in parchment, the channel marked -- and the
	// feed is ALSO drawn into that same log, for refusals and notices. So
	// every line anybody said appeared twice, once dressed and once plain,
	// two rows apart.
	//
	// The handler stays bound rather than being unwired, because the hand is
	// the thing that will one day want to know that somebody spoke -- a
	// citizen who is being talked to should probably stop walking. It simply
	// does not repeat it.
}

void AIntervalHand::Say(const FString& Text, int64 Tick, bool bRefusal)
{
	// THE SAME THING, ONCE.
	//
	// Some of what the world says it says every tick for as long as the
	// condition holds. A citizen waiting to be born is told "waiting ten
	// minutes, like everyone" three hundred times, once a second, and since
	// the feed went into the chat box that is three hundred lines -- the
	// chat scrolled past anything anybody had actually said, which for a
	// world built around talking to strangers is worse than saying nothing.
	//
	// A repeat of the line immediately above is dropped. It is not counted or
	// summarised: a "(x300)" would be this window keeping a tally the world
	// does not keep, and the thing a player needs to know is that the
	// condition still holds, which the one line already says.
	if (Feed.Num() > 0 && Feed.Last().Text == Text)
	{
		Feed.Last().At = FPlatformTime::Seconds();
		Feed.Last().Tick = Tick;
		return;
	}

	FIntervalFeedLine Line;
	Line.Text = Text;
	Line.Tick = Tick;
	Line.bRefusal = bRefusal;
	Line.At = FPlatformTime::Seconds();
	Feed.Add(Line);
	while (Feed.Num() > FMath::Max(FeedLines, 1) * 4)
	{
		Feed.RemoveAt(0);
	}
	OnFeedLine.Broadcast(Line);
	UE_LOG(LogIntervalHand, Log, TEXT("%s"), *Text);
}

// ---------------------------------------------------------------------------
// POINTING AT THINGS.
//
// A pick is not a ray against geometry. Everything in this world stands on a
// TILE -- the frame gives every node, mob and citizen an x and a y and nothing
// else -- so the honest question is "what does the world say is on this
// square", and the answer is the same one the world would give a citizen
// standing there. It also sidesteps a whole class of wrongness: a tree whose
// canopy overhangs its neighbour would otherwise be clicked by pointing at
// ground it is not on.
TArray<FIntervalTarget> AIntervalHand::TargetsAt(int32 TileX, int32 TileY) const
{
	TArray<FIntervalTarget> Found;
	if (!Bridge)
	{
		return Found;
	}
	const FIntervalFrame& Frame = Bridge->GetFrame();

	auto Take = [&](const FIntervalEntity& E, EIntervalTargetKind Kind)
	{
		if (E.X != TileX || E.Y != TileY)
		{
			return;
		}
		FIntervalTarget T;
		T.Kind = Kind;
		T.Id = E.Id;
		T.Type = E.Kind;
		if (const FString* Finer = E.Fields.Find(TEXT("kind")))
		{
			T.Sub = *Finer;
		}
		// WHAT TO CALL IT. The world's own name where it gave one -- a keeper
		// is `Delia` -- and its finest word otherwise. Never a word this
		// window made up.
		if (const FString* Named = E.Fields.Find(TEXT("name")))
		{
			T.Name = *Named;
			// §7ds: AND WHAT THEY KEEP, WHERE THE WORLD SAID. A keeper's `kind`
			// is a trade the engine names -- `banker` is "the banker", `lumber`
			// is "the axe man" -- and until now the window used the name alone,
			// so a street in Anchor was a row of people called things with no
			// way to tell which one takes a deposit. Seventy-six of the
			// hundred and fifty-seven have no kind at all; those are residents
			// and stay just their name, which is the truth about them.
			if (Bridge && T.Type == TEXT("keeper") && !T.Sub.IsEmpty())
			{
				const FString Who = Bridge->WhoIs(*Named, T.Sub);
				if (!Who.IsEmpty()) { T.Name = Who; }
			}
		}
		// A THING ON THE GROUND IS NAMED BY WHAT IT IS, AND MARKED BY WHOSE
		// IT IS. The world writes `item` on every drop and `by` only where a
		// citizen's goods reached the ground -- never on a beast's spoil -- so
		// `another` here is the world's own answer and not a guess.
		if (Kind == EIntervalTargetKind::Drop)
		{
			if (const FString* What = E.Fields.Find(TEXT("item")))
			{
				T.Name = *What;
			}
			const FString* Whose = E.Fields.Find(TEXT("by"));
			const bool bTheirs = Whose && !Whose->IsEmpty()
				&& *Whose != Bridge->GetFrame().Me.Id;
			T.Sub = bTheirs ? TEXT("another") : TEXT("mine");
			if (const FString* Many = E.Fields.Find(TEXT("qty")))
			{
				const int32 N = FCString::Atoi(**Many);
				if (N > 1) { T.Name = FString::Printf(TEXT("%s x%d"), *T.Name, N); }
			}
		}
		// AND WHAT MAY BE DONE TO A PERSON. The bridge writes it as a list on
		// the citizen themselves; see `mayDoTo`. Flattened into the entity's
		// fields under dotted keys like everything else the world sends, so
		// it comes back as `may.0`, `may.1` and so on.
		// A BEAST CARRIES ONE TOO. `still` reaches six tiles and names a
		// `target`, so it has nowhere to be clicked unless the thing it is
		// aimed at offers it.
		if (Kind == EIntervalTargetKind::Citizen || Kind == EIntervalTargetKind::Mob)
		{
			if (const FString* Allowed = E.Fields.Find(TEXT("may")))
			{
				Allowed->ParseIntoArray(T.May, TEXT(" "), true);
			}
		}
		if (T.Name.IsEmpty())
		{
			T.Name = T.Sub.IsEmpty() ? T.Type : T.Sub;
		}
		// A CITIZEN WHO HAS NOT TAKEN A NAME IS STILL SOMEBODY.
		//
		// Their nameplate reads `9e18ba7b, newcomer` -- the first eight of
		// their key -- and every menu about them read as though the person
		// were missing: "trade with  " with nothing after it, and a second
		// page headed by the same blank. Most citizens are nameless, because
		// a name costs standing, so this is the ordinary case and not the
		// edge one.
		if (Kind == EIntervalTargetKind::Citizen && T.Name.IsEmpty())
		{
			T.Name = T.Id.Left(8);
		}
		T.X = E.X;
		T.Y = E.Y;
		Found.Add(MoveTemp(T));
	};

	// CITIZENS AND MOBS FIRST. A wolf standing on a tree's tile is the thing
	// you meant to click; the tree is not going anywhere.
	for (const TPair<FString, FIntervalEntity>& P : Frame.Players)
	{
		if (P.Key != Frame.Me.Id) { Take(P.Value, EIntervalTargetKind::Citizen); }
	}
	for (const TPair<FString, FIntervalEntity>& M : Frame.Mobs)
	{
		Take(M.Value, EIntervalTargetKind::Mob);
	}
	for (const TPair<FString, FIntervalEntity>& N : Frame.Nodes)
	{
		Take(N.Value, EIntervalTargetKind::Node);
	}
	// AND WHAT IS LYING ON IT. Before a node, because a thing dropped on a
	// doorway is the thing you are reaching for; the doorway is not going
	// anywhere. See EIntervalTargetKind::Drop.
	for (const TPair<FString, FIntervalEntity>& G : Frame.Ground)
	{
		Take(G.Value, EIntervalTargetKind::Drop);
	}

	// AND THE GROUND ITSELF, ALWAYS LAST AND ALWAYS THERE. Walking somewhere
	// is a thing a citizen can always choose, including onto a tile with a
	// tree on it -- the world decides whether that is allowed, not this.
	FIntervalTarget Earth;
	Earth.Kind = EIntervalTargetKind::Ground;
	Earth.X = TileX;
	Earth.Y = TileY;
	Earth.Name = FString::Printf(TEXT("%d, %d"), TileX, TileY);
	Found.Add(MoveTemp(Earth));
	return Found;
}

TArray<FIntervalTarget> AIntervalHand::TargetsUnderCursor() const
{
	int32 X = 0, Y = 0;
	if (!TileUnderCursor(X, Y))
	{
		return TArray<FIntervalTarget>();
	}
	return TargetsAt(X, Y);
}

namespace
{
	/**
	 * THE WORLD'S WORD FOR A DEED, AS A PERSON WOULD SAY IT.
	 *
	 * The engine's verbs are identifiers -- `deposit_all`, `offer_trade`,
	 * `read_chart`, `set_look` -- and a menu that prints them raw is a menu
	 * written in the world's internal language. Three of them had already been
	 * renamed by hand in the citizen's menu ("trade with", "part from"), which
	 * is the sign that the problem is general and the fix should be too:
	 * anything not named here simply loses its underscores, so a verb added to
	 * the world tomorrow reads acceptably tomorrow without being listed.
	 */
	/**
	 * What is in the pack, BY SLOT, so a deed that names a slot can name the
	 * right one. Empty strings for the empty slots, because the world's slot
	 * numbers are positions and not an ordering of what happens to be held.
	 */
	TArray<FString> PackWords(const FIntervalFrame& Now)
	{
		TArray<FString> Out;
		const FString* Raw = Now.Me.Fields.Find(TEXT("inventory"));
		if (!Raw)
		{
			return Out;
		}
		TArray<TSharedPtr<FJsonValue>> Slots;
		const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(*Raw);
		FJsonSerializer::Deserialize(Reader, Slots);
		for (const TSharedPtr<FJsonValue>& Entry : Slots)
		{
			FString What;
			if (Entry.IsValid() && Entry->Type == EJson::Object)
			{
				Entry->AsObject()->TryGetStringField(TEXT("item"), What);
			}
			Out.Add(What);
		}
		return Out;
	}

	/** How many are in each slot, alongside `PackWords`. */
	TArray<int32> PackCounts(const FIntervalFrame& Now)
	{
		TArray<int32> Out;
		const FString* Raw = Now.Me.Fields.Find(TEXT("inventory"));
		if (!Raw)
		{
			return Out;
		}
		TArray<TSharedPtr<FJsonValue>> Slots;
		const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(*Raw);
		FJsonSerializer::Deserialize(Reader, Slots);
		for (const TSharedPtr<FJsonValue>& Entry : Slots)
		{
			double Many = 1.0;
			if (Entry.IsValid() && Entry->Type == EJson::Object)
			{
				Entry->AsObject()->TryGetNumberField(TEXT("qty"), Many);
			}
			Out.Add(FMath::Max(static_cast<int32>(Many), 1));
		}
		return Out;
	}

	/** What is in the pack, as {word: how many}, read off the frame's own JSON. */
	TMap<FString, int32> CarriedIn(const FIntervalFrame& Now)
	{
		TMap<FString, int32> Carried;
		const FString* Raw = Now.Me.Fields.Find(TEXT("inventory"));
		if (!Raw)
		{
			return Carried;
		}
		TArray<TSharedPtr<FJsonValue>> Slots;
		const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(*Raw);
		FJsonSerializer::Deserialize(Reader, Slots);
		for (const TSharedPtr<FJsonValue>& Entry : Slots)
		{
			if (!Entry.IsValid() || Entry->Type != EJson::Object)
			{
				continue;
			}
			const TSharedPtr<FJsonObject>& Slot = Entry->AsObject();
			FString What;
			double Many = 1.0;
			Slot->TryGetStringField(TEXT("item"), What);
			Slot->TryGetNumberField(TEXT("qty"), Many);
			if (!What.IsEmpty())
			{
				Carried.FindOrAdd(What) += FMath::Max(static_cast<int32>(Many), 1);
			}
		}
		return Carried;
	}

	FString Phrase(const FString& Verb)
	{
		static const TMap<FString, FString> Said = {
			{ TEXT("deposit_all"),  TEXT("put everything away") },
			{ TEXT("offer_trade"),  TEXT("trade with") },
			{ TEXT("accept_trade"), TEXT("take the offer") },
			{ TEXT("cancel_trade"), TEXT("withdraw the offer") },
			{ TEXT("read_chart"),   TEXT("read") },
			{ TEXT("set_look"),     TEXT("change your face") },
			{ TEXT("claim_name"),   TEXT("take the name") },
			{ TEXT("stock_market"), TEXT("stock") },
			{ TEXT("price_market"), TEXT("price") },
			{ TEXT("raise_market"), TEXT("raise a stall") },
			{ TEXT("take_market"),  TEXT("take the takings") },
			{ TEXT("dismantle_market"), TEXT("take the stall down") },
			{ TEXT("build_brewpot"), TEXT("build a brewpot") },
		};
		if (const FString* Found = Said.Find(Verb))
		{
			return *Found;
		}
		return Verb.Replace(TEXT("_"), TEXT(" "));
	}
}

TArray<FIntervalOption> AIntervalHand::OptionsFor(const FIntervalTarget& Target) const
{
	TArray<FIntervalOption> Out;
	auto Add = [&Out](const FString& Verb, const FString& Label,
		const FString& Argument = FString())
	{
		FIntervalOption O;
		O.Verb = Verb;
		O.Label = Label;
		O.Argument = Argument;
		O.bDefault = Out.Num() == 0;
		Out.Add(MoveTemp(O));
	};

	switch (Target.Kind)
	{
	case EIntervalTargetKind::Node:
	{
		// WHAT THE BRIDGE SAYS, NOT WHAT THIS WINDOW THINKS. The affordances
		// are derived from the engine's own executor and handed over in
		// `hello`; nothing here knows that a well is for drinking.
		//
		// Asked by the FINER word first and the plain one after, because
		// `oak-tree` gathers and `tree` gathers, and a kind the table has
		// never heard of should still fall back to what its type affords.
		TArray<FString> Verbs;
		if (Bridge)
		{
			if (!Target.Sub.IsEmpty()) { Verbs = Bridge->AffordsFor(Target.Sub); }
			if (Verbs.Num() == 0) { Verbs = Bridge->AffordsFor(Target.Type); }
		}

		// §7ds: AND ANYTHING WITH WRITING ON IT CAN BE READ.
		//
		// First, so that it is the DEFAULT on a signpost: `Add` marks the first
		// row default and the interaction model is RuneScape's, where a left
		// click does the thing you obviously meant. On a post by the road that
		// is reading it. On a tollgate, which also takes a toll, reading is
		// still what you do first -- you want to know the price before you pay
		// it -- and paying is one row down.
		//
		// `read` is not an engine verb and never files anything; ActOnWith
		// answers it. So it is offered on evidence rather than on affordance:
		// the node has words on it, therefore they can be read.
		if (Bridge)
		{
			if (const FIntervalEntity* Post = Bridge->GetFrame().Nodes.Find(Target.Id))
			{
				const FString* Says = Post->Fields.Find(TEXT("text"));
				if (Says && !Says->IsEmpty())
				{
					Add(TEXT("read"), FString::Printf(TEXT("read  %s"), *Target.Name));
				}
			}
		}
		for (const FString& V : Verbs)
		{
			// A VERB THAT ALSO NAMES A THING IS ONE LINE AND A PAGE.
			//
			// `buy` names an ITEM and `smith` a RECIPE -- in both the world
			// finds the counter or the anvil the citizen is standing at -- so
			// a row reading "buy  delve" files a purchase of nothing and is
			// refused. The things themselves used to be listed here, one row
			// each, which for fifty-nine recipes is not a menu. Now the verb
			// appears once and `ChoicesFor` fills the second page.
			if (ChoicesFor(Target, V).Num() > 0)
			{
				Add(V, FString::Printf(TEXT("%s  %s"), *Phrase(V), *Target.Name));
				continue;
			}

			// AND ONLY WHAT THIS WINDOW CAN ACTUALLY FILE. See `CanFile`.
			if (Bridge && !Bridge->CanFile(V, false, Target.Kind))
			{
				continue;
			}
			// AND NOT A WORD THIS CITIZEN'S BOOK DOES NOT HOLD. See MaySpeak.
			if (Bridge && !Bridge->MaySpeak(V))
			{
				continue;
			}
			// AND NOT ONE SHUT FROM HERE. See FIntervalFrame::Barred.
			if (Bridge && Bridge->GetFrame().Barred.Contains(V))
			{
				continue;
			}
			Add(V, FString::Printf(TEXT("%s  %s"), *Phrase(V), *Target.Name));
		}
		// §0: THE FOUNTAIN IS THE DOOR OUT OF THE PRACTICE.
		//
		// Crossing is `spawn` and names nothing, so the banner at the top of
		// the screen has been the only way to press it. That works and reads
		// as a button on a heads-up display, which is not how anything else
		// in this world is done: "in the web window I used the fountain to
		// cross into the world... we can wire it to the fountain I think it
		// thematically fits".
		//
		// It does. A newcomer standing in Nought can now SEE where the door
		// is and walk to it, which is a better first five minutes than a
		// notice telling them to wait. Offered from the moment they arrive
		// rather than only once the vigil ripens: the bridge answers an early
		// press with how much is left, which is a countdown and not a
		// refusal, and knowing where to go is most of what a newcomer wants.
		if (Bridge && Bridge->GetFrame().bNought
			&& (Target.Type == TEXT("fountain") || Target.Type == TEXT("well")))
		{
			Add(TEXT("cross"), TEXT("cross into the world"));
		}
		break;
	}
	case EIntervalTargetKind::Pack:
	{
		// WHAT A THING IN THE PACK AFFORDS, derived by the bridge from the
		// engine exactly as a node's affordances are -- `wield` out of
		// EQUIPPABLE, `eat` out of the healing chain, `drop` for anything at
		// all. This window holds no opinion about what a loaf is for.
		TArray<FString> Verbs;
		if (Bridge)
		{
			Verbs = Bridge->AffordsForItem(Target.Name);
		}
		// AND WHAT THE GROUND UNDERFOOT ALLOWS, which is not the same question.
		//
		// Cooking, brewing, grinding, burying, stoking and banking are not
		// things an ITEM affords -- a loaf is no more cookable in a meadow
		// than it is bankable there -- they are things the PLACE affords, and
		// the engine's item tables were never going to name them. Drawn on
		// the place instead, they are rows that want a `slot` a node cannot
		// give, which is why a hearth has offered `cook` since the day the
		// menu existed and it has never once worked.
		//
		// So: a verb the ground allows, whose schema wants a slot, is a verb
		// about a thing in the pack, and it goes on the pack's rows. One rule,
		// derived from the world's own tables, in place of a list of places
		// and what may be done at them.
		//
		// They join the list BEFORE the sort rather than being pushed in front
		// of it, because the front of the list is the DEFAULT and a left click
		// on a sword at a bank must still draw the sword.
		if (Bridge)
		{
			const FIntervalFrame& Here = Bridge->GetFrame();
			for (const FString& Allowed : Here.AtHand)
			{
				const FIntervalAffords* Named = Bridge->VerbFields.Find(Allowed);
				if (!Named || !Named->Verbs.Contains(TEXT("slot")))
				{
					continue;
				}
				// BUT NOT ONE THAT ALSO NAMES THE PLACE.
				//
				// The ground says `stoke` may be done here; it cannot say
				// which fire, and it cannot say that bread is not fuel. Drawn
				// on the pack that put a "stoke" line on every row at a
				// furnace, and a citizen between two fires could feed the one
				// they did not mean. Those verbs are drawn on the place
				// instead, which knows both. See `NamesPlaceAndSlot`.
				if (Bridge->NamesPlaceAndSlot(Allowed))
				{
					continue;
				}
				Verbs.AddUnique(Allowed);
			}
		}
		// THE OBVIOUS THING FIRST, AND `drop` LAST OF ALL.
		//
		// The affordances arrive in the order the engine's tables happen to
		// name them, and for a weapon that put `drop` first -- so it became
		// the DEFAULT, and a left click on the sword a citizen had just walked
		// sixty tiles and spent twenty gold on threw it onto the grass. What a
		// thing affords is the world's to say; which of those a player most
		// likely meant is the window's, and no window has ever guessed "throw
		// it away".
		//
		// Putting a thing on, eating it and reading it lead; taking it off
		// follows; letting go of it is last.
		Verbs.Sort([](const FString& A, const FString& B)
		{
			auto Rank = [](const FString& V)
			{
				if (V == TEXT("drop")) { return 3; }
				// §6g: PUTTING A THING AWAY IS NOT THE OBVIOUS THING EITHER.
				// Ranked with `unwield` rather than left among the ordinary
				// verbs, because at a counter every item in the pack gains
				// this line and an unranked tie put it FIRST on the arrows --
				// so a left click on a quiver at a bank banked it instead of
				// nocking it. The same argument as `drop`: what a thing
				// affords is the world's to say, which one a player meant is
				// the window's, and nobody ever meant "file it away".
				if (V == TEXT("unwield") || V == TEXT("deposit")) { return 2; }
				// AND THE REST OF WHAT THE GROUND ALLOWS sits with the
				// ordinary verbs at 1: cooking a loaf at a fire IS the
				// obvious thing to do with a loaf at a fire.
				if (V == TEXT("wield") || V == TEXT("eat")
					|| V == TEXT("drink") || V == TEXT("read")) { return 0; }
				return 1;
			};
			return Rank(A) < Rank(B);
		});
		const bool bCanChoose = Bridge
			&& Bridge->MakesFromItem(Target.Name).Num() > 0;
		for (const FString& V : Verbs)
		{
			// `bCanChoose` because a verb whose schema wants a word this
			// window can supply from a menu line is filable, and one whose
			// word nothing can supply is not. See CanFile.
			if (Bridge && !Bridge->CanFile(V, bCanChoose, Target.Kind))
			{
				continue;
			}
			// AND NOT A VERB THIS CITIZEN IS NOT FAR ENOUGH ALONG FOR.
			//
			// `charter` is the one today: a chart becomes a ferry licence only
			// for a master wayfarer, and on anybody else the line is a lie.
			// The bar comes from the engine through the bridge; see VerbNeeds.
			if (Bridge && !Bridge->MeetsBar(V))
			{
				continue;
			}
			// AND NOT A THING THIS CITIZEN IS NOT FAR ENOUGH ALONG TO HOLD.
			//
			// The bar for taking a thing up is on the THING, not on the verb:
			// `wield` asks for nothing and `old-chain` asks for prowess 30.
			// So a newcomer who found the rarest drop in the world was offered
			// the one line they most wanted, clicked it, and nothing happened
			// at all -- no refusal in the feed, because a deed the world
			// declines at the validator never becomes an event.
			if (Bridge && V == TEXT("wield") && !Bridge->CanTakeUp(Target.Name))
			{
				continue;
			}
			// AND TAKING OFF A THING THAT IS NOT ON. `unwield` asks for a
			// slot, so it belongs to the four cells above the pack and not to
			// the pack: a chain in a bag is in no slot, and the line did
			// nothing whatever when clicked. See IsWorn.
			if (Bridge && V == TEXT("unwield")
				&& Target.Kind == EIntervalTargetKind::Pack
				&& !Bridge->IsWorn(Target.Name))
			{
				continue;
			}
			// AND NOT A WORD THIS CITIZEN'S BOOK DOES NOT HOLD. See MaySpeak.
			if (Bridge && !Bridge->MaySpeak(V))
			{
				continue;
			}
			// AND NOT ONE THE WORLD HAS ALREADY SAID IS SHUT FROM HERE.
			// See FIntervalFrame::Barred: the bridge answers per frame what
			// no affordance table can, because the condition is about the
			// citizen rather than about the ground or the thing.
			if (Bridge && Bridge->GetFrame().Barred.Contains(V))
			{
				continue;
			}
			// ONE VERB, SEVERAL THINGS TO MAKE.
			//
			// `fletch` is not one deed, it is a workbench: a log becomes a
			// bow, a torch, a wand or a staff, and arrows come from BONES,
			// which is the one everybody guesses wrong. A single line saying
			// "fletch logs" would make a player guess which -- so the makes
			// are the lines, the way a stall's goods are the lines and an
			// anvil's recipes are. The bridge says what they are; this only
			// draws them.
			// ONE LINE, AND IT OPENS A LIST.
			//
			// This put every make in the main menu -- "fletch bow from logs",
			// "fletch torch from logs", and two more -- which is four lines
			// for one idea and pushes `drop` off the bottom of a short menu.
			// "We should have right click fletch log and then bring up a
			// menu, instead of all the fletch options appearing in one
			// column." So the verb is one line and the makes are a second
			// page, which is what a submenu is for and what this genre does.
			//
			// The makes are NOT listed here. The menu asks the bridge for
			// them when the line is chosen, so a make added to the world
			// appears without this file knowing anything about it.
			Add(V, FString::Printf(TEXT("%s  %s"), *Phrase(V), *Target.Name));
		}
		break;
	}
	case EIntervalTargetKind::Drop:
		// WHOSE IT IS CHANGES THE WORDS AND THE DEED.
		//
		// The world writes `by` wherever a citizen's things reach the ground
		// and never on a beast's spoil, so it already knows a stranger's logs
		// from a spider's. Taking a stranger's needs `confirm`, because one
		// tap at a crowded furnace must not be able to end a run that cost
		// somebody nine hundred hours -- so the menu says whose it is rather
		// than hiding the difference behind an identical word.
		Add(TEXT("pickup"), Target.Sub == TEXT("another")
			? FString::Printf(TEXT("take  %s  (another's)"), *Target.Name)
			: FString::Printf(TEXT("take  %s"), *Target.Name));
		// §7cf: AND THE TWO WORDS THAT ARE SAID TO A THING ON THE GROUND.
		//
		// `seal` and `unmake` name a `groundId`, which a row like this is the
		// only place in the window that has one. Both are spells: they ask for
		// the word to be in the citizen's book, a goo-staff in the hand and a
		// sigil in the pack, and the world refuses them anywhere near the
		// Lists. The book comes from the engine's own table; the rest is read
		// off the frame, so a row is only drawn where it would work.
		if (Bridge)
		{
			const FIntervalFrame& Said = Bridge->GetFrame();
			const FString* Book = Said.Me.Fields.Find(TEXT("book"));
			const FString* Held = Said.Me.Fields.Find(TEXT("equipment.weapon.item"));
			const bool bStaff = Held && *Held == TEXT("goo-staff");
			const bool bSigil = CarriedIn(Said).Contains(TEXT("sigil"));
			// Named, like the citizen's own table, so the coverage report can
			// see them: it reads the tables that ARE rows by name, because
			// every attempt to recognise them by shape has been wrong.
			static const TMap<FString, FString> Ground = {
				{ TEXT("seal"),   TEXT("seal") },
				{ TEXT("unmake"), TEXT("unmake") },
			};
			for (const TPair<FString, FString>& Word : Ground)
			{
				if (bStaff && bSigil
					&& Bridge->Speaks(Book ? *Book : FString(), Word.Key))
				{
					Add(Word.Key, FString::Printf(TEXT("%s  %s"),
						*Word.Value, *Target.Name));
				}
			}
		}
		break;
	case EIntervalTargetKind::Mob:
		Add(TEXT("attack"), FString::Printf(TEXT("attack  %s"), *Target.Name));
		// §7cf: AND WHAT MAY BE CAST AT IT. `still` is a spell of sight rather
		// than touch -- it outranges the bow -- so it is offered on a beast
		// that is nowhere near, which is exactly the point of it. The bridge
		// has already asked whether this citizen can: the level, the three
		// sigils, the cooldown and the beast's own immunity.
		for (const FString& Word : Target.May)
		{
			Add(Word, FString::Printf(TEXT("%s  %s"), *Phrase(Word), *Target.Name));
		}
		break;
	case EIntervalTargetKind::Citizen:
	{
		// YOURSELF IS A CITIZEN TOO, and a different menu.
		//
		// A handful of this world's deeds are about nobody but the person
		// doing them -- swearing to a calling, swearing a stint, sounding a
		// horn, stopping following somebody. None of them names a target, so
		// none of them could be a row on anything, and all of them have been
		// filable and unreachable since the day they were written.
		//
		// They go here because this is where a player already points at a
		// person, and the person they can always point at is themselves. No
		// new panel, no new gesture: right-click yourself, exactly as you
		// would right-click anybody.
		const FIntervalFrame& Now = Bridge ? Bridge->GetFrame() : GEmptyFrame;
		if (Now.bHasMe && Target.Id == Now.Me.Id)
		{
			// ONLY WHAT IS ACTUALLY OPEN. An oath already sworn cannot be
			// sworn again and the world says so; offering it anyway would be
			// a row that exists to be refused.
			if (ChoicesFor(Target, TEXT("swear")).Num() > 0)
			{
				Add(TEXT("swear"), TEXT("swear a calling"));
			}
			if (Bridge && Bridge->StintCap > 0)
			{
				Add(TEXT("stint"), TEXT("swear a stint"));
			}
			// THE HORN IS THE ONE THING IN THE OFF HAND THAT DOES SOMETHING.
			// It asks for no level and no cooldown of its own; it asks only
			// that you are carrying it, which the frame already says.
			const FString* Offhand = Now.Me.Fields.Find(TEXT("equipment.offhand.item"));
			if (Offhand && *Offhand == TEXT("horn"))
			{
				Add(TEXT("sound"), TEXT("sound the horn"));
			}
			Add(TEXT("unfollow"), TEXT("stop following"));
			// AND WHAT THE TILE UNDER THEM ALLOWS. A watchfire is kindled
			// where you stand and a stall is raised where you stand, so they
			// belong with the other deeds that are about nobody but you. The
			// bridge has already decided whether each is possible; if it is
			// not here, it is not offered.
			static const TMap<FString, FString> Underfoot = {
				{ TEXT("kindle"),       TEXT("kindle a watchfire here") },
				{ TEXT("raise_market"), TEXT("raise a stall here") },
				{ TEXT("survey"),       TEXT("survey this marker") },
				// §7a: and the first plank of a wild span, which the engine
				// requires you to be standing on. The bridge has already
				// checked the crossing, the empty tile and the plank.
				{ TEXT("found"),        TEXT("lay the first plank here") },
			};
			for (const TPair<FString, FString>& One : Underfoot)
			{
				if (Now.Underfoot.Contains(One.Key))
				{
					Add(One.Key, One.Value);
				}
			}
			break;
		}
		// AND WHAT MAY ACTUALLY BE DONE TO SOMEBODY ELSE.
		//
		// This listed all eight social verbs on every citizen and let the
		// world refuse the seven that were not allowed. The user rejected
		// that on sight -- "it should only show actually available options.
		// Not attack unless it's in wild or if both have consignment" -- and
		// a menu whose rows mostly do nothing is not a menu whatever the
		// reasoning behind it.
		//
		// The conditions are the world's and are answered by the bridge,
		// which has the whole state: whether you are in the Wilds together,
		// whether they are already a friend, whether there is an
		// apprenticeship between you at all. This draws what it is told and
		// keeps no copy of the rules.
		//
		// THE WORDS ARE NOT THE ENGINE'S EITHER. "attack" and "strike" were
		// two rows nobody could tell apart -- `special` is the harder blow
		// your weapon has, not a different kind of fight -- and "part from"
		// read as leaving somebody when it means ending an apprenticeship.
		const TMap<FString, FString> Reads = {
			{ TEXT("offer_trade"), TEXT("trade with  {}") },
			{ TEXT("befriend"),    TEXT("remember  {}") },
			{ TEXT("unfriend"),    TEXT("forget  {}") },
			{ TEXT("follow"),      TEXT("fall in behind  {}") },
			{ TEXT("teach"),       TEXT("take  {}  as apprentice") },
			{ TEXT("part"),        TEXT("end the apprenticeship with  {}") },
			{ TEXT("attackp"),     TEXT("attack  {}") },
			{ TEXT("gambit"),      TEXT("strike hard at  {}") },
			{ TEXT("still"),       TEXT("still  {}") },
			{ TEXT("mendp"),       TEXT("mend  {}") },
		};
		// THE ORDER IS THE WINDOW'S, because the default is the first line and
		// the obvious thing to do to a person is not to hit them.
		static const TCHAR* Order[] = { TEXT("offer_trade"), TEXT("befriend"),
			TEXT("unfriend"), TEXT("follow"), TEXT("teach"), TEXT("part"),
			TEXT("mendp"), TEXT("still"), TEXT("attackp"), TEXT("gambit") };
		for (const TCHAR* Verb : Order)
		{
			if (!Target.May.Contains(Verb))
			{
				continue;
			}
			// SUBSTITUTED, NOT FORMATTED. `Printf` wants its format known at
			// compile time, and these come out of a table -- which is the
			// point of having a table.
			const FString* Reading = Reads.Find(Verb);
			Add(Verb, Reading ? Reading->Replace(TEXT("{}"), *Target.Name)
			                  : Target.Name);
		}
		break;
	}
	case EIntervalTargetKind::Vault:
	{
		// §6g: OUT OF THE VAULT, AND HOW MANY.
		//
		// `withdraw` is the one verb in the world that wants a COUNT, and a
		// count has no obvious gesture: a cell cannot be dragged here and a
		// number cannot be typed into a menu. So the counts are the lines, the
		// same way a stall's goods are -- one, ten, and the lot -- and the
		// obvious thing a left click does is take one.
		//
		// The offers are trimmed to what is actually there. Ten of something
		// there are three of is a row that files a deed the world refuses,
		// and a menu should not contain a lie about the vault it is drawn
		// from.
		const int32 Many = FMath::Max(1, Target.X);
		Add(TEXT("withdraw"), FString::Printf(TEXT("withdraw  %s"), *Target.Name),
			TEXT("1"));
		if (Many >= 10)
		{
			Add(TEXT("withdraw"), FString::Printf(TEXT("withdraw 10  %s"),
				*Target.Name), TEXT("10"));
		}
		if (Many > 1)
		{
			Add(TEXT("withdraw"), FString::Printf(TEXT("withdraw all  %s   (%d)"),
				*Target.Name, Many), FString::FromInt(Many));
		}
		break;
	}
	default:
		break;
	}

	// WALK HERE is offered for anything that is a PLACE, always last. It is
	// what a left click on bare ground has always done and it must not stop
	// being reachable because something is standing on the tile.
	//
	// A thing in the pack is not a place. It was offered anyway, because this
	// line was written before the pack had a menu, so a right click on a stack
	// of arrows ended with "walk here 0, 0" -- 0,0 being the slot number and
	// the far corner of the island, which is nowhere anybody meant.
	if (Target.Kind != EIntervalTargetKind::Pack
		&& Target.Kind != EIntervalTargetKind::Vault)
	{
		Add(TEXT("walk"), FString::Printf(TEXT("walk here  %d, %d"),
			Target.X, Target.Y));
	}
	return Out;
}

namespace
{
}

TArray<FIntervalOption> AIntervalHand::ChoicesFor(const FIntervalTarget& Target,
	const FString& Verb, const FString& SoFar) const
{
	TArray<FIntervalOption> Out;
	if (!Bridge)
	{
		return Out;
	}
	auto Offer = [&Out, &Verb](const FString& Label, const FString& Argument,
		bool bMore = false)
	{
		FIntervalOption O;
		O.Verb = Verb;
		O.Label = Label;
		O.Argument = Argument;
		O.bMore = bMore;
		Out.Add(MoveTemp(O));
	};

	// §11b: WHAT A HAULER TAKES UP.
	//
	// `consign` names a LIST of pack slots, which is the only deed in the
	// world that does, and a list is the one thing a menu line cannot carry.
	// So the verb sat afforded and undrawable at every store on the island,
	// and the whole hauling trade was out of reach of a mouse.
	//
	// The page is what a hauler actually wants first and what they want after.
	// EVERYTHING is the top line, because a consignment is a load and a load is
	// what is in the pack; the single slots follow for somebody carrying one
	// thing they mean to run and several they do not. Both are legal deeds --
	// the world asks only for at least one slot and at most a pack's worth --
	// and neither needs a second kind of menu to express.
	if (Verb == TEXT("consign"))
	{
		const FIntervalFrame& Now = Bridge->GetFrame();
		// ALREADY BEARING ONE IS THE END OF IT. The world refuses a second
		// load and says so; a page of refusals is not a page.
		const FString* Borne = Now.Me.Fields.Find(TEXT("consignment"));
		if (Borne && !Borne->IsEmpty() && *Borne != TEXT("null"))
		{
			return Out;
		}
		const TArray<FString> Words = PackWords(Now);
		const TArray<int32> Counts = PackCounts(Now);
		int32 Carried = 0;
		for (const FString& W : Words) { if (!W.IsEmpty()) { ++Carried; } }
		if (Carried == 0)
		{
			return Out;
		}
		if (Carried > 1)
		{
			Offer(FString::Printf(TEXT("everything  (%d)"), Carried), TEXT("*"));
		}
		for (int32 i = 0; i < Words.Num(); ++i)
		{
			if (Words[i].IsEmpty()) { continue; }
			const int32 Many = Counts.IsValidIndex(i) ? Counts[i] : 1;
			Offer(Many > 1
				? FString::Printf(TEXT("%s  (%d)"), *Words[i], Many)
				: Words[i], FString::FromInt(i));
		}
		return Out;
	}

	// WHICH FUEL, AT THE FIRE THAT WAS POINTED AT.
	//
	// `stoke` and `brew` are the only two deeds in the world that name a place
	// AND a thing in the pack, and that makes them a verb on the PLACE with a
	// page of things, exactly like an anvil's recipes. "Wouldn't it be better
	// to have stoke on the furnace and fire instead of on the item? That way
	// it wouldn't be possible to mistakenly stoke the wrong node."
	//
	// Which is the whole argument: the fire is the thing clicked, so there is
	// nothing to guess. Drawn the other way round -- on the coal's own row --
	// the window had to go looking for a fire beside the citizen, and somebody
	// standing between a furnace and a watchfire could feed the wrong one.
	//
	// ONLY WHAT THIS FIRE TAKES, and only what is being carried. A furnace
	// burns coal and charcoal; a watchfire takes coal or any log; a brewpot
	// wants grain, saltpetre or a raw catch. None of that is written here: it
	// is read off the engine's own handlers and sent by the bridge, so a fifth
	// wood or a new fuel appears on this page by itself. See `fuelsByNode`.
	if (Target.Kind == EIntervalTargetKind::Node && Bridge->NamesPlaceAndSlot(Verb))
	{
		const TArray<FString> Takes = Bridge->TakenAt(Verb, Target.Type, Target.Sub);
		if (Takes.Num() == 0)
		{
			return Out;   // the world has no such rule at this kind of place
		}
		const FIntervalFrame& Now = Bridge->GetFrame();
		const TArray<FString> Words = PackWords(Now);
		const TArray<int32> Counts = PackCounts(Now);
		for (int32 i = 0; i < Words.Num(); ++i)
		{
			if (Words[i].IsEmpty() || !Takes.Contains(Words[i]))
			{
				continue;
			}
			const int32 Many = Counts.IsValidIndex(i) ? Counts[i] : 1;
			// The slot rides on the line, because a slot is what the deed
			// takes and the player chose the row.
			Offer(Many > 1
				? FString::Printf(TEXT("%s  (%d)"), *Words[i], Many)
				: Words[i], FString::FromInt(i));
		}
		// AND NOTHING AT ALL IF THEY CARRY NO FUEL, so the verb does not
		// appear on the fire. A menu shows only what is possible, and "stoke"
		// with an empty pack is a line that can only fail. What it takes
		// stays discoverable: the handbook says, and so does the fire going
		// out.
		return Out;
	}

	// §7dp: WHAT IS ON THE SHELF OF A HOARD.
	//
	// `rifle` names an ITEM as well as the hoard -- you take one thing out of
	// it, once in a life -- and the window had no way to name one, so the
	// affordance was there and the line was never drawn. The contents arrive
	// in the frame like every other field of a node, flattened to `shelf.<item>`
	// with the count as the value, so the page is a read rather than a guess:
	// what the hoard actually holds, in the quantities it holds it.
	//
	// ONCE IN A LIFE is the world's rule and it is worth respecting here:
	// somebody who has already taken their one thing gets no page at all,
	// rather than a list of things that will be refused.
	if (Verb == TEXT("rifle"))
	{
		const FIntervalFrame& Now = Bridge->GetFrame();
		const FString* Spent = Now.Me.Fields.Find(TEXT("barrowed"));
		if (Spent && (*Spent == TEXT("true") || *Spent == TEXT("1")))
		{
			return Out;
		}
		const FIntervalEntity* Hoard = Now.Nodes.Find(Target.Id);
		if (!Hoard)
		{
			return Out;
		}
		for (const TPair<FString, FString>& Row : Hoard->Fields)
		{
			if (!Row.Key.StartsWith(TEXT("shelf.")))
			{
				continue;
			}
			const int32 Count = FCString::Atoi(*Row.Value);
			if (Count <= 0)
			{
				continue;
			}
			const FString Item = Row.Key.RightChop(6);
			Offer(FString::Printf(TEXT("%s  (%d)"), *Item, Count), Item);
		}
		return Out;
	}

	// §6br: WHOSE NAME GOES ON THE STONE.
	//
	// Four things, and the fourth is the point: a graver in the pack, a stone
	// that has no name yet, and the citizen it is FOR standing at the stone
	// with you. Nothing about who you are qualifies you; you either have the
	// chisel and the friend or you do not.
	//
	// So the page is the people who are actually at this stone. Not everybody
	// in sight -- a list of thirty names of whom one is standing here is a
	// list nobody can use -- and never yourself, which the world refuses and
	// which is the whole meaning of the deed: a name is given, not taken.
	if (Verb == TEXT("grave"))
	{
		const FIntervalFrame& Now = Bridge->GetFrame();
		if (!PackWords(Now).Contains(TEXT("graver")))
		{
			return Out;
		}
		for (const TPair<FString, FIntervalEntity>& Who : Now.Players)
		{
			if (Who.Key == Now.Me.Id)
			{
				continue;
			}
			// At or beside the stone, which is the world's own test and the
			// reason a name never appears on this island without its owner
			// having walked to the spot.
			if (FMath::Abs(Who.Value.X - Target.X)
				+ FMath::Abs(Who.Value.Y - Target.Y) > 1)
			{
				continue;
			}
			const FString* Named = Who.Value.Fields.Find(TEXT("name"));
			if (!Named || Named->IsEmpty())
			{
				continue;
			}
			Offer(*Named, Who.Key);
		}
		return Out;
	}

	// §7d: WHICH FACE. A look is one byte and the window reads it the way the
	// flat window does: bits for skin, for hair, for a beard, for the coat.
	// Offering all two hundred and fifty-six would be a list nobody reads, and
	// most of them differ only in bits this window does not draw.
	//
	// So it offers the ones that differ VISIBLY: the eight coats, each with
	// the skin and hair that come with it. That is the whole of what changes
	// on screen, and a citizen who wants a particular pairing can stand at the
	// glass again -- a look is free and changeable, which is the world's own
	// rule and the reason this can be a short list rather than a careful one.
	if (Verb == TEXT("set_look"))
	{
		for (int32 Coat = 0; Coat < 8; ++Coat)
		{
			// The coat is bits 2-4 of the byte, so stepping it by four walks
			// the eight of them; the low bits carry the skin along with it.
			const int32 Byte = (Coat * 4 + Coat) & 255;
			Offer(FString::Printf(TEXT("face %d"), Coat + 1),
				FString::FromInt(Byte));
		}
		return Out;
	}

	// WHAT A CITIZEN MAY SWEAR THEMSELVES TO.
	//
	// Seventeen callings, each resting on a craft, each asking fifty in it --
	// so the page is the ones this citizen has actually earned, and a citizen
	// who has earned none is told that rather than shown a list of seventeen
	// refusals. The level a craft is at is derived from its experience by the
	// world's own ladder; the window reads the level the frame already carries.
	if (Verb == TEXT("swear"))
	{
		const FIntervalFrame& Now = Bridge->GetFrame();
		// ALREADY SWORN IS SWORN FOR EVER. The world refuses a second oath and
		// it is right to: a calling is the one thing a citizen chooses about
		// themselves that is remembered permanently.
		const FString* Already = Now.Me.Fields.Find(TEXT("calling"));
		if (Already && !Already->IsEmpty())
		{
			return Out;
		}
		// §5r-iv: AND HOW MUCH OF THE ISLAND HAS BEEN SEEN.
		//
		// Half the door to a calling is travel, five of the island's seven
		// countries, because level fifty arrives in under two hours and a
		// citizen could otherwise swear their one lifelong trade having stood
		// at a single rock the whole time. Sent as a count beside the list the
		// world keeps; see `countries` in the bridge.
		const FString* Seen = Now.Me.Fields.Find(TEXT("countries"));
		const int32 Walked = Seen ? FCString::Atoi(**Seen) : 0;
		if (Bridge->SwearCountries > 0 && Walked < Bridge->SwearCountries)
		{
			// A ROW THAT READS RATHER THAN FILES. The same shape the anvil uses
			// when nothing can be forged: a player standing at the altar with
			// the levels and no miles must be told which half is missing, or
			// the page is empty for a reason they cannot see.
			FIntervalOption Why;
			Why.Label = FString::Printf(
				TEXT("walk more of the island first  (%d of %d countries)"),
				Walked, Bridge->SwearCountries);
			Out.Add(MoveTemp(Why));
			return Out;
		}
		// AND WHAT THE CLICK COSTS, SAID BEFORE IT IS CLICKED.
		//
		// This is the only choice in a citizen's life that cannot be taken
		// back, and the page listed "forester (woodcraft)" with nothing to say
		// so. A player in their second evening has no way to know from the row
		// that they are fixing the one craft they may ever master and capping
		// the other eight for good.
		//
		// A row with no verb files nothing and closes the menu, which is the
		// same thing the anvil does when nothing can be forged: it is there to
		// be read. First, so it is read before the eye reaches the callings.
		{
			FIntervalOption Weight;
			Weight.Label = FString::Printf(
				TEXT("for life, every other craft stops at %d"), Bridge->CapOther);
			Out.Add(MoveTemp(Weight));
		}
		for (const TPair<FString, FString>& Calling : Bridge->Callings)
		{
			// THE LEVEL, NOT THE EXPERIENCE. This read `skills.<craft>` off the
			// frame and compared it to fifty -- but that field is the raw
			// experience the world stores, and fifty experience is about level
			// three. So every calling was offered almost at once and the world
			// refused every one of them, which is the exact thing a menu here
			// must not do.
			//
			// `Levels` carries the craft's real level, worked out by the engine
			// and sent per interval, and `FillCrafts` already draws from it.
			const FIntervalCraft* Craft = Bridge->GetFrame().Levels.Find(Calling.Value);
			const int32 Reached = Craft ? Craft->Level : 0;
			if (Reached >= Bridge->SwearLevel)
			{
				Offer(FString::Printf(TEXT("%s   (%s)"), *Calling.Key, *Calling.Value),
					Calling.Key);
			}
		}
		return Out;
	}

	// AND FOR HOW LONG A STINT IS SWORN.
	//
	// The founding sets the cap and the engine will not take a stint over it.
	// A counter that stepped one interval at a time would be seven thousand
	// clicks, so the page is the lengths a person would actually name -- in
	// minutes, because the world ticks once a second and nobody swears in
	// seconds.
	if (Verb == TEXT("stint") && Bridge->StintCap > 0)
	{
		static const int32 Minutes[] = { 5, 10, 15, 30, 60, 120 };
		for (int32 Long : Minutes)
		{
			const int32 Ticks = Long * 60;
			if (Ticks > Bridge->StintCap)
			{
				break;
			}
			Offer(FString::Printf(TEXT("%d minutes"), Long), FString::FromInt(Ticks));
		}
		// AND THE WHOLE OF IT, when the cap is not one of the round numbers.
		if (Bridge->StintCap > 120 * 60)
		{
			Offer(FString::Printf(TEXT("as long as allowed   (%d minutes)"),
				Bridge->StintCap / 60), FString::FromInt(Bridge->StintCap));
		}
		return Out;
	}

	// AN OFFER OF TRADE IS TWO QUESTIONS: what you are handing over, and what
	// you want for it. The world demands both -- `giveSlots` must name a slot
	// that holds something, and the shape gate insists on an item XOR a
	// positive sum of gold -- so a bare "trade with Ulric" is a malformed deed
	// and always was. It was on the citizen menu from the day the menu existed
	// and has never once worked.
	//
	// Asked one at a time, as two pages. Crossing them into one page would be
	// a line for every thing you carry times every price, which is not a menu.
	if (Verb == TEXT("offer_trade") && Target.Kind == EIntervalTargetKind::Citizen)
	{
		const FIntervalFrame& Now = Bridge->GetFrame();
		if (SoFar.IsEmpty())
		{
			// WHAT YOU ARE GIVING. One line per thing in the pack, because a
			// slot that holds nothing is an offer the world refuses.
			const TArray<FString> Carried = PackWords(Now);
			const TArray<int32> Many = PackCounts(Now);
			for (int32 Slot = 0; Slot < Carried.Num(); ++Slot)
			{
				if (Carried[Slot].IsEmpty())
				{
					continue;
				}
				// THE WHOLE SLOT, AND THE ROW SAYS SO.
				//
				// `giveSlots` names SLOTS: a stack goes across whole, and the
				// world has no way to say "five of these ten". A row reading
				// just "arrows" let a citizen think they were offering one
				// arrow for ten gold when they were offering all ten, which
				// is the kind of surprise a trade must not contain.
				const int32 Count = Many.IsValidIndex(Slot) ? Many[Slot] : 1;
				Offer(Count > 1
					? FString::Printf(TEXT("%s  x%d   (the whole stack)"),
						*Carried[Slot], Count)
					: Carried[Slot],
					FString::FromInt(Slot), true);
			}
			return Out;
		}
		// AND WHAT YOU WANT FOR IT. Gold, in the sums a person actually names
		// -- a counter that stepped one coin at a time would be a hundred
		// clicks for a hundred gold, and this world's prices are round.
		static const int32 Asks[] = { 1, 5, 10, 25, 50, 100, 250, 1000 };
		for (int32 Ask : Asks)
		{
			Offer(FString::Printf(TEXT("for %d gold"), Ask),
				FString::Printf(TEXT("%s|%d"), *SoFar, Ask));
		}
		// AND ANY SUM AT ALL. Round numbers cover most of what a person names
		// and none of what they mean when they are haggling -- "it should be
		// possible to trade for x gold instead of arbitrary amounts" -- so the
		// last line hands the question to a box you can type a number into.
		Offer(TEXT("for another amount…"),
			FString::Printf(TEXT("%s|ask"), *SoFar));
		return Out;
	}

	// A THING IN THE PACK, AND WHAT IT CAN BECOME. A log makes a bow, a torch,
	// a wand or a staff; arrows come from bones. The bridge derives it.
	if (Verb == TEXT("fletch") && Target.Kind == EIntervalTargetKind::Pack)
	{
		for (const FString& Make : Bridge->MakesFromItem(Target.Name))
		{
			Offer(Make, Make);
		}
		return Out;
	}

	// A SHOP IS ITS GOODS. `buy` names an ITEM -- the world finds whichever
	// counter the citizen is standing at -- so the price goes on the line and
	// the list is the shop window: a player learns what is for sale by right
	// clicking the stall, the same way they learn everything else.
	if (Verb == TEXT("buy"))
	{
		const FIntervalStock* Stock = Bridge->StockOf(Target.Sub);
		if (!Stock)
		{
			Stock = Bridge->StockOf(Target.Type);
		}
		if (Stock)
		{
			for (const TPair<FString, int32>& Good : Stock->Price)
			{
				Offer(FString::Printf(TEXT("%s   %d gold"), *Good.Key, Good.Value),
					Good.Key);
			}
		}
		return Out;
	}

	// AN ANVIL IS ITS WORK. Every recipe is listed with what it takes -- and
	// ONLY the ones the citizen has the materials for, because a list of
	// fifty-nine things of which two are possible is a list nobody reads.
	// What is missing stays discoverable: the cost is written on every row.
	// `smelt` IS THE SAME QUESTION AS `smith`, asked at a furnace instead of an
	// anvil: it names a RECIPE out of the same table, and the ore-to-bar
	// entries in that table are exactly what a furnace is for. It was left out
	// only because the branch was written while standing at an anvil.
	if (Verb == TEXT("smith") || Verb == TEXT("smelt"))
	{
		const TMap<FString, int32> Carried = CarriedIn(Bridge->GetFrame());
		for (const TPair<FString, FIntervalStock>& Work : Bridge->Recipes)
		{
			FString Cost;
			bool bAfford = true;
			for (const TPair<FString, int32>& Part : Work.Value.Price)
			{
				const int32* Have = Carried.Find(Part.Key);
				if (!Have || *Have < Part.Value)
				{
					bAfford = false;
				}
				Cost += FString::Printf(TEXT("%s%d %s"),
					Cost.IsEmpty() ? TEXT("") : TEXT(", "), Part.Value, *Part.Key);
			}
			if (bAfford)
			{
				Offer(FString::Printf(TEXT("%s   (%s)"), *Work.Key, *Cost), Work.Key);
			}
		}
		// AND IF THE ANSWER IS NONE, SAY SO. Dropping the `smith` line
		// altogether would leave a citizen standing at an anvil wondering
		// whether the window had forgotten anvils. A row with no verb files
		// nothing and just closes -- it is there to be read.
		if (Out.Num() == 0)
		{
			FIntervalOption Nothing;
			Nothing.Label = Verb == TEXT("smelt")
				? TEXT("nothing you carry can be smelted here")
				: TEXT("nothing you carry can be forged here");
			Out.Add(MoveTemp(Nothing));
		}
		return Out;
	}
	return Out;
}

FString AIntervalHand::VerbUnderCursor() const
{
	const TArray<FIntervalTarget> Under = TargetsUnderCursor();
	if (Under.Num() == 0)
	{
		return FString();
	}
	const TArray<FIntervalOption> Options = OptionsFor(Under[0]);
	// `walk` is what bare ground offers and is not worth a cursor of its own.
	if (Options.Num() == 0 || Options[0].Verb == TEXT("walk"))
	{
		return FString();
	}
	// AND WHAT IT IS ABOUT, WHERE THE VERB ALONE IS NOT ENOUGH.
	//
	// `gather` is one word for three jobs -- chopping, mining and fishing --
	// so a cursor keyed on the verb alone showed a PICKAXE over a tree, which
	// is not a hint, it is a wrong answer. The kind rides along after a bar
	// and the window picks the tool from it.
	if (Options[0].Verb == TEXT("gather"))
	{
		const FString& Kind = Under[0].Sub.IsEmpty() ? Under[0].Type : Under[0].Sub;
		return Options[0].Verb + TEXT("|") + Kind;
	}
	return Options[0].Verb;
}

void AIntervalHand::ActOn(const FString& Verb, const FIntervalTarget& Target)
{
	ActOnWith(Verb, Target, FString());
}

void AIntervalHand::ActOnWith(const FString& Verb, const FIntervalTarget& Target,
	const FString& Argument)
{
	// ---- THE BRACKETS, ON THE THING BEING ACTED ON ----
	//
	// `walk` is left alone deliberately: it reaches `WalkTo` below and is
	// marked there with the ring, so marking it here as well would put both
	// marks on one click and say two things at once.
	//
	// The tile comes from the frame rather than from the cursor. A target is
	// named by id, and the id is what the deed carries; asking the cursor
	// again would mark wherever the pointer had got to by the time the menu
	// row was chosen, which on a moving beast is the wrong tile.
	if (Verb != TEXT("walk") && Bridge)
	{
		const FIntervalFrame& Where = Bridge->GetFrame();
		const FIntervalEntity* It = Where.Nodes.Find(Target.Id);
		if (!It) { It = Where.Mobs.Find(Target.Id); }
		if (!It) { It = Where.Players.Find(Target.Id); }
		if (!It) { It = Where.Ground.Find(Target.Id); }
		if (It) { ShowMark(It->X, It->Y, true); }
	}
	// ---- §7ds: READING IS NOT A DEED ----
	//
	// Two hundred and ten nodes on the founded island carry a `text`: a hundred
	// and ninety-nine signposts, eight landmarks and three tollgates. "Bleakfell.
	// The last roof. Past here the moor keeps its own hours." "Watersmeet.
	// Boats, and a ferryman with no ferry. Ask Gilbert what he is building."
	// None of it had ever been shown to anybody.
	//
	// It was invisible for a structural reason rather than an oversight: a
	// node's options come from `AffordsFor`, which is the engine's own list of
	// what a verb can do to a thing, and NOTHING in the engine reads a sign.
	// There is no `read` input and there should not be -- reading does not
	// change the world, costs no interval and files nothing -- so a window
	// waiting to be told about it waits for ever.
	//
	// So it is answered here, like `walk`. The text is already on the node in
	// every frame; this is the window finally saying it out loud.
	if (Verb == TEXT("read"))
	{
		if (Bridge)
		{
			if (const FIntervalEntity* Post = Bridge->GetFrame().Nodes.Find(Target.Id))
			{
				if (const FString* Says = Post->Fields.Find(TEXT("text")))
				{
					if (!Says->IsEmpty()) { Say(*Says, Bridge->GetFrame().Tick, false); return; }
				}
			}
		}
		// A sign with nothing on it is a post. Saying so is better than a
		// menu row that does nothing when it is clicked.
		Say(TEXT("Nothing is written on it."), Bridge ? Bridge->GetFrame().Tick : 0, false);
		return;
	}

	if (Verb == TEXT("walk"))
	{
		// ---- A CLICK ON THE GROUND IS ROUTED ----
		//
		// This filed ONE STRAIGHT RUN, which the world stops at the first
		// thing in the way. Around any building that means a click, a wall,
		// another click, another wall; in a courtyard with one way out it
		// means the citizen never leaves at all, however many times you click.
		// A player would read that as a window whose walking does not work,
		// and it is half of what "walking is extremely buggy" was: the other
		// half was twelve frames a second, which was found and fixed, and this
		// was left because a citizen standing in open country gets away with
		// it.
		//
		// `WalkRoute` is the one the minimap has always used -- it plans, it
		// re-plans when a leg stops dead, and it remembers which tiles turned
		// out to be shut. It falls back to a straight run when there is no
		// bridge or no citizen to plan for, so there is nothing to lose.
		//
		// Found by trying to walk from a courtyard in Anchor to the plots
		// outside it: the row of buildings at y=282 is unbroken for fifteen
		// tiles and the gap is at the far end of it.
		WalkRoute(Target.X, Target.Y);
		return;
	}

	// WHICH FIELD CARRIES THE TARGET is the only thing this has to know about
	// any verb, and the world's own schema decides it: a node goes in
	// `nodeId`, a mob in `mobId`, a citizen in `targetId`. Everything else --
	// whether the deed is legal, whether the citizen is close enough, whether
	// they have the tool -- is the world's to refuse, and it says so through
	// the feed.
	// AND WHETHER IT NAMES ONE AT ALL, which the engine's schema decides.
	//
	// This filed `nodeId` for every node, `mobId` for every beast and
	// `targetId` for every citizen, unconditionally. That is right for most
	// verbs and wrong for the ones where the world finds the thing itself: a
	// citizen drinks from whichever well they are beside, cooks at whichever
	// hearth, smelts at whichever furnace, smiths at whichever anvil, buys at
	// whichever stall -- and the deed names none of them. Every one of those
	// came back "unknown field nodeId on drink" and did nothing, from a menu
	// entry that had offered it a second earlier. The menu was right, the
	// affordance was right, and the deed was malformed on the way out.
	//
	// So the field is the one the schema asks for, and when the schema asks
	// for none the deed carries none. The TARGET is still used -- to decide
	// whether to walk there first, which is the other half of what a click on
	// a distant thing means.
	// A THING IN THE PACK IS NAMED BY ITS SLOT, and a slot is a number.
	//
	// Every other target is named by an id in a string field; the pack's
	// verbs -- wield, eat, drop, alch, bury -- take `slot`. There is no walk
	// to do first either: what a citizen is carrying is always in reach.
	// TAKING SOMETHING OFF THE GROUND HAS ITS OWN DOOR ALREADY.
	//
	// `PickUp` was written long before there was any way to reach it: it
	// knows the deed carries a BOOLEAN and that the world types its fields,
	// which `Deed` cannot express. The menu simply had no line that called
	// it, so `drop` worked and `pickup` did not, and a thing put down was a
	// thing gone.
	//
	// The confirmation is not a second click here. The player has already
	// read "(another's)" on the line they chose, which is exactly the
	// information the world's gate exists to put in front of them.
	if (Target.Kind == EIntervalTargetKind::Drop && Verb == TEXT("pickup"))
	{
		PickUp(Target.Id, Target.Sub == TEXT("another"));
		return;
	}
	// AND TAKING A THING OFF NAMES THE SLOT, NOT THE THING.
	//
	// `unwield` is `{ gear }` and gear is a WORD -- `weapon`, `head` -- where
	// every other verb a menu line files about a carried thing takes `slot`,
	// a number. The generic path below sends the number, the world types the
	// field as a name, and the deed is malformed before it is even judged. So
	// `unwield` has been in the menu since the menu existed and has never once
	// taken a helmet off anybody; `AIntervalHand::Unwield` was written for it
	// and had no caller at all.
	//
	// The slot comes from the frame, which says what is in each one. A line
	// drawn for a thing that is not worn cannot get here: see the filter in
	// OptionsFor, which is the other half of this.
	if (Verb == TEXT("unwield") && Bridge)
	{
		const FString Gear = Bridge->WornSlotOf(Target.Name);
		if (!Gear.IsEmpty())
		{
			Unwield(Gear);
			return;
		}
	}
	// THE DEEDS A CITIZEN DOES TO THEMSELVES. None of them names a target --
	// the world knows who filed it -- so none goes through the target-field
	// machinery below, which would look for somebody to point at and find the
	// person doing the pointing.
	if (Verb == TEXT("swear"))
	{
		// §5w: AND WHO ATTESTED IT, STATED AS NOBODY.
		//
		// `attester` is a declared field on `swear` and every declared field in
		// this constitution is required, so leaving it out is a malformed deed.
		// Empty is the world's word for "nobody attested this", which is a real
		// swearing: the first forester has nobody to name.
		//
		// Naming a master from this window is a separate piece of work. It
		// wants a page of the masters standing beside you who have taken you
		// on, which is a thing the frame can answer and the menu cannot yet
		// ask. Until then a swearing from here is unattested, which is legal
		// and costs the citizen nothing but the mark.
		Deed(TEXT("swear"), {}, { { TEXT("calling"), Argument },
			{ TEXT("attester"), FString() } });
		return;
	}
	if (Verb == TEXT("set_look"))
	{
		Deed(TEXT("set_look"), { { TEXT("look"), FCString::Atoi(*Argument) } }, {});
		return;
	}
	if (Verb == TEXT("stint"))
	{
		Deed(TEXT("stint"), { { TEXT("n"), FCString::Atoi(*Argument) } }, {});
		return;
	}
	if (Verb == TEXT("sound") || Verb == TEXT("unfollow")
		|| Verb == TEXT("kindle") || Verb == TEXT("raise_market")
		|| Verb == TEXT("survey"))
	{
		Deed(Verb, {}, {});
		return;
	}

	// ---- A DEED THAT WANTS A FIGURE ASKS FOR ONE ----
	//
	// `price_market` wants what to charge, `lay` how many planks to put down,
	// `dedicate` what to pay. Each is afforded by a node the citizen is
	// standing at, and each was undrawable for want of one number -- so the
	// menu offered nothing at a stall you own, a half-built span or a
	// dedication, which are three of the more interesting things on the
	// island to be standing in front of.
	{
		static const TMap<FString, TPair<FString, FString>> Figures = {
			{ TEXT("price_market"), { TEXT("ask"), TEXT("what will you charge?") } },
			{ TEXT("lay"),          { TEXT("n"),   TEXT("how many planks?") } },
			{ TEXT("dedicate"),     { TEXT("pay"), TEXT("how much will you give?") } },
		};
		if (const TPair<FString, FString>* Wants = Figures.Find(Verb))
		{
			if (Argument.IsEmpty())
			{
				AskingVerb = Verb;
				AskingField = Wants->Key;
				AskingFor = Wants->Value;
				AskingOn = Target;
				return;
			}
			TMap<FString, FString> Words;
			const FString Field = Bridge ? Bridge->TargetFieldFor(Verb) : FString();
			if (!Field.IsEmpty() && !Target.Id.IsEmpty())
			{
				Words.Add(Field, Target.Id);
			}
			Deed(Verb, { { Wants->Key, FCString::Atoi(*Argument) } }, Words);
			return;
		}
	}

	// §0: THE CROSSING, WHICH IS NOT A DEED THIS WINDOW FILES.
	//
	// `cross` is the window's own word. The bridge knows birth is two-phase,
	// how long the vigil is, and that a bare `spawn` with no wait behind it is
	// refused forever with nothing said, so it is asked for the whole thing at
	// once. Walking to the fountain first is the ordinary behaviour for a verb
	// aimed at a node, and it is what makes this read as going somewhere.
	if (Verb == TEXT("cross"))
	{
		const FIntervalFrame& Here = Bridge ? Bridge->GetFrame() : GEmptyFrame;
		if (Here.bHasMe
			&& FMath::Abs(Here.Me.X - Target.X) + FMath::Abs(Here.Me.Y - Target.Y) > 1)
		{
			WalkRoute(Target.X, Target.Y);
			return;
		}
		if (Bridge)
		{
			Bridge->EnterWorld();
		}
		return;
	}

	// AN OFFER OF TRADE, COMPOSED BY THE TWO PAGES ABOVE.
	//
	// The argument that comes back is "<slot>|<gold>", which is the only place
	// in this window where a menu line carries two answers -- because the deed
	// wants two and the world will not take it with either missing.
	if (Verb == TEXT("offer_trade") && Target.Kind == EIntervalTargetKind::Citizen)
	{
		FString SlotWord;
		FString GoldWord;
		if (!Argument.Split(TEXT("|"), &SlotWord, &GoldWord))
		{
			Say(TEXT("say what to give and what for"), 0, true);
			return;
		}
		// A SUM TO BE TYPED, rather than one of the round ones. The menu
		// cannot take a number, so it hands the question on: the offer waits,
		// named but unpriced, until a figure is entered.
		if (GoldWord == TEXT("ask"))
		{
			Asking = Target.Id;
			AskingSlot = FCString::Atoi(*SlotWord);
			return;
		}
		OfferTrade(Target.Id, { FCString::Atoi(*SlotWord) }, FString(),
			FCString::Atoi(*GoldWord));
		return;
	}

	// §7a: THE FIRST PLANK, which names the tile the citizen is standing on.
	//
	// The only verb in the world whose target is a coordinate rather than an
	// id, and the coordinate is not a choice: the engine refuses it unless it
	// is the founder's own tile. So there is nothing to point at and nothing
	// to ask -- the deed is filled in from where they are standing, which is
	// the same place the menu was opened.
	if (Verb == TEXT("found"))
	{
		const FIntervalFrame& Standing = Bridge ? Bridge->GetFrame() : GEmptyFrame;
		if (!Standing.bHasMe)
		{
			Say(TEXT("nowhere to lay it"), 0, true);
			return;
		}
		Deed(TEXT("found"), { { TEXT("x"), Standing.Me.X },
		                      { TEXT("y"), Standing.Me.Y } }, {});
		return;
	}

	// §11b: TAKING UP A CONSIGNMENT, which is the one deed that names a LIST.
	//
	// It goes before the field machinery below because that machinery puts the
	// menu's answer into a single word, and this answer is either a slot or
	// the whole pack. `Consign` already knew how to send a list; it had never
	// been called by anything a player could click.
	if (Verb == TEXT("consign"))
	{
		TArray<int32> Slots;
		if (Argument == TEXT("*"))
		{
			const TArray<FString> Words = PackWords(
				Bridge ? Bridge->GetFrame() : GEmptyFrame);
			for (int32 i = 0; i < Words.Num(); ++i)
			{
				if (!Words[i].IsEmpty()) { Slots.Add(i); }
			}
		}
		else if (!Argument.IsEmpty())
		{
			Slots.Add(FCString::Atoi(*Argument));
		}
		Consign(Slots);
		return;
	}

	// §6g: OUT OF THE VAULT. There is no walking to do and no counter to name:
	// a citizen reading their vault is already standing at it, and the world
	// finds it for them. The count rode in on the menu line.
	if (Target.Kind == EIntervalTargetKind::Vault)
	{
		Withdraw(Target.Name, Argument.IsEmpty() ? 1 : FCString::Atoi(*Argument));
		return;
	}

	if (Target.Kind == EIntervalTargetKind::Pack)
	{
		// A CHOICE AS WELL AS A SLOT, where the verb takes one. `fletch` says
		// `make`; everything else in the pack takes the slot alone.
		TMap<FString, FString> Choice;
		if (!Argument.IsEmpty())
		{
			Choice.Add(TEXT("make"), Argument);
		}
		// A VERB THAT ALSO NAMES A PLACE IS NOT A PACK VERB AT ALL. `stoke`
		// and `brew` want a node as well as a slot, and a pack row has no
		// node to give -- so they are drawn on the PLACE and ask which thing
		// there. See `NamesPlaceAndSlot`, and the filter in OptionsFor that
		// keeps them off these rows.
		Deed(Verb, { { TEXT("slot"), Target.X } }, Choice);
		return;
	}

	const FString Field = Bridge ? Bridge->TargetFieldFor(Verb) : FString();
	TMap<FString, FString> Words;
	// ---- A SLOT IS A NUMBER, NOT A WORD ----
	//
	// `stoke` and `brew` name the place that was clicked AND the thing out of
	// the pack that the page chose, and the world types a slot as an integer.
	// Sent as a word it is malformed before it is judged, which is how feeding
	// the furnace managed to be offered and do nothing for as long as it did.
	//
	// It goes through the ordinary tail below rather than taking a path of its
	// own, because that tail is also what walks to a fire on the far side of a
	// wall and files the deed on arrival. See `PendingWith`.
	TMap<FString, int32> Figures;
	const bool bPlaceAndSlot = Bridge && Bridge->NamesPlaceAndSlot(Verb);
	if (bPlaceAndSlot)
	{
		if (Argument.IsEmpty())
		{
			// The page supplies the slot. A bare line files nothing rather
			// than a deed with a hole in it.
			return;
		}
		Figures.Add(TEXT("slot"), FCString::Atoi(*Argument));
	}
	else if (!Argument.IsEmpty())
	{
		// `buy` says `item`; `smith` and `smelt` say `recipe`. All three name a
		// thing rather than a place, and the schema is the authority on which
		// word each one wants.
		// `buy` and `rifle` say `item`; `smith` and `smelt` say `recipe`;
		// `grave` says `target`, because the thing it names is a person and
		// not a thing. The schema is the authority on which word each wants.
		const TCHAR* Word = TEXT("item");
		if (Verb == TEXT("smith") || Verb == TEXT("smelt")) { Word = TEXT("recipe"); }
		else if (Verb == TEXT("grave")) { Word = TEXT("target"); }
		Words.Add(Word, Argument);
	}
	switch (Target.Kind)
	{
	case EIntervalTargetKind::Node:
		if (!Field.IsEmpty()) { Words.Add(Field, Target.Id); }
		break;
	case EIntervalTargetKind::Mob:
		if (!Field.IsEmpty()) { Words.Add(Field, Target.Id); }
		// ONLY A BLOW HAS A STYLE. This was added to every deed aimed at a
		// beast, which was harmless while the only one was `attack` -- and the
		// moment a spell could be cast at one it became "unknown field style
		// on still", refused for a field the player never asked for.
		if (Verb == TEXT("attack") || Verb == TEXT("gambit"))
		{
			Words.Add(TEXT("style"), TEXT("even"));
		}
		break;
	case EIntervalTargetKind::Citizen:
		if (!Field.IsEmpty()) { Words.Add(Field, Target.Id); }
		if (Verb == TEXT("attackp") || Verb == TEXT("gambit"))
		{
			Words.Add(TEXT("style"), TEXT("even"));
		}
		break;

	default:
		Say(TEXT("nothing there to do that to"), 0, true);
		return;
	}

	// WALK TO IT FIRST IF IT IS OUT OF REACH. Adjacency in this world is
	// Manhattan distance one, and a deed filed from further away is refused
	// with nothing said about distance -- which reads as the click having done
	// nothing at all. Walking first is what a citizen would do anyway.
	const FIntervalFrame& Frame = Bridge ? Bridge->GetFrame() : GEmptyFrame;
	if (Frame.bHasMe)
	{
		const int32 Reach = FMath::Abs(Frame.Me.X - Target.X)
			+ FMath::Abs(Frame.Me.Y - Target.Y);
		if (Reach > 1)
		{
			// BESIDE IT, NOT ONTO IT.
			//
			// This walked to the target's own tile, and a node's tile is
			// occupied by the node: a stall, a well, an anvil, a tree. The
			// world refuses the last step every time, the window says "that
			// way is blocked", and the deed that was waiting on the walk is
			// dropped -- so clicking `buy` on a stall two tiles away did
			// nothing at all, and clicking it from beside the stall worked.
			// Which is a maddening thing to debug and an obvious thing to see
			// once the walk is watched.
			//
			// Adjacency in this world is Manhattan distance one, so the place
			// to stand is whichever of the four neighbours is nearest. Ties go
			// to the first, which is fine: they are all one step apart.
			// AND AN EMPTY ONE. Nearest is not enough: a stall in a row of
			// buildings has three of its four neighbours built on, and the
			// nearest of them is as unwalkable as the stall itself. The window
			// already knows what stands on every tile in sight -- it is the
			// same question the menu asks -- so a neighbour with anything on
			// it is passed over. A tile out of sight is taken on trust, which
			// is the right way round: the world refuses what it must.
			int32 StandX = Target.X;
			int32 StandY = Target.Y;
			int32 Best = MAX_int32;
			const int32 Around[4][2] = { {1, 0}, {-1, 0}, {0, 1}, {0, -1} };
			for (int32 Pass = 0; Pass < 2 && Best == MAX_int32; ++Pass)
			{
				for (const int32 (&Step)[2] : Around)
				{
					const int32 X = Target.X + Step[0];
					const int32 Y = Target.Y + Step[1];
					if (Pass == 0)
					{
						bool bTaken = false;
						for (const FIntervalTarget& Standing : TargetsAt(X, Y))
						{
							if (Standing.Kind != EIntervalTargetKind::Ground)
							{
								bTaken = true;
								break;
							}
						}
						if (bTaken)
						{
							continue;
						}
					}
					const int32 Far = FMath::Abs(Frame.Me.X - X)
						+ FMath::Abs(Frame.Me.Y - Y);
					if (Far < Best)
					{
						Best = Far;
						StandX = X;
						StandY = Y;
					}
				}
			}
			Say(FString::Printf(TEXT("%s is %d tiles off; walking there first"),
				*Target.Name, Reach), Frame.Tick, false);
			// ROUTED, for the same reason as above: a click on a stall on
			// the other side of a wall is a walk that has to get round it.
			WalkRoute(StandX, StandY);
			Pending = Verb;
			PendingOn = Target;
			PendingWith = Argument;
			return;
		}
	}
	Deed(Verb, Figures, Words);
}

bool AIntervalHand::TileUnderCursor(int32& OutX, int32& OutY) const
{
	APlayerController* PC = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
	if (!PC)
	{
		return false;
	}

	FVector Origin, Direction;
	if (!PC->DeprojectMousePositionToWorld(Origin, Direction))
	{
		return false;
	}

	// THE GROUND PLANE IS THE FALLBACK, NOT THE ANSWER. The world is flat --
	// it has tiles, not heights -- so where the ray crosses z = 0 is a tile
	// that always exists, and that is what this returns when the ray passes
	// through nothing on its way down.
	//
	// It was once the whole of it, and that was the bug: see `PickHeight`.
	// Tracing against real geometry is still not the answer either, and for a
	// reason the original note got right -- a click on a tree would be
	// answered with the tree's collider or with nothing, and most of what this
	// window draws has no collision at all. A column over each occupied tile
	// is the middle course: it knows nothing about meshes and it is still what
	// the player sees.
	if (FMath::IsNearlyZero(Direction.Z))
	{
		return false;
	}
	const float Distance = -Origin.Z / Direction.Z;
	if (Distance <= 0.f)
	{
		return false;   // looking at the sky
	}

	const FVector Ground = Origin + Direction * Distance;
	UIntervalGeometry::WorldToTile(Ground, OutX, OutY);

	// ---- AND NOW THE THINGS STANDING UP BETWEEN HERE AND THERE ----
	if (PickHeight > 0.f && Direction.Z < 0.f)
	{
		FreshenStoodOn();
		if (StoodOn.Num() > 0)
		{
			// Where the ray drops below the top of the tallest column. Above
			// that there is nothing to hit, so there is nothing to walk.
			const float Enter = FMath::Max(0.f, (PickHeight - Origin.Z) / Direction.Z);
			if (Enter < Distance)
			{
				// Fine enough that a two-metre tile cannot be stepped over,
				// and capped so that a camera lying almost flat -- where the
				// slab is very long in world terms -- costs a fixed amount.
				const float Step = UIntervalGeometry::GetTileSize() * 0.25f;
				const int32 Most = 64;
				const float Span = Distance - Enter;
				const float Walk = FMath::Min(Step, Span / static_cast<float>(Most));
				int32 LastX = MIN_int32, LastY = MIN_int32;
				for (float T = Enter; T <= Distance; T += FMath::Max(Walk, 1.f))
				{
					const FVector At = Origin + Direction * T;
					int32 TX = 0, TY = 0;
					UIntervalGeometry::WorldToTile(At, TX, TY);
					if (TX == LastX && TY == LastY)
					{
						continue;
					}
					LastX = TX; LastY = TY;
					if (StoodOn.Contains(TileKey(TX, TY)))
					{
						// The NEAREST column the ray pierces, which is the one
						// in front of the player's eye.
						OutX = TX; OutY = TY;
						return true;
					}
				}
			}
		}
	}
	return true;
}

void AIntervalHand::ShowMark(int32 TileX, int32 TileY, bool bAction)
{
	if (!bDrawMarks)
	{
		return;
	}
	MarkTile = FIntPoint(TileX, TileY);
	bMarkAction = bAction;
	MarkAt = FPlatformTime::Seconds();
}

// ---------------------------------------------------------------------------
// REBUILT EVERY FRAME, which is cheaper than it sounds and simpler than the
// alternative. A ring is seventy-two triangles and the brackets are sixteen;
// rebuilding them is nothing next to keeping a dynamic material instance alive
// per mark so that an opacity can be animated through it. The colour and the
// fade ride in the vertex colours, which `M_IntervalMark` reads directly.
void AIntervalHand::DriveMark()
{
	if (!Mark || MarkAt <= 0.0)
	{
		return;
	}
	const float Life = static_cast<float>(FPlatformTime::Seconds() - MarkAt);
	if (Life >= MarkSeconds)
	{
		Mark->ClearAllMeshSections();
		bMarkBuilt = false;
		MarkAt = 0.0;
		return;
	}
	const float T = FMath::Clamp(Life / FMath::Max(MarkSeconds, 0.01f), 0.f, 1.f);
	// It arrives wide and settles onto the tile, hard at first and slowing:
	// the eye is drawn by the movement and then released. Cubic, so almost all
	// of the travel is over in the first third of its life.
	const float Ease = 1.f - FMath::Pow(1.f - T, 3.f);
	FLinearColor Tint = bMarkAction ? MarkActColour : MarkWalkColour;
	// Full for the first third, then out. A mark that began fading instantly
	// is faint for the whole of the moment it exists to answer.
	Tint.A = 1.f - FMath::Clamp((T - 0.33f) / 0.67f, 0.f, 1.f);

	// THE COMPONENT GOES TO THE TILE AND THE MESH IS BUILT AROUND NOTHING.
	//
	// A procedural mesh's vertices are in COMPONENT space, and this component
	// hangs off the hand, which is not at the world origin. Building the ring
	// at world coordinates therefore drew it at the tile PLUS wherever the
	// hand happened to be, which on this island is far out to sea. The
	// structures actor gets away with world coordinates only because it sits
	// at the origin and always has.
	//
	// So the component is moved and the geometry is built about its own zero,
	// which is correct wherever the hand is and needs nothing to be true of
	// the actor it is attached to.
	Mark->SetWorldLocation(UIntervalGeometry::TileToWorld(MarkTile.X, MarkTile.Y)
		+ FVector(0.f, 0.f, MarkLift));
	const FVector Centre = FVector::ZeroVector;

	TArray<FVector> Vertices;
	TArray<int32> Triangles;
	TArray<FVector> Normals;
	TArray<FVector2D> UVs;
	TArray<FLinearColor> Colors;
	TArray<FProcMeshTangent> Tangents;

	// Flat, facing up, wound so it is seen from above.
	auto Quad = [&](const FVector2D& A, const FVector2D& B,
	                const FVector2D& C, const FVector2D& D)
	{
		const int32 Base = Vertices.Num();
		const FVector2D Corners[4] = { A, B, C, D };
		for (const FVector2D& P : Corners)
		{
			Vertices.Add(Centre + FVector(P.X, P.Y, 0.f));
			Normals.Add(FVector::UpVector);
			UVs.Add(FVector2D(0.f, 0.f));
			Colors.Add(Tint);
			Tangents.Add(FProcMeshTangent(1.f, 0.f, 0.f));
		}
		Triangles.Add(Base); Triangles.Add(Base + 1); Triangles.Add(Base + 2);
		Triangles.Add(Base); Triangles.Add(Base + 2); Triangles.Add(Base + 3);
	};

	if (bMarkAction)
	{
		// FOUR CORNERS, holding the tile. Not a box: a closed square reads as
		// a lid over whatever is standing there, and the thing being acted on
		// is the point of the mark.
		const float Half = FMath::Lerp(104.f, 82.f, Ease);
		const float Arm = 46.f;
		const float Thick = 11.f;
		for (int32 SX = -1; SX <= 1; SX += 2)
		{
			for (int32 SY = -1; SY <= 1; SY += 2)
			{
				const float X0 = SX * Half, X1 = SX * (Half - Thick);
				const float Y0 = SY * Half, Y1 = SY * (Half - Thick);
				const float XA = SX * (Half - Arm), YA = SY * (Half - Arm);
				// the arm that runs along X, and the one that runs along Y
				Quad(FVector2D(XA, Y0), FVector2D(X0, Y0),
				     FVector2D(X0, Y1), FVector2D(XA, Y1));
				Quad(FVector2D(X0, YA), FVector2D(X0, Y0),
				     FVector2D(X1, Y0), FVector2D(X1, YA));
			}
		}
	}
	else
	{
		// A RING: a place, with nothing held inside it.
		const float Radius = FMath::Lerp(92.f, 64.f, Ease);
		const float Thick = 9.f;
		const int32 Steps = 36;
		for (int32 i = 0; i < Steps; ++i)
		{
			const float A0 = (2.f * PI * i) / Steps;
			const float A1 = (2.f * PI * (i + 1)) / Steps;
			const FVector2D U0(FMath::Cos(A0), FMath::Sin(A0));
			const FVector2D U1(FMath::Cos(A1), FMath::Sin(A1));
			Quad(U0 * (Radius + Thick * 0.5f), U1 * (Radius + Thick * 0.5f),
			     U1 * (Radius - Thick * 0.5f), U0 * (Radius - Thick * 0.5f));
		}
	}

	// ---- CREATED ONCE, THEN UPDATED ----
	//
	// This cleared every section and made a new one on each frame, and a mark
	// that is torn down and rebuilt sixty times a second is a mark the render
	// thread can quite reasonably find nothing of. It never appeared once.
	//
	// The vertex count is fixed for a given shape -- thirty-six quads for the
	// ring, eight for the brackets -- so the only moment a section must be
	// built from scratch is when the mark appears or changes kind. Every other
	// frame moves vertices and colours through the same buffers.
	if (!bMarkBuilt || bMarkBuiltAction != bMarkAction)
	{
		Mark->ClearAllMeshSections();
		Mark->CreateMeshSection_LinearColor(0, Vertices, Triangles, Normals, UVs,
			Colors, Tangents, false);
		bMarkBuilt = true;
		bMarkBuiltAction = bMarkAction;
	}
	else
	{
		Mark->UpdateMeshSection_LinearColor(0, Vertices, Normals, UVs, Colors, Tangents);
	}
	if (const UIntervalLook* Wardrobe = UIntervalLook::Resolve(nullptr))
	{
		if (Wardrobe->MarkMaterial) { Mark->SetMaterial(0, Wardrobe->MarkMaterial); }
	}
}

void AIntervalHand::FreshenStoodOn() const
{
	if (!Bridge)
	{
		StoodOn.Reset();
		StoodOnAt = -1;
		return;
	}
	const FIntervalFrame& Frame = Bridge->GetFrame();
	if (StoodOnAt == Frame.Tick && StoodOn.Num() > 0)
	{
		return;
	}
	StoodOnAt = Frame.Tick;
	StoodOn.Reset();
	for (const TPair<FString, FIntervalEntity>& Pair : Frame.Nodes)
	{
		StoodOn.Add(TileKey(Pair.Value.X, Pair.Value.Y));
	}
	for (const TPair<FString, FIntervalEntity>& Pair : Frame.Mobs)
	{
		StoodOn.Add(TileKey(Pair.Value.X, Pair.Value.Y));
	}
	for (const TPair<FString, FIntervalEntity>& Pair : Frame.Players)
	{
		StoodOn.Add(TileKey(Pair.Value.X, Pair.Value.Y));
	}
	// AND WHAT IS LYING ON THE FLOOR. A dropped axe is a thing with a verb on
	// it, drawn small and low -- so it gains least from this and would be the
	// one omission nobody could explain.
	for (const TPair<FString, FIntervalEntity>& Pair : Frame.Ground)
	{
		StoodOn.Add(TileKey(Pair.Value.X, Pair.Value.Y));
	}
}

// ---------------------------------------------------------------------------
// THE REST OF THE WORLD'S VERBS.
//
// One shape for all of them: name the deed, hand over its integers and its
// words, and say something in the feed if there is no bridge to hand it to.
// NOTHING HERE VETS ANYTHING. The engine's normalizer refuses a malformed
// deed and the world's rules refuse a disallowed one, and both refusals come
// back through the same channel and land in the feed. A window that checked
// first would be a second copy of the rules, and the second copy is always
// the one that is wrong.
void AIntervalHand::Deed(const FString& Verb, const TMap<FString, int32>& Numbers,
	const TMap<FString, FString>& Words)
{
	if (!Bridge || !Bridge->IsConnected())
	{
		Say(FString::Printf(TEXT("no bridge: cannot %s"), *Verb), 0, true);
		return;
	}
	const FIntervalFrame& Frame = Bridge->GetFrame();
	if (!Frame.bHasMe)
	{
		// The same distinction WalkTo makes: a citizen part-way through a
		// birth has not been refused, they have not been asked for.
		Say(FString::Printf(TEXT("not in the world yet: cannot %s"), *Verb),
			Frame.Tick, true);
		Bridge->EnterWorld();
		return;
	}
	Bridge->SendIntent(Verb, Numbers, Words);
}

void AIntervalHand::Plain(const FString& Verb)
{
	Deed(Verb, {}, {});
}

void AIntervalHand::Gather(const FString& NodeId)
{
	Deed(TEXT("gather"), {}, { { TEXT("nodeId"), NodeId } });
}

void AIntervalHand::Attack(const FString& MobId, const FString& Style)
{
	Deed(TEXT("attack"), {}, { { TEXT("mobId"), MobId }, { TEXT("style"), Style } });
}

void AIntervalHand::AttackPerson(const FString& PlayerId, const FString& Style)
{
	// `targetId` is a 64-hex key here, not a node id: the world validates it
	// as T.hex64. Passed through untouched -- a window that trimmed or
	// lower-cased a key would file a deed against nobody.
	Deed(TEXT("attackp"), {}, { { TEXT("targetId"), PlayerId }, { TEXT("style"), Style } });
}

void AIntervalHand::Wield(int32 Slot)
{
	Deed(TEXT("wield"), { { TEXT("slot"), Slot } }, {});
}

void AIntervalHand::Unwield(const FString& Gear)
{
	Deed(TEXT("unwield"), {}, { { TEXT("gear"), Gear } });
}

void AIntervalHand::Buy(const FString& Item)
{
	Deed(TEXT("buy"), {}, { { TEXT("item"), Item } });
}

void AIntervalHand::Drop(int32 Slot)
{
	Deed(TEXT("drop"), { { TEXT("slot"), Slot } }, {});
}

void AIntervalHand::PickUp(const FString& GroundId, bool bConfirm)
{
	// `confirm` is the world's own guard on picking up something that is not
	// yours to take; it is passed through, never decided here.
	// A BOOLEAN, because the world types its fields. Sent as the number 1 this
	// was refused every time -- "field confirm on pickup must be true or
	// false" -- so nothing could ever be picked up.
	if (!Bridge || !Bridge->IsConnected())
	{
		Say(TEXT("no bridge: cannot pickup"), 0, true);
		return;
	}
	if (!Bridge->GetFrame().bHasMe)
	{
		Say(TEXT("not in the world yet: cannot pickup"), Bridge->GetFrame().Tick, true);
		Bridge->EnterWorld();
		return;
	}
	Bridge->SendIntentBool(TEXT("pickup"), {}, { { TEXT("groundId"), GroundId } },
		{ { TEXT("confirm"), bConfirm } });
}

void AIntervalHand::Cast(const FString& Spell)
{
	// ---- ONE SPELL GOES THROUGH `cast`. THE REST ARE VERBS OF THEIR OWN ----
	//
	// The book lists seven lines and this sent all seven as `cast`, which the
	// world refuses six times out of seven: "field spell on cast must be a
	// constitutional spell". Every spell in the book was dead from the book.
	//
	// The world is right and this was wrong. engine.js says so in as many
	// words -- "`cast` now carries one spell, the mending; `still`, `seal`,
	// `unmake` and the barrow four are verbs of their own" -- and each of
	// those verbs takes a TARGET that `cast` has no field for: `still` a mob,
	// `mendp` a citizen, `seal` and `unmake` a pile on the ground, `transmute`
	// a slot in the pack.
	//
	// THIS WINDOW ALREADY SENDS ALL OF THEM CORRECTLY, from the menu on the
	// thing they act on: see `Still`, `MendOther`, `Seal`, `Unmake` and
	// `Transmute` below, and the rows that offer them in `AffordsFor`. So
	// nothing here is missing. What was missing is that the BOOK is a list of
	// what a citizen knows, not a row of buttons, and a spell that needs
	// something to aim at cannot be fired from a list with nothing in it.
	//
	// So the book says what to aim at instead of sending a deed the world will
	// refuse. A refusal that explains itself is worth more than a silent one,
	// and this one was not even silent: it printed the world's own schema
	// error at somebody trying to cast a spell.
	if (Spell == TEXT("mend"))
	{
		Deed(TEXT("cast"), {}, { { TEXT("spell"), Spell } });
		return;
	}
	const int32 Tick = Bridge ? Bridge->GetFrame().Tick : 0;
	if (Spell == TEXT("still"))
	{
		Say(TEXT("still: click what you are fighting"), Tick, true);
	}
	else if (Spell == TEXT("mendp"))
	{
		Say(TEXT("mend another: click the citizen you are mending"), Tick, true);
	}
	else if (Spell == TEXT("seal"))
	{
		Say(TEXT("seal: click the pack on the ground"), Tick, true);
	}
	else if (Spell == TEXT("unmake"))
	{
		Say(TEXT("unmake: click the thing you are taking apart"), Tick, true);
	}
	else if (Spell == TEXT("transmute"))
	{
		Say(TEXT("transmute: click the thing in your pack"), Tick, true);
	}
	else
	{
		Say(FString::Printf(TEXT("%s is not cast from the book"), *Spell), Tick, true);
	}
}

void AIntervalHand::Haul(const FString& NodeId)
{
	Deed(TEXT("haul"), {}, { { TEXT("nodeId"), NodeId } });
}

void AIntervalHand::Unload(const FString& NodeId)
{
	Deed(TEXT("unload"), {}, { { TEXT("nodeId"), NodeId } });
}

void AIntervalHand::Smith(const FString& Recipe)
{
	Deed(TEXT("smith"), {}, { { TEXT("recipe"), Recipe } });
}

void AIntervalHand::ClaimName(const FString& Name)
{
	Deed(TEXT("claim_name"), {}, { { TEXT("name"), Name } });
}

void AIntervalHand::Follow(const FString& TargetId)
{
	Deed(TEXT("follow"), {}, { { TEXT("targetId"), TargetId } });
}

// ---- THE SPELLBOOK ----
void AIntervalHand::Still(const FString& Target)
{
	Deed(TEXT("still"), {}, { { TEXT("target"), Target } });
}

void AIntervalHand::MendOther(const FString& Target)
{
	Deed(TEXT("mendp"), {}, { { TEXT("target"), Target } });
}

void AIntervalHand::Seal(const FString& GroundId)
{
	Deed(TEXT("seal"), {}, { { TEXT("groundId"), GroundId } });
}

void AIntervalHand::Unmake(const FString& GroundId)
{
	Deed(TEXT("unmake"), {}, { { TEXT("groundId"), GroundId } });
}

void AIntervalHand::Transmute(int32 Slot)
{
	Deed(TEXT("transmute"), { { TEXT("slot"), Slot } }, {});
}

void AIntervalHand::Waking(const FString& TargetId)
{
	Deed(TEXT("waking"), {}, { { TEXT("targetId"), TargetId } });
}

void AIntervalHand::Rot(const FString& TargetId)
{
	Deed(TEXT("rot"), {}, { { TEXT("targetId"), TargetId } });
}

void AIntervalHand::Taking(const FString& TargetId)
{
	Deed(TEXT("taking"), {}, { { TEXT("targetId"), TargetId } });
}

void AIntervalHand::Withering(const FString& TargetId)
{
	Deed(TEXT("withering"), {}, { { TEXT("targetId"), TargetId } });
}

void AIntervalHand::TurnBook()
{
	Plain(TEXT("turn"));
}

void AIntervalHand::Release()
{
	Plain(TEXT("release"));
}

void AIntervalHand::Deliver(int32 Slot)
{
	Deed(TEXT("deliver"), { { TEXT("slot"), Slot } }, {});
}

void AIntervalHand::Consign(const TArray<int32>& Slots)
{
	// A LIST, WHICH THE INTEGER MAP CANNOT CARRY. `consign` wants an array of
	// ascending unique slot indices and SendIntent takes scalars, so this one
	// deed builds its own JSON. Sorted and de-duplicated here because the
	// engine requires ascending and unique -- that is the CANONICAL FORM of
	// the request, not a rule about the world, and getting it wrong means two
	// windows asking the same thing sign different bytes.
	if (!Bridge || !Bridge->IsConnected() || Slots.Num() == 0)
	{
		Say(TEXT("nothing to consign"), 0, true);
		return;
	}
	TArray<int32> Tidy = Slots;
	Tidy.Sort();
	for (int32 i = Tidy.Num() - 1; i > 0; --i)
	{
		if (Tidy[i] == Tidy[i - 1]) { Tidy.RemoveAt(i); }
	}
	Bridge->SendIntentList(TEXT("consign"), TEXT("slots"), Tidy);
}

// ---------------------------------------------------------------------------
// THE THIRTEEN THAT WERE STILL MISSING. See the note over their declarations.
//
// Name for name and type for type against the engine's INPUT_SCHEMAS, like
// every verb above them. Nothing here vets anything: a market a citizen may
// not raise is refused by the world, and that refusal comes back through the
// feed like any other.

void AIntervalHand::RaiseMarket()
{
	Plain(TEXT("raise_market"));
}

void AIntervalHand::StockMarket(int32 Slot)
{
	Deed(TEXT("stock_market"), { { TEXT("slot"), Slot } }, {});
}

void AIntervalHand::PriceMarket(int32 Ask)
{
	Deed(TEXT("price_market"), { { TEXT("ask"), Ask } }, {});
}

void AIntervalHand::TakeMarket()
{
	Plain(TEXT("take_market"));
}

void AIntervalHand::DismantleMarket()
{
	Plain(TEXT("dismantle_market"));
}

void AIntervalHand::AcceptTrade(const FString& FromPlayerId)
{
	// `from` is a 64-hex key, validated as T.hex64. Passed through untouched,
	// for the same reason `attackp` passes its target through untouched: a
	// window that trimmed or lower-cased a key would accept a trade from
	// nobody.
	Deed(TEXT("accept_trade"), {}, { { TEXT("from"), FromPlayerId } });
}

void AIntervalHand::CancelTrade()
{
	Plain(TEXT("cancel_trade"));
}

void AIntervalHand::BuildBrewpot()
{
	Plain(TEXT("build_brewpot"));
}

void AIntervalHand::DepositAll()
{
	Plain(TEXT("deposit_all"));
}

void AIntervalHand::ReadChart(int32 Slot)
{
	Deed(TEXT("read_chart"), { { TEXT("slot"), Slot } }, {});
}

void AIntervalHand::Recall(const FString& ToId)
{
	Deed(TEXT("recall"), {}, { { TEXT("to"), ToId } });
}

void AIntervalHand::SetLook(int32 Look)
{
	Deed(TEXT("set_look"), { { TEXT("look"), Look } }, {});
}

void AIntervalHand::OfferTrade(const FString& ToPlayerId, const TArray<int32>& GiveSlots,
	const FString& WantItem, int32 WantGold)
{
	// FOUR FIELDS OF THREE SHAPES, so this one builds its own request exactly
	// as `consign` does -- a key, a list of slots, an item that may be null,
	// and a count of coin.
	//
	// BOTH DEMAND FIELDS GO, ALWAYS. The engine says it plainly: "the canonical
	// item trade carries wantGold: 0; the canonical gold trade carries
	// wantItem: null. Omission is not a representation." An empty `WantItem`
	// here means coin is wanted, and it is sent as a JSON null rather than left
	// out or sent as an empty string.
	if (!Bridge || !Bridge->IsConnected() || GiveSlots.Num() == 0)
	{
		Say(TEXT("nothing to offer"), 0, true);
		return;
	}
	TArray<int32> Tidy = GiveSlots;
	Tidy.Sort();
	for (int32 i = Tidy.Num() - 1; i > 0; --i)
	{
		if (Tidy[i] == Tidy[i - 1]) { Tidy.RemoveAt(i); }
	}
	Bridge->SendOfferTrade(ToPlayerId, Tidy, WantItem, WantGold);
}

bool AIntervalHand::WalkRoute(int32 TileX, int32 TileY)
{
	Route.Reset();
	if (RouteGoal != FIntPoint(TileX, TileY))
	{
		Rethinks = 0;          // a new destination: a fresh allowance
	}
	if (!Bridge || !Bridge->IsConnected())
	{
		return WalkTo(TileX, TileY);
	}
	const FIntervalFrame& Frame = Bridge->GetFrame();
	if (!Frame.bHasMe)
	{
		return WalkTo(TileX, TileY);
	}
	const FIntPoint From(Frame.Me.X, Frame.Me.Y);
	const FIntPoint To(TileX, TileY);
	if (From == To)
	{
		return false;
	}

	// WHAT IS SHUT. A node stands on its tile and nothing walks through it --
	// which is the same rule the walk-beside code uses, and is the whole of
	// what this window knows about the ground. The DESTINATION is left open
	// even if something stands on it, because a click on a stall means "go to
	// the stall" and the leg that ends beside it is close enough.
	TSet<FIntPoint> Shut;
	Shut.Reserve(Frame.Nodes.Num() + Frame.Mobs.Num());
	for (const TPair<FString, FIntervalEntity>& Node : Frame.Nodes)
	{
		Shut.Add(FIntPoint(Node.Value.X, Node.Value.Y));
	}
	// ---- AND A LIVING BEAST, WHICH THE WORLD BARS AND THIS DID NOT ----
	//
	// `canStep` refuses a step onto a tile a living mob is standing on, in as
	// many words: "a living beast holds its tile -- you do not walk THROUGH a
	// troll, you deal with it". This window planned straight through them.
	//
	// What that costs is worse than one refused step. The leg stops dead, the
	// tile it was trying to enter is written into `Learned` as a wall, the
	// route is thought again -- and the beast has usually moved by then, so the
	// wall that was learned is a lie about empty ground that then has to be
	// forgotten. A wolf standing on a lane could poison a stretch of road for a
	// hundred intervals. This is most of what walking in this world feels like
	// going wrong.
	//
	// A DEAD one does not bar anything: the engine checks `health > 0` and so
	// does this, off the same field the citizens' own drawing reads.
	for (const TPair<FString, FIntervalEntity>& Beast : Frame.Mobs)
	{
		bool bAlive = true;
		if (const FString* Hp = Beast.Value.Fields.Find(TEXT("health")))
		{
			bAlive = FCString::Atof(**Hp) > 0.f;
		}
		if (bAlive)
		{
			Shut.Add(FIntPoint(Beast.Value.X, Beast.Value.Y));
		}
	}
	Shut.Remove(To);

	// AND WHAT WALKING HAS TAUGHT IT.
	//
	// The window's picture of the world is the frame's nodes and the chunks it
	// has drawn, and neither is complete: a route fifty tiles long is planned
	// partly through ground nothing has told it about. So when a leg stops
	// dead, the tile it was trying to step onto is remembered as shut and the
	// route is thought again. That is how a person learns a landscape -- by
	// walking into it -- and it means the second attempt at a journey is
	// always better than the first.
	// WHAT HAS BEEN LEARNED, MINUS WHAT HAS BEEN FORGOTTEN. A tile refused a
	// hundred intervals ago is not evidence about now.
	{
		const int64 Now_ = Frame.Tick;
		for (auto It = Learned.CreateIterator(); It; ++It)
		{
			if (Now_ - It.Value() > ForgetAfter) { It.RemoveCurrent(); }
			else { Shut.Add(It.Key()); }
		}
	}
	Shut.Remove(To);

	// AND THE WATER, which no node list mentions and which stops a walk as
	// surely as a wall. The chunks the window has drawn reach much further
	// than the frame's nodes do, so this is the larger half of what it knows.
	AIntervalGround* Land = nullptr;
	TSet<uint8> Wet;
	{
		TActorIterator<AIntervalGround> It(GetWorld());
		Land = It ? *It : nullptr;
	}
	if (Land)
	{
		const TArray<FString>& Names = Bridge->GetTileNames();
		for (int32 i = 0; i < Names.Num(); ++i)
		{
			const FString& Word = Names[i];
			// THE THREE THAT CANNOT BE WALKED, BY NAME AND NOT BY GUESSWORK.
			//
			// The world's terrains are a short list the bridge sends in
			// `hello`, and exactly three of them stop a walk: `sea`, `river`
			// and `mountain` -- the last being the spine the map draws as a
			// ridge. Everything else, including `crags` and `scree`, is rough
			// ground a citizen crosses.
			//
			// An earlier version matched SUBSTRINGS -- "crag", "ridge",
			// "cliff" -- which was wrong twice over. Neither "ridge" nor
			// "cliff" is a word this world uses, so the mountain stayed open
			// and every route went straight at it; and "crag" matched `crags`,
			// which is the ordinary ground of a whole quarter of the island,
			// so the router decided there was nowhere to walk at all and fell
			// back to walking blindly. A name is a name: compared whole.
			//
			// `bridge` and `causey` are deliberately NOT here. They are how
			// the water is crossed, and the whole point of them is that they
			// are walkable where the river is not.
			if (Word == TEXT("sea") || Word == TEXT("river")
				|| Word == TEXT("mountain"))
			{
				Wet.Add(static_cast<uint8>(i));
			}
		}
	}

	// A* over the square the map shows, which is as far as a map click can
	// ask for anyway. Bounded, so a route that cannot be found costs a known
	// amount of work rather than searching the island.
	const int32 Span = 60;
	const FIntPoint Low(FMath::Min(From.X, To.X) - Span, FMath::Min(From.Y, To.Y) - Span);
	const FIntPoint High(FMath::Max(From.X, To.X) + Span, FMath::Max(From.Y, To.Y) + Span);
	auto Heuristic = [&To](const FIntPoint& P)
	{
		// Chebyshev, because a step may be diagonal and the world says so.
		return FMath::Max(FMath::Abs(P.X - To.X), FMath::Abs(P.Y - To.Y));
	};

	TMap<FIntPoint, FIntPoint> Came;
	TMap<FIntPoint, int32> Cost;
	TArray<TPair<int32, FIntPoint>> Open;
	Cost.Add(From, 0);
	Open.Add({ Heuristic(From), From });
	bool bFound = false;
	int32 Looked = 0;
	// ---- A HEAP, AND THE OLD NOTE HERE WAS WRONG ABOUT WHY NOT ----
	//
	// It said: "A heap would be faster and this is a few thousand tiles once a
	// click, which is not worth the machinery." The budget on the line below
	// is a HUNDRED AND SIXTY THOUSAND, and a linear scan for the cheapest is
	// O(n) on every pop, so the search is quadratic in how far it looks. A few
	// thousand tiles is fine; a route the length of the island, or any route
	// that has to search round a lake before it finds the way, is tens of
	// millions of comparisons inside one click. That is felt as the window
	// stopping, and it is felt worst exactly when the walk is hardest, which
	// is the opposite of what anybody wants.
	//
	// `Algo::Heapify` and friends are in the engine already, so the machinery
	// is one predicate and three calls. Pops go from O(n) to O(log n).
	auto Cheaper = [](const TPair<int32, FIntPoint>& A,
		const TPair<int32, FIntPoint>& B) { return A.Key < B.Key; };
	Open.Heapify(Cheaper);
	while (Open.Num() > 0 && Looked < 160000)
	{
		TPair<int32, FIntPoint> Top;
		Open.HeapPop(Top, Cheaper, EAllowShrinking::No);
		const FIntPoint Here = Top.Value;
		++Looked;
		if (Here == To) { bFound = true; break; }
		const int32 Far = Cost[Here] + 1;
		for (int32 dx = -1; dx <= 1; ++dx)
		{
			for (int32 dy = -1; dy <= 1; ++dy)
			{
				if (!dx && !dy) { continue; }
				const FIntPoint Next(Here.X + dx, Here.Y + dy);
				if (Next.X < Low.X || Next.X > High.X
					|| Next.Y < Low.Y || Next.Y > High.Y) { continue; }
				if (Shut.Contains(Next)) { continue; }
				if (Land && Next != To && Wet.Contains(Land->CodeAtTile(Next.X, Next.Y)))
				{
					continue;
				}
				const int32* Had = Cost.Find(Next);
				if (Had && *Had <= Far) { continue; }
				Cost.Add(Next, Far);
				Came.Add(Next, Here);
				Open.HeapPush({ Far + Heuristic(Next), Next }, Cheaper);
			}
		}
	}
	if (!bFound)
	{
		// ---- SAY SO, AND THEN TRY HARDER BEFORE SAYING IT ----
		//
		// Walking blindly at an unreachable place is what this did, and it is
		// the worst of both: the world refuses the step, the refusal is
		// written down as a wall, and the wall makes the NEXT search fail too.
		// That is the loop that stranded a citizen on a beach.
		//
		// So a failed search first drops everything it thinks it has learned
		// -- the most likely reason a route cannot be found on open country is
		// that the memory is wrong -- and searches once more. Only if that
		// also fails is the place genuinely out of reach, and then it is said
		// plainly rather than mimed by standing still.
		if (Learned.Num() > 0 && !bSecondThoughts)
		{
			Learned.Reset();
			TGuardValue<bool> Once(bSecondThoughts, true);
			return WalkRoute(TileX, TileY);
		}
		Say(FString::Printf(TEXT("there is no way to %d, %d from here"), TileX, TileY),
			Frame.Tick, true);
		Route.Reset();
		RouteGoal = FIntPoint::ZeroValue;
		return false;
	}

	// UNWIND, AND KEEP ONLY THE CORNERS. The world takes a direction and a
	// count, so a straight run of forty is one deed; a corner is where the
	// direction changes and is the only place a new one is needed.
	TArray<FIntPoint> Back;
	for (FIntPoint At = To; At != From; At = Came[At]) { Back.Add(At); }
	Algo::Reverse(Back);
	FIntPoint Was = From;
	FIntPoint Way(0, 0);
	for (int32 i = 0; i < Back.Num(); ++i)
	{
		const FIntPoint Step(FMath::Clamp(Back[i].X - Was.X, -1, 1),
			FMath::Clamp(Back[i].Y - Was.Y, -1, 1));
		if (i > 0 && Step != Way)
		{
			Route.Add(Was);
		}
		Way = Step;
		Was = Back[i];
	}
	Route.Add(To);

	RouteGoal = To;
	UE_LOG(LogIntervalHand, Log,
		TEXT("route to %d,%d in %d steps, %d corners (%d tiles learned shut)"),
		TileX, TileY, Back.Num(), Route.Num(), Learned.Num());
	const FIntPoint First = Route[0];
	Route.RemoveAt(0);
	return WalkTo(First.X, First.Y);
}

bool AIntervalHand::WalkTo(int32 TileX, int32 TileY)
{
	if (!Bridge || !Bridge->IsConnected())
	{
		Say(TEXT("no bridge: nothing to walk with"), 0, true);
		return false;
	}
	// THE RING, HERE, because every path that moves a citizen comes through
	// this one function -- so no walk is sent without its mark.
	//
	// AND BEFORE THE WORLD HAS AGREED, deliberately. It sits above the checks
	// below, so a citizen who is not in the world yet still gets a mark and
	// then a refusal in the feed. That is the right way round: the mark
	// answers the HAND, and the whole reason it exists is that the world's own
	// answer is up to an interval away. A mark that waited for agreement would
	// be silent for exactly the second it is needed.
	ShowMark(TileX, TileY, false);

	const FIntervalFrame& Frame = Bridge->GetFrame();
	if (!Frame.bHasMe)
	{
		// Not a refusal from the world -- the world has not been asked. Said
		// out loud anyway, because a click that does nothing and says nothing
		// is the exact failure this feed exists to prevent. And say WHICH
		// nothing: a citizen part-way through a birth is not the same as one
		// who has never knocked, and "nothing happened" covers both.
		if (Frame.BirthState == TEXT("waiting"))
		{
			Say(FString::Printf(TEXT("not in the world yet: waiting to be born (%d/%d)"),
				Frame.BirthWaited, Frame.BirthRipeAt), Frame.Tick, true);
		}
		else if (Frame.BirthState == TEXT("ripe"))
		{
			Say(TEXT("the wait is up: crossing into the world"), Frame.Tick, true);
			Bridge->EnterWorld();
		}
		else
		{
			Say(TEXT("not in the world yet: nobody has knocked"), Frame.Tick, true);
			Bridge->EnterWorld();
		}
		return false;
	}

	// THE TOLD TILE. Frame.Me is what the last interval said, not what is
	// being drawn. These differ for most of every second and only one of them
	// is a fact.
	const int32 FromX = Frame.Me.X;
	const int32 FromY = Frame.Me.Y;

	const int32 DeltaX = TileX - FromX;
	const int32 DeltaY = TileY - FromY;
	if (DeltaX == 0 && DeltaY == 0)
	{
		return false;
	}

	// THE WALK FOLLOWS THE LINE, WHICH IT DID NOT USED TO.
	//
	// This filed ONE run: the diagonal direction, for `max(|dx|,|dy|)` steps.
	// For anything not already on one of the eight rays that is wrong twice.
	// Asked to go one west and five north it walked five north-WEST -- four
	// tiles past the target on the other axis -- and then had to walk four
	// back east to fix it. What that looks like on screen is a citizen setting
	// off at a slant, stopping, and sidling: "it walks 3 ticks towards it then
	// 2 ticks to the side. Like kind of a sideways L, same pattern every
	// single time."
	//
	// The world takes a direction and a count, so a run can only ever be a
	// straight line or a true diagonal. A straight-LOOKING path is therefore
	// made of several runs, interleaved the way Bresenham interleaves them --
	// diagonal steps spread evenly through the straight ones -- rather than
	// all the diagonal first and the remainder after. This files the leading
	// run of that plan; Tick files the next when this one finishes, working
	// from wherever the citizen actually ended up, so a deflection round a
	// wall re-plans instead of compounding.
	const int32 Across = FMath::Abs(DeltaX);
	const int32 Up = FMath::Abs(DeltaY);
	const int32 SignX = FMath::Clamp(DeltaX, -1, 1);
	const int32 SignY = FMath::Clamp(DeltaY, -1, 1);

	int32 StepX = SignX;
	int32 StepY = SignY;
	int32 Steps = 0;
	if (Across == 0 || Up == 0 || Across == Up)
	{
		// Already on one of the eight rays: one run does the whole thing.
		Steps = FMath::Max(Across, Up);
	}
	else
	{
		// The long axis moves every step; the short one moves on the steps
		// where the error term says the true line has crossed into the next
		// row. The leading run is however many steps share the first kind.
		const bool bWideX = Across > Up;
		const int32 Major = bWideX ? Across : Up;
		const int32 Minor = bWideX ? Up : Across;
		int32 Error = Major / 2;
		const bool bFirstIsDiagonal = (Error + Minor) >= Major;
		for (int32 i = 0; i < Major; ++i)
		{
			Error += Minor;
			const bool bDiagonal = Error >= Major;
			if (bDiagonal)
			{
				Error -= Major;
			}
			if (bDiagonal != bFirstIsDiagonal)
			{
				break;
			}
			++Steps;
		}
		if (!bFirstIsDiagonal)
		{
			StepX = bWideX ? SignX : 0;
			StepY = bWideX ? 0 : SignY;
		}
	}
	Steps = FMath::Clamp(Steps, 1, FMath::Max(MaxSteps, 1));

	TMap<FString, int32> Numbers;
	Numbers.Add(TEXT("dx"), StepX);
	Numbers.Add(TEXT("dy"), StepY);
	Numbers.Add(TEXT("steps"), Steps);

	// The verb is the world's own. This window does not stamp the tick, does
	// not sign, and does not know whether the walk is legal.
	Bridge->SendIntent(TEXT("walk"), Numbers, TMap<FString, FString>());

	// REMEMBER WHERE THE CLICK ASKED FOR. One run reaches one of the eight
	// rays out of here; anywhere else needs the straight remainder afterwards,
	// which Tick files when this run has finished. See `Bound`.
	Bound = FIntPoint(TileX, TileY);
	bBound = true;
	Legs = 1;
	LastSeenAt = FIntPoint(Frame.Me.X, Frame.Me.Y);
	FiledAt = Frame.Tick;
	FiledInput = LastInputOf(Frame);

	UE_LOG(LogIntervalHand, Log, TEXT("walk %d,%d x%d from tile %d,%d toward %d,%d"),
		StepX, StepY, Steps, FromX, FromY, TileX, TileY);
	return true;
}

void AIntervalHand::Enter()
{
	if (Bridge)
	{
		Bridge->EnterWorld();
	}
}


// ---------------------------------------------------------------------------
// EVERY OTHER VERB THE WORLD HAS.
//
// The window could file twenty-six of the world's sixty-two citizen intents.
// The rest were not refused by the world -- they were never sent, which is a
// different thing and a worse one: a citizen could not swear a calling, drink
// from a well, light a fire, fletch an arrow, sail a ferry or found a town,
// and nothing anywhere said why. `drink` was the cautionary one: wells restore
// a citizen to FULL, every other window grew a drink button the day wells
// started working, and because this one could not send the word a hurt citizen
// looked unhealable and whole journeys were planned around a limit that did
// not exist.
//
// These are generated from the world's own INPUT_SCHEMAS -- name for name and
// type for type -- rather than typed out from reading, because a hand copy of
// a table is the single most reliable source of bugs in this project's
// history. Each is the same two lines: name the verb, hand over the fields.
// The window still decides nothing about whether a deed is legal.

void AIntervalHand::Archive(const FString& Subject)
{
	Deed(TEXT("archive"), {}, { { TEXT("subject"), Subject } });
}

void AIntervalHand::Befriend(const FString& TargetId)
{
	Deed(TEXT("befriend"), {}, { { TEXT("targetId"), TargetId } });
}

void AIntervalHand::Char(const FString& NodeId)
{
	Deed(TEXT("char"), {}, { { TEXT("nodeId"), NodeId } });
}

void AIntervalHand::Charter(int32 Slot)
{
	Deed(TEXT("charter"), { { TEXT("slot"), Slot } }, {});
}

void AIntervalHand::Dedicate(const FString& NodeId, int32 Pay)
{
	Deed(TEXT("dedicate"), { { TEXT("pay"), Pay } }, { { TEXT("nodeId"), NodeId } });
}

void AIntervalHand::Drink()
{
	Deed(TEXT("drink"), {}, {});
}

void AIntervalHand::Fletch(int32 Slot, const FString& Make)
{
	Deed(TEXT("fletch"), { { TEXT("slot"), Slot } }, { { TEXT("make"), Make } });
}

void AIntervalHand::Found(int32 X, int32 Y)
{
	Deed(TEXT("found"), { { TEXT("x"), X }, { TEXT("y"), Y } }, {});
}

void AIntervalHand::Grave(const FString& NodeId, const FString& Target)
{
	Deed(TEXT("grave"), {}, { { TEXT("nodeId"), NodeId }, { TEXT("target"), Target } });
}

void AIntervalHand::Grind(int32 Slot)
{
	Deed(TEXT("grind"), { { TEXT("slot"), Slot } }, {});
}

void AIntervalHand::Kindle()
{
	Deed(TEXT("kindle"), {}, {});
}

void AIntervalHand::Lay(const FString& NodeId, int32 N)
{
	Deed(TEXT("lay"), { { TEXT("n"), N } }, { { TEXT("nodeId"), NodeId } });
}

void AIntervalHand::Lift(const FString& NodeId)
{
	Deed(TEXT("lift"), {}, { { TEXT("nodeId"), NodeId } });
}

void AIntervalHand::Light(int32 Slot)
{
	Deed(TEXT("light"), { { TEXT("slot"), Slot } }, {});
}

void AIntervalHand::Move(int32 Dx, int32 Dy)
{
	Deed(TEXT("move"), { { TEXT("dx"), Dx }, { TEXT("dy"), Dy } }, {});
}

void AIntervalHand::Nock(int32 Slot)
{
	Deed(TEXT("nock"), { { TEXT("slot"), Slot } }, {});
}

void AIntervalHand::Offer(int32 Slot)
{
	Deed(TEXT("offer"), { { TEXT("slot"), Slot } }, {});
}

void AIntervalHand::Pay()
{
	Deed(TEXT("pay"), {}, {});
}


void AIntervalHand::Restore()
{
	Deed(TEXT("restore"), {}, {});
}

void AIntervalHand::Rifle(const FString& NodeId, const FString& Item)
{
	Deed(TEXT("rifle"), {}, { { TEXT("nodeId"), NodeId }, { TEXT("item"), Item } });
}

void AIntervalHand::Sail()
{
	Deed(TEXT("sail"), {}, {});
}

void AIntervalHand::Sapling(const FString& NodeId)
{
	Deed(TEXT("sapling"), {}, { { TEXT("nodeId"), NodeId } });
}

void AIntervalHand::Setbuck()
{
	Deed(TEXT("setbuck"), {}, {});
}

void AIntervalHand::Sound()
{
	Deed(TEXT("sound"), {}, {});
}

void AIntervalHand::Gambit(const FString& TargetId, const FString& Style)
{
	Deed(TEXT("gambit"), {}, { { TEXT("targetId"), TargetId }, { TEXT("style"), Style } });
}

void AIntervalHand::Stamp(int32 Slot)
{
	Deed(TEXT("stamp"), { { TEXT("slot"), Slot } }, {});
}

void AIntervalHand::Stint(int32 N)
{
	Deed(TEXT("stint"), { { TEXT("n"), N } }, {});
}

void AIntervalHand::Survey()
{
	Deed(TEXT("survey"), {}, {});
}

void AIntervalHand::Swear(const FString& Calling)
{
	// A CALLING IS NAMED, not inferred. The schema validates it with a function
	// rather than a type -- it must be a key of SWORN -- which is why the first
	// sweep read this as taking nothing and generated a swearing that could only
	// ever be refused.
	Deed(TEXT("swear"), {}, { { TEXT("calling"), Calling } });
}

void AIntervalHand::Turn()
{
	Deed(TEXT("turn"), {}, {});
}

void AIntervalHand::Unfollow()
{
	Deed(TEXT("unfollow"), {}, {});
}

void AIntervalHand::Unfriend(const FString& TargetId)
{
	Deed(TEXT("unfriend"), {}, { { TEXT("targetId"), TargetId } });
}

void AIntervalHand::Withdraw(const FString& Item, int32 Qty)
{
	Deed(TEXT("withdraw"), { { TEXT("qty"), Qty } }, { { TEXT("item"), Item } });
}


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

void AIntervalHand::Brew(const FString& NodeD, int32 Slot)
{
	Deed(TEXT("brew"), { { TEXT("slot"), Slot } }, { { TEXT("nodeId"), NodeD } });
}

void AIntervalHand::Bury(int32 Slot)
{
	Deed(TEXT("bury"), { { TEXT("slot"), Slot } }, {});
}

void AIntervalHand::Collect(const FString& NodeD)
{
	Deed(TEXT("collect"), {}, { { TEXT("nodeId"), NodeD } });
}

void AIntervalHand::Cook(int32 Slot)
{
	Deed(TEXT("cook"), { { TEXT("slot"), Slot } }, {});
}

void AIntervalHand::Deposit(int32 Slot)
{
	Deed(TEXT("deposit"), { { TEXT("slot"), Slot } }, {});
}

void AIntervalHand::Dismantle(const FString& NodeD)
{
	Deed(TEXT("dismantle"), {}, { { TEXT("nodeId"), NodeD } });
}

void AIntervalHand::Eat(int32 Slot)
{
	Deed(TEXT("eat"), { { TEXT("slot"), Slot } }, {});
}

void AIntervalHand::Harvest(const FString& NodeD)
{
	Deed(TEXT("harvest"), {}, { { TEXT("nodeId"), NodeD } });
}

void AIntervalHand::Invoke()
{
	Deed(TEXT("invoke"), {}, {});
}

void AIntervalHand::Plant(int32 Slot)
{
	Deed(TEXT("plant"), { { TEXT("slot"), Slot } }, {});
}

void AIntervalHand::Saw()
{
	Deed(TEXT("saw"), {}, {});
}

void AIntervalHand::Smelt(const FString& Recipe)
{
	Deed(TEXT("smelt"), {}, { { TEXT("recipe"), Recipe } });
}

void AIntervalHand::Stoke(const FString& NodeD, int32 Slot)
{
	Deed(TEXT("stoke"), { { TEXT("slot"), Slot } }, { { TEXT("nodeId"), NodeD } });
}

void AIntervalHand::Stop()
{
	Deed(TEXT("stop"), {}, {});
}

void AIntervalHand::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	// On the FRAME, not the interval: a mark that settled once a second would
	// be a stutter in the one place the window is answering a human hand.
	DriveMark();

	// ---- THE SECOND LEG OF A WALK ----
	//
	// One `walk` is one straight run, so a click that is not on a ray out of
	// where you stand needs the remainder afterwards. Filed only when the
	// first run has FINISHED -- the world says so, in `action` -- and only if
	// the citizen actually moved, so walking into a wall stops rather than
	// re-filing the same refused deed for ever.
	// ---- §7dn/§7dq: WHAT THE GROUND AHEAD WILL ASK ----
	//
	// Two tiles on the island refuse a citizen and the GROUND does the
	// refusing, so the engine does not move them and nothing is wrong: no
	// refusal, no error, no message. In the window that reads as an invisible
	// wall, which is the one thing a place built on preparation must not look
	// like.
	//
	// Said once on arrival rather than every interval, because the condition
	// holds for as long as you stand there and `Say` would be dropping a
	// repeat anyway. Said again if it CHANGES while you stand there, which is
	// the interesting case: a torch burning out in front of the Smother's
	// mouth is the item doing exactly what it is for, and the citizen should
	// be told the door just shut.
	if (Bridge && Bridge->IsConnected())
	{
		const FIntervalFrame& Gate = Bridge->GetFrame();
		if (Gate.ThresholdSays != LastThresholdSaid)
		{
			LastThresholdSaid = Gate.ThresholdSays;
			if (!Gate.ThresholdSays.IsEmpty())
			{
				Say(Gate.ThresholdSays, Gate.Tick, !Gate.bThresholdOpen);
			}
		}
	}

	if (bBound && Bridge && Bridge->IsConnected())
	{
		const FIntervalFrame& Now = Bridge->GetFrame();
		if (!Now.bHasMe)
		{
			bBound = false;
		}
		// NOT UNTIL THE WORLD HAS ANSWERED -- and being asked is not being
		// answered. See `FiledInput`: a deed takes two or three intervals to
		// be signed, carried and applied, and judging the frame after filing
		// reads every walk as blocked.
		else if (LastInputOf(Now) <= FiledInput)
		{
			// Still in flight, OR declined in silence. Only time tells them
			// apart, and this is the waiting.
			if (Now.Tick - FiledAt >= AnswerPatience)
			{
				// THE WORLD WOULD NOT TAKE IT. Said plainly, because the
				// alternative is a citizen clicking at a window that has
				// stopped answering and no way to tell that from a crash.
				// Why it was declined is the world's business and is not
				// guessed at here.
				Say(TEXT("the world would not take that"), Now.Tick, true);
				bBound = false;
			}
		}
		else
		{
			// Accepted. Now the citizen's position means something.
			const FIntPoint At(Now.Me.X, Now.Me.Y);
			const FString* Doing = Now.Me.Fields.Find(TEXT("action"));
			const bool bStillWalking = Doing && Doing->Contains(TEXT("walk"));
			// CLOSE ENOUGH IS ARRIVED, AT A CORNER.
			//
			// A route through a town turns forty corners a tile apart, and
			// the world walks in whole tiles from wherever the citizen
			// actually is -- so landing exactly on every one of them is not
			// something to rely on. Demanding it meant a near miss was read
			// as "the walk stopped", which learned a wall that was not there
			// and re-planned from a picture of the world that got worse every
			// time. The last corner, which is where the player asked to go,
			// still has to be reached exactly.
			const int32 Off = FMath::Max(FMath::Abs(At.X - Bound.X),
				FMath::Abs(At.Y - Bound.Y));
			// AND NOT BEFORE THE WALK HAS FINISHED.
			//
			// Corners in a town are a tile apart, so "within one tile" is true
			// of the NEXT corner as well as this one -- and the hand turned
			// three of them a second, filing a new walk over the top of each
			// before the world had taken a single step. The citizen stood
			// still while the window worked furiously. A near miss only counts
			// once the world says the walking is over; landing exactly on the
			// corner still counts at once, which is the common case.
			if (At == Bound || (Route.Num() > 0 && Off <= 1 && !bStillWalking))
			{
				// ARRIVED -- at this corner. If there are more, turn it.
				if (Route.Num() > 0)
				{
					const FIntPoint Next = Route[0];
					Route.RemoveAt(0);
					bBound = false;
					WalkTo(Next.X, Next.Y);
				}
				else
				{
					bBound = false;
					RouteGoal = FIntPoint::ZeroValue;
					Rethinks = 0;
				}
			}
			// STOPPED IS NOT ALWAYS "NOT WALKING".
			//
			// A blocked leg was noticed only when the world stopped calling
			// the citizen's action a walk. Against the ridge it never does:
			// the deed is accepted, the action stays `walk`, and the citizen
			// stands still for ever while the window waits politely for them
			// to finish. Counting the intervals in which a bound citizen has
			// not moved catches it whatever the world calls what they are
			// doing.
			// AN `ELSE`, AND THE WHOLE JOURNEY TURNED ON IT.
			//
			// This ran unconditionally after the arrival test above, so on the
			// very tick a corner was reached and the NEXT leg filed, the
			// stall logic ran on the same frame with the old position, decided
			// the citizen had not moved, and filed something else over the top
			// of the leg just sent. A routed journey therefore advanced one
			// tile and stopped, every time, for any route with a corner in
			// it -- which is every route through a town. It looked like the
			// world refusing to move anybody.
			else
			{
			StillFor = (At == LastSeenAt) ? StillFor + 1 : 0;
			if (bStillWalking && StillFor < 4)
			{
				LastSeenAt = At;
			}
			else if (!bStillWalking || StillFor >= 4)
			{
				StillFor = 0;
				// MANY LEGS ARE NORMAL NOW. A straight-looking walk is made of
				// interleaved runs -- see WalkTo -- so a dozen legs is an
				// ordinary diagonal journey and not a sign of anything wrong.
				// Being STUCK is still one thing only: the world took the deed
				// and the citizen did not move.
				if (At == LastSeenAt || Legs >= 512)
				{
					// The world took the deed and the citizen still did not
					// move: that is a wall, and now we may say so honestly.
					bBound = false;
					// REMEMBER WHAT STOPPED US. The step that was refused was
					// toward `Bound`, so the tile one pace that way is the one
					// that is shut -- not `Bound` itself, which may be forty
					// tiles off and perfectly walkable.
					// ONLY FROM A REAL STANDSTILL. A citizen that moved and
					// then stopped short has not found a wall; it has found
					// the end of what the world would do this interval.
					if (At == LastSeenAt)
					{
						const FIntPoint Wall(
							At.X + FMath::Clamp(Bound.X - At.X, -1, 1),
							At.Y + FMath::Clamp(Bound.Y - At.Y, -1, 1));
						if (Wall != At)
						{
							Learned.Add(Wall, Now.Tick);
							UE_LOG(LogIntervalHand, Verbose,
								TEXT("learned %d,%d is shut"), Wall.X, Wall.Y);
						}
					}
					// LOOK AGAIN RATHER THAN GIVE UP. Standing somewhere new
					// means seeing nodes that were not in the frame when the
					// route was planned, so the second thought is a better
					// one. Only a handful, and only while the citizen is
					// actually getting somewhere.
					if (RouteGoal != FIntPoint::ZeroValue && FIntPoint(At) != RouteGoal
						&& Rethinks < 24)
					{
						++Rethinks;
						Route.Reset();
						WalkRoute(RouteGoal.X, RouteGoal.Y);
					}
					else
					{
						if (At != Bound && At == LastSeenAt)
						{
							Say(TEXT("that way is blocked"), Now.Tick, true);
						}
						Route.Reset();
						RouteGoal = FIntPoint::ZeroValue;
					}
				}
				else
				{
					LastSeenAt = At;
					++Legs;
					const FIntPoint Want = Bound;
					bBound = false;      // WalkTo sets it again, with a fresh watermark
					WalkTo(Want.X, Want.Y);
				}
			}
			}
		}
	}

	// Once an interval at most: this is a knock at a door, not a battering ram.
	if (bEnterAutomatically && Bridge && Bridge->IsConnected())
	{
		const FIntervalFrame& Frame = Bridge->GetFrame();
		if (!Frame.bHasMe && Frame.Tick != LastEnterTick)
		{
			LastEnterTick = Frame.Tick;
			Bridge->EnterWorld();
		}
	}

	// THE DEED THAT WAS WAITING ON A WALK. Filed the moment the citizen is
	// beside the thing they pointed at, and dropped if they got no closer --
	// a walk the world refused should not leave a deed armed for ever.
	if (!Pending.IsEmpty() && Bridge)
	{
		const FIntervalFrame& Now = Bridge->GetFrame();
		if (Now.bHasMe)
		{
			const int32 Reach = FMath::Abs(Now.Me.X - PendingOn.X)
				+ FMath::Abs(Now.Me.Y - PendingOn.Y);
			if (Reach <= 1)
			{
				const FString Verb = Pending;
				const FIntervalTarget On = PendingOn;
				const FString With = PendingWith;
				Pending.Reset();
				PendingWith.Reset();
				ActOnWith(Verb, On, With);
			}
			else if (!bBound)
			{
				// The walk is over and we are still not there: the world would
				// not take us. Say so rather than holding the deed.
				Say(FString::Printf(TEXT("could not get to %s -- %s dropped"),
					*PendingOn.Name, *Pending), Now.Tick, true);
				Pending.Reset();
				PendingWith.Reset();
			}
		}
	}

	// ---- THE TWO BUTTONS ----
	//
	// RuneScape's arrangement, and it was asked for by name: LEFT does the
	// default thing to whatever is under the cursor, RIGHT lists everything
	// that thing affords. It suits a world where the obvious thing to do to a
	// citizen is trade rather than violence, and where no single click could
	// carry that distinction.
	//
	// Before this a player could reach one of the world's sixty-nine verbs.
	if (bClickToWalk)
	{
		if (APlayerController* PC = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr)
		{
			// WAS IT PRESSED, NOT IS IT DOWN.
			//
			// This read `IsInputKeyDown` and looked for the edge against last
			// frame, which silently drops any click shorter than a frame --
			// and a click IS shorter than a frame whenever the window is not
			// running fast. Streaming a new region of the world takes the
			// editor down to about a frame every three seconds, and at that
			// rate a real mouse's press and release both land between two
			// polls: the button was never observed down, so no edge was ever
			// seen, so nothing happened. The pointer moved to the plot and the
			// menu did not open, with nothing wrong in any log.
			//
			// `WasInputKeyJustPressed` asks a different question -- did a press
			// EVENT arrive during the last frame -- which is answered from the
			// event counts and does not care how briefly the button was held.
			// It also removes the edge bookkeeping, since an event is counted
			// once by construction.
			//
			// This matters beyond the harness. A player on a slow machine, or
			// on the far end of the stream, clicks exactly this fast.
			bool bPressed = PC->WasInputKeyJustPressed(EKeys::LeftMouseButton);
			bool bRight = PC->WasInputKeyJustPressed(EKeys::RightMouseButton);
			bool bReleased = PC->WasInputKeyJustReleased(EKeys::RightMouseButton);

			// ---- AND THE SAME TWO THINGS, FROM ONE FINGER ----
			//
			// A phone has no buttons and this window's whole model is two of
			// them. The substitution is the one every game of this shape makes
			// and the one everybody already knows: a TAP is the left button, a
			// LONG PRESS is the right. A finger that travels is neither -- it
			// is the camera being turned, which the gate reads for itself.
			//
			// THE POINTER IS MOVED TO THE FINGER, which is what makes all of
			// this work with no other change anywhere. Every question this
			// window asks about what is under the pointer -- what is there,
			// what it affords, whether the interface is in the way -- is asked
			// of the CURSOR, and on a phone the cursor is wherever the last
			// touch was. Putting it there means the picking, the menus, the
			// panel test and the drawn pointer are the code that already
			// works, rather than a second copy of it for touch.
			{
				float Tx = 0.f, Ty = 0.f;
				bool bFinger = false;
				PC->GetInputTouchState(ETouchIndex::Touch1, Tx, Ty, bFinger);
				const FVector2D Where(Tx, Ty);
				const double Now = FPlatformTime::Seconds();
				if (bFinger)
				{
					PC->SetMouseLocation(FMath::RoundToInt(Tx), FMath::RoundToInt(Ty));
					if (TouchDownAt < 0.0)
					{
						TouchDownAt = Now;
						TouchDownWhere = Where;
						bTouchHeldFired = false;
					}
					const bool bStill = FVector2D::Distance(Where, TouchDownWhere) <= TouchSlop;
					if (!bTouchHeldFired && bStill && Now - TouchDownAt >= LongPress)
					{
						// THE MENU, WITHOUT WAITING FOR THE FINGER TO LIFT. A
						// long press that only answered on release would feel
						// like a delay rather than a gesture; every phone
						// opens its menu while the finger is still down, and
						// the finger lifting afterwards must then do nothing.
						bTouchHeldFired = true;
						bRight = true;
						bReleased = true;
						RightWentDown = Where;
					}
				}
				else if (TouchDownAt >= 0.0)
				{
					const bool bStill = FVector2D::Distance(Where, TouchDownWhere) <= TouchSlop
						|| TouchDownWhere.IsNearlyZero();
					// A TAP IS A FINGER THAT DID NOT STAY AND DID NOT TRAVEL.
					// If the hold already answered, the lift is nothing.
					if (!bTouchHeldFired && bStill
						&& Now - TouchDownAt < LongPress)
					{
						bPressed = true;
					}
					TouchDownAt = -1.0;
					bTouchHeldFired = false;
				}
			}

			TActorIterator<AIntervalHud> Screen(GetWorld());
			const bool bOverPanels = Screen && Screen->PointerIsOverPanels();

			// AND NOT AT ALL WHEN THE CURSOR IS ON THE INTERFACE.
			//
			// A click on the pack, the chat or the map is not a click on the
			// world, and until now the world answered it anyway -- so a menu
			// opened on a pack slot carried a `walk here 0, 0` from whatever
			// the cursor was notionally over, and a click in the chat box sent
			// the citizen walking. See `PointerIsOverPanels`.
			if (bOverPanels)
			{
			}
			// THE INTERFACE ANSWERS FIRST, AND FOR A FRAME EITHER SIDE.
			//
			// Slate dispatches a widget's mouse handler and the actor's Tick
			// in an order this window does not control, so a flag set by the
			// widget can arrive after the hand has already offered the world's
			// menu for the same click. Holding the claim for a couple of
			// frames covers both orders; the cost is that a right click on the
			// world immediately after one on the pack is ignored, which at
			// two frames is not a thing a hand can do.
			else if (UiTookTheClick > 0)
			{
				--UiTookTheClick;
			}
			// EVERYTHING BELOW IS "THE CURSOR IS ON THE WORLD AND THE
			// INTERFACE HAS NOT ALREADY ANSWERED". It has to stay inside this
			// arm: a left click on the pack that reached the world is the
			// fault `PointerIsOverPanels` exists to prevent.
			else
			{
			// ---- THE RIGHT BUTTON: TWO STATEMENTS, NOT A CHAIN ----
			//
			// It has to be two, and the reason cost an hour. A click faster
			// than a frame arrives with BOTH edges set at once, and in an
			// else-if chain that means only one of them is ever seen.
			//
			// Written as a chain, the one-frame case fell into the release
			// branch WITHOUT the press branch having run -- so `RightWentDown`
			// still held wherever the right button had last gone down, which
			// might be the pack in the corner. The distance check then
			// measured from there to the middle of the world, decided the
			// person had been dragging the camera, and swallowed the menu.
			// From the chair: right click a thing in the pack, then right
			// click anything in the world, and nothing happens at all.
			//
			// As two statements the press always records where it happened
			// and the release always measures from it -- zero for a one-frame
			// click, which is exactly what it is.
			if (bRight)
			{
				// Holding the right button and dragging turns the camera,
				// which is what a hand tries first, so the menu has to wait
				// and see whether this was a click or a turn.
				RightWentDown = FSlateApplication::Get().GetCursorPos();
				bRightMayMenu = true;
			}
			if (bReleased && bRightMayMenu)
			{
				bRightMayMenu = false;
				// A CLICK IS A RIGHT BUTTON THAT DID NOT TRAVEL. Six pixels is
				// the slop of a real hand on a real mouse; beyond that the
				// person was turning the world and does not also want a list
				// of what a fence affords.
				const FVector2D Up = FSlateApplication::Get().GetCursorPos();
				if (FVector2D::Distance(Up, RightWentDown) > 6.0)
				{
				}
				else
				{
				// AND REMEMBER THAT IT IS OPEN.
				//
				// `bMenuOpen` was read below and never written, so it was
				// always false -- which meant the branch beneath, the one that
				// exists so that a click on a menu row does not ALSO act on
				// whatever the world has behind the menu, never ran. Every
				// choice made from the menu did its own deed and a second one:
				// picking `gather` off a seam filed the gather and then walked
				// the citizen to whatever tile the row happened to cover.
				//
				// It is set only when there is something to show, so a right
				// click on bare ground does not arm a swallow for the next
				// left click.
				const TArray<FIntervalTarget> Under = TargetsUnderCursor();
				bMenuOpen = Under.Num() > 0;
				OnOptions.Broadcast(Under);
				}
			}
			else if (bPressed)
			{
				// A left click closes an open menu rather than acting through
				// it, which is what every window of this shape does.
				if (bMenuOpen)
				{
					bMenuOpen = false;
					OnOptions.Broadcast(TArray<FIntervalTarget>());
				}
				else
				{
					const TArray<FIntervalTarget> Under = TargetsUnderCursor();
					if (Under.Num() > 0)
					{
						const TArray<FIntervalOption> Options = OptionsFor(Under[0]);
						if (Options.Num() > 0)
						{
							ActOnWith(Options[0].Verb, Under[0], Options[0].Argument);
						}
					}
				}
			}
			}
		}
	}

	if (!bDrawFeed || !GEngine)
	{
		return;
	}

	// A stand-in for the flat window's feed until §7 builds the door in UMG.
	// On screen, newest last, dropped after FeedSeconds.
	const double Now = FPlatformTime::Seconds();
	int32 Shown = 0;
	for (int32 Index = Feed.Num() - 1; Index >= 0 && Shown < FMath::Max(FeedLines, 1); --Index)
	{
		const FIntervalFeedLine& Line = Feed[Index];
		if (Now - Line.At > FeedSeconds)
		{
			break;
		}
		GEngine->AddOnScreenDebugMessage(
			static_cast<uint64>(reinterpret_cast<UPTRINT>(this)) + Index, 0.f,
			Line.bRefusal ? FColor(226, 138, 108) : FColor(216, 210, 190),
			Line.Text, false);
		++Shown;
	}
}
