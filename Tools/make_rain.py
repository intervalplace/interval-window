#!/usr/bin/env python3
"""Build M_IntervalRain from rain.hlsl, and save it."""
import json, os, subprocess, sys
import rpc as _rpc
SP = os.path.dirname(os.path.abspath(__file__))
M = '/Game/Interval/Materials/M_IntervalRain.M_IntervalRain'
MAT = 'editor_toolset.toolsets.material.MaterialTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'

def call(toolset, tool, args):
    # One session for the whole script; see Tools/rpc.py.
    return _rpc.call(toolset, tool, args)


# Stop the session first: recompiling a material the running world is using
# wedges the editor, and it wedges on the first call.
call('EditorToolset.EditorAppToolset', 'StopPIE', {})
call('editor_toolset.toolsets.asset.AssetTools', 'delete',
     {'path': '/Game/Interval/Materials/M_IntervalRain'})
print('create:', call(MAT, 'create_material',
      {'folder_path': '/Game/Interval/Materials', 'asset_name': 'M_IntervalRain'})[:80])

# Unlit, translucent, and TWO SIDED -- the camera is inside the cylinder, so
# every polygon of it is a back face.
call(OBJ, 'set_properties', {'instance': {'refPath': M}, 'values': json.dumps({
    'MaterialDomain': 'MD_Surface',
    'BlendMode': 'BLEND_Translucent',
    'ShadingModel': 'MSM_Unlit',
    'TwoSided': True,
    'bUsedWithStaticLighting': False,
})})

for cls in ('Custom', 'WorldPosition', 'ScalarParameter', 'ScalarParameter', 'Time',
            'VectorParameter', 'ScalarParameter', 'VertexNormalWS',
            'CameraVectorWS', 'CameraPositionWS'):
    call(MAT, 'add_expression', {'material_or_function': {'refPath': M},
         'expression_class': {'refPath': '/Script/Engine.MaterialExpression' + cls},
         'x': -800, 'y': 0})

call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_0'},
     'values': json.dumps({'ParameterName': 'Rain', 'DefaultValue': 0.5})})
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_1'},
     'values': json.dumps({'ParameterName': 'Day', 'DefaultValue': 1.0})})
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionVectorParameter_0'},
     'values': json.dumps({'ParameterName': 'Foot'})})
# How wide the drum is, so the streaks can be sized in metres of world rather
# than in fractions of a cylinder.
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_2'},
     'values': json.dumps({'ParameterName': 'Radius', 'DefaultValue': 4500.0})})

blank = {'inputName': 'None', 'input': {'expression': 'None', 'outputIndex': 0,
         'inputName': 'None', 'mask': 0, 'maskR': 0, 'maskG': 0, 'maskB': 0, 'maskA': 0}}
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCustom_0'},
     'values': json.dumps({'Inputs': [blank] * 9})})

def inp(name, expr, mask=0, rgb=False):
    return {'inputName': name, 'input': {'expression': {'refPath': M + ':' + expr},
            'outputIndex': 0, 'inputName': 'None', 'mask': mask,
            'maskR': int(rgb), 'maskG': int(rgb), 'maskB': int(rgb), 'maskA': 0}}

print('code:', call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCustom_0'},
      'values': json.dumps({
          'Code': open(SP + '/rain.hlsl').read(),
          'Description': 'rain',
          'OutputType': 'CMOT_Float3',
          'AdditionalOutputs': [{'outputName': 'Opacity', 'outputType': 'CMOT_Float1'}],
          'Inputs': [inp('W', 'MaterialExpressionWorldPosition_0', 1, True),
                     inp('Rain', 'MaterialExpressionScalarParameter_0'),
                     inp('Day', 'MaterialExpressionScalarParameter_1'),
                     inp('Time', 'MaterialExpressionTime_0'),
                     inp('Foot', 'MaterialExpressionVectorParameter_0', 1, True),
                     inp('Radius', 'MaterialExpressionScalarParameter_2'),
                     inp('N', 'MaterialExpressionVertexNormalWS_0', 1, True),
                     inp('Eye', 'MaterialExpressionCameraVectorWS_0', 1, True),
                     inp('CamPos', 'MaterialExpressionCameraPositionWS_0', 1, True)]})}))

for prop, out in (('MP_EmissiveColor', ''), ('MP_Opacity', 'Opacity')):
    call(MAT, 'connect_to_output', {'expression': {'refPath': M + ':MaterialExpressionCustom_0'},
         'output_name': out, 'material_property': prop})

r = call(MAT, 'recompile', {'material_or_function': {'refPath': M}})
# Look for failure, not for the word "error": Unreal says "Material failed to
# compile: ..." without it, and a grep for the word reports clean over a
# material that is falling back to the default.
bad = [l for l in r.split('\n')
       if any(w in l.lower() for w in ('error', 'fail', 'not available'))]
print('compile:', '\n  '.join(bad)[:500] if bad else 'clean')
print('save:', call('editor_toolset.toolsets.asset.AssetTools', 'save_assets',
                    {'asset_paths': ['/Game/Interval/Materials/M_IntervalRain']}))

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
