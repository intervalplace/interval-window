#!/usr/bin/env python3
"""Stand meshes in a row in the editor and photograph them, then take them away.

An asset thumbnail is no use for judging a helmet: it is 512 pixels of whatever
the thumbnail camera felt like, and for a mesh two centimetres across it comes
out as a speck. And a piece of armour cannot be judged in the world either,
because the world gives it to somebody when it feels like it and not before.

So they are stood in a row in the EDITOR level -- no Simulate, no world built,
nothing running -- photographed at a scale that matches a citizen, and deleted
again. The actors are named `__rack_*` and this script removes every one of
them before it starts as well as after it finishes, so an interrupted run
cannot leave furniture in the level.

  rack.py out.png <scale> /Game/A /Game/B ...
"""
import json, os, re, subprocess, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import rpc

SCENE = 'editor_toolset.toolsets.scene.SceneTools'
APP = 'EditorToolset.EditorAppToolset'
STEP = 80.0            # centimetres between one piece and the next
HERE = (0.0, 0.0, 300.0)
YAW = float(os.environ.get('RACK_YAW', '0'))
PITCH = float(os.environ.get('RACK_PITCH', '0'))
ROLL = float(os.environ.get('RACK_ROLL', '0'))


def sweep():
    found = json.loads(rpc.call(SCENE, 'find_actors',
                                {'name': '__rack', 'tag': '',
                                 'collision_channels': []}))['returnValue']
    for a in found:
        rpc.call(SCENE, 'remove_from_scene', {'actor': a})
    return len(found)


def main(out, scale, assets):
    rpc.call(APP, 'StopPIE', {})
    gone = sweep()
    if gone:
        print('cleared %d left over' % gone)
    wide = STEP * (len(assets) - 1)
    for i, a in enumerate(assets):
        rpc.call(SCENE, 'add_to_scene_from_asset', {
            'asset_path': a, 'name': '__rack_%d' % i,
            'xform': {'location': {'x': HERE[0] - wide / 2 + i * STEP,
                                   'y': HERE[1], 'z': HERE[2]},
                      # A QUARTER TURN EACH. A helmet photographed from one
                      # side is a helmet you cannot judge, and a breastplate
                      # seen edge-on is a sheet of paper -- which is what the
                      # first rack of these looked like and was not.
                      'rotation': {'pitch': PITCH, 'yaw': YAW, 'roll': ROLL},
                      'scale': {'x': scale, 'y': scale, 'z': scale}}})
    # Far enough back to hold the whole row, low enough to see the shapes.
    # The camera goes to `cap.py`, not to SetCameraTransform: the capture takes
    # its own transform and refuses the call without one, so moving the
    # viewport first and photographing second photographs the old view.
    subprocess.run([sys.executable, SP + '/cap.py', out,
                    str(HERE[0]),
                    # A FLOOR ON THE DISTANCE: with one piece in the rack the
                    # row is zero across and the camera ends up inside the
                    # thing it is photographing.
                    str(HERE[1] - max(wide * 0.72, 260.0) - 180.0),
                    str(HERE[2] + 6.0),
                    '-2', '90', '0', '1300'], check=True)
    sweep()
    print(out)


if __name__ == '__main__':
    main(sys.argv[1], float(sys.argv[2]), sys.argv[3:])
