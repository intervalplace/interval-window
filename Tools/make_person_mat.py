#!/usr/bin/env python3
"""Build the two master materials: the people's, and the wood's."""
import json, os, subprocess, sys
import rpc as _rpc
SP = os.path.dirname(os.path.abspath(__file__))
MAT = 'editor_toolset.toolsets.material.MaterialTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
ART = '/Game/Interval/Universal/People/'

# STOP THE SESSION FIRST. Recompiling a material that actors in a running
# Simulate session are wearing wedges the editor solidly -- it keeps the port
# open, accepts connections and answers nothing, and it wedges on the first
# call, so stopping the session afterwards is already too late. Twice.
def call(toolset, tool, args):
    # One session for the whole script; see Tools/rpc.py.
    return _rpc.call(toolset, tool, args)


call('EditorToolset.EditorAppToolset', 'StopPIE', {})


def build(name, foliage):
    """One master, twice: the people's and the wood's.

    They are the same shader to the last line. What differs is one flag --
    Two Sided Foliage, which is a light TRANSPORT model and not a brightness
    knob -- and the one extra wire that feeds it. Keeping them as two copies of
    one script rather than two scripts is the point: a fix to the dye, the
    weather or the wind lands on the wood and on the citizen together, and
    there is no second file to forget.
    """
    M = '/Game/Interval/Materials/%s.%s' % (name, name)
    call('editor_toolset.toolsets.asset.AssetTools', 'delete',
         {'path': '/Game/Interval/Materials/' + name})
    print(name, 'create:', call(MAT, 'create_material',
          {'folder_path': '/Game/Interval/Materials', 'asset_name': name})[:80])

    flags = {
        'BlendMode': 'BLEND_Masked',
        'bUsedWithSkeletalMesh': True,
        'bUsedWithInstancedStaticMeshes': True,
    }
    if foliage:
        # TWO SIDED FOLIAGE IS A TRANSPORT PATH, NOT A BRIGHTNESS SETTING.
        # It is the one shading model that carries light THROUGH a surface to
        # the side away from the lamp, which is the whole of why a wood is
        # green and not a field of black cut-outs. See `Trans` in the shader.
        flags['ShadingModel'] = 'MSM_TwoSidedFoliage'
        flags['TwoSided'] = True
    call(OBJ, 'set_properties', {'instance': {'refPath': M}, 'values': json.dumps(flags)})

    for cls in ('Custom', 'TextureSampleParameter2D', 'TextureSampleParameter2D',
                'TextureSampleParameter2D', 'ScalarParameter', 'ScalarParameter',
                'ScalarParameter', 'ScalarParameter', 'CollectionParameter',
                'ScalarParameter', 'ScalarParameter', 'ScalarParameter',
                'ScalarParameter', 'ScalarParameter', 'VertexNormalWS',
                'PreSkinnedPosition',
                'VertexInterpolator', 'Multiply', 'Custom', 'PreSkinnedPosition',
                'WorldPosition', 'Time', 'ScalarParameter', 'ScalarParameter',
                'CollectionParameter', 'Add', 'CollectionParameter',
                # APPENDED, NEVER INSERTED. Every expression below is addressed by
                # the index the engine gives it in creation order, so a new node
                # put anywhere but the end silently renumbers the ones after it and
                # the material comes out wired to the wrong parameters.
                'ScalarParameter',
                # AND TWO MORE, for per-instance variation. Appended, for the
                # reason written directly above.
                'PerInstanceRandom', 'ScalarParameter',
                # AND ONE MORE: `Cover`, which decides whether the albedo's
                # ALPHA cuts the surface. Appended, for the reason above.
                'ScalarParameter',
                # AND THE SEASON, three amounts off the one collection the hour
                # writes. The year turns in twenty-eight days from the
                # constitutional day index alone, so every window over this
                # world agrees on the calendar without the engine having a word
                # for a season. Appended, for the reason written above.
                'CollectionParameter', 'CollectionParameter', 'CollectionParameter'):
        call(MAT, 'add_expression', {'material_or_function': {'refPath': M},
             'expression_class': {'refPath': '/Script/Engine.MaterialExpression' + cls},
             'x': -900, 'y': 0})

    # The parameter NAMES are what the instances will be built against. Defaults
    # are a real outfit so the master previews as a person rather than as a checker.
    # NOT `name`. That is the material being built, and rebinding it here once
    # sent every save below to /Game/Interval/Materials/ORMTexture -- which
    # succeeds, saves nothing, and leaves the real material unwritten.
    for i, (slot, tex, kind) in enumerate((
            ('BaseColorTexture', 'T_Peasant_BaseColor',  'SAMPLERTYPE_Color'),
            ('NormalTexture',    'T_Peasant_Normal',     'SAMPLERTYPE_Normal'),
            ('ORMTexture',       'T_Peasant_ORM',        'SAMPLERTYPE_LinearColor'))):
        call(OBJ, 'set_properties',
             {'instance': {'refPath': '%s:MaterialExpressionTextureSampleParameter2D_%d' % (M, i)},
              'values': json.dumps({'ParameterName': slot,
                                    'Texture': {'refPath': ART + tex + '.' + tex},
                                    'SamplerType': kind})})

    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_0'},
         'values': json.dumps({'ParameterName': 'Shift', 'DefaultValue': 0.5})})
    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_1'},
         'values': json.dumps({'ParameterName': 'Strength', 'DefaultValue': 1.0})})
    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_2'},
         'values': json.dumps({'ParameterName': 'Puff', 'DefaultValue': 0.0})})
    # Nothing is cut by default: a number far below any citizen's feet keeps the
    # whole surface, so a material that says nothing about it draws in full.
    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_3'},
         'values': json.dumps({'ParameterName': 'Cut', 'DefaultValue': -100000.0})})
    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_4'},
         'values': json.dumps({'ParameterName': 'RoughFloor', 'DefaultValue': 0.0})})
    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_5'},
         'values': json.dumps({'ParameterName': 'HairTint', 'DefaultValue': 0.0})})
    # Zero unless the sheet is a real ORM. See the note in the shader.
    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_6'},
         'values': json.dumps({'ParameterName': 'MetalMax', 'DefaultValue': 0.0})})
    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_7'},
         'values': json.dumps({'ParameterName': 'Pallor', 'DefaultValue': 0.0})})
    # One, for art that was painted for this renderer. More, for art that was not.
    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_10'},
         'values': json.dumps({'ParameterName': 'Lift', 'DefaultValue': 1.0})})
    # Nothing sways unless a level says so, and nothing is stiff by default either.
    # BELIEVE THE ORM'S OCCLUSION, UNLESS THERE IS NO ORM.
    #
    # `AO` is read from the red channel of the ORM sheet, and half the art in this
    # project ships no ORM at all -- the nature kit, the hairstyles, the armour --
    # so the COLOUR map stands in for one. Its red channel is then not occlusion,
    # it is how red the thing is, and a green leaf is (88,123,0): red 88, which is
    # 0.10 in linear, which tells the renderer that ninety per cent of the sky is
    # blocked from reaching a leaf hanging in open air. Every canopy went black at
    # noon and stayed black through four wrong diagnoses -- a lift, a normal map,
    # two-sidedness, an sRGB flag -- because the albedo was never the problem.
    #
    # A floor, not a switch, because a sheet that IS an ORM should keep its
    # occlusion. Zero here means "the sheet is telling the truth".
    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_11'},
         'values': json.dumps({'ParameterName': 'AOFloor', 'DefaultValue': 0.0})})
    # HOW MUCH THIS SHEET VARIES FROM COPY TO COPY. Zero for anything there is
    # only one of -- a person, an anvil -- and one for anything the world
    # stamps out in thousands. See the note in person_mat.hlsl.
    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_12'},
         'values': json.dumps({'ParameterName': 'Varies', 'DefaultValue': 0.0})})
    # DOES THIS SHEET'S ALPHA CUT THE SURFACE?
    #
    # Zero for a person, whose texture is opaque and whose only cut is the
    # collar. ONE for anything made of CARDS -- leaves, grass, flowers -- whose
    # sheet is a mostly-transparent atlas of leaf clusters, and whose alpha is
    # the only thing that says where the leaf ends and the air begins.
    #
    # It was never consulted. `Mask` was `(Skin.z >= Cut) ? 1 : 0`, and every
    # foliage instance sets `Cut` to -100000 so that the collar test always
    # passes -- which meant the mask came out 1 for every pixel of every leaf
    # card. So each card rendered as a full opaque QUAD: a bit of green leaf
    # and a great deal of the atlas's empty black. That is why every tree in
    # the world had a canopy of dark shattered shards instead of leaves, and
    # why the trunk beneath it looked fine -- bark is not a card and its sheet
    # has nothing to cut.
    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_13'},
         'values': json.dumps({'ParameterName': 'Cover', 'DefaultValue': 0.0})})
    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_8'},
         'values': json.dumps({'ParameterName': 'Sway', 'DefaultValue': 0.0})})
    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_9'},
         'values': json.dumps({'ParameterName': 'Stiff', 'DefaultValue': 1.0})})
    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCollectionParameter_1'},
         'values': json.dumps({'Collection': {'refPath': '/Game/Interval/MPC_IntervalSky.MPC_IntervalSky'},
                               'ParameterName': 'Gale'})})
    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCollectionParameter_2'},
         'values': json.dumps({'Collection': {'refPath': '/Game/Interval/MPC_IntervalSky.MPC_IntervalSky'},
                               'ParameterName': 'Walker'})})
    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCollectionParameter_0'},
         'values': json.dumps({'Collection': {'refPath': '/Game/Interval/MPC_IntervalSky.MPC_IntervalSky'},
                               'ParameterName': 'Wet'})})
    # the season, on the same collection
    for _n, _which in enumerate(('Autumn', 'Winter', 'Spring')):
        call(OBJ, 'set_properties',
             {'instance': {'refPath': M + ':MaterialExpressionCollectionParameter_%d' % (3 + _n)},
              'values': json.dumps({
                  'Collection': {'refPath': '/Game/Interval/MPC_IntervalSky.MPC_IntervalSky'},
                  'ParameterName': _which})})

    blank = {'inputName': 'None', 'input': {'expression': 'None', 'outputIndex': 0,
             'inputName': 'None', 'mask': 0, 'maskR': 0, 'maskG': 0, 'maskB': 0, 'maskA': 0}}
    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCustom_0'},
         'values': json.dumps({'Inputs': [blank] * 20})})

    def inp(name, expr, mask=0, rgb=False):
        return {'inputName': name, 'input': {'expression': {'refPath': M + ':' + expr},
                'outputIndex': 0, 'inputName': 'None', 'mask': mask,
                'maskR': int(rgb), 'maskG': int(rgb), 'maskB': int(rgb), 'maskA': 0}}

    # THE ALPHA CHANNEL ALONE, off the same sampler `Base` comes from. A leaf
    # atlas keeps the shape of the leaf in its alpha and nothing else does, so
    # this is the one lane that says where a card stops being a leaf.
    def alpha(name, expr):
        return {'inputName': name, 'input': {'expression': {'refPath': M + ':' + expr},
                'outputIndex': 0, 'inputName': 'None', 'mask': 1,
                'maskR': 0, 'maskG': 0, 'maskB': 0, 'maskA': 1}}

    print(name, 'code:', call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCustom_0'},
          'values': json.dumps({
              # LEAFY_FLAG IS SUBSTITUTED, NOT PARAMETERISED. One shader
              # becomes two materials and only the foliage one turns with the
              # year; a scalar parameter would mean a node, an input and a
              # default on both, to carry a number that is known here.
              'Code': open(SP + '/person_mat.hlsl').read()
                      .replace('LEAFY_FLAG', '1.0' if foliage else '0.0'),
              'Description': 'person',
              'OutputType': 'CMOT_Float3',
              'AdditionalOutputs': [{'outputName': 'Rough', 'outputType': 'CMOT_Float1'},
                                    {'outputName': 'Metal', 'outputType': 'CMOT_Float1'},
                                    {'outputName': 'AO',    'outputType': 'CMOT_Float1'},
                                    {'outputName': 'Mask',  'outputType': 'CMOT_Float1'},
                                {'outputName': 'Trans', 'outputType': 'CMOT_Float3'}],
              'Inputs': [inp('Base', 'MaterialExpressionTextureSampleParameter2D_0', 1, True),
                         inp('ORM',  'MaterialExpressionTextureSampleParameter2D_2', 1, True),
                         inp('Shift', 'MaterialExpressionScalarParameter_0'),
                         inp('Strength', 'MaterialExpressionScalarParameter_1'),
                         inp('Wet', 'MaterialExpressionCollectionParameter_0'),
                         inp('Skin', 'MaterialExpressionVertexInterpolator_0', 1, True),
                         inp('Cut', 'MaterialExpressionScalarParameter_3'),
                         inp('RoughFloor', 'MaterialExpressionScalarParameter_4'),
                         inp('HairTint', 'MaterialExpressionScalarParameter_5'),
                         inp('MetalMax', 'MaterialExpressionScalarParameter_6'),
                         inp('Pallor', 'MaterialExpressionScalarParameter_7'),
                         inp('Lift', 'MaterialExpressionScalarParameter_10'),
                         inp('AOFloor', 'MaterialExpressionScalarParameter_11'),
                         inp('Vary', 'MaterialExpressionPerInstanceRandom_0'),
                         inp('Varies', 'MaterialExpressionScalarParameter_12'),
                         alpha('Sheet', 'MaterialExpressionTextureSampleParameter2D_0'),
                         inp('Cover', 'MaterialExpressionScalarParameter_13'),
                         inp('Autumn', 'MaterialExpressionCollectionParameter_3'),
                         inp('Winter', 'MaterialExpressionCollectionParameter_4'),
                         inp('Spring', 'MaterialExpressionCollectionParameter_5')]})}))

    # THE BIND-POSE POSITION IS A VERTEX-SHADER FACT.
    #
    # `PreSkinnedPosition` is not available to the pixel shader, and the opacity
    # mask is a pixel-shader output, so reading one from the other fails outright:
    #   "External code identifier 'PreSkinnedPosition' is not available in the
    #    EMaterialShaderFrequency::Pixel shader."
    # A vertex interpolator is the bridge -- it evaluates in the vertex shader and
    # carries the value across, which is exactly what it is for.
    # ---- THE WIND, WHICH IS A VERTEX-SHADER NODE OF ITS OWN --------------------
    #
    # It cannot share the node above: that one reads a vertex interpolator, which
    # makes it pixel-only, and world position offset is a vertex output.
    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCustom_1'},
         'values': json.dumps({'Inputs': [blank] * 7})})

    def winp(name, expr, mask=0, rgb=False):
        return {'inputName': name, 'input': {'expression': {'refPath': M + ':' + expr},
                'outputIndex': 0, 'inputName': 'None', 'mask': mask,
                'maskR': int(rgb), 'maskG': int(rgb), 'maskB': int(rgb), 'maskA': 0}}

    print(name, 'wind:', call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCustom_1'},
          'values': json.dumps({
              'Code': open(SP + '/wind.hlsl').read(),
              'Description': 'wind',
              'OutputType': 'CMOT_Float3',
              'Inputs': [winp('Local', 'MaterialExpressionPreSkinnedPosition_1', 1, True),
                         winp('World', 'MaterialExpressionWorldPosition_0', 1, True),
                         winp('Time', 'MaterialExpressionTime_0'),
                         winp('Sway', 'MaterialExpressionScalarParameter_8'),
                         winp('Stiff', 'MaterialExpressionScalarParameter_9'),
                         winp('Gale', 'MaterialExpressionCollectionParameter_1'),
                         winp('Walker', 'MaterialExpressionCollectionParameter_2', 1, True)]})}))

    # The cloth stand-off, in the graph rather than in the node above.
    for pin, src in (('A', 'MaterialExpressionVertexNormalWS_0'),
                     ('B', 'MaterialExpressionScalarParameter_2')):
        print(name, 'puff ' + pin + ':', call(MAT, 'connect_expressions', {
            'from_expression': {'refPath': M + ':' + src}, 'from_output_name': '',
            'to_expression': {'refPath': M + ':MaterialExpressionMultiply_0'},
            'to_input_name': pin}))
    # Both offsets reach the same output: a garment stands off the body AND a leaf
    # moves in the wind, and no surface is ever asked to do both.
    for pin, src in (('A', 'MaterialExpressionMultiply_0'),
                     ('B', 'MaterialExpressionCustom_1')):
        call(MAT, 'connect_expressions', {
            'from_expression': {'refPath': M + ':' + src}, 'from_output_name': '',
            'to_expression': {'refPath': M + ':MaterialExpressionAdd_0'},
            'to_input_name': pin})
    call(MAT, 'connect_to_output', {'expression': {'refPath': M + ':MaterialExpressionAdd_0'},
         'output_name': '', 'material_property': 'MP_WorldPositionOffset'})

    print(name, 'interp:', call(MAT, 'connect_expressions', {
        'from_expression': {'refPath': M + ':MaterialExpressionPreSkinnedPosition_0'},
        'from_output_name': '',
        'to_expression': {'refPath': M + ':MaterialExpressionVertexInterpolator_0'},
        'to_input_name': 'VS'}))   # its pins are VS in, PS out

    wires = [('MP_BaseColor', ''), ('MP_Roughness', 'Rough'),
             ('MP_Metallic', 'Metal'), ('MP_AmbientOcclusion', 'AO'),
             ('MP_OpacityMask', 'Mask')]
    if foliage:
        wires.append(('MP_SubsurfaceColor', 'Trans'))
    for prop, out in wires:
        call(MAT, 'connect_to_output', {'expression': {'refPath': M + ':MaterialExpressionCustom_0'},
             'output_name': out, 'material_property': prop})
    # The normal map goes straight through; there is nothing to do to it.
    call(MAT, 'connect_to_output',
         {'expression': {'refPath': M + ':MaterialExpressionTextureSampleParameter2D_1'},
          'output_name': '', 'material_property': 'MP_Normal'})

    # LOOK FOR FAILURE, NOT FOR THE WORD "ERROR". The compiler answers a broken
    # material with "Material failed to compile: ..." and no "error" anywhere in
    # it, so a grep for that word reported a clean build over a material that was
    # falling back to the default grey one -- which is precisely the symptom that
    # has now cost this project three separate afternoons.
    r = call(MAT, 'recompile', {'material_or_function': {'refPath': M}})
    bad = [l for l in r.split('\n')
           if any(w in l.lower() for w in ('error', 'fail', 'not available', 'warning'))]
    print(name, 'compile:', '\n  '.join(bad)[:600] if bad else 'clean')
    print(name, 'save:', call('editor_toolset.toolsets.asset.AssetTools', 'save_assets',
                        {'asset_paths': ['/Game/Interval/Materials/' + name]}))


build('M_IntervalPerson', False)
build('M_IntervalFoliage', True)

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
