"""
Call graph data model.

Contains the CallGraph class and its factory helpers (make_class_node,
make_method_node, make_call_edge).  Extracted verbatim from
call_graph_builder.py so that parsers and consumers can import from a
single place without circular dependencies.

ASCII-only (cp1252-safe for Windows).
"""

import builtins
import json
import logging
import os

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Resolution confidence levels
# ---------------------------------------------------------------------------
# Every edge produced by resolve_edges() carries one of these under the
# "confidence" key so downstream consumers can separate an edge backed by
# positive evidence from a guess.  Issue #266: a wrongly-resolved edge is a
# confident falsehood that inflates fan-in based risk signals, whereas an
# unresolved edge is a known unknown.  Only CONFIDENCE_HIGH edges may be used
# to rank danger zones and hot nodes.
CONFIDENCE_HIGH = "high"
CONFIDENCE_AMBIGUOUS = "ambiguous"
CONFIDENCE_NONE = "none"


def _derive_builtin_callee_names():
    """Derive the set of callee names a Python builtin or container may own.

    Built from the live interpreter -- ``dir(builtins)`` plus the public
    method names of str, list, dict and set -- so the set tracks the running
    Python version instead of being hand-maintained and going stale.

    A call whose callee simple name is in this set cannot be attributed to a
    project method on name alone: ``parts.append(x)`` names the list method,
    not whichever project class happens to define an ``append``.
    """
    names = set(dir(builtins))
    for container in (str, list, dict, set):
        names.update(n for n in dir(container) if not n.startswith("_"))
    return frozenset(names)


BUILTIN_CALLEE_NAMES = _derive_builtin_callee_names()

# ---------------------------------------------------------------------------
# Transitive call-path exploration limits
# ---------------------------------------------------------------------------
# compute_call_paths() previously hard-coded max_depth=15 and max_paths=200
# which silently truncated analysis of any call chain longer than 15 hops.
# Issue #207 raised the defaults and made both configurable via env vars.
# Issue #265: max_paths=500 still bound in production -- it truncated path
# traversal on every run regardless of how many files were ingested, so the
# shipping default is now unbounded and only an explicit operator setting
# reintroduces a cap.
#   CLAUDE_CG_MAX_DEPTH  (default 30) -- deeper covers most real codebases
#   CLAUDE_CG_MAX_PATHS  (default unbounded) -- set to a positive integer to cap
# Callers may also pass explicit max_depth / max_paths kwargs which override
# the env defaults for a single call.


def _env_int(name, default):
    """Parse an int env var; fall back to default on missing/invalid value."""
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return int(raw)
    except (ValueError, TypeError):
        return default


def _env_positive_int_or_none(name):
    """Read an optional positive-integer cap from the environment.

    Returns None (meaning "no cap") when the variable is unset, blank,
    unparseable, or non-positive, so a malformed value can never silently
    truncate traversal.
    """
    raw = os.environ.get(name)
    if not raw:
        return None
    try:
        value = int(raw)
    except (ValueError, TypeError):
        return None
    return value if value > 0 else None


DEFAULT_MAX_DEPTH = _env_int("CLAUDE_CG_MAX_DEPTH", 30)
DEFAULT_MAX_PATHS = _env_positive_int_or_none("CLAUDE_CG_MAX_PATHS")

# =========================================================================
# Node / Edge factory helpers
# =========================================================================


def make_class_node(fqn, name, file_path, line, bases=None):
    """Create a class node dict.

    Args:
        fqn: Fully qualified name (e.g., module.py::ClassName)
        name: Simple class name
        file_path: Relative path to file
        line: Line number of class definition
        bases: List of parent class names
    """
    return {
        "id": fqn,
        "type": "class",
        "name": name,
        "file": file_path,
        "line": line,
        "bases": bases or [],
        "methods": [],  # populated later with method FQNs
    }


def make_method_node(
    fqn,
    name,
    file_path,
    line,
    parent_class=None,
    params=None,
    return_type="",
    visibility="+",
    is_async=False,
    cyclomatic=1,
):
    """Create a method/function node dict.

    Args:
        fqn: Fully qualified name (e.g., module.py::ClassName.method)
        name: Simple method name
        file_path: Relative path to file
        line: Line number
        parent_class: FQN of parent class (None for standalone functions)
        params: List of parameter strings
        return_type: Return type annotation string
        visibility: + (public) or - (private)
        is_async: Whether it is async
        cyclomatic: Cyclomatic complexity of this method
    """
    return {
        "id": fqn,
        "type": "method" if parent_class else "function",
        "name": name,
        "file": file_path,
        "line": line,
        "parent_class": parent_class,
        "params": params or [],
        "return_type": return_type,
        "visibility": visibility,
        "is_async": is_async,
        "cyclomatic": cyclomatic,
    }


def make_call_edge(from_fqn, to_fqn, line, call_type="call"):
    """Create a call edge dict.

    Args:
        from_fqn: Caller FQN
        to_fqn: Callee FQN (or best-effort name if unresolved)
        line: Line number of the call
        call_type: 'call', 'method_call', 'inheritance', 'super_call'
    """
    return {
        "from": from_fqn,
        "to": to_fqn,
        "line": line,
        "type": call_type,
    }


# =========================================================================
# Helpers
# =========================================================================


def _safe_avg(values):
    """Calculate average, return 0.0 for empty list."""
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


# =========================================================================
# CallGraph - main data structure
# =========================================================================


class CallGraph:
    """Complete call graph for a project.

    Attributes:
        nodes: Dict of FQN -> node dict (classes, methods, functions)
        edges: List of call edge dicts
        classes: Dict of FQN -> class node
        methods: Dict of FQN -> method/function node
        files: Set of relative file paths analysed
    """

    def __init__(self):
        """Initialise empty node/class/method/edge/file collections."""
        self.nodes = {}  # fqn -> node dict
        self.classes = {}  # fqn -> class node
        self.methods = {}  # fqn -> method/function node
        self.edges = []  # list of call edge dicts
        self.files = set()  # relative file paths

        # Computed after build
        self._call_paths = None
        self._impact_map = None
        self._impact_map_high_confidence = None
        self._resolved_edges = None

    # ------------------------------------------------------------------
    # Population
    # ------------------------------------------------------------------

    def add_file_results(self, visitor):
        """Merge results from a parser visitor into this graph.

        The visitor object must expose .classes, .methods, .edges, and
        .rel_path attributes (matching the shape produced by all concrete
        parsers in the parsers/ package).
        """
        for cls in visitor.classes:
            self.classes[cls["id"]] = cls
            self.nodes[cls["id"]] = cls
        for method in visitor.methods:
            self.methods[method["id"]] = method
            self.nodes[method["id"]] = method
        self.edges.extend(visitor.edges)
        self.files.add(visitor.rel_path)

    # ------------------------------------------------------------------
    # Edge resolution
    # ------------------------------------------------------------------

    def resolve_edges(self):
        """Resolve unqualified callee names to FQNs where possible.

        After all files are processed, try to match call targets
        to known method/function definitions.
        """
        # Build lookup: simple name -> list of FQNs
        name_to_fqns = {}
        for fqn, node in self.methods.items():
            name = node["name"]
            if name not in name_to_fqns:
                name_to_fqns[name] = []
            name_to_fqns[name].append(fqn)

        # Also map class names
        class_name_to_fqn = {}
        for fqn, cls in self.classes.items():
            class_name_to_fqn[cls["name"]] = fqn

        resolved = []
        for edge in self.edges:
            to_name = edge["to"]
            resolved_to, confidence = self._resolve_target(to_name, edge["from"], name_to_fqns, class_name_to_fqn)
            new_edge = dict(edge)
            new_edge["to"] = resolved_to
            new_edge["resolved"] = resolved_to != to_name
            new_edge["confidence"] = confidence
            resolved.append(new_edge)

        self._resolved_edges = resolved
        self._impact_map = None
        self._impact_map_high_confidence = None
        return resolved

    def _resolve_target(self, target, caller_fqn, name_to_fqns, class_name_to_fqn):
        """Try to resolve a call target to a known FQN.

        Returns a ``(target, confidence)`` tuple where confidence is one of
        CONFIDENCE_HIGH (positive evidence backs the binding),
        CONFIDENCE_AMBIGUOUS (a project method carries the name but nothing
        distinguishes it from a builtin or from its sibling candidates) or
        CONFIDENCE_NONE (no project method carries the name at all).

        Resolution strategy, in precedence order:
        1. A target that already looks like a FQN is kept, and rated high only
           when that FQN names a method this graph actually knows.
        2. For a dotted ``receiver.method`` target, a receiver naming a known
           class that owns ``method`` is direct evidence and resolves high.
        3. A callee whose simple name belongs to a builtin or to str/list/dict/
           set is left unresolved: the name alone cannot distinguish
           ``parts.append(x)`` from a project ``append``.
        4. Otherwise a same-file definition, then a sole project definition,
           resolve high.
        5. A bare name matching two or more project definitions with no
           same-file candidate is left unresolved as ambiguous rather than
           bound to an arbitrary first match.
        6. A class name resolves to its constructor.

        Issue #266: steps 2, 3 and 5 are the fix. Step 5 previously returned
        ``candidates[0]``, and steps 3/4 previously bound every builtin and
        stdlib call to whichever same-named project method existed, which
        inflated fan-in and drove the danger-zone and hot-node rankings that
        Step 1 planning consumes.
        """
        # Already resolved
        if "::" in target:
            return (target, CONFIDENCE_HIGH if target in self.methods else CONFIDENCE_NONE)

        # Get caller file for same-file preference
        caller_file = caller_fqn.split("::")[0] if "::" in caller_fqn else ""

        # Handle dotted targets like ClassName.method
        if "." in target:
            receiver, method_name = target.rsplit(".", 1)
            if "::" in receiver:
                return (target, CONFIDENCE_NONE)

            owner_fqn = class_name_to_fqn.get(receiver.rsplit(".", 1)[-1])
            if owner_fqn:
                owned_fqn = "%s.%s" % (owner_fqn, method_name)
                if owned_fqn in self.methods:
                    return (owned_fqn, CONFIDENCE_HIGH)

            if method_name in BUILTIN_CALLEE_NAMES:
                return (target, CONFIDENCE_AMBIGUOUS)

            if method_name in name_to_fqns:
                candidates = name_to_fqns[method_name]
                same_file = [c for c in candidates if c.startswith(caller_file + "::")]
                if same_file:
                    return (same_file[0], CONFIDENCE_HIGH)
                if len(candidates) == 1:
                    return (candidates[0], CONFIDENCE_HIGH)
                return (target, CONFIDENCE_AMBIGUOUS)
            return (target, CONFIDENCE_NONE)

        # Simple name lookup
        if target in name_to_fqns:
            if target in BUILTIN_CALLEE_NAMES:
                return (target, CONFIDENCE_AMBIGUOUS)
            candidates = name_to_fqns[target]
            same_file = [c for c in candidates if c.startswith(caller_file + "::")]
            if same_file:
                return (same_file[0], CONFIDENCE_HIGH)
            if len(candidates) == 1:
                return (candidates[0], CONFIDENCE_HIGH)
            return (target, CONFIDENCE_AMBIGUOUS)

        # Check if it is a class name (constructor call)
        if target in class_name_to_fqn:
            class_fqn = class_name_to_fqn[target]
            init_fqn = "%s.__init__" % class_fqn
            if init_fqn in self.methods:
                return (init_fqn, CONFIDENCE_HIGH)
            return (class_fqn, CONFIDENCE_HIGH)

        # Unresolved - external or builtin
        return (target, CONFIDENCE_NONE)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_edges(self):
        """Get resolved edges (or raw if not yet resolved)."""
        if self._resolved_edges is not None:
            return self._resolved_edges
        return self.edges

    def get_high_confidence_edges(self):
        """Get only the edges whose callee binding is backed by positive evidence.

        Raw edges (resolve_edges not yet run) carry no confidence marker and
        are therefore all excluded -- an unresolved graph has no
        high-confidence subset to report.
        """
        return [e for e in self.get_edges() if e.get("confidence") == CONFIDENCE_HIGH]

    def get_resolution_confidence(self):
        """Summarise how many call edges carry each confidence level.

        Returns a dict with total_call_edges, high_confidence, ambiguous and
        no_candidate counts so callers can report the high-confidence figure
        alongside the raw one rather than in place of it.
        """
        counts = {
            "total_call_edges": 0,
            "high_confidence": 0,
            "ambiguous": 0,
            "no_candidate": 0,
        }
        for edge in self.get_edges():
            if edge.get("type") == "inheritance":
                continue
            counts["total_call_edges"] += 1
            confidence = edge.get("confidence", CONFIDENCE_NONE)
            if confidence == CONFIDENCE_HIGH:
                counts["high_confidence"] += 1
            elif confidence == CONFIDENCE_AMBIGUOUS:
                counts["ambiguous"] += 1
            else:
                counts["no_candidate"] += 1
        return counts

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def compute_call_paths(self, max_depth=None, max_paths=None):
        """Compute all call paths from entry points.

        Entry points are methods/functions not called by any other method.

        Args:
            max_depth: Maximum path depth to explore. Defaults to
                DEFAULT_MAX_DEPTH (30, overridable via CLAUDE_CG_MAX_DEPTH
                env var). Paths longer than this are truncated.
            max_paths: Maximum number of paths to emit, or None for no cap.
                Defaults to DEFAULT_MAX_PATHS (unbounded, overridable via
                CLAUDE_CG_MAX_PATHS env var). When a cap is in force,
                emission stops once that many paths have been collected and
                a warning is logged.

        Returns list of path dicts:
        [{"id": "path_N", "path": [fqn1, fqn2, ...], "depth": N,
          "total_complexity": N}]

        Previously hard-coded at max_depth=15, max_paths=200 -- issue #207
        raised the defaults and made them configurable, and issue #265
        removed the remaining max_paths cap that still truncated every
        production run.
        """
        if self._call_paths is not None:
            return self._call_paths

        # Resolve limits (explicit args override env defaults)
        if max_depth is None:
            max_depth = DEFAULT_MAX_DEPTH
        if max_paths is None:
            max_paths = DEFAULT_MAX_PATHS

        edges = self.get_edges()

        # Build adjacency: caller -> [callees]
        adjacency = {}
        for edge in edges:
            if edge["type"] == "inheritance":
                continue
            src = edge["from"]
            dst = edge["to"]
            if src not in adjacency:
                adjacency[src] = []
            adjacency[src].append(dst)

        # Find all callees
        all_callees = set()
        for targets in adjacency.values():
            all_callees.update(targets)

        # Entry points: defined methods not in callee set
        entry_points = []
        for fqn in self.methods:
            name = self.methods[fqn]["name"]
            if name.startswith("_") and not name.startswith("__"):
                continue  # skip private
            if fqn not in all_callees:
                entry_points.append(fqn)

        # DFS from each entry point
        paths = []
        path_id = 0
        for entry in entry_points:
            if max_paths is not None and path_id >= max_paths:
                break
            stack = [(entry, [entry], 0)]
            while stack and (max_paths is None or path_id < max_paths):
                current, path, depth = stack.pop()
                if depth >= max_depth:
                    continue

                callees = adjacency.get(current, [])
                if not callees or depth >= max_depth - 1:
                    if len(path) >= 2:
                        total_cx = sum(
                            self.methods.get(fqn, {}).get("cyclomatic", 1) for fqn in path if fqn in self.methods
                        )
                        paths.append(
                            {
                                "id": "path_%d" % path_id,
                                "path": list(path),
                                "depth": len(path),
                                "total_complexity": total_cx,
                            }
                        )
                        path_id += 1
                else:
                    for callee in callees:
                        if callee in path:
                            continue  # avoid cycles
                        if callee not in self.methods:
                            continue  # skip unresolved
                        stack.append((callee, path + [callee], depth + 1))

        # Emit a warning when exploration hit a hard cap so operators know
        # their results may be truncated. Keeps silent truncation visible
        # without changing the return shape.
        if max_paths is not None and path_id >= max_paths:
            logger.warning(
                "compute_call_paths: hit max_paths=%d limit; results truncated. "
                "Increase via CLAUDE_CG_MAX_PATHS env var or pass max_paths kwarg.",
                max_paths,
            )

        self._call_paths = paths
        return paths

    def compute_impact_map(self, high_confidence_only=False):
        """Build reverse dependency map: what is affected when X changes.

        Args:
            high_confidence_only: When True, only edges whose callee binding
                is backed by positive evidence contribute callers. Fan-in
                rankings (danger zones, hot nodes) must use this variant so a
                builtin-name collision cannot inflate a method's apparent
                blast radius.

        Returns dict: {fqn: set of FQNs that call this method (transitively)}
        """
        if high_confidence_only:
            if self._impact_map_high_confidence is not None:
                return self._impact_map_high_confidence
        elif self._impact_map is not None:
            return self._impact_map

        edges = self.get_high_confidence_edges() if high_confidence_only else self.get_edges()

        # Reverse adjacency: callee -> [callers]
        reverse = {}
        for edge in edges:
            if edge["type"] == "inheritance":
                continue
            dst = edge["to"]
            src = edge["from"]
            if dst not in reverse:
                reverse[dst] = set()
            reverse[dst].add(src)

        # Transitive closure via BFS from each node
        impact = {}
        for fqn in self.methods:
            affected = set()
            queue = [fqn]
            visited = set()
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                callers = reverse.get(current, set())
                for caller in callers:
                    if caller not in visited:
                        affected.add(caller)
                        queue.append(caller)
            impact[fqn] = affected

        if high_confidence_only:
            self._impact_map_high_confidence = impact
        else:
            self._impact_map = impact
        return impact

    def get_max_call_depth(self):
        """Get the maximum call chain depth."""
        paths = self.compute_call_paths()
        if not paths:
            return 0
        return max(p["depth"] for p in paths)

    def get_stats(self):
        """Get summary statistics for the call graph."""
        edges = self.get_edges()
        call_edges = [e for e in edges if e["type"] != "inheritance"]
        inheritance_edges = [e for e in edges if e["type"] == "inheritance"]
        resolved = [e for e in call_edges if e.get("resolved", False)]
        confidence = self.get_resolution_confidence()

        return {
            "total_classes": len(self.classes),
            "total_methods": len(self.methods),
            "total_functions": sum(1 for m in self.methods.values() if m["type"] == "function"),
            "total_call_edges": len(call_edges),
            "total_inheritance_edges": len(inheritance_edges),
            "resolved_edges": len(resolved),
            "unresolved_edges": len(call_edges) - len(resolved),
            "high_confidence_edges": confidence["high_confidence"],
            "ambiguous_edges": confidence["ambiguous"],
            "files_analyzed": len(self.files),
            "max_call_depth": self.get_max_call_depth(),
            "avg_cyclomatic": _safe_avg([m.get("cyclomatic", 1) for m in self.methods.values()]),
            "max_cyclomatic": max(
                (m.get("cyclomatic", 1) for m in self.methods.values()),
                default=0,
            ),
        }

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self):
        """Serialise the full call graph to a dict.

        This is the proper call stack format:
        - nodes: classes and methods with FQN, params, types
        - edges: method-to-method calls with line numbers
        - call_paths: full call chains with depth and complexity
        """
        edges = self.get_edges()
        paths = self.compute_call_paths()
        stats = self.get_stats()

        return {
            "version": "2.0.0",
            "stats": stats,
            "nodes": {
                "classes": list(self.classes.values()),
                "methods": list(self.methods.values()),
            },
            "edges": edges,
            "call_paths": paths[:100],
        }

    def to_json(self, indent=2):
        """Serialise to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
