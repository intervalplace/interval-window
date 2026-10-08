#!/usr/bin/env python3
"""Build M_IntervalPerson from person.hlsl, and SAVE it.

A material created over MCP and not saved is gone at the next rebuild, like
everything else here. This is the whole recipe, so it can be run again.
"""
import json, os, subprocess, sys
import rpc as _rpc
SP = os.path.dirname(os.path.abspath(__file__))
M = '/Game/Interval/Materials/M_IntervalPerson.M_IntervalPerson'

def call(toolset, tool, args):
    # One session for the whole script; see Tools/rpc.py.
    return _rpc.call(toolset, tool, args)


MAT = 'editor_toolset.toolsets.material.MaterialTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'

# Built from scratch every time. Editing a material in place over MCP means
# guessing which nodes are already there and what they are called; deleting
# first makes this recipe the only thing that decides what the asset contains.
call('editor_toolset.toolsets.asset.AssetTools', 'delete',
     {'path': '/Game/Interval/Materials/M_IntervalPerson'})
print('create:', call(MAT, 'create_material',
                      {'folder_path': '/Game/Interval/Materials',
                       'asset_name': 'M_IntervalPerson'})[:90])
for cls in ('Custom', 'WorldPosition', 'ScalarParameter', 'ScalarParameter',
            'ScalarParameter', 'ScalarParameter', 'ScalarParameter',
            'VectorParameter', 'VectorParameter'):
    call(MAT, 'add_expression', {'material_or_function': {'refPath': M},
         'expression_class': {'refPath': '/Script/Engine.MaterialExpression' + cls},
         'x': -800, 'y': 0})

call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_0'},
     'values': json.dumps({'ParameterName': 'Who', 'DefaultValue': 0.5})})
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_1'},
     'values': json.dumps({'ParameterName': 'Tall', 'DefaultValue': 1.0})})
for i, (name, dv) in enumerate((('Hue', 0.1), ('Skin', 2.0), ('Hair', 1.0)), start=2):
    call(OBJ, 'set_properties',
         {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_%d' % i},
          'values': json.dumps({'ParameterName': name, 'DefaultValue': dv})})
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionVectorParameter_0'},
     'values': json.dumps({'ParameterName': 'Foot'})})
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionVectorParameter_1'},
     'values': json.dumps({'ParameterName': 'Fore',
                           'DefaultValue': {'r': 1.0, 'g': 0.0, 'b': 0.0, 'a': 1.0}})})

# THE ARRAY GROWS FIRST, THEN FILLS. The setter refuses to change a property's
# size and its elements in one call -- "insertion points are ambiguous" -- so
# a Custom node with more than the one default input takes two.
blank = {'inputName': 'None', 'input': {'expression': 'None', 'outputIndex': 0,
         'inputName': 'None', 'mask': 0, 'maskR': 0, 'maskG': 0, 'maskB': 0, 'maskA': 0}}
call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCustom_0'},
     'values': json.dumps({'Inputs': [blank] * 8})})

def inp(name, expr, mask=0, rgb=False):
    return {'inputName': name, 'input': {'expression': {'refPath': M + ':' + expr},
            'outputIndex': 0, 'inputName': 'None', 'mask': mask,
            'maskR': int(rgb), 'maskG': int(rgb), 'maskB': int(rgb), 'maskA': 0}}

print('code:', call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCustom_0'},
      'values': json.dumps({
          'Code': open(SP + '/person.hlsl').read(),
          'Description': 'person',
          'OutputType': 'CMOT_Float3',
          'AdditionalOutputs': [{'outputName': 'Rough', 'outputType': 'CMOT_Float1'},
                                {'outputName': 'Shape', 'outputType': 'CMOT_Float3'}],
          'Inputs': [inp('W', 'MaterialExpressionWorldPosition_0', 1, True),
                     inp('Who', 'MaterialExpressionScalarParameter_0'),
                     inp('Foot', 'MaterialExpressionVectorParameter_0', 1, True),
                     inp('Fore', 'MaterialExpressionVectorParameter_1', 1, True),
                     inp('Tall', 'MaterialExpressionScalarParameter_1'),
                     inp('Hue', 'MaterialExpressionScalarParameter_2'),
                     inp('Skin', 'MaterialExpressionScalarParameter_3'),
                     inp('Hair', 'MaterialExpressionScalarParameter_4')]})}))

# THE USAGE FLAG, WITHOUT WHICH NONE OF THE ABOVE HAPPENS.
# A material that has not been marked as usable on a skeletal mesh is silently
# swapped for the default one at draw time -- no warning, no error, the graph
# compiles clean and the figure just comes out plain. An afternoon went into
# the identical fault on instanced meshes earlier in this project; it looked
# like a shader bug both times and was a checkbox both times.
call(OBJ, 'set_properties', {'instance': {'refPath': M},
     'values': json.dumps({'bUsedWithSkeletalMesh': True})})

for prop, out in (('MP_BaseColor', ''), ('MP_Roughness', 'Rough'),
                  ('MP_WorldPositionOffset', 'Shape')):
    call(MAT, 'connect_to_output', {'expression': {'refPath': M + ':MaterialExpressionCustom_0'},
         'output_name': out, 'material_property': prop})

r = call(MAT, 'recompile', {'material_or_function': {'refPath': M}})
bad = [l for l in r.split('\n') if 'error' in l.lower()]
print('compile:', bad[0][:160] if bad else 'clean')
print('save:', call('editor_toolset.toolsets.asset.AssetTools', 'save_assets',
                    {'asset_paths': ['/Game/Interval/Materials/M_IntervalPerson']}))
