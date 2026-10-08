#!/usr/bin/env python3
"""One MCP session, reused, for scripts that make hundreds of calls.

`mcp.py` is a COMMAND: it opens a session, makes one call and exits, which is
exactly right when a shell wants to set one property. Every dress_* script was
built on top of it and pays for that shape several hundred times over -- a
fresh interpreter, a fresh TCP connection and a fresh MCP `initialize` per
material parameter. Dressing the wardrobe took nine minutes of which almost
none was the editor doing anything.

This is the same wire protocol with the session opened once. Import it and
call `call(toolset, tool, args)`; the return is the tool's text payload, which
is what every caller here already parses.
"""
import json
import urllib.request

URL = 'http://127.0.0.1:8000/mcp'
HDR = {'Content-Type': 'application/json',
       'Accept': 'application/json, text/event-stream'}

_sid = None


def _post(method, params, sid=None):
    h = dict(HDR)
    if sid:
        h['Mcp-Session-Id'] = sid
    body = json.dumps({'jsonrpc': '2.0', 'id': 1,
                       'method': method, 'params': params}).encode()
    req = urllib.request.Request(URL, body, h)
    with urllib.request.urlopen(req, timeout=600) as r:
        return r.headers.get('Mcp-Session-Id'), r.read().decode()


def session():
    """Open the session once and keep it. Re-opened if the editor restarts."""
    global _sid
    if _sid is None:
        _sid, _ = _post('initialize', {'protocolVersion': '2025-06-18',
                                       'capabilities': {},
                                       'clientInfo': {'name': 'rpc', 'version': '1'}})
    return _sid


def raw(toolset, tool, args):
    """The whole JSON-RPC envelope, as `mcp.py` prints it."""
    return _post('tools/call', {'name': 'call_tool', 'arguments': {
        'toolset_name': toolset, 'tool_name': tool,
        'arguments': args}}, session())[1]


def call(toolset, tool, args):
    """The tool's own text payload -- the string every caller here parses.

    An editor that has been restarted answers a stale session id with an
    error rather than a result, so one retry with a fresh session is worth
    more than a clear error message in the middle of a nine-minute rebuild.
    """
    global _sid
    out = raw(toolset, tool, args)
    try:
        return json.loads(out)['result']['content'][0]['text']
    except Exception:
        _sid = None
        out = raw(toolset, tool, args)
        try:
            return json.loads(out)['result']['content'][0]['text']
        except Exception:
            return out[:400]
