"""V2-035 / PRD NFR-2 / SRS NFR-8 regression suite.

Three obligations, kept separate because they fail for different reasons:

1. PRESENCE -- all five ADR-016 mechanisms exist and behave as specified. These
   tests exercise the mechanisms rather than grepping for their names, because a
   name is not a behaviour and AC 4 is only worth more than a checklist if the
   assertions can actually fail.
2. ABSENCE -- the gate finds a fixed timeout planted on the pipeline path, and
   does NOT find one in prose, in a configurable value, or outside that path.
   Every check has a companion proving it can fail.
3. MUTATION -- a scanner rewritten to report nothing is rejected by this suite.
   A check that cannot detect its own defeat is not evidence.

The gate is executed from its STORED form: fixtures are written to a temporary
tree on disk and the gate's own ``main`` is invoked against that root, so what is
tested is the file that ships rather than a string assembled in a test.
"""

import ast
import importlib.util
import itertools
import random
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = REPO_ROOT / "scripts" / "verify_no_fixed_timeouts.py"

_LOAD_COUNTER = itertools.count()

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def load_gate():
    """Import the gate from its stored file rather than from a copy.

    Returns:
        module: The loaded ``verify_no_fixed_timeouts`` module.
    """
    name = "verify_no_fixed_timeouts_under_test_%d" % next(_LOAD_COUNTER)
    spec = importlib.util.spec_from_file_location(name, GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def gate():
    """Provide a freshly loaded gate module for one test."""
    return load_gate()


def _write(root, relative, body):
    """Write a fixture module into a temporary scan tree.

    Args:
        root: Temporary repository root.
        relative: Repository-relative path for the module.
        body: Source text, dedented before writing.

    Returns:
        Path: The written file.
    """
    target = Path(root) / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(textwrap.dedent(body), encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# AC 4 -- presence of all five ADR-016 mechanisms
# ---------------------------------------------------------------------------


class TestMechanismsPresent:
    """Every ADR-016 mechanism exists and does what the ADR says it does."""

    def test_mechanism_1_attempt_budget_bounds_by_attempts_not_time(self):
        """An attempt budget is exhausted by counting, with no clock involved."""
        from langgraph_engine.liveness import AttemptBudget, BudgetExhausted

        budget = AttemptBudget(3, "unit")
        assert [budget.consume() for _ in range(3)] == [1, 2, 3]
        assert budget.exhausted
        with pytest.raises(BudgetExhausted) as caught:
            budget.consume()
        assert caught.value.limit == 3

    def test_mechanism_1_budget_rejects_an_unsatisfiable_limit(self):
        """A limit below one would forbid the first attempt, so it is refused."""
        from langgraph_engine.liveness import AttemptBudget

        with pytest.raises(ValueError):
            AttemptBudget(0, "unit")

    def test_mechanism_2_lease_renewal_defeats_expiry_but_silence_does_not(self):
        """Renewal resets the silence measurement; elapsed time alone never expires a lease."""
        from langgraph_engine.liveness import Lease, LeaseExpired

        now = {"t": 0.0}
        lease = Lease("unit", interval=10.0, clock=lambda: now["t"], warn_on_degraded=False)

        for _ in range(100):
            now["t"] += 9.0
            lease.renew()
        assert not lease.expired(), "a lease renewed every 9s must survive 900s of runtime"
        assert lease.renewals == 100

        now["t"] += 11.0
        assert lease.expired()
        with pytest.raises(LeaseExpired):
            lease.check()

    def test_mechanism_2_lease_defaults_to_unbounded(self):
        """With no interval configured a lease never expires, however long the silence."""
        from langgraph_engine.liveness import Lease

        now = {"t": 0.0}
        lease = Lease("unit", clock=lambda: now["t"], warn_on_degraded=False)
        now["t"] += 10**9
        assert lease.interval is None
        assert not lease.expired()

    def test_mechanism_2_lease_reports_its_own_durability(self):
        """The lease records whether durable state actually backs it.

        Durable checkpointing is currently unavailable in this environment, so the
        assertion is that the lease AGREES with the measured probe rather than
        that it is durable. A lease that claimed durability it did not have would
        be worse than one that admits the gap.
        """
        from langgraph_engine.liveness import Lease, durable_state_available

        lease = Lease("unit", warn_on_degraded=False)
        assert lease.durable is durable_state_available()
        assert lease.degraded is not durable_state_available()

    def test_mechanism_2_durability_probe_matches_the_checkpointer_module(self):
        """The probe's import paths are the same two the checkpointer itself tries."""
        from langgraph_engine import checkpointer
        from langgraph_engine.liveness import durable_state_available

        assert durable_state_available() is bool(checkpointer._SQLITE_SAVER_AVAILABLE)

    def test_mechanism_3_convergence_signals_no_progress_after_patience(self):
        """Repeated identical states converge; a changed state resets the run."""
        from langgraph_engine.liveness import ConvergenceMonitor

        monitor = ConvergenceMonitor(patience=3)
        assert not monitor.observe({"done": 1})
        assert not monitor.observe({"done": 1})
        assert not monitor.observe({"done": 1})
        assert monitor.observe({"done": 1})

        monitor.reset()
        for value in (1, 2, 3, 4, 5):
            assert not monitor.observe({"done": value})

    def test_mechanism_3_convergence_ignores_dict_ordering(self):
        """Key order is not part of a state's meaning and must not look like progress."""
        from langgraph_engine.liveness import state_hash

        assert state_hash({"a": 1, "b": 2}) == state_hash({"b": 2, "a": 1})

    def test_mechanism_4_breaker_exists_per_external_dependency(self):
        """Each named dependency gets its own breaker; one outage cannot fail-fast another."""
        from langgraph_engine.liveness import EXTERNAL_DEPENDENCIES, get_breaker, reset_registry

        reset_registry()
        breakers = {name: get_breaker(name) for name in EXTERNAL_DEPENDENCIES}
        assert len(set(id(item) for item in breakers.values())) == len(EXTERNAL_DEPENDENCIES)
        assert get_breaker("claude_cli") is breakers["claude_cli"]
        reset_registry()

    def test_mechanism_4_reopen_wait_is_not_fixed(self):
        """Consecutive trips must back off; a constant reopen wait is the anti-pattern."""
        from langgraph_engine.liveness import CircuitBreaker

        breaker = CircuitBreaker("unit", initial_wait=30.0, max_wait=300.0)
        waits = [breaker.reopen_wait(n) for n in (1, 2, 3, 4)]
        assert waits == [30.0, 60.0, 120.0, 240.0]
        assert len(set(waits)) == len(waits), "reopen wait must differ per trip count"
        assert breaker.reopen_wait(10) == 300.0, "the wait must be capped, not unbounded"

    def test_mechanism_4_min_calls_floor_prevents_a_trip_on_noise(self):
        """Below the floor no failure rate may trip anything, however bad it looks."""
        from langgraph_engine.liveness import STATE_CLOSED, CircuitBreaker

        breaker = CircuitBreaker("unit", failure_rate_threshold=0.5, min_calls=10, window_size=20)
        for _ in range(9):
            breaker.record_failure()
        assert breaker.failure_rate == 1.0
        assert breaker.state == STATE_CLOSED, "9 failures is below the 10-call floor"
        breaker.record_failure()
        assert breaker.state != STATE_CLOSED

    def test_mechanism_4_breaker_trips_and_fails_fast_without_calling(self):
        """An OPEN breaker rejects before the dependency is touched."""
        from langgraph_engine.liveness import BreakerOpen, CircuitBreaker

        breaker = CircuitBreaker("unit", failure_rate_threshold=0.5, min_calls=4, window_size=8)
        for _ in range(4):
            breaker.record_failure()
        calls = []
        with pytest.raises(BreakerOpen):
            breaker.call(lambda: calls.append(1))
        assert calls == [], "an OPEN breaker must not dispatch the call"

    def test_mechanism_4_half_open_probe_success_closes_the_breaker(self):
        """A successful probe after the cooldown returns the breaker to CLOSED."""
        from langgraph_engine.liveness import STATE_CLOSED, STATE_OPEN, CircuitBreaker

        now = {"t": 0.0}
        breaker = CircuitBreaker(
            "unit", failure_rate_threshold=0.5, min_calls=4, window_size=8, initial_wait=30.0, clock=lambda: now["t"]
        )
        for _ in range(4):
            breaker.record_failure()
        assert breaker.state == STATE_OPEN
        assert not breaker.allows()
        now["t"] += 31.0
        assert breaker.allows()
        breaker.record_success()
        assert breaker.state == STATE_CLOSED

    def test_mechanism_slow_call_rate_trips_without_aborting_any_call(self):
        """ADR-016's own fifth mechanism: degradation is judged by rate, not by cancelling a call."""
        from langgraph_engine.liveness import STATE_OPEN, CircuitBreaker

        breaker = CircuitBreaker(
            "unit",
            failure_rate_threshold=0.99,
            slow_call_rate_threshold=0.5,
            slow_call_duration=10.0,
            min_calls=4,
            window_size=8,
        )
        for _ in range(4):
            breaker.record_success(duration=120.0)
        assert breaker.state == STATE_OPEN, "a population of slow successes must trip the breaker"

    def test_mechanism_5_full_jitter_samples_the_whole_interval(self):
        """Full jitter draws uniformly from zero to the capped exponential ceiling."""
        from langgraph_engine.liveness import deterministic_ceiling, full_jitter_delay

        rng = random.Random(1729)
        ceiling = deterministic_ceiling(3, base=1.0, cap=30.0)
        assert ceiling == 8.0
        samples = [full_jitter_delay(3, 1.0, 30.0, rng=rng) for _ in range(500)]
        assert all(0.0 <= value <= ceiling for value in samples)
        assert min(samples) < ceiling * 0.1, "full jitter must be able to retry almost immediately"
        assert max(samples) > ceiling * 0.9, "full jitter must be able to use the whole interval"
        assert len(set(samples)) > 1, "a deterministic delay is not jitter"

    def test_mechanism_5_jitter_ceiling_is_capped(self):
        """The exponential ceiling saturates rather than growing without bound."""
        from langgraph_engine.liveness import deterministic_ceiling

        assert deterministic_ceiling(0, 2.0, 30.0) == 2.0
        assert deterministic_ceiling(20, 2.0, 30.0) == 30.0

    def test_all_five_mechanisms_are_importable_from_one_surface(self):
        """AC 4's checklist, asserted against the package's public surface."""
        import langgraph_engine.liveness as liveness

        for name in ("AttemptBudget", "Lease", "ConvergenceMonitor", "CircuitBreaker", "full_jitter_delay"):
            assert hasattr(liveness, name), "ADR-016 mechanism missing: " + name


class TestMechanismComposition:
    """The new mechanisms compose with the machinery that was already here."""

    def test_breaker_rejection_never_reaches_the_effect_ledger(self, tmp_path):
        """A fail-fast must not leave the PENDING entry the ledger refuses to guess about."""
        from langgraph_engine.effect_ledger import EffectLedger
        from langgraph_engine.liveness import BreakerOpen, CircuitBreaker

        ledger = EffectLedger("nfr2-compose", base_dir=str(tmp_path))
        key = ledger.effect_key(step=2, effect_name="github_issue")
        breaker = CircuitBreaker("unit", failure_rate_threshold=0.5, min_calls=2, window_size=4)
        breaker.record_failure()
        breaker.record_failure()

        with pytest.raises(BreakerOpen):
            breaker.call(lambda: ledger.run_once(key, lambda: {"issue": 1}))

        assert ledger.lookup(key) is None, "the breaker must reject before the ledger announces anything"

    def test_retry_driver_defers_error_classification_to_llm_retry(self):
        """The driver consumes the existing classifier rather than growing a second one."""
        from langgraph_engine.liveness import AttemptBudget, BudgetExhausted, call_with_liveness, reset_registry
        from langgraph_engine.sdlc_pipeline.llm_retry import is_llm_retryable

        reset_registry()
        attempts = {"n": 0}

        def flaky():
            attempts["n"] += 1
            raise RuntimeError("connection reset by peer")

        with pytest.raises(BudgetExhausted):
            call_with_liveness(
                flaky,
                budget=AttemptBudget(3, "unit"),
                is_retryable=is_llm_retryable,
                sleep=lambda _seconds: None,
            )
        assert attempts["n"] == 3

        terminal = {"n": 0}

        def permanent():
            terminal["n"] += 1
            raise ValueError("invalid model name")

        with pytest.raises(ValueError):
            call_with_liveness(
                permanent,
                budget=AttemptBudget(3, "unit"),
                is_retryable=is_llm_retryable,
                sleep=lambda _seconds: None,
            )
        assert terminal["n"] == 1, "a terminal error must not be retried"
        reset_registry()

    def test_breaker_trip_is_not_treated_as_rate_limit_evidence(self):
        """model_fallback escalates on positive rate-limit evidence only; a trip is not that."""
        from langgraph_engine.liveness import BreakerOpen
        from langgraph_engine.model_fallback import FAILURE_OTHER, classify_failure

        assert classify_failure(BreakerOpen("claude_cli", 30.0)) == FAILURE_OTHER


class TestSupervisedSubprocess:
    """The call-site replacement for subprocess.run(timeout=N)."""

    def test_unbounded_by_default_and_captures_output(self):
        """With no interval configured the child runs to completion."""
        from langgraph_engine.liveness import run_supervised

        result = run_supervised([sys.executable, "-c", "print('hello')"])
        assert result.returncode == 0
        assert "hello" in result.stdout

    def test_stdin_is_delivered(self):
        """A prompt written to stdin reaches the child."""
        from langgraph_engine.liveness import run_supervised

        result = run_supervised(
            [sys.executable, "-c", "import sys; sys.stdout.write(sys.stdin.read().upper())"],
            input="abc",
        )
        assert result.stdout.strip() == "ABC"

    def test_a_slow_but_talking_child_is_not_killed(self):
        """Duration alone never ends a child; this one outlives its own lease interval."""
        from langgraph_engine.liveness import run_supervised

        script = "import sys,time\nfor _ in range(8):\n    sys.stdout.write('.');sys.stdout.flush();time.sleep(0.15)\n"
        result = run_supervised([sys.executable, "-u", "-c", script], lease_interval=0.6)
        assert result.returncode == 0
        assert result.stdout.count(".") == 8
        assert result.duration > 0.6, "the child must have outlived its own lease interval"

    def test_a_silent_child_is_ended_for_no_progress(self):
        """Silence past the interval is a no-progress verdict, not a timeout."""
        from langgraph_engine.liveness import NoProgress, run_supervised

        with pytest.raises(NoProgress):
            run_supervised([sys.executable, "-c", "import time; time.sleep(30)"], lease_interval=0.5)


# ---------------------------------------------------------------------------
# AC 1 -- absence, with both directions of specificity
# ---------------------------------------------------------------------------


PIPELINE_FIXTURE = "langgraph_engine/sdlc_pipeline/nodes/fixture_node.py"

OUTSIDE_FIXTURE = "langgraph_engine/diagrams/fixture_diagram.py"


def _run_gate(gate, root):
    """Run the gate over a temporary root and return its exit status.

    Args:
        gate: Loaded gate module.
        root: Temporary repository root.

    Returns:
        int: Gate exit status.
    """
    return gate.main(["--root", str(root)])


class TestGateNegative:
    """Each check has a companion proving it can fail."""

    def test_planted_fixed_literal_on_the_pipeline_path_is_rejected(self, gate, tmp_path):
        """The load-bearing negative: a fixed timeout on the pipeline path fails the gate."""
        _write(tmp_path, PIPELINE_FIXTURE, "import subprocess\n\n\ndef go():\n    subprocess.run(['x'], timeout=60)\n")
        assert _run_gate(gate, tmp_path) == 1

    def test_planted_env_default_on_the_pipeline_path_is_rejected(self, gate, tmp_path):
        """An env var makes a value overridable; a finite DEFAULT is still a fixed timeout."""
        _write(
            tmp_path,
            PIPELINE_FIXTURE,
            """
            import os
            import subprocess

            _T = int(os.getenv("SOME_TIMEOUT", "90"))


            def go():
                subprocess.run(["x"], timeout=_T)
            """,
        )
        assert _run_gate(gate, tmp_path) == 1

    def test_planted_composite_arithmetic_is_rejected(self, gate, tmp_path):
        """The 75-second composite shape -- a finite default plus a constant -- is caught."""
        _write(
            tmp_path,
            PIPELINE_FIXTURE,
            """
            import os
            import subprocess


            def go():
                subprocess.run(["x"], timeout=int(os.getenv("T", "60")) + 15)
            """,
        )
        assert _run_gate(gate, tmp_path) == 1

    def test_planted_signal_alarm_is_rejected(self, gate, tmp_path):
        """signal.alarm is named by the acceptance criterion and is detected as such."""
        _write(tmp_path, PIPELINE_FIXTURE, "import signal\n\n\ndef go():\n    signal.alarm(30)\n")
        assert _run_gate(gate, tmp_path) == 1

    def test_an_unknown_value_shape_is_rejected_rather_than_ignored(self, gate, tmp_path):
        """The accepted set is defined and the complement fails, so a novel shape cannot slip past."""
        _write(
            tmp_path,
            PIPELINE_FIXTURE,
            """
            import subprocess

            from somewhere import mystery


            def go():
                subprocess.run(["x"], timeout=mystery.value)
            """,
        )
        assert _run_gate(gate, tmp_path) == 1


class TestGateSpecificity:
    """The gate must not fire on things that are not fixed timeouts."""

    def test_prose_mentioning_timeout_does_not_fire(self, gate, tmp_path):
        """A docstring, a comment and a log string all say the token and none is a timeout."""
        _write(
            tmp_path,
            PIPELINE_FIXTURE,
            '''
            """Module docstring explaining that timeout=60 used to be passed here."""


            def go():
                """Call the child.

                The old implementation used timeout=90, and signal.alarm(30) before that.
                """
                # historical note: subprocess.run(cmd, timeout=300) was the original shape
                return "timeout=45 appears in this log format string"
            ''',
        )
        assert _run_gate(gate, tmp_path) == 0

    def test_a_configurable_unbounded_timeout_does_not_fire(self, gate, tmp_path):
        """env_optional_seconds returns None when unset, which is what the criterion asks for."""
        _write(
            tmp_path,
            PIPELINE_FIXTURE,
            """
            from langgraph_engine.liveness import env_optional_seconds


            def go(call):
                return call(timeout=env_optional_seconds("SOME_SILENCE"))
            """,
        )
        assert _run_gate(gate, tmp_path) == 0

    def test_an_explicit_none_does_not_fire(self, gate, tmp_path):
        """A literal None is unbounded and must be accepted."""
        _write(tmp_path, PIPELINE_FIXTURE, "def go(call):\n    return call(timeout=None)\n")
        assert _run_gate(gate, tmp_path) == 0

    def test_a_parameter_defaulting_to_none_does_not_fire(self, gate, tmp_path):
        """A pass-through parameter whose default is None is unbounded by default."""
        _write(
            tmp_path,
            PIPELINE_FIXTURE,
            "def go(call, timeout=None):\n    return call(timeout=timeout)\n",
        )
        assert _run_gate(gate, tmp_path) == 0

    def test_a_fixed_timeout_outside_the_pipeline_path_does_not_fail_the_gate(self, gate, tmp_path):
        """Scope is enforced as declared: outside the pipeline path a fixed timeout is reported only."""
        _write(tmp_path, OUTSIDE_FIXTURE, "import subprocess\n\n\ndef go():\n    subprocess.run(['x'], timeout=60)\n")
        assert _run_gate(gate, tmp_path) == 0

        sites, _unreadable = gate.scan([Path(tmp_path) / OUTSIDE_FIXTURE], Path(tmp_path))
        assert len(sites) == 1, "the site must still be SCANNED and reported"
        assert sites[0].value_class == gate.VALUE_FIXED_LITERAL
        assert not sites[0].is_violation()

    def test_a_non_timeout_keyword_does_not_fire(self, gate, tmp_path):
        """Only the timeout keyword is a timeout; a similarly named argument is not."""
        _write(
            tmp_path,
            PIPELINE_FIXTURE,
            "def go(call):\n    return call(interval=60, deadline=60, lease_interval=60)\n",
        )
        assert _run_gate(gate, tmp_path) == 0


class TestTheOnePermittedTimeout:
    """AC 3's exception, asserted rather than asserted-about.

    An exemption whose justification is only prose in a dict is a claim. These
    tests make each clause of that justification a property the suite enforces:
    configurable, disable-able to unbounded, and routed into a circuit breaker
    instead of aborting the enclosing step.
    """

    def test_the_socket_timeout_is_configurable(self, monkeypatch):
        """ANTHROPIC_HTTP_TIMEOUT overrides the default."""
        from langgraph_engine.llm_call import DEFAULT_ANTHROPIC_HTTP_TIMEOUT, _anthropic_socket_timeout

        monkeypatch.delenv("ANTHROPIC_HTTP_TIMEOUT", raising=False)
        assert _anthropic_socket_timeout() == DEFAULT_ANTHROPIC_HTTP_TIMEOUT
        monkeypatch.setenv("ANTHROPIC_HTTP_TIMEOUT", "12.5")
        assert _anthropic_socket_timeout() == 12.5

    def test_the_socket_timeout_can_be_disabled_to_unbounded(self, monkeypatch):
        """Zero means no bound at all, which is what "user-overridable" has to permit."""
        from langgraph_engine.llm_call import _anthropic_socket_timeout

        monkeypatch.setenv("ANTHROPIC_HTTP_TIMEOUT", "0")
        assert _anthropic_socket_timeout() is None
        monkeypatch.delenv("ANTHROPIC_HTTP_TIMEOUT", raising=False)
        assert _anthropic_socket_timeout(0) is None

    def test_a_malformed_override_falls_back_rather_than_crashing(self, monkeypatch):
        """A typo in an env var must not take the provider down."""
        from langgraph_engine.llm_call import DEFAULT_ANTHROPIC_HTTP_TIMEOUT, _anthropic_socket_timeout

        monkeypatch.setenv("ANTHROPIC_HTTP_TIMEOUT", "not-a-number")
        assert _anthropic_socket_timeout() == DEFAULT_ANTHROPIC_HTTP_TIMEOUT

    def test_the_socket_call_is_routed_through_a_circuit_breaker(self):
        """The clause that makes it an exception rather than a violation.

        Asserted structurally over the AST of the shipped module: the
        ``messages.create`` call carrying the timeout must sit inside a
        ``breaker.call(...)``. A timeout that aborted the step directly would
        satisfy none of ADR-016's conditions, and prose in a dict cannot detect
        that regression.
        """
        source = (REPO_ROOT / "langgraph_engine" / "llm_call.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        guarded = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "call"):
                continue
            if not (isinstance(func.value, ast.Name) and func.value.id == "breaker"):
                continue
            for inner in ast.walk(node):
                if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute):
                    if inner.func.attr == "create":
                        guarded.append(inner.lineno)
        assert guarded, "the Anthropic messages.create call must be wrapped in breaker.call(...)"


class TestGateOnTheRealTree:
    """The gate's verdict on the repository as it actually stands."""

    def test_the_repository_passes(self, gate):
        """Executed from the stored gate file against the real tree."""
        assert gate.main([]) == 0

    def test_exactly_one_documented_exception_is_declared(self, gate):
        """AC 3 as an enforced property rather than a claim."""
        assert len(gate.DOCUMENTED_EXCEPTIONS) == gate.MAX_DOCUMENTED_EXCEPTIONS == 1

    def test_the_declared_exception_is_reached_by_the_scan(self, gate):
        """An exemption for a site the scan cannot see would exempt nothing."""
        files = list(gate.iter_python_files(REPO_ROOT, gate.SCAN_SCOPE))
        sites, _unreadable = gate.scan(files, REPO_ROOT)
        exempted = [site for site in sites if site.exception_key() in gate.DOCUMENTED_EXCEPTIONS]
        assert len(exempted) == 1, "the documented exception must correspond to exactly one scanned site"
        assert exempted[0].path == "langgraph_engine/llm_call.py"

    def test_the_named_adr_016_sites_no_longer_carry_a_fixed_timeout(self, gate):
        """ADR-016's own enumeration of 6 application sites, re-checked against the tree."""
        named = (
            "langgraph_engine/sdlc_pipeline/architecture/prompt_gen_expert_caller.py",
            "langgraph_engine/sdlc_pipeline/architecture/todo_decomposer.py",
            "langgraph_engine/sdlc_pipeline/architecture/orchestrator_agent_caller.py",
            "langgraph_engine/sdlc_pipeline/architecture/todo_executor.py",
            "langgraph_engine/sdlc_pipeline/nodes/task_orchestration.py",
        )
        files = [REPO_ROOT / path for path in named]
        sites, unreadable = gate.scan(files, REPO_ROOT)
        assert unreadable == []
        assert [site.record() for site in sites if site.value_class in gate.FAILING_VALUE_CLASSES] == []

    def test_no_pipeline_module_still_names_a_retired_timeout_variable(self):
        """The retired env vars must be gone from the modules that used to read them.

        Asserted structurally over string CONSTANTS, not over raw text, so a
        docstring recording the history of the change is not a violation of it.
        """
        retired = {
            "STEP1_PROMPT_GEN_TIMEOUT",
            "STEP1_TODO_DECOMPOSER_TIMEOUT",
            "STEP1_ORCHESTRATOR_TIMEOUT",
            "STEP0_TODO_EXEC_TIMEOUT",
            "FAITHFULNESS_GATE_TIMEOUT",
            "STEP10_LLM_TIMEOUT",
        }
        roots = (
            REPO_ROOT / "langgraph_engine" / "sdlc_pipeline" / "architecture",
            REPO_ROOT / "langgraph_engine" / "sdlc_pipeline" / "nodes",
        )
        offenders = []
        for root in roots:
            for path in sorted(root.rglob("*.py")):
                if "__pycache__" in path.parts:
                    continue
                tree = ast.parse(path.read_text(encoding="utf-8"))
                docstrings = set()
                for owner in ast.walk(tree):
                    body = getattr(owner, "body", None)
                    if isinstance(owner, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and body:
                        first = body[0]
                        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                            docstrings.add(id(first.value))
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                        continue
                    if id(node) in docstrings:
                        continue
                    if node.value in retired:
                        offenders.append("{}:{}:{}".format(path.name, node.lineno, node.value))
        assert offenders == [], "retired timeout variables still read as code: {}".format(offenders)


# ---------------------------------------------------------------------------
# Mutation -- prove this suite rejects a scanner that reports nothing
# ---------------------------------------------------------------------------


class TestMutation:
    """A check that cannot detect its own defeat is not evidence."""

    def test_a_scanner_that_reports_zero_is_rejected(self, tmp_path):
        """Replace the detector with one that finds nothing; the negative test must fail."""
        mutant = load_gate()
        mutant.analyse_source = lambda source, display_path: []

        _write(tmp_path, PIPELINE_FIXTURE, "import subprocess\n\n\ndef go():\n    subprocess.run(['x'], timeout=60)\n")

        honest = load_gate()
        assert honest.main(["--root", str(tmp_path)]) == 1, "the honest gate must reject the planted violation"
        assert mutant.main(["--root", str(tmp_path)]) == 0, "the mutant reports zero, as constructed"

        with pytest.raises(AssertionError):
            assert mutant.main(["--root", str(tmp_path)]) == 1

    def test_a_classifier_that_calls_everything_unbounded_is_rejected(self, tmp_path):
        """Weakening the value classifier rather than the detector must also be caught."""
        mutant = load_gate()
        mutant.classify_value = lambda value, facts, enclosing, depth=0: (mutant.VALUE_UNBOUNDED, "mutated")

        _write(tmp_path, PIPELINE_FIXTURE, "import subprocess\n\n\ndef go():\n    subprocess.run(['x'], timeout=60)\n")

        assert mutant.main(["--root", str(tmp_path)]) == 0
        with pytest.raises(AssertionError):
            assert mutant.main(["--root", str(tmp_path)]) == 1

    def test_the_gate_runs_as_a_process_from_its_stored_file(self):
        """Executed as a subprocess so nothing in this suite's import state can affect it."""
        completed = subprocess.run(
            [sys.executable, str(GATE_PATH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert "verify_no_fixed_timeouts: PASSED" in completed.stdout
