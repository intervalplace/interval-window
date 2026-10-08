#!/usr/bin/env python3
"""Build M_IntervalThatch from thatch.hlsl, and save it.

THIS MATERIAL HAD NO BUILD SCRIPT. It covers every roof in every settlement --
the largest single surface in an aerial view of the window -- and the only
copy of its shader was inside the asset, where nothing could diff it, review
it or rebuild it. The source here was recovered from the live material and is
now the thing that decides what the asset contains.
"""
import json, os
import rpc as _rpc

SP = os.path.dirname(os.path.abspath(__file__))
M = '/Game/Interval/Materials/M_IntervalThatch.M_IntervalThatch'
MAT = 'editor_toolset.toolsets.material.MaterialTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
AST = 'editor_toolset.toolsets.asset.AssetTools'


def call(toolset, tool, args):
    # One session for the whole script; see Tools/rpc.py.
    return _rpc.call(toolset, tool, args)


# Stop the session first. Rebuilding an asset the running world is using wedges
# the editor solidly, and it wedges on the FIRST call.
call('EditorToolset.EditorAppToolset', 'StopPIE', {})
call(AST, 'delete', {'path': '/Game/Interval/Materials/M_IntervalThatch'})
print('create:', call(MAT, 'create_material',
      {'folder_path': '/Game/Interval/Materials', 'asset_name': 'M_IntervalThatch'})[:70])

# MASKED, AND DITHERED. The roof dissolves for whoever is standing under it
# and is solid for everybody else; the dither is what lets temporal AA resolve
# that into a soft fade instead of a checkerboard.
# A WORLD-SPACE NORMAL, for the reason the ground and the flat master use one:
# the courses are described in world Z, and a roof is a procedural mesh whose
# tangents this window generates at runtime.
call(OBJ, 'set_properties', {'instance': {'refPath': M}, 'values': json.dumps({
    'MaterialDomain': 'MD_Surface',
    'BlendMode': 'BLEND_Masked',
    'ShadingModel': 'MSM_DefaultLit',
    'OpacityMaskClipValue': 0.33,
    # THE DITHER IS THE MATERIAL'S OWN. Without it the roof pops from solid to
    # gone at one distance; with it, temporal AA resolves the mask into a soft
    # fade as somebody walks in under the eaves.
    'DitherOpacityMask': True,
    'bTangentSpaceNormal': False,
    'bUsedWithStaticLighting': False,
})})

# APPENDED, NEVER INSERTED: each expression is addressed by the index the
# engine gives it in creation order.
for cls in ('Custom', 'WorldPosition', 'VertexColor', 'CameraPositionWS',
            'VertexNormalWS', 'CollectionParameter'):
    call(MAT, 'add_expression', {'material_or_function': {'refPath': M},
         'expression_class': {'refPath': '/Script/Engine.MaterialExpression' + cls},
         'x': -800, 'y': 0})

blank = {'inputName': 'None', 'input': {'expression': 'None', 'outputIndex': 0,
         'inputName': 'None', 'mask': 0, 'maskR': 0, 'maskG': 0, 'maskB': 0, 'maskA': 0}}
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCustom_0'},
     # ONE BLANK PER INPUT the code below declares. The engine sizes the
     # array from this, so a fifth input added above and not counted here
     # compiles to "use of undeclared identifier" for EVERY input, not just
     # the new one.
     'values': json.dumps({'Inputs': [blank] * 5})})


def inp(name, expr, mask=0, r=0, g=0, b=0, a=0):
    return {'inputName': name,
            'input': {'expression': {'refPath': M + ':' + expr}, 'outputIndex': 0,
                      'inputName': 'None', 'mask': mask,
                      'maskR': r, 'maskG': g, 'maskB': b, 'maskA': a}}


call(OBJ, 'set_properties',
     {'instance': {'refPath': M + ':MaterialExpressionCollectionParameter_0'},
      'values': json.dumps({
          'Collection': {'refPath': '/Game/Interval/MPC_IntervalSky.MPC_IntervalSky'},
          'ParameterName': 'Walker'})})

print('code:', call(OBJ, 'set_properties',
      {'instance': {'refPath': M + ':MaterialExpressionCustom_0'}, 'values': json.dumps({
          'Code': open(os.path.join(SP, 'thatch.hlsl')).read(),
          'Description': 'Thatch',
          'OutputType': 'CMOT_Float3',
          'AdditionalOutputs': [{'outputName': 'Rough', 'outputType': 'CMOT_Float1'},
                                {'outputName': 'Mask', 'outputType': 'CMOT_Float1'},
                                {'outputName': 'Normal', 'outputType': 'CMOT_Float3'}],
          'Inputs': [
              inp('P', 'MaterialExpressionWorldPosition_0', 1, 1, 1, 1, 0),
              # THE BUILDING'S OWN SEED, in the red channel of the vertex
              # colour. AIntervalChunk hashes the building's corner in world
              # TILES, so a roof weathers the same way in every window.
              inp('House', 'MaterialExpressionVertexColor_0', 1, 1, 0, 0, 0),
              inp('Cam', 'MaterialExpressionCameraPositionWS_0'),
              # WHERE THE CITIZEN IS STANDING, from the shared collection the
              # sky already fills every interval. The roof's dissolve used the
              # CAMERA, which in a view from twenty-five metres up is never
              # near a roof even when the person is directly under it -- so a
              # citizen who walked indoors was hidden by the roof they were
              # standing beneath, and what was going on in there was illegible.
              #
              # Every plant on the island already leans away from this same
              # vector; the roof is simply another thing that should know
              # where somebody is rather than where the camera is.
              inp('Walk', 'MaterialExpressionCollectionParameter_0', 1, 1, 1, 1, 0),
              inp('N', 'MaterialExpressionVertexNormalWS_0', 1, 1, 1, 1, 0),
          ]})}))

for prop, out in (('MP_BaseColor', ''), ('MP_Roughness', 'Rough'),
                  ('MP_OpacityMask', 'Mask'), ('MP_Normal', 'Normal')):
    call(MAT, 'connect_to_output', {'expression': {'refPath': M + ':MaterialExpressionCustom_0'},
         'output_name': out, 'material_property': prop})

r = call(MAT, 'recompile', {'material_or_function': {'refPath': M}})
bad = [l for l in r.split('\n')
       if any(w in l.lower() for w in ('error', 'fail', 'not available'))]
print('compile:', '\n  '.join(bad)[:600] if bad else 'clean')
print('save:', call(AST, 'save_assets',
                    {'asset_paths': ['/Game/Interval/Materials/M_IntervalThatch']})[:60])
print('NOW RUN apply.py -- this replaced the asset and orphaned live pointers')
