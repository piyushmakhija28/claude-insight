# v2.0.0 Review Index

**For:** Piyush Makhija · **Purpose:** one review pass before implementation begins
**Status:** Phase 0 COMPLETE · Phase 1 COMPLETE · **Phase 2 COMPLETE — consensus APPROVED at iteration 4, 0 open items**
**Artifacts:** 61 across `docs/phase-0-*`, `docs/phase-1-architecture/`, `docs/phase-2-validation/`
**Last updated:** 2026-08-01

Read the MUST READ tier. Skim the second. Ignore the third unless you want to audit a specific claim.

If something looks wrong, name the artifact and the claim. Everything here traces to a source.

---

## 1. MUST READ — your judgement changes the implementation

| # | File | Size | What it is | What to look for |
|---|------|------|-----------|------------------|
| 1 | `phase-0-reverse-engineering/as_built_executive_summary.md` | 32 lines | The five findings that most change what v2.0.0 should do | Start here. One file if you read nothing else. |
| 2 | `phase-1-architecture/hld.md` **SS 12** | — | Answers to the 6 open architectural questions | **The highest-value section.** Each labelled RESOLVED or PROVISIONAL. These are the real design decisions. |
| 3 | `phase-1-architecture/hld.md` **SS 4** | **17 ADRs** | Every technology decision, Chosen/Why/Rejected | ADR-006 (opt-in trade-off), ADR-010 (zero bundled hooks), ADR-012 (plugin-root ascent), ADR-015 (KG adapter), ADR-019 (zero bundled MCP servers), ADR-020 (three-layer push gate) |
| 4 | `phase-0-reverse-engineering/contradictions.md` | 175 lines | 6 ranked policy-vs-code contradictions | Whether you agree with the ranking. #1 and #2 drive real scope. |
| 5 | `phase-0-requirements/product-sequencing-v2.md` | ~287 lines | WSJF, MVP boundary, critical path, risks | **The MVP boundary** — what ships in v2.0.0 vs defers to v2.1 |
| 6 | `phase-0-requirements/prd-v2.md` | ~476 lines | FR-1..FR-23, NFR-1..NFR-5, measurable ACs, RTM | Sections 4 and 5. Are these ACs ones you could hold someone to? |
| 7 | `phase-2-validation/hld_v2.md` **ADR-019, ADR-020** | — | The two Phase 2 decisions | **ADR-019: the plugin bundles ZERO MCP servers.** ADR-020: three-layer control on the push gate. Both change what gets built. |
| 8 | `phase-2-validation/hld_v2.md` **SS 10** | 8 steps | Migration runbook, rebuilt in Phase 2 | Step 2 is `register-mcp`. If a user skips it, they get a plugin with no MCP servers and no error. Judge whether that ordering is safe. |
| 9 | `phase-1-architecture/consensus_summary_phase1.md` + `phase-2-validation/consensus_summary_phase2.md` | ≤80 lines each | Both binary gates' final verdicts | What each checked, and what each explicitly did not |

**Suggested order:** 1 → 2 → 3 → 7 → 5. Items 4, 6, 8, 9 are supporting detail.

---

## 2. OPEN ITEMS — unresolved, NOT decided

Carried forward deliberately. Not settled to make the documents look finished.

| Item | Status | Why it matters |
|------|--------|----------------|
| **FR-15 home-directory split** | **DISPUTED** | C.1 says 13 live-code sites / 103 comments. An independent grep says ~95 / 23. The grep cannot structurally separate docstring bodies from code, so it does not refute C.1 — but 13 is unverified by any independent method. **~7x swing in remediation scope.** AST re-derivation mandated before FR-15 is sized. (OAQ 6) |
| **Plugin extraction boundary** | **NO CLEAN SEAM** | Package-level import SCC spans ~15-16 subpackages; function-level has ZERO cycles and 708 fragmented communities (largest 9%). Both correct, different graphs. HLD draws the seam *around* the monolith (`plugin_api/` Facade) rather than forcing a cut. Cycle-breaking sequenced to v2.1+ with quantified targets. (OAQ 5) |
| **`${CLAUDE_PLUGIN_ROOT}` in `.mcp.json`** | UNDOCUMENTED | If unsupported, bundled MCP servers cannot use relative paths. (FR-14a item 1) |
| **What `/plugin install` writes to settings.json** | UNDOCUMENTED | FR-18 cannot verify clean uninstall without knowing what install created. (FR-14a item 3) |
| **What `/plugin uninstall` leaves behind** | UNDOCUMENTED | Same. (FR-14a item 4) |
| **Bundled MCP servers vs NFR-1** | **PROVISIONAL** | ADR-018: bundled `.mcp.json` stdio servers are spawned processes too — NFR-1 could fail through the mechanism chosen to replace hooks. (FR-14a item 5) |
| **Stop-hook true per-turn spawn count** | INFERRED, NOT MEASURED | ~2 is a static filesystem inference (7 of 9 scripts absent), never observed at runtime. FR-8a's AC requires runtime instrumentation; a static re-derivation does NOT satisfy it. |
| **`audit_surface.json` counts** | **LOWER BOUNDS** | Its AST scan missed 4 aliased subprocess imports. The same blind spot may affect its 62 credential sites and 17 settings.json writers — nobody has checked. |
| **Push gate after FR-4** | **UNPROTECTED, BOTH WAYS** | Protected *today* only because FR-4 has not run and the live PreToolUse hook still fires. After FR-4 it has neither preventive nor detective cover unless **both** `register-mcp` and the ADR-017 CI assertion are built. Both are **designed, not built**. This is a sequencing constraint on implementation, not a doc fix. (Phase 2) |
| **WSJF inputs behind the MVP boundary** | **UNVALIDATED JUDGEMENT** | The arithmetic over them is exact and verified. The integers themselves are the PM's single-pass estimates, entered once, never cross-checked by a second party. Normal for WSJF and not a defect — but the MVP line is softer than the precision of the numbers implies. (Phase 2, consensus iteration 3) |
| **FR-25 / FR-26 have no owner** | **PROPOSED ONLY — YOUR DECISION** | The two anti-defect checks (arithmetic recomputation; cross-file backward-propagation) exist only as proposals in `advisory_items.json`. `prd-v2.md` stops at FR-24. Each was **narrowed three times in three passes** as new instances outgrew its scope, and FR-25's own file records that a recomputation check "would have PASSED both before and after the fix while the diagram was actively contradicting an ADR." **Accept into the PRD, defer to v2.1, or drop.** Not decided. (Phase 2) |
| **`VERSION` vs `CLAUDE.md`** | ~~CONTRADICTION~~ **CLOSED 2026-08-02 by `1919bdb`** | This row said `VERSION` read **1.21.5** while `CLAUDE.md` and the phase-0 docs said **1.21.4**. **It has been false since `1919bdb`** ("chore: sync the version strings to VERSION"), which moved `CLAUDE.md`, `README.md`, `SRS.md` and `langgraph_engine/__init__.py` to match — traced with `git log -L 4,4:CLAUDE.md`. **The row itself then went stale for two days**, and #293 was dispatched against a defect that no longer existed. Two corrections to what it said even when true: it names "both phase-0 docs" where **four** phase-0 files carry 1.21.4, and all four are historical baselines ("v1.21.4 -> v2.0.0") — different in kind from `CLAUDE.md:4`, which asserts the current version. **Still drifting and outside `sync-version.py`'s targets: `Dockerfile:3,42` and `k8s/deployment.yaml:13,28` read 1.6.1** — roughly fifteen minors behind, and that absence from the sync targets is the mechanism of their drift. |

**FR-14a is a spike, not a doc question.** Four of the above resolve in under an hour by building a throwaway plugin and measuring. That must happen before the packaging design freezes.

**The push-gate item is the one to read twice.** It is the only open item where the *order* of implementation determines whether a live protection lapses.

---

## 3. ACCEPTED RISKS — you decided these; recorded so they are not silently revisited

| Risk | Decision | Consequence accepted |
|------|----------|---------------------|
| Enforcement becomes opt-in | ADR-006 | Policies do not apply on sessions where the plugin is never invoked. Stated at full strength twice in the HLD, verified unsoftened by the gate. |
| 3 policies deleted permanently | ADR-009b | `auto-skill-agent-selection` (710 lines), `auto-plan-mode-suggestion` (1,045), `adaptive-skill-registry` (109) — **1,864 lines, irrecoverable.** `~/.claude/` is not version-controlled. A port-to-git-first alternative was offered and declined. |
| Stop hook repaired, not removed | FR-8a | 7 of 9 dead script references individually rebuilt or formally retired. More work than stripping it. |
| Plugin ships zero hooks | ADR-010 | Evidence-forced. Plugin hooks merge silently and cannot be individually disabled, so bundling any would defeat the project at install time. |

---

## 4. WHAT PHASE 1 DECIDED — the six open questions

| # | Question | Verdict |
|---|----------|---------|
| 1 | What replaces `post-tool-tracker.py` as checkpoint writer? | **RESOLVED** — `CheckpointManager` already exists, sits outside the deletion set, triggered at step boundaries. Phase 0's "sole writer" claim was a conflation of two independent systems; crash recovery was never at risk. |
| 2 | Disposition of the 15 hook-coupled policies | **RESOLVED** — 5 port-to-MCP, 5 demote-to-advisory, 5 delete. `push_gate` fixed as mandatory port-to-MCP + CI gate. |
| 3 | How the plugin finds its own root | **RESOLVED** — manifest-anchored `__file__` ascent needs no undocumented behaviour, so ADR-009a branch 2 no longer depends on the unverified env-var question. |
| 4 | The CallGraph truncation fix | **RESOLVED in design, but its TARGET was wrong — see 4b below.** Four-phase discovery, unbounded default, mandatory `DiscoveryManifest` argument, so dropping becomes *inexpressible* rather than discouraged. The design stands. The site list it was written against does not. |
| 5 | Plugin extraction boundary | **RESOLVED AS A NEGATIVE** — no clean seam exists; 708 fragmented communities is positive evidence *against* a cut. Seam drawn around the monolith instead. |
| 6 | FR-15's home-directory split | **UNRESOLVED BY DESIGN** — left unsized, AST re-derivation required first. |

**Scope expansions Phase 1 found that Phase 0 missed entirely:**
- **NFR-2 is already violated inside the engine** — 6 `timeout=` application sites across 5 files, including a 75-second wall-clock timeout on the pipeline path. Deleting hooks does not satisfy NFR-2.
- **NFR-1's acceptance criterion was ill-defined** — the retained Stop hook is engine code, so "delta = 0 processes attributable to claude-workflow-engine" could never pass. Now requires per-component attribution.
- **De-hooking removes ~6 of 116 spawn sites (~5%)**, not the large reduction the narrative implied. `stop_notifier/` retains 17 and is kept.

---

## 4b. WHAT PHASE 5's PROBE FOUND — read this before implementing FR-9a

`ast-graph-engineer` ran the builder rather than reading it. Four findings, all **MEASURED at runtime**.

**1. The cap everyone cites is dead code.** `langgraph_engine/parsers/config.py:11`'s `MAX_FILES = 300`
is read by nothing. Its only importer re-exports it. Its own docstring calls itself "a single source
of truth" — false. **The cap that binds is `parsers/call_graph_builder_legacy.py:64`**, enforced at
lines 107 and 118.

> **Consequence:** implementing FR-9a against the cited line would have changed the constant, looked
> complete, and left discovery stopping at 300 files. **19 files across every phase cite
> `parsers/config.py`** — including `SRS.md`, written the same day as this probe.

**2. 17 truncation sites exist — but only TWO bind.** Phase 1's "four files plus a fifth
different-class truncator" was half right. The full enumeration, and what it means as a work list:

| Class | Sites | Binding today |
|---|---|---|
| File-count caps | 4 | **1** — `call_graph_builder_legacy.py:64` |
| File-size caps | 4 | **0** — measured; no file exceeds 100 KB |
| Graph-traversal caps | 2 | **1** — `graph_model.py:43`, `MAX_PATHS = 500` |
| Different-class truncators | 2 | n/a — not call-graph |
| Downstream diagram truncators | 5 | post-discovery |
| **Total** | **17** | **2** |

> **Why the distinction matters:** 17 counts *code locations*, not active truncations. Read as a work
> list it sends an implementer to 17 places, of which 4 have measured-zero impact, 1 is dead and 1 is
> dormant. **A work list padded with inert sites invites exactly the failure this whole finding is
> about** — a fix aimed at the wrong site that looks complete.

> **`graph_model.py:43` survives fixing the file cap.** Both probe runs emitted `hit max_paths=500
> limit; results truncated`. **Every sequence and interaction diagram is capped at 500 paths no
> matter how many files are ingested.** FR-9a must cover both sites or it half-works.

**3. `CLAUDE.md`'s "578 classes / 3,985 methods" is a genuine untruncated measurement — of a
different codebase.** Traced via `git log -S` to commit `ab54428`, whose tree held 226 `.py` files;
under 300, so truncation was impossible. Re-running the builder on that archived tree reproduces
**579 / 3,992**. **Today's complete figures are 480 / 3,506 — lower, despite nearly double the
files**, because the v1.15–v1.20 refactors deleted class surface. What the pipeline consumes today
is **449 / 2,844**.

**4. "4 languages (Python/Java/TS/Kotlin)" is false, and always was.** Zero Java, TypeScript or
Kotlin source files at the current tree *or* the 2026-03 tree. Published in **`CLAUDE.md:25,248`,
`CHANGELOG.md:433`, ADR-002:51,96, `PIPELINE_ARCHITECTURE.md:137,212`.**

**A rule-45 inversion — RESOLVED, and NOT by changing the rule.** The AST fallback
(`diagrams/ast_analyzer.py:152,193`) uses an **uncapped** `rglob("*.py")`, so the mandated primary
source reaches **73%** of the codebase while the fallback beneath it reaches **100%**.

I initially read this as a rule defect and said so. **The architect overruled it, and is right.**
Rule 45 §6 is correct *in principle* — a CallGraph carries resolved call edges the AST scan cannot
produce, so it is the better source **in kind**. What is broken is that the better source is capped.
Changing the rule would **enshrine a workaround for a defect**, and the ordering would become wrong
again the moment FR-9a lands, with the rule then documenting the bug as intended behaviour. That is
the DOCUMENTED-ONLY failure running in reverse.

It is also **not uniform by diagram type**, so a blanket change would be wrong even as a stopgap: for
class and package diagrams coverage dominates and the fallback is currently better; for sequence and
interaction diagrams the primary remains better despite lower coverage — and is separately capped by
`graph_model.py:43`, which the AST fallback never reaches because it produces no call paths at all.

**Disposition:** leave §6 unchanged; the inversion is recorded in the HLD as independent
justification for FR-9a, so nobody "fixes" a diagram-coverage complaint by bypassing the primary and
thereby removes the pressure to fix the real defect.

**Read-only override: EXISTS, demonstrated.** `CallGraphBuilder.__init__.__defaults__ = (N,)`
propagates through `build_call_graph()`. Rebinding module-level `MAX_FILES` is a silent no-op —
defaults bind at def-time, which is the trap. No env var exists. `CLAUDE_CG_MAX_PATHS=500` truncates
traversal independently and fired on **both** probe runs. This is why the 26 diagrams could be
generated from complete data without editing source.

---

## 4c. FR-9b / SRS FR-38 — the resolver defect (YOUR RULING: v2.0.0 scope)

**`langgraph_engine/parsers/graph_model.py:265`**, inside `_resolve_target()`, returns `candidates[0]`
for a bare simple method name matching multiple FQNs. Builtin and stdlib calls therefore bind to
whatever same-named project class sorts first:

| Collision | Inflated target | Measured in-degree |
|---|---|---|
| `list.append()` | `JsonlAppender.append` | **1,592** |
| `str.format()` | `ErrorMessages.format` | 755–756 *(two agents measured 755 and 756; left as a range, not adjudicated)* |
| `dict.get()` | `_MemoryLayer.get` / `set` | — |

**55.5% of cross-file "resolved" edges are collision artifacts.** Of 26,114 total: 18,608 unresolved,
2,853 builtin-collision, 433 cross-file ambiguity, leaving **4,220 high-confidence**. *(Arithmetic
reconciles exactly: 18,608 + 2,853 + 433 = 21,894; 26,114 − 21,894 = 4,220.)*

**Why it is not cosmetic:** `sdlc_pipeline/call_graph_analyzer.py` builds `danger_zones` (`:303`) and
`hot_nodes` (`:1197`) from an `n >= 5` caller-count gate — and `_classify_risk` (`:56-67`) labels
per-method risk on an 8+ gate. **Both are caller-count-only.** So `JsonlAppender.append` currently
ranks as the codebase's top danger zone on the strength of every `list.append()` in the repo, and
that ranking is injected into the Step 0 planning prompt via `prompt_gen_expert_caller.py`.

**The precondition was verified, not assumed:** `resolve_edges()` *is* invoked at
`call_graph_builder_legacy.py:96` on every build. Had it not been, `_resolved_edges` would stay
`None`, `get_edges()` would return raw edges, and the requirement would have been unwarranted.

**FR-9a alone is insufficient.** Fixing discovery without fixing resolution yields a *larger* graph
feeding the same broken resolver. The dependency is stated in the requirement.

**A separate consumer trap, explicitly NOT this defect:** `resolve_edges()` writes to
`_resolved_edges`, not `graph.edges` — so reading `graph.edges` gives 656 instead of 7,004. **No
shipping code does this**; all four consumers use `get_edges()` (`:155`, `:455`, `:600`, `:1209`).
It caught an agent, not the pipeline.

---

## 4a. WHAT PHASE 2 DECIDED — cross-validation of the HLD

Phase 2 put the HLD in front of the BA and PM agents, let the architect defend it, and ran the
gates over the whole exchange. It produced two new ADRs and one structural mechanism.

| # | Decision | Verdict |
|---|----------|---------|
| ADR-019 | Does the plugin bundle MCP servers? | **NO — zero bundled servers.** Bundled `.mcp.json` stdio servers spawn on plugin enable, so bundling any would violate NFR-1 through the very mechanism chosen to replace hooks. Registration becomes an explicit opt-in `register-mcp` command. Resolves OAQ from Phase 1's PROVISIONAL ADR-018. |
| ADR-020 | How is the push gate protected once its hook is deleted? | **Three layers** — PREVENT (`unregister-mcp` refuses to strip it), DETECT (`doctor` reports it missing), PREVENT-THE-HARM (git `pre-push` hook as the last line). No single layer is trusted alone. **Neither of the first two is built yet** — see the open item above. |
| SS 10 | Migration runbook | Rebuilt from scratch to **8 steps**, with `register-mcp` at step 2. Prior version silently assumed servers arrived with the plugin. |

**The mechanism worth knowing about:** `sa_defence.json` now carries a field-suffix convention —
`_record`/`_as_filed` means frozen-at-filing, `_now` means live-and-must-be-current — enforced by a
validator **embedded in the file itself** and covering all 14 top-level sections. It exists because
one defect class recurred four times in that file while the architect was actively concentrating on
it. A date-stamped manual sweep was offered as the alternative and rejected: a sweep is a
documented-only control, and this file is its own disproof.

**What the convention does NOT do**, stated by the architect and accepted by the gate: it classifies
*fields*, not *content*. It makes omitting the frozen/live distinction impossible. It cannot verify
that a correctly-labelled `_now` claim is actually true. Keeping them true is still human work — the
convention makes that work *enumerable* rather than a judgement call over prose.

---

## 5. SHOULD SKIM

| File | What it tells you |
|------|-------------------|
| `phase-0-reverse-engineering/capability_loss.md` | What stops working when hooks are deleted — 27 capabilities by name: 16 PreToolUse components (14 policy gates plus the daemon and registry mechanism), 9 PostToolUse capabilities, 2 cross-cutting. Descriptor corrected 2026-08-02; it previously read "14 PreToolUse gates, 9 PostToolUse capabilities", which totals 23 and is what the 25 undercount was reconciled against |
| `phase-0-reverse-engineering/builder_divergence.md` | Root cause of `MAX_FILES=300`, with the real invocation that proved it |
| `phase-0-reverse-engineering/path_violations.md` | Every `~/.claude/` reference and unencoded `open()`, by file:line |
| `phase-0-reverse-engineering/claude_md_drift.md` | Where CLAUDE.md disagrees with the filesystem |
| `phase-1-architecture/hld.md` SS 13a | The HLD's own verification-status statement and correction record |
| `phase-0-reverse-engineering/as-built-prd.md` Appendix E | Per-FR gap analysis vs your original requirement doc |

---

## 6. REFERENCE ONLY — machine output, audit-on-demand

**Graph/analysis:** `ast_call_graph.json` (4.2 MB) · `codebase_kg/` (5 files) · `audit_surface.json` ·
`impact_analysis_graph.json` · `structural_inventory.json` · `complexity_report.json` · `lhs.json` ·
`api_surface.json` · `rts_selection.json` · `policy_corpus_inventory.json` ·
`policy_enforcement_raw.json` · `dead_code_report.json`

**Gate output:** `hallucination_report_phase0/1/2.json` · `faithfulness_scorecard_phase0/1/2.json` ·
`hallucination_report_sequencing.json` · `consensus_verdict_phase1/2.json` — plus their
`_summary.md` counterparts

**Phase 2 review exchange:** `ba_review.json` (10 findings) · `pm_review.json` (9 findings) ·
`sa_defence.json` (the architect's response, plus the field-suffix convention and its embedded
validator) · `advisory_items.json`

**Per-agent prose summaries** (each duplicates its JSON): `dead_code_summary.md` ·
`ast_call_graph_summary.md` · `impact_analysis_summary.md` · `structural_inventory_summary.md` ·
`policy_corpus_summary.md` · `policy_enforcement_summary.md` · `stop_hook_overhead.md`

**Housekeeping — two files for you to rule on:**
- `dead_code_report.json.malformed.bak` — backup of an artifact repaired mid-run. Safe to delete.
- `phase-1-architecture/hld-v1.20.0-superseded.md` — the **pre-existing git-tracked HLD** that the
  new one replaced. The orchestrator assigned that output path without checking it was occupied;
  the architect preserved the prior content and disclosed it. The original is also recoverable via
  `git show a955c43:docs/phase-1-architecture/hld.md`. Keep or delete as you prefer.

---

## 7. WHAT THE QUALITY GATES DO AND DO NOT GUARANTEE

Read this before weighting the scores.

**They verify PROVENANCE.** A claim traces to a cited source, and the source says what is claimed.
This caught a citation invoking a skill file as *licence* for a method that file explicitly
*forbids* — which required reading the cited text, and which no internal-consistency check finds.

**They do NOT verify TRUTH.** If a source was never independently measured, accurate citation
upgrades its apparent status without adding evidence. FR-15's "13 call sites" passed both Phase 0
gates at 1.00/1.00 and remains unverified. That is the gates' scope, not a defect in them — and it
is why section 2 exists.

**"No defect found in what was examined" is not "verified."** Both Phase 1.3 gates declared coverage
reductions. The consensus gate names what it did not re-read in each iteration. The HLD's own SS 13a
states this in the same terms. Treat clean scores as bounded by their stated scope.

**Correction record — every defect caught before shipping, by phase:**

| # | Correction | Found by |
|---|-----------|----------|
| 1 | "46/46 orphan policies" — false, artifact of an orchestrator briefing error (SRS.md never supplied). Real figure 14/46. | The KG agent flagging it as absence-of-evidence |
| 2 | "70% cycle blocks extraction" — overstated; package-level vs function-level measure different graphs | Phase C.2.5 |
| 3 | 8-spawn Stop-hook floor — wrong; 7 of 9 target scripts do not exist, true floor ~2 | Cross-agent contradiction |
| 4 | Three invented skill names in an orchestrator dispatch | The BA agent refusing to substitute |
| 5 | Malformed `dead_code_report.json` (illegal key inside an array) | Phase C.2.5 ingestion |
| 6 | `setup_wizard.py` "writes hook registrations" — fabricated mechanism | Orchestrator, then confirmed 3x independently |
| 7 | `audit_surface.json` undercounts spawns — AST scan misses 4 aliased imports | Hallucination gate, generalised by orchestrator |
| 8 | "7 empty KG domains" — false; they hold **486 real edges** under a `relationships` key | Faithfulness gate's from-scratch classifier |
| 9-13 | **Five instances** of one defect class: a summary count disagreeing with its enumeration. Included a **missing 75-second timeout** on the pipeline path and a **wrong policy-disposition tally** (4/6/5 vs 5/5/5 — both sum to 15, so any total-check passes it) | Consensus gate across 4 iterations |
| 14 | **Eight instances** of a second class — *backward propagation*: a claim corrected in one place, left standing in the artifact it was copied from or into. 4 in `hld.md`, 4 in `sa_defence.json` | Consensus gate, Phase 2 |
| 15 | ADR-012's **heading** kept a claim its own body, diagram and table had already reframed. Diagnosis: "a heading is skimmed as a label rather than re-read as a claim" | Consensus gate, Phase 2 |
| 16 | `pm_review.json` reported as having "no findings array" — it has 9. Root cause: a probe using `list(d.keys())[:9]` read as exhaustive | Consensus gate, Phase 2 |
| 17 | A governance guarantee documented as **active** that does not exist (ADR-017's CI assertion is designed, not built) | Consensus gate, Phase 2 iteration 2 |
| 18 | The **validator itself went stale in the pass that extended it** — its embedded source still encoded the old 3-array scope while the file claimed 14 sections. The stale-claim defect, inside the mechanism built to prevent it | The architect, by executing the *stored* string instead of trusting the authored form |
| 19-20 | Two orchestrator errors: findings mis-attributed between the BA and PM reviews, and an "omitted 4" figure that was really 5 against a stale denominator — which then survived three passes | Consensus gate, Phase 2 |
| 21 | This index stated two new rules were "binding on FR-25 and FR-26" with the "(proposed)" hedge dropped — present-tense-as-existing framing, in the document that catalogues that defect | Phase 5 SRS agent, contradicting its own brief |
| 22 | **`parsers/config.py:11` is dead code** — the truncation constant cited in **19 files across every phase** is read by nothing. Fixing it would have changed nothing while appearing to succeed | Phase 5 probe, by running the builder instead of reading it |
| 23 | "578 classes / 3,985 methods" in `CLAUDE.md` — a real untruncated measurement of a **226-file 2026-03 tree**. Today's complete figure is **480 / 3,506** | Phase 5 probe, via `git log -S` + archived-tree re-run |
| 24 | **"4 languages (Python/Java/TS/Kotlin)"** — false at every timestamp; zero Java/TS/Kotlin files ever. Published in 5 documents | Phase 5 probe |
| 25 | This index said `hld.md` SS 4 holds **"15 ADRs"** — correct at Phase 1, stale once ADR-019 and ADR-020 landed at Phase 2. It is **17**: 15 numeric ids (006–020) plus ADR-**009a** and **009b**, which a `ADR-[0-9]{3}` regex silently misses | V2-001's author, while writing ADR-006 |
| 26 | `prd-v2.md` SS 9 still claimed hook deletion "removes the sole writer of crash-recovery checkpoint state" — **retracted**; OAQ 1 established `CheckpointManager` sits outside the deletion set, so crash recovery was never at risk. The real loss is per-tool-call *telemetry* | V2-001's author |
| 27 | The orchestrator's closing comment on **#267 cited commit `8c34d3f`**, which is not a commit in this repository. The real hash is **`92053ff`**. Typed from memory instead of read from `git log`, in a comment whose entire purpose is to make the work auditable — a wrong hash makes the close *unverifiable*, which is worse than omitting it. Corrected publicly on the issue rather than by editing the comment | The orchestrator, immediately after, by reading `git log` |

| 28 | **Line citations into `hld_v2.md` have drifted wholesale.** V2-015's author found `hld_v2.md:759` wrong; measuring the rest showed it is not a typo but one systematic cause — the file grew, and *nothing re-anchored the citations*. Three of four checked were off by **exactly +31** (759→790, 738→769, 773→804) and the fourth by +77 (1934→2011). **36 such citations exist across 6 documents**; spot-resolving them lands several on blank lines and one on a table separator | V2-015's author found the first; the orchestrator measured the scope |

| 29 | **"17 pre-existing settings.json writers" is the wrong noun, and Phase 8 blessed it.** The source field is `audit_surface.json:406` `settings_json_touch_sites_count` — *string-literal mention sites*, 17 of them across **5 modules**, of which exactly **one** (`setup_wizard.py`) writes. `premise_scan_bh.json` marked the claim `MEASURED` / "ACCURATE AGAINST ITS SOURCE" by checking that the declared 17 matched the array's 17. **That check cannot catch a noun mismatch** — the count was right and the word for what it counted was wrong | V2-016's author, re-measuring a figure the brief told it not to trust |
| 30 | **Two settings.json writers were never in any count**, because every scan was Python-only. `scripts/setup/setup-global-claude.ps1:127,140` (`Copy-Item -Force`) and `setup-global-claude.sh:161,167` (`cp`) **replace the user's entire `settings.json` with a template** whenever it lacks the string `3-level-flow`. That is strictly worse than the read-modify-write ADV-008 does document, and it appears in neither HLD SS 8.4 nor ADV-008's `minimum_fix` | V2-016's author; confirmed at source by the orchestrator |

| 31 | **A negative control eroded until it broke, and the comment above it asserted that could not happen.** `test_call_graph_discovery_coverage.py`'s constants block claimed "these are floors, not equalities, so **adding source files cannot fail the suite**". False. The floor *assertions* do get safer as the tree grows — but the negative control asserts the *opposite* direction, that a 300-file capped build stays BELOW the floor, and growth erodes exactly that. Measured margin: **+662 methods on 2026-08-01, +10 on 2026-08-03**, then negative when one test file landed. It failed while nothing it guards had regressed | V2-021's author, which isolated it by moving its own file in and out rather than accepting the orchestrator's "pre-existing" guess |
| 32 | **The orchestrator called #31 "pre-existing" on reasoning that could not have been right.** I argued batch E's growth caused it, from my own green run at `88bb5e9`. V2-019 had called it pre-existing after stashing its changes — but a stash cannot remove *siblings'* untracked files, so its control was contaminated by the very concurrency it had itself flagged. Both of us were guessing at an attribution one measurement settles | V2-021's author, by measuring capped-build methods with and without its file |

| 33 | **The engine's own Level 0 auto-fix corrupted source code.** Its "Windows path handling" check flagged `tests\test_open_encoding_gate.py`, ran unattended in hook context, and rewrote `\n` to `/n` **inside string literals** — a newline escape is not a path separator. Two tests then failed with `SyntaxError: invalid syntax` on a snippet that no longer parsed. It corrupted some occurrences and not others in the same string, so the damage looked like an authoring typo rather than a tool | The orchestrator, tracing a `SyntaxError` in a file no human had edited |
| 34 | **The orchestrator destroyed a node's work while tidying.** V2-019 recorded its measurement in `SRS.md`'s FR-30 status block. I ran `git restore SRS.md` to drop the hook's date-stamp churn and took the FR-30 update with it. `git restore` on a file with two unrelated sources of change discards both | The orchestrator, when the surviving diff turned out to be nothing but date stamps |

| 35 | **"0 absolute path literals" was false, and both the census and my own Level 0 rewrite missed the same form.** `scripts/tools/create_mcp_repos.py:25` hardcoded `Path("C:/Users/techd/Documents/workspace-...")` — a real absolute path carrying the machine owner's username. The census's regex checked the **backslash** drive form only. So does the AST scanner I wrote for the Level 0 guard two commits earlier and vouched for: its pattern requires a backslash, so `C:/` passes it untouched. Two independent checks with the same blind spot | V2-018's author found the literal; the orchestrator confirmed its own scanner shares the gap |
| 36 | **2 of the census's 13 "code-level" home-directory sites are docstring `Example::` blocks** (`src/mcp/base/persistence.py:44` and `:199`). Remediating them would have rewritten documentation — the precise thing FR-15's own AC forbids. So the 13 was 11 genuine plus 2 false positives, **and 22 real CODE sites it never saw** | V2-018's author, classifying by enclosing node |

| 37 | **NOT an error but a live REQUIREMENTS CONFLICT: two accepted criteria demand opposite outcomes from the same one-shot measurement.** ADR-020 Path C's PASS is that `claude plugin uninstall` **does NOT remove** the `register-mcp`-written `mcpServers` entry — that is how the push gate outlives the plugin (`adr-020-path-c-verification.md:246`, verified). PRD FR-18 / SRS FR-31 (a)'s PASS is that **no MCP tool the plugin registered remains callable** — the entry is gone. **One install-then-uninstall cycle settles both, and they cannot both pass.** Both procedures are written, both are blocked on the same owner ruling, and neither document referenced the other | V2-022's author, reading both procedures against each other |

**#37 was the only item in this record that could not be resolved by measuring harder** — the
measurement was already designed; what was undecided was which outcome the project wanted.

> **RESOLVED by owner ruling, 2026-08-03. ADR-020 Path C wins.** The version push gate is a safety
> net against un-gated pushes, so a `register-mcp`-written entry **persists in user-scope settings
> across plugin uninstall** unless the user explicitly removed it. **FR-31 (a) is therefore
> scope-limited to plugin-specific *operational* tools and does not reach safety-enforcement gates**;
> non-essential residue (caches, ephemeral state) is still purged.
>
> Consequences that follow and are NOT yet done: `prd-v2.md` FR-18 and `SRS.md` FR-31 both still
> carry the unnarrowed wording, and `adr-020-path-c-verification.md` and
> `fr31-uninstall-residue-verification.md` SS 6 both still present Path C as an open question rather
> than a settled requirement. The blocked cycle, when authorised, now has ONE expected outcome
> instead of two contradictory ones — which is what makes it worth running.
>
> **But the ruling does NOT unblock the cycle yet, and this was measured rather than assumed.**
> `claude plugin uninstall` is capability-blind, and `push-gate` is marked `not_built_yet` in
> `plugin/mcp-registry.json` because V2-024 owns it. So the **only** entry `register-mcp` can write
> today is the progress writer — an *operational* tool, which the narrowing explicitly does **not**
> exempt. A cycle run before V2-024 lands still resolves against an operational entry, and FR-31 (a)
> **can still fail**. The narrowing is requirement-side scoping; the host cannot tell a safety gate
> from an operational tool and never will.

| 38 | **The orchestrator's brief asserted a fact about three files that was true of one.** I told V2-025 that all three settings files "currently DO carry a live PreToolUse registration", and built a design instruction on it. Measured: only `~/.claude/settings.json` does; `~/.claude/settings.local.json` and the tracked `.claude/settings.local.json` both have an **empty `hooks` block**. The agent measured it, contradicted the brief, and **changed its default settings target because of it** — defaulting to the user-scope file would have parked the gate in the passing half of its own truth table and flipped whenever the owner edited a file CI cannot see | V2-025's author, refusing to take the brief's premise on trust |
| 39 | **I landed a gate and never wired it.** `scripts/verify_home_paths.py` shipped with V2-018 and appeared in no workflow and no pre-commit hook — found by a repo-wide search across `*.yml/*.yaml/*.py/*.toml/*.cfg/*.md/*.sh`. **This is the same defect class this record already holds**, from when three policy gates existed and nothing executed any of them. I had written that finding myself and then reproduced it. Now wired into `ci.yml` | V2-025's author, auditing what actually invokes the gates |

| 40 | **The Stop hook tries to open a pull request on every response turn, and only a missing import stops it.** Verified at source: `hooks/stop_notifier/core.py:319`, `:363` and `:483` call `github_pr_workflow.run_pr_workflow()`, and `post_impl.py:166` calls `github_create_pr(...)`. Both modules are absent — 276 and 72 live-log occurrences of the resulting failure. **Restoring either module without first revisiting the trigger conditions would make the hook open real PRs unprompted, once per turn, on any feature branch.** The Stop hook is one of the two hooks explicitly RETAINED across the plugin migration | V2-033's author, instrumenting the hook it was asked only to count spawns in |
| 41 | **The spawn floor is 7, not the enumerated 4 — and the criterion's own line citations were wrong.** Measured identically across 20 runs. The enumerated-four model assumed the two unconditional `git rev-parse` calls return early; that holds only on a default branch, and this one is **64 commits ahead of `main`** (verified), so each continues into a `git rev-list` and branch detection adds three more. Separately: `voice.py:144` is cited as the spawn launch and is a **docstring line** — the only `subprocess.Popen` in that file is at **164** (verified); and the claim that both guarded targets "resolve as a sibling" is false, since the voice notifier resolves to a different directory entirely | V2-033's author; both citations confirmed at source by the orchestrator |

| 52 | **The unit suite passes on Windows and FAILS on Linux, and this release was merged knowing that.** `ci.yml`'s `Test (Python 3.10)` and `Test (Python 3.11)` jobs both exit 1 on `ubuntu-latest` (run #154, `30978135295`). The same suite runs to completion with exit 0 on the Windows development machine, repeatedly, including immediately before the merge. **The cause is unknown** — the failure logs require authentication this session did not have — and the plausible classes are the ones this repository has already been bitten by: path separators, subprocess spawn mechanics, and default text encoding. **The two workflows this sprint added both PASS on ubuntu**, including the push-gate reachability assertion, so the release's core contract is verified on Linux; it is the pre-existing test job that is red | The orchestrator, reading workflow badges after the PR-status tool reported no checks at all |
| 53 | **The orchestrator's "most probable explanation" was wrong, and its own hedge was right.** `github_get_pr_status` returns `checks: []` for a PR with **183 workflow runs against it**. I read that as Actions most likely being disabled, and said in the same breath that I could not distinguish it from the tool simply not reporting checks. The second reading was correct. A push was made specifically to test the first, and had the hedge not been stated the next step would have been changing repository settings **to fix a problem that did not exist** | The orchestrator, via workflow status badges, which render their conclusion as text |

> **DIAGNOSED AND FIXED 2026-08-05, and the framing above was wrong.** This is not a Windows/Linux
> split. **CI runs a different command than the orchestrator did.** I ran
> `pytest tests/ --ignore=tests/integration --ignore=tests/load -p no:randomly`; CI runs
> `pytest tests/ -m "not integration"` — no ignores, and **no `-p no:randomly`, so its order is
> randomised.** Under CI's exact command the suite fails on Windows too, which removes the platform
> from the explanation entirely.
>
> The failure is `test_nfr1_harness.py::TestRealSpawnDetection::test_real_spawn_is_detected_and_fails`
> — **the flake every node in this sprint was warned about and correctly attributed.** Its cause is
> now measured: the test spawned a child that lived 0.6s, while the measurement window is only as
> long as ten near-empty tool calls take. `Popen` returns before the OS has made a process
> enumerable, so on a loaded machine the window closed before the child became visible, and the
> harness was blamed for missing a spawn that had not happened yet. The child now announces itself on
> stdout and the test blocks on that byte, making its existence a **precondition** of the measurement
> rather than a race against it.
>
> **Negative control, same load, same machine: pre-fix 3 of 8 failed; post-fix 0 of 8, and 0 of 12
> unloaded.** All four CI steps then pass locally end to end — collect, unit, integration, coverage.
> The first load attempt produced 0 of 8 too and proved nothing, because `multiprocessing` from stdin
> never started the workers; that run was discarded rather than counted.

**#52's original entry is left standing above rather than rewritten**, because the sequence matters:
the release was merged on an honest but wrong hypothesis, and the correction is worth more than a
tidy record. **The lesson is not "Linux differs" — it is that a suite is only green under the command
you actually ran**, and for weeks that command differed from CI's in three ways nobody had compared.

**#53 is the sharpest instance in this record of a tool being believed over an instrument.** The
PR-status tool was not lying; it simply did not populate a field, and an empty list reads exactly
like an empty result. **The badge endpoint renders its conclusion as text and settled the question in
one call.** When a tool reports absence, the question to ask is whether it looked.

| 50 | **Fixing the bootstrap template armed the script that reads it, and the orchestrator nearly shipped that.** Removing the three deleted hooks from `scripts/settings-config.json` also removed the only occurrence of `3-level-flow` — which is the **sentinel** both setup scripts test to decide whether hooks are already installed. Guard fails -> `else` branch -> **`Copy-Item -Force` / `cp`, a wholesale replacement of the user's `settings.json`.** So a machine bootstrapped from the corrected template would have been overwritten on **every subsequent run**, and on this machine — where the hooks are already deleted, so `3-level-flow` appears nowhere — a setup run would have destroyed **26 `mcpServers` entries including the push gate registered hours earlier.** Sentinel changed to `stop-notifier`, verified present in the template, in the live file and in the guard | The orchestrator, checking what its own one-line fix touched downstream |
| 51 | **And the orchestrator flipped that file's line endings while fixing it** — wrote LF over a CRLF file, turning a 20-line edit into an 85-line churn. Caught by reading `git diff --stat` rather than trusting the write. **This is the fourth instance in this record**: two subagent mutation harnesses did it, `verify_plugin_conformance.py` was flipped whole by something unattributed, and now this. `Path.write_text` and `io.open(..., "w")` both normalise silently on Windows | The orchestrator, immediately, from the diffstat |

**#50 is the sharpest example in this record of a fix that is correct in isolation and dangerous in
composition.** The template change was right, minimal, tested and paired with a negative — and it
would have converted a dormant hazard into an active one on the next `setup-global-claude` run,
because nothing connected the file's *contents* to the string another file *greps it for*. **The
class is not "stale citation" but "implicit coupling through a literal", and no gate in this
repository detects it.**

| 48 | **The premise scan contracted the defect class it was built to hunt.** `premise_scan_bh` verified the `VERSION` vs `CLAUDE.md` contradiction as "STILL TRUE. MEASURED" and was committed 2026-08-02 at 10:35 and 10:56. **The fix landed at 15:30 the same day.** The verdict was correct when written and false four hours later, and it stayed in the record for two days — so a scan whose entire purpose was finding stale premises became one, in under a working day | V2-037's author, refusing to fix a defect it had not reproduced |
| 49 | **Running this repository's unit suite MUTATES TRACKED FILES.** `tests/test_sync_version.py` shells out to `scripts/tools/sync-version.py`, which rewrites `CLAUDE.md`, `README.md`, `SRS.md` and `langgraph_engine/__init__.py` to match `VERSION`. Confirmed: all four are modified in the working tree, and **the version bump in them cannot be attributed** — it may have come from V2-036 or from any full-suite run, including mine. Directly hazardous to this effort's commit hygiene: the orchestrator has been blanket-restoring three of those four files to strip date stamps, **which would now silently revert the 2.0.0 bump** | V2-037's author, unable to attribute a change it had not made |

**#49 is the most operationally dangerous entry in this record**, because it makes a routine verification
step a writer. Every "run the full suite, then commit" cycle in this sprint was also a
version-propagation step, and nobody knew. It also means the restore-then-commit habit that protected
against the engine's date stamps is **actively wrong from this commit onward** — the four files must be
inspected hunk by hunk, as `SRS.md` already had to be, rather than restored wholesale.

| 46 | **The hook deletion is not durable: the bootstrap template re-creates all three.** `scripts/settings-config.json` still registers `UserPromptSubmit`, `PreToolUse` and `PostToolUse` — verified after the migration. It is the template `~/.claude/settings.json` is bootstrapped from, and the removal script does not touch it. **Anyone setting up a machine from it re-creates exactly what V2-027 just deleted**, with no gate noticing | V2-028's author, looking for what the deletion did not reach |
| 47 | **The gate that bans fixed pipeline timeouts cannot see the engine's own entry point.** `verify_no_fixed_timeouts.py`'s `SCAN_SCOPE` is `("langgraph_engine", "plugin")` — `scripts/` is excluded. `scripts/3-level-flow.py:539` holds `ORCHESTRATION_TIMEOUT_SEC = 300`, used at `:555` as a wall-clock abort on the pipeline path. **A FIXED_LITERAL on exactly the surface NFR-2 governs, invisible to the gate written to ban it** | V2-028's author |

**#46 is the same shape as #39 — a control that exists and is not reached.** The deletion was executed
correctly, verified by handshake, and backed up; and it is still undone by one untouched template
file. **A migration is durable only when the thing that recreates the old state is also changed**, and
nothing in V2-027's acceptance criteria mentions that file.

| 44 | **The v1.20 step renumbering silently voided the per-step timeout table, and nothing noticed for the whole era.** `timeout_wrapper.STEP_TIMEOUTS` was keyed `{0,8,9,10,11,12,13,14}` — verified at HEAD — which was the **pre-v1.20** numbering. The live wrapped steps are `{2,3,4,5,6,7,8}`. **Intersection: `{8}`.** So six of seven wrapped steps ran with **no deadline at all**, and the seventh — now *Final Telemetry & Summary* — inherited the **900-second** budget written for *GitHub Issue Creation*. The table's own comment (*"v1.15.2: removed dead entries for steps 1,2,3,4,5,6,7"*) was correct under the old scheme and became actively misleading under the new one. A test, `TestStepTimeout`, was **pinning the stale table and passing** | V2-035's author, resolving the call sites from the AST instead of reading the dict |
| 45 | **`run_pr_workflow` is not absent — see the escalation on #40.** Recorded separately here because it changes that entry's severity rather than adding a new defect | V2-034's author |

**#44 is the renumbering-drift class at its most expensive.** The v1.20 rename is documented in
`CLAUDE.md` as a deliberate, tracked, domain-driven renumbering — and it still left a live control
table keyed to the old scheme, guarded by a test that asserted the old scheme too. **Both the code
and its test agreed with each other and neither agreed with the pipeline.** That is why the fix came
from resolving the actual `_run_step` call sites rather than reading either.

| 42 | **The durable checkpointer does not exist at runtime, and asking for it silently returns a non-durable one.** Verified: `langgraph.checkpoint.sqlite` and `langgraph_checkpoint_sqlite` both raise `ModuleNotFoundError`; `_SQLITE_SAVER_AVAILABLE` is `False`; and `CheckpointerManager.get_default_checkpointer(use_sqlite=True)` returns **`langgraph.checkpoint.memory.InMemorySaver`**. `requirements.txt:31` declares `langgraph-checkpoint-sqlite>=1.0.0` (absent) and `:7` pins `langgraph<1.0.0` while 1.1.6 is installed. The degradation is **triple-silent**: `checkpointer.py:126` catches `(ImportError, Exception)` and falls back with no log, and `orchestrator.py:786,850` catch `Exception` and compile the graph with **no checkpointer at all** | V2-031's author; reproduced independently by the orchestrator |
| 43 | **V2-026's checkpointer finding was half right, and the half that was wrong is the half that mattered.** It reported `SqliteSaver` configured with `thread_id` as the session id. The **configuration** is real (`checkpointer.py:253` does set `thread_id`); the **object** is not. A configuration check confirmed a durability claim that the runtime does not honour — the same shape as #29, where a count matched its source and the noun was wrong | V2-031's author, resolving the import rather than reading the config |

**#42 and #43 together are why AC 1's parenthetical mattered.** The criterion said to use "the existing
checkpoint writer" and pointed at the wrong one. The genuinely durable writer is `CheckpointManager`
(file/JSON) — the same component OAQ 1 named as owning crash recovery in entry 26. **Had the author
followed the citation instead of resolving it, the crash-resume test would have exercised an
in-memory saver and passed, certifying durability that does not exist.**

> **ESCALATED 2026-08-04.** V2-033 recorded the PR modules as *absent*. **`run_pr_workflow` is not
> absent.** It is at `scripts/github_pr_workflow/versioning.py:264` (verified), and its own docstring
> enumerates: *"3. Create PR ... 5. **Merge PR** ... 7. Version bump + CHANGELOG on main"*, with
> *"Called from stop-notifier.py when `.session-work-done` flag exists."*
>
> **DE-ESCALATED IN PART, SAME DAY, AND THE CORRECTION IS THE ORCHESTRATOR'S.** I wrote that the
> barrier was "a **one-line** search-path bug" and that fixing it "would arm all of it". **That
> overstates the risk.** `scripts/github_pr_workflow/__init__.py` re-exports **only `main`** (verified),
> so `github_pr_workflow.run_pr_workflow` raises `AttributeError` regardless of `sys.path`. **Two
> independent things must change, not one.** The hazard is real and the severity was wrong.
>
> **The call-site citations also drifted, inside this session, in the direction nobody watches for.**
> I cited `core.py:319, :363, :483`; they are now `:128, :172, :292`, and the file is 315 lines. Those
> citations were **correct when written** — verified against `463451e`, where `core.py` was 506 lines
> and the calls sat exactly there. V2-034 then retired 7 dead references and the file **shrank**.
> Correction 28 recorded citation drift from documents *growing*; this is the same defect from a file
> **shrinking**, over a few hours, in a record whose entire purpose is to stay checkable.

**#40 is the most dangerous finding in this record and it was found incidentally.** The issue asked
only for a spawn census; the hazard surfaced because the author traced what the hook actually reaches
rather than what it is documented to do. **A dormant defect that is dormant only because of a missing
file is not fixed — it is armed**, and the file's absence is the kind of thing a future cleanup
"restores" without knowing why it was gone.

**#38 and #39 are both mine and both are process failures rather than knowledge failures.** #38 is
correction 27's rule again — a fact restated from working memory when one command would have settled
it — except this time it was *inside a brief*, where a wrong premise steers an agent's design rather
than merely misinforming a reader. **The agent's refusal to accept it is what saved the design**, and
that only worked because the brief also told it to re-measure everything. #39 is worse in a quiet
way: I found the unwired-gate defect, wrote it into this record, and then committed a gate without
wiring it. **Recording a lesson is not the same as having learned it.**

**#35 is the more uncomfortable of the two, because half of it is mine.** I rewrote the Level 0 path
scanner, wrote its docstring, added nine tests and reported it fixed — and it still only recognises
one of the two ways a Windows drive path is written. The tests I wrote all used the backslash form,
so every one of them passed while the gap sat untouched. **A test suite written by the same person
who wrote the pattern inherits that person's blind spot**; the forward-slash form was found by a
different agent solving a different problem. `verify_home_paths` now covers this repository for that
class, so the hole is contained rather than closed — the Level 0 check itself is still half-blind and
that is recorded, not fixed.

**#33 and #34 are the same shape as #31 — an automatic process degrading work nobody was watching.**
#33 is the more serious: an auto-fix that runs unattended and rewrites string literals can silently
break any file it touches, and it fires on a check whose premise (backslash means path) is wrong for
Python source. **#34's lesson is narrower and mine: never `git restore` a whole file to drop
generated churn when a real edit is also in it** — inspect the diff and revert only the hunks that
are noise.

**#31 and #32 close the loop on the rule this project keeps relearning: a check is only as good as its
ability to fail, and that ability can decay silently.** The control was correct when written and
became vacuous-then-broken without anyone touching it. It is now anchored to the complete build of
the same run, so it cannot erode again — and, proven at the time of the fix, it still fails when the
cap is raised above the file count. **Measured 2026-08-03: complete build 452 files / 4448 methods
against floors of 411 / 3506 — a build could lose 942 methods and still clear the floor.** The
literals were deliberately NOT re-baselined, because `phase-5-uml/callgraph_coverage_probe.md` cites
them and moving them silently would break that provenance.

**#29 and #30 are one lesson from two directions: a number can be verified against its source and
still be false.** #29's count matched its array exactly and was still wrong about *what it counted*;
#30's scan was internally consistent and still blind to two files because it only read one language.
Both survived a phase whose explicit job was premise-checking. **Verifying a figure against the
document it came from is not verification — only re-deriving it from the artefact is.**

**#28 is the defect class already recorded at #23-25 — citation drift from document growth — but this
is the first time it was measured as a *population* rather than found one at a time.** Only the four
that batch D's next agent will actually read were re-anchored; **the other 32 are recorded and left**,
because a mass rewrite would drift again on the next edit. The durable fix is to cite by heading
rather than by line, and that is a decision for the reviewer, not a change to make silently.

**#27 is the second instance of the same root cause as #19-20: a fact restated from working memory
when the source was one command away.** Both were caught only because something else prompted a
re-read. The rule that follows is narrow and mechanical — **an identifier that another person will
use to look something up (commit hash, issue number, line number, file path) gets read from the tool
that owns it at the moment of writing, never recalled.**

**Of these, only #6 was authoring fabrication.** The rest were accurate citation of imperfect
measurements, or errors originating in the orchestrator's own briefs. That is the dominant failure
mode in this run: not agents inventing facts, but faithful propagation of unverified ones. Treat
cited Phase 0 numbers as **best available**, not verified.

**Two rules came out of this that apply to everything built from here:**

1. **Any check needs a companion negative test proving it can fail.** Otherwise it is a green light
   with no mechanism behind it.
2. **Any embedded or generated check must be executed from its stored form, not its authored form.**
   Defect #18 was invisible to every method except this one, and it was found in the same pass that
   created it.

**These two rules have no owner.** They were written to bind **FR-25 and FR-26** — but those are
**PROPOSED IDs that exist only in `phase-2-validation/advisory_items.json`**, hedged as "(proposed)"
in every occurrence. **`prd-v2.md` stops at FR-24.** Neither proposal has been accepted into the
requirement set, sized, or assigned. **This is a decision for you** (see section 2).

*Recorded as correction #21: an earlier revision of this very section stated the rules were "binding
on FR-25 and FR-26" with the "(proposed)" hedge dropped — present-tense-as-existing framing, the
exact leak `hallucination_report_sequencing.json` was checking for, committed in the document that
catalogues that defect class. Found by the Phase 5 SRS agent contradicting its own brief.*
