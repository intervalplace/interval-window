#!/usr/bin/env python3
"""Build M_IntervalCinder from cinder.hlsl, and save it.

The embers in the cracks of the cinder-crown, which is the rarest cosmetic in
this world and defends nothing: one in two thousand and forty-eight off the
dragon, "pure cosmetic" in the engine's own words. A thing whose only purpose
is to be seen ought to be visible after dark, so the splits between its burnt
lumps are still alight.

The same shape as `make_quicks.py` and for the same reason: unlit and ADDITIVE,
so what it returns lands on the frame over whatever the burnt stone beside it
is doing, and it needs nothing to decide when night is -- it reads `Night` off
the one collection the hour writes to, exactly as the stars do.

NOT TWO SIDED, unlike the stars: this is on the outside of a solid object and
a two-sided emissive would light the inside of the crown as well.
"""
import json, os
import rpc as _rpc

SP = os.path.dirname(os.path.abspath(__file__))
M = '/Game/Interval/Materials/M_IntervalCinder.M_IntervalCinder'
MAT = 'editor_toolset.toolsets.material.MaterialTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
AST = 'editor_toolset.toolsets.asset.AssetTools'


def call(toolset, tool, args):
    # One session for the whole script; see Tools/rpc.py.
    return _rpc.call(toolset, tool, args)


call('EditorToolset.EditorAppToolset', 'StopPIE', {})
call(AST, 'delete', {'path': '/Game/Interval/Materials/M_IntervalCinder'})
print('create:', call(MAT, 'create_material',
      {'folder_path': '/Game/Interval/Materials', 'asset_name': 'M_IntervalCinder'})[:70])

# AND USED WITH INSTANCED STATIC MESHES, because a worn piece is hung as one
# and a material without that flag is silently swapped for the default grey.
# Twice bitten; see the same note in make_glow.py.
call(OBJ, 'set_properties', {'instance': {'refPath': M}, 'values': json.dumps({
    'MaterialDomain': 'MD_Surface',
    'BlendMode': 'BLEND_Additive',
    'ShadingModel': 'MSM_Unlit',
    'TwoSided': False,
    'bUsedWithInstancedStaticMeshes': True,
    'bUsedWithStaticLighting': False,
})})

# APPENDED, NEVER INSERTED: each expression is addressed by creation order.
for cls in ('Custom', 'CollectionParameter', 'Time', 'ScalarParameter'):
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
     'values': json.dumps({'Inputs': [blank] * 3})})


def inp(name, expr, mask=0, r=0, g=0, b=0, a=0):
    return {'inputName': name,
            'input': {'expression': {'refPath': M + ':' + expr}, 'outputIndex': 0,
                      'inputName': 'None', 'mask': mask,
                      'maskR': r, 'maskG': g, 'maskB': b, 'maskA': a}}


print('code:', call(OBJ, 'set_properties',
      {'instance': {'refPath': M + ':MaterialExpressionCustom_0'}, 'values': json.dumps({
          'Code': open(os.path.join(SP, 'cinder.hlsl')).read(),
          'Description': 'cinder',
          'OutputType': 'CMOT_Float3',
          'Inputs': [
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
                    {'asset_paths': ['/Game/Interval/Materials/M_IntervalCinder']})[:60])
