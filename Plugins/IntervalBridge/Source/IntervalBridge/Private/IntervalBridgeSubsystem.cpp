#include "IntervalBridgeSubsystem.h"
#include "IntervalGeometry.h"
#include "IntervalScript.h"

#include "WebSocketsModule.h"
#include "IWebSocket.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/Base64.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Engine/GameInstance.h"
#include "TimerManager.h"

DEFINE_LOG_CATEGORY_STATIC(LogIntervalBridge, Log, All);

namespace
{
	/** Condense any sub-document back to a string. Nested shapes are the
	 *  renderer's business only when it asks; it never gets a typed copy. */
	FString CondenseValue(const TSharedPtr<FJsonValue>& Value)
	{
		if (!Value.IsValid())
		{
			return FString();
		}

		FString Out;
		TSharedRef<TJsonWriter<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>> Writer =
			TJsonWriterFactory<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>::Create(&Out);

		if (Value->Type == EJson::Object)
		{
			FJsonSerializer::Serialize(Value->AsObject().ToSharedRef(), Writer);
		}
		else if (Value->Type == EJson::Array)
		{
			FJsonSerializer::Serialize(Value->AsArray(), Writer);
		}
		else
		{
			return Value->AsString();
		}

		return Out;
	}

	FString FlattenValue(const TSharedPtr<FJsonValue>& Value)
	{
		if (!Value.IsValid() || Value->Type == EJson::Null)
		{
			return FString();
		}
		switch (Value->Type)
		{
		case EJson::String:  return Value->AsString();
		case EJson::Number:  return LexToString(Value->AsNumber());
		case EJson::Boolean: return Value->AsBool() ? TEXT("true") : TEXT("false");
		default:             return CondenseValue(Value);
		}
	}

	void AddNested(FIntervalEntity& Entity, const FString& Prefix,
		const TSharedPtr<FJsonValue>& Value, int32 Depth)
	{
		if (Depth > 3 || !Value.IsValid() || Value->Type != EJson::Object)
		{
			return;
		}
		const TSharedPtr<FJsonObject> Inner = Value->AsObject();
		if (!Inner.IsValid())
		{
			return;
		}
		for (const TPair<FString, TSharedPtr<FJsonValue>>& Sub : Inner->Values)
		{
			const FString Key = Prefix + TEXT(".") + Sub.Key;
			Entity.Fields.Add(Key, FlattenValue(Sub.Value));
			AddNested(Entity, Key, Sub.Value, Depth + 1);
		}
	}

	FIntervalEntity ParseEntity(const FString& Id, const TSharedPtr<FJsonObject>& Object)
	{
		FIntervalEntity Entity;
		Entity.Id = Id;
		if (!Object.IsValid())
		{
			return Entity;
		}

		for (const TPair<FString, TSharedPtr<FJsonValue>>& Pair : Object->Values)
		{
			if (Pair.Key == TEXT("x")) { Entity.X = static_cast<int32>(Pair.Value->AsNumber()); continue; }
			if (Pair.Key == TEXT("y")) { Entity.Y = static_cast<int32>(Pair.Value->AsNumber()); continue; }
			if (Pair.Key == TEXT("type") && Pair.Value->Type == EJson::String) { Entity.Kind = Pair.Value->AsString(); }
			Entity.Fields.Add(Pair.Key, FlattenValue(Pair.Value));

			// AND DOWN, UNDER DOTTED KEYS. `action` is an object --
			// {"type":"gather","nodeId":"seam-80"} -- and a name plate that
			// prints the whole of it tells a citizen less than the one word
			// inside it does. Flattening the nesting too means a window can
			// ask for `action.type` without anything here knowing that
			// `action` has a shape, or what any of its words mean.
			//
			// TWO LEVELS, NOT ONE. `equipment` is an object of objects: each
			// slot holds a STACK, {"item":"iron-hatchet","qty":1}, exactly as
			// an inventory slot does. Stopping at one level made
			// `equipment.weapon` the condensed JSON of the stack, so the panel
			// printed nothing and the body drew no tool -- a wielded hatchet
			// was invisible in both places, silently, because a name that is
			// really a blob of JSON matches no kit in the wardrobe and no
			// string in the panel. The depth cap keeps a deep object from
			// filling the map; three is past everything the world sends.
			AddNested(Entity, Pair.Key, Pair.Value, 1);
		}
		return Entity;
	}

	void ParseEntityMap(const TSharedPtr<FJsonObject>& Source, const FString& Field, TMap<FString, FIntervalEntity>& Out)
	{
		Out.Reset();
		const TSharedPtr<FJsonObject>* Map = nullptr;
		if (!Source.IsValid() || !Source->TryGetObjectField(Field, Map) || !Map)
		{
			return;
		}
		Out.Reserve((*Map)->Values.Num());
		for (const TPair<FString, TSharedPtr<FJsonValue>>& Pair : (*Map)->Values)
		{
			if (Pair.Value->Type != EJson::Object)
			{
				continue;
			}
			Out.Add(Pair.Key, ParseEntity(Pair.Key, Pair.Value->AsObject()));
		}
	}

	void DecodePlane(const TSharedPtr<FJsonObject>& Source, const FString& Field, TArray<uint8>& Out)
	{
		Out.Reset();
		FString Encoded;
		if (Source.IsValid() && Source->TryGetStringField(Field, Encoded))
		{
			FBase64::Decode(Encoded, Out);
		}
	}
}

void UIntervalBridgeSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	if (!FModuleManager::Get().IsModuleLoaded(TEXT("WebSockets")))
	{
		FModuleManager::Get().LoadModule(TEXT("WebSockets"));
	}

	FString Url;
	if (!FParse::Value(FCommandLine::Get(), TEXT("intervalbridge="), Url) || Url.IsEmpty())
	{
		// ---- A PHONE HAS NOWHERE TO DIAL ----
		//
		// The desktop default is a Node process on the loopback, because that
		// is what a desktop has. iOS will neither ship Node nor let an app
		// start an interpreter, so there is no second process to talk to and
		// no port to talk on: the bridge runs INSIDE this one, on the rules
		// staged into Content/Bridge, and the default says so rather than
		// leaving a phone dialling an address that can never answer.
		//
		// It is still a command line away on either platform. A desktop that
		// wants no Node passes `-intervalbridge=inproc`; a phone on a bench
		// beside a laptop could be pointed at one.
#if PLATFORM_IOS || PLATFORM_ANDROID
		Url = TEXT("inproc");
#else
		Url = TEXT("ws://127.0.0.1:7777");
#endif
	}
	// ---- OR NO PROCESS AT ALL ----
	//
	// `-intervalbridge=inproc` runs the world's own bridge inside this program.
	// Everything after this point is identical either way: a frame arrives at
	// `HandleMessage` and a deed leaves through `Say`, and neither of them
	// learns whether there was a socket in between.
	if (Url.Equals(TEXT("inproc"), ESearchCase::IgnoreCase))
	{
		bInProcess = true;
		Endpoint = TEXT("inproc");
		OpenInProcessBridge();
		return;
	}
	Connect(Url);
}

void UIntervalBridgeSubsystem::OpenInProcessBridge()
{
#if INTERVAL_HAS_SCRIPT
	FIntervalScript& Script = FIntervalScript::Get();
	if (!Script.IsOpen())
	{
		UE_LOG(LogIntervalBridge, Error,
			TEXT("no JavaScript context, so no bridge in this process"));
		OnConnectionChanged.Broadcast(false);
		return;
	}

	// WHAT THE BRIDGE IS TOLD, and it is the same three answers the desktop
	// takes off a command line. THE NODE IS THE PLAYER'S CHOICE and not this
	// program's: there is no authoritative server in this world, interval.place
	// is simply one that is usually up, and a client that could not be pointed
	// elsewhere would be making a claim about the world that is not true.
	FString Node;
	if (!FParse::Value(FCommandLine::Get(), TEXT("intervalnode="), Node)
		|| Node.IsEmpty())
	{
		Node = TEXT("https://interval.place");
	}
	FString CitizenFile;
	if (!FParse::Value(FCommandLine::Get(), TEXT("intervalkey="), CitizenFile)
		|| CitizenFile.IsEmpty())
	{
		CitizenFile = TEXT("unreal-key.json");
	}
	TMap<FString, FString> Options;
	Options.Add(TEXT("pillar"), Node);
	Options.Add(TEXT("key"), CitizenFile);
	Options.Add(TEXT("port"), TEXT("0"));

	// LISTENING BEFORE IT IS OPENED, because the `hello` goes out during the
	// load and a greeting nobody heard is a window with none of the world's
	// words in it.
	Script.OnFrame = [this](const FString& Text) { HandleMessage(Text); };

	FString Error;
	if (!Script.OpenBridge(Options, Error))
	{
		Script.OnFrame = nullptr;
		UE_LOG(LogIntervalBridge, Error,
			TEXT("the bridge would not start in this process: %s"), *Error);
		OnConnectionChanged.Broadcast(false);
		return;
	}

	// AND THE CLOCK, WHICH IS THE ONE THING THE ENGINE HAS NOT GOT.
	//
	// JavaScriptCore has no timers: they belong to whatever pumps the event
	// loop, which in a browser is the browser, in Node is libuv, and here is
	// the game thread, already running and needing no help. The world ticks
	// once a second, so this is nought to do on all but one frame in sixty.
	if (!PumpHandle.IsValid())
	{
		PumpHandle = FTSTicker::GetCoreTicker().AddTicker(
			TEXT("IntervalBridge.Pump"), 0.f, [](float) -> bool
			{
				if (FIntervalScript::Exists())
				{
					FIntervalScript::Get().Pump();
				}
				return true;
			});
	}
	UE_LOG(LogIntervalBridge, Log,
		TEXT("the bridge is in this process, asking %s"), *Node);
	OnConnectionChanged.Broadcast(true);
#else
	UE_LOG(LogIntervalBridge, Error,
		TEXT("this platform has no JavaScript engine, so the bridge cannot "
		     "run in this process"));
	OnConnectionChanged.Broadcast(false);
#endif
}

void UIntervalBridgeSubsystem::Say(const FString& Text)
{
#if INTERVAL_HAS_SCRIPT
	if (bInProcess)
	{
		FIntervalScript::Get().ToBridge(Text);
		return;
	}
#endif
	if (Socket.IsValid() && Socket->IsConnected())
	{
		Socket->Send(Text);
	}
}

void UIntervalBridgeSubsystem::Deinitialize()
{
	if (PumpHandle.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(PumpHandle);
		PumpHandle.Reset();
	}
#if INTERVAL_HAS_SCRIPT
	// THE FRAME CALLBACK HOLDS A `this`, and the script context outlives this
	// subsystem: a game instance shut down with that lambda still installed is
	// a bridge calling a dead object on the next tick.
	if (bInProcess && FIntervalScript::Exists())
	{
		FIntervalScript::Get().OnFrame = nullptr;
	}
#endif
	if (Socket.IsValid())
	{
		Socket->OnConnected().RemoveAll(this);
		Socket->OnConnectionError().RemoveAll(this);
		Socket->OnClosed().RemoveAll(this);
		Socket->OnMessage().RemoveAll(this);
		if (Socket->IsConnected())
		{
			Socket->Close();
		}
		Socket.Reset();
	}
	Super::Deinitialize();
}

void UIntervalBridgeSubsystem::Connect(const FString& Url)
{
	Endpoint = Url;

	if (Socket.IsValid())
	{
		Socket->OnConnected().RemoveAll(this);
		Socket->OnConnectionError().RemoveAll(this);
		Socket->OnClosed().RemoveAll(this);
		Socket->OnMessage().RemoveAll(this);
		if (Socket->IsConnected())
		{
			Socket->Close();
		}
		Socket.Reset();
	}

	Socket = FWebSocketsModule::Get().CreateWebSocket(Endpoint, TEXT(""));
	Socket->OnConnected().AddUObject(this, &UIntervalBridgeSubsystem::HandleConnected);
	Socket->OnConnectionError().AddUObject(this, &UIntervalBridgeSubsystem::HandleConnectionError);
	Socket->OnClosed().AddUObject(this, &UIntervalBridgeSubsystem::HandleClosed);
	Socket->OnMessage().AddUObject(this, &UIntervalBridgeSubsystem::HandleMessage);
	Socket->Connect();
}

bool UIntervalBridgeSubsystem::IsConnected() const
{
#if INTERVAL_HAS_SCRIPT
	if (bInProcess)
	{
		return FIntervalScript::Exists() && FIntervalScript::Get().IsBridgeOpen();
	}
#endif
	return Socket.IsValid() && Socket->IsConnected();
}

void UIntervalBridgeSubsystem::HandleConnected()
{
	ReconnectDelay = 1.f;
	UE_LOG(LogIntervalBridge, Log, TEXT("bridge open at %s"), *Endpoint);
	OnConnectionChanged.Broadcast(true);
}

void UIntervalBridgeSubsystem::HandleConnectionError(const FString& Error)
{
	// SAY SO IN THE FEED, NOT JUST THE LOG. A window that fails silently is
	// indistinguishable from a world that will not let you move, and that
	// mistake has already cost this project a day on the WebGL windows.
	UE_LOG(LogIntervalBridge, Warning, TEXT("bridge error: %s"), *Error);
	OnConnectionChanged.Broadcast(false);
	ScheduleReconnect();
}

void UIntervalBridgeSubsystem::HandleClosed(int32 StatusCode, const FString& Reason, bool bWasClean)
{
	UE_LOG(LogIntervalBridge, Warning, TEXT("bridge closed (%d) %s"), StatusCode, *Reason);
	OnConnectionChanged.Broadcast(false);
	ScheduleReconnect();
}

void UIntervalBridgeSubsystem::ScheduleReconnect()
{
	UGameInstance* GameInstance = GetGameInstance();
	if (!GameInstance)
	{
		return;
	}

	// Backs off, but never past a few seconds: the bridge is a local process
	// an operator may well be restarting while the editor stays open.
	ReconnectDelay = FMath::Min(ReconnectDelay * 2.f, 8.f);
	GameInstance->GetTimerManager().ClearTimer(ReconnectTimer);
	GameInstance->GetTimerManager().SetTimer(
		ReconnectTimer,
		FTimerDelegate::CreateWeakLambda(this, [this]() { Connect(Endpoint); }),
		ReconnectDelay, false);
}

void UIntervalBridgeSubsystem::SendRaw(const TSharedRef<FJsonObject>& Object)
{
	if (!IsConnected())
	{
		return;
	}
	// WHAT WE JUST DID, REMEMBERED HERE AND NOWHERE ELSE. See Doing.
	//
	// Hooked at the one place every deed passes through rather than in each of
	// the thirty-odd calls above it: a verb wired next session is animated the
	// day it is wired, without anybody having to remember this.
	FString Kind;
	FString Verb;
	if (Object->TryGetStringField(TEXT("k"), Kind) && Kind == TEXT("do")
		&& Object->TryGetStringField(TEXT("type"), Verb) && !Verb.IsEmpty())
	{
		Doing = FName(*Verb);
		// A LITTLE OVER ONE INTERVAL. Shorter and the motion can fall entirely
		// between two frames of a deed asked for just after a tick; much
		// longer and a citizen is still kneading bread two seconds after they
		// walked away from the board.
		DoingUntil = FPlatformTime::Seconds() + 1.15;
	}

	FString Out;
	TSharedRef<TJsonWriter<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>> Writer =
		TJsonWriterFactory<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>::Create(&Out);
	FJsonSerializer::Serialize(Object, Writer);
	Say(Out);
}

void UIntervalBridgeSubsystem::RequestTerrain(int32 X0, int32 Y0, int32 W, int32 H, int32 Skirt)
{
	TSharedRef<FJsonObject> Request = MakeShared<FJsonObject>();
	Request->SetStringField(TEXT("k"), TEXT("terrain"));
	Request->SetNumberField(TEXT("x0"), X0);
	Request->SetNumberField(TEXT("y0"), Y0);
	Request->SetNumberField(TEXT("w"), W);
	Request->SetNumberField(TEXT("h"), H);
	Request->SetNumberField(TEXT("skirt"), Skirt);
	SendRaw(Request);
}

void UIntervalBridgeSubsystem::SendChat(const FString& Text, const FString& Scope)
{
	// EIGHTY, which is what the world takes. It was two hundred and forty here,
	// which is not a limit this window is allowed to invent: the node refuses a
	// longer line whole, so a citizen who typed one watched it disappear with
	// nothing said. Cutting it at the world's own length is the honest thing --
	// they see what was sent.
	const FString Said = Text.TrimStartAndEnd().Left(80);
	if (Said.IsEmpty())
	{
		return;
	}
	TSharedRef<FJsonObject> Request = MakeShared<FJsonObject>();
	Request->SetStringField(TEXT("k"), TEXT("chat"));
	Request->SetStringField(TEXT("text"), Said);
	Request->SetStringField(TEXT("scope"), Scope == TEXT("far") ? TEXT("far") : TEXT("near"));
	SendRaw(Request);
}

void UIntervalBridgeSubsystem::SendIntent(const FString& Type, const TMap<FString, int32>& Numbers, const TMap<FString, FString>& Text)
{
	TSharedRef<FJsonObject> Request = MakeShared<FJsonObject>();
	Request->SetStringField(TEXT("k"), TEXT("do"));
	Request->SetStringField(TEXT("type"), Type);
	for (const TPair<FString, int32>& Pair : Numbers)
	{
		Request->SetNumberField(Pair.Key, Pair.Value);
	}
	for (const TPair<FString, FString>& Pair : Text)
	{
		Request->SetStringField(Pair.Key, Pair.Value);
	}
	// No tick, no world id, no signature. The bridge supplies all three, and
	// that is what keeps a fast renderer from acting on a dead interval.
	SendRaw(Request);
}

void UIntervalBridgeSubsystem::SendIntentBool(const FString& Type,
	const TMap<FString, int32>& Numbers, const TMap<FString, FString>& Text,
	const TMap<FString, bool>& Flags)
{
	TSharedRef<FJsonObject> Request = MakeShared<FJsonObject>();
	Request->SetStringField(TEXT("k"), TEXT("do"));
	Request->SetStringField(TEXT("type"), Type);
	for (const TPair<FString, int32>& Pair : Numbers) { Request->SetNumberField(Pair.Key, Pair.Value); }
	for (const TPair<FString, FString>& Pair : Text) { Request->SetStringField(Pair.Key, Pair.Value); }
	// A REAL JSON BOOLEAN. The world's normalizer refuses 1 and refuses "true";
	// it wants true.
	for (const TPair<FString, bool>& Pair : Flags) { Request->SetBoolField(Pair.Key, Pair.Value); }
	SendRaw(Request);
}

void UIntervalBridgeSubsystem::SendIntentList(const FString& Type, const FString& Field,
	const TArray<int32>& Values)
{
	TSharedRef<FJsonObject> Request = MakeShared<FJsonObject>();
	Request->SetStringField(TEXT("k"), TEXT("do"));
	Request->SetStringField(TEXT("type"), Type);
	TArray<TSharedPtr<FJsonValue>> List;
	List.Reserve(Values.Num());
	for (int32 V : Values)
	{
		List.Add(MakeShared<FJsonValueNumber>(V));
	}
	Request->SetArrayField(Field, List);
	// Same as every other deed: no tick, no world id, no signature. The bridge
	// supplies all three.
	SendRaw(Request);
}

void UIntervalBridgeSubsystem::SendOfferTrade(const FString& To, const TArray<int32>& GiveSlots,
	const FString& WantItem, int32 WantGold)
{
	TSharedRef<FJsonObject> Request = MakeShared<FJsonObject>();
	Request->SetStringField(TEXT("k"), TEXT("do"));
	Request->SetStringField(TEXT("type"), TEXT("offer_trade"));
	Request->SetStringField(TEXT("to"), To);
	TArray<TSharedPtr<FJsonValue>> Slots;
	Slots.Reserve(GiveSlots.Num());
	for (int32 V : GiveSlots)
	{
		Slots.Add(MakeShared<FJsonValueNumber>(V));
	}
	Request->SetArrayField(TEXT("giveSlots"), Slots);
	// A REAL JSON NULL when no item is wanted. Not an empty string, which is an
	// item named "", and not the field left out, which the engine refuses --
	// "omission is not a representation". The same lesson the pickup's boolean
	// taught: this world types its fields and means it.
	if (WantItem.IsEmpty())
	{
		Request->SetField(TEXT("wantItem"), MakeShared<FJsonValueNull>());
	}
	else
	{
		Request->SetStringField(TEXT("wantItem"), WantItem);
	}
	Request->SetNumberField(TEXT("wantGold"), WantGold);
	// Same as every other deed: no tick, no world id, no signature. The bridge
	// supplies all three.
	SendRaw(Request);
}

void UIntervalBridgeSubsystem::Resync()
{
	TSharedRef<FJsonObject> Request = MakeShared<FJsonObject>();
	Request->SetStringField(TEXT("k"), TEXT("resync"));
	SendRaw(Request);
}

void UIntervalBridgeSubsystem::EnterWorld()
{
	const TSharedRef<FJsonObject> Request = MakeShared<FJsonObject>();
	Request->SetStringField(TEXT("k"), TEXT("enter"));
	SendRaw(Request);
}

void UIntervalBridgeSubsystem::CarryCitizenOut()
{
	const TSharedRef<FJsonObject> Request = MakeShared<FJsonObject>();
	Request->SetStringField(TEXT("k"), TEXT("carry-out"));
	SendRaw(Request);
}

void UIntervalBridgeSubsystem::CarryCitizenIn()
{
	const TSharedRef<FJsonObject> Request = MakeShared<FJsonObject>();
	Request->SetStringField(TEXT("k"), TEXT("carry-in"));
	SendRaw(Request);
}

void UIntervalBridgeSubsystem::ReadFounding(const TSharedPtr<FJsonObject>& Root)
{
	// THE FOUNDING IS TOLD, ONCE, AND NEVER DERIVED.
	//
	// Both of these have been sitting in `hello` as raw JSON since the bridge
	// was written, because nothing in the window had a use for them yet. The
	// window still learns nothing from them: it does not know what a capital
	// is or what a road is for. It knows that the world named a rectangle and
	// a word, and that a level may have an opinion about that word.
	Settlements.Reset();
	Ways.Reset();
	if (!Root.IsValid())
	{
		return;
	}

	const TArray<TSharedPtr<FJsonValue>>* Seats = nullptr;
	if (Root->TryGetArrayField(TEXT("settlements"), Seats) && Seats)
	{
		for (const TSharedPtr<FJsonValue>& Value : *Seats)
		{
			const TSharedPtr<FJsonObject> Seat = Value.IsValid() ? Value->AsObject() : nullptr;
			if (!Seat.IsValid()) { continue; }
			FIntervalSettlement Town;
			Seat->TryGetStringField(TEXT("tag"), Town.Tag);
			Seat->TryGetStringField(TEXT("name"), Town.Name);
			FString Word;
			if (Seat->TryGetStringField(TEXT("kind"), Word)) { Town.Kind = FName(*Word); }
			if (Seat->TryGetStringField(TEXT("ring"), Word)) { Town.Ring = FName(*Word); }
			Seat->TryGetNumberField(TEXT("x"), Town.X);
			Seat->TryGetNumberField(TEXT("y"), Town.Y);
			Seat->TryGetNumberField(TEXT("w"), Town.W);
			Seat->TryGetNumberField(TEXT("h"), Town.H);
			if (Town.W > 0 && Town.H > 0) { Settlements.Add(MoveTemp(Town)); }
		}
	}

	// The roads arrive as "x,y" strings under `tiles`, which is how /api/roads
	// serves them; a set is the only shape anything here wants them in.
	const TSharedPtr<FJsonObject>* RoadObject = nullptr;
	if (Root->TryGetObjectField(TEXT("roads"), RoadObject) && RoadObject)
	{
		const TArray<TSharedPtr<FJsonValue>>* Laid = nullptr;
		if ((*RoadObject)->TryGetArrayField(TEXT("tiles"), Laid) && Laid)
		{
			for (const TSharedPtr<FJsonValue>& Value : *Laid)
			{
				const FString Pair = Value.IsValid() ? Value->AsString() : FString();
				FString Left, Right;
				if (Pair.Split(TEXT(","), &Left, &Right))
				{
					Ways.Add(FIntPoint(FCString::Atoi(*Left), FCString::Atoi(*Right)));
				}
			}
		}
	}

	UE_LOG(LogTemp, Log, TEXT("[interval] founding: %d settlements, %d road tiles"),
		Settlements.Num(), Ways.Num());
}

void UIntervalBridgeSubsystem::HandleMessage(const FString& Message)
{
	TSharedPtr<FJsonObject> Root;
	TSharedRef<TJsonReader<TCHAR>> Reader = TJsonReaderFactory<TCHAR>::Create(Message);
	if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
	{
		UE_LOG(LogIntervalBridge, Warning, TEXT("unparsable message, %d chars"), Message.Len());
		return;
	}

	const FString Kind = Root->GetStringField(TEXT("k"));

	if (Kind == TEXT("hello"))
	{
		Root->TryGetStringField(TEXT("playerId"), PlayerId);
		Root->TryGetStringField(TEXT("worldId"), WorldId);

		const TSharedPtr<FJsonObject>* Genesis = nullptr;
		if (Root->TryGetObjectField(TEXT("genesis"), Genesis) && Genesis)
		{
			(*Genesis)->TryGetNumberField(TEXT("worldW"), WorldW);
			(*Genesis)->TryGetNumberField(TEXT("worldH"), WorldH);
		}

		double TickMs = 1000.0;
		Root->TryGetNumberField(TEXT("tickMs"), TickMs);
		TickSeconds = FMath::Max(TickMs, 1.0) / 1000.0;
		// Start from what the world says and let arrivals correct it.
		TickMeasured = TickSeconds;

		// WHAT EACH NODE TYPE AFFORDS, so a player can be offered it.
		//
		// The window can file sixty-six of the world's verbs and a PLAYER could
		// reach one of them -- walk -- because there was no way to point at
		// anything and nothing to say what pointing at it would allow. That
		// answer is world knowledge, so the bridge derives it from the engine
		// (see `affordances` there) and hands it over once, here, exactly as it
		// hands over the terrain names. This window holds no opinion about what
		// a well is for.
		const TSharedPtr<FJsonObject>* AffordsObject = nullptr;
		if (Root->TryGetObjectField(TEXT("affords"), AffordsObject) && AffordsObject)
		{
			Affords.Reset();
			for (const TPair<FString, TSharedPtr<FJsonValue>>& Row : (*AffordsObject)->Values)
			{
				const TArray<TSharedPtr<FJsonValue>>* Verbs = nullptr;
				if (!Row.Value.IsValid() || !Row.Value->TryGetArray(Verbs) || !Verbs)
				{
					continue;
				}
				FIntervalAffords Got;
				for (const TSharedPtr<FJsonValue>& V : *Verbs)
				{
					FString Word;
					if (V.IsValid() && V->TryGetString(Word) && !Word.IsEmpty())
					{
						Got.Verbs.Add(Word);
					}
				}
				if (Got.Verbs.Num() > 0)
				{
					Affords.Add(Row.Key, MoveTemp(Got));
				}
			}
			UE_LOG(LogTemp, Log, TEXT("[interval] the bridge affords %d node types"),
				Affords.Num());
		}

		// AND WHICH FIELD EACH VERB NAMES ITS TARGET IN -- or whether it
		// takes one at all.
		//
		// This window used to attach `nodeId` to every deed filed against a
		// node, which is right for most verbs and wrong for the ones where the
		// world finds the thing itself: a citizen drinks from whichever well
		// they are standing beside, cooks at whichever hearth, smiths at
		// whichever anvil, and the deed names none of them. Those came back
		// "unknown field nodeId on drink" and did nothing, from menu entries
		// that had just offered to do them. The engine's own schemas say; the
		// bridge reads them and sends them here.
		const TSharedPtr<FJsonObject>* TakesObject = nullptr;
		if (Root->TryGetObjectField(TEXT("verbTakes"), TakesObject) && TakesObject)
		{
			VerbTarget.Reset();
			for (const TPair<FString, TSharedPtr<FJsonValue>>& Row : (*TakesObject)->Values)
			{
				const TArray<TSharedPtr<FJsonValue>>* Fields = nullptr;
				if (!Row.Value.IsValid() || !Row.Value->TryGetArray(Fields) || !Fields)
				{
					continue;
				}
				for (const TSharedPtr<FJsonValue>& F : *Fields)
				{
					FString Field;
					if (!F.IsValid() || !F->TryGetString(Field))
					{
						continue;
					}
					// Only the three that name a THING. A verb may also take a
					// style or a recipe, and those are not targets.
					if (Field == TEXT("nodeId") || Field == TEXT("mobId")
						|| Field == TEXT("targetId"))
					{
						VerbTarget.Add(Row.Key, Field);
						break;
					}
				}
			}
			UE_LOG(LogTemp, Log, TEXT("[interval] %d verbs name a target"),
				VerbTarget.Num());
		}

		// §6dj: THE HEIGHT OF THE LAND, sent once with the world.
		//
		// Kept in the geometry, not here, because everything that stands on a
		// tile needs it and none of them should have to be handed a grid.
		if (const TSharedPtr<FJsonObject>* Elev = nullptr;
			Root->TryGetObjectField(TEXT("elev"), Elev) && Elev)
		{
			UIntervalGeometry::FLand& Land = UIntervalGeometry::Land();
			double N = 0.0;
			if ((*Elev)->TryGetNumberField(TEXT("step"), N)) { Land.Step = FMath::Max(1, static_cast<int32>(N)); }
			if ((*Elev)->TryGetNumberField(TEXT("w"), N))    { Land.W = static_cast<int32>(N); }
			if ((*Elev)->TryGetNumberField(TEXT("h"), N))    { Land.H = static_cast<int32>(N); }
			const TArray<TSharedPtr<FJsonValue>>* Values = nullptr;
			if ((*Elev)->TryGetArrayField(TEXT("v"), Values) && Values)
			{
				Land.V.Reset(Values->Num());
				for (const TSharedPtr<FJsonValue>& One : *Values)
				{
					Land.V.Add(static_cast<uint8>(FMath::Clamp(
						static_cast<int32>(One->AsNumber()), 0, 255)));
				}
			}
			UE_LOG(LogTemp, Log, TEXT("[interval] the land is %dx%d samples, %d tiles apart"),
				Land.W, Land.H, Land.Step);
		}

		// §7cf: THE BOOKS, so nothing here keeps a second copy of them.
		if (const TSharedPtr<FJsonObject>* Written = nullptr;
			Root->TryGetObjectField(TEXT("books"), Written) && Written)
		{
			Books.Reset();
			for (const TPair<FString, TSharedPtr<FJsonValue>>& One : (*Written)->Values)
			{
				const TArray<TSharedPtr<FJsonValue>>* Words = nullptr;
				if (!One.Value.IsValid() || !One.Value->TryGetArray(Words) || !Words)
				{
					continue;
				}
				FIntervalAffords Held;
				for (const TSharedPtr<FJsonValue>& Word : *Words)
				{
					Held.Verbs.Add(Word->AsString());
				}
				Books.Add(One.Key, MoveTemp(Held));
			}
		}

		// WHAT MAY BE SWORN, AND FOR HOW LONG.
		{
			const TSharedPtr<FJsonObject>* Sworn = nullptr;
			// ---- WHAT EACH KEEPER'S TRADE IS CALLED ----
			//
			// A keeper node carries a `name` the world gave it and, for eighty-one
			// of the hundred and fifty-seven, a `kind`. This table turns the kind
			// into the trade: `banker` into "the banker", `lumber` into "the axe
			// man". The window had the name and not the trade, so Anchor was a
			// street of people called things with no way to tell which one takes
			// a deposit.
			if (const TSharedPtr<FJsonObject>* Trades = nullptr;
				Root->TryGetObjectField(TEXT("keepers"), Trades) && Trades)
			{
				KeeperTrades.Reset();
				for (const TPair<FString, TSharedPtr<FJsonValue>>& Row : (*Trades)->Values)
				{
					FString Called;
					if (Row.Value.IsValid() && Row.Value->TryGetString(Called))
					{
						KeeperTrades.Add(Row.Key, Called);
					}
				}
			}
			if (Root->TryGetObjectField(TEXT("callings"), Sworn) && Sworn)
			{
				Callings.Reset();
				for (const TPair<FString, TSharedPtr<FJsonValue>>& Row : (*Sworn)->Values)
				{
					FString Craft;
					if (Row.Value.IsValid() && Row.Value->TryGetString(Craft))
					{
						Callings.Add(Row.Key, Craft);
					}
				}
			}
			double Number = 0.0;
			if (Root->TryGetNumberField(TEXT("swearLevel"), Number))
			{
				SwearLevel = static_cast<int32>(Number);
			}
			// §5r-iv: the other half of the door to a calling.
			if (Root->TryGetNumberField(TEXT("swearCountries"), Number))
			{
				SwearCountries = static_cast<int32>(Number);
			}
			// §5k: and what it costs.
			if (Root->TryGetNumberField(TEXT("capOther"), Number))
			{
				CapOther = static_cast<int32>(Number);
			}
			if (Root->TryGetNumberField(TEXT("stintCap"), Number))
			{
				StintCap = static_cast<int32>(Number);
			}
			if (Root->TryGetNumberField(TEXT("nameStanding"), Number))
			{
				NameStanding = static_cast<int32>(Number);
			}
		}

		// AND THE CRAFT LEVELS A FEW VERBS ASK FOR. See VerbNeeds.
		const TSharedPtr<FJsonObject>* Bars = nullptr;
		if (Root->TryGetObjectField(TEXT("verbNeeds"), Bars) && Bars)
		{
			VerbNeeds.Reset();
			for (const TPair<FString, TSharedPtr<FJsonValue>>& Row : (*Bars)->Values)
			{
				const TSharedPtr<FJsonObject>* Want = nullptr;
				if (!Row.Value.IsValid() || !Row.Value->TryGetObject(Want) || !Want)
				{
					continue;
				}
				FIntervalVerbBar Bar;
				(*Want)->TryGetStringField(TEXT("skill"), Bar.Craft);
				double Rung = 0.0;
				if ((*Want)->TryGetNumberField(TEXT("level"), Rung))
				{
					Bar.Level = static_cast<int32>(Rung);
				}
				if (!Bar.Craft.IsEmpty()) { VerbNeeds.Add(Row.Key, Bar); }
			}
		}

		// AND THE CRAFT LEVELS A FEW ITEMS ASK FOR BEFORE THEY MAY BE HELD.
		// Per item rather than per verb, because that is the shape the world
		// keeps them in. See WieldNeeds.
		const TSharedPtr<FJsonObject>* Arms = nullptr;
		if (Root->TryGetObjectField(TEXT("wieldNeeds"), Arms) && Arms)
		{
			WieldNeeds.Reset();
			for (const TPair<FString, TSharedPtr<FJsonValue>>& Row : (*Arms)->Values)
			{
				const TSharedPtr<FJsonObject>* Want = nullptr;
				if (!Row.Value.IsValid() || !Row.Value->TryGetObject(Want) || !Want)
				{
					continue;
				}
				TArray<FIntervalVerbBar> Rungs;
				for (const TPair<FString, TSharedPtr<FJsonValue>>& Each : (*Want)->Values)
				{
					double Height = 0.0;
					if (!Each.Value.IsValid() || !Each.Value->TryGetNumber(Height))
					{
						continue;
					}
					FIntervalVerbBar Asked;
					Asked.Craft = Each.Key;
					Asked.Level = static_cast<int32>(Height);
					Rungs.Add(Asked);
				}
				if (Rungs.Num() > 0) { WieldNeeds.Add(Row.Key, Rungs); }
			}
		}

		// AND EVERY FIELD EACH VERB NAMES, so a deed this window cannot fill
		// in is never offered. See `CanFile` for what "cannot" means.
		const TSharedPtr<FJsonObject>* FieldsObject = nullptr;
		if (Root->TryGetObjectField(TEXT("verbFields"), FieldsObject) && FieldsObject)
		{
			VerbFields.Reset();
			for (const TPair<FString, TSharedPtr<FJsonValue>>& Row : (*FieldsObject)->Values)
			{
				const TArray<TSharedPtr<FJsonValue>>* Names = nullptr;
				if (!Row.Value.IsValid() || !Row.Value->TryGetArray(Names) || !Names)
				{
					continue;
				}
				FIntervalAffords Got;
				for (const TSharedPtr<FJsonValue>& N : *Names)
				{
					FString Name;
					if (N.IsValid() && N->TryGetString(Name) && !Name.IsEmpty())
					{
						Got.Verbs.Add(Name);
					}
				}
				VerbFields.Add(Row.Key, MoveTemp(Got));
			}
			UE_LOG(LogTemp, Log, TEXT("[interval] %d verbs declare their fields"),
				VerbFields.Num());
		}

		// AND WHAT EACH KIND OF STALL SELLS. See the note in the bridge: a
		// `buy` with no item in it is a deed the world refuses, so the menu
		// has to offer the goods by name.
		const TSharedPtr<FJsonObject>* SellsObject = nullptr;
		if (Root->TryGetObjectField(TEXT("stallSells"), SellsObject) && SellsObject)
		{
			StallSells.Reset();
			for (const TPair<FString, TSharedPtr<FJsonValue>>& Row : (*SellsObject)->Values)
			{
				const TSharedPtr<FJsonObject>* Goods = nullptr;
				if (!Row.Value.IsValid() || !Row.Value->TryGetObject(Goods) || !Goods)
				{
					continue;
				}
				FIntervalStock Stock;
				for (const TPair<FString, TSharedPtr<FJsonValue>>& Good : (*Goods)->Values)
				{
					double Price = 0.0;
					if (Good.Value.IsValid() && Good.Value->TryGetNumber(Price))
					{
						Stock.Price.Add(Good.Key, FMath::RoundToInt(Price));
					}
				}
				if (Stock.Price.Num() > 0)
				{
					StallSells.Add(Row.Key, MoveTemp(Stock));
				}
			}
			UE_LOG(LogTemp, Log, TEXT("[interval] %d kinds of stall keep stock"),
				StallSells.Num());
		}

		// AND WHAT CAN BE MADE AT AN ANVIL, with what it costs.
		const TSharedPtr<FJsonObject>* RecipeObject = nullptr;
		if (Root->TryGetObjectField(TEXT("recipes"), RecipeObject) && RecipeObject)
		{
			Recipes.Reset();
			for (const TPair<FString, TSharedPtr<FJsonValue>>& Row : (*RecipeObject)->Values)
			{
				const TSharedPtr<FJsonObject>* Cost = nullptr;
				if (!Row.Value.IsValid() || !Row.Value->TryGetObject(Cost) || !Cost)
				{
					continue;
				}
				FIntervalStock Needs;
				for (const TPair<FString, TSharedPtr<FJsonValue>>& Part : (*Cost)->Values)
				{
					double Many = 0.0;
					if (Part.Value.IsValid() && Part.Value->TryGetNumber(Many))
					{
						Needs.Price.Add(Part.Key, FMath::RoundToInt(Many));
					}
				}
				Recipes.Add(Row.Key, MoveTemp(Needs));
			}
			UE_LOG(LogTemp, Log, TEXT("[interval] %d things can be made"), Recipes.Num());
		}

		// AND WHAT A THING IN THE PACK AFFORDS, derived the same way.
		// The same shape as `itemAffords`, and read the same way: a map from a
		// thing's word to a list of words.
		const TSharedPtr<FJsonObject>* MakesObject = nullptr;
		if (Root->TryGetObjectField(TEXT("itemMakes"), MakesObject) && MakesObject)
		{
			ItemMakes.Reset();
			for (const TPair<FString, TSharedPtr<FJsonValue>>& Row : (*MakesObject)->Values)
			{
				const TArray<TSharedPtr<FJsonValue>>* Makes = nullptr;
				if (!Row.Value.IsValid() || !Row.Value->TryGetArray(Makes) || !Makes)
				{
					continue;
				}
				FIntervalAffords Got;
				for (const TSharedPtr<FJsonValue>& V : *Makes)
				{
					FString Word;
					if (V.IsValid() && V->TryGetString(Word) && !Word.IsEmpty())
					{
						Got.Verbs.Add(Word);
					}
				}
				if (Got.Verbs.Num() > 0) { ItemMakes.Add(Row.Key, MoveTemp(Got)); }
			}
		}

		const TSharedPtr<FJsonObject>* ItemAffordsObject = nullptr;
		if (Root->TryGetObjectField(TEXT("itemAffords"), ItemAffordsObject) && ItemAffordsObject)
		{
			ItemAffords.Reset();
			for (const TPair<FString, TSharedPtr<FJsonValue>>& Row : (*ItemAffordsObject)->Values)
			{
				const TArray<TSharedPtr<FJsonValue>>* Verbs = nullptr;
				if (!Row.Value.IsValid() || !Row.Value->TryGetArray(Verbs) || !Verbs)
				{
					continue;
				}
				FIntervalAffords Got;
				for (const TSharedPtr<FJsonValue>& V : *Verbs)
				{
					FString Word;
					if (V.IsValid() && V->TryGetString(Word) && !Word.IsEmpty())
					{
						Got.Verbs.Add(Word);
					}
				}
				if (Got.Verbs.Num() > 0)
				{
					ItemAffords.Add(Row.Key, MoveTemp(Got));
				}
			}
			UE_LOG(LogTemp, Log, TEXT("[interval] the bridge affords %d items"),
				ItemAffords.Num());
		}

		// ---- AND WHAT EACH PLACE WILL TAKE, for the two verbs that name a
		// place AND a slot. Nested one deeper than the tables above: a verb,
		// then the node types that verb is done at, then the things each of
		// those takes. Flattened to `verb|nodetype` here, because the window
		// only ever asks for one pair at a time. See `fuelsByNode`.
		const TSharedPtr<FJsonObject>* TakenAtObject = nullptr;
		if (Root->TryGetObjectField(TEXT("takesAt"), TakenAtObject) && TakenAtObject)
		{
			TakesAt.Reset();
			for (const TPair<FString, TSharedPtr<FJsonValue>>& Verb : (*TakenAtObject)->Values)
			{
				const TSharedPtr<FJsonObject>* Places = nullptr;
				if (!Verb.Value.IsValid() || !Verb.Value->TryGetObject(Places) || !Places)
				{
					continue;
				}
				for (const TPair<FString, TSharedPtr<FJsonValue>>& Place : (*Places)->Values)
				{
					const TArray<TSharedPtr<FJsonValue>>* Things = nullptr;
					if (!Place.Value.IsValid() || !Place.Value->TryGetArray(Things) || !Things)
					{
						continue;
					}
					FIntervalAffords Got;
					for (const TSharedPtr<FJsonValue>& T : *Things)
					{
						FString Word;
						if (T.IsValid() && T->TryGetString(Word) && !Word.IsEmpty())
						{
							Got.Verbs.Add(Word);
						}
					}
					if (Got.Verbs.Num() > 0)
					{
						TakesAt.Add(Verb.Key + TEXT("|") + Place.Key, MoveTemp(Got));
					}
				}
			}
			UE_LOG(LogTemp, Log, TEXT("[interval] the bridge knows what %d places take"),
				TakesAt.Num());
		}

		// §6c: AND WHERE THE DEAD COME BACK. A fact about the founding, sent
		// once, so the five intervals a death lasts can say what happens next.
		const TSharedPtr<FJsonObject>* BackObject = nullptr;
		if (Root->TryGetObjectField(TEXT("returnTo"), BackObject) && BackObject)
		{
			(*BackObject)->TryGetStringField(TEXT("place"), ReturnPlace);
			(*BackObject)->TryGetNumberField(TEXT("x"), ReturnX);
			(*BackObject)->TryGetNumberField(TEXT("y"), ReturnY);
			UE_LOG(LogTemp, Log, TEXT("[interval] the dead return to %s (%d,%d)"),
				ReturnPlace.IsEmpty() ? TEXT("the spawn") : *ReturnPlace, ReturnX, ReturnY);
		}

		const TSharedPtr<FJsonObject>* TablesObject = nullptr;
		if (Root->TryGetObjectField(TEXT("tables"), TablesObject) && TablesObject)
		{
			Tables = *TablesObject;
			TablesJson = CondenseValue(MakeShared<FJsonValueObject>(Tables));
		}

		SettlementsJson = CondenseValue(Root->TryGetField(TEXT("settlements")));
		WaysJson = CondenseValue(Root->TryGetField(TEXT("roads")));
		ReadFounding(Root);

		TileNames.Reset();
		const TArray<TSharedPtr<FJsonValue>>* Names = nullptr;
		if (Root->TryGetArrayField(TEXT("tiles"), Names) && Names)
		{
			for (const TSharedPtr<FJsonValue>& Name : *Names)
			{
				TileNames.Add(Name->AsString());
			}
		}

		UE_LOG(LogIntervalBridge, Log, TEXT("world %s, %dx%d, %d terrains, citizen %s"),
			*WorldId.Left(12), WorldW, WorldH, TileNames.Num(), *PlayerId.Left(12));
		OnReady.Broadcast();
		return;
	}

	if (Kind == TEXT("tiles"))
	{
		// The bridge met ground it had no name for and grew its list. Nothing
		// here is invalidated -- old codes keep their meaning, the list only
		// ever appends -- but materials want warming for the new ones.
		const TArray<TSharedPtr<FJsonValue>>* Names = nullptr;
		if (Root->TryGetArrayField(TEXT("tiles"), Names) && Names)
		{
			TileNames.Reset();
			for (const TSharedPtr<FJsonValue>& Name : *Names)
			{
				TileNames.Add(Name->AsString());
			}
			OnTileNamesChanged.Broadcast(true);
		}
		return;
	}

	if (Kind == TEXT("frame"))
	{
		PrevFrame = Frame;

		FIntervalFrame Next;
		double TickNumber = 0.0;
		Root->TryGetNumberField(TEXT("tick"), TickNumber);
		Next.Tick = static_cast<int64>(TickNumber);

		const TSharedPtr<FJsonObject>* MeObject = nullptr;
		if (Root->TryGetObjectField(TEXT("me"), MeObject) && MeObject && (*MeObject).IsValid())
		{
			Next.Me = ParseEntity(PlayerId, *MeObject);
			Next.bHasMe = true;
		}

		if (const TSharedPtr<FJsonObject>* Birth = nullptr; Root->HasTypedField<EJson::Object>(TEXT("birth")))
		{
			const TSharedPtr<FJsonObject> B = Root->GetObjectField(TEXT("birth"));
			Next.BirthState = B->HasField(TEXT("state")) ? B->GetStringField(TEXT("state")) : FString();
			Next.BirthWaited = B->HasField(TEXT("waited")) ? static_cast<int32>(B->GetNumberField(TEXT("waited"))) : 0;
			Next.BirthRipeAt = B->HasField(TEXT("ripeAt")) ? static_cast<int32>(B->GetNumberField(TEXT("ripeAt"))) : 0;
		}
		// WHICH WORLD THIS IS. Read on every frame, not once: a resident
		// crosses out of Nought mid-session and the banner has to go.
		{
			Next.bNought = Root->HasField(TEXT("nought"))
				&& Root->GetBoolField(TEXT("nought"));
		}

		// §5c: THE TRADE STANDING BETWEEN TWO PEOPLE, both directions.
		if (const TSharedPtr<FJsonObject>* Trade = nullptr;
			Root->HasTypedField<EJson::Object>(TEXT("trade")))
		{
			const TSharedPtr<FJsonObject> T = Root->GetObjectField(TEXT("trade"));
			// WHAT IS BEING HANDED OVER, AS ONE SENTENCE. The window prints it
			// and does nothing else with it, so a list of words is a list of
			// words -- the deed names a key and a slot, never these.
			auto Sentence = [](const TSharedPtr<FJsonObject>& Side)
			{
				FString Said;
				const TArray<TSharedPtr<FJsonValue>>* Give = nullptr;
				if (Side->TryGetArrayField(TEXT("give"), Give) && Give)
				{
					for (const TSharedPtr<FJsonValue>& Word : *Give)
					{
						Said += (Said.IsEmpty() ? TEXT("") : TEXT(", ")) + Word->AsString();
					}
				}
				return Said;
			};
			auto Asking = [](const TSharedPtr<FJsonObject>& Side)
			{
				FString Want;
				if (Side->TryGetStringField(TEXT("wantItem"), Want) && !Want.IsEmpty())
				{
					return Want;
				}
				double Gold = 0.0;
				Side->TryGetNumberField(TEXT("wantGold"), Gold);
				return FString::Printf(TEXT("%d gold"), static_cast<int32>(Gold));
			};
			const TSharedPtr<FJsonObject>* Side = nullptr;
			if (T->TryGetObjectField(TEXT("offered"), Side) && Side)
			{
				(*Side)->TryGetStringField(TEXT("from"), Next.OfferFrom);
				(*Side)->TryGetStringField(TEXT("name"), Next.OfferName);
				Next.OfferGives = Sentence(*Side);
				Next.OfferWants = Asking(*Side);
			}
			if (T->TryGetObjectField(TEXT("mine"), Side) && Side)
			{
				(*Side)->TryGetStringField(TEXT("toName"), Next.MineTo);
				Next.MineGives = Sentence(*Side);
				Next.MineWants = Asking(*Side);
			}
		}

		// WHAT EACH CRAFT IS AT. See `FIntervalFrame::Levels`.
		if (const TSharedPtr<FJsonObject>* Rungs = nullptr;
			Root->TryGetObjectField(TEXT("levels"), Rungs) && Rungs)
		{
			for (const TPair<FString, TSharedPtr<FJsonValue>>& Craft : (*Rungs)->Values)
			{
				const TSharedPtr<FJsonObject>* Rung = nullptr;
				if (!Craft.Value.IsValid() || !Craft.Value->TryGetObject(Rung) || !Rung)
				{
					continue;
				}
				FIntervalCraft Learned;
				double N = 0.0;
				if ((*Rung)->TryGetNumberField(TEXT("level"), N)) { Learned.Level = static_cast<int32>(N); }
				if ((*Rung)->TryGetNumberField(TEXT("xp"), N))    { Learned.Xp    = static_cast<int32>(N); }
				if ((*Rung)->TryGetNumberField(TEXT("from"), N))  { Learned.From  = static_cast<int32>(N); }
				if ((*Rung)->TryGetNumberField(TEXT("next"), N))  { Learned.Next  = static_cast<int32>(N); }
				Next.Levels.Add(Craft.Key, Learned);
			}
		}

		// WHAT THE GROUND UNDERFOOT AFFORDS. Every frame: one step changes it.
		if (const TArray<TSharedPtr<FJsonValue>>* Here = nullptr;
			Root->TryGetArrayField(TEXT("atHand"), Here) && Here)
		{
			for (const TSharedPtr<FJsonValue>& Word : *Here)
			{
				Next.AtHand.Add(Word->AsString());
			}
		}
		if (Next.AtHand.Num() != Frame.AtHand.Num())
		{
			UE_LOG(LogTemp, Log, TEXT("[interval] underfoot: %s"),
				*FString::Join(Next.AtHand, TEXT(" ")));
		}

		// AND WHAT CANNOT BE DONE FROM HERE AT ALL. See FIntervalFrame::Barred.
		if (const TArray<TSharedPtr<FJsonValue>>* Shut = nullptr;
			Root->TryGetArrayField(TEXT("barred"), Shut) && Shut)
		{
			for (const TSharedPtr<FJsonValue>& Word : *Shut)
			{
				Next.Barred.Add(Word->AsString());
			}
		}

		// AND WHAT MAY BE DONE ON THE TILE ITSELF. See `FIntervalFrame::Underfoot`.
		if (const TArray<TSharedPtr<FJsonValue>>* Here = nullptr;
			Root->TryGetArrayField(TEXT("underfoot"), Here) && Here)
		{
			for (const TSharedPtr<FJsonValue>& Word : *Here)
			{
				Next.Underfoot.Add(Word->AsString());
			}
		}

		// §6g: THE COUNTER IN REACH. Read every frame for the same reason --
		// a citizen walks away from a bank and the screen must shut.
		if (const TSharedPtr<FJsonObject>* Vault = nullptr;
			Root->HasTypedField<EJson::Object>(TEXT("vault")))
		{
			const TSharedPtr<FJsonObject> V = Root->GetObjectField(TEXT("vault"));
			Next.bAtVault = true;
			const TSharedPtr<FJsonObject>* Items = nullptr;
			if (V->TryGetObjectField(TEXT("items"), Items) && Items)
			{
				for (const TPair<FString, TSharedPtr<FJsonValue>>& Held : (*Items)->Values)
				{
					const int32 Many = static_cast<int32>(Held.Value->AsNumber());
					if (Many > 0)
					{
						Next.Vault.Add(Held.Key, Many);
					}
				}
			}
		}
		Next.Place = Root->HasField(TEXT("place"))
			? Root->GetStringField(TEXT("place")) : FString();
		// §7dq: the ground underfoot by name, and whether anything in hand is
		// burning. Both are the bridge's answers, not this window's guesses.
		Next.Surface = Root->HasField(TEXT("surface"))
			? Root->GetStringField(TEXT("surface")) : FString();
		Next.bLit = Root->HasField(TEXT("lit")) && Root->GetBoolField(TEXT("lit"));
		// §7dn/§7dq: and what the ground ahead will ask, if anything does
		if (const TSharedPtr<FJsonObject>* Gate = nullptr;
			Root->TryGetObjectField(TEXT("threshold"), Gate) && Gate && Gate->IsValid())
		{
			(*Gate)->TryGetStringField(TEXT("says"), Next.ThresholdSays);
			(*Gate)->TryGetBoolField(TEXT("may"), Next.bThresholdOpen);
			// and the tile, so the window can draw the crossing and not only
			// explain it
			(*Gate)->TryGetNumberField(TEXT("x"), Next.ThresholdX);
			(*Gate)->TryGetNumberField(TEXT("y"), Next.ThresholdY);
		}
		if (Root->HasTypedField<EJson::Object>(TEXT("ceiling")))
		{
			const TSharedPtr<FJsonObject> C = Root->GetObjectField(TEXT("ceiling"));
			Next.CeilingLeft = C->HasField(TEXT("left")) ? static_cast<int32>(C->GetNumberField(TEXT("left"))) : 0;
			Next.CeilingAllow = C->HasField(TEXT("allow")) ? static_cast<int32>(C->GetNumberField(TEXT("allow"))) : 0;
			Next.CeilingWarn = C->HasField(TEXT("warn")) ? static_cast<int32>(C->GetNumberField(TEXT("warn"))) : 0;
			Next.bStoodDown = C->HasField(TEXT("stoodDown")) && C->GetBoolField(TEXT("stoodDown"));
		}
		if (Root->HasTypedField<EJson::Object>(TEXT("door")))
		{
			const TSharedPtr<FJsonObject> D = Root->GetObjectField(TEXT("door"));
			if (D->HasField(TEXT("finalizedTick"))) { Next.FinalizedTick = static_cast<int64>(D->GetNumberField(TEXT("finalizedTick"))); }
			if (D->HasField(TEXT("witnesses"))) { Next.Witnesses = static_cast<int32>(D->GetNumberField(TEXT("witnesses"))); }
			if (D->HasField(TEXT("quorum"))) { Next.Quorum = static_cast<int32>(D->GetNumberField(TEXT("quorum"))); }
			if (D->HasField(TEXT("keyFile"))) { KeyFile = D->GetStringField(TEXT("keyFile")); }
		}
		if (Root->HasTypedField<EJson::Object>(TEXT("sky")))
		{
			const TSharedPtr<FJsonObject> S = Root->GetObjectField(TEXT("sky"));
			auto Num = [&S](const TCHAR* Key, float Fallback)
			{
				double V = Fallback;
				S->TryGetNumberField(Key, V);
				return static_cast<float>(V);
			};
			Next.Sky.bValid = true;
			Next.Sky.ElevationDeg = Num(TEXT("elevDeg"), 45.f);
			Next.Sky.Bearing = Num(TEXT("bearing"), 180.f);
			Next.Sky.DayAmount = Num(TEXT("dayAmt"), 1.f);
			Next.Sky.Warm = Num(TEXT("warm"), 0.f);
			Next.Sky.Overcast = Num(TEXT("overcast"), 0.f);
			Next.Sky.Rain = Num(TEXT("rain"), 0.f);
			Next.Sky.Aurora = Num(TEXT("aurora"), 0.f);
			Next.Sky.Rainbow = Num(TEXT("rainbow"), 0.f);
			Next.Sky.Spring = Num(TEXT("spring"), 0.f);
			Next.Sky.Autumn = Num(TEXT("autumn"), 0.f);
			Next.Sky.Winter = Num(TEXT("winter"), 0.f);
			Next.Sky.DayFraction = Num(TEXT("dayF"), 0.f);
		}
		ParseEntityMap(Root, TEXT("players"), Next.Players);
		ParseEntityMap(Root, TEXT("mobs"), Next.Mobs);
		ParseEntityMap(Root, TEXT("nodes"), Next.Nodes);
		ParseEntityMap(Root, TEXT("ground"), Next.Ground);

		Frame = MoveTemp(Next);
		// ---- HOW LONG THAT ONE TOOK ----
		// Measured before the arrival time is overwritten, and smoothed hard:
		// what is wanted is the RATE intervals are arriving at, not the length
		// of the last one. See TickMeasured.
		{
			const double At = FPlatformTime::Seconds();
			if (FrameArrivedAt > 0.0)
			{
				const double Gap = At - FrameArrivedAt;
				// A frame that took between half and twice the world's own
				// tempo is an interval that was a little late or a little
				// early. Anything outside that is a stall or a catch-up burst
				// and says nothing about the rate.
				if (Gap > TickSeconds * 0.5 && Gap < TickSeconds * 2.0)
				{
					TickMeasured = FMath::Lerp(TickMeasured, Gap, 0.15);
					// AND HOW LATE THE LATE ONES ARE. Straight up to any gap
					// longer than the one being held, and a fiftieth of the way
					// back down otherwise -- about half a minute to forget a
					// stall that has stopped happening. A mean cannot do this
					// job: see `GetInterpAlpha`.
					TickSlowest = (Gap > TickSlowest)
						? Gap : FMath::Lerp(TickSlowest, Gap, 0.02);
				}
			}
			FrameArrivedAt = At;
		}
		OnFrame.Broadcast();

		// ---- AND TELL THE BRIDGE WHAT WE HAVE SEEN ----
		//
		// The world ticks once a second; an editor streaming a new region of
		// the island runs slower than that, and Unreal's websocket delivers a
		// limited number of messages per game tick. So the window falls behind
		// and never catches up -- eight hundred ticks, a quarter of an hour of
		// the world's history, queued up and being replayed one frame at a
		// time.
		//
		// The bridge cannot see this: it has written the bytes and the socket
		// has taken them, so nothing on its side looks backed up. Only the
		// window knows, so only the window can say. This is one small message
		// per frame applied, and `pushFrame` skips a tick for any window whose
		// last word was more than a few ticks ago.
		//
		// What it fixes is not smoothness. A window a quarter of an hour
		// behind files a walk, the world does it at once, and the window --
		// still watching fifteen minutes ago -- sees nothing happen and
		// reports that the world would not take it. Every deed looks refused.
		Say(FString::Printf(TEXT("{\"k\":\"seen\",\"tick\":%lld}"), Frame.Tick));
		return;
	}

	if (Kind == TEXT("terrain"))
	{
		FIntervalTerrainChunk Chunk;
		Root->TryGetNumberField(TEXT("x0"), Chunk.X0);
		Root->TryGetNumberField(TEXT("y0"), Chunk.Y0);
		Root->TryGetNumberField(TEXT("w"), Chunk.W);
		Root->TryGetNumberField(TEXT("h"), Chunk.H);
		Root->TryGetNumberField(TEXT("skirt"), Chunk.Skirt);
		DecodePlane(Root, TEXT("tiles"), Chunk.Tiles);
		DecodePlane(Root, TEXT("road"), Chunk.Ways);
		DecodePlane(Root, TEXT("ridge"), Chunk.Spine);
		DecodePlane(Root, TEXT("hash"), Chunk.Seeds);
		// A bridge that predates this plane sends none, and an empty one reads
		// as dry everywhere -- which draws the crossings the way they were
		// drawn before there were any, rather than gouging the banks.
		DecodePlane(Root, TEXT("wet"), Chunk.Wet);

		const int32 Expected = (Chunk.W + Chunk.Skirt * 2) * (Chunk.H + Chunk.Skirt * 2);
		if (Chunk.Tiles.Num() != Expected)
		{
			// A short plane would be drawn as a hole in the island, and a hole
			// looks exactly like terrain. Refuse it loudly instead.
			UE_LOG(LogIntervalBridge, Error, TEXT("chunk %d,%d is %d bytes for %d tiles, so it was dropped"),
				Chunk.X0, Chunk.Y0, Chunk.Tiles.Num(), Expected);
			return;
		}
		OnTerrainChunk.Broadcast(Chunk);
		return;
	}

	// WHAT THE BRIDGE DID WITH A CITIZEN. Not a refusal, because half of these
	// are successes, and the refusal channel was already carrying answers that
	// worked once (see the bridge's `enter`) and reading as failures.
	if (Kind == TEXT("carry"))
	{
		FString Of, Why;
		Root->TryGetStringField(TEXT("of"), Of);
		Root->TryGetStringField(TEXT("why"), Why);
		bCarryWorked = Root->HasField(TEXT("ok")) && Root->GetBoolField(TEXT("ok"));
		CarrySaid = Why;
		UE_LOG(LogIntervalBridge, Log, TEXT("carry %s: %s"), *Of, *Why);
		return;
	}

	if (Kind == TEXT("refused"))
	{
		FIntervalRefusal Refusal;
		Root->TryGetStringField(TEXT("of"), Refusal.Of);
		Root->TryGetStringField(TEXT("why"), Refusal.Why);
		double RefusedTick = 0.0;
		Root->TryGetNumberField(TEXT("tick"), RefusedTick);
		Refusal.Tick = static_cast<int64>(RefusedTick);
		Refusal.bOk = Root->HasField(TEXT("ok")) && Root->GetBoolField(TEXT("ok"));
		UE_LOG(LogIntervalBridge, Warning, TEXT("%s %s: %s"),
			Refusal.bOk ? TEXT("answered") : TEXT("refused"), *Refusal.Of, *Refusal.Why);
		OnRefused.Broadcast(Refusal);
		return;
	}

	if (Kind == TEXT("cry"))
	{
		FIntervalCry Cry;
		Cry.Text = Root->GetStringField(TEXT("text"));
		double CriedAt = 0.0;
		Root->TryGetNumberField(TEXT("tick"), CriedAt);
		Cry.Tick = static_cast<int64>(CriedAt);
		if (!Cry.Text.IsEmpty())
		{
			OnCry.Broadcast(Cry);
		}
		return;
	}

	if (Kind == TEXT("chat"))
	{
		FIntervalSaid Said;
		Said.SpeakerId = Root->GetStringField(TEXT("playerId"));
		Said.Name = Root->GetStringField(TEXT("name"));
		Said.Text = Root->GetStringField(TEXT("text"));
		Said.Calling = Root->HasField(TEXT("calling"))
			? Root->GetStringField(TEXT("calling")) : FString();
		Said.Place = Root->HasField(TEXT("place"))
			? Root->GetStringField(TEXT("place")) : FString();
		Said.Scope = Root->HasField(TEXT("scope"))
			? Root->GetStringField(TEXT("scope")) : FString(TEXT("near"));
		Said.Standing = Root->HasField(TEXT("standing"))
			? static_cast<int32>(Root->GetNumberField(TEXT("standing"))) : 0;
		Said.X = Root->HasField(TEXT("x"))
			? static_cast<int32>(Root->GetNumberField(TEXT("x"))) : 0;
		Said.Y = Root->HasField(TEXT("y"))
			? static_cast<int32>(Root->GetNumberField(TEXT("y"))) : 0;
		OnChat.Broadcast(Said);
		return;
	}
}

FString UIntervalBridgeSubsystem::GetTileName(uint8 Code) const
{
	return TileNames.IsValidIndex(Code) ? TileNames[Code] : FString();
}

float UIntervalBridgeSubsystem::GetTableNumber(const FString& Path, float Fallback) const
{
	if (!Tables.IsValid())
	{
		return Fallback;
	}

	TArray<FString> Parts;
	Path.ParseIntoArray(Parts, TEXT("."), true);
	TSharedPtr<FJsonObject> Cursor = Tables;

	for (int32 Index = 0; Index < Parts.Num(); ++Index)
	{
		const TSharedPtr<FJsonValue> Value = Cursor->TryGetField(Parts[Index]);
		if (!Value.IsValid())
		{
			return Fallback;
		}
		if (Index == Parts.Num() - 1)
		{
			return Value->Type == EJson::Number ? static_cast<float>(Value->AsNumber()) : Fallback;
		}
		if (Value->Type != EJson::Object)
		{
			return Fallback;
		}
		Cursor = Value->AsObject();
	}
	return Fallback;
}

FString UIntervalBridgeSubsystem::GetTableString(const FString& Path, const FString& Fallback) const
{
	if (!Tables.IsValid())
	{
		return Fallback;
	}

	TArray<FString> Parts;
	Path.ParseIntoArray(Parts, TEXT("."), true);
	TSharedPtr<FJsonObject> Cursor = Tables;

	for (int32 Index = 0; Index < Parts.Num(); ++Index)
	{
		const TSharedPtr<FJsonValue> Value = Cursor->TryGetField(Parts[Index]);
		if (!Value.IsValid())
		{
			return Fallback;
		}
		if (Index == Parts.Num() - 1)
		{
			return FlattenValue(Value);
		}
		if (Value->Type != EJson::Object)
		{
			return Fallback;
		}
		Cursor = Value->AsObject();
	}
	return Fallback;
}

float UIntervalBridgeSubsystem::GetInterpAlpha() const
{
	if (FrameArrivedAt <= 0.0)
	{
		return 0.f;
	}
	// Clamped, never extrapolated. A late interval holds the pose it has
	// rather than sliding a citizen into ground the world never put them on.
	//
	// AGAINST THE MEASURED RATE, NOT THE DECLARED ONE. Dividing by a flat
	// second meant a figure finished its whole tile's walk at exactly one
	// second and then STOOD STILL for however long the next frame was late --
	// a dead beat at the end of every stride, which is the specific way that
	// interpolated movement reads as stuttering rather than as walking. The
	// world's tempo is a thousand milliseconds; what a socket delivers is a
	// thousand and something, and it is the something that the eye sees.
	// AND LEANING LONG, because the two ways of being wrong are not equal.
	//
	// Running a little SLOW costs nothing: a stride that has not finished when
	// the next interval lands is simply redirected from wherever it had got to,
	// which is exactly what FIntervalStride was built to make safe. Running
	// fast costs a visible stop.
	//
	// THE MEAN WAS THE WRONG NUMBER TO STRETCH. This was `TickMeasured * 1.14`
	// -- an average of arrivals, leaned on by a seventh. Arrivals on this world
	// scatter from about 744 to 1032 milliseconds, and an average sits in the
	// middle of that by construction: a seventh of the way up from the middle
	// still falls short of the slowest arrivals, and EVERY one of those is a
	// figure reaching its tile and standing in it until the world speaks. That
	// is the "walks smoothly, then pauses, every tick" that survived the first
	// attempt at this, and it had to, because no multiple of a mean can
	// anticipate a tail.
	//
	// So it is sized against the slow tail instead, which is a number that
	// knows what it is for. `TickSlowest` jumps straight up to any gap longer
	// than itself and leaks back down slowly, so the span is comfortably past
	// where the next interval will land, and the clamp below is reached only
	// when an interval is slower than every interval of the last half minute.
	//
	// What it costs is that the figure walks a touch behind the world and
	// arrives a touch after it does. That is invisible; a dead stop is not.
	const double Span = FMath::Max(TickSlowest * 1.03, 0.05);
	const double Elapsed = FPlatformTime::Seconds() - FrameArrivedAt;
	return static_cast<float>(FMath::Clamp(Elapsed / Span, 0.0, 1.0));
}
