"""Tests for restoring a measurement from JSON and combining two phases.

A genuinely cold phase can only be observed at the very start of a fresh session,
so cold and warm are necessarily two separate invocations. Reporting them together
needs a measurement to survive JSON -- which nothing provided.

The danger in adding it is drift: if a restored measurement computed its verdict
from a second copy of the ladder, that copy would be free to disagree with the
live one, and the direction it would drift is toward PASS, because that branch has
the fewest conditions. So the tests that matter here are the ones asserting the
two paths agree, and the ones asserting that missing evidence raises rather than
defaulting to zero.
"""

import json
import os
import sys

import pytest

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from nfr1 import harness  # noqa: E402

pytestmark = pytest.mark.unit


def phase_payload(phase, tool_calls=10, crossed=False, plugin=0, unknown=0, proved=0):
    """Build a measurement payload of the shape Measurement.to_dict() produces."""
    return {
        "phase": phase,
        "tool_calls_recorded": tool_calls,
        "tool_calls_required": harness.REQUIRED_TOOL_CALLS,
        "turn_boundary": {"crossed": crossed, "witnesses": [], "effect": ""},
        "union_delta": {
            "observed_process_count": plugin + unknown + proved,
            "plugin_attributable_count": plugin,
            "unattributed_count": unknown,
            "not_plugin_descended_count": proved,
        },
    }


class TestARestoredMeasurementAgreesWithTheLiveOne:
    """The whole point: JSON must not change the answer."""

    @pytest.mark.parametrize(
        "kwargs,expected",
        [
            ({}, harness.VERDICT_PASS),
            ({"plugin": 1}, harness.VERDICT_FAIL),
            ({"unknown": 3}, harness.VERDICT_INDETERMINATE),
            ({"crossed": True}, harness.VERDICT_INDETERMINATE),
            ({"tool_calls": 9}, harness.VERDICT_INDETERMINATE),
        ],
    )
    def test_each_verdict_survives_the_round_trip(self, kwargs, expected):
        restored = harness.measurement_from_dict(phase_payload(harness.PHASE_WARM, **kwargs))
        verdict, _ = restored.verdict()
        assert verdict == expected

    def test_the_restored_verdict_matches_compute_verdict_exactly(self):
        """Both paths must call the same function, not two copies of one ladder."""
        payload = phase_payload(harness.PHASE_WARM, unknown=4, proved=2)
        restored = harness.measurement_from_dict(payload)
        direct = harness.compute_verdict(
            crossed=False, tool_calls=10, plugin_count=0, unattributed_count=4, not_plugin_descended_count=2
        )
        assert restored.verdict() == direct

    def test_the_reasons_survive_too_not_just_the_verdict(self):
        restored = harness.measurement_from_dict(phase_payload(harness.PHASE_WARM, plugin=2))
        _, reasons = restored.verdict()
        assert "2 process(es) attributable to the plugin" in reasons[0]


class TestRestoringRefusesToInventEvidence:
    """A missing count must raise. Defaulting it to zero would manufacture a pass."""

    @pytest.mark.parametrize("key", ["phase", "tool_calls_recorded", "turn_boundary", "union_delta"])
    def test_a_missing_top_level_key_raises(self, key):
        payload = phase_payload(harness.PHASE_WARM)
        del payload[key]
        with pytest.raises(ValueError):
            harness.measurement_from_dict(payload)

    @pytest.mark.parametrize("key", ["plugin_attributable_count", "unattributed_count", "not_plugin_descended_count"])
    def test_a_missing_union_count_raises(self, key):
        payload = phase_payload(harness.PHASE_WARM)
        del payload["union_delta"][key]
        with pytest.raises(ValueError):
            harness.measurement_from_dict(payload)

    def test_an_unknown_phase_raises(self):
        with pytest.raises(ValueError):
            harness.measurement_from_dict(phase_payload("lukewarm"))

    def test_a_complete_payload_does_not_raise(self):
        """Specificity: the guard must not reject everything."""
        assert harness.measurement_from_dict(phase_payload(harness.PHASE_COLD)) is not None

    def test_a_restored_payload_is_flagged_as_restored(self):
        restored = harness.measurement_from_dict(phase_payload(harness.PHASE_WARM))
        assert restored.to_dict()["restored_from_json"] is True


class TestCombiningTwoPhases:
    """Cold and warm are reported as two numbers, and both must be present."""

    def _write(self, tmp_path, name, payload):
        path = tmp_path / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def test_two_clean_phases_produce_a_report_carrying_both(self, tmp_path):
        from nfr1 import cli

        cold = self._write(tmp_path, "cold.json", phase_payload(harness.PHASE_COLD))
        warm = self._write(tmp_path, "warm.json", phase_payload(harness.PHASE_WARM))
        report = cli.build_combined_report(cold, warm, None)
        assert report["cold"]["phase"] == harness.PHASE_COLD
        assert report["warm"]["phase"] == harness.PHASE_WARM

    def test_a_failing_phase_fails_the_whole_report(self, tmp_path):
        from nfr1 import cli

        cold = self._write(tmp_path, "cold.json", phase_payload(harness.PHASE_COLD, plugin=1))
        warm = self._write(tmp_path, "warm.json", phase_payload(harness.PHASE_WARM))
        report = cli.build_combined_report(cold, warm, None)
        assert report["verdict"] == harness.VERDICT_FAIL

    def test_the_phases_cannot_be_supplied_the_wrong_way_round(self, tmp_path):
        """Swapping them would silently label a warm count as cold."""
        from nfr1 import cli

        cold = self._write(tmp_path, "cold.json", phase_payload(harness.PHASE_WARM))
        warm = self._write(tmp_path, "warm.json", phase_payload(harness.PHASE_COLD))
        with pytest.raises(ValueError):
            cli.build_combined_report(cold, warm, None)

    def test_no_combined_figure_is_exposed(self, tmp_path):
        """Cold-start benchmarking is a named anti-pattern; a blend describes neither."""
        from nfr1 import cli

        cold = self._write(tmp_path, "cold.json", phase_payload(harness.PHASE_COLD))
        warm = self._write(tmp_path, "warm.json", phase_payload(harness.PHASE_WARM))
        report = cli.build_combined_report(cold, warm, None)
        for key in report:
            assert "average" not in key.lower()
            assert "combined" not in key.lower() or key == "blending_policy"

    def test_a_report_missing_a_phase_is_indeterminate(self):
        """The paired negative: build_report must refuse a single-phase verdict."""
        warm = harness.measurement_from_dict(phase_payload(harness.PHASE_WARM))
        report = harness.build_report(plugin_root=None, cold=None, warm=warm)
        verdict, reasons = report.overall_verdict()
        assert verdict != harness.VERDICT_PASS
        assert any("cold" in r for r in reasons)
