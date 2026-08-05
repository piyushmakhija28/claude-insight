"""
Shared LLM Call Module - Strategy Pattern with Provider Interface.

Design Patterns:
  - Strategy: LLMProvider ABC defines the interface, concrete classes implement it
  - Chain of Responsibility: Fallback chain tries providers in configured order
  - Singleton: Each provider instantiated once, reused across all calls
  - Factory: get_providers() builds the chain from configuration

Providers (2 options):
  1. claude_cli  - Claude Code CLI (uses your Anthropic subscription)
  2. anthropic   - Anthropic API direct (needs ANTHROPIC_API_KEY)

Configuration (env vars):
  LLM_PROVIDER=auto            # auto | claude_cli | anthropic
  LLM_FALLBACK=anthropic       # Fallback provider (comma-separated for chain)
  ANTHROPIC_API_KEY=sk-ant-...
  ANTHROPIC_MODEL_FAST=claude-haiku-4-5-20251001
  ANTHROPIC_MODEL_DEEP=claude-opus-4-6-20250514

Model tiers (same across all providers):
  fast     -> classification, JSON, yes/no, titles
  balanced -> skill selection, code review, synthesis
  deep     -> planning, complex reasoning, architecture

Temperature guidelines (research-backed):
  0.0-0.1: JSON output, classification, code review
  0.2-0.3: Skill selection, title generation, structured output
  0.4:     Planning, complex reasoning
  0.7+:    Creative tasks (not used in pipeline)

Usage (unchanged - backward compatible):
    from langgraph_engine.llm_call import llm_call
    response = llm_call(prompt, model="fast", temperature=0.1)

NFR-2 / ADR-016 -- WHERE THE ONE PERMITTED TIMEOUT LIVES
--------------------------------------------------------
``timeout`` on every provider's ``call`` now defaults to None, meaning unbounded:
a CLI subprocess is bounded by progress (see ``liveness.run_supervised``) and
never by a deadline.

``AnthropicProvider`` is the single documented exception ADR-016 permits, and it
is deliberately the only one. It is a socket/HTTP-level timeout on ONE network
call, not a bound on the enclosing pipeline task: it is configurable through
ANTHROPIC_HTTP_TIMEOUT, it can be disabled entirely by setting that to 0, and
when it fires it is recorded as a failure against the ``anthropic_api`` circuit
breaker and surfaced as a retryable error rather than aborting the step. A
design with no socket timeout at all hangs forever with no recovery signal,
which ADR-016 rejects explicitly; a socket timeout that feeds a breaker is a
different construct from a deadline that kills a task, and only the second is
banned.
"""

import logging
import os
import shutil
from abc import ABC, abstractmethod
from typing import List, Optional

from .liveness import get_breaker, run_supervised

_log = logging.getLogger(__name__)


ANTHROPIC_HTTP_TIMEOUT_VAR = "ANTHROPIC_HTTP_TIMEOUT"

DEFAULT_ANTHROPIC_HTTP_TIMEOUT = 60.0


def _anthropic_socket_timeout(override=None):
    """Resolve the one socket/HTTP timeout ADR-016 permits.

    Args:
        override: Per-call value in seconds, or None to read the environment.

    Returns:
        float or None: The socket timeout, or None when it is disabled -- either
        by setting ANTHROPIC_HTTP_TIMEOUT to 0 or by passing 0 explicitly. None
        means the SDK is left to its own default behaviour with no bound imposed
        here, which is what "user-overridable to unbounded" requires.
    """
    if override is not None:
        return float(override) if float(override) > 0 else None
    raw = os.environ.get(ANTHROPIC_HTTP_TIMEOUT_VAR, "").strip()
    if not raw:
        return DEFAULT_ANTHROPIC_HTTP_TIMEOUT
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return DEFAULT_ANTHROPIC_HTTP_TIMEOUT
    return value if value > 0 else None


# =============================================================================
# INTERFACE: LLMProvider (Strategy Pattern)
# =============================================================================


class LLMProvider(ABC):
    """Abstract interface for LLM providers.

    All providers must implement call() and is_available().
    Same input/output contract regardless of backend.
    """

    @abstractmethod
    def call(
        self,
        prompt: str,
        model: str = "fast",
        temperature: float = 0.3,
        timeout: Optional[float] = None,
        json_mode: bool = False,
    ) -> Optional[str]:
        """Send prompt to LLM and return response text.

        Args:
            prompt: The prompt text to send.
            model: Tier - "fast", "balanced", or "deep".
            temperature: Sampling temperature (0.0-1.0).
            timeout: Provider-specific bound. None, the default, means unbounded:
                see the module docstring for why only one provider honours it.
            json_mode: If True, request JSON-formatted output.

        Returns:
            Response text string, or None on failure.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is configured and reachable.

        Called ONCE at init time. Result is cached.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging."""
        ...


# =============================================================================
# IMPLEMENTATION: ClaudeCLIProvider
# =============================================================================


class ClaudeCLIProvider(LLMProvider):
    """Claude Code CLI provider (uses user's Anthropic subscription)."""

    MODEL_MAP = {
        "fast": "haiku",
        "balanced": "sonnet",
        "deep": "opus",
        "fast_classification": "haiku",
        "complex_reasoning": "opus",
        "synthesis": "sonnet",
        "planning": "opus",
        "code_review": "sonnet",
    }

    def __init__(self):
        """Detect the claude CLI on PATH and record availability."""
        self._claude_path = shutil.which("claude")
        self._available = self._claude_path is not None

    @property
    def name(self) -> str:
        """Provider name used in logs and get_active_providers()."""
        return "claude_cli"

    def is_available(self) -> bool:
        """Return True when the 'claude' CLI was found on PATH at init."""
        return self._available

    def call(self, prompt, model="fast", temperature=0.3, timeout=None, json_mode=False):
        """Run the prompt through the 'claude' CLI and return its stdout.

        The CLI is bounded by progress rather than by elapsed time: it runs for as
        long as it keeps writing, and the ``claude_cli`` circuit breaker is what
        stops a systemically failing CLI from being called again.

        Args:
            prompt: Prompt text; truncated to 10k chars to stay within CLI limits.
            model: Tier key mapped to a CLI model alias via MODEL_MAP.
            temperature: Accepted for interface parity; the CLI ignores it.
            timeout: Seconds of CLI silence tolerated before the child is treated
                as stuck. None, the default, means unbounded.
            json_mode: Accepted for interface parity; not enforced by the CLI.

        Returns:
            Stripped stdout on success, or None if unavailable, on non-zero exit,
            empty output, or any subprocess error.
        """
        if not self._available:
            return None

        cli_model = self.MODEL_MAP.get(model, "haiku")

        if len(prompt) > 10000:
            prompt = prompt[:10000] + "\n[truncated]"

        env = os.environ.copy()
        env["CLAUDE_WORKFLOW_RUNNING"] = "1"

        try:
            result = run_supervised(
                [self._claude_path, "-p", "--model", cli_model, prompt],
                lease_interval=timeout,
                lease_name="llm_claude_cli",
                env=env,
                breaker_name="claude_cli",
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception as exc:
            _log.debug("ClaudeCLIProvider call failed: %s", exc)
        return None


# =============================================================================
# IMPLEMENTATION: AnthropicProvider (Direct Claude API via SDK)
# =============================================================================


class AnthropicProvider(LLMProvider):
    """Anthropic API provider (direct Claude API, requires ANTHROPIC_API_KEY).

    Uses the official Anthropic Python SDK for reliable API access with
    automatic retries, proper error handling, and typed exceptions.
    This is DIFFERENT from ClaudeCLIProvider which uses the 'claude' CLI tool.
    """

    MODEL_MAP = {
        "fast": "claude-haiku-4-5",
        "balanced": "claude-sonnet-4-6",
        "deep": "claude-opus-4-6",
        "fast_classification": "claude-haiku-4-5",
        "complex_reasoning": "claude-opus-4-6",
        "synthesis": "claude-sonnet-4-6",
        "planning": "claude-opus-4-6",
        "code_review": "claude-sonnet-4-6",
    }

    def __init__(self):
        """Read the Anthropic API key and base URL from the environment."""
        self._api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self._base_url = os.getenv("ANTHROPIC_BASE_URL", None)  # SDK handles default
        # Allow model override via env
        self._model_fast = os.getenv("ANTHROPIC_MODEL_FAST", self.MODEL_MAP["fast"])
        self._model_balanced = os.getenv("ANTHROPIC_MODEL_BALANCED", self.MODEL_MAP["balanced"])
        self._model_deep = os.getenv("ANTHROPIC_MODEL_DEEP", self.MODEL_MAP["deep"])
        self._available = bool(self._api_key)
        self._client = None  # Lazy init -- avoid import overhead at startup

    def _get_client(self):
        """Lazy-init the Anthropic SDK client (once per provider instance)."""
        if self._client is None:
            try:
                import anthropic as _anthropic_sdk

                kwargs = {"api_key": self._api_key, "max_retries": 2}
                if self._base_url:
                    kwargs["base_url"] = self._base_url
                self._client = _anthropic_sdk.Anthropic(**kwargs)
            except ImportError:
                _log.warning("anthropic SDK not installed. Run: pip install anthropic")
                self._available = False
        return self._client

    @property
    def name(self) -> str:
        """Provider name used in logs and get_active_providers()."""
        return "anthropic"

    def is_available(self) -> bool:
        """Return True when an ANTHROPIC_API_KEY was present at init."""
        return self._available

    def call(self, prompt, model="fast", temperature=0.3, timeout=None, json_mode=False):
        """Send the prompt to the Anthropic Messages API and return the text.

        Selects the model by tier, optionally appends a JSON-only instruction,
        and maps typed SDK exceptions to graceful failures (auth errors disable
        the provider; rate-limit/status/connection errors are logged at debug).

        Args:
            prompt: Prompt text to send.
            model: Tier key selecting fast/balanced/deep model ids.
            temperature: Sampling temperature (0.0-1.0).
            timeout: Per-request socket/HTTP timeout override in seconds. None,
                the default, uses ANTHROPIC_HTTP_TIMEOUT; setting either to 0
                disables the socket timeout entirely. This is the ONE timeout
                ADR-016 permits, and it feeds the circuit breaker rather than
                aborting the enclosing pipeline task.
            json_mode: If True, append an instruction to return only valid JSON.

        Returns:
            The response text, or None on any failure or empty output.
        """
        if not self._available:
            return None

        client = self._get_client()
        if client is None:
            return None

        # Select model by tier
        if model in ("deep", "complex_reasoning", "planning"):
            api_model = self._model_deep
        elif model in ("balanced", "synthesis", "code_review"):
            api_model = self._model_balanced
        else:
            api_model = self._model_fast

        actual_prompt = prompt
        if json_mode:
            actual_prompt = prompt + "\n\nIMPORTANT: Return ONLY valid JSON. No explanation or markdown."

        try:
            import anthropic as _anthropic_sdk

            breaker = get_breaker("anthropic_api")
            socket_timeout = _anthropic_socket_timeout(timeout)
            response = breaker.call(
                lambda: client.messages.create(
                    model=api_model,
                    max_tokens=2048,
                    messages=[{"role": "user", "content": actual_prompt}],
                    temperature=temperature,
                    timeout=socket_timeout,
                )
            )
            text = next((block.text for block in response.content if block.type == "text"), "").strip()
            return text if text else None

        except _anthropic_sdk.AuthenticationError:
            _log.warning("AnthropicProvider: invalid API key -- disabling provider")
            self._available = False
        except _anthropic_sdk.RateLimitError as exc:
            _log.debug("AnthropicProvider rate limited: %s", exc)
        except _anthropic_sdk.APIStatusError as exc:
            _log.debug("AnthropicProvider API error %s: %s", exc.status_code, exc)
        except _anthropic_sdk.APIConnectionError as exc:
            _log.debug("AnthropicProvider connection error: %s", exc)
        except Exception as exc:
            _log.debug("AnthropicProvider call failed: %s", exc)
        return None


# =============================================================================
# PROVIDER CHAIN (Chain of Responsibility + Factory)
# =============================================================================

# Default temperature per model tier (research-backed)
DEFAULT_TEMPERATURES = {
    "fast": 0.1,
    "balanced": 0.3,
    "deep": 0.4,
    "fast_classification": 0.1,
    "complex_reasoning": 0.4,
    "synthesis": 0.2,
    "planning": 0.4,
    "code_review": 0.1,
}

# Provider registry (Singleton instances)
_PROVIDER_REGISTRY = {
    "claude_cli": ClaudeCLIProvider,
    "anthropic": AnthropicProvider,
}

_provider_chain: List[LLMProvider] = []


def _build_provider_chain() -> List[LLMProvider]:
    """Build the provider chain from configuration (Factory Pattern).

    Configuration via env vars:
      LLM_PROVIDER=auto       -> try all available providers (default)
      LLM_PROVIDER=anthropic  -> Anthropic API first, then LLM_FALLBACK chain
      LLM_PROVIDER=claude_cli -> Claude CLI first, then LLM_FALLBACK chain
      LLM_FALLBACK=anthropic  -> explicit fallback chain (comma-separated)

    Default fallback strategy:
      - auto mode             -> try all providers: claude_cli -> anthropic
      - Specific provider set -> use that provider; apply LLM_FALLBACK if set
      - LLM_FALLBACK set      -> use user's explicit fallback (overrides default)

    Returns:
        List of instantiated, available providers in priority order.
    """
    primary = os.getenv("LLM_PROVIDER", "auto").strip().lower()
    fallback_str = os.getenv("LLM_FALLBACK", "").strip()

    if primary == "auto":
        # Auto mode: try Claude CLI -> Anthropic API
        order = ["claude_cli", "anthropic"]
    else:
        order = [primary]
        if fallback_str:
            # User explicitly defined fallbacks -- respect their choice
            order.extend(f.strip() for f in fallback_str.split(",") if f.strip())

    chain = []
    for provider_name in order:
        cls = _PROVIDER_REGISTRY.get(provider_name)
        if cls:
            instance = cls()
            if instance.is_available():
                chain.append(instance)

    return chain


# Build chain once at import time (Singleton)
_provider_chain = _build_provider_chain()


# =============================================================================
# PUBLIC API (Backward Compatible)
# =============================================================================


def llm_call(
    prompt: str,
    model: str = "fast",
    temperature: Optional[float] = None,
    timeout: Optional[float] = None,
    json_mode: bool = False,
) -> Optional[str]:
    """Make an LLM call with automatic fallback chain.

    Tries each configured provider in order until one succeeds.
    Fully backward compatible - same signature as before.

    Args:
        prompt: The prompt text to send.
        model: "fast" (haiku), "balanced" (sonnet), "deep" (opus).
        temperature: Override temp (default: auto per model tier).
        timeout: Provider-specific bound. None, the default, means unbounded.
        json_mode: If True, request JSON format.

    Returns:
        Response text string, or None if all providers failed.
    """
    if temperature is None:
        temperature = DEFAULT_TEMPERATURES.get(model, 0.3)

    for provider in _provider_chain:
        response = provider.call(prompt, model, temperature, timeout, json_mode)
        if response:
            return response

    return None


def get_active_providers() -> List[str]:
    """Return names of currently active providers in chain order."""
    return [p.name for p in _provider_chain]


def generate_llm_commit_title(commit_type: str = None, cwd: str = None) -> Optional[str]:
    """Generate a meaningful commit title using LLM with staged diff context.

    Single source of truth for LLM-powered commit messages. Used by both
    git-auto-commit-policy.py and github_pr_workflow.py.

    Args:
        commit_type: Optional semantic type (feat, fix, refactor, etc.)
        cwd: Working directory for git commands (default: current dir)

    Returns:
        Commit title string (max 72 chars), or None if LLM unavailable.
    """
    try:
        stat_result = run_supervised(["git", "diff", "--cached", "--stat"], cwd=cwd)
        stat_text = stat_result.stdout.strip() if stat_result.returncode == 0 else ""

        diff_result = run_supervised(["git", "diff", "--cached"], cwd=cwd)
        diff_text = diff_result.stdout[:3000] if diff_result.returncode == 0 else ""

        if not stat_text and not diff_text:
            return None

        type_hint = f"Commit type: {commit_type}\n" if commit_type else ""
        type_rule = (
            f"- Start with type prefix: {commit_type}:\n"
            if commit_type
            else "- Use conventional commit format: type: description\n"
        )

        prompt = (
            f"Generate a git commit message for these changes.\n"
            f"{type_hint}\n"
            f"Changed files:\n{stat_text}\n\n"
            f"Diff (truncated):\n{diff_text}\n\n"
            f"Rules:\n"
            f"- Return ONLY the commit title (one line, under 72 chars)\n"
            f"{type_rule}"
            f"- Focus on WHAT changed and WHY, not just file names\n"
            f"- Be specific: 'fix stash detection using stdout+stderr' not 'fix issues'\n"
            f"- No quotes, no explanation, just the commit title line\n"
        )

        response = llm_call(prompt, model="fast", temperature=0.1)
        if not response:
            return None

        title = response.strip().splitlines()[0].strip().strip('"').strip("'")
        if commit_type and not title.lower().startswith(commit_type):
            title = f"{commit_type}: {title}"
        return title[:69] + "..." if len(title) > 72 else title

    except Exception as exc:
        _log.debug("generate_llm_commit_title failed: %s", exc)
        return None
