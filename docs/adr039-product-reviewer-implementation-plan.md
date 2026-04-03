# ADR-039 Product Skill Reviewer Implementation Plan

## Scope

This document defines the implementation plan for applying [ADR-039](/E:/ai/LEE-Lite-skill-first/ssot/adr/ADR-039-Reviewer%20%E8%83%BD%E5%8A%9B%E6%8F%90%E5%8D%87%E9%87%87%E7%94%A8%E5%88%86%E5%B1%82%20Review%20Contract%20%E4%B8%8E%20Coverage%20Gate%20%E5%9F%BA%E7%BA%BF.MD) to the product workflow skills:

- `ll-product-raw-to-src`
- `ll-product-src-to-epic`
- `ll-product-epic-to-feat`

The plan is constrained by ADR-039 phase-1 scope:

- force `coverage` output into review artifacts
- make gate block on `missing coverage`, `not_checked`, and `blocker_count > 0`
- do not require a full review expert system in the first rollout

## Current State

The product skills already have most of the runtime surfaces needed for ADR-039:

- workflow contracts in `ll.contract.yaml`
- executor and supervisor role prompts
- prose `review-checklist.md`
- `document_test` reports with `test_outcome`, `defect_counts`, `recommended_next_action`, and `sections`
- gate integration and `freeze_requires`
- package readiness validation and regression tests

The current gap is specific and narrow:

1. review artifacts do not emit ADR-039 `coverage` with a shared vocabulary
2. gate logic does not enforce `not_checked` or `blocker_count > 0`
3. review checklists are prose checklists, not machine-consumable required checks
4. there is no phase-1 review routing layer that maps product artifact families to the ADR-039 minimum dimensions

## Non-Goals

This plan does not try to do the following in the first rollout:

- build a standalone `Review Contract` runtime for all skills
- productize the full `Extract -> Coverage -> Judge -> Challenge` loop as a new engine
- introduce new skill-specific profile families
- migrate all governed workflows beyond the three product skills in one pass
- replace current `document_test` or `supervisor review` objects with a new artifact family

## Target State

After this plan:

- every product skill review path emits `coverage`
- `coverage` uses the ADR-039 phase-1 shared vocabulary:
  - `ssot_alignment`
  - `object_completeness`
  - `contract_completeness`
  - `state_transition_closure`
  - `failure_path`
  - `testability`
- every product skill emits a stable `blocker_count`
- gate blocks when:
  - coverage is missing
  - any required check is `not_checked`
  - `blocker_count > 0`
- `Review Contract` remains lightweight in phase 1:
  - embedded config
  - hard-coded family mapping
  - or small JSON/YAML fragments

## Canonical Integration Points

### Product Raw to SRC

- `skills/ll-product-raw-to-src/ll.contract.yaml`
- `skills/ll-product-raw-to-src/resources/checklists/review-checklist.md`
- `skills/ll-product-raw-to-src/scripts/raw_to_src_supervisor_phase.py`
- `skills/ll-product-raw-to-src/scripts/raw_to_src_runtime_support.py`
- `skills/ll-product-raw-to-src/scripts/raw_to_src_gate_integration.py`
- `skills/ll-product-raw-to-src/tests/test_raw_to_src_regressions.py`
- `skills/ll-product-raw-to-src/tests/test_raw_to_src_supervisor_regressions.py`

### Product SRC to EPIC

- `skills/ll-product-src-to-epic/ll.contract.yaml`
- `skills/ll-product-src-to-epic/resources/checklists/review-checklist.md`
- `skills/ll-product-src-to-epic/scripts/src_to_epic_behavior_review.py`
- `skills/ll-product-src-to-epic/scripts/src_to_epic_cli_integration.py`
- `skills/ll-product-src-to-epic/scripts/src_to_epic_runtime.py`
- `skills/ll-product-src-to-epic/scripts/src_to_epic_gate_integration.py`
- `skills/ll-product-src-to-epic/tests/test_src_to_epic_semantic_lock.py`

### Product EPIC to FEAT

- `skills/ll-product-epic-to-feat/ll.contract.yaml`
- `skills/ll-product-epic-to-feat/resources/checklists/review-checklist.md`
- `skills/ll-product-epic-to-feat/scripts/epic_to_feat_cli_integration.py`
- `skills/ll-product-epic-to-feat/scripts/epic_to_feat_runtime.py`
- `skills/ll-product-epic-to-feat/scripts/epic_to_feat_gate_integration.py`
- `skills/ll-product-epic-to-feat/tests/test_epic_to_feat_semantic_lock.py`

## Implementation Strategy

Roll out in one canary chain, not three parallel redesigns.

Order:

1. `ll-product-raw-to-src`
2. `ll-product-src-to-epic`
3. `ll-product-epic-to-feat`

Reason:

- `raw-to-src` already has the richest supervisor and document-test surface
- it is the upstream producer for the other two workflows
- it lets us prove the ADR-039 phase-1 gate semantics once, then copy the shape downstream

## Phase 0

Documentation and contract freeze.

Goals:

- align this plan with ADR-039 phase-1 scope
- freeze the shared coverage vocabulary for product skills
- choose one shared review-family mapping for the product chain

Decision for phase 1:

- all three product skills use the same artifact family route: `src_or_feat`
- no `Risk Profiles` beyond `default` in phase 1 unless a concrete blocker requires `workflow_sensitive`
- `Review Contract` is implemented as lightweight embedded metadata, not a new standalone subsystem

Outputs:

- this implementation plan
- ADR-039 as the governing policy

## Phase 1

Add phase-1 review coverage semantics to contracts.

Files:

- `skills/ll-product-raw-to-src/ll.contract.yaml`
- `skills/ll-product-src-to-epic/ll.contract.yaml`
- `skills/ll-product-epic-to-feat/ll.contract.yaml`

Contract additions:

- declare the ADR-039 minimum coverage vocabulary
- declare required checks for the product chain
- declare phase-1 gate block conditions
- record the lightweight review-family mapping

Recommended shape:

```yaml
review_phase1:
  artifact_family: src_or_feat
  risk_profiles:
    - default
  coverage_dimensions:
    - ssot_alignment
    - object_completeness
    - contract_completeness
    - state_transition_closure
    - failure_path
    - testability
  gate_block_conditions:
    - missing_coverage
    - required_check_not_checked
    - blocker_count_gt_zero
```

Constraints:

- do not add phase-1 custom dimensions per skill
- do not add exception rules in the first pass
- do not introduce a new artifact family for each workflow

## Phase 2

Emit structured coverage and blocker count from the real review path.

Files:

- `skills/ll-product-raw-to-src/scripts/raw_to_src_supervisor_phase.py`
- `skills/ll-product-src-to-epic/scripts/src_to_epic_behavior_review.py`
- `skills/ll-product-epic-to-feat/scripts/epic_to_feat_runtime.py`
- `skills/ll-product-src-to-epic/scripts/src_to_epic_cli_integration.py`
- `skills/ll-product-epic-to-feat/scripts/epic_to_feat_cli_integration.py`

Responsibilities:

- append `coverage` to existing review artifacts
- append `required_checks`
- append `blocker_count`
- keep current findings and verdict payloads; do not replace them

Minimum output shape:

```json
{
  "coverage": {
    "ssot_alignment": "checked",
    "object_completeness": "checked",
    "contract_completeness": "partial",
    "state_transition_closure": "checked",
    "failure_path": "not_checked",
    "testability": "checked"
  },
  "required_checks": [
    "ssot_alignment",
    "object_completeness",
    "contract_completeness",
    "state_transition_closure",
    "failure_path",
    "testability"
  ],
  "blocker_count": 1
}
```

Rules:

- `coverage` is a declaration of review scope, not proof of correctness
- findings stay authoritative for issue detail
- phase-1 challenge output is optional
- if current review logic cannot confidently evaluate a dimension, it must emit `not_checked`, not invent `checked`

## Phase 3

Wire gate blocking into the existing runtime path.

Files:

- `skills/ll-product-raw-to-src/scripts/raw_to_src_runtime_support.py`
- `skills/ll-product-raw-to-src/scripts/raw_to_src_runtime.py`
- `skills/ll-product-src-to-epic/scripts/src_to_epic_runtime.py`
- `skills/ll-product-epic-to-feat/scripts/epic_to_feat_runtime.py`

Responsibilities:

- validate that review artifacts contain `coverage`
- reject unknown phase-1 coverage keys during gate parsing
- block on missing required checks
- block on any `not_checked`
- block on `blocker_count > 0`

Implementation rule:

- integrate into current readiness and package validation paths
- do not create a parallel “review gate” runtime
- reuse current `validate_document_test_report(...)` and package-readiness checks where possible

## Phase 4

Align prompts and checklists with the new machine-readable path.

Files:

- `skills/ll-product-raw-to-src/resources/checklists/review-checklist.md`
- `skills/ll-product-src-to-epic/resources/checklists/review-checklist.md`
- `skills/ll-product-epic-to-feat/resources/checklists/review-checklist.md`
- `skills/ll-product-raw-to-src/agents/supervisor.md`
- `skills/ll-product-src-to-epic/agents/supervisor.md`
- `skills/ll-product-epic-to-feat/agents/supervisor.md`

Changes:

- rewrite prose checklist items to align with the six shared coverage dimensions
- explicitly tell the reviewer when to emit `not_checked`
- require `blocker_count` consistency with findings severity
- keep domain-specific review guidance, but map it to the shared vocabulary

This phase is deliberately downstream of runtime wiring.

Reason:

- the machine path should be stable before prompts are expanded
- otherwise the team will overfit prompt text without stable gate semantics

## Phase 5

Shared review support extraction, but only after the three skills behave the same way.

Candidate shared modules:

- `cli/lib/product_review_phase1.py`
- `cli/lib/product_review_coverage.py`
- `cli/lib/product_review_gate_rules.py`

Move to shared code only if:

- all three product skills emit the same phase-1 fields
- gate logic is duplicated in materially identical ways
- tests prove the shared path does not weaken current domain-specific checks

Do not start here.

## Testing Plan

### Unit and Regression

Extend or add tests for:

- coverage field presence
- vocabulary validation
- `not_checked` gate rejection
- `blocker_count > 0` gate rejection
- compatibility with existing `document_test_report.json` consumers

Target files:

- `skills/ll-product-raw-to-src/tests/test_raw_to_src_regressions.py`
- `skills/ll-product-raw-to-src/tests/test_raw_to_src_supervisor_regressions.py`
- `skills/ll-product-src-to-epic/tests/test_src_to_epic_semantic_lock.py`
- `skills/ll-product-epic-to-feat/tests/test_epic_to_feat_semantic_lock.py`

Recommended new tests:

- `tests/unit/test_product_review_phase1_contracts.py`
- `tests/unit/test_product_review_phase1_gate_rules.py`

### Validation Order

1. contract updates parse cleanly
2. per-skill review artifact generation emits `coverage`
3. gate rejects `missing coverage`
4. gate rejects `not_checked`
5. gate rejects `blocker_count > 0`
6. existing positive paths still produce gate-ready packages when coverage is complete and blocker count is zero

## Risks

- the team may try to introduce phase-1 custom coverage dimensions per skill
- gate logic may be duplicated inconsistently across three runtimes
- prompt updates may come before runtime validation and create false confidence
- `document_test` and `review_report` may drift if only one artifact gets `coverage`
- `blocker_count` may be derived inconsistently from existing severity vocabularies

## Mitigations

- freeze the six shared coverage dimensions before code changes
- ship `raw-to-src` first and replay the same shape downstream
- keep `coverage` additive; do not redesign current review artifacts in phase 1
- centralize blocker derivation rules before extracting shared modules
- reject unknown coverage keys in gate parsing

## Acceptance Criteria

The implementation is complete when:

1. all three product skills emit ADR-039 phase-1 `coverage`
2. all three product skills use the same six-key coverage vocabulary
3. all three product skill gates block on `missing coverage`
4. all three product skill gates block on `not_checked`
5. all three product skill gates block on `blocker_count > 0`
6. no new skill-specific profile or exception-rule system is introduced in phase 1
7. current positive workflow paths remain valid when coverage is complete and blocker count is zero

## Recommended Execution Order

1. freeze the six-key coverage vocabulary in contracts
2. implement `raw-to-src` coverage emission
3. implement `raw-to-src` gate blocking
4. replay the same pattern into `src-to-epic`
5. replay the same pattern into `epic-to-feat`
6. align checklists and supervisor prompts
7. only then evaluate whether shared support code is warranted
