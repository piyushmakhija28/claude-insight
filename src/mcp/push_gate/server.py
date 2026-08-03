"""stdio MCP server exposing the version-push gate as a named tool.

PRD FR-23 / SRS FR-35: the two rules that live in
``hooks/pre_tool_enforcer/policies/push_gate.py`` must be reachable by name from
an MCP tool BEFORE that hook package is deleted (PRD FR-4). This server is that
reachability. It is registered at user scope by the plugin's ``register-mcp``
command; nothing bundles it and nothing spawns it until a session resolves the
entry, which is what ADR-019 requires.

WHY THIS SERVER TAKES NO THIRD-PARTY DEPENDENCY
-----------------------------------------------
The sibling servers in this workspace are built on ``mcp``/``FastMCP``. This one
is not, and the difference is deliberate. A safety gate whose start-up depends
on a pip package disappears silently the moment that package is missing from the
interpreter the settings entry names -- the server fails to spawn, no tool is
listed, and the only symptom is a capability that quietly is not there. Every
rule here is expressible in the standard library, so the dependency buys nothing
and costs a failure mode. The shape follows this repository's own dependency-free
stdio server, ``tests/fixtures/reachability_mcp_server.py``.

The consequence is that the JSON-RPC framing and the lifecycle gate are written
here rather than inherited, which is also why the gate can be tested directly
rather than assumed.

LIFECYCLE GATE (M1)
-------------------
``handle`` is a three-state machine: UNINITIALIZED -> INITIALIZING -> READY.
Any method other than ``initialize`` and ``notifications/initialized`` arriving
before READY is answered with a protocol-level error and is never executed. The
enforcement mechanism is the explicit state check in ``handle``, not a
convention, and a test drives a ``tools/call`` through the real process without
the initialized notification to prove the rejection happens.

isError VERSUS A PROTOCOL ERROR
-------------------------------
A blocked push is NOT an error. It is this tool's successful answer to the
question it was asked, so it comes back as an ordinary result with
``isError: false`` and the block described in the payload. Marking it as an
error would push the one outcome the caller most needs to reason about onto the
path many clients do not feed back into the conversation. Protocol errors are
reserved for malformed calls: an unknown method, an unknown tool name, or a
missing or wrongly-typed ``command`` argument.

Windows-safe: ASCII only, no Unicode characters.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from push_gate_policy import (  # noqa: E402
    DETERMINATION_ALLOWED,
    DETERMINATION_BLOCKED,
    DETERMINATION_UNDETERMINED,
    evaluate_push,
)

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "push-gate"
SERVER_VERSION = "1.0.0"
TOOL_NAME = "check_push_allowed"

STATE_UNINITIALIZED = "uninitialized"
STATE_INITIALIZING = "initializing"
STATE_READY = "ready"

ERROR_PARSE = -32700
ERROR_INVALID_REQUEST = -32600
ERROR_METHOD_NOT_FOUND = -32601
ERROR_INVALID_PARAMS = -32602
ERROR_NOT_INITIALIZED = -32002

TOOL_DESCRIPTION = (
    "Decides whether a shell command's 'git push' satisfies this machine's two "
    "local version-push rules: the branch being pushed carries a VERSION change "
    "(measured against its merge base), and no tracked file has uncommitted "
    "changes. Use this before running any command that pushes, and pass the "
    "command verbatim so the push is found by parsing rather than by substring. "
    "It does NOT check branch protection, review status or CI, and it is a no-op "
    "in a repository that tracks no VERSION file."
)


def tool_descriptor():
    """Return the single tool this server advertises.

    The output schema carries only what a caller needs to act: whether the push
    may proceed, which rules refused and why, and which questions could not be
    answered. No field describes a person, so there is no PII to minimise, and
    the repository and file paths that are present are the whole substance of an
    actionable refusal.

    The annotations place this tool at the top of the four-hint safety lattice:
    it reads git state and writes nothing, it is reversible because it changes
    nothing, repeated identical calls have identical effect, and it reaches only
    the local filesystem and a local git process -- no network call is made, and
    ``origin/main`` is consulted as an already-fetched local ref.

    Returns:
        dict: A ``tools/list`` descriptor entry.
    """
    return {
        "name": TOOL_NAME,
        "description": TOOL_DESCRIPTION,
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command about to run, verbatim and unmodified.",
                },
                "tool_name": {
                    "type": "string",
                    "description": "Tool the command belongs to. Only 'Bash' is judged; anything else is allowed.",
                },
                "cwd": {
                    "type": "string",
                    "description": (
                        "Directory a bare 'git push' in this command would run in. Supply it: this "
                        "server is a separate process and its own working directory is not yours."
                    ),
                },
            },
            "required": ["command"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "push_detected": {
                    "type": "boolean",
                    "description": "True when the command contains a push that publishes commits.",
                },
                "allowed": {
                    "type": "boolean",
                    "description": "True when no rule refused the push. Fail-open: also true when a rule could not be answered.",
                },
                "determination": {
                    "type": "string",
                    "enum": [DETERMINATION_ALLOWED, DETERMINATION_BLOCKED, DETERMINATION_UNDETERMINED],
                    "description": "ALLOWED, BLOCKED, or UNDETERMINED when a rule failed open rather than passing.",
                },
                "violations": {
                    "type": "array",
                    "description": "One entry per refusing rule, with its policy code and the actionable message.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "rule": {"type": "string", "description": "Rule identifier that refused."},
                            "code": {"type": "string", "description": "Policy code, L3.10 or L3.11."},
                            "message": {"type": "string", "description": "The refusal text, including how to comply."},
                        },
                        "required": ["rule", "code", "message"],
                    },
                },
                "undetermined": {
                    "type": "array",
                    "description": "Questions the gate could not answer, so a fail-open is visible rather than silent.",
                    "items": {"type": "string"},
                },
                "repo": {
                    "type": ["string", "null"],
                    "description": "Repository root the rules were asked of, or null when it could not be resolved.",
                },
                "target": {
                    "type": ["string", "null"],
                    "description": "Directory the push runs in, empty string meaning the caller's own directory.",
                },
                "cwd_source": {
                    "type": "string",
                    "description": "'caller' when cwd was supplied, 'server-process' when it was not and was guessed.",
                },
            },
            "required": ["push_detected", "allowed", "determination", "violations", "undetermined"],
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
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _result(request_id, payload):
    """Build a JSON-RPC success response.

    Args:
        request_id: The id of the request being answered.
        payload: The result object.

    Returns:
        dict: A JSON-RPC result response object.
    """
    return {"jsonrpc": "2.0", "id": request_id, "result": payload}


def _summary(verdict):
    """Render the one-line human summary that accompanies the structured result.

    Args:
        verdict: Payload returned by ``evaluate_push``.

    Returns:
        str: A single line naming the outcome and, when refused, the rules.
    """
    if not verdict["push_detected"]:
        return "No git push that publishes commits was found in this command; nothing to gate."
    if verdict["violations"]:
        rules = ", ".join(item["rule"] for item in verdict["violations"])
        return "Push BLOCKED by {0}. {1}".format(rules, verdict["violations"][0]["message"])
    if verdict["undetermined"]:
        return "Push allowed, but the gate could not answer every question: {0}".format(
            "; ".join(verdict["undetermined"])
        )
    return "Push allowed: the branch carries a VERSION change and no tracked file is modified."


def _call_tool(request_id, params):
    """Execute a ``tools/call`` request.

    Argument validation is the one place a protocol error is correct here: a
    missing or wrongly-typed ``command`` violates the declared ``inputSchema``,
    which is a malformed call rather than a business outcome. Every outcome the
    rules themselves can produce -- allowed, blocked, or undetermined -- is a
    successful result.

    Args:
        request_id: The id of the request being answered.
        params: The request's params object.

    Returns:
        dict: A JSON-RPC response object.
    """
    name = (params or {}).get("name")
    if name != TOOL_NAME:
        return _error(request_id, ERROR_INVALID_PARAMS, "unknown tool: {0}".format(name))

    arguments = (params or {}).get("arguments") or {}
    command = arguments.get("command")
    if not isinstance(command, str):
        return _error(
            request_id,
            ERROR_INVALID_PARAMS,
            "argument 'command' is required and must be a string",
        )

    tool_name = arguments.get("tool_name") or "Bash"
    caller_cwd = arguments.get("cwd") or None
    verdict = evaluate_push(command, tool_name=tool_name, caller_cwd=caller_cwd)

    return _result(
        request_id,
        {
            "content": [{"type": "text", "text": _summary(verdict)}],
            "structuredContent": verdict,
            "isError": False,
        },
    )


def handle(message, state):
    """Route one inbound JSON-RPC message.

    Any non-lifecycle method arriving before the initialized notification is
    routed to a protocol error and is never executed, because the handshake is a
    gate rather than a convention.

    Args:
        message: The parsed inbound message.
        state: The current lifecycle state string.

    Returns:
        tuple: ``(response dict or None, next state string)``.
    """
    method = message.get("method")
    request_id = message.get("id")

    if method == "initialize":
        if state != STATE_UNINITIALIZED:
            return _error(request_id, ERROR_INVALID_REQUEST, "initialize received twice"), state
        return (
            _result(
                request_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
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
            _error(request_id, ERROR_NOT_INITIALIZED, "server not initialized: {0} rejected".format(method)),
            state,
        )

    if method == "tools/list":
        return _result(request_id, {"tools": [tool_descriptor()]}), state

    if method == "tools/call":
        return _call_tool(request_id, message.get("params")), state

    return _error(request_id, ERROR_METHOD_NOT_FOUND, "method not found: {0}".format(method)), state


def main():
    """Read newline-delimited JSON-RPC from stdin and answer on stdout.

    Both streams are reconfigured to UTF-8 first. On Windows the default is the
    ANSI codepage, so a command argument carrying a non-ASCII path would be
    decoded into different characters than the caller sent -- and the gate would
    then resolve a different directory than the one being pushed from. The wire
    format is defined as UTF-8, so this is conformance rather than preference.

    Returns:
        int: Always 0; the process exits when stdin closes.
    """
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.reconfigure(encoding="utf-8")
    state = STATE_UNINITIALIZED
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps(_error(None, ERROR_PARSE, "parse error")) + "\n")
            sys.stdout.flush()
            continue
        response, state = handle(message, state)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
