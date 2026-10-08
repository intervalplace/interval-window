#include "IntervalScript.h"

#if INTERVAL_HAS_SCRIPT

#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/PlatformFileManager.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "WebSocketsModule.h"
#include "IWebSocket.h"

// ---- APPLE'S HEADERS, BEHIND THE ENGINE'S OWN GUARDS ----
//
// CarbonCore defines a struct called `FVector`, Unreal has a type of that
// name, and including a framework that reaches CoreServices makes the build
// fail inside `NumberFormatting.h` -- about a name nobody here used, from a
// header nobody here asked for. `PreAppleSystemHeaders.h` exists for exactly
// this class of collision and is what every engine module that touches a
// system framework uses.
#include "Apple/PreAppleSystemHeaders.h"

// AND ONE NAME PUT OUT OF THE WAY BY HAND. The engine's guards save the macros
// mach-o redefines; they do not know about this one. CarbonCore declares
// `struct FVector` -- a Carbon numeric formatting type, nothing to do with
// geometry -- and Unreal's `FVector` is a type alias by the time this file is
// compiled, so the two meet and the build stops in a header neither of them
// asked for. Renaming Carbon's for the length of the include is the whole fix,
// and it is undone immediately after.
#pragma push_macro("FVector")
#define FVector FVector_CarbonCore

THIRD_PARTY_INCLUDES_START
// THE C HEADERS, NOT THE UMBRELLA. `<JavaScriptCore/JavaScriptCore.h>` is the
// framework's front door and it brings CoreServices in behind it -- and
// CarbonCore defines a struct called `FVector`, which Unreal also has. The
// build then fails inside `NumberFormatting.h`, about a name nobody here used,
// from a header nobody here asked for.
//
// The C interface is six headers and needs none of that.
#include <JavaScriptCore/JSBase.h>
#include <JavaScriptCore/JSContextRef.h>
#include <JavaScriptCore/JSStringRef.h>
#include <JavaScriptCore/JSValueRef.h>
#include <JavaScriptCore/JSObjectRef.h>
#include <JavaScriptCore/JSTypedArray.h>
// ---- THE TWO THINGS A PHONE ALREADY DOES BETTER THAN JAVASCRIPT ----
//
// The rules hash constantly -- a world's identity, a deed's signature, the
// scatter plane, every keeper's name -- and `engine.js` says out loud that it
// prefers a native digest where there is one and falls back to a pure-JS
// implementation where there is not. On Apple platforms there is one, in a
// header that needs no framework at all.
//
// And randomness. A key minted from a weak source is a citizen somebody else
// can become, so there is no fallback anywhere in this port: the host either
// supplies a real one or key minting throws. `/dev/urandom` is the kernel's,
// on both platforms, and needs nothing linked.
// DECLARED, NOT INCLUDED. `<CommonCrypto/CommonDigest.h>` drags in CarbonCore,
// which defines a struct called `FVector` -- and Unreal has one of those. The
// build fails with "definition of type 'FVector' conflicts with type alias of
// the same name", from a header nobody here asked for, about a name nobody
// here used. These two symbols are in libSystem on both platforms and have
// been stable for fifteen years; naming them is cheaper than fighting Carbon.
extern "C" unsigned char* CC_SHA256(const void* Data, uint32 Len, unsigned char* Md);
extern "C" unsigned char* CC_SHA512(const void* Data, uint32 Len, unsigned char* Md);
#include <stdio.h>
THIRD_PARTY_INCLUDES_END
#undef FVector
#pragma pop_macro("FVector")
#include "Apple/PostAppleSystemHeaders.h"

static constexpr size_t kSha256Bytes = 32;
static constexpr size_t kSha512Bytes = 64;

DEFINE_LOG_CATEGORY_STATIC(LogIntervalScript, Log, All);

// ---------------------------------------------------------------------------
// STRINGS, WHICH ARE THE WHOLE OF THE FRICTION IN THIS API.
//
// JavaScriptCore's C interface passes every name and every piece of source as
// a reference-counted JSStringRef, and every one of them has to be released.
// A leak here is a leak of every script ever run, so they are wrapped once and
// never handled loose.
// ---------------------------------------------------------------------------
namespace
{
	struct FJsString
	{
		JSStringRef Ref = nullptr;
		explicit FJsString(const FString& In)
		{
			Ref = JSStringCreateWithUTF8CString(TCHAR_TO_UTF8(*In));
		}
		~FJsString() { if (Ref) { JSStringRelease(Ref); } }
		operator JSStringRef() const { return Ref; }
	};

	/** A JSValue as an FString, whatever it happens to be. */
	FString AsString(JSContextRef Ctx, JSValueRef Value)
	{
		if (!Value)
		{
			return FString();
		}
		JSStringRef Str = JSValueToStringCopy(Ctx, Value, nullptr);
		if (!Str)
		{
			return FString();
		}
		const size_t Size = JSStringGetMaximumUTF8CStringSize(Str);
		TArray<char> Buffer;
		Buffer.SetNumUninitialized(static_cast<int32>(Size));
		JSStringGetUTF8CString(Str, Buffer.GetData(), Size);
		JSStringRelease(Str);
		return FString(UTF8_TO_TCHAR(Buffer.GetData()));
	}

	/** An exception, with the line it came from where there is one. */
	FString AsError(JSContextRef Ctx, JSValueRef Thrown)
	{
		FString Text = AsString(Ctx, Thrown);
		if (!JSValueIsObject(Ctx, Thrown))
		{
			return Text;
		}
		JSObjectRef Obj = JSValueToObject(Ctx, Thrown, nullptr);
		auto Field = [&](const TCHAR* Name) -> FString
		{
			FJsString Key(Name);
			JSValueRef V = JSObjectGetProperty(Ctx, Obj, Key, nullptr);
			return (V && !JSValueIsUndefined(Ctx, V)) ? AsString(Ctx, V) : FString();
		};
		const FString Where = Field(TEXT("sourceURL"));
		const FString Line = Field(TEXT("line"));
		if (!Where.IsEmpty())
		{
			Text += FString::Printf(TEXT("  (%s:%s)"), *Where, *Line);
		}
		const FString Stack = Field(TEXT("stack"));
		if (!Stack.IsEmpty())
		{
			Text += TEXT("\n") + Stack;
		}
		return Text;
	}

	void Define(JSContextRef Ctx, const TCHAR* Name, JSObjectCallAsFunctionCallback Fn)
	{
		JSObjectRef Global = JSContextGetGlobalObject(Ctx);
		FJsString Key(Name);
		JSObjectRef Func = JSObjectMakeFunctionWithCallback(Ctx, Key, Fn);
		JSObjectSetProperty(Ctx, Global, Key, Func,
			kJSPropertyAttributeDontDelete, nullptr);
	}

	// ---- print, and a console that forwards to it ----
	//
	// The RULES never say anything. The LANDSCAPE does: it counts the scenes it
	// laid, the residents who had nowhere to stand and the fields it could not
	// finish, and it says so through `console.warn`. Those lines are worth
	// having in the editor's log, where they sit beside everything else this
	// window says about the world it is drawing.
	JSValueRef SayFn(JSContextRef Ctx, JSObjectRef, JSObjectRef,
		size_t Count, const JSValueRef Args[], JSValueRef*)
	{
		FString Line;
		for (size_t i = 0; i < Count; ++i)
		{
			if (i > 0) { Line += TEXT(" "); }
			Line += AsString(Ctx, Args[i]);
		}
		UE_LOG(LogIntervalScript, Log, TEXT("[js] %s"), *Line);
		return JSValueMakeUndefined(Ctx);
	}

	// ---- the digest, in the platform's own hands ----
	//
	// `__digest(bits, bytes)` -> bytes. The shim wires this in as the two
	// functions `@noble/hashes/sha2.js` would have exported, so `engine.js`
	// takes the path it already takes on a node and nothing in the rules knows
	// the difference. SHA-256 is SHA-256; the answer is the same or one of the
	// two implementations is wrong.
	JSValueRef DigestFn(JSContextRef Ctx, JSObjectRef, JSObjectRef,
		size_t Count, const JSValueRef Args[], JSValueRef* Thrown)
	{
		auto Fail = [&](const TCHAR* Why) -> JSValueRef
		{
			FJsString Msg(Why);
			JSValueRef One[1] = { JSValueMakeString(Ctx, Msg) };
			*Thrown = JSObjectMakeError(Ctx, 1, One, nullptr);
			return JSValueMakeUndefined(Ctx);
		};
		if (Count < 2)
		{
			return Fail(TEXT("__digest wants the bit width and the bytes"));
		}
		const int32 Bits = static_cast<int32>(JSValueToNumber(Ctx, Args[0], nullptr));
		JSObjectRef In = JSValueToObject(Ctx, Args[1], nullptr);
		if (!In || JSValueGetTypedArrayType(Ctx, Args[1], nullptr)
			== kJSTypedArrayTypeNone)
		{
			return Fail(TEXT("__digest wants a Uint8Array"));
		}
		const size_t Length = JSObjectGetTypedArrayByteLength(Ctx, In, nullptr);
		const uint8* Bytes = static_cast<const uint8*>(
			JSObjectGetTypedArrayBytesPtr(Ctx, In, nullptr));
		const size_t OutLen = (Bits == 512) ? kSha512Bytes : kSha256Bytes;
		// Copied into a buffer JavaScriptCore owns, because a no-copy array
		// over a stack buffer outlives the stack.
		JSObjectRef Out = JSObjectMakeTypedArray(Ctx, kJSTypedArrayTypeUint8Array,
			OutLen, nullptr);
		uint8* Dest = static_cast<uint8*>(
			JSObjectGetTypedArrayBytesPtr(Ctx, Out, nullptr));
		if (Bits == 512)
		{
			CC_SHA512(Bytes, static_cast<uint32>(Length), Dest);
		}
		else
		{
			CC_SHA256(Bytes, static_cast<uint32>(Length), Dest);
		}
		return Out;
	}

	// ---- randomness, from the kernel and from nowhere else ----
	JSValueRef EntropyFn(JSContextRef Ctx, JSObjectRef, JSObjectRef,
		size_t Count, const JSValueRef Args[], JSValueRef* Thrown)
	{
		auto Fail = [&](const TCHAR* Why) -> JSValueRef
		{
			FJsString Msg(Why);
			JSValueRef One[1] = { JSValueMakeString(Ctx, Msg) };
			*Thrown = JSObjectMakeError(Ctx, 1, One, nullptr);
			return JSValueMakeUndefined(Ctx);
		};
		if (Count < 1)
		{
			return Fail(TEXT("__entropy wants a Uint8Array to fill"));
		}
		JSObjectRef Arr = JSValueToObject(Ctx, Args[0], nullptr);
		if (!Arr || JSValueGetTypedArrayType(Ctx, Args[0], nullptr)
			== kJSTypedArrayTypeNone)
		{
			return Fail(TEXT("__entropy wants a Uint8Array"));
		}
		const size_t Length = JSObjectGetTypedArrayByteLength(Ctx, Arr, nullptr);
		uint8* Dest = static_cast<uint8*>(
			JSObjectGetTypedArrayBytesPtr(Ctx, Arr, nullptr));
		FILE* Urandom = fopen("/dev/urandom", "rb");
		if (!Urandom)
		{
			return Fail(TEXT("no /dev/urandom: refusing to invent entropy for "
			                 "a key, which would be a citizen anybody can be"));
		}
		const size_t Got = fread(Dest, 1, Length, Urandom);
		fclose(Urandom);
		if (Got != Length)
		{
			return Fail(TEXT("/dev/urandom gave short measure"));
		}
		return Args[0];
	}

	// ---- fetch, which is Unreal's HTTP module with a promise round it ----
	//
	// `__fetch(url, done)` and the promise is built in JavaScript, where a
	// promise belongs. The callback is PROTECTED for as long as the request is
	// in flight: JavaScriptCore collects anything it cannot see a reference
	// to, and a reply that arrives forty frames later would otherwise call a
	// function that has been swept.
	//
	// AND IT ANSWERS ON THE GAME THREAD, which is not a detail. A JSC context
	// is not thread-safe and every other call into this one comes from the
	// game thread; Unreal's HTTP completion delegate fires there too, so the
	// two never meet anywhere else.
	JSValueRef FetchFn(JSContextRef Ctx, JSObjectRef, JSObjectRef,
		size_t Count, const JSValueRef Args[], JSValueRef* Thrown)
	{
		if (Count < 2 || !JSValueIsObject(Ctx, Args[1]))
		{
			FJsString Msg(TEXT("__fetch wants a url and a callback"));
			JSValueRef One[1] = { JSValueMakeString(Ctx, Msg) };
			*Thrown = JSObjectMakeError(Ctx, 1, One, nullptr);
			return JSValueMakeUndefined(Ctx);
		}
		const FString Url = AsString(Ctx, Args[0]);
		JSObjectRef Done = JSValueToObject(Ctx, Args[1], nullptr);
		JSGlobalContextRef Global = JSContextGetGlobalContext(Ctx);
		JSValueProtect(Global, Done);
		JSGlobalContextRetain(Global);

		TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request =
			FHttpModule::Get().CreateRequest();
		Request->SetURL(Url);
		Request->SetVerb(TEXT("GET"));
		Request->SetHeader(TEXT("Accept"), TEXT("application/json"));
		Request->OnProcessRequestComplete().BindLambda(
			[Global, Done, Url](FHttpRequestPtr, FHttpResponsePtr Response,
				bool bConnected)
			{
				const int32 Status = Response.IsValid()
					? Response->GetResponseCode() : 0;
				const FString Body = Response.IsValid()
					? Response->GetContentAsString() : FString();
				JSValueRef CallArgs[3] = {
					JSValueMakeBoolean(Global, bConnected && Response.IsValid()),
					JSValueMakeNumber(Global, static_cast<double>(Status)),
					JSValueMakeString(Global, FJsString(Body)),
				};
				JSValueRef Threw = nullptr;
				JSObjectCallAsFunction(Global, Done, nullptr, 3, CallArgs, &Threw);
				if (Threw)
				{
					UE_LOG(LogIntervalScript, Error, TEXT("fetch %s: %s"),
						*Url, *AsError(Global, Threw));
				}
				JSValueUnprotect(Global, Done);
				JSGlobalContextRelease(Global);
			});
		Request->ProcessRequest();
		return JSValueMakeUndefined(Ctx);
	}

	// ---- a socket to a node ----
	//
	// KEPT IN C++ AND NAMED BY A NUMBER. The alternative is handing a pointer
	// to JavaScript inside an object, and a JavaScript object that owns a
	// native socket is a socket whose lifetime is decided by a garbage
	// collector. A number cannot be dereferenced by accident, and the map is
	// the one place a socket is closed.
	struct FDialled
	{
		TSharedPtr<IWebSocket> Socket;
	};
	TMap<int32, FDialled> GDialled;
	int32 GNextDialled = 1;

	/** Hand an event up to the JavaScript that is wearing this socket. */
	void Tell(JSGlobalContextRef Ctx, int32 Id, const TCHAR* Kind,
		const FString& Payload)
	{
		JSObjectRef Global = JSContextGetGlobalObject(Ctx);
		FJsString Name(TEXT("__wsEvent"));
		JSValueRef Fn = JSObjectGetProperty(Ctx, Global, Name, nullptr);
		if (!Fn || !JSValueIsObject(Ctx, Fn))
		{
			return;
		}
		JSObjectRef Call = JSValueToObject(Ctx, Fn, nullptr);
		FJsString KindStr(Kind);
		FJsString PayloadStr(Payload);
		JSValueRef Args[3] = {
			JSValueMakeNumber(Ctx, static_cast<double>(Id)),
			JSValueMakeString(Ctx, KindStr),
			JSValueMakeString(Ctx, PayloadStr),
		};
		JSValueRef Threw = nullptr;
		JSObjectCallAsFunction(Ctx, Call, nullptr, 3, Args, &Threw);
		if (Threw)
		{
			UE_LOG(LogIntervalScript, Error, TEXT("socket %d %s: %s"),
				Id, Kind, *AsError(Ctx, Threw));
		}
	}

	JSValueRef DialFn(JSContextRef Ctx, JSObjectRef, JSObjectRef,
		size_t Count, const JSValueRef Args[], JSValueRef* Thrown)
	{
		if (Count < 1)
		{
			FJsString Msg(TEXT("__wsOpen wants a url"));
			JSValueRef One[1] = { JSValueMakeString(Ctx, Msg) };
			*Thrown = JSObjectMakeError(Ctx, 1, One, nullptr);
			return JSValueMakeUndefined(Ctx);
		}
		const FString Url = AsString(Ctx, Args[0]);
		JSGlobalContextRef Global = JSContextGetGlobalContext(Ctx);

		// THE MODULE HAS TO BE LOADED BEFORE IT IS USED, and it is not loaded
		// by default in every configuration. Asking for it here costs nothing
		// twice and is the difference between a socket and a crash.
		if (!FModuleManager::Get().IsModuleLoaded(TEXT("WebSockets")))
		{
			FModuleManager::Get().LoadModule(TEXT("WebSockets"));
		}
		TSharedPtr<IWebSocket> Socket =
			FWebSocketsModule::Get().CreateWebSocket(Url, TEXT(""));
		if (!Socket.IsValid())
		{
			FJsString Msg(TEXT("could not make a socket"));
			JSValueRef One[1] = { JSValueMakeString(Ctx, Msg) };
			*Thrown = JSObjectMakeError(Ctx, 1, One, nullptr);
			return JSValueMakeUndefined(Ctx);
		}
		const int32 Id = GNextDialled++;
		GDialled.Add(Id, FDialled{ Socket });
		JSGlobalContextRetain(Global);

		Socket->OnConnected().AddLambda([Global, Id]()
		{
			Tell(Global, Id, TEXT("open"), FString());
		});
		Socket->OnConnectionError().AddLambda([Global, Id](const FString& Why)
		{
			Tell(Global, Id, TEXT("error"), Why);
		});
		Socket->OnMessage().AddLambda([Global, Id](const FString& Message)
		{
			Tell(Global, Id, TEXT("message"), Message);
		});
		Socket->OnClosed().AddLambda([Global, Id](int32 Code,
			const FString& Why, bool)
		{
			Tell(Global, Id, TEXT("close"), FString::Printf(TEXT("%d %s"), Code, *Why));
			GDialled.Remove(Id);
			JSGlobalContextRelease(Global);
		});
		Socket->Connect();
		return JSValueMakeNumber(Ctx, static_cast<double>(Id));
	}

	JSValueRef SendFn(JSContextRef Ctx, JSObjectRef, JSObjectRef,
		size_t Count, const JSValueRef Args[], JSValueRef*)
	{
		if (Count < 2)
		{
			return JSValueMakeBoolean(Ctx, false);
		}
		const int32 Id = static_cast<int32>(JSValueToNumber(Ctx, Args[0], nullptr));
		FDialled* Found = GDialled.Find(Id);
		if (!Found || !Found->Socket.IsValid() || !Found->Socket->IsConnected())
		{
			return JSValueMakeBoolean(Ctx, false);
		}
		Found->Socket->Send(AsString(Ctx, Args[1]));
		return JSValueMakeBoolean(Ctx, true);
	}

	JSValueRef ShutFn(JSContextRef Ctx, JSObjectRef, JSObjectRef,
		size_t Count, const JSValueRef Args[], JSValueRef*)
	{
		if (Count < 1)
		{
			return JSValueMakeUndefined(Ctx);
		}
		const int32 Id = static_cast<int32>(JSValueToNumber(Ctx, Args[0], nullptr));
		if (FDialled* Found = GDialled.Find(Id))
		{
			if (Found->Socket.IsValid())
			{
				Found->Socket->Close();
			}
		}
		return JSValueMakeUndefined(Ctx);
	}

	// ---- the door in, which in this process is not a door ----
	//
	// `__toWindow(text)` -- one frame of the world, as the bridge wrote it.
	//
	// THE STRING IS NOT SHORTENED AND THE SHAPE IS NOT CHANGED. The bridge
	// could have handed an object across instead of JSON, since there is no
	// wire between here and the renderer any more, and it does not: the window
	// parses the same bytes it has always parsed, so there is one bridge and
	// one window and the arrangement that is proven is the one that runs. The
	// cost is a parse the desktop was already paying.
	JSValueRef ToWindowFn(JSContextRef Ctx, JSObjectRef, JSObjectRef,
		size_t Count, const JSValueRef Args[], JSValueRef*)
	{
		if (Count < 1)
		{
			return JSValueMakeBoolean(Ctx, false);
		}
		FIntervalScript::Get().TakeFrame(AsString(Ctx, Args[0]));
		return JSValueMakeBoolean(Ctx, true);
	}

	// ---- writeFile ----
	//
	// One thing a citizen owns has to survive the app being closed, and it is
	// the key: it IS the citizen, there is nobody to ask for it back, and a
	// window that could not keep it would mint a new person every launch. On a
	// phone this becomes the keychain; here it is a file beside the world's
	// own, under the project and nowhere else.
	JSValueRef WriteFn(JSContextRef Ctx, JSObjectRef, JSObjectRef,
		size_t Count, const JSValueRef Args[], JSValueRef* Thrown)
	{
		if (Count < 2)
		{
			FJsString Msg(TEXT("__write wants a name and some text"));
			JSValueRef One[1] = { JSValueMakeString(Ctx, Msg) };
			*Thrown = JSObjectMakeError(Ctx, 1, One, nullptr);
			return JSValueMakeUndefined(Ctx);
		}
		FString Name = AsString(Ctx, Args[0]);
		Name.RemoveFromStart(TEXT("./"));
		// UNDER THE ROOT AND NOWHERE ELSE. A name with a `..` in it is the
		// difference between a key file and anything on the disk.
		if (Name.Contains(TEXT("..")) || Name.StartsWith(TEXT("/")))
		{
			FJsString Msg(TEXT("__write will not leave the world's own folder"));
			JSValueRef One[1] = { JSValueMakeString(Ctx, Msg) };
			*Thrown = JSObjectMakeError(Ctx, 1, One, nullptr);
			return JSValueMakeUndefined(Ctx);
		}
		const FString Path = FPaths::Combine(FIntervalScript::SourceRoot(), Name);
		const FString Text = AsString(Ctx, Args[1]);
		const bool bOk = FFileHelper::SaveStringToFile(Text, *Path);
		return JSValueMakeBoolean(Ctx, bOk);
	}

	// ---- readFile ----
	//
	// The one thing `portable/boot.mjs` asks for by name. Under the `jsc`
	// shell it is the shell's own; here it is this.
	JSValueRef ReadFn(JSContextRef Ctx, JSObjectRef, JSObjectRef,
		size_t Count, const JSValueRef Args[], JSValueRef* Thrown)
	{
		if (Count < 1)
		{
			return JSValueMakeUndefined(Ctx);
		}
		const FString Name = AsString(Ctx, Args[0]);
		const FString Text = FIntervalScript::ReadSource(Name);
		if (Text.IsEmpty())
		{
			// SAID, NOT SWALLOWED. A missing file that comes back as an empty
			// string is a module that evaluates to nothing and fails later
			// somewhere else entirely.
			const FString Message = FString::Printf(
				TEXT("no such source: %s (looked in %s)"),
				*Name, *FIntervalScript::SourceRoot());
			FJsString Msg(Message);
			JSValueRef Args1[1] = { JSValueMakeString(Ctx, Msg) };
			*Thrown = JSObjectMakeError(Ctx, 1, Args1, nullptr);
			return JSValueMakeUndefined(Ctx);
		}
		FJsString Out(Text);
		return JSValueMakeString(Ctx, Out);
	}
}

FIntervalScript::FIntervalScript()
{
	// A context group of its own, so nothing here shares a heap or a lock with
	// anything else that might one day want a JavaScript engine in this app.
	JSGlobalContextRef Ctx = JSGlobalContextCreate(nullptr);
	if (!Ctx)
	{
		UE_LOG(LogIntervalScript, Error,
			TEXT("JavaScriptCore would not make a context"));
		return;
	}
	Context = Ctx;
	InstallSay();
	InstallRead();
	Define(static_cast<JSContextRef>(Context), TEXT("__digest"), &DigestFn);
	Define(static_cast<JSContextRef>(Context), TEXT("__entropy"), &EntropyFn);
	Define(static_cast<JSContextRef>(Context), TEXT("__write"), &WriteFn);
	InstallFetch();
	InstallSockets();
	InstallDoor();
}

FIntervalScript::~FIntervalScript()
{
	if (Context)
	{
		JSGlobalContextRelease(static_cast<JSGlobalContextRef>(Context));
		Context = nullptr;
	}
}

void FIntervalScript::InstallSay()
{
	JSContextRef Ctx = static_cast<JSContextRef>(Context);
	Define(Ctx, TEXT("print"), &SayFn);
	FString Ignored;
	// A console in JavaScript rather than four more native functions: it is
	// the same forwarding either way and this one can be read.
	Run(TEXT("globalThis.console = globalThis.console || {"
	         "  log: (...a) => print(...a), warn: (...a) => print(...a),"
	         "  error: (...a) => print(...a), info: (...a) => print(...a),"
	         "  debug: () => {} };"),
		TEXT("console.js"), Ignored);
}

void FIntervalScript::InstallRead()
{
	Define(static_cast<JSContextRef>(Context), TEXT("readFile"), &ReadFn);
}

void FIntervalScript::InstallFetch()
{
	JSContextRef Ctx = static_cast<JSContextRef>(Context);
	Define(Ctx, TEXT("__fetch"), &FetchFn);
	FString Ignored;
	// THE PROMISE IS BUILT IN JAVASCRIPT, where a promise belongs, and it is
	// the shape the bridge already calls: `fetch(url)` giving something with
	// `ok`, `status` and `json()`. Nothing in the world's own code learns that
	// it is running inside a game.
	Run(TEXT(
		"globalThis.fetch = (url) => new Promise((resolve, reject) => {"
		"  __fetch(String(url), (reached, status, body) => {"
		"    if (!reached) { reject(new Error('could not reach ' + url)); return; }"
		"    resolve({ ok: status >= 200 && status < 300, status, url: String(url),"
		"      text: async () => body,"
		"      json: async () => JSON.parse(body) });"
		"  });"
		"});"),
		TEXT("fetch.js"), Ignored);
}

void FIntervalScript::InstallSockets()
{
	JSContextRef Ctx = static_cast<JSContextRef>(Context);
	Define(Ctx, TEXT("__wsOpen"), &DialFn);
	Define(Ctx, TEXT("__wsSend"), &SendFn);
	Define(Ctx, TEXT("__wsClose"), &ShutFn);
	FString Ignored;
	// THE `ws` PACKAGE'S SHAPE, because that is the shape the bridge calls:
	// `on('open'|'message'|'close'|'error')`, `send`, `close`, `readyState`.
	// Nothing in the world's own code learns that its socket is Unreal's.
	Run(TEXT(
		"(() => {"
		"  const live = new Map();"
		"  globalThis.__wsEvent = (id, kind, payload) => {"
		"    const s = live.get(id);"
		"    if (!s) return;"
		"    if (kind === 'open') { s.readyState = 1; }"
		"    if (kind === 'close') { s.readyState = 3; live.delete(id); }"
		"    for (const fn of (s.handlers[kind] || [])) {"
		"      try { fn(payload); } catch (e) {"
		"        print('a socket handler threw: ' + (e && e.message || e)); }"
		"    }"
		"  };"
		"  globalThis.__dial = (url) => {"
		"    const id = __wsOpen(String(url));"
		"    const s = {"
		"      id, readyState: 0, handlers: {},"
		"      on (what, fn) { (this.handlers[what] ||= []).push(fn); return this; },"
		"      send (msg) { return __wsSend(this.id, String(msg)); },"
		"      close () { __wsClose(this.id); },"
		"    };"
		"    live.set(id, s);"
		"    return s;"
		"  };"
		"})();"),
		TEXT("dial.js"), Ignored);
}

void FIntervalScript::InstallDoor()
{
	Define(static_cast<JSContextRef>(Context), TEXT("__toWindow"), &ToWindowFn);
}

static TUniquePtr<FIntervalScript> GTheScript;

FIntervalScript& FIntervalScript::Get()
{
	if (!GTheScript.IsValid())
	{
		GTheScript = MakeUnique<FIntervalScript>();
	}
	return *GTheScript;
}

bool FIntervalScript::Exists()
{
	return GTheScript.IsValid();
}

FString FIntervalScript::SourceRoot()
{
	// THE REPOSITORY BESIDE THE PROJECT, on a desktop: the same folder the
	// packaged client copies into `bridge`, and the same one the Node bridge
	// runs out of, so there is one copy of the world's rules on this machine
	// and not two. A phone has no such folder and will stage them into the
	// app's content; that is the line to change and it is a path, not an idea.
	static FString Root;
	if (Root.IsEmpty())
	{
		// ---- OR WHEREVER SOMEBODY SAYS ----
		//
		// `-intervalrules=content` takes the phone's path on a desktop, which
		// is the only way to find out whether the app's own copy is complete
		// without building the app. The staged copy is a hand-written list in
		// `Tools/stage_bridge.sh` and a hand-written list is a list that will
		// one day be short by one file; on a phone that is a window which
		// draws the title card and then nothing, with the reason in a
		// JavaScript exception nobody can reach.
		FString Told;
		if (FParse::Value(FCommandLine::Get(), TEXT("intervalrules="), Told)
			&& !Told.IsEmpty())
		{
			Root = Told.Equals(TEXT("content"), ESearchCase::IgnoreCase)
				? FPaths::ConvertRelativePathToFull(
					FPaths::Combine(FPaths::ProjectContentDir(), TEXT("Bridge")))
				: FPaths::ConvertRelativePathToFull(Told);
			return Root;
		}

		const FString Beside = FPaths::Combine(FPaths::ProjectDir(),
			TEXT(".."), TEXT("interval-bridge"));
		Root = FPaths::ConvertRelativePathToFull(Beside);
		if (!FPlatformFileManager::Get().GetPlatformFile().DirectoryExists(*Root))
		{
			// THE APP'S OWN COPY, which is what a phone has and what a
			// packaged desktop client has too. See stage_bridge.sh.
			Root = FPaths::Combine(FPaths::ProjectContentDir(), TEXT("Bridge"));
			Root = FPaths::ConvertRelativePathToFull(Root);
		}
	}
	return Root;
}

FString FIntervalScript::ReadSource(const FString& Name)
{
	FString Clean = Name;
	Clean.RemoveFromStart(TEXT("./"));
	const FString Path = FPaths::Combine(SourceRoot(), Clean);
	FString Text;
	if (!FFileHelper::LoadFileToString(Text, *Path))
	{
		return FString();
	}
	return Text;
}

bool FIntervalScript::Boot(FString& OutError)
{
	// ONCE. The rules are evaluated for their own bytes' sake and evaluating
	// them twice would make two engines in one context, each with its own
	// tables, and nothing would say which one anybody was holding.
	if (bBooted)
	{
		return true;
	}
	// IN THIS ORDER AND NOT ANOTHER. The shim installs the Buffer, the console
	// and the `require` that must FAIL for 'crypto'; the loader needs nothing
	// but itself; `start.js` uses both and hands the engine its own source.
	const TCHAR* Files[] = { TEXT("portable/shim.js"),
	                         TEXT("portable/esm.js"),
	                         TEXT("portable/start.js") };
	for (const TCHAR* Name : Files)
	{
		const FString Source = ReadSource(Name);
		if (Source.IsEmpty())
		{
			OutError = FString::Printf(TEXT("no %s under %s"), Name, *SourceRoot());
			return false;
		}
		if (!Run(Source, Name, OutError))
		{
			OutError = FString::Printf(TEXT("%s: %s"), Name, *OutError);
			return false;
		}
	}
	bBooted = true;
	return true;
}

// ---------------------------------------------------------------------------
// THE BRIDGE, IN THIS PROCESS
// ---------------------------------------------------------------------------

void FIntervalScript::TakeFrame(const FString& Text)
{
	if (OnFrame)
	{
		OnFrame(Text);
		return;
	}
	// NOBODY LISTENING IS NOT NOTHING HAPPENING. A bridge whose frames go
	// nowhere looks exactly like a bridge that is not running, and that
	// mistake has cost this project a day before. Say the first few so the
	// log shows the world arriving, then stop, because there is one a second
	// for as long as the editor is open.
	static int32 Unheard = 0;
	if (++Unheard <= 3)
	{
		UE_LOG(LogIntervalScript, Log,
			TEXT("[bridge] a frame with nobody to draw it (%d chars): %s"),
			Text.Len(), *Text.Left(160));
	}
}

bool FIntervalScript::ToBridge(const FString& Text)
{
	if (!Context || !bBridgeOpen)
	{
		return false;
	}
	JSContextRef Ctx = static_cast<JSContextRef>(Context);
	JSObjectRef Global = JSContextGetGlobalObject(Ctx);
	FJsString Name(TEXT("__fromWindow"));
	JSValueRef Fn = JSObjectGetProperty(Ctx, Global, Name, nullptr);
	if (!Fn || !JSValueIsObject(Ctx, Fn))
	{
		return false;
	}
	JSObjectRef Call = JSValueToObject(Ctx, Fn, nullptr);
	FJsString Payload(Text);
	JSValueRef Args[1] = { JSValueMakeString(Ctx, Payload) };
	JSValueRef Threw = nullptr;
	JSObjectCallAsFunction(Ctx, Call, nullptr, 1, Args, &Threw);
	if (Threw)
	{
		UE_LOG(LogIntervalScript, Error, TEXT("the bridge threw on %s: %s"),
			*Text.Left(80), *AsError(Ctx, Threw));
		return false;
	}
	return true;
}

int32 FIntervalScript::Pump()
{
	if (!Context || !bBooted)
	{
		return 0;
	}
	// NO SOURCE IS COMPILED HERE. This runs once a frame for as long as the
	// window is open, and `JSEvaluateScript` on a string would parse that
	// string sixty times a second for ever. Two property reads and a call is
	// what it costs instead, which is nothing anybody can measure.
	JSContextRef Ctx = static_cast<JSContextRef>(Context);
	JSObjectRef Global = JSContextGetGlobalObject(Ctx);
	FJsString ClockName(TEXT("__intervalClock"));
	JSValueRef ClockVal = JSObjectGetProperty(Ctx, Global, ClockName, nullptr);
	if (!ClockVal || !JSValueIsObject(Ctx, ClockVal))
	{
		return 0;
	}
	JSObjectRef Clock = JSValueToObject(Ctx, ClockVal, nullptr);
	FJsString RunName(TEXT("run"));
	JSValueRef RunVal = JSObjectGetProperty(Ctx, Clock, RunName, nullptr);
	if (!RunVal || !JSValueIsObject(Ctx, RunVal))
	{
		return 0;
	}
	JSObjectRef Run = JSValueToObject(Ctx, RunVal, nullptr);
	JSValueRef Threw = nullptr;
	JSValueRef Fired = JSObjectCallAsFunction(Ctx, Run, Clock, 0, nullptr, &Threw);
	if (Threw)
	{
		UE_LOG(LogIntervalScript, Error, TEXT("the clock threw: %s"),
			*AsError(Ctx, Threw));
		return 0;
	}
	return static_cast<int32>(JSValueToNumber(Ctx, Fired, nullptr));
}

bool FIntervalScript::OpenBridge(const TMap<FString, FString>& Options,
	FString& OutError)
{
	if (bBridgeOpen)
	{
		return true;
	}
	if (!Boot(OutError))
	{
		return false;
	}

	// THE SETTINGS, AS A JAVASCRIPT OBJECT AND NOT AS A COMMAND LINE. On a
	// desktop `HOST.option` reads `process.argv`, because that is what a
	// process has; here there is no process to have argv, so the same question
	// is answered off an object the host put there.
	FString Literal = TEXT("globalThis.__intervalOptions = {");
	bool bFirst = true;
	for (const TPair<FString, FString>& Pair : Options)
	{
		FString Value = Pair.Value;
		Value.ReplaceInline(TEXT("\\"), TEXT("\\\\"));
		Value.ReplaceInline(TEXT("'"), TEXT("\\'"));
		Literal += FString::Printf(TEXT("%s'%s': '%s'"),
			bFirst ? TEXT("") : TEXT(", "), *Pair.Key, *Value);
		bFirst = false;
	}
	Literal += TEXT("};");
	if (!Run(Literal, TEXT("options.js"), OutError))
	{
		return false;
	}

	const FString Host = ReadSource(TEXT("portable/host-unreal.js"));
	if (Host.IsEmpty())
	{
		OutError = FString::Printf(TEXT("no portable/host-unreal.js under %s"),
			*SourceRoot());
		return false;
	}
	if (!Run(Host, TEXT("portable/host-unreal.js"), OutError))
	{
		return false;
	}

	// AND THE BRIDGE. `bBridgeOpen` goes up FIRST, because loading the bridge
	// calls `HOST.door`, which sends the window its `hello` before this call
	// has returned -- and a frame that arrives while the flag is still down is
	// a frame the window never sees. Set it back down if the load throws.
	//
	// AND IT FINISHES LATER. The bridge's last two statements ask a node for
	// the founding and build the island from it, so its body is compiled as an
	// async one and returns a promise the moment it reaches its first fetch.
	// This call therefore starts the bridge and does not wait for it: what
	// comes back is `loading`, and `open` or `failed: why` arrives in the log a
	// few seconds later. A caller that wanted to block would be blocking the
	// thread the fetch has to complete on.
	bBridgeOpen = true;
	FString State;
	if (!Eval(TEXT("String(globalThis.__intervalOpenBridge());"),
		TEXT("openbridge.js"), State, OutError))
	{
		bBridgeOpen = false;
		return false;
	}
	UE_LOG(LogIntervalScript, Log,
		TEXT("the bridge is starting inside this process (%s)"), *State);
	return true;
}

bool FIntervalScript::Run(const FString& Source, const FString& Where,
	FString& OutError)
{
	FString Ignored;
	return Eval(Source, Where, Ignored, OutError);
}

bool FIntervalScript::Eval(const FString& Source, const FString& Where,
	FString& OutValue, FString& OutError)
{
	if (!Context)
	{
		OutError = TEXT("there is no context");
		return false;
	}
	JSContextRef Ctx = static_cast<JSContextRef>(Context);
	FJsString Script(Source);
	FJsString Url(Where);
	JSValueRef Thrown = nullptr;
	JSValueRef Value = JSEvaluateScript(Ctx, Script, nullptr, Url, 1, &Thrown);
	if (Thrown)
	{
		OutError = AsError(Ctx, Thrown);
		return false;
	}
	OutValue = AsString(Ctx, Value);
	return true;
}

#endif   // INTERVAL_HAS_SCRIPT
