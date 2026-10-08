#include "Modules/ModuleManager.h"

// Nothing to start and nothing to stop: the subsystem owns the socket and
// the game instance owns the subsystem.
IMPLEMENT_MODULE(FDefaultModuleImpl, IntervalBridge);
