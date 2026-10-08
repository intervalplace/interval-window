#!/usr/bin/env python3
"""Build M_IntervalWings: the flat master, plus a wing beat.

The same argument as `make_hang.py`, one word different. A world position
offset belongs to the MATERIAL and not to the instance, so wiring a flap into
the flat master would have every wall in every settlement pay the vertex work
to multiply it by zero. The birds get their own master.

A DUPLICATE of the flat master rather than a second copy of its graph, for the
same reason: two copies of one graph drift, and the drift is invisible until
somebody photographs a bird against a wall and the weather has stopped landing
on one of them.

  make_wings.py       -- run it after make_flat.py, before apply.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpc as _rpc

SP = os.path.dirname(os.path.abspath(__file__))
FLAT = '/Game/Interval/Materials/M_IntervalFlat'
WINGS = '/Game/Interval/Materials/M_IntervalWings'
M = WINGS + '.M_IntervalWings'
MAT = 'editor_toolset.toolsets.material.MaterialTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
AST = 'editor_toolset.toolsets.asset.AssetTools'

def call(toolset, tool, args):
    return _rpc.call(toolset, tool, args)

# See the note in make_flat.py: rebuilding an asset the running world holds
# wedges the editor, and it wedges on the FIRST call.
call('EditorToolset.EditorAppToolset', 'StopPIE', {})
call(AST, 'delete', {'path': WINGS})
print('duplicate:', call(AST, 'duplicate', {'path': FLAT, 'new_path': WINGS}))

# APPENDED, NEVER INSERTED, exactly as in make_flat.py: the duplicate carries
# the flat graph's expressions under their existing names, so everything added
# here takes the next index of its own class and nothing already wired moves.
for cls in ('Custom', 'ScalarParameter', 'ScalarParameter', 'ScalarParameter',
            'LocalPosition', 'Time', 'PerInstanceRandom',
            'Constant3Vector', 'Constant3Vector', 'Constant3Vector',
            'Transform', 'Transform', 'Transform'):
    call(MAT, 'add_expression', {'material_or_function': {'refPath': M},
         'expression_class': {'refPath': '/Script/Engine.MaterialExpression' + cls},
         'x': -1400, 'y': 600})

E = lambda n: {'refPath': M + ':MaterialExpression' + n}

# HALF THE WINGSPAN, in centimetres, so wings.hlsl can turn a local y into a
# fraction of the way out without knowing which bird it is on. The forged one
# is 94 cm across, so 47.
call(OBJ, 'set_properties', {'instance': E('ScalarParameter_6'),
     'values': json.dumps({'ParameterName': 'Span', 'DefaultValue': 47.0})})
# AND HOW FAR THE TIP TRAVELS, likewise in centimetres. A crow's wingtip moves
# through about a third of its own span; 16 is that, and more reads as a moth.
call(OBJ, 'set_properties', {'instance': E('ScalarParameter_7'),
     'values': json.dumps({'ParameterName': 'Amp', 'DefaultValue': 16.0})})
# BEATS A SECOND. A crow is between two and three; slower reads as an eagle and
# faster reads as an insect, and at this distance that is the whole difference
# between a bird and a fly on the lens.
call(OBJ, 'set_properties', {'instance': E('ScalarParameter_8'),
     'values': json.dumps({'ParameterName': 'Rate', 'DefaultValue': 2.4})})

# THE THREE AXES THE BEAT IS BUILT FROM. A bird's up is the bird's own up: it
# heads wherever it is going and may bank, and a flap offset along WORLD z
# would be right only for one flying dead level. So the object's own X, Y and
# Z are carried into world space and the shader works in those.
for i, v in ((0, (1.0, 0.0, 0.0)), (1, (0.0, 1.0, 0.0)), (2, (0.0, 0.0, 1.0))):
    call(OBJ, 'set_properties', {'instance': E('Constant3Vector_%d' % i),
         'values': json.dumps({'Constant': {'r': v[0], 'g': v[1], 'b': v[2], 'a': 0.0}})})
    call(OBJ, 'set_properties', {'instance': E('Transform_%d' % i),
         'values': json.dumps({'TransformSourceType': 'TRANSFORMSOURCE_Local',
                               'TransformType': 'TRANSFORM_World'})})
    # THE PIN HAS NO NAME, and `Input` is not it. A Transform node's single
    # input is unnamed -- `get_expression_input_names` answers `["None"]` --
    # and connecting to a pin that does not exist is accepted in silence: the
    # node keeps an unwired input, hands back nothing, and the swing comes out
    # exactly zero while every other check reads clean. The material compiled,
    # the offset was connected, the instance had its parameters, and the chain
    # hung as still as it had before.
    call(MAT, 'connect_expressions', {
        'from_expression': E('Constant3Vector_%d' % i), 'from_output_name': '',
        'to_expression': E('Transform_%d' % i), 'to_input_name': ''})

blank = {'inputName': 'None', 'input': {'expression': 'None', 'outputIndex': 0,
         'inputName': 'None', 'mask': 0, 'maskR': 0, 'maskG': 0, 'maskB': 0, 'maskA': 0}}
call(OBJ, 'set_properties', {'instance': E('Custom_1'),
     'values': json.dumps({'Inputs': [blank] * 9})})

def inp(name, expr, rgb=False):
    return {'inputName': name, 'input': {'expression': E(expr),
            'outputIndex': 0, 'inputName': 'None', 'mask': int(rgb),
            'maskR': int(rgb), 'maskG': int(rgb), 'maskB': int(rgb), 'maskA': 0}}

print('code:', call(OBJ, 'set_properties', {'instance': E('Custom_1'),
      'values': json.dumps({
          'Code': open(os.path.join(SP, 'wings.hlsl')).read(),
          'Description': 'wings',
          'OutputType': 'CMOT_Float3',
          'Inputs': [inp('Local', 'LocalPosition_0', True),
                     inp('Span', 'ScalarParameter_6'),
                     inp('Amp', 'ScalarParameter_7'),
                     inp('Rate', 'ScalarParameter_8'),
                     inp('Phase', 'PerInstanceRandom_0'),
                     inp('Fore', 'Transform_0', True),
                     inp('Side', 'Transform_1', True),
                     inp('Up', 'Transform_2', True),
                     inp('Time', 'Time_0')]})})[:120])

call(MAT, 'connect_to_output', {'expression': E('Custom_1'),
     'output_name': '', 'material_property': 'MP_WorldPositionOffset'})

r = call(MAT, 'recompile', {'material_or_function': {'refPath': M}})
bad = [l for l in r.split('\n') if 'error' in l.lower()]
print('compile:', bad[0][:300] if bad else 'clean')
print('save:', call(AST, 'save_assets', {'asset_paths': [WINGS]}))
print('NOW RUN apply.py -- the look points at this by path')
