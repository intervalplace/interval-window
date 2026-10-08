#!/usr/bin/env python3
"""Build M_IntervalGround from ground.hlsl, and save it.

This material has been edited in place a dozen times over as many sessions and
the graph had drifted -- nodes left behind by experiments, an input wired for a
fade that was taken out again. Built from scratch every run, the file on disk
is the only thing that decides what it contains.
"""
import json, os, subprocess, sys
import rpc as _rpc
SP = os.path.dirname(os.path.abspath(__file__))
M = '/Game/Interval/Materials/M_IntervalGround.M_IntervalGround'
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
     {'path': '/Game/Interval/Materials/M_IntervalGround'})
print('create:', call(MAT, 'create_material',
      {'folder_path': '/Game/Interval/Materials', 'asset_name': 'M_IntervalGround'})[:80])

# CREATION ORDER IS THE WIRING DIAGRAM. The editor names an expression
# MaterialExpression<Class>_<nth of that class>, so anything new goes on the
# END of this list; inserting in the middle renumbers every later node and the
# connections land on the wrong pins with a clean compile.
for cls in ('Custom', 'TextureCoordinate', 'TextureObjectParameter',
            'VectorParameter', 'WorldPosition', 'CollectionParameter',
            'Time', 'CollectionParameter', 'CameraPositionWS', 'VertexNormalWS',
            # APPENDED, NEVER INSERTED: every expression above is addressed by
            # the index the engine gives it in creation order.
            'ActorPositionWS', 'ScalarParameter'):
    call(MAT, 'add_expression', {'material_or_function': {'refPath': M},
         'expression_class': {'refPath': '/Script/Engine.MaterialExpression' + cls},
         'x': -900, 'y': 0})

# The names matter: the chunk sets Control and ChunkSize on its own instance
# of this material, by name, every time a chunk is built.
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionTextureObjectParameter_0'},
     'values': json.dumps({'ParameterName': 'Control',
                           'Texture': {'refPath': '/Game/Interval/Materials/'
                                       'T_IntervalControlDefault.T_IntervalControlDefault'},
                           'SamplerType': 'SAMPLERTYPE_LinearColor'})})
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionVectorParameter_0'},
     'values': json.dumps({'ParameterName': 'ChunkSize',
                           'DefaultValue': {'r': 64.0, 'g': 64.0, 'b': 4.0, 'a': 0.0}})})
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCollectionParameter_0'},
     'values': json.dumps({'Collection': {'refPath': '/Game/Interval/MPC_IntervalSky.MPC_IntervalSky'},
                           'ParameterName': 'Wet'})})
# Whether drops are landing NOW, as opposed to whether the ground remembers
# that they were. The rings want the first and the darkening wants the second.
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCollectionParameter_1'},
     'values': json.dumps({'Collection': {'refPath': '/Game/Interval/MPC_IntervalSky.MPC_IntervalSky'},
                           'ParameterName': 'Rain'})})

# A WORLD-SPACE NORMAL, NOT A TANGENT-SPACE ONE. The rain rings are the only
# thing this material perturbs, and they are described in world XY; asking for
# them in the tangent space of a mesh this window generates at runtime would
# make them depend on how that generator happened to lay its tangents out.
call(OBJ, 'set_properties', {'instance': {'refPath': M},
     'values': json.dumps({'bTangentSpaceNormal': False})})

blank = {'inputName': 'None', 'input': {'expression': 'None', 'outputIndex': 0,
         'inputName': 'None', 'mask': 0, 'maskR': 0, 'maskG': 0, 'maskB': 0, 'maskA': 0}}
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCustom_0'},
     'values': json.dumps({'Inputs': [blank] * 11})})

call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_0'},
     'values': json.dumps({'ParameterName': 'TileSize', 'DefaultValue': 200.0})})

def inp(name, expr, mask=0, rgb=False):
    return {'inputName': name, 'input': {'expression': {'refPath': M + ':' + expr},
            'outputIndex': 0, 'inputName': 'None', 'mask': mask,
            'maskR': int(rgb), 'maskG': int(rgb), 'maskB': int(rgb), 'maskA': 0}}

print('code:', call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCustom_0'},
      'values': json.dumps({
          'Code': open(SP + '/ground.hlsl').read(),
          'Description': 'ground',
          'OutputType': 'CMOT_Float3',
          'AdditionalOutputs': [{'outputName': 'Rough', 'outputType': 'CMOT_Float1'},
                                {'outputName': 'Normal', 'outputType': 'CMOT_Float3'}],
          'Inputs': [inp('UV', 'MaterialExpressionTextureCoordinate_0'),
                     inp('Control', 'MaterialExpressionTextureObjectParameter_0'),
                     inp('ChunkSize', 'MaterialExpressionVectorParameter_0', 1, True),
                     inp('W', 'MaterialExpressionWorldPosition_0', 1, True),
                     inp('Wet', 'MaterialExpressionCollectionParameter_0'),
                     inp('Time', 'MaterialExpressionTime_0'),
                     inp('Rain', 'MaterialExpressionCollectionParameter_1'),
                     inp('CamPos', 'MaterialExpressionCameraPositionWS_0', 1, True),
                     inp('N', 'MaterialExpressionVertexNormalWS_0', 1, True),
                     # WHERE THIS CHUNK'S CORNER IS. The tile coordinates are
                     # derived from world position now, and a position needs
                     # an origin to be measured from; a chunk actor is spawned
                     # exactly at its own corner tile. See ground.hlsl.
                     inp('Origin', 'MaterialExpressionActorPositionWS_0', 1, True),
                     # HOW BIG A TILE IS, in centimetres. Its own scalar and
                     # not a fourth component of `ChunkSize`: a vector
                     # parameter's default output is RGB, so a `.w` off it
                     # does not compile at all.
                     inp('Tile', 'MaterialExpressionScalarParameter_0')]})}))

for prop, out in (('MP_BaseColor', ''), ('MP_Roughness', 'Rough'),
                  ('MP_Normal', 'Normal')):
    call(MAT, 'connect_to_output', {'expression': {'refPath': M + ':MaterialExpressionCustom_0'},
         'output_name': out, 'material_property': prop})

r = call(MAT, 'recompile', {'material_or_function': {'refPath': M}})
bad = [l for l in r.split('\n') if 'error' in l.lower()]
print('compile:', bad[0][:200] if bad else 'clean')
print('save:', call('editor_toolset.toolsets.asset.AssetTools', 'save_assets',
                    {'asset_paths': ['/Game/Interval/Materials/M_IntervalGround']}))

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
