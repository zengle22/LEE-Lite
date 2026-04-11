---
name: ll-qa-gate-evaluate
description: ADR-047 governed skill for executing the release gate evaluation, reading API/E2E manifests, settlements, and waivers to generate release_gate_input.yaml with pass/fail decisions and evidence hash binding.
---

# LL QA Gate Evaluate

This skill implements the ADR-047 gate evaluation step. It reads the complete test state from both chains (API and E2E manifests, settlements, waiver records) and produces a `release_gate_input.yaml` with a pass/fail/conditional_pass decision. This is the formal gate between test execution and release approval.

## Canonical Authority

- ADR: `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-047-双链测试架构与防偷懒治理框架.MD`
- Gate evaluator script: `E:\ai\LEE-Lite-skill-first\ssot\tests\gate\gate-evaluator.py`
- Upstream handoff: `ll-test-exec-cli` (API execution) + `ll-test-exec-web-e2e` (E2E execution)
- Downstream consumer: CI pipeline, human gate orchestrator (`ll-gate-human-orchestrator`)

## Runtime Boundary Baseline

- Interpret this workflow using `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-038-运行时核心抽象边界与对象分层基线.MD`.
- This capability is a governed `Skill` for `Test State -> Gate Decision` evaluation.

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md`
7. `output/semantic-checklist.md`

## Execution Protocol

1. Read input artifacts:
   - `api-coverage-manifest.yaml` from `ssot/tests/api/{feat_id}/`
   - `e2e-coverage-manifest.yaml` from `ssot/tests/e2e/{prototype_id}/`
   - API settlement report from `ssot/tests/.artifacts/settlement/api-settlement-report.yaml`
   - E2E settlement report from `ssot/tests/.artifacts/settlement/e2e-settlement-report.yaml`
   - Waiver records from `ssot/tests/.artifacts/settlement/waiver.yaml`
2. Compute API chain metrics:
   - total items, designed items, executed items, passed items, failed items, blocked items, uncovered items
   - pass rate = passed / (executed - obsolete - approved_waiver)
   - items with lifecycle_status=passed must have evidence_status=complete
   - items with waiver_status=pending count as failed
3. Compute E2E chain metrics:
   - same metrics as API chain
   - additionally verify minimum exception journey coverage (must have ≥1 exception journey executed)
4. Apply ADR-047 anti-laziness checks:
   - **Manifest freeze**: manifest items existed before execution (not modified post-execution to add passes)
   - **Cut records**: all cut items have valid cut_record with approver
   - **Pending waiver**: waiver_status=pending items count as failed
   - **Evidence consistency**: lifecycle_status=passed requires evidence_status=complete
   - **Min exception coverage**: E2E must have executed ≥1 exception journey
   - **No-evidence-not-executed**: items with no evidence_refs are NOT counted as executed
   - **Evidence hash binding**: execution log hashes are present and verifiable
5. Generate gate decision:
   - `pass`: both chains ≥80% pass rate, all anti-laziness checks pass, evidence complete
   - `conditional_pass`: one chain meets threshold with minor gaps, waiver records cover remaining
   - `fail`: any chain below threshold or anti-laziness check failure
6. Compute evidence_hash from all evidence_refs across both chains.
7. Generate `release_gate_input.yaml` at `ssot/tests/.artifacts/tests/settlement/release_gate_input.yaml`:
   ```yaml
   gate_evaluation:
     evaluated_at: {timestamp}
     feature_id: {feat_id}
     final_decision: pass|fail|conditional_pass
     api_chain:
       total: N
       passed: N
       failed: N
       blocked: N
       uncovered: N
       pass_rate: X.XX
       evidence_status: complete|partial|missing
     e2e_chain:
       total: N
       passed: N
       failed: N
       blocked: N
       uncovered: N
       pass_rate: X.XX
       exception_journeys_executed: N
       evidence_status: complete|partial|missing
     anti_laziness_checks:
       manifest_frozen: true|false
       cut_records_valid: true|false
       pending_waivers_counted: true|false
       evidence_consistent: true|false
       min_exception_coverage: true|false
       no_evidence_not_executed: true|false
       evidence_hash_binding: true|false
     evidence_hash: {sha256}
     decision_reason: {explanation}
   ```
8. Run executor agent to evaluate, then supervisor agent to validate decision logic.

## Workflow Boundary

- Input: API manifest + E2E manifest + settlements + waivers
- Output: one `release_gate_input.yaml`
- Out of scope: approving the release (human gate orchestrator), re-running failed tests

## Non-Negotiable Rules

- Do not generate a gate decision without reading all required input artifacts.
- Do not count items with waiver_status=pending as passed — they must count as failed.
- Do not count items with no evidence_refs as executed.
- Do not allow lifecycle_status=passed with evidence_status=missing/incomplete — gate must reject.
- Do not generate a pass decision when exception journey coverage is zero.
- Do not skip any of the 7 anti-laziness checks.
- The final_decision field must be one of: `pass`, `fail`, `conditional_pass`.
- Evidence hash must be a SHA-256 of all evidence file contents.
