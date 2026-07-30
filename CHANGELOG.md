# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [UNRELEASED]

### Fixed

- **The SRS was generated somewhere nothing reads it** -- `DocumentationGenerator` created the SRS at `docs/SYSTEM_REQUIREMENTS_SPECIFICATION.md`, a path that exists nowhere in this repo, while `documentation_manager` reads the project-root `SRS.md` and both `rules/11` (permitted root documentation files) and `rules/44` (SRS lifecycle: "Create `SRS.md` at project root") place it at the root. Since the generator creates the file when absent, a fresh project got one SRS written into `docs/` that nothing ever read, while the root `SRS.md` the manager later appends FR entries and Change Log rows to was never generated at all -- two half-documents instead of one. The generator now targets root `SRS.md`, and a test asserts it stays in step with the first entry of the manager's `_SRS_ALTERNATES`.

---

## [1.21.1] - 2026-07-30

### Fixed

- **The push gates could not block a push, and fired on commands that merely mentioned one** (#249) -- `[BLOCKED L3.10]` and `[BLOCKED L3.11]` ran from the PostToolUse tracker, which fires *after* the tool completes: the push had already reached the remote by the time the gate printed that it was blocked. Four defects in total. (1) Wrong hook event, so nothing was ever prevented. (2) Detection was `"git push" in command`, so a grep for that string, an `echo`, or a commit message mentioning it all tripped the gate -- observed repeatedly on read-only greps during this work. (3) The VERSION question was answered from a session-wide list of every edited file, which spanned repositories and included scratchpad paths. (4) On a multi-commit branch the answer changed per push, so a follow-up commit re-reported a violation the branch already satisfied. Both rules now live in `hooks/pre_tool_enforcer/policies/push_gate.py` on PreToolUse, where a non-zero result actually stops the push. The command is tokenized and a git invocation is only recognized at the command position (`cd X && git push`, `git -C X push`, `VAR=1 git push`, `sudo git push` all handled; `--dry-run` / `--delete` exempt). VERSION is checked against the branch's merge base so one bump covers every push on the branch, and the clean-tree rule is scoped to the repository being pushed and ignores untracked files so coverage artifacts cannot block. Every check fails open, and the VERSION rule only applies to a repo that actually tracks a VERSION file -- only 4 of the 25 repos in this workspace do, so without that guard the gate would have blocked every push in the other 21 permanently, with nothing to bump to satisfy it. A command that commits before pushing is exempt from both rules: PreToolUse can only see the state before the command runs, so a chained `git commit && git push` looked dirty and version-less at gate time and produced a block the user could not act on -- committing first is exactly what they had already written. Four bugs of my own were caught, the last one by the gate blocking a real push of mine: a porcelain-prefix slice truncated the first reported path by a character, and `shlex.split(posix=True)` ate the backslashes in Windows paths so `git -C C:\path
epo push` resolved to nothing and silently allowed the push.
- **`scripts/tools/sync-version.py` never propagated anything, and any argument became the project version** (#248) -- three defects, all silent. `PROJECT_ROOT` was `Path(__file__).resolve().parent.parent`, which resolves to `scripts/` rather than the repo root, so `VERSION_FILE` pointed at a non-existent `scripts/VERSION` and every markdown target reported `[SKIP] not found` while the run still exited 0. `argv[1]` was written straight into VERSION with no validation, so `sync-version.py --help` set the version to the literal string `--help` and left a stray `scripts/VERSION` behind. Targets were rewritten with `Path.write_text`, which on Windows converts the committed LF files to CRLF and turns a two-line bump into a whole-file diff. Now: root resolved three parents up, real `argparse` with semver validation that rejects before touching any file, byte-preserving writes, a missing target fails the run instead of being skipped, and the stale `docs/SYSTEM_REQUIREMENTS_SPECIFICATION.md` target replaced with the root `SRS.md` that actually exists.
- **`scripts/tools/release.py` had the identical `parent.parent` root bug**, so it read a non-existent `scripts/VERSION` (reporting the current version as `0.0.0`) and looked for `scripts/CHANGELOG.md`.
- **`locked_json_update` raced instead of skipping when its lock was unavailable** -- `FileLock` fails open after a 5-second timeout so a lock problem can never break a tool call, but the read-modify-write then proceeded unlocked, which is exactly what produced the original `flow-trace.corrupt-*` archives. Surfaced as a flaky assertion in the new concurrency test: it passed in isolation (180/180 updates, lock acquired every time) and failed only under full-suite load. The read-modify-write is now skipped and reported as failure when the lock cannot be taken; the durable record is the append-only `flow-trace.jsonl` stream, which a single `O_APPEND` write cannot interleave. `record_policy_execution` accordingly reports success on that append rather than on the best-effort aggregate. A full-file replace under `atomic_write_text` keeps the opposite behavior deliberately -- an unlocked replace can lose an update but can never corrupt the file.
- **Version drift the broken sync had been hiding** -- `langgraph_engine/__init__.py` still declared `__version__ = "1.19.1"` and `SRS.md` said `1.20.0`. Both now match `VERSION`; a test asserts every hand-written reference agrees.

### Removed

- **`scripts/tools/bump-version.sh`** -- dead foreign code. It invoked `bump-version.py` and `update-docs.py` (neither exists in this repo) and staged `src/app.py` and `templates/base.html` (leftovers from an unrelated Flask project), on top of carrying the same off-by-one `PROJECT_ROOT`. `release.py` is the working release path.

---

## [1.21.0] - 2026-07-30

### Fixed

- **Hooks were not session-aware and fought each other over shared files** -- Claude Code passes a `session_id` in every hook stdin payload and no hook read it. Seven independent resolvers (`project_session.py`, `policy_tracking_helper.py`, `pre_tool_enforcer/loaders.py`, `post_tool_tracker/loaders.py`, `stop_notifier/voice.py`, `src/mcp/base/persistence.py`, `scripts/helpers/session_resolver.py`) each guessed the session from `.current-session.json`, a pointer file only the `session_create` MCP tool ever wrote -- so it had been frozen since 2026-03-17 while hooks kept appending to that 4-month-old session folder. Two of those resolvers were dead code: `scripts/helpers/session_resolver.py` read a `session_id` key the pointer file never had, and every resolver rejected IDs lacking a `SESSION-` prefix, which is exactly the shape of Claude's own payload UUID.
- **New `hooks/session_context.py` owns session identity** -- resolution order is bound payload `session_id` -> `CLAUDE_SESSION_ID` env -> pointer file -> legacy progress file. Each hook calls `bind_session(payload)` immediately after parsing stdin, which publishes the identity process-wide (and to child processes) so no call signature had to change. All seven resolvers now delegate to it.
- **Two incompatible session ID generators produced two folders per run** -- `context_sync/session_loader.py` minted `session-<ts>-<hex8>` and overwrote the `SESSION-<ts>-<suffix>` ID that `3-level-flow.py` had already set. Hooks validate the `SESSION-` prefix, so the engine's ID was rejected by all of them. The node now inherits the caller's ID and normalizes it; generation is a last-resort fallback only.
- **Two session roots (split brain)** -- hooks hardcoded `{memory}/logs/sessions` while `context_sync/helpers.py` fell back to `~/.claude/logs/sessions` on a failed `src/` import, leaving 569 session directories in a tree nothing read. Both sides now resolve the root through `session_context.get_sessions_root()`.
- **`flow-trace.json` corruption from concurrent read-modify-write** -- `record_policy_execution()` read, mutated and rewrote the file with no lock, from pre-tool, post-tool and stop hooks firing concurrently; one session folder held 44 `flow-trace.corrupt-*` archives (three within the same minute). Writes now run under a cross-process `FileLock` with atomic `os.replace`, plus an append-only `flow-trace.jsonl` companion stream written with a single `O_APPEND` `os.write`.
- **`session-progress.json` was one global file shared by every session and project** -- observed carrying `modified_files_since_commit` entries from `claude-global-library` while the active session was `claude-workflow-engine`. Progress is now per-session at `sessions/{SESSION_ID}/progress.json`, stamped with its `session_id`; the global file remains read-only as a fallback for pre-existing sessions. `save_session_progress()` also no longer truncates the target with mode `"w"` before taking its lock.
- **Unresolved sessions fabricated a `sessions/unknown/` folder** -- `policy_tracking_helper.get_session_id()` defaulted to the literal string `"unknown"`, so every failed resolution appended into one directory that looked like a real session. Those records now route to `sessions/_unresolved/`.
- **Warm PreToolUse daemon leaked session state across requests** -- the long-lived daemon reused `loaders._flow_trace_cache` from whichever session first populated it. Each request now binds its own session and resets session-scoped caches.

- **CI went red on every branch when `mcp` 2.0.0 was released** -- unrelated to the session work, surfaced by it. `requirements.txt` carried an unbounded `mcp>=1.0.0`; mcp 2.0.0 renamed `FastMCP` to `MCPServer` and moved `mcp.server.fastmcp.*` to `mcp.server.mcpserver.*`, so `src/mcp/session_mcp_server.py`'s `from mcp.server.fastmcp import FastMCP` fails with `ModuleNotFoundError` and collection aborts. Confirmed as dependency drift rather than a code regression by re-running main's last green run (commit `66bd654`, green 2026-07-26) with a fresh install: it now fails identically. Bounded to `mcp>=1.0.0,<2.0.0`; the 2.x migration spans this repo plus the 13 `mcp-*` server repos and is tracked separately.

- **`mcp` 2.x support; the `<2.0.0` bound from earlier in this release is removed** -- mcp 2.0.0 renamed `FastMCP` to `MCPServer` and moved `mcp.server.fastmcp.*` to `mcp.server.mcpserver.*`, with the v1 path gone and no alias. All 22 server files across this repo and the `mcp-*` fleet now use a two-line version probe that prefers the v2 name and falls back to v1, so each repo runs under either major version and can be upgraded independently -- a hard cut would have broken every repo not migrated in the same breath, since they all share one installed `mcp` package. Nothing else needed changing: `MCPServer(name, instructions=...)`, `@mcp.tool()` and `mcp.run(transport="stdio")` are identical in both versions. Verified by loading all 22 servers (292 tools registered, counts unchanged) and resolving the probe under both mcp 1.26.0 and 2.0.0.

### Added

- **`scripts/tools/migrate_session_dirs.py`** -- consolidates historical session directories onto one root and one ID format. Move-only, never deletes; anything not cleanly normalizable goes to a timestamped `sessions/_archive/` folder. Dry run by default, `--apply` to execute. Applied: 1264 directories case-normalized, 148 renamed, 2032 files merged, orphan root drained, `unknown/` archived, 0 failures, 0 empty directories left behind.
- **`tests/test_session_context.py`** -- 34 tests covering normalization of all three ID forms, resolution precedence, per-session scoping, path-traversal rejection, IDE-mode roots, and concurrency regression tests that assert 180 threaded updates leave the aggregate parseable with no lost records and 200 concurrent JSONL appends produce exactly 200 valid lines.

---

## [1.20.3] - 2026-07-25

### Changed

- **`agent_persona.py` PreToolUse gate message clarified** -- the `[GENERIC-OK]` escape hatch already accepted any generic subagent spawn, but its message only described "genuinely generic one-off tasks". Documented that it also covers recurring content-authoring tasks where no persona exists to inject because the persona/skill itself is what the task produces (e.g. authoring a new `SKILL.md`/`agent.md` for a library domain that doesn't have that persona yet). No logic change.

---

## [1.20.2] - 2026-07-22

### Fixed

- **CI red on `main` for 5 consecutive runs** -- 9 tests (`test_faithfulness_gate.py`, `test_import_manager.py`, `test_kg_routing.py`, `test_library_resolver.py`) required the real `claude-global-library` sibling checkout, which exists on developer machines but is never checked out on the GitHub Actions runner. Moved all 9 to `tests/integration/test_library_resolver_real_sibling.py` with a `pytest.mark.skipif` guard keyed on sibling-directory presence, so they run fully in local dev and skip cleanly in CI instead of hard-failing.

---

## [1.20.1] - 2026-07-22

### Fixed

- **Non-ASCII characters in `library_adapter.py` docstrings** -- three section-symbol characters replaced with "Section" to satisfy the Windows/cp1252 ASCII-only file check.

---

## [1.20.0] - 2026-07-12

Major release: flat -> domain-subpackage migration, Step 0 TODO-decomposition pipeline,
audited-deficiency remediation, and a standards / logging hardening pass.

### Added

- **Domain subpackages** -- flat `langgraph_engine/*.py` modules reorganized into focused packages: `analysis/`, `context/`, `engine_logging/`, `github/`, `metrics/`, `quality/`, `security/`, `skills/`, `standards/` (backward-compat shims kept at the old paths).
- **Step 0 TODO-decomposition pipeline** -- the monolithic orchestrator call is replaced by `prompt_gen_expert_caller -> todo_decomposer -> todo_executor` (per-TODO agent execution).
- **SRS / UML / architecture lifecycle rules** added under `rules/`.

### Changed

- **Graph factory unified** -- `verify_node` runtime-verification wrapping moved into `orchestrator.create_flow_graph`; duplicate `pipeline_builder.py` removed; `ENABLE_RUNTIME_VERIFICATION` now live.
- **error_logger console output routed through the shared logger** (severity-based dispatch; `_print_error` -> `_log_error`).
- **~180 silent `except Exception: pass`** across 44 modules narrowed to specific exception types + `logger.debug/warning` (Rule 2: no silently-swallowed exceptions).

### Fixed

- **loguru interpolation bug** -- 124 `logger.<level>("...%s...", arg)` calls across 17 loguru-backed files silently dropped their positional args (loguru uses `str.format`, not %-interpolation); converted to brace-style `"...{}...", arg`.
- **Step 0 planning chain revived** -- node<->caller CLI-flag mismatch, wrong return-key read, and a hardcoded 30s timeout overriding the STEP0_* budgets; all repaired.
- **level1_sync hyphen->underscore rename completed** -- session pruning and preference / pattern / context features (previously silent no-ops) restored.
- **Red CI greened** -- test suites repointed from deleted hyphen modules to real subpackage locations; `llm_call` neutralized in the unit suite (no real `claude` subprocess) and `github`/`quality` added to the PEP 562 `_LAZY_SUBMODULES` self-heal so `unittest.mock.patch` dotted targets resolve on Python 3.10.
- **Post-migration review fixes** -- the `step_logger` shim now re-exports `_summarize_result` (previously `ImportError` on every step-log write, escaping the `OSError`-only handler); fixed an `exc` name-clobber in the SonarQube auto-fixer backup-restore path (`NameError` on double-failure); the `metrics` aggregator counts `"COMPLETED"` status toward `success_rate` again. The legacy `complexity_distribution` histogram (tied to the removed 1-10 `complexity` field) is intentionally dropped in favor of the 1-25 `combined_complexity_score`.

### Docs

- CLAUDE.md: corrected directory layout (`langgraph_engine/` is at repo root, not under `scripts/`), rewrote the Step 0 flow (todo-decomposition), and refreshed Quick Info counts. README version + test badges updated (1.20.0, 45 test files).

---

## [1.19.3] - 2026-04-19

### Fixed

- **Level -1 regex: single-char escape sequences still matched** -- `%d:\n`, `%s:\t` were matched because `%` is not a word char so negative lookbehind passed. Fixed by requiring 2+ chars after `:\` (first char `[A-Za-z0-9_]` + at least one more). Prevents `test_call_graph_analyzer.py` fixture corruption. (Issue #229, PR #230)
- **`OPTIONS:\n` and `KB SUGGESTIONS:\n` restored** -- These strings in `recovery.py` were corrupted to `/n` by the old auto-fix bug. Restored in PR #230. (Issue #225)
- **Full escape sequence corruption audit** -- 6 additional `/n` corruptions fixed across `github_code_review.py`, `steps8to12_github.py`, `steps8to12_jira.py`, `prompt-generator.py`, `test_call_graph_analyzer.py`. (Issue #226, PR #232)
- **ASCII encoding: 37 non-ASCII Python files fixed** -- Replaced em dashes, arrows, box-drawing chars, emoji, curly quotes with ASCII equivalents. Level -1 ASCII check now passes. (Issue #227, PR #231)

### Files Changed

| File | Change |
|------|--------|
| `langgraph_engine/level_minus1/nodes.py` | Detection regex: 2-char minimum path segment |
| `langgraph_engine/level_minus1/recovery.py` | Fix regex: 2-char min + restored `OPTIONS:\n` |
| `langgraph_engine/level3_execution/github_code_review.py` | Restored `\n` escape sequences |
| `langgraph_engine/level3_execution/steps8to12_github.py` | Restored `\n` escape sequences |
| `langgraph_engine/level3_execution/steps8to12_jira.py` | Restored `\n` escape sequences |
| `tests/test_call_graph_analyzer.py` | Restored `\n` in fixture source string |
| 37 Python files | Replaced non-ASCII chars with ASCII equivalents |

---

## [1.19.2] - 2026-04-19

### Fixed

- **Level -1 Windows path regex corrupts escape sequences** — `nodes.py` detection and `recovery.py` fix regex both used `([A-Za-z]):\\([\w\\. \-]+)` which matched any `<letter>:\<word>` sequence. This caused false positives on Python escape sequences: `"Either:\n"` became `"Either:/n"`, `r"\s+"` patterns became `r"/s+"`. Fixed by adding `(?<![A-Za-z0-9_])` negative lookbehind so only real Windows drive paths (`C:\Users\...`) are matched. (Issue #222, PR #223)
- **stop-notifier shim simplified** — replaced `importlib.util` spec-loading with `sys.path` insert + direct import, consistent with other hook shims. (Issue #220, PR #221)

### Files Changed

| File | Change |
|------|--------|
| `langgraph_engine/level_minus1/nodes.py` | Detection regex: added negative lookbehind, switched from `"\\" in content` to compiled regex |
| `langgraph_engine/level_minus1/recovery.py` | Fix regex: added `(?<![A-Za-z0-9_])` negative lookbehind |
| `hooks/stop-notifier.py` | Simplified from 27-line `importlib.util` loader to 15-line `sys.path` shim |

---

## [1.19.1] - 2026-04-15

### Fixed — CI Failures

- **Python 3.9 dependency conflict** — `mcp>=1.0.0` requires Python>=3.10; CI matrix updated from `["3.9","3.11"]` to `["3.10","3.11"]`; `pyproject.toml` `requires-python` updated from `>=3.9` to `>=3.10`; Python 3.9 classifier removed
- **Python 3.11 collection error** — `tests/test_session.py` was a misplaced Flask scratch script from the `claude-insight` project (not a pytest file, imported `flask` which is not installed); deleted
- **4 untracked test files** — `tests/e2e/conftest.py`, `tests/e2e/test_full_mode_runtime_verification.py`, `tests/e2e/test_hook_mode_runtime_verification.py`, `tests/integration/test_runtime_verification_integration.py` were documented in CHANGELOG v1.18.0 as added but never committed; now committed

### Changed

- **README roadmap** — removed redundant "Past Releases" summary table (full history already in CHANGELOG); renamed "Next" to "Upcoming"; updated Python badge and prerequisites from 3.9+ to 3.10+

### Files Changed

| File | Change |
|------|--------|
| `.github/workflows/ci.yml` | Python matrix: `["3.9","3.11"]` → `["3.10","3.11"]` |
| `pyproject.toml` | `requires-python = ">=3.9"` → `">=3.10"`; removed 3.9 classifier |
| `tests/test_session.py` | Deleted (misplaced Flask script, not a pytest file) |
| `tests/e2e/conftest.py` | Added (was untracked since v1.18.0) |
| `tests/e2e/test_full_mode_runtime_verification.py` | Added (was untracked since v1.18.0) |
| `tests/e2e/test_hook_mode_runtime_verification.py` | Added (was untracked since v1.18.0) |
| `tests/integration/test_runtime_verification_integration.py` | Added (was untracked since v1.18.0) |
| `README.md` | Python badge + prerequisites updated to 3.10+; roadmap cleanup |

---

## [1.19.0] - 2026-04-15

### Added — CI & Distribution

- **GitHub Actions CI** (`.github/workflows/ci.yml`) — auto-triggers on push/PR to `main`; paths-ignore for docs/uml/drawio/md; Python 3.9 + 3.11 matrix; `concurrency: cancel-in-progress`
- **Hard CI gates** — `secrets_check.py` exit-1 gate runs first; unit tests and integration tests are mandatory (no `continue-on-error`)
- **32 offline integration tests** (`tests/integration/`) — uses `responses` mock library; covers full GitHub PR lifecycle (issue → branch → PR → merge → close); runs in ~0.3s, no GitHub token required
- **PyPI packaging** — `pyproject.toml` (hatchling, PEP 621), `MANIFEST.in` (includes policies/, rules/, templates/), `requirements-dev.txt` (responses, pytest-cov, ruff)
- **PyPI publish workflow** (`.github/workflows/publish.yml`) — fires automatically on GitHub Release; `pip install claude-workflow-engine`
- **`langgraph_engine/__init__.py`** — `__version__ = "1.19.0"` added; importable package version
- **`sync-version.py` extended** — now keeps `__version__` in `langgraph_engine/__init__.py` in sync on version bumps

### Files Added

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | Auto-CI on push/PR to main |
| `.github/workflows/publish.yml` | PyPI publish on GitHub Release |
| `pyproject.toml` | Package metadata (hatchling, PEP 621) |
| `MANIFEST.in` | sdist asset inclusion (policies/, rules/, templates/) |
| `requirements-dev.txt` | Dev deps: responses, pytest-cov, ruff |
| `tests/integration/conftest.py` | Mock GitHub API fixtures (responses library) |
| `tests/integration/test_github_integration.py` | 27 offline endpoint tests |
| `tests/integration/test_github_pr_workflow.py` | 5 lifecycle tests (issue→PR→close) |
| `langgraph_engine/__init__.py` | `__version__ = "1.19.0"` |
| `scripts/tools/sync-version.py` | Extended to sync `__version__` on bumps |

---

## [1.18.0] - 2026-04-14

### Added — Runtime Verification
- Runtime Verification package (`langgraph_engine/runtime_verification/`)
- `NodeContract` DSL: `PreconditionSpec`, `PostconditionSpec`, `InvariantSpec`, `Violation`, `NodeContract` dataclasses
- `RuntimeVerifier` + `NullVerifier` -- Registry + Null Object + Singleton patterns; <5ms per-node overhead
- `@verify_node(contract)` decorator -- non-invasive wrapping, zero overhead when `ENABLE_RUNTIME_VERIFICATION=0`
- Level transition guards for 4 pipeline boundaries (`level_minus1->level1`, `level1->level3`, `pre_analysis->step0`, `step0->step8`)
- `schema_verifier`: `verify_orchestration_prompt()`, `verify_orchestrator_result()` for LLM output validation
- `VerificationReport` dataclass with `to_dict()` for JSON-serialisable FlowState storage
- `QualityGate` Gate 5: `verification_gate` -- non-strict by default, halts on `STRICT_RUNTIME_VERIFICATION=1`
- `FlowState` keys: `verification_report: Optional[Dict]`, `verification_violations: List[str]`
- Env vars: `ENABLE_RUNTIME_VERIFICATION=0`, `STRICT_RUNTIME_VERIFICATION=0`, `VERIFICATION_LOG_LEVEL=WARNING`
- **34 unit tests** — `test_runtime_verifier` (15), `test_level_transition_guards` (8), `test_schema_verifier` (7), `test_quality_gate_verification` (4)
- **E2E tests** — `tests/e2e/test_hook_mode_runtime_verification.py` (11 tests, Hook Mode), `tests/e2e/test_full_mode_runtime_verification.py` (9 tests, Full Mode)
- **7 integration tests** — `tests/integration/test_runtime_verification_integration.py`

### Added — Observability Exposure
- **`/health` endpoint** — `verification` snapshot block added: `enabled`, `total_violations`, `critical_violations`, `last_run_ms`
- **Prometheus counter** — `verification_violations_total` (9th metric); labels: `level`, `node`; incremented on every violation
- **OpenTelemetry spans** — `runtime_verification.verify_node` span wraps every `@verify_node` call; 4 attributes: `node.name`, `contract.name`, `violations.count`, `violations.critical`

### Architecture
- ADR-003: Decorator pattern over node subclassing
- ADR-004: Opt-in default (`ENABLE_RUNTIME_VERIFICATION=0`)
- ADR-005: No LLM/network/I/O calls in verifier (enforces <5ms latency contract)

---

## [1.17.0] - 2026-04-10

### Added — Open Source Readiness

- **Community files** — `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`, issue templates, PR template
- **GitHub Discussions enabled** — feature requests, integration questions, workflow sharing, Q&A
- **All 13 MCP server repos made public** under [techdeveloper-org](https://github.com/orgs/techdeveloper-org/repositories)
- **README rewrite** — full open-source-grade documentation (architecture, benchmarks, MCP table, community section)

### Fixed — F821 Undefined-Name Audit (issues #212–#216)

- `hooks/stop_notifier/` — 30 F821 errors fixed; missing imports restored (#212)
- `langgraph_engine/level3_execution/nodes/` — 17 F821 errors fixed (#213)
- `langgraph_engine/diagrams/drawio/converter.py` — ~80 F821 errors fixed; `S_*` constants + logger imported (#214)
- `scripts/github_pr_workflow/` — 12 F821 errors fixed; missing `git_ops` imports restored (#215)
- 4 files — stale `# ruff: noqa: F821` suppressors removed after fixes (#216)

### Changed

- `ruff check .` — passes clean with zero suppressors across all fixed files

---

## [1.16.1] - 2026-04-07

### Changed — Diagram Output Restructure + Configurable Paths

- **`uml/` moved to project root** — previously `docs/uml/`, now at `<target_project>/uml/` (top-level, not nested under docs)
- **`drawio/` moved to project root** — previously `docs/drawio/`, now at `<target_project>/drawio/` (top-level)
- **`UML_OUTPUT_DIR` env var** — overrides the UML output directory; relative paths resolved against target project root, absolute paths used as-is; defaults to `uml/`
- **`DRAWIO_OUTPUT_DIR` env var** — overrides the draw.io output directory; same resolution logic; defaults to `drawio/`
- **`.env.example`** — added `DIAGRAM OUTPUT DIRECTORIES` section documenting both new env vars
- **`rules/11-documentation-files.md`** — exemption list updated: `uml/` and `drawio/` at root are now auto-generated exempt dirs

### Files Updated

| File | Change |
|------|--------|
| `langgraph_engine/diagrams/legacy_generator.py` | `__init__` reads `UML_OUTPUT_DIR`; absolute/relative path logic |
| `langgraph_engine/level3_execution/documentation_manager.py` | `_generate_drawio_diagrams()` reads `DRAWIO_OUTPUT_DIR`; relative path in return values |
| `scripts/architecture/generate_system_diagram.py` | `__main__` block reads `DRAWIO_OUTPUT_DIR` |
| `scripts/tools/create_mcp_repos.py` | Fixed stale `DRAWIO_OUTPUT_DIR` default (`docs/diagrams/` → `drawio/`) |
| `tests/test_uml_generators.py` | Updated test assertions to expect `uml/` not `docs/uml/` |
| `CLAUDE.md`, `README.md`, `rules/11-documentation-files.md` | Directory layout references updated |

### Why

Diagram output directories belong at the target project root alongside source code, not buried inside `docs/`. This matches the convention for auto-generated artifacts. Env var configurability allows different projects to direct output wherever needed (e.g. `diagrams/uml`, `/tmp/preview`, a custom CI artifacts path).

---

## [1.8.0] - 2026-03-28

### Added — Orchestration Template Fast-Path

- **`--orchestration-template=PATH` CLI flag** in `3-level-flow.py` — accepts a pre-filled JSON template that bypasses Steps 0-5 entirely and routes directly to Step 6 (skill validation)
- **`_load_orchestration_template(path)`** — validates required fields (`task_type`, `complexity`, `skill`/`skills`, `agent`/`agents`) and returns parsed dict; raises `ValueError` on malformed input
- **Template fast-path node logic** in `orchestration_pre_analysis_node` — when template is detected, injects all step 0-5 FlowState fields and returns early (before call graph scan)
- **`template_fast_path` routing** in `route_pre_analysis` — two-way priority routing: Template (→ `level3_step6`) > miss (→ `level3_step0_0`)
- **`orchestration_template` and `template_fast_path` FlowState fields** in `state_definition.py`
- **`level3_step6` conditional edge** added to `orchestrator.py` pre-analysis routing map
- **`orchestration_template.example.json`** — fully annotated example template with all supported fields
- **README: Orchestration Template Fast-Path section** — full explanation with before/after comparison, decision tree, field reference, and fail-safe behavior
- **README: Pre-Analysis Decision Tree updated** — now shows two-priority routing with Template as highest priority

### Performance Impact

| Metric | Before (full pipeline) | After (template fast-path) |
|--------|----------------------|---------------------------|
| LLM calls (hook mode) | 7-8 calls | **1 call** (Step 10 only) |
| Hook mode latency | ~60 seconds | **~15 seconds** |
| LLM cost reduction | baseline | **~87% reduction** |
| Pipeline determinism | LLM-dependent | **Fully deterministic** (Steps 0-5) |

### Changed

- `route_pre_analysis` — extended from 1-way to 2-way routing (template > normal)
- `orchestrator.py` conditional edges map — added `"level3_step6"` target
- `README.md` — "How the Engine Reduces LLM Calls" table updated with Template Fast-Path as new top entry
- `README.md` — Running the Pipeline section updated with `--orchestration-template` usage

### Fail-Safe Design

Template fast-path is fail-open: any error (file not found, invalid JSON, missing fields, runtime exception) logs a warning and falls through to the normal pipeline. No pipeline interruption.

---

## [1.5.0] - 2026-03-21

### Added — Modular Architecture (9 New Packages)

- `core/` — Cross-cutting abstractions: LazyLoader, get_logger, node_error_handler, safe_execute, NodeResult, create_integration_hook, get_infra, create_step_node, StepExecutionContext
- `state/` — FlowState split into 6 modules: state_definition, step_keys, reducers, toon_format, context_optimizer, __init__
- `routing/` — All 7 routing functions extracted from orchestrator.py, split by pipeline level
- `helper_nodes/` — 11 helper node functions split by concern (context, output, step, standards, level_minus1)
- `diagrams/` — Strategy Pattern: DiagramFactory + 13 AbstractDiagramGenerator subclasses (class, sequence, activity, state, component, package, usecase, object, deployment, communication, composite, interaction + AST analyzer + Kroki renderer)
- `parsers/` — Abstract Factory: ParserRegistry + 4 language parsers (PythonASTParser, JavaRegexParser, TypeScriptRegexParser, KotlinRegexParser)
- `sonarqube/` — Facade: SonarQubeScanner + api_client, lightweight_scanner, result_aggregator, auto_fixer, config
- `integrations/` — Abstract Factory + Template Method: IntegrationRegistry + AbstractIntegration (Create/Update/Close lifecycle) + GitHub, Jira, Figma, Jenkins concrete adapters
- `pipeline_builder.py` — Builder Pattern: PipelineBuilder with chainable add_level_minus1(), add_level1(), add_level2(), add_level3(), build() + create_flow_graph() convenience function

### Changed

- `flow_state.py` — Reduced to 27-line backward-compat shim (re-exports from `state/`)
- `uml_generators.py` — Backward-compat note added; DiagramFactory is new entry point
- `call_graph_builder.py` — Backward-compat note added; ParserRegistry is new entry point
- VERSION bumped: 1.4.1 → 1.5.0
- Total Python files: 295+ → 360+ (65 new files in 9 packages)
- LangGraph Engine modules: 92 → 155+
- SRS (`scripts/System_Requirement_Analysis.md`) — Complete rewrite with proper project content

### Design Patterns Applied

- Factory Method — create_integration_hook, create_step_node, PipelineBuilder.add_level*
- Abstract Factory — ParserRegistry (4 languages), IntegrationRegistry (4 services)
- Strategy — DiagramFactory (13 diagram types, swappable at runtime)
- Decorator — node_error_handler, safe_execute
- Builder — NodeResult fluent builder, PipelineBuilder chain
- Facade — SonarQubeScanner (api + lightweight + aggregator unified)
- Template Method — AbstractIntegration lifecycle (create/on_branch/update/on_review/close)
- Registry (DSA) — DiagramFactory, ParserRegistry, IntegrationRegistry hash maps

### Tests

- 1,608 tests passing (133 core modularization tests verified)

---

## [1.4.1] - 2026-03-18

### Added

- Step 10 transitions and updates for Jira + Figma workflows
- Figma MCP server + design-to-code pipeline integration
- CLI interface, setup wizard, and getting started guide

### Changed

- Full integration lifecycle (Create → Update → Close) for Jira and Figma

---

## [1.4.0] - 2026-03-15

### Added

- Jira integration (dual GitHub+Jira issue tracking, Steps 8/9/11/12)
- Jenkins CI/CD integration (Steps 10/11)
- SonarQube scanner with auto-fix loop
- Quality gate enforcement (4 gates)
- Unit test auto-generation (4 languages)
- Integration test generation (CallGraph call-path based)
- Coverage analyzer (AST-based, risk-prioritized)

---

## [1.3.0] - 2026-03-10

### Added

- Call graph v2.0 (class-level FQN, 578 classes, 3,985 methods, 4 languages)
- UML generators (13 diagram types, CallGraph-powered)
- Metrics aggregator + dashboard

---

## [1.0.0] - 2026-03-01

### Added

- 4-Level pipeline architecture (Level -1, 1, 2, 3)
- 15-step SDLC automation
- 19 MCP servers (323 tools)
- GitHub integration (issue, branch, PR, merge, review)
- Policy system (63 policies)
- Hook system (UserPromptSubmit, PreToolUse, PostToolUse, Stop)
- Hybrid LLM inference (4 providers)
- Session management + TOON compression

---

[1.19.0]: https://github.com/techdeveloper-org/claude-workflow-engine/compare/v1.18.0...v1.19.0
[1.18.0]: https://github.com/techdeveloper-org/claude-workflow-engine/compare/v1.17.0...v1.18.0
[1.17.0]: https://github.com/techdeveloper-org/claude-workflow-engine/compare/v1.16.1...v1.17.0
[1.16.1]: https://github.com/techdeveloper-org/claude-workflow-engine/compare/v1.8.0...v1.16.1
[1.8.0]: https://github.com/techdeveloper-org/claude-workflow-engine/compare/v1.5.0...v1.8.0
[1.5.0]: https://github.com/techdeveloper-org/claude-workflow-engine/compare/v1.4.1...v1.5.0
[1.4.1]: https://github.com/techdeveloper-org/claude-workflow-engine/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/techdeveloper-org/claude-workflow-engine/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/techdeveloper-org/claude-workflow-engine/compare/v1.0.0...v1.3.0
[1.0.0]: https://github.com/techdeveloper-org/claude-workflow-engine/releases/tag/v1.0.0
