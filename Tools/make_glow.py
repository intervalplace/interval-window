#!/usr/bin/env python3
"""Build M_IntervalGlow from glow.hlsl, and save it."""
import json, os, subprocess, sys
import rpc as _rpc
SP = os.path.dirname(os.path.abspath(__file__))
M = '/Game/Interval/Materials/M_IntervalGlow.M_IntervalGlow'
MAT = 'editor_toolset.toolsets.material.MaterialTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'

def call(toolset, tool, args):
    # One session for the whole script; see Tools/rpc.py.
    return _rpc.call(toolset, tool, args)


# Stop the session first. Rebuilding an asset the running world is using wedges
# the editor solidly -- it holds the port, accepts connections and answers
# nothing -- and it wedges on the FIRST call, so stopping afterwards is too late.
call('EditorToolset.EditorAppToolset', 'StopPIE', {})
call('editor_toolset.toolsets.asset.AssetTools', 'delete',
     {'path': '/Game/Interval/Materials/M_IntervalGlow'})
print('create:', call(MAT, 'create_material',
      {'folder_path': '/Game/Interval/Materials', 'asset_name': 'M_IntervalGlow'})[:80])

# Unlit and additive: a light in the dark adds to what is behind it.
# bUsedWithInstancedStaticMeshes, because these are instances and a material
# without that flag is silently swapped for the default -- twice bitten.
call(OBJ, 'set_properties', {'instance': {'refPath': M}, 'values': json.dumps({
    'MaterialDomain': 'MD_Surface',
    'BlendMode': 'BLEND_Additive',
    'ShadingModel': 'MSM_Unlit',
    'bUsedWithInstancedStaticMeshes': True,
})})

for cls in ('Custom', 'Time', 'ScalarParameter', 'PerInstanceCustomData'):
    call(MAT, 'add_expression', {'material_or_function': {'refPath': M},
         'expression_class': {'refPath': '/Script/Engine.MaterialExpression' + cls},
         'x': -800, 'y': 0})

call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_0'},
     'values': json.dumps({'ParameterName': 'Night', 'DefaultValue': 1.0})})

blank = {'inputName': 'None', 'input': {'expression': 'None', 'outputIndex': 0,
         'inputName': 'None', 'mask': 0, 'maskR': 0, 'maskG': 0, 'maskB': 0, 'maskA': 0}}
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCustom_0'},
     'values': json.dumps({'Inputs': [blank, blank, blank]})})

def inp(name, expr):
    return {'inputName': name, 'input': {'expression': {'refPath': M + ':' + expr},
            'outputIndex': 0, 'inputName': 'None', 'mask': 0,
            'maskR': 0, 'maskG': 0, 'maskB': 0, 'maskA': 0}}

print('code:', call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCustom_0'},
      'values': json.dumps({
          'Code': open(SP + '/glow.hlsl').read(),
          'Description': 'glow-worm',
          'OutputType': 'CMOT_Float3',
          'Inputs': [inp('Time', 'MaterialExpressionTime_0'),
                     inp('Night', 'MaterialExpressionScalarParameter_0'),
                     inp('Which', 'MaterialExpressionPerInstanceCustomData_0')]})}))

call(MAT, 'connect_to_output', {'expression': {'refPath': M + ':MaterialExpressionCustom_0'},
     'output_name': '', 'material_property': 'MP_EmissiveColor'})

r = call(MAT, 'recompile', {'material_or_function': {'refPath': M}})
bad = [l for l in r.split('\n') if 'error' in l.lower()]
print('compile:', bad[0][:200] if bad else 'clean')
print('save:', call('editor_toolset.toolsets.asset.AssetTools', 'save_assets',
                    {'asset_paths': ['/Game/Interval/Materials/M_IntervalGlow']}))

# ---------------------------------------------------------------------------
# NOW RUN apply.py.
#
# This script DELETES the material and makes a new one at the same path. Any
# asset already loaded in the running editor -- the look asset above all --
# still points at the OLD object, which is now trash. A material instance made
# from a trashed material renders NOTHING, silently, with no warning and a
# clean compile. Re-running apply.py rebuilds the look asset and re-resolves
# the pointer. Restarting the editor does it too, and more slowly.
print('NOW RUN apply.py -- this replaced the asset and orphaned live pointers')
