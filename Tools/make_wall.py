#!/usr/bin/env python3
"""Build M_IntervalWall: the master for everything that is a flat colour.

That is more than the flat-coloured people it was written for. Every composed
prop, wall, roof, cairn and scarecrow in this project is an engine primitive
with one colour on it, and they all used to hang off a second master that was
a vector wired straight to base colour and nothing else -- no weather, no
grain, no courses. Two masters doing one job is one master too many, so the
prop instances were moved here and this one grew what they needed.

The parameter NAMES are the whole trick. The FBX importer gives every imported
material a `DiffuseColor` vector holding the colour the artist chose; if this
material asks for a parameter of exactly that name, re-parenting an imported
instance onto it keeps the colour without anything having to copy it across.
"""
import json, os, subprocess, sys
import rpc as _rpc
SP = os.path.dirname(os.path.abspath(__file__))
M = '/Game/Interval/Materials/M_IntervalWall.M_IntervalWall'
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
     {'path': '/Game/Interval/Materials/M_IntervalWall'})
print('create:', call(MAT, 'create_material',
      {'folder_path': '/Game/Interval/Materials', 'asset_name': 'M_IntervalWall'})[:80])

# Both flags, both learned the hard way: a material without the matching usage
# bit is silently swapped for the default grey one, and the swap looks exactly
# like a shader that failed to compile.
call(OBJ, 'set_properties', {'instance': {'refPath': M}, 'values': json.dumps({
    'bUsedWithSkeletalMesh': True,
    'bUsedWithInstancedStaticMeshes': True,
    # MASKED, AND DITHERED. See the head of wall.hlsl for why this is a master
    # of its own rather than a switch on the flat one. The clip value is high
    # and the soft edge is handed to temporal AA, which is the arrangement the
    # thatch roof and the timber frame both use, so the three fade alike.
    'BlendMode': 'BLEND_Masked',
    'OpacityMaskClipValue': 0.33,
    'DitherOpacityMask': True,
})})

# APPENDED, NEVER INSERTED: every expression below is addressed by the index
# the engine gives it in creation order.
for cls in ('Custom', 'VectorParameter', 'ScalarParameter', 'ScalarParameter',
            'CollectionParameter', 'CollectionParameter',
            'WorldPosition', 'VertexNormalWS', 'ScalarParameter', 'ScalarParameter',
            'ScalarParameter', 'ScalarParameter', 'CameraPositionWS'):
    call(MAT, 'add_expression', {'material_or_function': {'refPath': M},
         'expression_class': {'refPath': '/Script/Engine.MaterialExpression' + cls},
         'x': -800, 'y': 0})

call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionVectorParameter_0'},
     'values': json.dumps({'ParameterName': 'DiffuseColor',
                           'DefaultValue': {'r': 0.5, 'g': 0.5, 'b': 0.5, 'a': 1.0}})})
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_0'},
     'values': json.dumps({'ParameterName': 'Shift', 'DefaultValue': 0.5})})
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_1'},
     'values': json.dumps({'ParameterName': 'Strength', 'DefaultValue': 0.0})})
# How rough the surface is when dry. Named `Rough` because that is what the
# hand-built prop instances already called it, and renaming a parameter that
# fourteen instances are keyed to buys nothing.
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_4'},
     'values': json.dumps({'ParameterName': 'Rough', 'DefaultValue': 0.88})})
# How tall one course of masonry is, in centimetres. Zero is "not masonry".
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_2'},
     'values': json.dumps({'ParameterName': 'Course', 'DefaultValue': 0.0})})
# How much the world-space mottle shows. A little on everything; a wall wants
# more than a shirt does.
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_3'},
     'values': json.dumps({'ParameterName': 'Grain', 'DefaultValue': 0.05})})
# HOW FAR APART THE BOARDS RUN, in centimetres, for a plank wall or a course
# of thatch. Zero is "this surface has no lines across it", which is most of
# them.
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_5'},
     'values': json.dumps({'ParameterName': 'Plank', 'DefaultValue': 0.0})})
# A WORLD-SPACE NORMAL, for the same reason the ground uses one: the grooves
# are described in world axes, and asking for them in the tangent space of a
# scaled engine primitive would make them depend on how that primitive's UVs
# happen to run.
call(OBJ, 'set_properties', {'instance': {'refPath': M},
     'values': json.dumps({'bTangentSpaceNormal': False})})
# WHERE THE CITIZEN IS, off the same collection the hour writes to. The cut at
# the tail of wall.hlsl reads this and nothing else does.
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCollectionParameter_1'},
     'values': json.dumps({'Collection': {'refPath': '/Game/Interval/MPC_IntervalSky.MPC_IntervalSky'},
                           'ParameterName': 'Walker'})})
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCollectionParameter_0'},
     'values': json.dumps({'Collection': {'refPath': '/Game/Interval/MPC_IntervalSky.MPC_IntervalSky'},
                           'ParameterName': 'Wet'})})

blank = {'inputName': 'None', 'input': {'expression': 'None', 'outputIndex': 0,
         'inputName': 'None', 'mask': 0, 'maskR': 0, 'maskG': 0, 'maskB': 0, 'maskA': 0}}
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCustom_0'},
     'values': json.dumps({'Inputs': [blank] * 12})})

def inp(name, expr, mask=0, rgb=False):
    return {'inputName': name, 'input': {'expression': {'refPath': M + ':' + expr},
            'outputIndex': 0, 'inputName': 'None', 'mask': mask,
            'maskR': int(rgb), 'maskG': int(rgb), 'maskB': int(rgb), 'maskA': 0}}

print('code:', call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCustom_0'},
      'values': json.dumps({
          'Code': open(SP + '/wall.hlsl').read(),
          'Description': 'wall',
          'OutputType': 'CMOT_Float3',
          'AdditionalOutputs': [{'outputName': 'Rough', 'outputType': 'CMOT_Float1'},
                                {'outputName': 'Normal', 'outputType': 'CMOT_Float3'},
                                {'outputName': 'Mask', 'outputType': 'CMOT_Float1'}],
          'Inputs': [inp('Base', 'MaterialExpressionVectorParameter_0', 1, True),
                     inp('Shift', 'MaterialExpressionScalarParameter_0'),
                     inp('Strength', 'MaterialExpressionScalarParameter_1'),
                     inp('Wet', 'MaterialExpressionCollectionParameter_0'),
                     inp('Walk', 'MaterialExpressionCollectionParameter_1', 1, True),
                     inp('Wp', 'MaterialExpressionWorldPosition_0', 1, True),
                     inp('Norm', 'MaterialExpressionVertexNormalWS_0', 1, True),
                     inp('Course', 'MaterialExpressionScalarParameter_2'),
                     inp('Grain', 'MaterialExpressionScalarParameter_3'),
                     # NOT `Rough`: that is already the name of one of this
                     # node's OUTPUTS, and a Custom node whose input and output
                     # share a name fails to compile with "redefinition of
                     # parameter" from inside generated engine code.
                     inp('DryRough', 'MaterialExpressionScalarParameter_4'),
                     inp('Plank', 'MaterialExpressionScalarParameter_5'),
                     inp('CamPos', 'MaterialExpressionCameraPositionWS_0', 1, True)]})}))

for prop, out in (('MP_BaseColor', ''), ('MP_Roughness', 'Rough'),
                  ('MP_Normal', 'Normal'), ('MP_OpacityMask', 'Mask')):
    call(MAT, 'connect_to_output', {'expression': {'refPath': M + ':MaterialExpressionCustom_0'},
         'output_name': out, 'material_property': prop})

r = call(MAT, 'recompile', {'material_or_function': {'refPath': M}})
bad = [l for l in r.split('\n') if 'error' in l.lower()]
print('compile:', bad[0][:300] if bad else 'clean')
print('save:', call('editor_toolset.toolsets.asset.AssetTools', 'save_assets',
                    {'asset_paths': ['/Game/Interval/Materials/M_IntervalWall']}))

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
