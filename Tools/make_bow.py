#!/usr/bin/env python3
"""Build M_IntervalBow from bow.hlsl, and save it.

The same shape as `make_quicks.py` and for the same reasons: unlit and ADDITIVE,
on a sphere the camera is inside, reading the VIEW RAY so the dome's size and
position never enter into it. A rainbow IS added light -- it is sunlight thrown
back out of the air -- so additive is not a convenience here, it is the truth.

WHAT IS DIFFERENT is that this one has to be told two things a frame: how much
of a bow the world says there is, and which way the sun is. They are set on a
dynamic instance by `AIntervalHour` rather than on the weather collection,
because nothing else reads either of them and adding to that collection is the
one operation in this project that can silently unbind every material on the
island. See the note at the top of make_mpc.py.
"""
import json, os
import rpc as _rpc

SP = os.path.dirname(os.path.abspath(__file__))
M = '/Game/Interval/Materials/M_IntervalBow.M_IntervalBow'
MAT = 'editor_toolset.toolsets.material.MaterialTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
AST = 'editor_toolset.toolsets.asset.AssetTools'


def call(toolset, tool, args):
    # One session for the whole script; see Tools/rpc.py.
    return _rpc.call(toolset, tool, args)


call('EditorToolset.EditorAppToolset', 'StopPIE', {})
call(AST, 'delete', {'path': '/Game/Interval/Materials/M_IntervalBow'})
print('create:', call(MAT, 'create_material',
      {'folder_path': '/Game/Interval/Materials', 'asset_name': 'M_IntervalBow'})[:70])

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
for cls in ('Custom', 'CameraVectorWS', 'CollectionParameter',
            'VectorParameter', 'ScalarParameter'):
    call(MAT, 'add_expression', {'material_or_function': {'refPath': M},
         'expression_class': {'refPath': '/Script/Engine.MaterialExpression' + cls},
         'x': -800, 'y': 0})

# `Day` off the weather collection, so the bow drowns as the light goes
# without anything here having to decide when dusk is -- the same relation the
# stars have to it, the other way up.
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCollectionParameter_0'},
     'values': json.dumps({'Collection': {'refPath': '/Game/Interval/MPC_IntervalSky.MPC_IntervalSky'},
                           'ParameterName': 'Day'})})
# WHICH WAY THE SUN IS, as a unit vector pointing TOWARD it. The bow is a
# circle round the opposite direction, so this is the whole geometry.
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionVectorParameter_0'},
     'values': json.dumps({'ParameterName': 'Sun',
                           'DefaultValue': {'r': 0.0, 'g': 0.0, 'b': 1.0, 'a': 1.0}})})
# HOW MUCH OF A BOW THERE IS, which is the world's own number and is nought
# nearly always.
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_0'},
     'values': json.dumps({'ParameterName': 'Bow', 'DefaultValue': 0.0})})

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
          'Code': open(os.path.join(SP, 'bow.hlsl')).read(),
          'Description': 'rainbow',
          'OutputType': 'CMOT_Float3',
          'Inputs': [
              inp('Eye', 'MaterialExpressionCameraVectorWS_0', 1, 1, 1, 1, 0),
              inp('Day', 'MaterialExpressionCollectionParameter_0'),
              inp('Sun', 'MaterialExpressionVectorParameter_0', 1, 1, 1, 1, 0),
              inp('Bow', 'MaterialExpressionScalarParameter_0'),
          ]})}))

call(MAT, 'connect_to_output', {'expression': {'refPath': M + ':MaterialExpressionCustom_0'},
     'output_name': '', 'material_property': 'MP_EmissiveColor'})

r = call(MAT, 'recompile', {'material_or_function': {'refPath': M}})
bad = [l for l in r.split('\n')
       if any(w in l.lower() for w in ('error', 'fail', 'not available'))]
print('compile:', '\n  '.join(bad)[:600] if bad else 'clean')
print('save:', call(AST, 'save_assets',
                    {'asset_paths': ['/Game/Interval/Materials/M_IntervalBow']})[:60])
