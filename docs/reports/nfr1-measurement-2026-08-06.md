# NFR-1 measurement, 2026-08-06

The first measurement of NFR-1 that is valid on its own terms: a real plugin installed and
loaded, ten real tool calls counted, a window that stayed inside one response turn, and a
process count taken across it.

**Overall verdict: INDETERMINATE.** Not a failure. `plugin_attributable_count` is **0** in
every delta of both phases, and both structural gates PASS. What blocks a verdict is ten
processes — nine of them Windows system processes whose command lines the operating system
refused to disclose to an unelevated observer.

Artifacts: `nfr1-cold-final.json`, `nfr1-warm-final.json`, `nfr1-report.json`.

---

## 1. What was measured

PRD NFR-1, as revised at Phase 2.1: *with the plugin installed but not invoked, an OS-level
process count is taken immediately before and after 10 tool calls in a fresh session,
attributed per component. Pass = 0 processes attributable to the plugin.*

Plugin: `claude-workflow-engine` v0.1.0, installed from the local marketplace
`techdeveloper-org` and confirmed loaded — its eleven skills were live in the measuring
session. Zero bundled hooks (ADR-010), zero bundled MCP servers (ADR-019).

## 2. Result

| | cold | warm |
|---|---|---|
| tool calls recorded | 10 / 10 | 10 / 10 |
| turn boundary | CLEAN (all three witnesses silent) | CLEAN |
| window | 247.3 s | 245.7 s |
| processes observed | 56 | 52 |
| **attributable to the plugin** | **0** | **0** |
| shown not to descend from the plugin | 5 | 1 |
| unknown | 6 | 4 |

Structural gates: **PASS** — `adr019_no_bundled_mcp`, `adr010_no_bundled_hooks`.

Cold and warm are reported as two numbers and never blended; the report exposes no combined
figure, because averaging a cold count with a warm one describes neither.

## 3. What blocks a PASS

All ten, itemised:

| phase | process | why unknown |
|---|---|---|
| cold | `WmiApSrv.exe`, `WmiPrvSE.exe` | access denied |
| cold | `esrv_svc.exe` (Intel) | access denied |
| cold | `timeout.exe`, `cmd.exe`, `conhost.exe` | access denied |
| warm | `MoUsoCoreWorker.exe` (Windows Update) | access denied |
| warm | `svchost.exe`, `WmiPrvSE.exe` | access denied |
| warm | `backgroundTaskHost.exe` | ancestry chain broke |

Nine of ten are a **permissions** limit, not a measurement defect: an unelevated process
cannot read the command line of a process owned by SYSTEM or another user, so the harness
cannot show they are not the plugin's, and it refuses to assume.

**A PASS is therefore one elevated run away.** Running the observer as Administrator should
resolve all nine. That is worth attempting before any amendment to the criterion, because if
it succeeds no amendment is needed.

## 4. What had to be fixed before this number could be trusted

Every item below was found by attempting a real measurement. None was found by review.

| Defect | Effect if unfixed |
|---|---|
| Plugin markers normalised to forward slashes, process text left with backslashes | Plugin markers could **never match a Windows process**; `plugin_count` was structurally 0 |
| A broad marker could direct-match before the ancestry walk | A plugin-spawned shell could be charged elsewhere, silently |
| The bare word `plugin` derived from the root's basename | Unrelated software charged to the plugin — false FAILs |
| Ancestry index built from endpoints while records came from the sampler | Short-lived parents missing; 63 processes unknown with usable parent ids |
| "Unknown" conflated with "shown not to be the plugin" | Verdict unreachable on any machine running other software |
| The proof granted to a process whose own identity was unreadable | `--self-test` returned PASS where it must return FAIL |
| Anchoring at the newest assistant record | Landed past the whole batch: 0 counted, full budget burned |
| Counting `tool_use` rather than `tool_result` | Window closed in **0.19 s**, bracketing none of the execution |

Recorded in full as corrections 55–71 in `docs/REVIEW-INDEX.md`.

## 5. A finding outside NFR-1

The pre-fix cold run reported 79 unknowns. **53 were the operator's own shell profile.**
`~/.bashrc` contained `source <(ng completion script)`, which invoked the Angular CLI on every
shell startup and spawned six processes — `sh -> node -> cmd -> node -> cmd -> node`, running
`npm --version` and `npm-prefix.js`.

Claude Code starts a fresh shell per tool call, so every tool call paid it.

| | before | after |
|---|---|---|
| interactive shell startup | 2929 ms | 375 ms |
| processes per shell | 6 | 0 |
| `ng` tab-completion | works | still works |

Replaced with a cached completion script. The measurement did not merely tolerate this noise —
it located a latency cost paid on every tool call of every session.

## 6. Closure status

`harness.py` carries the issue's own closure condition:

> *"This issue cannot close on a harness that has never produced a pass."*

| Condition | Status |
|---|---|
| V2-015 — a plugin exists and is installed | **met** |
| V2-027 — hook registrations deleted | **met** |
| Cold and warm both reported | **met** — this is the first run where both exist |
| A PASS has been produced | **not met** |

Three of four conditions are now satisfied. The fourth is blocked by nine access-denied system
processes, and the recommended next step is an elevated run rather than an amendment.

## 7. Amendment, and closure of #259

**Ruled by the requirement owner on 2026-08-06. Recorded here rather than inferred.**

The elevated run was **declined**, and the reasoning is sound: requiring Administrator rights
is neither practical nor safe in a normal or corporate development environment, so a criterion
that can only be satisfied under elevation is a criterion most engineers could never verify.

**A PASS was not produced, and this amendment does not pretend otherwise.** Both phases are
INDETERMINATE. What the owner ruled is that NFR-1's *question* has been answered:

> Does an installed but uninvoked plugin spawn processes?

Answered by `plugin_attributable_count = 0` across every delta of both phases, with both
structural gates PASS and both windows valid. Processes the operating system refuses to
describe are **outside the criterion's reach, not evidence against it** — a permanent property
of unelevated measurement on Windows, not a pending task.

`harness.py`'s `closure_note` now carries both halves: the original bar, and this amendment.
Two tests pin it so a later rewrite cannot quietly erase the fact that the bar went unmet.

**What this closure does not claim:**

- It does not claim a PASS.
- It does not claim every process in the window was identified — ten were not.
- It does not claim the criterion is satisfiable as originally written on an unelevated
  Windows machine. On the present evidence it is not, and that is the reason for the
  amendment rather than a footnote to it.

**What it does claim,** and what the evidence supports: the plugin contributes zero processes
to a session that has installed it and not invoked it, measured twice, under conditions the
harness itself certifies as valid.
