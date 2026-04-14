---
name: render-testset-view
description: Backward compatibility skill — aggregates plan/manifest/spec/settlement artifacts from dual-chain system and renders old testset-compatible view.
---

# Render Testset View

This skill provides backward compatibility by aggregating plan, manifest, spec, and settlement artifacts from the new dual-chain system (ADR-047) and rendering them into the old testset-compatible view format. It does NOT execute tests — it is a read-only aggregation skill that transforms new-format artifacts into the legacy testset JSON schema that existing consumers expect.

## Canonical Authority

- ADR: ADR-047 sections 3.7 and 11.1
- Upstream skills: ll-qa-feat-to-apiplan, ll-qa-api-manifest-init, ll-qa-api-spec-gen, ll-qa-settlement
- Legacy testset format: .local/adr018-skill-trial/real-001/artifacts/active/formal/testset/

## Runtime Boundary Baseline

- This capability is a governed `Skill` for `Dual-Chain Artifacts -> Legacy Testset View` transformation.
- Read-only aggregation — does NOT execute tests or modify input artifacts.

## Required Read Order

1. ll.contract.yaml
2. input/contract.yaml
3. output/contract.yaml
4. agents/executor.md
5. agents/supervisor.md
6. input/semantic-checklist.md
7. output/semantic-checklist.md

## Execution Protocol

1. Read input artifacts — accept api-test-plan, api-coverage-manifest, api-test-spec, api-settlement-report (and E2E equivalents if provided). Validate that at least one complete chain (API or E2E) has all 4 artifacts present.
2. Aggregate coverage data from all provided layers — extract capabilities from plan, coverage items from manifest, case mappings from spec, pass/fail statistics from settlement.
3. Map to old testset format — generate assigned_id (derived from feature_id), test_set_ref (matching assigned_id), title (from feat title or feature_id), functional_areas (from api_objects / capabilities), coverage_matrix (from manifest items with lifecycle_status, capability, coverage_id).
4. Write output as JSON at specified output path — conforming to exact legacy testset schema with required fields: assigned_id, test_set_ref, title, functional_areas (array), coverage_matrix (array with coverage_id, capability, lifecycle_status, passed, failed).
5. Run executor agent to perform aggregation and rendering, then supervisor agent to validate output consistency against input artifacts.

## Workflow Boundary

- Input: plan + manifest + spec + settlement (API and/or E2E chains)
- Output: testset-compatible JSON view at specified output path
- Out of scope: test execution, manifest modification, gate evaluation

## Non-Negotiable Rules

- Do not execute tests — this is a read-only aggregation skill.
- Do not modify input artifacts — all source files remain unchanged.
- Output must be readable by old testset consumers — conform to exact legacy schema.
- Aggregate all available chains if both API and E2E are provided — merge coverage data.
- assigned_id and test_set_ref must be deterministic from feature_id — same input always yields same output ID.
- Coverage statistics must be consistent with input settlement report numbers — no fabrication.
- functional_areas must be non-empty if any input chain was provided.
