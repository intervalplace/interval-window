// The project exists as code for one reason: a Blueprint-only project cannot
// compile a source plugin, and IntervalBridge is the whole of this window's
// C++. This module stays empty on purpose -- see Source/interval/interval.h.
using UnrealBuildTool;
using System.Collections.Generic;

public class intervalTarget : TargetRules
{
	public intervalTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.V7;
		IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_8;
		ExtraModuleNames.Add("interval");

		// ---- AND NO, THE CLIENT CANNOT SIMPLY KEEP ITS LOG ----
		//
		// A Shipping build compiles UE_LOG out altogether, and the client
		// people download is Shipping, so the one window whose behaviour
		// matters is the one window that can say nothing. Every note in this
		// project about what the window reports, from `bReportUndrawnKinds` to
		// the undrawn-word grep, is true only of an editor. What that cost:
		// the window held the whole island instead of streaming it, 112 chunks
		// and 1.33 million scatter instances, for months, and the warning that
		// would have said so could not be printed.
		//
		// `bUseLoggingInShipping = true` is the obvious fix and UBT REFUSES IT:
		//
		//   interval modifies the values of properties:
		//   [ bUseLoggingInShipping: True != False ]. This is not allowed, as
		//   interval has build products in common with UnrealGame.
		//
		// It is a global define, so every engine module would have to be
		// rebuilt to agree with it, and the installed engine's own objects
		// were compiled the other way. The ways out are a unique build
		// environment, which means compiling the engine, or
		// bOverrideBuildEnvironment, which links modules that disagree about
		// NO_LOGGING and is how you get a crash in an unrelated class.
		//
		// AND IT COST AN AFTERNOON, because the refusal was silent: the binary
		// step in Tools/client.sh piped UBT through `tail -2` and did not look
		// at its exit code, so the build "succeeded", xcodebuild wrapped the
		// PREVIOUS executable, and the installed client died before main on a
		// missing dylib. See the note on that step, which now checks.
		//
		// So the window writes what it has to say to its own file instead, and
		// that works in every configuration. See IntervalSay in IntervalHand.cpp.
	}
}
