# Upstream Workflow Analysis

Source template: `E:\ai\LEE\spec-global\departments\product\workflows\templates\raw-to-src\v1\workflow.yaml`

## Upstream Stage Sequence

1. `input_validation`
   - Reject existing SSOT objects and `gate-materialize` placeholders.
2. `raw_input_intake`
   - Capture raw source content and source references.
3. `source_normalization`
   - Build one `normalized_src` candidate with problem statement, target users, scenarios, business drivers, and constraints.
   - Keep same-topic fidelity.
   - If the input is ADR, produce thin bridge SRC semantics.
4. `source_review`
   - Review whether the candidate is stable and traceable enough to serve as downstream source truth.
5. `src_acceptance_auto_check`
   - Run schema, contract, completeness, and dependency checks.
6. `src_acceptance_review`
   - Review six dimensions: functional closure, user story experience, feature completeness, logic vulnerability, industry gap, improvement opportunities.
7. `src_defect_fix_loop`
   - Fix or defer defects, with strict policy for P0 and P1 items.
8. `src_acceptance_approval_gate`
   - Approve only when P0/P1 defects are cleared or explicitly deferred with justification.
9. `source_freeze`
   - Freeze the final SRC and issue `src_root_id`.
10. `output_validation`
    - Validate final SSOT headers, source refs, content completeness, and naming.

## Target Mapping In This Skill

- The source stage semantics are preserved, but the skill now stops at `freeze_readiness_assessment`.
- `input_validation`, `structural_acceptance_check`, and `structural_recheck` remain deterministic and scriptable.
- `source_review` maps to `source_semantic_review`.
- `src_acceptance_auto_check` and `src_defect_fix_loop` map to the structural loop with minimal deterministic patching.
- `src_acceptance_review` maps to `semantic_acceptance_review`.
- `src_acceptance_approval_gate` and `source_freeze` are externalized: the skill emits readiness evidence, `handoff-proposal.json`, and `job-proposal.json`; an external gate decides final materialization.

## Boundaries Preserved

- Raw input only. Already-governed SSOT input is rejected.
- One SRC candidate package per run.
- No automatic split into multiple SRC files.
- No downstream EPIC/FEAT/TASK generation inside this workflow.
- ADR inputs must produce `governance_bridge_src` semantics.
- Formal downstream routing requires handoff runtime artifacts aligned with ADR-003.
