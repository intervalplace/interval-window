// Transport only. If this list ever grows a gameplay dependency, something
// has been reimplemented that already exists in JavaScript.
using UnrealBuildTool;

public class IntervalBridge : ModuleRules
{
	public IntervalBridge(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"ProceduralMeshComponent",
			"AnimGraphRuntime",   // PlayAnimation on a single-node skeletal mesh
			"InputCore",          // EKeys, for the one mouse button the hand uses
			"UMG", "Slate", "SlateCore",   // the door, built in code rather than in an asset
			"Niagara",            // hearth smoke and embers, rain splashes, footfall dust
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"Json",
			"WebSockets",   // an engine module, not a plugin: it must NOT be listed in the .uplugin
			"RenderCore",
			"RHI",
			"HTTP",         // what `fetch` is, once the rules run in this process
		});

		// ---- JAVASCRIPTCORE, WHICH IS HOW THE RULES RUN ON A PHONE ----
		//
		// On a desktop the world's knowledge is a Node process beside the game
		// and this module only draws what it is told. iOS will not host a
		// second process and will not let an app start an interpreter, so the
		// bridge has to run INSIDE the app -- in the JavaScript engine the
		// platform already ships, which is JavaScriptCore.
		//
		// It is a SYSTEM FRAMEWORK on both Apple platforms, so there is nothing
		// to vendor and nothing to license: macOS has the same one, which is
		// why this is written and debugged on a Mac first and why iOS is then
		// a packaging step rather than a session with a phone on a cable.
		//
		// Nothing else in this module may depend on it. The engine's source is
		// evaluated as text and its SHA is what a founding records; a build
		// that transpiled or bundled it would be a different world.
		if (Target.Platform == UnrealTargetPlatform.Mac
			|| Target.Platform == UnrealTargetPlatform.IOS)
		{
			PublicFrameworks.Add("JavaScriptCore");
		}
	}
}
