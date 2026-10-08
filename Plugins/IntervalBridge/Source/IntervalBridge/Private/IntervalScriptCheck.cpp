// A CONSOLE COMMAND THAT ASKS THE RULES WHO THEY ARE, from inside the editor.
//
// The whole argument of the iOS port is one number: `engine.js` is evaluated
// as text, byte for byte as it is on disk, so the SHA of those bytes is the
// same here as on a node and a founding made in this process names the same
// rules. Everything else -- the landscape, the bridge, the frames -- rests on
// that, and it is worth being able to ask for it in one line.
//
//   interval.js.check      in the editor's console
#include "IntervalScript.h"

#if INTERVAL_HAS_SCRIPT

#include "HAL/IConsoleManager.h"
#include "Containers/Ticker.h"
#include "Misc/Paths.h"

DEFINE_LOG_CATEGORY_STATIC(LogIntervalScriptCheck, Log, All);

static void IntervalScriptCheck(const TArray<FString>& Args)
{
	FIntervalScript& Script = FIntervalScript::Get();
	if (!Script.IsOpen())
	{
		UE_LOG(LogIntervalScriptCheck, Error,
			TEXT("no JavaScript context: is JavaScriptCore linked?"));
		return;
	}
	UE_LOG(LogIntervalScriptCheck, Display, TEXT("the world's files are in %s"),
		*FIntervalScript::SourceRoot());

	FString Error;
	if (!Script.Boot(Error))
	{
		UE_LOG(LogIntervalScriptCheck, Error, TEXT("%s"), *Error);
		return;
	}

	// ---- THE ONE NUMBER ----
	auto Ask = [&Script](const TCHAR* What, const TCHAR* Source)
	{
		FString Value, Why;
		if (Script.Eval(Source, TEXT("check.js"), Value, Why))
		{
			UE_LOG(LogIntervalScriptCheck, Display, TEXT("  %-22s %s"),
				What, *Value);
		}
		else
		{
			UE_LOG(LogIntervalScriptCheck, Error, TEXT("  %-22s %s"), What, *Why);
		}
	};

	Ask(TEXT("exports"), TEXT("Object.keys(__intervalEngine).length"));
	// ---- AND A CITIZEN, AND A DEED THEY SIGNED ----
	//
	// The hash proves the bytes; this proves the rules RUN and, more to the
	// point, that a citizen made in this process can act. A key is minted from
	// the kernel's randomness, a walk is signed with it, and the signature is
	// checked by the world's own verifier -- the same function a node runs
	// before it will take the deed.
	Ask(TEXT("a citizen, minted here"), TEXT(
		"(() => {"
		"  const E = __intervalEngine;"
		"  E.initCrypto && E.initCrypto();"
		"  globalThis.__me = E.generateIdentity();"
		"  return __me.playerId.slice(0, 16) + '…';"
		"})()"));
	Ask(TEXT("and a deed they signed"), TEXT(
		"(() => {"
		"  const E = __intervalEngine;"
		"  const input = E.signInput({ worldId: 'a4de408dc51d2528', tick: 1,"
		"    playerId: __me.playerId, ...E.normalizeInput("
		"      { type: 'walk', dx: 1, dy: 0, steps: 1 }) }, __me.privateKey);"
		"  globalThis.__deed = input;"
		"  return input.sig.slice(0, 16) + '…';"
		"})()"));
	Ask(TEXT("which the world accepts"), TEXT(
		"String(__intervalEngine.verifyInputSig(__deed))"));
	// AND PUT WHERE A NODE CAN BE ASKED THE SAME QUESTION. Unreal verifying
	// its own signature proves the two halves of this process agree with each
	// other and nothing more; the thing worth knowing is whether the WORLD
	// takes it, and the world is somewhere else.
	Ask(TEXT("written out for a node"), TEXT(
		"String(__write('portable/signed-in-unreal.json',"
		"  JSON.stringify({ playerId: __me.playerId, input: __deed }, null, 1)))"));
	Ask(TEXT("engine hash"), TEXT("__intervalEngine.engineHash()"));
	Ask(TEXT("generators"), TEXT("Object.keys(__intervalWorldgen).join(' ')"));

	// AND A FOUNDING -- BUT ONLY WHEN ASKED FOR IT.
	//
	// A hash that matches proves the bytes and nothing about whether the rules
	// RUN, so the obvious next thing is to found `expanse7` from the six public
	// values any node will hand over and compare the world id. It is also a
	// minute of work in Node and considerably more here, all of it on the game
	// thread, and while it runs the editor does not draw a frame.
	//
	// A client never founds anything -- it asks a node for the genesis -- so
	// this is a diagnostic and not a thing the app will ever do. It is behind
	// an argument for that reason:
	//
	//   interval.js.check found
	//
	// The day something in the app does need to found, it goes on a worker
	// thread or the app is a black screen for a minute.
	if (!Args.ContainsByPredicate([](const FString& A)
		{ return A.Equals(TEXT("found"), ESearchCase::IgnoreCase); }))
	{
		UE_LOG(LogIntervalScriptCheck, Display,
			TEXT("  (add `found` to also build the island, which takes a "
			     "while and stops the editor drawing while it does)"));
		return;
	}
	Ask(TEXT("expanse7 world id"), TEXT(
		"(() => {"
		"  const g = __intervalWorldgen.foundGenesis('interval-expanse-v7',"
		"    'solo-538',"
		"    '6cde7f4e2631a1af4ff405cb51d1bf78f66ba3ec83531d18adee6599d8ca1cdd',"
		"    1789813895202, 896, 512);"
		"  return __intervalEngine.worldId(g);"
		"})()"));
	Ask(TEXT("and the ground at 460,264"), TEXT(
		"(() => {"
		"  const g = __intervalWorldgen.foundGenesis('interval-expanse-v7',"
		"    'solo-538',"
		"    '6cde7f4e2631a1af4ff405cb51d1bf78f66ba3ec83531d18adee6599d8ca1cdd',"
		"    1789813895202, 896, 512);"
		"  const G = __intervalWorldgen.generatorFor(g);"
		"  return G.groundKindAt(g, 460, 264) ?? G.biomeAt(g, 460, 264);"
		"})()"));
}

// ---------------------------------------------------------------------------
// AND THE SAME CONTEXT, ASKING A REAL NODE.
//
// Everything above runs on files. This is the first thing in the port that
// leaves the machine: the world's own `fetch`, which is Unreal's HTTP module
// with a promise round it, pointed at whichever node the window is already
// talking to. It answers some frames later, so the reply is logged from the
// callback rather than returned.
//
//   interval.js.world [https://interval.place]
// ---------------------------------------------------------------------------
static void IntervalScriptWorld(const TArray<FString>& Args)
{
	FIntervalScript& Script = FIntervalScript::Get();
	if (!Script.IsOpen())
	{
		UE_LOG(LogIntervalScriptCheck, Error, TEXT("no JavaScript context"));
		return;
	}
	FString Error;
	if (!Script.Boot(Error))
	{
		UE_LOG(LogIntervalScriptCheck, Error, TEXT("%s"), *Error);
		return;
	}
	const FString Where = Args.Num() > 0 ? Args[0] : TEXT("https://interval.place");
	const FString Source = FString::Printf(TEXT(
		"(async () => {"
		"  const at = %s;"
		"  try {"
		"    const w = await (await fetch(at + '/api/world')).json();"
		"    print('the node at ' + at + ' says: world ' + String(w.worldId).slice(0, 12)"
		"      + '… tick ' + w.tick + ', ' + w.players + ' citizens, ' + w.mobs + ' beasts');"
		"    const g = await (await fetch(at + '/api/genesis')).json();"
		"    const G = g.genesis ?? g;"
		"    print('  and the founding: ' + G.worldGenerator + ' ' + G.worldW + 'x' + G.worldH"
		"      + ', seed ' + G.genesisSeed);"
		// THE BIOME AND NOT THE GROUND KIND, and the difference is a minute.
		//
		// `biomeAt` is arithmetic on the coordinates and answers instantly.
		// `groundKindAt` asks whether the tile is a road, a floor or a quay,
		// and to answer that for expanse7 it has to route every road on the
		// island -- a cost field over four hundred thousand tiles, computed
		// once and memoised. On the game thread that is the editor not drawing
		// a frame for a minute, which is exactly what it did the first time
		// this line was written.
		//
		// The real bridge never does this on a frame either: it answers the
		// window's terrain requests from a worker and the first one is slow.
		// When the in-process bridge arrives, that is the rule to keep.
		"    const gen = __intervalWorldgen.generatorFor(G);"
		"    print('  the country at 460,264 is ' + gen.biomeAt(G, 460, 264));"
		"  } catch (e) { print('the node would not answer: ' + (e && e.message || e)); }"
		"})()"),
		*FString::Printf(TEXT("'%s'"), *Where));
	FString Value, Why;
	if (!Script.Eval(Source, TEXT("world.js"), Value, Why))
	{
		UE_LOG(LogIntervalScriptCheck, Error, TEXT("%s"), *Why);
		return;
	}
	UE_LOG(LogIntervalScriptCheck, Display,
		TEXT("asked %s; the answer arrives in a moment, as [js] lines"), *Where);
}

// ---------------------------------------------------------------------------
// AND A SOCKET TO A NODE, which is the last thing the portable proof stood in
// for. The pillar answers an `adopt` with a `hello` and then sends the whole
// world, so the first two messages down the wire are the test: if they arrive
// and parse, the rules in this process are being fed by the world itself.
//
//   interval.js.dial [wss://interval.place]
// ---------------------------------------------------------------------------
static void IntervalScriptDial(const TArray<FString>& Args)
{
	FIntervalScript& Script = FIntervalScript::Get();
	FString Error;
	if (!Script.IsOpen() || !Script.Boot(Error))
	{
		UE_LOG(LogIntervalScriptCheck, Error, TEXT("%s"),
			Error.IsEmpty() ? TEXT("no JavaScript context") : *Error);
		return;
	}
	const FString Where = Args.Num() > 0 ? Args[0] : TEXT("wss://interval.place");
	const FString Source = FString::Printf(TEXT(
		"(() => {"
		"  const E = __intervalEngine;"
		"  E.initCrypto && E.initCrypto();"
		"  const me = E.generateIdentity();"
		"  let seen = 0;"
		"  const up = __dial('%s');"
		"  up.on('open', () => {"
		"    print('the socket opened; saying who we are');"
		"    up.send(JSON.stringify({ type: 'adopt', pub: me.playerId }));"
		"    up.send(JSON.stringify({ type: 'resync' }));"
		"  });"
		"  up.on('error', (why) => print('the socket would not open: ' + why));"
		"  up.on('close', (why) => print('the socket closed: ' + why));"
		"  up.on('message', (text) => {"
		"    let m; try { m = JSON.parse(text); } catch { return; }"
		"    seen++;"
		"    if (m.type === 'hello') {"
		"      print('  the node adopted us as ' + String(m.playerId).slice(0, 12) + '…');"
		"      return;"
		"    }"
		"    if (m.type === 'state') {"
		"      const s = m.state;"
		"      print('  and sent the world: tick ' + s.tick + ', '"
		"        + Object.keys(s.players || {}).length + ' citizens, '"
		"        + Object.keys(s.nodes || {}).length + ' things standing');"
		"      print('  which the rules read as world ' + String(E.worldId(s.genesis)).slice(0, 16) + '…');"
		"      up.close();"
		"      return;"
		"    }"
		"    if (seen < 4) { print('  it also said: ' + m.type); }"
		"  });"
		"})()"), *Where);
	FString Value, Why;
	if (!Script.Eval(Source, TEXT("dial.js"), Value, Why))
	{
		UE_LOG(LogIntervalScriptCheck, Error, TEXT("%s"), *Why);
		return;
	}
	UE_LOG(LogIntervalScriptCheck, Display,
		TEXT("dialling %s; what comes back arrives as [js] lines"), *Where);
}

// ---------------------------------------------------------------------------
// AND THE WHOLE BRIDGE, RUNNING HERE.
//
// Everything above proves a piece: the rules load, a key signs, the landscape
// comes out tile for tile the same, a node answers over HTTP, a socket opens.
// This runs `unreal-bridge.mjs` itself -- the same file the desktop runs, not
// a port of it -- with Unreal underneath it in place of Node, and listens to
// what comes out of the door.
//
// WHAT TO LOOK FOR. A `hello` first, with the citizen and the world's tables;
// then a frame a second, each one the island as it stands. If those arrive the
// desktop client needs no Node process either, and iOS is a packaging step.
//
// A CITIZEN OF ITS OWN, and that is deliberate. Pointing this at the key the
// Node bridge beside the editor is already using would have two bridges adopt
// one citizen at the same moment, which is not a thing the world is asked to
// make sense of.
//
//   interval.js.bridge [https://interval.place]
// ---------------------------------------------------------------------------
static FTSTicker::FDelegateHandle GBridgePump;
static int32 GFramesSeen = 0;
static int32 GNewestTick = -1;
static int32 GToldTick = -1;

/** The number after a `"name":` in a frame, or -1. Enough for a count. */
static int32 NumberAfter(const FString& Text, const TCHAR* Field)
{
	const FString Key = FString::Printf(TEXT("\"%s\":"), Field);
	int32 At = Text.Find(Key);
	if (At == INDEX_NONE)
	{
		return -1;
	}
	At += Key.Len();
	FString Digits;
	while (At < Text.Len() && FChar::IsDigit(Text[At]))
	{
		Digits.AppendChar(Text[At++]);
	}
	return Digits.IsEmpty() ? -1 : FCString::Atoi(*Digits);
}

static void IntervalScriptBridge(const TArray<FString>& Args)
{
	FIntervalScript& Script = FIntervalScript::Get();
	if (!Script.IsOpen())
	{
		UE_LOG(LogIntervalScriptCheck, Error, TEXT("no JavaScript context"));
		return;
	}
	if (Script.IsBridgeOpen())
	{
		FString State, Why;
		Script.Eval(TEXT("String(globalThis.__intervalBridgeState)"),
			TEXT("state.js"), State, Why);
		UE_LOG(LogIntervalScriptCheck, Display,
			TEXT("the bridge is already here (%s): %d frames so far, "
			     "newest tick %d"), *State, GFramesSeen, GNewestTick);
		return;
	}

	// WHAT THE BRIDGE IS TOLD, and it is the same three questions the desktop
	// answers off a command line.
	TMap<FString, FString> Options;
	Options.Add(TEXT("pillar"), Args.Num() > 0 ? Args[0] : TEXT("https://interval.place"));
	Options.Add(TEXT("key"), TEXT("unreal-key-inproc.json"));
	Options.Add(TEXT("port"), TEXT("0"));

	// LISTENING BEFORE IT IS OPEN, because `hello` goes out during the load.
	Script.OnFrame = [](const FString& Text)
	{
		GFramesSeen++;
		const int32 Tick = NumberAfter(Text, TEXT("tick"));
		if (Tick > GNewestTick)
		{
			GNewestTick = Tick;
		}
		// THE FIRST FEW AND THEN ONE A MINUTE -- BUT EVERYTHING THAT IS NOT A
		// FRAME, always. There is a frame a second for as long as the editor
		// is open and a log that prints all of them is a log nothing else can
		// be read in; the answers to the window's own questions, on the other
		// hand, are rare and are exactly what is being tested.
		const bool bOrdinary = Text.Contains(TEXT("\"k\":\"frame\""));
		if (!bOrdinary || GFramesSeen <= 3 || GFramesSeen % 60 == 0)
		{
			const int32 Cut = Text.Find(TEXT(","));
			UE_LOG(LogIntervalScriptCheck, Display,
				TEXT("frame %d: %d chars, %s, tick %d"), GFramesSeen, Text.Len(),
				*Text.Left(Cut > 0 ? Cut : 24), Tick);
		}
	};

	FString Error;
	if (!Script.OpenBridge(Options, Error))
	{
		Script.OnFrame = nullptr;
		UE_LOG(LogIntervalScriptCheck, Error, TEXT("the bridge would not open: %s"),
			*Error);
		return;
	}

	// AND THE CLOCK TURNS, which is the part that has no equivalent in the
	// engine: JavaScriptCore has no timers, so the world's tick is a game
	// thread tick calling a table. This also answers the bridge's stop-and-wait
	// -- it will send no second frame until the window says which tick it has
	// seen -- which the real window does for itself and this command has to do
	// by hand, one frame late so nothing re-enters the JavaScript from inside
	// a call that is already in it.
	if (!GBridgePump.IsValid())
	{
		GBridgePump = FTSTicker::GetCoreTicker().AddTicker(
			TEXT("interval.js.bridge"), 0.f, [](float) -> bool
			{
				FIntervalScript& S = FIntervalScript::Get();
				S.Pump();
				if (GNewestTick > GToldTick)
				{
					GToldTick = GNewestTick;
					S.ToBridge(FString::Printf(
						TEXT("{\"k\":\"seen\",\"tick\":%d}"), GToldTick));
				}
				return true;
			});
	}

	UE_LOG(LogIntervalScriptCheck, Display,
		TEXT("the bridge is up in this process, keyed on %s; what it says "
		     "arrives as [js] and frame lines"),
		*FPaths::Combine(FIntervalScript::SourceRoot(),
			TEXT("unreal-key-inproc.json")));
}

// ---------------------------------------------------------------------------
// AND A WAY TO SAY SOMETHING TO IT, which is the other half of the door.
//
// Whatever is typed is handed to the bridge exactly as the window's own
// requests are handed to it, so this is how a request can be tried before the
// renderer is wired to make it: a region of terrain, a tick seen, a deed.
//
//   interval.js.ask {"k":"terrain","x0":464,"y0":260,"w":8,"h":8,"skirt":1}
// ---------------------------------------------------------------------------
static void IntervalScriptAsk(const TArray<FString>& Args)
{
	FIntervalScript& Script = FIntervalScript::Get();
	if (!Script.IsBridgeOpen())
	{
		UE_LOG(LogIntervalScriptCheck, Error,
			TEXT("there is no bridge here; run interval.js.bridge first"));
		return;
	}
	// JOINED WITH SPACES, because the console splits on them and JSON has
	// none that matter. A request with a space inside a string would be the
	// exception and there is no such request.
	const FString Said = FString::Join(Args, TEXT(" "));
	if (Said.IsEmpty())
	{
		UE_LOG(LogIntervalScriptCheck, Error, TEXT("interval.js.ask <json>"));
		return;
	}
	UE_LOG(LogIntervalScriptCheck, Display, TEXT("%s -> the bridge %s"), *Said,
		Script.ToBridge(Said) ? TEXT("took it") : TEXT("would not take it"));
}

// ---------------------------------------------------------------------------
// AND A WAY TO ASK THE RULES A QUESTION IN THEIR OWN LANGUAGE.
//
// Everything else here is a rehearsed test. This is the one that is not: when
// something in the world's own JavaScript is not doing what it says, the
// question is usually one expression long and the alternative is a rebuild.
//
//   interval.js.eval globalThis.__intervalClock.count()
//   interval.js.eval globalThis.__intervalBridgeState
// ---------------------------------------------------------------------------
static void IntervalScriptEval(const TArray<FString>& Args)
{
	FIntervalScript& Script = FIntervalScript::Get();
	if (!Script.IsOpen())
	{
		UE_LOG(LogIntervalScriptCheck, Error, TEXT("no JavaScript context"));
		return;
	}
	const FString Question = FString::Join(Args, TEXT(" "));
	if (Question.IsEmpty())
	{
		UE_LOG(LogIntervalScriptCheck, Error, TEXT("interval.js.eval <expression>"));
		return;
	}
	FString Answer, Why;
	if (!Script.Eval(FString::Printf(TEXT("String(%s)"), *Question),
		TEXT("eval.js"), Answer, Why))
	{
		UE_LOG(LogIntervalScriptCheck, Error, TEXT("%s -> %s"), *Question, *Why);
		return;
	}
	UE_LOG(LogIntervalScriptCheck, Display, TEXT("%s -> %s"), *Question, *Answer);
}

static FAutoConsoleCommand GIntervalScriptEval(
	TEXT("interval.js.eval"),
	TEXT("Evaluate one expression in the world's own JavaScript."),
	FConsoleCommandWithArgsDelegate::CreateStatic(&IntervalScriptEval));

static FAutoConsoleCommand GIntervalScriptAsk(
	TEXT("interval.js.ask"),
	TEXT("Say to the in-process bridge exactly what the window would say."),
	FConsoleCommandWithArgsDelegate::CreateStatic(&IntervalScriptAsk));

static FAutoConsoleCommand GIntervalScriptBridge(
	TEXT("interval.js.bridge"),
	TEXT("Run the whole bridge inside this process, with no Node at all."),
	FConsoleCommandWithArgsDelegate::CreateStatic(&IntervalScriptBridge));

static FAutoConsoleCommand GIntervalScriptDial(
	TEXT("interval.js.dial"),
	TEXT("Open a socket to a node from the rules running in this process."),
	FConsoleCommandWithArgsDelegate::CreateStatic(&IntervalScriptDial));

static FAutoConsoleCommand GIntervalScriptWorld(
	TEXT("interval.js.world"),
	TEXT("Ask a node about the world, through the rules running in this process."),
	FConsoleCommandWithArgsDelegate::CreateStatic(&IntervalScriptWorld));

static FAutoConsoleCommand GIntervalScriptCheck(
	TEXT("interval.js.check"),
	TEXT("Load the world's own rules in this process and say who they are."),
	FConsoleCommandWithArgsDelegate::CreateStatic(&IntervalScriptCheck));

#endif
