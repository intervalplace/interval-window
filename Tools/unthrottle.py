#!/usr/bin/env python3
"""Stop the editor dozing when its window is not in the foreground.

Unreal drops the editor to about three frames a second whenever it is not the
foreground window, which under automation is always. Every frame-time reading
taken this way is then a reading of the doze and of nothing else: 344 ms,
unmoved by turning off Lumen, volumetric fog or hardware ray tracing, and
reported just the same by an editor with no world running at all.

Neither Config/DefaultEditorPerProjectUserSettings.ini nor the saved per-user
config changes it. The live object does, and this sets it.
"""
import json
import rpc

OBJ = 'editor_toolset.toolsets.object.ObjectTools'
CDO = '/Script/UnrealEd.Default__EditorPerformanceSettings'
print(rpc.call(OBJ, 'set_properties', {'instance': {'refPath': CDO},
      'values': json.dumps({'bThrottleCPUWhenNotForeground': False})})[:80])
