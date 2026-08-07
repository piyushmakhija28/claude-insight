"""Component definitions and attribution roles for the NFR-1 measurement.

NFR-1 is only meaningful per component. A single aggregate process delta cannot pass,
because the retained Stop hook is engine code that fires every response turn, so the
engine can never show a zero delta against itself. This module supplies the vocabulary
that makes attribution possible: which components exist, what evidence identifies each
one, and which role each plays in the verdict.

The role split is the load-bearing part.

    PLUGIN_COUNTED      The verdict is computed over these. Any process attributed here
                        fails NFR-1.
    PERMITTED_EXCLUSION Excluded from the verdict. HLD section 9 permits EXACTLY ONE
                        such component, justified by ADR-010: the retained user-level
                        Stop and Notification hooks, which the plugin never owned. The
                        registry enforces the cardinality rather than trusting callers,
                        because a second carve-out would leave nothing able to make
                        NFR-1 fail, and a metric that cannot fail measures nothing.
    OBSERVED            Reported for completeness, outside the verdict. Engine
                        processes, user-scope MCP servers, and the harness's own
                        scaffolding live here.

Unattributed processes are deliberately not a role. They are reported as their own
bucket by the attribution module and drive an INDETERMINATE verdict, because a process
the harness cannot identify cannot be shown to not belong to the plugin.

Two OBSERVED entries (statusline_hook, claude_code_host) were added to cover non-plugin
process sources a real measurement window on this machine showed. Deliberately NOT
covered, because no specific marker for them could be measured rather than guessed:

    node.exe    A prior brief for this change assumed node.exe was the Claude Code host
                process. Direct measurement on this machine (tests/nfr1/process_probe.py
                snapshot, cross-checked by parent-pid chain) showed the opposite: the
                Claude Code CLI here runs as claude.exe, and every node.exe present
                belonged to unrelated npm/vite dev servers with no Claude Code ancestor
                at all. Marking node.exe as the host would have been wrong on this
                machine, not merely unspecific, so it carries no marker in either
                direction and stays unattributed.
    chrome.exe  Ordinary browser activity unconnected to the plugin, the engine, or
                Claude Code. There is no component it should be charged to; it is
                reported as unattributed noise, which is the correct and complete
                treatment for it.
"""

import os
import sys

ROLE_PLUGIN_COUNTED = "PLUGIN_COUNTED"
ROLE_PERMITTED_EXCLUSION = "PERMITTED_EXCLUSION"
ROLE_OBSERVED = "OBSERVED"

VALID_ROLES = frozenset({ROLE_PLUGIN_COUNTED, ROLE_PERMITTED_EXCLUSION, ROLE_OBSERVED})

MAX_PERMITTED_EXCLUSIONS = 1

KEY_PLUGIN = "plugin"
KEY_RETAINED_USER_HOOKS = "retained_user_hooks"
KEY_ENGINE = "engine_non_plugin"
KEY_MCP_USER_SCOPE = "mcp_user_scope"
KEY_HARNESS_SELF = "harness_self"
KEY_STATUSLINE_HOOK = "statusline_hook"
KEY_CLAUDE_CODE_HOST = "claude_code_host"


class ExclusionPolicyError(ValueError):
    """Raised when a registry would carry more than the one permitted exclusion."""


class ComponentSpec(object):
    """Identifies one component and states its role in the NFR-1 verdict.

    Attributes:
        key: Stable identifier used in reports.
        role: One of VALID_ROLES.
        markers: Lowercase, forward-slash substrings matched against a process's name,
            executable path and command line. Any hit attributes the process to this
            component. Markers are normalised on both case and path separator at
            construction, and matches() normalises the process text the same way, so a
            marker written with Windows backslashes still matches. Normalising only one
            side is how a marker becomes silently dead -- it never matches, the
            component collects nothing, and nothing reports that it stopped working.
        justification: Why this component carries its role. Required for the permitted
            exclusion so the carve-out can never be widened silently.
        description: Human-readable summary for the report.
    """

    __slots__ = ("key", "role", "markers", "justification", "description")

    def __init__(self, key, role, markers, justification="", description=""):
        if role not in VALID_ROLES:
            raise ValueError("unknown role %r for component %r" % (role, key))
        if role == ROLE_PERMITTED_EXCLUSION and not justification:
            raise ValueError("component %r claims the permitted exclusion without a justification" % key)
        self.key = key
        self.role = role
        self.markers = tuple(m.lower().replace("\\", "/") for m in markers if m)
        self.justification = justification
        self.description = description

    def matches(self, record):
        """Return the marker that identifies this record, or None.

        Comparison text is backslash-normalised to forward slashes before the
        substring check, matching the normalisation build_default_registry already
        applies to plugin_root-derived markers. Without this, a marker built from a
        path on one separator convention could never match a process reported on the
        other: Windows commonly reports command lines and executable paths with
        backslashes, and a marker normalised to forward slashes is not a substring of
        text that still has backslashes, or vice versa.

        Args:
            record: A ProcessRecord to test.

        Returns:
            The matching marker string, or None when no marker applies.
        """
        if record.cmdline is None and record.exe is None and not record.name:
            return None
        text = record.search_text().replace("\\", "/")
        for marker in self.markers:
            if marker in text:
                return marker
        return None

    def to_dict(self):
        """Return a JSON-serialisable view of this specification."""
        return {
            "key": self.key,
            "role": self.role,
            "markers": list(self.markers),
            "justification": self.justification,
            "description": self.description,
        }


class ComponentRegistry(object):
    """An ordered set of ComponentSpec objects with the exclusion cardinality enforced.

    Order matters. Registration order is match order, so the plugin is registered first
    and the broad engine component last. Without that ordering a plugin process living
    inside the repository tree would be absorbed by the engine's marker and never
    counted, which would turn the verdict into an unconditional pass.
    """

    def __init__(self, specs=None):
        self._specs = []
        for spec in specs or []:
            self.register(spec)

    def register(self, spec):
        """Add a component, refusing a duplicate key or a second exclusion.

        Args:
            spec: The ComponentSpec to add.

        Returns:
            The registry, for chaining.

        Raises:
            ValueError: If the key is already registered.
            ExclusionPolicyError: If adding spec would exceed the single exclusion
                that HLD section 9 permits.
        """
        if any(existing.key == spec.key for existing in self._specs):
            raise ValueError("component %r is already registered" % spec.key)
        if spec.role == ROLE_PERMITTED_EXCLUSION:
            current = sum(1 for s in self._specs if s.role == ROLE_PERMITTED_EXCLUSION)
            if current + 1 > MAX_PERMITTED_EXCLUSIONS:
                raise ExclusionPolicyError(
                    "HLD section 9 permits exactly %d exclusion; %r would be number %d. "
                    "A second carve-out would leave nothing able to make NFR-1 fail."
                    % (MAX_PERMITTED_EXCLUSIONS, spec.key, current + 1)
                )
        self._specs.append(spec)
        return self

    def __iter__(self):
        return iter(self._specs)

    def __len__(self):
        return len(self._specs)

    def get(self, key):
        """Return the component with the given key, or None."""
        for spec in self._specs:
            if spec.key == key:
                return spec
        return None

    def keys_with_role(self, role):
        """Return the keys of every component holding the given role."""
        return [spec.key for spec in self._specs if spec.role == role]

    def to_dict(self):
        """Return a JSON-serialisable view of the whole registry."""
        return {
            "components": [spec.to_dict() for spec in self._specs],
            "permitted_exclusions_used": len(self.keys_with_role(ROLE_PERMITTED_EXCLUSION)),
            "permitted_exclusions_max": MAX_PERMITTED_EXCLUSIONS,
        }


def qualified_tail(normalised_root):
    """Return the last two path components of a plugin root, or None.

    The plugin root's absolute path is already a marker, but it only matches a
    process that names the plugin at exactly this location. A shorter, relocatable
    marker is wanted too -- and the obvious choice, the bare basename, is a trap.
    This plugin's directory is literally named ``plugin``, so the basename marker
    was the single word ``plugin``, which matches any command line mentioning it:
    ``chrome.exe --disable-plugins`` would have been charged to the plugin.

    That direction produces false FAILs rather than false passes, so it never
    corrupted a measurement -- nothing matched it in the first real run -- but a
    metric that can fail for the wrong reason is no better than one that cannot
    fail at all.

    Two components are enough to be distinctive while staying relocatable. A root
    with only one component yields nothing, because there is no way to qualify it.

    Args:
        normalised_root: Plugin root, forward-slashed, without a trailing slash.

    Returns:
        str or None: Lowercase ``parent/leaf``, or None when it cannot be qualified.
    """
    parts = [p for p in normalised_root.split("/") if p]
    if len(parts) < 2:
        return None
    return "/".join(parts[-2:]).lower()


def build_default_registry(plugin_root=None, extra_plugin_markers=None):
    """Build the registry used by a real NFR-1 measurement.

    Args:
        plugin_root: Filesystem path of the installed plugin, or None when no plugin
            exists yet. When None the plugin component still exists and still carries
            generic markers, so the harness cannot degrade into an unconditional pass
            simply because the plugin is absent.
        extra_plugin_markers: Additional lowercase substrings that identify plugin
            processes, for hosts where the plugin installs under a non-default path.

    Returns:
        ComponentRegistry ordered most specific first.
    """
    plugin_markers = ["claude_plugin_root", "claude-workflow-engine-plugin"]
    if plugin_root:
        normalised = str(plugin_root).replace("\\", "/").rstrip("/")
        plugin_markers.append(normalised.lower())
        qualified = qualified_tail(normalised)
        if qualified:
            plugin_markers.append(qualified)
    env_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env_root:
        plugin_markers.append(env_root.replace("\\", "/").lower())
    plugin_markers.extend(m.lower() for m in (extra_plugin_markers or []))

    registry = ComponentRegistry()
    registry.register(
        ComponentSpec(
            key=KEY_PLUGIN,
            role=ROLE_PLUGIN_COUNTED,
            markers=plugin_markers,
            description=(
                "The installed plugin: its command entry points. Under ADR-019 it "
                "bundles zero MCP servers, so there are no bundled servers to count."
            ),
        )
    )
    registry.register(
        ComponentSpec(
            key=KEY_RETAINED_USER_HOOKS,
            role=ROLE_PERMITTED_EXCLUSION,
            markers=["stop_notifier", "stop-notifier", "notification-hook", "notify_hook"],
            justification=(
                "ADR-010. The retained user-level Stop and Notification hooks are "
                "user-scope settings.json entries the plugin never owned, installed or "
                "modified. HLD section 9 permits this one exclusion and no other."
            ),
            description=(
                "Retained user-level Stop and Notification hooks. hooks/stop_notifier/ "
                "holds 17 spawn sites and fires every response turn."
            ),
        )
    )
    registry.register(
        ComponentSpec(
            key=KEY_MCP_USER_SCOPE,
            role=ROLE_OBSERVED,
            markers=["mcp-session-mgr", "mcp-git-ops", "mcp-github-api", "mcp_server", "mcp-"],
            description=(
                "User-scope MCP servers. Never bundled by the plugin (ADR-019); "
                "registered only by an explicit opt-in register-mcp step."
            ),
        )
    )
    registry.register(
        ComponentSpec(
            key=KEY_ENGINE,
            role=ROLE_OBSERVED,
            markers=["langgraph_engine", "3-level-flow", "claude-workflow-engine"],
            description=(
                "Engine code outside the plugin boundary. Reported for completeness; " "outside the plugin verdict."
            ),
        )
    )
    registry.register(
        ComponentSpec(
            key=KEY_HARNESS_SELF,
            role=ROLE_OBSERVED,
            markers=["tests/nfr1", "tests\\nfr1", "nfr1-sampler", "nfr1_selftest"],
            description=(
                "The harness's own scaffolding, including any process the PowerShell "
                "fallback backend spawns. Isolated so measurement apparatus never "
                "contaminates another component's count."
            ),
        )
    )
    registry.register(
        ComponentSpec(
            key=KEY_STATUSLINE_HOOK,
            role=ROLE_OBSERVED,
            markers=["statusline-command.sh"],
            description=(
                "Claude Code's own statusline, run on a timer by the Claude Code host "
                "process, never by the plugin. The marker names the retained script "
                "itself rather than the bash.exe/sh.exe interpreter that runs it, "
                "because the interpreter name is shared by countless unrelated "
                "processes and is exactly the kind of marker Part 1 of this change "
                "exists to stop from swallowing a plugin-spawned process."
            ),
        )
    )
    registry.register(
        ComponentSpec(
            key=KEY_CLAUDE_CODE_HOST,
            role=ROLE_OBSERVED,
            markers=["claude.exe"],
            description=(
                "The Claude Code CLI host process itself (observed on this machine as "
                "C:\\Users\\<user>\\.local\\bin\\claude.exe), plus every console host and "
                "shell it spawns to run a tool call (conhost.exe, sh.exe, cmd.exe, and "
                "any bash.exe not already claimed by the statusline marker above), "
                "attributed here by ANCESTRY rather than by their own name. Those "
                "interpreter and console-host names are generic and shared by "
                "unrelated software, so this component intentionally carries no "
                "marker for any of them; a process reaches this component only by "
                "having claude.exe somewhere in its ancestor chain. Processes that a "
                "real measurement window shows running under claude.exe but NOT "
                "reachable by ancestry (or where the host's own binary name differs "
                "from claude.exe on a given machine) are left unattributed rather than "
                "guessed at; see the module docstring for what this deliberately does "
                "not cover."
            ),
        )
    )
    return registry


class SpawnOpportunity(object):
    """One place the retained Stop hook can spawn a process on a response turn.

    A guarded opportunity whose target does not resolve is INERT. An inert opportunity
    is a PASS condition and must never be reported as a failure or as missing
    behaviour: the guard is doing its job.

    Attributes:
        site: Repository-relative file and line of the spawn call.
        kind: "unconditional" or "guarded".
        target_description: What the site launches.
        resolution_site: Where a guarded site resolves its target, if applicable.
        resolver: Zero-argument callable returning the resolved target path, or None
            for unconditional sites.
    """

    __slots__ = ("site", "kind", "target_description", "resolution_site", "resolver")

    def __init__(self, site, kind, target_description, resolution_site=None, resolver=None):
        self.site = site
        self.kind = kind
        self.target_description = target_description
        self.resolution_site = resolution_site
        self.resolver = resolver

    def evaluate(self):
        """Resolve this opportunity against the live filesystem.

        Returns:
            Dict describing whether the opportunity is armed or inert, with the
            resolved path when one could be computed.
        """
        result = {
            "site": self.site,
            "kind": self.kind,
            "target": self.target_description,
            "resolution_site": self.resolution_site,
        }
        if self.kind == "unconditional":
            result["state"] = "armed"
            result["resolved_target"] = None
            result["verdict_effect"] = "none: attributed to the permitted exclusion"
            return result
        try:
            resolved = self.resolver() if self.resolver else None
        except OSError as exc:
            result["state"] = "unresolved"
            result["resolved_target"] = None
            result["error"] = str(exc)
            result["verdict_effect"] = "none"
            return result
        result["resolved_target"] = str(resolved) if resolved else None
        armed = bool(resolved) and os.path.exists(str(resolved))
        result["state"] = "armed" if armed else "inert"
        result["verdict_effect"] = (
            "none: attributed to the permitted exclusion"
            if armed
            else "none: an inert guarded opportunity is a PASS, not a missing behaviour"
        )
        return result


def _resolve_stop_notifier_sync_version(repo_root):
    """Resolve the sync-version.py target as hooks/stop_notifier/post_impl.py does.

    post_impl.py line 284 computes Path(__file__).resolve().parent / "sync-version.py",
    which names a sibling inside hooks/stop_notifier/. No such file exists there; the
    real script lives at scripts/tools/sync-version.py. The guard at line 285 therefore
    suppresses the line 286 spawn.
    """
    return os.path.join(str(repo_root), "hooks", "stop_notifier", "sync-version.py")


def _resolve_stop_notifier_voice(repo_root):
    """Resolve the voice-notifier.py target as hooks/stop_notifier/helpers.py does.

    helpers.py line 142 computes CURRENT_DIR / "voice-notifier.py". CURRENT_DIR is NOT
    a sibling of helpers.py. It comes from hooks/ide_paths.py, which sets it to
    ~/.claude/scripts when that directory exists and ~/.claude/memory/current
    otherwise. The target therefore resolves under the user's home directory and is
    host-dependent: creating ~/.claude/scripts/voice-notifier.py arms this opportunity
    on that host. It is resolved live on every call rather than assumed inert.
    """
    hooks_dir = os.path.join(str(repo_root), "hooks")
    if hooks_dir not in sys.path:
        sys.path.insert(0, hooks_dir)
    try:
        import ide_paths
    except ImportError:
        home = os.path.expanduser("~")
        scripts_dir = os.path.join(home, ".claude", "scripts")
        base = scripts_dir if os.path.isdir(scripts_dir) else os.path.join(home, ".claude", "memory", "current")
        return os.path.join(base, "voice-notifier.py")
    return str(ide_paths.CURRENT_DIR / "voice-notifier.py")


def _repo_root_from_here():
    """Return the repository root inferred from this file's location."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def describe_stop_hook_spawn_floor(repo_root=None):
    """Describe the retained Stop hook's per-response-turn spawn floor.

    The floor is FOUR OPPORTUNITIES by project-owner ruling: two unconditional git
    rev-parse calls and two guarded script launches. Line numbers below were verified
    against source by an independent AST scan and agree with
    docs/phase-0-reverse-engineering/audit_surface.json.

    None of this affects the verdict. The retained Stop hook is the single permitted
    exclusion, so every process it spawns is excluded by construction. The description
    exists so a reader can tell an inert guard from an absent measurement.

    Args:
        repo_root: Repository root, or None to infer it from this file's location.

    Returns:
        Dict carrying the evaluated opportunities and their provenance.
    """
    root = repo_root or _repo_root_from_here()
    opportunities = [
        SpawnOpportunity(
            site="hooks/stop_notifier/post_impl.py:55",
            kind="unconditional",
            target_description="git rev-parse --abbrev-ref HEAD",
        ),
        SpawnOpportunity(
            site="hooks/stop_notifier/post_impl.py:208",
            kind="unconditional",
            target_description="git rev-parse --abbrev-ref HEAD",
        ),
        SpawnOpportunity(
            site="hooks/stop_notifier/post_impl.py:286",
            kind="guarded",
            target_description="python sync-version.py",
            resolution_site="hooks/stop_notifier/post_impl.py:284",
            resolver=lambda: _resolve_stop_notifier_sync_version(root),
        ),
        SpawnOpportunity(
            site="hooks/stop_notifier/voice.py:164",
            kind="guarded",
            target_description="python voice-notifier.py",
            resolution_site="hooks/stop_notifier/helpers.py:142",
            resolver=lambda: _resolve_stop_notifier_voice(root),
        ),
    ]
    evaluated = [opp.evaluate() for opp in opportunities]
    return {
        "expected_opportunity_count": 4,
        "observed_opportunity_count": len(evaluated),
        "provenance": (
            "count CITED from the project-owner ruling; line numbers MEASURED by AST "
            "scan and cross-checked against audit_surface.json"
        ),
        "armed": [o["site"] for o in evaluated if o["state"] == "armed"],
        "inert": [o["site"] for o in evaluated if o["state"] == "inert"],
        "inert_is_a_pass": True,
        "opportunities": evaluated,
        "verdict_effect": (
            "none. The retained Stop hook is the single permitted exclusion under "
            "ADR-010, so all four opportunities are excluded from the plugin count "
            "whether they fire or not."
        ),
    }
