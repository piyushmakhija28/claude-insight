# Draw.io Diagram Generation Report (Phase 5, UML)

**Scope:** rule 45 (`45-uml-diagram-lifecycle.md`) draw.io deliverable -- 13 editable
`.drawio` files in `{project_root}/drawio/`.
**Source files modified:** 0. Writes are confined to `drawio/*.drawio` and this report.
**Result:** **13 of 13 generated, 13 of 13 XML-validated, 0 skipped.**

Every number below is labelled MEASURED (observed at runtime or by exhaustive
enumeration) or INFERRED. No count is stated that cannot be re-derived from the
extraction described in section 2.

---

## 1. Graph verification gate

The task required confirming the probe's complete figures before generating anything.

| Quantity | Probe (expected) | This run (observed) | Match |
|---|---|---|---|
| Files ingested | 411 | **411** | yes |
| Classes | 480 | **480** | yes |
| Methods | 3,506 | **3,506** | yes |

Full `get_stats()` from this run, MEASURED-RUNTIME:

```
total_classes 480   total_methods 3506   total_functions 1340
total_call_edges 26114   total_inheritance_edges 75
resolved_edges 7004   unresolved_edges 19110
files_analyzed 411   max_call_depth 11
avg_cyclomatic 4.43   max_cyclomatic 107
```

The gate passed, so generation proceeded.

`max_call_depth` reads 11 here versus 7 in the probe's unbounded run. That is not a
discrepancy in the three gated figures: this run raised `CLAUDE_CG_MAX_PATHS` to 20000
and `CLAUDE_CG_MAX_DEPTH` to 60, so `compute_call_paths()` explored past the GT-2
`max_paths=500` ceiling that truncated the probe's traversal. Class, method and file
counts are unaffected by traversal limits and matched exactly.

### 1.1 Language claim

MEASURED: all 411 discovered source files are `.py`. The graph contains
**480 classes across `.py` files only; 0 `.java`, `.ts`, `.tsx`, `.kt`**. The
"4 languages (Python/Java/TS/Kotlin)" claim in `CLAUDE.md:25` is not reproduced in any
diagram. Where the four registered parsers appear (object diagram), each is annotated
with its measured input file count -- `PythonASTParser -> 411 files`, the other three
`-> 0 files`.

---

## 2. Data acquisition (read-only)

```python
os.environ["CLAUDE_CG_MAX_PATHS"] = "20000"
os.environ["CLAUDE_CG_MAX_DEPTH"] = "60"
import langgraph_engine.parsers.call_graph_builder_legacy as legacy
legacy.CallGraphBuilder.__init__.__defaults__ = (10 ** 9,)   # probe-demonstrated override
graph = legacy.build_call_graph(ROOT)
```

No source file was edited. The module-global `MAX_FILES` was **not** rebound (the probe
proved that a no-op, and this run did not rely on it).

A second, independent extraction pass was run over the same 411 files: a direct
`ast.parse` of every file collecting `Import` / `ImportFrom` nodes.
MEASURED: **2,651 import statements parsed, 0 parse failures across all 411 files**;
791 of those resolve to an internal module, 1,860 are stdlib/third-party.

---

## 3. Two corrections made during generation

Both were found by verification, not assumed. They changed which data reached the
diagrams, so they are recorded here.

### 3.1 `graph.edges` is the raw edge list, not the resolved one

`CallGraph.resolve_edges()` stores its output in `self._resolved_edges` and returns it;
it does **not** mutate `self.edges`. An extraction that dumps `graph.edges` therefore
gets unresolved targets. Measured effect: 656 apparently-resolved edges from
`graph.edges` versus **7,004** from `graph.get_edges()`. All diagrams here use
`get_edges()`.

### 3.2 55.5 percent of cross-file "resolved" call edges are name-collision artifacts

`CallGraph._resolve_target()` prefers a same-file match, then accepts a unique
candidate, then falls back to `candidates[0]` on ambiguity. Because callee names are
matched as bare simple names, ubiquitous method names resolve to whichever project
method happens to share the name.

MEASURED over the resolved set:

| | count |
|---|---|
| resolved non-inheritance edges | 7,004 |
| of those, cross-file | 5,087 |
| cross-file whose callee simple name is a generic/builtin name | **2,823 (55.5 %)** |

Top offenders, MEASURED: `append` 1,590, `format` 754, `__init__` 262, `set` 157,
`get` 103, `exists` 67. The consequence is that
`src/mcp/base/persistence.py::JsonlAppender.append` carries an in-degree of **1,592**
and appears to be the most-called method in the system. It is not: those are
`list.append` calls. Cross-package edge weights derived from this set are equally
polluted -- five of the top six cross-package pairs point at `src/mcp`.

**Therefore:** package and component structure in these diagrams is derived from the
**AST import graph** (exact), not from resolved call edges. The call graph diagram uses
the resolved set only after excluding generic callee names and test-side endpoints,
which leaves **932 edges over 280 distinct file pairs** (from 5,087). This is stated on
the diagram itself so a reader cannot mistake the filtering for completeness.

---

## 4. Per-diagram record

Element count = `mxCell` entries with `vertex="1"` or `edge="1"` (excludes the two
structural cells `id=0` and `id=1`). All 13 parsed clean.

| # | File | Vertices | Edges | Elements | Bytes | XML parse | Primary data source |
|---|---|---|---|---|---|---|---|
| 1 | `class_diagram.drawio` | 116 | 30 | **146** | 55,638 | PASS | CallGraph declared bases + method counts |
| 2 | `package_diagram.drawio` | 53 | 24 | **77** | 29,680 | PASS | AST import graph + measured package sizes |
| 3 | `component_diagram.drawio` | 40 | 29 | **69** | 21,101 | PASS | Package sizes + measured subclass sets |
| 4 | `sequence_diagram.drawio` | 11 | 28 | **39** | 15,410 | PASS | `orchestrator.create_flow_graph()` edge order |
| 5 | `state_diagram.drawio` | 34 | 34 | **68** | 19,825 | PASS | `create_flow_graph()` nodes + conditional routers |
| 6 | `activity_diagram.drawio` | 28 | 30 | **58** | 16,201 | PASS | `create_flow_graph()` routers + fork/join |
| 7 | `deployment_diagram.drawio` | 21 | 9 | **30** | 10,508 | PASS | `k8s/*.yaml`, `Dockerfile`, `docker-compose.yml` |
| 8 | `usecase_diagram.drawio` | 20 | 14 | **34** | 9,868 | PASS | Measured entry-point file listing |
| 9 | `object_diagram.drawio` | 56 | 4 | **60** | 24,258 | PASS | Two real `CallGraph` instances' `get_stats()` |
| 10 | `composite_diagram.drawio` | 33 | 6 | **39** | 12,384 | PASS | `UMLDiagramGenerator` measured members + cc |
| 11 | `interaction_diagram.drawio` | 14 | 12 | **26** | 8,960 | PASS | Level node counts + package sizes |
| 12 | `communication_diagram.drawio` | 13 | 16 | **29** | 9,405 | PASS | Import edges + filtered call edges |
| 13 | `call_graph_diagram.drawio` | 45 | 11 | **56** | 19,820 | PASS | Filtered resolved call edges |

**Totals: 484 vertices, 247 edges, 731 elements. 13 PASS, 0 FAIL, 0 skipped.**

### 4.1 Validation performed on every file

Applied per file; any failure would delete the file and mark the type SKIPPED
(rule 45 section 7). None triggered.

1. Re-parse with `xml.etree.ElementTree` -- well-formedness.
2. Root element is `mxfile`; `diagram/mxGraphModel` present; `root` contains
   `mxCell id="0"` then `mxCell id="1" parent="0"`.
3. All `mxCell` ids unique.
4. Every `source` / `target` attribute references an id that exists in the file
   (no dangling edge endpoints).
5. Whole file decodes as **ASCII** -- confirmed for all 13.
6. Rendering semantics: each `value` was XML-unescaped then run through an HTML
   parser to confirm the label a viewer actually sees.

### 4.2 Two rendering defects found and fixed by check 6

Check 6 is the one that mattered, and it caught two real bugs that a
well-formedness-only check would have shipped.

- **Double-escaped HTML tags.** Writing `&lt;br&gt;` in the generator produced
  `&amp;lt;br&amp;gt;` in the file, which draw.io renders as the literal text `<br>`
  instead of a line break. Affected 155 label fragments across 12 of the 13 diagrams.
  Fixed by emitting raw `<br>` / `<b>` / `<i>` and letting the XML writer escape once.
- **A package name eaten as markup.** The `<root>` package label was emitted as a raw
  tag, so the HTML parser consumed it and the label rendered blank. Fixed by
  angle-bracket-escaping literal names for display. Deliberately *not* applied to the
  UML stereotype `<<abstract>>`, which is verified to render as visible text.

Post-fix: **0 labels contain a literal unrendered tag, 0 unknown tags, in all 13 files.**

### 4.3 Format conformance (rule 45 section 4.2)

- One `.drawio` per type, XML format -- yes.
- Text-only, no embedded binary assets -- yes; no `data:` URI or base64 payload in any
  file, and every file is plain ASCII.
- Same stems as the `uml/` set with `.drawio` extension, no timestamps, no version
  suffixes -- yes, the 13 names in rule 45 section 5 exactly.
- `DRAWIO_SHARE` was not set, so no shareable-URL comment was added.
- Editor compatibility: the emitted structure
  (`mxfile > diagram > mxGraphModel > root > mxCell[0], mxCell[1]`, geometry as
  `mxGeometry as="geometry"`) is byte-for-byte the same shape the project's own
  `DrawioConverter` emits in the pre-existing `drawio/*-diagram.drawio` files. Only
  standard mxGraph style keys and built-in shape names are used
  (`swimlane`, `shape=umlActor`, `shape=umlLifeline`, `shape=umlFrame`, `shape=component`,
  `shape=folder`, `shape=cube`, `shape=note`, `shape=endState`, `ellipse`, `rhombus`,
  `line`) -- no custom stencil or plugin dependency.

  **Not verified:** the files were not opened in draw.io desktop, app.diagrams.net, or
  the VS Code extension. No renderer was available in this environment. Compatibility
  is established by schema conformance and parity with the project's existing files,
  which is evidence but not a substitute for opening them.

---

## 5. What each diagram asserts, and on what evidence

- **Class** -- the 6 inheritance hierarchies whose parent resolves to an in-project
  class: `AbstractDiagramGenerator` (12 subclasses), `AbstractIntegration` (4),
  `AbstractLanguageParser` (4), `WorkflowEngineError` (6), `LLMProvider` (2),
  `LazyClient` (2). 36 classes drawn of 480 measured. MEASURED: 75 declared-base edges
  exist; **30** resolve to an in-project parent, the other 45 name external bases
  (`unittest.TestCase` x25, `ABC` x5, `Exception` x5, `object` x3, and one each of
  `ast.NodeVisitor`, `logging.Handler`, `Enum`, `Protocol`, `BaseHTTPRequestHandler`).
  Base classes carry their full measured method list; subclasses carry measured counts.
- **Package** -- all **44** measured packages with measured file/class/method counts
  (enumerable: the counts sum to 411 files). Dependency arrows are internal AST import
  edges. MEASURED: 109 distinct cross-package import pairs, 82 non-test. **24** pairs
  with weight >= 5 are drawn; every omitted pair has weight <= 4. The diagram says so.
- **Component** -- subsystems at measured package granularity; the 4 integration
  adapters and 2 LLM providers are the measured subclass sets, not a guess. An external
  system is drawn only where a concrete in-project adapter class was measured.
- **Sequence** -- 9 lifelines, 28 messages, ordered by the measured edge order of
  `create_flow_graph()`. Full mode only; the hook-mode short-circuit is noted.
- **State** -- the complete measured state machine: **27 nodes and 34 transitions**,
  read from `create_flow_graph()`. Conditional branches (red dashed) are the 4 measured
  routers: `route_after_preflight_guard`, `route_after_preflight_guard_user_choice`,
  `route_pre_analysis`, `route_after_step5_review`. Both measured back-edges are drawn
  (`sdlc_step5_retry -> sdlc_step4_implementation`,
  `fix_preflight_guard -> preflight_guard_unicode`).
- **Activity** -- same control flow as a decision/fork graph. The fork/join is the
  measured parallel pair `level1_complexity || level1_context`.
- **Deployment** -- values read from the 5 `k8s/` manifests and `docker-compose.yml`:
  Deployment `workflow-engine` replicas 2, HPA min 2 / max 6 / CPU 70 %, Service
  ClusterIP with named ports health 8080 + metrics 9090, liveness `GET /health:8080`,
  readiness `GET /readiness:8080`, image `workflow-engine:1.6.1`.
  Flagged on the diagram: that image tag **lags the CLAUDE.md project version 1.21.4**.
- **Use case** -- one use case per measured entry point: the 8 files in `scripts/*.py`
  and the 3 hook entry points in `hooks/*.py`, plus 3 capabilities whose implementing
  packages were measured. No speculative feature added.
- **Object** -- a genuine instance snapshot. Both `CallGraph` objects were really
  constructed; the complete one (411/480/3506) and the truncated one that ships today
  (300/449/2844) are shown side by side with their real `get_stats()` values, together
  with the traversal limits and the parser registry's measured per-extension input.
- **Composite** -- internals of `UMLDiagramGenerator`, the largest measured class
  (26 methods), with measured cyclomatic complexity per operation. Notes the measured
  fact that the class exposes `generate_timing_diagram`, a 14th type rule 45 does not
  list.
- **Interaction overview** -- three `ref` frames, one per level, each labelled with its
  measured node count and package size; three measured branch points.
- **Communication** -- 16 numbered messages between subsystems. Each link is backed by
  either an AST import edge or a filtered cross-file call edge.
- **Call graph** -- the top 11 of the 932 surviving filtered cross-file call edges, with
  an explicit on-diagram panel naming the excluded artifacts and their counts.

---

## 6. Skipped diagrams

**None.** All 13 rule-45 types were generated and validated.

---

## 7. Pre-existing files in `drawio/` -- not conformant, not touched

`drawio/` already contained 13 files dated 6-7 April, which this run did **not**
modify or delete. They do not satisfy rule 45:

- **Naming:** hyphenated (`class-diagram.drawio`) where rule 45 section 5 mandates
  underscores (`class_diagram.drawio`). They therefore sit alongside, not in place of,
  the conformant set -- `drawio/` now holds 26 `.drawio` files.
- **Type coverage:** the legacy set has no `call_graph_diagram` (rule 45 type 13) and
  carries an extra `system-architecture.drawio` that rule 45 does not define.
- **Staleness:** all 13 are dated 6-7 April, i.e. they predate the v1.20 package
  migration that created `langgraph_engine/sdlc_pipeline/` in its current form.

Recommendation: delete the 13 legacy hyphenated files. Not done here -- removing files
was outside this task's mandate.

### 7.1 Separate finding: rule 45 section 2 is being violated on the Git rule

Rule 45 section 2 states: *"Never commit generated diagram files to Git (add both dirs
to `.gitignore`)."*

MEASURED:

- `git ls-files drawio/` returns **13 tracked files** -- every legacy diagram is
  committed.
- `.gitignore` contains **no entry** for `drawio/` or `uml/` (grep for both returned
  nothing).

So the repository is doing the opposite of what the rule requires, and has been since
April. This is pre-existing and unrelated to this run, but it means the 13 new files
will also be offered for commit unless `.gitignore` is fixed first. `.gitignore` was
not edited here: it is shared with the concurrently running Mermaid pass that writes
`uml/`, and changing it was not in scope.

---

## 8. What could not be verified

- **Visual rendering.** No draw.io renderer was available. Files are schema-valid,
  ASCII, dangling-reference-free, use only built-in shapes, and match the structure of
  the project's own converter output -- but nobody opened them. Layout quality in
  particular (overlap, edge crossings) is unverified; the dense diagrams
  (class 146 elements, package 77) are the likeliest to want manual tidying, which is
  exactly what an editable format is for.
- **Whether `mcp-uml-diagram` / `mcp-drawio-diagram` apply their own caps.** Those
  server repos are not on this filesystem. These diagrams were generated directly from
  the in-process call graph and did not route through either MCP server, so their caps
  are irrelevant to this output but remain unmeasured.
- **Cross-file call-edge accuracy after filtering.** The generic-name filter removes a
  measured 55.5 % artifact class, but it is a name blocklist, not a type-aware
  resolver. Some genuine calls to methods named `get`/`set`/`run` were removed with the
  artifacts, and some rarer name collisions certainly survive. The 932 surviving edges
  are *less wrong*, not proven correct. Any diagram consumer needing exact call
  dependencies should treat `_resolve_target()` as the root problem.
- **Whether the 24 drawn import pairs are the most architecturally significant.** They
  are the highest-weight ones by import count, which is a proxy for coupling, not a
  measure of importance.

---

## 9. Reproduction

```bash
# 1. extract (read-only; writes only to a scratch dir)
python dio_extract.py      # -> 411 files, 480 classes, 3506 methods, 2651 imports
# 2. generate + validate 13 files into drawio/
python dio_gen.py          # -> GENERATED 13 / 13
```

Generator scripts live in the session scratchpad (`dio_mx.py` the mxGraph writer,
`dio_data.py` the measured facts, `dio_gen.py` the 13 builders). They are throwaway
tooling for this documentation pass and were deliberately not added to the repository.
