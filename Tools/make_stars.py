#!/usr/bin/env python3
"""Build M_IntervalStars from stars.hlsl, and save it.

Unlit and ADDITIVE: what it returns is what lands on the frame, over whatever
the sky atmosphere has already put there. That is the right relation -- the
atmosphere decides what colour the sky is and the stars are added into it, so
they drown as the sky brightens without anything having to decide when dawn is.
"""
import json, os
import rpc as _rpc

SP = os.path.dirname(os.path.abspath(__file__))
M = '/Game/Interval/Materials/M_IntervalStars.M_IntervalStars'
MAT = 'editor_toolset.toolsets.material.MaterialTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
AST = 'editor_toolset.toolsets.asset.AssetTools'


def call(toolset, tool, args):
    # One session for the whole script; see Tools/rpc.py.
    return _rpc.call(toolset, tool, args)


call('EditorToolset.EditorAppToolset', 'StopPIE', {})
call(AST, 'delete', {'path': '/Game/Interval/Materials/M_IntervalStars'})
print('create:', call(MAT, 'create_material',
      {'folder_path': '/Game/Interval/Materials', 'asset_name': 'M_IntervalStars'})[:70])

# TWO SIDED, because the camera is inside the sphere and every polygon of it is
# therefore a back face -- the same reason the rain drum is two sided.
call(OBJ, 'set_properties', {'instance': {'refPath': M}, 'values': json.dumps({
    'MaterialDomain': 'MD_Surface',
    'BlendMode': 'BLEND_Additive',
    'ShadingModel': 'MSM_Unlit',
    'TwoSided': True,
    'bUsedWithStaticLighting': False,
})})

# APPENDED, NEVER INSERTED: each expression is addressed by creation order.
for cls in ('Custom', 'CameraVectorWS', 'CollectionParameter', 'Time',
            'ScalarParameter'):
    call(MAT, 'add_expression', {'material_or_function': {'refPath': M},
         'expression_class': {'refPath': '/Script/Engine.MaterialExpression' + cls},
         'x': -800, 'y': 0})

call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCollectionParameter_0'},
     'values': json.dumps({'Collection': {'refPath': '/Game/Interval/MPC_IntervalSky.MPC_IntervalSky'},
                           'ParameterName': 'Night'})})
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_0'},
     'values': json.dumps({'ParameterName': 'Bright', 'DefaultValue': 1.0})})

blank = {'inputName': 'None', 'input': {'expression': 'None', 'outputIndex': 0,
         'inputName': 'None', 'mask': 0, 'maskR': 0, 'maskG': 0, 'maskB': 0, 'maskA': 0}}
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCustom_0'},
     'values': json.dumps({'Inputs': [blank] * 4})})


def inp(name, expr, mask=0, r=0, g=0, b=0, a=0):
    return {'inputName': name,
            'input': {'expression': {'refPath': M + ':' + expr}, 'outputIndex': 0,
                      'inputName': 'None', 'mask': mask,
                      'maskR': r, 'maskG': g, 'maskB': b, 'maskA': a}}


print('code:', call(OBJ, 'set_properties',
      {'instance': {'refPath': M + ':MaterialExpressionCustom_0'}, 'values': json.dumps({
          'Code': open(os.path.join(SP, 'stars.hlsl')).read(),
          'Description': 'stars',
          'OutputType': 'CMOT_Float3',
          'Inputs': [
              inp('Eye', 'MaterialExpressionCameraVectorWS_0', 1, 1, 1, 1, 0),
              inp('Night', 'MaterialExpressionCollectionParameter_0'),
              inp('Time', 'MaterialExpressionTime_0'),
              inp('Bright', 'MaterialExpressionScalarParameter_0'),
          ]})}))

call(MAT, 'connect_to_output', {'expression': {'refPath': M + ':MaterialExpressionCustom_0'},
     'output_name': '', 'material_property': 'MP_EmissiveColor'})

r = call(MAT, 'recompile', {'material_or_function': {'refPath': M}})
bad = [l for l in r.split('\n')
       if any(w in l.lower() for w in ('error', 'fail', 'not available'))]
print('compile:', '\n  '.join(bad)[:600] if bad else 'clean')
print('save:', call(AST, 'save_assets',
                    {'asset_paths': ['/Game/Interval/Materials/M_IntervalStars']})[:60])
