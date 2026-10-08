#!/usr/bin/env python3
"""Build M_IntervalSmoke and M_IntervalEmber -- the two particle materials.

Both are the same shape: a Custom node fed the particle's UV, colour, age and
random seed, writing colour and opacity. They differ in blend mode and in
which of the two shader files they carry, so they are built by one function
called twice, the way the person and foliage masters are.
"""
import json, os
import rpc as _rpc

SP = os.path.dirname(os.path.abspath(__file__))
MAT = 'editor_toolset.toolsets.material.MaterialTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
AST = 'editor_toolset.toolsets.asset.AssetTools'
FOLDER = '/Game/Interval/Materials'


def call(toolset, tool, args):
    # One session for the whole script; see Tools/rpc.py.
    return _rpc.call(toolset, tool, args)


# EXPRESSIONS ARE ADDRESSED BY CREATION ORDER. The editor names them
# MaterialExpression<Class>_<nth of that class>, so this list is the material's
# wiring diagram and anything new goes on the END of it. Inserting in the
# middle silently renumbers every later node and the connections land on the
# wrong pins with a clean compile.
NODES = ['Custom', 'TextureCoordinate', 'ParticleColor', 'ParticleRelativeTime',
         'ParticleRandom', 'DepthFade', 'Time', 'ScalarParameter']


def build(name, code, additive):
    M = '%s/%s.%s' % (FOLDER, name, name)
    call(AST, 'delete', {'path': '%s/%s' % (FOLDER, name)})
    print('create:', call(MAT, 'create_material',
          {'folder_path': FOLDER, 'asset_name': name})[:70])

    # WHY THE LIT ONE IS LIT.
    #
    # Smoke over a hearth is a pale thing at noon and an orange thing at dusk,
    # and a flat unlit grey is neither. A volumetric per-vertex lighting mode
    # gives a translucent sprite the sun AND the hearth's own point light for
    # about the cost of a vertex, which is the cheapest honest answer.
    # An ember is a light source and has nothing to be lit BY, so it is unlit
    # and additive -- what it returns is what lands on the frame.
    call(OBJ, 'set_properties', {'instance': {'refPath': M}, 'values': json.dumps({
        'MaterialDomain': 'MD_Surface',
        'BlendMode': 'BLEND_Additive' if additive else 'BLEND_Translucent',
        'ShadingModel': 'MSM_Unlit' if additive else 'MSM_DefaultLit',
        'TranslucencyLightingMode': 'TLM_VolumetricPerVertexDirectional',
        'TwoSided': True,
        # WITHOUT THESE IT DRAWS NOTHING. A material is only compiled for the
        # vertex factories it says it is used with, and a sprite particle is
        # its own factory. The permutation is simply missing otherwise, and the
        # renderer falls back to the default checker with no error anywhere.
        'bUsedWithNiagaraSprites': True,
        'bUsedWithParticleSprites': True,
        'bUsedWithStaticLighting': False,
        'bCastDynamicShadowAsMasked': False,
    })})

    for cls in NODES:
        call(MAT, 'add_expression', {'material_or_function': {'refPath': M},
             'expression_class': {'refPath': '/Script/Engine.MaterialExpression' + cls},
             'x': -800, 'y': 0})

    # How far into the surface behind it the sprite fades out. A hundred and
    # forty centimetres is about half a roof's thickness: enough that a puff
    # leaving a ridge has no straight edge across the thatch, not so much that
    # the whole puff disappears into it.
    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionDepthFade_0'},
         'values': json.dumps({'OpacityDefault': 1.0, 'FadeDistanceDefault': 140.0})})
    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionScalarParameter_0'},
         'values': json.dumps({'ParameterName': 'Thin', 'DefaultValue': 1.0})})

    # Same two-step as everywhere else: the setter will not grow a property and
    # fill its elements in one call.
    blank = {'inputName': 'None', 'input': {'expression': 'None', 'outputIndex': 0,
             'inputName': 'None', 'mask': 0, 'maskR': 0, 'maskG': 0, 'maskB': 0, 'maskA': 0}}
    call(OBJ, 'set_properties', {'instance': {'refPath': M + ':MaterialExpressionCustom_0'},
         'values': json.dumps({'Inputs': [blank] * 8})})

    def inp(label, expr, mask=0, r=0, g=0, b=0, a=0):
        return {'inputName': label,
                'input': {'expression': {'refPath': M + ':' + expr}, 'outputIndex': 0,
                          'inputName': 'None', 'mask': mask,
                          'maskR': r, 'maskG': g, 'maskB': b, 'maskA': a}}

    print('code:', call(OBJ, 'set_properties',
          {'instance': {'refPath': M + ':MaterialExpressionCustom_0'}, 'values': json.dumps({
              'Code': open(os.path.join(SP, code)).read(),
              'Description': name,
              'OutputType': 'CMOT_Float3',
              'AdditionalOutputs': [{'outputName': 'Opacity', 'outputType': 'CMOT_Float1'}],
              'Inputs': [
                  inp('UV', 'MaterialExpressionTextureCoordinate_0'),
                  # THE PARTICLE'S COLOUR AND ITS ALPHA, SEPARATELY. One
                  # expression, two masks: rgb for the tint and a on its own for
                  # how solid the puff is, because the alpha is what the
                  # emitter's fade curve is actually writing to.
                  inp('PC', 'MaterialExpressionParticleColor_0', 1, 1, 1, 1, 0),
                  inp('PA', 'MaterialExpressionParticleColor_0', 1, 0, 0, 0, 1),
                  inp('Age', 'MaterialExpressionParticleRelativeTime_0'),
                  inp('Seed', 'MaterialExpressionParticleRandom_0'),
                  inp('Soft', 'MaterialExpressionDepthFade_0'),
                  inp('T', 'MaterialExpressionTime_0'),
                  inp('Thin', 'MaterialExpressionScalarParameter_0'),
              ]})}))

    for prop, out in ((('MP_EmissiveColor' if additive else 'MP_BaseColor'), ''),
                      ('MP_Opacity', 'Opacity')):
        call(MAT, 'connect_to_output', {'expression': {'refPath': M + ':MaterialExpressionCustom_0'},
             'output_name': out, 'material_property': prop})

    r = call(MAT, 'recompile', {'material_or_function': {'refPath': M}})
    # Look for FAILURE, not for the word "error": Unreal says "Material failed
    # to compile" without it, and a grep for the word reports clean over a
    # material that is quietly falling back to the default.
    bad = [l for l in r.split('\n')
           if any(w in l.lower() for w in ('error', 'fail', 'not available'))]
    print('compile:', '\n  '.join(bad)[:600] if bad else 'clean')
    print('save:', call(AST, 'save_assets', {'asset_paths': ['%s/%s' % (FOLDER, name)]})[:60])


# Recompiling a material the running world is using wedges the editor, and it
# wedges on the first call rather than the one that matters.
call('EditorToolset.EditorAppToolset', 'StopPIE', {})
build('M_IntervalSmoke', 'smoke.hlsl', additive=False)
build('M_IntervalEmber', 'ember.hlsl', additive=True)
print('NOW RUN make_fx.py -- the emitters point at these by path')
