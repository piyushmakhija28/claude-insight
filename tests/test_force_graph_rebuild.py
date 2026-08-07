"""FORCE_GRAPH_REBUILD must actually bypass the stale flag.

The variable was documented in five files -- CLAUDE.md, ADR-002, the deployment
guide, RUNBOOK_STALE_GRAPH.md and the troubleshooting guide -- and read by no
code at all. RUNBOOK Option B instructs an operator to `export
FORCE_GRAPH_REBUILD=1` while recovering from a stale-graph incident, and that
command did nothing. A wrong default is confusing; a recovery procedure that
silently fails is worse, because it is consulted precisely when something has
already gone wrong.

The scenario ADR-002 names is the one that matters here, and it is the case the
stale flag cannot cover: if `call_graph_stale` is never set -- because the node
that sets it crashed -- the guard cannot fire, and Step 5 reviews an outdated
snapshot in silence. There is no in-state signal for the operator to correct, so
the override has to come from outside the state. Every test below therefore
leaves `call_graph_stale` unset and supplies a usable cached snapshot: without
the override, the cache is what the function returns.

Each assertion is paired with its opposite. "Forced rebuild returns fresh data"
proves nothing on its own, because a function that always rebuilds satisfies it
too -- so the unset and "0" cases assert that the cache is still honoured.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from langgraph_engine.sdlc_pipeline.call_graph_analyzer import refresh_call_graph_if_stale  # noqa: E402

CACHED = {"nodes": ["cached_node"], "call_graph_available": True}
FRESH = {"nodes": ["fresh_node"], "call_graph_available": True}


@pytest.fixture()
def not_stale_state():
    """State with a usable cache and no stale flag -- ADR-002's crash scenario."""
    return {"step4_pre_change_graph": dict(CACHED)}


def _run(state, tmp_path):
    """Call the guard with snapshot_call_graph stubbed, returning (result, mock)."""
    with patch("langgraph_engine.sdlc_pipeline.call_graph_analyzer.snapshot_call_graph") as mock_snap:
        mock_snap.return_value = dict(FRESH)
        result = refresh_call_graph_if_stale(state, str(tmp_path))
    return result, mock_snap


class TestTheOverrideBypassesTheStaleFlag:
    """FORCE_GRAPH_REBUILD=1 rebuilds even when nothing marked the graph stale."""

    def test_forced_rebuild_ignores_a_usable_cache(self, monkeypatch, not_stale_state, tmp_path):
        monkeypatch.setenv("FORCE_GRAPH_REBUILD", "1")
        result, mock_snap = _run(not_stale_state, tmp_path)
        mock_snap.assert_called_once_with(str(tmp_path))
        assert result["nodes"] == ["fresh_node"], "the cache was returned despite the override"


class TestTheOverrideIsOffByDefault:
    """The half that fails if the rebuild became unconditional."""

    def test_unset_returns_the_cached_snapshot(self, monkeypatch, not_stale_state, tmp_path):
        monkeypatch.delenv("FORCE_GRAPH_REBUILD", raising=False)
        result, mock_snap = _run(not_stale_state, tmp_path)
        mock_snap.assert_not_called()
        assert result["nodes"] == ["cached_node"]

    def test_zero_returns_the_cached_snapshot(self, monkeypatch, not_stale_state, tmp_path):
        """Documented default is 0, so 0 must behave exactly like unset."""
        monkeypatch.setenv("FORCE_GRAPH_REBUILD", "0")
        result, mock_snap = _run(not_stale_state, tmp_path)
        mock_snap.assert_not_called()
        assert result["nodes"] == ["cached_node"]

    def test_only_the_literal_1_enables_it(self, monkeypatch, not_stale_state, tmp_path):
        """Matches the ENABLE_* convention used across the engine: == "1", not truthiness.

        "true" is the value an operator is most likely to reach for by habit, so
        it is worth pinning that it does NOT enable the override rather than
        leaving the reader to infer it from the comparison.
        """
        monkeypatch.setenv("FORCE_GRAPH_REBUILD", "true")
        result, mock_snap = _run(not_stale_state, tmp_path)
        mock_snap.assert_not_called()
        assert result["nodes"] == ["cached_node"]


class TestTheOverrideDoesNotDisableTheStaleFlag:
    """Setting it to 0 must not switch off ordinary stale-based rebuilding.

    RUNBOOK Option A used to read as though `FORCE_GRAPH_REBUILD=0` turned that
    off and unsetting it turned it back on. It never did, and this pins that the
    two paths are independent so the corrected wording cannot silently drift
    back.
    """

    def test_stale_still_rebuilds_when_the_override_is_zero(self, monkeypatch, tmp_path):
        monkeypatch.setenv("FORCE_GRAPH_REBUILD", "0")
        state = {"call_graph_stale": True, "step4_pre_change_graph": dict(CACHED)}
        result, mock_snap = _run(state, tmp_path)
        mock_snap.assert_called_once_with(str(tmp_path))
        assert result["nodes"] == ["fresh_node"]
