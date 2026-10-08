// IntervalScript.h -- the world's own rules, running inside this process.
//
// WHAT THIS IS FOR. Everywhere else in this plugin the arrangement is one
// sentence: the bridge holds the key and all world knowledge, Unreal holds
// only pixels. On a desktop the bridge is a Node process beside the game and
// this module talks to it over a loopback socket. iOS will not have that --
// the platform will neither ship Node nor let an app start an interpreter --
// so on a phone the bridge has to run INSIDE the app, in the JavaScript engine
// the platform already has.
//
// That engine is JavaScriptCore, and macOS ships the same one. So this is
// written and debugged on a Mac, against a window that already works, and iOS
// becomes a packaging step rather than a debugging session on a cable.
//
// NOTHING ABOUT THE WORLD IS IN HERE. This class knows how to make a context,
// hand it the four things it cannot do for itself, and run a script. Every
// rule, every table and every tile stays in the JavaScript, exactly as it is
// on disk -- see interval-bridge/portable/README.md, where the whole bridge is
// already proven to run in this engine and to answer a window's first question
// with the same bytes a node sends.
//
// THE ENGINE'S SOURCE IS NEVER TRANSFORMED. It is read as text and evaluated
// as text, because the SHA of those bytes IS what a founding records about
// which rules made it. A build that bundled or transpiled it would be a
// different world, and would say so in the one number that matters.

#pragma once

#include "CoreMinimal.h"

#if PLATFORM_MAC || PLATFORM_IOS
#define INTERVAL_HAS_SCRIPT 1
#else
#define INTERVAL_HAS_SCRIPT 0
#endif

#if INTERVAL_HAS_SCRIPT

/**
 * One JavaScript context, with the handful of things a host has to provide.
 *
 * The list is closed and it is short, which is the whole reason this is worth
 * doing at all; see `install` in interval-bridge/portable/shim.js for why each
 * one is there. This class supplies the two that must come from the platform:
 * somewhere to print, and a way to read a file's text.
 */
class INTERVALBRIDGE_API FIntervalScript
{
public:
	FIntervalScript();
	~FIntervalScript();

	FIntervalScript(const FIntervalScript&) = delete;
	FIntervalScript& operator=(const FIntervalScript&) = delete;

	/** Whether a context was made. False means the framework is not there. */
	bool IsOpen() const { return Context != nullptr; }

	/**
	 * Run a piece of source. `Where` names it in a stack trace and nowhere
	 * else. Returns false and fills `OutError` when the script throws.
	 */
	bool Run(const FString& Source, const FString& Where, FString& OutError);

	/** Run it and give back whatever it evaluated to, as a string. */
	bool Eval(const FString& Source, const FString& Where, FString& OutValue,
		FString& OutError);

	/**
	 * WHERE THE WORLD'S OWN FILES ARE.
	 *
	 * On a desktop they are the repository beside the project, which is also
	 * what the packaged client copies into its `bridge` folder. On a phone
	 * they will be staged into the app; this is the one place that has to
	 * learn that, and it is a path and not an idea.
	 */
	static FString SourceRoot();

	/** The text of one of them, or empty. */
	static FString ReadSource(const FString& Name);

	/**
	 * THE ONE CONTEXT THIS SESSION HAS, made when it is first asked for.
	 *
	 * A context that lives on the stack cannot be given a `fetch`: an HTTP
	 * reply arrives some frames after it was asked for, and by then a stack
	 * context is gone and the callback it protected is a dangling reference.
	 * Anything that talks to a node therefore needs one that outlives the call
	 * that started it, and there is no reason to have two.
	 */
	static FIntervalScript& Get();

	/** Whether there is one yet, without making one. */
	static bool Exists();

	/**
	 * THE WHOLE WORLD, LOADED: the shim, the module loader, the rules and the
	 * landscape, in that order, out of the files on disk.
	 *
	 * Everything it needs is already installed by the constructor. Returns
	 * false with a reason when a file is missing or a script throws, which
	 * during a port is most of what is worth knowing.
	 */
	bool Boot(FString& OutError);

	/**
	 * THE WHOLE BRIDGE, RUNNING IN THIS PROCESS.
	 *
	 * Boots the rules if they are not up, installs the host that stands in for
	 * Node -- a setting, a file, the key, a socket, a clock, a door -- and then
	 * loads `unreal-bridge.mjs`, which is the same file the desktop runs, read
	 * off the disk and hoisted as it is.
	 *
	 * THIS TAKES AS LONG AS IT TAKES. Loading the bridge asks a node for the
	 * founding and then builds the island from it: fifteen settlements, five
	 * thousand tiles of road, every field and every holding. On this machine
	 * that is the better part of a minute, and it happens on whichever thread
	 * calls this. That is the one thing still wrong with it and it is a
	 * scheduling problem, not a correctness one.
	 *
	 * `Options` are what `HOST.option` answers with: `pillar` (the node),
	 * `key` (the citizen's file), `port` (which in this process is ignored).
	 */
	bool OpenBridge(const TMap<FString, FString>& Options, FString& OutError);

	/** Whether the bridge is up in this context. */
	bool IsBridgeOpen() const { return bBridgeOpen; }

	/**
	 * WHAT THE WINDOW SAYS, HANDED TO THE BRIDGE.
	 *
	 * Exactly the JSON the window used to write into a loopback socket: a
	 * region of terrain, a tick it has seen, a deed, a line of chat. Returns
	 * false when there is no bridge to say it to.
	 */
	bool ToBridge(const FString& Text);

	/**
	 * WHAT THE BRIDGE SAYS, HANDED TO WHOEVER IS DRAWING.
	 *
	 * Set by the subsystem. Called on the game thread, inside whatever call
	 * made the bridge speak -- a timer running out, a socket delivering a
	 * patch, the window asking for terrain -- so it must not be slow and must
	 * not re-enter `ToBridge`.
	 */
	TFunction<void(const FString&)> OnFrame;

	/** Called by the native `__toWindow`, and by nothing else. */
	void TakeFrame(const FString& Text);

	/**
	 * THE CLOCK, TURNED ONCE.
	 *
	 * JavaScriptCore has no timers: they belong to whatever pumps the event
	 * loop, which in a browser is the browser and here is the game thread.
	 * Call this once a frame. Returns how many timers fired, which is normally
	 * nought and once a second is one.
	 */
	int32 Pump();

private:
	void* Context = nullptr;

	/** `print` and a `console`, so the generator's own counting can be heard. */
	void InstallSay();

	/** `readFile`, which is how the rules and the landscape get in. */
	void InstallRead();

	/**
	 * `__fetch`, which is how the rules reach a node.
	 *
	 * The bridge asks a node five questions before it draws anything -- the
	 * founding, the tables, the settlements, the roads and the tick -- and
	 * every one of them is a `fetch`. JavaScriptCore has no networking at all,
	 * so this is Unreal's HTTP module with a promise around it.
	 */
	void InstallFetch();

	/**
	 * `__wsOpen`, `__wsSend`, `__wsClose`: a socket to a node.
	 *
	 * The bridge dials a pillar and then lives on what comes down it -- a
	 * snapshot, then a patch every tick, for as long as the window is open.
	 * JavaScriptCore has no networking, so this is Unreal's WebSockets module
	 * with the `ws` package's shape put round it in JavaScript, because that
	 * is the shape `unreal-bridge.mjs` already calls.
	 */
	void InstallSockets();

	/**
	 * `__toWindow`, which is the door in with no door.
	 *
	 * On a desktop the window is a separate program and knocks on a loopback
	 * socket. In this process the window and the bridge are the same program,
	 * so there is nothing to listen on: the bridge's `send` lands here.
	 */
	void InstallDoor();

	/** Whether Boot has already run in this context. */
	bool bBooted = false;

	/** Whether `unreal-bridge.mjs` has been loaded in this context. */
	bool bBridgeOpen = false;
};

#endif
