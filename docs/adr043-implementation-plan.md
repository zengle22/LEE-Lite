# ADR-043 Implementation Plan

## Scope

This document defines the implementation plan for [ADR-043](E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-043-当前 Governed Skill 输出采用语义覆盖合同、双轨评审视图与可执行 Completeness Gate 基线.MD).

Phase-1 scope is intentionally narrow and only covers the workflows already present in the repository with active runtime validators and freeze gates:

- `ll-product-epic-to-feat`
- `ll-dev-feat-to-tech`
- `ll-dev-feat-to-proto`
- `ll-dev-proto-to-ui`

The target artifacts are:

- `feat_freeze_package`
- `tech_design_package`
- `prototype_package`
- `ui_spec_package`

## Goals

1. Introduce a machine-readable `semantic-dimensions.json` as the single semantic SSOT for each phase-1 skill.
2. Replace hand-maintained `semantic-checklist.md` with generated checklist views derived from that SSOT.
3. Upgrade the formal contract surface for each phase-1 skill so `output/contract.yaml`, `output/schema.json`, and where needed `ll.contract.yaml` explicitly declare the ADR-043 semantic objects.
4. Enforce ADR-043 gate semantics with layered validation:
   - L1 hard rules
   - L2 weak heuristics
   - L3 AI review output
5. Prove the rollout on a real canary chain already present in the repo, not on synthetic examples.

## Current State

The repository already has most of the runtime surfaces ADR-043 needs.

### Product EPIC to FEAT

Current files:

- `skills/ll-product-epic-to-feat/output/contract.yaml`
- `skills/ll-product-epic-to-feat/output/schema.json`
- `skills/ll-product-epic-to-feat/output/semantic-checklist.md`
- `skills/ll-product-epic-to-feat/output/template.md`
- `skills/ll-product-epic-to-feat/scripts/epic_to_feat_derivation.py`
- `skills/ll-product-epic-to-feat/scripts/epic_to_feat_runtime.py`
- `skills/ll-product-epic-to-feat/scripts/epic_to_feat_cli_integration.py`
- `skills/ll-product-epic-to-feat/tests/test_epic_to_feat_review_phase1.py`
- `skills/ll-product-epic-to-feat/tests/test_epic_to_feat_semantic_lock.py`
- `tests/unit/test_lee_product_epic_to_feat.py`

Observed project-specific gap:

- `feat_freeze_package` already has rich structure, but derivation still emits generic fallback such as `Primary product actor` and `secondary product actor`.
- current runtime validation checks for structure and presence, not semantic density.

### FEAT to TECH

Current files:

- `skills/ll-dev-feat-to-tech/output/contract.yaml`
- `skills/ll-dev-feat-to-tech/output/schema.json`
- `skills/ll-dev-feat-to-tech/output/semantic-checklist.md`
- `skills/ll-dev-feat-to-tech/output/template.md`
- `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_validation.py`
- `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_package_content.py`
- `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_package_builder.py`
- `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_runtime.py`
- `tests/unit/test_lee_dev_feat_to_tech.py`
- `tests/unit/test_lee_dev_feat_to_tech_execution_metadata.py`
- `tests/unit/support_feat_to_tech.py`

Observed project-specific gap:

- there is no skill-local `tests/` directory; the effective test surface is in `tests/unit`.
- `tech_design_package` already has `design_consistency_check`, but it still mainly proves structural completeness.
- generated samples already show generic state machine and weak glossary ownership lines passing through.

### FEAT to PROTOTYPE

Current files:

- `skills/ll-dev-feat-to-proto/output/contract.yaml`
- `skills/ll-dev-feat-to-proto/output/schema.json`
- `skills/ll-dev-feat-to-proto/output/semantic-checklist.md`
- `skills/ll-dev-feat-to-proto/output/template.md`
- `skills/ll-dev-feat-to-proto/scripts/feat_to_proto.py`
- `skills/ll-dev-feat-to-proto/tests/test_feat_to_proto_workflow.py`
- `tests/unit/test_cli_runtime_feat_to_proto.py`

Observed project-specific gap:

- this workflow already has strong structural checks for journey, shell, route smoke, reachability, and placeholder lint.
- the missing piece is not file presence but semantic coverage of state, feedback, exception, and owner-bound delta scope.

### PROTOTYPE to UI

Current files:

- `skills/ll-dev-proto-to-ui/output/contract.yaml`
- `skills/ll-dev-proto-to-ui/output/schema.json`
- `skills/ll-dev-proto-to-ui/output/semantic-checklist.md`
- `skills/ll-dev-proto-to-ui/output/template.md`
- `skills/ll-dev-proto-to-ui/scripts/proto_to_ui.py`
- `skills/ll-dev-proto-to-ui/scripts/feat_to_ui.py`
- `skills/ll-dev-proto-to-ui/tests/test_proto_to_ui_workflow.py`
- `tests/unit/test_cli_runtime_feat_to_ui.py`
- `tests/unit/test_lee_dev_feat_to_ui.py`
- `tests/unit/support_feat_to_ui.py`

Observed project-specific gap:

- `ui-semantic-source-ledger.json` already exists and is the strongest semantic evidence base in the phase-1 chain.
- the remaining gap is to turn that ledger plus current prose sections into explicit semantic coverage and gate results.

## Canary Chain

Use the active `SRC-003` chain as the canary, because the repository already has live assets across EPIC, FEAT, surface-map, TECH, PROTOTYPE, and UI.

Relevant assets already present:

- `ssot/epic/EPIC-SRC-003-001__gate-execution-runner.md`
- `ssot/feat/FEAT-SRC-003-001__批准后-ready-job-生成流.md`
- `ssot/feat/FEAT-SRC-003-002__runner-用户入口流.md`
- `ssot/mapping/SURFACE-MAP-FEAT-SRC-003-001__批准后-ready-job-生成流-surface-map-package.json`
- `ssot/mapping/SURFACE-MAP-FEAT-SRC-003-002__runner-用户入口流-surface-map-package.json`
- `ssot/tech/SRC-003/TECH-SRC-003-001__批准后-ready-job-生成流-technical-design-package.md`
- `ssot/tech/SRC-003/TECH-SRC-003-002__runner-用户入口流-technical-design-package.md`
- `ssot/prototype/SRC-003/PROTO-RUNNER-OPERATOR-MAIN/index.html`
- `ssot/ui/SRC-003/UI-RUNNER-OPERATOR-SHELL.md`
- `.workflow/runs/src003-adr042-epic2feat-20260407-r1/...`
- `.workflow/runs/src003-adr042-tech-001-20260407-r1/...`
- `.workflow/runs/src003-adr042-tech-002-20260407-r1/...`

Why this canary is the right one:

- it already exercises ADR-042 `surface_map` ownership binding
- it already has real generated `TECH` output
- it already has prototype and UI owners under `ssot/`
- it is new enough that we can still tighten contracts without broad migration cost

Canary policy for phase 1:

- treat `EPIC-SRC-003-001` as the upstream replay input for `ll-product-epic-to-feat`
- freeze an explicit canary manifest that maps replayed FEAT outputs to the existing `FEAT-SRC-003-*` and `SURFACE-MAP-FEAT-SRC-003-*` namespace before any gate results are interpreted
- treat current `ssot/` artifacts as observational baseline, not automatic golden fixtures for the new semantic gate
- if a historical sample fails the new gate, classify it as `baseline_debt` unless the replayed phase-1 output is expected to pass and still fails on the same dimension
- phase-1 success is judged on replayed canary outputs and their lineage, not on blanket exemption for old samples

## Non-Goals

This plan does not try to do the following in phase 1:

- introduce ADR-043 to `raw-to-src`, `src-to-epic`, `tech-to-impl`, or `feat-to-testset`
- build a generic NLP engine that fully judges semantic quality
- retroactively rewrite all historical SSOT packages in `ssot/`
- replace current bundle markdown, review reports, or freeze gates with a brand-new artifact family
- solve final review UX for every workflow family in one pass

## Target State

After this plan:

- every phase-1 skill has `output/semantic-dimensions.json`
- every phase-1 skill updates `output/contract.yaml` and `output/schema.json` so the semantic objects are part of the formal repository contract surface
- any skill-level runtime contract that enumerates review/gate evidence updates `ll.contract.yaml` accordingly
- `semantic-dimensions.json` is the single SSOT for semantic completeness
- `output/semantic-checklist.md` is generated from that SSOT and not hand-maintained
- review/completeness reports emit `semantic_coverage`
- freeze gates block on `semantic_pass = false`
- validation is layered:
  - L1 hard rules block directly
  - L2 weak rules produce partial/heuristic signals
  - L3 AI review remains a review artifact, not a fake deterministic validator
- review output exposes three stable views:
  - Narrative
  - Checklist
  - Diff

## Implementation Strategy

Roll out upstream to downstream and prove each layer before moving on.

Order:

1. contract surface alignment
2. shared semantic support layer
3. prompt and review wiring
4. `ll-product-epic-to-feat`
5. `ll-dev-feat-to-tech`
6. `ll-dev-feat-to-proto`
7. `ll-dev-proto-to-ui`
8. `SRC-003` canary replay and baseline adjudication

Reason:

- `epic-to-feat` is the first place where semantic debt becomes formal package debt
- if contract/schema are not updated first, runtime semantics and repository contracts drift immediately
- L3 review has to be wired before per-skill rollout or the plan will only ship L1/L2 rules in practice
- `feat-to-tech` currently has the highest risk of “section exists but semantics thin”
- `feat-to-proto` and `proto-to-ui` already have better structural discipline, so they should consume the shared layer after FEAT/TECH semantics are stable

## Phase 0

Documentation and contract freeze.

Goals:

- align this plan with ADR-043
- freeze the phase-1 core semantic dimensions for the four skills
- freeze the validation layering model
- freeze the canary chain
- freeze the contract delta matrix for `output/contract.yaml`, `output/schema.json`, handoff fields, and review/gate projections

Decisions to lock in:

- each skill gets at most 5-6 `core_dimensions`
- everything else becomes `auxiliary_dimensions`
- `semantic-dimensions.json` is the only semantic SSOT
- `semantic-checklist.md` must be generated
- `semantic_pass` only depends on:
  - required dimension coverage status
  - L1/L2 validator output
  - accepted review projection rules

Outputs:

- ADR-043
- this implementation plan
- a phase-1 canary manifest for `SRC-003` replay and baseline adjudication

## Phase 1

Freeze the phase-1 contract delta before runtime rewiring.

Files to update in every covered skill:

- `output/contract.yaml`
- `output/schema.json`
- `ll.contract.yaml` when the skill-level contract enumerates review/gate evidence or runtime outputs
- `output/semantic-dimensions.json`

Contract rules:

- `output/contract.yaml` and `output/schema.json` must declare `semantic-dimensions.json` as a formal companion contract artifact, not just an implementation detail
- per-skill report and gate schemas must explicitly carry `semantic_coverage` and `semantic_pass`
- handoff schemas must explicitly carry `semantic_ready` and `open_semantic_gaps`
- `ll.contract.yaml` must be updated wherever skill-level runtime evidence or report artifacts need the new semantic fields to be considered contractually valid
- each `semantic-dimensions.json` file must define:
  - `artifact_type`
  - `schema_version`
  - `core_dimensions`
  - `auxiliary_dimensions`
- each `core_dimension` must define:
  - `id`
  - `required`
  - `review_question`
  - `evidence_targets`
  - `l1_rules`
  - `l2_rules`
- `auxiliary_dimensions` can omit gate-specific validation rules

Frozen phase-1 core dimensions:

### EPIC to FEAT

- `actor_and_intent`
- `flow_and_journey`
- `rules_and_constraints`
- `inputs_outputs_and_authority`
- `edge_cases_and_boundary`
- `acceptance_and_testability`

### FEAT to TECH

- `carrier_and_module_responsibility`
- `contracts_and_field_semantics`
- `state_and_runtime_flow`
- `failure_and_compensation`
- `integration_and_compatibility`
- `ownership_and_constraints`

### FEAT to PROTOTYPE

- `journey_and_surface_slice`
- `entry_exit_and_initial_view`
- `cta_and_container_semantics`
- `primary_states_and_feedback`
- `exception_retry_skip_paths`
- `shell_alignment_and_owner_binding`

### PROTOTYPE to UI

- `page_goal_and_task_flow`
- `information_hierarchy_and_regions`
- `field_action_validation_and_feedback`
- `state_behaviors`
- `component_container_contracts`
- `source_ledger_and_inference_disclosure`

## Phase 2

Introduce a shared semantic support layer before per-skill rewiring.

Recommended new shared modules:

- `cli/lib/workflow_semantic_dimensions.py`
- `cli/lib/workflow_semantic_projection.py`
- `cli/lib/workflow_semantic_coverage.py`
- `cli/lib/workflow_semantic_validators.py`
- `cli/lib/workflow_semantic_diff.py`

Responsibilities:

- load `semantic-dimensions.json`
- generate checklist markdown from the SSOT
- compute `semantic_coverage`
- evaluate L1 and L2 rules
- build Narrative / Checklist / Diff review payloads
- expose a stable data model that per-skill schema updates can reference without custom one-off projections

Phase-1 constraint:

- do not build a large framework
- keep it small and file-based
- shared code should only cover repeated mechanics, not workflow-specific semantics

## Phase 2.5

Wire L3 review and review projections into actual agent and review entry points before skill rollout.

Files likely to change across the four skills:

- `agents/executor.md`
- `agents/supervisor.md`
- `agents/openai.yaml`
- `evidence/report.template.md`
- `evidence/execution-evidence.schema.json`
- `evidence/supervision-evidence.schema.json`

Skill-local review/gate producers to wire in this phase:

- `skills/ll-product-epic-to-feat/scripts/epic_to_feat_review_phase1.py`
- `skills/ll-product-epic-to-feat/scripts/epic_to_feat_gate_integration.py`
- `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_governance.py`
- `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_gate_integration.py`
- `skills/ll-dev-feat-to-proto/scripts/feat_to_ui_gate_integration.py`
- `skills/ll-dev-proto-to-ui/scripts/feat_to_ui_gate_integration.py`

Implementation tasks:

1. make executor and supervisor prompts consume the skill-local `core_dimensions` and reviewer questions explicitly
2. require L3 review output to emit per-dimension judgment, evidence references, unresolved gaps, and reviewer-facing narrative anchors
3. ensure review/gate producers persist L3 results into existing review/completeness artifacts instead of leaving them as transient prompt output
4. make the review projection contract explicit:
   - Checklist view ships with the generated checklist and report anchors
   - Diff view ships with the same per-skill rollout that introduces semantic coverage
   - Narrative view ships in minimal form during per-skill rollout, with wording polish allowed later
5. update evidence schemas so L3 output is a required artifact when semantic review runs

## Phase 3

Wire ADR-043 into `ll-product-epic-to-feat`.

Files:

- `skills/ll-product-epic-to-feat/ll.contract.yaml`
- `skills/ll-product-epic-to-feat/output/contract.yaml`
- `skills/ll-product-epic-to-feat/output/schema.json`
- `skills/ll-product-epic-to-feat/output/semantic-dimensions.json`
- `skills/ll-product-epic-to-feat/output/semantic-checklist.md`
- `skills/ll-product-epic-to-feat/scripts/epic_to_feat_derivation.py`
- `skills/ll-product-epic-to-feat/scripts/epic_to_feat_runtime.py`
- `skills/ll-product-epic-to-feat/scripts/epic_to_feat_cli_integration.py`
- `skills/ll-product-epic-to-feat/scripts/epic_to_feat_gate_integration.py`
- `skills/ll-product-epic-to-feat/scripts/epic_to_feat_review_phase1.py`
- `skills/ll-product-epic-to-feat/output/template.md`
- `skills/ll-product-epic-to-feat/tests/test_epic_to_feat_review_phase1.py`
- `skills/ll-product-epic-to-feat/tests/test_epic_to_feat_semantic_lock.py`
- `tests/unit/test_lee_product_epic_to_feat.py`

Implementation tasks:

1. update `output/contract.yaml`, `output/schema.json`, and where applicable `ll.contract.yaml` so FEAT formally declares:
   - `semantic-dimensions.json`
   - `semantic_coverage`
   - `semantic_pass`
   - `semantic_ready`
   - `open_semantic_gaps`
2. replace hand-maintained semantic checklist with generated output
3. wire L3 review into `epic_to_feat_review_phase1.py` and gate integration so FEAT has a stable semantic review artifact producer
4. add `semantic_coverage` to:
   - `feat-review-report.json`
   - `feat-acceptance-report.json`
   - `feat-freeze-gate.json`
5. add placeholder detection for:
   - `Primary product actor`
   - `secondary product actor`
   - `None`
   - `TBD`
6. add FEAT-topic alignment checks for:
   - business flow
   - exception flow
   - authoritative output
7. add `semantic_ready` and `open_semantic_gaps` to `handoff-to-feat-downstreams.json`
8. ship all three review views in the same phase:
   - Narrative in current FEAT bundle/review surface
   - Checklist in generated checklist plus report anchors
   - Diff against upstream EPIC input and prior FEAT revision when present

Acceptance for this phase:

- FEAT package can fail semantically even when schema passes
- FEAT formal contracts and runtime outputs stay in sync
- generated checklist matches `semantic-dimensions.json`
- generic actor fallback is rejected
- L3 review output is persisted and visible to reviewers

## Phase 4

Wire ADR-043 into `ll-dev-feat-to-tech`.

Files:

- `skills/ll-dev-feat-to-tech/ll.contract.yaml`
- `skills/ll-dev-feat-to-tech/output/contract.yaml`
- `skills/ll-dev-feat-to-tech/output/schema.json`
- `skills/ll-dev-feat-to-tech/output/semantic-dimensions.json`
- `skills/ll-dev-feat-to-tech/output/semantic-checklist.md`
- `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_governance.py`
- `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_validation.py`
- `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_package_content.py`
- `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_package_builder.py`
- `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_runtime.py`
- `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_gate_integration.py`
- `tests/unit/test_lee_dev_feat_to_tech.py`
- `tests/unit/test_lee_dev_feat_to_tech_execution_metadata.py`
- `tests/unit/support_feat_to_tech.py`

Implementation tasks:

1. update `output/contract.yaml`, `output/schema.json`, and where applicable `ll.contract.yaml` so TECH formally declares the semantic contract and review fields
2. compute semantic coverage for the six TECH core dimensions
3. make `design_consistency_check` consume semantic coverage instead of only section presence
4. wire L3 review into `feat_to_tech_governance.py` and the gate path so semantic quality has an actual review source
5. tighten L1/L2 checks for:
   - generic state machine
   - `None` ownership lines
   - integration points too thin
   - exception sections copied from unrelated FEAT topic
6. append `semantic_coverage` to:
   - `tech-review-report.json`
   - `tech-acceptance-report.json`
   - `tech-freeze-gate.json`
7. add `semantic_ready` to `handoff-to-tech-impl.json`
8. ship all three review views in the same phase:
   - Narrative in the TECH bundle/report surface
   - Checklist in generated checklist plus report anchors
   - Diff against authoritative FEAT input and prior owner-aligned TECH revision

Acceptance for this phase:

- `tech_design_package` cannot reach `accepted` when glossary ownership is placeholder-level
- generic lifecycle text alone is insufficient for `state_and_runtime_flow`
- L3 review findings are visible in the same artifacts that carry gate status

## Phase 5

Wire ADR-043 into `ll-dev-feat-to-proto`.

Files:

- `skills/ll-dev-feat-to-proto/ll.contract.yaml`
- `skills/ll-dev-feat-to-proto/output/contract.yaml`
- `skills/ll-dev-feat-to-proto/output/schema.json`
- `skills/ll-dev-feat-to-proto/output/semantic-dimensions.json`
- `skills/ll-dev-feat-to-proto/output/semantic-checklist.md`
- `skills/ll-dev-feat-to-proto/scripts/feat_to_proto.py`
- `skills/ll-dev-feat-to-proto/scripts/feat_to_ui_gate_integration.py`
- `skills/ll-dev-feat-to-proto/output/template.md`
- `skills/ll-dev-feat-to-proto/tests/test_feat_to_proto_workflow.py`
- `tests/unit/test_cli_runtime_feat_to_proto.py`

Implementation tasks:

1. update `output/contract.yaml`, `output/schema.json`, and where applicable `ll.contract.yaml` so PROTOTYPE formally declares the semantic contract and review fields
2. compute prototype semantic coverage from:
   - journey structural spec
   - route map
   - reachability report
   - placeholder lint
   - review report
3. wire L3 review into the prototype gate/review path so experiential quality is captured as a durable artifact
4. add `semantic_coverage` to:
   - `prototype-completeness-report.json`
   - `prototype-review-report.json`
   - `prototype-freeze-gate.json`
5. fail semantic gate when:
   - happy path exists but no exception/retry/skip path is frozen
   - entry/initial view is missing
   - shell alignment or owner binding is unresolved
6. emit the three review views in the same rollout:
   - Narrative in `prototype-bundle.md`
   - Checklist in generated checklist output
   - Diff against upstream FEAT and current owner snapshot

Acceptance for this phase:

- prototype package can no longer pass based only on file presence plus route smoke
- review projections are available without waiting for a later cross-skill phase

## Phase 6

Wire ADR-043 into `ll-dev-proto-to-ui`.

Files:

- `skills/ll-dev-proto-to-ui/ll.contract.yaml`
- `skills/ll-dev-proto-to-ui/output/contract.yaml`
- `skills/ll-dev-proto-to-ui/output/schema.json`
- `skills/ll-dev-proto-to-ui/output/semantic-dimensions.json`
- `skills/ll-dev-proto-to-ui/output/semantic-checklist.md`
- `skills/ll-dev-proto-to-ui/scripts/proto_to_ui.py`
- `skills/ll-dev-proto-to-ui/scripts/feat_to_ui.py`
- `skills/ll-dev-proto-to-ui/scripts/feat_to_ui_gate_integration.py`
- `skills/ll-dev-proto-to-ui/output/template.md`
- `skills/ll-dev-proto-to-ui/tests/test_proto_to_ui_workflow.py`
- `tests/unit/test_cli_runtime_feat_to_ui.py`
- `tests/unit/test_lee_dev_feat_to_ui.py`
- `tests/unit/support_feat_to_ui.py`

Implementation tasks:

1. update `output/contract.yaml`, `output/schema.json`, and where applicable `ll.contract.yaml` so UI formally declares the semantic contract and review fields
2. turn `ui-semantic-source-ledger.json` into semantic evidence, not just provenance
3. compute semantic coverage for:
   - page goal
   - hierarchy
   - field/action/validation/feedback
   - state behaviors
   - component/container contracts
   - inference disclosure
4. wire L3 review into the UI review/gate path so implementation-facing quality has a stable reviewer artifact
5. append `semantic_coverage` to:
   - `ui-spec-completeness-report.json`
   - `ui-spec-review-report.json`
   - `ui-spec-freeze-gate.json`
6. add the three review views in the same rollout:
   - Narrative in the UI bundle/report surface
   - Checklist in generated checklist plus report anchors
   - Diff against:
     - prototype package
     - current shared UI owner

Acceptance for this phase:

- UI package cannot pass if it preserves structure but still hides AI inference or loses field/action semantics
- review projections are already present at skill integration time, not deferred

## Phase 7

Canary replay and baseline adjudication on the live `SRC-003` chain.

Implementation rules:

- replay from `EPIC-SRC-003-001` through the phase-1 skill chain with an explicit manifest that maps generated FEAT outputs to the existing `SRC-003` namespace
- evaluate both generated canary outputs and existing `ssot/` samples, but do not let historical sample drift mask runtime regressions
- record failures as one of:
  - `runtime_regression`
  - `baseline_debt`
  - `mapping_gap`
- only `runtime_regression` blocks phase-1 completion; `baseline_debt` and `mapping_gap` require tracked follow-up, not silent exemption

Validation targets:

- `FEAT-SRC-003-001`
- `FEAT-SRC-003-002`
- corresponding `SURFACE-MAP-FEAT-SRC-003-*`
- `TECH-SRC-003-001`
- `TECH-SRC-003-002`
- `PROTO-RUNNER-OPERATOR-MAIN`
- `UI-RUNNER-OPERATOR-SHELL`

Success conditions:

- semantic gate blocks generic placeholders now visible in sample output
- canary packages can still be revised into passing artifacts without breaking structural lineage
- current surface-map / owner model remains intact
- canary results distinguish baseline debt from real rollout regressions

## Testing Plan

### Unit and Workflow Tests

Extend or add tests for:

- contract/schema alignment for `semantic-dimensions.json`, `semantic_coverage`, `semantic_pass`, `semantic_ready`, and `open_semantic_gaps`
- `semantic-dimensions.json` presence and parseability
- generated checklist consistency
- L1 placeholder rejection
- L2 weak-rule emission
- `semantic_pass` gate rejection
- handoff `semantic_ready` propagation
- L3 review artifact persistence and shape
- per-skill Narrative / Checklist / Diff projection availability
- canary baseline classification (`runtime_regression` vs `baseline_debt` vs `mapping_gap`)

Primary test files:

- `skills/ll-product-epic-to-feat/tests/test_epic_to_feat_review_phase1.py`
- `skills/ll-product-epic-to-feat/tests/test_epic_to_feat_semantic_lock.py`
- `tests/unit/test_lee_product_epic_to_feat.py`
- `tests/unit/test_lee_dev_feat_to_tech.py`
- `tests/unit/test_lee_dev_feat_to_tech_execution_metadata.py`
- `tests/unit/test_cli_runtime_feat_to_proto.py`
- `skills/ll-dev-feat-to-proto/tests/test_feat_to_proto_workflow.py`
- `tests/unit/test_cli_runtime_feat_to_ui.py`
- `skills/ll-dev-proto-to-ui/tests/test_proto_to_ui_workflow.py`

Recommended new tests:

- `tests/unit/test_workflow_semantic_dimensions.py`
- `tests/unit/test_workflow_semantic_projection.py`
- `tests/unit/test_workflow_semantic_gate.py`

### Validation Order

1. contracts, schemas, and `semantic-dimensions.json` parse together
2. checklist generation is deterministic
3. L3 review wiring produces valid persisted artifacts before per-skill gate rollout
4. per-skill L1 validation blocks placeholder output
5. per-skill review/completeness artifacts emit `semantic_coverage`
6. freeze gates block `semantic_pass = false`
7. `SRC-003` canary replay still yields revisable, lineaged outputs with explicit baseline classification

## Risks

- the team may re-expand dimensions beyond 5-6 core dimensions per skill
- generated checklist and report logic may drift if generation is not centralized
- `feat-to-tech` may be hardest to stabilize because its current samples already mix strong structure with weak semantics
- `proto-to-ui` may become over-dependent on provenance and still under-specify interaction semantics
- existing historical SSOT under `ssot/` may fail new gates if replayed immediately
- canary namespace mapping may be ambiguous if replayed `epic-to-feat` outputs are not bound to the current `SRC-003` fixture set up front

## Mitigations

- freeze the small core dimension sets before code changes
- make `semantic-dimensions.json` the only source and generate everything else
- keep L1 strict and L2 conservative
- do not let L2 heuristics silently flip pass/fail without review visibility
- use `SRC-003` as a bounded canary before wider rollout
- keep historical migration out of phase 1
- freeze the canary manifest before replay so `mapping_gap` is handled as a data-baseline issue, not a semantic regression

## Acceptance Criteria

The implementation is complete when:

1. all four phase-1 skills have `output/semantic-dimensions.json`
2. all four phase-1 skills update `output/contract.yaml` and `output/schema.json` to declare the ADR-043 semantic surfaces, and update `ll.contract.yaml` where runtime evidence contracts require it
3. all four phase-1 skills generate `semantic-checklist.md` from that SSOT
4. all four phase-1 skills emit `semantic_coverage`
5. all four phase-1 freeze gates block on `semantic_pass = false`
6. the three review views are available in current bundle/report surfaces during each per-skill rollout, not only at the end
7. L3 review has a real prompt/agent/review-producer path and persists reviewer-visible output
8. `SRC-003` canary replay passes structural validation, enforces the new semantic gate semantics, and separates baseline debt from rollout regressions
9. no phase-1 validator tries to become a full free-form semantic judge

## Recommended Execution Order

1. freeze dimension sets and canary scope
2. freeze the contract/schema delta matrix
3. add shared semantic support modules
4. wire prompts, agents, and review producers for L3 output
5. integrate `ll-product-epic-to-feat`
6. integrate `ll-dev-feat-to-tech`
7. integrate `ll-dev-feat-to-proto`
8. integrate `ll-dev-proto-to-ui`
9. run `SRC-003` canary replay and baseline adjudication
10. only then decide whether to expand ADR-043 upstream or downstream
