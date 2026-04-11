---
name: ll-qa-settlement
description: ADR-047 governed skill for generating API/E2E settlement reports with pass/fail/blocked/uncovered statistics, gap lists, and waiver lists after test execution.
---

# LL QA Settlement

This skill implements the ADR-047 settlement generation step. After test execution completes, it reads the updated manifests and test results to produce settlement reports for both API and E2E chains. The settlement reports provide the authoritative test outcome statistics consumed by the gate evaluator.

## Canonical Authority

- ADR: `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-047-双链测试架构与防偷懒治理框架.MD`
- Upstream handoff: `ll-test-exec-cli` (API execution) + `ll-test-exec-web-e2e` (E2E execution)
- Downstream consumer: `ll-qa-gate-evaluate`

## Runtime Boundary Baseline

- Interpret this workflow using `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-038-运行时核心抽象边界与对象分层基线.MD`.
- This capability is a governed `Skill` for `Test Results -> Settlement Report` generation.

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md`
7. `output/semantic-checklist.md`

## Execution Protocol

1. Accept updated manifests after test execution:
   - `api-coverage-manifest.yaml` with lifecycle_status and evidence_status updated for executed items
   - `e2e-coverage-manifest.yaml` with lifecycle_status and evidence_status updated for executed items
2. For each chain, compute statistics:
   - `total`: total coverage items in manifest
   - `designed`: items with lifecycle_status=designed (not yet executed)
   - `executed`: items with lifecycle_status in (passed, failed, blocked) and evidence_refs non-empty
   - `passed`: items with lifecycle_status=passed and evidence_status=complete
   - `failed`: items with lifecycle_status=failed
   - `blocked`: items with lifecycle_status=blocked (dependency failure)
   - `uncovered`: items with lifecycle_status=designed (never executed)
   - `cut`: items with lifecycle_status=cut (approved reductions)
   - `obsolete`: items with obsolete=true or superseded_by set
3. Generate gap list: all items where lifecycle_status is failed, blocked, or uncovered (excluding cut, obsolete)
4. Generate waiver list: all items where waiver_status is not `none`
5. Generate chain-specific settlement reports:

### API Settlement Report
At `ssot/tests/.artifacts/settlement/api-settlement-report.yaml`:
```yaml
api_settlement:
  feature_id: {feat_id}
  generated_at: {timestamp}
  statistics:
    total: N
    designed: N
    executed: N
    passed: N
    failed: N
    blocked: N
    uncovered: N
    cut: N
    obsolete: N
    pass_rate: X.XX
  gap_list:
    - coverage_id: {id}
      capability: {cap}
      lifecycle_status: failed|blocked|uncovered
      reason: {why}
  waiver_list:
    - coverage_id: {id}
      waiver_status: pending|approved|rejected
      waiver_reason: {reason}
```

### E2E Settlement Report
At `ssot/tests/.artifacts/settlement/e2e-settlement-report.yaml`:
```yaml
e2e_settlement:
  prototype_id: {proto_id}
  generated_at: {timestamp}
  statistics:
    total: N
    designed: N
    executed: N
    passed: N
    failed: N
    blocked: N
    uncovered: N
    cut: N
    obsolete: N
    pass_rate: X.XX
    exception_journeys:
      total: N
      executed: N
      passed: N
  gap_list: [...]
  waiver_list: [...]
```

6. Run executor agent to generate reports, then supervisor agent to validate statistics consistency.
7. Validate: executed = passed + failed + blocked, pass_rate = passed / max(executed, 1).

## Workflow Boundary

- Input: updated API/E2E manifests after test execution
- Output: `api-settlement-report.yaml` and `e2e-settlement-report.yaml` in `ssot/tests/.artifacts/settlement/`
- Out of scope: gate evaluation (downstream skill), re-running failed tests

## Non-Negotiable Rules

- Do not generate a settlement report without reading the updated manifests.
- Do not count items with no evidence_refs as executed.
- Do not count cut items in the total for pass rate calculation.
- Do not count obsolete items in any statistics except the obsolete counter.
- pass_rate must exclude obsolete and approved waiver items from denominator.
- Gap list must include all failed, blocked, and uncovered items (excluding cut and obsolete).
- Waiver list must include all items with non-none waiver_status.
- Statistics must be self-consistent: executed = passed + failed + blocked.
