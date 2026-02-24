#!/usr/bin/env python3
"""
Test Suite: test_stop_notifier.py
Target: stop-notifier.py v3.2.0
Author: qa-testing-agent
Date: 2026-02-24

Coverage:
  - Unit Tests: read_flag, delete_flag, increment_retry,
                get_session_start_default, get_work_done_default
  - Integration Tests: full flag-to-speak flow, retry flow,
                       max retries, work-done priority
  - Mock Tests: LLM timeout simulation, success/failure responses,
                model fallback chain
  - Logging Tests: error messages, retry counters, model attempts,
                   timeout handling

Windows-Safe: ASCII only (no Unicode/emojis)
"""

import sys
import os
import json
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Bootstrap: load stop-notifier.py as a module and register in sys.modules
# so that patch('stop_notifier.X') works correctly.
# ---------------------------------------------------------------------------
_SCRIPT_PATH = Path(__file__).parent / 'stop-notifier.py'

import importlib.util
_spec = importlib.util.spec_from_file_location('stop_notifier', str(_SCRIPT_PATH))
_mod = importlib.util.module_from_spec(_spec)
# Register BEFORE exec so internal imports land on the right object
sys.modules['stop_notifier'] = _mod
_mod.__name__ = 'stop_notifier'
_spec.loader.exec_module(_mod)

# Convenience aliases
read_flag = _mod.read_flag
delete_flag = _mod.delete_flag
increment_retry = _mod.increment_retry
get_session_start_default = _mod.get_session_start_default
get_task_complete_default = _mod.get_task_complete_default
get_work_done_default = _mod.get_work_done_default
generate_dynamic_message = _mod.generate_dynamic_message
speak = _mod.speak
log_s = _mod.log_s
STOP_LOG = _mod.STOP_LOG


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tmp_flag(tmp_dir, filename, content='hello context'):
    """Create a plain-text flag file and return its Path."""
    p = Path(tmp_dir) / filename
    p.write_text(content, encoding='utf-8')
    return p


def _tmp_json_flag(tmp_dir, filename, data):
    """Create a JSON flag file and return its Path."""
    p = Path(tmp_dir) / filename
    p.write_text(json.dumps(data), encoding='utf-8')
    return p


def _good_http_mock(content_str):
    """Return a context-manager-compatible mock that returns content_str."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = content_str.encode('utf-8')
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def _llm_json(message_text):
    """Build a minimal OpenRouter-compatible JSON response payload."""
    return json.dumps({
        'choices': [{'message': {'content': message_text}}]
    })


# ===========================================================================
# SECTION 1: UNIT TESTS
# ===========================================================================

class TestReadFlag(unittest.TestCase):
    """Unit tests for read_flag()."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_reads_existing_file_content(self):
        p = _tmp_flag(self.tmp, '.session-start-voice', 'Good morning context')
        result = read_flag(p)
        self.assertEqual(result, 'Good morning context')

    def test_returns_empty_string_when_file_missing(self):
        p = Path(self.tmp) / '.nonexistent-flag'
        result = read_flag(p)
        self.assertEqual(result, '')

    def test_strips_whitespace(self):
        p = _tmp_flag(self.tmp, '.flag', '  context with spaces  \n')
        result = read_flag(p)
        self.assertEqual(result, 'context with spaces')

    def test_does_NOT_delete_flag_after_read(self):
        """read_flag must be non-destructive - file must still exist after call."""
        p = _tmp_flag(self.tmp, '.session-start-voice', 'context')
        read_flag(p)
        self.assertTrue(p.exists(), 'read_flag() must not delete the flag file')

    def test_empty_file_returns_empty_string(self):
        p = Path(self.tmp) / '.flag'
        p.write_text('', encoding='utf-8')
        result = read_flag(p)
        self.assertEqual(result, '')

    def test_plain_ascii_content_preserved(self):
        p = _tmp_flag(self.tmp, '.flag', 'Session with plain details')
        result = read_flag(p)
        self.assertEqual(result, 'Session with plain details')


class TestDeleteFlag(unittest.TestCase):
    """Unit tests for delete_flag()."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_deletes_existing_flag(self):
        p = _tmp_flag(self.tmp, '.session-start-voice', 'context')
        delete_flag(p)
        self.assertFalse(p.exists(), 'Flag must be deleted after delete_flag()')

    def test_does_not_raise_when_flag_missing(self):
        """delete_flag on a non-existent path must be a no-op."""
        p = Path(self.tmp) / '.nonexistent'
        try:
            delete_flag(p)
        except Exception as exc:
            self.fail(f'delete_flag raised on missing file: {exc}')

    def test_idempotent_second_call(self):
        """Calling delete_flag twice on same path must not raise."""
        p = _tmp_flag(self.tmp, '.flag', 'ctx')
        delete_flag(p)
        try:
            delete_flag(p)
        except Exception as exc:
            self.fail(f'Second delete_flag call raised: {exc}')


class TestIncrementRetry(unittest.TestCase):
    """Unit tests for increment_retry()."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_first_retry_on_plain_text_flag_returns_true(self):
        """
        Plain-text flag (no .json suffix): treated as retries=0 -> incremented
        to 1, returns True.
        Note: the function reads JSON only when suffix=='.json'.
        Plain files get a fresh dict({'retries': 0}).
        """
        p = _tmp_flag(self.tmp, '.session-start-voice', 'plain context')
        result = increment_retry(p)
        self.assertTrue(result, 'First retry should return True (still has retries)')

    def test_retry_counter_written_to_file(self):
        """After increment on a plain flag, file must contain JSON with retries=1."""
        p = _tmp_flag(self.tmp, '.flag', 'context')
        increment_retry(p)
        data = json.loads(p.read_text(encoding='utf-8'))
        self.assertEqual(data.get('retries'), 1)

    def test_second_retry_returns_true(self):
        p = _tmp_json_flag(self.tmp, '.flag.json', {'content': 'ctx', 'retries': 1})
        result = increment_retry(p)
        self.assertTrue(result)

    def test_third_retry_returns_true(self):
        """retries=2 -> 3, still below max, returns True."""
        p = _tmp_json_flag(self.tmp, '.flag.json', {'content': 'ctx', 'retries': 2})
        result = increment_retry(p)
        self.assertTrue(result)

    def test_max_retries_exceeded_returns_false(self):
        """When retries is already 3, next call must return False."""
        p = _tmp_json_flag(self.tmp, '.flag.json', {'content': 'ctx', 'retries': 3})
        result = increment_retry(p)
        self.assertFalse(result, 'Max retries (3) exceeded -> must return False')

    def test_non_json_suffix_handled_as_plain(self):
        """Files without .json suffix treated as plain text; retries field added."""
        p = _tmp_flag(self.tmp, '.session-start-voice', 'session context')
        increment_retry(p)
        content = p.read_text(encoding='utf-8')
        data = json.loads(content)
        self.assertIn('retries', data)
        self.assertEqual(data['retries'], 1)

    def test_missing_file_returns_false(self):
        """
        increment_retry on a missing file:
        - For .json suffix: flag_path.read_text() raises FileNotFoundError
          -> caught by except -> returns False
        - For non-.json suffix: dict initialized from scratch (retries=0 -> 1)
          -> write_text raises FileNotFoundError on missing dir? No - the parent
          dir exists (tmp_dir exists but we chose a ghost filename in tmp).

        Use a ghost JSON file so the read path throws.
        """
        p = Path(self.tmp) / 'ghost.json'
        result = increment_retry(p)
        self.assertFalse(result, 'Missing .json flag -> read fails -> return False')


class TestGetSessionStartDefault(unittest.TestCase):
    """Unit tests for get_session_start_default() fallback messages."""

    def test_morning_greeting(self):
        """hour < 12 -> 'Good morning'"""
        with patch.object(_mod, 'datetime') as mock_dt:
            mock_dt.now.return_value = MagicMock(hour=9)
            msg = get_session_start_default()
        self.assertIn('Good morning', msg)
        self.assertIn('Sir', msg)

    def test_afternoon_greeting(self):
        """12 <= hour < 17 -> 'Good afternoon'"""
        with patch.object(_mod, 'datetime') as mock_dt:
            mock_dt.now.return_value = MagicMock(hour=14)
            msg = get_session_start_default()
        self.assertIn('Good afternoon', msg)

    def test_evening_greeting(self):
        """hour >= 17 -> 'Good evening'"""
        with patch.object(_mod, 'datetime') as mock_dt:
            mock_dt.now.return_value = MagicMock(hour=20)
            msg = get_session_start_default()
        self.assertIn('Good evening', msg)

    def test_boundary_noon_is_afternoon(self):
        """hour=12 should be 'Good afternoon', not morning."""
        with patch.object(_mod, 'datetime') as mock_dt:
            mock_dt.now.return_value = MagicMock(hour=12)
            msg = get_session_start_default()
        self.assertIn('Good afternoon', msg)

    def test_boundary_17_is_evening(self):
        """hour=17 should be 'Good evening', not afternoon."""
        with patch.object(_mod, 'datetime') as mock_dt:
            mock_dt.now.return_value = MagicMock(hour=17)
            msg = get_session_start_default()
        self.assertIn('Good evening', msg)

    def test_returns_non_empty_string(self):
        msg = get_session_start_default()
        self.assertIsInstance(msg, str)
        self.assertGreater(len(msg.strip()), 0)

    def test_mentions_session_started(self):
        msg = get_session_start_default()
        self.assertIn('session started', msg.lower())

    def test_mentions_ready(self):
        msg = get_session_start_default()
        self.assertIn('ready', msg.lower())


class TestGetWorkDoneDefault(unittest.TestCase):
    """Unit tests for get_work_done_default() fallback messages."""

    def test_returns_string(self):
        msg = get_work_done_default()
        self.assertIsInstance(msg, str)

    def test_contains_sir(self):
        msg = get_work_done_default()
        self.assertIn('Sir', msg)

    def test_mentions_completion(self):
        msg = get_work_done_default()
        msg_lower = msg.lower()
        self.assertTrue(
            'complet' in msg_lower or 'done' in msg_lower,
            f'Expected completion keyword in: {msg}'
        )

    def test_non_empty(self):
        msg = get_work_done_default()
        self.assertGreater(len(msg.strip()), 10)


class TestGetTaskCompleteDefault(unittest.TestCase):
    """Unit tests for get_task_complete_default() fallback."""

    def test_returns_string_with_sir(self):
        msg = get_task_complete_default()
        self.assertIsInstance(msg, str)
        self.assertIn('Sir', msg)

    def test_mentions_task(self):
        msg = get_task_complete_default()
        self.assertIn('task', msg.lower())


# ===========================================================================
# SECTION 2: INTEGRATION TESTS
# ===========================================================================

class TestCompleteFlow(unittest.TestCase):
    """
    Integration Tests: flag exists -> LLM call -> speak -> delete.
    All external I/O (LLM, speak, delete) is mocked.
    Uses patch.object() which targets the already-loaded module object directly.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _absent(self, name):
        """Return path to a file that does not exist."""
        return Path(self.tmp) / name

    def test_session_start_llm_success_speaks_and_deletes(self):
        """
        Flow: SESSION_START flag exists, LLM returns message ->
              speak() called with LLM message, delete_flag() called once.
        """
        flag = _tmp_flag(self.tmp, '.session-start-voice', 'morning context')

        with patch.object(_mod, 'SESSION_START_FLAG', flag), \
             patch.object(_mod, 'TASK_COMPLETE_FLAG', self._absent('.tc')), \
             patch.object(_mod, 'WORK_DONE_FLAG', self._absent('.wd')), \
             patch.object(_mod, 'generate_dynamic_message', return_value='Sir, ready.') as mock_llm, \
             patch.object(_mod, 'speak') as mock_speak, \
             patch.object(_mod, 'delete_flag') as mock_delete:
            with self.assertRaises(SystemExit):
                _mod.main()

        mock_llm.assert_called_once_with('session_start', 'morning context')
        mock_speak.assert_called_once_with('Sir, ready.')
        mock_delete.assert_called_once_with(flag)

    def test_work_done_llm_success_speaks_and_deletes(self):
        """
        Flow: WORK_DONE flag exists, LLM returns message ->
              speak() called, delete_flag() called.
        """
        flag = _tmp_flag(self.tmp, '.session-work-done', 'All tests passed')

        with patch.object(_mod, 'SESSION_START_FLAG', self._absent('.ss')), \
             patch.object(_mod, 'TASK_COMPLETE_FLAG', self._absent('.tc')), \
             patch.object(_mod, 'WORK_DONE_FLAG', flag), \
             patch.object(_mod, 'generate_dynamic_message', return_value='Sir, all done.') as mock_llm, \
             patch.object(_mod, 'speak') as mock_speak, \
             patch.object(_mod, 'delete_flag') as mock_delete:
            with self.assertRaises(SystemExit):
                _mod.main()

        mock_llm.assert_called_once_with('work_done', 'All tests passed')
        mock_speak.assert_called_once_with('Sir, all done.')
        mock_delete.assert_called_once_with(flag)

    def test_task_complete_flow(self):
        """TASK_COMPLETE flag: successful LLM -> speak and delete."""
        flag = _tmp_flag(self.tmp, '.task-complete-voice', 'task info')

        with patch.object(_mod, 'SESSION_START_FLAG', self._absent('.ss')), \
             patch.object(_mod, 'TASK_COMPLETE_FLAG', flag), \
             patch.object(_mod, 'WORK_DONE_FLAG', self._absent('.wd')), \
             patch.object(_mod, 'generate_dynamic_message', return_value='Sir, task done.') as mock_llm, \
             patch.object(_mod, 'speak') as mock_speak, \
             patch.object(_mod, 'delete_flag') as mock_delete:
            with self.assertRaises(SystemExit):
                _mod.main()

        mock_llm.assert_called_once_with('task_complete', 'task info')
        mock_speak.assert_called_once_with('Sir, task done.')
        mock_delete.assert_called_once_with(flag)

    def test_retry_flow_flag_persists_when_retries_remain(self):
        """
        Flow: LLM fails, increment_retry returns True (retries remain) ->
              speak fallback, delete_flag must NOT be called for this flag.
        """
        flag = _tmp_flag(self.tmp, '.session-start-voice', 'context')

        with patch.object(_mod, 'SESSION_START_FLAG', flag), \
             patch.object(_mod, 'TASK_COMPLETE_FLAG', self._absent('.tc')), \
             patch.object(_mod, 'WORK_DONE_FLAG', self._absent('.wd')), \
             patch.object(_mod, 'generate_dynamic_message', return_value=None), \
             patch.object(_mod, 'increment_retry', return_value=True), \
             patch.object(_mod, 'speak') as mock_speak, \
             patch.object(_mod, 'delete_flag') as mock_delete:
            with self.assertRaises(SystemExit):
                _mod.main()

        mock_speak.assert_called()
        # delete_flag must NOT be called with this flag
        called_with = [c.args[0] for c in mock_delete.call_args_list]
        self.assertNotIn(flag, called_with,
                         'Flag must NOT be deleted when retries remain')

    def test_max_retries_uses_fallback_and_deletes_flag(self):
        """
        Flow: LLM fails, increment_retry returns False (max retries) ->
              speak fallback message, delete flag.
        """
        flag = _tmp_flag(self.tmp, '.session-start-voice', 'ctx')

        with patch.object(_mod, 'SESSION_START_FLAG', flag), \
             patch.object(_mod, 'TASK_COMPLETE_FLAG', self._absent('.tc')), \
             patch.object(_mod, 'WORK_DONE_FLAG', self._absent('.wd')), \
             patch.object(_mod, 'generate_dynamic_message', return_value=None), \
             patch.object(_mod, 'increment_retry', return_value=False), \
             patch.object(_mod, 'speak') as mock_speak, \
             patch.object(_mod, 'delete_flag') as mock_delete:
            with self.assertRaises(SystemExit):
                _mod.main()

        mock_speak.assert_called()
        mock_delete.assert_called_with(flag)

    def test_work_done_max_retries_always_speaks(self):
        """
        CRITICAL: work-done flag must ALWAYS trigger speak even at max retries.
        This is the most important notification in the system.
        """
        flag = _tmp_flag(self.tmp, '.session-work-done', 'all done')

        with patch.object(_mod, 'SESSION_START_FLAG', self._absent('.ss')), \
             patch.object(_mod, 'TASK_COMPLETE_FLAG', self._absent('.tc')), \
             patch.object(_mod, 'WORK_DONE_FLAG', flag), \
             patch.object(_mod, 'generate_dynamic_message', return_value=None), \
             patch.object(_mod, 'increment_retry', return_value=False), \
             patch.object(_mod, 'speak') as mock_speak, \
             patch.object(_mod, 'delete_flag') as mock_delete:
            with self.assertRaises(SystemExit):
                _mod.main()

        self.assertTrue(mock_speak.called,
                        'work-done MUST call speak() even at max retries')
        mock_delete.assert_called_with(flag)

    def test_no_flags_no_speak(self):
        """No flag files present -> speak must never be called."""
        with patch.object(_mod, 'SESSION_START_FLAG', self._absent('.ss')), \
             patch.object(_mod, 'TASK_COMPLETE_FLAG', self._absent('.tc')), \
             patch.object(_mod, 'WORK_DONE_FLAG', self._absent('.wd')), \
             patch.object(_mod, 'speak') as mock_speak, \
             patch.object(_mod, 'generate_dynamic_message') as mock_llm:
            with self.assertRaises(SystemExit):
                _mod.main()

        mock_speak.assert_not_called()
        mock_llm.assert_not_called()

    def test_session_start_retry_uses_context_as_fallback_text(self):
        """When LLM fails and retries remain, speak receives the flag's context text."""
        flag = _tmp_flag(self.tmp, '.session-start-voice', 'My custom context message')

        with patch.object(_mod, 'SESSION_START_FLAG', flag), \
             patch.object(_mod, 'TASK_COMPLETE_FLAG', self._absent('.tc')), \
             patch.object(_mod, 'WORK_DONE_FLAG', self._absent('.wd')), \
             patch.object(_mod, 'generate_dynamic_message', return_value=None), \
             patch.object(_mod, 'increment_retry', return_value=True), \
             patch.object(_mod, 'speak') as mock_speak, \
             patch.object(_mod, 'delete_flag'):
            with self.assertRaises(SystemExit):
                _mod.main()

        mock_speak.assert_called_once_with('My custom context message')


class TestPriorityOrder(unittest.TestCase):
    """All three flags are processed independently when they all exist."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_all_three_flags_processed(self):
        """When all 3 flags exist and LLM succeeds, all 3 must speak and delete."""
        f1 = _tmp_flag(self.tmp, '.session-start-voice', 'ctx1')
        f2 = _tmp_flag(self.tmp, '.task-complete-voice', 'ctx2')
        f3 = _tmp_flag(self.tmp, '.session-work-done', 'ctx3')

        with patch.object(_mod, 'SESSION_START_FLAG', f1), \
             patch.object(_mod, 'TASK_COMPLETE_FLAG', f2), \
             patch.object(_mod, 'WORK_DONE_FLAG', f3), \
             patch.object(_mod, 'generate_dynamic_message', return_value='message'), \
             patch.object(_mod, 'speak') as mock_speak, \
             patch.object(_mod, 'delete_flag') as mock_delete:
            with self.assertRaises(SystemExit):
                _mod.main()

        self.assertEqual(mock_speak.call_count, 3,
                         'All 3 flags must trigger speak')
        self.assertEqual(mock_delete.call_count, 3,
                         'All 3 flags must be deleted on LLM success')

    def test_session_start_llm_call_uses_correct_event_type(self):
        """SESSION_START flag -> generate_dynamic_message called with 'session_start'."""
        flag = _tmp_flag(self.tmp, '.session-start-voice', 'ctx')

        with patch.object(_mod, 'SESSION_START_FLAG', flag), \
             patch.object(_mod, 'TASK_COMPLETE_FLAG', Path(self.tmp) / '.absent'), \
             patch.object(_mod, 'WORK_DONE_FLAG', Path(self.tmp) / '.absent2'), \
             patch.object(_mod, 'generate_dynamic_message', return_value='msg') as mock_llm, \
             patch.object(_mod, 'speak'), \
             patch.object(_mod, 'delete_flag'):
            with self.assertRaises(SystemExit):
                _mod.main()

        self.assertEqual(mock_llm.call_args[0][0], 'session_start')

    def test_work_done_llm_call_uses_correct_event_type(self):
        """WORK_DONE flag -> generate_dynamic_message called with 'work_done'."""
        flag = _tmp_flag(self.tmp, '.session-work-done', 'ctx')

        with patch.object(_mod, 'SESSION_START_FLAG', Path(self.tmp) / '.absent'), \
             patch.object(_mod, 'TASK_COMPLETE_FLAG', Path(self.tmp) / '.absent2'), \
             patch.object(_mod, 'WORK_DONE_FLAG', flag), \
             patch.object(_mod, 'generate_dynamic_message', return_value='msg') as mock_llm, \
             patch.object(_mod, 'speak'), \
             patch.object(_mod, 'delete_flag'):
            with self.assertRaises(SystemExit):
                _mod.main()

        self.assertEqual(mock_llm.call_args[0][0], 'work_done')


# ===========================================================================
# SECTION 3: MOCK TESTS (network / LLM simulation)
# ===========================================================================

class TestGenerateDynamicMessage(unittest.TestCase):
    """
    Mock tests for generate_dynamic_message().
    Tests: timeout simulation, success, failure, model fallback chain,
           15s timeout value verification (v3.2.0 requirement).
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.api_key_file = Path(self.tmp) / 'openrouter-api-key'
        self.api_key_file.write_text('sk-test-fake-key', encoding='utf-8')

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _patch_key(self):
        return patch.object(_mod, 'API_KEY_FILE', self.api_key_file)

    def test_no_api_key_returns_none(self):
        missing = Path(self.tmp) / 'no-key'
        with patch.object(_mod, 'API_KEY_FILE', missing):
            result = generate_dynamic_message('session_start', 'ctx')
        self.assertIsNone(result, 'Without API key must return None')

    def test_successful_llm_response_returned(self):
        """Mock a clean HTTP response -> function returns the message text."""
        resp_mock = _good_http_mock(_llm_json('Good morning Sir. Ready.'))

        with self._patch_key(), \
             patch.object(_mod.urllib_request, 'urlopen', return_value=resp_mock):
            result = generate_dynamic_message('session_start', 'morning')

        self.assertEqual(result, 'Good morning Sir. Ready.')

    def test_strips_surrounding_quotes(self):
        """LLM response wrapped in quotes -> quotes stripped."""
        resp_mock = _good_http_mock(_llm_json('"Sir, session started."'))

        with self._patch_key(), \
             patch.object(_mod.urllib_request, 'urlopen', return_value=resp_mock):
            result = generate_dynamic_message('session_start', '')

        self.assertEqual(result, 'Sir, session started.')

    def test_strips_markdown_asterisks_and_backticks(self):
        """Markdown artifacts must be stripped from the LLM output."""
        resp_mock = _good_http_mock(_llm_json('**Sir**, `session` started.'))

        with self._patch_key(), \
             patch.object(_mod.urllib_request, 'urlopen', return_value=resp_mock):
            result = generate_dynamic_message('work_done', 'summary')

        self.assertNotIn('*', result)
        self.assertNotIn('`', result)

    def test_timeout_simulation_all_models_fail_returns_none(self):
        """
        Simulating URLError (timeout) on all 3 models.
        v3.2.0 uses timeout=15s; the mock still simulates failure.
        Result must be None so caller falls back to static message.
        """
        from urllib.error import URLError

        with self._patch_key(), \
             patch.object(_mod.urllib_request, 'urlopen',
                          side_effect=URLError('timed out')):
            result = generate_dynamic_message('session_start', 'ctx')

        self.assertIsNone(result,
                          'All-models timeout -> must return None for static fallback')

    def test_model_fallback_chain_on_first_model_failure(self):
        """
        First model fails (URLError), second model succeeds.
        Verifies the for-loop model fallback chain in generate_dynamic_message().
        """
        from urllib.error import URLError

        good_resp = _good_http_mock(_llm_json('Sir, fallback model responded.'))
        call_count = [0]

        def side_effect(req, timeout):
            call_count[0] += 1
            if call_count[0] == 1:
                raise URLError('first model network error')
            return good_resp

        with self._patch_key(), \
             patch.object(_mod.urllib_request, 'urlopen', side_effect=side_effect):
            result = generate_dynamic_message('task_complete', 'context')

        self.assertEqual(result, 'Sir, fallback model responded.')
        self.assertEqual(call_count[0], 2, 'Should have tried exactly 2 models')

    def test_all_three_models_fail_returns_none(self):
        """All 3 models fail -> generate_dynamic_message returns None."""
        from urllib.error import URLError

        with self._patch_key(), \
             patch.object(_mod.urllib_request, 'urlopen',
                          side_effect=URLError('all fail')):
            result = generate_dynamic_message('work_done', 'summary')

        self.assertIsNone(result)

    def test_empty_content_response_tries_next_model(self):
        """LLM returns empty content string -> must fall through to next model."""
        empty_resp = _good_http_mock(_llm_json(''))
        good_resp = _good_http_mock(_llm_json('Sir, second model.'))

        call_count = [0]

        def side_effect(req, timeout):
            call_count[0] += 1
            if call_count[0] == 1:
                return empty_resp
            return good_resp

        with self._patch_key(), \
             patch.object(_mod.urllib_request, 'urlopen', side_effect=side_effect):
            result = generate_dynamic_message('session_start', 'ctx')

        self.assertEqual(result, 'Sir, second model.')

    def test_timeout_is_15_seconds_v320(self):
        """
        v3.2.0 CRITICAL: timeout parameter passed to urlopen must be 15.
        Old v3.1.0 used 5s. This test verifies the upgrade.
        """
        from urllib.error import URLError

        observed_timeouts = []

        def capture(req, timeout):
            observed_timeouts.append(timeout)
            raise URLError('forced fail for capture')

        with self._patch_key(), \
             patch.object(_mod.urllib_request, 'urlopen', side_effect=capture):
            generate_dynamic_message('session_start', '')

        self.assertGreater(len(observed_timeouts), 0,
                           'urlopen must have been called at least once')
        for t in observed_timeouts:
            self.assertEqual(t, 15,
                             f'Expected timeout=15s (v3.2.0 requirement), got {t}s')

    def test_mock_success_speaks_and_deletes_end_to_end(self):
        """
        Full path: mock LLM success inside main() -> speak called with
        LLM-returned text, flag deleted.
        """
        flag = _tmp_flag(self.tmp, '.session-work-done', 'done summary')
        resp_mock = _good_http_mock(_llm_json('Sir, everything is complete.'))

        with patch.object(_mod, 'SESSION_START_FLAG', Path(self.tmp) / '.absent'), \
             patch.object(_mod, 'TASK_COMPLETE_FLAG', Path(self.tmp) / '.absent2'), \
             patch.object(_mod, 'WORK_DONE_FLAG', flag), \
             patch.object(_mod, 'API_KEY_FILE', self.api_key_file), \
             patch.object(_mod.urllib_request, 'urlopen', return_value=resp_mock), \
             patch.object(_mod, 'speak') as mock_speak, \
             patch.object(_mod, 'delete_flag') as mock_delete:
            with self.assertRaises(SystemExit):
                _mod.main()

        mock_speak.assert_called_once_with('Sir, everything is complete.')
        mock_delete.assert_called_once_with(flag)

    def test_mock_llm_failure_triggers_fallback_message(self):
        """
        Full path: mock LLM failure (no API key) inside main() ->
        speak called with static fallback, flag deleted after max retries.
        """
        flag = _tmp_flag(self.tmp, '.session-work-done', '')
        no_key = Path(self.tmp) / 'no-key'  # does not exist

        with patch.object(_mod, 'SESSION_START_FLAG', Path(self.tmp) / '.absent'), \
             patch.object(_mod, 'TASK_COMPLETE_FLAG', Path(self.tmp) / '.absent2'), \
             patch.object(_mod, 'WORK_DONE_FLAG', flag), \
             patch.object(_mod, 'API_KEY_FILE', no_key), \
             patch.object(_mod, 'increment_retry', return_value=False), \
             patch.object(_mod, 'speak') as mock_speak, \
             patch.object(_mod, 'delete_flag') as mock_delete:
            with self.assertRaises(SystemExit):
                _mod.main()

        # speak must have been called with the static fallback
        mock_speak.assert_called()
        spoken_text = mock_speak.call_args[0][0]
        self.assertIn('Sir', spoken_text)
        mock_delete.assert_called_with(flag)

    def test_mock_max_retries_speak_receives_default_message(self):
        """
        When context is empty and max retries exceeded, speak must receive
        the output of get_work_done_default() - not an empty string.
        """
        flag = _tmp_flag(self.tmp, '.session-work-done', '')
        no_key = Path(self.tmp) / 'no-key'
        expected_default = get_work_done_default()

        with patch.object(_mod, 'SESSION_START_FLAG', Path(self.tmp) / '.absent'), \
             patch.object(_mod, 'TASK_COMPLETE_FLAG', Path(self.tmp) / '.absent2'), \
             patch.object(_mod, 'WORK_DONE_FLAG', flag), \
             patch.object(_mod, 'API_KEY_FILE', no_key), \
             patch.object(_mod, 'increment_retry', return_value=False), \
             patch.object(_mod, 'speak') as mock_speak, \
             patch.object(_mod, 'delete_flag'):
            with self.assertRaises(SystemExit):
                _mod.main()

        mock_speak.assert_called_once_with(expected_default)


# ===========================================================================
# SECTION 4: LOGGING TESTS
# ===========================================================================

class TestLogging(unittest.TestCase):
    """
    Verify that log_s() writes entries and that key flow events produce
    the correct log entries (retry counters, model names, timeout values,
    error types, success markers).
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.log_file = Path(self.tmp) / 'test-stop-notifier.log'
        self.log_patcher = patch.object(_mod, 'STOP_LOG', self.log_file)
        self.log_patcher.start()

    def tearDown(self):
        self.log_patcher.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _read_log(self):
        if not self.log_file.exists():
            return ''
        return self.log_file.read_text(encoding='utf-8')

    def test_log_s_writes_timestamped_entry(self):
        log_s('TEST ENTRY')
        content = self._read_log()
        self.assertIn('TEST ENTRY', content)
        import re
        self.assertRegex(content, r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')

    def test_log_s_appends_multiple_entries(self):
        log_s('FIRST')
        log_s('SECOND')
        log_s('THIRD')
        content = self._read_log()
        self.assertIn('FIRST', content)
        self.assertIn('SECOND', content)
        self.assertIn('THIRD', content)

    def test_delete_flag_logs_flag_name(self):
        p = Path(self.tmp) / '.my-flag'
        p.write_text('x', encoding='utf-8')
        delete_flag(p)
        content = self._read_log()
        self.assertIn('.my-flag', content)
        self.assertIn('deleted', content.lower())

    def test_increment_retry_logs_attempt_number(self):
        p = _tmp_flag(self.tmp, '.flag', 'ctx')
        increment_retry(p)
        content = self._read_log()
        self.assertIn('attempt', content.lower())
        self.assertIn('1/3', content)

    def test_increment_retry_logs_max_exceeded(self):
        p = _tmp_json_flag(self.tmp, '.flag.json', {'content': 'x', 'retries': 3})
        increment_retry(p)
        content = self._read_log()
        self.assertIn('max retries', content.lower())

    def test_llm_logs_start_with_timeout(self):
        """[llm] log line must mention the 15s timeout (v3.2.0)."""
        api_key_file = Path(self.tmp) / 'key'
        api_key_file.write_text('sk-fake', encoding='utf-8')
        from urllib.error import URLError

        with patch.object(_mod, 'API_KEY_FILE', api_key_file), \
             patch.object(_mod.urllib_request, 'urlopen',
                          side_effect=URLError('fail')):
            generate_dynamic_message('session_start', 'ctx')

        content = self._read_log()
        self.assertIn('[llm]', content)
        self.assertIn('15s', content)

    def test_llm_logs_each_model_attempt(self):
        """Each model in the fallback chain must be logged with its attempt number."""
        api_key_file = Path(self.tmp) / 'key'
        api_key_file.write_text('sk-fake', encoding='utf-8')
        from urllib.error import URLError

        with patch.object(_mod, 'API_KEY_FILE', api_key_file), \
             patch.object(_mod.urllib_request, 'urlopen',
                          side_effect=URLError('fail')):
            generate_dynamic_message('session_start', 'ctx')

        content = self._read_log()
        self.assertIn('Attempt 1/', content)
        self.assertIn('Attempt 2/', content)
        self.assertIn('Attempt 3/', content)

    def test_llm_logs_all_models_failed_message(self):
        """When all models fail, the 'All X models failed' message must be logged."""
        api_key_file = Path(self.tmp) / 'key'
        api_key_file.write_text('sk-fake', encoding='utf-8')
        from urllib.error import URLError

        with patch.object(_mod, 'API_KEY_FILE', api_key_file), \
             patch.object(_mod.urllib_request, 'urlopen',
                          side_effect=URLError('fail')):
            generate_dynamic_message('work_done', 'summary')

        content = self._read_log()
        self.assertIn('All', content)
        self.assertIn('failed', content.lower())

    def test_llm_logs_success_with_model_and_message(self):
        """On success, log must contain 'SUCCESS' and the returned message."""
        api_key_file = Path(self.tmp) / 'key'
        api_key_file.write_text('sk-fake', encoding='utf-8')
        resp_mock = _good_http_mock(_llm_json('Sir, done.'))

        with patch.object(_mod, 'API_KEY_FILE', api_key_file), \
             patch.object(_mod.urllib_request, 'urlopen', return_value=resp_mock):
            generate_dynamic_message('task_complete', 'ctx')

        content = self._read_log()
        self.assertIn('SUCCESS', content)
        self.assertIn('Sir, done.', content)

    def test_llm_logs_url_error_type(self):
        """URLError must produce a log line containing 'URL error'."""
        api_key_file = Path(self.tmp) / 'key'
        api_key_file.write_text('sk-fake', encoding='utf-8')
        from urllib.error import URLError

        with patch.object(_mod, 'API_KEY_FILE', api_key_file), \
             patch.object(_mod.urllib_request, 'urlopen',
                          side_effect=URLError('timed out')):
            generate_dynamic_message('session_start', '')

        content = self._read_log()
        self.assertIn('URL error', content)

    def test_llm_logs_no_api_key(self):
        """Missing API key must produce a 'No API key' log entry."""
        missing = Path(self.tmp) / 'no-key'
        with patch.object(_mod, 'API_KEY_FILE', missing):
            generate_dynamic_message('session_start', 'ctx')

        content = self._read_log()
        self.assertIn('No API key', content)

    def test_connecting_log_line_before_urlopen(self):
        """Log must contain 'Connecting to OpenRouter' before each urlopen call."""
        api_key_file = Path(self.tmp) / 'key'
        api_key_file.write_text('sk-fake', encoding='utf-8')
        resp_mock = _good_http_mock(_llm_json('Sir, test.'))

        with patch.object(_mod, 'API_KEY_FILE', api_key_file), \
             patch.object(_mod.urllib_request, 'urlopen', return_value=resp_mock):
            generate_dynamic_message('session_start', '')

        content = self._read_log()
        self.assertIn('Connecting to OpenRouter', content)

    def test_stop_hook_logs_silence_when_no_flags(self):
        """When no flags exist, main() must log the 'No voice flags found' message."""
        tmp = tempfile.mkdtemp()
        try:
            with patch.object(_mod, 'SESSION_START_FLAG', Path(tmp) / '.ss'), \
                 patch.object(_mod, 'TASK_COMPLETE_FLAG', Path(tmp) / '.tc'), \
                 patch.object(_mod, 'WORK_DONE_FLAG', Path(tmp) / '.wd'):
                with self.assertRaises(SystemExit):
                    _mod.main()

            content = self._read_log()
            self.assertIn('No voice flags found', content)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# ===========================================================================
# SECTION 5: SPEAK FUNCTION TESTS
# ===========================================================================

class TestSpeak(unittest.TestCase):
    """Tests for the speak() non-blocking Popen launcher."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.voice_script = Path(self.tmp) / 'voice-notifier.py'
        self.voice_script.write_text('# fake voice script', encoding='utf-8')

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_empty_text_does_not_launch_popen(self):
        with patch.object(_mod, 'VOICE_SCRIPT', self.voice_script), \
             patch.object(_mod.subprocess, 'Popen') as mock_popen:
            speak('')
        mock_popen.assert_not_called()

    def test_whitespace_only_does_not_launch_popen(self):
        with patch.object(_mod, 'VOICE_SCRIPT', self.voice_script), \
             patch.object(_mod.subprocess, 'Popen') as mock_popen:
            speak('   \t\n')
        mock_popen.assert_not_called()

    def test_missing_voice_script_does_not_raise(self):
        missing = Path(self.tmp) / 'no-voice.py'
        with patch.object(_mod, 'VOICE_SCRIPT', missing):
            try:
                speak('Sir, test message.')
            except Exception as exc:
                self.fail(f'speak() raised on missing voice script: {exc}')

    def test_valid_text_calls_popen(self):
        with patch.object(_mod, 'VOICE_SCRIPT', self.voice_script), \
             patch.object(_mod.subprocess, 'Popen') as mock_popen:
            speak('Sir, session started.')
        mock_popen.assert_called_once()

    def test_valid_text_passed_to_popen_command(self):
        with patch.object(_mod, 'VOICE_SCRIPT', self.voice_script), \
             patch.object(_mod.subprocess, 'Popen') as mock_popen:
            speak('Sir, session started.')
        cmd = mock_popen.call_args[0][0]
        self.assertIn('Sir, session started.', cmd)

    def test_popen_called_with_devnull_streams(self):
        """Fire-and-forget pattern: stdout and stderr must be DEVNULL."""
        import subprocess as sp
        with patch.object(_mod, 'VOICE_SCRIPT', self.voice_script), \
             patch.object(_mod.subprocess, 'Popen') as mock_popen:
            speak('Sir, hello.')
        kwargs = mock_popen.call_args[1]
        self.assertEqual(kwargs.get('stdout'), sp.DEVNULL)
        self.assertEqual(kwargs.get('stderr'), sp.DEVNULL)


# ===========================================================================
# MAIN RUNNER
# ===========================================================================

if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        # Unit tests
        TestReadFlag,
        TestDeleteFlag,
        TestIncrementRetry,
        TestGetSessionStartDefault,
        TestGetWorkDoneDefault,
        TestGetTaskCompleteDefault,
        # Integration tests
        TestCompleteFlow,
        TestPriorityOrder,
        # Mock tests (network/LLM simulation)
        TestGenerateDynamicMessage,
        # Logging tests
        TestLogging,
        # speak() function tests
        TestSpeak,
    ]

    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    print('')
    print('=' * 70)
    print('TEST SUMMARY')
    print('=' * 70)
    print(f'  Tests run   : {result.testsRun}')
    print(f'  Failures    : {len(result.failures)}')
    print(f'  Errors      : {len(result.errors)}')
    print(f'  Skipped     : {len(result.skipped)}')
    print(f'  Result      : {"PASS" if result.wasSuccessful() else "FAIL"}')
    print('=' * 70)

    sys.exit(0 if result.wasSuccessful() else 1)
