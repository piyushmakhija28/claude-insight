# FR-8a / SRS FR-19 — Stop-hook spawn instrumentation and capability decisions

**Work item:** V2-033 (GitHub #289) · **Unblocks:** V2-034 (#290)
**Measured:** 2026-08-03 · **Checkout:** branch `docs/segregate-docs-tree`, 64 commits ahead of `main`, clean working tree
**Instrument:** `scripts/tools/stop_hook_spawn_instrument.py` · **Gate:** `tests/test_stop_hook_spawn_instrumentation.py`

This closes the open item recorded in `docs/REVIEW-INDEX.md` as *"Stop-hook true per-turn spawn
count — INFERRED, NOT MEASURED"*. The inference it replaces was `~2`. **The measured figure is 7.**

---

## 1. Headline results

| Question | Answer | Basis |
|---|---|---|
| Subprocess spawns per invocation | **7**, identical in all 20 runs | MEASURED, audit hook |
| Distinct spawn sequences across 20 runs | **1** — the hook is deterministic on a fixed checkout | MEASURED |
| Wall-clock per invocation | mean **272.6 ms**, median 257.0, min 241.4, max 381.0 (sd 39.5) | MEASURED |
| Of the 9 referenced scripts, how many ran | **0** | MEASURED |
| Guards evaluated and returned False | **8** of 9 | MEASURED |
| Guards never reached at all | **1** of 9 (`voice-notifier.py`) | MEASURED |
| Real Claude Code Stop events captured under instrumentation | **0** — see §5 | MEASURED |

---

## 2. Measured versus carried forward

Every figure the acceptance criterion carries forward was re-derived. Three are confirmed,
three are wrong.

| Carried-forward claim | Verdict | Measured value |
|---|---|---|
| 17 subprocess call sites in `hooks/stop_notifier/` | **CONFIRMED** | 17 |
| Split core.py 11 / post_impl.py 5 / voice.py 1 | **CONFIRMED** | 11 / 5 / 1 (helpers.py 0, `__init__.py` 0) |
| `git rev-parse` at `post_impl.py:56`, unconditional | **CONFIRMED with a correction** | The `subprocess.run` call node begins at **line 55**; line 56 is its argv literal. Fires 20/20. |
| `git rev-parse` at `post_impl.py:209`, unconditional | **CONFIRMED with a correction** | Call node at **line 208**; line 209 is its argv literal. Fires 20/20. |
| `sync-version.py` spawn resolved at `post_impl.py:284` | **CONFIRMED** | Resolution at 284, guard at 285, spawn at 286. Target missing; guard returns False. |
| `voice-notifier.py` launched from `voice.py:144` | **WRONG** | Line 144 is inside the `speak()` **docstring**. The only spawn in `voice.py` is at **line 164**. |
| Both guarded targets "resolve as a sibling inside `hooks/stop_notifier/`" | **WRONG for voice** | Only `sync-version.py` resolves as a sibling. `voice-notifier.py` resolves via `helpers.py:142` to `CURRENT_DIR`, which is under the **user home** (`~/.claude/memory/current/voice-notifier.py`), never a package sibling. |
| The floor is **four** per-turn spawn opportunities | **WRONG on this checkout** | **Seven** spawns fire per turn. Five sites outside the enumerated four fire on every invocation; a sixth is enumerated below as a permitted exception. See §3. |

The `voice.py:144` and sibling-rationale errors are already corrected inside
`tests/nfr1/components.py`, which stores `voice.py:164` and asserts the home-anchored
resolution. The acceptance criterion text is stale relative to the tree, not the reverse.

---

## 3. The spawn sequence, attributed

Identical in all 20 invocations, in this order:

| # | argv | Attributed site | Bucket |
|---|---|---|---|
| 1 | `git branch --show-current` | `core.py:377` | named exception |
| 2 | `git rev-list --count main..docs/segregate-docs-tree` | `core.py:422` | named exception |
| 3 | `git status --porcelain` | `core.py:432` | named exception |
| 4 | `git rev-parse --abbrev-ref HEAD` | `post_impl.py:208` | **enumerated (2)** |
| 5 | `git rev-list --count main..HEAD` | `post_impl.py:216` | named exception |
| 6 | `git rev-parse --abbrev-ref HEAD` | `post_impl.py:55` | **enumerated (1)** |
| 7 | `git rev-list --count main..HEAD` | `post_impl.py:64` | named exception |

Sites 4 and 6 emit byte-identical argv, as do 5 and 7. They are separated by execution order,
which is fixed by `core.main` calling `_run_post_implementation_steps` (line 491) before
`_create_pr_from_pipeline_data` (line 494). Site 2 is separable by argv alone: it is the only
site interpolating the branch name (`main..{current_branch}`) rather than `main..HEAD`.

### Why the enumerated four under-counts

The four-opportunity model assumed opportunities 1 and 2 return early. They only do so on a
default branch. On any feature branch, each continues past its branch check into a second
`git rev-list` — and `core.py`'s PRIORITY 4 branch detection adds three more. Six named
exceptions are documented in the instrument, each with a rationale; five fire on this
checkout, and `core.py:349` does not because `.pr-workflow-retry` is absent (measured).

The gate therefore asserts a **subset** relation against enumerated-plus-excepted, not a count.

---

## 4. Capability decision per referenced script

| # | Script | Spawn site | Resolved target | Guard | Decision |
|---|---|---|---|---|---|
| 1 | `git-auto-commit-policy.py` | core.py:82 | `scripts/architecture/03-execution-system/09-git-commit/` | evaluated, **False** | **INERT — dead reference** |
| 2 | `auto-save-session.py` | core.py:111 | `scripts/architecture/01-sync-system/session-management/` | evaluated, **False** | **INERT — dead reference** |
| 3 | `archive-old-sessions.py` | core.py:139 | `scripts/architecture/01-sync-system/session-management/` | evaluated, **False** | **INERT — dead reference** |
| 4 | `session-pruner.py` | core.py:163 | `scripts/architecture/01-sync-system/` | evaluated, **False** | **INERT — dead reference** |
| 5 | `common-failures-prevention.py` | core.py:197 | `scripts/architecture/03-execution-system/failure-prevention/` | evaluated, **False** | **INERT — dead reference** |
| 6 | `preference-auto-tracker.py` | core.py:222 | `scripts/architecture/01-sync-system/user-preferences/` | evaluated, **False** | **INERT — dead reference** |
| 7 | `plan-session-archiver.py` | core.py:243 | `scripts/architecture/03-execution-system/02-plan-mode/` | evaluated, **False** | **INERT — dead reference** |
| 8 | `sync-version.py` | post_impl.py:286 | `hooks/stop_notifier/sync-version.py` | evaluated, **False** | **INERT — dead reference.** The real script is at `scripts/tools/sync-version.py`, unreachable by a `__file__`-sibling resolution |
| 9 | `voice-notifier.py` | voice.py:164 | `~/.claude/memory/current/voice-notifier.py` | **never evaluated** | **INERT, and unreachable on a silent turn** — see below |

`scripts/architecture/` contains exactly two Python files on this checkout
(`generate_system_diagram.py`, `03-execution-system/00-code-graph-analysis/code-graph-analyzer.py`).
None of the seven directories that references 1–7 name exist.

**Item 9 differs in kind and V2-034 must not treat it like the others.** `speak()` is called
only from `handle_voice_flag`, which returns early unless a voice flag file is present. On a
silent turn — the overwhelming majority — the `VOICE_SCRIPT.exists()` guard at `voice.py:155`
is never executed. The instrument reports this as `GUARD_NOT_REACHED`, deliberately distinct
from `GUARD_FALSE_SCRIPT_SKIPPED`. Recording an unreached guard as a failed guard would assert
a stronger fact than was measured.

---

## 5. What "REAL" could and could not be obtained

Acceptance criterion 1 asks for 20 consecutive **real** Stop-hook invocations. That was not
achievable from this execution context, and the figure is not simulated to fill the gap.

**The Stop hook is live.** `~/.claude/settings.json` registers it as a synchronous 60-second
command hook running `hooks/stop-notifier.py`. It has fired **1,643** genuine times since
2026-03-08 by its own terminal log marker.

**It did not fire once during this work.** A baseline was taken at 23,815 log lines before any
measurement and re-read afterwards: **zero growth, log mtime frozen at 19:12:16**, while
`tool-tracker.jsonl` continued updating from this agent's own tool calls seconds earlier. The
Stop event belongs to the parent session's completed response turns; **subagent turns do not
emit it**. No amount of work inside a subagent produces a real Stop invocation.

Three tiers were therefore produced, and they are not interchangeable:

| Tier | What is real | Count obtained | Answers |
|---|---|---|---|
| **Observational — historical** | Genuine Stop events, their own log artifacts | 1,643 total; last 20 analysed | which code paths were reached |
| **Observational — live window** | Genuine Stop events during this task | **0** | nothing |
| **Instrumented** | Real entry point, real guards, real git repo; **harness-triggered**, replica home | **20** | exact spawn counts, durations, guard dispositions |

The log corroborates but cannot count. `core.py`'s branch detection logs nothing when the
working tree is dirty, so log silence does not imply no spawns — which is precisely why FR-8a
demanded runtime instrumentation and why a static re-derivation was ruled insufficient.
Across the whole log the live path is well evidenced: 4,637 branch-detection lines and 276
lines showing `post_impl` reaching its MCP import.

---

## 6. Per-invocation measurements (instrumented tier, n = 20)

| # | Spawns | Wall ms | In-process ms | Guards | Floor |
|---|---|---|---|---|---|
| 1 | 7 | 255.7 | 191.7 | 8 False, 1 not reached | PASS |
| 2 | 7 | 260.4 | 183.9 | 8 False, 1 not reached | PASS |
| 3 | 7 | 264.3 | 198.3 | 8 False, 1 not reached | PASS |
| 4 | 7 | 299.6 | 235.9 | 8 False, 1 not reached | PASS |
| 5 | 7 | 256.6 | 182.5 | 8 False, 1 not reached | PASS |
| 6 | 7 | 379.8 | 310.2 | 8 False, 1 not reached | PASS |
| 7 | 7 | 279.1 | 203.0 | 8 False, 1 not reached | PASS |
| 8 | 7 | 250.2 | 178.0 | 8 False, 1 not reached | PASS |
| 9 | 7 | 268.9 | 195.6 | 8 False, 1 not reached | PASS |
| 10 | 7 | 286.7 | 202.7 | 8 False, 1 not reached | PASS |
| 11 | 7 | 262.5 | 194.5 | 8 False, 1 not reached | PASS |
| 12 | 7 | 256.5 | 184.1 | 8 False, 1 not reached | PASS |
| 13 | 7 | 245.9 | 180.6 | 8 False, 1 not reached | PASS |
| 14 | 7 | 257.1 | 194.2 | 8 False, 1 not reached | PASS |
| 15 | 7 | 254.1 | 180.2 | 8 False, 1 not reached | PASS |
| 16 | 7 | 381.0 | 313.0 | 8 False, 1 not reached | PASS |
| 17 | 7 | 251.2 | 180.3 | 8 False, 1 not reached | PASS |
| 18 | 7 | 256.9 | 194.5 | 8 False, 1 not reached | PASS |
| 19 | 7 | 244.3 | 183.8 | 8 False, 1 not reached | PASS |
| 20 | 7 | 241.4 | 180.4 | 8 False, 1 not reached | PASS |

**Observer perturbation.** Five uninstrumented control runs of the same entry point gave mean
253.2 ms (median 254.4, min 246.7, max 261.4). The audit hook and the recording `Path.exists`
cost **+19.4 ms on the mean, about 7.7 %**, and do not change the spawn count. Durations above
include interpreter startup, which Claude Code also pays.

---

## 7. Method, and where it is intrusive

**Observational tiers** parse artifacts only and never invoke the hook.

**The instrumented tier is intrusive and is labelled so in its own output.** A wrapper installs
a CPython audit hook capturing every `subprocess.Popen` event, and replaces `Path.exists` with
a recording pass-through, then executes the real `hooks/stop-notifier.py` through `runpy` under
`run_name="__main__"`, with a realistic Stop payload on stdin and the repository as cwd. The
code path, every guard, and the git repository are real. Only the trigger and the home
directory are not.

**Home redirection.** `HOME`/`USERPROFILE` point at a replica seeded to reproduce the three
facts about the live home that change which guards are reached: `~/.claude/scripts` absent,
`.voice-disabled` present, and at least one session directory under `~/.claude/logs/sessions`.
Without the third, `_run_post_implementation_steps` returns before reaching the `sync-version.py`
guard and opportunity 3 would have been mis-reported as unreachable. Hermeticity was verified:
across all 20 runs, **zero** recorded guard paths fall under the real `~/.claude`.

**No PR could be created.** `_create_pr_from_pipeline_data` imports `github_mcp_server` from
`src/mcp/` and `core.py` imports `github_pr_workflow` from the hook package. **Neither module
exists** (measured), so both paths raise `ModuleNotFoundError` into their enclosing handlers.
This is not a precaution taken by the harness; it is the measured state of the tree, and the
live log shows genuine turns failing the same way 276 and 72 times respectively.

---

## 8. Incidental findings for V2-034

1. **A tenth dead reference exists beyond the nine.** `hooks/metrics_emitter.py` **does not
   exist anywhere in the repository**. `helpers.py` imports it inside a `try` and falls back to
   a no-op, so the `emit_hook_execution` call at `core.py:498` silently discards the duration
   the hook computes at `core.py:497`. **This is why no real invocation has a recorded
   duration** and why criterion 1(b) is unobtainable observationally. If V2-034 wants real
   durations rather than harness durations, restoring this emitter is the cheapest route.

2. **The hook attempts PR creation on every turn of every feature branch.** With 64 commits
   ahead and a clean tree it reaches `github_pr_workflow.run_pr_workflow()` and
   `github_create_pr(...)`. Both currently fail on a missing import. **If either module is
   restored without also revisiting the trigger conditions, the Stop hook will begin opening
   real pull requests unprompted.** Whoever fixes or retires these references should decide
   that deliberately.

3. **`.pr-ready-timestamp` is live state in the owner's home**, written and unlinked by the
   debounce logic on ordinary turns.

4. **Retiring references 1–7 does not reduce the spawn count.** All seven are already inert
   behind `.exists()` guards; the 7 spawns are git calls. Removing dead references is a
   correctness improvement, not an NFR-1 improvement.

---

## 9. Verification of the gate itself

`tests/test_stop_hook_spawn_instrumentation.py` — 24 tests, all passing. Every check drives
`evaluate_spawn_floor` as it is **stored** in the instrument module, not a re-authored copy.

**Specificity, both directions.** The gate fails on an unenumerated fifth spawn and on either
unconditional opportunity going missing; it passes when opportunities 3 and 4 stay silent, and
also passes when they fire. A silent guarded opportunity is the measured expected state.

**Mutation testing — 8 mutants, 8 killed, 0 survivors:** forcing `evaluate_spawn_floor` to
always PASS; deleting the must-fire check; deleting the outside-the-set check; collapsing both
`rev-parse` sites onto one; conflating `GUARD_NOT_REACHED` into `GUARD_FALSE`; making the census
skip `Popen` sites; making the resolver always report `ARMED`; and ignoring retry-flag guard
evidence. The module was restored and the suite re-run green afterwards.

---

## 10. Not verified

- **Spawn behaviour on `main`.** Measured only on `docs/segregate-docs-tree`. On a default
  branch, opportunities 1 and 2 return early and the count should fall — predicted, not measured.
- **Behaviour when a voice flag is present.** Opportunity 4's guard was never reached in 20
  silent turns; its behaviour on a voice-flag turn is unmeasured.
- **`core.py:349`.** Never fired; `.pr-workflow-retry` was absent throughout.
- **Real per-invocation durations and spawn counts.** Unobtainable here for the reasons in §5
  and finding 1 of §8.
- **Whether the parent session's Stop invocations would show 7.** Strongly corroborated by the
  live log, but the parent was never instrumented.
