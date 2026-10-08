#!/usr/bin/env python3
"""Call an unreal-mcp tool over HTTP.

Exists so that large payloads -- a few kilobytes of HLSL, say -- can be sent
from a FILE instead of being escaped by hand into a tool call twice over.
  mcp.py <toolset> <tool> <args.json>
"""
import json, sys, urllib.request

URL = 'http://127.0.0.1:8000/mcp'
HDR = {'Content-Type': 'application/json',
       'Accept': 'application/json, text/event-stream'}

def rpc(method, params, sid=None):
    h = dict(HDR)
    if sid:
        h['Mcp-Session-Id'] = sid
    body = json.dumps({'jsonrpc': '2.0', 'id': 1,
                       'method': method, 'params': params}).encode()
    req = urllib.request.Request(URL, body, h)
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.headers.get('Mcp-Session-Id'), r.read().decode()

sid, _ = rpc('initialize', {'protocolVersion': '2025-06-18', 'capabilities': {},
                            'clientInfo': {'name': 'mcp.py', 'version': '1'}})
args = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
_, out = rpc('tools/call', {'name': 'call_tool', 'arguments': {
    'toolset_name': sys.argv[1], 'tool_name': sys.argv[2], 'arguments': args}}, sid)
print(out)
