#!/usr/bin/env python3
"""Build M_IntervalHang: the flat master, plus a swing.

WHY A SECOND MASTER AND NOT A SWITCH ON THE FIRST. `M_IntervalFlat` is worn by
every composed prop, every wall, every roof and every forged piece in the
project -- which is most of the geometry on screen. A world position offset
belongs to the MATERIAL, not to the instance: wire one into the flat master
with an amplitude of zero and every wall in every settlement still pays the
vertex work to multiply it by zero. So the hanging things get their own master,
and nothing that does not hang is asked to think about hanging.

It is a DUPLICATE rather than a second copy of make_flat.py's graph, for the
same reason apply.py reads the look asset rather than the tables: two copies of
one graph drift, and the drift is invisible until somebody photographs a chain
next to a wall and the weather has stopped landing on one of them.

  make_hang.py        -- run it after make_flat.py, before dress_forged.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpc as _rpc

SP = os.path.dirname(os.path.abspath(__file__))
FLAT = '/Game/Interval/Materials/M_IntervalFlat'
HANG = '/Game/Interval/Materials/M_IntervalHang'
M = HANG + '.M_IntervalHang'
MAT = 'editor_toolset.toolsets.material.MaterialTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
AST = 'editor_toolset.toolsets.asset.AssetTools'

def call(toolset, tool, args):
    return _rpc.call(toolset, tool, args)

# See the note in make_flat.py: rebuilding an asset the running world holds
# wedges the editor, and it wedges on the FIRST call.
call('EditorToolset.EditorAppToolset', 'StopPIE', {})
call(AST, 'delete', {'path': HANG})
print('duplicate:', call(AST, 'duplicate', {'path': FLAT, 'new_path': HANG}))

# APPENDED, NEVER INSERTED, exactly as in make_flat.py: the duplicate carries
# the flat graph's expressions under their existing names, so everything added
# here takes the next index of its own class and nothing already wired moves.
for cls in ('Custom', 'ScalarParameter', 'ScalarParameter', 'LocalPosition',
            'ObjectPositionWS', 'Time', 'Constant3Vector', 'Constant3Vector',
            'Transform', 'Transform'):
    call(MAT, 'add_expression', {'material_or_function': {'refPath': M},
         'expression_class': {'refPath': '/Script/Engine.MaterialExpression' + cls},
         'x': -1400, 'y': 600})

E = lambda n: {'refPath': M + ':MaterialExpression' + n}

# HOW LONG THE RUN IS, in centimetres, so hang.hlsl can turn a local z into a
# fraction of the way down without knowing which object it is on. The chain is
# 91 cm; anything else that hangs sets its own.
call(OBJ, 'set_properties', {'instance': E('ScalarParameter_6'),
     'values': json.dumps({'ParameterName': 'HangLength', 'DefaultValue': 91.0})})
# AND HOW FAR THE TIP TRAVELS, likewise in centimetres. Nine is a chain
# breathing; thirty is a chain being swung, which is a different deed.
call(OBJ, 'set_properties', {'instance': E('ScalarParameter_7'),
     'values': json.dumps({'ParameterName': 'HangAmp', 'DefaultValue': 9.0})})

# THE TWO AXES THE SWING TRAVELS ALONG. A pendulum swings in a plane about its
# pivot, and which plane that is depends on how the hand is held -- so the
# directions are the OBJECT's own X and Y carried into world space, not world
# axes. A chain that swung north whichever way its owner faced would read as a
# chain being blown rather than one being carried.
for i, v in ((0, (1.0, 0.0, 0.0)), (1, (0.0, 1.0, 0.0))):
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
     'values': json.dumps({'Inputs': [blank] * 7})})

def inp(name, expr, rgb=False):
    return {'inputName': name, 'input': {'expression': E(expr),
            'outputIndex': 0, 'inputName': 'None', 'mask': int(rgb),
            'maskR': int(rgb), 'maskG': int(rgb), 'maskB': int(rgb), 'maskA': 0}}

print('code:', call(OBJ, 'set_properties', {'instance': E('Custom_1'),
      'values': json.dumps({
          'Code': open(os.path.join(SP, 'hang.hlsl')).read(),
          'Description': 'hang',
          'OutputType': 'CMOT_Float3',
          'Inputs': [inp('Local', 'LocalPosition_0', True),
                     inp('Length', 'ScalarParameter_6'),
                     inp('Amp', 'ScalarParameter_7'),
                     inp('Side', 'Transform_0', True),
                     inp('Fore', 'Transform_1', True),
                     inp('Pivot', 'ObjectPositionWS_0', True),
                     inp('Time', 'Time_0')]})})[:120])

call(MAT, 'connect_to_output', {'expression': E('Custom_1'),
     'output_name': '', 'material_property': 'MP_WorldPositionOffset'})

r = call(MAT, 'recompile', {'material_or_function': {'refPath': M}})
bad = [l for l in r.split('\n') if 'error' in l.lower()]
print('compile:', bad[0][:300] if bad else 'clean')
print('save:', call(AST, 'save_assets', {'asset_paths': [HANG]}))
print('NOW RUN dress_forged.py and apply.py')
