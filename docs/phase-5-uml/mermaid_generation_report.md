# Mermaid Generation Report (Phase 5, UML)

**Scope:** generation of all 13 Mermaid UML diagram types per
`rules/45-uml-diagram-lifecycle.md` into `uml/` at project root.
**Source files modified:** 0. Writes are the 13 files in `uml/` plus this report.
**Diagram types generated:** 13 of 13. **Skipped:** 0.

---

## 1. Graph verification

The default CallGraph is truncated at 300 of 411 files and would have omitted all 45
files of `langgraph_engine/sdlc_pipeline/`. It was not used. The read-only override
documented in `callgraph_coverage_probe.md` section 3.1 was applied in-process:

```python
legacy.CallGraphBuilder.__init__.__defaults__ = (10 ** 9,)
os.environ["CLAUDE_CG_MAX_PATHS"] = "200000"
os.environ["CLAUDE_CG_MAX_DEPTH"] = "60"
```

No source file was edited. The module-global rebinding trap
(`legacy.MAX_FILES = N`, which silently does nothing) was not used.

### MEASURED totals obtained

| Metric | Probe target | This run | Match |
|---|---|---|---|
| files_analyzed | 411 | **411** | yes |
| total_classes | 480 | **480** | yes |
| total_methods | 3506 | **3506** | yes |
| total_functions | 1340 | 1340 | yes |
| total_call_edges | 26114 | 26114 | yes |
| total_inheritance_edges | 75 | 75 | yes |
| resolved_edges | 7004 | 7004 | yes |
| avg_cyclomatic | 4.43 | 4.43 | yes |
| max_cyclomatic | 107 | 107 | yes |
| max_call_depth | 7 | **11** | no - explained below |

`max_call_depth` is the only divergence. It is not a discrepancy in the graph: this run
raised `CLAUDE_CG_MAX_PATHS` from 500 to 200000, so `compute_call_paths()` enumerated
deeper chains before hitting its cap. Depth is a function of how many paths were
enumerated, not of the file set. The three verification figures named in the task
(411 / 480 / 3506) matched exactly.

Independent cross-check: an `os.walk` of the repository excluding the builder's
`EXCLUDED_DIRS` counted **411** `.py` files in 57 directories, confirming the builder
discovered every file on disk and dropped none to the file-size cap.

### Language mix (MEASURED, by extension over all 411 discovered files)

| Extension | Count |
|---|---|
| `.py` | 411 |
| `.java` | 0 |
| `.ts` | 0 |
| `.tsx` | 0 |
| `.kt` | 0 |

The project documentation's claim that the CallGraph covers "4 languages
(Python/Java/TS/Kotlin)" was **not reproduced** in any diagram. It describes parser
capability, not graph content. No multi-language structure was drawn.

---

## 2. Edge confidence grading

The builder resolves call targets by simple name. Unqualified calls to builtin
container and string methods therefore bind onto same-named user methods, producing
edges that do not exist. Before grading, the apparent highest fan-in method in the
codebase was `src/mcp/base/persistence.py::JsonlAppender.append` at **1592** incoming
edges - i.e. every `list.append()` call in the repository - followed by
`ErrorMessages.format` at 756 (every `str.format()`) and `_MemoryLayer.get/set` at
111/162 (every `dict.get()`).

Publishing those as architectural hot nodes would have been a fabrication. All 26114
call edges were graded:

| Class | Count | Used in diagrams |
|---|---|---|
| unresolved (target is not a known project method) | 18608 | no |
| dropped: target simple name collides with a builtin method name | 2853 | no |
| dropped: multiple same-name candidates resolved across files | 433 | no |
| **high-confidence** | **4220** | **yes** |

Every call, package and class relationship in the 13 diagrams is drawn from the 4220
high-confidence edges. Inheritance edges (75) are AST-direct and were not graded, only
normalised: the resolver rewrites `Base` to `Base.__init__` on 6 edges, which was
undone.

---

## 3. Per-diagram record

Node counts below were measured by parsing the emitted Mermaid blocks, not asserted.
"Containers" are `subgraph` grouping boxes. Rule 45 section 4.1 caps at 50.

| # | File | Nodes | Containers | Total | Truncated | Truncation criterion | Data source |
|---|---|---|---|---|---|---|---|
| 1 | `class_diagram.md` | 42 | 0 | 42 | no | n/a - complete set for its criterion | CallGraph inheritance edges (priority 1) |
| 2 | `package_diagram.md` | 42 | 4 | 46 | no | n/a | CallGraph high-confidence cross-package edges |
| 3 | `component_diagram.md` | 32 | 6 | 38 | no | n/a | CallGraph package structure + Dockerfile/k8s + `integrations/` |
| 4 | `sequence_diagram.md` | 8 | 0 | 8 | no | n/a | CallGraph edges, cross-checked against source lines |
| 5 | `state_diagram.md` | 8 | 0 | 8 | no | n/a | AST: `IntegrationState` enum + all `self._state` assignment sites |
| 6 | `activity_diagram.md` | 34 | 0 | 34 | no | n/a | Direct source read of `create_flow_graph()` |
| 7 | `deployment_diagram.md` | 17 | 6 | 23 | no | n/a | `Dockerfile`, `docker-compose.yml`, 5 `k8s/*.yaml` |
| 8 | `usecase_diagram.md` | 17 | 1 | 18 | no | n/a | MEASURED entry points (`__main__` / argparse) |
| 9 | `object_diagram.md` | 12 | 0 | 12 | no | n/a | MEASURED runtime snapshot of both builder runs |
| 10 | `composite_diagram.md` | 31 | 6 | 37 | no | n/a | CallGraph method inventory + `__init__` source read |
| 11 | `interaction_diagram.md` | 22 | 0 | 22 | no | n/a | `create_flow_graph()` topology + cross-package edge weights |
| 12 | `communication_diagram.md` | 10 | 0 | 10 | no | n/a | CallGraph high-confidence class-to-class edges |
| 13 | `call_graph_diagram.md` | 32 | 7 | 39 | **yes** | Top 30 of 3506 methods by MEASURED high-confidence fan-in, tests excluded; plus 2 supporting nodes to make the bootstrap path visible | CallGraph |

Only diagram 13 required truncation. Its `%% Truncated:` notice is carried inside the
Mermaid block so it travels with the rendered artifact, and it names the ranking metric
rather than saying "top 50" without a criterion.

Where a diagram is marked "not truncated", the selection criterion is stated in the
file itself and is a closed set (for example: all classes in an inheritance hierarchy,
all nodes in the compiled pipeline graph, all objects declared in the k8s manifests).
Two diagrams are narrower than their nominal universe *by construction* and say so:
`package_diagram.md` covers the 42 of 53 production packages that have at least one
measured cross-package call edge, and `class_diagram.md` covers 40 of the 48 production
classes that participate in inheritance.

### Format compliance (verified programmatically)

All 13 files: exact rule 45 filename, ASCII-only bytes (0 non-ASCII in any file),
opening comment `<!-- Generated by pipeline Step 13 -- do not edit manually -->`,
exactly one fenced block opened with a triple-backtick `mermaid` fence, and no
timestamps or version suffixes in filenames.

---

## 4. Findings surfaced during generation

These are byproducts of building the diagrams honestly. None blocked generation.

1. **`uml/` and `drawio/` are not gitignored.** Rule 45 section 2 states "Never commit
   generated diagram files to Git (add both dirs to `.gitignore`)". A grep of
   `.gitignore` for `uml`/`drawio` returns nothing. The 13 files just written are
   therefore committable. `.gitignore` was **not** modified by this pass; adding the two
   entries is a required follow-up.

2. **`DrawioConverter` supports 12 types, rule 45 requires 13.** MEASURED:
   `DrawioConverter.SUPPORTED_TYPES` = `class, sequence, activity, state, component,
   package, deployment, usecase, object, communication, composite, interaction`. There
   is no `call_graph` entry, so `_generate_drawio_diagrams()` can never produce
   `drawio/call_graph_diagram.drawio`.

3. **`AbstractDiagramGenerator` has 12 subclasses, not 13.** The call-graph type is
   produced by `UMLDiagramGenerator.generate_call_graph_diagram()`, which sits outside
   that hierarchy. The same type is the one missing from the draw.io converter.

4. **`UMLDiagramGenerator` exposes 15 `generate_*` methods for 13 rule-45 types.**
   `generate_timing_diagram` and `generate_uml_from_code` have no rule-45 filename;
   `generate_all()` calls only 13 of the 15.

5. **`_generate_drawio_diagrams()` is invisible to the CallGraph.** It imports
   `DrawioConverter` lazily inside the method body
   (`sdlc_pipeline/documentation_manager.py:310`), and the AST builder does not resolve
   calls through function-local imports. The `documentation_manager -> DrawioConverter`
   relation is real but absent from the graph; it is drawn in
   `communication_diagram.md` with that gap flagged.

6. **k8s manifests are pinned to version 1.6.1.** `k8s/deployment.yaml` sets
   `image: workflow-engine:1.6.1` and `version: "1.6.1"` while `CLAUDE.md` declares the
   project at 1.21.4.

7. **`on_branch()` performs no state transition.** Both `GitHubIntegration` and
   `JiraIntegration` implement it, neither assigns `self._state`. Step 3 of the
   pipeline has no corresponding `IntegrationState` transition.

8. **`JenkinsIntegration` and `FigmaIntegration` never advance state.** Both are
   `AbstractIntegration` subclasses with zero `self._state` assignments; they inherit
   the base initialisation to `DISABLED` and stay there.

9. **77 cyclomatic points are spent on languages this repo does not contain.**
   `CallGraphBuilder._analyze_typescript` (cx 37), `_analyze_java` (21) and
   `_analyze_kotlin` (19) are among the most complex methods in the codebase and cannot
   execute here.

10. **The deployed configuration runs the smaller graph.** `k8s/configmap.yaml` sets
    `CLAUDE_HOOK_MODE: "1"`, so the pod compiles the 18-node hook-mode graph, not the
    27-node full-mode graph.

---

## 5. What could not be verified

- **The 12 external MCP servers.** `CLAUDE.md` documents 13 MCP servers; only
  `src/mcp/` is present on this filesystem. The other 12 live in separate repositories
  that were not read. They are deliberately absent from `component_diagram.md` rather
  than drawn on documentation alone.
- **Hook registration.** The binding of `hooks/pre-tool-enforcer.py`,
  `post-tool-tracker.py` and `stop-notifier.py` to Claude Code lifecycle events lives in
  `~/.claude/settings.json`, outside this repository. It was not read. Those
  actor-to-use-case arrows in `usecase_diagram.md` are labelled MEASURED-BY-DOC.
- **Actor bindings generally.** Which human or machine invokes a given entry point is
  not recoverable from an AST. Every binding in `usecase_diagram.md` is individually
  labelled MEASURED, MEASURED-BY-DOC, or INFERRED.
- **Rendering.** The 13 Mermaid blocks were validated structurally (fence integrity,
  node counting via a parser, GitHub-compatible constructs only, no Kroki-only
  extensions). They were **not** rendered by a Mermaid engine; no renderer was
  available offline in this environment.
- **Whether the 4220-edge high-confidence set is itself complete.** The grading removes
  false positives. It does not recover the 18608 unresolved edges, some unknown fraction
  of which are real project calls the name-based resolver failed to bind. Coupling
  weights in `package_diagram.md` and `interaction_diagram.md` are therefore lower
  bounds, not exact counts.
