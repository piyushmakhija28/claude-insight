"""A minimal, real stdio MCP server used to MEASURE capability reachability.

The round-trip test does not assert that register-mcp wrote what register-mcp
wrote - that would be a tautology dressed as evidence. It instead reads the
entry back out of the settings file, spawns exactly what that entry says, and
completes a real JSON-RPC 2.0 lifecycle handshake against the spawned process.
A capability is called reachable only when a tool is actually listed by the
server the settings file points at.

This server also enforces the lifecycle gate, so the same fixture supports the
negative case: any tools/list arriving before notifications/initialized is
answered with a protocol-level error rather than a result.
"""

import json
import sys

PROTOCOL_VERSION = "2025-06-18"
TOOL_NAME = "reachability_probe"

STATE_UNINITIALIZED = "uninitialized"
STATE_INITIALIZING = "initializing"
STATE_READY = "ready"


def _tool_descriptor():
    """Return the single tool this server advertises.

    The output schema carries one boolean and nothing else. There is no PII
    here to minimise, and no field is present that the probe's purpose does not
    require.

    Returns:
        dict: A tools/list descriptor entry.
    """
    return {
        "name": TOOL_NAME,
        "description": (
            "Confirms this server was reachable from the registered settings "
            "entry. Use only to verify registration; it has no other effect."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "reachable": {
                    "type": "boolean",
                    "description": "Always true when this server answered.",
                }
            },
            "required": ["reachable"],
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    }


def _error(request_id, code, message):
    """Build a protocol-level JSON-RPC error response.

    Args:
        request_id: The id of the request being answered.
        code: JSON-RPC error code.
        message: Human-readable error message.

    Returns:
        dict: A JSON-RPC error response object.
    """
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def _result(request_id, payload):
    """Build a JSON-RPC success response.

    Args:
        request_id: The id of the request being answered.
        payload: The result object.

    Returns:
        dict: A JSON-RPC result response object.
    """
    return {"jsonrpc": "2.0", "id": request_id, "result": payload}


def handle(message, state):
    """Route one inbound JSON-RPC message.

    Any non-lifecycle method arriving before the initialized notification is
    routed to a protocol error, never answered helpfully, because the handshake
    is a gate rather than a convention.

    Args:
        message: The parsed inbound message.
        state: The current lifecycle state string.

    Returns:
        tuple: (response dict or None, next state string).
    """
    method = message.get("method")
    request_id = message.get("id")

    if method == "initialize":
        if state != STATE_UNINITIALIZED:
            return (
                _error(request_id, -32600, "initialize received twice"),
                STATE_UNINITIALIZED,
            )
        return (
            _result(
                request_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "reachability-probe", "version": "1.0.0"},
                },
            ),
            STATE_INITIALIZING,
        )

    if method == "notifications/initialized":
        if state != STATE_INITIALIZING:
            return None, state
        return None, STATE_READY

    if state != STATE_READY:
        return (
            _error(
                request_id,
                -32002,
                "server not initialized: {0} rejected".format(method),
            ),
            state,
        )

    if method == "tools/list":
        return _result(request_id, {"tools": [_tool_descriptor()]}), state

    if method == "tools/call":
        name = (message.get("params") or {}).get("name")
        if name != TOOL_NAME:
            return _error(request_id, -32602, "unknown tool: {0}".format(name)), state
        return (
            _result(
                request_id,
                {
                    "content": [{"type": "text", "text": "reachable"}],
                    "structuredContent": {"reachable": True},
                    "isError": False,
                },
            ),
            state,
        )

    return _error(request_id, -32601, "method not found: {0}".format(method)), state


def main():
    """Read newline-delimited JSON-RPC from stdin and answer on stdout.

    Returns:
        int: Always 0; the process exits when stdin closes.
    """
    state = STATE_UNINITIALIZED
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps(_error(None, -32700, "parse error")) + "\n")
            sys.stdout.flush()
            continue
        response, state = handle(message, state)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
