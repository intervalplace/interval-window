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
	}
}
