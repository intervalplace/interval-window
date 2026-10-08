#!/usr/bin/env python3
"""Build M_IntervalTimberFrame from tf.hlsl, and save it.

LIKE THE THATCH, THIS HAD NO BUILD SCRIPT. It draws every wall of every
building in fifteen settlements and the only copy of its graph was inside the
asset. `tf.hlsl` was already on disk and already matched the live code, so
nothing was recovered here -- what was missing was the twenty lines that put
it back into a material.
"""
import json, os
import rpc as _rpc

SP = os.path.dirname(os.path.abspath(__file__))
M = '/Game/Interval/Materials/M_IntervalTimberFrame.M_IntervalTimberFrame'
MAT = 'editor_toolset.toolsets.material.MaterialTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
AST = 'editor_toolset.toolsets.asset.AssetTools'


def call(toolset, tool, args):
    # One session for the whole script; see Tools/rpc.py.
    return _rpc.call(toolset, tool, args)


call('EditorToolset.EditorAppToolset', 'StopPIE', {})
call(AST, 'delete', {'path': '/Game/Interval/Materials/M_IntervalTimberFrame'})
print('create:', call(MAT, 'create_material',
      {'folder_path': '/Game/Interval/Materials', 'asset_name': 'M_IntervalTimberFrame'})[:70])

# INSTANCED STATIC MESHES, and it matters: most of a town's walls are instanced
# cubes carrying the building's seed in per-instance custom data. Without the
# usage bit the material is silently swapped for the default grey.
call(OBJ, 'set_properties', {'instance': {'refPath': M}, 'values': json.dumps({
    'MaterialDomain': 'MD_Surface',
    # MASKED, so the walls of the room you are standing in can be cut down to
    # the waist. Nothing else here is transparent and nothing wants to be: the
    # clip value is high and the dither hands the soft edge to temporal AA,
    # which is the same arrangement the thatch uses to get out of your way.
    'BlendMode': 'BLEND_Masked',
    'OpacityMaskClipValue': 0.33,
    'DitherOpacityMask': True,
    'ShadingModel': 'MSM_DefaultLit',
    'bUsedWithInstancedStaticMeshes': True,
    'bTangentSpaceNormal': False,
    'bUsedWithStaticLighting': False,
})})

for cls in ('Custom', 'WorldPosition', 'PerInstanceCustomData', 'VertexColor',
            'VertexNormalWS', 'CameraPositionWS', 'CollectionParameter',
            'CollectionParameter'):
    call(MAT, 'add_expression', {'material_or_function': {'refPath': M},
         'expression_class': {'refPath': '/Script/Engine.MaterialExpression' + cls},
         'x': -800, 'y': 0})

# How dark it is, off the one collection the hour writes to -- so the windows
# come up at dusk without anything here deciding when dusk is.
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCollectionParameter_0'},
     'values': json.dumps({'Collection': {'refPath': '/Game/Interval/MPC_IntervalSky.MPC_IntervalSky'},
                           'ParameterName': 'Night'})})

# AND WHERE THE CITIZEN IS, off the same collection, with how far indoors they
# are in the alpha. See the tail of tf.hlsl: this is what cuts the walls.
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCollectionParameter_1'},
     'values': json.dumps({'Collection': {'refPath': '/Game/Interval/MPC_IntervalSky.MPC_IntervalSky'},
                           'ParameterName': 'Walker'})})

blank = {'inputName': 'None', 'input': {'expression': 'None', 'outputIndex': 0,
         'inputName': 'None', 'mask': 0, 'maskR': 0, 'maskG': 0, 'maskB': 0, 'maskA': 0}}
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCustom_0'},
     'values': json.dumps({'Inputs': [blank] * 7})})


def inp(name, expr, mask=0, r=0, g=0, b=0, a=0):
    return {'inputName': name,
            'input': {'expression': {'refPath': M + ':' + expr}, 'outputIndex': 0,
                      'inputName': 'None', 'mask': mask,
                      'maskR': r, 'maskG': g, 'maskB': b, 'maskA': a}}


print('code:', call(OBJ, 'set_properties',
      {'instance': {'refPath': M + ':MaterialExpressionCustom_0'}, 'values': json.dumps({
          'Code': open(os.path.join(SP, 'tf.hlsl')).read(),
          'Description': 'Half timbering',
          'OutputType': 'CMOT_Float3',
          'AdditionalOutputs': [{'outputName': 'Rough', 'outputType': 'CMOT_Float1'},
                                {'outputName': 'Normal', 'outputType': 'CMOT_Float3'},
                                {'outputName': 'Glow', 'outputType': 'CMOT_Float3'},
                                {'outputName': 'Mask', 'outputType': 'CMOT_Float1'}],
          'Inputs': [
              inp('P', 'MaterialExpressionWorldPosition_0', 1, 1, 1, 1, 0),
              inp('House', 'MaterialExpressionPerInstanceCustomData_0'),
              # A wall of one house arrives two ways -- instanced cubes with
              # the seed in custom data, and a procedural quad where the window
              # closed a roof's perimeter, which has no custom data at all and
              # carries the seed in vertex colour instead. The shader tells
              # them apart by the blue channel; both are wired here.
              inp('VC', 'MaterialExpressionVertexColor_0', 1, 1, 1, 1, 0),
              inp('Nrm', 'MaterialExpressionVertexNormalWS_0', 1, 1, 1, 1, 0),
              inp('Cam', 'MaterialExpressionCameraPositionWS_0'),
              inp('Night', 'MaterialExpressionCollectionParameter_0'),
              # ALL FOUR CHANNELS. The alpha is the indoors amount and the
              # wall cut reads it; masked to rgb, as the thatch takes it, the
              # walls would come down in the middle of the street.
              inp('Walk', 'MaterialExpressionCollectionParameter_1', 1, 1, 1, 1, 1),
          ]})}))

for prop, out in (('MP_BaseColor', ''), ('MP_Roughness', 'Rough'),
                  ('MP_Normal', 'Normal'), ('MP_EmissiveColor', 'Glow'),
                  ('MP_OpacityMask', 'Mask')):
    call(MAT, 'connect_to_output', {'expression': {'refPath': M + ':MaterialExpressionCustom_0'},
         'output_name': out, 'material_property': prop})

r = call(MAT, 'recompile', {'material_or_function': {'refPath': M}})
bad = [l for l in r.split('\n')
       if any(w in l.lower() for w in ('error', 'fail', 'not available'))]
print('compile:', '\n  '.join(bad)[:600] if bad else 'clean')
print('save:', call(AST, 'save_assets',
                    {'asset_paths': ['/Game/Interval/Materials/M_IntervalTimberFrame']})[:60])
print('NOW RUN apply.py -- this replaced the asset and orphaned live pointers')
