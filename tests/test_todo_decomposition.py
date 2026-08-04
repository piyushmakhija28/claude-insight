"""Tests for the TODO-decomposition enhancement.

Covers:
  - todo_decomposer: _parse_args, _extract_todo_list, _load_prompt_file, _build_decompose_prompt
  - todo_executor: _load_checkpoint, _save_checkpoint, execute_todo_list
  - FlowState new fields: todo_list, todo_results, completed_todos, current_todo_index
  - task_orchestration: import smoke test for step1_task_analysis_node
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path for all imports
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from langgraph_engine.sdlc_pipeline.architecture.todo_decomposer import (  # noqa: E402
    _build_decompose_prompt,
    _extract_todo_list,
    _load_prompt_file,
    _parse_args,
)
from langgraph_engine.sdlc_pipeline.architecture.todo_executor import (  # noqa: E402
    _load_checkpoint,
    _save_checkpoint,
    execute_todo_list,
)

# ===========================================================================
# Group 1: todo_decomposer._parse_args
# ===========================================================================


class TestParseArgs:
    """Unit tests for _parse_args argument parsing."""

    def test_parse_args_defaults(self):
        result = _parse_args(["script_name"])
        assert result["orchestration_prompt_file"] == ""
        assert result["complexity_score"] == 5

    def test_parse_args_space_form(self):
        argv = ["x", "--orchestration-prompt-file", "/tmp/f.txt", "--complexity-score", "15"]
        result = _parse_args(argv)
        assert result["orchestration_prompt_file"] == "/tmp/f.txt"
        assert result["complexity_score"] == 15

    def test_parse_args_equals_form(self):
        argv = ["x", "--complexity-score=20"]
        result = _parse_args(argv)
        assert result["complexity_score"] == 20

    def test_parse_args_invalid_complexity(self):
        argv = ["x", "--complexity-score", "abc"]
        result = _parse_args(argv)
        assert result["complexity_score"] == 5


# ===========================================================================
# Group 2: todo_decomposer._extract_todo_list
# ===========================================================================


class TestExtractTodoList:
    """Unit tests for _extract_todo_list JSON extraction logic."""

    def test_extract_valid_json(self):
        response = json.dumps({"todo_list": [{"id": "todo_001", "title": "do something"}]})
        todo_list, error = _extract_todo_list(response)
        assert error is None
        assert isinstance(todo_list, list)
        assert len(todo_list) == 1
        assert todo_list[0]["id"] == "todo_001"

    def test_extract_no_todo_list_key(self):
        """When the JSON is valid but has no 'todo_list' key, the function
        returns an empty list.  The implementation falls through to the
        'No todo_list found' branch only when the key is absent AND the
        default empty list is returned from parsed.get(); verify both the
        empty list and that parsing did not raise.

        Actual behavior: parsed.get('todo_list', []) returns [] and
        isinstance([], list) is True so the function returns ([], None).
        The test asserts the observable contract rather than an internal
        error message.
        """
        response = json.dumps({"other": []})
        todo_list, error = _extract_todo_list(response)
        assert todo_list == []
        # error is None because an empty list IS a valid (empty) list
        assert error is None

    def test_extract_invalid_json(self):
        response = "this is not json {{{"
        todo_list, error = _extract_todo_list(response)
        assert todo_list == []
        assert error is not None

    def test_extract_empty_response(self):
        todo_list, error = _extract_todo_list("")
        assert todo_list == []
        assert error is not None

    def test_extract_json_embedded_in_text(self):
        preamble = "Here is the decomposed list as requested:\n\n"
        embedded = json.dumps({"todo_list": [{"id": "todo_001", "title": "task one"}]})
        response = preamble + embedded + "\n\nLet me know if you need changes."
        todo_list, error = _extract_todo_list(response)
        assert isinstance(todo_list, list)
        assert len(todo_list) == 1
        assert todo_list[0]["id"] == "todo_001"


# ===========================================================================
# Group 3: todo_decomposer._load_prompt_file
# ===========================================================================


class TestLoadPromptFile:
    """Unit tests for _load_prompt_file file reading logic."""

    def test_load_prompt_file_missing(self, tmp_path):
        non_existent = str(tmp_path / "does_not_exist.txt")
        text, error = _load_prompt_file(non_existent)
        assert text is None
        assert error is not None

    def test_load_prompt_file_empty_path(self):
        text, error = _load_prompt_file("")
        assert text is None
        assert error is not None

    def test_load_prompt_file_ok(self, tmp_path):
        content = "This is the orchestration prompt content."
        prompt_file = tmp_path / "prompt.txt"
        prompt_file.write_text(content, encoding="utf-8")
        text, error = _load_prompt_file(str(prompt_file))
        assert error is None
        assert text == content


# ===========================================================================
# Group 4: todo_decomposer._build_decompose_prompt
# ===========================================================================


class TestBuildDecomposePrompt:
    """Unit tests for _build_decompose_prompt template filling."""

    def test_build_prompt_contains_complexity(self):
        prompt = _build_decompose_prompt("some orchestration text", 18)
        assert "18" in prompt

    def test_build_prompt_contains_orchestration_text(self):
        orchestration_text = "UNIQUE_ORCHESTRATION_CONTENT_XYZ"
        prompt = _build_decompose_prompt(orchestration_text, 5)
        assert orchestration_text in prompt


# ===========================================================================
# Group 5: todo_executor._load_checkpoint
# ===========================================================================


class TestLoadCheckpoint:
    """Unit tests for _load_checkpoint reading sidecar checkpoint files."""

    def test_load_checkpoint_missing_file(self, tmp_path):
        non_existent = str(tmp_path / "no_checkpoint.json")
        completed_ids, results = _load_checkpoint(non_existent)
        assert completed_ids == set()
        assert results == {}

    def test_load_checkpoint_valid(self, tmp_path):
        checkpoint_path = tmp_path / "todo_checkpoint.json"
        data = {
            "completed_ids": ["todo_001", "todo_002"],
            "results": {"todo_001": {"status": "SUCCESS"}, "todo_002": {"status": "SUCCESS"}},
        }
        checkpoint_path.write_text(json.dumps(data), encoding="utf-8")
        completed_ids, results = _load_checkpoint(str(checkpoint_path))
        assert completed_ids == {"todo_001", "todo_002"}
        assert "todo_001" in results
        assert results["todo_002"]["status"] == "SUCCESS"

    def test_load_checkpoint_corrupt_json(self, tmp_path):
        checkpoint_path = tmp_path / "corrupt_checkpoint.json"
        checkpoint_path.write_text("not valid json {{{", encoding="utf-8")
        completed_ids, results = _load_checkpoint(str(checkpoint_path))
        assert completed_ids == set()
        assert results == {}


# ===========================================================================
# Group 6: todo_executor._save_checkpoint
# ===========================================================================


class TestSaveCheckpoint:
    """Unit tests for _save_checkpoint writing sidecar checkpoint files."""

    def test_save_checkpoint_creates_file(self, tmp_path):
        checkpoint_path = tmp_path / "subdir" / "todo_checkpoint.json"
        completed = {"todo_001", "todo_002"}
        results = {"todo_001": {"status": "SUCCESS"}, "todo_002": {"status": "SUCCESS"}}
        _save_checkpoint(str(checkpoint_path), completed, results)
        assert checkpoint_path.exists()
        loaded = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        assert set(loaded["completed_ids"]) == completed
        assert loaded["results"] == results

    def test_save_checkpoint_bad_path(self):
        bad_path = "/nonexistent_root_dir_that_cannot_exist/subdir/checkpoint.json"
        completed = {"todo_001"}
        results = {}
        _save_checkpoint(bad_path, completed, results)


# ===========================================================================
# Group 7: todo_executor.execute_todo_list (mock subprocess)
# ===========================================================================


class TestExecuteTodoList:
    """Integration-style tests for execute_todo_list with mocked subprocess."""

    _FAKE_SUCCESS_STDOUT = json.dumps({"llm_response": "agent output here"})

    def _make_state(self, tmp_path):
        return {"session_dir": str(tmp_path), "project_root": str(tmp_path)}

    def _make_proc(self, returncode=0, stdout="", stderr=""):
        proc = MagicMock()
        proc.returncode = returncode
        proc.stdout = stdout
        proc.stderr = stderr
        return proc

    def test_execute_empty_list(self, tmp_path):
        state = self._make_state(tmp_path)
        results = execute_todo_list(state, [])
        assert results == []

    def test_execute_skips_completed(self, tmp_path):
        checkpoint_path = tmp_path / "todo_checkpoint.json"
        data = {
            "completed_ids": ["todo_001"],
            "results": {"todo_001": {"status": "SUCCESS", "llm_response": "cached"}},
        }
        checkpoint_path.write_text(json.dumps(data), encoding="utf-8")

        state = self._make_state(tmp_path)
        todo_list = [{"id": "todo_001", "prompt": "do something"}]

        with patch("langgraph_engine.sdlc_pipeline.architecture.todo_executor.run_supervised") as mock_run:
            results = execute_todo_list(state, todo_list)

        mock_run.assert_not_called()
        assert len(results) == 1
        assert results[0]["status"] == "SKIPPED"
        assert results[0]["todo_id"] == "todo_001"

    def test_execute_single_todo_success(self, tmp_path):
        state = self._make_state(tmp_path)
        todo_list = [{"id": "todo_002", "prompt": "implement feature X"}]

        fake_proc = self._make_proc(returncode=0, stdout=self._FAKE_SUCCESS_STDOUT)

        with patch(
            "langgraph_engine.sdlc_pipeline.architecture.todo_executor.run_supervised",
            return_value=fake_proc,
        ):
            results = execute_todo_list(state, todo_list)

        assert len(results) == 1
        assert results[0]["status"] == "SUCCESS"
        assert results[0]["todo_id"] == "todo_002"

    def test_execute_single_todo_failure(self, tmp_path):
        state = self._make_state(tmp_path)
        todo_list = [{"id": "todo_003", "prompt": "implement feature Y"}]

        fake_proc = self._make_proc(returncode=1, stdout="", stderr="some error message")

        with patch(
            "langgraph_engine.sdlc_pipeline.architecture.todo_executor.run_supervised",
            return_value=fake_proc,
        ):
            results = execute_todo_list(state, todo_list)

        assert len(results) == 1
        assert results[0]["status"] == "FAILED"
        assert results[0]["todo_id"] == "todo_003"

    def test_execute_never_raises(self, tmp_path):
        state = self._make_state(tmp_path)
        todo_list = [{"id": "todo_004", "prompt": "do something dangerous"}]

        with patch(
            "langgraph_engine.sdlc_pipeline.architecture.todo_executor.run_supervised",
            side_effect=RuntimeError("unexpected subprocess failure"),
        ):
            results = execute_todo_list(state, todo_list)

        assert len(results) == 1
        assert results[0]["status"] == "FAILED"
        assert results[0]["todo_id"] == "todo_004"

    def test_execute_updates_checkpoint(self, tmp_path):
        state = self._make_state(tmp_path)
        todo_list = [{"id": "todo_005", "prompt": "build the feature"}]

        fake_proc = self._make_proc(returncode=0, stdout=self._FAKE_SUCCESS_STDOUT)

        with patch(
            "langgraph_engine.sdlc_pipeline.architecture.todo_executor.run_supervised",
            return_value=fake_proc,
        ):
            execute_todo_list(state, todo_list)

        checkpoint_path = tmp_path / "todo_checkpoint.json"
        assert checkpoint_path.exists()
        data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        assert "todo_005" in data["completed_ids"]


# ===========================================================================
# Group 8: state_definition regression
# ===========================================================================


class TestStateDefinitionRegression:
    """Regression tests ensuring new FlowState fields are accepted."""

    def test_state_fields_exist(self):
        from langgraph_engine.state.state_definition import FlowState

        state: FlowState = {}
        state["todo_list"] = [{"id": "todo_001"}]
        state["todo_results"] = [{"status": "SUCCESS", "todo_id": "todo_001"}]
        state["completed_todos"] = ["todo_001"]
        state["current_todo_index"] = 0

        assert state.get("todo_list") == [{"id": "todo_001"}]
        assert state.get("todo_results") is not None
        assert state.get("completed_todos") == ["todo_001"]
        assert state.get("current_todo_index") == 0


# ===========================================================================
# Group 9: task_orchestration smoke (import only)
# ===========================================================================


class TestStepWrappersSmoke:
    """Import smoke test ensuring step1_task_analysis_node is importable."""

    def test_step1_imports(self):
        from langgraph_engine.sdlc_pipeline.nodes.task_orchestration import step1_task_analysis_node

        assert callable(step1_task_analysis_node)
