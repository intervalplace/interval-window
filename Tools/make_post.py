#!/usr/bin/env python3
"""KEPT AS A RECORD. Running this changes nothing you can see.

`AIntervalAir` spawns itself unbound at priority ten and overrides every
property below, so the level's own volume loses on all of them. That was found
out after an afternoon of writing numbers into it and photographing the result,
which is why this file still exists: the numbers were right and the PLACE was
wrong. They live on the look asset now -- ExposureAt, FilmToe, Occlusion -- and
the air reads them.

The original note follows, because the reasoning in it is still the reasoning.

The post process volume, set deliberately instead of by whatever was left.

WHY THIS IS A FILE AND NOT A THING SOMEBODY CLICKED.

The volume arrived with the TopDown template and nobody had looked at it. Two
of its settings were quietly deciding how the whole world reads:

  AUTO EXPOSURE. A window onto a world with an hour in it must NOT normalise
  its own brightness. The bridge computes where the sun is; this window turns
  that into a light; and then auto exposure spends six seconds undoing it, so
  that midnight and midday come out the same brightness and the only thing you
  can still tell apart is the colour. Everything this project does to make the
  hour legible is cancelled by one checkbox. Pinning the exposure -- minimum
  equal to maximum -- is what makes a dusk look like a dusk.

  THE TOE. `FilmToe` is how hard the tonemapper crushes the dark end. At the
  template's 0.55 a surface in shadow lands on the flat of the curve and comes
  out black -- which is what a rampart's north face, a tree's far side and the
  ground under a wall all were, and what four separate wrong diagnoses were
  chasing before anybody looked at the curve.

Run it after any change here; it writes to the level's volume and saves.
"""
import json, os, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import rpc

VOL = ('/Game/TopDown/Lvl_TopDown.Lvl_TopDown:PersistentLevel.'
       'PostProcessVolume_UAID_A4FC143F8D45840303_1325759232')
OBJ = 'editor_toolset.toolsets.object.ObjectTools'

# How bright the window is exposed for, in whatever units this project's sun is
# in -- which is the legacy range, since its noon is 6.2 and not a hundred
# thousand. Pinned, so the hour is what changes and not the camera.
EXPOSURE = 0.62

WANT = {
    'bOverride_AutoExposureMethod': True,
    'AutoExposureMethod': 'AEM_Histogram',
    'bOverride_AutoExposureMinBrightness': True,
    'bOverride_AutoExposureMaxBrightness': True,
    'AutoExposureMinBrightness': EXPOSURE,
    'AutoExposureMaxBrightness': EXPOSURE,
    'bOverride_AutoExposureBias': True,
    'AutoExposureBias': 0.0,

    # THE DARK END OF THE CURVE.
    # A shallower toe keeps a shadow a shadow instead of a hole. The shoulder
    # is left alone: the sky and a whitewashed gable are meant to roll off.
    'bOverride_FilmToe': True,
    'FilmToe': 0.20,
    'bOverride_FilmSlope': True,
    'FilmSlope': 0.86,
    'bOverride_FilmBlackClip': True,
    'FilmBlackClip': 0.0,

    # Screen-space occlusion at a metre and a quarter is a shadow the world did
    # not cast. Kept, because a corner should darken, but lightly.
    'bOverride_AmbientOcclusionIntensity': True,
    'AmbientOcclusionIntensity': 0.35,
    'bOverride_AmbientOcclusionRadius': True,
    'AmbientOcclusionRadius': 80.0,
}

if __name__ == '__main__':
    if len(sys.argv) > 1:
        WANT['AutoExposureMinBrightness'] = float(sys.argv[1])
        WANT['AutoExposureMaxBrightness'] = float(sys.argv[1])
    if len(sys.argv) > 2:
        WANT['FilmToe'] = float(sys.argv[2])
    rpc.call('EditorToolset.EditorAppToolset', 'StopPIE', {})
    print('set:', rpc.call(OBJ, 'set_properties', {
        'instance': {'refPath': VOL},
        'values': json.dumps({'Settings': WANT})}))
    # SAVE THE ACTOR, NOT THE MAP. This level is One File Per Actor, so the
    # volume is its own package under __ExternalActors__ and saving the map
    # leaves it behind -- the change then works until the editor restarts and
    # silently reverts, which is the worst kind of change.
    print('save:', rpc.call('editor_toolset.toolsets.scene.SceneTools', 'save_actor',
                            {'actor': {'refPath': VOL}}))
