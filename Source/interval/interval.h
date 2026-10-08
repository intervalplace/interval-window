// interval.h -- deliberately nothing.
//
// Every line of this window's C++ lives in Plugins/IntervalBridge, which is
// transport and geometry and holds no opinion about the world. This module
// exists only so UnrealBuildTool has a project target to hang that plugin on.
// If gameplay logic ever appears here, it is a second copy of something that
// already exists in JavaScript, and check-window-unreal.mjs will say so.
#pragma once

#include "CoreMinimal.h"
