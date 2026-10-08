#!/usr/bin/env python3
"""Capture the viewport straight to a PNG.

Going through the shell keeps a megabyte of base64 out of the conversation --
the picture is the point, the encoding of it is not.
  cap.py <out.png> [x y z pitch yaw roll]
"""
import base64, json, re, sys, urllib.request
URL='http://127.0.0.1:8000/mcp'
H={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
def rpc(m,p,sid=None):
    h=dict(H)
    if sid: h['Mcp-Session-Id']=sid
    r=urllib.request.urlopen(urllib.request.Request(URL,json.dumps(
        {'jsonrpc':'2.0','id':1,'method':m,'params':p}).encode(),h),timeout=240)
    return r.headers.get('Mcp-Session-Id'), r.read().decode()
sid,_=rpc('initialize',{'protocolVersion':'2025-06-18','capabilities':{},
                        'clientInfo':{'name':'cap','version':'1'}})
# THE UI IS OFF FOR PHOTOGRAPHS AND ON FOR PLAY.
#
# Every picture in these notes so far was of the WORLD -- a roof, a flame, a
# cobbled street -- and the HUD over the top of it would only be in the way.
# But a session played with a real mouse has to be watched through the same
# glass the player sees, HUD and pointer and menu included, or there is no way
# to tell a menu that did not open from a menu that opened off-screen.
#   CAP_UI=1 cap.py shot.png
import os
args={'bShowUI': os.environ.get('CAP_UI') == '1','annotations':[]}
if len(sys.argv)>2:
    x,y,z,p,yw,r=[float(v) for v in sys.argv[2:8]]
    args['captureTransform']={'location':{'x':x,'y':y,'z':z},
                              'rotation':{'pitch':p,'yaw':yw,'roll':r}}
# TWICE, AND KEEP THE SECOND.
#
# The first capture after the camera moves can come back as the frame that was
# already on the screen -- Slate does not necessarily redraw the level viewport
# between the transform being set and the pixels being read, and when the
# editor is behind another window it throttles and definitely does not. The
# symptom is a photograph that is byte-identical to the previous one, which
# reads as "my change did nothing" and is not.
for _ in range(2):
    _,out=rpc('tools/call',{'name':'call_tool','arguments':{
        'toolset_name':'EditorToolset.EditorAppToolset',
        'tool_name':'CaptureViewport','arguments':args}},sid)
m=re.search(r'"data\\?"\s*:\s*\\?"([A-Za-z0-9+/=]+)', out)
if not m:
    print(out[:400]); sys.exit(1)
open(sys.argv[1],'wb').write(base64.b64decode(m.group(1)))

# DOWN IN STEPS, NOT IN ONE JUMP. The viewport renders at about 4000 pixels
# across and a single `sips -Z 1400` point-samples it, which turns timber
# studs, thatch courses and the ground's grain into a one-pixel comb over the
# whole frame -- sky included. It looks exactly like a rendering artefact and
# is not one: halving twice averages instead, and the comb goes away. An hour
# went into chasing it in the post-process before the crop at full size showed
# the render was clean all along.
import subprocess
def wide(p):
    out = subprocess.run(['sips', '-g', 'pixelWidth', p], capture_output=True, text=True).stdout
    return int(out.strip().split()[-1])
target = int(sys.argv[8]) if len(sys.argv) > 8 else 1400
w = wide(sys.argv[1])
while w > target * 2:
    w //= 2
    subprocess.run(['sips', '-Z', str(w), sys.argv[1]], capture_output=True)
subprocess.run(['sips', '-Z', str(target), sys.argv[1]], capture_output=True)
print(sys.argv[1])
