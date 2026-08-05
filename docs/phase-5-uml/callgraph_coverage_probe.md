# CallGraph Coverage Probe (Phase 5, UML)

**Scope:** read-only measurement of the CallGraph builder's own discovery limits.
**Source files modified:** 0. The two artifacts in `docs/phase-5-uml/` are the only writes.
**Method:** the builder was instantiated in-process and run. Every number below is labelled
MEASURED (observed at runtime, or observed by exhaustive static enumeration) or INFERRED.
No probe output was sliced, sampled, or head-limited; the manifest lists every discovered
path and every absent path in full.

---

## 1. Truncation sites: 4 file-count cap files, not "four plus a fifth"

The Phase 1 claim under test was: *the cap is duplicated across four files, plus a fifth
different-class truncator.*

**Verdict: the four-file part is CONFIRMED. The "fifth" part undercounts - there are two
different-class truncators, not one. The claim also omits two graph-traversal caps, one of
which binds even after the file cap is lifted.**

The enumeration below is exhaustive for project code. It comes from a repo-wide grep over
`*.py` excluding `.venv/`, for both `MAX_FILES`-style declarations and `max_files` parameter
defaults. Third-party hits inside `.venv/Lib/site-packages/starlette/` were excluded as
not-our-code.

### 1.1 File-count caps on call-graph / AST discovery (4 files) - MEASURED-STATIC

| ID | File:line | Constant | Value | Live? |
|----|-----------|----------|-------|-------|
| FC-1 | `langgraph_engine/parsers/config.py:11` | `MAX_FILES` | 300 | **No** |
| FC-2 | `langgraph_engine/parsers/call_graph_builder_legacy.py:64` | `MAX_FILES` | 300 | **Yes - this is the one that binds** |
| FC-3 | `langgraph_engine/sdlc_pipeline/architecture/00-code-graph-analysis/code_graph_analyzer.py:73` | `MAX_FILES` | 500 | No (dormant duplicate) |
| FC-4 | `scripts/architecture/03-execution-system/00-code-graph-analysis/code-graph-analyzer.py:68` | `MAX_FILES` | 500 | Yes, but not on the UML path |

Notes that matter more than the count:

- **FC-1 is dead.** `config.py`'s docstring says it "centralises all limits ... so that
  CallGraphBuilder and each language parser read from a single source of truth." That is
  false. The only importer repo-wide is `langgraph_engine/parsers/__init__.py:22`, which
  re-exports it through `__all__`. Nothing reads it. Editing `config.py:11` would change
  nothing. The cap that actually binds is the duplicate at
  `call_graph_builder_legacy.py:64`, enforced at lines 107 and 118 of the same file.
- **FC-3 has no importers.** A repo-wide grep for `code_graph_analyzer` finds only
  self-references plus tests pointing at the `scripts/` copy.
- **FC-4 is live** - loaded by `importlib` at
  `langgraph_engine/analysis/complexity_calculator.py:366-373` - but at 500 it is above the
  411 files on disk, so it does not truncate anything today. It is also not on the UML path.

### 1.2 File-size caps (4 files, same distribution) - MEASURED-STATIC

`MAX_FILE_SIZE_KB = 100` appears at `parsers/config.py:14`,
`parsers/call_graph_builder_legacy.py:65` (live, enforced at line 113),
`sdlc_pipeline/architecture/00-code-graph-analysis/code_graph_analyzer.py:74`, and
`scripts/architecture/03-execution-system/00-code-graph-analysis/code-graph-analyzer.py:69`.

MEASURED impact today: **zero**. No source file in the repo exceeds 100 KB. These caps are
latent, not active.

### 1.3 Graph-traversal caps the claim did not mention (2 sites) - MEASURED

| ID | File:line | Constant | Value | Env override | Binds today? |
|----|-----------|----------|-------|--------------|--------------|
| GT-1 | `langgraph_engine/parsers/graph_model.py:42` | `DEFAULT_MAX_DEPTH` | 30 | `CLAUDE_CG_MAX_DEPTH` | No |
| GT-2 | `langgraph_engine/parsers/graph_model.py:43` | `DEFAULT_MAX_PATHS` | 500 | `CLAUDE_CG_MAX_PATHS` | **Yes** |

GT-1 does not bind: observed `max_call_depth` was 11 (truncated run) and 7 (unbounded run).

GT-2 **does** bind, and this is the finding that survives lifting the file cap. Both probe
runs emitted, verbatim:

```
compute_call_paths: hit max_paths=500 limit; results truncated.
Increase via CLAUDE_CG_MAX_PATHS env var or pass max_paths kwarg.
```

Any sequence or interaction diagram built from `compute_call_paths()` is truncated at 500
paths regardless of how many files were ingested.

### 1.4 Different-class truncators (2, not 1) - MEASURED-STATIC

| ID | File:line | Constants | What it actually bounds |
|----|-----------|-----------|-------------------------|
| DC-1 | `langgraph_engine/build_dependency_resolver/parsers.py:681-682` | `max_depth = 4`, `max_files_scanned = 1000` | BFS in `_dir_has_code_uncached()` answering "does this directory contain source" |
| DC-2 | `langgraph_engine/sdlc_pipeline/code_explorer.py:453` | `max_files = 3` | `extract_code_snippets()` - first 15 lines of at most 3 files, for LLM context |

Neither participates in call-graph construction.

### 1.5 Downstream diagram truncators (5 sites) - MEASURED-STATIC

These sit after discovery and cap what reaches a rendered diagram. Listed because rule
45 governs diagram fidelity, but they are not discovery limits:

- `diagrams/sequence_diagram.py:171-172` - `chains[:20]` per file, break at 80 total
- `diagrams/interaction_diagram.py:76-77` - `chains[:10]` per file, break at 40 total
- `diagrams/legacy_generator.py:414-415` - `chains[:20]`, break at 80
- `diagrams/legacy_generator.py:740-741` - `chains[:10]`, break at 40
- `diagrams/drawio/drawio_converter_enriched.py:270, 403, 611` - `max_styled_nodes` 200

**Total distinct truncation sites enumerated: 17** (4 file-count + 4 file-size +
2 traversal + 2 different-class + 5 diagram-level).

---

## 2. The actual discovery set - MEASURED-RUNTIME

The builder **was run**. `CallGraphBuilder._discover_files()` and `.build()` were called
in-process against the project root, twice: once at the default cap, once with the cap
lifted via a constructor argument.

| | Truncated (shipping default) | Complete (cap lifted) |
|---|---|---|
| Files ingested | **300** | **411** |
| Classes | 449 | 480 |
| Methods | 2,844 | 3,506 |
| Functions | 887 | 1,340 |
| Call edges | 18,098 | 26,114 |
| Resolved edges | 4,908 | 7,004 |

**111 files - 27 percent of the codebase - are invisible to the shipping builder.**
18.9 percent of methods are missing from it.

On disk: 411 source files, **all `.py`**. Zero `.java`, `.ts`, `.tsx`, `.kt`.

### 2.1 Package coverage

| Top package | In truncated scope | On disk | Missing |
|---|---|---|---|
| `langgraph_engine` | 164 | 237 | 73 |
| `tests` | 75 | 75 | 0 |
| `scripts` | 37 | 37 | 0 |
| `src` | 16 | 16 | 0 |
| `hooks` | 7 | 45 | **38** |
| repo root | 1 | 1 | 0 |

**Fully absent subtrees** (0 files in scope):

- `langgraph_engine/sdlc_pipeline` - **45 of 45 files absent**. This is the entire Level 2
  SDLC Execution Core.
- `hooks/pre_tool_enforcer` - 21 of 21 absent
- `hooks/post_tool_tracker` - 12 of 12 absent
- `hooks/stop_notifier` - 5 of 5 absent
- `langgraph_engine/state` - 5 of 5 absent (FlowState, StepKeys, reducers)
- `langgraph_engine/skills` - 4 of 4 absent
- `langgraph_engine/standards` - 4 of 4 absent
- `langgraph_engine/security` - 2 of 2 absent

**Partially absent:** `langgraph_engine/diagrams` (19 of 24), `langgraph_engine/context_sync`
(8 of 12), `langgraph_engine/runtime_verification` (4 of 8).

**Fully in scope:** all of `tests/` (75 files, **25 percent of the entire budget**),
`scripts/`, `src/`, and roughly 20 other `langgraph_engine` subpackages.

This reproduces the prior finding exactly: sdlc_pipeline 100 percent invisible, 38 of 45
hook files invisible, 25 percent of budget on tests.

### 2.2 Why the boundary falls where it does - MEASURED-RUNTIME

Discovery is `project_root.glob("**/*.py")` with a running counter. Measured indices in the
full (unbounded) traversal order:

- index 72: first `tests/` file - so all 75 test files are admitted early
- index 299 (the last file admitted): `langgraph_engine/runtime_verification/node_contracts.py`
- index 304: **first `langgraph_engine/sdlc_pipeline/` file**
- index 378: first `hooks/pre_tool_enforcer/` file

The 300-file budget is exhausted **five files before the sdlc_pipeline tree begins**. This
is not a considered exclusion; it is an alphabetical accident. A cap of 310 would admit the
first few sdlc_pipeline files and change nothing else.

---

## 3. The decisive question: yes, a read-only override exists

All four candidate mechanisms were **executed against the live builder**, not reasoned about.
Two work, two do not. The two negative results are as important as the positives.

| Mechanism | Works? | Files discovered |
|---|---|---|
| Environment variable (`CALLGRAPH_MAX_FILES`, `MAX_FILES`, `CLAUDE_CG_MAX_FILES` all set to 99999) | **No** | 300 |
| Constructor kwarg `CallGraphBuilder(root, max_files=N)` | **Yes** | 411 |
| Rebinding the module global `legacy.MAX_FILES = N` | **No** | 300 |
| Patching `CallGraphBuilder.__init__.__defaults__ = (N,)` | **Yes** | 411 |

**No environment variable exists for the file cap.** The only `os.environ` read anywhere in
`langgraph_engine/parsers/` is `graph_model.py:33`, which serves `CLAUDE_CG_MAX_DEPTH` and
`CLAUDE_CG_MAX_PATHS` only. Setting three plausibly-named vars to 99999 left discovery at
exactly 300.

**Rebinding the module attribute silently does nothing.** `max_files=MAX_FILES` at
`call_graph_builder_legacy.py:76` binds the default at function-definition time, so
`legacy.MAX_FILES = 99999` is ignored. This is the trap: it looks like it worked, and it
does not. Measured, 300.

### 3.1 Demonstrated invocation

The constructor argument is sufficient if you drive the builder yourself:

```python
from langgraph_engine.parsers.call_graph_builder_legacy import CallGraphBuilder
graph = CallGraphBuilder(project_root, max_files=10**9).build()
# MEASURED: files_analyzed=411, total_classes=480, total_methods=3506
```

It is **not** sufficient for the UML path. `diagrams/legacy_generator.py:93` calls
`build_call_graph(str(self.project_root))`, and `build_call_graph()` at
`call_graph_builder_legacy.py:682` constructs `CallGraphBuilder(project_path)` with no
`max_files`. To widen the diagram generators without editing source, patch the default:

```python
import langgraph_engine.parsers.call_graph_builder_legacy as legacy
legacy.CallGraphBuilder.__init__.__defaults__ = (10**9,)
# MEASURED: build_call_graph(root) -> files_analyzed=411, classes=480, methods=3506
```

Pair it with `CLAUDE_CG_MAX_PATHS` to lift GT-2, which otherwise still truncates call-path
enumeration at 500 even on the full file set.

**Answer: yes. No source edit is required for a read-only documentation pass.**

---

## 4. CLAUDE.md's 578 classes / 3,985 methods was measured COMPLETE - and is now stale

**Verdict: the published figure was an untruncated measurement when it was written. It is
not a truncated number. It is simply out of date, and its "4 languages" qualifier was never
true.**

Evidence (MEASURED-RUNTIME, not inferred):

1. `git log -S "3,985" -- CLAUDE.md` identifies commit **ab54428** as the first commit
   introducing the figure into CLAUDE.md.
2. `git ls-tree -r` at that commit: **226 `.py` files, 0 `.java`/`.ts`/`.tsx`/`.kt` files.**
3. 226 is below the 300 cap, so truncation was structurally impossible at that commit.
4. That tree was exported with `git archive` into a scratch directory (no worktree, no
   checkout, repo untouched) and the builder was run against it at both caps:

```
default300  files=226 classes=579 methods=3992 functions=1265
unbounded   files=226 classes=579 methods=3992 functions=1265
```

Identical at both caps, as predicted. **579 classes / 3,992 methods** lands within 1 class
and 7 methods of the published **578 / 3,985** - close enough to identify the published
number as a complete measurement of a near-neighbour commit.

Two consequences:

- **The figure is stale, and stale downward.** The complete measurement today is
  **480 classes / 3,506 methods**, despite the file count nearly doubling from 226 to 411.
  The v1.15-v1.20 refactors deleted more class surface than they added. Anyone comparing
  today's output to the documented 578/3,985 will conclude the builder regressed; it did
  not, the documentation did.
- **What the pipeline actually consumes is 449 classes / 2,844 methods** - the truncated
  figure. CLAUDE.md publishes a number that is neither what the builder can see nor what it
  does see.

The "4 languages (Python/Java/TS/Kotlin)" qualifier is **false at both timestamps**: zero
non-Python source files existed at commit ab54428 and zero exist today. The builder
*supports* four languages; the graph has only ever contained one.

Affected documentation: `CLAUDE.md:25`, `CLAUDE.md:248`, `CHANGELOG.md:433`,
`docs/architecture/ADR-002-call-graph-intelligence.md:51` and `:96`,
`docs/architecture/PIPELINE_ARCHITECTURE.md:137` and `:212`.

---

## 5. Consequence for rule 45

Rule 45 section 6 makes CallGraph the primary source for class, package, component, and
sequence diagrams, with AST direct scan as fallback #3. Measured:

- Under the shipping default, those four structural diagrams cannot depict
  `langgraph_engine/sdlc_pipeline/` at all - the 45-file Level 2 SDLC Execution Core, which
  is the subsystem the diagrams most need to show. Nor `langgraph_engine/state/` (FlowState,
  StepKeys), nor 38 of 45 hook files.
- The AST fallback is **not** subject to the file cap:
  `diagrams/ast_analyzer.py:152` and `:193` use an uncapped `rglob("*.py")`. So the fallback
  path sees more of the codebase than the primary path rule 45 mandates. That inversion is
  worth flagging separately.
- GT-2 (`max_paths=500`) still truncates sequence-diagram input after any file-cap fix.

---

## 6. What could not be determined

- Whether the external `mcp-uml-diagram` server repo applies its own independent cap. That
  repo is not on this filesystem and was not probed.
- Whether the 300 cap has a runtime-budget justification. No timing measurement was taken
  beyond noting that both the truncated and the unbounded build completed without timing out.
- The exact commit the published 578/3,985 was measured on. ab54428 yields 579/3,992 -
  adjacent but not identical. The parent commits were not bisected; one commit either side
  would almost certainly land exactly.
- Runtime behaviour of FC-3 and FC-4 (`MAX_FILES = 500`) under a codebase larger than 500
  files. Both were assessed statically only; neither binds at 411 files.
