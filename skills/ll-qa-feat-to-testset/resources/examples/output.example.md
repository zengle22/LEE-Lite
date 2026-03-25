---
artifact_type: test_set_candidate_package
workflow_key: qa.feat-to-testset
status: approval_pending
package_role: candidate
schema_version: 1.0.0
feat_ref: FEAT-SRC-001-001
test_set_ref: TESTSET-SRC-001-001
derived_slug: governed-feat-to-testset
source_refs:
  - product.epic-to-feat::feat-src-001
  - FEAT-SRC-001-001
  - EPIC-SRC-001
  - SRC-001
---

# Example TESTSET Candidate Package

## Selected FEAT

- feat_ref: `FEAT-SRC-001-001`
- title: Governed FEAT to TESTSET

## Requirement Analysis

- coverage_scope 与 risk_focus 来自 selected FEAT。
- coverage_exclusions 明确不扩张到 TECH / TASK / runner implementation。

## Strategy Draft

- integration + e2e layers
- one acceptance check maps to at least one test unit

## TESTSET

- main_object: `test-set.yaml`
- status: `approved`
- companion artifacts serve the main object and do not compete with it.

## Gate Subjects

- `analysis_review`
- `strategy_review`
- `test_set_approval`

## Downstream Handoff

- target_skill: `skill.qa.test_exec_web_e2e`
- required_environment_inputs cover environment, data, services, access, feature_flags, ui_or_integration_context

## Traceability

- `AC-01 -> TS-SRC-001-001-U01`
- `AC-02 -> TS-SRC-001-001-U02`
