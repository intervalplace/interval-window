#!/usr/bin/env python3
"""The one place every material reads the weather from.

A material parameter collection is a handful of numbers the whole project can
see. Without it, telling the ground it is raining means finding every chunk's
own material instance and setting it -- a hundred and twelve of them, rebuilt
whenever the citizen walks -- and the thatch and the timber could not be told
at all. One collection, set once a frame by whoever knows the hour.
"""
import json, os, subprocess, sys
import rpc as _rpc
SP = os.path.dirname(os.path.abspath(__file__))
C = '/Game/Interval/MPC_IntervalSky.MPC_IntervalSky'
MAT = 'editor_toolset.toolsets.material.MaterialTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'

def call(toolset, tool, args):
    # One session for the whole script; see Tools/rpc.py.
    return _rpc.call(toolset, tool, args)


# Stop the session first: rebuilding a collection the running world reads from
# wedges the editor, and it wedges on the first call.
call('EditorToolset.EditorAppToolset', 'StopPIE', {})

# NEVER DELETE AND RE-CREATE THIS ASSET.
#
# A material does not reference a collection parameter by NAME. It stores the
# parameter's GUID, and a fresh collection mints fresh GUIDs -- so deleting
# this and making another one at the same path silently unbinds every material
# that reads the weather. Nothing errors, nothing warns, the collection reads
# back with all the right parameter names, and the ground quietly stops knowing
# whether it is raining. It cost a green meadow turning to bare earth and an
# hour of looking for the reason.
#
# Updating in place keeps the GUIDs of the parameters that already exist and
# only mints one for anything new.
exists = call('editor_toolset.toolsets.asset.AssetTools', 'exists',
              {'path': '/Game/Interval/MPC_IntervalSky'})
if 'true' not in exists:
    print('create:', call(MAT, 'create_parameter_collection',
          {'folder_path': '/Game/Interval', 'asset_name': 'MPC_IntervalSky'})[:90])
else:
    print('updating the existing collection in place, to keep its GUIDs')

# `Gale` is how hard it is blowing, and it is DERIVED rather than invented:
# the world reports overcast and rain, and a wet grey day is a windy one. The
# foliage reads it, so every blade of grass on the island leans the same way at
# the same moment -- which is the whole reason it lives on the collection
# instead of in each material.
#
# AND THE SEASON, which is three numbers for the same reason the weather is.
#
# The year turns in twenty-eight days and `sky.mjs` already works out how far
# into spring, autumn or winter the world is, from `dayIdx % 28` alone. That
# makes it CONSTITUTIONAL rather than decorative: the day index is a fact every
# window over this world agrees on, so two people standing in the same field on
# different windows see the same autumn without the engine knowing the word.
# The bridge has been sending these three numbers for as long as it has sent
# the weather; nothing had read them.
#
# Three separate amounts rather than one "time of year", because they overlap
# at the edges and because a material wants to ask "how gold are the leaves"
# without doing arithmetic on a wrapped year. High summer is simply all three
# at zero, which is why it needs no parameter of its own.
scalars = [('Rain', 0.0), ('Day', 1.0), ('Wet', 0.0), ('Night', 0.0), ('Gale', 0.3),
           ('Autumn', 0.0), ('Winter', 0.0), ('Spring', 0.0)]
blank = {'ParameterName': 'None', 'DefaultValue': 0.0}
# Same two-step as everywhere else: the setter will not change a property's
# size and its elements in one call.
call(OBJ, 'set_properties', {'instance': {'refPath': C},
     'values': json.dumps({'ScalarParameters': [blank] * len(scalars)})})
call(OBJ, 'set_properties', {'instance': {'refPath': C},
     'values': json.dumps({'ScalarParameters': [
         {'ParameterName': n, 'DefaultValue': v} for n, v in scalars]})})

# WHERE THE CITIZEN IS STANDING, so that what grows underfoot can get out of
# their way. One vector, set once a frame by the hour, read by every blade of
# grass on the island -- the same reason the weather lives here.
vectors = [('Walker', {'r': 0.0, 'g': 0.0, 'b': 0.0, 'a': 0.0})]
blankv = {'ParameterName': 'None', 'DefaultValue': {'r': 0.0, 'g': 0.0, 'b': 0.0, 'a': 0.0}}
call(OBJ, 'set_properties', {'instance': {'refPath': C},
     'values': json.dumps({'VectorParameters': [blankv] * len(vectors)})})
call(OBJ, 'set_properties', {'instance': {'refPath': C},
     'values': json.dumps({'VectorParameters': [
         {'ParameterName': n, 'DefaultValue': v} for n, v in vectors]})})

print('save:', call('editor_toolset.toolsets.asset.AssetTools', 'save_assets',
                    {'asset_paths': ['/Game/Interval/MPC_IntervalSky']}))
print('check:', call(OBJ, 'get_properties', {'instance': {'refPath': C},
      'properties': ['ScalarParameters']})[:300])
