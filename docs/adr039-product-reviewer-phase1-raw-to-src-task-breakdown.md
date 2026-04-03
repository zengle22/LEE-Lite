# ADR-039 Product Reviewer Phase 1 Raw-to-SRC Task Breakdown

## Scope

This document breaks Phase 1 of [ADR-039 Product Skill Reviewer Implementation Plan](/E:/ai/LEE-Lite-skill-first/docs/adr039-product-reviewer-implementation-plan.md) into executable work packages for the `ll-product-raw-to-src` canary.

This is not the downstream rollout plan for all product skills.

This document only covers:

- `ll-product-raw-to-src`
- ADR-039 phase-1 coverage semantics
- gate blocking on `missing coverage`, `not_checked`, and `blocker_count > 0`

## Goal

Make `ll-product-raw-to-src` the canary implementation of ADR-039 phase 1, so that:

- supervisor or review artifacts emit the six-key coverage declaration
- the same artifact also emits `required_checks` and `blocker_count`
- package readiness and freeze readiness reject missing coverage and incomplete review scope
- downstream product workflows can copy the exact same shape instead of redesigning it

## Constraints

- no standalone review runtime
- no new skill-specific artifact family
- no phase-1 custom coverage dimensions
- no exception-rule framework in the canary
- no weakening of current structural, semantic, or document-test checks

## Existing Runtime Path

Current `raw-to-src` canary path already exists:

1. input validation
2. executor generation
3. semantic review
4. document test
5. supervisor phase
6. package validation
7. freeze readiness
8. gate pending handoff

The ADR-039 work must attach to this path, not replace it.

## Canonical Files

### Contract and policy

- `skills/ll-product-raw-to-src/ll.contract.yaml`
- `skills/ll-product-raw-to-src/resources/checklists/review-checklist.md`

### Review and supervision

- `skills/ll-product-raw-to-src/scripts/raw_to_src_supervisor_phase.py`
- `skills/ll-product-raw-to-src/scripts/raw_to_src_records.py`

### Runtime and gate

- `skills/ll-product-raw-to-src/scripts/raw_to_src_runtime_support.py`
- `skills/ll-product-raw-to-src/scripts/raw_to_src_runtime.py`
- `skills/ll-product-raw-to-src/scripts/raw_to_src_gate_integration.py`

### Tests

- `skills/ll-product-raw-to-src/tests/test_raw_to_src_regressions.py`
- `skills/ll-product-raw-to-src/tests/test_raw_to_src_supervisor_regressions.py`

## Work Package 1

Freeze phase-1 review metadata in contract.

Files:

- `skills/ll-product-raw-to-src/ll.contract.yaml`

Add:

- `review_phase1.artifact_family`
- `review_phase1.risk_profiles`
- `review_phase1.coverage_dimensions`
- `review_phase1.required_checks`
- `review_phase1.gate_block_conditions`

Required values:

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
  required_checks:
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

Acceptance:

- contract parses
- no new custom phase-1 dimensions are introduced
- contract remains specific to `raw-to-src` runtime instead of creating generic framework code

## Work Package 2

Emit machine-readable coverage from the review path.

Files:

- `skills/ll-product-raw-to-src/scripts/raw_to_src_supervisor_phase.py`
- optionally `skills/ll-product-raw-to-src/scripts/raw_to_src_records.py` if shared packaging helpers are needed

Task:

- augment the current review or supervision artifact so it emits:
  - `coverage`
  - `required_checks`
  - `blocker_count`

Phase-1 output contract:

```json
{
  "coverage": {
    "ssot_alignment": "checked|partial|not_checked",
    "object_completeness": "checked|partial|not_checked",
    "contract_completeness": "checked|partial|not_checked",
    "state_transition_closure": "checked|partial|not_checked",
    "failure_path": "checked|partial|not_checked",
    "testability": "checked|partial|not_checked"
  },
  "required_checks": [
    "ssot_alignment",
    "object_completeness",
    "contract_completeness",
    "state_transition_closure",
    "failure_path",
    "testability"
  ],
  "blocker_count": 0
}
```

Rules:

- coverage is additive, not a replacement for findings
- if a dimension is not actually evaluated, emit `not_checked`
- if a dimension is partially evaluated, emit `partial`
- do not infer `blocker_count` from prose; derive it from existing structured findings severity rules

Open design decision to resolve during implementation:

- choose the authoritative carrier for phase-1 fields:
  - embed in `document-test-report.json`
  - embed in supervisor evidence
  - embed in a dedicated review report JSON already consumed by runtime

Preferred direction:

- use the review artifact already closest to current gate and package-readiness checks
- avoid splitting phase-1 fields across multiple artifacts

Acceptance:

- the emitted artifact is produced on the real runtime path
- the artifact contains all six coverage keys every run
- the artifact contains stable `blocker_count`

## Work Package 3

Teach package validation to reject broken review coverage.

Files:

- `skills/ll-product-raw-to-src/scripts/raw_to_src_runtime_support.py`

Task:

- extend package validation so it checks:
  - coverage exists
  - coverage keys match the six-key vocabulary exactly
  - all `required_checks` exist in coverage
  - none of the required checks are `not_checked`
  - `blocker_count` exists and is an integer

Implementation rule:

- reuse the current package validation path
- prefer a small dedicated validator function
- do not create a parallel review validation pipeline

Suggested function split:

- `validate_review_phase1_fields(report: dict[str, Any]) -> list[str]`
- call it from existing `validate_output_package(...)`

Acceptance:

- package validation fails with explicit messages for:
  - missing coverage
  - unknown keys
  - missing required checks
  - `not_checked`
  - invalid blocker count

## Work Package 4

Apply the same rules to freeze readiness.

Files:

- `skills/ll-product-raw-to-src/scripts/raw_to_src_runtime.py`
- `skills/ll-product-raw-to-src/scripts/raw_to_src_runtime_support.py`

Task:

- ensure freeze readiness and action routing do not continue if review coverage is incomplete
- make ADR-039 review completeness a formal readiness precondition

Required runtime behavior:

- `missing coverage -> blocked`
- `required check = not_checked -> blocked`
- `blocker_count > 0 -> blocked`

Important constraint:

- preserve existing blocking rules
- ADR-039 phase-1 checks must add to current gate criteria, not replace them

Acceptance:

- positive canary path still reaches `freeze_ready` when coverage is complete and blocker count is zero
- negative canary paths stop before gate handoff

## Work Package 5

Align the review checklist with the machine path.

Files:

- `skills/ll-product-raw-to-src/resources/checklists/review-checklist.md`
- optionally `skills/ll-product-raw-to-src/agents/supervisor.md`

Task:

- map the current prose checklist to the six shared coverage dimensions
- tell the reviewer which checklist items drive which coverage field
- tell the reviewer to emit `not_checked` when a dimension was not actually reviewed

Do not:

- expand into full ADR-039 challenge loop
- add profile-specific dimensions
- add broad new review theory into the prompt

Acceptance:

- checklist language and machine fields no longer drift
- reviewer instructions match the emitted coverage vocabulary

## Work Package 6

Regression and negative tests.

Files:

- `skills/ll-product-raw-to-src/tests/test_raw_to_src_supervisor_regressions.py`
- `skills/ll-product-raw-to-src/tests/test_raw_to_src_regressions.py`
- optionally `tests/unit/test_product_review_phase1_gate_rules.py`

Add tests for:

1. positive canary:
   - coverage present
   - all six keys present
   - no `not_checked`
   - `blocker_count == 0`
   - workflow still reaches `freeze_ready`

2. negative missing coverage:
   - review artifact omits `coverage`
   - package validation fails

3. negative unknown key:
   - review artifact contains a custom key such as `domain_object_coverage`
   - package validation fails

4. negative not_checked:
   - one required dimension is `not_checked`
   - freeze readiness fails

5. negative blocker count:
   - `blocker_count > 0`
   - freeze readiness fails even if other package checks pass

Test bar:

- do not weaken current semantic lock or supervisor regression assertions
- extend them with ADR-039 behavior instead

## Validation Commands

Minimum validation set after implementation:

```powershell
pytest skills/ll-product-raw-to-src/tests/test_raw_to_src_supervisor_regressions.py
pytest skills/ll-product-raw-to-src/tests/test_raw_to_src_regressions.py
```

Recommended additional validation:

```powershell
pytest tests/unit/test_product_review_phase1_gate_rules.py
python skills/ll-product-raw-to-src/scripts/raw_to_src.py validate-package-readiness --artifacts-dir <sample-artifacts-dir>
```

## Sequencing

Execute in this order:

1. Work Package 1
2. Work Package 2
3. Work Package 3
4. Work Package 4
5. Work Package 6
6. Work Package 5

Reason:

- gate semantics must be real before prompt and checklist text are polished
- tests should lock behavior before review prose is rewritten

## Exit Criteria

The `raw-to-src` canary is complete when:

1. `ll.contract.yaml` declares the phase-1 review metadata
2. the real review path emits six-key coverage
3. the emitted artifact includes `required_checks`
4. the emitted artifact includes `blocker_count`
5. package validation rejects incomplete or custom coverage
6. freeze readiness blocks on `not_checked`
7. freeze readiness blocks on `blocker_count > 0`
8. current successful canary path still reaches gate-ready handoff when review coverage is complete

## Rollout Handoff

Only after the `raw-to-src` canary is green should the team copy the same pattern to:

1. `ll-product-src-to-epic`
2. `ll-product-epic-to-feat`

The downstream rollout should copy:

- the same six coverage keys
- the same `required_checks` shape
- the same gate block conditions

It should not re-open:

- new profiles
- new dimensions
- new artifact family routing
