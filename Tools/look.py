#!/usr/bin/env python3
"""Point the editor viewport at the citizen, wherever they have got to.

Flying a free camera around an island that is mostly sea is a good way to lose
a person. This asks the bridge where the citizen is standing right now -- the
same frame Unreal is drawing from, so it cannot disagree -- and puts the
viewport camera a few metres off their shoulder.

  look.py            # over their shoulder
  look.py front      # facing them
  look.py 3000       # a wide view from that far up

Nothing here touches the world. It moves a camera.
"""
import json, os, subprocess, sys, urllib.request

SP = os.path.dirname(os.path.abspath(__file__))
TILE = 200.0          # IntervalGeometry::TileSize
# The bridge is a SIBLING of the project directory, not a child of it:
#   .../Unreal Projects/interval/Tools/look.py
#   .../Unreal Projects/interval-bridge/
BRIDGE = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), 'interval-bridge')

WHERE = '''
import { WebSocket } from 'ws'
const ws = new WebSocket('ws://127.0.0.1:7777')
ws.on('message', (d) => {
  const f = JSON.parse(d.toString())
  if (!f.players) return
  const me = f.me && f.players[f.me] ? f.players[f.me]
           : f.players[Object.keys(f.players)[0]]
  if (!me) return
  console.log(JSON.stringify({ x: me.x, y: me.y }))
  process.exit(0)
})
ws.on('error', (e) => { console.error(e.message); process.exit(1) })
setTimeout(() => process.exit(1), 20000)
'''

def ask_bridge():
    # Run from the bridge's own directory: `ws` is its dependency, not ours.
    tmp = os.path.join(BRIDGE, '_look.mjs')
    open(tmp, 'w').write(WHERE)
    try:
        out = subprocess.run(['node', tmp], cwd=BRIDGE, capture_output=True,
                             text=True, timeout=40).stdout.strip()
    finally:
        os.remove(tmp)
    if not out:
        raise SystemExit('the bridge said nothing -- is it running on 7777?')
    return json.loads(out)


def mcp(tool, args):
    json.dump(args, open(SP + '/_look.json', 'w'))
    return subprocess.run([sys.executable, SP + '/mcp.py',
                           'EditorToolset.EditorAppToolset', tool,
                           SP + '/_look.json'], capture_output=True, text=True).stdout


arg = sys.argv[1] if len(sys.argv) > 1 else ''
me = ask_bridge()
x, y = (me['x'] + 0.5) * TILE, (me['y'] + 0.5) * TILE

if arg.isdigit():
    high = float(arg)
    where = {'x': x - high * 0.6, 'y': y - high * 0.6, 'z': high}
    rot = {'pitch': -40.0, 'yaw': 45.0, 'roll': 0.0}
else:
    back = -1.0 if arg == 'front' else 1.0
    where = {'x': x - 120.0 * back, 'y': y - 100.0 * back, 'z': 140.0}
    rot = {'pitch': -4.0, 'yaw': 38.7 if back > 0 else 218.7, 'roll': 0.0}

print('citizen on tile %d,%d' % (me['x'], me['y']))
print(mcp('SetCameraTransform', {'transform': {'location': where, 'rotation': rot}})[:120])
